"""Pure history reducer for strategy candidate research queue reports."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
)


__all__ = (
    "PaperStrategyCandidateResearchQueueHistoryReport",
    "build_paper_strategy_candidate_research_queue_history_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
ACTION_STATUSES = ("research_ready", "watch", "blocked")
RESEARCH_STATUSES = ("ready", "watch", "blocked")
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
class PaperStrategyCandidateResearchQueueHistoryReport:
    generated_at: datetime
    source_report_count: int
    first_source_generated_at: datetime | None
    last_source_generated_at: datetime | None
    action_status_research_ready_count: int
    action_status_watch_count: int
    action_status_blocked_count: int
    research_status_ready_count: int
    research_status_watch_count: int
    research_status_blocked_count: int
    total_ready_notional: Decimal
    total_selected_notional: Decimal
    total_suggested_notional: Decimal
    latest_action_status: str | None
    latest_recommended_next_step: str | None
    latest_research_status: str | None
    latest_top_research_priority_score: Decimal | None
    latest_average_research_ready_score: Decimal | None
    status_transition_count: int
    ready_notional_delta: Decimal
    selected_notional_delta: Decimal
    latest_selected_count: int
    latest_skipped_count: int
    latest_not_selected_count: int
    latest_primary_reason_code_counts: tuple[tuple[str, int], ...]
    latest_reason_codes: tuple[str, ...]
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
            "action_status_research_ready_count",
            "action_status_watch_count",
            "action_status_blocked_count",
            "research_status_ready_count",
            "research_status_watch_count",
            "research_status_blocked_count",
            "status_transition_count",
            "latest_selected_count",
            "latest_skipped_count",
            "latest_not_selected_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "total_ready_notional",
            _quantize_nonnegative_decimal("total_ready_notional", self.total_ready_notional),
        )
        object.__setattr__(
            self,
            "total_selected_notional",
            _quantize_nonnegative_decimal("total_selected_notional", self.total_selected_notional),
        )
        object.__setattr__(
            self,
            "total_suggested_notional",
            _quantize_nonnegative_decimal("total_suggested_notional", self.total_suggested_notional),
        )
        if self.latest_top_research_priority_score is not None:
            object.__setattr__(
                self,
                "latest_top_research_priority_score",
                _quantize_score("latest_top_research_priority_score", self.latest_top_research_priority_score),
            )
        if self.latest_average_research_ready_score is not None:
            object.__setattr__(
                self,
                "latest_average_research_ready_score",
                _quantize_score("latest_average_research_ready_score", self.latest_average_research_ready_score),
            )
        _require_optional_action_status("latest_action_status", self.latest_action_status)
        _require_optional_queue_next_step("latest_recommended_next_step", self.latest_recommended_next_step)
        _require_optional_research_status("latest_research_status", self.latest_research_status)
        object.__setattr__(
            self, "ready_notional_delta", _quantize_decimal("ready_notional_delta", self.ready_notional_delta),
        )
        object.__setattr__(
            self,
            "selected_notional_delta",
            _quantize_decimal("selected_notional_delta", self.selected_notional_delta),
        )
        object.__setattr__(
            self,
            "latest_primary_reason_code_counts",
            _normalize_reason_code_counts("latest_primary_reason_code_counts", self.latest_primary_reason_code_counts),
        )
        object.__setattr__(
            self,
            "latest_reason_codes",
            _normalize_reason_codes("latest_reason_codes", self.latest_reason_codes),
        )
        _validate_history_report(self)
        _require_hard_flags("history_report", self)


def build_paper_strategy_candidate_research_queue_history_report(
    reports: Iterable[PaperStrategyCandidateResearchQueueReport],
    *,
    generated_at: datetime,
) -> PaperStrategyCandidateResearchQueueHistoryReport:
    """Reduce exact candidate research queue reports into deterministic history metrics."""

    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    source_reports = _normalize_source_reports(reports)
    first_report = source_reports[0] if source_reports else None
    latest_report = source_reports[-1] if source_reports else None

    return PaperStrategyCandidateResearchQueueHistoryReport(
        generated_at=generated_at,
        source_report_count=len(source_reports),
        first_source_generated_at=(
            first_report.generated_at if first_report is not None else None
        ),
        last_source_generated_at=(
            latest_report.generated_at if latest_report is not None else None
        ),
        action_status_research_ready_count=_action_status_count(source_reports, "research_ready"),
        action_status_watch_count=_action_status_count(source_reports, "watch"),
        action_status_blocked_count=_action_status_count(source_reports, "blocked"),
        research_status_ready_count=_research_status_count(source_reports, "ready"),
        research_status_watch_count=_research_status_count(source_reports, "watch"),
        research_status_blocked_count=_research_status_count(source_reports, "blocked"),
        total_ready_notional=_sum_notional(source_reports, "total_ready_notional"),
        total_selected_notional=_sum_notional(source_reports, "total_selected_notional"),
        total_suggested_notional=_sum_notional(source_reports, "total_suggested_notional"),
        latest_action_status=(
            latest_report.action_status if latest_report is not None else None
        ),
        latest_recommended_next_step=(
            latest_report.recommended_next_step if latest_report is not None else None
        ),
        latest_research_status=(
            latest_report.research_status if latest_report is not None else None
        ),
        latest_top_research_priority_score=(
            latest_report.top_research_priority_score if latest_report is not None else None
        ),
        latest_average_research_ready_score=(
            latest_report.average_research_ready_score if latest_report is not None else None
        ),
        status_transition_count=_status_transition_count(source_reports),
        ready_notional_delta=_notional_delta(source_reports, "total_ready_notional"),
        selected_notional_delta=_notional_delta(source_reports, "total_selected_notional"),
        latest_selected_count=(
            latest_report.selected_count if latest_report is not None else 0
        ),
        latest_skipped_count=(
            latest_report.skipped_count if latest_report is not None else 0
        ),
        latest_not_selected_count=(
            latest_report.not_selected_count if latest_report is not None else 0
        ),
        latest_primary_reason_code_counts=(
            latest_report.primary_reason_code_counts if latest_report is not None else ()
        ),
        latest_reason_codes=(
            latest_report.reason_codes if latest_report is not None else ()
        ),
    )


# --- internal helpers ---


def _normalize_source_reports(
    value: Iterable[PaperStrategyCandidateResearchQueueReport],
) -> tuple[PaperStrategyCandidateResearchQueueReport, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reports must be an iterable")
    try:
        reports = tuple(value)
    except TypeError as exc:
        raise ValueError("reports must be an iterable") from exc
    seen_keys: set[tuple[datetime, str, str]] = set()
    for report in reports:
        if type(report) is not PaperStrategyCandidateResearchQueueReport:
            raise ValueError(
                "reports must contain PaperStrategyCandidateResearchQueueReport values",
            )
        _require_hard_flags("reports", report)
        key = _history_sort_key(report)
        if key in seen_keys:
            raise ValueError("duplicate generated_at/config source history sort key")
        seen_keys.add(key)
    return tuple(sorted(reports, key=_history_sort_key))


def _history_sort_key(
    report: PaperStrategyCandidateResearchQueueReport,
) -> tuple[datetime, str, str]:
    return (report.generated_at, report.config_version, report.source_config_version)


def _action_status_count(
    reports: tuple[PaperStrategyCandidateResearchQueueReport, ...], action_status: str,
) -> int:
    return sum(1 for r in reports if r.action_status == action_status)


def _research_status_count(
    reports: tuple[PaperStrategyCandidateResearchQueueReport, ...], research_status: str,
) -> int:
    return sum(1 for r in reports if r.research_status == research_status)


def _sum_notional(
    reports: tuple[PaperStrategyCandidateResearchQueueReport, ...], field_name: str,
) -> Decimal:
    return _quantize_nonnegative_decimal(
        field_name, sum((getattr(r, field_name) for r in reports), ZERO),
    )


def _notional_delta(
    reports: tuple[PaperStrategyCandidateResearchQueueReport, ...], field_name: str,
) -> Decimal:
    if not reports:
        return ZERO.quantize(QUANTUM)
    return _quantize_decimal(
        f"{field_name}_delta",
        getattr(reports[-1], field_name) - getattr(reports[0], field_name),
    )


def _status_transition_count(
    reports: tuple[PaperStrategyCandidateResearchQueueReport, ...],
) -> int:
    transition_count = 0
    previous_status: str | None = None
    for report in reports:
        if previous_status is not None and report.action_status != previous_status:
            transition_count += 1
        previous_status = report.action_status
    return transition_count


def _normalize_reason_code_counts(
    field_name: str, value: Iterable[tuple[str, int]],
) -> tuple[tuple[str, int], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in rows:
        if not isinstance(row, tuple) or len(row) != 2:
            raise ValueError(f"{field_name} items must be (str, int) tuples")
        code, count = row
        _require_canonical_string(f"{field_name} reason_code", code)
        if code in seen_codes:
            raise ValueError(f"duplicate {field_name} reason_code")
        seen_codes.add(code)
        _require_nonnegative_int(f"{field_name} count", count)
        if count == 0:
            raise ValueError(f"{field_name} count must be positive")
    return rows


def _normalize_reason_codes(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    normalized: list[str] = []
    for code in codes:
        _require_canonical_string(f"{field_name} item", code)
        if code not in normalized:
            normalized.append(code)
    return tuple(normalized)


def _validate_history_report(report: PaperStrategyCandidateResearchQueueHistoryReport) -> None:
    action_total = (
        report.action_status_research_ready_count
        + report.action_status_watch_count
        + report.action_status_blocked_count
    )
    if action_total != report.source_report_count:
        raise ValueError("action status counts must match source_report_count")
    research_total = (
        report.research_status_ready_count
        + report.research_status_watch_count
        + report.research_status_blocked_count
    )
    if research_total != report.source_report_count:
        raise ValueError("research status counts must match source_report_count")
    if report.source_report_count == 0:
        _validate_empty_history_report(report)
        return
    _validate_nonempty_history_report(report)


def _validate_empty_history_report(report: PaperStrategyCandidateResearchQueueHistoryReport) -> None:
    if report.first_source_generated_at is not None:
        raise ValueError("first_source_generated_at must be None for empty history")
    if report.last_source_generated_at is not None:
        raise ValueError("last_source_generated_at must be None for empty history")
    if report.latest_action_status is not None:
        raise ValueError("latest_action_status must be None for empty history")
    if report.latest_recommended_next_step is not None:
        raise ValueError("latest_recommended_next_step must be None for empty history")
    if report.latest_research_status is not None:
        raise ValueError("latest_research_status must be None for empty history")
    if report.latest_top_research_priority_score is not None:
        raise ValueError("latest_top_research_priority_score must be None for empty history")
    if report.latest_average_research_ready_score is not None:
        raise ValueError("latest_average_research_ready_score must be None for empty history")
    if report.status_transition_count != 0:
        raise ValueError("status_transition_count must be zero for empty history")
    for notional_field in (
        "total_ready_notional", "total_selected_notional", "total_suggested_notional",
        "ready_notional_delta", "selected_notional_delta",
    ):
        if getattr(report, notional_field) != ZERO.quantize(QUANTUM):
            raise ValueError(f"{notional_field} must be zero for empty history")
    for count_field in ("latest_selected_count", "latest_skipped_count", "latest_not_selected_count"):
        if getattr(report, count_field) != 0:
            raise ValueError(f"{count_field} must be zero for empty history")
    if report.latest_primary_reason_code_counts:
        raise ValueError("latest_primary_reason_code_counts must be empty for empty history")
    if report.latest_reason_codes:
        raise ValueError("latest_reason_codes must be empty for empty history")


def _validate_nonempty_history_report(report: PaperStrategyCandidateResearchQueueHistoryReport) -> None:
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
    if report.latest_research_status is None:
        raise ValueError("latest_research_status is required")
    if report.latest_top_research_priority_score is None:
        raise ValueError("latest_top_research_priority_score is required")
    if report.latest_average_research_ready_score is None:
        raise ValueError("latest_average_research_ready_score is required")
    if _action_status_report_count(report, report.latest_action_status) == 0:
        raise ValueError("latest_action_status must be represented in status counts")
    if _research_status_report_count(report, report.latest_research_status) == 0:
        raise ValueError("latest_research_status must be represented in status counts")
    if (
        report.latest_recommended_next_step
        != NEXT_STEP_BY_ACTION_STATUS[report.latest_action_status]
    ):
        raise ValueError("latest_recommended_next_step must match latest_action_status")
    if report.status_transition_count >= report.source_report_count:
        raise ValueError("status_transition_count must be below source_report_count")


def _action_status_report_count(
    report: PaperStrategyCandidateResearchQueueHistoryReport,
    status: str,
) -> int:
    if status == "research_ready":
        return report.action_status_research_ready_count
    if status == "watch":
        return report.action_status_watch_count
    return report.action_status_blocked_count


def _research_status_report_count(
    report: PaperStrategyCandidateResearchQueueHistoryReport,
    status: str,
) -> int:
    if status == "ready":
        return report.research_status_ready_count
    if status == "watch":
        return report.research_status_watch_count
    return report.research_status_blocked_count


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


def _require_optional_research_status(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not str or value not in RESEARCH_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


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


def _quantize_score(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")
