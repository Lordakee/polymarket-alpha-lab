"""Pure paper-only health reducer for project screening rank stability history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.paper_project_screening_rank_stability import (
    STABILITY_STATUSES as RANK_STABILITY_STATUSES,
    PaperProjectScreeningRankStabilityReport,
)


DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_HISTORY_HEALTH_CONFIG_VERSION = (
    "paper-project-screening-rank-stability-db-history-health-v0"
)
HEALTH_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_project_screening_rank_stability_review",
    "watch": "throttle_paper_project_screening_rank_stability_review",
    "blocked": "block_paper_project_screening_rank_stability_review",
}
PASS_REASON_CODE = "paper_project_screening_rank_stability_db_history_health_passed"
BLOCKED_REASON_CODES = frozenset(
    (
        "insufficient_paper_project_screening_rank_stability_samples",
        "latest_paper_project_screening_rank_stability_blocked",
        "blocked_paper_project_screening_rank_stability_count_threshold_exceeded",
        "missing_latest_paper_project_screening_rank_stability_source_timestamp",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "latest_paper_project_screening_rank_stability_watch",
        "watch_paper_project_screening_rank_stability_count_threshold_exceeded",
        "low_paper_project_screening_rank_stability_stable_ready_count",
        "unstable_paper_project_screening_rank_stability_ready_candidates_present",
        "stale_paper_project_screening_rank_stability_source_history",
        "duplicate_latest_paper_project_screening_rank_stability_source_generated_at_threshold_exceeded",
    ),
)
HEALTH_REASON_CODES = BLOCKED_REASON_CODES | WATCH_REASON_CODES | frozenset(
    (PASS_REASON_CODE,),
)

__all__ = (
    "DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_HISTORY_HEALTH_CONFIG_VERSION",
    "HEALTH_STATUSES",
    "NEXT_STEP_BY_STATUS",
    "PASS_REASON_CODE",
    "BLOCKED_REASON_CODES",
    "WATCH_REASON_CODES",
    "HEALTH_REASON_CODES",
    "PaperProjectScreeningRankStabilityDbHistoryHealthConfig",
    "PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount",
    "PaperProjectScreeningRankStabilityDbHistoryHealthReport",
    "build_paper_project_screening_rank_stability_db_history_health_report",
)


@dataclass(frozen=True)
class PaperProjectScreeningRankStabilityDbHistoryHealthConfig:
    config_version: str = (
        DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_HISTORY_HEALTH_CONFIG_VERSION
    )
    min_rank_stability_report_count: int = 3
    min_latest_stable_ready_count: int = 1
    max_unstable_ready_count: int = 0
    max_watch_rank_stability_report_count: int = 0
    max_blocked_rank_stability_report_count: int = 0
    max_duplicate_latest_generated_at_count: int = 0
    max_latest_age_seconds: int = 86_400
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperProjectScreeningRankStabilityDbHistoryHealthConfig:
            raise TypeError(
                "PaperProjectScreeningRankStabilityDbHistoryHealthConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperProjectScreeningRankStabilityDbHistoryHealthConfig:
            raise ValueError(
                "config must be exactly "
                "PaperProjectScreeningRankStabilityDbHistoryHealthConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int(
            "min_rank_stability_report_count",
            self.min_rank_stability_report_count,
        )
        for field_name in (
            "min_latest_stable_ready_count",
            "max_unstable_ready_count",
            "max_watch_rank_stability_report_count",
            "max_blocked_rank_stability_report_count",
            "max_duplicate_latest_generated_at_count",
            "max_latest_age_seconds",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount:
            raise TypeError(
                "PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperProjectScreeningRankStabilityDbHistoryHealthReport:
    generated_at: datetime
    config_version: str
    health_status: str
    recommended_next_step: str
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
    reason_code_counts: tuple[
        PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperProjectScreeningRankStabilityDbHistoryHealthReport:
            raise TypeError(
                "PaperProjectScreeningRankStabilityDbHistoryHealthReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperProjectScreeningRankStabilityDbHistoryHealthReport:
            raise ValueError(
                "health report must be exactly "
                "PaperProjectScreeningRankStabilityDbHistoryHealthReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_health_status("health_status", self.health_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
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
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=HEALTH_REASON_CODES,
            ),
        )
        _validate_health_report(self)
        _validate_hard_flags("health report", self)


def build_paper_project_screening_rank_stability_db_history_health_report(
    rank_stability_reports: object,
    *,
    config: PaperProjectScreeningRankStabilityDbHistoryHealthConfig,
    generated_at: datetime,
) -> PaperProjectScreeningRankStabilityDbHistoryHealthReport:
    if type(config) is not PaperProjectScreeningRankStabilityDbHistoryHealthConfig:
        raise ValueError(
            "config must be exactly "
            "PaperProjectScreeningRankStabilityDbHistoryHealthConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _validate_hard_flags("config", config)

    reports = _normalize_rank_stability_reports(rank_stability_reports)
    latest_report = _latest_source_report(reports)
    stable_rank_stability_report_count = _status_count(reports, "stable")
    watch_rank_stability_report_count = _status_count(reports, "watch")
    blocked_rank_stability_report_count = _status_count(reports, "blocked")
    missing_latest_timestamp = any(
        report.latest_generated_at is None for report in reports
    )
    duplicate_latest_generated_at_count = _duplicate_latest_generated_at_count(reports)
    latest_source_age_seconds, max_source_age_seconds = _source_age_seconds(
        generated_at_utc,
        reports,
    )
    latest_source_generated_at = (
        None
        if missing_latest_timestamp or latest_report is None
        else latest_report.latest_generated_at
    )
    reason_codes = _health_reason_codes(
        reports=reports,
        latest_report=latest_report,
        watch_rank_stability_report_count=watch_rank_stability_report_count,
        blocked_rank_stability_report_count=blocked_rank_stability_report_count,
        missing_latest_timestamp=missing_latest_timestamp,
        duplicate_latest_generated_at_count=duplicate_latest_generated_at_count,
        latest_source_age_seconds=latest_source_age_seconds,
        config=config,
    )
    health_status = _health_status(reason_codes)

    return PaperProjectScreeningRankStabilityDbHistoryHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        health_status=health_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[health_status],
        rank_stability_report_count=len(reports),
        stable_rank_stability_report_count=stable_rank_stability_report_count,
        watch_rank_stability_report_count=watch_rank_stability_report_count,
        blocked_rank_stability_report_count=blocked_rank_stability_report_count,
        latest_rank_stability_status=(
            latest_report.stability_status if latest_report is not None else None
        ),
        latest_candidate_count=(
            latest_report.candidate_count if latest_report is not None else None
        ),
        latest_stable_ready_count=(
            latest_report.stable_ready_count if latest_report is not None else None
        ),
        latest_unstable_ready_count=(
            latest_report.unstable_ready_count if latest_report is not None else None
        ),
        latest_source_generated_at=latest_source_generated_at,
        latest_source_age_seconds=latest_source_age_seconds,
        max_source_age_seconds=max_source_age_seconds,
        duplicate_latest_generated_at_count=duplicate_latest_generated_at_count,
        reason_code_counts=_reason_code_counts(reports),
        reason_codes=reason_codes,
    )


def _normalize_rank_stability_reports(
    value: object,
) -> tuple[PaperProjectScreeningRankStabilityReport, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rank_stability_reports must be a list or tuple")
    reports = tuple(value)
    for report in reports:
        if type(report) is not PaperProjectScreeningRankStabilityReport:
            raise ValueError(
                "rank_stability_reports must contain "
                "PaperProjectScreeningRankStabilityReport values",
            )
        _validate_rank_stability_report(report)
    return reports


def _validate_rank_stability_report(
    report: PaperProjectScreeningRankStabilityReport,
) -> None:
    _validate_hard_flags("rank stability report", report)
    _as_utc("source generated_at", report.generated_at)
    _require_canonical_string("source config_version", report.config_version)
    _require_rank_stability_status("source stability_status", report.stability_status)
    for field_name in (
        "source_report_count",
        "candidate_count",
        "stable_count",
        "watch_count",
        "blocked_count",
        "stable_ready_count",
        "unstable_ready_count",
        "scoring_side_changed_count",
        "source_status_changed_count",
        "screening_status_changed_count",
        "research_bucket_changed_count",
    ):
        _require_nonnegative_int(f"source {field_name}", getattr(report, field_name))
    _as_optional_utc("source latest_generated_at", report.latest_generated_at)
    if report.top_stable_market_slug is not None:
        _require_canonical_string(
            "source top_stable_market_slug",
            report.top_stable_market_slug,
        )
    _normalize_reason_codes("source reason_codes", report.reason_codes)


def _health_reason_codes(
    *,
    reports: tuple[PaperProjectScreeningRankStabilityReport, ...],
    latest_report: PaperProjectScreeningRankStabilityReport | None,
    watch_rank_stability_report_count: int,
    blocked_rank_stability_report_count: int,
    missing_latest_timestamp: bool,
    duplicate_latest_generated_at_count: int,
    latest_source_age_seconds: int | None,
    config: PaperProjectScreeningRankStabilityDbHistoryHealthConfig,
) -> tuple[str, ...]:
    blocked_reasons: list[str] = []
    watch_reasons: list[str] = []

    if len(reports) < config.min_rank_stability_report_count:
        blocked_reasons.append(
            "insufficient_paper_project_screening_rank_stability_samples",
        )
    if latest_report is not None and latest_report.stability_status == "blocked":
        blocked_reasons.append("latest_paper_project_screening_rank_stability_blocked")
    if (
        blocked_rank_stability_report_count
        > config.max_blocked_rank_stability_report_count
    ):
        blocked_reasons.append(
            "blocked_paper_project_screening_rank_stability_count_threshold_exceeded",
        )
    if missing_latest_timestamp:
        blocked_reasons.append(
            "missing_latest_paper_project_screening_rank_stability_source_timestamp",
        )

    if latest_report is not None and latest_report.stability_status == "watch":
        watch_reasons.append("latest_paper_project_screening_rank_stability_watch")
    if watch_rank_stability_report_count > config.max_watch_rank_stability_report_count:
        watch_reasons.append(
            "watch_paper_project_screening_rank_stability_count_threshold_exceeded",
        )
    if (
        latest_report is not None
        and latest_report.stable_ready_count < config.min_latest_stable_ready_count
    ):
        watch_reasons.append(
            "low_paper_project_screening_rank_stability_stable_ready_count",
        )
    if (
        latest_report is not None
        and latest_report.unstable_ready_count > config.max_unstable_ready_count
    ):
        watch_reasons.append(
            "unstable_paper_project_screening_rank_stability_ready_candidates_present",
        )
    if (
        latest_source_age_seconds is not None
        and latest_source_age_seconds > config.max_latest_age_seconds
    ):
        watch_reasons.append(
            "stale_paper_project_screening_rank_stability_source_history",
        )
    if (
        duplicate_latest_generated_at_count
        > config.max_duplicate_latest_generated_at_count
    ):
        watch_reasons.append(
            "duplicate_latest_paper_project_screening_rank_stability_source_generated_at_threshold_exceeded",
        )

    reason_codes = blocked_reasons + watch_reasons
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(sorted(set(reason_codes)))


def _health_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _latest_source_report(
    reports: tuple[PaperProjectScreeningRankStabilityReport, ...],
) -> PaperProjectScreeningRankStabilityReport | None:
    if not reports:
        return None
    return max(
        enumerate(reports),
        key=lambda item: (*_latest_source_sort_key(item[1]), item[0]),
    )[1]


def _latest_source_sort_key(
    report: PaperProjectScreeningRankStabilityReport,
) -> tuple[int, datetime, datetime]:
    latest_generated_at = _as_optional_utc(
        "source latest_generated_at",
        report.latest_generated_at,
    )
    report_generated_at = _as_utc("source generated_at", report.generated_at)
    if latest_generated_at is None:
        return (0, report_generated_at, report_generated_at)
    return (1, latest_generated_at, report_generated_at)


def _source_age_seconds(
    generated_at: datetime,
    reports: tuple[PaperProjectScreeningRankStabilityReport, ...],
) -> tuple[int | None, int | None]:
    if not reports:
        return (None, None)
    latest_generated_values = tuple(
        _as_optional_utc("source latest_generated_at", report.latest_generated_at)
        for report in reports
    )
    if any(value is None for value in latest_generated_values):
        return (None, None)
    ages = tuple(
        _age_seconds(generated_at, latest_generated_at)
        for latest_generated_at in latest_generated_values
        if latest_generated_at is not None
    )
    return (min(ages), max(ages))


def _age_seconds(generated_at: datetime, source_generated_at: datetime) -> int:
    source_generated_at_utc = _as_utc("source latest_generated_at", source_generated_at)
    age_seconds = int((generated_at - source_generated_at_utc).total_seconds())
    if age_seconds < 0:
        raise ValueError("source latest_generated_at must not be future dated")
    return age_seconds


def _duplicate_latest_generated_at_count(
    reports: tuple[PaperProjectScreeningRankStabilityReport, ...],
) -> int:
    counts: dict[datetime, int] = {}
    for report in reports:
        latest_generated_at = _as_optional_utc(
            "source latest_generated_at",
            report.latest_generated_at,
        )
        if latest_generated_at is None:
            continue
        counts[latest_generated_at] = counts.get(latest_generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _reason_code_counts(
    reports: tuple[PaperProjectScreeningRankStabilityReport, ...],
) -> tuple[PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for report in reports:
        for reason_code in set(report.reason_codes):
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount(
            reason_code,
            report_count,
        )
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _status_count(
    reports: tuple[PaperProjectScreeningRankStabilityReport, ...],
    stability_status: str,
) -> int:
    return sum(1 for report in reports if report.stability_status == stability_status)


def _validate_health_report(
    report: PaperProjectScreeningRankStabilityDbHistoryHealthReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.health_status]:
        raise ValueError("recommended_next_step must match health_status")
    if report.rank_stability_report_count != (
        report.stable_rank_stability_report_count
        + report.watch_rank_stability_report_count
        + report.blocked_rank_stability_report_count
    ):
        raise ValueError("rank_stability_report_count must equal status counts")
    if report.rank_stability_report_count == 0:
        _validate_empty_health_report(report)
    else:
        _validate_nonempty_health_report(report)
    _validate_health_reason_codes(report)
    for row in report.reason_code_counts:
        if row.report_count > report.rank_stability_report_count:
            raise ValueError("reason_code_counts report_count must not exceed source count")


def _validate_empty_health_report(
    report: PaperProjectScreeningRankStabilityDbHistoryHealthReport,
) -> None:
    if report.health_status != "blocked":
        raise ValueError("health_status must be blocked without rank stability reports")
    if report.recommended_next_step != "block_paper_project_screening_rank_stability_review":
        raise ValueError("recommended_next_step must block without rank stability reports")
    if report.reason_codes != (
        "insufficient_paper_project_screening_rank_stability_samples",
    ):
        raise ValueError(
            "reason_codes must only contain the insufficient samples reason "
            "without rank stability reports",
        )
    for field_name in (
        "latest_rank_stability_status",
        "latest_candidate_count",
        "latest_stable_ready_count",
        "latest_unstable_ready_count",
        "latest_source_generated_at",
        "latest_source_age_seconds",
        "max_source_age_seconds",
    ):
        if getattr(report, field_name) is not None:
            raise ValueError(f"{field_name} must be absent without source reports")
    if report.duplicate_latest_generated_at_count != 0:
        raise ValueError(
            "duplicate_latest_generated_at_count must be zero without source reports",
        )
    if report.reason_code_counts:
        raise ValueError("reason_code_counts must be empty without source reports")


def _validate_nonempty_health_report(
    report: PaperProjectScreeningRankStabilityDbHistoryHealthReport,
) -> None:
    for field_name in (
        "latest_rank_stability_status",
        "latest_candidate_count",
        "latest_stable_ready_count",
        "latest_unstable_ready_count",
    ):
        if getattr(report, field_name) is None:
            raise ValueError(f"{field_name} is required with source reports")
    if (
        report.latest_stable_ready_count is not None
        and report.latest_unstable_ready_count is not None
        and report.latest_candidate_count is not None
        and (
            report.latest_stable_ready_count + report.latest_unstable_ready_count
            > report.latest_candidate_count
        )
    ):
        raise ValueError("latest_candidate_count must cover latest ready counts")
    missing_latest_reason = (
        "missing_latest_paper_project_screening_rank_stability_source_timestamp"
        in report.reason_codes
    )
    if missing_latest_reason:
        if report.latest_source_generated_at is not None:
            raise ValueError("latest_source_generated_at must be absent without timestamp")
        if report.latest_source_age_seconds is not None:
            raise ValueError("latest_source_age_seconds must be absent without timestamp")
        if report.max_source_age_seconds is not None:
            raise ValueError("max_source_age_seconds must be absent without timestamp")
    else:
        if report.latest_source_generated_at is None:
            raise ValueError(
                "latest_source_generated_at is required with source reports",
            )
        if report.latest_source_age_seconds is None:
            raise ValueError("latest_source_age_seconds is required with source reports")
        if report.max_source_age_seconds is None:
            raise ValueError("max_source_age_seconds is required with source reports")
        if report.latest_source_age_seconds > report.max_source_age_seconds:
            raise ValueError(
                "latest_source_age_seconds must not exceed max_source_age_seconds",
            )
    if report.duplicate_latest_generated_at_count >= max(
        report.rank_stability_report_count,
        1,
    ):
        raise ValueError(
            "duplicate_latest_generated_at_count must be below source count",
        )
    if not report.reason_code_counts:
        raise ValueError("reason_code_counts must summarize source reports")


def _validate_health_reason_codes(
    report: PaperProjectScreeningRankStabilityDbHistoryHealthReport,
) -> None:
    has_pass_reason = PASS_REASON_CODE in report.reason_codes
    has_other_reason = any(
        reason_code in BLOCKED_REASON_CODES or reason_code in WATCH_REASON_CODES
        for reason_code in report.reason_codes
    )
    if has_pass_reason and has_other_reason:
        raise ValueError("reason_codes pass reason must not be mixed with other reasons")
    if report.health_status != _health_status(report.reason_codes):
        raise ValueError("health_status must match reason_codes")
    if report.health_status == "pass" and report.reason_codes != (PASS_REASON_CODE,):
        raise ValueError("reason_codes must contain the pass reason for pass health")
    if report.health_status != "pass" and has_pass_reason:
        raise ValueError("reason_codes must not contain pass reason unless health passes")


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    previous_key: tuple[int, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason code counts")
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.report_count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allowed: frozenset[str] | None = None,
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
        if allowed is not None and code not in allowed:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > code:
            raise ValueError(f"{field_name} must be sorted")
        previous = code
        seen.add(code)
    return codes


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


def _validate_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")
