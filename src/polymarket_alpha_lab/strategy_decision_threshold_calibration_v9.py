"""Pure read-only decision threshold calibration v9 report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_DECISION_THRESHOLD_CALIBRATION_V9_CONFIG_VERSION = (
    "strategy-decision-threshold-calibration-v9"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

THRESHOLD_STATUSES = ("standard", "elevated", "blocked")
STABLE_REASON = "threshold_calibration_v9_stable"
PAPER_CALIBRATION_WEAK_REASON = "paper_calibration_weak"
SOURCE_QUALITY_LOW_REASON = "source_quality_low"
COST_DRAG_HIGH_REASON = "cost_drag_high"
RESOLUTION_RISK_HIGH_REASON = "resolution_risk_high"
TEAM_CONFIDENCE_LOW_REASON = "team_confidence_low"
ELEVATED_REASON = "recommended_threshold_elevated"
BLOCKED_REASON = "recommended_threshold_blocked"

REASON_PRIORITY = (
    PAPER_CALIBRATION_WEAK_REASON,
    SOURCE_QUALITY_LOW_REASON,
    COST_DRAG_HIGH_REASON,
    RESOLUTION_RISK_HIGH_REASON,
    TEAM_CONFIDENCE_LOW_REASON,
    BLOCKED_REASON,
    ELEVATED_REASON,
    STABLE_REASON,
)


@dataclass(frozen=True)
class StrategyDecisionThresholdCalibrationV9Config:
    config_version: str = DEFAULT_STRATEGY_DECISION_THRESHOLD_CALIBRATION_V9_CONFIG_VERSION
    base_recommended_threshold: Decimal = Decimal("0.040000")
    minimum_recommended_threshold: Decimal = Decimal("0.020000")
    maximum_recommended_threshold: Decimal = Decimal("0.200000")
    elevated_threshold: Decimal = Decimal("0.100000")
    blocked_threshold: Decimal = Decimal("0.160000")
    calibration_gap_weight: Decimal = Decimal("0.060000")
    source_quality_gap_weight: Decimal = Decimal("0.050000")
    cost_drag_weight: Decimal = Decimal("0.250000")
    resolution_risk_weight: Decimal = Decimal("0.060000")
    team_confidence_gap_weight: Decimal = Decimal("0.040000")
    weak_paper_calibration: Decimal = Decimal("0.650000")
    low_source_quality: Decimal = Decimal("0.550000")
    high_cost_drag: Decimal = Decimal("0.100000")
    high_resolution_risk: Decimal = Decimal("0.650000")
    low_team_confidence: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_STRATEGY_DECISION_THRESHOLD_CALIBRATION_V9_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "base_recommended_threshold",
            "minimum_recommended_threshold",
            "maximum_recommended_threshold",
            "elevated_threshold",
            "blocked_threshold",
            "calibration_gap_weight",
            "source_quality_gap_weight",
            "cost_drag_weight",
            "resolution_risk_weight",
            "team_confidence_gap_weight",
            "weak_paper_calibration",
            "low_source_quality",
            "high_cost_drag",
            "high_resolution_risk",
            "low_team_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_threshold_order(self)
        reject_unsafe_surface_fields("strategy decision threshold calibration v9 config", self)
        require_paper_only_flags("strategy decision threshold calibration v9 config", self)


@dataclass(frozen=True)
class StrategyDecisionThresholdCalibrationV9Input:
    historical_paper_calibration: Decimal
    source_quality: Decimal
    cost_drag: Decimal
    resolution_risk: Decimal
    team_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "historical_paper_calibration",
            "source_quality",
            "cost_drag",
            "resolution_risk",
            "team_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        reject_unsafe_surface_fields("strategy decision threshold calibration v9 input", self)
        require_paper_only_flags("strategy decision threshold calibration v9 input", self)


@dataclass(frozen=True)
class StrategyDecisionThresholdCalibrationV9Report:
    generated_at: datetime
    config_version: str
    historical_paper_calibration: Decimal
    source_quality: Decimal
    cost_drag: Decimal
    resolution_risk: Decimal
    team_confidence: Decimal
    recommended_threshold: Decimal
    threshold_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "historical_paper_calibration",
            "source_quality",
            "cost_drag",
            "resolution_risk",
            "team_confidence",
            "recommended_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("threshold_status", self.threshold_status, THRESHOLD_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("strategy decision threshold calibration v9 report", self)
        require_paper_only_flags("strategy decision threshold calibration v9 report", self)


def build_strategy_decision_threshold_calibration_v9_report(
    input_value: StrategyDecisionThresholdCalibrationV9Input,
    *,
    config: StrategyDecisionThresholdCalibrationV9Config,
    generated_at: datetime,
) -> StrategyDecisionThresholdCalibrationV9Report:
    if type(input_value) is not StrategyDecisionThresholdCalibrationV9Input:
        raise ValueError("input_value must be a StrategyDecisionThresholdCalibrationV9Input")
    if type(config) is not StrategyDecisionThresholdCalibrationV9Config:
        raise ValueError("config must be a StrategyDecisionThresholdCalibrationV9Config")
    require_paper_only_flags("strategy decision threshold calibration v9 input", input_value)
    require_paper_only_flags("strategy decision threshold calibration v9 config", config)

    recommended_threshold = _recommended_threshold(input_value, config)
    threshold_status = _threshold_status(recommended_threshold, config)
    reason_codes = _reason_codes(input_value, config, threshold_status)
    return StrategyDecisionThresholdCalibrationV9Report(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        historical_paper_calibration=input_value.historical_paper_calibration,
        source_quality=input_value.source_quality,
        cost_drag=input_value.cost_drag,
        resolution_risk=input_value.resolution_risk,
        team_confidence=input_value.team_confidence,
        recommended_threshold=recommended_threshold,
        threshold_status=threshold_status,
        reason_codes=reason_codes,
    )


def strategy_decision_threshold_calibration_v9_payload(
    report: StrategyDecisionThresholdCalibrationV9Report,
) -> dict[str, Any]:
    if type(report) is not StrategyDecisionThresholdCalibrationV9Report:
        raise ValueError("report must be a StrategyDecisionThresholdCalibrationV9Report")
    require_paper_only_flags("strategy decision threshold calibration v9 report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    require_paper_only_flags(
        "strategy decision threshold calibration v9 payload",
        _PayloadFlags(payload),
    )
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _recommended_threshold(
    input_value: StrategyDecisionThresholdCalibrationV9Input,
    config: StrategyDecisionThresholdCalibrationV9Config,
) -> Decimal:
    threshold = config.base_recommended_threshold
    threshold += _gap(input_value.historical_paper_calibration) * config.calibration_gap_weight
    threshold += _gap(input_value.source_quality) * config.source_quality_gap_weight
    threshold += input_value.cost_drag * config.cost_drag_weight
    threshold += input_value.resolution_risk * config.resolution_risk_weight
    threshold += _gap(input_value.team_confidence) * config.team_confidence_gap_weight
    return _clamp(
        _quantize(threshold),
        config.minimum_recommended_threshold,
        config.maximum_recommended_threshold,
    )


def _gap(value: Decimal) -> Decimal:
    return _quantize(ONE - value)


def _clamp(value: Decimal, minimum_value: Decimal, maximum_value: Decimal) -> Decimal:
    if value < minimum_value:
        return minimum_value
    if value > maximum_value:
        return maximum_value
    return _quantize(value)


def _threshold_status(
    recommended_threshold: Decimal,
    config: StrategyDecisionThresholdCalibrationV9Config,
) -> str:
    if recommended_threshold >= config.blocked_threshold:
        return "blocked"
    if recommended_threshold >= config.elevated_threshold:
        return "elevated"
    return "standard"


def _reason_codes(
    input_value: StrategyDecisionThresholdCalibrationV9Input,
    config: StrategyDecisionThresholdCalibrationV9Config,
    threshold_status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if input_value.historical_paper_calibration <= config.weak_paper_calibration:
        codes.append(PAPER_CALIBRATION_WEAK_REASON)
    if input_value.source_quality <= config.low_source_quality:
        codes.append(SOURCE_QUALITY_LOW_REASON)
    if input_value.cost_drag >= config.high_cost_drag:
        codes.append(COST_DRAG_HIGH_REASON)
    if input_value.resolution_risk >= config.high_resolution_risk:
        codes.append(RESOLUTION_RISK_HIGH_REASON)
    if input_value.team_confidence <= config.low_team_confidence:
        codes.append(TEAM_CONFIDENCE_LOW_REASON)
    if threshold_status == "blocked":
        codes.append(BLOCKED_REASON)
    elif threshold_status == "elevated":
        codes.append(ELEVATED_REASON)
    elif not codes:
        codes.append(STABLE_REASON)
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _validate_report(report: StrategyDecisionThresholdCalibrationV9Report) -> None:
    config = StrategyDecisionThresholdCalibrationV9Config(config_version=report.config_version)
    input_value = StrategyDecisionThresholdCalibrationV9Input(
        historical_paper_calibration=report.historical_paper_calibration,
        source_quality=report.source_quality,
        cost_drag=report.cost_drag,
        resolution_risk=report.resolution_risk,
        team_confidence=report.team_confidence,
    )
    if report.recommended_threshold != _recommended_threshold(input_value, config):
        raise ValueError("recommended_threshold must match threshold inputs")
    if report.threshold_status != _threshold_status(report.recommended_threshold, config):
        raise ValueError("threshold_status must match recommended_threshold")
    if report.reason_codes != _reason_codes(input_value, config, report.threshold_status):
        raise ValueError("reason_codes must match threshold inputs and status")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
        if reason_code not in REASON_PRIORITY:
            raise ValueError(f"{field_name} must contain known reason codes")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in REASON_PRIORITY if reason_code in seen)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part.lower() != part:
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_threshold_order(config: StrategyDecisionThresholdCalibrationV9Config) -> None:
    if config.minimum_recommended_threshold > config.base_recommended_threshold:
        raise ValueError("minimum_recommended_threshold must not exceed base threshold")
    if config.base_recommended_threshold > config.maximum_recommended_threshold:
        raise ValueError("maximum_recommended_threshold must be at least base threshold")
    if config.elevated_threshold > config.blocked_threshold:
        raise ValueError("elevated_threshold must not exceed blocked threshold")
    if config.blocked_threshold > config.maximum_recommended_threshold:
        raise ValueError("blocked_threshold must not exceed maximum threshold")


__all__ = (
    "DEFAULT_STRATEGY_DECISION_THRESHOLD_CALIBRATION_V9_CONFIG_VERSION",
    "StrategyDecisionThresholdCalibrationV9Config",
    "StrategyDecisionThresholdCalibrationV9Input",
    "StrategyDecisionThresholdCalibrationV9Report",
    "build_strategy_decision_threshold_calibration_v9_report",
    "strategy_decision_threshold_calibration_v9_payload",
)
