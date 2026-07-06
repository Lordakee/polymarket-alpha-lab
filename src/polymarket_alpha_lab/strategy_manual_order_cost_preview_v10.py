"""Paper-only readonly manual cost preview."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
BPS_DENOMINATOR = Decimal("10000.000000")
WATCH_BREAKEVEN_PROBABILITY = Decimal("0.500000")
COST_WARNING_TIERS = ("ok", "watch", "block")
SIDES = ("buy", "sell")


@dataclass(frozen=True)
class ManualOrderCostPreviewInput:
    side: str
    outcome_price: Decimal
    intended_size: Decimal
    fee_rate: Decimal
    estimated_slippage_bps: Decimal
    settlement_cost_bps: Decimal
    gas_or_deposit_cost: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "side", _normalize_side(self.side))
        object.__setattr__(
            self,
            "outcome_price",
            _normalize_probability_price("outcome_price", self.outcome_price),
        )
        object.__setattr__(
            self,
            "intended_size",
            _normalize_positive_decimal("intended_size", self.intended_size),
        )
        for field_name in (
            "fee_rate",
            "estimated_slippage_bps",
            "settlement_cost_bps",
            "gas_or_deposit_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("manual cost preview input", self)
        require_paper_only_flags("manual cost preview input", self)


@dataclass(frozen=True)
class ManualOrderCostPreviewResult:
    side: str
    outcome_price: Decimal
    intended_size: Decimal
    fee_rate: Decimal
    estimated_slippage_bps: Decimal
    settlement_cost_bps: Decimal
    gas_or_deposit_cost: Decimal
    gross_cost: Decimal
    fee_cost: Decimal
    slippage_cost: Decimal
    total_cost: Decimal
    breakeven_probability: Decimal
    cost_warning_tier: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "side", _normalize_side(self.side))
        object.__setattr__(
            self,
            "outcome_price",
            _normalize_probability_price("outcome_price", self.outcome_price),
        )
        object.__setattr__(
            self,
            "intended_size",
            _normalize_positive_decimal("intended_size", self.intended_size),
        )
        for field_name in (
            "fee_rate",
            "estimated_slippage_bps",
            "settlement_cost_bps",
            "gas_or_deposit_cost",
            "gross_cost",
            "fee_cost",
            "slippage_cost",
            "total_cost",
            "breakeven_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.cost_warning_tier not in COST_WARNING_TIERS:
            raise ValueError("cost_warning_tier must be ok, watch, or block")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("manual cost preview result", self)
        require_paper_only_flags("manual cost preview result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return manual_order_cost_preview_payload(self)


def preview_manual_order_cost(
    preview_input: ManualOrderCostPreviewInput,
) -> ManualOrderCostPreviewResult:
    if type(preview_input) is not ManualOrderCostPreviewInput:
        raise ValueError("preview_input must be a ManualOrderCostPreviewInput")
    require_paper_only_flags("manual cost preview input", preview_input)
    reject_unsafe_surface_fields("manual cost preview input", preview_input)

    gross_cost = _normalize_nonnegative_decimal(
        "gross_cost",
        preview_input.outcome_price * preview_input.intended_size,
    )
    fee_cost = _normalize_nonnegative_decimal(
        "fee_cost",
        gross_cost * preview_input.fee_rate,
    )
    slippage_cost = _normalize_nonnegative_decimal(
        "slippage_cost",
        gross_cost * preview_input.estimated_slippage_bps / BPS_DENOMINATOR,
    )
    settlement_cost = _normalize_nonnegative_decimal(
        "settlement_cost",
        gross_cost * preview_input.settlement_cost_bps / BPS_DENOMINATOR,
    )
    total_cost = _normalize_nonnegative_decimal(
        "total_cost",
        (
            gross_cost
            + fee_cost
            + slippage_cost
            + settlement_cost
            + preview_input.gas_or_deposit_cost
        ),
    )
    breakeven_probability = _normalize_nonnegative_decimal(
        "breakeven_probability",
        total_cost / preview_input.intended_size,
    )
    cost_warning_tier = _cost_warning_tier(breakeven_probability)

    return ManualOrderCostPreviewResult(
        side=preview_input.side,
        outcome_price=preview_input.outcome_price,
        intended_size=preview_input.intended_size,
        fee_rate=preview_input.fee_rate,
        estimated_slippage_bps=preview_input.estimated_slippage_bps,
        settlement_cost_bps=preview_input.settlement_cost_bps,
        gas_or_deposit_cost=preview_input.gas_or_deposit_cost,
        gross_cost=gross_cost,
        fee_cost=fee_cost,
        slippage_cost=slippage_cost,
        total_cost=total_cost,
        breakeven_probability=breakeven_probability,
        cost_warning_tier=cost_warning_tier,
        reason_codes=_reason_codes(
            preview_input.reason_codes,
            fixed_cost=preview_input.gas_or_deposit_cost,
            breakeven_probability=breakeven_probability,
            cost_warning_tier=cost_warning_tier,
        ),
    )


def manual_order_cost_preview_payload(
    report: ManualOrderCostPreviewResult,
) -> dict[str, Any]:
    if type(report) is not ManualOrderCostPreviewResult:
        raise ValueError("report must be a ManualOrderCostPreviewResult")
    require_paper_only_flags("manual cost preview result", report)
    reject_unsafe_surface_fields("manual cost preview result", report)
    return json_ready_no_floats(
        {
            "side": report.side,
            "outcome_price": report.outcome_price,
            "intended_size": report.intended_size,
            "fee_rate": report.fee_rate,
            "estimated_slippage_bps": report.estimated_slippage_bps,
            "settlement_cost_bps": report.settlement_cost_bps,
            "gas_or_deposit_cost": report.gas_or_deposit_cost,
            "gross_cost": report.gross_cost,
            "fee_cost": report.fee_cost,
            "slippage_cost": report.slippage_cost,
            "total_cost": report.total_cost,
            "breakeven_probability": report.breakeven_probability,
            "cost_warning_tier": report.cost_warning_tier,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _reason_codes(
    existing: tuple[str, ...],
    *,
    fixed_cost: Decimal,
    breakeven_probability: Decimal,
    cost_warning_tier: str,
) -> tuple[str, ...]:
    additions = ["manual_cost_preview"]
    if fixed_cost > ZERO:
        additions.append("fixed_cost_present")
    if breakeven_probability > ONE:
        additions.append("breakeven_probability_above_one")
    additions.append(f"cost_warning_{cost_warning_tier}")
    return _append_reason_codes(existing, tuple(additions))


def _cost_warning_tier(breakeven_probability: Decimal) -> str:
    if breakeven_probability > ONE:
        return "block"
    if breakeven_probability >= WATCH_BREAKEVEN_PROBABILITY:
        return "watch"
    return "ok"


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _normalize_side(value: Any) -> str:
    _require_canonical_string("side", value)
    if value not in SIDES:
        raise ValueError("side must be buy or sell")
    return value


def _normalize_reason_codes(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    return value


def _normalize_probability_price(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal


def _normalize_positive_decimal(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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
    return value.quantize(QUANTUM)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "ManualOrderCostPreviewInput",
    "ManualOrderCostPreviewResult",
    "manual_order_cost_preview_payload",
    "preview_manual_order_cost",
)
