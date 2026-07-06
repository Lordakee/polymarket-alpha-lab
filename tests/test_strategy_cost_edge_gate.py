from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_cost_edge_gate import (
    StrategyCostEdgeGateConfig,
    StrategyCostEdgeGateInput,
    StrategyCostEdgeGateResult,
    evaluate_strategy_cost_edge_gate,
    strategy_cost_edge_gate_payload,
)


def _config(**overrides):
    values = {
        "config_version": "strategy-cost-edge-gate-v0",
        "min_candidate_cost_adjusted_edge": Decimal("0.010000"),
        "min_watch_cost_adjusted_edge": Decimal("0.000000"),
        "max_total_cost_per_share": Decimal("0.020000"),
        "max_spread_cost": Decimal("0.006000"),
        "max_fee_cost": Decimal("0.006000"),
        "max_slippage_cost": Decimal("0.006000"),
    }
    values.update(overrides)
    return StrategyCostEdgeGateConfig(**values)


def _edge_input(**overrides):
    values = {
        "candidate_id": "fed-cut-yes",
        "net_edge_per_share": Decimal("0.025000"),
        "total_cost_per_share": Decimal("0.012000"),
        "spread_cost": Decimal("0.003000"),
        "fee_cost": Decimal("0.004000"),
        "slippage_cost": Decimal("0.005000"),
        "reason_codes": ("paper_edge_present",),
    }
    values.update(overrides)
    return StrategyCostEdgeGateInput(**values)


def test_strategy_cost_edge_gate_marks_candidate_when_cost_adjusted_edge_clears_thresholds():
    result = evaluate_strategy_cost_edge_gate(_edge_input(), config=_config())

    assert isinstance(result, StrategyCostEdgeGateResult)
    assert result.candidate_id == "fed-cut-yes"
    assert result.gate_status == "candidate"
    assert result.net_edge_per_share == Decimal("0.025000")
    assert result.total_cost_per_share == Decimal("0.012000")
    assert result.spread_cost == Decimal("0.003000")
    assert result.fee_cost == Decimal("0.004000")
    assert result.slippage_cost == Decimal("0.005000")
    assert result.cost_adjusted_edge == Decimal("0.013000")
    assert result.reason_codes == (
        "paper_edge_present",
        "cost_edge_candidate",
        "cost_thresholds_passed",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_strategy_cost_edge_gate_marks_watch_when_edge_is_positive_but_below_candidate():
    result = evaluate_strategy_cost_edge_gate(
        _edge_input(net_edge_per_share=Decimal("0.017000")),
        config=_config(),
    )

    assert result.gate_status == "watch"
    assert result.cost_adjusted_edge == Decimal("0.005000")
    assert result.reason_codes == (
        "paper_edge_present",
        "cost_edge_watch",
        "cost_adjusted_edge_below_candidate",
    )


def test_strategy_cost_edge_gate_blocks_when_cost_adjusted_edge_is_negative():
    result = evaluate_strategy_cost_edge_gate(
        _edge_input(net_edge_per_share=Decimal("0.010000")),
        config=_config(),
    )

    assert result.gate_status == "blocked"
    assert result.cost_adjusted_edge == Decimal("-0.002000")
    assert result.reason_codes == (
        "paper_edge_present",
        "cost_edge_blocked",
        "cost_adjusted_edge_below_watch",
        "cost_drag_exceeds_edge",
    )


def test_strategy_cost_edge_gate_blocks_when_cost_component_exceeds_limit():
    result = evaluate_strategy_cost_edge_gate(
        _edge_input(
            net_edge_per_share=Decimal("0.050000"),
            total_cost_per_share=Decimal("0.021000"),
            spread_cost=Decimal("0.010000"),
            fee_cost=Decimal("0.004000"),
            slippage_cost=Decimal("0.007000"),
        ),
        config=_config(),
    )

    assert result.gate_status == "blocked"
    assert result.cost_adjusted_edge == Decimal("0.029000")
    assert result.reason_codes == (
        "paper_edge_present",
        "cost_edge_blocked",
        "total_cost_above_limit",
        "spread_cost_above_limit",
        "slippage_cost_above_limit",
    )


def test_strategy_cost_edge_gate_blocks_when_total_cost_does_not_match_components():
    result = evaluate_strategy_cost_edge_gate(
        _edge_input(total_cost_per_share=Decimal("0.013000")),
        config=_config(),
    )

    assert result.gate_status == "blocked"
    assert result.cost_adjusted_edge == Decimal("0.012000")
    assert "cost_component_total_mismatch" in result.reason_codes


def test_strategy_cost_edge_gate_uses_decimal_only_inputs():
    with pytest.raises(ValueError, match="net_edge_per_share must be a Decimal"):
        _edge_input(net_edge_per_share=0.025)

    with pytest.raises(ValueError, match="max_fee_cost must be a Decimal"):
        _config(max_fee_cost=0.006)


def test_strategy_cost_edge_gate_requires_tuple_reason_codes_and_hard_flags():
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        _edge_input(reason_codes=["paper_edge_present"])

    with pytest.raises(ValueError, match="paper_only must be True"):
        _edge_input(paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        _config(readonly=False)


def test_strategy_cost_edge_gate_dataclasses_are_frozen():
    edge_input = _edge_input()
    result = evaluate_strategy_cost_edge_gate(edge_input, config=_config())

    with pytest.raises(FrozenInstanceError):
        edge_input.candidate_id = "changed"

    with pytest.raises(FrozenInstanceError):
        result.gate_status = "watch"


def test_strategy_cost_edge_gate_payload_is_report_only_and_json_ready():
    result = evaluate_strategy_cost_edge_gate(
        _edge_input(net_edge_per_share=Decimal("0.017000")),
        config=_config(),
    )

    payload = strategy_cost_edge_gate_payload(result)

    assert payload["candidate_id"] == "fed-cut-yes"
    assert payload["gate_status"] == "watch"
    assert payload["cost_adjusted_edge"] == "0.005000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    unsafe = object.__new__(StrategyCostEdgeGateResult)
    object.__setattr__(unsafe, "paper_only", False)
    object.__setattr__(unsafe, "report_only", True)
    object.__setattr__(unsafe, "readonly", True)
    with pytest.raises(ValueError, match="paper_only must be True"):
        strategy_cost_edge_gate_payload(unsafe)
