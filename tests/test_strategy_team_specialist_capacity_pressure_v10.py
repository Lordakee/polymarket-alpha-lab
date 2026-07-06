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
    / "strategy_team_specialist_capacity_pressure_v10.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_specialist_capacity_pressure_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def capacity_input(**overrides: object):
    module = api()
    values = {
        "team_id": "team-resolution",
        "category": "market-review",
        "open_ticket_count": d("2.000000"),
        "urgent_ticket_count": d("0.000000"),
        "capacity_minutes": d("480.000000"),
        "committed_minutes": d("240.000000"),
        "average_ticket_age_minutes": d("15.000000"),
        "trust_score": d("0.900000"),
    }
    values.update(overrides)
    return module.TeamSpecialistCapacityPressureV10Input(**values)


def evaluate(**overrides: object):
    module = api()
    return module.evaluate_team_specialist_capacity_pressure_v10(
        capacity_input(**overrides),
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


def test_critical_capacity_deficit_escalates_specialist_triage() -> None:
    decision = evaluate(
        open_ticket_count=d("12.000000"),
        urgent_ticket_count=d("4.000000"),
        capacity_minutes=d("480.000000"),
        committed_minutes=d("620.000000"),
        average_ticket_age_minutes=d("180.000000"),
        trust_score=d("0.450000"),
    )

    assert is_dataclass(decision)
    assert decision.team_id == "team-resolution"
    assert decision.category == "market-review"
    assert decision.open_ticket_count == d("12.000000")
    assert decision.urgent_ticket_count == d("4.000000")
    assert decision.capacity_minutes == d("480.000000")
    assert decision.committed_minutes == d("620.000000")
    assert decision.average_ticket_age_minutes == d("180.000000")
    assert decision.trust_score == d("0.450000")
    assert decision.available_capacity_minutes == d("-140.000000")
    assert decision.pressure_status == "critical"
    assert decision.triage_action == "pause_new_intake_and_escalate_specialist"
    assert decision.reason_codes == (
        "capacity_deficit_critical",
        "urgent_ticket_pressure_high",
        "backlog_pressure_high",
        "ticket_age_stale",
        "trust_score_low",
    )
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True


def test_normal_capacity_keeps_monitoring_with_positive_capacity() -> None:
    decision = evaluate()

    assert decision.available_capacity_minutes == d("240.000000")
    assert decision.pressure_status == "normal"
    assert decision.triage_action == "continue_monitoring"
    assert decision.reason_codes == ("capacity_within_plan",)


def test_strained_and_pressured_statuses_select_triage_actions() -> None:
    strained = evaluate(
        open_ticket_count=d("4.000000"),
        urgent_ticket_count=d("1.000000"),
        committed_minutes=d("390.000000"),
        average_ticket_age_minutes=d("40.000000"),
        trust_score=d("0.850000"),
    )
    pressured = evaluate(
        open_ticket_count=d("8.000000"),
        urgent_ticket_count=d("2.000000"),
        committed_minutes=d("450.000000"),
        average_ticket_age_minutes=d("130.000000"),
        trust_score=d("0.600000"),
    )

    assert strained.available_capacity_minutes == d("90.000000")
    assert strained.pressure_status == "strained"
    assert strained.triage_action == "prioritize_aging_tickets"
    assert strained.reason_codes == (
        "capacity_buffer_thin",
        "urgent_ticket_present",
    )

    assert pressured.available_capacity_minutes == d("30.000000")
    assert pressured.pressure_status == "pressured"
    assert pressured.triage_action == "rebalance_queue_and_prioritize_urgent"
    assert pressured.reason_codes == (
        "capacity_buffer_low",
        "urgent_ticket_pressure_elevated",
        "ticket_age_stale",
        "trust_score_watch",
    )


def test_payload_uses_decimal_strings_reason_lists_and_no_floats() -> None:
    module = api()
    decision = evaluate(
        team_id="team-specialist-alpha",
        category="liquidity-risk",
        open_ticket_count=d("8.000000"),
        urgent_ticket_count=d("2.000000"),
        committed_minutes=d("450.000000"),
        average_ticket_age_minutes=d("130.000000"),
        trust_score=d("0.600000"),
    )

    payload = module.team_specialist_capacity_pressure_v10_payload(decision)
    encoded = json.dumps(payload, sort_keys=True)

    assert decision.payload == payload
    assert payload["team_id"] == "team-specialist-alpha"
    assert payload["category"] == "liquidity-risk"
    assert payload["open_ticket_count"] == "8.000000"
    assert payload["urgent_ticket_count"] == "2.000000"
    assert payload["capacity_minutes"] == "480.000000"
    assert payload["committed_minutes"] == "450.000000"
    assert payload["average_ticket_age_minutes"] == "130.000000"
    assert payload["trust_score"] == "0.600000"
    assert payload["available_capacity_minutes"] == "30.000000"
    assert payload["pressure_status"] == "pressured"
    assert payload["triage_action"] == "rebalance_queue_and_prioritize_urgent"
    assert payload["reason_codes"] == [
        "capacity_buffer_low",
        "urgent_ticket_pressure_elevated",
        "ticket_age_stale",
        "trust_score_watch",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"30.000000"' in encoded
    assert_no_float_values(payload)


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    numeric_fields = {
        "open_ticket_count",
        "urgent_ticket_count",
        "capacity_minutes",
        "committed_minutes",
        "average_ticket_age_minutes",
        "trust_score",
        "available_capacity_minutes",
    }

    for cls in (
        module.TeamSpecialistCapacityPressureV10Input,
        module.TeamSpecialistCapacityPressureV10Result,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal


def test_validation_rejects_bad_types_ranges_precision_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_id"):
        capacity_input(team_id=_StringSubclass("team-resolution"))

    with pytest.raises(ValueError, match="capacity_minutes must be a Decimal"):
        capacity_input(capacity_minutes=480)

    with pytest.raises(ValueError, match="open_ticket_count must be a Decimal"):
        capacity_input(open_ticket_count=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="capacity_minutes must be positive"):
        capacity_input(capacity_minutes=d("0.000000"))

    with pytest.raises(ValueError, match="urgent_ticket_count must not exceed open_ticket_count"):
        capacity_input(
            open_ticket_count=d("1.000000"),
            urgent_ticket_count=d("2.000000"),
        )

    with pytest.raises(ValueError, match="committed_minutes must be nonnegative"):
        capacity_input(committed_minutes=d("-0.000001"))

    with pytest.raises(ValueError, match="trust_score must be between 0 and 1"):
        capacity_input(trust_score=d("1.000001"))

    with pytest.raises(ValueError, match="average_ticket_age_minutes must be finite"):
        capacity_input(average_ticket_age_minutes=Decimal("NaN"))

    with pytest.raises(ValueError, match="committed_minutes must use the required decimal precision"):
        capacity_input(committed_minutes=d("1.0000001"))

    with pytest.raises(ValueError, match="reason_codes must be unique"):
        module.TeamSpecialistCapacityPressureV10Result(
            team_id="team-resolution",
            category="market-review",
            open_ticket_count=d("4.000000"),
            urgent_ticket_count=d("1.000000"),
            capacity_minutes=d("480.000000"),
            committed_minutes=d("390.000000"),
            average_ticket_age_minutes=d("40.000000"),
            trust_score=d("0.850000"),
            available_capacity_minutes=d("90.000000"),
            pressure_status="strained",
            triage_action="prioritize_aging_tickets",
            reason_codes=("capacity_buffer_thin", "capacity_buffer_thin"),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(capacity_input(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(evaluate(), readonly=False)

    with pytest.raises(FrozenInstanceError):
        decision = evaluate()
        decision.pressure_status = "pressured"  # type: ignore[misc]


def test_public_strings_reject_secret_like_values_before_payload_leakage() -> None:
    with pytest.raises(ValueError, match="must not contain sensitive material"):
        capacity_input(team_id="postgresql://user:secret@example.invalid/team")


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
