"""DB-API repository for paper allocation metrics evaluation reports."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_row import (
    PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow,
    paper_autonomous_allocation_proposal_db_history_metrics_evaluation_from_db_row,
    paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row,
)


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_REPORTS_TABLE",
    "insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report",
    "load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"
DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_REPORTS_TABLE = (
    "paper_autonomous_allocation_proposal_metrics_evaluation_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "evaluation_status",
    "recommended_next_step",
    "source_report_count",
    "latest_report_generated_at",
    "reason_code_counts",
    "reason_codes",
    "diagnostics",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)
_STATUSES = ("pass", "watch", "blocked")


def insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_REPORTS_TABLE
    ),
) -> PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_autonomous_allocation_proposal_db_history_metrics_evaluation_to_db_row(
        report,
    )
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            evaluation_status,
            recommended_next_step,
            source_report_count,
            latest_report_generated_at,
            reason_code_counts,
            reason_codes,
            diagnostics,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.evaluation_status,
        row.recommended_next_step,
        row.source_report_count,
        row.latest_report_generated_at,
        row.reason_code_counts_json,
        list(row.reason_codes),
        row.diagnostics_json,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    except BaseException:
        try:
            cursor.close()
        except Exception:
            pass
        raise
    cursor.close()
    return row


def load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    evaluation_status: str | None = None,
    limit: int | None = None,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_REPORTS_TABLE
    ),
) -> tuple[Any, ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if evaluation_status is not None:
        _require_status("evaluation_status", evaluation_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    where_parts: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        where_parts.append("config_version = %s")
        params.append(config_version)
    if evaluation_status is not None:
        where_parts.append("evaluation_status = %s")
        params.append(evaluation_status)

    where_clause = ""
    if where_parts:
        where_clause = "WHERE " + " AND ".join(where_parts)

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
    except BaseException:
        try:
            cursor.close()
        except Exception:
            pass
        raise
    cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(
        paper_autonomous_allocation_proposal_db_history_metrics_evaluation_from_db_row(
            row,
        )
        for row in rows
    )


def _db_row_from_record(
    record: Any,
) -> PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow:
    if isinstance(record, PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected metrics evaluation columns")
    return PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        evaluation_status=values[3],
        recommended_next_step=values[4],
        source_report_count=values[5],
        latest_report_generated_at=values[6],
        reason_code_counts_json=_normalize_json_object("reason_code_counts", values[7]),
        reason_codes=values[8],
        diagnostics_json=_normalize_json_object("diagnostics", values[9]),
        payload_json=_normalize_json_object("payload", values[10]),
        paper_only=values[11],
        report_only=values[12],
        readonly=values[13],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


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


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


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
