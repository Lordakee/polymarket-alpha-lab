"""Pure category signal quality digest reducer for Phase 1 reports."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_CATEGORY_SIGNAL_QUALITY_DIGEST_CONFIG_VERSION = (
    "market-category-signal-quality-digest-v0"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

STATUS_CLEAR = "clear"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
STATUSES = (STATUS_CLEAR, STATUS_WATCH, STATUS_BLOCKED)
STATUS_WEIGHT = {
    STATUS_BLOCKED: Decimal("2"),
    STATUS_WATCH: Decimal("1"),
    STATUS_CLEAR: Decimal("0"),
}

INPUT_REASON_CODES = ("input_signal_quality_available",)
ROW_REASON_CODES = (
    "category_forecast_dispersion_excessive",
    "category_low_source_family_diversity",
    "category_probability_momentum_unstable",
    "category_resolution_not_ready",
    "category_signal_quality_clear",
    "category_sources_stale",
)
REPORT_REASON_CODES = (
    "signal_quality_digest_blocked",
    "signal_quality_digest_clear",
    "signal_quality_digest_empty",
    "signal_quality_digest_watch",
    "signal_quality_resolution_not_ready",
    "signal_quality_sources_stale",
)
UNSAFE_VALUE_FRAGMENTS = (
    "au" "th",
    "wall" "et",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "re" "place",
    "pri" "vate" "_" "ke" "y",
    "api" "_" "ke" "y",
    "exchange" "_" "mutation",
    "live" "_" "trading",
    "live" " " "trading",
    "se" "cret",
    "to" "ken",
    "pass" "word",
    "bear" "er",
    "cre" "dential",
)

__all__ = (
    "DEFAULT_MARKET_CATEGORY_SIGNAL_QUALITY_DIGEST_CONFIG_VERSION",
    "MarketCategorySignalQualityDigestConfig",
    "MarketCategorySignalQualityInput",
    "MarketCategorySignalQualityCategoryRow",
    "MarketCategorySignalQualityReasonCodeCount",
    "MarketCategorySignalQualityDigestReport",
    "build_market_category_signal_quality_digest_report",
    "market_category_signal_quality_digest_payload",
)


@dataclass(frozen=True)
class MarketCategorySignalQualityDigestConfig:
    config_version: str = DEFAULT_MARKET_CATEGORY_SIGNAL_QUALITY_DIGEST_CONFIG_VERSION
    stale_source_age_seconds: Decimal = Decimal("86400")
    minimum_source_family_count: Decimal = Decimal("2")
    excessive_forecast_dispersion: Decimal = Decimal("0.700000")
    unstable_momentum_delta: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "stale_source_age_seconds",
            _normalize_positive_count(
                "stale_source_age_seconds",
                self.stale_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "minimum_source_family_count",
            _normalize_positive_count(
                "minimum_source_family_count",
                self.minimum_source_family_count,
            ),
        )
        object.__setattr__(
            self,
            "excessive_forecast_dispersion",
            _normalize_ratio(
                "excessive_forecast_dispersion",
                self.excessive_forecast_dispersion,
            ),
        )
        object.__setattr__(
            self,
            "unstable_momentum_delta",
            _normalize_ratio(
                "unstable_momentum_delta",
                self.unstable_momentum_delta,
            ),
        )
        require_paper_only_flags("MarketCategorySignalQualityDigestConfig", self)


@dataclass(frozen=True)
class MarketCategorySignalQualityInput:
    category_id: str
    market_id: str
    source_family: str
    source_observed_at: datetime
    forecast_low: Decimal
    forecast_high: Decimal
    probability_now: Decimal
    probability_previous: Decimal
    probability_observed_at: datetime
    resolution_ready: bool
    resolution_source_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "category_id",
            _require_canonical_string("category_id", self.category_id),
        )
        object.__setattr__(
            self,
            "market_id",
            _require_canonical_string("market_id", self.market_id),
        )
        object.__setattr__(
            self,
            "source_family",
            _require_canonical_string("source_family", self.source_family),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "forecast_low",
            _normalize_ratio("forecast_low", self.forecast_low),
        )
        object.__setattr__(
            self,
            "forecast_high",
            _normalize_ratio("forecast_high", self.forecast_high),
        )
        object.__setattr__(
            self,
            "probability_now",
            _normalize_ratio("probability_now", self.probability_now),
        )
        object.__setattr__(
            self,
            "probability_previous",
            _normalize_ratio("probability_previous", self.probability_previous),
        )
        object.__setattr__(
            self,
            "probability_observed_at",
            _as_utc("probability_observed_at", self.probability_observed_at),
        )
        if type(self.resolution_ready) is not bool:
            raise ValueError("resolution_ready must be a bool")
        object.__setattr__(
            self,
            "resolution_source_count",
            _normalize_nonnegative_count(
                "resolution_source_count",
                self.resolution_source_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                INPUT_REASON_CODES,
            ),
        )
        _validate_input(self)
        require_paper_only_flags("MarketCategorySignalQualityInput", self)


@dataclass(frozen=True)
class MarketCategorySignalQualityCategoryRow:
    category_id: str
    market_count: Decimal
    source_family_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    source_freshness_ratio: Decimal
    max_source_age_seconds: Decimal
    forecast_dispersion: Decimal
    momentum_delta_abs: Decimal
    resolution_ready_count: Decimal
    resolution_not_ready_count: Decimal
    resolution_ready_ratio: Decimal
    resolution_source_count: Decimal
    latest_source_observed_at: datetime
    latest_probability_observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "category_id",
            _require_canonical_string("category_id", self.category_id),
        )
        for field_name in (
            "market_count",
            "source_family_count",
            "fresh_source_count",
            "stale_source_count",
            "max_source_age_seconds",
            "resolution_ready_count",
            "resolution_not_ready_count",
            "resolution_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_freshness_ratio",
            "forecast_dispersion",
            "momentum_delta_abs",
            "resolution_ready_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_source_observed_at",
            _as_utc("latest_source_observed_at", self.latest_source_observed_at),
        )
        object.__setattr__(
            self,
            "latest_probability_observed_at",
            _as_utc(
                "latest_probability_observed_at",
                self.latest_probability_observed_at,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_category_row(self)
        require_paper_only_flags("MarketCategorySignalQualityCategoryRow", self)


@dataclass(frozen=True)
class MarketCategorySignalQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _require_canonical_string("reason_code", self.reason_code),
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        require_paper_only_flags("MarketCategorySignalQualityReasonCodeCount", self)


@dataclass(frozen=True)
class MarketCategorySignalQualityDigestReport:
    generated_at: datetime
    config_version: str
    category_count: Decimal
    market_count: Decimal
    clear_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketCategorySignalQualityReasonCodeCount, ...]
    category_rows: tuple[MarketCategorySignalQualityCategoryRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "category_count",
            "market_count",
            "clear_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "category_rows",
            _normalize_category_rows(self.category_rows),
        )
        _validate_report(self)
        require_paper_only_flags("MarketCategorySignalQualityDigestReport", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)
        reject_unsafe_surface_fields("market category signal quality digest", self)


def build_market_category_signal_quality_digest_report(
    inputs: list[MarketCategorySignalQualityInput]
    | tuple[MarketCategorySignalQualityInput, ...],
    *,
    config: MarketCategorySignalQualityDigestConfig,
    generated_at: datetime,
) -> MarketCategorySignalQualityDigestReport:
    if type(config) is not MarketCategorySignalQualityDigestConfig:
        raise ValueError("config must be a MarketCategorySignalQualityDigestConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    category_rows = tuple(
        sorted(
            (
                _category_row(category_id, rows, config, generated_at_utc)
                for category_id, rows in _category_groups(normalized_inputs)
            ),
            key=_category_row_sort_key,
        )
    )
    reason_codes = _report_reason_codes(category_rows)
    status = _status_rollup(tuple(row.status for row in category_rows))
    if not category_rows:
        status = STATUS_BLOCKED
    return MarketCategorySignalQualityDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        category_count=_count(len(category_rows)),
        market_count=_sum_rows(category_rows, "market_count"),
        clear_count=_status_count(category_rows, STATUS_CLEAR),
        watch_count=_status_count(category_rows, STATUS_WATCH),
        blocked_count=_status_count(category_rows, STATUS_BLOCKED),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes),
        category_rows=category_rows,
    )


def market_category_signal_quality_digest_payload(
    report: MarketCategorySignalQualityDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketCategorySignalQualityDigestReport:
        raise ValueError("report must be a MarketCategorySignalQualityDigestReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("market category signal quality digest", report)
    _validate_report_derived_validation_digest(report)
    return json_ready_no_floats(report)


def _normalize_inputs(
    inputs: list[MarketCategorySignalQualityInput]
    | tuple[MarketCategorySignalQualityInput, ...],
) -> tuple[MarketCategorySignalQualityInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_market_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketCategorySignalQualityInput:
            raise ValueError("inputs must contain MarketCategorySignalQualityInput values")
        require_paper_only_flags("input", row)
        if row.market_id in seen_market_ids:
            raise ValueError("inputs must not contain duplicate market_id values")
        seen_market_ids.add(row.market_id)
    return rows


def _category_groups(
    rows: tuple[MarketCategorySignalQualityInput, ...],
) -> tuple[tuple[str, tuple[MarketCategorySignalQualityInput, ...]], ...]:
    category_ids = tuple(sorted({row.category_id for row in rows}))
    return tuple(
        (
            category_id,
            tuple(row for row in rows if row.category_id == category_id),
        )
        for category_id in category_ids
    )


def _category_row(
    category_id: str,
    rows: tuple[MarketCategorySignalQualityInput, ...],
    config: MarketCategorySignalQualityDigestConfig,
    generated_at: datetime,
) -> MarketCategorySignalQualityCategoryRow:
    source_ages = tuple(
        _seconds_between(row.source_observed_at, generated_at)
        for row in rows
    )
    fresh_count = _count(
        sum(1 for age in source_ages if age <= config.stale_source_age_seconds)
    )
    stale_count = _count(len(source_ages)) - fresh_count
    ready_count = _count(sum(1 for row in rows if row.resolution_ready))
    not_ready_count = _count(len(rows)) - ready_count
    forecast_dispersion = _ratio(
        max(row.forecast_high for row in rows) - min(row.forecast_low for row in rows)
    )
    momentum_delta_abs = _ratio(
        max(abs(row.probability_now - row.probability_previous) for row in rows)
    )
    reason_codes = _row_reason_codes(
        source_family_count=_count(len({row.source_family for row in rows})),
        stale_count=stale_count,
        forecast_dispersion=forecast_dispersion,
        momentum_delta_abs=momentum_delta_abs,
        not_ready_count=not_ready_count,
        config=config,
    )
    return MarketCategorySignalQualityCategoryRow(
        category_id=category_id,
        market_count=_count(len(rows)),
        source_family_count=_count(len({row.source_family for row in rows})),
        fresh_source_count=fresh_count,
        stale_source_count=stale_count,
        source_freshness_ratio=_ratio(fresh_count / _count(len(rows))),
        max_source_age_seconds=_normalize_nonnegative_count(
            "max_source_age_seconds",
            max(source_ages),
        ),
        forecast_dispersion=forecast_dispersion,
        momentum_delta_abs=momentum_delta_abs,
        resolution_ready_count=ready_count,
        resolution_not_ready_count=not_ready_count,
        resolution_ready_ratio=_ratio(ready_count / _count(len(rows))),
        resolution_source_count=_sum_inputs(rows, "resolution_source_count"),
        latest_source_observed_at=max(row.source_observed_at for row in rows),
        latest_probability_observed_at=max(row.probability_observed_at for row in rows),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_family_count: Decimal,
    stale_count: Decimal,
    forecast_dispersion: Decimal,
    momentum_delta_abs: Decimal,
    not_ready_count: Decimal,
    config: MarketCategorySignalQualityDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if forecast_dispersion > config.excessive_forecast_dispersion:
        codes.append("category_forecast_dispersion_excessive")
    if (
        source_family_count < config.minimum_source_family_count
        and not_ready_count == ZERO_COUNT
    ):
        codes.append("category_low_source_family_diversity")
    if momentum_delta_abs > config.unstable_momentum_delta:
        codes.append("category_probability_momentum_unstable")
    if not_ready_count > ZERO_COUNT:
        codes.append("category_resolution_not_ready")
    if stale_count > ZERO_COUNT:
        codes.append("category_sources_stale")
    if not codes:
        codes.append("category_signal_quality_clear")
    return tuple(sorted(codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "category_forecast_dispersion_excessive" in reason_codes
        or "category_resolution_not_ready" in reason_codes
    ):
        return STATUS_BLOCKED
    if reason_codes == ("category_signal_quality_clear",):
        return STATUS_CLEAR
    return STATUS_WATCH


def _report_reason_codes(
    rows: tuple[MarketCategorySignalQualityCategoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("signal_quality_digest_empty",)
    codes: list[str] = []
    status = _status_rollup(tuple(row.status for row in rows))
    if status == STATUS_BLOCKED:
        codes.append("signal_quality_digest_blocked")
    elif status == STATUS_WATCH:
        codes.append("signal_quality_digest_watch")
    else:
        codes.append("signal_quality_digest_clear")
    if any("category_resolution_not_ready" in row.reason_codes for row in rows):
        codes.append("signal_quality_resolution_not_ready")
    if any("category_sources_stale" in row.reason_codes for row in rows):
        codes.append("signal_quality_sources_stale")
    return tuple(codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketCategorySignalQualityReasonCodeCount, ...]:
    return tuple(
        MarketCategorySignalQualityReasonCodeCount(
            reason_code=reason_code,
            count=_count(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in sorted(set(reason_codes))
    )


def _category_row_sort_key(
    row: MarketCategorySignalQualityCategoryRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.resolution_not_ready_count,
        -row.forecast_dispersion,
        -row.momentum_delta_abs,
        row.category_id,
    )


def _status_rollup(statuses: tuple[str, ...]) -> str:
    if any(status == STATUS_BLOCKED for status in statuses):
        return STATUS_BLOCKED
    if any(status == STATUS_WATCH for status in statuses):
        return STATUS_WATCH
    return STATUS_CLEAR


def _status_count(
    rows: tuple[MarketCategorySignalQualityCategoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _sum_inputs(
    rows: tuple[MarketCategorySignalQualityInput, ...],
    field_name: str,
) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _sum_rows(
    rows: tuple[MarketCategorySignalQualityCategoryRow, ...],
    field_name: str,
) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _seconds_between(start: datetime, finish: datetime) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(str((finish - start).total_seconds()))
    if seconds < ZERO_COUNT:
        return ZERO_COUNT
    return _normalize_nonnegative_count("source_age_seconds", seconds)


def _validate_input(row: MarketCategorySignalQualityInput) -> None:
    if row.forecast_low > row.forecast_high:
        raise ValueError("forecast_low must be less than or equal to forecast_high")
    if row.resolution_ready is False and row.resolution_source_count > ZERO_COUNT:
        raise ValueError("resolution_source_count must be zero when not ready")
    if row.resolution_ready is True and row.resolution_source_count == ZERO_COUNT:
        raise ValueError("resolution_source_count must be positive when ready")


def _validate_category_row(row: MarketCategorySignalQualityCategoryRow) -> None:
    if row.market_count == ZERO_COUNT:
        raise ValueError("market_count must be positive")
    if row.fresh_source_count + row.stale_source_count != row.market_count:
        raise ValueError("source freshness counts must match market_count")
    if row.resolution_ready_count + row.resolution_not_ready_count != row.market_count:
        raise ValueError("resolution counts must match market_count")
    if row.reason_codes != tuple(sorted(row.reason_codes)):
        raise ValueError("reason_codes must use stable sequence")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: MarketCategorySignalQualityDigestReport) -> None:
    if report.category_count != _count(len(report.category_rows)):
        raise ValueError("category_count must match category_rows")
    if report.market_count != _sum_rows(report.category_rows, "market_count"):
        raise ValueError("market_count must match category_rows")
    for field_name, status in (
        ("clear_count", STATUS_CLEAR),
        ("watch_count", STATUS_WATCH),
        ("blocked_count", STATUS_BLOCKED),
    ):
        if getattr(report, field_name) != _status_count(report.category_rows, status):
            raise ValueError(f"{field_name} must match category_rows")
    expected_status = STATUS_BLOCKED
    if report.category_rows:
        expected_status = _status_rollup(tuple(row.status for row in report.category_rows))
    if report.status != expected_status:
        raise ValueError("status must match category_rows")
    if report.reason_codes != _report_reason_codes(report.category_rows):
        raise ValueError("reason_codes must match category_rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.category_rows != tuple(sorted(report.category_rows, key=_category_row_sort_key)):
        raise ValueError("category_rows must use stable sequence")


def _normalize_category_rows(
    value: object,
) -> tuple[MarketCategorySignalQualityCategoryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("category_rows must be a list or tuple")
    rows = tuple(value)
    seen_category_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketCategorySignalQualityCategoryRow:
            raise ValueError("category_rows must contain category rows")
        require_paper_only_flags("category_row", row)
        if row.category_id in seen_category_ids:
            raise ValueError("category_rows must not contain duplicate category_id values")
        seen_category_ids.add(row.category_id)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketCategorySignalQualityReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not MarketCategorySignalQualityReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        require_paper_only_flags("reason_code_count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must not contain duplicate values")
        seen_reason_codes.add(count.reason_code)
    if counts != tuple(sorted(counts, key=lambda count: count.reason_code)):
        raise ValueError("reason_code_counts must use stable sequence")
    return counts


def _report_payload_without_digest(
    report: MarketCategorySignalQualityDigestReport,
) -> dict[str, Any]:
    return {
        field.name: json_ready_no_floats(getattr(report, field.name))
        for field in fields(report)
        if field.name != DERIVED_VALIDATION_DIGEST_FIELD
    }


def _report_derived_validation_digest(
    report: MarketCategorySignalQualityDigestReport,
) -> str:
    canonical_payload = json.dumps(
        _report_payload_without_digest(report),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _validate_report_derived_validation_digest(
    report: MarketCategorySignalQualityDigestReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member(field_name, code, allowed_values)
    if len(codes) != len(set(codes)):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return codes


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if _has_unsafe_value(value):
        raise ValueError(f"{field_name} has unsafe value")
    return value


def _has_unsafe_value(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_VALUE_FRAGMENTS)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(value: Decimal) -> Decimal:
    return _normalize_ratio("ratio", value)
