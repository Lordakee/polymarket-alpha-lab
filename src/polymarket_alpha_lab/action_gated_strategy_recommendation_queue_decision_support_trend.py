"""Pure paper action-gated queue decision-support trend reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterable

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority import (
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk import (
    PaperActionGatedStrategyRecommendationQueueRiskReport,
)


__all__ = (
    "PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReasonCodeRow",
    "PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport",
    "PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary",
    "build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report",
)


ZERO = Decimal("0")
DECIMAL_QUANTUM = Decimal("0.000001")
RISK_STATUSES = ("pass", "watch", "blocked")


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary:
    input_position: int
    generated_at: datetime
    risk_status: str
    risk_recommended_next_step: str
    risk_reason_codes: tuple[str, ...]
    source_queue_count: int
    candidate_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    ready_notional: Decimal
    largest_queue_ready_notional: Decimal
    top_priority_score: Decimal
    average_priority_score: Decimal

    def __post_init__(self) -> None:
        _require_positive_int("input_position", self.input_position)
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_risk_status("risk_status", self.risk_status)
        _require_canonical_string(
            "risk_recommended_next_step",
            self.risk_recommended_next_step,
        )
        object.__setattr__(
            self,
            "risk_reason_codes",
            _normalize_reason_codes(self.risk_reason_codes),
        )
        for field_name in (
            "source_queue_count",
            "candidate_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "ready_notional",
            _quantize_decimal("ready_notional", self.ready_notional),
        )
        object.__setattr__(
            self,
            "largest_queue_ready_notional",
            _quantize_decimal(
                "largest_queue_ready_notional",
                self.largest_queue_ready_notional,
            ),
        )
        object.__setattr__(
            self,
            "top_priority_score",
            _quantize_decimal("top_priority_score", self.top_priority_score),
        )
        object.__setattr__(
            self,
            "average_priority_score",
            _quantize_decimal(
                "average_priority_score",
                self.average_priority_score,
            ),
        )
        if self.candidate_count != self.ready_count + self.watch_count + self.blocked_count:
            raise ValueError("candidate_count must match candidate status counts")


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReasonCodeRow:
    reason_code: str
    total_count: int
    latest_count: int
    snapshot_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        for field_name in ("total_count", "latest_count", "snapshot_count"):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.snapshot_count > self.total_count:
            raise ValueError("snapshot_count must not exceed total_count")
        if self.latest_count > self.total_count:
            raise ValueError("latest_count must not exceed total_count")


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport:
    generated_at: datetime
    source_snapshot_count: int
    first_generated_at: datetime | None
    latest_generated_at: datetime | None
    latest_risk_status: str | None
    risk_status_counts: tuple[tuple[str, int], ...]
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    ready_notional_first: Decimal | None
    ready_notional_latest: Decimal | None
    ready_notional_delta: Decimal | None
    top_priority_score_first: Decimal | None
    top_priority_score_latest: Decimal | None
    top_priority_score_delta: Decimal | None
    average_priority_score_first: Decimal | None
    average_priority_score_latest: Decimal | None
    average_priority_score_delta: Decimal | None
    source_queue_count_first: int | None
    source_queue_count_latest: int | None
    source_queue_count_delta: int | None
    duplicate_generated_at_count: int
    latest_reason_code_counts: tuple[tuple[str, int], ...]
    total_reason_code_counts: tuple[tuple[str, int], ...]
    repeated_reason_code_counts: tuple[tuple[str, int], ...]
    reason_code_rows: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReasonCodeRow,
        ...,
    ]
    source_summaries: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_generated_at",
            _as_optional_utc(self.first_generated_at),
        )
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_optional_utc(self.latest_generated_at),
        )
        _require_nonnegative_int("source_snapshot_count", self.source_snapshot_count)
        if self.latest_risk_status is not None:
            _require_risk_status("latest_risk_status", self.latest_risk_status)
        object.__setattr__(
            self,
            "risk_status_counts",
            _normalize_status_counts(self.risk_status_counts),
        )
        for field_name in (
            "consecutive_latest_watch_count",
            "consecutive_latest_blocked_count",
            "duplicate_generated_at_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "ready_notional_first",
            "ready_notional_latest",
            "ready_notional_delta",
            "top_priority_score_first",
            "top_priority_score_latest",
            "top_priority_score_delta",
            "average_priority_score_first",
            "average_priority_score_latest",
            "average_priority_score_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_optional_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_queue_count_first",
            "source_queue_count_latest",
            "source_queue_count_delta",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _require_int(field_name, value)
        object.__setattr__(
            self,
            "latest_reason_code_counts",
            _normalize_reason_code_counts(self.latest_reason_code_counts),
        )
        object.__setattr__(
            self,
            "total_reason_code_counts",
            _normalize_reason_code_counts(self.total_reason_code_counts),
        )
        object.__setattr__(
            self,
            "repeated_reason_code_counts",
            _normalize_reason_code_counts(self.repeated_reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_code_rows",
            _normalize_reason_code_rows(self.reason_code_rows),
        )
        object.__setattr__(
            self,
            "source_summaries",
            _normalize_source_summaries(self.source_summaries),
        )
        _validate_report_consistency(self)
        _require_hard_flags("trend_report", self)


def build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
    snapshot_pairs: object,
    *,
    generated_at: datetime,
) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport:
    generated_at = _as_utc(generated_at)
    pairs = _normalize_snapshot_pairs(snapshot_pairs)
    summaries = tuple(
        sorted(
            (
                _source_summary_from_pair(
                    priority_report,
                    risk_report,
                    input_position=index,
                )
                for index, (priority_report, risk_report) in enumerate(pairs, start=1)
            ),
            key=lambda summary: (summary.generated_at, summary.input_position),
        ),
    )
    first = summaries[0] if summaries else None
    latest = summaries[-1] if summaries else None
    status_counts = _status_counts(summaries)
    latest_reason_counts = (
        _reason_code_counts(latest.risk_reason_codes)
        if latest is not None
        else ()
    )
    total_reason_counts = _total_reason_code_counts(summaries)

    return PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport(
        generated_at=generated_at,
        source_snapshot_count=len(summaries),
        first_generated_at=first.generated_at if first is not None else None,
        latest_generated_at=latest.generated_at if latest is not None else None,
        latest_risk_status=latest.risk_status if latest is not None else None,
        risk_status_counts=status_counts,
        consecutive_latest_watch_count=_latest_status_streak(summaries, "watch"),
        consecutive_latest_blocked_count=_latest_status_streak(summaries, "blocked"),
        ready_notional_first=first.ready_notional if first is not None else None,
        ready_notional_latest=latest.ready_notional if latest is not None else None,
        ready_notional_delta=_decimal_delta(
            first.ready_notional if first is not None else None,
            latest.ready_notional if latest is not None else None,
        ),
        top_priority_score_first=first.top_priority_score if first is not None else None,
        top_priority_score_latest=(
            latest.top_priority_score
            if latest is not None
            else None
        ),
        top_priority_score_delta=_decimal_delta(
            first.top_priority_score if first is not None else None,
            latest.top_priority_score if latest is not None else None,
        ),
        average_priority_score_first=(
            first.average_priority_score
            if first is not None
            else None
        ),
        average_priority_score_latest=(
            latest.average_priority_score
            if latest is not None
            else None
        ),
        average_priority_score_delta=_decimal_delta(
            first.average_priority_score if first is not None else None,
            latest.average_priority_score if latest is not None else None,
        ),
        source_queue_count_first=(
            first.source_queue_count
            if first is not None
            else None
        ),
        source_queue_count_latest=(
            latest.source_queue_count
            if latest is not None
            else None
        ),
        source_queue_count_delta=_int_delta(
            first.source_queue_count if first is not None else None,
            latest.source_queue_count if latest is not None else None,
        ),
        duplicate_generated_at_count=_duplicate_generated_at_count(summaries),
        latest_reason_code_counts=latest_reason_counts,
        total_reason_code_counts=total_reason_counts,
        repeated_reason_code_counts=_repeated_reason_code_counts(total_reason_counts),
        reason_code_rows=_reason_code_rows(summaries, latest_reason_counts),
        source_summaries=summaries,
    )


def _normalize_snapshot_pairs(
    value: object,
) -> tuple[
    tuple[
        PaperActionGatedStrategyRecommendationQueuePriorityReport,
        PaperActionGatedStrategyRecommendationQueueRiskReport,
    ],
    ...,
]:
    if type(value) not in (list, tuple):
        raise ValueError("snapshot_pairs must be a list or tuple")
    pairs = tuple(value)
    normalized = tuple(_normalize_snapshot_pair(pair) for pair in pairs)
    return normalized


def _normalize_snapshot_pair(
    value: object,
) -> tuple[
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
    PaperActionGatedStrategyRecommendationQueueRiskReport,
]:
    if type(value) is not tuple or len(value) != 2:
        raise ValueError("snapshot_pairs must contain priority/risk report pairs")
    priority_report, risk_report = value
    if type(priority_report) is not PaperActionGatedStrategyRecommendationQueuePriorityReport:
        raise ValueError("snapshot_pairs must contain PriorityReport values")
    if type(risk_report) is not PaperActionGatedStrategyRecommendationQueueRiskReport:
        raise ValueError("snapshot_pairs must contain RiskReport values")
    _validate_priority_hard_flags(priority_report)
    _require_hard_flags("risk_report", risk_report)
    _validate_pair_consistency(priority_report, risk_report)
    return (priority_report, risk_report)


def _source_summary_from_pair(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
    *,
    input_position: int,
) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary:
    return PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary(
        input_position=input_position,
        generated_at=risk_report.generated_at,
        risk_status=risk_report.status,
        risk_recommended_next_step=risk_report.recommended_next_step,
        risk_reason_codes=risk_report.reason_codes,
        source_queue_count=risk_report.source_queue_count,
        candidate_count=risk_report.candidate_count,
        ready_count=risk_report.ready_count,
        watch_count=risk_report.watch_count,
        blocked_count=risk_report.blocked_count,
        ready_notional=risk_report.total_ready_notional,
        largest_queue_ready_notional=risk_report.largest_queue_ready_notional,
        top_priority_score=priority_report.top_research_priority_score,
        average_priority_score=priority_report.average_research_priority_score,
    )


def _validate_pair_consistency(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
) -> None:
    message = "priority_report and risk_report must describe the same source snapshot"
    if _as_utc(priority_report.generated_at) != _as_utc(risk_report.generated_at):
        raise ValueError(message)
    if priority_report.source_report_count != risk_report.source_queue_count:
        raise ValueError(message)
    if priority_report.research_ready_count != risk_report.research_ready_source_count:
        raise ValueError(message)
    if priority_report.watch_count != risk_report.watch_source_count:
        raise ValueError(message)
    if priority_report.blocked_count != risk_report.blocked_source_count:
        raise ValueError(message)
    if priority_report.total_ready_notional != risk_report.total_ready_notional:
        raise ValueError(message)
    if (
        _largest_priority_ready_notional(priority_report)
        != risk_report.largest_queue_ready_notional
    ):
        raise ValueError(message)
    if _priority_source_config_versions(priority_report) != tuple(
        sorted(risk_report.source_config_versions),
    ):
        raise ValueError(message)
    if _sum_priority_rows("candidate_count", priority_report) != risk_report.candidate_count:
        raise ValueError(message)
    if _sum_priority_rows("ready_count", priority_report) != risk_report.ready_count:
        raise ValueError(message)
    if _sum_priority_rows("watch_count", priority_report) != risk_report.watch_count:
        raise ValueError(message)
    if _sum_priority_rows("blocked_count", priority_report) != risk_report.blocked_count:
        raise ValueError(message)


def _priority_source_config_versions(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> tuple[str, ...]:
    return tuple(sorted({row.config_version for row in priority_report.priority_rows}))


def _largest_priority_ready_notional(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> Decimal:
    return _quantize_decimal(
        "largest_queue_ready_notional",
        max(
            (row.total_ready_notional for row in priority_report.priority_rows),
            default=ZERO.quantize(DECIMAL_QUANTUM),
        ),
    )


def _sum_priority_rows(
    field_name: str,
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> int:
    return sum(getattr(row, field_name) for row in priority_report.priority_rows)


def _validate_priority_hard_flags(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> None:
    _require_hard_flags("priority_report", priority_report)
    for row in priority_report.priority_rows:
        _require_hard_flags("priority_row", row)


def _validate_report_consistency(
    report: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport,
) -> None:
    if report.source_snapshot_count != len(report.source_summaries):
        raise ValueError("source_snapshot_count must match source_summaries")
    if report.source_snapshot_count == 0:
        _validate_empty_report(report)
        return
    _validate_source_summary_order(report.source_summaries)

    first = report.source_summaries[0]
    latest = report.source_summaries[-1]
    latest_reason_counts = _reason_code_counts(latest.risk_reason_codes)
    total_reason_counts = _total_reason_code_counts(report.source_summaries)

    if report.first_generated_at != first.generated_at:
        raise ValueError("first_generated_at must match source_summaries")
    if report.latest_generated_at != latest.generated_at:
        raise ValueError("latest_generated_at must match source_summaries")
    if report.latest_risk_status != latest.risk_status:
        raise ValueError("latest_risk_status must match source_summaries")
    if report.risk_status_counts != _status_counts(report.source_summaries):
        raise ValueError("risk_status_counts must match source_summaries")
    if report.consecutive_latest_watch_count != _latest_status_streak(
        report.source_summaries,
        "watch",
    ):
        raise ValueError("consecutive_latest_watch_count must match source_summaries")
    if report.consecutive_latest_blocked_count != _latest_status_streak(
        report.source_summaries,
        "blocked",
    ):
        raise ValueError("consecutive_latest_blocked_count must match source_summaries")
    if report.ready_notional_first != first.ready_notional:
        raise ValueError("ready_notional_first must match source_summaries")
    if report.ready_notional_latest != latest.ready_notional:
        raise ValueError("ready_notional_latest must match source_summaries")
    if report.ready_notional_delta != _decimal_delta(
        first.ready_notional,
        latest.ready_notional,
    ):
        raise ValueError("ready_notional_delta must match source_summaries")
    if report.top_priority_score_first != first.top_priority_score:
        raise ValueError("top_priority_score_first must match source_summaries")
    if report.top_priority_score_latest != latest.top_priority_score:
        raise ValueError("top_priority_score_latest must match source_summaries")
    if report.top_priority_score_delta != _decimal_delta(
        first.top_priority_score,
        latest.top_priority_score,
    ):
        raise ValueError("top_priority_score_delta must match source_summaries")
    if report.average_priority_score_first != first.average_priority_score:
        raise ValueError("average_priority_score_first must match source_summaries")
    if report.average_priority_score_latest != latest.average_priority_score:
        raise ValueError("average_priority_score_latest must match source_summaries")
    if report.average_priority_score_delta != _decimal_delta(
        first.average_priority_score,
        latest.average_priority_score,
    ):
        raise ValueError("average_priority_score_delta must match source_summaries")
    if report.source_queue_count_first != first.source_queue_count:
        raise ValueError("source_queue_count_first must match source_summaries")
    if report.source_queue_count_latest != latest.source_queue_count:
        raise ValueError("source_queue_count_latest must match source_summaries")
    if report.source_queue_count_delta != _int_delta(
        first.source_queue_count,
        latest.source_queue_count,
    ):
        raise ValueError("source_queue_count_delta must match source_summaries")
    if report.duplicate_generated_at_count != _duplicate_generated_at_count(
        report.source_summaries,
    ):
        raise ValueError("duplicate_generated_at_count must match source_summaries")
    if report.latest_reason_code_counts != latest_reason_counts:
        raise ValueError("latest_reason_code_counts must match source_summaries")
    if report.total_reason_code_counts != total_reason_counts:
        raise ValueError("total_reason_code_counts must match source_summaries")
    if report.repeated_reason_code_counts != _repeated_reason_code_counts(
        total_reason_counts,
    ):
        raise ValueError("repeated_reason_code_counts must match source_summaries")
    if report.reason_code_rows != _reason_code_rows(
        report.source_summaries,
        latest_reason_counts,
    ):
        raise ValueError("reason_code_rows must match source_summaries")


def _validate_source_summary_order(
    summaries: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary,
        ...,
    ],
) -> None:
    if summaries != tuple(
        sorted(summaries, key=lambda summary: (summary.generated_at, summary.input_position)),
    ):
        raise ValueError(
            "source_summaries must be sorted by generated_at and input_position",
        )
    input_positions = tuple(summary.input_position for summary in summaries)
    if tuple(sorted(input_positions)) != tuple(range(1, len(summaries) + 1)):
        raise ValueError("input_position values must be unique and contiguous")


def _validate_empty_report(
    report: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport,
) -> None:
    if report.first_generated_at is not None or report.latest_generated_at is not None:
        raise ValueError("generated_at bounds must be absent without snapshots")
    if report.latest_risk_status is not None:
        raise ValueError("latest_risk_status must be absent without snapshots")
    if report.risk_status_counts:
        raise ValueError("risk_status_counts must be empty without snapshots")
    for field_name in (
        "consecutive_latest_watch_count",
        "consecutive_latest_blocked_count",
        "duplicate_generated_at_count",
    ):
        if getattr(report, field_name) != 0:
            raise ValueError(f"{field_name} must be zero without snapshots")
    for field_name in (
        "ready_notional_first",
        "ready_notional_latest",
        "ready_notional_delta",
        "top_priority_score_first",
        "top_priority_score_latest",
        "top_priority_score_delta",
        "average_priority_score_first",
        "average_priority_score_latest",
        "average_priority_score_delta",
        "source_queue_count_first",
        "source_queue_count_latest",
        "source_queue_count_delta",
    ):
        if getattr(report, field_name) is not None:
            raise ValueError(f"{field_name} must be absent without snapshots")
    if report.latest_reason_code_counts:
        raise ValueError("latest_reason_code_counts must be empty without snapshots")
    if report.total_reason_code_counts:
        raise ValueError("total_reason_code_counts must be empty without snapshots")
    if report.repeated_reason_code_counts:
        raise ValueError("repeated_reason_code_counts must be empty without snapshots")
    if report.reason_code_rows:
        raise ValueError("reason_code_rows must be empty without snapshots")


def _status_counts(
    summaries: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary,
        ...,
    ],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for summary in summaries:
        counts[summary.risk_status] = counts.get(summary.risk_status, 0) + 1
    return tuple(
        (status, counts[status])
        for status in RISK_STATUSES
        if counts.get(status, 0) > 0
    )


def _latest_status_streak(
    summaries: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary,
        ...,
    ],
    status: str,
) -> int:
    count = 0
    for summary in reversed(summaries):
        if summary.risk_status != status:
            break
        count += 1
    return count


def _duplicate_generated_at_count(
    summaries: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary,
        ...,
    ],
) -> int:
    counts: dict[datetime, int] = {}
    for summary in summaries:
        counts[summary.generated_at] = counts.get(summary.generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _reason_code_counts(reason_codes: tuple[str, ...]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for reason_code in reason_codes:
        counts[reason_code] = counts.get(reason_code, 0) + 1
    return _sorted_counts(counts)


def _total_reason_code_counts(
    summaries: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary,
        ...,
    ],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for summary in summaries:
        for reason_code in summary.risk_reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return _sorted_counts(counts)


def _repeated_reason_code_counts(
    counts: tuple[tuple[str, int], ...],
) -> tuple[tuple[str, int], ...]:
    return tuple((reason_code, count) for reason_code, count in counts if count > 1)


def _reason_code_rows(
    summaries: tuple[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary,
        ...,
    ],
    latest_counts: tuple[tuple[str, int], ...],
) -> tuple[
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReasonCodeRow,
    ...,
]:
    latest_count_by_code = dict(latest_counts)
    total_counts = _total_reason_code_counts(summaries)
    rows = []
    for reason_code, total_count in total_counts:
        rows.append(
            PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReasonCodeRow(
                reason_code=reason_code,
                total_count=total_count,
                latest_count=latest_count_by_code.get(reason_code, 0),
                snapshot_count=sum(
                    1
                    for summary in summaries
                    if reason_code in set(summary.risk_reason_codes)
                ),
            ),
        )
    return tuple(rows)


def _sorted_counts(counts: dict[str, int]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _decimal_delta(first: Decimal | None, latest: Decimal | None) -> Decimal | None:
    if first is None or latest is None:
        return None
    return _quantize_decimal("delta", latest - first)


def _int_delta(first: int | None, latest: int | None) -> int | None:
    if first is None or latest is None:
        return None
    return latest - first


def _normalize_source_summaries(
    value: Iterable[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary,
    ],
) -> tuple[
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary,
    ...,
]:
    if isinstance(value, (str, bytes)):
        raise ValueError("source_summaries must be an iterable")
    try:
        summaries = tuple(value)
    except TypeError as exc:
        raise ValueError("source_summaries must be an iterable") from exc
    for summary in summaries:
        if (
            type(summary)
            is not PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary
        ):
            raise ValueError("source_summaries must contain trend summary values")
    return tuple(
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSnapshotSummary(
            input_position=summary.input_position,
            generated_at=summary.generated_at,
            risk_status=summary.risk_status,
            risk_recommended_next_step=summary.risk_recommended_next_step,
            risk_reason_codes=summary.risk_reason_codes,
            source_queue_count=summary.source_queue_count,
            candidate_count=summary.candidate_count,
            ready_count=summary.ready_count,
            watch_count=summary.watch_count,
            blocked_count=summary.blocked_count,
            ready_notional=summary.ready_notional,
            largest_queue_ready_notional=summary.largest_queue_ready_notional,
            top_priority_score=summary.top_priority_score,
            average_priority_score=summary.average_priority_score,
        )
        for summary in summaries
    )


def _normalize_reason_code_rows(
    value: Iterable[
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReasonCodeRow,
    ],
) -> tuple[
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReasonCodeRow,
    ...,
]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_rows must be an iterable") from exc
    for row in rows:
        if (
            type(row)
            is not PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReasonCodeRow
        ):
            raise ValueError("reason_code_rows must contain trend reason rows")
    return tuple(
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReasonCodeRow(
            reason_code=row.reason_code,
            total_count=row.total_count,
            latest_count=row.latest_count,
            snapshot_count=row.snapshot_count,
        )
        for row in rows
    )


def _normalize_status_counts(
    value: tuple[tuple[str, int], ...],
) -> tuple[tuple[str, int], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("risk_status_counts must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("risk_status_counts must be an iterable") from exc
    seen: set[str] = set()
    normalized: list[tuple[str, int]] = []
    for item in items:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("risk_status_counts entries must be status/count pairs")
        status, count = item
        _require_risk_status("risk_status_counts status", status)
        _require_positive_int("risk_status_counts count", count)
        if status in seen:
            raise ValueError("risk_status_counts must not contain duplicate statuses")
        seen.add(status)
        normalized.append((status, count))
    return tuple(
        (status, count)
        for status in RISK_STATUSES
        for item_status, count in normalized
        if item_status == status
    )


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not items:
        raise ValueError("reason_codes must not be empty")
    for item in items:
        _require_canonical_string("reason_codes", item)
    return items


def _normalize_reason_code_counts(
    value: tuple[tuple[str, int], ...],
) -> tuple[tuple[str, int], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    counts: dict[str, int] = {}
    for item in items:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts entries must be reason/count pairs")
        reason_code, count = item
        _require_canonical_string("reason_code", reason_code)
        _require_nonnegative_int("reason_code count", count)
        if count > 0:
            counts[reason_code] = counts.get(reason_code, 0) + count
    return _sorted_counts(counts)


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    return None if value is None else _as_utc(value)


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(DECIMAL_QUANTUM)


def _quantize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _quantize_decimal(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_risk_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RISK_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")
