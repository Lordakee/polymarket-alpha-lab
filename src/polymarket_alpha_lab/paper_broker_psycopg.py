"""Optional psycopg adapter for paper broker execution record persistence."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import re
from typing import Any, TypeVar

from polymarket_alpha_lab.paper_broker import PaperBrokerExecutionRecord
from polymarket_alpha_lab.paper_broker_db_row import (
    paper_broker_execution_record_to_db_row,
)
from polymarket_alpha_lab.supabase_paper_broker_config import (
    DEFAULT_PAPER_BROKER_DB_TABLE,
    SupabasePaperBrokerConfig,
)


__all__ = (
    "insert_paper_broker_execution_record_from_config",
    "insert_paper_broker_execution_record_with_psycopg",
)


_T = TypeVar("_T")
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")


def insert_paper_broker_execution_record_from_config(
    config: SupabasePaperBrokerConfig,
    record: PaperBrokerExecutionRecord,
    *,
    connect: Callable[[str], Any] | None = None,
    insert_record: Callable[..., _T] | None = None,
) -> _T | None:
    if type(config) is not SupabasePaperBrokerConfig:
        raise ValueError("config must be a SupabasePaperBrokerConfig")
    _require_record(record)
    if config.enabled is False:
        return None
    if config.dsn is None:
        raise ValueError("enabled config must include a DSN")
    if connect is None:
        return insert_paper_broker_execution_record_with_psycopg(
            config.dsn,
            record,
            table_name=config.table_name,
            insert_record=insert_record,
        )
    return _with_raw_owned_connection(
        config.dsn,
        lambda connection: _insert_with_boundary(
            connection,
            record,
            table_name=config.table_name,
            insert_record=insert_record,
        ),
        connect=connect,
    )


def insert_paper_broker_execution_record_with_psycopg(
    dsn: str,
    record: PaperBrokerExecutionRecord,
    *,
    table_name: str = DEFAULT_PAPER_BROKER_DB_TABLE,
    connect: Callable[[str], Any] | None = None,
    insert_record: Callable[..., _T] | None = None,
) -> _T:
    _require_dsn(dsn)
    _require_record(record)
    table_name = _validate_table_name(table_name)
    return _with_psycopg_owned_connection(
        dsn,
        lambda connection: _insert_with_boundary(
            connection,
            record,
            table_name=table_name,
            insert_record=insert_record,
        ),
        connect=connect,
    )


def _insert_with_boundary(
    connection: Any,
    record: PaperBrokerExecutionRecord,
    *,
    table_name: str,
    insert_record: Callable[..., _T] | None,
) -> _T:
    if insert_record is not None:
        return insert_record(connection, record, table_name=table_name)
    return _default_insert_record(connection, record, table_name=table_name)


def _default_insert_record(
    connection: Any,
    record: PaperBrokerExecutionRecord,
    *,
    table_name: str,
) -> Any:
    return _insert_record_generic(connection, record, table_name=table_name)


def _insert_record_generic(
    connection: Any,
    record: PaperBrokerExecutionRecord,
    *,
    table_name: str,
) -> Any:
    table_name = _validate_table_name(table_name)
    row = paper_broker_execution_record_to_db_row(record)
    sql = f"""
        INSERT INTO {table_name} (
            record_sha256,
            generated_at,
            config_version,
            execution_status,
            recommended_next_step,
            source_gate_status,
            source_proposal_count,
            source_proposal_total_notional,
            execution_notional,
            reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (record_sha256) DO NOTHING
        """
    params = (
        row.record_sha256,
        row.generated_at,
        row.config_version,
        row.execution_status,
        row.recommended_next_step,
        row.source_gate_status,
        row.source_proposal_count,
        row.source_proposal_total_notional,
        row.execution_notional,
        row.reason_codes_json,
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


def _with_raw_owned_connection(
    dsn: str,
    operation: Callable[[Any], _T],
    *,
    connect: Callable[[str], Any],
) -> _T:
    return _with_owned_connection(
        dsn,
        operation,
        connection_factory=lambda: _connect_with(dsn, connect),
    )


def _with_psycopg_owned_connection(
    dsn: str,
    operation: Callable[[Any], _T],
    *,
    connect: Callable[[str], Any] | None,
) -> _T:
    jsonb_adapter = _jsonb_adapter()

    def connection_factory() -> _PsycopgJsonConnection:
        if connect is None:
            connection = _connect(dsn)
        else:
            connection = _connect_with(dsn, connect)
        return _PsycopgJsonConnection(connection, jsonb_adapter)

    return _with_owned_connection(dsn, operation, connection_factory=connection_factory)


def _with_owned_connection(
    dsn: str,
    operation: Callable[[Any], _T],
    *,
    connection_factory: Callable[[], Any],
) -> _T:
    connection = connection_factory()
    try:
        result = operation(connection)
        connection.commit()
        return result
    except BaseException as exc:
        try:
            connection.rollback()
        except Exception:
            pass
        if isinstance(exc, Exception):
            _raise_redacted(exc, dsn=dsn)
        raise
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _connect(dsn: str) -> Any:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper broker psycopg adapter; "
            "install the postgres extra.",
        ) from exc
    return _connect_with(dsn, psycopg.connect)


def _connect_with(dsn: str, connect: Callable[[str], Any]) -> Any:
    try:
        return connect(dsn)
    except Exception:
        raise RuntimeError("failed to connect to the paper broker database") from None


def _jsonb_adapter() -> type[Any]:
    try:
        from psycopg.types.json import Jsonb
    except ModuleNotFoundError as exc:
        if exc.name not in ("psycopg", "psycopg.types", "psycopg.types.json"):
            raise
        raise RuntimeError(
            "psycopg is required to use the paper broker psycopg adapter; "
            "install the postgres extra.",
        ) from exc
    return Jsonb


@dataclass(frozen=True)
class _PsycopgJsonConnection:
    connection: Any
    jsonb_adapter: type[Any]

    def cursor(self) -> Any:
        return _PsycopgJsonCursor(self.connection.cursor(), self.jsonb_adapter)

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()

    def close(self) -> None:
        self.connection.close()


@dataclass(frozen=True)
class _PsycopgJsonCursor:
    cursor: Any
    jsonb_adapter: type[Any]

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        return self.cursor.execute(sql, _adapt_json_params(params, self.jsonb_adapter))

    @property
    def rowcount(self) -> int:
        return self.cursor.rowcount

    def fetchall(self) -> Any:
        return self.cursor.fetchall()

    def close(self) -> None:
        self.cursor.close()


def _adapt_json_params(params: tuple[Any, ...], jsonb_adapter: type[Any]) -> tuple[Any, ...]:
    return tuple(
        jsonb_adapter(param) if isinstance(param, (dict, list)) else param
        for param in params
    )


def _require_dsn(value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError("dsn must be a canonical nonblank string")


def _require_record(record: object) -> None:
    if type(record) is not PaperBrokerExecutionRecord:
        raise ValueError("record must be a PaperBrokerExecutionRecord")
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(record, flag_name) is not True:
            raise ValueError(f"{flag_name} must be True for paper broker record")


def _validate_table_name(value: object) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError("table_name must be a simple lowercase identifier")
    return value


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
    if secret and secret in value:
        value = value.replace(secret, "<redacted>")
    if "postgresql://" in value:
        return "paper broker database operation failed for <redacted>"
    return value
