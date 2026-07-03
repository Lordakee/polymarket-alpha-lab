from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_calibration import (
    PaperForecastCalibrationConfig,
    PaperForecastCalibrationReport,
    build_paper_forecast_calibration_report,
)
from polymarket_alpha_lab.forecast_calibration_trend import (
    PaperForecastCalibrationTrendConfig,
    PaperForecastCalibrationTrendReport,
    PaperForecastCalibrationTrendStatusRow,
    build_paper_forecast_calibration_trend_report,
)
from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceObservation


GENERATED_AT = datetime(2026, 6, 18, 15, 0, tzinfo=UTC)
REPORT_STATUSES = (
    "empty_calibration_history",
    "insufficient_calibration_sample",
    "calibration_evidence_observed",
    "calibration_quality_flags",
)


def _config(**overrides) -> PaperForecastCalibrationTrendConfig:
    values = {"config_version": "forecast-calibration-trend-v0"}
    values.update(overrides)
    return PaperForecastCalibrationTrendConfig(**values)


def _probability_observation(
    index: int,
    *,
    probability: Decimal,
    actual: Decimal,
) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=datetime(2026, 6, 1, tzinfo=UTC) + timedelta(days=index),
        source_packet_id=f"packet-{index}",
        condition_id=f"condition-{index % 2}",
        token_id=f"token-{index}",
        market_slug=f"market-{index % 2}",
        strategy_type="relative_value",
        risk_tags=("liquidity",),
        predicted_probability=probability,
        actual_outcome_value=actual,
    )


def _edge_only_observation(index: int) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=datetime(2026, 5, 1, tzinfo=UTC) + timedelta(days=index),
        source_packet_id=f"edge-packet-{index}",
        condition_id=f"edge-condition-{index}",
        token_id=f"edge-token-{index}",
        market_slug=f"edge-market-{index}",
        strategy_type="relative_value",
        risk_tags=("liquidity",),
        theoretical_edge_ratio=Decimal("0.0500"),
        executable_edge_ratio=Decimal("0.0300"),
        fill_probability=Decimal("0.7500"),
        residual_exposure_ratio=Decimal("0.0200"),
        paper_return_ratio=Decimal("0.0100"),
    )


def _calibration_report(
    *,
    generated_at: datetime,
    probabilities: tuple[Decimal, ...],
    actuals: tuple[Decimal, ...],
    min_observation_count: int,
    max_brier_score: Decimal = Decimal("0.250000"),
    max_expected_calibration_error: Decimal = Decimal("0.100000"),
) -> PaperForecastCalibrationReport:
    observations = [
        _probability_observation(index, probability=probability, actual=actual)
        for index, (probability, actual) in enumerate(
            zip(probabilities, actuals, strict=True),
            start=1,
        )
    ]
    return build_paper_forecast_calibration_report(
        observations,
        config=PaperForecastCalibrationConfig(
            config_version="forecast-calibration-v0",
            probability_bucket_width=Decimal("0.5000"),
            min_observation_count=min_observation_count,
            max_brier_score=max_brier_score,
            max_expected_calibration_error=max_expected_calibration_error,
        ),
        generated_at=generated_at,
    )


def _empty_calibration_report(
    generated_at: datetime,
) -> PaperForecastCalibrationReport:
    return build_paper_forecast_calibration_report(
        [_edge_only_observation(1)],
        config=PaperForecastCalibrationConfig(config_version="forecast-calibration-v0"),
        generated_at=generated_at,
    )


def _trend_report(
    *reports: PaperForecastCalibrationReport,
    generated_at: datetime = GENERATED_AT,
) -> PaperForecastCalibrationTrendReport:
    return build_paper_forecast_calibration_trend_report(
        reports,
        config=_config(),
        generated_at=generated_at,
    )


def test_forecast_calibration_trend_reports_empty_sequence_as_readonly_report_only():
    report = _trend_report()

    assert isinstance(report, PaperForecastCalibrationTrendReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "forecast-calibration-trend-v0"
    assert report.calibration_report_count == 0
    assert report.first_report_generated_at is None
    assert report.latest_report_generated_at is None
    assert report.latest_status is None
    assert report.latest_observation_count == 0
    assert report.latest_brier_score is None
    assert report.latest_mean_absolute_error is None
    assert report.latest_expected_calibration_error is None
    assert report.latest_max_bucket_error is None
    assert report.latest_bucket_count == 0
    assert report.worst_observed_brier_score is None
    assert report.worst_observed_expected_calibration_error is None
    assert report.worst_observed_max_bucket_error is None
    assert report.consecutive_insufficient_sample_count == 0
    assert report.consecutive_quality_flag_count == 0
    assert report.status_rows == tuple(
        PaperForecastCalibrationTrendStatusRow(status, 0, None)
        for status in REPORT_STATUSES
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_forecast_calibration_trend_preserves_append_order_latest_and_streaks():
    first_append = _calibration_report(
        generated_at=datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
        probabilities=(Decimal("0.2000"), Decimal("0.8000")),
        actuals=(Decimal("0"), Decimal("1")),
        min_observation_count=2,
        max_expected_calibration_error=Decimal("0.250000"),
    )
    earlier_timestamp = _calibration_report(
        generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        probabilities=(Decimal("0.9000"), Decimal("0.9000")),
        actuals=(Decimal("0"), Decimal("0")),
        min_observation_count=2,
    )
    latest_append = _calibration_report(
        generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
        probabilities=(Decimal("0.8000"), Decimal("0.8000")),
        actuals=(Decimal("0"), Decimal("0")),
        min_observation_count=2,
    )

    report = _trend_report(first_append, earlier_timestamp, latest_append)

    assert report.calibration_report_count == 3
    assert report.first_report_generated_at == first_append.generated_at
    assert report.latest_report_generated_at == latest_append.generated_at
    assert report.latest_status == "calibration_quality_flags"
    assert report.latest_observation_count == 2
    assert report.latest_brier_score == Decimal("0.640000")
    assert report.latest_mean_absolute_error == Decimal("0.800000")
    assert report.latest_expected_calibration_error == Decimal("0.800000")
    assert report.latest_max_bucket_error == Decimal("0.800000")
    assert report.latest_bucket_count == 1
    assert report.worst_observed_brier_score == Decimal("0.810000")
    assert report.worst_observed_expected_calibration_error == Decimal("0.900000")
    assert report.worst_observed_max_bucket_error == Decimal("0.900000")
    assert report.consecutive_insufficient_sample_count == 0
    assert report.consecutive_quality_flag_count == 2


def test_forecast_calibration_trend_counts_status_rows_with_quantized_ratios():
    reports = (
        _empty_calibration_report(datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
        _calibration_report(
            generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
            probabilities=(Decimal("0.8000"), Decimal("0.2000")),
            actuals=(Decimal("1"), Decimal("0")),
            min_observation_count=3,
        ),
        _calibration_report(
            generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
            probabilities=(Decimal("0.8000"), Decimal("0.2000")),
            actuals=(Decimal("1"), Decimal("0")),
            min_observation_count=2,
            max_expected_calibration_error=Decimal("0.250000"),
        ),
        _calibration_report(
            generated_at=datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
            probabilities=(Decimal("0.9000"), Decimal("0.9000")),
            actuals=(Decimal("0"), Decimal("0")),
            min_observation_count=2,
        ),
    )

    report = _trend_report(*reports)

    assert report.latest_status == "calibration_quality_flags"
    assert report.status_rows == (
        PaperForecastCalibrationTrendStatusRow(
            "empty_calibration_history",
            1,
            Decimal("0.250000"),
        ),
        PaperForecastCalibrationTrendStatusRow(
            "insufficient_calibration_sample",
            1,
            Decimal("0.250000"),
        ),
        PaperForecastCalibrationTrendStatusRow(
            "calibration_evidence_observed",
            1,
            Decimal("0.250000"),
        ),
        PaperForecastCalibrationTrendStatusRow(
            "calibration_quality_flags",
            1,
            Decimal("0.250000"),
        ),
    )


def test_forecast_calibration_trend_allocates_non_terminating_status_ratios_exactly():
    reports = (
        _empty_calibration_report(datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
        _calibration_report(
            generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
            probabilities=(Decimal("0.8000"), Decimal("0.2000")),
            actuals=(Decimal("1"), Decimal("0")),
            min_observation_count=3,
        ),
        _calibration_report(
            generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
            probabilities=(Decimal("0.8000"), Decimal("0.2000")),
            actuals=(Decimal("1"), Decimal("0")),
            min_observation_count=2,
            max_expected_calibration_error=Decimal("0.250000"),
        ),
    )

    report = _trend_report(*reports)

    assert tuple(row.report_ratio for row in report.status_rows) == (
        Decimal("0.333334"),
        Decimal("0.333333"),
        Decimal("0.333333"),
        Decimal("0.000000"),
    )
    assert sum((row.report_ratio for row in report.status_rows), Decimal("0")) == Decimal(
        "1.000000"
    )


def test_forecast_calibration_trend_rejects_reports_after_trend_generated_at():
    future_report = _empty_calibration_report(
        datetime(2026, 6, 18, 15, 1, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="latest_report_generated_at"):
        _trend_report(future_report, generated_at=GENERATED_AT)


def test_forecast_calibration_trend_resets_streaks_when_latest_is_observed():
    report = _trend_report(
        _calibration_report(
            generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
            probabilities=(Decimal("0.8000"), Decimal("0.8000")),
            actuals=(Decimal("0"), Decimal("0")),
            min_observation_count=2,
        ),
        _calibration_report(
            generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
            probabilities=(Decimal("0.8000"), Decimal("0.2000")),
            actuals=(Decimal("1"), Decimal("0")),
            min_observation_count=2,
            max_expected_calibration_error=Decimal("0.250000"),
        ),
    )

    assert report.latest_status == "calibration_evidence_observed"
    assert report.consecutive_insufficient_sample_count == 0
    assert report.consecutive_quality_flag_count == 0


def test_forecast_calibration_trend_counts_insufficient_sample_streak():
    report = _trend_report(
        _calibration_report(
            generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
            probabilities=(Decimal("0.8000"), Decimal("0.2000")),
            actuals=(Decimal("1"), Decimal("0")),
            min_observation_count=2,
            max_expected_calibration_error=Decimal("0.250000"),
        ),
        _calibration_report(
            generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
            probabilities=(Decimal("0.8000"), Decimal("0.2000")),
            actuals=(Decimal("1"), Decimal("0")),
            min_observation_count=3,
        ),
        _calibration_report(
            generated_at=datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
            probabilities=(Decimal("0.7000"),),
            actuals=(Decimal("1"),),
            min_observation_count=3,
        ),
    )

    assert report.latest_status == "insufficient_calibration_sample"
    assert report.consecutive_insufficient_sample_count == 2
    assert report.consecutive_quality_flag_count == 0


def test_forecast_calibration_trend_preserves_duplicate_timestamp_append_order():
    generated_at = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    lower_error = _calibration_report(
        generated_at=generated_at,
        probabilities=(Decimal("0.8000"), Decimal("0.2000")),
        actuals=(Decimal("1"), Decimal("0")),
        min_observation_count=2,
        max_expected_calibration_error=Decimal("0.250000"),
    )
    higher_error = _calibration_report(
        generated_at=generated_at,
        probabilities=(Decimal("0.9000"), Decimal("0.9000")),
        actuals=(Decimal("0"), Decimal("0")),
        min_observation_count=2,
    )

    first = _trend_report(lower_error, higher_error)
    second = _trend_report(higher_error, lower_error)

    assert first.latest_brier_score == Decimal("0.810000")
    assert second.latest_brier_score == Decimal("0.040000")
    assert first.worst_observed_brier_score == Decimal("0.810000")
    assert second.worst_observed_brier_score == Decimal("0.810000")


def test_forecast_calibration_trend_normalizes_generated_at_to_utc():
    report = _trend_report(
        generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone(timedelta(hours=-5))),
    )

    assert report.generated_at == GENERATED_AT


def test_forecast_calibration_trend_rejects_invalid_builder_inputs():
    invalid_reports = (
        object(),
        "not reports",
        b"not reports",
        {"report": _empty_calibration_report(GENERATED_AT)},
        (report for report in ()),
    )
    for value in invalid_reports:
        with pytest.raises(ValueError, match="reports must be a list or tuple"):
            build_paper_forecast_calibration_trend_report(
                value,
                config=_config(),
                generated_at=GENERATED_AT,
            )

    with pytest.raises(ValueError, match="PaperForecastCalibrationReport"):
        build_paper_forecast_calibration_trend_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_forecast_calibration_trend_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_forecast_calibration_trend_report(
            (),
            config=_config(),
            generated_at="now",
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_forecast_calibration_trend_rejects_source_reports_with_nonfinal_flags(
    flag_name,
):
    calibration_report = _empty_calibration_report(GENERATED_AT)
    object.__setattr__(calibration_report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        build_paper_forecast_calibration_trend_report(
            (calibration_report,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_forecast_calibration_trend_rejects_source_reports_with_all_hard_flags_false():
    calibration_report = _empty_calibration_report(GENERATED_AT)
    object.__setattr__(calibration_report, "paper_only", False)
    object.__setattr__(calibration_report, "report_only", False)
    object.__setattr__(calibration_report, "readonly", False)

    with pytest.raises(ValueError, match="paper_only"):
        build_paper_forecast_calibration_trend_report(
            (calibration_report,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_forecast_calibration_trend_dataclasses_are_frozen_and_revalidate_flags():
    report = _trend_report(_empty_calibration_report(GENERATED_AT))

    with pytest.raises(FrozenInstanceError):
        report.latest_status = "calibration_evidence_observed"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_forecast_calibration_trend_report_revalidates_empty_consistency():
    report = _trend_report()

    with pytest.raises(ValueError, match="latest_status"):
        replace(report, latest_status="empty_calibration_history")
    with pytest.raises(ValueError, match="latest_observation_count"):
        replace(report, latest_observation_count=1)
    with pytest.raises(ValueError, match="first_report_generated_at"):
        replace(report, first_report_generated_at=GENERATED_AT)


def test_forecast_calibration_trend_report_revalidates_status_rows_and_streaks():
    report = _trend_report(
        _calibration_report(
            generated_at=GENERATED_AT,
            probabilities=(Decimal("0.9000"), Decimal("0.9000")),
            actuals=(Decimal("0"), Decimal("0")),
            min_observation_count=2,
        ),
    )

    with pytest.raises(ValueError, match="status_rows"):
        replace(report, status_rows=tuple(reversed(report.status_rows)))
    drifted_row = replace(report.status_rows[-1])
    object.__setattr__(drifted_row, "report_ratio", Decimal("0.500000"))
    with pytest.raises(ValueError, match="status_rows ratios"):
        replace(
            report,
            status_rows=(
                *report.status_rows[:-1],
                drifted_row,
            ),
        )
    with pytest.raises(ValueError, match="quality flag streak"):
        replace(report, consecutive_quality_flag_count=0)


def test_forecast_calibration_trend_revalidates_latest_status_row_membership():
    report = _trend_report(
        _calibration_report(
            generated_at=GENERATED_AT,
            probabilities=(Decimal("0.9000"), Decimal("0.9000")),
            actuals=(Decimal("0"), Decimal("0")),
            min_observation_count=2,
        ),
    )
    rows_without_latest = (
        PaperForecastCalibrationTrendStatusRow(
            "empty_calibration_history",
            1,
            Decimal("1.000000"),
        ),
        PaperForecastCalibrationTrendStatusRow(
            "insufficient_calibration_sample",
            0,
            Decimal("0.000000"),
        ),
        PaperForecastCalibrationTrendStatusRow(
            "calibration_evidence_observed",
            0,
            Decimal("0.000000"),
        ),
        PaperForecastCalibrationTrendStatusRow(
            "calibration_quality_flags",
            0,
            Decimal("0.000000"),
        ),
    )

    with pytest.raises(ValueError, match="latest_status"):
        replace(report, status_rows=rows_without_latest)


def test_forecast_calibration_trend_revalidates_streaks_against_status_rows():
    first = _calibration_report(
        generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        probabilities=(Decimal("0.8000"), Decimal("0.8000")),
        actuals=(Decimal("0"), Decimal("0")),
        min_observation_count=2,
    )
    latest = _calibration_report(
        generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
        probabilities=(Decimal("0.9000"), Decimal("0.9000")),
        actuals=(Decimal("0"), Decimal("0")),
        min_observation_count=2,
    )
    report = _trend_report(first, latest)

    with pytest.raises(ValueError, match="quality flag streak"):
        replace(report, consecutive_quality_flag_count=3)


def test_forecast_calibration_trend_revalidates_latest_status_metrics():
    report = _trend_report(_empty_calibration_report(GENERATED_AT))

    with pytest.raises(ValueError, match="latest_observation_count"):
        replace(
            report,
            latest_status="calibration_quality_flags",
            latest_observation_count=0,
            latest_brier_score=None,
            latest_mean_absolute_error=None,
            latest_expected_calibration_error=None,
            latest_max_bucket_error=None,
            latest_bucket_count=0,
            worst_observed_brier_score=None,
            worst_observed_expected_calibration_error=None,
            worst_observed_max_bucket_error=None,
            consecutive_quality_flag_count=1,
            status_rows=(
                PaperForecastCalibrationTrendStatusRow(
                    "empty_calibration_history",
                    0,
                    Decimal("0.000000"),
                ),
                PaperForecastCalibrationTrendStatusRow(
                    "insufficient_calibration_sample",
                    0,
                    Decimal("0.000000"),
                ),
                PaperForecastCalibrationTrendStatusRow(
                    "calibration_evidence_observed",
                    0,
                    Decimal("0.000000"),
                ),
                PaperForecastCalibrationTrendStatusRow(
                    "calibration_quality_flags",
                    1,
                    Decimal("1.000000"),
                ),
            ),
        )


def test_forecast_calibration_trend_revalidates_metric_decimal_precision():
    report = _trend_report(
        _calibration_report(
            generated_at=GENERATED_AT,
            probabilities=(Decimal("0.8000"), Decimal("0.2000")),
            actuals=(Decimal("1"), Decimal("0")),
            min_observation_count=2,
            max_expected_calibration_error=Decimal("0.250000"),
        ),
    )

    compatible = replace(report, latest_brier_score=Decimal("0.0400000"))
    assert compatible.latest_brier_score == Decimal("0.0400000")

    with pytest.raises(ValueError, match="latest_brier_score"):
        replace(report, latest_brier_score=Decimal("0.0400004"))


def test_forecast_calibration_trend_config_rows_and_all_are_exact():
    from polymarket_alpha_lab import forecast_calibration_trend

    assert forecast_calibration_trend.__all__ == (
        "PaperForecastCalibrationTrendConfig",
        "PaperForecastCalibrationTrendStatusRow",
        "PaperForecastCalibrationTrendReport",
        "build_paper_forecast_calibration_trend_report",
    )

    with pytest.raises(ValueError, match="config_version"):
        PaperForecastCalibrationTrendConfig(config_version=" forecast-calibration-trend-v0 ")
    with pytest.raises(ValueError, match="config paper_only must be True"):
        PaperForecastCalibrationTrendConfig(
            config_version="forecast-calibration-trend-v0",
            paper_only=False,
        )
    with pytest.raises(ValueError, match="calibration_status"):
        PaperForecastCalibrationTrendStatusRow("unknown", 0, None)
    with pytest.raises(ValueError, match="status row readonly must be True"):
        PaperForecastCalibrationTrendStatusRow(
            "calibration_evidence_observed",
            1,
            Decimal("1.000000"),
            readonly=False,
        )
    with pytest.raises(ValueError, match="report_ratio"):
        PaperForecastCalibrationTrendStatusRow(
            "calibration_evidence_observed",
            1,
            Decimal("0.1000004"),
        )
