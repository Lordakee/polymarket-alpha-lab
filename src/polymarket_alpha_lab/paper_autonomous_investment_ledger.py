"""Pure paper autonomous investment ledger reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext

from polymarket_alpha_lab.paper_broker import PaperBrokerExecutionRecord


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_CONFIG_VERSION",
    "PaperAutonomousInvestmentLedgerConfig",
    "PaperAutonomousInvestmentLedgerEntry",
    "PaperAutonomousInvestmentLedgerReasonCodeCount",
    "PaperAutonomousInvestmentLedgerReport",
    "build_paper_autonomous_investment_ledger_report",
)


DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_CONFIG_VERSION = (
    "paper-autonomous-investment-ledger-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
LEDGER_STATUSES = ("pass", "watch", "blocked")
EXECUTION_STATUSES = ("paper_submitted", "paper_blocked", "paper_held")
PASS_REASON_CODE = "paper_autonomous_investment_ledger_passed"
BLOCKED_REASON_CODES = frozenset(
    (
        "paper_autonomous_investment_ledger_blocked_records_present",
        "paper_autonomous_investment_ledger_no_source_records",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "paper_autonomous_investment_ledger_held_records_present",
        "paper_autonomous_investment_ledger_stale_source_records",
    ),
)
NEXT_STEP_BY_STATUS = {
    "pass": "archive_paper_autonomous_investment_ledger",
    "watch": "review_paper_autonomous_investment_ledger",
    "blocked": "block_paper_autonomous_investment_ledger",
}


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerConfig:
    config_version: str = DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_CONFIG_VERSION
    max_latest_source_age_seconds: int = 86_400
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperAutonomousInvestmentLedgerConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousInvestmentLedgerConfig:
            raise ValueError(
                "config must be exactly PaperAutonomousInvestmentLedgerConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "max_latest_source_age_seconds",
            self.max_latest_source_age_seconds,
        )
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerEntry:
    entry_rank: int
    source_generated_at: datetime
    source_config_version: str
    execution_status: str
    recommended_next_step: str
    source_gate_status: str
    source_proposal_count: int
    source_proposal_total_notional: Decimal
    execution_notional: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperAutonomousInvestmentLedgerEntry does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousInvestmentLedgerEntry:
            raise ValueError(
                "entry must be exactly PaperAutonomousInvestmentLedgerEntry",
            )
        _require_positive_int("entry_rank", self.entry_rank)
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc("source_generated_at", self.source_generated_at),
        )
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_execution_status("execution_status", self.execution_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_canonical_string("source_gate_status", self.source_gate_status)
        _require_nonnegative_int("source_proposal_count", self.source_proposal_count)
        object.__setattr__(
            self,
            "source_proposal_total_notional",
            _quantize(self.source_proposal_total_notional),
        )
        object.__setattr__(
            self,
            "execution_notional",
            _quantize(self.execution_notional),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_entry_consistency(self)
        _validate_hard_flags("entry", self)


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerReasonCodeCount:
    reason_code: str
    source_record_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperAutonomousInvestmentLedgerReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousInvestmentLedgerReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "PaperAutonomousInvestmentLedgerReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("source_record_count", self.source_record_count)
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerReport:
    generated_at: datetime
    config_version: str
    ledger_status: str
    recommended_next_step: str
    source_record_count: int
    submitted_count: int
    held_count: int
    blocked_count: int
    total_submitted_notional: Decimal
    held_zero_notional_count: int
    blocked_zero_notional_count: int
    latest_generated_at: datetime | None
    latest_age_seconds: int | None
    reason_code_counts: tuple[PaperAutonomousInvestmentLedgerReasonCodeCount, ...]
    entries: tuple[PaperAutonomousInvestmentLedgerEntry, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperAutonomousInvestmentLedgerReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousInvestmentLedgerReport:
            raise ValueError(
                "report must be exactly PaperAutonomousInvestmentLedgerReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_optional_utc("latest_generated_at", self.latest_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_ledger_status("ledger_status", self.ledger_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_nonnegative_int("source_record_count", self.source_record_count)
        _require_nonnegative_int("submitted_count", self.submitted_count)
        _require_nonnegative_int("held_count", self.held_count)
        _require_nonnegative_int("blocked_count", self.blocked_count)
        object.__setattr__(
            self,
            "total_submitted_notional",
            _quantize(self.total_submitted_notional),
        )
        _require_nonnegative_int(
            "held_zero_notional_count",
            self.held_zero_notional_count,
        )
        _require_nonnegative_int(
            "blocked_zero_notional_count",
            self.blocked_zero_notional_count,
        )
        _require_optional_nonnegative_int(
            "latest_age_seconds",
            self.latest_age_seconds,
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "entries", _normalize_entries(self.entries))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _validate_hard_flags("report", self)


def build_paper_autonomous_investment_ledger_report(
    *,
    broker_execution_records: tuple[PaperBrokerExecutionRecord, ...],
    config: PaperAutonomousInvestmentLedgerConfig | None = None,
    generated_at: datetime,
) -> PaperAutonomousInvestmentLedgerReport:
    """Reduce paper broker execution records into a replayable ledger report."""

    if config is None:
        config = PaperAutonomousInvestmentLedgerConfig()
    if type(config) is not PaperAutonomousInvestmentLedgerConfig:
        raise ValueError(
            "config must be exactly PaperAutonomousInvestmentLedgerConfig",
        )
    _validate_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_records = _normalize_source_records(broker_execution_records)
    entries = _ledger_entries(source_records)
    latest_generated_at = _latest_generated_at(entries)

    latest_age_seconds: int | None = None
    if latest_generated_at is not None:
        latest_age_seconds = _latest_source_age_seconds(
            generated_at=generated_at_utc,
            source_generated_at=latest_generated_at,
        )

    submitted_count = _status_count(entries, "paper_submitted")
    held_count = _status_count(entries, "paper_held")
    blocked_count = _status_count(entries, "paper_blocked")
    total_submitted_notional = _total_submitted_notional(entries)
    held_zero_notional_count = _zero_notional_count(entries, "paper_held")
    blocked_zero_notional_count = _zero_notional_count(entries, "paper_blocked")
    reason_codes = _ledger_reason_codes(
        source_record_count=len(source_records),
        held_count=held_count,
        blocked_count=blocked_count,
        latest_age_seconds=latest_age_seconds,
        config=config,
    )
    ledger_status = _ledger_status(reason_codes)

    return PaperAutonomousInvestmentLedgerReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        ledger_status=ledger_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[ledger_status],
        source_record_count=len(source_records),
        submitted_count=submitted_count,
        held_count=held_count,
        blocked_count=blocked_count,
        total_submitted_notional=total_submitted_notional,
        held_zero_notional_count=held_zero_notional_count,
        blocked_zero_notional_count=blocked_zero_notional_count,
        latest_generated_at=latest_generated_at,
        latest_age_seconds=latest_age_seconds,
        reason_code_counts=_reason_code_counts(entries),
        entries=entries,
        reason_codes=reason_codes,
    )


def _normalize_source_records(
    value: object,
) -> tuple[PaperBrokerExecutionRecord, ...]:
    if type(value) is not tuple:
        raise ValueError("broker_execution_records must be a tuple")
    for index, record in enumerate(value):
        if type(record) is not PaperBrokerExecutionRecord:
            raise ValueError(
                "broker_execution_records entries must be exact "
                "PaperBrokerExecutionRecord values",
            )
        _validate_hard_flags(f"broker_execution_records.{index}", record)
    return value


def _ledger_entries(
    source_records: tuple[PaperBrokerExecutionRecord, ...],
) -> tuple[PaperAutonomousInvestmentLedgerEntry, ...]:
    sorted_records = tuple(sorted(source_records, key=_source_record_sort_key))
    return tuple(
        PaperAutonomousInvestmentLedgerEntry(
            entry_rank=index,
            source_generated_at=record.generated_at,
            source_config_version=record.config_version,
            execution_status=record.execution_status,
            recommended_next_step=record.recommended_next_step,
            source_gate_status=record.source_gate_status,
            source_proposal_count=record.source_proposal_count,
            source_proposal_total_notional=record.source_proposal_total_notional,
            execution_notional=record.execution_notional,
            reason_codes=record.reason_codes,
        )
        for index, record in enumerate(sorted_records, start=1)
    )


def _source_record_sort_key(record: PaperBrokerExecutionRecord) -> tuple[object, ...]:
    return (
        record.generated_at,
        record.execution_status,
        record.source_gate_status,
        record.source_proposal_count,
        record.source_proposal_total_notional,
        record.execution_notional,
        record.reason_codes,
        record.config_version,
        record.recommended_next_step,
    )


def _latest_generated_at(
    entries: tuple[PaperAutonomousInvestmentLedgerEntry, ...],
) -> datetime | None:
    latest: datetime | None = None
    for entry in entries:
        if latest is None or entry.source_generated_at > latest:
            latest = entry.source_generated_at
    return latest


def _latest_source_age_seconds(
    *,
    generated_at: datetime,
    source_generated_at: datetime,
) -> int:
    if source_generated_at > generated_at:
        raise ValueError("source records must not be newer than generated_at")
    difference = generated_at - source_generated_at
    whole_seconds = difference.days * 86_400 + difference.seconds
    if difference.microseconds:
        whole_seconds += 1
    return whole_seconds


def _status_count(
    entries: tuple[PaperAutonomousInvestmentLedgerEntry, ...],
    execution_status: str,
) -> int:
    return sum(1 for entry in entries if entry.execution_status == execution_status)


def _zero_notional_count(
    entries: tuple[PaperAutonomousInvestmentLedgerEntry, ...],
    execution_status: str,
) -> int:
    return sum(
        1
        for entry in entries
        if entry.execution_status == execution_status
        and entry.execution_notional == ZERO
    )


def _total_submitted_notional(
    entries: tuple[PaperAutonomousInvestmentLedgerEntry, ...],
) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for entry in entries:
            if entry.execution_status == "paper_submitted":
                total += entry.execution_notional
    return _quantize(total)


def _reason_code_counts(
    entries: tuple[PaperAutonomousInvestmentLedgerEntry, ...],
) -> tuple[PaperAutonomousInvestmentLedgerReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for entry in entries:
        for reason_code in entry.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperAutonomousInvestmentLedgerReasonCodeCount(
            reason_code=reason_code,
            source_record_count=count,
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _ledger_reason_codes(
    *,
    source_record_count: int,
    held_count: int,
    blocked_count: int,
    latest_age_seconds: int | None,
    config: PaperAutonomousInvestmentLedgerConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    if source_record_count == 0:
        reason_codes.add("paper_autonomous_investment_ledger_no_source_records")
    if blocked_count:
        reason_codes.add("paper_autonomous_investment_ledger_blocked_records_present")
    if held_count:
        reason_codes.add("paper_autonomous_investment_ledger_held_records_present")
    if (
        latest_age_seconds is not None
        and latest_age_seconds > config.max_latest_source_age_seconds
    ):
        reason_codes.add("paper_autonomous_investment_ledger_stale_source_records")
    if not reason_codes:
        reason_codes.add(PASS_REASON_CODE)
    return tuple(sorted(reason_codes))


def _ledger_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _normalize_entries(
    value: object,
) -> tuple[PaperAutonomousInvestmentLedgerEntry, ...]:
    if type(value) is not tuple:
        raise ValueError("entries must be a tuple")
    previous_rank = 0
    previous_sort_key: tuple[object, ...] | None = None
    for entry in value:
        if type(entry) is not PaperAutonomousInvestmentLedgerEntry:
            raise ValueError("entries must contain exact ledger entries")
        if entry.entry_rank != previous_rank + 1:
            raise ValueError("entry_rank must be contiguous")
        current_sort_key = _entry_sort_key(entry)
        if previous_sort_key is not None and previous_sort_key > current_sort_key:
            raise ValueError("entries must be deterministically sorted")
        previous_rank = entry.entry_rank
        previous_sort_key = current_sort_key
    return value


def _entry_sort_key(
    entry: PaperAutonomousInvestmentLedgerEntry,
) -> tuple[object, ...]:
    return (
        entry.source_generated_at,
        entry.execution_status,
        entry.source_gate_status,
        entry.source_proposal_count,
        entry.source_proposal_total_notional,
        entry.execution_notional,
        entry.reason_codes,
        entry.source_config_version,
        entry.recommended_next_step,
    )


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperAutonomousInvestmentLedgerReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    previous_sort_key: tuple[int, str] | None = None
    for row in value:
        if type(row) is not PaperAutonomousInvestmentLedgerReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason rows")
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        current_sort_key = (-row.source_record_count, row.reason_code)
        if previous_sort_key is not None and previous_sort_key > current_sort_key:
            raise ValueError("reason_code_counts must be deterministic")
        seen.add(row.reason_code)
        previous_sort_key = current_sort_key
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} is required")
    seen: set[str] = set()
    previous_reason_code: str | None = None
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous_reason_code is not None and previous_reason_code > reason_code:
            raise ValueError(f"{field_name} must be sorted")
        seen.add(reason_code)
        previous_reason_code = reason_code
    return value


def _validate_entry_consistency(
    entry: PaperAutonomousInvestmentLedgerEntry,
) -> None:
    if entry.execution_status == "paper_submitted" and entry.execution_notional <= ZERO:
        raise ValueError("paper_submitted entries must have positive notional")
    if entry.execution_status in ("paper_blocked", "paper_held") and (
        entry.execution_notional != ZERO
    ):
        raise ValueError("blocked/held entries must have zero notional")


def _validate_report_consistency(
    report: PaperAutonomousInvestmentLedgerReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.ledger_status]:
        raise ValueError("recommended_next_step must match ledger_status")
    if report.source_record_count != len(report.entries):
        raise ValueError("source_record_count must match entries")
    if report.submitted_count != _status_count(report.entries, "paper_submitted"):
        raise ValueError("submitted_count must match entries")
    if report.held_count != _status_count(report.entries, "paper_held"):
        raise ValueError("held_count must match entries")
    if report.blocked_count != _status_count(report.entries, "paper_blocked"):
        raise ValueError("blocked_count must match entries")
    if report.total_submitted_notional != _total_submitted_notional(report.entries):
        raise ValueError("total_submitted_notional must match entries")
    if report.held_zero_notional_count != _zero_notional_count(
        report.entries,
        "paper_held",
    ):
        raise ValueError("held_zero_notional_count must match entries")
    if report.blocked_zero_notional_count != _zero_notional_count(
        report.entries,
        "paper_blocked",
    ):
        raise ValueError("blocked_zero_notional_count must match entries")
    if tuple(
        (row.reason_code, row.source_record_count)
        for row in report.reason_code_counts
    ) != _reason_counts_from_entries(report.entries):
        raise ValueError("reason_code_counts must match entries")
    if report.latest_generated_at != _latest_generated_at(report.entries):
        raise ValueError("latest_generated_at must match entries")
    if report.ledger_status != _ledger_status(report.reason_codes):
        raise ValueError("ledger_status must match reason_codes")
    has_pass_reason = PASS_REASON_CODE in report.reason_codes
    has_other_reason = any(
        reason_code in BLOCKED_REASON_CODES or reason_code in WATCH_REASON_CODES
        for reason_code in report.reason_codes
    )
    if has_pass_reason and has_other_reason:
        raise ValueError("pass reason must not be mixed with watch or blocked reasons")
    if report.source_record_count == 0:
        if report.latest_generated_at is not None:
            raise ValueError("latest_generated_at must be absent without source records")
        if report.latest_age_seconds is not None:
            raise ValueError("latest_age_seconds must be absent without source records")
        if report.reason_code_counts:
            raise ValueError("reason_code_counts must be empty without source records")
    else:
        if report.latest_generated_at is None:
            raise ValueError("latest_generated_at is required with source records")
        if report.latest_age_seconds is None:
            raise ValueError("latest_age_seconds is required with source records")
        if report.latest_generated_at > report.generated_at:
            raise ValueError("latest_generated_at must not be newer than generated_at")
        if report.latest_age_seconds != _latest_source_age_seconds(
            generated_at=report.generated_at,
            source_generated_at=report.latest_generated_at,
        ):
            raise ValueError("latest_age_seconds must match latest_generated_at")


def _reason_counts_from_entries(
    entries: tuple[PaperAutonomousInvestmentLedgerEntry, ...],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for entry in entries:
        for reason_code in entry.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        ),
    )


def _require_ledger_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in LEDGER_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_execution_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in EXECUTION_STATUSES:
        raise ValueError(f"{field_name} must be one of {EXECUTION_STATUSES}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be a positive int")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _quantize(value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("decimal value must be a Decimal")
    if not value.is_finite():
        raise ValueError("decimal value must be finite")
    return value.quantize(QUANTUM)


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


def _validate_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
