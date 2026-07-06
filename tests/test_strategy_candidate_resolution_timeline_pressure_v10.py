from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.strategy_candidate_resolution_timeline_pressure_v10",
    )


def pressure_input(**overrides: Any):
    values: dict[str, Any] = {
        "candidate_id": "candidate-alpha",
        "market_slug": "market-alpha",
        "outcome_name": "Yes",
        "time_to_resolution_minutes": d("1440.000000"),
        "source_update_cadence_minutes": d("0.000000"),
        "pending_resolution_dependencies": d("0.000000"),
        "market_move_since_last_research": d("0.000000"),
        "review_queue_age_minutes": d("0.000000"),
    }
    values.update(overrides)
    return api().StrategyCandidateResolutionTimelinePressureV10Input(**values)


def build(subject: object | None = None):
    return api().build_strategy_candidate_resolution_timeline_pressure_v10(
        pressure_input() if subject is None else subject,
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


def test_normal_pressure_candidate_uses_readonly_payload_defaults() -> None:
    module = api()

    result = build()

    assert result == module.StrategyCandidateResolutionTimelinePressureV10Result(
        candidate_id="candidate-alpha",
        market_slug="market-alpha",
        outcome_name="Yes",
        time_to_resolution_minutes=d("1440.000000"),
        source_update_cadence_minutes=d("0.000000"),
        pending_resolution_dependencies=d("0.000000"),
        market_move_since_last_research=d("0.000000"),
        review_queue_age_minutes=d("0.000000"),
        resolution_time_pressure=d("0.000000"),
        source_cadence_pressure=d("0.000000"),
        dependency_pressure=d("0.000000"),
        market_move_pressure=d("0.000000"),
        review_queue_pressure=d("0.000000"),
        pressure_score=d("0.000000"),
        pressure_status="normal",
        review_action="normal_queue",
        recommended_review_minutes=d("720.000000"),
        reason_codes=(
            "pressure_status_normal",
            "resolution_window_sufficient",
            "source_cadence_fresh",
            "dependencies_clear",
            "market_move_stable",
            "review_queue_fresh",
        ),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.payload
    assert payload == module.strategy_candidate_resolution_timeline_pressure_v10_payload(
        result,
    )
    assert payload["pressure_score"] == "0.000000"
    assert payload["review_action"] == "normal_queue"
    assert payload["recommended_review_minutes"] == "720.000000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_critical_pressure_captures_timeline_dependencies_move_and_queue_age() -> None:
    result = build(
        pressure_input(
            candidate_id="candidate-critical",
            time_to_resolution_minutes=d("30.000000"),
            source_update_cadence_minutes=d("60.000000"),
            pending_resolution_dependencies=d("5.000000"),
            market_move_since_last_research=d("-0.150000"),
            review_queue_age_minutes=d("720.000000"),
        ),
    )

    assert result.resolution_time_pressure == d("1.000000")
    assert result.source_cadence_pressure == d("1.000000")
    assert result.dependency_pressure == d("1.000000")
    assert result.market_move_pressure == d("1.000000")
    assert result.review_queue_pressure == d("1.000000")
    assert result.pressure_score == d("1.000000")
    assert result.pressure_status == "critical"
    assert result.review_action == "review_now"
    assert result.recommended_review_minutes == d("15.000000")
    assert result.reason_codes == (
        "pressure_status_critical",
        "resolution_window_urgent",
        "source_cadence_misses_resolution",
        "dependencies_heavy",
        "market_move_large",
        "review_queue_stale",
    )


def test_watch_pressure_scores_independent_non_resolution_factors() -> None:
    result = build(
        pressure_input(
            time_to_resolution_minutes=d("1440.000000"),
            source_update_cadence_minutes=d("720.000000"),
            pending_resolution_dependencies=d("2.000000"),
            market_move_since_last_research=d("0.075000"),
            review_queue_age_minutes=d("360.000000"),
        ),
    )

    assert result.resolution_time_pressure == d("0.000000")
    assert result.source_cadence_pressure == d("0.500000")
    assert result.dependency_pressure == d("0.400000")
    assert result.market_move_pressure == d("0.500000")
    assert result.review_queue_pressure == d("0.500000")
    assert result.pressure_score == d("0.330000")
    assert result.pressure_status == "watch"
    assert result.review_action == "monitor_queue"
    assert result.recommended_review_minutes == d("240.000000")
    assert result.reason_codes == (
        "pressure_status_watch",
        "resolution_window_sufficient",
        "source_cadence_slow",
        "dependencies_pending",
        "market_move_observed",
        "review_queue_aged",
    )


def test_validation_rejects_wrong_types_subclasses_bad_flags_and_mismatched_results() -> None:
    module = api()
    subject = pressure_input()
    result = build(subject)

    class InputSubclass(module.StrategyCandidateResolutionTimelinePressureV10Input):
        pass

    with pytest.raises(FrozenInstanceError):
        subject.candidate_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.pressure_status = "critical"  # type: ignore[misc]

    with pytest.raises(ValueError, match="time_to_resolution_minutes must be a Decimal"):
        pressure_input(time_to_resolution_minutes=1440)
    with pytest.raises(ValueError, match="source_update_cadence_minutes must be a Decimal"):
        pressure_input(source_update_cadence_minutes="60.000000")
    with pytest.raises(ValueError, match="pending_resolution_dependencies must be a whole"):
        pressure_input(pending_resolution_dependencies=d("1.500000"))
    with pytest.raises(ValueError, match="market_move_since_last_research must be between"):
        pressure_input(market_move_since_last_research=d("1.000001"))
    with pytest.raises(ValueError, match="review_queue_age_minutes must be nonnegative"):
        pressure_input(review_queue_age_minutes=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        pressure_input(paper_only=False)
    with pytest.raises(ValueError, match="candidate must be"):
        build(object())
    with pytest.raises(ValueError, match="candidate must be"):
        build(InputSubclass(**subject.__dict__))
    with pytest.raises(ValueError, match="pressure_score must match"):
        replace(
            build(
                pressure_input(
                    time_to_resolution_minutes=d("30.000000"),
                    source_update_cadence_minutes=d("60.000000"),
                    pending_resolution_dependencies=d("5.000000"),
                    market_move_since_last_research=d("0.150000"),
                    review_queue_age_minutes=d("720.000000"),
                ),
            ),
            pressure_score=d("0.990000"),
        )
    with pytest.raises(ValueError, match="result must be"):
        module.strategy_candidate_resolution_timeline_pressure_v10_payload(object())


def test_module_is_pure_readonly_decimal_only_and_unwired_from_execution_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    lowered = source.lower()

    assert module.StrategyCandidateResolutionTimelinePressureV10Input.__dataclass_params__.frozen
    assert module.StrategyCandidateResolutionTimelinePressureV10Result.__dataclass_params__.frozen
    assert module.__all__ == (
        "PRESSURE_STATUSES",
        "REVIEW_ACTIONS",
        "REASON_CODES",
        "StrategyCandidateResolutionTimelinePressureV10Input",
        "StrategyCandidateResolutionTimelinePressureV10Result",
        "build_strategy_candidate_resolution_timeline_pressure_v10",
        "strategy_candidate_resolution_timeline_pressure_v10_payload",
    )

    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "clob",
        "wallet",
        "private_key",
        "signing",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    assert all(fragment not in source for fragment in forbidden_fragments)
    assert "database" not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
