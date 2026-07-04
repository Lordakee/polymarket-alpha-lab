"""Pure in-memory source ack recheck status report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import (
    require_team_category_pair,
    require_team_id,
)


DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_STATUS_CONFIG_VERSION = (
    "research-packet-source-ack-recheck-status-v0"
)

ROW_STATUSES = ("overdue", "in_progress", "blocked", "cleared")
REPORT_STATUSES = ("empty", "cleared", "in_progress", "overdue", "blocked")
STATUS_RANK = {
    "blocked": 0,
    "overdue": 1,
    "in_progress": 2,
    "cleared": 3,
}
STATUS_REASON_CODES = (
    "source_ack_recheck_status_blocked",
    "source_ack_recheck_status_overdue",
    "source_ack_recheck_status_in_progress",
    "source_ack_recheck_status_cleared",
)
EMPTY_REASON_CODE = "source_ack_recheck_status_empty"
BLOCKED_REASON_CODES = (
    "source_ack_recheck_blocked_owner_missing",
    "source_ack_recheck_blocked_source_unavailable",
    "source_ack_recheck_blocked_dependency",
)
REASON_CODES = (EMPTY_REASON_CODE, *STATUS_REASON_CODES, *BLOCKED_REASON_CODES)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("cre", "den", "tial"),
        _join_parts("pri", "vate", "_key"),
        _join_parts("sec", "ret"),
        _join_parts("tok", "en"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
        _join_parts("au", "th"),
        _join_parts("li", "ve"),
    ),
)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckStatusConfig:
    config_version: str = DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_STATUS_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("status config", self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckStatusInput:
    recheck_id: str
    acknowledgement_id: str
    packet_id: str
    source_id: str
    source_family: str
    team_id: str
    category_id: str
    requested_at: datetime
    due_at: datetime
    started_at: datetime | None = None
    cleared_at: datetime | None = None
    blocked_at: datetime | None = None
    blocked_reason_code: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "recheck_id",
            "acknowledgement_id",
            "packet_id",
            "source_id",
            "source_family",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        for field_name in ("requested_at", "due_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in ("started_at", "cleared_at", "blocked_at"):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "blocked_reason_code",
            _normalize_optional_blocked_reason_code(
                "blocked_reason_code",
                self.blocked_reason_code,
            ),
        )
        reject_unsafe_surface_fields("source ack recheck status input", self)
        require_paper_only_flags("status input", self)
        _validate_status_input(self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckStatusRow:
    recheck_id: str
    acknowledgement_id: str
    packet_id: str
    source_id: str
    source_family: str
    team_id: str
    category_id: str
    status: str
    requested_at: datetime
    due_at: datetime
    started_at: datetime | None
    cleared_at: datetime | None
    blocked_at: datetime | None
    blocked_reason_code: str | None
    recheck_age_seconds: Decimal
    overdue_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "recheck_id",
            "acknowledgement_id",
            "packet_id",
            "source_id",
            "source_family",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_member("status", self.status, ROW_STATUSES)
        for field_name in ("requested_at", "due_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in ("started_at", "cleared_at", "blocked_at"):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "blocked_reason_code",
            _normalize_optional_blocked_reason_code(
                "blocked_reason_code",
                self.blocked_reason_code,
            ),
        )
        for field_name in ("recheck_age_seconds", "overdue_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("source ack recheck status row", self)
        require_paper_only_flags("status row", self)
        _validate_status_row(self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckStatusSummaryRow:
    team_id: str
    category_id: str
    source_family: str
    status: str
    recheck_count: Decimal
    overdue_count: Decimal
    in_progress_count: Decimal
    blocked_count: Decimal
    cleared_count: Decimal
    overdue_ratio: Decimal
    blocked_ratio: Decimal
    cleared_ratio: Decimal
    max_recheck_age_seconds: Decimal
    max_overdue_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("source_family", self.source_family)
        _require_member("status", self.status, ROW_STATUSES)
        for field_name in (
            "recheck_count",
            "overdue_count",
            "in_progress_count",
            "blocked_count",
            "cleared_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("overdue_ratio", "blocked_ratio", "cleared_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_recheck_age_seconds", "max_overdue_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("source ack recheck status summary row", self)
        require_paper_only_flags("status summary row", self)
        _validate_summary_row(self)


@dataclass(frozen=True)
class ResearchPacketSourceAckRecheckStatusReport:
    generated_at: datetime
    config_version: str
    status: str
    recheck_count: Decimal
    summary_row_count: Decimal
    overdue_count: Decimal
    in_progress_count: Decimal
    blocked_count: Decimal
    cleared_count: Decimal
    overdue_ratio: Decimal
    blocked_ratio: Decimal
    cleared_ratio: Decimal
    max_recheck_age_seconds: Decimal
    max_overdue_age_seconds: Decimal
    rows: tuple[ResearchPacketSourceAckRecheckStatusRow, ...]
    summary_rows: tuple[ResearchPacketSourceAckRecheckStatusSummaryRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_member("status", self.status, REPORT_STATUSES)
        for field_name in (
            "recheck_count",
            "summary_row_count",
            "overdue_count",
            "in_progress_count",
            "blocked_count",
            "cleared_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("overdue_ratio", "blocked_ratio", "cleared_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_recheck_age_seconds", "max_overdue_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_status_rows(self.rows))
        object.__setattr__(
            self,
            "summary_rows",
            _normalize_summary_rows(self.summary_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("source ack recheck status report", self)
        require_paper_only_flags("status report", self)
        _validate_report(self)


def build_research_packet_source_ack_recheck_status_report(
    rechecks: Iterable[ResearchPacketSourceAckRecheckStatusInput],
    *,
    config: ResearchPacketSourceAckRecheckStatusConfig,
    generated_at: datetime,
) -> ResearchPacketSourceAckRecheckStatusReport:
    if type(config) is not ResearchPacketSourceAckRecheckStatusConfig:
        raise ValueError("config must be a ResearchPacketSourceAckRecheckStatusConfig")
    require_paper_only_flags("status config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_status_inputs(rechecks)
    _validate_input_times(inputs, generated_at_utc)
    rows = tuple(
        sorted(
            (_status_row(row, generated_at_utc) for row in inputs),
            key=_status_row_sort_key,
        ),
    )
    summary_rows = _summary_rows(rows)

    return ResearchPacketSourceAckRecheckStatusReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        recheck_count=_count(len(rows)),
        summary_row_count=_count(len(summary_rows)),
        overdue_count=_status_count(rows, "overdue"),
        in_progress_count=_status_count(rows, "in_progress"),
        blocked_count=_status_count(rows, "blocked"),
        cleared_count=_status_count(rows, "cleared"),
        overdue_ratio=_ratio(_status_count(rows, "overdue"), _count(len(rows))),
        blocked_ratio=_ratio(_status_count(rows, "blocked"), _count(len(rows))),
        cleared_ratio=_ratio(_status_count(rows, "cleared"), _count(len(rows))),
        max_recheck_age_seconds=_max_decimal(
            tuple(row.recheck_age_seconds for row in rows),
        ),
        max_overdue_age_seconds=_max_decimal(
            tuple(row.overdue_age_seconds for row in rows),
        ),
        rows=rows,
        summary_rows=summary_rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_packet_source_ack_recheck_status_report_to_payload(
    report: ResearchPacketSourceAckRecheckStatusReport,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketSourceAckRecheckStatusReport:
        raise ValueError("report must be a ResearchPacketSourceAckRecheckStatusReport")
    reject_unsafe_surface_fields("source ack recheck status report", report)
    require_paper_only_flags("status report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("source ack recheck status payload", payload)
    return payload


def _status_row(
    row: ResearchPacketSourceAckRecheckStatusInput,
    generated_at: datetime,
) -> ResearchPacketSourceAckRecheckStatusRow:
    status = _input_status(row, generated_at)
    blocked_reason_code = (
        row.blocked_reason_code if status == "blocked" else None
    )
    return ResearchPacketSourceAckRecheckStatusRow(
        recheck_id=row.recheck_id,
        acknowledgement_id=row.acknowledgement_id,
        packet_id=row.packet_id,
        source_id=row.source_id,
        source_family=row.source_family,
        team_id=row.team_id,
        category_id=row.category_id,
        status=status,
        requested_at=row.requested_at,
        due_at=row.due_at,
        started_at=row.started_at,
        cleared_at=row.cleared_at,
        blocked_at=row.blocked_at,
        blocked_reason_code=blocked_reason_code,
        recheck_age_seconds=_duration_seconds(row.requested_at, generated_at),
        overdue_age_seconds=_overdue_age_seconds(row.due_at, generated_at, status),
        reason_codes=_row_reason_codes(status, blocked_reason_code),
    )


def _input_status(
    row: ResearchPacketSourceAckRecheckStatusInput,
    generated_at: datetime,
) -> str:
    if row.blocked_at is not None:
        return "blocked"
    if row.cleared_at is not None:
        return "cleared"
    if generated_at > row.due_at:
        return "overdue"
    return "in_progress"


def _summary_rows(
    rows: tuple[ResearchPacketSourceAckRecheckStatusRow, ...],
) -> tuple[ResearchPacketSourceAckRecheckStatusSummaryRow, ...]:
    grouped: dict[
        tuple[str, str, str],
        list[ResearchPacketSourceAckRecheckStatusRow],
    ] = {}
    for row in rows:
        key = (row.team_id, row.category_id, row.source_family)
        grouped.setdefault(key, []).append(row)

    summary_rows = tuple(
        _summary_row(key, tuple(value)) for key, value in grouped.items()
    )
    return tuple(sorted(summary_rows, key=_summary_row_sort_key))


def _summary_row(
    key: tuple[str, str, str],
    rows: tuple[ResearchPacketSourceAckRecheckStatusRow, ...],
) -> ResearchPacketSourceAckRecheckStatusSummaryRow:
    recheck_count = _count(len(rows))
    overdue_count = _status_count(rows, "overdue")
    in_progress_count = _status_count(rows, "in_progress")
    blocked_count = _status_count(rows, "blocked")
    cleared_count = _status_count(rows, "cleared")
    return ResearchPacketSourceAckRecheckStatusSummaryRow(
        team_id=key[0],
        category_id=key[1],
        source_family=key[2],
        status=_rollup_status(rows),
        recheck_count=recheck_count,
        overdue_count=overdue_count,
        in_progress_count=in_progress_count,
        blocked_count=blocked_count,
        cleared_count=cleared_count,
        overdue_ratio=_ratio(overdue_count, recheck_count),
        blocked_ratio=_ratio(blocked_count, recheck_count),
        cleared_ratio=_ratio(cleared_count, recheck_count),
        max_recheck_age_seconds=_max_decimal(
            tuple(row.recheck_age_seconds for row in rows),
        ),
        max_overdue_age_seconds=_max_decimal(
            tuple(row.overdue_age_seconds for row in rows),
        ),
        reason_codes=_summary_reason_codes(rows),
    )


def _normalize_status_inputs(
    value: Iterable[ResearchPacketSourceAckRecheckStatusInput],
) -> tuple[ResearchPacketSourceAckRecheckStatusInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rechecks must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rechecks must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketSourceAckRecheckStatusInput:
            raise ValueError(
                "rechecks must contain ResearchPacketSourceAckRecheckStatusInput values",
            )
        require_paper_only_flags("status input", row)
        if row.recheck_id in seen:
            raise ValueError("recheck_id values must be unique")
        seen.add(row.recheck_id)
    return rows


def _normalize_status_rows(
    value: tuple[ResearchPacketSourceAckRecheckStatusRow, ...],
) -> tuple[ResearchPacketSourceAckRecheckStatusRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketSourceAckRecheckStatusRow:
            raise ValueError("rows must contain status row values")
        require_paper_only_flags("status row", row)
        if row.recheck_id in seen:
            raise ValueError("row recheck_id values must be unique")
        seen.add(row.recheck_id)
    return tuple(sorted(rows, key=_status_row_sort_key))


def _normalize_summary_rows(
    value: tuple[ResearchPacketSourceAckRecheckStatusSummaryRow, ...],
) -> tuple[ResearchPacketSourceAckRecheckStatusSummaryRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("summary_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("summary_rows must be an iterable") from exc
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketSourceAckRecheckStatusSummaryRow:
            raise ValueError("summary_rows must contain summary row values")
        require_paper_only_flags("status summary row", row)
        key = (row.team_id, row.category_id, row.source_family)
        if key in seen:
            raise ValueError("summary_rows must be unique by team, category, source family")
        seen.add(key)
    return tuple(sorted(rows, key=_summary_row_sort_key))


def _validate_input_times(
    rows: tuple[ResearchPacketSourceAckRecheckStatusInput, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        for field_name in ("requested_at", "started_at", "cleared_at", "blocked_at"):
            value = getattr(row, field_name)
            if value is not None and value > generated_at:
                raise ValueError(f"{field_name} must be <= generated_at")


def _validate_status_input(row: ResearchPacketSourceAckRecheckStatusInput) -> None:
    if row.due_at < row.requested_at:
        raise ValueError("due_at must be >= requested_at")
    if row.started_at is not None and row.started_at < row.requested_at:
        raise ValueError("started_at must be >= requested_at")
    if row.cleared_at is not None and row.cleared_at < row.requested_at:
        raise ValueError("cleared_at must be >= requested_at")
    if row.blocked_at is not None and row.blocked_at < row.requested_at:
        raise ValueError("blocked_at must be >= requested_at")
    if (
        row.started_at is not None
        and row.cleared_at is not None
        and row.cleared_at < row.started_at
    ):
        raise ValueError("cleared_at must be >= started_at")
    if (
        row.started_at is not None
        and row.blocked_at is not None
        and row.blocked_at < row.started_at
    ):
        raise ValueError("blocked_at must be >= started_at")
    if row.cleared_at is not None and row.blocked_at is not None:
        raise ValueError("cleared_at and blocked_at must not both be set")
    if row.blocked_at is not None and row.blocked_reason_code is None:
        raise ValueError("blocked_reason_code is required when blocked_at is set")
    if row.blocked_at is None and row.blocked_reason_code is not None:
        raise ValueError("blocked_reason_code requires blocked_at")


def _validate_status_row(row: ResearchPacketSourceAckRecheckStatusRow) -> None:
    if row.due_at < row.requested_at:
        raise ValueError("due_at must be >= requested_at")
    if row.cleared_at is not None and row.blocked_at is not None:
        raise ValueError("cleared_at and blocked_at must not both be set")
    if row.status == "blocked":
        if row.blocked_at is None or row.blocked_reason_code is None:
            raise ValueError("blocked rows require blocked_at and blocked_reason_code")
    else:
        if row.blocked_at is not None or row.blocked_reason_code is not None:
            raise ValueError("only blocked rows may include blocked fields")
    if row.status == "cleared" and row.cleared_at is None:
        raise ValueError("cleared rows require cleared_at")
    if row.status in ("overdue", "in_progress") and row.cleared_at is not None:
        raise ValueError("active rows must not include cleared_at")
    if row.status == "overdue" and row.overdue_age_seconds <= ZERO_SECONDS:
        raise ValueError("overdue rows require positive overdue_age_seconds")
    if row.status in ("in_progress", "cleared") and row.overdue_age_seconds != ZERO_SECONDS:
        raise ValueError("non-overdue rows require zero overdue_age_seconds")
    if row.reason_codes != _row_reason_codes(row.status, row.blocked_reason_code):
        raise ValueError("reason_codes must match status")


def _validate_summary_row(row: ResearchPacketSourceAckRecheckStatusSummaryRow) -> None:
    counted = (
        row.overdue_count
        + row.in_progress_count
        + row.blocked_count
        + row.cleared_count
    )
    if counted != row.recheck_count:
        raise ValueError("summary counts must add up to recheck_count")
    if row.status != _rollup_status_from_counts(row):
        raise ValueError("status must match summary counts")
    if row.overdue_ratio != _ratio(row.overdue_count, row.recheck_count):
        raise ValueError("overdue_ratio must match overdue_count")
    if row.blocked_ratio != _ratio(row.blocked_count, row.recheck_count):
        raise ValueError("blocked_ratio must match blocked_count")
    if row.cleared_ratio != _ratio(row.cleared_count, row.recheck_count):
        raise ValueError("cleared_ratio must match cleared_count")
    if row.max_overdue_age_seconds > row.max_recheck_age_seconds:
        raise ValueError("max_overdue_age_seconds must be <= max_recheck_age_seconds")
    if _status_reason_code(row.status) not in row.reason_codes:
        raise ValueError("reason_codes must include status reason")


def _validate_report(report: ResearchPacketSourceAckRecheckStatusReport) -> None:
    if report.recheck_count != _count(len(report.rows)):
        raise ValueError("recheck_count must match rows")
    if report.summary_row_count != _count(len(report.summary_rows)):
        raise ValueError("summary_row_count must match summary_rows")
    if report.overdue_count != _status_count(report.rows, "overdue"):
        raise ValueError("overdue_count must match rows")
    if report.in_progress_count != _status_count(report.rows, "in_progress"):
        raise ValueError("in_progress_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.cleared_count != _status_count(report.rows, "cleared"):
        raise ValueError("cleared_count must match rows")
    if report.overdue_ratio != _ratio(report.overdue_count, report.recheck_count):
        raise ValueError("overdue_ratio must match overdue_count")
    if report.blocked_ratio != _ratio(report.blocked_count, report.recheck_count):
        raise ValueError("blocked_ratio must match blocked_count")
    if report.cleared_ratio != _ratio(report.cleared_count, report.recheck_count):
        raise ValueError("cleared_ratio must match cleared_count")
    if report.max_recheck_age_seconds != _max_decimal(
        tuple(row.recheck_age_seconds for row in report.rows),
    ):
        raise ValueError("max_recheck_age_seconds must match rows")
    if report.max_overdue_age_seconds != _max_decimal(
        tuple(row.overdue_age_seconds for row in report.rows),
    ):
        raise ValueError("max_overdue_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.summary_rows != _summary_rows(report.rows):
        raise ValueError("summary_rows must match rows")


def _row_reason_codes(
    status: str,
    blocked_reason_code: str | None,
) -> tuple[str, ...]:
    if status == "blocked":
        if blocked_reason_code is None:
            raise ValueError("blocked_reason_code is required for blocked status")
        return ("source_ack_recheck_status_blocked", blocked_reason_code)
    return (_status_reason_code(status),)


def _summary_reason_codes(
    rows: tuple[ResearchPacketSourceAckRecheckStatusRow, ...],
) -> tuple[str, ...]:
    codes: list[str] = []
    for status in ("blocked", "overdue", "in_progress", "cleared"):
        if any(row.status == status for row in rows):
            codes.append(_status_reason_code(status))
    for code in BLOCKED_REASON_CODES:
        if any(code in row.reason_codes for row in rows):
            codes.append(code)
    return tuple(codes)


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceAckRecheckStatusRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    codes: list[str] = []
    for status in ("blocked", "overdue", "in_progress"):
        if any(row.status == status for row in rows):
            codes.append(_status_reason_code(status))
    if not codes:
        codes.append("source_ack_recheck_status_cleared")
    for code in BLOCKED_REASON_CODES:
        if any(code in row.reason_codes for row in rows):
            codes.append(code)
    return tuple(codes)


def _status_reason_code(status: str) -> str:
    if status == "blocked":
        return "source_ack_recheck_status_blocked"
    if status == "overdue":
        return "source_ack_recheck_status_overdue"
    if status == "in_progress":
        return "source_ack_recheck_status_in_progress"
    if status == "cleared":
        return "source_ack_recheck_status_cleared"
    raise ValueError("status must be known")


def _report_status(rows: tuple[ResearchPacketSourceAckRecheckStatusRow, ...]) -> str:
    if not rows:
        return "empty"
    return _rollup_status(rows)


def _rollup_status(rows: tuple[ResearchPacketSourceAckRecheckStatusRow, ...]) -> str:
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "overdue" for row in rows):
        return "overdue"
    if any(row.status == "in_progress" for row in rows):
        return "in_progress"
    return "cleared"


def _rollup_status_from_counts(
    row: ResearchPacketSourceAckRecheckStatusSummaryRow,
) -> str:
    if row.blocked_count > ZERO_COUNT:
        return "blocked"
    if row.overdue_count > ZERO_COUNT:
        return "overdue"
    if row.in_progress_count > ZERO_COUNT:
        return "in_progress"
    return "cleared"


def _status_row_sort_key(
    row: ResearchPacketSourceAckRecheckStatusRow,
) -> tuple[int, str, str, str, datetime, str]:
    return (
        STATUS_RANK[row.status],
        row.team_id,
        row.category_id,
        row.source_family,
        row.due_at,
        row.recheck_id,
    )


def _summary_row_sort_key(
    row: ResearchPacketSourceAckRecheckStatusSummaryRow,
) -> tuple[int, str, str, str]:
    return (
        STATUS_RANK[row.status],
        row.team_id,
        row.category_id,
        row.source_family,
    )


def _status_count(
    rows: tuple[ResearchPacketSourceAckRecheckStatusRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("end time must be >= start time")
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
        return seconds.quantize(SECONDS_QUANTUM)


def _overdue_age_seconds(due_at: datetime, generated_at: datetime, status: str) -> Decimal:
    if status in ("in_progress", "cleared"):
        return ZERO_SECONDS
    if generated_at <= due_at:
        return ZERO_SECONDS
    return _duration_seconds(due_at, generated_at)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return max(values, default=ZERO_SECONDS)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return decimal_value.quantize(COUNT_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be a whole-number Decimal") from exc


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > Decimal("1"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return decimal_value.quantize(RATIO_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be a ratio Decimal") from exc


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return decimal_value.quantize(SECONDS_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be a seconds Decimal") from exc


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_text(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain a canonical string")


def _reject_unsafe_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain a canonical string")
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains an unsafe surface fragment")


def _normalize_optional_blocked_reason_code(
    field_name: str,
    value: object,
) -> str | None:
    if value is None:
        return None
    if type(value) is not str or value not in BLOCKED_REASON_CODES:
        raise ValueError(f"{field_name} must be a known blocked reason code")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for code in codes:
        if type(code) is not str or code not in REASON_CODES:
            raise ValueError(f"{field_name} must contain known reason codes")
        if code not in seen:
            seen.add(code)
            normalized.append(code)
    return tuple(normalized)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_STATUS_CONFIG_VERSION",
    "ResearchPacketSourceAckRecheckStatusConfig",
    "ResearchPacketSourceAckRecheckStatusInput",
    "ResearchPacketSourceAckRecheckStatusReport",
    "ResearchPacketSourceAckRecheckStatusRow",
    "ResearchPacketSourceAckRecheckStatusSummaryRow",
    "build_research_packet_source_ack_recheck_status_report",
    "research_packet_source_ack_recheck_status_report_to_payload",
)
