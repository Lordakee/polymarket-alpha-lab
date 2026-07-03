from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.market_close_acknowledgement_recheck_sla_report import (
    CATEGORY_REPEATED_MISS_REASON,
    CONTRADICTORY_SOURCE_REASON,
    MISSING_OWNER_REASON,
    OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON,
    STALE_SOURCE_REASON,
    TEAM_REPEATED_MISS_REASON,
    MarketCloseAcknowledgementRecheckSlaConfig,
    MarketCloseAcknowledgementRecheckSlaInputRow,
    build_market_close_acknowledgement_recheck_sla_report,
    market_close_acknowledgement_recheck_sla_report_to_payload,
)


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _row(
    market_id: str,
    *,
    category_id: str = "politics",
    owner_team_id: str | None = "team-alpha",
    market_closed_at: datetime = datetime(2026, 1, 1, 11, 30, tzinfo=UTC),
    close_acknowledged_at: datetime | None = datetime(2026, 1, 1, 11, 45, tzinfo=UTC),
    source_observed_at: datetime = datetime(2026, 1, 1, 11, 55, tzinfo=UTC),
    source_contradicts_close: bool = False,
) -> MarketCloseAcknowledgementRecheckSlaInputRow:
    return MarketCloseAcknowledgementRecheckSlaInputRow(
        market_id=market_id,
        category_id=category_id,
        owner_team_id=owner_team_id,
        source_id=f"{market_id}-source",
        market_closed_at=market_closed_at,
        close_acknowledged_at=close_acknowledged_at,
        source_observed_at=source_observed_at,
        source_contradicts_close=source_contradicts_close,
    )


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False


def test_report_flags_sla_exceptions_repeated_misses_and_json_payload() -> None:
    config = MarketCloseAcknowledgementRecheckSlaConfig(
        acknowledgement_sla_seconds=Decimal("3600.000000"),
        source_stale_seconds=Decimal("900.000000"),
        team_repeated_miss_threshold=Decimal("2.000000"),
        category_repeated_miss_threshold=Decimal("2.000000"),
    )

    report = build_market_close_acknowledgement_recheck_sla_report(
        (
            _row(
                "market-e-clear",
                category_id="economics",
                owner_team_id="team-gamma",
                market_closed_at=datetime(2026, 1, 1, 11, 50, tzinfo=UTC),
                close_acknowledged_at=datetime(2026, 1, 1, 11, 55, tzinfo=UTC),
                source_observed_at=datetime(2026, 1, 1, 11, 58, tzinfo=UTC),
            ),
            _row(
                "market-a-overdue",
                market_closed_at=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
                close_acknowledged_at=None,
                source_observed_at=datetime(2026, 1, 1, 11, 50, tzinfo=UTC),
            ),
            _row(
                "market-d-stale",
                category_id="sports",
                owner_team_id="team-beta",
                market_closed_at=datetime(2026, 1, 1, 11, 55, tzinfo=UTC),
                close_acknowledged_at=datetime(2026, 1, 1, 11, 56, tzinfo=UTC),
                source_observed_at=datetime(2026, 1, 1, 11, 0, tzinfo=UTC),
            ),
            _row(
                "market-c-contradictory",
                source_contradicts_close=True,
            ),
            _row(
                "market-b-missing-owner",
                owner_team_id=None,
                market_closed_at=datetime(2026, 1, 1, 11, 30, tzinfo=UTC),
                close_acknowledged_at=datetime(2026, 1, 1, 11, 40, tzinfo=UTC),
            ),
        ),
        config=config,
        generated_at=NOW,
    )

    assert report.report_status == "breached"
    assert report.reason_codes == (
        OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON,
        MISSING_OWNER_REASON,
        STALE_SOURCE_REASON,
        CONTRADICTORY_SOURCE_REASON,
        TEAM_REPEATED_MISS_REASON,
        CATEGORY_REPEATED_MISS_REASON,
    )
    assert report.market_count == Decimal("5.000000")
    assert report.clear_market_count == Decimal("1.000000")
    assert report.watch_market_count == Decimal("1.000000")
    assert report.breached_market_count == Decimal("3.000000")
    assert report.exception_market_count == Decimal("4.000000")
    assert report.overdue_close_acknowledgement_count == Decimal("1.000000")
    assert report.missing_owner_count == Decimal("1.000000")
    assert report.stale_source_count == Decimal("1.000000")
    assert report.contradictory_source_count == Decimal("1.000000")
    assert report.team_repeated_miss_count == Decimal("1.000000")
    assert report.category_repeated_miss_count == Decimal("1.000000")
    assert report.exception_ratio == Decimal("0.800000")
    assert report.max_close_age_seconds == Decimal("7200.000000")
    assert report.max_source_age_seconds == Decimal("3600.000000")
    assert report.max_acknowledgement_lag_seconds == Decimal("900.000000")
    assert tuple(row.market_id for row in report.rows) == (
        "market-a-overdue",
        "market-b-missing-owner",
        "market-c-contradictory",
        "market-d-stale",
        "market-e-clear",
    )
    assert report.rows[0].reason_codes == (OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON,)
    assert report.rows[3].sla_status == "watch"
    assert report.team_repeated_miss_rows[0].miss_id == "team-alpha"
    assert report.team_repeated_miss_rows[0].miss_count == Decimal("2.000000")
    assert report.category_repeated_miss_rows[0].miss_id == "politics"
    assert report.category_repeated_miss_rows[0].miss_count == Decimal("3.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = market_close_acknowledgement_recheck_sla_report_to_payload(report)
    assert payload["market_count"] == "5.000000"
    assert payload["rows"][0]["close_age_seconds"] == "7200.000000"
    assert payload["team_repeated_miss_rows"][0]["miss_count"] == "2.000000"
    assert _contains_float(payload) is False


def test_clear_report_uses_decimal_zeroes_and_hard_flags() -> None:
    report = build_market_close_acknowledgement_recheck_sla_report(
        (
            _row(
                "market-clear",
                category_id="economics",
                owner_team_id="team-gamma",
                market_closed_at=datetime(2026, 1, 1, 11, 50, tzinfo=UTC),
                close_acknowledged_at=datetime(2026, 1, 1, 11, 55, tzinfo=UTC),
                source_observed_at=datetime(2026, 1, 1, 11, 58, tzinfo=UTC),
            ),
        ),
        config=MarketCloseAcknowledgementRecheckSlaConfig(),
        generated_at=NOW,
    )

    assert report.report_status == "clear"
    assert report.reason_codes == ("market_close_acknowledgement_recheck_sla_clear",)
    assert report.exception_market_count == Decimal("0.000000")
    assert report.exception_ratio == Decimal("0.000000")
    assert report.team_repeated_miss_rows == ()
    assert report.category_repeated_miss_rows == ()
    assert report.rows[0].sla_status == "clear"
    assert report.rows[0].close_age_seconds == Decimal("600.000000")

    with pytest.raises(FrozenInstanceError):
        report.rows[0].sla_status = "watch"  # type: ignore[misc]


def test_watch_report_status_for_stale_source_only() -> None:
    report = build_market_close_acknowledgement_recheck_sla_report(
        (
            _row(
                "market-stale-source",
                category_id="economics",
                owner_team_id="team-gamma",
                market_closed_at=datetime(2026, 1, 1, 11, 50, tzinfo=UTC),
                close_acknowledged_at=datetime(2026, 1, 1, 11, 55, tzinfo=UTC),
                source_observed_at=datetime(2026, 1, 1, 11, 0, tzinfo=UTC),
            ),
        ),
        config=MarketCloseAcknowledgementRecheckSlaConfig(
            source_stale_seconds=Decimal("900.000000"),
        ),
        generated_at=NOW,
    )

    assert report.report_status == "watch"
    assert report.reason_codes == (STALE_SOURCE_REASON,)
    assert report.watch_market_count == Decimal("1.000000")
    assert report.breached_market_count == Decimal("0.000000")


def test_empty_report_status_and_zero_metrics() -> None:
    report = build_market_close_acknowledgement_recheck_sla_report(
        (),
        config=MarketCloseAcknowledgementRecheckSlaConfig(),
        generated_at=NOW,
    )

    assert report.report_status == "empty"
    assert report.reason_codes == ("market_close_acknowledgement_recheck_sla_empty",)
    assert report.market_count == Decimal("0.000000")
    assert report.exception_market_count == Decimal("0.000000")
    assert report.exception_ratio == Decimal("0.000000")
    assert report.max_close_age_seconds == Decimal("0.000000")
    assert report.rows == ()
    assert report.team_repeated_miss_rows == ()
    assert report.category_repeated_miss_rows == ()


def test_repeated_miss_market_count_includes_clear_scope_markets() -> None:
    report = build_market_close_acknowledgement_recheck_sla_report(
        (
            _row(
                "market-alpha-overdue",
                owner_team_id="team-alpha",
                category_id="politics",
                market_closed_at=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
                close_acknowledged_at=None,
                source_observed_at=datetime(2026, 1, 1, 11, 55, tzinfo=UTC),
            ),
            _row(
                "market-alpha-contradictory",
                owner_team_id="team-alpha",
                category_id="politics",
                source_contradicts_close=True,
            ),
            _row(
                "market-alpha-clear",
                owner_team_id="team-alpha",
                category_id="politics",
                market_closed_at=datetime(2026, 1, 1, 11, 50, tzinfo=UTC),
                close_acknowledged_at=datetime(2026, 1, 1, 11, 55, tzinfo=UTC),
                source_observed_at=datetime(2026, 1, 1, 11, 58, tzinfo=UTC),
            ),
        ),
        config=MarketCloseAcknowledgementRecheckSlaConfig(
            team_repeated_miss_threshold=Decimal("2.000000"),
            category_repeated_miss_threshold=Decimal("2.000000"),
        ),
        generated_at=NOW,
    )

    team_row = report.team_repeated_miss_rows[0]
    assert team_row.miss_id == "team-alpha"
    assert team_row.market_count == Decimal("3.000000")
    assert team_row.miss_count == Decimal("2.000000")
    assert team_row.repeated_miss is True

    category_row = report.category_repeated_miss_rows[0]
    assert category_row.miss_id == "politics"
    assert category_row.market_count == Decimal("3.000000")
    assert category_row.miss_count == Decimal("2.000000")
    assert category_row.repeated_miss is True


def test_validation_rejects_naive_times_non_decimal_seconds_and_false_flags() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _row(
            "market-naive",
            market_closed_at=datetime(2026, 1, 1, 11, 50),
        )

    with pytest.raises(ValueError, match="Decimal"):
        MarketCloseAcknowledgementRecheckSlaConfig(
            acknowledgement_sla_seconds=3600,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="paper_only"):
        MarketCloseAcknowledgementRecheckSlaConfig(paper_only=False)

    with pytest.raises(ValueError, match="Decimal"):
        report = build_market_close_acknowledgement_recheck_sla_report(
            (_row("market-decimal"),),
            config=MarketCloseAcknowledgementRecheckSlaConfig(),
            generated_at=NOW,
        )
        type(report.rows[0])(
            **{
                **report.rows[0].__dict__,
                "close_age_seconds": 1,
            },
        )


def test_builder_rejects_duplicate_market_ids_and_future_recheck_times() -> None:
    with pytest.raises(ValueError, match="unique"):
        build_market_close_acknowledgement_recheck_sla_report(
            (_row("market-duplicate"), _row("market-duplicate")),
            config=MarketCloseAcknowledgementRecheckSlaConfig(),
            generated_at=NOW,
        )

    with pytest.raises(ValueError, match="future"):
        build_market_close_acknowledgement_recheck_sla_report(
            (
                _row(
                    "market-future-source",
                    source_observed_at=datetime(2026, 1, 1, 12, 1, tzinfo=UTC),
                ),
            ),
            config=MarketCloseAcknowledgementRecheckSlaConfig(),
            generated_at=NOW,
        )
