from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import strategy_decision_audit_packet as audit_module
from polymarket_alpha_lab.strategy_decision_audit_packet import (
    StrategyDecisionAuditCosts,
    StrategyDecisionAuditForecast,
    StrategyDecisionAuditMarketProbability,
    StrategyDecisionAuditRecommendation,
    StrategyDecisionAuditResolutionRisk,
    StrategyDecisionAuditSourceQuality,
    StrategyDecisionAuditTeamMemory,
    build_strategy_decision_audit_packet,
    strategy_decision_audit_packet_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def forecast(**overrides: object) -> StrategyDecisionAuditForecast:
    values = {
        "forecast_probability": d("0.6100004"),
        "forecast_confidence": d("0.820000"),
        "reason_codes": ("forecast_model_edge_positive",),
    }
    values.update(overrides)
    return StrategyDecisionAuditForecast(**values)


def market_probability(**overrides: object) -> StrategyDecisionAuditMarketProbability:
    values = {
        "candidate_id": "candidate-001",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "market_probability": d("0.540000"),
        "reason_codes": ("market_probability_snapshot_observed",),
    }
    values.update(overrides)
    return StrategyDecisionAuditMarketProbability(**values)


def costs(**overrides: object) -> StrategyDecisionAuditCosts:
    values = {
        "fee_cost": d("0.006000"),
        "slippage_cost": d("0.004000"),
        "liquidity_cost": d("0.002000"),
        "total_cost": d("0.012000"),
        "cost_adjusted_edge": d("0.058000"),
        "reason_codes": ("cost_adjusted_edge_positive",),
    }
    values.update(overrides)
    return StrategyDecisionAuditCosts(**values)


def source_quality(**overrides: object) -> StrategyDecisionAuditSourceQuality:
    values = {
        "source_quality_score": d("0.880000"),
        "source_count": 4,
        "reason_codes": ("source_quality_ready",),
    }
    values.update(overrides)
    return StrategyDecisionAuditSourceQuality(**values)


def team_memory(**overrides: object) -> StrategyDecisionAuditTeamMemory:
    values = {
        "team_id": "macro-rates",
        "team_memory_score": d("0.910000"),
        "reason_codes": ("team_memory_supportive",),
    }
    values.update(overrides)
    return StrategyDecisionAuditTeamMemory(**values)


def resolution_risk(**overrides: object) -> StrategyDecisionAuditResolutionRisk:
    values = {
        "resolution_risk_score": d("0.120000"),
        "reason_codes": ("resolution_risk_acceptable",),
    }
    values.update(overrides)
    return StrategyDecisionAuditResolutionRisk(**values)


def recommendation(**overrides: object) -> StrategyDecisionAuditRecommendation:
    values = {
        "recommendation": "enter",
        "reason_codes": ("recommendation_enter",),
    }
    values.update(overrides)
    return StrategyDecisionAuditRecommendation(**values)


def packet():
    return build_strategy_decision_audit_packet(
        forecast=forecast(),
        market_probability=market_probability(),
        costs=costs(),
        source_quality=source_quality(),
        team_memory=team_memory(),
        resolution_risk=resolution_risk(),
        recommendation=recommendation(),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert "secret" not in lowered
            assert "auth" not in lowered
            assert "order" not in lowered
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_builds_complete_audit_packet_from_typed_decision_inputs() -> None:
    result = packet()

    assert result.config_version == "strategy-decision-audit-packet-v0"
    assert result.candidate_id == "candidate-001"
    assert result.market_slug == "fed-cuts-by-september"
    assert result.outcome_name == "Yes"
    assert result.team_id == "macro-rates"
    assert result.packet_status == "ready"
    assert result.forecast.forecast_probability == d("0.610000")
    assert result.forecast_edge == d("0.070000")
    assert result.cost_adjusted_edge == d("0.058000")
    assert result.recommendation.recommendation == "enter"
    assert result.reason_codes == (
        "strategy_decision_audit_packet_ready",
        "forecast_model_edge_positive",
        "market_probability_snapshot_observed",
        "cost_adjusted_edge_positive",
        "source_quality_ready",
        "team_memory_supportive",
        "resolution_risk_acceptable",
        "recommendation_enter",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_payload_is_auditable_decimal_stringified_and_omits_live_keys() -> None:
    payload = strategy_decision_audit_packet_payload(packet())

    assert payload == {
        "config_version": "strategy-decision-audit-packet-v0",
        "candidate_id": "candidate-001",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "team_id": "macro-rates",
        "packet_status": "ready",
        "forecast_edge": "0.070000",
        "cost_adjusted_edge": "0.058000",
        "forecast": {
            "forecast_probability": "0.610000",
            "forecast_confidence": "0.820000",
            "reason_codes": ["forecast_model_edge_positive"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        "market_probability": {
            "candidate_id": "candidate-001",
            "market_slug": "fed-cuts-by-september",
            "outcome_name": "Yes",
            "market_probability": "0.540000",
            "reason_codes": ["market_probability_snapshot_observed"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        "costs": {
            "fee_cost": "0.006000",
            "slippage_cost": "0.004000",
            "liquidity_cost": "0.002000",
            "total_cost": "0.012000",
            "cost_adjusted_edge": "0.058000",
            "reason_codes": ["cost_adjusted_edge_positive"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        "source_quality": {
            "source_quality_score": "0.880000",
            "source_count": 4,
            "reason_codes": ["source_quality_ready"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        "team_memory": {
            "team_id": "macro-rates",
            "team_memory_score": "0.910000",
            "reason_codes": ["team_memory_supportive"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        "resolution_risk": {
            "resolution_risk_score": "0.120000",
            "reason_codes": ["resolution_risk_acceptable"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        "recommendation": {
            "recommendation": "enter",
            "reason_codes": ["recommendation_enter"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        "reason_codes": [
            "strategy_decision_audit_packet_ready",
            "forecast_model_edge_positive",
            "market_probability_snapshot_observed",
            "cost_adjusted_edge_positive",
            "source_quality_ready",
            "team_memory_supportive",
            "resolution_risk_acceptable",
            "recommendation_enter",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_no_float_values(payload)


def test_outputs_are_frozen_typed_and_reason_codes_must_remain_complete() -> None:
    result = packet()

    with pytest.raises(FrozenInstanceError):
        result.packet_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        replace(result.forecast, forecast_probability=0.61)
    with pytest.raises(ValueError, match="source_count must be a positive int"):
        source_quality(source_count=0)
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(result.costs, reason_codes=["cost_adjusted_edge_positive"])
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(result.recommendation, reason_codes=("recommendation_enter", "recommendation_enter"))
    with pytest.raises(ValueError, match="reason_codes must include all component reason codes"):
        replace(result, reason_codes=("strategy_decision_audit_packet_ready",))
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="payload must be a StrategyDecisionAuditPacket"):
        strategy_decision_audit_packet_payload(object())


def test_packet_status_reflects_recommendation_without_losing_component_reasons() -> None:
    watched = build_strategy_decision_audit_packet(
        forecast=forecast(reason_codes=("forecast_uncertainty_watch",)),
        market_probability=market_probability(reason_codes=("market_probability_snapshot_observed",)),
        costs=costs(reason_codes=("cost_adjusted_edge_positive",)),
        source_quality=source_quality(reason_codes=("source_quality_ready",)),
        team_memory=team_memory(reason_codes=("team_memory_supportive",)),
        resolution_risk=resolution_risk(reason_codes=("resolution_risk_watch",)),
        recommendation=recommendation(
            recommendation="watch",
            reason_codes=("recommendation_watch",),
        ),
    )
    blocked = build_strategy_decision_audit_packet(
        forecast=forecast(),
        market_probability=market_probability(),
        costs=costs(cost_adjusted_edge=d("-0.010000"), reason_codes=("cost_adjusted_edge_negative",)),
        source_quality=source_quality(),
        team_memory=team_memory(),
        resolution_risk=resolution_risk(
            resolution_risk_score=d("0.870000"),
            reason_codes=("resolution_risk_blocked",),
        ),
        recommendation=recommendation(
            recommendation="skip",
            reason_codes=("recommendation_skip",),
        ),
    )

    assert watched.packet_status == "watch"
    assert watched.reason_codes == (
        "strategy_decision_audit_packet_watch",
        "forecast_uncertainty_watch",
        "market_probability_snapshot_observed",
        "cost_adjusted_edge_positive",
        "source_quality_ready",
        "team_memory_supportive",
        "resolution_risk_watch",
        "recommendation_watch",
    )
    assert blocked.packet_status == "blocked"
    assert blocked.reason_codes == (
        "strategy_decision_audit_packet_blocked",
        "forecast_model_edge_positive",
        "market_probability_snapshot_observed",
        "cost_adjusted_edge_negative",
        "source_quality_ready",
        "team_memory_supportive",
        "resolution_risk_blocked",
        "recommendation_skip",
    )


def test_module_is_pure_and_has_no_secret_auth_or_live_action_surface() -> None:
    source = inspect.getsource(audit_module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "http",
        "io",
        "json",
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
