"""DB-API repository for paper action-gated queue decision-support reports."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_db_row import (
    PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow,
    paper_action_gated_strategy_recommendation_queue_decision_support_from_db_row,
    paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row,
)


__all__ = (
    "DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_DECISION_SUPPORT_TABLE",
    "insert_paper_action_gated_strategy_recommendation_queue_decision_support_report",
    "load_paper_action_gated_strategy_recommendation_queue_decision_support_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_POSTGRES_IDENTIFIER_MAX_LENGTH = 63
_RISK_STATUSES = ("pass", "watch", "blocked")
DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_DECISION_SUPPORT_TABLE = (
    "paper_action_gated_queue_decision_support_reports"
)
_SELECT_COLUMNS = (
    "snapshot_sha256",
    "generated_at",
    "priority_source_report_count",
    "priority_research_ready_count",
    "priority_watch_count",
    "priority_blocked_count",
    "priority_total_ready_notional",
    "top_research_priority_score",
    "average_research_priority_score",
    "risk_config_version",
    "risk_status",
    "risk_recommended_next_step",
    "risk_source_queue_count",
    "risk_candidate_count",
    "risk_ready_count",
    "risk_total_ready_notional",
    "risk_largest_queue_ready_notional",
    "risk_reason_codes",
    "priority_payload",
    "risk_payload",
    "paper_only",
    "report_only",
    "readonly",
)
_JSON_COLUMN_ALIASES = {
    "risk_reason_codes": "risk_reason_codes_json",
    "priority_payload": "priority_payload_json",
    "risk_payload": "risk_payload_json",
}


def insert_paper_action_gated_strategy_recommendation_queue_decision_support_report(
    connection: Any,
    priority_report: Any,
    risk_report: Any,
    *,
    table_name: str = (
        DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_DECISION_SUPPORT_TABLE
    ),
) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
        priority_report,
        risk_report,
    )
    sql = f"""
        INSERT INTO {table_name} (
            snapshot_sha256,
            generated_at,
            priority_source_report_count,
            priority_research_ready_count,
            priority_watch_count,
            priority_blocked_count,
            priority_total_ready_notional,
            top_research_priority_score,
            average_research_priority_score,
            risk_config_version,
            risk_status,
            risk_recommended_next_step,
            risk_source_queue_count,
            risk_candidate_count,
            risk_ready_count,
            risk_total_ready_notional,
            risk_largest_queue_ready_notional,
            risk_reason_codes,
            priority_payload,
            risk_payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (snapshot_sha256) DO NOTHING
        """
    params = (
        row.snapshot_sha256,
        row.generated_at,
        row.priority_source_report_count,
        row.priority_research_ready_count,
        row.priority_watch_count,
        row.priority_blocked_count,
        row.priority_total_ready_notional,
        row.top_research_priority_score,
        row.average_research_priority_score,
        row.risk_config_version,
        row.risk_status,
        row.risk_recommended_next_step,
        row.risk_source_queue_count,
        row.risk_candidate_count,
        row.risk_ready_count,
        row.risk_total_ready_notional,
        row.risk_largest_queue_ready_notional,
        row.risk_reason_codes_json,
        row.priority_payload_json,
        row.risk_payload_json,
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


def load_paper_action_gated_strategy_recommendation_queue_decision_support_reports(
    connection: Any,
    *,
    risk_status: str | None = None,
    risk_config_version: str | None = None,
    limit: int | None = None,
    table_name: str = (
        DEFAULT_ACTION_GATED_STRATEGY_RECOMMENDATION_QUEUE_DECISION_SUPPORT_TABLE
    ),
) -> tuple[Any, ...]:
    table_name = _validate_table_name(table_name)
    if risk_status is not None:
        _require_risk_status("risk_status", risk_status)
    if risk_config_version is not None:
        _require_canonical_string("risk_config_version", risk_config_version)
    if limit is not None:
        _require_positive_int("limit", limit)

    where_parts: list[str] = []
    params: list[Any] = []
    if risk_status is not None:
        where_parts.append("risk_status = %s")
        params.append(risk_status)
    if risk_config_version is not None:
        where_parts.append("risk_config_version = %s")
        params.append(risk_config_version)
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
        ORDER BY generated_at DESC, inserted_at DESC, snapshot_sha256 DESC
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
        paper_action_gated_strategy_recommendation_queue_decision_support_from_db_row(
            row,
        )
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
) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow:
    if isinstance(
        record,
        PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow,
    ):
        return record
    if isinstance(record, Mapping):
        values = _values_from_mapping(record)
    elif hasattr(record, "_asdict"):
        values = _values_from_mapping(record._asdict())
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError(
            "DB row must contain selected action-gated queue decision-support columns",
        )
    return PaperActionGatedStrategyRecommendationQueueDecisionSupportDbRow(
        snapshot_sha256=values[0],
        generated_at=values[1],
        priority_source_report_count=values[2],
        priority_research_ready_count=values[3],
        priority_watch_count=values[4],
        priority_blocked_count=values[5],
        priority_total_ready_notional=values[6],
        top_research_priority_score=values[7],
        average_research_priority_score=values[8],
        risk_config_version=values[9],
        risk_status=values[10],
        risk_recommended_next_step=values[11],
        risk_source_queue_count=values[12],
        risk_candidate_count=values[13],
        risk_ready_count=values[14],
        risk_total_ready_notional=values[15],
        risk_largest_queue_ready_notional=values[16],
        risk_reason_codes_json=_normalize_json_array(
            "risk_reason_codes",
            values[17],
        ),
        priority_payload_json=_normalize_json_object("priority_payload", values[18]),
        risk_payload_json=_normalize_json_object("risk_payload", values[19]),
        paper_only=values[20],
        report_only=values[21],
        readonly=values[22],
    )


def _values_from_mapping(record: Mapping[str, Any]) -> tuple[Any, ...]:
    values: list[Any] = []
    for column in _SELECT_COLUMNS:
        if column in record:
            values.append(record[column])
            continue
        alias = _JSON_COLUMN_ALIASES.get(column)
        if alias is not None and alias in record:
            values.append(record[alias])
            continue
        raise KeyError(column)
    return tuple(values)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


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
    if any(
        _IDENTIFIER_PATTERN.fullmatch(part) is None
        or len(part) > _POSTGRES_IDENTIFIER_MAX_LENGTH
        for part in parts
    ):
        raise ValueError(
            "table_name must be a lowercase identifier with optional schema prefix",
        )
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_risk_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in _RISK_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
