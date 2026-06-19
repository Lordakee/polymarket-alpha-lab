"""Optional psycopg adapter for paper trade journal storage."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from polymarket_alpha_lab.paper_trade_journal_store import (
    insert_paper_trade_record,
    load_paper_trade_records,
)


_DEFAULT_TABLE_NAME = "paper_trade_journal_records"
_T = TypeVar("_T")


def insert_paper_trade_record_with_psycopg(
    dsn: str,
    record: Any,
    *,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> Any:
    return _with_owned_connection(
        dsn,
        lambda connection: insert_paper_trade_record(
            connection,
            record,
            table_name=table_name,
        ),
    )


def load_paper_trade_records_with_psycopg(
    dsn: str,
    *,
    condition_id: str | None = None,
    token_id: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_TABLE_NAME,
) -> tuple[Any, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_paper_trade_records(
            connection,
            condition_id=condition_id,
            token_id=token_id,
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
        connection.rollback()
        raise
    finally:
        connection.close()


def _connect(dsn: str) -> Any:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the paper trade journal psycopg adapter; "
            "install the postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn)
    except Exception:
        raise RuntimeError("failed to connect to the paper trade journal database") from None


def _jsonb_adapter() -> type[Any]:
    try:
        from psycopg.types.json import Jsonb
    except ModuleNotFoundError as exc:
        if exc.name not in ("psycopg", "psycopg.types", "psycopg.types.json"):
            raise
        raise RuntimeError(
            "psycopg is required to use the paper trade journal psycopg adapter; "
            "install the postgres extra.",
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
    "insert_paper_trade_record_with_psycopg",
    "load_paper_trade_records_with_psycopg",
)
