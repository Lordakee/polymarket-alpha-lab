"""DB-API repository for paper NAV snapshots."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.paper_nav_snapshot_db_row import (
    PaperNavSnapshotDbRow,
    paper_nav_snapshot_from_db_row,
    paper_nav_snapshot_to_db_row,
)


__all__ = (
    "insert_paper_nav_snapshot",
    "load_paper_nav_snapshots",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_DEFAULT_TABLE_NAME = "paper_nav_snapshots"
_SELECT_COLUMNS = (
    "snapshot_sha256",
    "marked_at",
    "starting_cash",
    "cash_balance",
    "exit_nav",
    "midpoint_nav",
    "total_cost_basis",
    "unrealized_exit_pnl",
    "mark_count",
    "payload_json",
    "paper_only",
)


def insert_paper_nav_snapshot(
    connection: Any,
    snapshot: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> PaperNavSnapshotDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_nav_snapshot_to_db_row(snapshot)
    sql = f"""
        INSERT INTO {table_name} (
            snapshot_sha256,
            marked_at,
            starting_cash,
            cash_balance,
            exit_nav,
            midpoint_nav,
            total_cost_basis,
            unrealized_exit_pnl,
            mark_count,
            payload_json,
            paper_only
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (snapshot_sha256) DO NOTHING
        """
    params = (
        row.snapshot_sha256,
        row.marked_at,
        row.starting_cash,
        row.cash_balance,
        row.exit_nav,
        row.midpoint_nav,
        row.total_cost_basis,
        row.unrealized_exit_pnl,
        row.mark_count,
        row.payload_json,
        row.paper_only,
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    finally:
        cursor.close()
    return row


def load_paper_nav_snapshots(
    connection: Any,
    *,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple[Any, ...]:
    table_name = _validate_table_name(table_name)
    if limit is not None:
        _require_positive_int("limit", limit)

    limit_clause = ""
    params: list[Any] = []
    if limit is not None:
        limit_clause = "LIMIT %s"
        params.append(limit)

    columns = ",\n            ".join(_SELECT_COLUMNS)
    sql = f"""
        SELECT
            {columns}
        FROM {table_name}
        ORDER BY marked_at DESC, snapshot_sha256 DESC
        {limit_clause}
        """
    cursor = connection.cursor()
    try:
        cursor.execute(sql, tuple(params))
        records = cursor.fetchall()
    finally:
        cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(paper_nav_snapshot_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperNavSnapshotDbRow:
    if isinstance(record, PaperNavSnapshotDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected NAV snapshot columns")
    return PaperNavSnapshotDbRow(
        snapshot_sha256=values[0],
        marked_at=values[1],
        starting_cash=values[2],
        cash_balance=values[3],
        exit_nav=values[4],
        midpoint_nav=values[5],
        total_cost_basis=values[6],
        unrealized_exit_pnl=values[7],
        mark_count=values[8],
        payload_json=_normalize_json_object("payload_json", values[9]),
        paper_only=values[10],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError("table_name must be a simple lowercase identifier")
    return value


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
