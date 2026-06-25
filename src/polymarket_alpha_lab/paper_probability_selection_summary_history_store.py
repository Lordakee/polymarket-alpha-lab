"""DB-API repository for paper probability selection summary history reports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_probability_selection_summary_history_db_row import (
    PaperProbabilitySelectionSummaryHistoryDbRow,
    paper_probability_selection_summary_history_report_from_db_row,
    paper_probability_selection_summary_history_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_probability_selection_summary_history import (
        PaperProbabilitySelectionSummaryHistoryReport,
    )


__all__ = (
    "DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_REPORTS_TABLE",
    "PaperProbabilitySelectionSummaryHistoryInsertResult",
    "insert_paper_probability_selection_summary_history_report",
    "insert_paper_probability_selection_summary_history_report_with_result",
    "load_paper_probability_selection_summary_history_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_REPORTS_TABLE = (
    "paper_probability_selection_summary_history_reports"
)
_HISTORY_STATUSES = ("ready", "watch", "blocked")
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_report_count",
    "latest_generated_at",
    "latest_age_seconds",
    "latest_queue_count",
    "latest_selected_count",
    "latest_selected_share",
    "average_selected_share",
    "history_status",
    "recommended_next_step",
    "reason_codes",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryHistoryInsertResult:
    row: PaperProbabilitySelectionSummaryHistoryDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperProbabilitySelectionSummaryHistoryDbRow:
            raise ValueError(
                "row must be a PaperProbabilitySelectionSummaryHistoryDbRow",
            )
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_probability_selection_summary_history_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_REPORTS_TABLE,
) -> PaperProbabilitySelectionSummaryHistoryDbRow:
    return insert_paper_probability_selection_summary_history_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_probability_selection_summary_history_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_REPORTS_TABLE,
) -> PaperProbabilitySelectionSummaryHistoryInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_probability_selection_summary_history_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            source_report_count,
            latest_generated_at,
            latest_age_seconds,
            latest_queue_count,
            latest_selected_count,
            latest_selected_share,
            average_selected_share,
            history_status,
            recommended_next_step,
            reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.source_report_count,
        row.latest_generated_at,
        row.latest_age_seconds,
        row.latest_queue_count,
        row.latest_selected_count,
        row.latest_selected_share,
        row.average_selected_share,
        row.history_status,
        row.recommended_next_step,
        row.reason_codes_json,
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
    return PaperProbabilitySelectionSummaryHistoryInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_probability_selection_summary_history_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    history_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_REPORTS_TABLE,
) -> tuple["PaperProbabilitySelectionSummaryHistoryReport", ...]:
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
        paper_probability_selection_summary_history_report_from_db_row(row)
        for row in rows
    )


def _db_row_from_record(record: Any) -> PaperProbabilitySelectionSummaryHistoryDbRow:
    if isinstance(record, PaperProbabilitySelectionSummaryHistoryDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected selection summary history columns")
    return PaperProbabilitySelectionSummaryHistoryDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        source_report_count=values[3],
        latest_generated_at=values[4],
        latest_age_seconds=values[5],
        latest_queue_count=values[6],
        latest_selected_count=values[7],
        latest_selected_share=values[8],
        average_selected_share=values[9],
        history_status=values[10],
        recommended_next_step=values[11],
        reason_codes_json=_normalize_json_array("reason_codes", values[12]),
        payload_json=_normalize_json_object("payload", values[13]),
        paper_only=values[14],
        report_only=values[15],
        readonly=values[16],
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
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
