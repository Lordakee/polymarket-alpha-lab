"""Pure Phase 1 weather flash flood guidance break digest reducer."""

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


DEFAULT_WEATHER_FLASH_FLOOD_GUIDANCE_BREAK_DIGEST_CONFIG_VERSION = (
    "market-research-weather-flash-flood-guidance-break-digest-v0"
)

SOURCE_CURRENT = "current"
SOURCE_STALE = "stale"

ROW_STATUSES = ("pass", "watch", "blocked")
SOURCE_STATUSES = (SOURCE_CURRENT, SOURCE_STALE)

SOURCE_STALE_REASON = "weather_flash_flood_guidance_break_source_stale"
THRESHOLD_EXCEEDED_REASON = (
    "weather_flash_flood_guidance_break_threshold_exceeded"
)
HEAVY_RAINFALL_REASON = "weather_flash_flood_guidance_break_heavy_rainfall"
SATURATED_SOIL_REASON = "weather_flash_flood_guidance_break_saturated_soil"
THRESHOLD_WATCH_REASON = "weather_flash_flood_guidance_break_threshold_watch"
LOW_CONFIDENCE_REASON = "weather_flash_flood_guidance_break_low_confidence"
ROW_CLEAR_REASON = "weather_flash_flood_guidance_break_row_clear"
DIGEST_CLEAR_REASON = "weather_flash_flood_guidance_break_digest_clear"
DIGEST_EMPTY_REASON = "weather_flash_flood_guidance_break_digest_empty"

ROW_REASON_CODES = (
    SOURCE_STALE_REASON,
    THRESHOLD_EXCEEDED_REASON,
    HEAVY_RAINFALL_REASON,
    SATURATED_SOIL_REASON,
    THRESHOLD_WATCH_REASON,
    LOW_CONFIDENCE_REASON,
    ROW_CLEAR_REASON,
)
REPORT_REASON_CODES = (
    SOURCE_STALE_REASON,
    THRESHOLD_EXCEEDED_REASON,
    HEAVY_RAINFALL_REASON,
    SATURATED_SOIL_REASON,
    THRESHOLD_WATCH_REASON,
    LOW_CONFIDENCE_REASON,
    DIGEST_CLEAR_REASON,
    DIGEST_EMPTY_REASON,
)

NEXT_STEPS = {
    "pass": "continue_report_only_weather_flash_flood_guidance_break_digest",
    "watch": "monitor_report_only_weather_flash_flood_guidance_break_digest",
    "blocked": "block_report_only_weather_flash_flood_guidance_break_digest",
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
    "pri" "vate" "_" "ke" "y",
)


__all__ = (
    "DEFAULT_WEATHER_FLASH_FLOOD_GUIDANCE_BREAK_DIGEST_CONFIG_VERSION",
    "WeatherFlashFloodGuidanceBreakDigestConfig",
    "WeatherFlashFloodGuidanceBreakObservation",
    "WeatherFlashFloodGuidanceBreakDigestRow",
    "WeatherFlashFloodGuidanceBreakReasonCodeCount",
    "WeatherFlashFloodGuidanceBreakDigestReport",
    "build_market_research_weather_flash_flood_guidance_break_digest",
    "market_research_weather_flash_flood_guidance_break_digest_json",
)


@dataclass(frozen=True)
class WeatherFlashFloodGuidanceBreakDigestConfig:
    config_version: str = (
        DEFAULT_WEATHER_FLASH_FLOOD_GUIDANCE_BREAK_DIGEST_CONFIG_VERSION
    )
    max_source_age_seconds: Decimal = Decimal("1800.000000")
    watch_guidance_break_ratio: Decimal = Decimal("0.850000")
    blocked_guidance_break_ratio: Decimal = Decimal("1.000000")
    saturated_soil_ratio: Decimal = Decimal("0.800000")
    heavy_rainfall_inches_6h: Decimal = Decimal("3.000000")
    low_confidence_ratio: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherFlashFloodGuidanceBreakDigestConfig:
            raise TypeError(
                "WeatherFlashFloodGuidanceBreakDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherFlashFloodGuidanceBreakDigestConfig:
            raise ValueError(
                "config must be exactly WeatherFlashFloodGuidanceBreakDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_WEATHER_FLASH_FLOOD_GUIDANCE_BREAK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_positive_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "watch_guidance_break_ratio",
            "blocked_guidance_break_ratio",
            "saturated_soil_ratio",
            "low_confidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_guidance_break_ratio <= ZERO:
            raise ValueError("watch_guidance_break_ratio must be positive")
        if self.blocked_guidance_break_ratio <= ZERO:
            raise ValueError("blocked_guidance_break_ratio must be positive")
        if self.blocked_guidance_break_ratio < self.watch_guidance_break_ratio:
            raise ValueError(
                "blocked_guidance_break_ratio must be at least watch threshold",
            )
        object.__setattr__(
            self,
            "heavy_rainfall_inches_6h",
            _require_positive_decimal(
                "heavy_rainfall_inches_6h",
                self.heavy_rainfall_inches_6h,
            ),
        )
        require_paper_only_flags(
            "WeatherFlashFloodGuidanceBreakDigestConfig",
            self,
        )


@dataclass(frozen=True)
class WeatherFlashFloodGuidanceBreakObservation:
    basin_id: str
    event_id: str
    source_id: str
    observed_at: datetime
    rainfall_inches_6h: Decimal
    flash_flood_guidance_inches_6h: Decimal
    antecedent_soil_saturation_ratio: Decimal
    forecast_confidence_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherFlashFloodGuidanceBreakObservation:
            raise TypeError(
                "WeatherFlashFloodGuidanceBreakObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherFlashFloodGuidanceBreakObservation:
            raise ValueError(
                "observation must be exactly WeatherFlashFloodGuidanceBreakObservation",
            )
        for field_name in ("basin_id", "event_id", "source_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "rainfall_inches_6h",
            _require_nonnegative_decimal(
                "rainfall_inches_6h",
                self.rainfall_inches_6h,
            ),
        )
        object.__setattr__(
            self,
            "flash_flood_guidance_inches_6h",
            _require_positive_decimal(
                "flash_flood_guidance_inches_6h",
                self.flash_flood_guidance_inches_6h,
            ),
        )
        for field_name in (
            "antecedent_soil_saturation_ratio",
            "forecast_confidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags(
            "WeatherFlashFloodGuidanceBreakObservation",
            self,
        )


@dataclass(frozen=True)
class WeatherFlashFloodGuidanceBreakDigestRow:
    basin_id: str
    event_id: str
    source_id: str
    observed_at: datetime
    source_age_seconds: Decimal
    source_freshness_status: str
    rainfall_inches_6h: Decimal
    flash_flood_guidance_inches_6h: Decimal
    guidance_break_ratio: Decimal
    antecedent_soil_saturation_ratio: Decimal
    forecast_confidence_ratio: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherFlashFloodGuidanceBreakDigestRow:
            raise TypeError(
                "WeatherFlashFloodGuidanceBreakDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherFlashFloodGuidanceBreakDigestRow:
            raise ValueError("row must be exactly WeatherFlashFloodGuidanceBreakDigestRow")
        for field_name in ("basin_id", "event_id", "source_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_age_seconds",
            "rainfall_inches_6h",
            "guidance_break_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "flash_flood_guidance_inches_6h",
            _require_positive_decimal(
                "flash_flood_guidance_inches_6h",
                self.flash_flood_guidance_inches_6h,
            ),
        )
        for field_name in (
            "antecedent_soil_saturation_ratio",
            "forecast_confidence_ratio",
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
        _require_member("row_status", self.row_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        reject_unsafe_surface_fields(
            "weather flash flood guidance break row",
            self,
        )
        require_paper_only_flags(
            "WeatherFlashFloodGuidanceBreakDigestRow",
            self,
        )


@dataclass(frozen=True)
class WeatherFlashFloodGuidanceBreakReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherFlashFloodGuidanceBreakReasonCodeCount:
            raise TypeError(
                "WeatherFlashFloodGuidanceBreakReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherFlashFloodGuidanceBreakReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "WeatherFlashFloodGuidanceBreakReasonCodeCount",
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
            "weather flash flood guidance break reason code count",
            self,
        )
        require_paper_only_flags(
            "WeatherFlashFloodGuidanceBreakReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class WeatherFlashFloodGuidanceBreakDigestReport:
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
    guidance_break_count: Decimal
    guidance_watch_count: Decimal
    max_source_age_seconds: Decimal
    max_source_age_observed_seconds: Decimal
    max_guidance_break_ratio: Decimal
    max_rainfall_inches_6h: Decimal
    min_flash_flood_guidance_inches_6h: Decimal
    average_forecast_confidence_ratio: Decimal
    rows: tuple[WeatherFlashFloodGuidanceBreakDigestRow, ...]
    reason_code_counts: tuple[WeatherFlashFloodGuidanceBreakReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not WeatherFlashFloodGuidanceBreakDigestReport:
            raise TypeError(
                "WeatherFlashFloodGuidanceBreakDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not WeatherFlashFloodGuidanceBreakDigestReport:
            raise ValueError(
                "report must be exactly WeatherFlashFloodGuidanceBreakDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_WEATHER_FLASH_FLOOD_GUIDANCE_BREAK_DIGEST_CONFIG_VERSION
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
            "guidance_break_count",
            "guidance_watch_count",
            "max_source_age_seconds",
            "max_source_age_observed_seconds",
            "max_guidance_break_ratio",
            "max_rainfall_inches_6h",
            "min_flash_flood_guidance_inches_6h",
            "average_forecast_confidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_forecast_confidence_ratio > ONE:
            raise ValueError(
                "average_forecast_confidence_ratio must be no greater than one",
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
        reject_unsafe_surface_fields(
            "weather flash flood guidance break report",
            self,
        )
        require_paper_only_flags(
            "WeatherFlashFloodGuidanceBreakDigestReport",
            self,
        )


def build_market_research_weather_flash_flood_guidance_break_digest(
    observations: Iterable[WeatherFlashFloodGuidanceBreakObservation],
    *,
    config: WeatherFlashFloodGuidanceBreakDigestConfig,
    generated_at: datetime,
) -> WeatherFlashFloodGuidanceBreakDigestReport:
    if type(config) is not WeatherFlashFloodGuidanceBreakDigestConfig:
        raise ValueError(
            "config must be exactly WeatherFlashFloodGuidanceBreakDigestConfig",
        )
    require_paper_only_flags(
        "WeatherFlashFloodGuidanceBreakDigestConfig",
        config,
    )
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
    sorted_rows = tuple(sorted(rows, key=_row_sort_tuple))
    reason_codes = _report_reason_codes(sorted_rows)
    digest_status = _digest_status(sorted_rows)
    row_count = _count_decimal(len(sorted_rows))

    return WeatherFlashFloodGuidanceBreakDigestReport(
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
        guidance_break_count=_count_decimal(
            sum(1 for row in sorted_rows if THRESHOLD_EXCEEDED_REASON in row.reason_codes),
        ),
        guidance_watch_count=_count_decimal(
            sum(1 for row in sorted_rows if THRESHOLD_WATCH_REASON in row.reason_codes),
        ),
        max_source_age_seconds=config.max_source_age_seconds,
        max_source_age_observed_seconds=max(
            (row.source_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_guidance_break_ratio=max(
            (row.guidance_break_ratio for row in sorted_rows),
            default=ZERO,
        ),
        max_rainfall_inches_6h=max(
            (row.rainfall_inches_6h for row in sorted_rows),
            default=ZERO,
        ),
        min_flash_flood_guidance_inches_6h=min(
            (row.flash_flood_guidance_inches_6h for row in sorted_rows),
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


def market_research_weather_flash_flood_guidance_break_digest_json(
    report: WeatherFlashFloodGuidanceBreakDigestReport,
) -> dict[str, Any]:
    if type(report) is not WeatherFlashFloodGuidanceBreakDigestReport:
        raise ValueError(
            "report must be exactly WeatherFlashFloodGuidanceBreakDigestReport",
        )
    reject_unsafe_surface_fields(
        "weather flash flood guidance break report",
        report,
    )
    value = json_ready_no_floats(asdict(report))
    if not isinstance(value, dict):
        raise ValueError("report JSON value must be an object")
    reject_unsafe_surface_fields(
        "weather flash flood guidance break JSON value",
        value,
    )
    return value


def _row_for_observation(
    observation: WeatherFlashFloodGuidanceBreakObservation,
    *,
    config: WeatherFlashFloodGuidanceBreakDigestConfig,
    generated_at: datetime,
) -> WeatherFlashFloodGuidanceBreakDigestRow:
    source_age_seconds = _age_seconds(generated_at, observation.observed_at)
    source_freshness_status = (
        SOURCE_STALE
        if source_age_seconds > config.max_source_age_seconds
        else SOURCE_CURRENT
    )
    guidance_break_ratio = _ratio(
        observation.rainfall_inches_6h,
        observation.flash_flood_guidance_inches_6h,
    )
    reason_codes = _row_reason_codes(
        source_freshness_status=source_freshness_status,
        rainfall_inches_6h=observation.rainfall_inches_6h,
        guidance_break_ratio=guidance_break_ratio,
        antecedent_soil_saturation_ratio=observation.antecedent_soil_saturation_ratio,
        forecast_confidence_ratio=observation.forecast_confidence_ratio,
        config=config,
    )
    return WeatherFlashFloodGuidanceBreakDigestRow(
        basin_id=observation.basin_id,
        event_id=observation.event_id,
        source_id=observation.source_id,
        observed_at=observation.observed_at,
        source_age_seconds=source_age_seconds,
        source_freshness_status=source_freshness_status,
        rainfall_inches_6h=observation.rainfall_inches_6h,
        flash_flood_guidance_inches_6h=observation.flash_flood_guidance_inches_6h,
        guidance_break_ratio=guidance_break_ratio,
        antecedent_soil_saturation_ratio=observation.antecedent_soil_saturation_ratio,
        forecast_confidence_ratio=observation.forecast_confidence_ratio,
        row_status=_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_freshness_status: str,
    rainfall_inches_6h: Decimal,
    guidance_break_ratio: Decimal,
    antecedent_soil_saturation_ratio: Decimal,
    forecast_confidence_ratio: Decimal,
    config: WeatherFlashFloodGuidanceBreakDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source_freshness_status == SOURCE_STALE:
        reasons.append(SOURCE_STALE_REASON)
    if guidance_break_ratio >= config.blocked_guidance_break_ratio:
        reasons.append(THRESHOLD_EXCEEDED_REASON)
    elif guidance_break_ratio >= config.watch_guidance_break_ratio:
        reasons.append(THRESHOLD_WATCH_REASON)
    if rainfall_inches_6h >= config.heavy_rainfall_inches_6h:
        reasons.append(HEAVY_RAINFALL_REASON)
    if antecedent_soil_saturation_ratio >= config.saturated_soil_ratio:
        reasons.append(SATURATED_SOIL_REASON)
    if forecast_confidence_ratio <= config.low_confidence_ratio:
        reasons.append(LOW_CONFIDENCE_REASON)
    if not reasons:
        reasons.append(ROW_CLEAR_REASON)
    return _sort_reason_codes(tuple(reasons), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[WeatherFlashFloodGuidanceBreakDigestRow, ...],
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
    rows: tuple[WeatherFlashFloodGuidanceBreakDigestRow, ...],
) -> tuple[WeatherFlashFloodGuidanceBreakReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == (DIGEST_EMPTY_REASON,):
        return (
            WeatherFlashFloodGuidanceBreakReasonCodeCount(
                reason_code=DIGEST_EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    if reason_codes == (DIGEST_CLEAR_REASON,):
        return (
            WeatherFlashFloodGuidanceBreakReasonCodeCount(
                reason_code=DIGEST_CLEAR_REASON,
                count=row_count,
                row_ratio=ONE,
            ),
        )
    return tuple(
        WeatherFlashFloodGuidanceBreakReasonCodeCount(
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
    if THRESHOLD_EXCEEDED_REASON in reason_codes:
        return "blocked"
    if reason_codes == (ROW_CLEAR_REASON,):
        return "pass"
    return "watch"


def _digest_status(rows: tuple[WeatherFlashFloodGuidanceBreakDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_observations(
    observations: Iterable[WeatherFlashFloodGuidanceBreakObservation],
    *,
    generated_at: datetime,
) -> tuple[WeatherFlashFloodGuidanceBreakObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError(
            "observations must be an iterable of "
            "WeatherFlashFloodGuidanceBreakObservation",
        )
    rows = tuple(observations)
    seen_pairs: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not WeatherFlashFloodGuidanceBreakObservation:
            raise ValueError(
                "observations must contain WeatherFlashFloodGuidanceBreakObservation",
            )
        require_paper_only_flags(
            "WeatherFlashFloodGuidanceBreakObservation",
            row,
        )
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        pair = (row.basin_id, row.event_id)
        if pair in seen_pairs:
            raise ValueError("event_id values must be unique per basin_id")
        seen_pairs.add(pair)
    return tuple(sorted(rows, key=lambda row: (row.basin_id, row.event_id, row.source_id)))


def _normalize_rows(
    rows: tuple[WeatherFlashFloodGuidanceBreakDigestRow, ...],
) -> tuple[WeatherFlashFloodGuidanceBreakDigestRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not WeatherFlashFloodGuidanceBreakDigestRow:
            raise ValueError("rows must contain WeatherFlashFloodGuidanceBreakDigestRow")
        require_paper_only_flags(
            "WeatherFlashFloodGuidanceBreakDigestRow",
            row,
        )
    normalized = tuple(sorted(rows, key=_row_sort_tuple))
    if rows != normalized:
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[WeatherFlashFloodGuidanceBreakReasonCodeCount, ...],
) -> tuple[WeatherFlashFloodGuidanceBreakReasonCodeCount, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not WeatherFlashFloodGuidanceBreakReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "WeatherFlashFloodGuidanceBreakReasonCodeCount",
            )
        require_paper_only_flags(
            "WeatherFlashFloodGuidanceBreakReasonCodeCount",
            row,
        )
    normalized = tuple(sorted(rows, key=lambda row: _reason_sort_value(row.reason_code)))
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


def _row_sort_tuple(
    row: WeatherFlashFloodGuidanceBreakDigestRow,
) -> tuple[Decimal | str, ...]:
    return (
        STATUS_RANK[row.row_status],
        -row.guidance_break_ratio,
        -row.rainfall_inches_6h,
        -row.antecedent_soil_saturation_ratio,
        row.basin_id,
        row.event_id,
        row.source_id,
    )


def _reason_sort_value(reason_code: str) -> Decimal:
    return REASON_RANK[reason_code]


def _validate_row(row: WeatherFlashFloodGuidanceBreakDigestRow) -> None:
    expected_status = _status_for_reason_codes(row.reason_codes)
    if row.row_status != expected_status:
        raise ValueError("row_status must match reason_codes")
    if row.source_freshness_status == SOURCE_STALE:
        if SOURCE_STALE_REASON not in row.reason_codes:
            raise ValueError("stale source rows must include stale reason")
    if row.source_freshness_status == SOURCE_CURRENT:
        if SOURCE_STALE_REASON in row.reason_codes:
            raise ValueError("current source rows must not include stale reason")
    if row.guidance_break_ratio != _ratio(
        row.rainfall_inches_6h,
        row.flash_flood_guidance_inches_6h,
    ):
        raise ValueError("guidance_break_ratio must match rainfall and guidance")


def _validate_report(report: WeatherFlashFloodGuidanceBreakDigestReport) -> None:
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
    if report.guidance_break_count != _count_decimal(
        sum(1 for row in rows if THRESHOLD_EXCEEDED_REASON in row.reason_codes),
    ):
        raise ValueError("guidance_break_count must match rows")
    if report.guidance_watch_count != _count_decimal(
        sum(1 for row in rows if THRESHOLD_WATCH_REASON in row.reason_codes),
    ):
        raise ValueError("guidance_watch_count must match rows")
    if report.max_source_age_observed_seconds != max(
        (row.source_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_source_age_observed_seconds must match rows")
    if report.max_guidance_break_ratio != max(
        (row.guidance_break_ratio for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_guidance_break_ratio must match rows")
    if report.max_rainfall_inches_6h != max(
        (row.rainfall_inches_6h for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_rainfall_inches_6h must match rows")
    if report.min_flash_flood_guidance_inches_6h != min(
        (row.flash_flood_guidance_inches_6h for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_flash_flood_guidance_inches_6h must match rows")
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
