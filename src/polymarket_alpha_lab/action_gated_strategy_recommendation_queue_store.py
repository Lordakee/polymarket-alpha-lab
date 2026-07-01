"""DB-API repository for paper action-gated strategy recommendation queues."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_db_row import (
    PaperActionGatedStrategyRecommendationQueueDbRow,
    paper_action_gated_strategy_recommendation_queue_report_from_db_row,
    paper_action_gated_strategy_recommendation_queue_report_to_db_row,
)


__all__ = (
    "DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_TABLE",
    "insert_paper_action_gated_strategy_recommendation_queue_report",
    "load_paper_action_gated_strategy_recommendation_queue_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_TABLE = (
    "paper_action_gated_strategy_recommendation_queue_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_config_version",
    "action_status",
    "recommended_next_step",
    "candidate_count",
    "ready_count",
    "watch_count",
    "blocked_count",
    "total_ready_notional",
    "reason_code_counts",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_action_gated_strategy_recommendation_queue_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_TABLE,
) -> PaperActionGatedStrategyRecommendationQueueDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            source_config_version,
            action_status,
            recommended_next_step,
            candidate_count,
            ready_count,
            watch_count,
            blocked_count,
            total_ready_notional,
            reason_code_counts,
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
        row.source_config_version,
        row.action_status,
        row.recommended_next_step,
        row.candidate_count,
        row.ready_count,
        row.watch_count,
        row.blocked_count,
        row.total_ready_notional,
        row.reason_code_counts_json,
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


def load_paper_action_gated_strategy_recommendation_queue_reports(
    connection: Any,
    *,
    source_config_version: str | None = None,
    action_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_TABLE,
) -> tuple[Any, ...]:
    table_name = _validate_table_name(table_name)
    if source_config_version is not None:
        _require_canonical_string("source_config_version", source_config_version)
    if action_status is not None:
        _require_canonical_string("action_status", action_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    where_parts: list[str] = []
    params: list[Any] = []
    if source_config_version is not None:
        where_parts.append("source_config_version = %s")
        params.append(source_config_version)
    if action_status is not None:
        where_parts.append("action_status = %s")
        params.append(action_status)
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
    return tuple(
        paper_action_gated_strategy_recommendation_queue_report_from_db_row(row)
        for row in rows
    )


def _close_cursor(cursor: Any, operation_error: BaseException | None) -> None:
    if operation_error is None:
        cursor.close()
        return
    try:
        cursor.close()
    except BaseException:
        pass


def _db_row_from_record(
    record: Any,
) -> PaperActionGatedStrategyRecommendationQueueDbRow:
    if isinstance(record, PaperActionGatedStrategyRecommendationQueueDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected action-gated queue columns")
    return PaperActionGatedStrategyRecommendationQueueDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        source_config_version=values[3],
        action_status=values[4],
        recommended_next_step=values[5],
        candidate_count=values[6],
        ready_count=values[7],
        watch_count=values[8],
        blocked_count=values[9],
        total_ready_notional=values[10],
        reason_code_counts_json=_normalize_json_object(
            "reason_code_counts",
            values[11],
        ),
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
