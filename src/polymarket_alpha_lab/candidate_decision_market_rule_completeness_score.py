"""Pure report-only market rule completeness scoring for candidate decisions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_MARKET_RULE_COMPLETENESS_SCORE_CONFIG_VERSION",
    "CandidateDecisionMarketRuleCompletenessScoreConfig",
    "CandidateDecisionMarketRuleCompletenessScoreInput",
    "CandidateDecisionMarketRuleCompletenessScoreResult",
    "score_candidate_decision_market_rule_completeness",
    "candidate_decision_market_rule_completeness_score_payload",
)


DEFAULT_CANDIDATE_DECISION_MARKET_RULE_COMPLETENESS_SCORE_CONFIG_VERSION = (
    "candidate-decision-market-rule-completeness-score-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_REASON_PREFIX = "candidate_decision_market_rule_completeness_"
VALIDATION_DIGEST_ALGORITHM = (
    "candidate-decision-market-rule-completeness-score-v0-sha256"
)
HEX_DIGITS = frozenset("0123456789abcdef")
UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
    "au" + "th",
    "candidate" + "_id",
    "d" + "sn",
    "market" + "_id",
    "market" + "_slug",
    "position" + "_size",
    "position" + "_sizing",
    "raw" + "_candidate",
    "sec" + "ret",
    "ta" + "ble",
    "tok" + "en",
    "u" + "rl",
    "wall" + "et",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "au" + "th",
    "candidate" + "_id",
    "d" + "sn",
    "ht" + "tp",
    "market-question",
    "market" + "_slug",
    "or" + "der",
    "polymarket",
    "position-size",
    "position_size",
    "post" + "gres",
    "question=",
    "recommend" + "ation",
    "sec" + "ret",
    "s" + "ell",
    "source-ref",
    "source_ref",
    "supa" + "base",
    "table:",
    "tok" + "en",
    "tr" + "ade",
    "url=",
    "wall" + "et",
    "www.",
    "b" + "uy",
)


@dataclass(frozen=True)
class CandidateDecisionMarketRuleCompletenessScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_MARKET_RULE_COMPLETENESS_SCORE_CONFIG_VERSION
    )
    minimum_pass_score: Decimal = Decimal("0.900000")
    minimum_watch_score: Decimal = Decimal("0.650000")
    minimum_rule_clause_count: Decimal = Decimal("2")
    minimum_boundary_condition_count: Decimal = Decimal("1")
    minimum_disqualifier_clause_count: Decimal = Decimal("1")
    minimum_settlement_source_count: Decimal = Decimal("1")
    maximum_contradiction_count: Decimal = Decimal("0")
    minimum_rule_specificity_score: Decimal = Decimal("0.700000")
    maximum_ambiguity_score: Decimal = Decimal("0.300000")
    rule_clause_weight: Decimal = Decimal("0.150000")
    boundary_condition_weight: Decimal = Decimal("0.150000")
    disqualifier_clause_weight: Decimal = Decimal("0.100000")
    settlement_source_weight: Decimal = Decimal("0.200000")
    contradiction_weight: Decimal = Decimal("0.150000")
    rule_specificity_weight: Decimal = Decimal("0.150000")
    ambiguity_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_pass_score",
            "minimum_watch_score",
            "minimum_rule_specificity_score",
            "maximum_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_watch_score > self.minimum_pass_score:
            raise ValueError(
                "minimum_watch_score must be less than or equal to minimum_pass_score",
            )
        for field_name in (
            "minimum_rule_clause_count",
            "minimum_boundary_condition_count",
            "minimum_disqualifier_clause_count",
            "minimum_settlement_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "maximum_contradiction_count",
            _normalize_nonnegative_count(
                "maximum_contradiction_count",
                self.maximum_contradiction_count,
            ),
        )
        for field_name in (
            "rule_clause_weight",
            "boundary_condition_weight",
            "disqualifier_clause_weight",
            "settlement_source_weight",
            "contradiction_weight",
            "rule_specificity_weight",
            "ambiguity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class CandidateDecisionMarketRuleCompletenessScoreInput:
    redacted_candidate_ref: str
    rule_clause_count: Decimal
    boundary_condition_count: Decimal
    disqualifier_clause_count: Decimal
    settlement_source_count: Decimal
    contradiction_count: Decimal
    rule_specificity_score: Decimal
    ambiguity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_candidate_ref(
            "redacted_candidate_ref",
            self.redacted_candidate_ref,
        )
        for field_name in (
            "rule_clause_count",
            "boundary_condition_count",
            "disqualifier_clause_count",
            "settlement_source_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("rule_specificity_score", "ambiguity_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("candidate_state", self)


@dataclass(frozen=True)
class CandidateDecisionMarketRuleCompletenessScoreResult:
    config_version: str
    redacted_candidate_ref: str
    status: str
    minimum_pass_score: Decimal
    minimum_watch_score: Decimal
    rule_clause_count: Decimal
    minimum_rule_clause_count: Decimal
    rule_clause_score: Decimal
    boundary_condition_count: Decimal
    minimum_boundary_condition_count: Decimal
    boundary_condition_score: Decimal
    disqualifier_clause_count: Decimal
    minimum_disqualifier_clause_count: Decimal
    disqualifier_clause_score: Decimal
    settlement_source_count: Decimal
    minimum_settlement_source_count: Decimal
    settlement_source_score: Decimal
    contradiction_count: Decimal
    maximum_contradiction_count: Decimal
    contradiction_score: Decimal
    rule_specificity_score: Decimal
    minimum_rule_specificity_score: Decimal
    ambiguity_score: Decimal
    maximum_ambiguity_score: Decimal
    ambiguity_component_score: Decimal
    market_rule_completeness_score: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_redacted_candidate_ref(
            "redacted_candidate_ref",
            self.redacted_candidate_ref,
        )
        _require_member("status", self.status, PUBLIC_STATUSES)
        for field_name in (
            "rule_clause_count",
            "minimum_rule_clause_count",
            "boundary_condition_count",
            "minimum_boundary_condition_count",
            "disqualifier_clause_count",
            "minimum_disqualifier_clause_count",
            "settlement_source_count",
            "minimum_settlement_source_count",
            "contradiction_count",
            "maximum_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rule_clause_score",
            "minimum_pass_score",
            "minimum_watch_score",
            "boundary_condition_score",
            "disqualifier_clause_score",
            "settlement_source_score",
            "contradiction_score",
            "rule_specificity_score",
            "minimum_rule_specificity_score",
            "ambiguity_score",
            "maximum_ambiguity_score",
            "ambiguity_component_score",
            "market_rule_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_rule_clause_count",
            "minimum_boundary_condition_count",
            "minimum_disqualifier_clause_count",
            "minimum_settlement_source_count",
        ):
            if getattr(self, field_name) <= ZERO:
                raise ValueError(f"{field_name} must be positive")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_result_consistency(self)
        _validate_result_digest(self)
        _require_hard_flags("score_result", self)


def score_candidate_decision_market_rule_completeness(
    candidate_state: CandidateDecisionMarketRuleCompletenessScoreInput,
    config: CandidateDecisionMarketRuleCompletenessScoreConfig,
) -> CandidateDecisionMarketRuleCompletenessScoreResult:
    """Score one candidate's rule completeness without side effects."""

    _require_exact_type(
        "candidate_state",
        candidate_state,
        CandidateDecisionMarketRuleCompletenessScoreInput,
    )
    _require_exact_type(
        "config",
        config,
        CandidateDecisionMarketRuleCompletenessScoreConfig,
    )

    rule_clause_score = _capped_ratio_from_counts(
        candidate_state.rule_clause_count,
        config.minimum_rule_clause_count,
    )
    boundary_condition_score = _capped_ratio_from_counts(
        candidate_state.boundary_condition_count,
        config.minimum_boundary_condition_count,
    )
    disqualifier_clause_score = _capped_ratio_from_counts(
        candidate_state.disqualifier_clause_count,
        config.minimum_disqualifier_clause_count,
    )
    settlement_source_score = _capped_ratio_from_counts(
        candidate_state.settlement_source_count,
        config.minimum_settlement_source_count,
    )
    contradiction_score = _contradiction_component_score(
        candidate_state.contradiction_count,
        config.maximum_contradiction_count,
    )
    ambiguity_component_score = _inverse_probability_score(
        candidate_state.ambiguity_score,
    )
    composite_score = _quantize_decimal(
        "market_rule_completeness_score",
        (
            rule_clause_score * config.rule_clause_weight
            + boundary_condition_score * config.boundary_condition_weight
            + disqualifier_clause_score * config.disqualifier_clause_weight
            + settlement_source_score * config.settlement_source_weight
            + contradiction_score * config.contradiction_weight
            + candidate_state.rule_specificity_score * config.rule_specificity_weight
            + ambiguity_component_score * config.ambiguity_weight
        ),
    )
    status = _public_status(
        market_rule_completeness_score=composite_score,
        settlement_source_count=candidate_state.settlement_source_count,
        minimum_settlement_source_count=config.minimum_settlement_source_count,
        contradiction_count=candidate_state.contradiction_count,
        maximum_contradiction_count=config.maximum_contradiction_count,
        minimum_pass_score=config.minimum_pass_score,
        minimum_watch_score=config.minimum_watch_score,
    )
    reason_codes = _result_reason_codes(
        status=status,
        rule_clause_count=candidate_state.rule_clause_count,
        minimum_rule_clause_count=config.minimum_rule_clause_count,
        boundary_condition_count=candidate_state.boundary_condition_count,
        minimum_boundary_condition_count=config.minimum_boundary_condition_count,
        disqualifier_clause_count=candidate_state.disqualifier_clause_count,
        minimum_disqualifier_clause_count=config.minimum_disqualifier_clause_count,
        settlement_source_count=candidate_state.settlement_source_count,
        minimum_settlement_source_count=config.minimum_settlement_source_count,
        contradiction_count=candidate_state.contradiction_count,
        maximum_contradiction_count=config.maximum_contradiction_count,
        rule_specificity_score=candidate_state.rule_specificity_score,
        minimum_rule_specificity_score=config.minimum_rule_specificity_score,
        ambiguity_score=candidate_state.ambiguity_score,
        maximum_ambiguity_score=config.maximum_ambiguity_score,
    )
    validation_digest = _result_validation_digest(
        config_version=config.config_version,
        redacted_candidate_ref=candidate_state.redacted_candidate_ref,
        status=status,
        rule_clause_count=candidate_state.rule_clause_count,
        minimum_rule_clause_count=config.minimum_rule_clause_count,
        rule_clause_score=rule_clause_score,
        minimum_pass_score=config.minimum_pass_score,
        minimum_watch_score=config.minimum_watch_score,
        boundary_condition_count=candidate_state.boundary_condition_count,
        minimum_boundary_condition_count=config.minimum_boundary_condition_count,
        boundary_condition_score=boundary_condition_score,
        disqualifier_clause_count=candidate_state.disqualifier_clause_count,
        minimum_disqualifier_clause_count=config.minimum_disqualifier_clause_count,
        disqualifier_clause_score=disqualifier_clause_score,
        settlement_source_count=candidate_state.settlement_source_count,
        minimum_settlement_source_count=config.minimum_settlement_source_count,
        settlement_source_score=settlement_source_score,
        contradiction_count=candidate_state.contradiction_count,
        maximum_contradiction_count=config.maximum_contradiction_count,
        contradiction_score=contradiction_score,
        rule_specificity_score=candidate_state.rule_specificity_score,
        minimum_rule_specificity_score=config.minimum_rule_specificity_score,
        ambiguity_score=candidate_state.ambiguity_score,
        maximum_ambiguity_score=config.maximum_ambiguity_score,
        ambiguity_component_score=ambiguity_component_score,
        market_rule_completeness_score=composite_score,
        reason_codes=reason_codes,
    )

    return CandidateDecisionMarketRuleCompletenessScoreResult(
        config_version=config.config_version,
        redacted_candidate_ref=candidate_state.redacted_candidate_ref,
        status=status,
        minimum_pass_score=config.minimum_pass_score,
        minimum_watch_score=config.minimum_watch_score,
        rule_clause_count=candidate_state.rule_clause_count,
        minimum_rule_clause_count=config.minimum_rule_clause_count,
        rule_clause_score=rule_clause_score,
        boundary_condition_count=candidate_state.boundary_condition_count,
        minimum_boundary_condition_count=config.minimum_boundary_condition_count,
        boundary_condition_score=boundary_condition_score,
        disqualifier_clause_count=candidate_state.disqualifier_clause_count,
        minimum_disqualifier_clause_count=config.minimum_disqualifier_clause_count,
        disqualifier_clause_score=disqualifier_clause_score,
        settlement_source_count=candidate_state.settlement_source_count,
        minimum_settlement_source_count=config.minimum_settlement_source_count,
        settlement_source_score=settlement_source_score,
        contradiction_count=candidate_state.contradiction_count,
        maximum_contradiction_count=config.maximum_contradiction_count,
        contradiction_score=contradiction_score,
        rule_specificity_score=candidate_state.rule_specificity_score,
        minimum_rule_specificity_score=config.minimum_rule_specificity_score,
        ambiguity_score=candidate_state.ambiguity_score,
        maximum_ambiguity_score=config.maximum_ambiguity_score,
        ambiguity_component_score=ambiguity_component_score,
        market_rule_completeness_score=composite_score,
        reason_codes=reason_codes,
        validation_digest=validation_digest,
    )


def candidate_decision_market_rule_completeness_score_payload(
    score_result: CandidateDecisionMarketRuleCompletenessScoreResult,
) -> dict[str, object]:
    if type(score_result) is not CandidateDecisionMarketRuleCompletenessScoreResult:
        raise ValueError(
            "score_result must be a CandidateDecisionMarketRuleCompletenessScoreResult",
        )
    _require_hard_flags("score_result", score_result)
    _validate_result_consistency(score_result)
    _validate_result_digest(score_result)
    _reject_unsafe_public_payload("score_result", score_result)
    payload = {
        "config_version": score_result.config_version,
        "redacted_candidate_ref": score_result.redacted_candidate_ref,
        "status": score_result.status,
        "minimum_pass_score": _decimal_payload(score_result.minimum_pass_score),
        "minimum_watch_score": _decimal_payload(score_result.minimum_watch_score),
        "rule_clause_count": _decimal_payload(score_result.rule_clause_count),
        "minimum_rule_clause_count": _decimal_payload(
            score_result.minimum_rule_clause_count,
        ),
        "rule_clause_score": _decimal_payload(score_result.rule_clause_score),
        "boundary_condition_count": _decimal_payload(
            score_result.boundary_condition_count,
        ),
        "minimum_boundary_condition_count": _decimal_payload(
            score_result.minimum_boundary_condition_count,
        ),
        "boundary_condition_score": _decimal_payload(
            score_result.boundary_condition_score,
        ),
        "disqualifier_clause_count": _decimal_payload(
            score_result.disqualifier_clause_count,
        ),
        "minimum_disqualifier_clause_count": _decimal_payload(
            score_result.minimum_disqualifier_clause_count,
        ),
        "disqualifier_clause_score": _decimal_payload(
            score_result.disqualifier_clause_score,
        ),
        "settlement_source_count": _decimal_payload(
            score_result.settlement_source_count,
        ),
        "minimum_settlement_source_count": _decimal_payload(
            score_result.minimum_settlement_source_count,
        ),
        "settlement_source_score": _decimal_payload(
            score_result.settlement_source_score,
        ),
        "contradiction_count": _decimal_payload(score_result.contradiction_count),
        "maximum_contradiction_count": _decimal_payload(
            score_result.maximum_contradiction_count,
        ),
        "contradiction_score": _decimal_payload(score_result.contradiction_score),
        "rule_specificity_score": _decimal_payload(
            score_result.rule_specificity_score,
        ),
        "minimum_rule_specificity_score": _decimal_payload(
            score_result.minimum_rule_specificity_score,
        ),
        "ambiguity_score": _decimal_payload(score_result.ambiguity_score),
        "maximum_ambiguity_score": _decimal_payload(
            score_result.maximum_ambiguity_score,
        ),
        "ambiguity_component_score": _decimal_payload(
            score_result.ambiguity_component_score,
        ),
        "market_rule_completeness_score": _decimal_payload(
            score_result.market_rule_completeness_score,
        ),
        "reason_codes": list(score_result.reason_codes),
        "validation_digest": score_result.validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_public_payload("market rule completeness payload", payload)
    return payload


def _weight_sum(config: CandidateDecisionMarketRuleCompletenessScoreConfig) -> Decimal:
    return _quantize_decimal(
        "weights",
        (
            config.rule_clause_weight
            + config.boundary_condition_weight
            + config.disqualifier_clause_weight
            + config.settlement_source_weight
            + config.contradiction_weight
            + config.rule_specificity_weight
            + config.ambiguity_weight
        ),
    )


def _capped_ratio_from_counts(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _quantize_decimal("ratio", numerator / denominator)
    if ratio > ONE:
        return ONE
    return ratio


def _contradiction_component_score(value: Decimal, limit: Decimal) -> Decimal:
    if value > limit:
        return ZERO
    return ONE


def _inverse_probability_score(value: Decimal) -> Decimal:
    return _quantize_decimal("inverse_probability_score", ONE - value)


def _public_status(
    *,
    market_rule_completeness_score: Decimal,
    settlement_source_count: Decimal,
    minimum_settlement_source_count: Decimal,
    contradiction_count: Decimal,
    maximum_contradiction_count: Decimal,
    minimum_pass_score: Decimal,
    minimum_watch_score: Decimal,
) -> str:
    if (
        settlement_source_count < minimum_settlement_source_count
        or contradiction_count > maximum_contradiction_count
    ):
        return "block"
    if market_rule_completeness_score >= minimum_pass_score:
        return "pass"
    if market_rule_completeness_score >= minimum_watch_score:
        return "watch"
    return "block"


def _result_reason_codes(
    *,
    status: str,
    rule_clause_count: Decimal,
    minimum_rule_clause_count: Decimal,
    boundary_condition_count: Decimal,
    minimum_boundary_condition_count: Decimal,
    disqualifier_clause_count: Decimal,
    minimum_disqualifier_clause_count: Decimal,
    settlement_source_count: Decimal,
    minimum_settlement_source_count: Decimal,
    contradiction_count: Decimal,
    maximum_contradiction_count: Decimal,
    rule_specificity_score: Decimal,
    minimum_rule_specificity_score: Decimal,
    ambiguity_score: Decimal,
    maximum_ambiguity_score: Decimal,
) -> tuple[str, ...]:
    reason_codes = [f"{STATUS_REASON_PREFIX}{status}"]
    if rule_clause_count < minimum_rule_clause_count:
        reason_codes.append("rule_clause_count_below_minimum")
    if boundary_condition_count < minimum_boundary_condition_count:
        reason_codes.append("boundary_condition_count_below_minimum")
    if disqualifier_clause_count < minimum_disqualifier_clause_count:
        reason_codes.append("disqualifier_clause_count_below_minimum")
    if settlement_source_count < minimum_settlement_source_count:
        reason_codes.append("settlement_source_count_below_minimum")
    if contradiction_count > maximum_contradiction_count:
        reason_codes.append("contradiction_count_above_limit")
    if rule_specificity_score < minimum_rule_specificity_score:
        reason_codes.append("rule_specificity_score_below_minimum")
    if ambiguity_score > maximum_ambiguity_score:
        reason_codes.append("ambiguity_score_above_limit")
    if len(reason_codes) == 1:
        reason_codes.append("market_rule_completeness_sufficient")
    return tuple(reason_codes)


def _validate_result_consistency(
    score_result: CandidateDecisionMarketRuleCompletenessScoreResult,
) -> None:
    expected_rule_clause_score = _capped_ratio_from_counts(
        score_result.rule_clause_count,
        score_result.minimum_rule_clause_count,
    )
    if score_result.rule_clause_score != expected_rule_clause_score:
        raise ValueError("rule_clause_score must match rule_clause_count")
    expected_boundary_condition_score = _capped_ratio_from_counts(
        score_result.boundary_condition_count,
        score_result.minimum_boundary_condition_count,
    )
    if score_result.boundary_condition_score != expected_boundary_condition_score:
        raise ValueError(
            "boundary_condition_score must match boundary_condition_count",
        )
    expected_disqualifier_clause_score = _capped_ratio_from_counts(
        score_result.disqualifier_clause_count,
        score_result.minimum_disqualifier_clause_count,
    )
    if score_result.disqualifier_clause_score != expected_disqualifier_clause_score:
        raise ValueError(
            "disqualifier_clause_score must match disqualifier_clause_count",
        )
    expected_settlement_source_score = _capped_ratio_from_counts(
        score_result.settlement_source_count,
        score_result.minimum_settlement_source_count,
    )
    if score_result.settlement_source_score != expected_settlement_source_score:
        raise ValueError("settlement_source_score must match settlement_source_count")
    expected_contradiction_score = _contradiction_component_score(
        score_result.contradiction_count,
        score_result.maximum_contradiction_count,
    )
    if score_result.contradiction_score != expected_contradiction_score:
        raise ValueError("contradiction_score must match contradiction_count")
    expected_ambiguity_component_score = _inverse_probability_score(
        score_result.ambiguity_score,
    )
    if score_result.ambiguity_component_score != expected_ambiguity_component_score:
        raise ValueError("ambiguity_component_score must match ambiguity_score")
    expected_status = _public_status(
        market_rule_completeness_score=score_result.market_rule_completeness_score,
        settlement_source_count=score_result.settlement_source_count,
        minimum_settlement_source_count=score_result.minimum_settlement_source_count,
        contradiction_count=score_result.contradiction_count,
        maximum_contradiction_count=score_result.maximum_contradiction_count,
        minimum_pass_score=score_result.minimum_pass_score,
        minimum_watch_score=score_result.minimum_watch_score,
    )
    if score_result.status != expected_status:
        raise ValueError("status must match scoring thresholds")
    expected_reason_codes = _result_reason_codes(
        status=score_result.status,
        rule_clause_count=score_result.rule_clause_count,
        minimum_rule_clause_count=score_result.minimum_rule_clause_count,
        boundary_condition_count=score_result.boundary_condition_count,
        minimum_boundary_condition_count=score_result.minimum_boundary_condition_count,
        disqualifier_clause_count=score_result.disqualifier_clause_count,
        minimum_disqualifier_clause_count=score_result.minimum_disqualifier_clause_count,
        settlement_source_count=score_result.settlement_source_count,
        minimum_settlement_source_count=score_result.minimum_settlement_source_count,
        contradiction_count=score_result.contradiction_count,
        maximum_contradiction_count=score_result.maximum_contradiction_count,
        rule_specificity_score=score_result.rule_specificity_score,
        minimum_rule_specificity_score=score_result.minimum_rule_specificity_score,
        ambiguity_score=score_result.ambiguity_score,
        maximum_ambiguity_score=score_result.maximum_ambiguity_score,
    )
    if score_result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match score_result")


def _validate_result_digest(
    score_result: CandidateDecisionMarketRuleCompletenessScoreResult,
) -> None:
    if score_result.validation_digest != _result_validation_digest(
        config_version=score_result.config_version,
        redacted_candidate_ref=score_result.redacted_candidate_ref,
        status=score_result.status,
        minimum_pass_score=score_result.minimum_pass_score,
        minimum_watch_score=score_result.minimum_watch_score,
        rule_clause_count=score_result.rule_clause_count,
        minimum_rule_clause_count=score_result.minimum_rule_clause_count,
        rule_clause_score=score_result.rule_clause_score,
        boundary_condition_count=score_result.boundary_condition_count,
        minimum_boundary_condition_count=score_result.minimum_boundary_condition_count,
        boundary_condition_score=score_result.boundary_condition_score,
        disqualifier_clause_count=score_result.disqualifier_clause_count,
        minimum_disqualifier_clause_count=score_result.minimum_disqualifier_clause_count,
        disqualifier_clause_score=score_result.disqualifier_clause_score,
        settlement_source_count=score_result.settlement_source_count,
        minimum_settlement_source_count=score_result.minimum_settlement_source_count,
        settlement_source_score=score_result.settlement_source_score,
        contradiction_count=score_result.contradiction_count,
        maximum_contradiction_count=score_result.maximum_contradiction_count,
        contradiction_score=score_result.contradiction_score,
        rule_specificity_score=score_result.rule_specificity_score,
        minimum_rule_specificity_score=score_result.minimum_rule_specificity_score,
        ambiguity_score=score_result.ambiguity_score,
        maximum_ambiguity_score=score_result.maximum_ambiguity_score,
        ambiguity_component_score=score_result.ambiguity_component_score,
        market_rule_completeness_score=score_result.market_rule_completeness_score,
        reason_codes=score_result.reason_codes,
    ):
        raise ValueError("validation_digest must match score_result")


def _result_validation_digest(
    *,
    config_version: str,
    redacted_candidate_ref: str,
    status: str,
    minimum_pass_score: Decimal,
    minimum_watch_score: Decimal,
    rule_clause_count: Decimal,
    minimum_rule_clause_count: Decimal,
    rule_clause_score: Decimal,
    boundary_condition_count: Decimal,
    minimum_boundary_condition_count: Decimal,
    boundary_condition_score: Decimal,
    disqualifier_clause_count: Decimal,
    minimum_disqualifier_clause_count: Decimal,
    disqualifier_clause_score: Decimal,
    settlement_source_count: Decimal,
    minimum_settlement_source_count: Decimal,
    settlement_source_score: Decimal,
    contradiction_count: Decimal,
    maximum_contradiction_count: Decimal,
    contradiction_score: Decimal,
    rule_specificity_score: Decimal,
    minimum_rule_specificity_score: Decimal,
    ambiguity_score: Decimal,
    maximum_ambiguity_score: Decimal,
    ambiguity_component_score: Decimal,
    market_rule_completeness_score: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    digest_parts = (
        VALIDATION_DIGEST_ALGORITHM,
        config_version,
        redacted_candidate_ref,
        status,
        _decimal_payload(minimum_pass_score),
        _decimal_payload(minimum_watch_score),
        _decimal_payload(rule_clause_count),
        _decimal_payload(minimum_rule_clause_count),
        _decimal_payload(rule_clause_score),
        _decimal_payload(boundary_condition_count),
        _decimal_payload(minimum_boundary_condition_count),
        _decimal_payload(boundary_condition_score),
        _decimal_payload(disqualifier_clause_count),
        _decimal_payload(minimum_disqualifier_clause_count),
        _decimal_payload(disqualifier_clause_score),
        _decimal_payload(settlement_source_count),
        _decimal_payload(minimum_settlement_source_count),
        _decimal_payload(settlement_source_score),
        _decimal_payload(contradiction_count),
        _decimal_payload(maximum_contradiction_count),
        _decimal_payload(contradiction_score),
        _decimal_payload(rule_specificity_score),
        _decimal_payload(minimum_rule_specificity_score),
        _decimal_payload(ambiguity_score),
        _decimal_payload(maximum_ambiguity_score),
        _decimal_payload(ambiguity_component_score),
        _decimal_payload(market_rule_completeness_score),
        "\x1f".join(reason_codes),
        "paper_only=True",
        "report_only=True",
        "readonly=True",
    )
    return hashlib.sha256("\n".join(digest_parts).encode("utf-8")).hexdigest()


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_hard_flags(field_name, value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        expected = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {expected}")


def _require_redacted_candidate_ref(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not value.startswith("candidate_ref_"):
        raise ValueError(f"{field_name} must be redacted")
    _reject_unsafe_public_value(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a validation digest")
    if len(value) != 64 or any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for key in _iter_payload_keys(payload):
        lowered_key = key.lower()
        if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe public payload field in {label}: {key}")
    _reject_unsafe_public_values(label, payload)


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        keys: list[str] = []
        for field in fields(value):
            keys.append(field.name)
            keys.extend(_iter_payload_keys(getattr(value, field.name)))
        return tuple(keys)
    if isinstance(value, dict):
        keys = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _reject_unsafe_public_values(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_values(label, getattr(value, field.name))
        return
    if type(value) is str:
        _reject_unsafe_public_value(label, value)
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_values(label, item)


def _reject_unsafe_public_value(label: str, value: str) -> None:
    lowered_value = value.lower()
    if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"unsafe public payload value in {label}")
