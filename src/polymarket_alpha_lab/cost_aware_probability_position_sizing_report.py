"""Paper-only cost-aware probability position sizing report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_COST_AWARE_PROBABILITY_POSITION_SIZING_CONFIG_VERSION = (
    "cost-aware-probability-position-sizing-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
BASE_TEAM_CALIBRATION_CONFIDENCE = Decimal("0.800000")
RISK_BANDS = ("candidate", "watch", "blocked")


@dataclass(frozen=True)
class CostAwareProbabilityPositionSizingConfig:
    config_version: str = DEFAULT_COST_AWARE_PROBABILITY_POSITION_SIZING_CONFIG_VERSION
    candidate_fraction_cap: Decimal = Decimal("0.080000")
    watch_fraction_cap: Decimal = Decimal("0.030000")
    min_candidate_edge_to_threshold: Decimal = Decimal("0.040000")
    min_watch_edge_to_threshold: Decimal = Decimal("0.010000")
    min_liquidity_depth: Decimal = Decimal("1000.000000")
    max_spread: Decimal = Decimal("0.030000")
    min_settlement_risk_headroom: Decimal = Decimal("0.200000")
    min_team_calibration_confidence: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_fraction_cap",
            "watch_fraction_cap",
            "min_candidate_edge_to_threshold",
            "min_watch_edge_to_threshold",
            "min_liquidity_depth",
            "max_spread",
            "min_settlement_risk_headroom",
            "min_team_calibration_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_fraction_cap > self.candidate_fraction_cap:
            raise ValueError("watch_fraction_cap must not exceed candidate_fraction_cap")
        if self.min_watch_edge_to_threshold > self.min_candidate_edge_to_threshold:
            raise ValueError(
                "min_watch_edge_to_threshold must not exceed "
                "min_candidate_edge_to_threshold",
            )
        reject_unsafe_surface_fields("cost-aware probability sizing config", self)
        require_paper_only_flags("cost-aware probability sizing config", self)


@dataclass(frozen=True)
class CostAwareProbabilityPositionSizingInput:
    market_id: str
    forecast_yes_probability: Decimal
    market_probability: Decimal
    cost_adjusted_threshold: Decimal
    edge_to_threshold: Decimal
    liquidity_depth: Decimal
    spread: Decimal
    settlement_risk_headroom: Decimal
    team_calibration_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in (
            "forecast_yes_probability",
            "market_probability",
            "cost_adjusted_threshold",
            "spread",
            "settlement_risk_headroom",
            "team_calibration_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_to_threshold",
            _normalize_decimal("edge_to_threshold", self.edge_to_threshold),
        )
        object.__setattr__(
            self,
            "liquidity_depth",
            _normalize_nonnegative_decimal("liquidity_depth", self.liquidity_depth),
        )
        reject_unsafe_surface_fields("cost-aware probability sizing input", self)
        require_paper_only_flags("cost-aware probability sizing input", self)


@dataclass(frozen=True)
class CostAwareProbabilityPositionSizingReport:
    market_id: str
    forecast_yes_probability: Decimal
    market_probability: Decimal
    cost_adjusted_threshold: Decimal
    raw_probability_edge: Decimal
    edge_to_threshold: Decimal
    liquidity_depth: Decimal
    spread: Decimal
    settlement_risk_headroom: Decimal
    team_calibration_confidence: Decimal
    max_position_fraction: Decimal
    risk_band: str
    blocker_reasons: tuple[str, ...]
    attention_reasons: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in (
            "forecast_yes_probability",
            "market_probability",
            "cost_adjusted_threshold",
            "spread",
            "settlement_risk_headroom",
            "team_calibration_confidence",
            "max_position_fraction",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("raw_probability_edge", "edge_to_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_depth",
            _normalize_nonnegative_decimal("liquidity_depth", self.liquidity_depth),
        )
        if self.risk_band not in RISK_BANDS:
            raise ValueError("risk_band must be candidate, watch, or blocked")
        object.__setattr__(
            self,
            "blocker_reasons",
            _normalize_reason_codes("blocker_reasons", self.blocker_reasons),
        )
        object.__setattr__(
            self,
            "attention_reasons",
            _normalize_reason_codes("attention_reasons", self.attention_reasons),
        )
        if self.risk_band == "blocked" and self.max_position_fraction != ZERO:
            raise ValueError("blocked reports must have zero max_position_fraction")
        if self.risk_band != "blocked" and self.blocker_reasons:
            raise ValueError("non-blocked reports must not include blocker_reasons")
        reject_unsafe_surface_fields("cost-aware probability sizing report", self)
        require_paper_only_flags("cost-aware probability sizing report", self)


def build_cost_aware_probability_position_sizing_report(
    sizing_input: CostAwareProbabilityPositionSizingInput,
    *,
    config: CostAwareProbabilityPositionSizingConfig,
) -> CostAwareProbabilityPositionSizingReport:
    if type(sizing_input) is not CostAwareProbabilityPositionSizingInput:
        raise ValueError(
            "sizing_input must be a CostAwareProbabilityPositionSizingInput",
        )
    if type(config) is not CostAwareProbabilityPositionSizingConfig:
        raise ValueError(
            "config must be a CostAwareProbabilityPositionSizingConfig",
        )
    require_paper_only_flags("cost-aware probability sizing input", sizing_input)
    require_paper_only_flags("cost-aware probability sizing config", config)

    raw_probability_edge = _normalize_decimal(
        "raw_probability_edge",
        sizing_input.forecast_yes_probability - sizing_input.market_probability,
    )
    blocker_reasons = _blocking_reason_codes(sizing_input, config)
    if blocker_reasons:
        risk_band = "blocked"
        max_position_fraction = ZERO
        attention_reasons: tuple[str, ...] = ()
    else:
        risk_band = _risk_band(sizing_input, config)
        max_position_fraction = _max_position_fraction(sizing_input, config, risk_band)
        attention_reasons = _attention_reason_codes(sizing_input, config, risk_band)

    return CostAwareProbabilityPositionSizingReport(
        market_id=sizing_input.market_id,
        forecast_yes_probability=sizing_input.forecast_yes_probability,
        market_probability=sizing_input.market_probability,
        cost_adjusted_threshold=sizing_input.cost_adjusted_threshold,
        raw_probability_edge=raw_probability_edge,
        edge_to_threshold=sizing_input.edge_to_threshold,
        liquidity_depth=sizing_input.liquidity_depth,
        spread=sizing_input.spread,
        settlement_risk_headroom=sizing_input.settlement_risk_headroom,
        team_calibration_confidence=sizing_input.team_calibration_confidence,
        max_position_fraction=max_position_fraction,
        risk_band=risk_band,
        blocker_reasons=blocker_reasons,
        attention_reasons=attention_reasons,
    )


def cost_aware_probability_position_sizing_payload(
    report: CostAwareProbabilityPositionSizingReport,
) -> dict[str, Any]:
    if type(report) is not CostAwareProbabilityPositionSizingReport:
        raise ValueError("report must be a CostAwareProbabilityPositionSizingReport")
    require_paper_only_flags("cost-aware probability sizing report", report)
    reject_unsafe_surface_fields("cost-aware probability sizing report", report)
    return json_ready_no_floats(report)


def _blocking_reason_codes(
    sizing_input: CostAwareProbabilityPositionSizingInput,
    config: CostAwareProbabilityPositionSizingConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if sizing_input.forecast_yes_probability < sizing_input.cost_adjusted_threshold:
        reason_codes.append("forecast_below_cost_adjusted_threshold")
    if sizing_input.edge_to_threshold < config.min_watch_edge_to_threshold:
        reason_codes.append("edge_to_threshold_below_watch")
    if sizing_input.liquidity_depth < config.min_liquidity_depth:
        reason_codes.append("insufficient_liquidity_depth")
    if sizing_input.spread > config.max_spread:
        reason_codes.append("spread_above_limit")
    if sizing_input.settlement_risk_headroom < config.min_settlement_risk_headroom:
        reason_codes.append("settlement_risk_headroom_below_minimum")
    if sizing_input.team_calibration_confidence < config.min_team_calibration_confidence:
        reason_codes.append("team_calibration_confidence_below_minimum")
    return tuple(reason_codes)


def _attention_reason_codes(
    sizing_input: CostAwareProbabilityPositionSizingInput,
    config: CostAwareProbabilityPositionSizingConfig,
    risk_band: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if risk_band == "watch":
        reason_codes.append("edge_to_threshold_below_candidate")
    if sizing_input.spread > ZERO:
        reason_codes.append("spread_present")
    return _dedupe_reason_codes(tuple(reason_codes))


def _risk_band(
    sizing_input: CostAwareProbabilityPositionSizingInput,
    config: CostAwareProbabilityPositionSizingConfig,
) -> str:
    if sizing_input.edge_to_threshold >= config.min_candidate_edge_to_threshold:
        return "candidate"
    return "watch"


def _max_position_fraction(
    sizing_input: CostAwareProbabilityPositionSizingInput,
    config: CostAwareProbabilityPositionSizingConfig,
    risk_band: str,
) -> Decimal:
    cap = config.candidate_fraction_cap
    if risk_band == "watch":
        cap = config.watch_fraction_cap
    confidence_adjusted_edge = (
        sizing_input.edge_to_threshold
        * sizing_input.team_calibration_confidence
        / BASE_TEAM_CALIBRATION_CONFIDENCE
    )
    if confidence_adjusted_edge < ZERO:
        confidence_adjusted_edge = ZERO
    capped_fraction = min(cap, confidence_adjusted_edge)
    return _normalize_probability(
        "max_position_fraction",
        capped_fraction,
    )


def _dedupe_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    values: list[str] = []
    for reason_code in reason_codes:
        if reason_code not in values:
            values.append(reason_code)
    return tuple(values)


def _normalize_reason_codes(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    return value


def _normalize_probability(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_nonnegative_decimal(field_name, value)
    if decimal > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
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
    "DEFAULT_COST_AWARE_PROBABILITY_POSITION_SIZING_CONFIG_VERSION",
    "CostAwareProbabilityPositionSizingConfig",
    "CostAwareProbabilityPositionSizingInput",
    "CostAwareProbabilityPositionSizingReport",
    "build_cost_aware_probability_position_sizing_report",
    "cost_aware_probability_position_sizing_payload",
)
