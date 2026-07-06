"""Pure typed strategy decision audit packet payloads."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_DECISION_AUDIT_PACKET_CONFIG_VERSION = (
    "strategy-decision-audit-packet-v0"
)
STRATEGY_DECISION_AUDIT_PACKET_STATUSES = ("ready", "watch", "blocked")
STRATEGY_DECISION_AUDIT_RECOMMENDATIONS = ("enter", "watch", "skip")
PACKET_STATUS_REASON_CODES = (
    "strategy_decision_audit_packet_ready",
    "strategy_decision_audit_packet_watch",
    "strategy_decision_audit_packet_blocked",
)
FORECAST_REASON_CODES = (
    "forecast_model_edge_positive",
    "forecast_model_edge_negative",
    "forecast_uncertainty_watch",
)
MARKET_PROBABILITY_REASON_CODES = ("market_probability_snapshot_observed",)
COST_REASON_CODES = (
    "cost_adjusted_edge_positive",
    "cost_adjusted_edge_negative",
)
SOURCE_QUALITY_REASON_CODES = (
    "source_quality_ready",
    "source_quality_watch",
    "source_quality_blocked",
)
TEAM_MEMORY_REASON_CODES = (
    "team_memory_supportive",
    "team_memory_watch",
    "team_memory_blocked",
)
RESOLUTION_RISK_REASON_CODES = (
    "resolution_risk_acceptable",
    "resolution_risk_watch",
    "resolution_risk_blocked",
)
RECOMMENDATION_REASON_CODES = (
    "recommendation_enter",
    "recommendation_watch",
    "recommendation_skip",
)
STRATEGY_DECISION_AUDIT_PACKET_REASON_CODES = (
    PACKET_STATUS_REASON_CODES
    + FORECAST_REASON_CODES
    + MARKET_PROBABILITY_REASON_CODES
    + COST_REASON_CODES
    + SOURCE_QUALITY_REASON_CODES
    + TEAM_MEMORY_REASON_CODES
    + RESOLUTION_RISK_REASON_CODES
    + RECOMMENDATION_REASON_CODES
)
SCORE_QUANT = Decimal("0.000001")
DECIMAL_ZERO = Decimal("0")
DECIMAL_ONE = Decimal("1.000000")
DECIMAL_NEGATIVE_ONE = Decimal("-1.000000")


@dataclass(frozen=True)
class StrategyDecisionAuditForecast:
    forecast_probability: Decimal
    forecast_confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "forecast_confidence",
            _normalize_probability("forecast_confidence", self.forecast_confidence),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                FORECAST_REASON_CODES,
            ),
        )
        require_paper_only_flags("StrategyDecisionAuditForecast", self)
        reject_unsafe_surface_fields("StrategyDecisionAuditForecast", self)


@dataclass(frozen=True)
class StrategyDecisionAuditMarketProbability:
    candidate_id: str
    market_slug: str
    outcome_name: str
    market_probability: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "outcome_name"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "market_probability",
            _normalize_probability("market_probability", self.market_probability),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                MARKET_PROBABILITY_REASON_CODES,
            ),
        )
        require_paper_only_flags("StrategyDecisionAuditMarketProbability", self)
        reject_unsafe_surface_fields("StrategyDecisionAuditMarketProbability", self)


@dataclass(frozen=True)
class StrategyDecisionAuditCosts:
    fee_cost: Decimal
    slippage_cost: Decimal
    liquidity_cost: Decimal
    total_cost: Decimal
    cost_adjusted_edge: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("fee_cost", "slippage_cost", "liquidity_cost", "total_cost"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_signed_score("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                COST_REASON_CODES,
            ),
        )
        require_paper_only_flags("StrategyDecisionAuditCosts", self)
        reject_unsafe_surface_fields("StrategyDecisionAuditCosts", self)
        _validate_costs(self)


@dataclass(frozen=True)
class StrategyDecisionAuditSourceQuality:
    source_quality_score: Decimal
    source_count: int
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_quality_score",
            _normalize_probability("source_quality_score", self.source_quality_score),
        )
        _require_positive_int("source_count", self.source_count)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                SOURCE_QUALITY_REASON_CODES,
            ),
        )
        require_paper_only_flags("StrategyDecisionAuditSourceQuality", self)
        reject_unsafe_surface_fields("StrategyDecisionAuditSourceQuality", self)


@dataclass(frozen=True)
class StrategyDecisionAuditTeamMemory:
    team_id: str
    team_memory_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        object.__setattr__(
            self,
            "team_memory_score",
            _normalize_probability("team_memory_score", self.team_memory_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                TEAM_MEMORY_REASON_CODES,
            ),
        )
        require_paper_only_flags("StrategyDecisionAuditTeamMemory", self)
        reject_unsafe_surface_fields("StrategyDecisionAuditTeamMemory", self)


@dataclass(frozen=True)
class StrategyDecisionAuditResolutionRisk:
    resolution_risk_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "resolution_risk_score",
            _normalize_probability("resolution_risk_score", self.resolution_risk_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                RESOLUTION_RISK_REASON_CODES,
            ),
        )
        require_paper_only_flags("StrategyDecisionAuditResolutionRisk", self)
        reject_unsafe_surface_fields("StrategyDecisionAuditResolutionRisk", self)


@dataclass(frozen=True)
class StrategyDecisionAuditRecommendation:
    recommendation: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if (
            type(self.recommendation) is not str
            or self.recommendation not in STRATEGY_DECISION_AUDIT_RECOMMENDATIONS
        ):
            raise ValueError("recommendation must be enter, watch, or skip")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                RECOMMENDATION_REASON_CODES,
            ),
        )
        require_paper_only_flags("StrategyDecisionAuditRecommendation", self)
        reject_unsafe_surface_fields("StrategyDecisionAuditRecommendation", self)
        _validate_recommendation_reason(self)


@dataclass(frozen=True)
class StrategyDecisionAuditPacket:
    config_version: str
    candidate_id: str
    market_slug: str
    outcome_name: str
    team_id: str
    packet_status: str
    forecast_edge: Decimal
    cost_adjusted_edge: Decimal
    forecast: StrategyDecisionAuditForecast
    market_probability: StrategyDecisionAuditMarketProbability
    costs: StrategyDecisionAuditCosts
    source_quality: StrategyDecisionAuditSourceQuality
    team_memory: StrategyDecisionAuditTeamMemory
    resolution_risk: StrategyDecisionAuditResolutionRisk
    recommendation: StrategyDecisionAuditRecommendation
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "config_version",
            "candidate_id",
            "market_slug",
            "outcome_name",
            "team_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_status("packet_status", self.packet_status)
        object.__setattr__(
            self,
            "forecast_edge",
            _normalize_signed_score("forecast_edge", self.forecast_edge),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_signed_score("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        _require_component(
            "forecast",
            self.forecast,
            StrategyDecisionAuditForecast,
        )
        _require_component(
            "market_probability",
            self.market_probability,
            StrategyDecisionAuditMarketProbability,
        )
        _require_component("costs", self.costs, StrategyDecisionAuditCosts)
        _require_component(
            "source_quality",
            self.source_quality,
            StrategyDecisionAuditSourceQuality,
        )
        _require_component("team_memory", self.team_memory, StrategyDecisionAuditTeamMemory)
        _require_component(
            "resolution_risk",
            self.resolution_risk,
            StrategyDecisionAuditResolutionRisk,
        )
        _require_component(
            "recommendation",
            self.recommendation,
            StrategyDecisionAuditRecommendation,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                STRATEGY_DECISION_AUDIT_PACKET_REASON_CODES,
            ),
        )
        require_paper_only_flags("StrategyDecisionAuditPacket", self)
        reject_unsafe_surface_fields("StrategyDecisionAuditPacket", self)
        _validate_packet_consistency(self)


def build_strategy_decision_audit_packet(
    *,
    forecast: StrategyDecisionAuditForecast,
    market_probability: StrategyDecisionAuditMarketProbability,
    costs: StrategyDecisionAuditCosts,
    source_quality: StrategyDecisionAuditSourceQuality,
    team_memory: StrategyDecisionAuditTeamMemory,
    resolution_risk: StrategyDecisionAuditResolutionRisk,
    recommendation: StrategyDecisionAuditRecommendation,
    config_version: str = DEFAULT_STRATEGY_DECISION_AUDIT_PACKET_CONFIG_VERSION,
) -> StrategyDecisionAuditPacket:
    _require_component("forecast", forecast, StrategyDecisionAuditForecast)
    _require_component(
        "market_probability",
        market_probability,
        StrategyDecisionAuditMarketProbability,
    )
    _require_component("costs", costs, StrategyDecisionAuditCosts)
    _require_component("source_quality", source_quality, StrategyDecisionAuditSourceQuality)
    _require_component("team_memory", team_memory, StrategyDecisionAuditTeamMemory)
    _require_component(
        "resolution_risk",
        resolution_risk,
        StrategyDecisionAuditResolutionRisk,
    )
    _require_component(
        "recommendation",
        recommendation,
        StrategyDecisionAuditRecommendation,
    )
    _require_canonical_string("config_version", config_version)

    packet_status = _packet_status(recommendation)
    return StrategyDecisionAuditPacket(
        config_version=config_version,
        candidate_id=market_probability.candidate_id,
        market_slug=market_probability.market_slug,
        outcome_name=market_probability.outcome_name,
        team_id=team_memory.team_id,
        packet_status=packet_status,
        forecast_edge=(
            forecast.forecast_probability - market_probability.market_probability
        ).quantize(SCORE_QUANT),
        cost_adjusted_edge=costs.cost_adjusted_edge,
        forecast=forecast,
        market_probability=market_probability,
        costs=costs,
        source_quality=source_quality,
        team_memory=team_memory,
        resolution_risk=resolution_risk,
        recommendation=recommendation,
        reason_codes=_packet_reason_codes(
            packet_status=packet_status,
            forecast=forecast,
            market_probability=market_probability,
            costs=costs,
            source_quality=source_quality,
            team_memory=team_memory,
            resolution_risk=resolution_risk,
            recommendation=recommendation,
        ),
    )


def strategy_decision_audit_packet_payload(
    payload: StrategyDecisionAuditPacket,
) -> dict[str, Any]:
    if type(payload) is not StrategyDecisionAuditPacket:
        raise ValueError("payload must be a StrategyDecisionAuditPacket")
    require_paper_only_flags("StrategyDecisionAuditPacket", payload)
    reject_unsafe_surface_fields("StrategyDecisionAuditPacket", payload)
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("payload must serialize to a JSON object")
    reject_unsafe_surface_fields("StrategyDecisionAuditPacket payload", ready)
    return ready


def _packet_status(recommendation: StrategyDecisionAuditRecommendation) -> str:
    if recommendation.recommendation == "enter":
        return "ready"
    if recommendation.recommendation == "watch":
        return "watch"
    return "blocked"


def _packet_status_reason(packet_status: str) -> str:
    return f"strategy_decision_audit_packet_{packet_status}"


def _packet_reason_codes(
    *,
    packet_status: str,
    forecast: StrategyDecisionAuditForecast,
    market_probability: StrategyDecisionAuditMarketProbability,
    costs: StrategyDecisionAuditCosts,
    source_quality: StrategyDecisionAuditSourceQuality,
    team_memory: StrategyDecisionAuditTeamMemory,
    resolution_risk: StrategyDecisionAuditResolutionRisk,
    recommendation: StrategyDecisionAuditRecommendation,
) -> tuple[str, ...]:
    return (
        (_packet_status_reason(packet_status),)
        + forecast.reason_codes
        + market_probability.reason_codes
        + costs.reason_codes
        + source_quality.reason_codes
        + team_memory.reason_codes
        + resolution_risk.reason_codes
        + recommendation.reason_codes
    )


def _validate_packet_consistency(packet: StrategyDecisionAuditPacket) -> None:
    expected_status = _packet_status(packet.recommendation)
    if packet.packet_status != expected_status:
        raise ValueError("packet_status must match recommendation")
    if packet.candidate_id != packet.market_probability.candidate_id:
        raise ValueError("candidate_id must match market_probability")
    if packet.market_slug != packet.market_probability.market_slug:
        raise ValueError("market_slug must match market_probability")
    if packet.outcome_name != packet.market_probability.outcome_name:
        raise ValueError("outcome_name must match market_probability")
    if packet.team_id != packet.team_memory.team_id:
        raise ValueError("team_id must match team_memory")
    expected_edge = (
        packet.forecast.forecast_probability
        - packet.market_probability.market_probability
    ).quantize(SCORE_QUANT)
    if packet.forecast_edge != expected_edge:
        raise ValueError("forecast_edge must match forecast minus market probability")
    if packet.cost_adjusted_edge != packet.costs.cost_adjusted_edge:
        raise ValueError("cost_adjusted_edge must match costs")
    expected_reasons = _packet_reason_codes(
        packet_status=packet.packet_status,
        forecast=packet.forecast,
        market_probability=packet.market_probability,
        costs=packet.costs,
        source_quality=packet.source_quality,
        team_memory=packet.team_memory,
        resolution_risk=packet.resolution_risk,
        recommendation=packet.recommendation,
    )
    if packet.reason_codes != expected_reasons:
        raise ValueError("reason_codes must include all component reason codes")


def _validate_costs(value: StrategyDecisionAuditCosts) -> None:
    expected_total = (
        value.fee_cost + value.slippage_cost + value.liquidity_cost
    ).quantize(SCORE_QUANT)
    if value.total_cost != expected_total:
        raise ValueError("total_cost must match fee, slippage, and liquidity costs")


def _validate_recommendation_reason(value: StrategyDecisionAuditRecommendation) -> None:
    expected_reason = f"recommendation_{value.recommendation}"
    if value.reason_codes != (expected_reason,):
        raise ValueError("recommendation reason_codes must match recommendation")


def _require_component(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    require_paper_only_flags(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in STRATEGY_DECISION_AUDIT_PACKET_STATUSES
    ):
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive int")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < DECIMAL_ZERO or normalized > DECIMAL_ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_signed_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < DECIMAL_NEGATIVE_ONE or normalized > DECIMAL_ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(SCORE_QUANT)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must contain at least one value")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return value


__all__ = (
    "DEFAULT_STRATEGY_DECISION_AUDIT_PACKET_CONFIG_VERSION",
    "STRATEGY_DECISION_AUDIT_PACKET_REASON_CODES",
    "STRATEGY_DECISION_AUDIT_PACKET_STATUSES",
    "STRATEGY_DECISION_AUDIT_RECOMMENDATIONS",
    "StrategyDecisionAuditCosts",
    "StrategyDecisionAuditForecast",
    "StrategyDecisionAuditMarketProbability",
    "StrategyDecisionAuditPacket",
    "StrategyDecisionAuditRecommendation",
    "StrategyDecisionAuditResolutionRisk",
    "StrategyDecisionAuditSourceQuality",
    "StrategyDecisionAuditTeamMemory",
    "build_strategy_decision_audit_packet",
    "strategy_decision_audit_packet_payload",
)
