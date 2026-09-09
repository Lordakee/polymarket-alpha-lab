"""Lazy psycopg adapter for atomic team evaluation attempt persistence.

The sole V1 write path validates every service input offline first: exact
envelope type and batch shape, the orphan run-binding contract (``tea_id``
equals ``team_evidence_aggregation_id(evaluation_scope_payload)``;
``run_metadata`` present and well-formed; ``tfr_id`` equals
``team_forecast_run_id(tea_id, run_metadata)``), row conversion through the
Node 4 codec (both ``team_evaluation_attempt_to_db_row`` and
``team_evaluation_attempt_row_parameters``), and the table identifier. All
of that happens before DSN validation, before any psycopg import, and before
any connection. Every DSN passes through ``validate_local_postgres_dsn``;
DSNs are never echoed into errors. One owned connection carries one batch
call to the store's private transaction-scoped writer, exactly one commit, a
rollback on every ``BaseException``, and a guaranteed close. JSON parameters
are adapted by registering the psycopg jsonb dumper for plain dict values on
the owned connection; cursors and SQL stay owned by the store. The public
legacy insert rejects every ``tea:v1:``/``tfr:v1:``/``tfe:v1:`` identifier
before connection activity and never calls the private writer. Phase 1:
paper-only, report-only, readonly.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn
from polymarket_alpha_lab.team_evidence_aggregation_attempt_store import (
    _insert_attempt_rows_atomic,
    insert_team_evaluation_attempt,
    load_latest_team_evaluation_attempt,
    load_team_evaluation_attempt_rows,
)
from polymarket_alpha_lab.team_evidence_aggregation_db_row import (
    TeamEvaluationAttemptDbRow,
    team_evaluation_attempt_row_parameters,
    team_evaluation_attempt_to_db_row,
)
from polymarket_alpha_lab.team_forecast_build_envelope import (
    TeamForecastBuildEnvelope,
    team_evidence_aggregation_id,
    team_forecast_evaluation_scope_payload,
    team_forecast_run_id,
)

_V1_ID_PREFIXES = ("tea:v1:", "tfr:v1:", "tfe:v1:")
_LEGACY_ID_FIELDS = ("tea_id", "tfr_id", "tfe_id")
_DEFAULT_TABLE_NAME = "team_evaluation_attempts"
_ENV_VAR_NAME = "POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_DSN"
_TABLE_NAME_ERROR = (
    "table_name must be a lowercase identifier with optional schema prefix "
    "and each identifier part length <= 63"
)
_T = TypeVar("_T")


def insert_team_evaluation_attempts_with_psycopg(
    dsn: str,
    envelopes: tuple[TeamForecastBuildEnvelope, ...],
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple[Any, ...]:
    """Atomically persist validated envelopes; one write result per input.

    Inputs are fully validated (batch shape, envelope type, orphan run
    binding, Node 4 row conversion, table identifier) before DSN validation
    and before psycopg is imported. The returned tuple preserves input
    order; each result exposes ``inserted`` (True for a fresh rowcount 1,
    False for a duplicate-conflict rowcount 0) and Phase 1 hard flags.
    """

    rows = _prepare_attempt_rows(envelopes)
    _validate_table_name(table_name)

    def operation(connection: Any) -> tuple[Any, ...]:
        results = tuple(
            _insert_attempt_rows_atomic(connection, rows, table_name=table_name),
        )
        if len(results) != len(rows):
            raise ValueError(
                "the store writer must return exactly one write result per "
                "input row",
            )
        return results

    return _with_owned_connection(dsn, operation)


def persist_team_evaluation_attempts_with_psycopg(
    dsn: str,
    envelopes: tuple[TeamForecastBuildEnvelope, ...],
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple[Any, ...]:
    """Scope-canonical name delegating to the same sole atomic V1 writer."""

    return insert_team_evaluation_attempts_with_psycopg(
        dsn, envelopes, table_name=table_name,
    )


def insert_team_evaluation_attempt_with_psycopg(
    dsn: str,
    row: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> Any:
    """Legacy single-row insert; rejects V1 identifiers before connecting."""

    _reject_v1_identifiers(row)
    _validate_table_name(table_name)
    return _with_owned_connection(
        dsn,
        lambda connection: insert_team_evaluation_attempt(
            connection,
            row,
            table_name=table_name,
        ),
    )


def load_team_evaluation_attempts_with_psycopg(
    dsn: str,
    *,
    tfr_id: str | None = None,
    scope_version: str | None = None,
    scope_key: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple[Any, ...]:
    """Read persisted attempt rows through one owned connection.

    Filter combination rules and ordering live in the store loader; this
    wrapper only owns the table identifier check, the DSN check, the
    connection lifecycle, and the single commit.
    """

    _validate_table_name(table_name)
    return _with_owned_connection(
        dsn,
        lambda connection: load_team_evaluation_attempt_rows(
            connection,
            tfr_id=tfr_id,
            scope_version=scope_version,
            scope_key=scope_key,
            limit=limit,
            table_name=table_name,
        ),
    )


def load_latest_team_evaluation_attempt_with_psycopg(
    dsn: str,
    *,
    tfr_id: str | None = None,
    scope_version: str | None = None,
    scope_key: str | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> Any:
    """Read the latest attempt for one run or scope; ordering lives in the store."""

    _validate_table_name(table_name)
    return _with_owned_connection(
        dsn,
        lambda connection: load_latest_team_evaluation_attempt(
            connection,
            tfr_id=tfr_id,
            scope_version=scope_version,
            scope_key=scope_key,
            table_name=table_name,
        ),
    )


def _prepare_attempt_rows(
    envelopes: tuple[TeamForecastBuildEnvelope, ...],
) -> tuple[TeamEvaluationAttemptDbRow, ...]:
    if type(envelopes) is not tuple or not envelopes:
        raise ValueError(
            "envelopes must be a nonempty tuple of "
            "TeamForecastBuildEnvelope values",
        )
    rows: list[TeamEvaluationAttemptDbRow] = []
    for index, envelope in enumerate(envelopes):
        if type(envelope) is not TeamForecastBuildEnvelope:
            raise ValueError(
                f"envelopes[{index}] must be exactly TeamForecastBuildEnvelope",
            )
        payload = team_forecast_evaluation_scope_payload(envelope)
        run_metadata = payload.get("run_metadata")
        if type(run_metadata) is not dict:
            raise ValueError(
                f"envelopes[{index}] is an orphan run binding: "
                "evaluation_scope_payload.run_metadata must be a present "
                "JSON object",
            )
        if envelope.tea_id != team_evidence_aggregation_id(payload):
            raise ValueError(
                f"envelopes[{index}] is an orphan run binding: tea_id must "
                "equal team_evidence_aggregation_id(evaluation_scope_payload)",
            )
        if envelope.tfr_id != team_forecast_run_id(envelope.tea_id, run_metadata):
            raise ValueError(
                f"envelopes[{index}] is an orphan run binding: tfr_id must "
                "equal team_forecast_run_id(tea_id, run_metadata)",
            )
        row = team_evaluation_attempt_to_db_row(
            tea_id=envelope.tea_id,
            tfr_id=envelope.tfr_id,
            evaluation_scope_payload=payload,
        )
        team_evaluation_attempt_row_parameters(row)  # offline codec round trip
        rows.append(row)
    return tuple(rows)


def _reject_v1_identifiers(row: Any) -> None:
    for field_name in _LEGACY_ID_FIELDS:
        _reject_v1_value(field_name, getattr(row, field_name, None))
    _reject_v1_payload_values(getattr(row, "evaluation_scope_payload", None))


def _reject_v1_value(field_name: str, value: Any) -> None:
    if type(value) is not str:
        return
    for prefix in _V1_ID_PREFIXES:
        if value.startswith(prefix):
            raise ValueError(
                "insert_team_evaluation_attempt_with_psycopg must not "
                f"accept a {field_name} carrying a reserved {prefix} "
                "identifier; use "
                "insert_team_evaluation_attempts_with_psycopg",
            )


def _reject_v1_payload_values(value: Any) -> None:
    if type(value) is str:
        _reject_v1_value("evaluation_scope_payload", value)
    elif type(value) is list:
        for item in value:
            _reject_v1_payload_values(item)
    elif type(value) is dict:
        for item in value.values():
            _reject_v1_payload_values(item)


def _validate_table_name(value: str) -> str:
    if type(value) is not str:
        raise ValueError(_TABLE_NAME_ERROR)
    parts = value.split(".")
    if len(parts) not in (1, 2) or not all(_is_table_identifier(p) for p in parts):
        raise ValueError(_TABLE_NAME_ERROR)
    return value


def _is_table_identifier(part: str) -> bool:
    if not part or len(part.encode("utf-8")) > 63:
        return False
    if not ("a" <= part[0] <= "z"):
        return False
    if len(part) > 1 and not ("a" <= part[-1] <= "z" or "0" <= part[-1] <= "9"):
        return False
    return all(
        char == "_" or "a" <= char <= "z" or "0" <= char <= "9"
        for char in part[1:-1]
    )


def _with_owned_connection(dsn: str, operation: Callable[[Any], _T]) -> _T:
    validate_local_postgres_dsn(dsn, env_var_name=_ENV_VAR_NAME)
    connection = _connect(dsn)
    try:
        _register_dict_jsonb_dumper(connection)
        result = operation(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()
    return result


def _connect(dsn: str) -> Any:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the team evaluation attempt "
            "psycopg adapter; install the postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn)
    except BaseException:
        raise RuntimeError(
            "failed to connect to the team evaluation attempt database",
        ) from None


def _register_dict_jsonb_dumper(connection: Any) -> None:
    from psycopg.types.json import JsonbDumper

    connection.adapters.register_dumper(dict, JsonbDumper)


__all__ = (
    "insert_team_evaluation_attempt_with_psycopg",
    "persist_team_evaluation_attempts_with_psycopg",
)
