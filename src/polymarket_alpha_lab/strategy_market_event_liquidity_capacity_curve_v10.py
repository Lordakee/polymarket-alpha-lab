"""Paper-only readonly market event liquidity capacity curve."""

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
BASE_CAPACITY_UNITS = Decimal("100.000000")
MANUAL_REVIEW_MULTIPLIER = Decimal("2.400000")
CAPACITY_CEILING_MULTIPLIER = Decimal("4.000000")
THIN_DEPTH_THRESHOLD = Decimal("0.300000")
LOW_DAILY_VOLUME_THRESHOLD = Decimal("0.400000")
EDGE_BUFFER_WATCH_BPS = Decimal("40.000000")
NEAR_RESOLUTION_MINUTES = Decimal("60.000000")
MEDIUM_RESOLUTION_MINUTES = Decimal("1440.000000")
LOW_TIME_HAIRCUT = Decimal("0.500000")
MEDIUM_TIME_HAIRCUT = Decimal("0.750000")
HIGH_TIME_HAIRCUT = Decimal("1.000000")
CAPACITY_STATUSES = ("available", "watch", "blocked")
CAPACITY_TIER_NAMES = ("research_probe", "manual_review", "capacity_ceiling")


@dataclass(frozen=True)
class MarketEventLiquidityCapacityCurveInput:
    market_id: str
    depth_score: Decimal
    spread_bps: Decimal
    slippage_bps: Decimal
    daily_volume_score: Decimal
    cost_adjusted_edge_bps: Decimal
    time_to_resolution_minutes: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in ("depth_score", "daily_volume_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_bps",
            "slippage_bps",
            "time_to_resolution_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge_bps",
            _normalize_decimal("cost_adjusted_edge_bps", self.cost_adjusted_edge_bps),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("market event liquidity capacity curve input", self)
        require_paper_only_flags("market event liquidity capacity curve input", self)


@dataclass(frozen=True)
class MarketEventLiquidityCapacityTier:
    tier_name: str
    min_size: Decimal
    max_size: Decimal
    tier_status: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if self.tier_name not in CAPACITY_TIER_NAMES:
            raise ValueError("tier_name must be a known capacity tier")
        for field_name in ("min_size", "max_size"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_size < self.min_size:
            raise ValueError("max_size must be >= min_size")
        _require_capacity_status("tier_status", self.tier_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("market event liquidity capacity tier", self)
        require_paper_only_flags("market event liquidity capacity tier", self)


@dataclass(frozen=True)
class MarketEventLiquidityRecommendedManualSizeBand:
    min_size: Decimal
    max_size: Decimal
    band_status: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("min_size", "max_size"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_size < self.min_size:
            raise ValueError("max_size must be >= min_size")
        _require_capacity_status("band_status", self.band_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields(
            "market event liquidity recommended manual size band",
            self,
        )
        require_paper_only_flags(
            "market event liquidity recommended manual size band",
            self,
        )


@dataclass(frozen=True)
class MarketEventLiquidityCapacityCurveResult:
    market_id: str
    depth_score: Decimal
    spread_bps: Decimal
    slippage_bps: Decimal
    daily_volume_score: Decimal
    cost_adjusted_edge_bps: Decimal
    time_to_resolution_minutes: Decimal
    friction_bps: Decimal
    net_cost_adjusted_edge_bps: Decimal
    effective_liquidity_score: Decimal
    capacity_status: str
    capacity_tiers: tuple[MarketEventLiquidityCapacityTier, ...]
    recommended_manual_size_band: MarketEventLiquidityRecommendedManualSizeBand
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in ("depth_score", "daily_volume_score", "effective_liquidity_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_bps",
            "slippage_bps",
            "time_to_resolution_minutes",
            "friction_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("cost_adjusted_edge_bps", "net_cost_adjusted_edge_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_capacity_status("capacity_status", self.capacity_status)
        object.__setattr__(
            self,
            "capacity_tiers",
            _normalize_capacity_tiers(self.capacity_tiers),
        )
        if type(self.recommended_manual_size_band) is not MarketEventLiquidityRecommendedManualSizeBand:
            raise ValueError(
                "recommended_manual_size_band must be a "
                "MarketEventLiquidityRecommendedManualSizeBand",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("market event liquidity capacity curve result", self)
        require_paper_only_flags("market event liquidity capacity curve result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return market_event_liquidity_capacity_curve_payload(self)


def estimate_market_event_liquidity_capacity_curve(
    curve_input: MarketEventLiquidityCapacityCurveInput,
) -> MarketEventLiquidityCapacityCurveResult:
    if type(curve_input) is not MarketEventLiquidityCapacityCurveInput:
        raise ValueError("curve_input must be a MarketEventLiquidityCapacityCurveInput")
    require_paper_only_flags("market event liquidity capacity curve input", curve_input)
    reject_unsafe_surface_fields("market event liquidity capacity curve input", curve_input)

    time_haircut, time_reason_code = _time_haircut(
        curve_input.time_to_resolution_minutes,
    )
    friction_bps = _normalize_nonnegative_decimal(
        "friction_bps",
        curve_input.spread_bps + curve_input.slippage_bps,
    )
    net_cost_adjusted_edge_bps = _normalize_decimal(
        "net_cost_adjusted_edge_bps",
        curve_input.cost_adjusted_edge_bps - friction_bps,
    )
    effective_liquidity_score = _normalize_ratio(
        "effective_liquidity_score",
        curve_input.depth_score * curve_input.daily_volume_score * time_haircut,
    )
    base_capacity = _normalize_nonnegative_decimal(
        "base_capacity",
        effective_liquidity_score * BASE_CAPACITY_UNITS,
    )
    capacity_status = _capacity_status(curve_input, net_cost_adjusted_edge_bps)
    capacity_tiers = _capacity_tiers(base_capacity, capacity_status)
    recommended_manual_size_band = _recommended_manual_size_band(
        base_capacity,
        capacity_status,
    )

    return MarketEventLiquidityCapacityCurveResult(
        market_id=curve_input.market_id,
        depth_score=curve_input.depth_score,
        spread_bps=curve_input.spread_bps,
        slippage_bps=curve_input.slippage_bps,
        daily_volume_score=curve_input.daily_volume_score,
        cost_adjusted_edge_bps=curve_input.cost_adjusted_edge_bps,
        time_to_resolution_minutes=curve_input.time_to_resolution_minutes,
        friction_bps=friction_bps,
        net_cost_adjusted_edge_bps=net_cost_adjusted_edge_bps,
        effective_liquidity_score=effective_liquidity_score,
        capacity_status=capacity_status,
        capacity_tiers=capacity_tiers,
        recommended_manual_size_band=recommended_manual_size_band,
        reason_codes=_reason_codes(
            curve_input.reason_codes,
            curve_input=curve_input,
            net_cost_adjusted_edge_bps=net_cost_adjusted_edge_bps,
            capacity_status=capacity_status,
            time_reason_code=time_reason_code,
        ),
    )


def market_event_liquidity_capacity_curve_payload(
    report: MarketEventLiquidityCapacityCurveResult,
) -> dict[str, Any]:
    if type(report) is not MarketEventLiquidityCapacityCurveResult:
        raise ValueError("report must be a MarketEventLiquidityCapacityCurveResult")
    require_paper_only_flags("market event liquidity capacity curve result", report)
    reject_unsafe_surface_fields("market event liquidity capacity curve result", report)
    return json_ready_no_floats(
        {
            "market_id": report.market_id,
            "depth_score": report.depth_score,
            "spread_bps": report.spread_bps,
            "slippage_bps": report.slippage_bps,
            "daily_volume_score": report.daily_volume_score,
            "cost_adjusted_edge_bps": report.cost_adjusted_edge_bps,
            "time_to_resolution_minutes": report.time_to_resolution_minutes,
            "friction_bps": report.friction_bps,
            "net_cost_adjusted_edge_bps": report.net_cost_adjusted_edge_bps,
            "effective_liquidity_score": report.effective_liquidity_score,
            "capacity_status": report.capacity_status,
            "capacity_tiers": report.capacity_tiers,
            "recommended_manual_size_band": report.recommended_manual_size_band,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _capacity_status(
    curve_input: MarketEventLiquidityCapacityCurveInput,
    net_cost_adjusted_edge_bps: Decimal,
) -> str:
    if (
        net_cost_adjusted_edge_bps <= ZERO
        or curve_input.depth_score == ZERO
        or curve_input.daily_volume_score == ZERO
    ):
        return "blocked"
    if (
        curve_input.depth_score < THIN_DEPTH_THRESHOLD
        or curve_input.daily_volume_score < LOW_DAILY_VOLUME_THRESHOLD
        or curve_input.time_to_resolution_minutes < NEAR_RESOLUTION_MINUTES
        or net_cost_adjusted_edge_bps < EDGE_BUFFER_WATCH_BPS
    ):
        return "watch"
    return "available"


def _capacity_tiers(
    base_capacity: Decimal,
    capacity_status: str,
) -> tuple[MarketEventLiquidityCapacityTier, ...]:
    research_max = base_capacity
    manual_max = _normalize_nonnegative_decimal(
        "manual_review_max_size",
        base_capacity * MANUAL_REVIEW_MULTIPLIER,
    )
    ceiling_max = _normalize_nonnegative_decimal(
        "capacity_ceiling_max_size",
        base_capacity * CAPACITY_CEILING_MULTIPLIER,
    )

    if capacity_status == "blocked":
        return (
            _capacity_tier("research_probe", ZERO, ZERO, "blocked"),
            _capacity_tier("manual_review", ZERO, ZERO, "blocked"),
            _capacity_tier("capacity_ceiling", ZERO, ZERO, "blocked"),
        )
    if capacity_status == "watch":
        return (
            _capacity_tier("research_probe", ZERO, research_max, "watch"),
            _capacity_tier("manual_review", research_max, manual_max, "watch"),
            _capacity_tier("capacity_ceiling", manual_max, ceiling_max, "blocked"),
        )
    return (
        _capacity_tier("research_probe", ZERO, research_max, "available"),
        _capacity_tier("manual_review", research_max, manual_max, "available"),
        _capacity_tier("capacity_ceiling", manual_max, ceiling_max, "watch"),
    )


def _capacity_tier(
    tier_name: str,
    min_size: Decimal,
    max_size: Decimal,
    tier_status: str,
) -> MarketEventLiquidityCapacityTier:
    return MarketEventLiquidityCapacityTier(
        tier_name=tier_name,
        min_size=min_size,
        max_size=max_size,
        tier_status=tier_status,
        reason_codes=(f"capacity_tier_{tier_name}", f"capacity_{tier_status}"),
    )


def _recommended_manual_size_band(
    base_capacity: Decimal,
    capacity_status: str,
) -> MarketEventLiquidityRecommendedManualSizeBand:
    if capacity_status == "blocked":
        min_size = ZERO
        max_size = ZERO
    elif capacity_status == "watch":
        min_size = ZERO
        max_size = base_capacity
    else:
        min_size = base_capacity
        max_size = _normalize_nonnegative_decimal(
            "manual_review_max_size",
            base_capacity * MANUAL_REVIEW_MULTIPLIER,
        )
    return MarketEventLiquidityRecommendedManualSizeBand(
        min_size=min_size,
        max_size=max_size,
        band_status=capacity_status,
        reason_codes=("recommended_manual_size_band", f"capacity_{capacity_status}"),
    )


def _reason_codes(
    existing: tuple[str, ...],
    *,
    curve_input: MarketEventLiquidityCapacityCurveInput,
    net_cost_adjusted_edge_bps: Decimal,
    capacity_status: str,
    time_reason_code: str,
) -> tuple[str, ...]:
    additions = [
        "market_event_liquidity_capacity_curve",
        f"capacity_{capacity_status}",
    ]
    if net_cost_adjusted_edge_bps <= ZERO:
        additions.append("edge_not_cost_covering")
    if curve_input.depth_score < THIN_DEPTH_THRESHOLD:
        additions.append("thin_depth")
    if curve_input.daily_volume_score < LOW_DAILY_VOLUME_THRESHOLD:
        additions.append("low_daily_volume")
    if curve_input.time_to_resolution_minutes < NEAR_RESOLUTION_MINUTES:
        additions.append("near_resolution")
    if ZERO < net_cost_adjusted_edge_bps < EDGE_BUFFER_WATCH_BPS:
        additions.append("edge_buffer_thin")
    additions.append(time_reason_code)
    return _append_reason_codes(existing, tuple(additions))


def _time_haircut(time_to_resolution_minutes: Decimal) -> tuple[Decimal, str]:
    if time_to_resolution_minutes < NEAR_RESOLUTION_MINUTES:
        return LOW_TIME_HAIRCUT, "time_haircut_low"
    if time_to_resolution_minutes < MEDIUM_RESOLUTION_MINUTES:
        return MEDIUM_TIME_HAIRCUT, "time_haircut_medium"
    return HIGH_TIME_HAIRCUT, "time_haircut_high"


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _normalize_capacity_tiers(
    value: Any,
) -> tuple[MarketEventLiquidityCapacityTier, ...]:
    if type(value) is not tuple:
        raise ValueError("capacity_tiers must be a tuple")
    if len(value) != len(CAPACITY_TIER_NAMES):
        raise ValueError("capacity_tiers must contain all capacity tiers")
    seen: set[str] = set()
    for tier in value:
        if type(tier) is not MarketEventLiquidityCapacityTier:
            raise ValueError(
                "capacity_tiers must contain MarketEventLiquidityCapacityTier values",
            )
        require_paper_only_flags("market event liquidity capacity tier", tier)
        reject_unsafe_surface_fields("market event liquidity capacity tier", tier)
        if tier.tier_name in seen:
            raise ValueError("capacity_tiers must not contain duplicate tier_name values")
        seen.add(tier.tier_name)
    if tuple(tier.tier_name for tier in value) != CAPACITY_TIER_NAMES:
        raise ValueError("capacity_tiers must be ordered by capacity tier")
    return value


def _require_capacity_status(field_name: str, value: Any) -> None:
    if value not in CAPACITY_STATUSES:
        raise ValueError(f"{field_name} must be available, watch, or blocked")


def _normalize_reason_codes(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    return value


def _normalize_ratio(field_name: str, value: Any) -> Decimal:
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


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "MarketEventLiquidityCapacityCurveInput",
    "MarketEventLiquidityCapacityCurveResult",
    "MarketEventLiquidityCapacityTier",
    "MarketEventLiquidityRecommendedManualSizeBand",
    "estimate_market_event_liquidity_capacity_curve",
    "market_event_liquidity_capacity_curve_payload",
)
