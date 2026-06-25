"""DB-API load helper for persisted paper broker execution records."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab import paper_broker_db_row
from polymarket_alpha_lab.paper_broker_db_row import PaperBrokerExecutionDbRow


__all__ = (
    "DEFAULT_PAPER_BROKER_EXECUTION_RECORDS_TABLE",
    "load_paper_broker_execution_records",
)


DEFAULT_PAPER_BROKER_EXECUTION_RECORDS_TABLE = "paper_broker_execution_records"
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
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


def load_paper_broker_execution_records(
    connection: Any,
    *,
    execution_status: str | None = None,
    config_version: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_BROKER_EXECUTION_RECORDS_TABLE,
) -> tuple[Any, ...]:
    table_name = _validate_table_name(table_name)
    if execution_status is not None:
        _require_canonical_string("execution_status", execution_status)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if execution_status is not None:
        conditions.append("execution_status = %s")
        params.append(execution_status)
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)

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
    return tuple(paper_broker_db_row.from_db_row(row) for row in rows)


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
        raise ValueError("DB row must contain selected paper broker columns")
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
        raise ValueError("table_name must be a simple lowercase identifier")
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
