"""DB-API repository for paper trade cost audit reports."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.paper_trade_cost_audit_db_row import (
    PaperTradeCostAuditReportDbRow,
    paper_trade_cost_audit_report_from_db_row,
    paper_trade_cost_audit_report_to_db_row,
)


__all__ = (
    "DEFAULT_PAPER_TRADE_COST_AUDIT_REPORTS_TABLE",
    "insert_paper_trade_cost_audit_report",
    "load_paper_trade_cost_audit_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"
DEFAULT_PAPER_TRADE_COST_AUDIT_REPORTS_TABLE = "paper_trade_cost_audit_reports"
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "trade_count",
    "total_filled_size",
    "total_requested_size",
    "fill_rate",
    "mean_theoretical_edge",
    "mean_cost_adjusted_edge",
    "mean_edge_cost_drag",
    "total_edge_cost_drag",
    "mean_research_slippage",
    "mean_fill_slippage",
    "partial_fill_count",
    "negative_cost_adjusted_edge_count",
    "largest_single_trade_cost_drag",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_trade_cost_audit_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_TRADE_COST_AUDIT_REPORTS_TABLE,
) -> PaperTradeCostAuditReportDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_trade_cost_audit_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            trade_count,
            total_filled_size,
            total_requested_size,
            fill_rate,
            mean_theoretical_edge,
            mean_cost_adjusted_edge,
            mean_edge_cost_drag,
            total_edge_cost_drag,
            mean_research_slippage,
            mean_fill_slippage,
            partial_fill_count,
            negative_cost_adjusted_edge_count,
            largest_single_trade_cost_drag,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.trade_count,
        row.total_filled_size,
        row.total_requested_size,
        row.fill_rate,
        row.mean_theoretical_edge,
        row.mean_cost_adjusted_edge,
        row.mean_edge_cost_drag,
        row.total_edge_cost_drag,
        row.mean_research_slippage,
        row.mean_fill_slippage,
        row.partial_fill_count,
        row.negative_cost_adjusted_edge_count,
        row.largest_single_trade_cost_drag,
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


def load_paper_trade_cost_audit_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_TRADE_COST_AUDIT_REPORTS_TABLE,
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
    return tuple(paper_trade_cost_audit_report_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperTradeCostAuditReportDbRow:
    if isinstance(record, PaperTradeCostAuditReportDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected paper trade cost audit columns")
    return PaperTradeCostAuditReportDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        trade_count=values[3],
        total_filled_size=values[4],
        total_requested_size=values[5],
        fill_rate=values[6],
        mean_theoretical_edge=values[7],
        mean_cost_adjusted_edge=values[8],
        mean_edge_cost_drag=values[9],
        total_edge_cost_drag=values[10],
        mean_research_slippage=values[11],
        mean_fill_slippage=values[12],
        partial_fill_count=values[13],
        negative_cost_adjusted_edge_count=values[14],
        largest_single_trade_cost_drag=values[15],
        payload_json=_normalize_json_object("payload_json", values[16]),
        paper_only=values[17],
        report_only=values[18],
        readonly=values[19],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str:
        raise ValueError(_TABLE_NAME_ERROR)
    parts = value.split(".")
    if len(parts) not in (1, 2):
        raise ValueError(_TABLE_NAME_ERROR)
    if any(_IDENTIFIER_PATTERN.fullmatch(part) is None for part in parts):
        raise ValueError(_TABLE_NAME_ERROR)
    if any(len(part.encode("utf-8")) > 63 for part in parts):
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
