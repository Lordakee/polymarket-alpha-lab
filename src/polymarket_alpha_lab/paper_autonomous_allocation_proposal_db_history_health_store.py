"""DB-API repository for paper allocation proposal DB-history health reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
    HEALTH_STATUSES,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row import (
    PaperAutonomousAllocationProposalDbHistoryHealthDbRow,
    paper_autonomous_allocation_proposal_db_history_health_report_from_db_row,
    paper_autonomous_allocation_proposal_db_history_health_report_to_db_row,
)


if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
        PaperAutonomousAllocationProposalDbHistoryHealthReport,
    )


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE",
    "PaperAutonomousAllocationProposalDbHistoryHealthInsertResult",
    "insert_paper_autonomous_allocation_proposal_db_history_health_report",
    "insert_paper_autonomous_allocation_proposal_db_history_health_report_with_result",
    "load_paper_autonomous_allocation_proposal_db_history_health_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_POSTGRES_IDENTIFIER_MAX_LENGTH = 63
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"
DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE = (
    "paper_autonomous_allocation_proposal_db_history_health_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "health_status",
    "recommended_next_step",
    "history_report_count",
    "pass_report_count",
    "watch_report_count",
    "blocked_report_count",
    "latest_history_status",
    "latest_proposal_status",
    "latest_allocated_count",
    "latest_total_allocated_paper_notional",
    "max_source_age_seconds",
    "latest_source_age_seconds",
    "duplicate_latest_report_generated_at_count",
    "reason_code_counts_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryHealthInsertResult:
    row: PaperAutonomousAllocationProposalDbHistoryHealthDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperAutonomousAllocationProposalDbHistoryHealthDbRow:
            raise ValueError(
                "row must be a "
                "PaperAutonomousAllocationProposalDbHistoryHealthDbRow",
            )
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_autonomous_allocation_proposal_db_history_health_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE
    ),
) -> PaperAutonomousAllocationProposalDbHistoryHealthDbRow:
    return (
        insert_paper_autonomous_allocation_proposal_db_history_health_report_with_result(
            connection,
            report,
            table_name=table_name,
        ).row
    )


def insert_paper_autonomous_allocation_proposal_db_history_health_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE
    ),
) -> PaperAutonomousAllocationProposalDbHistoryHealthInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_autonomous_allocation_proposal_db_history_health_report_to_db_row(
        report,
    )
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
    except BaseException:
        try:
            cursor.close()
        except BaseException:
            pass
        raise
    cursor.close()
    if rowcount not in (0, 1):
        raise ValueError("insert rowcount must be 0 or 1")
    return PaperAutonomousAllocationProposalDbHistoryHealthInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_autonomous_allocation_proposal_db_history_health_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    health_status: str | None = None,
    latest_history_status: str | None = None,
    limit: int | None = None,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE
    ),
) -> tuple["PaperAutonomousAllocationProposalDbHistoryHealthReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if health_status is not None:
        _require_health_status("health_status", health_status)
    if latest_history_status is not None:
        _require_health_status("latest_history_status", latest_history_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if health_status is not None:
        conditions.append("health_status = %s")
        params.append(health_status)
    if latest_history_status is not None:
        conditions.append("latest_history_status = %s")
        params.append(latest_history_status)

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
    except BaseException:
        try:
            cursor.close()
        except BaseException:
            pass
        raise
    cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(
        paper_autonomous_allocation_proposal_db_history_health_report_from_db_row(
            row,
        )
        for row in rows
    )


def _db_row_from_record(
    record: Any,
) -> PaperAutonomousAllocationProposalDbHistoryHealthDbRow:
    if isinstance(record, PaperAutonomousAllocationProposalDbHistoryHealthDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected DB-history health columns")
    kwargs = dict(zip(_SELECT_COLUMNS, values, strict=True))
    kwargs["reason_code_counts_json"] = _normalize_json_array(
        "reason_code_counts_json",
        kwargs["reason_code_counts_json"],
    )
    kwargs["reason_codes_json"] = _normalize_json_array(
        "reason_codes_json",
        kwargs["reason_codes_json"],
    )
    kwargs["payload_json"] = _normalize_json_object(
        "payload_json",
        kwargs["payload_json"],
    )
    return PaperAutonomousAllocationProposalDbHistoryHealthDbRow(**kwargs)


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str:
        raise ValueError(_TABLE_NAME_ERROR)
    parts = value.split(".")
    if not 1 <= len(parts) <= 2:
        raise ValueError(_TABLE_NAME_ERROR)
    for part in parts:
        if (
            len(part.encode("utf-8")) > _POSTGRES_IDENTIFIER_MAX_LENGTH
            or _IDENTIFIER_PATTERN.fullmatch(part) is None
        ):
            raise ValueError(_TABLE_NAME_ERROR)
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
