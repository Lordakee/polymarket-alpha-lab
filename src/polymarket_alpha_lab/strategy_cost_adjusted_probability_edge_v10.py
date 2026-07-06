"""Paper-only readonly cost-adjusted probability edge reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
BPS_MULTIPLIER = Decimal("10000.000000")

EDGE_STATUSES = (
    "positive_edge",
    "cost_dragged_edge",
    "negative_edge",
)
REASON_CODES = (
    "raw_edge_positive",
    "raw_edge_nonpositive",
    "cost_adjusted_edge_positive",
    "cost_adjusted_edge_nonpositive",
    "cost_drag_exceeds_raw_edge",
    "fee_cost_present",
    "slippage_cost_present",
    "settlement_cost_present",
    "resolution_risk_premium_present",
    "confidence_penalty_present",
)


@dataclass(frozen=True)
class CostAdjustedProbabilityEdgeV10Input:
    market_price_probability: Decimal
    forecast_probability: Decimal
    fee_cost_bps: Decimal
    slippage_cost_bps: Decimal
    settlement_cost_bps: Decimal
    resolution_risk_premium_bps: Decimal
    confidence_penalty_bps: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "market_price_probability",
            _normalize_probability(
                "market_price_probability",
                self.market_price_probability,
            ),
        )
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        for field_name in (
            "fee_cost_bps",
            "slippage_cost_bps",
            "settlement_cost_bps",
            "resolution_risk_premium_bps",
            "confidence_penalty_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class CostAdjustedProbabilityEdgeV10Result:
    market_price_probability: Decimal
    forecast_probability: Decimal
    fee_cost_bps: Decimal
    slippage_cost_bps: Decimal
    settlement_cost_bps: Decimal
    resolution_risk_premium_bps: Decimal
    confidence_penalty_bps: Decimal
    raw_edge_bps: Decimal
    cost_adjusted_edge_bps: Decimal
    edge_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "market_price_probability",
            _normalize_probability(
                "market_price_probability",
                self.market_price_probability,
            ),
        )
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        for field_name in (
            "fee_cost_bps",
            "slippage_cost_bps",
            "settlement_cost_bps",
            "resolution_risk_premium_bps",
            "confidence_penalty_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "raw_edge_bps",
            _normalize_decimal("raw_edge_bps", self.raw_edge_bps),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge_bps",
            _normalize_decimal(
                "cost_adjusted_edge_bps",
                self.cost_adjusted_edge_bps,
            ),
        )
        _require_member("edge_status", self.edge_status, EDGE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("result", self)
        _validate_result(self)

    @property
    def payload(self) -> dict[str, Any]:
        return cost_adjusted_probability_edge_v10_payload(self)


def strategy_cost_adjusted_probability_edge_v10(
    edge_input: CostAdjustedProbabilityEdgeV10Input,
) -> CostAdjustedProbabilityEdgeV10Result:
    if type(edge_input) is not CostAdjustedProbabilityEdgeV10Input:
        raise ValueError("edge_input must be a CostAdjustedProbabilityEdgeV10Input")
    _require_hard_flags("input", edge_input)

    raw_edge_bps = _raw_edge_bps(edge_input)
    cost_adjusted_edge_bps = _cost_adjusted_edge_bps(edge_input, raw_edge_bps)
    edge_status = _edge_status(raw_edge_bps, cost_adjusted_edge_bps)
    reason_codes = _reason_codes(edge_input, raw_edge_bps, cost_adjusted_edge_bps)

    return CostAdjustedProbabilityEdgeV10Result(
        market_price_probability=edge_input.market_price_probability,
        forecast_probability=edge_input.forecast_probability,
        fee_cost_bps=edge_input.fee_cost_bps,
        slippage_cost_bps=edge_input.slippage_cost_bps,
        settlement_cost_bps=edge_input.settlement_cost_bps,
        resolution_risk_premium_bps=edge_input.resolution_risk_premium_bps,
        confidence_penalty_bps=edge_input.confidence_penalty_bps,
        raw_edge_bps=raw_edge_bps,
        cost_adjusted_edge_bps=cost_adjusted_edge_bps,
        edge_status=edge_status,
        reason_codes=reason_codes,
    )


def cost_adjusted_probability_edge_v10_payload(
    report: CostAdjustedProbabilityEdgeV10Result,
) -> dict[str, Any]:
    if type(report) is not CostAdjustedProbabilityEdgeV10Result:
        raise ValueError("report must be a CostAdjustedProbabilityEdgeV10Result")
    _require_hard_flags("result", report)
    return {
        "market_price_probability": str(report.market_price_probability),
        "forecast_probability": str(report.forecast_probability),
        "fee_cost_bps": str(report.fee_cost_bps),
        "slippage_cost_bps": str(report.slippage_cost_bps),
        "settlement_cost_bps": str(report.settlement_cost_bps),
        "resolution_risk_premium_bps": str(report.resolution_risk_premium_bps),
        "confidence_penalty_bps": str(report.confidence_penalty_bps),
        "raw_edge_bps": str(report.raw_edge_bps),
        "cost_adjusted_edge_bps": str(report.cost_adjusted_edge_bps),
        "edge_status": report.edge_status,
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _raw_edge_bps(edge_input: CostAdjustedProbabilityEdgeV10Input) -> Decimal:
    return _normalize_decimal(
        "raw_edge_bps",
        (edge_input.forecast_probability - edge_input.market_price_probability)
        * BPS_MULTIPLIER,
    )


def _cost_adjusted_edge_bps(
    edge_input: CostAdjustedProbabilityEdgeV10Input,
    raw_edge_bps: Decimal,
) -> Decimal:
    return _normalize_decimal(
        "cost_adjusted_edge_bps",
        raw_edge_bps - _total_cost_bps(edge_input),
    )


def _total_cost_bps(edge_input: CostAdjustedProbabilityEdgeV10Input) -> Decimal:
    return _normalize_nonnegative_decimal(
        "total_cost_bps",
        (
            edge_input.fee_cost_bps
            + edge_input.slippage_cost_bps
            + edge_input.settlement_cost_bps
            + edge_input.resolution_risk_premium_bps
            + edge_input.confidence_penalty_bps
        ),
    )


def _edge_status(raw_edge_bps: Decimal, cost_adjusted_edge_bps: Decimal) -> str:
    if raw_edge_bps <= ZERO:
        return "negative_edge"
    if cost_adjusted_edge_bps <= ZERO:
        return "cost_dragged_edge"
    return "positive_edge"


def _reason_codes(
    edge_input: CostAdjustedProbabilityEdgeV10Input,
    raw_edge_bps: Decimal,
    cost_adjusted_edge_bps: Decimal,
) -> tuple[str, ...]:
    codes = [
        "raw_edge_positive" if raw_edge_bps > ZERO else "raw_edge_nonpositive",
        (
            "cost_adjusted_edge_positive"
            if cost_adjusted_edge_bps > ZERO
            else "cost_adjusted_edge_nonpositive"
        ),
    ]
    if raw_edge_bps > ZERO and cost_adjusted_edge_bps <= ZERO:
        codes.append("cost_drag_exceeds_raw_edge")
    if edge_input.fee_cost_bps > ZERO:
        codes.append("fee_cost_present")
    if edge_input.slippage_cost_bps > ZERO:
        codes.append("slippage_cost_present")
    if edge_input.settlement_cost_bps > ZERO:
        codes.append("settlement_cost_present")
    if edge_input.resolution_risk_premium_bps > ZERO:
        codes.append("resolution_risk_premium_present")
    if edge_input.confidence_penalty_bps > ZERO:
        codes.append("confidence_penalty_present")
    return tuple(codes)


def _validate_result(result: CostAdjustedProbabilityEdgeV10Result) -> None:
    edge_input = CostAdjustedProbabilityEdgeV10Input(
        market_price_probability=result.market_price_probability,
        forecast_probability=result.forecast_probability,
        fee_cost_bps=result.fee_cost_bps,
        slippage_cost_bps=result.slippage_cost_bps,
        settlement_cost_bps=result.settlement_cost_bps,
        resolution_risk_premium_bps=result.resolution_risk_premium_bps,
        confidence_penalty_bps=result.confidence_penalty_bps,
    )
    expected_raw_edge_bps = _raw_edge_bps(edge_input)
    expected_cost_adjusted_edge_bps = _cost_adjusted_edge_bps(
        edge_input,
        expected_raw_edge_bps,
    )
    expected_edge_status = _edge_status(
        expected_raw_edge_bps,
        expected_cost_adjusted_edge_bps,
    )
    expected_reason_codes = _reason_codes(
        edge_input,
        expected_raw_edge_bps,
        expected_cost_adjusted_edge_bps,
    )
    if result.raw_edge_bps != expected_raw_edge_bps:
        raise ValueError("raw_edge_bps must match probability gap")
    if result.cost_adjusted_edge_bps != expected_cost_adjusted_edge_bps:
        raise ValueError("cost_adjusted_edge_bps must match edge after costs")
    if result.edge_status != expected_edge_status:
        raise ValueError("edge_status must match cost-adjusted edge")
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match edge inputs")


def _normalize_probability(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal


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
    "CostAdjustedProbabilityEdgeV10Input",
    "CostAdjustedProbabilityEdgeV10Result",
    "cost_adjusted_probability_edge_v10_payload",
    "strategy_cost_adjusted_probability_edge_v10",
)
