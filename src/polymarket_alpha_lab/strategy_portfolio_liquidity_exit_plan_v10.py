"""Pure paper/report portfolio liquidity exit planner."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_CEILING
from typing import Any

__all__ = (
    "CONFIG_VERSION",
    "PortfolioLiquidityExitPlanV10Input",
    "StrategyPortfolioLiquidityExitPlanV10Report",
    "build_strategy_portfolio_liquidity_exit_plan_v10_report",
    "strategy_portfolio_liquidity_exit_plan_v10_payload",
)


CONFIG_VERSION = "strategy-portfolio-liquidity-exit-plan-v10"

ZERO = Decimal("0")
ONE = Decimal("1")
SIZE_QUANTUM = Decimal("0.000001")
BPS_QUANTUM = Decimal("0.01")
SCORE_QUANTUM = Decimal("0.000001")
SENTINEL_SIZE_TO_DEPTH_RATIO = Decimal("999999.000000")

PRESSURE_COST_BPS_MULTIPLIER = Decimal("100")
MAX_COST_BPS_FOR_SCORE = Decimal("200")
URGENCY_WINDOW_HOURS = Decimal("72")

RATIO_SCORE_WEIGHT = Decimal("0.35")
COST_SCORE_WEIGHT = Decimal("0.20")
URGENCY_SCORE_WEIGHT = Decimal("0.25")
PRESSURE_SCORE_WEIGHT = Decimal("0.20")

STAGE_EXIT_SCORE = Decimal("0.350000")
IMMEDIATE_EXIT_SCORE = Decimal("0.800000")

RECOMMENDED_ACTIONS = ("monitor", "stage_exit", "exit_immediately")
UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
    "api_key",
    "auth",
    "broker",
    "credential",
    "execution",
    "live",
    "network",
    "order",
    "persist",
    "private_key",
    "secret",
    "trade",
    "wallet",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "api key",
    "api_key",
    "credential",
    "execution",
    "live",
    "network",
    "order",
    "persist",
    "private key",
    "private_key",
    "secret",
    "trade",
    "wallet",
)


@dataclass(frozen=True)
class PortfolioLiquidityExitPlanV10Input:
    """Decimal-only inputs for a paper/report portfolio exit-liquidity plan."""

    position_size_proxy: Decimal
    exit_depth: Decimal
    spread_bps: Decimal
    expected_slippage_bps: Decimal
    hours_to_resolution: Decimal
    correlated_exit_pressure: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "position_size_proxy",
            _quantize_nonnegative_size(
                "position_size_proxy",
                self.position_size_proxy,
            ),
        )
        object.__setattr__(
            self,
            "exit_depth",
            _quantize_nonnegative_size("exit_depth", self.exit_depth),
        )
        object.__setattr__(
            self,
            "spread_bps",
            _quantize_nonnegative_bps("spread_bps", self.spread_bps),
        )
        object.__setattr__(
            self,
            "expected_slippage_bps",
            _quantize_nonnegative_bps(
                "expected_slippage_bps",
                self.expected_slippage_bps,
            ),
        )
        object.__setattr__(
            self,
            "hours_to_resolution",
            _quantize_nonnegative_size(
                "hours_to_resolution",
                self.hours_to_resolution,
            ),
        )
        object.__setattr__(
            self,
            "correlated_exit_pressure",
            _quantize_probability(
                "correlated_exit_pressure",
                self.correlated_exit_pressure,
            ),
        )


@dataclass(frozen=True)
class StrategyPortfolioLiquidityExitPlanV10Report:
    """Paper-only exit-liquidity recommendation with no execution side effects."""

    generated_at: datetime
    config_version: str
    position_size_proxy: Decimal
    exit_depth: Decimal
    spread_bps: Decimal
    expected_slippage_bps: Decimal
    hours_to_resolution: Decimal
    correlated_exit_pressure: Decimal
    pressure_adjusted_exit_depth: Decimal
    pressure_adjusted_size_to_depth_ratio: Decimal
    estimated_exit_cost_bps: Decimal
    liquidity_stress_score: Decimal
    recommended_action: str
    recommended_exit_fraction: Decimal
    planned_exit_size_proxy: Decimal
    exit_slice_count: int
    max_slice_size_proxy: Decimal
    min_hours_between_slices: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must match strategy version")
        for field_name in (
            "position_size_proxy",
            "exit_depth",
            "hours_to_resolution",
            "pressure_adjusted_exit_depth",
            "planned_exit_size_proxy",
            "max_slice_size_proxy",
            "min_hours_between_slices",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_nonnegative_size(field_name, getattr(self, field_name)),
            )
        for field_name in ("spread_bps", "expected_slippage_bps", "estimated_exit_cost_bps"):
            object.__setattr__(
                self,
                field_name,
                _quantize_nonnegative_bps(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "correlated_exit_pressure",
            "recommended_exit_fraction",
            "liquidity_stress_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "pressure_adjusted_size_to_depth_ratio",
            _quantize_nonnegative_size(
                "pressure_adjusted_size_to_depth_ratio",
                self.pressure_adjusted_size_to_depth_ratio,
            ),
        )
        _require_recommended_action(self.recommended_action)
        _require_nonnegative_int("exit_slice_count", self.exit_slice_count)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_portfolio_liquidity_exit_plan_v10_payload(self)


def build_strategy_portfolio_liquidity_exit_plan_v10_report(
    scenario: PortfolioLiquidityExitPlanV10Input,
    *,
    generated_at: datetime,
) -> StrategyPortfolioLiquidityExitPlanV10Report:
    """Build a deterministic paper/report exit-liquidity plan."""

    if type(scenario) is not PortfolioLiquidityExitPlanV10Input:
        raise ValueError("scenario must be a PortfolioLiquidityExitPlanV10Input")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    pressure_adjusted_depth = _pressure_adjusted_exit_depth(scenario)
    size_to_depth_ratio = _pressure_adjusted_size_to_depth_ratio(
        scenario.position_size_proxy,
        pressure_adjusted_depth,
    )
    estimated_cost_bps = _estimated_exit_cost_bps(scenario)
    stress_score = _liquidity_stress_score(
        size_to_depth_ratio=size_to_depth_ratio,
        estimated_exit_cost_bps=estimated_cost_bps,
        hours_to_resolution=scenario.hours_to_resolution,
        correlated_exit_pressure=scenario.correlated_exit_pressure,
    )
    action = _recommended_action(
        scenario=scenario,
        pressure_adjusted_depth=pressure_adjusted_depth,
        size_to_depth_ratio=size_to_depth_ratio,
        estimated_exit_cost_bps=estimated_cost_bps,
        liquidity_stress_score=stress_score,
    )
    exit_fraction = _recommended_exit_fraction(
        recommended_action=action,
        size_to_depth_ratio=size_to_depth_ratio,
        estimated_exit_cost_bps=estimated_cost_bps,
        hours_to_resolution=scenario.hours_to_resolution,
        correlated_exit_pressure=scenario.correlated_exit_pressure,
    )
    planned_exit_size = _quantize_size(scenario.position_size_proxy * exit_fraction)
    slice_count = _exit_slice_count(
        recommended_action=action,
        planned_exit_size_proxy=planned_exit_size,
        pressure_adjusted_exit_depth=pressure_adjusted_depth,
    )

    return StrategyPortfolioLiquidityExitPlanV10Report(
        generated_at=generated_at,
        config_version=CONFIG_VERSION,
        position_size_proxy=scenario.position_size_proxy,
        exit_depth=scenario.exit_depth,
        spread_bps=scenario.spread_bps,
        expected_slippage_bps=scenario.expected_slippage_bps,
        hours_to_resolution=scenario.hours_to_resolution,
        correlated_exit_pressure=scenario.correlated_exit_pressure,
        pressure_adjusted_exit_depth=pressure_adjusted_depth,
        pressure_adjusted_size_to_depth_ratio=size_to_depth_ratio,
        estimated_exit_cost_bps=estimated_cost_bps,
        liquidity_stress_score=stress_score,
        recommended_action=action,
        recommended_exit_fraction=exit_fraction,
        planned_exit_size_proxy=planned_exit_size,
        exit_slice_count=slice_count,
        max_slice_size_proxy=_max_slice_size(planned_exit_size, slice_count),
        min_hours_between_slices=_min_hours_between_slices(
            scenario.hours_to_resolution,
            slice_count,
        ),
        reason_codes=_reason_codes(
            scenario=scenario,
            pressure_adjusted_depth=pressure_adjusted_depth,
            size_to_depth_ratio=size_to_depth_ratio,
            estimated_exit_cost_bps=estimated_cost_bps,
        ),
    )


def strategy_portfolio_liquidity_exit_plan_v10_payload(
    report: StrategyPortfolioLiquidityExitPlanV10Report | dict[str, Any],
) -> dict[str, Any]:
    """Return a JSON-ready, public-safe, paper/report-only payload."""

    if type(report) is StrategyPortfolioLiquidityExitPlanV10Report:
        _require_hard_flags(report)
        payload = _report_payload(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a StrategyPortfolioLiquidityExitPlanV10Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags(_DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _report_payload(report: StrategyPortfolioLiquidityExitPlanV10Report) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "position_size_proxy": _decimal_payload(report.position_size_proxy),
        "exit_depth": _decimal_payload(report.exit_depth),
        "spread_bps": _decimal_payload(report.spread_bps),
        "expected_slippage_bps": _decimal_payload(report.expected_slippage_bps),
        "hours_to_resolution": _decimal_payload(report.hours_to_resolution),
        "correlated_exit_pressure": _decimal_payload(report.correlated_exit_pressure),
        "pressure_adjusted_exit_depth": _decimal_payload(
            report.pressure_adjusted_exit_depth,
        ),
        "pressure_adjusted_size_to_depth_ratio": _decimal_payload(
            report.pressure_adjusted_size_to_depth_ratio,
        ),
        "estimated_exit_cost_bps": _decimal_payload(report.estimated_exit_cost_bps),
        "liquidity_stress_score": _decimal_payload(report.liquidity_stress_score),
        "recommended_action": report.recommended_action,
        "recommended_exit_fraction": _decimal_payload(
            report.recommended_exit_fraction,
        ),
        "planned_exit_size_proxy": _decimal_payload(report.planned_exit_size_proxy),
        "exit_slice_count": str(report.exit_slice_count),
        "max_slice_size_proxy": _decimal_payload(report.max_slice_size_proxy),
        "min_hours_between_slices": _decimal_payload(report.min_hours_between_slices),
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _pressure_adjusted_exit_depth(
    scenario: PortfolioLiquidityExitPlanV10Input,
) -> Decimal:
    return _quantize_size(scenario.exit_depth * (ONE - scenario.correlated_exit_pressure))


def _pressure_adjusted_size_to_depth_ratio(
    position_size_proxy: Decimal,
    pressure_adjusted_exit_depth: Decimal,
) -> Decimal:
    if position_size_proxy == ZERO:
        return _quantize_size(ZERO)
    if pressure_adjusted_exit_depth == ZERO:
        return SENTINEL_SIZE_TO_DEPTH_RATIO
    return _quantize_size(position_size_proxy / pressure_adjusted_exit_depth)


def _estimated_exit_cost_bps(
    scenario: PortfolioLiquidityExitPlanV10Input,
) -> Decimal:
    pressure_premium_bps = (
        scenario.correlated_exit_pressure * PRESSURE_COST_BPS_MULTIPLIER
    )
    return _quantize_bps(
        scenario.spread_bps + scenario.expected_slippage_bps + pressure_premium_bps,
    )


def _liquidity_stress_score(
    *,
    size_to_depth_ratio: Decimal,
    estimated_exit_cost_bps: Decimal,
    hours_to_resolution: Decimal,
    correlated_exit_pressure: Decimal,
) -> Decimal:
    ratio_score = _min_decimal(size_to_depth_ratio, ONE)
    cost_score = _min_decimal(estimated_exit_cost_bps / MAX_COST_BPS_FOR_SCORE, ONE)
    urgency_score = _resolution_urgency_score(hours_to_resolution)
    score = (
        (ratio_score * RATIO_SCORE_WEIGHT)
        + (cost_score * COST_SCORE_WEIGHT)
        + (urgency_score * URGENCY_SCORE_WEIGHT)
        + (correlated_exit_pressure * PRESSURE_SCORE_WEIGHT)
    )
    return _quantize_score(_min_decimal(score, ONE))


def _resolution_urgency_score(hours_to_resolution: Decimal) -> Decimal:
    if hours_to_resolution >= URGENCY_WINDOW_HOURS:
        return ZERO
    if hours_to_resolution == ZERO:
        return ONE
    return _min_decimal(
        (URGENCY_WINDOW_HOURS - hours_to_resolution) / URGENCY_WINDOW_HOURS,
        ONE,
    )


def _recommended_action(
    *,
    scenario: PortfolioLiquidityExitPlanV10Input,
    pressure_adjusted_depth: Decimal,
    size_to_depth_ratio: Decimal,
    estimated_exit_cost_bps: Decimal,
    liquidity_stress_score: Decimal,
) -> str:
    if scenario.position_size_proxy == ZERO:
        return "monitor"
    if pressure_adjusted_depth == ZERO:
        return "exit_immediately"
    if liquidity_stress_score >= IMMEDIATE_EXIT_SCORE:
        return "exit_immediately"
    if size_to_depth_ratio >= Decimal("3.000000"):
        return "exit_immediately"
    if scenario.hours_to_resolution <= Decimal("6") and (
        size_to_depth_ratio >= ONE or estimated_exit_cost_bps >= Decimal("100")
    ):
        return "exit_immediately"
    if liquidity_stress_score >= STAGE_EXIT_SCORE:
        return "stage_exit"
    if size_to_depth_ratio >= Decimal("0.500000"):
        return "stage_exit"
    if estimated_exit_cost_bps >= Decimal("75"):
        return "stage_exit"
    if scenario.hours_to_resolution <= Decimal("48"):
        return "stage_exit"
    if scenario.correlated_exit_pressure >= Decimal("0.200000"):
        return "stage_exit"
    return "monitor"


def _recommended_exit_fraction(
    *,
    recommended_action: str,
    size_to_depth_ratio: Decimal,
    estimated_exit_cost_bps: Decimal,
    hours_to_resolution: Decimal,
    correlated_exit_pressure: Decimal,
) -> Decimal:
    if recommended_action == "monitor":
        return _quantize_score(ZERO)
    if recommended_action == "exit_immediately":
        return _quantize_score(ONE)

    fraction = Decimal("0.250000")
    if size_to_depth_ratio >= Decimal("0.750000"):
        fraction = Decimal("0.500000")
    if size_to_depth_ratio >= Decimal("1.250000"):
        fraction = Decimal("0.750000")
    if size_to_depth_ratio >= Decimal("2.000000"):
        fraction = ONE
    if estimated_exit_cost_bps >= Decimal("125"):
        fraction = _max_decimal(fraction, Decimal("0.750000"))
    if hours_to_resolution <= Decimal("12"):
        fraction = _max_decimal(fraction, Decimal("0.750000"))
    if correlated_exit_pressure >= Decimal("0.750000"):
        fraction = _max_decimal(fraction, Decimal("0.750000"))
    return _quantize_score(fraction)


def _exit_slice_count(
    *,
    recommended_action: str,
    planned_exit_size_proxy: Decimal,
    pressure_adjusted_exit_depth: Decimal,
) -> int:
    if planned_exit_size_proxy == ZERO:
        return 0
    if recommended_action == "exit_immediately":
        return 1
    target_slice_size = pressure_adjusted_exit_depth * Decimal("0.200000")
    if target_slice_size <= ZERO:
        return 1
    return max(
        1,
        min(
            24,
            int(
                (planned_exit_size_proxy / target_slice_size).to_integral_value(
                    rounding=ROUND_CEILING,
                ),
            ),
        ),
    )


def _max_slice_size(planned_exit_size_proxy: Decimal, exit_slice_count: int) -> Decimal:
    if exit_slice_count == 0:
        return _quantize_size(ZERO)
    return _quantize_size(planned_exit_size_proxy / Decimal(exit_slice_count))


def _min_hours_between_slices(
    hours_to_resolution: Decimal,
    exit_slice_count: int,
) -> Decimal:
    if exit_slice_count == 0:
        return _quantize_size(ZERO)
    return _quantize_size(hours_to_resolution / Decimal(exit_slice_count))


def _reason_codes(
    *,
    scenario: PortfolioLiquidityExitPlanV10Input,
    pressure_adjusted_depth: Decimal,
    size_to_depth_ratio: Decimal,
    estimated_exit_cost_bps: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if scenario.position_size_proxy == ZERO:
        reasons.append("no_position_size_proxy")
    if scenario.position_size_proxy > ZERO and pressure_adjusted_depth == ZERO:
        reasons.append("exit_depth_unavailable")
    if size_to_depth_ratio > ONE:
        reasons.append("position_exceeds_pressure_adjusted_depth")
    elif size_to_depth_ratio >= Decimal("0.500000"):
        reasons.append("position_depth_ratio_elevated")
    if estimated_exit_cost_bps >= Decimal("75"):
        reasons.append("exit_cost_elevated")
    if scenario.hours_to_resolution <= Decimal("24"):
        reasons.append("resolution_window_short")
    elif scenario.hours_to_resolution <= URGENCY_WINDOW_HOURS:
        reasons.append("resolution_window_compressed")
    if scenario.correlated_exit_pressure >= Decimal("0.750000"):
        reasons.append("correlated_exit_pressure_high")
    elif scenario.correlated_exit_pressure >= Decimal("0.200000"):
        reasons.append("correlated_exit_pressure_elevated")
    if not reasons:
        reasons.append("exit_liquidity_monitor")
    return tuple(reasons)


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_exact_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _quantize_size(value: Decimal) -> Decimal:
    return value.quantize(SIZE_QUANTUM)


def _quantize_bps(value: Decimal) -> Decimal:
    return value.quantize(BPS_QUANTUM)


def _quantize_score(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANTUM)


def _quantize_nonnegative_size(field_name: str, value: Decimal) -> Decimal:
    _require_exact_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_size(value)


def _quantize_nonnegative_bps(field_name: str, value: Decimal) -> Decimal:
    _require_exact_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_bps(value)


def _quantize_probability(field_name: str, value: Decimal) -> Decimal:
    _require_exact_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_score(value)


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_recommended_action(value: str) -> None:
    if value not in RECOMMENDED_ACTIONS:
        raise ValueError("recommended_action must be a recognized action")


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    normalized: list[str] = []
    for code in codes:
        if type(code) is not str or not code:
            raise ValueError(f"{field_name} items must be nonempty strings")
        if code != code.strip() or code.lower() != code or " " in code:
            raise ValueError(f"{field_name} items must be canonical reason codes")
        if code not in normalized:
            normalized.append(code)
    return tuple(normalized)


def _require_hard_flags(report: StrategyPortfolioLiquidityExitPlanV10Report) -> None:
    if getattr(report, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(report, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(report, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _validate_report(report: StrategyPortfolioLiquidityExitPlanV10Report) -> None:
    scenario = PortfolioLiquidityExitPlanV10Input(
        position_size_proxy=report.position_size_proxy,
        exit_depth=report.exit_depth,
        spread_bps=report.spread_bps,
        expected_slippage_bps=report.expected_slippage_bps,
        hours_to_resolution=report.hours_to_resolution,
        correlated_exit_pressure=report.correlated_exit_pressure,
    )
    expected_pressure_adjusted_depth = _pressure_adjusted_exit_depth(scenario)
    if report.pressure_adjusted_exit_depth != expected_pressure_adjusted_depth:
        raise ValueError("pressure_adjusted_exit_depth must match inputs")
    expected_size_to_depth_ratio = _pressure_adjusted_size_to_depth_ratio(
        report.position_size_proxy,
        expected_pressure_adjusted_depth,
    )
    if report.pressure_adjusted_size_to_depth_ratio != expected_size_to_depth_ratio:
        raise ValueError("pressure_adjusted_size_to_depth_ratio must match inputs")
    expected_estimated_cost_bps = _estimated_exit_cost_bps(scenario)
    if report.estimated_exit_cost_bps != expected_estimated_cost_bps:
        raise ValueError("estimated_exit_cost_bps must match inputs")
    expected_stress_score = _liquidity_stress_score(
        size_to_depth_ratio=expected_size_to_depth_ratio,
        estimated_exit_cost_bps=expected_estimated_cost_bps,
        hours_to_resolution=report.hours_to_resolution,
        correlated_exit_pressure=report.correlated_exit_pressure,
    )
    if report.liquidity_stress_score != expected_stress_score:
        raise ValueError("liquidity_stress_score must match inputs")
    expected_action = _recommended_action(
        scenario=scenario,
        pressure_adjusted_depth=expected_pressure_adjusted_depth,
        size_to_depth_ratio=expected_size_to_depth_ratio,
        estimated_exit_cost_bps=expected_estimated_cost_bps,
        liquidity_stress_score=expected_stress_score,
    )
    if report.recommended_action != expected_action:
        raise ValueError("recommended_action must match inputs")
    expected_exit_fraction = _recommended_exit_fraction(
        recommended_action=expected_action,
        size_to_depth_ratio=expected_size_to_depth_ratio,
        estimated_exit_cost_bps=expected_estimated_cost_bps,
        hours_to_resolution=report.hours_to_resolution,
        correlated_exit_pressure=report.correlated_exit_pressure,
    )
    if report.recommended_exit_fraction != expected_exit_fraction:
        raise ValueError("recommended_exit_fraction must match inputs")
    expected_planned_size = _quantize_size(
        report.position_size_proxy * expected_exit_fraction,
    )
    if report.planned_exit_size_proxy != expected_planned_size:
        raise ValueError("planned_exit_size_proxy must match recommended_exit_fraction")
    expected_slice_count = _exit_slice_count(
        recommended_action=expected_action,
        planned_exit_size_proxy=expected_planned_size,
        pressure_adjusted_exit_depth=expected_pressure_adjusted_depth,
    )
    if report.exit_slice_count != expected_slice_count:
        raise ValueError("exit_slice_count must match inputs")
    expected_max_slice_size = _max_slice_size(
        expected_planned_size,
        expected_slice_count,
    )
    if report.max_slice_size_proxy != expected_max_slice_size:
        raise ValueError("max_slice_size_proxy must match inputs")
    expected_min_hours_between_slices = _min_hours_between_slices(
        report.hours_to_resolution,
        expected_slice_count,
    )
    if report.min_hours_between_slices != expected_min_hours_between_slices:
        raise ValueError("min_hours_between_slices must match inputs")
    expected_reason_codes = _reason_codes(
        scenario=scenario,
        pressure_adjusted_depth=expected_pressure_adjusted_depth,
        size_to_depth_ratio=expected_size_to_depth_ratio,
        estimated_exit_cost_bps=expected_estimated_cost_bps,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match inputs")
    if report.recommended_action == "monitor":
        if report.recommended_exit_fraction != ZERO.quantize(SCORE_QUANTUM):
            raise ValueError("monitor recommendations must not plan an exit")
        if report.planned_exit_size_proxy != ZERO.quantize(SIZE_QUANTUM):
            raise ValueError("monitor recommendations must have zero planned exit size")
        if report.exit_slice_count != 0:
            raise ValueError("monitor recommendations must have zero exit slices")
    else:
        if report.position_size_proxy == ZERO:
            raise ValueError("exit recommendations require positive position_size_proxy")
        if report.recommended_exit_fraction == ZERO:
            raise ValueError("exit recommendations require positive exit fraction")
        if report.planned_exit_size_proxy == ZERO:
            raise ValueError("exit recommendations require positive planned exit size")
        if report.exit_slice_count == 0:
            raise ValueError("exit recommendations require at least one exit slice")
    if report.planned_exit_size_proxy > report.position_size_proxy:
        raise ValueError("planned_exit_size_proxy cannot exceed position_size_proxy")
    if not report.reason_codes:
        raise ValueError("reason_codes must not be empty")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return _decimal_payload(value)
    if type(value) is datetime:
        return _as_utc(value).isoformat()
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("payload numeric values must be rendered as strings")
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    raise ValueError("payload contains an unsupported value")


def _decimal_payload(value: Decimal) -> str:
    _require_exact_decimal("payload", value)
    if not value.is_finite():
        raise ValueError("payload Decimal value must be finite")
    return format(value, "f")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key, UNSAFE_PUBLIC_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if type(value) is list or type(value) is tuple:
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value, UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError(f"unsafe live surface value in {path or label}")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        _as_utc(value)
        return
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must be rendered as a string")
    raise ValueError("payload contains an unsupported value")


def _has_unsafe_public_fragment(value: str, fragments: tuple[str, ...]) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in fragments)


def _min_decimal(left: Decimal, right: Decimal) -> Decimal:
    return left if left <= right else right


def _max_decimal(left: Decimal, right: Decimal) -> Decimal:
    return left if left >= right else right
