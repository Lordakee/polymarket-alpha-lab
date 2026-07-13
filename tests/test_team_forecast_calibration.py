from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.team_forecast_calibration import (
    TeamForecastCalibrationConfig,
    TeamForecastCalibrationReport,
    build_team_forecast_calibration_report,
)
from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastOutcome,
    TeamForecastOutcomeDbRow,
    team_forecast_from_db_row,
    team_forecast_outcome_from_db_row,
    team_forecast_outcome_to_db_row,
    team_forecast_to_db_row,
)
from polymarket_alpha_lab.team_forecast_packet import TeamForecastPacket


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _forecast_row(
    forecast_id: str,
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    event_template: str = "btc_hit_price",
    probability: Decimal = d("0.800000"),
    confidence: Decimal = d("0.700000"),
    selected_side: str = "yes",
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
            selected_side=selected_side,
            forecast_probability=probability,
            confidence=confidence,
            evidence_quality=d("0.800000"),
            data_freshness_score=d("0.900000"),
            resolution_risk=d("0.100000"),
            base_rate=d("0.540000"),
            market_implied_probability_observed=d("0.570000"),
            reason_codes=("team_forecast_calibration_test",),
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
    directionally_correct: bool | None = None,
) -> TeamForecastOutcomeDbRow:
    resolved = resolved_at if resolved_at is not None else GENERATED_AT + timedelta(days=1)
    generated = generated_at if generated_at is not None else resolved + timedelta(minutes=5)
    actual_value = d("1.000000") if actual_outcome == "yes" else d("0.000000")
    forecast_error = abs(forecast.forecast_probability - actual_value)
    brier_score = forecast_error * forecast_error
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
            brier_score=brier_score,
            paper_pnl=d("0.000000"),
            cost_adjusted_return=d("0.000000"),
            directionally_correct=directionally_correct,
            profitable_after_cost=False,
            resolution_dispute_flag=False,
            reason_codes=(f"settled_{actual_outcome}",),
        ),
        config_version="team-forecast-outcome-v0",
        generated_at=generated,
    )


def _bypassed_row(row: object, **overrides: Any) -> object:
    malformed = object.__new__(type(row))
    for key, value in row.__dict__.items():
        object.__setattr__(malformed, key, value)
    for key, value in overrides.items():
        object.__setattr__(malformed, key, value)
    return malformed


def test_actual_no_metrics_use_canonical_pyes_regardless_of_selected_side() -> None:
    reports = []
    groups = []
    outcomes = []

    for selected_side in ("yes", "no"):
        forecast = _forecast_row(
            "canonical-pyes-no-outcome",
            probability=d("0.200000"),
            selected_side=selected_side,
        )
        outcome = _outcome_row(forecast, actual_outcome="no")
        report = build_team_forecast_calibration_report(
            (forecast,),
            (outcome,),
            config=TeamForecastCalibrationConfig(
                config_version="team-calibration-pyes-contract-test",
                bucket_count=2,
                min_settled_forecasts=1,
            ),
            generated_at=GENERATED_AT,
        )
        outcomes.append(outcome)
        reports.append(report)
        groups.append(report.groups[0])

    assert tuple(outcome.brier_score for outcome in outcomes) == (
        d("0.040000"),
        d("0.040000"),
    )
    assert reports[0] == reports[1]
    assert groups[0] == groups[1]
    assert groups[1].observed_yes_rate == d("0.000000")
    assert groups[1].average_forecast_probability == d("0.200000")
    assert groups[1].average_brier_score == d("0.040000")
    assert groups[1].calibration_error == d("0.200000")


def test_build_team_forecast_calibration_report_summarizes_team_buckets_and_metrics() -> None:
    first = _forecast_row(
        "forecast-btc-1",
        probability=d("0.800000"),
        confidence=d("0.700000"),
        generated_at=GENERATED_AT,
    )
    second = _forecast_row(
        "forecast-btc-2",
        probability=d("0.200000"),
        confidence=d("0.500000"),
        generated_at=GENERATED_AT + timedelta(minutes=1),
    )
    third = _forecast_row(
        "forecast-btc-3",
        probability=d("0.600000"),
        confidence=d("0.900000"),
        generated_at=GENERATED_AT + timedelta(minutes=2),
    )
    unsettled = _forecast_row(
        "forecast-btc-unsettled",
        probability=d("0.950000"),
        confidence=d("0.300000"),
        generated_at=GENERATED_AT + timedelta(minutes=3),
    )

    report = build_team_forecast_calibration_report(
        (third, unsettled, second, first),
        (
            _outcome_row(first, actual_outcome="yes"),
            _outcome_row(second, actual_outcome="no"),
            _outcome_row(third, actual_outcome="no", directionally_correct=False),
        ),
        config=TeamForecastCalibrationConfig(
            config_version="team-calibration-test",
            bucket_count=2,
            min_settled_forecasts=3,
        ),
        generated_at=datetime(2026, 7, 1, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, TeamForecastCalibrationReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "team-calibration-test"
    assert report.forecast_count == 4
    assert report.settled_count == 3
    assert report.duplicate_forecast_count == 0
    assert report.duplicate_outcome_count == 0
    assert report.orphan_outcome_count == 0
    assert report.status == "validated"
    assert report.reason_codes == ("min_settled_forecasts_met",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(group.group_type for group in report.groups) == (
        "team",
        "category",
        "event_template",
    )
    team_group = report.groups[0]
    assert team_group.group_key == "crypto_btc"
    assert team_group.team_id == "crypto_btc"
    assert team_group.category_id is None
    assert team_group.event_template is None
    assert team_group.forecast_count == 4
    assert team_group.settled_count == 3
    assert team_group.observed_yes_rate == d("0.333333")
    assert team_group.average_forecast_probability == d("0.533333")
    assert team_group.average_confidence == d("0.700000")
    assert team_group.average_brier_score == d("0.146667")
    assert team_group.calibration_error == d("0.200000")
    assert team_group.directionally_correct_count == 2
    assert team_group.status == "validated"
    assert team_group.reason_codes == ("min_settled_forecasts_met",)

    assert tuple(bucket.bucket_label for bucket in team_group.buckets) == (
        "0.000000-0.500000",
        "0.500000-1.000000",
    )
    assert team_group.buckets[0].forecast_count == 1
    assert team_group.buckets[0].settled_count == 1
    assert team_group.buckets[0].observed_yes_rate == d("0.000000")
    assert team_group.buckets[0].average_forecast_probability == d("0.200000")
    assert team_group.buckets[0].average_confidence == d("0.500000")
    assert team_group.buckets[0].average_brier_score == d("0.040000")
    assert team_group.buckets[0].calibration_error == d("0.200000")
    assert team_group.buckets[0].directionally_correct_count == 1

    assert team_group.buckets[1].forecast_count == 3
    assert team_group.buckets[1].settled_count == 2
    assert team_group.buckets[1].observed_yes_rate == d("0.500000")
    assert team_group.buckets[1].average_forecast_probability == d("0.700000")
    assert team_group.buckets[1].average_confidence == d("0.800000")
    assert team_group.buckets[1].average_brier_score == d("0.200000")
    assert team_group.buckets[1].calibration_error == d("0.200000")
    assert team_group.buckets[1].directionally_correct_count == 1


def test_builder_deduplicates_forecasts_and_outcomes_and_counts_orphans() -> None:
    older_forecast = _forecast_row(
        "forecast-btc-1",
        probability=d("0.200000"),
        generated_at=GENERATED_AT,
    )
    latest_forecast = _forecast_row(
        "forecast-btc-1",
        probability=d("0.800000"),
        generated_at=GENERATED_AT + timedelta(hours=1),
    )
    second_forecast = _forecast_row(
        "forecast-btc-2",
        probability=d("0.400000"),
        generated_at=GENERATED_AT,
    )
    orphan_forecast = _forecast_row("forecast-btc-orphan")

    older_outcome = _outcome_row(
        latest_forecast,
        outcome_id="outcome-older",
        actual_outcome="no",
        resolved_at=GENERATED_AT + timedelta(days=1),
    )
    latest_outcome = _outcome_row(
        latest_forecast,
        outcome_id="outcome-latest",
        actual_outcome="yes",
        resolved_at=GENERATED_AT + timedelta(days=2),
    )
    same_resolution_latest_generated = _outcome_row(
        second_forecast,
        outcome_id="outcome-b",
        actual_outcome="no",
        resolved_at=GENERATED_AT + timedelta(days=3),
        generated_at=GENERATED_AT + timedelta(days=3, minutes=2),
    )
    same_resolution_older_generated = _outcome_row(
        second_forecast,
        outcome_id="outcome-a",
        actual_outcome="yes",
        resolved_at=GENERATED_AT + timedelta(days=3),
        generated_at=GENERATED_AT + timedelta(days=3, minutes=1),
    )
    orphan_outcome = _outcome_row(
        orphan_forecast,
        outcome_id="outcome-orphan",
        actual_outcome="yes",
    )

    report = build_team_forecast_calibration_report(
        (older_forecast, latest_forecast, second_forecast),
        (
            older_outcome,
            latest_outcome,
            same_resolution_older_generated,
            same_resolution_latest_generated,
            orphan_outcome,
        ),
        config=TeamForecastCalibrationConfig(
            config_version="team-calibration-test",
            bucket_count=2,
            min_settled_forecasts=3,
        ),
        generated_at=GENERATED_AT,
    )

    assert report.forecast_count == 2
    assert report.settled_count == 2
    assert report.duplicate_forecast_count == 1
    assert report.duplicate_outcome_count == 2
    assert report.orphan_outcome_count == 1
    assert report.status == "candidate"
    assert report.reason_codes == (
        "duplicate_forecasts_deduplicated",
        "duplicate_outcomes_deduplicated",
        "insufficient_settled_forecasts",
        "orphan_outcomes_ignored",
    )

    team_group = report.groups[0]
    assert team_group.average_forecast_probability == d("0.600000")
    assert team_group.observed_yes_rate == d("0.500000")
    assert team_group.average_brier_score == d("0.100000")


def test_builder_emits_only_team_group_when_subgroups_do_not_meet_sample_threshold() -> None:
    btc = _forecast_row(
        "forecast-btc-1",
        probability=d("0.800000"),
        team_id="crypto_btc",
        category_id="finance.crypto.btc",
        event_template="btc_hit_price",
    )
    eth = _forecast_row(
        "forecast-eth-1",
        probability=d("0.300000"),
        team_id="crypto_eth",
        category_id="finance.crypto.eth",
        event_template="eth_hit_price",
    )

    report = build_team_forecast_calibration_report(
        (btc, eth),
        (_outcome_row(btc, actual_outcome="yes"), _outcome_row(eth, actual_outcome="no")),
        config=TeamForecastCalibrationConfig(
            config_version="team-calibration-test",
            min_settled_forecasts=2,
            min_group_settled_forecasts=2,
        ),
        generated_at=GENERATED_AT,
    )

    assert tuple((group.group_type, group.group_key) for group in report.groups) == (
        ("team", "crypto_btc"),
        ("team", "crypto_eth"),
    )
    assert report.status == "validated"


def test_builder_accepts_empty_lists_and_marks_candidate_without_groups() -> None:
    report = build_team_forecast_calibration_report(
        [],
        [],
        config=TeamForecastCalibrationConfig(config_version="team-calibration-test"),
        generated_at=GENERATED_AT,
    )

    assert report.forecast_count == 0
    assert report.settled_count == 0
    assert report.groups == ()
    assert report.status == "candidate"
    assert report.reason_codes == (
        "insufficient_settled_forecasts",
        "no_forecasts",
        "no_settled_forecasts",
    )


def test_builder_rejects_non_exact_row_types_iterables_and_false_flags() -> None:
    forecast = _forecast_row("forecast-btc-1")
    outcome = _outcome_row(forecast)
    config = TeamForecastCalibrationConfig(config_version="team-calibration-test")

    for bad_forecasts in (
        (row for row in (forecast,)),
        {"forecast": forecast},
        "forecast",
        b"forecast",
    ):
        with pytest.raises(ValueError, match="forecast_rows"):
            build_team_forecast_calibration_report(
                bad_forecasts,
                (outcome,),
                config=config,
                generated_at=GENERATED_AT,
            )

    for bad_outcomes in (
        (row for row in (outcome,)),
        {"outcome": outcome},
        "outcome",
        b"outcome",
    ):
        with pytest.raises(ValueError, match="outcome_rows"):
            build_team_forecast_calibration_report(
                (forecast,),
                bad_outcomes,
                config=config,
                generated_at=GENERATED_AT,
            )

    with pytest.raises(ValueError, match="TeamForecastDbRow"):
        build_team_forecast_calibration_report(
            (team_forecast_from_db_row(forecast),),
            (outcome,),
            config=config,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="TeamForecastOutcomeDbRow"):
        build_team_forecast_calibration_report(
            (forecast,),
            (team_forecast_outcome_from_db_row(outcome),),
            config=config,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="paper_only"):
        build_team_forecast_calibration_report(
            (_bypassed_row(forecast, paper_only=False),),
            (outcome,),
            config=config,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="report_only"):
        build_team_forecast_calibration_report(
            (forecast,),
            (_bypassed_row(outcome, report_only=False),),
            config=config,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="config"):
        build_team_forecast_calibration_report(
            (forecast,),
            (outcome,),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="generated_at"):
        build_team_forecast_calibration_report(
            (forecast,),
            (outcome,),
            config=config,
            generated_at=None,
        )


def test_dataclasses_validate_invariants_and_are_frozen() -> None:
    with pytest.raises(ValueError, match="bucket_count"):
        TeamForecastCalibrationConfig(
            config_version="team-calibration-test",
            bucket_count=0,
        )
    with pytest.raises(ValueError, match="min_settled_forecasts"):
        TeamForecastCalibrationConfig(
            config_version="team-calibration-test",
            min_settled_forecasts=-1,
        )
    with pytest.raises(ValueError, match="paper_only"):
        TeamForecastCalibrationConfig(
            config_version="team-calibration-test",
            paper_only=False,
        )

    forecast = _forecast_row("forecast-btc-1")
    report = build_team_forecast_calibration_report(
        (forecast,),
        (_outcome_row(forecast),),
        config=TeamForecastCalibrationConfig(
            config_version="team-calibration-test",
            min_settled_forecasts=1,
        ),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.forecast_count = 99  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.groups[0].buckets[0].settled_count = 99  # type: ignore[misc]
