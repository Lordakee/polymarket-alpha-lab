from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_calibration import (
    PaperForecastCalibrationBucket,
    PaperForecastCalibrationConfig,
    PaperForecastCalibrationReport,
    build_paper_forecast_calibration_report,
)
from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceObservation


GENERATED_AT = datetime(2026, 9, 10, tzinfo=UTC)


def probability_observation(
    index: int,
    *,
    probability: Decimal,
    actual: Decimal,
) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=datetime(2026, 9, 1, tzinfo=UTC) + timedelta(days=index),
        source_packet_id=f"packet-{index}",
        condition_id=f"condition-{index % 2}",
        token_id=f"token-{index}",
        market_slug=f"market-{index % 2}",
        strategy_type="relative_value",
        risk_tags=("liquidity",),
        predicted_probability=probability,
        actual_outcome_value=actual,
    )


def edge_only_observation(index: int) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=datetime(2026, 8, 1, tzinfo=UTC) + timedelta(days=index),
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


def valid_calibration_report() -> PaperForecastCalibrationReport:
    return build_paper_forecast_calibration_report(
        [
            probability_observation(1, probability=Decimal("0.2000"), actual=Decimal("0")),
            probability_observation(2, probability=Decimal("0.7000"), actual=Decimal("1")),
        ],
        config=PaperForecastCalibrationConfig(
            config_version="calibration-test",
            probability_bucket_width=Decimal("0.5000"),
            min_observation_count=2,
        ),
        generated_at=GENERATED_AT,
    )


def test_build_paper_forecast_calibration_report_summarizes_resolved_probabilities():
    first = probability_observation(
        1,
        probability=Decimal("0.8000"),
        actual=Decimal("1"),
    )
    second = probability_observation(
        2,
        probability=Decimal("0.2000"),
        actual=Decimal("0"),
    )
    third = probability_observation(
        3,
        probability=Decimal("0.6000"),
        actual=Decimal("0"),
    )

    report = build_paper_forecast_calibration_report(
        [third, edge_only_observation(99), second, first],
        config=PaperForecastCalibrationConfig(
            config_version="calibration-test",
            probability_bucket_width=Decimal("0.5000"),
            min_observation_count=3,
            max_brier_score=Decimal("0.150000"),
            max_expected_calibration_error=Decimal("0.250000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperForecastCalibrationReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "calibration-test"
    assert report.observation_count == 3
    assert report.first_observed_at == first.observed_at
    assert report.last_observed_at == third.observed_at
    assert report.brier_score == Decimal("0.146667")
    assert report.mean_absolute_error == Decimal("0.333333")
    assert report.expected_calibration_error == Decimal("0.200000")
    assert report.max_bucket_error == Decimal("0.200000")
    assert report.bucket_count == 2
    assert report.status == "calibration_evidence_observed"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [bucket.bucket_label for bucket in report.buckets] == [
        "0.0000-0.5000",
        "0.5000-1.0000",
    ]
    assert report.buckets[0].observation_count == 1
    assert report.buckets[0].mean_predicted_probability == Decimal("0.200000")
    assert report.buckets[0].observed_frequency == Decimal("0.000000")
    assert report.buckets[0].bucket_error == Decimal("0.200000")
    assert report.buckets[0].bucket_weight == Decimal("0.333333")
    assert report.buckets[1].observation_count == 2
    assert report.buckets[1].mean_predicted_probability == Decimal("0.700000")
    assert report.buckets[1].observed_frequency == Decimal("0.500000")
    assert report.buckets[1].bucket_error == Decimal("0.200000")
    assert report.buckets[1].bucket_weight == Decimal("0.666667")


def test_build_paper_forecast_calibration_report_handles_empty_calibration_history():
    report = build_paper_forecast_calibration_report(
        [edge_only_observation(1)],
        config=PaperForecastCalibrationConfig(config_version="calibration-test"),
        generated_at=GENERATED_AT,
    )

    assert report.observation_count == 0
    assert report.first_observed_at is None
    assert report.last_observed_at is None
    assert report.brier_score is None
    assert report.mean_absolute_error is None
    assert report.expected_calibration_error is None
    assert report.max_bucket_error is None
    assert report.bucket_count == 0
    assert report.buckets == ()
    assert report.status == "empty_calibration_history"


def test_build_paper_forecast_calibration_report_marks_insufficient_evidence_before_threshold():
    report = build_paper_forecast_calibration_report(
        [
            probability_observation(1, probability=Decimal("0.8000"), actual=Decimal("1")),
            probability_observation(2, probability=Decimal("0.2000"), actual=Decimal("0")),
        ],
        config=PaperForecastCalibrationConfig(
            config_version="calibration-test",
            min_observation_count=3,
        ),
        generated_at=GENERATED_AT,
    )

    assert report.observation_count == 2
    assert report.brier_score == Decimal("0.040000")
    assert report.expected_calibration_error == Decimal("0.200000")
    assert report.status == "insufficient_calibration_sample"


def test_build_paper_forecast_calibration_report_emits_exact_total_bucket_weight():
    report = build_paper_forecast_calibration_report(
        [
            probability_observation(1, probability=Decimal("0.1000"), actual=Decimal("0")),
            probability_observation(2, probability=Decimal("0.5000"), actual=Decimal("1")),
            probability_observation(3, probability=Decimal("0.9000"), actual=Decimal("1")),
        ],
        config=PaperForecastCalibrationConfig(
            config_version="calibration-test",
            probability_bucket_width=Decimal("0.2000"),
            min_observation_count=3,
        ),
        generated_at=GENERATED_AT,
    )

    assert report.observation_count == 3
    assert report.bucket_count == 3
    assert sum((bucket.bucket_weight for bucket in report.buckets), Decimal("0")) == Decimal(
        "1.000000"
    )


def test_build_paper_forecast_calibration_report_marks_drift_after_threshold_breach():
    report = build_paper_forecast_calibration_report(
        [
            probability_observation(index, probability=Decimal("0.9000"), actual=Decimal("0"))
            for index in range(3)
        ],
        config=PaperForecastCalibrationConfig(
            config_version="calibration-test",
            min_observation_count=3,
            max_brier_score=Decimal("0.250000"),
            max_expected_calibration_error=Decimal("0.100000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.observation_count == 3
    assert report.brier_score == Decimal("0.810000")
    assert report.expected_calibration_error == Decimal("0.900000")
    assert report.status == "calibration_quality_flags"


def test_build_paper_forecast_calibration_report_uses_utc_bounds_and_final_one_bucket():
    first = probability_observation(
        1,
        probability=Decimal("0.9000"),
        actual=Decimal("1"),
    )
    last = replace(
        probability_observation(
            2,
            probability=Decimal("1.0000"),
            actual=Decimal("1"),
        ),
        observed_at=datetime(2026, 9, 2, 20, tzinfo=timezone(timedelta(hours=-4))),
    )

    report = build_paper_forecast_calibration_report(
        [last, first],
        config=PaperForecastCalibrationConfig(
            config_version="calibration-test",
            probability_bucket_width=Decimal("0.3000"),
            min_observation_count=2,
        ),
        generated_at=datetime(2026, 9, 10, 8, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == datetime(2026, 9, 10, 12, tzinfo=UTC)
    assert report.first_observed_at == first.observed_at
    assert report.last_observed_at == datetime(2026, 9, 3, tzinfo=UTC)
    assert [bucket.bucket_label for bucket in report.buckets] == ["0.9000-1.0000"]
    assert report.buckets[0].observation_count == 2
    assert report.buckets[0].mean_predicted_probability == Decimal("0.950000")
    assert report.buckets[0].observed_frequency == Decimal("1.000000")
    assert report.buckets[0].bucket_error == Decimal("0.050000")


def test_forecast_calibration_dataclasses_reject_invalid_inputs_and_flags():
    with pytest.raises(ValueError, match="config_version"):
        PaperForecastCalibrationConfig(config_version=" ")
    with pytest.raises(ValueError, match="probability_bucket_width"):
        PaperForecastCalibrationConfig(
            config_version="calibration-test",
            probability_bucket_width=Decimal("0"),
        )
    with pytest.raises(ValueError, match="probability_bucket_width"):
        PaperForecastCalibrationConfig(
            config_version="calibration-test",
            probability_bucket_width=Decimal("0.00001"),
        )
    with pytest.raises(ValueError, match="max_brier_score"):
        PaperForecastCalibrationConfig(
            config_version="calibration-test",
            max_brier_score=1,
        )
    with pytest.raises(ValueError, match="max_brier_score"):
        PaperForecastCalibrationConfig(
            config_version="calibration-test",
            max_brier_score=Decimal("0.2500004"),
        )
    with pytest.raises(ValueError, match="max_expected_calibration_error"):
        PaperForecastCalibrationConfig(
            config_version="calibration-test",
            max_expected_calibration_error=Decimal("0.1000004"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            build_paper_forecast_calibration_report(
                [
                    probability_observation(
                        1,
                        probability=Decimal("0.8000"),
                        actual=Decimal("1"),
                    )
                ],
                config=PaperForecastCalibrationConfig(config_version="calibration-test"),
                generated_at=GENERATED_AT,
            ),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(
            build_paper_forecast_calibration_report(
                [
                    probability_observation(
                        1,
                        probability=Decimal("0.8000"),
                        actual=Decimal("1"),
                    )
                ],
                config=PaperForecastCalibrationConfig(config_version="calibration-test"),
                generated_at=GENERATED_AT,
            ),
            report_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(
            build_paper_forecast_calibration_report(
                [
                    probability_observation(
                        1,
                        probability=Decimal("0.8000"),
                        actual=Decimal("1"),
                    )
                ],
                config=PaperForecastCalibrationConfig(config_version="calibration-test"),
                generated_at=GENERATED_AT,
            ),
            readonly=False,
        )


def test_forecast_calibration_report_rejects_duplicate_bucket_identity():
    report = valid_calibration_report()
    duplicate_bucket = replace(
        report.buckets[0],
        observation_count=1,
        mean_predicted_probability=Decimal("0.300000"),
        bucket_error=Decimal("0.300000"),
        bucket_weight=Decimal("0.500000"),
    )

    with pytest.raises(ValueError, match="bucket identity"):
        replace(
            report,
            bucket_count=3,
            buckets=(report.buckets[0], duplicate_bucket, report.buckets[1]),
        )


def test_forecast_calibration_report_rejects_overlapping_buckets():
    report = valid_calibration_report()
    overlapping_first = replace(
        report.buckets[0],
        upper_probability=Decimal("0.6000"),
        bucket_label="0.0000-0.6000",
    )

    with pytest.raises(ValueError, match="overlap"):
        replace(report, buckets=(overlapping_first, report.buckets[1]))


def test_forecast_calibration_report_rejects_same_lower_different_upper_buckets():
    report = valid_calibration_report()
    same_lower_bucket = replace(
        report.buckets[1],
        lower_probability=report.buckets[0].lower_probability,
        upper_probability=Decimal("0.7500"),
        bucket_label="0.0000-0.7500",
    )

    with pytest.raises(ValueError, match="overlap"):
        replace(report, buckets=(report.buckets[0], same_lower_bucket))


def test_forecast_calibration_report_rejects_unsorted_bucket_ranges():
    report = valid_calibration_report()
    later_bucket = replace(
        report.buckets[1],
        lower_probability=Decimal("0.1000"),
        upper_probability=Decimal("0.4000"),
        bucket_label="0.1000-0.4000",
    )

    with pytest.raises(ValueError, match="sorted"):
        replace(report, buckets=(later_bucket, report.buckets[0]))


def test_forecast_calibration_report_rejects_bucket_observation_count_mismatch():
    report = valid_calibration_report()
    mismatched_bucket = replace(report.buckets[0], observation_count=2)

    with pytest.raises(ValueError, match="bucket observation_count"):
        replace(report, buckets=(mismatched_bucket, report.buckets[1]))


def test_forecast_calibration_report_rejects_bucket_weight_sum_mismatch():
    report = valid_calibration_report()
    overweight_bucket = replace(report.buckets[0], bucket_weight=Decimal("0.750000"))

    with pytest.raises(ValueError, match="bucket weights"):
        replace(report, buckets=(overweight_bucket, report.buckets[1]))


def test_forecast_calibration_report_rejects_near_exact_bucket_weight_sum():
    report = valid_calibration_report()
    near_exact_bucket = replace(report.buckets[1], bucket_weight=Decimal("0.666666"))

    with pytest.raises(ValueError, match="bucket weights"):
        replace(report, buckets=(report.buckets[0], near_exact_bucket))


def test_forecast_calibration_bucket_rejects_complementary_subquantum_weights():
    with pytest.raises(ValueError, match="bucket_weight"):
        PaperForecastCalibrationBucket(
            bucket_label="0.0000-0.5000",
            lower_probability=Decimal("0.0000"),
            upper_probability=Decimal("0.5000"),
            observation_count=1,
            mean_predicted_probability=Decimal("0.200000"),
            observed_frequency=Decimal("0.000000"),
            bucket_error=Decimal("0.200000"),
            bucket_weight=Decimal("0.5000004"),
        )


def test_forecast_calibration_bucket_rejects_subquantum_fields_and_label_mismatch():
    with pytest.raises(ValueError, match="lower_probability"):
        replace(valid_calibration_report().buckets[0], lower_probability=Decimal("0.00001"))

    with pytest.raises(ValueError, match="mean_predicted_probability"):
        replace(
            valid_calibration_report().buckets[0],
            mean_predicted_probability=Decimal("0.2000004"),
        )

    with pytest.raises(ValueError, match="bucket_label"):
        replace(valid_calibration_report().buckets[0], bucket_label="mismatched")


def test_forecast_calibration_allocates_bucket_weights_without_negative_residual():
    from polymarket_alpha_lab.forecast_calibration import _bucket_weights_from_counts

    weights = _bucket_weights_from_counts((3334682, 3702383, 2962953, 1))

    assert len(weights) == 4
    assert all(weight >= Decimal("0.000000") for weight in weights)
    assert all(weight == weight.quantize(Decimal("0.000001")) for weight in weights)
    assert sum(weights, Decimal("0")) == Decimal("1.000000")


def test_forecast_calibration_report_direct_construction_rejects_bucket_invariants():
    bucket = PaperForecastCalibrationBucket(
        bucket_label="0.0000-0.5000",
        lower_probability=Decimal("0.0000"),
        upper_probability=Decimal("0.5000"),
        observation_count=1,
        mean_predicted_probability=Decimal("0.200000"),
        observed_frequency=Decimal("0.000000"),
        bucket_error=Decimal("0.200000"),
        bucket_weight=Decimal("0.500000"),
    )

    with pytest.raises(ValueError, match="bucket weights"):
        PaperForecastCalibrationReport(
            generated_at=GENERATED_AT,
            config_version="calibration-test",
            observation_count=1,
            first_observed_at=datetime(2026, 9, 1, tzinfo=UTC),
            last_observed_at=datetime(2026, 9, 1, tzinfo=UTC),
            brier_score=Decimal("0.040000"),
            mean_absolute_error=Decimal("0.200000"),
            expected_calibration_error=Decimal("0.200000"),
            max_bucket_error=Decimal("0.200000"),
            bucket_count=1,
            status="calibration_evidence_observed",
            buckets=(bucket,),
        )


def test_forecast_calibration_report_rejects_subquantum_report_metrics():
    report = valid_calibration_report()

    with pytest.raises(ValueError, match="brier_score"):
        replace(report, brier_score=Decimal("0.0400004"))
    with pytest.raises(ValueError, match="expected_calibration_error"):
        replace(report, expected_calibration_error=Decimal("0.2000004"))


def test_forecast_calibration_report_rejects_out_of_domain_metrics():
    report = valid_calibration_report()

    with pytest.raises(ValueError, match="brier_score"):
        replace(report, brier_score=Decimal("2.000000"))
    with pytest.raises(ValueError, match="bucket_error"):
        replace(report.buckets[0], bucket_error=Decimal("2.000000"))


def test_forecast_calibration_report_rejects_status_time_and_bucket_metric_mismatches():
    report = valid_calibration_report()

    with pytest.raises(ValueError, match="status"):
        replace(report, status="empty_calibration_history")
    with pytest.raises(ValueError, match="observed_at bounds"):
        replace(report, first_observed_at=report.last_observed_at + timedelta(days=1))
    with pytest.raises(ValueError, match="expected_calibration_error"):
        replace(report, expected_calibration_error=Decimal("0.100000"))
    with pytest.raises(ValueError, match="max_bucket_error"):
        replace(report, max_bucket_error=Decimal("0.100000"))


def test_forecast_calibration_dataclasses_are_frozen():
    report = build_paper_forecast_calibration_report(
        [probability_observation(1, probability=Decimal("0.8000"), actual=Decimal("1"))],
        config=PaperForecastCalibrationConfig(config_version="calibration-test"),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.observation_count = 0
    with pytest.raises(FrozenInstanceError):
        report.buckets[0].bucket_error = Decimal("0")


def test_build_paper_forecast_calibration_report_rejects_bad_public_inputs():
    observation = probability_observation(
        1,
        probability=Decimal("0.8000"),
        actual=Decimal("1"),
    )
    config = PaperForecastCalibrationConfig(config_version="calibration-test")

    with pytest.raises(ValueError, match="observations"):
        build_paper_forecast_calibration_report(
            "not-observations",
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PaperForecastEvidenceObservation"):
        build_paper_forecast_calibration_report(
            [object()],
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_forecast_calibration_report(
            [observation],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_forecast_calibration_report(
            [observation],
            config=config,
            generated_at=None,
        )
