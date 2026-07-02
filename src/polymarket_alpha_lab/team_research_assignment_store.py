"""DB-API repository for team research assignment reports."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import re
from typing import TYPE_CHECKING, Any, Callable, TypeVar

if TYPE_CHECKING:
    from polymarket_alpha_lab.team_research_assignment import (
        TeamResearchAssignmentReport,
    )


__all__ = (
    "DEFAULT_TEAM_RESEARCH_ASSIGNMENT_REPORTS_TABLE",
    "TeamResearchAssignmentInsertResult",
    "insert_team_research_assignment_report",
    "insert_team_research_assignment_report_with_result",
    "load_team_research_assignment_reports",
)


_DB_ROW_MODULE_NAME = "polymarket_alpha_lab.team_research_assignment_db_row"
_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = (
    "table_name must be a lowercase identifier with optional schema prefix"
)
_REDACTED_DB_OPERATION_MESSAGE = (
    "team research assignment database operation failed for <redacted>"
)
DEFAULT_TEAM_RESEARCH_ASSIGNMENT_REPORTS_TABLE = "team_research_assignment_reports"
_LOAD_ASSIGNMENT_STATUSES = frozenset(("ready", "watch", "blocked"))
_SENSITIVE_DB_ERROR_MARKERS = (
    "account",
    "api_key",
    "api-secret",
    "api_secret",
    "auth",
    "credential",
    "hash",
    "market question",
    "market slug",
    "market_question",
    "market_slug",
    "order",
    "payload",
    "payload_json",
    "postgres://",
    "postgresql://",
    "private-key",
    "private_key",
    "question",
    "report_sha256",
    "secret",
    "sha256",
    "trade",
    "wallet",
)
_T = TypeVar("_T")
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_queue_config_version",
    "source_route_config_version",
    "source_memory_config_version",
    "assignment_status",
    "assignment_count",
    "assigned_count",
    "watch_count",
    "blocked_count",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class TeamResearchAssignmentInsertResult:
    row: Any
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not _db_row_class():
            raise ValueError("row must be a TeamResearchAssignmentDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_team_research_assignment_report(
    connection: Any,
    report: "TeamResearchAssignmentReport",
    *,
    table_name: str = DEFAULT_TEAM_RESEARCH_ASSIGNMENT_REPORTS_TABLE,
) -> Any:
    return insert_team_research_assignment_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_team_research_assignment_report_with_result(
    connection: Any,
    report: "TeamResearchAssignmentReport",
    *,
    table_name: str = DEFAULT_TEAM_RESEARCH_ASSIGNMENT_REPORTS_TABLE,
) -> TeamResearchAssignmentInsertResult:
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

    rowcount = _with_cursor_cleanup(
        cursor,
        _execute_insert,
        table_name=table_name,
    )
    return TeamResearchAssignmentInsertResult(row=row, inserted=rowcount == 1)


def load_team_research_assignment_reports(
    connection: Any,
    *,
    assignment_status: str | None = None,
    config_version: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_TEAM_RESEARCH_ASSIGNMENT_REPORTS_TABLE,
) -> tuple["TeamResearchAssignmentReport", ...]:
    table_name = _validate_table_name(table_name)
    if assignment_status is not None:
        _require_load_assignment_status(assignment_status)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if assignment_status is not None:
        conditions.append("assignment_status = %s")
        params.append(assignment_status)
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

    records = _with_cursor_cleanup(
        cursor,
        _fetch_records,
        table_name=table_name,
    )
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(_report_from_db_row(row) for row in rows)


def _with_cursor_cleanup(
    cursor: Any,
    operation: Callable[[], _T],
    *,
    table_name: str,
) -> _T:
    try:
        result = operation()
    except BaseException as exc:
        try:
            cursor.close()
        except BaseException:
            pass
        if isinstance(exc, Exception):
            _raise_redacted_db_operation_error(exc, table_name=table_name)
        raise

    try:
        cursor.close()
    except Exception as exc:
        _raise_redacted_db_operation_error(exc, table_name=table_name)
    return result


def _raise_redacted_db_operation_error(exc: Exception, *, table_name: str) -> None:
    message = _redact_db_operation_error(str(exc), table_name=table_name)
    if not message.strip():
        message = exc.__class__.__name__
    try:
        redacted_exc = type(exc)(message)
    except Exception:
        redacted_exc = RuntimeError(message)
    raise redacted_exc from None


def _redact_db_operation_error(value: str, *, table_name: str) -> str:
    lowered = value.lower()
    if table_name and table_name.lower() in lowered:
        return _REDACTED_DB_OPERATION_MESSAGE
    if any(marker in lowered for marker in _SENSITIVE_DB_ERROR_MARKERS):
        return _REDACTED_DB_OPERATION_MESSAGE
    return value


def _db_row_module() -> Any:
    return importlib.import_module(_DB_ROW_MODULE_NAME)


def _db_row_class() -> type[Any]:
    return _db_row_module().TeamResearchAssignmentDbRow


def _report_to_db_row(report: Any) -> Any:
    return _db_row_module().team_research_assignment_report_to_db_row(report)


def _report_from_db_row(row: Any) -> Any:
    return _db_row_module().team_research_assignment_report_from_db_row(row)


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
        raise ValueError(
            "DB row must contain selected team research assignment columns",
        )
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


def _require_load_assignment_status(value: object) -> None:
    _require_canonical_string("assignment_status", value)
    if value not in _LOAD_ASSIGNMENT_STATUSES:
        allowed = ", ".join(sorted(_LOAD_ASSIGNMENT_STATUSES))
        raise ValueError(f"assignment_status must be one of {allowed}")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
