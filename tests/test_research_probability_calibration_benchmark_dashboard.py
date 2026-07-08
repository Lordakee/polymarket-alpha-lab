from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.research_probability_calibration_benchmark_dashboard",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    benchmark_label: str = "model-alpha",
    *,
    forecast_count: Decimal = d("120.000000"),
    settled_count: Decimal = d("100.000000"),
    brier_score: Decimal = d("0.120000"),
    expected_calibration_error: Decimal = d("0.020000"),
    hard_review_flag: bool = False,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchProbabilityCalibrationBenchmarkObservation(
        benchmark_label=benchmark_label,
        forecast_count=forecast_count,
        settled_count=settled_count,
        brier_score=brier_score,
        expected_calibration_error=expected_calibration_error,
        hard_review_flag=hard_review_flag,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report_from(
    observations: tuple[Any, ...],
    *,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_probability_calibration_benchmark_dashboard(
        observations,
        config=module.ResearchProbabilityCalibrationBenchmarkDashboardConfig(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def assert_no_public_float_or_int(value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        pytest.fail(f"public payload numeric must be Decimal-derived text: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_float_or_int(item)


def test_builds_pass_watch_block_dashboard_with_public_review_statuses() -> None:
    module = api()
    report = report_from(
        (
            observation("model-gamma", hard_review_flag=True),
            observation(
                "model-beta",
                brier_score=d("0.210000"),
                expected_calibration_error=d("0.070000"),
            ),
            observation("model-alpha"),
        ),
    )

    assert report.public_status == "block"
    assert report.benchmark_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.total_forecast_count == d("360.000000")
    assert report.total_settled_count == d("300.000000")
    assert report.average_brier_score == d("0.150000")
    assert report.average_expected_calibration_error == d("0.036667")
    assert report.max_brier_score == d("0.210000")
    assert report.max_expected_calibration_error == d("0.070000")
    assert report.hard_review_flag_count == d("1.000000")
    assert report.reason_codes == (
        "benchmark_sample_pass",
        "benchmark_brier_pass",
        "benchmark_brier_watch",
        "benchmark_ece_pass",
        "benchmark_ece_watch",
        "benchmark_hard_review_clear",
        "benchmark_hard_review_flag",
        "benchmark_calibration_pass",
        "benchmark_calibration_watch",
        "benchmark_calibration_block",
        "dashboard_benchmark_block",
    )

    rows_by_label = {row.benchmark_label: row for row in report.rows}
    assert rows_by_label["model-alpha"].public_status == "pass"
    assert rows_by_label["model-beta"].public_status == "watch"
    assert rows_by_label["model-gamma"].public_status == "block"
    assert rows_by_label["model-gamma"].reason_codes == (
        "benchmark_sample_pass",
        "benchmark_brier_pass",
        "benchmark_ece_pass",
        "benchmark_hard_review_flag",
        "benchmark_calibration_block",
    )
    assert tuple(row.benchmark_label for row in report.rows) == (
        "model-alpha",
        "model-beta",
        "model-gamma",
    )

    payload = module.research_probability_calibration_benchmark_dashboard_payload(report)
    assert_no_public_float_or_int(payload)
    assert payload["public_status"] == "block"
    assert payload["benchmark_count"] == "3.000000"
    assert [row["benchmark_label"] for row in payload["rows"]] == [
        "model-alpha",
        "model-beta",
        "model-gamma",
    ]
    assert {
        value
        for value in walk_values(payload)
        if isinstance(value, str) and value in {"pass", "watch", "block"}
    } == {"pass", "watch", "block"}
    assert all(
        status in {"pass", "watch", "block"}
        for status in [payload["public_status"]]
        + [row["public_status"] for row in payload["rows"]]
    )


def test_dataclasses_are_frozen_and_numeric_inputs_are_decimal_only() -> None:
    module = api()

    for cls_name in (
        "ResearchProbabilityCalibrationBenchmarkDashboardConfig",
        "ResearchProbabilityCalibrationBenchmarkObservation",
        "ResearchProbabilityCalibrationBenchmarkDashboardRow",
        "ResearchProbabilityCalibrationBenchmarkReasonCodeCount",
        "ResearchProbabilityCalibrationBenchmarkDashboardReport",
    ):
        cls = getattr(module, cls_name)
        assert is_dataclass(cls)
        assert getattr(cls, "__dataclass_params__").frozen is True

    numeric_field_names = {
        field.name
        for cls_name in (
            "ResearchProbabilityCalibrationBenchmarkObservation",
            "ResearchProbabilityCalibrationBenchmarkDashboardRow",
            "ResearchProbabilityCalibrationBenchmarkReasonCodeCount",
            "ResearchProbabilityCalibrationBenchmarkDashboardReport",
        )
        for field in fields(getattr(module, cls_name))
        if field.name.endswith("_count")
        or field.name.endswith("_score")
        or field.name.endswith("_error")
    }
    assert numeric_field_names

    with pytest.raises(ValueError, match="forecast_count must be a Decimal"):
        observation(forecast_count=120)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="brier_score must be a Decimal"):
        observation(brier_score=_DecimalSubclass("0.120000"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report_from(
            (observation(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="hard_review_flag must be a bool"):
        observation(hard_review_flag=1)  # type: ignore[arg-type]

    row = report_from((observation(),)).rows[0]
    with pytest.raises(FrozenInstanceError):
        row.public_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="public_status"):
        replace(row, public_status="review")


def test_public_payload_rejects_leaky_keys_values_and_hard_flag_downgrades() -> None:
    module = api()
    payload = module.research_probability_calibration_benchmark_dashboard_payload(
        report_from((observation(),)),
    )

    with pytest.raises(ValueError, match="unsafe public"):
        module.research_probability_calibration_benchmark_dashboard_payload(
            {**payload, "market_slug": "will-election-market-close"},
        )

    leaked_value = json.loads(json.dumps(payload))
    leaked_value["rows"][0]["reason_codes"] = [
        "raw_candidate_id_source_url_buy_recommendation",
    ]
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_probability_calibration_benchmark_dashboard_payload(leaked_value)

    with pytest.raises(ValueError, match="unsafe public"):
        observation("market_id_model")
    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        module.ResearchProbabilityCalibrationBenchmarkDashboardConfig(report_only=False)


def test_hard_review_flags_force_block_without_trading_or_action_language() -> None:
    module = api()
    report = report_from(
        (
            observation("model-alpha", hard_review_flag=True),
            observation("model-beta"),
        ),
    )

    flagged_row = report.rows[0]
    assert flagged_row.benchmark_label == "model-alpha"
    assert flagged_row.public_status == "block"
    assert "benchmark_hard_review_flag" in flagged_row.reason_codes
    assert report.public_status == "block"
    assert report.hard_review_flag_count == d("1.000000")

    payload_text = json.dumps(
        module.research_probability_calibration_benchmark_dashboard_payload(report),
        sort_keys=True,
    ).lower()
    for forbidden in ("buy", "sell", "position", "recommendation"):
        assert forbidden not in payload_text


def test_payload_is_deterministic_for_input_order_and_timezone() -> None:
    module = api()
    observations = (
        observation("model-beta", brier_score=d("0.210000")),
        observation("model-alpha"),
        observation("model-gamma", hard_review_flag=True),
    )
    shifted_generated_at = datetime(
        2026,
        7,
        8,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    first = module.research_probability_calibration_benchmark_dashboard_payload(
        module.build_research_probability_calibration_benchmark_dashboard(
            observations,
            config=module.ResearchProbabilityCalibrationBenchmarkDashboardConfig(),
            generated_at=GENERATED_AT,
        ),
    )
    second = module.research_probability_calibration_benchmark_dashboard_payload(
        module.build_research_probability_calibration_benchmark_dashboard(
            tuple(reversed(observations)),
            config=module.ResearchProbabilityCalibrationBenchmarkDashboardConfig(),
            generated_at=shifted_generated_at,
        ),
    )

    assert first == second
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
        second,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert_no_public_float_or_int(first)


def test_report_digest_matches_public_summary_and_rejects_tampering() -> None:
    module = api()
    report = report_from(
        (
            observation("model-alpha"),
            observation("model-beta", brier_score=d("0.210000")),
            observation("model-gamma", hard_review_flag=True),
        ),
    )

    payload = module.research_probability_calibration_benchmark_dashboard_payload(report)
    digest = module.research_probability_calibration_benchmark_dashboard_digest(report)

    assert_no_public_float_or_int(digest)
    assert "rows" not in digest
    for key in (
        "generated_at",
        "config_version",
        "public_status",
        "benchmark_count",
        "pass_count",
        "watch_count",
        "block_count",
        "total_forecast_count",
        "total_settled_count",
        "average_brier_score",
        "average_expected_calibration_error",
        "max_brier_score",
        "max_expected_calibration_error",
        "hard_review_flag_count",
        "reason_codes",
        "reason_code_counts",
    ):
        assert digest[key] == payload[key]
    assert digest["report_validation_digest"] == payload["validation_digest"]
    assert len(digest["digest_validation_digest"]) == 64

    tampered = json.loads(json.dumps(payload))
    tampered["rows"][0]["brier_score"] = "0.121000"
    with pytest.raises(ValueError, match="validation_digest"):
        module.research_probability_calibration_benchmark_dashboard_payload(tampered)
