"""Pure Phase 1 winter storm warning upgrade research digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_RESEARCH_WEATHER_WINTER_STORM_WARNING_UPGRADE_DIGEST_CONFIG_VERSION = (
    "market-research-weather-winter-storm-warning-upgrade-digest-v0"
)

SOURCE_FRESH = "fresh"
SOURCE_STALE = "stale"

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
UPGRADE_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
SOURCE_STATUSES = (SOURCE_FRESH, SOURCE_STALE)

SOURCE_FRESH_REASON = "weather_winter_storm_warning_upgrade_source_fresh"
SOURCE_STALE_REASON = "weather_winter_storm_warning_upgrade_source_stale"
PRESSURE_BLOCKED_REASON = "weather_winter_storm_warning_upgrade_pressure_blocked"
PRESSURE_WATCH_REASON = "weather_winter_storm_warning_upgrade_pressure_watch"
PRESSURE_PASS_REASON = "weather_winter_storm_warning_upgrade_pressure_pass"
SNOWFALL_BLOCKED_REASON = "weather_winter_storm_warning_upgrade_snowfall_delta_blocked"
SNOWFALL_WATCH_REASON = "weather_winter_storm_warning_upgrade_snowfall_delta_watch"
ICE_BLOCKED_REASON = "weather_winter_storm_warning_upgrade_ice_risk_blocked"
ICE_WATCH_REASON = "weather_winter_storm_warning_upgrade_ice_risk_watch"
LEAD_BLOCKED_REASON = "weather_winter_storm_warning_upgrade_short_lead_time_blocked"
LEAD_WATCH_REASON = "weather_winter_storm_warning_upgrade_short_lead_time_watch"
CONSENSUS_BLOCKED_REASON = (
    "weather_winter_storm_warning_upgrade_model_consensus_blocked"
)
CONSENSUS_WATCH_REASON = "weather_winter_storm_warning_upgrade_model_consensus_watch"
IMPACT_BLOCKED_REASON = "weather_winter_storm_warning_upgrade_impact_blocked"
IMPACT_WATCH_REASON = "weather_winter_storm_warning_upgrade_impact_watch"
DIGEST_EMPTY_REASON = "weather_winter_storm_warning_upgrade_digest_empty"

NEXT_STEPS = {
    BLOCKED_STATUS: "block_report_only_weather_winter_storm_warning_upgrade_digest",
    WATCH_STATUS: "monitor_report_only_weather_winter_storm_warning_upgrade_digest",
    PASS_STATUS: "continue_report_only_weather_winter_storm_warning_upgrade_digest",
}
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")
QUANT = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_TEXT_BLOCKS = (
    "li" "ve",
    "tra" "ding",
    "au" "th",
    "wal" "let",
    "acc" "ount",
    "ord" "er",
    "can" "cel",
    "repl" "ace",
    "ex" "change",
    "se" "cret",
    "tok" "en",
    "pass" "word",
    "pri" "vate" "_" "key",
    "api" "_" "key",
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_WEATHER_WINTER_STORM_WARNING_UPGRADE_DIGEST_CONFIG_VERSION",
    "WeatherWinterStormWarningUpgradeDigestConfig",
    "WeatherWinterStormWarningUpgradeObservation",
    "WeatherWinterStormWarningUpgradeDigestRow",
    "WeatherWinterStormWarningUpgradeReasonCodeCount",
    "WeatherWinterStormWarningUpgradeDigestReport",
    "build_market_research_weather_winter_storm_warning_upgrade_digest",
    "market_research_weather_winter_storm_warning_upgrade_digest_payload",
)


@dataclass(frozen=True)
class WeatherWinterStormWarningUpgradeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_WEATHER_WINTER_STORM_WARNING_UPGRADE_DIGEST_CONFIG_VERSION
    )
    max_source_age_seconds: Decimal = Decimal("1800.000000")
    watch_upgrade_pressure_threshold: Decimal = Decimal("0.350000")
    blocked_upgrade_pressure_threshold: Decimal = Decimal("0.700000")
    watch_snowfall_forecast_delta_inches: Decimal = Decimal("2.000000")
    blocked_snowfall_forecast_delta_inches: Decimal = Decimal("6.000000")
    watch_ice_accretion_risk: Decimal = Decimal("0.300000")
    blocked_ice_accretion_risk: Decimal = Decimal("0.600000")
    watch_warning_lead_time_hours: Decimal = Decimal("12.000000")
    blocked_warning_lead_time_hours: Decimal = Decimal("6.000000")
    watch_model_consensus_score: Decimal = Decimal("0.500000")
    blocked_model_consensus_score: Decimal = Decimal("0.800000")
    watch_population_airport_impact_score: Decimal = Decimal("0.400000")
    blocked_population_airport_impact_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherWinterStormWarningUpgradeDigestConfig:
            raise TypeError(
                "WeatherWinterStormWarningUpgradeDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            WeatherWinterStormWarningUpgradeDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_WEATHER_WINTER_STORM_WARNING_UPGRADE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_source_age_seconds",
            "watch_snowfall_forecast_delta_inches",
            "blocked_snowfall_forecast_delta_inches",
            "watch_warning_lead_time_hours",
            "blocked_warning_lead_time_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_upgrade_pressure_threshold",
            "blocked_upgrade_pressure_threshold",
            "watch_ice_accretion_risk",
            "blocked_ice_accretion_risk",
            "watch_model_consensus_score",
            "blocked_model_consensus_score",
            "watch_population_airport_impact_score",
            "blocked_population_airport_impact_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        if (
            self.blocked_upgrade_pressure_threshold
            <= self.watch_upgrade_pressure_threshold
        ):
            raise ValueError(
                "blocked_upgrade_pressure_threshold must exceed watch threshold",
            )
        if (
            self.blocked_snowfall_forecast_delta_inches
            < self.watch_snowfall_forecast_delta_inches
        ):
            raise ValueError(
                "blocked_snowfall_forecast_delta_inches must be at least watch threshold",
            )
        if self.blocked_ice_accretion_risk < self.watch_ice_accretion_risk:
            raise ValueError("blocked_ice_accretion_risk must be at least watch threshold")
        if self.blocked_warning_lead_time_hours > self.watch_warning_lead_time_hours:
            raise ValueError(
                "blocked_warning_lead_time_hours must be at most watch threshold",
            )
        if self.blocked_model_consensus_score < self.watch_model_consensus_score:
            raise ValueError(
                "blocked_model_consensus_score must be at least watch threshold",
            )
        if (
            self.blocked_population_airport_impact_score
            < self.watch_population_airport_impact_score
        ):
            raise ValueError(
                "blocked_population_airport_impact_score must be at least watch threshold",
            )
        reject_unsafe_surface_fields(
            "weather winter storm warning upgrade config",
            self,
        )
        require_paper_only_flags(
            "WeatherWinterStormWarningUpgradeDigestConfig",
            self,
        )


@dataclass(frozen=True)
class WeatherWinterStormWarningUpgradeObservation:
    event_id: str
    region_id: str
    forecast_office: str
    market_slug: str
    source_id: str
    forecast_valid_at: datetime
    source_observed_at: datetime
    snowfall_forecast_delta_inches: Decimal
    ice_accretion_risk: Decimal
    warning_lead_time_hours: Decimal
    model_consensus_score: Decimal
    population_airport_impact_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherWinterStormWarningUpgradeObservation:
            raise TypeError(
                "WeatherWinterStormWarningUpgradeObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            WeatherWinterStormWarningUpgradeObservation,
            "observation",
        )
        for field_name in (
            "event_id",
            "region_id",
            "forecast_office",
            "market_slug",
            "source_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
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
            "snowfall_forecast_delta_inches",
            _require_nonnegative_decimal(
                "snowfall_forecast_delta_inches",
                self.snowfall_forecast_delta_inches,
            ),
        )
        object.__setattr__(
            self,
            "warning_lead_time_hours",
            _require_nonnegative_decimal(
                "warning_lead_time_hours",
                self.warning_lead_time_hours,
            ),
        )
        for field_name in (
            "ice_accretion_risk",
            "model_consensus_score",
            "population_airport_impact_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        reject_unsafe_surface_fields(
            "weather winter storm warning upgrade observation",
            self,
        )
        require_paper_only_flags(
            "WeatherWinterStormWarningUpgradeObservation",
            self,
        )


@dataclass(frozen=True)
class WeatherWinterStormWarningUpgradeDigestRow:
    event_id: str
    region_id: str
    forecast_office: str
    market_slug: str
    source_id: str
    forecast_valid_at: datetime
    source_observed_at: datetime
    source_age_seconds: Decimal
    source_freshness_status: str
    snowfall_forecast_delta_inches: Decimal
    ice_accretion_risk: Decimal
    warning_lead_time_hours: Decimal
    model_consensus_score: Decimal
    population_airport_impact_score: Decimal
    upgrade_pressure: Decimal
    upgrade_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherWinterStormWarningUpgradeDigestRow:
            raise TypeError(
                "WeatherWinterStormWarningUpgradeDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, WeatherWinterStormWarningUpgradeDigestRow, "row")
        for field_name in (
            "event_id",
            "region_id",
            "forecast_office",
            "market_slug",
            "source_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
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
            "snowfall_forecast_delta_inches",
            "warning_lead_time_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "ice_accretion_risk",
            "model_consensus_score",
            "population_airport_impact_score",
            "upgrade_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        _require_member(
            "source_freshness_status",
            self.source_freshness_status,
            SOURCE_STATUSES,
        )
        _require_member("upgrade_status", self.upgrade_status, UPGRADE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("weather winter storm warning upgrade row", self)
        require_paper_only_flags("WeatherWinterStormWarningUpgradeDigestRow", self)


@dataclass(frozen=True)
class WeatherWinterStormWarningUpgradeReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherWinterStormWarningUpgradeReasonCodeCount:
            raise TypeError(
                "WeatherWinterStormWarningUpgradeReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            WeatherWinterStormWarningUpgradeReasonCodeCount,
            "reason_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_probability("row_ratio", self.row_ratio),
        )
        reject_unsafe_surface_fields(
            "weather winter storm warning upgrade reason code count",
            self,
        )
        require_paper_only_flags(
            "WeatherWinterStormWarningUpgradeReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class WeatherWinterStormWarningUpgradeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    max_upgrade_pressure: Decimal
    report_risk_score: Decimal
    max_snowfall_forecast_delta_inches: Decimal
    max_ice_accretion_risk: Decimal
    min_warning_lead_time_hours: Decimal
    max_model_consensus_score: Decimal
    max_population_airport_impact_score: Decimal
    max_source_age_seconds: Decimal
    max_source_age_observed_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[WeatherWinterStormWarningUpgradeReasonCodeCount, ...]
    rows: tuple[WeatherWinterStormWarningUpgradeDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherWinterStormWarningUpgradeDigestReport:
            raise TypeError(
                "WeatherWinterStormWarningUpgradeDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, WeatherWinterStormWarningUpgradeDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_WEATHER_WINTER_STORM_WARNING_UPGRADE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("digest_status", self.digest_status, UPGRADE_STATUSES)
        _require_canonical_string("next_step", self.next_step)
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_source_count",
            "max_snowfall_forecast_delta_inches",
            "min_warning_lead_time_hours",
            "max_source_age_seconds",
            "max_source_age_observed_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_upgrade_pressure",
            "report_risk_score",
            "max_ice_accretion_risk",
            "max_model_consensus_score",
            "max_population_airport_impact_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields(
            "weather winter storm warning upgrade report",
            self,
        )
        require_paper_only_flags("WeatherWinterStormWarningUpgradeDigestReport", self)


def build_market_research_weather_winter_storm_warning_upgrade_digest(
    observations: Iterable[WeatherWinterStormWarningUpgradeObservation],
    *,
    config: WeatherWinterStormWarningUpgradeDigestConfig,
    generated_at: datetime,
) -> WeatherWinterStormWarningUpgradeDigestReport:
    if type(config) is not WeatherWinterStormWarningUpgradeDigestConfig:
        raise ValueError(
            "config must be exactly WeatherWinterStormWarningUpgradeDigestConfig",
        )
    reject_unsafe_surface_fields(
        "weather winter storm warning upgrade config",
        config,
    )
    require_paper_only_flags("WeatherWinterStormWarningUpgradeDigestConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        sorted(
            (
                _row_for_observation(
                    observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)
    row_count = _count_decimal(len(rows))
    return WeatherWinterStormWarningUpgradeDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        next_step=NEXT_STEPS[digest_status],
        input_count=_count_decimal(len(normalized_observations)),
        row_count=row_count,
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_source_status_count(rows, SOURCE_STALE),
        max_upgrade_pressure=_max_row_decimal(rows, "upgrade_pressure"),
        report_risk_score=_ratio(
            _sum_decimal(row.upgrade_pressure for row in rows),
            row_count,
        ),
        max_snowfall_forecast_delta_inches=_max_row_decimal(
            rows,
            "snowfall_forecast_delta_inches",
        ),
        max_ice_accretion_risk=_max_row_decimal(rows, "ice_accretion_risk"),
        min_warning_lead_time_hours=_min_row_decimal(
            rows,
            "warning_lead_time_hours",
        ),
        max_model_consensus_score=_max_row_decimal(rows, "model_consensus_score"),
        max_population_airport_impact_score=_max_row_decimal(
            rows,
            "population_airport_impact_score",
        ),
        max_source_age_seconds=config.max_source_age_seconds,
        max_source_age_observed_seconds=_max_row_decimal(rows, "source_age_seconds"),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        rows=rows,
    )


def market_research_weather_winter_storm_warning_upgrade_digest_payload(
    report: WeatherWinterStormWarningUpgradeDigestReport,
) -> dict[str, Any]:
    if type(report) is not WeatherWinterStormWarningUpgradeDigestReport:
        raise ValueError(
            "report must be exactly WeatherWinterStormWarningUpgradeDigestReport",
        )
    reject_unsafe_surface_fields(
        "weather winter storm warning upgrade report",
        report,
    )
    require_paper_only_flags("WeatherWinterStormWarningUpgradeDigestReport", report)
    value = _json_value(report)
    if type(value) is not dict:
        raise ValueError("report payload must be an object")
    _require_payload_flags(value)
    reject_unsafe_surface_fields(
        "weather winter storm warning upgrade payload",
        value,
    )
    return value


def _row_for_observation(
    observation: WeatherWinterStormWarningUpgradeObservation,
    *,
    config: WeatherWinterStormWarningUpgradeDigestConfig,
    generated_at: datetime,
) -> WeatherWinterStormWarningUpgradeDigestRow:
    source_age_seconds = _age_seconds(generated_at, observation.source_observed_at)
    source_freshness_status = (
        SOURCE_STALE if source_age_seconds > config.max_source_age_seconds else SOURCE_FRESH
    )
    source_fresh = source_freshness_status == SOURCE_FRESH
    upgrade_pressure = _upgrade_pressure(observation, config)
    if not source_fresh or upgrade_pressure >= config.blocked_upgrade_pressure_threshold:
        upgrade_status = BLOCKED_STATUS
    elif upgrade_pressure >= config.watch_upgrade_pressure_threshold:
        upgrade_status = WATCH_STATUS
    else:
        upgrade_status = PASS_STATUS
    return WeatherWinterStormWarningUpgradeDigestRow(
        event_id=observation.event_id,
        region_id=observation.region_id,
        forecast_office=observation.forecast_office,
        market_slug=observation.market_slug,
        source_id=observation.source_id,
        forecast_valid_at=observation.forecast_valid_at,
        source_observed_at=observation.source_observed_at,
        source_age_seconds=source_age_seconds,
        source_freshness_status=source_freshness_status,
        snowfall_forecast_delta_inches=observation.snowfall_forecast_delta_inches,
        ice_accretion_risk=observation.ice_accretion_risk,
        warning_lead_time_hours=observation.warning_lead_time_hours,
        model_consensus_score=observation.model_consensus_score,
        population_airport_impact_score=observation.population_airport_impact_score,
        upgrade_pressure=upgrade_pressure,
        upgrade_status=upgrade_status,
        reason_codes=_row_reason_codes(
            observation.upstream_reason_codes,
            source_freshness_status=source_freshness_status,
            upgrade_status=upgrade_status,
            snowfall_forecast_delta_inches=observation.snowfall_forecast_delta_inches,
            ice_accretion_risk=observation.ice_accretion_risk,
            warning_lead_time_hours=observation.warning_lead_time_hours,
            model_consensus_score=observation.model_consensus_score,
            population_airport_impact_score=observation.population_airport_impact_score,
            config=config,
        ),
    )


def _upgrade_pressure(
    observation: WeatherWinterStormWarningUpgradeObservation,
    config: WeatherWinterStormWarningUpgradeDigestConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        snowfall_component = _capped_ratio(
            observation.snowfall_forecast_delta_inches,
            config.blocked_snowfall_forecast_delta_inches,
        )
        lead_component = _short_lead_component(
            observation.warning_lead_time_hours,
            config.watch_warning_lead_time_hours,
        )
        pressure = (
            snowfall_component
            + observation.ice_accretion_risk
            + lead_component
            + observation.model_consensus_score
            + observation.population_airport_impact_score
        ) / FIVE
    return _quantize_decimal(min(max(pressure, ZERO), ONE))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    source_freshness_status: str,
    upgrade_status: str,
    snowfall_forecast_delta_inches: Decimal,
    ice_accretion_risk: Decimal,
    warning_lead_time_hours: Decimal,
    model_consensus_score: Decimal,
    population_airport_impact_score: Decimal,
    config: WeatherWinterStormWarningUpgradeDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if source_freshness_status == SOURCE_STALE:
        reason_codes.append(SOURCE_STALE_REASON)
        return _normalize_reason_codes(tuple(reason_codes))

    reason_codes.append(SOURCE_FRESH_REASON)
    if upgrade_status == BLOCKED_STATUS:
        reason_codes.append(PRESSURE_BLOCKED_REASON)
    elif upgrade_status == WATCH_STATUS:
        reason_codes.append(PRESSURE_WATCH_REASON)
    else:
        reason_codes.append(PRESSURE_PASS_REASON)
    if snowfall_forecast_delta_inches >= config.blocked_snowfall_forecast_delta_inches:
        reason_codes.append(SNOWFALL_BLOCKED_REASON)
    elif snowfall_forecast_delta_inches >= config.watch_snowfall_forecast_delta_inches:
        reason_codes.append(SNOWFALL_WATCH_REASON)
    if ice_accretion_risk >= config.blocked_ice_accretion_risk:
        reason_codes.append(ICE_BLOCKED_REASON)
    elif ice_accretion_risk >= config.watch_ice_accretion_risk:
        reason_codes.append(ICE_WATCH_REASON)
    if warning_lead_time_hours <= config.blocked_warning_lead_time_hours:
        reason_codes.append(LEAD_BLOCKED_REASON)
    elif warning_lead_time_hours <= config.watch_warning_lead_time_hours:
        reason_codes.append(LEAD_WATCH_REASON)
    if model_consensus_score >= config.blocked_model_consensus_score:
        reason_codes.append(CONSENSUS_BLOCKED_REASON)
    elif model_consensus_score >= config.watch_model_consensus_score:
        reason_codes.append(CONSENSUS_WATCH_REASON)
    if population_airport_impact_score >= config.blocked_population_airport_impact_score:
        reason_codes.append(IMPACT_BLOCKED_REASON)
    elif population_airport_impact_score >= config.watch_population_airport_impact_score:
        reason_codes.append(IMPACT_WATCH_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_observations(
    observations: Iterable[WeatherWinterStormWarningUpgradeObservation],
    *,
    generated_at: datetime,
) -> tuple[WeatherWinterStormWarningUpgradeObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must be an iterable of "
            "WeatherWinterStormWarningUpgradeObservation",
        )
    normalized = tuple(observations)
    seen_event_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not WeatherWinterStormWarningUpgradeObservation:
            raise ValueError(
                "observations must contain WeatherWinterStormWarningUpgradeObservation",
            )
        reject_unsafe_surface_fields(
            "weather winter storm warning upgrade observation",
            observation,
        )
        require_paper_only_flags(
            "WeatherWinterStormWarningUpgradeObservation",
            observation,
        )
        if observation.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be after generated_at")
        if observation.event_id in seen_event_ids:
            raise ValueError("duplicate event_id values are not supported")
        seen_event_ids.add(observation.event_id)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.region_id,
                item.forecast_office,
                item.market_slug,
                item.event_id,
            ),
        ),
    )


def _normalize_rows(
    rows: Iterable[WeatherWinterStormWarningUpgradeDigestRow],
) -> tuple[WeatherWinterStormWarningUpgradeDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not WeatherWinterStormWarningUpgradeDigestRow:
            raise ValueError("rows must contain WeatherWinterStormWarningUpgradeDigestRow")
        require_paper_only_flags("WeatherWinterStormWarningUpgradeDigestRow", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[WeatherWinterStormWarningUpgradeReasonCodeCount],
) -> tuple[WeatherWinterStormWarningUpgradeReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not WeatherWinterStormWarningUpgradeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "WeatherWinterStormWarningUpgradeReasonCodeCount",
            )
        require_paper_only_flags(
            "WeatherWinterStormWarningUpgradeReasonCodeCount",
            count,
        )
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row(row: WeatherWinterStormWarningUpgradeDigestRow) -> None:
    if row.source_freshness_status == SOURCE_STALE:
        if row.upgrade_status != BLOCKED_STATUS:
            raise ValueError("stale source rows must be blocked")
        if SOURCE_STALE_REASON not in row.reason_codes:
            raise ValueError("stale source rows must include stale source reason")
        if SOURCE_FRESH_REASON in row.reason_codes:
            raise ValueError("stale source rows must not include fresh source reason")
        if (
            PRESSURE_BLOCKED_REASON in row.reason_codes
            or PRESSURE_WATCH_REASON in row.reason_codes
            or PRESSURE_PASS_REASON in row.reason_codes
        ):
            raise ValueError("stale source rows must not include pressure reason")
        return
    if SOURCE_STALE_REASON in row.reason_codes:
        raise ValueError("fresh source rows must not include stale source reason")
    if SOURCE_FRESH_REASON not in row.reason_codes:
        raise ValueError("fresh source rows must include source freshness reason")
    if row.upgrade_status == BLOCKED_STATUS:
        if PRESSURE_BLOCKED_REASON not in row.reason_codes:
            raise ValueError("upgrade_status must match reason_codes")
    elif row.upgrade_status == WATCH_STATUS:
        if PRESSURE_WATCH_REASON not in row.reason_codes:
            raise ValueError("upgrade_status must match reason_codes")
    elif PRESSURE_PASS_REASON not in row.reason_codes:
        raise ValueError("upgrade_status must match reason_codes")


def _validate_report(report: WeatherWinterStormWarningUpgradeDigestReport) -> None:
    rows = report.rows
    if report.input_count != _count_decimal(len(rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_count != _status_count(rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.stale_source_count != _source_status_count(rows, SOURCE_STALE):
        raise ValueError("stale_source_count must match rows")
    if report.max_upgrade_pressure != _max_row_decimal(rows, "upgrade_pressure"):
        raise ValueError("max_upgrade_pressure must match rows")
    if report.report_risk_score != _ratio(
        _sum_decimal(row.upgrade_pressure for row in rows),
        report.row_count,
    ):
        raise ValueError("report_risk_score must match rows")
    if report.max_snowfall_forecast_delta_inches != _max_row_decimal(
        rows,
        "snowfall_forecast_delta_inches",
    ):
        raise ValueError("max_snowfall_forecast_delta_inches must match rows")
    if report.max_ice_accretion_risk != _max_row_decimal(rows, "ice_accretion_risk"):
        raise ValueError("max_ice_accretion_risk must match rows")
    if report.min_warning_lead_time_hours != _min_row_decimal(
        rows,
        "warning_lead_time_hours",
    ):
        raise ValueError("min_warning_lead_time_hours must match rows")
    if report.max_model_consensus_score != _max_row_decimal(
        rows,
        "model_consensus_score",
    ):
        raise ValueError("max_model_consensus_score must match rows")
    if report.max_population_airport_impact_score != _max_row_decimal(
        rows,
        "population_airport_impact_score",
    ):
        raise ValueError("max_population_airport_impact_score must match rows")
    if report.max_source_age_observed_seconds != _max_row_decimal(
        rows,
        "source_age_seconds",
    ):
        raise ValueError("max_source_age_observed_seconds must match rows")
    if report.digest_status != _digest_status(rows):
        raise ValueError("digest_status must match rows")
    if report.next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts must match rows")


def _report_reason_codes(
    rows: tuple[WeatherWinterStormWarningUpgradeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (DIGEST_EMPTY_REASON,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[WeatherWinterStormWarningUpgradeDigestRow, ...],
) -> tuple[WeatherWinterStormWarningUpgradeReasonCodeCount, ...]:
    if reason_codes == (DIGEST_EMPTY_REASON,):
        return ()
    row_count = _count_decimal(len(rows))
    return tuple(
        sorted(
            (
                WeatherWinterStormWarningUpgradeReasonCodeCount(
                    reason_code=reason_code,
                    count=_count_decimal(
                        sum(1 for row in rows if reason_code in row.reason_codes),
                    ),
                    row_ratio=_ratio(
                        _count_decimal(
                            sum(1 for row in rows if reason_code in row.reason_codes),
                        ),
                        row_count,
                    ),
                )
                for reason_code in reason_codes
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _status_count(
    rows: tuple[WeatherWinterStormWarningUpgradeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.upgrade_status == status))


def _source_status_count(
    rows: tuple[WeatherWinterStormWarningUpgradeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if row.source_freshness_status == status),
    )


def _digest_status(
    rows: tuple[WeatherWinterStormWarningUpgradeDigestRow, ...],
) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.upgrade_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.upgrade_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _row_sort_key(
    row: WeatherWinterStormWarningUpgradeDigestRow,
) -> tuple[Decimal | str, ...]:
    return (
        STATUS_RANK[row.upgrade_status],
        -row.upgrade_pressure,
        -row.snowfall_forecast_delta_inches,
        -row.ice_accretion_risk,
        row.region_id,
        row.forecast_office,
        row.market_slug,
        row.event_id,
    )


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("source_observed_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _capped_ratio(value: Decimal, total: Decimal) -> Decimal:
    if total <= ZERO:
        raise ValueError("ratio total must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(min(value / total, ONE))


def _short_lead_component(value: Decimal, watch_threshold: Decimal) -> Decimal:
    if value >= watch_threshold:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal((watch_threshold - value) / watch_threshold)


def _ratio(value: Decimal, total: Decimal) -> Decimal:
    if total == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(value / total)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize_decimal(total + value)
    return total


def _max_row_decimal(
    rows: tuple[WeatherWinterStormWarningUpgradeDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[WeatherWinterStormWarningUpgradeDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if not _CANONICAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be canonical")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _TEXT_BLOCKS):
        raise ValueError(f"{field_name} value is not allowed")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported value")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _require_payload_flags(value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


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
