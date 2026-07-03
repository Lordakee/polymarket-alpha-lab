"""Pure in-memory priority report for market close acknowledgement rechecks."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_PRIORITY_CONFIG_VERSION = (
    "market-close-acknowledgement-recheck-priority-v0"
)

ROW_STATUSES = ("critical", "watch", "clear")
REPORT_STATUSES = ("empty", "critical", "watch", "clear")
ROW_REASON_CODES = (
    "market_close_ack_priority_close_time_lag_critical",
    "market_close_ack_priority_close_time_lag_watch",
    "market_close_ack_priority_missing_ack_pressure_critical",
    "market_close_ack_priority_missing_ack_pressure_watch",
    "market_close_ack_priority_stale_recheck_age_critical",
    "market_close_ack_priority_stale_recheck_age_watch",
    "market_close_ack_priority_recheck_missing",
    "market_close_ack_priority_clear",
)
REPORT_REASON_CODES = ("market_close_ack_priority_empty", *ROW_REASON_CODES)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
UTC_OFFSET = timedelta(0)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckPriorityConfig:
    config_version: str = (
        DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_PRIORITY_CONFIG_VERSION
    )
    close_time_lag_watch_seconds: Decimal = Decimal("900.000000")
    close_time_lag_critical_seconds: Decimal = Decimal("3600.000000")
    missing_ack_watch_ratio: Decimal = Decimal("0.250000")
    missing_ack_critical_ratio: Decimal = Decimal("0.500000")
    stale_recheck_watch_seconds: Decimal = Decimal("1800.000000")
    stale_recheck_critical_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "close_time_lag_watch_seconds",
            "close_time_lag_critical_seconds",
            "stale_recheck_watch_seconds",
            "stale_recheck_critical_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in ("missing_ack_watch_ratio", "missing_ack_critical_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("market close acknowledgement recheck priority config", self)
        reject_unsafe_surface_fields("market close acknowledgement recheck priority config", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckPriorityInput:
    market_slug: str
    closed_at: datetime
    acknowledged_at: datetime | None
    last_rechecked_at: datetime | None
    expected_ack_count: Decimal
    acknowledged_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "market_slug",
            _require_public_string("market_slug", self.market_slug),
        )
        object.__setattr__(self, "closed_at", _as_utc("closed_at", self.closed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_optional_utc("last_rechecked_at", self.last_rechecked_at),
        )
        object.__setattr__(
            self,
            "expected_ack_count",
            _normalize_positive_count("expected_ack_count", self.expected_ack_count),
        )
        object.__setattr__(
            self,
            "acknowledged_count",
            _normalize_nonnegative_count("acknowledged_count", self.acknowledged_count),
        )
        _validate_input(self)
        require_paper_only_flags("market close acknowledgement recheck priority input", self)
        reject_unsafe_surface_fields("market close acknowledgement recheck priority input", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckPriorityRow:
    priority_rank: Decimal
    market_slug: str
    priority_status: str
    closed_at: datetime
    acknowledged_at: datetime | None
    last_rechecked_at: datetime | None
    expected_ack_count: Decimal
    acknowledged_count: Decimal
    missing_ack_count: Decimal
    missing_ack_pressure_ratio: Decimal
    close_time_lag_seconds: Decimal
    stale_recheck_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_count("priority_rank", self.priority_rank),
        )
        object.__setattr__(
            self,
            "market_slug",
            _require_public_string("market_slug", self.market_slug),
        )
        _require_member("priority_status", self.priority_status, ROW_STATUSES)
        object.__setattr__(self, "closed_at", _as_utc("closed_at", self.closed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_optional_utc("last_rechecked_at", self.last_rechecked_at),
        )
        object.__setattr__(
            self,
            "expected_ack_count",
            _normalize_positive_count("expected_ack_count", self.expected_ack_count),
        )
        for field_name in ("acknowledged_count", "missing_ack_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_ack_pressure_ratio",
            _normalize_ratio(
                "missing_ack_pressure_ratio",
                self.missing_ack_pressure_ratio,
            ),
        )
        for field_name in ("close_time_lag_seconds", "stale_recheck_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _validate_row(self)
        require_paper_only_flags("market close acknowledgement recheck priority row", self)
        reject_unsafe_surface_fields("market close acknowledgement recheck priority row", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckPriorityReport:
    generated_at: datetime
    config_version: str
    status: str
    market_count: Decimal
    critical_market_count: Decimal
    watch_market_count: Decimal
    clear_market_count: Decimal
    priority_market_count: Decimal
    close_time_lag_market_count: Decimal
    missing_ack_market_count: Decimal
    stale_recheck_market_count: Decimal
    max_close_time_lag_seconds: Decimal
    max_missing_ack_pressure_ratio: Decimal
    max_stale_recheck_age_seconds: Decimal
    rows: tuple[MarketCloseAcknowledgementRecheckPriorityRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_member("status", self.status, REPORT_STATUSES)
        for field_name in (
            "market_count",
            "critical_market_count",
            "watch_market_count",
            "clear_market_count",
            "priority_market_count",
            "close_time_lag_market_count",
            "missing_ack_market_count",
            "stale_recheck_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_close_time_lag_seconds", "max_stale_recheck_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_missing_ack_pressure_ratio",
            _normalize_ratio(
                "max_missing_ack_pressure_ratio",
                self.max_missing_ack_pressure_ratio,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        require_paper_only_flags("market close acknowledgement recheck priority report", self)
        reject_unsafe_surface_fields("market close acknowledgement recheck priority report", self)


def build_market_close_acknowledgement_recheck_priority_report(
    candidates: Iterable[MarketCloseAcknowledgementRecheckPriorityInput],
    *,
    config: MarketCloseAcknowledgementRecheckPriorityConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckPriorityReport:
    if type(config) is not MarketCloseAcknowledgementRecheckPriorityConfig:
        raise ValueError(
            "config must be a MarketCloseAcknowledgementRecheckPriorityConfig",
        )
    require_paper_only_flags("market close acknowledgement recheck priority config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(candidates)
    _validate_input_times(inputs, generated_at_utc)
    base_rows = tuple(
        _priority_row(row, config=config, generated_at=generated_at_utc)
        for row in inputs
    )
    rows = tuple(
        _with_priority_rank(row, index)
        for index, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    return MarketCloseAcknowledgementRecheckPriorityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        market_count=_count(len(rows)),
        critical_market_count=_status_count(rows, "critical"),
        watch_market_count=_status_count(rows, "watch"),
        clear_market_count=_status_count(rows, "clear"),
        priority_market_count=_count(
            sum(1 for row in rows if row.priority_status != "clear"),
        ),
        close_time_lag_market_count=_count(
            sum(1 for row in rows if _has_close_lag_reason(row)),
        ),
        missing_ack_market_count=_count(
            sum(1 for row in rows if row.missing_ack_count > ZERO_COUNT),
        ),
        stale_recheck_market_count=_count(
            sum(1 for row in rows if _has_stale_recheck_reason(row)),
        ),
        max_close_time_lag_seconds=_max_seconds(
            tuple(row.close_time_lag_seconds for row in rows),
        ),
        max_missing_ack_pressure_ratio=_max_ratio(
            tuple(row.missing_ack_pressure_ratio for row in rows),
        ),
        max_stale_recheck_age_seconds=_max_seconds(
            tuple(row.stale_recheck_age_seconds for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def market_close_acknowledgement_recheck_priority_report_to_payload(
    report: MarketCloseAcknowledgementRecheckPriorityReport,
) -> dict[str, Any]:
    if type(report) is not MarketCloseAcknowledgementRecheckPriorityReport:
        raise ValueError(
            "report must be a MarketCloseAcknowledgementRecheckPriorityReport",
        )
    require_paper_only_flags("market close acknowledgement recheck priority report", report)
    reject_unsafe_surface_fields("market close acknowledgement recheck priority report", report)
    ready = json_ready_no_floats(report)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("market close acknowledgement recheck priority payload", ready)
    return ready


def _priority_row(
    row: MarketCloseAcknowledgementRecheckPriorityInput,
    *,
    config: MarketCloseAcknowledgementRecheckPriorityConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckPriorityRow:
    close_time_lag_seconds = _close_time_lag_seconds(row, generated_at)
    stale_recheck_age_seconds = _duration_seconds(
        row.closed_at if row.last_rechecked_at is None else row.last_rechecked_at,
        generated_at,
    )
    missing_ack_count = row.expected_ack_count - row.acknowledged_count
    missing_ack_pressure_ratio = _ratio(missing_ack_count, row.expected_ack_count)
    reason_codes = _row_reason_codes(
        close_time_lag_seconds=close_time_lag_seconds,
        missing_ack_pressure_ratio=missing_ack_pressure_ratio,
        stale_recheck_age_seconds=stale_recheck_age_seconds,
        recheck_missing=row.last_rechecked_at is None,
        config=config,
    )
    return MarketCloseAcknowledgementRecheckPriorityRow(
        priority_rank=_count(1),
        market_slug=row.market_slug,
        priority_status=_priority_status(reason_codes),
        closed_at=row.closed_at,
        acknowledged_at=row.acknowledged_at,
        last_rechecked_at=row.last_rechecked_at,
        expected_ack_count=row.expected_ack_count,
        acknowledged_count=row.acknowledged_count,
        missing_ack_count=missing_ack_count,
        missing_ack_pressure_ratio=missing_ack_pressure_ratio,
        close_time_lag_seconds=close_time_lag_seconds,
        stale_recheck_age_seconds=stale_recheck_age_seconds,
        reason_codes=reason_codes,
    )


def _with_priority_rank(
    row: MarketCloseAcknowledgementRecheckPriorityRow,
    index: int,
) -> MarketCloseAcknowledgementRecheckPriorityRow:
    return MarketCloseAcknowledgementRecheckPriorityRow(
        priority_rank=_count(index),
        market_slug=row.market_slug,
        priority_status=row.priority_status,
        closed_at=row.closed_at,
        acknowledged_at=row.acknowledged_at,
        last_rechecked_at=row.last_rechecked_at,
        expected_ack_count=row.expected_ack_count,
        acknowledged_count=row.acknowledged_count,
        missing_ack_count=row.missing_ack_count,
        missing_ack_pressure_ratio=row.missing_ack_pressure_ratio,
        close_time_lag_seconds=row.close_time_lag_seconds,
        stale_recheck_age_seconds=row.stale_recheck_age_seconds,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    close_time_lag_seconds: Decimal,
    missing_ack_pressure_ratio: Decimal,
    stale_recheck_age_seconds: Decimal,
    recheck_missing: bool,
    config: MarketCloseAcknowledgementRecheckPriorityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if close_time_lag_seconds >= config.close_time_lag_critical_seconds:
        reason_codes.append("market_close_ack_priority_close_time_lag_critical")
    elif close_time_lag_seconds >= config.close_time_lag_watch_seconds:
        reason_codes.append("market_close_ack_priority_close_time_lag_watch")
    if missing_ack_pressure_ratio >= config.missing_ack_critical_ratio:
        reason_codes.append("market_close_ack_priority_missing_ack_pressure_critical")
    elif missing_ack_pressure_ratio >= config.missing_ack_watch_ratio:
        reason_codes.append("market_close_ack_priority_missing_ack_pressure_watch")
    if stale_recheck_age_seconds >= config.stale_recheck_critical_seconds:
        reason_codes.append("market_close_ack_priority_stale_recheck_age_critical")
    elif stale_recheck_age_seconds >= config.stale_recheck_watch_seconds:
        reason_codes.append("market_close_ack_priority_stale_recheck_age_watch")
    if recheck_missing:
        reason_codes.append("market_close_ack_priority_recheck_missing")
    if not reason_codes:
        reason_codes.append("market_close_ack_priority_clear")
    return tuple(reason_codes)


def _priority_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_critical") for reason_code in reason_codes):
        return "critical"
    if reason_codes == ("market_close_ack_priority_clear",):
        return "clear"
    return "watch"


def _report_status(
    rows: tuple[MarketCloseAcknowledgementRecheckPriorityRow, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.priority_status == "critical" for row in rows):
        return "critical"
    if any(row.priority_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketCloseAcknowledgementRecheckPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("market_close_ack_priority_empty",)
    reason_codes = tuple(
        reason_code
        for reason_code in ROW_REASON_CODES
        if reason_code != "market_close_ack_priority_clear"
        and any(reason_code in row.reason_codes for row in rows)
    )
    if reason_codes:
        return reason_codes
    return ("market_close_ack_priority_clear",)


def _normalize_inputs(
    value: Iterable[MarketCloseAcknowledgementRecheckPriorityInput],
) -> tuple[MarketCloseAcknowledgementRecheckPriorityInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckPriorityInput:
            raise ValueError(
                "candidates must contain MarketCloseAcknowledgementRecheckPriorityInput values",
            )
        require_paper_only_flags("market close acknowledgement recheck priority input", row)
        if row.market_slug in seen:
            raise ValueError("market_slug values must be unique")
        seen.add(row.market_slug)
    return rows


def _normalize_rows(
    value: Iterable[MarketCloseAcknowledgementRecheckPriorityRow],
) -> tuple[MarketCloseAcknowledgementRecheckPriorityRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckPriorityRow:
            raise ValueError("rows must contain priority row values")
        require_paper_only_flags("market close acknowledgement recheck priority row", row)
        if row.market_slug in seen:
            raise ValueError("rows market_slug values must be unique")
        seen.add(row.market_slug)
    return rows


def _validate_config(config: MarketCloseAcknowledgementRecheckPriorityConfig) -> None:
    if config.close_time_lag_critical_seconds < config.close_time_lag_watch_seconds:
        raise ValueError(
            "close_time_lag_critical_seconds must be >= close_time_lag_watch_seconds",
        )
    if config.missing_ack_watch_ratio <= ZERO_RATIO:
        raise ValueError("missing_ack_watch_ratio must be positive")
    if config.missing_ack_critical_ratio < config.missing_ack_watch_ratio:
        raise ValueError("missing_ack_critical_ratio must be >= missing_ack_watch_ratio")
    if config.stale_recheck_critical_seconds < config.stale_recheck_watch_seconds:
        raise ValueError(
            "stale_recheck_critical_seconds must be >= stale_recheck_watch_seconds",
        )


def _validate_input(row: MarketCloseAcknowledgementRecheckPriorityInput) -> None:
    if row.acknowledged_count > row.expected_ack_count:
        raise ValueError("acknowledged_count must not exceed expected_ack_count")
    if row.acknowledged_at is not None and row.acknowledged_at < row.closed_at:
        raise ValueError("acknowledged_at must be >= closed_at")


def _validate_row(row: MarketCloseAcknowledgementRecheckPriorityRow) -> None:
    if row.acknowledged_count > row.expected_ack_count:
        raise ValueError("acknowledged_count must not exceed expected_ack_count")
    if row.missing_ack_count != row.expected_ack_count - row.acknowledged_count:
        raise ValueError("missing_ack_count must match acknowledgement counts")
    if row.missing_ack_pressure_ratio != _ratio(
        row.missing_ack_count,
        row.expected_ack_count,
    ):
        raise ValueError("missing_ack_pressure_ratio must match acknowledgement counts")
    if row.acknowledged_at is not None and row.acknowledged_at < row.closed_at:
        raise ValueError("acknowledged_at must be >= closed_at")
    if row.priority_status != _priority_status(row.reason_codes):
        raise ValueError("priority_status must match reason_codes")


def _validate_report(report: MarketCloseAcknowledgementRecheckPriorityReport) -> None:
    if report.market_count != _count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.critical_market_count != _status_count(report.rows, "critical"):
        raise ValueError("critical_market_count must match rows")
    if report.watch_market_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_market_count must match rows")
    if report.clear_market_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_market_count must match rows")
    if report.priority_market_count != _count(
        sum(1 for row in report.rows if row.priority_status != "clear"),
    ):
        raise ValueError("priority_market_count must match rows")
    if report.close_time_lag_market_count != _count(
        sum(1 for row in report.rows if _has_close_lag_reason(row)),
    ):
        raise ValueError("close_time_lag_market_count must match rows")
    if report.missing_ack_market_count != _count(
        sum(1 for row in report.rows if row.missing_ack_count > ZERO_COUNT),
    ):
        raise ValueError("missing_ack_market_count must match rows")
    if report.stale_recheck_market_count != _count(
        sum(1 for row in report.rows if _has_stale_recheck_reason(row)),
    ):
        raise ValueError("stale_recheck_market_count must match rows")
    if report.max_close_time_lag_seconds != _max_seconds(
        tuple(row.close_time_lag_seconds for row in report.rows),
    ):
        raise ValueError("max_close_time_lag_seconds must match rows")
    if report.max_missing_ack_pressure_ratio != _max_ratio(
        tuple(row.missing_ack_pressure_ratio for row in report.rows),
    ):
        raise ValueError("max_missing_ack_pressure_ratio must match rows")
    if report.max_stale_recheck_age_seconds != _max_seconds(
        tuple(row.stale_recheck_age_seconds for row in report.rows),
    ):
        raise ValueError("max_stale_recheck_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    for index, row in enumerate(report.rows, start=1):
        if row.priority_rank != _count(index):
            raise ValueError("priority_rank values must be sequential")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sorting")
    _validate_row_times(report.rows, report.generated_at)


def _validate_input_times(
    rows: tuple[MarketCloseAcknowledgementRecheckPriorityInput, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.closed_at > generated_at:
            raise ValueError("closed_at must be <= generated_at")
        if row.acknowledged_at is not None and row.acknowledged_at > generated_at:
            raise ValueError("acknowledged_at must be <= generated_at")
        if row.last_rechecked_at is not None and row.last_rechecked_at > generated_at:
            raise ValueError("last_rechecked_at must be <= generated_at")


def _validate_row_times(
    rows: tuple[MarketCloseAcknowledgementRecheckPriorityRow, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.closed_at > generated_at:
            raise ValueError("closed_at must be <= generated_at")
        if row.acknowledged_at is not None and row.acknowledged_at > generated_at:
            raise ValueError("acknowledged_at must be <= generated_at")
        if row.last_rechecked_at is not None and row.last_rechecked_at > generated_at:
            raise ValueError("last_rechecked_at must be <= generated_at")
        if row.close_time_lag_seconds != _close_time_lag_seconds(row, generated_at):
            raise ValueError("close_time_lag_seconds must match generated_at")
        expected_stale_age = _duration_seconds(
            row.closed_at if row.last_rechecked_at is None else row.last_rechecked_at,
            generated_at,
        )
        if row.stale_recheck_age_seconds != expected_stale_age:
            raise ValueError("stale_recheck_age_seconds must match generated_at")


def _row_sort_key(
    row: MarketCloseAcknowledgementRecheckPriorityRow,
) -> tuple[Decimal, Decimal, Decimal, tuple[str, ...], str, str, str, str]:
    return (
        -row.close_time_lag_seconds,
        -row.missing_ack_pressure_ratio,
        -row.stale_recheck_age_seconds,
        row.reason_codes,
        row.market_slug,
        _datetime_key(row.closed_at),
        _datetime_key(row.acknowledged_at),
        _datetime_key(row.last_rechecked_at),
    )


def _datetime_key(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.isoformat()


def _status_count(
    rows: tuple[MarketCloseAcknowledgementRecheckPriorityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.priority_status == status))


def _has_close_lag_reason(row: MarketCloseAcknowledgementRecheckPriorityRow) -> bool:
    return (
        "market_close_ack_priority_close_time_lag_critical" in row.reason_codes
        or "market_close_ack_priority_close_time_lag_watch" in row.reason_codes
    )


def _has_stale_recheck_reason(row: MarketCloseAcknowledgementRecheckPriorityRow) -> bool:
    return (
        "market_close_ack_priority_stale_recheck_age_critical" in row.reason_codes
        or "market_close_ack_priority_stale_recheck_age_watch" in row.reason_codes
    )


def _close_time_lag_seconds(
    row: (
        MarketCloseAcknowledgementRecheckPriorityInput
        | MarketCloseAcknowledgementRecheckPriorityRow
    ),
    generated_at: datetime,
) -> Decimal:
    end = generated_at if row.acknowledged_at is None else row.acknowledged_at
    return _duration_seconds(row.closed_at, end)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("end time must be >= start time")
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
        return seconds.quantize(SECONDS_QUANTUM)


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    return max(values, default=ZERO_RATIO)


def _max_seconds(values: tuple[Decimal, ...]) -> Decimal:
    return max(values, default=ZERO_SECONDS)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(field_name, value)
    if decimal_value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        normalized = decimal_value.quantize(COUNT_QUANTUM)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > Decimal("1"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(RATIO_QUANTUM)


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(SECONDS_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.utcoffset() != UTC_OFFSET:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain a canonical string")
    if any(character < " " for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
        if reason_code not in seen:
            seen.add(reason_code)
            normalized.append(reason_code)
    expected = tuple(
        reason_code
        for reason_code in allowed
        if reason_code in normalized
    )
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must be deterministic")
    return tuple(normalized)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


__all__ = (
    "DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_PRIORITY_CONFIG_VERSION",
    "MarketCloseAcknowledgementRecheckPriorityConfig",
    "MarketCloseAcknowledgementRecheckPriorityInput",
    "MarketCloseAcknowledgementRecheckPriorityReport",
    "MarketCloseAcknowledgementRecheckPriorityRow",
    "build_market_close_acknowledgement_recheck_priority_report",
    "market_close_acknowledgement_recheck_priority_report_to_payload",
)
