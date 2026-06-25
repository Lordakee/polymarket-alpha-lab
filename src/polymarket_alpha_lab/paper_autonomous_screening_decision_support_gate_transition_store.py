"""DB-API repository for paper autonomous screening gate transition reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row import (
    PaperAutonomousScreeningDecisionSupportGateTransitionDbRow,
    paper_autonomous_screening_decision_support_gate_transition_report_from_db_row,
    paper_autonomous_screening_decision_support_gate_transition_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition import (
        PaperAutonomousScreeningDecisionSupportGateTransitionReport,
    )


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_REPORTS_TABLE",
    "PaperAutonomousScreeningDecisionSupportGateTransitionInsertResult",
    "insert_paper_autonomous_screening_decision_support_gate_transition_report",
    "insert_paper_autonomous_screening_decision_support_gate_transition_report_with_result",
    "load_paper_autonomous_screening_decision_support_gate_transition_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_TABLE_NAME_ERROR = "table_name must be a simple lowercase identifier"
_GATE_STATUSES = ("pass", "watch", "blocked")
DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_REPORTS_TABLE = (
    "paper_autonomous_screening_gate_transition_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "gate_report_count",
    "transition_count",
    "first_report_generated_at",
    "latest_report_generated_at",
    "latest_from_gate_status",
    "latest_to_gate_status",
    "latest_introduced_reason_codes_json",
    "latest_cleared_reason_codes_json",
    "latest_persistent_reason_codes_json",
    "status_transition_rows_json",
    "reason_change_rows_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateTransitionInsertResult:
    row: PaperAutonomousScreeningDecisionSupportGateTransitionDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperAutonomousScreeningDecisionSupportGateTransitionDbRow:
            raise ValueError(
                "row must be a "
                "PaperAutonomousScreeningDecisionSupportGateTransitionDbRow",
            )
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_autonomous_screening_decision_support_gate_transition_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_REPORTS_TABLE
    ),
) -> PaperAutonomousScreeningDecisionSupportGateTransitionDbRow:
    return (
        insert_paper_autonomous_screening_decision_support_gate_transition_report_with_result(
            connection,
            report,
            table_name=table_name,
        ).row
    )


def insert_paper_autonomous_screening_decision_support_gate_transition_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_REPORTS_TABLE
    ),
) -> PaperAutonomousScreeningDecisionSupportGateTransitionInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_autonomous_screening_decision_support_gate_transition_report_to_db_row(
        report,
    )
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
    return PaperAutonomousScreeningDecisionSupportGateTransitionInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_autonomous_screening_decision_support_gate_transition_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    latest_from_gate_status: str | None = None,
    latest_to_gate_status: str | None = None,
    limit: int | None = None,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_REPORTS_TABLE
    ),
) -> tuple["PaperAutonomousScreeningDecisionSupportGateTransitionReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if latest_from_gate_status is not None:
        _require_gate_status("latest_from_gate_status", latest_from_gate_status)
    if latest_to_gate_status is not None:
        _require_gate_status("latest_to_gate_status", latest_to_gate_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if latest_from_gate_status is not None:
        conditions.append("latest_from_gate_status = %s")
        params.append(latest_from_gate_status)
    if latest_to_gate_status is not None:
        conditions.append("latest_to_gate_status = %s")
        params.append(latest_to_gate_status)

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
    return tuple(
        paper_autonomous_screening_decision_support_gate_transition_report_from_db_row(
            row,
        )
        for row in rows
    )


def _db_row_from_record(
    record: Any,
) -> PaperAutonomousScreeningDecisionSupportGateTransitionDbRow:
    if isinstance(record, PaperAutonomousScreeningDecisionSupportGateTransitionDbRow):
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
            "DB row must contain selected autonomous screening gate transition "
            "columns",
        )
    kwargs = dict(zip(_SELECT_COLUMNS, values, strict=True))
    for column in (
        "latest_introduced_reason_codes_json",
        "latest_cleared_reason_codes_json",
        "latest_persistent_reason_codes_json",
    ):
        kwargs[column] = _normalize_json_array(column, kwargs[column])
    kwargs["status_transition_rows_json"] = _normalize_optional_json_array(
        "status_transition_rows_json",
        kwargs["status_transition_rows_json"],
    )
    kwargs["reason_change_rows_json"] = _normalize_optional_json_array(
        "reason_change_rows_json",
        kwargs["reason_change_rows_json"],
    )
    kwargs["payload_json"] = _normalize_json_object(
        "payload_json",
        kwargs["payload_json"],
    )
    return PaperAutonomousScreeningDecisionSupportGateTransitionDbRow(**kwargs)


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


def _normalize_optional_json_array(
    field_name: str,
    value: Any,
) -> list[Any] | None:
    if value is None:
        return None
    return _normalize_json_array(field_name, value)


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
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
