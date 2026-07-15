from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def _module():
    return importlib.import_module(
        "polymarket_alpha_lab.probability_event_forecast_calibration_residual_report",
    )


def _build(
    *,
    forecast_probability: Decimal = d("0.620000"),
    historical_calibrated_probability: Decimal = d("0.600000"),
    calibration_error_probability: Decimal = d("0.020000"),
    sample_count: Decimal = d("150.000000"),
    recency_penalty_probability: Decimal = d("0.010000"),
    config=None,
):
    module = _module()
    return module.build_probability_event_forecast_calibration_residual_report(
        forecast_probability=forecast_probability,
        historical_calibrated_probability=historical_calibrated_probability,
        calibration_error_probability=calibration_error_probability,
        sample_count=sample_count,
        recency_penalty_probability=recency_penalty_probability,
        config=config
        or module.ProbabilityEventForecastCalibrationResidualConfig(
            config_version="probability-event-forecast-calibration-residual-v0",
        ),
    )


def test_low_residual_passes_with_public_payload_and_digest() -> None:
    report = _build()
    module = _module()

    assert type(report) is module.ProbabilityEventForecastCalibrationResidualReport
    assert report.config_version == "probability-event-forecast-calibration-residual-v0"
    assert report.forecast_probability == d("0.620000")
    assert report.historical_calibrated_probability == d("0.600000")
    assert report.calibration_error_probability == d("0.020000")
    assert report.sample_count == d("150.000000")
    assert report.recency_penalty_probability == d("0.010000")
    assert report.calibration_residual_probability == d("0.050000")
    assert report.adjusted_forecast_probability == d("0.590000")
    assert report.calibration_residual_status == "pass"
    assert report.status == "pass"
    assert report.reason_codes == ("forecast_calibration_residual_pass",)
    assert report.manual_next_step == "continue_readonly_paper_probability_review"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == module.probability_event_forecast_calibration_residual_report_payload(
        report,
    )
    assert payload["forecast_probability"] == "0.620000"
    assert payload["adjusted_forecast_probability"] == "0.590000"
    assert payload["calibration_residual_status"] == "pass"
    assert payload["reason_codes"] == ["forecast_calibration_residual_pass"]
    assert payload["manual_next_step"] == "continue_readonly_paper_probability_review"
    assert payload["payload_digest"] == report.payload_digest
    assert report.payload_digest == (
        module.probability_event_forecast_calibration_residual_report_digest(report)
    )
    json.dumps(payload, sort_keys=True)
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)


def test_high_residual_and_small_sample_trigger_watch_review() -> None:
    report = _build(
        forecast_probability=d("0.820000"),
        historical_calibrated_probability=d("0.650000"),
        calibration_error_probability=d("0.060000"),
        sample_count=d("24.000000"),
        recency_penalty_probability=d("0.030000"),
    )

    assert report.calibration_residual_probability == d("0.260000")
    assert report.adjusted_forecast_probability == d("0.730000")
    assert report.calibration_residual_status == "watch"
    assert report.reason_codes == (
        "forecast_historical_gap_above_watch",
        "calibration_error_above_watch",
        "sample_count_below_minimum",
        "recency_penalty_present",
    )
    assert report.manual_next_step == "manually_review_forecast_calibration_residual"


def test_extreme_residual_or_probability_floor_triggers_block_without_execution() -> None:
    residual_report = _build(
        forecast_probability=d("0.950000"),
        historical_calibrated_probability=d("0.500000"),
        calibration_error_probability=d("0.090000"),
        sample_count=d("100.000000"),
        recency_penalty_probability=d("0.060000"),
    )
    floor_report = _build(
        forecast_probability=d("0.080000"),
        historical_calibrated_probability=d("0.020000"),
        calibration_error_probability=d("0.040000"),
        sample_count=d("60.000000"),
        recency_penalty_probability=d("0.080000"),
    )

    assert residual_report.calibration_residual_probability == d("0.600000")
    assert residual_report.adjusted_forecast_probability == d("0.800000")
    assert residual_report.calibration_residual_status == "block"
    assert residual_report.reason_codes == (
        "forecast_historical_gap_above_block",
        "calibration_error_above_watch",
        "recency_penalty_present",
    )
    assert residual_report.manual_next_step == (
        "pause_paper_probability_review_until_calibration_residual_is_resolved"
    )
    assert floor_report.adjusted_forecast_probability == d("0.000000")
    assert floor_report.calibration_residual_status == "block"
    assert floor_report.reason_codes == (
        "calibration_error_above_watch",
        "adjusted_forecast_probability_at_boundary",
        "recency_penalty_present",
    )


def test_validation_enforces_decimal_only_frozen_flags_and_digest_consistency() -> None:
    module = _module()
    report = _build()

    with pytest.raises(FrozenInstanceError):
        report.calibration_residual_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="forecast_probability"):
        _build(forecast_probability="0.620000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="forecast_probability"):
        _build(forecast_probability=d("0.6200001"))
    with pytest.raises(ValueError, match="historical_calibrated_probability"):
        _build(historical_calibrated_probability=d("-0.010000"))
    with pytest.raises(ValueError, match="calibration_error_probability"):
        _build(calibration_error_probability=d("1.010000"))
    with pytest.raises(ValueError, match="sample_count"):
        _build(sample_count=d("24.500000"))
    with pytest.raises(ValueError, match="recency_penalty_probability"):
        _build(recency_penalty_probability=d("-0.010000"))
    with pytest.raises(ValueError, match="paper_only"):
        module.ProbabilityEventForecastCalibrationResidualConfig(
            config_version="probability-event-forecast-calibration-residual-v0",
            paper_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=("forecast_calibration_residual_pass", "x"))
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(report, manual_next_step="execute_trade")
    with pytest.raises(ValueError, match="payload_digest"):
        replace(report, payload_digest="0" * 64)
    with pytest.raises(ValueError, match="config"):
        _build(config=object())

    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(
            fragment in lowered
            for fragment in (
                "auth",
                "execution",
                "key",
                "live",
                "order",
                "sign",
                "trade",
                "wallet",
            )
        )


def test_owned_module_has_no_network_persistence_or_execution_surfaces() -> None:
    module = _module()
    forbidden_names = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "web3",
        "ccxt",
        "psycopg",
    )

    for forbidden_name in forbidden_names:
        assert not hasattr(module, forbidden_name)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, str):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field_name in value.__dataclass_fields__:
            _assert_no_non_decimal_public_numbers(getattr(value, field_name))
