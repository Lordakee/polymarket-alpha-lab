from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_market_research_budget_guard_v10.py"
)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_market_research_budget_guard_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def guard_input(**overrides: object):
    module = api()
    values = {
        "market_id": "market_alpha",
        "priority_score": d("0.820000"),
        "estimated_research_minutes": d("45.000000"),
        "team_capacity_score": d("0.780000"),
        "time_to_resolution_minutes": d("1440.000000"),
        "expected_value_bps": d("75.000000"),
        "source_gap_count": d("1.000000"),
        "human_review_required": False,
    }
    values.update(overrides)
    return module.StrategyMarketResearchBudgetGuardV10Input(**values)


def evaluate(**overrides: object):
    module = api()
    return module.evaluate_strategy_market_research_budget_guard_v10(
        guard_input(**overrides),
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


def test_budget_guard_approves_full_research_minutes_and_payload() -> None:
    module = api()

    decision = evaluate()
    payload = module.strategy_market_research_budget_guard_v10_payload(decision)

    assert is_dataclass(decision)
    assert decision.market_id == "market_alpha"
    assert decision.priority_score == d("0.820000")
    assert decision.estimated_research_minutes == d("45.000000")
    assert decision.approved_minutes == d("45.000000")
    assert decision.budget_status == "approved"
    assert decision.budget_warning_level == "none"
    assert decision.reason_codes == (
        "market_research_budget_approved",
        "priority_score_high",
        "team_capacity_available",
        "resolution_window_sufficient",
        "expected_value_supports_budget",
        "source_gap_count_low",
    )
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True
    assert decision.payload == payload
    assert payload == {
        "market_id": "market_alpha",
        "priority_score": "0.820000",
        "estimated_research_minutes": "45.000000",
        "team_capacity_score": "0.780000",
        "time_to_resolution_minutes": "1440.000000",
        "expected_value_bps": "75.000000",
        "source_gap_count": "1.000000",
        "human_review_required": False,
        "budget_status": "approved",
        "approved_minutes": "45.000000",
        "budget_warning_level": "none",
        "reason_codes": [
            "market_research_budget_approved",
            "priority_score_high",
            "team_capacity_available",
            "resolution_window_sufficient",
            "expected_value_supports_budget",
            "source_gap_count_low",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_no_float_values(payload)


def test_budget_guard_limits_minutes_when_capacity_window_or_value_are_tight() -> None:
    decision = evaluate(
        priority_score=d("0.650000"),
        estimated_research_minutes=d("90.000000"),
        team_capacity_score=d("0.420000"),
        time_to_resolution_minutes=d("180.000000"),
        expected_value_bps=d("20.000000"),
        source_gap_count=d("3.000000"),
    )

    assert decision.approved_minutes == d("30.000000")
    assert decision.budget_status == "limited"
    assert decision.budget_warning_level == "medium"
    assert decision.reason_codes == (
        "market_research_budget_limited",
        "priority_score_standard",
        "team_capacity_constrained",
        "resolution_window_tight",
        "expected_value_watch",
        "source_gap_count_moderate",
    )


def test_budget_guard_blocks_autonomous_budget_on_hard_risk_conditions() -> None:
    decision = evaluate(
        priority_score=d("0.100000"),
        estimated_research_minutes=d("60.000000"),
        team_capacity_score=d("0.100000"),
        time_to_resolution_minutes=d("10.000000"),
        expected_value_bps=d("0.000000"),
        source_gap_count=d("5.000000"),
        human_review_required=True,
    )

    assert decision.approved_minutes == ZERO
    assert decision.budget_status == "blocked"
    assert decision.budget_warning_level == "high"
    assert decision.reason_codes == (
        "market_research_budget_blocked",
        "priority_score_below_floor",
        "team_capacity_below_floor",
        "resolution_window_too_short",
        "expected_value_below_floor",
        "source_gap_count_high",
        "human_review_required",
    )


def test_budget_guard_validates_decimal_inputs_counts_flags_and_freezing() -> None:
    module = api()
    decision = evaluate()

    with pytest.raises(FrozenInstanceError):
        decision.budget_status = "limited"  # type: ignore[misc]

    with pytest.raises(ValueError, match="inputs must be"):
        module.evaluate_strategy_market_research_budget_guard_v10(object())

    with pytest.raises(ValueError, match="priority_score must be a Decimal"):
        guard_input(priority_score=0.82)

    with pytest.raises(ValueError, match="priority_score must be exactly Decimal"):
        guard_input(priority_score=DecimalSubclass("0.820000"))

    with pytest.raises(ValueError, match="team_capacity_score must be between zero and one"):
        guard_input(team_capacity_score=d("1.100000"))

    with pytest.raises(ValueError, match="estimated_research_minutes must be nonnegative"):
        guard_input(estimated_research_minutes=d("-1.000000"))

    with pytest.raises(ValueError, match="source_gap_count must be a whole Decimal"):
        guard_input(source_gap_count=d("1.500000"))

    with pytest.raises(ValueError, match="human_review_required must be a bool"):
        guard_input(human_review_required=1)

    with pytest.raises(ValueError, match="input paper_only must be True"):
        guard_input(paper_only=False)

    with pytest.raises(ValueError, match="decision readonly must be True"):
        replace(decision, readonly=False)

    with pytest.raises(ValueError, match="payload must match decision fields"):
        replace(decision, payload={})


def test_budget_guard_rejects_tampered_derived_decision_fields() -> None:
    decision = evaluate()

    with pytest.raises(ValueError, match="approved_minutes must match budget inputs"):
        replace(decision, approved_minutes=d("30.000000"))

    with pytest.raises(ValueError, match="budget_status must match budget inputs"):
        replace(decision, budget_status="limited")

    with pytest.raises(ValueError, match="budget_warning_level must match budget inputs"):
        replace(decision, budget_warning_level="medium")

    with pytest.raises(ValueError, match="reason_codes must match budget inputs"):
        replace(decision, reason_codes=("market_research_budget_approved",))


def test_budget_guard_payload_rejects_bad_type_float_flags_and_live_surface() -> None:
    module = api()
    decision = evaluate()

    with pytest.raises(ValueError, match="decision must be"):
        module.strategy_market_research_budget_guard_v10_payload(object())

    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.strategy_market_research_budget_guard_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.strategy_market_research_budget_guard_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "priority_score": 0.82,
            },
        )

    with pytest.raises(ValueError, match="unsafe live surface"):
        module.strategy_market_research_budget_guard_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet": "redacted",
            },
        )

    with pytest.raises(ValueError, match="payload paper_only must be True"):
        module.strategy_market_research_budget_guard_v10_payload(
            {"market_id": "market_alpha"},
        )

    with pytest.raises(ValueError, match="unsafe live surface"):
        module.strategy_market_research_budget_guard_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "reason_codes": ["market_research_budget_approved", "submit_order"],
            },
        )

    with pytest.raises(ValueError, match="JSON object keys must be strings"):
        module.strategy_market_research_budget_guard_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                1: "market_alpha",
            },
        )

    assert module.strategy_market_research_budget_guard_v10_payload(decision) == (
        decision.payload
    )


def test_budget_guard_decimal_fields_are_exact_decimal_instances() -> None:
    decision = evaluate()

    for item in fields(decision):
        if item.name in {
            "market_id",
            "human_review_required",
            "budget_status",
            "budget_warning_level",
            "reason_codes",
            "payload",
            "paper_only",
            "report_only",
            "readonly",
        }:
            continue
        assert type(getattr(decision, item.name)) is Decimal


def test_module_scope_stays_paper_report_readonly_without_io_or_live_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "http",
        "network",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "execute",
        "fetch",
        "network",
        "persist",
        "request",
        "sign",
        "submit",
        "wallet",
    )
    forbidden_attr_names = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert lowered not in forbidden_attr_names
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
