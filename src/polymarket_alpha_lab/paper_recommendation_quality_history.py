"""Historical reducer for paper recommendation quality summaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.paper_recommendation_quality_summary import (
    PaperRecommendationQualitySummaryReport,
)


SUMMARY_STATUSES = ("pass", "watch", "blocked", "incomplete")
HISTORY_STATUSES = ("pass", "watch", "blocked")
SUBREPORT_NAMES = (
    "health",
    "consistency",
    "risk_budget",
    "reason_trend",
    "rank_stability",
)


@dataclass(frozen=True)
class PaperRecommendationQualityHistoryConfig:
    config_version: str
    min_report_count: int = 3
    max_blocked_summary_count: int = 0
    max_incomplete_summary_count: int = 0
    max_duplicate_generated_at_count: int = 0
    max_recurring_incomplete_subreport_count: int = 1
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_report_count", self.min_report_count)
        for field_name in (
            "max_blocked_summary_count",
            "max_incomplete_summary_count",
            "max_duplicate_generated_at_count",
            "max_recurring_incomplete_subreport_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperRecommendationQualityHistoryStatusRow:
    summary_status: str
    status_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_summary_status("summary_status", self.summary_status)
        _require_nonnegative_int("status_count", self.status_count)
        _require_hard_flags("status row", self)


@dataclass(frozen=True)
class PaperRecommendationQualityHistoryRecurringSubreportRow:
    report_name: str
    incomplete_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_report_name("report_name", self.report_name)
        _require_positive_int("incomplete_count", self.incomplete_count)
        _require_hard_flags("recurring subreport row", self)


@dataclass(frozen=True)
class PaperRecommendationQualityHistoryReport:
    generated_at: datetime
    config_version: str
    history_status: str
    source_report_count: int
    first_source_generated_at: datetime | None
    latest_source_generated_at: datetime | None
    summary_status_rows: tuple[PaperRecommendationQualityHistoryStatusRow, ...]
    duplicate_generated_at_count: int
    recurring_blocked_reason_codes: tuple[str, ...]
    recurring_incomplete_subreports: tuple[
        PaperRecommendationQualityHistoryRecurringSubreportRow,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_history_status("history_status", self.history_status)
        _require_nonnegative_int("source_report_count", self.source_report_count)
        object.__setattr__(
            self,
            "first_source_generated_at",
            _as_optional_utc("first_source_generated_at", self.first_source_generated_at),
        )
        object.__setattr__(
            self,
            "latest_source_generated_at",
            _as_optional_utc("latest_source_generated_at", self.latest_source_generated_at),
        )
        object.__setattr__(
            self,
            "summary_status_rows",
            _normalize_status_rows(self.summary_status_rows),
        )
        _require_nonnegative_int(
            "duplicate_generated_at_count",
            self.duplicate_generated_at_count,
        )
        object.__setattr__(
            self,
            "recurring_blocked_reason_codes",
            _normalize_reason_codes(
                "recurring_blocked_reason_codes",
                self.recurring_blocked_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "recurring_incomplete_subreports",
            _normalize_recurring_subreports(self.recurring_incomplete_subreports),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("history report", self)


def build_paper_recommendation_quality_history_report(
    summary_reports: object,
    *,
    config: PaperRecommendationQualityHistoryConfig,
    generated_at: datetime,
) -> PaperRecommendationQualityHistoryReport:
    if type(config) is not PaperRecommendationQualityHistoryConfig:
        raise ValueError("config must be a PaperRecommendationQualityHistoryConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("config", config)
    reports = _normalize_summary_reports(summary_reports)
    chronological_reports = _chronological_reports(reports)
    status_rows = _status_rows(chronological_reports)
    duplicate_generated_at_count = _duplicate_generated_at_count(chronological_reports)
    recurring_blocked_reason_codes = _blocked_reason_codes(chronological_reports)
    recurring_incomplete_subreports = _recurring_incomplete_subreports(
        chronological_reports,
        config.max_recurring_incomplete_subreport_count,
    )
    reason_codes = _report_reason_codes(
        reports=chronological_reports,
        status_rows=status_rows,
        duplicate_generated_at_count=duplicate_generated_at_count,
        recurring_blocked_reason_codes=recurring_blocked_reason_codes,
        recurring_incomplete_subreports=recurring_incomplete_subreports,
        config=config,
    )

    return PaperRecommendationQualityHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        history_status=_history_status(
            reports=chronological_reports,
            status_rows=status_rows,
            duplicate_generated_at_count=duplicate_generated_at_count,
            recurring_incomplete_subreports=recurring_incomplete_subreports,
            config=config,
        ),
        source_report_count=len(chronological_reports),
        first_source_generated_at=(
            chronological_reports[0].generated_at if chronological_reports else None
        ),
        latest_source_generated_at=(
            chronological_reports[-1].generated_at if chronological_reports else None
        ),
        summary_status_rows=status_rows,
        duplicate_generated_at_count=duplicate_generated_at_count,
        recurring_blocked_reason_codes=recurring_blocked_reason_codes,
        recurring_incomplete_subreports=recurring_incomplete_subreports,
        reason_codes=reason_codes,
    )


def _normalize_summary_reports(
    summary_reports: object,
) -> tuple[PaperRecommendationQualitySummaryReport, ...]:
    if type(summary_reports) not in (list, tuple):
        raise ValueError("summary_reports must be a list or tuple")
    reports = tuple(summary_reports)
    for report in reports:
        if type(report) is not PaperRecommendationQualitySummaryReport:
            raise ValueError(
                "summary_reports must contain PaperRecommendationQualitySummaryReport values",
            )
        _require_hard_flags("summary report", report)
    return reports


def _chronological_reports(
    reports: tuple[PaperRecommendationQualitySummaryReport, ...],
) -> tuple[PaperRecommendationQualitySummaryReport, ...]:
    return tuple(
        report
        for _, report in sorted(
            enumerate(reports),
            key=lambda item: (item[1].generated_at, item[0]),
        )
    )


def _status_rows(
    reports: tuple[PaperRecommendationQualitySummaryReport, ...],
) -> tuple[PaperRecommendationQualityHistoryStatusRow, ...]:
    return tuple(
        PaperRecommendationQualityHistoryStatusRow(
            summary_status,
            sum(1 for report in reports if report.summary_status == summary_status),
        )
        for summary_status in SUMMARY_STATUSES
    )


def _duplicate_generated_at_count(
    reports: tuple[PaperRecommendationQualitySummaryReport, ...],
) -> int:
    counts: dict[datetime, int] = {}
    for report in reports:
        counts[report.generated_at] = counts.get(report.generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _blocked_reason_codes(
    reports: tuple[PaperRecommendationQualitySummaryReport, ...],
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    for report in reports:
        for subreport in report.subreports:
            if subreport.status == "blocked":
                reason_codes.update(subreport.reason_codes)
    return tuple(sorted(reason_codes))


def _recurring_incomplete_subreports(
    reports: tuple[PaperRecommendationQualitySummaryReport, ...],
    max_recurring_incomplete_subreport_count: int,
) -> tuple[PaperRecommendationQualityHistoryRecurringSubreportRow, ...]:
    counts: dict[str, int] = {}
    for report in reports:
        for subreport in report.subreports:
            if subreport.status == "incomplete":
                counts[subreport.report_name] = counts.get(subreport.report_name, 0) + 1
    return tuple(
        PaperRecommendationQualityHistoryRecurringSubreportRow(report_name, count)
        for report_name, count in sorted(counts.items())
        if count > max_recurring_incomplete_subreport_count
    )


def _history_status(
    *,
    reports: tuple[PaperRecommendationQualitySummaryReport, ...],
    status_rows: tuple[PaperRecommendationQualityHistoryStatusRow, ...],
    duplicate_generated_at_count: int,
    recurring_incomplete_subreports: tuple[
        PaperRecommendationQualityHistoryRecurringSubreportRow,
        ...,
    ],
    config: PaperRecommendationQualityHistoryConfig,
) -> str:
    if len(reports) < config.min_report_count:
        return "blocked"
    if _count_for_status(status_rows, "blocked") > config.max_blocked_summary_count:
        return "blocked"
    if _count_for_status(status_rows, "incomplete") > config.max_incomplete_summary_count:
        return "blocked"
    if duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        return "watch"
    if recurring_incomplete_subreports:
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    reports: tuple[PaperRecommendationQualitySummaryReport, ...],
    status_rows: tuple[PaperRecommendationQualityHistoryStatusRow, ...],
    duplicate_generated_at_count: int,
    recurring_blocked_reason_codes: tuple[str, ...],
    recurring_incomplete_subreports: tuple[
        PaperRecommendationQualityHistoryRecurringSubreportRow,
        ...,
    ],
    config: PaperRecommendationQualityHistoryConfig,
) -> tuple[str, ...]:
    if len(reports) < config.min_report_count:
        return ("insufficient_quality_summary_history",)
    reason_codes: list[str] = []
    if _count_for_status(status_rows, "blocked") > config.max_blocked_summary_count:
        reason_codes.append("blocked_quality_summary_threshold_exceeded")
        if recurring_blocked_reason_codes:
            reason_codes.append("recurring_blocked_reason_codes_present")
    if _count_for_status(status_rows, "incomplete") > config.max_incomplete_summary_count:
        reason_codes.append("incomplete_quality_summary_threshold_exceeded")
    if duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        reason_codes.append("duplicate_generated_at_threshold_exceeded")
    if recurring_incomplete_subreports:
        reason_codes.append("recurring_incomplete_subreports_present")
    if not reason_codes:
        reason_codes.append("quality_summary_history_passed")
    return tuple(sorted(reason_codes))


def _count_for_status(
    status_rows: tuple[PaperRecommendationQualityHistoryStatusRow, ...],
    summary_status: str,
) -> int:
    for row in status_rows:
        if row.summary_status == summary_status:
            return row.status_count
    return 0


def _normalize_status_rows(
    rows: object,
) -> tuple[PaperRecommendationQualityHistoryStatusRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("summary_status_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("summary_status_rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperRecommendationQualityHistoryStatusRow:
            raise ValueError(
                "summary_status_rows must contain PaperRecommendationQualityHistoryStatusRow values",
            )
        _require_hard_flags("status row", row)
    if tuple(row.summary_status for row in normalized) != SUMMARY_STATUSES:
        raise ValueError("summary_status_rows must contain all summary statuses")
    return normalized


def _normalize_recurring_subreports(
    rows: object,
) -> tuple[PaperRecommendationQualityHistoryRecurringSubreportRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("recurring_incomplete_subreports must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("recurring_incomplete_subreports must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperRecommendationQualityHistoryRecurringSubreportRow:
            raise ValueError(
                "recurring_incomplete_subreports must contain "
                "PaperRecommendationQualityHistoryRecurringSubreportRow values",
            )
        _require_hard_flags("recurring subreport row", row)
    if normalized != tuple(sorted(normalized, key=lambda row: row.report_name)):
        raise ValueError("recurring_incomplete_subreports must be deterministic")
    return normalized


def _validate_report_consistency(
    report: PaperRecommendationQualityHistoryReport,
) -> None:
    if report.source_report_count == 0:
        if report.first_source_generated_at is not None:
            raise ValueError("first_source_generated_at must be absent without reports")
        if report.latest_source_generated_at is not None:
            raise ValueError("latest_source_generated_at must be absent without reports")
    elif report.first_source_generated_at is None or report.latest_source_generated_at is None:
        raise ValueError("source generated_at bounds are required with reports")
    if report.recurring_blocked_reason_codes != tuple(sorted(report.recurring_blocked_reason_codes)):
        raise ValueError("recurring_blocked_reason_codes must be deterministic")
    if report.reason_codes != tuple(sorted(report.reason_codes)):
        raise ValueError("reason_codes must be deterministic")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_summary_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SUMMARY_STATUSES:
        raise ValueError(f"{field_name} must be a known summary status")


def _require_history_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HISTORY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_report_name(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SUBREPORT_NAMES:
        raise ValueError(f"{field_name} must be a known quality subreport name")


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


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "PaperRecommendationQualityHistoryConfig",
    "PaperRecommendationQualityHistoryReport",
    "PaperRecommendationQualityHistoryRecurringSubreportRow",
    "PaperRecommendationQualityHistoryStatusRow",
    "build_paper_recommendation_quality_history_report",
)
