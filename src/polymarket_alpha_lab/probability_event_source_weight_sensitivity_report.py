"""Paper-only source weight sensitivity report for probability events."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


__all__ = (
    "ProbabilityEventSourceWeightSensitivityConfig",
    "ProbabilityEventSourceWeightSensitivityReport",
    "build_probability_event_source_weight_sensitivity_report",
    "probability_event_source_weight_sensitivity_report_payload",
)


DEFAULT_CONFIG_VERSION = "probability-event-source-weight-sensitivity-v0"
ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
SOURCE_QUALITY_STATUSES = ("pass", "watch", "blocked", "block")
SENSITIVITY_STATUSES = ("pass", "watch", "block")


@dataclass(frozen=True)
class ProbabilityEventSourceWeightSensitivityConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    official_source_overweight_threshold: Decimal = Decimal("0.700000")
    official_source_underweight_threshold: Decimal = Decimal("0.200000")
    independent_source_underweight_threshold: Decimal = Decimal("0.200000")
    specialist_memory_overweight_threshold: Decimal = Decimal("0.550000")
    weight_spread_watch_threshold: Decimal = Decimal("0.400000")
    contradiction_penalty_watch_threshold: Decimal = Decimal("0.500000")
    contradiction_penalty_block_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventSourceWeightSensitivityConfig:
            raise TypeError(
                "ProbabilityEventSourceWeightSensitivityConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventSourceWeightSensitivityConfig:
            raise ValueError(
                "config must be exactly ProbabilityEventSourceWeightSensitivityConfig",
            )
        _require_config_version(self.config_version)
        for field_name in (
            "official_source_overweight_threshold",
            "official_source_underweight_threshold",
            "independent_source_underweight_threshold",
            "specialist_memory_overweight_threshold",
            "weight_spread_watch_threshold",
            "contradiction_penalty_watch_threshold",
            "contradiction_penalty_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.official_source_underweight_threshold
            >= self.official_source_overweight_threshold
        ):
            raise ValueError(
                "official_source_overweight_threshold must exceed "
                "official_source_underweight_threshold",
            )
        if (
            self.contradiction_penalty_block_threshold
            <= self.contradiction_penalty_watch_threshold
        ):
            raise ValueError(
                "contradiction_penalty_block_threshold must exceed "
                "contradiction_penalty_watch_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ProbabilityEventSourceWeightSensitivityReport:
    generated_at: datetime
    config_version: str
    official_source_weight: Decimal
    independent_source_weight: Decimal
    specialist_memory_weight: Decimal
    contradiction_penalty: Decimal
    source_quality_status: str
    total_source_weight: Decimal
    max_source_weight: Decimal
    min_source_weight: Decimal
    weight_spread: Decimal
    sensitivity_status: str
    weight_imbalance_reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventSourceWeightSensitivityReport:
            raise TypeError(
                "ProbabilityEventSourceWeightSensitivityReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventSourceWeightSensitivityReport:
            raise ValueError(
                "report must be exactly ProbabilityEventSourceWeightSensitivityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "official_source_weight",
            "independent_source_weight",
            "specialist_memory_weight",
            "contradiction_penalty",
            "total_source_weight",
            "max_source_weight",
            "min_source_weight",
            "weight_spread",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_quality_status",
            _normalize_source_quality_status(self.source_quality_status),
        )
        _require_enum("sensitivity_status", self.sensitivity_status, SENSITIVITY_STATUSES)
        object.__setattr__(
            self,
            "weight_imbalance_reason_codes",
            _normalize_reason_codes(
                "weight_imbalance_reason_codes",
                self.weight_imbalance_reason_codes,
            ),
        )
        _require_manual_next_step(self.manual_next_step)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)

    @property
    def status(self) -> str:
        return self.sensitivity_status

    @property
    def payload(self) -> dict[str, Any]:
        return probability_event_source_weight_sensitivity_report_payload(self)


def build_probability_event_source_weight_sensitivity_report(
    *,
    official_source_weight: Decimal,
    independent_source_weight: Decimal,
    specialist_memory_weight: Decimal,
    contradiction_penalty: Decimal,
    source_quality_status: str,
    config: ProbabilityEventSourceWeightSensitivityConfig,
    generated_at: datetime,
) -> ProbabilityEventSourceWeightSensitivityReport:
    if type(config) is not ProbabilityEventSourceWeightSensitivityConfig:
        raise ValueError("config must be a ProbabilityEventSourceWeightSensitivityConfig")
    _require_hard_flags("config", config)
    official_weight = _require_ratio_decimal(
        "official_source_weight",
        official_source_weight,
    )
    independent_weight = _require_ratio_decimal(
        "independent_source_weight",
        independent_source_weight,
    )
    memory_weight = _require_ratio_decimal(
        "specialist_memory_weight",
        specialist_memory_weight,
    )
    penalty = _require_ratio_decimal("contradiction_penalty", contradiction_penalty)
    normalized_quality_status = _normalize_source_quality_status(source_quality_status)
    total_weight = _quantize(official_weight + independent_weight + memory_weight)
    if total_weight != ONE.quantize(QUANTUM):
        raise ValueError("total_source_weight must equal 1.000000")
    max_weight = max(official_weight, independent_weight, memory_weight)
    min_weight = min(official_weight, independent_weight, memory_weight)
    spread = _quantize(max_weight - min_weight)
    reason_codes = _reason_codes(
        official_source_weight=official_weight,
        independent_source_weight=independent_weight,
        specialist_memory_weight=memory_weight,
        contradiction_penalty=penalty,
        source_quality_status=normalized_quality_status,
        weight_spread=spread,
        config=config,
    )
    sensitivity_status = _sensitivity_status(reason_codes)
    return ProbabilityEventSourceWeightSensitivityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        official_source_weight=official_weight,
        independent_source_weight=independent_weight,
        specialist_memory_weight=memory_weight,
        contradiction_penalty=penalty,
        source_quality_status=normalized_quality_status,
        total_source_weight=total_weight,
        max_source_weight=max_weight,
        min_source_weight=min_weight,
        weight_spread=spread,
        sensitivity_status=sensitivity_status,
        weight_imbalance_reason_codes=reason_codes,
        manual_next_step=_manual_next_step(sensitivity_status, reason_codes),
    )


def probability_event_source_weight_sensitivity_report_payload(
    report: ProbabilityEventSourceWeightSensitivityReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventSourceWeightSensitivityReport:
        raise ValueError(
            "report must be a ProbabilityEventSourceWeightSensitivityReport",
        )
    _require_hard_flags("report", report)
    return {field.name: _payload_value(getattr(report, field.name)) for field in fields(report)}


def _reason_codes(
    *,
    official_source_weight: Decimal,
    independent_source_weight: Decimal,
    specialist_memory_weight: Decimal,
    contradiction_penalty: Decimal,
    source_quality_status: str,
    weight_spread: Decimal,
    config: ProbabilityEventSourceWeightSensitivityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if official_source_weight > config.official_source_overweight_threshold:
        reason_codes.append("official_source_overweight")
    if official_source_weight < config.official_source_underweight_threshold:
        reason_codes.append("official_source_underweight")
    if independent_source_weight < config.independent_source_underweight_threshold:
        reason_codes.append("independent_source_underweight")
    if specialist_memory_weight > config.specialist_memory_overweight_threshold:
        reason_codes.append("specialist_memory_overweight")
    if (
        "official_source_overweight" not in reason_codes
        and weight_spread > config.weight_spread_watch_threshold
    ):
        reason_codes.append("weight_spread_high")
    if contradiction_penalty >= config.contradiction_penalty_block_threshold:
        reason_codes.append("contradiction_penalty_high")
    elif contradiction_penalty >= config.contradiction_penalty_watch_threshold:
        reason_codes.append("contradiction_penalty_watch")
    if source_quality_status == "blocked":
        reason_codes.append("source_quality_blocked")
    elif source_quality_status == "watch":
        reason_codes.append("source_quality_watch")
    return tuple(reason_codes)


def _sensitivity_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "contradiction_penalty_high" in reason_codes
        or "source_quality_blocked" in reason_codes
    ):
        return "block"
    if reason_codes:
        return "watch"
    return "pass"


def _manual_next_step(sensitivity_status: str, reason_codes: tuple[str, ...]) -> str:
    if sensitivity_status == "block":
        return "pause_paper_event_and_escalate_source_review"
    if (
        "official_source_overweight" in reason_codes
        or "independent_source_underweight" in reason_codes
    ):
        return "manually_review_official_source_dependency"
    if "specialist_memory_overweight" in reason_codes:
        return "manually_review_specialist_memory_dependency"
    if "contradiction_penalty_watch" in reason_codes:
        return "manually_review_contradiction_penalty_assumption"
    if "source_quality_watch" in reason_codes:
        return "manually_recheck_source_quality_inputs"
    if reason_codes:
        return "manually_review_source_weight_imbalance"
    return "continue_paper_review_without_weight_change"


def _validate_report_consistency(
    report: ProbabilityEventSourceWeightSensitivityReport,
) -> None:
    total_weight = _quantize(
        report.official_source_weight
        + report.independent_source_weight
        + report.specialist_memory_weight,
    )
    if report.total_source_weight != total_weight:
        raise ValueError("total_source_weight must match source weights")
    if report.total_source_weight != ONE.quantize(QUANTUM):
        raise ValueError("total_source_weight must equal 1.000000")
    max_weight = max(
        report.official_source_weight,
        report.independent_source_weight,
        report.specialist_memory_weight,
    )
    min_weight = min(
        report.official_source_weight,
        report.independent_source_weight,
        report.specialist_memory_weight,
    )
    if report.max_source_weight != max_weight:
        raise ValueError("max_source_weight must match source weights")
    if report.min_source_weight != min_weight:
        raise ValueError("min_source_weight must match source weights")
    if report.weight_spread != _quantize(max_weight - min_weight):
        raise ValueError("weight_spread must match source weights")
    config = ProbabilityEventSourceWeightSensitivityConfig(
        config_version=report.config_version,
    )
    expected_reason_codes = _reason_codes(
        official_source_weight=report.official_source_weight,
        independent_source_weight=report.independent_source_weight,
        specialist_memory_weight=report.specialist_memory_weight,
        contradiction_penalty=report.contradiction_penalty,
        source_quality_status=report.source_quality_status,
        weight_spread=report.weight_spread,
        config=config,
    )
    if report.weight_imbalance_reason_codes != expected_reason_codes:
        raise ValueError("weight_imbalance_reason_codes must match source weights")
    expected_status = _sensitivity_status(expected_reason_codes)
    if report.sensitivity_status != expected_status:
        raise ValueError("sensitivity_status must match source weights")
    if report.manual_next_step != _manual_next_step(expected_status, expected_reason_codes):
        raise ValueError("manual_next_step must match source weights")


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value: {value!r}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_config_version(value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError("config_version must be a non-empty string")
    if value != DEFAULT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _normalize_source_quality_status(value: object) -> str:
    _require_enum("source_quality_status", value, SOURCE_QUALITY_STATUSES)
    if value == "block":
        return "blocked"
    return value


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or not reason_code:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if reason_code != reason_code.lower() or " " in reason_code:
            raise ValueError(f"{field_name} must contain canonical reason codes")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _require_manual_next_step(value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError("manual_next_step must be a non-empty string")
    if value != value.lower() or " " in value:
        raise ValueError("manual_next_step must be canonical")


def _require_hard_flags(context: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{context} {flag_name} must be True")
