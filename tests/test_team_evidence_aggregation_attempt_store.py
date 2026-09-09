"""Node 5 store contract tests: team evaluation attempts, offline DB-API fakes.

Governing plan: docs/superpowers/plans/2026-07-13-team-forecast-atomic-persistence.md
(caller owns the transaction; the store owns SQL, filters, and the fence)."""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.team_evidence_aggregation_attempt_store as attempt_store
from polymarket_alpha_lab.team_evidence_aggregation_db_row import (
    TeamEvaluationAttemptDbRow,
    team_evaluation_attempt_row_parameters,
    team_evaluation_attempt_to_db_row,
)

SCOPE_VERSION = "team-evidence-aggregation-store-test-v1"
CONFIG_VERSION = "generic-store-test-v1"
CONFIG_DIGEST = hashlib.sha256(b"store-test-config").hexdigest()
ATTEMPTED_AT_EARLIER = "2026-07-13T08:55:00.000000+00:00"
ATTEMPTED_AT = "2026-07-13T09:00:00.000000+00:00"
ATTEMPTED_AT_LATER = "2026-07-13T09:05:00.000000+00:00"
HARD_FLAGS = {"paper_only": True, "report_only": True, "readonly": True}
# Hardcoded lock on the Node 4 insert column order (== codec parameter keys).
ATTEMPT_COLUMNS = (
    "tea_id", "tfr_id", "attempted_at", "status", "hard_flag", "scope_version",
    "scope_key", "config_version", "config_digest", "diagnostic_record_count",
    "arithmetic_record_count", "payload_sha256", "evaluation_scope_payload",
    "paper_only", "report_only", "readonly",
)
DEFAULT_TABLE = "team_evaluation_attempts"
EXPECTED_COLUMNS_SQL = ", ".join(ATTEMPT_COLUMNS)
EXPECTED_PLACEHOLDERS = ", ".join(f"%({column})s" for column in ATTEMPT_COLUMNS)


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def attempt_payload(
    *,
    status: str = "ready",
    contradiction: str | None = None,
    evaluated_at: str = ATTEMPTED_AT,
    scope_version: str = SCOPE_VERSION,
    domain_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if contradiction is None:
        contradiction = {"blocked": "blocked", "watch": "watch"}.get(status, "none")
    domain = (
        {"team_id": "crypto_btc", "market_slug": "will-btc-close-above-105k-on-july-4"}
        if domain_context is None else dict(domain_context)
    )
    result = {"evaluated_at": evaluated_at, "status": status,
              "contradiction": {"status": contradiction},
              "config_version": CONFIG_VERSION, "config_digest": CONFIG_DIGEST,
              "diagnostic_record_count": 1, "arithmetic_record_count": 1, **HARD_FLAGS}
    return {
        "scope_version": scope_version, "domain_context": domain,
        "provenance": ["clob:book/0xabc", "gamma:market/12345"],
        "run_metadata": {"run_id": "node5-store-run-001",
                         "generator_version": "team-forecast-generator-v1", **HARD_FLAGS},
        "evaluator_receipts": [{"evaluator_id": "evaluator:alpha", **HARD_FLAGS}],
        "node2_config": {"config": {"config_version": CONFIG_VERSION, **HARD_FLAGS}},
        "node2_input": {"input": {"record_count": 1, **HARD_FLAGS}},
        "node2_result": {"result": result},
    }


def attempt_row(
    *,
    status: str = "ready",
    contradiction: str | None = None,
    evaluated_at: str = ATTEMPTED_AT,
    scope_version: str = SCOPE_VERSION,
    domain_context: dict[str, Any] | None = None,
    seed: str = "alpha",
    tfr_seed: str = "run-1",
) -> TeamEvaluationAttemptDbRow:
    return team_evaluation_attempt_to_db_row(
        tea_id="tea:v1:" + digest(f"tea:{seed}"),
        tfr_id="tfr:v1:" + digest(f"tfr:{tfr_seed}"),
        evaluation_scope_payload=attempt_payload(
            status=status, contradiction=contradiction, evaluated_at=evaluated_at,
            scope_version=scope_version, domain_context=domain_context),
    )


def row_record(row: TeamEvaluationAttemptDbRow) -> dict[str, Any]:
    return {column: getattr(row, column) for column in ATTEMPT_COLUMNS}


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def expected_select(table_name: str, where_clause: str, tail: str) -> str:
    return (
        f"SELECT {EXPECTED_COLUMNS_SQL} FROM {table_name} {where_clause} "
        f"ORDER BY attempted_at DESC, tea_id DESC {tail}"
    )


class FakeCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        rowcount: int = 1,
        rowcounts: tuple[int, ...] | None = None,
        execute_errors: tuple[Exception | None, ...] | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.rows = tuple(rows)
        self.rowcount = rowcount
        self._rowcounts = list(rowcounts) if rowcounts is not None else None
        self._execute_errors = list(execute_errors) if execute_errors is not None else None
        self.calls: list[tuple[str, Any]] = []
        self.close_count = 0
        self.fetchall_error = fetchall_error
        self.close_error = close_error

    def execute(self, sql: str, params: Any = None) -> None:
        self.calls.append((sql, params))
        if self._execute_errors is not None:
            error = self._execute_errors.pop(0)
            if error is not None:
                raise error
        if self._rowcounts is not None:
            self.rowcount = self._rowcounts.pop(0)

    def fetchall(self) -> tuple[Any, ...]:
        if self.fetchall_error is not None:
            raise self.fetchall_error
        return self.rows

    def close(self) -> None:
        self.close_count += 1
        if self.close_error is not None:
            raise self.close_error


class FakeConnection:
    def __init__(self, rows: tuple[Any, ...] = (), **cursor_kwargs: Any) -> None:
        self.cursor_instance = FakeCursor(rows, **cursor_kwargs)
        self.cursor_count = 0
        self.commit_count = 0
        self.rollback_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


@dataclass(frozen=True)
class FakeLegacyRow:
    tea_id: str | None = "legacy-tea-001"
    tfr_id: str | None = "legacy-tfr-001"
    tfe_id: str | None = None
    evaluation_scope_payload: Any = None


@pytest.fixture()
def writer_spy(monkeypatch: pytest.MonkeyPatch) -> list[tuple[Any, ...]]:
    calls: list[tuple[Any, ...]] = []

    def spy(*args: Any, **kwargs: Any) -> None:
        calls.append((args, kwargs))
        raise AssertionError("the private atomic writer must not be called")

    monkeypatch.setattr(attempt_store, "_insert_attempt_rows_atomic", spy)
    return calls


def test_public_exports_match_store_surface() -> None:
    assert set(attempt_store.__all__) == {
        "TEAM_EVALUATION_ATTEMPT_COLUMNS", "TeamEvaluationAttemptWriteResult",
        "insert_team_evaluation_attempt", "load_latest_team_evaluation_attempt",
        "load_team_evaluation_attempt_rows",
    }
    assert attempt_store.TEAM_EVALUATION_ATTEMPT_COLUMNS == tuple(
        team_evaluation_attempt_row_parameters(attempt_row())
    )


def test_private_writer_executes_exact_node4_columns_and_parameters() -> None:
    row = attempt_row(seed="insert")
    connection = FakeConnection(rowcounts=(1,))

    results = attempt_store._insert_attempt_rows_atomic(
        connection, (row,), table_name="research.team_evaluation_attempts"
    )

    cursor = connection.cursor_instance
    assert connection.cursor_count == 1
    assert connection.commit_count == 0 and connection.rollback_count == 0
    assert cursor.close_count == 1 and len(cursor.calls) == 1
    sql, params = cursor.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        f"""
        INSERT INTO research.team_evaluation_attempts (
            {EXPECTED_COLUMNS_SQL}
        ) VALUES ({EXPECTED_PLACEHOLDERS})
        ON CONFLICT (tea_id) DO NOTHING
        """,
    )
    assert params == team_evaluation_attempt_row_parameters(row)
    assert list(params) == list(attempt_store.TEAM_EVALUATION_ATTEMPT_COLUMNS)
    assert params["attempted_at"] == ATTEMPTED_AT and params["paper_only"] is True
    assert json.dumps(params, allow_nan=False, default=str)
    assert results == (
        attempt_store.TeamEvaluationAttemptWriteResult(row=row, inserted=True),
    )
    assert results[0].inserted is True and results[0].row is row
    assert (results[0].paper_only is True and results[0].report_only is True
            and results[0].readonly is True)


@pytest.mark.parametrize(
    ("rowcount", "inserted"), ((1, True), (0, False), (-1, None), (2, None))
)
def test_private_writer_maps_rowcount_to_inserted_flag(
    rowcount: int, inserted: bool | None
) -> None:
    connection = FakeConnection(rowcounts=(rowcount,))
    row = attempt_row(seed=f"rc-{rowcount}")
    if inserted is None:
        with pytest.raises(ValueError, match="rowcount"):
            attempt_store._insert_attempt_rows_atomic(connection, (row,))
    else:
        results = attempt_store._insert_attempt_rows_atomic(connection, (row,))
        assert results[0].inserted is inserted and results[0].row == row
        sql, _ = connection.cursor_instance.calls[0]
        assert normalize_sql(sql).startswith("INSERT INTO team_evaluation_attempts")
    assert connection.cursor_instance.close_count == 1
    assert connection.commit_count == 0 and connection.rollback_count == 0


def test_private_writer_mixed_batch_preserves_order_on_one_cursor() -> None:
    rows = (
        attempt_row(seed="batch-1", evaluated_at=ATTEMPTED_AT_EARLIER),
        attempt_row(seed="batch-2", evaluated_at=ATTEMPTED_AT),
        attempt_row(seed="batch-3", evaluated_at=ATTEMPTED_AT_LATER),
    )
    connection = FakeConnection(rowcounts=(1, 0, 1))

    results = attempt_store._insert_attempt_rows_atomic(connection, rows)

    cursor = connection.cursor_instance
    assert connection.cursor_count == 1
    assert [sql for sql, _ in cursor.calls] == [cursor.calls[0][0]] * 3
    expected_params = [team_evaluation_attempt_row_parameters(row) for row in rows]
    assert [params for _, params in cursor.calls] == expected_params
    assert tuple(result.row for result in results) == rows
    assert tuple(result.inserted for result in results) == (True, False, True)
    assert cursor.close_count == 1
    assert connection.commit_count == 0 and connection.rollback_count == 0


def test_private_writer_empty_batch_returns_empty_without_cursor_activity() -> None:
    connection = FakeConnection()

    assert attempt_store._insert_attempt_rows_atomic(connection, ()) == ()
    assert connection.cursor_count == 0 and connection.cursor_instance.calls == []


def test_private_writer_rejects_invalid_rows_and_table_before_cursor() -> None:
    for rows in ("not-a-sequence", 7, {"tea_id": "tea:v1:" + digest("dict")}):
        connection = FakeConnection()
        with pytest.raises(ValueError, match="rows"):
            attempt_store._insert_attempt_rows_atomic(connection, rows)
        assert connection.cursor_count == 0 and connection.cursor_instance.calls == []

    element_connection = FakeConnection()
    with pytest.raises(ValueError, match="TeamEvaluationAttemptDbRow"):
        attempt_store._insert_attempt_rows_atomic(
            element_connection, (attempt_row(seed="ok"), object())
        )
    assert element_connection.cursor_count == 0

    for table_name in ("schema.too.many.parts", "team_evaluation_attempts; drop table users"):
        table_connection = FakeConnection()
        with pytest.raises(ValueError, match="table_name"):
            attempt_store._insert_attempt_rows_atomic(
                table_connection, (attempt_row(seed="table"),), table_name=table_name
            )
        assert table_connection.cursor_count == 0


def test_private_writer_error_paths_close_cursor_and_never_commit() -> None:
    execute_error = RuntimeError("execute failed")
    single = FakeConnection(execute_errors=(execute_error,))
    close_failure = FakeConnection(
        execute_errors=(execute_error,), close_error=RuntimeError("close failed")
    )
    second_error = RuntimeError("second row failed")
    batch = FakeConnection(rowcounts=(1,), execute_errors=(None, second_error))

    with pytest.raises(RuntimeError) as single_info:
        attempt_store._insert_attempt_rows_atomic(
            single, (attempt_row(seed="execute-error"),)
        )
    with pytest.raises(RuntimeError) as close_info:
        attempt_store._insert_attempt_rows_atomic(
            close_failure, (attempt_row(seed="execute-close-error"),)
        )
    with pytest.raises(RuntimeError) as batch_info:
        attempt_store._insert_attempt_rows_atomic(
            batch, (attempt_row(seed="first-ok"), attempt_row(seed="second-fails"))
        )

    assert single_info.value is execute_error and close_info.value is execute_error
    assert batch_info.value is second_error
    assert len(batch.cursor_instance.calls) == 2
    for connection in (single, close_failure, batch):
        assert connection.cursor_instance.close_count == 1
        assert connection.commit_count == 0 and connection.rollback_count == 0


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"inserted": 1}, "inserted"),
        ({"paper_only": False}, "paper_only"),
        ({"report_only": False}, "report_only"),
        ({"readonly": False}, "readonly"),
        ({"row": object()}, "row must be a TeamEvaluationAttemptDbRow"),
    ),
)
def test_write_result_rejects_invalid_fields(
    kwargs: dict[str, Any], message: str
) -> None:
    values = {"row": attempt_row(seed="write-result"), "inserted": True} | kwargs

    with pytest.raises(ValueError, match=message):
        attempt_store.TeamEvaluationAttemptWriteResult(**values)


@pytest.mark.parametrize(
    ("row", "prefix"),
    (
        (FakeLegacyRow(tea_id="tea:v1:" + digest("legacy:tea")), "tea:v1:"),
        (FakeLegacyRow(tfr_id="tfr:v1:" + digest("legacy:tfr")), "tfr:v1:"),
        (FakeLegacyRow(tfe_id="tfe:v1:" + digest("legacy:tfe")), "tfe:v1:"),
        (None, "tea:v1:"),
        (FakeLegacyRow(evaluation_scope_payload={
            "nested": ["tfe:v1:" + digest("embedded")]}), "tfe:v1:"),
    ),
)
def test_legacy_insert_rejects_every_v1_identifier_before_cursor_activity(
    row: Any, prefix: str, writer_spy: list[tuple[Any, ...]]
) -> None:
    connection = FakeConnection()
    legacy_row = attempt_row(seed="legacy-real") if row is None else row

    with pytest.raises(ValueError, match=prefix):
        attempt_store.insert_team_evaluation_attempt(connection, legacy_row)

    assert connection.cursor_count == 0 and connection.cursor_instance.calls == []
    assert writer_spy == []


def test_legacy_insert_rejects_non_row_and_table_names_before_cursor(
    writer_spy: list[tuple[Any, ...]],
) -> None:
    non_row = FakeConnection()
    bad_table = FakeConnection()

    with pytest.raises(ValueError, match="TeamEvaluationAttemptDbRow"):
        attempt_store.insert_team_evaluation_attempt(non_row, FakeLegacyRow())
    with pytest.raises(ValueError, match="table_name"):
        attempt_store.insert_team_evaluation_attempt(
            bad_table,
            FakeLegacyRow(),
            table_name="team_evaluation_attempts; drop table users",
        )

    assert non_row.cursor_count == 0 and bad_table.cursor_count == 0
    assert non_row.cursor_instance.calls == [] and writer_spy == []


def test_private_writer_is_the_only_insert_sql_path() -> None:
    source = Path(attempt_store.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    insert_functions = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            isinstance(sub, ast.Constant) and isinstance(sub.value, str)
            and "INSERT INTO" in sub.value
            for sub in ast.walk(node)
        )
    }
    assert insert_functions == {"_insert_attempt_rows_atomic"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert "DO UPDATE" not in node.value and "DELETE" not in node.value
            assert "FOR UPDATE" not in node.value
        if isinstance(node, ast.Import):
            assert all("psycopg" not in alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module is None or "psycopg" not in node.module


def test_load_attempt_rows_filters_order_and_rebuilds_rows() -> None:
    ready = attempt_row(status="ready", seed="load-ready")
    connection = FakeConnection(rows=(row_record(ready),))

    rows = attempt_store.load_team_evaluation_attempt_rows(
        connection, tfr_id=ready.tfr_id, scope_version=SCOPE_VERSION,
        scope_key=ready.scope_key, limit=25,
        table_name="research.team_evaluation_attempts",
    )

    assert rows == (ready,)
    cursor = connection.cursor_instance
    assert cursor.close_count == 1
    assert connection.commit_count == 0 and connection.rollback_count == 0
    sql, params = cursor.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        expected_select(
            "research.team_evaluation_attempts",
            "WHERE tfr_id = %s AND scope_version = %s AND scope_key = %s",
            "LIMIT %s",
        )
    )
    assert params == (ready.tfr_id, SCOPE_VERSION, ready.scope_key, 25)


def test_load_attempt_rows_accepts_tfr_filter_and_positional_records() -> None:
    row = attempt_row(status="watch", seed="load-tfr-only")
    filtered = FakeConnection(rows=(row,))
    positional = FakeConnection(
        rows=(tuple(getattr(row, column) for column in ATTEMPT_COLUMNS),)
    )

    rows = attempt_store.load_team_evaluation_attempt_rows(filtered, tfr_id=row.tfr_id)
    positional_rows = attempt_store.load_team_evaluation_attempt_rows(positional)

    assert rows == (row,) and positional_rows == (row,)
    sql, params = filtered.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        expected_select(DEFAULT_TABLE, "WHERE tfr_id = %s", "")
    )
    assert "LIMIT" not in normalize_sql(sql) and params == (row.tfr_id,)


@pytest.mark.parametrize(
    ("status", "hard_flag"), (("ready", False), ("watch", False), ("blocked", True))
)
def test_load_attempt_rows_preserve_status_and_hard_flag(
    status: str, hard_flag: bool
) -> None:
    row = attempt_row(status=status, seed=f"load-{status}")
    assert row.status == status and row.hard_flag is hard_flag
    connection = FakeConnection(rows=(row_record(row),))

    loaded = attempt_store.load_team_evaluation_attempt_rows(connection)

    assert loaded == (row,)
    assert loaded[0].status == status and loaded[0].hard_flag is hard_flag
    assert loaded[0].paper_only is True and loaded[0].readonly is True


def test_latest_attempt_within_tfr_returns_newest_without_status_fallback() -> None:
    newest = attempt_row(
        status="blocked", seed="latest-blocked", tfr_seed="latest-run",
        evaluated_at=ATTEMPTED_AT_LATER)
    connection = FakeConnection(rows=(row_record(newest),))

    latest = attempt_store.load_latest_team_evaluation_attempt(
        connection, tfr_id=newest.tfr_id
    )

    assert latest == newest
    assert latest is not None
    assert latest.status == "blocked" and latest.hard_flag is True
    cursor = connection.cursor_instance
    assert cursor.close_count == 1 and connection.commit_count == 0
    sql, params = cursor.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        expected_select(DEFAULT_TABLE, "WHERE tfr_id = %s", "LIMIT 1")
    )
    assert params == (newest.tfr_id,)
    where_clause = normalize_sql(sql).split("WHERE", 1)[1].split("ORDER BY", 1)[0]
    assert "status" not in where_clause


def test_latest_attempt_within_scope_pair_orders_and_filters() -> None:
    row = attempt_row(status="watch", seed="latest-scope", evaluated_at=ATTEMPTED_AT)
    connection = FakeConnection(rows=(row_record(row),))

    latest = attempt_store.load_latest_team_evaluation_attempt(
        connection, scope_version=SCOPE_VERSION, scope_key=row.scope_key,
        table_name="research.team_evaluation_attempts",
    )

    assert latest == row
    assert latest is not None
    assert latest.status == "watch" and latest.hard_flag is False
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        expected_select(
            "research.team_evaluation_attempts",
            "WHERE scope_version = %s AND scope_key = %s",
            "LIMIT 1",
        )
    )
    assert params == (SCOPE_VERSION, row.scope_key)


def test_latest_attempt_returns_none_without_rows() -> None:
    connection = FakeConnection(rows=())

    latest = attempt_store.load_latest_team_evaluation_attempt(
        connection, tfr_id="tfr:v1:" + digest("empty-run")
    )

    assert latest is None and connection.cursor_instance.close_count == 1
    assert connection.commit_count == 0 and connection.rollback_count == 0


@pytest.mark.parametrize(
    "kwargs",
    (
        {},
        {"scope_version": SCOPE_VERSION},
        {"scope_key": digest("scope-only")},
        {"tfr_id": "tfr:v1:" + digest("run"), "scope_version": SCOPE_VERSION},
        {"tfr_id": "tfr:v1:" + digest("run"), "scope_key": digest("scope")},
    ),
)
def test_latest_attempt_rejects_incomplete_or_mixed_lookup_modes_before_cursor(
    kwargs: dict[str, Any],
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="latest"):
        attempt_store.load_latest_team_evaluation_attempt(connection, **kwargs)

    assert connection.cursor_count == 0 and connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"tfr_id": "run-1"}, "tfr_id"),
        ({"tfr_id": "tfr:v1:XYZ"}, "tfr_id"),
        ({"scope_version": SCOPE_VERSION, "scope_key": "not-hex"}, "scope_key"),
        ({"scope_version": " ", "scope_key": digest("space-version")}, "scope_version"),
    ),
)
def test_latest_attempt_rejects_invalid_identifier_values_before_cursor(
    kwargs: dict[str, Any], message: str
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        attempt_store.load_latest_team_evaluation_attempt(connection, **kwargs)

    assert connection.cursor_count == 0 and connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"tfr_id": "run-1"}, "tfr_id"),
        ({"tfr_id": "tfr:v1:" + digest("upper") + "0"}, "tfr_id"),
        ({"scope_version": ""}, "scope_version"),
        ({"scope_version": " leading-space"}, "scope_version"),
        ({"scope_key": "A" * 64}, "scope_key"),
        ({"scope_key": digest("scope") + "0"}, "scope_key"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
        ({"table_name": "schema.too.many.parts"}, "table_name"),
        ({"table_name": "team_evaluation_attempts; drop table users"}, "table_name"),
    ),
)
def test_load_attempt_rows_rejects_invalid_filters_before_cursor(
    kwargs: dict[str, Any], message: str
) -> None:
    connection = FakeConnection()
    kwargs.setdefault("table_name", DEFAULT_TABLE)

    with pytest.raises(ValueError, match=message):
        attempt_store.load_team_evaluation_attempt_rows(connection, **kwargs)

    assert connection.cursor_count == 0 and connection.cursor_instance.calls == []


def test_load_attempt_rows_error_paths_close_cursor_and_preserve_errors() -> None:
    fetchall_error = RuntimeError("fetchall failed")
    close_error = RuntimeError("close failed")
    fetchall_failure = FakeConnection(fetchall_error=fetchall_error, close_error=close_error)
    close_failure = FakeConnection(close_error=close_error)

    with pytest.raises(RuntimeError) as fetchall_info:
        attempt_store.load_team_evaluation_attempt_rows(fetchall_failure)
    with pytest.raises(RuntimeError) as close_info:
        attempt_store.load_team_evaluation_attempt_rows(close_failure)

    assert fetchall_info.value is fetchall_error and close_info.value is close_error
    assert fetchall_failure.cursor_instance.close_count == 1
    assert close_failure.cursor_instance.close_count == 1
    assert close_failure.cursor_instance.calls
