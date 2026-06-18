from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceObservation
from polymarket_alpha_lab.strategy_segment_summary import (
    PaperStrategySegmentSummaryConfig,
    PaperStrategySegmentRow,
    PaperStrategySegmentSummaryReport,
    build_paper_strategy_segment_summary_report,
)


GENERATED_AT = datetime(2026, 6, 17, 12, 0, tzinfo=UTC)


def _config(**overrides):
    values = {"config_version": "strategy-segment-summary-v0"}
    values.update(overrides)
    return PaperStrategySegmentSummaryConfig(**values)


def _observation(
    index: int,
    *,
    observed_at: datetime | None = None,
    strategy_type: str = "book_imbalance_paper",
    risk_tags: tuple[str, ...] = ("thin_liquidity",),
    predicted_probability: Decimal | None = Decimal("0.7000"),
    actual_outcome_value: Decimal | None = Decimal("1"),
    paper_return_ratio: Decimal | None = None,
) -> PaperForecastEvidenceObservation:
    probability_values = {}
    if predicted_probability is not None or actual_outcome_value is not None:
        probability_values = {
            "predicted_probability": predicted_probability,
            "actual_outcome_value": actual_outcome_value,
        }

    return_values = {}
    if paper_return_ratio is not None:
        return_values = {
            "theoretical_edge_ratio": Decimal("0.1000"),
            "executable_edge_ratio": Decimal("0.0500"),
            "fill_probability": Decimal("1.0000"),
            "residual_exposure_ratio": Decimal("0.0000"),
            "paper_return_ratio": paper_return_ratio,
        }

    return PaperForecastEvidenceObservation(
        observed_at=observed_at or GENERATED_AT + timedelta(minutes=index),
        source_packet_id=f"packet-{index}",
        condition_id=f"condition-{index}",
        token_id=f"token-{index}",
        market_slug=f"market-{index}",
        strategy_type=strategy_type,
        risk_tags=risk_tags,
        **probability_values,
        **return_values,
    )


def _build(observations, **config_overrides):
    return build_paper_strategy_segment_summary_report(
        observations,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _row_by_key(report, segment_type, segment_name):
    return {
        (row.segment_type, row.segment_name): row
        for row in report.rows
    }[(segment_type, segment_name)]


def test_strategy_segment_summary_empty_inputs_collapse_to_counts_and_no_rows():
    report = _build(())

    assert isinstance(report, PaperStrategySegmentSummaryReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-segment-summary-v0"
    assert report.observation_count == 0
    assert report.strategy_segment_count == 0
    assert report.risk_tag_segment_count == 0
    assert report.first_observed_at is None
    assert report.last_observed_at is None
    assert report.rows == ()


def test_strategy_segment_summary_normalizes_report_datetimes_to_utc():
    local_generated_at = datetime(
        2026,
        6,
        17,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    report = build_paper_strategy_segment_summary_report(
        (
            _observation(
                1,
                observed_at=datetime(
                    2026,
                    6,
                    17,
                    8,
                    30,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                paper_return_ratio=Decimal("0.1000"),
            ),
        ),
        config=_config(min_segment_observations=1),
        generated_at=local_generated_at,
    )

    assert report.generated_at == datetime(2026, 6, 17, 12, 0, tzinfo=UTC)
    assert report.first_observed_at == datetime(2026, 6, 17, 12, 30, tzinfo=UTC)
    assert report.last_observed_at == datetime(2026, 6, 17, 12, 30, tzinfo=UTC)


def test_strategy_segment_summary_groups_strategy_and_risk_tag_segments():
    observations = (
        _observation(
            1,
            observed_at=GENERATED_AT + timedelta(hours=1),
            strategy_type="mean_reversion_paper",
            risk_tags=("thin_liquidity", "late_resolution"),
            predicted_probability=Decimal("0.7500"),
            actual_outcome_value=Decimal("1"),
            paper_return_ratio=Decimal("0.1000"),
        ),
        _observation(
            2,
            observed_at=GENERATED_AT - timedelta(hours=2),
            strategy_type="mean_reversion_paper",
            risk_tags=("thin_liquidity",),
            predicted_probability=Decimal("0.2500"),
            actual_outcome_value=Decimal("0"),
            paper_return_ratio=Decimal("-0.0500"),
        ),
        _observation(
            3,
            strategy_type="news_event_paper",
            risk_tags=("late_resolution",),
            predicted_probability=Decimal("0.6000"),
            actual_outcome_value=Decimal("0"),
        ),
        _observation(
            4,
            observed_at=GENERATED_AT + timedelta(hours=3),
            strategy_type="mean_reversion_paper",
            risk_tags=("thin_liquidity",),
            predicted_probability=None,
            actual_outcome_value=None,
            paper_return_ratio=Decimal("0.2000"),
        ),
        _observation(
            5,
            observed_at=GENERATED_AT + timedelta(hours=4),
            strategy_type="news_event_paper",
            risk_tags=("late_resolution",),
            predicted_probability=Decimal("0.8000"),
            actual_outcome_value=Decimal("1"),
            paper_return_ratio=Decimal("0.1200"),
        ),
    )

    report = _build(observations, min_segment_observations=3)

    assert report.observation_count == 5
    assert report.strategy_segment_count == 2
    assert report.risk_tag_segment_count == 2
    assert report.first_observed_at == GENERATED_AT - timedelta(hours=2)
    assert report.last_observed_at == GENERATED_AT + timedelta(hours=4)
    assert tuple((row.segment_type, row.segment_name) for row in report.rows) == (
        ("risk_tag", "late_resolution"),
        ("risk_tag", "thin_liquidity"),
        ("strategy_type", "mean_reversion_paper"),
        ("strategy_type", "news_event_paper"),
    )

    mean_reversion = _row_by_key(report, "strategy_type", "mean_reversion_paper")
    assert mean_reversion.observation_count == 3
    assert mean_reversion.probability_observation_count == 2
    assert mean_reversion.return_observation_count == 3
    assert mean_reversion.mean_predicted_probability == Decimal("0.500000")
    assert mean_reversion.observed_frequency == Decimal("0.500000")
    assert mean_reversion.brier_score == Decimal("0.062500")
    assert mean_reversion.mean_paper_return_ratio == Decimal("0.083333")
    assert mean_reversion.positive_return_rate == Decimal("0.666667")
    assert mean_reversion.status == "insufficient_segment_probability_sample"

    thin_liquidity = _row_by_key(report, "risk_tag", "thin_liquidity")
    assert thin_liquidity.observation_count == 3
    assert thin_liquidity.probability_observation_count == 2
    assert thin_liquidity.return_observation_count == 3
    assert thin_liquidity.mean_predicted_probability == Decimal("0.500000")
    assert thin_liquidity.observed_frequency == Decimal("0.500000")
    assert thin_liquidity.brier_score == Decimal("0.062500")
    assert thin_liquidity.mean_paper_return_ratio == Decimal("0.083333")
    assert thin_liquidity.positive_return_rate == Decimal("0.666667")
    assert thin_liquidity.status == "insufficient_segment_probability_sample"

    late_resolution = _row_by_key(report, "risk_tag", "late_resolution")
    assert late_resolution.observation_count == 3
    assert late_resolution.probability_observation_count == 3
    assert late_resolution.return_observation_count == 2
    assert late_resolution.mean_predicted_probability == Decimal("0.716667")
    assert late_resolution.observed_frequency == Decimal("0.666667")
    assert late_resolution.brier_score == Decimal("0.154167")
    assert late_resolution.mean_paper_return_ratio == Decimal("0.110000")
    assert late_resolution.positive_return_rate == Decimal("1.000000")
    assert late_resolution.status == "segment_evidence_observed"


def test_strategy_segment_summary_keeps_return_only_segments_descriptive():
    observations = (
        _observation(
            1,
            predicted_probability=None,
            actual_outcome_value=None,
            paper_return_ratio=Decimal("-0.0200"),
        ),
        _observation(
            2,
            predicted_probability=None,
            actual_outcome_value=None,
            paper_return_ratio=Decimal("0.0300"),
        ),
    )

    report = _build(observations, min_segment_observations=2)

    row = _row_by_key(report, "strategy_type", "book_imbalance_paper")
    assert row.observation_count == 2
    assert row.probability_observation_count == 0
    assert row.return_observation_count == 2
    assert row.mean_predicted_probability is None
    assert row.observed_frequency is None
    assert row.brier_score is None
    assert row.mean_paper_return_ratio == Decimal("0.005000")
    assert row.positive_return_rate == Decimal("0.500000")
    assert row.status == "segment_return_evidence_observed"


def test_strategy_segment_summary_rejects_unsorted_duplicate_rows_and_count_mismatches():
    report = _build(
        (
            _observation(1, paper_return_ratio=Decimal("0.1000")),
            _observation(
                2,
                observed_at=GENERATED_AT + timedelta(minutes=1),
                paper_return_ratio=Decimal("-0.0500"),
            ),
        ),
        min_segment_observations=1,
    )

    with pytest.raises(ValueError, match="sorted"):
        replace(report, rows=(report.rows[1], report.rows[0]))

    with pytest.raises(ValueError, match="duplicate"):
        replace(
            report,
            rows=(report.rows[0], report.rows[0], report.rows[1]),
            strategy_segment_count=1,
            risk_tag_segment_count=2,
        )

    with pytest.raises(ValueError, match="strategy_segment_count"):
        replace(report, strategy_segment_count=2)

    with pytest.raises(ValueError, match="risk_tag_segment_count"):
        replace(report, risk_tag_segment_count=2)


def test_strategy_segment_summary_rejects_report_observation_and_time_mismatches():
    report = _build(
        (
            _observation(1, paper_return_ratio=Decimal("0.1000")),
            _observation(
                2,
                observed_at=GENERATED_AT + timedelta(minutes=1),
                paper_return_ratio=Decimal("-0.0500"),
            ),
        ),
        min_segment_observations=1,
    )

    with pytest.raises(ValueError, match="observation_count"):
        replace(report, observation_count=0)
    with pytest.raises(ValueError, match="observed_at bounds"):
        replace(report, first_observed_at=None, last_observed_at=None)
    with pytest.raises(ValueError, match="observed_at bounds"):
        replace(report, first_observed_at=report.last_observed_at + timedelta(minutes=1))

    empty_report = _build(())
    with pytest.raises(ValueError, match="observed_at bounds"):
        replace(
            empty_report,
            first_observed_at=GENERATED_AT,
            last_observed_at=GENERATED_AT,
        )


def test_strategy_segment_summary_direct_report_construction_rejects_mismatch():
    row = PaperStrategySegmentRow(
        segment_type="strategy_type",
        segment_name="book_imbalance_paper",
        observation_count=2,
        probability_observation_count=2,
        return_observation_count=0,
        mean_predicted_probability=Decimal("0.700000"),
        observed_frequency=Decimal("1.000000"),
        brier_score=Decimal("0.090000"),
        mean_paper_return_ratio=None,
        positive_return_rate=None,
        status="segment_evidence_observed",
    )

    with pytest.raises(ValueError, match="observation_count"):
        PaperStrategySegmentSummaryReport(
            generated_at=GENERATED_AT,
            config_version="strategy-segment-summary-v0",
            observation_count=1,
            strategy_segment_count=1,
            risk_tag_segment_count=0,
            first_observed_at=GENERATED_AT,
            last_observed_at=GENERATED_AT,
            rows=(row,),
        )


def test_strategy_segment_row_rejects_impossible_evidence_role_counts():
    with pytest.raises(ValueError, match="evidence role counts"):
        PaperStrategySegmentRow(
            segment_type="strategy_type",
            segment_name="book_imbalance_paper",
            observation_count=3,
            probability_observation_count=1,
            return_observation_count=1,
            mean_predicted_probability=Decimal("0.700000"),
            observed_frequency=Decimal("1.000000"),
            brier_score=Decimal("0.090000"),
            mean_paper_return_ratio=Decimal("0.010000"),
            positive_return_rate=Decimal("1.000000"),
            status="insufficient_segment_probability_sample",
        )


def test_strategy_segment_row_rejects_subquantum_metrics():
    with pytest.raises(ValueError, match="mean_predicted_probability"):
        PaperStrategySegmentRow(
            segment_type="strategy_type",
            segment_name="book_imbalance_paper",
            observation_count=1,
            probability_observation_count=1,
            return_observation_count=1,
            mean_predicted_probability=Decimal("0.7000004"),
            observed_frequency=Decimal("1.000000"),
            brier_score=Decimal("0.090000"),
            mean_paper_return_ratio=Decimal("0.010000"),
            positive_return_rate=Decimal("1.000000"),
            status="segment_evidence_observed",
        )

    with pytest.raises(ValueError, match="brier_score"):
        PaperStrategySegmentRow(
            segment_type="strategy_type",
            segment_name="book_imbalance_paper",
            observation_count=1,
            probability_observation_count=1,
            return_observation_count=0,
            mean_predicted_probability=Decimal("0.700000"),
            observed_frequency=Decimal("1.000000"),
            brier_score=Decimal("0.0900004"),
            mean_paper_return_ratio=None,
            positive_return_rate=None,
            status="segment_evidence_observed",
        )


def test_strategy_segment_summary_rejects_invalid_inputs_and_flags():
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version="")
    with pytest.raises(ValueError, match="min_segment_observations"):
        _config(min_segment_observations=-1)
    with pytest.raises(ValueError, match="config"):
        build_paper_strategy_segment_summary_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_strategy_segment_summary_report(
            (),
            config=_config(),
            generated_at="now",
        )
    with pytest.raises(ValueError, match="iterable"):
        _build("not-observations")
    with pytest.raises(ValueError, match="PaperForecastEvidenceObservation"):
        _build((object(),))

    report = _build(())
    with pytest.raises(FrozenInstanceError):
        report.observation_count = 10
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
