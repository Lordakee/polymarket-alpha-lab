"""Pure report-only convective watch upgrade research digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_WEATHER_CONVECTIVE_WATCH_UPGRADE_DIGEST_CONFIG_VERSION",
    "ConvectiveWatchUpgradeDigestConfig",
    "ConvectiveWatchUpgradeDigestRow",
    "ConvectiveWatchUpgradeObservation",
    "ConvectiveWatchUpgradeReasonCodeCount",
    "WeatherConvectiveWatchUpgradeDigestReport",
    "build_market_research_weather_convective_watch_upgrade_digest",
    "market_research_weather_convective_watch_upgrade_digest_payload",
)


DEFAULT_MARKET_RESEARCH_WEATHER_CONVECTIVE_WATCH_UPGRADE_DIGEST_CONFIG_VERSION = (
    "weather-convective-watch-upgrade-digest-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
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
WATCH_TYPES = ("severe_thunderstorm", "tornado")


@dataclass(frozen=True)
class ConvectiveWatchUpgradeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_WEATHER_CONVECTIVE_WATCH_UPGRADE_DIGEST_CONFIG_VERSION
    )
    max_source_age_seconds: Decimal = Decimal("900.000000")
    watch_upgrade_pressure_threshold: Decimal = Decimal("0.500000")
    blocked_upgrade_pressure_threshold: Decimal = Decimal("0.750000")
    source_quorum_minimum: Decimal = Decimal("2.000000")
    cape_shear_watch_threshold: Decimal = Decimal("0.600000")
    model_agreement_watch_threshold: Decimal = Decimal("0.650000")
    short_warning_lead_time_minutes: Decimal = Decimal("60.000000")
    population_exposure_watch_threshold: Decimal = Decimal("0.650000")
    airport_exposure_watch_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ConvectiveWatchUpgradeDigestConfig, "config")
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
            "cape_shear_watch_threshold",
            "model_agreement_watch_threshold",
            "population_exposure_watch_threshold",
            "airport_exposure_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_quorum_minimum",
            "short_warning_lead_time_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.blocked_upgrade_pressure_threshold <= self.watch_upgrade_pressure_threshold:
            raise ValueError(
                "blocked_upgrade_pressure_threshold must exceed "
                "watch_upgrade_pressure_threshold",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ConvectiveWatchUpgradeObservation:
    event_id: str
    market_slug: str
    market_category: str
    region_id: str
    forecast_office: str
    target_watch_type: str
    source_reference: str
    forecast_valid_at: datetime
    source_observed_at: datetime
    cape_shear_composite: Decimal
    model_agreement_score: Decimal
    warning_lead_time_minutes: Decimal
    population_exposure_score: Decimal
    airport_exposure_score: Decimal
    source_quorum_count: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ConvectiveWatchUpgradeObservation, "observation")
        for field_name in (
            "event_id",
            "market_slug",
            "region_id",
            "forecast_office",
        ):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_market_category(self.market_category)
        _require_watch_type("target_watch_type", self.target_watch_type)
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
        for field_name in (
            "cape_shear_composite",
            "model_agreement_score",
            "population_exposure_score",
            "airport_exposure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("warning_lead_time_minutes", "source_quorum_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ConvectiveWatchUpgradeDigestRow:
    event_id: str
    market_slug: str
    market_category: str
    region_id: str
    forecast_office: str
    target_watch_type: str
    redacted_source_reference: str
    forecast_valid_at: datetime
    source_observed_at: datetime
    source_age_seconds: Decimal
    cape_shear_composite: Decimal
    model_agreement_score: Decimal
    warning_lead_time_minutes: Decimal
    warning_lead_pressure: Decimal
    population_exposure_score: Decimal
    airport_exposure_score: Decimal
    source_quorum_count: Decimal
    source_quorum_score: Decimal
    risk_score: Decimal
    upgrade_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ConvectiveWatchUpgradeDigestRow, "row")
        for field_name in (
            "event_id",
            "market_slug",
            "region_id",
            "forecast_office",
            "redacted_source_reference",
        ):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_market_category(self.market_category)
        _require_watch_type("target_watch_type", self.target_watch_type)
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
        for field_name in (
            "source_age_seconds",
            "warning_lead_time_minutes",
            "source_quorum_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cape_shear_composite",
            "model_agreement_score",
            "warning_lead_pressure",
            "population_exposure_score",
            "airport_exposure_score",
            "source_quorum_score",
            "risk_score",
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
class ConvectiveWatchUpgradeReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ConvectiveWatchUpgradeReasonCodeCount, "reason_count")
        _require_public_identifier("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class WeatherConvectiveWatchUpgradeDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    source_quorum_low_count: Decimal
    tornado_watch_count: Decimal
    severe_thunderstorm_watch_count: Decimal
    max_risk_score: Decimal
    max_cape_shear_composite: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ConvectiveWatchUpgradeReasonCodeCount, ...]
    rows: tuple[ConvectiveWatchUpgradeDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, WeatherConvectiveWatchUpgradeDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_source_count",
            "source_quorum_low_count",
            "tornado_watch_count",
            "severe_thunderstorm_watch_count",
            "max_risk_score",
            "max_cape_shear_composite",
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


def build_market_research_weather_convective_watch_upgrade_digest(
    observations: Iterable[ConvectiveWatchUpgradeObservation],
    *,
    config: ConvectiveWatchUpgradeDigestConfig,
    generated_at: datetime,
) -> WeatherConvectiveWatchUpgradeDigestReport:
    if type(config) is not ConvectiveWatchUpgradeDigestConfig:
        raise ValueError("config must be a ConvectiveWatchUpgradeDigestConfig")
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
    return WeatherConvectiveWatchUpgradeDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, "convective_watch_source_stale"),
        source_quorum_low_count=_reason_count(rows, "convective_watch_source_quorum_low"),
        tornado_watch_count=_watch_type_count(rows, "tornado"),
        severe_thunderstorm_watch_count=_watch_type_count(rows, "severe_thunderstorm"),
        max_risk_score=_max_row_decimal(rows, "risk_score"),
        max_cape_shear_composite=_max_row_decimal(rows, "cape_shear_composite"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def market_research_weather_convective_watch_upgrade_digest_payload(
    report: WeatherConvectiveWatchUpgradeDigestReport,
) -> dict[str, Any]:
    if type(report) is not WeatherConvectiveWatchUpgradeDigestReport:
        raise ValueError("report must be a WeatherConvectiveWatchUpgradeDigestReport")
    _require_hard_flags(report)
    value = _json_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    _require_payload_hard_flags(value)
    _reject_unsafe_payload(value)
    return value


def _row_from_observation(
    value: ConvectiveWatchUpgradeObservation,
    *,
    config: ConvectiveWatchUpgradeDigestConfig,
    generated_at: datetime,
) -> ConvectiveWatchUpgradeDigestRow:
    source_age_seconds = _seconds_between(
        generated_at,
        value.source_observed_at,
        "source_observed_at",
    )
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    source_quorum_met = value.source_quorum_count >= config.source_quorum_minimum
    source_quorum_score = _source_quorum_score(
        value.source_quorum_count,
        config.source_quorum_minimum,
    )
    warning_lead_pressure = _warning_lead_pressure(
        value.warning_lead_time_minutes,
        config.short_warning_lead_time_minutes,
    )
    risk_score = _risk_score(
        cape_shear_composite=value.cape_shear_composite,
        model_agreement_score=value.model_agreement_score,
        warning_lead_pressure=warning_lead_pressure,
        population_exposure_score=value.population_exposure_score,
        airport_exposure_score=value.airport_exposure_score,
        source_quorum_score=source_quorum_score,
    )
    if (
        not source_fresh
        or not source_quorum_met
        or risk_score >= config.blocked_upgrade_pressure_threshold
    ):
        status = BLOCKED_STATUS
    elif risk_score >= config.watch_upgrade_pressure_threshold:
        status = WATCH_STATUS
    else:
        status = PASS_STATUS
    return ConvectiveWatchUpgradeDigestRow(
        event_id=value.event_id,
        market_slug=value.market_slug,
        market_category=value.market_category,
        region_id=value.region_id,
        forecast_office=value.forecast_office,
        target_watch_type=value.target_watch_type,
        redacted_source_reference=_redact_public_reference(value.source_reference),
        forecast_valid_at=value.forecast_valid_at,
        source_observed_at=value.source_observed_at,
        source_age_seconds=source_age_seconds,
        cape_shear_composite=value.cape_shear_composite,
        model_agreement_score=value.model_agreement_score,
        warning_lead_time_minutes=value.warning_lead_time_minutes,
        warning_lead_pressure=warning_lead_pressure,
        population_exposure_score=value.population_exposure_score,
        airport_exposure_score=value.airport_exposure_score,
        source_quorum_count=value.source_quorum_count,
        source_quorum_score=source_quorum_score,
        risk_score=risk_score,
        upgrade_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            market_category=value.market_category,
            forecast_office=value.forecast_office,
            target_watch_type=value.target_watch_type,
            source_fresh=source_fresh,
            source_quorum_met=source_quorum_met,
            status=status,
            cape_shear_composite=value.cape_shear_composite,
            model_agreement_score=value.model_agreement_score,
            warning_lead_time_minutes=value.warning_lead_time_minutes,
            population_exposure_score=value.population_exposure_score,
            airport_exposure_score=value.airport_exposure_score,
            config=config,
        ),
    )


def _risk_score(
    *,
    cape_shear_composite: Decimal,
    model_agreement_score: Decimal,
    warning_lead_pressure: Decimal,
    population_exposure_score: Decimal,
    airport_exposure_score: Decimal,
    source_quorum_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            min(
                cape_shear_composite * Decimal("0.300000")
                + model_agreement_score * Decimal("0.200000")
                + warning_lead_pressure * Decimal("0.150000")
                + population_exposure_score * Decimal("0.150000")
                + airport_exposure_score * Decimal("0.100000")
                + source_quorum_score * Decimal("0.100000"),
                ONE,
            ),
        )


def _warning_lead_pressure(
    warning_lead_time_minutes: Decimal,
    short_warning_lead_time_minutes: Decimal,
) -> Decimal:
    if warning_lead_time_minutes >= short_warning_lead_time_minutes:
        return _quantize_decimal(ZERO)
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "warning_lead_pressure",
            (short_warning_lead_time_minutes - warning_lead_time_minutes)
            / short_warning_lead_time_minutes,
        )


def _source_quorum_score(
    source_quorum_count: Decimal,
    source_quorum_minimum: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "source_quorum_score",
            min(source_quorum_count / source_quorum_minimum, ONE),
        )


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    market_category: str,
    forecast_office: str,
    target_watch_type: str,
    source_fresh: bool,
    source_quorum_met: bool,
    status: str,
    cape_shear_composite: Decimal,
    model_agreement_score: Decimal,
    warning_lead_time_minutes: Decimal,
    population_exposure_score: Decimal,
    airport_exposure_score: Decimal,
    config: ConvectiveWatchUpgradeDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    reason_codes.append(f"convective_watch_market_category_{market_category}")
    reason_codes.append(f"convective_watch_forecast_office_{forecast_office.lower()}")
    reason_codes.append(f"convective_watch_type_{target_watch_type}")
    reason_codes.append(
        "convective_watch_source_fresh"
        if source_fresh
        else "convective_watch_source_stale",
    )
    reason_codes.append(
        "convective_watch_source_quorum_met"
        if source_quorum_met
        else "convective_watch_source_quorum_low",
    )
    if source_fresh and source_quorum_met:
        if status == BLOCKED_STATUS:
            reason_codes.append("convective_watch_upgrade_pressure_blocked")
        elif status == WATCH_STATUS:
            reason_codes.append("convective_watch_upgrade_pressure_watch")
        else:
            reason_codes.append("convective_watch_upgrade_pressure_pass")
    if cape_shear_composite >= config.cape_shear_watch_threshold:
        reason_codes.append("convective_watch_cape_shear_threshold_met")
    if model_agreement_score >= config.model_agreement_watch_threshold:
        reason_codes.append("convective_watch_model_agreement")
    if warning_lead_time_minutes < config.short_warning_lead_time_minutes:
        reason_codes.append("convective_watch_short_warning_lead_time")
    if population_exposure_score >= config.population_exposure_watch_threshold:
        reason_codes.append("convective_watch_population_exposure")
    if airport_exposure_score >= config.airport_exposure_watch_threshold:
        reason_codes.append("convective_watch_airport_exposure")
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_observations(
    observations: Iterable[ConvectiveWatchUpgradeObservation],
) -> tuple[ConvectiveWatchUpgradeObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for value in normalized:
        if type(value) is not ConvectiveWatchUpgradeObservation:
            raise ValueError(
                "observations must contain ConvectiveWatchUpgradeObservation",
            )
        _require_hard_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[ConvectiveWatchUpgradeDigestRow],
) -> tuple[ConvectiveWatchUpgradeDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ConvectiveWatchUpgradeDigestRow:
            raise ValueError("rows must contain ConvectiveWatchUpgradeDigestRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ConvectiveWatchUpgradeReasonCodeCount],
) -> tuple[ConvectiveWatchUpgradeReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ConvectiveWatchUpgradeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ConvectiveWatchUpgradeReasonCodeCount",
            )
        _require_hard_flags(count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row_consistency(row: ConvectiveWatchUpgradeDigestRow) -> None:
    if _contains_unsafe_reference(row.redacted_source_reference):
        raise ValueError("redacted_source_reference must be redacted")
    if row.upgrade_status == BLOCKED_STATUS:
        if (
            "convective_watch_upgrade_pressure_blocked" not in row.reason_codes
            and "convective_watch_source_stale" not in row.reason_codes
            and "convective_watch_source_quorum_low" not in row.reason_codes
        ):
            raise ValueError("upgrade_status must match reason_codes")
    elif row.upgrade_status == WATCH_STATUS:
        if "convective_watch_upgrade_pressure_watch" not in row.reason_codes:
            raise ValueError("upgrade_status must match reason_codes")
    elif "convective_watch_upgrade_pressure_pass" not in row.reason_codes:
        raise ValueError("upgrade_status must match reason_codes")


def _validate_report_consistency(report: WeatherConvectiveWatchUpgradeDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.stale_source_count != _reason_count(
        report.rows,
        "convective_watch_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.source_quorum_low_count != _reason_count(
        report.rows,
        "convective_watch_source_quorum_low",
    ):
        raise ValueError("source_quorum_low_count must match rows")
    if report.tornado_watch_count != _watch_type_count(report.rows, "tornado"):
        raise ValueError("tornado_watch_count must match rows")
    if report.severe_thunderstorm_watch_count != _watch_type_count(
        report.rows,
        "severe_thunderstorm",
    ):
        raise ValueError("severe_thunderstorm_watch_count must match rows")
    if report.max_risk_score != _max_row_decimal(report.rows, "risk_score"):
        raise ValueError("max_risk_score must match rows")
    if report.max_cape_shear_composite != _max_row_decimal(
        report.rows,
        "cape_shear_composite",
    ):
        raise ValueError("max_cape_shear_composite must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_reason_codes(
    rows: tuple[ConvectiveWatchUpgradeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("convective_watch_upgrade_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ConvectiveWatchUpgradeDigestRow, ...],
) -> tuple[ConvectiveWatchUpgradeReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        sorted(
            (
                ConvectiveWatchUpgradeReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                )
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _status_count(
    rows: tuple[ConvectiveWatchUpgradeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.upgrade_status == status))


def _reason_count(
    rows: tuple[ConvectiveWatchUpgradeDigestRow, ...],
    code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if code in row.reason_codes))


def _watch_type_count(
    rows: tuple[ConvectiveWatchUpgradeDigestRow, ...],
    target_watch_type: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.target_watch_type == target_watch_type))


def _max_row_decimal(
    rows: tuple[ConvectiveWatchUpgradeDigestRow, ...],
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


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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


def _require_watch_type(field_name: str, value: object) -> None:
    if type(value) is not str or value not in WATCH_TYPES:
        raise ValueError(f"{field_name} must be a supported convective watch type")


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
    row: ConvectiveWatchUpgradeDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.upgrade_status],
        -row.risk_score,
        -row.cape_shear_composite,
        row.event_id,
        row.market_slug,
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
