from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/strategy_forecast_confidence_interval_v10.py",
)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_forecast_confidence_interval_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def interval(**overrides: object):
    module = api()
    values = {
        "point_forecast": d("0.550000"),
        "model_dispersion": d("0.080000"),
        "source_conflict_score": d("0.200000"),
        "sample_size": d("25"),
        "calibration_error_bps": d("100"),
        "time_to_resolution_minutes": d("45"),
    }
    values.update(overrides)
    return module.calculate_strategy_forecast_confidence_interval(**values)


def test_calculates_deterministic_interval_and_reason_codes() -> None:
    result = interval()

    assert result.lower_probability == d("0.415000")
    assert result.upper_probability == d("0.685000")
    assert result.interval_width == d("0.270000")
    assert result.confidence_tier == "low"
    assert result.reason_codes == (
        "confidence_tier_low",
        "model_dispersion_elevated",
        "source_conflict_elevated",
        "sample_size_small",
        "calibration_error_elevated",
        "near_resolution_window",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_high_confidence_interval_payload_uses_decimal_strings() -> None:
    module = api()
    result = interval(
        point_forecast=d("0.400000"),
        model_dispersion=d("0.010000"),
        source_conflict_score=d("0.020000"),
        sample_size=d("120"),
        calibration_error_bps=d("10"),
        time_to_resolution_minutes=d("1440"),
    )

    assert result.lower_probability == d("0.373250")
    assert result.upper_probability == d("0.426750")
    assert result.interval_width == d("0.053500")
    assert result.confidence_tier == "high"
    assert result.reason_codes == ("confidence_tier_high",)

    payload = module.strategy_forecast_confidence_interval_payload(result)
    assert payload["lower_probability"] == "0.373250"
    assert payload["upper_probability"] == "0.426750"
    assert payload["interval_width"] == "0.053500"
    assert payload["confidence_tier"] == "high"
    assert not any(type(value) is float for value in _walk_payload(payload))
    assert not any(type(value) is int for value in _walk_payload(payload))


def test_probability_bounds_are_clamped_without_exceeding_probability_space() -> None:
    result = interval(
        point_forecast=d("0.970000"),
        model_dispersion=d("0.100000"),
        source_conflict_score=d("0.300000"),
        sample_size=d("5"),
        calibration_error_bps=d("200"),
        time_to_resolution_minutes=d("30"),
    )

    assert result.lower_probability == d("0.780000")
    assert result.upper_probability == d("1.000000")
    assert result.interval_width == d("0.220000")
    assert result.confidence_tier == "low"
    assert result.reason_codes == (
        "confidence_tier_low",
        "model_dispersion_elevated",
        "source_conflict_elevated",
        "sample_size_very_small",
        "calibration_error_elevated",
        "near_resolution_window",
        "upper_probability_clamped",
    )


def test_validation_rejects_non_decimal_invalid_ranges_and_false_flags() -> None:
    module = api()
    result = interval()

    with pytest.raises(FrozenInstanceError):
        result.interval_width = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="point_forecast must be a Decimal"):
        interval(point_forecast=0.55)
    with pytest.raises(ValueError, match="sample_size must be a Decimal"):
        interval(sample_size=25)
    with pytest.raises(ValueError, match="source_conflict_score must be a Decimal"):
        interval(source_conflict_score=True)
    with pytest.raises(ValueError, match="model_dispersion must be finite"):
        interval(model_dispersion=Decimal("NaN"))
    with pytest.raises(ValueError, match="point_forecast must be between 0 and 1"):
        interval(point_forecast=d("1.000001"))
    with pytest.raises(ValueError, match="sample_size must be an integer Decimal"):
        interval(sample_size=d("25.500000"))
    with pytest.raises(ValueError, match="calibration_error_bps must be <= 10000"):
        interval(calibration_error_bps=d("10000.000001"))
    with pytest.raises(ValueError, match="time_to_resolution_minutes must be nonnegative"):
        interval(time_to_resolution_minutes=d("-1"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(
            module.StrategyForecastConfidenceIntervalInput(
                point_forecast=d("0.500000"),
                model_dispersion=d("0.010000"),
                source_conflict_score=d("0.020000"),
                sample_size=d("40"),
                calibration_error_bps=d("20"),
                time_to_resolution_minutes=d("120"),
            ),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_build_requires_exact_input_type_and_result_self_consistency() -> None:
    module = api()
    input_row = module.StrategyForecastConfidenceIntervalInput(
        point_forecast=d("0.500000"),
        model_dispersion=d("0.020000"),
        source_conflict_score=d("0.030000"),
        sample_size=d("50"),
        calibration_error_bps=d("25"),
        time_to_resolution_minutes=d("240"),
    )

    with pytest.raises(ValueError, match="input_row must be"):
        module.build_strategy_forecast_confidence_interval(object())
    with pytest.raises(ValueError, match="interval_width must match probability bounds"):
        module.StrategyForecastConfidenceIntervalResult(
            lower_probability=d("0.400000"),
            upper_probability=d("0.600000"),
            interval_width=d("0.300000"),
            confidence_tier="medium",
            reason_codes=("confidence_tier_medium",),
        )

    result = module.build_strategy_forecast_confidence_interval(input_row)
    assert result.lower_probability == d("0.467500")
    assert result.upper_probability == d("0.532500")
    assert result.interval_width == d("0.065000")


def test_public_numeric_fields_are_decimal_only() -> None:
    module = api()
    decimal_fields = {
        "StrategyForecastConfidenceIntervalInput": {
            "point_forecast",
            "model_dispersion",
            "source_conflict_score",
            "sample_size",
            "calibration_error_bps",
            "time_to_resolution_minutes",
        },
        "StrategyForecastConfidenceIntervalResult": {
            "lower_probability",
            "upper_probability",
            "interval_width",
        },
    }

    for class_name, field_names in decimal_fields.items():
        annotations = getattr(module, class_name).__annotations__
        for field_name in field_names:
            assert annotations[field_name] == "Decimal"


def test_module_scope_has_no_live_io_or_execution_surface() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "signing",
        "account",
        "order",
        "submit",
        "cancel",
        "recommend",
        "advice",
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "open(",
        ".read(",
        ".write(",
    ):
        assert forbidden not in lowered


def _walk_payload(value: Any):
    if isinstance(value, dict):
        for nested in value.values():
            yield from _walk_payload(nested)
    elif isinstance(value, (tuple, list)):
        for nested in value:
            yield from _walk_payload(nested)
    else:
        yield value
