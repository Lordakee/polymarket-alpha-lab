"""Pure read-only history reducer for persisted paper order lifecycle records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_order_lifecycle import (
    LIFECYCLE_STATUSES,
    TERMINAL_STATUSES,
    PaperOrderLifecycleRecord,
)


__all__ = (
    "DEFAULT_PAPER_ORDER_LIFECYCLE_DB_HISTORY_CONFIG_VERSION",
    "PaperOrderLifecycleDbHistoryConfig",
    "PaperOrderLifecycleDbHistoryReasonCodeCount",
    "PaperOrderLifecycleDbHistoryReport",
    "PaperOrderLifecycleDbHistoryStatusRow",
    "build_paper_order_lifecycle_db_history_report",
)


DEFAULT_PAPER_ORDER_LIFECYCLE_DB_HISTORY_CONFIG_VERSION = (
    "paper-order-lifecycle-db-history-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")


@dataclass(frozen=True)
class PaperOrderLifecycleDbHistoryConfig:
    config_version: str = DEFAULT_PAPER_ORDER_LIFECYCLE_DB_HISTORY_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperOrderLifecycleDbHistoryConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperOrderLifecycleDbHistoryConfig:
            raise ValueError("config must be exactly PaperOrderLifecycleDbHistoryConfig")
        _require_canonical_string("config_version", self.config_version)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperOrderLifecycleDbHistoryStatusRow:
    lifecycle_status: str
    status_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperOrderLifecycleDbHistoryStatusRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperOrderLifecycleDbHistoryStatusRow:
            raise ValueError("status row must be exactly PaperOrderLifecycleDbHistoryStatusRow")
        _require_lifecycle_status("lifecycle_status", self.lifecycle_status)
        _require_nonnegative_int("status_count", self.status_count)
        _require_hard_flags("status row", self)


@dataclass(frozen=True)
class PaperOrderLifecycleDbHistoryReasonCodeCount:
    reason_code: str
    count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperOrderLifecycleDbHistoryReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperOrderLifecycleDbHistoryReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "PaperOrderLifecycleDbHistoryReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("count", self.count)
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperOrderLifecycleDbHistoryReport:
    generated_at: datetime
    config_version: str
    record_count: int
    first_record_generated_at: datetime | None
    latest_record_generated_at: datetime | None
    latest_lifecycle_status: str | None
    terminal_record_count: int
    nonterminal_record_count: int
    filled_record_count: int
    blocked_record_count: int
    held_record_count: int
    total_fill_notional: Decimal
    latest_fill_notional: Decimal | None
    lifecycle_status_rows: tuple[PaperOrderLifecycleDbHistoryStatusRow, ...]
    duplicate_generated_at_count: int
    latest_same_status_streak: int
    reason_code_counts: tuple[PaperOrderLifecycleDbHistoryReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperOrderLifecycleDbHistoryReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperOrderLifecycleDbHistoryReport:
            raise ValueError("report must be exactly PaperOrderLifecycleDbHistoryReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("record_count", self.record_count)
        object.__setattr__(
            self,
            "first_record_generated_at",
            _as_optional_utc(
                "first_record_generated_at",
                self.first_record_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_record_generated_at",
            _as_optional_utc(
                "latest_record_generated_at",
                self.latest_record_generated_at,
            ),
        )
        if self.latest_lifecycle_status is not None:
            _require_lifecycle_status(
                "latest_lifecycle_status",
                self.latest_lifecycle_status,
            )
        for field_name in (
            "terminal_record_count",
            "nonterminal_record_count",
            "filled_record_count",
            "blocked_record_count",
            "held_record_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "total_fill_notional",
            _require_nonnegative_decimal(
                "total_fill_notional",
                self.total_fill_notional,
            ).quantize(QUANTUM),
        )
        object.__setattr__(
            self,
            "latest_fill_notional",
            _optional_nonnegative_decimal(
                "latest_fill_notional",
                self.latest_fill_notional,
            ),
        )
        object.__setattr__(
            self,
            "lifecycle_status_rows",
            _normalize_status_rows(self.lifecycle_status_rows),
        )
        _require_nonnegative_int(
            "duplicate_generated_at_count",
            self.duplicate_generated_at_count,
        )
        _require_nonnegative_int(
            "latest_same_status_streak",
            self.latest_same_status_streak,
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags("history report", self)


def build_paper_order_lifecycle_db_history_report(
    records: object,
    *,
    config: PaperOrderLifecycleDbHistoryConfig,
    generated_at: datetime,
) -> PaperOrderLifecycleDbHistoryReport:
    if type(config) is not PaperOrderLifecycleDbHistoryConfig:
        raise ValueError("config must be a PaperOrderLifecycleDbHistoryConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("config", config)

    normalized_records = _chronological_records(_normalize_records(records))
    latest = normalized_records[-1] if normalized_records else None

    return PaperOrderLifecycleDbHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        record_count=len(normalized_records),
        first_record_generated_at=(
            normalized_records[0].generated_at if normalized_records else None
        ),
        latest_record_generated_at=latest.generated_at if latest is not None else None,
        latest_lifecycle_status=latest.lifecycle_status if latest is not None else None,
        terminal_record_count=sum(1 for record in normalized_records if record.is_terminal),
        nonterminal_record_count=sum(
            1 for record in normalized_records if not record.is_terminal
        ),
        filled_record_count=sum(
            1 for record in normalized_records if record.lifecycle_status == "paper_filled"
        ),
        blocked_record_count=sum(
            1 for record in normalized_records if record.lifecycle_status == "risk_blocked"
        ),
        held_record_count=sum(
            1
            for record in normalized_records
            if record.lifecycle_status == "human_approval_pending"
        ),
        total_fill_notional=sum(
            (record.fill_notional for record in normalized_records),
            ZERO,
        ).quantize(QUANTUM),
        latest_fill_notional=latest.fill_notional if latest is not None else None,
        lifecycle_status_rows=_status_rows(normalized_records),
        duplicate_generated_at_count=_duplicate_generated_at_count(normalized_records),
        latest_same_status_streak=_latest_same_status_streak(normalized_records),
        reason_code_counts=_reason_code_counts(normalized_records),
    )


def _normalize_records(
    value: object,
) -> tuple[PaperOrderLifecycleRecord, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("records must be a list or tuple")
    records = tuple(value)
    for record in records:
        if type(record) is not PaperOrderLifecycleRecord:
            raise ValueError("records must contain PaperOrderLifecycleRecord values")
        _validate_source_record(record)
    return records


def _validate_source_record(record: PaperOrderLifecycleRecord) -> None:
    _require_hard_flags("source record", record)
    _as_utc("record generated_at", record.generated_at)
    _require_canonical_string("record config_version", record.config_version)
    _require_lifecycle_status("record lifecycle_status", record.lifecycle_status)
    _require_nonnegative_decimal("record fill_notional", record.fill_notional)
    if type(record.is_terminal) is not bool:
        raise ValueError("record is_terminal must be a bool")
    if record.is_terminal != (record.lifecycle_status in TERMINAL_STATUSES):
        raise ValueError("record is_terminal must match lifecycle status")
    _normalize_reason_codes("record reason_codes", record.reason_codes, allow_empty=True)


def _chronological_records(
    records: tuple[PaperOrderLifecycleRecord, ...],
) -> tuple[PaperOrderLifecycleRecord, ...]:
    return tuple(
        record
        for _, record in sorted(
            enumerate(records),
            key=lambda item: (
                _as_utc("record generated_at", item[1].generated_at),
                item[0],
            ),
        )
    )


def _status_rows(
    records: tuple[PaperOrderLifecycleRecord, ...],
) -> tuple[PaperOrderLifecycleDbHistoryStatusRow, ...]:
    return tuple(
        PaperOrderLifecycleDbHistoryStatusRow(
            lifecycle_status,
            sum(1 for record in records if record.lifecycle_status == lifecycle_status),
        )
        for lifecycle_status in LIFECYCLE_STATUSES
    )


def _duplicate_generated_at_count(
    records: tuple[PaperOrderLifecycleRecord, ...],
) -> int:
    counts: dict[datetime, int] = {}
    for record in records:
        generated_at = _as_utc("record generated_at", record.generated_at)
        counts[generated_at] = counts.get(generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _latest_same_status_streak(
    records: tuple[PaperOrderLifecycleRecord, ...],
) -> int:
    if not records:
        return 0
    latest_status = records[-1].lifecycle_status
    count = 0
    for record in reversed(records):
        if record.lifecycle_status != latest_status:
            break
        count += 1
    return count


def _reason_code_counts(
    records: tuple[PaperOrderLifecycleRecord, ...],
) -> tuple[PaperOrderLifecycleDbHistoryReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for record in records:
        for reason_code in record.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperOrderLifecycleDbHistoryReasonCodeCount(reason_code, count)
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _validate_report(report: PaperOrderLifecycleDbHistoryReport) -> None:
    if report.record_count == 0:
        _validate_empty_report(report)
    else:
        _validate_nonempty_report(report)
    if report.terminal_record_count + report.nonterminal_record_count != report.record_count:
        raise ValueError("terminal and nonterminal counts must match record_count")
    if sum(row.status_count for row in report.lifecycle_status_rows) != report.record_count:
        raise ValueError("lifecycle_status_rows must match record_count")
    if tuple(row.lifecycle_status for row in report.lifecycle_status_rows) != LIFECYCLE_STATUSES:
        raise ValueError("lifecycle_status_rows must be deterministic")
    if report.duplicate_generated_at_count >= max(report.record_count, 1):
        raise ValueError("duplicate_generated_at_count must be below record_count")
    if report.reason_code_counts != tuple(
        sorted(
            report.reason_code_counts,
            key=lambda row: (-row.count, row.reason_code),
        )
    ):
        raise ValueError("reason_code_counts must be deterministic")


def _validate_empty_report(report: PaperOrderLifecycleDbHistoryReport) -> None:
    for field_name in (
        "first_record_generated_at",
        "latest_record_generated_at",
        "latest_lifecycle_status",
        "latest_fill_notional",
    ):
        if getattr(report, field_name) is not None:
            raise ValueError(f"{field_name} must be absent without records")
    if report.terminal_record_count != 0 or report.nonterminal_record_count != 0:
        raise ValueError("terminal counts must be zero without records")
    if report.filled_record_count != 0:
        raise ValueError("filled_record_count must be zero without records")
    if report.blocked_record_count != 0:
        raise ValueError("blocked_record_count must be zero without records")
    if report.held_record_count != 0:
        raise ValueError("held_record_count must be zero without records")
    if report.total_fill_notional != ZERO:
        raise ValueError("total_fill_notional must be zero without records")
    if report.duplicate_generated_at_count != 0:
        raise ValueError("duplicate_generated_at_count must be zero without records")
    if report.latest_same_status_streak != 0:
        raise ValueError("latest_same_status_streak must be zero without records")
    if report.reason_code_counts:
        raise ValueError("reason_code_counts must be empty without records")


def _validate_nonempty_report(report: PaperOrderLifecycleDbHistoryReport) -> None:
    for field_name in (
        "first_record_generated_at",
        "latest_record_generated_at",
        "latest_lifecycle_status",
        "latest_fill_notional",
    ):
        if getattr(report, field_name) is None:
            raise ValueError(f"{field_name} is required with records")
    if report.latest_record_generated_at < report.first_record_generated_at:
        raise ValueError("latest_record_generated_at must not precede first record")
    if report.latest_same_status_streak <= 0:
        raise ValueError("latest_same_status_streak must be positive with records")


def _normalize_status_rows(
    value: object,
) -> tuple[PaperOrderLifecycleDbHistoryStatusRow, ...]:
    if type(value) is not tuple:
        raise ValueError("lifecycle_status_rows must be a tuple")
    for row in value:
        if type(row) is not PaperOrderLifecycleDbHistoryStatusRow:
            raise ValueError(
                "lifecycle_status_rows must contain "
                "PaperOrderLifecycleDbHistoryStatusRow values",
            )
        _require_hard_flags("status row", row)
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperOrderLifecycleDbHistoryReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    reason_codes: set[str] = set()
    for row in value:
        if type(row) is not PaperOrderLifecycleDbHistoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "PaperOrderLifecycleDbHistoryReasonCodeCount values",
            )
        _require_hard_flags("reason code count", row)
        if row.reason_code in reason_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason codes")
        reason_codes.add(row.reason_code)
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    return reason_codes


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


def _optional_nonnegative_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value).quantize(QUANTUM)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_lifecycle_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in LIFECYCLE_STATUSES:
        raise ValueError(f"{field_name} must be a known lifecycle status")


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


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
