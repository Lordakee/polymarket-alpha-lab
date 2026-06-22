"""Optional psycopg adapter for paper probability recommendation queues."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from polymarket_alpha_lab.paper_probability_recommendation_queue_store import (
    insert_paper_probability_recommendation_queue_report,
    load_paper_probability_recommendation_queue_reports,
)


DEFAULT_PAPER_PROBABILITY_RECOMMENDATION_QUEUE_TABLE = (
    "paper_probability_recommendation_queue_reports"
)
_T = TypeVar("_T")


def insert_paper_probability_recommendation_queue_report_with_psycopg(
    dsn: str,
    report: Any,
    *,
    table_name: str = DEFAULT_PAPER_PROBABILITY_RECOMMENDATION_QUEUE_TABLE,
) -> None:
    def insert_with_connection(connection: Any) -> None:
        insert_paper_probability_recommendation_queue_report(
            connection,
            report,
            table_name=table_name,
        )

    _with_owned_connection(dsn, insert_with_connection)


def load_paper_probability_recommendation_queue_reports_with_psycopg(
    dsn: str,
    *,
    source_config_version: str | None = None,
    limit: int | None = None,
    table_name: str = DEFAULT_PAPER_PROBABILITY_RECOMMENDATION_QUEUE_TABLE,
) -> tuple[Any, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_paper_probability_recommendation_queue_reports(
            connection,
            source_config_version=source_config_version,
            limit=limit,
            table_name=table_name,
        ),
    )


def _with_owned_connection(dsn: str, operation: Callable[[Any], _T]) -> _T:
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


def _connect(dsn: str) -> Any:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper probability recommendation "
            "queue psycopg adapter; install the postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper probability recommendation queue database",
        ) from None


def _jsonb_adapter() -> type[Any]:
    try:
        from psycopg.types.json import Jsonb
    except ModuleNotFoundError as exc:
        if exc.name not in ("psycopg", "psycopg.types", "psycopg.types.json"):
            raise
        raise RuntimeError(
            "psycopg is required to use the paper probability recommendation "
            "queue psycopg adapter; install the postgres extra.",
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
    "insert_paper_probability_recommendation_queue_report_with_psycopg",
    "load_paper_probability_recommendation_queue_reports_with_psycopg",
)
