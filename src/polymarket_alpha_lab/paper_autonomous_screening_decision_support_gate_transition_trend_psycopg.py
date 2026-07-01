"""Optional psycopg adapter for paper autonomous screening transition trend reports."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_trend_store import (
    DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_REPORTS_TABLE,
    insert_paper_autonomous_screening_decision_support_gate_transition_trend_report_with_result,
    load_paper_autonomous_screening_decision_support_gate_transition_trend_reports,
)
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn
from polymarket_alpha_lab.supabase_paper_autonomous_screening_decision_support_gate_transition_trend_config import (
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_DB_DSN_ENV_VAR,
)


_T = TypeVar("_T")


def insert_paper_autonomous_screening_decision_support_gate_transition_trend_report_with_psycopg(
    dsn: str,
    report: Any,
    *,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_REPORTS_TABLE
    ),
) -> Any:
    return _with_owned_write_connection(
        dsn,
        lambda connection: (
            insert_paper_autonomous_screening_decision_support_gate_transition_trend_report_with_result(
                connection,
                report,
                table_name=table_name,
            )
        ),
    )


def load_paper_autonomous_screening_decision_support_gate_transition_trend_reports_with_psycopg(
    dsn: str,
    *,
    config_version: str | None = None,
    latest_from_gate_status: str | None = None,
    latest_to_gate_status: str | None = None,
    limit: int | None = None,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_REPORTS_TABLE
    ),
) -> Any:
    return _with_owned_read_connection(
        dsn,
        lambda connection: (
            load_paper_autonomous_screening_decision_support_gate_transition_trend_reports(
                connection,
                config_version=config_version,
                latest_from_gate_status=latest_from_gate_status,
                latest_to_gate_status=latest_to_gate_status,
                limit=limit,
                table_name=table_name,
            )
        ),
    )


def _with_owned_write_connection(dsn: str, operation: Callable[[Any], _T]) -> _T:
    _validate_local_dsn(dsn)
    jsonb_adapter = _jsonb_adapter()
    connection = _PsycopgJsonConnection(_connect(dsn), jsonb_adapter)
    try:
        result = operation(connection)
        connection.commit()
        return result
    except BaseException:
        try:
            connection.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _with_owned_read_connection(dsn: str, operation: Callable[[Any], _T]) -> _T:
    _validate_local_dsn(dsn)
    connection = _connect(dsn, autocommit=True)
    try:
        return operation(connection)
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _connect(dsn: str, **kwargs: Any) -> Any:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous screening "
            "decision-support gate transition trend adapter; install the "
            "postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn, **kwargs)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous screening gate transition "
            "trend database",
        ) from None


def _validate_local_dsn(dsn: str) -> None:
    validate_local_postgres_dsn(
        dsn,
        env_var_name=(
            PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_DB_DSN_ENV_VAR
        ),
    )


def _jsonb_adapter() -> type[Any]:
    try:
        from psycopg.types.json import Jsonb
    except ModuleNotFoundError as exc:
        if exc.name not in ("psycopg", "psycopg.types", "psycopg.types.json"):
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous screening "
            "decision-support gate transition trend adapter; install the "
            "postgres extra.",
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

    def close(self) -> None:
        self.cursor.close()


def _adapt_json_params(params: tuple[Any, ...], jsonb_adapter: type[Any]) -> tuple[Any, ...]:
    return tuple(
        jsonb_adapter(param) if isinstance(param, (dict, list)) else param
        for param in params
    )


__all__ = (
    "insert_paper_autonomous_screening_decision_support_gate_transition_trend_report_with_psycopg",
    "load_paper_autonomous_screening_decision_support_gate_transition_trend_reports_with_psycopg",
)
