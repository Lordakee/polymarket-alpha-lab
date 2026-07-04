"""Pure local market-close calendar monitor.

This module summarizes supplied market close/end timestamps for research
scheduling. It is a pure reducer over caller-provided objects and emits
redacted calendar counts only.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.domain import MarketSnapshot


__all__ = (
    "MarketCloseCalendarMonitorConfig",
    "MarketCloseCalendarMonitorInput",
    "market_close_calendar_monitor_payload",
    "MarketCloseCalendarMonitorReport",
    "MarketCloseCalendarMonitorRow",
    "build_market_close_calendar_monitor_report",
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")

REPORT_STATUSES = ("empty", "pass", "watch", "blocked")
ROW_STATUSES = ("missing_close_time", "upcoming_close", "overdue_close", "closed")
PASS_REASON_CODE = "market_close_calendar_clear"


@dataclass(frozen=True)
class MarketCloseCalendarMonitorConfig:
    config_version: str
    upcoming_close_horizon_seconds: Decimal
    overdue_close_grace_seconds: Decimal
    stale_resolution_grace_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal(
            "upcoming_close_horizon_seconds",
            self.upcoming_close_horizon_seconds,
        )
        _require_nonnegative_decimal(
            "overdue_close_grace_seconds",
            self.overdue_close_grace_seconds,
        )
        _require_nonnegative_decimal(
            "stale_resolution_grace_seconds",
            self.stale_resolution_grace_seconds,
        )
        _validate_hard_flags(self)


@dataclass(frozen=True)
class MarketCloseCalendarMonitorInput:
    condition_id: str
    close_time: datetime | None
    closed: bool
    active: bool
    resolution_observed: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        object.__setattr__(
            self,
            "close_time",
            _as_optional_utc("close_time", self.close_time),
        )
        for field_name in ("closed", "active", "resolution_observed"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        if self.closed and self.active:
            raise ValueError("closed markets must not be active")
        if self.resolution_observed and not self.closed:
            raise ValueError("resolution_observed markets must be closed")
        _validate_hard_flags(self)


@dataclass(frozen=True)
class MarketCloseCalendarMonitorRow:
    condition_id: str
    close_time: datetime | None
    closed: bool
    active: bool
    resolution_observed: bool
    calendar_status: str
    seconds_until_close: Decimal | None
    seconds_overdue_close: Decimal | None
    stale_resolution_seconds: Decimal | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        object.__setattr__(
            self,
            "close_time",
            _as_optional_utc("close_time", self.close_time),
        )
        for field_name in ("closed", "active", "resolution_observed"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        _require_row_status("calendar_status", self.calendar_status)
        for field_name in (
            "seconds_until_close",
            "seconds_overdue_close",
            "stale_resolution_seconds",
        ):
            _require_optional_nonnegative_decimal(field_name, getattr(self, field_name))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _validate_hard_flags(self)


@dataclass(frozen=True)
class MarketCloseCalendarMonitorReport:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    markets_with_close_time_count: Decimal
    missing_close_time_count: Decimal
    upcoming_close_count: Decimal
    next_upcoming_close_at: datetime | None
    min_upcoming_close_seconds: Decimal
    max_upcoming_close_seconds: Decimal
    overdue_close_count: Decimal
    max_overdue_close_seconds: Decimal
    mean_overdue_close_seconds: Decimal
    stale_resolution_count: Decimal
    max_stale_resolution_seconds: Decimal
    mean_stale_resolution_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketCloseCalendarMonitorRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.generated_at) is not datetime:
            raise ValueError("generated_at must be a datetime")
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "markets_with_close_time_count",
            "missing_close_time_count",
            "upcoming_close_count",
            "overdue_close_count",
            "stale_resolution_count",
        ):
            _require_nonnegative_count_decimal(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "next_upcoming_close_at",
            _as_optional_utc("next_upcoming_close_at", self.next_upcoming_close_at),
        )
        for field_name in (
            "min_upcoming_close_seconds",
            "max_upcoming_close_seconds",
            "max_overdue_close_seconds",
            "mean_overdue_close_seconds",
            "max_stale_resolution_seconds",
            "mean_stale_resolution_seconds",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_report_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _validate_hard_flags(self)


def build_market_close_calendar_monitor_report(
    market_inputs: Iterable[MarketCloseCalendarMonitorInput | MarketSnapshot],
    *,
    config: MarketCloseCalendarMonitorConfig,
    generated_at: datetime,
) -> MarketCloseCalendarMonitorReport:
    """Summarize upcoming, overdue, and stale market close calendar signals."""

    if type(config) is not MarketCloseCalendarMonitorConfig:
        raise ValueError("config must be a MarketCloseCalendarMonitorConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    generated_at_utc = _as_utc(generated_at)
    inputs = _normalize_market_inputs(market_inputs)

    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    upcoming_distances = tuple(
        row.seconds_until_close
        for row in rows
        if row.calendar_status == "upcoming_close" and row.seconds_until_close is not None
    )
    overdue_ages = tuple(
        row.seconds_overdue_close
        for row in rows
        if row.seconds_overdue_close is not None
    )
    stale_ages = tuple(
        row.stale_resolution_seconds
        for row in rows
        if row.stale_resolution_seconds is not None
    )
    reason_codes = _report_reason_codes(rows)
    status = _report_status(reason_codes, market_count=len(rows))

    return MarketCloseCalendarMonitorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_count_decimal(len(rows)),
        markets_with_close_time_count=_count_decimal(
            sum(1 for row in rows if row.close_time is not None),
        ),
        missing_close_time_count=_count_decimal(
            sum(1 for row in rows if row.close_time is None),
        ),
        upcoming_close_count=_count_decimal(len(upcoming_distances)),
        next_upcoming_close_at=min(
            (row.close_time for row in rows if row.calendar_status == "upcoming_close"),
            default=None,
        ),
        min_upcoming_close_seconds=(
            min(upcoming_distances) if upcoming_distances else ZERO.quantize(RATIO_QUANTUM)
        ),
        max_upcoming_close_seconds=(
            max(upcoming_distances) if upcoming_distances else ZERO.quantize(RATIO_QUANTUM)
        ),
        overdue_close_count=_count_decimal(
            sum(1 for row in rows if row.calendar_status == "overdue_close"),
        ),
        max_overdue_close_seconds=(
            max(overdue_ages) if overdue_ages else ZERO.quantize(RATIO_QUANTUM)
        ),
        mean_overdue_close_seconds=_mean(overdue_ages),
        stale_resolution_count=_count_decimal(len(stale_ages)),
        max_stale_resolution_seconds=(
            max(stale_ages) if stale_ages else ZERO.quantize(RATIO_QUANTUM)
        ),
        mean_stale_resolution_seconds=_mean(stale_ages),
        status=status,
        reason_codes=reason_codes,
        rows=rows,
    )


def market_close_calendar_monitor_payload(
    report: MarketCloseCalendarMonitorReport,
) -> dict[str, object]:
    if type(report) is not MarketCloseCalendarMonitorReport:
        raise ValueError("report must be a MarketCloseCalendarMonitorReport")
    _validate_hard_flags(report)
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "market_count": _decimal_payload(report.market_count),
        "markets_with_close_time_count": _decimal_payload(
            report.markets_with_close_time_count,
        ),
        "missing_close_time_count": _decimal_payload(report.missing_close_time_count),
        "upcoming_close_count": _decimal_payload(report.upcoming_close_count),
        "next_upcoming_close_at": _optional_datetime_payload(
            report.next_upcoming_close_at,
        ),
        "min_upcoming_close_seconds": _decimal_payload(
            report.min_upcoming_close_seconds,
        ),
        "max_upcoming_close_seconds": _decimal_payload(
            report.max_upcoming_close_seconds,
        ),
        "overdue_close_count": _decimal_payload(report.overdue_close_count),
        "max_overdue_close_seconds": _decimal_payload(
            report.max_overdue_close_seconds,
        ),
        "mean_overdue_close_seconds": _decimal_payload(
            report.mean_overdue_close_seconds,
        ),
        "stale_resolution_count": _decimal_payload(report.stale_resolution_count),
        "max_stale_resolution_seconds": _decimal_payload(
            report.max_stale_resolution_seconds,
        ),
        "mean_stale_resolution_seconds": _decimal_payload(
            report.mean_stale_resolution_seconds,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _normalize_market_inputs(
    market_inputs: Iterable[MarketCloseCalendarMonitorInput | MarketSnapshot],
) -> tuple[MarketCloseCalendarMonitorInput, ...]:
    if isinstance(market_inputs, (str, bytes)):
        raise ValueError("market_inputs must be an iterable of market timestamp values")
    try:
        values = tuple(market_inputs)
    except TypeError as exc:
        raise ValueError(
            "market_inputs must be an iterable of market timestamp values",
        ) from exc

    normalized: list[MarketCloseCalendarMonitorInput] = []
    for value in values:
        if type(value) is MarketCloseCalendarMonitorInput:
            _validate_hard_flags(value)
            normalized.append(value)
        elif type(value) is MarketSnapshot:
            normalized.append(_input_from_market_snapshot(value))
        else:
            raise ValueError(
                "market_inputs must contain MarketCloseCalendarMonitorInput "
                "or MarketSnapshot values",
            )
    return tuple(normalized)


def _input_from_market_snapshot(market: MarketSnapshot) -> MarketCloseCalendarMonitorInput:
    return MarketCloseCalendarMonitorInput(
        condition_id=market.condition_id,
        close_time=market.end_time,
        closed=market.closed,
        active=market.active,
        resolution_observed=_resolution_observed(market.resolution_status),
    )


def _resolution_observed(resolution_status: str | None) -> bool:
    if resolution_status is None:
        return False
    return bool(str(resolution_status).strip())


def _row_from_input(
    item: MarketCloseCalendarMonitorInput,
    *,
    config: MarketCloseCalendarMonitorConfig,
    generated_at: datetime,
) -> MarketCloseCalendarMonitorRow:
    if item.close_time is None:
        return MarketCloseCalendarMonitorRow(
            condition_id=item.condition_id,
            close_time=None,
            closed=item.closed,
            active=item.active,
            resolution_observed=item.resolution_observed,
            calendar_status="missing_close_time",
            seconds_until_close=None,
            seconds_overdue_close=None,
            stale_resolution_seconds=None,
            reason_codes=("missing_close_timestamp",),
        )

    close_time = _as_utc(item.close_time)
    if close_time > generated_at:
        seconds_until = _seconds_between(generated_at, close_time)
        if seconds_until <= config.upcoming_close_horizon_seconds:
            return MarketCloseCalendarMonitorRow(
                condition_id=item.condition_id,
                close_time=close_time,
                closed=item.closed,
                active=item.active,
                resolution_observed=item.resolution_observed,
                calendar_status="upcoming_close",
                seconds_until_close=seconds_until,
                seconds_overdue_close=None,
                stale_resolution_seconds=None,
                reason_codes=("upcoming_close_watch",),
            )
        return MarketCloseCalendarMonitorRow(
            condition_id=item.condition_id,
            close_time=close_time,
            closed=item.closed,
            active=item.active,
            resolution_observed=item.resolution_observed,
            calendar_status="closed" if item.closed else "upcoming_close",
            seconds_until_close=None,
            seconds_overdue_close=None,
            stale_resolution_seconds=None,
            reason_codes=("future_close_outside_monitor_horizon",),
        )

    seconds_overdue = _seconds_between(close_time, generated_at)
    stale_seconds = (
        seconds_overdue
        if item.closed
        and not item.resolution_observed
        and seconds_overdue >= config.stale_resolution_grace_seconds
        else None
    )
    if not item.closed and seconds_overdue >= config.overdue_close_grace_seconds:
        return MarketCloseCalendarMonitorRow(
            condition_id=item.condition_id,
            close_time=close_time,
            closed=item.closed,
            active=item.active,
            resolution_observed=item.resolution_observed,
            calendar_status="overdue_close",
            seconds_until_close=None,
            seconds_overdue_close=seconds_overdue,
            stale_resolution_seconds=stale_seconds,
            reason_codes=("overdue_close_blocking",),
        )
    if stale_seconds is not None:
        return MarketCloseCalendarMonitorRow(
            condition_id=item.condition_id,
            close_time=close_time,
            closed=item.closed,
            active=item.active,
            resolution_observed=item.resolution_observed,
            calendar_status="overdue_close",
            seconds_until_close=None,
            seconds_overdue_close=seconds_overdue,
            stale_resolution_seconds=stale_seconds,
            reason_codes=("stale_resolution_calendar",),
        )
    return MarketCloseCalendarMonitorRow(
        condition_id=item.condition_id,
        close_time=close_time,
        closed=item.closed,
        active=item.active,
        resolution_observed=item.resolution_observed,
        calendar_status="closed" if item.closed else "upcoming_close",
        seconds_until_close=None,
        seconds_overdue_close=None,
        stale_resolution_seconds=None,
        reason_codes=("market_close_calendar_clear",),
    )


def _report_reason_codes(
    rows: tuple[MarketCloseCalendarMonitorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_market_close_calendar_inputs",)

    reasons: set[str] = set()
    if any(row.calendar_status == "missing_close_time" for row in rows):
        reasons.add("missing_close_timestamp")
    if any("upcoming_close_watch" in row.reason_codes for row in rows):
        reasons.add("upcoming_close_watch")
    if any("overdue_close_blocking" in row.reason_codes for row in rows):
        reasons.add("overdue_close_blocking")
    if any(row.stale_resolution_seconds is not None for row in rows):
        reasons.add("stale_resolution_calendar")
    if not reasons:
        reasons.add(PASS_REASON_CODE)
    return tuple(sorted(reasons))


def _report_status(reason_codes: tuple[str, ...], *, market_count: int) -> str:
    if market_count == 0:
        return "empty"
    if "overdue_close_blocking" in reason_codes:
        return "blocked"
    if reason_codes != (PASS_REASON_CODE,):
        return "watch"
    return "pass"


def _row_sort_key(row: MarketCloseCalendarMonitorRow) -> tuple[int, datetime, str]:
    severity = {
        "missing_close_time": 0,
        "overdue_close": 1,
        "upcoming_close": 2,
        "closed": 3,
    }[row.calendar_status]
    close_time = row.close_time or datetime(
        9999,
        12,
        31,
        23,
        59,
        59,
        999999,
        tzinfo=UTC,
    )
    return severity, close_time, row.condition_id


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = _as_utc(end) - _as_utc(start)
    microseconds = (
        (delta.days * 86_400 + delta.seconds) * 1_000_000 + delta.microseconds
    )
    return (Decimal(microseconds) / Decimal("1000000")).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return (sum(values, ZERO) / Decimal(len(values))).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _normalize_rows(
    rows: tuple[MarketCloseCalendarMonitorRow, ...],
) -> tuple[MarketCloseCalendarMonitorRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not MarketCloseCalendarMonitorRow:
            raise ValueError("rows must contain MarketCloseCalendarMonitorRow values")
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic calendar sort")
    return normalized


def _validate_row_consistency(row: MarketCloseCalendarMonitorRow) -> None:
    if row.closed and row.active:
        raise ValueError("closed rows must not be active")
    if row.resolution_observed and not row.closed:
        raise ValueError("resolution_observed rows must be closed")
    if row.calendar_status == "missing_close_time" and row.close_time is not None:
        raise ValueError("missing close rows must not have close_time")
    if row.seconds_until_close is not None and row.seconds_overdue_close is not None:
        raise ValueError("row cannot have both upcoming and overdue seconds")
    if row.stale_resolution_seconds is not None and row.resolution_observed:
        raise ValueError("stale rows must not have observed resolution")


def _validate_report_consistency(report: MarketCloseCalendarMonitorReport) -> None:
    if report.market_count != _count_decimal(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.markets_with_close_time_count != _count_decimal(
        sum(1 for row in report.rows if row.close_time is not None),
    ):
        raise ValueError("markets_with_close_time_count must match rows")
    if report.missing_close_time_count != _count_decimal(
        sum(1 for row in report.rows if row.close_time is None),
    ):
        raise ValueError("missing_close_time_count must match rows")
    if report.upcoming_close_count != _count_decimal(
        sum(
            1
            for row in report.rows
            if row.calendar_status == "upcoming_close"
            and "upcoming_close_watch" in row.reason_codes
        ),
    ):
        raise ValueError("upcoming_close_count must match rows")
    if report.overdue_close_count != _count_decimal(
        sum(1 for row in report.rows if row.calendar_status == "overdue_close"),
    ):
        raise ValueError("overdue_close_count must match rows")
    if report.stale_resolution_count != _count_decimal(
        sum(1 for row in report.rows if row.stale_resolution_seconds is not None),
    ):
        raise ValueError("stale_resolution_count must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match row calendar state")
    if report.status != _report_status(report.reason_codes, market_count=report.market_count):
        raise ValueError("status must match reason codes")
    if report.status == "pass" and report.reason_codes != (PASS_REASON_CODE,):
        raise ValueError("pass status must use the pass reason code")
    if report.status != "pass" and PASS_REASON_CODE in report.reason_codes:
        raise ValueError("non-pass status must not use the pass reason code")
    if report.status == "empty" and report.reason_codes != (
        "empty_market_close_calendar_inputs",
    ):
        raise ValueError("empty status must use the empty reason code")


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of canonical strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of canonical strings") from exc
    for reason_code in normalized:
        _require_canonical_string("reason_code", reason_code)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("reason_codes must be sorted")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return normalized


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("datetime value is required")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime value must be UTC-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime or None")
    return _as_utc(value)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_count_decimal(field_name: str, value: Any) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal count")


def _require_nonnegative_decimal(field_name: str, value: Any) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(field_name: str, value: Any) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)


def _require_report_status(field_name: str, value: Any) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be a known market close calendar status")


def _require_row_status(field_name: str, value: Any) -> None:
    if type(value) is not str or value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be a known market close calendar row status")


def _validate_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _row_payload(row: MarketCloseCalendarMonitorRow) -> dict[str, object]:
    _validate_hard_flags(row)
    return {
        "condition_id": row.condition_id,
        "close_time": _optional_datetime_payload(row.close_time),
        "closed": row.closed,
        "active": row.active,
        "resolution_observed": row.resolution_observed,
        "calendar_status": row.calendar_status,
        "seconds_until_close": _optional_decimal_payload(row.seconds_until_close),
        "seconds_overdue_close": _optional_decimal_payload(row.seconds_overdue_close),
        "stale_resolution_seconds": _optional_decimal_payload(
            row.stale_resolution_seconds,
        ),
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _datetime_payload(value: datetime) -> str:
    return _as_utc(value).isoformat()


def _optional_datetime_payload(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _datetime_payload(value)


def _decimal_payload(value: Decimal) -> str:
    _require_nonnegative_decimal("payload decimal", value)
    return str(value)


def _optional_decimal_payload(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_payload(value)
