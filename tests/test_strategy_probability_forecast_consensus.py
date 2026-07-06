from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_probability_forecast_consensus import (
    StrategyProbabilityForecastConsensusConfig,
    StrategyProbabilityForecastConsensusInput,
    StrategyProbabilityForecastConsensusReport,
    build_strategy_probability_forecast_consensus,
)


NOW = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


def _forecast(
    team_id: str,
    probability: str,
    *,
    weight: str = "1",
    confidence: str = "1",
) -> StrategyProbabilityForecastConsensusInput:
    return StrategyProbabilityForecastConsensusInput(
        team_id=team_id,
        forecast_probability=Decimal(probability),
        weight=Decimal(weight),
        confidence=Decimal(confidence),
        reason_codes=(f"{team_id}_forecast",),
    )


def test_weighted_consensus_uses_weight_times_confidence_and_reports_dispersion() -> None:
    report = build_strategy_probability_forecast_consensus(
        (
            _forecast("sports", "0.600000", weight="2", confidence="0.900000"),
            _forecast("macro", "0.400000", weight="1", confidence="0.600000"),
        ),
        generated_at=NOW,
    )

    assert report.consensus_probability == Decimal("0.550000")
    assert report.dispersion_score == Decimal("0.075000")
    assert report.average_confidence == Decimal("0.800000")
    assert report.total_effective_weight == Decimal("2.400000")
    assert report.forecast_count == Decimal("2.000000")
    assert report.consensus_status == "ready"
    assert report.reason_codes == ("consensus_ready",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_dispersion_marks_conflict() -> None:
    report = build_strategy_probability_forecast_consensus(
        (
            _forecast("sports", "0.200000"),
            _forecast("macro", "0.900000"),
        ),
        generated_at=NOW,
    )

    assert report.consensus_probability == Decimal("0.550000")
    assert report.dispersion_score == Decimal("0.350000")
    assert report.consensus_status == "conflict"
    assert report.reason_codes == ("high_dispersion", "consensus_conflict")


def test_low_average_confidence_marks_watch_even_when_probabilities_agree() -> None:
    report = build_strategy_probability_forecast_consensus(
        (
            _forecast("sports", "0.700000", confidence="0.200000"),
            _forecast("macro", "0.700000", confidence="0.200000"),
        ),
        generated_at=NOW,
        config=StrategyProbabilityForecastConsensusConfig(
            min_average_confidence=Decimal("0.500000"),
        ),
    )

    assert report.consensus_probability == Decimal("0.700000")
    assert report.dispersion_score == Decimal("0.000000")
    assert report.average_confidence == Decimal("0.200000")
    assert report.consensus_status == "watch"
    assert report.reason_codes == ("low_average_confidence", "consensus_watch")


def test_empty_forecasts_return_readonly_insufficient_evidence_report() -> None:
    report = build_strategy_probability_forecast_consensus((), generated_at=NOW)

    assert report.consensus_probability == Decimal("0.000000")
    assert report.dispersion_score == Decimal("0.000000")
    assert report.average_confidence == Decimal("0.000000")
    assert report.total_effective_weight == Decimal("0.000000")
    assert report.forecast_count == Decimal("0.000000")
    assert report.consensus_status == "insufficient_evidence"
    assert report.reason_codes == ("no_forecasts", "insufficient_forecast_count")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_rejects_float_probability_for_decimal_only_surface() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        StrategyProbabilityForecastConsensusInput(
            team_id="sports",
            forecast_probability=0.55,  # type: ignore[arg-type]
            weight=Decimal("1"),
            confidence=Decimal("1"),
            reason_codes=("float_probability",),
        )


def test_rejects_duplicate_team_ids() -> None:
    with pytest.raises(ValueError, match="duplicate.*team_id"):
        build_strategy_probability_forecast_consensus(
            (
                _forecast("sports", "0.600000"),
                _forecast("sports", "0.700000"),
            ),
            generated_at=NOW,
        )


def test_input_and_report_are_frozen_and_hard_flagged() -> None:
    row = _forecast("sports", "0.600000")
    with pytest.raises(FrozenInstanceError):
        row.weight = Decimal("2")  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly"):
        StrategyProbabilityForecastConsensusReport(
            generated_at=NOW,
            config_version="strategy-probability-forecast-consensus-v0",
            forecast_count=Decimal("0"),
            total_weight=Decimal("0"),
            total_effective_weight=Decimal("0"),
            average_confidence=Decimal("0"),
            consensus_probability=Decimal("0"),
            dispersion_score=Decimal("0"),
            consensus_status="insufficient_evidence",
            forecasts=(),
            reason_codes=("no_forecasts",),
            readonly=False,
        )
