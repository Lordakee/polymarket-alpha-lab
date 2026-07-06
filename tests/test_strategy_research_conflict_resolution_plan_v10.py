from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_research_conflict_resolution_plan_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def build_plan(**overrides):
    module = api()
    values = {
        "market_id": "btc-july-close-above-100k",
        "source_disagreement_status": "critical",
        "model_disagreement_status": "material",
        "resolution_risk_tier": "high",
        "missing_data_types": ("primary_source", "resolution_rule", "model_trace"),
        "time_to_resolution_minutes": d("45"),
        "team_capacity_score": d("0.250000"),
    }
    values.update(overrides)
    return module.build_strategy_research_conflict_resolution_plan_v10(**values)


def test_high_conflict_inputs_generate_escalating_readonly_plan() -> None:
    plan = build_plan()

    assert is_dataclass(plan)
    assert plan.plan_version == "strategy-research-conflict-resolution-plan-v10"
    assert plan.market_id == "btc-july-close-above-100k"
    assert plan.conflict_plan_status == "escalate"
    assert plan.escalation_required is True
    assert plan.reason_codes == (
        "strategy_research_conflict_resolution_plan_v10_source_conflict",
        "strategy_research_conflict_resolution_plan_v10_model_conflict",
        "strategy_research_conflict_resolution_plan_v10_high_resolution_risk",
        "strategy_research_conflict_resolution_plan_v10_missing_primary_source",
        "strategy_research_conflict_resolution_plan_v10_missing_resolution_rule",
        "strategy_research_conflict_resolution_plan_v10_missing_model_trace",
        "strategy_research_conflict_resolution_plan_v10_capacity_constrained",
    )
    assert plan.paper_only is True
    assert plan.report_only is True
    assert plan.readonly is True

    steps = plan.resolution_steps
    assert tuple(step.step_rank for step in steps) == (
        d("1"),
        d("2"),
        d("3"),
        d("4"),
        d("5"),
    )
    assert tuple(step.research_action for step in steps) == (
        "capture_current_research_evidence",
        "reconcile_source_disagreement",
        "review_model_disagreement",
        "collect_missing_resolution_data",
        "escalate_to_research_lead",
    )
    assert tuple(step.deadline_minutes for step in steps) == (
        d("0"),
        d("15"),
        d("30"),
        d("45"),
        d("45"),
    )
    assert tuple(step.step_status for step in steps) == (
        "planned",
        "planned",
        "planned",
        "planned",
        "escalation",
    )
    assert steps[3].reason_codes == (
        "strategy_research_conflict_resolution_plan_v10_missing_primary_source",
        "strategy_research_conflict_resolution_plan_v10_missing_resolution_rule",
        "strategy_research_conflict_resolution_plan_v10_missing_model_trace",
    )
    assert plan.payload.resolution_step_count == d("5")
    assert plan.payload.team_capacity_score == d("0.250000")


def test_clear_inputs_generate_recorded_no_conflict_plan() -> None:
    plan = build_plan(
        source_disagreement_status="aligned",
        model_disagreement_status="aligned",
        resolution_risk_tier="low",
        missing_data_types=(),
        time_to_resolution_minutes=d("120"),
        team_capacity_score=d("0.900000"),
    )

    assert plan.conflict_plan_status == "clear"
    assert plan.escalation_required is False
    assert plan.reason_codes == (
        "strategy_research_conflict_resolution_plan_v10_no_conflict",
    )
    assert tuple(step.research_action for step in plan.resolution_steps) == (
        "record_no_conflict_review",
    )
    assert plan.resolution_steps[0].deadline_minutes == d("120")
    assert plan.resolution_steps[0].step_status == "recorded"


def test_payload_helper_uses_decimal_strings_and_no_floats() -> None:
    payload = api().strategy_research_conflict_resolution_plan_v10_payload(build_plan())

    assert payload["payload"]["time_to_resolution_minutes"] == "45"
    assert payload["payload"]["team_capacity_score"] == "0.250000"
    assert payload["payload"]["resolution_step_count"] == "5"
    assert payload["resolution_steps"][0]["deadline_minutes"] == "0"
    assert payload["resolution_steps"][0]["step_rank"] == "1"
    assert all(not isinstance(value, float) for value in _walk_values(payload))


def test_validation_rejects_invalid_inputs_and_inconsistent_reports() -> None:
    module = api()

    with pytest.raises(ValueError, match="market_id"):
        build_plan(market_id=" btc ")
    with pytest.raises(ValueError, match="source_disagreement_status"):
        build_plan(source_disagreement_status="unknown")
    with pytest.raises(ValueError, match="missing_data_types"):
        build_plan(missing_data_types=("primary_source", "primary_source"))
    with pytest.raises(ValueError, match="time_to_resolution_minutes"):
        build_plan(time_to_resolution_minutes=45)
    with pytest.raises(ValueError, match="team_capacity_score"):
        build_plan(team_capacity_score=d("1.000001"))
    with pytest.raises(ValueError, match="request"):
        module.build_strategy_research_conflict_resolution_plan_v10_from_request(object())

    plan = build_plan()
    with pytest.raises(ValueError, match="conflict_plan_status"):
        replace(plan, conflict_plan_status="clear")
    with pytest.raises(ValueError, match="payload"):
        replace(plan, payload=replace(plan.payload, resolution_step_count=d("4")))


def test_hard_flags_public_dataclasses_are_frozen_and_decimal_only() -> None:
    module = api()
    request = module.StrategyResearchConflictResolutionPlanV10Request(
        market_id="btc-july-close-above-100k",
        source_disagreement_status="minor",
        model_disagreement_status="aligned",
        resolution_risk_tier="medium",
        missing_data_types=("timestamp",),
        time_to_resolution_minutes=d("90"),
        team_capacity_score=d("0.700000"),
    )
    plan = module.build_strategy_research_conflict_resolution_plan_v10_from_request(request)

    with pytest.raises(FrozenInstanceError):
        request.market_id = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        plan.resolution_steps[0].deadline_minutes = d("99")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        plan.conflict_plan_status = "clear"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(request, paper_only=False)
    with pytest.raises(ValueError, match="deadline_minutes"):
        replace(plan.resolution_steps[0], deadline_minutes=30)


def test_static_module_has_no_forbidden_surfaces_or_float_literals() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_research_conflict_resolution_plan_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "private_key",
        "live trading",
        "order placement",
        "database",
        "payload_json",
        "open(",
        "read(",
        "write(",
        "float(",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "read", "write", "float"}


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in _walk_values(child))
    return (value,)
