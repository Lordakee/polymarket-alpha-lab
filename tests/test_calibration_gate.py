from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.calibration_gate import (
    PaperCalibrationGateConfig,
    PaperCalibrationGateReport,
    PaperCalibrationGateRow,
    build_paper_calibration_gate_report,
)
from polymarket_alpha_lab.forecast_calibration import (
    PaperForecastCalibrationConfig,
    build_paper_forecast_calibration_report,
)
from polymarket_alpha_lab.forecast_calibration_trend import (
    PaperForecastCalibrationTrendReport,
    PaperForecastCalibrationTrendStatusRow,
)
from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceObservation


GENERATED_AT = datetime(2026, 6, 18, 15, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 18, 14, 0, tzinfo=UTC)
REPORT_STATUSES = (
    "empty_calibration_history",
    "insufficient_calibration_sample",
    "calibration_evidence_observed",
    "calibration_quality_flags",
)


def _config(**overrides) -> PaperCalibrationGateConfig:
    values = {
        "config_version": "paper-calibration-gate-v0",
        "min_calibration_report_count": 1,
        "min_observation_count": 30,
        "max_brier_score": Decimal("0.250000"),
        "max_calibration_error": Decimal("0.100000"),
    }
    values.update(overrides)
    return PaperCalibrationGateConfig(**values)


def _status_rows(
    *,
    empty: int = 0,
    insufficient: int = 0,
    observed: int = 0,
    quality: int = 0,
) -> tuple[PaperForecastCalibrationTrendStatusRow, ...]:
    counts = {
        "empty_calibration_history": empty,
        "insufficient_calibration_sample": insufficient,
        "calibration_evidence_observed": observed,
        "calibration_quality_flags": quality,
    }
    total = sum(counts.values())
    return tuple(
        PaperForecastCalibrationTrendStatusRow(
            status,
            counts[status],
            (
                None
                if total == 0
                else (Decimal(counts[status]) / Decimal(total)).quantize(
                    Decimal("0.000001"),
                )
            ),
        )
        for status in REPORT_STATUSES
    )


def _passing_trend_report(
    *,
    generated_at: datetime = SOURCE_GENERATED_AT,
) -> PaperForecastCalibrationTrendReport:
    return PaperForecastCalibrationTrendReport(
        generated_at=generated_at,
        config_version="forecast-calibration-trend-v0",
        calibration_report_count=2,
        first_report_generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
        latest_report_generated_at=generated_at,
        latest_status="calibration_evidence_observed",
        latest_observation_count=40,
        latest_brier_score=Decimal("0.120000"),
        latest_mean_absolute_error=Decimal("0.200000"),
        latest_expected_calibration_error=Decimal("0.060000"),
        latest_max_bucket_error=Decimal("0.080000"),
        latest_bucket_count=3,
        worst_observed_brier_score=Decimal("0.140000"),
        worst_observed_expected_calibration_error=Decimal("0.070000"),
        worst_observed_max_bucket_error=Decimal("0.090000"),
        consecutive_insufficient_sample_count=0,
        consecutive_quality_flag_count=0,
        status_rows=_status_rows(observed=2),
    )


def _insufficient_trend_report() -> PaperForecastCalibrationTrendReport:
    return PaperForecastCalibrationTrendReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="forecast-calibration-trend-v0",
        calibration_report_count=1,
        first_report_generated_at=SOURCE_GENERATED_AT,
        latest_report_generated_at=SOURCE_GENERATED_AT,
        latest_status="insufficient_calibration_sample",
        latest_observation_count=12,
        latest_brier_score=Decimal("0.160000"),
        latest_mean_absolute_error=Decimal("0.300000"),
        latest_expected_calibration_error=Decimal("0.070000"),
        latest_max_bucket_error=Decimal("0.090000"),
        latest_bucket_count=2,
        worst_observed_brier_score=Decimal("0.160000"),
        worst_observed_expected_calibration_error=Decimal("0.070000"),
        worst_observed_max_bucket_error=Decimal("0.090000"),
        consecutive_insufficient_sample_count=1,
        consecutive_quality_flag_count=0,
        status_rows=_status_rows(insufficient=1),
    )


def _empty_trend_report() -> PaperForecastCalibrationTrendReport:
    return PaperForecastCalibrationTrendReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="forecast-calibration-trend-v0",
        calibration_report_count=0,
        first_report_generated_at=None,
        latest_report_generated_at=None,
        latest_status=None,
        latest_observation_count=0,
        latest_brier_score=None,
        latest_mean_absolute_error=None,
        latest_expected_calibration_error=None,
        latest_max_bucket_error=None,
        latest_bucket_count=0,
        worst_observed_brier_score=None,
        worst_observed_expected_calibration_error=None,
        worst_observed_max_bucket_error=None,
        consecutive_insufficient_sample_count=0,
        consecutive_quality_flag_count=0,
        status_rows=_status_rows(),
    )


def _quality_flag_trend_report() -> PaperForecastCalibrationTrendReport:
    return PaperForecastCalibrationTrendReport(
        generated_at=SOURCE_GENERATED_AT,
        config_version="forecast-calibration-trend-v0",
        calibration_report_count=1,
        first_report_generated_at=SOURCE_GENERATED_AT,
        latest_report_generated_at=SOURCE_GENERATED_AT,
        latest_status="calibration_quality_flags",
        latest_observation_count=40,
        latest_brier_score=Decimal("0.260000"),
        latest_mean_absolute_error=Decimal("0.410000"),
        latest_expected_calibration_error=Decimal("0.120000"),
        latest_max_bucket_error=Decimal("0.140000"),
        latest_bucket_count=2,
        worst_observed_brier_score=Decimal("0.260000"),
        worst_observed_expected_calibration_error=Decimal("0.120000"),
        worst_observed_max_bucket_error=Decimal("0.140000"),
        consecutive_insufficient_sample_count=0,
        consecutive_quality_flag_count=1,
        status_rows=_status_rows(quality=1),
    )


def _probability_observation(
    index: int,
    *,
    actual: Decimal,
) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=datetime(2026, 6, 1, tzinfo=UTC) + timedelta(days=index),
        source_packet_id=f"packet-{index}",
        condition_id=f"condition-{index % 2}",
        token_id=f"token-{index}",
        market_slug=f"market-{index % 2}",
        strategy_type="relative_value",
        risk_tags=("calibration",),
        predicted_probability=Decimal("0.5000"),
        actual_outcome_value=actual,
    )


def _passing_calibration_report():
    observations = tuple(
        _probability_observation(
            index,
            actual=Decimal("1") if index % 2 == 0 else Decimal("0"),
        )
        for index in range(30)
    )
    return build_paper_forecast_calibration_report(
        observations,
        config=PaperForecastCalibrationConfig(
            config_version="forecast-calibration-v0",
            probability_bucket_width=Decimal("0.5000"),
            min_observation_count=30,
            max_brier_score=Decimal("0.250000"),
            max_expected_calibration_error=Decimal("0.100000"),
        ),
        generated_at=SOURCE_GENERATED_AT,
    )


def test_calibration_gate_passes_when_calibration_trend_is_mature_and_within_thresholds():
    report = build_paper_calibration_gate_report(
        _passing_trend_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperCalibrationGateReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-calibration-gate-v0"
    assert report.source_report_kind == "forecast_calibration_trend"
    assert report.source_config_version == "forecast-calibration-trend-v0"
    assert report.source_generated_at == SOURCE_GENERATED_AT
    assert report.gate_status == "passed"
    assert report.passed is True
    assert report.reason_codes == (
        "calibration_history_ready",
        "observation_count_ready",
        "brier_score_within_limit",
        "calibration_error_within_limit",
    )
    assert report.gate_rows == (
        PaperCalibrationGateRow(
            "calibration_history",
            "passed",
            "calibration_history_ready",
            2,
            1,
        ),
        PaperCalibrationGateRow(
            "observation_count",
            "passed",
            "observation_count_ready",
            40,
            30,
        ),
        PaperCalibrationGateRow(
            "brier_score",
            "passed",
            "brier_score_within_limit",
            Decimal("0.120000"),
            Decimal("0.250000"),
        ),
        PaperCalibrationGateRow(
            "calibration_error",
            "passed",
            "calibration_error_within_limit",
            Decimal("0.060000"),
            Decimal("0.100000"),
        ),
    )
    assert report.gate_count == 4
    assert report.passed_gate_count == 4
    assert report.watch_gate_count == 0
    assert report.blocked_gate_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_calibration_gate_accepts_single_forecast_calibration_report_source():
    report = build_paper_calibration_gate_report(
        _passing_calibration_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.source_report_kind == "forecast_calibration_report"
    assert report.source_config_version == "forecast-calibration-v0"
    assert report.gate_status == "passed"
    assert report.passed is True


def test_calibration_gate_watches_insufficient_sample_without_passing():
    report = build_paper_calibration_gate_report(
        _insufficient_trend_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "watch"
    assert report.passed is False
    assert report.reason_codes == (
        "calibration_history_ready",
        "observation_count_insufficient",
        "brier_score_within_limit",
        "calibration_error_within_limit",
    )
    assert report.watch_gate_count == 1
    assert report.blocked_gate_count == 0
    assert report.gate_rows[1] == PaperCalibrationGateRow(
        "observation_count",
        "watch",
        "observation_count_insufficient",
        12,
        30,
    )


def test_calibration_gate_watches_empty_history_without_passing():
    report = build_paper_calibration_gate_report(
        _empty_trend_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "watch"
    assert report.passed is False
    assert report.reason_codes == (
        "calibration_history_empty",
        "observation_count_insufficient",
        "brier_score_unavailable",
        "calibration_error_unavailable",
    )
    assert report.watch_gate_count == 4
    assert report.blocked_gate_count == 0


def test_calibration_gate_blocks_high_brier_and_calibration_error():
    report = build_paper_calibration_gate_report(
        _quality_flag_trend_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.passed is False
    assert report.reason_codes == (
        "calibration_history_ready",
        "observation_count_ready",
        "brier_score_above_limit",
        "calibration_error_above_limit",
    )
    assert report.blocked_gate_count == 2
    assert report.gate_rows[2] == PaperCalibrationGateRow(
        "brier_score",
        "blocked",
        "brier_score_above_limit",
        Decimal("0.260000"),
        Decimal("0.250000"),
    )
    assert report.gate_rows[3] == PaperCalibrationGateRow(
        "calibration_error",
        "blocked",
        "calibration_error_above_limit",
        Decimal("0.120000"),
        Decimal("0.100000"),
    )


def test_calibration_gate_rejects_wrong_scalar_types_exactly():
    with pytest.raises(ValueError, match="min_observation_count"):
        PaperCalibrationGateConfig(
            config_version="paper-calibration-gate-v0",
            min_observation_count=True,
        )
    with pytest.raises(ValueError, match="max_brier_score"):
        PaperCalibrationGateConfig(
            config_version="paper-calibration-gate-v0",
            max_brier_score=0.25,
        )
    with pytest.raises(ValueError, match="observed_value"):
        PaperCalibrationGateRow(
            "brier_score",
            "passed",
            "brier_score_within_limit",
            True,
            Decimal("0.250000"),
        )
    with pytest.raises(ValueError, match="source_report"):
        build_paper_calibration_gate_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_calibration_gate_report(
            _passing_trend_report(),
            config=_config(),
            generated_at="now",
        )


def test_calibration_gate_normalizes_datetimes_to_utc():
    report = build_paper_calibration_gate_report(
        _passing_trend_report(
            generated_at=datetime(2026, 6, 18, 17, 0, tzinfo=timezone(timedelta(hours=2))),
        ),
        config=_config(),
        generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone(timedelta(hours=-5))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.source_generated_at == datetime(2026, 6, 18, 15, 0, tzinfo=UTC)


def test_calibration_gate_dataclasses_are_frozen_and_revalidate_hard_flags():
    report = build_paper_calibration_gate_report(
        _passing_trend_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.gate_status = "blocked"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_calibration_gate_rejects_source_reports_without_hard_flags(flag_name):
    source_report = _passing_trend_report()
    object.__setattr__(source_report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        build_paper_calibration_gate_report(
            source_report,
            config=_config(),
            generated_at=GENERATED_AT,
        )
