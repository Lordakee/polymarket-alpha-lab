"""Pure strategy recommendation labels from paper decision inputs."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_POLICY_CONFIG_VERSION",
    "StrategyRecommendationPolicyConfig",
    "StrategyRecommendationPolicyInput",
    "StrategyRecommendationPolicyLabel",
    "label_strategy_recommendation",
    "strategy_recommendation_policy_payload",
)


DEFAULT_STRATEGY_RECOMMENDATION_POLICY_CONFIG_VERSION = (
    "strategy-recommendation-policy-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
NEGATIVE_ONE = Decimal("-1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RECOMMENDED_ACTIONS = (
    "research_more",
    "watch",
    "paper_trade_yes",
    "paper_trade_no",
    "reject",
)
RECOMMENDED_SIDES = ("yes", "no", "none")


@dataclass(frozen=True)
class StrategyRecommendationPolicyConfig:
    config_version: str = DEFAULT_STRATEGY_RECOMMENDATION_POLICY_CONFIG_VERSION
    paper_trade_score: Decimal = Decimal("0.700000")
    watch_score: Decimal = Decimal("0.500000")
    research_score: Decimal = Decimal("0.250000")
    min_team_memory_confidence: Decimal = Decimal("0.650000")
    watch_team_memory_confidence: Decimal = Decimal("0.500000")
    min_source_quality: Decimal = Decimal("0.700000")
    watch_source_quality: Decimal = Decimal("0.550000")
    cost_guard_watch: Decimal = Decimal("0.200000")
    cost_guard_reject: Decimal = Decimal("0.350000")
    resolution_risk_watch: Decimal = Decimal("0.300000")
    resolution_risk_reject: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "paper_trade_score",
            "watch_score",
            "research_score",
            "min_team_memory_confidence",
            "watch_team_memory_confidence",
            "min_source_quality",
            "watch_source_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cost_guard_watch",
            "cost_guard_reject",
            "resolution_risk_watch",
            "resolution_risk_reject",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )

        _require_at_most(
            "watch_score",
            self.watch_score,
            "paper_trade_score",
            self.paper_trade_score,
        )
        _require_at_most(
            "research_score",
            self.research_score,
            "watch_score",
            self.watch_score,
        )
        _require_at_most(
            "watch_team_memory_confidence",
            self.watch_team_memory_confidence,
            "min_team_memory_confidence",
            self.min_team_memory_confidence,
        )
        _require_at_most(
            "watch_source_quality",
            self.watch_source_quality,
            "min_source_quality",
            self.min_source_quality,
        )
        _require_at_most(
            "cost_guard_watch",
            self.cost_guard_watch,
            "cost_guard_reject",
            self.cost_guard_reject,
        )
        _require_at_most(
            "resolution_risk_watch",
            self.resolution_risk_watch,
            "resolution_risk_reject",
            self.resolution_risk_reject,
        )
        reject_unsafe_surface_fields("strategy recommendation policy config", self)
        require_paper_only_flags("strategy recommendation policy config", self)


@dataclass(frozen=True)
class StrategyRecommendationPolicyInput:
    recommendation_id: str
    market_slug: str
    decision_matrix_score: Decimal
    team_memory_confidence: Decimal
    source_quality: Decimal
    cost_guard: Decimal
    resolution_risk: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("recommendation_id", self.recommendation_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "decision_matrix_score",
            _normalize_signed_score("decision_matrix_score", self.decision_matrix_score),
        )
        for field_name in ("team_memory_confidence", "source_quality"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("cost_guard", "resolution_risk"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_string_tuple("upstream_reason_codes", self.upstream_reason_codes),
        )
        reject_unsafe_surface_fields("strategy recommendation policy input", self)
        require_paper_only_flags("strategy recommendation policy input", self)


@dataclass(frozen=True)
class StrategyRecommendationPolicyLabel:
    config_version: str
    recommendation_id: str
    market_slug: str
    decision_matrix_score: Decimal
    decision_score_magnitude: Decimal
    team_memory_confidence: Decimal
    source_quality: Decimal
    cost_guard: Decimal
    resolution_risk: Decimal
    recommended_action: str
    recommended_side: str
    reason_codes: tuple[str, ...]
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("recommendation_id", self.recommendation_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "decision_matrix_score",
            _normalize_signed_score("decision_matrix_score", self.decision_matrix_score),
        )
        object.__setattr__(
            self,
            "decision_score_magnitude",
            _normalize_probability_decimal(
                "decision_score_magnitude",
                self.decision_score_magnitude,
            ),
        )
        for field_name in ("team_memory_confidence", "source_quality"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("cost_guard", "resolution_risk"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("recommended_action", self.recommended_action, RECOMMENDED_ACTIONS)
        _require_member("recommended_side", self.recommended_side, RECOMMENDED_SIDES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_nonempty_string_tuple("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_string_tuple("upstream_reason_codes", self.upstream_reason_codes),
        )
        _validate_label_shape(self)
        reject_unsafe_surface_fields("strategy recommendation policy label", self)
        require_paper_only_flags("strategy recommendation policy label", self)


def label_strategy_recommendation(
    candidate: StrategyRecommendationPolicyInput,
    *,
    config: StrategyRecommendationPolicyConfig,
) -> StrategyRecommendationPolicyLabel:
    if type(candidate) is not StrategyRecommendationPolicyInput:
        raise ValueError("candidate must be a StrategyRecommendationPolicyInput")
    if type(config) is not StrategyRecommendationPolicyConfig:
        raise ValueError("config must be a StrategyRecommendationPolicyConfig")
    require_paper_only_flags("strategy recommendation policy input", candidate)
    require_paper_only_flags("strategy recommendation policy config", config)

    decision_score_magnitude = _absolute_decimal(candidate.decision_matrix_score)
    recommended_side = _recommended_side(candidate.decision_matrix_score)
    action, generated_reason_codes = _recommended_action_and_reason_codes(
        candidate=candidate,
        decision_score_magnitude=decision_score_magnitude,
        config=config,
    )
    reason_codes = _normalize_nonempty_string_tuple(
        "reason_codes",
        (*candidate.upstream_reason_codes, *generated_reason_codes),
    )

    return StrategyRecommendationPolicyLabel(
        config_version=config.config_version,
        recommendation_id=candidate.recommendation_id,
        market_slug=candidate.market_slug,
        decision_matrix_score=candidate.decision_matrix_score,
        decision_score_magnitude=decision_score_magnitude,
        team_memory_confidence=candidate.team_memory_confidence,
        source_quality=candidate.source_quality,
        cost_guard=candidate.cost_guard,
        resolution_risk=candidate.resolution_risk,
        recommended_action=action,
        recommended_side=recommended_side,
        reason_codes=reason_codes,
        upstream_reason_codes=candidate.upstream_reason_codes,
    )


def strategy_recommendation_policy_payload(
    label: StrategyRecommendationPolicyLabel,
) -> dict[str, object]:
    if type(label) is not StrategyRecommendationPolicyLabel:
        raise ValueError("label must be a StrategyRecommendationPolicyLabel")
    reject_unsafe_surface_fields("strategy recommendation policy label", label)
    require_paper_only_flags("strategy recommendation policy label", label)
    ready = json_ready_no_floats(label)
    if type(ready) is not dict:
        raise ValueError("label payload must be a JSON object")
    return ready


def _recommended_action_and_reason_codes(
    *,
    candidate: StrategyRecommendationPolicyInput,
    decision_score_magnitude: Decimal,
    config: StrategyRecommendationPolicyConfig,
) -> tuple[str, tuple[str, ...]]:
    reason_codes: list[str] = [_edge_reason_code(candidate.decision_matrix_score)]

    cost_reason = _upper_guard_reason_code(
        value=candidate.cost_guard,
        watch_threshold=config.cost_guard_watch,
        reject_threshold=config.cost_guard_reject,
        pass_code="cost_guard_passed",
        watch_code="cost_guard_watch",
        reject_code="cost_guard_reject",
    )
    resolution_reason = _upper_guard_reason_code(
        value=candidate.resolution_risk,
        watch_threshold=config.resolution_risk_watch,
        reject_threshold=config.resolution_risk_reject,
        pass_code="resolution_risk_passed",
        watch_code="resolution_risk_watch",
        reject_code="resolution_risk_reject",
    )
    team_memory_reason = _lower_quality_reason_code(
        value=candidate.team_memory_confidence,
        watch_threshold=config.watch_team_memory_confidence,
        ready_threshold=config.min_team_memory_confidence,
        pass_code="team_memory_confidence_passed",
        watch_code="team_memory_confidence_watch",
        below_watch_code="team_memory_confidence_below_watch_threshold",
    )
    source_quality_reason = _lower_quality_reason_code(
        value=candidate.source_quality,
        watch_threshold=config.watch_source_quality,
        ready_threshold=config.min_source_quality,
        pass_code="source_quality_passed",
        watch_code="source_quality_watch",
        below_watch_code="source_quality_below_watch_threshold",
    )

    reason_codes.extend((cost_reason, resolution_reason, team_memory_reason, source_quality_reason))

    if "cost_guard_reject" in reason_codes or "resolution_risk_reject" in reason_codes:
        return "reject", tuple(reason_codes)

    if decision_score_magnitude < config.research_score:
        reason_codes.append("decision_matrix_score_below_research_threshold")
    elif decision_score_magnitude >= config.paper_trade_score:
        reason_codes.append("paper_trade_threshold_met")
    else:
        reason_codes.append("paper_trade_threshold_not_met")

    if (
        "decision_matrix_score_below_research_threshold" in reason_codes
        or "team_memory_confidence_below_watch_threshold" in reason_codes
        or "source_quality_below_watch_threshold" in reason_codes
    ):
        return "research_more", tuple(reason_codes)

    paper_ready = (
        "paper_trade_threshold_met" in reason_codes
        and team_memory_reason == "team_memory_confidence_passed"
        and source_quality_reason == "source_quality_passed"
        and cost_reason == "cost_guard_passed"
        and resolution_reason == "resolution_risk_passed"
    )
    if paper_ready and candidate.decision_matrix_score > ZERO:
        return "paper_trade_yes", tuple(reason_codes)
    if paper_ready and candidate.decision_matrix_score < ZERO:
        return "paper_trade_no", tuple(reason_codes)
    return "watch", tuple(reason_codes)


def _upper_guard_reason_code(
    *,
    value: Decimal,
    watch_threshold: Decimal,
    reject_threshold: Decimal,
    pass_code: str,
    watch_code: str,
    reject_code: str,
) -> str:
    if value >= reject_threshold:
        return reject_code
    if value >= watch_threshold:
        return watch_code
    return pass_code


def _lower_quality_reason_code(
    *,
    value: Decimal,
    watch_threshold: Decimal,
    ready_threshold: Decimal,
    pass_code: str,
    watch_code: str,
    below_watch_code: str,
) -> str:
    if value < watch_threshold:
        return below_watch_code
    if value < ready_threshold:
        return watch_code
    return pass_code


def _edge_reason_code(decision_matrix_score: Decimal) -> str:
    if decision_matrix_score > ZERO:
        return "decision_matrix_positive_edge"
    if decision_matrix_score < ZERO:
        return "decision_matrix_negative_edge"
    return "decision_matrix_no_edge"


def _recommended_side(decision_matrix_score: Decimal) -> str:
    if decision_matrix_score > ZERO:
        return "yes"
    if decision_matrix_score < ZERO:
        return "no"
    return "none"


def _validate_label_shape(label: StrategyRecommendationPolicyLabel) -> None:
    if label.decision_score_magnitude != _absolute_decimal(label.decision_matrix_score):
        raise ValueError("decision_score_magnitude must match decision_matrix_score")
    if label.recommended_action == "paper_trade_yes" and label.recommended_side != "yes":
        raise ValueError("paper_trade_yes labels must recommend the yes side")
    if label.recommended_action == "paper_trade_no" and label.recommended_side != "no":
        raise ValueError("paper_trade_no labels must recommend the no side")
    if label.recommended_side != _recommended_side(label.decision_matrix_score):
        raise ValueError("recommended_side must match decision_matrix_score")
    for reason_code in label.upstream_reason_codes:
        if reason_code not in label.reason_codes:
            raise ValueError("reason_codes must include upstream_reason_codes")
    if label.recommended_action == "reject" and not any(
        reason_code.endswith("_reject") for reason_code in label.reason_codes
    ):
        raise ValueError("reject labels must include a reject reason")
    if label.recommended_action.startswith("paper_trade_") and (
        "paper_trade_threshold_met" not in label.reason_codes
    ):
        raise ValueError("paper trade labels must include the paper trade threshold reason")


def _require_at_most(
    lower_name: str,
    lower_value: Decimal,
    upper_name: str,
    upper_value: Decimal,
) -> None:
    if lower_value > upper_value:
        raise ValueError(f"{lower_name} must not exceed {upper_name}")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be a probability Decimal")
    return normalized


def _normalize_signed_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < NEGATIVE_ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1.000000 and 1.000000")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _normalize_nonempty_string_tuple(field_name: str, values: object) -> tuple[str, ...]:
    normalized = _normalize_string_tuple(field_name, values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _normalize_string_tuple(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for value in values:
        _require_canonical_string(field_name, value)
    return tuple(sorted(dict.fromkeys(values)))


def _absolute_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return abs(value).quantize(QUANTUM)
