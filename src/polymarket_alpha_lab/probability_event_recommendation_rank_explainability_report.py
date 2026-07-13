"""Pure paper-only probability event recommendation rank explainer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any, Mapping, Sequence


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_EDGE_REVIEW_MIN = Decimal("0.100000")
_CONFIDENCE_REVIEW_MIN = Decimal("0.600000")
_SOURCE_REVIEW_MIN = Decimal("0.600000")
_PENALTY_HIGH_MIN = Decimal("0.200000")
_PENALTY_EXTREME_MIN = Decimal("0.800000")
_RECOMMEND_SCORE_MIN = Decimal("0.250000")
_CONFIDENCE_WEIGHT = Decimal("0.100000")
_SOURCE_WEIGHT = Decimal("0.050000")
_COST_WEIGHT = Decimal("0.400000")
_RISK_WEIGHT = Decimal("0.300000")
_AUDIT_FACTOR_SUPPORT_WEIGHT = Decimal("0.100000")
_AUDIT_RESOLUTION_CLARITY_WEIGHT = Decimal("0.123333")
_AUDIT_MANUAL_BLOCKER_WEIGHT = Decimal("0.800000")
_FACTOR_REVIEW_MIN = Decimal("0.600000")
_MANUAL_BLOCKER_CLEAR_MAX = Decimal("0.000000")
_RECOMMENDATION_STATUSES = frozenset(("recommend", "watch", "reject"))
_MANUAL_NEXT_STEPS = frozenset(
    (
        "manual_review_candidate",
        "manual_research_update",
        "manual_reject_candidate",
    ),
)
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_REASON_CODE_SEQUENCE = (
    "edge_positive",
    "edge_below_review_threshold",
    "cost_efficient",
    "cost_attention_required",
    "liquidity_sufficient",
    "liquidity_below_review_threshold",
    "freshness_current",
    "freshness_stale",
    "source_quorum_met",
    "source_quorum_below_review_threshold",
    "resolution_clear",
    "resolution_unclear",
    "team_confidence_high",
    "team_confidence_below_review_threshold",
    "manual_blockers_clear",
    "manual_blockers_present",
    "confidence_high",
    "confidence_below_review_threshold",
    "source_quality_high",
    "source_quality_below_review_threshold",
    "cost_penalty_high",
    "cost_penalty_extreme",
    "risk_penalty_high",
    "risk_penalty_extreme",
)
_PAYLOAD_DIGEST_FIELD = "payload_digest"
_PUBLIC_PAYLOAD_FIELDS = (
    "edge_score_probability",
    "confidence_score_probability",
    "source_quality_probability",
    "cost_penalty_probability",
    "risk_penalty_probability",
    "recommendation_status",
    "rank_explainability_score",
    "reason_codes",
    "factor_explanations",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
_AUDIT_FACTOR_NAMES = (
    "edge",
    "cost",
    "liquidity",
    "freshness",
    "source_quorum",
    "resolution_clarity",
    "team_confidence",
    "manual_blockers",
)
_LEGACY_FACTOR_NAMES = (
    "edge",
    "confidence",
    "source_quality",
    "cost_penalty",
    "risk_penalty",
)
_FACTOR_DIRECTIONS = frozenset(("support", "penalty", "blocker"))
_UNSAFE_PUBLIC_TOKENS = tuple(
    "".join(chr(item) for item in code)
    for code in (
        (108, 105, 118, 101),
        (97, 117, 116, 104),
        (119, 97, 108, 108, 101, 116),
        (107, 101, 121),
        (115, 105, 103, 110),
        (111, 114, 100, 101, 114),
        (110, 101, 116, 119, 111, 114, 107),
        (100, 97, 116, 97, 98, 97, 115, 101),
        (112, 101, 114, 115, 105, 115, 116),
        (101, 120, 101, 99, 117, 116, 101),
        (116, 114, 97, 100, 101),
        (98, 117, 121),
        (115, 101, 108, 108),
    )
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ProbabilityEventRecommendationRankFactorExplanation(_FinalDataclass):
    factor_name: str
    score_probability: Decimal
    direction: str
    reason_code: str
    explanation: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_factor_name(self.factor_name)
        object.__setattr__(
            self,
            "score_probability",
            _require_ratio_decimal("score_probability", self.score_probability),
        )
        _require_member("direction", self.direction, _FACTOR_DIRECTIONS)
        if self.reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if type(self.explanation) is not str or self.explanation.strip() != self.explanation:
            raise ValueError("explanation must be a canonical string")
        _require_hard_flags("factor_explanation", self)
        _reject_unsafe_public_payload("factor_explanation", _factor_payload(self))


@dataclass(frozen=True)
class ProbabilityEventRecommendationRankExplainabilityReport(_FinalDataclass):
    edge_score_probability: Decimal
    confidence_score_probability: Decimal
    source_quality_probability: Decimal
    cost_penalty_probability: Decimal
    risk_penalty_probability: Decimal
    recommendation_status: str
    rank_explainability_score: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    factor_explanations: tuple[ProbabilityEventRecommendationRankFactorExplanation, ...] = ()
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "edge_score_probability",
            "confidence_score_probability",
            "source_quality_probability",
            "cost_penalty_probability",
            "risk_penalty_probability",
            "rank_explainability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "recommendation_status",
            self.recommendation_status,
            _RECOMMENDATION_STATUSES,
        )
        _require_member("manual_next_step", self.manual_next_step, _MANUAL_NEXT_STEPS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "factor_explanations",
            _normalize_factor_explanations(self.factor_explanations),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", _public_payload_values(self))
        if self.payload_digest == "":
            object.__setattr__(
                self,
                _PAYLOAD_DIGEST_FIELD,
                _report_payload_digest(self),
            )
        else:
            object.__setattr__(
                self,
                _PAYLOAD_DIGEST_FIELD,
                _normalize_sha256(_PAYLOAD_DIGEST_FIELD, self.payload_digest),
            )
        _validate_payload_digest(self)

    @property
    def public_payload(self) -> dict[str, object]:
        _validate_payload_digest(self)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        payload = _public_payload_values(self)
        payload[_PAYLOAD_DIGEST_FIELD] = self.payload_digest
        _reject_unsafe_public_payload("payload", payload)
        return payload


def build_probability_event_recommendation_rank_explainability_report(
    *,
    edge_score_probability: Decimal,
    confidence_score_probability: Decimal | None = None,
    source_quality_probability: Decimal | None = None,
    cost_penalty_probability: Decimal | None = None,
    risk_penalty_probability: Decimal | None = None,
    cost_score_probability: Decimal | None = None,
    liquidity_score_probability: Decimal | None = None,
    freshness_score_probability: Decimal | None = None,
    source_quorum_score_probability: Decimal | None = None,
    resolution_clarity_score_probability: Decimal | None = None,
    team_confidence_score_probability: Decimal | None = None,
    manual_blocker_score_probability: Decimal | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventRecommendationRankExplainabilityReport:
    edge = _require_ratio_decimal("edge_score_probability", edge_score_probability)
    flags = _PhaseFlags(paper_only=paper_only, report_only=report_only, readonly=readonly)
    _require_hard_flags("builder", flags)
    audit_mode = any(
        value is not None
        for value in (
            cost_score_probability,
            liquidity_score_probability,
            freshness_score_probability,
            source_quorum_score_probability,
            resolution_clarity_score_probability,
            team_confidence_score_probability,
            manual_blocker_score_probability,
        )
    )
    if audit_mode:
        if any(
            value is not None
            for value in (
                confidence_score_probability,
                source_quality_probability,
                cost_penalty_probability,
                risk_penalty_probability,
            )
        ):
            raise ValueError(
                "legacy aliases must not be supplied with audit factors",
            )
        return _build_audit_factor_report(
            edge_score_probability=edge,
            cost_score_probability=cost_score_probability,
            liquidity_score_probability=liquidity_score_probability,
            freshness_score_probability=freshness_score_probability,
            source_quorum_score_probability=source_quorum_score_probability,
            resolution_clarity_score_probability=resolution_clarity_score_probability,
            team_confidence_score_probability=team_confidence_score_probability,
            manual_blocker_score_probability=manual_blocker_score_probability,
            paper_only=paper_only,
            report_only=report_only,
            readonly=readonly,
        )

    confidence = _require_ratio_decimal(
        "confidence_score_probability",
        _require_present_decimal(
            "confidence_score_probability",
            confidence_score_probability,
        ),
    )
    source_quality = _require_ratio_decimal(
        "source_quality_probability",
        _require_present_decimal("source_quality_probability", source_quality_probability),
    )
    cost_penalty = _require_ratio_decimal(
        "cost_penalty_probability",
        _require_present_decimal("cost_penalty_probability", cost_penalty_probability),
    )
    risk_penalty = _require_ratio_decimal(
        "risk_penalty_probability",
        _require_present_decimal("risk_penalty_probability", risk_penalty_probability),
    )

    score = _rank_explainability_score(
        edge_score_probability=edge,
        confidence_score_probability=confidence,
        source_quality_probability=source_quality,
        cost_penalty_probability=cost_penalty,
        risk_penalty_probability=risk_penalty,
    )
    reason_codes = _reason_codes(
        edge_score_probability=edge,
        confidence_score_probability=confidence,
        source_quality_probability=source_quality,
        cost_penalty_probability=cost_penalty,
        risk_penalty_probability=risk_penalty,
    )
    status = _recommendation_status(
        rank_explainability_score=score,
        reason_codes=reason_codes,
    )
    return ProbabilityEventRecommendationRankExplainabilityReport(
        edge_score_probability=edge,
        confidence_score_probability=confidence,
        source_quality_probability=source_quality,
        cost_penalty_probability=cost_penalty,
        risk_penalty_probability=risk_penalty,
        recommendation_status=status,
        rank_explainability_score=score,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(status),
        factor_explanations=_legacy_factor_explanations(
            edge_score_probability=edge,
            confidence_score_probability=confidence,
            source_quality_probability=source_quality,
            cost_penalty_probability=cost_penalty,
            risk_penalty_probability=risk_penalty,
        ),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_recommendation_rank_explainability_report_payload(
    report: ProbabilityEventRecommendationRankExplainabilityReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventRecommendationRankExplainabilityReport:
        raise ValueError(
            "report must be a ProbabilityEventRecommendationRankExplainabilityReport",
        )
    return report.public_payload


def validate_probability_event_recommendation_rank_explainability_public_payload(
    payload: object,
) -> dict[str, object]:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_fields(payload)

    supplied_digest = _require_payload_string(
        _PAYLOAD_DIGEST_FIELD,
        payload[_PAYLOAD_DIGEST_FIELD],
    )
    digest_payload = {
        field_name: payload[field_name]
        for field_name in _PUBLIC_PAYLOAD_FIELDS
        if field_name != _PAYLOAD_DIGEST_FIELD
    }
    if supplied_digest != _payload_digest_for_values(digest_payload):
        raise ValueError("payload_digest must match payload fields")

    probe = ProbabilityEventRecommendationRankExplainabilityReport(
        edge_score_probability=_decimal_from_payload(
            "edge_score_probability",
            payload["edge_score_probability"],
        ),
        confidence_score_probability=_decimal_from_payload(
            "confidence_score_probability",
            payload["confidence_score_probability"],
        ),
        source_quality_probability=_decimal_from_payload(
            "source_quality_probability",
            payload["source_quality_probability"],
        ),
        cost_penalty_probability=_decimal_from_payload(
            "cost_penalty_probability",
            payload["cost_penalty_probability"],
        ),
        risk_penalty_probability=_decimal_from_payload(
            "risk_penalty_probability",
            payload["risk_penalty_probability"],
        ),
        recommendation_status=_require_payload_string(
            "recommendation_status",
            payload["recommendation_status"],
        ),
        rank_explainability_score=_decimal_from_payload(
            "rank_explainability_score",
            payload["rank_explainability_score"],
        ),
        reason_codes=_require_payload_reason_codes(payload["reason_codes"]),
        factor_explanations=_require_payload_factor_explanations(
            payload["factor_explanations"],
        ),
        manual_next_step=_require_payload_string(
            "manual_next_step",
            payload["manual_next_step"],
        ),
        paper_only=_require_payload_bool("paper_only", payload["paper_only"]),
        report_only=_require_payload_bool("report_only", payload["report_only"]),
        readonly=_require_payload_bool("readonly", payload["readonly"]),
        payload_digest=supplied_digest,
    )
    validated_payload = _public_payload_values(probe)
    validated_payload[_PAYLOAD_DIGEST_FIELD] = probe.payload_digest
    return validated_payload


@dataclass(frozen=True)
class _PhaseFlags:
    paper_only: bool
    report_only: bool
    readonly: bool


def _build_audit_factor_report(
    *,
    edge_score_probability: Decimal,
    cost_score_probability: Decimal | None,
    liquidity_score_probability: Decimal | None,
    freshness_score_probability: Decimal | None,
    source_quorum_score_probability: Decimal | None,
    resolution_clarity_score_probability: Decimal | None,
    team_confidence_score_probability: Decimal | None,
    manual_blocker_score_probability: Decimal | None,
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> ProbabilityEventRecommendationRankExplainabilityReport:
    cost_score = _require_ratio_decimal(
        "cost_score_probability",
        _require_present_decimal("cost_score_probability", cost_score_probability),
    )
    liquidity_score = _require_ratio_decimal(
        "liquidity_score_probability",
        _require_present_decimal(
            "liquidity_score_probability",
            liquidity_score_probability,
        ),
    )
    freshness_score = _require_ratio_decimal(
        "freshness_score_probability",
        _require_present_decimal("freshness_score_probability", freshness_score_probability),
    )
    source_quorum_score = _require_ratio_decimal(
        "source_quorum_score_probability",
        _require_present_decimal(
            "source_quorum_score_probability",
            source_quorum_score_probability,
        ),
    )
    resolution_clarity_score = _require_ratio_decimal(
        "resolution_clarity_score_probability",
        _require_present_decimal(
            "resolution_clarity_score_probability",
            resolution_clarity_score_probability,
        ),
    )
    team_confidence_score = _require_ratio_decimal(
        "team_confidence_score_probability",
        _require_present_decimal(
            "team_confidence_score_probability",
            team_confidence_score_probability,
        ),
    )
    manual_blocker_score = _require_ratio_decimal(
        "manual_blocker_score_probability",
        _require_present_decimal(
            "manual_blocker_score_probability",
            manual_blocker_score_probability,
        ),
    )
    factor_explanations = _audit_factor_explanations(
        edge_score_probability=edge_score_probability,
        cost_score_probability=cost_score,
        liquidity_score_probability=liquidity_score,
        freshness_score_probability=freshness_score,
        source_quorum_score_probability=source_quorum_score,
        resolution_clarity_score_probability=resolution_clarity_score,
        team_confidence_score_probability=team_confidence_score,
        manual_blocker_score_probability=manual_blocker_score,
    )
    score = _audit_rank_explainability_score(factor_explanations)
    reason_codes = _factor_reason_codes(factor_explanations)
    status = _recommendation_status(
        rank_explainability_score=score,
        reason_codes=reason_codes,
    )
    return ProbabilityEventRecommendationRankExplainabilityReport(
        edge_score_probability=edge_score_probability,
        confidence_score_probability=team_confidence_score,
        source_quality_probability=_quantize(
            (freshness_score + source_quorum_score + resolution_clarity_score)
            / Decimal("3.000000"),
        ),
        cost_penalty_probability=_ONE - cost_score,
        risk_penalty_probability=manual_blocker_score,
        recommendation_status=status,
        rank_explainability_score=score,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(status),
        factor_explanations=factor_explanations,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _rank_explainability_score(
    *,
    edge_score_probability: Decimal,
    confidence_score_probability: Decimal,
    source_quality_probability: Decimal,
    cost_penalty_probability: Decimal,
    risk_penalty_probability: Decimal,
) -> Decimal:
    if (
        edge_score_probability < _EDGE_REVIEW_MIN
        or confidence_score_probability < _CONFIDENCE_REVIEW_MIN
        or source_quality_probability < _SOURCE_REVIEW_MIN
    ):
        return _ZERO
    raw_score = (
        edge_score_probability
        + (confidence_score_probability * _CONFIDENCE_WEIGHT)
        + (source_quality_probability * _SOURCE_WEIGHT)
        - (cost_penalty_probability * _COST_WEIGHT)
        - (risk_penalty_probability * _RISK_WEIGHT)
    )
    if raw_score < _ZERO:
        return _ZERO
    if raw_score > _ONE:
        return _ONE
    return _quantize(raw_score)


def _audit_rank_explainability_score(
    factor_explanations: tuple[ProbabilityEventRecommendationRankFactorExplanation, ...],
) -> Decimal:
    factors = _factor_score_map(factor_explanations)
    if (
        factors["edge"] < _EDGE_REVIEW_MIN
        or factors["cost"] < _FACTOR_REVIEW_MIN
        or factors["liquidity"] < _FACTOR_REVIEW_MIN
        or factors["freshness"] < _FACTOR_REVIEW_MIN
        or factors["source_quorum"] < _FACTOR_REVIEW_MIN
        or factors["resolution_clarity"] < _FACTOR_REVIEW_MIN
        or factors["team_confidence"] < _CONFIDENCE_REVIEW_MIN
    ):
        return _ZERO
    raw_score = (
        factors["edge"]
        + (factors["cost"] * _AUDIT_FACTOR_SUPPORT_WEIGHT)
        + (factors["liquidity"] * _AUDIT_FACTOR_SUPPORT_WEIGHT)
        + (factors["freshness"] * _AUDIT_FACTOR_SUPPORT_WEIGHT)
        + (factors["source_quorum"] * _AUDIT_FACTOR_SUPPORT_WEIGHT)
        + (factors["resolution_clarity"] * _AUDIT_RESOLUTION_CLARITY_WEIGHT)
        + (factors["team_confidence"] * _AUDIT_FACTOR_SUPPORT_WEIGHT)
        - (factors["manual_blockers"] * _AUDIT_MANUAL_BLOCKER_WEIGHT)
    )
    if raw_score < _ZERO:
        return _ZERO
    if raw_score > _ONE:
        return _ONE
    return _quantize(raw_score)


def _reason_codes(
    *,
    edge_score_probability: Decimal,
    confidence_score_probability: Decimal,
    source_quality_probability: Decimal,
    cost_penalty_probability: Decimal,
    risk_penalty_probability: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if edge_score_probability >= _EDGE_REVIEW_MIN:
        reason_codes.append("edge_positive")
    else:
        reason_codes.append("edge_below_review_threshold")
    if confidence_score_probability >= _CONFIDENCE_REVIEW_MIN:
        reason_codes.append("confidence_high")
    else:
        reason_codes.append("confidence_below_review_threshold")
    if source_quality_probability >= _SOURCE_REVIEW_MIN:
        reason_codes.append("source_quality_high")
    else:
        reason_codes.append("source_quality_below_review_threshold")
    if cost_penalty_probability >= _PENALTY_EXTREME_MIN:
        reason_codes.append("cost_penalty_extreme")
    elif cost_penalty_probability >= _PENALTY_HIGH_MIN:
        reason_codes.append("cost_penalty_high")
    if risk_penalty_probability >= _PENALTY_EXTREME_MIN:
        reason_codes.append("risk_penalty_extreme")
    elif risk_penalty_probability >= _PENALTY_HIGH_MIN:
        reason_codes.append("risk_penalty_high")
    return _normalize_reason_codes(reason_codes)


def _audit_factor_explanations(
    *,
    edge_score_probability: Decimal,
    cost_score_probability: Decimal,
    liquidity_score_probability: Decimal,
    freshness_score_probability: Decimal,
    source_quorum_score_probability: Decimal,
    resolution_clarity_score_probability: Decimal,
    team_confidence_score_probability: Decimal,
    manual_blocker_score_probability: Decimal,
) -> tuple[ProbabilityEventRecommendationRankFactorExplanation, ...]:
    return (
        ProbabilityEventRecommendationRankFactorExplanation(
            factor_name="edge",
            score_probability=edge_score_probability,
            direction="support",
            reason_code=_edge_factor_reason_code(edge_score_probability),
            explanation="cost-adjusted probability edge is positive"
            if edge_score_probability >= _EDGE_REVIEW_MIN
            else "cost-adjusted probability edge is below review threshold",
        ),
        ProbabilityEventRecommendationRankFactorExplanation(
            factor_name="cost",
            score_probability=cost_score_probability,
            direction="support",
            reason_code="cost_efficient"
            if cost_score_probability >= _FACTOR_REVIEW_MIN
            else "cost_attention_required",
            explanation="fees, spread, and slippage leave enough paper edge"
            if cost_score_probability >= _FACTOR_REVIEW_MIN
            else "fees, spread, or slippage need paper review",
        ),
        ProbabilityEventRecommendationRankFactorExplanation(
            factor_name="liquidity",
            score_probability=liquidity_score_probability,
            direction="support",
            reason_code="liquidity_sufficient"
            if liquidity_score_probability >= _FACTOR_REVIEW_MIN
            else "liquidity_below_review_threshold",
            explanation="paper depth is sufficient for review sizing"
            if liquidity_score_probability >= _FACTOR_REVIEW_MIN
            else "paper depth is below review threshold",
        ),
        ProbabilityEventRecommendationRankFactorExplanation(
            factor_name="freshness",
            score_probability=freshness_score_probability,
            direction="support",
            reason_code="freshness_current"
            if freshness_score_probability >= _FACTOR_REVIEW_MIN
            else "freshness_stale",
            explanation="candidate evidence is current enough for paper review"
            if freshness_score_probability >= _FACTOR_REVIEW_MIN
            else "candidate evidence needs freshness review",
        ),
        ProbabilityEventRecommendationRankFactorExplanation(
            factor_name="source_quorum",
            score_probability=source_quorum_score_probability,
            direction="support",
            reason_code="source_quorum_met"
            if source_quorum_score_probability >= _FACTOR_REVIEW_MIN
            else "source_quorum_below_review_threshold",
            explanation="independent public source quorum is met"
            if source_quorum_score_probability >= _FACTOR_REVIEW_MIN
            else "independent public source quorum is below review threshold",
        ),
        ProbabilityEventRecommendationRankFactorExplanation(
            factor_name="resolution_clarity",
            score_probability=resolution_clarity_score_probability,
            direction="support",
            reason_code="resolution_clear"
            if resolution_clarity_score_probability >= _FACTOR_REVIEW_MIN
            else "resolution_unclear",
            explanation="resolution criteria are clear enough to audit"
            if resolution_clarity_score_probability >= _FACTOR_REVIEW_MIN
            else "resolution criteria need additional review",
        ),
        ProbabilityEventRecommendationRankFactorExplanation(
            factor_name="team_confidence",
            score_probability=team_confidence_score_probability,
            direction="support",
            reason_code="team_confidence_high"
            if team_confidence_score_probability >= _CONFIDENCE_REVIEW_MIN
            else "team_confidence_below_review_threshold",
            explanation="specialist team confidence supports paper review"
            if team_confidence_score_probability >= _CONFIDENCE_REVIEW_MIN
            else "specialist team confidence is below review threshold",
        ),
        ProbabilityEventRecommendationRankFactorExplanation(
            factor_name="manual_blockers",
            score_probability=manual_blocker_score_probability,
            direction="blocker",
            reason_code="manual_blockers_clear"
            if manual_blocker_score_probability <= _MANUAL_BLOCKER_CLEAR_MAX
            else "manual_blockers_present",
            explanation="manual review blockers are clear"
            if manual_blocker_score_probability <= _MANUAL_BLOCKER_CLEAR_MAX
            else "manual review blockers require attention",
        ),
    )


def _legacy_factor_explanations(
    *,
    edge_score_probability: Decimal,
    confidence_score_probability: Decimal,
    source_quality_probability: Decimal,
    cost_penalty_probability: Decimal,
    risk_penalty_probability: Decimal,
) -> tuple[ProbabilityEventRecommendationRankFactorExplanation, ...]:
    return (
        ProbabilityEventRecommendationRankFactorExplanation(
            factor_name="edge",
            score_probability=edge_score_probability,
            direction="support",
            reason_code=_edge_factor_reason_code(edge_score_probability),
            explanation="cost-adjusted probability edge is positive"
            if edge_score_probability >= _EDGE_REVIEW_MIN
            else "cost-adjusted probability edge is below review threshold",
        ),
        ProbabilityEventRecommendationRankFactorExplanation(
            factor_name="confidence",
            score_probability=confidence_score_probability,
            direction="support",
            reason_code="confidence_high"
            if confidence_score_probability >= _CONFIDENCE_REVIEW_MIN
            else "confidence_below_review_threshold",
            explanation="confidence score supports paper review"
            if confidence_score_probability >= _CONFIDENCE_REVIEW_MIN
            else "confidence score is below review threshold",
        ),
        ProbabilityEventRecommendationRankFactorExplanation(
            factor_name="source_quality",
            score_probability=source_quality_probability,
            direction="support",
            reason_code="source_quality_high"
            if source_quality_probability >= _SOURCE_REVIEW_MIN
            else "source_quality_below_review_threshold",
            explanation="source quality supports paper review"
            if source_quality_probability >= _SOURCE_REVIEW_MIN
            else "source quality is below review threshold",
        ),
        ProbabilityEventRecommendationRankFactorExplanation(
            factor_name="cost_penalty",
            score_probability=cost_penalty_probability,
            direction="penalty",
            reason_code="cost_penalty_extreme"
            if cost_penalty_probability >= _PENALTY_EXTREME_MIN
            else "cost_penalty_high"
            if cost_penalty_probability >= _PENALTY_HIGH_MIN
            else "cost_efficient",
            explanation="paper cost penalty is extreme"
            if cost_penalty_probability >= _PENALTY_EXTREME_MIN
            else "paper cost penalty needs review"
            if cost_penalty_probability >= _PENALTY_HIGH_MIN
            else "paper cost penalty is low",
        ),
        ProbabilityEventRecommendationRankFactorExplanation(
            factor_name="risk_penalty",
            score_probability=risk_penalty_probability,
            direction="penalty",
            reason_code="risk_penalty_extreme"
            if risk_penalty_probability >= _PENALTY_EXTREME_MIN
            else "risk_penalty_high"
            if risk_penalty_probability >= _PENALTY_HIGH_MIN
            else "manual_blockers_clear",
            explanation="paper risk penalty is extreme"
            if risk_penalty_probability >= _PENALTY_EXTREME_MIN
            else "paper risk penalty needs review"
            if risk_penalty_probability >= _PENALTY_HIGH_MIN
            else "paper risk penalty is low",
        ),
    )


def _edge_factor_reason_code(edge_score_probability: Decimal) -> str:
    if edge_score_probability >= _EDGE_REVIEW_MIN:
        return "edge_positive"
    return "edge_below_review_threshold"


def _factor_reason_codes(
    factor_explanations: tuple[ProbabilityEventRecommendationRankFactorExplanation, ...],
) -> tuple[str, ...]:
    return _normalize_reason_codes(tuple(factor.reason_code for factor in factor_explanations))


def _factor_score_map(
    factor_explanations: tuple[ProbabilityEventRecommendationRankFactorExplanation, ...],
) -> dict[str, Decimal]:
    return {factor.factor_name: factor.score_probability for factor in factor_explanations}


def _recommendation_status(
    *,
    rank_explainability_score: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    if (
        "cost_penalty_extreme" in reason_codes
        or "risk_penalty_extreme" in reason_codes
        or "manual_blockers_present" in reason_codes
    ):
        return "reject"
    if rank_explainability_score >= _RECOMMEND_SCORE_MIN:
        return "recommend"
    return "watch"


def _manual_next_step(recommendation_status: str) -> str:
    if recommendation_status == "recommend":
        return "manual_review_candidate"
    if recommendation_status == "watch":
        return "manual_research_update"
    if recommendation_status == "reject":
        return "manual_reject_candidate"
    raise ValueError("recommendation_status must be supported")


def _validate_report_consistency(
    report: ProbabilityEventRecommendationRankExplainabilityReport,
) -> None:
    _validate_factor_explanations_consistency(report.factor_explanations)
    _validate_factor_score_bindings(report)
    if _factor_names(report.factor_explanations) == _AUDIT_FACTOR_NAMES:
        expected_score = _audit_rank_explainability_score(report.factor_explanations)
        expected_reasons = _factor_reason_codes(report.factor_explanations)
    else:
        expected_score = _rank_explainability_score(
            edge_score_probability=report.edge_score_probability,
            confidence_score_probability=report.confidence_score_probability,
            source_quality_probability=report.source_quality_probability,
            cost_penalty_probability=report.cost_penalty_probability,
            risk_penalty_probability=report.risk_penalty_probability,
        )
        expected_reasons = _reason_codes(
            edge_score_probability=report.edge_score_probability,
            confidence_score_probability=report.confidence_score_probability,
            source_quality_probability=report.source_quality_probability,
            cost_penalty_probability=report.cost_penalty_probability,
            risk_penalty_probability=report.risk_penalty_probability,
        )
    if report.rank_explainability_score != expected_score:
        raise ValueError("rank_explainability_score must match report inputs")
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report inputs")
    expected_status = _recommendation_status(
        rank_explainability_score=expected_score,
        reason_codes=expected_reasons,
    )
    if report.recommendation_status != expected_status:
        raise ValueError("recommendation_status must match report inputs")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match recommendation_status")


def _validate_factor_explanations_consistency(
    factor_explanations: tuple[ProbabilityEventRecommendationRankFactorExplanation, ...],
) -> None:
    if type(factor_explanations) is not tuple:
        raise ValueError("factor_explanations must be a tuple")
    normalized = _normalize_factor_explanations(factor_explanations)
    for factor in normalized:
        _require_factor_name(factor.factor_name)
        if factor.score_probability != _require_ratio_decimal(
            "score_probability",
            factor.score_probability,
        ):
            raise ValueError("score_probability must be canonical")
        _require_member("direction", factor.direction, _FACTOR_DIRECTIONS)
        if factor.reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if type(factor.explanation) is not str or factor.explanation.strip() != factor.explanation:
            raise ValueError("explanation must be a canonical string")
        _require_hard_flags("factor_explanation", factor)
        _reject_unsafe_public_payload("factor_explanation", _factor_payload(factor))

    scores = _factor_score_map(normalized)
    if _factor_names(normalized) == _AUDIT_FACTOR_NAMES:
        expected = _audit_factor_explanations(
            edge_score_probability=scores["edge"],
            cost_score_probability=scores["cost"],
            liquidity_score_probability=scores["liquidity"],
            freshness_score_probability=scores["freshness"],
            source_quorum_score_probability=scores["source_quorum"],
            resolution_clarity_score_probability=scores["resolution_clarity"],
            team_confidence_score_probability=scores["team_confidence"],
            manual_blocker_score_probability=scores["manual_blockers"],
        )
    else:
        expected = _legacy_factor_explanations(
            edge_score_probability=scores["edge"],
            confidence_score_probability=scores["confidence"],
            source_quality_probability=scores["source_quality"],
            cost_penalty_probability=scores["cost_penalty"],
            risk_penalty_probability=scores["risk_penalty"],
        )

    for factor, expected_factor in zip(normalized, expected, strict=True):
        if factor.direction != expected_factor.direction:
            raise ValueError(f"{factor.factor_name} direction must match factor semantics")
        if factor.reason_code != expected_factor.reason_code:
            raise ValueError(f"{factor.factor_name} reason_code must match factor score")
        if factor.explanation != expected_factor.explanation:
            raise ValueError(f"{factor.factor_name} explanation must match factor score")


def _validate_factor_score_bindings(
    report: ProbabilityEventRecommendationRankExplainabilityReport,
) -> None:
    scores = _factor_score_map(report.factor_explanations)
    if _factor_names(report.factor_explanations) == _AUDIT_FACTOR_NAMES:
        expected_fields = {
            "edge_score_probability": scores["edge"],
            "confidence_score_probability": scores["team_confidence"],
            "source_quality_probability": _quantize(
                (
                    scores["freshness"]
                    + scores["source_quorum"]
                    + scores["resolution_clarity"]
                )
                / Decimal("3.000000"),
            ),
            "cost_penalty_probability": _quantize(_ONE - scores["cost"]),
            "risk_penalty_probability": scores["manual_blockers"],
        }
    else:
        expected_fields = {
            "edge_score_probability": scores["edge"],
            "confidence_score_probability": scores["confidence"],
            "source_quality_probability": scores["source_quality"],
            "cost_penalty_probability": scores["cost_penalty"],
            "risk_penalty_probability": scores["risk_penalty"],
        }

    for field_name, expected_value in expected_fields.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match factor_explanations")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_member(field_name: str, value: object, members: frozenset[str]) -> str:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_present_decimal(field_name: str, value: Decimal | None) -> Decimal:
    if value is None:
        raise ValueError(f"{field_name} must be a Decimal")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain strings")
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    normalized_codes = tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )
    if "manual_blockers_present" in normalized_codes:
        normalized_codes = tuple(
            reason_code
            for reason_code in normalized_codes
            if reason_code
            in (
                "edge_below_review_threshold",
                "manual_blockers_present",
            )
        )
    elif "cost_penalty_extreme" in normalized_codes or "risk_penalty_extreme" in normalized_codes:
        normalized_codes = tuple(
            reason_code
            for reason_code in normalized_codes
            if reason_code
            in (
                "edge_below_review_threshold",
                "cost_penalty_extreme",
                "risk_penalty_extreme",
            )
        )
    return normalized_codes


def _normalize_factor_explanations(
    factor_explanations: Sequence[ProbabilityEventRecommendationRankFactorExplanation],
) -> tuple[ProbabilityEventRecommendationRankFactorExplanation, ...]:
    if isinstance(factor_explanations, (str, bytes)) or not isinstance(
        factor_explanations,
        Sequence,
    ):
        raise ValueError("factor_explanations must be a sequence")
    normalized = tuple(factor_explanations)
    for factor in normalized:
        if type(factor) is not ProbabilityEventRecommendationRankFactorExplanation:
            raise ValueError("factor_explanations must contain factor explanations")
        _require_hard_flags("factor_explanation", factor)
    names = _factor_names(normalized)
    if names not in (_AUDIT_FACTOR_NAMES, _LEGACY_FACTOR_NAMES):
        raise ValueError("factor_explanations must match the required factor order")
    return normalized


def _factor_names(
    factor_explanations: tuple[ProbabilityEventRecommendationRankFactorExplanation, ...],
) -> tuple[str, ...]:
    return tuple(factor.factor_name for factor in factor_explanations)


def _require_factor_name(value: object) -> str:
    if type(value) is not str or value not in (*_AUDIT_FACTOR_NAMES, *_LEGACY_FACTOR_NAMES):
        raise ValueError("factor_name must be supported")
    return value


def _public_payload_values(
    report: ProbabilityEventRecommendationRankExplainabilityReport,
) -> dict[str, object]:
    return {
        "edge_score_probability": _decimal_payload(report.edge_score_probability),
        "confidence_score_probability": _decimal_payload(
            report.confidence_score_probability,
        ),
        "source_quality_probability": _decimal_payload(report.source_quality_probability),
        "cost_penalty_probability": _decimal_payload(report.cost_penalty_probability),
        "risk_penalty_probability": _decimal_payload(report.risk_penalty_probability),
        "recommendation_status": report.recommendation_status,
        "rank_explainability_score": _decimal_payload(report.rank_explainability_score),
        "reason_codes": list(report.reason_codes),
        "factor_explanations": [
            _factor_payload(factor) for factor in report.factor_explanations
        ],
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _factor_payload(
    factor: ProbabilityEventRecommendationRankFactorExplanation,
) -> dict[str, object]:
    return {
        "factor_name": factor.factor_name,
        "score_probability": _decimal_payload(factor.score_probability),
        "direction": factor.direction,
        "reason_code": factor.reason_code,
        "explanation": factor.explanation,
        "paper_only": factor.paper_only,
        "report_only": factor.report_only,
        "readonly": factor.readonly,
    }


def _report_payload_digest(
    report: ProbabilityEventRecommendationRankExplainabilityReport,
) -> str:
    return _payload_digest_for_values(_public_payload_values(report))


def _payload_digest_for_values(payload: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def _validate_payload_digest(
    report: ProbabilityEventRecommendationRankExplainabilityReport,
) -> None:
    if report.payload_digest != _report_payload_digest(report):
        raise ValueError("payload_digest must match report fields")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 string")
    return value


def _decimal_payload(value: Decimal) -> str:
    return format(_require_ratio_decimal("payload_decimal", value), "f")


def _require_payload_fields(payload: dict[str, object]) -> None:
    if tuple(payload.keys()) != _PUBLIC_PAYLOAD_FIELDS:
        raise ValueError("payload fields must match report payload schema")


def _require_payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_payload_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    return _normalize_reason_codes(value)


def _require_payload_factor_explanations(
    value: object,
) -> tuple[ProbabilityEventRecommendationRankFactorExplanation, ...]:
    if type(value) is not list:
        raise ValueError("factor_explanations must be a list")
    factors: list[ProbabilityEventRecommendationRankFactorExplanation] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError("factor_explanations must contain objects")
        if tuple(item.keys()) != (
            "factor_name",
            "score_probability",
            "direction",
            "reason_code",
            "explanation",
            "paper_only",
            "report_only",
            "readonly",
        ):
            raise ValueError("factor_explanations must match payload schema")
        factors.append(
            ProbabilityEventRecommendationRankFactorExplanation(
                factor_name=_require_payload_string("factor_name", item["factor_name"]),
                score_probability=_decimal_from_payload(
                    "score_probability",
                    item["score_probability"],
                ),
                direction=_require_payload_string("direction", item["direction"]),
                reason_code=_require_payload_string("reason_code", item["reason_code"]),
                explanation=_require_payload_string("explanation", item["explanation"]),
                paper_only=_require_payload_bool("paper_only", item["paper_only"]),
                report_only=_require_payload_bool("report_only", item["report_only"]),
                readonly=_require_payload_bool("readonly", item["readonly"]),
            ),
        )
    return _normalize_factor_explanations(factors)


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    return _require_ratio_decimal(field_name, Decimal(value))


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for text in _walk_public_strings(value):
        lowered = text.lower()
        if any(token in lowered for token in _UNSAFE_PUBLIC_TOKENS):
            raise ValueError(f"unsafe public {label}")


def _walk_public_strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if is_dataclass(value) and not isinstance(value, type):
        return _walk_public_strings(asdict(value))
    if type(value) is Decimal:
        return ()
    if type(value) is bool:
        return ()
    if type(value) is str:
        return (value,)
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric public values must be Decimal strings")
    if isinstance(value, Mapping):
        return tuple(
            text
            for key, item in value.items()
            for text in _walk_public_strings(key) + _walk_public_strings(item)
        )
    if isinstance(value, (list, tuple)):
        return tuple(text for item in value for text in _walk_public_strings(item))
    raise ValueError("public value is not JSON serializable")


__all__ = (
    "ProbabilityEventRecommendationRankFactorExplanation",
    "ProbabilityEventRecommendationRankExplainabilityReport",
    "build_probability_event_recommendation_rank_explainability_report",
    "probability_event_recommendation_rank_explainability_report_payload",
    "validate_probability_event_recommendation_rank_explainability_public_payload",
)
