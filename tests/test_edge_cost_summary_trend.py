from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.edge_cost_summary import PaperEdgeCostSummaryReport
from polymarket_alpha_lab.edge_cost_summary_trend import (
    PaperEdgeCostSummaryTrendConfig,
    PaperEdgeCostSummaryTrendReport,
    PaperEdgeCostSummaryTrendStatusRow,
    build_paper_edge_cost_summary_trend_report,
)


GENERATED_AT = datetime(2026, 6, 18, 16, 0, tzinfo=UTC)
EDGE_COST_SUMMARY_STATUSES = (
    "empty_edge_cost_history",
    "insufficient_edge_cost_sample",
    "edge_cost_evidence_observed",
    "edge_cost_quality_flags",
)


def _config(**overrides) -> PaperEdgeCostSummaryTrendConfig:
    values = {"config_version": "edge-cost-summary-trend-v0"}
    values.update(overrides)
    return PaperEdgeCostSummaryTrendConfig(**values)


def _summary_report(**overrides) -> PaperEdgeCostSummaryReport:
    values = {
        "generated_at": datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        "config_version": "edge-cost-summary-v0",
        "edge_observation_count": 4,
        "first_observed_at": datetime(2026, 6, 1, tzinfo=UTC),
        "last_observed_at": datetime(2026, 6, 4, tzinfo=UTC),
        "mean_theoretical_edge_ratio": Decimal("0.080000"),
        "mean_executable_edge_ratio": Decimal("0.050000"),
        "mean_edge_cost_drag": Decimal("0.030000"),
        "mean_fill_probability": Decimal("0.750000"),
        "mean_residual_exposure_ratio": Decimal("0.100000"),
        "mean_paper_return_ratio": Decimal("0.010000"),
        "negative_executable_edge_count": 0,
        "negative_executable_edge_rate": Decimal("0.000000"),
        "low_fill_probability_count": 0,
        "low_fill_probability_rate": Decimal("0.000000"),
        "high_residual_exposure_count": 0,
        "high_residual_exposure_rate": Decimal("0.000000"),
        "positive_paper_return_count": 3,
        "positive_paper_return_rate": Decimal("0.750000"),
        "status": "edge_cost_evidence_observed",
    }
    values.update(overrides)
    if (
        "mean_edge_cost_drag" in overrides
        and "mean_theoretical_edge_ratio" not in overrides
        and "mean_executable_edge_ratio" not in overrides
    ):
        values["mean_theoretical_edge_ratio"] = (
            values["mean_executable_edge_ratio"] + values["mean_edge_cost_drag"]
        ).quantize(Decimal("0.000001"))
    elif "mean_edge_cost_drag" in overrides and "mean_executable_edge_ratio" not in overrides:
        values["mean_executable_edge_ratio"] = (
            values["mean_theoretical_edge_ratio"] - values["mean_edge_cost_drag"]
        ).quantize(Decimal("0.000001"))
    return PaperEdgeCostSummaryReport(**values)


def _empty_summary_report(generated_at: datetime = GENERATED_AT) -> PaperEdgeCostSummaryReport:
    return PaperEdgeCostSummaryReport(
        generated_at=generated_at,
        config_version="edge-cost-summary-v0",
        edge_observation_count=0,
        first_observed_at=None,
        last_observed_at=None,
        mean_theoretical_edge_ratio=None,
        mean_executable_edge_ratio=None,
        mean_edge_cost_drag=None,
        mean_fill_probability=None,
        mean_residual_exposure_ratio=None,
        mean_paper_return_ratio=None,
        negative_executable_edge_count=0,
        negative_executable_edge_rate=None,
        low_fill_probability_count=0,
        low_fill_probability_rate=None,
        high_residual_exposure_count=0,
        high_residual_exposure_rate=None,
        positive_paper_return_count=0,
        positive_paper_return_rate=None,
        status="empty_edge_cost_history",
    )


def _trend_report(
    *reports: PaperEdgeCostSummaryReport,
    generated_at: datetime = GENERATED_AT,
) -> PaperEdgeCostSummaryTrendReport:
    return build_paper_edge_cost_summary_trend_report(
        reports,
        config=_config(),
        generated_at=generated_at,
    )


def test_edge_cost_summary_trend_reports_empty_sequence_as_readonly_report_only():
    report = _trend_report()

    assert isinstance(report, PaperEdgeCostSummaryTrendReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "edge-cost-summary-trend-v0"
    assert report.edge_cost_report_count == 0
    assert report.first_report_generated_at is None
    assert report.latest_report_generated_at is None
    assert report.latest_status is None
    assert report.latest_edge_observation_count == 0
    assert report.latest_mean_theoretical_edge_ratio is None
    assert report.latest_mean_executable_edge_ratio is None
    assert report.latest_mean_edge_cost_drag is None
    assert report.latest_mean_fill_probability is None
    assert report.latest_mean_residual_exposure_ratio is None
    assert report.latest_mean_paper_return_ratio is None
    assert report.latest_negative_executable_edge_count == 0
    assert report.latest_negative_executable_edge_rate is None
    assert report.latest_low_fill_probability_count == 0
    assert report.latest_low_fill_probability_rate is None
    assert report.latest_high_residual_exposure_count == 0
    assert report.latest_high_residual_exposure_rate is None
    assert report.latest_positive_paper_return_count == 0
    assert report.latest_positive_paper_return_rate is None
    assert report.largest_negative_executable_edge_count == 0
    assert report.largest_low_fill_probability_count == 0
    assert report.largest_high_residual_exposure_count == 0
    assert report.worst_observed_mean_edge_cost_drag is None
    assert report.worst_observed_mean_residual_exposure_ratio is None
    assert report.consecutive_quality_flag_count == 0
    assert report.consecutive_insufficient_sample_count == 0
    assert report.status_rows == tuple(
        PaperEdgeCostSummaryTrendStatusRow(status, 0, None)
        for status in EDGE_COST_SUMMARY_STATUSES
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_edge_cost_summary_trend_preserves_append_order_latest_and_streaks():
    first_append = _summary_report(
        generated_at=datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
        edge_observation_count=3,
        mean_theoretical_edge_ratio=Decimal("0.040000"),
        mean_executable_edge_ratio=Decimal("0.020000"),
        mean_edge_cost_drag=Decimal("0.020000"),
        mean_fill_probability=Decimal("0.700000"),
        mean_residual_exposure_ratio=Decimal("0.120000"),
        mean_paper_return_ratio=Decimal("0.005000"),
        positive_paper_return_count=2,
        positive_paper_return_rate=Decimal("0.666667"),
    )
    earlier_timestamp = _summary_report(
        generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        edge_observation_count=5,
        mean_theoretical_edge_ratio=Decimal("0.090000"),
        mean_executable_edge_ratio=Decimal("0.020000"),
        mean_edge_cost_drag=Decimal("0.070000"),
        mean_fill_probability=Decimal("0.550000"),
        mean_residual_exposure_ratio=Decimal("0.400000"),
        mean_paper_return_ratio=Decimal("-0.010000"),
        negative_executable_edge_count=2,
        negative_executable_edge_rate=Decimal("0.400000"),
        low_fill_probability_count=1,
        low_fill_probability_rate=Decimal("0.200000"),
        high_residual_exposure_count=3,
        high_residual_exposure_rate=Decimal("0.600000"),
        positive_paper_return_count=1,
        positive_paper_return_rate=Decimal("0.200000"),
        status="edge_cost_quality_flags",
    )
    latest_append = _summary_report(
        generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
        edge_observation_count=4,
        mean_theoretical_edge_ratio=Decimal("0.070000"),
        mean_executable_edge_ratio=Decimal("-0.010000"),
        mean_edge_cost_drag=Decimal("0.080000"),
        mean_fill_probability=Decimal("0.450000"),
        mean_residual_exposure_ratio=Decimal("0.300000"),
        mean_paper_return_ratio=Decimal("-0.020000"),
        negative_executable_edge_count=1,
        negative_executable_edge_rate=Decimal("0.250000"),
        low_fill_probability_count=2,
        low_fill_probability_rate=Decimal("0.500000"),
        high_residual_exposure_count=1,
        high_residual_exposure_rate=Decimal("0.250000"),
        positive_paper_return_count=1,
        positive_paper_return_rate=Decimal("0.250000"),
        status="edge_cost_quality_flags",
    )

    report = _trend_report(first_append, earlier_timestamp, latest_append)

    assert report.edge_cost_report_count == 3
    assert report.first_report_generated_at == first_append.generated_at
    assert report.latest_report_generated_at == latest_append.generated_at
    assert report.latest_status == "edge_cost_quality_flags"
    assert report.latest_edge_observation_count == 4
    assert report.latest_mean_theoretical_edge_ratio == Decimal("0.070000")
    assert report.latest_mean_executable_edge_ratio == Decimal("-0.010000")
    assert report.latest_mean_edge_cost_drag == Decimal("0.080000")
    assert report.latest_mean_fill_probability == Decimal("0.450000")
    assert report.latest_mean_residual_exposure_ratio == Decimal("0.300000")
    assert report.latest_mean_paper_return_ratio == Decimal("-0.020000")
    assert report.latest_negative_executable_edge_count == 1
    assert report.latest_negative_executable_edge_rate == Decimal("0.250000")
    assert report.latest_low_fill_probability_count == 2
    assert report.latest_low_fill_probability_rate == Decimal("0.500000")
    assert report.latest_high_residual_exposure_count == 1
    assert report.latest_high_residual_exposure_rate == Decimal("0.250000")
    assert report.latest_positive_paper_return_count == 1
    assert report.latest_positive_paper_return_rate == Decimal("0.250000")
    assert report.largest_negative_executable_edge_count == 2
    assert report.largest_low_fill_probability_count == 2
    assert report.largest_high_residual_exposure_count == 3
    assert report.worst_observed_mean_edge_cost_drag == Decimal("0.080000")
    assert report.worst_observed_mean_residual_exposure_ratio == Decimal("0.400000")
    assert report.consecutive_quality_flag_count == 2
    assert report.consecutive_insufficient_sample_count == 0


def test_edge_cost_summary_trend_counts_status_rows_with_quantized_ratios():
    reports = (
        _empty_summary_report(datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
        _summary_report(
            generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
            edge_observation_count=1,
            positive_paper_return_count=1,
            positive_paper_return_rate=Decimal("1.000000"),
            status="insufficient_edge_cost_sample",
        ),
        _summary_report(
            generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
        ),
        _summary_report(
            generated_at=datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
            edge_observation_count=2,
            negative_executable_edge_count=1,
            negative_executable_edge_rate=Decimal("0.500000"),
            low_fill_probability_count=1,
            low_fill_probability_rate=Decimal("0.500000"),
            positive_paper_return_count=1,
            positive_paper_return_rate=Decimal("0.500000"),
            status="edge_cost_quality_flags",
        ),
    )

    report = _trend_report(*reports)

    assert report.status_rows == (
        PaperEdgeCostSummaryTrendStatusRow(
            "empty_edge_cost_history",
            1,
            Decimal("0.250000"),
        ),
        PaperEdgeCostSummaryTrendStatusRow(
            "insufficient_edge_cost_sample",
            1,
            Decimal("0.250000"),
        ),
        PaperEdgeCostSummaryTrendStatusRow(
            "edge_cost_evidence_observed",
            1,
            Decimal("0.250000"),
        ),
        PaperEdgeCostSummaryTrendStatusRow(
            "edge_cost_quality_flags",
            1,
            Decimal("0.250000"),
        ),
    )


def test_edge_cost_summary_trend_canonicalizes_valid_source_rate_decimals():
    source_report = _summary_report(
        edge_observation_count=2,
        negative_executable_edge_count=1,
        negative_executable_edge_rate=Decimal("0.5"),
        low_fill_probability_count=1,
        low_fill_probability_rate=Decimal("0.5"),
        high_residual_exposure_count=1,
        high_residual_exposure_rate=Decimal("0.5"),
        positive_paper_return_count=1,
        positive_paper_return_rate=Decimal("0.5"),
        status="edge_cost_quality_flags",
    )

    report = _trend_report(source_report)

    assert report.latest_negative_executable_edge_rate == Decimal("0.500000")
    assert report.latest_low_fill_probability_rate == Decimal("0.500000")
    assert report.latest_high_residual_exposure_rate == Decimal("0.500000")
    assert report.latest_positive_paper_return_rate == Decimal("0.500000")


def test_edge_cost_summary_trend_counts_insufficient_sample_streak():
    report = _trend_report(
        _summary_report(
            generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
            status="edge_cost_evidence_observed",
        ),
        _summary_report(
            generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
            edge_observation_count=2,
            positive_paper_return_count=1,
            positive_paper_return_rate=Decimal("0.500000"),
            status="insufficient_edge_cost_sample",
        ),
        _summary_report(
            generated_at=datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
            edge_observation_count=1,
            positive_paper_return_count=0,
            positive_paper_return_rate=Decimal("0.000000"),
            status="insufficient_edge_cost_sample",
        ),
    )

    assert report.latest_status == "insufficient_edge_cost_sample"
    assert report.consecutive_insufficient_sample_count == 2
    assert report.consecutive_quality_flag_count == 0


def test_edge_cost_summary_trend_resets_streaks_when_latest_is_observed():
    report = _trend_report(
        _summary_report(
            generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
            negative_executable_edge_count=1,
            negative_executable_edge_rate=Decimal("0.250000"),
            status="edge_cost_quality_flags",
        ),
        _summary_report(
            generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
            status="edge_cost_evidence_observed",
        ),
    )

    assert report.latest_status == "edge_cost_evidence_observed"
    assert report.consecutive_quality_flag_count == 0
    assert report.consecutive_insufficient_sample_count == 0


def test_edge_cost_summary_trend_preserves_duplicate_timestamp_append_order():
    generated_at = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    lower_drag = _summary_report(
        generated_at=generated_at,
        mean_edge_cost_drag=Decimal("0.010000"),
        mean_residual_exposure_ratio=Decimal("0.200000"),
    )
    higher_drag = _summary_report(
        generated_at=generated_at,
        mean_edge_cost_drag=Decimal("0.090000"),
        mean_residual_exposure_ratio=Decimal("0.300000"),
    )

    first = _trend_report(lower_drag, higher_drag)
    second = _trend_report(higher_drag, lower_drag)

    assert first.latest_mean_edge_cost_drag == Decimal("0.090000")
    assert second.latest_mean_edge_cost_drag == Decimal("0.010000")
    assert first.worst_observed_mean_edge_cost_drag == Decimal("0.090000")
    assert second.worst_observed_mean_edge_cost_drag == Decimal("0.090000")


def test_edge_cost_summary_trend_keeps_historical_worsts_when_latest_is_empty():
    observed = _summary_report(
        generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        mean_edge_cost_drag=Decimal("0.090000"),
        mean_residual_exposure_ratio=Decimal("0.300000"),
        negative_executable_edge_count=2,
        negative_executable_edge_rate=Decimal("0.500000"),
        high_residual_exposure_count=1,
        high_residual_exposure_rate=Decimal("0.250000"),
        positive_paper_return_count=1,
        positive_paper_return_rate=Decimal("0.250000"),
        status="edge_cost_quality_flags",
    )
    empty_latest = _empty_summary_report(
        datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
    )

    report = _trend_report(observed, empty_latest)

    assert report.latest_status == "empty_edge_cost_history"
    assert report.latest_edge_observation_count == 0
    assert report.latest_mean_edge_cost_drag is None
    assert report.largest_negative_executable_edge_count == 2
    assert report.largest_high_residual_exposure_count == 1
    assert report.worst_observed_mean_edge_cost_drag == Decimal("0.090000")
    assert report.worst_observed_mean_residual_exposure_ratio == Decimal("0.300000")
    assert report.consecutive_quality_flag_count == 0
    assert report.consecutive_insufficient_sample_count == 0


def test_edge_cost_summary_trend_normalizes_generated_at_to_utc():
    report = _trend_report(
        generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=timezone(timedelta(hours=-5))),
    )

    assert report.generated_at == GENERATED_AT


def test_edge_cost_summary_trend_rejects_invalid_builder_inputs():
    invalid_reports = (
        object(),
        "not reports",
        b"not reports",
        {"report": _empty_summary_report(GENERATED_AT)},
        (report for report in ()),
    )
    for value in invalid_reports:
        with pytest.raises(ValueError, match="reports must be a list or tuple"):
            build_paper_edge_cost_summary_trend_report(
                value,
                config=_config(),
                generated_at=GENERATED_AT,
            )

    with pytest.raises(ValueError, match="PaperEdgeCostSummaryReport"):
        build_paper_edge_cost_summary_trend_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_edge_cost_summary_trend_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_edge_cost_summary_trend_report(
            (),
            config=_config(),
            generated_at="now",
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_edge_cost_summary_trend_rejects_source_reports_with_nonfinal_flags(flag_name):
    source_report = _empty_summary_report(GENERATED_AT)
    object.__setattr__(source_report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        build_paper_edge_cost_summary_trend_report(
            (source_report,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_edge_cost_summary_trend_dataclasses_are_frozen_and_revalidate_flags():
    report = _trend_report(_summary_report())

    with pytest.raises(FrozenInstanceError):
        report.latest_status = "edge_cost_quality_flags"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_edge_cost_summary_trend_report_revalidates_empty_consistency():
    report = _trend_report()

    with pytest.raises(ValueError, match="latest_status"):
        replace(report, latest_status="empty_edge_cost_history")
    with pytest.raises(ValueError, match="latest_edge_observation_count"):
        replace(report, latest_edge_observation_count=1)
    with pytest.raises(ValueError, match="first_report_generated_at"):
        replace(report, first_report_generated_at=GENERATED_AT)


def test_edge_cost_summary_trend_report_revalidates_status_rows_streaks_and_worsts():
    report = _trend_report(
        _summary_report(
            generated_at=GENERATED_AT,
            mean_edge_cost_drag=Decimal("0.070000"),
            mean_residual_exposure_ratio=Decimal("0.300000"),
            negative_executable_edge_count=1,
            negative_executable_edge_rate=Decimal("0.250000"),
            status="edge_cost_quality_flags",
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
    with pytest.raises(ValueError, match="quality flag streak"):
        replace(report, consecutive_quality_flag_count=2)
    with pytest.raises(ValueError, match="status_rows"):
        replace(
            report,
            status_rows=(
                *report.status_rows[:-1],
                PaperEdgeCostSummaryTrendStatusRow(
                    "edge_cost_quality_flags",
                    0,
                    Decimal("0.000000"),
                ),
            ),
        )
    with pytest.raises(ValueError, match="latest_status"):
        replace(
            report,
            status_rows=(
                PaperEdgeCostSummaryTrendStatusRow(
                    "empty_edge_cost_history",
                    1,
                    Decimal("1.000000"),
                ),
                PaperEdgeCostSummaryTrendStatusRow(
                    "insufficient_edge_cost_sample",
                    0,
                    Decimal("0.000000"),
                ),
                PaperEdgeCostSummaryTrendStatusRow(
                    "edge_cost_evidence_observed",
                    0,
                    Decimal("0.000000"),
                ),
                PaperEdgeCostSummaryTrendStatusRow(
                    "edge_cost_quality_flags",
                    0,
                    Decimal("0.000000"),
                ),
            ),
        )
    with pytest.raises(ValueError, match="largest_negative_executable_edge_count"):
        replace(report, largest_negative_executable_edge_count=0)
    with pytest.raises(ValueError, match="worst_observed_mean_edge_cost_drag"):
        replace(report, worst_observed_mean_edge_cost_drag=Decimal("0.060000"))
    with pytest.raises(ValueError, match="worst_observed_mean_edge_cost_drag"):
        replace(report, worst_observed_mean_edge_cost_drag=None)
    with pytest.raises(ValueError, match="worst_observed_mean_residual_exposure_ratio"):
        replace(report, worst_observed_mean_residual_exposure_ratio=Decimal("0.200000"))
    with pytest.raises(ValueError, match="worst_observed_mean_residual_exposure_ratio"):
        replace(report, worst_observed_mean_residual_exposure_ratio=None)


def test_edge_cost_summary_trend_direct_constructor_rejects_negative_cost_drag_metrics():
    latest_observed = _trend_report(_summary_report())

    with pytest.raises(ValueError, match="latest_mean_edge_cost_drag"):
        PaperEdgeCostSummaryTrendReport(
            **{
                **vars(latest_observed),
                "latest_mean_edge_cost_drag": Decimal("-0.000001"),
            },
        )

    latest_empty_with_history = _trend_report(
        _summary_report(),
        _empty_summary_report(datetime(2026, 6, 18, 13, 0, tzinfo=UTC)),
    )

    with pytest.raises(ValueError, match="worst_observed_mean_edge_cost_drag"):
        PaperEdgeCostSummaryTrendReport(
            **{
                **vars(latest_empty_with_history),
                "worst_observed_mean_edge_cost_drag": Decimal("-0.000001"),
            },
        )


def test_edge_cost_summary_trend_report_bounds_insufficient_sample_streak():
    report = _trend_report(
        _summary_report(
            generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
            status="edge_cost_evidence_observed",
        ),
        _summary_report(
            generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
            edge_observation_count=2,
            positive_paper_return_count=1,
            positive_paper_return_rate=Decimal("0.500000"),
            status="insufficient_edge_cost_sample",
        ),
    )

    with pytest.raises(ValueError, match="requires a streak"):
        replace(report, consecutive_insufficient_sample_count=0)
    with pytest.raises(ValueError, match="insufficient sample streak"):
        replace(report, consecutive_insufficient_sample_count=2)
    with pytest.raises(ValueError, match="quality flags"):
        replace(
            report,
            latest_negative_executable_edge_count=1,
            latest_negative_executable_edge_rate=Decimal("0.500000"),
            largest_negative_executable_edge_count=1,
        )


def test_edge_cost_summary_trend_config_rows_and_all_are_exact():
    from polymarket_alpha_lab import edge_cost_summary_trend

    assert edge_cost_summary_trend.__all__ == (
        "PaperEdgeCostSummaryTrendConfig",
        "PaperEdgeCostSummaryTrendStatusRow",
        "PaperEdgeCostSummaryTrendReport",
        "build_paper_edge_cost_summary_trend_report",
    )

    with pytest.raises(ValueError, match="config_version"):
        PaperEdgeCostSummaryTrendConfig(config_version=" edge-cost-summary-trend-v0 ")
    with pytest.raises(ValueError, match="edge_cost_status"):
        PaperEdgeCostSummaryTrendStatusRow("unknown", 0, None)
    with pytest.raises(ValueError, match="report_ratio"):
        PaperEdgeCostSummaryTrendStatusRow(
            "edge_cost_evidence_observed",
            1,
            Decimal("0.1"),
        )
