"""DB-API repository for paper autonomous allocation proposal reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row import (
    PaperAutonomousAllocationProposalDbRow,
    paper_autonomous_allocation_proposal_report_from_db_row,
    paper_autonomous_allocation_proposal_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal import (
        PaperAutonomousAllocationProposalReport,
    )


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_REPORTS_TABLE",
    "PaperAutonomousAllocationProposalInsertResult",
    "insert_paper_autonomous_allocation_proposal_report",
    "insert_paper_autonomous_allocation_proposal_report_with_result",
    "load_paper_autonomous_allocation_proposal_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_POSTGRES_IDENTIFIER_MAX_LENGTH = 63
_TABLE_NAME_ERROR = "table_name must be a simple lowercase identifier"
_STATUSES = ("pass", "watch", "blocked")
DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_REPORTS_TABLE = (
    "paper_autonomous_allocation_proposal_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "proposal_status",
    "recommended_next_step",
    "reason_codes_json",
    "reason_code_counts_json",
    "screening_gate_generated_at",
    "screening_gate_config_version",
    "screening_gate_status",
    "screening_gate_recommended_next_step",
    "queue_risk_generated_at",
    "queue_risk_config_version",
    "queue_risk_status",
    "queue_risk_recommended_next_step",
    "source_queue_report_count",
    "source_queue_ready_count",
    "source_queue_watch_count",
    "source_queue_blocked_count",
    "allocation_config_version",
    "allocation_generated_at",
    "allocation_input_count",
    "allocation_row_count",
    "allocation_allocated_count",
    "allocation_capped_count",
    "allocation_no_budget_count",
    "allocation_non_recommend_count",
    "allocation_skipped_count",
    "allocation_total_requested_paper_notional",
    "allocation_total_allocated_paper_notional",
    "allocation_remaining_paper_budget",
    "allocation_total_paper_budget",
    "allocation_max_paper_notional_per_market",
    "allocation_max_paper_notional_per_event",
    "allocation_max_paper_notional_per_theme",
    "allocation_max_paper_notional_per_correlation_group",
    "allocation_rows_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalInsertResult:
    row: PaperAutonomousAllocationProposalDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperAutonomousAllocationProposalDbRow:
            raise ValueError("row must be a PaperAutonomousAllocationProposalDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_autonomous_allocation_proposal_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_REPORTS_TABLE,
) -> PaperAutonomousAllocationProposalDbRow:
    return insert_paper_autonomous_allocation_proposal_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_autonomous_allocation_proposal_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_REPORTS_TABLE,
) -> PaperAutonomousAllocationProposalInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_autonomous_allocation_proposal_report_to_db_row(report)
    columns = ",\n            ".join(_SELECT_COLUMNS)
    placeholders = ", ".join("%s" for _ in _SELECT_COLUMNS)
    sql = f"""
        INSERT INTO {table_name} (
            {columns}
        ) VALUES ({placeholders})
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = tuple(getattr(row, column) for column in _SELECT_COLUMNS)
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        rowcount = cursor.rowcount
    finally:
        try:
            cursor.close()
        except Exception:
            pass
    if rowcount not in (0, 1):
        raise ValueError("insert rowcount must be 0 or 1")
    return PaperAutonomousAllocationProposalInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_autonomous_allocation_proposal_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    proposal_status: str | None = None,
    screening_gate_status: str | None = None,
    allocation_config_version: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_REPORTS_TABLE,
) -> tuple["PaperAutonomousAllocationProposalReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if proposal_status is not None:
        _require_status("proposal_status", proposal_status)
    if screening_gate_status is not None:
        _require_status("screening_gate_status", screening_gate_status)
    if allocation_config_version is not None:
        _require_canonical_string(
            "allocation_config_version",
            allocation_config_version,
        )
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if proposal_status is not None:
        conditions.append("proposal_status = %s")
        params.append(proposal_status)
    if screening_gate_status is not None:
        conditions.append("screening_gate_status = %s")
        params.append(screening_gate_status)
    if allocation_config_version is not None:
        conditions.append("allocation_config_version = %s")
        params.append(allocation_config_version)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    limit_clause = ""
    if limit is not None:
        limit_clause = "LIMIT %s"
        params.append(limit)

    columns = ",\n            ".join(_SELECT_COLUMNS)
    sql = f"""
        SELECT
            {columns}
        FROM {table_name}
        {where_clause}
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        {limit_clause}
        """
    cursor = connection.cursor()
    try:
        cursor.execute(sql, tuple(params))
        records = cursor.fetchall()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(paper_autonomous_allocation_proposal_report_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperAutonomousAllocationProposalDbRow:
    if isinstance(record, PaperAutonomousAllocationProposalDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected allocation proposal columns")
    kwargs = dict(zip(_SELECT_COLUMNS, values, strict=True))
    kwargs["reason_codes_json"] = _normalize_json_array(
        "reason_codes_json",
        kwargs["reason_codes_json"],
    )
    kwargs["reason_code_counts_json"] = _normalize_json_array(
        "reason_code_counts_json",
        kwargs["reason_code_counts_json"],
    )
    kwargs["allocation_rows_json"] = _normalize_json_array(
        "allocation_rows_json",
        kwargs["allocation_rows_json"],
    )
    kwargs["payload_json"] = _normalize_json_object(
        "payload_json",
        kwargs["payload_json"],
    )
    return PaperAutonomousAllocationProposalDbRow(**kwargs)


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


def _validate_table_name(value: str) -> str:
    if (
        type(value) is not str
        or len(value) > _POSTGRES_IDENTIFIER_MAX_LENGTH
        or _IDENTIFIER_PATTERN.fullmatch(value) is None
    ):
        raise ValueError(_TABLE_NAME_ERROR)
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
