"""Opt-in real-database lifecycle acceptance for central data persistence.

The whole destructive scenario runs inside ONE transaction that is always
rolled back, so synthetic rows, audit rows, and any incidental purge deletes
never persist.  The checked-in migration is re-applied inside that same
transaction to prove idempotency.  Enable explicitly:

    PAL_CENTRAL_DATA_DB_LIFECYCLE=1
    POLYMARKET_ALPHA_LAB_CENTRAL_DATA_PERSISTENCE_DSN=<validated local DSN>

The DSN must pass ``validate_local_postgres_dsn`` and is never echoed.
"""

from datetime import UTC, datetime, timedelta
import os
from pathlib import Path

import pytest

from polymarket_alpha_lab.central_data_contracts import (
    EvidenceReference,
    Freshness,
    NormalizedObservation,
    ObservationValueState,
    ParseState,
    RawResponse,
    SourceDefinition,
    sha256_hash,
)
from polymarket_alpha_lab.central_data_db_row import (
    NormalizedObservationRow,
    RawEventRow,
)
from polymarket_alpha_lab.central_data_store import (
    AUDIT_TABLE,
    NORMALIZED_TABLE,
    RAW_TABLE,
    CentralDataStore,
    CentralDataStoreError,
)
from polymarket_alpha_lab.supabase_central_data_config import (
    CENTRAL_DATA_PERSISTENCE_DSN_ENV_VAR,
    validate_local_postgres_dsn,
)


pytestmark = pytest.mark.skipif(
    os.environ.get("PAL_CENTRAL_DATA_DB_LIFECYCLE") != "1",
    reason="set PAL_CENTRAL_DATA_DB_LIFECYCLE=1 and provide the DSN env var "
    "for the local-only destructive lifecycle acceptance",
)

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "supabase"
    / "migrations"
    / "20260731000000_central_data_evidence.sql"
)

_RAW_COLUMNS = (
    "raw_event_id", "source_id", "source_family", "endpoint_url",
    "official_source", "request_url", "final_url", "retrieval_time",
    "status_code", "content_type", "safe_headers", "failure_status",
    "raw_body", "body_length", "raw_payload_sha256", "expires_at",
    "paper_only", "report_only", "readonly",
)

_LIFECYCLE_SOURCE = SourceDefinition(
    "pal-m0-lifecycle-a",
    "pal-m0-official",
    "https://example.invalid/pal-m0-a",
    "application/json",
    60,
    True,
)
_LIFECYCLE_SOURCE_B = SourceDefinition(
    "pal-m0-lifecycle-b",
    "pal-m0-official-b",
    "https://example.invalid/pal-m0-b",
    "application/json",
    60,
    True,
)
_LIFECYCLE_SOURCE_C = SourceDefinition(
    "pal-m0-lifecycle-c",
    "pal-m0-official-c",
    "https://example.invalid/pal-m0-c",
    "application/json",
    60,
    True,
)


def _raw_row(
    source: SourceDefinition,
    *,
    body: bytes,
    retrieval_time: datetime,
) -> RawEventRow:
    raw = RawResponse(
        200,
        {"content-type": "application/json"},
        body,
        source.url_template,
        retrieval_time=retrieval_time,
        request_url=source.url_template,
        content_type="application/json",
    )
    return RawEventRow.from_contracts(source, raw)


def _normalized_row(
    raw: RawEventRow,
    source: SourceDefinition,
) -> NormalizedObservationRow:
    observation = NormalizedObservation(
        source.source_id,
        raw.retrieval_time,
        {"pal_m0_value": "synthetic"},
        Freshness.FRESH,
        ParseState.SUCCESS,
        EvidenceReference(
            source.source_id,
            raw.retrieval_time,
            raw.retrieval_time,
            raw.raw_payload_sha256,
        ),
        ObservationValueState.PRESENT,
        reason_codes=("pal_m0_synthetic",),
    )
    return NormalizedObservationRow.from_contracts(source, observation, raw.identity)


def _dsn() -> str:
    dsn = os.environ.get(CENTRAL_DATA_PERSISTENCE_DSN_ENV_VAR)
    if not dsn:
        pytest.fail(
            f"{CENTRAL_DATA_PERSISTENCE_DSN_ENV_VAR} must be set for the lifecycle run"
        )
    validate_local_postgres_dsn(dsn)
    return dsn


@pytest.fixture()
def connection():
    psycopg = pytest.importorskip("psycopg")
    conn = psycopg.connect(_dsn(), connect_timeout=10)
    conn.autocommit = False
    try:
        yield conn
    finally:
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()


@pytest.fixture()
def wrapped(connection):
    from polymarket_alpha_lab.central_data_psycopg import _JsonConnection
    from psycopg.types.json import Jsonb

    return _JsonConnection(connection, Jsonb)


def _scalar(connection, sql: str, params: tuple = ()) -> object:
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
        assert row is not None
        return row[0]


def _counts(connection) -> dict[str, int]:
    return {
        key: int(_scalar(connection, f"SELECT count(*) FROM {name}"))
        for key, name in (
            ("raw", RAW_TABLE),
            ("normalized", NORMALIZED_TABLE),
            ("audit", AUDIT_TABLE),
        )
    }


def _pg_cron_available(connection) -> bool:
    return bool(
        _scalar(
            connection,
            "SELECT count(*) = 1 FROM pg_catalog.pg_extension "
            "WHERE extname = 'pg_cron'",
        )
    )


def _raw_insert_sql() -> str:
    placeholders = ", ".join("%s" for _column in _RAW_COLUMNS)
    return (
        f"INSERT INTO {RAW_TABLE} ({', '.join(_RAW_COLUMNS)}) "
        f"VALUES ({placeholders})"
    )


def _raw_variant(base: tuple, event_id: str, **overrides) -> tuple:
    values = list(base)
    values[0] = event_id
    for column, value in overrides.items():
        values[_RAW_COLUMNS.index(column)] = value
    return tuple(values)


def test_lifecycle_scenario(connection, wrapped) -> None:
    if not _pg_cron_available(connection):
        pytest.skip("pg_cron must already be installed for the lifecycle run")

    baseline = _counts(connection)
    now = datetime.now(UTC)
    row_a = _raw_row(
        _LIFECYCLE_SOURCE,
        body=b'{"pal_m0": "synthetic-a"}',
        retrieval_time=now,
    )
    row_b = _raw_row(
        _LIFECYCLE_SOURCE_B,
        body=b'{"pal_m0": "synthetic-b"}',
        retrieval_time=now,
    )
    row_c_old = _raw_row(
        _LIFECYCLE_SOURCE_C,
        body=b'{"pal_m0": "synthetic-c-expired"}',
        retrieval_time=now - timedelta(days=30),
    )
    normalized_b = _normalized_row(row_b, _LIFECYCLE_SOURCE_B)
    normalized_c = _normalized_row(row_c_old, _LIFECYCLE_SOURCE_C)
    synthetic_ids = (row_a.raw_event_id, row_b.raw_event_id, row_c_old.raw_event_id)
    store = CentralDataStore(wrapped)
    base = row_a.as_parameters()

    try:
        # 3. Idempotent migration reapplication inside the same transaction.
        migration_sql = MIGRATION_PATH.read_text(encoding="utf-8")
        with connection.cursor() as cursor:
            cursor.execute(migration_sql)
        for name in (RAW_TABLE, NORMALIZED_TABLE, AUDIT_TABLE):
            assert _scalar(connection, "SELECT to_regclass(%s) IS NOT NULL", (name,))
        assert _scalar(
            connection,
            "SELECT to_regprocedure(%s) IS NOT NULL",
            (
                "central_data_internal.purge_expired_central_data_raw_response_events"
                "(timestamptz, integer)",
            ),
        )

        # 4. Retention health gate (sees this transaction's seeded state).
        assert store.health_check_retention() is True

        # 5. Insert + idempotent replay.
        assert store.insert_raw_event(row_a).status == "inserted"
        assert store.insert_raw_event(row_a).status == "already_present"

        # 6. Identity collisions for differing integer, jsonb, and bytea fields.
        different_body = b'{"pal_m0": "different"}'

        def _install_conflicting(**overrides) -> None:
            with connection.transaction():
                cursor = wrapped.cursor()
                try:
                    cursor.execute(
                        f"DELETE FROM {RAW_TABLE} WHERE raw_event_id = %s",
                        (row_a.raw_event_id,),
                    )
                    cursor.execute(
                        _raw_insert_sql(),
                        _raw_variant(base, row_a.raw_event_id, **overrides),
                    )
                finally:
                    cursor.close()

        conflicting_variants = (
            {"status_code": 204},
            {"safe_headers": {"date": "Thu, 01 Jan 2026 00:00:00 GMT"}},
            {
                "raw_body": different_body,
                "body_length": len(different_body),
                "raw_payload_sha256": sha256_hash(different_body),
            },
        )
        for overrides in conflicting_variants:
            _install_conflicting(**overrides)
            with pytest.raises(CentralDataStoreError) as caught:
                store.insert_raw_event(row_a)
            assert caught.value.code == "identity_collision"
        with connection.transaction():
            cursor = wrapped.cursor()
            try:
                cursor.execute(
                    f"DELETE FROM {RAW_TABLE} WHERE raw_event_id = %s",
                    (row_a.raw_event_id,),
                )
            finally:
                cursor.close()
        assert store.insert_raw_event(row_a).status == "inserted"

        # 7. Normalized insert + replay.
        assert store.insert_raw_event(row_b).status == "inserted"
        assert store.insert_normalized_observation(normalized_b).status == "inserted"
        assert store.insert_normalized_observation(normalized_b).status == "already_present"

        # 8. Provenance mismatch: the stored raw row stops matching the row.
        with connection.transaction():
            cursor = wrapped.cursor()
            try:
                cursor.execute(
                    f"UPDATE {RAW_TABLE} SET source_id = 'pal-m0-corrupted' "
                    "WHERE raw_event_id = %s",
                    (row_b.raw_event_id,),
                )
            finally:
                cursor.close()
        with pytest.raises(CentralDataStoreError) as caught:
            store.insert_normalized_observation(
                _normalized_row(row_b, _LIFECYCLE_SOURCE_B)
            )
        assert caught.value.code == "raw_event_provenance_mismatch"
        with connection.transaction():
            cursor = wrapped.cursor()
            try:
                cursor.execute(
                    f"UPDATE {RAW_TABLE} SET source_id = %s WHERE raw_event_id = %s",
                    (_LIFECYCLE_SOURCE_B.source_id, row_b.raw_event_id),
                )
            finally:
                cursor.close()
        assert store.insert_normalized_observation(
            _normalized_row(row_b, _LIFECYCLE_SOURCE_B)
        ).status == "already_present"

        # 9. Missing raw event.
        row_never = _raw_row(
            _LIFECYCLE_SOURCE_C,
            body=b'{"pal_m0": "never-inserted"}',
            retrieval_time=now,
        )
        with pytest.raises(CentralDataStoreError) as caught:
            store.insert_normalized_observation(
                _normalized_row(row_never, _LIFECYCLE_SOURCE_C)
            )
        assert caught.value.code == "raw_event_unavailable"

        # 10. Readback with filters.
        readback = store.get_unexpired_raw(source_id=_LIFECYCLE_SOURCE.source_id)
        assert tuple(row.raw_event_id for row in readback) == (row_a.raw_event_id,)
        assert bytes(readback[0].raw_body) == row_a.raw_body
        assert readback[0].raw_payload_sha256 == row_a.raw_payload_sha256
        assert dict(readback[0].safe_headers) == dict(row_a.safe_headers)
        assert store.get_unexpired_raw(source_id="pal-m0-absent") == ()
        observations = store.get_normalized_observations(raw_event_id=row_b.raw_event_id)
        assert tuple(row.normalized_observation_id for row in observations) == (
            normalized_b.normalized_observation_id,
        )
        assert dict(observations[0].typed_value) == dict(normalized_b.typed_value)
        assert tuple(observations[0].reason_codes) == tuple(normalized_b.reason_codes)

        # 11. Database-level CHECK enforcement (savepoint-isolated).
        def _expect_check_failure(insert_sql: str, params: tuple) -> None:
            with pytest.raises(Exception) as caught:
                with connection.transaction():
                    cursor = wrapped.cursor()
                    try:
                        cursor.execute(insert_sql, params)
                    finally:
                        cursor.close()
            diag = getattr(caught.value, "diag", None)
            assert getattr(diag, "sqlstate", None) == "23514", caught.value

        _expect_check_failure(
            _raw_insert_sql(),
            _raw_variant(base, "a" * 64, content_type="text/html"),
        )
        _expect_check_failure(
            _raw_insert_sql(),
            _raw_variant(base, "b" * 64, body_length=base[13] + 1),
        )
        _expect_check_failure(
            _raw_insert_sql(),
            _raw_variant(base, "c" * 64, expires_at=base[7] + timedelta(days=30)),
        )
        _expect_check_failure(
            _raw_insert_sql(),
            _raw_variant(base, "d" * 64, raw_payload_sha256="e" * 64),
        )
        oversize = b"x" * (2 * 1024 * 1024 + 1)
        _expect_check_failure(
            _raw_insert_sql(),
            _raw_variant(
                base,
                "f" * 64,
                raw_body=oversize,
                body_length=len(oversize),
            ),
        )
        normalized_columns = (
            "normalized_observation_id", "raw_event_id", "source_id",
            "source_family", "endpoint_url", "official_source",
            "observation_time", "retrieval_time", "raw_payload_sha256",
            "parser_version", "parse_state", "freshness_state",
            "failure_status", "value_state", "reason_codes", "typed_value",
            "paper_only", "report_only", "readonly",
        )
        normalized_placeholders = ", ".join("%s" for _column in normalized_columns)
        malformed_normalized = list(normalized_b.as_parameters())
        malformed_normalized[15] = {"type": "bogus"}
        _expect_check_failure(
            f"INSERT INTO {NORMALIZED_TABLE} ({', '.join(normalized_columns)}) "
            f"VALUES ({normalized_placeholders})",
            tuple(malformed_normalized),
        )

        # 12. Boundary sanity: refused payloads never reach SQL.
        refused = RawResponse(
            200,
            {"authorization": "Bearer pal-m0-not-real"},
            b'{"ok": true}',
            _LIFECYCLE_SOURCE.url_template,
            retrieval_time=now,
            request_url=_LIFECYCLE_SOURCE.url_template,
            content_type="application/json",
        )
        with pytest.raises(ValueError):
            RawEventRow.from_contracts(_LIFECYCLE_SOURCE, refused)

        # 13. Retention cutoff boundary with an already-expired row.
        assert store.insert_raw_event(row_c_old).status == "inserted"
        # The store intentionally refuses to normalize an already-expired
        # raw event (its lock requires expires_at > now), so this valid row
        # is bound by direct SQL purely to prove normalized-row survival
        # across the purge; the refusal itself is covered by step 9.
        cursor = wrapped.cursor()
        try:
            cursor.execute(
                f"INSERT INTO {NORMALIZED_TABLE} ({', '.join(normalized_columns)}) "
                f"VALUES ({normalized_placeholders})",
                normalized_c.as_parameters(),
            )
        finally:
            cursor.close()
        deleted = store.purge_expired_raw(datetime.now(UTC))
        assert deleted >= 1
        assert row_c_old.raw_event_id not in tuple(
            row.raw_event_id
            for row in store.get_unexpired_raw(source_id=_LIFECYCLE_SOURCE_C.source_id)
        )
        assert row_a.raw_event_id in tuple(
            row.raw_event_id
            for row in store.get_unexpired_raw(source_id=_LIFECYCLE_SOURCE.source_id)
        )
        audit_rows = store.load_retention_audit(limit=100)
        assert {
            (row["audit_kind"], row["reason_code"])
            for row in audit_rows
            if row["audit_kind"] == "raw_delete"
            and row["raw_event_id"] == row_c_old.raw_event_id
        } == {("raw_delete", "expired_retention")}
        assert any(row["audit_kind"] == "purge_run" for row in audit_rows)
        # Normalized rows survive the purge of their raw event.
        assert tuple(
            row.normalized_observation_id
            for row in store.get_normalized_observations(
                raw_event_id=row_c_old.raw_event_id
            )
        ) == (normalized_c.normalized_observation_id,)
    finally:
        connection.rollback()

    # 14. Rollback verification: baseline counts and explicit ID absence.
    assert _counts(connection) == baseline
    for event_id in synthetic_ids:
        assert _scalar(
            connection,
            f"SELECT count(*) FROM {RAW_TABLE} WHERE raw_event_id = %s",
            (event_id,),
        ) == 0
        assert _scalar(
            connection,
            f"SELECT count(*) FROM {NORMALIZED_TABLE} WHERE raw_event_id = %s",
            (event_id,),
        ) == 0
        assert _scalar(
            connection,
            f"SELECT count(*) FROM {AUDIT_TABLE} WHERE raw_event_id = %s",
            (event_id,),
        ) == 0
    assert _scalar(
        connection,
        f"SELECT count(*) FROM {NORMALIZED_TABLE} "
        "WHERE normalized_observation_id = %s",
        (normalized_b.normalized_observation_id,),
    ) == 0
    connection.rollback()


def test_catalog_and_privilege_contract(connection) -> None:
    if not _pg_cron_available(connection):
        pytest.skip("pg_cron must already be installed for the lifecycle run")

    # Supabase databases drop the PUBLIC role, so only the platform roles
    # are probed here.
    restricted_roles = ("anon", "authenticated", "service_role")
    for table in (RAW_TABLE, NORMALIZED_TABLE, AUDIT_TABLE):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT r.rolname, c.relrowsecurity, c.relforcerowsecurity "
                "FROM pg_catalog.pg_class c "
                "JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
                "JOIN pg_catalog.pg_roles r ON r.oid = c.relowner "
                "WHERE n.nspname || '.' || c.relname = %s",
                (table,),
            )
            row = cursor.fetchone()
        assert row is not None, table
        owner, rls, force = row
        assert owner == "postgres", table
        assert rls is True, table
        assert force is False, table
        for role in restricted_roles:
            assert _scalar(
                connection,
                "SELECT has_table_privilege(%s, %s, 'SELECT')",
                (role, table),
            ) is False
            assert _scalar(
                connection,
                "SELECT has_table_privilege(%s, %s, 'INSERT')",
                (role, table),
            ) is False
    for role in ("anon", "authenticated", "service_role"):
        assert _scalar(
            connection,
            "SELECT has_schema_privilege(%s, 'central_data_internal', 'USAGE')",
            (role,),
        ) is False
        assert _scalar(
            connection,
            "SELECT has_function_privilege(%s, %s, 'EXECUTE')",
            (
                role,
                "central_data_internal.purge_expired_central_data_raw_response_events"
                "(timestamptz, integer)",
            ),
        ) is False

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT jobname, schedule, command, database, username, active "
            "FROM cron.job WHERE jobname = 'central_data_raw_retention_15m'"
        )
        job = cursor.fetchone()
    assert job == (
        "central_data_raw_retention_15m",
        "*/15 * * * *",
        "select central_data_internal.purge_expired_central_data_raw_response_events();",
        "postgres",
        "postgres",
        True,
    )
    connection.rollback()


def test_connection_guards(connection) -> None:
    assert _scalar(connection, "SELECT current_database()") == "postgres"
    assert _scalar(connection, "SELECT current_user") == "postgres"
    assert _scalar(
        connection, "SELECT current_setting('cron.database_name', true)"
    ) == "postgres"
    connection.rollback()
