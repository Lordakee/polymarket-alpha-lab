"""DB-API repository for paper autonomous proposal risk gate reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_autonomous_proposal import PROPOSAL_STATUSES
from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_db_row import (
    PaperAutonomousProposalRiskGateDbRow,
    paper_autonomous_proposal_risk_gate_report_from_db_row,
    paper_autonomous_proposal_risk_gate_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate import (
        PaperAutonomousProposalRiskGateReport,
    )


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_REPORTS_TABLE",
    "PaperAutonomousProposalRiskGateInsertResult",
    "insert_paper_autonomous_proposal_risk_gate_report",
    "insert_paper_autonomous_proposal_risk_gate_report_with_result",
    "load_paper_autonomous_proposal_risk_gate_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"
DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_REPORTS_TABLE = (
    "paper_autonomous_proposal_risk_gate_reports"
)
_GATE_STATUSES = ("pass", "watch", "blocked")
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "gate_status",
    "recommended_next_step",
    "source_proposal_status",
    "source_proposal_count",
    "source_proposal_total_notional",
    "blocked_reason_codes_json",
    "watch_reason_codes_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)
_LOAD_COLUMNS = (*_SELECT_COLUMNS, "inserted_at")
_JSON_COLUMNS = frozenset(
    (
        "blocked_reason_codes_json",
        "watch_reason_codes_json",
        "reason_codes_json",
        "payload_json",
    ),
)


@dataclass(frozen=True)
class PaperAutonomousProposalRiskGateInsertResult:
    row: PaperAutonomousProposalRiskGateDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperAutonomousProposalRiskGateDbRow:
            raise ValueError("row must be a PaperAutonomousProposalRiskGateDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_autonomous_proposal_risk_gate_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_REPORTS_TABLE,
) -> PaperAutonomousProposalRiskGateDbRow:
    return insert_paper_autonomous_proposal_risk_gate_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_autonomous_proposal_risk_gate_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_REPORTS_TABLE,
) -> PaperAutonomousProposalRiskGateInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_autonomous_proposal_risk_gate_report_to_db_row(report)
    columns = ",\n            ".join(_SELECT_COLUMNS)
    placeholders = ", ".join("%s" for _ in _SELECT_COLUMNS)
    sql = f"""
        INSERT INTO {table_name} (
            {columns}
        ) VALUES ({placeholders})
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = tuple(_db_param(column, getattr(row, column)) for column in _SELECT_COLUMNS)
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
    return PaperAutonomousProposalRiskGateInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_autonomous_proposal_risk_gate_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    gate_status: str | None = None,
    source_proposal_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_REPORTS_TABLE,
) -> tuple["PaperAutonomousProposalRiskGateReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if gate_status is not None:
        _require_gate_status("gate_status", gate_status)
    if source_proposal_status is not None:
        _require_source_proposal_status(
            "source_proposal_status",
            source_proposal_status,
        )
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
    if source_proposal_status is not None:
        conditions.append("source_proposal_status = %s")
        params.append(source_proposal_status)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    limit_clause = ""
    if limit is not None:
        limit_clause = "LIMIT %s"
        params.append(limit)

    columns = ",\n            ".join(_LOAD_COLUMNS)
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
        paper_autonomous_proposal_risk_gate_report_from_db_row(row)
        for row in rows
    )


def _db_row_from_record(record: Any) -> PaperAutonomousProposalRiskGateDbRow:
    if isinstance(record, PaperAutonomousProposalRiskGateDbRow):
        return record
    if isinstance(record, dict):
        columns = _LOAD_COLUMNS if all(column in record for column in _LOAD_COLUMNS) else _SELECT_COLUMNS
        values = tuple(record[column] for column in columns)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        columns = (
            _LOAD_COLUMNS
            if all(column in as_dict for column in _LOAD_COLUMNS)
            else _SELECT_COLUMNS
        )
        values = tuple(as_dict[column] for column in columns)
    else:
        values = tuple(record)
    if len(values) == len(_LOAD_COLUMNS):
        values = values[: len(_SELECT_COLUMNS)]
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError(
            "DB row must contain selected paper autonomous proposal risk gate columns",
        )
    return PaperAutonomousProposalRiskGateDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        gate_status=values[3],
        recommended_next_step=values[4],
        source_proposal_status=values[5],
        source_proposal_count=values[6],
        source_proposal_total_notional=values[7],
        blocked_reason_codes_json=values[8],
        watch_reason_codes_json=values[9],
        reason_codes_json=values[10],
        payload_json=values[11],
        paper_only=values[12],
        report_only=values[13],
        readonly=values[14],
    )


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


def _db_param(column: str, value: Any) -> Any:
    if column in _JSON_COLUMNS:
        return _mutable_json_value(value)
    return value


def _mutable_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _mutable_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_mutable_json_value(item) for item in value]
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_source_proposal_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PROPOSAL_STATUSES:
        raise ValueError(f"{field_name} must be a known proposal status")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
