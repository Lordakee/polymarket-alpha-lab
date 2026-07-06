"""Pure paper/report/readonly candidate expected-value buffer v10."""

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
BPS_PER_UNIT = Decimal("10000.000000")
SCREENING_STATUSES = ("candidate", "watch", "blocked")
SCREENING_DECISIONS = ("screen_in", "manual_review", "reject")


@dataclass(frozen=True)
class StrategyCandidateExpectedValueBufferV10Input:
    market_id: str
    forecast_probability: Decimal
    market_probability: Decimal
    fee_bps: Decimal
    spread_bps: Decimal
    slippage_bps: Decimal
    forecast_uncertainty_bps: Decimal
    resolution_ambiguity_bps: Decimal
    liquidity_exit_cost_bps: Decimal
    minimum_buffer_bps: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in ("forecast_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_bps",
            "spread_bps",
            "slippage_bps",
            "forecast_uncertainty_bps",
            "resolution_ambiguity_bps",
            "liquidity_exit_cost_bps",
            "minimum_buffer_bps",
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
        reject_unsafe_surface_fields("candidate expected value buffer input", self)
        require_paper_only_flags("candidate expected value buffer input", self)


@dataclass(frozen=True)
class StrategyCandidateExpectedValueBufferV10Result:
    market_id: str
    forecast_probability: Decimal
    market_probability: Decimal
    gross_edge_bps: Decimal
    fee_bps: Decimal
    spread_bps: Decimal
    slippage_bps: Decimal
    market_friction_cost_bps: Decimal
    forecast_uncertainty_bps: Decimal
    resolution_ambiguity_bps: Decimal
    liquidity_exit_cost_bps: Decimal
    total_conservative_adjustment_bps: Decimal
    net_expected_value_buffer_bps: Decimal
    minimum_buffer_bps: Decimal
    screening_status: str
    screening_decision: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in ("forecast_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_edge_bps",
            "net_expected_value_buffer_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_bps",
            "spread_bps",
            "slippage_bps",
            "market_friction_cost_bps",
            "forecast_uncertainty_bps",
            "resolution_ambiguity_bps",
            "liquidity_exit_cost_bps",
            "total_conservative_adjustment_bps",
            "minimum_buffer_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("screening_status", self.screening_status, SCREENING_STATUSES)
        _require_choice(
            "screening_decision",
            self.screening_decision,
            SCREENING_DECISIONS,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("candidate expected value buffer result", self)
        require_paper_only_flags("candidate expected value buffer result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_expected_value_buffer_v10_payload(self)


def estimate_strategy_candidate_expected_value_buffer_v10(
    buffer_input: StrategyCandidateExpectedValueBufferV10Input,
) -> StrategyCandidateExpectedValueBufferV10Result:
    if type(buffer_input) is not StrategyCandidateExpectedValueBufferV10Input:
        raise ValueError(
            "buffer_input must be a StrategyCandidateExpectedValueBufferV10Input",
        )
    reject_unsafe_surface_fields("candidate expected value buffer input", buffer_input)
    require_paper_only_flags("candidate expected value buffer input", buffer_input)

    gross_edge_bps = _normalize_decimal(
        "gross_edge_bps",
        (buffer_input.forecast_probability - buffer_input.market_probability)
        * BPS_PER_UNIT,
    )
    market_friction_cost_bps = _normalize_nonnegative_decimal(
        "market_friction_cost_bps",
        buffer_input.fee_bps + buffer_input.spread_bps + buffer_input.slippage_bps,
    )
    total_conservative_adjustment_bps = _normalize_nonnegative_decimal(
        "total_conservative_adjustment_bps",
        market_friction_cost_bps
        + buffer_input.forecast_uncertainty_bps
        + buffer_input.resolution_ambiguity_bps
        + buffer_input.liquidity_exit_cost_bps,
    )
    net_expected_value_buffer_bps = _normalize_decimal(
        "net_expected_value_buffer_bps",
        gross_edge_bps - total_conservative_adjustment_bps,
    )
    screening_status = _screening_status(
        net_expected_value_buffer_bps,
        buffer_input.minimum_buffer_bps,
    )

    return StrategyCandidateExpectedValueBufferV10Result(
        market_id=buffer_input.market_id,
        forecast_probability=buffer_input.forecast_probability,
        market_probability=buffer_input.market_probability,
        gross_edge_bps=gross_edge_bps,
        fee_bps=buffer_input.fee_bps,
        spread_bps=buffer_input.spread_bps,
        slippage_bps=buffer_input.slippage_bps,
        market_friction_cost_bps=market_friction_cost_bps,
        forecast_uncertainty_bps=buffer_input.forecast_uncertainty_bps,
        resolution_ambiguity_bps=buffer_input.resolution_ambiguity_bps,
        liquidity_exit_cost_bps=buffer_input.liquidity_exit_cost_bps,
        total_conservative_adjustment_bps=total_conservative_adjustment_bps,
        net_expected_value_buffer_bps=net_expected_value_buffer_bps,
        minimum_buffer_bps=buffer_input.minimum_buffer_bps,
        screening_status=screening_status,
        screening_decision=_screening_decision(screening_status),
        reason_codes=_reason_codes(
            buffer_input.reason_codes,
            gross_edge_bps=gross_edge_bps,
            market_friction_cost_bps=market_friction_cost_bps,
            forecast_uncertainty_bps=buffer_input.forecast_uncertainty_bps,
            resolution_ambiguity_bps=buffer_input.resolution_ambiguity_bps,
            liquidity_exit_cost_bps=buffer_input.liquidity_exit_cost_bps,
            net_expected_value_buffer_bps=net_expected_value_buffer_bps,
            minimum_buffer_bps=buffer_input.minimum_buffer_bps,
            screening_status=screening_status,
        ),
    )


def strategy_candidate_expected_value_buffer_v10_payload(
    result: StrategyCandidateExpectedValueBufferV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidateExpectedValueBufferV10Result:
        raise ValueError(
            "result must be a StrategyCandidateExpectedValueBufferV10Result",
        )
    reject_unsafe_surface_fields("candidate expected value buffer result", result)
    require_paper_only_flags("candidate expected value buffer result", result)
    return json_ready_no_floats(
        {
            "market_id": result.market_id,
            "forecast_probability": result.forecast_probability,
            "market_probability": result.market_probability,
            "gross_edge_bps": result.gross_edge_bps,
            "fee_bps": result.fee_bps,
            "spread_bps": result.spread_bps,
            "slippage_bps": result.slippage_bps,
            "market_friction_cost_bps": result.market_friction_cost_bps,
            "forecast_uncertainty_bps": result.forecast_uncertainty_bps,
            "resolution_ambiguity_bps": result.resolution_ambiguity_bps,
            "liquidity_exit_cost_bps": result.liquidity_exit_cost_bps,
            "total_conservative_adjustment_bps": (
                result.total_conservative_adjustment_bps
            ),
            "net_expected_value_buffer_bps": result.net_expected_value_buffer_bps,
            "minimum_buffer_bps": result.minimum_buffer_bps,
            "screening_status": result.screening_status,
            "screening_decision": result.screening_decision,
            "reason_codes": result.reason_codes,
            "paper_only": result.paper_only,
            "report_only": result.report_only,
            "readonly": result.readonly,
        },
    )


def _screening_status(
    net_expected_value_buffer_bps: Decimal,
    minimum_buffer_bps: Decimal,
) -> str:
    if net_expected_value_buffer_bps <= ZERO:
        return "blocked"
    if net_expected_value_buffer_bps < minimum_buffer_bps:
        return "watch"
    return "candidate"


def _screening_decision(screening_status: str) -> str:
    if screening_status == "candidate":
        return "screen_in"
    if screening_status == "watch":
        return "manual_review"
    if screening_status == "blocked":
        return "reject"
    raise ValueError("screening_status must be supported")


def _reason_codes(
    existing: tuple[str, ...],
    *,
    gross_edge_bps: Decimal,
    market_friction_cost_bps: Decimal,
    forecast_uncertainty_bps: Decimal,
    resolution_ambiguity_bps: Decimal,
    liquidity_exit_cost_bps: Decimal,
    net_expected_value_buffer_bps: Decimal,
    minimum_buffer_bps: Decimal,
    screening_status: str,
) -> tuple[str, ...]:
    additions = [
        "strategy_candidate_expected_value_buffer",
        f"buffer_{screening_status}",
        _gross_edge_reason_code(gross_edge_bps),
    ]
    if market_friction_cost_bps > ZERO:
        additions.append("market_friction_applied")
    if forecast_uncertainty_bps > ZERO:
        additions.append("forecast_uncertainty_applied")
    if resolution_ambiguity_bps > ZERO:
        additions.append("resolution_ambiguity_applied")
    if liquidity_exit_cost_bps > ZERO:
        additions.append("liquidity_exit_cost_applied")
    if net_expected_value_buffer_bps <= ZERO:
        additions.append("costs_exceed_edge")
    elif net_expected_value_buffer_bps < minimum_buffer_bps:
        additions.append("minimum_buffer_not_met")
    else:
        additions.append("minimum_buffer_met")
    return _append_reason_codes(existing, tuple(additions))


def _gross_edge_reason_code(gross_edge_bps: Decimal) -> str:
    if gross_edge_bps > ZERO:
        return "gross_edge_positive"
    if gross_edge_bps == ZERO:
        return "gross_edge_flat"
    return "gross_edge_negative"


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


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
    return value.quantize(QUANTUM)


def _normalize_reason_codes(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    return value


def _require_choice(
    field_name: str,
    value: Any,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "SCREENING_STATUSES",
    "SCREENING_DECISIONS",
    "StrategyCandidateExpectedValueBufferV10Input",
    "StrategyCandidateExpectedValueBufferV10Result",
    "estimate_strategy_candidate_expected_value_buffer_v10",
    "strategy_candidate_expected_value_buffer_v10_payload",
)
