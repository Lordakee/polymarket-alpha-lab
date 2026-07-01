"""DB-API repository for team diagnostics snapshot reports."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import re
from typing import TYPE_CHECKING, Any, Callable, TypeVar

if TYPE_CHECKING:
    from polymarket_alpha_lab.team_diagnostics_snapshot import (
        TeamDiagnosticsSnapshotReport,
    )


__all__ = (
    "DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOTS_TABLE",
    "TeamDiagnosticsSnapshotInsertResult",
    "insert_team_diagnostics_snapshot_report",
    "insert_team_diagnostics_snapshot_report_with_result",
    "load_team_diagnostics_snapshot_reports",
)


_DB_ROW_MODULE_NAME = "polymarket_alpha_lab.team_diagnostics_snapshot_db_row"
_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"
DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOTS_TABLE = "team_diagnostics_snapshots"
_T = TypeVar("_T")
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_config_version",
    "team_id",
    "market_slug",
    "forecast_id",
    "forecast_row_count",
    "evidence_row_count",
    "outcome_row_count",
    "memory_eligible_reference_count",
    "calibration_status",
    "calibration_settled_count",
    "calibration_group_count",
    "event_template_row_count",
    "event_template_status",
    "source_reliability_row_count",
    "source_reliability_missing_source_evidence_count",
    "evidence_quality_status",
    "evidence_quality_pass_count",
    "evidence_quality_watch_count",
    "evidence_quality_blocked_count",
    "evidence_quality_average_quality_score",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class TeamDiagnosticsSnapshotInsertResult:
    row: Any
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not _db_row_class():
            raise ValueError("row must be a TeamDiagnosticsSnapshotDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_team_diagnostics_snapshot_report(
    connection: Any,
    report: "TeamDiagnosticsSnapshotReport",
    *,
    table_name: str = DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOTS_TABLE,
) -> Any:
    return insert_team_diagnostics_snapshot_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_team_diagnostics_snapshot_report_with_result(
    connection: Any,
    report: "TeamDiagnosticsSnapshotReport",
    *,
    table_name: str = DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOTS_TABLE,
) -> TeamDiagnosticsSnapshotInsertResult:
    table_name = _validate_table_name(table_name)
    row = _report_to_db_row(report)
    columns = ",\n            ".join(_SELECT_COLUMNS)
    placeholders = ", ".join("%s" for _column in _SELECT_COLUMNS)
    sql = f"""
        INSERT INTO {table_name} (
            {columns}
        ) VALUES ({placeholders})
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = tuple(getattr(row, column) for column in _SELECT_COLUMNS)
    cursor = connection.cursor()

    def _execute_insert() -> int:
        cursor.execute(sql, params)
        rowcount = cursor.rowcount
        if rowcount not in (0, 1):
            raise ValueError("insert rowcount must be 0 or 1")
        return rowcount

    rowcount = _with_cursor_cleanup(cursor, _execute_insert)
    return TeamDiagnosticsSnapshotInsertResult(row=row, inserted=rowcount == 1)


def load_team_diagnostics_snapshot_reports(
    connection: Any,
    *,
    team_id: str | None = None,
    market_slug: str | None = None,
    forecast_id: str | None = None,
    config_version: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOTS_TABLE,
) -> tuple["TeamDiagnosticsSnapshotReport", ...]:
    table_name = _validate_table_name(table_name)
    if team_id is not None:
        _require_canonical_string("team_id", team_id)
    if market_slug is not None:
        _require_canonical_string("market_slug", market_slug)
    if forecast_id is not None:
        _require_canonical_string("forecast_id", forecast_id)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if team_id is not None:
        conditions.append("team_id = %s")
        params.append(team_id)
    if market_slug is not None:
        conditions.append("market_slug = %s")
        params.append(market_slug)
    if forecast_id is not None:
        conditions.append("forecast_id = %s")
        params.append(forecast_id)
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
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        {limit_clause}
        """
    cursor = connection.cursor()

    def _fetch_records() -> Any:
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()

    records = _with_cursor_cleanup(cursor, _fetch_records)
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(_report_from_db_row(row) for row in rows)


def _with_cursor_cleanup(cursor: Any, operation: Callable[[], _T]) -> _T:
    operation_succeeded = False
    try:
        result = operation()
        operation_succeeded = True
        return result
    finally:
        if operation_succeeded:
            cursor.close()
        else:
            try:
                cursor.close()
            except BaseException:
                pass


def _db_row_module() -> Any:
    return importlib.import_module(_DB_ROW_MODULE_NAME)


def _db_row_class() -> type[Any]:
    return _db_row_module().TeamDiagnosticsSnapshotDbRow


def _report_to_db_row(report: Any) -> Any:
    return _db_row_module().team_diagnostics_snapshot_report_to_db_row(report)


def _report_from_db_row(row: Any) -> Any:
    return _db_row_module().team_diagnostics_snapshot_report_from_db_row(row)


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
        raise ValueError("DB row must contain selected team diagnostics snapshot columns")
    normalized = {
        column: _normalize_json_array(column, value)
        if column == "reason_codes_json"
        else _normalize_json_object(column, value)
        if column == "payload_json"
        else value
        for column, value in zip(_SELECT_COLUMNS, values, strict=True)
    }
    return row_type(**normalized)


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str:
        raise ValueError(_TABLE_NAME_ERROR)
    parts = value.split(".")
    if len(parts) not in (1, 2):
        raise ValueError(_TABLE_NAME_ERROR)
    for part in parts:
        if len(part.encode("utf-8")) > 63:
            raise ValueError(_TABLE_NAME_ERROR)
        if _IDENTIFIER_PATTERN.fullmatch(part) is None:
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
