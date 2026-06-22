"""Optional psycopg adapter for strategy candidate research queue storage."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from polymarket_alpha_lab.strategy_candidate_research_queue_store import (
    DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_TABLE,
    insert_paper_strategy_candidate_research_queue_report,
)


_T = TypeVar("_T")


def insert_paper_strategy_candidate_research_queue_report_with_psycopg(
    dsn: str,
    report: Any,
    *,
    table_name: str = DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_TABLE,
) -> Any:
    return _with_owned_connection(
        dsn,
        lambda connection: insert_paper_strategy_candidate_research_queue_report(
            connection,
            report,
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
            "psycopg is required to use the strategy candidate research queue "
            "psycopg adapter; install the postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn)
    except Exception:
        raise RuntimeError(
            "failed to connect to the strategy candidate research queue database",
        ) from None


def _jsonb_adapter() -> type[Any]:
    try:
        from psycopg.types.json import Jsonb
    except ModuleNotFoundError as exc:
        if exc.name not in ("psycopg", "psycopg.types", "psycopg.types.json"):
            raise
        raise RuntimeError(
            "psycopg is required to use the strategy candidate research queue "
            "psycopg adapter; install the postgres extra.",
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

    def close(self) -> None:
        self.cursor.close()


def _adapt_json_params(params: tuple[Any, ...], jsonb_adapter: type[Any]) -> tuple[Any, ...]:
    return tuple(
        jsonb_adapter(param) if isinstance(param, (dict, list)) else param
        for param in params
    )


__all__ = ("insert_paper_strategy_candidate_research_queue_report_with_psycopg",)
