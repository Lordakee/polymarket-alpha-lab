from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import strategy_recommendation_decision_audit_bundle_v2 as audit_module
from polymarket_alpha_lab.strategy_recommendation_decision_audit_bundle_v2 import (
    StrategyRecommendationDecisionAuditBundleV2,
    StrategyRecommendationDecisionAuditBundleV2Input,
    build_strategy_recommendation_decision_audit_bundle_v2,
    strategy_recommendation_decision_audit_bundle_v2_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def recommendation_input(**overrides: object) -> StrategyRecommendationDecisionAuditBundleV2Input:
    values = {
        "candidate_id": "candidate-001",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "research_quality_score": d("0.860000"),
        "official_source_anchor_score": d("0.900000"),
        "information_freshness_score": d("0.820000"),
        "gross_edge": d("0.120000"),
        "fee_cost": d("0.010000"),
        "slippage_cost": d("0.008000"),
        "break_even_edge": d("0.018000"),
        "recommended_position_notional": d("125.000000"),
        "max_position_notional": d("150.000000"),
        "exit_liquidity_score": d("0.770000"),
        "resolution_risk_score": d("0.180000"),
        "specialist_quorum_score": d("0.800000"),
        "specialist_approval_count": 3,
        "specialist_required_count": 3,
        "portfolio_impact_score": d("0.220000"),
        "reason_codes": ("candidate_input_complete",),
    }
    values.update(overrides)
    return StrategyRecommendationDecisionAuditBundleV2Input(**values)


def report(
    **overrides: object,
) -> StrategyRecommendationDecisionAuditBundleV2:
    return build_strategy_recommendation_decision_audit_bundle_v2(
        recommendation_input(**overrides),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            for fragment in (
                "auth",
                "wallet",
                "order",
                "network",
                "database",
                "persist",
                "signing",
                "mutation",
                "buy",
                "sell",
                "trade",
            ):
                assert fragment not in lowered
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_builds_ready_audit_bundle_with_decimal_only_derived_posture() -> None:
    result = report()

    assert result.config_version == "strategy-recommendation-decision-audit-bundle-v2"
    assert result.candidate_id == "candidate-001"
    assert result.market_slug == "fed-cuts-by-september"
    assert result.outcome_name == "Yes"
    assert result.final_recommendation == "paper_enter"
    assert result.recommendation_posture == "ready"
    assert result.net_edge == d("0.102000")
    assert result.cost_break_even_margin == d("0.102000")
    assert result.position_sizing_score == d("0.833333")
    assert result.liquidity_exit_feasible is True
    assert result.specialist_quorum_met is True
    assert result.audit_score == d("0.742814")
    assert result.reason_codes == (
        "recommendation_posture_ready",
        "candidate_input_complete",
        "research_quality_ready",
        "official_source_anchor_ready",
        "information_freshness_ready",
        "cost_break_even_positive",
        "position_size_within_limit",
        "liquidity_exit_feasible",
        "resolution_risk_acceptable",
        "specialist_quorum_met",
        "portfolio_impact_acceptable",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_payload_serializes_decimals_as_strings_and_validates_digest() -> None:
    result = report()
    payload = strategy_recommendation_decision_audit_bundle_v2_payload(result)

    assert payload == {
        "config_version": "strategy-recommendation-decision-audit-bundle-v2",
        "candidate_id": "candidate-001",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "research_quality_score": "0.860000",
        "official_source_anchor_score": "0.900000",
        "information_freshness_score": "0.820000",
        "gross_edge": "0.120000",
        "fee_cost": "0.010000",
        "slippage_cost": "0.008000",
        "break_even_edge": "0.018000",
        "net_edge": "0.102000",
        "cost_break_even_margin": "0.102000",
        "recommended_position_notional": "125.000000",
        "max_position_notional": "150.000000",
        "position_sizing_score": "0.833333",
        "exit_liquidity_score": "0.770000",
        "liquidity_exit_feasible": True,
        "resolution_risk_score": "0.180000",
        "specialist_quorum_score": "0.800000",
        "specialist_approval_count": 3,
        "specialist_required_count": 3,
        "specialist_quorum_met": True,
        "portfolio_impact_score": "0.220000",
        "audit_score": "0.742814",
        "final_recommendation": "paper_enter",
        "recommendation_posture": "ready",
        "reason_codes": [
            "recommendation_posture_ready",
            "candidate_input_complete",
            "research_quality_ready",
            "official_source_anchor_ready",
            "information_freshness_ready",
            "cost_break_even_positive",
            "position_size_within_limit",
            "liquidity_exit_feasible",
            "resolution_risk_acceptable",
            "specialist_quorum_met",
            "portfolio_impact_acceptable",
        ],
        "derived_validation_digest": result.derived_validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(result, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["audit_score"] = "0.010000"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        audit_module.validate_strategy_recommendation_decision_audit_bundle_v2_public_payload(
            tampered_payload,
        )


def test_watch_and_blocked_postures_explain_primary_risk_drivers() -> None:
    watched = report(
        information_freshness_score=d("0.580000"),
        recommended_position_notional=d("175.000000"),
        exit_liquidity_score=d("0.590000"),
    )
    blocked = report(
        official_source_anchor_score=d("0.420000"),
        gross_edge=d("0.010000"),
        break_even_edge=d("0.018000"),
        resolution_risk_score=d("0.850000"),
        specialist_approval_count=1,
        portfolio_impact_score=d("0.810000"),
    )

    assert watched.final_recommendation == "paper_watch"
    assert watched.recommendation_posture == "watch"
    assert "information_freshness_watch" in watched.reason_codes
    assert "position_size_above_limit" in watched.reason_codes
    assert "liquidity_exit_watch" in watched.reason_codes

    assert blocked.final_recommendation == "paper_skip"
    assert blocked.recommendation_posture == "blocked"
    assert "official_source_anchor_blocked" in blocked.reason_codes
    assert "cost_break_even_negative" in blocked.reason_codes
    assert "resolution_risk_blocked" in blocked.reason_codes
    assert "specialist_quorum_missing" in blocked.reason_codes
    assert "portfolio_impact_blocked" in blocked.reason_codes


def test_inputs_and_outputs_are_frozen_decimal_only_and_internally_consistent() -> None:
    result = report()

    with pytest.raises(FrozenInstanceError):
        result.final_recommendation = "paper_skip"  # type: ignore[misc]
    with pytest.raises(ValueError, match="research_quality_score must be a Decimal"):
        recommendation_input(research_quality_score="0.86")
    with pytest.raises(ValueError, match="gross_edge must be a Decimal"):
        recommendation_input(gross_edge=0.12)
    with pytest.raises(ValueError, match="specialist_required_count must be positive"):
        recommendation_input(specialist_required_count=0)
    with pytest.raises(ValueError, match="specialist_approval_count cannot exceed"):
        recommendation_input(specialist_approval_count=4)
    with pytest.raises(ValueError, match="break_even_edge must match fee and slippage costs"):
        recommendation_input(break_even_edge=d("0.017000"))
    with pytest.raises(ValueError, match="net_edge must match gross_edge minus break_even_edge"):
        replace(result, net_edge=d("0.100000"))
    with pytest.raises(ValueError, match="reason_codes must include all derived reasons"):
        replace(result, reason_codes=("recommendation_posture_ready",))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(result, paper_only=False)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("candidate_id", "candidate-live-check"),
        ("market_slug", "wallet-pressure"),
        ("outcome_name", "Buy"),
        ("reason_codes", ("candidate_input_complete", "trade_signal")),
    ),
)
def test_rejects_unsafe_public_keys_and_values(field_name: str, bad_value: object) -> None:
    with pytest.raises(ValueError, match="unsafe public value"):
        recommendation_input(**{field_name: bad_value})

    payload = strategy_recommendation_decision_audit_bundle_v2_payload(report())
    payload["wallet_key"] = "public"
    with pytest.raises(ValueError, match="unsafe public key"):
        audit_module.validate_strategy_recommendation_decision_audit_bundle_v2_public_payload(
            payload,
        )


def test_payload_rejects_int_or_float_metric_values_and_wrong_payload_type() -> None:
    payload = strategy_recommendation_decision_audit_bundle_v2_payload(report())
    payload["audit_score"] = 1
    with pytest.raises(ValueError, match="must be serialized Decimal strings"):
        audit_module.validate_strategy_recommendation_decision_audit_bundle_v2_public_payload(
            payload,
        )

    payload = strategy_recommendation_decision_audit_bundle_v2_payload(report())
    payload["net_edge"] = 0.102
    with pytest.raises(ValueError, match="must be serialized Decimal strings"):
        audit_module.validate_strategy_recommendation_decision_audit_bundle_v2_public_payload(
            payload,
        )

    with pytest.raises(
        ValueError,
        match="bundle must be a StrategyRecommendationDecisionAuditBundleV2",
    ):
        strategy_recommendation_decision_audit_bundle_v2_payload(object())


def test_module_is_pure_readonly_report_only_and_has_no_live_surface() -> None:
    source = inspect.getsource(audit_module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "http",
        "io",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "open",
        "print",
        "input",
        "compile",
        "eval",
        "exec",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "trade",
    }
    forbidden_attr_fragments = (
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "network",
        "persist",
        "request",
        "secret",
        "sign",
        "submit",
        "trade",
        "wallet",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".", 1)[0] for alias in node.names}
            assert imported_roots.isdisjoint(forbidden_import_roots)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
