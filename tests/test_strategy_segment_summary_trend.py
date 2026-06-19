from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_segment_summary import (
    PaperStrategySegmentRow,
    PaperStrategySegmentSummaryReport,
)
from polymarket_alpha_lab.strategy_segment_summary_trend import (
    PaperStrategySegmentSummaryTrendConfig,
    PaperStrategySegmentSummaryTrendReport,
    PaperStrategySegmentSummaryTrendStatusRow,
    build_paper_strategy_segment_summary_trend_report,
)


GENERATED_AT = datetime(2026, 6, 17, 18, 0, tzinfo=UTC)
SUMMARY_REPORT_STATUSES = (
    "insufficient_segment_probability_sample",
    "segment_evidence_observed",
    "segment_return_evidence_observed",
)


def _config(**overrides) -> PaperStrategySegmentSummaryTrendConfig:
    values = {"config_version": "strategy-segment-summary-trend-v0"}
    values.update(overrides)
    return PaperStrategySegmentSummaryTrendConfig(**values)


def _row(
    *,
    segment_type: str = "strategy_type",
    segment_name: str = "book_imbalance_paper",
    observation_count: int = 3,
    probability_observation_count: int = 3,
    return_observation_count: int = 0,
    status: str = "segment_evidence_observed",
) -> PaperStrategySegmentRow:
    probability_fields = {
        "mean_predicted_probability": Decimal("0.600000"),
        "observed_frequency": Decimal("0.666667"),
        "brier_score": Decimal("0.160000"),
    }
    if probability_observation_count == 0:
        probability_fields = {
            "mean_predicted_probability": None,
            "observed_frequency": None,
            "brier_score": None,
        }

    return_fields = {
        "mean_paper_return_ratio": None,
        "positive_return_rate": None,
    }
    if return_observation_count > 0:
        return_fields = {
            "mean_paper_return_ratio": Decimal("0.025000"),
            "positive_return_rate": Decimal("0.666667"),
        }

    return PaperStrategySegmentRow(
        segment_type=segment_type,
        segment_name=segment_name,
        observation_count=observation_count,
        probability_observation_count=probability_observation_count,
        return_observation_count=return_observation_count,
        status=status,
        **probability_fields,
        **return_fields,
    )


def _summary_report(
    *rows: PaperStrategySegmentRow,
    generated_at: datetime = GENERATED_AT,
) -> PaperStrategySegmentSummaryReport:
    observation_count = sum(
        row.observation_count for row in rows if row.segment_type == "strategy_type"
    )
    observed_at = generated_at if observation_count > 0 else None
    return PaperStrategySegmentSummaryReport(
        generated_at=generated_at,
        config_version="strategy-segment-summary-v0",
        observation_count=observation_count,
        strategy_segment_count=sum(
            1 for row in rows if row.segment_type == "strategy_type"
        ),
        risk_tag_segment_count=sum(1 for row in rows if row.segment_type == "risk_tag"),
        first_observed_at=observed_at,
        last_observed_at=observed_at,
        rows=rows,
    )


def _trend_report(
    *reports: PaperStrategySegmentSummaryReport,
) -> PaperStrategySegmentSummaryTrendReport:
    return build_paper_strategy_segment_summary_trend_report(
        reports,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def test_segment_summary_trend_empty_input_is_readonly_report_only():
    trend = _trend_report()

    assert isinstance(trend, PaperStrategySegmentSummaryTrendReport)
    assert trend.generated_at == GENERATED_AT
    assert trend.config_version == "strategy-segment-summary-trend-v0"
    assert trend.segment_summary_report_count == 0
    assert trend.first_report_generated_at is None
    assert trend.latest_report_generated_at is None
    assert trend.latest_status is None
    assert trend.latest_total_observation_count == 0
    assert trend.latest_probability_observation_count == 0
    assert trend.latest_return_observation_count == 0
    assert trend.latest_strategy_segment_count == 0
    assert trend.latest_risk_tag_segment_count == 0
    assert trend.latest_incomplete_segment_count == 0
    assert trend.latest_return_only_segment_count == 0
    assert trend.largest_observed_incomplete_segment_count == 0
    assert trend.largest_observed_return_only_segment_count == 0
    assert trend.consecutive_incomplete_segment_count == 0
    assert trend.consecutive_return_only_segment_count == 0
    assert trend.status_rows == tuple(
        PaperStrategySegmentSummaryTrendStatusRow(status, 0, None)
        for status in SUMMARY_REPORT_STATUSES
    )
    assert trend.paper_only is True
    assert trend.report_only is True
    assert trend.readonly is True


def test_segment_summary_trend_preserves_append_order_latest_and_counts_streaks():
    first_appended = _summary_report(
        _row(segment_type="risk_tag", segment_name="late_resolution"),
        _row(segment_type="strategy_type", segment_name="mean_reversion_paper"),
        generated_at=datetime(2026, 6, 17, 15, 0, tzinfo=UTC),
    )
    earlier_timestamp = _summary_report(
        _row(
            segment_type="risk_tag",
            segment_name="late_resolution",
            probability_observation_count=0,
            return_observation_count=3,
            status="segment_return_evidence_observed",
        ),
        _row(
            segment_type="strategy_type",
            segment_name="mean_reversion_paper",
            observation_count=2,
            probability_observation_count=1,
            return_observation_count=1,
            status="insufficient_segment_probability_sample",
        ),
        generated_at=datetime(2026, 6, 17, 13, 0, tzinfo=UTC),
    )
    latest_appended = _summary_report(
        _row(
            segment_type="risk_tag",
            segment_name="thin_liquidity",
            probability_observation_count=0,
            return_observation_count=3,
            status="segment_return_evidence_observed",
        ),
        _row(
            segment_type="strategy_type",
            segment_name="book_imbalance_paper",
            probability_observation_count=0,
            return_observation_count=3,
            status="segment_return_evidence_observed",
        ),
        generated_at=datetime(2026, 6, 17, 14, 0, tzinfo=UTC),
    )

    trend = _trend_report(first_appended, earlier_timestamp, latest_appended)

    assert trend.segment_summary_report_count == 3
    assert trend.first_report_generated_at == first_appended.generated_at
    assert trend.latest_report_generated_at == latest_appended.generated_at
    assert trend.latest_status == "segment_return_evidence_observed"
    assert trend.latest_total_observation_count == 3
    assert trend.latest_probability_observation_count == 0
    assert trend.latest_return_observation_count == 3
    assert trend.latest_strategy_segment_count == 1
    assert trend.latest_risk_tag_segment_count == 1
    assert trend.latest_incomplete_segment_count == 0
    assert trend.latest_return_only_segment_count == 2
    assert trend.largest_observed_incomplete_segment_count == 1
    assert trend.largest_observed_return_only_segment_count == 2
    assert trend.consecutive_incomplete_segment_count == 0
    assert trend.consecutive_return_only_segment_count == 2
    assert trend.status_rows == (
        PaperStrategySegmentSummaryTrendStatusRow(
            "insufficient_segment_probability_sample",
            1,
            Decimal("0.333333"),
        ),
        PaperStrategySegmentSummaryTrendStatusRow(
            "segment_evidence_observed",
            1,
            Decimal("0.333333"),
        ),
        PaperStrategySegmentSummaryTrendStatusRow(
            "segment_return_evidence_observed",
            1,
            Decimal("0.333333"),
        ),
    )


def test_segment_summary_trend_classifies_empty_source_reports_as_insufficient_sample():
    empty_source_report = _summary_report(
        generated_at=datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
    )

    trend = _trend_report(empty_source_report)

    assert trend.latest_status == "insufficient_segment_probability_sample"
    assert trend.latest_total_observation_count == 0
    assert trend.latest_incomplete_segment_count == 0
    assert trend.consecutive_incomplete_segment_count == 0
    assert trend.status_rows == (
        PaperStrategySegmentSummaryTrendStatusRow(
            "insufficient_segment_probability_sample",
            1,
            Decimal("1.000000"),
        ),
        PaperStrategySegmentSummaryTrendStatusRow(
            "segment_evidence_observed",
            0,
            Decimal("0.000000"),
        ),
        PaperStrategySegmentSummaryTrendStatusRow(
            "segment_return_evidence_observed",
            0,
            Decimal("0.000000"),
        ),
    )


def test_segment_summary_trend_rejects_invalid_builder_inputs():
    invalid_inputs = (
        object(),
        "not reports",
        b"not reports",
        {"report": _summary_report()},
        (report for report in ()),
    )
    for reports in invalid_inputs:
        with pytest.raises(ValueError, match="reports must be a list or tuple"):
            build_paper_strategy_segment_summary_trend_report(
                reports,
                config=_config(),
                generated_at=GENERATED_AT,
            )

    with pytest.raises(ValueError, match="PaperStrategySegmentSummaryReport"):
        build_paper_strategy_segment_summary_trend_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_strategy_segment_summary_trend_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_strategy_segment_summary_trend_report(
            (),
            config=_config(),
            generated_at="now",
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_segment_summary_trend_rejects_source_reports_with_false_flags(flag_name):
    report = _summary_report(
        _row(segment_type="strategy_type", segment_name="book_imbalance_paper"),
    )
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        _trend_report(report)


def test_segment_summary_trend_dataclasses_are_frozen_and_revalidate_flags():
    trend = _trend_report(
        _summary_report(
            _row(segment_type="strategy_type", segment_name="book_imbalance_paper"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        trend.latest_status = None
    with pytest.raises(ValueError, match="paper_only"):
        replace(trend, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(trend, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(trend, readonly=False)


def test_segment_summary_trend_report_revalidates_status_rows_and_latest_state():
    trend = _trend_report(
        _summary_report(
            _row(
                segment_type="strategy_type",
                segment_name="book_imbalance_paper",
                observation_count=2,
                probability_observation_count=1,
                return_observation_count=1,
                status="insufficient_segment_probability_sample",
            ),
        ),
    )

    with pytest.raises(ValueError, match="latest_status"):
        replace(trend, latest_status="segment_evidence_observed")
    with pytest.raises(ValueError, match="status_rows"):
        replace(trend, status_rows=tuple(reversed(trend.status_rows)))

    missing_latest_status_rows = (
        PaperStrategySegmentSummaryTrendStatusRow(
            "insufficient_segment_probability_sample",
            0,
            Decimal("0.000000"),
        ),
        PaperStrategySegmentSummaryTrendStatusRow(
            "segment_evidence_observed",
            1,
            Decimal("1.000000"),
        ),
        PaperStrategySegmentSummaryTrendStatusRow(
            "segment_return_evidence_observed",
            0,
            Decimal("0.000000"),
        ),
    )
    with pytest.raises(ValueError, match="latest_status"):
        replace(
            trend,
            status_rows=missing_latest_status_rows,
        )

    drifted_row = replace(trend.status_rows[0])
    object.__setattr__(drifted_row, "report_ratio", Decimal("0.500000"))
    with pytest.raises(ValueError, match="status_rows ratios"):
        replace(
            trend,
            status_rows=(
                drifted_row,
                *trend.status_rows[1:],
            ),
        )


def test_segment_summary_trend_report_revalidates_zero_observation_latest_metrics():
    trend = _trend_report(
        _summary_report(
            generated_at=datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        ),
    )

    with pytest.raises(ValueError, match="latest_status"):
        replace(trend, latest_status="segment_evidence_observed")
    with pytest.raises(ValueError, match="latest_strategy_segment_count"):
        replace(trend, latest_strategy_segment_count=1)
    with pytest.raises(ValueError, match="latest_risk_tag_segment_count"):
        replace(trend, latest_risk_tag_segment_count=1)
    with pytest.raises(ValueError, match="latest_incomplete_segment_count"):
        replace(
            trend,
            latest_incomplete_segment_count=1,
            largest_observed_incomplete_segment_count=1,
            consecutive_incomplete_segment_count=1,
        )


def test_segment_summary_trend_config_and_rows_reject_invalid_values():
    with pytest.raises(ValueError, match="config_version"):
        PaperStrategySegmentSummaryTrendConfig(
            config_version=" strategy-segment-summary-trend-v0 ",
        )
    with pytest.raises(ValueError, match="summary_status"):
        PaperStrategySegmentSummaryTrendStatusRow("unknown", 0, None)
    with pytest.raises(ValueError, match="report_ratio"):
        PaperStrategySegmentSummaryTrendStatusRow(
            "segment_evidence_observed",
            1,
            Decimal("0.5"),
        )
