from __future__ import annotations

import ast
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.paper_trade_cost_audit_db_history_load as db_history_load
from polymarket_alpha_lab.paper_trade_cost_audit import PaperTradeCostAuditReport


GENERATED_AT = datetime(2026, 6, 21, 10, 0, tzinfo=UTC)
HISTORY_CONFIG_VERSION = "paper-trade-cost-audit-db-history-load-v0"


def _report(
    *,
    generated_at: datetime,
    trade_count: int = 4,
    fill_rate: Decimal = Decimal("1.000000"),
    mean_theoretical_edge: Decimal = Decimal("0.060000"),
    mean_cost_adjusted_edge: Decimal = Decimal("0.040000"),
    mean_edge_cost_drag: Decimal = Decimal("0.020000"),
    total_edge_cost_drag: Decimal = Decimal("8.000000"),
    partial_fill_count: int = 0,
    negative_cost_adjusted_edge_count: int = 0,
) -> PaperTradeCostAuditReport:
    if trade_count == 0:
        return PaperTradeCostAuditReport(
            generated_at=generated_at,
            config_version="paper-trade-cost-audit-v0",
            trade_count=0,
            total_filled_size=Decimal("0"),
            total_requested_size=Decimal("0"),
            fill_rate=None,
            mean_theoretical_edge=None,
            mean_cost_adjusted_edge=None,
            mean_edge_cost_drag=None,
            total_edge_cost_drag=None,
            mean_research_slippage=None,
            mean_fill_slippage=None,
            partial_fill_count=0,
            negative_cost_adjusted_edge_count=0,
            largest_single_trade_cost_drag=None,
        )

    requested_size = Decimal(trade_count * 100).quantize(Decimal("0.0001"))
    total_filled_size = (requested_size * fill_rate).quantize(Decimal("0.000001"))
    return PaperTradeCostAuditReport(
        generated_at=generated_at,
        config_version="paper-trade-cost-audit-v0",
        trade_count=trade_count,
        total_filled_size=total_filled_size,
        total_requested_size=requested_size,
        fill_rate=fill_rate,
        mean_theoretical_edge=mean_theoretical_edge,
        mean_cost_adjusted_edge=mean_cost_adjusted_edge,
        mean_edge_cost_drag=mean_edge_cost_drag,
        total_edge_cost_drag=total_edge_cost_drag,
        mean_research_slippage=Decimal("0.004000"),
        mean_fill_slippage=Decimal("0.006000"),
        partial_fill_count=partial_fill_count,
        negative_cost_adjusted_edge_count=negative_cost_adjusted_edge_count,
        largest_single_trade_cost_drag=Decimal("2.000000"),
    )


def test_load_paper_trade_cost_audit_db_history_builds_from_store_desc_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    calls: list[tuple[Any, int | None, str]] = []

    def load_reports(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "paper_trade_cost_audit_reports",
    ) -> tuple[PaperTradeCostAuditReport, ...]:
        calls.append((connection_arg, limit, table_name))
        return (
            _report(
                generated_at=datetime(2026, 6, 21, 9, 0, tzinfo=UTC),
                trade_count=5,
                fill_rate=Decimal("0.800000"),
                mean_theoretical_edge=Decimal("0.080000"),
                mean_cost_adjusted_edge=Decimal("-0.020000"),
                mean_edge_cost_drag=Decimal("0.100000"),
                total_edge_cost_drag=Decimal("10.000000"),
                partial_fill_count=1,
                negative_cost_adjusted_edge_count=1,
            ),
            _report(
                generated_at=datetime(2026, 6, 21, 8, 0, tzinfo=UTC),
                trade_count=3,
                fill_rate=Decimal("0.666667"),
                mean_theoretical_edge=Decimal("0.060000"),
                mean_cost_adjusted_edge=Decimal("-0.010000"),
                mean_edge_cost_drag=Decimal("0.070000"),
                total_edge_cost_drag=Decimal("6.000000"),
                partial_fill_count=2,
                negative_cost_adjusted_edge_count=2,
            ),
            _report(
                generated_at=datetime(2026, 6, 21, 7, 0, tzinfo=UTC),
                trade_count=2,
                fill_rate=Decimal("0.500000"),
                mean_theoretical_edge=Decimal("0.030000"),
                mean_cost_adjusted_edge=Decimal("0.020000"),
                mean_edge_cost_drag=Decimal("0.010000"),
                total_edge_cost_drag=Decimal("1.000000"),
                partial_fill_count=1,
                negative_cost_adjusted_edge_count=0,
            ),
        )

    monkeypatch.setattr(
        db_history_load.paper_trade_cost_audit_store,
        "load_paper_trade_cost_audit_reports",
        load_reports,
    )

    history = db_history_load.load_paper_trade_cost_audit_db_history_report(
        generated_at=GENERATED_AT,
        config_version=HISTORY_CONFIG_VERSION,
        connection=connection,
        limit=25,
        table_name="paper_trade_cost_archive",
    )

    assert calls == [(connection, 25, "paper_trade_cost_archive")]
    assert history.generated_at == GENERATED_AT
    assert history.config_version == HISTORY_CONFIG_VERSION
    assert history.cost_audit_report_count == 3
    assert history.first_report_generated_at == datetime(2026, 6, 21, 7, 0, tzinfo=UTC)
    assert history.latest_report_generated_at == datetime(2026, 6, 21, 9, 0, tzinfo=UTC)
    assert history.latest_trade_count == 5
    assert history.latest_fill_rate == Decimal("0.800000")
    assert history.latest_mean_theoretical_edge == Decimal("0.080000")
    assert history.latest_mean_cost_adjusted_edge == Decimal("-0.020000")
    assert history.latest_mean_edge_cost_drag == Decimal("0.100000")
    assert history.latest_total_edge_cost_drag == Decimal("10.000000")
    assert history.latest_partial_fill_count == 1
    assert history.latest_negative_cost_adjusted_edge_count == 1
    assert history.worst_observed_mean_edge_cost_drag == Decimal("0.100000")
    assert history.worst_observed_negative_cost_adjusted_edge_count == 2
    assert history.consecutive_negative_cost_adjusted_edge_count == 2
    assert history.status == "latest_negative_cost_adjusted_edges"


def test_load_paper_trade_cost_audit_db_history_keeps_empty_history_readonly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def load_reports(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "paper_trade_cost_audit_reports",
    ) -> tuple[PaperTradeCostAuditReport, ...]:
        return ()

    monkeypatch.setattr(
        db_history_load.paper_trade_cost_audit_store,
        "load_paper_trade_cost_audit_reports",
        load_reports,
    )

    history = db_history_load.load_paper_trade_cost_audit_db_history_report(
        generated_at=GENERATED_AT,
        config_version=HISTORY_CONFIG_VERSION,
        connection=object(),
    )

    assert history.status == "empty_cost_audit_history"
    assert history.cost_audit_report_count == 0
    assert history.first_report_generated_at is None
    assert history.latest_report_generated_at is None
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True


@pytest.mark.parametrize(
    ("flag_name", "message"),
    (
        ("paper_only", "paper_only"),
        ("report_only", "report_only"),
        ("readonly", "readonly"),
    ),
)
def test_load_paper_trade_cost_audit_db_history_rejects_unsafe_loaded_flags(
    monkeypatch: pytest.MonkeyPatch,
    flag_name: str,
    message: str,
) -> None:
    def load_reports(
        connection_arg: object,
        *,
        limit: int | None = None,
        table_name: str = "paper_trade_cost_audit_reports",
    ) -> tuple[PaperTradeCostAuditReport, ...]:
        report = replace(
            _report(generated_at=datetime(2026, 6, 21, 7, 0, tzinfo=UTC)),
        )
        object.__setattr__(report, flag_name, False)
        return (report,)

    monkeypatch.setattr(
        db_history_load.paper_trade_cost_audit_store,
        "load_paper_trade_cost_audit_reports",
        load_reports,
    )

    with pytest.raises(ValueError, match=message):
        db_history_load.load_paper_trade_cost_audit_db_history_report(
            generated_at=GENERATED_AT,
            config_version=HISTORY_CONFIG_VERSION,
            connection=object(),
        )


def test_paper_trade_cost_audit_db_history_load_module_has_no_live_driver_or_cli_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_trade_cost_audit_db_history_load.py"
    )
    module = ast.parse(module_path.read_text())
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "aiohttp",
        "argparse",
        "click",
        "eth_account",
        "httpx",
        "os",
        "psycopg",
        "requests",
        "socket",
        "sys",
        "urllib",
        "websocket",
        "websockets",
    }
