"""DB-API repository for local observability trends reports."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.local_observability_trends import (
    LocalObservabilityTrendsReport,
)
from polymarket_alpha_lab.local_observability_trends_db_row import (
    LocalObservabilityTrendsDbRow,
    local_observability_trends_report_from_db_row,
    local_observability_trends_report_to_db_row,
)


__all__ = (
    "DEFAULT_LOCAL_OBSERVABILITY_TRENDS_TABLE",
    "insert_local_observability_trends_report",
    "load_local_observability_trends_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"
DEFAULT_LOCAL_OBSERVABILITY_TRENDS_TABLE = "local_observability_trends_reports"
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "strategy_evidence_snapshot_count",
    "strategy_evidence_latest_status",
    "outcome_freshness_status",
    "outcome_report_count",
    "nav_risk_status",
    "nav_risk_report_count",
    "paper_trade_cost_status",
    "paper_trade_cost_report_count",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_local_observability_trends_report(
    connection: Any,
    report: LocalObservabilityTrendsReport,
    *,
    table_name: str = DEFAULT_LOCAL_OBSERVABILITY_TRENDS_TABLE,
) -> LocalObservabilityTrendsDbRow:
    table_name = _validate_table_name(table_name)
    row = local_observability_trends_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            strategy_evidence_snapshot_count,
            strategy_evidence_latest_status,
            outcome_freshness_status,
            outcome_report_count,
            nav_risk_status,
            nav_risk_report_count,
            paper_trade_cost_status,
            paper_trade_cost_report_count,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.strategy_evidence_snapshot_count,
        row.strategy_evidence_latest_status,
        row.outcome_freshness_status,
        row.outcome_report_count,
        row.nav_risk_status,
        row.nav_risk_report_count,
        row.paper_trade_cost_status,
        row.paper_trade_cost_report_count,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    finally:
        cursor.close()
    return row


def load_local_observability_trends_reports(
    connection: Any,
    *,
    limit: int | None = None,
    table_name: str = DEFAULT_LOCAL_OBSERVABILITY_TRENDS_TABLE,
) -> tuple[LocalObservabilityTrendsReport, ...]:
    table_name = _validate_table_name(table_name)
    if limit is not None:
        _require_positive_int("limit", limit)

    params: list[Any] = []
    limit_clause = ""
    if limit is not None:
        limit_clause = "LIMIT %s"
        params.append(limit)

    columns = ",\n            ".join(_SELECT_COLUMNS)
    sql = f"""
        SELECT
            {columns}
        FROM {table_name}
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
    return tuple(local_observability_trends_report_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> LocalObservabilityTrendsDbRow:
    if isinstance(record, LocalObservabilityTrendsDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected local observability trends columns")
    return LocalObservabilityTrendsDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        strategy_evidence_snapshot_count=values[3],
        strategy_evidence_latest_status=values[4],
        outcome_freshness_status=values[5],
        outcome_report_count=values[6],
        nav_risk_status=values[7],
        nav_risk_report_count=values[8],
        paper_trade_cost_status=values[9],
        paper_trade_cost_report_count=values[10],
        payload_json=_normalize_json_object("payload_json", values[11]),
        paper_only=values[12],
        report_only=values[13],
        readonly=values[14],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str:
        raise ValueError(_TABLE_NAME_ERROR)
    parts = value.split(".")
    if not 1 <= len(parts) <= 2:
        raise ValueError(_TABLE_NAME_ERROR)
    for part in parts:
        if len(part.encode("utf-8")) > 63:
            raise ValueError(_TABLE_NAME_ERROR)
        if _IDENTIFIER_PATTERN.fullmatch(part) is None:
            raise ValueError(_TABLE_NAME_ERROR)
    return value


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
