"""Pure trend reducer over project screening rank stability DB-history health."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.paper_project_screening_rank_stability import (
    STABILITY_STATUSES as RANK_STABILITY_STATUSES,
)
from polymarket_alpha_lab.paper_project_screening_rank_stability_db_history_health import (
    HEALTH_STATUSES,
    NEXT_STEP_BY_STATUS as SOURCE_NEXT_STEP_BY_STATUS,
    PaperProjectScreeningRankStabilityDbHistoryHealthReport,
)


DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_HISTORY_HEALTH_TREND_CONFIG_VERSION = (
    "paper-project-screening-rank-stability-db-history-health-trend-v0"
)

__all__ = (
    "DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_HISTORY_HEALTH_TREND_CONFIG_VERSION",
    "PaperProjectScreeningRankStabilityDbHistoryHealthTrendConfig",
    "PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow",
    "PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary",
    "PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport",
    "build_paper_project_screening_rank_stability_db_history_health_trend_report",
)


@dataclass(frozen=True)
class PaperProjectScreeningRankStabilityDbHistoryHealthTrendConfig:
    config_version: str = (
        DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_HISTORY_HEALTH_TREND_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendConfig:
            raise TypeError(
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendConfig:
            raise ValueError(
                "config must be exactly "
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow:
    reason_code: str
    total_count: int
    latest_count: int
    snapshot_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow:
            raise TypeError(
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow:
            raise ValueError(
                "reason code row must be exactly "
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow",
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
class PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary:
    input_position: int
    generated_at: datetime
    health_status: str
    rank_stability_report_count: int
    stable_rank_stability_report_count: int
    watch_rank_stability_report_count: int
    blocked_rank_stability_report_count: int
    latest_rank_stability_status: str | None
    latest_candidate_count: int | None
    latest_stable_ready_count: int | None
    latest_unstable_ready_count: int | None
    latest_source_generated_at: datetime | None
    latest_source_age_seconds: int | None
    max_source_age_seconds: int | None
    duplicate_latest_generated_at_count: int
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary:
            raise TypeError(
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary
        ):
            raise ValueError(
                "snapshot summary must be exactly "
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary",
            )
        _require_positive_int("input_position", self.input_position)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_health_status("health_status", self.health_status)
        for field_name in (
            "rank_stability_report_count",
            "stable_rank_stability_report_count",
            "watch_rank_stability_report_count",
            "blocked_rank_stability_report_count",
            "duplicate_latest_generated_at_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.latest_rank_stability_status is not None:
            _require_rank_stability_status(
                "latest_rank_stability_status",
                self.latest_rank_stability_status,
            )
        for field_name in (
            "latest_candidate_count",
            "latest_stable_ready_count",
            "latest_unstable_ready_count",
            "latest_source_age_seconds",
            "max_source_age_seconds",
        ):
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_source_generated_at",
            _as_optional_utc(
                "latest_source_generated_at",
                self.latest_source_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_snapshot_summary(self)
        _validate_hard_flags("snapshot summary", self)


@dataclass(frozen=True)
class PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport:
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
    rank_stability_report_count_first: int | None
    rank_stability_report_count_latest: int | None
    rank_stability_report_count_delta: int | None
    stable_rank_stability_report_count_first: int | None
    stable_rank_stability_report_count_latest: int | None
    stable_rank_stability_report_count_delta: int | None
    watch_rank_stability_report_count_first: int | None
    watch_rank_stability_report_count_latest: int | None
    watch_rank_stability_report_count_delta: int | None
    blocked_rank_stability_report_count_first: int | None
    blocked_rank_stability_report_count_latest: int | None
    blocked_rank_stability_report_count_delta: int | None
    latest_candidate_count_first: int | None
    latest_candidate_count_latest: int | None
    latest_candidate_count_delta: int | None
    latest_stable_ready_count_first: int | None
    latest_stable_ready_count_latest: int | None
    latest_stable_ready_count_delta: int | None
    latest_unstable_ready_count_first: int | None
    latest_unstable_ready_count_latest: int | None
    latest_unstable_ready_count_delta: int | None
    latest_source_generated_at_first: datetime | None
    latest_source_generated_at_latest: datetime | None
    latest_source_generated_at_delta_seconds: int | None
    latest_source_age_seconds_first: int | None
    latest_source_age_seconds_latest: int | None
    latest_source_age_seconds_delta: int | None
    max_source_age_seconds_first: int | None
    max_source_age_seconds_latest: int | None
    max_source_age_seconds_delta: int | None
    duplicate_latest_generated_at_count_first: int | None
    duplicate_latest_generated_at_count_latest: int | None
    duplicate_latest_generated_at_count_delta: int | None
    latest_reason_code_counts: tuple[tuple[str, int], ...]
    total_reason_code_counts: tuple[tuple[str, int], ...]
    repeated_reason_code_counts: tuple[tuple[str, int], ...]
    reason_code_rows: tuple[
        PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow,
        ...,
    ]
    source_summaries: tuple[
        PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport:
            raise TypeError(
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport:
            raise ValueError(
                "trend report must be exactly "
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport",
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
            "rank_stability_report_count_first",
            "rank_stability_report_count_latest",
            "stable_rank_stability_report_count_first",
            "stable_rank_stability_report_count_latest",
            "watch_rank_stability_report_count_first",
            "watch_rank_stability_report_count_latest",
            "blocked_rank_stability_report_count_first",
            "blocked_rank_stability_report_count_latest",
            "latest_candidate_count_first",
            "latest_candidate_count_latest",
            "latest_stable_ready_count_first",
            "latest_stable_ready_count_latest",
            "latest_unstable_ready_count_first",
            "latest_unstable_ready_count_latest",
            "latest_source_age_seconds_first",
            "latest_source_age_seconds_latest",
            "max_source_age_seconds_first",
            "max_source_age_seconds_latest",
            "duplicate_latest_generated_at_count_first",
            "duplicate_latest_generated_at_count_latest",
        ):
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "rank_stability_report_count_delta",
            "stable_rank_stability_report_count_delta",
            "watch_rank_stability_report_count_delta",
            "blocked_rank_stability_report_count_delta",
            "latest_candidate_count_delta",
            "latest_stable_ready_count_delta",
            "latest_unstable_ready_count_delta",
            "latest_source_generated_at_delta_seconds",
            "latest_source_age_seconds_delta",
            "max_source_age_seconds_delta",
            "duplicate_latest_generated_at_count_delta",
        ):
            _require_optional_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_source_generated_at_first",
            _as_optional_utc(
                "latest_source_generated_at_first",
                self.latest_source_generated_at_first,
            ),
        )
        object.__setattr__(
            self,
            "latest_source_generated_at_latest",
            _as_optional_utc(
                "latest_source_generated_at_latest",
                self.latest_source_generated_at_latest,
            ),
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


def build_paper_project_screening_rank_stability_db_history_health_trend_report(
    health_reports: object,
    *,
    config: PaperProjectScreeningRankStabilityDbHistoryHealthTrendConfig,
    generated_at: datetime,
) -> PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport:
    if type(config) is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendConfig:
        raise ValueError(
            "config must be a "
            "PaperProjectScreeningRankStabilityDbHistoryHealthTrendConfig",
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

    return PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport(
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
        rank_stability_report_count_first=(
            first.rank_stability_report_count if first is not None else None
        ),
        rank_stability_report_count_latest=(
            latest.rank_stability_report_count if latest is not None else None
        ),
        rank_stability_report_count_delta=_int_delta(
            first.rank_stability_report_count if first is not None else None,
            latest.rank_stability_report_count if latest is not None else None,
        ),
        stable_rank_stability_report_count_first=(
            first.stable_rank_stability_report_count if first is not None else None
        ),
        stable_rank_stability_report_count_latest=(
            latest.stable_rank_stability_report_count if latest is not None else None
        ),
        stable_rank_stability_report_count_delta=_int_delta(
            first.stable_rank_stability_report_count if first is not None else None,
            latest.stable_rank_stability_report_count if latest is not None else None,
        ),
        watch_rank_stability_report_count_first=(
            first.watch_rank_stability_report_count if first is not None else None
        ),
        watch_rank_stability_report_count_latest=(
            latest.watch_rank_stability_report_count if latest is not None else None
        ),
        watch_rank_stability_report_count_delta=_int_delta(
            first.watch_rank_stability_report_count if first is not None else None,
            latest.watch_rank_stability_report_count if latest is not None else None,
        ),
        blocked_rank_stability_report_count_first=(
            first.blocked_rank_stability_report_count if first is not None else None
        ),
        blocked_rank_stability_report_count_latest=(
            latest.blocked_rank_stability_report_count if latest is not None else None
        ),
        blocked_rank_stability_report_count_delta=_int_delta(
            first.blocked_rank_stability_report_count if first is not None else None,
            latest.blocked_rank_stability_report_count if latest is not None else None,
        ),
        latest_candidate_count_first=(
            first.latest_candidate_count if first is not None else None
        ),
        latest_candidate_count_latest=(
            latest.latest_candidate_count if latest is not None else None
        ),
        latest_candidate_count_delta=_int_delta(
            first.latest_candidate_count if first is not None else None,
            latest.latest_candidate_count if latest is not None else None,
        ),
        latest_stable_ready_count_first=(
            first.latest_stable_ready_count if first is not None else None
        ),
        latest_stable_ready_count_latest=(
            latest.latest_stable_ready_count if latest is not None else None
        ),
        latest_stable_ready_count_delta=_int_delta(
            first.latest_stable_ready_count if first is not None else None,
            latest.latest_stable_ready_count if latest is not None else None,
        ),
        latest_unstable_ready_count_first=(
            first.latest_unstable_ready_count if first is not None else None
        ),
        latest_unstable_ready_count_latest=(
            latest.latest_unstable_ready_count if latest is not None else None
        ),
        latest_unstable_ready_count_delta=_int_delta(
            first.latest_unstable_ready_count if first is not None else None,
            latest.latest_unstable_ready_count if latest is not None else None,
        ),
        latest_source_generated_at_first=(
            first.latest_source_generated_at if first is not None else None
        ),
        latest_source_generated_at_latest=(
            latest.latest_source_generated_at if latest is not None else None
        ),
        latest_source_generated_at_delta_seconds=_datetime_delta_seconds(
            first.latest_source_generated_at if first is not None else None,
            latest.latest_source_generated_at if latest is not None else None,
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
        duplicate_latest_generated_at_count_first=(
            first.duplicate_latest_generated_at_count if first is not None else None
        ),
        duplicate_latest_generated_at_count_latest=(
            latest.duplicate_latest_generated_at_count if latest is not None else None
        ),
        duplicate_latest_generated_at_count_delta=_int_delta(
            first.duplicate_latest_generated_at_count if first is not None else None,
            latest.duplicate_latest_generated_at_count if latest is not None else None,
        ),
        latest_reason_code_counts=latest_reason_code_counts,
        total_reason_code_counts=total_reason_code_counts,
        repeated_reason_code_counts=repeated_reason_code_counts,
        reason_code_rows=reason_code_rows,
        source_summaries=summaries,
    )


def _summary_from_report(
    report: PaperProjectScreeningRankStabilityDbHistoryHealthReport,
    *,
    input_position: int,
) -> PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary:
    return PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary(
        input_position=input_position,
        generated_at=report.generated_at,
        health_status=report.health_status,
        rank_stability_report_count=report.rank_stability_report_count,
        stable_rank_stability_report_count=report.stable_rank_stability_report_count,
        watch_rank_stability_report_count=report.watch_rank_stability_report_count,
        blocked_rank_stability_report_count=report.blocked_rank_stability_report_count,
        latest_rank_stability_status=report.latest_rank_stability_status,
        latest_candidate_count=report.latest_candidate_count,
        latest_stable_ready_count=report.latest_stable_ready_count,
        latest_unstable_ready_count=report.latest_unstable_ready_count,
        latest_source_generated_at=report.latest_source_generated_at,
        latest_source_age_seconds=report.latest_source_age_seconds,
        max_source_age_seconds=report.max_source_age_seconds,
        duplicate_latest_generated_at_count=report.duplicate_latest_generated_at_count,
        reason_codes=report.reason_codes,
    )


def _normalize_health_reports(
    value: object,
) -> tuple[PaperProjectScreeningRankStabilityDbHistoryHealthReport, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("health_reports must be a list or tuple")
    reports = tuple(value)
    for report in reports:
        if type(report) is not PaperProjectScreeningRankStabilityDbHistoryHealthReport:
            raise ValueError(
                "health_reports must contain "
                "PaperProjectScreeningRankStabilityDbHistoryHealthReport values",
            )
        _validate_health_report_value(report)
    return reports


def _validate_health_report_value(
    report: PaperProjectScreeningRankStabilityDbHistoryHealthReport,
) -> None:
    _validate_hard_flags("health report", report)
    _as_utc("source generated_at", report.generated_at)
    _require_canonical_string("source config_version", report.config_version)
    _require_health_status("source health_status", report.health_status)
    _require_canonical_string(
        "source recommended_next_step",
        report.recommended_next_step,
    )
    if report.recommended_next_step != SOURCE_NEXT_STEP_BY_STATUS[report.health_status]:
        raise ValueError("source recommended_next_step must match health_status")
    for field_name in (
        "rank_stability_report_count",
        "stable_rank_stability_report_count",
        "watch_rank_stability_report_count",
        "blocked_rank_stability_report_count",
        "duplicate_latest_generated_at_count",
    ):
        _require_nonnegative_int(f"source {field_name}", getattr(report, field_name))
    if report.latest_rank_stability_status is not None:
        _require_rank_stability_status(
            "source latest_rank_stability_status",
            report.latest_rank_stability_status,
        )
    for field_name in (
        "latest_candidate_count",
        "latest_stable_ready_count",
        "latest_unstable_ready_count",
        "latest_source_age_seconds",
        "max_source_age_seconds",
    ):
        _require_optional_nonnegative_int(
            f"source {field_name}",
            getattr(report, field_name),
        )
    _as_optional_utc(
        "source latest_source_generated_at",
        report.latest_source_generated_at,
    )
    _normalize_reason_codes("source reason_codes", report.reason_codes)


def _status_counts(
    summaries: tuple[
        PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary,
        ...,
    ],
) -> tuple[tuple[str, int], ...]:
    counts = {status: 0 for status in HEALTH_STATUSES}
    for summary in summaries:
        counts[summary.health_status] += 1
    return tuple((status, counts[status]) for status in HEALTH_STATUSES)


def _latest_status_streak(
    summaries: tuple[
        PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary,
        ...,
    ],
    status: str,
) -> int:
    count = 0
    for summary in reversed(summaries):
        if summary.health_status != status:
            break
        count += 1
    return count


def _duplicate_generated_at_count(
    summaries: tuple[
        PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary,
        ...,
    ],
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
    summaries: tuple[
        PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary,
        ...,
    ],
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
    summaries: tuple[
        PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary,
        ...,
    ],
) -> tuple[PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow, ...]:
    latest_map = dict(latest_reason_code_counts)
    snapshot_counts: dict[str, int] = {}
    for summary in summaries:
        for reason_code in set(summary.reason_codes):
            snapshot_counts[reason_code] = snapshot_counts.get(reason_code, 0) + 1
    return tuple(
        PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow(
            reason_code=reason_code,
            total_count=total_count,
            latest_count=latest_map.get(reason_code, 0),
            snapshot_count=snapshot_counts.get(reason_code, 0),
        )
        for reason_code, total_count in total_reason_code_counts
    )


def _normalize_status_counts(value: object) -> tuple[tuple[str, int], ...]:
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
) -> tuple[PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_rows must be a tuple")
    rows = tuple(value)
    previous_key: tuple[int, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow:
            raise ValueError("reason_code_rows must contain exact reason rows")
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
) -> tuple[PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary, ...]:
    if type(value) is not tuple:
        raise ValueError("source_summaries must be a tuple")
    summaries = tuple(value)
    previous_key: tuple[datetime, int] | None = None
    for summary in summaries:
        if (
            type(summary)
            is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary
        ):
            raise ValueError("source_summaries must contain exact snapshot summaries")
        key = (summary.generated_at, summary.input_position)
        if previous_key is not None and previous_key > key:
            raise ValueError("source_summaries must be chronological")
        previous_key = key
    return summaries


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} is required")
    seen: set[str] = set()
    previous: str | None = None
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > reason_code:
            raise ValueError(f"{field_name} must be sorted")
        previous = reason_code
        seen.add(reason_code)
    return reason_codes


def _validate_snapshot_summary(
    summary: PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary,
) -> None:
    if summary.rank_stability_report_count != (
        summary.stable_rank_stability_report_count
        + summary.watch_rank_stability_report_count
        + summary.blocked_rank_stability_report_count
    ):
        raise ValueError("rank_stability_report_count must equal status counts")
    if summary.rank_stability_report_count == 0:
        for field_name in (
            "latest_rank_stability_status",
            "latest_candidate_count",
            "latest_stable_ready_count",
            "latest_unstable_ready_count",
            "latest_source_generated_at",
            "latest_source_age_seconds",
            "max_source_age_seconds",
        ):
            if getattr(summary, field_name) is not None:
                raise ValueError(f"{field_name} must be absent without sources")
        if summary.duplicate_latest_generated_at_count != 0:
            raise ValueError(
                "duplicate_latest_generated_at_count must be zero without sources",
            )
    elif summary.latest_rank_stability_status is None:
        raise ValueError("latest_rank_stability_status is required with sources")
    if (
        summary.latest_stable_ready_count is not None
        and summary.latest_unstable_ready_count is not None
        and summary.latest_candidate_count is not None
        and (
            summary.latest_stable_ready_count + summary.latest_unstable_ready_count
            > summary.latest_candidate_count
        )
    ):
        raise ValueError("latest_candidate_count must cover latest ready counts")


def _validate_report_consistency(
    report: PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport,
) -> None:
    if report.source_health_report_count != len(report.source_summaries):
        raise ValueError("source_health_report_count must match source_summaries")
    if sum(count for _, count in report.health_status_counts) != report.source_health_report_count:
        raise ValueError("health_status_counts must sum to source_health_report_count")
    if report.source_health_report_count == 0:
        _validate_empty_report(report)
        return
    first = report.source_summaries[0]
    latest = report.source_summaries[-1]
    if report.first_generated_at != first.generated_at:
        raise ValueError("first_generated_at must match first summary")
    if report.latest_generated_at != latest.generated_at:
        raise ValueError("latest_generated_at must match latest summary")
    if report.latest_health_status != latest.health_status:
        raise ValueError("latest_health_status must match latest summary")
    expected_status_counts = _status_counts(report.source_summaries)
    if report.health_status_counts != expected_status_counts:
        raise ValueError("health_status_counts must match summaries")
    if report.consecutive_latest_watch_count != _latest_status_streak(
        report.source_summaries,
        "watch",
    ):
        raise ValueError("consecutive_latest_watch_count must match summaries")
    if report.consecutive_latest_blocked_count != _latest_status_streak(
        report.source_summaries,
        "blocked",
    ):
        raise ValueError("consecutive_latest_blocked_count must match summaries")
    if report.duplicate_generated_at_count != _duplicate_generated_at_count(
        report.source_summaries,
    ):
        raise ValueError("duplicate_generated_at_count must match summaries")
    _validate_metric_pair(
        "rank_stability_report_count",
        first.rank_stability_report_count,
        latest.rank_stability_report_count,
        report.rank_stability_report_count_first,
        report.rank_stability_report_count_latest,
        report.rank_stability_report_count_delta,
    )
    _validate_metric_pair(
        "stable_rank_stability_report_count",
        first.stable_rank_stability_report_count,
        latest.stable_rank_stability_report_count,
        report.stable_rank_stability_report_count_first,
        report.stable_rank_stability_report_count_latest,
        report.stable_rank_stability_report_count_delta,
    )
    _validate_metric_pair(
        "watch_rank_stability_report_count",
        first.watch_rank_stability_report_count,
        latest.watch_rank_stability_report_count,
        report.watch_rank_stability_report_count_first,
        report.watch_rank_stability_report_count_latest,
        report.watch_rank_stability_report_count_delta,
    )
    _validate_metric_pair(
        "blocked_rank_stability_report_count",
        first.blocked_rank_stability_report_count,
        latest.blocked_rank_stability_report_count,
        report.blocked_rank_stability_report_count_first,
        report.blocked_rank_stability_report_count_latest,
        report.blocked_rank_stability_report_count_delta,
    )
    _validate_metric_pair(
        "latest_candidate_count",
        first.latest_candidate_count,
        latest.latest_candidate_count,
        report.latest_candidate_count_first,
        report.latest_candidate_count_latest,
        report.latest_candidate_count_delta,
    )
    _validate_metric_pair(
        "latest_stable_ready_count",
        first.latest_stable_ready_count,
        latest.latest_stable_ready_count,
        report.latest_stable_ready_count_first,
        report.latest_stable_ready_count_latest,
        report.latest_stable_ready_count_delta,
    )
    _validate_metric_pair(
        "latest_unstable_ready_count",
        first.latest_unstable_ready_count,
        latest.latest_unstable_ready_count,
        report.latest_unstable_ready_count_first,
        report.latest_unstable_ready_count_latest,
        report.latest_unstable_ready_count_delta,
    )
    _validate_datetime_metric_pair(
        "latest_source_generated_at",
        first.latest_source_generated_at,
        latest.latest_source_generated_at,
        report.latest_source_generated_at_first,
        report.latest_source_generated_at_latest,
        report.latest_source_generated_at_delta_seconds,
    )
    _validate_metric_pair(
        "latest_source_age_seconds",
        first.latest_source_age_seconds,
        latest.latest_source_age_seconds,
        report.latest_source_age_seconds_first,
        report.latest_source_age_seconds_latest,
        report.latest_source_age_seconds_delta,
    )
    _validate_metric_pair(
        "max_source_age_seconds",
        first.max_source_age_seconds,
        latest.max_source_age_seconds,
        report.max_source_age_seconds_first,
        report.max_source_age_seconds_latest,
        report.max_source_age_seconds_delta,
    )
    _validate_metric_pair(
        "duplicate_latest_generated_at_count",
        first.duplicate_latest_generated_at_count,
        latest.duplicate_latest_generated_at_count,
        report.duplicate_latest_generated_at_count_first,
        report.duplicate_latest_generated_at_count_latest,
        report.duplicate_latest_generated_at_count_delta,
    )
    if report.latest_reason_code_counts != _reason_code_counts(latest.reason_codes):
        raise ValueError("latest_reason_code_counts must match latest summary")
    if report.total_reason_code_counts != _reason_code_counts_across_summaries(
        report.source_summaries,
    ):
        raise ValueError("total_reason_code_counts must match summaries")
    if report.repeated_reason_code_counts != tuple(
        row for row in report.total_reason_code_counts if row[1] > 1
    ):
        raise ValueError("repeated_reason_code_counts must match totals")
    if tuple(row.reason_code for row in report.reason_code_rows) != tuple(
        reason_code for reason_code, _ in report.total_reason_code_counts
    ):
        raise ValueError("reason_code_rows must match total_reason_code_counts")


def _validate_empty_report(
    report: PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport,
) -> None:
    absent_fields = (
        "first_generated_at",
        "latest_generated_at",
        "latest_health_status",
        "rank_stability_report_count_first",
        "rank_stability_report_count_latest",
        "rank_stability_report_count_delta",
        "stable_rank_stability_report_count_first",
        "stable_rank_stability_report_count_latest",
        "stable_rank_stability_report_count_delta",
        "watch_rank_stability_report_count_first",
        "watch_rank_stability_report_count_latest",
        "watch_rank_stability_report_count_delta",
        "blocked_rank_stability_report_count_first",
        "blocked_rank_stability_report_count_latest",
        "blocked_rank_stability_report_count_delta",
        "latest_candidate_count_first",
        "latest_candidate_count_latest",
        "latest_candidate_count_delta",
        "latest_stable_ready_count_first",
        "latest_stable_ready_count_latest",
        "latest_stable_ready_count_delta",
        "latest_unstable_ready_count_first",
        "latest_unstable_ready_count_latest",
        "latest_unstable_ready_count_delta",
        "latest_source_generated_at_first",
        "latest_source_generated_at_latest",
        "latest_source_generated_at_delta_seconds",
        "latest_source_age_seconds_first",
        "latest_source_age_seconds_latest",
        "latest_source_age_seconds_delta",
        "max_source_age_seconds_first",
        "max_source_age_seconds_latest",
        "max_source_age_seconds_delta",
        "duplicate_latest_generated_at_count_first",
        "duplicate_latest_generated_at_count_latest",
        "duplicate_latest_generated_at_count_delta",
    )
    for field_name in absent_fields:
        if getattr(report, field_name) is not None:
            raise ValueError(f"{field_name} must be absent without source reports")
    if report.health_status_counts != (("pass", 0), ("watch", 0), ("blocked", 0)):
        raise ValueError("health_status_counts must be zero without source reports")
    for field_name in (
        "consecutive_latest_watch_count",
        "consecutive_latest_blocked_count",
        "duplicate_generated_at_count",
    ):
        if getattr(report, field_name) != 0:
            raise ValueError(f"{field_name} must be zero without source reports")
    if report.latest_reason_code_counts:
        raise ValueError("latest_reason_code_counts must be empty without sources")
    if report.total_reason_code_counts:
        raise ValueError("total_reason_code_counts must be empty without sources")
    if report.repeated_reason_code_counts:
        raise ValueError("repeated_reason_code_counts must be empty without sources")
    if report.reason_code_rows:
        raise ValueError("reason_code_rows must be empty without sources")


def _validate_metric_pair(
    field_name: str,
    expected_first: int | None,
    expected_latest: int | None,
    actual_first: int | None,
    actual_latest: int | None,
    actual_delta: int | None,
) -> None:
    if actual_first != expected_first:
        raise ValueError(f"{field_name}_first must match first summary")
    if actual_latest != expected_latest:
        raise ValueError(f"{field_name}_latest must match latest summary")
    if actual_delta != _int_delta(expected_first, expected_latest):
        raise ValueError(f"{field_name}_delta must match first/latest summaries")


def _validate_datetime_metric_pair(
    field_name: str,
    expected_first: datetime | None,
    expected_latest: datetime | None,
    actual_first: datetime | None,
    actual_latest: datetime | None,
    actual_delta: int | None,
) -> None:
    if actual_first != expected_first:
        raise ValueError(f"{field_name}_first must match first summary")
    if actual_latest != expected_latest:
        raise ValueError(f"{field_name}_latest must match latest summary")
    if actual_delta != _datetime_delta_seconds(expected_first, expected_latest):
        raise ValueError(f"{field_name}_delta_seconds must match first/latest summaries")


def _int_delta(first: int | None, latest: int | None) -> int | None:
    if first is None or latest is None:
        return None
    return latest - first


def _datetime_delta_seconds(first: datetime | None, latest: datetime | None) -> int | None:
    if first is None or latest is None:
        return None
    return int((_as_utc("latest", latest) - _as_utc("first", first)).total_seconds())


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


def _require_rank_stability_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RANK_STABILITY_STATUSES:
        raise ValueError(f"{field_name} must be stable, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


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


def _validate_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")
