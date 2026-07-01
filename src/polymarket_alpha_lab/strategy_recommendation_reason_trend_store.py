"""DB-API repository for strategy recommendation reason trend reports."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.strategy_recommendation_reason_trend_db_row import (
    PaperStrategyRecommendationReasonTrendDbRow,
    strategy_recommendation_reason_trend_report_from_db_row,
    strategy_recommendation_reason_trend_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.strategy_recommendation_reason_trend import (
        PaperStrategyRecommendationReasonTrendReport,
    )


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_REASON_TREND_TABLE",
    "insert_strategy_recommendation_reason_trend_report",
    "load_strategy_recommendation_reason_trend_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
DEFAULT_STRATEGY_RECOMMENDATION_REASON_TREND_TABLE = (
    "strategy_recommendation_reason_trend_reports"
)
_STATUSES = ("stable", "watch", "blocked")
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "status",
    "source_report_count",
    "first_generated_at",
    "latest_generated_at",
    "latest_primary_reason_code_counts",
    "total_primary_reason_code_counts",
    "top_new_reason_codes",
    "persistent_reason_codes",
    "latest_reason_code_count",
    "latest_no_reason_code_count",
    "latest_blocked_reason_count",
    "latest_no_reason_code_share",
    "latest_blocked_reason_share",
    "max_blocked_reason_share",
    "max_no_reason_code_share",
    "top_reason_code_limit",
    "blocked_reason_codes",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_strategy_recommendation_reason_trend_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_STRATEGY_RECOMMENDATION_REASON_TREND_TABLE,
) -> PaperStrategyRecommendationReasonTrendDbRow:
    table_name = _validate_table_name(table_name)
    row = strategy_recommendation_reason_trend_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            status,
            source_report_count,
            first_generated_at,
            latest_generated_at,
            latest_primary_reason_code_counts,
            total_primary_reason_code_counts,
            top_new_reason_codes,
            persistent_reason_codes,
            latest_reason_code_count,
            latest_no_reason_code_count,
            latest_blocked_reason_count,
            latest_no_reason_code_share,
            latest_blocked_reason_share,
            max_blocked_reason_share,
            max_no_reason_code_share,
            top_reason_code_limit,
            blocked_reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.status,
        row.source_report_count,
        row.first_generated_at,
        row.latest_generated_at,
        row.latest_primary_reason_code_counts_json,
        row.total_primary_reason_code_counts_json,
        row.top_new_reason_codes_json,
        row.persistent_reason_codes_json,
        row.latest_reason_code_count,
        row.latest_no_reason_code_count,
        row.latest_blocked_reason_count,
        row.latest_no_reason_code_share,
        row.latest_blocked_reason_share,
        row.max_blocked_reason_share,
        row.max_no_reason_code_share,
        row.top_reason_code_limit,
        row.blocked_reason_codes_json,
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


def load_strategy_recommendation_reason_trend_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_STRATEGY_RECOMMENDATION_REASON_TREND_TABLE,
) -> tuple["PaperStrategyRecommendationReasonTrendReport", ...]:
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
    return tuple(strategy_recommendation_reason_trend_report_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperStrategyRecommendationReasonTrendDbRow:
    if isinstance(record, PaperStrategyRecommendationReasonTrendDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected reason trend columns")
    return PaperStrategyRecommendationReasonTrendDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        status=values[3],
        source_report_count=values[4],
        first_generated_at=values[5],
        latest_generated_at=values[6],
        latest_primary_reason_code_counts_json=_normalize_json_object(
            "latest_primary_reason_code_counts",
            values[7],
        ),
        total_primary_reason_code_counts_json=_normalize_json_object(
            "total_primary_reason_code_counts",
            values[8],
        ),
        top_new_reason_codes_json=_normalize_json_object(
            "top_new_reason_codes",
            values[9],
        ),
        persistent_reason_codes_json=_normalize_json_list(
            "persistent_reason_codes",
            values[10],
        ),
        latest_reason_code_count=values[11],
        latest_no_reason_code_count=values[12],
        latest_blocked_reason_count=values[13],
        latest_no_reason_code_share=values[14],
        latest_blocked_reason_share=values[15],
        max_blocked_reason_share=values[16],
        max_no_reason_code_share=values[17],
        top_reason_code_limit=values[18],
        blocked_reason_codes_json=_normalize_json_list(
            "blocked_reason_codes",
            values[19],
        ),
        payload_json=_normalize_json_object("payload", values[20]),
        paper_only=values[21],
        report_only=values[22],
        readonly=values[23],
    )


def _close_cursor_after_operation_error(cursor: Any) -> None:
    try:
        cursor.close()
    except BaseException:
        pass


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_list(field_name: str, value: Any) -> list[Any]:
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


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be stable, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
