"""Optional psycopg adapter for paper allocation metrics evaluation storage."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation_store import (
    DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_REPORTS_TABLE,
    insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report,
    load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_reports,
)
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn
from polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_config import (
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_DSN_ENV_VAR,
)


_T = TypeVar("_T")


def insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report_with_psycopg(
    dsn: str,
    report: Any,
    *,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_REPORTS_TABLE
    ),
) -> Any:
    return _with_owned_write_connection(
        dsn,
        lambda connection: (
            insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
                connection,
                report,
                table_name=table_name,
            )
        ),
    )


def load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_reports_with_psycopg(
    dsn: str,
    *,
    config_version: str | None = None,
    evaluation_status: str | None = None,
    limit: int | None = None,
    table_name: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_REPORTS_TABLE
    ),
) -> tuple[Any, ...]:
    return _with_owned_read_connection(
        dsn,
        lambda connection: (
            load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_reports(
                connection,
                config_version=config_version,
                evaluation_status=evaluation_status,
                limit=limit,
                table_name=table_name,
            )
        ),
    )


def _with_owned_write_connection(dsn: str, operation: Callable[[Any], _T]) -> _T:
    validate_local_postgres_dsn(
        dsn,
        env_var_name=(
            PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_DSN_ENV_VAR
        ),
    )
    jsonb_adapter = _jsonb_adapter()
    connection = _PsycopgJsonConnection(_connect(dsn), jsonb_adapter)
    try:
        result = operation(connection)
        connection.commit()
    except BaseException:
        try:
            connection.rollback()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass
        raise
    connection.close()
    return result


def _with_owned_read_connection(dsn: str, operation: Callable[[Any], _T]) -> _T:
    validate_local_postgres_dsn(
        dsn,
        env_var_name=(
            PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_DB_DSN_ENV_VAR
        ),
    )
    connection = _connect(dsn, autocommit=True)
    try:
        result = operation(connection)
    except BaseException:
        try:
            connection.close()
        except Exception:
            pass
        raise
    connection.close()
    return result


def _connect(dsn: str, **kwargs: Any) -> Any:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous allocation proposal "
            "metrics evaluation psycopg adapter; install the postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn, **kwargs)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper autonomous allocation proposal metrics "
            "evaluation database",
        ) from None


def _jsonb_adapter() -> type[Any]:
    try:
        from psycopg.types.json import Jsonb
    except ModuleNotFoundError as exc:
        if exc.name not in ("psycopg", "psycopg.types", "psycopg.types.json"):
            raise
        raise RuntimeError(
            "psycopg is required to use the paper autonomous allocation proposal "
            "metrics evaluation psycopg adapter; install the postgres extra.",
        ) from exc

    return Jsonb


@dataclass(frozen=True)
class _PsycopgJsonConnection:
    connection: Any
    jsonb_adapter: type[Any]

    def cursor(self) -> Any:
        return _PsycopgJsonCursor(
            self.connection.cursor(),
            self.jsonb_adapter,
        )

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

    def fetchall(self) -> Any:
        return self.cursor.fetchall()

    def close(self) -> None:
        self.cursor.close()


def _adapt_json_params(params: tuple[Any, ...], jsonb_adapter: type[Any]) -> tuple[Any, ...]:
    return tuple(
        jsonb_adapter(param) if isinstance(param, (dict, list)) else param
        for param in params
    )


__all__ = (
    "insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report_with_psycopg",
    "load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_reports_with_psycopg",
)
