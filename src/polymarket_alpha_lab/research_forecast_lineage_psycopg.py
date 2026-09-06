"""Local-only psycopg boundary for research forecast lineage."""

from __future__ import annotations

from typing import Any

from .research_forecast_lineage_db_row import ResearchForecastLineageRow
from .research_forecast_lineage_store import (
    ResearchForecastLineageInsertResult,
    ResearchForecastLineageStore,
)
from .supabase_central_data_config import validate_local_postgres_dsn


def insert_research_forecast_lineage_with_psycopg(
    dsn: str,
    row: ResearchForecastLineageRow,
) -> ResearchForecastLineageInsertResult:
    validate_local_postgres_dsn(dsn)
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError("psycopg is required for lineage persistence") from exc

    connection: Any = None
    try:
        connection = psycopg.connect(dsn)
        result = ResearchForecastLineageStore(connection).insert(row)
        connection.commit()
        return result
    except BaseException:
        if connection is not None:
            try:
                connection.rollback()
            except Exception:
                pass
        raise
    finally:
        if connection is not None:
            connection.close()


__all__ = ("insert_research_forecast_lineage_with_psycopg",)
