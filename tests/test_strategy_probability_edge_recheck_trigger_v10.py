import ast
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_probability_edge_recheck_trigger_v10 import (
    ProbabilityEdgeRecheckTriggerV10Input,
    ProbabilityEdgeRecheckTriggerV10Result,
    probability_edge_recheck_trigger_v10_payload,
    strategy_probability_edge_recheck_trigger_v10,
)


def _trigger_input(**overrides):
    values = {
        "market_id": "market-123",
        "last_edge_bps": Decimal("80.000000"),
        "current_market_move_bps": Decimal("65.000000"),
        "source_freshness_status": "stale",
        "forecast_confidence_tier": "medium",
        "time_to_resolution_minutes": Decimal("90.000000"),
        "cost_change_bps": Decimal("15.000000"),
    }
    values.update(overrides)
    return ProbabilityEdgeRecheckTriggerV10Input(**values)


def test_strategy_triggers_critical_recheck_for_stale_source_and_edge_risk():
    result = strategy_probability_edge_recheck_trigger_v10(_trigger_input())

    assert isinstance(result, ProbabilityEdgeRecheckTriggerV10Result)
    assert result.market_id == "market-123"
    assert result.last_edge_bps == Decimal("80.000000")
    assert result.current_market_move_bps == Decimal("65.000000")
    assert result.cost_change_bps == Decimal("15.000000")
    assert result.recheck_status == "recheck_now"
    assert result.recheck_priority == "critical"
    assert result.next_recheck_minutes == Decimal("0.000000")
    assert result.reason_codes == (
        "source_freshness_stale",
        "forecast_confidence_medium",
        "resolution_window_near",
        "market_move_large",
        "cost_change_present",
        "edge_buffer_at_risk",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.payload == probability_edge_recheck_trigger_v10_payload(result)


def test_strategy_schedules_recheck_for_low_confidence_even_without_price_move():
    result = strategy_probability_edge_recheck_trigger_v10(
        _trigger_input(
            last_edge_bps=Decimal("140.000000"),
            current_market_move_bps=Decimal("0.000000"),
            source_freshness_status="fresh",
            forecast_confidence_tier="low",
            time_to_resolution_minutes=Decimal("180.000000"),
            cost_change_bps=Decimal("0.000000"),
        ),
    )

    assert result.recheck_status == "recheck_scheduled"
    assert result.recheck_priority == "medium"
    assert result.next_recheck_minutes == Decimal("15.000000")
    assert result.reason_codes == (
        "source_freshness_fresh",
        "forecast_confidence_low",
        "resolution_window_soon",
        "market_move_immaterial",
        "cost_change_immaterial",
        "edge_buffer_stable",
    )


def test_strategy_defers_stable_fresh_high_confidence_market():
    result = strategy_probability_edge_recheck_trigger_v10(
        _trigger_input(
            last_edge_bps=Decimal("250.000000"),
            current_market_move_bps=Decimal("8.000000"),
            source_freshness_status="fresh",
            forecast_confidence_tier="high",
            time_to_resolution_minutes=Decimal("1440.000000"),
            cost_change_bps=Decimal("0.000000"),
        ),
    )

    assert result.recheck_status == "no_recheck"
    assert result.recheck_priority == "low"
    assert result.next_recheck_minutes == Decimal("240.000000")
    assert result.reason_codes == (
        "source_freshness_fresh",
        "forecast_confidence_high",
        "resolution_window_open",
        "market_move_immaterial",
        "cost_change_immaterial",
        "edge_buffer_stable",
    )


def test_strategy_uses_absolute_move_and_cost_change_for_signed_inputs():
    result = strategy_probability_edge_recheck_trigger_v10(
        _trigger_input(
            last_edge_bps=Decimal("-40.000000"),
            current_market_move_bps=Decimal("-45.000000"),
            source_freshness_status="fresh",
            forecast_confidence_tier="high",
            time_to_resolution_minutes=Decimal("600.000000"),
            cost_change_bps=Decimal("-12.000000"),
        ),
    )

    assert result.recheck_status == "recheck_now"
    assert result.recheck_priority == "high"
    assert result.next_recheck_minutes == Decimal("5.000000")
    assert result.reason_codes == (
        "source_freshness_fresh",
        "forecast_confidence_high",
        "resolution_window_open",
        "market_move_moderate",
        "cost_change_present",
        "edge_buffer_at_risk",
    )
    assert result.payload["absolute_market_move_bps"] == "45.000000"
    assert result.payload["absolute_cost_change_bps"] == "12.000000"
    assert result.payload["absolute_last_edge_bps"] == "40.000000"


def test_strategy_requires_decimal_inputs_supported_labels_and_safety_flags():
    with pytest.raises(ValueError, match="last_edge_bps must be a Decimal"):
        _trigger_input(last_edge_bps=80)

    with pytest.raises(ValueError, match="time_to_resolution_minutes must be nonnegative"):
        _trigger_input(time_to_resolution_minutes=Decimal("-0.000001"))

    with pytest.raises(ValueError, match="source_freshness_status is not supported"):
        _trigger_input(source_freshness_status="delayed")

    with pytest.raises(ValueError, match="forecast_confidence_tier is not supported"):
        _trigger_input(forecast_confidence_tier="certain")

    with pytest.raises(ValueError, match="input must be paper_only"):
        _trigger_input(paper_only=False)

    with pytest.raises(ValueError, match="input must be readonly"):
        _trigger_input(readonly=False)


def test_strategy_rejects_non_input_objects_and_bad_result_consistency():
    with pytest.raises(ValueError, match="trigger_input must be a"):
        strategy_probability_edge_recheck_trigger_v10(object())

    with pytest.raises(ValueError, match="reason_codes must match trigger inputs"):
        ProbabilityEdgeRecheckTriggerV10Result(
            market_id="market-123",
            last_edge_bps=Decimal("80.000000"),
            current_market_move_bps=Decimal("65.000000"),
            source_freshness_status="stale",
            forecast_confidence_tier="medium",
            time_to_resolution_minutes=Decimal("90.000000"),
            cost_change_bps=Decimal("15.000000"),
            absolute_last_edge_bps=Decimal("80.000000"),
            absolute_market_move_bps=Decimal("65.000000"),
            absolute_cost_change_bps=Decimal("15.000000"),
            recheck_status="recheck_now",
            recheck_priority="critical",
            next_recheck_minutes=Decimal("0.000000"),
            reason_codes=("source_freshness_stale",),
        )


def test_strategy_dataclasses_are_frozen():
    trigger_input = _trigger_input()
    result = strategy_probability_edge_recheck_trigger_v10(trigger_input)

    with pytest.raises(FrozenInstanceError):
        trigger_input.market_id = "other-market"

    with pytest.raises(FrozenInstanceError):
        result.recheck_priority = "low"


def test_payload_is_json_ready_and_keeps_readonly_report_surface():
    result = strategy_probability_edge_recheck_trigger_v10(_trigger_input())
    payload = probability_edge_recheck_trigger_v10_payload(result)

    assert payload == result.payload
    assert payload["market_id"] == "market-123"
    assert payload["last_edge_bps"] == "80.000000"
    assert payload["current_market_move_bps"] == "65.000000"
    assert payload["cost_change_bps"] == "15.000000"
    assert payload["recheck_status"] == "recheck_now"
    assert payload["recheck_priority"] == "critical"
    assert payload["next_recheck_minutes"] == "0.000000"
    assert payload["reason_codes"] == [
        "source_freshness_stale",
        "forecast_confidence_medium",
        "resolution_window_near",
        "market_move_large",
        "cost_change_present",
        "edge_buffer_at_risk",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert all(not isinstance(value, Decimal) for value in payload.values())


def test_strategy_module_has_no_live_or_persistent_surface_area():
    source = Path(
        "src/polymarket_alpha_lab/strategy_probability_edge_recheck_trigger_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live trading",
        "auth",
        "wallet",
        "signing",
        "order placement",
        "database",
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
