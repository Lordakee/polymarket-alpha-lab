from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.forecast_confidence_backtest_readiness import (
    ForecastConfidenceBacktestReadinessConfig,
    ForecastConfidenceBacktestReadinessReport,
    forecast_confidence_backtest_readiness_payload,
    build_forecast_confidence_backtest_readiness_report,
)
from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastOutcome,
    TeamForecastOutcomeDbRow,
    team_forecast_outcome_from_db_row,
    team_forecast_outcome_to_db_row,
    team_forecast_to_db_row,
)
from polymarket_alpha_lab.team_forecast_packet import TeamForecastPacket


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _forecast_row(
    forecast_id: str,
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    probability: Decimal = d("0.700000"),
    confidence: Decimal = d("0.800000"),
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
            event_template="confidence_readiness_test",
            selected_side="yes",
            forecast_probability=probability,
            confidence=confidence,
            evidence_quality=d("0.800000"),
            data_freshness_score=d("0.900000"),
            resolution_risk=d("0.100000"),
            base_rate=d("0.500000"),
            market_implied_probability_observed=d("0.550000"),
            reason_codes=("forecast_confidence_readiness_test",),
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
    resolution_dispute_flag: bool = False,
) -> TeamForecastOutcomeDbRow:
    resolved = resolved_at if resolved_at is not None else GENERATED_AT + timedelta(days=1)
    generated = generated_at if generated_at is not None else resolved + timedelta(minutes=5)
    actual_value = d("1.000000") if actual_outcome == "yes" else d("0.000000")
    forecast_error = abs(forecast.forecast_probability - actual_value)
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
            brier_score=forecast_error * forecast_error,
            paper_pnl=ZERO,
            cost_adjusted_return=ZERO,
            directionally_correct=True,
            profitable_after_cost=False,
            resolution_dispute_flag=resolution_dispute_flag,
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


def _config(**overrides: object) -> ForecastConfidenceBacktestReadinessConfig:
    values: dict[str, object] = {
        "config_version": "confidence-backtest-readiness-test",
        "group_by": "team",
        "min_resolved_observations": 3,
        "min_confidence_bucket_count": 2,
        "min_average_confidence": d("0.650000"),
        "min_resolution_coverage_ratio": d("0.750000"),
    }
    values.update(overrides)
    return ForecastConfidenceBacktestReadinessConfig(**values)


def _report(
    forecasts: tuple[TeamForecastDbRow, ...],
    outcomes: tuple[TeamForecastOutcomeDbRow, ...],
    *,
    cfg: ForecastConfidenceBacktestReadinessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ForecastConfidenceBacktestReadinessReport:
    return build_forecast_confidence_backtest_readiness_report(
        forecasts,
        outcomes,
        config=cfg or _config(),
        generated_at=generated_at,
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_floats(item)


def test_report_marks_group_ready_when_resolved_paper_observations_are_sufficient() -> None:
    first = _forecast_row("btc-1", confidence=d("0.900000"))
    second = _forecast_row("btc-2", confidence=d("0.700000"))
    third = _forecast_row("btc-3", confidence=d("0.600000"))
    unsettled = _forecast_row("btc-4", confidence=d("0.400000"))

    report = _report(
        (third, unsettled, first, second),
        (_outcome_row(first), _outcome_row(second), _outcome_row(third)),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "confidence-backtest-readiness-test"
    assert report.group_by == "team"
    assert report.forecast_count == 4
    assert report.resolved_observation_count == 3
    assert report.unresolved_forecast_count == 1
    assert report.duplicate_forecast_count == 0
    assert report.duplicate_outcome_count == 0
    assert report.orphan_outcome_count == 0
    assert report.disputed_outcome_count == 0
    assert report.group_count == 1
    assert report.ready_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.status == "ready"
    assert report.reason_codes == ("backtest_readiness_ready",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert row.group_type == "team"
    assert row.group_key == "crypto_btc"
    assert row.team_id == "crypto_btc"
    assert row.category_id is None
    assert row.forecast_count == 4
    assert row.resolved_observation_count == 3
    assert row.unresolved_forecast_count == 1
    assert row.resolution_coverage_ratio == d("0.750000")
    assert row.average_confidence == d("0.733333")
    assert row.min_confidence == d("0.600000")
    assert row.max_confidence == d("0.900000")
    assert row.confidence_bucket_count == 3
    assert row.status == "ready"
    assert row.reason_codes == ("backtest_readiness_ready",)


def test_report_watches_or_blocks_groups_with_insufficient_resolved_confidence_samples() -> None:
    btc = tuple(
        _forecast_row(f"btc-{index}", confidence=d("0.900000"))
        for index in range(1, 5)
    )
    eth = tuple(
        _forecast_row(
            f"eth-{index}",
            team_id="crypto_eth",
            category_id="finance.crypto.eth",
            confidence=d("0.500000"),
        )
        for index in range(1, 4)
    )
    config = _config(min_resolution_coverage_ratio=d("0.500000"))

    report = _report(
        btc + eth,
        (
            _outcome_row(btc[0]),
            _outcome_row(btc[1]),
            _outcome_row(eth[0]),
            _outcome_row(eth[1]),
            _outcome_row(eth[2], resolution_dispute_flag=True),
        ),
        cfg=config,
    )

    assert tuple(row.group_key for row in report.rows) == ("crypto_btc", "crypto_eth")
    assert tuple(row.status for row in report.rows) == ("watch", "blocked")
    assert report.ready_count == 0
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert report.status == "blocked"
    assert report.reason_codes == (
        "blocked_backtest_readiness_group",
        "watch_backtest_readiness_group",
    )
    assert report.rows[0].reason_codes == (
        "confidence_bucket_coverage_watch",
        "insufficient_resolved_observations",
    )
    assert report.rows[1].reason_codes == (
        "disputed_outcomes_present",
        "low_average_confidence",
        "single_confidence_bucket",
    )


def test_report_can_group_by_category_and_counts_duplicates_and_orphans_deterministically() -> None:
    older_forecast = _forecast_row(
        "btc-1",
        confidence=d("0.400000"),
        generated_at=GENERATED_AT - timedelta(hours=1),
    )
    latest_forecast = _forecast_row(
        "btc-1",
        confidence=d("0.900000"),
        generated_at=GENERATED_AT,
    )
    second = _forecast_row("btc-2", confidence=d("0.700000"))
    orphan = _forecast_row("btc-orphan", confidence=d("0.800000"))
    older_outcome = _outcome_row(
        latest_forecast,
        outcome_id="outcome-old",
        resolved_at=GENERATED_AT + timedelta(days=1),
        generated_at=GENERATED_AT + timedelta(days=1, minutes=1),
    )
    latest_outcome = _outcome_row(
        latest_forecast,
        outcome_id="outcome-new",
        resolved_at=GENERATED_AT + timedelta(days=2),
        generated_at=GENERATED_AT + timedelta(days=2, minutes=1),
    )

    report = _report(
        (older_forecast, latest_forecast, second),
        (older_outcome, latest_outcome, _outcome_row(second), _outcome_row(orphan)),
        cfg=_config(group_by="category", min_resolved_observations=2),
    )

    assert report.forecast_count == 2
    assert report.resolved_observation_count == 2
    assert report.duplicate_forecast_count == 1
    assert report.duplicate_outcome_count == 1
    assert report.orphan_outcome_count == 1
    assert report.status == "ready"
    assert report.reason_codes == (
        "backtest_readiness_ready",
        "duplicate_forecasts_deduplicated",
        "duplicate_outcomes_deduplicated",
        "orphan_outcomes_ignored",
    )
    assert tuple((row.group_type, row.group_key) for row in report.rows) == (
        ("category", "crypto_btc:finance.crypto.btc"),
    )


def test_empty_report_is_report_only_and_json_ready_without_floats() -> None:
    report = _report((), (), cfg=_config(min_resolved_observations=1))
    payload = forecast_confidence_backtest_readiness_payload(report)

    assert report.status == "blocked"
    assert report.reason_codes == (
        "no_forecasts",
        "no_resolved_observations",
    )
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["resolved_observation_count"] == "0.000000"
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_floats(payload)


def test_report_has_deterministic_derived_validation_digest_in_public_payload() -> None:
    first = _forecast_row("btc-1", confidence=d("0.900000"))
    second = _forecast_row("btc-2", confidence=d("0.700000"))

    report = _report(
        (first, second),
        (_outcome_row(first), _outcome_row(second)),
        cfg=_config(min_resolved_observations=2),
    )
    rebuilt = _report(
        (first, second),
        (_outcome_row(first), _outcome_row(second)),
        cfg=_config(min_resolved_observations=2),
    )
    payload = forecast_confidence_backtest_readiness_payload(report)

    assert len(report.derived_validation_digest) == 64
    assert report.derived_validation_digest == rebuilt.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["forecast_count"] == "2.000000"
    assert payload["ready_count"] == "1.000000"
    assert payload["rows"][0]["forecast_count"] == "2.000000"
    assert payload["rows"][0]["average_confidence"] == "0.800000"


def test_builder_validates_utc_datetime_inputs_flags_types_and_config() -> None:
    forecast = _forecast_row("btc-1")
    outcome = _outcome_row(forecast)

    report = _report(
        (forecast,),
        (outcome,),
        cfg=_config(min_resolved_observations=1),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC

    with pytest.raises(ValueError, match="forecast_rows"):
        _report((item for item in (forecast,)), (outcome,))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="outcome_rows"):
        _report((forecast,), (item for item in (outcome,)))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="TeamForecastDbRow"):
        _report((object(),), (outcome,))  # type: ignore[tuple-item]
    with pytest.raises(ValueError, match="TeamForecastOutcomeDbRow"):
        _report((forecast,), (team_forecast_outcome_from_db_row(outcome),))  # type: ignore[tuple-item]
    with pytest.raises(ValueError, match="paper_only"):
        _report((_bypassed_row(forecast, paper_only=False),), (outcome,))  # type: ignore[tuple-item]
    with pytest.raises(ValueError, match="readonly"):
        _report((forecast,), (_bypassed_row(outcome, readonly=False),))  # type: ignore[tuple-item]
    with pytest.raises(ValueError, match="config"):
        build_forecast_confidence_backtest_readiness_report(
            (forecast,),
            (outcome,),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report((forecast,), (outcome,), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            (forecast,),
            (outcome,),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="group_by"):
        _config(group_by="event_template")
    with pytest.raises(ValueError, match="min_resolved_observations"):
        _config(min_resolved_observations=_IntSubclass(3))
    with pytest.raises(ValueError, match="min_average_confidence"):
        _config(min_average_confidence=_DecimalSubclass("0.650000"))


def test_decimal_fields_reject_ints_in_report_and_rows() -> None:
    forecast = _forecast_row("btc-1")
    report = _report(
        (forecast,),
        (_outcome_row(forecast),),
        cfg=_config(min_resolved_observations=1, min_confidence_bucket_count=1),
    )

    with pytest.raises(ValueError, match="forecast_count"):
        replace(report, forecast_count=1)
    with pytest.raises(ValueError, match="ready_count"):
        replace(report, ready_count=1)
    with pytest.raises(ValueError, match="forecast_count"):
        replace(report.rows[0], forecast_count=1)


def test_dataclasses_enforce_consistency_and_are_frozen() -> None:
    forecast = _forecast_row("btc-1")
    second = _forecast_row(
        "eth-1",
        team_id="crypto_eth",
        category_id="finance.crypto.eth",
        confidence=d("0.700000"),
    )
    report = _report(
        (forecast, second),
        (_outcome_row(forecast), _outcome_row(second)),
        cfg=_config(min_resolved_observations=1, min_confidence_bucket_count=1),
    )

    with pytest.raises(FrozenInstanceError):
        report.ready_count = 99  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="ready_count"):
        replace(report, ready_count=2)
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)

    public = repr(asdict(report)).lower()
    for banned in (
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "investment_advice",
    ):
        assert banned not in public


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "live_trading_surface",
        "auth_token_surface",
        "wallet_surface",
        "order_surface",
        "network_surface",
        "database_surface",
        "persist_surface",
    ),
)
def test_payload_rejects_unsafe_live_surface_values(unsafe_value: str) -> None:
    forecast = _forecast_row("btc-1")
    report = _report(
        (forecast,),
        (_outcome_row(forecast),),
        cfg=_config(min_resolved_observations=1, min_confidence_bucket_count=1),
    )
    unsafe_report = _bypassed_row(report, reason_codes=(unsafe_value,))

    with pytest.raises(ValueError, match="unsafe"):
        forecast_confidence_backtest_readiness_payload(unsafe_report)  # type: ignore[arg-type]
