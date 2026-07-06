"""Pure Phase 1 review backlog prioritizer for strategy recommendations."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_REVIEW_BACKLOG_PRIORITIZER_V2_CONFIG_VERSION",
    "StrategyRecommendationReviewBacklogPrioritizerV2Config",
    "StrategyRecommendationReviewBacklogPrioritizerV2Input",
    "StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount",
    "StrategyRecommendationReviewBacklogPrioritizerV2Report",
    "StrategyRecommendationReviewBacklogPrioritizerV2Row",
    "build_strategy_recommendation_review_backlog_prioritizer_v2_report",
    "strategy_recommendation_review_backlog_prioritizer_v2_payload",
)


DEFAULT_STRATEGY_RECOMMENDATION_REVIEW_BACKLOG_PRIORITIZER_V2_CONFIG_VERSION = (
    "strategy-recommendation-review-backlog-prioritizer-v2"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REVIEW_STATUSES = ("review_now", "watch", "blocked")
ROW_STATUS_WEIGHT = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "review_now": Decimal("2.000000"),
}
_UNSAFE_TEXT_FRAGMENTS = frozenset(
    "".join(parts)
    for parts in (
        ("li", "ve"),
        ("au", "th"),
        ("wa", "llet"),
        ("or", "der"),
        ("net", "work"),
        ("data", "base"),
        ("per", "sist"),
        ("sig", "ning"),
        ("muta", "tion"),
        ("b", "uy"),
        ("se", "ll"),
        ("tra", "de"),
    )
)


@dataclass(frozen=True)
class StrategyRecommendationReviewBacklogPrioritizerV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_REVIEW_BACKLOG_PRIORITIZER_V2_CONFIG_VERSION
    )
    minimum_source_verified_edge: Decimal = Decimal("0.030000")
    stale_research_ready_age_seconds: Decimal = Decimal("7200.000000")
    market_probability_movement_watch: Decimal = Decimal("0.040000")
    uncertainty_band_width_watch: Decimal = Decimal("0.120000")
    liquidity_exit_risk_watch: Decimal = Decimal("0.500000")
    liquidity_exit_risk_block: Decimal = Decimal("0.850000")
    portfolio_impact_watch: Decimal = Decimal("0.100000")
    portfolio_impact_block: Decimal = Decimal("0.250000")
    resolution_ambiguity_watch: Decimal = Decimal("0.400000")
    resolution_ambiguity_block: Decimal = Decimal("0.800000")
    minimum_specialist_confidence: Decimal = Decimal("0.600000")
    source_verified_edge_weight: Decimal = Decimal("3.000000")
    stale_research_readiness_weight: Decimal = Decimal("1.500000")
    market_probability_movement_weight: Decimal = Decimal("2.000000")
    uncertainty_band_width_weight: Decimal = Decimal("1.250000")
    liquidity_exit_risk_weight: Decimal = Decimal("2.250000")
    portfolio_impact_weight: Decimal = Decimal("1.750000")
    resolution_ambiguity_weight: Decimal = Decimal("2.500000")
    specialist_confidence_weight: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "minimum_source_verified_edge",
            _normalize_nonnegative_decimal(
                "minimum_source_verified_edge",
                self.minimum_source_verified_edge,
            ),
        )
        object.__setattr__(
            self,
            "stale_research_ready_age_seconds",
            _normalize_nonnegative_decimal(
                "stale_research_ready_age_seconds",
                self.stale_research_ready_age_seconds,
            ),
        )
        for field_name in (
            "market_probability_movement_watch",
            "uncertainty_band_width_watch",
            "liquidity_exit_risk_watch",
            "liquidity_exit_risk_block",
            "portfolio_impact_watch",
            "portfolio_impact_block",
            "resolution_ambiguity_watch",
            "resolution_ambiguity_block",
            "minimum_specialist_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_verified_edge_weight",
            "stale_research_readiness_weight",
            "market_probability_movement_weight",
            "uncertainty_band_width_weight",
            "liquidity_exit_risk_weight",
            "portfolio_impact_weight",
            "resolution_ambiguity_weight",
            "specialist_confidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most(
            "liquidity_exit_risk_watch",
            self.liquidity_exit_risk_watch,
            self.liquidity_exit_risk_block,
        )
        _require_at_most(
            "portfolio_impact_watch",
            self.portfolio_impact_watch,
            self.portfolio_impact_block,
        )
        _require_at_most(
            "resolution_ambiguity_watch",
            self.resolution_ambiguity_watch,
            self.resolution_ambiguity_block,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class StrategyRecommendationReviewBacklogPrioritizerV2Input:
    recommendation_id: str
    source_verified_edge: Decimal
    research_observed_at: datetime
    market_probability_movement: Decimal
    uncertainty_low_probability: Decimal
    uncertainty_high_probability: Decimal
    liquidity_exit_risk: Decimal
    portfolio_impact: Decimal
    resolution_ambiguity: Decimal
    specialist_confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("recommendation_id", self.recommendation_id)
        object.__setattr__(
            self,
            "source_verified_edge",
            _normalize_signed_probability_delta(
                "source_verified_edge",
                self.source_verified_edge,
            ),
        )
        object.__setattr__(
            self,
            "research_observed_at",
            _as_utc("research_observed_at", self.research_observed_at),
        )
        for field_name in (
            "market_probability_movement",
            "uncertainty_low_probability",
            "uncertainty_high_probability",
            "liquidity_exit_risk",
            "portfolio_impact",
            "resolution_ambiguity",
            "specialist_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.uncertainty_low_probability > self.uncertainty_high_probability:
            raise ValueError(
                "uncertainty_low_probability must not exceed "
                "uncertainty_high_probability",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class StrategyRecommendationReviewBacklogPrioritizerV2Row:
    recommendation_id: str
    priority_rank: Decimal
    review_status: str
    priority_score: Decimal
    source_verified_edge: Decimal
    research_observed_at: datetime
    research_age_seconds: Decimal
    stale_research_readiness: Decimal
    market_probability_movement: Decimal
    uncertainty_low_probability: Decimal
    uncertainty_high_probability: Decimal
    uncertainty_band_width: Decimal
    liquidity_exit_risk: Decimal
    portfolio_impact: Decimal
    resolution_ambiguity: Decimal
    specialist_confidence: Decimal
    specialist_confidence_deficit: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("recommendation_id", self.recommendation_id)
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_count("priority_rank", self.priority_rank),
        )
        _require_review_status("review_status", self.review_status)
        object.__setattr__(
            self,
            "priority_score",
            _normalize_nonnegative_decimal("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "source_verified_edge",
            _normalize_signed_probability_delta(
                "source_verified_edge",
                self.source_verified_edge,
            ),
        )
        object.__setattr__(
            self,
            "research_observed_at",
            _as_utc("research_observed_at", self.research_observed_at),
        )
        object.__setattr__(
            self,
            "research_age_seconds",
            _normalize_nonnegative_decimal(
                "research_age_seconds",
                self.research_age_seconds,
            ),
        )
        for field_name in (
            "stale_research_readiness",
            "market_probability_movement",
            "uncertainty_low_probability",
            "uncertainty_high_probability",
            "uncertainty_band_width",
            "liquidity_exit_risk",
            "portfolio_impact",
            "resolution_ambiguity",
            "specialist_confidence",
            "specialist_confidence_deficit",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.uncertainty_low_probability > self.uncertainty_high_probability:
            raise ValueError(
                "uncertainty_low_probability must not exceed "
                "uncertainty_high_probability",
            )
        if self.uncertainty_band_width != _quantize(
            self.uncertainty_high_probability - self.uncertainty_low_probability,
        ):
            raise ValueError("uncertainty_band_width must match uncertainty inputs")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.review_status != _row_status(self.reason_codes):
            raise ValueError("review_status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class StrategyRecommendationReviewBacklogPrioritizerV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    review_now_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_priority_score: Decimal
    min_priority_score: Decimal
    average_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount,
        ...,
    ]
    priority_rows: tuple[StrategyRecommendationReviewBacklogPrioritizerV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "review_now_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_priority_score",
            "min_priority_score",
            "average_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_review_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "priority_rows",
            _normalize_rows(self.priority_rows),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)
        derived_validation_digest = _report_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != derived_validation_digest:
                raise ValueError("derived_validation_digest does not match report")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                derived_validation_digest,
            )


def build_strategy_recommendation_review_backlog_prioritizer_v2_report(
    recommendations: Iterable[StrategyRecommendationReviewBacklogPrioritizerV2Input],
    *,
    config: StrategyRecommendationReviewBacklogPrioritizerV2Config,
    generated_at: datetime,
) -> StrategyRecommendationReviewBacklogPrioritizerV2Report:
    if type(config) is not StrategyRecommendationReviewBacklogPrioritizerV2Config:
        raise ValueError(
            "config must be a "
            "StrategyRecommendationReviewBacklogPrioritizerV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(recommendations)
    metric_rows = tuple(
        _candidate_metrics(row, config=config, generated_at=generated_at_utc)
        for row in input_rows
    )
    rows = tuple(
        StrategyRecommendationReviewBacklogPrioritizerV2Row(
            priority_rank=_count(index),
            **metric,
        )
        for index, metric in enumerate(
            sorted(metric_rows, key=_metric_sort_key),
            start=1,
        )
    )
    priority_scores = tuple(row.priority_score for row in rows)
    return StrategyRecommendationReviewBacklogPrioritizerV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        review_now_count=_status_count(rows, "review_now"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        max_priority_score=_max_decimal(priority_scores),
        min_priority_score=_min_decimal(priority_scores),
        average_priority_score=_average_decimal(priority_scores),
        status=_rollup_status(tuple(row.review_status for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        priority_rows=rows,
    )


def strategy_recommendation_review_backlog_prioritizer_v2_payload(
    report: StrategyRecommendationReviewBacklogPrioritizerV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyRecommendationReviewBacklogPrioritizerV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyRecommendationReviewBacklogPrioritizerV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _candidate_metrics(
    recommendation: StrategyRecommendationReviewBacklogPrioritizerV2Input,
    *,
    config: StrategyRecommendationReviewBacklogPrioritizerV2Config,
    generated_at: datetime,
) -> dict[str, Any]:
    if recommendation.research_observed_at > generated_at:
        raise ValueError("research_observed_at must not be after generated_at")
    research_age_seconds = _duration_seconds(
        recommendation.research_observed_at,
        generated_at,
    )
    uncertainty_band_width = _quantize(
        recommendation.uncertainty_high_probability
        - recommendation.uncertainty_low_probability,
    )
    stale_research_readiness = (
        ONE
        if research_age_seconds > config.stale_research_ready_age_seconds
        else ZERO
    )
    specialist_confidence_deficit = _quantize(
        max(ZERO, config.minimum_specialist_confidence - recommendation.specialist_confidence),
    )
    reason_codes = _row_reason_codes(
        recommendation,
        config=config,
        research_age_seconds=research_age_seconds,
        stale_research_readiness=stale_research_readiness,
        uncertainty_band_width=uncertainty_band_width,
        specialist_confidence_deficit=specialist_confidence_deficit,
    )
    review_status = _row_status(reason_codes)
    priority_score = _priority_score(
        recommendation,
        config=config,
        stale_research_readiness=stale_research_readiness,
        uncertainty_band_width=uncertainty_band_width,
        specialist_confidence_deficit=specialist_confidence_deficit,
    )
    return {
        "recommendation_id": recommendation.recommendation_id,
        "review_status": review_status,
        "priority_score": priority_score,
        "source_verified_edge": recommendation.source_verified_edge,
        "research_observed_at": recommendation.research_observed_at,
        "research_age_seconds": research_age_seconds,
        "stale_research_readiness": stale_research_readiness,
        "market_probability_movement": recommendation.market_probability_movement,
        "uncertainty_low_probability": recommendation.uncertainty_low_probability,
        "uncertainty_high_probability": recommendation.uncertainty_high_probability,
        "uncertainty_band_width": uncertainty_band_width,
        "liquidity_exit_risk": recommendation.liquidity_exit_risk,
        "portfolio_impact": recommendation.portfolio_impact,
        "resolution_ambiguity": recommendation.resolution_ambiguity,
        "specialist_confidence": recommendation.specialist_confidence,
        "specialist_confidence_deficit": specialist_confidence_deficit,
        "reason_codes": reason_codes,
    }


def _row_reason_codes(
    recommendation: StrategyRecommendationReviewBacklogPrioritizerV2Input,
    *,
    config: StrategyRecommendationReviewBacklogPrioritizerV2Config,
    research_age_seconds: Decimal,
    stale_research_readiness: Decimal,
    uncertainty_band_width: Decimal,
    specialist_confidence_deficit: Decimal,
) -> tuple[str, ...]:
    reason_codes = list(recommendation.reason_codes)
    if recommendation.source_verified_edge < ZERO:
        reason_codes.append("source_verified_edge_negative_blocked")
    elif recommendation.source_verified_edge < config.minimum_source_verified_edge:
        reason_codes.append("source_verified_edge_below_minimum_watch")
    if stale_research_readiness == ONE:
        reason_codes.append("stale_research_ready_watch")
    if recommendation.market_probability_movement > config.market_probability_movement_watch:
        reason_codes.append("market_probability_movement_watch")
    if uncertainty_band_width > config.uncertainty_band_width_watch:
        reason_codes.append("uncertainty_band_width_watch")
    if recommendation.liquidity_exit_risk >= config.liquidity_exit_risk_block:
        reason_codes.append("liquidity_exit_risk_blocked")
    elif recommendation.liquidity_exit_risk > config.liquidity_exit_risk_watch:
        reason_codes.append("liquidity_exit_risk_watch")
    if recommendation.portfolio_impact >= config.portfolio_impact_block:
        reason_codes.append("portfolio_impact_blocked")
    elif recommendation.portfolio_impact > config.portfolio_impact_watch:
        reason_codes.append("portfolio_impact_watch")
    if recommendation.resolution_ambiguity >= config.resolution_ambiguity_block:
        reason_codes.append("resolution_ambiguity_blocked")
    elif recommendation.resolution_ambiguity > config.resolution_ambiguity_watch:
        reason_codes.append("resolution_ambiguity_watch")
    if specialist_confidence_deficit > ZERO:
        reason_codes.append("specialist_confidence_low_watch")
    if not any(code.endswith(("_watch", "_blocked")) for code in reason_codes):
        reason_codes.append("review_backlog_ready")
    _ = research_age_seconds
    return tuple(sorted(reason_codes))


def _priority_score(
    recommendation: StrategyRecommendationReviewBacklogPrioritizerV2Input,
    *,
    config: StrategyRecommendationReviewBacklogPrioritizerV2Config,
    stale_research_readiness: Decimal,
    uncertainty_band_width: Decimal,
    specialist_confidence_deficit: Decimal,
) -> Decimal:
    score = (
        _normalized_pressure(
            max(ZERO, recommendation.source_verified_edge),
            config.minimum_source_verified_edge,
        )
        * config.source_verified_edge_weight
    )
    score += stale_research_readiness * config.stale_research_readiness_weight
    score += (
        _normalized_pressure(
            recommendation.market_probability_movement,
            config.market_probability_movement_watch,
        )
        * config.market_probability_movement_weight
    )
    score += (
        _normalized_pressure(uncertainty_band_width, config.uncertainty_band_width_watch)
        * config.uncertainty_band_width_weight
    )
    score += (
        _normalized_pressure(
            recommendation.liquidity_exit_risk,
            config.liquidity_exit_risk_watch,
        )
        * config.liquidity_exit_risk_weight
    )
    score += (
        _normalized_pressure(recommendation.portfolio_impact, config.portfolio_impact_watch)
        * config.portfolio_impact_weight
    )
    score += (
        _normalized_pressure(
            recommendation.resolution_ambiguity,
            config.resolution_ambiguity_watch,
        )
        * config.resolution_ambiguity_weight
    )
    if specialist_confidence_deficit > ZERO:
        score += config.specialist_confidence_weight
    return _quantize(score)


def _metric_sort_key(metric: dict[str, Any]) -> tuple[Decimal, Decimal, str]:
    status = metric["review_status"]
    if type(status) is not str:
        raise ValueError("review_status must be a string")
    score = metric["priority_score"]
    if type(score) is not Decimal:
        raise ValueError("priority_score must be a Decimal")
    recommendation_id = metric["recommendation_id"]
    if type(recommendation_id) is not str:
        raise ValueError("recommendation_id must be a string")
    return (ROW_STATUS_WEIGHT[status], -score, recommendation_id)


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "review_now"


def _rollup_reason_codes(
    rows: tuple[StrategyRecommendationReviewBacklogPrioritizerV2Row, ...],
) -> tuple[str, ...]:
    status = _rollup_status(tuple(row.review_status for row in rows))
    if not rows:
        return ("review_backlog_empty",)
    headline = {
        "blocked": "review_backlog_blocked",
        "watch": "review_backlog_watch",
        "review_now": "review_backlog_ready",
    }[status]
    risk_codes = tuple(
        sorted(
            {
                code
                for row in rows
                for code in row.reason_codes
                if code.endswith(("_watch", "_blocked"))
            },
        ),
    )
    return (headline, *risk_codes)


def _reason_code_counts(
    rows: tuple[StrategyRecommendationReviewBacklogPrioritizerV2Row, ...],
) -> tuple[StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount, ...]:
    counter: Counter[str] = Counter(
        code for row in rows for code in row.reason_codes
    )
    return tuple(
        StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _status_count(
    rows: tuple[StrategyRecommendationReviewBacklogPrioritizerV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.review_status == status))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_blocked") for code in reason_codes):
        return "blocked"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    return "review_now"


def _validate_report_consistency(
    report: StrategyRecommendationReviewBacklogPrioritizerV2Report,
) -> None:
    rows = report.priority_rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match priority_rows")
    if report.review_now_count != _status_count(rows, "review_now"):
        raise ValueError("review_now_count must match priority_rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match priority_rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match priority_rows")
    priority_scores = tuple(row.priority_score for row in rows)
    if report.max_priority_score != _max_decimal(priority_scores):
        raise ValueError("max_priority_score must match priority_rows")
    if report.min_priority_score != _min_decimal(priority_scores):
        raise ValueError("min_priority_score must match priority_rows")
    if report.average_priority_score != _average_decimal(priority_scores):
        raise ValueError("average_priority_score must match priority_rows")
    expected_status = _rollup_status(tuple(row.review_status for row in rows))
    if report.status != expected_status:
        raise ValueError("status must match priority_rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match priority_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match priority_rows")
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    actual_ranks = tuple(row.priority_rank for row in rows)
    if actual_ranks != expected_ranks:
        raise ValueError("priority_rank must be sequential")
    for row in rows:
        if row.research_observed_at > report.generated_at:
            raise ValueError("research_observed_at must not be after generated_at")
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("priority_rows must be sorted by priority")


def _row_sort_key(
    row: StrategyRecommendationReviewBacklogPrioritizerV2Row,
) -> tuple[Decimal, Decimal, str]:
    return (ROW_STATUS_WEIGHT[row.review_status], -row.priority_score, row.recommendation_id)


def _report_validation_digest(
    report: StrategyRecommendationReviewBacklogPrioritizerV2Report,
) -> str:
    return _validation_digest(_json_ready(report, include_digest=False))


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    _require_digest("derived_validation_digest", digest)
    expected = _validation_digest(_payload_without_digest(payload))
    if digest != expected:
        raise ValueError("derived_validation_digest does not match payload")


def _validation_digest(payload: Any) -> str:
    encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_without_digest(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }


def _json_ready(value: Any, *, include_digest: bool = True) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _json_ready(nested_value, include_digest=include_digest)
            for key, nested_value in asdict(value).items()
            if include_digest or key != "derived_validation_digest"
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or value is None:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived string values")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item, include_digest=include_digest) for item in value]
    if isinstance(value, list):
        return [_json_ready(item, include_digest=include_digest) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item, include_digest=include_digest)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _contains_unsafe_text(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _contains_unsafe_text(key):
                raise ValueError(f"unsafe field in {label}")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _contains_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS)


def _normalize_inputs(
    recommendations: Iterable[StrategyRecommendationReviewBacklogPrioritizerV2Input],
) -> tuple[StrategyRecommendationReviewBacklogPrioritizerV2Input, ...]:
    rows = tuple(recommendations)
    for row in rows:
        if type(row) is not StrategyRecommendationReviewBacklogPrioritizerV2Input:
            raise ValueError(
                "recommendations must contain "
                "StrategyRecommendationReviewBacklogPrioritizerV2Input values",
            )
        _require_hard_flags("recommendation", row)
    ids = tuple(row.recommendation_id for row in rows)
    if len(set(ids)) != len(ids):
        raise ValueError("recommendation_id values must be unique")
    return rows


def _normalize_rows(
    rows: object,
) -> tuple[StrategyRecommendationReviewBacklogPrioritizerV2Row, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("priority_rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyRecommendationReviewBacklogPrioritizerV2Row:
            raise ValueError(
                "priority_rows must contain "
                "StrategyRecommendationReviewBacklogPrioritizerV2Row values",
            )
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "StrategyRecommendationReviewBacklogPrioritizerV2ReasonCodeCount values",
            )
    codes = tuple(count.reason_code for count in counts)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_code_counts must be unique")
    return counts


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized = tuple(sorted(reason_codes))
    for code in normalized:
        _require_reason_code("reason_codes", code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _normalize_report_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for code in reason_codes:
        _require_reason_code("reason_codes", code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if reason_codes[0] not in {
        "review_backlog_blocked",
        "review_backlog_empty",
        "review_backlog_ready",
        "review_backlog_watch",
    }:
        raise ValueError("reason_codes must start with a backlog rollup reason")
    tail = reason_codes[1:]
    if tuple(sorted(tail)) != tail:
        raise ValueError("rollup reason_codes tail must be sorted")
    return reason_codes


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if _contains_unsafe_text(value):
        raise ValueError(f"{field_name} has unsafe value")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if any(char not in "abcdefghijklmnopqrstuvwxyz0123456789_" for char in value):
        raise ValueError(f"{field_name} must be lowercase snake_case strings")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if _contains_unsafe_text(value):
        raise ValueError(f"{field_name} has unsafe value")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_-."
    if any(char not in allowed for char in value):
        raise ValueError(f"{field_name} must be lowercase canonical text")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex string")


def _require_review_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REVIEW_STATUSES:
        raise ValueError(f"{field_name} must be a known review status")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_at_most(field_name: str, value: Decimal, maximum: Decimal) -> None:
    if value > maximum:
        raise ValueError(f"{field_name} must not exceed block threshold")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_signed_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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
    return _quantize(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    if delta.days < 0:
        raise ValueError("research_observed_at must not be after generated_at")
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(seconds)


def _normalized_pressure(value: Decimal, threshold: Decimal) -> Decimal:
    if threshold <= ZERO:
        return ZERO
    return _quantize(min(ONE, value / threshold))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)
