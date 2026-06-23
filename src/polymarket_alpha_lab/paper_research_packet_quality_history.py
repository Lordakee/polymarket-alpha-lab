"""Historical reducer for paper research packet quality reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polymarket_alpha_lab.paper_research_packet_quality import (
    CHECK_NAMES,
    QUALITY_STATUSES,
    PaperResearchPacketQualityCheckRow,
    PaperResearchPacketQualityReasonCodeCount,
    PaperResearchPacketQualityReport,
)


__all__ = (
    "DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_HISTORY_CONFIG_VERSION",
    "PaperResearchPacketQualityHistoryConfig",
    "PaperResearchPacketQualityHistoryCheckSummaryRow",
    "PaperResearchPacketQualityHistoryRecurringReasonCodeRow",
    "PaperResearchPacketQualityHistoryReport",
    "PaperResearchPacketQualityHistoryStatusRow",
    "build_paper_research_packet_quality_history_report",
)


QUANTUM = Decimal("0.000001")
STATUS_RANK = {"pass": 0, "watch": 1, "blocked": 2}
RECURRING_STATUSES = ("blocked", "watch")
RECURRING_STATUS_RANK = {"blocked": 0, "watch": 1}
DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_HISTORY_CONFIG_VERSION = (
    "paper-research-packet-quality-history-v0"
)


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryConfig:
    config_version: str = DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_HISTORY_CONFIG_VERSION
    min_report_count: int = 3
    max_blocked_quality_report_count: int = 0
    max_watch_quality_report_count: int = 0
    max_duplicate_generated_at_count: int = 0
    max_recurring_reason_code_report_count: int = 1
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_report_count", self.min_report_count)
        for field_name in (
            "max_blocked_quality_report_count",
            "max_watch_quality_report_count",
            "max_duplicate_generated_at_count",
            "max_recurring_reason_code_report_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryStatusRow:
    quality_status: str
    status_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_quality_status("quality_status", self.quality_status)
        _require_nonnegative_int("status_count", self.status_count)
        _validate_hard_flags("status row", self)


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryCheckSummaryRow:
    check_name: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_check_name("check_name", self.check_name)
        _require_quality_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_hard_flags("check summary row", self)


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryRecurringReasonCodeRow:
    check_status: str
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_recurring_check_status("check_status", self.check_status)
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("recurring reason row", self)


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryReport:
    generated_at: datetime
    config_version: str
    history_status: str
    source_report_count: int
    first_source_generated_at: datetime | None
    latest_source_generated_at: datetime | None
    latest_quality_status: str | None
    latest_source_age_seconds: int | None
    latest_included_share: Decimal | None
    latest_skipped_share: Decimal | None
    latest_check_rows: tuple[PaperResearchPacketQualityHistoryCheckSummaryRow, ...]
    quality_status_rows: tuple[PaperResearchPacketQualityHistoryStatusRow, ...]
    duplicate_generated_at_count: int
    recurring_reason_code_rows: tuple[
        PaperResearchPacketQualityHistoryRecurringReasonCodeRow,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_quality_status("history_status", self.history_status)
        _require_nonnegative_int("source_report_count", self.source_report_count)
        object.__setattr__(
            self,
            "first_source_generated_at",
            _normalize_optional_utc("first_source_generated_at", self.first_source_generated_at),
        )
        object.__setattr__(
            self,
            "latest_source_generated_at",
            _normalize_optional_utc("latest_source_generated_at", self.latest_source_generated_at),
        )
        if self.latest_quality_status is not None:
            _require_quality_status("latest_quality_status", self.latest_quality_status)
        if self.latest_source_age_seconds is not None:
            _require_nonnegative_int(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            )
        object.__setattr__(
            self,
            "latest_included_share",
            _normalize_optional_decimal("latest_included_share", self.latest_included_share),
        )
        object.__setattr__(
            self,
            "latest_skipped_share",
            _normalize_optional_decimal("latest_skipped_share", self.latest_skipped_share),
        )
        object.__setattr__(
            self,
            "latest_check_rows",
            _normalize_history_check_rows(self.latest_check_rows),
        )
        object.__setattr__(
            self,
            "quality_status_rows",
            _normalize_quality_status_rows(self.quality_status_rows),
        )
        _require_nonnegative_int(
            "duplicate_generated_at_count",
            self.duplicate_generated_at_count,
        )
        object.__setattr__(
            self,
            "recurring_reason_code_rows",
            _normalize_recurring_reason_code_rows(self.recurring_reason_code_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _validate_hard_flags("history report", self)


def build_paper_research_packet_quality_history_report(
    quality_reports: object,
    *,
    config: PaperResearchPacketQualityHistoryConfig,
    generated_at: datetime,
) -> PaperResearchPacketQualityHistoryReport:
    if type(config) is not PaperResearchPacketQualityHistoryConfig:
        raise ValueError(
            "config must be a PaperResearchPacketQualityHistoryConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _validate_hard_flags("config", config)
    reports = _normalize_quality_reports(quality_reports)
    chronological_reports = _chronological_reports(reports)
    quality_status_rows = _quality_status_rows(chronological_reports)
    duplicate_generated_at_count = _duplicate_generated_at_count(chronological_reports)
    recurring_reason_code_rows = _recurring_reason_code_rows(
        chronological_reports,
        max_recurring_reason_code_report_count=config.max_recurring_reason_code_report_count,
    )
    latest = chronological_reports[-1] if chronological_reports else None
    latest_quality_status = latest.quality_status if latest is not None else None
    latest_source_age_seconds = (
        latest.source_age_seconds if latest is not None else None
    )
    latest_included_share = latest.included_share if latest is not None else None
    latest_skipped_share = latest.skipped_share if latest is not None else None
    latest_check_rows = (
        _latest_check_summary_rows(latest.check_rows) if latest is not None else ()
    )

    return PaperResearchPacketQualityHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        history_status=_history_status(
            reports=chronological_reports,
            quality_status_rows=quality_status_rows,
            duplicate_generated_at_count=duplicate_generated_at_count,
            recurring_reason_code_rows=recurring_reason_code_rows,
            config=config,
        ),
        source_report_count=len(chronological_reports),
        first_source_generated_at=(
            chronological_reports[0].generated_at if chronological_reports else None
        ),
        latest_source_generated_at=(
            latest.generated_at if latest is not None else None
        ),
        latest_quality_status=latest_quality_status,
        latest_source_age_seconds=latest_source_age_seconds,
        latest_included_share=latest_included_share,
        latest_skipped_share=latest_skipped_share,
        latest_check_rows=latest_check_rows,
        quality_status_rows=quality_status_rows,
        duplicate_generated_at_count=duplicate_generated_at_count,
        recurring_reason_code_rows=recurring_reason_code_rows,
        reason_codes=_history_reason_codes(
            reports=chronological_reports,
            quality_status_rows=quality_status_rows,
            duplicate_generated_at_count=duplicate_generated_at_count,
            recurring_reason_code_rows=recurring_reason_code_rows,
            config=config,
        ),
    )


def _latest_check_summary_rows(
    rows: tuple[PaperResearchPacketQualityCheckRow, ...],
) -> tuple[PaperResearchPacketQualityHistoryCheckSummaryRow, ...]:
    return tuple(
        PaperResearchPacketQualityHistoryCheckSummaryRow(
            row.check_name,
            row.status,
            row.reason_codes,
        )
        for row in rows
    )


def _normalize_quality_reports(
    quality_reports: object,
) -> tuple[PaperResearchPacketQualityReport, ...]:
    if type(quality_reports) not in (list, tuple):
        raise ValueError("quality_reports must be a list or tuple")
    reports = tuple(quality_reports)
    for report in reports:
        if type(report) is not PaperResearchPacketQualityReport:
            raise ValueError(
                "quality_reports must contain PaperResearchPacketQualityReport values",
            )
        _validate_quality_report(report)
    return reports


def _chronological_reports(
    reports: tuple[PaperResearchPacketQualityReport, ...],
) -> tuple[PaperResearchPacketQualityReport, ...]:
    return tuple(
        report
        for _, report in sorted(
            enumerate(reports),
            key=lambda item: (item[1].generated_at, item[0]),
        )
    )


def _quality_status_rows(
    reports: tuple[PaperResearchPacketQualityReport, ...],
) -> tuple[PaperResearchPacketQualityHistoryStatusRow, ...]:
    return tuple(
        PaperResearchPacketQualityHistoryStatusRow(
            quality_status,
            sum(1 for report in reports if report.quality_status == quality_status),
        )
        for quality_status in QUALITY_STATUSES
    )


def _duplicate_generated_at_count(
    reports: tuple[PaperResearchPacketQualityReport, ...],
) -> int:
    counts: dict[datetime, int] = {}
    for report in reports:
        counts[report.generated_at] = counts.get(report.generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _recurring_reason_code_rows(
    reports: tuple[PaperResearchPacketQualityReport, ...],
    *,
    max_recurring_reason_code_report_count: int,
) -> tuple[PaperResearchPacketQualityHistoryRecurringReasonCodeRow, ...]:
    counts: dict[tuple[str, str], int] = {}
    for report in reports:
        seen_for_report: set[tuple[str, str]] = set()
        for row in report.check_rows:
            if row.status not in RECURRING_STATUSES:
                continue
            for reason_code in row.reason_codes:
                key = (row.status, reason_code)
                if key in seen_for_report:
                    continue
                seen_for_report.add(key)
                counts[key] = counts.get(key, 0) + 1
    return tuple(
        PaperResearchPacketQualityHistoryRecurringReasonCodeRow(
            check_status,
            reason_code,
            report_count,
        )
        for (check_status, reason_code), report_count in sorted(
            counts.items(),
            key=lambda item: _recurring_reason_code_sort_key(item[0]),
        )
        if report_count > max_recurring_reason_code_report_count
    )


def _history_status(
    *,
    reports: tuple[PaperResearchPacketQualityReport, ...],
    quality_status_rows: tuple[PaperResearchPacketQualityHistoryStatusRow, ...],
    duplicate_generated_at_count: int,
    recurring_reason_code_rows: tuple[
        PaperResearchPacketQualityHistoryRecurringReasonCodeRow,
        ...,
    ],
    config: PaperResearchPacketQualityHistoryConfig,
) -> str:
    if len(reports) < config.min_report_count:
        return "blocked"
    if _count_for_status(quality_status_rows, "blocked") > config.max_blocked_quality_report_count:
        return "blocked"
    if _count_for_status(quality_status_rows, "watch") > config.max_watch_quality_report_count:
        return "watch"
    if duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        return "watch"
    if recurring_reason_code_rows:
        return "watch"
    return "pass"


def _history_reason_codes(
    *,
    reports: tuple[PaperResearchPacketQualityReport, ...],
    quality_status_rows: tuple[PaperResearchPacketQualityHistoryStatusRow, ...],
    duplicate_generated_at_count: int,
    recurring_reason_code_rows: tuple[
        PaperResearchPacketQualityHistoryRecurringReasonCodeRow,
        ...,
    ],
    config: PaperResearchPacketQualityHistoryConfig,
) -> tuple[str, ...]:
    if len(reports) < config.min_report_count:
        return ("insufficient_paper_research_packet_quality_history",)
    reason_codes: list[str] = []
    if _count_for_status(quality_status_rows, "blocked") > config.max_blocked_quality_report_count:
        reason_codes.append("blocked_quality_report_threshold_exceeded")
        if any(row.check_status == "blocked" for row in recurring_reason_code_rows):
            reason_codes.append("recurring_blocked_reason_codes_present")
    if _count_for_status(quality_status_rows, "watch") > config.max_watch_quality_report_count:
        reason_codes.append("watch_quality_report_threshold_exceeded")
        if any(row.check_status == "watch" for row in recurring_reason_code_rows):
            reason_codes.append("recurring_watch_reason_codes_present")
    if duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        reason_codes.append("duplicate_generated_at_threshold_exceeded")
    if (
        any(row.check_status == "blocked" for row in recurring_reason_code_rows)
        and "recurring_blocked_reason_codes_present" not in reason_codes
    ):
        reason_codes.append("recurring_blocked_reason_codes_present")
    if (
        any(row.check_status == "watch" for row in recurring_reason_code_rows)
        and "recurring_watch_reason_codes_present" not in reason_codes
    ):
        reason_codes.append("recurring_watch_reason_codes_present")
    if not reason_codes:
        reason_codes.append("paper_research_packet_quality_history_passed")
    return tuple(sorted(reason_codes))


def _count_for_status(
    status_rows: tuple[PaperResearchPacketQualityHistoryStatusRow, ...],
    quality_status: str,
) -> int:
    for row in status_rows:
        if row.quality_status == quality_status:
            return row.status_count
    return 0


def _validate_quality_report(report: PaperResearchPacketQualityReport) -> None:
    _validate_hard_flags("quality report", report)
    generated_at = _as_utc("generated_at", report.generated_at)
    source_generated_at = _as_utc("source_generated_at", report.source_generated_at)
    _require_canonical_string("config_version", report.config_version)
    _require_canonical_string("source_config_version", report.source_config_version)
    if source_generated_at > generated_at:
        raise ValueError("source generated_at must not be after generated_at")
    for field_name in (
        "input_row_count",
        "packet_row_count",
        "included_count",
        "skipped_count",
        "high_priority_count",
        "medium_priority_count",
        "low_priority_count",
        "source_age_seconds",
        "check_count",
        "pass_count",
        "watch_count",
        "blocked_count",
    ):
        _require_nonnegative_int(field_name, getattr(report, field_name))
    if report.source_age_seconds != _timedelta_seconds(
        generated_at - source_generated_at,
    ):
        raise ValueError("source_age_seconds must match generated_at and source_generated_at")
    if report.packet_row_count != report.included_count + report.skipped_count:
        raise ValueError("packet_row_count must match included_count and skipped_count")
    if report.input_row_count < report.packet_row_count:
        raise ValueError("input_row_count must cover packet_row_count")
    if (
        report.high_priority_count
        + report.medium_priority_count
        + report.low_priority_count
        != report.included_count
    ):
        raise ValueError("priority counts must match included_count")
    if report.packet_row_count == 0:
        if report.included_share is not None:
            raise ValueError("included_share must be None when packet_row_count is zero")
        if report.skipped_share is not None:
            raise ValueError("skipped_share must be None when packet_row_count is zero")
    else:
        if report.included_share != _ratio(report.included_count, report.packet_row_count):
            raise ValueError("included_share must match packet_row_count")
        if report.skipped_share != _ratio(report.skipped_count, report.packet_row_count):
            raise ValueError("skipped_share must match packet_row_count")
    check_rows = _normalize_source_check_rows(report.check_rows)
    if tuple(row.check_name for row in check_rows) != CHECK_NAMES:
        raise ValueError("check_rows must be deterministic")
    if report.check_count != len(check_rows):
        raise ValueError("check_count must match check_rows")
    if report.pass_count != _count_check_status(check_rows, "pass"):
        raise ValueError("pass_count must match check_rows")
    if report.watch_count != _count_check_status(check_rows, "watch"):
        raise ValueError("watch_count must match check_rows")
    if report.blocked_count != _count_check_status(check_rows, "blocked"):
        raise ValueError("blocked_count must match check_rows")
    if report.check_count != report.pass_count + report.watch_count + report.blocked_count:
        raise ValueError("check_count must match status counts")
    if report.quality_status != _quality_status_from_rows(check_rows):
        raise ValueError("quality_status must match check_rows")
    reason_code_counts = _normalize_reason_code_counts(report.reason_code_counts)
    if report.reason_code_counts != reason_code_counts:
        raise ValueError("reason_code_counts must be deterministic")


def _validate_report_consistency(report: PaperResearchPacketQualityHistoryReport) -> None:
    if report.source_report_count == 0:
        if report.first_source_generated_at is not None:
            raise ValueError("first_source_generated_at must be absent without reports")
        if report.latest_source_generated_at is not None:
            raise ValueError("latest_source_generated_at must be absent without reports")
        if report.latest_quality_status is not None:
            raise ValueError("latest_quality_status must be absent without reports")
        if report.latest_source_age_seconds is not None:
            raise ValueError("latest_source_age_seconds must be absent without reports")
        if report.latest_included_share is not None:
            raise ValueError("latest_included_share must be absent without reports")
        if report.latest_skipped_share is not None:
            raise ValueError("latest_skipped_share must be absent without reports")
        if report.latest_check_rows:
            raise ValueError("latest_check_rows must be absent without reports")
    else:
        if report.first_source_generated_at is None or report.latest_source_generated_at is None:
            raise ValueError("source generated_at bounds are required with reports")
        if report.first_source_generated_at > report.latest_source_generated_at:
            raise ValueError("source generated_at bounds must be chronological")
        if report.latest_quality_status is None:
            raise ValueError("latest_quality_status is required with reports")
        _require_quality_status("latest_quality_status", report.latest_quality_status)
        if report.latest_source_age_seconds is None:
            raise ValueError("latest_source_age_seconds is required with reports")
        _require_nonnegative_int("latest_source_age_seconds", report.latest_source_age_seconds)
        if report.latest_included_share is not None:
            _require_decimal("latest_included_share", report.latest_included_share)
        if report.latest_skipped_share is not None:
            _require_decimal("latest_skipped_share", report.latest_skipped_share)
        if tuple(row.check_name for row in report.latest_check_rows) != CHECK_NAMES:
            raise ValueError("latest_check_rows must be deterministic")
        if report.latest_quality_status != _quality_status_from_rows(report.latest_check_rows):
            raise ValueError("latest_quality_status must match latest_check_rows")
    if report.quality_status_rows != tuple(
        PaperResearchPacketQualityHistoryStatusRow(
            quality_status,
            _count_for_status(report.quality_status_rows, quality_status),
        )
        for quality_status in QUALITY_STATUSES
    ):
        raise ValueError("quality_status_rows must be deterministic")
    if report.source_report_count != sum(row.status_count for row in report.quality_status_rows):
        raise ValueError("quality_status_rows must match source_report_count")
    if report.quality_status_rows != tuple(
        sorted(
            report.quality_status_rows,
            key=lambda row: STATUS_RANK[row.quality_status],
        )
    ):
        raise ValueError("quality_status_rows must be deterministic")
    if report.duplicate_generated_at_count < 0:
        raise ValueError("duplicate_generated_at_count must be nonnegative")
    if report.recurring_reason_code_rows != tuple(
        sorted(
            report.recurring_reason_code_rows,
            key=lambda row: _recurring_reason_code_sort_key(
                (row.check_status, row.reason_code),
            ),
        )
    ):
        raise ValueError("recurring_reason_code_rows must be deterministic")
    if report.reason_codes != tuple(sorted(report.reason_codes)):
        raise ValueError("reason_codes must be deterministic")
    if len(set(report.reason_codes)) != len(report.reason_codes):
        raise ValueError("reason_codes must not contain duplicate values")
    if not report.reason_codes:
        raise ValueError("reason_codes must not be empty")


def _normalize_history_check_rows(
    rows: object,
) -> tuple[PaperResearchPacketQualityHistoryCheckSummaryRow, ...]:
    normalized = _normalize_tuple(rows, "latest_check_rows")
    for row in normalized:
        if type(row) is not PaperResearchPacketQualityHistoryCheckSummaryRow:
            raise ValueError(
                "latest_check_rows must contain PaperResearchPacketQualityHistoryCheckSummaryRow values",
            )
        _validate_hard_flags("check summary row", row)
    return normalized


def _normalize_source_check_rows(
    rows: object,
) -> tuple[PaperResearchPacketQualityCheckRow, ...]:
    normalized = _normalize_tuple(rows, "check_rows")
    for row in normalized:
        if type(row) is not PaperResearchPacketQualityCheckRow:
            raise ValueError("check_rows must contain PaperResearchPacketQualityCheckRow values")
        _validate_hard_flags("check row", row)
    return normalized


def _normalize_quality_status_rows(
    rows: object,
) -> tuple[PaperResearchPacketQualityHistoryStatusRow, ...]:
    normalized = _normalize_tuple(rows, "quality_status_rows")
    for row in normalized:
        if type(row) is not PaperResearchPacketQualityHistoryStatusRow:
            raise ValueError(
                "quality_status_rows must contain PaperResearchPacketQualityHistoryStatusRow values",
            )
        _validate_hard_flags("status row", row)
    return normalized


def _normalize_recurring_reason_code_rows(
    rows: object,
) -> tuple[PaperResearchPacketQualityHistoryRecurringReasonCodeRow, ...]:
    normalized = _normalize_tuple(rows, "recurring_reason_code_rows")
    for row in normalized:
        if type(row) is not PaperResearchPacketQualityHistoryRecurringReasonCodeRow:
            raise ValueError(
                "recurring_reason_code_rows must contain "
                "PaperResearchPacketQualityHistoryRecurringReasonCodeRow values",
            )
        _validate_hard_flags("recurring reason row", row)
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[PaperResearchPacketQualityReasonCodeCount, ...]:
    normalized = _normalize_tuple(rows, "reason_code_counts")
    for row in normalized:
        if type(row) is not PaperResearchPacketQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain PaperResearchPacketQualityReasonCodeCount values",
            )
        _validate_hard_flags("reason count row", row)
    sorted_rows = tuple(sorted(normalized, key=lambda row: (-row.count, row.reason_code)))
    if normalized != sorted_rows:
        raise ValueError("reason_code_counts must be deterministic")
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    normalized = _normalize_tuple(value, field_name)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in normalized:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate values")
        seen.add(reason_code)
    if normalized != tuple(sorted(normalized)):
        raise ValueError(f"{field_name} must be deterministic")
    return normalized


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal(field_name, value)


def _normalize_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        return tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc


def _quality_status_from_rows(
    rows: tuple[PaperResearchPacketQualityHistoryCheckSummaryRow, ...],
) -> str:
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _count_check_status(
    rows: tuple[PaperResearchPacketQualityHistoryCheckSummaryRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _quality_status_sort_key(row: PaperResearchPacketQualityHistoryStatusRow) -> int:
    return STATUS_RANK[row.quality_status]


def _recurring_reason_code_sort_key(item: tuple[str, str]) -> tuple[int, str]:
    check_status, reason_code = item
    return RECURRING_STATUS_RANK[check_status], reason_code


def _validate_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _timedelta_seconds(value: timedelta) -> int:
    if value < timedelta(0):
        raise ValueError("source generated_at must not be after generated_at")
    return value.days * 86_400 + value.seconds


def _ratio(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(count) / Decimal(total)).quantize(QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


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


def _require_quality_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_check_name(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in CHECK_NAMES:
        raise ValueError(f"{field_name} must be a known quality check")


def _require_recurring_check_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RECURRING_STATUSES:
        raise ValueError(f"{field_name} must be watch or blocked")
