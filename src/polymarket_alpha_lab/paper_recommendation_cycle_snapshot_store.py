"""DB-API repository for paper recommendation cycle snapshots."""

from __future__ import annotations

import re
from typing import Any

from polymarket_alpha_lab.paper_recommendation_cycle_snapshot_db_row import (
    PaperRecommendationCycleSnapshotDbRow,
    paper_recommendation_cycle_snapshot_from_db_row,
    paper_recommendation_cycle_snapshot_to_db_row,
)


__all__ = (
    "insert_paper_recommendation_cycle_snapshot",
    "load_paper_recommendation_cycle_snapshots",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_DEFAULT_TABLE_NAME = "paper_recommendation_cycle_snapshots"
_SELECT_COLUMNS = (
    "snapshot_sha256",
    "generated_at",
    "config_version",
    "final_status",
    "stage_counts",
    "artifact_counts",
    "reason_codes",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_recommendation_cycle_snapshot(
    connection: Any,
    report: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> PaperRecommendationCycleSnapshotDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_recommendation_cycle_snapshot_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            snapshot_sha256,
            generated_at,
            config_version,
            final_status,
            stage_counts,
            artifact_counts,
            reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (snapshot_sha256) DO NOTHING
        """
    params = (
        row.snapshot_sha256,
        row.generated_at,
        row.config_version,
        row.final_status,
        row.stage_counts_json,
        row.artifact_counts_json,
        list(row.reason_codes),
        row.payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    finally:
        cursor.close()
    return row


def load_paper_recommendation_cycle_snapshots(
    connection: Any,
    *,
    config_version: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple[Any, ...]:
    table_name = _validate_table_name(table_name)
    if config_version is not None:
        _require_canonical_string("config_version", config_version)
    if limit is not None:
        _require_positive_int("limit", limit)

    where_clause = ""
    params: list[Any] = []
    if config_version is not None:
        where_clause = "WHERE config_version = %s"
        params.append(config_version)

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
        ORDER BY generated_at DESC
        {limit_clause}
        """
    cursor = connection.cursor()
    try:
        cursor.execute(sql, tuple(params))
        records = cursor.fetchall()
    finally:
        cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(paper_recommendation_cycle_snapshot_from_db_row(row) for row in rows)


def _db_row_from_record(record: Any) -> PaperRecommendationCycleSnapshotDbRow:
    if isinstance(record, PaperRecommendationCycleSnapshotDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in _SELECT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in _SELECT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(_SELECT_COLUMNS):
        raise ValueError("DB row must contain selected snapshot columns")
    stage_counts = _normalize_json_object("stage_counts", values[4])
    artifact_counts = _normalize_json_object("artifact_counts", values[5])
    return PaperRecommendationCycleSnapshotDbRow(
        snapshot_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        final_status=values[3],
        stage_count=stage_counts["stage_count"],
        artifact_count=artifact_counts["artifact_count"],
        blocked_artifact_count=artifact_counts["blocked_count"],
        watch_artifact_count=artifact_counts["watch_count"],
        reason_codes=values[6],
        stage_counts_json=stage_counts,
        artifact_counts_json=artifact_counts,
        payload_json=_normalize_json_object("payload", values[7]),
        paper_only=values[8],
        report_only=values[9],
        readonly=values[10],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError("table_name must be a simple lowercase identifier")
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
