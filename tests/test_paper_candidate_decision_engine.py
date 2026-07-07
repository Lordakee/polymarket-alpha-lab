from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.candidate_decision_cost_liquidity_adapter import (
    CandidateDecisionCostLiquidityFacts,
    adapt_candidate_decision_cost_liquidity,
)
from polymarket_alpha_lab.candidate_decision_evidence_adapter import (
    CandidateDecisionEvidenceAdapterInput,
    build_candidate_decision_evidence_adapter_result,
)
from polymarket_alpha_lab.candidate_decision_resolution_risk_adapter import (
    CandidateDecisionResolutionRiskFacts,
    build_candidate_decision_resolution_risk_adapter_report,
)
from polymarket_alpha_lab.candidate_decision_team_memory_adapter import (
    CandidateDecisionTeamMemoryAdapterInput,
    build_candidate_decision_team_memory_adapter,
)


MODULE_NAME = "polymarket_alpha_lab.paper_candidate_decision_engine"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "paper_candidate_decision_engine.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing orchestrator module: {MODULE_NAME}")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def _cost_liquidity(**overrides: object) -> Any:
    values: dict[str, object] = {
        "candidate_id": "candidate-alpha",
        "market_id": "market-alpha",
        "selected_side": "yes",
        "observed_at": GENERATED_AT,
        "forecast_probability": d("0.650000"),
        "executable_price": d("0.590000"),
        "fee_cost_per_share": d("0.003000"),
        "spread_cost_per_share": d("0.010000"),
        "slippage_cost_per_share": d("0.004000"),
        "funding_cost_per_share": d("0.001000"),
        "finalization_cost_per_share": d("0.001000"),
        "time_cost_per_share": d("0.001000"),
        "risk_cost_per_share": d("0.002000"),
        "capital_cost_per_share": d("0.003000"),
        "requested_paper_shares": d("100.000000"),
        "available_depth_shares": d("200.000000"),
        "reason_codes": ("cost_liquidity_input",),
    }
    values.update(overrides)
    return adapt_candidate_decision_cost_liquidity(
        CandidateDecisionCostLiquidityFacts(**values),
    )


def _evidence(**overrides: object) -> Any:
    values: dict[str, object] = {
        "source_count": d("4"),
        "fresh_source_count": d("4"),
        "authority_score": d("0.950000"),
        "redundancy_score": d("0.900000"),
        "contradiction_score": d("0.000000"),
        "traceability_score": d("0.950000"),
        "stale_source_count": d("0"),
        "source_report_refs": (
            "evidence:alpha-secondary",
            "evidence:alpha-primary",
        ),
    }
    values.update(overrides)
    return build_candidate_decision_evidence_adapter_result(
        CandidateDecisionEvidenceAdapterInput(**values),
    )


def _team_memory(**overrides: object) -> Any:
    values: dict[str, object] = {
        "primary_team_id": "politics",
        "secondary_team_ids": ("crypto_btc",),
        "memory_use_policy": "allow",
        "calibration_score": d("0.900000"),
        "settled_sample_count": d("40"),
        "source_memory_score": d("0.800000"),
        "capacity_score": d("0.700000"),
        "source_report_refs": ("team-memory:politics",),
        "source_reason_codes": ("team_memory_readiness_digest_passed",),
    }
    values.update(overrides)
    return build_candidate_decision_team_memory_adapter(
        CandidateDecisionTeamMemoryAdapterInput(**values),
    )


def _resolution_risk(
    *,
    cost_liquidity: Any,
    evidence: Any,
    team_memory: Any,
    normalized_market_question: str = "Will the alpha event resolve yes?",
    source_report_refs: tuple[str, ...] = ("resolution:alpha",),
    **overrides: object,
) -> Any:
    values: dict[str, object] = {
        "candidate_id": cost_liquidity.candidate_id,
        "market_id": cost_liquidity.market_id,
        "normalized_market_question": normalized_market_question,
        "primary_team_id": team_memory.primary_team_id,
        "secondary_team_ids": team_memory.secondary_team_ids,
        "selected_side": cost_liquidity.selected_side,
        "forecast_probability": cost_liquidity.forecast_probability,
        "executable_price": cost_liquidity.executable_price,
        "gross_edge": cost_liquidity.gross_edge,
        "estimated_cost_drag": cost_liquidity.estimated_cost_drag,
        "cost_score": cost_liquidity.cost_score,
        "liquidity_score": cost_liquidity.liquidity_score,
        "evidence_score": evidence.evidence_score,
        "team_memory_score": team_memory.team_memory_score,
        "team_memory_policy": team_memory.team_memory_policy,
        "source_report_refs": source_report_refs,
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
        "reason_codes": ("resolution_input_vetted",),
    }
    values.update(overrides)
    return build_candidate_decision_resolution_risk_adapter_report(
        CandidateDecisionResolutionRiskFacts(**values),
    )


def _engine_input(
    *,
    candidate_id: str = "candidate-alpha",
    market_id: str = "market-alpha",
    normalized_market_question: str = "Will the alpha event resolve yes?",
    cost_liquidity: Any | None = None,
    evidence: Any | None = None,
    resolution_risk: Any | None = None,
    team_memory: Any | None = None,
    source_report_refs: tuple[str, ...] = ("candidate-screen:alpha",),
) -> Any:
    module = api()
    cost_output = cost_liquidity if cost_liquidity is not None else _cost_liquidity(
        candidate_id=candidate_id,
        market_id=market_id,
    )
    evidence_output = evidence if evidence is not None else _evidence()
    team_output = team_memory if team_memory is not None else _team_memory()
    resolution_output = (
        resolution_risk
        if resolution_risk is not None
        else _resolution_risk(
            cost_liquidity=cost_output,
            evidence=evidence_output,
            team_memory=team_output,
            normalized_market_question=normalized_market_question,
        )
    )
    return module.PaperCandidateDecisionEngineInput(
        candidate_id=candidate_id,
        market_id=market_id,
        normalized_market_question=normalized_market_question,
        primary_team_id=team_output.primary_team_id,
        secondary_team_ids=team_output.secondary_team_ids,
        selected_side=cost_output.selected_side,
        forecast_probability=cost_output.forecast_probability,
        executable_price=cost_output.executable_price,
        source_report_refs=source_report_refs,
        cost_liquidity=cost_output,
        evidence=evidence_output,
        resolution_risk=resolution_output,
        team_memory=team_output,
    )


def _report(*inputs: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_paper_candidate_decision_engine_report(
        inputs,
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_paper_recommend_row_uses_all_adapter_outputs_and_merged_provenance() -> None:
    module = api()
    candidate = _engine_input(
        source_report_refs=("candidate-screen:z", "candidate-screen:a"),
    )

    report = _report(candidate)

    assert is_dataclass(report)
    assert report.candidate_count == d("1")
    assert report.paper_recommend_count == d("1")
    assert report.reject_count == d("0")
    assert report.watch_count == d("0")
    assert report.research_more_count == d("0")
    assert len(report.rows) == 1

    row = report.rows[0]
    assert type(row) is module.PaperCandidateDecisionEngineRow
    assert row.score_report.action == "paper_recommend"
    assert row.score_report.candidate_id == "candidate-alpha"
    assert row.score_report.market_id == "market-alpha"
    assert row.score_report.net_edge == d("0.035000")
    assert row.score_report.cost_score == candidate.cost_liquidity.cost_score
    assert row.score_report.liquidity_score == candidate.cost_liquidity.liquidity_score
    assert row.score_report.evidence_score == candidate.evidence.evidence_score
    assert row.score_report.resolution_score == candidate.resolution_risk.resolution_score
    assert row.score_report.team_memory_score == candidate.team_memory.team_memory_score
    assert row.score_input.source_report_refs == (
        "candidate-screen:a",
        "candidate-screen:z",
        "evidence:alpha-primary",
        "evidence:alpha-secondary",
        "resolution:alpha",
        "team-memory:politics",
    )
    assert row.score_input.adapter_reason_codes == tuple(
        sorted(row.score_input.adapter_reason_codes),
    )
    assert "candidate_cost_liquidity_adapter_v0" in row.score_input.adapter_reason_codes
    assert "evidence_adapter_pass" in row.score_input.adapter_reason_codes
    assert "resolution_adapter_clear" in row.score_input.adapter_reason_codes
    assert "team_memory_adapter_allow" in row.score_input.adapter_reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_rejects_due_to_evidence_resolution_and_team_memory_blockers() -> None:
    evidence_block = _evidence(contradiction_score=d("0.800000"))
    evidence_candidate = _engine_input(
        candidate_id="candidate-evidence-block",
        market_id="market-evidence-block",
        evidence=evidence_block,
    )

    resolution_cost = _cost_liquidity(
        candidate_id="candidate-resolution-block",
        market_id="market-resolution-block",
    )
    resolution_evidence = _evidence()
    resolution_team = _team_memory()
    resolution_block = _resolution_risk(
        cost_liquidity=resolution_cost,
        evidence=resolution_evidence,
        team_memory=resolution_team,
        specificity_status="blocked",
    )
    resolution_candidate = _engine_input(
        candidate_id="candidate-resolution-block",
        market_id="market-resolution-block",
        cost_liquidity=resolution_cost,
        evidence=resolution_evidence,
        resolution_risk=resolution_block,
        team_memory=resolution_team,
    )

    team_cost = _cost_liquidity(
        candidate_id="candidate-team-block",
        market_id="market-team-block",
    )
    team_evidence = _evidence()
    team_block = _team_memory(memory_use_policy="block")
    team_resolution = _resolution_risk(
        cost_liquidity=team_cost,
        evidence=team_evidence,
        team_memory=team_block,
    )
    team_candidate = _engine_input(
        candidate_id="candidate-team-block",
        market_id="market-team-block",
        cost_liquidity=team_cost,
        evidence=team_evidence,
        resolution_risk=team_resolution,
        team_memory=team_block,
    )

    report = _report(evidence_candidate, resolution_candidate, team_candidate)

    assert report.reject_count == d("3")
    hard_blockers = {
        row.score_report.candidate_id: row.score_report.hard_blocker_codes
        for row in report.rows
    }
    assert hard_blockers["candidate-evidence-block"] == (
        "evidence_score_below_blocking_threshold",
    )
    assert hard_blockers["candidate-resolution-block"] == (
        "resolution_score_below_blocking_threshold",
    )
    assert hard_blockers["candidate-team-block"] == (
        "team_memory_policy_blocked",
    )
    assert all(row.score_report.action == "reject" for row in report.rows)


def test_research_more_and_watch_aggregate_counts() -> None:
    research_team = _team_memory(memory_use_policy="throttle")
    research_cost = _cost_liquidity(
        candidate_id="candidate-research",
        market_id="market-research",
    )
    research_evidence = _evidence()
    research_resolution = _resolution_risk(
        cost_liquidity=research_cost,
        evidence=research_evidence,
        team_memory=research_team,
    )
    research_candidate = _engine_input(
        candidate_id="candidate-research",
        market_id="market-research",
        cost_liquidity=research_cost,
        evidence=research_evidence,
        resolution_risk=research_resolution,
        team_memory=research_team,
    )

    watch_cost = _cost_liquidity(
        candidate_id="candidate-watch",
        market_id="market-watch",
        forecast_probability=d("0.620000"),
    )
    watch_evidence = _evidence()
    watch_team = _team_memory()
    watch_resolution = _resolution_risk(
        cost_liquidity=watch_cost,
        evidence=watch_evidence,
        team_memory=watch_team,
    )
    watch_candidate = _engine_input(
        candidate_id="candidate-watch",
        market_id="market-watch",
        cost_liquidity=watch_cost,
        evidence=watch_evidence,
        resolution_risk=watch_resolution,
        team_memory=watch_team,
    )

    report = _report(watch_candidate, research_candidate)

    assert report.candidate_count == d("2")
    assert report.reject_count == d("0")
    assert report.research_more_count == d("1")
    assert report.watch_count == d("1")
    assert report.paper_recommend_count == d("0")
    assert {
        row.score_report.candidate_id: row.score_report.action for row in report.rows
    } == {
        "candidate-research": "research_more",
        "candidate-watch": "watch",
    }


def test_identity_mismatches_are_rejected_before_building_rows() -> None:
    module = api()
    cost = _cost_liquidity(candidate_id="candidate-alpha", market_id="market-alpha")
    evidence = _evidence()
    team = _team_memory()
    resolution = _resolution_risk(
        cost_liquidity=cost,
        evidence=evidence,
        team_memory=team,
    )

    with pytest.raises(ValueError, match="cost_liquidity.candidate_id"):
        module.PaperCandidateDecisionEngineInput(
            candidate_id="candidate-other",
            market_id="market-alpha",
            normalized_market_question="Will the alpha event resolve yes?",
            primary_team_id="politics",
            secondary_team_ids=("crypto_btc",),
            selected_side="yes",
            forecast_probability=d("0.650000"),
            executable_price=d("0.590000"),
            source_report_refs=("candidate-screen:alpha",),
            cost_liquidity=cost,
            evidence=evidence,
            resolution_risk=resolution,
            team_memory=team,
        )

    with pytest.raises(ValueError, match="resolution_risk.market_id"):
        _engine_input(
            resolution_risk=replace(resolution, market_id="market-other"),
        )
    with pytest.raises(ValueError, match="team_memory.primary_team_id"):
        module.PaperCandidateDecisionEngineInput(
            candidate_id="candidate-alpha",
            market_id="market-alpha",
            normalized_market_question="Will the alpha event resolve yes?",
            primary_team_id="politics",
            secondary_team_ids=("crypto_btc",),
            selected_side="yes",
            forecast_probability=d("0.650000"),
            executable_price=d("0.590000"),
            source_report_refs=("candidate-screen:alpha",),
            cost_liquidity=cost,
            evidence=evidence,
            resolution_risk=resolution,
            team_memory=_team_memory(primary_team_id="crypto_btc", secondary_team_ids=()),
        )
    with pytest.raises(ValueError, match="evidence_score"):
        _engine_input(
            evidence=build_candidate_decision_evidence_adapter_result(
                CandidateDecisionEvidenceAdapterInput(
                    source_count=d("4"),
                    fresh_source_count=d("4"),
                    authority_score=d("0.500000"),
                    redundancy_score=d("0.900000"),
                    contradiction_score=d("0.000000"),
                    traceability_score=d("0.950000"),
                    stale_source_count=d("0"),
                    source_report_refs=("evidence:lower-score",),
                ),
            ),
            resolution_risk=resolution,
        )


def test_deterministic_row_sorting_and_reason_counts() -> None:
    beta_cost = _cost_liquidity(candidate_id="candidate-beta", market_id="market-beta")
    beta_evidence = _evidence(source_report_refs=("evidence:beta",))
    beta_team = _team_memory(source_report_refs=("team-memory:beta",))
    beta_resolution = _resolution_risk(
        cost_liquidity=beta_cost,
        evidence=beta_evidence,
        team_memory=beta_team,
        source_report_refs=("resolution:beta",),
    )
    beta = _engine_input(
        candidate_id="candidate-beta",
        market_id="market-beta",
        cost_liquidity=beta_cost,
        evidence=beta_evidence,
        resolution_risk=beta_resolution,
        team_memory=beta_team,
        source_report_refs=("candidate-screen:beta",),
    )

    alpha = _engine_input(source_report_refs=("candidate-screen:alpha",))
    report = _report(beta, alpha)

    assert tuple(row.score_report.candidate_id for row in report.rows) == (
        "candidate-alpha",
        "candidate-beta",
    )
    assert report.reason_counts == tuple(
        sorted(report.reason_counts, key=lambda item: item.reason_code),
    )
    reason_counts = {item.reason_code: item.count for item in report.reason_counts}
    assert reason_counts["candidate_decision_paper_recommend"] == d("2")
    assert reason_counts["candidate_cost_liquidity_adapter_v0"] == d("2")
    assert reason_counts["evidence_adapter_pass"] == d("2")
    assert reason_counts["team_memory_adapter_allow"] == d("2")
    assert reason_counts["resolution_adapter_clear"] == d("2")


def test_payload_json_contains_no_floats_and_report_is_frozen() -> None:
    module = api()
    report = _report(_engine_input())

    payload = module.paper_candidate_decision_engine_payload(report)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["paper_recommend_count"] == "1"
    assert payload["rows"][0]["score_report"]["action"] == "paper_recommend"
    assert payload["rows"][0]["score_input"]["forecast_probability"] == "0.650000"
    assert payload["rows"][0]["score_input"]["adapter_reason_codes"] == sorted(
        payload["rows"][0]["score_input"]["adapter_reason_codes"],
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "candidate-alpha" in rendered
    assert_no_float_values(payload)

    with pytest.raises(FrozenInstanceError):
        report.paper_recommend_count = d("0")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].score_report = report.rows[0].score_report  # type: ignore[misc]
    with pytest.raises(ValueError, match="report"):
        module.paper_candidate_decision_engine_payload(object())


def test_hard_flags_exact_types_and_forbidden_surface_scan() -> None:
    module = api()
    candidate = _engine_input()

    assert module.__all__ == (
        "DEFAULT_PAPER_CANDIDATE_DECISION_ENGINE_VERSION",
        "PaperCandidateDecisionEngineInput",
        "PaperCandidateDecisionEngineReasonCount",
        "PaperCandidateDecisionEngineRow",
        "PaperCandidateDecisionEngineReport",
        "build_paper_candidate_decision_engine_report",
        "paper_candidate_decision_engine_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(candidate, readonly=False)
    with pytest.raises(ValueError, match="inputs"):
        module.build_paper_candidate_decision_engine_report(
            candidate,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PaperCandidateDecisionEngineInput"):
        module.build_paper_candidate_decision_engine_report(
            [object()],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_paper_candidate_decision_engine_report(
            [candidate],
            generated_at=datetime(2026, 7, 7, 12, 0),
        )

    for item in fields(candidate):
        value = getattr(candidate, item.name)
        if item.name in {"paper_only", "report_only", "readonly"}:
            continue
        if isinstance(value, Decimal):
            assert type(value) is Decimal

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for banned in (
        "requests",
        "httpx",
        "urllib",
        "websocket",
        "socket",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "subprocess",
        "click",
        "argparse",
        "open(",
        ".write(",
        "private_key",
        "wallet",
        "place_order",
        "cancel_order",
        "execute(",
        "connect(",
    ):
        assert banned not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "float"}
