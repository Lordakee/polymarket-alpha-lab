"""Optional psycopg adapter for probability selection/scorer agreement trend gates."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_store import (
    DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_REPORTS_TABLE,
    insert_probability_selection_scorer_agreement_trend_gate_report,
    load_probability_selection_scorer_agreement_trend_gate_reports,
)
from polymarket_alpha_lab.supabase_probability_selection_scorer_agreement_trend_gate_config import (
    PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_DB_DSN_ENV_VAR,
)
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn


_T = TypeVar("_T")


def insert_probability_selection_scorer_agreement_trend_gate_report_with_psycopg(
    dsn: str,
    report: Any,
    *,
    table_name: str = (
        DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_REPORTS_TABLE
    ),
) -> Any:
    return _with_owned_connection(
        dsn,
        lambda connection: insert_probability_selection_scorer_agreement_trend_gate_report(
            connection,
            report,
            table_name=table_name,
        ),
    )


def load_probability_selection_scorer_agreement_trend_gate_reports_with_psycopg(
    dsn: str,
    *,
    config_version: str | None = None,
    gate_status: str | None = None,
    limit: int | None = None,
    table_name: str = (
        DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_REPORTS_TABLE
    ),
) -> tuple[Any, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_probability_selection_scorer_agreement_trend_gate_reports(
            connection,
            config_version=config_version,
            gate_status=gate_status,
            limit=limit,
            table_name=table_name,
        ),
    )


def _with_owned_connection(dsn: str, operation: Callable[[Any], _T]) -> _T:
    validate_local_postgres_dsn(
        dsn,
        env_var_name=PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_DB_DSN_ENV_VAR,
    )
    jsonb_adapter = _jsonb_adapter()
    connection = _PsycopgJsonConnection(_connect(dsn), jsonb_adapter)
    try:
        return operation(connection)
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
            "psycopg is required to use the probability selection scorer agreement "
            "trend-gate psycopg adapter; install the postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the probability selection scorer agreement "
            "trend-gate database",
        ) from None


def _jsonb_adapter() -> type[Any]:
    try:
        from psycopg.types.json import Jsonb
    except ModuleNotFoundError as exc:
        if exc.name not in ("psycopg", "psycopg.types", "psycopg.types.json"):
            raise
        raise RuntimeError(
            "psycopg is required to use the probability selection scorer agreement "
            "trend-gate psycopg adapter; install the postgres extra.",
        ) from exc

    return Jsonb


@dataclass(frozen=True)
class _PsycopgJsonConnection:
    connection: Any
    jsonb_adapter: type[Any]

    def cursor(self) -> Any:
        return _PsycopgJsonCursor(self.connection.cursor(), self.jsonb_adapter)

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


__all__ = (
    "insert_probability_selection_scorer_agreement_trend_gate_report_with_psycopg",
    "load_probability_selection_scorer_agreement_trend_gate_reports_with_psycopg",
)
