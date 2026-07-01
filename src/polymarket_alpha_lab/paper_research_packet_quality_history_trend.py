"""Pure trend reducer for paper research packet quality history reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.paper_research_packet_quality import QUALITY_STATUSES
from polymarket_alpha_lab.paper_research_packet_quality_history import (
    PaperResearchPacketQualityHistoryCheckSummaryRow,
    PaperResearchPacketQualityHistoryRecurringReasonCodeRow,
    PaperResearchPacketQualityHistoryReport,
)


DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_HISTORY_TREND_CONFIG_VERSION = (
    "paper-research-packet-quality-history-trend-v0"
)
TREND_STATUSES = ("stable", "watch", "blocked")
RECURRING_STATUSES = ("blocked", "watch")
HISTORY_STATUS_RANK = {"pass": 0, "watch": 1, "blocked": 2}
RECURRING_STATUS_RANK = {"blocked": 0, "watch": 1}
PASS_REASON_CODE = "paper_research_packet_quality_history_trend_stable"
BLOCKED_REASON_CODES = frozenset(
    (
        "insufficient_paper_research_packet_quality_history_trend",
        "missing_latest_quality_history_report",
        "blocked_quality_history_report_threshold_exceeded",
        "latest_quality_history_blocked",
        "latest_quality_blocked",
        "consecutive_quality_history_blocked_threshold_exceeded",
        "recurring_blocked_quality_reason_codes_present",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "watch_quality_history_report_threshold_exceeded",
        "latest_quality_history_watch",
        "latest_quality_watch",
        "consecutive_quality_history_watch_threshold_exceeded",
        "duplicate_quality_history_generated_at_threshold_exceeded",
        "recurring_watch_quality_reason_codes_present",
        "stale_quality_history_trend",
    ),
)
ALLOWED_REASON_CODES = BLOCKED_REASON_CODES | WATCH_REASON_CODES | {PASS_REASON_CODE}

__all__ = (
    "DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_HISTORY_TREND_CONFIG_VERSION",
    "PaperResearchPacketQualityHistoryTrendConfig",
    "PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow",
    "PaperResearchPacketQualityHistoryTrendReport",
    "PaperResearchPacketQualityHistoryTrendStatusRow",
    "build_paper_research_packet_quality_history_trend_report",
)


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryTrendConfig:
    config_version: str = (
        DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_HISTORY_TREND_CONFIG_VERSION
    )
    min_history_report_count: int = 3
    max_latest_history_age_seconds: int = 86_400
    max_blocked_history_report_count: int = 0
    max_watch_history_report_count: int = 0
    max_consecutive_latest_watch_count: int = 0
    max_consecutive_latest_blocked_count: int = 0
    max_duplicate_generated_at_count: int = 0
    max_recurring_reason_code_history_report_count: int = 1
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_history_report_count",
            "max_latest_history_age_seconds",
            "max_blocked_history_report_count",
            "max_watch_history_report_count",
            "max_consecutive_latest_watch_count",
            "max_consecutive_latest_blocked_count",
            "max_duplicate_generated_at_count",
            "max_recurring_reason_code_history_report_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryTrendStatusRow:
    history_status: str
    status_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_quality_status("history_status", self.history_status)
        _require_nonnegative_int("status_count", self.status_count)
        _validate_hard_flags("status row", self)


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow:
    check_status: str
    reason_code: str
    history_report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_recurring_status("check_status", self.check_status)
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("history_report_count", self.history_report_count)
        _validate_hard_flags("recurring reason row", self)


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryTrendReport:
    generated_at: datetime
    config_version: str
    trend_status: str
    source_history_report_count: int
    first_history_generated_at: datetime | None
    latest_history_generated_at: datetime | None
    latest_history_age_seconds: int | None
    latest_history_status: str | None
    latest_quality_status: str | None
    history_status_rows: tuple[PaperResearchPacketQualityHistoryTrendStatusRow, ...]
    duplicate_generated_at_count: int
    consecutive_latest_pass_count: int
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    latest_reason_codes: tuple[str, ...]
    recurring_reason_code_rows: tuple[
        PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_trend_status("trend_status", self.trend_status)
        _require_nonnegative_int(
            "source_history_report_count",
            self.source_history_report_count,
        )
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
        _require_optional_nonnegative_int(
            "latest_history_age_seconds",
            self.latest_history_age_seconds,
        )
        if self.latest_history_status is not None:
            _require_quality_status("latest_history_status", self.latest_history_status)
        if self.latest_quality_status is not None:
            _require_quality_status("latest_quality_status", self.latest_quality_status)
        object.__setattr__(
            self,
            "history_status_rows",
            _normalize_status_rows(self.history_status_rows),
        )
        for field_name in (
            "duplicate_generated_at_count",
            "consecutive_latest_pass_count",
            "consecutive_latest_watch_count",
            "consecutive_latest_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_reason_codes",
            _normalize_reason_codes(
                "latest_reason_codes",
                self.latest_reason_codes,
                allow_empty=True,
                allowed_reason_codes=None,
            ),
        )
        object.__setattr__(
            self,
            "recurring_reason_code_rows",
            _normalize_recurring_reason_code_rows(self.recurring_reason_code_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed_reason_codes=ALLOWED_REASON_CODES,
            ),
        )
        _validate_trend_report(self)
        _validate_hard_flags("trend report", self)


def build_paper_research_packet_quality_history_trend_report(
    history_reports: object,
    *,
    config: PaperResearchPacketQualityHistoryTrendConfig,
    generated_at: datetime,
) -> PaperResearchPacketQualityHistoryTrendReport:
    if type(config) is not PaperResearchPacketQualityHistoryTrendConfig:
        raise ValueError(
            "config must be a PaperResearchPacketQualityHistoryTrendConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _validate_hard_flags("config", config)

    generated_at_utc = _as_utc("generated_at", generated_at)
    reports = _normalize_history_reports(history_reports)
    chronological_reports = _chronological_reports(reports)
    status_rows = _history_status_rows(chronological_reports)
    duplicate_generated_at_count = _duplicate_generated_at_count(chronological_reports)
    recurring_reason_code_rows = _recurring_reason_code_rows(
        chronological_reports,
        max_recurring_reason_code_history_report_count=(
            config.max_recurring_reason_code_history_report_count
        ),
    )
    latest = chronological_reports[-1] if chronological_reports else None
    latest_history_generated_at = (
        _as_utc("history_report.generated_at", latest.generated_at)
        if latest is not None
        else None
    )
    latest_history_age_seconds = _latest_history_age_seconds(
        generated_at_utc,
        latest_history_generated_at,
    )
    reason_codes = _trend_reason_codes(
        reports=chronological_reports,
        status_rows=status_rows,
        duplicate_generated_at_count=duplicate_generated_at_count,
        recurring_reason_code_rows=recurring_reason_code_rows,
        latest_history_age_seconds=latest_history_age_seconds,
        config=config,
    )
    return PaperResearchPacketQualityHistoryTrendReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        trend_status=_trend_status(reason_codes),
        source_history_report_count=len(chronological_reports),
        first_history_generated_at=(
            _as_utc("history_report.generated_at", chronological_reports[0].generated_at)
            if chronological_reports
            else None
        ),
        latest_history_generated_at=latest_history_generated_at,
        latest_history_age_seconds=latest_history_age_seconds,
        latest_history_status=latest.history_status if latest is not None else None,
        latest_quality_status=latest.latest_quality_status if latest is not None else None,
        history_status_rows=status_rows,
        duplicate_generated_at_count=duplicate_generated_at_count,
        consecutive_latest_pass_count=_consecutive_latest_status_count(
            chronological_reports,
            "pass",
        ),
        consecutive_latest_watch_count=_consecutive_latest_status_count(
            chronological_reports,
            "watch",
        ),
        consecutive_latest_blocked_count=_consecutive_latest_status_count(
            chronological_reports,
            "blocked",
        ),
        latest_reason_codes=latest.reason_codes if latest is not None else (),
        recurring_reason_code_rows=recurring_reason_code_rows,
        reason_codes=reason_codes,
    )


def _normalize_history_reports(
    value: object,
) -> tuple[PaperResearchPacketQualityHistoryReport, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("history_reports must be a list or tuple")
    reports = tuple(value)
    for report in reports:
        if type(report) is not PaperResearchPacketQualityHistoryReport:
            raise ValueError(
                "history_reports must contain PaperResearchPacketQualityHistoryReport values",
            )
        _validate_history_report(report)
    return reports


def _chronological_reports(
    reports: tuple[PaperResearchPacketQualityHistoryReport, ...],
) -> tuple[PaperResearchPacketQualityHistoryReport, ...]:
    return tuple(
        report
        for _, report in sorted(
            enumerate(reports),
            key=lambda item: (
                _as_utc("history_report.generated_at", item[1].generated_at),
                item[0],
            ),
        )
    )


def _history_status_rows(
    reports: tuple[PaperResearchPacketQualityHistoryReport, ...],
) -> tuple[PaperResearchPacketQualityHistoryTrendStatusRow, ...]:
    return tuple(
        PaperResearchPacketQualityHistoryTrendStatusRow(
            history_status,
            sum(1 for report in reports if report.history_status == history_status),
        )
        for history_status in QUALITY_STATUSES
    )


def _duplicate_generated_at_count(
    reports: tuple[PaperResearchPacketQualityHistoryReport, ...],
) -> int:
    counts: dict[datetime, int] = {}
    for report in reports:
        generated_at = _as_utc("history_report.generated_at", report.generated_at)
        counts[generated_at] = counts.get(generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _consecutive_latest_status_count(
    reports: tuple[PaperResearchPacketQualityHistoryReport, ...],
    history_status: str,
) -> int:
    if not reports or reports[-1].history_status != history_status:
        return 0
    count = 0
    for report in reversed(reports):
        if report.history_status != history_status:
            break
        count += 1
    return count


def _recurring_reason_code_rows(
    reports: tuple[PaperResearchPacketQualityHistoryReport, ...],
    *,
    max_recurring_reason_code_history_report_count: int,
) -> tuple[PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow, ...]:
    counts: dict[tuple[str, str], int] = {}
    for report in reports:
        seen_for_report: set[tuple[str, str]] = set()
        for row in report.recurring_reason_code_rows:
            key = (row.check_status, row.reason_code)
            if key in seen_for_report:
                continue
            seen_for_report.add(key)
            counts[key] = counts.get(key, 0) + 1
    return tuple(
        PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow(
            check_status,
            reason_code,
            history_report_count,
        )
        for (check_status, reason_code), history_report_count in sorted(
            counts.items(),
            key=lambda item: _recurring_reason_code_sort_key(item[0]),
        )
        if history_report_count > max_recurring_reason_code_history_report_count
    )


def _trend_reason_codes(
    *,
    reports: tuple[PaperResearchPacketQualityHistoryReport, ...],
    status_rows: tuple[PaperResearchPacketQualityHistoryTrendStatusRow, ...],
    duplicate_generated_at_count: int,
    recurring_reason_code_rows: tuple[
        PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow,
        ...,
    ],
    latest_history_age_seconds: int | None,
    config: PaperResearchPacketQualityHistoryTrendConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    latest = reports[-1] if reports else None

    if len(reports) < config.min_history_report_count:
        reason_codes.append("insufficient_paper_research_packet_quality_history_trend")
    if latest is None:
        reason_codes.append("missing_latest_quality_history_report")
    if _count_for_status(status_rows, "blocked") > config.max_blocked_history_report_count:
        reason_codes.append("blocked_quality_history_report_threshold_exceeded")
    if latest is not None and latest.history_status == "blocked":
        reason_codes.append("latest_quality_history_blocked")
    if latest is not None and latest.latest_quality_status == "blocked":
        reason_codes.append("latest_quality_blocked")
    if (
        _consecutive_latest_status_count(reports, "blocked")
        > config.max_consecutive_latest_blocked_count
    ):
        reason_codes.append("consecutive_quality_history_blocked_threshold_exceeded")
    if any(row.check_status == "blocked" for row in recurring_reason_code_rows):
        reason_codes.append("recurring_blocked_quality_reason_codes_present")

    if _count_for_status(status_rows, "watch") > config.max_watch_history_report_count:
        reason_codes.append("watch_quality_history_report_threshold_exceeded")
    if latest is not None and latest.history_status == "watch":
        reason_codes.append("latest_quality_history_watch")
    if latest is not None and latest.latest_quality_status == "watch":
        reason_codes.append("latest_quality_watch")
    if (
        _consecutive_latest_status_count(reports, "watch")
        > config.max_consecutive_latest_watch_count
    ):
        reason_codes.append("consecutive_quality_history_watch_threshold_exceeded")
    if duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        reason_codes.append("duplicate_quality_history_generated_at_threshold_exceeded")
    if any(row.check_status == "watch" for row in recurring_reason_code_rows):
        reason_codes.append("recurring_watch_quality_reason_codes_present")
    if (
        latest_history_age_seconds is not None
        and latest_history_age_seconds > config.max_latest_history_age_seconds
    ):
        reason_codes.append("stale_quality_history_trend")

    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(sorted(set(reason_codes)))


def _trend_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "stable"


def _latest_history_age_seconds(
    generated_at: datetime,
    latest_history_generated_at: datetime | None,
) -> int | None:
    if latest_history_generated_at is None:
        return None
    age_seconds = int(
        (
            _as_utc("generated_at", generated_at)
            - _as_utc("latest_history_generated_at", latest_history_generated_at)
        ).total_seconds(),
    )
    if age_seconds < 0:
        raise ValueError("latest_history_age_seconds must be nonnegative")
    return age_seconds


def _count_for_status(
    rows: tuple[PaperResearchPacketQualityHistoryTrendStatusRow, ...],
    history_status: str,
) -> int:
    for row in rows:
        if row.history_status == history_status:
            return row.status_count
    return 0


def _validate_history_report(report: PaperResearchPacketQualityHistoryReport) -> None:
    _validate_hard_flags("history report", report)
    _require_canonical_string("source config_version", report.config_version)
    _require_quality_status("source history_status", report.history_status)
    _require_nonnegative_int("source source_history_report_count", report.source_report_count)
    _as_utc("source generated_at", report.generated_at)
    for row in report.latest_check_rows:
        if type(row) is not PaperResearchPacketQualityHistoryCheckSummaryRow:
            raise ValueError("latest_check_rows must contain exact quality history rows")
        _validate_hard_flags("latest check row", row)
    for row in report.recurring_reason_code_rows:
        if type(row) is not PaperResearchPacketQualityHistoryRecurringReasonCodeRow:
            raise ValueError("recurring_reason_code_rows must contain exact recurring rows")
        _validate_hard_flags("recurring reason row", row)
    _normalize_reason_codes(
        "source reason_codes",
        report.reason_codes,
        allowed_reason_codes=None,
    )


def _validate_trend_report(
    report: PaperResearchPacketQualityHistoryTrendReport,
) -> None:
    if report.source_history_report_count == 0:
        _validate_empty_trend_report(report)
    else:
        _validate_nonempty_trend_report(report)
    _validate_status_rows(report)
    _validate_consecutive_latest_counts(report)
    if report.reason_codes != tuple(sorted(report.reason_codes)):
        raise ValueError("reason_codes must be sorted")
    if report.trend_status != _trend_status(report.reason_codes):
        raise ValueError("trend_status must match reason_codes")
    has_pass_reason = PASS_REASON_CODE in report.reason_codes
    has_failure_reason = any(
        reason_code in BLOCKED_REASON_CODES or reason_code in WATCH_REASON_CODES
        for reason_code in report.reason_codes
    )
    if has_pass_reason and has_failure_reason:
        raise ValueError("stable reason must not be mixed with watch or blocked reasons")
    if report.latest_history_generated_at is None:
        if report.latest_history_age_seconds is not None:
            raise ValueError("latest_history_age_seconds requires latest timestamp")
    elif (
        report.latest_history_age_seconds
        != _latest_history_age_seconds(report.generated_at, report.latest_history_generated_at)
    ):
        raise ValueError("latest_history_age_seconds must match latest timestamp")


def _validate_empty_trend_report(
    report: PaperResearchPacketQualityHistoryTrendReport,
) -> None:
    if report.first_history_generated_at is not None:
        raise ValueError("first_history_generated_at must be absent without reports")
    if report.latest_history_generated_at is not None:
        raise ValueError("latest_history_generated_at must be absent without reports")
    if report.latest_history_status is not None:
        raise ValueError("latest_history_status must be absent without reports")
    if report.latest_quality_status is not None:
        raise ValueError("latest_quality_status must be absent without reports")
    if report.latest_reason_codes:
        raise ValueError("latest_reason_codes must be absent without reports")
    if report.recurring_reason_code_rows:
        raise ValueError("recurring_reason_code_rows must be absent without reports")
    for field_name in (
        "duplicate_generated_at_count",
        "consecutive_latest_pass_count",
        "consecutive_latest_watch_count",
        "consecutive_latest_blocked_count",
    ):
        if getattr(report, field_name) != 0:
            raise ValueError(f"{field_name} must be zero without reports")


def _validate_nonempty_trend_report(
    report: PaperResearchPacketQualityHistoryTrendReport,
) -> None:
    if report.first_history_generated_at is None:
        raise ValueError("first_history_generated_at is required with reports")
    if report.latest_history_generated_at is None:
        raise ValueError("latest_history_generated_at is required with reports")
    if report.first_history_generated_at > report.latest_history_generated_at:
        raise ValueError("history generated_at bounds must be chronological")
    if report.latest_history_status is None:
        raise ValueError("latest_history_status is required with reports")
    if report.latest_quality_status is None:
        raise ValueError("latest_quality_status is required with reports")
    if not report.latest_reason_codes:
        raise ValueError("latest_reason_codes is required with reports")
    if _count_for_status(report.history_status_rows, report.latest_history_status) <= 0:
        raise ValueError("history_status_rows must cover latest_history_status")


def _validate_status_rows(report: PaperResearchPacketQualityHistoryTrendReport) -> None:
    rows = report.history_status_rows
    if type(rows) is not tuple or len(rows) != len(QUALITY_STATUSES):
        raise ValueError("history_status_rows must cover pass, watch, and blocked")
    if tuple(row.history_status for row in rows) != QUALITY_STATUSES:
        raise ValueError("history_status_rows must be pass, watch, blocked")
    if report.source_history_report_count != sum(row.status_count for row in rows):
        raise ValueError("history_status_rows must match source_history_report_count")
    expected_rows = tuple(
        PaperResearchPacketQualityHistoryTrendStatusRow(
            history_status,
            _count_for_status(rows, history_status),
        )
        for history_status in QUALITY_STATUSES
    )
    if rows != expected_rows:
        raise ValueError("history_status_rows must be deterministic")


def _validate_consecutive_latest_counts(
    report: PaperResearchPacketQualityHistoryTrendReport,
) -> None:
    fields_by_status = {
        "pass": "consecutive_latest_pass_count",
        "watch": "consecutive_latest_watch_count",
        "blocked": "consecutive_latest_blocked_count",
    }
    for history_status, field_name in fields_by_status.items():
        count = getattr(report, field_name)
        if report.latest_history_status == history_status:
            if report.source_history_report_count > 0 and count == 0:
                raise ValueError(f"{field_name} must be positive for latest status")
            if count > report.source_history_report_count:
                raise ValueError(f"{field_name} must not exceed source count")
            if count > _count_for_status(report.history_status_rows, history_status):
                raise ValueError(f"{field_name} must not exceed status count")
        elif count != 0:
            raise ValueError(f"{field_name} must be zero unless it is the latest status")


def _normalize_status_rows(
    rows: object,
) -> tuple[PaperResearchPacketQualityHistoryTrendStatusRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("history_status_rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not PaperResearchPacketQualityHistoryTrendStatusRow:
            raise ValueError("history_status_rows must contain exact status rows")
        _validate_hard_flags("status row", row)
    return normalized


def _normalize_recurring_reason_code_rows(
    rows: object,
) -> tuple[PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("recurring_reason_code_rows must be a tuple")
    normalized = tuple(rows)
    previous_key: tuple[int, str] | None = None
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow:
            raise ValueError("recurring_reason_code_rows must contain exact recurring rows")
        _validate_hard_flags("recurring reason row", row)
        key = _recurring_reason_code_sort_key((row.check_status, row.reason_code))
        if previous_key is not None and previous_key > key:
            raise ValueError("recurring_reason_code_rows must be deterministic")
        source_key = (row.check_status, row.reason_code)
        if source_key in seen:
            raise ValueError("recurring_reason_code_rows must be unique")
        seen.add(source_key)
        previous_key = key
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
    allowed_reason_codes: frozenset[str] | None = ALLOWED_REASON_CODES,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    codes = tuple(value)
    if not codes and not allow_empty:
        raise ValueError(f"{field_name} is required")
    previous: str | None = None
    seen: set[str] = set()
    for code in codes:
        _require_canonical_string(field_name, code)
        if allowed_reason_codes is not None and code not in allowed_reason_codes:
            raise ValueError(f"{field_name} must match trend semantics")
        if code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > code:
            raise ValueError(f"{field_name} must be sorted")
        seen.add(code)
        previous = code
    return codes


def _recurring_reason_code_sort_key(item: tuple[str, str]) -> tuple[int, str]:
    check_status, reason_code = item
    return RECURRING_STATUS_RANK[check_status], reason_code


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


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_trend_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TREND_STATUSES:
        raise ValueError(f"{field_name} must be stable, watch, or blocked")


def _require_quality_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_recurring_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RECURRING_STATUSES:
        raise ValueError(f"{field_name} must be watch or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")
