from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_time_to_resolution_edge_decay_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "candidate_id": "candidate-time-decay-v2",
        "current_edge_bps": d("120.000000"),
        "hours_to_close": d("18.000000"),
        "source_freshness_decay_ratio": d("0.500000"),
        "settlement_lag_hours": d("36.000000"),
        "liquidity_exit_friction_bps": d("40.000000"),
        "probability_movement_velocity_bps_per_hour": d("2.000000"),
        "uncertainty_ratio": d("0.400000"),
        "minimum_actionable_score": d("50.000000"),
        "reason_codes": ("research_signal_present",),
    }
    values.update(overrides)
    return module.StrategyCandidateTimeToResolutionEdgeDecayV2Input(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_strategy_candidate_time_to_resolution_edge_decay_v2(
        score_input() if subject is None else subject,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_time_to_resolution_edge_decay_penalizes_all_phase_1_inputs() -> None:
    module = api()

    result = score()

    assert result == module.StrategyCandidateTimeToResolutionEdgeDecayV2Result(
        candidate_id="candidate-time-decay-v2",
        current_edge_bps=d("120.000000"),
        hours_to_close=d("18.000000"),
        close_proximity_ratio=d("0.750000"),
        close_proximity_decay_bps=d("22.500000"),
        source_freshness_decay_ratio=d("0.500000"),
        source_freshness_decay_bps=d("18.000000"),
        settlement_lag_hours=d("36.000000"),
        settlement_lag_ratio=d("0.500000"),
        settlement_lag_decay_bps=d("6.000000"),
        liquidity_exit_friction_bps=d("40.000000"),
        probability_movement_velocity_bps_per_hour=d("2.000000"),
        velocity_projection_hours=d("18.000000"),
        probability_velocity_decay_bps=d("36.000000"),
        uncertainty_ratio=d("0.400000"),
        uncertainty_decay_bps=d("9.600000"),
        expected_edge_decay_bps=d("132.100000"),
        expected_edge_decay_ratio=d("1.100833"),
        paper_score_bps=d("-12.100000"),
        minimum_actionable_score=d("50.000000"),
        edge_decay_rank="high",
        score_status="blocked",
        score_decision="reject",
        reason_codes=(
            "research_signal_present",
            "strategy_candidate_time_to_resolution_edge_decay_v2",
            "score_blocked",
            "edge_decay_high",
            "edge_positive",
            "close_proximity_decay_applied",
            "source_freshness_decay_applied",
            "settlement_lag_decay_applied",
            "liquidity_exit_friction_applied",
            "probability_velocity_decay_applied",
            "uncertainty_decay_applied",
            "score_below_zero",
        ),
        derived_validation_digest=(
            "e7d8baff6ae4b7cc5a329066059256a1a2e57af95bfe3de12224775f042c4303"
        ),
    )
    assert type(result.paper_score_bps) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_candidate_when_decay_adjusted_edge_clears_threshold() -> None:
    result = score(
        score_input(
            current_edge_bps=d("240.000000"),
            hours_to_close=d("96.000000"),
            source_freshness_decay_ratio=d("0.000000"),
            settlement_lag_hours=d("0.000000"),
            liquidity_exit_friction_bps=d("5.000000"),
            probability_movement_velocity_bps_per_hour=d("0.250000"),
            uncertainty_ratio=d("0.000000"),
            minimum_actionable_score=d("100.000000"),
            reason_codes=(),
        ),
    )

    assert result.close_proximity_ratio == d("0.000000")
    assert result.close_proximity_decay_bps == d("0.000000")
    assert result.velocity_projection_hours == d("24.000000")
    assert result.probability_velocity_decay_bps == d("6.000000")
    assert result.expected_edge_decay_bps == d("11.000000")
    assert result.expected_edge_decay_ratio == d("0.045833")
    assert result.paper_score_bps == d("229.000000")
    assert result.edge_decay_rank == "low"
    assert result.score_status == "candidate"
    assert result.score_decision == "paper_candidate"
    assert result.reason_codes == (
        "strategy_candidate_time_to_resolution_edge_decay_v2",
        "score_candidate",
        "edge_decay_low",
        "edge_positive",
        "liquidity_exit_friction_applied",
        "probability_velocity_decay_applied",
        "minimum_actionable_score_met",
    )


def test_watch_when_score_is_positive_but_below_threshold() -> None:
    result = score(
        score_input(
            current_edge_bps=d("100.000000"),
            hours_to_close=d("36.000000"),
            source_freshness_decay_ratio=d("0.100000"),
            settlement_lag_hours=d("0.000000"),
            liquidity_exit_friction_bps=d("10.000000"),
            probability_movement_velocity_bps_per_hour=d("0.500000"),
            uncertainty_ratio=d("0.100000"),
            minimum_actionable_score=d("80.000000"),
            reason_codes=(),
        ),
    )

    assert result.close_proximity_ratio == d("0.500000")
    assert result.close_proximity_decay_bps == d("12.500000")
    assert result.source_freshness_decay_bps == d("3.000000")
    assert result.settlement_lag_decay_bps == d("0.000000")
    assert result.expected_edge_decay_bps == d("39.500000")
    assert result.expected_edge_decay_ratio == d("0.395000")
    assert result.paper_score_bps == d("60.500000")
    assert result.edge_decay_rank == "moderate"
    assert result.score_status == "watch"
    assert result.score_decision == "manual_review"
    assert "score_positive_below_minimum" in result.reason_codes


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    result = score()
    payload = result.payload

    assert payload == module.strategy_candidate_time_to_resolution_edge_decay_v2_payload(
        result,
    )
    assert payload["paper_score_bps"] == "-12.100000"
    assert payload["expected_edge_decay_ratio"] == "1.100833"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_time_to_resolution_edge_decay_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_ranked_and_hard_flagged() -> None:
    module = api()
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.StrategyCandidateTimeToResolutionEdgeDecayV2Input.__dataclass_params__.frozen
    assert module.StrategyCandidateTimeToResolutionEdgeDecayV2Result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.candidate_id = "other-candidate"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.edge_decay_rank = "low"  # type: ignore[misc]

    for instance in (subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="current_edge_bps must be a Decimal"):
        score_input(current_edge_bps=120)
    with pytest.raises(ValueError, match="candidate_id must be a canonical"):
        score_input(candidate_id=" candidate-time-decay-v2")
    with pytest.raises(ValueError, match="hours_to_close must be nonnegative"):
        score_input(hours_to_close=d("-0.000001"))
    with pytest.raises(ValueError, match="source_freshness_decay_ratio must be between"):
        score_input(source_freshness_decay_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["research_signal_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())

    rebuilt = module.StrategyCandidateTimeToResolutionEdgeDecayV2Result(
        **public_field_values(result),
    )
    assert rebuilt == result


def test_rejects_digest_tampering_and_unsafe_public_payload_keys_and_values() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.StrategyCandidateTimeToResolutionEdgeDecayV2Result(
            **{
                **public_field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )

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
        with pytest.raises(ValueError, match="unsafe"):
            score_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_time_to_resolution_edge_decay_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_time_to_resolution_edge_decay_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/strategy_candidate_time_to_resolution_edge_decay_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    unsafe_surface_terms = (
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "wallet",
        " auth",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_surface_terms:
        assert term not in lowered

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
    assert module.__all__ == (
        "SCORE_STATUSES",
        "SCORE_DECISIONS",
        "EDGE_DECAY_RANKS",
        "StrategyCandidateTimeToResolutionEdgeDecayV2Input",
        "StrategyCandidateTimeToResolutionEdgeDecayV2Result",
        "estimate_strategy_candidate_time_to_resolution_edge_decay_v2",
        "strategy_candidate_time_to_resolution_edge_decay_v2_payload",
        "reject_strategy_candidate_time_to_resolution_edge_decay_v2_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "strategy_candidate_time_to_resolution_edge_decay_v2" not in getattr(
        root,
        "__all__",
        (),
    )
