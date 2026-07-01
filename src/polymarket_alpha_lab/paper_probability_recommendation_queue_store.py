"""DB-API repository for paper probability recommendation queue reports."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.paper_probability_recommendation_queue import (
    PaperProbabilityRecommendationQueueReport,
)
from polymarket_alpha_lab.paper_probability_recommendation_queue_db_row import (
    PaperProbabilityRecommendationQueueDbRow,
    paper_probability_recommendation_queue_report_from_db_row,
    paper_probability_recommendation_queue_report_to_db_row,
)


__all__ = (
    "insert_paper_probability_recommendation_queue_report",
    "load_paper_probability_recommendation_queue_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_DEFAULT_TABLE_NAME = "paper_probability_recommendation_queue_reports"
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "source_config_version",
    "input_count",
    "queue_count",
    "research_review_count",
    "await_fresh_context_count",
    "skip_count",
    "excluded_count",
    "reason_code_counts",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_probability_recommendation_queue_report(
    connection: Any,
    report: PaperProbabilityRecommendationQueueReport,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> PaperProbabilityRecommendationQueueDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_probability_recommendation_queue_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            source_config_version,
            input_count,
            queue_count,
            research_review_count,
            await_fresh_context_count,
            skip_count,
            excluded_count,
            reason_code_counts,
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
        row.source_config_version,
        row.input_count,
        row.queue_count,
        row.research_review_count,
        row.await_fresh_context_count,
        row.skip_count,
        row.excluded_count,
        row.reason_code_counts_json,
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


def load_paper_probability_recommendation_queue_reports(
    connection: Any,
    *,
    source_config_version: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple[PaperProbabilityRecommendationQueueReport, ...]:
    table_name = _validate_table_name(table_name)
    if source_config_version is not None:
        _require_canonical_string("source_config_version", source_config_version)
    if limit is not None:
        _require_positive_int("limit", limit)

    where_clause = ""
    params: list[Any] = []
    if source_config_version is not None:
        where_clause = "WHERE source_config_version = %s"
        params.append(source_config_version)

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
    return tuple(
        paper_probability_recommendation_queue_report_from_db_row(row)
        for row in rows
    )


def _db_row_from_record(record: Any) -> PaperProbabilityRecommendationQueueDbRow:
    if isinstance(record, PaperProbabilityRecommendationQueueDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected probability queue columns")
    return PaperProbabilityRecommendationQueueDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        source_config_version=values[2],
        input_count=values[3],
        queue_count=values[4],
        research_review_count=values[5],
        await_fresh_context_count=values[6],
        skip_count=values[7],
        excluded_count=values[8],
        reason_code_counts_json=_normalize_json_object(
            "reason_code_counts",
            values[9],
        ),
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
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError("table_name must be a simple lowercase identifier")
    return value


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


def _close_cursor_after_operation_error(cursor: Any) -> None:
    try:
        cursor.close()
    except BaseException:
        pass
