"""DB-API repository for autonomous market scorer reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.autonomous_market_scorer_db_row import (
    AutonomousMarketScorerDbRow,
    autonomous_market_scorer_report_from_db_row,
    autonomous_market_scorer_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.autonomous_market_scorer import (
        AutonomousMarketScorerReport,
    )


__all__ = (
    "DEFAULT_AUTONOMOUS_MARKET_SCORER_REPORTS_TABLE",
    "SELECT_COLUMNS",
    "AutonomousMarketScorerInsertResult",
    "insert_autonomous_market_scorer_report",
    "insert_autonomous_market_scorer_report_with_result",
    "load_autonomous_market_scorer_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
DEFAULT_AUTONOMOUS_MARKET_SCORER_REPORTS_TABLE = (
    "autonomous_market_scorer_reports"
)
_GATE_STATUSES = ("pass", "watch", "blocked")
SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "gate_status",
    "markets_scored",
    "markets_skipped",
    "markets_blocked",
    "top_total_score",
    "average_total_score",
    "total_recommended_notional",
    "paper_only",
    "report_only",
    "readonly",
    "reason_codes",
    "score_rows",
    "payload",
)


@dataclass(frozen=True)
class AutonomousMarketScorerInsertResult:
    row: AutonomousMarketScorerDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not AutonomousMarketScorerDbRow:
            raise ValueError("row must be an AutonomousMarketScorerDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_autonomous_market_scorer_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_AUTONOMOUS_MARKET_SCORER_REPORTS_TABLE,
) -> AutonomousMarketScorerDbRow:
    return insert_autonomous_market_scorer_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_autonomous_market_scorer_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_AUTONOMOUS_MARKET_SCORER_REPORTS_TABLE,
) -> AutonomousMarketScorerInsertResult:
    table_name = _validate_table_name(table_name)
    row = autonomous_market_scorer_report_to_db_row(report)
    columns = ",\n            ".join(SELECT_COLUMNS)
    placeholders = ", ".join("%s" for _ in SELECT_COLUMNS)
    sql = f"""
        INSERT INTO {table_name} (
            {columns}
        ) VALUES ({placeholders})
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = tuple(_param_for_column(row, column) for column in SELECT_COLUMNS)
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        rowcount = cursor.rowcount
    except BaseException:
        _close_cursor_after_operation_error(cursor)
        raise
    cursor.close()
    if rowcount not in (0, 1):
        raise ValueError("insert rowcount must be 0 or 1; rowcount must be 0 or 1")
    return AutonomousMarketScorerInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_autonomous_market_scorer_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    gate_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_AUTONOMOUS_MARKET_SCORER_REPORTS_TABLE,
) -> tuple["AutonomousMarketScorerReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if gate_status is not None:
        _require_gate_status("gate_status", gate_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if gate_status is not None:
        conditions.append("gate_status = %s")
        params.append(gate_status)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    limit_clause = ""
    if limit is not None:
        limit_clause = "LIMIT %s"
        params.append(limit)

    columns = ",\n            ".join(SELECT_COLUMNS)
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
        _close_cursor_after_operation_error(cursor)
        raise
    cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(autonomous_market_scorer_report_from_db_row(row) for row in rows)


def _param_for_column(row: AutonomousMarketScorerDbRow, column: str) -> Any:
    if column == "reason_codes":
        return row.reason_codes_json
    if column == "score_rows":
        return row.score_rows_json
    if column == "payload":
        return row.payload_json
    return getattr(row, column)


def _close_cursor_after_operation_error(cursor: Any) -> None:
    try:
        cursor.close()
    except BaseException:
        pass


def _db_row_from_record(record: Any) -> AutonomousMarketScorerDbRow:
    if isinstance(record, AutonomousMarketScorerDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(SELECT_COLUMNS):
        raise ValueError("DB row must contain selected scorer columns")
    return AutonomousMarketScorerDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        gate_status=values[3],
        markets_scored=values[4],
        markets_skipped=values[5],
        markets_blocked=values[6],
        top_total_score=values[7],
        average_total_score=values[8],
        total_recommended_notional=values[9],
        paper_only=values[10],
        report_only=values[11],
        readonly=values[12],
        reason_codes_json=_normalize_json_array("reason_codes", values[13]),
        score_rows_json=_normalize_json_object_array("score_rows", values[14]),
        payload_json=_normalize_json_object("payload", values[15]),
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


def _normalize_json_object_array(field_name: str, value: Any) -> list[dict[str, Any]]:
    normalized = _normalize_json_array(field_name, value)
    for item in normalized:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
    return normalized


def _validate_table_name(value: str) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError("table_name must be a simple lowercase identifier")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
