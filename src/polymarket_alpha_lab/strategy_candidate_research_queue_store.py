"""DB-API repository for paper strategy candidate research queue reports."""

from __future__ import annotations

import re
from typing import Any, Callable

from polymarket_alpha_lab.strategy_candidate_research_queue_db_row import (
    PaperStrategyCandidateResearchQueueDbRow,
    paper_strategy_candidate_research_queue_report_from_db_row,
    paper_strategy_candidate_research_queue_report_to_db_row,
)
from polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config import (
    SupabaseStrategyCandidateResearchQueueConfig,
)


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_TABLE",
    "insert_paper_strategy_candidate_research_queue_report",
    "load_paper_strategy_candidate_research_queue_reports",
    "paper_strategy_candidate_research_queue_report_sink_from_config",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_TABLE = (
    "paper_strategy_candidate_research_queue_reports"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_config_version",
    "action_status",
    "recommended_next_step",
    "research_status",
    "candidate_count",
    "research_ready_count",
    "watch_count",
    "blocked_count",
    "selected_count",
    "skipped_count",
    "not_selected_count",
    "total_ready_notional",
    "total_selected_notional",
    "total_suggested_notional",
    "top_research_priority_score",
    "average_research_ready_score",
    "source_reason_code_counts",
    "primary_reason_code_counts",
    "reason_codes",
    "rows",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_paper_strategy_candidate_research_queue_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_TABLE,
) -> PaperStrategyCandidateResearchQueueDbRow:
    table_name = _validate_table_name(table_name)
    row = paper_strategy_candidate_research_queue_report_to_db_row(report)
    sql = f"""
        INSERT INTO {table_name} (
            report_sha256,
            generated_at,
            config_version,
            source_config_version,
            action_status,
            recommended_next_step,
            research_status,
            candidate_count,
            research_ready_count,
            watch_count,
            blocked_count,
            selected_count,
            skipped_count,
            not_selected_count,
            total_ready_notional,
            total_selected_notional,
            total_suggested_notional,
            top_research_priority_score,
            average_research_ready_score,
            source_reason_code_counts,
            primary_reason_code_counts,
            reason_codes,
            rows,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """
    params = (
        row.report_sha256,
        row.generated_at,
        row.config_version,
        row.source_config_version,
        row.action_status,
        row.recommended_next_step,
        row.research_status,
        row.candidate_count,
        row.research_ready_count,
        row.watch_count,
        row.blocked_count,
        row.selected_count,
        row.skipped_count,
        row.not_selected_count,
        row.total_ready_notional,
        row.total_selected_notional,
        row.total_suggested_notional,
        row.top_research_priority_score,
        row.average_research_ready_score,
        _source_reason_code_counts_json(row),
        _primary_reason_code_counts_json(row),
        _reason_codes_json(row),
        _rows_json(row),
        _payload_json(row),
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


def load_paper_strategy_candidate_research_queue_reports(
    connection: Any,
    *,
    source_config_version: str | None = None,
    action_status: str | None = None,
    research_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_TABLE,
) -> tuple[Any, ...]:
    table_name = _validate_table_name(table_name)
    if source_config_version is not None:
        _require_canonical_string("source_config_version", source_config_version)
    if action_status is not None:
        _require_canonical_string("action_status", action_status)
    if research_status is not None:
        _require_canonical_string("research_status", research_status)
    if limit is not None:
        _require_positive_int("limit", limit)

    where_parts: list[str] = []
    params: list[Any] = []
    if source_config_version is not None:
        where_parts.append("source_config_version = %s")
        params.append(source_config_version)
    if action_status is not None:
        where_parts.append("action_status = %s")
        params.append(action_status)
    if research_status is not None:
        where_parts.append("research_status = %s")
        params.append(research_status)
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
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        {limit_clause}
        """
    cursor = connection.cursor()
    try:
        cursor.execute(sql, tuple(params))
        records = cursor.fetchall()
    finally:
        cursor.close()
    rows = tuple(_db_row_from_record(record) for record in records)
    return tuple(
        paper_strategy_candidate_research_queue_report_from_db_row(row)
        for row in rows
    )


class _StrategyCandidateResearchQueueReportSink:
    def __init__(
        self,
        *,
        dsn: str,
        table_name: str,
        report_sink: Callable[..., object],
    ) -> None:
        self._dsn = dsn
        self._table_name = table_name
        self._report_sink = report_sink

    def __call__(self, report: Any) -> object:
        try:
            return self._report_sink(
                dsn=self._dsn,
                report=report,
                table_name=self._table_name,
            )
        except Exception as exc:
            raise type(exc)(_sanitize_secret_text(str(exc), self._dsn)) from None

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"dsn=<redacted>, "
            f"table_name={self._table_name!r}"
            ")"
        )


def paper_strategy_candidate_research_queue_report_sink_from_config(
    config: Any,
    *,
    report_sink: Callable[..., object],
) -> Callable[[Any], object] | None:
    if type(config) is not SupabaseStrategyCandidateResearchQueueConfig:
        raise ValueError(
            "config must be a SupabaseStrategyCandidateResearchQueueConfig",
        )
    if config.enabled is False:
        return None
    if config.dsn is None:
        raise ValueError("enabled config must include a DSN")
    return _StrategyCandidateResearchQueueReportSink(
        dsn=config.dsn,
        table_name=config.table_name,
        report_sink=report_sink,
    )


def _sanitize_secret_text(value: str, secret: str) -> str:
    if secret and secret in value:
        value = value.replace(secret, "<redacted>")
    if "postgresql://" in value:
        return "insert failed for <redacted>"
    return value


def _source_reason_code_counts_json(row: Any) -> dict[str, int]:
    if hasattr(row, "source_reason_code_counts_json"):
        return dict(row.source_reason_code_counts_json)
    return _count_map_from_payload_rows(
        _payload_list(row, "source_reason_code_counts"),
        field_name="source_reason_code_counts",
    )


def _primary_reason_code_counts_json(row: Any) -> dict[str, int]:
    if hasattr(row, "primary_reason_code_counts_json"):
        return dict(row.primary_reason_code_counts_json)
    return _count_map_from_payload_rows(
        _payload_list(row, "primary_reason_code_counts"),
        field_name="primary_reason_code_counts",
    )


def _reason_codes_json(row: Any) -> list[str]:
    if hasattr(row, "reason_codes_json"):
        return list(row.reason_codes_json)
    return _string_list_from_payload(_payload_list(row, "reason_codes"))


def _rows_json(row: Any) -> list[dict[str, Any]]:
    if hasattr(row, "rows_json"):
        return list(row.rows_json)
    values = _payload_list(row, "rows")
    if any(type(item) is not dict for item in values):
        raise ValueError("rows must be a JSON array of objects")
    return [dict(item) for item in values]


def _payload_json(row: Any) -> dict[str, Any]:
    payload = getattr(row, "payload_json", None)
    if type(payload) is not dict:
        raise ValueError("row must expose payload_json")
    return dict(payload)


def _payload_list(row: Any, key: str) -> list[Any]:
    payload = _payload_json(row)
    value = payload.get(key)
    if type(value) is not list:
        raise ValueError(f"{key} must be a JSON array")
    return list(value)


def _count_map_from_payload_rows(
    values: list[Any],
    *,
    field_name: str,
) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in values:
        reason_code: Any
        count: Any
        if type(item) is dict:
            reason_code = item.get("reason_code")
            count = item.get("count")
        elif type(item) in (list, tuple) and len(item) == 2:
            reason_code, count = item
        else:
            raise ValueError(f"{field_name} rows must be JSON objects or pairs")
        if type(reason_code) is not str or not reason_code:
            raise ValueError(f"{field_name} reason_code must be a nonblank string")
        if type(count) is not int or count <= 0:
            raise ValueError(f"{field_name} count must be a positive int")
        result[reason_code] = count
    return result


def _string_list_from_payload(values: list[Any]) -> list[str]:
    result: list[str] = []
    for item in values:
        if type(item) is not str:
            raise ValueError("reason_codes must be a JSON array of strings")
        result.append(item)
    return result


def _db_row_from_record(record: Any) -> PaperStrategyCandidateResearchQueueDbRow:
    if isinstance(record, PaperStrategyCandidateResearchQueueDbRow):
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
            "DB row must contain selected strategy candidate research queue columns",
        )
    return PaperStrategyCandidateResearchQueueDbRow(
        report_sha256=values[0],
        generated_at=values[1],
        config_version=values[2],
        source_config_version=values[3],
        action_status=values[4],
        recommended_next_step=values[5],
        research_status=values[6],
        candidate_count=values[7],
        research_ready_count=values[8],
        watch_count=values[9],
        blocked_count=values[10],
        selected_count=values[11],
        skipped_count=values[12],
        not_selected_count=values[13],
        total_ready_notional=values[14],
        total_selected_notional=values[15],
        total_suggested_notional=values[16],
        top_research_priority_score=values[17],
        average_research_ready_score=values[18],
        source_reason_code_counts_json=_normalize_json_object(
            "source_reason_code_counts",
            values[19],
        ),
        primary_reason_code_counts_json=_normalize_json_object(
            "primary_reason_code_counts",
            values[20],
        ),
        reason_codes_json=_normalize_json_array("reason_codes", values[21]),
        rows_json=_normalize_json_array_of_objects("rows", values[22]),
        payload_json=_normalize_json_object("payload", values[23]),
        paper_only=values[24],
        report_only=values[25],
        readonly=values[26],
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _normalize_json_array(field_name: str, value: Any) -> list[Any]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a JSON array")
    return list(value)


def _normalize_json_array_of_objects(
    field_name: str,
    value: Any,
) -> list[dict[str, Any]]:
    values = _normalize_json_array(field_name, value)
    if any(type(item) is not dict for item in values):
        raise ValueError(f"{field_name} must be a JSON array of objects")
    return [dict(item) for item in values]


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
    if any(_IDENTIFIER_PATTERN.fullmatch(part) is None for part in parts):
        raise ValueError(
            "table_name must be a lowercase identifier with optional schema prefix",
        )
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
