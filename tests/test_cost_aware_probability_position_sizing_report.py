from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from polymarket_alpha_lab.cost_aware_probability_position_sizing_report import (
    CostAwareProbabilityPositionSizingConfig,
    CostAwareProbabilityPositionSizingInput,
    CostAwareProbabilityPositionSizingReport,
    build_cost_aware_probability_position_sizing_report,
    cost_aware_probability_position_sizing_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides):
    values = {
        "config_version": "cost-aware-probability-position-sizing-v0",
        "candidate_fraction_cap": d("0.080000"),
        "watch_fraction_cap": d("0.030000"),
        "min_candidate_edge_to_threshold": d("0.040000"),
        "min_watch_edge_to_threshold": d("0.010000"),
        "min_liquidity_depth": d("1000.000000"),
        "max_spread": d("0.030000"),
        "min_settlement_risk_headroom": d("0.200000"),
        "min_team_calibration_confidence": d("0.650000"),
    }
    values.update(overrides)
    return CostAwareProbabilityPositionSizingConfig(**values)


def _sizing_input(**overrides):
    values = {
        "market_id": "fed-cut-2026-yes",
        "forecast_yes_probability": d("0.620000"),
        "market_probability": d("0.540000"),
        "cost_adjusted_threshold": d("0.570000"),
        "edge_to_threshold": d("0.050000"),
        "liquidity_depth": d("2500.000000"),
        "spread": d("0.018000"),
        "settlement_risk_headroom": d("0.480000"),
        "team_calibration_confidence": d("0.820000"),
    }
    values.update(overrides)
    return CostAwareProbabilityPositionSizingInput(**values)


def test_builds_candidate_sizing_report_from_cost_aware_probability_inputs():
    report = build_cost_aware_probability_position_sizing_report(
        _sizing_input(),
        config=_config(),
    )

    assert isinstance(report, CostAwareProbabilityPositionSizingReport)
    assert report.market_id == "fed-cut-2026-yes"
    assert report.forecast_yes_probability == d("0.620000")
    assert report.market_probability == d("0.540000")
    assert report.cost_adjusted_threshold == d("0.570000")
    assert report.raw_probability_edge == d("0.080000")
    assert report.edge_to_threshold == d("0.050000")
    assert report.max_position_fraction == d("0.051250")
    assert report.risk_band == "candidate"
    assert report.blocker_reasons == ()
    assert report.attention_reasons == ("spread_present",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_caps_watch_sizing_when_edge_is_positive_but_below_candidate_floor():
    report = build_cost_aware_probability_position_sizing_report(
        _sizing_input(edge_to_threshold=d("0.020000")),
        config=_config(),
    )

    assert report.risk_band == "watch"
    assert report.max_position_fraction == d("0.020500")
    assert report.blocker_reasons == ()
    assert report.attention_reasons == (
        "edge_to_threshold_below_candidate",
        "spread_present",
    )


def test_blocks_sizing_when_cost_threshold_and_risk_constraints_fail():
    report = build_cost_aware_probability_position_sizing_report(
        _sizing_input(
            forecast_yes_probability=d("0.560000"),
            edge_to_threshold=d("-0.010000"),
            liquidity_depth=d("300.000000"),
            spread=d("0.055000"),
            settlement_risk_headroom=d("0.120000"),
            team_calibration_confidence=d("0.500000"),
        ),
        config=_config(),
    )

    assert report.risk_band == "blocked"
    assert report.max_position_fraction == d("0.000000")
    assert report.blocker_reasons == (
        "forecast_below_cost_adjusted_threshold",
        "edge_to_threshold_below_watch",
        "insufficient_liquidity_depth",
        "spread_above_limit",
        "settlement_risk_headroom_below_minimum",
        "team_calibration_confidence_below_minimum",
    )
    assert report.attention_reasons == ()


def test_requires_decimal_only_inputs_and_readonly_safety_flags():
    with pytest.raises(ValueError, match="forecast_yes_probability must be a Decimal"):
        _sizing_input(forecast_yes_probability=0.62)

    with pytest.raises(ValueError, match="max_spread must be a Decimal"):
        _config(max_spread=0.03)

    with pytest.raises(ValueError, match="paper_only must be True"):
        _sizing_input(paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        _config(readonly=False)


def test_dataclasses_are_frozen():
    sizing_input = _sizing_input()
    report = build_cost_aware_probability_position_sizing_report(
        sizing_input,
        config=_config(),
    )

    with pytest.raises(FrozenInstanceError):
        sizing_input.market_id = "changed"

    with pytest.raises(FrozenInstanceError):
        report.max_position_fraction = d("0.010000")


def test_payload_is_json_ready_and_preserves_report_only_boundaries():
    report = build_cost_aware_probability_position_sizing_report(
        _sizing_input(edge_to_threshold=d("0.020000")),
        config=_config(),
    )

    payload = cost_aware_probability_position_sizing_payload(report)

    assert payload["market_id"] == "fed-cut-2026-yes"
    assert payload["max_position_fraction"] == "0.020500"
    assert payload["risk_band"] == "watch"
    assert payload["blocker_reasons"] == []
    assert payload["attention_reasons"] == [
        "edge_to_threshold_below_candidate",
        "spread_present",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    unsafe = object.__new__(CostAwareProbabilityPositionSizingReport)
    object.__setattr__(unsafe, "paper_only", False)
    object.__setattr__(unsafe, "report_only", True)
    object.__setattr__(unsafe, "readonly", True)
    with pytest.raises(ValueError, match="paper_only must be True"):
        cost_aware_probability_position_sizing_payload(unsafe)
