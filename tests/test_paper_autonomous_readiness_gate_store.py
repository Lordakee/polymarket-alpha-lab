from __future__ import annotations

from collections import namedtuple
from copy import deepcopy
from typing import Any

import pytest

from polymarket_alpha_lab.paper_autonomous_readiness_gate import (
    ALLOCATION_SOURCE_NAME,
    INVESTMENT_LEDGER_SOURCE_NAME,
    SCREENING_SOURCE_NAME,
    STRATEGY_RISK_AUDIT_HISTORY_GATE_SOURCE_NAME,
)
from tests.test_paper_autonomous_readiness_gate_db_row import _report


SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "readiness_status",
    "recommended_next_step",
    "source_statuses_json",
    "source_config_versions_json",
    "reason_code_counts_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


class FakeCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        rowcount: int = 1,
        *,
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.rows = rows
        self.rowcount = rowcount
        self.execute_error = execute_error
        self.fetchall_error = fetchall_error
        self.close_error = close_error
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchall(self) -> tuple[Any, ...]:
        if self.fetchall_error is not None:
            raise self.fetchall_error
        return self.rows

    def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FakeConnection:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        rowcount: int = 1,
        *,
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(
            rows,
            rowcount,
            execute_error=execute_error,
            fetchall_error=fetchall_error,
            close_error=close_error,
        )
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


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def _db_row():
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_db_row import (
        paper_autonomous_readiness_gate_report_to_db_row,
    )

    return paper_autonomous_readiness_gate_report_to_db_row(_report())


def _row_values(row: object) -> tuple[Any, ...]:
    return tuple(getattr(row, column) for column in SELECT_COLUMNS)


def test_insert_readiness_gate_report_uses_parameterized_insert() -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        insert_paper_autonomous_readiness_gate_report,
    )

    connection = FakeConnection()
    report = _report()
    expected_row = _db_row()

    inserted = insert_paper_autonomous_readiness_gate_report(connection, report)

    assert inserted == expected_row
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_autonomous_readiness_gate_reports (
            report_sha256,
            generated_at,
            config_version,
            readiness_status,
            recommended_next_step,
            source_statuses_json,
            source_config_versions_json,
            reason_code_counts_json,
            reason_codes_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == _row_values(expected_row)
    assert "paper-autonomous-readiness-gate-test-v0" not in sql
    assert "screening-health-v0" not in sql
    assert "allocation-trend-gate-v0" not in sql
    assert "ledger-trend-gate-v0" not in sql
    assert "throttle_paper_autonomous_readiness_review" not in sql


def test_insert_readiness_gate_report_with_result_observes_duplicate() -> None:
    import polymarket_alpha_lab.paper_autonomous_readiness_gate_store as store

    report = _report()
    expected_row = _db_row()

    inserted = store.insert_paper_autonomous_readiness_gate_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = store.insert_paper_autonomous_readiness_gate_report_with_result(
        FakeConnection(rowcount=0),
        report,
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_insert_readiness_gate_report_rejects_unexpected_rowcount() -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        insert_paper_autonomous_readiness_gate_report_with_result,
    )

    with pytest.raises(ValueError, match="rowcount"):
        insert_paper_autonomous_readiness_gate_report_with_result(
            FakeConnection(rowcount=2),
            _report(),
        )


def test_insert_preserves_execute_exception_when_cursor_close_fails() -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        insert_paper_autonomous_readiness_gate_report_with_result,
    )

    execute_error = RuntimeError("execute failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        execute_error=execute_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        insert_paper_autonomous_readiness_gate_report_with_result(
            connection,
            _report(),
        )

    assert exc_info.value is execute_error
    assert connection.cursor_instance.closed is True


def test_insert_raises_cursor_close_error_after_successful_execute() -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        insert_paper_autonomous_readiness_gate_report_with_result,
    )

    close_error = RuntimeError("close failed")

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        insert_paper_autonomous_readiness_gate_report_with_result(
            FakeConnection(close_error=close_error),
            _report(),
        )

    assert exc_info.value is close_error


def test_load_readiness_gate_reports_filters_in_deterministic_order() -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        load_paper_autonomous_readiness_gate_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_paper_autonomous_readiness_gate_reports(
        connection,
        config_version="paper-autonomous-readiness-gate-test-v0",
        readiness_status="watch",
        screening_config_version="screening-health-v0",
        strategy_cycle_history_gate_config_version="strategy-cycle-history-gate-v0",
        strategy_risk_audit_history_gate_config_version=(
            "strategy-risk-audit-history-gate-v0"
        ),
        allocation_config_version="allocation-trend-gate-v0",
        investment_ledger_config_version="ledger-trend-gate-v0",
        limit=25,
        table_name="readiness_gate_archive",
    )

    assert reports == (_report(),)
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            report_sha256,
            generated_at,
            config_version,
            readiness_status,
            recommended_next_step,
            source_statuses_json,
            source_config_versions_json,
            reason_code_counts_json,
            reason_codes_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM readiness_gate_archive
        WHERE config_version = %s AND readiness_status = %s
            AND source_config_versions_json @> %s
            AND source_config_versions_json @> %s
            AND source_config_versions_json @> %s
            AND source_config_versions_json @> %s
            AND source_config_versions_json @> %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (
        "paper-autonomous-readiness-gate-test-v0",
        "watch",
        [[SCREENING_SOURCE_NAME, "screening-health-v0"]],
        [["strategy_cycle_report_history_gate", "strategy-cycle-history-gate-v0"]],
        [
            [
                STRATEGY_RISK_AUDIT_HISTORY_GATE_SOURCE_NAME,
                "strategy-risk-audit-history-gate-v0",
            ],
        ],
        [[ALLOCATION_SOURCE_NAME, "allocation-trend-gate-v0"]],
        [[INVESTMENT_LEDGER_SOURCE_NAME, "ledger-trend-gate-v0"]],
        25,
    )


def test_load_preserves_fetchall_exception_when_cursor_close_fails() -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        load_paper_autonomous_readiness_gate_reports,
    )

    fetchall_error = RuntimeError("fetchall failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        fetchall_error=fetchall_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError, match="fetchall failed") as exc_info:
        load_paper_autonomous_readiness_gate_reports(connection)

    assert exc_info.value is fetchall_error
    assert connection.cursor_instance.closed is True


def test_load_raises_cursor_close_error_after_successful_fetch() -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        load_paper_autonomous_readiness_gate_reports,
    )

    close_error = RuntimeError("close failed")

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        load_paper_autonomous_readiness_gate_reports(
            FakeConnection(close_error=close_error),
        )

    assert exc_info.value is close_error


def test_load_readiness_gate_reports_filters_strategy_cycle_history_gate_source() -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        load_paper_autonomous_readiness_gate_reports,
    )

    connection = FakeConnection()

    reports = load_paper_autonomous_readiness_gate_reports(
        connection,
        strategy_cycle_history_gate_config_version="strategy-cycle-history-gate-v0",
    )

    assert reports == ()
    sql, params = connection.cursor_instance.calls[0]
    assert "source_config_versions_json @> %s" in sql
    assert [
        ["strategy_cycle_report_history_gate", "strategy-cycle-history-gate-v0"],
    ] in params


def test_load_readiness_gate_reports_filters_strategy_risk_audit_history_gate_source() -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        load_paper_autonomous_readiness_gate_reports,
    )

    connection = FakeConnection()

    reports = load_paper_autonomous_readiness_gate_reports(
        connection,
        strategy_risk_audit_history_gate_config_version=(
            "strategy-risk-audit-history-gate-v0"
        ),
    )

    assert reports == ()
    sql, params = connection.cursor_instance.calls[0]
    assert "source_config_versions_json @> %s" in sql
    assert [
        [
            STRATEGY_RISK_AUDIT_HISTORY_GATE_SOURCE_NAME,
            "strategy-risk-audit-history-gate-v0",
        ],
    ] in params


def test_load_readiness_gate_reports_accepts_positional_rows() -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        load_paper_autonomous_readiness_gate_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(_row_values(row),))

    reports = load_paper_autonomous_readiness_gate_reports(connection)

    assert reports == (_report(),)


def test_load_readiness_gate_reports_accepts_dict_rows_without_mutation() -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        load_paper_autonomous_readiness_gate_reports,
    )

    row = _db_row()
    payload_before = deepcopy(row.payload_json)
    config_versions_before = deepcopy(row.source_config_versions_json)
    record = dict(zip(SELECT_COLUMNS, _row_values(row), strict=True))
    connection = FakeConnection(rows=(record,))

    reports = load_paper_autonomous_readiness_gate_reports(connection)

    assert reports == (_report(),)
    assert record["payload_json"] == payload_before
    assert record["source_config_versions_json"] == config_versions_before


def test_load_readiness_gate_reports_accepts_namedtuple_like_rows() -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        load_paper_autonomous_readiness_gate_reports,
    )

    row = _db_row()
    Record = namedtuple("Record", SELECT_COLUMNS)
    connection = FakeConnection(rows=(Record(*_row_values(row)),))

    reports = load_paper_autonomous_readiness_gate_reports(connection)

    assert reports == (_report(),)


def test_load_readiness_gate_reports_accepts_db_row_objects() -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        load_paper_autonomous_readiness_gate_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_paper_autonomous_readiness_gate_reports(connection)

    assert reports == (_report(),)


@pytest.mark.parametrize(
    "table_name",
    [
        "paper_autonomous_readiness_gate_reports; drop table users",
        "audit.paper_autonomous_readiness_gate_reports",
        "PaperAutonomousReadinessGateReports",
        "_paper_autonomous_readiness_gate_reports",
        "paper_autonomous_readiness_gate_reports_",
        "a",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    table_name: str,
) -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        insert_paper_autonomous_readiness_gate_report,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        insert_paper_autonomous_readiness_gate_report(
            connection,
            _report(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "readiness_gate_archive",
        "gate_1_archive_2",
    ],
)
def test_load_accepts_simple_lowercase_table_names(table_name: str) -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        load_paper_autonomous_readiness_gate_reports,
    )

    connection = FakeConnection()

    load_paper_autonomous_readiness_gate_reports(connection, table_name=table_name)

    sql, _params = connection.cursor_instance.calls[0]
    assert f"FROM {table_name}" in sql


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "audit.readiness_gate_archive"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"table_name": "a"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " gate-v0"}, "config_version"),
        ({"readiness_status": "paused"}, "readiness_status"),
        ({"readiness_status": True}, "readiness_status"),
        ({"screening_config_version": ""}, "screening_config_version"),
        (
            {"strategy_cycle_history_gate_config_version": ""},
            "strategy_cycle_history_gate_config_version",
        ),
        (
            {"strategy_risk_audit_history_gate_config_version": ""},
            "strategy_risk_audit_history_gate_config_version",
        ),
        ({"allocation_config_version": ""}, "allocation_config_version"),
        ({"investment_ledger_config_version": ""}, "investment_ledger_config_version"),
        ({"limit": 0}, "limit"),
        ({"limit": -1}, "limit"),
        ({"limit": True}, "limit"),
        ({"limit": "5"}, "limit"),
    ),
)
def test_load_rejects_invalid_query_inputs_before_cursor_creation(
    kwargs: dict[str, Any],
    message: str,
) -> None:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate_store import (
        load_paper_autonomous_readiness_gate_reports,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        load_paper_autonomous_readiness_gate_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_and_store_functions() -> None:
    import polymarket_alpha_lab.paper_autonomous_readiness_gate_store as store

    assert (
        store.DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE
        == "paper_autonomous_readiness_gate_reports"
    )
    assert "insert_paper_autonomous_readiness_gate_report" in store.__all__
    assert "load_paper_autonomous_readiness_gate_reports" in store.__all__
