from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.domain import MarketSnapshot
from polymarket_alpha_lab.market_close_calendar_monitor import (
    MarketCloseCalendarMonitorConfig,
    MarketCloseCalendarMonitorInput,
    MarketCloseCalendarMonitorReport,
    build_market_close_calendar_monitor_report,
    market_close_calendar_monitor_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _config(**overrides) -> MarketCloseCalendarMonitorConfig:
    values = {
        "config_version": "market-close-calendar-monitor-v0",
        "upcoming_close_horizon_seconds": Decimal("7200"),
        "overdue_close_grace_seconds": Decimal("900"),
        "stale_resolution_grace_seconds": Decimal("3600"),
    }
    values.update(overrides)
    return MarketCloseCalendarMonitorConfig(**values)


def _market(
    condition_id: str,
    *,
    end_time: datetime | None,
    active: bool = True,
    closed: bool = False,
    resolution_status: str | None = None,
) -> MarketSnapshot:
    return MarketSnapshot(
        condition_id=condition_id,
        market_slug=f"secret-slug-{condition_id}",
        question=f"Will secret market {condition_id} resolve?",
        active=active,
        closed=closed,
        accepting_orders=active and not closed,
        end_time=end_time,
        volume_24h=Decimal("10"),
        liquidity=Decimal("20"),
        captured_at=GENERATED_AT - timedelta(minutes=5),
        resolution_status=resolution_status,
    )


def _input(condition_id: str, **overrides) -> MarketCloseCalendarMonitorInput:
    values = {
        "condition_id": condition_id,
        "close_time": GENERATED_AT + timedelta(hours=1),
        "closed": False,
        "active": True,
        "resolution_observed": False,
    }
    values.update(overrides)
    return MarketCloseCalendarMonitorInput(**values)


def _assert_payload_has_no_public_numbers(value: Any) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            _assert_payload_has_no_public_numbers(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_payload_has_no_public_numbers(nested)
    else:
        assert type(value) not in (Decimal, float, int)


def test_calendar_monitor_summarizes_upcoming_overdue_and_stale_without_market_text():
    upcoming = _market("0xupcoming", end_time=GENERATED_AT + timedelta(hours=1))
    overdue = _market("0xoverdue", end_time=GENERATED_AT - timedelta(minutes=30))
    stale = _market(
        "0xstale",
        end_time=GENERATED_AT - timedelta(hours=3),
        active=False,
        closed=True,
    )
    future = _market("0xfuture", end_time=GENERATED_AT + timedelta(days=2))

    report = build_market_close_calendar_monitor_report(
        (upcoming, overdue, stale, future),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, MarketCloseCalendarMonitorReport)
    assert report.market_count == Decimal("4")
    assert report.markets_with_close_time_count == Decimal("4")
    assert report.upcoming_close_count == Decimal("1")
    assert report.next_upcoming_close_at == GENERATED_AT + timedelta(hours=1)
    assert report.min_upcoming_close_seconds == Decimal("3600.000000")
    assert report.max_upcoming_close_seconds == Decimal("3600.000000")
    assert report.overdue_close_count == Decimal("2")
    assert report.max_overdue_close_seconds == Decimal("10800.000000")
    assert report.mean_overdue_close_seconds == Decimal("6300.000000")
    assert report.stale_resolution_count == Decimal("1")
    assert report.max_stale_resolution_seconds == Decimal("10800.000000")
    assert report.mean_stale_resolution_seconds == Decimal("10800.000000")
    assert report.status == "blocked"
    assert report.reason_codes == (
        "overdue_close_blocking",
        "stale_resolution_calendar",
        "upcoming_close_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    field_names = {field.name for field in fields(report)}
    row_field_names = {field.name for field in fields(report.rows[0])}
    assert "market_slug" not in field_names
    assert "question" not in field_names
    assert "payload" not in field_names
    assert "market_slug" not in row_field_names
    assert "question" not in row_field_names
    assert "payload" not in row_field_names
    assert "secret-slug" not in repr(report)
    assert "secret market" not in repr(report)


def test_calendar_monitor_accepts_explicit_readonly_timestamp_inputs():
    report = build_market_close_calendar_monitor_report(
        (
            _input(
                "0xactive",
                close_time=GENERATED_AT + timedelta(minutes=30),
            ),
            _input(
                "0xresolved",
                close_time=GENERATED_AT - timedelta(hours=2),
                closed=True,
                active=False,
                resolution_observed=True,
            ),
            _input(
                "0xmissing",
                close_time=None,
                closed=False,
                active=True,
                resolution_observed=False,
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.market_count == Decimal("3")
    assert report.markets_with_close_time_count == Decimal("2")
    assert report.missing_close_time_count == Decimal("1")
    assert report.upcoming_close_count == Decimal("1")
    assert report.overdue_close_count == Decimal("0")
    assert report.stale_resolution_count == Decimal("0")
    assert report.status == "watch"
    assert report.reason_codes == (
        "missing_close_timestamp",
        "upcoming_close_watch",
    )
    assert tuple(row.condition_id for row in report.rows) == (
        "0xmissing",
        "0xactive",
        "0xresolved",
    )


def test_calendar_monitor_empty_inputs_are_empty_status():
    report = build_market_close_calendar_monitor_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.market_count == Decimal("0")
    assert report.status == "empty"
    assert report.reason_codes == ("empty_market_close_calendar_inputs",)
    assert report.rows == ()


def test_calendar_monitor_payload_serializes_decimal_counts_and_datetimes_as_strings():
    report = build_market_close_calendar_monitor_report(
        (
            _input("0xactive", close_time=GENERATED_AT + timedelta(minutes=30)),
            _input("0xmissing", close_time=None),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = market_close_calendar_monitor_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "2"
    assert payload["markets_with_close_time_count"] == "1"
    assert payload["missing_close_time_count"] == "1"
    assert payload["upcoming_close_count"] == "1"
    assert payload["min_upcoming_close_seconds"] == "1800.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    rows = payload["rows"]
    assert isinstance(rows, list)
    assert rows[0]["close_time"] is None
    assert rows[1]["seconds_until_close"] == "1800.000000"
    _assert_payload_has_no_public_numbers(payload)
    assert "secret" not in repr(payload)


def test_calendar_monitor_report_rejects_public_int_float_and_decimal_subclass_counts():
    kwargs = {
        "generated_at": GENERATED_AT,
        "config_version": "market-close-calendar-monitor-v0",
        "market_count": Decimal("1"),
        "markets_with_close_time_count": Decimal("1"),
        "missing_close_time_count": Decimal("0"),
        "upcoming_close_count": Decimal("1"),
        "next_upcoming_close_at": GENERATED_AT + timedelta(hours=1),
        "min_upcoming_close_seconds": Decimal("3600.000000"),
        "max_upcoming_close_seconds": Decimal("3600.000000"),
        "overdue_close_count": Decimal("0"),
        "max_overdue_close_seconds": Decimal("0.000000"),
        "mean_overdue_close_seconds": Decimal("0.000000"),
        "stale_resolution_count": Decimal("0"),
        "max_stale_resolution_seconds": Decimal("0.000000"),
        "mean_stale_resolution_seconds": Decimal("0.000000"),
        "status": "watch",
        "reason_codes": ("upcoming_close_watch",),
        "rows": (
            build_market_close_calendar_monitor_report(
                (_input("0xactive"),),
                config=_config(),
                generated_at=GENERATED_AT,
            ).rows[0],
        ),
    }

    with pytest.raises(ValueError, match="market_count"):
        MarketCloseCalendarMonitorReport(**{**kwargs, "market_count": 1})
    with pytest.raises(ValueError, match="market_count"):
        MarketCloseCalendarMonitorReport(**{**kwargs, "market_count": 1.0})
    with pytest.raises(ValueError, match="market_count"):
        MarketCloseCalendarMonitorReport(
            **{**kwargs, "market_count": _DecimalSubclass("1")},
        )
    with pytest.raises(ValueError, match="market_count"):
        MarketCloseCalendarMonitorReport(
            **{**kwargs, "market_count": Decimal("1.5")},
        )


def test_calendar_monitor_rejects_fast_mode_and_keeps_dataclasses_frozen():
    report = build_market_close_calendar_monitor_report(
        (_input("0xfrozen"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.market_count = 2
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="upcoming_close_horizon_seconds"):
        _config(upcoming_close_horizon_seconds=7200)
    with pytest.raises(ValueError, match="overdue_close_grace_seconds"):
        _config(overdue_close_grace_seconds=_DecimalSubclass("900"))
    with pytest.raises(TypeError, match="fast"):
        MarketCloseCalendarMonitorConfig(
            config_version="market-close-calendar-monitor-v0",
            upcoming_close_horizon_seconds=Decimal("7200"),
            overdue_close_grace_seconds=Decimal("900"),
            stale_resolution_grace_seconds=Decimal("3600"),
            fast=True,
        )


def test_calendar_monitor_rejects_invalid_inputs_and_datetime_values():
    with pytest.raises(ValueError, match="market_inputs"):
        build_market_close_calendar_monitor_report(
            "not markets",
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="market_inputs"):
        build_market_close_calendar_monitor_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="condition_id"):
        MarketCloseCalendarMonitorInput(
            condition_id=" 0xbad ",
            close_time=GENERATED_AT,
            closed=False,
            active=True,
            resolution_observed=False,
        )
    with pytest.raises(ValueError, match="closed markets must not be active"):
        MarketCloseCalendarMonitorInput(
            condition_id="0xbad",
            close_time=GENERATED_AT,
            closed=True,
            active=True,
            resolution_observed=False,
        )
    with pytest.raises(ValueError, match="UTC-aware"):
        MarketCloseCalendarMonitorInput(
            condition_id="0xnaive",
            close_time=datetime(2026, 7, 2, 12, 0),
            closed=False,
            active=True,
            resolution_observed=False,
        )
    with pytest.raises(ValueError, match="UTC-aware"):
        MarketCloseCalendarMonitorInput(
            condition_id="0xnoneoffset",
            close_time=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
            closed=False,
            active=True,
            resolution_observed=False,
        )
    with pytest.raises(ValueError, match="datetime"):
        MarketCloseCalendarMonitorInput(
            condition_id="0xsubclass",
            close_time=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
            closed=False,
            active=True,
            resolution_observed=False,
        )
    with pytest.raises(ValueError, match="UTC-aware"):
        build_market_close_calendar_monitor_report(
            (_input("0xactive"),),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
