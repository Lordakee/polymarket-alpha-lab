"""Optional psycopg adapter for action-gated queue decision-support trends."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_store import (
    DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE,
    DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE,
    insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows,
    load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows,
)


__all__ = (
    "insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg",
    "load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg",
)


_T = TypeVar("_T")


def insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
    dsn: str,
    trend_report: Any,
    snapshot_pairs: Any,
    *,
    reports_table_name: str = DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE,
    sources_table_name: str = DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE,
) -> Any:
    return _with_owned_connection(
        dsn,
        lambda connection: insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows(
            connection,
            trend_report,
            snapshot_pairs,
            reports_table_name=reports_table_name,
            sources_table_name=sources_table_name,
        ),
    )


def load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
    dsn: str,
    *,
    latest_risk_status: str | None = None,
    limit: int | None = None,
    reports_table_name: str = DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE,
    sources_table_name: str = DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE,
) -> tuple[Any, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows(
            connection,
            latest_risk_status=latest_risk_status,
            limit=limit,
            reports_table_name=reports_table_name,
            sources_table_name=sources_table_name,
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
            "psycopg is required to use the action-gated queue decision-support "
            "trend psycopg adapter; install the postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn)
    except Exception:
        raise RuntimeError(
            "failed to connect to the action-gated queue decision-support trend database",
        ) from None


def _jsonb_adapter() -> type[Any]:
    try:
        from psycopg.types.json import Jsonb
    except ModuleNotFoundError as exc:
        if exc.name not in ("psycopg", "psycopg.types", "psycopg.types.json"):
            raise
        raise RuntimeError(
            "psycopg is required to use the action-gated queue decision-support "
            "trend psycopg adapter; install the postgres extra.",
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
