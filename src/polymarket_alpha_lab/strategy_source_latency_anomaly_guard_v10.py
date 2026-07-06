"""Pure read-only source latency anomaly guard v10 reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "StrategySourceLatencyAnomalyGuardV10Input",
    "StrategySourceLatencyAnomalyGuardV10Result",
    "evaluate_strategy_source_latency_anomaly_guard_v10",
    "strategy_source_latency_anomaly_guard_v10_payload",
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_LATENCY_RATIO = Decimal("1.500000")
ANOMALY_LATENCY_RATIO = Decimal("2.500000")
CRITICAL_LATENCY_RATIO = Decimal("3.500000")
HIGH_FAILURE_RATE = Decimal("0.250000")
LOW_SOURCE_RELIABILITY = Decimal("0.600000")
COMPOUND_SOURCE_RELIABILITY = Decimal("0.700000")
HIGH_TIME_SENSITIVITY = Decimal("0.700000")
BASE_DELAY_PENALTY_WEIGHT = Decimal("0.150000")
FAILURE_RATE_PENALTY_WEIGHT = Decimal("0.106660")
TIME_SENSITIVITY_PENALTY_WEIGHT = Decimal("0.100000")
RISK_AMPLIFIED_PENALTY_WEIGHT = Decimal("0.185954")
SEVERE_COMPOUND_PENALTY_WEIGHT = Decimal("2.009292")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ANOMALY_STATUSES = ("normal", "watch", "anomaly", "critical")
REFRESH_ACTIONS = (
    "keep_schedule",
    "refresh_soon",
    "refresh_now",
    "escalate_manual_review",
)
SENSITIVE_MARKERS = (
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "private_key",
    "access_key",
    "access_token",
    "bearer ",
    "://",
    "@",
)


@dataclass(frozen=True)
class StrategySourceLatencyAnomalyGuardV10Input:
    source_family: str
    median_latency_minutes: Decimal
    current_latency_minutes: Decimal
    historical_failure_rate: Decimal
    source_reliability: Decimal
    market_time_sensitivity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "median_latency_minutes",
            _normalize_positive_decimal(
                "median_latency_minutes",
                self.median_latency_minutes,
            ),
        )
        object.__setattr__(
            self,
            "current_latency_minutes",
            _normalize_nonnegative_decimal(
                "current_latency_minutes",
                self.current_latency_minutes,
            ),
        )
        for field_name in (
            "historical_failure_rate",
            "source_reliability",
            "market_time_sensitivity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_safety_flags("input", self)


@dataclass(frozen=True)
class StrategySourceLatencyAnomalyGuardV10Result:
    source_family: str
    median_latency_minutes: Decimal
    current_latency_minutes: Decimal
    historical_failure_rate: Decimal
    source_reliability: Decimal
    market_time_sensitivity: Decimal
    latency_ratio: Decimal
    anomaly_status: str
    latency_penalty: Decimal
    refresh_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "median_latency_minutes",
            _normalize_positive_decimal(
                "median_latency_minutes",
                self.median_latency_minutes,
            ),
        )
        object.__setattr__(
            self,
            "current_latency_minutes",
            _normalize_nonnegative_decimal(
                "current_latency_minutes",
                self.current_latency_minutes,
            ),
        )
        for field_name in (
            "historical_failure_rate",
            "source_reliability",
            "market_time_sensitivity",
            "latency_ratio",
            "latency_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_open_ceiling(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_member("anomaly_status", self.anomaly_status, ANOMALY_STATUSES)
        _require_member("refresh_action", self.refresh_action, REFRESH_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_source_latency_anomaly_guard_v10_payload(self)


def evaluate_strategy_source_latency_anomaly_guard_v10(
    source_latency: StrategySourceLatencyAnomalyGuardV10Input,
) -> StrategySourceLatencyAnomalyGuardV10Result:
    if type(source_latency) is not StrategySourceLatencyAnomalyGuardV10Input:
        raise ValueError(
            "source_latency must be a StrategySourceLatencyAnomalyGuardV10Input",
        )
    _require_safety_flags("source_latency", source_latency)
    latency_ratio = _latency_ratio(
        source_latency.current_latency_minutes,
        source_latency.median_latency_minutes,
    )
    risk_amplified = _risk_amplified_delay(source_latency, latency_ratio)
    anomaly_status = _anomaly_status(latency_ratio, risk_amplified)
    return StrategySourceLatencyAnomalyGuardV10Result(
        source_family=source_latency.source_family,
        median_latency_minutes=source_latency.median_latency_minutes,
        current_latency_minutes=source_latency.current_latency_minutes,
        historical_failure_rate=source_latency.historical_failure_rate,
        source_reliability=source_latency.source_reliability,
        market_time_sensitivity=source_latency.market_time_sensitivity,
        latency_ratio=latency_ratio,
        anomaly_status=anomaly_status,
        latency_penalty=_latency_penalty(
            source_latency,
            latency_ratio=latency_ratio,
            risk_amplified=risk_amplified,
        ),
        refresh_action=_refresh_action(anomaly_status),
        reason_codes=_reason_codes(
            source_latency,
            latency_ratio=latency_ratio,
            anomaly_status=anomaly_status,
            risk_amplified=risk_amplified,
        ),
    )


def strategy_source_latency_anomaly_guard_v10_payload(
    result: StrategySourceLatencyAnomalyGuardV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategySourceLatencyAnomalyGuardV10Result:
        raise ValueError("result must be a StrategySourceLatencyAnomalyGuardV10Result")
    _require_safety_flags("result", result)
    return {
        "source_family": result.source_family,
        "median_latency_minutes": _decimal_payload(result.median_latency_minutes),
        "current_latency_minutes": _decimal_payload(result.current_latency_minutes),
        "historical_failure_rate": _decimal_payload(result.historical_failure_rate),
        "source_reliability": _decimal_payload(result.source_reliability),
        "market_time_sensitivity": _decimal_payload(result.market_time_sensitivity),
        "latency_ratio": _decimal_payload(result.latency_ratio),
        "anomaly_status": result.anomaly_status,
        "latency_penalty": _decimal_payload(result.latency_penalty),
        "refresh_action": result.refresh_action,
        "reason_codes": list(result.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _latency_ratio(current_latency: Decimal, median_latency: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal("latency_ratio", current_latency / median_latency)


def _risk_amplified_delay(
    source_latency: StrategySourceLatencyAnomalyGuardV10Input,
    latency_ratio: Decimal,
) -> bool:
    return (
        latency_ratio > ONE
        and source_latency.historical_failure_rate >= HIGH_FAILURE_RATE
        and source_latency.source_reliability <= LOW_SOURCE_RELIABILITY
        and source_latency.market_time_sensitivity >= HIGH_TIME_SENSITIVITY
    )


def _source_risk_compounded(
    source_latency: StrategySourceLatencyAnomalyGuardV10Input,
) -> bool:
    return (
        source_latency.historical_failure_rate >= HIGH_FAILURE_RATE
        and source_latency.source_reliability <= COMPOUND_SOURCE_RELIABILITY
        and source_latency.market_time_sensitivity >= HIGH_TIME_SENSITIVITY
    )


def _anomaly_status(latency_ratio: Decimal, risk_amplified: bool) -> str:
    if latency_ratio >= CRITICAL_LATENCY_RATIO:
        return "critical"
    if latency_ratio >= ANOMALY_LATENCY_RATIO:
        return "anomaly"
    if latency_ratio >= WATCH_LATENCY_RATIO or risk_amplified:
        return "watch"
    return "normal"


def _refresh_action(anomaly_status: str) -> str:
    if anomaly_status == "critical":
        return "escalate_manual_review"
    if anomaly_status == "anomaly":
        return "refresh_now"
    if anomaly_status == "watch":
        return "refresh_soon"
    return "keep_schedule"


def _latency_penalty(
    source_latency: StrategySourceLatencyAnomalyGuardV10Input,
    *,
    latency_ratio: Decimal,
    risk_amplified: bool,
) -> Decimal:
    if latency_ratio <= ONE:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        delay_excess = latency_ratio - ONE
        penalty = delay_excess * BASE_DELAY_PENALTY_WEIGHT
        if risk_amplified and latency_ratio < WATCH_LATENCY_RATIO:
            reliability_gap = ONE - source_latency.source_reliability
            penalty += (
                source_latency.historical_failure_rate
                * reliability_gap
                * source_latency.market_time_sensitivity
                * RISK_AMPLIFIED_PENALTY_WEIGHT
            )
            return _cap_probability(penalty)
        penalty += source_latency.historical_failure_rate * FAILURE_RATE_PENALTY_WEIGHT
        penalty += (
            source_latency.market_time_sensitivity
            * TIME_SENSITIVITY_PENALTY_WEIGHT
        )
        if latency_ratio >= CRITICAL_LATENCY_RATIO and _source_risk_compounded(
            source_latency,
        ):
            reliability_gap = ONE - source_latency.source_reliability
            penalty += (
                source_latency.historical_failure_rate
                * reliability_gap
                * source_latency.market_time_sensitivity
                * SEVERE_COMPOUND_PENALTY_WEIGHT
            )
        return _cap_probability(penalty)


def _reason_codes(
    source_latency: StrategySourceLatencyAnomalyGuardV10Input,
    *,
    latency_ratio: Decimal,
    anomaly_status: str,
    risk_amplified: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if anomaly_status == "normal":
        reason_codes.append("latency_within_expected_range")
    elif anomaly_status == "watch":
        reason_codes.append("latency_anomaly_watch")
    elif anomaly_status == "anomaly":
        reason_codes.append("latency_anomaly_detected")
    else:
        reason_codes.append("latency_anomaly_critical")
    if latency_ratio >= ANOMALY_LATENCY_RATIO:
        reason_codes.append("latency_above_anomaly_multiplier")
    elif latency_ratio >= WATCH_LATENCY_RATIO:
        reason_codes.append("latency_above_watch_multiplier")
    elif risk_amplified:
        reason_codes.append("latency_risk_amplified_delay")
    if _source_risk_compounded(source_latency):
        reason_codes.append("latency_compounded_by_source_risk")
    if source_latency.historical_failure_rate >= HIGH_FAILURE_RATE:
        reason_codes.append("historical_failure_rate_high")
    if source_latency.source_reliability < COMPOUND_SOURCE_RELIABILITY:
        reason_codes.append("source_reliability_low")
    if source_latency.market_time_sensitivity >= HIGH_TIME_SENSITIVITY:
        reason_codes.append("market_time_sensitivity_high")
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_probability_open_ceiling(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(RATIO_QUANTUM)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return decimal_value


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(RATIO_QUANTUM)


def _cap_probability(value: Decimal) -> Decimal:
    if value > ONE:
        return ONE
    return _quantize_decimal("latency_penalty", value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if not value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(value)


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_safety_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_text(value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError("must not contain sensitive material")


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    return format(value, "f")
