"""Pure trend reducer over allocation proposal DB-history health snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
    PaperAutonomousAllocationProposalDbHistoryHealthReport,
)

DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_TREND_CONFIG_VERSION = (
    "paper-autonomous-allocation-proposal-db-history-health-trend-v0"
)
HEALTH_STATUSES = ("pass", "watch", "blocked")
DECIMAL_QUANTUM = Decimal("0.000001")

__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_TREND_CONFIG_VERSION",
    "PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig",
    "PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow",
    "PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary",
    "PaperAutonomousAllocationProposalDbHistoryHealthTrendReport",
    "build_paper_autonomous_allocation_proposal_db_history_health_trend_report",
)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig:
    config_version: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_TREND_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig:
            raise TypeError(
                "PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig:
            raise ValueError(
                "config must be exactly "
                "PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow:
    reason_code: str
    total_count: int
    latest_count: int
    snapshot_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow:
            raise TypeError(
                "PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow
        ):
            raise ValueError(
                "reason code row must be exactly "
                "PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow",
            )
        _require_canonical_string("reason_code", self.reason_code)
        for field_name in ("total_count", "latest_count", "snapshot_count"):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.latest_count > self.total_count:
            raise ValueError("latest_count must not exceed total_count")
        if self.snapshot_count > self.total_count:
            raise ValueError("snapshot_count must not exceed total_count")
        _validate_hard_flags("reason code row", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary:
    input_position: int
    generated_at: datetime
    health_status: str
    history_report_count: int
    pass_report_count: int
    watch_report_count: int
    blocked_report_count: int
    latest_allocated_count: int | None
    latest_total_allocated_paper_notional: Decimal | None
    latest_source_age_seconds: int | None
    max_source_age_seconds: int | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary:
            raise TypeError(
                "PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary
        ):
            raise ValueError(
                "snapshot summary must be exactly "
                "PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary",
            )
        _require_positive_int("input_position", self.input_position)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_health_status("health_status", self.health_status)
        for field_name in (
            "history_report_count",
            "pass_report_count",
            "watch_report_count",
            "blocked_report_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_optional_nonnegative_int(
            "latest_allocated_count",
            self.latest_allocated_count,
        )
        object.__setattr__(
            self,
            "latest_total_allocated_paper_notional",
            _quantize_optional_decimal(
                "latest_total_allocated_paper_notional",
                self.latest_total_allocated_paper_notional,
            ),
        )
        _require_optional_nonnegative_int(
            "latest_source_age_seconds",
            self.latest_source_age_seconds,
        )
        _require_optional_nonnegative_int(
            "max_source_age_seconds",
            self.max_source_age_seconds,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.history_report_count != (
            self.pass_report_count + self.watch_report_count + self.blocked_report_count
        ):
            raise ValueError("history_report_count must equal status counts")
        if self.latest_source_age_seconds is not None and self.max_source_age_seconds is None:
            raise ValueError("max_source_age_seconds is required with latest_source_age_seconds")
        if (
            self.latest_source_age_seconds is not None
            and self.max_source_age_seconds is not None
            and self.latest_source_age_seconds > self.max_source_age_seconds
        ):
            raise ValueError("latest_source_age_seconds must not exceed max_source_age_seconds")
        _validate_hard_flags("snapshot summary", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
    generated_at: datetime
    config_version: str
    source_health_report_count: int
    first_generated_at: datetime | None
    latest_generated_at: datetime | None
    latest_health_status: str | None
    health_status_counts: tuple[tuple[str, int], ...]
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    duplicate_generated_at_count: int
    history_report_count_first: int | None
    history_report_count_latest: int | None
    history_report_count_delta: int | None
    pass_report_count_first: int | None
    pass_report_count_latest: int | None
    pass_report_count_delta: int | None
    watch_report_count_first: int | None
    watch_report_count_latest: int | None
    watch_report_count_delta: int | None
    blocked_report_count_first: int | None
    blocked_report_count_latest: int | None
    blocked_report_count_delta: int | None
    latest_allocated_count_first: int | None
    latest_allocated_count_latest: int | None
    latest_allocated_count_delta: int | None
    latest_total_allocated_paper_notional_first: Decimal | None
    latest_total_allocated_paper_notional_latest: Decimal | None
    latest_total_allocated_paper_notional_delta: Decimal | None
    latest_source_age_seconds_first: int | None
    latest_source_age_seconds_latest: int | None
    latest_source_age_seconds_delta: int | None
    max_source_age_seconds_first: int | None
    max_source_age_seconds_latest: int | None
    max_source_age_seconds_delta: int | None
    latest_reason_code_counts: tuple[tuple[str, int], ...]
    total_reason_code_counts: tuple[tuple[str, int], ...]
    repeated_reason_code_counts: tuple[tuple[str, int], ...]
    reason_code_rows: tuple[
        PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow,
        ...,
    ]
    source_summaries: tuple[
        PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
            raise TypeError(
                "PaperAutonomousAllocationProposalDbHistoryHealthTrendReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
            raise ValueError(
                "trend report must be exactly "
                "PaperAutonomousAllocationProposalDbHistoryHealthTrendReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "source_health_report_count",
            self.source_health_report_count,
        )
        object.__setattr__(
            self,
            "first_generated_at",
            _as_optional_utc("first_generated_at", self.first_generated_at),
        )
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_optional_utc("latest_generated_at", self.latest_generated_at),
        )
        if self.latest_health_status is not None:
            _require_health_status("latest_health_status", self.latest_health_status)
        object.__setattr__(
            self,
            "health_status_counts",
            _normalize_status_counts(self.health_status_counts),
        )
        for field_name in (
            "consecutive_latest_watch_count",
            "consecutive_latest_blocked_count",
            "duplicate_generated_at_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "history_report_count_first",
            "history_report_count_latest",
            "history_report_count_delta",
            "pass_report_count_first",
            "pass_report_count_latest",
            "pass_report_count_delta",
            "watch_report_count_first",
            "watch_report_count_latest",
            "watch_report_count_delta",
            "blocked_report_count_first",
            "blocked_report_count_latest",
            "blocked_report_count_delta",
            "latest_allocated_count_first",
            "latest_allocated_count_latest",
            "latest_allocated_count_delta",
            "latest_source_age_seconds_first",
            "latest_source_age_seconds_latest",
            "latest_source_age_seconds_delta",
            "max_source_age_seconds_first",
            "max_source_age_seconds_latest",
            "max_source_age_seconds_delta",
        ):
            _require_optional_int(field_name, getattr(self, field_name))
        for field_name in (
            "latest_total_allocated_paper_notional_first",
            "latest_total_allocated_paper_notional_latest",
            "latest_total_allocated_paper_notional_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_optional_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_reason_code_counts",
            _normalize_reason_code_counts(
                "latest_reason_code_counts",
                self.latest_reason_code_counts,
            ),
        )
        object.__setattr__(
            self,
            "total_reason_code_counts",
            _normalize_reason_code_counts(
                "total_reason_code_counts",
                self.total_reason_code_counts,
            ),
        )
        object.__setattr__(
            self,
            "repeated_reason_code_counts",
            _normalize_reason_code_counts(
                "repeated_reason_code_counts",
                self.repeated_reason_code_counts,
            ),
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
        _validate_hard_flags("trend report", self)


def build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
    health_reports: object,
    *,
    config: PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
    if type(config) is not PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig:
        raise ValueError(
            "config must be a PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _validate_hard_flags("config", config)

    reports = _normalize_health_reports(health_reports)
    summaries = tuple(
        sorted(
            (
                _summary_from_report(report, input_position=index)
                for index, report in enumerate(reports, start=1)
            ),
            key=lambda summary: (summary.generated_at, summary.input_position),
        ),
    )
    first = summaries[0] if summaries else None
    latest = summaries[-1] if summaries else None
    latest_reason_code_counts = (
        _reason_code_counts(latest.reason_codes) if latest is not None else ()
    )
    total_reason_code_counts = _reason_code_counts_across_summaries(summaries)
    repeated_reason_code_counts = tuple(
        row for row in total_reason_code_counts if row[1] > 1
    )
    reason_code_rows = _reason_code_rows(
        latest_reason_code_counts=latest_reason_code_counts,
        total_reason_code_counts=total_reason_code_counts,
        summaries=summaries,
    )

    return PaperAutonomousAllocationProposalDbHistoryHealthTrendReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_health_report_count=len(summaries),
        first_generated_at=first.generated_at if first is not None else None,
        latest_generated_at=latest.generated_at if latest is not None else None,
        latest_health_status=latest.health_status if latest is not None else None,
        health_status_counts=_status_counts(summaries),
        consecutive_latest_watch_count=_latest_status_streak(summaries, "watch"),
        consecutive_latest_blocked_count=_latest_status_streak(summaries, "blocked"),
        duplicate_generated_at_count=_duplicate_generated_at_count(summaries),
        history_report_count_first=(
            first.history_report_count if first is not None else None
        ),
        history_report_count_latest=(
            latest.history_report_count if latest is not None else None
        ),
        history_report_count_delta=_int_delta(
            first.history_report_count if first is not None else None,
            latest.history_report_count if latest is not None else None,
        ),
        pass_report_count_first=(first.pass_report_count if first is not None else None),
        pass_report_count_latest=(
            latest.pass_report_count if latest is not None else None
        ),
        pass_report_count_delta=_int_delta(
            first.pass_report_count if first is not None else None,
            latest.pass_report_count if latest is not None else None,
        ),
        watch_report_count_first=(
            first.watch_report_count if first is not None else None
        ),
        watch_report_count_latest=(
            latest.watch_report_count if latest is not None else None
        ),
        watch_report_count_delta=_int_delta(
            first.watch_report_count if first is not None else None,
            latest.watch_report_count if latest is not None else None,
        ),
        blocked_report_count_first=(
            first.blocked_report_count if first is not None else None
        ),
        blocked_report_count_latest=(
            latest.blocked_report_count if latest is not None else None
        ),
        blocked_report_count_delta=_int_delta(
            first.blocked_report_count if first is not None else None,
            latest.blocked_report_count if latest is not None else None,
        ),
        latest_allocated_count_first=(
            first.latest_allocated_count if first is not None else None
        ),
        latest_allocated_count_latest=(
            latest.latest_allocated_count if latest is not None else None
        ),
        latest_allocated_count_delta=_int_delta(
            first.latest_allocated_count if first is not None else None,
            latest.latest_allocated_count if latest is not None else None,
        ),
        latest_total_allocated_paper_notional_first=(
            first.latest_total_allocated_paper_notional if first is not None else None
        ),
        latest_total_allocated_paper_notional_latest=(
            latest.latest_total_allocated_paper_notional if latest is not None else None
        ),
        latest_total_allocated_paper_notional_delta=_decimal_delta(
            first.latest_total_allocated_paper_notional if first is not None else None,
            latest.latest_total_allocated_paper_notional if latest is not None else None,
        ),
        latest_source_age_seconds_first=(
            first.latest_source_age_seconds if first is not None else None
        ),
        latest_source_age_seconds_latest=(
            latest.latest_source_age_seconds if latest is not None else None
        ),
        latest_source_age_seconds_delta=_int_delta(
            first.latest_source_age_seconds if first is not None else None,
            latest.latest_source_age_seconds if latest is not None else None,
        ),
        max_source_age_seconds_first=(
            first.max_source_age_seconds if first is not None else None
        ),
        max_source_age_seconds_latest=(
            latest.max_source_age_seconds if latest is not None else None
        ),
        max_source_age_seconds_delta=_int_delta(
            first.max_source_age_seconds if first is not None else None,
            latest.max_source_age_seconds if latest is not None else None,
        ),
        latest_reason_code_counts=latest_reason_code_counts,
        total_reason_code_counts=total_reason_code_counts,
        repeated_reason_code_counts=repeated_reason_code_counts,
        reason_code_rows=reason_code_rows,
        source_summaries=summaries,
    )


def _summary_from_report(
    report: PaperAutonomousAllocationProposalDbHistoryHealthReport,
    *,
    input_position: int,
) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary:
    return PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary(
        input_position=input_position,
        generated_at=report.generated_at,
        health_status=report.health_status,
        history_report_count=report.history_report_count,
        pass_report_count=report.pass_report_count,
        watch_report_count=report.watch_report_count,
        blocked_report_count=report.blocked_report_count,
        latest_allocated_count=report.latest_allocated_count,
        latest_total_allocated_paper_notional=report.latest_total_allocated_paper_notional,
        latest_source_age_seconds=report.latest_source_age_seconds,
        max_source_age_seconds=report.max_source_age_seconds,
        reason_codes=report.reason_codes,
    )


def _normalize_health_reports(
    value: object,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryHealthReport, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("health_reports must be a list or tuple")
    reports = tuple(value)
    for report in reports:
        if type(report) is not PaperAutonomousAllocationProposalDbHistoryHealthReport:
            raise ValueError(
                "health_reports must contain "
                "PaperAutonomousAllocationProposalDbHistoryHealthReport values",
            )
        _validate_health_report_value(report)
    return reports


def _validate_health_report_value(
    report: PaperAutonomousAllocationProposalDbHistoryHealthReport,
) -> None:
    _validate_hard_flags("health report", report)
    _as_utc("source generated_at", report.generated_at)
    _require_canonical_string("source config_version", report.config_version)
    _require_health_status("source health_status", report.health_status)
    _require_canonical_string(
        "source recommended_next_step",
        report.recommended_next_step,
    )
    for field_name in (
        "history_report_count",
        "pass_report_count",
        "watch_report_count",
        "blocked_report_count",
        "duplicate_latest_report_generated_at_count",
    ):
        _require_nonnegative_int(field_name, getattr(report, field_name))
    if report.latest_history_status is not None:
        _require_health_status("source latest_history_status", report.latest_history_status)
    if report.latest_proposal_status is not None:
        _require_health_status(
            "source latest_proposal_status",
            report.latest_proposal_status,
        )
    _require_optional_nonnegative_int(
        "source latest_allocated_count",
        report.latest_allocated_count,
    )
    _quantize_optional_decimal(
        "source latest_total_allocated_paper_notional",
        report.latest_total_allocated_paper_notional,
    )
    _require_optional_nonnegative_int(
        "source latest_source_age_seconds",
        report.latest_source_age_seconds,
    )
    _require_optional_nonnegative_int(
        "source max_source_age_seconds",
        report.max_source_age_seconds,
    )
    _normalize_reason_codes("source reason_codes", report.reason_codes)


def _status_counts(
    summaries: tuple[PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary, ...],
) -> tuple[tuple[str, int], ...]:
    counts = {status: 0 for status in HEALTH_STATUSES}
    for summary in summaries:
        counts[summary.health_status] += 1
    return tuple((status, counts[status]) for status in HEALTH_STATUSES)


def _latest_status_streak(
    summaries: tuple[PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary, ...],
    status: str,
) -> int:
    count = 0
    for summary in reversed(summaries):
        if summary.health_status != status:
            break
        count += 1
    return count


def _duplicate_generated_at_count(
    summaries: tuple[PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary, ...],
) -> int:
    counts: dict[datetime, int] = {}
    for summary in summaries:
        counts[summary.generated_at] = counts.get(summary.generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for reason_code in reason_codes:
        counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(sorted(counts.items()))


def _reason_code_counts_across_summaries(
    summaries: tuple[PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary, ...],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for summary in summaries:
        for reason_code in set(summary.reason_codes):
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        ),
    )


def _reason_code_rows(
    *,
    latest_reason_code_counts: tuple[tuple[str, int], ...],
    total_reason_code_counts: tuple[tuple[str, int], ...],
    summaries: tuple[PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary, ...],
) -> tuple[PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow, ...]:
    latest_map = dict(latest_reason_code_counts)
    total_map = dict(total_reason_code_counts)
    snapshot_counts: dict[str, int] = {}
    for summary in summaries:
        for reason_code in set(summary.reason_codes):
            snapshot_counts[reason_code] = snapshot_counts.get(reason_code, 0) + 1
    return tuple(
        PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow(
            reason_code=reason_code,
            total_count=total_count,
            latest_count=latest_map.get(reason_code, 0),
            snapshot_count=snapshot_counts.get(reason_code, 0),
        )
        for reason_code, total_count in total_reason_code_counts
    )


def _snapshot_reason_code_counts(
    summaries: tuple[PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary, ...],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for summary in summaries:
        for reason_code in set(summary.reason_codes):
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(counts.items())


def _normalize_status_counts(
    value: object,
) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError("health_status_counts must be a tuple")
    rows: list[tuple[str, int]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("health_status_counts must contain (status, count) tuples")
        status, count = item
        _require_health_status("health_status_counts status", status)
        _require_nonnegative_int("health_status_counts count", count)
        if status in seen:
            raise ValueError("health_status_counts must be unique")
        seen.add(status)
        rows.append((status, count))
    expected = tuple(status for status in HEALTH_STATUSES)
    if tuple(status for status, _ in rows) != expected:
        raise ValueError("health_status_counts must follow pass/watch/blocked order")
    return tuple(rows)


def _normalize_reason_code_counts(
    field_name: str,
    value: object,
) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    rows: list[tuple[str, int]] = []
    seen: set[str] = set()
    previous_key: tuple[int, str] | None = None
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError(f"{field_name} must contain (reason_code, count) tuples")
        reason_code, count = item
        _require_canonical_string(field_name, reason_code)
        _require_positive_int(field_name, count)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        key = (-count, reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError(f"{field_name} must be deterministic")
        previous_key = key
        seen.add(reason_code)
        rows.append((reason_code, count))
    return tuple(rows)


def _normalize_reason_code_rows(
    value: object,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_rows must be a tuple")
    rows = tuple(value)
    previous_key: tuple[int, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if (
            type(row)
            is not PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow
        ):
            raise ValueError("reason_code_rows must contain exact reason code rows")
        if row.reason_code in seen:
            raise ValueError("reason_code_rows must be unique")
        key = (-row.total_count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_rows must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_source_summaries(
    value: object,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary, ...]:
    if type(value) is not tuple:
        raise ValueError("source_summaries must be a tuple")
    summaries = tuple(value)
    previous_key: tuple[datetime, int] | None = None
    seen_positions: set[int] = set()
    for summary in summaries:
        if (
            type(summary)
            is not PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary
        ):
            raise ValueError("source_summaries must contain exact snapshot summaries")
        key = (summary.generated_at, summary.input_position)
        if previous_key is not None and previous_key > key:
            raise ValueError("source_summaries must be ordered")
        if summary.input_position in seen_positions:
            raise ValueError("source_summaries input_position must be unique")
        previous_key = key
        seen_positions.add(summary.input_position)
    return summaries


def _validate_report_consistency(
    report: PaperAutonomousAllocationProposalDbHistoryHealthTrendReport,
) -> None:
    if report.source_health_report_count == 0:
        _validate_empty_report(report)
    else:
        _validate_nonempty_report(report)
    if report.source_health_report_count != sum(
        count for _, count in report.health_status_counts
    ):
        raise ValueError("health_status_counts must match source_health_report_count")
    if report.duplicate_generated_at_count >= max(report.source_health_report_count, 1):
        raise ValueError("duplicate_generated_at_count must be below source count")
    if len(report.source_summaries) != report.source_health_report_count:
        raise ValueError("source_summaries must match source_health_report_count")
    snapshot_count_map = dict(_snapshot_reason_code_counts(report.source_summaries))
    if report.reason_code_rows != tuple(
        PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow(
            reason_code=reason_code,
            total_count=total_count,
            latest_count=dict(report.latest_reason_code_counts).get(reason_code, 0),
            snapshot_count=snapshot_count_map.get(reason_code, 0),
        )
        for reason_code, total_count in report.total_reason_code_counts
    ):
        raise ValueError("reason_code_rows must align with reason code counts")
    if report.repeated_reason_code_counts != tuple(
        row for row in report.total_reason_code_counts if row[1] > 1
    ):
        raise ValueError("repeated_reason_code_counts must derive from total_reason_code_counts")


def _validate_empty_report(
    report: PaperAutonomousAllocationProposalDbHistoryHealthTrendReport,
) -> None:
    if report.first_generated_at is not None:
        raise ValueError("first_generated_at must be absent without source reports")
    if report.latest_generated_at is not None:
        raise ValueError("latest_generated_at must be absent without source reports")
    if report.latest_health_status is not None:
        raise ValueError("latest_health_status must be absent without source reports")
    if report.health_status_counts != (
        ("pass", 0),
        ("watch", 0),
        ("blocked", 0),
    ):
        raise ValueError("health_status_counts must be zeroed without source reports")
    for field_name in (
        "history_report_count_first",
        "history_report_count_latest",
        "history_report_count_delta",
        "pass_report_count_first",
        "pass_report_count_latest",
        "pass_report_count_delta",
        "watch_report_count_first",
        "watch_report_count_latest",
        "watch_report_count_delta",
        "blocked_report_count_first",
        "blocked_report_count_latest",
        "blocked_report_count_delta",
        "latest_allocated_count_first",
        "latest_allocated_count_latest",
        "latest_allocated_count_delta",
        "latest_total_allocated_paper_notional_first",
        "latest_total_allocated_paper_notional_latest",
        "latest_total_allocated_paper_notional_delta",
        "latest_source_age_seconds_first",
        "latest_source_age_seconds_latest",
        "latest_source_age_seconds_delta",
        "max_source_age_seconds_first",
        "max_source_age_seconds_latest",
        "max_source_age_seconds_delta",
    ):
        if getattr(report, field_name) is not None:
            raise ValueError(f"{field_name} must be absent without source reports")
    if report.latest_reason_code_counts:
        raise ValueError("latest_reason_code_counts must be empty without source reports")
    if report.total_reason_code_counts:
        raise ValueError("total_reason_code_counts must be empty without source reports")
    if report.repeated_reason_code_counts:
        raise ValueError("repeated_reason_code_counts must be empty without source reports")
    if report.reason_code_rows:
        raise ValueError("reason_code_rows must be empty without source reports")
    if report.source_summaries:
        raise ValueError("source_summaries must be empty without source reports")


def _validate_nonempty_report(
    report: PaperAutonomousAllocationProposalDbHistoryHealthTrendReport,
) -> None:
    if report.first_generated_at is None:
        raise ValueError("first_generated_at is required with source reports")
    if report.latest_generated_at is None:
        raise ValueError("latest_generated_at is required with source reports")
    if report.first_generated_at > report.latest_generated_at:
        raise ValueError("first_generated_at must not be after latest_generated_at")
    if report.latest_health_status is None:
        raise ValueError("latest_health_status is required with source reports")
    first = report.source_summaries[0]
    latest = report.source_summaries[-1]
    if report.first_generated_at != first.generated_at:
        raise ValueError("first_generated_at must match first source summary")
    if report.latest_generated_at != latest.generated_at:
        raise ValueError("latest_generated_at must match latest source summary")
    if report.latest_health_status != latest.health_status:
        raise ValueError("latest_health_status must match latest source summary")
    _validate_scalar_pair(
        "history_report_count",
        first.history_report_count,
        latest.history_report_count,
        report.history_report_count_first,
        report.history_report_count_latest,
        report.history_report_count_delta,
    )
    _validate_scalar_pair(
        "pass_report_count",
        first.pass_report_count,
        latest.pass_report_count,
        report.pass_report_count_first,
        report.pass_report_count_latest,
        report.pass_report_count_delta,
    )
    _validate_scalar_pair(
        "watch_report_count",
        first.watch_report_count,
        latest.watch_report_count,
        report.watch_report_count_first,
        report.watch_report_count_latest,
        report.watch_report_count_delta,
    )
    _validate_scalar_pair(
        "blocked_report_count",
        first.blocked_report_count,
        latest.blocked_report_count,
        report.blocked_report_count_first,
        report.blocked_report_count_latest,
        report.blocked_report_count_delta,
    )
    _validate_optional_scalar_pair(
        "latest_allocated_count",
        first.latest_allocated_count,
        latest.latest_allocated_count,
        report.latest_allocated_count_first,
        report.latest_allocated_count_latest,
        report.latest_allocated_count_delta,
    )
    _validate_optional_decimal_pair(
        "latest_total_allocated_paper_notional",
        first.latest_total_allocated_paper_notional,
        latest.latest_total_allocated_paper_notional,
        report.latest_total_allocated_paper_notional_first,
        report.latest_total_allocated_paper_notional_latest,
        report.latest_total_allocated_paper_notional_delta,
    )
    _validate_optional_scalar_pair(
        "latest_source_age_seconds",
        first.latest_source_age_seconds,
        latest.latest_source_age_seconds,
        report.latest_source_age_seconds_first,
        report.latest_source_age_seconds_latest,
        report.latest_source_age_seconds_delta,
    )
    _validate_optional_scalar_pair(
        "max_source_age_seconds",
        first.max_source_age_seconds,
        latest.max_source_age_seconds,
        report.max_source_age_seconds_first,
        report.max_source_age_seconds_latest,
        report.max_source_age_seconds_delta,
    )


def _validate_scalar_pair(
    label: str,
    first_value: int,
    latest_value: int,
    report_first: int | None,
    report_latest: int | None,
    report_delta: int | None,
) -> None:
    if report_first != first_value:
        raise ValueError(f"{label}_first must match first source summary")
    if report_latest != latest_value:
        raise ValueError(f"{label}_latest must match latest source summary")
    if report_delta != latest_value - first_value:
        raise ValueError(f"{label}_delta must match latest minus first")


def _validate_optional_scalar_pair(
    label: str,
    first_value: int | None,
    latest_value: int | None,
    report_first: int | None,
    report_latest: int | None,
    report_delta: int | None,
) -> None:
    if report_first != first_value:
        raise ValueError(f"{label}_first must match first source summary")
    if report_latest != latest_value:
        raise ValueError(f"{label}_latest must match latest source summary")
    if report_delta != _int_delta(first_value, latest_value):
        raise ValueError(f"{label}_delta must match latest minus first")


def _validate_optional_decimal_pair(
    label: str,
    first_value: Decimal | None,
    latest_value: Decimal | None,
    report_first: Decimal | None,
    report_latest: Decimal | None,
    report_delta: Decimal | None,
) -> None:
    if report_first != _quantize_optional_decimal(f"{label}_first", first_value):
        raise ValueError(f"{label}_first must match first source summary")
    if report_latest != _quantize_optional_decimal(f"{label}_latest", latest_value):
        raise ValueError(f"{label}_latest must match latest source summary")
    if report_delta != _decimal_delta(first_value, latest_value):
        raise ValueError(f"{label}_delta must match latest minus first")


def _int_delta(first: int | None, latest: int | None) -> int | None:
    if first is None or latest is None:
        return None
    return latest - first


def _decimal_delta(first: Decimal | None, latest: Decimal | None) -> Decimal | None:
    if first is None or latest is None:
        return None
    return _quantize_decimal_value(latest - first)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be a positive int")


def _require_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")


def _require_optional_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_int(field_name, value)


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _quantize_decimal_value(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("decimal value must be a Decimal")
    if not value.is_finite():
        raise ValueError("decimal value must be finite")
    return value.quantize(DECIMAL_QUANTUM)


def _quantize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(DECIMAL_QUANTUM)


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} is required")
    previous: str | None = None
    seen: set[str] = set()
    for code in codes:
        _require_canonical_string(field_name, code)
        if code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > code:
            raise ValueError(f"{field_name} must be sorted")
        previous = code
        seen.add(code)
    return codes


def _validate_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")
