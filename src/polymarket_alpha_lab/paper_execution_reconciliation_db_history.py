"""Pure read-only history reducer for paper execution reconciliation reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_execution_reconciliation import (
    RECONCILIATION_STATUSES,
    PaperExecutionReconciliationReport,
)


__all__ = (
    "DEFAULT_PAPER_EXECUTION_RECONCILIATION_DB_HISTORY_CONFIG_VERSION",
    "PaperExecutionReconciliationDbHistoryConfig",
    "PaperExecutionReconciliationDbHistoryReasonCodeRow",
    "PaperExecutionReconciliationDbHistoryReport",
    "PaperExecutionReconciliationDbHistoryStatusRow",
    "build_paper_execution_reconciliation_db_history_report",
)


DEFAULT_PAPER_EXECUTION_RECONCILIATION_DB_HISTORY_CONFIG_VERSION = (
    "paper-execution-reconciliation-db-history-v0"
)
HISTORY_STATUSES = ("pass", "watch", "blocked")
ZERO = Decimal("0.000000")
NO_POSITION_FIELD_CONCERN = (
    "current PaperExecutionReconciliationReport has no explicit no_position_count field; "
    "history uses total_positions == 0"
)


@dataclass(frozen=True)
class PaperExecutionReconciliationDbHistoryConfig:
    config_version: str = (
        DEFAULT_PAPER_EXECUTION_RECONCILIATION_DB_HISTORY_CONFIG_VERSION
    )
    min_report_count: int = 1
    max_pending_streak: int = 0
    max_discrepancy_streak: int = 0
    max_duplicate_generated_at_count: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperExecutionReconciliationDbHistoryConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperExecutionReconciliationDbHistoryConfig:
            raise ValueError(
                "config must be a PaperExecutionReconciliationDbHistoryConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_report_count", self.min_report_count)
        for field_name in (
            "max_pending_streak",
            "max_discrepancy_streak",
            "max_duplicate_generated_at_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperExecutionReconciliationDbHistoryStatusRow:
    reconciliation_status: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperExecutionReconciliationDbHistoryStatusRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_reconciliation_status(
            "reconciliation_status",
            self.reconciliation_status,
        )
        _require_nonnegative_int("report_count", self.report_count)
        _require_hard_flags("status row", self)


@dataclass(frozen=True)
class PaperExecutionReconciliationDbHistoryReasonCodeRow:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperExecutionReconciliationDbHistoryReasonCodeRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _require_hard_flags("reason code row", self)


@dataclass(frozen=True)
class PaperExecutionReconciliationDbHistoryReport:
    generated_at: datetime
    config_version: str
    history_status: str
    report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    latest_reconciliation_status: str | None
    pending_streak_count: int
    discrepancy_streak_count: int
    total_pnl_sum: Decimal | None
    latest_total_pnl: Decimal | None
    realized_pnl_sum: Decimal | None
    latest_realized_pnl: Decimal | None
    unrealized_pnl_sum: Decimal | None
    latest_unrealized_pnl: Decimal | None
    no_position_report_count: int
    duplicate_generated_at_count: int
    reconciliation_status_rows: tuple[
        PaperExecutionReconciliationDbHistoryStatusRow,
        ...,
    ]
    latest_reason_codes: tuple[str, ...]
    reason_code_rows: tuple[
        PaperExecutionReconciliationDbHistoryReasonCodeRow,
        ...,
    ]
    reason_codes: tuple[str, ...]
    concerns: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperExecutionReconciliationDbHistoryReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_history_status("history_status", self.history_status)
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
        if self.latest_reconciliation_status is not None:
            _require_reconciliation_status(
                "latest_reconciliation_status",
                self.latest_reconciliation_status,
            )
        for field_name in ("pending_streak_count", "discrepancy_streak_count"):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "total_pnl_sum",
            "latest_total_pnl",
            "realized_pnl_sum",
            "latest_realized_pnl",
            "unrealized_pnl_sum",
            "latest_unrealized_pnl",
        ):
            _require_optional_decimal(field_name, getattr(self, field_name))
        _require_nonnegative_int(
            "no_position_report_count",
            self.no_position_report_count,
        )
        _require_nonnegative_int(
            "duplicate_generated_at_count",
            self.duplicate_generated_at_count,
        )
        object.__setattr__(
            self,
            "reconciliation_status_rows",
            _normalize_status_rows(self.reconciliation_status_rows),
        )
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
        object.__setattr__(
            self,
            "concerns",
            _normalize_reason_codes("concerns", self.concerns, allow_empty=True),
        )
        _validate_history_report(self)
        _require_hard_flags("history report", self)


def build_paper_execution_reconciliation_db_history_report(
    reconciliation_reports: object,
    *,
    config: PaperExecutionReconciliationDbHistoryConfig,
    generated_at: datetime,
) -> PaperExecutionReconciliationDbHistoryReport:
    if type(config) is not PaperExecutionReconciliationDbHistoryConfig:
        raise ValueError(
            "config must be a PaperExecutionReconciliationDbHistoryConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("config", config)

    reports = _normalize_reconciliation_reports(reconciliation_reports)
    chronological_reports = _chronological_reports(reports)
    latest = chronological_reports[-1] if chronological_reports else None
    status_rows = _reconciliation_status_rows(chronological_reports)
    duplicate_generated_at_count = _duplicate_generated_at_count(
        chronological_reports,
    )
    pending_streak_count = _consecutive_latest_status_count(
        chronological_reports,
        "has_pending",
    )
    discrepancy_streak_count = _consecutive_latest_status_count(
        chronological_reports,
        "has_discrepancies",
    )

    return PaperExecutionReconciliationDbHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        history_status=_history_status(
            report_count=len(chronological_reports),
            pending_streak_count=pending_streak_count,
            discrepancy_streak_count=discrepancy_streak_count,
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
        latest_reconciliation_status=(
            latest.reconciliation_status if latest is not None else None
        ),
        pending_streak_count=pending_streak_count,
        discrepancy_streak_count=discrepancy_streak_count,
        total_pnl_sum=_sum_optional_decimal_field(chronological_reports, "total_pnl"),
        latest_total_pnl=latest.total_pnl if latest is not None else None,
        realized_pnl_sum=_sum_required_decimal_field(
            chronological_reports,
            "realized_pnl",
        ),
        latest_realized_pnl=latest.realized_pnl if latest is not None else None,
        unrealized_pnl_sum=_sum_required_decimal_field(
            chronological_reports,
            "unrealized_pnl",
        ),
        latest_unrealized_pnl=latest.unrealized_pnl if latest is not None else None,
        no_position_report_count=sum(
            1 for report in chronological_reports if report.total_positions == 0
        ),
        duplicate_generated_at_count=duplicate_generated_at_count,
        reconciliation_status_rows=status_rows,
        latest_reason_codes=latest.reason_codes if latest is not None else (),
        reason_code_rows=_reason_code_rows(chronological_reports),
        reason_codes=_history_reason_codes(
            report_count=len(chronological_reports),
            pending_streak_count=pending_streak_count,
            discrepancy_streak_count=discrepancy_streak_count,
            duplicate_generated_at_count=duplicate_generated_at_count,
            config=config,
        ),
        concerns=(NO_POSITION_FIELD_CONCERN,),
    )


def _normalize_reconciliation_reports(
    value: object,
) -> tuple[PaperExecutionReconciliationReport, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reconciliation_reports must be a list or tuple")
    reports = tuple(value)
    for report in reports:
        if type(report) is not PaperExecutionReconciliationReport:
            raise ValueError(
                "reconciliation_reports must contain "
                "PaperExecutionReconciliationReport values",
            )
        _validate_reconciliation_report(report)
    return reports


def _chronological_reports(
    reports: tuple[PaperExecutionReconciliationReport, ...],
) -> tuple[PaperExecutionReconciliationReport, ...]:
    return tuple(
        report
        for _, report in sorted(
            enumerate(reports),
            key=lambda item: (_as_utc("report generated_at", item[1].generated_at), item[0]),
        )
    )


def _reconciliation_status_rows(
    reports: tuple[PaperExecutionReconciliationReport, ...],
) -> tuple[PaperExecutionReconciliationDbHistoryStatusRow, ...]:
    return tuple(
        PaperExecutionReconciliationDbHistoryStatusRow(
            reconciliation_status,
            sum(
                1
                for report in reports
                if report.reconciliation_status == reconciliation_status
            ),
        )
        for reconciliation_status in RECONCILIATION_STATUSES
    )


def _duplicate_generated_at_count(
    reports: tuple[PaperExecutionReconciliationReport, ...],
) -> int:
    counts: dict[datetime, int] = {}
    for report in reports:
        generated_at = _as_utc("report generated_at", report.generated_at)
        counts[generated_at] = counts.get(generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _consecutive_latest_status_count(
    reports: tuple[PaperExecutionReconciliationReport, ...],
    reconciliation_status: str,
) -> int:
    if not reports or reports[-1].reconciliation_status != reconciliation_status:
        return 0
    count = 0
    for report in reversed(reports):
        if report.reconciliation_status != reconciliation_status:
            break
        count += 1
    return count


def _sum_optional_decimal_field(
    reports: tuple[PaperExecutionReconciliationReport, ...],
    field_name: str,
) -> Decimal | None:
    values = tuple(
        getattr(report, field_name)
        for report in reports
        if getattr(report, field_name) is not None
    )
    if not values:
        return None
    total = ZERO
    for value in values:
        _require_decimal(field_name, value)
        total += value
    return total


def _sum_required_decimal_field(
    reports: tuple[PaperExecutionReconciliationReport, ...],
    field_name: str,
) -> Decimal | None:
    if not reports:
        return None
    total = ZERO
    for report in reports:
        value = getattr(report, field_name)
        _require_decimal(field_name, value)
        total += value
    return total


def _reason_code_rows(
    reports: tuple[PaperExecutionReconciliationReport, ...],
) -> tuple[PaperExecutionReconciliationDbHistoryReasonCodeRow, ...]:
    counts: dict[str, int] = {}
    for report in reports:
        report_reason_codes = _normalize_reason_codes(
            "report reason_codes",
            report.reason_codes,
            allow_empty=True,
        )
        for reason_code in report_reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperExecutionReconciliationDbHistoryReasonCodeRow(
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
    pending_streak_count: int,
    discrepancy_streak_count: int,
    duplicate_generated_at_count: int,
    config: PaperExecutionReconciliationDbHistoryConfig,
) -> str:
    if report_count < config.min_report_count:
        return "blocked"
    if discrepancy_streak_count > config.max_discrepancy_streak:
        return "blocked"
    if pending_streak_count > config.max_pending_streak:
        return "watch"
    if duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        return "watch"
    return "pass"


def _history_reason_codes(
    *,
    report_count: int,
    pending_streak_count: int,
    discrepancy_streak_count: int,
    duplicate_generated_at_count: int,
    config: PaperExecutionReconciliationDbHistoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if report_count < config.min_report_count:
        reason_codes.append("insufficient_paper_execution_reconciliation_history")
    if pending_streak_count > config.max_pending_streak:
        reason_codes.append("pending_reconciliation_streak_threshold_exceeded")
    if discrepancy_streak_count > config.max_discrepancy_streak:
        reason_codes.append("discrepancy_reconciliation_streak_threshold_exceeded")
    if duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        reason_codes.append("duplicate_generated_at_threshold_exceeded")
    if not reason_codes:
        reason_codes.append("paper_execution_reconciliation_db_history_passed")
    return tuple(sorted(set(reason_codes)))


def _validate_reconciliation_report(
    report: PaperExecutionReconciliationReport,
) -> None:
    _require_hard_flags("reconciliation report", report)
    _as_utc("report generated_at", report.generated_at)
    _require_canonical_string("report config_version", report.config_version)
    _require_reconciliation_status(
        "reconciliation_status",
        report.reconciliation_status,
    )
    _require_nonnegative_int("total_positions", report.total_positions)
    if report.total_pnl is not None:
        _require_decimal("total_pnl", report.total_pnl)
    _require_decimal("realized_pnl", report.realized_pnl)
    _require_decimal("unrealized_pnl", report.unrealized_pnl)
    _normalize_reason_codes(
        "report reason_codes",
        report.reason_codes,
        allow_empty=True,
    )


def _validate_history_report(
    report: PaperExecutionReconciliationDbHistoryReport,
) -> None:
    if report.report_count == 0:
        _validate_empty_history_report(report)
    else:
        _validate_nonempty_history_report(report)
    if report.reconciliation_status_rows != tuple(
        PaperExecutionReconciliationDbHistoryStatusRow(
            reconciliation_status,
            _count_for_status(report.reconciliation_status_rows, reconciliation_status),
        )
        for reconciliation_status in RECONCILIATION_STATUSES
    ):
        raise ValueError("reconciliation_status_rows must be deterministic")
    if report.report_count != sum(
        row.report_count for row in report.reconciliation_status_rows
    ):
        raise ValueError("reconciliation_status_rows must match report_count")
    if report.no_position_report_count > report.report_count:
        raise ValueError("no_position_report_count must not exceed report_count")
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
    report: PaperExecutionReconciliationDbHistoryReport,
) -> None:
    absent_fields = (
        "first_report_generated_at",
        "latest_report_generated_at",
        "latest_reconciliation_status",
        "total_pnl_sum",
        "latest_total_pnl",
        "realized_pnl_sum",
        "latest_realized_pnl",
        "unrealized_pnl_sum",
        "latest_unrealized_pnl",
    )
    for field_name in absent_fields:
        if getattr(report, field_name) is not None:
            raise ValueError(f"{field_name} must be absent without reports")
    for field_name in (
        "pending_streak_count",
        "discrepancy_streak_count",
        "no_position_report_count",
        "duplicate_generated_at_count",
    ):
        if getattr(report, field_name) != 0:
            raise ValueError(f"{field_name} must be zero without reports")
    if report.latest_reason_codes:
        raise ValueError("latest_reason_codes must be absent without reports")
    if report.reason_code_rows:
        raise ValueError("reason_code_rows must be absent without reports")


def _validate_nonempty_history_report(
    report: PaperExecutionReconciliationDbHistoryReport,
) -> None:
    required_fields = (
        "first_report_generated_at",
        "latest_report_generated_at",
        "latest_reconciliation_status",
        "realized_pnl_sum",
        "latest_realized_pnl",
        "unrealized_pnl_sum",
        "latest_unrealized_pnl",
    )
    for field_name in required_fields:
        if getattr(report, field_name) is None:
            raise ValueError(f"{field_name} is required with reports")
    if report.latest_report_generated_at < report.first_report_generated_at:
        raise ValueError("latest_report_generated_at must not precede first report")
    if _count_for_status(
        report.reconciliation_status_rows,
        report.latest_reconciliation_status,
    ) == 0:
        raise ValueError(
            "reconciliation_status_rows must cover latest_reconciliation_status",
        )


def _validate_consecutive_latest_counts(
    report: PaperExecutionReconciliationDbHistoryReport,
) -> None:
    fields_by_status = {
        "has_pending": "pending_streak_count",
        "has_discrepancies": "discrepancy_streak_count",
    }
    for reconciliation_status, field_name in fields_by_status.items():
        count = getattr(report, field_name)
        if report.latest_reconciliation_status == reconciliation_status:
            if report.report_count > 0 and count == 0:
                raise ValueError(f"{field_name} must be positive for latest status")
            if count > report.report_count:
                raise ValueError(f"{field_name} must not exceed report_count")
            if count > _count_for_status(
                report.reconciliation_status_rows,
                reconciliation_status,
            ):
                raise ValueError(
                    f"{field_name} must not exceed reconciliation_status_rows count",
                )
        elif count != 0:
            raise ValueError(f"{field_name} must be zero unless it is the latest status")


def _normalize_status_rows(
    rows: object,
) -> tuple[PaperExecutionReconciliationDbHistoryStatusRow, ...]:
    normalized = _normalize_tuple(rows, "reconciliation_status_rows")
    for row in normalized:
        if type(row) is not PaperExecutionReconciliationDbHistoryStatusRow:
            raise ValueError(
                "reconciliation_status_rows must contain "
                "PaperExecutionReconciliationDbHistoryStatusRow values",
            )
        _require_hard_flags("status row", row)
    return normalized


def _normalize_reason_code_rows(
    rows: object,
) -> tuple[PaperExecutionReconciliationDbHistoryReasonCodeRow, ...]:
    normalized = _normalize_tuple(rows, "reason_code_rows")
    for row in normalized:
        if type(row) is not PaperExecutionReconciliationDbHistoryReasonCodeRow:
            raise ValueError(
                "reason_code_rows must contain "
                "PaperExecutionReconciliationDbHistoryReasonCodeRow values",
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
        return tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc


def _count_for_status(
    rows: tuple[PaperExecutionReconciliationDbHistoryStatusRow, ...],
    reconciliation_status: str | None,
) -> int:
    for row in rows:
        if row.reconciliation_status == reconciliation_status:
            return row.report_count
    return 0


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


def _require_history_status(field_name: str, value: object) -> None:
    if value not in HISTORY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_reconciliation_status(field_name: str, value: object) -> None:
    if value not in RECONCILIATION_STATUSES:
        raise ValueError(f"{field_name} must be a known reconciliation status")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive int")


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is not None:
        _require_decimal(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")
