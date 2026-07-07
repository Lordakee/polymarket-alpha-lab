"""Pure report-only candidate decision falsifiability scoring."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_FALSIFIABILITY_SCORE_CONFIG_VERSION",
    "CandidateDecisionFalsifiabilityScoreConfig",
    "CandidateDecisionFalsifiabilityScoreInput",
    "CandidateDecisionFalsifiabilityScoreResult",
    "score_candidate_decision_falsifiability",
    "candidate_decision_falsifiability_score_payload",
)


DEFAULT_CANDIDATE_DECISION_FALSIFIABILITY_SCORE_CONFIG_VERSION = (
    "candidate-decision-falsifiability-score-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_REASON_PREFIX = "candidate_decision_falsifiability_"
VALIDATION_DIGEST_ALGORITHM = "candidate-decision-falsifiability-score-v0-sha256"
HEX_DIGITS = frozenset("0123456789abcdef")

UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
    "au" + "th",
    "candidate" + "_id",
    "condition" + "_id",
    "d" + "sn",
    "market" + "_id",
    "market" + "_slug",
    "market" + "question",
    "position" + "_size",
    "position" + "_sizing",
    "question",
    "raw" + "_candidate",
    "sec" + "ret",
    "slug",
    "source" + "_ref",
    "source" + "_refs",
    "source" + "_text",
    "source" + "_url",
    "source" + "_uri",
    "sourceref",
    "sourcerefs",
    "sourcetext",
    "sourceurl",
    "sourceuri",
    "ta" + "ble",
    "tok" + "en",
    "u" + "rl",
    "wall" + "et",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "://",
    "au" + "th",
    "b" + "uy",
    "candidate" + "_id",
    "d" + "sn",
    "from ",
    "ht" + "tp",
    "market-question",
    "market" + "_slug",
    "my" + "sql",
    "or" + "der",
    "polymarket",
    "position-size",
    "position" + "_size",
    "position sizing",
    "position" + "sizing",
    "post" + "gres",
    "question=",
    "recommend" + "ation",
    "recommend ",
    "recommended",
    "schema:",
    "sec" + "ret",
    "select ",
    "s" + "ell",
    "source-ref",
    "source" + "_ref",
    "source text",
    "source" + "_text",
    "source" + "_url",
    "supa" + "base",
    "table:",
    "tok" + "en",
    "tr" + "ade",
    "url=",
    "wall" + "et",
    "www.",
)


@dataclass(frozen=True)
class CandidateDecisionFalsifiabilityScoreConfig:
    config_version: str = DEFAULT_CANDIDATE_DECISION_FALSIFIABILITY_SCORE_CONFIG_VERSION
    minimum_pass_score: Decimal = Decimal("0.800000")
    minimum_watch_score: Decimal = Decimal("0.550000")
    minimum_observable_condition_count: Decimal = Decimal("1")
    minimum_measurable_threshold_count: Decimal = Decimal("1")
    maximum_pass_subjective_clause_count: Decimal = Decimal("0")
    maximum_watch_subjective_clause_count: Decimal = Decimal("2")
    maximum_pass_oracle_dependency_score: Decimal = Decimal("0.300000")
    maximum_watch_oracle_dependency_score: Decimal = Decimal("0.600000")
    maximum_pass_dispute_risk_score: Decimal = Decimal("0.250000")
    maximum_watch_dispute_risk_score: Decimal = Decimal("0.600000")
    minimum_pass_evidence_verifiability_score: Decimal = Decimal("0.750000")
    minimum_watch_evidence_verifiability_score: Decimal = Decimal("0.500000")
    observable_condition_weight: Decimal = Decimal("0.200000")
    measurable_threshold_weight: Decimal = Decimal("0.200000")
    subjective_clause_weight: Decimal = Decimal("0.150000")
    oracle_dependency_weight: Decimal = Decimal("0.150000")
    dispute_risk_weight: Decimal = Decimal("0.150000")
    evidence_verifiability_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionFalsifiabilityScoreConfig:
            raise ValueError("config must be a CandidateDecisionFalsifiabilityScoreConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_pass_score",
            "minimum_watch_score",
            "maximum_pass_oracle_dependency_score",
            "maximum_watch_oracle_dependency_score",
            "maximum_pass_dispute_risk_score",
            "maximum_watch_dispute_risk_score",
            "minimum_pass_evidence_verifiability_score",
            "minimum_watch_evidence_verifiability_score",
            "observable_condition_weight",
            "measurable_threshold_weight",
            "subjective_clause_weight",
            "oracle_dependency_weight",
            "dispute_risk_weight",
            "evidence_verifiability_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_observable_condition_count",
            "minimum_measurable_threshold_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_pass_subjective_clause_count",
            "maximum_watch_subjective_clause_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class CandidateDecisionFalsifiabilityScoreInput:
    redacted_candidate_ref: str
    observable_condition_count: Decimal
    measurable_threshold_count: Decimal
    subjective_clause_count: Decimal
    oracle_dependency_score: Decimal
    dispute_risk_score: Decimal
    evidence_verifiability_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionFalsifiabilityScoreInput:
            raise ValueError("candidate_state must be a CandidateDecisionFalsifiabilityScoreInput")
        _require_redacted_candidate_ref("redacted_candidate_ref", self.redacted_candidate_ref)
        for field_name in (
            "observable_condition_count",
            "measurable_threshold_count",
            "subjective_clause_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "oracle_dependency_score",
            "dispute_risk_score",
            "evidence_verifiability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("candidate_state", self)


@dataclass(frozen=True)
class CandidateDecisionFalsifiabilityScoreResult:
    config_version: str
    redacted_candidate_ref: str
    status: str
    minimum_pass_score: Decimal
    minimum_watch_score: Decimal
    observable_condition_count: Decimal
    minimum_observable_condition_count: Decimal
    observable_condition_score: Decimal
    observable_condition_weight: Decimal
    measurable_threshold_count: Decimal
    minimum_measurable_threshold_count: Decimal
    measurable_threshold_score: Decimal
    measurable_threshold_weight: Decimal
    subjective_clause_count: Decimal
    maximum_pass_subjective_clause_count: Decimal
    maximum_watch_subjective_clause_count: Decimal
    subjective_clause_score: Decimal
    subjective_clause_weight: Decimal
    oracle_dependency_score: Decimal
    maximum_pass_oracle_dependency_score: Decimal
    maximum_watch_oracle_dependency_score: Decimal
    oracle_dependency_component_score: Decimal
    oracle_dependency_weight: Decimal
    dispute_risk_score: Decimal
    maximum_pass_dispute_risk_score: Decimal
    maximum_watch_dispute_risk_score: Decimal
    dispute_risk_component_score: Decimal
    dispute_risk_weight: Decimal
    evidence_verifiability_score: Decimal
    minimum_pass_evidence_verifiability_score: Decimal
    minimum_watch_evidence_verifiability_score: Decimal
    evidence_verifiability_weight: Decimal
    falsifiability_score: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionFalsifiabilityScoreResult:
            raise ValueError("score_result must be a CandidateDecisionFalsifiabilityScoreResult")
        _require_canonical_string("config_version", self.config_version)
        _require_redacted_candidate_ref("redacted_candidate_ref", self.redacted_candidate_ref)
        _require_member("status", self.status, PUBLIC_STATUSES)
        for field_name in (
            "observable_condition_count",
            "minimum_observable_condition_count",
            "measurable_threshold_count",
            "minimum_measurable_threshold_count",
            "subjective_clause_count",
            "maximum_pass_subjective_clause_count",
            "maximum_watch_subjective_clause_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_score",
            "minimum_watch_score",
            "observable_condition_score",
            "observable_condition_weight",
            "measurable_threshold_score",
            "measurable_threshold_weight",
            "subjective_clause_score",
            "subjective_clause_weight",
            "oracle_dependency_score",
            "maximum_pass_oracle_dependency_score",
            "maximum_watch_oracle_dependency_score",
            "oracle_dependency_component_score",
            "oracle_dependency_weight",
            "dispute_risk_score",
            "maximum_pass_dispute_risk_score",
            "maximum_watch_dispute_risk_score",
            "dispute_risk_component_score",
            "dispute_risk_weight",
            "evidence_verifiability_score",
            "minimum_pass_evidence_verifiability_score",
            "minimum_watch_evidence_verifiability_score",
            "evidence_verifiability_weight",
            "falsifiability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
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


def score_candidate_decision_falsifiability(
    candidate_state: CandidateDecisionFalsifiabilityScoreInput,
    config: CandidateDecisionFalsifiabilityScoreConfig,
) -> CandidateDecisionFalsifiabilityScoreResult:
    """Score whether a candidate can be objectively falsified, without side effects."""

    _require_exact_type(
        "candidate_state",
        candidate_state,
        CandidateDecisionFalsifiabilityScoreInput,
    )
    _require_exact_type("config", config, CandidateDecisionFalsifiabilityScoreConfig)

    observable_condition_score = _capped_ratio_from_counts(
        candidate_state.observable_condition_count,
        config.minimum_observable_condition_count,
    )
    measurable_threshold_score = _capped_ratio_from_counts(
        candidate_state.measurable_threshold_count,
        config.minimum_measurable_threshold_count,
    )
    subjective_clause_score = _subjective_clause_component_score(
        candidate_state.subjective_clause_count,
        config.maximum_pass_subjective_clause_count,
        config.maximum_watch_subjective_clause_count,
    )
    oracle_dependency_component_score = _inverse_probability_score(
        candidate_state.oracle_dependency_score,
    )
    dispute_risk_component_score = _inverse_probability_score(
        candidate_state.dispute_risk_score,
    )
    falsifiability_score = _quantize_decimal(
        "falsifiability_score",
        (
            observable_condition_score * config.observable_condition_weight
            + measurable_threshold_score * config.measurable_threshold_weight
            + subjective_clause_score * config.subjective_clause_weight
            + oracle_dependency_component_score * config.oracle_dependency_weight
            + dispute_risk_component_score * config.dispute_risk_weight
            + candidate_state.evidence_verifiability_score
            * config.evidence_verifiability_weight
        ),
    )
    status = _public_status(
        falsifiability_score=falsifiability_score,
        observable_condition_count=candidate_state.observable_condition_count,
        minimum_observable_condition_count=config.minimum_observable_condition_count,
        measurable_threshold_count=candidate_state.measurable_threshold_count,
        minimum_measurable_threshold_count=config.minimum_measurable_threshold_count,
        subjective_clause_count=candidate_state.subjective_clause_count,
        maximum_pass_subjective_clause_count=config.maximum_pass_subjective_clause_count,
        maximum_watch_subjective_clause_count=config.maximum_watch_subjective_clause_count,
        oracle_dependency_score=candidate_state.oracle_dependency_score,
        maximum_pass_oracle_dependency_score=config.maximum_pass_oracle_dependency_score,
        maximum_watch_oracle_dependency_score=config.maximum_watch_oracle_dependency_score,
        dispute_risk_score=candidate_state.dispute_risk_score,
        maximum_pass_dispute_risk_score=config.maximum_pass_dispute_risk_score,
        maximum_watch_dispute_risk_score=config.maximum_watch_dispute_risk_score,
        evidence_verifiability_score=candidate_state.evidence_verifiability_score,
        minimum_pass_evidence_verifiability_score=(
            config.minimum_pass_evidence_verifiability_score
        ),
        minimum_watch_evidence_verifiability_score=(
            config.minimum_watch_evidence_verifiability_score
        ),
        minimum_pass_score=config.minimum_pass_score,
        minimum_watch_score=config.minimum_watch_score,
    )
    reason_codes = _result_reason_codes(
        status=status,
        observable_condition_count=candidate_state.observable_condition_count,
        minimum_observable_condition_count=config.minimum_observable_condition_count,
        measurable_threshold_count=candidate_state.measurable_threshold_count,
        minimum_measurable_threshold_count=config.minimum_measurable_threshold_count,
        subjective_clause_count=candidate_state.subjective_clause_count,
        maximum_pass_subjective_clause_count=config.maximum_pass_subjective_clause_count,
        maximum_watch_subjective_clause_count=config.maximum_watch_subjective_clause_count,
        oracle_dependency_score=candidate_state.oracle_dependency_score,
        maximum_pass_oracle_dependency_score=config.maximum_pass_oracle_dependency_score,
        maximum_watch_oracle_dependency_score=config.maximum_watch_oracle_dependency_score,
        dispute_risk_score=candidate_state.dispute_risk_score,
        maximum_pass_dispute_risk_score=config.maximum_pass_dispute_risk_score,
        maximum_watch_dispute_risk_score=config.maximum_watch_dispute_risk_score,
        evidence_verifiability_score=candidate_state.evidence_verifiability_score,
        minimum_pass_evidence_verifiability_score=(
            config.minimum_pass_evidence_verifiability_score
        ),
        minimum_watch_evidence_verifiability_score=(
            config.minimum_watch_evidence_verifiability_score
        ),
    )
    validation_digest = _result_validation_digest(
        config_version=config.config_version,
        redacted_candidate_ref=candidate_state.redacted_candidate_ref,
        status=status,
        minimum_pass_score=config.minimum_pass_score,
        minimum_watch_score=config.minimum_watch_score,
        observable_condition_count=candidate_state.observable_condition_count,
        minimum_observable_condition_count=config.minimum_observable_condition_count,
        observable_condition_score=observable_condition_score,
        observable_condition_weight=config.observable_condition_weight,
        measurable_threshold_count=candidate_state.measurable_threshold_count,
        minimum_measurable_threshold_count=config.minimum_measurable_threshold_count,
        measurable_threshold_score=measurable_threshold_score,
        measurable_threshold_weight=config.measurable_threshold_weight,
        subjective_clause_count=candidate_state.subjective_clause_count,
        maximum_pass_subjective_clause_count=config.maximum_pass_subjective_clause_count,
        maximum_watch_subjective_clause_count=config.maximum_watch_subjective_clause_count,
        subjective_clause_score=subjective_clause_score,
        subjective_clause_weight=config.subjective_clause_weight,
        oracle_dependency_score=candidate_state.oracle_dependency_score,
        maximum_pass_oracle_dependency_score=config.maximum_pass_oracle_dependency_score,
        maximum_watch_oracle_dependency_score=config.maximum_watch_oracle_dependency_score,
        oracle_dependency_component_score=oracle_dependency_component_score,
        oracle_dependency_weight=config.oracle_dependency_weight,
        dispute_risk_score=candidate_state.dispute_risk_score,
        maximum_pass_dispute_risk_score=config.maximum_pass_dispute_risk_score,
        maximum_watch_dispute_risk_score=config.maximum_watch_dispute_risk_score,
        dispute_risk_component_score=dispute_risk_component_score,
        dispute_risk_weight=config.dispute_risk_weight,
        evidence_verifiability_score=candidate_state.evidence_verifiability_score,
        minimum_pass_evidence_verifiability_score=(
            config.minimum_pass_evidence_verifiability_score
        ),
        minimum_watch_evidence_verifiability_score=(
            config.minimum_watch_evidence_verifiability_score
        ),
        evidence_verifiability_weight=config.evidence_verifiability_weight,
        falsifiability_score=falsifiability_score,
        reason_codes=reason_codes,
    )

    return CandidateDecisionFalsifiabilityScoreResult(
        config_version=config.config_version,
        redacted_candidate_ref=candidate_state.redacted_candidate_ref,
        status=status,
        minimum_pass_score=config.minimum_pass_score,
        minimum_watch_score=config.minimum_watch_score,
        observable_condition_count=candidate_state.observable_condition_count,
        minimum_observable_condition_count=config.minimum_observable_condition_count,
        observable_condition_score=observable_condition_score,
        observable_condition_weight=config.observable_condition_weight,
        measurable_threshold_count=candidate_state.measurable_threshold_count,
        minimum_measurable_threshold_count=config.minimum_measurable_threshold_count,
        measurable_threshold_score=measurable_threshold_score,
        measurable_threshold_weight=config.measurable_threshold_weight,
        subjective_clause_count=candidate_state.subjective_clause_count,
        maximum_pass_subjective_clause_count=config.maximum_pass_subjective_clause_count,
        maximum_watch_subjective_clause_count=config.maximum_watch_subjective_clause_count,
        subjective_clause_score=subjective_clause_score,
        subjective_clause_weight=config.subjective_clause_weight,
        oracle_dependency_score=candidate_state.oracle_dependency_score,
        maximum_pass_oracle_dependency_score=config.maximum_pass_oracle_dependency_score,
        maximum_watch_oracle_dependency_score=config.maximum_watch_oracle_dependency_score,
        oracle_dependency_component_score=oracle_dependency_component_score,
        oracle_dependency_weight=config.oracle_dependency_weight,
        dispute_risk_score=candidate_state.dispute_risk_score,
        maximum_pass_dispute_risk_score=config.maximum_pass_dispute_risk_score,
        maximum_watch_dispute_risk_score=config.maximum_watch_dispute_risk_score,
        dispute_risk_component_score=dispute_risk_component_score,
        dispute_risk_weight=config.dispute_risk_weight,
        evidence_verifiability_score=candidate_state.evidence_verifiability_score,
        minimum_pass_evidence_verifiability_score=(
            config.minimum_pass_evidence_verifiability_score
        ),
        minimum_watch_evidence_verifiability_score=(
            config.minimum_watch_evidence_verifiability_score
        ),
        evidence_verifiability_weight=config.evidence_verifiability_weight,
        falsifiability_score=falsifiability_score,
        reason_codes=reason_codes,
        validation_digest=validation_digest,
    )


def candidate_decision_falsifiability_score_payload(
    score_result: CandidateDecisionFalsifiabilityScoreResult,
) -> dict[str, object]:
    if type(score_result) is not CandidateDecisionFalsifiabilityScoreResult:
        raise ValueError("score_result must be a CandidateDecisionFalsifiabilityScoreResult")
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
        "observable_condition_count": _decimal_payload(
            score_result.observable_condition_count,
        ),
        "minimum_observable_condition_count": _decimal_payload(
            score_result.minimum_observable_condition_count,
        ),
        "observable_condition_score": _decimal_payload(
            score_result.observable_condition_score,
        ),
        "observable_condition_weight": _decimal_payload(
            score_result.observable_condition_weight,
        ),
        "measurable_threshold_count": _decimal_payload(
            score_result.measurable_threshold_count,
        ),
        "minimum_measurable_threshold_count": _decimal_payload(
            score_result.minimum_measurable_threshold_count,
        ),
        "measurable_threshold_score": _decimal_payload(
            score_result.measurable_threshold_score,
        ),
        "measurable_threshold_weight": _decimal_payload(
            score_result.measurable_threshold_weight,
        ),
        "subjective_clause_count": _decimal_payload(
            score_result.subjective_clause_count,
        ),
        "maximum_pass_subjective_clause_count": _decimal_payload(
            score_result.maximum_pass_subjective_clause_count,
        ),
        "maximum_watch_subjective_clause_count": _decimal_payload(
            score_result.maximum_watch_subjective_clause_count,
        ),
        "subjective_clause_score": _decimal_payload(
            score_result.subjective_clause_score,
        ),
        "subjective_clause_weight": _decimal_payload(
            score_result.subjective_clause_weight,
        ),
        "oracle_dependency_score": _decimal_payload(
            score_result.oracle_dependency_score,
        ),
        "maximum_pass_oracle_dependency_score": _decimal_payload(
            score_result.maximum_pass_oracle_dependency_score,
        ),
        "maximum_watch_oracle_dependency_score": _decimal_payload(
            score_result.maximum_watch_oracle_dependency_score,
        ),
        "oracle_dependency_component_score": _decimal_payload(
            score_result.oracle_dependency_component_score,
        ),
        "oracle_dependency_weight": _decimal_payload(
            score_result.oracle_dependency_weight,
        ),
        "dispute_risk_score": _decimal_payload(score_result.dispute_risk_score),
        "maximum_pass_dispute_risk_score": _decimal_payload(
            score_result.maximum_pass_dispute_risk_score,
        ),
        "maximum_watch_dispute_risk_score": _decimal_payload(
            score_result.maximum_watch_dispute_risk_score,
        ),
        "dispute_risk_component_score": _decimal_payload(
            score_result.dispute_risk_component_score,
        ),
        "dispute_risk_weight": _decimal_payload(score_result.dispute_risk_weight),
        "evidence_verifiability_score": _decimal_payload(
            score_result.evidence_verifiability_score,
        ),
        "minimum_pass_evidence_verifiability_score": _decimal_payload(
            score_result.minimum_pass_evidence_verifiability_score,
        ),
        "minimum_watch_evidence_verifiability_score": _decimal_payload(
            score_result.minimum_watch_evidence_verifiability_score,
        ),
        "evidence_verifiability_weight": _decimal_payload(
            score_result.evidence_verifiability_weight,
        ),
        "falsifiability_score": _decimal_payload(score_result.falsifiability_score),
        "reason_codes": list(score_result.reason_codes),
        "validation_digest": score_result.validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_public_payload("falsifiability payload", payload)
    return payload


def _validate_config(config: CandidateDecisionFalsifiabilityScoreConfig) -> None:
    if config.minimum_watch_score > config.minimum_pass_score:
        raise ValueError("minimum_watch_score must be less than or equal to minimum_pass_score")
    if (
        config.maximum_watch_subjective_clause_count
        < config.maximum_pass_subjective_clause_count
    ):
        raise ValueError(
            "maximum_watch_subjective_clause_count must be at least pass limit",
        )
    if config.maximum_watch_oracle_dependency_score < config.maximum_pass_oracle_dependency_score:
        raise ValueError(
            "maximum_watch_oracle_dependency_score must be at least pass limit",
        )
    if config.maximum_watch_dispute_risk_score < config.maximum_pass_dispute_risk_score:
        raise ValueError("maximum_watch_dispute_risk_score must be at least pass limit")
    if (
        config.minimum_watch_evidence_verifiability_score
        > config.minimum_pass_evidence_verifiability_score
    ):
        raise ValueError(
            "minimum_watch_evidence_verifiability_score must be no greater than pass minimum",
        )
    if _weight_sum(config) != ONE:
        raise ValueError("weights must sum to 1.000000")
    _reject_unsafe_public_payload("config", config)


def _weight_sum(config: CandidateDecisionFalsifiabilityScoreConfig) -> Decimal:
    return _quantize_decimal(
        "weights",
        (
            config.observable_condition_weight
            + config.measurable_threshold_weight
            + config.subjective_clause_weight
            + config.oracle_dependency_weight
            + config.dispute_risk_weight
            + config.evidence_verifiability_weight
        ),
    )


def _capped_ratio_from_counts(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _quantize_decimal("ratio", numerator / denominator)
    if ratio > ONE:
        return ONE
    return ratio


def _subjective_clause_component_score(
    value: Decimal,
    pass_limit: Decimal,
    watch_limit: Decimal,
) -> Decimal:
    if value <= pass_limit:
        return ONE
    if value >= watch_limit:
        return ZERO
    if watch_limit == pass_limit:
        return ZERO
    return _quantize_decimal(
        "subjective_clause_score",
        (watch_limit - value) / (watch_limit - pass_limit),
    )


def _inverse_probability_score(value: Decimal) -> Decimal:
    return _quantize_decimal("inverse_probability_score", ONE - value)


def _public_status(
    *,
    falsifiability_score: Decimal,
    observable_condition_count: Decimal,
    minimum_observable_condition_count: Decimal,
    measurable_threshold_count: Decimal,
    minimum_measurable_threshold_count: Decimal,
    subjective_clause_count: Decimal,
    maximum_pass_subjective_clause_count: Decimal,
    maximum_watch_subjective_clause_count: Decimal,
    oracle_dependency_score: Decimal,
    maximum_pass_oracle_dependency_score: Decimal,
    maximum_watch_oracle_dependency_score: Decimal,
    dispute_risk_score: Decimal,
    maximum_pass_dispute_risk_score: Decimal,
    maximum_watch_dispute_risk_score: Decimal,
    evidence_verifiability_score: Decimal,
    minimum_pass_evidence_verifiability_score: Decimal,
    minimum_watch_evidence_verifiability_score: Decimal,
    minimum_pass_score: Decimal,
    minimum_watch_score: Decimal,
) -> str:
    if (
        observable_condition_count < minimum_observable_condition_count
        or measurable_threshold_count < minimum_measurable_threshold_count
        or subjective_clause_count > maximum_watch_subjective_clause_count
        or oracle_dependency_score > maximum_watch_oracle_dependency_score
        or dispute_risk_score > maximum_watch_dispute_risk_score
        or evidence_verifiability_score < minimum_watch_evidence_verifiability_score
    ):
        return "block"
    if (
        falsifiability_score >= minimum_pass_score
        and subjective_clause_count <= maximum_pass_subjective_clause_count
        and oracle_dependency_score <= maximum_pass_oracle_dependency_score
        and dispute_risk_score <= maximum_pass_dispute_risk_score
        and evidence_verifiability_score >= minimum_pass_evidence_verifiability_score
    ):
        return "pass"
    if falsifiability_score >= minimum_watch_score:
        return "watch"
    return "block"


def _result_reason_codes(
    *,
    status: str,
    observable_condition_count: Decimal,
    minimum_observable_condition_count: Decimal,
    measurable_threshold_count: Decimal,
    minimum_measurable_threshold_count: Decimal,
    subjective_clause_count: Decimal,
    maximum_pass_subjective_clause_count: Decimal,
    maximum_watch_subjective_clause_count: Decimal,
    oracle_dependency_score: Decimal,
    maximum_pass_oracle_dependency_score: Decimal,
    maximum_watch_oracle_dependency_score: Decimal,
    dispute_risk_score: Decimal,
    maximum_pass_dispute_risk_score: Decimal,
    maximum_watch_dispute_risk_score: Decimal,
    evidence_verifiability_score: Decimal,
    minimum_pass_evidence_verifiability_score: Decimal,
    minimum_watch_evidence_verifiability_score: Decimal,
) -> tuple[str, ...]:
    reason_codes = [f"{STATUS_REASON_PREFIX}{status}"]
    if observable_condition_count < minimum_observable_condition_count:
        reason_codes.append("observable_condition_count_below_minimum")
    if measurable_threshold_count < minimum_measurable_threshold_count:
        reason_codes.append("measurable_threshold_count_below_minimum")
    if subjective_clause_count > maximum_watch_subjective_clause_count:
        reason_codes.append("subjective_clause_count_above_watch_limit")
    elif subjective_clause_count > maximum_pass_subjective_clause_count:
        reason_codes.append("subjective_clause_count_above_pass_limit")
    if oracle_dependency_score > maximum_watch_oracle_dependency_score:
        reason_codes.append("oracle_dependency_score_above_watch_limit")
    elif oracle_dependency_score > maximum_pass_oracle_dependency_score:
        reason_codes.append("oracle_dependency_score_above_pass_limit")
    if dispute_risk_score > maximum_watch_dispute_risk_score:
        reason_codes.append("dispute_risk_score_above_watch_limit")
    elif dispute_risk_score > maximum_pass_dispute_risk_score:
        reason_codes.append("dispute_risk_score_above_pass_limit")
    if evidence_verifiability_score < minimum_watch_evidence_verifiability_score:
        reason_codes.append("evidence_verifiability_score_below_watch_minimum")
    elif evidence_verifiability_score < minimum_pass_evidence_verifiability_score:
        reason_codes.append("evidence_verifiability_score_below_pass_minimum")
    if len(reason_codes) == 1:
        reason_codes.append("falsifiability_sufficient")
    return tuple(reason_codes)


def _validate_result_consistency(score_result: CandidateDecisionFalsifiabilityScoreResult) -> None:
    expected_observable_condition_score = _capped_ratio_from_counts(
        score_result.observable_condition_count,
        score_result.minimum_observable_condition_count,
    )
    if score_result.observable_condition_score != expected_observable_condition_score:
        raise ValueError("observable_condition_score must match observable_condition_count")
    expected_measurable_threshold_score = _capped_ratio_from_counts(
        score_result.measurable_threshold_count,
        score_result.minimum_measurable_threshold_count,
    )
    if score_result.measurable_threshold_score != expected_measurable_threshold_score:
        raise ValueError("measurable_threshold_score must match measurable_threshold_count")
    expected_subjective_clause_score = _subjective_clause_component_score(
        score_result.subjective_clause_count,
        score_result.maximum_pass_subjective_clause_count,
        score_result.maximum_watch_subjective_clause_count,
    )
    if score_result.subjective_clause_score != expected_subjective_clause_score:
        raise ValueError("subjective_clause_score must match subjective_clause_count")
    expected_oracle_dependency_component_score = _inverse_probability_score(
        score_result.oracle_dependency_score,
    )
    if (
        score_result.oracle_dependency_component_score
        != expected_oracle_dependency_component_score
    ):
        raise ValueError(
            "oracle_dependency_component_score must match oracle_dependency_score",
        )
    expected_dispute_risk_component_score = _inverse_probability_score(
        score_result.dispute_risk_score,
    )
    if score_result.dispute_risk_component_score != expected_dispute_risk_component_score:
        raise ValueError("dispute_risk_component_score must match dispute_risk_score")
    expected_falsifiability_score = _quantize_decimal(
        "falsifiability_score",
        (
            score_result.observable_condition_score * score_result.observable_condition_weight
            + score_result.measurable_threshold_score
            * score_result.measurable_threshold_weight
            + score_result.subjective_clause_score * score_result.subjective_clause_weight
            + score_result.oracle_dependency_component_score
            * score_result.oracle_dependency_weight
            + score_result.dispute_risk_component_score * score_result.dispute_risk_weight
            + score_result.evidence_verifiability_score
            * score_result.evidence_verifiability_weight
        ),
    )
    if score_result.falsifiability_score != expected_falsifiability_score:
        raise ValueError("falsifiability_score must match component scores")
    expected_status = _public_status(
        falsifiability_score=score_result.falsifiability_score,
        observable_condition_count=score_result.observable_condition_count,
        minimum_observable_condition_count=score_result.minimum_observable_condition_count,
        measurable_threshold_count=score_result.measurable_threshold_count,
        minimum_measurable_threshold_count=score_result.minimum_measurable_threshold_count,
        subjective_clause_count=score_result.subjective_clause_count,
        maximum_pass_subjective_clause_count=score_result.maximum_pass_subjective_clause_count,
        maximum_watch_subjective_clause_count=score_result.maximum_watch_subjective_clause_count,
        oracle_dependency_score=score_result.oracle_dependency_score,
        maximum_pass_oracle_dependency_score=score_result.maximum_pass_oracle_dependency_score,
        maximum_watch_oracle_dependency_score=score_result.maximum_watch_oracle_dependency_score,
        dispute_risk_score=score_result.dispute_risk_score,
        maximum_pass_dispute_risk_score=score_result.maximum_pass_dispute_risk_score,
        maximum_watch_dispute_risk_score=score_result.maximum_watch_dispute_risk_score,
        evidence_verifiability_score=score_result.evidence_verifiability_score,
        minimum_pass_evidence_verifiability_score=(
            score_result.minimum_pass_evidence_verifiability_score
        ),
        minimum_watch_evidence_verifiability_score=(
            score_result.minimum_watch_evidence_verifiability_score
        ),
        minimum_pass_score=score_result.minimum_pass_score,
        minimum_watch_score=score_result.minimum_watch_score,
    )
    if score_result.status != expected_status:
        raise ValueError("status must match scoring thresholds")
    expected_reason_codes = _result_reason_codes(
        status=score_result.status,
        observable_condition_count=score_result.observable_condition_count,
        minimum_observable_condition_count=score_result.minimum_observable_condition_count,
        measurable_threshold_count=score_result.measurable_threshold_count,
        minimum_measurable_threshold_count=score_result.minimum_measurable_threshold_count,
        subjective_clause_count=score_result.subjective_clause_count,
        maximum_pass_subjective_clause_count=score_result.maximum_pass_subjective_clause_count,
        maximum_watch_subjective_clause_count=score_result.maximum_watch_subjective_clause_count,
        oracle_dependency_score=score_result.oracle_dependency_score,
        maximum_pass_oracle_dependency_score=score_result.maximum_pass_oracle_dependency_score,
        maximum_watch_oracle_dependency_score=score_result.maximum_watch_oracle_dependency_score,
        dispute_risk_score=score_result.dispute_risk_score,
        maximum_pass_dispute_risk_score=score_result.maximum_pass_dispute_risk_score,
        maximum_watch_dispute_risk_score=score_result.maximum_watch_dispute_risk_score,
        evidence_verifiability_score=score_result.evidence_verifiability_score,
        minimum_pass_evidence_verifiability_score=(
            score_result.minimum_pass_evidence_verifiability_score
        ),
        minimum_watch_evidence_verifiability_score=(
            score_result.minimum_watch_evidence_verifiability_score
        ),
    )
    if score_result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match score_result")


def _validate_result_digest(score_result: CandidateDecisionFalsifiabilityScoreResult) -> None:
    if score_result.validation_digest != _result_validation_digest(
        config_version=score_result.config_version,
        redacted_candidate_ref=score_result.redacted_candidate_ref,
        status=score_result.status,
        minimum_pass_score=score_result.minimum_pass_score,
        minimum_watch_score=score_result.minimum_watch_score,
        observable_condition_count=score_result.observable_condition_count,
        minimum_observable_condition_count=score_result.minimum_observable_condition_count,
        observable_condition_score=score_result.observable_condition_score,
        observable_condition_weight=score_result.observable_condition_weight,
        measurable_threshold_count=score_result.measurable_threshold_count,
        minimum_measurable_threshold_count=score_result.minimum_measurable_threshold_count,
        measurable_threshold_score=score_result.measurable_threshold_score,
        measurable_threshold_weight=score_result.measurable_threshold_weight,
        subjective_clause_count=score_result.subjective_clause_count,
        maximum_pass_subjective_clause_count=score_result.maximum_pass_subjective_clause_count,
        maximum_watch_subjective_clause_count=score_result.maximum_watch_subjective_clause_count,
        subjective_clause_score=score_result.subjective_clause_score,
        subjective_clause_weight=score_result.subjective_clause_weight,
        oracle_dependency_score=score_result.oracle_dependency_score,
        maximum_pass_oracle_dependency_score=score_result.maximum_pass_oracle_dependency_score,
        maximum_watch_oracle_dependency_score=score_result.maximum_watch_oracle_dependency_score,
        oracle_dependency_component_score=score_result.oracle_dependency_component_score,
        oracle_dependency_weight=score_result.oracle_dependency_weight,
        dispute_risk_score=score_result.dispute_risk_score,
        maximum_pass_dispute_risk_score=score_result.maximum_pass_dispute_risk_score,
        maximum_watch_dispute_risk_score=score_result.maximum_watch_dispute_risk_score,
        dispute_risk_component_score=score_result.dispute_risk_component_score,
        dispute_risk_weight=score_result.dispute_risk_weight,
        evidence_verifiability_score=score_result.evidence_verifiability_score,
        minimum_pass_evidence_verifiability_score=(
            score_result.minimum_pass_evidence_verifiability_score
        ),
        minimum_watch_evidence_verifiability_score=(
            score_result.minimum_watch_evidence_verifiability_score
        ),
        evidence_verifiability_weight=score_result.evidence_verifiability_weight,
        falsifiability_score=score_result.falsifiability_score,
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
    observable_condition_count: Decimal,
    minimum_observable_condition_count: Decimal,
    observable_condition_score: Decimal,
    observable_condition_weight: Decimal,
    measurable_threshold_count: Decimal,
    minimum_measurable_threshold_count: Decimal,
    measurable_threshold_score: Decimal,
    measurable_threshold_weight: Decimal,
    subjective_clause_count: Decimal,
    maximum_pass_subjective_clause_count: Decimal,
    maximum_watch_subjective_clause_count: Decimal,
    subjective_clause_score: Decimal,
    subjective_clause_weight: Decimal,
    oracle_dependency_score: Decimal,
    maximum_pass_oracle_dependency_score: Decimal,
    maximum_watch_oracle_dependency_score: Decimal,
    oracle_dependency_component_score: Decimal,
    oracle_dependency_weight: Decimal,
    dispute_risk_score: Decimal,
    maximum_pass_dispute_risk_score: Decimal,
    maximum_watch_dispute_risk_score: Decimal,
    dispute_risk_component_score: Decimal,
    dispute_risk_weight: Decimal,
    evidence_verifiability_score: Decimal,
    minimum_pass_evidence_verifiability_score: Decimal,
    minimum_watch_evidence_verifiability_score: Decimal,
    evidence_verifiability_weight: Decimal,
    falsifiability_score: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    digest_parts = (
        VALIDATION_DIGEST_ALGORITHM,
        config_version,
        redacted_candidate_ref,
        status,
        _decimal_payload(minimum_pass_score),
        _decimal_payload(minimum_watch_score),
        _decimal_payload(observable_condition_count),
        _decimal_payload(minimum_observable_condition_count),
        _decimal_payload(observable_condition_score),
        _decimal_payload(observable_condition_weight),
        _decimal_payload(measurable_threshold_count),
        _decimal_payload(minimum_measurable_threshold_count),
        _decimal_payload(measurable_threshold_score),
        _decimal_payload(measurable_threshold_weight),
        _decimal_payload(subjective_clause_count),
        _decimal_payload(maximum_pass_subjective_clause_count),
        _decimal_payload(maximum_watch_subjective_clause_count),
        _decimal_payload(subjective_clause_score),
        _decimal_payload(subjective_clause_weight),
        _decimal_payload(oracle_dependency_score),
        _decimal_payload(maximum_pass_oracle_dependency_score),
        _decimal_payload(maximum_watch_oracle_dependency_score),
        _decimal_payload(oracle_dependency_component_score),
        _decimal_payload(oracle_dependency_weight),
        _decimal_payload(dispute_risk_score),
        _decimal_payload(maximum_pass_dispute_risk_score),
        _decimal_payload(maximum_watch_dispute_risk_score),
        _decimal_payload(dispute_risk_component_score),
        _decimal_payload(dispute_risk_weight),
        _decimal_payload(evidence_verifiability_score),
        _decimal_payload(minimum_pass_evidence_verifiability_score),
        _decimal_payload(minimum_watch_evidence_verifiability_score),
        _decimal_payload(evidence_verifiability_weight),
        _decimal_payload(falsifiability_score),
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
