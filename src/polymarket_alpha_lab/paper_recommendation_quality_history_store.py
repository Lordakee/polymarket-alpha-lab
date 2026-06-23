"""DB-API repository for paper recommendation quality history reports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_recommendation_quality_history_db_row import (
    PaperRecommendationQualityHistoryDbRow,
    paper_recommendation_quality_history_report_from_db_row,
    paper_recommendation_quality_history_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_recommendation_quality_history import (
        PaperRecommendationQualityHistoryReport,
    )


__all__ = (
    "DEFAULT_PAPER_RECOMMENDATION_QUALITY_HISTORY_REPORTS_TABLE",
    "PaperRecommendationQualityHistoryInsertResult",
    "insert_paper_recommendation_quality_history_report",
    "insert_paper_recommendation_quality_history_report_with_result",
    "load_paper_recommendation_quality_history_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
DEFAULT_PAPER_RECOMMENDATION_QUALITY_HISTORY_REPORTS_TABLE = (
    "paper_recommendation_quality_history_reports"
)
_HISTORY_STATUSES = ("pass", "watch", "blocked")
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "history_status",
    "source_report_count",
    "first_source_generated_at",
    "latest_source_generated_at",
    "summary_status_rows_json",
    "pass_summary_count",
    "watch_summary_count",
    "blocked_summary_count",
    "incomplete_summary_count",
    "duplicate_generated_at_count",
    "recurring_blocked_reason_codes_json",
    "recurring_incomplete_subreports_json",
    "recurring_incomplete_subreport_count",
    "reason_codes_json",
    "reason_code_count",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperRecommendationQualityHistoryInsertResult:
    row: PaperRecommendationQualityHistoryDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperRecommendationQualityHistoryDbRow:
            raise ValueError("row must be a PaperRecommendationQualityHistoryDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_recommendation_quality_history_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_RECOMMENDATION_QUALITY_HISTORY_REPORTS_TABLE,
) -> PaperRecommendationQualityHistoryDbRow:
    return insert_paper_recommendation_quality_history_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_recommendation_quality_history_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_RECOMMENDATION_QUALITY_HISTORY_REPORTS_TABLE,
) -> PaperRecommendationQualityHistoryInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_recommendation_quality_history_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            history_status,
            source_report_count,
            first_source_generated_at,
            latest_source_generated_at,
            summary_status_rows_json,
            pass_summary_count,
            watch_summary_count,
            blocked_summary_count,
            incomplete_summary_count,
            duplicate_generated_at_count,
            recurring_blocked_reason_codes_json,
            recurring_incomplete_subreports_json,
            recurring_incomplete_subreport_count,
            reason_codes_json,
            reason_code_count,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.history_status,
        row.source_report_count,
        row.first_source_generated_at,
        row.latest_source_generated_at,
        row.summary_status_rows_json,
        row.pass_summary_count,
        row.watch_summary_count,
        row.blocked_summary_count,
        row.incomplete_summary_count,
        row.duplicate_generated_at_count,
        row.recurring_blocked_reason_codes_json,
        row.recurring_incomplete_subreports_json,
        row.recurring_incomplete_subreport_count,
        row.reason_codes_json,
        row.reason_code_count,
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        rowcount = cursor.rowcount
    finally:
        try:
            cursor.close()
        except Exception:
            pass
    if rowcount not in (0, 1):
        raise ValueError("insert rowcount must be 0 or 1")
    return PaperRecommendationQualityHistoryInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_recommendation_quality_history_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    history_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_RECOMMENDATION_QUALITY_HISTORY_REPORTS_TABLE,
) -> tuple["PaperRecommendationQualityHistoryReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if history_status is not None:
        _require_history_status("history_status", history_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if history_status is not None:
        conditions.append("history_status = %s")
        params.append(history_status)

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
    finally:
        try:
            cursor.close()
        except Exception:
            pass
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(
        paper_recommendation_quality_history_report_from_db_row(row)
        for row in rows
    )


def _db_row_from_record(record: Any) -> PaperRecommendationQualityHistoryDbRow:
    if isinstance(record, PaperRecommendationQualityHistoryDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected quality history columns")
    return PaperRecommendationQualityHistoryDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        history_status=values[3],
        source_report_count=values[4],
        first_source_generated_at=values[5],
        latest_source_generated_at=values[6],
        summary_status_rows_json=_normalize_json_array(
            "summary_status_rows",
            values[7],
        ),
        pass_summary_count=values[8],
        watch_summary_count=values[9],
        blocked_summary_count=values[10],
        incomplete_summary_count=values[11],
        duplicate_generated_at_count=values[12],
        recurring_blocked_reason_codes_json=_normalize_json_array(
            "recurring_blocked_reason_codes",
            values[13],
        ),
        recurring_incomplete_subreports_json=_normalize_json_array(
            "recurring_incomplete_subreports",
            values[14],
        ),
        recurring_incomplete_subreport_count=values[15],
        reason_codes_json=_normalize_json_array("reason_codes", values[16]),
        reason_code_count=values[17],
        payload_json=_normalize_json_object("payload", values[18]),
        paper_only=values[19],
        report_only=values[20],
        readonly=values[21],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
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


def _require_history_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _HISTORY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
