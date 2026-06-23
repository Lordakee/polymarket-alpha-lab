"""DB-API repository for paper research packet reports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_research_packet_db_row import (
    PaperResearchPacketDbRow,
    paper_research_packet_report_from_db_row,
    paper_research_packet_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_research_packet import PaperResearchPacketReport


__all__ = (
    "DEFAULT_PAPER_RESEARCH_PACKET_REPORTS_TABLE",
    "PaperResearchPacketInsertResult",
    "insert_paper_research_packet_report",
    "insert_paper_research_packet_report_with_result",
    "load_paper_research_packet_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"
DEFAULT_PAPER_RESEARCH_PACKET_REPORTS_TABLE = "paper_research_packet_reports"
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "input_row_count",
    "packet_row_count",
    "included_count",
    "skipped_count",
    "high_priority_count",
    "medium_priority_count",
    "low_priority_count",
    "packet_rows_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperResearchPacketInsertResult:
    row: PaperResearchPacketDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperResearchPacketDbRow:
            raise ValueError("row must be a PaperResearchPacketDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_research_packet_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_RESEARCH_PACKET_REPORTS_TABLE,
) -> PaperResearchPacketDbRow:
    return insert_paper_research_packet_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_research_packet_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_RESEARCH_PACKET_REPORTS_TABLE,
) -> PaperResearchPacketInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_research_packet_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            input_row_count,
            packet_row_count,
            included_count,
            skipped_count,
            high_priority_count,
            medium_priority_count,
            low_priority_count,
            packet_rows_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.input_row_count,
        row.packet_row_count,
        row.included_count,
        row.skipped_count,
        row.high_priority_count,
        row.medium_priority_count,
        row.low_priority_count,
        row.packet_rows_json,
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
    return PaperResearchPacketInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_research_packet_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_RESEARCH_PACKET_REPORTS_TABLE,
) -> tuple["PaperResearchPacketReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)

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
    return tuple(paper_research_packet_report_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperResearchPacketDbRow:
    if isinstance(record, PaperResearchPacketDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected paper research packet columns")
    return PaperResearchPacketDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        input_row_count=values[3],
        packet_row_count=values[4],
        included_count=values[5],
        skipped_count=values[6],
        high_priority_count=values[7],
        medium_priority_count=values[8],
        low_priority_count=values[9],
        packet_rows_json=_normalize_json_array("packet_rows", values[10]),
        payload_json=_normalize_json_object("payload", values[11]),
        paper_only=values[12],
        report_only=values[13],
        readonly=values[14],
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
    if type(value) is not str:
        raise ValueError(_TABLE_NAME_ERROR)
    parts = value.split(".")
    if not 1 <= len(parts) <= 2:
        raise ValueError(_TABLE_NAME_ERROR)
    for part in parts:
        if len(part.encode("utf-8")) > 63:
            raise ValueError(_TABLE_NAME_ERROR)
        if _IDENTIFIER_PATTERN.fullmatch(part) is None:
            raise ValueError(_TABLE_NAME_ERROR)
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
