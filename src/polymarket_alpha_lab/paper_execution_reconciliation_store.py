"""DB-API repository for paper execution reconciliation reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_execution_reconciliation_db_row import (
    PaperExecutionReconciliationDbRow,
    paper_execution_reconciliation_report_from_db_row,
    paper_execution_reconciliation_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_execution_reconciliation import (
        PaperExecutionReconciliationReport,
    )


__all__ = (
    "DEFAULT_PAPER_EXECUTION_RECONCILIATION_REPORTS_TABLE",
    "PaperExecutionReconciliationInsertResult",
    "insert_paper_execution_reconciliation_report",
    "insert_paper_execution_reconciliation_report_with_result",
    "load_paper_execution_reconciliation_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_TABLE_NAME_ERROR = "table_name must be a simple lowercase identifier"
DEFAULT_PAPER_EXECUTION_RECONCILIATION_REPORTS_TABLE = (
    "paper_execution_reconciliation_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "reconciliation_status",
    "total_positions",
    "filled_pending_count",
    "settled_win_count",
    "settled_loss_count",
    "expired_count",
    "cancelled_count",
    "total_fill_notional",
    "total_cost_basis",
    "total_outcome_value",
    "total_pnl",
    "realized_pnl",
    "unrealized_pnl",
    "position_rows_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperExecutionReconciliationInsertResult:
    row: PaperExecutionReconciliationDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperExecutionReconciliationDbRow:
            raise ValueError("row must be a PaperExecutionReconciliationDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_execution_reconciliation_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_EXECUTION_RECONCILIATION_REPORTS_TABLE,
) -> PaperExecutionReconciliationDbRow:
    return insert_paper_execution_reconciliation_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_execution_reconciliation_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_EXECUTION_RECONCILIATION_REPORTS_TABLE,
) -> PaperExecutionReconciliationInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_execution_reconciliation_report_to_db_row(report)
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
    return PaperExecutionReconciliationInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_execution_reconciliation_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    reconciliation_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_EXECUTION_RECONCILIATION_REPORTS_TABLE,
) -> tuple["PaperExecutionReconciliationReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if reconciliation_status is not None:
        _require_canonical_string("reconciliation_status", reconciliation_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if reconciliation_status is not None:
        conditions.append("reconciliation_status = %s")
        params.append(reconciliation_status)

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
    return tuple(
        paper_execution_reconciliation_report_from_db_row(row)
        for row in rows
    )


def _db_row_from_record(record: Any) -> PaperExecutionReconciliationDbRow:
    if isinstance(record, PaperExecutionReconciliationDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected execution reconciliation columns")
    return PaperExecutionReconciliationDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        reconciliation_status=values[3],
        total_positions=values[4],
        filled_pending_count=values[5],
        settled_win_count=values[6],
        settled_loss_count=values[7],
        expired_count=values[8],
        cancelled_count=values[9],
        total_fill_notional=values[10],
        total_cost_basis=values[11],
        total_outcome_value=values[12],
        total_pnl=values[13],
        realized_pnl=values[14],
        unrealized_pnl=values[15],
        position_rows_json=_normalize_json_array("position_rows_json", values[16]),
        reason_codes_json=_normalize_json_array("reason_codes_json", values[17]),
        payload_json=_normalize_json_object("payload_json", values[18]),
        paper_only=values[19],
        report_only=values[20],
        readonly=values[21],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError(_TABLE_NAME_ERROR)
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
