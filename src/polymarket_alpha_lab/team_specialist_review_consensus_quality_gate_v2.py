"""Readonly paper-only gate for specialist review consensus quality."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_REVIEW_CONSENSUS_QUALITY_GATE_V2_CONFIG_VERSION = (
    "team-specialist-review-consensus-quality-gate-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

GATE_STATUSES = ("pass", "watch", "blocked")
ROW_STATUSES = ("complete", "incomplete")
ROW_REASON_CODES = (
    "team_specialist_review_consensus_quality_row_complete",
    "team_specialist_review_consensus_quality_row_incomplete",
)
REPORT_REASON_CODES = (
    "team_specialist_review_consensus_quality_gate_passed",
    "team_specialist_review_consensus_quality_gate_empty",
    "team_specialist_review_consensus_quality_gate_min_specialist_count_unmet",
    "team_specialist_review_consensus_quality_gate_quorum_unmet",
    "team_specialist_review_consensus_quality_gate_incomplete_reviews",
    "team_specialist_review_consensus_quality_gate_disagreement_blocked",
    "team_specialist_review_consensus_quality_gate_consensus_below_watch",
    "team_specialist_review_consensus_quality_gate_disagreement_watch",
    "team_specialist_review_consensus_quality_gate_consensus_below_pass",
)
BLOCKING_REASON_CODES = frozenset(
    (
        "team_specialist_review_consensus_quality_gate_empty",
        "team_specialist_review_consensus_quality_gate_min_specialist_count_unmet",
        "team_specialist_review_consensus_quality_gate_quorum_unmet",
        "team_specialist_review_consensus_quality_gate_incomplete_reviews",
        "team_specialist_review_consensus_quality_gate_disagreement_blocked",
        "team_specialist_review_consensus_quality_gate_consensus_below_watch",
    ),
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
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

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_REVIEW_CONSENSUS_QUALITY_GATE_V2_CONFIG_VERSION",
    "TeamSpecialistReviewConsensusQualityGateV2Config",
    "TeamSpecialistReviewConsensusQualityGateV2Review",
    "TeamSpecialistReviewConsensusQualityGateV2Row",
    "TeamSpecialistReviewConsensusQualityGateV2Report",
    "build_team_specialist_review_consensus_quality_gate_v2",
    "team_specialist_review_consensus_quality_gate_v2_payload",
)


@dataclass(frozen=True)
class TeamSpecialistReviewConsensusQualityGateV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_REVIEW_CONSENSUS_QUALITY_GATE_V2_CONFIG_VERSION
    )
    evidence_weight: Decimal = Decimal("0.400000")
    rationale_weight: Decimal = Decimal("0.400000")
    confidence_weight: Decimal = Decimal("0.200000")
    disagreement_penalty_weight: Decimal = Decimal("0.500000")
    min_pass_consensus_score: Decimal = Decimal("0.800000")
    min_watch_consensus_score: Decimal = Decimal("0.600000")
    max_pass_disagreement_ratio: Decimal = Decimal("0.200000")
    max_watch_disagreement_ratio: Decimal = Decimal("0.400000")
    min_quorum_participation_ratio: Decimal = Decimal("0.750000")
    min_specialist_count: Decimal = Decimal("3")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "evidence_weight",
            "rationale_weight",
            "confidence_weight",
            "disagreement_penalty_weight",
            "min_pass_consensus_score",
            "min_watch_consensus_score",
            "max_pass_disagreement_ratio",
            "max_watch_disagreement_ratio",
            "min_quorum_participation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_specialist_count",
            _normalize_positive_integral_decimal(
                "min_specialist_count",
                self.min_specialist_count,
            ),
        )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistReviewConsensusQualityGateV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistReviewConsensusQualityGateV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistReviewConsensusQualityGateV2Review:
    cohort_id: str
    specialist_id: str
    evidence_score: Decimal
    rationale_score: Decimal
    confidence_score: Decimal
    review_complete: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "cohort_id",
            _require_non_empty_string("cohort_id", self.cohort_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_non_empty_string("specialist_id", self.specialist_id),
        )
        for field_name in (
            "evidence_score",
            "rationale_score",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if type(self.review_complete) is not bool:
            raise ValueError("review_complete must be a bool")
        _require_hard_flags("TeamSpecialistReviewConsensusQualityGateV2Review", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistReviewConsensusQualityGateV2Review",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistReviewConsensusQualityGateV2Row:
    rank: Decimal
    cohort_id: str
    specialist_id: str
    evidence_score: Decimal
    rationale_score: Decimal
    confidence_score: Decimal
    raw_review_score: Decimal
    peer_deviation_score: Decimal
    disagreement_penalty: Decimal
    consensus_contribution_score: Decimal
    review_complete: bool
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        object.__setattr__(
            self,
            "cohort_id",
            _require_non_empty_string("cohort_id", self.cohort_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_non_empty_string("specialist_id", self.specialist_id),
        )
        for field_name in (
            "evidence_score",
            "rationale_score",
            "confidence_score",
            "raw_review_score",
            "peer_deviation_score",
            "disagreement_penalty",
            "consensus_contribution_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if type(self.review_complete) is not bool:
            raise ValueError("review_complete must be a bool")
        _require_row_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("TeamSpecialistReviewConsensusQualityGateV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistReviewConsensusQualityGateV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class TeamSpecialistReviewConsensusQualityGateV2Report:
    generated_at: datetime
    config_version: str
    gate_status: str
    specialist_count: Decimal
    complete_review_count: Decimal
    quorum_participation_ratio: Decimal
    average_raw_review_score: Decimal
    disagreement_ratio: Decimal
    disagreement_penalty_weight: Decimal
    disagreement_penalty: Decimal
    consensus_quality_score: Decimal
    min_pass_consensus_score: Decimal
    min_watch_consensus_score: Decimal
    max_pass_disagreement_ratio: Decimal
    max_watch_disagreement_ratio: Decimal
    min_quorum_participation_ratio: Decimal
    min_specialist_count: Decimal
    rows: tuple[TeamSpecialistReviewConsensusQualityGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_gate_status("gate_status", self.gate_status)
        for field_name in (
            "specialist_count",
            "complete_review_count",
            "min_specialist_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "quorum_participation_ratio",
            "average_raw_review_score",
            "disagreement_ratio",
            "disagreement_penalty_weight",
            "disagreement_penalty",
            "consensus_quality_score",
            "min_pass_consensus_score",
            "min_watch_consensus_score",
            "max_pass_disagreement_ratio",
            "max_watch_disagreement_ratio",
            "min_quorum_participation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("TeamSpecialistReviewConsensusQualityGateV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistReviewConsensusQualityGateV2Report",
            _payload_value(asdict(self)),
        )
        if self.derived_validation_digest != _derived_validation_digest(asdict(self)):
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistReviewConsensusQualityGateV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_review_consensus_quality_gate_v2(
    specialist_reviews: object,
    *,
    config: TeamSpecialistReviewConsensusQualityGateV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistReviewConsensusQualityGateV2Report:
    if config is None:
        config = TeamSpecialistReviewConsensusQualityGateV2Config()
    if type(config) is not TeamSpecialistReviewConsensusQualityGateV2Config:
        raise ValueError(
            "config must be a TeamSpecialistReviewConsensusQualityGateV2Config",
        )
    _require_hard_flags("TeamSpecialistReviewConsensusQualityGateV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    reviews = _normalize_reviews(specialist_reviews)
    rows = _rows_for_reviews(reviews, config)
    complete_review_count = _complete_review_count(rows)
    specialist_count = Decimal(len(rows)).quantize(COUNT_QUANT)
    quorum_ratio = _ratio_or_zero(complete_review_count, specialist_count)
    average_raw_score = _average_raw_score(rows)
    disagreement_ratio = _disagreement_ratio(rows)
    penalty = _score_penalty(disagreement_ratio, config.disagreement_penalty_weight)
    consensus_quality_score = _clamp_ratio(average_raw_score - penalty)
    reasons = _report_reason_codes(
        specialist_count=specialist_count,
        complete_review_count=complete_review_count,
        quorum_participation_ratio=quorum_ratio,
        disagreement_ratio=disagreement_ratio,
        consensus_quality_score=consensus_quality_score,
        config=config,
    )
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "gate_status": _gate_status(reasons),
        "specialist_count": specialist_count,
        "complete_review_count": complete_review_count,
        "quorum_participation_ratio": quorum_ratio,
        "average_raw_review_score": average_raw_score,
        "disagreement_ratio": disagreement_ratio,
        "disagreement_penalty_weight": config.disagreement_penalty_weight,
        "disagreement_penalty": penalty,
        "consensus_quality_score": consensus_quality_score,
        "min_pass_consensus_score": config.min_pass_consensus_score,
        "min_watch_consensus_score": config.min_watch_consensus_score,
        "max_pass_disagreement_ratio": config.max_pass_disagreement_ratio,
        "max_watch_disagreement_ratio": config.max_watch_disagreement_ratio,
        "min_quorum_participation_ratio": config.min_quorum_participation_ratio,
        "min_specialist_count": config.min_specialist_count,
        "rows": rows,
        "reason_codes": reasons,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistReviewConsensusQualityGateV2Report(**values)


def team_specialist_review_consensus_quality_gate_v2_payload(
    value: object,
) -> dict[str, object]:
    if type(value) is TeamSpecialistReviewConsensusQualityGateV2Report:
        return value.payload
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload(
        "team_specialist_review_consensus_quality_gate_v2_payload",
        payload,
    )
    _require_sha256_digest(
        "derived_validation_digest",
        payload.get("derived_validation_digest"),
    )
    if payload["derived_validation_digest"] != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload fields")
    return payload


def _rows_for_reviews(
    reviews: tuple[TeamSpecialistReviewConsensusQualityGateV2Review, ...],
    config: TeamSpecialistReviewConsensusQualityGateV2Config,
) -> tuple[TeamSpecialistReviewConsensusQualityGateV2Row, ...]:
    sorted_reviews = tuple(
        sorted(reviews, key=lambda item: (item.cohort_id, item.specialist_id)),
    )
    raw_scores = tuple(_raw_review_score(item, config) for item in sorted_reviews)
    complete_scores = tuple(
        score
        for score, review in zip(raw_scores, sorted_reviews, strict=True)
        if review.review_complete
    )
    average_raw_score = _average_score_values(complete_scores)
    return tuple(
        _row_for_review(
            rank=index,
            review=review,
            raw_review_score=raw_score,
            average_raw_score=average_raw_score,
            config=config,
        )
        for index, (review, raw_score) in enumerate(
            zip(sorted_reviews, raw_scores, strict=True),
            start=1,
        )
    )


def _row_for_review(
    *,
    rank: int,
    review: TeamSpecialistReviewConsensusQualityGateV2Review,
    raw_review_score: Decimal,
    average_raw_score: Decimal,
    config: TeamSpecialistReviewConsensusQualityGateV2Config,
) -> TeamSpecialistReviewConsensusQualityGateV2Row:
    peer_deviation = _absolute_difference(raw_review_score, average_raw_score)
    row_penalty = _score_penalty(peer_deviation, config.disagreement_penalty_weight)
    return TeamSpecialistReviewConsensusQualityGateV2Row(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        cohort_id=review.cohort_id,
        specialist_id=review.specialist_id,
        evidence_score=review.evidence_score,
        rationale_score=review.rationale_score,
        confidence_score=review.confidence_score,
        raw_review_score=raw_review_score,
        peer_deviation_score=peer_deviation,
        disagreement_penalty=row_penalty,
        consensus_contribution_score=_clamp_ratio(raw_review_score - row_penalty),
        review_complete=review.review_complete,
        row_status="complete" if review.review_complete else "incomplete",
        reason_codes=(
            "team_specialist_review_consensus_quality_row_complete"
            if review.review_complete
            else "team_specialist_review_consensus_quality_row_incomplete",
        ),
    )


def _raw_review_score(
    review: TeamSpecialistReviewConsensusQualityGateV2Review,
    config: TeamSpecialistReviewConsensusQualityGateV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            review.evidence_score * config.evidence_weight
            + review.rationale_score * config.rationale_weight
            + review.confidence_score * config.confidence_weight,
        )


def _average_raw_score(
    rows: tuple[TeamSpecialistReviewConsensusQualityGateV2Row, ...],
) -> Decimal:
    return _average_score_values(
        tuple(row.raw_review_score for row in rows if row.review_complete),
    )


def _average_score_values(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(sum(values, ZERO) / Decimal(len(values)))


def _disagreement_ratio(
    rows: tuple[TeamSpecialistReviewConsensusQualityGateV2Row, ...],
) -> Decimal:
    complete_scores = tuple(row.raw_review_score for row in rows if row.review_complete)
    if len(complete_scores) < 2:
        return ZERO
    return _absolute_difference(max(complete_scores), min(complete_scores))


def _score_penalty(score: Decimal, weight: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(score * weight)


def _absolute_difference(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(abs(left - right))


def _complete_review_count(
    rows: tuple[TeamSpecialistReviewConsensusQualityGateV2Row, ...],
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.review_complete)).quantize(COUNT_QUANT)


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _report_reason_codes(
    *,
    specialist_count: Decimal,
    complete_review_count: Decimal,
    quorum_participation_ratio: Decimal,
    disagreement_ratio: Decimal,
    consensus_quality_score: Decimal,
    config: TeamSpecialistReviewConsensusQualityGateV2Config
    | TeamSpecialistReviewConsensusQualityGateV2Report,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if specialist_count == ZERO:
        reasons.append("team_specialist_review_consensus_quality_gate_empty")
    if specialist_count < config.min_specialist_count:
        reasons.append(
            "team_specialist_review_consensus_quality_gate_min_specialist_count_unmet",
        )
    if (
        specialist_count >= config.min_specialist_count
        and quorum_participation_ratio < config.min_quorum_participation_ratio
    ):
        reasons.append("team_specialist_review_consensus_quality_gate_quorum_unmet")
    if complete_review_count < specialist_count:
        reasons.append("team_specialist_review_consensus_quality_gate_incomplete_reviews")
    if disagreement_ratio > config.max_watch_disagreement_ratio:
        reasons.append("team_specialist_review_consensus_quality_gate_disagreement_blocked")
    if consensus_quality_score < config.min_watch_consensus_score:
        reasons.append("team_specialist_review_consensus_quality_gate_consensus_below_watch")
    if (
        config.max_pass_disagreement_ratio
        < disagreement_ratio
        <= config.max_watch_disagreement_ratio
    ):
        reasons.append("team_specialist_review_consensus_quality_gate_disagreement_watch")
    if (
        config.min_watch_consensus_score
        <= consensus_quality_score
        < config.min_pass_consensus_score
    ):
        reasons.append("team_specialist_review_consensus_quality_gate_consensus_below_pass")
    return tuple(reasons or ("team_specialist_review_consensus_quality_gate_passed",))


def _gate_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("team_specialist_review_consensus_quality_gate_passed",):
        return "pass"
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _normalize_reviews(
    value: object,
) -> tuple[TeamSpecialistReviewConsensusQualityGateV2Review, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("specialist_reviews must be an iterable")
    reviews = tuple(value)
    for item in reviews:
        if type(item) is not TeamSpecialistReviewConsensusQualityGateV2Review:
            raise ValueError(
                "specialist review items must be "
                "TeamSpecialistReviewConsensusQualityGateV2Review",
            )
        _require_hard_flags("TeamSpecialistReviewConsensusQualityGateV2Review", item)
    keys = tuple((item.cohort_id, item.specialist_id) for item in reviews)
    if len(set(keys)) != len(keys):
        raise ValueError("specialist review items must not contain duplicate keys")
    return reviews


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistReviewConsensusQualityGateV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistReviewConsensusQualityGateV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistReviewConsensusQualityGateV2Row",
            )
    return value


def _validate_config(config: TeamSpecialistReviewConsensusQualityGateV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.evidence_weight
            + config.rationale_weight
            + config.confidence_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("review score weights must sum to 1.000000")
    if config.min_watch_consensus_score > config.min_pass_consensus_score:
        raise ValueError("min_watch_consensus_score must not exceed min_pass_consensus_score")
    if config.max_pass_disagreement_ratio > config.max_watch_disagreement_ratio:
        raise ValueError(
            "max_pass_disagreement_ratio must not exceed max_watch_disagreement_ratio",
        )


def _validate_row_consistency(row: TeamSpecialistReviewConsensusQualityGateV2Row) -> None:
    expected_status = "complete" if row.review_complete else "incomplete"
    if row.row_status != expected_status:
        raise ValueError("row_status must match review_complete")
    expected_reason = (
        "team_specialist_review_consensus_quality_row_complete"
        if row.review_complete
        else "team_specialist_review_consensus_quality_row_incomplete"
    )
    if row.reason_codes != (expected_reason,):
        raise ValueError("row reason_codes must match review_complete")
    if row.consensus_contribution_score != _clamp_ratio(
        row.raw_review_score - row.disagreement_penalty,
    ):
        raise ValueError("consensus_contribution_score must match row scores")


def _validate_report_consistency(
    report: TeamSpecialistReviewConsensusQualityGateV2Report,
) -> None:
    rows = report.rows
    if report.specialist_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("specialist_count must match rows")
    if report.complete_review_count != _complete_review_count(rows):
        raise ValueError("complete_review_count must match rows")
    if report.quorum_participation_ratio != _ratio_or_zero(
        report.complete_review_count,
        report.specialist_count,
    ):
        raise ValueError("quorum_participation_ratio must match counts")
    if report.average_raw_review_score != _average_raw_score(rows):
        raise ValueError("average_raw_review_score must match rows")
    if report.disagreement_ratio != _disagreement_ratio(rows):
        raise ValueError("disagreement_ratio must match rows")
    if report.disagreement_penalty != _score_penalty(
        report.disagreement_ratio,
        report.disagreement_penalty_weight,
    ):
        raise ValueError("disagreement_penalty must match disagreement_ratio")
    if report.consensus_quality_score != _clamp_ratio(
        report.average_raw_review_score - report.disagreement_penalty,
    ):
        raise ValueError("consensus_quality_score must match score inputs")
    _validate_rows_sorted(rows)
    _validate_row_peer_scores(rows, report)
    expected_reasons = _report_reason_codes(
        specialist_count=report.specialist_count,
        complete_review_count=report.complete_review_count,
        quorum_participation_ratio=report.quorum_participation_ratio,
        disagreement_ratio=report.disagreement_ratio,
        consensus_quality_score=report.consensus_quality_score,
        config=report,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report fields")
    if report.gate_status != _gate_status(report.reason_codes):
        raise ValueError("gate_status must match reason_codes")

def _validate_rows_sorted(
    rows: tuple[TeamSpecialistReviewConsensusQualityGateV2Row, ...],
) -> None:
    expected = tuple(sorted(rows, key=lambda row: (row.cohort_id, row.specialist_id)))
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by cohort, specialist, and rank")


def _validate_row_peer_scores(
    rows: tuple[TeamSpecialistReviewConsensusQualityGateV2Row, ...],
    report: TeamSpecialistReviewConsensusQualityGateV2Report,
) -> None:
    for row in rows:
        if row.peer_deviation_score != _absolute_difference(
            row.raw_review_score,
            report.average_raw_review_score,
        ):
            raise ValueError("row peer_deviation_score must match report average")
        if row.disagreement_penalty != _score_penalty(
            row.peer_deviation_score,
            report.disagreement_penalty_weight,
        ):
            raise ValueError("row disagreement_penalty must match peer_deviation_score")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_gate_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_row_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be complete or incomplete")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _require_payload_hard_flags(payload: dict[str, object]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("paper_only must be True for payload")
    if payload.get("report_only") is not True:
        raise ValueError("report_only must be True for payload")
    if payload.get("readonly") is not True:
        raise ValueError("readonly must be True for payload")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is float:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
