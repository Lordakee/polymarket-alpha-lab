"""Pure report-only resolution cost/risk scoring for candidate events."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COST_DRAG_CAP_BPS = Decimal("280.000000")
SETTLEMENT_DELAY_CAP_HOURS = Decimal("336.000000")

RISK_STATUSES = ("pass", "watch", "blocked")
REQUIRED_FOLLOWUPS = (
    "review_fee_drag",
    "reduce_fee_drag",
    "review_expected_slippage",
    "reduce_expected_slippage",
    "clarify_dispute_ambiguity",
    "resolve_dispute_ambiguity",
    "track_settlement_delay",
    "plan_settlement_delay",
    "refresh_resolution_source_confidence",
)
REASON_CODES = (
    "resolution_cost_risk_clear",
    "fee_drag_present",
    "fee_drag_high",
    "expected_slippage_present",
    "expected_slippage_high",
    "dispute_ambiguity_present",
    "dispute_ambiguity_high",
    "settlement_delay_present",
    "settlement_delay_long",
    "resolution_source_confidence_gap",
    "resolution_source_confidence_severe_gap",
)


@dataclass(frozen=True)
class StrategyEventResolutionCostRiskScoreV10Input:
    market_id: str
    fee_drag_bps: Decimal
    expected_slippage_bps: Decimal
    dispute_ambiguity_score: Decimal
    settlement_delay_hours: Decimal
    resolution_source_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyEventResolutionCostRiskScoreV10Input:
            raise ValueError("input must be a StrategyEventResolutionCostRiskScoreV10Input")
        _require_canonical_string("market_id", self.market_id)
        for field_name in ("fee_drag_bps", "expected_slippage_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "dispute_ambiguity_score",
            _normalize_ratio_decimal(
                "dispute_ambiguity_score",
                self.dispute_ambiguity_score,
            ),
        )
        object.__setattr__(
            self,
            "settlement_delay_hours",
            _normalize_nonnegative_decimal(
                "settlement_delay_hours",
                self.settlement_delay_hours,
            ),
        )
        object.__setattr__(
            self,
            "resolution_source_confidence",
            _normalize_ratio_decimal(
                "resolution_source_confidence",
                self.resolution_source_confidence,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyEventResolutionCostRiskScoreV10Report:
    market_id: str
    fee_drag_bps: Decimal
    expected_slippage_bps: Decimal
    dispute_ambiguity_score: Decimal
    settlement_delay_hours: Decimal
    resolution_source_confidence: Decimal
    cost_drag_bps: Decimal
    resolution_cost_risk_score: Decimal
    risk_status: str
    required_followups: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyEventResolutionCostRiskScoreV10Report:
            raise ValueError("report must be a StrategyEventResolutionCostRiskScoreV10Report")
        _require_canonical_string("market_id", self.market_id)
        for field_name in ("fee_drag_bps", "expected_slippage_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "dispute_ambiguity_score",
            _normalize_ratio_decimal(
                "dispute_ambiguity_score",
                self.dispute_ambiguity_score,
            ),
        )
        object.__setattr__(
            self,
            "settlement_delay_hours",
            _normalize_nonnegative_decimal(
                "settlement_delay_hours",
                self.settlement_delay_hours,
            ),
        )
        object.__setattr__(
            self,
            "resolution_source_confidence",
            _normalize_ratio_decimal(
                "resolution_source_confidence",
                self.resolution_source_confidence,
            ),
        )
        object.__setattr__(
            self,
            "cost_drag_bps",
            _normalize_nonnegative_decimal("cost_drag_bps", self.cost_drag_bps),
        )
        object.__setattr__(
            self,
            "resolution_cost_risk_score",
            _normalize_ratio_decimal(
                "resolution_cost_risk_score",
                self.resolution_cost_risk_score,
            ),
        )
        _require_member("risk_status", self.risk_status, RISK_STATUSES)
        object.__setattr__(
            self,
            "required_followups",
            _normalize_string_tuple(
                "required_followups",
                self.required_followups,
                REQUIRED_FOLLOWUPS,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple(
                "reason_codes",
                self.reason_codes,
                REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_event_resolution_cost_risk_score_v10_payload(self)


def build_strategy_event_resolution_cost_risk_score_v10_report(
    *,
    market_id: str,
    fee_drag_bps: Decimal,
    expected_slippage_bps: Decimal,
    dispute_ambiguity_score: Decimal,
    settlement_delay_hours: Decimal,
    resolution_source_confidence: Decimal,
) -> StrategyEventResolutionCostRiskScoreV10Report:
    input_row = StrategyEventResolutionCostRiskScoreV10Input(
        market_id=market_id,
        fee_drag_bps=fee_drag_bps,
        expected_slippage_bps=expected_slippage_bps,
        dispute_ambiguity_score=dispute_ambiguity_score,
        settlement_delay_hours=settlement_delay_hours,
        resolution_source_confidence=resolution_source_confidence,
    )
    cost_drag_bps = _cost_drag_bps(input_row)
    risk_score = _resolution_cost_risk_score(input_row, cost_drag_bps)

    return StrategyEventResolutionCostRiskScoreV10Report(
        market_id=input_row.market_id,
        fee_drag_bps=input_row.fee_drag_bps,
        expected_slippage_bps=input_row.expected_slippage_bps,
        dispute_ambiguity_score=input_row.dispute_ambiguity_score,
        settlement_delay_hours=input_row.settlement_delay_hours,
        resolution_source_confidence=input_row.resolution_source_confidence,
        cost_drag_bps=cost_drag_bps,
        resolution_cost_risk_score=risk_score,
        risk_status=_risk_status(input_row, risk_score),
        required_followups=_required_followups(input_row),
        reason_codes=_reason_codes(input_row),
    )


def strategy_event_resolution_cost_risk_score_v10_payload(
    report: StrategyEventResolutionCostRiskScoreV10Report,
) -> dict[str, Any]:
    if type(report) is not StrategyEventResolutionCostRiskScoreV10Report:
        raise ValueError("report must be a StrategyEventResolutionCostRiskScoreV10Report")
    _require_hard_flags("report", report)
    return {
        "market_id": report.market_id,
        "fee_drag_bps": str(report.fee_drag_bps),
        "expected_slippage_bps": str(report.expected_slippage_bps),
        "dispute_ambiguity_score": str(report.dispute_ambiguity_score),
        "settlement_delay_hours": str(report.settlement_delay_hours),
        "resolution_source_confidence": str(report.resolution_source_confidence),
        "cost_drag_bps": str(report.cost_drag_bps),
        "resolution_cost_risk_score": str(report.resolution_cost_risk_score),
        "risk_status": report.risk_status,
        "required_followups": list(report.required_followups),
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _cost_drag_bps(
    input_row: StrategyEventResolutionCostRiskScoreV10Input,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "cost_drag_bps",
        input_row.fee_drag_bps + input_row.expected_slippage_bps,
    )


def _resolution_cost_risk_score(
    input_row: StrategyEventResolutionCostRiskScoreV10Input,
    cost_drag_bps: Decimal,
) -> Decimal:
    cost_drag_component = (
        min(cost_drag_bps, COST_DRAG_CAP_BPS)
        / COST_DRAG_CAP_BPS
        * Decimal("0.280000")
    )
    ambiguity_component = input_row.dispute_ambiguity_score * Decimal("0.300000")
    settlement_delay_component = (
        min(input_row.settlement_delay_hours, SETTLEMENT_DELAY_CAP_HOURS)
        / SETTLEMENT_DELAY_CAP_HOURS
        * Decimal("0.300000")
    )
    source_confidence_component = (
        ONE - input_row.resolution_source_confidence
    ) * Decimal("0.333333")
    score = (
        cost_drag_component
        + ambiguity_component
        + settlement_delay_component
        + source_confidence_component
    )
    return min(max(score, ZERO), ONE).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _risk_status(
    input_row: StrategyEventResolutionCostRiskScoreV10Input,
    risk_score: Decimal,
) -> str:
    if risk_score >= Decimal("0.700000"):
        return "blocked"
    if input_row.dispute_ambiguity_score >= Decimal("0.900000"):
        return "blocked"
    if input_row.resolution_source_confidence <= Decimal("0.250000"):
        return "blocked"
    if risk_score > ZERO:
        return "watch"
    return "pass"


def _required_followups(
    input_row: StrategyEventResolutionCostRiskScoreV10Input,
) -> tuple[str, ...]:
    values: list[str] = []
    if input_row.fee_drag_bps >= Decimal("100.000000"):
        values.append("reduce_fee_drag")
    elif input_row.fee_drag_bps > ZERO:
        values.append("review_fee_drag")
    if input_row.expected_slippage_bps >= Decimal("100.000000"):
        values.append("reduce_expected_slippage")
    elif input_row.expected_slippage_bps > ZERO:
        values.append("review_expected_slippage")
    if input_row.dispute_ambiguity_score >= Decimal("0.750000"):
        values.append("resolve_dispute_ambiguity")
    elif input_row.dispute_ambiguity_score > ZERO:
        values.append("clarify_dispute_ambiguity")
    if input_row.settlement_delay_hours >= Decimal("168.000000"):
        values.append("plan_settlement_delay")
    elif input_row.settlement_delay_hours > ZERO:
        values.append("track_settlement_delay")
    if input_row.resolution_source_confidence < Decimal("0.850000"):
        values.append("refresh_resolution_source_confidence")
    return tuple(values)


def _reason_codes(
    input_row: StrategyEventResolutionCostRiskScoreV10Input,
) -> tuple[str, ...]:
    values: list[str] = []
    if input_row.fee_drag_bps >= Decimal("100.000000"):
        values.append("fee_drag_high")
    elif input_row.fee_drag_bps > ZERO:
        values.append("fee_drag_present")
    if input_row.expected_slippage_bps >= Decimal("100.000000"):
        values.append("expected_slippage_high")
    elif input_row.expected_slippage_bps > ZERO:
        values.append("expected_slippage_present")
    if input_row.dispute_ambiguity_score >= Decimal("0.750000"):
        values.append("dispute_ambiguity_high")
    elif input_row.dispute_ambiguity_score > ZERO:
        values.append("dispute_ambiguity_present")
    if input_row.settlement_delay_hours >= Decimal("168.000000"):
        values.append("settlement_delay_long")
    elif input_row.settlement_delay_hours > ZERO:
        values.append("settlement_delay_present")
    if input_row.resolution_source_confidence <= Decimal("0.250000"):
        values.append("resolution_source_confidence_severe_gap")
    elif input_row.resolution_source_confidence < Decimal("0.850000"):
        values.append("resolution_source_confidence_gap")
    if not values:
        values.append("resolution_cost_risk_clear")
    return tuple(values)


def _validate_report(report: StrategyEventResolutionCostRiskScoreV10Report) -> None:
    input_row = StrategyEventResolutionCostRiskScoreV10Input(
        market_id=report.market_id,
        fee_drag_bps=report.fee_drag_bps,
        expected_slippage_bps=report.expected_slippage_bps,
        dispute_ambiguity_score=report.dispute_ambiguity_score,
        settlement_delay_hours=report.settlement_delay_hours,
        resolution_source_confidence=report.resolution_source_confidence,
    )
    expected_cost_drag_bps = _cost_drag_bps(input_row)
    expected_score = _resolution_cost_risk_score(input_row, expected_cost_drag_bps)
    if report.cost_drag_bps != expected_cost_drag_bps:
        raise ValueError("cost_drag_bps must match fee and slippage inputs")
    if report.resolution_cost_risk_score != expected_score:
        raise ValueError("resolution_cost_risk_score must match resolution risk inputs")
    if report.risk_status != _risk_status(input_row, expected_score):
        raise ValueError("risk_status must match resolution risk inputs")
    if report.required_followups != _required_followups(input_row):
        raise ValueError("required_followups must match resolution risk inputs")
    if report.reason_codes != _reason_codes(input_row):
        raise ValueError("reason_codes must match resolution risk inputs")


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_ratio_decimal(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_nonnegative_decimal(field_name, value)
    if decimal > ONE:
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


def _normalize_string_tuple(
    field_name: str,
    values: Any,
    allowed_values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not values:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in values:
        _require_member(field_name, value, allowed_values)
    return values


def _require_member(
    field_name: str,
    value: Any,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} is not supported")


def _require_hard_flags(field_name: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "REASON_CODES",
    "REQUIRED_FOLLOWUPS",
    "RISK_STATUSES",
    "StrategyEventResolutionCostRiskScoreV10Input",
    "StrategyEventResolutionCostRiskScoreV10Report",
    "build_strategy_event_resolution_cost_risk_score_v10_report",
    "strategy_event_resolution_cost_risk_score_v10_payload",
)
