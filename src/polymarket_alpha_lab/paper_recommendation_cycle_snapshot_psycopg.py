"""Optional psycopg adapter for paper recommendation cycle snapshot storage."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from polymarket_alpha_lab.paper_recommendation_cycle_snapshot_store import (
    insert_paper_recommendation_cycle_snapshot,
    load_paper_recommendation_cycle_snapshots,
)


_DEFAULT_TABLE_NAME = "paper_recommendation_cycle_snapshots"
_T = TypeVar("_T")


def insert_paper_recommendation_cycle_snapshot_with_psycopg(
    dsn: str,
    report: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> Any:
    return _with_owned_connection(
        dsn,
        lambda connection: insert_paper_recommendation_cycle_snapshot(
            connection,
            report,
            table_name=table_name,
        ),
    )


def load_paper_recommendation_cycle_snapshots_with_psycopg(
    dsn: str,
    *,
    config_version: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple[Any, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_paper_recommendation_cycle_snapshots(
            connection,
            config_version=config_version,
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
            "psycopg is required to use the paper recommendation cycle snapshot "
            "psycopg adapter; install the postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn)
    except Exception:
        raise RuntimeError(
            "failed to connect to the paper recommendation cycle snapshot database",
        ) from None


def _jsonb_adapter() -> type[Any]:
    try:
        from psycopg.types.json import Jsonb
    except ModuleNotFoundError as exc:
        if exc.name not in ("psycopg", "psycopg.types", "psycopg.types.json"):
            raise
        raise RuntimeError(
            "psycopg is required to use the paper recommendation cycle snapshot "
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
    "insert_paper_recommendation_cycle_snapshot_with_psycopg",
    "load_paper_recommendation_cycle_snapshots_with_psycopg",
)
