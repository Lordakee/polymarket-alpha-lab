"""Concrete DB-API store for internal central evidence tables."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
import re
from typing import Any, TypeVar

from .central_data_db_row import NormalizedObservationRow, RawEventRow


RAW_TABLE = "central_data_internal.central_data_raw_response_events"
NORMALIZED_TABLE = "central_data_internal.central_data_normalized_observations"
AUDIT_TABLE = "central_data_internal.central_data_raw_retention_audit"
PURGE_FUNCTION = "central_data_internal.purge_expired_central_data_raw_response_events"
RETENTION_JOB_NAME = "central_data_raw_retention_15m"
RETENTION_SCHEDULE = "*/15 * * * *"
RETENTION_COMMAND = "select central_data_internal.purge_expired_central_data_raw_response_events();"

_T = TypeVar("_T")
_RAW_COLUMNS = (
    "raw_event_id", "source_id", "source_family", "endpoint_url", "official_source",
    "request_url", "final_url", "retrieval_time", "status_code", "content_type",
    "safe_headers", "failure_status", "raw_body", "body_length", "raw_payload_sha256",
    "expires_at", "paper_only", "report_only", "readonly",
)
_NORMALIZED_COLUMNS = (
    "normalized_observation_id", "raw_event_id", "source_id", "source_family",
    "endpoint_url", "official_source", "observation_time", "retrieval_time",
    "raw_payload_sha256", "parser_version", "parse_state", "freshness_state",
    "failure_status", "value_state", "reason_codes", "typed_value", "paper_only",
    "report_only", "readonly",
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class CentralDataStoreError(RuntimeError):
    """Fixed, redacted persistence failure."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)

    def __repr__(self) -> str:
        return f"CentralDataStoreError(code={self.code!r})"


@dataclass(frozen=True)
class CentralDataInsertResult:
    identity: str
    status: str

    @property
    def inserted(self) -> bool:
        return self.status == "inserted"


def _raise_db_error() -> None:
    raise CentralDataStoreError("central_data_database_operation_failed") from None


def _with_cursor(connection: Any, operation: Callable[[Any], _T]) -> _T:
    try:
        cursor = connection.cursor()
    except Exception:
        _raise_db_error()
    try:
        result = operation(cursor)
    except CentralDataStoreError:
        try:
            cursor.close()
        except Exception:
            pass
        raise
    except BaseException as exc:
        try:
            cursor.close()
        except BaseException:
            pass
        if isinstance(exc, Exception):
            _raise_db_error()
        raise
    try:
        cursor.close()
    except Exception:
        _raise_db_error()
    return result


def _positive_limit(value: object, *, maximum: int = 5000) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"limit must be an int from 1 to {maximum}")
    return value


def _canonical_source_id(value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError("source_id must be a canonical nonblank string")
    return value


def _raw_event_id(value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError("raw_event_id must be a lowercase SHA-256 digest")
    return value


def _record_values(record: Any, columns: tuple[str, ...]) -> tuple[Any, ...]:
    if isinstance(record, Mapping):
        return tuple(record[column] for column in columns)
    if isinstance(record, (tuple, list)) and len(record) == len(columns):
        return tuple(record)
    return tuple(getattr(record, column) for column in columns)


def _same_values(actual: tuple[Any, ...], expected: tuple[Any, ...]) -> bool:
    def normalize(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {key: normalize(item) for key, item in value.items()}
        if isinstance(value, list):
            return tuple(normalize(item) for item in value)
        if isinstance(value, tuple):
            return tuple(normalize(item) for item in value)
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value.astimezone(UTC)
        return value

    return normalize(actual) == normalize(expected)


class CentralDataStore:
    """Transaction-neutral operations against an injected DB-API connection."""

    def __init__(self, connection: Any) -> None:
        if connection is None or not hasattr(connection, "cursor"):
            raise ValueError("connection must provide cursor()")
        self.connection = connection

    def health_check_retention(self) -> bool:
        sql = f"""
            SELECT (
                (SELECT count(*) = 1
                   FROM cron.job
                  WHERE jobname = %s)
                AND (SELECT count(*) = 1
                   FROM cron.job
                  WHERE jobname = %s
                    AND schedule = %s
                    AND command = %s
                    AND database = 'postgres'
                    AND username = 'postgres'
                    AND active IS TRUE)
                AND NOT EXISTS (
                    SELECT 1
                      FROM cron.job AS j
                      JOIN cron.job_run_details AS r ON r.jobid = j.jobid
                     WHERE j.jobname = %s
                       AND (r.status <> 'succeeded'
                            OR r.start_time >= statement_timestamp() - interval '1 hour'
                               AND r.end_time IS NULL)
                       AND r.start_time >= statement_timestamp() - interval '1 hour'
                )
                AND EXISTS (
                    SELECT 1
                      FROM {AUDIT_TABLE}
                     WHERE audit_kind = 'purge_run'
                       AND job_name = %s
                       AND run_status = 'ok'
                       AND backlog_remaining IS FALSE
                       AND run_completed_at >= statement_timestamp() - interval '1 hour'
                )
                AND NOT EXISTS (
                    SELECT 1 FROM {RAW_TABLE}
                     WHERE expires_at <= statement_timestamp()
                )
            ) AS retention_ready
        """

        def operation(cursor: Any) -> bool:
            cursor.execute(
                sql,
                (
                    RETENTION_JOB_NAME,
                    RETENTION_JOB_NAME,
                    RETENTION_SCHEDULE,
                    RETENTION_COMMAND,
                    RETENTION_JOB_NAME,
                    RETENTION_JOB_NAME,
                ),
            )
            record = cursor.fetchone()
            if record is None:
                return False
            if isinstance(record, Mapping):
                return record.get("retention_ready") is True
            return record[0] is True

        return _with_cursor(self.connection, operation)

    def insert_raw_event(
        self,
        row: RawEventRow | str,
        raw_event: Mapping[str, Any] | None = None,
    ) -> CentralDataInsertResult:
        if not isinstance(row, RawEventRow):
            if type(row) is not str or raw_event is None:
                raise ValueError("row must be a RawEventRow")
            values = dict(raw_event)
            values.setdefault("raw_event_id", row)
            row = RawEventRow(**values)
        if not self.health_check_retention():
            raise CentralDataStoreError("central_data_retention_not_ready")

        columns = ", ".join(_RAW_COLUMNS)
        placeholders = ", ".join("%s" for _column in _RAW_COLUMNS)
        insert_sql = f"""
            INSERT INTO {RAW_TABLE} ({columns})
            VALUES ({placeholders})
            ON CONFLICT (raw_event_id) DO NOTHING
            RETURNING raw_event_id
        """
        select_sql = f"SELECT {columns} FROM {RAW_TABLE} WHERE raw_event_id = %s"
        expected = row.as_parameters()

        def operation(cursor: Any) -> CentralDataInsertResult:
            cursor.execute(insert_sql, expected)
            returned = cursor.fetchone()
            if returned is not None:
                return CentralDataInsertResult(row.raw_event_id, "inserted")
            cursor.execute(select_sql, (row.raw_event_id,))
            existing = cursor.fetchone()
            if existing is None or not _same_values(_record_values(existing, _RAW_COLUMNS), expected):
                raise CentralDataStoreError("identity_collision")
            return CentralDataInsertResult(row.raw_event_id, "already_present")

        return _with_cursor(self.connection, operation)

    def insert_normalized_observation(
        self,
        row: NormalizedObservationRow | Mapping[str, Any],
    ) -> CentralDataInsertResult:
        if not isinstance(row, NormalizedObservationRow):
            row = NormalizedObservationRow(**dict(row))
        lock_sql = f"""
            SELECT raw_event_id, source_id, source_family, endpoint_url, official_source,
                   retrieval_time, raw_payload_sha256
              FROM {RAW_TABLE}
             WHERE raw_event_id = %s
               AND expires_at > statement_timestamp()
             FOR KEY SHARE
        """
        columns = ", ".join(_NORMALIZED_COLUMNS)
        placeholders = ", ".join("%s" for _column in _NORMALIZED_COLUMNS)
        insert_sql = f"""
            INSERT INTO {NORMALIZED_TABLE} ({columns})
            VALUES ({placeholders})
            ON CONFLICT (normalized_observation_id) DO NOTHING
            RETURNING normalized_observation_id
        """
        select_sql = (
            f"SELECT {columns} FROM {NORMALIZED_TABLE} "
            "WHERE normalized_observation_id = %s"
        )
        expected = row.as_parameters()
        expected_raw = (
            row.raw_event_id,
            row.source_id,
            row.source_family,
            row.endpoint_url,
            row.official_source,
            row.retrieval_time,
            row.raw_payload_sha256,
        )

        def operation(cursor: Any) -> CentralDataInsertResult:
            cursor.execute(lock_sql, (row.raw_event_id,))
            raw_record = cursor.fetchone()
            if raw_record is None:
                raise CentralDataStoreError("raw_event_unavailable")
            raw_values = _record_values(
                raw_record,
                (
                    "raw_event_id", "source_id", "source_family", "endpoint_url",
                    "official_source", "retrieval_time", "raw_payload_sha256",
                ),
            )
            if not _same_values(raw_values, expected_raw):
                raise CentralDataStoreError("raw_event_provenance_mismatch")
            cursor.execute(insert_sql, expected)
            returned = cursor.fetchone()
            if returned is not None:
                return CentralDataInsertResult(row.normalized_observation_id, "inserted")
            cursor.execute(select_sql, (row.normalized_observation_id,))
            existing = cursor.fetchone()
            if existing is None or not _same_values(
                _record_values(existing, _NORMALIZED_COLUMNS), expected
            ):
                raise CentralDataStoreError("identity_collision")
            return CentralDataInsertResult(row.normalized_observation_id, "already_present")

        return _with_cursor(self.connection, operation)

    def get_unexpired_raw(
        self,
        *,
        source_id: str | None = None,
        limit: int = 100,
    ) -> tuple[RawEventRow, ...]:
        limit = _positive_limit(limit)
        conditions = ["expires_at > statement_timestamp()"]
        params: list[Any] = []
        if source_id is not None:
            conditions.append("source_id = %s")
            params.append(_canonical_source_id(source_id))
        params.append(limit)
        columns = ", ".join(_RAW_COLUMNS)
        sql = f"""
            SELECT {columns} FROM {RAW_TABLE}
             WHERE {' AND '.join(conditions)}
             ORDER BY retrieval_time DESC, raw_event_id DESC
             LIMIT %s
        """

        def operation(cursor: Any) -> tuple[RawEventRow, ...]:
            cursor.execute(sql, tuple(params))
            records = cursor.fetchall()
            return tuple(RawEventRow(**dict(zip(_RAW_COLUMNS, _record_values(record, _RAW_COLUMNS)))) for record in records)

        return _with_cursor(self.connection, operation)

    def get_normalized_observations(
        self,
        *,
        source_id: str | None = None,
        raw_event_id: str | None = None,
        limit: int = 100,
    ) -> tuple[NormalizedObservationRow, ...]:
        limit = _positive_limit(limit)
        conditions: list[str] = []
        params: list[Any] = []
        if source_id is not None:
            conditions.append("source_id = %s")
            params.append(_canonical_source_id(source_id))
        if raw_event_id is not None:
            conditions.append("raw_event_id = %s")
            params.append(_raw_event_id(raw_event_id))
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)
        columns = ", ".join(_NORMALIZED_COLUMNS)
        sql = f"""
            SELECT {columns} FROM {NORMALIZED_TABLE}
            {where}
            ORDER BY observation_time DESC, normalized_observation_id DESC
            LIMIT %s
        """

        def operation(cursor: Any) -> tuple[NormalizedObservationRow, ...]:
            cursor.execute(sql, tuple(params))
            records = cursor.fetchall()
            rows = []
            for record in records:
                values = dict(zip(_NORMALIZED_COLUMNS, _record_values(record, _NORMALIZED_COLUMNS)))
                values["reason_codes"] = tuple(values["reason_codes"])
                rows.append(NormalizedObservationRow(**values))
            return tuple(rows)

        return _with_cursor(self.connection, operation)

    def load_retention_audit(self, *, limit: int = 100) -> tuple[dict[str, Any], ...]:
        limit = _positive_limit(limit)
        sql = f"""
            SELECT audit_id, audit_kind, job_name, cutoff_time, run_started_at,
                   run_completed_at, deleted_count, backlog_remaining, run_status,
                   source_id, source_family, official_source, raw_event_id,
                   raw_payload_sha256, original_body_length, expires_at, deleted_at,
                   reason_code, paper_only, report_only, readonly
              FROM {AUDIT_TABLE}
             ORDER BY inserted_at DESC, audit_id DESC
             LIMIT %s
        """
        columns = (
            "audit_id", "audit_kind", "job_name", "cutoff_time", "run_started_at",
            "run_completed_at", "deleted_count", "backlog_remaining", "run_status",
            "source_id", "source_family", "official_source", "raw_event_id",
            "raw_payload_sha256", "original_body_length", "expires_at", "deleted_at",
            "reason_code", "paper_only", "report_only", "readonly",
        )

        def operation(cursor: Any) -> tuple[dict[str, Any], ...]:
            cursor.execute(sql, (limit,))
            return tuple(dict(zip(columns, _record_values(record, columns))) for record in cursor.fetchall())

        return _with_cursor(self.connection, operation)

    def purge_expired_raw(self, cutoff: datetime, *, batch_limit: int = 500) -> int:
        if type(cutoff) is not datetime:
            raise ValueError("cutoff must be a datetime")
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=UTC)
        else:
            cutoff = cutoff.astimezone(UTC)
        batch_limit = _positive_limit(batch_limit)
        sql = f"SELECT {PURGE_FUNCTION}(%s, %s)"

        def operation(cursor: Any) -> int:
            cursor.execute(sql, (cutoff, batch_limit))
            record = cursor.fetchone()
            if record is None:
                _raise_db_error()
            value = next(iter(record.values())) if isinstance(record, Mapping) else record[0]
            if type(value) is not int or value < 0:
                _raise_db_error()
            return value

        return _with_cursor(self.connection, operation)


__all__ = (
    "AUDIT_TABLE",
    "CentralDataInsertResult",
    "CentralDataStore",
    "CentralDataStoreError",
    "NORMALIZED_TABLE",
    "PURGE_FUNCTION",
    "RAW_TABLE",
    "RETENTION_COMMAND",
    "RETENTION_JOB_NAME",
    "RETENTION_SCHEDULE",
)
