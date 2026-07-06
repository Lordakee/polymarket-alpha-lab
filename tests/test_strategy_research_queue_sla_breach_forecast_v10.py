from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_research_queue_sla_breach_forecast_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def queue_input(**overrides: object):
    module = api()
    values = {
        "queue_lane": "policy_research",
        "assigned_priority": "medium",
        "team_capacity_score": d("0.800000"),
        "open_ticket_count": d("3.000000"),
        "average_resolution_minutes": d("30.000000"),
        "time_to_market_resolution_minutes": d("240.000000"),
        "human_review_required": False,
    }
    values.update(overrides)
    return module.ResearchQueueSlaBreachForecastV10Input(**values)


def evaluate(**overrides: object):
    return api().strategy_research_queue_sla_breach_forecast_v10(
        queue_input(**overrides),
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for child in value.values():
            items.extend(walk(child))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for child in value:
            items.extend(walk(child))
        return tuple(items)
    return (value,)


def test_clear_capacity_returns_on_track_readonly_payload() -> None:
    result = evaluate()

    assert is_dataclass(result)
    assert result.breach_risk_status == "on_track"
    assert result.expected_delay_minutes == d("0.000000")
    assert result.escalation_action == "monitor"
    assert result.reason_codes == (
        "priority_medium",
        "capacity_healthy",
        "ticket_pressure_normal",
        "resolution_window_clear",
        "human_review_not_required",
        "breach_risk_on_track",
        "escalation_monitor",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.payload
    assert payload == api().strategy_research_queue_sla_breach_forecast_v10_payload(result)
    assert payload["config_version"] == "strategy-research-queue-sla-breach-forecast-v10"
    assert payload["queue_lane"] == "policy_research"
    assert payload["assigned_priority"] == "medium"
    assert payload["team_capacity_score"] == "0.800000"
    assert payload["open_ticket_count"] == "3.000000"
    assert payload["expected_delay_minutes"] == "0.000000"
    assert payload["breach_risk_status"] == "on_track"
    assert payload["escalation_action"] == "monitor"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is float for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))


def test_overloaded_urgent_manual_review_forecasts_breach_and_page_lead() -> None:
    result = evaluate(
        assigned_priority="urgent",
        team_capacity_score=d("0.250000"),
        open_ticket_count=d("8.000000"),
        average_resolution_minutes=d("75.000000"),
        time_to_market_resolution_minutes=d("90.000000"),
        human_review_required=True,
    )

    assert result.breach_risk_status == "breach_likely"
    assert result.expected_delay_minutes == d("535.000000")
    assert result.escalation_action == "page_research_lead"
    assert result.reason_codes == (
        "priority_urgent",
        "capacity_critical",
        "ticket_pressure_high",
        "resolution_window_compressed",
        "human_review_required",
        "expected_delay_positive",
        "breach_risk_likely",
        "escalation_page_research_lead",
    )


def test_priority_and_review_pressure_can_trigger_watch_without_delay() -> None:
    result = evaluate(
        assigned_priority="high",
        team_capacity_score=d("0.900000"),
        open_ticket_count=d("1.000000"),
        average_resolution_minutes=d("20.000000"),
        time_to_market_resolution_minutes=d("180.000000"),
        human_review_required=True,
    )

    assert result.expected_delay_minutes == d("0.000000")
    assert result.breach_risk_status == "watch"
    assert result.escalation_action == "queue_owner_review"
    assert "priority_high" in result.reason_codes
    assert "human_review_required" in result.reason_codes


def test_validation_requires_decimal_inputs_bounds_flags_and_frozen_outputs() -> None:
    module = api()
    result = evaluate()

    with pytest.raises(FrozenInstanceError):
        result.breach_risk_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="team_capacity_score must be a Decimal"):
        queue_input(team_capacity_score=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="open_ticket_count must be a Decimal"):
        queue_input(open_ticket_count=3)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="team_capacity_score must be a Decimal"):
        queue_input(team_capacity_score=_DecimalSubclass("0.800000"))

    with pytest.raises(ValueError, match="average_resolution_minutes must be finite"):
        queue_input(average_resolution_minutes=Decimal("NaN"))

    with pytest.raises(ValueError, match="team_capacity_score must be between 0 and 1"):
        queue_input(team_capacity_score=d("1.000001"))

    with pytest.raises(ValueError, match="open_ticket_count must be a whole Decimal"):
        queue_input(open_ticket_count=d("1.500000"))

    with pytest.raises(ValueError, match="average_resolution_minutes must be greater than zero"):
        queue_input(average_resolution_minutes=d("0.000000"))

    with pytest.raises(ValueError, match="assigned_priority must be one of"):
        queue_input(assigned_priority="rush")

    with pytest.raises(ValueError, match="human_review_required must be a bool"):
        queue_input(human_review_required=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="input must be paper_only"):
        queue_input(paper_only=False)

    with pytest.raises(ValueError, match="result must be readonly"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="reason_codes must match"):
        module.ResearchQueueSlaBreachForecastV10Result(
            queue_lane="policy_research",
            assigned_priority="medium",
            team_capacity_score=d("0.800000"),
            open_ticket_count=d("3.000000"),
            average_resolution_minutes=d("30.000000"),
            time_to_market_resolution_minutes=d("240.000000"),
            human_review_required=False,
            breach_risk_status="on_track",
            expected_delay_minutes=d("0.000000"),
            escalation_action="monitor",
            reason_codes=("breach_risk_likely",),
        )


def test_payload_rejects_bad_dicts_and_non_report_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="payload must be readonly"):
        module.strategy_research_queue_sla_breach_forecast_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.strategy_research_queue_sla_breach_forecast_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "expected_delay_minutes": 1.5,
            },
        )

    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        module.strategy_research_queue_sla_breach_forecast_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "open_ticket_count": 3,
            },
        )

    with pytest.raises(ValueError, match="payload field is not supported"):
        module.strategy_research_queue_sla_breach_forecast_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "extra": "field"},
        )

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_research_queue_sla_breach_forecast_v10_payload(object())


def test_module_scope_is_paper_report_readonly_without_side_effect_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_research_queue_sla_breach_forecast_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "signing",
        "order placement",
        "submit",
        "cancel",
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
