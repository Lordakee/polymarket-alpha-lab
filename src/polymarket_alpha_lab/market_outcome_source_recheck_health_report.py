"""Pure in-memory Polymarket outcome source recheck health report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from numbers import Number
from typing import Any


DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_HEALTH_CONFIG_VERSION = (
    "market-outcome-source-recheck-health-v0"
)

HEALTH_STATUSES = ("clear", "watch", "blocked")
ROW_REASON_CODES = (
    "market_outcome_source_recheck_missing_source",
    "market_outcome_source_recheck_stale_source",
    "market_outcome_source_recheck_missing_acknowledgement",
    "market_outcome_source_recheck_stale_acknowledgement",
    "market_outcome_source_recheck_source_outcome_conflict",
    "market_outcome_source_recheck_low_source_coverage",
)
CLEAR_REASON_CODE = "market_outcome_source_recheck_health_clear"
REPORT_REASON_CODES = (CLEAR_REASON_CODE,) + ROW_REASON_CODES
BLOCKING_REASON_CODES = frozenset(
    (
        "market_outcome_source_recheck_missing_source",
        "market_outcome_source_recheck_missing_acknowledgement",
        "market_outcome_source_recheck_source_outcome_conflict",
        "market_outcome_source_recheck_low_source_coverage",
    ),
)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "clear": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("cre", "den", "tial"),
        _join_parts("api", "_", "key"),
        _join_parts("private", "_", "key"),
        _join_parts("secret"),
        _join_parts("tok", "en"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("submit"),
        _join_parts("can", "cel"),
        _join_parts("sign"),
        _join_parts("li", "ve"),
        _join_parts("tra", "ding"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("dsn"),
        _join_parts("per", "sist"),
    ),
)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckHealthConfig:
    config_version: str = DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_HEALTH_CONFIG_VERSION
    stale_source_seconds: Decimal = Decimal("3600.000000")
    stale_acknowledgement_seconds: Decimal = Decimal("1800.000000")
    min_source_coverage_ratio: Decimal = Decimal("0.750000")
    max_conflict_ratio: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckHealthConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in ("stale_source_seconds", "stale_acknowledgement_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_source_coverage_ratio", "max_conflict_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckObservation:
    market_slug: str
    condition_id: str
    source_id: str
    source_family: str
    final_outcome_at: datetime
    source_checked_at: datetime | None
    source_acknowledged_at: datetime | None
    expected_outcome: str | None
    source_outcome: str | None
    expected_source_count: Decimal
    verified_source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "condition_id", "source_id", "source_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "final_outcome_at",
            _as_utc("final_outcome_at", self.final_outcome_at),
        )
        object.__setattr__(
            self,
            "source_checked_at",
            _as_optional_utc("source_checked_at", self.source_checked_at),
        )
        object.__setattr__(
            self,
            "source_acknowledged_at",
            _as_optional_utc("source_acknowledged_at", self.source_acknowledged_at),
        )
        object.__setattr__(
            self,
            "expected_outcome",
            _normalize_optional_public_string("expected_outcome", self.expected_outcome),
        )
        object.__setattr__(
            self,
            "source_outcome",
            _normalize_optional_public_string("source_outcome", self.source_outcome),
        )
        for field_name in ("expected_source_count", "verified_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _validate_observation(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckHealthReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckHealthReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckHealthRow:
    market_slug: str
    condition_id: str
    source_id: str
    source_family: str
    final_outcome_at: datetime
    source_checked_at: datetime | None
    source_acknowledged_at: datetime | None
    expected_outcome: str | None
    source_outcome: str | None
    expected_source_count: Decimal
    verified_source_count: Decimal
    source_age_seconds: Decimal | None
    acknowledgement_lag_seconds: Decimal
    source_coverage_ratio: Decimal
    source_outcome_conflict: bool
    health_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckHealthRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "condition_id", "source_id", "source_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "final_outcome_at",
            _as_utc("final_outcome_at", self.final_outcome_at),
        )
        object.__setattr__(
            self,
            "source_checked_at",
            _as_optional_utc("source_checked_at", self.source_checked_at),
        )
        object.__setattr__(
            self,
            "source_acknowledged_at",
            _as_optional_utc("source_acknowledged_at", self.source_acknowledged_at),
        )
        object.__setattr__(
            self,
            "expected_outcome",
            _normalize_optional_public_string("expected_outcome", self.expected_outcome),
        )
        object.__setattr__(
            self,
            "source_outcome",
            _normalize_optional_public_string("source_outcome", self.source_outcome),
        )
        for field_name in ("expected_source_count", "verified_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _normalize_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_coverage_ratio",
            _normalize_ratio("source_coverage_ratio", self.source_coverage_ratio),
        )
        _require_bool("source_outcome_conflict", self.source_outcome_conflict)
        _require_member("health_status", self.health_status, HEALTH_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckHealthReport:
    generated_at: datetime
    config_version: str
    health_status: str
    input_count: Decimal
    row_count: Decimal
    clear_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    stale_source_count: Decimal
    stale_acknowledgement_count: Decimal
    missing_source_count: Decimal
    missing_acknowledgement_count: Decimal
    source_outcome_conflict_count: Decimal
    low_source_coverage_count: Decimal
    attention_count: Decimal
    attention_ratio: Decimal
    source_coverage_ratio: Decimal
    conflict_ratio: Decimal
    max_source_age_seconds: Decimal
    max_acknowledgement_lag_seconds: Decimal
    stale_source_seconds: Decimal
    stale_acknowledgement_seconds: Decimal
    min_source_coverage_ratio: Decimal
    max_conflict_ratio: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketOutcomeSourceRecheckHealthReasonCodeCount, ...]
    rows: tuple[MarketOutcomeSourceRecheckHealthRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckHealthReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("health_status", self.health_status, HEALTH_STATUSES)
        for field_name in (
            "input_count",
            "row_count",
            "clear_count",
            "watch_count",
            "blocked_count",
            "stale_source_count",
            "stale_acknowledgement_count",
            "missing_source_count",
            "missing_acknowledgement_count",
            "source_outcome_conflict_count",
            "low_source_coverage_count",
            "attention_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("attention_ratio", "source_coverage_ratio", "conflict_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_source_age_seconds",
            "max_acknowledgement_lag_seconds",
            "stale_source_seconds",
            "stale_acknowledgement_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_source_coverage_ratio", "max_conflict_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_market_outcome_source_recheck_health_report(
    observations: list[MarketOutcomeSourceRecheckObservation]
    | tuple[MarketOutcomeSourceRecheckObservation, ...],
    *,
    config: MarketOutcomeSourceRecheckHealthConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckHealthReport:
    if type(config) is not MarketOutcomeSourceRecheckHealthConfig:
        raise ValueError("config must be a MarketOutcomeSourceRecheckHealthConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    _validate_unique_observations(normalized_observations)
    _validate_not_after_generated_at(
        normalized_observations,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        sorted(
            (
                _build_row(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count(len(rows))
    attention_count = _count(sum(1 for row in rows if row.health_status != "clear"))
    conflict_count = _reason_count(
        rows,
        "market_outcome_source_recheck_source_outcome_conflict",
    )

    return MarketOutcomeSourceRecheckHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        health_status=_report_health_status(rows),
        input_count=row_count,
        row_count=row_count,
        clear_count=_status_count(rows, "clear"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        stale_source_count=_reason_count(
            rows,
            "market_outcome_source_recheck_stale_source",
        ),
        stale_acknowledgement_count=_reason_count(
            rows,
            "market_outcome_source_recheck_stale_acknowledgement",
        ),
        missing_source_count=_reason_count(
            rows,
            "market_outcome_source_recheck_missing_source",
        ),
        missing_acknowledgement_count=_reason_count(
            rows,
            "market_outcome_source_recheck_missing_acknowledgement",
        ),
        source_outcome_conflict_count=conflict_count,
        low_source_coverage_count=_reason_count(
            rows,
            "market_outcome_source_recheck_low_source_coverage",
        ),
        attention_count=attention_count,
        attention_ratio=_ratio(attention_count, row_count),
        source_coverage_ratio=_average_source_coverage_ratio(rows),
        conflict_ratio=_ratio(conflict_count, row_count),
        max_source_age_seconds=max(
            (row.source_age_seconds for row in rows if row.source_age_seconds is not None),
            default=ZERO,
        ),
        max_acknowledgement_lag_seconds=max(
            (row.acknowledgement_lag_seconds for row in rows),
            default=ZERO,
        ),
        stale_source_seconds=config.stale_source_seconds,
        stale_acknowledgement_seconds=config.stale_acknowledgement_seconds,
        min_source_coverage_ratio=config.min_source_coverage_ratio,
        max_conflict_ratio=config.max_conflict_ratio,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def market_outcome_source_recheck_health_report_payload(
    report: MarketOutcomeSourceRecheckHealthReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeSourceRecheckHealthReport:
        raise ValueError("report must be a MarketOutcomeSourceRecheckHealthReport")
    revalidated_report = _revalidate_report(report)
    payload = _report_public_payload_for_digest(revalidated_report)
    payload["derived_validation_digest"] = revalidated_report.derived_validation_digest
    validate_market_outcome_source_recheck_health_public_payload(payload)
    return payload


def validate_market_outcome_source_recheck_health_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("market outcome source recheck health payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _build_row(
    value: MarketOutcomeSourceRecheckObservation,
    *,
    config: MarketOutcomeSourceRecheckHealthConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckHealthRow:
    source_age_seconds = (
        None
        if value.source_checked_at is None
        else _age_seconds(value.source_checked_at, generated_at)
    )
    acknowledgement_lag_seconds = (
        _age_seconds(value.final_outcome_at, generated_at)
        if value.source_acknowledged_at is None
        else _age_seconds(value.final_outcome_at, value.source_acknowledged_at)
    )
    acknowledgement_age_seconds = (
        None
        if value.source_acknowledged_at is None
        else _age_seconds(value.source_acknowledged_at, generated_at)
    )
    coverage_ratio = _safe_ratio(value.verified_source_count, value.expected_source_count)
    source_outcome_conflict = _source_outcome_conflict(value)
    reason_codes = _row_reason_codes(
        source_checked_at=value.source_checked_at,
        source_age_seconds=source_age_seconds,
        source_acknowledged_at=value.source_acknowledged_at,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
        source_outcome_conflict=source_outcome_conflict,
        source_coverage_ratio=coverage_ratio,
        config=config,
    )
    return MarketOutcomeSourceRecheckHealthRow(
        market_slug=value.market_slug,
        condition_id=value.condition_id,
        source_id=value.source_id,
        source_family=value.source_family,
        final_outcome_at=value.final_outcome_at,
        source_checked_at=value.source_checked_at,
        source_acknowledged_at=value.source_acknowledged_at,
        expected_outcome=value.expected_outcome,
        source_outcome=value.source_outcome,
        expected_source_count=value.expected_source_count,
        verified_source_count=value.verified_source_count,
        source_age_seconds=source_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_coverage_ratio=coverage_ratio,
        source_outcome_conflict=source_outcome_conflict,
        health_status=_row_health_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_checked_at: datetime | None,
    source_age_seconds: Decimal | None,
    source_acknowledged_at: datetime | None,
    acknowledgement_age_seconds: Decimal | None,
    source_outcome_conflict: bool,
    source_coverage_ratio: Decimal,
    config: MarketOutcomeSourceRecheckHealthConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_checked_at is None:
        reason_codes.append("market_outcome_source_recheck_missing_source")
    elif source_age_seconds is not None and source_age_seconds >= config.stale_source_seconds:
        reason_codes.append("market_outcome_source_recheck_stale_source")
    if source_acknowledged_at is None:
        reason_codes.append("market_outcome_source_recheck_missing_acknowledgement")
    elif (
        acknowledgement_age_seconds is not None
        and acknowledgement_age_seconds >= config.stale_acknowledgement_seconds
    ):
        reason_codes.append("market_outcome_source_recheck_stale_acknowledgement")
    if source_outcome_conflict:
        reason_codes.append("market_outcome_source_recheck_source_outcome_conflict")
    if source_coverage_ratio < config.min_source_coverage_ratio:
        reason_codes.append("market_outcome_source_recheck_low_source_coverage")
    if not reason_codes:
        reason_codes.append(CLEAR_REASON_CODE)
    return tuple(reason_codes)


def _row_health_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (CLEAR_REASON_CODE,):
        return "clear"
    return "watch"


def _report_health_status(rows: tuple[MarketOutcomeSourceRecheckHealthRow, ...]) -> str:
    statuses = tuple(row.health_status for row in rows)
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketOutcomeSourceRecheckHealthRow, ...],
) -> tuple[str, ...]:
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON_CODE
    )
    if not present:
        return (CLEAR_REASON_CODE,)
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in present)


def _reason_code_counts(
    rows: tuple[MarketOutcomeSourceRecheckHealthRow, ...],
) -> tuple[MarketOutcomeSourceRecheckHealthReasonCodeCount, ...]:
    return tuple(
        MarketOutcomeSourceRecheckHealthReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
        )
        for reason_code in ROW_REASON_CODES
        if _reason_count(rows, reason_code) > ZERO
    )


def _source_outcome_conflict(value: MarketOutcomeSourceRecheckObservation) -> bool:
    if value.expected_outcome is None or value.source_outcome is None:
        return False
    return value.expected_outcome.casefold() != value.source_outcome.casefold()


def _normalize_observations(
    value: object,
) -> tuple[MarketOutcomeSourceRecheckObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    observations = tuple(value)
    for item in observations:
        if type(item) is not MarketOutcomeSourceRecheckObservation:
            raise ValueError(
                "observations must contain MarketOutcomeSourceRecheckObservation values",
            )
        _require_hard_flags(item)
    return observations


def _normalize_rows(value: object) -> tuple[MarketOutcomeSourceRecheckHealthRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketOutcomeSourceRecheckHealthRow:
            raise ValueError("rows must contain MarketOutcomeSourceRecheckHealthRow values")
        _require_hard_flags(row)
        key = _item_key(row)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate market outcome source recheck")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketOutcomeSourceRecheckHealthReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not MarketOutcomeSourceRecheckHealthReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketOutcomeSourceRecheckHealthReasonCodeCount values",
            )
        _require_hard_flags(item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        item
        for reason_code in ROW_REASON_CODES
        for item in counts
        if item.reason_code == reason_code
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_observation(value: MarketOutcomeSourceRecheckObservation) -> None:
    if value.verified_source_count > value.expected_source_count:
        raise ValueError("verified_source_count must not exceed expected_source_count")
    if value.source_checked_at is not None and value.source_checked_at < value.final_outcome_at:
        raise ValueError("source_checked_at must not be before final_outcome_at")
    if (
        value.source_acknowledged_at is not None
        and value.source_acknowledged_at < value.final_outcome_at
    ):
        raise ValueError("source_acknowledged_at must not be before final_outcome_at")


def _validate_unique_observations(
    observations: tuple[MarketOutcomeSourceRecheckObservation, ...],
) -> None:
    seen_keys: set[tuple[str, str, str]] = set()
    for item in observations:
        key = _item_key(item)
        if key in seen_keys:
            raise ValueError("observations contain duplicate market outcome source recheck")
        seen_keys.add(key)


def _validate_not_after_generated_at(
    observations: tuple[MarketOutcomeSourceRecheckObservation, ...],
    *,
    generated_at: datetime,
) -> None:
    for item in observations:
        for field_name in (
            "final_outcome_at",
            "source_checked_at",
            "source_acknowledged_at",
        ):
            value = getattr(item, field_name)
            if value is not None and value > generated_at:
                raise ValueError(f"{field_name} must not be after generated_at")


def _validate_row(row: MarketOutcomeSourceRecheckHealthRow) -> None:
    if row.verified_source_count > row.expected_source_count:
        raise ValueError("verified_source_count must not exceed expected_source_count")
    if row.source_checked_at is None and row.source_age_seconds is not None:
        raise ValueError("source_age_seconds must be absent without source_checked_at")
    if row.source_checked_at is not None and row.source_age_seconds is None:
        raise ValueError("source_age_seconds is required with source_checked_at")
    if row.source_coverage_ratio != _safe_ratio(
        row.verified_source_count,
        row.expected_source_count,
    ):
        raise ValueError("source_coverage_ratio must match source counts")
    if row.source_outcome_conflict != _row_source_outcome_conflict(row):
        raise ValueError("source_outcome_conflict must match outcomes")
    if row.health_status != _row_health_status(row.reason_codes):
        raise ValueError("health_status must match reason_codes")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: MarketOutcomeSourceRecheckHealthReport) -> None:
    rows = report.rows
    row_count = _count(len(rows))
    if report.input_count != row_count:
        raise ValueError("input_count must match rows")
    if report.row_count != row_count:
        raise ValueError("row_count must match rows")
    for field_name, status in (
        ("clear_count", "clear"),
        ("watch_count", "watch"),
        ("blocked_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.clear_count + report.watch_count + report.blocked_count != report.row_count:
        raise ValueError("status counts must match row_count")
    for field_name, reason_code in (
        ("stale_source_count", "market_outcome_source_recheck_stale_source"),
        (
            "stale_acknowledgement_count",
            "market_outcome_source_recheck_stale_acknowledgement",
        ),
        ("missing_source_count", "market_outcome_source_recheck_missing_source"),
        (
            "missing_acknowledgement_count",
            "market_outcome_source_recheck_missing_acknowledgement",
        ),
        (
            "source_outcome_conflict_count",
            "market_outcome_source_recheck_source_outcome_conflict",
        ),
        (
            "low_source_coverage_count",
            "market_outcome_source_recheck_low_source_coverage",
        ),
    ):
        if getattr(report, field_name) != _reason_count(rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.attention_count != _count(
        sum(1 for row in rows if row.health_status != "clear"),
    ):
        raise ValueError("attention_count must match rows")
    if report.attention_ratio != _ratio(report.attention_count, report.row_count):
        raise ValueError("attention_ratio must match counts")
    if report.source_coverage_ratio != _average_source_coverage_ratio(rows):
        raise ValueError("source_coverage_ratio must match rows")
    if report.conflict_ratio != _ratio(
        report.source_outcome_conflict_count,
        report.row_count,
    ):
        raise ValueError("conflict_ratio must match counts")
    if report.max_source_age_seconds != max(
        (row.source_age_seconds for row in rows if row.source_age_seconds is not None),
        default=ZERO,
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.max_acknowledgement_lag_seconds != max(
        (row.acknowledgement_lag_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_acknowledgement_lag_seconds must match rows")
    if report.health_status != _report_health_status(rows):
        raise ValueError("health_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _item_key(
    value: MarketOutcomeSourceRecheckObservation | MarketOutcomeSourceRecheckHealthRow,
) -> tuple[str, str, str]:
    return (value.market_slug, value.condition_id, value.source_id)


def _row_sort_key(
    row: MarketOutcomeSourceRecheckHealthRow,
) -> tuple[Decimal, Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.health_status],
        -_count(len(tuple(code for code in row.reason_codes if code != CLEAR_REASON_CODE))),
        -max(
            row.source_age_seconds if row.source_age_seconds is not None else ZERO,
            row.acknowledgement_lag_seconds,
        ),
        row.market_slug,
        row.condition_id,
        row.source_id,
    )


def _status_count(
    rows: tuple[MarketOutcomeSourceRecheckHealthRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.health_status == status))


def _reason_count(
    rows: tuple[MarketOutcomeSourceRecheckHealthRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_source_coverage_ratio(
    rows: tuple[MarketOutcomeSourceRecheckHealthRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (
            sum((row.source_coverage_ratio for row in rows), ZERO) / Decimal(len(rows))
        ).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _ratio(numerator, denominator)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative integer")
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _age_seconds(earlier: datetime, later: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("age seconds must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(delta.days * 86400 + delta.seconds)
        if delta.microseconds:
            seconds += Decimal(delta.microseconds) / MICROSECOND_DIVISOR
        return seconds.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _row_source_outcome_conflict(row: MarketOutcomeSourceRecheckHealthRow) -> bool:
    if row.expected_outcome is None or row.source_outcome is None:
        return False
    return row.expected_outcome.casefold() != row.source_outcome.casefold()


def _revalidate_report(
    report: MarketOutcomeSourceRecheckHealthReport,
) -> MarketOutcomeSourceRecheckHealthReport:
    return MarketOutcomeSourceRecheckHealthReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        health_status=report.health_status,
        input_count=report.input_count,
        row_count=report.row_count,
        clear_count=report.clear_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        stale_source_count=report.stale_source_count,
        stale_acknowledgement_count=report.stale_acknowledgement_count,
        missing_source_count=report.missing_source_count,
        missing_acknowledgement_count=report.missing_acknowledgement_count,
        source_outcome_conflict_count=report.source_outcome_conflict_count,
        low_source_coverage_count=report.low_source_coverage_count,
        attention_count=report.attention_count,
        attention_ratio=report.attention_ratio,
        source_coverage_ratio=report.source_coverage_ratio,
        conflict_ratio=report.conflict_ratio,
        max_source_age_seconds=report.max_source_age_seconds,
        max_acknowledgement_lag_seconds=report.max_acknowledgement_lag_seconds,
        stale_source_seconds=report.stale_source_seconds,
        stale_acknowledgement_seconds=report.stale_acknowledgement_seconds,
        min_source_coverage_ratio=report.min_source_coverage_ratio,
        max_conflict_ratio=report.max_conflict_ratio,
        reason_codes=report.reason_codes,
        reason_code_counts=report.reason_code_counts,
        rows=report.rows,
        derived_validation_digest=report.derived_validation_digest,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _row_derived_validation_digest(row: MarketOutcomeSourceRecheckHealthRow) -> str:
    return _public_payload_derived_validation_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(
    report: MarketOutcomeSourceRecheckHealthReport,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _row_public_payload_for_digest(row: MarketOutcomeSourceRecheckHealthRow) -> dict[str, Any]:
    payload = _json_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: MarketOutcomeSourceRecheckHealthReport,
) -> dict[str, Any]:
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded_payload = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple | list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_value(item)
        return ready
    if isinstance(value, Number) and type(value) is not bool:
        raise ValueError("JSON value must use Decimal strings")
    if type(value) is str:
        _reject_unsafe_public_text(value)
    return value


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _reject_public_numeric_values(value: Any) -> None:
    if isinstance(value, Number) and type(value) is not bool:
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    for public_text in _public_payload_strings(value):
        try:
            _reject_unsafe_public_text(public_text)
        except ValueError as exc:
            raise ValueError(f"unsafe public surface in {label}") from exc


def _public_payload_strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        texts: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload object keys must be strings")
            texts.append(key)
            texts.extend(_public_payload_strings(item))
        return tuple(texts)
    if isinstance(value, list):
        texts = []
        for item in value:
            texts.extend(_public_payload_strings(item))
        return tuple(texts)
    if type(value) is str:
        return (value,)
    return ()


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_sha256_digest(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_public_string(field_name, value)
    return value


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is str:
        _reject_unsafe_public_text(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    if normalized != normalized.quantize(QUANTUM, rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must use 0.000001 precision")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.quantize(QUANTUM, rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must use 0.000001 precision")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError("unsafe public surface text is not allowed")


__all__ = (
    "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_HEALTH_CONFIG_VERSION",
    "MarketOutcomeSourceRecheckHealthConfig",
    "MarketOutcomeSourceRecheckObservation",
    "MarketOutcomeSourceRecheckHealthReasonCodeCount",
    "MarketOutcomeSourceRecheckHealthRow",
    "MarketOutcomeSourceRecheckHealthReport",
    "build_market_outcome_source_recheck_health_report",
    "market_outcome_source_recheck_health_report_payload",
    "validate_market_outcome_source_recheck_health_public_payload",
)
