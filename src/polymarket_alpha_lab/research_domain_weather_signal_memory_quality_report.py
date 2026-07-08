"""Pure report-only weather signal memory quality reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_DOMAIN_WEATHER_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION = (
    "research-domain-weather-signal-memory-quality-report-v0"
)

WEATHER_SIGNAL_MEMORY_QUALITY_STATUSES = ("pass", "watch", "block")

NO_INPUTS_REASON = "weather_signal_memory_quality_no_inputs"
REPORT_PASS_REASON = "weather_signal_memory_quality_report_pass"
REPORT_WATCH_REASON = "weather_signal_memory_quality_report_watch"
REPORT_BLOCK_REASON = "weather_signal_memory_quality_report_block"
CLEAR_REASON = "weather_signal_memory_quality_clear"

FORECAST_STALE_BLOCK_REASON = "forecast_memory_stale_block"
ALERT_STALE_BLOCK_REASON = "alert_memory_stale_block"
STATION_STALE_BLOCK_REASON = "station_memory_stale_block"
RESOLUTION_RULE_STALE_BLOCK_REASON = "resolution_rule_memory_stale_block"
FORECAST_CONFLICT_BLOCK_REASON = "forecast_memory_conflict_block"
ALERT_CONFLICT_BLOCK_REASON = "alert_memory_conflict_block"
STATION_CONFLICT_BLOCK_REASON = "station_memory_conflict_block"
RESOLUTION_RULE_CONFLICT_BLOCK_REASON = "resolution_rule_memory_conflict_block"
FORECAST_MISSING_BLOCK_REASON = "forecast_memory_missing_block"
ALERT_MISSING_BLOCK_REASON = "alert_memory_missing_block"
STATION_MISSING_BLOCK_REASON = "station_memory_missing_block"
RESOLUTION_RULE_MISSING_BLOCK_REASON = "resolution_rule_memory_missing_block"

FORECAST_STALE_WATCH_REASON = "forecast_memory_stale_watch"
ALERT_STALE_WATCH_REASON = "alert_memory_stale_watch"
STATION_STALE_WATCH_REASON = "station_memory_stale_watch"
RESOLUTION_RULE_STALE_WATCH_REASON = "resolution_rule_memory_stale_watch"
FORECAST_CONFLICT_WATCH_REASON = "forecast_memory_conflict_watch"
ALERT_CONFLICT_WATCH_REASON = "alert_memory_conflict_watch"
STATION_CONFLICT_WATCH_REASON = "station_memory_conflict_watch"
RESOLUTION_RULE_CONFLICT_WATCH_REASON = "resolution_rule_memory_conflict_watch"
FORECAST_MISSING_WATCH_REASON = "forecast_memory_missing_watch"
ALERT_MISSING_WATCH_REASON = "alert_memory_missing_watch"
STATION_MISSING_WATCH_REASON = "station_memory_missing_watch"
RESOLUTION_RULE_MISSING_WATCH_REASON = "resolution_rule_memory_missing_watch"

WEATHER_SIGNAL_MEMORY_QUALITY_REASON_CODES = (
    NO_INPUTS_REASON,
    REPORT_PASS_REASON,
    REPORT_WATCH_REASON,
    REPORT_BLOCK_REASON,
    CLEAR_REASON,
    FORECAST_STALE_BLOCK_REASON,
    ALERT_STALE_BLOCK_REASON,
    STATION_STALE_BLOCK_REASON,
    RESOLUTION_RULE_STALE_BLOCK_REASON,
    FORECAST_CONFLICT_BLOCK_REASON,
    ALERT_CONFLICT_BLOCK_REASON,
    STATION_CONFLICT_BLOCK_REASON,
    RESOLUTION_RULE_CONFLICT_BLOCK_REASON,
    FORECAST_MISSING_BLOCK_REASON,
    ALERT_MISSING_BLOCK_REASON,
    STATION_MISSING_BLOCK_REASON,
    RESOLUTION_RULE_MISSING_BLOCK_REASON,
    FORECAST_STALE_WATCH_REASON,
    ALERT_STALE_WATCH_REASON,
    STATION_STALE_WATCH_REASON,
    RESOLUTION_RULE_STALE_WATCH_REASON,
    FORECAST_CONFLICT_WATCH_REASON,
    ALERT_CONFLICT_WATCH_REASON,
    STATION_CONFLICT_WATCH_REASON,
    RESOLUTION_RULE_CONFLICT_WATCH_REASON,
    FORECAST_MISSING_WATCH_REASON,
    ALERT_MISSING_WATCH_REASON,
    STATION_MISSING_WATCH_REASON,
    RESOLUTION_RULE_MISSING_WATCH_REASON,
)

_REASON_RANK = {
    reason_code: index
    for index, reason_code in enumerate(WEATHER_SIGNAL_MEMORY_QUALITY_REASON_CODES)
}
_ROW_BLOCK_REASONS = (
    FORECAST_STALE_BLOCK_REASON,
    ALERT_STALE_BLOCK_REASON,
    STATION_STALE_BLOCK_REASON,
    RESOLUTION_RULE_STALE_BLOCK_REASON,
    FORECAST_CONFLICT_BLOCK_REASON,
    ALERT_CONFLICT_BLOCK_REASON,
    STATION_CONFLICT_BLOCK_REASON,
    RESOLUTION_RULE_CONFLICT_BLOCK_REASON,
    FORECAST_MISSING_BLOCK_REASON,
    ALERT_MISSING_BLOCK_REASON,
    STATION_MISSING_BLOCK_REASON,
    RESOLUTION_RULE_MISSING_BLOCK_REASON,
)
_ROW_WATCH_REASONS = (
    FORECAST_STALE_WATCH_REASON,
    ALERT_STALE_WATCH_REASON,
    STATION_STALE_WATCH_REASON,
    RESOLUTION_RULE_STALE_WATCH_REASON,
    FORECAST_CONFLICT_WATCH_REASON,
    ALERT_CONFLICT_WATCH_REASON,
    STATION_CONFLICT_WATCH_REASON,
    RESOLUTION_RULE_CONFLICT_WATCH_REASON,
    FORECAST_MISSING_WATCH_REASON,
    ALERT_MISSING_WATCH_REASON,
    STATION_MISSING_WATCH_REASON,
    RESOLUTION_RULE_MISSING_WATCH_REASON,
)
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_MEMORY_INPUT_TYPE_COUNT = Decimal("4.000000")
_LOWER = "abcdefghijklmnopqrstuvwxyz"
_DIGITS = "0123456789"
_LABEL_CHARS = frozenset(_LOWER + _DIGITS + "_.-")


def _j(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = (
    _j("candidate", "_id"),
    _j("candidate", "_slug"),
    _j("market", "_id"),
    _j("market", "_slug"),
    _j("condition", "_id"),
    _j("to", "ken", "_id"),
    "slug",
    "question",
    _j("source", "_text"),
    _j("raw", "_text"),
    _j("source", "_url"),
    _j("u", "rl"),
    "://",
    "www.",
    "dsn",
    _j("table", "_name"),
    _j("to", "ken"),
    _j("wall", "et"),
    _j("au", "th"),
    _j("ord", "er"),
    _j("tra", "de"),
    _j("li", "ve"),
    _j("net", "work"),
    _j("rec", "ommend", "ation"),
    _j("siz", "ing"),
)

__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_WEATHER_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION",
    "WEATHER_SIGNAL_MEMORY_QUALITY_STATUSES",
    "WEATHER_SIGNAL_MEMORY_QUALITY_REASON_CODES",
    "ResearchDomainWeatherSignalMemoryQualityConfig",
    "ResearchDomainWeatherSignalMemoryQualityInput",
    "ResearchDomainWeatherSignalMemoryQualityReasonCodeCount",
    "ResearchDomainWeatherSignalMemoryQualityReport",
    "ResearchDomainWeatherSignalMemoryQualityRow",
    "build_research_domain_weather_signal_memory_quality_report",
    "research_domain_weather_signal_memory_quality_report_digest",
    "research_domain_weather_signal_memory_quality_report_payload",
)


@dataclass(frozen=True)
class ResearchDomainWeatherSignalMemoryQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_WEATHER_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
    )
    watch_memory_age_seconds: Decimal = Decimal("21600.000000")
    block_memory_age_seconds: Decimal = Decimal("86400.000000")
    watch_conflict_count: Decimal = Decimal("1.000000")
    block_conflict_count: Decimal = Decimal("2.000000")
    watch_missing_count: Decimal = Decimal("1.000000")
    block_missing_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainWeatherSignalMemoryQualityConfig:
            raise TypeError(
                "ResearchDomainWeatherSignalMemoryQualityConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainWeatherSignalMemoryQualityConfig:
            raise ValueError(
                "config must be exactly ResearchDomainWeatherSignalMemoryQualityConfig",
            )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_WEATHER_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported value")
        for field_name in ("watch_memory_age_seconds", "block_memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_conflict_count",
            "block_conflict_count",
            "watch_missing_count",
            "block_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_memory_age_seconds >= self.block_memory_age_seconds:
            raise ValueError("watch_memory_age_seconds must be below block threshold")
        if self.watch_conflict_count >= self.block_conflict_count:
            raise ValueError("watch_conflict_count must be below block threshold")
        if self.watch_missing_count >= self.block_missing_count:
            raise ValueError("watch_missing_count must be below block threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainWeatherSignalMemoryQualityInput:
    weather_signal_bucket: str
    memory_scope_bucket: str
    forecast_memory_age_seconds: Decimal
    alert_memory_age_seconds: Decimal
    station_memory_age_seconds: Decimal
    resolution_rule_memory_age_seconds: Decimal
    forecast_conflict_count: Decimal
    alert_conflict_count: Decimal
    station_conflict_count: Decimal
    resolution_rule_conflict_count: Decimal
    forecast_missing_count: Decimal
    alert_missing_count: Decimal
    station_missing_count: Decimal
    resolution_rule_missing_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainWeatherSignalMemoryQualityInput:
            raise TypeError(
                "ResearchDomainWeatherSignalMemoryQualityInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainWeatherSignalMemoryQualityInput:
            raise ValueError(
                "input must be exactly ResearchDomainWeatherSignalMemoryQualityInput",
            )
        for field_name in ("weather_signal_bucket", "memory_scope_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        for field_name in _AGE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in _CONFLICT_FIELDS + _MISSING_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchDomainWeatherSignalMemoryQualityRow:
    weather_signal_bucket: str
    memory_scope_bucket: str
    observed_at: datetime
    status: str
    forecast_memory_age_seconds: Decimal
    alert_memory_age_seconds: Decimal
    station_memory_age_seconds: Decimal
    resolution_rule_memory_age_seconds: Decimal
    max_memory_age_seconds: Decimal
    forecast_conflict_count: Decimal
    alert_conflict_count: Decimal
    station_conflict_count: Decimal
    resolution_rule_conflict_count: Decimal
    total_conflict_count: Decimal
    forecast_missing_count: Decimal
    alert_missing_count: Decimal
    station_missing_count: Decimal
    resolution_rule_missing_count: Decimal
    total_missing_count: Decimal
    freshness_score: Decimal
    non_conflict_score: Decimal
    completeness_score: Decimal
    memory_quality_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainWeatherSignalMemoryQualityRow:
            raise TypeError(
                "ResearchDomainWeatherSignalMemoryQualityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainWeatherSignalMemoryQualityRow:
            raise ValueError("row must be exactly ResearchDomainWeatherSignalMemoryQualityRow")
        for field_name in ("weather_signal_bucket", "memory_scope_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        for field_name in _AGE_FIELDS + ("max_memory_age_seconds",):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            _CONFLICT_FIELDS
            + ("total_conflict_count",)
            + _MISSING_FIELDS
            + ("total_missing_count",)
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_score",
            "non_conflict_score",
            "completeness_score",
            "memory_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _validate_row_totals(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchDomainWeatherSignalMemoryQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainWeatherSignalMemoryQualityReasonCodeCount:
            raise TypeError(
                "ResearchDomainWeatherSignalMemoryQualityReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainWeatherSignalMemoryQualityReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchDomainWeatherSignalMemoryQualityReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchDomainWeatherSignalMemoryQualityReport:
    generated_at: datetime
    config_version: str
    report_status: str
    staleness_status: str
    conflict_status: str
    completeness_status: str
    forecast_handoff_status: str
    memory_input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_input_count: Decimal
    conflicting_input_count: Decimal
    missing_input_count: Decimal
    total_conflict_count: Decimal
    total_missing_count: Decimal
    max_memory_age_seconds: Decimal
    average_memory_quality_score: Decimal
    rows: tuple[ResearchDomainWeatherSignalMemoryQualityRow, ...]
    reason_code_counts: tuple[ResearchDomainWeatherSignalMemoryQualityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainWeatherSignalMemoryQualityReport:
            raise TypeError(
                "ResearchDomainWeatherSignalMemoryQualityReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainWeatherSignalMemoryQualityReport:
            raise ValueError(
                "report must be exactly ResearchDomainWeatherSignalMemoryQualityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "report_status",
            "staleness_status",
            "conflict_status",
            "completeness_status",
            "forecast_handoff_status",
        ):
            _require_status(field_name, getattr(self, field_name))
        for field_name in (
            "memory_input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_input_count",
            "conflicting_input_count",
            "missing_input_count",
            "total_conflict_count",
            "total_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_memory_age_seconds",
            _require_nonnegative_decimal(
                "max_memory_age_seconds",
                self.max_memory_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "average_memory_quality_score",
            _require_ratio_decimal(
                "average_memory_quality_score",
                self.average_memory_quality_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_domain_weather_signal_memory_quality_report_payload(self)


_AGE_FIELDS = (
    "forecast_memory_age_seconds",
    "alert_memory_age_seconds",
    "station_memory_age_seconds",
    "resolution_rule_memory_age_seconds",
)
_CONFLICT_FIELDS = (
    "forecast_conflict_count",
    "alert_conflict_count",
    "station_conflict_count",
    "resolution_rule_conflict_count",
)
_MISSING_FIELDS = (
    "forecast_missing_count",
    "alert_missing_count",
    "station_missing_count",
    "resolution_rule_missing_count",
)
_STALE_BLOCK_REASONS = (
    FORECAST_STALE_BLOCK_REASON,
    ALERT_STALE_BLOCK_REASON,
    STATION_STALE_BLOCK_REASON,
    RESOLUTION_RULE_STALE_BLOCK_REASON,
)
_STALE_WATCH_REASONS = (
    FORECAST_STALE_WATCH_REASON,
    ALERT_STALE_WATCH_REASON,
    STATION_STALE_WATCH_REASON,
    RESOLUTION_RULE_STALE_WATCH_REASON,
)
_CONFLICT_BLOCK_REASONS = (
    FORECAST_CONFLICT_BLOCK_REASON,
    ALERT_CONFLICT_BLOCK_REASON,
    STATION_CONFLICT_BLOCK_REASON,
    RESOLUTION_RULE_CONFLICT_BLOCK_REASON,
)
_CONFLICT_WATCH_REASONS = (
    FORECAST_CONFLICT_WATCH_REASON,
    ALERT_CONFLICT_WATCH_REASON,
    STATION_CONFLICT_WATCH_REASON,
    RESOLUTION_RULE_CONFLICT_WATCH_REASON,
)
_MISSING_BLOCK_REASONS = (
    FORECAST_MISSING_BLOCK_REASON,
    ALERT_MISSING_BLOCK_REASON,
    STATION_MISSING_BLOCK_REASON,
    RESOLUTION_RULE_MISSING_BLOCK_REASON,
)
_MISSING_WATCH_REASONS = (
    FORECAST_MISSING_WATCH_REASON,
    ALERT_MISSING_WATCH_REASON,
    STATION_MISSING_WATCH_REASON,
    RESOLUTION_RULE_MISSING_WATCH_REASON,
)


def build_research_domain_weather_signal_memory_quality_report(
    memory_inputs: tuple[object, ...] | list[object],
    *,
    config: ResearchDomainWeatherSignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainWeatherSignalMemoryQualityReport:
    if type(config) is not ResearchDomainWeatherSignalMemoryQualityConfig:
        raise ValueError("config must be ResearchDomainWeatherSignalMemoryQualityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(memory_inputs, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (_build_row(item, config=config) for item in inputs),
            key=lambda row: (
                _STATUS_RANK[row.status],
                row.weather_signal_bucket,
                row.memory_scope_bucket,
                row.observed_at.isoformat(),
            ),
        ),
    )
    reason_codes = _report_reason_codes(rows)
    report_status = _status_from_reason_codes(reason_codes)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": report_status,
        "staleness_status": _component_status(rows, "stale"),
        "conflict_status": _component_status(rows, "conflict"),
        "completeness_status": _component_status(rows, "missing"),
        "forecast_handoff_status": report_status,
        "memory_input_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(sum(1 for row in rows if row.status == "pass")),
        "watch_count": _decimal_count(sum(1 for row in rows if row.status == "watch")),
        "block_count": _decimal_count(sum(1 for row in rows if row.status == "block")),
        "stale_input_count": _decimal_count(
            sum(1 for row in rows if _row_has_reason_fragment(row, "stale")),
        ),
        "conflicting_input_count": _decimal_count(
            sum(1 for row in rows if _row_has_reason_fragment(row, "conflict")),
        ),
        "missing_input_count": _decimal_count(
            sum(1 for row in rows if _row_has_reason_fragment(row, "missing")),
        ),
        "total_conflict_count": sum((row.total_conflict_count for row in rows), _ZERO),
        "total_missing_count": sum((row.total_missing_count for row in rows), _ZERO),
        "max_memory_age_seconds": max(
            (row.max_memory_age_seconds for row in rows),
            default=_ZERO,
        ),
        "average_memory_quality_score": _average_decimal(
            tuple(row.memory_quality_score for row in rows),
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchDomainWeatherSignalMemoryQualityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_domain_weather_signal_memory_quality_report_payload(
    value: object,
) -> dict[str, Any]:
    if isinstance(
        value,
        (
            ResearchDomainWeatherSignalMemoryQualityConfig,
            ResearchDomainWeatherSignalMemoryQualityInput,
            ResearchDomainWeatherSignalMemoryQualityRow,
            ResearchDomainWeatherSignalMemoryQualityReasonCodeCount,
            ResearchDomainWeatherSignalMemoryQualityReport,
        ),
    ):
        _require_hard_flags("payload", value)
    elif type(value) is not dict:
        raise ValueError("value must be a weather signal memory dataclass or payload dict")
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    if "derived_validation_digest" in payload:
        _validate_payload_digest(payload)
    return payload


def research_domain_weather_signal_memory_quality_report_digest(value: object) -> str:
    payload = research_domain_weather_signal_memory_quality_report_payload(value)
    if "derived_validation_digest" not in payload:
        return _report_digest_from_values(payload)
    digest = payload["derived_validation_digest"]
    _require_sha256_digest("derived_validation_digest", digest)
    return digest


def _build_row(
    item: ResearchDomainWeatherSignalMemoryQualityInput,
    *,
    config: ResearchDomainWeatherSignalMemoryQualityConfig,
) -> ResearchDomainWeatherSignalMemoryQualityRow:
    reason_codes = _row_reason_codes(item, config)
    freshness_score = _freshness_score(item, config)
    non_conflict_score = _bounded_gap_score(
        _sum_decimals(tuple(getattr(item, field_name) for field_name in _CONFLICT_FIELDS)),
        config.block_conflict_count * _MEMORY_INPUT_TYPE_COUNT,
    )
    completeness_score = _bounded_gap_score(
        _sum_decimals(tuple(getattr(item, field_name) for field_name in _MISSING_FIELDS)),
        config.block_missing_count * _MEMORY_INPUT_TYPE_COUNT,
    )
    return ResearchDomainWeatherSignalMemoryQualityRow(
        weather_signal_bucket=item.weather_signal_bucket,
        memory_scope_bucket=item.memory_scope_bucket,
        observed_at=item.observed_at,
        status=_status_from_reason_codes(reason_codes),
        forecast_memory_age_seconds=item.forecast_memory_age_seconds,
        alert_memory_age_seconds=item.alert_memory_age_seconds,
        station_memory_age_seconds=item.station_memory_age_seconds,
        resolution_rule_memory_age_seconds=item.resolution_rule_memory_age_seconds,
        max_memory_age_seconds=max(getattr(item, field_name) for field_name in _AGE_FIELDS),
        forecast_conflict_count=item.forecast_conflict_count,
        alert_conflict_count=item.alert_conflict_count,
        station_conflict_count=item.station_conflict_count,
        resolution_rule_conflict_count=item.resolution_rule_conflict_count,
        total_conflict_count=_sum_decimals(
            tuple(getattr(item, field_name) for field_name in _CONFLICT_FIELDS),
        ),
        forecast_missing_count=item.forecast_missing_count,
        alert_missing_count=item.alert_missing_count,
        station_missing_count=item.station_missing_count,
        resolution_rule_missing_count=item.resolution_rule_missing_count,
        total_missing_count=_sum_decimals(
            tuple(getattr(item, field_name) for field_name in _MISSING_FIELDS),
        ),
        freshness_score=freshness_score,
        non_conflict_score=non_conflict_score,
        completeness_score=completeness_score,
        memory_quality_score=_average_decimal(
            (freshness_score, non_conflict_score, completeness_score),
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchDomainWeatherSignalMemoryQualityInput,
    config: ResearchDomainWeatherSignalMemoryQualityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_age_reason(
        reason_codes,
        item.forecast_memory_age_seconds,
        config,
        FORECAST_STALE_BLOCK_REASON,
        FORECAST_STALE_WATCH_REASON,
    )
    _append_age_reason(
        reason_codes,
        item.alert_memory_age_seconds,
        config,
        ALERT_STALE_BLOCK_REASON,
        ALERT_STALE_WATCH_REASON,
    )
    _append_age_reason(
        reason_codes,
        item.station_memory_age_seconds,
        config,
        STATION_STALE_BLOCK_REASON,
        STATION_STALE_WATCH_REASON,
    )
    _append_age_reason(
        reason_codes,
        item.resolution_rule_memory_age_seconds,
        config,
        RESOLUTION_RULE_STALE_BLOCK_REASON,
        RESOLUTION_RULE_STALE_WATCH_REASON,
    )
    _append_count_reason(
        reason_codes,
        item.forecast_conflict_count,
        config.watch_conflict_count,
        config.block_conflict_count,
        FORECAST_CONFLICT_BLOCK_REASON,
        FORECAST_CONFLICT_WATCH_REASON,
    )
    _append_count_reason(
        reason_codes,
        item.alert_conflict_count,
        config.watch_conflict_count,
        config.block_conflict_count,
        ALERT_CONFLICT_BLOCK_REASON,
        ALERT_CONFLICT_WATCH_REASON,
    )
    _append_count_reason(
        reason_codes,
        item.station_conflict_count,
        config.watch_conflict_count,
        config.block_conflict_count,
        STATION_CONFLICT_BLOCK_REASON,
        STATION_CONFLICT_WATCH_REASON,
    )
    _append_count_reason(
        reason_codes,
        item.resolution_rule_conflict_count,
        config.watch_conflict_count,
        config.block_conflict_count,
        RESOLUTION_RULE_CONFLICT_BLOCK_REASON,
        RESOLUTION_RULE_CONFLICT_WATCH_REASON,
    )
    _append_count_reason(
        reason_codes,
        item.forecast_missing_count,
        config.watch_missing_count,
        config.block_missing_count,
        FORECAST_MISSING_BLOCK_REASON,
        FORECAST_MISSING_WATCH_REASON,
    )
    _append_count_reason(
        reason_codes,
        item.alert_missing_count,
        config.watch_missing_count,
        config.block_missing_count,
        ALERT_MISSING_BLOCK_REASON,
        ALERT_MISSING_WATCH_REASON,
    )
    _append_count_reason(
        reason_codes,
        item.station_missing_count,
        config.watch_missing_count,
        config.block_missing_count,
        STATION_MISSING_BLOCK_REASON,
        STATION_MISSING_WATCH_REASON,
    )
    _append_count_reason(
        reason_codes,
        item.resolution_rule_missing_count,
        config.watch_missing_count,
        config.block_missing_count,
        RESOLUTION_RULE_MISSING_BLOCK_REASON,
        RESOLUTION_RULE_MISSING_WATCH_REASON,
    )
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _append_age_reason(
    reason_codes: list[str],
    value: Decimal,
    config: ResearchDomainWeatherSignalMemoryQualityConfig,
    block_reason: str,
    watch_reason: str,
) -> None:
    if value >= config.block_memory_age_seconds:
        reason_codes.append(block_reason)
    elif value >= config.watch_memory_age_seconds:
        reason_codes.append(watch_reason)


def _append_count_reason(
    reason_codes: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    block_reason: str,
    watch_reason: str,
) -> None:
    if value >= block_threshold:
        reason_codes.append(block_reason)
    elif value >= watch_threshold:
        reason_codes.append(watch_reason)


def _freshness_score(
    item: ResearchDomainWeatherSignalMemoryQualityInput,
    config: ResearchDomainWeatherSignalMemoryQualityConfig,
) -> Decimal:
    return _average_decimal(
        tuple(
            _bounded_gap_score(getattr(item, field_name), config.block_memory_age_seconds)
            for field_name in _AGE_FIELDS
        ),
    )


def _bounded_gap_score(value: Decimal, ceiling: Decimal) -> Decimal:
    if ceiling <= _ZERO:
        raise ValueError("ceiling must be positive")
    return max(_ZERO, min(_ONE, _quantize(_ONE - (value / ceiling))))


def _normalize_inputs(
    memory_inputs: tuple[object, ...] | list[object],
    *,
    generated_at: datetime,
) -> tuple[ResearchDomainWeatherSignalMemoryQualityInput, ...]:
    if type(memory_inputs) not in (list, tuple):
        raise ValueError("memory_inputs must be a list or tuple")
    normalized = tuple(memory_inputs)
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not ResearchDomainWeatherSignalMemoryQualityInput:
            raise ValueError(
                "memory_inputs must contain ResearchDomainWeatherSignalMemoryQualityInput",
            )
        _require_hard_flags("input", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (item.weather_signal_bucket, item.memory_scope_bucket)
        if key in seen:
            raise ValueError("memory_inputs must not contain duplicate aggregate keys")
        seen.add(key)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.weather_signal_bucket,
                item.memory_scope_bucket,
                item.observed_at.isoformat(),
            ),
        ),
    )


def _report_reason_codes(
    rows: tuple[ResearchDomainWeatherSignalMemoryQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    row_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    report_status = _status_from_reason_codes(row_codes or (REPORT_PASS_REASON,))
    if report_status == "block":
        return _normalize_reason_codes((REPORT_BLOCK_REASON, *row_codes))
    if report_status == "watch":
        return _normalize_reason_codes((REPORT_WATCH_REASON, *row_codes))
    return (REPORT_PASS_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchDomainWeatherSignalMemoryQualityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchDomainWeatherSignalMemoryQualityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchDomainWeatherSignalMemoryQualityReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=_ONE,
                row_ratio=_ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchDomainWeatherSignalMemoryQualityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
            row_ratio=_quantize(Decimal(counter[reason_code]) / row_count),
        )
        for reason_code in reason_codes
    )


def _component_status(
    rows: tuple[ResearchDomainWeatherSignalMemoryQualityRow, ...],
    fragment: str,
) -> str:
    if not rows:
        return "block"
    relevant = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if fragment in reason_code
    )
    return _status_from_reason_codes(relevant or (REPORT_PASS_REASON,))


def _row_has_reason_fragment(
    row: ResearchDomainWeatherSignalMemoryQualityRow,
    fragment: str,
) -> bool:
    return any(fragment in reason_code for reason_code in row.reason_codes)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code in _ROW_BLOCK_REASONS
        or reason_code in (NO_INPUTS_REASON, REPORT_BLOCK_REASON)
        for reason_code in reason_codes
    ):
        return "block"
    if any(reason_code in _ROW_WATCH_REASONS or reason_code == REPORT_WATCH_REASON for reason_code in reason_codes):
        return "watch"
    return "pass"


def _normalize_rows(
    rows: tuple[ResearchDomainWeatherSignalMemoryQualityRow, ...],
) -> tuple[ResearchDomainWeatherSignalMemoryQualityRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchDomainWeatherSignalMemoryQualityRow:
            raise ValueError("rows must contain ResearchDomainWeatherSignalMemoryQualityRow")
        _require_hard_flags("row", row)
        key = (row.weather_signal_bucket, row.memory_scope_bucket)
        if key in seen:
            raise ValueError("rows must not contain duplicate aggregate keys")
        seen.add(key)
    expected = tuple(
        sorted(
            normalized,
            key=lambda row: (
                _STATUS_RANK[row.status],
                row.weather_signal_bucket,
                row.memory_scope_bucket,
                row.observed_at.isoformat(),
            ),
        ),
    )
    if normalized != expected:
        raise ValueError("rows must be deterministic")
    return normalized


def _normalize_reason_code_counts(
    counts: tuple[ResearchDomainWeatherSignalMemoryQualityReasonCodeCount, ...],
) -> tuple[ResearchDomainWeatherSignalMemoryQualityReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(counts)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchDomainWeatherSignalMemoryQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchDomainWeatherSignalMemoryQualityReasonCodeCount",
            )
        _require_hard_flags("reason count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected = tuple(sorted(normalized, key=lambda item: _REASON_RANK[item.reason_code]))
    if normalized != expected:
        raise ValueError("reason_code_counts must be deterministic")
    return normalized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must be nonempty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    expected = tuple(
        reason_code
        for reason_code in WEATHER_SIGNAL_MEMORY_QUALITY_REASON_CODES
        if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _validate_row_totals(row: ResearchDomainWeatherSignalMemoryQualityRow) -> None:
    if row.max_memory_age_seconds != max(getattr(row, field_name) for field_name in _AGE_FIELDS):
        raise ValueError("max_memory_age_seconds must match row")
    if row.total_conflict_count != _sum_decimals(
        tuple(getattr(row, field_name) for field_name in _CONFLICT_FIELDS),
    ):
        raise ValueError("total_conflict_count must match row")
    if row.total_missing_count != _sum_decimals(
        tuple(getattr(row, field_name) for field_name in _MISSING_FIELDS),
    ):
        raise ValueError("total_missing_count must match row")
    if row.memory_quality_score != _average_decimal(
        (row.freshness_score, row.non_conflict_score, row.completeness_score),
    ):
        raise ValueError("memory_quality_score must match component scores")


def _validate_report(report: ResearchDomainWeatherSignalMemoryQualityReport) -> None:
    rows = report.rows
    if report.memory_input_count != _decimal_count(len(rows)):
        raise ValueError("memory_input_count must match rows")
    for status, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("block", "block_count"),
    ):
        if getattr(report, field_name) != _decimal_count(
            sum(1 for row in rows if row.status == status),
        ):
            raise ValueError(f"{field_name} must match rows")
    if report.stale_input_count != _decimal_count(
        sum(1 for row in rows if _row_has_reason_fragment(row, "stale")),
    ):
        raise ValueError("stale_input_count must match rows")
    if report.conflicting_input_count != _decimal_count(
        sum(1 for row in rows if _row_has_reason_fragment(row, "conflict")),
    ):
        raise ValueError("conflicting_input_count must match rows")
    if report.missing_input_count != _decimal_count(
        sum(1 for row in rows if _row_has_reason_fragment(row, "missing")),
    ):
        raise ValueError("missing_input_count must match rows")
    if report.total_conflict_count != sum((row.total_conflict_count for row in rows), _ZERO):
        raise ValueError("total_conflict_count must match rows")
    if report.total_missing_count != sum((row.total_missing_count for row in rows), _ZERO):
        raise ValueError("total_missing_count must match rows")
    if report.max_memory_age_seconds != max(
        (row.max_memory_age_seconds for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_memory_age_seconds must match rows")
    if report.average_memory_quality_score != _average_decimal(
        tuple(row.memory_quality_score for row in rows),
    ):
        raise ValueError("average_memory_quality_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.report_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("report_status must match reason_codes")
    if report.forecast_handoff_status != report.report_status:
        raise ValueError("forecast_handoff_status must match report_status")
    if report.staleness_status != _component_status(rows, "stale"):
        raise ValueError("staleness_status must match rows")
    if report.conflict_status != _component_status(rows, "conflict"):
        raise ValueError("conflict_status must match rows")
    if report.completeness_status != _component_status(rows, "missing"):
        raise ValueError("completeness_status must match rows")


def _payload_value(value: object) -> object:
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is dict:
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _validate_payload_flags(value: object, field_path: str) -> None:
    if type(value) is not dict:
        return
    for flag in ("paper_only", "report_only", "readonly"):
        if value.get(flag) is not True:
            raise ValueError(f"{field_path}.{flag} must be True")
    for key, item in value.items():
        if type(item) is dict:
            _validate_payload_flags(item, f"{field_path}.{key}")
        elif type(item) is list:
            for index, nested_item in enumerate(item):
                if type(nested_item) is dict:
                    _validate_payload_flags(nested_item, f"{field_path}.{key}.{index}")


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_public_string(key)
            _reject_unsafe_public_payload(item)
    elif type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(item)
    elif type(value) is str:
        _reject_unsafe_public_string(value)


def _reject_unsafe_public_string(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload surface")


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload["derived_validation_digest"]
    _require_sha256_digest("derived_validation_digest", digest)
    expected = _report_digest_from_values(
        {key: item for key, item in payload.items() if key != "derived_validation_digest"},
    )
    if digest != expected:
        raise ValueError("derived_validation_digest does not match report payload")


def _report_values_without_digest(
    report: ResearchDomainWeatherSignalMemoryQualityReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_EVEN)


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if any(character not in _LABEL_CHARS for character in value):
        raise ValueError(f"{field_name} must be public-safe")
    if any(fragment in value.lower() for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe")
    return value


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in WEATHER_SIGNAL_MEMORY_QUALITY_REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in WEATHER_SIGNAL_MEMORY_QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
