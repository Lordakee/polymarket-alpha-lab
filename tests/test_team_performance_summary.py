from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_performance_summary import (
    TeamPerformanceSummaryConfig,
    build_team_performance_summary_report,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


@dataclass(frozen=True)
class ForecastStub:
    forecast_id: str
    team_id: str
    market_slug: str
    category_id: str
    selected_side: str
    forecast_probability: Decimal
    generated_at: datetime = GENERATED_AT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class OutcomeStub:
    outcome_id: str
    forecast_id: str
    team_id: str
    market_slug: str
    actual_outcome: str
    resolved_at: datetime
    paper_pnl: Decimal
    cost_adjusted_return: Decimal
    directionally_correct: bool | None = None
    profitable_after_cost: bool | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def test_summary_calculates_brier_from_raw_forecasts_and_excludes_unresolved():
    forecasts = (
        ForecastStub(
            forecast_id="forecast-btc-1",
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
            category_id="finance.crypto.btc",
            selected_side="yes",
            forecast_probability=Decimal("0.800000"),
        ),
        ForecastStub(
            forecast_id="forecast-btc-2",
            team_id="crypto_btc",
            market_slug="bitcoin-above-100k",
            category_id="finance.crypto.btc",
            selected_side="yes",
            forecast_probability=Decimal("0.400000"),
        ),
        ForecastStub(
            forecast_id="forecast-btc-unresolved",
            team_id="crypto_btc",
            market_slug="bitcoin-above-150k",
            category_id="finance.crypto.btc",
            selected_side="yes",
            forecast_probability=Decimal("0.990000"),
        ),
    )
    outcomes = (
        OutcomeStub(
            outcome_id="outcome-btc-1",
            forecast_id="forecast-btc-1",
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
            actual_outcome="yes",
            resolved_at=GENERATED_AT,
            paper_pnl=Decimal("1.200000"),
            cost_adjusted_return=Decimal("0.120000"),
            directionally_correct=True,
            profitable_after_cost=True,
        ),
        OutcomeStub(
            outcome_id="outcome-btc-2",
            forecast_id="forecast-btc-2",
            team_id="crypto_btc",
            market_slug="bitcoin-above-100k",
            actual_outcome="no",
            resolved_at=GENERATED_AT,
            paper_pnl=Decimal("-0.200000"),
            cost_adjusted_return=Decimal("-0.020000"),
            directionally_correct=True,
            profitable_after_cost=False,
        ),
    )

    report = build_team_performance_summary_report(
        forecasts,
        outcomes,
        config=TeamPerformanceSummaryConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.generated_at == GENERATED_AT
    assert report.forecast_count == 3
    assert report.settled_count == 2
    assert len(report.rows) == 1

    row = report.rows[0]
    assert row.team_id == "crypto_btc"
    assert row.category_id == "finance.crypto.btc"
    assert row.forecast_count == 3
    assert row.settled_count == 2
    assert row.directionally_correct_count == 2
    assert row.profitable_after_cost_count == 1
    assert row.average_brier_score == Decimal("0.100000")
    assert row.hit_rate == Decimal("1.000000")
    assert row.paper_pnl == Decimal("1.000000")
    assert row.cost_adjusted_return == Decimal("0.100000")
    assert row.team_trust_score == Decimal("1.000000")
    assert row.allocation_trust_score == Decimal("1.000000")
    assert "insufficient_trust_sample" in row.reason_codes
    assert "insufficient_allocation_sample" in row.reason_codes


def test_outcome_idempotency_uses_unique_forecast_id_not_outcome_id():
    forecasts = (
        ForecastStub(
            forecast_id="forecast-btc-1",
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
            category_id="finance.crypto.btc",
            selected_side="yes",
            forecast_probability=Decimal("0.800000"),
        ),
        ForecastStub(
            forecast_id="forecast-btc-2",
            team_id="crypto_btc",
            market_slug="bitcoin-above-100k",
            category_id="finance.crypto.btc",
            selected_side="yes",
            forecast_probability=Decimal("0.400000"),
        ),
    )
    outcomes = (
        OutcomeStub(
            outcome_id="outcome-btc-older",
            forecast_id="forecast-btc-1",
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
            actual_outcome="no",
            resolved_at=datetime(2026, 6, 30, 12, 0, tzinfo=UTC),
            paper_pnl=Decimal("-1.000000"),
            cost_adjusted_return=Decimal("-0.100000"),
            directionally_correct=False,
            profitable_after_cost=False,
        ),
        OutcomeStub(
            outcome_id="outcome-btc-latest",
            forecast_id="forecast-btc-1",
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
            actual_outcome="yes",
            resolved_at=GENERATED_AT,
            paper_pnl=Decimal("1.200000"),
            cost_adjusted_return=Decimal("0.120000"),
            directionally_correct=True,
            profitable_after_cost=True,
        ),
        OutcomeStub(
            outcome_id="outcome-btc-2",
            forecast_id="forecast-btc-2",
            team_id="crypto_btc",
            market_slug="bitcoin-above-100k",
            actual_outcome="no",
            resolved_at=GENERATED_AT,
            paper_pnl=Decimal("-0.200000"),
            cost_adjusted_return=Decimal("-0.020000"),
            directionally_correct=True,
            profitable_after_cost=False,
        ),
    )

    report = build_team_performance_summary_report(
        forecasts,
        outcomes,
        config=TeamPerformanceSummaryConfig(),
        generated_at=GENERATED_AT,
    )

    row = report.rows[0]
    assert row.settled_count == 2
    assert row.average_brier_score == Decimal("0.100000")
    assert row.paper_pnl == Decimal("1.000000")


def test_thresholds_clear_to_non_neutral_trust_and_allocation_scores():
    forecasts = tuple(
        ForecastStub(
            forecast_id=f"forecast-btc-{index}",
            team_id="crypto_btc",
            market_slug=f"bitcoin-{index}",
            category_id="finance.crypto.btc",
            selected_side="yes",
            forecast_probability=Decimal("0.800000"),
        )
        for index in range(50)
    )
    outcomes = tuple(
        OutcomeStub(
            outcome_id=f"outcome-btc-{index}",
            forecast_id=f"forecast-btc-{index}",
            team_id="crypto_btc",
            market_slug=f"bitcoin-{index}",
            actual_outcome="yes",
            resolved_at=GENERATED_AT,
            paper_pnl=Decimal("1.000000"),
            cost_adjusted_return=Decimal("0.100000"),
            directionally_correct=True,
            profitable_after_cost=True,
        )
        for index in range(50)
    )

    report = build_team_performance_summary_report(
        forecasts,
        outcomes,
        config=TeamPerformanceSummaryConfig(),
        generated_at=GENERATED_AT,
    )

    row = report.rows[0]
    assert row.settled_count == 50
    assert row.team_trust_score == Decimal("1.200000")
    assert row.allocation_trust_score == Decimal("1.100000")
    assert "trust_sample_ready" in row.reason_codes
    assert "allocation_sample_ready" in row.reason_codes
    assert "insufficient_trust_sample" not in row.reason_codes
    assert "insufficient_allocation_sample" not in row.reason_codes


def test_rows_are_grouped_by_team_and_category_and_are_frozen():
    forecasts = (
        ForecastStub(
            forecast_id="forecast-btc-1",
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
            category_id="finance.crypto.btc",
            selected_side="yes",
            forecast_probability=Decimal("0.800000"),
        ),
        ForecastStub(
            forecast_id="forecast-eth-1",
            team_id="crypto_eth",
            market_slug="ethereum-above-8k",
            category_id="finance.crypto.eth",
            selected_side="yes",
            forecast_probability=Decimal("0.300000"),
        ),
    )
    outcomes = (
        OutcomeStub(
            outcome_id="outcome-eth-1",
            forecast_id="forecast-eth-1",
            team_id="crypto_eth",
            market_slug="ethereum-above-8k",
            actual_outcome="no",
            resolved_at=GENERATED_AT,
            paper_pnl=Decimal("0.500000"),
            cost_adjusted_return=Decimal("0.050000"),
        ),
    )

    report = build_team_performance_summary_report(
        forecasts,
        outcomes,
        config=TeamPerformanceSummaryConfig(),
        generated_at=GENERATED_AT,
    )

    assert tuple((row.team_id, row.category_id) for row in report.rows) == (
        ("crypto_btc", "finance.crypto.btc"),
        ("crypto_eth", "finance.crypto.eth"),
    )
    assert report.rows[0].settled_count == 0
    assert report.rows[0].average_brier_score == Decimal("0.000000")
    assert "no_settled_forecasts" in report.rows[0].reason_codes

    with pytest.raises(FrozenInstanceError):
        report.rows[0].forecast_count = 99  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        report.forecast_count = 99  # type: ignore[misc]


def test_float_metrics_and_false_safety_flags_raise():
    with pytest.raises(ValueError, match="min_trust_sample_count"):
        TeamPerformanceSummaryConfig(min_trust_sample_count=0)

    with pytest.raises(ValueError, match="team_trust_floor"):
        TeamPerformanceSummaryConfig(team_trust_floor=0.5)  # type: ignore[arg-type]

    forecast_with_float = ForecastStub(
        forecast_id="forecast-btc-1",
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        category_id="finance.crypto.btc",
        selected_side="yes",
        forecast_probability=Decimal("0.800000"),
    )
    object.__setattr__(forecast_with_float, "forecast_probability", 0.8)
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        build_team_performance_summary_report(
            (forecast_with_float,),
            (),
            config=TeamPerformanceSummaryConfig(),
            generated_at=GENERATED_AT,
        )

    unsafe_forecast = ForecastStub(
        forecast_id="forecast-btc-1",
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        category_id="finance.crypto.btc",
        selected_side="yes",
        forecast_probability=Decimal("0.800000"),
        paper_only=False,
    )
    with pytest.raises(ValueError, match="paper_only must be True"):
        build_team_performance_summary_report(
            (unsafe_forecast,),
            (),
            config=TeamPerformanceSummaryConfig(),
            generated_at=GENERATED_AT,
        )

