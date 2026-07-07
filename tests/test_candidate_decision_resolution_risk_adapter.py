from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "candidate_decision_resolution_risk_adapter.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.candidate_decision_resolution_risk_adapter",
    )


def decision_api():
    return importlib.import_module("polymarket_alpha_lab.candidate_decision_score")


def d(value: str) -> Decimal:
    return Decimal(value)


def facts(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-btc-resolution-001",
        "market_id": "market-btc-resolution-001",
        "normalized_market_question": "btc above threshold at close",
        "primary_team_id": "crypto_btc",
        "secondary_team_ids": ("macro_rates",),
        "selected_side": "yes",
        "forecast_probability": d("0.620000"),
        "executable_price": d("0.570000"),
        "gross_edge": d("0.050000"),
        "estimated_cost_drag": d("0.015000"),
        "cost_score": d("0.800000"),
        "liquidity_score": d("0.760000"),
        "evidence_score": d("0.820000"),
        "team_memory_score": d("0.740000"),
        "team_memory_policy": "allow",
        "source_report_refs": (
            "resolution-dispute-risk:sha256-alpha",
            "outcome-rule-clarity:sha256-beta",
        ),
        "specificity_status": "pass",
        "specificity_risk_score": d("0.000000"),
        "dependency_status": "pass",
        "dependency_risk_score": d("0.000000"),
        "dispute_risk_status": "clear",
        "dispute_risk_score": d("0.000000"),
        "outcome_rule_clarity_status": "clear",
        "outcome_rule_clarity_score": d("1.000000"),
        "close_readiness_status": "ready",
        "authoritative_source_present": True,
        "unresolved_ambiguity_count": d("0"),
        "reason_codes": ("upstream_resolution_clear",),
    }
    values.update(overrides)
    return module.CandidateDecisionResolutionRiskFacts(**values)


def report(**overrides: object):
    module = api()
    return module.build_candidate_decision_resolution_risk_adapter_report(
        facts(**overrides),
    )


def test_clear_low_risk_resolution_score_feeds_candidate_decision_input() -> None:
    module = api()
    decision_module = decision_api()

    adapter_report = report()
    decision_input = module.build_candidate_decision_score_input_from_resolution_risk(
        facts(),
    )

    assert type(adapter_report) is module.CandidateDecisionResolutionRiskAdapterReport
    assert is_dataclass(adapter_report)
    assert adapter_report.__dataclass_params__.frozen
    assert adapter_report.resolution_score == d("1.000000")
    assert adapter_report.resolution_risk_status == "clear"
    assert adapter_report.close_readiness_score == d("1.000000")
    assert adapter_report.hard_blocker_codes == ()
    assert adapter_report.reason_codes == (
        "resolution_adapter_clear",
        "resolution_authoritative_source_present",
        "resolution_close_ready",
        "resolution_no_unresolved_ambiguity",
        "upstream_resolution_clear",
    )

    assert type(decision_input) is decision_module.CandidateDecisionScoreInput
    assert decision_input.resolution_score == d("1.000000")
    assert decision_input.adapter_reason_codes == adapter_report.reason_codes
    assert decision_input.primary_team_id == "crypto_btc"
    assert decision_input.secondary_team_ids == ("macro_rates",)
    assert decision_input.paper_only is True
    assert decision_input.report_only is True
    assert decision_input.readonly is True


def test_dependency_and_dispute_blockers_force_resolution_floor() -> None:
    dependency = report(
        dependency_status="blocked",
        dependency_risk_score=d("0.720000"),
    )
    dispute = report(
        dispute_risk_status="elevated",
        dispute_risk_score=d("0.500000"),
    )

    assert dependency.resolution_score == d("0.300000")
    assert dependency.resolution_risk_status == "blocked"
    assert dependency.hard_blocker_codes == ("resolution_dependency_blocked",)
    assert dependency.reason_codes[:2] == (
        "resolution_adapter_blocked",
        "resolution_dependency_blocked",
    )

    assert dispute.resolution_score == d("0.300000")
    assert dispute.resolution_risk_status == "blocked"
    assert dispute.hard_blocker_codes == ("resolution_dispute_elevated",)
    assert dispute.reason_codes[:2] == (
        "resolution_adapter_blocked",
        "resolution_dispute_elevated",
    )


def test_close_readiness_watch_maps_explicitly_without_blocking() -> None:
    adapter_report = report(close_readiness_status="watch")

    assert adapter_report.close_readiness_score == d("0.650000")
    assert adapter_report.resolution_score == d("0.930000")
    assert adapter_report.resolution_risk_status == "watch"
    assert adapter_report.hard_blocker_codes == ()
    assert adapter_report.reason_codes[:3] == (
        "resolution_adapter_watch",
        "resolution_authoritative_source_present",
        "resolution_close_watch",
    )


def test_unresolved_ambiguity_blocks_even_when_component_scores_are_clear() -> None:
    adapter_report = report(unresolved_ambiguity_count=d("2"))

    assert adapter_report.resolution_score == d("0.300000")
    assert adapter_report.resolution_risk_status == "blocked"
    assert adapter_report.hard_blocker_codes == ("resolution_ambiguity_unresolved",)
    assert "resolution_ambiguity_unresolved" in adapter_report.reason_codes


def test_validation_rejects_invalid_decimals_statuses_team_ids_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="specificity_risk_score"):
        facts(specificity_risk_score=d("-0.100000"))
    with pytest.raises(ValueError, match="dependency_risk_score"):
        facts(dependency_risk_score=_DecimalSubclass("0.000000"))
    with pytest.raises(ValueError, match="dispute_risk_status"):
        facts(dispute_risk_status="blocked ")
    with pytest.raises(ValueError, match="close_readiness_status"):
        facts(close_readiness_status="pass")
    with pytest.raises(ValueError, match="outcome_rule_clarity_status"):
        facts(outcome_rule_clarity_status=_StringSubclass("clear"))
    with pytest.raises(ValueError, match="primary_team_id"):
        facts(primary_team_id="general")
    with pytest.raises(ValueError, match="secondary_team_ids"):
        facts(secondary_team_ids=("macro_rates", "macro_rates"))
    with pytest.raises(ValueError, match="authoritative_source_present"):
        facts(authoritative_source_present=1)
    with pytest.raises(ValueError, match="unresolved_ambiguity_count"):
        facts(unresolved_ambiguity_count=d("1.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        facts(paper_only=False)
    with pytest.raises(ValueError, match="CandidateDecisionResolutionRiskFacts"):
        module.build_candidate_decision_resolution_risk_adapter_report(object())

    frozen = facts()
    with pytest.raises(FrozenInstanceError):
        frozen.close_readiness_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="resolution_score"):
        replace(report(), resolution_score=1)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report(),
            resolution_risk_status="blocked",
            reason_codes=("resolution_adapter_blocked",),
        )


def test_payload_is_json_safe_and_contains_no_float_or_decimal_values() -> None:
    module = api()
    adapter_report = report(
        specificity_risk_score=d("0.120000"),
        dependency_risk_score=d("0.080000"),
        dispute_risk_score=d("0.040000"),
        outcome_rule_clarity_score=d("0.900000"),
        reason_codes=("zeta_source", "alpha_source"),
    )

    payload = module.candidate_decision_resolution_risk_adapter_payload(adapter_report)

    assert payload["resolution_score"] == "0.892000"
    assert payload["specificity_risk_score"] == "0.120000"
    assert payload["unresolved_ambiguity_count"] == "0"
    assert payload["reason_codes"] == [
        "resolution_adapter_watch",
        "resolution_authoritative_source_present",
        "resolution_close_ready",
        "resolution_no_unresolved_ambiguity",
        "alpha_source",
        "zeta_source",
    ]
    json.dumps(payload, sort_keys=True)
    assert not any(isinstance(value, (Decimal, float)) for value in _walk_payload(payload))

    for public_record in (facts(), adapter_report):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal, field.name


def test_static_module_has_no_forbidden_surfaces_or_float_literals() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    call_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("adapter module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite3",
        "supabase",
        "os",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "execute",
        "urlopen",
        "getenv",
        "system",
        "popen",
    }
    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert call_names.isdisjoint(forbidden_call_names)

    lowered = source.lower()
    for forbidden in (
        "api_key",
        "authorization",
        "credential",
        "private_key",
        "secret",
        "wallet",
        "account_access",
        "order_placement",
        "place_order",
        "submit_order",
        "cancel_order",
        "live_trading",
        "network",
        "database",
        "db_",
    ):
        assert forbidden not in lowered


def _walk_payload(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload(item))
    else:
        values.append(value)
    return tuple(values)
