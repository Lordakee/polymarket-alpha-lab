"""Lazy psycopg boundary for local central evidence persistence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, TypeVar

from .central_data_db_row import NormalizedObservationRow, RawEventRow
from .central_data_store import CentralDataInsertResult, CentralDataStore, CentralDataStoreError
from .supabase_central_data_config import (
    from_central_data_env,
    validate_local_postgres_dsn,
)


_T = TypeVar("_T")


class CentralDataPsycopgError(RuntimeError):
    """Fixed, redacted adapter failure."""

    def __init__(self, code: str = "central_data_persistence_failed") -> None:
        self.code = code
        super().__init__(code)


def _driver_parts() -> tuple[Any, type[Any]]:
    try:
        import psycopg
        from psycopg.types.json import Jsonb
    except (ImportError, ModuleNotFoundError):
        raise CentralDataPsycopgError("central_data_psycopg_unavailable") from None
    return psycopg, Jsonb


@dataclass(frozen=True)
class _JsonCursor:
    cursor: Any
    jsonb: type[Any]

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        adapted = tuple(
            self.jsonb(value) if isinstance(value, (dict, list)) else value
            for value in params
        )
        return self.cursor.execute(sql, adapted)

    def fetchone(self) -> Any:
        return self.cursor.fetchone()

    def fetchall(self) -> Any:
        return self.cursor.fetchall()

    @property
    def rowcount(self) -> int:
        return self.cursor.rowcount

    def close(self) -> None:
        self.cursor.close()


@dataclass(frozen=True)
class _JsonConnection:
    connection: Any
    jsonb: type[Any]

    def cursor(self) -> _JsonCursor:
        return _JsonCursor(self.connection.cursor(), self.jsonb)

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()

    def close(self) -> None:
        self.connection.close()


def _connect(dsn: str, *, readonly: bool) -> _JsonConnection:
    validate_local_postgres_dsn(dsn)
    psycopg, jsonb = _driver_parts()
    connection = None
    try:
        connection = psycopg.connect(dsn)
        if readonly:
            connection.autocommit = True
        return _JsonConnection(connection, jsonb)
    except Exception:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
        raise CentralDataPsycopgError("central_data_connection_failed") from None


def _write(dsn: str, operation: Callable[[CentralDataStore], _T]) -> _T:
    validate_local_postgres_dsn(dsn)
    connection = _connect(dsn, readonly=False)
    original: BaseException | None = None
    try:
        result = operation(CentralDataStore(connection))
        connection.commit()
        return result
    except BaseException as exc:
        original = exc
        try:
            connection.rollback()
        except BaseException:
            pass
        if isinstance(exc, (CentralDataStoreError, CentralDataPsycopgError, ValueError)):
            raise exc from None
        if isinstance(exc, Exception):
            raise CentralDataPsycopgError() from None
        raise
    finally:
        try:
            connection.close()
        except Exception:
            if original is None:
                raise CentralDataPsycopgError("central_data_connection_close_failed") from None


def _read(dsn: str, operation: Callable[[CentralDataStore], _T]) -> _T:
    validate_local_postgres_dsn(dsn)
    connection = _connect(dsn, readonly=True)
    original: BaseException | None = None
    try:
        return operation(CentralDataStore(connection))
    except BaseException as exc:
        original = exc
        if isinstance(exc, (CentralDataStoreError, CentralDataPsycopgError, ValueError)):
            raise exc from None
        if isinstance(exc, Exception):
            raise CentralDataPsycopgError() from None
        raise
    finally:
        try:
            connection.close()
        except Exception:
            if original is None:
                raise CentralDataPsycopgError("central_data_connection_close_failed") from None


@dataclass(frozen=True, repr=False)
class CentralDataPsycopg:
    _dsn: str = field(repr=False)

    def __post_init__(self) -> None:
        validate_local_postgres_dsn(self._dsn)

    def __repr__(self) -> str:
        return "CentralDataPsycopg(dsn=<redacted>)"

    @classmethod
    def from_config(cls) -> "CentralDataPsycopg | None":
        config = from_central_data_env()
        if not config.enabled:
            return None
        if config.dsn is None:
            raise CentralDataPsycopgError("central_data_dsn_missing")
        return cls(config.dsn)

    def insert_raw_event(self, row: RawEventRow) -> CentralDataInsertResult:
        return _write(self._dsn, lambda store: store.insert_raw_event(row))

    def insert_normalized_observation(self, row: NormalizedObservationRow) -> CentralDataInsertResult:
        return _write(self._dsn, lambda store: store.insert_normalized_observation(row))

    def purge_expired_raw(self, cutoff: datetime, *, batch_limit: int = 500) -> int:
        return _write(
            self._dsn,
            lambda store: store.purge_expired_raw(cutoff, batch_limit=batch_limit),
        )

    def get_unexpired_raw(self, *, source_id: str | None = None, limit: int = 100) -> tuple[RawEventRow, ...]:
        return _read(
            self._dsn,
            lambda store: store.get_unexpired_raw(source_id=source_id, limit=limit),
        )

    def get_normalized_observations(
        self,
        *,
        source_id: str | None = None,
        raw_event_id: str | None = None,
        limit: int = 100,
    ) -> tuple[NormalizedObservationRow, ...]:
        return _read(
            self._dsn,
            lambda store: store.get_normalized_observations(
                source_id=source_id,
                raw_event_id=raw_event_id,
                limit=limit,
            ),
        )


def insert_raw_event_with_psycopg(dsn: str, row: RawEventRow) -> CentralDataInsertResult:
    return CentralDataPsycopg(dsn).insert_raw_event(row)


def insert_normalized_observation_with_psycopg(
    dsn: str,
    row: NormalizedObservationRow,
) -> CentralDataInsertResult:
    return CentralDataPsycopg(dsn).insert_normalized_observation(row)


def purge_expired_raw_with_psycopg(
    dsn: str,
    cutoff: datetime,
    *,
    batch_limit: int = 500,
) -> int:
    return CentralDataPsycopg(dsn).purge_expired_raw(cutoff, batch_limit=batch_limit)


__all__ = (
    "CentralDataPsycopg",
    "CentralDataPsycopgError",
    "insert_normalized_observation_with_psycopg",
    "insert_raw_event_with_psycopg",
    "purge_expired_raw_with_psycopg",
)
