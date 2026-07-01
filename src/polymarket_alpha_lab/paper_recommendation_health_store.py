"""DB-API repository for paper recommendation health reports."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_recommendation_health_db_row import (
    PaperRecommendationHealthDbRow,
    paper_recommendation_health_report_from_db_row,
    paper_recommendation_health_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_recommendation_health import (
        PaperRecommendationHealthReport,
    )


__all__ = (
    "insert_paper_recommendation_health_report",
    "load_paper_recommendation_health_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_DEFAULT_TABLE_NAME = "paper_recommendation_health_reports"
_HEALTH_STATUSES = ("pass", "watch", "blocked")
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "health_status",
    "row_count",
    "recommend_count",
    "watch_count",
    "reject_count",
    "average_net_probability_edge",
    "average_total_cost_per_share",
    "top_recommendation_score",
    "reason_code_counts",
    "max_average_cost_per_share",
    "min_recommend_share",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_recommendation_health_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> PaperRecommendationHealthDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_recommendation_health_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            health_status,
            row_count,
            recommend_count,
            watch_count,
            reject_count,
            average_net_probability_edge,
            average_total_cost_per_share,
            top_recommendation_score,
            reason_code_counts,
            max_average_cost_per_share,
            min_recommend_share,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.health_status,
        row.row_count,
        row.recommend_count,
        row.watch_count,
        row.reject_count,
        row.average_net_probability_edge,
        row.average_total_cost_per_share,
        row.top_recommendation_score,
        row.reason_code_counts_json,
        row.max_average_cost_per_share,
        row.min_recommend_share,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )
    cursor = connection.cursor()
    operation_error: BaseException | None = None
    try:
        cursor.execute(sql, params)
    except BaseException as exc:
        operation_error = exc
        raise
    finally:
        _close_cursor(cursor, operation_error)
    return row


def load_paper_recommendation_health_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    health_status: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple["PaperRecommendationHealthReport", ...]:
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
    operation_error: BaseException | None = None
    try:
        cursor.execute(sql, tuple(params))
        records = cursor.fetchall()
    except BaseException as exc:
        operation_error = exc
        raise
    finally:
        _close_cursor(cursor, operation_error)
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(paper_recommendation_health_report_from_db_row(row) for row in rows)


def _close_cursor(cursor: Any, operation_error: BaseException | None) -> None:
    if operation_error is None:
        cursor.close()
        return
    try:
        cursor.close()
    except BaseException:
        pass


def _db_row_from_record(record: Any) -> PaperRecommendationHealthDbRow:
    if isinstance(record, PaperRecommendationHealthDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected health columns")
    return PaperRecommendationHealthDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        health_status=values[3],
        row_count=values[4],
        recommend_count=values[5],
        watch_count=values[6],
        reject_count=values[7],
        average_net_probability_edge=values[8],
        average_total_cost_per_share=values[9],
        top_recommendation_score=values[10],
        reason_code_counts_json=values[11],
        max_average_cost_per_share=values[12],
        min_recommend_share=values[13],
        payload_json=_normalize_json_object("payload", values[14]),
        paper_only=values[15],
        report_only=values[16],
        readonly=values[17],
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


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
