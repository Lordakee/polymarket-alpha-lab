from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
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
from polymarket_alpha_lab.candidate_decision_score import CandidateDecisionScoreConfig
from polymarket_alpha_lab.candidate_decision_team_memory_adapter import (
    CandidateDecisionTeamMemoryAdapterInput,
    build_candidate_decision_team_memory_adapter,
)
from polymarket_alpha_lab.paper_candidate_decision_engine import (
    PaperCandidateDecisionEngineInput,
    PaperCandidateDecisionEngineReport,
    build_paper_candidate_decision_engine_report,
)


MODULE_NAME = "polymarket_alpha_lab.paper_candidate_decision_engine_load"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "paper_candidate_decision_engine_load.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing loader module: {MODULE_NAME}")
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
    return module.PaperCandidateDecisionEngineCandidateBundle(**values)


def _engine_input_from_bundle(bundle: object) -> PaperCandidateDecisionEngineInput:
    module = api()
    return module.paper_candidate_decision_engine_input_from_bundle(bundle)


def _unsafe_exact_bundle(source: object, **overrides: object) -> object:
    module = api()
    bundle = object.__new__(module.PaperCandidateDecisionEngineCandidateBundle)
    for item in fields(source):
        object.__setattr__(bundle, item.name, getattr(source, item.name))
    for field_name, value in overrides.items():
        object.__setattr__(bundle, field_name, value)
    return bundle


def test_load_report_from_bundle_loader_delegates_exact_inputs_and_sorts_rows() -> None:
    module = api()
    alpha = _bundle(source_report_refs=("candidate-screen:z", "candidate-screen:a"))

    beta_cost = _cost_liquidity(candidate_id="candidate-beta", market_id="market-beta")
    beta_evidence = _evidence(source_report_refs=("evidence:beta",))
    beta_team = _team_memory(source_report_refs=("team-memory:beta",))
    beta_resolution = _resolution_risk(
        cost_liquidity=beta_cost,
        evidence=beta_evidence,
        team_memory=beta_team,
        source_report_refs=("resolution:beta",),
    )
    beta = _bundle(
        candidate_id="candidate-beta",
        market_id="market-beta",
        cost_liquidity=beta_cost,
        evidence=beta_evidence,
        resolution_risk=beta_resolution,
        team_memory=beta_team,
        source_report_refs=("candidate-screen:beta",),
    )
    score_config = CandidateDecisionScoreConfig()
    calls: list[tuple[str, object]] = []

    def candidate_bundle_loader() -> tuple[object, ...]:
        calls.append(("loader", None))
        return (beta, alpha)

    def report_builder(
        inputs: tuple[PaperCandidateDecisionEngineInput, ...],
        *,
        generated_at: datetime,
        score_config: CandidateDecisionScoreConfig | None,
    ) -> PaperCandidateDecisionEngineReport:
        calls.append(("builder", inputs))
        assert generated_at is GENERATED_AT
        assert score_config is score_config_arg
        assert tuple(input_value.candidate_id for input_value in inputs) == (
            "candidate-beta",
            "candidate-alpha",
        )
        assert all(type(input_value) is PaperCandidateDecisionEngineInput for input_value in inputs)
        assert inputs[1].source_report_refs == (
            "candidate-screen:a",
            "candidate-screen:z",
        )
        return build_paper_candidate_decision_engine_report(
            inputs,
            generated_at=generated_at,
            score_config=score_config,
        )

    score_config_arg = score_config
    report = module.load_paper_candidate_decision_engine_report(
        generated_at=GENERATED_AT,
        score_config=score_config,
        candidate_bundle_loader=candidate_bundle_loader,
        report_builder=report_builder,
    )

    assert type(report) is PaperCandidateDecisionEngineReport
    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-alpha",
        "candidate-beta",
    )
    assert report.candidate_count == d("2")
    assert calls[0] == ("loader", None)
    assert calls[1][0] == "builder"
    assert len(calls) == 2


def test_load_report_accepts_explicit_bundles_and_input_loader_sources() -> None:
    module = api()
    bundle = _bundle()
    input_value = _engine_input_from_bundle(bundle)
    input_loader_calls = 0

    report_from_bundle = module.load_paper_candidate_decision_engine_report(
        generated_at=GENERATED_AT,
        candidate_bundles=(bundle,),
    )

    def candidate_input_loader() -> tuple[PaperCandidateDecisionEngineInput, ...]:
        nonlocal input_loader_calls
        input_loader_calls += 1
        return (input_value,)

    report_from_input_loader = module.load_paper_candidate_decision_engine_report(
        generated_at=GENERATED_AT,
        candidate_input_loader=candidate_input_loader,
    )

    assert type(report_from_bundle) is PaperCandidateDecisionEngineReport
    assert type(report_from_input_loader) is PaperCandidateDecisionEngineReport
    assert report_from_bundle.rows[0].score_report.candidate_id == "candidate-alpha"
    assert report_from_input_loader.rows[0].score_report.candidate_id == "candidate-alpha"
    assert input_loader_calls == 1


def test_candidate_bundle_is_frozen_and_enforces_exact_type_and_hard_flags() -> None:
    module = api()
    bundle = _bundle()

    assert module.__all__ == (
        "PaperCandidateDecisionEngineCandidateBundle",
        "load_paper_candidate_decision_engine_report",
        "paper_candidate_decision_engine_input_from_bundle",
    )
    assert is_dataclass(module.PaperCandidateDecisionEngineCandidateBundle)
    assert module.PaperCandidateDecisionEngineCandidateBundle.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        bundle.market_id = "market-other"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        module.PaperCandidateDecisionEngineCandidateBundle(
            candidate_id=bundle.candidate_id,
            market_id=bundle.market_id,
            normalized_market_question=bundle.normalized_market_question,
            primary_team_id=bundle.primary_team_id,
            secondary_team_ids=bundle.secondary_team_ids,
            selected_side=bundle.selected_side,
            forecast_probability=bundle.forecast_probability,
            executable_price=bundle.executable_price,
            source_report_refs=bundle.source_report_refs,
            cost_liquidity=bundle.cost_liquidity,
            evidence=bundle.evidence,
            resolution_risk=bundle.resolution_risk,
            team_memory=bundle.team_memory,
            readonly=False,
        )

    class BundleSubclass(module.PaperCandidateDecisionEngineCandidateBundle):
        pass

    with pytest.raises(ValueError, match="exactly PaperCandidateDecisionEngineCandidateBundle"):
        BundleSubclass(
            candidate_id=bundle.candidate_id,
            market_id=bundle.market_id,
            normalized_market_question=bundle.normalized_market_question,
            primary_team_id=bundle.primary_team_id,
            secondary_team_ids=bundle.secondary_team_ids,
            selected_side=bundle.selected_side,
            forecast_probability=bundle.forecast_probability,
            executable_price=bundle.executable_price,
            source_report_refs=bundle.source_report_refs,
            cost_liquidity=bundle.cost_liquidity,
            evidence=bundle.evidence,
            resolution_risk=bundle.resolution_risk,
            team_memory=bundle.team_memory,
        )

    bad_loaded_bundle = _unsafe_exact_bundle(bundle, readonly=False)
    builder_calls = 0

    def report_builder(**_kwargs: object) -> object:
        nonlocal builder_calls
        builder_calls += 1
        raise AssertionError("builder must not run after hard-flag rejection")

    with pytest.raises(ValueError, match="candidate_bundles.0"):
        module.load_paper_candidate_decision_engine_report(
            generated_at=GENERATED_AT,
            candidate_bundles=(bad_loaded_bundle,),
            report_builder=report_builder,
        )
    assert builder_calls == 0

    with pytest.raises(
        ValueError,
        match="candidate_bundles.0 must be exactly PaperCandidateDecisionEngineCandidateBundle",
    ):
        module.load_paper_candidate_decision_engine_report(
            generated_at=GENERATED_AT,
            candidate_bundles=(SimpleNamespace(paper_only=True, report_only=True, readonly=True),),
            report_builder=report_builder,
        )
    assert builder_calls == 0


def test_rejects_bad_sources_and_mismatches_through_engine_input_validation() -> None:
    module = api()
    bundle = _bundle()

    with pytest.raises(ValueError, match="exactly one candidate source"):
        module.load_paper_candidate_decision_engine_report(generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="exactly one candidate source"):
        module.load_paper_candidate_decision_engine_report(
            generated_at=GENERATED_AT,
            candidate_bundles=(bundle,),
            candidate_bundle_loader=lambda: (bundle,),
        )
    with pytest.raises(ValueError, match="candidate_bundles must be a list or tuple"):
        module.load_paper_candidate_decision_engine_report(
            generated_at=GENERATED_AT,
            candidate_bundles={bundle},
        )
    with pytest.raises(ValueError, match="candidate_bundle_loader must be callable"):
        module.load_paper_candidate_decision_engine_report(
            generated_at=GENERATED_AT,
            candidate_bundle_loader=object(),
        )

    bad_mismatch = _unsafe_exact_bundle(bundle, candidate_id="candidate-other")
    with pytest.raises(ValueError, match="cost_liquidity.candidate_id"):
        module.load_paper_candidate_decision_engine_report(
            generated_at=GENERATED_AT,
            candidate_bundles=(bad_mismatch,),
        )


def test_rejects_floats_non_exact_score_config_and_non_exact_report_return() -> None:
    module = api()
    bundle = _bundle()

    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        _bundle(forecast_probability=0.65)

    class ScoreConfigSubclass(CandidateDecisionScoreConfig):
        pass

    score_config = CandidateDecisionScoreConfig()
    bad_score_config = object.__new__(ScoreConfigSubclass)
    for item in fields(score_config):
        object.__setattr__(bad_score_config, item.name, getattr(score_config, item.name))

    with pytest.raises(ValueError, match="score_config"):
        module.load_paper_candidate_decision_engine_report(
            generated_at=GENERATED_AT,
            score_config=bad_score_config,
            candidate_bundles=(bundle,),
        )

    with pytest.raises(ValueError, match="paper candidate decision engine report"):
        module.load_paper_candidate_decision_engine_report(
            generated_at=GENERATED_AT,
            candidate_bundles=(bundle,),
            report_builder=lambda *_args, **_kwargs: SimpleNamespace(
                paper_only=True,
                report_only=True,
                readonly=True,
            ),
        )


def test_loader_module_has_no_network_db_cli_file_write_or_float_surface() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    signature = inspect.signature(module.load_paper_candidate_decision_engine_report)

    for forbidden_parameter in (
        "connection",
        "cursor",
        "dsn",
        "table",
        "path",
        "filename",
    ):
        assert forbidden_parameter not in signature.parameters

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
            assert node.func.id not in {"open", "float"}
