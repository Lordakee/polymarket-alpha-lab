"""DB-API repository for paper recommendation consistency reports."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_recommendation_consistency_db_row import (
    PaperRecommendationConsistencyDbRow,
    paper_recommendation_consistency_report_from_db_row,
    paper_recommendation_consistency_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_recommendation_consistency import (
        PaperRecommendationConsistencyReport,
    )


__all__ = (
    "insert_paper_recommendation_consistency_report",
    "load_paper_recommendation_consistency_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_DEFAULT_TABLE_NAME = "paper_recommendation_consistency_reports"
_STATUSES = ("pass", "watch", "blocked")
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "consistency_status",
    "reason_codes",
    "group_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "max_edge_spread",
    "max_score_spread",
    "min_source_count",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_recommendation_consistency_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> PaperRecommendationConsistencyDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_recommendation_consistency_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            consistency_status,
            reason_codes,
            group_count,
            pass_count,
            watch_count,
            blocked_count,
            max_edge_spread,
            max_score_spread,
            min_source_count,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.consistency_status,
        row.reason_codes_json,
        row.group_count,
        row.pass_count,
        row.watch_count,
        row.blocked_count,
        row.max_edge_spread,
        row.max_score_spread,
        row.min_source_count,
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


def load_paper_recommendation_consistency_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    consistency_status: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple["PaperRecommendationConsistencyReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if consistency_status is not None:
        _require_status("consistency_status", consistency_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if consistency_status is not None:
        conditions.append("consistency_status = %s")
        params.append(consistency_status)

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
    return tuple(paper_recommendation_consistency_report_from_db_row(row) for row in rows)


def _close_cursor(cursor: Any, operation_error: BaseException | None) -> None:
    if operation_error is None:
        cursor.close()
        return
    try:
        cursor.close()
    except BaseException:
        pass


def _db_row_from_record(record: Any) -> PaperRecommendationConsistencyDbRow:
    if isinstance(record, PaperRecommendationConsistencyDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected consistency columns")
    return PaperRecommendationConsistencyDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        consistency_status=values[3],
        reason_codes_json=values[4],
        group_count=values[5],
        pass_count=values[6],
        watch_count=values[7],
        blocked_count=values[8],
        max_edge_spread=values[9],
        max_score_spread=values[10],
        min_source_count=values[11],
        payload_json=_normalize_json_object("payload", values[12]),
        paper_only=values[13],
        report_only=values[14],
        readonly=values[15],
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
