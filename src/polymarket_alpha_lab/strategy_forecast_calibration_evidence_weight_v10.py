"""Pure report-only screening for forecast calibration evidence weight v10."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONFIG_VERSION = "strategy_forecast_calibration_evidence_weight_v10"
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
DECIMAL_CONTEXT = Context(prec=64)

CALIBRATION_WEIGHT = Decimal("0.340000")
FRESHNESS_WEIGHT = Decimal("0.250000")
SOURCE_INDEPENDENCE_WEIGHT = Decimal("0.230000")
LIQUIDITY_WEIGHT = Decimal("0.100000")
RESOLUTION_CLARITY_WEIGHT = Decimal("0.080000")

SCREENING_STATUSES = ("pass", "watch", "reject")
REASON_CODES = (
    "calibration_supported",
    "calibration_error_elevated",
    "evidence_fresh",
    "evidence_stale",
    "source_independence_strong",
    "source_independence_mixed",
    "source_independence_weak",
    "liquidity_supported",
    "liquidity_thin",
    "resolution_clear",
    "resolution_ambiguous",
)


@dataclass(frozen=True)
class ForecastCalibrationEvidenceWeightConfig:
    max_evidence_age_hours: Decimal = Decimal("96.000000")
    target_independent_source_count: Decimal = Decimal("4")
    max_correlated_source_count: Decimal = Decimal("4")
    target_market_liquidity_usd: Decimal = Decimal("10000.000000")
    pass_evidence_weight_score: Decimal = Decimal("0.700000")
    watch_evidence_weight_score: Decimal = Decimal("0.450000")
    config_version: str = DEFAULT_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ForecastCalibrationEvidenceWeightConfig:
            raise ValueError("config must be exact")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_evidence_age_hours",
            _normalize_positive_decimal(
                "max_evidence_age_hours",
                self.max_evidence_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "target_independent_source_count",
            _normalize_positive_whole_decimal(
                "target_independent_source_count",
                self.target_independent_source_count,
            ),
        )
        object.__setattr__(
            self,
            "max_correlated_source_count",
            _normalize_positive_whole_decimal(
                "max_correlated_source_count",
                self.max_correlated_source_count,
            ),
        )
        object.__setattr__(
            self,
            "target_market_liquidity_usd",
            _normalize_positive_decimal(
                "target_market_liquidity_usd",
                self.target_market_liquidity_usd,
            ),
        )
        object.__setattr__(
            self,
            "pass_evidence_weight_score",
            _normalize_probability(
                "pass_evidence_weight_score",
                self.pass_evidence_weight_score,
            ),
        )
        object.__setattr__(
            self,
            "watch_evidence_weight_score",
            _normalize_probability(
                "watch_evidence_weight_score",
                self.watch_evidence_weight_score,
            ),
        )
        if self.pass_evidence_weight_score < self.watch_evidence_weight_score:
            raise ValueError(
                "pass_evidence_weight_score must be at least watch_evidence_weight_score",
            )
        reject_unsafe_surface_fields("forecast calibration evidence config", self)
        require_paper_only_flags("ForecastCalibrationEvidenceWeightConfig", self)


@dataclass(frozen=True)
class ForecastCalibrationEvidenceWeightInput:
    forecast_id: str
    market_id: str
    observed_at: datetime
    forecast_probability: Decimal
    historical_calibration_error: Decimal
    evidence_age_hours: Decimal
    independent_source_count: Decimal
    correlated_source_count: Decimal
    market_liquidity_usd: Decimal
    resolution_clarity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ForecastCalibrationEvidenceWeightInput:
            raise ValueError("input must be exact")
        _require_canonical_string("forecast_id", self.forecast_id)
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "historical_calibration_error",
            "resolution_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_age_hours", "market_liquidity_usd"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("independent_source_count", "correlated_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        reject_unsafe_surface_fields("forecast calibration evidence input", self)
        require_paper_only_flags("ForecastCalibrationEvidenceWeightInput", self)


@dataclass(frozen=True)
class ForecastCalibrationEvidenceWeightRow:
    config_version: str
    forecast_id: str
    market_id: str
    observed_at: datetime
    forecast_probability: Decimal
    historical_calibration_error: Decimal
    evidence_age_hours: Decimal
    independent_source_count: Decimal
    correlated_source_count: Decimal
    market_liquidity_usd: Decimal
    calibration_score: Decimal
    freshness_score: Decimal
    source_independence_score: Decimal
    liquidity_score: Decimal
    resolution_clarity_score: Decimal
    evidence_weight_score: Decimal
    screening_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ForecastCalibrationEvidenceWeightRow:
            raise ValueError("row must be exact")
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("forecast_id", self.forecast_id)
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "historical_calibration_error",
            "calibration_score",
            "freshness_score",
            "source_independence_score",
            "liquidity_score",
            "resolution_clarity_score",
            "evidence_weight_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_age_hours", "market_liquidity_usd"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("independent_source_count", "correlated_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_member("screening_status", self.screening_status, SCREENING_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        reject_unsafe_surface_fields("forecast calibration evidence row", self)
        require_paper_only_flags("ForecastCalibrationEvidenceWeightRow", self)


def weight_forecast_calibration_evidence(
    forecast_input: ForecastCalibrationEvidenceWeightInput,
    *,
    config: ForecastCalibrationEvidenceWeightConfig | None = None,
) -> ForecastCalibrationEvidenceWeightRow:
    """Weight a forecast's evidence value without side effects or live trading access."""

    if type(forecast_input) is not ForecastCalibrationEvidenceWeightInput:
        raise ValueError("forecast_input must be a ForecastCalibrationEvidenceWeightInput")
    if config is None:
        config = ForecastCalibrationEvidenceWeightConfig()
    if type(config) is not ForecastCalibrationEvidenceWeightConfig:
        raise ValueError("config must be a ForecastCalibrationEvidenceWeightConfig")

    calibration_score = _normalize_probability(
        "calibration_score",
        _quantize_probability(ONE - forecast_input.historical_calibration_error),
    )
    freshness_score = _ratio_score(
        config.max_evidence_age_hours - forecast_input.evidence_age_hours,
        config.max_evidence_age_hours,
    )
    source_independence_score = _source_independence_score(forecast_input, config)
    liquidity_score = _ratio_score(
        forecast_input.market_liquidity_usd,
        config.target_market_liquidity_usd,
    )
    evidence_weight_score = _weighted_score(
        calibration_score=calibration_score,
        freshness_score=freshness_score,
        source_independence_score=source_independence_score,
        liquidity_score=liquidity_score,
        resolution_clarity_score=forecast_input.resolution_clarity_score,
    )

    return ForecastCalibrationEvidenceWeightRow(
        config_version=config.config_version,
        forecast_id=forecast_input.forecast_id,
        market_id=forecast_input.market_id,
        observed_at=forecast_input.observed_at,
        forecast_probability=forecast_input.forecast_probability,
        historical_calibration_error=forecast_input.historical_calibration_error,
        evidence_age_hours=forecast_input.evidence_age_hours,
        independent_source_count=forecast_input.independent_source_count,
        correlated_source_count=forecast_input.correlated_source_count,
        market_liquidity_usd=forecast_input.market_liquidity_usd,
        calibration_score=calibration_score,
        freshness_score=freshness_score,
        source_independence_score=source_independence_score,
        liquidity_score=liquidity_score,
        resolution_clarity_score=forecast_input.resolution_clarity_score,
        evidence_weight_score=evidence_weight_score,
        screening_status=_screening_status(evidence_weight_score, config),
        reason_codes=_reason_codes(
            calibration_score=calibration_score,
            freshness_score=freshness_score,
            source_independence_score=source_independence_score,
            liquidity_score=liquidity_score,
            resolution_clarity_score=forecast_input.resolution_clarity_score,
        ),
    )


def strategy_forecast_calibration_evidence_weight_payload(
    row: ForecastCalibrationEvidenceWeightRow,
) -> dict[str, Any]:
    if type(row) is not ForecastCalibrationEvidenceWeightRow:
        raise ValueError("row must be a ForecastCalibrationEvidenceWeightRow")
    payload = json_ready_no_floats(asdict(row))
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    return payload


def _source_independence_score(
    forecast_input: ForecastCalibrationEvidenceWeightInput,
    config: ForecastCalibrationEvidenceWeightConfig,
) -> Decimal:
    independent_coverage = _ratio_score(
        forecast_input.independent_source_count,
        config.target_independent_source_count,
    )
    with localcontext(DECIMAL_CONTEXT):
        correlation_denominator = config.max_correlated_source_count * TWO
        correlation_drag = forecast_input.correlated_source_count / correlation_denominator
        correlation_penalty = _clamp_probability(ONE - correlation_drag)
        return _quantize_probability(independent_coverage * correlation_penalty)


def _weighted_score(
    *,
    calibration_score: Decimal,
    freshness_score: Decimal,
    source_independence_score: Decimal,
    liquidity_score: Decimal,
    resolution_clarity_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_probability(
            (calibration_score * CALIBRATION_WEIGHT)
            + (freshness_score * FRESHNESS_WEIGHT)
            + (source_independence_score * SOURCE_INDEPENDENCE_WEIGHT)
            + (liquidity_score * LIQUIDITY_WEIGHT)
            + (resolution_clarity_score * RESOLUTION_CLARITY_WEIGHT),
        )


def _screening_status(
    evidence_weight_score: Decimal,
    config: ForecastCalibrationEvidenceWeightConfig,
) -> str:
    if evidence_weight_score >= config.pass_evidence_weight_score:
        return "pass"
    if evidence_weight_score >= config.watch_evidence_weight_score:
        return "watch"
    return "reject"


def _reason_codes(
    *,
    calibration_score: Decimal,
    freshness_score: Decimal,
    source_independence_score: Decimal,
    liquidity_score: Decimal,
    resolution_clarity_score: Decimal,
) -> tuple[str, ...]:
    codes = [
        "calibration_supported"
        if calibration_score >= Decimal("0.800000")
        else "calibration_error_elevated",
        "evidence_fresh" if freshness_score >= Decimal("0.500000") else "evidence_stale",
        _source_independence_reason_code(source_independence_score),
        "liquidity_supported" if liquidity_score >= Decimal("0.500000") else "liquidity_thin",
        "resolution_clear"
        if resolution_clarity_score >= Decimal("0.750000")
        else "resolution_ambiguous",
    ]
    return tuple(codes)


def _source_independence_reason_code(source_independence_score: Decimal) -> str:
    if source_independence_score >= Decimal("0.750000"):
        return "source_independence_strong"
    if source_independence_score >= Decimal("0.400000"):
        return "source_independence_mixed"
    return "source_independence_weak"


def _ratio_score(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if numerator <= ZERO:
            return ZERO.quantize(QUANTUM)
        return _quantize_probability(_clamp_probability(numerator / denominator))


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for value in values:
        _require_member("reason_codes", value, REASON_CODES)
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return value


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANTUM)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_whole_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(COUNT_QUANTUM)
    if value != decimal_value:
        raise ValueError(f"{field_name} must be a whole number")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _quantize_probability(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _clamp_probability(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_member(
    field_name: str,
    value: str,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


__all__ = [
    "DEFAULT_CONFIG_VERSION",
    "ForecastCalibrationEvidenceWeightConfig",
    "ForecastCalibrationEvidenceWeightInput",
    "ForecastCalibrationEvidenceWeightRow",
    "strategy_forecast_calibration_evidence_weight_payload",
    "weight_forecast_calibration_evidence",
]
