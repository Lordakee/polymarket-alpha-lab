"""Paper-only review queue for probability side-edge recommendations."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext

from polymarket_alpha_lab.paper_probability_side_edge import (
    PaperProbabilitySideEdgeRow,
)


__all__ = (
    "PaperProbabilityRecommendationQueueConfig",
    "PaperProbabilityRecommendationQueueRow",
    "PaperProbabilityRecommendationQueueReport",
    "build_paper_probability_recommendation_queue_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64)
ACTIONS = ("recommend", "watch", "reject")
DEPTH_STATUSES = ("sufficient_depth", "partial_depth", "no_depth")
REVIEW_PRIORITIES = ("research_review", "watch", "skip")
RECOMMENDED_NEXT_STEPS = ("research_review", "await_fresh_context", "skip")
NEXT_STEP_RANK = {
    "research_review": 0,
    "await_fresh_context": 1,
    "skip": 2,
}
SIDES = ("yes", "no")


@dataclass(frozen=True)
class PaperProbabilityRecommendationQueueConfig:
    config_version: str
    max_queue_rows: int
    min_recommendation_score: Decimal
    include_watch: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("max_queue_rows", self.max_queue_rows)
        object.__setattr__(
            self,
            "min_recommendation_score",
            _normalize_probability(
                "min_recommendation_score",
                self.min_recommendation_score,
            ),
        )
        _require_bool("include_watch", self.include_watch)
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class PaperProbabilityRecommendationQueueRow:
    queue_rank: int
    market_slug: str
    question: str
    side: str
    action: str
    recommendation_score: Decimal
    net_probability_edge: Decimal
    total_cost_per_share: Decimal
    depth_status: str
    executable_paper_shares: Decimal
    review_priority: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_positive_int("queue_rank", self.queue_rank)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_side("side", self.side)
        _require_action("action", self.action)
        object.__setattr__(
            self,
            "recommendation_score",
            _normalize_probability("recommendation_score", self.recommendation_score),
        )
        object.__setattr__(
            self,
            "net_probability_edge",
            _normalize_decimal("net_probability_edge", self.net_probability_edge),
        )
        object.__setattr__(
            self,
            "total_cost_per_share",
            _normalize_nonnegative_decimal(
                "total_cost_per_share",
                self.total_cost_per_share,
            ),
        )
        _require_depth_status("depth_status", self.depth_status)
        object.__setattr__(
            self,
            "executable_paper_shares",
            _normalize_nonnegative_decimal(
                "executable_paper_shares",
                self.executable_paper_shares,
            ),
        )
        _require_review_priority("review_priority", self.review_priority)
        _require_recommended_next_step(
            "recommended_next_step",
            self.recommended_next_step,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_queue_row(self)
        _require_safety_flags("queue_row", self)


@dataclass(frozen=True)
class PaperProbabilityRecommendationQueueReport:
    generated_at: datetime
    source_config_version: str
    input_count: int
    queue_count: int
    research_review_count: int
    await_fresh_context_count: int
    skip_count: int
    excluded_count: int
    queue_rows: tuple[PaperProbabilityRecommendationQueueRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("source_config_version", self.source_config_version)
        for field_name in (
            "input_count",
            "queue_count",
            "research_review_count",
            "await_fresh_context_count",
            "skip_count",
            "excluded_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        queue_rows = _normalize_queue_rows(self.queue_rows)
        object.__setattr__(self, "queue_rows", queue_rows)
        _validate_report(self)
        _require_safety_flags("queue_report", self)


def build_paper_probability_recommendation_queue_report(
    rows: Iterable[PaperProbabilitySideEdgeRow],
    *,
    config: PaperProbabilityRecommendationQueueConfig,
    generated_at: datetime,
) -> PaperProbabilityRecommendationQueueReport:
    """Reduce side-edge rows to a research-review queue, never an order queue."""

    if type(config) is not PaperProbabilityRecommendationQueueConfig:
        raise ValueError("config must be a PaperProbabilityRecommendationQueueConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_safety_flags("config", config)

    input_rows = _normalize_inputs(rows)
    row_values = _rankable_values(input_rows, config=config)
    selected_values = _rank_values(row_values[: config.max_queue_rows])
    queue_rows = tuple(
        PaperProbabilityRecommendationQueueRow(
            queue_rank=index,
            market_slug=values.market_slug,
            question=values.question,
            side=values.side,
            action=values.action,
            recommendation_score=values.recommendation_score,
            net_probability_edge=values.net_probability_edge,
            total_cost_per_share=values.total_cost_per_share,
            depth_status=values.depth_status,
            executable_paper_shares=values.executable_paper_shares,
            review_priority=values.review_priority,
            recommended_next_step=values.recommended_next_step,
            reason_codes=values.reason_codes,
        )
        for index, values in enumerate(selected_values, start=1)
    )
    return PaperProbabilityRecommendationQueueReport(
        generated_at=_as_utc(generated_at),
        source_config_version=config.config_version,
        input_count=len(input_rows),
        queue_count=len(queue_rows),
        research_review_count=_next_step_count(queue_rows, "research_review"),
        await_fresh_context_count=_next_step_count(
            queue_rows,
            "await_fresh_context",
        ),
        skip_count=_next_step_count(queue_rows, "skip"),
        excluded_count=len(input_rows) - len(queue_rows),
        queue_rows=queue_rows,
    )


@dataclass(frozen=True)
class _QueueValues:
    market_slug: str
    question: str
    side: str
    action: str
    recommendation_score: Decimal
    net_probability_edge: Decimal
    total_cost_per_share: Decimal
    depth_status: str
    executable_paper_shares: Decimal
    review_priority: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]


def _rankable_values(
    rows: tuple[PaperProbabilitySideEdgeRow, ...],
    *,
    config: PaperProbabilityRecommendationQueueConfig,
) -> tuple[_QueueValues, ...]:
    return tuple(
        sorted(
            (
                value
                for value in (_queue_values(row, config=config) for row in rows)
                if value is not None
            ),
            key=_values_sort_key,
        ),
    )


def _queue_values(
    row: PaperProbabilitySideEdgeRow,
    *,
    config: PaperProbabilityRecommendationQueueConfig,
) -> _QueueValues | None:
    next_step = _recommended_next_step(row, config=config)
    if next_step is None:
        return None
    return _QueueValues(
        market_slug=row.market_slug,
        question=row.question,
        side=row.side,
        action=row.action,
        recommendation_score=row.recommendation_score,
        net_probability_edge=row.net_probability_edge,
        total_cost_per_share=row.total_cost_per_share,
        depth_status=row.depth_status,
        executable_paper_shares=row.executable_paper_shares,
        review_priority=_review_priority(next_step),
        recommended_next_step=next_step,
        reason_codes=row.reason_codes,
    )


def _recommended_next_step(
    row: PaperProbabilitySideEdgeRow,
    *,
    config: PaperProbabilityRecommendationQueueConfig,
) -> str | None:
    if (
        row.action == "recommend"
        and row.recommendation_score >= config.min_recommendation_score
    ):
        return "research_review"
    if config.include_watch is not True:
        return None
    if row.action == "reject":
        return "skip"
    return "await_fresh_context"


def _review_priority(recommended_next_step: str) -> str:
    if recommended_next_step == "research_review":
        return "research_review"
    if recommended_next_step == "await_fresh_context":
        return "watch"
    return "skip"


def _rank_values(values: tuple[_QueueValues, ...]) -> tuple[_QueueValues, ...]:
    return tuple(sorted(values, key=_values_sort_key))


def _values_sort_key(
    values: _QueueValues,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        NEXT_STEP_RANK[values.recommended_next_step],
        -values.recommendation_score,
        -values.net_probability_edge,
        -values.executable_paper_shares,
        values.total_cost_per_share,
        values.market_slug,
        values.side,
    )


def _normalize_inputs(
    value: Iterable[PaperProbabilitySideEdgeRow],
) -> tuple[PaperProbabilitySideEdgeRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("inputs must be an iterable of PaperProbabilitySideEdgeRow values")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of PaperProbabilitySideEdgeRow values",
        ) from exc
    for row in rows:
        if type(row) is not PaperProbabilitySideEdgeRow:
            raise ValueError("inputs must contain PaperProbabilitySideEdgeRow values")
        _require_safety_flags("inputs", row)
    return rows


def _normalize_queue_rows(
    value: Iterable[PaperProbabilityRecommendationQueueRow],
) -> tuple[PaperProbabilityRecommendationQueueRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("queue_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("queue_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperProbabilityRecommendationQueueRow:
            raise ValueError(
                "queue_rows must contain PaperProbabilityRecommendationQueueRow values",
            )
        _require_safety_flags("queue_rows", row)
    return rows


def _validate_queue_row(row: PaperProbabilityRecommendationQueueRow) -> None:
    expected_priority = _review_priority(row.recommended_next_step)
    if row.review_priority != expected_priority:
        raise ValueError("review_priority must match recommended_next_step")
    if row.recommended_next_step == "research_review":
        if row.action != "recommend":
            raise ValueError("recommended_next_step must match action")
        if row.recommendation_score <= ZERO:
            raise ValueError("recommendation_score must be positive")
    if row.recommended_next_step == "await_fresh_context" and row.action == "reject":
        raise ValueError("recommended_next_step must match action")
    if row.recommended_next_step == "skip" and row.action != "reject":
        raise ValueError("recommended_next_step must match action")


def _validate_report(report: PaperProbabilityRecommendationQueueReport) -> None:
    if report.queue_count != len(report.queue_rows):
        raise ValueError("queue_count must match queue_rows")
    if report.input_count < report.queue_count:
        raise ValueError("input_count must be at least queue_count")
    if report.excluded_count != report.input_count - report.queue_count:
        raise ValueError("excluded_count must match input_count and queue_count")
    if report.research_review_count != _next_step_count(
        report.queue_rows,
        "research_review",
    ):
        raise ValueError("research_review_count must match queue_rows")
    if report.await_fresh_context_count != _next_step_count(
        report.queue_rows,
        "await_fresh_context",
    ):
        raise ValueError("await_fresh_context_count must match queue_rows")
    if report.skip_count != _next_step_count(report.queue_rows, "skip"):
        raise ValueError("skip_count must match queue_rows")
    if (
        report.research_review_count
        + report.await_fresh_context_count
        + report.skip_count
        != report.queue_count
    ):
        raise ValueError("recommended_next_step counts must match queue_count")
    if tuple(row.queue_rank for row in report.queue_rows) != tuple(
        range(1, len(report.queue_rows) + 1),
    ):
        raise ValueError("queue_rank values must be contiguous")
    if report.queue_rows != _sort_queue_rows(report.queue_rows):
        raise ValueError("queue_rows must use deterministic ordering")


def _sort_queue_rows(
    rows: tuple[PaperProbabilityRecommendationQueueRow, ...],
) -> tuple[PaperProbabilityRecommendationQueueRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                NEXT_STEP_RANK[row.recommended_next_step],
                -row.recommendation_score,
                -row.net_probability_edge,
                -row.executable_paper_shares,
                row.total_cost_per_share,
                row.market_slug,
                row.side,
                row.queue_rank,
            ),
        ),
    )


def _next_step_count(
    rows: Iterable[PaperProbabilityRecommendationQueueRow],
    recommended_next_step: str,
) -> int:
    return sum(1 for row in rows if row.recommended_next_step == recommended_next_step)


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for value in values:
        _require_canonical_string("reason_codes", value)
    return tuple(sorted(set(values)))


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes or no")


def _require_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTIONS:
        raise ValueError(f"{field_name} must be recommend, watch, or reject")


def _require_depth_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DEPTH_STATUSES:
        raise ValueError(f"{field_name} must be a known depth status")


def _require_review_priority(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REVIEW_PRIORITIES:
        raise ValueError(f"{field_name} must be research_review, watch, or skip")


def _require_recommended_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RECOMMENDED_NEXT_STEPS:
        raise ValueError(
            f"{field_name} must be research_review, await_fresh_context, or skip",
        )


def _require_safety_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")
