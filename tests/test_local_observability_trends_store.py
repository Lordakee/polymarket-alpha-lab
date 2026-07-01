from __future__ import annotations

from collections import namedtuple
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

import pytest

from polymarket_alpha_lab.local_observability_trends import (
    LocalObservabilityTrendsReport,
)
from polymarket_alpha_lab.local_observability_trends_db_row import (
    LocalObservabilityTrendsDbRow,
    local_observability_trends_report_to_db_row,
)
from polymarket_alpha_lab.local_observability_trends_store import (
    DEFAULT_LOCAL_OBSERVABILITY_TRENDS_TABLE,
    insert_local_observability_trends_report,
    load_local_observability_trends_reports,
)
from polymarket_alpha_lab.nav_risk_trend import (
    PaperNavRiskTrendConfig,
    build_paper_nav_risk_trend_report,
)
from polymarket_alpha_lab.outcome_freshness import (
    OutcomeFreshnessConfig,
    build_outcome_freshness_report,
)
from polymarket_alpha_lab.paper_trade_cost_trend import (
    PaperTradeCostTrendConfig,
    build_paper_trade_cost_trend_report,
)
from polymarket_alpha_lab.strategy_evidence_trend import (
    PaperStrategyEvidenceTrendConfig,
    build_paper_strategy_evidence_trend_report,
)


GENERATED_AT = datetime(2026, 6, 20, 18, 30, tzinfo=UTC)
SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "strategy_evidence_snapshot_count",
    "strategy_evidence_latest_status",
    "outcome_freshness_status",
    "outcome_report_count",
    "nav_risk_status",
    "nav_risk_report_count",
    "paper_trade_cost_status",
    "paper_trade_cost_report_count",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
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


def _report() -> LocalObservabilityTrendsReport:
    return LocalObservabilityTrendsReport(
        generated_at=GENERATED_AT,
        config_version="local-observability-trends-v0",
        strategy_evidence_trend=build_paper_strategy_evidence_trend_report(
            (),
            config=PaperStrategyEvidenceTrendConfig(
                config_version="strategy-evidence-trend-v0",
            ),
            generated_at=GENERATED_AT,
        ),
        outcome_freshness=build_outcome_freshness_report(
            (),
            config=OutcomeFreshnessConfig(
                config_version="outcome-freshness-v0",
                stale_after_seconds=60,
            ),
            generated_at=GENERATED_AT,
        ),
        nav_risk_trend=build_paper_nav_risk_trend_report(
            (),
            config=PaperNavRiskTrendConfig(config_version="nav-risk-trend-v0"),
            generated_at=GENERATED_AT,
        ),
        paper_trade_cost_trend=build_paper_trade_cost_trend_report(
            (),
            config=PaperTradeCostTrendConfig(
                config_version="paper-trade-cost-trend-v0",
            ),
            generated_at=GENERATED_AT,
        ),
    )


def _row() -> LocalObservabilityTrendsDbRow:
    return local_observability_trends_report_to_db_row(_report())


def _row_values(row: LocalObservabilityTrendsDbRow) -> tuple[Any, ...]:
    return tuple(getattr(row, column) for column in SELECT_COLUMNS)


def test_insert_local_observability_trends_report_uses_parameterized_insert() -> None:
    connection = FakeConnection()
    report = _report()
    expected_row = local_observability_trends_report_to_db_row(report)

    inserted = insert_local_observability_trends_report(connection, report)

    assert inserted == expected_row
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO local_observability_trends_reports (
            report_sha256,
            generated_at,
            config_version,
            strategy_evidence_snapshot_count,
            strategy_evidence_latest_status,
            outcome_freshness_status,
            outcome_report_count,
            nav_risk_status,
            nav_risk_report_count,
            paper_trade_cost_status,
            paper_trade_cost_report_count,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == _row_values(expected_row)


def test_insert_local_observability_trends_report_preserves_execute_error_when_close_fails() -> None:
    execute_error = RuntimeError("execute failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(execute_error=execute_error, close_error=close_error)

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        insert_local_observability_trends_report(connection, _report())

    assert exc_info.value is execute_error
    assert connection.cursor_instance.closed is True


def test_load_local_observability_trends_reports_selects_latest_reports_with_limit() -> None:
    row = _row()
    connection = FakeConnection(rows=(row,))

    reports = load_local_observability_trends_reports(
        connection,
        limit=25,
        table_name="audit.local_observability_trends_reports",
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
            strategy_evidence_snapshot_count,
            strategy_evidence_latest_status,
            outcome_freshness_status,
            outcome_report_count,
            nav_risk_status,
            nav_risk_report_count,
            paper_trade_cost_status,
            paper_trade_cost_report_count,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM audit.local_observability_trends_reports
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (25,)


def test_load_local_observability_trends_reports_propagates_close_error_after_success() -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(rows=(_row(),), close_error=close_error)

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        load_local_observability_trends_reports(connection)

    assert exc_info.value is close_error
    assert connection.cursor_instance.closed is True


def test_load_local_observability_trends_reports_accepts_positional_rows() -> None:
    row = _row()
    connection = FakeConnection(rows=(_row_values(row),))

    reports = load_local_observability_trends_reports(connection)

    assert reports == (_report(),)


def test_load_local_observability_trends_reports_accepts_dict_rows_without_mutation() -> None:
    row = _row()
    payload_before = deepcopy(row.payload_json)
    record = dict(zip(SELECT_COLUMNS, _row_values(row), strict=True))
    connection = FakeConnection(rows=(record,))

    reports = load_local_observability_trends_reports(connection)

    assert reports == (_report(),)
    assert record["payload_json"] == payload_before


def test_load_local_observability_trends_reports_accepts_namedtuple_like_rows() -> None:
    row = _row()
    Record = namedtuple("Record", SELECT_COLUMNS)
    connection = FakeConnection(rows=(Record(*_row_values(row)),))

    reports = load_local_observability_trends_reports(connection)

    assert reports == (_report(),)


def test_load_local_observability_trends_reports_accepts_db_row_objects() -> None:
    row = _row()
    connection = FakeConnection(rows=(row,))

    reports = load_local_observability_trends_reports(connection)

    assert reports == (_report(),)


@pytest.mark.parametrize(
    "table_name",
    [
        "local_observability_trends_reports; drop table users",
        "LocalObservabilityTrendsReports",
        "audit.LocalObservabilityTrendsReports",
        "_local_observability_trends_reports",
        "audit._local_observability_trends_reports",
        "local_observability_trends_reports_",
        "public.audit.local_observability_trends_reports",
        "public." + "a" + ("b" * 62) + "1",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    table_name: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        insert_local_observability_trends_report(
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

    insert_local_observability_trends_report(
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
        "audit.local_observability_trends_reports",
    ],
)
def test_load_accepts_lowercase_optional_schema_table_names(
    table_name: str,
) -> None:
    connection = FakeConnection()

    load_local_observability_trends_reports(connection, table_name=table_name)

    sql, _params = connection.cursor_instance.calls[0]
    assert f"FROM {table_name}" in sql


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "public.audit.local_observability_trends_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        (
            {
                "table_name": (
                    "public." + "a" + ("b" * 62) + "1"
                ),
            },
            "table_name",
        ),
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
        load_local_observability_trends_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_and_store_functions() -> None:
    assert DEFAULT_LOCAL_OBSERVABILITY_TRENDS_TABLE == (
        "local_observability_trends_reports"
    )
