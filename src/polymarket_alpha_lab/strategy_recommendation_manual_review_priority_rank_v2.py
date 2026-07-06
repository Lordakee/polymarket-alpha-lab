"""Phase 1 paper-only priority ranks for manual recommendation review."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext


__all__ = (
    "StrategyRecommendationManualReviewPriorityRankConfig",
    "StrategyRecommendationManualReviewPriorityRankInput",
    "StrategyRecommendationManualReviewPriorityRankReport",
    "StrategyRecommendationManualReviewPriorityRankRow",
    "build_strategy_recommendation_manual_review_priority_rank_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
NEGATIVE_ONE = Decimal("-1")
QUANTUM = Decimal("0.000001")
BOUNDARY_STATEMENT = (
    "Phase 1 paper-only manual-review priority rank for human review before "
    "paper execution; it is not an execution instruction."
)
SELECTED_SIDES = ("yes", "no")
REASON_CODES = (
    "positive_expected_value_after_cost",
    "nonpositive_expected_value_after_cost",
    "evidence_gap",
    "resolution_ambiguity",
    "market_urgency",
    "liquidity_capacity_available",
    "liquidity_capacity_limited",
    "team_confidence_disagreement",
)


@dataclass(frozen=True)
class StrategyRecommendationManualReviewPriorityRankConfig:
    config_version: str = "manual-review-priority-rank-v2"
    expected_value_after_cost_weight: Decimal = Decimal("100.000000")
    evidence_gap_weight: Decimal = Decimal("10.000000")
    resolution_ambiguity_weight: Decimal = Decimal("10.000000")
    market_urgency_weight: Decimal = Decimal("10.000000")
    liquidity_capacity_weight: Decimal = Decimal("10.000000")
    team_confidence_disagreement_weight: Decimal = Decimal("10.000000")
    evidence_gap_reason_threshold: Decimal = Decimal("0.250000")
    resolution_ambiguity_reason_threshold: Decimal = Decimal("0.250000")
    market_urgency_reason_threshold: Decimal = Decimal("0.250000")
    liquidity_capacity_reason_floor: Decimal = Decimal("0.500000")
    team_confidence_disagreement_reason_threshold: Decimal = Decimal("0.250000")
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "expected_value_after_cost_weight",
            "evidence_gap_weight",
            "resolution_ambiguity_weight",
            "market_urgency_weight",
            "liquidity_capacity_weight",
            "team_confidence_disagreement_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_gap_reason_threshold",
            "resolution_ambiguity_reason_threshold",
            "market_urgency_reason_threshold",
            "liquidity_capacity_reason_floor",
            "team_confidence_disagreement_reason_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_boundary_statement(self.boundary_statement)
        _require_phase_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationManualReviewPriorityRankInput:
    recommendation_id: str
    market_slug: str
    selected_side: str
    expected_value_after_cost: Decimal
    evidence_gap_score: Decimal
    resolution_ambiguity_score: Decimal
    market_urgency_score: Decimal
    liquidity_capacity_score: Decimal
    team_confidence_disagreement_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("recommendation_id", self.recommendation_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_selected_side(self.selected_side)
        object.__setattr__(
            self,
            "expected_value_after_cost",
            _normalize_edge("expected_value_after_cost", self.expected_value_after_cost),
        )
        for field_name in (
            "evidence_gap_score",
            "resolution_ambiguity_score",
            "market_urgency_score",
            "liquidity_capacity_score",
            "team_confidence_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_phase_flags("recommendation", self)


@dataclass(frozen=True)
class StrategyRecommendationManualReviewPriorityRankRow:
    priority_rank: int
    recommendation_id: str
    market_slug: str
    selected_side: str
    priority_score: Decimal
    expected_value_after_cost: Decimal
    evidence_gap_score: Decimal
    resolution_ambiguity_score: Decimal
    market_urgency_score: Decimal
    liquidity_capacity_score: Decimal
    team_confidence_disagreement_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_positive_int("priority_rank", self.priority_rank)
        _require_canonical_string("recommendation_id", self.recommendation_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_selected_side(self.selected_side)
        object.__setattr__(
            self,
            "priority_score",
            _normalize_nonnegative_decimal("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "expected_value_after_cost",
            _normalize_edge("expected_value_after_cost", self.expected_value_after_cost),
        )
        for field_name in (
            "evidence_gap_score",
            "resolution_ambiguity_score",
            "market_urgency_score",
            "liquidity_capacity_score",
            "team_confidence_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_phase_flags("priority_rank", self)


@dataclass(frozen=True)
class StrategyRecommendationManualReviewPriorityRankReport:
    generated_at: datetime
    config_version: str
    recommendation_count: int
    top_priority_score: Decimal
    average_priority_score: Decimal
    priority_ranks: tuple[StrategyRecommendationManualReviewPriorityRankRow, ...]
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("recommendation_count", self.recommendation_count)
        object.__setattr__(
            self,
            "top_priority_score",
            _normalize_nonnegative_decimal("top_priority_score", self.top_priority_score),
        )
        object.__setattr__(
            self,
            "average_priority_score",
            _normalize_nonnegative_decimal(
                "average_priority_score",
                self.average_priority_score,
            ),
        )
        object.__setattr__(
            self,
            "priority_ranks",
            _normalize_priority_ranks(self.priority_ranks),
        )
        _require_boundary_statement(self.boundary_statement)
        _validate_report(self)
        _require_phase_flags("report", self)


def build_strategy_recommendation_manual_review_priority_rank_report(
    recommendations: Iterable[StrategyRecommendationManualReviewPriorityRankInput],
    *,
    generated_at: datetime,
    config: StrategyRecommendationManualReviewPriorityRankConfig | None = None,
) -> StrategyRecommendationManualReviewPriorityRankReport:
    """Rank manual-review recommendations without side effects or execution output."""

    rank_config = StrategyRecommendationManualReviewPriorityRankConfig() if config is None else config
    if type(rank_config) is not StrategyRecommendationManualReviewPriorityRankConfig:
        raise ValueError("config must be a StrategyRecommendationManualReviewPriorityRankConfig")
    _require_phase_flags("config", rank_config)
    normalized = _normalize_recommendations(recommendations)
    rows = tuple(
        StrategyRecommendationManualReviewPriorityRankRow(
            priority_rank=index,
            recommendation_id=value.recommendation_id,
            market_slug=value.market_slug,
            selected_side=value.selected_side,
            priority_score=value.priority_score,
            expected_value_after_cost=value.expected_value_after_cost,
            evidence_gap_score=value.evidence_gap_score,
            resolution_ambiguity_score=value.resolution_ambiguity_score,
            market_urgency_score=value.market_urgency_score,
            liquidity_capacity_score=value.liquidity_capacity_score,
            team_confidence_disagreement_score=value.team_confidence_disagreement_score,
            reason_codes=value.reason_codes,
        )
        for index, value in enumerate(
            sorted(
                (_rank_values(recommendation, rank_config) for recommendation in normalized),
                key=_rank_value_sort_key,
            ),
            start=1,
        )
    )
    return StrategyRecommendationManualReviewPriorityRankReport(
        generated_at=generated_at,
        config_version=rank_config.config_version,
        recommendation_count=len(rows),
        top_priority_score=_top_priority_score(rows),
        average_priority_score=_average_priority_score(rows),
        priority_ranks=rows,
    )


@dataclass(frozen=True)
class _RankValues:
    recommendation_id: str
    market_slug: str
    selected_side: str
    priority_score: Decimal
    expected_value_after_cost: Decimal
    evidence_gap_score: Decimal
    resolution_ambiguity_score: Decimal
    market_urgency_score: Decimal
    liquidity_capacity_score: Decimal
    team_confidence_disagreement_score: Decimal
    reason_codes: tuple[str, ...]


def _rank_values(
    recommendation: StrategyRecommendationManualReviewPriorityRankInput,
    config: StrategyRecommendationManualReviewPriorityRankConfig,
) -> _RankValues:
    return _RankValues(
        recommendation_id=recommendation.recommendation_id,
        market_slug=recommendation.market_slug,
        selected_side=recommendation.selected_side,
        priority_score=_priority_score(recommendation, config),
        expected_value_after_cost=recommendation.expected_value_after_cost,
        evidence_gap_score=recommendation.evidence_gap_score,
        resolution_ambiguity_score=recommendation.resolution_ambiguity_score,
        market_urgency_score=recommendation.market_urgency_score,
        liquidity_capacity_score=recommendation.liquidity_capacity_score,
        team_confidence_disagreement_score=(
            recommendation.team_confidence_disagreement_score
        ),
        reason_codes=_reason_codes(recommendation, config),
    )


def _priority_score(
    recommendation: StrategyRecommendationManualReviewPriorityRankInput,
    config: StrategyRecommendationManualReviewPriorityRankConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = (
            max(recommendation.expected_value_after_cost, ZERO)
            * config.expected_value_after_cost_weight
            + recommendation.evidence_gap_score * config.evidence_gap_weight
            + recommendation.resolution_ambiguity_score
            * config.resolution_ambiguity_weight
            + recommendation.market_urgency_score * config.market_urgency_weight
            + recommendation.liquidity_capacity_score * config.liquidity_capacity_weight
            + recommendation.team_confidence_disagreement_score
            * config.team_confidence_disagreement_weight
        )
    return _normalize_nonnegative_decimal("priority_score", score)


def _reason_codes(
    recommendation: StrategyRecommendationManualReviewPriorityRankInput,
    config: StrategyRecommendationManualReviewPriorityRankConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if recommendation.expected_value_after_cost > ZERO:
        reason_codes.append("positive_expected_value_after_cost")
    else:
        reason_codes.append("nonpositive_expected_value_after_cost")
    if recommendation.evidence_gap_score >= config.evidence_gap_reason_threshold:
        reason_codes.append("evidence_gap")
    if (
        recommendation.resolution_ambiguity_score
        >= config.resolution_ambiguity_reason_threshold
    ):
        reason_codes.append("resolution_ambiguity")
    if recommendation.market_urgency_score >= config.market_urgency_reason_threshold:
        reason_codes.append("market_urgency")
    if recommendation.liquidity_capacity_score >= config.liquidity_capacity_reason_floor:
        reason_codes.append("liquidity_capacity_available")
    else:
        reason_codes.append("liquidity_capacity_limited")
    if (
        recommendation.team_confidence_disagreement_score
        >= config.team_confidence_disagreement_reason_threshold
    ):
        reason_codes.append("team_confidence_disagreement")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _rank_value_sort_key(
    value: _RankValues,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, str, str]:
    return (
        -value.priority_score,
        -value.expected_value_after_cost,
        -value.evidence_gap_score,
        -value.resolution_ambiguity_score,
        -value.market_urgency_score,
        -value.liquidity_capacity_score,
        -value.team_confidence_disagreement_score,
        value.recommendation_id,
        value.market_slug,
        value.selected_side,
    )


def _normalize_recommendations(
    value: Iterable[StrategyRecommendationManualReviewPriorityRankInput],
) -> tuple[StrategyRecommendationManualReviewPriorityRankInput, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("recommendations must be an iterable")
    recommendations = tuple(value)
    keys: set[tuple[str, str, str]] = set()
    for recommendation in recommendations:
        if type(recommendation) is not StrategyRecommendationManualReviewPriorityRankInput:
            raise ValueError(
                "recommendations must contain StrategyRecommendationManualReviewPriorityRankInput",
            )
        _require_phase_flags("recommendation", recommendation)
        key = (
            recommendation.recommendation_id,
            recommendation.market_slug,
            recommendation.selected_side,
        )
        if key in keys:
            raise ValueError("recommendations must not contain duplicate recommendations")
        keys.add(key)
    return recommendations


def _normalize_priority_ranks(
    value: object,
) -> tuple[StrategyRecommendationManualReviewPriorityRankRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("priority_ranks must be a list or tuple")
    rows = tuple(value)
    seen_ranks: set[int] = set()
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationManualReviewPriorityRankRow:
            raise ValueError(
                "priority_ranks must contain StrategyRecommendationManualReviewPriorityRankRow",
            )
        if row.priority_rank in seen_ranks:
            raise ValueError("priority_ranks must not contain duplicate ranks")
        seen_ranks.add(row.priority_rank)
        key = (row.recommendation_id, row.market_slug, row.selected_side)
        if key in seen_keys:
            raise ValueError("priority_ranks must not contain duplicate recommendations")
        seen_keys.add(key)
        _require_phase_flags("priority_rank", row)
    if tuple(row.priority_rank for row in rows) != tuple(range(1, len(rows) + 1)):
        raise ValueError("priority_ranks must be consecutively ranked")
    if tuple(sorted(rows, key=_priority_row_sort_key)) != rows:
        raise ValueError("priority_ranks must be deterministically sorted")
    return rows


def _priority_row_sort_key(
    row: StrategyRecommendationManualReviewPriorityRankRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, str, str, int]:
    return (
        -row.priority_score,
        -row.expected_value_after_cost,
        -row.evidence_gap_score,
        -row.resolution_ambiguity_score,
        -row.market_urgency_score,
        -row.liquidity_capacity_score,
        -row.team_confidence_disagreement_score,
        row.recommendation_id,
        row.market_slug,
        row.selected_side,
        row.priority_rank,
    )


def _top_priority_score(
    rows: tuple[StrategyRecommendationManualReviewPriorityRankRow, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANTUM)
    return rows[0].priority_score


def _average_priority_score(
    rows: tuple[StrategyRecommendationManualReviewPriorityRankRow, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANTUM)
    with localcontext() as context:
        context.prec = 28
        average = sum((row.priority_score for row in rows), ZERO) / Decimal(len(rows))
    return _normalize_nonnegative_decimal("average_priority_score", average)


def _validate_report(report: StrategyRecommendationManualReviewPriorityRankReport) -> None:
    if report.recommendation_count != len(report.priority_ranks):
        raise ValueError("recommendation_count must match priority_ranks")
    expected_top = _top_priority_score(report.priority_ranks)
    if report.top_priority_score != expected_top:
        raise ValueError("top_priority_score must match priority_ranks")
    expected_average = _average_priority_score(report.priority_ranks)
    if report.average_priority_score != expected_average:
        raise ValueError("average_priority_score must match priority_ranks")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_edge(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < NEGATIVE_ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext() as context:
        context.prec = 28
        quantized = value.quantize(QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_selected_side(value: object) -> None:
    if type(value) is not str or value not in SELECTED_SIDES:
        raise ValueError(f"selected_side must be one of {SELECTED_SIDES}")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive int")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_boundary_statement(value: object) -> None:
    if value != BOUNDARY_STATEMENT:
        raise ValueError("boundary_statement must match the Phase 1 safety boundary")


def _require_phase_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name}.{flag_name} must be True")
