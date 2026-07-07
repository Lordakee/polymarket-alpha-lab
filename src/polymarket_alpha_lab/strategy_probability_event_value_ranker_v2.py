"""Phase 1 paper-only probability-event value ranker.

The module is intentionally pure and report-only: it ranks provided candidate
snapshots without opening any external surface or creating executable actions.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from typing import Any


DEFAULT_STRATEGY_PROBABILITY_EVENT_VALUE_RANKER_V2_CONFIG_VERSION = (
    "strategy-probability-event-value-ranker-v2"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
RECOMMENDATION_POSTURES = ("recommend", "watch", "reject")
REPORT_STATUSES = ("empty", "ranked")
ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "rank",
    "candidate_id",
    "event_id",
    "market_slug",
    "outcome_name",
    "category",
    "recommendation_posture",
    "implied_probability",
    "model_probability",
    "probability_edge",
    "information_quality_score",
    "liquidity_score",
    "specialist_consensus_score",
    "resolution_risk_score",
    "category_exposure_score",
    "composite_value_score",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_FIELDS = (
    *ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "report_status",
    "recommendation_count",
    "recommend_count",
    "watch_count",
    "reject_count",
    "min_recommendation_score",
    "min_edge",
    "min_information_quality_score",
    "min_liquidity_score",
    "max_resolution_risk_score",
    "max_category_exposure_score",
    "rows",
    "reason_code_counts",
    "source_categories",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    *REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
UNSAFE_PUBLIC_TEXT_TOKENS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sign" + "ing",
    "mut" + "ation",
    "bu" + "y",
    "se" + "ll",
    "tra" + "de",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class StrategyProbabilityEventValueRankerV2Config(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_STRATEGY_PROBABILITY_EVENT_VALUE_RANKER_V2_CONFIG_VERSION
    )
    min_recommendation_score: Decimal = Decimal("0.250000")
    min_edge: Decimal = Decimal("0.030000")
    min_information_quality_score: Decimal = Decimal("0.600000")
    min_liquidity_score: Decimal = Decimal("0.500000")
    max_resolution_risk_score: Decimal = Decimal("0.300000")
    max_category_exposure_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyProbabilityEventValueRankerV2Config, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_PROBABILITY_EVENT_VALUE_RANKER_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_recommendation_score",
            "min_edge",
            "min_information_quality_score",
            "min_liquidity_score",
            "max_resolution_risk_score",
            "max_category_exposure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _config_public_payload(self))


@dataclass(frozen=True)
class StrategyProbabilityEventValueRankerV2Candidate(_FinalPublicDataclass):
    candidate_id: str
    event_id: str
    market_slug: str
    outcome_name: str
    category: str
    implied_probability: Decimal
    model_probability: Decimal
    information_quality_score: Decimal
    liquidity_score: Decimal
    specialist_consensus_score: Decimal
    resolution_risk_score: Decimal
    category_exposure_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyProbabilityEventValueRankerV2Candidate,
            "candidate",
        )
        for field_name in (
            "candidate_id",
            "event_id",
            "market_slug",
            "outcome_name",
            "category",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "implied_probability",
            "model_probability",
            "information_quality_score",
            "liquidity_score",
            "specialist_consensus_score",
            "resolution_risk_score",
            "category_exposure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("candidate", self)
        _reject_unsafe_public_payload("candidate", _candidate_public_probe(self))


@dataclass(frozen=True)
class StrategyProbabilityEventValueRankerV2Row(_FinalPublicDataclass):
    rank: Decimal
    candidate_id: str
    event_id: str
    market_slug: str
    outcome_name: str
    category: str
    recommendation_posture: str
    implied_probability: Decimal
    model_probability: Decimal
    probability_edge: Decimal
    information_quality_score: Decimal
    liquidity_score: Decimal
    specialist_consensus_score: Decimal
    resolution_risk_score: Decimal
    category_exposure_score: Decimal
    composite_value_score: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyProbabilityEventValueRankerV2Row, "row")
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_whole_decimal("rank", self.rank),
        )
        for field_name in (
            "candidate_id",
            "event_id",
            "market_slug",
            "outcome_name",
            "category",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member(
            "recommendation_posture",
            self.recommendation_posture,
            RECOMMENDATION_POSTURES,
        )
        for field_name in (
            "implied_probability",
            "model_probability",
            "information_quality_score",
            "liquidity_score",
            "specialist_consensus_score",
            "resolution_risk_score",
            "category_exposure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("probability_edge", "composite_value_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_derived_fields(self)
        _reject_unsafe_public_payload("row", _row_public_payload_values(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_row_derived_validation_digest(self)


@dataclass(frozen=True)
class StrategyProbabilityEventValueRankerV2ReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyProbabilityEventValueRankerV2ReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload(
            "reason_code_count",
            _reason_code_count_public_payload(self),
        )


@dataclass(frozen=True)
class StrategyProbabilityEventValueRankerV2Report(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    recommendation_count: Decimal
    recommend_count: Decimal
    watch_count: Decimal
    reject_count: Decimal
    min_recommendation_score: Decimal
    min_edge: Decimal
    min_information_quality_score: Decimal
    min_liquidity_score: Decimal
    max_resolution_risk_score: Decimal
    max_category_exposure_score: Decimal
    rows: tuple[StrategyProbabilityEventValueRankerV2Row, ...]
    reason_code_counts: tuple[StrategyProbabilityEventValueRankerV2ReasonCodeCount, ...]
    source_categories: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyProbabilityEventValueRankerV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_PROBABILITY_EVENT_VALUE_RANKER_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "recommendation_count",
            "recommend_count",
            "watch_count",
            "reject_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_recommendation_score",
            "min_edge",
            "min_information_quality_score",
            "min_liquidity_score",
            "max_resolution_risk_score",
            "max_category_exposure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "source_categories",
            _normalize_string_tuple("source_categories", self.source_categories),
        )
        _require_hard_flags("report", self)
        _validate_report_derived_fields(self)
        _reject_unsafe_public_payload("report", _report_public_payload_values(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)


def build_strategy_probability_event_value_ranker_v2_report(
    candidates: tuple[StrategyProbabilityEventValueRankerV2Candidate, ...]
    | list[StrategyProbabilityEventValueRankerV2Candidate],
    *,
    config: StrategyProbabilityEventValueRankerV2Config
    | None = None,
    generated_at: datetime,
) -> StrategyProbabilityEventValueRankerV2Report:
    """Rank probability-event candidates into paper-only recommendation postures."""

    if config is None:
        config = StrategyProbabilityEventValueRankerV2Config()
    _require_exact_type(config, StrategyProbabilityEventValueRankerV2Config, "config")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    rows = tuple(
        _row_for_candidate(candidate, config=config, rank=COUNT_ONE)
        for candidate in normalized_candidates
    )
    sorted_rows = tuple(
        replace(
            row,
            rank=_count_decimal(index + 1),
            derived_validation_digest="",
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key))
    )
    reason_code_counts = _reason_code_counts(sorted_rows)
    return StrategyProbabilityEventValueRankerV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        report_status="ranked" if sorted_rows else "empty",
        recommendation_count=_count_decimal(len(sorted_rows)),
        recommend_count=_count_decimal(
            sum(1 for row in sorted_rows if row.recommendation_posture == "recommend"),
        ),
        watch_count=_count_decimal(
            sum(1 for row in sorted_rows if row.recommendation_posture == "watch"),
        ),
        reject_count=_count_decimal(
            sum(1 for row in sorted_rows if row.recommendation_posture == "reject"),
        ),
        min_recommendation_score=config.min_recommendation_score,
        min_edge=config.min_edge,
        min_information_quality_score=config.min_information_quality_score,
        min_liquidity_score=config.min_liquidity_score,
        max_resolution_risk_score=config.max_resolution_risk_score,
        max_category_exposure_score=config.max_category_exposure_score,
        rows=sorted_rows,
        reason_code_counts=reason_code_counts,
        source_categories=tuple(
            sorted(dict.fromkeys(candidate.category for candidate in normalized_candidates)),
        ),
    )


def strategy_probability_event_value_ranker_v2_payload(
    report: StrategyProbabilityEventValueRankerV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is StrategyProbabilityEventValueRankerV2Report:
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_values(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        validate_strategy_probability_event_value_ranker_v2_public_payload(payload)
        return payload
    if type(report) is dict:
        validate_strategy_probability_event_value_ranker_v2_public_payload(report)
        return dict(report)
    raise ValueError(
        "report must be a StrategyProbabilityEventValueRankerV2Report or public payload",
    )


def validate_strategy_probability_event_value_ranker_v2_public_payload(
    payload: object,
) -> None:
    _reject_unsafe_public_payload(
        "strategy probability event value ranker v2 public payload",
        payload,
    )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_payload_fields("public payload", payload, REPORT_PAYLOAD_FIELDS)
    for field_name in (
        "generated_at",
        "config_version",
        "report_status",
    ):
        _require_canonical_string(field_name, payload[field_name])
    _require_member("report_status", payload["report_status"], REPORT_STATUSES)
    for field_name in (
        "recommendation_count",
        "recommend_count",
        "watch_count",
        "reject_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    for field_name in (
        "min_recommendation_score",
        "min_edge",
        "min_information_quality_score",
        "min_liquidity_score",
        "max_resolution_risk_score",
        "max_category_exposure_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], ratio=True)
    rows = _require_public_rows(payload["rows"])
    reason_code_counts = _require_public_reason_code_counts(payload["reason_code_counts"])
    source_categories = _require_public_string_list("source_categories", payload["source_categories"])
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _normalize_sha256(DERIVED_VALIDATION_DIGEST_FIELD, payload[DERIVED_VALIDATION_DIGEST_FIELD])
    _validate_public_row_digests(rows)
    expected_reason_code_counts = _public_reason_code_counts(rows)
    if reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    if Decimal(str(payload["recommendation_count"])) != _count_decimal(len(rows)):
        raise ValueError("recommendation_count must match rows")
    posture_counts = _public_posture_counts(rows)
    for field_name, posture in (
        ("recommend_count", "recommend"),
        ("watch_count", "watch"),
        ("reject_count", "reject"),
    ):
        if Decimal(str(payload[field_name])) != posture_counts[posture]:
            raise ValueError(f"{field_name} must match rows")
    if payload["report_status"] == "empty" and rows:
        raise ValueError("report_status must match rows")
    if payload["report_status"] == "ranked" and not rows:
        raise ValueError("report_status must match rows")
    expected_categories = tuple(sorted(dict.fromkeys(str(row["category"]) for row in rows)))
    if source_categories != expected_categories:
        raise ValueError("source_categories must match rows")
    expected_digest = _digest_public_payload(
        "strategy_probability_event_value_ranker_v2_report",
        _payload_without_digest(payload, REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST),
    )
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != expected_digest:
        raise ValueError("derived_validation_digest must match public payload")


def _row_for_candidate(
    candidate: StrategyProbabilityEventValueRankerV2Candidate,
    *,
    config: StrategyProbabilityEventValueRankerV2Config,
    rank: Decimal,
) -> StrategyProbabilityEventValueRankerV2Row:
    edge = _quantize(candidate.model_probability - candidate.implied_probability)
    composite_score = _composite_value_score(candidate, edge)
    posture = _recommendation_posture(
        candidate,
        config=config,
        probability_edge=edge,
        composite_value_score=composite_score,
    )
    return StrategyProbabilityEventValueRankerV2Row(
        rank=rank,
        candidate_id=candidate.candidate_id,
        event_id=candidate.event_id,
        market_slug=candidate.market_slug,
        outcome_name=candidate.outcome_name,
        category=candidate.category,
        recommendation_posture=posture,
        implied_probability=candidate.implied_probability,
        model_probability=candidate.model_probability,
        probability_edge=edge,
        information_quality_score=candidate.information_quality_score,
        liquidity_score=candidate.liquidity_score,
        specialist_consensus_score=candidate.specialist_consensus_score,
        resolution_risk_score=candidate.resolution_risk_score,
        category_exposure_score=candidate.category_exposure_score,
        composite_value_score=composite_score,
        reason_codes=_row_reason_codes(
            candidate,
            config=config,
            probability_edge=edge,
            composite_value_score=composite_score,
            recommendation_posture=posture,
        ),
    )


def _composite_value_score(
    candidate: StrategyProbabilityEventValueRankerV2Candidate,
    probability_edge: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        raw_score = probability_edge
        raw_score += candidate.information_quality_score * Decimal("0.100000")
        raw_score += candidate.liquidity_score * Decimal("0.100000")
        raw_score += candidate.specialist_consensus_score * Decimal("0.100000")
        raw_score += (ONE - candidate.resolution_risk_score) * Decimal("0.050000")
        raw_score += (ONE - candidate.category_exposure_score) * Decimal("0.025000")
    return _quantize(raw_score)


def _recommendation_posture(
    candidate: StrategyProbabilityEventValueRankerV2Candidate,
    *,
    config: StrategyProbabilityEventValueRankerV2Config,
    probability_edge: Decimal,
    composite_value_score: Decimal,
) -> str:
    if probability_edge <= ZERO:
        return "reject"
    if candidate.information_quality_score < config.min_information_quality_score:
        return "reject"
    if candidate.liquidity_score < config.min_liquidity_score:
        return "reject"
    if candidate.resolution_risk_score > config.max_resolution_risk_score:
        return "reject"
    if composite_value_score < config.min_recommendation_score:
        return "reject"
    if probability_edge < config.min_edge:
        return "watch"
    if candidate.category_exposure_score > config.max_category_exposure_score:
        return "watch"
    return "recommend"


def _row_reason_codes(
    candidate: StrategyProbabilityEventValueRankerV2Candidate,
    *,
    config: StrategyProbabilityEventValueRankerV2Config,
    probability_edge: Decimal,
    composite_value_score: Decimal,
    recommendation_posture: str,
) -> tuple[str, ...]:
    reasons = [f"recommendation_posture_{recommendation_posture}"]
    if probability_edge <= ZERO:
        reasons.append("edge_not_positive")
    elif probability_edge < config.min_edge:
        reasons.append("edge_below_minimum")
    else:
        reasons.append("edge_meets_minimum")
    if candidate.information_quality_score < config.min_information_quality_score:
        reasons.append("information_quality_low")
    else:
        reasons.append("information_quality_confirmed")
    if candidate.liquidity_score < config.min_liquidity_score:
        reasons.append("liquidity_low")
    else:
        reasons.append("liquidity_confirmed")
    if candidate.resolution_risk_score > config.max_resolution_risk_score:
        reasons.append("resolution_risk_high")
    else:
        reasons.append("resolution_risk_acceptable")
    if candidate.category_exposure_score > config.max_category_exposure_score:
        reasons.append("category_exposure_high")
    else:
        reasons.append("category_exposure_acceptable")
    if composite_value_score < config.min_recommendation_score:
        reasons.append("score_below_recommendation_minimum")
    else:
        reasons.append("score_meets_recommendation_minimum")
    reasons.extend(candidate.reason_codes)
    return tuple(dict.fromkeys(reasons))


def _row_sort_key(row: StrategyProbabilityEventValueRankerV2Row) -> tuple[int, Decimal, Decimal, str]:
    posture_order = {"recommend": 0, "watch": 1, "reject": 2}
    return (
        posture_order[row.recommendation_posture],
        -row.composite_value_score,
        -row.probability_edge,
        row.candidate_id,
    )


def _reason_code_counts(
    rows: tuple[StrategyProbabilityEventValueRankerV2Row, ...],
) -> tuple[StrategyProbabilityEventValueRankerV2ReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        StrategyProbabilityEventValueRankerV2ReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _validate_row_derived_fields(row: StrategyProbabilityEventValueRankerV2Row) -> None:
    expected_edge = _quantize(row.model_probability - row.implied_probability)
    if row.probability_edge != expected_edge:
        raise ValueError("probability_edge must match candidate probabilities")
    expected_score = _quantize(
        row.probability_edge
        + row.information_quality_score * Decimal("0.100000")
        + row.liquidity_score * Decimal("0.100000")
        + row.specialist_consensus_score * Decimal("0.100000")
        + (ONE - row.resolution_risk_score) * Decimal("0.050000")
        + (ONE - row.category_exposure_score) * Decimal("0.025000"),
    )
    if row.composite_value_score != expected_score:
        raise ValueError("composite_value_score must match row inputs")


def _validate_report_derived_fields(report: StrategyProbabilityEventValueRankerV2Report) -> None:
    rows = report.rows
    if report.recommendation_count != _count_decimal(len(rows)):
        raise ValueError("recommendation_count must match rows")
    for field_name, posture in (
        ("recommend_count", "recommend"),
        ("watch_count", "watch"),
        ("reject_count", "reject"),
    ):
        expected_count = _count_decimal(
            sum(1 for row in rows if row.recommendation_posture == posture),
        )
        if getattr(report, field_name) != expected_count:
            raise ValueError(f"{field_name} must match rows")
    if report.report_status == "empty" and rows:
        raise ValueError("report_status must match rows")
    if report.report_status == "ranked" and not rows:
        raise ValueError("report_status must match rows")
    expected_reason_counts = _reason_code_counts(rows)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    expected_categories = tuple(sorted(dict.fromkeys(row.category for row in rows)))
    if report.source_categories != expected_categories:
        raise ValueError("source_categories must match rows")
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be sorted by recommendation posture and value score")
    expected_ranks = tuple(_count_decimal(index + 1) for index, _row in enumerate(rows))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("row ranks must be sequential")
    for row in rows:
        _validate_row_derived_validation_digest(row)


def _row_public_payload_values(
    row: StrategyProbabilityEventValueRankerV2Row,
) -> dict[str, object]:
    return {
        "rank": _decimal_payload(row.rank),
        "candidate_id": row.candidate_id,
        "event_id": row.event_id,
        "market_slug": row.market_slug,
        "outcome_name": row.outcome_name,
        "category": row.category,
        "recommendation_posture": row.recommendation_posture,
        "implied_probability": _decimal_payload(row.implied_probability),
        "model_probability": _decimal_payload(row.model_probability),
        "probability_edge": _decimal_payload(row.probability_edge),
        "information_quality_score": _decimal_payload(row.information_quality_score),
        "liquidity_score": _decimal_payload(row.liquidity_score),
        "specialist_consensus_score": _decimal_payload(row.specialist_consensus_score),
        "resolution_risk_score": _decimal_payload(row.resolution_risk_score),
        "category_exposure_score": _decimal_payload(row.category_exposure_score),
        "composite_value_score": _decimal_payload(row.composite_value_score),
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(row: StrategyProbabilityEventValueRankerV2Row) -> dict[str, object]:
    payload = _row_public_payload_values(row)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _reason_code_count_public_payload(
    reason_code_count: StrategyProbabilityEventValueRankerV2ReasonCodeCount,
) -> dict[str, object]:
    return {
        "reason_code": reason_code_count.reason_code,
        "count": _decimal_payload(reason_code_count.count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_public_payload_values(
    report: StrategyProbabilityEventValueRankerV2Report,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "report_status": report.report_status,
        "recommendation_count": _decimal_payload(report.recommendation_count),
        "recommend_count": _decimal_payload(report.recommend_count),
        "watch_count": _decimal_payload(report.watch_count),
        "reject_count": _decimal_payload(report.reject_count),
        "min_recommendation_score": _decimal_payload(report.min_recommendation_score),
        "min_edge": _decimal_payload(report.min_edge),
        "min_information_quality_score": _decimal_payload(
            report.min_information_quality_score,
        ),
        "min_liquidity_score": _decimal_payload(report.min_liquidity_score),
        "max_resolution_risk_score": _decimal_payload(report.max_resolution_risk_score),
        "max_category_exposure_score": _decimal_payload(
            report.max_category_exposure_score,
        ),
        "rows": [_row_public_payload(row) for row in report.rows],
        "reason_code_counts": [
            _reason_code_count_public_payload(reason_code_count)
            for reason_code_count in report.reason_code_counts
        ],
        "source_categories": list(report.source_categories),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _config_public_payload(
    config: StrategyProbabilityEventValueRankerV2Config,
) -> dict[str, object]:
    return {
        "config_version": config.config_version,
        "min_recommendation_score": _decimal_payload(config.min_recommendation_score),
        "min_edge": _decimal_payload(config.min_edge),
        "min_information_quality_score": _decimal_payload(
            config.min_information_quality_score,
        ),
        "min_liquidity_score": _decimal_payload(config.min_liquidity_score),
        "max_resolution_risk_score": _decimal_payload(config.max_resolution_risk_score),
        "max_category_exposure_score": _decimal_payload(
            config.max_category_exposure_score,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _candidate_public_probe(
    candidate: StrategyProbabilityEventValueRankerV2Candidate,
) -> dict[str, object]:
    return {
        "candidate_id": candidate.candidate_id,
        "event_id": candidate.event_id,
        "market_slug": candidate.market_slug,
        "outcome_name": candidate.outcome_name,
        "category": candidate.category,
        "reason_codes": list(candidate.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_derived_validation_digest(row: StrategyProbabilityEventValueRankerV2Row) -> str:
    return _digest_public_payload(
        "strategy_probability_event_value_ranker_v2_row",
        _row_public_payload_values(row),
    )


def _report_derived_validation_digest(
    report: StrategyProbabilityEventValueRankerV2Report,
) -> str:
    return _digest_public_payload(
        "strategy_probability_event_value_ranker_v2_report",
        _report_public_payload_values(report),
    )


def _validate_row_derived_validation_digest(
    row: StrategyProbabilityEventValueRankerV2Row,
) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_derived_validation_digest(
    report: StrategyProbabilityEventValueRankerV2Report,
) -> None:
    _validate_report_derived_fields(report)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _digest_public_payload(label: str, payload: dict[str, object]) -> str:
    return hashlib.sha256(
        (
            label
            + "|"
            + json.dumps(payload, sort_keys=True, separators=(",", ":"))
        ).encode("utf-8"),
    ).hexdigest()


def _payload_without_digest(
    payload: dict[str, object],
    fields_without_digest: tuple[str, ...],
) -> dict[str, object]:
    return {field_name: payload[field_name] for field_name in fields_without_digest}


def _require_public_rows(value: object) -> tuple[dict[str, object], ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    rows: list[dict[str, object]] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_payload_fields("row", item, ROW_PAYLOAD_FIELDS)
        for field_name in (
            "candidate_id",
            "event_id",
            "market_slug",
            "outcome_name",
            "category",
        ):
            _require_canonical_string(field_name, item[field_name])
        _require_member(
            "recommendation_posture",
            item["recommendation_posture"],
            RECOMMENDATION_POSTURES,
        )
        _require_decimal_payload_string("rank", item["rank"], whole=True)
        for field_name in (
            "implied_probability",
            "model_probability",
            "information_quality_score",
            "liquidity_score",
            "specialist_consensus_score",
            "resolution_risk_score",
            "category_exposure_score",
        ):
            _require_decimal_payload_string(field_name, item[field_name], ratio=True)
        for field_name in ("probability_edge", "composite_value_score"):
            _require_decimal_payload_string(field_name, item[field_name])
        _require_public_string_list("reason_codes", item["reason_codes"])
        _normalize_sha256(DERIVED_VALIDATION_DIGEST_FIELD, item[DERIVED_VALIDATION_DIGEST_FIELD])
        _require_hard_flags("row", _PayloadFlags(item))
        rows.append(dict(item))
    return tuple(rows)


def _validate_public_row_digests(rows: tuple[dict[str, object], ...]) -> None:
    for row in rows:
        expected_digest = _digest_public_payload(
            "strategy_probability_event_value_ranker_v2_row",
            _payload_without_digest(row, ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST),
        )
        if row[DERIVED_VALIDATION_DIGEST_FIELD] != expected_digest:
            raise ValueError("derived_validation_digest must match row fields")


def _require_public_reason_code_counts(
    value: object,
) -> tuple[tuple[str, str], ...]:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    items: list[tuple[str, str]] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        _require_payload_fields(
            "reason_code_count",
            item,
            ("reason_code", "count", "paper_only", "report_only", "readonly"),
        )
        _require_canonical_string("reason_code", item["reason_code"])
        _require_decimal_payload_string("count", item["count"], whole=True)
        if Decimal(str(item["count"])) <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", _PayloadFlags(item))
        items.append((str(item["reason_code"]), str(item["count"])))
    return tuple(items)


def _public_reason_code_counts(
    rows: tuple[dict[str, object], ...],
) -> tuple[tuple[str, str], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row["reason_codes"]:
            counts[str(reason_code)] = counts.get(str(reason_code), 0) + 1
    return tuple(
        (reason_code, _decimal_payload(_count_decimal(count)))
        for reason_code, count in sorted(counts.items())
    )


def _public_posture_counts(rows: tuple[dict[str, object], ...]) -> dict[str, Decimal]:
    return {
        posture: _count_decimal(
            sum(1 for row in rows if row["recommendation_posture"] == posture),
        )
        for posture in RECOMMENDATION_POSTURES
    }


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _normalize_candidates(
    candidates: tuple[StrategyProbabilityEventValueRankerV2Candidate, ...]
    | list[StrategyProbabilityEventValueRankerV2Candidate],
) -> tuple[StrategyProbabilityEventValueRankerV2Candidate, ...]:
    if type(candidates) not in (tuple, list):
        raise ValueError("candidates must be a tuple or list")
    normalized = tuple(candidates)
    seen: set[str] = set()
    for candidate in normalized:
        _require_exact_type(
            candidate,
            StrategyProbabilityEventValueRankerV2Candidate,
            "candidate",
        )
        if candidate.candidate_id in seen:
            raise ValueError("candidate_id must be unique")
        seen.add(candidate.candidate_id)
    return normalized


def _normalize_rows(value: object) -> tuple[StrategyProbabilityEventValueRankerV2Row, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    rows = tuple(value)
    for row in rows:
        _require_exact_type(row, StrategyProbabilityEventValueRankerV2Row, "row")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[StrategyProbabilityEventValueRankerV2ReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    items = tuple(value)
    for item in items:
        _require_exact_type(
            item,
            StrategyProbabilityEventValueRankerV2ReasonCodeCount,
            "reason_code_count",
        )
    if tuple(sorted(items, key=lambda item: item.reason_code)) != items:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return items


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    items = tuple(value)
    for item in items:
        _require_canonical_string(field_name, item)
    if tuple(sorted(dict.fromkeys(items))) != items:
        raise ValueError(f"{field_name} must be sorted unique canonical strings")
    return items


def _require_public_string_list(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    items = tuple(value)
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must contain unique values")
    return items


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    items = tuple(value)
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must contain unique values")
    return items


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_signed_decimal(field_name: str, value: object) -> Decimal:
    return _normalize_decimal(field_name, value)


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO or normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a positive whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    ratio: bool = False,
    whole: bool = False,
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if _decimal_payload(decimal_value) != value:
        raise ValueError(f"{field_name} must be a six-place Decimal string")
    if ratio and (decimal_value < ZERO or decimal_value > ONE):
        raise ValueError(f"{field_name} must be between 0 and 1")
    if whole and (decimal_value < ZERO or decimal_value != decimal_value.to_integral_value()):
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal string")


def _decimal_payload(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must contain a known value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if value.strip() != value or len(value) != 64 or value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{flag_name} must be True for {label}")


def _require_payload_fields(
    label: str,
    payload: dict[str, object],
    expected_fields: tuple[str, ...],
) -> None:
    expected = set(expected_fields)
    actual = set(payload)
    missing = sorted(expected - actual)
    if missing:
        raise ValueError(f"{missing[0]} is required for {label}")
    extra = sorted(actual - expected)
    if extra:
        raise ValueError(f"unsafe public field in {label}: {extra[0]}")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if type(value) is str:
        if _has_unsafe_public_token(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            child_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_token(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and child is not True:
                raise ValueError(f"{child_path} must be True for {label}")
            _reject_unsafe_public_payload(label, child, child_path)
        return
    if type(value) in (list, tuple):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, child, child_path)
        return
    if type(value) in (Decimal, int):
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    raise ValueError(f"{path or label} contains unsupported value")


def _has_unsafe_public_token(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = tuple(part for part in normalized.split("_") if part)
    return any(token in UNSAFE_PUBLIC_TEXT_TOKENS for token in tokens)


__all__ = (
    "DEFAULT_STRATEGY_PROBABILITY_EVENT_VALUE_RANKER_V2_CONFIG_VERSION",
    "RECOMMENDATION_POSTURES",
    "StrategyProbabilityEventValueRankerV2Candidate",
    "StrategyProbabilityEventValueRankerV2Config",
    "StrategyProbabilityEventValueRankerV2ReasonCodeCount",
    "StrategyProbabilityEventValueRankerV2Report",
    "StrategyProbabilityEventValueRankerV2Row",
    "build_strategy_probability_event_value_ranker_v2_report",
    "strategy_probability_event_value_ranker_v2_payload",
    "validate_strategy_probability_event_value_ranker_v2_public_payload",
)
