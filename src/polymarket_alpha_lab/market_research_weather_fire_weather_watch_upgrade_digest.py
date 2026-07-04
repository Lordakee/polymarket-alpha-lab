"""Pure report-only fire weather watch upgrade research digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_WEATHER_FIRE_WEATHER_WATCH_UPGRADE_DIGEST_CONFIG_VERSION",
    "FireWeatherWatchUpgradeDigestConfig",
    "FireWeatherWatchUpgradeDigestReport",
    "FireWeatherWatchUpgradeDigestRow",
    "FireWeatherWatchUpgradeObservation",
    "FireWeatherWatchUpgradeReasonCodeCount",
    "build_market_research_weather_fire_weather_watch_upgrade_digest",
    "market_research_weather_fire_weather_watch_upgrade_digest_payload",
)


DEFAULT_MARKET_RESEARCH_WEATHER_FIRE_WEATHER_WATCH_UPGRADE_DIGEST_CONFIG_VERSION = (
    "fire-weather-watch-upgrade-digest-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")
DECIMAL_CONTEXT = Context(prec=64)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
UPGRADE_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}
MARKET_CATEGORIES = ("disaster", "energy", "policy", "weather")


@dataclass(frozen=True)
class FireWeatherWatchUpgradeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_WEATHER_FIRE_WEATHER_WATCH_UPGRADE_DIGEST_CONFIG_VERSION
    )
    max_source_age_seconds: Decimal = Decimal("1800.000000")
    watch_upgrade_pressure_threshold: Decimal = Decimal("0.350000")
    blocked_upgrade_pressure_threshold: Decimal = Decimal("0.700000")
    fire_weather_watch_pressure_bonus: Decimal = Decimal("0.100000")
    red_flag_warning_pressure_bonus: Decimal = Decimal("0.250000")
    wind_gust_watch_threshold_mph: Decimal = Decimal("30.000000")
    relative_humidity_watch_threshold_pct: Decimal = Decimal("20.000000")
    fuel_moisture_watch_threshold_pct: Decimal = Decimal("8.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, FireWeatherWatchUpgradeDigestConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "watch_upgrade_pressure_threshold",
            "blocked_upgrade_pressure_threshold",
            "fire_weather_watch_pressure_bonus",
            "red_flag_warning_pressure_bonus",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "wind_gust_watch_threshold_mph",
            "relative_humidity_watch_threshold_pct",
            "fuel_moisture_watch_threshold_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_percent_or_measure(field_name, getattr(self, field_name)),
            )
        if self.blocked_upgrade_pressure_threshold <= self.watch_upgrade_pressure_threshold:
            raise ValueError(
                "blocked_upgrade_pressure_threshold must exceed "
                "watch_upgrade_pressure_threshold",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class FireWeatherWatchUpgradeObservation:
    event_id: str
    market_slug: str
    market_category: str
    region_id: str
    weather_zone: str
    source_reference: str
    forecast_valid_at: datetime
    source_observed_at: datetime
    fire_weather_watch_active: bool
    red_flag_warning_active: bool
    wind_gust_mph: Decimal
    relative_humidity_pct: Decimal
    fuel_moisture_pct: Decimal
    affected_probability: Decimal
    market_relevance: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, FireWeatherWatchUpgradeObservation, "observation")
        for field_name in ("event_id", "market_slug", "region_id", "weather_zone"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_market_category(self.market_category)
        _require_source_reference(self.source_reference)
        object.__setattr__(
            self,
            "forecast_valid_at",
            _as_utc("forecast_valid_at", self.forecast_valid_at),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in ("fire_weather_watch_active", "red_flag_warning_active"):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "wind_gust_mph",
            _normalize_nonnegative_decimal("wind_gust_mph", self.wind_gust_mph),
        )
        for field_name in ("relative_humidity_pct", "fuel_moisture_pct"):
            object.__setattr__(
                self,
                field_name,
                _normalize_percent_or_measure(field_name, getattr(self, field_name)),
            )
        for field_name in ("affected_probability", "market_relevance"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class FireWeatherWatchUpgradeDigestRow:
    event_id: str
    market_slug: str
    market_category: str
    region_id: str
    weather_zone: str
    redacted_source_reference: str
    forecast_valid_at: datetime
    source_observed_at: datetime
    source_age_seconds: Decimal
    fire_weather_watch_active: bool
    red_flag_warning_active: bool
    wind_gust_mph: Decimal
    relative_humidity_pct: Decimal
    fuel_moisture_pct: Decimal
    affected_probability: Decimal
    market_relevance: Decimal
    upgrade_pressure: Decimal
    upgrade_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, FireWeatherWatchUpgradeDigestRow, "row")
        for field_name in (
            "event_id",
            "market_slug",
            "region_id",
            "weather_zone",
            "redacted_source_reference",
        ):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_market_category(self.market_category)
        object.__setattr__(
            self,
            "forecast_valid_at",
            _as_utc("forecast_valid_at", self.forecast_valid_at),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        for field_name in ("fire_weather_watch_active", "red_flag_warning_active"):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "wind_gust_mph",
            _normalize_nonnegative_decimal("wind_gust_mph", self.wind_gust_mph),
        )
        for field_name in ("relative_humidity_pct", "fuel_moisture_pct"):
            object.__setattr__(
                self,
                field_name,
                _normalize_percent_or_measure(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "affected_probability",
            "market_relevance",
            "upgrade_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_upgrade_status("upgrade_status", self.upgrade_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class FireWeatherWatchUpgradeReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, FireWeatherWatchUpgradeReasonCodeCount, "reason_count")
        _require_public_identifier("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class FireWeatherWatchUpgradeDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    fire_weather_watch_count: Decimal
    red_flag_warning_count: Decimal
    max_upgrade_pressure: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[FireWeatherWatchUpgradeReasonCodeCount, ...]
    rows: tuple[FireWeatherWatchUpgradeDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, FireWeatherWatchUpgradeDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_source_count",
            "fire_weather_watch_count",
            "red_flag_warning_count",
            "max_upgrade_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_market_research_weather_fire_weather_watch_upgrade_digest(
    observations: Iterable[FireWeatherWatchUpgradeObservation],
    *,
    config: FireWeatherWatchUpgradeDigestConfig,
    generated_at: datetime,
) -> FireWeatherWatchUpgradeDigestReport:
    if type(config) is not FireWeatherWatchUpgradeDigestConfig:
        raise ValueError("config must be a FireWeatherWatchUpgradeDigestConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags(config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(value, config=config, generated_at=generated_at)
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    return FireWeatherWatchUpgradeDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, "fire_weather_source_stale"),
        fire_weather_watch_count=_bool_count(rows, "fire_weather_watch_active"),
        red_flag_warning_count=_bool_count(rows, "red_flag_warning_active"),
        max_upgrade_pressure=_max_row_decimal(rows, "upgrade_pressure"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def market_research_weather_fire_weather_watch_upgrade_digest_payload(
    report: FireWeatherWatchUpgradeDigestReport,
) -> dict[str, Any]:
    if type(report) is not FireWeatherWatchUpgradeDigestReport:
        raise ValueError("report must be a FireWeatherWatchUpgradeDigestReport")
    _require_hard_flags(report)
    value = _json_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    _require_payload_hard_flags(value)
    _reject_unsafe_payload(value)
    return value


def _row_from_observation(
    value: FireWeatherWatchUpgradeObservation,
    *,
    config: FireWeatherWatchUpgradeDigestConfig,
    generated_at: datetime,
) -> FireWeatherWatchUpgradeDigestRow:
    source_age_seconds = _seconds_between(
        generated_at,
        value.source_observed_at,
        "source_observed_at",
    )
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    upgrade_pressure = _upgrade_pressure(value, config)
    if not source_fresh or upgrade_pressure >= config.blocked_upgrade_pressure_threshold:
        status = BLOCKED_STATUS
    elif upgrade_pressure >= config.watch_upgrade_pressure_threshold:
        status = WATCH_STATUS
    else:
        status = PASS_STATUS
    return FireWeatherWatchUpgradeDigestRow(
        event_id=value.event_id,
        market_slug=value.market_slug,
        market_category=value.market_category,
        region_id=value.region_id,
        weather_zone=value.weather_zone,
        redacted_source_reference=_redact_public_reference(value.source_reference),
        forecast_valid_at=value.forecast_valid_at,
        source_observed_at=value.source_observed_at,
        source_age_seconds=source_age_seconds,
        fire_weather_watch_active=value.fire_weather_watch_active,
        red_flag_warning_active=value.red_flag_warning_active,
        wind_gust_mph=value.wind_gust_mph,
        relative_humidity_pct=value.relative_humidity_pct,
        fuel_moisture_pct=value.fuel_moisture_pct,
        affected_probability=value.affected_probability,
        market_relevance=value.market_relevance,
        upgrade_pressure=upgrade_pressure,
        upgrade_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            market_category=value.market_category,
            source_fresh=source_fresh,
            status=status,
            fire_weather_watch_active=value.fire_weather_watch_active,
            red_flag_warning_active=value.red_flag_warning_active,
            wind_gust_mph=value.wind_gust_mph,
            relative_humidity_pct=value.relative_humidity_pct,
            fuel_moisture_pct=value.fuel_moisture_pct,
            config=config,
        ),
    )


def _upgrade_pressure(
    value: FireWeatherWatchUpgradeObservation,
    config: FireWeatherWatchUpgradeDigestConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        pressure = value.affected_probability * value.market_relevance
        if value.fire_weather_watch_active:
            pressure += config.fire_weather_watch_pressure_bonus
        if value.red_flag_warning_active:
            pressure += config.red_flag_warning_pressure_bonus
    return _quantize_decimal(min(pressure, ONE))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    market_category: str,
    source_fresh: bool,
    status: str,
    fire_weather_watch_active: bool,
    red_flag_warning_active: bool,
    wind_gust_mph: Decimal,
    relative_humidity_pct: Decimal,
    fuel_moisture_pct: Decimal,
    config: FireWeatherWatchUpgradeDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    reason_codes.append(f"fire_weather_market_category_{market_category}")
    if source_fresh:
        reason_codes.append("fire_weather_source_fresh")
        if status == BLOCKED_STATUS:
            reason_codes.append("fire_weather_upgrade_pressure_blocked")
        elif status == WATCH_STATUS:
            reason_codes.append("fire_weather_upgrade_pressure_watch")
        else:
            reason_codes.append("fire_weather_upgrade_pressure_pass")
    else:
        reason_codes.append("fire_weather_source_stale")
    if fire_weather_watch_active:
        reason_codes.append("fire_weather_watch_active")
    if red_flag_warning_active:
        reason_codes.append("fire_weather_red_flag_warning_active")
    if wind_gust_mph >= config.wind_gust_watch_threshold_mph:
        reason_codes.append("fire_weather_wind_gust_threshold_met")
    if relative_humidity_pct <= config.relative_humidity_watch_threshold_pct:
        reason_codes.append("fire_weather_relative_humidity_threshold_met")
    if fuel_moisture_pct <= config.fuel_moisture_watch_threshold_pct:
        reason_codes.append("fire_weather_fuel_moisture_threshold_met")
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_observations(
    observations: Iterable[FireWeatherWatchUpgradeObservation],
) -> tuple[FireWeatherWatchUpgradeObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for value in normalized:
        if type(value) is not FireWeatherWatchUpgradeObservation:
            raise ValueError(
                "observations must contain FireWeatherWatchUpgradeObservation",
            )
        _require_hard_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[FireWeatherWatchUpgradeDigestRow],
) -> tuple[FireWeatherWatchUpgradeDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not FireWeatherWatchUpgradeDigestRow:
            raise ValueError("rows must contain FireWeatherWatchUpgradeDigestRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[FireWeatherWatchUpgradeReasonCodeCount],
) -> tuple[FireWeatherWatchUpgradeReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not FireWeatherWatchUpgradeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain FireWeatherWatchUpgradeReasonCodeCount",
            )
        _require_hard_flags(count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row_consistency(row: FireWeatherWatchUpgradeDigestRow) -> None:
    if _contains_unsafe_reference(row.redacted_source_reference):
        raise ValueError("redacted_source_reference must be redacted")
    if row.upgrade_status == BLOCKED_STATUS:
        if (
            "fire_weather_upgrade_pressure_blocked" not in row.reason_codes
            and "fire_weather_source_stale" not in row.reason_codes
        ):
            raise ValueError("upgrade_status must match reason_codes")
    elif row.upgrade_status == WATCH_STATUS:
        if "fire_weather_upgrade_pressure_watch" not in row.reason_codes:
            raise ValueError("upgrade_status must match reason_codes")
    elif "fire_weather_upgrade_pressure_pass" not in row.reason_codes:
        raise ValueError("upgrade_status must match reason_codes")


def _validate_report_consistency(report: FireWeatherWatchUpgradeDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.stale_source_count != _reason_count(
        report.rows,
        "fire_weather_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.fire_weather_watch_count != _bool_count(
        report.rows,
        "fire_weather_watch_active",
    ):
        raise ValueError("fire_weather_watch_count must match rows")
    if report.red_flag_warning_count != _bool_count(report.rows, "red_flag_warning_active"):
        raise ValueError("red_flag_warning_count must match rows")
    if report.max_upgrade_pressure != _max_row_decimal(report.rows, "upgrade_pressure"):
        raise ValueError("max_upgrade_pressure must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_reason_codes(
    rows: tuple[FireWeatherWatchUpgradeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("fire_weather_watch_upgrade_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[FireWeatherWatchUpgradeDigestRow, ...],
) -> tuple[FireWeatherWatchUpgradeReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        sorted(
            (
                FireWeatherWatchUpgradeReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                )
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _status_count(
    rows: tuple[FireWeatherWatchUpgradeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.upgrade_status == status))


def _reason_count(
    rows: tuple[FireWeatherWatchUpgradeDigestRow, ...],
    code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if code in row.reason_codes))


def _bool_count(
    rows: tuple[FireWeatherWatchUpgradeDigestRow, ...],
    field_name: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if getattr(row, field_name) is True))


def _max_row_decimal(
    rows: tuple[FireWeatherWatchUpgradeDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    return max(getattr(row, field_name) for row in rows)


def _seconds_between(later: datetime, earlier: datetime, earlier_name: str) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError(f"{earlier_name} must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_percent_or_measure(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > HUNDRED:
        raise ValueError(f"{field_name} must be between 0 and 100")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_source_reference(value: object) -> None:
    if type(value) is not str:
        raise ValueError("source_reference must be a string")
    if not value or value.strip() != value:
        raise ValueError("source_reference must be a canonical nonblank string")


def _require_market_category(value: object) -> None:
    if type(value) is not str or value not in MARKET_CATEGORIES:
        raise ValueError("market_category must be a supported category")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_upgrade_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in UPGRADE_STATUSES:
        raise ValueError(f"{field_name} must be a known upgrade status")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_payload_hard_flags(value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: FireWeatherWatchUpgradeDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.upgrade_status],
        -row.upgrade_pressure,
        -row.affected_probability,
        row.event_id,
    )


def _redact_public_reference(value: str) -> str:
    if _contains_unsafe_reference(value):
        digest = sha256(value.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"
    return value


def _contains_unsafe_reference(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in ("://", "?", "@", "="))


def _reject_unsafe_payload(value: object, path: str = "payload") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_payload(item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_payload(item, f"{path}[{index}]")
        return
    if type(value) is str and _contains_unsafe_reference(value):
        raise ValueError(f"{path} has unsafe reference")


def _json_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value
