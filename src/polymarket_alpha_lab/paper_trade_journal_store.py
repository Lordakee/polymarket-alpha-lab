"""DB-API repository for paper trade journal records."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.paper_trade_journal_db_row import (
    PaperTradeJournalDbRow,
    paper_trade_record_from_db_row,
    paper_trade_record_to_db_row,
)


__all__ = (
    "insert_paper_trade_record",
    "load_paper_trade_records",
)

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_DEFAULT_TABLE_NAME = "paper_trade_journal_records"
_SELECT_COLUMNS = (
    "record_sha256",
    "packet_id",
    "decision_timestamp_utc",
    "condition_id",
    "token_id",
    "market_slug",
    "outcome_name",
    "order_side",
    "fill_status",
    "fill_filled_size",
    "fill_average_price",
    "account_equity_before_trade",
    "payload_json",
    "paper_only",
)


def insert_paper_trade_record(
    connection: Any,
    record: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> PaperTradeJournalDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_trade_record_to_db_row(record)
    sql = f"""
        INSERT INTO {table_name} (
            record_sha256,
            packet_id,
            decision_timestamp_utc,
            condition_id,
            token_id,
            market_slug,
            outcome_name,
            order_side,
            fill_status,
            fill_filled_size,
            fill_average_price,
            account_equity_before_trade,
            payload_json,
            paper_only
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (record_sha256) DO NOTHING
        """
    params = (
        row.record_sha256,
        row.packet_id,
        row.decision_timestamp_utc,
        row.condition_id,
        row.token_id,
        row.market_slug,
        row.outcome_name,
        row.order_side,
        row.fill_status,
        row.fill_filled_size,
        row.fill_average_price,
        row.account_equity_before_trade,
        row.payload_json,
        row.paper_only,
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    finally:
        cursor.close()
    return row


def load_paper_trade_records(
    connection: Any,
    *,
    condition_id: str | None = None,
    token_id: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple[Any, ...]:
    table_name = _validate_table_name(table_name)
    if condition_id is not None:
        _require_canonical_string("condition_id", condition_id)
    if token_id is not None:
        _require_canonical_string("token_id", token_id)
    if limit is not None:
        _require_positive_int("limit", limit)

    where_parts: list[str] = []
    params: list[Any] = []
    if condition_id is not None:
        where_parts.append("condition_id = %s")
        params.append(condition_id)
    if token_id is not None:
        where_parts.append("token_id = %s")
        params.append(token_id)
    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

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
        ORDER BY decision_timestamp_utc DESC, inserted_at DESC, record_sha256 DESC
        {limit_clause}
        """
    cursor = connection.cursor()
    try:
        cursor.execute(sql, tuple(params))
        records = cursor.fetchall()
    finally:
        cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(paper_trade_record_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperTradeJournalDbRow:
    if isinstance(record, PaperTradeJournalDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected paper trade journal columns")
    return PaperTradeJournalDbRow(
        record_sha256=values[0],
        packet_id=values[1],
        decision_timestamp_utc=values[2],
        condition_id=values[3],
        token_id=values[4],
        market_slug=values[5],
        outcome_name=values[6],
        order_side=values[7],
        fill_status=values[8],
        fill_filled_size=values[9],
        fill_average_price=values[10],
        account_equity_before_trade=values[11],
        payload_json=_normalize_json_object("payload_json", values[12]),
        paper_only=values[13],
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
