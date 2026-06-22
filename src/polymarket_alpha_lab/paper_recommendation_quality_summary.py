"""Pure paper-only quality summary reducer for recommendation reports."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime


__all__ = (
    "PaperRecommendationQualityReasonCodeCount",
    "PaperRecommendationQualitySubreportSummary",
    "PaperRecommendationQualitySummaryReport",
    "build_paper_recommendation_quality_summary_report",
)


STATUSES = ("pass", "watch", "blocked", "incomplete")
SUBREPORT_NAMES = (
    "health",
    "consistency",
    "risk_budget",
    "reason_trend",
    "rank_stability",
)


@dataclass(frozen=True)
class PaperRecommendationQualityReasonCodeCount:
    reason_code: str
    subreport_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("subreport_count", self.subreport_count)


@dataclass(frozen=True)
class PaperRecommendationQualitySubreportSummary:
    report_name: str
    status: str
    generated_at: datetime | None
    config_version: str | None
    row_count: int
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_report_name("report_name", self.report_name)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "generated_at",
            _optional_as_utc("generated_at", self.generated_at),
        )
        if self.config_version is not None:
            _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("row_count", self.row_count)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("subreport summary", self)


@dataclass(frozen=True)
class PaperRecommendationQualitySummaryReport:
    generated_at: datetime
    config_version: str
    summary_status: str
    subreport_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    incomplete_count: int
    reason_code_counts: tuple[PaperRecommendationQualityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    subreports: tuple[PaperRecommendationQualitySubreportSummary, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("summary_status", self.summary_status)
        for field_name in (
            "subreport_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "incomplete_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "subreports", _normalize_subreports(self.subreports))
        _validate_report_consistency(self)
        _require_hard_flags("quality summary report", self)


def build_paper_recommendation_quality_summary_report(
    *,
    health_report: object | None,
    consistency_report: object | None,
    risk_budget_report: object | None,
    reason_trend_report: object | None,
    generated_at: datetime,
    config_version: str,
    rank_stability_report: object | None = None,
) -> PaperRecommendationQualitySummaryReport:
    generated_at = _as_utc("generated_at", generated_at)
    _require_canonical_string("config_version", config_version)
    subreports = (
        _health_summary(health_report),
        _consistency_summary(consistency_report),
        _risk_budget_summary(risk_budget_report),
        _reason_trend_summary(reason_trend_report),
        _rank_stability_summary(rank_stability_report),
    )
    reason_code_counts = _reason_code_counts(subreports)

    return PaperRecommendationQualitySummaryReport(
        generated_at=generated_at,
        config_version=config_version,
        summary_status=_summary_status(subreports),
        subreport_count=len(subreports),
        pass_count=_status_count(subreports, "pass"),
        watch_count=_status_count(subreports, "watch"),
        blocked_count=_status_count(subreports, "blocked"),
        incomplete_count=_status_count(subreports, "incomplete"),
        reason_code_counts=reason_code_counts,
        reason_codes=tuple(row.reason_code for row in reason_code_counts),
        subreports=subreports,
    )


def _health_summary(report: object | None) -> PaperRecommendationQualitySubreportSummary:
    if report is None:
        return _missing_required_summary("health", "health_report_missing")
    _require_hard_flags("health report", report)
    return PaperRecommendationQualitySubreportSummary(
        report_name="health",
        status=_status_from_source(
            "health_status",
            _required_attr(report, "health_status"),
        ),
        generated_at=_required_attr(report, "generated_at"),
        config_version=_required_attr(report, "config_version"),
        row_count=_required_attr(report, "row_count"),
        reason_codes=_reason_codes_from_count_rows(
            _required_attr(report, "reason_code_counts"),
        ),
    )


def _consistency_summary(
    report: object | None,
) -> PaperRecommendationQualitySubreportSummary:
    if report is None:
        return _missing_required_summary("consistency", "consistency_report_missing")
    _require_hard_flags("consistency report", report)
    return PaperRecommendationQualitySubreportSummary(
        report_name="consistency",
        status=_status_from_source(
            "consistency_status",
            _required_attr(report, "consistency_status"),
        ),
        generated_at=_required_attr(report, "generated_at"),
        config_version=_required_attr(report, "config_version"),
        row_count=_required_attr(report, "group_count"),
        reason_codes=_required_attr(report, "reason_codes"),
    )


def _risk_budget_summary(
    report: object | None,
) -> PaperRecommendationQualitySubreportSummary:
    if report is None:
        return _missing_required_summary("risk_budget", "risk_budget_report_missing")
    _require_hard_flags("risk_budget report", report)
    return PaperRecommendationQualitySubreportSummary(
        report_name="risk_budget",
        status=_status_from_source("status", _required_attr(report, "status")),
        generated_at=_required_attr(report, "generated_at"),
        config_version=_required_attr(report, "config_version"),
        row_count=_required_attr(report, "selected_count"),
        reason_codes=_required_attr(report, "reason_codes"),
    )


def _reason_trend_summary(
    report: object | None,
) -> PaperRecommendationQualitySubreportSummary:
    if report is None:
        return _missing_required_summary("reason_trend", "reason_trend_report_missing")
    _require_hard_flags("reason_trend report", report)
    source_report_count = _required_attr(report, "source_report_count")
    _require_nonnegative_int("source_report_count", source_report_count)
    reason_codes = _reason_codes_from_trend_rows(
        _required_attr(report, "reason_trend_rows"),
    )
    status = "pass"
    if source_report_count == 0:
        status = "watch"
        reason_codes = ("reason_trend_source_reports_missing",)
    elif not reason_codes:
        status = "watch"
        reason_codes = ("reason_trend_reasons_missing",)

    return PaperRecommendationQualitySubreportSummary(
        report_name="reason_trend",
        status=status,
        generated_at=_required_attr(report, "generated_at"),
        config_version=_required_attr(report, "config_version"),
        row_count=source_report_count,
        reason_codes=reason_codes,
    )


def _rank_stability_summary(
    report: object | None,
) -> PaperRecommendationQualitySubreportSummary:
    if report is None:
        return PaperRecommendationQualitySubreportSummary(
            report_name="rank_stability",
            status="watch",
            generated_at=None,
            config_version=None,
            row_count=0,
            reason_codes=("optional_rank_stability_report_missing",),
        )
    _require_hard_flags("rank_stability report", report)
    return PaperRecommendationQualitySubreportSummary(
        report_name="rank_stability",
        status=_rank_status_from_source(
            _required_attr(report, "stability_status"),
        ),
        generated_at=_required_attr(report, "generated_at"),
        config_version=_required_attr(report, "config_version"),
        row_count=_required_attr(report, "candidate_count"),
        reason_codes=_required_attr(report, "reason_codes"),
    )


def _missing_required_summary(
    report_name: str,
    reason_code: str,
) -> PaperRecommendationQualitySubreportSummary:
    return PaperRecommendationQualitySubreportSummary(
        report_name=report_name,
        status="incomplete",
        generated_at=None,
        config_version=None,
        row_count=0,
        reason_codes=(reason_code,),
    )


def _reason_codes_from_count_rows(rows: object) -> tuple[str, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    reason_codes = tuple(_required_attr(row, "reason_code") for row in normalized)
    if not reason_codes:
        return ("health_reasons_missing",)
    return _normalize_reason_codes("reason_code_counts", reason_codes)


def _reason_codes_from_trend_rows(rows: object) -> tuple[str, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_trend_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_trend_rows must be an iterable") from exc
    reason_codes = tuple(_required_attr(row, "reason_code") for row in normalized)
    if not reason_codes:
        return ()
    return _normalize_reason_codes("reason_trend_rows", reason_codes)


def _reason_code_counts(
    subreports: tuple[PaperRecommendationQualitySubreportSummary, ...],
) -> tuple[PaperRecommendationQualityReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for subreport in subreports:
        counts.update(frozenset(subreport.reason_codes))
    return tuple(
        PaperRecommendationQualityReasonCodeCount(
            reason_code=reason_code,
            subreport_count=subreport_count,
        )
        for reason_code, subreport_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _summary_status(
    subreports: tuple[PaperRecommendationQualitySubreportSummary, ...],
) -> str:
    if any(subreport.status == "blocked" for subreport in subreports):
        return "blocked"
    if any(subreport.status == "incomplete" for subreport in subreports):
        return "incomplete"
    if any(subreport.status == "watch" for subreport in subreports):
        return "watch"
    return "pass"


def _status_count(
    subreports: tuple[PaperRecommendationQualitySubreportSummary, ...],
    status: str,
) -> int:
    return sum(1 for subreport in subreports if subreport.status == status)


def _normalize_subreports(
    subreports: object,
) -> tuple[PaperRecommendationQualitySubreportSummary, ...]:
    if isinstance(subreports, (str, bytes)):
        raise ValueError("subreports must be an iterable")
    try:
        normalized = tuple(subreports)
    except TypeError as exc:
        raise ValueError("subreports must be an iterable") from exc
    for subreport in normalized:
        if type(subreport) is not PaperRecommendationQualitySubreportSummary:
            raise ValueError("subreports must contain quality subreport summaries")
        _require_hard_flags("subreport summary", subreport)
    if tuple(subreport.report_name for subreport in normalized) != SUBREPORT_NAMES:
        raise ValueError("subreports must follow deterministic report order")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[PaperRecommendationQualityReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperRecommendationQualityReasonCodeCount:
            raise ValueError("reason_code_counts must contain quality reason rows")
    sorted_rows = tuple(sorted(normalized, key=lambda row: (-row.subreport_count, row.reason_code)))
    if normalized != sorted_rows:
        raise ValueError("reason_code_counts must be deterministically sorted")
    return normalized


def _validate_report_consistency(
    report: PaperRecommendationQualitySummaryReport,
) -> None:
    if report.subreport_count != len(report.subreports):
        raise ValueError("subreport_count must match subreports")
    if report.pass_count != _status_count(report.subreports, "pass"):
        raise ValueError("pass_count must match subreports")
    if report.watch_count != _status_count(report.subreports, "watch"):
        raise ValueError("watch_count must match subreports")
    if report.blocked_count != _status_count(report.subreports, "blocked"):
        raise ValueError("blocked_count must match subreports")
    if report.incomplete_count != _status_count(report.subreports, "incomplete"):
        raise ValueError("incomplete_count must match subreports")
    if report.subreport_count != (
        report.pass_count
        + report.watch_count
        + report.blocked_count
        + report.incomplete_count
    ):
        raise ValueError("subreport_count must match status counts")
    expected_reason_code_counts = _reason_code_counts(report.subreports)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match subreports")
    expected_reason_codes = tuple(row.reason_code for row in expected_reason_code_counts)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    if report.summary_status != _summary_status(report.subreports):
        raise ValueError("summary_status must match subreports")


def _status_from_source(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in ("pass", "watch", "blocked"):
        raise ValueError(f"{field_name} must be pass, watch, or blocked")
    return value


def _rank_status_from_source(value: object) -> str:
    _require_canonical_string("stability_status", value)
    if value == "stable":
        return "pass"
    if value in ("watch", "blocked"):
        return value
    raise ValueError("stability_status must be stable, watch, or blocked")


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _optional_as_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    return items


def _require_hard_flags(field_name: str, value: object) -> None:
    if _required_attr(value, "paper_only") is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if _required_attr(value, "report_only") is not True:
        raise ValueError(f"{field_name} must be report_only")
    if _required_attr(value, "readonly") is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_report_name(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in SUBREPORT_NAMES:
        raise ValueError(f"{field_name} must be a known subreport name")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, blocked, or incomplete")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
