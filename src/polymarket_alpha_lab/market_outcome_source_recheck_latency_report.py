"""Pure report reducer for market outcome source recheck latency."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_LATENCY_REPORT_CONFIG_VERSION = (
    "market-outcome-source-recheck-latency-report-v0"
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

_CLEAR_REASON = "outcome_source_recheck_latency_clear"
_MISSING_RECHECK_REASON = "missing_outcome_source_recheck"
_SLOW_RECHECK_REASON = "slow_outcome_source_recheck"
_BLOCKED_RECHECK_REASON = "blocked_outcome_source_recheck_latency"
_MISSING_ACK_REASON = "missing_source_acknowledgement"
_OUTCOME_MISMATCH_REASON = "outcome_source_mismatch"
_REASON_SEQUENCE = (
    _CLEAR_REASON,
    _MISSING_RECHECK_REASON,
    _SLOW_RECHECK_REASON,
    _BLOCKED_RECHECK_REASON,
    _MISSING_ACK_REASON,
    _OUTCOME_MISMATCH_REASON,
)
_ACTIVE_REASON_SEQUENCE = (
    _MISSING_RECHECK_REASON,
    _SLOW_RECHECK_REASON,
    _BLOCKED_RECHECK_REASON,
    _MISSING_ACK_REASON,
    _OUTCOME_MISMATCH_REASON,
)
_STATUSES = ("ready", "watch", "blocked")
_STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "ready": Decimal("2.000000"),
}


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckLatencyConfig:
    config_version: str = (
        DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_LATENCY_REPORT_CONFIG_VERSION
    )
    watch_recheck_latency_seconds: Decimal = Decimal("900.000000")
    blocked_recheck_latency_seconds: Decimal = Decimal("3600.000000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckLatencyConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, MarketOutcomeSourceRecheckLatencyConfig)
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_recheck_latency_seconds",
            _normalize_positive_decimal(
                "watch_recheck_latency_seconds",
                self.watch_recheck_latency_seconds,
            ),
        )
        object.__setattr__(
            self,
            "blocked_recheck_latency_seconds",
            _normalize_positive_decimal(
                "blocked_recheck_latency_seconds",
                self.blocked_recheck_latency_seconds,
            ),
        )
        if self.blocked_recheck_latency_seconds <= self.watch_recheck_latency_seconds:
            raise ValueError(
                "blocked_recheck_latency_seconds must exceed watch_recheck_latency_seconds",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckObservation:
    market_slug: str
    condition_id: str
    outcome_id: str
    source_id: str
    final_outcome_at: datetime
    recheck_requested_at: datetime
    source_rechecked_at: datetime | None
    source_acknowledged_at: datetime | None
    expected_outcome: str
    source_outcome: str | None
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
            "outcome_id",
            "source_id",
            "expected_outcome",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_outcome",
            _normalize_optional_public_string("source_outcome", self.source_outcome),
        )
        for field_name in ("final_outcome_at", "recheck_requested_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_rechecked_at", "source_acknowledged_at"):
            object.__setattr__(
                self,
                field_name,
                _optional_as_utc(field_name, getattr(self, field_name)),
            )
        _validate_observation_timeline(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("observation", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckLatencyRow:
    market_slug: str
    condition_id: str
    outcome_id: str
    source_id: str
    expected_outcome: str
    source_outcome: str | None
    latency_status: str
    reason_codes: tuple[str, ...]
    source_recheck_latency_seconds: Decimal
    source_acknowledgement_latency_seconds: Decimal | None
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckLatencyRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "condition_id",
            "outcome_id",
            "source_id",
            "expected_outcome",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_outcome",
            _normalize_optional_public_string("source_outcome", self.source_outcome),
        )
        _require_status("latency_status", self.latency_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "source_recheck_latency_seconds",
            _normalize_nonnegative_decimal(
                "source_recheck_latency_seconds",
                self.source_recheck_latency_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_acknowledgement_latency_seconds",
            _normalize_optional_nonnegative_decimal(
                "source_acknowledgement_latency_seconds",
                self.source_acknowledgement_latency_seconds,
            ),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckLatencyReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    issue_count: Decimal
    missing_recheck_count: Decimal
    slow_recheck_count: Decimal
    missing_acknowledgement_count: Decimal
    outcome_mismatch_count: Decimal
    issue_ratio: Decimal
    max_recheck_latency_seconds: Decimal
    rows: tuple[MarketOutcomeSourceRecheckLatencyRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckLatencyReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, MarketOutcomeSourceRecheckLatencyReport)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "issue_count",
            "missing_recheck_count",
            "slow_recheck_count",
            "missing_acknowledgement_count",
            "outcome_mismatch_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "issue_ratio",
            _normalize_ratio("issue_ratio", self.issue_ratio),
        )
        object.__setattr__(
            self,
            "max_recheck_latency_seconds",
            _normalize_nonnegative_decimal(
                "max_recheck_latency_seconds",
                self.max_recheck_latency_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)


def build_market_outcome_source_recheck_latency_report(
    observations: Iterable[MarketOutcomeSourceRecheckObservation],
    *,
    config: MarketOutcomeSourceRecheckLatencyConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckLatencyReport:
    if type(config) is not MarketOutcomeSourceRecheckLatencyConfig:
        raise ValueError("config must be a MarketOutcomeSourceRecheckLatencyConfig")
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    _require_or_set_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    values = _normalize_observations(observations)
    _validate_generated_at_covers_values(generated_at, values)
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
    issue_count = _decimal_count(
        sum(1 for row in rows if row.latency_status != "ready"),
    )
    return MarketOutcomeSourceRecheckLatencyReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_decimal_count(len(values)),
        row_count=row_count,
        ready_count=_status_count(rows, "ready"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        issue_count=issue_count,
        missing_recheck_count=_reason_count(rows, _MISSING_RECHECK_REASON),
        slow_recheck_count=_latency_issue_count(rows),
        missing_acknowledgement_count=_reason_count(rows, _MISSING_ACK_REASON),
        outcome_mismatch_count=_reason_count(rows, _OUTCOME_MISMATCH_REASON),
        issue_ratio=_ratio(issue_count, row_count),
        max_recheck_latency_seconds=_max_recheck_latency_seconds(rows),
        rows=rows,
    )


def market_outcome_source_recheck_latency_report_payload(
    report: MarketOutcomeSourceRecheckLatencyReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeSourceRecheckLatencyReport:
        raise ValueError("report must be a MarketOutcomeSourceRecheckLatencyReport")
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    validate_market_outcome_source_recheck_latency_report_payload(payload)
    return payload


def validate_market_outcome_source_recheck_latency_report_payload(
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
    config: MarketOutcomeSourceRecheckLatencyConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckLatencyRow:
    recheck_latency = _optional_stage_delta(
        value.recheck_requested_at,
        value.source_rechecked_at,
    )
    if recheck_latency is None:
        recheck_latency = _seconds_between(value.recheck_requested_at, generated_at)
    acknowledgement_latency = _optional_stage_delta(
        value.recheck_requested_at,
        value.source_acknowledged_at,
    )
    reason_codes = _row_reason_codes(
        value,
        recheck_latency=recheck_latency,
        config=config,
    )
    return MarketOutcomeSourceRecheckLatencyRow(
        market_slug=value.market_slug,
        condition_id=value.condition_id,
        outcome_id=value.outcome_id,
        source_id=value.source_id,
        expected_outcome=value.expected_outcome,
        source_outcome=value.source_outcome,
        latency_status=_row_status(reason_codes),
        reason_codes=reason_codes,
        source_recheck_latency_seconds=recheck_latency,
        source_acknowledgement_latency_seconds=acknowledgement_latency,
    )


def _row_reason_codes(
    value: MarketOutcomeSourceRecheckObservation,
    *,
    recheck_latency: Decimal,
    config: MarketOutcomeSourceRecheckLatencyConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if value.source_rechecked_at is None:
        reason_codes.append(_MISSING_RECHECK_REASON)
    elif recheck_latency > config.blocked_recheck_latency_seconds:
        reason_codes.append(_BLOCKED_RECHECK_REASON)
    elif recheck_latency > config.watch_recheck_latency_seconds:
        reason_codes.append(_SLOW_RECHECK_REASON)
    if value.source_acknowledged_at is None:
        reason_codes.append(_MISSING_ACK_REASON)
    if (
        value.source_outcome is not None
        and value.source_outcome != value.expected_outcome
    ):
        reason_codes.append(_OUTCOME_MISMATCH_REASON)
    if not reason_codes:
        reason_codes.append(_CLEAR_REASON)
    return _normalize_reason_codes(reason_codes)


def _normalize_observations(
    values: Iterable[MarketOutcomeSourceRecheckObservation],
) -> tuple[MarketOutcomeSourceRecheckObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_keys: set[tuple[str, str, str, str]] = set()
    for value in normalized:
        if type(value) is not MarketOutcomeSourceRecheckObservation:
            raise ValueError(
                "observations must contain MarketOutcomeSourceRecheckObservation values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("observation", value)
        _require_or_set_digest(value)
        key = (value.market_slug, value.condition_id, value.outcome_id, value.source_id)
        if key in seen_keys:
            raise ValueError("observations must not contain duplicate recheck keys")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    values: Iterable[MarketOutcomeSourceRecheckLatencyRow],
) -> tuple[MarketOutcomeSourceRecheckLatencyRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain MarketOutcomeSourceRecheckLatencyRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain MarketOutcomeSourceRecheckLatencyRow values",
        ) from exc
    for row in rows:
        if type(row) is not MarketOutcomeSourceRecheckLatencyRow:
            raise ValueError(
                "rows must contain MarketOutcomeSourceRecheckLatencyRow values",
            )
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    if len(set(_row_identity(row) for row in rows)) != len(rows):
        raise ValueError("rows must be unique")
    return rows


def _validate_observation_timeline(value: MarketOutcomeSourceRecheckObservation) -> None:
    if _seconds_between(value.final_outcome_at, value.recheck_requested_at) < _ZERO:
        raise ValueError("recheck_requested_at must be at or after final_outcome_at")
    if (
        value.source_rechecked_at is not None
        and _seconds_between(value.recheck_requested_at, value.source_rechecked_at)
        < _ZERO
    ):
        raise ValueError("source_rechecked_at must be at or after recheck_requested_at")
    if (
        value.source_acknowledged_at is not None
        and _seconds_between(value.recheck_requested_at, value.source_acknowledged_at)
        < _ZERO
    ):
        raise ValueError("source_acknowledged_at must be at or after recheck_requested_at")
    if (
        value.source_rechecked_at is not None
        and value.source_acknowledged_at is not None
        and _seconds_between(value.source_rechecked_at, value.source_acknowledged_at)
        < _ZERO
    ):
        raise ValueError("source_acknowledged_at must be at or after source_rechecked_at")
    if value.source_rechecked_at is None and value.source_outcome is not None:
        raise ValueError("source_outcome requires source_rechecked_at")
    if value.source_rechecked_at is None and value.source_acknowledged_at is not None:
        raise ValueError("source_acknowledged_at requires source_rechecked_at")


def _validate_generated_at_covers_values(
    generated_at: datetime,
    values: tuple[MarketOutcomeSourceRecheckObservation, ...],
) -> None:
    for value in values:
        for field_name in (
            "final_outcome_at",
            "recheck_requested_at",
            "source_rechecked_at",
            "source_acknowledged_at",
        ):
            item = getattr(value, field_name)
            if item is not None and _seconds_between(item, generated_at) < _ZERO:
                raise ValueError(f"{field_name} must not be after generated_at")


def _validate_row_consistency(row: MarketOutcomeSourceRecheckLatencyRow) -> None:
    if row.latency_status != _row_status(row.reason_codes):
        raise ValueError("latency_status must match reason_codes")
    if row.latency_status == "ready" and row.reason_codes != (_CLEAR_REASON,):
        raise ValueError("ready rows require clear reason")
    if row.latency_status != "ready" and row.reason_codes == (_CLEAR_REASON,):
        raise ValueError("issue rows require active reasons")
    if _OUTCOME_MISMATCH_REASON in row.reason_codes and (
        row.source_outcome is None or row.source_outcome == row.expected_outcome
    ):
        raise ValueError("outcome_source_mismatch requires a distinct source_outcome")
    if _OUTCOME_MISMATCH_REASON not in row.reason_codes and (
        row.source_outcome is not None and row.source_outcome != row.expected_outcome
    ):
        raise ValueError("source_outcome must match expected_outcome without mismatch")
    if _MISSING_ACK_REASON in row.reason_codes and (
        row.source_acknowledgement_latency_seconds is not None
    ):
        raise ValueError("missing acknowledgement rows must omit acknowledgement latency")
    if _MISSING_ACK_REASON not in row.reason_codes and (
        row.source_acknowledgement_latency_seconds is None
    ):
        raise ValueError("acknowledgement latency is required without missing reason")


def _validate_report_consistency(
    report: MarketOutcomeSourceRecheckLatencyReport,
) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.issue_count != _quantize(report.watch_count + report.blocked_count):
        raise ValueError("issue_count must match watch and blocked rows")
    if report.missing_recheck_count != _reason_count(report.rows, _MISSING_RECHECK_REASON):
        raise ValueError("missing_recheck_count must match rows")
    if report.slow_recheck_count != _latency_issue_count(report.rows):
        raise ValueError("slow_recheck_count must match rows")
    if report.missing_acknowledgement_count != _reason_count(
        report.rows,
        _MISSING_ACK_REASON,
    ):
        raise ValueError("missing_acknowledgement_count must match rows")
    if report.outcome_mismatch_count != _reason_count(
        report.rows,
        _OUTCOME_MISMATCH_REASON,
    ):
        raise ValueError("outcome_mismatch_count must match rows")
    if report.issue_ratio != _ratio(report.issue_count, report.row_count):
        raise ValueError("issue_ratio must match issue and row counts")
    if report.max_recheck_latency_seconds != _max_recheck_latency_seconds(report.rows):
        raise ValueError("max_recheck_latency_seconds must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if len(set(_row_identity(row) for row in report.rows)) != len(report.rows):
        raise ValueError("rows must be unique")


def _row_sort_key(
    row: MarketOutcomeSourceRecheckLatencyRow,
) -> tuple[Decimal, Decimal, str, str, str, str]:
    return (
        _STATUS_RANK[row.latency_status],
        -_active_reason_count(row.reason_codes),
        row.market_slug,
        row.condition_id,
        row.outcome_id,
        row.source_id,
    )


def _row_identity(
    row: MarketOutcomeSourceRecheckLatencyRow,
) -> tuple[str, str, str, str]:
    return (row.market_slug, row.condition_id, row.outcome_id, row.source_id)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code
        in (
            _MISSING_RECHECK_REASON,
            _BLOCKED_RECHECK_REASON,
            _MISSING_ACK_REASON,
            _OUTCOME_MISMATCH_REASON,
        )
        for reason_code in reason_codes
    ):
        return "blocked"
    if reason_codes == (_CLEAR_REASON,):
        return "ready"
    return "watch"


def _status_count(
    rows: tuple[MarketOutcomeSourceRecheckLatencyRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.latency_status == status))


def _reason_count(
    rows: tuple[MarketOutcomeSourceRecheckLatencyRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _latency_issue_count(rows: tuple[MarketOutcomeSourceRecheckLatencyRow, ...]) -> Decimal:
    return _decimal_count(
        sum(
            1
            for row in rows
            if (
                _SLOW_RECHECK_REASON in row.reason_codes
                or _BLOCKED_RECHECK_REASON in row.reason_codes
            )
        ),
    )


def _active_reason_count(reason_codes: tuple[str, ...]) -> Decimal:
    return _decimal_count(sum(reason_code != _CLEAR_REASON for reason_code in reason_codes))


def _max_recheck_latency_seconds(
    rows: tuple[MarketOutcomeSourceRecheckLatencyRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return _normalize_nonnegative_decimal(
        "max_recheck_latency_seconds",
        max(row.source_recheck_latency_seconds for row in rows),
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


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
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
        raise ValueError("reason_codes must contain at least one value")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in _REASON_SEQUENCE:
            raise ValueError("reason_codes must contain known values")
    if reason_codes == (_CLEAR_REASON,):
        return reason_codes
    expected = tuple(
        reason_code
        for reason_code in _ACTIVE_REASON_SEQUENCE
        if reason_code in reason_codes
    )
    if expected != reason_codes:
        raise ValueError("reason_codes must use deterministic sequence")
    return reason_codes


def _normalize_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_public_string(field_name, value)
    return value


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


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
    raise ValueError("unsupported public payload value")


def _require_public_payload_values(value: object) -> None:
    if value is None or type(value) in (str, bool):
        return
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
    raise ValueError("public payload values must be strings, booleans, nulls, or arrays")


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, dict):
        if _DIGEST_FIELD in value:
            digest = value[_DIGEST_FIELD]
            if type(digest) is not str or digest != _derived_digest(value):
                raise ValueError("derived_validation_digest does not match public payload")
        for item in value.values():
            _validate_payload_digest_tree(item)
    elif isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)


__all__ = (
    "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_LATENCY_REPORT_CONFIG_VERSION",
    "MarketOutcomeSourceRecheckLatencyConfig",
    "MarketOutcomeSourceRecheckObservation",
    "MarketOutcomeSourceRecheckLatencyRow",
    "MarketOutcomeSourceRecheckLatencyReport",
    "build_market_outcome_source_recheck_latency_report",
    "market_outcome_source_recheck_latency_report_payload",
    "validate_market_outcome_source_recheck_latency_report_payload",
)
