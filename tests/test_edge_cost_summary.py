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
        "residual_exposure_ratio": Decimal("0.050000"),
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


def test_edge_cost_summary_reduces_caller_supplied_paper_observations_in_append_order():
    observations = [
        edge_observation(
            1,
            datetime(2026, 6, 3, tzinfo=UTC),
            market_slug="market-alpha",
            strategy_type="strategy-a",
            risk_tags=("liquidity", "volatility"),
            theoretical_edge_ratio=Decimal("0.100000"),
            executable_edge_ratio=Decimal("0.040000"),
            fill_probability=Decimal("0.600000"),
            residual_exposure_ratio=Decimal("0.120000"),
            paper_return_ratio=Decimal("0.010000"),
        ),
        edge_observation(
            2,
            datetime(2026, 6, 1, 8, tzinfo=UTC),
            market_slug="market-beta",
            strategy_type="strategy-b",
            risk_tags=("liquidity",),
            theoretical_edge_ratio=Decimal("0.030000"),
            executable_edge_ratio=Decimal("0.050000"),
            fill_probability=Decimal("0.400000"),
            residual_exposure_ratio=Decimal("0.080000"),
            paper_return_ratio=Decimal("-0.020000"),
        ),
        edge_observation(
            3,
            datetime(2026, 6, 2, tzinfo=UTC),
            market_slug="market-alpha",
            strategy_type="strategy-a",
            risk_tags=("depth",),
            theoretical_edge_ratio=Decimal("0.020000"),
            executable_edge_ratio=Decimal("-0.010000"),
            fill_probability=Decimal("0.800000"),
            residual_exposure_ratio=Decimal("0.110000"),
            paper_return_ratio=Decimal("0.030000"),
        ),
    ]

    report = build_paper_edge_cost_summary_report(
        observations,
        config=PaperEdgeCostSummaryConfig(
            config_version="edge-cost-summary-test",
            low_fill_probability_threshold=Decimal("0.500000"),
            high_residual_exposure_threshold=Decimal("0.100000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperEdgeCostSummaryReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "edge-cost-summary-test"
    assert report.edge_observation_count == 3
    assert report.first_observed_at == datetime(2026, 6, 3, tzinfo=UTC)
    assert report.latest_observed_at == datetime(2026, 6, 2, tzinfo=UTC)
    assert report.unique_market_count == 2
    assert report.unique_strategy_count == 2
    assert report.unique_risk_tag_count == 3
    assert report.mean_theoretical_edge_ratio == Decimal("0.050000")
    assert report.mean_executable_edge_ratio == Decimal("0.026667")
    assert report.mean_edge_cost_gap == Decimal("0.030000")
    assert report.worst_edge_cost_gap == Decimal("0.060000")
    assert report.negative_executable_edge_count == 1
    assert report.negative_executable_edge_ratio == Decimal("0.333333")
    assert report.mean_fill_probability == Decimal("0.600000")
    assert report.low_fill_probability_count == 1
    assert report.low_fill_probability_ratio == Decimal("0.333333")
    assert report.mean_residual_exposure_ratio == Decimal("0.103333")
    assert report.worst_residual_exposure_ratio == Decimal("0.120000")
    assert report.high_residual_exposure_count == 2
    assert report.high_residual_exposure_ratio == Decimal("0.666667")
    assert report.mean_paper_return_ratio == Decimal("0.006667")
    assert report.positive_paper_return_count == 2
    assert report.positive_paper_return_ratio == Decimal("0.666667")
    assert report.status == "edge_cost_summary_observed"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_edge_cost_summary_reports_empty_without_metric_values():
    report = build_paper_edge_cost_summary_report(
        [],
        config=PaperEdgeCostSummaryConfig(config_version="edge-cost-summary-test"),
        generated_at=GENERATED_AT,
    )

    assert report.edge_observation_count == 0
    assert report.first_observed_at is None
    assert report.latest_observed_at is None
    assert report.unique_market_count == 0
    assert report.unique_strategy_count == 0
    assert report.unique_risk_tag_count == 0
    assert report.mean_theoretical_edge_ratio is None
    assert report.mean_executable_edge_ratio is None
    assert report.mean_edge_cost_gap is None
    assert report.worst_edge_cost_gap is None
    assert report.negative_executable_edge_count == 0
    assert report.negative_executable_edge_ratio is None
    assert report.mean_fill_probability is None
    assert report.low_fill_probability_count == 0
    assert report.low_fill_probability_ratio is None
    assert report.mean_residual_exposure_ratio is None
    assert report.worst_residual_exposure_ratio is None
    assert report.high_residual_exposure_count == 0
    assert report.high_residual_exposure_ratio is None
    assert report.mean_paper_return_ratio is None
    assert report.positive_paper_return_count == 0
    assert report.positive_paper_return_ratio is None
    assert report.status == "empty_edge_cost_summary"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_edge_cost_summary_uses_default_thresholds_for_quality_counts_only():
    report = build_paper_edge_cost_summary_report(
        [
            edge_observation(
                1,
                datetime(2026, 6, 1, tzinfo=UTC),
                fill_probability=Decimal("0.499999"),
                residual_exposure_ratio=Decimal("0.100001"),
            ),
            edge_observation(
                2,
                datetime(2026, 6, 2, tzinfo=UTC),
                fill_probability=Decimal("0.500000"),
                residual_exposure_ratio=Decimal("0.100000"),
            ),
        ],
        config=PaperEdgeCostSummaryConfig(config_version="edge-cost-summary-test"),
        generated_at=GENERATED_AT,
    )

    assert report.low_fill_probability_count == 1
    assert report.low_fill_probability_ratio == Decimal("0.500000")
    assert report.high_residual_exposure_count == 1
    assert report.high_residual_exposure_ratio == Decimal("0.500000")
    assert report.status == "edge_cost_summary_observed"


def test_edge_cost_summary_dataclasses_are_frozen_and_validate_flags_and_decimals():
    config = PaperEdgeCostSummaryConfig(config_version="edge-cost-summary-test")
    assert config.low_fill_probability_threshold == Decimal("0.500000")
    assert config.high_residual_exposure_threshold == Decimal("0.100000")

    report = build_paper_edge_cost_summary_report(
        [edge_observation(1, datetime(2026, 6, 1, tzinfo=UTC))],
        config=config,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(FrozenInstanceError):
        report.edge_observation_count = 0
    with pytest.raises(ValueError, match="low_fill_probability_threshold"):
        replace(config, low_fill_probability_threshold=0.5)
    with pytest.raises(ValueError, match="high_residual_exposure_threshold"):
        replace(config, high_residual_exposure_threshold=Decimal("0.1000001"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_edge_cost_summary_revalidates_empty_and_nonempty_report_consistency():
    empty_report = build_paper_edge_cost_summary_report(
        [],
        config=PaperEdgeCostSummaryConfig(config_version="edge-cost-summary-test"),
        generated_at=GENERATED_AT,
    )
    report = build_paper_edge_cost_summary_report(
        [edge_observation(1, datetime(2026, 6, 1, tzinfo=UTC))],
        config=PaperEdgeCostSummaryConfig(config_version="edge-cost-summary-test"),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="mean_theoretical_edge_ratio"):
        replace(empty_report, mean_theoretical_edge_ratio=Decimal("0.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(empty_report, status="edge_cost_summary_observed")
    with pytest.raises(ValueError, match="latest_observed_at"):
        replace(report, latest_observed_at=None)
    with pytest.raises(ValueError, match="negative_executable_edge_ratio"):
        replace(report, negative_executable_edge_ratio=Decimal("0.500000"))
    with pytest.raises(ValueError, match="worst_edge_cost_gap"):
        replace(report, worst_edge_cost_gap=Decimal("-0.000001"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="empty_edge_cost_summary")


def test_edge_cost_summary_rejects_non_report_inputs_and_non_edge_observations():
    config = PaperEdgeCostSummaryConfig(config_version="edge-cost-summary-test")
    observation = edge_observation(1, datetime(2026, 6, 1, tzinfo=UTC))

    with pytest.raises(ValueError, match="config"):
        build_paper_edge_cost_summary_report(
            [observation],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_edge_cost_summary_report(
            [observation],
            config=config,
            generated_at="2026-06-18T12:00:00Z",
        )

    rejected_containers = (
        "not-observations",
        b"not-observations",
        {"observation": observation},
        (item for item in [observation]),
    )
    for rejected in rejected_containers:
        with pytest.raises(ValueError, match="observations must be a list or tuple"):
            build_paper_edge_cost_summary_report(
                rejected,
                config=config,
                generated_at=GENERATED_AT,
            )

    with pytest.raises(ValueError, match="PaperForecastEvidenceObservation"):
        build_paper_edge_cost_summary_report(
            [object()],
            config=config,
            generated_at=GENERATED_AT,
        )

    subclass_observation = object.__new__(
        type("ObservationSubclass", (PaperForecastEvidenceObservation,), {}),
    )
    with pytest.raises(ValueError, match="PaperForecastEvidenceObservation"):
        build_paper_edge_cost_summary_report(
            [subclass_observation],
            config=config,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="complete edge"):
        build_paper_edge_cost_summary_report(
            [probability_observation(1, datetime(2026, 6, 1, tzinfo=UTC))],
            config=config,
            generated_at=GENERATED_AT,
        )


def test_edge_cost_summary_rejects_non_paper_or_incomplete_edge_observations():
    config = PaperEdgeCostSummaryConfig(config_version="edge-cost-summary-test")

    non_paper_observation = edge_observation(1, datetime(2026, 6, 1, tzinfo=UTC))
    object.__setattr__(non_paper_observation, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        build_paper_edge_cost_summary_report(
            [non_paper_observation],
            config=config,
            generated_at=GENERATED_AT,
        )

    incomplete_observation = edge_observation(2, datetime(2026, 6, 2, tzinfo=UTC))
    object.__setattr__(incomplete_observation, "fill_probability", None)
    with pytest.raises(ValueError, match="fill_probability"):
        build_paper_edge_cost_summary_report(
            [incomplete_observation],
            config=config,
            generated_at=GENERATED_AT,
        )
