"""DB-API repository for paper strategy candidate research queue history reports."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.strategy_candidate_research_queue_history_db_row import (
    PaperStrategyCandidateResearchQueueHistoryDbRow,
    paper_strategy_candidate_research_queue_history_report_from_db_row,
    paper_strategy_candidate_research_queue_history_report_to_db_row,
)


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_TABLE",
    "insert_paper_strategy_candidate_research_queue_history_report",
    "load_paper_strategy_candidate_research_queue_history_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_TABLE = (
    "paper_strategy_candidate_research_queue_history_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "source_report_count",
    "first_source_generated_at",
    "last_source_generated_at",
    "action_status_research_ready_count",
    "action_status_watch_count",
    "action_status_blocked_count",
    "research_status_ready_count",
    "research_status_watch_count",
    "research_status_blocked_count",
    "total_ready_notional",
    "total_selected_notional",
    "total_suggested_notional",
    "latest_action_status",
    "latest_recommended_next_step",
    "latest_research_status",
    "latest_top_research_priority_score",
    "latest_average_research_ready_score",
    "status_transition_count",
    "ready_notional_delta",
    "selected_notional_delta",
    "latest_selected_count",
    "latest_skipped_count",
    "latest_not_selected_count",
    "latest_primary_reason_code_counts",
    "latest_reason_codes",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_strategy_candidate_research_queue_history_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_TABLE,
) -> PaperStrategyCandidateResearchQueueHistoryDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_strategy_candidate_research_queue_history_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            source_report_count,
            first_source_generated_at,
            last_source_generated_at,
            action_status_research_ready_count,
            action_status_watch_count,
            action_status_blocked_count,
            research_status_ready_count,
            research_status_watch_count,
            research_status_blocked_count,
            total_ready_notional,
            total_selected_notional,
            total_suggested_notional,
            latest_action_status,
            latest_recommended_next_step,
            latest_research_status,
            latest_top_research_priority_score,
            latest_average_research_ready_score,
            status_transition_count,
            ready_notional_delta,
            selected_notional_delta,
            latest_selected_count,
            latest_skipped_count,
            latest_not_selected_count,
            latest_primary_reason_code_counts,
            latest_reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.source_report_count,
        row.first_source_generated_at,
        row.last_source_generated_at,
        row.action_status_research_ready_count,
        row.action_status_watch_count,
        row.action_status_blocked_count,
        row.research_status_ready_count,
        row.research_status_watch_count,
        row.research_status_blocked_count,
        row.total_ready_notional,
        row.total_selected_notional,
        row.total_suggested_notional,
        row.latest_action_status,
        row.latest_recommended_next_step,
        row.latest_research_status,
        row.latest_top_research_priority_score,
        row.latest_average_research_ready_score,
        row.status_transition_count,
        row.ready_notional_delta,
        row.selected_notional_delta,
        row.latest_selected_count,
        row.latest_skipped_count,
        row.latest_not_selected_count,
        row.latest_primary_reason_code_counts_json,
        row.latest_reason_codes_json,
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


def load_paper_strategy_candidate_research_queue_history_reports(
    connection: Any,
    *,
    latest_action_status: str | None = None,
    latest_research_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_TABLE,
) -> tuple[Any, ...]:
    table_name = _validate_table_name(table_name)
    if latest_action_status is not None:
        _require_canonical_string("latest_action_status", latest_action_status)
    if latest_research_status is not None:
        _require_canonical_string("latest_research_status", latest_research_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    where_parts: list[str] = []
    params: list[Any] = []
    if latest_action_status is not None:
        where_parts.append("latest_action_status = %s")
        params.append(latest_action_status)
    if latest_research_status is not None:
        where_parts.append("latest_research_status = %s")
        params.append(latest_research_status)
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
    except BaseException:
        _close_cursor_after_operation_error(cursor)
        raise
    cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(
        paper_strategy_candidate_research_queue_history_report_from_db_row(row)
        for row in rows
    )


def _db_row_from_record(
    record: Any,
) -> PaperStrategyCandidateResearchQueueHistoryDbRow:
    if isinstance(record, PaperStrategyCandidateResearchQueueHistoryDbRow):
        return record
    if isinstance(record, dict):
        values = _selected_column_values(record)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = _selected_column_values(as_dict)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise _selected_columns_value_error()
    return PaperStrategyCandidateResearchQueueHistoryDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        source_report_count=values[2],
        first_source_generated_at=values[3],
        last_source_generated_at=values[4],
        action_status_research_ready_count=values[5],
        action_status_watch_count=values[6],
        action_status_blocked_count=values[7],
        research_status_ready_count=values[8],
        research_status_watch_count=values[9],
        research_status_blocked_count=values[10],
        total_ready_notional=values[11],
        total_selected_notional=values[12],
        total_suggested_notional=values[13],
        latest_action_status=values[14],
        latest_recommended_next_step=values[15],
        latest_research_status=values[16],
        latest_top_research_priority_score=values[17],
        latest_average_research_ready_score=values[18],
        status_transition_count=values[19],
        ready_notional_delta=values[20],
        selected_notional_delta=values[21],
        latest_selected_count=values[22],
        latest_skipped_count=values[23],
        latest_not_selected_count=values[24],
        latest_primary_reason_code_counts_json=_normalize_json_object(
            "latest_primary_reason_code_counts",
            values[25],
        ),
        latest_reason_codes_json=_normalize_json_list(
            "latest_reason_codes",
            values[26],
        ),
        payload_json=_normalize_json_object("payload", values[27]),
        paper_only=values[28],
        report_only=values[29],
        readonly=values[30],
    )


def _selected_column_values(record: Any) -> tuple[Any, ...]:
    try:
        return tuple(record[column] for column in _SELECT_COLUMNS)
    except KeyError:
        raise _selected_columns_value_error() from None


def _selected_columns_value_error() -> ValueError:
    return ValueError(
        "DB row must contain selected strategy candidate research queue "
        "history columns",
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_list(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON list")
    return list(value)


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


def _close_cursor_after_operation_error(cursor: Any) -> None:
    try:
        cursor.close()
    except Exception:
        pass
