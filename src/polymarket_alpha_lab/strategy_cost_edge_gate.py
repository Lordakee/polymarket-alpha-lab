"""Paper-only cost-adjusted strategy edge gate."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_COST_EDGE_GATE_CONFIG_VERSION = "strategy-cost-edge-gate-v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
GATE_STATUSES = ("candidate", "watch", "blocked")


@dataclass(frozen=True)
class StrategyCostEdgeGateConfig:
    config_version: str = DEFAULT_STRATEGY_COST_EDGE_GATE_CONFIG_VERSION
    min_candidate_cost_adjusted_edge: Decimal = Decimal("0.010000")
    min_watch_cost_adjusted_edge: Decimal = Decimal("0.000000")
    max_total_cost_per_share: Decimal = Decimal("0.020000")
    max_spread_cost: Decimal = Decimal("0.006000")
    max_fee_cost: Decimal = Decimal("0.006000")
    max_slippage_cost: Decimal = Decimal("0.006000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_candidate_cost_adjusted_edge",
            "min_watch_cost_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_total_cost_per_share",
            "max_spread_cost",
            "max_fee_cost",
            "max_slippage_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_cost_adjusted_edge > self.min_candidate_cost_adjusted_edge:
            raise ValueError(
                "min_watch_cost_adjusted_edge must not exceed "
                "min_candidate_cost_adjusted_edge",
            )
        reject_unsafe_surface_fields("strategy cost edge gate config", self)
        require_paper_only_flags("strategy cost edge gate config", self)


@dataclass(frozen=True)
class StrategyCostEdgeGateInput:
    candidate_id: str
    net_edge_per_share: Decimal
    total_cost_per_share: Decimal
    spread_cost: Decimal
    fee_cost: Decimal
    slippage_cost: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        object.__setattr__(
            self,
            "net_edge_per_share",
            _normalize_decimal("net_edge_per_share", self.net_edge_per_share),
        )
        for field_name in (
            "total_cost_per_share",
            "spread_cost",
            "fee_cost",
            "slippage_cost",
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
        reject_unsafe_surface_fields("strategy cost edge gate input", self)
        require_paper_only_flags("strategy cost edge gate input", self)


@dataclass(frozen=True)
class StrategyCostEdgeGateResult:
    candidate_id: str
    gate_status: str
    net_edge_per_share: Decimal
    total_cost_per_share: Decimal
    spread_cost: Decimal
    fee_cost: Decimal
    slippage_cost: Decimal
    cost_adjusted_edge: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        if self.gate_status not in GATE_STATUSES:
            raise ValueError("gate_status must be candidate, watch, or blocked")
        object.__setattr__(
            self,
            "net_edge_per_share",
            _normalize_decimal("net_edge_per_share", self.net_edge_per_share),
        )
        for field_name in (
            "total_cost_per_share",
            "spread_cost",
            "fee_cost",
            "slippage_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_decimal("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("strategy cost edge gate result", self)
        require_paper_only_flags("strategy cost edge gate result", self)


def evaluate_strategy_cost_edge_gate(
    edge_input: StrategyCostEdgeGateInput,
    *,
    config: StrategyCostEdgeGateConfig,
) -> StrategyCostEdgeGateResult:
    if type(edge_input) is not StrategyCostEdgeGateInput:
        raise ValueError("edge_input must be a StrategyCostEdgeGateInput")
    if type(config) is not StrategyCostEdgeGateConfig:
        raise ValueError("config must be a StrategyCostEdgeGateConfig")
    require_paper_only_flags("strategy cost edge gate input", edge_input)
    require_paper_only_flags("strategy cost edge gate config", config)

    cost_adjusted_edge = _normalize_decimal(
        "cost_adjusted_edge",
        edge_input.net_edge_per_share - edge_input.total_cost_per_share,
    )
    blocking_reasons = _blocking_reason_codes(edge_input, config, cost_adjusted_edge)

    if blocking_reasons:
        gate_status = "blocked"
        reason_codes = _append_reason_codes(
            edge_input.reason_codes,
            ("cost_edge_blocked",) + blocking_reasons,
        )
    elif cost_adjusted_edge >= config.min_candidate_cost_adjusted_edge:
        gate_status = "candidate"
        reason_codes = _append_reason_codes(
            edge_input.reason_codes,
            ("cost_edge_candidate", "cost_thresholds_passed"),
        )
    else:
        gate_status = "watch"
        reason_codes = _append_reason_codes(
            edge_input.reason_codes,
            ("cost_edge_watch", "cost_adjusted_edge_below_candidate"),
        )

    return StrategyCostEdgeGateResult(
        candidate_id=edge_input.candidate_id,
        gate_status=gate_status,
        net_edge_per_share=edge_input.net_edge_per_share,
        total_cost_per_share=edge_input.total_cost_per_share,
        spread_cost=edge_input.spread_cost,
        fee_cost=edge_input.fee_cost,
        slippage_cost=edge_input.slippage_cost,
        cost_adjusted_edge=cost_adjusted_edge,
        reason_codes=reason_codes,
    )


def strategy_cost_edge_gate_payload(report: StrategyCostEdgeGateResult) -> dict[str, Any]:
    if type(report) is not StrategyCostEdgeGateResult:
        raise ValueError("report must be a StrategyCostEdgeGateResult")
    require_paper_only_flags("strategy cost edge gate result", report)
    reject_unsafe_surface_fields("strategy cost edge gate result", report)
    return json_ready_no_floats(report)


def _blocking_reason_codes(
    edge_input: StrategyCostEdgeGateInput,
    config: StrategyCostEdgeGateConfig,
    cost_adjusted_edge: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if edge_input.total_cost_per_share > config.max_total_cost_per_share:
        reason_codes.append("total_cost_above_limit")
    if edge_input.spread_cost > config.max_spread_cost:
        reason_codes.append("spread_cost_above_limit")
    if edge_input.fee_cost > config.max_fee_cost:
        reason_codes.append("fee_cost_above_limit")
    if edge_input.slippage_cost > config.max_slippage_cost:
        reason_codes.append("slippage_cost_above_limit")
    if edge_input.total_cost_per_share != _component_cost_total(edge_input):
        reason_codes.append("cost_component_total_mismatch")
    if cost_adjusted_edge < config.min_watch_cost_adjusted_edge:
        reason_codes.append("cost_adjusted_edge_below_watch")
    if cost_adjusted_edge < ZERO:
        reason_codes.append("cost_drag_exceeds_edge")
    return tuple(reason_codes)


def _component_cost_total(edge_input: StrategyCostEdgeGateInput) -> Decimal:
    return _normalize_decimal(
        "component_cost_total",
        edge_input.spread_cost + edge_input.fee_cost + edge_input.slippage_cost,
    )


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _normalize_reason_codes(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    return value


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
    "DEFAULT_STRATEGY_COST_EDGE_GATE_CONFIG_VERSION",
    "StrategyCostEdgeGateConfig",
    "StrategyCostEdgeGateInput",
    "StrategyCostEdgeGateResult",
    "evaluate_strategy_cost_edge_gate",
    "strategy_cost_edge_gate_payload",
)
