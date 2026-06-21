"""DB-API repository for strategy risk audit reports."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditReport,
    _require_canonical_string,
)
from polymarket_alpha_lab.strategy_risk_audit_db_row import (
    PaperStrategyRiskAuditReportDbRow,
    strategy_risk_audit_report_from_db_row,
    strategy_risk_audit_report_to_db_row,
)


__all__ = (
    "DEFAULT_STRATEGY_RISK_AUDIT_REPORTS_TABLE",
    "insert_strategy_risk_audit_report",
    "load_strategy_risk_audit_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"
DEFAULT_STRATEGY_RISK_AUDIT_REPORTS_TABLE = "strategy_risk_audit_reports"
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "status",
    "gate_count",
    "pass_count",
    "fail_count",
    "incomplete_count",
    "gate_results_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_strategy_risk_audit_report(
    connection: Any,
    report: PaperStrategyRiskAuditReport,
    *,
    table_name: str = DEFAULT_STRATEGY_RISK_AUDIT_REPORTS_TABLE,
) -> PaperStrategyRiskAuditReportDbRow:
    table_name = _validate_table_name(table_name)
    row = strategy_risk_audit_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            status,
            gate_count,
            pass_count,
            fail_count,
            incomplete_count,
            gate_results_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.status,
        row.gate_count,
        row.pass_count,
        row.fail_count,
        row.incomplete_count,
        row.gate_results_json,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    finally:
        cursor.close()
    return row


def load_strategy_risk_audit_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_STRATEGY_RISK_AUDIT_REPORTS_TABLE,
) -> tuple[PaperStrategyRiskAuditReport, ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if limit is not None:
        _require_positive_int("limit", limit)

    where_clause = ""
    params: list[Any] = []
    if config_version is not None:
        where_clause = "WHERE config_version = %s"
        params.append(config_version)

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
        cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(strategy_risk_audit_report_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperStrategyRiskAuditReportDbRow:
    if isinstance(record, PaperStrategyRiskAuditReportDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected strategy risk audit columns")
    return PaperStrategyRiskAuditReportDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        status=values[3],
        gate_count=values[4],
        pass_count=values[5],
        fail_count=values[6],
        incomplete_count=values[7],
        gate_results_json=_normalize_json_array("gate_results_json", values[8]),
        payload_json=_normalize_json_object("payload_json", values[9]),
        paper_only=values[10],
        report_only=values[11],
        readonly=values[12],
    )


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
    if not 1 <= len(parts) <= 2:
        raise ValueError(_TABLE_NAME_ERROR)
    for part in parts:
        if len(part.encode("utf-8")) > 63:
            raise ValueError(_TABLE_NAME_ERROR)
        if _IDENTIFIER_PATTERN.fullmatch(part) is None:
            raise ValueError(_TABLE_NAME_ERROR)
    return value


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
