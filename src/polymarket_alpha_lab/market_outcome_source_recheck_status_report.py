"""Read-only status report for market outcome source rechecks."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_STATUS_REPORT_CONFIG_VERSION = (
    "market-outcome-source-recheck-status-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DIGEST_FIELD = "derived_validation_digest"

_BLOCKED_REASON = "market_outcome_source_recheck_blocked"
_CONFLICT_REASON = "market_outcome_source_recheck_conflict"
_OPEN_GAP_REASON = "market_outcome_source_recheck_open_gap"
_OVERDUE_REASON = "market_outcome_source_recheck_overdue"
_STALE_ACK_REASON = "market_outcome_source_recheck_stale_ack"
_STALE_EVIDENCE_REASON = "market_outcome_source_recheck_stale_evidence"
_CLEARED_REASON = "market_outcome_source_recheck_cleared"

_RECHECK_STATUSES = ("blocked", "overdue", "watch", "cleared")
_STATUS_WEIGHT = {"blocked": 0, "overdue": 1, "watch": 2, "cleared": 3}
_REASON_CODES = (
    _BLOCKED_REASON,
    _CONFLICT_REASON,
    _OPEN_GAP_REASON,
    _OVERDUE_REASON,
    _STALE_ACK_REASON,
    _STALE_EVIDENCE_REASON,
    _CLEARED_REASON,
)
_REASON_WEIGHT = {reason_code: index for index, reason_code in enumerate(_REASON_CODES)}
_SURFACE_FRAGMENTS = (
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "".join(("per", "sist")),
)


__all__ = (
    "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_STATUS_REPORT_CONFIG_VERSION",
    "MarketOutcomeSourceRecheckObservation",
    "MarketOutcomeSourceRecheckStatusConfig",
    "MarketOutcomeSourceRecheckStatusReport",
    "MarketOutcomeSourceRecheckStatusRow",
    "build_market_outcome_source_recheck_status_report",
    "market_outcome_source_recheck_status_report_payload",
    "validate_market_outcome_source_recheck_status_report_payload",
)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckStatusConfig:
    config_version: str = (
        DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_STATUS_REPORT_CONFIG_VERSION
    )
    due_grace_seconds: Decimal = Decimal("0.000000")
    stale_ack_seconds: Decimal = Decimal("3600.000000")
    stale_evidence_seconds: Decimal = Decimal("7200.000000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckStatusConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "due_grace_seconds",
            _normalize_nonnegative_decimal(
                "due_grace_seconds",
                self.due_grace_seconds,
            ),
        )
        for field_name in ("stale_ack_seconds", "stale_evidence_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckObservation:
    market_slug: str
    condition_id: str
    source_id: str
    source_family: str
    next_recheck_due_at: datetime
    last_acknowledged_at: datetime | None
    last_evidence_checked_at: datetime | None
    open_gap_count: Decimal = Decimal("0.000000")
    conflict_count: Decimal = Decimal("0.000000")
    blocked: bool = False
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "condition_id",
            "source_id",
            "source_family",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "next_recheck_due_at",
            _as_utc("next_recheck_due_at", self.next_recheck_due_at),
        )
        object.__setattr__(
            self,
            "last_acknowledged_at",
            _optional_as_utc("last_acknowledged_at", self.last_acknowledged_at),
        )
        object.__setattr__(
            self,
            "last_evidence_checked_at",
            _optional_as_utc(
                "last_evidence_checked_at",
                self.last_evidence_checked_at,
            ),
        )
        for field_name in ("open_gap_count", "conflict_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if type(self.blocked) is not bool:
            raise ValueError("blocked must be a bool")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("observation", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckStatusRow:
    market_slug: str
    condition_id: str
    source_id: str
    source_family: str
    next_recheck_due_at: datetime
    last_acknowledged_at: datetime | None
    last_evidence_checked_at: datetime | None
    recheck_status: str
    due_age_seconds: Decimal
    ack_age_seconds: Decimal | None
    evidence_age_seconds: Decimal | None
    open_gap_count: Decimal
    conflict_count: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckStatusRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "condition_id",
            "source_id",
            "source_family",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "next_recheck_due_at",
            _as_utc("next_recheck_due_at", self.next_recheck_due_at),
        )
        object.__setattr__(
            self,
            "last_acknowledged_at",
            _optional_as_utc("last_acknowledged_at", self.last_acknowledged_at),
        )
        object.__setattr__(
            self,
            "last_evidence_checked_at",
            _optional_as_utc(
                "last_evidence_checked_at",
                self.last_evidence_checked_at,
            ),
        )
        _require_recheck_status("recheck_status", self.recheck_status)
        object.__setattr__(
            self,
            "due_age_seconds",
            _normalize_nonnegative_decimal("due_age_seconds", self.due_age_seconds),
        )
        for field_name in ("ack_age_seconds", "evidence_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("open_gap_count", "conflict_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckStatusReport:
    generated_at: datetime
    config_version: str
    report_status: str
    row_count: Decimal
    blocked_count: Decimal
    overdue_count: Decimal
    watch_count: Decimal
    cleared_count: Decimal
    attention_count: Decimal
    open_gap_count: Decimal
    conflict_count: Decimal
    stale_ack_count: Decimal
    stale_evidence_count: Decimal
    attention_ratio: Decimal
    oldest_due_age_seconds: Decimal | None
    rows: tuple[MarketOutcomeSourceRecheckStatusRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckStatusReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_recheck_status("report_status", self.report_status)
        for field_name in (
            "row_count",
            "blocked_count",
            "overdue_count",
            "watch_count",
            "cleared_count",
            "attention_count",
            "open_gap_count",
            "conflict_count",
            "stale_ack_count",
            "stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "attention_ratio",
            _normalize_ratio("attention_ratio", self.attention_ratio),
        )
        object.__setattr__(
            self,
            "oldest_due_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "oldest_due_age_seconds",
                self.oldest_due_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_counts(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)
        _validate_report_payload_shape(self)


def build_market_outcome_source_recheck_status_report(
    observations: Iterable[MarketOutcomeSourceRecheckObservation],
    *,
    config: MarketOutcomeSourceRecheckStatusConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckStatusReport:
    if type(config) is not MarketOutcomeSourceRecheckStatusConfig:
        raise ValueError("config must be a MarketOutcomeSourceRecheckStatusConfig")
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    _require_or_set_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    values = _normalize_observations(observations, generated_at=generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    value,
                    config=config,
                    generated_at=generated_at,
                )
                for value in values
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _decimal_count(len(rows))
    cleared_count = _status_count(rows, "cleared")
    attention_count = _quantize(row_count - cleared_count)

    return MarketOutcomeSourceRecheckStatusReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_status=_report_status(rows),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        overdue_count=_status_count(rows, "overdue"),
        watch_count=_status_count(rows, "watch"),
        cleared_count=cleared_count,
        attention_count=attention_count,
        open_gap_count=_sum_count(row.open_gap_count for row in rows),
        conflict_count=_sum_count(row.conflict_count for row in rows),
        stale_ack_count=_reason_count(rows, _STALE_ACK_REASON),
        stale_evidence_count=_reason_count(rows, _STALE_EVIDENCE_REASON),
        attention_ratio=_ratio(attention_count, row_count),
        oldest_due_age_seconds=_oldest_due_age_seconds(rows),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def market_outcome_source_recheck_status_report_payload(
    report: MarketOutcomeSourceRecheckStatusReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeSourceRecheckStatusReport:
        raise ValueError("report must be a MarketOutcomeSourceRecheckStatusReport")
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_market_outcome_source_recheck_status_report_payload(payload)
    return payload


def validate_market_outcome_source_recheck_status_report_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return True


def _row_from_observation(
    value: MarketOutcomeSourceRecheckObservation,
    *,
    config: MarketOutcomeSourceRecheckStatusConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckStatusRow:
    due_age_seconds = _due_age_seconds(value.next_recheck_due_at, generated_at)
    ack_age_seconds = _known_age_seconds(
        "last_acknowledged_at",
        value.last_acknowledged_at,
        generated_at,
    )
    evidence_age_seconds = _known_age_seconds(
        "last_evidence_checked_at",
        value.last_evidence_checked_at,
        generated_at,
    )
    reason_codes = _row_reason_codes(
        blocked=value.blocked,
        open_gap_count=value.open_gap_count,
        conflict_count=value.conflict_count,
        due_age_seconds=due_age_seconds,
        ack_age_seconds=ack_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
        config=config,
    )

    return MarketOutcomeSourceRecheckStatusRow(
        market_slug=value.market_slug,
        condition_id=value.condition_id,
        source_id=value.source_id,
        source_family=value.source_family,
        next_recheck_due_at=value.next_recheck_due_at,
        last_acknowledged_at=value.last_acknowledged_at,
        last_evidence_checked_at=value.last_evidence_checked_at,
        recheck_status=_row_status(reason_codes),
        due_age_seconds=due_age_seconds,
        ack_age_seconds=ack_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
        open_gap_count=value.open_gap_count,
        conflict_count=value.conflict_count,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    blocked: bool,
    open_gap_count: Decimal,
    conflict_count: Decimal,
    due_age_seconds: Decimal,
    ack_age_seconds: Decimal | None,
    evidence_age_seconds: Decimal | None,
    config: MarketOutcomeSourceRecheckStatusConfig,
) -> tuple[str, ...]:
    requested_codes: list[str] = []
    if blocked:
        requested_codes.append(_BLOCKED_REASON)
    if conflict_count > _ZERO:
        requested_codes.append(_CONFLICT_REASON)
    if open_gap_count > _ZERO:
        requested_codes.append(_OPEN_GAP_REASON)
    if due_age_seconds > config.due_grace_seconds:
        requested_codes.append(_OVERDUE_REASON)
    if ack_age_seconds is None or ack_age_seconds > config.stale_ack_seconds:
        requested_codes.append(_STALE_ACK_REASON)
    if (
        evidence_age_seconds is None
        or evidence_age_seconds > config.stale_evidence_seconds
    ):
        requested_codes.append(_STALE_EVIDENCE_REASON)
    if not requested_codes:
        requested_codes.append(_CLEARED_REASON)
    return tuple(reason_code for reason_code in _REASON_CODES if reason_code in requested_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if _BLOCKED_REASON in reason_codes or _CONFLICT_REASON in reason_codes:
        return "blocked"
    if _OVERDUE_REASON in reason_codes:
        return "overdue"
    if (
        _OPEN_GAP_REASON in reason_codes
        or _STALE_ACK_REASON in reason_codes
        or _STALE_EVIDENCE_REASON in reason_codes
    ):
        return "watch"
    return "cleared"


def _report_status(rows: tuple[MarketOutcomeSourceRecheckStatusRow, ...]) -> str:
    if not rows:
        return "cleared"
    return min((row.recheck_status for row in rows), key=lambda item: _STATUS_WEIGHT[item])


def _report_reason_codes(
    rows: tuple[MarketOutcomeSourceRecheckStatusRow, ...],
) -> tuple[str, ...]:
    requested_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != _CLEARED_REASON
    }
    if not requested_codes:
        return (_CLEARED_REASON,)
    return tuple(reason_code for reason_code in _REASON_CODES if reason_code in requested_codes)


def _normalize_observations(
    values: Iterable[MarketOutcomeSourceRecheckObservation],
    *,
    generated_at: datetime,
) -> tuple[MarketOutcomeSourceRecheckObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for value in observations:
        if type(value) is not MarketOutcomeSourceRecheckObservation:
            raise ValueError(
                "observations must contain MarketOutcomeSourceRecheckObservation values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("observation", value)
        _require_or_set_digest(value)
        for field_name in ("last_acknowledged_at", "last_evidence_checked_at"):
            known_at = getattr(value, field_name)
            if known_at is not None and known_at > generated_at:
                raise ValueError("known timestamp must be at or before generated_at")
        key = (value.market_slug, value.condition_id, value.source_id)
        if key in seen_keys:
            raise ValueError("observations must contain unique recheck keys")
        seen_keys.add(key)
    return observations


def _normalize_rows(
    values: Iterable[MarketOutcomeSourceRecheckStatusRow],
) -> tuple[MarketOutcomeSourceRecheckStatusRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain MarketOutcomeSourceRecheckStatusRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain MarketOutcomeSourceRecheckStatusRow values",
        ) from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketOutcomeSourceRecheckStatusRow:
            raise ValueError(
                "rows must contain MarketOutcomeSourceRecheckStatusRow values",
            )
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
        key = _row_identity(row)
        if key in seen_keys:
            raise ValueError("rows must be unique")
        seen_keys.add(key)
    return rows


def _validate_row_consistency(row: MarketOutcomeSourceRecheckStatusRow) -> None:
    if row.recheck_status != _row_status(row.reason_codes):
        raise ValueError("reason_codes must match recheck_status")
    if row.recheck_status == "cleared" and row.reason_codes != (_CLEARED_REASON,):
        raise ValueError("reason_codes must use cleared reason for cleared rows")
    if row.open_gap_count > _ZERO and _OPEN_GAP_REASON not in row.reason_codes:
        raise ValueError("reason_codes must include open gap reason")
    if row.conflict_count > _ZERO and _CONFLICT_REASON not in row.reason_codes:
        raise ValueError("reason_codes must include conflict reason")
    if _OPEN_GAP_REASON in row.reason_codes and row.open_gap_count <= _ZERO:
        raise ValueError("open_gap_count must explain open gap reason")
    if _CONFLICT_REASON in row.reason_codes and row.conflict_count <= _ZERO:
        raise ValueError("conflict_count must explain conflict reason")
    if _CLEARED_REASON in row.reason_codes and len(row.reason_codes) != 1:
        raise ValueError("reason_codes must not mix cleared with attention reasons")


def _validate_report_counts(report: MarketOutcomeSourceRecheckStatusReport) -> None:
    rows = report.rows
    row_count = _decimal_count(len(rows))
    if report.row_count != row_count:
        raise ValueError("row_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.overdue_count != _status_count(rows, "overdue"):
        raise ValueError("overdue_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.cleared_count != _status_count(rows, "cleared"):
        raise ValueError("cleared_count must match rows")
    if report.attention_count != _quantize(report.row_count - report.cleared_count):
        raise ValueError("attention_count must match rows")
    if report.open_gap_count != _sum_count(row.open_gap_count for row in rows):
        raise ValueError("open_gap_count must match rows")
    if report.conflict_count != _sum_count(row.conflict_count for row in rows):
        raise ValueError("conflict_count must match rows")
    if report.stale_ack_count != _reason_count(rows, _STALE_ACK_REASON):
        raise ValueError("stale_ack_count must match rows")
    if report.stale_evidence_count != _reason_count(rows, _STALE_EVIDENCE_REASON):
        raise ValueError("stale_evidence_count must match rows")
    if report.attention_ratio != _ratio(report.attention_count, report.row_count):
        raise ValueError("attention_ratio must match rows")
    if report.oldest_due_age_seconds != _oldest_due_age_seconds(rows):
        raise ValueError("oldest_due_age_seconds must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_report_payload_shape(report: MarketOutcomeSourceRecheckStatusReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("payload rows must use deterministic status sort")


def _row_sort_key(row: MarketOutcomeSourceRecheckStatusRow) -> tuple[int, int, str, str, str]:
    return (
        _STATUS_WEIGHT[row.recheck_status],
        _primary_reason_weight(row.reason_codes),
        row.market_slug,
        row.condition_id,
        row.source_id,
    )


def _primary_reason_weight(reason_codes: tuple[str, ...]) -> int:
    return min(_REASON_WEIGHT[reason_code] for reason_code in reason_codes)


def _row_identity(row: MarketOutcomeSourceRecheckStatusRow) -> tuple[str, str, str]:
    return (row.market_slug, row.condition_id, row.source_id)


def _status_count(
    rows: tuple[MarketOutcomeSourceRecheckStatusRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.recheck_status == status))


def _reason_count(
    rows: tuple[MarketOutcomeSourceRecheckStatusRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _sum_count(values: Iterable[Decimal]) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _oldest_due_age_seconds(
    rows: tuple[MarketOutcomeSourceRecheckStatusRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.due_age_seconds for row in rows)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _due_age_seconds(next_due_at: datetime, generated_at: datetime) -> Decimal:
    if next_due_at >= generated_at:
        return _ZERO
    return _seconds_between(next_due_at, generated_at)


def _known_age_seconds(
    field_name: str,
    value: datetime | None,
    generated_at: datetime,
) -> Decimal | None:
    if value is None:
        return None
    if value > generated_at:
        raise ValueError(f"{field_name} known timestamp must be at or before generated_at")
    return _seconds_between(value, generated_at)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    if delta < timedelta(0):
        raise ValueError("datetime range must be nonnegative")
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in _REASON_WEIGHT:
            raise ValueError("reason_codes must contain known values")
    expected = tuple(reason_code for reason_code in _REASON_CODES if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_recheck_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _RECHECK_STATUSES:
        raise ValueError(f"{field_name} must be blocked, overdue, watch, or cleared")


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_as_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _payload_value(value: object, *, include_digest: bool = True) -> object:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item, include_digest=include_digest) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(
                getattr(value, field.name),
                include_digest=include_digest,
            )
            for field in fields(value)
            if include_digest or field.name != _DIGEST_FIELD
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    expected = _payload_digest(_payload_value(value, include_digest=False))
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if type(current) is not str or current != expected:
        raise ValueError("derived_validation_digest payload mismatch")


def _payload_digest(value: object) -> str:
    ready = _strip_digest_fields(value)
    encoded = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _strip_digest_fields(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _strip_digest_fields(item)
            for key, item in value.items()
            if key != _DIGEST_FIELD
        }
    if isinstance(value, list):
        return [_strip_digest_fields(item) for item in value]
    return value


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _validate_payload_digest_tree(item)
        if _DIGEST_FIELD in value:
            current = value[_DIGEST_FIELD]
            if type(current) is not str or current != _payload_digest(value):
                raise ValueError("derived_validation_digest payload mismatch")
    elif isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload field must be a string")
            if _contains_surface_fragment(key):
                raise ValueError("unsafe live surface field")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, list) or isinstance(value, tuple):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if _contains_surface_fragment(field.name):
                raise ValueError("unsafe live surface field")
            _reject_unsafe_public_surface(label, getattr(value, field.name))
        return
    if type(value) is str and _contains_surface_fragment(value):
        raise ValueError("unsafe public value")


def _contains_surface_fragment(value: str) -> bool:
    normalized = "".join(character for character in value.lower() if character.isalnum())
    return any(fragment in normalized for fragment in _SURFACE_FRAGMENTS)


def _require_public_payload_values(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True")
            _require_public_payload_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_public_payload_values(item)
        return
    if type(value) in (float, int, Decimal):
        raise ValueError("Decimal-derived public values must be strings")
    if value is None or type(value) in (str, bool):
        return
    raise ValueError("public payload contains unsupported value")
