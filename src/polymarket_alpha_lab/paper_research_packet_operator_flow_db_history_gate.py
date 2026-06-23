"""Pure gate reducer for persisted paper operator-flow DB history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history import (
    PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow,
    PaperResearchPacketOperatorFlowDbHistoryReport,
    PaperResearchPacketOperatorFlowDbHistoryStatusRow,
)

DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_HISTORY_GATE_CONFIG_VERSION = (
    "paper-research-packet-operator-flow-db-history-gate-v0"
)

FLOW_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_autonomous_screening_decision_support",
    "watch": "throttle_paper_autonomous_screening_decision_support",
    "blocked": "block_paper_autonomous_screening_decision_support",
}
PASS_REASON_CODE = "paper_operator_flow_db_history_gate_passed"
BLOCKED_REASON_CODES = frozenset(
    (
        "insufficient_operator_flow_db_history",
        "source_operator_flow_db_history_blocked",
        "latest_operator_flow_blocked",
        "consecutive_operator_flow_blocked_threshold_exceeded",
        "missing_latest_operator_flow_history_timestamp",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "source_operator_flow_db_history_watch",
        "latest_operator_flow_watch",
        "consecutive_operator_flow_watch_threshold_exceeded",
        "duplicate_operator_flow_generated_at_threshold_exceeded",
        "stale_operator_flow_db_history",
    ),
)

__all__ = (
    "DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_HISTORY_GATE_CONFIG_VERSION",
    "PaperResearchPacketOperatorFlowDbHistoryGateConfig",
    "PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount",
    "PaperResearchPacketOperatorFlowDbHistoryGateReport",
    "build_paper_research_packet_operator_flow_db_history_gate_report",
)


@dataclass(frozen=True)
class PaperResearchPacketOperatorFlowDbHistoryGateConfig:
    config_version: str = (
        DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_HISTORY_GATE_CONFIG_VERSION
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
class PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount:
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
class PaperResearchPacketOperatorFlowDbHistoryGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[
        PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount,
        ...
    ]
    source_report_count: int
    latest_source_generated_at: datetime | None
    latest_source_age_seconds: int | None
    source_history_status: str
    latest_flow_status: str | None
    latest_quality_status: str | None
    latest_operator_history_status: str | None
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
        _require_flow_status("gate_status", self.gate_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_nonnegative_int("source_report_count", self.source_report_count)
        _require_optional_nonnegative_int(
            "latest_source_age_seconds",
            self.latest_source_age_seconds,
        )
        _require_flow_status("source_history_status", self.source_history_status)
        if self.latest_flow_status is not None:
            _require_flow_status("latest_flow_status", self.latest_flow_status)
        if self.latest_quality_status is not None:
            _require_flow_status("latest_quality_status", self.latest_quality_status)
        if self.latest_operator_history_status is not None:
            _require_flow_status(
                "latest_operator_history_status",
                self.latest_operator_history_status,
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


def build_paper_research_packet_operator_flow_db_history_gate_report(
    history_report: object,
    *,
    config: PaperResearchPacketOperatorFlowDbHistoryGateConfig,
    generated_at: datetime,
) -> PaperResearchPacketOperatorFlowDbHistoryGateReport:
    if type(history_report) is not PaperResearchPacketOperatorFlowDbHistoryReport:
        raise ValueError(
            "history_report must be a PaperResearchPacketOperatorFlowDbHistoryReport",
        )
    if type(config) is not PaperResearchPacketOperatorFlowDbHistoryGateConfig:
        raise ValueError(
            "config must be a PaperResearchPacketOperatorFlowDbHistoryGateConfig",
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
    return PaperResearchPacketOperatorFlowDbHistoryGateReport(
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
        latest_flow_status=history_report.latest_flow_status,
        latest_quality_status=history_report.latest_quality_status,
        latest_operator_history_status=history_report.latest_history_status,
        duplicate_generated_at_count=history_report.duplicate_generated_at_count,
        consecutive_latest_pass_count=history_report.consecutive_latest_pass_count,
        consecutive_latest_watch_count=history_report.consecutive_latest_watch_count,
        consecutive_latest_blocked_count=history_report.consecutive_latest_blocked_count,
        reason_codes=reason_codes,
    )


def _gate_reason_codes(
    *,
    history_report: PaperResearchPacketOperatorFlowDbHistoryReport,
    config: PaperResearchPacketOperatorFlowDbHistoryGateConfig,
    latest_source_age_seconds: int | None,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if history_report.report_count < config.min_history_report_count:
        reason_codes.append("insufficient_operator_flow_db_history")
    if history_report.history_status == "blocked":
        reason_codes.append("source_operator_flow_db_history_blocked")
    if history_report.latest_flow_status == "blocked":
        reason_codes.append("latest_operator_flow_blocked")
    if (
        history_report.consecutive_latest_blocked_count
        > config.max_consecutive_latest_blocked_count
    ):
        reason_codes.append("consecutive_operator_flow_blocked_threshold_exceeded")
    if history_report.latest_report_generated_at is None:
        reason_codes.append("missing_latest_operator_flow_history_timestamp")

    if history_report.history_status == "watch":
        reason_codes.append("source_operator_flow_db_history_watch")
    if history_report.latest_flow_status == "watch":
        reason_codes.append("latest_operator_flow_watch")
    if (
        history_report.consecutive_latest_watch_count
        > config.max_consecutive_latest_watch_count
    ):
        reason_codes.append("consecutive_operator_flow_watch_threshold_exceeded")
    if history_report.duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        reason_codes.append("duplicate_operator_flow_generated_at_threshold_exceeded")
    if (
        latest_source_age_seconds is not None
        and latest_source_age_seconds > config.max_latest_age_seconds
    ):
        reason_codes.append("stale_operator_flow_db_history")

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
) -> tuple[PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for reason_code in reason_codes:
        counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount(
            reason_code,
            report_count,
        )
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _validate_history_report(
    history_report: PaperResearchPacketOperatorFlowDbHistoryReport,
) -> None:
    _validate_hard_flags("history report", history_report)
    _require_canonical_string("source config_version", history_report.config_version)
    _require_flow_status("source history_status", history_report.history_status)
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
    history_report: PaperResearchPacketOperatorFlowDbHistoryReport,
) -> None:
    rows = history_report.flow_status_rows
    if type(rows) is not tuple or len(rows) != len(FLOW_STATUSES):
        raise ValueError("flow_status_rows must cover pass, watch, and blocked")
    seen: list[str] = []
    total_count = 0
    for row in rows:
        if type(row) is not PaperResearchPacketOperatorFlowDbHistoryStatusRow:
            raise ValueError("flow_status_rows must contain exact status rows")
        _validate_hard_flags("flow status row", row)
        _require_flow_status("flow_status", row.flow_status)
        _require_nonnegative_int("status_count", row.status_count)
        seen.append(row.flow_status)
        total_count += row.status_count
    if tuple(seen) != FLOW_STATUSES:
        raise ValueError("flow_status_rows must be pass, watch, blocked")
    if total_count != history_report.report_count:
        raise ValueError("flow_status_rows must sum to source report_count")
    if history_report.duplicate_generated_at_count >= max(history_report.report_count, 1):
        raise ValueError("duplicate_generated_at_count must be less than report_count")
    latest_status = history_report.latest_flow_status
    if latest_status is not None:
        matching_count = _count_for_status(rows, latest_status)
        if matching_count <= 0:
            raise ValueError("flow_status_rows must cover latest_flow_status")


def _validate_source_latest_fields(
    history_report: PaperResearchPacketOperatorFlowDbHistoryReport,
) -> None:
    if history_report.latest_flow_status is not None:
        _require_flow_status("latest_flow_status", history_report.latest_flow_status)
    if history_report.latest_quality_status is not None:
        _require_flow_status("latest_quality_status", history_report.latest_quality_status)
    if history_report.latest_history_status is not None:
        _require_flow_status("latest_history_status", history_report.latest_history_status)
    _require_optional_nonnegative_int(
        "latest_packet_row_count",
        history_report.latest_packet_row_count,
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
        if history_report.latest_flow_status is not None:
            raise ValueError("empty source history cannot have latest_flow_status")
        return
    if history_report.latest_flow_status is None:
        raise ValueError("latest_flow_status is required for source reports")
    if positive_statuses != (history_report.latest_flow_status,):
        raise ValueError("consecutive latest count must match latest_flow_status")
    latest_count = latest_counts[history_report.latest_flow_status]
    if latest_count > history_report.report_count:
        raise ValueError("consecutive latest count must not exceed source count")
    if latest_count > _count_for_status(
        history_report.flow_status_rows,
        history_report.latest_flow_status,
    ):
        raise ValueError("consecutive latest count must not exceed status count")


def _validate_source_reason_rows(
    history_report: PaperResearchPacketOperatorFlowDbHistoryReport,
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
        if type(row) is not PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow:
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
    report: PaperResearchPacketOperatorFlowDbHistoryGateReport,
) -> None:
    expected_next_step = NEXT_STEP_BY_STATUS[report.gate_status]
    if report.recommended_next_step != expected_next_step:
        raise ValueError("recommended_next_step must match gate_status")
    if tuple(row.reason_code for row in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
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
) -> tuple[PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_code_counts is required")
    previous_key: tuple[int, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount:
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
    rows: tuple[PaperResearchPacketOperatorFlowDbHistoryStatusRow, ...],
    flow_status: str,
) -> int:
    for row in rows:
        if row.flow_status == flow_status:
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


def _require_flow_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FLOW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


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
