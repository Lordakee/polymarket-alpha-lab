"""Pure paper-only evidence-weighted recommendation ranking v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_STRATEGY_RECOMMENDATION_EVIDENCE_WEIGHTED_RANK_V2_CONFIG_VERSION = (
    "strategy-recommendation-evidence-weighted-rank-v2-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE = Decimal("1.000000")

SIDE_YES = "yes"
SIDE_NO = "no"
SELECTED_SIDES = (SIDE_YES, SIDE_NO)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
PAPER_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

NEXT_KEEP = "keep_for_paper_review"
NEXT_COLLECT = "collect_more_evidence"
NEXT_DROP = "drop_from_paper_review"
RECOMMENDED_NEXT_STEPS = (NEXT_KEEP, NEXT_COLLECT, NEXT_DROP)
NEXT_STEP_BY_STATUS = {
    STATUS_READY: NEXT_KEEP,
    STATUS_WATCH: NEXT_COLLECT,
    STATUS_BLOCKED: NEXT_DROP,
}

READY_REASON = "strategy_recommendation_evidence_weighted_rank_v2_ready"
WEAK_EVIDENCE_REASON = (
    "strategy_recommendation_evidence_weighted_rank_v2_weak_evidence_penalty"
)
SOURCE_QUALITY_BOOST_REASON = (
    "strategy_recommendation_evidence_weighted_rank_v2_source_quality_boost"
)
EVIDENCE_STRENGTH_LOW_REASON = (
    "strategy_recommendation_evidence_weighted_rank_v2_evidence_strength_low"
)
SOURCE_QUALITY_LOW_REASON = (
    "strategy_recommendation_evidence_weighted_rank_v2_source_quality_low"
)
INDEPENDENT_SOURCES_LOW_REASON = (
    "strategy_recommendation_evidence_weighted_rank_v2_independent_sources_low"
)
SCORE_BELOW_ZERO_REASON = (
    "strategy_recommendation_evidence_weighted_rank_v2_score_below_zero"
)
REASON_CODE_SEQUENCE = (
    WEAK_EVIDENCE_REASON,
    SOURCE_QUALITY_BOOST_REASON,
    EVIDENCE_STRENGTH_LOW_REASON,
    SOURCE_QUALITY_LOW_REASON,
    INDEPENDENT_SOURCES_LOW_REASON,
    SCORE_BELOW_ZERO_REASON,
    READY_REASON,
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "ord" + "er",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sign" + "ing",
    "muta" + "tion",
    "b" + "uy",
    "s" + "ell",
    "tr" + "ade",
)

__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_EVIDENCE_WEIGHTED_RANK_V2_CONFIG_VERSION",
    "StrategyRecommendationEvidenceWeightedRankV2Config",
    "StrategyRecommendationEvidenceWeightedRankV2Input",
    "StrategyRecommendationEvidenceWeightedRankV2Row",
    "StrategyRecommendationEvidenceWeightedRankV2Report",
    "build_strategy_recommendation_evidence_weighted_rank_v2",
    "strategy_recommendation_evidence_weighted_rank_v2_payload",
)


@dataclass(frozen=True)
class StrategyRecommendationEvidenceWeightedRankV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_EVIDENCE_WEIGHTED_RANK_V2_CONFIG_VERSION
    )
    evidence_weight: Decimal = Decimal("0.350000")
    source_quality_weight: Decimal = Decimal("0.200000")
    weak_evidence_penalty_weight: Decimal = Decimal("0.250000")
    min_evidence_strength_score: Decimal = Decimal("0.600000")
    min_source_quality_score: Decimal = Decimal("0.650000")
    min_independent_source_count: Decimal = Decimal("2")
    max_weak_evidence_ratio: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRecommendationEvidenceWeightedRankV2Config:
            raise TypeError(
                "StrategyRecommendationEvidenceWeightedRankV2Config does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationEvidenceWeightedRankV2Config:
            raise ValueError(
                "config must be exactly "
                "StrategyRecommendationEvidenceWeightedRankV2Config",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_RECOMMENDATION_EVIDENCE_WEIGHTED_RANK_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "evidence_weight",
            "source_quality_weight",
            "weak_evidence_penalty_weight",
            "min_evidence_strength_score",
            "min_source_quality_score",
            "max_weak_evidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_independent_source_count",
            _require_positive_count_decimal(
                "min_independent_source_count",
                self.min_independent_source_count,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationEvidenceWeightedRankV2Input:
    recommendation_id: str
    market_slug: str
    selected_side: str
    model_probability: Decimal
    market_probability: Decimal
    expected_edge: Decimal
    evidence_strength_score: Decimal
    source_quality_score: Decimal
    independent_source_count: Decimal
    weak_evidence_count: Decimal
    source_reference: str
    rationale_summary: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRecommendationEvidenceWeightedRankV2Input:
            raise TypeError(
                "StrategyRecommendationEvidenceWeightedRankV2Input does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationEvidenceWeightedRankV2Input:
            raise ValueError(
                "candidate must be exactly "
                "StrategyRecommendationEvidenceWeightedRankV2Input",
            )
        for field_name in (
            "recommendation_id",
            "market_slug",
            "source_reference",
            "rationale_summary",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("selected_side", self.selected_side, SELECTED_SIDES)
        for field_name in (
            "model_probability",
            "market_probability",
            "evidence_strength_score",
            "source_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_edge",
            _require_signed_ratio_decimal("expected_edge", self.expected_edge),
        )
        for field_name in ("independent_source_count", "weak_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        expected_edge = _q(self.model_probability - self.market_probability)
        if self.expected_edge != expected_edge:
            raise ValueError("expected_edge must match model minus market probability")
        if self.weak_evidence_count > self.independent_source_count:
            raise ValueError(
                "weak_evidence_count must not exceed independent_source_count",
            )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyRecommendationEvidenceWeightedRankV2Row:
    recommendation_id: str
    market_slug: str
    selected_side: str
    model_probability: Decimal
    market_probability: Decimal
    expected_edge: Decimal
    evidence_strength_score: Decimal
    source_quality_score: Decimal
    independent_source_count: Decimal
    weak_evidence_count: Decimal
    weak_evidence_ratio: Decimal
    evidence_weighted_rank_score: Decimal
    recommendation_rank: Decimal
    paper_status: str
    recommended_next_step: str
    source_reference: str
    rationale_summary: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    payload: dict[str, Any] | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRecommendationEvidenceWeightedRankV2Row:
            raise TypeError(
                "StrategyRecommendationEvidenceWeightedRankV2Row does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationEvidenceWeightedRankV2Row:
            raise ValueError(
                "row must be exactly StrategyRecommendationEvidenceWeightedRankV2Row",
            )
        for field_name in (
            "recommendation_id",
            "market_slug",
            "source_reference",
            "rationale_summary",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("selected_side", self.selected_side, SELECTED_SIDES)
        for field_name in (
            "model_probability",
            "market_probability",
            "evidence_strength_score",
            "source_quality_score",
            "weak_evidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_edge",
            _require_signed_ratio_decimal("expected_edge", self.expected_edge),
        )
        object.__setattr__(
            self,
            "evidence_weighted_rank_score",
            _require_decimal(
                "evidence_weighted_rank_score",
                self.evidence_weighted_rank_score,
            ),
        )
        for field_name in (
            "independent_source_count",
            "weak_evidence_count",
            "recommendation_rank",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_or_zero_count_for_field(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.recommendation_rank <= ZERO_COUNT:
            raise ValueError("recommendation_rank must be positive")
        _require_member("paper_status", self.paper_status, PAPER_STATUSES)
        _require_member(
            "recommended_next_step",
            self.recommended_next_step,
            RECOMMENDED_NEXT_STEPS,
        )
        if self.recommended_next_step != NEXT_STEP_BY_STATUS[self.paper_status]:
            raise ValueError("recommended_next_step must match paper_status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        expected_digest = _validation_digest(_row_digest_material(self))
        if self.derived_validation_digest:
            _require_digest_string(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match row fields")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                expected_digest,
            )
        expected_payload = _row_payload(self)
        if self.payload is not None and self.payload != expected_payload:
            raise ValueError("payload does not match row fields")
        object.__setattr__(self, "payload", expected_payload)


@dataclass(frozen=True)
class StrategyRecommendationEvidenceWeightedRankV2Report:
    config_version: str
    recommendation_count: Decimal
    top_recommendation_id: str
    ranked_recommendations: tuple[StrategyRecommendationEvidenceWeightedRankV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    payload: dict[str, Any] | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRecommendationEvidenceWeightedRankV2Report:
            raise TypeError(
                "StrategyRecommendationEvidenceWeightedRankV2Report does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationEvidenceWeightedRankV2Report:
            raise ValueError(
                "report must be exactly "
                "StrategyRecommendationEvidenceWeightedRankV2Report",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_RECOMMENDATION_EVIDENCE_WEIGHTED_RANK_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "recommendation_count",
            _require_nonnegative_count_decimal(
                "recommendation_count",
                self.recommendation_count,
            ),
        )
        _require_public_string("top_recommendation_id", self.top_recommendation_id)
        object.__setattr__(
            self,
            "ranked_recommendations",
            _normalize_rows(self.ranked_recommendations),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        expected_digest = _validation_digest(_report_digest_material(self))
        if self.derived_validation_digest:
            _require_digest_string(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report fields")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                expected_digest,
            )
        expected_payload = _report_payload(self)
        if self.payload is not None and self.payload != expected_payload:
            raise ValueError("payload does not match report fields")
        object.__setattr__(self, "payload", expected_payload)


def build_strategy_recommendation_evidence_weighted_rank_v2(
    candidates: tuple[StrategyRecommendationEvidenceWeightedRankV2Input, ...],
    *,
    config: StrategyRecommendationEvidenceWeightedRankV2Config | None = None,
) -> StrategyRecommendationEvidenceWeightedRankV2Report:
    cfg = config or StrategyRecommendationEvidenceWeightedRankV2Config()
    if type(cfg) is not StrategyRecommendationEvidenceWeightedRankV2Config:
        raise ValueError(
            "config must be exactly "
            "StrategyRecommendationEvidenceWeightedRankV2Config",
        )
    _require_hard_flags("config", cfg)
    rows_without_rank = tuple(_row_for_candidate(candidate, cfg) for candidate in candidates)
    ranked_rows = tuple(
        _ranked_row(row, rank)
        for rank, row in enumerate(
            sorted(
                rows_without_rank,
                key=lambda item: (
                    -item.evidence_weighted_rank_score,
                    item.paper_status,
                    item.market_slug,
                    item.recommendation_id,
                ),
            ),
            start=1,
        )
    )
    report_reasons = _report_reason_codes(ranked_rows)
    top_id = ranked_rows[0].recommendation_id if ranked_rows else "none"
    return StrategyRecommendationEvidenceWeightedRankV2Report(
        config_version=cfg.config_version,
        recommendation_count=_count(len(ranked_rows)),
        top_recommendation_id=top_id,
        ranked_recommendations=ranked_rows,
        reason_codes=report_reasons,
    )


def strategy_recommendation_evidence_weighted_rank_v2_payload(
    value: (
        StrategyRecommendationEvidenceWeightedRankV2Report
        | StrategyRecommendationEvidenceWeightedRankV2Row
        | dict[str, Any]
    ),
) -> dict[str, Any]:
    if type(value) is StrategyRecommendationEvidenceWeightedRankV2Report:
        _require_hard_flags("report", value)
        return _report_payload(value)
    if type(value) is StrategyRecommendationEvidenceWeightedRankV2Row:
        _require_hard_flags("row", value)
        return _row_payload(value)
    if type(value) is dict:
        _reject_unsafe_public_payload("payload", value)
        _require_payload_flags(value)
        _validate_payload_digest(value)
        return _json_ready(value)
    raise ValueError("value must be a report, row, or payload dict")


def _row_for_candidate(
    candidate: StrategyRecommendationEvidenceWeightedRankV2Input,
    config: StrategyRecommendationEvidenceWeightedRankV2Config,
) -> StrategyRecommendationEvidenceWeightedRankV2Row:
    if type(candidate) is not StrategyRecommendationEvidenceWeightedRankV2Input:
        raise ValueError(
            "candidates must contain "
            "StrategyRecommendationEvidenceWeightedRankV2Input values",
        )
    _require_hard_flags("candidate", candidate)
    weak_ratio = _weak_evidence_ratio(candidate)
    score = _rank_score(candidate, config, weak_ratio)
    reasons = _row_reason_codes(candidate, config, weak_ratio, score)
    status = _paper_status(candidate, config, weak_ratio, score)
    return StrategyRecommendationEvidenceWeightedRankV2Row(
        recommendation_id=candidate.recommendation_id,
        market_slug=candidate.market_slug,
        selected_side=candidate.selected_side,
        model_probability=candidate.model_probability,
        market_probability=candidate.market_probability,
        expected_edge=candidate.expected_edge,
        evidence_strength_score=candidate.evidence_strength_score,
        source_quality_score=candidate.source_quality_score,
        independent_source_count=candidate.independent_source_count,
        weak_evidence_count=candidate.weak_evidence_count,
        weak_evidence_ratio=weak_ratio,
        evidence_weighted_rank_score=score,
        recommendation_rank=Decimal("1"),
        paper_status=status,
        recommended_next_step=NEXT_STEP_BY_STATUS[status],
        source_reference=candidate.source_reference,
        rationale_summary=candidate.rationale_summary,
        reason_codes=reasons,
    )


def _ranked_row(
    row: StrategyRecommendationEvidenceWeightedRankV2Row,
    rank: int,
) -> StrategyRecommendationEvidenceWeightedRankV2Row:
    return StrategyRecommendationEvidenceWeightedRankV2Row(
        recommendation_id=row.recommendation_id,
        market_slug=row.market_slug,
        selected_side=row.selected_side,
        model_probability=row.model_probability,
        market_probability=row.market_probability,
        expected_edge=row.expected_edge,
        evidence_strength_score=row.evidence_strength_score,
        source_quality_score=row.source_quality_score,
        independent_source_count=row.independent_source_count,
        weak_evidence_count=row.weak_evidence_count,
        weak_evidence_ratio=row.weak_evidence_ratio,
        evidence_weighted_rank_score=row.evidence_weighted_rank_score,
        recommendation_rank=_count(rank),
        paper_status=row.paper_status,
        recommended_next_step=row.recommended_next_step,
        source_reference=row.source_reference,
        rationale_summary=row.rationale_summary,
        reason_codes=row.reason_codes,
    )


def _rank_score(
    candidate: StrategyRecommendationEvidenceWeightedRankV2Input,
    config: StrategyRecommendationEvidenceWeightedRankV2Config,
    weak_ratio: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _q(
            candidate.expected_edge
            + (candidate.evidence_strength_score * config.evidence_weight)
            + (candidate.source_quality_score * config.source_quality_weight)
            - (weak_ratio * config.weak_evidence_penalty_weight),
        )


def _weak_evidence_ratio(
    candidate: StrategyRecommendationEvidenceWeightedRankV2Input,
) -> Decimal:
    if candidate.independent_source_count == ZERO_COUNT:
        return ZERO
    return _ratio(candidate.weak_evidence_count, candidate.independent_source_count)


def _row_reason_codes(
    candidate: StrategyRecommendationEvidenceWeightedRankV2Input,
    config: StrategyRecommendationEvidenceWeightedRankV2Config,
    weak_ratio: Decimal,
    score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if candidate.weak_evidence_count > ZERO_COUNT:
        reasons.append(WEAK_EVIDENCE_REASON)
    if candidate.source_quality_score >= config.min_source_quality_score:
        reasons.append(SOURCE_QUALITY_BOOST_REASON)
    if candidate.evidence_strength_score < config.min_evidence_strength_score:
        reasons.append(EVIDENCE_STRENGTH_LOW_REASON)
    if candidate.source_quality_score < config.min_source_quality_score:
        reasons.append(SOURCE_QUALITY_LOW_REASON)
    if candidate.independent_source_count < config.min_independent_source_count:
        reasons.append(INDEPENDENT_SOURCES_LOW_REASON)
    if score < ZERO:
        reasons.append(SCORE_BELOW_ZERO_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _paper_status(
    candidate: StrategyRecommendationEvidenceWeightedRankV2Input,
    config: StrategyRecommendationEvidenceWeightedRankV2Config,
    weak_ratio: Decimal,
    score: Decimal,
) -> str:
    if (
        candidate.independent_source_count == ZERO_COUNT
        or weak_ratio > config.max_weak_evidence_ratio
        or score < ZERO
    ):
        return STATUS_BLOCKED
    if (
        candidate.evidence_strength_score < config.min_evidence_strength_score
        or candidate.source_quality_score < config.min_source_quality_score
        or candidate.independent_source_count < config.min_independent_source_count
        or candidate.weak_evidence_count > ZERO_COUNT
    ):
        return STATUS_WATCH
    return STATUS_READY


def _report_reason_codes(
    rows: tuple[StrategyRecommendationEvidenceWeightedRankV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (INDEPENDENT_SOURCES_LOW_REASON,)
    reasons: list[str] = []
    for reason_code in REASON_CODE_SEQUENCE:
        if any(reason_code in row.reason_codes for row in rows):
            reasons.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _row_payload(row: StrategyRecommendationEvidenceWeightedRankV2Row) -> dict[str, Any]:
    return _json_ready(_row_payload_value(row))


def _report_payload(
    report: StrategyRecommendationEvidenceWeightedRankV2Report,
) -> dict[str, Any]:
    return _json_ready(
        {
            "config_version": report.config_version,
            "recommendation_count": report.recommendation_count,
            "top_recommendation_id": report.top_recommendation_id,
            "ranked_recommendations": report.ranked_recommendations,
            "reason_codes": report.reason_codes,
            "derived_validation_digest": report.derived_validation_digest,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _row_payload_value(row: StrategyRecommendationEvidenceWeightedRankV2Row) -> dict[str, Any]:
    return {
        "recommendation_id": row.recommendation_id,
        "market_slug": row.market_slug,
        "selected_side": row.selected_side,
        "model_probability": row.model_probability,
        "market_probability": row.market_probability,
        "expected_edge": row.expected_edge,
        "evidence_strength_score": row.evidence_strength_score,
        "source_quality_score": row.source_quality_score,
        "independent_source_count": row.independent_source_count,
        "weak_evidence_count": row.weak_evidence_count,
        "weak_evidence_ratio": row.weak_evidence_ratio,
        "evidence_weighted_rank_score": row.evidence_weighted_rank_score,
        "recommendation_rank": row.recommendation_rank,
        "paper_status": row.paper_status,
        "recommended_next_step": row.recommended_next_step,
        "source_reference": row.source_reference,
        "rationale_summary": row.rationale_summary,
        "reason_codes": row.reason_codes,
        "derived_validation_digest": row.derived_validation_digest,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _row_digest_material(row: StrategyRecommendationEvidenceWeightedRankV2Row) -> dict[str, Any]:
    value = _row_payload_value(row)
    value.pop("derived_validation_digest")
    return _json_ready(value)


def _report_digest_material(
    report: StrategyRecommendationEvidenceWeightedRankV2Report,
) -> dict[str, Any]:
    return _json_ready(
        {
            "config_version": report.config_version,
            "recommendation_count": report.recommendation_count,
            "top_recommendation_id": report.top_recommendation_id,
            "ranked_recommendations": report.ranked_recommendations,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _validation_digest(value: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("digest_material", value)
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest(value: dict[str, Any]) -> None:
    if "ranked_recommendations" in value:
        rows = value["ranked_recommendations"]
        if type(rows) is not list:
            raise ValueError("ranked_recommendations must be a list")
        for row in rows:
            if type(row) is not dict:
                raise ValueError("ranked_recommendations must contain row payloads")
            _validate_row_payload_digest(row)
        expected = _validation_digest(_report_digest_material_from_payload(value))
        if value.get("derived_validation_digest") != expected:
            raise ValueError("derived_validation_digest does not match report payload")
        return
    _validate_row_payload_digest(value)


def _validate_row_payload_digest(value: dict[str, Any]) -> None:
    expected = _validation_digest(_row_digest_material_from_payload(value))
    if value.get("derived_validation_digest") != expected:
        raise ValueError("derived_validation_digest does not match row payload")


def _row_digest_material_from_payload(value: dict[str, Any]) -> dict[str, Any]:
    material = dict(value)
    material.pop("derived_validation_digest", None)
    return _json_ready(material)


def _report_digest_material_from_payload(value: dict[str, Any]) -> dict[str, Any]:
    material = dict(value)
    material.pop("derived_validation_digest", None)
    return _json_ready(material)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        _require_decimal("JSON Decimal value", value)
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
            if field.name != "payload"
        }
    if type(value) is bool:
        return value
    if value is None:
        return None
    if type(value) is str:
        _reject_unsafe_public_value("JSON string", value)
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        _reject_unsafe_public_payload("JSON object", value)
        return {key: _json_ready(item) for key, item in value.items()}
    raise ValueError("value is not JSON serializable")


def _validate_row_consistency(
    row: StrategyRecommendationEvidenceWeightedRankV2Row,
) -> None:
    if row.expected_edge != _q(row.model_probability - row.market_probability):
        raise ValueError("expected_edge must match model minus market probability")
    if row.weak_evidence_count > row.independent_source_count:
        raise ValueError("weak_evidence_count must not exceed independent_source_count")
    expected_ratio = (
        ZERO
        if row.independent_source_count == ZERO_COUNT
        else _ratio(row.weak_evidence_count, row.independent_source_count)
    )
    if row.weak_evidence_ratio != expected_ratio:
        raise ValueError("weak_evidence_ratio must match weak divided by independent")


def _validate_report_consistency(
    report: StrategyRecommendationEvidenceWeightedRankV2Report,
) -> None:
    rows = report.ranked_recommendations
    if report.recommendation_count != _count(len(rows)):
        raise ValueError("recommendation_count must match ranked recommendations")
    expected_top = rows[0].recommendation_id if rows else "none"
    if report.top_recommendation_id != expected_top:
        raise ValueError("top_recommendation_id must match first ranked row")
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.recommendation_rank for row in rows) != expected_ranks:
        raise ValueError("recommendation_rank values must be sequential")
    if tuple(rows) != tuple(
        sorted(
            rows,
            key=lambda item: (
                item.recommendation_rank,
                -item.evidence_weighted_rank_score,
                item.market_slug,
                item.recommendation_id,
            ),
        ),
    ):
        raise ValueError("ranked_recommendations must be sorted by rank")


def _normalize_rows(value: object) -> tuple[StrategyRecommendationEvidenceWeightedRankV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("ranked_recommendations must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationEvidenceWeightedRankV2Row:
            raise ValueError(
                "ranked_recommendations must contain "
                "StrategyRecommendationEvidenceWeightedRankV2Row values",
            )
        _require_hard_flags("row", row)
        if row.recommendation_id in seen:
            raise ValueError("ranked_recommendations must not contain duplicates")
        seen.add(row.recommendation_id)
    return rows


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member(field_name, code, REASON_CODE_SEQUENCE)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} values must be unique")
    expected = tuple(code for code in REASON_CODE_SEQUENCE if code in codes)
    if codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return codes


def _require_payload_flags(value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_member(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be a known value")


def _require_public_string(field_name: str, value: object) -> None:
    _require_plain_string(field_name, value)
    _reject_unsafe_public_value(field_name, value)


def _require_plain_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _require_digest_string(field_name: str, value: object) -> None:
    _require_plain_string(field_name, value)
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_public_value(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_value(label, value)


def _reject_unsafe_public_value(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _q(decimal_value)


def _require_signed_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return _q(decimal_value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(COUNT_QUANTUM)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_positive_or_zero_count_for_field(
    field_name: str,
    value: object,
) -> Decimal:
    return _require_nonnegative_count_decimal(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _q(numerator / denominator)


def _count(value: int) -> Decimal:
    return Decimal(str(value)).quantize(COUNT_QUANTUM)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)
