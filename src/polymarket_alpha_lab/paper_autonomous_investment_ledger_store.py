"""DB-API repository for paper autonomous investment ledger reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_row import (
    PaperAutonomousInvestmentLedgerDbRow,
    paper_autonomous_investment_ledger_report_from_db_row,
    paper_autonomous_investment_ledger_report_to_db_row,
)


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_REPORTS_TABLE",
    "PaperAutonomousInvestmentLedgerInsertResult",
    "insert_paper_autonomous_investment_ledger_report",
    "insert_paper_autonomous_investment_ledger_report_with_result",
    "load_paper_autonomous_investment_ledger_reports",
)


_IDENTIFIER_PATTERN = r"^[a-z][a-z0-9_]*[a-z0-9]$"
_LEDGER_STATUSES = ("pass", "watch", "blocked")
DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_REPORTS_TABLE = (
    "paper_autonomous_investment_ledger_reports"
)
_COLUMN_ATTRIBUTE_PAIRS = (
    ("report_sha256", "report_sha256"),
    ("generated_at", "generated_at"),
    ("config_version", "config_version"),
    ("ledger_status", "ledger_status"),
    ("recommended_next_step", "recommended_next_step"),
    ("source_record_count", "source_record_count"),
    ("submitted_count", "submitted_count"),
    ("held_count", "held_count"),
    ("blocked_count", "blocked_count"),
    ("total_submitted_notional", "total_submitted_notional"),
    ("held_zero_notional_count", "held_zero_notional_count"),
    ("blocked_zero_notional_count", "blocked_zero_notional_count"),
    ("latest_generated_at", "latest_generated_at"),
    ("latest_age_seconds", "latest_age_seconds"),
    ("reason_code_counts", "reason_code_counts_json"),
    ("entries", "entries_json"),
    ("reason_codes", "reason_codes_json"),
    ("payload", "payload_json"),
    ("paper_only", "paper_only"),
    ("report_only", "report_only"),
    ("readonly", "readonly"),
)
_SELECT_COLUMNS = tuple(column for column, _attribute in _COLUMN_ATTRIBUTE_PAIRS)
_ROW_ATTRIBUTES = tuple(attribute for _column, attribute in _COLUMN_ATTRIBUTE_PAIRS)
_JSON_COLUMN_ALIASES = {
    "reason_code_counts": "reason_code_counts_json",
    "entries": "entries_json",
    "reason_codes": "reason_codes_json",
    "payload": "payload_json",
}
_POSITIONAL_ROW_ATTRIBUTES = (
    "report_sha256",
    "generated_at",
    "config_version",
    "ledger_status",
    "recommended_next_step",
    "source_record_count",
    "submitted_count",
    "held_count",
    "blocked_count",
    "total_submitted_notional",
    "held_zero_notional_count",
    "blocked_zero_notional_count",
    "latest_generated_at",
    "latest_age_seconds",
    "reason_code_counts_json",
    "entries_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerInsertResult:
    row: PaperAutonomousInvestmentLedgerDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperAutonomousInvestmentLedgerDbRow:
            raise ValueError("row must be a PaperAutonomousInvestmentLedgerDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_autonomous_investment_ledger_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_REPORTS_TABLE,
) -> PaperAutonomousInvestmentLedgerDbRow:
    return insert_paper_autonomous_investment_ledger_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_autonomous_investment_ledger_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_REPORTS_TABLE,
) -> PaperAutonomousInvestmentLedgerInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_autonomous_investment_ledger_report_to_db_row(report)
    columns = ",\n            ".join(_SELECT_COLUMNS)
    placeholders = ", ".join("%s" for _ in _SELECT_COLUMNS)
    sql = f"""
        INSERT INTO {table_name} (
            {columns}
        ) VALUES ({placeholders})
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = tuple(getattr(row, attribute) for attribute in _ROW_ATTRIBUTES)
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
    return PaperAutonomousInvestmentLedgerInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_autonomous_investment_ledger_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    ledger_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_REPORTS_TABLE,
) -> tuple[Any, ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if ledger_status is not None:
        _require_ledger_status("ledger_status", ledger_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if ledger_status is not None:
        conditions.append("ledger_status = %s")
        params.append(ledger_status)

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
        paper_autonomous_investment_ledger_report_from_db_row(row) for row in rows
    )


def _db_row_from_record(record: Any) -> PaperAutonomousInvestmentLedgerDbRow:
    if isinstance(record, PaperAutonomousInvestmentLedgerDbRow):
        return record
    if isinstance(record, dict):
        kwargs = {
            _JSON_COLUMN_ALIASES.get(column, column): record[column]
            for column in _SELECT_COLUMNS
        }
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        kwargs = {
            _JSON_COLUMN_ALIASES.get(column, column): as_dict[column]
            for column in _SELECT_COLUMNS
        }
    else:
        values = tuple(record)
        if len(values) != len(_POSITIONAL_ROW_ATTRIBUTES):
            raise ValueError("DB row must contain selected investment ledger columns")
        kwargs = dict(zip(_POSITIONAL_ROW_ATTRIBUTES, values, strict=True))
    kwargs["reason_code_counts_json"] = _normalize_json_array(
        "reason_code_counts_json",
        kwargs["reason_code_counts_json"],
    )
    kwargs["entries_json"] = _normalize_json_array(
        "entries_json",
        kwargs["entries_json"],
    )
    kwargs["reason_codes_json"] = _normalize_json_array(
        "reason_codes_json",
        kwargs["reason_codes_json"],
    )
    kwargs["payload_json"] = _normalize_json_object(
        "payload_json",
        kwargs["payload_json"],
    )
    return PaperAutonomousInvestmentLedgerDbRow(**kwargs)


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str or re.fullmatch(_IDENTIFIER_PATTERN, value) is None:
        raise ValueError("table_name must be a simple lowercase identifier")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_ledger_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _LEDGER_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
