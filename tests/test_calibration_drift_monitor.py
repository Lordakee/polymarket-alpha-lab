from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.calibration_drift_monitor import (
    CalibrationDriftMonitorConfig,
    CalibrationDriftMonitorReport,
    CalibrationDriftSlice,
    build_calibration_drift_monitor_report,
)
from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastOutcome,
    TeamForecastOutcomeDbRow,
    team_forecast_outcome_to_db_row,
    team_forecast_to_db_row,
)
from polymarket_alpha_lab.team_forecast_packet import TeamForecastPacket


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


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
            reason_codes=("calibration_drift_monitor_test",),
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
) -> TeamForecastOutcomeDbRow:
    resolved = resolved_at if resolved_at is not None else GENERATED_AT
    generated = generated_at if generated_at is not None else resolved + timedelta(minutes=5)
    actual_value = d("1.000000") if actual_outcome == "yes" else d("0.000000")
    forecast_error = abs(forecast.forecast_probability - actual_value)
    brier_score = forecast_error * forecast_error
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


def test_actual_no_drift_metrics_use_canonical_pyes_regardless_of_selected_side() -> None:
    reports = []
    slices = []
    outcomes = []

    for selected_side in ("yes", "no"):
        forecast = _forecast_row(
            "canonical-pyes-no-outcome",
            probability=d("0.200000"),
            selected_side=selected_side,
            generated_at=GENERATED_AT - timedelta(days=1),
        )
        outcome = _outcome_row(forecast, actual_outcome="no")
        report = build_calibration_drift_monitor_report(
            (forecast,),
            (outcome,),
            config=CalibrationDriftMonitorConfig(
                config_version="calibration-drift-pyes-contract-test",
                slice_days=14,
                min_settled_per_slice=1,
                ece_bucket_count=2,
                group_by="team",
            ),
            generated_at=GENERATED_AT,
        )
        outcomes.append(outcome)
        reports.append(report)
        slices.append(report.slices[0])

    assert tuple(outcome.brier_score for outcome in outcomes) == (
        d("0.040000"),
        d("0.040000"),
    )
    assert reports[0] == reports[1]
    assert slices[0] == slices[1]
    assert slices[1].average_brier_score == d("0.040000")
    assert slices[1].expected_calibration_error == d("0.200000")


def test_monitor_summarizes_brier_and_ece_drift_by_team_slices_without_market_identity() -> None:
    early_yes = _forecast_row(
        "early-yes",
        probability=d("0.800000"),
        generated_at=GENERATED_AT - timedelta(days=20),
    )
    early_no = _forecast_row(
        "early-no",
        probability=d("0.200000"),
        generated_at=GENERATED_AT - timedelta(days=19),
    )
    late_yes = _forecast_row(
        "late-yes",
        probability=d("0.600000"),
        generated_at=GENERATED_AT - timedelta(days=4),
    )
    late_no = _forecast_row(
        "late-no",
        probability=d("0.900000"),
        generated_at=GENERATED_AT - timedelta(days=3),
    )
    other_team = _forecast_row(
        "other-team",
        team_id="crypto_eth",
        category_id="finance.crypto.eth",
        event_template="eth_hit_price",
        probability=d("0.300000"),
        generated_at=GENERATED_AT - timedelta(days=2),
    )

    report = build_calibration_drift_monitor_report(
        (late_no, early_no, other_team, early_yes, late_yes),
        (
            _outcome_row(early_yes, actual_outcome="yes", resolved_at=GENERATED_AT - timedelta(days=18)),
            _outcome_row(early_no, actual_outcome="no", resolved_at=GENERATED_AT - timedelta(days=17)),
            _outcome_row(late_yes, actual_outcome="yes", resolved_at=GENERATED_AT - timedelta(days=2)),
            _outcome_row(late_no, actual_outcome="no", resolved_at=GENERATED_AT - timedelta(days=1)),
            _outcome_row(other_team, actual_outcome="no", resolved_at=GENERATED_AT - timedelta(days=1)),
        ),
        config=CalibrationDriftMonitorConfig(
            config_version="calibration-drift-monitor-test",
            slice_days=14,
            min_settled_per_slice=2,
            ece_bucket_count=2,
            group_by="team",
            brier_drift_warn_threshold=d("0.050000"),
            ece_drift_warn_threshold=d("0.050000"),
        ),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, CalibrationDriftMonitorReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "calibration-drift-monitor-test"
    assert report.group_by == "team"
    assert report.settled_count == 5
    assert report.group_count == 2
    assert report.slice_count == 3
    assert report.drift_watch_count == 1
    assert report.status == "drift_watch"
    assert report.reason_codes == ("calibration_drift_detected",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert report.slices == (
        CalibrationDriftSlice(
            group_type="team",
            group_key="crypto_btc",
            team_id="crypto_btc",
            category_id=None,
            slice_start_at=GENERATED_AT - timedelta(days=28),
            slice_end_at=GENERATED_AT - timedelta(days=14),
            settled_count=2,
            average_brier_score=d("0.040000"),
            expected_calibration_error=d("0.200000"),
            previous_average_brier_score=None,
            previous_expected_calibration_error=None,
            brier_score_delta=None,
            expected_calibration_error_delta=None,
            status="baseline",
            reason_codes=("baseline_slice",),
        ),
        CalibrationDriftSlice(
            group_type="team",
            group_key="crypto_btc",
            team_id="crypto_btc",
            category_id=None,
            slice_start_at=GENERATED_AT - timedelta(days=14),
            slice_end_at=GENERATED_AT,
            settled_count=2,
            average_brier_score=d("0.485000"),
            expected_calibration_error=d("0.250000"),
            previous_average_brier_score=d("0.040000"),
            previous_expected_calibration_error=d("0.200000"),
            brier_score_delta=d("0.445000"),
            expected_calibration_error_delta=d("0.050000"),
            status="drift_watch",
            reason_codes=(
                "brier_score_drift",
                "expected_calibration_error_drift",
            ),
        ),
        CalibrationDriftSlice(
            group_type="team",
            group_key="crypto_eth",
            team_id="crypto_eth",
            category_id=None,
            slice_start_at=GENERATED_AT - timedelta(days=14),
            slice_end_at=GENERATED_AT,
            settled_count=1,
            average_brier_score=d("0.090000"),
            expected_calibration_error=d("0.300000"),
            previous_average_brier_score=None,
            previous_expected_calibration_error=None,
            brier_score_delta=None,
            expected_calibration_error_delta=None,
            status="insufficient_slice_sample",
            reason_codes=("insufficient_settled_slice_sample",),
        ),
    )

    field_names = {field.name for field in fields(CalibrationDriftSlice)}
    assert "market_slug" not in field_names
    assert "question" not in field_names
    assert "recommendation" not in field_names


def test_monitor_supports_category_granularity_and_deduplicates_settled_rows() -> None:
    older_forecast = _forecast_row(
        "forecast-one",
        probability=d("0.200000"),
        generated_at=GENERATED_AT - timedelta(days=6),
    )
    latest_forecast = _forecast_row(
        "forecast-one",
        probability=d("0.800000"),
        generated_at=GENERATED_AT - timedelta(days=5),
    )
    second_forecast = _forecast_row(
        "forecast-two",
        probability=d("0.300000"),
        generated_at=GENERATED_AT - timedelta(days=4),
    )
    orphan_forecast = _forecast_row("forecast-orphan")

    old_outcome = _outcome_row(
        latest_forecast,
        outcome_id="old-outcome",
        actual_outcome="no",
        resolved_at=GENERATED_AT - timedelta(days=3),
    )
    latest_outcome = _outcome_row(
        latest_forecast,
        outcome_id="latest-outcome",
        actual_outcome="yes",
        resolved_at=GENERATED_AT - timedelta(days=2),
    )
    second_outcome = _outcome_row(
        second_forecast,
        actual_outcome="no",
        resolved_at=GENERATED_AT - timedelta(days=1),
    )
    orphan_outcome = _outcome_row(
        orphan_forecast,
        actual_outcome="yes",
        resolved_at=GENERATED_AT - timedelta(days=1),
    )

    report = build_calibration_drift_monitor_report(
        (older_forecast, latest_forecast, second_forecast),
        (old_outcome, latest_outcome, second_outcome, orphan_outcome),
        config=CalibrationDriftMonitorConfig(
            config_version="calibration-drift-monitor-test",
            slice_days=7,
            min_settled_per_slice=2,
            ece_bucket_count=2,
            group_by="category",
        ),
        generated_at=GENERATED_AT,
    )

    assert report.forecast_count == 2
    assert report.settled_count == 2
    assert report.duplicate_forecast_count == 1
    assert report.duplicate_outcome_count == 1
    assert report.orphan_outcome_count == 1
    assert report.group_by == "category"
    assert report.status == "stable"
    assert report.reason_codes == (
        "calibration_drift_not_detected",
        "duplicate_forecasts_deduplicated",
        "duplicate_outcomes_deduplicated",
        "orphan_outcomes_ignored",
    )
    assert tuple((row.group_type, row.group_key, row.category_id) for row in report.slices) == (
        ("category", "crypto_btc:finance.crypto.btc", "finance.crypto.btc"),
    )
    assert report.slices[0].average_brier_score == d("0.065000")
    assert report.slices[0].expected_calibration_error == d("0.250000")


def test_monitor_empty_report_is_readonly_and_contains_no_synthetic_metrics() -> None:
    report = build_calibration_drift_monitor_report(
        (),
        (),
        config=CalibrationDriftMonitorConfig(config_version="calibration-drift-monitor-test"),
        generated_at=GENERATED_AT,
    )

    assert report.forecast_count == 0
    assert report.settled_count == 0
    assert report.group_count == 0
    assert report.slice_count == 0
    assert report.drift_watch_count == 0
    assert report.status == "empty"
    assert report.reason_codes == ("no_settled_forecasts",)
    assert report.slices == ()


def test_monitor_rejects_non_decimal_thresholds_bad_flags_and_unsafe_rows() -> None:
    forecast = _forecast_row("forecast-btc-1")
    outcome = _outcome_row(forecast)

    with pytest.raises(ValueError, match="brier_drift_warn_threshold"):
        CalibrationDriftMonitorConfig(
            config_version="calibration-drift-monitor-test",
            brier_drift_warn_threshold="0.100000",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="group_by"):
        CalibrationDriftMonitorConfig(
            config_version="calibration-drift-monitor-test",
            group_by="market",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="paper_only"):
        CalibrationDriftMonitorConfig(
            config_version="calibration-drift-monitor-test",
            paper_only=False,
        )
    with pytest.raises(ValueError, match="forecast_rows"):
        build_calibration_drift_monitor_report(
            (row for row in (forecast,)),
            (outcome,),
            config=CalibrationDriftMonitorConfig(
                config_version="calibration-drift-monitor-test",
            ),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="TeamForecastDbRow"):
        build_calibration_drift_monitor_report(
            (_bypassed_row(forecast, readonly=False),),
            (outcome,),
            config=CalibrationDriftMonitorConfig(
                config_version="calibration-drift-monitor-test",
            ),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_calibration_drift_monitor_report(
            (forecast,),
            (outcome,),
            config=CalibrationDriftMonitorConfig(
                config_version="calibration-drift-monitor-test",
            ),
            generated_at=None,  # type: ignore[arg-type]
        )


def test_monitor_public_contracts_are_frozen() -> None:
    report = build_calibration_drift_monitor_report(
        (),
        (),
        config=CalibrationDriftMonitorConfig(config_version="calibration-drift-monitor-test"),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.settled_count = 99  # type: ignore[misc]
