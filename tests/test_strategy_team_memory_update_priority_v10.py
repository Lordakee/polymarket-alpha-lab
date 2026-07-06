from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_memory_update_priority_v10.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_memory_update_priority_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def priority_input(**overrides: object):
    module = api()
    values = {
        "team_id": "team-memory-alpha",
        "category": "macro",
        "feedback_route_status": "logged",
        "forecast_error_bps": d("40.000000"),
        "source_gap_count": d("0.000000"),
        "postmortem_status": "complete",
        "days_since_last_update": d("2.000000"),
        "sample_size": d("20.000000"),
    }
    values.update(overrides)
    return module.StrategyTeamMemoryUpdatePriorityV10Input(**values)


def evaluate(**overrides: object):
    module = api()
    return module.evaluate_strategy_team_memory_update_priority_v10(
        priority_input(**overrides),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_urgent_memory_update_clamps_score_and_routes_all_actions() -> None:
    decision = evaluate(
        team_id="team-calibration",
        category="election-resolution",
        feedback_route_status="review_required",
        forecast_error_bps=d("750.000000"),
        source_gap_count=d("4.000000"),
        postmortem_status="missing",
        days_since_last_update=d("45.000000"),
        sample_size=d("36.000000"),
    )

    assert is_dataclass(decision)
    assert decision.team_id == "team-calibration"
    assert decision.category == "election-resolution"
    assert decision.feedback_route_status == "review_required"
    assert decision.forecast_error_bps == d("750.000000")
    assert decision.source_gap_count == d("4.000000")
    assert decision.postmortem_status == "missing"
    assert decision.days_since_last_update == d("45.000000")
    assert decision.sample_size == d("36.000000")
    assert decision.update_priority_status == "urgent_update"
    assert decision.priority_score == d("100.000000")
    assert decision.memory_update_actions == (
        "apply_forecast_calibration_update",
        "refresh_source_gap_playbook",
        "complete_postmortem_memory_update",
        "refresh_stale_team_memory",
        "escalate_memory_update_review",
    )
    assert decision.reason_codes == (
        "feedback_route_status_review_required",
        "forecast_error_high",
        "source_gap_count_high",
        "postmortem_missing",
        "memory_update_stale",
        "sample_size_sufficient",
        "priority_score_clamped",
        "update_priority_status_urgent_update",
    )
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True


def test_monitor_priority_keeps_readonly_status_with_single_action() -> None:
    decision = evaluate()

    assert decision.priority_score == d("3.000000")
    assert decision.update_priority_status == "monitor"
    assert decision.memory_update_actions == ("continue_monitoring",)
    assert decision.reason_codes == (
        "feedback_route_status_logged",
        "forecast_error_low",
        "source_gap_absent",
        "postmortem_complete",
        "memory_recent",
        "sample_size_sufficient",
        "update_priority_status_monitor",
    )


def test_queue_prioritize_and_blocked_statuses_are_distinct() -> None:
    queued = evaluate(
        feedback_route_status="queued",
        forecast_error_bps=d("260.000000"),
        source_gap_count=d("1.000000"),
        postmortem_status="pending",
        days_since_last_update=d("20.000000"),
        sample_size=d("10.000000"),
    )
    prioritized = evaluate(
        feedback_route_status="review_required",
        forecast_error_bps=d("500.000000"),
        source_gap_count=d("2.000000"),
        postmortem_status="pending",
        days_since_last_update=d("28.000000"),
        sample_size=d("12.000000"),
    )
    blocked = evaluate(
        feedback_route_status="blocked",
        forecast_error_bps=d("300.000000"),
        source_gap_count=d("1.000000"),
        postmortem_status="blocked",
        days_since_last_update=d("12.000000"),
        sample_size=d("8.000000"),
    )

    assert queued.priority_score == d("49.000000")
    assert queued.update_priority_status == "queue_update"
    assert queued.memory_update_actions == (
        "apply_forecast_calibration_update",
        "refresh_source_gap_playbook",
        "complete_postmortem_memory_update",
        "refresh_stale_team_memory",
    )

    assert prioritized.priority_score == d("76.000000")
    assert prioritized.update_priority_status == "prioritize_update"
    assert prioritized.memory_update_actions[-1] == "escalate_memory_update_review"

    assert blocked.update_priority_status == "blocked"
    assert blocked.memory_update_actions[0] == "escalate_blocked_memory_update"
    assert "feedback_route_status_blocked" in blocked.reason_codes
    assert "postmortem_blocked" in blocked.reason_codes


def test_payload_uses_decimal_strings_reason_lists_and_no_floats() -> None:
    module = api()
    decision = evaluate(
        feedback_route_status="queued",
        forecast_error_bps=d("260.000000"),
        source_gap_count=d("1.000000"),
        postmortem_status="pending",
        days_since_last_update=d("20.000000"),
        sample_size=d("10.000000"),
    )

    payload = module.strategy_team_memory_update_priority_v10_payload(decision)
    encoded = json.dumps(payload, sort_keys=True)

    assert decision.payload == payload
    assert payload["config_version"] == "strategy-team-memory-update-priority-v10"
    assert payload["team_id"] == "team-memory-alpha"
    assert payload["category"] == "macro"
    assert payload["feedback_route_status"] == "queued"
    assert payload["forecast_error_bps"] == "260.000000"
    assert payload["source_gap_count"] == "1.000000"
    assert payload["postmortem_status"] == "pending"
    assert payload["days_since_last_update"] == "20.000000"
    assert payload["sample_size"] == "10.000000"
    assert payload["update_priority_status"] == "queue_update"
    assert payload["priority_score"] == "49.000000"
    assert payload["memory_update_actions"] == [
        "apply_forecast_calibration_update",
        "refresh_source_gap_playbook",
        "complete_postmortem_memory_update",
        "refresh_stale_team_memory",
    ]
    assert payload["reason_codes"] == [
        "feedback_route_status_queued",
        "forecast_error_moderate",
        "source_gap_present",
        "postmortem_pending",
        "memory_update_stale",
        "sample_size_sufficient",
        "update_priority_status_queue_update",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"49.000000"' in encoded
    assert_no_float_values(payload)


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    numeric_fields = {
        "forecast_error_bps",
        "source_gap_count",
        "days_since_last_update",
        "sample_size",
        "priority_score",
    }

    for cls in (
        module.StrategyTeamMemoryUpdatePriorityV10Input,
        module.StrategyTeamMemoryUpdatePriorityV10Result,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal


def test_validation_rejects_bad_types_ranges_precision_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_id"):
        priority_input(team_id=_StringSubclass("team-memory-alpha"))

    with pytest.raises(ValueError, match="forecast_error_bps must be a Decimal"):
        priority_input(forecast_error_bps=40)

    with pytest.raises(ValueError, match="source_gap_count must be a Decimal"):
        priority_input(source_gap_count=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="feedback_route_status must be a known value"):
        priority_input(feedback_route_status="unknown")

    with pytest.raises(ValueError, match="postmortem_status must be a known value"):
        priority_input(postmortem_status="unknown")

    with pytest.raises(ValueError, match="forecast_error_bps must be nonnegative"):
        priority_input(forecast_error_bps=d("-0.000001"))

    with pytest.raises(ValueError, match="source_gap_count must be a nonnegative whole Decimal"):
        priority_input(source_gap_count=d("1.500000"))

    with pytest.raises(ValueError, match="days_since_last_update must be nonnegative"):
        priority_input(days_since_last_update=d("-0.000001"))

    with pytest.raises(ValueError, match="sample_size must be positive"):
        priority_input(sample_size=d("0.000000"))

    with pytest.raises(ValueError, match="forecast_error_bps must be finite"):
        priority_input(forecast_error_bps=Decimal("NaN"))

    with pytest.raises(ValueError, match="sample_size must use the required decimal precision"):
        priority_input(sample_size=d("20.0000001"))

    with pytest.raises(ValueError, match="memory_update_actions must be unique"):
        replace(
            evaluate(),
            memory_update_actions=("continue_monitoring", "continue_monitoring"),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(priority_input(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(evaluate(), readonly=False)

    with pytest.raises(FrozenInstanceError):
        decision = evaluate()
        decision.update_priority_status = "urgent_update"  # type: ignore[misc]

    with pytest.raises(ValueError, match="decision must be a StrategyTeamMemoryUpdatePriorityV10Result"):
        module.strategy_team_memory_update_priority_v10_payload(priority_input())


def test_public_strings_reject_secret_like_values_before_payload_leakage() -> None:
    with pytest.raises(ValueError, match="must not contain sensitive material"):
        priority_input(team_id="api_key=secret")


def test_module_scope_is_paper_report_readonly_with_no_external_or_execution_surface() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "network",
        "database",
        "durable",
        "store",
        "open(",
        "requests",
        "http",
        "socket",
        "postgres",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "execute(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
