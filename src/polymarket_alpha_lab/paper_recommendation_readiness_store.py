"""DB-API repository for paper recommendation readiness reports."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_recommendation_readiness_db_row import (
    PaperRecommendationReadinessDbRow,
    paper_recommendation_readiness_report_from_db_row,
    paper_recommendation_readiness_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_recommendation_readiness import (
        PaperRecommendationReadinessReport,
    )


__all__ = (
    "insert_paper_recommendation_readiness_report",
    "load_paper_recommendation_readiness_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_DEFAULT_TABLE_NAME = "paper_recommendation_readiness_reports"
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "input_count",
    "row_count",
    "ready_count",
    "watch_count",
    "blocked_count",
    "top_adjusted_net_probability_edge",
    "total_cost_per_share",
    "readiness_status_counts",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_recommendation_readiness_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> PaperRecommendationReadinessDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_recommendation_readiness_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            input_count,
            row_count,
            ready_count,
            watch_count,
            blocked_count,
            top_adjusted_net_probability_edge,
            total_cost_per_share,
            readiness_status_counts,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.input_count,
        row.row_count,
        row.ready_count,
        row.watch_count,
        row.blocked_count,
        row.top_adjusted_net_probability_edge,
        row.total_cost_per_share,
        row.readiness_status_counts_json,
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


def load_paper_recommendation_readiness_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    min_blocked_count: int | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple["PaperRecommendationReadinessReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if min_blocked_count is not None:
        _require_nonnegative_int("min_blocked_count", min_blocked_count)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if min_blocked_count is not None:
        conditions.append("blocked_count >= %s")
        params.append(min_blocked_count)

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
    return tuple(paper_recommendation_readiness_report_from_db_row(row) for row in rows)


def _close_cursor(cursor: Any, operation_error: BaseException | None) -> None:
    if operation_error is None:
        cursor.close()
        return
    try:
        cursor.close()
    except BaseException:
        pass


def _db_row_from_record(record: Any) -> PaperRecommendationReadinessDbRow:
    if isinstance(record, PaperRecommendationReadinessDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected readiness columns")
    return PaperRecommendationReadinessDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        input_count=values[3],
        row_count=values[4],
        ready_count=values[5],
        watch_count=values[6],
        blocked_count=values[7],
        top_adjusted_net_probability_edge=values[8],
        total_cost_per_share=values[9],
        readiness_status_counts_json=values[10],
        payload_json=_normalize_json_object("payload", values[11]),
        paper_only=values[12],
        report_only=values[13],
        readonly=values[14],
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


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
