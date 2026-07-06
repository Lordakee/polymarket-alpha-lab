from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_evidence_gap_closure_plan_v4",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def gap(
    gap_id: str,
    gap_type: str,
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    market_slug: str = "btc-july-close-above-100k",
    source_id: str | None = "src-official",
    memory_item_id: str | None = "memory-alpha",
    severity_score: Decimal = Decimal("0.500000"),
):
    module = api()
    return module.StrategyEvidenceGapV4Input(
        gap_id=gap_id,
        team_id=team_id,
        category_id=category_id,
        market_slug=market_slug,
        gap_type=gap_type,
        source_id=source_id,
        memory_item_id=memory_item_id,
        severity_score=severity_score,
        reason_codes=("strategy_evidence_gap_closure_plan_v4_input",),
    )


def plan(*rows, cfg=None):
    module = api()
    return module.build_strategy_evidence_gap_closure_plan_v4(
        rows,
        config=cfg or module.StrategyEvidenceGapClosurePlanV4Config(),
    )


def test_gap_types_are_converted_to_ordered_research_actions() -> None:
    closure_plan = plan(
        gap(
            "gap-memory",
            "weak_team_memory",
            source_id=None,
            memory_item_id="memory-old",
            severity_score=d("0.600000"),
        ),
        gap(
            "gap-primary",
            "missing_primary_source",
            source_id=None,
            severity_score=d("0.900000"),
        ),
        gap(
            "gap-stale",
            "stale_evidence",
            source_id="source-stale",
            severity_score=d("0.800000"),
        ),
        gap(
            "gap-conflict",
            "conflicting_sources",
            source_id="source-conflict",
            severity_score=d("0.700000"),
        ),
        gap(
            "gap-resolution",
            "unclear_resolution",
            source_id="source-resolution",
            severity_score=d("0.700000"),
        ),
    )

    assert is_dataclass(closure_plan)
    assert closure_plan.plan_version == "strategy-evidence-gap-closure-plan-v4"
    assert closure_plan.action_count == d("5")
    assert closure_plan.blocking_action_count == d("4")
    assert closure_plan.watch_action_count == d("1")
    assert closure_plan.owner_team_count == d("1")
    assert closure_plan.reason_codes == (
        "strategy_evidence_gap_closure_plan_v4_missing_primary_source",
        "strategy_evidence_gap_closure_plan_v4_stale_evidence",
        "strategy_evidence_gap_closure_plan_v4_conflicting_sources",
        "strategy_evidence_gap_closure_plan_v4_unclear_resolution",
        "strategy_evidence_gap_closure_plan_v4_weak_team_memory",
    )
    assert closure_plan.paper_only is True
    assert closure_plan.report_only is True
    assert closure_plan.readonly is True

    actions = closure_plan.actions
    assert tuple(action.gap_id for action in actions) == (
        "gap-primary",
        "gap-stale",
        "gap-conflict",
        "gap-resolution",
        "gap-memory",
    )
    assert tuple(action.next_research_action for action in actions) == (
        "collect_primary_resolution_source",
        "refresh_stale_evidence",
        "reconcile_conflicting_sources",
        "clarify_resolution_rule",
        "rebuild_team_memory_support",
    )
    assert tuple(action.owner_team for action in actions) == (
        "crypto_btc",
        "crypto_btc",
        "crypto_btc",
        "crypto_btc",
        "crypto_btc",
    )
    assert tuple(action.deadline_minutes for action in actions) == (
        d("30"),
        d("45"),
        d("60"),
        d("90"),
        d("120"),
    )
    assert tuple(action.action_status for action in actions) == (
        "blocking",
        "watch",
        "blocking",
        "blocking",
        "blocking",
    )
    assert actions[0].reason_codes == (
        "strategy_evidence_gap_closure_plan_v4_missing_primary_source",
    )


def test_actions_sort_by_priority_severity_deadline_and_gap_id() -> None:
    closure_plan = plan(
        gap("gap-z", "weak_team_memory", severity_score=d("0.900000")),
        gap("gap-b", "missing_primary_source", severity_score=d("0.100000")),
        gap("gap-a", "missing_primary_source", severity_score=d("0.900000")),
        gap("gap-c", "stale_evidence", severity_score=d("0.900000")),
    )

    assert tuple(action.gap_id for action in closure_plan.actions) == (
        "gap-a",
        "gap-b",
        "gap-c",
        "gap-z",
    )
    assert tuple(action.priority_rank for action in closure_plan.actions) == (
        d("1"),
        d("2"),
        d("3"),
        d("4"),
    )


def test_empty_inputs_return_readonly_report_with_no_actions() -> None:
    closure_plan = plan()

    assert closure_plan.action_count == d("0")
    assert closure_plan.blocking_action_count == d("0")
    assert closure_plan.watch_action_count == d("0")
    assert closure_plan.owner_team_count == d("0")
    assert closure_plan.actions == ()
    assert closure_plan.reason_codes == (
        "strategy_evidence_gap_closure_plan_v4_no_gaps",
    )


def test_payload_helper_uses_decimal_strings_and_no_floats() -> None:
    payload = api().strategy_evidence_gap_closure_plan_v4_payload(
        plan(gap("gap-primary", "missing_primary_source", source_id=None)),
    )

    assert payload["action_count"] == "1"
    assert payload["actions"][0]["deadline_minutes"] == "30"
    assert payload["actions"][0]["severity_score"] == "0.500000"
    assert all(not isinstance(value, float) for value in _walk_values(payload))


def test_validation_rejects_invalid_inputs_and_inconsistent_reports() -> None:
    module = api()

    with pytest.raises(ValueError, match="gap_type"):
        gap("gap-bad", "needs_web_search")
    with pytest.raises(ValueError, match="team_id"):
        gap("gap-bad", "missing_primary_source", team_id="unknown")
    with pytest.raises(ValueError, match="category_id"):
        gap("gap-bad", "missing_primary_source", category_id="politics")
    with pytest.raises(ValueError, match="severity_score"):
        gap("gap-bad", "missing_primary_source", severity_score=d("1.000001"))
    with pytest.raises(ValueError, match="reason_codes"):
        module.StrategyEvidenceGapV4Input(
            gap_id="gap-bad",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            market_slug="btc-july-close-above-100k",
            gap_type="missing_primary_source",
            source_id=None,
            memory_item_id=None,
            severity_score=d("0.500000"),
            reason_codes=("wrong",),
        )
    with pytest.raises(ValueError, match="duplicate"):
        plan(
            gap("gap-primary", "missing_primary_source"),
            gap("gap-primary", "stale_evidence"),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_evidence_gap_closure_plan_v4((), config=object())

    closure_plan = plan(gap("gap-primary", "missing_primary_source"))
    with pytest.raises(ValueError, match="action_count"):
        replace(closure_plan, action_count=d("2"))


def test_hard_flags_public_dataclasses_are_frozen_and_decimal_only() -> None:
    row = gap("gap-primary", "missing_primary_source", source_id=None)
    closure_plan = plan(row)

    with pytest.raises(FrozenInstanceError):
        row.gap_type = "stale_evidence"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        closure_plan.actions[0].deadline_minutes = d("99")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        closure_plan.action_count = d("9")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="deadline_minutes"):
        replace(closure_plan.actions[0], deadline_minutes=30)


def test_static_module_has_no_forbidden_surfaces_or_float_literals() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_evidence_gap_closure_plan_v4.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "network",
        "live trading",
        "private_key",
        "api_key",
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
