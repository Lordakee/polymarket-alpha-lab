from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
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


class _DecimalSubclass(Decimal):
    pass


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


def _non_empty_report_kwargs() -> dict[str, object]:
    return {
        "generated_at": GENERATED_AT,
        "config_version": "paper-trade-cost-audit-v0",
        "trade_count": 1,
        "total_filled_size": Decimal("100"),
        "total_requested_size": Decimal("100"),
        "fill_rate": Decimal("1.000000"),
        "mean_theoretical_edge": Decimal("0.060000"),
        "mean_cost_adjusted_edge": Decimal("0.040000"),
        "mean_edge_cost_drag": Decimal("0.020000"),
        "total_edge_cost_drag": Decimal("2.000000"),
        "mean_research_slippage": Decimal("0.004000"),
        "mean_fill_slippage": None,
        "partial_fill_count": 0,
        "negative_cost_adjusted_edge_count": 0,
        "largest_single_trade_cost_drag": Decimal("2.000000"),
    }


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


@pytest.mark.parametrize(
    ("generated_at", "expected_generated_at"),
    (
        (datetime(2026, 6, 17, 10, 0), GENERATED_AT),
        (
            datetime(2026, 6, 17, 6, 0, tzinfo=timezone(timedelta(hours=-4))),
            GENERATED_AT,
        ),
    ),
)
def test_cost_audit_normalizes_generated_at_to_utc(
    generated_at: datetime,
    expected_generated_at: datetime,
):
    report = build_paper_trade_cost_audit_report(
        (_record(1),),
        config=CONFIG,
        generated_at=generated_at,
    )

    assert report.generated_at == expected_generated_at
    assert report.generated_at.tzinfo is UTC


def test_cost_audit_rejects_trade_decision_timestamps_after_generated_at():
    future_trade = replace(
        _record(1),
        decision_timestamp_utc=GENERATED_AT + timedelta(microseconds=1),
    )

    with pytest.raises(ValueError, match="decision_timestamp_utc"):
        build_paper_trade_cost_audit_report(
            (future_trade,),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )


def test_cost_audit_keeps_mean_fill_slippage_optional_when_all_fills_omit_it():
    report = build_paper_trade_cost_audit_report(
        (
            replace(_record(1), fill_slippage_estimate=None),
            replace(_record(2), fill_slippage_estimate=None),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.mean_fill_slippage is None
    assert report.mean_theoretical_edge == Decimal("0.060000")
    assert report.mean_cost_adjusted_edge == Decimal("0.040000")
    assert report.mean_edge_cost_drag == Decimal("0.020000")
    assert report.total_edge_cost_drag == Decimal("4.000000")
    assert report.mean_research_slippage == Decimal("0.004000")
    assert report.largest_single_trade_cost_drag == Decimal("2.000000")


def test_cost_audit_clamps_edge_cost_drag_to_zero_for_price_improvement():
    trades = (
        _record(
            1,
            requested_size=Decimal("10"),
            filled_size=Decimal("10"),
            theoretical_edge=Decimal("0.020000"),
            cost_adjusted_edge=Decimal("0.050000"),
        ),
        _record(
            2,
            requested_size=Decimal("10"),
            filled_size=Decimal("10"),
            theoretical_edge=Decimal("0.090000"),
            cost_adjusted_edge=Decimal("0.040000"),
        ),
    )

    report = build_paper_trade_cost_audit_report(
        trades,
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.mean_edge_cost_drag == Decimal("0.025000")
    assert report.total_edge_cost_drag == Decimal("0.500000")
    assert report.largest_single_trade_cost_drag == Decimal("0.500000")


def test_cost_audit_rejects_direct_constructed_records_with_non_decimal_metrics():
    with pytest.raises(ValueError, match="research_theoretical_edge"):
        build_paper_trade_cost_audit_report(
            (replace(_record(1), research_theoretical_edge="0.060000"),),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="research_theoretical_edge"):
        build_paper_trade_cost_audit_report(
            (
                replace(
                    _record(1),
                    research_theoretical_edge=_DecimalSubclass("0.060000"),
                ),
            ),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="fill_slippage_estimate"):
        build_paper_trade_cost_audit_report(
            (replace(_record(1), fill_slippage_estimate="0.006000"),),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )


def test_cost_audit_rejects_negative_slippage_estimates():
    with pytest.raises(ValueError, match="research_slippage_estimate"):
        build_paper_trade_cost_audit_report(
            (replace(_record(1), research_slippage_estimate=Decimal("-0.001000")),),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="fill_slippage_estimate"):
        build_paper_trade_cost_audit_report(
            (replace(_record(1), fill_slippage_estimate=Decimal("-0.001000")),),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )


def test_cost_audit_rejects_direct_constructed_records_with_inconsistent_fills():
    with pytest.raises(ValueError, match="fill accounting"):
        build_paper_trade_cost_audit_report(
            (
                replace(
                    _record(1),
                    order_requested_size=Decimal("100"),
                    fill_filled_size=Decimal("90"),
                    fill_unfilled_size=Decimal("20"),
                    fill_status="partial",
                ),
            ),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="fill_status"):
        build_paper_trade_cost_audit_report(
            (
                replace(
                    _record(1),
                    order_requested_size=Decimal("100"),
                    fill_filled_size=Decimal("90"),
                    fill_unfilled_size=Decimal("10"),
                    fill_status="complete",
                ),
            ),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )


def test_cost_audit_rejects_non_binary_outcome_records():
    with pytest.raises(ValueError, match="outcome_name"):
        build_paper_trade_cost_audit_report(
            (replace(_record(1), outcome_name="MAYBE"),),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )


def test_cost_audit_report_revalidates_derived_metric_consistency():
    report = build_paper_trade_cost_audit_report(
        (_record(1), _record(2, filled_size=Decimal("50"), unfilled_size=Decimal("50"))),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="fill_rate"):
        replace(report, fill_rate=Decimal("0.250000"))
    with pytest.raises(ValueError, match="partial_fill_count"):
        replace(report, partial_fill_count=3)
    with pytest.raises(ValueError, match="negative_cost_adjusted_edge_count"):
        replace(report, negative_cost_adjusted_edge_count=3)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_cost_audit_empty_report_rejects_direct_aggregate_metrics():
    empty = build_paper_trade_cost_audit_report(
        (),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="fill_rate"):
        replace(empty, fill_rate=Decimal("0.000000"))
    with pytest.raises(ValueError, match="mean_edge_cost_drag"):
        replace(empty, mean_edge_cost_drag=Decimal("0.000000"))
    with pytest.raises(ValueError, match="total_filled_size"):
        replace(empty, total_filled_size=Decimal("1"))
    with pytest.raises(ValueError, match="partial_fill_count"):
        replace(empty, partial_fill_count=1)


def test_cost_audit_non_empty_report_rejects_empty_report_totals():
    kwargs = _non_empty_report_kwargs()
    kwargs.update(
        total_filled_size=Decimal("0"),
        total_requested_size=Decimal("0"),
        fill_rate=None,
    )
    with pytest.raises(ValueError, match="total_requested_size"):
        PaperTradeCostAuditReport(**kwargs)

    kwargs = _non_empty_report_kwargs()
    kwargs.update(
        total_filled_size=Decimal("0"),
        fill_rate=Decimal("0.000000"),
    )
    with pytest.raises(ValueError, match="total_filled_size"):
        PaperTradeCostAuditReport(**kwargs)


@pytest.mark.parametrize(
    "field_name",
    (
        "mean_theoretical_edge",
        "mean_cost_adjusted_edge",
        "mean_edge_cost_drag",
        "total_edge_cost_drag",
        "mean_research_slippage",
        "largest_single_trade_cost_drag",
    ),
)
def test_cost_audit_non_empty_report_requires_metrics_from_valid_trades(
    field_name: str,
):
    kwargs = _non_empty_report_kwargs()
    kwargs[field_name] = None

    with pytest.raises(ValueError, match=field_name):
        PaperTradeCostAuditReport(**kwargs)


def test_cost_audit_report_rejects_subquantum_fill_rate():
    report = build_paper_trade_cost_audit_report(
        (_record(1), _record(2, filled_size=Decimal("50"), unfilled_size=Decimal("50"))),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="fill_rate"):
        replace(report, fill_rate=Decimal("0.7500004"))


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
