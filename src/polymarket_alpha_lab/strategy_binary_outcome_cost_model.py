"""Pure binary-outcome cost model for strategy research.

Polymarket positions resolve to event-contingent payoffs: a YES share pays
1.00 only if the event occurs, and a NO share pays 1.00 only if it does not.
This module models those probability payoffs directly instead of treating
outcome tokens like ordinary assets with mark-to-market price returns.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
EVENT_PAYOFF_MODE = "binary_probability_payoff"
REASON_CODE = "binary_event_payoff_model"


@dataclass(frozen=True)
class StrategyBinaryOutcomeCostAssumptions:
    yes_price: Decimal
    no_price: Decimal
    estimated_event_probability: Decimal
    shares: Decimal
    spread_buffer: Decimal = ZERO
    slippage_buffer: Decimal = ZERO
    taker_fee_rate: Decimal = Decimal("0.020000")

    def __post_init__(self) -> None:
        for field_name in (
            "yes_price",
            "no_price",
            "estimated_event_probability",
        ):
            _require_probability(field_name, getattr(self, field_name))
        _require_positive_decimal("shares", self.shares)
        for field_name in ("spread_buffer", "slippage_buffer", "taker_fee_rate"):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))


@dataclass(frozen=True)
class StrategyBinaryOutcomeCostReport:
    yes_price: Decimal
    no_price: Decimal
    estimated_event_probability: Decimal
    shares: Decimal
    spread_buffer: Decimal
    slippage_buffer: Decimal
    taker_fee_rate: Decimal
    yes_gross_cost: Decimal
    no_gross_cost: Decimal
    yes_taker_fee: Decimal
    no_taker_fee: Decimal
    yes_entry_cost: Decimal
    no_entry_cost: Decimal
    yes_round_trip_fee_drag: Decimal
    no_round_trip_fee_drag: Decimal
    spread_slippage_buffer_cost: Decimal
    yes_total_cost: Decimal
    no_total_cost: Decimal
    yes_breakeven_probability: Decimal
    no_breakeven_probability: Decimal
    yes_net_expected_value: Decimal
    no_net_expected_value: Decimal
    event_payoff_mode: str = EVENT_PAYOFF_MODE
    reason_codes: tuple[str, ...] = (REASON_CODE,)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "yes_price",
            "no_price",
            "estimated_event_probability",
            "yes_breakeven_probability",
            "no_breakeven_probability",
        ):
            _require_quantized_nonnegative_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "shares",
            "spread_buffer",
            "slippage_buffer",
            "taker_fee_rate",
            "yes_gross_cost",
            "no_gross_cost",
            "yes_taker_fee",
            "no_taker_fee",
            "yes_entry_cost",
            "no_entry_cost",
            "yes_round_trip_fee_drag",
            "no_round_trip_fee_drag",
            "spread_slippage_buffer_cost",
            "yes_total_cost",
            "no_total_cost",
        ):
            _require_quantized_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_quantized_decimal("yes_net_expected_value", self.yes_net_expected_value)
        _require_quantized_decimal("no_net_expected_value", self.no_net_expected_value)
        if self.event_payoff_mode != EVENT_PAYOFF_MODE:
            raise ValueError("event_payoff_mode must be binary_probability_payoff")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_strategy_binary_outcome_cost_report(
    assumptions: StrategyBinaryOutcomeCostAssumptions,
) -> StrategyBinaryOutcomeCostReport:
    """Build cost and EV metrics for a two-outcome event position."""

    if type(assumptions) is not StrategyBinaryOutcomeCostAssumptions:
        raise ValueError("assumptions must be a StrategyBinaryOutcomeCostAssumptions")

    yes_price = _quantize_decimal(assumptions.yes_price)
    no_price = _quantize_decimal(assumptions.no_price)
    estimated_event_probability = _quantize_decimal(
        assumptions.estimated_event_probability,
    )
    shares = _quantize_decimal(assumptions.shares)
    spread_buffer = _quantize_decimal(assumptions.spread_buffer)
    slippage_buffer = _quantize_decimal(assumptions.slippage_buffer)
    taker_fee_rate = _quantize_decimal(assumptions.taker_fee_rate)

    yes_gross_cost = _quantize_decimal(yes_price * shares)
    no_gross_cost = _quantize_decimal(no_price * shares)
    yes_taker_fee = _quantize_decimal(yes_gross_cost * taker_fee_rate)
    no_taker_fee = _quantize_decimal(no_gross_cost * taker_fee_rate)
    yes_entry_cost = _quantize_decimal(yes_gross_cost + yes_taker_fee)
    no_entry_cost = _quantize_decimal(no_gross_cost + no_taker_fee)
    payoff_taker_fee = _quantize_decimal(shares * taker_fee_rate)
    yes_round_trip_fee_drag = _quantize_decimal(yes_taker_fee + payoff_taker_fee)
    no_round_trip_fee_drag = _quantize_decimal(no_taker_fee + payoff_taker_fee)
    spread_slippage_buffer_cost = _quantize_decimal(
        shares * (spread_buffer + slippage_buffer),
    )
    yes_total_cost = _quantize_decimal(
        yes_gross_cost + yes_round_trip_fee_drag + spread_slippage_buffer_cost,
    )
    no_total_cost = _quantize_decimal(
        no_gross_cost + no_round_trip_fee_drag + spread_slippage_buffer_cost,
    )
    yes_breakeven_probability = _quantize_decimal(yes_total_cost / shares)
    no_breakeven_probability = _quantize_decimal(no_total_cost / shares)
    yes_expected_payoff = _quantize_decimal(estimated_event_probability * shares)
    no_expected_payoff = _quantize_decimal((ONE - estimated_event_probability) * shares)
    yes_net_expected_value = _quantize_decimal(yes_expected_payoff - yes_total_cost)
    no_net_expected_value = _quantize_decimal(no_expected_payoff - no_total_cost)

    return StrategyBinaryOutcomeCostReport(
        yes_price=yes_price,
        no_price=no_price,
        estimated_event_probability=estimated_event_probability,
        shares=shares,
        spread_buffer=spread_buffer,
        slippage_buffer=slippage_buffer,
        taker_fee_rate=taker_fee_rate,
        yes_gross_cost=yes_gross_cost,
        no_gross_cost=no_gross_cost,
        yes_taker_fee=yes_taker_fee,
        no_taker_fee=no_taker_fee,
        yes_entry_cost=yes_entry_cost,
        no_entry_cost=no_entry_cost,
        yes_round_trip_fee_drag=yes_round_trip_fee_drag,
        no_round_trip_fee_drag=no_round_trip_fee_drag,
        spread_slippage_buffer_cost=spread_slippage_buffer_cost,
        yes_total_cost=yes_total_cost,
        no_total_cost=no_total_cost,
        yes_breakeven_probability=yes_breakeven_probability,
        no_breakeven_probability=no_breakeven_probability,
        yes_net_expected_value=yes_net_expected_value,
        no_net_expected_value=no_net_expected_value,
    )


def _validate_report_consistency(report: StrategyBinaryOutcomeCostReport) -> None:
    expected_yes_gross_cost = _quantize_decimal(report.yes_price * report.shares)
    if report.yes_gross_cost != expected_yes_gross_cost:
        raise ValueError("yes_gross_cost must match yes price and shares")
    expected_no_gross_cost = _quantize_decimal(report.no_price * report.shares)
    if report.no_gross_cost != expected_no_gross_cost:
        raise ValueError("no_gross_cost must match no price and shares")

    expected_yes_taker_fee = _quantize_decimal(
        report.yes_gross_cost * report.taker_fee_rate,
    )
    if report.yes_taker_fee != expected_yes_taker_fee:
        raise ValueError("yes_taker_fee must match yes gross cost and taker fee rate")
    expected_no_taker_fee = _quantize_decimal(
        report.no_gross_cost * report.taker_fee_rate,
    )
    if report.no_taker_fee != expected_no_taker_fee:
        raise ValueError("no_taker_fee must match no gross cost and taker fee rate")

    if report.yes_entry_cost != _quantize_decimal(
        report.yes_gross_cost + report.yes_taker_fee,
    ):
        raise ValueError("yes_entry_cost must match yes gross cost and taker fee")
    if report.no_entry_cost != _quantize_decimal(
        report.no_gross_cost + report.no_taker_fee,
    ):
        raise ValueError("no_entry_cost must match no gross cost and taker fee")

    expected_payoff_taker_fee = _quantize_decimal(report.shares * report.taker_fee_rate)
    if report.yes_round_trip_fee_drag != _quantize_decimal(
        report.yes_taker_fee + expected_payoff_taker_fee,
    ):
        raise ValueError("yes_round_trip_fee_drag must include entry and payoff fees")
    if report.no_round_trip_fee_drag != _quantize_decimal(
        report.no_taker_fee + expected_payoff_taker_fee,
    ):
        raise ValueError("no_round_trip_fee_drag must include entry and payoff fees")

    expected_buffer_cost = _quantize_decimal(
        report.shares * (report.spread_buffer + report.slippage_buffer),
    )
    if report.spread_slippage_buffer_cost != expected_buffer_cost:
        raise ValueError("spread_slippage_buffer_cost must match shares and buffers")

    expected_yes_total_cost = _quantize_decimal(
        report.yes_gross_cost
        + report.yes_round_trip_fee_drag
        + report.spread_slippage_buffer_cost,
    )
    if report.yes_total_cost != expected_yes_total_cost:
        raise ValueError("yes_total_cost must match yes costs and buffers")
    expected_no_total_cost = _quantize_decimal(
        report.no_gross_cost
        + report.no_round_trip_fee_drag
        + report.spread_slippage_buffer_cost,
    )
    if report.no_total_cost != expected_no_total_cost:
        raise ValueError("no_total_cost must match no costs and buffers")

    if report.yes_breakeven_probability != _quantize_decimal(
        report.yes_total_cost / report.shares,
    ):
        raise ValueError("yes_breakeven_probability must match yes total cost")
    if report.no_breakeven_probability != _quantize_decimal(
        report.no_total_cost / report.shares,
    ):
        raise ValueError("no_breakeven_probability must match no total cost")

    expected_yes_ev = _quantize_decimal(
        report.estimated_event_probability * report.shares - report.yes_total_cost,
    )
    if report.yes_net_expected_value != expected_yes_ev:
        raise ValueError("yes_net_expected_value must match binary event payoff")
    expected_no_ev = _quantize_decimal(
        (ONE - report.estimated_event_probability) * report.shares
        - report.no_total_cost,
    )
    if report.no_net_expected_value != expected_no_ev:
        raise ValueError("no_net_expected_value must match binary event payoff")


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a tuple of strings")
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple of strings")
    if not reason_codes:
        raise ValueError("reason_codes must be nonempty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(reason_code)
    return tuple(normalized)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_probability(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_positive_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_quantized_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value != _quantize_decimal(value):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _require_quantized_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != _quantize_decimal(value):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


__all__ = (
    "StrategyBinaryOutcomeCostAssumptions",
    "StrategyBinaryOutcomeCostReport",
    "build_strategy_binary_outcome_cost_report",
)
