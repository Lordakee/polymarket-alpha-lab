"""Pure report-only convective outlook upgrade digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any


__all__ = (
    "DEFAULT_WEATHER_CONVECTIVE_OUTLOOK_UPGRADE_DIGEST_CONFIG_VERSION",
    "ConvectiveOutlookUpgradeDigestConfig",
    "ConvectiveOutlookUpgradeDigestRow",
    "ConvectiveOutlookUpgradeObservation",
    "WeatherConvectiveOutlookUpgradeDigestReport",
    "build_market_research_weather_convective_outlook_upgrade_digest",
    "market_research_weather_convective_outlook_upgrade_digest_payload",
)


DEFAULT_WEATHER_CONVECTIVE_OUTLOOK_UPGRADE_DIGEST_CONFIG_VERSION = (
    "weather-convective-outlook-upgrade-digest-v1"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
STALE_CONFIDENCE_CAP = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64)

HIGH_UPGRADE_RISK_STATUS = "high_upgrade_risk"
UPGRADE_WATCH_STATUS = "upgrade_watch"
LOW_UPGRADE_RISK_STATUS = "low_upgrade_risk"
UPGRADE_STATUSES = (
    HIGH_UPGRADE_RISK_STATUS,
    UPGRADE_WATCH_STATUS,
    LOW_UPGRADE_RISK_STATUS,
)
STATUS_RANK = {
    HIGH_UPGRADE_RISK_STATUS: Decimal("0"),
    UPGRADE_WATCH_STATUS: Decimal("1"),
    LOW_UPGRADE_RISK_STATUS: Decimal("2"),
}

RISK_CATEGORIES = (
    "general",
    "marginal",
    "slight",
    "enhanced",
    "moderate",
    "high",
)
CATEGORY_RANK = {
    "general": Decimal("0"),
    "marginal": Decimal("1"),
    "slight": Decimal("2"),
    "enhanced": Decimal("3"),
    "moderate": Decimal("4"),
    "high": Decimal("5"),
}


@dataclass(frozen=True)
class ConvectiveOutlookUpgradeDigestConfig:
    config_version: str = DEFAULT_WEATHER_CONVECTIVE_OUTLOOK_UPGRADE_DIGEST_CONFIG_VERSION
    max_source_age_seconds: Decimal = Decimal("900.000000")
    high_upgrade_risk_score: Decimal = Decimal("0.700000")
    watch_upgrade_risk_score: Decimal = Decimal("0.500000")
    severe_probability_watch: Decimal = Decimal("0.150000")
    significant_severe_probability_watch: Decimal = Decimal("0.100000")
    model_agreement_watch: Decimal = Decimal("0.650000")
    population_exposure_watch: Decimal = Decimal("0.650000")
    high_confidence_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ConvectiveOutlookUpgradeDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "high_upgrade_risk_score",
            "watch_upgrade_risk_score",
            "severe_probability_watch",
            "significant_severe_probability_watch",
            "model_agreement_watch",
            "population_exposure_watch",
            "high_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.high_upgrade_risk_score < self.watch_upgrade_risk_score:
            raise ValueError("high_upgrade_risk_score must be at least watch threshold")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ConvectiveOutlookUpgradeObservation:
    outlook_id: str
    region_key: str
    current_risk_category: str
    target_risk_category: str
    outlook_valid_at: datetime
    source_observed_at: datetime
    upgrade_signal_probability: Decimal
    severe_probability: Decimal
    significant_severe_probability: Decimal
    model_agreement_score: Decimal
    population_exposure_score: Decimal
    forecast_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ConvectiveOutlookUpgradeObservation, "observation")
        for field_name in ("outlook_id", "region_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_risk_category("current_risk_category", self.current_risk_category)
        _require_risk_category("target_risk_category", self.target_risk_category)
        _validate_upgrade_categories(
            self.current_risk_category,
            self.target_risk_category,
        )
        object.__setattr__(
            self,
            "outlook_valid_at",
            _as_utc("outlook_valid_at", self.outlook_valid_at),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in (
            "upgrade_signal_probability",
            "severe_probability",
            "significant_severe_probability",
            "model_agreement_score",
            "population_exposure_score",
            "forecast_confidence",
        ):
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
class ConvectiveOutlookUpgradeDigestRow:
    outlook_id: str
    region_key: str
    current_risk_category: str
    target_risk_category: str
    outlook_valid_at: datetime
    source_observed_at: datetime
    source_age_seconds: Decimal
    upgrade_step_count: Decimal
    upgrade_signal_probability: Decimal
    severe_probability: Decimal
    significant_severe_probability: Decimal
    model_agreement_score: Decimal
    population_exposure_score: Decimal
    forecast_confidence: Decimal
    upgrade_risk_score: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    upgrade_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ConvectiveOutlookUpgradeDigestRow, "row")
        for field_name in ("outlook_id", "region_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_risk_category("current_risk_category", self.current_risk_category)
        _require_risk_category("target_risk_category", self.target_risk_category)
        _validate_upgrade_categories(
            self.current_risk_category,
            self.target_risk_category,
        )
        object.__setattr__(
            self,
            "outlook_valid_at",
            _as_utc("outlook_valid_at", self.outlook_valid_at),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in ("source_age_seconds", "upgrade_step_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "upgrade_signal_probability",
            "severe_probability",
            "significant_severe_probability",
            "model_agreement_score",
            "population_exposure_score",
            "forecast_confidence",
            "upgrade_risk_score",
            "confidence_cap",
            "capped_confidence",
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
class WeatherConvectiveOutlookUpgradeDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    high_upgrade_risk_count: Decimal
    upgrade_watch_count: Decimal
    low_upgrade_risk_count: Decimal
    stale_source_count: Decimal
    max_upgrade_risk_score: Decimal
    max_severe_probability: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ConvectiveOutlookUpgradeDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, WeatherConvectiveOutlookUpgradeDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "high_upgrade_risk_count",
            "upgrade_watch_count",
            "low_upgrade_risk_count",
            "stale_source_count",
            "max_upgrade_risk_score",
            "max_severe_probability",
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


def build_market_research_weather_convective_outlook_upgrade_digest(
    observations: Iterable[ConvectiveOutlookUpgradeObservation],
    *,
    config: ConvectiveOutlookUpgradeDigestConfig,
    generated_at: datetime,
) -> WeatherConvectiveOutlookUpgradeDigestReport:
    if type(config) is not ConvectiveOutlookUpgradeDigestConfig:
        raise ValueError("config must be a ConvectiveOutlookUpgradeDigestConfig")
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

    return WeatherConvectiveOutlookUpgradeDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        high_upgrade_risk_count=_status_count(rows, HIGH_UPGRADE_RISK_STATUS),
        upgrade_watch_count=_status_count(rows, UPGRADE_WATCH_STATUS),
        low_upgrade_risk_count=_status_count(rows, LOW_UPGRADE_RISK_STATUS),
        stale_source_count=_reason_count(
            rows,
            "convective_outlook_upgrade_source_stale",
        ),
        max_upgrade_risk_score=_max_row_decimal(rows, "upgrade_risk_score"),
        max_severe_probability=_max_row_decimal(rows, "severe_probability"),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_research_weather_convective_outlook_upgrade_digest_payload(
    report: WeatherConvectiveOutlookUpgradeDigestReport,
) -> dict[str, Any]:
    if type(report) is not WeatherConvectiveOutlookUpgradeDigestReport:
        raise ValueError("report must be a WeatherConvectiveOutlookUpgradeDigestReport")
    value = _json_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    return value


def _row_from_observation(
    value: ConvectiveOutlookUpgradeObservation,
    *,
    config: ConvectiveOutlookUpgradeDigestConfig,
    generated_at: datetime,
) -> ConvectiveOutlookUpgradeDigestRow:
    source_age_seconds = _seconds_between(
        generated_at,
        value.source_observed_at,
        "source_observed_at",
    )
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    upgrade_step_count = _upgrade_step_count(
        value.current_risk_category,
        value.target_risk_category,
    )
    upgrade_risk_score = _upgrade_risk_score(
        upgrade_signal_probability=value.upgrade_signal_probability,
        severe_probability=value.severe_probability,
        significant_severe_probability=value.significant_severe_probability,
        model_agreement_score=value.model_agreement_score,
        population_exposure_score=value.population_exposure_score,
    )
    status = _upgrade_status(
        upgrade_risk_score=upgrade_risk_score,
        severe_probability=value.severe_probability,
        significant_severe_probability=value.significant_severe_probability,
        model_agreement_score=value.model_agreement_score,
        population_exposure_score=value.population_exposure_score,
        config=config,
    )
    confidence_cap = ONE if source_fresh else STALE_CONFIDENCE_CAP
    return ConvectiveOutlookUpgradeDigestRow(
        outlook_id=value.outlook_id,
        region_key=value.region_key,
        current_risk_category=value.current_risk_category,
        target_risk_category=value.target_risk_category,
        outlook_valid_at=value.outlook_valid_at,
        source_observed_at=value.source_observed_at,
        source_age_seconds=source_age_seconds,
        upgrade_step_count=upgrade_step_count,
        upgrade_signal_probability=value.upgrade_signal_probability,
        severe_probability=value.severe_probability,
        significant_severe_probability=value.significant_severe_probability,
        model_agreement_score=value.model_agreement_score,
        population_exposure_score=value.population_exposure_score,
        forecast_confidence=value.forecast_confidence,
        upgrade_risk_score=upgrade_risk_score,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.forecast_confidence, confidence_cap),
        upgrade_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            status=status,
            source_fresh=source_fresh,
            upgrade_step_count=upgrade_step_count,
            severe_probability=value.severe_probability,
            significant_severe_probability=value.significant_severe_probability,
            model_agreement_score=value.model_agreement_score,
            population_exposure_score=value.population_exposure_score,
            forecast_confidence=value.forecast_confidence,
            config=config,
        ),
    )


def _upgrade_risk_score(
    *,
    upgrade_signal_probability: Decimal,
    severe_probability: Decimal,
    significant_severe_probability: Decimal,
    model_agreement_score: Decimal,
    population_exposure_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            upgrade_signal_probability * Decimal("0.400000")
            + severe_probability * Decimal("0.250000")
            + significant_severe_probability * Decimal("0.150000")
            + model_agreement_score * Decimal("0.100000")
            + population_exposure_score * Decimal("0.100000"),
        )


def _upgrade_status(
    *,
    upgrade_risk_score: Decimal,
    severe_probability: Decimal,
    significant_severe_probability: Decimal,
    model_agreement_score: Decimal,
    population_exposure_score: Decimal,
    config: ConvectiveOutlookUpgradeDigestConfig,
) -> str:
    if upgrade_risk_score >= config.high_upgrade_risk_score:
        return HIGH_UPGRADE_RISK_STATUS
    if (
        upgrade_risk_score >= config.watch_upgrade_risk_score
        or severe_probability >= config.severe_probability_watch
        or significant_severe_probability >= config.significant_severe_probability_watch
        or model_agreement_score >= config.model_agreement_watch
        or population_exposure_score >= config.population_exposure_watch
    ):
        return UPGRADE_WATCH_STATUS
    return LOW_UPGRADE_RISK_STATUS


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    status: str,
    source_fresh: bool,
    upgrade_step_count: Decimal,
    severe_probability: Decimal,
    significant_severe_probability: Decimal,
    model_agreement_score: Decimal,
    population_exposure_score: Decimal,
    forecast_confidence: Decimal,
    config: ConvectiveOutlookUpgradeDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == HIGH_UPGRADE_RISK_STATUS:
        reason_codes.append("convective_outlook_upgrade_high_risk")
    elif status == UPGRADE_WATCH_STATUS:
        reason_codes.append("convective_outlook_upgrade_watch")
    else:
        reason_codes.append("convective_outlook_upgrade_low_risk")
    reason_codes.append(
        "convective_outlook_upgrade_source_fresh"
        if source_fresh
        else "convective_outlook_upgrade_source_stale",
    )
    if forecast_confidence >= config.high_confidence_threshold:
        reason_codes.append("convective_outlook_upgrade_high_confidence")
    if upgrade_step_count > ONE:
        reason_codes.append("convective_outlook_upgrade_multi_step")
    if severe_probability >= config.severe_probability_watch:
        reason_codes.append("convective_outlook_upgrade_severe_probability")
    if significant_severe_probability >= config.significant_severe_probability_watch:
        reason_codes.append("convective_outlook_upgrade_significant_severe_probability")
    if model_agreement_score >= config.model_agreement_watch:
        reason_codes.append("convective_outlook_upgrade_model_agreement")
    if population_exposure_score >= config.population_exposure_watch:
        reason_codes.append("convective_outlook_upgrade_population_exposure")
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_observations(
    observations: Iterable[ConvectiveOutlookUpgradeObservation],
) -> tuple[ConvectiveOutlookUpgradeObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for value in normalized:
        if type(value) is not ConvectiveOutlookUpgradeObservation:
            raise ValueError(
                "observations must contain ConvectiveOutlookUpgradeObservation",
            )
        _require_hard_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[ConvectiveOutlookUpgradeDigestRow],
) -> tuple[ConvectiveOutlookUpgradeDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ConvectiveOutlookUpgradeDigestRow:
            raise ValueError("rows must contain ConvectiveOutlookUpgradeDigestRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _validate_row_consistency(row: ConvectiveOutlookUpgradeDigestRow) -> None:
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    if row.upgrade_step_count != _upgrade_step_count(
        row.current_risk_category,
        row.target_risk_category,
    ):
        raise ValueError("upgrade_step_count must match risk categories")
    expected_reason = {
        HIGH_UPGRADE_RISK_STATUS: "convective_outlook_upgrade_high_risk",
        UPGRADE_WATCH_STATUS: "convective_outlook_upgrade_watch",
        LOW_UPGRADE_RISK_STATUS: "convective_outlook_upgrade_low_risk",
    }[row.upgrade_status]
    if expected_reason not in row.reason_codes:
        raise ValueError("upgrade_status must match reason_codes")


def _validate_report_consistency(
    report: WeatherConvectiveOutlookUpgradeDigestReport,
) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if (
        report.high_upgrade_risk_count
        + report.upgrade_watch_count
        + report.low_upgrade_risk_count
        != report.row_count
    ):
        raise ValueError("status counts must match row_count")
    if report.stale_source_count != _reason_count(
        report.rows,
        "convective_outlook_upgrade_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.max_upgrade_risk_score != _max_row_decimal(
        report.rows,
        "upgrade_risk_score",
    ):
        raise ValueError("max_upgrade_risk_score must match rows")
    if report.max_severe_probability != _max_row_decimal(
        report.rows,
        "severe_probability",
    ):
        raise ValueError("max_severe_probability must match rows")


def _report_reason_codes(
    rows: tuple[ConvectiveOutlookUpgradeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("convective_outlook_upgrade_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ConvectiveOutlookUpgradeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.upgrade_status == status))


def _reason_count(rows: tuple[ConvectiveOutlookUpgradeDigestRow, ...], code: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[ConvectiveOutlookUpgradeDigestRow, ...],
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


def _upgrade_step_count(current_risk_category: str, target_risk_category: str) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            CATEGORY_RANK[target_risk_category] - CATEGORY_RANK[current_risk_category],
        )


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


def _require_risk_category(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RISK_CATEGORIES:
        raise ValueError(f"{field_name} must be a known convective risk category")


def _validate_upgrade_categories(
    current_risk_category: str,
    target_risk_category: str,
) -> None:
    if CATEGORY_RANK[target_risk_category] <= CATEGORY_RANK[current_risk_category]:
        raise ValueError("target_risk_category must be higher than current_risk_category")


def _require_upgrade_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in UPGRADE_STATUSES:
        raise ValueError(f"{field_name} must be a known upgrade status")


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


def _row_sort_key(
    row: ConvectiveOutlookUpgradeDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.upgrade_status],
        -row.upgrade_risk_score,
        -row.severe_probability,
        row.outlook_id,
        row.region_key,
    )


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
