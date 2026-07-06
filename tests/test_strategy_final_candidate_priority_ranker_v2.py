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


MODULE_NAME = "polymarket_alpha_lab.strategy_final_candidate_priority_ranker_v2"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
EVALUATED_AT = datetime(2026, 7, 6, 11, 45, tzinfo=UTC)


class DerivedDecimal(Decimal):
    pass


def module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    report_module = module()
    values = {
        "max_uncertainty_band_probability": d("0.050000"),
        "max_liquidity_exit_risk_score": d("0.040000"),
        "max_resolution_risk_score": d("0.040000"),
        "min_specialist_signal_confidence": d("0.700000"),
        "min_portfolio_impact_score": d("0.000000"),
    }
    values.update(overrides)
    return report_module.StrategyFinalCandidatePriorityRankerV2Config(**values)


def candidate(**overrides: object) -> Any:
    report_module = module()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "market-alpha",
        "condition_id": "condition-alpha",
        "outcome": "yes",
        "evaluated_at": EVALUATED_AT,
        "source_verified_edge_probability": d("0.090000"),
        "cost_break_even_probability": d("0.020000"),
        "safety_gate_status": "pass",
        "uncertainty_band_probability": d("0.010000"),
        "portfolio_impact_score": d("0.030000"),
        "liquidity_exit_risk_score": d("0.005000"),
        "resolution_risk_score": d("0.005000"),
        "specialist_signal_confidence": d("0.900000"),
        "specialist_signal_count": d("3.000000"),
        "source_config_version": (
            report_module.DEFAULT_STRATEGY_FINAL_CANDIDATE_PRIORITY_RANKER_V2_CONFIG_VERSION
        ),
    }
    values.update(overrides)
    return report_module.StrategyFinalCandidatePriorityRankerV2Candidate(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    report_module = module()
    return report_module.build_strategy_final_candidate_priority_ranker_v2_report(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def test_builds_report_only_priority_report_with_decimal_scores_and_payload() -> None:
    report_module = module()
    report = build_report(
        candidate(
            candidate_id="candidate-watch",
            market_slug="market-watch",
            condition_id="condition-watch",
            safety_gate_status="watch",
            source_verified_edge_probability=d("0.070000"),
            cost_break_even_probability=d("0.020000"),
            uncertainty_band_probability=d("0.008000"),
            portfolio_impact_score=d("0.015000"),
            liquidity_exit_risk_score=d("0.005000"),
            resolution_risk_score=d("0.005000"),
            specialist_signal_confidence=d("0.650000"),
            specialist_signal_count=d("2.000000"),
        ),
        candidate(
            candidate_id="candidate-blocked",
            market_slug="market-blocked",
            condition_id="condition-blocked",
            source_verified_edge_probability=d("0.030000"),
            cost_break_even_probability=d("0.040000"),
            uncertainty_band_probability=d("0.005000"),
            portfolio_impact_score=d("0.010000"),
            liquidity_exit_risk_score=d("0.006000"),
            resolution_risk_score=d("0.006000"),
            specialist_signal_confidence=d("0.800000"),
            specialist_signal_count=d("1.000000"),
        ),
        candidate(
            candidate_id="candidate-beta",
            market_slug="market-beta",
            condition_id="condition-beta",
            source_verified_edge_probability=d("0.080000"),
            cost_break_even_probability=d("0.030000"),
            uncertainty_band_probability=d("0.005000"),
            portfolio_impact_score=d("0.020000"),
            liquidity_exit_risk_score=d("0.002000"),
            resolution_risk_score=d("0.003000"),
            specialist_signal_confidence=d("0.950000"),
            specialist_signal_count=d("4.000000"),
        ),
        candidate(),
    )

    assert report.generated_at == GENERATED_AT
    assert report.candidate_count == d("4.000000")
    assert report.pass_count == d("2.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.top_candidate_id == "candidate-alpha"
    assert report.max_priority_score == d("0.077000")
    assert report.total_priority_score == d("0.158750")
    assert report.ranking_status == "blocked"
    assert report.recommended_next_step == "hold_report_only_priority_review"
    assert report.reason_codes == (
        "edge_below_cost_break_even",
        "safety_gate_watch",
        "specialist_confidence_below_minimum",
    )
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.priority_rank, row.candidate_id, row.ranking_status) for row in report.rows) == (
        (d("1.000000"), "candidate-alpha", "pass"),
        (d("2.000000"), "candidate-beta", "pass"),
        (d("3.000000"), "candidate-watch", "watch"),
        (d("4.000000"), "candidate-blocked", "blocked"),
    )
    assert report.rows[0].edge_after_cost_probability == d("0.070000")
    assert report.rows[0].uncertainty_adjusted_edge_probability == d("0.060000")
    assert report.rows[0].risk_adjusted_edge_probability == d("0.050000")
    assert report.rows[0].priority_score == d("0.077000")
    assert report.rows[1].priority_score == d("0.059000")
    assert report.rows[2].priority_score == d("0.041750")
    assert report.rows[3].priority_score == d("-0.019000")

    payload = report_module.strategy_final_candidate_priority_ranker_v2_public_payload(report)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "4.000000"
    assert payload["max_priority_score"] == "0.077000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["priority_rank"] == "1.000000"
    assert payload["rows"][0]["priority_score"] == "0.077000"
    assert payload["rows"][0]["evaluated_at"] == "2026-07-06T11:45:00+00:00"
    assert report_module.validate_strategy_final_candidate_priority_ranker_v2_public_payload(payload)
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_and_all_pass_inputs_are_deterministic_readonly_reports() -> None:
    empty = build_report()
    assert empty.candidate_count == d("0.000000")
    assert empty.pass_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.blocked_count == d("0.000000")
    assert empty.top_candidate_id is None
    assert empty.max_priority_score == d("0.000000")
    assert empty.total_priority_score == d("0.000000")
    assert empty.ranking_status == "pass"
    assert empty.reason_codes == ("priority_ranker_empty",)
    assert empty.rows == ()

    all_pass = build_report(
        candidate(candidate_id="candidate-beta", market_slug="market-beta", condition_id="condition-beta"),
        candidate(candidate_id="candidate-alpha", market_slug="market-alpha", condition_id="condition-alpha"),
    )

    assert all_pass.candidate_count == d("2.000000")
    assert all_pass.pass_count == d("2.000000")
    assert all_pass.reason_codes == ("priority_ranker_passed",)
    assert tuple(row.candidate_id for row in all_pass.rows) == (
        "candidate-alpha",
        "candidate-beta",
    )


def test_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    report_module = module()

    assert report_module.__all__ == (
        "DEFAULT_STRATEGY_FINAL_CANDIDATE_PRIORITY_RANKER_V2_CONFIG_VERSION",
        "StrategyFinalCandidatePriorityRankerV2Candidate",
        "StrategyFinalCandidatePriorityRankerV2Config",
        "StrategyFinalCandidatePriorityRankerV2Report",
        "StrategyFinalCandidatePriorityRankerV2Row",
        "build_strategy_final_candidate_priority_ranker_v2_report",
        "strategy_final_candidate_priority_ranker_v2_public_payload",
        "validate_strategy_final_candidate_priority_ranker_v2_public_payload",
    )
    for exported_name in report_module.__all__:
        exported = getattr(report_module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    report = build_report(candidate())
    for item in (cfg(), candidate(), report, *report.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            assert type(value) is not int
            if field.name.endswith(("_count", "_score", "_probability", "_rank")):
                assert value is None or type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].priority_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_verified_edge_probability must be a Decimal"):
        candidate(source_verified_edge_probability=DerivedDecimal("0.090000"))
    with pytest.raises(ValueError, match="max_uncertainty_band_probability must be a Decimal"):
        cfg(max_uncertainty_band_probability=DerivedDecimal("0.050000"))

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(report_module.StrategyFinalCandidatePriorityRankerV2Config):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeCandidate(report_module.StrategyFinalCandidatePriorityRankerV2Candidate):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(report_module.StrategyFinalCandidatePriorityRankerV2Row):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(report_module.StrategyFinalCandidatePriorityRankerV2Report):
            pass


def test_validation_rejects_invalid_inputs_flags_duplicates_and_dates() -> None:
    report_module = module()

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report_module.build_strategy_final_candidate_priority_ranker_v2_report(
            (),
            config=cfg(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="evaluated_at must be timezone-aware"):
        candidate(evaluated_at=datetime(2026, 7, 6, 11, 45))
    with pytest.raises(ValueError, match="evaluated_at must not be after generated_at"):
        build_report(candidate(evaluated_at=datetime(2026, 7, 6, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="paper_only must be True"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)
    with pytest.raises(ValueError, match="safety_gate_status"):
        candidate(safety_gate_status="skip")
    with pytest.raises(ValueError, match="candidates"):
        report_module.build_strategy_final_candidate_priority_ranker_v2_report(
            "bad",
            config=cfg(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        report_module.build_strategy_final_candidate_priority_ranker_v2_report(
            (candidate(),),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate"):
        build_report(candidate(), candidate())


def test_report_consistency_and_digest_are_tamper_evident() -> None:
    report_module = module()
    report = build_report(candidate())

    with pytest.raises(ValueError, match="candidate_count"):
        replace(report, candidate_count=d("2.000000"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=(report.rows[0], report.rows[0]))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = report_module.strategy_final_candidate_priority_ranker_v2_public_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["candidate_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_module.validate_strategy_final_candidate_priority_ranker_v2_public_payload(
            tampered_payload,
        )

    object.__setattr__(report.rows[0], "candidate_id", "candidate-mutated")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_module.strategy_final_candidate_priority_ranker_v2_public_payload(report)


def test_unsafe_public_surface_values_and_payload_keys_are_rejected() -> None:
    report_module = module()
    unsafe_terms = (
        "".join(("li", "ve")),
        "".join(("au", "th")),
        "".join(("wall", "et")),
        "".join(("or", "der")),
        "".join(("net", "work")),
        "".join(("data", "base")),
        "".join(("per", "sist")),
        "".join(("sig", "ning")),
        "".join(("mu", "tation")),
        "".join(("bu", "y")),
        "".join(("sel", "l")),
        "".join(("tra", "de")),
    )

    for unsafe_term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            candidate(market_slug=f"market-{unsafe_term}")

    payload = report_module.strategy_final_candidate_priority_ranker_v2_public_payload(
        build_report(candidate()),
    )

    unsafe_payload_key = dict(payload)
    unsafe_payload_key["".join(("wall", "et"))] = "forbidden"
    with pytest.raises(ValueError, match="unsafe public"):
        report_module.validate_strategy_final_candidate_priority_ranker_v2_public_payload(
            unsafe_payload_key,
        )

    unsafe_payload_value = dict(payload)
    unsafe_payload_value["top_candidate_id"] = "candidate-" + "".join(("tra", "de"))
    with pytest.raises(ValueError, match="unsafe public"):
        report_module.validate_strategy_final_candidate_priority_ranker_v2_public_payload(
            unsafe_payload_value,
        )

    numeric_payload = dict(payload)
    numeric_payload["candidate_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        report_module.validate_strategy_final_candidate_priority_ranker_v2_public_payload(
            numeric_payload,
        )


def test_module_omits_runtime_financial_action_and_storage_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_final_candidate_priority_ranker_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "aiohttp",
        "socket",
        "psycopg",
        "sqlalchemy",
        "private_key",
        "account",
        "broker",
        "submit",
        "cancel",
        "authorization",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
            assert type(node.value) is not int
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
            assert node.func.id != "int"


def assert_no_public_numeric(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("float found in public payload")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError("int found in public payload")
    if isinstance(value, Decimal):
        raise AssertionError("Decimal found in public payload")
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_public_numeric(nested)
    elif isinstance(value, list | tuple):
        for nested in value:
            assert_no_public_numeric(nested)
