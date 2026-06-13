import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.analytics import (
    PaperAnalyticsBreach,
    PaperAnalyticsConfig,
    PaperAnalyticsLog,
    build_paper_analytics_report,
    build_paper_drawdown_points,
)
from polymarket_alpha_lab.domain import OrderBookLevel, OrderBookSnapshot
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill
from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.positions import build_paper_portfolio, mark_paper_nav
from polymarket_alpha_lab.research import build_research_packet


def complete_packet(**overrides):
    values = {
        "candidate": ScoredCandidate(
            condition_id="0xabc",
            token_id="111",
            market_slug="example-market",
            question="Will the example resolve yes?",
            total_score="78.500",
            raw_archive_path="data/raw/gamma/markets.json",
        ),
        "created_at": datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        "market_url": "https://polymarket.com/event/example-market",
        "outcome_name": "Yes",
        "strategy_type": "market_quality",
        "model_probability": Decimal("0.56"),
        "bid": Decimal("0.50"),
        "ask": Decimal("0.52"),
        "midpoint": Decimal("0.51"),
        "expected_entry_price": Decimal("0.514"),
        "fair_value_estimate": Decimal("0.56"),
        "theoretical_edge": Decimal("0.046"),
        "spread": Decimal("0.02"),
        "slippage_estimate": Decimal("0.004"),
        "cost_adjusted_edge": Decimal("0.026"),
        "confidence": Decimal("0.60"),
        "max_executable_size": Decimal("100"),
        "risk_tags": ("liquidity",),
        "thesis": "Tight spread and clear rules.",
        "invalidating_conditions": "Spread widens.",
        "rule_text": "Example rule.",
        "resolution_source": "Example source",
    }
    values.update(overrides)
    return build_research_packet(**values)


def complete_fill(**overrides):
    values = {
        "token_id": "111",
        "side": "buy",
        "requested_size": Decimal("100"),
        "order_book_captured_at": datetime(2026, 6, 13, 12, 30, 30, tzinfo=UTC),
        "order_book_snapshot_sha256": "a" * 64,
        "filled_size": Decimal("100"),
        "unfilled_size": Decimal("0"),
        "average_price": Decimal("0.514"),
        "worst_price": Decimal("0.52"),
        "best_bid": Decimal("0.49"),
        "best_ask": Decimal("0.51"),
        "midpoint": Decimal("0.500"),
        "spread": Decimal("0.020"),
        "slippage_estimate": Decimal("0.004"),
    }
    values.update(overrides)
    return PaperFill(**values)


def record_from(packet=None, fill=None, **overrides):
    values = {
        "packet": packet or complete_packet(),
        "fill": fill or complete_fill(),
        "decision_timestamp": datetime(2026, 6, 13, 12, 31),
        "order_book_raw_archive_path": "data/raw/clob/book-111.json",
        "order_book_raw_payload_sha256": "b" * 64,
        "account_equity_before_trade": Decimal("10000"),
        "sizing_limiter": "max_executable_size",
        "planned_exit_rule": "Mark at executable bid on review.",
    }
    values.update(overrides)
    return PaperTradeRecord.from_packet_and_fill(**values)


def packet_at(minute: int, **overrides):
    values = {"created_at": datetime(2026, 6, 13, 12, minute, tzinfo=UTC)}
    values.update(overrides)
    return complete_packet(**values)


def two_position_report():
    first = record_from()
    second_packet = packet_at(
        32,
        candidate=ScoredCandidate(
            condition_id="0xaaa",
            token_id="222",
            market_slug="another-market",
            question="Will another market resolve yes?",
            total_score="80.000",
            raw_archive_path="data/raw/gamma/markets-2.json",
        ),
        market_url="https://polymarket.com/event/another-market",
        outcome_name="Yes",
        strategy_type="relative_value",
        risk_tags=("liquidity", "event-risk"),
        resolution_source="Another source",
    )
    second = record_from(
        packet=second_packet,
        fill=complete_fill(
            token_id="222",
            requested_size=Decimal("50"),
            filled_size=Decimal("50"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.200"),
            worst_price=Decimal("0.20"),
        ),
        order_book_raw_archive_path="data/raw/clob/book-222.json",
        order_book_raw_payload_sha256="c" * 64,
    )
    portfolio = build_paper_portfolio([first, second], starting_cash=Decimal("10000"))
    snapshot = mark_paper_nav(
        portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(OrderBookLevel(Decimal("0.50"), Decimal("100")),),
                asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
                captured_at=datetime(2026, 6, 14, 0, 0, tzinfo=UTC),
            ),
            "222": OrderBookSnapshot(
                token_id="222",
                bids=(OrderBookLevel(Decimal("0.10"), Decimal("10")),),
                asks=(OrderBookLevel(Decimal("0.22"), Decimal("50")),),
                captured_at=datetime(2026, 6, 14, 0, 1, tzinfo=UTC),
            ),
        },
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )
    report = build_paper_analytics_report(
        portfolio,
        snapshot,
        config=PaperAnalyticsConfig(
            config_version="node3-test",
            max_open_cost_basis_ratio=Decimal("0.0100"),
            max_single_position_cost_basis_ratio=Decimal("0.0040"),
            max_strategy_cost_basis_ratio=Decimal("0.0040"),
            max_market_cost_basis_ratio=Decimal("0.0040"),
            max_risk_tag_cost_basis_ratio=Decimal("0.0040"),
            max_no_exit_depth_cost_basis_ratio=Decimal("0.0001"),
            min_cash_ratio=Decimal("0.9900"),
        ),
        generated_at=datetime(2026, 6, 14, 12, tzinfo=UTC),
    )
    return portfolio, snapshot, report


def test_build_paper_analytics_report_summarizes_performance_and_liquidity():
    _portfolio, snapshot, report = two_position_report()

    assert report.generated_at == datetime(2026, 6, 14, 12, tzinfo=UTC)
    assert report.config_version == "node3-test"
    assert report.marked_at == snapshot.marked_at
    assert report.paper_only is True
    assert report.position_count == 2
    assert report.portfolio_mark_status == "partially_executable"
    assert report.performance.starting_cash == Decimal("10000")
    assert report.performance.cash_balance == Decimal("9938.600")
    assert report.performance.realized_pnl == Decimal("0")
    assert report.performance.unrealized_exit_pnl == Decimal("-10.400")
    assert report.performance.total_exit_pnl == Decimal("-10.400")
    assert report.performance.exit_nav == Decimal("9989.600")
    assert report.performance.midpoint_nav == Decimal("9997.600")
    assert report.performance.total_cost_basis == Decimal("61.400")
    assert report.performance.exit_return_ratio == Decimal("-0.0010")
    assert report.performance.realized_return_ratio == Decimal("0.0000")
    assert report.performance.unrealized_exit_return_ratio == Decimal("-0.0010")
    assert report.performance.cash_ratio == Decimal("0.9939")
    assert report.performance.open_cost_basis_ratio == Decimal("0.0061")
    assert report.performance.midpoint_nav_gap == Decimal("8.000")
    assert report.performance.midpoint_nav_gap_ratio == Decimal("0.0008")
    assert report.exit_depth_coverage_ratio == Decimal("0.7333")
    assert report.exit_depth_shortfall_ratio == Decimal("0.2667")
    assert report.no_exit_depth_cost_basis_ratio == Decimal("0.0000")
    assert report.oldest_order_book_captured_at == datetime(2026, 6, 14, 0, 0, tzinfo=UTC)
    assert report.newest_order_book_captured_at == datetime(2026, 6, 14, 0, 1, tzinfo=UTC)


def test_build_paper_analytics_report_builds_position_exposures_and_buckets():
    _portfolio, _snapshot, report = two_position_report()

    assert [row.token_id for row in report.position_exposures] == ["222", "111"]
    first = report.position_exposures[0]
    assert first.token_id == "222"
    assert first.strategy_type == "relative_value"
    assert first.risk_tags == ("liquidity", "event-risk")
    assert first.open_size == Decimal("50")
    assert first.cost_basis == Decimal("10.000")
    assert first.max_loss_to_zero == Decimal("10.000")
    assert first.max_profit_to_one == Decimal("40.000")
    assert first.exit_value == Decimal("1.000")
    assert first.midpoint_value == Decimal("8.000")
    assert first.unrealized_exit_pnl == Decimal("-9.000")
    assert first.exit_filled_size == Decimal("10")
    assert first.exit_unfilled_size == Decimal("40")
    assert first.exit_coverage_ratio == Decimal("0.2000")
    assert first.exit_shortfall_ratio == Decimal("0.8000")
    assert first.cost_basis_ratio_to_starting_cash == Decimal("0.0010")
    assert first.cost_basis_ratio_to_total_open_basis == Decimal("0.1629")
    assert first.exit_value_ratio_to_exit_nav == Decimal("0.0001")
    assert first.mark_status == "partially_executable"
    assert first.source_packet_ids
    assert first.market_url == "https://polymarket.com/event/another-market"
    assert first.last_order_book_raw_payload_sha256 == "c" * 64
    assert first.opened_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert first.updated_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert first.average_entry_price == Decimal("0.200")
    assert first.realized_pnl == Decimal("0")
    assert first.entry_trade_count == 1
    assert first.exit_trade_count == 0

    buckets = {(bucket.bucket_type, bucket.bucket_value): bucket for bucket in report.buckets}
    assert buckets[("strategy_type", "relative_value")].cost_basis == Decimal("10.000")
    assert buckets[("market_slug", "another-market")].token_ids == ("222",)
    assert buckets[("risk_tag", "liquidity")].additive is False
    assert buckets[("risk_tag", "liquidity")].position_count == 2
    assert buckets[("risk_tag", "liquidity")].cost_basis == Decimal("61.400")
    assert buckets[("risk_tag", "event-risk")].additive is False
    assert buckets[("risk_tag", "event-risk")].token_ids == ("222",)
    assert buckets[("risk_tag", "event-risk")].cost_basis == Decimal("10.000")
    risk_tag_buckets = [
        bucket for bucket in report.buckets if bucket.bucket_type == "risk_tag"
    ]
    assert sum(bucket.cost_basis for bucket in risk_tag_buckets) > report.performance.total_cost_basis
    assert buckets[("mark_status", "partially_executable")].exit_unfilled_size == Decimal("40")


def test_build_paper_analytics_report_records_threshold_breaches():
    _portfolio, _snapshot, report = two_position_report()

    codes = [breach.code for breach in report.breaches]
    assert codes == [
        "single_position_cost_basis_limit",
        "strategy_cost_basis_limit",
        "market_cost_basis_limit",
        "risk_tag_cost_basis_limit",
    ]
    assert report.breaches[0].field_name == "position:111"
    assert report.breaches[0].observed_value == Decimal("0.0051")
    assert report.breaches[0].threshold == Decimal("0.0040")


def test_build_paper_analytics_report_rejects_mismatched_portfolio_and_snapshot():
    portfolio, snapshot, _report = two_position_report()
    other_portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    mismatched_snapshot = mark_paper_nav(
        other_portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(OrderBookLevel(Decimal("0.50"), Decimal("100")),),
                asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
                captured_at=datetime(2026, 6, 14, tzinfo=UTC),
            )
        },
        marked_at=snapshot.marked_at,
    )

    with pytest.raises(ValueError, match="cash_balance|token"):
        build_paper_analytics_report(
            portfolio,
            mismatched_snapshot,
            config=PaperAnalyticsConfig(config_version="node3-test"),
            generated_at=datetime(2026, 6, 14, tzinfo=UTC),
        )


def test_build_paper_analytics_report_rejects_corrupted_zero_starting_cash():
    portfolio, snapshot, _report = two_position_report()
    object.__setattr__(portfolio, "starting_cash", Decimal("0"))
    object.__setattr__(snapshot, "starting_cash", Decimal("0"))

    with pytest.raises(ValueError, match="starting_cash"):
        build_paper_analytics_report(
            portfolio,
            snapshot,
            config=PaperAnalyticsConfig(config_version="node3-test"),
            generated_at=datetime(2026, 6, 14, tzinfo=UTC),
        )


def test_build_paper_analytics_report_handles_empty_portfolio():
    portfolio = build_paper_portfolio([], starting_cash=Decimal("10000"))
    snapshot = mark_paper_nav(portfolio, {}, marked_at=datetime(2026, 6, 14, tzinfo=UTC))

    report = build_paper_analytics_report(
        portfolio,
        snapshot,
        config=PaperAnalyticsConfig(config_version="node3-test"),
        generated_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert report.position_count == 0
    assert report.portfolio_mark_status == "no_open_positions"
    assert report.position_exposures == ()
    assert report.buckets == ()
    assert report.exit_depth_coverage_ratio is None
    assert report.exit_depth_shortfall_ratio is None
    assert report.no_exit_depth_cost_basis_ratio is None
    assert report.performance.cash_balance == Decimal("10000")
    assert report.performance.exit_nav == Decimal("10000")
    assert report.performance.midpoint_nav == Decimal("10000")
    assert report.performance.total_cost_basis == Decimal("0")
    assert report.performance.unrealized_exit_pnl == Decimal("0")
    assert report.performance.exit_return_ratio == Decimal("0.0000")
    assert report.performance.cash_ratio == Decimal("1.0000")
    assert report.performance.open_cost_basis_ratio == Decimal("0.0000")
    assert report.performance.midpoint_nav_gap == Decimal("0")
    assert report.performance.midpoint_nav_gap_ratio == Decimal("0.0000")
    assert report.oldest_order_book_captured_at is None
    assert report.newest_order_book_captured_at is None
    assert len(report.drawdown_points) == 1


def test_build_paper_analytics_report_handles_missing_midpoint_without_nav_fallback():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    snapshot = mark_paper_nav(
        portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(OrderBookLevel(Decimal("0.50"), Decimal("100")),),
                asks=(),
                captured_at=datetime(2026, 6, 14, tzinfo=UTC),
            )
        },
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    report = build_paper_analytics_report(
        portfolio,
        snapshot,
        config=PaperAnalyticsConfig(config_version="node3-test"),
        generated_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert snapshot.exit_nav == Decimal("9998.600")
    assert snapshot.midpoint_nav is None
    assert report.portfolio_mark_status == "fully_executable"
    assert report.performance.midpoint_nav is None
    assert report.performance.midpoint_nav_gap is None
    assert report.performance.midpoint_nav_gap_ratio is None
    assert report.exit_depth_coverage_ratio == Decimal("1.0000")
    assert report.position_exposures[0].exit_value == Decimal("50.00")
    assert report.position_exposures[0].midpoint_value is None


def test_build_paper_analytics_report_handles_all_no_exit_depth():
    portfolio, _snapshot, _report = two_position_report()
    snapshot = mark_paper_nav(
        portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(),
                asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
                captured_at=datetime(2026, 6, 14, tzinfo=UTC),
            ),
            "222": OrderBookSnapshot(
                token_id="222",
                bids=(),
                asks=(OrderBookLevel(Decimal("0.22"), Decimal("50")),),
                captured_at=datetime(2026, 6, 14, 0, 1, tzinfo=UTC),
            ),
        },
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    report = build_paper_analytics_report(
        portfolio,
        snapshot,
        config=PaperAnalyticsConfig(
            config_version="node3-test",
            max_no_exit_depth_cost_basis_ratio=Decimal("0.0001"),
        ),
        generated_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert snapshot.exit_nav == Decimal("9938.600")
    assert snapshot.midpoint_nav is None
    assert snapshot.total_cost_basis == Decimal("61.400")
    assert report.portfolio_mark_status == "no_exit_depth"
    assert report.exit_depth_coverage_ratio == Decimal("0.0000")
    assert report.exit_depth_shortfall_ratio == Decimal("1.0000")
    assert report.no_exit_depth_cost_basis_ratio == Decimal("0.0061")
    assert {row.mark_status for row in report.position_exposures} == {"no_exit_depth"}
    assert [b.code for b in report.breaches if b.code == "no_exit_depth_limit"] == [
        "no_exit_depth_limit"
    ]


def test_build_paper_analytics_report_handles_zero_exit_nav_without_dividing_by_zero():
    packet = complete_packet(max_executable_size=Decimal("1"))
    fill = complete_fill(
        requested_size=Decimal("1"),
        filled_size=Decimal("1"),
        unfilled_size=Decimal("0"),
        average_price=Decimal("1"),
        worst_price=Decimal("1"),
        best_bid=Decimal("1"),
        best_ask=Decimal("1"),
        midpoint=Decimal("1"),
        spread=Decimal("0"),
        slippage_estimate=Decimal("0"),
    )
    portfolio = build_paper_portfolio(
        [record_from(packet=packet, fill=fill)],
        starting_cash=Decimal("1"),
    )
    snapshot = mark_paper_nav(
        portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(),
                asks=(OrderBookLevel(Decimal("1"), Decimal("1")),),
                captured_at=datetime(2026, 6, 14, tzinfo=UTC),
            )
        },
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    report = build_paper_analytics_report(
        portfolio,
        snapshot,
        config=PaperAnalyticsConfig(config_version="node3-test"),
        generated_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert snapshot.exit_nav == Decimal("0")
    assert report.performance.exit_return_ratio == Decimal("-1.0000")
    assert report.performance.cash_ratio == Decimal("0.0000")
    assert report.position_exposures[0].exit_value_ratio_to_exit_nav is None
    assert report.buckets
    assert all(bucket.exit_value_ratio_to_exit_nav is None for bucket in report.buckets)
    assert report.drawdown_points[0].high_watermark_nav == Decimal("0")
    assert report.drawdown_points[0].drawdown_ratio is None


@pytest.mark.parametrize(
    "bad_value",
    [
        Decimal("NaN"),
        Decimal("sNaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
        0.1,
        1,
        "0.1",
        None,
    ],
)
def test_analytics_config_rejects_non_decimal_or_non_finite_thresholds(bad_value):
    with pytest.raises(ValueError, match="max_open_cost_basis_ratio"):
        PaperAnalyticsConfig(
            config_version="node3-test",
            max_open_cost_basis_ratio=bad_value,
        )


def test_analytics_breach_rejects_float_values():
    with pytest.raises(ValueError, match="observed_value"):
        PaperAnalyticsBreach(
            code="open_cost_basis_limit",
            message="Example breach.",
            field_name="example",
            observed_value=0.1,
            threshold=Decimal("0.1000"),
        )


def test_analytics_breach_rejects_unknown_code():
    with pytest.raises(ValueError, match="code"):
        PaperAnalyticsBreach(
            code="unknown_limit",
            message="Example breach.",
            field_name="example",
            observed_value=Decimal("0.1000"),
            threshold=Decimal("0.0500"),
        )


def snapshot_with_exit_nav(marked_at, exit_nav):
    empty_portfolio = build_paper_portfolio([], starting_cash=exit_nav)
    return mark_paper_nav(empty_portfolio, {}, marked_at=marked_at)


def one_position_snapshot(marked_at, bid, ask):
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    return mark_paper_nav(
        portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(OrderBookLevel(bid, Decimal("100")),),
                asks=(OrderBookLevel(ask, Decimal("100")),),
                captured_at=marked_at,
            )
        },
        marked_at=marked_at,
    )


def test_build_paper_drawdown_points_uses_exit_nav_not_midpoint_nav():
    first = one_position_snapshot(
        datetime(2026, 6, 14, tzinfo=UTC),
        Decimal("0.50"),
        Decimal("0.90"),
    )
    second = one_position_snapshot(
        datetime(2026, 6, 15, tzinfo=UTC),
        Decimal("0.40"),
        Decimal("0.40"),
    )
    third = one_position_snapshot(
        datetime(2026, 6, 16, tzinfo=UTC),
        Decimal("0.70"),
        Decimal("0.70"),
    )

    points = build_paper_drawdown_points([third, first, second])

    assert [point.marked_at for point in points] == [
        datetime(2026, 6, 14, tzinfo=UTC),
        datetime(2026, 6, 15, tzinfo=UTC),
        datetime(2026, 6, 16, tzinfo=UTC),
    ]
    assert first.midpoint_nav != first.exit_nav
    assert first.midpoint_nav > second.midpoint_nav
    assert points[0].exit_nav == Decimal("9998.600")
    assert points[0].high_watermark_nav == Decimal("9998.600")
    assert points[0].drawdown == Decimal("0")
    assert points[0].drawdown_ratio == Decimal("0.0000")
    assert points[0].is_new_high is True
    assert points[1].high_watermark_nav == Decimal("9998.600")
    assert points[1].drawdown == Decimal("10.000")
    assert points[1].drawdown_ratio == Decimal("0.0010")
    assert points[1].is_new_high is False
    assert points[2].high_watermark_nav == Decimal("10018.600")
    assert points[2].drawdown == Decimal("0")
    assert points[2].is_new_high is True


def test_build_paper_drawdown_points_rejects_duplicate_marked_at():
    snapshot = snapshot_with_exit_nav(datetime(2026, 6, 14, tzinfo=UTC), Decimal("100"))

    with pytest.raises(ValueError, match="duplicate.*marked_at"):
        build_paper_drawdown_points([snapshot, snapshot])


def test_build_paper_drawdown_points_returns_none_ratio_when_high_watermark_is_zero():
    packet = complete_packet(max_executable_size=Decimal("1"))
    fill = complete_fill(
        requested_size=Decimal("1"),
        filled_size=Decimal("1"),
        unfilled_size=Decimal("0"),
        average_price=Decimal("1"),
        worst_price=Decimal("1"),
        best_bid=Decimal("1"),
        best_ask=Decimal("1"),
        midpoint=Decimal("1"),
        spread=Decimal("0"),
        slippage_estimate=Decimal("0"),
    )
    portfolio = build_paper_portfolio(
        [record_from(packet=packet, fill=fill)],
        starting_cash=Decimal("1"),
    )
    snapshot = mark_paper_nav(
        portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(),
                asks=(OrderBookLevel(Decimal("1"), Decimal("1")),),
                captured_at=datetime(2026, 6, 14, tzinfo=UTC),
            )
        },
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    points = build_paper_drawdown_points([snapshot])

    assert points[0].exit_nav == Decimal("0")
    assert points[0].high_watermark_nav == Decimal("0")
    assert points[0].drawdown == Decimal("0")
    assert points[0].drawdown_ratio is None
    assert points[0].is_new_high is True


def test_build_paper_drawdown_points_treats_equal_high_as_new_high():
    first = snapshot_with_exit_nav(datetime(2026, 6, 14, tzinfo=UTC), Decimal("100"))
    second = snapshot_with_exit_nav(datetime(2026, 6, 15, tzinfo=UTC), Decimal("90"))
    third = snapshot_with_exit_nav(datetime(2026, 6, 16, tzinfo=UTC), Decimal("100"))

    points = build_paper_drawdown_points([first, second, third])

    assert points[2].high_watermark_nav == Decimal("100")
    assert points[2].drawdown == Decimal("0")
    assert points[2].drawdown_ratio == Decimal("0.0000")
    assert points[2].is_new_high is True


def test_analytics_dataclasses_are_frozen():
    _portfolio, _snapshot, report = two_position_report()

    with pytest.raises(FrozenInstanceError):
        report.performance.cash_ratio = Decimal("0")
    with pytest.raises(FrozenInstanceError):
        report.position_exposures[0].open_size = Decimal("1")


def test_paper_analytics_log_appends_jsonl_report(tmp_path):
    _portfolio, _snapshot, report = two_position_report()
    log = PaperAnalyticsLog(path=tmp_path / "analytics.jsonl")

    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"breaches"')
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["generated_at"] == "2026-06-14T12:00:00+00:00"
    assert stored["marked_at"] == "2026-06-14T00:00:00+00:00"
    assert stored["performance"]["starting_cash"] == "10000"
    assert stored["performance"]["cash_ratio"] == "0.9939"
    assert stored["breaches"][0]["observed_value"] == "0.0051"
    assert stored["position_exposures"][0]["risk_tags"] == ["liquidity", "event-risk"]


def test_paper_analytics_log_appends_without_overwriting(tmp_path):
    _portfolio, _snapshot, report = two_position_report()
    second = replace(report, generated_at=datetime(2026, 6, 14, 13, tzinfo=UTC))
    log = PaperAnalyticsLog(path=tmp_path / "analytics.jsonl")

    log.append(report)
    log.append(second)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["generated_at"] == "2026-06-14T12:00:00+00:00"
    assert json.loads(lines[1])["generated_at"] == "2026-06-14T13:00:00+00:00"


def test_paper_analytics_log_creates_parent_directories_from_string_path(tmp_path):
    _portfolio, _snapshot, report = two_position_report()
    log = PaperAnalyticsLog(path=str(tmp_path / "nested" / "analytics.jsonl"))

    log.append(report)

    assert log.path.exists()
    assert len(log.path.read_text(encoding="utf-8").splitlines()) == 1


def test_paper_analytics_log_rejects_invalid_paths(tmp_path):
    with pytest.raises(ValueError, match="path"):
        PaperAnalyticsLog(path=object())
    with pytest.raises(ValueError, match="path"):
        PaperAnalyticsLog(path="")
    with pytest.raises(ValueError, match="path"):
        PaperAnalyticsLog(path=tmp_path)
    parent_file = tmp_path / "not-a-directory"
    parent_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="path"):
        PaperAnalyticsLog(path=parent_file / "analytics.jsonl")


def test_paper_analytics_log_rejects_invalid_public_input_before_open(tmp_path):
    log = PaperAnalyticsLog(path=tmp_path / "analytics.jsonl")

    with pytest.raises(ValueError, match="report"):
        log.append(object())

    assert not log.path.exists()


@pytest.mark.parametrize("bad_value", [Decimal("NaN"), float("nan"), object()])
def test_paper_analytics_log_preserves_existing_file_when_serialization_fails(
    tmp_path,
    bad_value,
):
    _portfolio, _snapshot, report = two_position_report()
    object.__setattr__(report.performance, "cash_ratio", bad_value)
    path = tmp_path / "analytics.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = PaperAnalyticsLog(path=path)

    with pytest.raises(ValueError, match="finite|JSON|serializable"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'
