from __future__ import annotations

import ast
import importlib
import inspect
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_recommendation_final_decision_matrix_v2"
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_RECOMMENDATION_FINAL_DECISION_MATRIX_V2_CONFIG_VERSION
        ),
        "minimum_pass_cost_adjusted_edge_bps": d("50.000000"),
        "minimum_watch_cost_adjusted_edge_bps": d("0.000000"),
        "minimum_pass_evidence_quorum_score": d("0.800000"),
        "minimum_watch_evidence_quorum_score": d("0.500000"),
        "minimum_pass_source_confidence_score": d("0.750000"),
        "minimum_watch_source_confidence_score": d("0.500000"),
        "maximum_pass_resolution_risk_score": d("0.250000"),
        "maximum_watch_resolution_risk_score": d("0.600000"),
        "minimum_pass_liquidity_capacity_ratio": d("1.500000"),
        "minimum_watch_liquidity_capacity_ratio": d("1.000000"),
        "minimum_pass_category_budget_remaining_ratio": d("0.200000"),
        "minimum_watch_category_budget_remaining_ratio": d("0.050000"),
        "minimum_pass_team_consensus_score": d("0.800000"),
        "minimum_watch_team_consensus_score": d("0.500000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationFinalDecisionMatrixV2Config(**values)


def candidate(
    candidate_id: str = "pass-alpha",
    *,
    market_slug: str | None = None,
    side: str = "yes",
    category: str = "macro",
    gross_edge_bps: Decimal = d("90.000000"),
    taker_fee_bps: Decimal = d("5.000000"),
    spread_cost_bps: Decimal = d("8.000000"),
    slippage_cost_bps: Decimal = d("7.000000"),
    evidence_quorum_score: Decimal = d("0.900000"),
    source_confidence_score: Decimal = d("0.860000"),
    resolution_risk_score: Decimal = d("0.100000"),
    liquidity_capacity_ratio: Decimal = d("2.000000"),
    category_budget_remaining_ratio: Decimal = d("0.350000"),
    team_consensus_score: Decimal = d("0.880000"),
    reason_codes: tuple[str, ...] = ("seed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.StrategyRecommendationFinalDecisionMatrixV2Candidate(
        candidate_id=candidate_id,
        market_slug=market_slug or f"{candidate_id}-market",
        side=side,
        category=category,
        gross_edge_bps=gross_edge_bps,
        taker_fee_bps=taker_fee_bps,
        spread_cost_bps=spread_cost_bps,
        slippage_cost_bps=slippage_cost_bps,
        evidence_quorum_score=evidence_quorum_score,
        source_confidence_score=source_confidence_score,
        resolution_risk_score=resolution_risk_score,
        liquidity_capacity_ratio=liquidity_capacity_ratio,
        category_budget_remaining_ratio=category_budget_remaining_ratio,
        team_consensus_score=team_consensus_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, config: object | None = None) -> Any:
    module = api()
    return module.build_strategy_recommendation_final_decision_matrix_v2_report(
        items,
        config=config if config is not None else cfg(),
    )


def assert_no_public_numeric(value: object) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (Decimal, float, int)):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_public_numeric(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric(item)


def unsafe_text(*parts: str) -> str:
    return "".join(parts)


def test_builds_phase_one_final_decision_matrix_with_four_outcomes() -> None:
    passed = candidate("pass-alpha")
    watched = candidate(
        "watch-beta",
        gross_edge_bps=d("50.000000"),
        taker_fee_bps=d("5.000000"),
        spread_cost_bps=d("8.000000"),
        slippage_cost_bps=d("7.000000"),
        liquidity_capacity_ratio=d("1.200000"),
        category_budget_remaining_ratio=d("0.120000"),
        team_consensus_score=d("0.800000"),
    )
    manual = candidate(
        "manual-gamma",
        gross_edge_bps=d("85.000000"),
        taker_fee_bps=d("5.000000"),
        spread_cost_bps=d("8.000000"),
        slippage_cost_bps=d("7.000000"),
        evidence_quorum_score=d("0.620000"),
        source_confidence_score=d("0.820000"),
        resolution_risk_score=d("0.160000"),
        category_budget_remaining_ratio=d("0.300000"),
        team_consensus_score=d("0.860000"),
    )
    abstained = candidate(
        "abstain-delta",
        gross_edge_bps=d("10.000000"),
        taker_fee_bps=d("5.000000"),
        spread_cost_bps=d("8.000000"),
        slippage_cost_bps=d("7.000000"),
        evidence_quorum_score=d("0.400000"),
        source_confidence_score=d("0.450000"),
        resolution_risk_score=d("0.750000"),
        liquidity_capacity_ratio=d("0.600000"),
        category_budget_remaining_ratio=d("0.030000"),
        team_consensus_score=d("0.400000"),
    )

    result = report(watched, abstained, manual, passed)
    repeat = report(passed, manual, abstained, watched)

    assert result == repeat
    assert is_dataclass(result)
    assert result.config_version == (
        "strategy-recommendation-final-decision-matrix-v2"
    )
    assert result.candidate_count == d("4")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.abstain_count == d("1")
    assert result.manual_review_count == d("1")
    assert result.top_candidate_id == "pass-alpha"
    assert result.final_decision == "pass"
    assert result.average_decision_score == d("0.721072")
    assert result.max_decision_score == d("0.934286")
    assert result.reason_codes == (
        "final_decision_pass",
        "final_decision_manual_review",
        "final_decision_watch",
        "final_decision_abstain",
        "cost_adjusted_edge_pass",
        "cost_adjusted_edge_watch",
        "cost_adjusted_edge_abstain",
        "evidence_quorum_pass",
        "evidence_quorum_review",
        "evidence_quorum_abstain",
        "source_confidence_pass",
        "source_confidence_abstain",
        "resolution_risk_pass",
        "resolution_risk_abstain",
        "liquidity_capacity_pass",
        "liquidity_capacity_watch",
        "liquidity_capacity_abstain",
        "category_budget_pass",
        "category_budget_watch",
        "category_budget_abstain",
        "team_consensus_pass",
        "team_consensus_abstain",
        "candidates_ranked",
        "seed",
    )
    assert DIGEST_PATTERN.match(result.report_digest)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.candidate_id for row in result.rows) == (
        "pass-alpha",
        "manual-gamma",
        "watch-beta",
        "abstain-delta",
    )
    assert tuple(row.rank for row in result.rows) == (
        d("1"),
        d("2"),
        d("3"),
        d("4"),
    )
    assert tuple(row.final_decision for row in result.rows) == (
        "pass",
        "manual-review",
        "watch",
        "abstain",
    )

    top = result.rows[0]
    assert top.total_cost_bps == d("20.000000")
    assert top.cost_adjusted_edge_bps == d("70.000000")
    assert top.cost_adjusted_edge_score == d("1.000000")
    assert top.resolution_safety_score == d("0.900000")
    assert top.liquidity_capacity_score == d("1.000000")
    assert top.category_budget_score == d("1.000000")
    assert top.decision_score == d("0.934286")
    assert top.reason_codes == (
        "final_decision_pass",
        "cost_adjusted_edge_pass",
        "evidence_quorum_pass",
        "source_confidence_pass",
        "resolution_risk_pass",
        "liquidity_capacity_pass",
        "category_budget_pass",
        "team_consensus_pass",
        "seed",
    )
    assert DIGEST_PATTERN.match(top.decision_digest)

    manual_row = result.rows[1]
    assert manual_row.cost_adjusted_edge_bps == d("65.000000")
    assert manual_row.decision_score == d("0.877143")
    assert manual_row.reason_codes == (
        "final_decision_manual_review",
        "cost_adjusted_edge_pass",
        "evidence_quorum_review",
        "source_confidence_pass",
        "resolution_risk_pass",
        "liquidity_capacity_pass",
        "category_budget_pass",
        "team_consensus_pass",
        "seed",
    )

    watch_row = result.rows[2]
    assert watch_row.cost_adjusted_edge_bps == d("30.000000")
    assert watch_row.cost_adjusted_edge_score == d("0.600000")
    assert watch_row.liquidity_capacity_score == d("0.800000")
    assert watch_row.category_budget_score == d("0.600000")
    assert watch_row.decision_score == d("0.780000")
    assert watch_row.reason_codes == (
        "final_decision_watch",
        "cost_adjusted_edge_watch",
        "evidence_quorum_pass",
        "source_confidence_pass",
        "resolution_risk_pass",
        "liquidity_capacity_watch",
        "category_budget_watch",
        "team_consensus_pass",
        "seed",
    )

    abstain_row = result.rows[3]
    assert abstain_row.cost_adjusted_edge_bps == d("-10.000000")
    assert abstain_row.cost_adjusted_edge_score == d("0.000000")
    assert abstain_row.resolution_safety_score == d("0.250000")
    assert abstain_row.decision_score == d("0.292857")
    assert abstain_row.reason_codes == (
        "final_decision_abstain",
        "cost_adjusted_edge_abstain",
        "evidence_quorum_abstain",
        "source_confidence_abstain",
        "resolution_risk_abstain",
        "liquidity_capacity_abstain",
        "category_budget_abstain",
        "team_consensus_abstain",
        "seed",
    )


def test_payload_serializes_decimal_strings_and_validates_digests() -> None:
    module = api()
    result = report(
        candidate("pass-alpha"),
        candidate(
            "watch-beta",
            gross_edge_bps=d("50.000000"),
            liquidity_capacity_ratio=d("1.200000"),
            category_budget_remaining_ratio=d("0.120000"),
            team_consensus_score=d("0.800000"),
        ),
    )

    payload = module.strategy_recommendation_final_decision_matrix_v2_payload(result)

    assert payload["candidate_count"] == "2"
    assert payload["pass_count"] == "1"
    assert payload["watch_count"] == "1"
    assert payload["average_decision_score"] == "0.857143"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["candidate_id"] == "pass-alpha"
    assert payload["rows"][0]["total_cost_bps"] == "20.000000"
    assert payload["rows"][0]["decision_digest"] == result.rows[0].decision_digest
    assert payload["report_digest"] == result.report_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    with pytest.raises(ValueError, match="decision_digest"):
        replace(result.rows[0], decision_digest="sha256:" + "0" * 64)
    with pytest.raises(ValueError, match="report_digest"):
        replace(result, report_digest="sha256:" + "0" * 64)
    with pytest.raises(ValueError, match="report must be"):
        module.strategy_recommendation_final_decision_matrix_v2_payload(object())


def test_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_STRATEGY_RECOMMENDATION_FINAL_DECISION_MATRIX_V2_CONFIG_VERSION",
        "StrategyRecommendationFinalDecisionMatrixV2Candidate",
        "StrategyRecommendationFinalDecisionMatrixV2Config",
        "StrategyRecommendationFinalDecisionMatrixV2Report",
        "StrategyRecommendationFinalDecisionMatrixV2Row",
        "build_strategy_recommendation_final_decision_matrix_v2_report",
        "strategy_recommendation_final_decision_matrix_v2_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    result = report(
        candidate("pass-alpha"),
        candidate(
            "watch-beta",
            gross_edge_bps=d("50.000000"),
            liquidity_capacity_ratio=d("1.200000"),
            category_budget_remaining_ratio=d("0.120000"),
            team_consensus_score=d("0.800000"),
        ),
    )
    row = result.rows[0]

    with pytest.raises(FrozenInstanceError):
        row.final_decision = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.final_decision = "abstain"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        cfg().minimum_pass_cost_adjusted_edge_bps = d("60.000000")

    for value in (cfg(), candidate(), row, result):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name.endswith(("_bps", "_score", "_ratio", "_count")):
                assert type(item) is Decimal

    with pytest.raises(ValueError, match="gross_edge_bps must be a Decimal"):
        candidate("float-edge", gross_edge_bps=0.90)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="taker_fee_bps must be nonnegative"):
        candidate("negative-cost", taker_fee_bps=d("-0.000001"))
    with pytest.raises(ValueError, match="evidence_quorum_score"):
        candidate("bad-quorum", evidence_quorum_score=d("1.000001"))
    with pytest.raises(ValueError, match="liquidity_capacity_ratio"):
        candidate("bad-capacity", liquidity_capacity_ratio=d("-0.000001"))
    with pytest.raises(ValueError, match="side"):
        candidate("bad-side", side="maybe")
    with pytest.raises(ValueError, match="paper_only"):
        candidate("bad-flag", paper_only=False)
    with pytest.raises(ValueError, match="minimum_watch_evidence_quorum_score"):
        cfg(
            minimum_pass_evidence_quorum_score=d("0.700000"),
            minimum_watch_evidence_quorum_score=d("0.800000"),
        )
    with pytest.raises(ValueError, match="duplicate candidate_id"):
        report(candidate("duplicate"), candidate("duplicate", market_slug="duplicate-b"))
    with pytest.raises(ValueError, match="deterministic sequence"):
        replace(result, rows=tuple(reversed(result.rows)), report_digest=None)
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)


def test_empty_matrix_is_report_only_abstain_with_zero_decimal_rollups() -> None:
    result = report()

    assert result.candidate_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.abstain_count == d("0")
    assert result.manual_review_count == d("0")
    assert result.top_candidate_id is None
    assert result.final_decision == "abstain"
    assert result.average_decision_score == d("0.000000")
    assert result.max_decision_score == d("0.000000")
    assert result.reason_codes == ("no_candidates",)
    assert result.rows == ()
    assert DIGEST_PATTERN.match(result.report_digest)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_module_scope_has_no_external_io_execution_or_live_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    lowered_source = source.lower()
    forbidden_source_fragments = (
        "asyncio",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "subprocess",
        "py_clob_client",
        "web3",
        "private_key",
        "api_key",
        unsafe_text("wal", "let"),
        unsafe_text("net", "work", "_client"),
        unsafe_text("data", "base", "_url"),
        unsafe_text("per", "sist", "_path"),
        "place_" + unsafe_text("or", "der"),
        "create_" + unsafe_text("or", "der"),
        "cancel_" + unsafe_text("or", "der"),
        "submit_" + unsafe_text("or", "der"),
        unsafe_text("li", "ve", "_trading"),
        unsafe_text("tra", "de", "_executor"),
        "open(",
        ".write(",
        ".read(",
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in lowered_source

    forbidden_import_roots = {
        "asyncio",
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
        "sign",
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

    tree = ast.parse(source)
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

    with pytest.raises(ValueError, match="unsafe"):
        candidate("wallet-pressure")
