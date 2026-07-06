"""Paper-only probability mispricing window v3."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_PROBABILITY_MISPRICING_WINDOW_V3_CONFIG_VERSION = (
    "strategy-probability-mispricing-window-v3"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WINDOW_STATUSES = ("open", "watch", "closed")
MISPRICED_SIDES = ("yes", "no", "none")


@dataclass(frozen=True)
class StrategyProbabilityMispricingWindowV3Config:
    config_version: str = DEFAULT_STRATEGY_PROBABILITY_MISPRICING_WINDOW_V3_CONFIG_VERSION
    min_open_abs_probability_gap: Decimal = Decimal("0.080000")
    min_watch_abs_probability_gap: Decimal = Decimal("0.030000")
    min_open_cost_adjusted_edge: Decimal = Decimal("0.015000")
    min_watch_cost_adjusted_edge: Decimal = Decimal("0.000000")
    min_open_liquidity: Decimal = Decimal("1000.000000")
    min_watch_liquidity: Decimal = Decimal("250.000000")
    min_open_time_to_resolution: Decimal = Decimal("3600.000000")
    min_watch_time_to_resolution: Decimal = Decimal("900.000000")
    max_open_recent_probability_velocity: Decimal = Decimal("0.050000")
    max_watch_recent_probability_velocity: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_STRATEGY_PROBABILITY_MISPRICING_WINDOW_V3_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_open_abs_probability_gap",
            "min_watch_abs_probability_gap",
            "max_open_recent_probability_velocity",
            "max_watch_recent_probability_velocity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_open_cost_adjusted_edge",
            "min_watch_cost_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_open_liquidity",
            "min_watch_liquidity",
            "min_open_time_to_resolution",
            "min_watch_time_to_resolution",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_abs_probability_gap > self.min_open_abs_probability_gap:
            raise ValueError(
                "min_watch_abs_probability_gap must not exceed "
                "min_open_abs_probability_gap",
            )
        if self.min_watch_cost_adjusted_edge > self.min_open_cost_adjusted_edge:
            raise ValueError(
                "min_watch_cost_adjusted_edge must not exceed "
                "min_open_cost_adjusted_edge",
            )
        if self.min_watch_liquidity > self.min_open_liquidity:
            raise ValueError("min_watch_liquidity must not exceed min_open_liquidity")
        if self.min_watch_time_to_resolution > self.min_open_time_to_resolution:
            raise ValueError(
                "min_watch_time_to_resolution must not exceed "
                "min_open_time_to_resolution",
            )
        if (
            self.max_open_recent_probability_velocity
            > self.max_watch_recent_probability_velocity
        ):
            raise ValueError(
                "max_open_recent_probability_velocity must not exceed "
                "max_watch_recent_probability_velocity",
            )
        reject_unsafe_surface_fields("strategy probability mispricing window v3 config", self)
        require_paper_only_flags("strategy probability mispricing window v3 config", self)


@dataclass(frozen=True)
class StrategyProbabilityMispricingWindowV3Input:
    candidate_id: str
    market_slug: str
    market_probability: Decimal
    forecast_probability: Decimal
    cost_adjusted_edge: Decimal
    liquidity: Decimal
    time_to_resolution: Decimal
    recent_probability_velocity: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in ("market_probability", "forecast_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_decimal("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        for field_name in ("liquidity", "time_to_resolution", "recent_probability_velocity"):
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
        reject_unsafe_surface_fields("strategy probability mispricing window v3 input", self)
        require_paper_only_flags("strategy probability mispricing window v3 input", self)


@dataclass(frozen=True)
class StrategyProbabilityMispricingWindowV3Result:
    candidate_id: str
    market_slug: str
    window_status: str
    mispriced_side: str
    market_probability: Decimal
    forecast_probability: Decimal
    probability_gap: Decimal
    abs_probability_gap: Decimal
    cost_adjusted_edge: Decimal
    liquidity: Decimal
    time_to_resolution: Decimal
    recent_probability_velocity: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        if self.window_status not in WINDOW_STATUSES:
            raise ValueError("window_status must be open, watch, or closed")
        if self.mispriced_side not in MISPRICED_SIDES:
            raise ValueError("mispriced_side must be yes, no, or none")
        for field_name in (
            "market_probability",
            "forecast_probability",
            "abs_probability_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("probability_gap", "cost_adjusted_edge"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("liquidity", "time_to_resolution", "recent_probability_velocity"):
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
        reject_unsafe_surface_fields("strategy probability mispricing window v3 result", self)
        require_paper_only_flags("strategy probability mispricing window v3 result", self)


def evaluate_strategy_probability_mispricing_window_v3(
    window_input: StrategyProbabilityMispricingWindowV3Input,
    *,
    config: StrategyProbabilityMispricingWindowV3Config,
) -> StrategyProbabilityMispricingWindowV3Result:
    if type(window_input) is not StrategyProbabilityMispricingWindowV3Input:
        raise ValueError("window_input must be a StrategyProbabilityMispricingWindowV3Input")
    if type(config) is not StrategyProbabilityMispricingWindowV3Config:
        raise ValueError("config must be a StrategyProbabilityMispricingWindowV3Config")
    require_paper_only_flags("strategy probability mispricing window v3 input", window_input)
    require_paper_only_flags("strategy probability mispricing window v3 config", config)

    probability_gap = _normalize_decimal(
        "probability_gap",
        window_input.forecast_probability - window_input.market_probability,
    )
    abs_probability_gap = _normalize_probability("abs_probability_gap", abs(probability_gap))
    mispriced_side = _mispriced_side(probability_gap)
    open_reasons = _open_gap_reasons(window_input, abs_probability_gap, config)
    closed_reasons = _closed_gap_reasons(window_input, abs_probability_gap, config)

    if not closed_reasons and not open_reasons:
        window_status = "open"
        reason_codes = _append_reason_codes(
            window_input.reason_codes,
            (
                "mispricing_window_open",
                "probability_gap_clears_open",
                "cost_adjusted_edge_clears_open",
                "liquidity_clears_open",
                "resolution_window_clears_open",
                "probability_velocity_stable",
            ),
        )
    elif closed_reasons:
        window_status = "closed"
        reason_codes = _append_reason_codes(
            window_input.reason_codes,
            ("mispricing_window_closed",) + closed_reasons,
        )
    else:
        window_status = "watch"
        reason_codes = _append_reason_codes(
            window_input.reason_codes,
            ("mispricing_window_watch",) + open_reasons,
        )

    return StrategyProbabilityMispricingWindowV3Result(
        candidate_id=window_input.candidate_id,
        market_slug=window_input.market_slug,
        window_status=window_status,
        mispriced_side=mispriced_side,
        market_probability=window_input.market_probability,
        forecast_probability=window_input.forecast_probability,
        probability_gap=probability_gap,
        abs_probability_gap=abs_probability_gap,
        cost_adjusted_edge=window_input.cost_adjusted_edge,
        liquidity=window_input.liquidity,
        time_to_resolution=window_input.time_to_resolution,
        recent_probability_velocity=window_input.recent_probability_velocity,
        reason_codes=reason_codes,
    )


def strategy_probability_mispricing_window_v3_payload(
    result: StrategyProbabilityMispricingWindowV3Result,
) -> dict[str, Any]:
    if type(result) is not StrategyProbabilityMispricingWindowV3Result:
        raise ValueError("result must be a StrategyProbabilityMispricingWindowV3Result")
    require_paper_only_flags("strategy probability mispricing window v3 result", result)
    reject_unsafe_surface_fields("strategy probability mispricing window v3 result", result)
    return json_ready_no_floats(result)


def _open_gap_reasons(
    window_input: StrategyProbabilityMispricingWindowV3Input,
    abs_probability_gap: Decimal,
    config: StrategyProbabilityMispricingWindowV3Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if abs_probability_gap < config.min_open_abs_probability_gap:
        reason_codes.append("probability_gap_below_open")
    if window_input.cost_adjusted_edge < config.min_open_cost_adjusted_edge:
        reason_codes.append("cost_adjusted_edge_below_open")
    if window_input.liquidity < config.min_open_liquidity:
        reason_codes.append("liquidity_below_open")
    if window_input.time_to_resolution < config.min_open_time_to_resolution:
        reason_codes.append("resolution_window_below_open")
    if window_input.recent_probability_velocity > config.max_open_recent_probability_velocity:
        reason_codes.append("probability_velocity_above_open")
    return tuple(reason_codes)


def _closed_gap_reasons(
    window_input: StrategyProbabilityMispricingWindowV3Input,
    abs_probability_gap: Decimal,
    config: StrategyProbabilityMispricingWindowV3Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if abs_probability_gap < config.min_watch_abs_probability_gap:
        reason_codes.append("probability_gap_below_watch")
    if window_input.cost_adjusted_edge < config.min_watch_cost_adjusted_edge:
        reason_codes.append("cost_adjusted_edge_below_watch")
    if window_input.liquidity < config.min_watch_liquidity:
        reason_codes.append("liquidity_below_watch")
    if window_input.time_to_resolution < config.min_watch_time_to_resolution:
        reason_codes.append("resolution_window_below_watch")
    if window_input.recent_probability_velocity > config.max_watch_recent_probability_velocity:
        reason_codes.append("probability_velocity_above_watch")
    return tuple(reason_codes)


def _mispriced_side(probability_gap: Decimal) -> str:
    if probability_gap > ZERO:
        return "yes"
    if probability_gap < ZERO:
        return "no"
    return "none"


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = list(existing)
    for addition in additions:
        if addition not in reason_codes:
            reason_codes.append(addition)
    return tuple(reason_codes)


def _normalize_reason_codes(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    return value


def _normalize_probability(field_name: str, value: Any) -> Decimal:
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
    return value.quantize(QUANTUM)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "DEFAULT_STRATEGY_PROBABILITY_MISPRICING_WINDOW_V3_CONFIG_VERSION",
    "StrategyProbabilityMispricingWindowV3Config",
    "StrategyProbabilityMispricingWindowV3Input",
    "StrategyProbabilityMispricingWindowV3Result",
    "evaluate_strategy_probability_mispricing_window_v3",
    "strategy_probability_mispricing_window_v3_payload",
)
