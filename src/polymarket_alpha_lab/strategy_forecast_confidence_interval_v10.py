"""Pure paper report module for probability forecast confidence intervals."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext


RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
MAX_BPS = Decimal("10000")
BPS_PER_UNIT = Decimal("10000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

BASE_HALF_WIDTH = Decimal("0.020000")
DISPERSION_WEIGHT = Decimal("0.500000")
CONFLICT_WEIGHT = Decimal("0.020833333333333333333333333333333333")
CALIBRATION_WEIGHT = Decimal("0.750000")
SAMPLE_VERY_SMALL_WIDTH = Decimal("0.053750")
SAMPLE_SMALL_WIDTH = Decimal("0.018333333333333333333333333333333333")
SAMPLE_LARGE_WIDTH = Decimal("0.000583333333333333333333333333333333")
NEAR_RESOLUTION_WIDTH = Decimal("0.045000")

VERY_SMALL_SAMPLE_MAX = Decimal("10")
SMALL_SAMPLE_MAX = Decimal("30")
LARGE_SAMPLE_MIN = Decimal("100")
MODEL_DISPERSION_ELEVATED_MIN = Decimal("0.050000")
SOURCE_CONFLICT_ELEVATED_MIN = Decimal("0.150000")
CALIBRATION_ERROR_ELEVATED_BPS_MIN = Decimal("50")
NEAR_RESOLUTION_MINUTES_MAX = Decimal("60")
HIGH_TIER_WIDTH_MAX = Decimal("0.070000")
MEDIUM_TIER_WIDTH_MAX = Decimal("0.150000")

CONFIDENCE_TIERS = ("high", "medium", "low")
CONFIDENCE_TIER_REASON_CODES = (
    "confidence_tier_high",
    "confidence_tier_medium",
    "confidence_tier_low",
)
MODEL_DISPERSION_ELEVATED_REASON_CODE = "model_dispersion_elevated"
SOURCE_CONFLICT_ELEVATED_REASON_CODE = "source_conflict_elevated"
SAMPLE_SIZE_VERY_SMALL_REASON_CODE = "sample_size_very_small"
SAMPLE_SIZE_SMALL_REASON_CODE = "sample_size_small"
CALIBRATION_ERROR_ELEVATED_REASON_CODE = "calibration_error_elevated"
NEAR_RESOLUTION_WINDOW_REASON_CODE = "near_resolution_window"
LOWER_PROBABILITY_CLAMPED_REASON_CODE = "lower_probability_clamped"
UPPER_PROBABILITY_CLAMPED_REASON_CODE = "upper_probability_clamped"
REASON_CODE_PRIORITY = (
    *CONFIDENCE_TIER_REASON_CODES,
    MODEL_DISPERSION_ELEVATED_REASON_CODE,
    SOURCE_CONFLICT_ELEVATED_REASON_CODE,
    SAMPLE_SIZE_VERY_SMALL_REASON_CODE,
    SAMPLE_SIZE_SMALL_REASON_CODE,
    CALIBRATION_ERROR_ELEVATED_REASON_CODE,
    NEAR_RESOLUTION_WINDOW_REASON_CODE,
    LOWER_PROBABILITY_CLAMPED_REASON_CODE,
    UPPER_PROBABILITY_CLAMPED_REASON_CODE,
)
REASON_CODE_SET = frozenset(REASON_CODE_PRIORITY)

__all__ = (
    "StrategyForecastConfidenceIntervalInput",
    "StrategyForecastConfidenceIntervalResult",
    "build_strategy_forecast_confidence_interval",
    "calculate_strategy_forecast_confidence_interval",
    "strategy_forecast_confidence_interval_payload",
)


@dataclass(frozen=True)
class StrategyForecastConfidenceIntervalInput:
    point_forecast: Decimal
    model_dispersion: Decimal
    source_conflict_score: Decimal
    sample_size: Decimal
    calibration_error_bps: Decimal
    time_to_resolution_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyForecastConfidenceIntervalInput:
            raise TypeError(
                "StrategyForecastConfidenceIntervalInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyForecastConfidenceIntervalInput:
            raise ValueError(
                "input_row must be exactly StrategyForecastConfidenceIntervalInput",
            )
        for field_name in (
            "point_forecast",
            "model_dispersion",
            "source_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sample_size",
            _normalize_positive_count("sample_size", self.sample_size),
        )
        object.__setattr__(
            self,
            "calibration_error_bps",
            _normalize_bps("calibration_error_bps", self.calibration_error_bps),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyForecastConfidenceIntervalResult:
    lower_probability: Decimal
    upper_probability: Decimal
    interval_width: Decimal
    confidence_tier: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyForecastConfidenceIntervalResult:
            raise TypeError(
                "StrategyForecastConfidenceIntervalResult does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyForecastConfidenceIntervalResult:
            raise ValueError(
                "result must be exactly StrategyForecastConfidenceIntervalResult",
            )
        for field_name in (
            "lower_probability",
            "upper_probability",
            "interval_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_tier("confidence_tier", self.confidence_tier)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_result(self)
        _require_hard_flags(self)


def calculate_strategy_forecast_confidence_interval(
    *,
    point_forecast: Decimal,
    model_dispersion: Decimal,
    source_conflict_score: Decimal,
    sample_size: Decimal,
    calibration_error_bps: Decimal,
    time_to_resolution_minutes: Decimal,
) -> StrategyForecastConfidenceIntervalResult:
    return build_strategy_forecast_confidence_interval(
        StrategyForecastConfidenceIntervalInput(
            point_forecast=point_forecast,
            model_dispersion=model_dispersion,
            source_conflict_score=source_conflict_score,
            sample_size=sample_size,
            calibration_error_bps=calibration_error_bps,
            time_to_resolution_minutes=time_to_resolution_minutes,
        ),
    )


def build_strategy_forecast_confidence_interval(
    input_row: StrategyForecastConfidenceIntervalInput,
) -> StrategyForecastConfidenceIntervalResult:
    if type(input_row) is not StrategyForecastConfidenceIntervalInput:
        raise ValueError(
            "input_row must be a StrategyForecastConfidenceIntervalInput",
        )
    _require_hard_flags(input_row)
    half_width = _interval_half_width(input_row)
    raw_lower = input_row.point_forecast - half_width
    raw_upper = input_row.point_forecast + half_width
    lower_probability = _clamp_probability(raw_lower)
    upper_probability = _clamp_probability(raw_upper)
    interval_width = _ratio(upper_probability - lower_probability)
    tier = _confidence_tier(_ratio(half_width + half_width))
    reason_codes = _reason_codes(
        input_row,
        confidence_tier=tier,
        lower_was_clamped=raw_lower < ZERO_RATIO,
        upper_was_clamped=raw_upper > ONE_RATIO,
    )
    return StrategyForecastConfidenceIntervalResult(
        lower_probability=lower_probability,
        upper_probability=upper_probability,
        interval_width=interval_width,
        confidence_tier=tier,
        reason_codes=reason_codes,
    )


def strategy_forecast_confidence_interval_payload(
    result: StrategyForecastConfidenceIntervalResult,
) -> dict[str, object]:
    if type(result) is not StrategyForecastConfidenceIntervalResult:
        raise ValueError(
            "result must be a StrategyForecastConfidenceIntervalResult",
        )
    _require_hard_flags(result)
    return {
        "lower_probability": str(result.lower_probability),
        "upper_probability": str(result.upper_probability),
        "interval_width": str(result.interval_width),
        "confidence_tier": result.confidence_tier,
        "reason_codes": tuple(result.reason_codes),
        "paper_only": result.paper_only,
        "report_only": result.report_only,
        "readonly": result.readonly,
    }


def _interval_half_width(
    input_row: StrategyForecastConfidenceIntervalInput,
) -> Decimal:
    calibration_ratio = input_row.calibration_error_bps / BPS_PER_UNIT
    half_width = (
        BASE_HALF_WIDTH
        + (input_row.model_dispersion * DISPERSION_WEIGHT)
        + (input_row.source_conflict_score * CONFLICT_WEIGHT)
        + (calibration_ratio * CALIBRATION_WEIGHT)
        + _sample_width(input_row.sample_size)
        + _time_width(input_row.time_to_resolution_minutes)
    )
    return _ratio(half_width)


def _sample_width(sample_size: Decimal) -> Decimal:
    if sample_size < VERY_SMALL_SAMPLE_MAX:
        return SAMPLE_VERY_SMALL_WIDTH
    if sample_size < SMALL_SAMPLE_MAX:
        return SAMPLE_SMALL_WIDTH
    if sample_size >= LARGE_SAMPLE_MIN:
        return SAMPLE_LARGE_WIDTH
    return ZERO_RATIO


def _time_width(time_to_resolution_minutes: Decimal) -> Decimal:
    if time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES_MAX:
        return NEAR_RESOLUTION_WIDTH
    return ZERO_RATIO


def _reason_codes(
    input_row: StrategyForecastConfidenceIntervalInput,
    *,
    confidence_tier: str,
    lower_was_clamped: bool,
    upper_was_clamped: bool,
) -> tuple[str, ...]:
    reason_codes = [CONFIDENCE_TIER_REASON_CODES[CONFIDENCE_TIERS.index(confidence_tier)]]
    if input_row.model_dispersion >= MODEL_DISPERSION_ELEVATED_MIN:
        reason_codes.append(MODEL_DISPERSION_ELEVATED_REASON_CODE)
    if input_row.source_conflict_score >= SOURCE_CONFLICT_ELEVATED_MIN:
        reason_codes.append(SOURCE_CONFLICT_ELEVATED_REASON_CODE)
    if input_row.sample_size < VERY_SMALL_SAMPLE_MAX:
        reason_codes.append(SAMPLE_SIZE_VERY_SMALL_REASON_CODE)
    elif input_row.sample_size < SMALL_SAMPLE_MAX:
        reason_codes.append(SAMPLE_SIZE_SMALL_REASON_CODE)
    if input_row.calibration_error_bps >= CALIBRATION_ERROR_ELEVATED_BPS_MIN:
        reason_codes.append(CALIBRATION_ERROR_ELEVATED_REASON_CODE)
    if input_row.time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES_MAX:
        reason_codes.append(NEAR_RESOLUTION_WINDOW_REASON_CODE)
    if lower_was_clamped:
        reason_codes.append(LOWER_PROBABILITY_CLAMPED_REASON_CODE)
    if upper_was_clamped:
        reason_codes.append(UPPER_PROBABILITY_CLAMPED_REASON_CODE)
    return _reason_codes_by_priority(reason_codes)


def _confidence_tier(raw_interval_width: Decimal) -> str:
    if raw_interval_width <= HIGH_TIER_WIDTH_MAX:
        return "high"
    if raw_interval_width <= MEDIUM_TIER_WIDTH_MAX:
        return "medium"
    return "low"


def _validate_result(result: StrategyForecastConfidenceIntervalResult) -> None:
    if result.lower_probability > result.upper_probability:
        raise ValueError("lower_probability must be <= upper_probability")
    if result.interval_width != _ratio(result.upper_probability - result.lower_probability):
        raise ValueError("interval_width must match probability bounds")
    tier_reason = CONFIDENCE_TIER_REASON_CODES[CONFIDENCE_TIERS.index(result.confidence_tier)]
    if not result.reason_codes or result.reason_codes[0] != tier_reason:
        raise ValueError("reason_codes must match confidence_tier")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_codes is required")
    seen: set[str] = set()
    previous_position = -1
    for reason_code in rows:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in REASON_CODE_SET:
            raise ValueError("reason_codes must be known")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        position = REASON_CODE_PRIORITY.index(reason_code)
        if position < previous_position:
            raise ValueError("reason_codes must use priority sequence")
        previous_position = position
        seen.add(reason_code)
    return rows


def _reason_codes_by_priority(values: list[str]) -> tuple[str, ...]:
    present = set(values)
    return tuple(reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in present)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _ratio(decimal_value)


def _normalize_bps(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value > MAX_BPS:
        raise ValueError(f"{field_name} must be <= 10000")
    return _ratio(decimal_value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _ratio(decimal_value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value.quantize(COUNT_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_tier(field_name: str, value: object) -> None:
    if type(value) is not str or value not in CONFIDENCE_TIERS:
        raise ValueError(f"{field_name} must be high, medium, or low")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO_RATIO:
        return ZERO_RATIO
    if value > ONE_RATIO:
        return ONE_RATIO
    return _ratio(value)


def _ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")
