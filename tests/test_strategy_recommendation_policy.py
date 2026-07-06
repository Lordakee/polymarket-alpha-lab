from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_recommendation_policy import (
    StrategyRecommendationPolicyConfig,
    StrategyRecommendationPolicyInput,
    StrategyRecommendationPolicyLabel,
    label_strategy_recommendation,
    strategy_recommendation_policy_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_recommendation_policy.py"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyRecommendationPolicyConfig:
    values: dict[str, object] = {
        "config_version": "strategy-recommendation-policy-test-v0",
        "paper_trade_score": d("0.700000"),
        "watch_score": d("0.500000"),
        "research_score": d("0.250000"),
        "min_team_memory_confidence": d("0.650000"),
        "watch_team_memory_confidence": d("0.500000"),
        "min_source_quality": d("0.700000"),
        "watch_source_quality": d("0.550000"),
        "cost_guard_watch": d("0.200000"),
        "cost_guard_reject": d("0.350000"),
        "resolution_risk_watch": d("0.300000"),
        "resolution_risk_reject": d("0.550000"),
    }
    values.update(overrides)
    return StrategyRecommendationPolicyConfig(**values)


def policy_input(**overrides: object) -> StrategyRecommendationPolicyInput:
    values: dict[str, object] = {
        "recommendation_id": "candidate-alpha",
        "market_slug": "will-alpha-resolve",
        "decision_matrix_score": d("0.820000"),
        "team_memory_confidence": d("0.760000"),
        "source_quality": d("0.840000"),
        "cost_guard": d("0.080000"),
        "resolution_risk": d("0.120000"),
        "upstream_reason_codes": ("decision_matrix_candidate_ready",),
    }
    values.update(overrides)
    return StrategyRecommendationPolicyInput(**values)


def label(
    *,
    candidate: StrategyRecommendationPolicyInput | None = None,
    cfg: StrategyRecommendationPolicyConfig | None = None,
) -> StrategyRecommendationPolicyLabel:
    return label_strategy_recommendation(candidate or policy_input(), config=cfg or config())


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_policy_recommends_paper_trade_yes_for_positive_ready_candidate() -> None:
    result = label()

    assert is_dataclass(result)
    assert result.config_version == "strategy-recommendation-policy-test-v0"
    assert result.recommendation_id == "candidate-alpha"
    assert result.market_slug == "will-alpha-resolve"
    assert result.decision_matrix_score == d("0.820000")
    assert result.decision_score_magnitude == d("0.820000")
    assert result.recommended_side == "yes"
    assert result.recommended_action == "paper_trade_yes"
    assert result.reason_codes == (
        "cost_guard_passed",
        "decision_matrix_candidate_ready",
        "decision_matrix_positive_edge",
        "paper_trade_threshold_met",
        "resolution_risk_passed",
        "source_quality_passed",
        "team_memory_confidence_passed",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_policy_recommends_paper_trade_no_for_negative_ready_candidate() -> None:
    result = label(candidate=policy_input(decision_matrix_score=d("-0.750000")))

    assert result.decision_matrix_score == d("-0.750000")
    assert result.decision_score_magnitude == d("0.750000")
    assert result.recommended_side == "no"
    assert result.recommended_action == "paper_trade_no"
    assert result.reason_codes == (
        "cost_guard_passed",
        "decision_matrix_candidate_ready",
        "decision_matrix_negative_edge",
        "paper_trade_threshold_met",
        "resolution_risk_passed",
        "source_quality_passed",
        "team_memory_confidence_passed",
    )


def test_policy_researches_more_when_score_or_evidence_is_incomplete() -> None:
    weak_score = label(candidate=policy_input(decision_matrix_score=d("0.220000")))
    weak_memory = label(
        candidate=policy_input(
            decision_matrix_score=d("0.640000"),
            team_memory_confidence=d("0.420000"),
            source_quality=d("0.700000"),
        ),
    )
    weak_sources = label(
        candidate=policy_input(
            decision_matrix_score=d("-0.640000"),
            team_memory_confidence=d("0.650000"),
            source_quality=d("0.400000"),
        ),
    )

    assert weak_score.recommended_action == "research_more"
    assert weak_score.reason_codes == (
        "cost_guard_passed",
        "decision_matrix_candidate_ready",
        "decision_matrix_positive_edge",
        "decision_matrix_score_below_research_threshold",
        "resolution_risk_passed",
        "source_quality_passed",
        "team_memory_confidence_passed",
    )
    assert weak_memory.recommended_action == "research_more"
    assert "team_memory_confidence_below_watch_threshold" in weak_memory.reason_codes
    assert weak_sources.recommended_action == "research_more"
    assert weak_sources.recommended_side == "no"
    assert "source_quality_below_watch_threshold" in weak_sources.reason_codes


def test_policy_watches_borderline_candidates_without_trade_or_reject() -> None:
    result = label(
        candidate=policy_input(
            decision_matrix_score=d("0.620000"),
            team_memory_confidence=d("0.560000"),
            source_quality=d("0.620000"),
            cost_guard=d("0.220000"),
            resolution_risk=d("0.320000"),
        ),
    )

    assert result.recommended_action == "watch"
    assert result.recommended_side == "yes"
    assert result.reason_codes == (
        "cost_guard_watch",
        "decision_matrix_candidate_ready",
        "decision_matrix_positive_edge",
        "paper_trade_threshold_not_met",
        "resolution_risk_watch",
        "source_quality_watch",
        "team_memory_confidence_watch",
    )


def test_policy_rejects_cost_guard_and_resolution_risk_overrides() -> None:
    cost_reject = label(
        candidate=policy_input(
            decision_matrix_score=d("0.910000"),
            cost_guard=d("0.350000"),
            resolution_risk=d("0.100000"),
        ),
    )
    resolution_reject = label(
        candidate=policy_input(
            decision_matrix_score=d("-0.910000"),
            cost_guard=d("0.100000"),
            resolution_risk=d("0.550000"),
        ),
    )

    assert cost_reject.recommended_action == "reject"
    assert cost_reject.reason_codes == (
        "cost_guard_reject",
        "decision_matrix_candidate_ready",
        "decision_matrix_positive_edge",
        "resolution_risk_passed",
        "source_quality_passed",
        "team_memory_confidence_passed",
    )
    assert resolution_reject.recommended_action == "reject"
    assert resolution_reject.recommended_side == "no"
    assert resolution_reject.reason_codes == (
        "cost_guard_passed",
        "decision_matrix_candidate_ready",
        "decision_matrix_negative_edge",
        "resolution_risk_reject",
        "source_quality_passed",
        "team_memory_confidence_passed",
    )


def test_outputs_are_decimal_only_frozen_tuple_only_and_payload_safe() -> None:
    result = label()

    for item in fields(result):
        item_value = getattr(result, item.name)
        if item.name in {
            "config_version",
            "recommendation_id",
            "market_slug",
            "recommended_action",
            "recommended_side",
            "reason_codes",
            "upstream_reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        }:
            continue
        assert type(item_value) is Decimal

    assert type(result.reason_codes) is tuple
    assert type(result.upstream_reason_codes) is tuple
    with pytest.raises(FrozenInstanceError):
        result.recommended_action = "reject"  # type: ignore[misc]

    with pytest.raises(ValueError, match="decision_matrix_score must be a Decimal"):
        policy_input(decision_matrix_score=0.5)
    with pytest.raises(ValueError, match="team_memory_confidence must be a Decimal"):
        policy_input(team_memory_confidence=_DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="upstream_reason_codes must be a tuple"):
        policy_input(upstream_reason_codes=["decision_matrix_candidate_ready"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(result, paper_only=False)
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(result, reason_codes=["paper_trade_threshold_met"])

    payload = strategy_recommendation_policy_payload(result)
    assert payload["decision_matrix_score"] == "0.820000"
    assert payload["decision_score_magnitude"] == "0.820000"
    assert payload["recommended_action"] == "paper_trade_yes"
    assert payload["recommended_side"] == "yes"
    assert payload["reason_codes"] == [
        "cost_guard_passed",
        "decision_matrix_candidate_ready",
        "decision_matrix_positive_edge",
        "paper_trade_threshold_met",
        "resolution_risk_passed",
        "source_quality_passed",
        "team_memory_confidence_passed",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="label must be a StrategyRecommendationPolicyLabel"):
        strategy_recommendation_policy_payload(object())


def test_config_thresholds_and_policy_input_validate_ranges_and_ordering() -> None:
    with pytest.raises(ValueError, match="watch_score must not exceed paper_trade_score"):
        config(watch_score=d("0.800000"), paper_trade_score=d("0.700000"))
    with pytest.raises(ValueError, match="research_score must not exceed watch_score"):
        config(research_score=d("0.600000"), watch_score=d("0.500000"))
    with pytest.raises(ValueError, match="watch_team_memory_confidence must not exceed"):
        config(watch_team_memory_confidence=d("0.700000"), min_team_memory_confidence=d("0.650000"))
    with pytest.raises(ValueError, match="source_quality must be a probability"):
        policy_input(source_quality=d("1.000001"))
    with pytest.raises(ValueError, match="resolution_risk must be nonnegative"):
        policy_input(resolution_risk=d("-0.000001"))
    with pytest.raises(ValueError, match="recommendation_id must be a canonical string"):
        policy_input(recommendation_id=" candidate-alpha")
    with pytest.raises(ValueError, match="config must be a StrategyRecommendationPolicyConfig"):
        label_strategy_recommendation(policy_input(), config=object())  # type: ignore[arg-type]


def test_module_scope_has_no_cli_db_network_or_live_trading_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "cli",
        "db",
        "http",
        "network",
        "order",
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
        "send",
        "trade",
        "order",
    }

    imports: list[str] = []
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.append(func.id)
            elif isinstance(func, ast.Attribute):
                calls.append(func.attr)

    lowered_imports = tuple(item.lower() for item in imports)
    assert not any(
        fragment in imported
        for imported in lowered_imports
        for fragment in forbidden_import_fragments
    )
    assert not (set(calls) & forbidden_call_names)
