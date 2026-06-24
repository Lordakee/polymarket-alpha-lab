"""Pure read-only history reducer for paper allocation proposal reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_autonomous_allocation_proposal import (
    PROPOSAL_STATUSES,
    PaperAutonomousAllocationProposalReport,
)


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION",
    "PaperAutonomousAllocationProposalDbHistoryConfig",
    "PaperAutonomousAllocationProposalDbHistoryReasonCodeRow",
    "PaperAutonomousAllocationProposalDbHistoryReport",
    "PaperAutonomousAllocationProposalDbHistoryStatusRow",
    "build_paper_autonomous_allocation_proposal_db_history_report",
)


DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION = (
    "paper-autonomous-allocation-proposal-db-history-v0"
)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryConfig:
    config_version: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION
    )
    min_report_count: int = 3
    max_blocked_proposal_report_count: int = 0
    max_watch_proposal_report_count: int = 0
    max_duplicate_generated_at_count: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_report_count", self.min_report_count)
        for field_name in (
            "max_blocked_proposal_report_count",
            "max_watch_proposal_report_count",
            "max_duplicate_generated_at_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryStatusRow:
    proposal_status: str
    status_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_proposal_status("proposal_status", self.proposal_status)
        _require_nonnegative_int("status_count", self.status_count)
        _require_hard_flags("status row", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryReasonCodeRow:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _require_hard_flags("reason code row", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryReport:
    generated_at: datetime
    config_version: str
    history_status: str
    report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_proposal_status: str | None
    latest_screening_gate_status: str | None
    latest_queue_risk_status: str | None
    latest_allocation_input_count: int | None
    latest_allocation_row_count: int | None
    latest_allocated_count: int | None
    latest_total_allocated_paper_notional: Decimal | None
    proposal_status_rows: tuple[
        PaperAutonomousAllocationProposalDbHistoryStatusRow,
        ...,
    ]
    duplicate_generated_at_count: int
    consecutive_latest_pass_count: int
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    latest_reason_codes: tuple[str, ...]
    reason_code_rows: tuple[
        PaperAutonomousAllocationProposalDbHistoryReasonCodeRow,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_proposal_status("history_status", self.history_status)
        _require_nonnegative_int("report_count", self.report_count)
        object.__setattr__(
            self,
            "first_report_generated_at",
            _as_optional_utc(
                "first_report_generated_at",
                self.first_report_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_report_generated_at",
            _as_optional_utc(
                "latest_report_generated_at",
                self.latest_report_generated_at,
            ),
        )
        if self.latest_proposal_status is not None:
            _require_proposal_status("latest_proposal_status", self.latest_proposal_status)
        if self.latest_screening_gate_status is not None:
            _require_proposal_status(
                "latest_screening_gate_status",
                self.latest_screening_gate_status,
            )
        if self.latest_queue_risk_status is not None:
            _require_proposal_status(
                "latest_queue_risk_status",
                self.latest_queue_risk_status,
            )
        for field_name in (
            "latest_allocation_input_count",
            "latest_allocation_row_count",
            "latest_allocated_count",
        ):
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        _require_optional_decimal(
            "latest_total_allocated_paper_notional",
            self.latest_total_allocated_paper_notional,
        )
        object.__setattr__(
            self,
            "proposal_status_rows",
            _normalize_status_rows(self.proposal_status_rows),
        )
        _require_nonnegative_int(
            "duplicate_generated_at_count",
            self.duplicate_generated_at_count,
        )
        for field_name in (
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
            ),
        )
        object.__setattr__(
            self,
            "reason_code_rows",
            _normalize_reason_code_rows(self.reason_code_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_history_report(self)
        _require_hard_flags("history report", self)


def build_paper_autonomous_allocation_proposal_db_history_report(
    proposal_reports: object,
    *,
    config: PaperAutonomousAllocationProposalDbHistoryConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryReport:
    if type(config) is not PaperAutonomousAllocationProposalDbHistoryConfig:
        raise ValueError(
            "config must be a PaperAutonomousAllocationProposalDbHistoryConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("config", config)

    reports = _normalize_proposal_reports(proposal_reports)
    chronological_reports = _chronological_reports(reports)
    status_rows = _proposal_status_rows(chronological_reports)
    duplicate_generated_at_count = _duplicate_generated_at_count(
        chronological_reports,
    )
    latest = chronological_reports[-1] if chronological_reports else None
    allocation_report = latest.allocation_report if latest is not None else None

    return PaperAutonomousAllocationProposalDbHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        history_status=_history_status(
            report_count=len(chronological_reports),
            proposal_status_rows=status_rows,
            duplicate_generated_at_count=duplicate_generated_at_count,
            config=config,
        ),
        report_count=len(chronological_reports),
        first_report_generated_at=(
            _as_utc("report generated_at", chronological_reports[0].generated_at)
            if chronological_reports
            else None
        ),
        latest_report_generated_at=(
            _as_utc("report generated_at", latest.generated_at)
            if latest is not None
            else None
        ),
        latest_proposal_status=latest.proposal_status if latest is not None else None,
        latest_screening_gate_status=(
            latest.screening_gate_status if latest is not None else None
        ),
        latest_queue_risk_status=latest.queue_risk_status if latest is not None else None,
        latest_allocation_input_count=(
            latest.allocation_input_count if latest is not None else None
        ),
        latest_allocation_row_count=(
            allocation_report.row_count if allocation_report is not None else None
        ),
        latest_allocated_count=(
            allocation_report.allocated_count if allocation_report is not None else None
        ),
        latest_total_allocated_paper_notional=(
            allocation_report.total_allocated_paper_notional
            if allocation_report is not None
            else None
        ),
        proposal_status_rows=status_rows,
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
        reason_code_rows=_reason_code_rows(chronological_reports),
        reason_codes=_history_reason_codes(
            report_count=len(chronological_reports),
            proposal_status_rows=status_rows,
            duplicate_generated_at_count=duplicate_generated_at_count,
            config=config,
        ),
    )


def _normalize_proposal_reports(
    value: object,
) -> tuple[PaperAutonomousAllocationProposalReport, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("proposal_reports must be a list or tuple")
    reports = tuple(value)
    for report in reports:
        if type(report) is not PaperAutonomousAllocationProposalReport:
            raise ValueError(
                "proposal_reports must contain "
                "PaperAutonomousAllocationProposalReport values",
            )
        _validate_proposal_report(report)
    return reports


def _chronological_reports(
    reports: tuple[PaperAutonomousAllocationProposalReport, ...],
) -> tuple[PaperAutonomousAllocationProposalReport, ...]:
    return tuple(
        report
        for _, report in sorted(
            enumerate(reports),
            key=lambda item: (_as_utc("report generated_at", item[1].generated_at), item[0]),
        )
    )


def _proposal_status_rows(
    reports: tuple[PaperAutonomousAllocationProposalReport, ...],
) -> tuple[PaperAutonomousAllocationProposalDbHistoryStatusRow, ...]:
    return tuple(
        PaperAutonomousAllocationProposalDbHistoryStatusRow(
            proposal_status,
            sum(1 for report in reports if report.proposal_status == proposal_status),
        )
        for proposal_status in PROPOSAL_STATUSES
    )


def _duplicate_generated_at_count(
    reports: tuple[PaperAutonomousAllocationProposalReport, ...],
) -> int:
    counts: dict[datetime, int] = {}
    for report in reports:
        generated_at = _as_utc("report generated_at", report.generated_at)
        counts[generated_at] = counts.get(generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _consecutive_latest_status_count(
    reports: tuple[PaperAutonomousAllocationProposalReport, ...],
    proposal_status: str,
) -> int:
    if not reports or reports[-1].proposal_status != proposal_status:
        return 0
    count = 0
    for report in reversed(reports):
        if report.proposal_status != proposal_status:
            break
        count += 1
    return count


def _reason_code_rows(
    reports: tuple[PaperAutonomousAllocationProposalReport, ...],
) -> tuple[PaperAutonomousAllocationProposalDbHistoryReasonCodeRow, ...]:
    counts: dict[str, int] = {}
    for report in reports:
        for reason_code in set(report.reason_codes):
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperAutonomousAllocationProposalDbHistoryReasonCodeRow(
            reason_code,
            report_count,
        )
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _history_status(
    *,
    report_count: int,
    proposal_status_rows: tuple[
        PaperAutonomousAllocationProposalDbHistoryStatusRow,
        ...,
    ],
    duplicate_generated_at_count: int,
    config: PaperAutonomousAllocationProposalDbHistoryConfig,
) -> str:
    if report_count < config.min_report_count:
        return "blocked"
    if (
        _count_for_status(proposal_status_rows, "blocked")
        > config.max_blocked_proposal_report_count
    ):
        return "blocked"
    if (
        _count_for_status(proposal_status_rows, "watch")
        > config.max_watch_proposal_report_count
    ):
        return "watch"
    if duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        return "watch"
    return "pass"


def _history_reason_codes(
    *,
    report_count: int,
    proposal_status_rows: tuple[
        PaperAutonomousAllocationProposalDbHistoryStatusRow,
        ...,
    ],
    duplicate_generated_at_count: int,
    config: PaperAutonomousAllocationProposalDbHistoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if report_count < config.min_report_count:
        reason_codes.append(
            "insufficient_paper_autonomous_allocation_proposal_history",
        )
    if (
        _count_for_status(proposal_status_rows, "blocked")
        > config.max_blocked_proposal_report_count
    ):
        reason_codes.append(
            "blocked_allocation_proposal_report_threshold_exceeded",
        )
    if (
        _count_for_status(proposal_status_rows, "watch")
        > config.max_watch_proposal_report_count
    ):
        reason_codes.append(
            "watch_allocation_proposal_report_threshold_exceeded",
        )
    if duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        reason_codes.append("duplicate_generated_at_threshold_exceeded")
    if not reason_codes:
        reason_codes.append("paper_autonomous_allocation_proposal_db_history_passed")
    return tuple(sorted(set(reason_codes)))


def _count_for_status(
    rows: tuple[PaperAutonomousAllocationProposalDbHistoryStatusRow, ...],
    proposal_status: str,
) -> int:
    for row in rows:
        if row.proposal_status == proposal_status:
            return row.status_count
    return 0


def _validate_proposal_report(
    report: PaperAutonomousAllocationProposalReport,
) -> None:
    _require_hard_flags("proposal report", report)
    _require_hard_flags("allocation report", report.allocation_report)
    for row in report.allocation_report.rows:
        _require_hard_flags("allocation row", row)
    for row in report.reason_code_counts:
        _require_hard_flags("reason code count", row)
    for summary in report.source_queue_summaries:
        _require_hard_flags("source queue summary", summary)


def _validate_history_report(
    report: PaperAutonomousAllocationProposalDbHistoryReport,
) -> None:
    if report.report_count == 0:
        _validate_empty_history_report(report)
    else:
        _validate_nonempty_history_report(report)
    if report.proposal_status_rows != tuple(
        PaperAutonomousAllocationProposalDbHistoryStatusRow(
            proposal_status,
            _count_for_status(report.proposal_status_rows, proposal_status),
        )
        for proposal_status in PROPOSAL_STATUSES
    ):
        raise ValueError("proposal_status_rows must be deterministic")
    if report.report_count != sum(row.status_count for row in report.proposal_status_rows):
        raise ValueError("proposal_status_rows must match report_count")
    if report.duplicate_generated_at_count >= max(report.report_count, 1):
        raise ValueError("duplicate_generated_at_count must be below report_count")
    for row in report.reason_code_rows:
        if row.report_count > report.report_count:
            raise ValueError("reason_code_rows report_count must not exceed report_count")
    if report.reason_code_rows != tuple(
        sorted(
            report.reason_code_rows,
            key=lambda row: (-row.report_count, row.reason_code),
        )
    ):
        raise ValueError("reason_code_rows must be deterministic")
    _validate_consecutive_latest_counts(report)


def _validate_empty_history_report(
    report: PaperAutonomousAllocationProposalDbHistoryReport,
) -> None:
    absent_fields = (
        "first_report_generated_at",
        "latest_report_generated_at",
        "latest_proposal_status",
        "latest_screening_gate_status",
        "latest_queue_risk_status",
        "latest_allocation_input_count",
        "latest_allocation_row_count",
        "latest_allocated_count",
        "latest_total_allocated_paper_notional",
    )
    for field_name in absent_fields:
        if getattr(report, field_name) is not None:
            raise ValueError(f"{field_name} must be absent without reports")
    if report.duplicate_generated_at_count != 0:
        raise ValueError("duplicate_generated_at_count must be zero without reports")
    if report.latest_reason_codes:
        raise ValueError("latest_reason_codes must be absent without reports")
    if report.reason_code_rows:
        raise ValueError("reason_code_rows must be absent without reports")
    for field_name in (
        "consecutive_latest_pass_count",
        "consecutive_latest_watch_count",
        "consecutive_latest_blocked_count",
    ):
        if getattr(report, field_name) != 0:
            raise ValueError(f"{field_name} must be zero without reports")


def _validate_nonempty_history_report(
    report: PaperAutonomousAllocationProposalDbHistoryReport,
) -> None:
    required_fields = (
        "first_report_generated_at",
        "latest_report_generated_at",
        "latest_proposal_status",
        "latest_screening_gate_status",
        "latest_queue_risk_status",
        "latest_allocation_input_count",
        "latest_allocation_row_count",
        "latest_allocated_count",
        "latest_total_allocated_paper_notional",
    )
    for field_name in required_fields:
        if getattr(report, field_name) is None:
            raise ValueError(f"{field_name} is required with reports")
    if report.latest_report_generated_at < report.first_report_generated_at:
        raise ValueError("latest_report_generated_at must not precede first report")
    if _count_for_status(report.proposal_status_rows, report.latest_proposal_status) == 0:
        raise ValueError("proposal_status_rows must cover latest_proposal_status")
    if not report.latest_reason_codes:
        raise ValueError("latest_reason_codes is required with reports")
    if not report.reason_code_rows:
        raise ValueError("reason_code_rows is required with reports")


def _validate_consecutive_latest_counts(
    report: PaperAutonomousAllocationProposalDbHistoryReport,
) -> None:
    fields_by_status = {
        "pass": "consecutive_latest_pass_count",
        "watch": "consecutive_latest_watch_count",
        "blocked": "consecutive_latest_blocked_count",
    }
    for proposal_status, field_name in fields_by_status.items():
        count = getattr(report, field_name)
        if report.latest_proposal_status == proposal_status:
            if report.report_count > 0 and count == 0:
                raise ValueError(f"{field_name} must be positive for latest status")
            if count > report.report_count:
                raise ValueError(f"{field_name} must not exceed report_count")
            if count > _count_for_status(report.proposal_status_rows, proposal_status):
                raise ValueError(
                    f"{field_name} must not exceed proposal_status_rows count",
                )
        elif count != 0:
            raise ValueError(f"{field_name} must be zero unless it is the latest status")


def _normalize_status_rows(
    rows: object,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryStatusRow, ...]:
    normalized = _normalize_tuple(rows, "proposal_status_rows")
    for row in normalized:
        if type(row) is not PaperAutonomousAllocationProposalDbHistoryStatusRow:
            raise ValueError(
                "proposal_status_rows must contain "
                "PaperAutonomousAllocationProposalDbHistoryStatusRow values",
            )
        _require_hard_flags("status row", row)
    return normalized


def _normalize_reason_code_rows(
    rows: object,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryReasonCodeRow, ...]:
    normalized = _normalize_tuple(rows, "reason_code_rows")
    for row in normalized:
        if type(row) is not PaperAutonomousAllocationProposalDbHistoryReasonCodeRow:
            raise ValueError(
                "reason_code_rows must contain "
                "PaperAutonomousAllocationProposalDbHistoryReasonCodeRow values",
            )
        _require_hard_flags("reason code row", row)
    reason_codes = tuple(row.reason_code for row in normalized)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_code_rows must not contain duplicate reason codes")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    normalized = _normalize_tuple(value, field_name)
    if not normalized and not allow_empty:
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


def _normalize_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        return tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_proposal_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PROPOSAL_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
