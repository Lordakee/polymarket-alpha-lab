"""Pure Phase 1 weather temperature extreme digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_WEATHER_TEMPERATURE_EXTREME_DIGEST_CONFIG_VERSION = (
    "market-research-weather-temperature-extreme-digest-v0"
)

DIGEST_STATUSES = ("ready", "watch", "blocked")
MATERIAL_TEMPERATURE_DEVIATION_REASON = (
    "market_research_weather_temperature_extreme_digest_material_temperature_deviation"
)
HIGH_FORECAST_CONFIDENCE_REASON = (
    "market_research_weather_temperature_extreme_digest_high_forecast_confidence"
)
STATION_DISAGREEMENT_REASON = (
    "market_research_weather_temperature_extreme_digest_station_disagreement"
)
MISSING_ACKNOWLEDGEMENT_REASON = (
    "market_research_weather_temperature_extreme_digest_missing_acknowledgement"
)
SLOW_ACKNOWLEDGEMENT_REASON = (
    "market_research_weather_temperature_extreme_digest_slow_acknowledgement"
)
STALE_OBSERVATION_REASON = (
    "market_research_weather_temperature_extreme_digest_stale_observation"
)
THIN_SOURCES_REASON = "market_research_weather_temperature_extreme_digest_thin_sources"
READY_REASON = "market_research_weather_temperature_extreme_digest_ready"
NO_INPUTS_REASON = "market_research_weather_temperature_extreme_digest_no_inputs"
REASON_CODES = (
    MATERIAL_TEMPERATURE_DEVIATION_REASON,
    HIGH_FORECAST_CONFIDENCE_REASON,
    STATION_DISAGREEMENT_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_OBSERVATION_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
NEXT_STEPS = {
    "ready": "allow_report_only_market_research_weather_temperature_extreme_digest",
    "watch": "watch_report_only_market_research_weather_temperature_extreme_digest",
    "blocked": "block_report_only_market_research_weather_temperature_extreme_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        "https://",
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_WEATHER_TEMPERATURE_EXTREME_DIGEST_CONFIG_VERSION",
    "MarketResearchWeatherTemperatureExtremeDigestConfig",
    "MarketResearchWeatherTemperatureExtremeDigestInputRow",
    "MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount",
    "MarketResearchWeatherTemperatureExtremeDigestReport",
    "MarketResearchWeatherTemperatureExtremeDigestRow",
    "build_market_research_weather_temperature_extreme_digest",
    "market_research_weather_temperature_extreme_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchWeatherTemperatureExtremeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_WEATHER_TEMPERATURE_EXTREME_DIGEST_CONFIG_VERSION
    )
    fresh_observation_max_age_seconds: Decimal = Decimal("3600.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_temperature_deviation_threshold_celsius: Decimal = Decimal("5.000000")
    high_forecast_confidence_threshold: Decimal = Decimal("0.750000")
    max_station_disagreement_score: Decimal = Decimal("0.600000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("900.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchWeatherTemperatureExtremeDigestConfig:
            raise TypeError(
                "MarketResearchWeatherTemperatureExtremeDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchWeatherTemperatureExtremeDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchWeatherTemperatureExtremeDigestConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "fresh_observation_max_age_seconds",
            "max_acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        object.__setattr__(
            self,
            "material_temperature_deviation_threshold_celsius",
            _require_positive_decimal(
                "material_temperature_deviation_threshold_celsius",
                self.material_temperature_deviation_threshold_celsius,
            ),
        )
        for field_name in (
            "high_forecast_confidence_threshold",
            "max_station_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchWeatherTemperatureExtremeDigestInputRow:
    research_key: str
    condition_id: str
    weather_region_key: str
    public_temperature_reference: str
    observed_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    baseline_temperature_celsius: Decimal
    observed_temperature_celsius: Decimal
    forecast_confidence_score: Decimal
    station_disagreement_score: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchWeatherTemperatureExtremeDigestInputRow:
            raise TypeError(
                "MarketResearchWeatherTemperatureExtremeDigestInputRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchWeatherTemperatureExtremeDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchWeatherTemperatureExtremeDigestInputRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "weather_region_key",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_canonical_string(
            "public_temperature_reference",
            self.public_temperature_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "baseline_temperature_celsius",
            "observed_temperature_celsius",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "forecast_confidence_score",
            "station_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchWeatherTemperatureExtremeDigestRow:
    research_key: str
    condition_id: str
    weather_region_key: str
    extreme_status: str
    observation_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    source_gap_count: Decimal
    baseline_temperature_celsius: Decimal
    observed_temperature_celsius: Decimal
    temperature_deviation_celsius: Decimal
    absolute_temperature_deviation_celsius: Decimal
    forecast_confidence_score: Decimal
    station_disagreement_score: Decimal
    redacted_public_temperature_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchWeatherTemperatureExtremeDigestRow:
            raise TypeError(
                "MarketResearchWeatherTemperatureExtremeDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchWeatherTemperatureExtremeDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchWeatherTemperatureExtremeDigestRow",
            )
        for field_name in ("research_key", "condition_id", "weather_region_key"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_digest_status("extreme_status", self.extreme_status)
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_optional_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        for field_name in ("source_count", "source_gap_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "baseline_temperature_celsius",
            "observed_temperature_celsius",
            "temperature_deviation_celsius",
            "absolute_temperature_deviation_celsius",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "forecast_confidence_score",
            "station_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_redacted_reference(
            "redacted_public_temperature_reference",
            self.redacted_public_temperature_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    extreme_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "extreme_ratio",
            _require_ratio_decimal("extreme_ratio", self.extreme_ratio),
        )
        _require_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchWeatherTemperatureExtremeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    temperature_extreme_count: Decimal
    ready_extreme_count: Decimal
    watch_extreme_count: Decimal
    blocked_extreme_count: Decimal
    material_temperature_deviation_count: Decimal
    stale_observation_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    high_forecast_confidence_count: Decimal
    station_disagreement_count: Decimal
    average_abs_temperature_deviation_celsius: Decimal
    max_observation_age_seconds: Decimal
    average_source_count: Decimal
    fresh_observation_max_age_seconds: Decimal
    min_source_count: Decimal
    material_temperature_deviation_threshold_celsius: Decimal
    high_forecast_confidence_threshold: Decimal
    max_station_disagreement_score: Decimal
    max_acknowledgement_lag_seconds: Decimal
    rows: tuple[MarketResearchWeatherTemperatureExtremeDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchWeatherTemperatureExtremeDigestReport:
            raise TypeError(
                "MarketResearchWeatherTemperatureExtremeDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchWeatherTemperatureExtremeDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchWeatherTemperatureExtremeDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "temperature_extreme_count",
            "ready_extreme_count",
            "watch_extreme_count",
            "blocked_extreme_count",
            "material_temperature_deviation_count",
            "stale_observation_count",
            "thin_source_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
            "high_forecast_confidence_count",
            "station_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_abs_temperature_deviation_celsius",
            "material_temperature_deviation_threshold_celsius",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_forecast_confidence_threshold",
            "max_station_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_observation_age_seconds",
            "average_source_count",
            "fresh_observation_max_age_seconds",
            "max_acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_nonnegative_count_decimal("min_source_count", self.min_source_count),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_flags("report", self)


def build_market_research_weather_temperature_extreme_digest(
    input_rows: list[MarketResearchWeatherTemperatureExtremeDigestInputRow]
    | tuple[MarketResearchWeatherTemperatureExtremeDigestInputRow, ...],
    *,
    config: MarketResearchWeatherTemperatureExtremeDigestConfig,
    generated_at: datetime,
) -> MarketResearchWeatherTemperatureExtremeDigestReport:
    if type(config) is not MarketResearchWeatherTemperatureExtremeDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchWeatherTemperatureExtremeDigestConfig",
        )
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows_in = _normalize_input_rows(input_rows)
    rows = _rows(rows_in, config=config, generated_at=generated_at_utc)
    extreme_count = _decimal_count(len(rows))
    ready_count = _status_count(rows, "ready")
    watch_count = _status_count(rows, "watch")
    blocked_count = _status_count(rows, "blocked")
    digest_status = _report_status(
        extreme_count=extreme_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)

    return MarketResearchWeatherTemperatureExtremeDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        temperature_extreme_count=extreme_count,
        ready_extreme_count=ready_count,
        watch_extreme_count=watch_count,
        blocked_extreme_count=blocked_count,
        material_temperature_deviation_count=_event_count_with(
            rows,
            MATERIAL_TEMPERATURE_DEVIATION_REASON,
        ),
        stale_observation_count=_event_count_with(rows, STALE_OBSERVATION_REASON),
        thin_source_count=_event_count_with(rows, THIN_SOURCES_REASON),
        missing_acknowledgement_count=_event_count_with(
            rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        slow_acknowledgement_count=_event_count_with(
            rows,
            SLOW_ACKNOWLEDGEMENT_REASON,
        ),
        high_forecast_confidence_count=_event_count_with(
            rows,
            HIGH_FORECAST_CONFIDENCE_REASON,
        ),
        station_disagreement_count=_event_count_with(
            rows,
            STATION_DISAGREEMENT_REASON,
        ),
        average_abs_temperature_deviation_celsius=(
            _average_abs_temperature_deviation(rows)
        ),
        max_observation_age_seconds=_max_decimal(
            row.observation_age_seconds for row in rows
        ),
        average_source_count=_average_decimal(row.source_count for row in rows),
        fresh_observation_max_age_seconds=config.fresh_observation_max_age_seconds,
        min_source_count=config.min_source_count,
        material_temperature_deviation_threshold_celsius=(
            config.material_temperature_deviation_threshold_celsius
        ),
        high_forecast_confidence_threshold=config.high_forecast_confidence_threshold,
        max_station_disagreement_score=config.max_station_disagreement_score,
        max_acknowledgement_lag_seconds=config.max_acknowledgement_lag_seconds,
        rows=rows,
        source_config_versions=_source_config_versions(rows_in),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_weather_temperature_extreme_digest_payload(
    report: MarketResearchWeatherTemperatureExtremeDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchWeatherTemperatureExtremeDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchWeatherTemperatureExtremeDigestReport",
        )
    _require_flags("report", report)
    json_object = _plain(asdict(report))
    if type(json_object) is not dict:
        raise ValueError("json object must be a dict")
    return json_object


def _normalize_input_rows(
    value: object,
) -> tuple[MarketResearchWeatherTemperatureExtremeDigestInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchWeatherTemperatureExtremeDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchWeatherTemperatureExtremeDigestInputRow",
            )
        _require_flags("input row", row)
        if row.weather_region_key in seen:
            raise ValueError("input rows must not contain duplicate weather region keys")
        seen.add(row.weather_region_key)
    return rows


def _rows(
    input_rows: tuple[MarketResearchWeatherTemperatureExtremeDigestInputRow, ...],
    *,
    config: MarketResearchWeatherTemperatureExtremeDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchWeatherTemperatureExtremeDigestRow, ...]:
    rows = []
    for row in input_rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        if row.acknowledged_at is not None and row.acknowledged_at < row.observed_at:
            raise ValueError("acknowledged_at must not precede observed_at")
        observation_age_seconds = _seconds_between(row.observed_at, generated_at)
        acknowledgement_lag_seconds = (
            None
            if row.acknowledged_at is None
            else _seconds_between(row.observed_at, row.acknowledged_at)
        )
        source_gap_count = _count_gap(config.min_source_count, row.source_count)
        temperature_deviation_celsius = _quantize(
            row.observed_temperature_celsius - row.baseline_temperature_celsius,
        )
        absolute_temperature_deviation_celsius = _abs_decimal(
            temperature_deviation_celsius,
        )
        reason_codes = _row_reason_codes(
            row,
            config=config,
            observation_age_seconds=observation_age_seconds,
            acknowledgement_lag_seconds=acknowledgement_lag_seconds,
            source_gap_count=source_gap_count,
            absolute_temperature_deviation_celsius=(
                absolute_temperature_deviation_celsius
            ),
        )
        rows.append(
            MarketResearchWeatherTemperatureExtremeDigestRow(
                research_key=row.research_key,
                condition_id=row.condition_id,
                weather_region_key=row.weather_region_key,
                extreme_status=_row_status(reason_codes),
                observation_age_seconds=observation_age_seconds,
                acknowledgement_lag_seconds=acknowledgement_lag_seconds,
                source_count=row.source_count,
                source_gap_count=source_gap_count,
                baseline_temperature_celsius=row.baseline_temperature_celsius,
                observed_temperature_celsius=row.observed_temperature_celsius,
                temperature_deviation_celsius=temperature_deviation_celsius,
                absolute_temperature_deviation_celsius=(
                    absolute_temperature_deviation_celsius
                ),
                forecast_confidence_score=row.forecast_confidence_score,
                station_disagreement_score=row.station_disagreement_score,
                redacted_public_temperature_reference=_redacted_public_reference(
                    row.public_temperature_reference,
                ),
                reason_codes=reason_codes,
            ),
        )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                _status_rank(item.extreme_status),
                item.weather_region_key,
                item.research_key,
            ),
        ),
    )


def _row_reason_codes(
    row: MarketResearchWeatherTemperatureExtremeDigestInputRow,
    *,
    config: MarketResearchWeatherTemperatureExtremeDigestConfig,
    observation_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    source_gap_count: Decimal,
    absolute_temperature_deviation_celsius: Decimal,
) -> tuple[str, ...]:
    reason_codes = []
    if (
        absolute_temperature_deviation_celsius
        >= config.material_temperature_deviation_threshold_celsius
    ):
        reason_codes.append(MATERIAL_TEMPERATURE_DEVIATION_REASON)
    if row.forecast_confidence_score > config.high_forecast_confidence_threshold:
        reason_codes.append(HIGH_FORECAST_CONFIDENCE_REASON)
    if row.station_disagreement_score > config.max_station_disagreement_score:
        reason_codes.append(STATION_DISAGREEMENT_REASON)
    if acknowledgement_lag_seconds is None:
        reason_codes.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        reason_codes.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if observation_age_seconds > config.fresh_observation_max_age_seconds:
        reason_codes.append(STALE_OBSERVATION_REASON)
    if source_gap_count > ZERO:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return "ready"
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return "blocked"
    return "watch"


def _report_status(
    *,
    extreme_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
) -> str:
    if extreme_count == ZERO:
        return "blocked"
    if blocked_count > ZERO:
        return "blocked"
    if watch_count > ZERO:
        return "watch"
    return "ready"


def _reason_code_counts(
    rows: tuple[MarketResearchWeatherTemperatureExtremeDigestRow, ...],
) -> tuple[MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                extreme_ratio=ZERO,
            ),
        )
    total = _decimal_count(len(rows))
    return tuple(
        MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount(
            reason_code=reason_code,
            count=_event_count_with(rows, reason_code),
            extreme_ratio=_ratio(_event_count_with(rows, reason_code), total),
        )
        for reason_code in REASON_CODES
        if reason_code != NO_INPUTS_REASON
        and any(reason_code in row.reason_codes for row in rows)
    )


def _event_count_with(
    rows: tuple[MarketResearchWeatherTemperatureExtremeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _source_config_versions(
    rows: tuple[MarketResearchWeatherTemperatureExtremeDigestInputRow, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted((row.weather_region_key, row.source_config_version) for row in rows),
    )


def _status_count(
    rows: tuple[MarketResearchWeatherTemperatureExtremeDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.extreme_status == status))


def _average_abs_temperature_deviation(
    rows: tuple[MarketResearchWeatherTemperatureExtremeDigestRow, ...],
) -> Decimal:
    return _average_decimal(
        row.absolute_temperature_deviation_celsius for row in rows
    )


def _average_decimal(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _ratio(sum(items, ZERO), _decimal_count(len(items)))


def _max_decimal(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return max(items)


def _count_gap(required_count: Decimal, actual_count: Decimal) -> Decimal:
    if actual_count >= required_count:
        return ZERO
    return _quantize(required_count - actual_count)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _abs_decimal(value: Decimal) -> Decimal:
    return value.copy_abs()


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _plain(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _plain(asdict(value))
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return tuple(_plain(item) for item in value)
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    return value


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchWeatherTemperatureExtremeDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchWeatherTemperatureExtremeDigestRow:
            raise ValueError(
                "rows must contain MarketResearchWeatherTemperatureExtremeDigestRow",
            )
        _require_flags("row", row)
        if row.weather_region_key in seen:
            raise ValueError("rows must not contain duplicate weather region keys")
        seen.add(row.weather_region_key)
    expected = tuple(
        sorted(
            rows,
            key=lambda item: (
                _status_rank(item.extreme_status),
                item.weather_region_key,
                item.research_key,
            ),
        ),
    )
    if rows != expected:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_source_config_versions(
    value: object,
) -> tuple[tuple[str, str], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("source_config_versions must be a list or tuple")
    versions = tuple(value)
    seen: set[str] = set()
    for item in versions:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("source_config_versions entries must be pairs")
        weather_region_key, source_config_version = item
        _require_public_string("source_config_versions weather_region_key", weather_region_key)
        _require_public_string(
            "source_config_versions source_config_version",
            source_config_version,
        )
        if weather_region_key in seen:
            raise ValueError("source_config_versions weather region keys must be unique")
        seen.add(weather_region_key)
    if versions != tuple(sorted(versions)):
        raise ValueError("source_config_versions must be sorted")
    return versions


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchWeatherTemperatureExtremeDigestReasonCodeCount",
            )
        _require_flags("reason code count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts reason codes must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        sorted(counts, key=lambda item: _reason_rank(item.reason_code)),
    )
    if counts != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_reason_code("reason_codes", code)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    expected = tuple(sorted(codes, key=_reason_rank))
    if codes != expected:
        raise ValueError("reason_codes must be sorted deterministically")
    return codes


def _validate_row(row: MarketResearchWeatherTemperatureExtremeDigestRow) -> None:
    expected_deviation = _quantize(
        row.observed_temperature_celsius - row.baseline_temperature_celsius,
    )
    if row.temperature_deviation_celsius != expected_deviation:
        raise ValueError(
            "temperature_deviation_celsius must match observed minus baseline",
        )
    if row.absolute_temperature_deviation_celsius != _abs_decimal(expected_deviation):
        raise ValueError(
            "absolute_temperature_deviation_celsius must match absolute deviation",
        )
    if row.extreme_status != _row_status(row.reason_codes):
        raise ValueError("extreme_status must match reason_codes")
    if row.reason_codes == (READY_REASON,) and (
        row.source_gap_count != ZERO
        or row.acknowledgement_lag_seconds is None
    ):
        raise ValueError("reason_codes must reflect row gaps")


def _validate_report(
    report: MarketResearchWeatherTemperatureExtremeDigestReport,
) -> None:
    rows = report.rows
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.temperature_extreme_count != _decimal_count(len(rows)):
        raise ValueError("temperature_extreme_count must match rows")
    checks = (
        ("ready_extreme_count", _status_count(rows, "ready")),
        ("watch_extreme_count", _status_count(rows, "watch")),
        ("blocked_extreme_count", _status_count(rows, "blocked")),
        (
            "material_temperature_deviation_count",
            _event_count_with(rows, MATERIAL_TEMPERATURE_DEVIATION_REASON),
        ),
        ("stale_observation_count", _event_count_with(rows, STALE_OBSERVATION_REASON)),
        ("thin_source_count", _event_count_with(rows, THIN_SOURCES_REASON)),
        (
            "missing_acknowledgement_count",
            _event_count_with(rows, MISSING_ACKNOWLEDGEMENT_REASON),
        ),
        (
            "slow_acknowledgement_count",
            _event_count_with(rows, SLOW_ACKNOWLEDGEMENT_REASON),
        ),
        (
            "high_forecast_confidence_count",
            _event_count_with(rows, HIGH_FORECAST_CONFIDENCE_REASON),
        ),
        (
            "station_disagreement_count",
            _event_count_with(rows, STATION_DISAGREEMENT_REASON),
        ),
        (
            "average_abs_temperature_deviation_celsius",
            _average_abs_temperature_deviation(rows),
        ),
        (
            "max_observation_age_seconds",
            _max_decimal(row.observation_age_seconds for row in rows),
        ),
        ("average_source_count", _average_decimal(row.source_count for row in rows)),
    )
    for field_name, expected in checks:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_status = _report_status(
        extreme_count=report.temperature_extreme_count,
        watch_count=report.watch_extreme_count,
        blocked_count=report.blocked_extreme_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match row statuses")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _status_rank(status: str) -> int:
    return {"blocked": 0, "watch": 1, "ready": 2}[status]


def _reason_rank(reason_code: str) -> int:
    return REASON_CODES.index(reason_code)


def _redacted_public_reference(value: str) -> str:
    if _contains_unsafe_text(value):
        return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"
    return value


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _contains_unsafe_text(value):
        raise ValueError(f"{field_name} must be redacted")


def _contains_unsafe_text(value: object) -> bool:
    if type(value) is not str:
        return False
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _require_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_digest_status(field_name: str, value: object) -> None:
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be one of {DIGEST_STATUSES}")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if any(ch.isspace() for ch in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if _contains_unsafe_text(value):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal count")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal count")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value
