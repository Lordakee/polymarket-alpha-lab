"""DB-API repository for paper recommendation quality summary reports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_recommendation_quality_summary_db_row import (
    PaperRecommendationQualitySummaryDbRow,
    paper_recommendation_quality_summary_report_from_db_row,
    paper_recommendation_quality_summary_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_recommendation_quality_summary import (
        PaperRecommendationQualitySummaryReport,
    )


__all__ = (
    "DEFAULT_PAPER_RECOMMENDATION_QUALITY_SUMMARY_REPORTS_TABLE",
    "PaperRecommendationQualitySummaryInsertResult",
    "insert_paper_recommendation_quality_summary_report",
    "insert_paper_recommendation_quality_summary_report_with_result",
    "load_paper_recommendation_quality_summary_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
DEFAULT_PAPER_RECOMMENDATION_QUALITY_SUMMARY_REPORTS_TABLE = (
    "paper_recommendation_quality_summary_reports"
)
_STATUSES = ("pass", "watch", "blocked", "incomplete")
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "summary_status",
    "subreport_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "incomplete_count",
    "reason_code_counts_json",
    "reason_codes_json",
    "subreports_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperRecommendationQualitySummaryInsertResult:
    row: PaperRecommendationQualitySummaryDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperRecommendationQualitySummaryDbRow:
            raise ValueError("row must be a PaperRecommendationQualitySummaryDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_recommendation_quality_summary_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_RECOMMENDATION_QUALITY_SUMMARY_REPORTS_TABLE,
) -> PaperRecommendationQualitySummaryDbRow:
    return insert_paper_recommendation_quality_summary_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_recommendation_quality_summary_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_RECOMMENDATION_QUALITY_SUMMARY_REPORTS_TABLE,
) -> PaperRecommendationQualitySummaryInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_recommendation_quality_summary_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            summary_status,
            subreport_count,
            pass_count,
            watch_count,
            blocked_count,
            incomplete_count,
            reason_code_counts_json,
            reason_codes_json,
            subreports_json,
            payload_json,
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
        row.summary_status,
        row.subreport_count,
        row.pass_count,
        row.watch_count,
        row.blocked_count,
        row.incomplete_count,
        row.reason_code_counts_json,
        row.reason_codes_json,
        row.subreports_json,
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
    return PaperRecommendationQualitySummaryInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_recommendation_quality_summary_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    summary_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_RECOMMENDATION_QUALITY_SUMMARY_REPORTS_TABLE,
) -> tuple["PaperRecommendationQualitySummaryReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if summary_status is not None:
        _require_status("summary_status", summary_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if summary_status is not None:
        conditions.append("summary_status = %s")
        params.append(summary_status)

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
        paper_recommendation_quality_summary_report_from_db_row(row) for row in rows
    )


def _db_row_from_record(record: Any) -> PaperRecommendationQualitySummaryDbRow:
    if isinstance(record, PaperRecommendationQualitySummaryDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected quality summary columns")
    return PaperRecommendationQualitySummaryDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        summary_status=values[3],
        subreport_count=values[4],
        pass_count=values[5],
        watch_count=values[6],
        blocked_count=values[7],
        incomplete_count=values[8],
        reason_code_counts_json=_normalize_json_array("reason_code_counts", values[9]),
        reason_codes_json=_normalize_json_array("reason_codes", values[10]),
        subreports_json=_normalize_json_array("subreports", values[11]),
        payload_json=_normalize_json_object("payload", values[12]),
        paper_only=values[13],
        report_only=values[14],
        readonly=values[15],
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


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, blocked, or incomplete")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
