"""DB-API repository for paper action-gated queue history reports."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_db_row import (
    PaperActionGatedStrategyRecommendationQueueHistoryDbRow,
    paper_action_gated_strategy_recommendation_queue_history_report_from_db_row,
    paper_action_gated_strategy_recommendation_queue_history_report_to_db_row,
)


__all__ = (
    "DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_HISTORY_TABLE",
    "insert_paper_action_gated_strategy_recommendation_queue_history_report",
    "load_paper_action_gated_strategy_recommendation_queue_history_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_HISTORY_TABLE = (
    "paper_action_gated_strategy_recommendation_queue_history_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "source_report_count",
    "first_source_generated_at",
    "last_source_generated_at",
    "research_ready_count",
    "watch_count",
    "blocked_count",
    "total_ready_notional",
    "latest_action_status",
    "latest_recommended_next_step",
    "status_transition_count",
    "ready_notional_delta",
    "latest_reason_code_counts",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_action_gated_strategy_recommendation_queue_history_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_HISTORY_TABLE,
) -> PaperActionGatedStrategyRecommendationQueueHistoryDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_action_gated_strategy_recommendation_queue_history_report_to_db_row(
        report,
    )
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            source_report_count,
            first_source_generated_at,
            last_source_generated_at,
            research_ready_count,
            watch_count,
            blocked_count,
            total_ready_notional,
            latest_action_status,
            latest_recommended_next_step,
            status_transition_count,
            ready_notional_delta,
            latest_reason_code_counts,
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
        row.source_report_count,
        row.first_source_generated_at,
        row.last_source_generated_at,
        row.research_ready_count,
        row.watch_count,
        row.blocked_count,
        row.total_ready_notional,
        row.latest_action_status,
        row.latest_recommended_next_step,
        row.status_transition_count,
        row.ready_notional_delta,
        row.latest_reason_code_counts_json,
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


def load_paper_action_gated_strategy_recommendation_queue_history_reports(
    connection: Any,
    *,
    latest_action_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_HISTORY_TABLE,
) -> tuple[Any, ...]:
    table_name = _validate_table_name(table_name)
    if latest_action_status is not None:
        _require_canonical_string("latest_action_status", latest_action_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    where_parts: list[str] = []
    params: list[Any] = []
    if latest_action_status is not None:
        where_parts.append("latest_action_status = %s")
        params.append(latest_action_status)
    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

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
    return tuple(
        paper_action_gated_strategy_recommendation_queue_history_report_from_db_row(
            row,
        )
        for row in rows
    )


def _db_row_from_record(
    record: Any,
) -> PaperActionGatedStrategyRecommendationQueueHistoryDbRow:
    if isinstance(record, PaperActionGatedStrategyRecommendationQueueHistoryDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError(
            "DB row must contain selected action-gated queue history columns",
        )
    return PaperActionGatedStrategyRecommendationQueueHistoryDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        source_report_count=values[2],
        first_source_generated_at=values[3],
        last_source_generated_at=values[4],
        research_ready_count=values[5],
        watch_count=values[6],
        blocked_count=values[7],
        total_ready_notional=values[8],
        latest_action_status=values[9],
        latest_recommended_next_step=values[10],
        status_transition_count=values[11],
        ready_notional_delta=values[12],
        latest_reason_code_counts_json=_normalize_json_object(
            "latest_reason_code_counts",
            values[13],
        ),
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
    if type(value) is not str:
        raise ValueError(
            "table_name must be a lowercase identifier with optional schema prefix",
        )
    parts = value.split(".")
    if not 1 <= len(parts) <= 2:
        raise ValueError(
            "table_name must be a lowercase identifier with optional schema prefix",
        )
    if any(_IDENTIFIER_PATTERN.fullmatch(part) is None for part in parts):
        raise ValueError(
            "table_name must be a lowercase identifier with optional schema prefix",
        )
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
