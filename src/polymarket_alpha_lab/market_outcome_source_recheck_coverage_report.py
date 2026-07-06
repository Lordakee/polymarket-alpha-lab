"""Pure readonly Polymarket outcome source recheck coverage report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_COVERAGE_REPORT_CONFIG_VERSION = (
    "market-outcome-source-recheck-coverage-report-v0"
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

_COVERAGE_STATUSES = ("pass", "watch", "blocked")
_COVERAGE_BUCKETS = ("covered", "stale", "partial", "missing")
_STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
_BUCKET_RANK = {"missing": 0, "partial": 1, "stale": 2, "covered": 3}

_COVERED_REASON = "outcome_source_recheck_covered"
_MISSING_REASON = "missing_outcome_source_recheck"
_PARTIAL_REASON = "partial_outcome_source_recheck_coverage"
_STALE_REASON = "stale_outcome_source_recheck"
_EMPTY_REASON = "outcome_source_recheck_coverage_empty"
_COMPLETE_REASON = "outcome_source_recheck_coverage_complete"
_REPORT_GAP_REASONS = (_MISSING_REASON, _PARTIAL_REASON, _STALE_REASON)


__all__ = (
    "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_COVERAGE_REPORT_CONFIG_VERSION",
    "MarketOutcomeSourceRecheckCoverageConfig",
    "MarketOutcomeSourceRecheckCoverageObservation",
    "MarketOutcomeSourceRecheckCoverageRow",
    "MarketOutcomeSourceRecheckCoverageReport",
    "build_market_outcome_source_recheck_coverage_report",
    "market_outcome_source_recheck_coverage_report_payload",
    "validate_market_outcome_source_recheck_coverage_report_payload",
)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckCoverageConfig:
    config_version: str = (
        DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_COVERAGE_REPORT_CONFIG_VERSION
    )
    required_recheck_source_count: Decimal = Decimal("1.000000")
    stale_recheck_seconds: Decimal = Decimal("7200.000000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckCoverageConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, MarketOutcomeSourceRecheckCoverageConfig)
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_recheck_source_count",
            _normalize_count(
                "required_recheck_source_count",
                self.required_recheck_source_count,
            ),
        )
        if self.required_recheck_source_count <= _ZERO:
            raise ValueError("required_recheck_source_count must be positive")
        object.__setattr__(
            self,
            "stale_recheck_seconds",
            _normalize_nonnegative_decimal(
                "stale_recheck_seconds",
                self.stale_recheck_seconds,
            ),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckCoverageObservation:
    market_slug: str
    condition_id: str
    source_id: str
    source_kind: str
    outcome_reported_at: datetime
    latest_source_rechecked_at: datetime | None
    source_count: Decimal
    rechecked_source_count: Decimal
    reason_codes: tuple[str, ...] = ("market_outcome_requires_source_recheck",)
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckCoverageObservation does not support subclassing",
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
            "outcome_reported_at",
            _as_utc("outcome_reported_at", self.outcome_reported_at),
        )
        object.__setattr__(
            self,
            "latest_source_rechecked_at",
            _optional_as_utc(
                "latest_source_rechecked_at",
                self.latest_source_rechecked_at,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_count("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "rechecked_source_count",
            _normalize_count("rechecked_source_count", self.rechecked_source_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_observation_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("observation", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckCoverageRow:
    market_slug: str
    condition_id: str
    source_id: str
    source_kind: str
    outcome_reported_at: datetime
    latest_source_rechecked_at: datetime | None
    coverage_status: str
    coverage_bucket: str
    source_count: Decimal
    rechecked_source_count: Decimal
    missing_recheck_count: Decimal
    coverage_ratio: Decimal
    source_age_seconds: Decimal
    recheck_age_seconds: Decimal | None
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckCoverageRow does not support subclassing",
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
            "outcome_reported_at",
            _as_utc("outcome_reported_at", self.outcome_reported_at),
        )
        object.__setattr__(
            self,
            "latest_source_rechecked_at",
            _optional_as_utc(
                "latest_source_rechecked_at",
                self.latest_source_rechecked_at,
            ),
        )
        _require_status("coverage_status", self.coverage_status)
        _require_bucket("coverage_bucket", self.coverage_bucket)
        for field_name in (
            "source_count",
            "rechecked_source_count",
            "missing_recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "coverage_ratio",
            _normalize_ratio("coverage_ratio", self.coverage_ratio),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "recheck_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "recheck_age_seconds",
                self.recheck_age_seconds,
            ),
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
class MarketOutcomeSourceRecheckCoverageReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    covered_count: Decimal
    partial_count: Decimal
    missing_count: Decimal
    stale_count: Decimal
    coverage_gap_count: Decimal
    covered_ratio: Decimal
    gap_ratio: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[MarketOutcomeSourceRecheckCoverageRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckCoverageReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, MarketOutcomeSourceRecheckCoverageReport)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "covered_count",
            "partial_count",
            "missing_count",
            "stale_count",
            "coverage_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "covered_ratio",
            _normalize_ratio("covered_ratio", self.covered_ratio),
        )
        object.__setattr__(
            self,
            "gap_ratio",
            _normalize_ratio("gap_ratio", self.gap_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)


def build_market_outcome_source_recheck_coverage_report(
    observations: Iterable[MarketOutcomeSourceRecheckCoverageObservation],
    *,
    config: MarketOutcomeSourceRecheckCoverageConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckCoverageReport:
    if type(config) is not MarketOutcomeSourceRecheckCoverageConfig:
        raise ValueError("config must be a MarketOutcomeSourceRecheckCoverageConfig")
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
    input_count = _decimal_count(len(values))
    covered_count = _bucket_count(rows, "covered")
    coverage_gap_count = _quantize(input_count - covered_count)

    return MarketOutcomeSourceRecheckCoverageReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=input_count,
        row_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        covered_count=covered_count,
        partial_count=_bucket_count(rows, "partial"),
        missing_count=_bucket_count(rows, "missing"),
        stale_count=_bucket_count(rows, "stale"),
        coverage_gap_count=coverage_gap_count,
        covered_ratio=_ratio(covered_count, input_count),
        gap_ratio=_ratio(coverage_gap_count, input_count),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_outcome_source_recheck_coverage_report_payload(
    report: MarketOutcomeSourceRecheckCoverageReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeSourceRecheckCoverageReport:
        raise ValueError("report must be a MarketOutcomeSourceRecheckCoverageReport")
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    validate_market_outcome_source_recheck_coverage_report_payload(payload)
    return payload


def validate_market_outcome_source_recheck_coverage_report_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return True


def _row_from_observation(
    value: MarketOutcomeSourceRecheckCoverageObservation,
    *,
    config: MarketOutcomeSourceRecheckCoverageConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckCoverageRow:
    source_age_seconds = _seconds_between(value.outcome_reported_at, generated_at)
    recheck_age_seconds = _optional_seconds_between(
        value.latest_source_rechecked_at,
        generated_at,
    )
    coverage_ratio = _ratio(value.rechecked_source_count, value.source_count)
    missing_recheck_count = _quantize(value.source_count - value.rechecked_source_count)
    coverage_bucket = _coverage_bucket(
        value,
        config=config,
        recheck_age_seconds=recheck_age_seconds,
    )

    return MarketOutcomeSourceRecheckCoverageRow(
        market_slug=value.market_slug,
        condition_id=value.condition_id,
        source_id=value.source_id,
        source_kind=value.source_kind,
        outcome_reported_at=value.outcome_reported_at,
        latest_source_rechecked_at=value.latest_source_rechecked_at,
        coverage_status=_status_from_bucket(coverage_bucket),
        coverage_bucket=coverage_bucket,
        source_count=value.source_count,
        rechecked_source_count=value.rechecked_source_count,
        missing_recheck_count=missing_recheck_count,
        coverage_ratio=coverage_ratio,
        source_age_seconds=source_age_seconds,
        recheck_age_seconds=recheck_age_seconds,
        reason_codes=_reason_codes_from_bucket(coverage_bucket),
    )


def _coverage_bucket(
    value: MarketOutcomeSourceRecheckCoverageObservation,
    *,
    config: MarketOutcomeSourceRecheckCoverageConfig,
    recheck_age_seconds: Decimal | None,
) -> str:
    if value.rechecked_source_count == _ZERO:
        return "missing"
    if value.rechecked_source_count < value.source_count:
        return "partial"
    if recheck_age_seconds is None:
        return "missing"
    if recheck_age_seconds > config.stale_recheck_seconds:
        return "stale"
    return "covered"


def _status_from_bucket(coverage_bucket: str) -> str:
    if coverage_bucket == "missing":
        return "blocked"
    if coverage_bucket in ("partial", "stale"):
        return "watch"
    if coverage_bucket == "covered":
        return "pass"
    raise ValueError("coverage_bucket is not supported")


def _reason_codes_from_bucket(coverage_bucket: str) -> tuple[str, ...]:
    if coverage_bucket == "missing":
        return (_MISSING_REASON,)
    if coverage_bucket == "partial":
        return (_PARTIAL_REASON,)
    if coverage_bucket == "stale":
        return (_STALE_REASON,)
    if coverage_bucket == "covered":
        return (_COVERED_REASON,)
    raise ValueError("coverage_bucket is not supported")


def _report_reason_codes(
    rows: tuple[MarketOutcomeSourceRecheckCoverageRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    present = frozenset(reason_code for row in rows for reason_code in row.reason_codes)
    if present == {_COVERED_REASON}:
        return (_COMPLETE_REASON,)
    return tuple(reason_code for reason_code in _REPORT_GAP_REASONS if reason_code in present)


def _normalize_observations(
    values: Iterable[MarketOutcomeSourceRecheckCoverageObservation],
) -> tuple[MarketOutcomeSourceRecheckCoverageObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for value in normalized:
        if type(value) is not MarketOutcomeSourceRecheckCoverageObservation:
            raise ValueError(
                "observations must contain MarketOutcomeSourceRecheckCoverageObservation values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("observation", value)
        _require_or_set_digest(value)
        key = (value.market_slug, value.condition_id, value.source_id)
        if key in seen_keys:
            raise ValueError("observations must not contain duplicate coverage keys")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    values: Iterable[MarketOutcomeSourceRecheckCoverageRow],
) -> tuple[MarketOutcomeSourceRecheckCoverageRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain MarketOutcomeSourceRecheckCoverageRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain MarketOutcomeSourceRecheckCoverageRow values",
        ) from exc
    for row in rows:
        if type(row) is not MarketOutcomeSourceRecheckCoverageRow:
            raise ValueError("rows must contain MarketOutcomeSourceRecheckCoverageRow values")
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic coverage sort")
    if len(set(_row_identity(row) for row in rows)) != len(rows):
        raise ValueError("rows must be unique")
    return rows


def _validate_observation_consistency(
    value: MarketOutcomeSourceRecheckCoverageObservation,
) -> None:
    if value.source_count <= _ZERO:
        raise ValueError("source_count must be positive")
    if value.rechecked_source_count > value.source_count:
        raise ValueError("rechecked_source_count must be at most source_count")
    if (
        value.latest_source_rechecked_at is not None
        and _seconds_between(value.outcome_reported_at, value.latest_source_rechecked_at)
        < _ZERO
    ):
        raise ValueError(
            "latest_source_rechecked_at must be at or after outcome_reported_at",
        )
    if value.latest_source_rechecked_at is None and value.rechecked_source_count > _ZERO:
        raise ValueError("latest_source_rechecked_at is required for rechecked sources")


def _validate_generated_at_covers_values(
    generated_at: datetime,
    values: tuple[MarketOutcomeSourceRecheckCoverageObservation, ...],
) -> None:
    for value in values:
        latest = value.outcome_reported_at
        if (
            value.latest_source_rechecked_at is not None
            and value.latest_source_rechecked_at > latest
        ):
            latest = value.latest_source_rechecked_at
        if _seconds_between(latest, generated_at) < _ZERO:
            raise ValueError("generated_at must be at or after every known coverage stage")


def _validate_row_consistency(row: MarketOutcomeSourceRecheckCoverageRow) -> None:
    if row.source_count <= _ZERO:
        raise ValueError("source_count must be positive")
    if row.rechecked_source_count > row.source_count:
        raise ValueError("rechecked_source_count must be at most source_count")
    if row.missing_recheck_count != _quantize(
        row.source_count - row.rechecked_source_count,
    ):
        raise ValueError("missing_recheck_count must match source coverage gap")
    if row.coverage_ratio != _ratio(row.rechecked_source_count, row.source_count):
        raise ValueError("coverage_ratio must match source coverage counts")
    if row.coverage_status != _status_from_bucket(row.coverage_bucket):
        raise ValueError("coverage_status must match coverage_bucket")
    if row.reason_codes != _reason_codes_from_bucket(row.coverage_bucket):
        raise ValueError("reason_codes must match coverage_bucket")
    if row.latest_source_rechecked_at is None and row.recheck_age_seconds is not None:
        raise ValueError("recheck_age_seconds require latest_source_rechecked_at")
    if row.latest_source_rechecked_at is not None and row.recheck_age_seconds is None:
        raise ValueError("latest_source_rechecked_at requires recheck_age_seconds")
    if row.latest_source_rechecked_at is None and row.rechecked_source_count > _ZERO:
        raise ValueError("latest_source_rechecked_at is required for rechecked sources")
    if (
        row.latest_source_rechecked_at is not None
        and _seconds_between(row.outcome_reported_at, row.latest_source_rechecked_at)
        < _ZERO
    ):
        raise ValueError(
            "latest_source_rechecked_at must be at or after outcome_reported_at",
        )


def _validate_report_consistency(
    report: MarketOutcomeSourceRecheckCoverageReport,
) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.covered_count != _bucket_count(report.rows, "covered"):
        raise ValueError("covered_count must match rows")
    if report.partial_count != _bucket_count(report.rows, "partial"):
        raise ValueError("partial_count must match rows")
    if report.missing_count != _bucket_count(report.rows, "missing"):
        raise ValueError("missing_count must match rows")
    if report.stale_count != _bucket_count(report.rows, "stale"):
        raise ValueError("stale_count must match rows")
    if report.coverage_gap_count != _quantize(report.row_count - report.covered_count):
        raise ValueError("coverage_gap_count must match rows")
    if report.covered_ratio != _ratio(report.covered_count, report.input_count):
        raise ValueError("covered_ratio must match covered and input counts")
    if report.gap_ratio != _ratio(report.coverage_gap_count, report.input_count):
        raise ValueError("gap_ratio must match coverage gap and input counts")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if len(set(_row_identity(row) for row in report.rows)) != len(report.rows):
        raise ValueError("rows must be unique")


def _row_sort_key(
    row: MarketOutcomeSourceRecheckCoverageRow,
) -> tuple[int, int, str, str, str]:
    return (
        _BUCKET_RANK[row.coverage_bucket],
        _STATUS_RANK[row.coverage_status],
        row.market_slug,
        row.condition_id,
        row.source_id,
    )


def _row_identity(row: MarketOutcomeSourceRecheckCoverageRow) -> tuple[str, str, str]:
    return (row.market_slug, row.condition_id, row.source_id)


def _status_count(
    rows: tuple[MarketOutcomeSourceRecheckCoverageRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.coverage_status == status))


def _bucket_count(
    rows: tuple[MarketOutcomeSourceRecheckCoverageRow, ...],
    coverage_bucket: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.coverage_bucket == coverage_bucket))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


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
    if type(value) is not str or value not in _COVERAGE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_bucket(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _COVERAGE_BUCKETS:
        raise ValueError(f"{field_name} must be covered, stale, partial, or missing")


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
