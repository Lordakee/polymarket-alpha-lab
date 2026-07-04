"""Pure Phase 1 weather winter storm airport digest reducer."""

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


DEFAULT_WEATHER_WINTER_STORM_AIRPORT_DIGEST_CONFIG_VERSION = (
    "market-research-weather-winter-storm-airport-digest-v0"
)

SOURCE_CURRENT = "current"
SOURCE_STALE = "stale"

ROW_STATUSES = ("pass", "watch", "blocked")
SOURCE_STATUSES = (SOURCE_CURRENT, SOURCE_STALE)

SOURCE_STALE_REASON = "weather_winter_storm_airport_source_stale"
GROUND_STOP_SPIKE_REASON = "weather_winter_storm_airport_ground_stop_spike"
DEPARTURE_DELAY_SURGE_REASON = "weather_winter_storm_airport_departure_delay_surge"
ARRIVAL_DELAY_SURGE_REASON = "weather_winter_storm_airport_arrival_delay_surge"
HEAVY_SNOWFALL_REASON = "weather_winter_storm_airport_heavy_snowfall"
ICING_RISK_REASON = "weather_winter_storm_airport_icing_risk"
DEICING_QUEUE_REASON = "weather_winter_storm_airport_deicing_queue_pressure"
GROUND_STOP_WATCH_REASON = "weather_winter_storm_airport_ground_stop_watch"
DEPARTURE_DELAY_WATCH_REASON = "weather_winter_storm_airport_departure_delay_watch"
ARRIVAL_DELAY_WATCH_REASON = "weather_winter_storm_airport_arrival_delay_watch"
LOW_RUNWAY_CLEAR_REASON = "weather_winter_storm_airport_low_runway_clear_score"
ROW_CLEAR_REASON = "weather_winter_storm_airport_row_clear"
DIGEST_CLEAR_REASON = "weather_winter_storm_airport_digest_clear"
DIGEST_EMPTY_REASON = "weather_winter_storm_airport_digest_empty"

ROW_REASON_CODES = (
    SOURCE_STALE_REASON,
    GROUND_STOP_SPIKE_REASON,
    DEPARTURE_DELAY_SURGE_REASON,
    ARRIVAL_DELAY_SURGE_REASON,
    HEAVY_SNOWFALL_REASON,
    ICING_RISK_REASON,
    DEICING_QUEUE_REASON,
    GROUND_STOP_WATCH_REASON,
    DEPARTURE_DELAY_WATCH_REASON,
    ARRIVAL_DELAY_WATCH_REASON,
    LOW_RUNWAY_CLEAR_REASON,
    ROW_CLEAR_REASON,
)
REPORT_REASON_CODES = (
    SOURCE_STALE_REASON,
    GROUND_STOP_SPIKE_REASON,
    DEPARTURE_DELAY_SURGE_REASON,
    ARRIVAL_DELAY_SURGE_REASON,
    HEAVY_SNOWFALL_REASON,
    ICING_RISK_REASON,
    DEICING_QUEUE_REASON,
    GROUND_STOP_WATCH_REASON,
    DEPARTURE_DELAY_WATCH_REASON,
    ARRIVAL_DELAY_WATCH_REASON,
    LOW_RUNWAY_CLEAR_REASON,
    DIGEST_CLEAR_REASON,
    DIGEST_EMPTY_REASON,
)

NEXT_STEPS = {
    "pass": "continue_report_only_weather_winter_storm_airport_digest",
    "watch": "monitor_report_only_weather_winter_storm_airport_digest",
    "blocked": "block_report_only_weather_winter_storm_airport_digest",
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
    "DEFAULT_WEATHER_WINTER_STORM_AIRPORT_DIGEST_CONFIG_VERSION",
    "WeatherWinterStormAirportDigestConfig",
    "WeatherWinterStormAirportObservation",
    "WeatherWinterStormAirportDigestRow",
    "WeatherWinterStormAirportReasonCodeCount",
    "WeatherWinterStormAirportDigestReport",
    "build_market_research_weather_winter_storm_airport_digest",
    "market_research_weather_winter_storm_airport_digest_json",
)


@dataclass(frozen=True)
class WeatherWinterStormAirportDigestConfig:
    config_version: str = DEFAULT_WEATHER_WINTER_STORM_AIRPORT_DIGEST_CONFIG_VERSION
    max_source_age_seconds: Decimal = Decimal("3600.000000")
    watch_ground_stop_ratio: Decimal = Decimal("0.100000")
    blocked_ground_stop_ratio: Decimal = Decimal("0.400000")
    watch_delay_minutes: Decimal = Decimal("45.000000")
    blocked_delay_minutes: Decimal = Decimal("180.000000")
    heavy_snowfall_inches_12h: Decimal = Decimal("6.000000")
    ice_accretion_inches: Decimal = Decimal("0.150000")
    high_deicing_queue_minutes: Decimal = Decimal("45.000000")
    low_runway_clear_score: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherWinterStormAirportDigestConfig:
            raise TypeError(
                "WeatherWinterStormAirportDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherWinterStormAirportDigestConfig:
            raise ValueError(
                "config must be exactly WeatherWinterStormAirportDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_WEATHER_WINTER_STORM_AIRPORT_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_source_age_seconds",
            "watch_delay_minutes",
            "blocked_delay_minutes",
            "heavy_snowfall_inches_12h",
            "ice_accretion_inches",
            "high_deicing_queue_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_ground_stop_ratio",
            "blocked_ground_stop_ratio",
            "low_runway_clear_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        if self.blocked_ground_stop_ratio < self.watch_ground_stop_ratio:
            raise ValueError("blocked_ground_stop_ratio must be at least watch threshold")
        if self.blocked_delay_minutes < self.watch_delay_minutes:
            raise ValueError("blocked_delay_minutes must be at least watch threshold")
        require_paper_only_flags("WeatherWinterStormAirportDigestConfig", self)


@dataclass(frozen=True)
class WeatherWinterStormAirportObservation:
    airport_id: str
    event_id: str
    source_id: str
    observed_at: datetime
    ground_stop_ratio: Decimal
    departure_delay_minutes: Decimal
    arrival_delay_minutes: Decimal
    snowfall_inches_12h: Decimal
    ice_accretion_inches: Decimal
    deicing_queue_minutes: Decimal
    runway_clear_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherWinterStormAirportObservation:
            raise TypeError(
                "WeatherWinterStormAirportObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherWinterStormAirportObservation:
            raise ValueError(
                "observation must be exactly WeatherWinterStormAirportObservation",
            )
        for field_name in ("airport_id", "event_id", "source_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "departure_delay_minutes",
            "arrival_delay_minutes",
            "snowfall_inches_12h",
            "ice_accretion_inches",
            "deicing_queue_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("ground_stop_ratio", "runway_clear_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("WeatherWinterStormAirportObservation", self)


@dataclass(frozen=True)
class WeatherWinterStormAirportDigestRow:
    airport_id: str
    event_id: str
    source_id: str
    observed_at: datetime
    source_age_seconds: Decimal
    source_freshness_status: str
    ground_stop_ratio: Decimal
    departure_delay_minutes: Decimal
    arrival_delay_minutes: Decimal
    snowfall_inches_12h: Decimal
    ice_accretion_inches: Decimal
    deicing_queue_minutes: Decimal
    runway_clear_score: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherWinterStormAirportDigestRow:
            raise TypeError(
                "WeatherWinterStormAirportDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherWinterStormAirportDigestRow:
            raise ValueError("row must be exactly WeatherWinterStormAirportDigestRow")
        for field_name in ("airport_id", "event_id", "source_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_age_seconds",
            "departure_delay_minutes",
            "arrival_delay_minutes",
            "snowfall_inches_12h",
            "ice_accretion_inches",
            "deicing_queue_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("ground_stop_ratio", "runway_clear_score"):
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
        _require_member("row_status", self.row_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("weather winter storm airport row", self)
        require_paper_only_flags("WeatherWinterStormAirportDigestRow", self)


@dataclass(frozen=True)
class WeatherWinterStormAirportReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherWinterStormAirportReasonCodeCount:
            raise TypeError(
                "WeatherWinterStormAirportReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherWinterStormAirportReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly WeatherWinterStormAirportReasonCodeCount",
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
        reject_unsafe_surface_fields("weather winter storm airport reason code count", self)
        require_paper_only_flags("WeatherWinterStormAirportReasonCodeCount", self)


@dataclass(frozen=True)
class WeatherWinterStormAirportDigestReport:
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
    max_ground_stop_ratio: Decimal
    max_departure_delay_minutes: Decimal
    max_arrival_delay_minutes: Decimal
    max_deicing_queue_minutes: Decimal
    max_snowfall_inches_12h: Decimal
    max_ice_accretion_inches: Decimal
    max_source_age_seconds: Decimal
    max_source_age_observed_seconds: Decimal
    average_runway_clear_score: Decimal
    rows: tuple[WeatherWinterStormAirportDigestRow, ...]
    reason_code_counts: tuple[WeatherWinterStormAirportReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherWinterStormAirportDigestReport:
            raise TypeError(
                "WeatherWinterStormAirportDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherWinterStormAirportDigestReport:
            raise ValueError("report must be exactly WeatherWinterStormAirportDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_WEATHER_WINTER_STORM_AIRPORT_DIGEST_CONFIG_VERSION:
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
            "max_departure_delay_minutes",
            "max_arrival_delay_minutes",
            "max_deicing_queue_minutes",
            "max_snowfall_inches_12h",
            "max_ice_accretion_inches",
            "max_source_age_seconds",
            "max_source_age_observed_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_ground_stop_ratio", "average_runway_clear_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
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
        reject_unsafe_surface_fields("weather winter storm airport report", self)
        require_paper_only_flags("WeatherWinterStormAirportDigestReport", self)


def build_market_research_weather_winter_storm_airport_digest(
    observations: Iterable[WeatherWinterStormAirportObservation],
    *,
    config: WeatherWinterStormAirportDigestConfig,
    generated_at: datetime,
) -> WeatherWinterStormAirportDigestReport:
    if type(config) is not WeatherWinterStormAirportDigestConfig:
        raise ValueError("config must be exactly WeatherWinterStormAirportDigestConfig")
    require_paper_only_flags("WeatherWinterStormAirportDigestConfig", config)
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

    return WeatherWinterStormAirportDigestReport(
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
        max_ground_stop_ratio=max(
            (row.ground_stop_ratio for row in sorted_rows),
            default=ZERO,
        ),
        max_departure_delay_minutes=max(
            (row.departure_delay_minutes for row in sorted_rows),
            default=ZERO,
        ),
        max_arrival_delay_minutes=max(
            (row.arrival_delay_minutes for row in sorted_rows),
            default=ZERO,
        ),
        max_deicing_queue_minutes=max(
            (row.deicing_queue_minutes for row in sorted_rows),
            default=ZERO,
        ),
        max_snowfall_inches_12h=max(
            (row.snowfall_inches_12h for row in sorted_rows),
            default=ZERO,
        ),
        max_ice_accretion_inches=max(
            (row.ice_accretion_inches for row in sorted_rows),
            default=ZERO,
        ),
        max_source_age_seconds=config.max_source_age_seconds,
        max_source_age_observed_seconds=max(
            (row.source_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        average_runway_clear_score=_ratio(
            _sum_decimal(row.runway_clear_score for row in sorted_rows),
            row_count,
        ),
        rows=sorted_rows,
        reason_code_counts=_reason_code_counts(reason_codes, sorted_rows),
        reason_codes=reason_codes,
    )


def market_research_weather_winter_storm_airport_digest_json(
    report: WeatherWinterStormAirportDigestReport,
) -> dict[str, Any]:
    if type(report) is not WeatherWinterStormAirportDigestReport:
        raise ValueError("report must be exactly WeatherWinterStormAirportDigestReport")
    reject_unsafe_surface_fields("weather winter storm airport report", report)
    value = json_ready_no_floats(asdict(report))
    if not isinstance(value, dict):
        raise ValueError("report JSON value must be an object")
    reject_unsafe_surface_fields("weather winter storm airport JSON value", value)
    return value


def _row_for_observation(
    observation: WeatherWinterStormAirportObservation,
    *,
    config: WeatherWinterStormAirportDigestConfig,
    generated_at: datetime,
) -> WeatherWinterStormAirportDigestRow:
    source_age_seconds = _age_seconds(generated_at, observation.observed_at)
    source_freshness_status = (
        SOURCE_STALE
        if source_age_seconds > config.max_source_age_seconds
        else SOURCE_CURRENT
    )
    reason_codes = _row_reason_codes(
        source_freshness_status=source_freshness_status,
        ground_stop_ratio=observation.ground_stop_ratio,
        departure_delay_minutes=observation.departure_delay_minutes,
        arrival_delay_minutes=observation.arrival_delay_minutes,
        snowfall_inches_12h=observation.snowfall_inches_12h,
        ice_accretion_inches=observation.ice_accretion_inches,
        deicing_queue_minutes=observation.deicing_queue_minutes,
        runway_clear_score=observation.runway_clear_score,
        config=config,
    )
    return WeatherWinterStormAirportDigestRow(
        airport_id=observation.airport_id,
        event_id=observation.event_id,
        source_id=observation.source_id,
        observed_at=observation.observed_at,
        source_age_seconds=source_age_seconds,
        source_freshness_status=source_freshness_status,
        ground_stop_ratio=observation.ground_stop_ratio,
        departure_delay_minutes=observation.departure_delay_minutes,
        arrival_delay_minutes=observation.arrival_delay_minutes,
        snowfall_inches_12h=observation.snowfall_inches_12h,
        ice_accretion_inches=observation.ice_accretion_inches,
        deicing_queue_minutes=observation.deicing_queue_minutes,
        runway_clear_score=observation.runway_clear_score,
        row_status=_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_freshness_status: str,
    ground_stop_ratio: Decimal,
    departure_delay_minutes: Decimal,
    arrival_delay_minutes: Decimal,
    snowfall_inches_12h: Decimal,
    ice_accretion_inches: Decimal,
    deicing_queue_minutes: Decimal,
    runway_clear_score: Decimal,
    config: WeatherWinterStormAirportDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source_freshness_status == SOURCE_STALE:
        reasons.append(SOURCE_STALE_REASON)
    if ground_stop_ratio >= config.blocked_ground_stop_ratio:
        reasons.append(GROUND_STOP_SPIKE_REASON)
    elif ground_stop_ratio >= config.watch_ground_stop_ratio:
        reasons.append(GROUND_STOP_WATCH_REASON)
    if departure_delay_minutes >= config.blocked_delay_minutes:
        reasons.append(DEPARTURE_DELAY_SURGE_REASON)
    elif departure_delay_minutes >= config.watch_delay_minutes:
        reasons.append(DEPARTURE_DELAY_WATCH_REASON)
    if arrival_delay_minutes >= config.blocked_delay_minutes:
        reasons.append(ARRIVAL_DELAY_SURGE_REASON)
    elif arrival_delay_minutes >= config.watch_delay_minutes:
        reasons.append(ARRIVAL_DELAY_WATCH_REASON)
    if snowfall_inches_12h >= config.heavy_snowfall_inches_12h:
        reasons.append(HEAVY_SNOWFALL_REASON)
    if ice_accretion_inches >= config.ice_accretion_inches:
        reasons.append(ICING_RISK_REASON)
    if deicing_queue_minutes >= config.high_deicing_queue_minutes:
        reasons.append(DEICING_QUEUE_REASON)
    if runway_clear_score <= config.low_runway_clear_score:
        reasons.append(LOW_RUNWAY_CLEAR_REASON)
    if not reasons:
        reasons.append(ROW_CLEAR_REASON)
    return _sort_reason_codes(tuple(reasons), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[WeatherWinterStormAirportDigestRow, ...],
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
    rows: tuple[WeatherWinterStormAirportDigestRow, ...],
) -> tuple[WeatherWinterStormAirportReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == (DIGEST_EMPTY_REASON,):
        return (
            WeatherWinterStormAirportReasonCodeCount(
                reason_code=DIGEST_EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    if reason_codes == (DIGEST_CLEAR_REASON,):
        return (
            WeatherWinterStormAirportReasonCodeCount(
                reason_code=DIGEST_CLEAR_REASON,
                count=row_count,
                row_ratio=ONE,
            ),
        )
    return tuple(
        WeatherWinterStormAirportReasonCodeCount(
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
        GROUND_STOP_SPIKE_REASON in reason_codes
        or DEPARTURE_DELAY_SURGE_REASON in reason_codes
        or ARRIVAL_DELAY_SURGE_REASON in reason_codes
    ):
        return "blocked"
    if reason_codes == (ROW_CLEAR_REASON,):
        return "pass"
    return "watch"


def _digest_status(rows: tuple[WeatherWinterStormAirportDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_observations(
    observations: Iterable[WeatherWinterStormAirportObservation],
    *,
    generated_at: datetime,
) -> tuple[WeatherWinterStormAirportObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError(
            "observations must be an iterable of WeatherWinterStormAirportObservation",
        )
    rows = tuple(observations)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not WeatherWinterStormAirportObservation:
            raise ValueError("observations must contain WeatherWinterStormAirportObservation")
        require_paper_only_flags("WeatherWinterStormAirportObservation", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (row.airport_id, row.event_id)
        if key in seen_keys:
            raise ValueError("event_id values must be unique per airport_id")
        seen_keys.add(key)
    return tuple(sorted(rows, key=lambda row: (row.airport_id, row.event_id, row.source_id)))


def _normalize_rows(
    rows: tuple[WeatherWinterStormAirportDigestRow, ...],
) -> tuple[WeatherWinterStormAirportDigestRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not WeatherWinterStormAirportDigestRow:
            raise ValueError("rows must contain WeatherWinterStormAirportDigestRow")
        require_paper_only_flags("WeatherWinterStormAirportDigestRow", row)
    normalized = tuple(sorted(rows, key=_row_sort_key))
    if rows != normalized:
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[WeatherWinterStormAirportReasonCodeCount, ...],
) -> tuple[WeatherWinterStormAirportReasonCodeCount, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not WeatherWinterStormAirportReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain WeatherWinterStormAirportReasonCodeCount",
            )
        require_paper_only_flags("WeatherWinterStormAirportReasonCodeCount", row)
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


def _row_sort_key(row: WeatherWinterStormAirportDigestRow) -> tuple[Decimal | str, ...]:
    return (
        STATUS_RANK[row.row_status],
        -row.ground_stop_ratio,
        -row.departure_delay_minutes,
        -row.arrival_delay_minutes,
        -row.deicing_queue_minutes,
        row.airport_id,
        row.event_id,
        row.source_id,
    )


def _reason_sort_key(reason_code: str) -> Decimal:
    return REASON_RANK[reason_code]


def _validate_row(row: WeatherWinterStormAirportDigestRow) -> None:
    expected_status = _status_for_reason_codes(row.reason_codes)
    if row.row_status != expected_status:
        raise ValueError("row_status must match reason_codes")
    if row.source_freshness_status == SOURCE_STALE:
        if SOURCE_STALE_REASON not in row.reason_codes:
            raise ValueError("stale source rows must include stale reason")
    if row.source_freshness_status == SOURCE_CURRENT:
        if SOURCE_STALE_REASON in row.reason_codes:
            raise ValueError("current source rows must not include stale reason")


def _validate_report(report: WeatherWinterStormAirportDigestReport) -> None:
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
    if report.max_ground_stop_ratio != max(
        (row.ground_stop_ratio for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_ground_stop_ratio must match rows")
    if report.max_departure_delay_minutes != max(
        (row.departure_delay_minutes for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_departure_delay_minutes must match rows")
    if report.max_arrival_delay_minutes != max(
        (row.arrival_delay_minutes for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_arrival_delay_minutes must match rows")
    if report.max_deicing_queue_minutes != max(
        (row.deicing_queue_minutes for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_deicing_queue_minutes must match rows")
    if report.max_snowfall_inches_12h != max(
        (row.snowfall_inches_12h for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_snowfall_inches_12h must match rows")
    if report.max_ice_accretion_inches != max(
        (row.ice_accretion_inches for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_ice_accretion_inches must match rows")
    if report.max_source_age_observed_seconds != max(
        (row.source_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_source_age_observed_seconds must match rows")
    if report.average_runway_clear_score != _ratio(
        _sum_decimal(row.runway_clear_score for row in rows),
        report.row_count,
    ):
        raise ValueError("average_runway_clear_score must match rows")
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
    lowered = value.lower()
    if any(fragment in lowered for fragment in _TEXT_BLOCKS):
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
