"""Pure research-priority ranking for action-gated queue reports."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)


__all__ = (
    "PaperActionGatedStrategyRecommendationQueuePriorityReport",
    "PaperActionGatedStrategyRecommendationQueuePriorityRow",
    "build_paper_action_gated_strategy_recommendation_queue_priority_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
ACTION_STATUSES = ("research_ready", "watch", "blocked")
QUEUE_NEXT_STEPS = (
    "review_candidate_research_queue",
    "await_fresh_cycle_evidence",
    "repair_cycle_evidence",
)
RESEARCH_PRIORITIES = (
    "research_review",
    "await_fresh_context",
    "repair_evidence",
)
ACTION_STATUS_RANK = {
    "research_ready": 0,
    "watch": 1,
    "blocked": 2,
}
ACTION_STATUS_SCORE = {
    "research_ready": Decimal("3.000000"),
    "watch": Decimal("1.000000"),
    "blocked": Decimal("0.000000"),
}
RESEARCH_PRIORITY_BY_ACTION_STATUS = {
    "research_ready": "research_review",
    "watch": "await_fresh_context",
    "blocked": "repair_evidence",
}


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueuePriorityRow:
    priority_rank: int
    source_generated_at: datetime
    config_version: str
    source_config_version: str
    action_status: str
    recommended_next_step: str
    research_priority: str
    candidate_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    total_ready_notional: Decimal
    top_queue_score: Decimal
    average_ready_score: Decimal
    research_priority_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_positive_int("priority_rank", self.priority_rank)
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc(self.source_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_action_status("action_status", self.action_status)
        _require_queue_next_step("recommended_next_step", self.recommended_next_step)
        _require_research_priority("research_priority", self.research_priority)
        for field_name in (
            "candidate_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "total_ready_notional",
            _quantize_nonnegative_decimal(
                "total_ready_notional",
                self.total_ready_notional,
            ),
        )
        object.__setattr__(
            self,
            "top_queue_score",
            _quantize_score("top_queue_score", self.top_queue_score),
        )
        object.__setattr__(
            self,
            "average_ready_score",
            _quantize_score("average_ready_score", self.average_ready_score),
        )
        object.__setattr__(
            self,
            "research_priority_score",
            _quantize_nonnegative_decimal(
                "research_priority_score",
                self.research_priority_score,
            ),
        )
        _validate_priority_row(self)
        _require_hard_flags("priority_row", self)


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueuePriorityReport:
    generated_at: datetime
    source_report_count: int
    research_ready_count: int
    watch_count: int
    blocked_count: int
    total_ready_notional: Decimal
    top_research_priority_score: Decimal
    average_research_priority_score: Decimal
    priority_rows: tuple[PaperActionGatedStrategyRecommendationQueuePriorityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        for field_name in (
            "source_report_count",
            "research_ready_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "total_ready_notional",
            _quantize_nonnegative_decimal(
                "total_ready_notional",
                self.total_ready_notional,
            ),
        )
        object.__setattr__(
            self,
            "top_research_priority_score",
            _quantize_nonnegative_decimal(
                "top_research_priority_score",
                self.top_research_priority_score,
            ),
        )
        object.__setattr__(
            self,
            "average_research_priority_score",
            _quantize_nonnegative_decimal(
                "average_research_priority_score",
                self.average_research_priority_score,
            ),
        )
        object.__setattr__(
            self,
            "priority_rows",
            _normalize_priority_rows(self.priority_rows),
        )
        _validate_priority_report(self)
        _require_hard_flags("priority_report", self)


def build_paper_action_gated_strategy_recommendation_queue_priority_report(
    reports: Iterable[PaperActionGatedStrategyRecommendationQueueReport],
    *,
    generated_at: datetime,
) -> PaperActionGatedStrategyRecommendationQueuePriorityReport:
    """Rank action-gated paper queue reports for human research attention."""

    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    source_reports = _normalize_source_reports(reports)
    values = tuple(
        sorted(
            (_priority_values(report) for report in source_reports),
            key=_sort_key,
        ),
    )
    priority_rows = tuple(
        PaperActionGatedStrategyRecommendationQueuePriorityRow(
            priority_rank=index,
            source_generated_at=value.source_generated_at,
            config_version=value.config_version,
            source_config_version=value.source_config_version,
            action_status=value.action_status,
            recommended_next_step=value.recommended_next_step,
            research_priority=value.research_priority,
            candidate_count=value.candidate_count,
            ready_count=value.ready_count,
            watch_count=value.watch_count,
            blocked_count=value.blocked_count,
            total_ready_notional=value.total_ready_notional,
            top_queue_score=value.top_queue_score,
            average_ready_score=value.average_ready_score,
            research_priority_score=value.research_priority_score,
        )
        for index, value in enumerate(values, start=1)
    )

    return PaperActionGatedStrategyRecommendationQueuePriorityReport(
        generated_at=generated_at,
        source_report_count=len(source_reports),
        research_ready_count=_action_status_count(priority_rows, "research_ready"),
        watch_count=_action_status_count(priority_rows, "watch"),
        blocked_count=_action_status_count(priority_rows, "blocked"),
        total_ready_notional=_total_ready_notional(priority_rows),
        top_research_priority_score=_top_research_priority_score(priority_rows),
        average_research_priority_score=_average_research_priority_score(priority_rows),
        priority_rows=priority_rows,
    )


@dataclass(frozen=True)
class _PriorityValues:
    source_generated_at: datetime
    config_version: str
    source_config_version: str
    action_status: str
    recommended_next_step: str
    research_priority: str
    candidate_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    total_ready_notional: Decimal
    top_queue_score: Decimal
    average_ready_score: Decimal
    research_priority_score: Decimal


def _priority_values(
    report: PaperActionGatedStrategyRecommendationQueueReport,
) -> _PriorityValues:
    top_queue_score = _source_top_queue_score(report)
    average_ready_score = _source_average_ready_score(report)
    return _PriorityValues(
        source_generated_at=report.generated_at,
        config_version=report.config_version,
        source_config_version=report.source_config_version,
        action_status=report.action_status,
        recommended_next_step=report.recommended_next_step,
        research_priority=RESEARCH_PRIORITY_BY_ACTION_STATUS[report.action_status],
        candidate_count=report.candidate_count,
        ready_count=report.ready_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        total_ready_notional=report.total_ready_notional,
        top_queue_score=top_queue_score,
        average_ready_score=average_ready_score,
        research_priority_score=_research_priority_score(
            report=report,
            top_queue_score=top_queue_score,
            average_ready_score=average_ready_score,
        ),
    )


def _research_priority_score(
    *,
    report: PaperActionGatedStrategyRecommendationQueueReport,
    top_queue_score: Decimal,
    average_ready_score: Decimal,
) -> Decimal:
    return _expected_research_priority_score(
        action_status=report.action_status,
        ready_count=report.ready_count,
        top_queue_score=top_queue_score,
        average_ready_score=average_ready_score,
    )


def _source_top_queue_score(
    report: PaperActionGatedStrategyRecommendationQueueReport,
) -> Decimal:
    if report.queue_summary_report is None:
        return ZERO.quantize(QUANTUM)
    _require_hard_flags("queue_summary_report", report.queue_summary_report)
    return report.queue_summary_report.top_score


def _source_average_ready_score(
    report: PaperActionGatedStrategyRecommendationQueueReport,
) -> Decimal:
    if report.queue_summary_report is None:
        return ZERO.quantize(QUANTUM)
    _require_hard_flags("queue_summary_report", report.queue_summary_report)
    return report.queue_summary_report.average_ready_score


def _sort_key(
    values: _PriorityValues,
) -> tuple[int, int, Decimal, Decimal, Decimal, int, str, str, datetime]:
    return (
        ACTION_STATUS_RANK[values.action_status],
        -values.ready_count,
        -values.top_queue_score,
        -values.average_ready_score,
        -values.total_ready_notional,
        -values.candidate_count,
        values.config_version,
        values.source_config_version,
        values.source_generated_at,
    )


def _priority_row_sort_key(
    row: PaperActionGatedStrategyRecommendationQueuePriorityRow,
) -> tuple[int, int, Decimal, Decimal, Decimal, int, str, str, datetime, int]:
    return (
        ACTION_STATUS_RANK[row.action_status],
        -row.ready_count,
        -row.top_queue_score,
        -row.average_ready_score,
        -row.total_ready_notional,
        -row.candidate_count,
        row.config_version,
        row.source_config_version,
        row.source_generated_at,
        row.priority_rank,
    )


def _normalize_source_reports(
    value: Iterable[PaperActionGatedStrategyRecommendationQueueReport],
) -> tuple[PaperActionGatedStrategyRecommendationQueueReport, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reports must be an iterable")
    try:
        reports = tuple(value)
    except TypeError as exc:
        raise ValueError("reports must be an iterable") from exc
    for report in reports:
        if type(report) is not PaperActionGatedStrategyRecommendationQueueReport:
            raise ValueError(
                "reports must contain "
                "PaperActionGatedStrategyRecommendationQueueReport values",
            )
        _require_hard_flags("reports", report)
    return reports


def _normalize_priority_rows(
    value: Iterable[PaperActionGatedStrategyRecommendationQueuePriorityRow],
) -> tuple[PaperActionGatedStrategyRecommendationQueuePriorityRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("priority_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("priority_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperActionGatedStrategyRecommendationQueuePriorityRow:
            raise ValueError(
                "priority_rows must contain "
                "PaperActionGatedStrategyRecommendationQueuePriorityRow values",
            )
        _require_hard_flags("priority_rows", row)
    return rows


def _validate_priority_row(
    row: PaperActionGatedStrategyRecommendationQueuePriorityRow,
) -> None:
    expected_priority = RESEARCH_PRIORITY_BY_ACTION_STATUS[row.action_status]
    if row.research_priority != expected_priority:
        raise ValueError("research_priority must match action_status")
    if row.research_priority_score != _expected_research_priority_score(
        action_status=row.action_status,
        ready_count=row.ready_count,
        top_queue_score=row.top_queue_score,
        average_ready_score=row.average_ready_score,
    ):
        raise ValueError("research_priority_score must match row fields")
    if row.ready_count + row.watch_count + row.blocked_count != row.candidate_count:
        raise ValueError("status counts must match candidate_count")
    if (
        row.action_status == "research_ready"
        and row.recommended_next_step != "review_candidate_research_queue"
    ):
        raise ValueError("recommended_next_step must match action_status")
    if (
        row.action_status == "watch"
        and row.recommended_next_step != "await_fresh_cycle_evidence"
    ):
        raise ValueError("recommended_next_step must match action_status")
    if (
        row.action_status == "blocked"
        and row.recommended_next_step != "repair_cycle_evidence"
    ):
        raise ValueError("recommended_next_step must match action_status")


def _expected_research_priority_score(
    *,
    action_status: str,
    ready_count: int,
    top_queue_score: Decimal,
    average_ready_score: Decimal,
) -> Decimal:
    raw_score = (
        ACTION_STATUS_SCORE[action_status]
        + Decimal(ready_count)
        + top_queue_score
        + average_ready_score
    )
    return _quantize_nonnegative_decimal("research_priority_score", raw_score)


def _validate_priority_report(
    report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> None:
    if report.source_report_count != len(report.priority_rows):
        raise ValueError("source_report_count must match priority_rows")
    if report.research_ready_count != _action_status_count(
        report.priority_rows,
        "research_ready",
    ):
        raise ValueError("research_ready_count must match priority_rows")
    if report.watch_count != _action_status_count(report.priority_rows, "watch"):
        raise ValueError("watch_count must match priority_rows")
    if report.blocked_count != _action_status_count(report.priority_rows, "blocked"):
        raise ValueError("blocked_count must match priority_rows")
    if (
        report.research_ready_count + report.watch_count + report.blocked_count
        != report.source_report_count
    ):
        raise ValueError("action status counts must match source_report_count")
    if tuple(row.priority_rank for row in report.priority_rows) != tuple(
        range(1, len(report.priority_rows) + 1),
    ):
        raise ValueError("priority_rank values must be contiguous")
    if report.priority_rows != tuple(
        sorted(report.priority_rows, key=_priority_row_sort_key),
    ):
        raise ValueError("priority_rows must use deterministic ordering")
    if report.total_ready_notional != _total_ready_notional(report.priority_rows):
        raise ValueError("total_ready_notional must match priority_rows")
    if report.top_research_priority_score != _top_research_priority_score(
        report.priority_rows,
    ):
        raise ValueError("top_research_priority_score must match priority_rows")
    if report.average_research_priority_score != _average_research_priority_score(
        report.priority_rows,
    ):
        raise ValueError("average_research_priority_score must match priority_rows")


def _action_status_count(
    rows: Iterable[PaperActionGatedStrategyRecommendationQueuePriorityRow],
    action_status: str,
) -> int:
    return sum(1 for row in rows if row.action_status == action_status)


def _total_ready_notional(
    rows: Iterable[PaperActionGatedStrategyRecommendationQueuePriorityRow],
) -> Decimal:
    return _quantize_nonnegative_decimal(
        "total_ready_notional",
        sum((row.total_ready_notional for row in rows), ZERO),
    )


def _top_research_priority_score(
    rows: tuple[PaperActionGatedStrategyRecommendationQueuePriorityRow, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANTUM)
    return _quantize_nonnegative_decimal(
        "top_research_priority_score",
        max(row.research_priority_score for row in rows),
    )


def _average_research_priority_score(
    rows: tuple[PaperActionGatedStrategyRecommendationQueuePriorityRow, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANTUM)
    return _quantize_nonnegative_decimal(
        "average_research_priority_score",
        sum((row.research_priority_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _as_utc(value: object) -> datetime:
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


def _require_action_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTION_STATUSES:
        raise ValueError(f"{field_name} must be research_ready, watch, or blocked")


def _require_queue_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUEUE_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a known next step")


def _require_research_priority(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_PRIORITIES:
        raise ValueError(f"{field_name} must be a known research priority")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _quantize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(QUANTUM)


def _quantize_score(field_name: str, value: object) -> Decimal:
    score = _quantize_nonnegative_decimal(field_name, value)
    if score > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return score


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")
