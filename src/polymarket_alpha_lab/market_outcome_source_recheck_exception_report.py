"""Pure report-only reducer for market outcome source recheck exceptions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_EXCEPTION_REPORT_CONFIG_VERSION = (
    "market-outcome-source-recheck-exception-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DIGEST_FIELD = "derived_validation_digest"
_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "".join(("per", "sist")),
)

_STATUSES = ("pass", "watch", "blocked")
_SEVERITIES = ("info", "warning", "critical")
_STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
_SEVERITY_RANK = {"critical": 0, "warning": 1, "info": 2}

_MISSING_ACK_REASON = "missing_official_source_acknowledgement"
_STALE_SOURCE_REASON = "stale_outcome_source"
_UNRESOLVED_CONFLICT_REASON = "unresolved_source_conflict"
_REPEATED_MARKET_GAP_REASON = "repeated_market_gap"


__all__ = (
    "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_EXCEPTION_REPORT_CONFIG_VERSION",
    "MarketOutcomeSourceRecheckExceptionConfig",
    "MarketOutcomeSourceRecheckObservation",
    "MarketOutcomeSourceRecheckExceptionRow",
    "MarketOutcomeSourceRecheckExceptionReport",
    "build_market_outcome_source_recheck_exception_report",
    "market_outcome_source_recheck_exception_report_payload",
    "validate_market_outcome_source_recheck_exception_report_payload",
)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckExceptionConfig:
    config_version: str = (
        DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_EXCEPTION_REPORT_CONFIG_VERSION
    )
    stale_source_seconds: Decimal = Decimal("7200.000000")
    repeated_market_threshold: Decimal = Decimal("2.000000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckExceptionConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, MarketOutcomeSourceRecheckExceptionConfig)
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_source_seconds",
            _normalize_nonnegative_decimal(
                "stale_source_seconds",
                self.stale_source_seconds,
            ),
        )
        object.__setattr__(
            self,
            "repeated_market_threshold",
            _normalize_count(
                "repeated_market_threshold",
                self.repeated_market_threshold,
            ),
        )
        if self.repeated_market_threshold <= _ZERO:
            raise ValueError("repeated_market_threshold must be positive")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckObservation:
    market_slug: str
    condition_id: str
    source_id: str
    source_kind: str
    recheck_requested_at: datetime
    source_observed_at: datetime
    official_source_acknowledged_at: datetime | None = None
    source_conflict_resolved_at: datetime | None = None
    has_source_conflict: bool = False
    reason_codes: tuple[str, ...] = ("closed_market_pending_source_recheck",)
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
            "source_kind",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "recheck_requested_at",
            _as_utc("recheck_requested_at", self.recheck_requested_at),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "official_source_acknowledged_at",
            _optional_as_utc(
                "official_source_acknowledged_at",
                self.official_source_acknowledged_at,
            ),
        )
        object.__setattr__(
            self,
            "source_conflict_resolved_at",
            _optional_as_utc(
                "source_conflict_resolved_at",
                self.source_conflict_resolved_at,
            ),
        )
        if type(self.has_source_conflict) is not bool:
            raise ValueError("has_source_conflict must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_observation_sequence(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("observation", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckExceptionRow:
    market_slug: str
    condition_id: str
    source_id: str
    source_kind: str
    status: str
    severity: str
    reason_codes: tuple[str, ...]
    source_age_seconds: Decimal
    acknowledgement_age_seconds: Decimal | None
    recheck_to_source_delta_seconds: Decimal
    recheck_to_acknowledgement_delta_seconds: Decimal | None
    repeated_market_gap_count: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckExceptionRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "condition_id",
            "source_id",
            "source_kind",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        _require_severity("severity", self.severity)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "source_age_seconds",
            "recheck_to_source_delta_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "acknowledgement_age_seconds",
            "recheck_to_acknowledgement_delta_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "repeated_market_gap_count",
            _normalize_count(
                "repeated_market_gap_count",
                self.repeated_market_gap_count,
            ),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckExceptionReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    exception_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    missing_official_source_acknowledgement_count: Decimal
    stale_outcome_source_count: Decimal
    unresolved_source_conflict_count: Decimal
    repeated_market_gap_count: Decimal
    exception_ratio: Decimal
    rows: tuple[MarketOutcomeSourceRecheckExceptionRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckExceptionReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, MarketOutcomeSourceRecheckExceptionReport)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "exception_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "missing_official_source_acknowledgement_count",
            "stale_outcome_source_count",
            "unresolved_source_conflict_count",
            "repeated_market_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "exception_ratio",
            _normalize_ratio("exception_ratio", self.exception_ratio),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)


def build_market_outcome_source_recheck_exception_report(
    observations: Iterable[MarketOutcomeSourceRecheckObservation],
    *,
    config: MarketOutcomeSourceRecheckExceptionConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckExceptionReport:
    if type(config) is not MarketOutcomeSourceRecheckExceptionConfig:
        raise ValueError("config must be a MarketOutcomeSourceRecheckExceptionConfig")
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    _require_or_set_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    values = _normalize_observations(observations)
    _validate_generated_at_covers_values(generated_at, values)

    gap_counts = _market_gap_counts(values, config.repeated_market_threshold)
    rows = tuple(
        sorted(
            (
                row
                for value in values
                if (
                    row := _row_from_observation(
                        value,
                        config=config,
                        generated_at=generated_at,
                        repeated_gap_count=gap_counts[value.market_slug],
                    )
                )
                is not None
            ),
            key=_row_sort_key,
        ),
    )

    return MarketOutcomeSourceRecheckExceptionReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_decimal_count(len(values)),
        exception_count=_decimal_count(len(rows)),
        row_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(len(values) - len(rows)),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        missing_official_source_acknowledgement_count=_reason_count(
            rows,
            _MISSING_ACK_REASON,
        ),
        stale_outcome_source_count=_reason_count(rows, _STALE_SOURCE_REASON),
        unresolved_source_conflict_count=_reason_count(
            rows,
            _UNRESOLVED_CONFLICT_REASON,
        ),
        repeated_market_gap_count=_repeated_market_count(rows),
        exception_ratio=_ratio(_decimal_count(len(rows)), _decimal_count(len(values))),
        rows=rows,
    )


def market_outcome_source_recheck_exception_report_payload(
    report: MarketOutcomeSourceRecheckExceptionReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeSourceRecheckExceptionReport:
        raise ValueError("report must be a MarketOutcomeSourceRecheckExceptionReport")
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    validate_market_outcome_source_recheck_exception_report_payload(payload)
    return payload


def validate_market_outcome_source_recheck_exception_report_payload(
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
    config: MarketOutcomeSourceRecheckExceptionConfig,
    generated_at: datetime,
    repeated_gap_count: Decimal,
) -> MarketOutcomeSourceRecheckExceptionRow | None:
    reasons: list[str] = []
    if value.official_source_acknowledged_at is None:
        reasons.append(_MISSING_ACK_REASON)
    if value.has_source_conflict and value.source_conflict_resolved_at is None:
        reasons.append(_UNRESOLVED_CONFLICT_REASON)
    if (
        not reasons
        and _seconds_between(value.source_observed_at, generated_at)
        > config.stale_source_seconds
    ):
        reasons.append(_STALE_SOURCE_REASON)
    if repeated_gap_count >= config.repeated_market_threshold and reasons:
        reasons.append(_REPEATED_MARKET_GAP_REASON)
    if not reasons:
        return None

    reason_codes = _normalize_reason_codes(tuple(reasons))
    return MarketOutcomeSourceRecheckExceptionRow(
        market_slug=value.market_slug,
        condition_id=value.condition_id,
        source_id=value.source_id,
        source_kind=value.source_kind,
        status=_status_from_reasons(reason_codes),
        severity=_severity_from_reasons(reason_codes),
        reason_codes=reason_codes,
        source_age_seconds=_seconds_between(value.source_observed_at, generated_at),
        acknowledgement_age_seconds=_optional_seconds_between(
            value.official_source_acknowledged_at,
            generated_at,
        ),
        recheck_to_source_delta_seconds=_seconds_between(
            value.recheck_requested_at,
            value.source_observed_at,
        ),
        recheck_to_acknowledgement_delta_seconds=_optional_stage_delta(
            value.recheck_requested_at,
            value.official_source_acknowledged_at,
        ),
        repeated_market_gap_count=repeated_gap_count,
    )


def _market_gap_counts(
    values: tuple[MarketOutcomeSourceRecheckObservation, ...],
    repeated_gap_threshold: Decimal,
) -> dict[str, Decimal]:
    raw_counts: dict[str, int] = {}
    for value in values:
        if _has_base_exception(value):
            raw_counts[value.market_slug] = raw_counts.get(value.market_slug, 0) + 1
    counts: dict[str, Decimal] = {}
    for value in values:
        count = _decimal_count(raw_counts.get(value.market_slug, 0))
        if count < repeated_gap_threshold:
            count = _ZERO
        counts[value.market_slug] = count
    return counts


def _has_base_exception(value: MarketOutcomeSourceRecheckObservation) -> bool:
    return (
        value.official_source_acknowledged_at is None
        or (value.has_source_conflict and value.source_conflict_resolved_at is None)
    )


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if (
        _MISSING_ACK_REASON in reason_codes
        or _UNRESOLVED_CONFLICT_REASON in reason_codes
    ):
        return "blocked"
    return "watch"


def _severity_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if (
        _MISSING_ACK_REASON in reason_codes
        or _UNRESOLVED_CONFLICT_REASON in reason_codes
    ):
        return "critical"
    return "warning"


def _normalize_observations(
    values: Iterable[MarketOutcomeSourceRecheckObservation],
) -> tuple[MarketOutcomeSourceRecheckObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for value in normalized:
        if type(value) is not MarketOutcomeSourceRecheckObservation:
            raise ValueError(
                "observations must contain MarketOutcomeSourceRecheckObservation values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("observation", value)
        _require_or_set_digest(value)
        key = (value.market_slug, value.condition_id, value.source_id)
        if key in seen_keys:
            raise ValueError("observations must not contain duplicate recheck keys")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    values: Iterable[MarketOutcomeSourceRecheckExceptionRow],
) -> tuple[MarketOutcomeSourceRecheckExceptionRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain MarketOutcomeSourceRecheckExceptionRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain MarketOutcomeSourceRecheckExceptionRow values",
        ) from exc
    for row in rows:
        if type(row) is not MarketOutcomeSourceRecheckExceptionRow:
            raise ValueError(
                "rows must contain MarketOutcomeSourceRecheckExceptionRow values",
            )
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic exception sort")
    if len(set(_row_identity(row) for row in rows)) != len(rows):
        raise ValueError("rows must be unique")
    return rows


def _validate_observation_sequence(
    value: MarketOutcomeSourceRecheckObservation,
) -> None:
    if _seconds_between(value.recheck_requested_at, value.source_observed_at) < _ZERO:
        raise ValueError("source_observed_at must be at or after recheck_requested_at")
    if (
        value.official_source_acknowledged_at is not None
        and _seconds_between(
            value.source_observed_at,
            value.official_source_acknowledged_at,
        )
        < _ZERO
    ):
        raise ValueError(
            "official_source_acknowledged_at must be at or after source_observed_at",
        )
    if (
        value.source_conflict_resolved_at is not None
        and _seconds_between(value.source_observed_at, value.source_conflict_resolved_at)
        < _ZERO
    ):
        raise ValueError(
            "source_conflict_resolved_at must be at or after source_observed_at",
        )


def _validate_generated_at_covers_values(
    generated_at: datetime,
    values: tuple[MarketOutcomeSourceRecheckObservation, ...],
) -> None:
    for value in values:
        if _seconds_between(_latest_stage_at(value), generated_at) < _ZERO:
            raise ValueError("generated_at must be at or after every known stage")


def _latest_stage_at(value: MarketOutcomeSourceRecheckObservation) -> datetime:
    latest = value.source_observed_at
    if (
        value.official_source_acknowledged_at is not None
        and value.official_source_acknowledged_at > latest
    ):
        latest = value.official_source_acknowledged_at
    if (
        value.source_conflict_resolved_at is not None
        and value.source_conflict_resolved_at > latest
    ):
        latest = value.source_conflict_resolved_at
    return latest


def _validate_row_consistency(row: MarketOutcomeSourceRecheckExceptionRow) -> None:
    if row.status == "watch" and row.severity != "warning":
        raise ValueError("watch rows must use warning severity")
    if row.status == "blocked" and row.severity != "critical":
        raise ValueError("blocked rows must use critical severity")
    if row.status == "pass":
        raise ValueError("exception rows must not use pass status")
    if row.status == "watch" and _STALE_SOURCE_REASON not in row.reason_codes:
        raise ValueError("watch rows must explain stale source exceptions")
    if row.status == "blocked" and not any(
        reason_code in (_MISSING_ACK_REASON, _UNRESOLVED_CONFLICT_REASON)
        for reason_code in row.reason_codes
    ):
        raise ValueError("blocked rows must explain blocking source exceptions")
    if row.acknowledgement_age_seconds is None and (
        row.recheck_to_acknowledgement_delta_seconds is not None
    ):
        raise ValueError("acknowledgement deltas require acknowledgement age")
    if row.acknowledgement_age_seconds is not None and (
        row.recheck_to_acknowledgement_delta_seconds is None
    ):
        raise ValueError("acknowledgement age requires acknowledgement delta")
    if _REPEATED_MARKET_GAP_REASON in row.reason_codes and (
        row.repeated_market_gap_count <= _ONE
    ):
        raise ValueError("repeated_market_gap requires repeated count")


def _validate_report_consistency(
    report: MarketOutcomeSourceRecheckExceptionReport,
) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.exception_count != report.row_count:
        raise ValueError("exception_count must match rows")
    if report.input_count < report.exception_count:
        raise ValueError("input_count must cover exceptions")
    if report.pass_count != _quantize(report.input_count - report.exception_count):
        raise ValueError("pass_count must match input and exception counts")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.missing_official_source_acknowledgement_count != _reason_count(
        report.rows,
        _MISSING_ACK_REASON,
    ):
        raise ValueError(
            "missing_official_source_acknowledgement_count must match rows",
        )
    if report.stale_outcome_source_count != _reason_count(
        report.rows,
        _STALE_SOURCE_REASON,
    ):
        raise ValueError("stale_outcome_source_count must match rows")
    if report.unresolved_source_conflict_count != _reason_count(
        report.rows,
        _UNRESOLVED_CONFLICT_REASON,
    ):
        raise ValueError("unresolved_source_conflict_count must match rows")
    if report.repeated_market_gap_count != _repeated_market_count(report.rows):
        raise ValueError("repeated_market_gap_count must match rows")
    if report.exception_ratio != _ratio(report.exception_count, report.input_count):
        raise ValueError("exception_ratio must match exception and input counts")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if len(set(_row_identity(row) for row in report.rows)) != len(report.rows):
        raise ValueError("rows must be unique")


def _row_sort_key(
    row: MarketOutcomeSourceRecheckExceptionRow,
) -> tuple[int, int, str, str, str]:
    return (
        _SEVERITY_RANK[row.severity],
        _STATUS_RANK[row.status],
        row.market_slug,
        row.condition_id,
        row.source_id,
    )


def _row_identity(row: MarketOutcomeSourceRecheckExceptionRow) -> tuple[str, str, str]:
    return (row.market_slug, row.condition_id, row.source_id)


def _status_count(
    rows: tuple[MarketOutcomeSourceRecheckExceptionRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[MarketOutcomeSourceRecheckExceptionRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _repeated_market_count(
    rows: tuple[MarketOutcomeSourceRecheckExceptionRow, ...],
) -> Decimal:
    return _decimal_count(
        len(
            {
                row.market_slug
                for row in rows
                if _REPEATED_MARKET_GAP_REASON in row.reason_codes
            },
        ),
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _optional_stage_delta(start: datetime, end: datetime | None) -> Decimal | None:
    if end is None:
        return None
    return _seconds_between(start, end)


def _optional_seconds_between(start: datetime | None, end: datetime) -> Decimal | None:
    if start is None:
        return None
    return _seconds_between(start, end)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    normalized = _normalize_reason_code_iterable(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes_preserving_sequence(value: Iterable[str]) -> tuple[str, ...]:
    return _normalize_reason_code_iterable(value)


def _normalize_reason_code_iterable(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_severity(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _SEVERITIES:
        raise ValueError(f"{field_name} must be info, warning, or critical")


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


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    for item in _surface_items(value):
        lowered = item.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
            raise ValueError(f"unsafe public surface in {label}: {item}")


def _surface_items(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[str] = []
        for field in fields(value):
            items.append(field.name)
            items.extend(_surface_items(getattr(value, field.name)))
        return tuple(items)
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            items.extend(_surface_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_surface_items(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_digest(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if current != expected or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _derived_digest(value: object) -> str:
    canonical = _canonical_digest_value(value)
    encoded = json.dumps(
        canonical,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _canonical_digest_value(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_digest_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != _DIGEST_FIELD
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key != _DIGEST_FIELD:
                result[key] = _canonical_digest_value(item)
        return result
    raise ValueError("unsupported digest value")


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            result[key] = _payload_value(item)
        return result
    raise ValueError("unsupported payload value")


def _require_public_payload_values(value: object) -> None:
    if value is None or type(value) in (str, bool):
        return
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_public_payload_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_public_payload_values(item)
        return
    raise ValueError("public payload contains unsupported value")


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, dict):
        if _DIGEST_FIELD in value:
            current = value[_DIGEST_FIELD]
            if type(current) is not str:
                raise ValueError("derived_validation_digest must be a string")
            expected = _derived_digest(value)
            if current != expected or not _is_sha256_hex(current):
                raise ValueError("derived_validation_digest does not match payload")
        for item in value.values():
            _validate_payload_digest_tree(item)
    elif isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)
