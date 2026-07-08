"""Pure in-memory resolution timeline report for prediction event research."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_CONFIG_VERSION = "market-resolution-timeline-report-v0"
EVENT_TYPES = (
    "info_refresh",
    "settlement_evidence",
    "dispute_window",
    "postmortem",
)
STATUSES = ("pass", "watch", "block")

PASS_REASON = "resolution_timeline_pass"
NO_EVENTS_REASON = "no_resolution_timeline_events"
INFO_REFRESH_WATCH_REASON = "info_refresh_overdue_watch"
SETTLEMENT_EVIDENCE_WATCH_REASON = "settlement_evidence_incomplete_watch"
SETTLEMENT_EVIDENCE_BLOCK_REASON = "settlement_evidence_incomplete_block"
DISPUTE_OPEN_REASON = "dispute_window_open"
DISPUTE_EXPIRED_REASON = "dispute_window_expired_block"
POSTMORTEM_WATCH_REASON = "postmortem_overdue_watch"
POSTMORTEM_BLOCK_REASON = "postmortem_overdue_block"

ISSUE_REASONS = (
    INFO_REFRESH_WATCH_REASON,
    SETTLEMENT_EVIDENCE_WATCH_REASON,
    SETTLEMENT_EVIDENCE_BLOCK_REASON,
    DISPUTE_OPEN_REASON,
    DISPUTE_EXPIRED_REASON,
    POSTMORTEM_WATCH_REASON,
    POSTMORTEM_BLOCK_REASON,
)
REASON_CODES = (PASS_REASON, NO_EVENTS_REASON) + ISSUE_REASONS

QUANT = Decimal("0.000001")
ZERO = Decimal("0")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "credential",
        "private",
        "secret",
        _join_parts("to", "ken"),
        _join_parts("que", "stion"),
        "slug",
        _join_parts("source", "_", "url"),
        "url",
        _join_parts("te", "xt"),
        "dsn",
        _join_parts("tab", "le"),
        _join_parts("wal", "let"),
        _join_parts("or", "der"),
        _join_parts("sig", "ning"),
        _join_parts("acc", "ount"),
    ),
)


@dataclass(frozen=True)
class MarketResolutionTimelineConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    info_refresh_grace_seconds: Decimal = Decimal("3600.000000")
    settlement_evidence_grace_seconds: Decimal = Decimal("7200.000000")
    dispute_window_grace_seconds: Decimal = Decimal("86400.000000")
    postmortem_grace_seconds: Decimal = Decimal("172800.000000")
    min_settlement_evidence_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "info_refresh_grace_seconds",
            "settlement_evidence_grace_seconds",
            "dispute_window_grace_seconds",
            "postmortem_grace_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_settlement_evidence_count",
            _require_positive_whole_decimal(
                "min_settlement_evidence_count",
                self.min_settlement_evidence_count,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResolutionTimelineEventInput:
    event_id: str
    market_id: str
    event_type: str
    due_at: datetime
    completed_at: datetime | None = None
    evidence_count: Decimal = Decimal("0")
    dispute_open: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("event_id", self.event_id)
        _require_public_string("market_id", self.market_id)
        _require_enum("event_type", self.event_type, EVENT_TYPES)
        object.__setattr__(self, "due_at", _as_utc("due_at", self.due_at))
        object.__setattr__(
            self,
            "completed_at",
            _optional_utc("completed_at", self.completed_at),
        )
        object.__setattr__(
            self,
            "evidence_count",
            _require_nonnegative_whole_decimal("evidence_count", self.evidence_count),
        )
        if type(self.dispute_open) is not bool:
            raise ValueError("dispute_open must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("event", self)


@dataclass(frozen=True)
class MarketResolutionTimelineRow:
    event_id: str
    market_id: str
    event_type: str
    due_at: datetime
    completed_at: datetime | None
    evidence_count: Decimal
    dispute_open: bool
    seconds_until_due: Decimal
    completion_lag_seconds: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("event_id", self.event_id)
        _require_public_string("market_id", self.market_id)
        _require_enum("event_type", self.event_type, EVENT_TYPES)
        object.__setattr__(self, "due_at", _as_utc("due_at", self.due_at))
        object.__setattr__(
            self,
            "completed_at",
            _optional_utc("completed_at", self.completed_at),
        )
        object.__setattr__(
            self,
            "evidence_count",
            _require_nonnegative_whole_decimal("evidence_count", self.evidence_count),
        )
        if type(self.dispute_open) is not bool:
            raise ValueError("dispute_open must be a bool")
        object.__setattr__(
            self,
            "seconds_until_due",
            _quantize(_require_decimal("seconds_until_due", self.seconds_until_due)),
        )
        object.__setattr__(
            self,
            "completion_lag_seconds",
            _optional_nonnegative_decimal(
                "completion_lag_seconds",
                self.completion_lag_seconds,
            ),
        )
        _require_enum("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResolutionTimelineReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResolutionTimelineReport:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    open_dispute_count: Decimal
    overdue_event_count: Decimal
    next_due_at: datetime | None
    status: str
    rows: tuple[MarketResolutionTimelineRow, ...]
    reason_code_counts: tuple[MarketResolutionTimelineReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "event_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "open_dispute_count",
            "overdue_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "next_due_at", _optional_utc("next_due_at", self.next_due_at))
        _require_enum("status", self.status, STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_resolution_timeline_report(
    event_rows: object,
    *,
    config: MarketResolutionTimelineConfig,
    generated_at: datetime,
) -> MarketResolutionTimelineReport:
    if type(config) is not MarketResolutionTimelineConfig:
        raise ValueError("config must be a MarketResolutionTimelineConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    events = _normalize_event_inputs(event_rows, generated_at=generated_at_utc)
    rows = tuple(
        _timeline_row(event, config=config, generated_at=generated_at_utc)
        for event in events
    )
    reason_codes = _report_reason_codes(rows)
    return MarketResolutionTimelineReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_decimal_count(len({row.market_id for row in rows})),
        event_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_decimal_count(sum(1 for row in rows if row.status == "watch")),
        blocked_count=_decimal_count(sum(1 for row in rows if row.status == "block")),
        open_dispute_count=_decimal_count(sum(1 for row in rows if row.dispute_open)),
        overdue_event_count=_decimal_count(
            sum(1 for row in rows if _is_overdue_pending(row, generated_at_utc)),
        ),
        next_due_at=_next_due_at(rows, generated_at_utc),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def market_resolution_timeline_report_payload(
    report: MarketResolutionTimelineReport,
) -> dict[str, Any]:
    if type(report) is not MarketResolutionTimelineReport:
        raise ValueError("report must be a MarketResolutionTimelineReport")
    _require_hard_flags("report", report)
    market_refs = {
        market_id: f"market_{index:03d}"
        for index, market_id in enumerate(sorted({row.market_id for row in report.rows}), 1)
    }
    payload: dict[str, Any] = {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "market_count": _payload_value(report.market_count),
        "event_count": _payload_value(report.event_count),
        "pass_count": _payload_value(report.pass_count),
        "watch_count": _payload_value(report.watch_count),
        "blocked_count": _payload_value(report.blocked_count),
        "open_dispute_count": _payload_value(report.open_dispute_count),
        "overdue_event_count": _payload_value(report.overdue_event_count),
        "next_due_at": _payload_value(report.next_due_at),
        "status": report.status,
        "rows": [
            {
                "event_ref": f"event_{index:03d}",
                "market_ref": market_refs[row.market_id],
                "event_type": row.event_type,
                "due_at": _payload_value(row.due_at),
                "completed_at": _payload_value(row.completed_at),
                "evidence_count": _payload_value(row.evidence_count),
                "dispute_open": row.dispute_open,
                "seconds_until_due": _payload_value(row.seconds_until_due),
                "completion_lag_seconds": _payload_value(row.completion_lag_seconds),
                "status": row.status,
                "reason_codes": list(row.reason_codes),
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            }
            for index, row in enumerate(report.rows, 1)
        ],
        "reason_code_counts": [
            {
                "reason_code": count.reason_code,
                "count": _payload_value(count.count),
                "paper_only": count.paper_only,
                "report_only": count.report_only,
                "readonly": count.readonly,
            }
            for count in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    _reject_unsafe_public_payload("market resolution timeline report payload", payload)
    return payload


def _normalize_event_inputs(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketResolutionTimelineEventInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("event rows must be an iterable of event row shapes")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("event rows must be an iterable of event row shapes") from exc
    events = tuple(_coerce_event_input(row) for row in rows)
    seen: set[tuple[str, str]] = set()
    for event in events:
        if event.due_at > generated_at and event.completed_at is not None:
            raise ValueError("completed_at must not be set before an event is due")
        if event.completed_at is not None and event.completed_at > generated_at:
            raise ValueError("completed_at must not be in the future")
        key = (event.market_id, event.event_id)
        if key in seen:
            raise ValueError("event_id values must be unique per market")
        seen.add(key)
    return tuple(
        sorted(
            events,
            key=lambda event: (
                event.market_id,
                event.due_at,
                event.event_type,
                event.event_id,
            ),
        ),
    )


def _coerce_event_input(value: object) -> MarketResolutionTimelineEventInput:
    if type(value) is MarketResolutionTimelineEventInput:
        _require_hard_flags("event", value)
        return value
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("event rows must be an iterable of event row shapes")
    try:
        return MarketResolutionTimelineEventInput(
            event_id=getattr(value, "event_id"),
            market_id=getattr(value, "market_id"),
            event_type=getattr(value, "event_type"),
            due_at=getattr(value, "due_at"),
            completed_at=getattr(value, "completed_at"),
            evidence_count=getattr(value, "evidence_count"),
            dispute_open=getattr(value, "dispute_open"),
            reason_codes=getattr(value, "reason_codes"),
            paper_only=getattr(value, "paper_only"),
            report_only=getattr(value, "report_only"),
            readonly=getattr(value, "readonly"),
        )
    except AttributeError as exc:
        raise ValueError("event rows must be an iterable of event row shapes") from exc


def _timeline_row(
    event: MarketResolutionTimelineEventInput,
    *,
    config: MarketResolutionTimelineConfig,
    generated_at: datetime,
) -> MarketResolutionTimelineRow:
    seconds_until_due = _duration_seconds(generated_at, event.due_at)
    completion_lag_seconds = (
        None
        if event.completed_at is None
        else _duration_seconds(event.due_at, event.completed_at)
    )
    status, reason_codes = _row_status_and_reasons(
        event,
        config=config,
        generated_at=generated_at,
    )
    return MarketResolutionTimelineRow(
        event_id=event.event_id,
        market_id=event.market_id,
        event_type=event.event_type,
        due_at=event.due_at,
        completed_at=event.completed_at,
        evidence_count=event.evidence_count,
        dispute_open=event.dispute_open,
        seconds_until_due=seconds_until_due,
        completion_lag_seconds=completion_lag_seconds,
        status=status,
        reason_codes=reason_codes,
    )


def _row_status_and_reasons(
    event: MarketResolutionTimelineEventInput,
    *,
    config: MarketResolutionTimelineConfig,
    generated_at: datetime,
) -> tuple[str, tuple[str, ...]]:
    overdue_seconds = max(_duration_seconds(event.due_at, generated_at), ZERO)
    status = "pass"
    reasons: list[str] = []
    if event.event_type == "info_refresh":
        if event.completed_at is None and event.due_at < generated_at:
            status = "watch"
            reasons.append(INFO_REFRESH_WATCH_REASON)
    elif event.event_type == "settlement_evidence":
        if event.evidence_count < config.min_settlement_evidence_count:
            if event.due_at < generated_at:
                if overdue_seconds > config.settlement_evidence_grace_seconds:
                    status = "block"
                    reasons.append(SETTLEMENT_EVIDENCE_BLOCK_REASON)
                else:
                    status = "watch"
                    reasons.append(SETTLEMENT_EVIDENCE_WATCH_REASON)
        elif event.due_at < generated_at and event.completed_at is None:
            status = "watch"
            reasons.append(SETTLEMENT_EVIDENCE_WATCH_REASON)
    elif event.event_type == "dispute_window":
        if event.dispute_open:
            if event.due_at < generated_at and overdue_seconds > config.dispute_window_grace_seconds:
                status = "block"
                reasons.append(DISPUTE_EXPIRED_REASON)
            else:
                status = "watch"
                reasons.append(DISPUTE_OPEN_REASON)
    elif event.event_type == "postmortem":
        if event.completed_at is None and event.due_at < generated_at:
            if overdue_seconds > config.postmortem_grace_seconds:
                status = "block"
                reasons.append(POSTMORTEM_BLOCK_REASON)
            else:
                status = "watch"
                reasons.append(POSTMORTEM_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    reasons.extend(f"input_{reason_code}" for reason_code in event.reason_codes)
    return status, _normalize_reason_codes("reason_codes", tuple(reasons), allow_empty=False)


def _report_status(rows: tuple[MarketResolutionTimelineRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[MarketResolutionTimelineRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (NO_EVENTS_REASON,)
    reasons: list[str] = []
    for reason in ISSUE_REASONS:
        if any(reason in row.reason_codes for row in rows):
            reasons.append(reason)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), allow_empty=False)


def _reason_code_counts(
    rows: tuple[MarketResolutionTimelineRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[MarketResolutionTimelineReasonCodeCount, ...]:
    if not rows:
        return tuple(
            MarketResolutionTimelineReasonCodeCount(reason_code=code, count=Decimal("1"))
            for code in report_reason_codes
        )
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        MarketResolutionTimelineReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in sorted(counts)
    )


def _next_due_at(
    rows: tuple[MarketResolutionTimelineRow, ...],
    generated_at: datetime,
) -> datetime | None:
    candidates = tuple(
        row.due_at
        for row in rows
        if row.completed_at is None and row.due_at >= generated_at
    )
    if not candidates:
        return None
    return min(candidates)


def _is_overdue_pending(row: MarketResolutionTimelineRow, generated_at: datetime) -> bool:
    return row.completed_at is None and row.due_at < generated_at


def _normalize_rows(value: object) -> tuple[MarketResolutionTimelineRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = value
    for row in rows:
        if type(row) is not MarketResolutionTimelineRow:
            raise ValueError("rows must contain MarketResolutionTimelineRow values")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResolutionTimelineReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    counts = value
    seen: set[str] = set()
    for item in counts:
        if type(item) is not MarketResolutionTimelineReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code counts")
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason codes")
        seen.add(item.reason_code)
        _require_hard_flags("reason_code_count", item)
    return tuple(sorted(counts, key=lambda item: item.reason_code))


def _validate_row(row: MarketResolutionTimelineRow) -> None:
    has_issue_reason = any(reason in ISSUE_REASONS for reason in row.reason_codes)
    has_pass_reason = PASS_REASON in row.reason_codes
    if row.status == "pass":
        if has_issue_reason or not has_pass_reason:
            raise ValueError("status does not match reason_codes")
    elif not has_issue_reason or has_pass_reason:
        raise ValueError("status does not match reason_codes")
    if row.completed_at is not None and row.completion_lag_seconds is None:
        raise ValueError("completion_lag_seconds must be set when completed_at is set")
    if row.completed_at is None and row.completion_lag_seconds is not None:
        raise ValueError("completion_lag_seconds must be None when completed_at is None")


def _validate_report(report: MarketResolutionTimelineReport) -> None:
    if report.market_count != _decimal_count(len({row.market_id for row in report.rows})):
        raise ValueError("market_count does not match rows")
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count does not match rows")
    if report.pass_count != _decimal_count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _decimal_count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count does not match rows")
    if report.blocked_count != _decimal_count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("blocked_count does not match rows")
    if report.open_dispute_count != _decimal_count(sum(1 for row in report.rows if row.dispute_open)):
        raise ValueError("open_dispute_count does not match rows")
    if report.overdue_event_count != _decimal_count(
        sum(1 for row in report.rows if _is_overdue_pending(row, report.generated_at)),
    ):
        raise ValueError("overdue_event_count does not match rows")
    if report.next_due_at != _next_due_at(report.rows, report.generated_at):
        raise ValueError("next_due_at does not match rows")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status does not match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes do not match rows")


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if type(value) is list:
        return [_payload_value(item) for item in value]
    raise ValueError("unsupported payload value")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            _require_public_string(f"{label} key", key)
            _reject_unsafe_public_payload(label, value)
        return
    if isinstance(payload, list):
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if type(payload) is str:
        _require_public_string(label, payload)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    start_utc = _as_utc("start", start)
    end_utc = _as_utc("end", end)
    delta = end_utc - start_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize(seconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _optional_nonnegative_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT)


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value.lower() != value or " " in value or "-" in value:
        raise ValueError(f"{field_name} must be a lowercase underscore code")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


__all__ = (
    "MarketResolutionTimelineConfig",
    "MarketResolutionTimelineEventInput",
    "MarketResolutionTimelineReasonCodeCount",
    "MarketResolutionTimelineReport",
    "MarketResolutionTimelineRow",
    "build_market_resolution_timeline_report",
    "market_resolution_timeline_report_payload",
)
