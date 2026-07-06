from dataclasses import FrozenInstanceError, is_dataclass
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_market_event_liquidity_capacity_curve_v10 import (
    MarketEventLiquidityCapacityCurveInput,
    MarketEventLiquidityCapacityCurveResult,
    market_event_liquidity_capacity_curve_payload,
    estimate_market_event_liquidity_capacity_curve,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def curve_input(**overrides):
    values = {
        "market_id": "market-election-resolution",
        "depth_score": d("0.800000"),
        "spread_bps": d("20.000000"),
        "slippage_bps": d("35.000000"),
        "daily_volume_score": d("0.700000"),
        "cost_adjusted_edge_bps": d("140.000000"),
        "time_to_resolution_minutes": d("720.000000"),
        "reason_codes": ("analyst_capacity_review",),
    }
    values.update(overrides)
    return MarketEventLiquidityCapacityCurveInput(**values)


def test_estimates_available_manual_capacity_curve_without_live_trading_surface():
    result = estimate_market_event_liquidity_capacity_curve(curve_input())

    assert isinstance(result, MarketEventLiquidityCapacityCurveResult)
    assert result.market_id == "market-election-resolution"
    assert result.capacity_status == "available"
    assert result.friction_bps == d("55.000000")
    assert result.net_cost_adjusted_edge_bps == d("85.000000")
    assert result.effective_liquidity_score == d("0.420000")
    assert result.capacity_tiers[0].tier_name == "research_probe"
    assert result.capacity_tiers[0].max_size == d("42.000000")
    assert result.capacity_tiers[1].tier_name == "manual_review"
    assert result.capacity_tiers[1].max_size == d("100.800000")
    assert result.capacity_tiers[2].tier_name == "capacity_ceiling"
    assert result.capacity_tiers[2].max_size == d("168.000000")
    assert result.recommended_manual_size_band.min_size == d("42.000000")
    assert result.recommended_manual_size_band.max_size == d("100.800000")
    assert result.reason_codes == (
        "analyst_capacity_review",
        "market_event_liquidity_capacity_curve",
        "capacity_available",
        "time_haircut_medium",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.payload == market_event_liquidity_capacity_curve_payload(result)


def test_blocks_capacity_when_cost_adjusted_edge_does_not_cover_liquidity_costs():
    result = estimate_market_event_liquidity_capacity_curve(
        curve_input(
            spread_bps=d("75.000000"),
            slippage_bps=d("80.000000"),
            cost_adjusted_edge_bps=d("120.000000"),
        ),
    )

    assert result.capacity_status == "blocked"
    assert result.net_cost_adjusted_edge_bps == d("-35.000000")
    assert result.recommended_manual_size_band.min_size == d("0.000000")
    assert result.recommended_manual_size_band.max_size == d("0.000000")
    assert all(tier.tier_status == "blocked" for tier in result.capacity_tiers)
    assert "edge_not_cost_covering" in result.reason_codes
    assert "capacity_blocked" in result.reason_codes


def test_watch_capacity_for_thin_depth_low_volume_or_near_resolution():
    result = estimate_market_event_liquidity_capacity_curve(
        curve_input(
            depth_score=d("0.250000"),
            daily_volume_score=d("0.300000"),
            time_to_resolution_minutes=d("45.000000"),
            cost_adjusted_edge_bps=d("95.000000"),
            spread_bps=d("35.000000"),
            slippage_bps=d("30.000000"),
            reason_codes=(),
        ),
    )

    assert result.capacity_status == "watch"
    assert result.effective_liquidity_score == d("0.037500")
    assert result.capacity_tiers[0].max_size == d("3.750000")
    assert result.recommended_manual_size_band.min_size == d("0.000000")
    assert result.recommended_manual_size_band.max_size == d("3.750000")
    assert result.reason_codes == (
        "market_event_liquidity_capacity_curve",
        "capacity_watch",
        "thin_depth",
        "low_daily_volume",
        "near_resolution",
        "edge_buffer_thin",
        "time_haircut_low",
    )


def test_decimal_only_inputs_validate_ranges_and_reason_codes():
    with pytest.raises(ValueError, match="depth_score must be a Decimal"):
        curve_input(depth_score=0.8)

    with pytest.raises(ValueError, match="depth_score must be between 0 and 1"):
        curve_input(depth_score=d("1.000001"))

    with pytest.raises(ValueError, match="spread_bps must be nonnegative"):
        curve_input(spread_bps=d("-0.000001"))

    with pytest.raises(ValueError, match="time_to_resolution_minutes must be nonnegative"):
        curve_input(time_to_resolution_minutes=d("-1.000000"))

    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        curve_input(reason_codes=["analyst_capacity_review"])

    with pytest.raises(ValueError, match="market_id must be a canonical nonblank string"):
        curve_input(market_id=" market-election-resolution")


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged():
    preview_input = curve_input()
    result = estimate_market_event_liquidity_capacity_curve(preview_input)

    assert is_dataclass(preview_input)
    assert is_dataclass(result)

    with pytest.raises(FrozenInstanceError):
        preview_input.market_id = "other-market"

    with pytest.raises(FrozenInstanceError):
        result.capacity_status = "blocked"

    with pytest.raises(ValueError, match="paper_only must be True"):
        curve_input(paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        curve_input(readonly=False)


def test_payload_is_json_ready_and_contains_no_decimal_objects_or_unsafe_surface():
    result = estimate_market_event_liquidity_capacity_curve(curve_input())
    payload = market_event_liquidity_capacity_curve_payload(result)

    assert payload == result.payload
    assert payload["market_id"] == "market-election-resolution"
    assert payload["capacity_status"] == "available"
    assert payload["friction_bps"] == "55.000000"
    assert payload["net_cost_adjusted_edge_bps"] == "85.000000"
    assert payload["capacity_tiers"][1]["max_size"] == "100.800000"
    assert payload["recommended_manual_size_band"]["min_size"] == "42.000000"
    assert payload["recommended_manual_size_band"]["max_size"] == "100.800000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    unsafe = object.__new__(MarketEventLiquidityCapacityCurveResult)
    object.__setattr__(unsafe, "paper_only", False)
    object.__setattr__(unsafe, "report_only", True)
    object.__setattr__(unsafe, "readonly", True)
    with pytest.raises(ValueError, match="paper_only must be True"):
        market_event_liquidity_capacity_curve_payload(unsafe)
