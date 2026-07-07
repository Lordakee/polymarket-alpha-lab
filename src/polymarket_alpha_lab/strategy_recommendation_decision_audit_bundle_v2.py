"""Readonly Decimal-only strategy recommendation decision audit bundle v2."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_CONFIG_VERSION = "strategy-recommendation-decision-audit-bundle-v2"
SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
NEGATIVE_ONE = Decimal("-1.000000")
DECIMAL_CONTEXT_PRECISION = 28
AUDIT_COMPONENT_COUNT = Decimal("9")

READY_THRESHOLD = Decimal("0.700000")
BLOCKED_THRESHOLD = Decimal("0.500000")
FRESHNESS_READY_THRESHOLD = Decimal("0.700000")
FRESHNESS_BLOCKED_THRESHOLD = Decimal("0.500000")
LIQUIDITY_READY_THRESHOLD = Decimal("0.650000")
LIQUIDITY_BLOCKED_THRESHOLD = Decimal("0.500000")
RESOLUTION_WATCH_THRESHOLD = Decimal("0.500000")
RESOLUTION_BLOCKED_THRESHOLD = Decimal("0.750000")
PORTFOLIO_WATCH_THRESHOLD = Decimal("0.500000")
PORTFOLIO_BLOCKED_THRESHOLD = Decimal("0.750000")
QUORUM_READY_THRESHOLD = Decimal("0.700000")
QUORUM_BLOCKED_THRESHOLD = Decimal("0.500000")
DIGEST_HEX_LENGTH = 64

FINAL_RECOMMENDATIONS = ("paper_enter", "paper_watch", "paper_skip")
RECOMMENDATION_POSTURES = ("ready", "watch", "blocked")
INPUT_REASON_CODES = ("candidate_input_complete",)
DERIVED_REASON_CODES = (
    "recommendation_posture_ready",
    "recommendation_posture_watch",
    "recommendation_posture_blocked",
    "research_quality_ready",
    "research_quality_watch",
    "research_quality_blocked",
    "official_source_anchor_ready",
    "official_source_anchor_watch",
    "official_source_anchor_blocked",
    "information_freshness_ready",
    "information_freshness_watch",
    "information_freshness_blocked",
    "cost_break_even_positive",
    "cost_break_even_negative",
    "position_size_within_limit",
    "position_size_above_limit",
    "liquidity_exit_feasible",
    "liquidity_exit_watch",
    "liquidity_exit_blocked",
    "resolution_risk_acceptable",
    "resolution_risk_watch",
    "resolution_risk_blocked",
    "specialist_quorum_met",
    "specialist_quorum_watch",
    "specialist_quorum_missing",
    "portfolio_impact_acceptable",
    "portfolio_impact_watch",
    "portfolio_impact_blocked",
)
ALL_REASON_CODES = INPUT_REASON_CODES + DERIVED_REASON_CODES
UNSAFE_PUBLIC_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
DECIMAL_PAYLOAD_FIELDS = frozenset(
    (
        "research_quality_score",
        "official_source_anchor_score",
        "information_freshness_score",
        "gross_edge",
        "fee_cost",
        "slippage_cost",
        "break_even_edge",
        "net_edge",
        "cost_break_even_margin",
        "recommended_position_notional",
        "max_position_notional",
        "position_sizing_score",
        "exit_liquidity_score",
        "resolution_risk_score",
        "specialist_quorum_score",
        "portfolio_impact_score",
        "audit_score",
    ),
)


@dataclass(frozen=True)
class StrategyRecommendationDecisionAuditBundleV2Input:
    candidate_id: str
    market_slug: str
    outcome_name: str
    research_quality_score: Decimal
    official_source_anchor_score: Decimal
    information_freshness_score: Decimal
    gross_edge: Decimal
    fee_cost: Decimal
    slippage_cost: Decimal
    break_even_edge: Decimal
    recommended_position_notional: Decimal
    max_position_notional: Decimal
    exit_liquidity_score: Decimal
    resolution_risk_score: Decimal
    specialist_quorum_score: Decimal
    specialist_approval_count: int
    specialist_required_count: int
    portfolio_impact_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "outcome_name"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "research_quality_score",
            "official_source_anchor_score",
            "information_freshness_score",
            "exit_liquidity_score",
            "resolution_risk_score",
            "specialist_quorum_score",
            "portfolio_impact_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "gross_edge",
            _normalize_signed_decimal("gross_edge", self.gross_edge),
        )
        for field_name in (
            "fee_cost",
            "slippage_cost",
            "break_even_edge",
            "recommended_position_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_position_notional",
            _normalize_positive_decimal(
                "max_position_notional",
                self.max_position_notional,
            ),
        )
        _require_nonnegative_int(
            "specialist_approval_count",
            self.specialist_approval_count,
        )
        _require_positive_int("specialist_required_count", self.specialist_required_count)
        if self.specialist_approval_count > self.specialist_required_count:
            raise ValueError("specialist_approval_count cannot exceed required count")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, INPUT_REASON_CODES),
        )
        _require_safety_flags("input", self)
        _validate_input_costs(self)


@dataclass(frozen=True)
class StrategyRecommendationDecisionAuditBundleV2:
    config_version: str
    candidate_id: str
    market_slug: str
    outcome_name: str
    research_quality_score: Decimal
    official_source_anchor_score: Decimal
    information_freshness_score: Decimal
    gross_edge: Decimal
    fee_cost: Decimal
    slippage_cost: Decimal
    break_even_edge: Decimal
    net_edge: Decimal
    cost_break_even_margin: Decimal
    recommended_position_notional: Decimal
    max_position_notional: Decimal
    position_sizing_score: Decimal
    exit_liquidity_score: Decimal
    liquidity_exit_feasible: bool
    resolution_risk_score: Decimal
    specialist_quorum_score: Decimal
    specialist_approval_count: int
    specialist_required_count: int
    specialist_quorum_met: bool
    portfolio_impact_score: Decimal
    audit_score: Decimal
    final_recommendation: str
    recommendation_posture: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "config_version",
            "candidate_id",
            "market_slug",
            "outcome_name",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "research_quality_score",
            "official_source_anchor_score",
            "information_freshness_score",
            "exit_liquidity_score",
            "resolution_risk_score",
            "specialist_quorum_score",
            "portfolio_impact_score",
            "audit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_edge",
            "net_edge",
            "cost_break_even_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_cost",
            "slippage_cost",
            "break_even_edge",
            "recommended_position_notional",
            "position_sizing_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_position_notional",
            _normalize_positive_decimal(
                "max_position_notional",
                self.max_position_notional,
            ),
        )
        if type(self.liquidity_exit_feasible) is not bool:
            raise ValueError("liquidity_exit_feasible must be a bool")
        if type(self.specialist_quorum_met) is not bool:
            raise ValueError("specialist_quorum_met must be a bool")
        _require_nonnegative_int(
            "specialist_approval_count",
            self.specialist_approval_count,
        )
        _require_positive_int("specialist_required_count", self.specialist_required_count)
        if self.specialist_approval_count > self.specialist_required_count:
            raise ValueError("specialist_approval_count cannot exceed required count")
        _require_member(
            "final_recommendation",
            self.final_recommendation,
            FINAL_RECOMMENDATIONS,
        )
        _require_member(
            "recommendation_posture",
            self.recommendation_posture,
            RECOMMENDATION_POSTURES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ALL_REASON_CODES),
        )
        _require_safety_flags("bundle", self)
        _validate_bundle_consistency(self)
        expected_digest = _bundle_derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")


def build_strategy_recommendation_decision_audit_bundle_v2(
    recommendation_input: StrategyRecommendationDecisionAuditBundleV2Input,
    *,
    config_version: str = DEFAULT_CONFIG_VERSION,
) -> StrategyRecommendationDecisionAuditBundleV2:
    if type(recommendation_input) is not StrategyRecommendationDecisionAuditBundleV2Input:
        raise ValueError(
            "recommendation_input must be a "
            "StrategyRecommendationDecisionAuditBundleV2Input",
        )
    _require_safety_flags("recommendation_input", recommendation_input)
    _require_canonical_string("config_version", config_version)

    net_edge = _net_edge(recommendation_input)
    position_sizing_score = _position_sizing_score(recommendation_input)
    liquidity_exit_feasible = _liquidity_exit_feasible(recommendation_input)
    specialist_quorum_met = _specialist_quorum_met(recommendation_input)
    recommendation_posture = _recommendation_posture(
        recommendation_input,
        net_edge=net_edge,
        liquidity_exit_feasible=liquidity_exit_feasible,
        specialist_quorum_met=specialist_quorum_met,
    )

    return StrategyRecommendationDecisionAuditBundleV2(
        config_version=config_version,
        candidate_id=recommendation_input.candidate_id,
        market_slug=recommendation_input.market_slug,
        outcome_name=recommendation_input.outcome_name,
        research_quality_score=recommendation_input.research_quality_score,
        official_source_anchor_score=(
            recommendation_input.official_source_anchor_score
        ),
        information_freshness_score=recommendation_input.information_freshness_score,
        gross_edge=recommendation_input.gross_edge,
        fee_cost=recommendation_input.fee_cost,
        slippage_cost=recommendation_input.slippage_cost,
        break_even_edge=recommendation_input.break_even_edge,
        net_edge=net_edge,
        cost_break_even_margin=net_edge,
        recommended_position_notional=(
            recommendation_input.recommended_position_notional
        ),
        max_position_notional=recommendation_input.max_position_notional,
        position_sizing_score=position_sizing_score,
        exit_liquidity_score=recommendation_input.exit_liquidity_score,
        liquidity_exit_feasible=liquidity_exit_feasible,
        resolution_risk_score=recommendation_input.resolution_risk_score,
        specialist_quorum_score=recommendation_input.specialist_quorum_score,
        specialist_approval_count=recommendation_input.specialist_approval_count,
        specialist_required_count=recommendation_input.specialist_required_count,
        specialist_quorum_met=specialist_quorum_met,
        portfolio_impact_score=recommendation_input.portfolio_impact_score,
        audit_score=_audit_score(
            recommendation_input,
            net_edge=net_edge,
            position_sizing_score=position_sizing_score,
        ),
        final_recommendation=_final_recommendation(recommendation_posture),
        recommendation_posture=recommendation_posture,
        reason_codes=_reason_codes(
            recommendation_input,
            recommendation_posture=recommendation_posture,
            net_edge=net_edge,
            liquidity_exit_feasible=liquidity_exit_feasible,
            specialist_quorum_met=specialist_quorum_met,
        ),
    )


def strategy_recommendation_decision_audit_bundle_v2_payload(
    bundle: StrategyRecommendationDecisionAuditBundleV2,
) -> dict[str, Any]:
    if type(bundle) is not StrategyRecommendationDecisionAuditBundleV2:
        raise ValueError(
            "bundle must be a StrategyRecommendationDecisionAuditBundleV2",
        )
    _require_safety_flags("bundle", bundle)
    _validate_bundle_consistency(bundle)
    if bundle.derived_validation_digest != _bundle_derived_validation_digest(bundle):
        raise ValueError("derived_validation_digest mismatch")
    payload = _bundle_public_payload(bundle)
    validate_strategy_recommendation_decision_audit_bundle_v2_public_payload(payload)
    return payload


def validate_strategy_recommendation_decision_audit_bundle_v2_public_payload(
    payload: object,
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload(payload)
    expected_keys = set(_public_payload_keys())
    actual_keys = set(payload)
    if actual_keys != expected_keys:
        raise ValueError("public payload keys must match audit schema")

    for field_name in (
        "config_version",
        "candidate_id",
        "market_slug",
        "outcome_name",
        "final_recommendation",
        "recommendation_posture",
    ):
        _payload_required_string(payload, field_name)
    _payload_required_member(payload, "final_recommendation", FINAL_RECOMMENDATIONS)
    _payload_required_member(payload, "recommendation_posture", RECOMMENDATION_POSTURES)
    for field_name in DECIMAL_PAYLOAD_FIELDS:
        _payload_required_decimal_string(payload, field_name)
    _payload_required_int(payload, "specialist_approval_count")
    _payload_required_int(payload, "specialist_required_count")
    _payload_required_bool(payload, "liquidity_exit_feasible")
    _payload_required_bool(payload, "specialist_quorum_met")
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not list:
        raise ValueError("reason_codes must be a list")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in ALL_REASON_CODES:
            raise ValueError("reason_codes must contain known reason codes")
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest mismatch")


def _net_edge(
    recommendation_input: StrategyRecommendationDecisionAuditBundleV2Input,
) -> Decimal:
    return _quantize(
        recommendation_input.gross_edge - recommendation_input.break_even_edge,
    )


def _position_sizing_score(
    recommendation_input: StrategyRecommendationDecisionAuditBundleV2Input,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _quantize_down(
            recommendation_input.recommended_position_notional
            / recommendation_input.max_position_notional,
        )


def _liquidity_exit_feasible(
    recommendation_input: StrategyRecommendationDecisionAuditBundleV2Input,
) -> bool:
    return (
        recommendation_input.exit_liquidity_score >= LIQUIDITY_READY_THRESHOLD
        and recommendation_input.recommended_position_notional
        <= recommendation_input.max_position_notional
    )


def _specialist_quorum_met(
    recommendation_input: StrategyRecommendationDecisionAuditBundleV2Input,
) -> bool:
    return (
        recommendation_input.specialist_approval_count
        >= recommendation_input.specialist_required_count
        and recommendation_input.specialist_quorum_score >= QUORUM_READY_THRESHOLD
    )


def _recommendation_posture(
    recommendation_input: StrategyRecommendationDecisionAuditBundleV2Input,
    *,
    net_edge: Decimal,
    liquidity_exit_feasible: bool,
    specialist_quorum_met: bool,
) -> str:
    if _has_blocking_condition(
        recommendation_input,
        net_edge=net_edge,
        specialist_quorum_met=specialist_quorum_met,
    ):
        return "blocked"
    if _has_watch_condition(
        recommendation_input,
        net_edge=net_edge,
        liquidity_exit_feasible=liquidity_exit_feasible,
        specialist_quorum_met=specialist_quorum_met,
    ):
        return "watch"
    return "ready"


def _has_blocking_condition(
    recommendation_input: StrategyRecommendationDecisionAuditBundleV2Input,
    *,
    net_edge: Decimal,
    specialist_quorum_met: bool,
) -> bool:
    return (
        recommendation_input.research_quality_score < BLOCKED_THRESHOLD
        or recommendation_input.official_source_anchor_score < BLOCKED_THRESHOLD
        or recommendation_input.information_freshness_score < FRESHNESS_BLOCKED_THRESHOLD
        or net_edge < ZERO
        or recommendation_input.exit_liquidity_score < LIQUIDITY_BLOCKED_THRESHOLD
        or recommendation_input.resolution_risk_score >= RESOLUTION_BLOCKED_THRESHOLD
        or recommendation_input.specialist_quorum_score < QUORUM_BLOCKED_THRESHOLD
        or not specialist_quorum_met
        or recommendation_input.portfolio_impact_score >= PORTFOLIO_BLOCKED_THRESHOLD
    )


def _has_watch_condition(
    recommendation_input: StrategyRecommendationDecisionAuditBundleV2Input,
    *,
    net_edge: Decimal,
    liquidity_exit_feasible: bool,
    specialist_quorum_met: bool,
) -> bool:
    return (
        recommendation_input.research_quality_score < READY_THRESHOLD
        or recommendation_input.official_source_anchor_score < READY_THRESHOLD
        or recommendation_input.information_freshness_score < FRESHNESS_READY_THRESHOLD
        or net_edge <= ZERO
        or recommendation_input.recommended_position_notional
        > recommendation_input.max_position_notional
        or not liquidity_exit_feasible
        or recommendation_input.resolution_risk_score >= RESOLUTION_WATCH_THRESHOLD
        or not specialist_quorum_met
        or recommendation_input.portfolio_impact_score >= PORTFOLIO_WATCH_THRESHOLD
    )


def _final_recommendation(recommendation_posture: str) -> str:
    if recommendation_posture == "ready":
        return "paper_enter"
    if recommendation_posture == "watch":
        return "paper_watch"
    return "paper_skip"


def _audit_score(
    recommendation_input: StrategyRecommendationDecisionAuditBundleV2Input,
    *,
    net_edge: Decimal,
    position_sizing_score: Decimal,
) -> Decimal:
    capped_edge = _cap_probability(net_edge)
    capped_position = _cap_probability(position_sizing_score)
    resolution_quality = ONE - recommendation_input.resolution_risk_score
    portfolio_quality = ONE - recommendation_input.portfolio_impact_score
    total = (
        recommendation_input.research_quality_score
        + recommendation_input.official_source_anchor_score
        + recommendation_input.information_freshness_score
        + capped_edge
        + capped_position
        + recommendation_input.exit_liquidity_score
        + resolution_quality
        + recommendation_input.specialist_quorum_score
        + portfolio_quality
    )
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _quantize_down(total / AUDIT_COMPONENT_COUNT)


def _reason_codes(
    recommendation_input: StrategyRecommendationDecisionAuditBundleV2Input,
    *,
    recommendation_posture: str,
    net_edge: Decimal,
    liquidity_exit_feasible: bool,
    specialist_quorum_met: bool,
) -> tuple[str, ...]:
    reason_codes = [f"recommendation_posture_{recommendation_posture}"]
    reason_codes.extend(recommendation_input.reason_codes)
    reason_codes.append(
        _score_reason(
            "research_quality",
            recommendation_input.research_quality_score,
            READY_THRESHOLD,
            BLOCKED_THRESHOLD,
            high_is_good=True,
        ),
    )
    reason_codes.append(
        _score_reason(
            "official_source_anchor",
            recommendation_input.official_source_anchor_score,
            READY_THRESHOLD,
            BLOCKED_THRESHOLD,
            high_is_good=True,
        ),
    )
    reason_codes.append(
        _score_reason(
            "information_freshness",
            recommendation_input.information_freshness_score,
            FRESHNESS_READY_THRESHOLD,
            FRESHNESS_BLOCKED_THRESHOLD,
            high_is_good=True,
        ),
    )
    if net_edge >= ZERO:
        reason_codes.append("cost_break_even_positive")
    else:
        reason_codes.append("cost_break_even_negative")
    if (
        recommendation_input.recommended_position_notional
        <= recommendation_input.max_position_notional
    ):
        reason_codes.append("position_size_within_limit")
    else:
        reason_codes.append("position_size_above_limit")
    if liquidity_exit_feasible:
        reason_codes.append("liquidity_exit_feasible")
    elif recommendation_input.exit_liquidity_score < LIQUIDITY_BLOCKED_THRESHOLD:
        reason_codes.append("liquidity_exit_blocked")
    else:
        reason_codes.append("liquidity_exit_watch")
    reason_codes.append(
        _score_reason(
            "resolution_risk",
            recommendation_input.resolution_risk_score,
            RESOLUTION_WATCH_THRESHOLD,
            RESOLUTION_BLOCKED_THRESHOLD,
            high_is_good=False,
        ),
    )
    if specialist_quorum_met:
        reason_codes.append("specialist_quorum_met")
    elif (
        recommendation_input.specialist_approval_count
        < recommendation_input.specialist_required_count
        or recommendation_input.specialist_quorum_score < QUORUM_BLOCKED_THRESHOLD
    ):
        reason_codes.append("specialist_quorum_missing")
    else:
        reason_codes.append("specialist_quorum_watch")
    reason_codes.append(
        _score_reason(
            "portfolio_impact",
            recommendation_input.portfolio_impact_score,
            PORTFOLIO_WATCH_THRESHOLD,
            PORTFOLIO_BLOCKED_THRESHOLD,
            high_is_good=False,
        ),
    )
    return _normalize_reason_codes(tuple(reason_codes), ALL_REASON_CODES)


def _score_reason(
    prefix: str,
    value: Decimal,
    ready_threshold: Decimal,
    blocked_threshold: Decimal,
    *,
    high_is_good: bool,
) -> str:
    if high_is_good:
        if value >= ready_threshold:
            return f"{prefix}_ready"
        if value < blocked_threshold:
            return f"{prefix}_blocked"
        return f"{prefix}_watch"
    if value < ready_threshold:
        return f"{prefix}_acceptable"
    if value >= blocked_threshold:
        return f"{prefix}_blocked"
    return f"{prefix}_watch"


def _validate_input_costs(
    recommendation_input: StrategyRecommendationDecisionAuditBundleV2Input,
) -> None:
    expected_break_even = _quantize(
        recommendation_input.fee_cost + recommendation_input.slippage_cost,
    )
    if recommendation_input.break_even_edge != expected_break_even:
        raise ValueError("break_even_edge must match fee and slippage costs")


def _validate_bundle_consistency(
    bundle: StrategyRecommendationDecisionAuditBundleV2,
) -> None:
    expected_break_even = _quantize(bundle.fee_cost + bundle.slippage_cost)
    if bundle.break_even_edge != expected_break_even:
        raise ValueError("break_even_edge must match fee and slippage costs")
    expected_net_edge = _quantize(bundle.gross_edge - bundle.break_even_edge)
    if bundle.net_edge != expected_net_edge:
        raise ValueError("net_edge must match gross_edge minus break_even_edge")
    if bundle.cost_break_even_margin != expected_net_edge:
        raise ValueError("cost_break_even_margin must match net_edge")
    expected_position_score = _quantize_down(
        bundle.recommended_position_notional / bundle.max_position_notional,
    )
    if bundle.position_sizing_score != expected_position_score:
        raise ValueError("position_sizing_score must match position sizing ratio")
    input_reason_codes = tuple(
        reason_code
        for reason_code in bundle.reason_codes
        if reason_code in INPUT_REASON_CODES
    )
    if not input_reason_codes:
        raise ValueError("reason_codes must include all derived reasons")
    input_view = StrategyRecommendationDecisionAuditBundleV2Input(
        candidate_id=bundle.candidate_id,
        market_slug=bundle.market_slug,
        outcome_name=bundle.outcome_name,
        research_quality_score=bundle.research_quality_score,
        official_source_anchor_score=bundle.official_source_anchor_score,
        information_freshness_score=bundle.information_freshness_score,
        gross_edge=bundle.gross_edge,
        fee_cost=bundle.fee_cost,
        slippage_cost=bundle.slippage_cost,
        break_even_edge=bundle.break_even_edge,
        recommended_position_notional=bundle.recommended_position_notional,
        max_position_notional=bundle.max_position_notional,
        exit_liquidity_score=bundle.exit_liquidity_score,
        resolution_risk_score=bundle.resolution_risk_score,
        specialist_quorum_score=bundle.specialist_quorum_score,
        specialist_approval_count=bundle.specialist_approval_count,
        specialist_required_count=bundle.specialist_required_count,
        portfolio_impact_score=bundle.portfolio_impact_score,
        reason_codes=input_reason_codes,
    )
    expected_liquidity = _liquidity_exit_feasible(input_view)
    if bundle.liquidity_exit_feasible != expected_liquidity:
        raise ValueError("liquidity_exit_feasible must match liquidity inputs")
    expected_quorum = _specialist_quorum_met(input_view)
    if bundle.specialist_quorum_met != expected_quorum:
        raise ValueError("specialist_quorum_met must match specialist inputs")
    expected_posture = _recommendation_posture(
        input_view,
        net_edge=bundle.net_edge,
        liquidity_exit_feasible=bundle.liquidity_exit_feasible,
        specialist_quorum_met=bundle.specialist_quorum_met,
    )
    if bundle.recommendation_posture != expected_posture:
        raise ValueError("recommendation_posture must match audit inputs")
    if bundle.final_recommendation != _final_recommendation(expected_posture):
        raise ValueError("final_recommendation must match recommendation_posture")
    expected_audit_score = _audit_score(
        input_view,
        net_edge=bundle.net_edge,
        position_sizing_score=bundle.position_sizing_score,
    )
    if bundle.audit_score != expected_audit_score:
        raise ValueError("audit_score must match audit component scores")
    expected_reasons = _reason_codes(
        input_view,
        recommendation_posture=bundle.recommendation_posture,
        net_edge=bundle.net_edge,
        liquidity_exit_feasible=bundle.liquidity_exit_feasible,
        specialist_quorum_met=bundle.specialist_quorum_met,
    )
    if bundle.reason_codes != expected_reasons:
        raise ValueError("reason_codes must include all derived reasons")


def _bundle_public_payload(
    bundle: StrategyRecommendationDecisionAuditBundleV2,
) -> dict[str, Any]:
    payload = _bundle_public_payload_for_digest(bundle)
    payload["derived_validation_digest"] = bundle.derived_validation_digest
    return payload


def _bundle_public_payload_for_digest(
    bundle: StrategyRecommendationDecisionAuditBundleV2,
) -> dict[str, Any]:
    return {
        "config_version": bundle.config_version,
        "candidate_id": bundle.candidate_id,
        "market_slug": bundle.market_slug,
        "outcome_name": bundle.outcome_name,
        "research_quality_score": _decimal_payload(bundle.research_quality_score),
        "official_source_anchor_score": _decimal_payload(
            bundle.official_source_anchor_score,
        ),
        "information_freshness_score": _decimal_payload(
            bundle.information_freshness_score,
        ),
        "gross_edge": _decimal_payload(bundle.gross_edge),
        "fee_cost": _decimal_payload(bundle.fee_cost),
        "slippage_cost": _decimal_payload(bundle.slippage_cost),
        "break_even_edge": _decimal_payload(bundle.break_even_edge),
        "net_edge": _decimal_payload(bundle.net_edge),
        "cost_break_even_margin": _decimal_payload(bundle.cost_break_even_margin),
        "recommended_position_notional": _decimal_payload(
            bundle.recommended_position_notional,
        ),
        "max_position_notional": _decimal_payload(bundle.max_position_notional),
        "position_sizing_score": _decimal_payload(bundle.position_sizing_score),
        "exit_liquidity_score": _decimal_payload(bundle.exit_liquidity_score),
        "liquidity_exit_feasible": bundle.liquidity_exit_feasible,
        "resolution_risk_score": _decimal_payload(bundle.resolution_risk_score),
        "specialist_quorum_score": _decimal_payload(bundle.specialist_quorum_score),
        "specialist_approval_count": bundle.specialist_approval_count,
        "specialist_required_count": bundle.specialist_required_count,
        "specialist_quorum_met": bundle.specialist_quorum_met,
        "portfolio_impact_score": _decimal_payload(bundle.portfolio_impact_score),
        "audit_score": _decimal_payload(bundle.audit_score),
        "final_recommendation": bundle.final_recommendation,
        "recommendation_posture": bundle.recommendation_posture,
        "reason_codes": list(bundle.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _public_payload_keys() -> tuple[str, ...]:
    return (
        "config_version",
        "candidate_id",
        "market_slug",
        "outcome_name",
        "research_quality_score",
        "official_source_anchor_score",
        "information_freshness_score",
        "gross_edge",
        "fee_cost",
        "slippage_cost",
        "break_even_edge",
        "net_edge",
        "cost_break_even_margin",
        "recommended_position_notional",
        "max_position_notional",
        "position_sizing_score",
        "exit_liquidity_score",
        "liquidity_exit_feasible",
        "resolution_risk_score",
        "specialist_quorum_score",
        "specialist_approval_count",
        "specialist_required_count",
        "specialist_quorum_met",
        "portfolio_impact_score",
        "audit_score",
        "final_recommendation",
        "recommendation_posture",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )


def _bundle_derived_validation_digest(
    bundle: StrategyRecommendationDecisionAuditBundleV2,
) -> str:
    return _public_payload_derived_validation_digest(
        _bundle_public_payload_for_digest(bundle),
    )


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_required_string(payload: dict[Any, Any], field_name: str) -> str:
    value = payload[field_name]
    _require_canonical_string(field_name, value)
    return value


def _payload_required_member(
    payload: dict[Any, Any],
    field_name: str,
    allowed_values: tuple[str, ...],
) -> str:
    value = _payload_required_string(payload, field_name)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")
    return value


def _payload_required_decimal_string(
    payload: dict[Any, Any],
    field_name: str,
) -> Decimal:
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be serialized Decimal strings")
    decimal_value = Decimal(value)
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != _decimal_payload(decimal_value):
        raise ValueError(f"{field_name} must be serialized Decimal strings")
    return decimal_value


def _payload_required_int(payload: dict[Any, Any], field_name: str) -> int:
    value = payload[field_name]
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    return value


def _payload_required_bool(payload: dict[Any, Any], field_name: str) -> bool:
    value = payload[field_name]
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_safety_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
    _reject_unsafe_public_payload(_object_public_values(value))


def _object_public_values(value: object) -> dict[str, object]:
    if isinstance(value, StrategyRecommendationDecisionAuditBundleV2Input):
        return {
            "candidate_id": value.candidate_id,
            "market_slug": value.market_slug,
            "outcome_name": value.outcome_name,
            "reason_codes": value.reason_codes,
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
    if isinstance(value, StrategyRecommendationDecisionAuditBundleV2):
        return {
            "config_version": value.config_version,
            "candidate_id": value.candidate_id,
            "market_slug": value.market_slug,
            "outcome_name": value.outcome_name,
            "final_recommendation": value.final_recommendation,
            "recommendation_posture": value.recommendation_posture,
            "reason_codes": value.reason_codes,
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
    return {}


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_key(key)
            _reject_unsafe_public_payload(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str):
        _reject_unsafe_public_value(value)


def _reject_unsafe_public_key(key: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public key: {key}")


def _reject_unsafe_public_value(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value: {value}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_value(value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_reason_codes(
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in value:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError("reason_codes must contain known reason codes")
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    return value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _normalize_signed_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < NEGATIVE_ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _cap_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANT)


def _quantize_down(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANT, rounding=ROUND_DOWN)


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("Decimal payload value must be finite")
    return str(_quantize(value))


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if len(value) != DIGEST_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "StrategyRecommendationDecisionAuditBundleV2",
    "StrategyRecommendationDecisionAuditBundleV2Input",
    "build_strategy_recommendation_decision_audit_bundle_v2",
    "strategy_recommendation_decision_audit_bundle_v2_payload",
    "validate_strategy_recommendation_decision_audit_bundle_v2_public_payload",
)
