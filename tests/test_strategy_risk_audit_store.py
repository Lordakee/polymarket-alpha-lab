from __future__ import annotations

from collections import namedtuple
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)
from polymarket_alpha_lab.strategy_risk_audit_db_row import (
    PaperStrategyRiskAuditReportDbRow,
    strategy_risk_audit_report_to_db_row,
)
from polymarket_alpha_lab.strategy_risk_audit_store import (
    DEFAULT_STRATEGY_RISK_AUDIT_REPORTS_TABLE,
    insert_strategy_risk_audit_report,
    load_strategy_risk_audit_reports,
)


GENERATED_AT = datetime(2026, 6, 20, 19, 30, tzinfo=UTC)
SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "status",
    "gate_count",
    "pass_count",
    "fail_count",
    "incomplete_count",
    "gate_results_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)
GATE_NAMES = (
    "paper_history",
    "settlement_evidence",
    "forecast_quality",
    "cost_discipline",
    "nav_drawdown",
    "open_exposure",
)


class FakeCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        execute_error: BaseException | None = None,
        fetchall_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.rows = rows
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
        *,
        execute_error: BaseException | None = None,
        fetchall_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(
            rows,
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


def _report() -> PaperStrategyRiskAuditReport:
    gate_results = tuple(
        PaperStrategyRiskAuditGateResult(
            gate_name=gate_name,
            status="pass",
            message=f"{gate_name} message",
            observed_value=f"{gate_name}=observed",
            threshold=f"{gate_name}=threshold",
        )
        for gate_name in GATE_NAMES
    )
    return PaperStrategyRiskAuditReport(
        generated_at=GENERATED_AT,
        config_version="strategy-risk-audit-v0",
        status="audit_ready",
        gate_count=6,
        pass_count=6,
        fail_count=0,
        incomplete_count=0,
        gate_results=gate_results,
    )


def _row() -> PaperStrategyRiskAuditReportDbRow:
    return strategy_risk_audit_report_to_db_row(_report())


def _row_values(row: PaperStrategyRiskAuditReportDbRow) -> tuple[Any, ...]:
    return tuple(getattr(row, column) for column in SELECT_COLUMNS)


def test_insert_strategy_risk_audit_report_uses_parameterized_insert() -> None:
    connection = FakeConnection()
    report = _report()
    expected_row = _row()

    inserted = insert_strategy_risk_audit_report(connection, report)

    assert inserted == expected_row
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO strategy_risk_audit_reports (
            report_sha256,
            generated_at,
            config_version,
            status,
            gate_count,
            pass_count,
            fail_count,
            incomplete_count,
            gate_results_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == _row_values(expected_row)


def test_insert_strategy_risk_audit_report_preserves_execute_error_when_close_fails() -> None:
    execute_error = RuntimeError("execute failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(execute_error=execute_error, close_error=close_error)

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        insert_strategy_risk_audit_report(connection, _report())

    assert exc_info.value is execute_error
    assert connection.cursor_instance.closed is True


def test_load_strategy_risk_audit_reports_filters_by_config_version_and_limit() -> None:
    row = _row()
    connection = FakeConnection(rows=(row,))

    reports = load_strategy_risk_audit_reports(
        connection,
        config_version="strategy-risk-audit-v0",
        limit=25,
        table_name="audit.strategy_risk_audit_reports",
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
            status,
            gate_count,
            pass_count,
            fail_count,
            incomplete_count,
            gate_results_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM audit.strategy_risk_audit_reports
        WHERE config_version = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("strategy-risk-audit-v0", 25)


def test_load_strategy_risk_audit_reports_propagates_close_error_after_success() -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(rows=(_row(),), close_error=close_error)

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        load_strategy_risk_audit_reports(connection)

    assert exc_info.value is close_error
    assert connection.cursor_instance.closed is True


def test_load_strategy_risk_audit_reports_accepts_positional_rows() -> None:
    row = _row()
    connection = FakeConnection(rows=(_row_values(row),))

    reports = load_strategy_risk_audit_reports(connection)

    assert reports == (_report(),)


def test_load_strategy_risk_audit_reports_accepts_dict_rows_without_mutation() -> None:
    row = _row()
    payload_before = deepcopy(row.payload_json)
    gate_results_before = deepcopy(row.gate_results_json)
    record = dict(zip(SELECT_COLUMNS, _row_values(row), strict=True))
    connection = FakeConnection(rows=(record,))

    reports = load_strategy_risk_audit_reports(connection)

    assert reports == (_report(),)
    assert record["payload_json"] == payload_before
    assert record["gate_results_json"] == gate_results_before


def test_load_strategy_risk_audit_reports_accepts_namedtuple_like_rows() -> None:
    row = _row()
    Record = namedtuple("Record", SELECT_COLUMNS)
    connection = FakeConnection(rows=(Record(*_row_values(row)),))

    reports = load_strategy_risk_audit_reports(connection)

    assert reports == (_report(),)


def test_load_strategy_risk_audit_reports_accepts_db_row_objects() -> None:
    row = _row()
    connection = FakeConnection(rows=(row,))

    reports = load_strategy_risk_audit_reports(connection)

    assert reports == (_report(),)


@pytest.mark.parametrize(
    "table_name",
    [
        "strategy_risk_audit_reports; drop table users",
        "StrategyRiskAuditReports",
        "audit.StrategyRiskAuditReports",
        "_strategy_risk_audit_reports",
        "audit._strategy_risk_audit_reports",
        "strategy_risk_audit_reports_",
        "public.audit.strategy_risk_audit_reports",
        "public." + "a" + ("b" * 62) + "1",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    table_name: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        insert_strategy_risk_audit_report(
            connection,
            _report(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_insert_accepts_lowercase_optional_schema_table_names_with_63_byte_parts() -> None:
    connection = FakeConnection()
    max_length_part = "a" + ("b" * 61) + "1"
    assert len(max_length_part.encode("utf-8")) == 63

    insert_strategy_risk_audit_report(
        connection,
        _report(),
        table_name=f"a.{max_length_part}",
    )

    sql, _params = connection.cursor_instance.calls[0]
    assert f"INSERT INTO a.{max_length_part}" in sql


@pytest.mark.parametrize(
    "table_name",
    [
        "a",
        "a.b",
        "audit.strategy_risk_audit_reports",
    ],
)
def test_load_accepts_lowercase_optional_schema_table_names(table_name: str) -> None:
    connection = FakeConnection()

    load_strategy_risk_audit_reports(connection, table_name=table_name)

    sql, _params = connection.cursor_instance.calls[0]
    assert f"FROM {table_name}" in sql


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "public.audit.strategy_risk_audit_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"table_name": "public." + "a" + ("b" * 62) + "1"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " strategy-risk-audit-v0"}, "config_version"),
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
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        load_strategy_risk_audit_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_and_store_functions() -> None:
    assert DEFAULT_STRATEGY_RISK_AUDIT_REPORTS_TABLE == (
        "strategy_risk_audit_reports"
    )
