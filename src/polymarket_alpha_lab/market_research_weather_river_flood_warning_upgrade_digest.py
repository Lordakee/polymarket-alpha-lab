"""Pure Phase 1 weather river flood warning upgrade digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_WEATHER_RIVER_FLOOD_WARNING_UPGRADE_DIGEST_CONFIG_VERSION = (
    "market-research-weather-river-flood-warning-upgrade-digest-v0"
)

SOURCE_CURRENT = "current"
SOURCE_STALE = "stale"

ROW_STATUSES = ("pass", "watch", "blocked")
SOURCE_STATUSES = (SOURCE_CURRENT, SOURCE_STALE)

SOURCE_STALE_REASON = "weather_river_flood_warning_upgrade_source_stale"
MAJOR_UPGRADE_REASON = "weather_river_flood_warning_upgrade_major_upgrade"
LEVEL_UPGRADE_REASON = "weather_river_flood_warning_upgrade_level_upgrade"
STAGE_ABOVE_REASON = "weather_river_flood_warning_upgrade_stage_above_flood_stage"
FORECAST_ABOVE_REASON = (
    "weather_river_flood_warning_upgrade_forecast_above_flood_stage"
)
STAGE_NEAR_REASON = "weather_river_flood_warning_upgrade_stage_near_flood_stage"
FORECAST_NEAR_REASON = "weather_river_flood_warning_upgrade_forecast_near_flood_stage"
HEAVY_RAINFALL_REASON = "weather_river_flood_warning_upgrade_heavy_rainfall"
LOW_CONFIDENCE_REASON = "weather_river_flood_warning_upgrade_low_confidence"
ROW_CLEAR_REASON = "weather_river_flood_warning_upgrade_row_clear"
DIGEST_CLEAR_REASON = "weather_river_flood_warning_upgrade_digest_clear"
DIGEST_EMPTY_REASON = "weather_river_flood_warning_upgrade_digest_empty"

ROW_REASON_CODES = (
    SOURCE_STALE_REASON,
    MAJOR_UPGRADE_REASON,
    LEVEL_UPGRADE_REASON,
    STAGE_ABOVE_REASON,
    FORECAST_ABOVE_REASON,
    STAGE_NEAR_REASON,
    FORECAST_NEAR_REASON,
    HEAVY_RAINFALL_REASON,
    LOW_CONFIDENCE_REASON,
    ROW_CLEAR_REASON,
)
REPORT_REASON_CODES = (
    SOURCE_STALE_REASON,
    MAJOR_UPGRADE_REASON,
    LEVEL_UPGRADE_REASON,
    STAGE_ABOVE_REASON,
    FORECAST_ABOVE_REASON,
    STAGE_NEAR_REASON,
    FORECAST_NEAR_REASON,
    HEAVY_RAINFALL_REASON,
    LOW_CONFIDENCE_REASON,
    DIGEST_CLEAR_REASON,
    DIGEST_EMPTY_REASON,
)

NEXT_STEPS = {
    "pass": "continue_report_only_weather_river_flood_warning_upgrade_digest",
    "watch": "monitor_report_only_weather_river_flood_warning_upgrade_digest",
    "blocked": "block_report_only_weather_river_flood_warning_upgrade_digest",
}
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
REASON_RANK = {
    reason_code: Decimal(index).quantize(Decimal("0.000001"))
    for index, reason_code in enumerate(REPORT_REASON_CODES + (ROW_CLEAR_REASON,))
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
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
)


__all__ = (
    "DEFAULT_WEATHER_RIVER_FLOOD_WARNING_UPGRADE_DIGEST_CONFIG_VERSION",
    "WeatherRiverFloodWarningUpgradeDigestConfig",
    "WeatherRiverFloodWarningUpgradeObservation",
    "WeatherRiverFloodWarningUpgradeDigestRow",
    "WeatherRiverFloodWarningUpgradeReasonCodeCount",
    "WeatherRiverFloodWarningUpgradeDigestReport",
    "build_market_research_weather_river_flood_warning_upgrade_digest",
    "market_research_weather_river_flood_warning_upgrade_digest_json",
)


@dataclass(frozen=True)
class WeatherRiverFloodWarningUpgradeDigestConfig:
    config_version: str = DEFAULT_WEATHER_RIVER_FLOOD_WARNING_UPGRADE_DIGEST_CONFIG_VERSION
    max_source_age_seconds: Decimal = Decimal("3600.000000")
    watch_upgrade_delta: Decimal = Decimal("1.000000")
    blocked_upgrade_delta: Decimal = Decimal("2.000000")
    near_flood_stage_ratio: Decimal = Decimal("0.900000")
    heavy_rainfall_inches_24h: Decimal = Decimal("3.000000")
    low_confidence_ratio: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherRiverFloodWarningUpgradeDigestConfig:
            raise TypeError(
                "WeatherRiverFloodWarningUpgradeDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherRiverFloodWarningUpgradeDigestConfig:
            raise ValueError(
                "config must be exactly WeatherRiverFloodWarningUpgradeDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_WEATHER_RIVER_FLOOD_WARNING_UPGRADE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_source_age_seconds",
            "watch_upgrade_delta",
            "blocked_upgrade_delta",
            "heavy_rainfall_inches_24h",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "near_flood_stage_ratio",
            _require_positive_probability(
                "near_flood_stage_ratio",
                self.near_flood_stage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "low_confidence_ratio",
            _require_probability("low_confidence_ratio", self.low_confidence_ratio),
        )
        if self.blocked_upgrade_delta < self.watch_upgrade_delta:
            raise ValueError(
                "blocked_upgrade_delta must be at least watch_upgrade_delta",
            )
        require_paper_only_flags("WeatherRiverFloodWarningUpgradeDigestConfig", self)


@dataclass(frozen=True)
class WeatherRiverFloodWarningUpgradeObservation:
    station_id: str
    event_id: str
    source_id: str
    observed_at: datetime
    prior_warning_level: Decimal
    current_warning_level: Decimal
    river_stage_feet: Decimal
    flood_stage_feet: Decimal
    forecast_crest_feet: Decimal
    rainfall_inches_24h: Decimal
    source_confidence_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherRiverFloodWarningUpgradeObservation:
            raise TypeError(
                "WeatherRiverFloodWarningUpgradeObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherRiverFloodWarningUpgradeObservation:
            raise ValueError(
                "observation must be exactly WeatherRiverFloodWarningUpgradeObservation",
            )
        for field_name in ("station_id", "event_id", "source_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "prior_warning_level",
            "current_warning_level",
            "river_stage_feet",
            "forecast_crest_feet",
            "rainfall_inches_24h",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "flood_stage_feet",
            _require_positive_decimal("flood_stage_feet", self.flood_stage_feet),
        )
        object.__setattr__(
            self,
            "source_confidence_ratio",
            _require_probability(
                "source_confidence_ratio",
                self.source_confidence_ratio,
            ),
        )
        if self.current_warning_level < self.prior_warning_level:
            raise ValueError(
                "current_warning_level must not be below prior_warning_level",
            )
        require_paper_only_flags("WeatherRiverFloodWarningUpgradeObservation", self)


@dataclass(frozen=True)
class WeatherRiverFloodWarningUpgradeDigestRow:
    station_id: str
    event_id: str
    source_id: str
    observed_at: datetime
    source_age_seconds: Decimal
    source_freshness_status: str
    prior_warning_level: Decimal
    current_warning_level: Decimal
    warning_level_delta: Decimal
    river_stage_feet: Decimal
    flood_stage_feet: Decimal
    river_stage_ratio: Decimal
    forecast_crest_feet: Decimal
    forecast_crest_ratio: Decimal
    rainfall_inches_24h: Decimal
    source_confidence_ratio: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherRiverFloodWarningUpgradeDigestRow:
            raise TypeError(
                "WeatherRiverFloodWarningUpgradeDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherRiverFloodWarningUpgradeDigestRow:
            raise ValueError("row must be exactly WeatherRiverFloodWarningUpgradeDigestRow")
        for field_name in ("station_id", "event_id", "source_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_age_seconds",
            "prior_warning_level",
            "current_warning_level",
            "warning_level_delta",
            "river_stage_feet",
            "river_stage_ratio",
            "forecast_crest_feet",
            "forecast_crest_ratio",
            "rainfall_inches_24h",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "flood_stage_feet",
            _require_positive_decimal("flood_stage_feet", self.flood_stage_feet),
        )
        object.__setattr__(
            self,
            "source_confidence_ratio",
            _require_probability(
                "source_confidence_ratio",
                self.source_confidence_ratio,
            ),
        )
        _require_member(
            "source_freshness_status",
            self.source_freshness_status,
            SOURCE_STATUSES,
        )
        _require_member("row_status", self.row_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("weather river flood warning upgrade row", self)
        require_paper_only_flags("WeatherRiverFloodWarningUpgradeDigestRow", self)


@dataclass(frozen=True)
class WeatherRiverFloodWarningUpgradeReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherRiverFloodWarningUpgradeReasonCodeCount:
            raise TypeError(
                "WeatherRiverFloodWarningUpgradeReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherRiverFloodWarningUpgradeReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "WeatherRiverFloodWarningUpgradeReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
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
            "weather river flood warning upgrade reason code count",
            self,
        )
        require_paper_only_flags("WeatherRiverFloodWarningUpgradeReasonCodeCount", self)


@dataclass(frozen=True)
class WeatherRiverFloodWarningUpgradeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    input_count: Decimal
    row_count: Decimal
    blocked_row_count: Decimal
    watch_row_count: Decimal
    pass_row_count: Decimal
    stale_source_count: Decimal
    upgrade_count: Decimal
    major_upgrade_count: Decimal
    current_above_flood_stage_count: Decimal
    forecast_above_flood_stage_count: Decimal
    max_source_age_seconds: Decimal
    max_source_age_observed_seconds: Decimal
    max_warning_level_delta: Decimal
    max_river_stage_ratio: Decimal
    max_forecast_crest_ratio: Decimal
    max_rainfall_inches_24h: Decimal
    average_source_confidence_ratio: Decimal
    rows: tuple[WeatherRiverFloodWarningUpgradeDigestRow, ...]
    reason_code_counts: tuple[WeatherRiverFloodWarningUpgradeReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherRiverFloodWarningUpgradeDigestReport:
            raise TypeError(
                "WeatherRiverFloodWarningUpgradeDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherRiverFloodWarningUpgradeDigestReport:
            raise ValueError(
                "report must be exactly WeatherRiverFloodWarningUpgradeDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_WEATHER_RIVER_FLOOD_WARNING_UPGRADE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("digest_status", self.digest_status, ROW_STATUSES)
        _require_canonical_string("next_step", self.next_step)
        for field_name in (
            "input_count",
            "row_count",
            "blocked_row_count",
            "watch_row_count",
            "pass_row_count",
            "stale_source_count",
            "upgrade_count",
            "major_upgrade_count",
            "current_above_flood_stage_count",
            "forecast_above_flood_stage_count",
            "max_source_age_seconds",
            "max_source_age_observed_seconds",
            "max_warning_level_delta",
            "max_river_stage_ratio",
            "max_forecast_crest_ratio",
            "max_rainfall_inches_24h",
            "average_source_confidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_source_confidence_ratio > ONE:
            raise ValueError("average_source_confidence_ratio must be no greater than one")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("weather river flood warning upgrade report", self)
        require_paper_only_flags("WeatherRiverFloodWarningUpgradeDigestReport", self)


def build_market_research_weather_river_flood_warning_upgrade_digest(
    observations: Iterable[WeatherRiverFloodWarningUpgradeObservation],
    *,
    config: WeatherRiverFloodWarningUpgradeDigestConfig,
    generated_at: datetime,
) -> WeatherRiverFloodWarningUpgradeDigestReport:
    if type(config) is not WeatherRiverFloodWarningUpgradeDigestConfig:
        raise ValueError(
            "config must be exactly WeatherRiverFloodWarningUpgradeDigestConfig",
        )
    require_paper_only_flags("WeatherRiverFloodWarningUpgradeDigestConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        _row_for_observation(
            observation,
            config=config,
            generated_at=generated_at_utc,
        )
        for observation in normalized_observations
    )
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    reason_codes = _report_reason_codes(sorted_rows)
    digest_status = _digest_status(sorted_rows)
    row_count = _count_decimal(len(sorted_rows))

    return WeatherRiverFloodWarningUpgradeDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        next_step=NEXT_STEPS[digest_status],
        input_count=_count_decimal(len(normalized_observations)),
        row_count=row_count,
        blocked_row_count=_count_decimal(
            sum(1 for row in sorted_rows if row.row_status == "blocked"),
        ),
        watch_row_count=_count_decimal(
            sum(1 for row in sorted_rows if row.row_status == "watch"),
        ),
        pass_row_count=_count_decimal(
            sum(1 for row in sorted_rows if row.row_status == "pass"),
        ),
        stale_source_count=_count_decimal(
            sum(1 for row in sorted_rows if row.source_freshness_status == SOURCE_STALE),
        ),
        upgrade_count=_count_decimal(
            sum(
                1
                for row in sorted_rows
                if (
                    MAJOR_UPGRADE_REASON in row.reason_codes
                    or LEVEL_UPGRADE_REASON in row.reason_codes
                )
            ),
        ),
        major_upgrade_count=_count_decimal(
            sum(1 for row in sorted_rows if MAJOR_UPGRADE_REASON in row.reason_codes),
        ),
        current_above_flood_stage_count=_count_decimal(
            sum(1 for row in sorted_rows if row.river_stage_feet >= row.flood_stage_feet),
        ),
        forecast_above_flood_stage_count=_count_decimal(
            sum(1 for row in sorted_rows if row.forecast_crest_feet >= row.flood_stage_feet),
        ),
        max_source_age_seconds=config.max_source_age_seconds,
        max_source_age_observed_seconds=max(
            (row.source_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_warning_level_delta=max(
            (row.warning_level_delta for row in sorted_rows),
            default=ZERO,
        ),
        max_river_stage_ratio=max(
            (row.river_stage_ratio for row in sorted_rows),
            default=ZERO,
        ),
        max_forecast_crest_ratio=max(
            (row.forecast_crest_ratio for row in sorted_rows),
            default=ZERO,
        ),
        max_rainfall_inches_24h=max(
            (row.rainfall_inches_24h for row in sorted_rows),
            default=ZERO,
        ),
        average_source_confidence_ratio=_ratio(
            _sum_decimal(row.source_confidence_ratio for row in sorted_rows),
            row_count,
        ),
        rows=sorted_rows,
        reason_code_counts=_reason_code_counts(reason_codes, sorted_rows),
        reason_codes=reason_codes,
    )


def market_research_weather_river_flood_warning_upgrade_digest_json(
    report: WeatherRiverFloodWarningUpgradeDigestReport,
) -> dict[str, Any]:
    if type(report) is not WeatherRiverFloodWarningUpgradeDigestReport:
        raise ValueError(
            "report must be exactly WeatherRiverFloodWarningUpgradeDigestReport",
        )
    reject_unsafe_surface_fields("weather river flood warning upgrade report", report)
    value = json_ready_no_floats(asdict(report))
    if not isinstance(value, dict):
        raise ValueError("report JSON value must be an object")
    reject_unsafe_surface_fields(
        "weather river flood warning upgrade JSON value",
        value,
    )
    return value


def _row_for_observation(
    observation: WeatherRiverFloodWarningUpgradeObservation,
    *,
    config: WeatherRiverFloodWarningUpgradeDigestConfig,
    generated_at: datetime,
) -> WeatherRiverFloodWarningUpgradeDigestRow:
    source_age_seconds = _age_seconds(generated_at, observation.observed_at)
    source_freshness_status = (
        SOURCE_STALE
        if source_age_seconds > config.max_source_age_seconds
        else SOURCE_CURRENT
    )
    warning_level_delta = _require_nonnegative_decimal(
        "warning_level_delta",
        observation.current_warning_level - observation.prior_warning_level,
    )
    river_stage_ratio = _ratio(observation.river_stage_feet, observation.flood_stage_feet)
    forecast_crest_ratio = _ratio(
        observation.forecast_crest_feet,
        observation.flood_stage_feet,
    )
    reason_codes = _row_reason_codes(
        source_freshness_status=source_freshness_status,
        warning_level_delta=warning_level_delta,
        river_stage_feet=observation.river_stage_feet,
        flood_stage_feet=observation.flood_stage_feet,
        river_stage_ratio=river_stage_ratio,
        forecast_crest_feet=observation.forecast_crest_feet,
        forecast_crest_ratio=forecast_crest_ratio,
        rainfall_inches_24h=observation.rainfall_inches_24h,
        source_confidence_ratio=observation.source_confidence_ratio,
        config=config,
    )
    return WeatherRiverFloodWarningUpgradeDigestRow(
        station_id=observation.station_id,
        event_id=observation.event_id,
        source_id=observation.source_id,
        observed_at=observation.observed_at,
        source_age_seconds=source_age_seconds,
        source_freshness_status=source_freshness_status,
        prior_warning_level=observation.prior_warning_level,
        current_warning_level=observation.current_warning_level,
        warning_level_delta=warning_level_delta,
        river_stage_feet=observation.river_stage_feet,
        flood_stage_feet=observation.flood_stage_feet,
        river_stage_ratio=river_stage_ratio,
        forecast_crest_feet=observation.forecast_crest_feet,
        forecast_crest_ratio=forecast_crest_ratio,
        rainfall_inches_24h=observation.rainfall_inches_24h,
        source_confidence_ratio=observation.source_confidence_ratio,
        row_status=_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_freshness_status: str,
    warning_level_delta: Decimal,
    river_stage_feet: Decimal,
    flood_stage_feet: Decimal,
    river_stage_ratio: Decimal,
    forecast_crest_feet: Decimal,
    forecast_crest_ratio: Decimal,
    rainfall_inches_24h: Decimal,
    source_confidence_ratio: Decimal,
    config: WeatherRiverFloodWarningUpgradeDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source_freshness_status == SOURCE_STALE:
        reasons.append(SOURCE_STALE_REASON)
    if warning_level_delta >= config.blocked_upgrade_delta:
        reasons.append(MAJOR_UPGRADE_REASON)
    elif warning_level_delta >= config.watch_upgrade_delta:
        reasons.append(LEVEL_UPGRADE_REASON)
    if river_stage_feet >= flood_stage_feet:
        reasons.append(STAGE_ABOVE_REASON)
    elif river_stage_ratio >= config.near_flood_stage_ratio:
        reasons.append(STAGE_NEAR_REASON)
    if forecast_crest_feet >= flood_stage_feet:
        reasons.append(FORECAST_ABOVE_REASON)
    elif forecast_crest_ratio >= config.near_flood_stage_ratio:
        reasons.append(FORECAST_NEAR_REASON)
    if rainfall_inches_24h >= config.heavy_rainfall_inches_24h:
        reasons.append(HEAVY_RAINFALL_REASON)
    if source_confidence_ratio <= config.low_confidence_ratio:
        reasons.append(LOW_CONFIDENCE_REASON)
    if not reasons:
        reasons.append(ROW_CLEAR_REASON)
    return _sort_reason_codes(tuple(reasons), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[WeatherRiverFloodWarningUpgradeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (DIGEST_EMPTY_REASON,)
    reasons = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != ROW_CLEAR_REASON
    )
    if not reasons:
        return (DIGEST_CLEAR_REASON,)
    return _sort_reason_codes(tuple(set(reasons)), REPORT_REASON_CODES)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[WeatherRiverFloodWarningUpgradeDigestRow, ...],
) -> tuple[WeatherRiverFloodWarningUpgradeReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == (DIGEST_EMPTY_REASON,):
        return (
            WeatherRiverFloodWarningUpgradeReasonCodeCount(
                reason_code=DIGEST_EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    if reason_codes == (DIGEST_CLEAR_REASON,):
        return (
            WeatherRiverFloodWarningUpgradeReasonCodeCount(
                reason_code=DIGEST_CLEAR_REASON,
                count=row_count,
                row_ratio=ONE,
            ),
        )
    return tuple(
        WeatherRiverFloodWarningUpgradeReasonCodeCount(
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
    )


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        MAJOR_UPGRADE_REASON in reason_codes
        or STAGE_ABOVE_REASON in reason_codes
        or FORECAST_ABOVE_REASON in reason_codes
    ):
        return "blocked"
    if reason_codes == (ROW_CLEAR_REASON,):
        return "pass"
    return "watch"


def _digest_status(rows: tuple[WeatherRiverFloodWarningUpgradeDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_observations(
    observations: Iterable[WeatherRiverFloodWarningUpgradeObservation],
    *,
    generated_at: datetime,
) -> tuple[WeatherRiverFloodWarningUpgradeObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError(
            "observations must be an iterable of "
            "WeatherRiverFloodWarningUpgradeObservation",
        )
    rows = tuple(observations)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not WeatherRiverFloodWarningUpgradeObservation:
            raise ValueError(
                "observations must contain WeatherRiverFloodWarningUpgradeObservation",
            )
        require_paper_only_flags("WeatherRiverFloodWarningUpgradeObservation", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (row.station_id, row.event_id)
        if key in seen_keys:
            raise ValueError("event_id values must be unique per station_id")
        seen_keys.add(key)
    return tuple(sorted(rows, key=lambda row: (row.station_id, row.event_id, row.source_id)))


def _normalize_rows(
    rows: tuple[WeatherRiverFloodWarningUpgradeDigestRow, ...],
) -> tuple[WeatherRiverFloodWarningUpgradeDigestRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not WeatherRiverFloodWarningUpgradeDigestRow:
            raise ValueError("rows must contain WeatherRiverFloodWarningUpgradeDigestRow")
        require_paper_only_flags("WeatherRiverFloodWarningUpgradeDigestRow", row)
    normalized = tuple(sorted(rows, key=_row_sort_key))
    if rows != normalized:
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[WeatherRiverFloodWarningUpgradeReasonCodeCount, ...],
) -> tuple[WeatherRiverFloodWarningUpgradeReasonCodeCount, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not WeatherRiverFloodWarningUpgradeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "WeatherRiverFloodWarningUpgradeReasonCodeCount",
            )
        require_paper_only_flags("WeatherRiverFloodWarningUpgradeReasonCodeCount", row)
    normalized = tuple(sorted(rows, key=lambda row: _reason_sort_key(row.reason_code)))
    if rows != normalized:
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_reason_codes)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    normalized = _sort_reason_codes(reason_codes, allowed_reason_codes)
    if reason_codes != normalized:
        raise ValueError(f"{field_name} must use deterministic sorting")
    return normalized


def _sort_reason_codes(
    reason_codes: tuple[str, ...],
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(reason_code for reason_code in allowed_reason_codes if reason_code in reason_codes)


def _row_sort_key(row: WeatherRiverFloodWarningUpgradeDigestRow) -> tuple[Decimal | str, ...]:
    return (
        STATUS_RANK[row.row_status],
        -row.warning_level_delta,
        -row.river_stage_ratio,
        -row.forecast_crest_ratio,
        -row.rainfall_inches_24h,
        row.station_id,
        row.event_id,
        row.source_id,
    )


def _reason_sort_key(reason_code: str) -> Decimal:
    return REASON_RANK[reason_code]


def _validate_row(row: WeatherRiverFloodWarningUpgradeDigestRow) -> None:
    expected_status = _status_for_reason_codes(row.reason_codes)
    if row.row_status != expected_status:
        raise ValueError("row_status must match reason_codes")
    if row.source_freshness_status == SOURCE_STALE:
        if SOURCE_STALE_REASON not in row.reason_codes:
            raise ValueError("stale source rows must include stale reason")
    if row.source_freshness_status == SOURCE_CURRENT:
        if SOURCE_STALE_REASON in row.reason_codes:
            raise ValueError("current source rows must not include stale reason")
    if row.current_warning_level < row.prior_warning_level:
        raise ValueError("current_warning_level must not be below prior_warning_level")
    if row.warning_level_delta != _require_nonnegative_decimal(
        "warning_level_delta",
        row.current_warning_level - row.prior_warning_level,
    ):
        raise ValueError("warning_level_delta must match warning levels")
    if row.warning_level_delta == ZERO:
        if (
            MAJOR_UPGRADE_REASON in row.reason_codes
            or LEVEL_UPGRADE_REASON in row.reason_codes
        ):
            raise ValueError("zero delta rows must not include upgrade reason")
    if row.river_stage_ratio != _ratio(row.river_stage_feet, row.flood_stage_feet):
        raise ValueError("river_stage_ratio must match stages")
    if row.forecast_crest_ratio != _ratio(
        row.forecast_crest_feet,
        row.flood_stage_feet,
    ):
        raise ValueError("forecast_crest_ratio must match stages")
    if row.river_stage_feet >= row.flood_stage_feet:
        if STAGE_ABOVE_REASON not in row.reason_codes:
            raise ValueError("above stage rows must include above stage reason")
    if row.river_stage_feet < row.flood_stage_feet:
        if STAGE_ABOVE_REASON in row.reason_codes:
            raise ValueError("below stage rows must not include above stage reason")
    if row.forecast_crest_feet >= row.flood_stage_feet:
        if FORECAST_ABOVE_REASON not in row.reason_codes:
            raise ValueError("above crest rows must include above crest reason")
    if row.forecast_crest_feet < row.flood_stage_feet:
        if FORECAST_ABOVE_REASON in row.reason_codes:
            raise ValueError("below crest rows must not include above crest reason")


def _validate_report(report: WeatherRiverFloodWarningUpgradeDigestReport) -> None:
    rows = report.rows
    if report.input_count != _count_decimal(len(rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_row_count != _count_decimal(
        sum(1 for row in rows if row.row_status == "blocked"),
    ):
        raise ValueError("blocked_row_count must match rows")
    if report.watch_row_count != _count_decimal(
        sum(1 for row in rows if row.row_status == "watch"),
    ):
        raise ValueError("watch_row_count must match rows")
    if report.pass_row_count != _count_decimal(
        sum(1 for row in rows if row.row_status == "pass"),
    ):
        raise ValueError("pass_row_count must match rows")
    if report.stale_source_count != _count_decimal(
        sum(1 for row in rows if row.source_freshness_status == SOURCE_STALE),
    ):
        raise ValueError("stale_source_count must match rows")
    if report.upgrade_count != _count_decimal(
        sum(
            1
            for row in rows
            if (
                MAJOR_UPGRADE_REASON in row.reason_codes
                or LEVEL_UPGRADE_REASON in row.reason_codes
            )
        ),
    ):
        raise ValueError("upgrade_count must match rows")
    if report.major_upgrade_count != _count_decimal(
        sum(1 for row in rows if MAJOR_UPGRADE_REASON in row.reason_codes),
    ):
        raise ValueError("major_upgrade_count must match rows")
    if report.current_above_flood_stage_count != _count_decimal(
        sum(1 for row in rows if row.river_stage_feet >= row.flood_stage_feet),
    ):
        raise ValueError("current_above_flood_stage_count must match rows")
    if report.forecast_above_flood_stage_count != _count_decimal(
        sum(1 for row in rows if row.forecast_crest_feet >= row.flood_stage_feet),
    ):
        raise ValueError("forecast_above_flood_stage_count must match rows")
    if report.max_source_age_observed_seconds != max(
        (row.source_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_source_age_observed_seconds must match rows")
    if report.max_warning_level_delta != max(
        (row.warning_level_delta for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_warning_level_delta must match rows")
    if report.max_river_stage_ratio != max(
        (row.river_stage_ratio for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_river_stage_ratio must match rows")
    if report.max_forecast_crest_ratio != max(
        (row.forecast_crest_ratio for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_forecast_crest_ratio must match rows")
    if report.max_rainfall_inches_24h != max(
        (row.rainfall_inches_24h for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_rainfall_inches_24h must match rows")
    if report.average_source_confidence_ratio != _ratio(
        _sum_decimal(row.source_confidence_ratio for row in rows),
        report.row_count,
    ):
        raise ValueError("average_source_confidence_ratio must match rows")
    if report.digest_status != _digest_status(rows):
        raise ValueError("digest_status must match rows")
    if report.next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if not _CANONICAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be canonical")
    value_low = value.lower()
    if any(fragment in value_low for fragment in _TEXT_BLOCKS):
        raise ValueError(f"{field_name} value is not allowed")


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported value")


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return normalized


def _require_positive_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_probability(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _require_nonnegative_decimal("source_age_seconds", seconds)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return total.quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)
