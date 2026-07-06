"""Paper-only readonly probability edge recheck trigger."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")

IMMINENT_RESOLUTION_MINUTES = Decimal("30.000000")
NEAR_RESOLUTION_MINUTES = Decimal("120.000000")
SOON_RESOLUTION_MINUTES = Decimal("240.000000")
MODERATE_MARKET_MOVE_BPS = Decimal("30.000000")
LARGE_MARKET_MOVE_BPS = Decimal("60.000000")

SOURCE_FRESHNESS_STATUSES = (
    "fresh",
    "stale",
    "expired",
)
FORECAST_CONFIDENCE_TIERS = (
    "high",
    "medium",
    "low",
)
RECHECK_STATUSES = (
    "recheck_now",
    "recheck_scheduled",
    "no_recheck",
)
RECHECK_PRIORITIES = (
    "critical",
    "high",
    "medium",
    "low",
)
REASON_CODES = (
    "source_freshness_fresh",
    "source_freshness_stale",
    "source_freshness_expired",
    "forecast_confidence_high",
    "forecast_confidence_medium",
    "forecast_confidence_low",
    "resolution_window_imminent",
    "resolution_window_near",
    "resolution_window_soon",
    "resolution_window_open",
    "market_move_large",
    "market_move_moderate",
    "market_move_immaterial",
    "cost_change_present",
    "cost_change_immaterial",
    "edge_buffer_at_risk",
    "edge_buffer_stable",
)


@dataclass(frozen=True)
class ProbabilityEdgeRecheckTriggerV10Input:
    market_id: str
    last_edge_bps: Decimal
    current_market_move_bps: Decimal
    source_freshness_status: str
    forecast_confidence_tier: str
    time_to_resolution_minutes: Decimal
    cost_change_bps: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in (
            "last_edge_bps",
            "current_market_move_bps",
            "cost_change_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        _require_member(
            "source_freshness_status",
            self.source_freshness_status,
            SOURCE_FRESHNESS_STATUSES,
        )
        _require_member(
            "forecast_confidence_tier",
            self.forecast_confidence_tier,
            FORECAST_CONFIDENCE_TIERS,
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ProbabilityEdgeRecheckTriggerV10Result:
    market_id: str
    last_edge_bps: Decimal
    current_market_move_bps: Decimal
    source_freshness_status: str
    forecast_confidence_tier: str
    time_to_resolution_minutes: Decimal
    cost_change_bps: Decimal
    absolute_last_edge_bps: Decimal
    absolute_market_move_bps: Decimal
    absolute_cost_change_bps: Decimal
    recheck_status: str
    recheck_priority: str
    next_recheck_minutes: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in (
            "last_edge_bps",
            "current_market_move_bps",
            "cost_change_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "time_to_resolution_minutes",
            "absolute_last_edge_bps",
            "absolute_market_move_bps",
            "absolute_cost_change_bps",
            "next_recheck_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "source_freshness_status",
            self.source_freshness_status,
            SOURCE_FRESHNESS_STATUSES,
        )
        _require_member(
            "forecast_confidence_tier",
            self.forecast_confidence_tier,
            FORECAST_CONFIDENCE_TIERS,
        )
        _require_member("recheck_status", self.recheck_status, RECHECK_STATUSES)
        _require_member("recheck_priority", self.recheck_priority, RECHECK_PRIORITIES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("result", self)
        _validate_result(self)

    @property
    def payload(self) -> dict[str, Any]:
        return probability_edge_recheck_trigger_v10_payload(self)


def strategy_probability_edge_recheck_trigger_v10(
    trigger_input: ProbabilityEdgeRecheckTriggerV10Input,
) -> ProbabilityEdgeRecheckTriggerV10Result:
    if type(trigger_input) is not ProbabilityEdgeRecheckTriggerV10Input:
        raise ValueError(
            "trigger_input must be a ProbabilityEdgeRecheckTriggerV10Input",
        )
    _require_hard_flags("input", trigger_input)

    metrics = _derive_recheck_metrics(trigger_input)
    return ProbabilityEdgeRecheckTriggerV10Result(
        market_id=trigger_input.market_id,
        last_edge_bps=trigger_input.last_edge_bps,
        current_market_move_bps=trigger_input.current_market_move_bps,
        source_freshness_status=trigger_input.source_freshness_status,
        forecast_confidence_tier=trigger_input.forecast_confidence_tier,
        time_to_resolution_minutes=trigger_input.time_to_resolution_minutes,
        cost_change_bps=trigger_input.cost_change_bps,
        absolute_last_edge_bps=metrics["absolute_last_edge_bps"],
        absolute_market_move_bps=metrics["absolute_market_move_bps"],
        absolute_cost_change_bps=metrics["absolute_cost_change_bps"],
        recheck_status=metrics["recheck_status"],
        recheck_priority=metrics["recheck_priority"],
        next_recheck_minutes=metrics["next_recheck_minutes"],
        reason_codes=metrics["reason_codes"],
    )


def probability_edge_recheck_trigger_v10_payload(
    report: ProbabilityEdgeRecheckTriggerV10Result,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEdgeRecheckTriggerV10Result:
        raise ValueError("report must be a ProbabilityEdgeRecheckTriggerV10Result")
    _require_hard_flags("result", report)
    return {
        "market_id": report.market_id,
        "last_edge_bps": str(report.last_edge_bps),
        "current_market_move_bps": str(report.current_market_move_bps),
        "source_freshness_status": report.source_freshness_status,
        "forecast_confidence_tier": report.forecast_confidence_tier,
        "time_to_resolution_minutes": str(report.time_to_resolution_minutes),
        "cost_change_bps": str(report.cost_change_bps),
        "absolute_last_edge_bps": str(report.absolute_last_edge_bps),
        "absolute_market_move_bps": str(report.absolute_market_move_bps),
        "absolute_cost_change_bps": str(report.absolute_cost_change_bps),
        "recheck_status": report.recheck_status,
        "recheck_priority": report.recheck_priority,
        "next_recheck_minutes": str(report.next_recheck_minutes),
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _derive_recheck_metrics(
    trigger_input: ProbabilityEdgeRecheckTriggerV10Input,
) -> dict[str, Any]:
    absolute_last_edge_bps = _absolute_decimal(
        "absolute_last_edge_bps",
        trigger_input.last_edge_bps,
    )
    absolute_market_move_bps = _absolute_decimal(
        "absolute_market_move_bps",
        trigger_input.current_market_move_bps,
    )
    absolute_cost_change_bps = _absolute_decimal(
        "absolute_cost_change_bps",
        trigger_input.cost_change_bps,
    )
    reason_codes = _reason_codes(
        trigger_input,
        absolute_last_edge_bps,
        absolute_market_move_bps,
        absolute_cost_change_bps,
    )
    recheck_priority = _recheck_priority(reason_codes)
    return {
        "absolute_last_edge_bps": absolute_last_edge_bps,
        "absolute_market_move_bps": absolute_market_move_bps,
        "absolute_cost_change_bps": absolute_cost_change_bps,
        "recheck_status": _recheck_status(recheck_priority),
        "recheck_priority": recheck_priority,
        "next_recheck_minutes": _next_recheck_minutes(recheck_priority),
        "reason_codes": reason_codes,
    }


def _reason_codes(
    trigger_input: ProbabilityEdgeRecheckTriggerV10Input,
    absolute_last_edge_bps: Decimal,
    absolute_market_move_bps: Decimal,
    absolute_cost_change_bps: Decimal,
) -> tuple[str, ...]:
    return (
        f"source_freshness_{trigger_input.source_freshness_status}",
        f"forecast_confidence_{trigger_input.forecast_confidence_tier}",
        _resolution_window_code(trigger_input.time_to_resolution_minutes),
        _market_move_code(absolute_market_move_bps),
        _cost_change_code(absolute_cost_change_bps),
        _edge_buffer_code(
            absolute_last_edge_bps,
            absolute_market_move_bps,
            absolute_cost_change_bps,
        ),
    )


def _resolution_window_code(time_to_resolution_minutes: Decimal) -> str:
    if time_to_resolution_minutes <= IMMINENT_RESOLUTION_MINUTES:
        return "resolution_window_imminent"
    if time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
        return "resolution_window_near"
    if time_to_resolution_minutes <= SOON_RESOLUTION_MINUTES:
        return "resolution_window_soon"
    return "resolution_window_open"


def _market_move_code(absolute_market_move_bps: Decimal) -> str:
    if absolute_market_move_bps >= LARGE_MARKET_MOVE_BPS:
        return "market_move_large"
    if absolute_market_move_bps >= MODERATE_MARKET_MOVE_BPS:
        return "market_move_moderate"
    return "market_move_immaterial"


def _cost_change_code(absolute_cost_change_bps: Decimal) -> str:
    if absolute_cost_change_bps > ZERO:
        return "cost_change_present"
    return "cost_change_immaterial"


def _edge_buffer_code(
    absolute_last_edge_bps: Decimal,
    absolute_market_move_bps: Decimal,
    absolute_cost_change_bps: Decimal,
) -> str:
    if absolute_last_edge_bps <= absolute_market_move_bps + absolute_cost_change_bps:
        return "edge_buffer_at_risk"
    return "edge_buffer_stable"


def _recheck_priority(reason_codes: tuple[str, ...]) -> str:
    score = ZERO
    if "source_freshness_expired" in reason_codes:
        score += Decimal("4.000000")
    if "source_freshness_stale" in reason_codes:
        score += Decimal("3.000000")
    if "forecast_confidence_low" in reason_codes:
        score += Decimal("2.000000")
    if "forecast_confidence_medium" in reason_codes:
        score += Decimal("1.000000")
    if "resolution_window_imminent" in reason_codes:
        score += Decimal("3.000000")
    if "resolution_window_near" in reason_codes:
        score += Decimal("2.000000")
    if "resolution_window_soon" in reason_codes:
        score += Decimal("1.000000")
    if "market_move_large" in reason_codes:
        score += Decimal("3.000000")
    if "market_move_moderate" in reason_codes:
        score += Decimal("2.000000")
    if "cost_change_present" in reason_codes:
        score += Decimal("1.000000")
    if "edge_buffer_at_risk" in reason_codes:
        score += Decimal("3.000000")

    if score >= Decimal("9.000000"):
        return "critical"
    if score >= Decimal("5.000000"):
        return "high"
    if score >= Decimal("2.000000"):
        return "medium"
    return "low"


def _recheck_status(recheck_priority: str) -> str:
    if recheck_priority in ("critical", "high"):
        return "recheck_now"
    if recheck_priority == "medium":
        return "recheck_scheduled"
    return "no_recheck"


def _next_recheck_minutes(recheck_priority: str) -> Decimal:
    if recheck_priority == "critical":
        return Decimal("0.000000")
    if recheck_priority == "high":
        return Decimal("5.000000")
    if recheck_priority == "medium":
        return Decimal("15.000000")
    return Decimal("240.000000")


def _validate_result(result: ProbabilityEdgeRecheckTriggerV10Result) -> None:
    trigger_input = ProbabilityEdgeRecheckTriggerV10Input(
        market_id=result.market_id,
        last_edge_bps=result.last_edge_bps,
        current_market_move_bps=result.current_market_move_bps,
        source_freshness_status=result.source_freshness_status,
        forecast_confidence_tier=result.forecast_confidence_tier,
        time_to_resolution_minutes=result.time_to_resolution_minutes,
        cost_change_bps=result.cost_change_bps,
    )
    metrics = _derive_recheck_metrics(trigger_input)
    for field_name in (
        "absolute_last_edge_bps",
        "absolute_market_move_bps",
        "absolute_cost_change_bps",
        "recheck_status",
        "recheck_priority",
        "next_recheck_minutes",
    ):
        if getattr(result, field_name) != metrics[field_name]:
            raise ValueError(f"{field_name} must match trigger inputs")
    if result.reason_codes != metrics["reason_codes"]:
        raise ValueError("reason_codes must match trigger inputs")


def _absolute_decimal(field_name: str, value: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal(field_name, abs(value))


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_reason_codes(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_member(field_name, reason_code, REASON_CODES)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    return value


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_member(field_name: str, value: Any, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_hard_flags(field_name: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "ProbabilityEdgeRecheckTriggerV10Input",
    "ProbabilityEdgeRecheckTriggerV10Result",
    "probability_edge_recheck_trigger_v10_payload",
    "strategy_probability_edge_recheck_trigger_v10",
)
