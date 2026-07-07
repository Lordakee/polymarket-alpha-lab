from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal

import pytest

from polymarket_alpha_lab import strategy_market_candidate_triage_v2 as triage_module
from polymarket_alpha_lab.strategy_market_candidate_triage_v2 import (
    StrategyMarketCandidateTriageV2Candidate,
    StrategyMarketCandidateTriageV2Config,
    StrategyMarketCandidateTriageV2Report,
    StrategyMarketCandidateTriageV2Row,
    build_strategy_market_candidate_triage_v2_report,
    strategy_market_candidate_triage_v2_payload,
    triage_strategy_market_candidate_v2,
    validate_strategy_market_candidate_triage_v2_public_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(**overrides: object) -> StrategyMarketCandidateTriageV2Candidate:
    values = {
        "market_id": "market-alpha",
        "category": "Macro policy",
        "model_probability": d("0.650000"),
        "market_probability": d("0.550000"),
        "estimated_cost_probability": d("0.020000"),
        "evidence_quality_score": d("0.820000"),
        "specialist_approval_count": d("2.000000"),
        "specialist_review_count": d("3.000000"),
        "liquidity_exit_feasibility_score": d("0.800000"),
        "resolution_risk_score": d("0.200000"),
        "category_exposure_score": d("0.200000"),
    }
    values.update(overrides)
    return StrategyMarketCandidateTriageV2Candidate(**values)


def report(
    *rows: StrategyMarketCandidateTriageV2Candidate,
    config: StrategyMarketCandidateTriageV2Config | None = None,
) -> StrategyMarketCandidateTriageV2Report:
    return build_strategy_market_candidate_triage_v2_report(
        rows or (candidate(),),
        config=config,
    )


def test_promote_candidate_returns_decimal_stringed_digest_bound_payload() -> None:
    triage = report()
    row = triage.rows[0]

    assert is_dataclass(triage)
    assert row.triage_bucket == "promote"
    assert row.recommended_next_step == "promote_to_phase_1_packet"
    assert row.reason_codes == ("candidate_promote_clear",)
    assert row.blocking_reasons == ()
    assert row.cost_break_even_probability == d("0.570000")
    assert row.cost_adjusted_edge == d("0.080000")
    assert row.specialist_quorum_ratio == d("0.666667")
    assert triage.candidate_count == d("1.000000")
    assert triage.promote_count == d("1.000000")
    assert triage.watch_count == d("0.000000")
    assert triage.block_count == d("0.000000")
    assert triage.research_needed_count == d("0.000000")
    assert len(row.derived_validation_digest) == 64
    assert len(triage.derived_validation_digest) == 64
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert triage.paper_only is True
    assert triage.report_only is True
    assert triage.readonly is True

    payload = strategy_market_candidate_triage_v2_payload(triage)
    assert payload["candidate_count"] == "1.000000"
    assert payload["promote_count"] == "1.000000"
    assert payload["derived_validation_digest"] == triage.derived_validation_digest
    assert payload["rows"][0]["cost_break_even_probability"] == "0.570000"
    assert payload["rows"][0]["cost_adjusted_edge"] == "0.080000"
    assert payload["rows"][0]["specialist_quorum_ratio"] == "0.666667"
    assert payload["rows"][0]["derived_validation_digest"] == row.derived_validation_digest
    validate_strategy_market_candidate_triage_v2_public_payload(payload)
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)


def test_watch_candidate_keeps_candidate_for_refresh_without_blocking() -> None:
    triage = report(
        candidate(
            market_id="market-watch",
            model_probability=d("0.600000"),
            market_probability=d("0.550000"),
            estimated_cost_probability=d("0.020000"),
            resolution_risk_score=d("0.400000"),
            category_exposure_score=d("0.400000"),
        ),
    )
    row = triage.rows[0]

    assert row.triage_bucket == "watch"
    assert row.recommended_next_step == "keep_on_watchlist"
    assert row.blocking_reasons == ()
    assert row.cost_adjusted_edge == d("0.030000")
    assert row.reason_codes == (
        "candidate_cost_adjusted_edge_below_promote",
        "candidate_resolution_risk_above_promote",
        "candidate_category_exposure_above_promote",
    )
    assert triage.watch_count == d("1.000000")


def test_research_needed_candidate_uses_evidence_quality_and_specialist_quorum() -> None:
    triage = report(
        candidate(
            market_id="market-research",
            evidence_quality_score=d("0.400000"),
            specialist_approval_count=d("1.000000"),
            specialist_review_count=d("1.000000"),
        ),
    )
    row = triage.rows[0]

    assert row.triage_bucket == "research-needed"
    assert row.recommended_next_step == "collect_more_public_evidence"
    assert row.blocking_reasons == ()
    assert row.specialist_quorum_ratio == d("1.000000")
    assert row.reason_codes == (
        "candidate_evidence_quality_below_floor_research_needed",
        "candidate_specialist_review_count_below_quorum_research_needed",
    )
    assert triage.research_needed_count == d("1.000000")


def test_block_candidate_reports_cost_liquidity_resolution_and_exposure_blockers() -> None:
    triage = report(
        candidate(
            market_id="market-block",
            model_probability=d("0.450000"),
            market_probability=d("0.940000"),
            estimated_cost_probability=d("0.020000"),
            liquidity_exit_feasibility_score=d("0.200000"),
            resolution_risk_score=d("0.700000"),
            category_exposure_score=d("0.700000"),
        ),
    )
    row = triage.rows[0]

    assert row.triage_bucket == "block"
    assert row.recommended_next_step == "block_until_constraints_clear"
    assert row.cost_break_even_probability == d("0.960000")
    assert row.cost_adjusted_edge == d("-0.510000")
    assert row.blocking_reasons == (
        "cost_adjusted_edge_negative",
        "cost_break_even_above_limit",
        "liquidity_exit_feasibility_below_floor",
        "resolution_risk_above_limit",
        "category_exposure_above_limit",
    )
    assert row.reason_codes == (
        "candidate_cost_adjusted_edge_negative_block",
        "candidate_cost_break_even_above_limit_block",
        "candidate_liquidity_exit_feasibility_below_floor_block",
        "candidate_resolution_risk_above_limit_block",
        "candidate_category_exposure_above_limit_block",
    )
    assert triage.block_count == d("1.000000")


def test_direct_function_returns_readonly_single_candidate_report() -> None:
    triage = triage_strategy_market_candidate_v2(
        market_id="market-direct",
        category="Sports",
        model_probability=d("0.630000"),
        market_probability=d("0.560000"),
        estimated_cost_probability=d("0.020000"),
        evidence_quality_score=d("0.800000"),
        specialist_approval_count=d("3.000000"),
        specialist_review_count=d("3.000000"),
        liquidity_exit_feasibility_score=d("0.780000"),
        resolution_risk_score=d("0.300000"),
        category_exposure_score=d("0.250000"),
    )

    assert triage.rows[0].triage_bucket == "promote"
    assert triage.rows[0].market_id == "market-direct"
    assert triage.rows[0].cost_adjusted_edge == d("0.050000")


def test_dataclasses_are_frozen_and_numeric_fields_are_decimal_only() -> None:
    triage = report()

    for dataclass_type in (
        StrategyMarketCandidateTriageV2Config,
        StrategyMarketCandidateTriageV2Candidate,
        StrategyMarketCandidateTriageV2Row,
        StrategyMarketCandidateTriageV2Report,
    ):
        assert is_dataclass(dataclass_type)

    with pytest.raises(FrozenInstanceError):
        triage.promote_count = d("0.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        triage.rows[0].cost_adjusted_edge = d("0.000000")  # type: ignore[misc]

    decimal_fields_by_object = (
        (
            triage,
            (
                "candidate_count",
                "promote_count",
                "watch_count",
                "block_count",
                "research_needed_count",
            ),
        ),
        (
            triage.rows[0],
            (
                "model_probability",
                "market_probability",
                "estimated_cost_probability",
                "cost_break_even_probability",
                "cost_adjusted_edge",
                "evidence_quality_score",
                "specialist_approval_count",
                "specialist_review_count",
                "specialist_quorum_ratio",
                "liquidity_exit_feasibility_score",
                "resolution_risk_score",
                "category_exposure_score",
            ),
        ),
    )
    for item, field_names in decimal_fields_by_object:
        for field_name in field_names:
            assert type(getattr(item, field_name)) is Decimal
        for field_name, value in item.__dict__.items():
            assert type(value) not in (int, float), field_name

    with pytest.raises(ValueError, match="model_probability"):
        candidate(model_probability=0.6)
    with pytest.raises(ValueError, match="market_probability"):
        candidate(market_probability=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="specialist_review_count"):
        candidate(specialist_review_count=d("2.500000"))
    with pytest.raises(ValueError, match="approval"):
        candidate(
            specialist_approval_count=d("3.000000"),
            specialist_review_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)


def test_derived_validation_digest_rejects_dataclass_and_public_payload_tampering() -> None:
    triage = report()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(triage, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(triage.rows[0], derived_validation_digest="0" * 64)

    tampered_report = report()
    object.__setattr__(tampered_report, "promote_count", d("0.000000"))
    with pytest.raises(ValueError, match="promote_count|derived_validation_digest"):
        strategy_market_candidate_triage_v2_payload(tampered_report)

    tampered_row_report = report()
    object.__setattr__(tampered_row_report.rows[0], "cost_adjusted_edge", d("0.000000"))
    with pytest.raises(ValueError, match="cost_adjusted_edge|derived_validation_digest"):
        strategy_market_candidate_triage_v2_payload(tampered_row_report)

    payload = strategy_market_candidate_triage_v2_payload(triage)
    tampered_payload = dict(payload)
    tampered_payload["candidate_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_market_candidate_triage_v2_payload(tampered_payload)

    tampered_row_payload = dict(payload)
    tampered_row_payload["rows"] = [dict(payload["rows"][0])]
    tampered_row_payload["rows"][0]["cost_adjusted_edge"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_market_candidate_triage_v2_payload(tampered_row_payload)


def test_public_surface_rejects_unsafe_keys_and_values() -> None:
    for unsafe_value in (
        "live market",
        "auth clue",
        "wallet clue",
        "order clue",
        "network clue",
        "database clue",
        "persist clue",
        "signing clue",
        "mutation clue",
        "buy clue",
        "sell clue",
        "trade clue",
    ):
        with pytest.raises(ValueError, match="unsafe public surface text"):
            candidate(category=unsafe_value)

    payload = strategy_market_candidate_triage_v2_payload(report())
    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wallet_hint"] = True
    with pytest.raises(ValueError, match="unsafe public surface text"):
        strategy_market_candidate_triage_v2_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_value_payload["rows"][0]["category"] = "sell clue"
    with pytest.raises(ValueError, match="unsafe public surface text"):
        strategy_market_candidate_triage_v2_payload(unsafe_value_payload)

    unsafe_numeric_payload = dict(payload)
    unsafe_numeric_payload["candidate_count"] = 1
    with pytest.raises(ValueError, match="Decimal strings"):
        strategy_market_candidate_triage_v2_payload(unsafe_numeric_payload)


def test_module_exposes_no_side_effect_import_or_callable_surface() -> None:
    source = inspect.getsource(triage_module)
    tree = ast.parse(source)
    forbidden_imports = {
        "aiohttp",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "urllib",
        "web3",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            assert "buy" not in node.name
            assert "sell" not in node.name
            assert "trade" not in node.name
    assert imported_roots.isdisjoint(forbidden_imports)


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False
