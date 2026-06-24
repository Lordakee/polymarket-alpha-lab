"""Pure gate reducer for persisted paper allocation proposal DB history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    PaperAutonomousAllocationProposalDbHistoryReasonCodeRow,
    PaperAutonomousAllocationProposalDbHistoryReport,
    PaperAutonomousAllocationProposalDbHistoryStatusRow,
)


DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_GATE_CONFIG_VERSION = (
    "paper-autonomous-allocation-proposal-db-history-gate-v0"
)

PROPOSAL_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_autonomous_allocation_proposal_history_review",
    "watch": "throttle_paper_autonomous_allocation_proposal_history_review",
    "blocked": "block_paper_autonomous_allocation_proposal_history_review",
}
PASS_REASON_CODE = "paper_autonomous_allocation_proposal_db_history_gate_passed"
BLOCKED_REASON_CODES = frozenset(
    (
        "insufficient_allocation_proposal_db_history",
        "source_allocation_proposal_db_history_blocked",
        "latest_allocation_proposal_blocked",
        "consecutive_allocation_proposal_blocked_threshold_exceeded",
        "missing_latest_allocation_proposal_history_timestamp",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "source_allocation_proposal_db_history_watch",
        "latest_allocation_proposal_watch",
        "consecutive_allocation_proposal_watch_threshold_exceeded",
        "duplicate_allocation_proposal_generated_at_threshold_exceeded",
        "stale_allocation_proposal_db_history",
    ),
)

__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_GATE_CONFIG_VERSION",
    "PaperAutonomousAllocationProposalDbHistoryGateConfig",
    "PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount",
    "PaperAutonomousAllocationProposalDbHistoryGateReport",
    "build_paper_autonomous_allocation_proposal_db_history_gate_report",
)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryGateConfig:
    config_version: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_GATE_CONFIG_VERSION
    )
    min_history_report_count: int = 3
    max_latest_age_seconds: int = 86400
    max_consecutive_latest_watch_count: int = 0
    max_consecutive_latest_blocked_count: int = 0
    max_duplicate_generated_at_count: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_history_report_count",
            self.min_history_report_count,
        )
        for field_name in (
            "max_latest_age_seconds",
            "max_consecutive_latest_watch_count",
            "max_consecutive_latest_blocked_count",
            "max_duplicate_generated_at_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[
        PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount,
        ...
    ]
    source_report_count: int
    latest_source_generated_at: datetime | None
    latest_source_age_seconds: int | None
    source_history_status: str
    latest_proposal_status: str | None
    latest_screening_gate_status: str | None
    latest_queue_risk_status: str | None
    latest_allocation_input_count: int | None
    latest_allocation_row_count: int | None
    latest_allocated_count: int | None
    latest_total_allocated_paper_notional: Decimal | None
    duplicate_generated_at_count: int
    consecutive_latest_pass_count: int
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc("source_generated_at", self.source_generated_at),
        )
        object.__setattr__(
            self,
            "latest_source_generated_at",
            _as_optional_utc(
                "latest_source_generated_at",
                self.latest_source_generated_at,
            ),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_proposal_status("gate_status", self.gate_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_nonnegative_int("source_report_count", self.source_report_count)
        _require_optional_nonnegative_int(
            "latest_source_age_seconds",
            self.latest_source_age_seconds,
        )
        _require_proposal_status("source_history_status", self.source_history_status)
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
        for field_name in (
            "duplicate_generated_at_count",
            "consecutive_latest_pass_count",
            "consecutive_latest_watch_count",
            "consecutive_latest_blocked_count",
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
        _validate_gate_report(self)
        _validate_hard_flags("gate report", self)


def build_paper_autonomous_allocation_proposal_db_history_gate_report(
    history_report: object,
    *,
    config: PaperAutonomousAllocationProposalDbHistoryGateConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryGateReport:
    if type(history_report) is not PaperAutonomousAllocationProposalDbHistoryReport:
        raise ValueError(
            "history_report must be a PaperAutonomousAllocationProposalDbHistoryReport",
        )
    if type(config) is not PaperAutonomousAllocationProposalDbHistoryGateConfig:
        raise ValueError(
            "config must be a PaperAutonomousAllocationProposalDbHistoryGateConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _validate_hard_flags("config", config)
    _validate_history_report(history_report)

    generated_at_utc = _as_utc("generated_at", generated_at)
    latest_source_generated_at = _as_optional_utc(
        "latest_report_generated_at",
        history_report.latest_report_generated_at,
    )
    latest_source_age_seconds = _latest_source_age_seconds(
        generated_at_utc,
        latest_source_generated_at,
    )
    reason_codes = _gate_reason_codes(
        history_report=history_report,
        config=config,
        latest_source_age_seconds=latest_source_age_seconds,
    )
    gate_status = _gate_status(reason_codes)
    return PaperAutonomousAllocationProposalDbHistoryGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_config_version=history_report.config_version,
        source_generated_at=history_report.generated_at,
        gate_status=gate_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[gate_status],
        reason_code_counts=_reason_code_counts(reason_codes),
        source_report_count=history_report.report_count,
        latest_source_generated_at=latest_source_generated_at,
        latest_source_age_seconds=latest_source_age_seconds,
        source_history_status=history_report.history_status,
        latest_proposal_status=history_report.latest_proposal_status,
        latest_screening_gate_status=history_report.latest_screening_gate_status,
        latest_queue_risk_status=history_report.latest_queue_risk_status,
        latest_allocation_input_count=history_report.latest_allocation_input_count,
        latest_allocation_row_count=history_report.latest_allocation_row_count,
        latest_allocated_count=history_report.latest_allocated_count,
        latest_total_allocated_paper_notional=(
            history_report.latest_total_allocated_paper_notional
        ),
        duplicate_generated_at_count=history_report.duplicate_generated_at_count,
        consecutive_latest_pass_count=history_report.consecutive_latest_pass_count,
        consecutive_latest_watch_count=history_report.consecutive_latest_watch_count,
        consecutive_latest_blocked_count=history_report.consecutive_latest_blocked_count,
        reason_codes=reason_codes,
    )


def _gate_reason_codes(
    *,
    history_report: PaperAutonomousAllocationProposalDbHistoryReport,
    config: PaperAutonomousAllocationProposalDbHistoryGateConfig,
    latest_source_age_seconds: int | None,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if history_report.report_count < config.min_history_report_count:
        reason_codes.append("insufficient_allocation_proposal_db_history")
    if history_report.history_status == "blocked":
        reason_codes.append("source_allocation_proposal_db_history_blocked")
    if history_report.latest_proposal_status == "blocked":
        reason_codes.append("latest_allocation_proposal_blocked")
    if (
        history_report.consecutive_latest_blocked_count
        > config.max_consecutive_latest_blocked_count
    ):
        reason_codes.append(
            "consecutive_allocation_proposal_blocked_threshold_exceeded",
        )
    if history_report.latest_report_generated_at is None:
        reason_codes.append("missing_latest_allocation_proposal_history_timestamp")

    if history_report.history_status == "watch":
        reason_codes.append("source_allocation_proposal_db_history_watch")
    if history_report.latest_proposal_status == "watch":
        reason_codes.append("latest_allocation_proposal_watch")
    if (
        history_report.consecutive_latest_watch_count
        > config.max_consecutive_latest_watch_count
    ):
        reason_codes.append(
            "consecutive_allocation_proposal_watch_threshold_exceeded",
        )
    if history_report.duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        reason_codes.append("duplicate_allocation_proposal_generated_at_threshold_exceeded")
    if (
        latest_source_age_seconds is not None
        and latest_source_age_seconds > config.max_latest_age_seconds
    ):
        reason_codes.append("stale_allocation_proposal_db_history")

    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(sorted(set(reason_codes)))


def _gate_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount, ...]:
    return tuple(
        PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount(
            reason_code,
            1,
        )
        for reason_code in reason_codes
    )


def _validate_history_report(
    history_report: PaperAutonomousAllocationProposalDbHistoryReport,
) -> None:
    _validate_hard_flags("history report", history_report)
    _require_canonical_string("source config_version", history_report.config_version)
    _require_proposal_status("source history_status", history_report.history_status)
    _require_nonnegative_int("source report_count", history_report.report_count)
    _as_utc("source generated_at", history_report.generated_at)
    latest_generated_at = _as_optional_utc(
        "source latest_report_generated_at",
        history_report.latest_report_generated_at,
    )
    if latest_generated_at is None and history_report.report_count > 0:
        raise ValueError("latest_report_generated_at is required for source reports")
    if latest_generated_at is not None:
        first_generated_at = _as_optional_utc(
            "source first_report_generated_at",
            history_report.first_report_generated_at,
        )
        if first_generated_at is None:
            raise ValueError("first_report_generated_at is required for source reports")
        if first_generated_at > latest_generated_at:
            raise ValueError("first_report_generated_at must not be after latest")
    _validate_source_status_rows(history_report)
    _validate_source_latest_fields(history_report)
    _validate_source_reason_rows(history_report)


def _validate_source_status_rows(
    history_report: PaperAutonomousAllocationProposalDbHistoryReport,
) -> None:
    rows = history_report.proposal_status_rows
    if type(rows) is not tuple or len(rows) != len(PROPOSAL_STATUSES):
        raise ValueError("proposal_status_rows must cover pass, watch, and blocked")
    seen: list[str] = []
    total_count = 0
    for row in rows:
        if type(row) is not PaperAutonomousAllocationProposalDbHistoryStatusRow:
            raise ValueError("proposal_status_rows must contain exact status rows")
        _validate_hard_flags("proposal status row", row)
        _require_proposal_status("proposal_status", row.proposal_status)
        _require_nonnegative_int("status_count", row.status_count)
        seen.append(row.proposal_status)
        total_count += row.status_count
    if tuple(seen) != PROPOSAL_STATUSES:
        raise ValueError("proposal_status_rows must be pass, watch, blocked")
    if total_count != history_report.report_count:
        raise ValueError("proposal_status_rows must sum to source report_count")
    if history_report.duplicate_generated_at_count >= max(history_report.report_count, 1):
        raise ValueError("duplicate_generated_at_count must be less than report_count")
    latest_status = history_report.latest_proposal_status
    if latest_status is not None and _count_for_status(rows, latest_status) <= 0:
        raise ValueError("proposal_status_rows must cover latest_proposal_status")


def _validate_source_latest_fields(
    history_report: PaperAutonomousAllocationProposalDbHistoryReport,
) -> None:
    if history_report.latest_proposal_status is not None:
        _require_proposal_status(
            "latest_proposal_status",
            history_report.latest_proposal_status,
        )
    if history_report.latest_screening_gate_status is not None:
        _require_proposal_status(
            "latest_screening_gate_status",
            history_report.latest_screening_gate_status,
        )
    if history_report.latest_queue_risk_status is not None:
        _require_proposal_status(
            "latest_queue_risk_status",
            history_report.latest_queue_risk_status,
        )
    for field_name in (
        "latest_allocation_input_count",
        "latest_allocation_row_count",
        "latest_allocated_count",
    ):
        _require_optional_nonnegative_int(field_name, getattr(history_report, field_name))
    _require_optional_decimal(
        "latest_total_allocated_paper_notional",
        history_report.latest_total_allocated_paper_notional,
    )
    for field_name in (
        "duplicate_generated_at_count",
        "consecutive_latest_pass_count",
        "consecutive_latest_watch_count",
        "consecutive_latest_blocked_count",
    ):
        _require_nonnegative_int(field_name, getattr(history_report, field_name))
    latest_counts = {
        "pass": history_report.consecutive_latest_pass_count,
        "watch": history_report.consecutive_latest_watch_count,
        "blocked": history_report.consecutive_latest_blocked_count,
    }
    positive_statuses = tuple(
        status for status, count in latest_counts.items() if count > 0
    )
    if history_report.report_count == 0:
        if positive_statuses:
            raise ValueError("empty source history cannot have latest streaks")
        if history_report.latest_proposal_status is not None:
            raise ValueError("empty source history cannot have latest_proposal_status")
        return
    if history_report.latest_proposal_status is None:
        raise ValueError("latest_proposal_status is required for source reports")
    for field_name in (
        "latest_screening_gate_status",
        "latest_queue_risk_status",
        "latest_allocation_input_count",
        "latest_allocation_row_count",
        "latest_allocated_count",
        "latest_total_allocated_paper_notional",
    ):
        if getattr(history_report, field_name) is None:
            raise ValueError(f"{field_name} is required for source reports")
    if positive_statuses != (history_report.latest_proposal_status,):
        raise ValueError("consecutive latest count must match latest_proposal_status")
    latest_count = latest_counts[history_report.latest_proposal_status]
    if latest_count > history_report.report_count:
        raise ValueError("consecutive latest count must not exceed source count")
    if latest_count > _count_for_status(
        history_report.proposal_status_rows,
        history_report.latest_proposal_status,
    ):
        raise ValueError("consecutive latest count must not exceed status count")


def _validate_source_reason_rows(
    history_report: PaperAutonomousAllocationProposalDbHistoryReport,
) -> None:
    _normalize_reason_codes(
        "latest_reason_codes",
        history_report.latest_reason_codes,
        allow_empty=True,
    )
    rows = history_report.reason_code_rows
    if type(rows) is not tuple:
        raise ValueError("reason_code_rows must be a tuple")
    if history_report.report_count > 0 and not rows:
        raise ValueError("reason_code_rows is required for source reports")
    previous_key: tuple[int, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not PaperAutonomousAllocationProposalDbHistoryReasonCodeRow:
            raise ValueError("reason_code_rows must contain exact reason rows")
        _validate_hard_flags("reason code row", row)
        _require_canonical_string("reason_code", row.reason_code)
        _require_positive_int("report_count", row.report_count)
        if row.reason_code in seen:
            raise ValueError("reason_code_rows must be unique")
        if row.report_count > history_report.report_count:
            raise ValueError("reason_code_rows report_count must not exceed source count")
        key = (-row.report_count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_rows must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    _normalize_reason_codes("source reason_codes", history_report.reason_codes)


def _validate_gate_report(
    report: PaperAutonomousAllocationProposalDbHistoryGateReport,
) -> None:
    expected_next_step = NEXT_STEP_BY_STATUS[report.gate_status]
    if report.recommended_next_step != expected_next_step:
        raise ValueError("recommended_next_step must match gate_status")
    if tuple(row.reason_code for row in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
    if any(row.report_count != 1 for row in report.reason_code_counts):
        raise ValueError("reason_code_counts must be presence counts")
    status_from_reasons = _gate_status(report.reason_codes)
    if report.gate_status != status_from_reasons:
        raise ValueError("gate_status must match reason_codes")
    has_pass_reason = PASS_REASON_CODE in report.reason_codes
    has_other_reason = any(
        reason_code in BLOCKED_REASON_CODES or reason_code in WATCH_REASON_CODES
        for reason_code in report.reason_codes
    )
    if has_pass_reason and has_other_reason:
        raise ValueError("pass reason must not be mixed with watch or blocked reasons")
    if report.latest_source_generated_at is None:
        if report.latest_source_age_seconds is not None:
            raise ValueError("latest_source_age_seconds requires latest timestamp")
    else:
        expected_age = _latest_source_age_seconds(
            report.generated_at,
            report.latest_source_generated_at,
        )
        if report.latest_source_age_seconds != expected_age:
            raise ValueError("latest_source_age_seconds must match latest timestamp")


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_code_counts is required")
    previous_key: tuple[int, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason rows")
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.report_count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _latest_source_age_seconds(
    generated_at: datetime,
    latest_source_generated_at: datetime | None,
) -> int | None:
    if latest_source_generated_at is None:
        return None
    age_seconds = int(
        (
            _as_utc("generated_at", generated_at)
            - _as_utc("latest_source_generated_at", latest_source_generated_at)
        ).total_seconds(),
    )
    if age_seconds < 0:
        raise ValueError("latest_source_age_seconds must be nonnegative")
    return age_seconds


def _count_for_status(
    rows: tuple[PaperAutonomousAllocationProposalDbHistoryStatusRow, ...],
    proposal_status: str,
) -> int:
    for row in rows:
        if row.proposal_status == proposal_status:
            return row.status_count
    return 0


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
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


def _require_proposal_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PROPOSAL_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


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
