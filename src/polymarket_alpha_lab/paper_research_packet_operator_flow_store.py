"""DB-API repository for paper research packet operator-flow reports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_research_packet_operator_flow_db_row import (
    PaperResearchPacketOperatorFlowDbRow,
    paper_research_packet_operator_flow_report_from_db_row,
    paper_research_packet_operator_flow_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_research_packet_operator_flow import (
        PaperResearchPacketOperatorFlowReport,
    )


__all__ = (
    "DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_REPORTS_TABLE",
    "PaperResearchPacketOperatorFlowInsertResult",
    "insert_paper_research_packet_operator_flow_report",
    "insert_paper_research_packet_operator_flow_report_with_result",
    "load_paper_research_packet_operator_flow_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"
_FLOW_STATUSES = ("pass", "watch", "blocked")
DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_REPORTS_TABLE = (
    "paper_research_packet_operator_flow_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "flow_status",
    "packet_generated_at",
    "packet_config_version",
    "packet_persisted",
    "packet_row_count",
    "included_count",
    "skipped_count",
    "quality_generated_at",
    "quality_config_version",
    "quality_status",
    "quality_persisted",
    "quality_check_count",
    "quality_pass_count",
    "quality_watch_count",
    "quality_blocked_count",
    "history_generated_at",
    "history_config_version",
    "history_status",
    "history_source_report_count",
    "history_latest_quality_status",
    "reason_codes_json",
    "reason_code_count",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperResearchPacketOperatorFlowInsertResult:
    row: PaperResearchPacketOperatorFlowDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperResearchPacketOperatorFlowDbRow:
            raise ValueError("row must be a PaperResearchPacketOperatorFlowDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_research_packet_operator_flow_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_REPORTS_TABLE,
) -> PaperResearchPacketOperatorFlowDbRow:
    return insert_paper_research_packet_operator_flow_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_research_packet_operator_flow_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_REPORTS_TABLE,
) -> PaperResearchPacketOperatorFlowInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_research_packet_operator_flow_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            flow_status,
            packet_generated_at,
            packet_config_version,
            packet_persisted,
            packet_row_count,
            included_count,
            skipped_count,
            quality_generated_at,
            quality_config_version,
            quality_status,
            quality_persisted,
            quality_check_count,
            quality_pass_count,
            quality_watch_count,
            quality_blocked_count,
            history_generated_at,
            history_config_version,
            history_status,
            history_source_report_count,
            history_latest_quality_status,
            reason_codes_json,
            reason_code_count,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.flow_status,
        row.packet_generated_at,
        row.packet_config_version,
        row.packet_persisted,
        row.packet_row_count,
        row.included_count,
        row.skipped_count,
        row.quality_generated_at,
        row.quality_config_version,
        row.quality_status,
        row.quality_persisted,
        row.quality_check_count,
        row.quality_pass_count,
        row.quality_watch_count,
        row.quality_blocked_count,
        row.history_generated_at,
        row.history_config_version,
        row.history_status,
        row.history_source_report_count,
        row.history_latest_quality_status,
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
    except BaseException:
        _close_cursor_preserving_operation_exception(cursor)
        raise
    cursor.close()
    if rowcount not in (0, 1):
        raise ValueError("insert rowcount must be 0 or 1")
    return PaperResearchPacketOperatorFlowInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_research_packet_operator_flow_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    flow_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_REPORTS_TABLE,
) -> tuple["PaperResearchPacketOperatorFlowReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if flow_status is not None:
        _require_flow_status("flow_status", flow_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if flow_status is not None:
        conditions.append("flow_status = %s")
        params.append(flow_status)

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
    except BaseException:
        _close_cursor_preserving_operation_exception(cursor)
        raise
    cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(
        paper_research_packet_operator_flow_report_from_db_row(row) for row in rows
    )


def _close_cursor_preserving_operation_exception(cursor: Any) -> None:
    try:
        cursor.close()
    except BaseException:
        pass


def _db_row_from_record(record: Any) -> PaperResearchPacketOperatorFlowDbRow:
    if isinstance(record, PaperResearchPacketOperatorFlowDbRow):
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
            "DB row must contain selected paper research packet operator-flow columns",
        )
    return PaperResearchPacketOperatorFlowDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        flow_status=values[3],
        packet_generated_at=values[4],
        packet_config_version=values[5],
        packet_persisted=values[6],
        packet_row_count=values[7],
        included_count=values[8],
        skipped_count=values[9],
        quality_generated_at=values[10],
        quality_config_version=values[11],
        quality_status=values[12],
        quality_persisted=values[13],
        quality_check_count=values[14],
        quality_pass_count=values[15],
        quality_watch_count=values[16],
        quality_blocked_count=values[17],
        history_generated_at=values[18],
        history_config_version=values[19],
        history_status=values[20],
        history_source_report_count=values[21],
        history_latest_quality_status=values[22],
        reason_codes_json=_normalize_reason_codes_json("reason_codes", values[23]),
        reason_code_count=values[24],
        payload_json=_normalize_json_object("payload", values[25]),
        paper_only=values[26],
        report_only=values[27],
        readonly=values[28],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


def _normalize_reason_codes_json(field_name: str, value: Any) -> list[str]:
    values = _normalize_json_array(field_name, value)
    for item in values:
        if type(item) is not str:
            raise ValueError(f"{field_name} must contain strings")
    return values


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


def _require_flow_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _FLOW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
