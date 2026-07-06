import ast
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_cost_adjusted_probability_edge_v10 import (
    CostAdjustedProbabilityEdgeV10Input,
    CostAdjustedProbabilityEdgeV10Result,
    cost_adjusted_probability_edge_v10_payload,
    strategy_cost_adjusted_probability_edge_v10,
)


def _edge_input(**overrides):
    values = {
        "market_price_probability": Decimal("0.420000"),
        "forecast_probability": Decimal("0.470000"),
        "fee_cost_bps": Decimal("12.000000"),
        "slippage_cost_bps": Decimal("18.000000"),
        "settlement_cost_bps": Decimal("5.000000"),
        "resolution_risk_premium_bps": Decimal("20.000000"),
        "confidence_penalty_bps": Decimal("10.000000"),
    }
    values.update(overrides)
    return CostAdjustedProbabilityEdgeV10Input(**values)


def test_strategy_calculates_cost_adjusted_probability_edge_as_readonly_report():
    result = strategy_cost_adjusted_probability_edge_v10(_edge_input())

    assert isinstance(result, CostAdjustedProbabilityEdgeV10Result)
    assert result.market_price_probability == Decimal("0.420000")
    assert result.forecast_probability == Decimal("0.470000")
    assert result.raw_edge_bps == Decimal("500.000000")
    assert result.cost_adjusted_edge_bps == Decimal("435.000000")
    assert result.edge_status == "positive_edge"
    assert result.reason_codes == (
        "raw_edge_positive",
        "cost_adjusted_edge_positive",
        "fee_cost_present",
        "slippage_cost_present",
        "settlement_cost_present",
        "resolution_risk_premium_present",
        "confidence_penalty_present",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.payload == cost_adjusted_probability_edge_v10_payload(result)


def test_strategy_marks_positive_raw_edge_as_cost_dragged_when_costs_consume_it():
    result = strategy_cost_adjusted_probability_edge_v10(
        _edge_input(
            market_price_probability=Decimal("0.510000"),
            forecast_probability=Decimal("0.515000"),
            fee_cost_bps=Decimal("15.000000"),
            slippage_cost_bps=Decimal("20.000000"),
            settlement_cost_bps=Decimal("5.000000"),
            resolution_risk_premium_bps=Decimal("15.000000"),
            confidence_penalty_bps=Decimal("10.000000"),
        ),
    )

    assert result.raw_edge_bps == Decimal("50.000000")
    assert result.cost_adjusted_edge_bps == Decimal("-15.000000")
    assert result.edge_status == "cost_dragged_edge"
    assert result.reason_codes[:2] == (
        "raw_edge_positive",
        "cost_adjusted_edge_nonpositive",
    )
    assert "cost_drag_exceeds_raw_edge" in result.reason_codes


def test_strategy_marks_negative_forecast_gap_as_negative_edge():
    result = strategy_cost_adjusted_probability_edge_v10(
        _edge_input(
            market_price_probability=Decimal("0.600000"),
            forecast_probability=Decimal("0.550000"),
            fee_cost_bps=Decimal("0.000000"),
            slippage_cost_bps=Decimal("0.000000"),
            settlement_cost_bps=Decimal("0.000000"),
            resolution_risk_premium_bps=Decimal("0.000000"),
            confidence_penalty_bps=Decimal("0.000000"),
        ),
    )

    assert result.raw_edge_bps == Decimal("-500.000000")
    assert result.cost_adjusted_edge_bps == Decimal("-500.000000")
    assert result.edge_status == "negative_edge"
    assert result.reason_codes == (
        "raw_edge_nonpositive",
        "cost_adjusted_edge_nonpositive",
    )


def test_strategy_requires_decimal_inputs_and_probability_ranges():
    with pytest.raises(ValueError, match="market_price_probability must be a Decimal"):
        _edge_input(market_price_probability=0.42)

    with pytest.raises(
        ValueError,
        match="market_price_probability must be between 0 and 1",
    ):
        _edge_input(market_price_probability=Decimal("1.000001"))

    with pytest.raises(ValueError, match="forecast_probability must be between 0 and 1"):
        _edge_input(forecast_probability=Decimal("-0.000001"))

    with pytest.raises(ValueError, match="fee_cost_bps must be nonnegative"):
        _edge_input(fee_cost_bps=Decimal("-0.000001"))


def test_strategy_rejects_non_decimal_numeric_values_and_bad_flags():
    with pytest.raises(ValueError, match="slippage_cost_bps must be a Decimal"):
        _edge_input(slippage_cost_bps=18)

    with pytest.raises(ValueError, match="confidence_penalty_bps must be finite"):
        _edge_input(confidence_penalty_bps=Decimal("NaN"))

    with pytest.raises(ValueError, match="input must be paper_only"):
        _edge_input(paper_only=False)

    with pytest.raises(ValueError, match="input must be readonly"):
        _edge_input(readonly=False)


def test_strategy_dataclasses_are_frozen():
    edge_input = _edge_input()
    result = strategy_cost_adjusted_probability_edge_v10(edge_input)

    with pytest.raises(FrozenInstanceError):
        edge_input.market_price_probability = Decimal("0.430000")

    with pytest.raises(FrozenInstanceError):
        result.edge_status = "negative_edge"


def test_payload_is_json_ready_and_keeps_report_surface_readonly():
    result = strategy_cost_adjusted_probability_edge_v10(_edge_input())
    payload = cost_adjusted_probability_edge_v10_payload(result)

    assert payload == result.payload
    assert payload["market_price_probability"] == "0.420000"
    assert payload["forecast_probability"] == "0.470000"
    assert payload["raw_edge_bps"] == "500.000000"
    assert payload["cost_adjusted_edge_bps"] == "435.000000"
    assert payload["edge_status"] == "positive_edge"
    assert payload["reason_codes"] == [
        "raw_edge_positive",
        "cost_adjusted_edge_positive",
        "fee_cost_present",
        "slippage_cost_present",
        "settlement_cost_present",
        "resolution_risk_premium_present",
        "confidence_penalty_present",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert all(not isinstance(value, Decimal) for value in payload.values())


def test_strategy_module_has_no_live_or_persistent_surface_area():
    source = Path(
        "src/polymarket_alpha_lab/strategy_cost_adjusted_probability_edge_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live trading",
        "auth",
        "wallet",
        "order placement",
        "database",
        "network",
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
