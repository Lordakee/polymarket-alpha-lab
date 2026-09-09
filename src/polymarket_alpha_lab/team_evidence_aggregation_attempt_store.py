"""DB-API repository for team evaluation attempts (Phase 1, paper-only).

Owns the validated ``team_evaluation_attempts`` identifiers, read queries,
latest-attempt ordering, the public legacy-insert rejection fence, and the one
private transaction-scoped batch insertion path that runs
``insert ... on conflict (tea_id) do nothing`` with the exact Node 4 column
order from ``team_evaluation_attempt_row_parameters``. The module stays
DB-API generic (connection/cursor protocol only, no psycopg import) and never
commits or rolls back: the transaction is owned by the caller.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, NoReturn

from polymarket_alpha_lab.team_evidence_aggregation_db_row import (
    TeamEvaluationAttemptDbRow,
    team_evaluation_attempt_row_parameters,
)

__all__ = (
    "TEAM_EVALUATION_ATTEMPT_COLUMNS",
    "TeamEvaluationAttemptWriteResult",
    "insert_team_evaluation_attempt",
    "load_latest_team_evaluation_attempt",
    "load_team_evaluation_attempt_rows",
)

_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"
_DEFAULT_TABLE_NAME = "team_evaluation_attempts"
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_V1_ID_PREFIXES = ("tea:v1:", "tfr:v1:", "tfe:v1:")
_LEGACY_ID_FIELDS = ("tea_id", "tfr_id", "tfe_id")
_TFR_ID_PREFIX = "tfr:v1:"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_TFR_ID_ERROR = "tfr_id must be an exact tfr:v1: identifier"
_SCOPE_KEY_ERROR = "scope_key must be a lowercase sha256 hex string"

TEAM_EVALUATION_ATTEMPT_COLUMNS: tuple[str, ...] = (
    "tea_id",
    "tfr_id",
    "attempted_at",
    "status",
    "hard_flag",
    "scope_version",
    "scope_key",
    "config_version",
    "config_digest",
    "diagnostic_record_count",
    "arithmetic_record_count",
    "payload_sha256",
    "evaluation_scope_payload",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True, slots=True)
class TeamEvaluationAttemptWriteResult:
    """One immutable atomic-write outcome per input row (Phase 1 flags True)."""

    row: TeamEvaluationAttemptDbRow
    inserted: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.row) is not TeamEvaluationAttemptDbRow:
            raise ValueError("row must be a TeamEvaluationAttemptDbRow")
        if type(self.inserted) is not bool:
            raise ValueError("inserted must be a bool")
        for flag in _HARD_FLAG_NAMES:
            if getattr(self, flag) is not True:
                raise ValueError(f"{flag} must be True")


def insert_team_evaluation_attempt(
    connection: Any,
    row: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> NoReturn:
    """Legacy compatibility fence; structurally unable to write V1 rows.

    Rejects every ``tea:v1:``, ``tfr:v1:``, or ``tfe:v1:`` identifier before
    any cursor activity, never calls the private atomic writer, and performs
    no insert of its own.
    """
    _validate_table_name(table_name)
    _reject_legacy_v1_row(row)
    if not isinstance(row, TeamEvaluationAttemptDbRow):
        raise ValueError("row must be a TeamEvaluationAttemptDbRow")
    raise ValueError(
        "insert_team_evaluation_attempt is a legacy surface; V1 team "
        "evaluation attempts must use the atomic batch writer"
    )


def load_team_evaluation_attempt_rows(
    connection: Any,
    *,
    tfr_id: str | None = None,
    scope_version: str | None = None,
    scope_key: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple[TeamEvaluationAttemptDbRow, ...]:
    """Load attempt rows ordered ``attempted_at DESC, tea_id DESC``."""
    table_name = _validate_table_name(table_name)
    where_clause, params = _attempt_filter_params(
        tfr_id=tfr_id,
        scope_version=scope_version,
        scope_key=scope_key,
        limit=limit,
    )
    sql = _select_attempt_sql(table_name, where_clause, _limit_clause(limit))
    records = _execute_load(connection, sql, tuple(params))
    return tuple(_attempt_row_from_record(record) for record in records)


def load_latest_team_evaluation_attempt(
    connection: Any,
    *,
    tfr_id: str | None = None,
    scope_version: str | None = None,
    scope_key: str | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> TeamEvaluationAttemptDbRow | None:
    """Load the latest attempt within ``tfr_id`` or ``(scope_version, scope_key)``.

    Ordered strictly by ``attempted_at DESC, tea_id DESC`` with ``LIMIT 1``.
    The latest row is returned regardless of status; there is no fallback to
    an older ready row. Returns ``None`` when no row matches.
    """
    table_name = _validate_table_name(table_name)
    where_clause, params = _latest_attempt_filter_params(
        tfr_id=tfr_id,
        scope_version=scope_version,
        scope_key=scope_key,
    )
    sql = _select_attempt_sql(table_name, where_clause, "LIMIT 1")
    records = _execute_load(connection, sql, tuple(params))
    if not records:
        return None
    if len(records) != 1:
        raise ValueError("latest-attempt query must return at most one record")
    return _attempt_row_from_record(records[0])


def _insert_attempt_rows_atomic(
    connection: Any,
    rows: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple[TeamEvaluationAttemptWriteResult, ...]:
    """The only SQL insertion path for team evaluation attempts.

    Validates the table name and every row (through the Node 4 parameter
    codec) before any cursor activity, then executes each insert on one
    cursor of the caller-owned connection and transaction. Maps rowcount 1
    to ``inserted=True`` and rowcount 0 to ``inserted=False``; never commits
    or rolls back.
    """
    table_name = _validate_table_name(table_name)
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list of TeamEvaluationAttemptDbRow")
    if not rows:
        return ()
    parameters = tuple(team_evaluation_attempt_row_parameters(row) for row in rows)
    column_sql = ",\n            ".join(TEAM_EVALUATION_ATTEMPT_COLUMNS)
    placeholders = ", ".join(
        f"%({column})s" for column in TEAM_EVALUATION_ATTEMPT_COLUMNS
    )
    sql = f"""
        INSERT INTO {table_name} (
            {column_sql}
        ) VALUES ({placeholders})
        ON CONFLICT (tea_id) DO NOTHING
        """
    results: list[TeamEvaluationAttemptWriteResult] = []
    cursor = connection.cursor()
    try:
        for row, params in zip(rows, parameters, strict=True):
            cursor.execute(sql, params)
            results.append(
                TeamEvaluationAttemptWriteResult(
                    row=row,
                    inserted=_inserted_from_rowcount(cursor.rowcount),
                )
            )
    except BaseException:
        _close_cursor_after_operation_error(cursor)
        raise
    cursor.close()
    return tuple(results)


def _inserted_from_rowcount(rowcount: Any) -> bool:
    if rowcount == 1:
        return True
    if rowcount == 0:
        return False
    raise ValueError("insert rowcount must be 0 or 1")


def _reject_legacy_v1_row(row: Any) -> None:
    for field_name in _LEGACY_ID_FIELDS:
        _reject_legacy_v1_value(field_name, getattr(row, field_name, None))
    _reject_legacy_v1_payload(getattr(row, "evaluation_scope_payload", None))


def _reject_legacy_v1_value(field_name: str, value: Any) -> None:
    if type(value) is str and value.startswith(_V1_ID_PREFIXES):
        raise ValueError(
            f"{field_name} carries a reserved "
            f"{_v1_prefix_of(value)} identifier; the legacy insert cannot "
            "write V1 rows"
        )


def _reject_legacy_v1_payload(value: Any) -> None:
    if type(value) is str:
        _reject_legacy_v1_value("evaluation_scope_payload", value)
    elif type(value) is list:
        for item in value:
            _reject_legacy_v1_payload(item)
    elif type(value) is dict:
        for item in value.values():
            _reject_legacy_v1_payload(item)


def _v1_prefix_of(value: str) -> str:
    for prefix in _V1_ID_PREFIXES:
        if value.startswith(prefix):
            return prefix
    raise ValueError("value must start with a V1 identifier prefix")


def _attempt_filter_params(
    *,
    tfr_id: str | None,
    scope_version: str | None,
    scope_key: str | None,
    limit: int | None,
) -> tuple[str, list[Any]]:
    if tfr_id is not None:
        _require_tfr_id(tfr_id)
    if scope_version is not None:
        _require_canonical_string("scope_version", scope_version)
    if scope_key is not None:
        _require_scope_key(scope_key)
    if limit is not None:
        _require_positive_int("limit", limit)

    where_parts: list[str] = []
    params: list[Any] = []
    if tfr_id is not None:
        where_parts.append("tfr_id = %s")
        params.append(tfr_id)
    if scope_version is not None:
        where_parts.append("scope_version = %s")
        params.append(scope_version)
    if scope_key is not None:
        where_parts.append("scope_key = %s")
        params.append(scope_key)
    if limit is not None:
        params.append(limit)
    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    return where_clause, params


def _latest_attempt_filter_params(
    *,
    tfr_id: str | None,
    scope_version: str | None,
    scope_key: str | None,
) -> tuple[str, list[Any]]:
    if tfr_id is not None and (scope_version is not None or scope_key is not None):
        raise ValueError(
            "latest-attempt lookup must use either tfr_id or both "
            "scope_version and scope_key, not both modes"
        )
    if tfr_id is None and (scope_version is None or scope_key is None):
        raise ValueError(
            "latest-attempt lookup requires tfr_id or both scope_version "
            "and scope_key"
        )
    if tfr_id is not None:
        _require_tfr_id(tfr_id)
        return "WHERE tfr_id = %s", [tfr_id]
    _require_canonical_string("scope_version", scope_version)
    _require_scope_key(scope_key)
    return (
        "WHERE scope_version = %s AND scope_key = %s",
        [scope_version, scope_key],
    )


def _select_attempt_sql(
    table_name: str,
    where_clause: str,
    limit_clause: str,
) -> str:
    column_sql = ",\n            ".join(TEAM_EVALUATION_ATTEMPT_COLUMNS)
    return f"""
        SELECT
            {column_sql}
        FROM {table_name}
        {where_clause}
        ORDER BY attempted_at DESC, tea_id DESC
        {limit_clause}
        """


def _limit_clause(limit: int | None) -> str:
    if limit is None:
        return ""
    return "LIMIT %s"


def _attempt_row_from_record(record: Any) -> TeamEvaluationAttemptDbRow:
    if isinstance(record, TeamEvaluationAttemptDbRow):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in TEAM_EVALUATION_ATTEMPT_COLUMNS)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in TEAM_EVALUATION_ATTEMPT_COLUMNS)
    else:
        values = tuple(record)
    if len(values) != len(TEAM_EVALUATION_ATTEMPT_COLUMNS):
        raise ValueError("DB record must contain the selected attempt columns")
    return TeamEvaluationAttemptDbRow(
        **dict(zip(TEAM_EVALUATION_ATTEMPT_COLUMNS, values, strict=True))
    )


def _execute_load(
    connection: Any,
    sql: str,
    params: tuple[Any, ...],
) -> tuple[Any, ...]:
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        records = cursor.fetchall()
    except BaseException:
        _close_cursor_after_operation_error(cursor)
        raise
    cursor.close()
    return tuple(records)


def _close_cursor_after_operation_error(cursor: Any) -> None:
    try:
        cursor.close()
    except BaseException:
        pass


def _validate_table_name(value: str) -> str:
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


def _require_tfr_id(value: object) -> None:
    if type(value) is not str or not value.startswith(_TFR_ID_PREFIX):
        raise ValueError(_TFR_ID_ERROR)
    if _SHA256_PATTERN.fullmatch(value[len(_TFR_ID_PREFIX):]) is None:
        raise ValueError(_TFR_ID_ERROR)


def _require_scope_key(value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(_SCOPE_KEY_ERROR)


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
