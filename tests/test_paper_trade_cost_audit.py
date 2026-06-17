from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.paper_trade_cost_audit import (
    PaperTradeCostAuditConfig,
    PaperTradeCostAuditReport,
    build_paper_trade_cost_audit_report,
)


GENERATED_AT = datetime(2026, 6, 17, 10, 0, tzinfo=UTC)
CONFIG = PaperTradeCostAuditConfig(config_version="paper-trade-cost-audit-v0")
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


def test_cost_audit_empty_inputs_yield_zero_counts_and_none_metrics():
    report = build_paper_trade_cost_audit_report(
        (),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperTradeCostAuditReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-trade-cost-audit-v0"
    assert report.trade_count == 0
    assert report.total_filled_size == Decimal("0")
    assert report.total_requested_size == Decimal("0")
    assert report.fill_rate is None
    assert report.mean_theoretical_edge is None
    assert report.mean_cost_adjusted_edge is None
    assert report.mean_edge_cost_drag is None
    assert report.total_edge_cost_drag is None
    assert report.mean_research_slippage is None
    assert report.mean_fill_slippage is None
    assert report.partial_fill_count == 0
    assert report.negative_cost_adjusted_edge_count == 0
    assert report.largest_single_trade_cost_drag is None
    assert report.paper_only is True
    assert report.report_only is True


def test_cost_audit_aggregates_edge_drag_slippage_and_fill_quality():
    trades = (
        _record(
            1,
            theoretical_edge=Decimal("0.060000"),
            cost_adjusted_edge=Decimal("0.040000"),
            research_slippage=Decimal("0.004000"),
            fill_slippage=Decimal("0.006000"),
        ),
        _record(
            2,
            requested_size=Decimal("100"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("60"),
            theoretical_edge=Decimal("0.030000"),
            cost_adjusted_edge=Decimal("-0.010000"),
            research_slippage=Decimal("0.002000"),
            fill_slippage=None,
        ),
        _record(
            3,
            theoretical_edge=Decimal("0.090000"),
            cost_adjusted_edge=Decimal("0.060000"),
            research_slippage=Decimal("0.008000"),
            fill_slippage=Decimal("0.012000"),
        ),
    )

    report = build_paper_trade_cost_audit_report(
        trades,
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.trade_count == 3
    assert report.total_filled_size == Decimal("240")
    assert report.total_requested_size == Decimal("300")
    assert report.fill_rate == Decimal("0.800000")
    assert report.mean_theoretical_edge == Decimal("0.060000")
    assert report.mean_cost_adjusted_edge == Decimal("0.030000")
    assert report.mean_edge_cost_drag == Decimal("0.030000")
    assert report.total_edge_cost_drag == Decimal("6.600000")
    assert report.mean_research_slippage == Decimal("0.004667")
    assert report.mean_fill_slippage == Decimal("0.009000")
    assert report.partial_fill_count == 1
    assert report.negative_cost_adjusted_edge_count == 1
    assert report.largest_single_trade_cost_drag == Decimal("3.000000")


def test_cost_audit_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="config must be"):
        build_paper_trade_cost_audit_report((), config=object(), generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_trade_cost_audit_report((), config=CONFIG, generated_at="now")
    with pytest.raises(ValueError, match="PaperTradeRecord"):
        build_paper_trade_cost_audit_report((object(),), config=CONFIG, generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="config_version"):
        PaperTradeCostAuditConfig(config_version="")


def test_cost_audit_dataclasses_are_frozen_and_revalidate_flags():
    report = build_paper_trade_cost_audit_report(
        (_record(1),),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.trade_count = 2
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
