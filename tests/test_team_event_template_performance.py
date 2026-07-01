from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
from typing import Any

import pytest

from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastOutcome,
    TeamForecastOutcomeDbRow,
    team_forecast_from_db_row,
    team_forecast_outcome_to_db_row,
    team_forecast_to_db_row,
)
from polymarket_alpha_lab.team_forecast_packet import TeamForecastPacket


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return importlib.import_module("polymarket_alpha_lab.team_event_template_performance")


def _forecast_row(
    forecast_id: str,
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    event_template: str = "btc_hit_price",
    probability: Decimal = d("0.800000"),
    confidence: Decimal = d("0.700000"),
    generated_at: datetime | None = None,
) -> TeamForecastDbRow:
    generated = generated_at if generated_at is not None else GENERATED_AT
    return team_forecast_to_db_row(
        TeamForecastPacket(
            forecast_id=forecast_id,
            team_id=team_id,
            condition_id=f"condition-{forecast_id}",
            market_slug=f"market-{forecast_id}",
            question=f"Will {forecast_id} resolve yes?",
            category_id=category_id,
            event_template=event_template,
            selected_side="yes",
            forecast_probability=probability,
            confidence=confidence,
            evidence_quality=d("0.800000"),
            data_freshness_score=d("0.900000"),
            resolution_risk=d("0.100000"),
            base_rate=d("0.540000"),
            market_implied_probability_observed=d("0.570000"),
            reason_codes=("team_event_template_performance_test",),
            memory_references=("memory-test",),
            source_references=("source-test",),
            known_failure_modes=("test_failure_mode",),
            config_version="team-forecast-v0",
            prompt_version="team-prompt-v0",
            generated_at=generated,
        ),
    )


def _outcome_row(
    forecast: TeamForecastDbRow,
    *,
    outcome_id: str | None = None,
    actual_outcome: str = "yes",
    resolved_at: datetime | None = None,
    generated_at: datetime | None = None,
    brier_score: Decimal | None = None,
    paper_pnl: Decimal = d("0.000000"),
    directionally_correct: bool | None = None,
    profitable_after_cost: bool = False,
    resolution_dispute_flag: bool = False,
) -> TeamForecastOutcomeDbRow:
    resolved = resolved_at if resolved_at is not None else GENERATED_AT + timedelta(days=1)
    generated = generated_at if generated_at is not None else resolved + timedelta(minutes=5)
    actual_value = d("1.000000") if actual_outcome == "yes" else d("0.000000")
    forecast_error = abs(forecast.forecast_probability - actual_value)
    score = brier_score if brier_score is not None else forecast_error * forecast_error
    if directionally_correct is None:
        directionally_correct = (
            forecast.forecast_probability >= d("0.500000")
            if actual_outcome == "yes"
            else forecast.forecast_probability < d("0.500000")
        )
    return team_forecast_outcome_to_db_row(
        TeamForecastOutcome(
            outcome_id=outcome_id or f"outcome-{forecast.forecast_id}",
            forecast_id=forecast.forecast_id,
            team_id=forecast.team_id,
            market_slug=forecast.market_slug,
            actual_outcome=actual_outcome,
            resolved_at=resolved,
            settlement_source="polymarket_public_resolution",
            forecast_error=forecast_error,
            brier_score=score,
            paper_pnl=paper_pnl,
            cost_adjusted_return=d("0.010000" if profitable_after_cost else "-0.010000"),
            directionally_correct=directionally_correct,
            profitable_after_cost=profitable_after_cost,
            resolution_dispute_flag=resolution_dispute_flag,
            reason_codes=(f"settled_{actual_outcome}",),
        ),
        config_version="team-forecast-outcome-v0",
        generated_at=generated,
    )


def _bypassed_row(row: object, **overrides: Any) -> object:
    malformed = object.__new__(type(row))
    for field in fields(row):
        object.__setattr__(malformed, field.name, getattr(row, field.name))
    for key, value in overrides.items():
        object.__setattr__(malformed, key, value)
    return malformed


def test_build_team_event_template_performance_report_groups_settled_templates() -> None:
    api = _api()
    first = _forecast_row(
        "forecast-btc-1",
        probability=d("0.800000"),
        confidence=d("0.700000"),
        generated_at=GENERATED_AT,
    )
    second = _forecast_row(
        "forecast-btc-2",
        probability=d("0.400000"),
        confidence=d("0.600000"),
        generated_at=GENERATED_AT + timedelta(minutes=1),
    )
    pending_same_template = _forecast_row(
        "forecast-btc-pending",
        probability=d("0.950000"),
        confidence=d("0.300000"),
        generated_at=GENERATED_AT + timedelta(minutes=2),
    )
    eth_template = _forecast_row(
        "forecast-eth-1",
        team_id="crypto_eth",
        category_id="finance.crypto.eth",
        event_template="eth_hit_price",
        probability=d("0.300000"),
        confidence=d("0.900000"),
        generated_at=GENERATED_AT,
    )

    report = api.build_team_event_template_performance_report(
        [pending_same_template, second, eth_template, first],
        [
            _outcome_row(
                first,
                actual_outcome="yes",
                brier_score=d("0.040000"),
                paper_pnl=d("0.150000"),
                profitable_after_cost=True,
            ),
            _outcome_row(
                second,
                actual_outcome="yes",
                brier_score=d("0.360000"),
                paper_pnl=d("-0.070000"),
                directionally_correct=False,
                profitable_after_cost=False,
                resolution_dispute_flag=True,
            ),
            _outcome_row(
                eth_template,
                actual_outcome="no",
                brier_score=d("0.090000"),
                paper_pnl=d("0.030000"),
                profitable_after_cost=True,
            ),
        ],
        config=api.TeamEventTemplatePerformanceConfig(
            config_version="team-event-template-performance-test",
            min_settled_forecasts=2,
            max_dispute_rate=d("0.750000"),
            min_profitable_after_cost_rate=d("0.400000"),
        ),
        generated_at=datetime(2026, 7, 1, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert type(report) is api.TeamEventTemplatePerformanceReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "team-event-template-performance-test"
    assert report.forecast_count == 4
    assert report.outcome_count == 3
    assert report.settled_count == 3
    assert report.duplicate_forecast_count == 0
    assert report.duplicate_outcome_count == 0
    assert report.orphan_outcome_count == 0
    assert report.row_count == 2
    assert report.status == "validated"
    assert report.reason_codes == ("min_settled_forecasts_met",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    btc, eth = report.rows
    assert type(btc) is api.TeamEventTemplatePerformanceRow
    assert (btc.team_id, btc.category_id, btc.event_template) == (
        "crypto_btc",
        "finance.crypto.btc",
        "btc_hit_price",
    )
    assert btc.forecast_count == 3
    assert btc.settled_count == 2
    assert btc.directionally_correct_count == 1
    assert btc.profitable_after_cost_count == 1
    assert btc.dispute_count == 1
    assert btc.average_brier_score == d("0.200000")
    assert btc.hit_rate == d("0.500000")
    assert btc.dispute_rate == d("0.500000")
    assert btc.profitable_after_cost_rate == d("0.500000")
    assert btc.paper_pnl == d("0.080000")
    assert btc.average_confidence == d("0.650000")
    assert btc.average_forecast_probability == d("0.600000")
    assert btc.status == "validated"
    assert btc.reason_codes == ("min_settled_forecasts_met",)
    assert btc.paper_only is True
    assert btc.report_only is True
    assert btc.readonly is True

    assert (eth.team_id, eth.category_id, eth.event_template) == (
        "crypto_eth",
        "finance.crypto.eth",
        "eth_hit_price",
    )
    assert eth.forecast_count == 1
    assert eth.settled_count == 1
    assert eth.average_brier_score == d("0.090000")
    assert eth.hit_rate == d("1.000000")
    assert eth.dispute_rate == d("0.000000")
    assert eth.profitable_after_cost_rate == d("1.000000")
    assert eth.paper_pnl == d("0.030000")
    assert eth.average_confidence == d("0.900000")
    assert eth.average_forecast_probability == d("0.300000")
    assert eth.status == "candidate"
    assert eth.reason_codes == ("insufficient_settled_forecasts",)


def test_status_marks_watch_for_dispute_or_profitability_threshold_breaches() -> None:
    api = _api()
    first = _forecast_row("forecast-btc-1")
    second = _forecast_row("forecast-btc-2")

    report = api.build_team_event_template_performance_report(
        (first, second),
        (
            _outcome_row(
                first,
                profitable_after_cost=False,
                resolution_dispute_flag=True,
                paper_pnl=d("-0.100000"),
            ),
            _outcome_row(
                second,
                profitable_after_cost=False,
                paper_pnl=d("-0.050000"),
            ),
        ),
        config=api.TeamEventTemplatePerformanceConfig(
            min_settled_forecasts=2,
            max_dispute_rate=d("0.250000"),
            min_profitable_after_cost_rate=d("0.500000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.status == "watch"
    assert report.reason_codes == (
        "dispute_rate_above_threshold",
        "profitability_rate_below_threshold",
    )
    assert report.rows[0].status == "watch"
    assert report.rows[0].reason_codes == (
        "dispute_rate_above_threshold",
        "profitability_rate_below_threshold",
    )
    assert report.rows[0].paper_pnl == d("-0.150000")


def test_builder_deduplicates_latest_forecasts_and_outcomes_and_counts_orphans() -> None:
    api = _api()
    older_forecast = _forecast_row(
        "forecast-btc-1",
        probability=d("0.200000"),
        confidence=d("0.400000"),
        generated_at=GENERATED_AT,
    )
    latest_forecast = _forecast_row(
        "forecast-btc-1",
        probability=d("0.800000"),
        confidence=d("0.900000"),
        generated_at=GENERATED_AT + timedelta(hours=1),
    )
    second_forecast = _forecast_row(
        "forecast-btc-2",
        probability=d("0.400000"),
        confidence=d("0.500000"),
        generated_at=GENERATED_AT,
    )
    orphan_forecast = _forecast_row("forecast-btc-orphan")

    older_outcome = _outcome_row(
        latest_forecast,
        outcome_id="outcome-older",
        actual_outcome="no",
        resolved_at=GENERATED_AT + timedelta(days=1),
        brier_score=d("0.640000"),
        paper_pnl=d("-0.300000"),
    )
    latest_outcome = _outcome_row(
        latest_forecast,
        outcome_id="outcome-latest",
        actual_outcome="yes",
        resolved_at=GENERATED_AT + timedelta(days=2),
        brier_score=d("0.040000"),
        paper_pnl=d("0.200000"),
        profitable_after_cost=True,
    )
    same_resolution_older_generated = _outcome_row(
        second_forecast,
        outcome_id="outcome-a",
        actual_outcome="yes",
        resolved_at=GENERATED_AT + timedelta(days=3),
        generated_at=GENERATED_AT + timedelta(days=3, minutes=1),
        brier_score=d("0.360000"),
        paper_pnl=d("-0.110000"),
    )
    same_resolution_latest_generated = _outcome_row(
        second_forecast,
        outcome_id="outcome-b",
        actual_outcome="no",
        resolved_at=GENERATED_AT + timedelta(days=3),
        generated_at=GENERATED_AT + timedelta(days=3, minutes=2),
        brier_score=d("0.160000"),
        paper_pnl=d("0.050000"),
        profitable_after_cost=True,
    )
    orphan_outcome = _outcome_row(
        orphan_forecast,
        outcome_id="outcome-orphan",
        brier_score=d("0.010000"),
        paper_pnl=d("1.000000"),
    )

    report = api.build_team_event_template_performance_report(
        [older_forecast, latest_forecast, second_forecast],
        [
            older_outcome,
            latest_outcome,
            same_resolution_older_generated,
            same_resolution_latest_generated,
            orphan_outcome,
        ],
        config=api.TeamEventTemplatePerformanceConfig(
            min_settled_forecasts=2,
            max_dispute_rate=d("0.250000"),
            min_profitable_after_cost_rate=d("0.500000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.forecast_count == 2
    assert report.outcome_count == 3
    assert report.settled_count == 2
    assert report.duplicate_forecast_count == 1
    assert report.duplicate_outcome_count == 2
    assert report.orphan_outcome_count == 1
    assert report.reason_codes == (
        "duplicate_forecasts_deduplicated",
        "duplicate_outcomes_deduplicated",
        "min_settled_forecasts_met",
        "orphan_outcomes_ignored",
    )

    row = report.rows[0]
    assert row.forecast_count == 2
    assert row.settled_count == 2
    assert row.average_brier_score == d("0.100000")
    assert row.paper_pnl == d("0.250000")
    assert row.average_confidence == d("0.700000")
    assert row.average_forecast_probability == d("0.600000")


def test_pending_only_templates_are_counted_but_not_emitted_as_rows() -> None:
    api = _api()
    pending = _forecast_row("forecast-btc-pending")

    report = api.build_team_event_template_performance_report(
        (pending,),
        (),
        config=api.TeamEventTemplatePerformanceConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.forecast_count == 1
    assert report.outcome_count == 0
    assert report.settled_count == 0
    assert report.row_count == 0
    assert report.rows == ()
    assert report.status == "candidate"
    assert report.reason_codes == ("insufficient_settled_forecasts",)


@pytest.mark.parametrize(
    ("forecast_rows", "outcome_rows", "message"),
    (
        ((row for row in ()), (), "forecast_rows must be a list or tuple"),
        ({}, (), "forecast_rows must be a list or tuple"),
        ("forecast-rows", (), "forecast_rows must be a list or tuple"),
        ((), (row for row in ()), "outcome_rows must be a list or tuple"),
        ((), {}, "outcome_rows must be a list or tuple"),
        ((), "outcome-rows", "outcome_rows must be a list or tuple"),
    ),
)
def test_builder_rejects_non_list_tuple_inputs(
    forecast_rows: object,
    outcome_rows: object,
    message: str,
) -> None:
    api = _api()

    with pytest.raises(ValueError, match=message):
        api.build_team_event_template_performance_report(
            forecast_rows,
            outcome_rows,
            config=api.TeamEventTemplatePerformanceConfig(),
            generated_at=GENERATED_AT,
        )


def test_builder_rejects_non_db_row_items_and_false_hard_flags() -> None:
    api = _api()
    forecast = _forecast_row("forecast-btc-1")
    outcome = _outcome_row(forecast)

    with pytest.raises(ValueError, match="forecast_rows items must be TeamForecastDbRow"):
        api.build_team_event_template_performance_report(
            [team_forecast_from_db_row(forecast)],
            [outcome],
            config=api.TeamEventTemplatePerformanceConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="outcome_rows items must be TeamForecastOutcomeDbRow"):
        api.build_team_event_template_performance_report(
            [forecast],
            [TeamForecastOutcome(
                outcome_id="outcome-packet",
                forecast_id=forecast.forecast_id,
                team_id=forecast.team_id,
                market_slug=forecast.market_slug,
                actual_outcome="yes",
                resolved_at=GENERATED_AT,
                settlement_source="polymarket_public_resolution",
                forecast_error=d("0.100000"),
                brier_score=d("0.010000"),
                paper_pnl=d("0.000000"),
                cost_adjusted_return=d("0.000000"),
                directionally_correct=True,
                profitable_after_cost=False,
                resolution_dispute_flag=False,
                reason_codes=("settled_yes",),
            )],
            config=api.TeamEventTemplatePerformanceConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="forecast row paper_only must be True"):
        api.build_team_event_template_performance_report(
            [_bypassed_row(forecast, paper_only=False)],
            [outcome],
            config=api.TeamEventTemplatePerformanceConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="outcome row readonly must be True"):
        api.build_team_event_template_performance_report(
            [forecast],
            [_bypassed_row(outcome, readonly=False)],
            config=api.TeamEventTemplatePerformanceConfig(),
            generated_at=GENERATED_AT,
        )


def test_public_exports_are_module_local_and_no_more() -> None:
    api = _api()

    assert api.__all__ == (
        "TeamEventTemplatePerformanceConfig",
        "TeamEventTemplatePerformanceReport",
        "TeamEventTemplatePerformanceRow",
        "build_team_event_template_performance_report",
    )
