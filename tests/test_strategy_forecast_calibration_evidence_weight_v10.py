from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_forecast_calibration_evidence_weight_v10 import (
    DEFAULT_CONFIG_VERSION,
    ForecastCalibrationEvidenceWeightConfig,
    ForecastCalibrationEvidenceWeightInput,
    ForecastCalibrationEvidenceWeightRow,
    strategy_forecast_calibration_evidence_weight_payload,
    weight_forecast_calibration_evidence,
)


def _config() -> ForecastCalibrationEvidenceWeightConfig:
    return ForecastCalibrationEvidenceWeightConfig(
        max_evidence_age_hours=Decimal("96.000000"),
        target_independent_source_count=Decimal("4"),
        max_correlated_source_count=Decimal("4"),
        target_market_liquidity_usd=Decimal("10000.000000"),
        pass_evidence_weight_score=Decimal("0.700000"),
        watch_evidence_weight_score=Decimal("0.450000"),
    )


def _screening_input() -> ForecastCalibrationEvidenceWeightInput:
    return ForecastCalibrationEvidenceWeightInput(
        forecast_id="forecast-macro-cut-001",
        market_id="market-fed-march-2026",
        observed_at=datetime(2026, 3, 15, 18, tzinfo=UTC),
        forecast_probability=Decimal("0.610000"),
        historical_calibration_error=Decimal("0.080000"),
        evidence_age_hours=Decimal("12.000000"),
        independent_source_count=Decimal("3"),
        correlated_source_count=Decimal("1"),
        market_liquidity_usd=Decimal("7500.000000"),
        resolution_clarity_score=Decimal("0.900000"),
    )


def test_weights_calibrated_fresh_independent_liquid_clear_forecast_evidence() -> None:
    row = weight_forecast_calibration_evidence(_screening_input(), config=_config())

    assert row.config_version == DEFAULT_CONFIG_VERSION
    assert row.forecast_id == "forecast-macro-cut-001"
    assert row.market_id == "market-fed-march-2026"
    assert row.observed_at == datetime(2026, 3, 15, 18, tzinfo=UTC)
    assert row.forecast_probability == Decimal("0.610000")
    assert row.calibration_score == Decimal("0.920000")
    assert row.freshness_score == Decimal("0.875000")
    assert row.source_independence_score == Decimal("0.656250")
    assert row.liquidity_score == Decimal("0.750000")
    assert row.resolution_clarity_score == Decimal("0.900000")
    assert row.evidence_weight_score == Decimal("0.829488")
    assert row.screening_status == "pass"
    assert row.reason_codes == (
        "calibration_supported",
        "evidence_fresh",
        "source_independence_mixed",
        "liquidity_supported",
        "resolution_clear",
    )
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_downgrades_stale_correlated_thin_ambiguous_forecast_evidence() -> None:
    weak_input = replace(
        _screening_input(),
        historical_calibration_error=Decimal("0.420000"),
        evidence_age_hours=Decimal("120.000000"),
        independent_source_count=Decimal("1"),
        correlated_source_count=Decimal("4"),
        market_liquidity_usd=Decimal("500.000000"),
        resolution_clarity_score=Decimal("0.350000"),
    )

    row = weight_forecast_calibration_evidence(weak_input, config=_config())

    assert row.calibration_score == Decimal("0.580000")
    assert row.freshness_score == Decimal("0.000000")
    assert row.source_independence_score == Decimal("0.125000")
    assert row.liquidity_score == Decimal("0.050000")
    assert row.resolution_clarity_score == Decimal("0.350000")
    assert row.evidence_weight_score == Decimal("0.258950")
    assert row.screening_status == "reject"
    assert row.reason_codes == (
        "calibration_error_elevated",
        "evidence_stale",
        "source_independence_weak",
        "liquidity_thin",
        "resolution_ambiguous",
    )


def test_payload_is_report_only_json_ready_without_float_values() -> None:
    row = weight_forecast_calibration_evidence(_screening_input(), config=_config())

    payload = strategy_forecast_calibration_evidence_weight_payload(row)

    assert payload == {
        "config_version": DEFAULT_CONFIG_VERSION,
        "forecast_id": "forecast-macro-cut-001",
        "market_id": "market-fed-march-2026",
        "observed_at": "2026-03-15T18:00:00+00:00",
        "forecast_probability": "0.610000",
        "historical_calibration_error": "0.080000",
        "evidence_age_hours": "12.000000",
        "independent_source_count": "3",
        "correlated_source_count": "1",
        "market_liquidity_usd": "7500.000000",
        "calibration_score": "0.920000",
        "freshness_score": "0.875000",
        "source_independence_score": "0.656250",
        "liquidity_score": "0.750000",
        "resolution_clarity_score": "0.900000",
        "evidence_weight_score": "0.829488",
        "screening_status": "pass",
        "reason_codes": [
            "calibration_supported",
            "evidence_fresh",
            "source_independence_mixed",
            "liquidity_supported",
            "resolution_clear",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert not _contains_float(payload)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    (
        ({"forecast_id": ""}, "forecast_id"),
        ({"market_id": " market-fed "}, "market_id"),
        ({"observed_at": datetime(2026, 3, 15, 18)}, "observed_at"),
        ({"forecast_probability": Decimal("1.100000")}, "forecast_probability"),
        ({"historical_calibration_error": Decimal("-0.010000")}, "historical_calibration_error"),
        ({"evidence_age_hours": Decimal("-1.000000")}, "evidence_age_hours"),
        ({"independent_source_count": Decimal("1.500000")}, "independent_source_count"),
        ({"correlated_source_count": Decimal("-1")}, "correlated_source_count"),
        ({"market_liquidity_usd": Decimal("-0.010000")}, "market_liquidity_usd"),
        ({"resolution_clarity_score": 0.9}, "resolution_clarity_score"),
        ({"paper_only": False}, "paper_only"),
        ({"report_only": False}, "report_only"),
        ({"readonly": False}, "readonly"),
    ),
)
def test_validates_forecast_calibration_evidence_inputs(
    kwargs: dict[str, object],
    match: str,
) -> None:
    valid_kwargs = {
        "forecast_id": "forecast-macro-cut-001",
        "market_id": "market-fed-march-2026",
        "observed_at": datetime(2026, 3, 15, 18, tzinfo=UTC),
        "forecast_probability": Decimal("0.610000"),
        "historical_calibration_error": Decimal("0.080000"),
        "evidence_age_hours": Decimal("12.000000"),
        "independent_source_count": Decimal("3"),
        "correlated_source_count": Decimal("1"),
        "market_liquidity_usd": Decimal("7500.000000"),
        "resolution_clarity_score": Decimal("0.900000"),
    }
    valid_kwargs.update(kwargs)

    with pytest.raises(ValueError, match=match):
        ForecastCalibrationEvidenceWeightInput(**valid_kwargs)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    (
        ({"max_evidence_age_hours": Decimal("0.000000")}, "max_evidence_age_hours"),
        ({"target_independent_source_count": Decimal("0")}, "target_independent_source_count"),
        ({"max_correlated_source_count": Decimal("1.500000")}, "max_correlated_source_count"),
        ({"target_market_liquidity_usd": Decimal("0.000000")}, "target_market_liquidity_usd"),
        ({"pass_evidence_weight_score": Decimal("0.400000")}, "pass_evidence_weight_score"),
        ({"watch_evidence_weight_score": Decimal("0.800000")}, "watch_evidence_weight_score"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_validates_evidence_weight_config(kwargs: dict[str, object], match: str) -> None:
    valid_kwargs = {
        "max_evidence_age_hours": Decimal("96.000000"),
        "target_independent_source_count": Decimal("4"),
        "max_correlated_source_count": Decimal("4"),
        "target_market_liquidity_usd": Decimal("10000.000000"),
        "pass_evidence_weight_score": Decimal("0.700000"),
        "watch_evidence_weight_score": Decimal("0.450000"),
    }
    valid_kwargs.update(kwargs)

    with pytest.raises(ValueError, match=match):
        ForecastCalibrationEvidenceWeightConfig(**valid_kwargs)


def test_outputs_are_frozen_and_reject_non_exact_or_subclassed_surfaces() -> None:
    row = weight_forecast_calibration_evidence(_screening_input(), config=_config())

    with pytest.raises(FrozenInstanceError):
        row.evidence_weight_score = Decimal("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=["calibration_supported"])  # type: ignore[arg-type]

    class ForecastCalibrationEvidenceWeightRowSubclass(ForecastCalibrationEvidenceWeightRow):
        pass

    with pytest.raises(ValueError, match="row"):
        ForecastCalibrationEvidenceWeightRowSubclass(
            config_version=DEFAULT_CONFIG_VERSION,
            forecast_id="forecast-macro-cut-001",
            market_id="market-fed-march-2026",
            observed_at=datetime(2026, 3, 15, 18, tzinfo=UTC),
            forecast_probability=Decimal("0.610000"),
            historical_calibration_error=Decimal("0.080000"),
            evidence_age_hours=Decimal("12.000000"),
            independent_source_count=Decimal("3"),
            correlated_source_count=Decimal("1"),
            market_liquidity_usd=Decimal("7500.000000"),
            calibration_score=Decimal("0.920000"),
            freshness_score=Decimal("0.875000"),
            source_independence_score=Decimal("0.656250"),
            liquidity_score=Decimal("0.750000"),
            resolution_clarity_score=Decimal("0.900000"),
            evidence_weight_score=Decimal("0.829488"),
            screening_status="pass",
            reason_codes=(
                "calibration_supported",
                "evidence_fresh",
                "source_independence_mixed",
                "liquidity_supported",
                "resolution_clear",
            ),
        )


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False
