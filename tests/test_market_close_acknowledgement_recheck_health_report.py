from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.market_close_acknowledgement_recheck_health_report import (
    MarketCloseAcknowledgementRecheckHealthConfig,
    MarketCloseAcknowledgementRecheckInputRow,
    build_market_close_acknowledgement_recheck_health_report,
    market_close_acknowledgement_recheck_health_report_to_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def _config() -> MarketCloseAcknowledgementRecheckHealthConfig:
    return MarketCloseAcknowledgementRecheckHealthConfig(
        close_lag_watch_seconds=Decimal("600"),
        close_lag_breach_seconds=Decimal("1800"),
        missing_ack_watch_count=Decimal("1"),
        missing_ack_breach_count=Decimal("2"),
        stale_recheck_watch_seconds=Decimal("900"),
        stale_recheck_breach_seconds=Decimal("3600"),
    )


def _row(
    market_slug: str,
    *,
    closed_seconds_ago: int,
    expected_ack_count: str = "1",
    acknowledged_count: str = "1",
    acknowledged_after_seconds: int | None = 30,
    rechecked_seconds_ago: int | None = 30,
) -> MarketCloseAcknowledgementRecheckInputRow:
    closed_at = GENERATED_AT - timedelta(seconds=closed_seconds_ago)
    return MarketCloseAcknowledgementRecheckInputRow(
        market_slug=market_slug,
        closed_at=closed_at,
        acknowledged_at=(
            None
            if acknowledged_after_seconds is None
            else closed_at + timedelta(seconds=acknowledged_after_seconds)
        ),
        last_rechecked_at=(
            None
            if rechecked_seconds_ago is None
            else GENERATED_AT - timedelta(seconds=rechecked_seconds_ago)
        ),
        expected_ack_count=Decimal(expected_ack_count),
        acknowledged_count=Decimal(acknowledged_count),
    )


def test_empty_input_builds_safe_empty_health_report() -> None:
    report = build_market_close_acknowledgement_recheck_health_report(
        [],
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.generated_at == GENERATED_AT
    assert report.status == "empty"
    assert report.row_count == Decimal("0")
    assert report.total_expected_ack_count == Decimal("0")
    assert report.total_missing_ack_count == Decimal("0")
    assert report.missing_ack_ratio is None
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_rows_are_sorted_deterministically_by_health_pressure_then_slug() -> None:
    report = build_market_close_acknowledgement_recheck_health_report(
        [
            _row("z-healthy", closed_seconds_ago=60),
            _row(
                "b-watch",
                closed_seconds_ago=600,
                acknowledged_after_seconds=None,
                acknowledged_count="0",
                rechecked_seconds_ago=900,
            ),
            _row(
                "c-breach",
                closed_seconds_ago=3600,
                expected_ack_count="2",
                acknowledged_after_seconds=None,
                acknowledged_count="0",
                rechecked_seconds_ago=3600,
            ),
            _row(
                "a-breach",
                closed_seconds_ago=3600,
                expected_ack_count="2",
                acknowledged_after_seconds=None,
                acknowledged_count="0",
                rechecked_seconds_ago=3600,
            ),
        ],
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert tuple(row.market_slug for row in report.rows) == (
        "a-breach",
        "c-breach",
        "b-watch",
        "z-healthy",
    )


def test_thresholds_drive_row_statuses_and_reason_codes() -> None:
    report = build_market_close_acknowledgement_recheck_health_report(
        [
            _row("healthy", closed_seconds_ago=120),
            _row(
                "watch",
                closed_seconds_ago=600,
                acknowledged_after_seconds=None,
                acknowledged_count="0",
                rechecked_seconds_ago=900,
            ),
            _row(
                "breach",
                closed_seconds_ago=1800,
                expected_ack_count="2",
                acknowledged_after_seconds=None,
                acknowledged_count="0",
                rechecked_seconds_ago=3600,
            ),
        ],
        config=_config(),
        generated_at=GENERATED_AT,
    )

    rows = {row.market_slug: row for row in report.rows}
    assert report.status == "breach"
    assert report.reason_codes == (
        "close_time_lag_breach",
        "missing_ack_pressure_breach",
        "stale_recheck_age_breach",
        "close_time_lag_watch",
        "missing_ack_pressure_watch",
        "stale_recheck_age_watch",
    )
    assert rows["healthy"].health_status == "healthy"
    assert rows["healthy"].reason_codes == ()
    assert rows["watch"].health_status == "watch"
    assert rows["watch"].close_time_lag_status == "watch"
    assert rows["watch"].missing_ack_status == "watch"
    assert rows["watch"].stale_recheck_status == "watch"
    assert rows["watch"].reason_codes == (
        "close_time_lag_watch",
        "missing_ack_pressure_watch",
        "stale_recheck_age_watch",
    )
    assert rows["breach"].health_status == "breach"
    assert rows["breach"].close_time_lag_status == "breach"
    assert rows["breach"].missing_ack_status == "breach"
    assert rows["breach"].stale_recheck_status == "breach"
    assert rows["breach"].reason_codes == (
        "close_time_lag_breach",
        "missing_ack_pressure_breach",
        "stale_recheck_age_breach",
    )


def test_naive_datetimes_are_rejected() -> None:
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_market_close_acknowledgement_recheck_health_report(
            [],
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )

    with pytest.raises(ValueError, match="closed_at must be timezone-aware"):
        MarketCloseAcknowledgementRecheckInputRow(
            market_slug="naive-close",
            closed_at=datetime(2026, 7, 2, 12, 0),
            acknowledged_at=None,
            last_rechecked_at=None,
            expected_ack_count=Decimal("1"),
            acknowledged_count=Decimal("0"),
        )


def test_secret_like_market_slug_is_rejected_before_payload_surface() -> None:
    with pytest.raises(ValueError, match="market_slug must not contain secret-like"):
        _row("api_key=abc123", closed_seconds_ago=60)


def test_public_dataclasses_are_frozen() -> None:
    row = _row("frozen", closed_seconds_ago=60)
    report = build_market_close_acknowledgement_recheck_health_report(
        [row],
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        row.market_slug = "mutated"
    with pytest.raises(FrozenInstanceError):
        report.status = "mutated"


def test_json_payload_uses_decimal_strings_and_iso_datetimes() -> None:
    report = build_market_close_acknowledgement_recheck_health_report(
        [
            _row(
                "json-safe",
                closed_seconds_ago=600,
                acknowledged_after_seconds=None,
                acknowledged_count="0",
                rechecked_seconds_ago=900,
            ),
        ],
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = market_close_acknowledgement_recheck_health_report_to_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["row_count"] == "1"
    assert payload["total_expected_ack_count"] == "1"
    assert payload["total_missing_ack_count"] == "1"
    assert payload["missing_ack_ratio"] == "1"
    assert payload["rows"][0]["closed_at"] == "2026-07-02T11:50:00+00:00"
    assert payload["rows"][0]["close_time_lag_seconds"] == "600"
    assert payload["rows"][0]["recheck_age_seconds"] == "900"
    assert not _contains_float_decimal_or_datetime(payload)
    json.dumps(payload, allow_nan=False)


def _contains_float_decimal_or_datetime(value: object) -> bool:
    if isinstance(value, (float, Decimal, datetime)):
        return True
    if isinstance(value, dict):
        return any(_contains_float_decimal_or_datetime(item) for item in value.values())
    if isinstance(value, list | tuple):
        return any(_contains_float_decimal_or_datetime(item) for item in value)
    return False
