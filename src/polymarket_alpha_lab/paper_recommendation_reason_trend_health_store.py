"""DB-API repository for paper recommendation reason trend health reports."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_recommendation_reason_trend_health_db_row import (
    PaperRecommendationReasonTrendHealthDbRow,
    paper_recommendation_reason_trend_health_report_from_db_row,
    paper_recommendation_reason_trend_health_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_recommendation_reason_trend_health import (
        PaperRecommendationReasonTrendHealthReport,
    )


__all__ = (
    "insert_paper_recommendation_reason_trend_health_report",
    "load_paper_recommendation_reason_trend_health_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_DEFAULT_TABLE_NAME = "paper_recommendation_reason_trend_health_reports"
_HEALTH_STATUSES = ("pass", "watch", "blocked")
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "health_status",
    "source_report_count",
    "reason_code_count",
    "blocked_status_count",
    "blocked_status_share",
    "reject_status_count",
    "reject_status_share",
    "new_reason_code_count",
    "transition_count",
    "persistent_reason_codes",
    "reason_codes",
    "max_blocked_status_share",
    "max_reject_status_share",
    "max_new_reason_code_count",
    "max_transition_count",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_recommendation_reason_trend_health_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> PaperRecommendationReasonTrendHealthDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_recommendation_reason_trend_health_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            health_status,
            source_report_count,
            reason_code_count,
            blocked_status_count,
            blocked_status_share,
            reject_status_count,
            reject_status_share,
            new_reason_code_count,
            transition_count,
            persistent_reason_codes,
            reason_codes,
            max_blocked_status_share,
            max_reject_status_share,
            max_new_reason_code_count,
            max_transition_count,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.health_status,
        row.source_report_count,
        row.reason_code_count,
        row.blocked_status_count,
        row.blocked_status_share,
        row.reject_status_count,
        row.reject_status_share,
        row.new_reason_code_count,
        row.transition_count,
        row.persistent_reason_codes_json,
        row.reason_codes_json,
        row.max_blocked_status_share,
        row.max_reject_status_share,
        row.max_new_reason_code_count,
        row.max_transition_count,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    finally:
        try:
            cursor.close()
        except Exception:
            pass
    return row


def load_paper_recommendation_reason_trend_health_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    health_status: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple["PaperRecommendationReasonTrendHealthReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if health_status is not None:
        _require_health_status("health_status", health_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if health_status is not None:
        conditions.append("health_status = %s")
        params.append(health_status)

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
        paper_recommendation_reason_trend_health_report_from_db_row(row)
        for row in rows
    )


def _db_row_from_record(record: Any) -> PaperRecommendationReasonTrendHealthDbRow:
    if isinstance(record, PaperRecommendationReasonTrendHealthDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected reason trend health columns")
    return PaperRecommendationReasonTrendHealthDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        health_status=values[3],
        source_report_count=values[4],
        reason_code_count=values[5],
        blocked_status_count=values[6],
        blocked_status_share=values[7],
        reject_status_count=values[8],
        reject_status_share=values[9],
        new_reason_code_count=values[10],
        transition_count=values[11],
        persistent_reason_codes_json=_normalize_json_array(
            "persistent_reason_codes",
            values[12],
        ),
        reason_codes_json=_normalize_json_array("reason_codes", values[13]),
        max_blocked_status_share=values[14],
        max_reject_status_share=values[15],
        max_new_reason_code_count=values[16],
        max_transition_count=values[17],
        payload_json=_normalize_json_object("payload", values[18]),
        paper_only=values[19],
        report_only=values[20],
        readonly=values[21],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError("table_name must be a simple lowercase identifier")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
