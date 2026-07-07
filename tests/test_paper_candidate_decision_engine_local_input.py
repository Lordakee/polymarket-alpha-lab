from __future__ import annotations

import ast
import importlib
import json
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
from polymarket_alpha_lab.paper_candidate_decision_engine import (
    PaperCandidateDecisionEngineReport,
)
from polymarket_alpha_lab.paper_candidate_decision_engine_load import (
    PaperCandidateDecisionEngineCandidateBundle,
)
from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats


MODULE_NAME = "polymarket_alpha_lab.paper_candidate_decision_engine_local_input"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "paper_candidate_decision_engine_local_input.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing local-input module: {MODULE_NAME}")
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


def _bundle(
    *,
    candidate_id: str = "candidate-alpha",
    market_id: str = "market-alpha",
    normalized_market_question: str = "Will the alpha event resolve yes?",
    cost_liquidity: Any | None = None,
    evidence: Any | None = None,
    resolution_risk: Any | None = None,
    team_memory: Any | None = None,
    source_report_refs: tuple[str, ...] = ("candidate-screen:alpha",),
    **overrides: object,
) -> PaperCandidateDecisionEngineCandidateBundle:
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
    values: dict[str, object] = {
        "candidate_id": candidate_id,
        "market_id": market_id,
        "normalized_market_question": normalized_market_question,
        "primary_team_id": team_output.primary_team_id,
        "secondary_team_ids": team_output.secondary_team_ids,
        "selected_side": cost_output.selected_side,
        "forecast_probability": cost_output.forecast_probability,
        "executable_price": cost_output.executable_price,
        "source_report_refs": source_report_refs,
        "cost_liquidity": cost_output,
        "evidence": evidence_output,
        "resolution_risk": resolution_output,
        "team_memory": team_output,
    }
    values.update(overrides)
    return PaperCandidateDecisionEngineCandidateBundle(**values)


def _payload(bundle: PaperCandidateDecisionEngineCandidateBundle) -> dict[str, Any]:
    payload = json_ready_no_floats(bundle)
    assert type(payload) is dict
    return payload


def test_recovers_single_object_array_and_jsonl_text_into_exact_bundles() -> None:
    module = api()
    alpha = _bundle(source_report_refs=("candidate-screen:z", "candidate-screen:a"))
    beta = _bundle(
        candidate_id="candidate-beta",
        market_id="market-beta",
        source_report_refs=("candidate-screen:beta",),
    )
    alpha_payload = _payload(alpha)
    beta_payload = _payload(beta)

    single = module.paper_candidate_decision_engine_candidate_bundles_from_jsonable(
        alpha_payload,
    )
    array_text = json.dumps([beta_payload, alpha_payload])
    array = module.paper_candidate_decision_engine_candidate_bundles_from_text(
        array_text,
    )
    jsonl_text = "\n".join(json.dumps(row) for row in (alpha_payload, beta_payload))
    jsonl = module.paper_candidate_decision_engine_candidate_bundles_from_text(
        jsonl_text,
    )

    assert single == (alpha,)
    assert tuple(row.candidate_id for row in array) == (
        "candidate-beta",
        "candidate-alpha",
    )
    assert tuple(row.candidate_id for row in jsonl) == (
        "candidate-alpha",
        "candidate-beta",
    )
    assert all(
        type(row) is PaperCandidateDecisionEngineCandidateBundle
        for rows in (single, array, jsonl)
        for row in rows
    )
    assert single[0].forecast_probability == Decimal("0.650000")
    assert single[0].source_report_refs == (
        "candidate-screen:a",
        "candidate-screen:z",
    )


def test_builds_report_from_local_json_text_through_existing_loader() -> None:
    module = api()
    alpha = _bundle()
    beta = _bundle(candidate_id="candidate-beta", market_id="market-beta")
    text = json.dumps([_payload(beta), _payload(alpha)])

    report = module.load_paper_candidate_decision_engine_report_from_local_input(
        generated_at=GENERATED_AT,
        candidate_bundle_text=text,
    )

    assert type(report) is PaperCandidateDecisionEngineReport
    assert report.generated_at == GENERATED_AT
    assert report.candidate_count == Decimal("2")
    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-alpha",
        "candidate-beta",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_explicit_path_source_reads_local_text_and_builds_report(tmp_path: Path) -> None:
    module = api()
    bundle_path = tmp_path / "candidate-bundles.jsonl"
    bundle_path.write_text(json.dumps(_payload(_bundle())) + "\n", encoding="utf-8")

    bundles = module.paper_candidate_decision_engine_candidate_bundles_from_path(
        bundle_path,
    )
    report = module.load_paper_candidate_decision_engine_report_from_local_input(
        generated_at=GENERATED_AT,
        candidate_bundle_path=bundle_path,
    )

    assert tuple(row.candidate_id for row in bundles) == ("candidate-alpha",)
    assert report.candidate_count == Decimal("1")
    assert report.rows[0].candidate_id == "candidate-alpha"


def test_rejects_empty_sources_multiple_sources_and_json_float_values() -> None:
    module = api()
    payload = _payload(_bundle())
    payload["forecast_probability"] = 0.65

    with pytest.raises(ValueError, match="at least one candidate bundle"):
        module.paper_candidate_decision_engine_candidate_bundles_from_jsonable([])
    with pytest.raises(ValueError, match="at least one candidate bundle"):
        module.paper_candidate_decision_engine_candidate_bundles_from_text("[]")
    with pytest.raises(ValueError, match="exactly one candidate bundle source"):
        module.load_paper_candidate_decision_engine_report_from_local_input(
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="exactly one candidate bundle source"):
        module.load_paper_candidate_decision_engine_report_from_local_input(
            generated_at=GENERATED_AT,
            candidate_bundle_rows=[_payload(_bundle())],
            candidate_bundle_text=json.dumps(_payload(_bundle())),
        )
    with pytest.raises(ValueError, match="JSON Decimal value must not be a float"):
        module.paper_candidate_decision_engine_candidate_bundles_from_text(
            json.dumps(payload),
        )


def test_local_input_module_has_only_pure_local_surface() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()

    assert module.__all__ == (
        "paper_candidate_decision_engine_candidate_bundles_from_jsonable",
        "paper_candidate_decision_engine_candidate_bundles_from_text",
        "paper_candidate_decision_engine_candidate_bundles_from_path",
        "load_paper_candidate_decision_engine_report_from_local_input",
    )
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
        "write_text",
        ".write(",
        "adapt_candidate_decision_cost_liquidity",
        "build_candidate_decision_evidence_adapter_result",
        "build_candidate_decision_resolution_risk_adapter_report",
        "build_candidate_decision_team_memory_adapter",
    ):
        assert banned not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "float", "eval", "exec"}
