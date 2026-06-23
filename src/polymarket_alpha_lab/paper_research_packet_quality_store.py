"""DB-API repository for paper research packet quality reports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_research_packet_quality_db_row import (
    PaperResearchPacketQualityDbRow,
    paper_research_packet_quality_report_from_db_row,
    paper_research_packet_quality_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_research_packet_quality import (
        PaperResearchPacketQualityReport,
    )


__all__ = (
    "DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_REPORTS_TABLE",
    "PaperResearchPacketQualityInsertResult",
    "insert_paper_research_packet_quality_report",
    "insert_paper_research_packet_quality_report_with_result",
    "load_paper_research_packet_quality_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"
_QUALITY_STATUSES = ("pass", "watch", "blocked")
DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_REPORTS_TABLE = (
    "paper_research_packet_quality_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_generated_at",
    "source_config_version",
    "input_row_count",
    "packet_row_count",
    "included_count",
    "skipped_count",
    "high_priority_count",
    "medium_priority_count",
    "low_priority_count",
    "source_age_seconds",
    "included_share",
    "skipped_share",
    "check_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "quality_status",
    "check_rows_json",
    "reason_code_counts_json",
    "reason_codes_json",
    "reason_code_count",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperResearchPacketQualityInsertResult:
    row: PaperResearchPacketQualityDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperResearchPacketQualityDbRow:
            raise ValueError("row must be a PaperResearchPacketQualityDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_research_packet_quality_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_REPORTS_TABLE,
) -> PaperResearchPacketQualityDbRow:
    return insert_paper_research_packet_quality_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_research_packet_quality_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_REPORTS_TABLE,
) -> PaperResearchPacketQualityInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_research_packet_quality_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            source_generated_at,
            source_config_version,
            input_row_count,
            packet_row_count,
            included_count,
            skipped_count,
            high_priority_count,
            medium_priority_count,
            low_priority_count,
            source_age_seconds,
            included_share,
            skipped_share,
            check_count,
            pass_count,
            watch_count,
            blocked_count,
            quality_status,
            check_rows_json,
            reason_code_counts_json,
            reason_codes_json,
            reason_code_count,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.source_generated_at,
        row.source_config_version,
        row.input_row_count,
        row.packet_row_count,
        row.included_count,
        row.skipped_count,
        row.high_priority_count,
        row.medium_priority_count,
        row.low_priority_count,
        row.source_age_seconds,
        row.included_share,
        row.skipped_share,
        row.check_count,
        row.pass_count,
        row.watch_count,
        row.blocked_count,
        row.quality_status,
        row.check_rows_json,
        row.reason_code_counts_json,
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
    return PaperResearchPacketQualityInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_research_packet_quality_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    quality_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_REPORTS_TABLE,
) -> tuple["PaperResearchPacketQualityReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if quality_status is not None:
        _require_quality_status("quality_status", quality_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if quality_status is not None:
        conditions.append("quality_status = %s")
        params.append(quality_status)

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
        paper_research_packet_quality_report_from_db_row(row) for row in rows
    )


def _db_row_from_record(record: Any) -> PaperResearchPacketQualityDbRow:
    if isinstance(record, PaperResearchPacketQualityDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected paper research packet quality columns")
    return PaperResearchPacketQualityDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        source_generated_at=values[3],
        source_config_version=values[4],
        input_row_count=values[5],
        packet_row_count=values[6],
        included_count=values[7],
        skipped_count=values[8],
        high_priority_count=values[9],
        medium_priority_count=values[10],
        low_priority_count=values[11],
        source_age_seconds=values[12],
        included_share=_normalize_optional_decimal("included_share", values[13]),
        skipped_share=_normalize_optional_decimal("skipped_share", values[14]),
        check_count=values[15],
        pass_count=values[16],
        watch_count=values[17],
        blocked_count=values[18],
        quality_status=values[19],
        check_rows_json=_normalize_json_array("check_rows", values[20]),
        reason_code_counts_json=_normalize_json_array("reason_code_counts", values[21]),
        reason_codes_json=_normalize_reason_codes_json("reason_codes", values[22]),
        reason_code_count=values[23],
        payload_json=_normalize_json_object("payload", values[24]),
        paper_only=values[25],
        report_only=values[26],
        readonly=values[27],
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


def _normalize_optional_decimal(field_name: str, value: Any) -> Decimal | None:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(Decimal("0.000001"))
    if quantized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    if quantized > Decimal("1"):
        raise ValueError(f"{field_name} must be at most 1")
    return quantized


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


def _require_quality_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
