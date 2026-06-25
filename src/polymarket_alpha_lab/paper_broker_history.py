"""Pure paper broker execution history reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_broker import (
    EXECUTION_STATUSES,
    NEXT_STEP_BY_STATUS,
    PaperBrokerExecutionRecord,
)


__all__ = (
    "DEFAULT_PAPER_BROKER_HISTORY_CONFIG_VERSION",
    "PaperBrokerHistoryConfig",
    "PaperBrokerHistoryReasonCodeCount",
    "PaperBrokerHistoryReport",
    "PaperBrokerHistoryStatusRow",
    "build_paper_broker_history_report",
)


DEFAULT_PAPER_BROKER_HISTORY_CONFIG_VERSION = "paper-broker-history-v0"
HISTORY_STATUSES = ("empty", "pass", "watch", "blocked")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")


_SUMMARY_BY_LATEST_EXECUTION_STATUS = {
    "paper_submitted": (
        "pass",
        NEXT_STEP_BY_STATUS["paper_submitted"],
        ("paper_broker_history_latest_submitted",),
    ),
    "paper_blocked": (
        "blocked",
        "repair_paper_broker_executions",
        ("paper_broker_history_latest_blocked",),
    ),
    "paper_held": (
        "watch",
        "review_paper_broker_executions",
        ("paper_broker_history_latest_held",),
    ),
}
_EMPTY_SUMMARY = (
    "empty",
    "await_paper_broker_executions",
    ("paper_broker_history_empty",),
)


@dataclass(frozen=True)
class PaperBrokerHistoryConfig:
    config_version: str = DEFAULT_PAPER_BROKER_HISTORY_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperBrokerHistoryConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperBrokerHistoryConfig:
            raise ValueError("config must be a PaperBrokerHistoryConfig")
        _require_canonical_string("config_version", self.config_version)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperBrokerHistoryStatusRow:
    execution_status: str
    status_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperBrokerHistoryStatusRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperBrokerHistoryStatusRow:
            raise ValueError("status row must be a PaperBrokerHistoryStatusRow")
        _require_execution_status("execution_status", self.execution_status)
        _require_nonnegative_int("status_count", self.status_count)
        _require_hard_flags("status row", self)


@dataclass(frozen=True)
class PaperBrokerHistoryReasonCodeCount:
    reason_code: str
    count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperBrokerHistoryReasonCodeCount does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperBrokerHistoryReasonCodeCount:
            raise ValueError(
                "reason code count must be a PaperBrokerHistoryReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("count", self.count)
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperBrokerHistoryReport:
    generated_at: datetime
    config_version: str
    record_count: int
    first_record_generated_at: datetime | None
    latest_record_generated_at: datetime | None
    latest_execution_status: str | None
    latest_recommended_next_step: str | None
    submitted_record_count: int
    blocked_record_count: int
    held_record_count: int
    total_execution_notional: Decimal
    latest_execution_notional: Decimal | None
    total_source_proposal_count: int
    execution_status_rows: tuple[PaperBrokerHistoryStatusRow, ...]
    reason_code_counts: tuple[PaperBrokerHistoryReasonCodeCount, ...]
    history_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("PaperBrokerHistoryReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PaperBrokerHistoryReport:
            raise ValueError("report must be a PaperBrokerHistoryReport")
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
        if self.latest_execution_status is not None:
            _require_execution_status(
                "latest_execution_status",
                self.latest_execution_status,
            )
        if self.latest_recommended_next_step is not None:
            _require_canonical_string(
                "latest_recommended_next_step",
                self.latest_recommended_next_step,
            )
        for field_name in (
            "submitted_record_count",
            "blocked_record_count",
            "held_record_count",
            "total_source_proposal_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "total_execution_notional",
            _require_nonnegative_decimal(
                "total_execution_notional",
                self.total_execution_notional,
            ).quantize(QUANTUM),
        )
        object.__setattr__(
            self,
            "latest_execution_notional",
            _optional_nonnegative_decimal(
                "latest_execution_notional",
                self.latest_execution_notional,
            ),
        )
        object.__setattr__(
            self,
            "execution_status_rows",
            _normalize_status_rows(self.execution_status_rows),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_history_status("history_status", self.history_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("history report", self)


def build_paper_broker_history_report(
    records: object,
    *,
    config: PaperBrokerHistoryConfig,
    generated_at: datetime,
) -> PaperBrokerHistoryReport:
    if type(config) is not PaperBrokerHistoryConfig:
        raise ValueError("config must be a PaperBrokerHistoryConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("config", config)

    normalized_records = _chronological_records(_normalize_records(records))
    latest = normalized_records[-1] if normalized_records else None
    history_status, next_step, reason_codes = _summary_fields(latest)

    return PaperBrokerHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        record_count=len(normalized_records),
        first_record_generated_at=(
            normalized_records[0].generated_at if normalized_records else None
        ),
        latest_record_generated_at=latest.generated_at if latest is not None else None,
        latest_execution_status=latest.execution_status if latest is not None else None,
        latest_recommended_next_step=(
            latest.recommended_next_step if latest is not None else None
        ),
        submitted_record_count=sum(
            1 for record in normalized_records if record.execution_status == "paper_submitted"
        ),
        blocked_record_count=sum(
            1 for record in normalized_records if record.execution_status == "paper_blocked"
        ),
        held_record_count=sum(
            1 for record in normalized_records if record.execution_status == "paper_held"
        ),
        total_execution_notional=sum(
            (record.execution_notional for record in normalized_records),
            ZERO,
        ).quantize(QUANTUM),
        latest_execution_notional=(
            latest.execution_notional if latest is not None else None
        ),
        total_source_proposal_count=sum(
            record.source_proposal_count for record in normalized_records
        ),
        execution_status_rows=_status_rows(normalized_records),
        reason_code_counts=_reason_code_counts(normalized_records),
        history_status=history_status,
        recommended_next_step=next_step,
        reason_codes=reason_codes,
    )


def _summary_fields(
    latest: PaperBrokerExecutionRecord | None,
) -> tuple[str, str, tuple[str, ...]]:
    if latest is None:
        return _EMPTY_SUMMARY
    return _SUMMARY_BY_LATEST_EXECUTION_STATUS[latest.execution_status]


def _normalize_records(value: object) -> tuple[PaperBrokerExecutionRecord, ...]:
    if type(value) is not tuple:
        raise ValueError("records must be a tuple")
    for record in value:
        if type(record) is not PaperBrokerExecutionRecord:
            raise ValueError("records must contain PaperBrokerExecutionRecord values")
        _validate_source_record(record)
    return value


def _validate_source_record(record: PaperBrokerExecutionRecord) -> None:
    _require_hard_flags("source record", record)
    _as_utc("record generated_at", record.generated_at)
    _require_canonical_string("record config_version", record.config_version)
    _require_execution_status("record execution_status", record.execution_status)
    if record.recommended_next_step != NEXT_STEP_BY_STATUS[record.execution_status]:
        raise ValueError("record recommended_next_step must match execution_status")
    _require_nonnegative_int("record source_proposal_count", record.source_proposal_count)
    _require_nonnegative_decimal(
        "record source_proposal_total_notional",
        record.source_proposal_total_notional,
    )
    _require_nonnegative_decimal("record execution_notional", record.execution_notional)
    _normalize_reason_codes("record reason_codes", record.reason_codes, allow_empty=True)


def _chronological_records(
    records: tuple[PaperBrokerExecutionRecord, ...],
) -> tuple[PaperBrokerExecutionRecord, ...]:
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
    records: tuple[PaperBrokerExecutionRecord, ...],
) -> tuple[PaperBrokerHistoryStatusRow, ...]:
    return tuple(
        PaperBrokerHistoryStatusRow(
            execution_status,
            sum(1 for record in records if record.execution_status == execution_status),
        )
        for execution_status in EXECUTION_STATUSES
    )


def _reason_code_counts(
    records: tuple[PaperBrokerExecutionRecord, ...],
) -> tuple[PaperBrokerHistoryReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for record in records:
        for reason_code in record.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperBrokerHistoryReasonCodeCount(reason_code, count)
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _validate_report(report: PaperBrokerHistoryReport) -> None:
    if report.record_count == 0:
        _validate_empty_report(report)
    else:
        _validate_nonempty_report(report)
    if (
        report.submitted_record_count
        + report.blocked_record_count
        + report.held_record_count
    ) != report.record_count:
        raise ValueError("execution status counts must match record_count")
    if sum(row.status_count for row in report.execution_status_rows) != report.record_count:
        raise ValueError("execution_status_rows must match record_count")
    if tuple(row.execution_status for row in report.execution_status_rows) != EXECUTION_STATUSES:
        raise ValueError("execution_status_rows must be deterministic")
    if report.reason_code_counts != tuple(
        sorted(
            report.reason_code_counts,
            key=lambda row: (-row.count, row.reason_code),
        )
    ):
        raise ValueError("reason_code_counts must be deterministic")


def _validate_empty_report(report: PaperBrokerHistoryReport) -> None:
    if report.first_record_generated_at is not None:
        raise ValueError("first_record_generated_at must be absent without records")
    if report.latest_record_generated_at is not None:
        raise ValueError("latest_record_generated_at must be absent without records")
    if report.latest_execution_status is not None:
        raise ValueError("latest_execution_status must be absent without records")
    if report.latest_recommended_next_step is not None:
        raise ValueError("latest_recommended_next_step must be absent without records")
    if report.latest_execution_notional is not None:
        raise ValueError("latest_execution_notional must be absent without records")
    if report.total_execution_notional != ZERO:
        raise ValueError("total_execution_notional must be zero without records")
    if report.total_source_proposal_count != 0:
        raise ValueError("total_source_proposal_count must be zero without records")
    if report.reason_code_counts != ():
        raise ValueError("reason_code_counts must be empty without records")


def _validate_nonempty_report(report: PaperBrokerHistoryReport) -> None:
    if report.first_record_generated_at is None:
        raise ValueError("first_record_generated_at is required with records")
    if report.latest_record_generated_at is None:
        raise ValueError("latest_record_generated_at is required with records")
    if report.latest_execution_status is None:
        raise ValueError("latest_execution_status is required with records")
    if report.latest_recommended_next_step is None:
        raise ValueError("latest_recommended_next_step is required with records")
    if report.latest_execution_notional is None:
        raise ValueError("latest_execution_notional is required with records")
    expected_history_status, expected_next_step, expected_reason_codes = (
        _SUMMARY_BY_LATEST_EXECUTION_STATUS[report.latest_execution_status]
    )
    if report.history_status != expected_history_status:
        raise ValueError("history_status must match latest_execution_status")
    if report.recommended_next_step != expected_next_step:
        raise ValueError("recommended_next_step must match latest_execution_status")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match latest_execution_status")


def _normalize_status_rows(
    value: object,
) -> tuple[PaperBrokerHistoryStatusRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("execution_status_rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not PaperBrokerHistoryStatusRow:
            raise ValueError("execution_status_rows must contain status rows")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperBrokerHistoryReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not PaperBrokerHistoryReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must be nonempty")
    previous: str | None = None
    for code in value:
        _require_canonical_string(f"{field_name} entry", code)
        if previous is not None and previous >= code:
            raise ValueError(f"{field_name} must be sorted and unique")
        previous = code
    return value


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


def _require_execution_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in EXECUTION_STATUSES:
        rendered = ", ".join(EXECUTION_STATUSES)
        raise ValueError(f"{field_name} must be one of: {rendered}")


def _require_history_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HISTORY_STATUSES:
        rendered = ", ".join(HISTORY_STATUSES)
        raise ValueError(f"{field_name} must be one of: {rendered}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


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


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a finite Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value).quantize(QUANTUM)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
