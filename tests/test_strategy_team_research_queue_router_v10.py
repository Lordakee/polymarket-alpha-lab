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
    / "strategy_team_research_queue_router_v10.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_research_queue_router_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(**overrides: object):
    module = api()
    values = {
        "category": "crypto",
        "subcategory": "bridge_risk",
        "edge_tier": "medium",
        "freshness_status": "fresh",
        "team_capacity": d("0.800000"),
        "team_trust_score": d("0.850000"),
        "resolution_urgency": d("0.300000"),
        "human_review_required": False,
    }
    values.update(overrides)
    return module.StrategyTeamResearchQueueRouterV10Candidate(**values)


def route(candidate_value=None):
    module = api()
    return module.route_strategy_team_research_queue_router_v10(
        candidate_value if candidate_value is not None else candidate(),
    )


def assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_float_or_int(item)


def test_blocked_freshness_routes_to_refresh_lane_with_hard_sla() -> None:
    result = route(
        candidate(
            edge_tier="high",
            freshness_status="blocked",
            team_capacity=d("0.900000"),
            team_trust_score=d("0.800000"),
            resolution_urgency=d("0.700000"),
        ),
    )

    assert is_dataclass(result)
    assert result.queue_lane == "blocked_refresh"
    assert result.assigned_priority == d("100.000000")
    assert result.sla_minutes == d("30")
    assert result.reason_codes == (
        "edge_tier_high",
        "freshness_blocked",
        "assigned_priority_clamped",
        "queue_lane_blocked_refresh",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_human_review_and_low_trust_route_to_review_lane() -> None:
    result = route(
        candidate(
            category="politics",
            subcategory="ballot_count",
            edge_tier="medium",
            freshness_status="fresh",
            team_capacity=d("0.700000"),
            team_trust_score=d("0.450000"),
            resolution_urgency=d("0.300000"),
            human_review_required=True,
        ),
    )

    assert result.queue_lane == "human_review"
    assert result.assigned_priority == d("66.750000")
    assert result.sla_minutes == d("60")
    assert result.reason_codes == (
        "edge_tier_medium",
        "freshness_fresh",
        "human_review_required",
        "team_trust_low",
        "queue_lane_human_review",
    )


def test_low_signal_candidate_routes_to_backlog_with_payload_decimal_strings() -> None:
    result = route(
        candidate(
            edge_tier="low",
            freshness_status="fresh",
            team_capacity=d("1.000000"),
            team_trust_score=d("1.000000"),
            resolution_urgency=d("0.000000"),
        ),
    )

    assert result.queue_lane == "long_term_backlog"
    assert result.assigned_priority == d("10.000000")
    assert result.sla_minutes == d("1440")
    assert result.reason_codes == (
        "edge_tier_low",
        "freshness_fresh",
        "queue_lane_long_term_backlog",
    )

    payload = result.payload
    assert payload["category"] == "crypto"
    assert payload["subcategory"] == "bridge_risk"
    assert payload["team_capacity"] == "1.000000"
    assert payload["team_trust_score"] == "1.000000"
    assert payload["resolution_urgency"] == "0.000000"
    assert payload["assigned_priority"] == "10.000000"
    assert payload["sla_minutes"] == "1440"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_float_or_int(payload)


def test_urgent_critical_candidate_routes_to_expedited_research() -> None:
    result = route(
        candidate(
            edge_tier="critical",
            freshness_status="aging",
            team_capacity=d("0.600000"),
            team_trust_score=d("0.650000"),
            resolution_urgency=d("0.900000"),
        ),
    )

    assert result.queue_lane == "expedited_research"
    assert result.assigned_priority == d("100.000000")
    assert result.sla_minutes == d("120")
    assert result.reason_codes == (
        "edge_tier_critical",
        "freshness_aging",
        "resolution_urgency_high",
        "assigned_priority_clamped",
        "queue_lane_expedited_research",
    )


def test_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    module = api()
    result = route()

    for klass in (
        module.StrategyTeamResearchQueueRouterV10Candidate,
        module.StrategyTeamResearchQueueRouterV10Decision,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        result.queue_lane = "human_review"  # type: ignore[misc]

    decimal_fields = {
        "team_capacity",
        "team_trust_score",
        "resolution_urgency",
        "assigned_priority",
        "sla_minutes",
    }
    for field in fields(result):
        if field.name in decimal_fields:
            assert type(getattr(result, field.name)) is Decimal

    with pytest.raises(ValueError, match="team_capacity"):
        candidate(team_capacity=1)
    with pytest.raises(ValueError, match="team_trust_score"):
        candidate(team_trust_score=0.5)
    with pytest.raises(ValueError, match="resolution_urgency"):
        candidate(resolution_urgency=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="human_review_required"):
        candidate(human_review_required=1)
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)


def test_validation_rejects_unknown_inputs_and_tampered_outputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="candidate"):
        module.route_strategy_team_research_queue_router_v10(object())
    with pytest.raises(ValueError, match="edge_tier"):
        candidate(edge_tier="moonshot")
    with pytest.raises(ValueError, match="freshness_status"):
        candidate(freshness_status="unknown")
    with pytest.raises(ValueError, match="category"):
        candidate(category=" crypto")
    with pytest.raises(ValueError, match="team_capacity"):
        candidate(team_capacity=d("-0.000001"))
    with pytest.raises(ValueError, match="team_trust_score"):
        candidate(team_trust_score=d("1.000001"))

    result = route()
    with pytest.raises(ValueError, match="queue_lane"):
        replace(result, queue_lane="human_review")
    with pytest.raises(ValueError, match="assigned_priority"):
        replace(result, assigned_priority=d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("queue_lane_long_term_backlog",))
    with pytest.raises(ValueError, match="decision"):
        module.strategy_team_research_queue_router_v10_payload(object())


def test_module_scope_is_readonly_report_only_and_external_io_free() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    lowered_source = source.lower()
    forbidden_literals = (
        "wallet",
        "private_key",
        "authentication",
        "credential",
        "submit_order",
        "cancel_order",
        "place_order",
        "execute_trade",
    )
    assert not any(token in lowered_source for token in forbidden_literals)

    result = route()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
