from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_probability_model_disagreement_panel_v10 import (
    ProbabilityModelDisagreementPanel,
    ProbabilityModelForecastInput,
    StrategyProbabilityModelDisagreementPanelConfig,
    StrategyProbabilityModelForecast,
    build_strategy_probability_model_disagreement_panel,
    strategy_probability_model_disagreement_panel_payload,
)


def D(value: str) -> Decimal:
    return Decimal(value)


def forecast(
    model_id: str,
    probability: str,
    *,
    calibration: str = "0.900000",
    recency: str = "0.900000",
    coverage: str = "0.900000",
    rationale: str = "0.900000",
) -> StrategyProbabilityModelForecast:
    return StrategyProbabilityModelForecast(
        model_id=model_id,
        forecast_probability=D(probability),
        calibration_score=D(calibration),
        recency_weight=D(recency),
        source_coverage_score=D(coverage),
        rationale_quality_score=D(rationale),
    )


def test_builds_pass_panel_with_decimal_consensus_payload_and_flags() -> None:
    report = build_strategy_probability_model_disagreement_panel(
        (
            forecast("model_b", "0.570000"),
            forecast("model_a", "0.550000"),
        ),
    )

    assert isinstance(report, ProbabilityModelDisagreementPanel)
    assert report.consensus_probability == D("0.560000")
    assert report.disagreement_status == "pass"
    assert report.confidence_penalty == D("0.045000")
    assert report.reason_codes == ("probability_model_panel_ready",)
    assert tuple(row.model_id for row in report.model_rows) == ("model_a", "model_b")
    assert all(row.row_status == "pass" for row in report.model_rows)
    assert all(row.model_weight == D("0.900000") for row in report.model_rows)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.payload
    assert payload == strategy_probability_model_disagreement_panel_payload(report)
    assert payload["consensus_probability"] == "0.560000"
    assert payload["confidence_penalty"] == "0.045000"
    assert payload["model_rows"][0]["forecast_probability"] == "0.550000"
    assert payload["model_rows"][0]["paper_only"] is True


def test_weights_consensus_by_model_quality_scores() -> None:
    report = build_strategy_probability_model_disagreement_panel(
        (
            forecast(
                "high_weight",
                "0.800000",
                calibration="1.000000",
                recency="1.000000",
                coverage="1.000000",
                rationale="1.000000",
            ),
            forecast(
                "low_weight",
                "0.200000",
                calibration="0.200000",
                recency="0.200000",
                coverage="0.200000",
                rationale="0.200000",
            ),
        ),
    )

    assert report.consensus_probability == D("0.700000")
    assert report.disagreement_status == "blocked"
    assert report.reason_codes == (
        "low_quality_model_input",
        "model_consensus_gap_blocked",
        "model_probability_dispersion_blocked",
    )
    low_weight_row = report.model_rows[1]
    assert low_weight_row.model_id == "low_weight"
    assert low_weight_row.model_weight == D("0.200000")
    assert low_weight_row.consensus_gap == D("0.500000")
    assert low_weight_row.row_status == "blocked"


def test_watch_status_for_moderate_dispersion_without_blocking_gap() -> None:
    config = StrategyProbabilityModelDisagreementPanelConfig(
        watch_disagreement_gap=D("0.050000"),
        blocked_disagreement_gap=D("0.500000"),
    )

    report = build_strategy_probability_model_disagreement_panel(
        (
            forecast("model_a", "0.400000"),
            forecast("model_b", "0.520000"),
        ),
        config=config,
    )

    assert report.consensus_probability == D("0.460000")
    assert report.disagreement_status == "watch"
    assert report.reason_codes == (
        "model_consensus_gap_watch",
        "model_probability_dispersion_watch",
    )
    assert tuple(row.row_status for row in report.model_rows) == ("watch", "watch")


def test_missing_and_single_model_panels_are_blocked_reports() -> None:
    missing_report = build_strategy_probability_model_disagreement_panel(())
    assert missing_report.consensus_probability == D("0.000000")
    assert missing_report.confidence_penalty == D("1.000000")
    assert missing_report.disagreement_status == "blocked"
    assert missing_report.reason_codes == ("missing_models",)

    single_report = build_strategy_probability_model_disagreement_panel(
        (forecast("solo", "0.610000"),),
    )
    assert single_report.consensus_probability == D("0.610000")
    assert single_report.disagreement_status == "blocked"
    assert single_report.reason_codes == ("insufficient_model_count",)


def test_rejects_float_values_and_duplicate_model_ids() -> None:
    with pytest.raises(ValueError, match="forecast_probability must not be a float"):
        StrategyProbabilityModelForecast(
            model_id="floaty",
            forecast_probability=0.5,
            calibration_score=D("0.900000"),
            recency_weight=D("0.900000"),
            source_coverage_score=D("0.900000"),
            rationale_quality_score=D("0.900000"),
        )

    with pytest.raises(ValueError, match="model_id values must be unique"):
        build_strategy_probability_model_disagreement_panel(
            (
                forecast("same", "0.510000"),
                forecast("same", "0.520000"),
            ),
        )


def test_requires_decimal_inputs_and_readonly_report_flags() -> None:
    with pytest.raises(ValueError, match="calibration_score must be a Decimal"):
        StrategyProbabilityModelForecast(
            model_id="integer_score",
            forecast_probability=D("0.500000"),
            calibration_score=1,
            recency_weight=D("0.900000"),
            source_coverage_score=D("0.900000"),
            rationale_quality_score=D("0.900000"),
        )

    with pytest.raises(ValueError, match="forecast must be paper_only"):
        StrategyProbabilityModelForecast(
            model_id="bad_flag",
            forecast_probability=D("0.500000"),
            calibration_score=D("0.900000"),
            recency_weight=D("0.900000"),
            source_coverage_score=D("0.900000"),
            rationale_quality_score=D("0.900000"),
            paper_only=False,
        )

    report = build_strategy_probability_model_disagreement_panel(
        (
            forecast("model_a", "0.510000"),
            forecast("model_b", "0.520000"),
        ),
    )
    with pytest.raises(FrozenInstanceError):
        report.consensus_probability = D("0.530000")


def test_public_aliases_point_to_typed_frozen_dataclasses() -> None:
    model_input = ProbabilityModelForecastInput(
        model_id="alias_model",
        forecast_probability=D("0.500000"),
        calibration_score=D("0.800000"),
        recency_weight=D("0.800000"),
        source_coverage_score=D("0.800000"),
        rationale_quality_score=D("0.800000"),
    )

    with pytest.raises(FrozenInstanceError):
        model_input.forecast_probability = D("0.510000")

    report = build_strategy_probability_model_disagreement_panel(
        (
            model_input,
            forecast("other_model", "0.510000"),
        ),
    )
    assert isinstance(report, ProbabilityModelDisagreementPanel)
