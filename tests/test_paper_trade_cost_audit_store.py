from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeReport:
    generated_at: datetime
    config_version: str
    trade_count: int


@dataclass(frozen=True)
class FakeDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    trade_count: int
    total_filled_size: Decimal
    total_requested_size: Decimal
    fill_rate: Decimal | None
    mean_theoretical_edge: Decimal | None
    mean_cost_adjusted_edge: Decimal | None
    mean_edge_cost_drag: Decimal | None
    total_edge_cost_drag: Decimal | None
    mean_research_slippage: Decimal | None
    mean_fill_slippage: Decimal | None
    partial_fill_count: int
    negative_cost_adjusted_edge_count: int
    largest_single_trade_cost_drag: Decimal | None
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class FakeCursor:
    def __init__(self, rows: tuple[Any, ...] = ()) -> None:
        self.rows = rows
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))

    def fetchall(self) -> tuple[Any, ...]:
        return self.rows

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, rows: tuple[Any, ...] = ()) -> None:
        self.cursor_instance = FakeCursor(rows)
        self.cursor_count = 0
        self.commit_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1


def d(value: str) -> Decimal:
    return Decimal(value)


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType("polymarket_alpha_lab.paper_trade_cost_audit_db_row")

    def to_db_row(report: FakeReport) -> FakeDbRow:
        return FakeDbRow(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            trade_count=report.trade_count,
            total_filled_size=d("240"),
            total_requested_size=d("300"),
            fill_rate=d("0.800000"),
            mean_theoretical_edge=d("0.060000"),
            mean_cost_adjusted_edge=d("0.030000"),
            mean_edge_cost_drag=d("0.030000"),
            total_edge_cost_drag=d("6.600000"),
            mean_research_slippage=d("0.004667"),
            mean_fill_slippage=d("0.009000"),
            partial_fill_count=1,
            negative_cost_adjusted_edge_count=1,
            largest_single_trade_cost_drag=d("3.000000"),
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "config_version": report.config_version,
                "trade_count": report.trade_count,
            },
        )

    def from_db_row(row: FakeDbRow) -> FakeReport:
        return FakeReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            trade_count=row.trade_count,
        )

    companion.PaperTradeCostAuditReportDbRow = FakeDbRow
    companion.paper_trade_cost_audit_report_to_db_row = to_db_row
    companion.paper_trade_cost_audit_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_trade_cost_audit_db_row",
        companion,
    )
    sys.modules.pop("polymarket_alpha_lab.paper_trade_cost_audit_store", None)
    return importlib.import_module("polymarket_alpha_lab.paper_trade_cost_audit_store")


def test_insert_report_uses_parameterized_insert_without_commit(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 0, 30, tzinfo=UTC)
    connection = FakeConnection()
    report = FakeReport(
        generated_at=generated_at,
        config_version="paper-trade-cost-audit-db-v0",
        trade_count=3,
    )

    inserted = store_module.insert_paper_trade_cost_audit_report(connection, report)

    assert inserted == FakeDbRow(
        report_sha256="a" * 64,
        generated_at=generated_at,
        config_version="paper-trade-cost-audit-db-v0",
        trade_count=3,
        total_filled_size=d("240"),
        total_requested_size=d("300"),
        fill_rate=d("0.800000"),
        mean_theoretical_edge=d("0.060000"),
        mean_cost_adjusted_edge=d("0.030000"),
        mean_edge_cost_drag=d("0.030000"),
        total_edge_cost_drag=d("6.600000"),
        mean_research_slippage=d("0.004667"),
        mean_fill_slippage=d("0.009000"),
        partial_fill_count=1,
        negative_cost_adjusted_edge_count=1,
        largest_single_trade_cost_drag=d("3.000000"),
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": "paper-trade-cost-audit-db-v0",
            "trade_count": 3,
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_trade_cost_audit_reports (
            report_sha256,
            generated_at,
            config_version,
            trade_count,
            total_filled_size,
            total_requested_size,
            fill_rate,
            mean_theoretical_edge,
            mean_cost_adjusted_edge,
            mean_edge_cost_drag,
            total_edge_cost_drag,
            mean_research_slippage,
            mean_fill_slippage,
            partial_fill_count,
            negative_cost_adjusted_edge_count,
            largest_single_trade_cost_drag,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        generated_at,
        "paper-trade-cost-audit-db-v0",
        3,
        d("240"),
        d("300"),
        d("0.800000"),
        d("0.060000"),
        d("0.030000"),
        d("0.030000"),
        d("6.600000"),
        d("0.004667"),
        d("0.009000"),
        1,
        1,
        d("3.000000"),
        {
            "generated_at": generated_at.isoformat(),
            "config_version": "paper-trade-cost-audit-db-v0",
            "trade_count": 3,
        },
        True,
        True,
        True,
    )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_trade_cost_audit_report(
            connection,
            FakeReport(
                generated_at=datetime(2026, 6, 20, 0, 30, tzinfo=UTC),
                config_version="paper-trade-cost-audit-db-v0",
                trade_count=0,
            ),
            table_name="paper_trade_cost_audit_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_reports_filters_limits_orders_and_maps_dict_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 0, 45, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": "b" * 64,
                "generated_at": generated_at,
                "config_version": "paper-trade-cost-audit-db-v0",
                "trade_count": 3,
                "total_filled_size": d("240"),
                "total_requested_size": d("300"),
                "fill_rate": d("0.800000"),
                "mean_theoretical_edge": d("0.060000"),
                "mean_cost_adjusted_edge": d("0.030000"),
                "mean_edge_cost_drag": d("0.030000"),
                "total_edge_cost_drag": d("6.600000"),
                "mean_research_slippage": d("0.004667"),
                "mean_fill_slippage": d("0.009000"),
                "partial_fill_count": 1,
                "negative_cost_adjusted_edge_count": 1,
                "largest_single_trade_cost_drag": d("3.000000"),
                "payload_json": {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-trade-cost-audit-db-v0",
                    "trade_count": 3,
                },
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )

    reports = store_module.load_paper_trade_cost_audit_reports(
        connection,
        config_version="paper-trade-cost-audit-db-v0",
        limit=25,
        table_name="public.paper_trade_cost_audit_reports",
    )

    assert reports == (
        FakeReport(
            generated_at=generated_at,
            config_version="paper-trade-cost-audit-db-v0",
            trade_count=3,
        ),
    )
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            report_sha256,
            generated_at,
            config_version,
            trade_count,
            total_filled_size,
            total_requested_size,
            fill_rate,
            mean_theoretical_edge,
            mean_cost_adjusted_edge,
            mean_edge_cost_drag,
            total_edge_cost_drag,
            mean_research_slippage,
            mean_fill_slippage,
            partial_fill_count,
            negative_cost_adjusted_edge_count,
            largest_single_trade_cost_drag,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM public.paper_trade_cost_audit_reports
        WHERE config_version = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-trade-cost-audit-db-v0", 25)


def test_load_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 0, 45, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-trade-cost-audit-db-v0",
                0,
                d("0"),
                d("0"),
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                0,
                0,
                None,
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-trade-cost-audit-db-v0",
                    "trade_count": 0,
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_trade_cost_audit_reports(connection)

    assert reports == (
        FakeReport(
            generated_at=generated_at,
            config_version="paper-trade-cost-audit-db-v0",
            trade_count=0,
        ),
    )


def test_load_reports_accepts_single_character_schema_and_table_names(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    reports = store_module.load_paper_trade_cost_audit_reports(
        connection,
        table_name="a.b",
    )

    assert reports == ()
    assert connection.cursor_count == 1
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert "FROM a.b" in normalize_sql(sql)
    assert params == ()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "Public.paper_trade_cost_audit_reports"}, "table_name"),
        ({"table_name": "public.audit.reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"table_name": "public." + ("a" * 64)}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-trade-cost-audit-db-v0"}, "config_version"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_rejects_invalid_query_inputs_without_executing_sql(
    store_module: types.ModuleType,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store_module.load_paper_trade_cost_audit_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
