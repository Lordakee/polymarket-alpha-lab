"""DB-API repository for paper autonomous readiness digest reports."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.paper_autonomous_readiness_digest import DIGEST_STATUSES
from polymarket_alpha_lab.paper_autonomous_readiness_digest_db_row import (
    PaperAutonomousReadinessDigestDbRow,
    paper_autonomous_readiness_digest_report_from_db_row,
    paper_autonomous_readiness_digest_report_to_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.paper_autonomous_readiness_digest import (
        PaperAutonomousReadinessDigestReport,
    )


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_REPORTS_TABLE",
    "PaperAutonomousReadinessDigestInsertResult",
    "insert_paper_autonomous_readiness_digest_report",
    "insert_paper_autonomous_readiness_digest_report_with_result",
    "load_paper_autonomous_readiness_digest_reports",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_TABLE_NAME_ERROR = "table_name must be a simple lowercase identifier"
DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_REPORTS_TABLE = (
    "paper_autonomous_readiness_digest_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "digest_status",
    "recommended_next_review_action",
    "evidence_json",
    "source_config_versions_json",
    "reason_code_counts_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class PaperAutonomousReadinessDigestInsertResult:
    row: PaperAutonomousReadinessDigestDbRow
    inserted: bool

    def __post_init__(self) -> None:
        if type(self.row) is not PaperAutonomousReadinessDigestDbRow:
            raise ValueError("row must be a PaperAutonomousReadinessDigestDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")


def insert_paper_autonomous_readiness_digest_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_REPORTS_TABLE,
) -> PaperAutonomousReadinessDigestDbRow:
    return insert_paper_autonomous_readiness_digest_report_with_result(
        connection,
        report,
        table_name=table_name,
    ).row


def insert_paper_autonomous_readiness_digest_report_with_result(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_REPORTS_TABLE,
) -> PaperAutonomousReadinessDigestInsertResult:
    table_name = _validate_table_name(table_name)
    row = paper_autonomous_readiness_digest_report_to_db_row(report)
    columns = ",\n            ".join(_SELECT_COLUMNS)
    placeholders = ", ".join("%s" for _ in _SELECT_COLUMNS)
    sql = f"""
        INSERT INTO {table_name} (
            {columns}
        ) VALUES ({placeholders})
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = tuple(getattr(row, column) for column in _SELECT_COLUMNS)
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
    return PaperAutonomousReadinessDigestInsertResult(
        row=row,
        inserted=rowcount == 1,
    )


def load_paper_autonomous_readiness_digest_reports(
    connection: Any,
    *,
    config_version: str | None = None,
    digest_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_REPORTS_TABLE,
) -> tuple["PaperAutonomousReadinessDigestReport", ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if digest_status is not None:
        _require_digest_status("digest_status", digest_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if config_version is not None:
        conditions.append("config_version = %s")
        params.append(config_version)
    if digest_status is not None:
        conditions.append("digest_status = %s")
        params.append(digest_status)

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
        paper_autonomous_readiness_digest_report_from_db_row(row) for row in rows
    )


def _db_row_from_record(record: Any) -> PaperAutonomousReadinessDigestDbRow:
    if isinstance(record, PaperAutonomousReadinessDigestDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected readiness digest columns")
    return PaperAutonomousReadinessDigestDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        digest_status=values[3],
        recommended_next_review_action=values[4],
        evidence_json=_normalize_json_object_array("evidence_json", values[5]),
        source_config_versions_json=_normalize_json_array(
            "source_config_versions_json",
            values[6],
        ),
        reason_code_counts_json=_normalize_json_object_array(
            "reason_code_counts_json",
            values[7],
        ),
        reason_codes_json=_normalize_json_array("reason_codes_json", values[8]),
        payload_json=_normalize_json_object("payload_json", values[9]),
        paper_only=values[10],
        report_only=values[11],
        readonly=values[12],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_object_array(field_name: str, value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized = list(value)
    for item in normalized:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
    return [dict(item) for item in normalized]


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError(_TABLE_NAME_ERROR)
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_digest_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
