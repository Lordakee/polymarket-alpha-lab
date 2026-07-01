"""DB-API repository for paper action-gated queue decision-support trends."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_db_row import (
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows,
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow,
    paper_action_gated_strategy_recommendation_queue_decision_support_trend_from_db_rows,
    paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows,
)


__all__ = (
    "DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE",
    "DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE",
    "insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows",
    "load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_RISK_STATUSES = ("pass", "watch", "blocked")
DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE = (
    "paper_action_gated_queue_decision_support_trend_reports"
)
DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE = (
    "paper_action_gated_queue_decision_support_trend_sources"
)
_REPORT_COLUMNS = (
    "trend_sha256",
    "trend_schema_version",
    "source_window_sha256",
    "generated_at",
    "source_snapshot_count",
    "first_generated_at",
    "latest_generated_at",
    "latest_risk_status",
    "risk_pass_count",
    "risk_watch_count",
    "risk_blocked_count",
    "consecutive_latest_watch_count",
    "consecutive_latest_blocked_count",
    "duplicate_generated_at_count",
    "ready_notional_first",
    "ready_notional_latest",
    "ready_notional_delta",
    "top_priority_score_first",
    "top_priority_score_latest",
    "top_priority_score_delta",
    "average_priority_score_first",
    "average_priority_score_latest",
    "average_priority_score_delta",
    "source_queue_count_first",
    "source_queue_count_latest",
    "source_queue_count_delta",
    "latest_reason_code_counts",
    "total_reason_code_counts",
    "repeated_reason_code_counts",
    "reason_code_rows",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_JSON_COLUMN_ALIASES = {
    "latest_reason_code_counts": "latest_reason_code_counts_json",
    "total_reason_code_counts": "total_reason_code_counts_json",
    "repeated_reason_code_counts": "repeated_reason_code_counts_json",
    "reason_code_rows": "reason_code_rows_json",
}
_SOURCE_COLUMNS = (
    "trend_sha256",
    "trend_ordinal",
    "source_input_position",
    "snapshot_sha256",
    "source_generated_at",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows(
    connection: Any,
    trend_report: Any,
    snapshot_pairs: Any,
    *,
    reports_table_name: str = DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE,
    sources_table_name: str = DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE,
) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows:
    reports_table_name = _validate_table_name(
        "reports_table_name",
        reports_table_name,
    )
    sources_table_name = _validate_table_name(
        "sources_table_name",
        sources_table_name,
    )
    db_rows = paper_action_gated_strategy_recommendation_queue_decision_support_trend_to_db_rows(
        trend_report,
        snapshot_pairs,
    )
    report_sql = f"""
        INSERT INTO {reports_table_name} (
            trend_sha256,
            trend_schema_version,
            source_window_sha256,
            generated_at,
            source_snapshot_count,
            first_generated_at,
            latest_generated_at,
            latest_risk_status,
            risk_pass_count,
            risk_watch_count,
            risk_blocked_count,
            consecutive_latest_watch_count,
            consecutive_latest_blocked_count,
            duplicate_generated_at_count,
            ready_notional_first,
            ready_notional_latest,
            ready_notional_delta,
            top_priority_score_first,
            top_priority_score_latest,
            top_priority_score_delta,
            average_priority_score_first,
            average_priority_score_latest,
            average_priority_score_delta,
            source_queue_count_first,
            source_queue_count_latest,
            source_queue_count_delta,
            latest_reason_code_counts,
            total_reason_code_counts,
            repeated_reason_code_counts,
            reason_code_rows,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (trend_sha256) DO NOTHING
        """
    source_sql = f"""
        INSERT INTO {sources_table_name} (
            trend_sha256,
            trend_ordinal,
            source_input_position,
            snapshot_sha256,
            source_generated_at,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (trend_sha256, trend_ordinal) DO NOTHING
        """
    cursor = connection.cursor()
    operation_error: BaseException | None = None
    try:
        cursor.execute(report_sql, _report_params(db_rows.trend_row))
        for source_row in db_rows.source_rows:
            cursor.execute(source_sql, _source_params(source_row))
    except BaseException as exc:
        operation_error = exc
        raise
    finally:
        _close_cursor(cursor, operation_error)
    return db_rows


def load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows(
    connection: Any,
    *,
    latest_risk_status: str | None = None,
    limit: int | None = None,
    reports_table_name: str = DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE,
    sources_table_name: str = DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE,
) -> tuple[PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows, ...]:
    reports_table_name = _validate_table_name(
        "reports_table_name",
        reports_table_name,
    )
    sources_table_name = _validate_table_name(
        "sources_table_name",
        sources_table_name,
    )
    if latest_risk_status is not None:
        _require_risk_status("latest_risk_status", latest_risk_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    report_rows = _load_report_rows(
        connection,
        latest_risk_status=latest_risk_status,
        limit=limit,
        reports_table_name=reports_table_name,
    )
    if not report_rows:
        return ()

    source_rows = _load_source_rows(
        connection,
        trend_sha256s=tuple(row.trend_sha256 for row in report_rows),
        sources_table_name=sources_table_name,
    )
    source_rows_by_trend_sha256: dict[
        str,
        list[PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow],
    ] = {}
    for source_row in source_rows:
        source_rows_by_trend_sha256.setdefault(source_row.trend_sha256, []).append(
            source_row,
        )

    aggregates = []
    for trend_row in report_rows:
        grouped_source_rows = tuple(
            sorted(
                source_rows_by_trend_sha256.get(trend_row.trend_sha256, ()),
                key=lambda source_row: source_row.trend_ordinal,
            ),
        )
        aggregates.append(
            paper_action_gated_strategy_recommendation_queue_decision_support_trend_from_db_rows(
                PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRows(
                    trend_row=trend_row,
                    source_rows=grouped_source_rows,
                ),
            ),
        )
    return tuple(aggregates)


def _load_report_rows(
    connection: Any,
    *,
    latest_risk_status: str | None,
    limit: int | None,
    reports_table_name: str,
) -> tuple[PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow, ...]:
    where_parts: list[str] = []
    params: list[Any] = []
    if latest_risk_status is not None:
        where_parts.append("latest_risk_status = %s")
        params.append(latest_risk_status)
    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    limit_clause = ""
    if limit is not None:
        limit_clause = "LIMIT %s"
        params.append(limit)

    columns = ",\n            ".join(_REPORT_COLUMNS)
    sql = f"""
        SELECT
            {columns}
        FROM {reports_table_name}
        {where_clause}
        ORDER BY generated_at DESC, inserted_at DESC, trend_sha256 DESC
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
    return tuple(_report_row_from_record(record) for record in records)


def _load_source_rows(
    connection: Any,
    *,
    trend_sha256s: tuple[str, ...],
    sources_table_name: str,
) -> tuple[PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow, ...]:
    placeholders = ", ".join("%s" for _ in trend_sha256s)
    columns = ",\n            ".join(_SOURCE_COLUMNS)
    sql = f"""
        SELECT
            {columns}
        FROM {sources_table_name}
        WHERE trend_sha256 IN ({placeholders})
        ORDER BY trend_sha256 ASC, trend_ordinal ASC
        """
    cursor = connection.cursor()
    operation_error: BaseException | None = None
    try:
        cursor.execute(sql, trend_sha256s)
        records = cursor.fetchall()
    except BaseException as exc:
        operation_error = exc
        raise
    finally:
        _close_cursor(cursor, operation_error)
    return tuple(_source_row_from_record(record) for record in records)


def _close_cursor(cursor: Any, operation_error: BaseException | None) -> None:
    if operation_error is None:
        cursor.close()
        return
    try:
        cursor.close()
    except BaseException:
        pass


def _report_params(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
) -> tuple[Any, ...]:
    return (
        row.trend_sha256,
        row.trend_schema_version,
        row.source_window_sha256,
        row.generated_at,
        row.source_snapshot_count,
        row.first_generated_at,
        row.latest_generated_at,
        row.latest_risk_status,
        row.risk_pass_count,
        row.risk_watch_count,
        row.risk_blocked_count,
        row.consecutive_latest_watch_count,
        row.consecutive_latest_blocked_count,
        row.duplicate_generated_at_count,
        row.ready_notional_first,
        row.ready_notional_latest,
        row.ready_notional_delta,
        row.top_priority_score_first,
        row.top_priority_score_latest,
        row.top_priority_score_delta,
        row.average_priority_score_first,
        row.average_priority_score_latest,
        row.average_priority_score_delta,
        row.source_queue_count_first,
        row.source_queue_count_latest,
        row.source_queue_count_delta,
        row.latest_reason_code_counts_json,
        row.total_reason_code_counts_json,
        row.repeated_reason_code_counts_json,
        row.reason_code_rows_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def _source_params(
    row: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow,
) -> tuple[Any, ...]:
    return (
        row.trend_sha256,
        row.trend_ordinal,
        row.source_input_position,
        row.snapshot_sha256,
        row.source_generated_at,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def _report_row_from_record(
    record: Any,
) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow:
    if isinstance(
        record,
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow,
    ):
        return record
    values = _values_from_record(
        record,
        columns=_REPORT_COLUMNS,
        aliases=_REPORT_JSON_COLUMN_ALIASES,
    )
    if len(values) != len(_REPORT_COLUMNS):
        raise ValueError(
            "DB row must contain selected action-gated queue trend report columns",
        )
    return PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendDbRow(
        trend_sha256=values[0],
        trend_schema_version=values[1],
        source_window_sha256=values[2],
        generated_at=values[3],
        source_snapshot_count=values[4],
        first_generated_at=values[5],
        latest_generated_at=values[6],
        latest_risk_status=values[7],
        risk_pass_count=values[8],
        risk_watch_count=values[9],
        risk_blocked_count=values[10],
        consecutive_latest_watch_count=values[11],
        consecutive_latest_blocked_count=values[12],
        duplicate_generated_at_count=values[13],
        ready_notional_first=values[14],
        ready_notional_latest=values[15],
        ready_notional_delta=values[16],
        top_priority_score_first=values[17],
        top_priority_score_latest=values[18],
        top_priority_score_delta=values[19],
        average_priority_score_first=values[20],
        average_priority_score_latest=values[21],
        average_priority_score_delta=values[22],
        source_queue_count_first=values[23],
        source_queue_count_latest=values[24],
        source_queue_count_delta=values[25],
        latest_reason_code_counts_json=_normalize_json_object(
            "latest_reason_code_counts",
            values[26],
        ),
        total_reason_code_counts_json=_normalize_json_object(
            "total_reason_code_counts",
            values[27],
        ),
        repeated_reason_code_counts_json=_normalize_json_object(
            "repeated_reason_code_counts",
            values[28],
        ),
        reason_code_rows_json=_normalize_json_array("reason_code_rows", values[29]),
        paper_only=values[30],
        report_only=values[31],
        readonly=values[32],
    )


def _source_row_from_record(
    record: Any,
) -> PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow:
    if isinstance(
        record,
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow,
    ):
        return record
    values = _values_from_record(record, columns=_SOURCE_COLUMNS, aliases={})
    if len(values) != len(_SOURCE_COLUMNS):
        raise ValueError(
            "DB row must contain selected action-gated queue trend source columns",
        )
    return PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendSourceDbRow(
        trend_sha256=values[0],
        trend_ordinal=values[1],
        source_input_position=values[2],
        snapshot_sha256=values[3],
        source_generated_at=values[4],
        paper_only=values[5],
        report_only=values[6],
        readonly=values[7],
    )


def _values_from_record(
    record: Any,
    *,
    columns: tuple[str, ...],
    aliases: Mapping[str, str],
) -> tuple[Any, ...]:
    if isinstance(record, Mapping):
        return _values_from_mapping(record, columns=columns, aliases=aliases)
    if hasattr(record, "_asdict"):
        return _values_from_mapping(record._asdict(), columns=columns, aliases=aliases)
    return tuple(record)


def _values_from_mapping(
    record: Mapping[str, Any],
    *,
    columns: tuple[str, ...],
    aliases: Mapping[str, str],
) -> tuple[Any, ...]:
    values: list[Any] = []
    for column in columns:
        if column in record:
            values.append(record[column])
            continue
        alias = aliases.get(column)
        if alias is not None and alias in record:
            values.append(record[alias])
            continue
        raise KeyError(column)
    return tuple(values)


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


def _validate_table_name(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(
            f"{field_name} must be a lowercase identifier with optional schema prefix",
        )
    parts = value.split(".")
    if not 1 <= len(parts) <= 2:
        raise ValueError(
            f"{field_name} must be a lowercase identifier with optional schema prefix",
        )
    for part in parts:
        if len(part.encode("utf-8")) > 63:
            raise ValueError(f"{field_name} identifier parts must be 63 bytes or less")
        if _IDENTIFIER_PATTERN.fullmatch(part) is None:
            raise ValueError(
                f"{field_name} must be a lowercase identifier with optional schema prefix",
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
