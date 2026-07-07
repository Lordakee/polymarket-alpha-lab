from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import strategy_candidate_recommendation_trace_v2 as module
from polymarket_alpha_lab.strategy_candidate_recommendation_trace_v2 import (
    StrategyCandidateRecommendationTraceV2Candidate,
    StrategyCandidateRecommendationTraceV2Config,
    StrategyCandidateRecommendationTraceV2Report,
    StrategyCandidateRecommendationTraceV2Row,
    build_strategy_candidate_recommendation_trace_v2_report,
    strategy_candidate_recommendation_trace_v2_payload,
    validate_strategy_candidate_recommendation_trace_v2_public_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyCandidateRecommendationTraceV2Config:
    values = {
        "config_version": "strategy-candidate-recommendation-trace-v2-test",
        "min_promote_edge_after_break_even": d("0.030000"),
        "min_watch_edge_after_break_even": d("0.000000"),
        "min_promote_source_quality_score": d("0.800000"),
        "min_watch_source_quality_score": d("0.600000"),
        "min_promote_specialist_arbitration_score": d("0.750000"),
        "min_watch_specialist_arbitration_score": d("0.550000"),
        "max_promote_resolution_risk_score": d("0.250000"),
        "max_watch_resolution_risk_score": d("0.500000"),
        "min_promote_liquidity_exit_feasibility_score": d("0.700000"),
        "min_watch_liquidity_exit_feasibility_score": d("0.450000"),
        "max_promote_category_exposure_ratio": d("0.250000"),
        "max_watch_category_exposure_ratio": d("0.400000"),
    }
    values.update(overrides)
    return StrategyCandidateRecommendationTraceV2Config(**values)


def candidate(**overrides: object) -> StrategyCandidateRecommendationTraceV2Candidate:
    values = {
        "candidate_id": "candidate-promote",
        "market_slug": "fed-rate-path",
        "question": "Will the policy rate be above the target level?",
        "category": "macro",
        "side": "yes",
        "observed_at": module.datetime(2026, 7, 6, 11, 50, tzinfo=module.UTC),
        "forecast_probability": d("0.650000"),
        "market_probability": d("0.550000"),
        "fee_probability_cost": d("0.005000"),
        "spread_probability_cost": d("0.010000"),
        "slippage_probability_cost": d("0.005000"),
        "settlement_probability_cost": d("0.000000"),
        "source_quality_score": d("0.900000"),
        "specialist_arbitration_score": d("0.850000"),
        "resolution_risk_score": d("0.100000"),
        "liquidity_exit_feasibility_score": d("0.850000"),
        "category_exposure_ratio": d("0.100000"),
        "reason_codes": ("screened_candidate",),
    }
    values.update(overrides)
    return StrategyCandidateRecommendationTraceV2Candidate(**values)


def generated_at() -> module.datetime:
    return module.datetime(2026, 7, 6, 12, 0, tzinfo=module.UTC)


def report(
    *candidates: StrategyCandidateRecommendationTraceV2Candidate,
) -> StrategyCandidateRecommendationTraceV2Report:
    return build_strategy_candidate_recommendation_trace_v2_report(
        candidates or (candidate(),),
        config=config(),
        generated_at=generated_at(),
    )


def assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) in (float, int, Decimal):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_scalars(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numeric_scalars(item)


def test_report_combines_all_trace_dimensions_into_statuses() -> None:
    promoted = candidate(candidate_id="candidate-promote")
    watched = candidate(
        candidate_id="candidate-watch",
        market_slug="inflation-print",
        source_quality_score=d("0.700000"),
    )
    blocked = candidate(
        candidate_id="candidate-block",
        market_slug="weather-index",
        forecast_probability=d("0.520000"),
        market_probability=d("0.510000"),
    )

    result = report(promoted, watched, blocked)

    assert result.candidate_count == d("3.000000")
    assert result.row_count == d("3.000000")
    assert result.promoted_count == d("1.000000")
    assert result.watched_count == d("1.000000")
    assert result.blocked_count == d("1.000000")
    assert result.report_status == "blocked"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    rows_by_id = {row.candidate_id: row for row in result.rows}
    promoted_row = rows_by_id["candidate-promote"]
    watched_row = rows_by_id["candidate-watch"]
    blocked_row = rows_by_id["candidate-block"]

    assert promoted_row.recommendation_status == "promoted"
    assert promoted_row.gross_probability_edge == d("0.100000")
    assert promoted_row.total_break_even_cost_probability == d("0.020000")
    assert promoted_row.break_even_probability == d("0.570000")
    assert promoted_row.edge_after_break_even == d("0.080000")
    assert promoted_row.reason_codes[:8] == (
        "candidate_recommendation_trace_promoted",
        "forecast_edge_promote",
        "cost_break_even_met",
        "source_quality_promote",
        "specialist_arbitration_promote",
        "resolution_risk_promote",
        "liquidity_exit_feasible",
        "category_exposure_promote",
    )
    assert watched_row.recommendation_status == "watched"
    assert "source_quality_watch" in watched_row.reason_codes
    assert watched_row.watch_floor_margin >= d("0.000000")
    assert watched_row.promotion_margin < d("0.000000")
    assert blocked_row.recommendation_status == "blocked"
    assert "forecast_edge_below_watch_floor" in blocked_row.reason_codes
    assert "cost_break_even_not_met" in blocked_row.reason_codes
    assert blocked_row.watch_floor_margin < d("0.000000")


def test_payload_serializes_decimal_strings_flags_and_digests() -> None:
    result = report(candidate())

    payload = strategy_candidate_recommendation_trace_v2_payload(result)

    assert payload["candidate_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    row = payload["rows"][0]
    assert row["forecast_probability"] == "0.650000"
    assert row["edge_after_break_even"] == "0.080000"
    assert row["paper_only"] is True
    assert row["report_only"] is True
    assert row["readonly"] is True
    assert len(row["derived_validation_digest"]) == 64
    assert_no_public_numeric_scalars(payload)
    assert validate_strategy_candidate_recommendation_trace_v2_public_payload(payload)
    assert strategy_candidate_recommendation_trace_v2_payload(payload) == payload


def test_derived_validation_digest_rejects_dataclass_and_payload_tampering() -> None:
    result = report(candidate())
    row = result.rows[0]

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, forecast_probability=d("0.660000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, promoted_count=d("2.000000"))

    payload = strategy_candidate_recommendation_trace_v2_payload(result)
    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_candidate_recommendation_trace_v2_payload(missing_digest)

    tampered_report = dict(payload)
    tampered_report["promoted_count"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_candidate_recommendation_trace_v2_payload(tampered_report)

    tampered_row = dict(payload)
    tampered_row["rows"] = [dict(payload["rows"][0])]
    tampered_row["rows"][0]["recommendation_status"] = "blocked"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_candidate_recommendation_trace_v2_payload(tampered_row)


def test_public_payload_rejects_unsafe_public_keys_and_values() -> None:
    payload = strategy_candidate_recommendation_trace_v2_payload(report(candidate()))

    unsafe_terms = (
        "live",
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
    )
    for term in unsafe_terms:
        unsafe_key_payload = dict(payload)
        unsafe_key_payload[f"{term}_field"] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            strategy_candidate_recommendation_trace_v2_payload(unsafe_key_payload)

        unsafe_value_payload = dict(payload)
        unsafe_value_payload["market_slug"] = f"{term} reference"
        with pytest.raises(ValueError, match="unsafe"):
            strategy_candidate_recommendation_trace_v2_payload(unsafe_value_payload)


def test_dataclasses_are_frozen_decimal_only_exact_typed_and_hard_flagged() -> None:
    cfg = config()
    source = candidate()
    result = report(source)

    with pytest.raises(FrozenInstanceError):
        result.report_status = "promoted"  # type: ignore[misc]
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        replace(source, forecast_probability=0.65)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="candidate_count must be a Decimal"):
        replace(result, candidate_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(cfg, paper_only=False)
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        candidate(observed_at=module.datetime(2026, 7, 6, 11, 50))
    with pytest.raises(ValueError, match="config"):
        build_strategy_candidate_recommendation_trace_v2_report(
            (source,),
            config=object(),  # type: ignore[arg-type]
            generated_at=generated_at(),
        )
    with pytest.raises(ValueError, match="candidate"):
        build_strategy_candidate_recommendation_trace_v2_report(
            (object(),),  # type: ignore[arg-type]
            config=config(),
            generated_at=generated_at(),
        )


def test_public_dataclasses_reject_subclassing() -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):

        class ConfigSubclass(StrategyCandidateRecommendationTraceV2Config):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class CandidateSubclass(StrategyCandidateRecommendationTraceV2Candidate):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class RowSubclass(StrategyCandidateRecommendationTraceV2Row):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class ReportSubclass(StrategyCandidateRecommendationTraceV2Report):
            pass


def test_module_is_pure_report_only_without_external_side_effect_surface() -> None:
    source = inspect.getsource(module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "http",
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
    }
    forbidden_attr_fragments = (
        "broker",
        "credential",
        "private_key",
        "secret",
        "token",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            if isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
        if isinstance(node, ast.Attribute):
            attr = node.attr.lower()
            assert not any(fragment in attr for fragment in forbidden_attr_fragments)
