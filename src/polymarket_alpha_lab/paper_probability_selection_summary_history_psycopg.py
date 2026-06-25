"""Optional psycopg adapter for paper probability selection summary history persistence."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import re
from typing import Any, TypeVar

from polymarket_alpha_lab.paper_probability_selection_summary_history import (
    PaperProbabilitySelectionSummaryHistoryReport,
)
from polymarket_alpha_lab.paper_probability_selection_summary_history_store import (
    DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_REPORTS_TABLE,
    insert_paper_probability_selection_summary_history_report,
    load_paper_probability_selection_summary_history_reports,
)
from polymarket_alpha_lab.supabase_paper_probability_selection_summary_history_config import (
    SupabasePaperProbabilitySelectionSummaryHistoryConfig,
)


__all__ = (
    "insert_paper_probability_selection_summary_history_report_from_config",
    "insert_paper_probability_selection_summary_history_report_with_psycopg",
    "load_paper_probability_selection_summary_history_reports_from_config",
    "load_paper_probability_selection_summary_history_reports_with_psycopg",
)


_T = TypeVar("_T")
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")


def insert_paper_probability_selection_summary_history_report_from_config(
    config: SupabasePaperProbabilitySelectionSummaryHistoryConfig,
    report: PaperProbabilitySelectionSummaryHistoryReport,
    *,
    connect: Callable[[str], Any] | None = None,
    insert_report: Callable[..., _T] | None = None,
) -> _T | None:
    if type(config) is not SupabasePaperProbabilitySelectionSummaryHistoryConfig:
        raise ValueError(
            "config must be a "
            "SupabasePaperProbabilitySelectionSummaryHistoryConfig",
        )
    _require_report(report)
    if config.enabled is False:
        return None
    if config.dsn is None:
        raise ValueError("enabled config must include a DSN")
    if connect is None:
        return insert_paper_probability_selection_summary_history_report_with_psycopg(
            config.dsn,
            report,
            table_name=config.table_name,
            insert_report=insert_report,
        )
    return _with_raw_owned_connection(
        config.dsn,
        lambda connection: _insert_with_boundary(
            connection,
            report,
            table_name=config.table_name,
            insert_report=insert_report,
        ),
        connect=connect,
    )


def load_paper_probability_selection_summary_history_reports_from_config(
    config: SupabasePaperProbabilitySelectionSummaryHistoryConfig,
    *,
    config_version: str | None = None,
    history_status: str | None = None,
    limit: int | None = None,
    connect: Callable[[str], Any] | None = None,
    load_reports: Callable[..., _T] | None = None,
) -> _T | None:
    if type(config) is not SupabasePaperProbabilitySelectionSummaryHistoryConfig:
        raise ValueError(
            "config must be a "
            "SupabasePaperProbabilitySelectionSummaryHistoryConfig",
        )
    if config.enabled is False:
        return None
    if config.dsn is None:
        raise ValueError("enabled config must include a DSN")
    if connect is None:
        return load_paper_probability_selection_summary_history_reports_with_psycopg(
            config.dsn,
            config_version=config_version,
            history_status=history_status,
            limit=limit,
            table_name=config.table_name,
            load_reports=load_reports,
        )
    return _with_raw_owned_connection(
        config.dsn,
        lambda connection: _load_with_boundary(
            connection,
            config_version=config_version,
            history_status=history_status,
            limit=limit,
            table_name=config.table_name,
            load_reports=load_reports,
        ),
        connect=connect,
    )


def insert_paper_probability_selection_summary_history_report_with_psycopg(
    dsn: str,
    report: PaperProbabilitySelectionSummaryHistoryReport,
    *,
    table_name: str = DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_REPORTS_TABLE,
    connect: Callable[[str], Any] | None = None,
    insert_report: Callable[..., _T] | None = None,
) -> _T:
    _require_dsn(dsn)
    _require_report(report)
    table_name = _validate_table_name(table_name)
    return _with_psycopg_owned_connection(
        dsn,
        lambda connection: _insert_with_boundary(
            connection,
            report,
            table_name=table_name,
            insert_report=insert_report,
        ),
        connect=connect,
    )


def load_paper_probability_selection_summary_history_reports_with_psycopg(
    dsn: str,
    *,
    config_version: str | None = None,
    history_status: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_REPORTS_TABLE,
    connect: Callable[[str], Any] | None = None,
    load_reports: Callable[..., _T] | None = None,
) -> _T:
    _require_dsn(dsn)
    table_name = _validate_table_name(table_name)
    return _with_psycopg_owned_connection(
        dsn,
        lambda connection: _load_with_boundary(
            connection,
            config_version=config_version,
            history_status=history_status,
            limit=limit,
            table_name=table_name,
            load_reports=load_reports,
        ),
        connect=connect,
    )


def _insert_with_boundary(
    connection: Any,
    report: PaperProbabilitySelectionSummaryHistoryReport,
    *,
    table_name: str,
    insert_report: Callable[..., _T] | None,
) -> _T:
    if insert_report is not None:
        return insert_report(connection, report, table_name=table_name)
    return _default_insert_report(connection, report, table_name=table_name)


def _default_insert_report(
    connection: Any,
    report: PaperProbabilitySelectionSummaryHistoryReport,
    *,
    table_name: str,
) -> Any:
    return insert_paper_probability_selection_summary_history_report(
        connection,
        report,
        table_name=table_name,
    )


def _load_with_boundary(
    connection: Any,
    *,
    config_version: str | None,
    history_status: str | None,
    limit: int | None,
    table_name: str,
    load_reports: Callable[..., _T] | None,
) -> _T:
    if load_reports is not None:
        return load_reports(
            connection,
            config_version=config_version,
            history_status=history_status,
            limit=limit,
            table_name=table_name,
        )
    return _default_load_reports(
        connection,
        config_version=config_version,
        history_status=history_status,
        limit=limit,
        table_name=table_name,
    )


def _default_load_reports(
    connection: Any,
    *,
    config_version: str | None,
    history_status: str | None,
    limit: int | None,
    table_name: str,
) -> Any:
    return load_paper_probability_selection_summary_history_reports(
        connection,
        config_version=config_version,
        history_status=history_status,
        limit=limit,
        table_name=table_name,
    )


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
            "psycopg is required to use the paper probability selection summary "
            "history adapter; install the postgres extra.",
        ) from exc
    return _connect_with(dsn, psycopg.connect)


def _connect_with(dsn: str, connect: Callable[[str], Any]) -> Any:
    try:
        return connect(dsn)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper probability selection summary "
            "history database",
        ) from None


def _jsonb_adapter() -> type[Any]:
    try:
        from psycopg.types.json import Jsonb
    except ModuleNotFoundError as exc:
        if exc.name not in ("psycopg", "psycopg.types", "psycopg.types.json"):
            raise
        raise RuntimeError(
            "psycopg is required to use the paper probability selection summary "
            "history adapter; install the postgres extra.",
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


def _require_report(report: object) -> None:
    if type(report) is not PaperProbabilitySelectionSummaryHistoryReport:
        raise ValueError(
            "report must be a PaperProbabilitySelectionSummaryHistoryReport",
        )
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(report, flag_name) is not True:
            raise ValueError(
                f"{flag_name} must be True for selection summary history report",
            )


def _validate_table_name(value: object) -> str:
    if type(value) is not str or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError("table_name must be a simple lowercase identifier")
    return value


def _raise_redacted(exc: Exception, *, dsn: str) -> None:
    message = _redact_dsn_text(str(exc), dsn=dsn)
    if not message.strip():
        message = exc.__class__.__name__
    try:
        redacted_exc = type(exc)(message)
    except Exception:
        redacted_exc = RuntimeError(message)
    raise redacted_exc from None


def _redact_dsn_text(value: str, *, dsn: str) -> str:
    if dsn and dsn in value:
        value = value.replace(dsn, "<redacted>")
    if "postgresql://" in value:
        return "selection summary history database operation failed for <redacted>"
    return value
