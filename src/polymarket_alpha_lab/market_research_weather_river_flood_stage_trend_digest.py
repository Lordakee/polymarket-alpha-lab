"""Pure Phase 1 weather river flood stage trend digest reducer."""

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


DEFAULT_WEATHER_RIVER_FLOOD_STAGE_TREND_DIGEST_CONFIG_VERSION = (
    "market-research-weather-river-flood-stage-trend-digest-v0"
)

OBSERVATION_CURRENT = "current"
OBSERVATION_STALE = "stale"

ROW_STATUSES = ("pass", "watch", "blocked")
OBSERVATION_STATUSES = (OBSERVATION_CURRENT, OBSERVATION_STALE)

OBSERVATION_STALE_REASON = "weather_river_flood_stage_trend_observation_stale"
STAGE_EXCEEDS_FLOOD_REASON = (
    "weather_river_flood_stage_trend_stage_exceeds_flood"
)
FORECAST_CREST_EXCEEDS_FLOOD_REASON = (
    "weather_river_flood_stage_trend_forecast_crest_exceeds_flood"
)
STAGE_RISE_BLOCKED_REASON = "weather_river_flood_stage_trend_stage_rise_blocked"
STAGE_RISE_WATCH_REASON = "weather_river_flood_stage_trend_stage_rise_watch"
CREST_REVISION_BLOCKED_REASON = (
    "weather_river_flood_stage_trend_crest_revision_blocked"
)
CREST_REVISION_WATCH_REASON = (
    "weather_river_flood_stage_trend_crest_revision_watch"
)
NEAR_FLOOD_STAGE_REASON = "weather_river_flood_stage_trend_near_flood_stage"
LOW_CONFIDENCE_REASON = "weather_river_flood_stage_trend_low_confidence"
ROW_CLEAR_REASON = "weather_river_flood_stage_trend_row_clear"
DIGEST_CLEAR_REASON = "weather_river_flood_stage_trend_digest_clear"
DIGEST_EMPTY_REASON = "weather_river_flood_stage_trend_digest_empty"

ROW_REASON_CODES = (
    OBSERVATION_STALE_REASON,
    STAGE_EXCEEDS_FLOOD_REASON,
    FORECAST_CREST_EXCEEDS_FLOOD_REASON,
    STAGE_RISE_BLOCKED_REASON,
    CREST_REVISION_BLOCKED_REASON,
    STAGE_RISE_WATCH_REASON,
    CREST_REVISION_WATCH_REASON,
    NEAR_FLOOD_STAGE_REASON,
    LOW_CONFIDENCE_REASON,
    ROW_CLEAR_REASON,
)
REPORT_REASON_CODES = (
    OBSERVATION_STALE_REASON,
    STAGE_EXCEEDS_FLOOD_REASON,
    FORECAST_CREST_EXCEEDS_FLOOD_REASON,
    STAGE_RISE_BLOCKED_REASON,
    CREST_REVISION_BLOCKED_REASON,
    STAGE_RISE_WATCH_REASON,
    CREST_REVISION_WATCH_REASON,
    NEAR_FLOOD_STAGE_REASON,
    LOW_CONFIDENCE_REASON,
    DIGEST_CLEAR_REASON,
    DIGEST_EMPTY_REASON,
)
BLOCKED_REASON_CODES = (
    STAGE_EXCEEDS_FLOOD_REASON,
    FORECAST_CREST_EXCEEDS_FLOOD_REASON,
    STAGE_RISE_BLOCKED_REASON,
    CREST_REVISION_BLOCKED_REASON,
)

NEXT_STEPS = {
    "pass": "continue_report_only_weather_river_flood_stage_trend_digest",
    "watch": "monitor_report_only_weather_river_flood_stage_trend_digest",
    "blocked": "block_report_only_weather_river_flood_stage_trend_digest",
}
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
REASON_RANK = {
    reason_code: Decimal(index).quantize(QUANT)
    for index, reason_code in enumerate(REPORT_REASON_CODES + (ROW_CLEAR_REASON,))
}
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
    "DEFAULT_WEATHER_RIVER_FLOOD_STAGE_TREND_DIGEST_CONFIG_VERSION",
    "WeatherRiverFloodStageTrendDigestConfig",
    "WeatherRiverFloodStageTrendObservation",
    "WeatherRiverFloodStageTrendDigestRow",
    "WeatherRiverFloodStageTrendReasonCodeCount",
    "WeatherRiverFloodStageTrendDigestReport",
    "build_market_research_weather_river_flood_stage_trend_digest",
    "market_research_weather_river_flood_stage_trend_digest_json",
)


@dataclass(frozen=True)
class WeatherRiverFloodStageTrendDigestConfig:
    config_version: str = DEFAULT_WEATHER_RIVER_FLOOD_STAGE_TREND_DIGEST_CONFIG_VERSION
    max_observation_age_seconds: Decimal = Decimal("3600.000000")
    near_flood_stage_margin_ft: Decimal = Decimal("1.000000")
    stage_rise_watch_ft: Decimal = Decimal("0.500000")
    stage_rise_blocked_ft: Decimal = Decimal("2.000000")
    forecast_crest_revision_watch_ft: Decimal = Decimal("0.500000")
    forecast_crest_revision_blocked_ft: Decimal = Decimal("1.500000")
    low_confidence_ratio: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherRiverFloodStageTrendDigestConfig:
            raise TypeError(
                "WeatherRiverFloodStageTrendDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherRiverFloodStageTrendDigestConfig:
            raise ValueError(
                "config must be exactly WeatherRiverFloodStageTrendDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_WEATHER_RIVER_FLOOD_STAGE_TREND_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_observation_age_seconds",
            "near_flood_stage_margin_ft",
            "stage_rise_watch_ft",
            "stage_rise_blocked_ft",
            "forecast_crest_revision_watch_ft",
            "forecast_crest_revision_blocked_ft",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "low_confidence_ratio",
            _require_probability("low_confidence_ratio", self.low_confidence_ratio),
        )
        if self.stage_rise_blocked_ft < self.stage_rise_watch_ft:
            raise ValueError(
                "stage_rise_blocked_ft must be at least stage_rise_watch_ft",
            )
        if (
            self.forecast_crest_revision_blocked_ft
            < self.forecast_crest_revision_watch_ft
        ):
            raise ValueError(
                "forecast_crest_revision_blocked_ft must be at least "
                "forecast_crest_revision_watch_ft",
            )
        require_paper_only_flags("WeatherRiverFloodStageTrendDigestConfig", self)


@dataclass(frozen=True)
class WeatherRiverFloodStageTrendObservation:
    gauge_id: str
    river_id: str
    market_slug: str
    source_id: str
    observed_at: datetime
    forecast_valid_at: datetime
    current_stage_ft: Decimal
    previous_stage_ft: Decimal
    flood_stage_ft: Decimal
    forecast_crest_ft: Decimal
    previous_forecast_crest_ft: Decimal
    forecast_confidence_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherRiverFloodStageTrendObservation:
            raise TypeError(
                "WeatherRiverFloodStageTrendObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherRiverFloodStageTrendObservation:
            raise ValueError(
                "observation must be exactly WeatherRiverFloodStageTrendObservation",
            )
        for field_name in ("gauge_id", "river_id", "market_slug", "source_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "forecast_valid_at",
            _as_utc("forecast_valid_at", self.forecast_valid_at),
        )
        if self.forecast_valid_at < self.observed_at:
            raise ValueError("forecast_valid_at must not be before observed_at")
        for field_name in (
            "current_stage_ft",
            "previous_stage_ft",
            "forecast_crest_ft",
            "previous_forecast_crest_ft",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "flood_stage_ft",
            _require_positive_decimal("flood_stage_ft", self.flood_stage_ft),
        )
        object.__setattr__(
            self,
            "forecast_confidence_ratio",
            _require_probability(
                "forecast_confidence_ratio",
                self.forecast_confidence_ratio,
            ),
        )
        require_paper_only_flags("WeatherRiverFloodStageTrendObservation", self)


@dataclass(frozen=True)
class WeatherRiverFloodStageTrendDigestRow:
    gauge_id: str
    river_id: str
    market_slug: str
    source_id: str
    observed_at: datetime
    forecast_valid_at: datetime
    observation_age_seconds: Decimal
    observation_freshness_status: str
    current_stage_ft: Decimal
    previous_stage_ft: Decimal
    flood_stage_ft: Decimal
    forecast_crest_ft: Decimal
    previous_forecast_crest_ft: Decimal
    stage_delta_ft: Decimal
    stage_vs_flood_ft: Decimal
    forecast_crest_vs_flood_ft: Decimal
    forecast_crest_revision_ft: Decimal
    forecast_confidence_ratio: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherRiverFloodStageTrendDigestRow:
            raise TypeError(
                "WeatherRiverFloodStageTrendDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherRiverFloodStageTrendDigestRow:
            raise ValueError(
                "row must be exactly WeatherRiverFloodStageTrendDigestRow",
            )
        for field_name in ("gauge_id", "river_id", "market_slug", "source_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "forecast_valid_at",
            _as_utc("forecast_valid_at", self.forecast_valid_at),
        )
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        _require_member(
            "observation_freshness_status",
            self.observation_freshness_status,
            OBSERVATION_STATUSES,
        )
        for field_name in (
            "current_stage_ft",
            "previous_stage_ft",
            "forecast_crest_ft",
            "previous_forecast_crest_ft",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "flood_stage_ft",
            _require_positive_decimal("flood_stage_ft", self.flood_stage_ft),
        )
        for field_name in (
            "stage_delta_ft",
            "stage_vs_flood_ft",
            "forecast_crest_vs_flood_ft",
            "forecast_crest_revision_ft",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "forecast_confidence_ratio",
            _require_probability(
                "forecast_confidence_ratio",
                self.forecast_confidence_ratio,
            ),
        )
        _require_member("row_status", self.row_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("weather river flood stage trend row", self)
        require_paper_only_flags("WeatherRiverFloodStageTrendDigestRow", self)


@dataclass(frozen=True)
class WeatherRiverFloodStageTrendReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherRiverFloodStageTrendReasonCodeCount:
            raise TypeError(
                "WeatherRiverFloodStageTrendReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherRiverFloodStageTrendReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "WeatherRiverFloodStageTrendReasonCodeCount",
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
            "weather river flood stage trend reason code count",
            self,
        )
        require_paper_only_flags("WeatherRiverFloodStageTrendReasonCodeCount", self)


@dataclass(frozen=True)
class WeatherRiverFloodStageTrendDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    input_count: Decimal
    row_count: Decimal
    blocked_row_count: Decimal
    watch_row_count: Decimal
    pass_row_count: Decimal
    stale_observation_count: Decimal
    flood_stage_exceedance_count: Decimal
    crest_exceedance_count: Decimal
    max_observation_age_seconds: Decimal
    max_observation_age_observed_seconds: Decimal
    max_current_stage_ft: Decimal
    max_stage_vs_flood_ft: Decimal
    max_forecast_crest_vs_flood_ft: Decimal
    max_stage_delta_ft: Decimal
    max_forecast_crest_revision_ft: Decimal
    average_forecast_confidence_ratio: Decimal
    rows: tuple[WeatherRiverFloodStageTrendDigestRow, ...]
    reason_code_counts: tuple[WeatherRiverFloodStageTrendReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherRiverFloodStageTrendDigestReport:
            raise TypeError(
                "WeatherRiverFloodStageTrendDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherRiverFloodStageTrendDigestReport:
            raise ValueError(
                "report must be exactly WeatherRiverFloodStageTrendDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_WEATHER_RIVER_FLOOD_STAGE_TREND_DIGEST_CONFIG_VERSION
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
            "stale_observation_count",
            "flood_stage_exceedance_count",
            "crest_exceedance_count",
            "max_observation_age_seconds",
            "max_observation_age_observed_seconds",
            "max_current_stage_ft",
            "average_forecast_confidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_stage_vs_flood_ft",
            "max_forecast_crest_vs_flood_ft",
            "max_stage_delta_ft",
            "max_forecast_crest_revision_ft",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
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
        reject_unsafe_surface_fields("weather river flood stage trend report", self)
        require_paper_only_flags("WeatherRiverFloodStageTrendDigestReport", self)


def build_market_research_weather_river_flood_stage_trend_digest(
    observations: Iterable[WeatherRiverFloodStageTrendObservation],
    *,
    config: WeatherRiverFloodStageTrendDigestConfig,
    generated_at: datetime,
) -> WeatherRiverFloodStageTrendDigestReport:
    if type(config) is not WeatherRiverFloodStageTrendDigestConfig:
        raise ValueError(
            "config must be exactly WeatherRiverFloodStageTrendDigestConfig",
        )
    require_paper_only_flags("WeatherRiverFloodStageTrendDigestConfig", config)
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
    sorted_rows = tuple(sorted(rows, key=_row_sort_fields))
    reason_codes = _report_reason_codes(sorted_rows)
    digest_status = _digest_status(sorted_rows)
    row_count = _count_decimal(len(sorted_rows))

    return WeatherRiverFloodStageTrendDigestReport(
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
        stale_observation_count=_count_decimal(
            sum(
                1
                for row in sorted_rows
                if row.observation_freshness_status == OBSERVATION_STALE
            ),
        ),
        flood_stage_exceedance_count=_count_decimal(
            sum(1 for row in sorted_rows if row.stage_vs_flood_ft >= ZERO),
        ),
        crest_exceedance_count=_count_decimal(
            sum(1 for row in sorted_rows if row.forecast_crest_vs_flood_ft >= ZERO),
        ),
        max_observation_age_seconds=config.max_observation_age_seconds,
        max_observation_age_observed_seconds=max(
            (row.observation_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_current_stage_ft=max(
            (row.current_stage_ft for row in sorted_rows),
            default=ZERO,
        ),
        max_stage_vs_flood_ft=max(
            (row.stage_vs_flood_ft for row in sorted_rows),
            default=ZERO,
        ),
        max_forecast_crest_vs_flood_ft=max(
            (row.forecast_crest_vs_flood_ft for row in sorted_rows),
            default=ZERO,
        ),
        max_stage_delta_ft=max(
            (row.stage_delta_ft for row in sorted_rows),
            default=ZERO,
        ),
        max_forecast_crest_revision_ft=max(
            (row.forecast_crest_revision_ft for row in sorted_rows),
            default=ZERO,
        ),
        average_forecast_confidence_ratio=_ratio(
            _sum_decimal(row.forecast_confidence_ratio for row in sorted_rows),
            row_count,
        ),
        rows=sorted_rows,
        reason_code_counts=_reason_code_counts(reason_codes, sorted_rows),
        reason_codes=reason_codes,
    )


def market_research_weather_river_flood_stage_trend_digest_json(
    report: WeatherRiverFloodStageTrendDigestReport,
) -> dict[str, Any]:
    if type(report) is not WeatherRiverFloodStageTrendDigestReport:
        raise ValueError(
            "report must be exactly WeatherRiverFloodStageTrendDigestReport",
        )
    reject_unsafe_surface_fields("weather river flood stage trend report", report)
    value = json_ready_no_floats(asdict(report))
    if not isinstance(value, dict):
        raise ValueError("report JSON value must be an object")
    reject_unsafe_surface_fields("weather river flood stage trend JSON value", value)
    return value


def _row_for_observation(
    observation: WeatherRiverFloodStageTrendObservation,
    *,
    config: WeatherRiverFloodStageTrendDigestConfig,
    generated_at: datetime,
) -> WeatherRiverFloodStageTrendDigestRow:
    observation_age_seconds = _age_seconds(generated_at, observation.observed_at)
    observation_freshness_status = (
        OBSERVATION_STALE
        if observation_age_seconds > config.max_observation_age_seconds
        else OBSERVATION_CURRENT
    )
    stage_delta_ft = _difference_decimal(
        "stage_delta_ft",
        observation.current_stage_ft,
        observation.previous_stage_ft,
    )
    stage_vs_flood_ft = _difference_decimal(
        "stage_vs_flood_ft",
        observation.current_stage_ft,
        observation.flood_stage_ft,
    )
    forecast_crest_vs_flood_ft = _difference_decimal(
        "forecast_crest_vs_flood_ft",
        observation.forecast_crest_ft,
        observation.flood_stage_ft,
    )
    forecast_crest_revision_ft = _difference_decimal(
        "forecast_crest_revision_ft",
        observation.forecast_crest_ft,
        observation.previous_forecast_crest_ft,
    )
    reason_codes = _row_reason_codes(
        observation_freshness_status=observation_freshness_status,
        stage_delta_ft=stage_delta_ft,
        stage_vs_flood_ft=stage_vs_flood_ft,
        forecast_crest_vs_flood_ft=forecast_crest_vs_flood_ft,
        forecast_crest_revision_ft=forecast_crest_revision_ft,
        forecast_confidence_ratio=observation.forecast_confidence_ratio,
        config=config,
    )
    return WeatherRiverFloodStageTrendDigestRow(
        gauge_id=observation.gauge_id,
        river_id=observation.river_id,
        market_slug=observation.market_slug,
        source_id=observation.source_id,
        observed_at=observation.observed_at,
        forecast_valid_at=observation.forecast_valid_at,
        observation_age_seconds=observation_age_seconds,
        observation_freshness_status=observation_freshness_status,
        current_stage_ft=observation.current_stage_ft,
        previous_stage_ft=observation.previous_stage_ft,
        flood_stage_ft=observation.flood_stage_ft,
        forecast_crest_ft=observation.forecast_crest_ft,
        previous_forecast_crest_ft=observation.previous_forecast_crest_ft,
        stage_delta_ft=stage_delta_ft,
        stage_vs_flood_ft=stage_vs_flood_ft,
        forecast_crest_vs_flood_ft=forecast_crest_vs_flood_ft,
        forecast_crest_revision_ft=forecast_crest_revision_ft,
        forecast_confidence_ratio=observation.forecast_confidence_ratio,
        row_status=_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation_freshness_status: str,
    stage_delta_ft: Decimal,
    stage_vs_flood_ft: Decimal,
    forecast_crest_vs_flood_ft: Decimal,
    forecast_crest_revision_ft: Decimal,
    forecast_confidence_ratio: Decimal,
    config: WeatherRiverFloodStageTrendDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if observation_freshness_status == OBSERVATION_STALE:
        reasons.append(OBSERVATION_STALE_REASON)
    if stage_vs_flood_ft >= ZERO:
        reasons.append(STAGE_EXCEEDS_FLOOD_REASON)
    if forecast_crest_vs_flood_ft >= ZERO:
        reasons.append(FORECAST_CREST_EXCEEDS_FLOOD_REASON)
    if stage_delta_ft >= config.stage_rise_blocked_ft:
        reasons.append(STAGE_RISE_BLOCKED_REASON)
    elif stage_delta_ft >= config.stage_rise_watch_ft:
        reasons.append(STAGE_RISE_WATCH_REASON)
    if forecast_crest_revision_ft >= config.forecast_crest_revision_blocked_ft:
        reasons.append(CREST_REVISION_BLOCKED_REASON)
    elif forecast_crest_revision_ft >= config.forecast_crest_revision_watch_ft:
        reasons.append(CREST_REVISION_WATCH_REASON)
    if _near_flood_stage(
        stage_vs_flood_ft=stage_vs_flood_ft,
        forecast_crest_vs_flood_ft=forecast_crest_vs_flood_ft,
        margin_ft=config.near_flood_stage_margin_ft,
    ):
        reasons.append(NEAR_FLOOD_STAGE_REASON)
    if forecast_confidence_ratio <= config.low_confidence_ratio:
        reasons.append(LOW_CONFIDENCE_REASON)
    if not reasons:
        reasons.append(ROW_CLEAR_REASON)
    return _sort_reason_codes(tuple(reasons), ROW_REASON_CODES)


def _near_flood_stage(
    *,
    stage_vs_flood_ft: Decimal,
    forecast_crest_vs_flood_ft: Decimal,
    margin_ft: Decimal,
) -> bool:
    closest_to_flood_ft = max(stage_vs_flood_ft, forecast_crest_vs_flood_ft)
    return closest_to_flood_ft < ZERO and -closest_to_flood_ft <= margin_ft


def _report_reason_codes(
    rows: tuple[WeatherRiverFloodStageTrendDigestRow, ...],
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
    rows: tuple[WeatherRiverFloodStageTrendDigestRow, ...],
) -> tuple[WeatherRiverFloodStageTrendReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == (DIGEST_EMPTY_REASON,):
        return (
            WeatherRiverFloodStageTrendReasonCodeCount(
                reason_code=DIGEST_EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    if reason_codes == (DIGEST_CLEAR_REASON,):
        return (
            WeatherRiverFloodStageTrendReasonCodeCount(
                reason_code=DIGEST_CLEAR_REASON,
                count=row_count,
                row_ratio=ONE,
            ),
        )
    return tuple(
        WeatherRiverFloodStageTrendReasonCodeCount(
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
    if any(reason_code in reason_codes for reason_code in BLOCKED_REASON_CODES):
        return "blocked"
    if reason_codes == (ROW_CLEAR_REASON,):
        return "pass"
    return "watch"


def _digest_status(rows: tuple[WeatherRiverFloodStageTrendDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_observations(
    observations: Iterable[WeatherRiverFloodStageTrendObservation],
    *,
    generated_at: datetime,
) -> tuple[WeatherRiverFloodStageTrendObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError(
            "observations must be an iterable of "
            "WeatherRiverFloodStageTrendObservation",
        )
    rows = tuple(observations)
    seen_pairs: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not WeatherRiverFloodStageTrendObservation:
            raise ValueError(
                "observations must contain WeatherRiverFloodStageTrendObservation",
            )
        require_paper_only_flags("WeatherRiverFloodStageTrendObservation", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        pair = (row.gauge_id, row.market_slug)
        if pair in seen_pairs:
            raise ValueError("gauge_id values must be unique per market_slug")
        seen_pairs.add(pair)
    return tuple(
        sorted(
            rows,
            key=lambda row: (row.market_slug, row.gauge_id, row.river_id, row.source_id),
        ),
    )


def _normalize_rows(
    rows: tuple[WeatherRiverFloodStageTrendDigestRow, ...],
) -> tuple[WeatherRiverFloodStageTrendDigestRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not WeatherRiverFloodStageTrendDigestRow:
            raise ValueError("rows must contain WeatherRiverFloodStageTrendDigestRow")
        require_paper_only_flags("WeatherRiverFloodStageTrendDigestRow", row)
    normalized = tuple(sorted(rows, key=_row_sort_fields))
    if rows != normalized:
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[WeatherRiverFloodStageTrendReasonCodeCount, ...],
) -> tuple[WeatherRiverFloodStageTrendReasonCodeCount, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not WeatherRiverFloodStageTrendReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "WeatherRiverFloodStageTrendReasonCodeCount",
            )
        require_paper_only_flags("WeatherRiverFloodStageTrendReasonCodeCount", row)
    normalized = tuple(sorted(rows, key=lambda row: _reason_sort_fields(row.reason_code)))
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


def _row_sort_fields(
    row: WeatherRiverFloodStageTrendDigestRow,
) -> tuple[Decimal | str, ...]:
    return (
        STATUS_RANK[row.row_status],
        -row.stage_vs_flood_ft,
        -row.forecast_crest_vs_flood_ft,
        -row.stage_delta_ft,
        -row.forecast_crest_revision_ft,
        row.market_slug,
        row.gauge_id,
        row.river_id,
        row.source_id,
    )


def _reason_sort_fields(reason_code: str) -> Decimal:
    return REASON_RANK[reason_code]


def _validate_row(row: WeatherRiverFloodStageTrendDigestRow) -> None:
    expected_status = _status_for_reason_codes(row.reason_codes)
    if row.row_status != expected_status:
        raise ValueError("row_status must match reason_codes")
    if row.observation_freshness_status == OBSERVATION_STALE:
        if OBSERVATION_STALE_REASON not in row.reason_codes:
            raise ValueError("stale observation rows must include stale reason")
    if row.observation_freshness_status == OBSERVATION_CURRENT:
        if OBSERVATION_STALE_REASON in row.reason_codes:
            raise ValueError("current observation rows must not include stale reason")
    if row.forecast_valid_at < row.observed_at:
        raise ValueError("forecast_valid_at must not be before observed_at")
    if row.stage_delta_ft != _difference_decimal(
        "stage_delta_ft",
        row.current_stage_ft,
        row.previous_stage_ft,
    ):
        raise ValueError("stage_delta_ft must match stage fields")
    if row.stage_vs_flood_ft != _difference_decimal(
        "stage_vs_flood_ft",
        row.current_stage_ft,
        row.flood_stage_ft,
    ):
        raise ValueError("stage_vs_flood_ft must match stage fields")
    if row.forecast_crest_vs_flood_ft != _difference_decimal(
        "forecast_crest_vs_flood_ft",
        row.forecast_crest_ft,
        row.flood_stage_ft,
    ):
        raise ValueError("forecast_crest_vs_flood_ft must match stage fields")
    if row.forecast_crest_revision_ft != _difference_decimal(
        "forecast_crest_revision_ft",
        row.forecast_crest_ft,
        row.previous_forecast_crest_ft,
    ):
        raise ValueError("forecast_crest_revision_ft must match stage fields")


def _validate_report(report: WeatherRiverFloodStageTrendDigestReport) -> None:
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
    if report.stale_observation_count != _count_decimal(
        sum(
            1
            for row in rows
            if row.observation_freshness_status == OBSERVATION_STALE
        ),
    ):
        raise ValueError("stale_observation_count must match rows")
    if report.flood_stage_exceedance_count != _count_decimal(
        sum(1 for row in rows if row.stage_vs_flood_ft >= ZERO),
    ):
        raise ValueError("flood_stage_exceedance_count must match rows")
    if report.crest_exceedance_count != _count_decimal(
        sum(1 for row in rows if row.forecast_crest_vs_flood_ft >= ZERO),
    ):
        raise ValueError("crest_exceedance_count must match rows")
    if report.max_observation_age_observed_seconds != max(
        (row.observation_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_observation_age_observed_seconds must match rows")
    if report.max_current_stage_ft != max(
        (row.current_stage_ft for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_current_stage_ft must match rows")
    if report.max_stage_vs_flood_ft != max(
        (row.stage_vs_flood_ft for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_stage_vs_flood_ft must match rows")
    if report.max_forecast_crest_vs_flood_ft != max(
        (row.forecast_crest_vs_flood_ft for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_forecast_crest_vs_flood_ft must match rows")
    if report.max_stage_delta_ft != max(
        (row.stage_delta_ft for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_stage_delta_ft must match rows")
    if report.max_forecast_crest_revision_ft != max(
        (row.forecast_crest_revision_ft for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_forecast_crest_revision_ft must match rows")
    if report.average_forecast_confidence_ratio != _ratio(
        _sum_decimal(row.forecast_confidence_ratio for row in rows),
        report.row_count,
    ):
        raise ValueError("average_forecast_confidence_ratio must match rows")
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
    return _require_nonnegative_decimal("observation_age_seconds", seconds)


def _difference_decimal(field_name: str, left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = left - right
    return _require_decimal(field_name, value)


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
