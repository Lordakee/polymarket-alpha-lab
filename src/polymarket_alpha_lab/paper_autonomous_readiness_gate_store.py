"""DB-API repository for paper autonomous readiness gate reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_autonomous_readiness_gate import (
    ALLOCATION_SOURCE_NAME,
    INVESTMENT_LEDGER_SOURCE_NAME,
    READINESS_STATUSES,
    SCREENING_SOURCE_NAME,
)
from polymarket_alpha_lab.paper_autonomous_readiness_gate_db_row import (
    PaperAutonomousReadinessGateDbRow,
    paper_autonomous_readiness_gate_report_from_db_row,
    paper_autonomous_readiness_gate_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_autonomous_readiness_gate import (
        PaperAutonomousReadinessGateReport,
    )


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE",
    "PaperAutonomousReadinessGateInsertResult",
    "insert_paper_autonomous_readiness_gate_report",
    "insert_paper_autonomous_readiness_gate_report_with_result",
    "load_paper_autonomous_readiness_gate_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_TABLE_NAME_ERROR = "table_name must be a simple lowercase identifier"
DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE = (
    "paper_autonomous_readiness_gate_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "readiness_status",
    "recommended_next_step",
    "source_statuses_json",
    "source_config_versions_json",
    "reason_code_counts_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperAutonomousReadinessGateInsertResult:
    row: PaperAutonomousReadinessGateDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperAutonomousReadinessGateDbRow:
            raise ValueError("row must be a PaperAutonomousReadinessGateDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_autonomous_readiness_gate_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE,
) -> PaperAutonomousReadinessGateDbRow:
    return insert_paper_autonomous_readiness_gate_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_autonomous_readiness_gate_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE,
) -> PaperAutonomousReadinessGateInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_autonomous_readiness_gate_report_to_db_row(report)
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
    return PaperAutonomousReadinessGateInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_autonomous_readiness_gate_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    readiness_status: str | None = None,
    screening_config_version: str | None = None,
    allocation_config_version: str | None = None,
    investment_ledger_config_version: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_REPORTS_TABLE,
) -> tuple["PaperAutonomousReadinessGateReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if readiness_status is not None:
        _require_readiness_status("readiness_status", readiness_status)
    if screening_config_version is not None:
        _require_canonical_string("screening_config_version", screening_config_version)
    if allocation_config_version is not None:
        _require_canonical_string("allocation_config_version", allocation_config_version)
    if investment_ledger_config_version is not None:
        _require_canonical_string(
            "investment_ledger_config_version",
            investment_ledger_config_version,
        )
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if readiness_status is not None:
        conditions.append("readiness_status = %s")
        params.append(readiness_status)
    if screening_config_version is not None:
        conditions.append("source_config_versions_json @> %s")
        params.append([[SCREENING_SOURCE_NAME, screening_config_version]])
    if allocation_config_version is not None:
        conditions.append("source_config_versions_json @> %s")
        params.append([[ALLOCATION_SOURCE_NAME, allocation_config_version]])
    if investment_ledger_config_version is not None:
        conditions.append("source_config_versions_json @> %s")
        params.append(
            [[INVESTMENT_LEDGER_SOURCE_NAME, investment_ledger_config_version]],
        )

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
    return tuple(paper_autonomous_readiness_gate_report_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperAutonomousReadinessGateDbRow:
    if isinstance(record, PaperAutonomousReadinessGateDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected readiness gate columns")
    return PaperAutonomousReadinessGateDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        readiness_status=values[3],
        recommended_next_step=values[4],
        source_statuses_json=_normalize_json_object_array(
            "source_statuses_json",
            values[5],
        ),
        source_config_versions_json=_normalize_json_array(
            "source_config_versions_json",
            values[6],
        ),
        reason_code_counts_json=_normalize_json_object_array(
            "reason_code_counts_json",
            values[7],
        ),
        reason_codes_json=_normalize_json_array("reason_codes_json", values[8]),
        payload_json=_normalize_json_object("payload_json", values[9]),
        paper_only=values[10],
        report_only=values[11],
        readonly=values[12],
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


def _require_readiness_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in READINESS_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
