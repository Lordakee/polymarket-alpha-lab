import ast
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.paper_trade_journal_db_cost_trend_load as db_cost_trend
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.paper_trade_cost_audit import (
    PaperTradeCostAuditConfig,
    PaperTradeCostAuditReport,
)
from polymarket_alpha_lab.paper_trade_cost_trend import (
    PaperTradeCostTrendConfig,
)


GENERATED_AT = datetime(2026, 6, 17, 10, 0, tzinfo=UTC)
COST_AUDIT_CONFIG = PaperTradeCostAuditConfig(
    config_version="paper-trade-cost-audit-v0",
)
COST_TREND_CONFIG_VERSION = "paper-trade-journal-db-cost-trend-v0"
COST_TREND_CONFIG = PaperTradeCostTrendConfig(config_version=COST_TREND_CONFIG_VERSION)
HEX = "a" * 64


def _record(
    index: int,
    *,
    requested_size: Decimal = Decimal("100"),
    filled_size: Decimal = Decimal("100"),
    unfilled_size: Decimal = Decimal("0"),
    theoretical_edge: Decimal = Decimal("0.060000"),
    cost_adjusted_edge: Decimal = Decimal("0.040000"),
    research_slippage: Decimal = Decimal("0.004000"),
    fill_slippage: Decimal | None = Decimal("0.006000"),
) -> PaperTradeRecord:
    return PaperTradeRecord(
        packet_id=f"pkt-{index}",
        packet_created_at=datetime(2026, 6, 17, 9, index, tzinfo=UTC),
        condition_id=f"0x{index:04x}",
        token_id=f"{index}",
        market_slug=f"market-{index}",
        market_url=f"https://polymarket.com/event/market-{index}",
        question=f"Will market {index} resolve yes?",
        outcome_name="YES",
        strategy_type="market_quality",
        source_score="80.000",
        market_raw_archive_path=f"data/raw/gamma/market-{index}.json",
        order_book_raw_archive_path=f"data/raw/clob/book-{index}.json",
        order_book_raw_payload_sha256=HEX,
        order_book_snapshot_sha256=HEX,
        risk_tags=("liquidity",),
        rule_text_hash=HEX,
        resolution_source="Official source",
        decision_timestamp_utc=datetime(2026, 6, 17, 9, index, 30, tzinfo=UTC),
        model_probability=Decimal("0.6000"),
        confidence=Decimal("0.8000"),
        research_bid=Decimal("0.5000"),
        research_ask=Decimal("0.5400"),
        research_midpoint=Decimal("0.5200"),
        research_expected_entry_price=Decimal("0.5400"),
        research_fair_value_estimate=Decimal("0.6000"),
        research_theoretical_edge=theoretical_edge,
        research_spread=Decimal("0.0400"),
        research_slippage_estimate=research_slippage,
        research_cost_adjusted_edge=cost_adjusted_edge,
        max_executable_size=Decimal("100"),
        order_side="buy",
        order_requested_size=requested_size,
        fill_filled_size=filled_size,
        fill_unfilled_size=unfilled_size,
        fill_status="complete" if unfilled_size == 0 else "partial",
        fill_average_price=Decimal("0.5400"),
        fill_worst_price=Decimal("0.5500"),
        fill_best_bid=Decimal("0.5000"),
        fill_best_ask=Decimal("0.5400"),
        fill_midpoint=Decimal("0.5200"),
        fill_spread=Decimal("0.0400"),
        fill_slippage_estimate=fill_slippage,
        order_book_captured_at=datetime(2026, 6, 17, 9, index, 20, tzinfo=UTC),
        account_equity_before_trade=Decimal("10000"),
        sizing_limiter="max_executable_size",
        planned_exit_rule="Hold to resolution.",
        thesis="Paper test thesis.",
        invalidating_conditions="Resolution source changes.",
    )


def test_load_paper_trade_journal_db_cost_trend_limits_and_builds_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = object()
    older_record = _record(1)
    newest_record = _record(
        2,
        requested_size=Decimal("100"),
        filled_size=Decimal("40"),
        unfilled_size=Decimal("60"),
        theoretical_edge=Decimal("0.030000"),
        cost_adjusted_edge=Decimal("-0.010000"),
        research_slippage=Decimal("0.002000"),
        fill_slippage=None,
    )
    calls: list[tuple[Any, int | None, str]] = []

    def load_records(
        connection_arg: object,
        *,
        condition_id: str | None = None,
        token_id: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_trade_journal_records",
    ) -> tuple[PaperTradeRecord, ...]:
        assert condition_id is None
        assert token_id is None
        calls.append((connection_arg, limit, table_name))
        return (newest_record, older_record)

    monkeypatch.setattr(
        db_cost_trend.paper_trade_journal_store,
        "load_paper_trade_records",
        load_records,
    )

    report = db_cost_trend.load_paper_trade_journal_db_cost_trend_report(
        generated_at=GENERATED_AT,
        config_version=COST_TREND_CONFIG_VERSION,
        connection=connection,
        limit=25,
        table_name="paper_trade_archive",
    )

    assert calls == [(connection, 25, "paper_trade_archive")]
    assert report.generated_at == GENERATED_AT
    assert report.config_version == COST_TREND_CONFIG_VERSION
    assert report.cost_audit_report_count == 2
    assert report.latest_trade_count == 2
    assert report.latest_fill_rate == Decimal("0.700000")
    assert report.latest_negative_cost_adjusted_edge_count == 1
    assert report.status == "latest_negative_cost_adjusted_edges"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_load_paper_trade_journal_db_cost_trend_builds_prefixes_in_append_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    older_record = _record(1)
    newest_record = _record(2)

    def load_records(
        connection_arg: object,
        *,
        condition_id: str | None = None,
        token_id: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_trade_journal_records",
    ) -> tuple[PaperTradeRecord, ...]:
        return (newest_record, older_record)

    first_audit = object()
    second_audit = object()
    trend_report = object()
    audit_calls: list[
        tuple[tuple[PaperTradeRecord, ...], PaperTradeCostAuditConfig, datetime]
    ] = []
    trend_calls: list[
        tuple[
            tuple[PaperTradeCostAuditReport, ...],
            PaperTradeCostTrendConfig,
            datetime,
        ]
    ] = []

    def build_audit(
        records: tuple[PaperTradeRecord, ...],
        *,
        config: PaperTradeCostAuditConfig,
        generated_at: datetime,
    ) -> object:
        audit_calls.append((tuple(records), config, generated_at))
        return first_audit if len(audit_calls) == 1 else second_audit

    def build_trend(
        reports: tuple[PaperTradeCostAuditReport, ...],
        *,
        config: PaperTradeCostTrendConfig,
        generated_at: datetime,
    ) -> object:
        trend_calls.append((tuple(reports), config, generated_at))
        return trend_report

    monkeypatch.setattr(
        db_cost_trend.paper_trade_journal_store,
        "load_paper_trade_records",
        load_records,
    )
    monkeypatch.setattr(db_cost_trend, "build_paper_trade_cost_audit_report", build_audit)
    monkeypatch.setattr(db_cost_trend, "build_paper_trade_cost_trend_report", build_trend)

    report = db_cost_trend.load_paper_trade_journal_db_cost_trend_report(
        generated_at=GENERATED_AT,
        config_version=COST_TREND_CONFIG_VERSION,
        connection=object(),
    )

    assert report is trend_report
    assert audit_calls == [
        ((older_record,), COST_AUDIT_CONFIG, GENERATED_AT),
        ((older_record, newest_record), COST_AUDIT_CONFIG, GENERATED_AT),
    ]
    assert trend_calls == [
        (
            (first_audit, second_audit),
            COST_TREND_CONFIG,
            GENERATED_AT,
        ),
    ]


def test_load_paper_trade_journal_db_cost_trend_allows_empty_trade_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def load_records(
        connection_arg: object,
        *,
        condition_id: str | None = None,
        token_id: str | None = None,
        limit: int | None = None,
        table_name: str = "paper_trade_journal_records",
    ) -> tuple[PaperTradeRecord, ...]:
        return ()

    monkeypatch.setattr(
        db_cost_trend.paper_trade_journal_store,
        "load_paper_trade_records",
        load_records,
    )

    report = db_cost_trend.load_paper_trade_journal_db_cost_trend_report(
        generated_at=GENERATED_AT,
        config_version=COST_TREND_CONFIG_VERSION,
        connection=object(),
    )

    assert report.cost_audit_report_count == 0
    assert report.latest_trade_count == 0
    assert report.latest_fill_rate is None
    assert report.status == "empty_cost_audit_history"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_paper_trade_journal_db_cost_trend_module_has_no_live_driver_or_network_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_trade_journal_db_cost_trend_load.py"
    )
    module = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "aiohttp",
        "argparse",
        "auth",
        "click",
        "eth_account",
        "http",
        "httpx",
        "live",
        "network",
        "order",
        "os",
        "psycopg",
        "requests",
        "socket",
        "sys",
        "urllib",
        "wallet",
        "websocket",
        "websockets",
        "write",
    }
