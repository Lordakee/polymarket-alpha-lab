"""DB-API repository for outcome tracking reports."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.outcome_tracking_db_row import (
    OutcomeTrackingReportDbRow,
    outcome_tracking_report_from_db_row,
    outcome_tracking_report_to_db_row,
)


__all__ = (
    "insert_outcome_tracking_report",
    "load_outcome_tracking_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_DEFAULT_TABLE_NAME = "outcome_tracking_reports"
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "total_markets_checked",
    "resolved_count",
    "pending_count",
    "observation_count",
    "forecast_evidence_status",
    "payload",
    "paper_only",
)


def insert_outcome_tracking_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> OutcomeTrackingReportDbRow:
    table_name = _validate_table_name(table_name)
    row = outcome_tracking_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            total_markets_checked,
            resolved_count,
            pending_count,
            observation_count,
            forecast_evidence_status,
            payload,
            paper_only
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.total_markets_checked,
        row.resolved_count,
        row.pending_count,
        row.observation_count,
        row.forecast_evidence_status,
        row.payload_json,
        row.paper_only,
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    except BaseException:
        try:
            cursor.close()
        except Exception:
            pass
        raise
    cursor.close()
    return row


def load_outcome_tracking_reports(
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
        ORDER BY generated_at DESC, report_sha256 DESC
        {limit_clause}
        """
    cursor = connection.cursor()
    try:
        cursor.execute(sql, tuple(params))
        records = cursor.fetchall()
    except BaseException:
        try:
            cursor.close()
        except Exception:
            pass
        raise
    cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(outcome_tracking_report_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> OutcomeTrackingReportDbRow:
    if isinstance(record, OutcomeTrackingReportDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected outcome tracking columns")
    return OutcomeTrackingReportDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        total_markets_checked=values[3],
        resolved_count=values[4],
        pending_count=values[5],
        observation_count=values[6],
        forecast_evidence_status=values[7],
        payload_json=_normalize_json_object("payload", values[8]),
        paper_only=values[9],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


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
