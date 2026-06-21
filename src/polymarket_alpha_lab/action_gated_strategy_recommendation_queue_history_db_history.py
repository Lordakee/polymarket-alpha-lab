"""Read-only history aggregation for persisted action-gated queue history reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history import (
    PaperActionGatedStrategyRecommendationQueueHistoryReport,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)


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
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryReport:
    generated_at: datetime
    config_version: str
    history_report_count: int
    first_history_generated_at: datetime | None
    latest_history_generated_at: datetime | None
    latest_source_report_count: int | None
    latest_action_status: str | None
    latest_recommended_next_step: str | None
    action_status_counts: tuple[tuple[str, int], ...]
    duplicate_generated_at_count: int
    consecutive_latest_research_ready_count: int
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    latest_total_ready_notional: Decimal | None
    latest_ready_notional_delta: Decimal | None
    latest_status_transition_count: int | None
    latest_reason_code_counts: tuple[tuple[str, int], ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "history_report_count",
            "duplicate_generated_at_count",
            "consecutive_latest_research_ready_count",
            "consecutive_latest_watch_count",
            "consecutive_latest_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "first_history_generated_at",
            _as_optional_utc(
                "first_history_generated_at",
                self.first_history_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_history_generated_at",
            _as_optional_utc(
                "latest_history_generated_at",
                self.latest_history_generated_at,
            ),
        )
        if self.latest_source_report_count is not None:
            _require_nonnegative_int(
                "latest_source_report_count",
                self.latest_source_report_count,
            )
        _require_optional_action_status("latest_action_status", self.latest_action_status)
        _require_optional_queue_next_step(
            "latest_recommended_next_step",
            self.latest_recommended_next_step,
        )
        _validate_optional_next_step_pair(
            self.latest_action_status,
            self.latest_recommended_next_step,
        )
        object.__setattr__(
            self,
            "action_status_counts",
            _normalize_action_status_counts(self.action_status_counts),
        )
        object.__setattr__(
            self,
            "latest_total_ready_notional",
            _quantize_optional_nonnegative_decimal(
                "latest_total_ready_notional",
                self.latest_total_ready_notional,
            ),
        )
        object.__setattr__(
            self,
            "latest_ready_notional_delta",
            _quantize_optional_decimal(
                "latest_ready_notional_delta",
                self.latest_ready_notional_delta,
            ),
        )
        if self.latest_status_transition_count is not None:
            _require_nonnegative_int(
                "latest_status_transition_count",
                self.latest_status_transition_count,
            )
        object.__setattr__(
            self,
            "latest_reason_code_counts",
            _normalize_reason_code_counts(
                "latest_reason_code_counts",
                self.latest_reason_code_counts,
            ),
        )
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_paper_action_gated_strategy_recommendation_queue_history_db_history_report(
    history_reports: object,
    *,
    config: PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryConfig,
    generated_at: datetime,
) -> PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryReport:
    if type(config) is not PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryConfig:
        raise ValueError(
            "config must be a "
            "PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    reports = _normalize_history_reports(history_reports)
    chronological_reports = tuple(sorted(reports, key=_history_sort_key))
    latest = chronological_reports[-1] if chronological_reports else None
    previous = chronological_reports[-2] if len(chronological_reports) >= 2 else None

    return PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        history_report_count=len(chronological_reports),
        first_history_generated_at=(
            chronological_reports[0].generated_at
            if chronological_reports
            else None
        ),
        latest_history_generated_at=(
            latest.generated_at if latest is not None else None
        ),
        latest_source_report_count=(
            latest.source_report_count if latest is not None else None
        ),
        latest_action_status=(
            latest.latest_action_status if latest is not None else None
        ),
        latest_recommended_next_step=(
            latest.latest_recommended_next_step if latest is not None else None
        ),
        action_status_counts=_action_status_counts(chronological_reports),
        duplicate_generated_at_count=_duplicate_generated_at_count(
            chronological_reports,
        ),
        consecutive_latest_research_ready_count=_latest_status_streak(
            chronological_reports,
            "research_ready",
        ),
        consecutive_latest_watch_count=_latest_status_streak(
            chronological_reports,
            "watch",
        ),
        consecutive_latest_blocked_count=_latest_status_streak(
            chronological_reports,
            "blocked",
        ),
        latest_total_ready_notional=(
            latest.total_ready_notional if latest is not None else None
        ),
        latest_ready_notional_delta=(
            _quantize_decimal_result(
                "latest_ready_notional_delta",
                latest.total_ready_notional - previous.total_ready_notional,
            )
            if latest is not None and previous is not None
            else None
        ),
        latest_status_transition_count=(
            latest.status_transition_count if latest is not None else None
        ),
        latest_reason_code_counts=(
            _reason_code_count_key(latest.latest_reason_code_counts)
            if latest is not None
            else ()
        ),
    )


def _normalize_history_reports(
    value: object,
) -> tuple[PaperActionGatedStrategyRecommendationQueueHistoryReport, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("history_reports must be a list or tuple")
    reports = tuple(value)
    normalized = []
    for report in reports:
        if type(report) is not PaperActionGatedStrategyRecommendationQueueHistoryReport:
            raise ValueError(
                "history_reports must contain "
                "PaperActionGatedStrategyRecommendationQueueHistoryReport values",
            )
        _validate_history_report_value(report)
        normalized.append(report)
    return tuple(normalized)


def _validate_history_report_value(
    report: PaperActionGatedStrategyRecommendationQueueHistoryReport,
) -> None:
    _require_hard_flags(report)
    _as_utc("history_report generated_at", report.generated_at)
    _as_optional_utc(
        "history_report first_source_generated_at",
        report.first_source_generated_at,
    )
    _as_optional_utc(
        "history_report last_source_generated_at",
        report.last_source_generated_at,
    )
    for field_name in (
        "source_report_count",
        "research_ready_count",
        "watch_count",
        "blocked_count",
        "status_transition_count",
    ):
        _require_nonnegative_int(field_name, getattr(report, field_name))
    _quantize_nonnegative_decimal(
        "total_ready_notional",
        report.total_ready_notional,
    )
    _quantize_decimal("ready_notional_delta", report.ready_notional_delta)
    _require_optional_action_status("latest_action_status", report.latest_action_status)
    _require_optional_queue_next_step(
        "latest_recommended_next_step",
        report.latest_recommended_next_step,
    )
    _validate_optional_next_step_pair(
        report.latest_action_status,
        report.latest_recommended_next_step,
    )
    _validate_history_report_source_consistency(report)
    for reason_count in report.latest_reason_code_counts:
        if type(reason_count) is not PaperRecommendationCycleActionGateReasonCodeCount:
            raise ValueError(
                "latest_reason_code_counts must contain "
                "PaperRecommendationCycleActionGateReasonCodeCount values",
            )
        _require_canonical_string("reason_code", reason_count.reason_code)
        _require_positive_int("reason_code_count", reason_count.count)


def _validate_history_report_source_consistency(
    report: PaperActionGatedStrategyRecommendationQueueHistoryReport,
) -> None:
    if (
        report.research_ready_count + report.watch_count + report.blocked_count
        != report.source_report_count
    ):
        raise ValueError("action status counts must match source_report_count")
    if report.source_report_count == 0:
        if report.latest_action_status is not None:
            raise ValueError("latest_action_status must be absent without source reports")
        if report.latest_recommended_next_step is not None:
            raise ValueError(
                "latest_recommended_next_step must be absent without source reports",
            )
        if report.latest_reason_code_counts:
            raise ValueError(
                "latest_reason_code_counts must be empty without source reports",
            )
    else:
        if report.latest_action_status is None:
            raise ValueError("latest_action_status is required with source reports")
        if report.latest_recommended_next_step is None:
            raise ValueError(
                "latest_recommended_next_step is required with source reports",
            )


def _history_sort_key(
    report: PaperActionGatedStrategyRecommendationQueueHistoryReport,
) -> tuple[
    datetime,
    int,
    tuple[bool, datetime],
    tuple[bool, datetime],
    int,
    int,
    int,
    Decimal,
    tuple[bool, str],
    tuple[bool, str],
    int,
    Decimal,
    tuple[tuple[str, int], ...],
]:
    return (
        _as_utc("generated_at", report.generated_at),
        report.source_report_count,
        _optional_datetime_sort_key(report.first_source_generated_at),
        _optional_datetime_sort_key(report.last_source_generated_at),
        report.research_ready_count,
        report.watch_count,
        report.blocked_count,
        report.total_ready_notional,
        _optional_string_sort_key(report.latest_action_status),
        _optional_string_sort_key(report.latest_recommended_next_step),
        report.status_transition_count,
        report.ready_notional_delta,
        _reason_code_count_key(report.latest_reason_code_counts),
    )


def _optional_datetime_sort_key(value: datetime | None) -> tuple[bool, datetime]:
    if value is None:
        return (False, datetime.min.replace(tzinfo=UTC))
    return (True, _as_utc("datetime", value))


def _optional_string_sort_key(value: str | None) -> tuple[bool, str]:
    if value is None:
        return (False, "")
    return (True, value)


def _reason_code_count_key(
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...],
) -> tuple[tuple[str, int], ...]:
    return tuple(sorted((row.reason_code, row.count) for row in reason_code_counts))


def _action_status_counts(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueHistoryReport, ...],
) -> tuple[tuple[str, int], ...]:
    counts = {status: 0 for status in ACTION_STATUSES}
    for report in reports:
        if report.latest_action_status in counts:
            counts[report.latest_action_status] += 1
    return tuple((status, counts[status]) for status in ACTION_STATUSES)


def _duplicate_generated_at_count(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueHistoryReport, ...],
) -> int:
    counts: dict[datetime, int] = {}
    for report in reports:
        generated_at = _as_utc("generated_at", report.generated_at)
        counts[generated_at] = counts.get(generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _latest_status_streak(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueHistoryReport, ...],
    status: str,
) -> int:
    count = 0
    for report in reversed(reports):
        if report.latest_action_status != status:
            break
        count += 1
    return count


def _normalize_action_status_counts(
    value: object,
) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError("action_status_counts must be a tuple")
    rows = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("action_status_counts must contain status/count pairs")
        status, count = item
        _require_action_status("action_status", status)
        _require_nonnegative_int("action_status_count", count)
        rows.append((status, count))
    if tuple(status for status, _ in rows) != ACTION_STATUSES:
        raise ValueError("action_status_counts must cover action statuses")
    return tuple(rows)


def _normalize_reason_code_counts(
    field_name: str,
    value: object,
) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError(f"{field_name} must contain reason/count pairs")
        reason_code, count = item
        _require_canonical_string("reason_code", reason_code)
        _require_positive_int("reason_code_count", count)
        normalized.append((reason_code, count))
    if tuple(sorted(normalized)) != tuple(normalized):
        raise ValueError(f"{field_name} must be sorted")
    return tuple(normalized)


def _validate_report_consistency(
    report: PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryReport,
) -> None:
    if report.history_report_count == 0:
        _validate_empty_report(report)
    else:
        _validate_nonempty_report(report)
    if sum(count for _, count in report.action_status_counts) > report.history_report_count:
        raise ValueError("action_status_counts must not exceed history_report_count")
    if report.duplicate_generated_at_count >= max(report.history_report_count, 1):
        raise ValueError(
            "duplicate_generated_at_count must be below history_report_count",
        )
    _validate_latest_status_streaks(report)


def _validate_empty_report(
    report: PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryReport,
) -> None:
    if report.first_history_generated_at is not None:
        raise ValueError("first_history_generated_at must be absent without history")
    if report.latest_history_generated_at is not None:
        raise ValueError("latest_history_generated_at must be absent without history")
    if report.latest_source_report_count is not None:
        raise ValueError("latest_source_report_count must be absent without history")
    if report.latest_action_status is not None:
        raise ValueError("latest_action_status must be absent without history")
    if report.latest_recommended_next_step is not None:
        raise ValueError("latest_recommended_next_step must be absent without history")
    if report.duplicate_generated_at_count != 0:
        raise ValueError("duplicate_generated_at_count must be zero without history")
    if report.consecutive_latest_research_ready_count != 0:
        raise ValueError(
            "consecutive_latest_research_ready_count must be zero without history",
        )
    if report.consecutive_latest_watch_count != 0:
        raise ValueError(
            "consecutive_latest_watch_count must be zero without history",
        )
    if report.consecutive_latest_blocked_count != 0:
        raise ValueError(
            "consecutive_latest_blocked_count must be zero without history",
        )
    if report.latest_total_ready_notional is not None:
        raise ValueError("latest_total_ready_notional must be absent without history")
    if report.latest_ready_notional_delta is not None:
        raise ValueError("latest_ready_notional_delta must be absent without history")
    if report.latest_status_transition_count is not None:
        raise ValueError("latest_status_transition_count must be absent without history")
    if report.latest_reason_code_counts:
        raise ValueError("latest_reason_code_counts must be empty without history")


def _validate_nonempty_report(
    report: PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryReport,
) -> None:
    if report.first_history_generated_at is None:
        raise ValueError("first_history_generated_at is required with history")
    if report.latest_history_generated_at is None:
        raise ValueError("latest_history_generated_at is required with history")
    if report.latest_history_generated_at < report.first_history_generated_at:
        raise ValueError("latest_history_generated_at must not precede first history")
    if report.latest_source_report_count is None:
        raise ValueError("latest_source_report_count is required with history")
    if report.latest_total_ready_notional is None:
        raise ValueError("latest_total_ready_notional is required with history")
    if report.latest_status_transition_count is None:
        raise ValueError("latest_status_transition_count is required with history")
    if report.history_report_count < 2:
        if report.latest_ready_notional_delta is not None:
            raise ValueError(
                "latest_ready_notional_delta must be absent without previous history",
            )
    elif report.latest_ready_notional_delta is None:
        raise ValueError("latest_ready_notional_delta is required with previous history")
    if report.latest_source_report_count == 0:
        if report.latest_action_status is not None:
            raise ValueError(
                "latest_action_status must be absent without source reports",
            )
        if report.latest_recommended_next_step is not None:
            raise ValueError(
                "latest_recommended_next_step must be absent without source reports",
            )
        if report.latest_reason_code_counts:
            raise ValueError(
                "latest_reason_code_counts must be empty without source reports",
            )
    else:
        if report.latest_action_status is None:
            raise ValueError("latest_action_status is required with source reports")
        if report.latest_recommended_next_step is None:
            raise ValueError(
                "latest_recommended_next_step is required with source reports",
            )


def _validate_latest_status_streaks(
    report: PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryReport,
) -> None:
    action_status_counts = dict(report.action_status_counts)
    streaks = (
        (
            "research_ready",
            "consecutive_latest_research_ready_count",
            report.consecutive_latest_research_ready_count,
        ),
        (
            "watch",
            "consecutive_latest_watch_count",
            report.consecutive_latest_watch_count,
        ),
        (
            "blocked",
            "consecutive_latest_blocked_count",
            report.consecutive_latest_blocked_count,
        ),
    )
    for status, field_name, count in streaks:
        if report.latest_action_status == status:
            if count <= 0:
                raise ValueError(
                    f"{field_name} must be positive when latest_action_status is {status}",
                )
        elif count != 0:
            raise ValueError(
                f"{field_name} must be zero unless latest_action_status is {status}",
            )
        if count > action_status_counts[status]:
            raise ValueError(
                f"{field_name} must not exceed {status} action_status_count",
            )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _quantize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    decimal_value = _quantize_optional_decimal(field_name, value)
    if decimal_value is not None and decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _quantize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal or None")
    return _quantize_decimal(field_name, value)


def _quantize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    quantized = decimal_value.quantize(DECIMAL_QUANTUM)
    if decimal_value != quantized:
        raise ValueError(f"{field_name} must use 0.000001 precision")
    return quantized


def _quantize_decimal_result(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value).quantize(DECIMAL_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_optional_action_status(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_action_status(field_name, value)


def _require_action_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTION_STATUSES:
        raise ValueError(f"{field_name} must be research_ready, watch, or blocked")


def _require_optional_queue_next_step(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not str or value not in QUEUE_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a known recommended next step")


def _validate_optional_next_step_pair(
    latest_action_status: str | None,
    latest_recommended_next_step: str | None,
) -> None:
    if latest_action_status is None:
        if latest_recommended_next_step is not None:
            raise ValueError(
                "latest_recommended_next_step requires latest_action_status",
            )
        return
    if latest_recommended_next_step is None:
        raise ValueError("latest_recommended_next_step is required")
    if latest_recommended_next_step != NEXT_STEP_BY_ACTION_STATUS[latest_action_status]:
        raise ValueError("latest_recommended_next_step must match latest_action_status")


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    _require_int(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be a nonnegative integer")


def _require_positive_int(field_name: str, value: Any) -> None:
    _require_nonnegative_int(field_name, value)
    if value == 0:
        raise ValueError(f"{field_name} must be positive")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


__all__ = (
    "PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryConfig",
    "PaperActionGatedStrategyRecommendationQueueHistoryDbHistoryReport",
    "build_paper_action_gated_strategy_recommendation_queue_history_db_history_report",
)
