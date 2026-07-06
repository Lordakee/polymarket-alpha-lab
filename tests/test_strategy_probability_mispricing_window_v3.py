from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_probability_mispricing_window_v3 import (
    StrategyProbabilityMispricingWindowV3Config,
    StrategyProbabilityMispricingWindowV3Input,
    StrategyProbabilityMispricingWindowV3Result,
    evaluate_strategy_probability_mispricing_window_v3,
    strategy_probability_mispricing_window_v3_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> StrategyProbabilityMispricingWindowV3Config:
    values = {
        "config_version": "strategy-probability-mispricing-window-v3",
        "min_open_abs_probability_gap": d("0.080000"),
        "min_watch_abs_probability_gap": d("0.030000"),
        "min_open_cost_adjusted_edge": d("0.015000"),
        "min_watch_cost_adjusted_edge": d("0.000000"),
        "min_open_liquidity": d("1000.000000"),
        "min_watch_liquidity": d("250.000000"),
        "min_open_time_to_resolution": d("3600.000000"),
        "min_watch_time_to_resolution": d("900.000000"),
        "max_open_recent_probability_velocity": d("0.050000"),
        "max_watch_recent_probability_velocity": d("0.150000"),
    }
    values.update(overrides)
    return StrategyProbabilityMispricingWindowV3Config(**values)


def _window_input(**overrides: object) -> StrategyProbabilityMispricingWindowV3Input:
    values = {
        "candidate_id": "fed-cut-yes-window",
        "market_slug": "fed-cut-2026",
        "market_probability": d("0.420000"),
        "forecast_probability": d("0.530000"),
        "cost_adjusted_edge": d("0.025000"),
        "liquidity": d("2000.000000"),
        "time_to_resolution": d("172800.000000"),
        "recent_probability_velocity": d("0.020000"),
        "reason_codes": ("paper_signal",),
    }
    values.update(overrides)
    return StrategyProbabilityMispricingWindowV3Input(**values)


def test_probability_mispricing_window_v3_opens_when_all_open_thresholds_clear() -> None:
    result = evaluate_strategy_probability_mispricing_window_v3(
        _window_input(),
        config=_config(),
    )

    assert isinstance(result, StrategyProbabilityMispricingWindowV3Result)
    assert result.window_status == "open"
    assert result.probability_gap == d("0.110000")
    assert result.abs_probability_gap == d("0.110000")
    assert result.mispriced_side == "yes"
    assert result.reason_codes == (
        "paper_signal",
        "mispricing_window_open",
        "probability_gap_clears_open",
        "cost_adjusted_edge_clears_open",
        "liquidity_clears_open",
        "resolution_window_clears_open",
        "probability_velocity_stable",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_probability_mispricing_window_v3_watches_when_signal_is_positive_but_not_clean() -> None:
    result = evaluate_strategy_probability_mispricing_window_v3(
        _window_input(
            forecast_probability=d("0.480000"),
            cost_adjusted_edge=d("0.010000"),
            liquidity=d("600.000000"),
            time_to_resolution=d("1800.000000"),
            recent_probability_velocity=d("0.070000"),
        ),
        config=_config(),
    )

    assert result.window_status == "watch"
    assert result.probability_gap == d("0.060000")
    assert result.abs_probability_gap == d("0.060000")
    assert result.mispriced_side == "yes"
    assert result.reason_codes == (
        "paper_signal",
        "mispricing_window_watch",
        "probability_gap_below_open",
        "cost_adjusted_edge_below_open",
        "liquidity_below_open",
        "resolution_window_below_open",
        "probability_velocity_above_open",
    )


def test_probability_mispricing_window_v3_closes_when_watch_thresholds_fail() -> None:
    result = evaluate_strategy_probability_mispricing_window_v3(
        _window_input(
            forecast_probability=d("0.440000"),
            cost_adjusted_edge=d("-0.001000"),
            liquidity=d("100.000000"),
            time_to_resolution=d("600.000000"),
            recent_probability_velocity=d("0.200000"),
        ),
        config=_config(),
    )

    assert result.window_status == "closed"
    assert result.probability_gap == d("0.020000")
    assert result.abs_probability_gap == d("0.020000")
    assert result.reason_codes == (
        "paper_signal",
        "mispricing_window_closed",
        "probability_gap_below_watch",
        "cost_adjusted_edge_below_watch",
        "liquidity_below_watch",
        "resolution_window_below_watch",
        "probability_velocity_above_watch",
    )


def test_probability_mispricing_window_v3_tracks_no_side_when_forecast_is_below_market() -> None:
    result = evaluate_strategy_probability_mispricing_window_v3(
        _window_input(
            market_probability=d("0.610000"),
            forecast_probability=d("0.500000"),
        ),
        config=_config(),
    )

    assert result.window_status == "open"
    assert result.probability_gap == d("-0.110000")
    assert result.abs_probability_gap == d("0.110000")
    assert result.mispriced_side == "no"


def test_probability_mispricing_window_v3_uses_decimal_only_public_numbers() -> None:
    result = evaluate_strategy_probability_mispricing_window_v3(
        _window_input(),
        config=_config(),
    )

    for field in fields(result):
        if field.name in {
            "market_probability",
            "forecast_probability",
            "probability_gap",
            "abs_probability_gap",
            "cost_adjusted_edge",
            "liquidity",
            "time_to_resolution",
            "recent_probability_velocity",
        }:
            assert type(getattr(result, field.name)) is Decimal

    with pytest.raises(ValueError, match="market_probability must be a Decimal"):
        _window_input(market_probability=0.42)
    with pytest.raises(ValueError, match="min_open_liquidity must be a Decimal"):
        _config(min_open_liquidity=1000.0)


def test_probability_mispricing_window_v3_validates_flags_reasons_and_freezes_dataclasses() -> None:
    window_input = _window_input()
    result = evaluate_strategy_probability_mispricing_window_v3(
        window_input,
        config=_config(),
    )

    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        _window_input(reason_codes=["paper_signal"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        _window_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        _config(readonly=False)
    with pytest.raises(ValueError, match="config must be a StrategyProbabilityMispricingWindowV3Config"):
        evaluate_strategy_probability_mispricing_window_v3(window_input, config=object())
    with pytest.raises(FrozenInstanceError):
        result.window_status = "closed"


def test_probability_mispricing_window_v3_payload_is_json_ready_and_report_only() -> None:
    result = evaluate_strategy_probability_mispricing_window_v3(
        _window_input(),
        config=_config(),
    )

    payload = strategy_probability_mispricing_window_v3_payload(result)

    assert payload["candidate_id"] == "fed-cut-yes-window"
    assert payload["window_status"] == "open"
    assert payload["market_probability"] == "0.420000"
    assert payload["forecast_probability"] == "0.530000"
    assert payload["probability_gap"] == "0.110000"
    assert payload["abs_probability_gap"] == "0.110000"
    assert payload["cost_adjusted_edge"] == "0.025000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    unsafe = object.__new__(StrategyProbabilityMispricingWindowV3Result)
    object.__setattr__(unsafe, "paper_only", False)
    object.__setattr__(unsafe, "report_only", True)
    object.__setattr__(unsafe, "readonly", True)
    with pytest.raises(ValueError, match="paper_only must be True"):
        strategy_probability_mispricing_window_v3_payload(unsafe)


def test_probability_mispricing_window_v3_surface_has_no_live_db_or_order_fields() -> None:
    for cls in (
        StrategyProbabilityMispricingWindowV3Config,
        StrategyProbabilityMispricingWindowV3Input,
        StrategyProbabilityMispricingWindowV3Result,
    ):
        field_names = {field.name for field in fields(cls)}
        assert {"paper_only", "report_only", "readonly"} <= field_names
        assert not any(
            forbidden in field_name
            for field_name in field_names
            for forbidden in (
                "auth",
                "db",
                "database",
                "live",
                "order",
                "trade",
                "trading",
                "wallet",
            )
        )
