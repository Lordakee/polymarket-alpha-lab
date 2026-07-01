"""DB-API repository for paper trade attribution reports."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.paper_trade_attribution_db_row import (
    PaperTradeAttributionReportDbRow,
    paper_trade_attribution_report_from_db_row,
    paper_trade_attribution_report_to_db_row,
)


__all__ = (
    "DEFAULT_PAPER_TRADE_ATTRIBUTION_REPORTS_TABLE",
    "insert_paper_trade_attribution_report",
    "load_paper_trade_attribution_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"
DEFAULT_PAPER_TRADE_ATTRIBUTION_REPORTS_TABLE = "paper_trade_attribution_reports"
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "trade_count",
    "row_count",
    "market_count",
    "filled_count",
    "complete_fill_count",
    "partial_fill_count",
    "resolved_count",
    "pending_count",
    "realized_win_count",
    "realized_loss_count",
    "total_requested_size",
    "total_filled_size",
    "total_unfilled_size",
    "total_notional",
    "first_trade_decision_at",
    "latest_trade_decision_at",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_trade_attribution_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_TRADE_ATTRIBUTION_REPORTS_TABLE,
) -> PaperTradeAttributionReportDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_trade_attribution_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            trade_count,
            row_count,
            market_count,
            filled_count,
            complete_fill_count,
            partial_fill_count,
            resolved_count,
            pending_count,
            realized_win_count,
            realized_loss_count,
            total_requested_size,
            total_filled_size,
            total_unfilled_size,
            total_notional,
            first_trade_decision_at,
            latest_trade_decision_at,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.trade_count,
        row.row_count,
        row.market_count,
        row.filled_count,
        row.complete_fill_count,
        row.partial_fill_count,
        row.resolved_count,
        row.pending_count,
        row.realized_win_count,
        row.realized_loss_count,
        row.total_requested_size,
        row.total_filled_size,
        row.total_unfilled_size,
        row.total_notional,
        row.first_trade_decision_at,
        row.latest_trade_decision_at,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
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


def load_paper_trade_attribution_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_TRADE_ATTRIBUTION_REPORTS_TABLE,
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
    except BaseException:
        try:
            cursor.close()
        except Exception:
            pass
        raise
    cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(paper_trade_attribution_report_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperTradeAttributionReportDbRow:
    if isinstance(record, PaperTradeAttributionReportDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected paper trade attribution columns")
    return PaperTradeAttributionReportDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        trade_count=values[3],
        row_count=values[4],
        market_count=values[5],
        filled_count=values[6],
        complete_fill_count=values[7],
        partial_fill_count=values[8],
        resolved_count=values[9],
        pending_count=values[10],
        realized_win_count=values[11],
        realized_loss_count=values[12],
        total_requested_size=values[13],
        total_filled_size=values[14],
        total_unfilled_size=values[15],
        total_notional=values[16],
        first_trade_decision_at=values[17],
        latest_trade_decision_at=values[18],
        payload_json=_normalize_json_object("payload_json", values[19]),
        paper_only=values[20],
        report_only=values[21],
        readonly=values[22],
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
