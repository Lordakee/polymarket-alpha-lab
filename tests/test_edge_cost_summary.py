from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.edge_cost_summary import (
    PaperEdgeCostSummaryConfig,
    PaperEdgeCostSummaryReport,
    build_paper_edge_cost_summary_report,
)
from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceObservation


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)


def edge_observation(index, observed_at, **overrides):
    values = {
        "observed_at": observed_at,
        "source_packet_id": f"packet-{index}",
        "condition_id": f"condition-{index}",
        "token_id": f"token-{index}",
        "market_slug": f"market-{index}",
        "strategy_type": "book_imbalance_screening_paper",
        "risk_tags": ("liquidity",),
        "theoretical_edge_ratio": Decimal("0.080000"),
        "executable_edge_ratio": Decimal("0.050000"),
        "fill_probability": Decimal("0.700000"),
        "residual_exposure_ratio": Decimal("0.100000"),
        "paper_return_ratio": Decimal("0.010000"),
    }
    values.update(overrides)
    return PaperForecastEvidenceObservation(**values)


def probability_observation(index, observed_at):
    return PaperForecastEvidenceObservation(
        observed_at=observed_at,
        source_packet_id=f"probability-packet-{index}",
        condition_id=f"probability-condition-{index}",
        token_id=f"probability-token-{index}",
        market_slug=f"probability-market-{index}",
        strategy_type="probability_calibration_paper",
        risk_tags=("calibration",),
        predicted_probability=Decimal("0.600000"),
        actual_outcome_value=Decimal("1"),
    )


def test_edge_cost_summary_filters_complete_edge_role_and_computes_metrics():
    observations = (
        edge_observation(
            1,
            datetime(2026, 6, 3, tzinfo=UTC),
            theoretical_edge_ratio=Decimal("0.100000"),
            executable_edge_ratio=Decimal("0.040000"),
            fill_probability=Decimal("0.600000"),
            residual_exposure_ratio=Decimal("0.100000"),
            paper_return_ratio=Decimal("0.010000"),
        ),
        edge_observation(
            2,
            datetime(2026, 6, 1, 8, tzinfo=UTC),
            theoretical_edge_ratio=Decimal("0.050000"),
            executable_edge_ratio=Decimal("-0.010000"),
            fill_probability=Decimal("0.400000"),
            residual_exposure_ratio=Decimal("0.300000"),
            paper_return_ratio=Decimal("-0.020000"),
        ),
        edge_observation(
            3,
            datetime(2026, 6, 2, tzinfo=UTC),
            theoretical_edge_ratio=Decimal("0.020000"),
            executable_edge_ratio=Decimal("0.010000"),
            fill_probability=Decimal("0.800000"),
            residual_exposure_ratio=Decimal("0.200000"),
            paper_return_ratio=Decimal("0.030000"),
        ),
    )

    report = build_paper_edge_cost_summary_report(
        observations,
        config=PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_edge_observation_count=3,
            min_fill_probability=Decimal("0.500000"),
            max_residual_exposure_ratio=Decimal("0.250000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperEdgeCostSummaryReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "edge-cost-summary-test"
    assert report.edge_observation_count == 3
    assert report.first_observed_at == datetime(2026, 6, 3, tzinfo=UTC)
    assert report.last_observed_at == datetime(2026, 6, 2, tzinfo=UTC)
    assert report.mean_theoretical_edge_ratio == Decimal("0.056667")
    assert report.mean_executable_edge_ratio == Decimal("0.013333")
    assert report.mean_edge_cost_drag == Decimal("0.043333")
    assert report.mean_fill_probability == Decimal("0.600000")
    assert report.mean_residual_exposure_ratio == Decimal("0.200000")
    assert report.mean_paper_return_ratio == Decimal("0.006667")
    assert report.negative_executable_edge_count == 1
    assert report.negative_executable_edge_rate == Decimal("0.333333")
    assert report.low_fill_probability_count == 1
    assert report.low_fill_probability_rate == Decimal("0.333333")
    assert report.high_residual_exposure_count == 1
    assert report.high_residual_exposure_rate == Decimal("0.333333")
    assert report.positive_paper_return_count == 2
    assert report.positive_paper_return_rate == Decimal("0.666667")
    assert report.status == "edge_cost_quality_flags"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_edge_cost_summary_reports_empty_for_empty_input():
    report = build_paper_edge_cost_summary_report(
        (),
        config=PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_edge_observation_count=1,
        ),
        generated_at=GENERATED_AT,
    )

    assert report.edge_observation_count == 0
    assert report.first_observed_at is None
    assert report.last_observed_at is None
    assert report.mean_theoretical_edge_ratio is None
    assert report.mean_executable_edge_ratio is None
    assert report.mean_edge_cost_drag is None
    assert report.mean_fill_probability is None
    assert report.mean_residual_exposure_ratio is None
    assert report.mean_paper_return_ratio is None
    assert report.negative_executable_edge_count == 0
    assert report.negative_executable_edge_rate is None
    assert report.low_fill_probability_count == 0
    assert report.low_fill_probability_rate is None
    assert report.high_residual_exposure_count == 0
    assert report.high_residual_exposure_rate is None
    assert report.positive_paper_return_count == 0
    assert report.positive_paper_return_rate is None
    assert report.status == "empty_edge_cost_history"


def test_edge_cost_summary_requires_complete_edge_role_observations():
    with pytest.raises(ValueError, match="complete edge role"):
        build_paper_edge_cost_summary_report(
            (probability_observation(1, datetime(2026, 6, 1, tzinfo=UTC)),),
            config=PaperEdgeCostSummaryConfig(
                config_version="edge-cost-summary-test",
                min_edge_observation_count=1,
            ),
            generated_at=GENERATED_AT,
        )


def test_edge_cost_summary_clamps_negative_cost_drag_to_zero():
    report = build_paper_edge_cost_summary_report(
        (
            edge_observation(
                1,
                datetime(2026, 6, 1, tzinfo=UTC),
                theoretical_edge_ratio=Decimal("0.020000"),
                executable_edge_ratio=Decimal("0.050000"),
            ),
            edge_observation(
                2,
                datetime(2026, 6, 2, tzinfo=UTC),
                theoretical_edge_ratio=Decimal("0.090000"),
                executable_edge_ratio=Decimal("0.040000"),
            ),
        ),
        config=PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_edge_observation_count=2,
        ),
        generated_at=GENERATED_AT,
    )

    assert report.mean_edge_cost_drag == Decimal("0.025000")


def test_edge_cost_summary_statuses_are_descriptive_sample_and_quality_states():
    config = PaperEdgeCostSummaryConfig(
        config_version="edge-cost-summary-test",
        min_edge_observation_count=2,
    )

    insufficient = build_paper_edge_cost_summary_report(
        (edge_observation(1, datetime(2026, 6, 1, tzinfo=UTC)),),
        config=config,
        generated_at=GENERATED_AT,
    )
    observed = build_paper_edge_cost_summary_report(
        (
            edge_observation(1, datetime(2026, 6, 1, tzinfo=UTC)),
            edge_observation(2, datetime(2026, 6, 2, tzinfo=UTC)),
        ),
        config=config,
        generated_at=GENERATED_AT,
    )

    assert insufficient.status == "insufficient_edge_cost_sample"
    assert observed.status == "edge_cost_evidence_observed"


def test_edge_cost_summary_flags_quality_before_sample_shortfall():
    report = build_paper_edge_cost_summary_report(
        (
            edge_observation(
                1,
                datetime(2026, 6, 1, tzinfo=UTC),
                executable_edge_ratio=Decimal("-0.010000"),
                fill_probability=Decimal("0.400000"),
                residual_exposure_ratio=Decimal("0.300000"),
            ),
        ),
        config=PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_edge_observation_count=30,
            min_fill_probability=Decimal("0.500000"),
            max_residual_exposure_ratio=Decimal("0.250000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.status == "edge_cost_quality_flags"
    assert report.negative_executable_edge_count == 1
    assert report.low_fill_probability_count == 1
    assert report.high_residual_exposure_count == 1


def test_edge_cost_summary_dataclasses_are_frozen_and_revalidate_final_flags():
    config = PaperEdgeCostSummaryConfig(config_version="edge-cost-summary-test")
    report = build_paper_edge_cost_summary_report(
        (edge_observation(1, datetime(2026, 6, 1, tzinfo=UTC)),),
        config=config,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(FrozenInstanceError):
        report.edge_observation_count = 0
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_edge_cost_summary_report_revalidates_derived_rates_and_status():
    report = build_paper_edge_cost_summary_report(
        (
            edge_observation(
                1,
                datetime(2026, 6, 1, tzinfo=UTC),
                executable_edge_ratio=Decimal("-0.010000"),
                fill_probability=Decimal("0.400000"),
                residual_exposure_ratio=Decimal("0.300000"),
            ),
            edge_observation(2, datetime(2026, 6, 2, tzinfo=UTC)),
        ),
        config=PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_edge_observation_count=2,
        ),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="negative_executable_edge_rate"):
        replace(report, negative_executable_edge_rate=Decimal("0.250000"))
    with pytest.raises(ValueError, match="low_fill_probability_rate"):
        replace(report, low_fill_probability_rate=Decimal("0.250000"))
    with pytest.raises(ValueError, match="high_residual_exposure_rate"):
        replace(report, high_residual_exposure_rate=Decimal("0.250000"))
    with pytest.raises(ValueError, match="positive_paper_return_rate"):
        replace(report, positive_paper_return_rate=Decimal("0.250000"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="edge_cost_evidence_observed")

    clean_report = build_paper_edge_cost_summary_report(
        (
            edge_observation(1, datetime(2026, 6, 1, tzinfo=UTC)),
            edge_observation(2, datetime(2026, 6, 2, tzinfo=UTC)),
        ),
        config=PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_edge_observation_count=2,
        ),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="status"):
        replace(clean_report, status="edge_cost_quality_flags")


def test_edge_cost_summary_empty_report_rejects_nonzero_direct_counts():
    report = build_paper_edge_cost_summary_report(
        (),
        config=PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_edge_observation_count=1,
        ),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="edge_observation_count"):
        replace(report, negative_executable_edge_count=1)
    with pytest.raises(ValueError, match="edge_observation_count"):
        replace(report, low_fill_probability_count=1)
    with pytest.raises(ValueError, match="edge_observation_count"):
        replace(report, high_residual_exposure_count=1)
    with pytest.raises(ValueError, match="edge_observation_count"):
        replace(report, positive_paper_return_count=1)


def test_edge_cost_summary_rejects_unquantized_decimal_thresholds_and_metrics():
    with pytest.raises(ValueError, match="min_fill_probability"):
        PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_fill_probability=Decimal("0.5000001"),
        )

    report = build_paper_edge_cost_summary_report(
        (edge_observation(1, datetime(2026, 6, 1, tzinfo=UTC)),),
        config=PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_edge_observation_count=1,
        ),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="mean_theoretical_edge_ratio"):
        replace(report, mean_theoretical_edge_ratio=Decimal("0.0800001"))
    with pytest.raises(ValueError, match="mean_fill_probability"):
        replace(report, mean_fill_probability=Decimal("0.7000001"))


def test_edge_cost_summary_report_rejects_unrealistic_cost_drag_metrics():
    report = build_paper_edge_cost_summary_report(
        (
            edge_observation(
                1,
                datetime(2026, 6, 1, tzinfo=UTC),
                theoretical_edge_ratio=Decimal("0.080000"),
                executable_edge_ratio=Decimal("0.030000"),
            ),
            edge_observation(
                2,
                datetime(2026, 6, 2, tzinfo=UTC),
                theoretical_edge_ratio=Decimal("0.040000"),
                executable_edge_ratio=Decimal("0.020000"),
            ),
        ),
        config=PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_edge_observation_count=2,
        ),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="mean_edge_cost_drag"):
        replace(report, mean_edge_cost_drag=Decimal("-0.000001"))
    with pytest.raises(ValueError, match="mean_edge_cost_drag"):
        replace(report, mean_edge_cost_drag=Decimal("0.030000"))


def test_edge_cost_summary_report_rejects_out_of_range_fill_and_residual_metrics():
    report = build_paper_edge_cost_summary_report(
        (edge_observation(1, datetime(2026, 6, 1, tzinfo=UTC)),),
        config=PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_edge_observation_count=1,
        ),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="mean_fill_probability"):
        replace(report, mean_fill_probability=Decimal("1.000001"))
    with pytest.raises(ValueError, match="mean_residual_exposure_ratio"):
        replace(report, mean_residual_exposure_ratio=Decimal("-0.000001"))


def test_edge_cost_summary_accepts_independent_high_fill_and_residual_probabilities():
    report = build_paper_edge_cost_summary_report(
        (
            edge_observation(
                1,
                datetime(2026, 6, 1, tzinfo=UTC),
                fill_probability=Decimal("0.800000"),
                residual_exposure_ratio=Decimal("0.300000"),
            ),
        ),
        config=PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_edge_observation_count=1,
            min_fill_probability=Decimal("0.500000"),
            max_residual_exposure_ratio=Decimal("0.250000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.mean_fill_probability == Decimal("0.800000")
    assert report.mean_residual_exposure_ratio == Decimal("0.300000")
    assert report.high_residual_exposure_count == 1
    assert report.high_residual_exposure_rate == Decimal("1.000000")
    assert report.status == "edge_cost_quality_flags"


def test_edge_cost_summary_report_rejects_negative_executable_mean_without_negative_count():
    report = build_paper_edge_cost_summary_report(
        (
            edge_observation(
                1,
                datetime(2026, 6, 1, tzinfo=UTC),
                executable_edge_ratio=Decimal("0.010000"),
            ),
            edge_observation(
                2,
                datetime(2026, 6, 2, tzinfo=UTC),
                executable_edge_ratio=Decimal("0.020000"),
            ),
        ),
        config=PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_edge_observation_count=2,
        ),
        generated_at=GENERATED_AT,
    )

    assert report.negative_executable_edge_count == 0
    with pytest.raises(ValueError, match="mean_executable_edge_ratio"):
        replace(report, mean_executable_edge_ratio=Decimal("-0.000001"))


def test_edge_cost_summary_rejects_non_decimal_thresholds_and_bad_inputs():
    with pytest.raises(ValueError, match="min_fill_probability"):
        PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            min_fill_probability=0.5,
        )
    with pytest.raises(ValueError, match="observations"):
        build_paper_edge_cost_summary_report(
            "not-observations",
            config=PaperEdgeCostSummaryConfig(config_version="edge-cost-summary-test"),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observations must be a list or tuple"):
        build_paper_edge_cost_summary_report(
            (edge_observation(1, datetime(2026, 6, 1, tzinfo=UTC)) for _ in range(1)),
            config=PaperEdgeCostSummaryConfig(config_version="edge-cost-summary-test"),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PaperForecastEvidenceObservation"):
        build_paper_edge_cost_summary_report(
            (object(),),
            config=PaperEdgeCostSummaryConfig(config_version="edge-cost-summary-test"),
            generated_at=GENERATED_AT,
        )
