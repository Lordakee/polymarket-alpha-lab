"""DB-API repository for paper recommendation risk budget reports."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_recommendation_risk_budget_db_row import (
    PaperRecommendationRiskBudgetDbRow,
    paper_recommendation_risk_budget_report_from_db_row,
    paper_recommendation_risk_budget_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_recommendation_risk_budget import (
        PaperRecommendationRiskBudgetReport,
    )


__all__ = (
    "insert_paper_recommendation_risk_budget_report",
    "load_paper_recommendation_risk_budget_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_DEFAULT_TABLE_NAME = "paper_recommendation_risk_budget_reports"
_STATUSES = ("pass", "watch", "blocked")
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "status",
    "reason_codes",
    "total_suggested_notional",
    "remaining_total_notional",
    "total_notional_utilization",
    "largest_single_recommendation_share",
    "selected_count",
    "blocked_count",
    "nav_notional",
    "max_total_utilization",
    "max_single_recommendation_share",
    "min_remaining_notional",
    "max_selected_count",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_recommendation_risk_budget_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> PaperRecommendationRiskBudgetDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_recommendation_risk_budget_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            status,
            reason_codes,
            total_suggested_notional,
            remaining_total_notional,
            total_notional_utilization,
            largest_single_recommendation_share,
            selected_count,
            blocked_count,
            nav_notional,
            max_total_utilization,
            max_single_recommendation_share,
            min_remaining_notional,
            max_selected_count,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.status,
        row.reason_codes_json,
        row.total_suggested_notional,
        row.remaining_total_notional,
        row.total_notional_utilization,
        row.largest_single_recommendation_share,
        row.selected_count,
        row.blocked_count,
        row.nav_notional,
        row.max_total_utilization,
        row.max_single_recommendation_share,
        row.min_remaining_notional,
        row.max_selected_count,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    except BaseException:
        _close_cursor_after_operation_error(cursor)
        raise
    cursor.close()
    return row


def load_paper_recommendation_risk_budget_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    status: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple["PaperRecommendationRiskBudgetReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if status is not None:
        _require_status("status", status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if status is not None:
        conditions.append("status = %s")
        params.append(status)

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
    except BaseException:
        _close_cursor_after_operation_error(cursor)
        raise
    cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(paper_recommendation_risk_budget_report_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperRecommendationRiskBudgetDbRow:
    if isinstance(record, PaperRecommendationRiskBudgetDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected risk budget columns")
    return PaperRecommendationRiskBudgetDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        status=values[3],
        reason_codes_json=values[4],
        total_suggested_notional=values[5],
        remaining_total_notional=values[6],
        total_notional_utilization=values[7],
        largest_single_recommendation_share=values[8],
        selected_count=values[9],
        blocked_count=values[10],
        nav_notional=values[11],
        max_total_utilization=values[12],
        max_single_recommendation_share=values[13],
        min_remaining_notional=values[14],
        max_selected_count=values[15],
        payload_json=_normalize_json_object("payload", values[16]),
        paper_only=values[17],
        report_only=values[18],
        readonly=values[19],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError("table_name must be a simple lowercase identifier")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _close_cursor_after_operation_error(cursor: Any) -> None:
    try:
        cursor.close()
    except BaseException:
        pass
