"""Pure report-only hurricane rapid intensification risk digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_WEATHER_HURRICANE_RAPID_INTENSIFICATION_DIGEST_CONFIG_VERSION",
    "WeatherHurricaneRapidIntensificationDigestConfig",
    "WeatherHurricaneRapidIntensificationDigestReport",
    "WeatherHurricaneRapidIntensificationDigestRow",
    "WeatherHurricaneRapidIntensificationObservation",
    "build_market_research_weather_hurricane_rapid_intensification_digest",
    "market_research_weather_hurricane_rapid_intensification_digest_payload",
)


DEFAULT_MARKET_RESEARCH_WEATHER_HURRICANE_RAPID_INTENSIFICATION_DIGEST_CONFIG_VERSION = (
    "weather-hurricane-rapid-intensification-digest-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
STALE_CONFIDENCE_CAP = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64)

RAPID_INTENSIFICATION_STATUS = "rapid_intensification_signal"
RAPID_INTENSIFICATION_WATCH_STATUS = "rapid_intensification_watch"
LOW_SIGNAL_STATUS = "low_signal"
RAPID_INTENSIFICATION_STATUSES = (
    RAPID_INTENSIFICATION_STATUS,
    RAPID_INTENSIFICATION_WATCH_STATUS,
    LOW_SIGNAL_STATUS,
)
STATUS_RANK = {
    RAPID_INTENSIFICATION_STATUS: Decimal("0"),
    RAPID_INTENSIFICATION_WATCH_STATUS: Decimal("1"),
    LOW_SIGNAL_STATUS: Decimal("2"),
}


@dataclass(frozen=True)
class WeatherHurricaneRapidIntensificationDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_WEATHER_HURRICANE_RAPID_INTENSIFICATION_DIGEST_CONFIG_VERSION
    )
    max_source_age_seconds: Decimal = Decimal("900.000000")
    rapid_intensification_24h_threshold_knots: Decimal = Decimal("30.000000")
    watch_intensification_24h_threshold_knots: Decimal = Decimal("15.000000")
    rapid_intensification_probability_threshold: Decimal = Decimal("0.550000")
    watch_probability_threshold: Decimal = Decimal("0.250000")
    min_watch_confidence: Decimal = Decimal("0.600000")
    high_confidence_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            WeatherHurricaneRapidIntensificationDigestConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "max_source_age_seconds",
            "rapid_intensification_24h_threshold_knots",
            "watch_intensification_24h_threshold_knots",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rapid_intensification_probability_threshold",
            "watch_probability_threshold",
            "min_watch_confidence",
            "high_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if (
            self.watch_intensification_24h_threshold_knots
            > self.rapid_intensification_24h_threshold_knots
        ):
            raise ValueError(
                "watch_intensification_24h_threshold_knots must not exceed "
                "rapid_intensification_24h_threshold_knots",
            )
        if (
            self.watch_probability_threshold
            > self.rapid_intensification_probability_threshold
        ):
            raise ValueError(
                "watch_probability_threshold must not exceed "
                "rapid_intensification_probability_threshold",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class WeatherHurricaneRapidIntensificationObservation:
    event_id: str
    storm_id: str
    basin: str
    storm_name: str
    forecast_region: str
    source_reference: str
    forecast_valid_at: datetime
    source_observed_at: datetime
    current_max_sustained_wind_knots: Decimal
    forecast_24h_max_sustained_wind_knots: Decimal
    intensification_24h_knots: Decimal
    rapid_intensification_probability: Decimal
    forecast_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            WeatherHurricaneRapidIntensificationObservation,
            "observation",
        )
        for field_name in (
            "event_id",
            "storm_id",
            "basin",
            "storm_name",
            "forecast_region",
            "source_reference",
        ):
            _require_public_identifier(field_name, getattr(self, field_name))
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
            "current_max_sustained_wind_knots",
            "forecast_24h_max_sustained_wind_knots",
            "intensification_24h_knots",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rapid_intensification_probability",
            _normalize_probability(
                "rapid_intensification_probability",
                self.rapid_intensification_probability,
            ),
        )
        object.__setattr__(
            self,
            "forecast_confidence",
            _normalize_probability("forecast_confidence", self.forecast_confidence),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class WeatherHurricaneRapidIntensificationDigestRow:
    event_id: str
    storm_id: str
    basin: str
    storm_name: str
    forecast_region: str
    redacted_source_reference: str
    forecast_valid_at: datetime
    source_observed_at: datetime
    source_age_seconds: Decimal
    current_max_sustained_wind_knots: Decimal
    forecast_24h_max_sustained_wind_knots: Decimal
    intensification_24h_knots: Decimal
    rapid_intensification_probability: Decimal
    forecast_confidence: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    rapid_intensification_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            WeatherHurricaneRapidIntensificationDigestRow,
            "row",
        )
        for field_name in (
            "event_id",
            "storm_id",
            "basin",
            "storm_name",
            "forecast_region",
            "redacted_source_reference",
        ):
            _require_public_identifier(field_name, getattr(self, field_name))
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
            "current_max_sustained_wind_knots",
            "forecast_24h_max_sustained_wind_knots",
            "intensification_24h_knots",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rapid_intensification_probability",
            "forecast_confidence",
            "confidence_cap",
            "capped_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_rapid_intensification_status(
            "rapid_intensification_status",
            self.rapid_intensification_status,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class WeatherHurricaneRapidIntensificationDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    rapid_intensification_count: Decimal
    watch_count: Decimal
    low_signal_count: Decimal
    stale_source_count: Decimal
    max_rapid_intensification_probability: Decimal
    max_intensification_24h_knots: Decimal
    max_forecast_24h_max_sustained_wind_knots: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[WeatherHurricaneRapidIntensificationDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            WeatherHurricaneRapidIntensificationDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "rapid_intensification_count",
            "watch_count",
            "low_signal_count",
            "stale_source_count",
            "max_rapid_intensification_probability",
            "max_intensification_24h_knots",
            "max_forecast_24h_max_sustained_wind_knots",
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
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_market_research_weather_hurricane_rapid_intensification_digest(
    observations: Iterable[WeatherHurricaneRapidIntensificationObservation],
    *,
    config: WeatherHurricaneRapidIntensificationDigestConfig,
    generated_at: datetime,
) -> WeatherHurricaneRapidIntensificationDigestReport:
    if type(config) is not WeatherHurricaneRapidIntensificationDigestConfig:
        raise ValueError(
            "config must be a WeatherHurricaneRapidIntensificationDigestConfig",
        )
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

    return WeatherHurricaneRapidIntensificationDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        rapid_intensification_count=_status_count(rows, RAPID_INTENSIFICATION_STATUS),
        watch_count=_status_count(rows, RAPID_INTENSIFICATION_WATCH_STATUS),
        low_signal_count=_status_count(rows, LOW_SIGNAL_STATUS),
        stale_source_count=_reason_count(
            rows,
            "hurricane_rapid_intensification_source_stale",
        ),
        max_rapid_intensification_probability=_max_row_decimal(
            rows,
            "rapid_intensification_probability",
        ),
        max_intensification_24h_knots=_max_row_decimal(
            rows,
            "intensification_24h_knots",
        ),
        max_forecast_24h_max_sustained_wind_knots=_max_row_decimal(
            rows,
            "forecast_24h_max_sustained_wind_knots",
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_research_weather_hurricane_rapid_intensification_digest_payload(
    report: WeatherHurricaneRapidIntensificationDigestReport,
) -> dict[str, Any]:
    if type(report) is not WeatherHurricaneRapidIntensificationDigestReport:
        raise ValueError(
            "report must be a WeatherHurricaneRapidIntensificationDigestReport",
        )
    _require_hard_flags(report)
    value = _json_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    _require_payload_hard_flags(value)
    _reject_unsafe_payload(value)
    return value


def _row_from_observation(
    value: WeatherHurricaneRapidIntensificationObservation,
    *,
    config: WeatherHurricaneRapidIntensificationDigestConfig,
    generated_at: datetime,
) -> WeatherHurricaneRapidIntensificationDigestRow:
    source_age_seconds = _seconds_between(
        generated_at,
        value.source_observed_at,
        "source_observed_at",
    )
    _seconds_between(generated_at, value.forecast_valid_at, "forecast_valid_at")
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    confident_enough = value.forecast_confidence >= config.min_watch_confidence
    rapid_24h_change = (
        value.intensification_24h_knots
        >= config.rapid_intensification_24h_threshold_knots
    )
    rapid_probability = (
        value.rapid_intensification_probability
        >= config.rapid_intensification_probability_threshold
    )
    watch_24h_change = (
        value.intensification_24h_knots
        >= config.watch_intensification_24h_threshold_knots
    )
    watch_probability = (
        value.rapid_intensification_probability >= config.watch_probability_threshold
    )
    rapid_signal = confident_enough and (rapid_24h_change or rapid_probability)
    watch_signal = confident_enough and (watch_24h_change or watch_probability)
    if rapid_signal:
        status = RAPID_INTENSIFICATION_STATUS
    elif watch_signal:
        status = RAPID_INTENSIFICATION_WATCH_STATUS
    else:
        status = LOW_SIGNAL_STATUS
    confidence_cap = ONE if source_fresh else STALE_CONFIDENCE_CAP
    return WeatherHurricaneRapidIntensificationDigestRow(
        event_id=value.event_id,
        storm_id=value.storm_id,
        basin=value.basin,
        storm_name=value.storm_name,
        forecast_region=value.forecast_region,
        redacted_source_reference=_redact_public_reference(value.source_reference),
        forecast_valid_at=value.forecast_valid_at,
        source_observed_at=value.source_observed_at,
        source_age_seconds=source_age_seconds,
        current_max_sustained_wind_knots=value.current_max_sustained_wind_knots,
        forecast_24h_max_sustained_wind_knots=(
            value.forecast_24h_max_sustained_wind_knots
        ),
        intensification_24h_knots=value.intensification_24h_knots,
        rapid_intensification_probability=value.rapid_intensification_probability,
        forecast_confidence=value.forecast_confidence,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.forecast_confidence, confidence_cap),
        rapid_intensification_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            status=status,
            source_fresh=source_fresh,
            rapid_24h_change=rapid_24h_change,
            rapid_probability=rapid_probability,
            watch_24h_change=watch_24h_change,
            watch_probability=watch_probability,
            forecast_confidence=value.forecast_confidence,
            high_confidence_threshold=config.high_confidence_threshold,
        ),
    )


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    status: str,
    source_fresh: bool,
    rapid_24h_change: bool,
    rapid_probability: bool,
    watch_24h_change: bool,
    watch_probability: bool,
    forecast_confidence: Decimal,
    high_confidence_threshold: Decimal,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == RAPID_INTENSIFICATION_STATUS:
        if rapid_24h_change:
            reason_codes.append("hurricane_rapid_intensification_24h_threshold")
        if rapid_probability:
            reason_codes.append(
                "hurricane_rapid_intensification_probability_threshold",
            )
    elif status == RAPID_INTENSIFICATION_WATCH_STATUS:
        if watch_24h_change:
            reason_codes.append("hurricane_rapid_intensification_watch_24h_change")
        if watch_probability:
            reason_codes.append("hurricane_rapid_intensification_watch_probability")
    else:
        reason_codes.append("hurricane_rapid_intensification_low_signal")
    reason_codes.append(
        "hurricane_rapid_intensification_source_fresh"
        if source_fresh
        else "hurricane_rapid_intensification_source_stale",
    )
    if forecast_confidence >= high_confidence_threshold:
        reason_codes.append("hurricane_rapid_intensification_high_confidence")
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_observations(
    observations: Iterable[WeatherHurricaneRapidIntensificationObservation],
) -> tuple[WeatherHurricaneRapidIntensificationObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for value in normalized:
        if type(value) is not WeatherHurricaneRapidIntensificationObservation:
            raise ValueError(
                "observations must contain "
                "WeatherHurricaneRapidIntensificationObservation",
            )
        _require_hard_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[WeatherHurricaneRapidIntensificationDigestRow],
) -> tuple[WeatherHurricaneRapidIntensificationDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not WeatherHurricaneRapidIntensificationDigestRow:
            raise ValueError(
                "rows must contain WeatherHurricaneRapidIntensificationDigestRow",
            )
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _validate_row_consistency(
    row: WeatherHurricaneRapidIntensificationDigestRow,
) -> None:
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    expected_reasons = {
        RAPID_INTENSIFICATION_STATUS: (
            "hurricane_rapid_intensification_24h_threshold",
            "hurricane_rapid_intensification_probability_threshold",
        ),
        RAPID_INTENSIFICATION_WATCH_STATUS: (
            "hurricane_rapid_intensification_watch_24h_change",
            "hurricane_rapid_intensification_watch_probability",
        ),
        LOW_SIGNAL_STATUS: ("hurricane_rapid_intensification_low_signal",),
    }[row.rapid_intensification_status]
    if not any(reason in row.reason_codes for reason in expected_reasons):
        raise ValueError("rapid_intensification_status must match reason_codes")
    if _contains_unsafe_reference(row.redacted_source_reference):
        raise ValueError("redacted_source_reference must be redacted")


def _validate_report_consistency(
    report: WeatherHurricaneRapidIntensificationDigestReport,
) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if (
        report.rapid_intensification_count
        + report.watch_count
        + report.low_signal_count
        != report.row_count
    ):
        raise ValueError("status counts must match row_count")
    if report.stale_source_count != _reason_count(
        report.rows,
        "hurricane_rapid_intensification_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.max_rapid_intensification_probability != _max_row_decimal(
        report.rows,
        "rapid_intensification_probability",
    ):
        raise ValueError("max_rapid_intensification_probability must match rows")
    if report.max_intensification_24h_knots != _max_row_decimal(
        report.rows,
        "intensification_24h_knots",
    ):
        raise ValueError("max_intensification_24h_knots must match rows")
    if report.max_forecast_24h_max_sustained_wind_knots != _max_row_decimal(
        report.rows,
        "forecast_24h_max_sustained_wind_knots",
    ):
        raise ValueError(
            "max_forecast_24h_max_sustained_wind_knots must match rows",
        )


def _report_reason_codes(
    rows: tuple[WeatherHurricaneRapidIntensificationDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("hurricane_rapid_intensification_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[WeatherHurricaneRapidIntensificationDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if row.rapid_intensification_status == status),
    )


def _reason_count(
    rows: tuple[WeatherHurricaneRapidIntensificationDigestRow, ...],
    code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[WeatherHurricaneRapidIntensificationDigestRow, ...],
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


def _require_rapid_intensification_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RAPID_INTENSIFICATION_STATUSES:
        raise ValueError(f"{field_name} must be a known rapid intensification status")


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
    row: WeatherHurricaneRapidIntensificationDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.rapid_intensification_status],
        -row.rapid_intensification_probability,
        -row.intensification_24h_knots,
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
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value
