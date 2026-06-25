"""DB-API repository for paper broker execution records."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_broker_db_row import (
    PaperBrokerExecutionDbRow,
    from_db_row,
    to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_broker import PaperBrokerExecutionRecord


__all__ = (
    "DEFAULT_PAPER_BROKER_EXECUTION_RECORDS_TABLE",
    "PaperBrokerExecutionInsertResult",
    "insert_paper_broker_execution_record",
    "insert_paper_broker_execution_record_with_result",
    "load_paper_broker_execution_records",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_TABLE_NAME_ERROR = "table_name must be a simple lowercase identifier"
DEFAULT_PAPER_BROKER_EXECUTION_RECORDS_TABLE = "paper_broker_execution_records"
_SELECT_COLUMNS = (
    "record_sha256",
    "generated_at",
    "config_version",
    "execution_status",
    "recommended_next_step",
    "source_gate_status",
    "source_proposal_count",
    "source_proposal_total_notional",
    "execution_notional",
    "reason_codes",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_ATTR_BY_DB_COLUMN = {
    "reason_codes": "reason_codes_json",
    "payload": "payload_json",
}


@dataclass(frozen=True)
class PaperBrokerExecutionInsertResult:
    row: PaperBrokerExecutionDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperBrokerExecutionDbRow:
            raise ValueError("row must be a PaperBrokerExecutionDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_broker_execution_record(
    connection: Any,
    record: Any,
    *,
    table_name: str = DEFAULT_PAPER_BROKER_EXECUTION_RECORDS_TABLE,
) -> PaperBrokerExecutionDbRow:
    return insert_paper_broker_execution_record_with_result(
        connection,
        record,
        table_name=table_name,
    ).row


def insert_paper_broker_execution_record_with_result(
    connection: Any,
    record: Any,
    *,
    table_name: str = DEFAULT_PAPER_BROKER_EXECUTION_RECORDS_TABLE,
) -> PaperBrokerExecutionInsertResult:
    table_name = _validate_table_name(table_name)
    row = to_db_row(record)
    columns = ",\n            ".join(_SELECT_COLUMNS)
    placeholders = ", ".join("%s" for _ in _SELECT_COLUMNS)
    sql = f"""
        INSERT INTO {table_name} (
            {columns}
        ) VALUES ({placeholders})
        ON CONFLICT (record_sha256) DO NOTHING
        """
    params = tuple(
        getattr(row, _ROW_ATTR_BY_DB_COLUMN.get(column, column))
        for column in _SELECT_COLUMNS
    )
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
    return PaperBrokerExecutionInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_broker_execution_records(
    connection: Any,
    *,
    config_version: str | None = None,
    execution_status: str | None = None,
    source_gate_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_BROKER_EXECUTION_RECORDS_TABLE,
) -> tuple["PaperBrokerExecutionRecord", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if execution_status is not None:
        _require_canonical_string("execution_status", execution_status)
    if source_gate_status is not None:
        _require_canonical_string("source_gate_status", source_gate_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if execution_status is not None:
        conditions.append("execution_status = %s")
        params.append(execution_status)
    if source_gate_status is not None:
        conditions.append("source_gate_status = %s")
        params.append(source_gate_status)

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
        ORDER BY generated_at DESC, inserted_at DESC, record_sha256 DESC
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
    return tuple(from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperBrokerExecutionDbRow:
    if isinstance(record, PaperBrokerExecutionDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected paper broker execution columns")
    return PaperBrokerExecutionDbRow(
        record_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        execution_status=values[3],
        recommended_next_step=values[4],
        source_gate_status=values[5],
        source_proposal_count=values[6],
        source_proposal_total_notional=values[7],
        execution_notional=values[8],
        reason_codes_json=_normalize_json_array("reason_codes", values[9]),
        payload_json=_normalize_json_object("payload", values[10]),
        paper_only=values[11],
        report_only=values[12],
        readonly=values[13],
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
