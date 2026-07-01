"""Env-backed read-only load helper for autonomous market scorer reports."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from polymarket_alpha_lab.autonomous_market_scorer_store import (
    load_autonomous_market_scorer_reports as _load_reports,
)
from polymarket_alpha_lab.supabase_autonomous_market_scorer_config import (
    AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR,
    from_autonomous_market_scorer_db_env,
)
from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn


def load_autonomous_market_scorer_reports_from_env(
    *,
    limit: int,
    connect: Callable[[str], Any] | None = None,
    loader: Callable[..., Any] | None = None,
) -> tuple[Any, ...]:
    _require_positive_limit(limit)
    config = from_autonomous_market_scorer_db_env()
    if not config.enabled:
        return ()

    if config.dsn is None:
        raise RuntimeError("autonomous market scorer DB DSN is required")
    using_default_connector = connect is None
    connector = _connect if using_default_connector else connect
    load = _load_reports if loader is None else loader
    try:
        connection = connector(config.dsn)
    except RuntimeError as exc:
        if using_default_connector and str(exc).startswith("psycopg is required"):
            raise
        raise RuntimeError(
            "failed to connect to the autonomous market scorer database",
        ) from None
    except Exception:
        raise RuntimeError(
            "failed to connect to the autonomous market scorer database",
        ) from None

    try:
        try:
            return tuple(
                load(
                    connection,
                    limit=limit,
                    table_name=config.table_name,
                ),
            )
        except Exception:
            raise RuntimeError(
                "failed to load autonomous market scorer reports",
            ) from None
    finally:
        try:
            connection.close()
        except Exception:
            pass


def _connect(dsn: str) -> Any:
    validate_local_postgres_dsn(
        dsn,
        env_var_name=AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR,
    )
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the autonomous market scorer "
            "load helper; install the postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn, autocommit=True)
    except Exception:
        raise RuntimeError(
            "failed to connect to the autonomous market scorer database",
        ) from None


def _require_positive_limit(value: object) -> None:
    if type(value) is not int:
        raise ValueError("limit must be an int")
    if value <= 0:
        raise ValueError("limit must be positive")


__all__ = ("load_autonomous_market_scorer_reports_from_env",)
