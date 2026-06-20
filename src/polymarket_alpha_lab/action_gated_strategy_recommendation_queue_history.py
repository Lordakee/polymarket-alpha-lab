"""Pure history reducer for action-gated queue reports."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)


__all__ = (
    "PaperActionGatedStrategyRecommendationQueueHistoryReport",
    "build_paper_action_gated_strategy_recommendation_queue_history_report",
)


ZERO = Decimal("0")
QUANTUM = Decimal("0.000001")
ACTION_STATUSES = ("research_ready", "watch", "blocked")
QUEUE_NEXT_STEPS = (
    "review_candidate_research_queue",
    "await_fresh_cycle_evidence",
    "repair_cycle_evidence",
)
NEXT_STEP_BY_ACTION_STATUS = {
    "research_ready": "review_candidate_research_queue",
    "watch": "await_fresh_cycle_evidence",
    "blocked": "repair_cycle_evidence",
}


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueHistoryReport:
    generated_at: datetime
    source_report_count: int
    first_source_generated_at: datetime | None
    last_source_generated_at: datetime | None
    research_ready_count: int
    watch_count: int
    blocked_count: int
    total_ready_notional: Decimal
    latest_action_status: str | None
    latest_recommended_next_step: str | None
    status_transition_count: int
    ready_notional_delta: Decimal
    latest_reason_code_counts: tuple[
        PaperRecommendationCycleActionGateReasonCodeCount,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_source_generated_at",
            _as_optional_utc(self.first_source_generated_at),
        )
        object.__setattr__(
            self,
            "last_source_generated_at",
            _as_optional_utc(self.last_source_generated_at),
        )
        for field_name in (
            "source_report_count",
            "research_ready_count",
            "watch_count",
            "blocked_count",
            "status_transition_count",
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
        _require_optional_action_status("latest_action_status", self.latest_action_status)
        _require_optional_queue_next_step(
            "latest_recommended_next_step",
            self.latest_recommended_next_step,
        )
        object.__setattr__(
            self,
            "ready_notional_delta",
            _quantize_decimal("ready_notional_delta", self.ready_notional_delta),
        )
        object.__setattr__(
            self,
            "latest_reason_code_counts",
            _normalize_reason_code_counts(self.latest_reason_code_counts),
        )
        _validate_history_report(self)
        _require_hard_flags("history_report", self)


def build_paper_action_gated_strategy_recommendation_queue_history_report(
    reports: Iterable[PaperActionGatedStrategyRecommendationQueueReport],
    *,
    generated_at: datetime,
) -> PaperActionGatedStrategyRecommendationQueueHistoryReport:
    """Reduce exact action-gated queue reports into deterministic history metrics."""

    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    source_reports = _normalize_source_reports(reports)
    first_report = source_reports[0] if source_reports else None
    latest_report = source_reports[-1] if source_reports else None

    return PaperActionGatedStrategyRecommendationQueueHistoryReport(
        generated_at=generated_at,
        source_report_count=len(source_reports),
        first_source_generated_at=(
            first_report.generated_at if first_report is not None else None
        ),
        last_source_generated_at=(
            latest_report.generated_at if latest_report is not None else None
        ),
        research_ready_count=_action_status_count(source_reports, "research_ready"),
        watch_count=_action_status_count(source_reports, "watch"),
        blocked_count=_action_status_count(source_reports, "blocked"),
        total_ready_notional=_total_ready_notional(source_reports),
        latest_action_status=(
            latest_report.action_status if latest_report is not None else None
        ),
        latest_recommended_next_step=(
            latest_report.recommended_next_step if latest_report is not None else None
        ),
        status_transition_count=_status_transition_count(source_reports),
        ready_notional_delta=_ready_notional_delta(source_reports),
        latest_reason_code_counts=(
            latest_report.reason_code_counts if latest_report is not None else ()
        ),
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
    return tuple(sorted(reports, key=_history_sort_key))


def _history_sort_key(
    report: PaperActionGatedStrategyRecommendationQueueReport,
) -> tuple[
    datetime,
    str,
    str,
    str,
    str,
    int,
    int,
    int,
    int,
    Decimal,
    tuple[tuple[str, int], ...],
]:
    return (
        report.generated_at,
        report.config_version,
        report.source_config_version,
        report.action_status,
        report.recommended_next_step,
        report.candidate_count,
        report.ready_count,
        report.watch_count,
        report.blocked_count,
        report.total_ready_notional,
        _reason_code_count_key(report.reason_code_counts),
    )


def _reason_code_count_key(
    reason_code_counts: Iterable[PaperRecommendationCycleActionGateReasonCodeCount],
) -> tuple[tuple[str, int], ...]:
    return tuple((row.reason_code, row.count) for row in reason_code_counts)


def _action_status_count(
    reports: Iterable[PaperActionGatedStrategyRecommendationQueueReport],
    action_status: str,
) -> int:
    return sum(1 for report in reports if report.action_status == action_status)


def _total_ready_notional(
    reports: Iterable[PaperActionGatedStrategyRecommendationQueueReport],
) -> Decimal:
    return _quantize_nonnegative_decimal(
        "total_ready_notional",
        sum((report.total_ready_notional for report in reports), ZERO),
    )


def _status_transition_count(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> int:
    transition_count = 0
    previous_status: str | None = None
    for report in reports:
        if previous_status is not None and report.action_status != previous_status:
            transition_count += 1
        previous_status = report.action_status
    return transition_count


def _ready_notional_delta(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> Decimal:
    if not reports:
        return ZERO.quantize(QUANTUM)
    return _quantize_decimal(
        "ready_notional_delta",
        reports[-1].total_ready_notional - reports[0].total_ready_notional,
    )


def _normalize_reason_code_counts(
    value: Iterable[PaperRecommendationCycleActionGateReasonCodeCount],
) -> tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("latest_reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("latest_reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperRecommendationCycleActionGateReasonCodeCount:
            raise ValueError(
                "latest_reason_code_counts must contain "
                "PaperRecommendationCycleActionGateReasonCodeCount values",
            )
        _require_canonical_string("latest_reason_code_counts reason_code", row.reason_code)
        _require_nonnegative_int("latest_reason_code_counts count", row.count)
    return rows


def _validate_history_report(
    report: PaperActionGatedStrategyRecommendationQueueHistoryReport,
) -> None:
    if (
        report.research_ready_count + report.watch_count + report.blocked_count
        != report.source_report_count
    ):
        raise ValueError("action status counts must match source_report_count")
    if report.source_report_count == 0:
        _validate_empty_history_report(report)
        return
    _validate_nonempty_history_report(report)


def _validate_empty_history_report(
    report: PaperActionGatedStrategyRecommendationQueueHistoryReport,
) -> None:
    if report.first_source_generated_at is not None:
        raise ValueError("first_source_generated_at must be None for empty history")
    if report.last_source_generated_at is not None:
        raise ValueError("last_source_generated_at must be None for empty history")
    if report.latest_action_status is not None:
        raise ValueError("latest_action_status must be None for empty history")
    if report.latest_recommended_next_step is not None:
        raise ValueError("latest_recommended_next_step must be None for empty history")
    if report.status_transition_count != 0:
        raise ValueError("status_transition_count must be zero for empty history")
    if report.total_ready_notional != ZERO.quantize(QUANTUM):
        raise ValueError("total_ready_notional must be zero for empty history")
    if report.ready_notional_delta != ZERO.quantize(QUANTUM):
        raise ValueError("ready_notional_delta must be zero for empty history")
    if report.latest_reason_code_counts:
        raise ValueError("latest_reason_code_counts must be empty for empty history")


def _validate_nonempty_history_report(
    report: PaperActionGatedStrategyRecommendationQueueHistoryReport,
) -> None:
    if report.first_source_generated_at is None:
        raise ValueError("first_source_generated_at is required")
    if report.last_source_generated_at is None:
        raise ValueError("last_source_generated_at is required")
    if report.last_source_generated_at < report.first_source_generated_at:
        raise ValueError("last_source_generated_at must not precede first_source_generated_at")
    if report.latest_action_status is None:
        raise ValueError("latest_action_status is required")
    if report.latest_recommended_next_step is None:
        raise ValueError("latest_recommended_next_step is required")
    if (
        report.latest_recommended_next_step
        != NEXT_STEP_BY_ACTION_STATUS[report.latest_action_status]
    ):
        raise ValueError("latest_recommended_next_step must match latest_action_status")
    if report.status_transition_count >= report.source_report_count:
        raise ValueError("status_transition_count must be below source_report_count")


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_action_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTION_STATUSES:
        raise ValueError(f"{field_name} must be research_ready, watch, or blocked")


def _require_optional_action_status(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_action_status(field_name, value)


def _require_queue_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUEUE_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a known next step")


def _require_optional_queue_next_step(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_queue_next_step(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    return _require_decimal(field_name, value).quantize(QUANTUM)


def _quantize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")
