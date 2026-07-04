"""Pure report-only hurricane landfall research digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any


__all__ = (
    "DEFAULT_WEATHER_HURRICANE_LANDFALL_DIGEST_CONFIG_VERSION",
    "HurricaneLandfallDigestRow",
    "HurricaneLandfallForecastObservation",
    "WeatherHurricaneLandfallDigestConfig",
    "WeatherHurricaneLandfallDigestReport",
    "build_market_research_weather_hurricane_landfall_digest",
    "market_research_weather_hurricane_landfall_digest_payload",
)


DEFAULT_WEATHER_HURRICANE_LANDFALL_DIGEST_CONFIG_VERSION = (
    "weather-hurricane-landfall-digest-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
STALE_CONFIDENCE_CAP = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64)

MAJOR_LANDFALL_STATUS = "major_landfall_signal"
LANDFALL_WATCH_STATUS = "landfall_watch"
LOW_SIGNAL_STATUS = "low_signal"
LANDFALL_STATUSES = (
    MAJOR_LANDFALL_STATUS,
    LANDFALL_WATCH_STATUS,
    LOW_SIGNAL_STATUS,
)
STATUS_RANK = {
    MAJOR_LANDFALL_STATUS: Decimal("0"),
    LANDFALL_WATCH_STATUS: Decimal("1"),
    LOW_SIGNAL_STATUS: Decimal("2"),
}


@dataclass(frozen=True)
class WeatherHurricaneLandfallDigestConfig:
    config_version: str = DEFAULT_WEATHER_HURRICANE_LANDFALL_DIGEST_CONFIG_VERSION
    max_source_age_seconds: Decimal = Decimal("900.000000")
    major_intensity_threshold: Decimal = Decimal("3.000000")
    min_watch_confidence: Decimal = Decimal("0.600000")
    high_confidence_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, WeatherHurricaneLandfallDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("max_source_age_seconds", "major_intensity_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_watch_confidence", "high_confidence_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class HurricaneLandfallForecastObservation:
    event_id: str
    basin: str
    storm_name: str
    landfall_region: str
    forecast_valid_at: datetime
    source_observed_at: datetime
    landfall_probability: Decimal
    expected_intensity_category: Decimal
    forecast_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, HurricaneLandfallForecastObservation, "observation")
        for field_name in ("event_id", "basin", "storm_name", "landfall_region"):
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
            "landfall_probability",
            _normalize_probability("landfall_probability", self.landfall_probability),
        )
        object.__setattr__(
            self,
            "expected_intensity_category",
            _normalize_nonnegative_decimal(
                "expected_intensity_category",
                self.expected_intensity_category,
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
class HurricaneLandfallDigestRow:
    event_id: str
    basin: str
    storm_name: str
    landfall_region: str
    forecast_valid_at: datetime
    source_observed_at: datetime
    source_age_seconds: Decimal
    landfall_probability: Decimal
    expected_intensity_category: Decimal
    forecast_confidence: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    landfall_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, HurricaneLandfallDigestRow, "row")
        for field_name in ("event_id", "basin", "storm_name", "landfall_region"):
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
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "landfall_probability",
            _normalize_probability("landfall_probability", self.landfall_probability),
        )
        object.__setattr__(
            self,
            "expected_intensity_category",
            _normalize_nonnegative_decimal(
                "expected_intensity_category",
                self.expected_intensity_category,
            ),
        )
        for field_name in ("forecast_confidence", "confidence_cap", "capped_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_landfall_status("landfall_status", self.landfall_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class WeatherHurricaneLandfallDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    major_landfall_count: Decimal
    watch_landfall_count: Decimal
    low_signal_count: Decimal
    stale_source_count: Decimal
    max_landfall_probability: Decimal
    max_expected_intensity_category: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[HurricaneLandfallDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, WeatherHurricaneLandfallDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "major_landfall_count",
            "watch_landfall_count",
            "low_signal_count",
            "stale_source_count",
            "max_landfall_probability",
            "max_expected_intensity_category",
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


def build_market_research_weather_hurricane_landfall_digest(
    observations: Iterable[HurricaneLandfallForecastObservation],
    *,
    config: WeatherHurricaneLandfallDigestConfig,
    generated_at: datetime,
) -> WeatherHurricaneLandfallDigestReport:
    if type(config) is not WeatherHurricaneLandfallDigestConfig:
        raise ValueError("config must be a WeatherHurricaneLandfallDigestConfig")
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

    return WeatherHurricaneLandfallDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        major_landfall_count=_status_count(rows, MAJOR_LANDFALL_STATUS),
        watch_landfall_count=_status_count(rows, LANDFALL_WATCH_STATUS),
        low_signal_count=_status_count(rows, LOW_SIGNAL_STATUS),
        stale_source_count=_reason_count(rows, "hurricane_landfall_source_stale"),
        max_landfall_probability=_max_row_decimal(rows, "landfall_probability"),
        max_expected_intensity_category=_max_row_decimal(
            rows,
            "expected_intensity_category",
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_research_weather_hurricane_landfall_digest_payload(
    report: WeatherHurricaneLandfallDigestReport,
) -> dict[str, Any]:
    if type(report) is not WeatherHurricaneLandfallDigestReport:
        raise ValueError("report must be a WeatherHurricaneLandfallDigestReport")
    value = _json_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    return value


def _row_from_observation(
    value: HurricaneLandfallForecastObservation,
    *,
    config: WeatherHurricaneLandfallDigestConfig,
    generated_at: datetime,
) -> HurricaneLandfallDigestRow:
    source_age_seconds = _seconds_between(
        generated_at,
        value.source_observed_at,
        "source_observed_at",
    )
    _seconds_between(generated_at, value.forecast_valid_at, "forecast_valid_at")
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    landfall_watch = (
        value.landfall_probability > ZERO
        and value.forecast_confidence >= config.min_watch_confidence
    )
    major_signal = (
        landfall_watch
        and value.expected_intensity_category >= config.major_intensity_threshold
    )
    if major_signal:
        status = MAJOR_LANDFALL_STATUS
    elif landfall_watch:
        status = LANDFALL_WATCH_STATUS
    else:
        status = LOW_SIGNAL_STATUS
    confidence_cap = ONE if source_fresh else STALE_CONFIDENCE_CAP
    return HurricaneLandfallDigestRow(
        event_id=value.event_id,
        basin=value.basin,
        storm_name=value.storm_name,
        landfall_region=value.landfall_region,
        forecast_valid_at=value.forecast_valid_at,
        source_observed_at=value.source_observed_at,
        source_age_seconds=source_age_seconds,
        landfall_probability=value.landfall_probability,
        expected_intensity_category=value.expected_intensity_category,
        forecast_confidence=value.forecast_confidence,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.forecast_confidence, confidence_cap),
        landfall_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            status=status,
            source_fresh=source_fresh,
            forecast_confidence=value.forecast_confidence,
            high_confidence_threshold=config.high_confidence_threshold,
        ),
    )


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    status: str,
    source_fresh: bool,
    forecast_confidence: Decimal,
    high_confidence_threshold: Decimal,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == MAJOR_LANDFALL_STATUS:
        reason_codes.append("hurricane_landfall_major_intensity_signal")
        reason_codes.append("hurricane_landfall_watch_probability")
    elif status == LANDFALL_WATCH_STATUS:
        reason_codes.append("hurricane_landfall_watch_probability")
    else:
        reason_codes.append("hurricane_landfall_low_signal")
    reason_codes.append(
        "hurricane_landfall_source_fresh"
        if source_fresh
        else "hurricane_landfall_source_stale",
    )
    if forecast_confidence >= high_confidence_threshold:
        reason_codes.append("hurricane_landfall_high_confidence")
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_observations(
    observations: Iterable[HurricaneLandfallForecastObservation],
) -> tuple[HurricaneLandfallForecastObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for value in normalized:
        if type(value) is not HurricaneLandfallForecastObservation:
            raise ValueError(
                "observations must contain HurricaneLandfallForecastObservation",
            )
        _require_hard_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[HurricaneLandfallDigestRow],
) -> tuple[HurricaneLandfallDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not HurricaneLandfallDigestRow:
            raise ValueError("rows must contain HurricaneLandfallDigestRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _validate_row_consistency(row: HurricaneLandfallDigestRow) -> None:
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    expected_reason = {
        MAJOR_LANDFALL_STATUS: "hurricane_landfall_major_intensity_signal",
        LANDFALL_WATCH_STATUS: "hurricane_landfall_watch_probability",
        LOW_SIGNAL_STATUS: "hurricane_landfall_low_signal",
    }[row.landfall_status]
    if expected_reason not in row.reason_codes:
        raise ValueError("landfall_status must match reason_codes")


def _validate_report_consistency(report: WeatherHurricaneLandfallDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if (
        report.major_landfall_count
        + report.watch_landfall_count
        + report.low_signal_count
        != report.row_count
    ):
        raise ValueError("status counts must match row_count")
    if report.stale_source_count != _reason_count(
        report.rows,
        "hurricane_landfall_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.max_landfall_probability != _max_row_decimal(
        report.rows,
        "landfall_probability",
    ):
        raise ValueError("max_landfall_probability must match rows")
    if report.max_expected_intensity_category != _max_row_decimal(
        report.rows,
        "expected_intensity_category",
    ):
        raise ValueError("max_expected_intensity_category must match rows")


def _report_reason_codes(
    rows: tuple[HurricaneLandfallDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("hurricane_landfall_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(rows: tuple[HurricaneLandfallDigestRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.landfall_status == status))


def _reason_count(rows: tuple[HurricaneLandfallDigestRow, ...], code: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[HurricaneLandfallDigestRow, ...],
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


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_landfall_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in LANDFALL_STATUSES:
        raise ValueError(f"{field_name} must be a known landfall status")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(row: HurricaneLandfallDigestRow) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.landfall_status],
        -row.landfall_probability,
        row.event_id,
    )


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
