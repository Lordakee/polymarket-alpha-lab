"""Optional psycopg adapter for team research assignment report storage."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib import import_module
from typing import Any, TypeVar

from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn
from polymarket_alpha_lab.supabase_team_research_assignment_config import (
    TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR,
    from_team_research_assignment_db_env,
)
from polymarket_alpha_lab.team_research_assignment import TeamResearchAssignmentReport


__all__ = (
    "insert_team_research_assignment_report_from_env",
    "load_team_research_assignment_reports",
    "load_team_research_assignment_reports_from_env",
)


_T = TypeVar("_T")
_STORE_MODULE_NAME = "polymarket_alpha_lab.team_research_assignment_store"
_REDACTED_DB_OPERATION_MESSAGE = (
    "team research assignment database operation failed for <redacted>"
)
_SENSITIVE_DB_ERROR_MARKERS = (
    "account",
    "api_key",
    "api-secret",
    "api_secret",
    "auth",
    "credential",
    "hash",
    "market question",
    "market slug",
    "market_question",
    "market_slug",
    "order",
    "payload",
    "payload_json",
    "postgres://",
    "postgresql://",
    "private-key",
    "private_key",
    "question",
    "report_sha256",
    "secret",
    "sha256",
    "trade",
    "wallet",
)


def insert_team_research_assignment_report_from_env(
    report: TeamResearchAssignmentReport,
    *,
    env: Mapping[str, str] | None = None,
    connect: Callable[[str], Any] | None = None,
    insert_report: Callable[..., _T] | None = None,
) -> _T | None:
    config = from_team_research_assignment_db_env(env)
    _require_report(report)
    if config.enabled is False:
        return None
    dsn = config.dsn
    if dsn is None:
        raise ValueError("enabled config must include a DSN")
    store_insert = (
        _default_store_function("insert_team_research_assignment_report_with_result")
        if insert_report is None
        else insert_report
    )
    return _with_connection(
        dsn,
        lambda connection: store_insert(
            connection,
            report,
            table_name=config.table_name,
        ),
        connect=connect,
        table_name=config.table_name,
    )


def load_team_research_assignment_reports_from_env(
    *,
    env: Mapping[str, str] | None = None,
    assignment_status: str | None = None,
    config_version: str | None = None,
    limit: int | None = None,
    connect: Callable[[str], Any] | None = None,
    load_reports: Callable[..., _T] | None = None,
) -> _T | None:
    config = from_team_research_assignment_db_env(env)
    if config.enabled is False:
        return None
    dsn = config.dsn
    if dsn is None:
        raise ValueError("enabled config must include a DSN")
    store_load = (
        _default_store_function("load_team_research_assignment_reports")
        if load_reports is None
        else load_reports
    )
    return _with_connection(
        dsn,
        lambda connection: store_load(
            connection,
            assignment_status=assignment_status,
            config_version=config_version,
            limit=limit,
            table_name=config.table_name,
        ),
        connect=connect,
        table_name=config.table_name,
    )


def load_team_research_assignment_reports(
    *,
    dsn: str,
    table_name: str,
    assignment_status: str | None = None,
    config_version: str | None = None,
    limit: int | None = None,
    connect: Callable[[str], Any] | None = None,
    load_reports: Callable[..., _T] | None = None,
) -> _T:
    store_load = (
        _default_store_function("load_team_research_assignment_reports")
        if load_reports is None
        else load_reports
    )
    return _with_connection(
        dsn,
        lambda connection: store_load(
            connection,
            assignment_status=assignment_status,
            config_version=config_version,
            limit=limit,
            table_name=table_name,
        ),
        connect=connect,
        table_name=table_name,
    )


def _with_connection(
    dsn: str,
    operation: Callable[[Any], _T],
    *,
    connect: Callable[[str], Any] | None,
    table_name: str,
) -> _T:
    if connect is None:
        return _with_psycopg_owned_connection(dsn, operation, table_name=table_name)
    return _with_raw_owned_connection(
        dsn,
        operation,
        connect=connect,
        table_name=table_name,
    )


def _with_raw_owned_connection(
    dsn: str,
    operation: Callable[[Any], _T],
    *,
    connect: Callable[[str], Any],
    table_name: str,
) -> _T:
    return _with_owned_connection(
        dsn,
        operation,
        connection_factory=lambda: _connect_with(connect, dsn),
        table_name=table_name,
    )


def _with_psycopg_owned_connection(
    dsn: str,
    operation: Callable[[Any], _T],
    *,
    table_name: str,
) -> _T:
    validate_local_postgres_dsn(
        dsn,
        env_var_name=TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR,
    )
    jsonb_adapter = _jsonb_adapter()
    return _with_owned_connection(
        dsn,
        operation,
        connection_factory=lambda: _PsycopgJsonConnection(
            _connect(dsn),
            jsonb_adapter,
        ),
        table_name=table_name,
    )


def _with_owned_connection(
    dsn: str,
    operation: Callable[[Any], _T],
    *,
    connection_factory: Callable[[], Any],
    table_name: str,
) -> _T:
    validate_local_postgres_dsn(
        dsn,
        env_var_name=TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR,
    )
    connection = connection_factory()
    try:
        result = operation(connection)
        connection.commit()
    except BaseException as exc:
        try:
            connection.rollback()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass
        if isinstance(exc, Exception):
            _raise_redacted(exc, dsn=dsn, table_name=table_name)
        raise
    try:
        connection.close()
    except Exception as exc:
        _raise_redacted(exc, dsn=dsn, table_name=table_name)
    return result


def _connect(dsn: str) -> Any:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the team research assignment psycopg "
            "adapter; install the postgres extra.",
        ) from exc
    return _connect_with(psycopg.connect, dsn)


def _connect_with(connect: Callable[[str], Any], dsn: str) -> Any:
    try:
        return connect(dsn)
    except Exception:
        raise RuntimeError(
            "failed to connect to the team research assignment database",
        ) from None


def _jsonb_adapter() -> type[Any]:
    try:
        from psycopg.types.json import Jsonb
    except ModuleNotFoundError as exc:
        if exc.name not in ("psycopg", "psycopg.types", "psycopg.types.json"):
            raise
        raise RuntimeError(
            "psycopg is required to use the team research assignment psycopg "
            "adapter; install the postgres extra.",
        ) from exc
    return Jsonb


def _default_store_function(name: str) -> Callable[..., Any]:
    try:
        store_module = import_module(_STORE_MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == _STORE_MODULE_NAME:
            raise RuntimeError(
                "team research assignment store functions are unavailable",
            ) from exc
        raise
    store_function = getattr(store_module, name, None)
    if store_function is None:
        raise RuntimeError("team research assignment store functions are unavailable")
    return store_function


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


def _require_report(report: object) -> None:
    if type(report) is not TeamResearchAssignmentReport:
        raise ValueError("report must be a TeamResearchAssignmentReport")
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(report, flag_name) is not True:
            raise ValueError(f"{flag_name} must be True for team research assignment report")


def _raise_redacted(exc: Exception, *, dsn: str, table_name: str) -> None:
    message = _redact_secret_text(str(exc), secret=dsn, table_name=table_name)
    if not message.strip():
        message = exc.__class__.__name__
    try:
        redacted_exc = type(exc)(message)
    except Exception:
        redacted_exc = RuntimeError(message)
    raise redacted_exc from None


def _redact_secret_text(value: str, *, secret: str, table_name: str) -> str:
    original = value
    if secret and secret in value:
        value = value.replace(secret, "<redacted>")
    if table_name and table_name in value:
        value = value.replace(table_name, "<redacted-table>")
    lowered_original = original.lower()
    lowered_value = value.lower()
    host = _dsn_host(secret) if secret else ""
    if host and host.lower() in lowered_value:
        return _REDACTED_DB_OPERATION_MESSAGE
    if any(marker in lowered_original for marker in _SENSITIVE_DB_ERROR_MARKERS):
        return _REDACTED_DB_OPERATION_MESSAGE
    return value


def _dsn_host(dsn: str) -> str:
    marker = "://"
    if marker in dsn:
        after_scheme = dsn.split(marker, 1)[1]
        authority = after_scheme.split("/", 1)[0]
        host_port = authority.rsplit("@", 1)[-1]
        if host_port.startswith("["):
            return host_port.split("]", 1)[0].lstrip("[")
        return host_port.split(":", 1)[0]
    for part in dsn.split():
        if part.startswith("host="):
            return part.split("=", 1)[1]
    return ""
