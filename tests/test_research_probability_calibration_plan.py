from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_probability_calibration_plan",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def calibration_case(
    case_sequence: str,
    forecast_probability: str,
    observed_frequency: str,
    *,
    observation_count: str = "40",
    evidence_confidence_score: str = "0.800000",
):
    module = api()
    return module.ResearchProbabilityCalibrationCaseInput(
        case_sequence=d(case_sequence),
        forecast_probability=d(forecast_probability),
        observed_frequency=d(observed_frequency),
        observation_count=d(observation_count),
        evidence_confidence_score=d(evidence_confidence_score),
        reason_codes=("research_probability_calibration_plan_input",),
    )


def build_plan(*rows, cfg=None):
    module = api()
    return module.build_research_probability_calibration_plan(
        rows,
        config=cfg or module.ResearchProbabilityCalibrationPlanConfig(),
    )


def test_cases_are_converted_to_ordered_calibration_steps() -> None:
    report = build_plan(
        calibration_case(
            "4",
            "0.600000",
            "0.610000",
            evidence_confidence_score="0.900000",
        ),
        calibration_case("2", "0.800000", "0.620000"),
        calibration_case(
            "3",
            "0.400000",
            "0.430000",
            observation_count="5",
            evidence_confidence_score="0.900000",
        ),
        calibration_case(
            "1",
            "0.520000",
            "0.450000",
            evidence_confidence_score="0.700000",
        ),
    )

    assert is_dataclass(report)
    assert report.plan_version == "research-probability-calibration-plan-v1"
    assert report.input_case_count == d("4")
    assert report.step_count == d("4")
    assert report.block_count == d("1")
    assert report.watch_count == d("2")
    assert report.pass_count == d("1")
    assert report.plan_status == "block"
    assert report.average_calibration_gap == d("0.072500")
    assert report.average_reliability_score == d("0.767750")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    steps = report.steps
    assert tuple(step.case_sequence for step in steps) == (
        d("2"),
        d("1"),
        d("3"),
        d("4"),
    )
    assert tuple(step.priority_rank for step in steps) == (
        d("1"),
        d("2"),
        d("3"),
        d("4"),
    )
    assert tuple(step.calibration_status for step in steps) == (
        "block",
        "watch",
        "watch",
        "pass",
    )
    assert tuple(step.calibration_gap for step in steps) == (
        d("0.180000"),
        d("0.070000"),
        d("0.030000"),
        d("0.010000"),
    )
    assert tuple(step.reliability_score for step in steps) == (
        d("0.656000"),
        d("0.651000"),
        d("0.873000"),
        d("0.891000"),
    )
    assert tuple(step.next_research_step for step in steps) == (
        "hold_public_probability_score_for_review",
        "track_calibration_gap_next_cycle",
        "expand_resolution_sample_review",
        "clear_for_report_publication",
    )
    assert report.reason_codes == (
        "research_probability_calibration_plan_gap_block",
        "research_probability_calibration_plan_thin_history_watch",
        "research_probability_calibration_plan_gap_watch",
        "research_probability_calibration_plan_pass",
    )


def test_low_confidence_statuses_use_floor_and_watch_thresholds() -> None:
    report = build_plan(
        calibration_case(
            "1",
            "0.510000",
            "0.500000",
            evidence_confidence_score="0.350000",
        ),
        calibration_case(
            "2",
            "0.510000",
            "0.500000",
            evidence_confidence_score="0.500000",
        ),
    )

    assert tuple(step.calibration_status for step in report.steps) == ("block", "watch")
    assert report.steps[0].reason_codes == (
        "research_probability_calibration_plan_low_confidence_block",
    )
    assert report.steps[1].reason_codes == (
        "research_probability_calibration_plan_low_confidence_watch",
    )


def test_empty_inputs_return_readonly_watch_report_with_no_steps() -> None:
    report = build_plan()

    assert report.input_case_count == d("0")
    assert report.step_count == d("0")
    assert report.block_count == d("0")
    assert report.watch_count == d("0")
    assert report.pass_count == d("0")
    assert report.average_calibration_gap == d("0.000000")
    assert report.average_reliability_score == d("0.000000")
    assert report.plan_status == "watch"
    assert report.steps == ()
    assert report.reason_codes == ("research_probability_calibration_plan_no_cases",)


def test_payload_helper_uses_decimal_strings_and_omits_raw_event_material() -> None:
    payload = api().research_probability_calibration_plan_payload(
        build_plan(calibration_case("1", "0.800000", "0.620000")),
    )

    assert payload["step_count"] == "1"
    assert payload["steps"][0]["case_sequence"] == "1"
    assert payload["steps"][0]["forecast_probability"] == "0.800000"
    assert payload["steps"][0]["observed_frequency"] == "0.620000"
    assert payload["steps"][0]["calibration_gap"] == "0.180000"
    assert all(not isinstance(value, float) for value in _walk_values(payload))

    rendered_payload = repr(payload).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "buy",
        "sell",
        "position",
        "recommendation",
    ):
        assert forbidden not in rendered_payload


def test_validation_rejects_invalid_inputs_and_inconsistent_reports() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_research_probability_calibration_plan((), config=object())
    with pytest.raises(ValueError, match="case_sequence"):
        calibration_case("1.5", "0.500000", "0.500000")
    with pytest.raises(ValueError, match="forecast_probability"):
        calibration_case("1", "0.5000001", "0.500000")
    with pytest.raises(ValueError, match="observation_count"):
        calibration_case("1", "0.500000", "0.500000", observation_count="-1")
    with pytest.raises(ValueError, match="reason_codes"):
        module.ResearchProbabilityCalibrationCaseInput(
            case_sequence=d("1"),
            forecast_probability=d("0.500000"),
            observed_frequency=d("0.500000"),
            observation_count=d("40"),
            evidence_confidence_score=d("0.800000"),
            reason_codes=("wrong",),
        )
    with pytest.raises(ValueError, match="duplicate"):
        build_plan(
            calibration_case("1", "0.500000", "0.500000"),
            calibration_case("1", "0.600000", "0.600000"),
        )

    report = build_plan(calibration_case("1", "0.500000", "0.500000"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("9"))


def test_hard_flags_public_dataclasses_are_frozen_and_decimal_only() -> None:
    row = calibration_case("1", "0.800000", "0.620000")
    report = build_plan(row)

    with pytest.raises(FrozenInstanceError):
        row.forecast_probability = d("0.700000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.steps[0].calibration_status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.plan_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="calibration_gap"):
        replace(report.steps[0], calibration_gap=d("0.010000"))
    with pytest.raises(ValueError, match="forecast_probability"):
        module = api()
        module.ResearchProbabilityCalibrationCaseInput(
            case_sequence=d("1"),
            forecast_probability=1,
            observed_frequency=d("0.500000"),
            observation_count=d("40"),
            evidence_confidence_score=d("0.800000"),
            reason_codes=("research_probability_calibration_plan_input",),
        )


def test_static_module_has_no_forbidden_surfaces_or_float_literals() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_probability_calibration_plan.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "network",
        "private_key",
        "api_key",
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "submit",
        "cancel",
        "replace",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "buy",
        "sell",
        "position",
        "recommendation",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "read", "write", "float"}


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in _walk_values(child))
    return (value,)
