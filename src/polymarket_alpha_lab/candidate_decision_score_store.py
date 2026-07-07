"""Injected-connection store helper for candidate decision score reports."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, InvalidOperation
import re
from typing import Any


DEFAULT_CANDIDATE_DECISION_SCORE_REPORT_TABLE = "candidate_decision_score_reports"

_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_TABLE_NAME_ERROR = (
    "table_name must be a lowercase identifier with optional schema prefix"
)
_SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "candidate_id",
    "market_id",
    "normalized_market_question",
    "primary_team_id",
    "secondary_team_ids",
    "selected_side",
    "forecast_probability",
    "executable_price",
    "gross_edge",
    "estimated_cost_drag",
    "net_edge",
    "cost_score",
    "liquidity_score",
    "evidence_score",
    "resolution_score",
    "team_memory_score",
    "team_memory_policy",
    "decision_score",
    "action",
    "hard_blocker_codes",
    "reason_codes",
    "source_report_refs",
    "derived_validation_digest",
    "boundary_statement",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_FIELDS_BY_COLUMN = {
    "report_sha256": "report_sha256",
    "generated_at": "generated_at",
    "config_version": "config_version",
    "candidate_id": "candidate_id",
    "market_id": "market_id",
    "normalized_market_question": "normalized_market_question",
    "primary_team_id": "primary_team_id",
    "secondary_team_ids": "secondary_team_ids_json",
    "selected_side": "selected_side",
    "forecast_probability": "forecast_probability",
    "executable_price": "executable_price",
    "gross_edge": "gross_edge",
    "estimated_cost_drag": "estimated_cost_drag",
    "net_edge": "net_edge",
    "cost_score": "cost_score",
    "liquidity_score": "liquidity_score",
    "evidence_score": "evidence_score",
    "resolution_score": "resolution_score",
    "team_memory_score": "team_memory_score",
    "team_memory_policy": "team_memory_policy",
    "decision_score": "decision_score",
    "action": "action",
    "hard_blocker_codes": "hard_blocker_codes_json",
    "reason_codes": "reason_codes_json",
    "source_report_refs": "source_report_refs_json",
    "derived_validation_digest": "derived_validation_digest",
    "boundary_statement": "boundary_statement",
    "payload": "payload_json",
    "paper_only": "paper_only",
    "report_only": "report_only",
    "readonly": "readonly",
}
_PAYLOAD_KEYS_BY_ROW_FIELD = {
    "normalized_market_question": "normalized_market_question",
    "secondary_team_ids_json": "secondary_team_ids",
    "selected_side": "selected_side",
    "forecast_probability": "forecast_probability",
    "executable_price": "executable_price",
    "gross_edge": "gross_edge",
    "estimated_cost_drag": "estimated_cost_drag",
    "net_edge": "net_edge",
    "cost_score": "cost_score",
    "liquidity_score": "liquidity_score",
    "evidence_score": "evidence_score",
    "resolution_score": "resolution_score",
    "team_memory_score": "team_memory_score",
    "team_memory_policy": "team_memory_policy",
    "hard_blocker_codes_json": "hard_blocker_codes",
    "derived_validation_digest": "derived_validation_digest",
    "boundary_statement": "boundary_statement",
}
_DECIMAL_ROW_FIELDS = frozenset(
    (
        "forecast_probability",
        "executable_price",
        "gross_edge",
        "estimated_cost_drag",
        "net_edge",
        "cost_score",
        "liquidity_score",
        "evidence_score",
        "resolution_score",
        "team_memory_score",
        "decision_score",
    ),
)
_POSTGRES_DSN_PATTERN = re.compile(r"postgres(?:ql)?://\S+", re.IGNORECASE)


def insert_candidate_decision_score_report(
    connection: Any,
    report: Any,
    *,
    table_name: str = DEFAULT_CANDIDATE_DECISION_SCORE_REPORT_TABLE,
) -> Any:
    table_name = _validate_table_name(table_name)
    row = _report_to_db_row(report)
    columns = ",\n            ".join(_SELECT_COLUMNS)
    placeholders = ", ".join("%s" for _column in _SELECT_COLUMNS)
    sql = f"""
        INSERT INTO {table_name} (
            {columns}
        ) VALUES ({placeholders})
        ON CONFLICT(report_sha256) DO NOTHING
        """
    params = _row_values(row)
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    except BaseException:
        _close_cursor_preserving_operation_exception(cursor)
        raise
    cursor.close()
    return row


def load_candidate_decision_score_reports(
    connection: Any,
    *,
    action: str | None = None,
    primary_team_id: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_CANDIDATE_DECISION_SCORE_REPORT_TABLE,
) -> tuple[Any, ...]:
    table_name = _validate_table_name(table_name)
    if action is not None:
        _require_canonical_string("action", action)
    if primary_team_id is not None:
        _require_canonical_string("primary_team_id", primary_team_id)
    if limit is not None:
        _require_positive_int("limit", limit)

    conditions: list[str] = []
    params: list[Any] = []
    if action is not None:
        conditions.append("action = %s")
        params.append(action)
    if primary_team_id is not None:
        conditions.append("primary_team_id = %s")
        params.append(primary_team_id)

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
    return tuple(_report_from_db_row(row) for row in rows)


def candidate_decision_score_report_sink_from_config(
    config: Any,
    *,
    connection_factory: Callable[[str], Any] | None = None,
) -> Callable[[Any], Any] | None:
    if getattr(config, "enabled") is not True:
        return None
    dsn = getattr(config, "dsn", None)
    if type(dsn) is not str or not dsn:
        raise ValueError("dsn must be set when candidate decision score DB is enabled")
    if connection_factory is None:
        raise ValueError(
            "connection_factory is required when candidate decision score DB is enabled",
        )
    table_name = _validate_table_name(getattr(config, "table", None))
    return _CandidateDecisionScoreReportSink(
        dsn=dsn,
        table_name=table_name,
        connection_factory=connection_factory,
    )


@dataclass(frozen=True, repr=False)
class _CandidateDecisionScoreReportSink:
    dsn: str
    table_name: str
    connection_factory: Callable[[str], Any]

    def __call__(self, report: Any) -> Any:
        try:
            connection = self.connection_factory(self.dsn)
            return insert_candidate_decision_score_report(
                connection,
                report,
                table_name=self.table_name,
            )
        except Exception as exc:
            _raise_redacted(exc, dsn=self.dsn)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            "dsn=<redacted>, "
            f"table_name={self.table_name!r}"
            ")"
        )


def _report_to_db_row(report: Any) -> Any:
    from polymarket_alpha_lab.candidate_decision_score_db_row import (
        candidate_decision_score_report_to_db_row,
    )

    return candidate_decision_score_report_to_db_row(report)


def _report_from_db_row(row: Any) -> Any:
    from polymarket_alpha_lab.candidate_decision_score_db_row import (
        candidate_decision_score_report_from_db_row,
    )

    return candidate_decision_score_report_from_db_row(row)


def _db_row_class() -> type[Any]:
    from polymarket_alpha_lab.candidate_decision_score_db_row import (
        CandidateDecisionScoreDbRow,
    )

    return CandidateDecisionScoreDbRow


def _row_values(row: Any) -> tuple[Any, ...]:
    return tuple(
        _row_value(row, _ROW_FIELDS_BY_COLUMN[column])
        for column in _SELECT_COLUMNS
    )


def _row_value(row: Any, row_field: str) -> Any:
    if hasattr(row, row_field):
        return getattr(row, row_field)
    payload_json = getattr(row, "payload_json", None)
    if not isinstance(payload_json, Mapping):
        raise ValueError(f"{row_field} must be present on candidate decision score DB row")
    if row_field not in _PAYLOAD_KEYS_BY_ROW_FIELD:
        raise ValueError(f"{row_field} must be present on candidate decision score DB row")
    value = payload_json.get(_PAYLOAD_KEYS_BY_ROW_FIELD[row_field])
    if row_field in _DECIMAL_ROW_FIELDS:
        return _decimal_from_payload(row_field, value)
    if row_field.endswith("_json") and type(value) is list:
        return list(value)
    return value


def _db_row_from_record(record: Any) -> Any:
    values_by_column = _record_values_by_column(record)
    row_kwargs = {
        row_field: values_by_column[column]
        for column, row_field in _ROW_FIELDS_BY_COLUMN.items()
    }
    row_class = _db_row_class()
    accepted_fields = _dataclass_field_names(row_class)
    if accepted_fields is not None:
        row_kwargs = {
            field_name: value
            for field_name, value in row_kwargs.items()
            if field_name in accepted_fields
        }
    return row_class(**row_kwargs)


def _record_values_by_column(record: Any) -> dict[str, Any]:
    if isinstance(record, Mapping):
        source = record
        return {column: _record_mapping_value(source, column) for column in _SELECT_COLUMNS}
    if hasattr(record, "_asdict"):
        source = record._asdict()
        return {column: _record_mapping_value(source, column) for column in _SELECT_COLUMNS}
    if isinstance(record, tuple):
        if len(record) != len(_SELECT_COLUMNS):
            raise ValueError("candidate decision score DB record has wrong column count")
        return dict(zip(_SELECT_COLUMNS, record, strict=True))
    return {column: _record_object_value(record, column) for column in _SELECT_COLUMNS}


def _record_mapping_value(source: Mapping[str, Any], column: str) -> Any:
    if column in source:
        return source[column]
    row_field = _ROW_FIELDS_BY_COLUMN[column]
    if row_field in source:
        return source[row_field]
    raise ValueError(f"{column} must be present in candidate decision score DB record")


def _record_object_value(source: Any, column: str) -> Any:
    if hasattr(source, column):
        return getattr(source, column)
    row_field = _ROW_FIELDS_BY_COLUMN[column]
    if hasattr(source, row_field):
        return getattr(source, row_field)
    return _row_value(source, row_field)


def _dataclass_field_names(row_class: type[Any]) -> frozenset[str] | None:
    if not is_dataclass(row_class):
        return None
    return frozenset(field.name for field in fields(row_class))


def _decimal_from_payload(field_name: str, value: Any) -> Decimal | None:
    if value is None:
        return None
    if type(value) is Decimal:
        return value
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _close_cursor_preserving_operation_exception(cursor: Any) -> None:
    try:
        cursor.close()
    except BaseException:
        pass


def _validate_table_name(value: Any) -> str:
    if type(value) is not str:
        raise ValueError(_TABLE_NAME_ERROR)
    parts = value.split(".")
    if len(parts) not in (1, 2):
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
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer")


def _raise_redacted(exc: Exception, *, dsn: str) -> None:
    message = _redact_secret_text(str(exc), secret=dsn)
    if not message.strip():
        message = exc.__class__.__name__
    try:
        redacted_exc = type(exc)(message)
    except Exception:
        redacted_exc = RuntimeError(message)
    raise redacted_exc from None


def _redact_secret_text(value: str, *, secret: str) -> str:
    redacted = value.replace(secret, "<redacted>")
    return _POSTGRES_DSN_PATTERN.sub("<redacted>", redacted)


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_SCORE_REPORT_TABLE",
    "insert_candidate_decision_score_report",
    "load_candidate_decision_score_reports",
    "candidate_decision_score_report_sink_from_config",
)
