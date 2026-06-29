"""DB-API repository for full paper strategy cycle reports."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.paper_strategy_cycle_report_db_row import (
    PaperStrategyCycleReportDbRow,
    paper_strategy_cycle_report_from_db_row,
    paper_strategy_cycle_report_to_db_row,
)


__all__ = (
    "insert_paper_strategy_cycle_report",
    "load_paper_strategy_cycle_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_DEFAULT_TABLE_NAME = "paper_strategy_cycle_reports"
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "scan_market_count",
    "considered_count",
    "snapshot_ready_count",
    "cost_aware_report_count",
    "blocked_counts_json",
    "payload_json",
    "paper_only",
    "report_only",
)


def insert_paper_strategy_cycle_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> PaperStrategyCycleReportDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_strategy_cycle_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            scan_market_count,
            considered_count,
            snapshot_ready_count,
            cost_aware_report_count,
            blocked_counts_json,
            payload_json,
            paper_only,
            report_only
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.scan_market_count,
        row.considered_count,
        row.snapshot_ready_count,
        row.cost_aware_report_count,
        row.blocked_counts_json,
        row.payload_json,
        row.paper_only,
        row.report_only,
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    finally:
        cursor.close()
    return row


def load_paper_strategy_cycle_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple[Any, ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if limit is not None:
        _require_positive_int("limit", limit)

    where_clause = ""
    params: list[Any] = []
    if config_version is not None:
        where_clause = "WHERE config_version = %s"
        params.append(config_version)

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
        cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(paper_strategy_cycle_report_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperStrategyCycleReportDbRow:
    if isinstance(record, PaperStrategyCycleReportDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected strategy cycle report columns")
    return PaperStrategyCycleReportDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        scan_market_count=values[3],
        considered_count=values[4],
        snapshot_ready_count=values[5],
        cost_aware_report_count=values[6],
        blocked_counts_json=_normalize_json_list("blocked_counts_json", values[7]),
        payload_json=_normalize_json_object("payload_json", values[8]),
        paper_only=values[9],
        report_only=values[10],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_list(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    return [list(item) if isinstance(item, tuple) else item for item in value]


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
