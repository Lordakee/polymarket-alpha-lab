from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest


def api():
    return importlib.import_module("polymarket_alpha_lab.candidate_decision_evidence_adapter")


def decision_api():
    return importlib.import_module("polymarket_alpha_lab.candidate_decision_score")


def d(value: str) -> Decimal:
    return Decimal(value)


def facts(**overrides: object):
    module = api()
    values = {
        "source_count": d("3"),
        "fresh_source_count": d("3"),
        "authority_score": d("0.900000"),
        "redundancy_score": d("0.800000"),
        "contradiction_score": d("0.020000"),
        "traceability_score": d("0.950000"),
        "freshness_minutes": d("10.000000"),
        "source_report_refs": ("freshness-authority:abc123", "contradiction:def456"),
    }
    values.update(overrides)
    return module.CandidateDecisionEvidenceAdapterInput(**values)


def build(**overrides: object):
    module = api()
    return module.build_candidate_decision_evidence_adapter_result(facts(**overrides))


def decision_input(adapter_result):
    module = decision_api()
    adapter = api()
    evidence_fields = adapter.candidate_decision_evidence_adapter_decision_fields(
        adapter_result,
    )
    return module.CandidateDecisionScoreInput(
        candidate_id="candidate-btc-fed-001",
        market_id="market-btc-fed-001",
        normalized_market_question="btc above threshold after fed decision",
        primary_team_id="crypto_btc",
        secondary_team_ids=("macro_rates",),
        selected_side="yes",
        forecast_probability=d("0.620000"),
        executable_price=d("0.570000"),
        gross_edge=d("0.050000"),
        estimated_cost_drag=d("0.015000"),
        cost_score=d("0.800000"),
        liquidity_score=d("0.800000"),
        resolution_score=d("0.800000"),
        team_memory_score=d("0.800000"),
        team_memory_policy="allow",
        **evidence_fields,
    )


def decision_report(adapter_result):
    module = decision_api()
    return module.build_candidate_decision_score_report(
        decision_input(adapter_result),
        config=module.CandidateDecisionScoreConfig(),
        generated_at=datetime(2026, 7, 7, 12, 0, tzinfo=UTC),
    )


def test_strong_evidence_passes_and_feeds_candidate_decision_input() -> None:
    module = api()
    result = build()

    assert type(result) is module.CandidateDecisionEvidenceAdapterResult
    assert is_dataclass(result)
    assert result.evidence_status == "pass"
    assert result.evidence_score == d("0.919500")
    assert result.weighted_evidence_score == d("0.919500")
    assert result.reason_codes == ("evidence_adapter_pass",)
    assert tuple(component.component_name for component in result.components) == (
        "authority_score",
        "contradiction_absence_score",
        "freshness_score",
        "redundancy_score",
        "source_count_score",
        "traceability_score",
    )
    assert sum((component.component_weight for component in result.components), d("0")) == d(
        "1.000000",
    )
    assert result.source_report_refs == (
        "contradiction:def456",
        "freshness-authority:abc123",
    )

    evidence_fields = module.candidate_decision_evidence_adapter_decision_fields(result)
    assert evidence_fields == {
        "adapter_reason_codes": ("evidence_adapter_pass",),
        "evidence_score": d("0.919500"),
        "source_report_refs": (
            "contradiction:def456",
            "freshness-authority:abc123",
        ),
    }
    assert decision_report(result).action == "paper_recommend"


def test_stale_single_source_creates_research_more_pressure_not_reject() -> None:
    result = build(
        source_count=d("1"),
        fresh_source_count=d("1"),
        redundancy_score=d("0.200000"),
        freshness_minutes=d("90.000000"),
    )

    assert result.evidence_status == "research_more"
    assert result.evidence_score == d("0.601167")
    assert result.reason_codes == (
        "evidence_adapter_research_more",
        "evidence_single_source_research_more",
        "evidence_freshness_stale",
        "evidence_redundancy_low",
        "evidence_weighted_score_below_pass_threshold",
    )
    report = decision_report(result)
    assert report.action == "research_more"
    assert "component_score_below_paper_recommend_threshold" in report.reason_codes
    assert "evidence_score_below_blocking_threshold" not in report.hard_blocker_codes


def test_stale_source_count_can_drive_freshness_without_freshness_minutes() -> None:
    result = build(
        source_count=d("4"),
        fresh_source_count=d("2"),
        freshness_minutes=None,
        stale_source_count=d("2"),
        authority_score=d("0.850000"),
        redundancy_score=d("0.700000"),
        contradiction_score=d("0.000000"),
        traceability_score=d("0.900000"),
    )

    assert result.evidence_status == "research_more"
    assert result.evidence_score == d("0.842500")
    assert "evidence_stale_sources_present" in result.reason_codes
    assert "evidence_freshness_stale" not in result.reason_codes


def test_contradiction_blocker_caps_evidence_for_candidate_reject() -> None:
    result = build(contradiction_score=d("0.900000"))

    assert result.evidence_status == "blocked"
    assert result.weighted_evidence_score == d("0.787500")
    assert result.evidence_score == d("0.300000")
    assert result.reason_codes == (
        "evidence_adapter_blocked",
        "evidence_contradiction_blocked",
    )
    report = decision_report(result)
    assert report.action == "reject"
    assert report.hard_blocker_codes == ("evidence_score_below_blocking_threshold",)


def test_missing_traceability_blocker_caps_evidence_for_candidate_reject() -> None:
    result = build(traceability_score=d("0.000000"))

    assert result.evidence_status == "blocked"
    assert result.weighted_evidence_score == d("0.777000")
    assert result.evidence_score == d("0.300000")
    assert result.reason_codes == (
        "evidence_adapter_blocked",
        "evidence_traceability_missing",
    )
    assert decision_report(result).action == "reject"


def test_duplicate_invalid_reason_codes_and_type_edges_are_rejected() -> None:
    result = build()
    module = api()

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            result,
            reason_codes=("evidence_adapter_pass", "evidence_adapter_pass"),
        )
    with pytest.raises(ValueError, match="reason_code"):
        replace(result, reason_codes=("not_a_known_reason",))
    with pytest.raises(ValueError, match="source_count"):
        facts(source_count=d("1.5"))
    with pytest.raises(ValueError, match="authority_score"):
        facts(authority_score=0.9)
    with pytest.raises(ValueError, match="freshness_minutes"):
        facts(freshness_minutes=d("10.000000"), stale_source_count=d("0"))
    with pytest.raises(ValueError, match="freshness_minutes"):
        facts(freshness_minutes=None, stale_source_count=None)

    with pytest.raises(TypeError, match="does not support subclassing"):
        class _InputSubclass(module.CandidateDecisionEvidenceAdapterInput):
            pass


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    module = api()
    result = build()

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_EVIDENCE_ADAPTER_CONFIG_VERSION",
        "CandidateDecisionEvidenceAdapterConfig",
        "CandidateDecisionEvidenceAdapterInput",
        "CandidateDecisionEvidenceAdapterComponent",
        "CandidateDecisionEvidenceAdapterResult",
        "build_candidate_decision_evidence_adapter_result",
        "candidate_decision_evidence_adapter_decision_fields",
        "candidate_decision_evidence_adapter_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        result.evidence_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        facts(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        module.CandidateDecisionEvidenceAdapterConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        module.build_candidate_decision_evidence_adapter_result(
            facts(),
            config=module.CandidateDecisionEvidenceAdapterConfig(paper_only=False),
        )


def test_payload_is_json_ready_without_float_values() -> None:
    module = api()
    result = build()
    payload = module.candidate_decision_evidence_adapter_payload(result)

    assert payload["evidence_score"] == "0.919500"
    assert payload["weighted_evidence_score"] == "0.919500"
    assert payload["components"][0]["component_weight"] == "0.250000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert json.loads(json.dumps(payload)) == payload

    def assert_no_float(value: object) -> None:
        assert type(value) is not float
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_float(item)

    assert_no_float(payload)
    with pytest.raises(ValueError, match="float"):
        module.candidate_decision_evidence_adapter_payload({"bad": 1.2})


def test_static_module_has_no_forbidden_surface_or_float_literals() -> None:
    source = Path("src/polymarket_alpha_lab/candidate_decision_evidence_adapter.py").read_text(
        encoding="utf-8",
    )
    lowered = source.lower()
    for banned in (
        "requests",
        "httpx",
        "urllib",
        "websocket",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "subprocess",
        "argparse",
        "click",
        "typer",
        "open(",
        ".write(",
        "pathlib",
        "private_key",
        "api_key",
        "secret",
        "token",
        "wallet",
        "account",
        "broker",
        "trade",
        "network",
        "database",
    ):
        assert banned not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
