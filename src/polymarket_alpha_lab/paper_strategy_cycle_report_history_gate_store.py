"""DB-API repository for paper strategy cycle history gate reports."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_strategy_cycle_report_history_gate import (
        PaperStrategyCycleReportHistoryGateReport,
    )


__all__ = (
    "DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_REPORTS_TABLE",
    "PaperStrategyCycleReportHistoryGateInsertResult",
    "insert_paper_strategy_cycle_report_history_gate_report",
    "insert_paper_strategy_cycle_report_history_gate_report_with_result",
    "load_paper_strategy_cycle_report_history_gate_reports",
)


_DB_ROW_MODULE_NAME = (
    "polymarket_alpha_lab.paper_strategy_cycle_report_history_gate_db_row"
)
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_TABLE_NAME_ERROR = "table_name must be a simple lowercase identifier"
_GATE_STATUSES = frozenset(("pass", "watch", "blocked"))
DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_REPORTS_TABLE = (
    "paper_strategy_cycle_report_history_gate_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_config_version",
    "source_generated_at",
    "gate_status",
    "recommended_next_step",
    "source_history_status",
    "source_report_count",
    "latest_source_generated_at",
    "latest_source_age_seconds",
    "latest_snapshot_ready_share",
    "blocked_market_share",
    "latest_snapshot_ready_count",
    "latest_considered_count",
    "total_blocked_market_count",
    "reason_code_counts_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryGateInsertResult:
    row: Any
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not _db_row_class():
            raise ValueError(
                "row must be a PaperStrategyCycleReportHistoryGateDbRow",
            )
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_strategy_cycle_report_history_gate_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_REPORTS_TABLE,
) -> Any:
    return insert_paper_strategy_cycle_report_history_gate_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_strategy_cycle_report_history_gate_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_REPORTS_TABLE,
) -> PaperStrategyCycleReportHistoryGateInsertResult:
    table_name = _validate_table_name(table_name)
    row = _report_to_db_row(report)
    columns = ",\n            ".join(_SELECT_COLUMNS)
    placeholders = ", ".join("%s" for _ in _SELECT_COLUMNS)
    sql = f"""
        INSERT INTO {table_name} (
            {columns}
        ) VALUES ({placeholders})
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = tuple(getattr(row, column) for column in _SELECT_COLUMNS)
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
    return PaperStrategyCycleReportHistoryGateInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_strategy_cycle_report_history_gate_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    gate_status: str | None = None,
    source_config_version: str | None = None,
    source_history_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_REPORTS_TABLE,
) -> tuple["PaperStrategyCycleReportHistoryGateReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if gate_status is not None:
        _require_gate_status("gate_status", gate_status)
    if source_config_version is not None:
        _require_canonical_string("source_config_version", source_config_version)
    if source_history_status is not None:
        _require_gate_status("source_history_status", source_history_status)
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
    if source_config_version is not None:
        conditions.append("source_config_version = %s")
        params.append(source_config_version)
    if source_history_status is not None:
        conditions.append("source_history_status = %s")
        params.append(source_history_status)

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
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
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
    return tuple(_report_from_db_row(row) for row in rows)


def _db_row_module() -> Any:
    return importlib.import_module(_DB_ROW_MODULE_NAME)


def _db_row_class() -> type[Any]:
    return _db_row_module().PaperStrategyCycleReportHistoryGateDbRow


def _report_to_db_row(report: Any) -> Any:
    return _db_row_module().paper_strategy_cycle_report_history_gate_report_to_db_row(
        report,
    )


def _report_from_db_row(row: Any) -> Any:
    return _db_row_module().paper_strategy_cycle_report_history_gate_report_from_db_row(
        row,
    )


def _db_row_from_record(record: Any) -> Any:
    row_type = _db_row_class()
    if isinstance(record, row_type):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected history gate columns")
    return row_type(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        source_config_version=values[3],
        source_generated_at=values[4],
        gate_status=values[5],
        recommended_next_step=values[6],
        source_history_status=values[7],
        source_report_count=values[8],
        latest_source_generated_at=values[9],
        latest_source_age_seconds=values[10],
        latest_snapshot_ready_share=values[11],
        blocked_market_share=values[12],
        latest_snapshot_ready_count=values[13],
        latest_considered_count=values[14],
        total_blocked_market_count=values[15],
        reason_code_counts_json=_normalize_json_object_array(
            "reason_code_counts_json",
            values[16],
        ),
        reason_codes_json=_normalize_json_array("reason_codes_json", values[17]),
        payload_json=_normalize_json_object("payload_json", values[18]),
        paper_only=values[19],
        report_only=values[20],
        readonly=values[21],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_object_array(field_name: str, value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized = list(value)
    for item in normalized:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
    return [dict(item) for item in normalized]


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


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
