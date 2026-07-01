"""Optional psycopg adapter for team forecast storage."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypeVar

from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn
from polymarket_alpha_lab.supabase_team_forecast_config import (
    TEAM_FORECAST_DB_DSN_ENV_VAR,
)
from polymarket_alpha_lab.team_forecast_db_row import TeamForecastDbRow
from polymarket_alpha_lab.team_forecast_db_row import TeamForecastEvidenceDbRow
from polymarket_alpha_lab.team_forecast_db_row import TeamForecastOutcome
from polymarket_alpha_lab.team_forecast_db_row import TeamForecastOutcomeDbRow
from polymarket_alpha_lab.team_forecast_db_row import TeamMarketRouteDbRow
from polymarket_alpha_lab.team_forecast_db_row import team_forecast_evidence_to_db_row
from polymarket_alpha_lab.team_forecast_db_row import team_forecast_outcome_to_db_row
from polymarket_alpha_lab.team_forecast_db_row import team_forecast_to_db_row
from polymarket_alpha_lab.team_forecast_db_row import team_route_to_db_row
from polymarket_alpha_lab.team_forecast_packet import TeamForecastEvidencePacket
from polymarket_alpha_lab.team_forecast_packet import TeamForecastPacket
from polymarket_alpha_lab.team_market_router import TeamMarketRouteReport


try:
    from polymarket_alpha_lab.team_forecast_store import (
        insert_team_market_route,
        insert_team_forecast,
        insert_team_forecast_evidence,
        insert_team_forecast_outcome,
        load_team_forecast_evidence,
        load_team_forecast_evidence_rows,
        load_team_forecast_outcomes,
        load_team_forecast_outcome_rows,
        load_team_forecast_rows,
        load_team_forecasts,
    )
except ModuleNotFoundError as exc:
    if exc.name != "polymarket_alpha_lab.team_forecast_store":
        raise

    def insert_team_market_route(
        connection: Any,
        row: TeamMarketRouteDbRow,
        *,
        table_name: str,
    ) -> TeamMarketRouteDbRow:
        raise RuntimeError("team forecast store module is required")

    def insert_team_forecast(
        connection: Any,
        row: TeamForecastDbRow,
        *,
        table_name: str,
    ) -> TeamForecastDbRow:
        raise RuntimeError("team forecast store module is required")

    def insert_team_forecast_evidence(
        connection: Any,
        row: TeamForecastEvidenceDbRow,
        *,
        table_name: str,
    ) -> TeamForecastEvidenceDbRow:
        raise RuntimeError("team forecast store module is required")

    def insert_team_forecast_outcome(
        connection: Any,
        row: TeamForecastOutcomeDbRow,
        *,
        table_name: str,
    ) -> TeamForecastOutcomeDbRow:
        raise RuntimeError("team forecast store module is required")

    def load_team_forecasts(
        connection: Any,
        *,
        team_id: str | None = None,
        market_slug: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[Any, ...]:
        raise RuntimeError("team forecast store module is required")

    def load_team_forecast_rows(
        connection: Any,
        *,
        team_id: str | None = None,
        market_slug: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[Any, ...]:
        raise RuntimeError("team forecast store module is required")

    def load_team_forecast_evidence(
        connection: Any,
        *,
        forecast_id: str | None = None,
        team_id: str | None = None,
        market_slug: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[Any, ...]:
        raise RuntimeError("team forecast store module is required")

    def load_team_forecast_evidence_rows(
        connection: Any,
        *,
        forecast_id: str | None = None,
        team_id: str | None = None,
        market_slug: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[Any, ...]:
        raise RuntimeError("team forecast store module is required")

    def load_team_forecast_outcomes(
        connection: Any,
        *,
        team_id: str | None = None,
        market_slug: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[Any, ...]:
        raise RuntimeError("team forecast store module is required")

    def load_team_forecast_outcome_rows(
        connection: Any,
        *,
        team_id: str | None = None,
        market_slug: str | None = None,
        limit: int | None = None,
        table_name: str,
    ) -> tuple[Any, ...]:
        raise RuntimeError("team forecast store module is required")


_T = TypeVar("_T")


def insert_team_market_route_with_psycopg(
    dsn: str,
    report: TeamMarketRouteReport,
    *,
    table_name: str,
) -> TeamMarketRouteDbRow:
    row = team_route_to_db_row(report)
    return _with_owned_connection(
        dsn,
        lambda connection: insert_team_market_route(
            connection,
            row,
            table_name=table_name,
        ),
    )


def insert_team_forecast_with_psycopg(
    dsn: str,
    packet: TeamForecastPacket,
    *,
    table_name: str,
) -> TeamForecastDbRow:
    row = team_forecast_to_db_row(packet)
    return _with_owned_connection(
        dsn,
        lambda connection: insert_team_forecast(
            connection,
            row,
            table_name=table_name,
        ),
    )


def load_team_forecasts_with_psycopg(
    dsn: str,
    *,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str,
) -> tuple[TeamForecastPacket, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_team_forecasts(
            connection,
            team_id=team_id,
            market_slug=market_slug,
            limit=limit,
            table_name=table_name,
        ),
    )


def load_team_forecast_rows_with_psycopg(
    dsn: str,
    *,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str,
) -> tuple[TeamForecastDbRow, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_team_forecast_rows(
            connection,
            team_id=team_id,
            market_slug=market_slug,
            limit=limit,
            table_name=table_name,
        ),
    )


def insert_team_forecast_evidence_with_psycopg(
    dsn: str,
    packet: TeamForecastEvidencePacket,
    *,
    forecast_id: str,
    config_version: str,
    generated_at: datetime,
    table_name: str,
) -> TeamForecastEvidenceDbRow:
    row = team_forecast_evidence_to_db_row(
        packet,
        forecast_id=forecast_id,
        config_version=config_version,
        generated_at=generated_at,
    )
    return _with_owned_connection(
        dsn,
        lambda connection: insert_team_forecast_evidence(
            connection,
            row,
            table_name=table_name,
        ),
    )


def load_team_forecast_evidence_with_psycopg(
    dsn: str,
    *,
    forecast_id: str | None = None,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str,
) -> tuple[TeamForecastEvidencePacket, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_team_forecast_evidence(
            connection,
            forecast_id=forecast_id,
            team_id=team_id,
            market_slug=market_slug,
            limit=limit,
            table_name=table_name,
        ),
    )


def load_team_forecast_evidence_rows_with_psycopg(
    dsn: str,
    *,
    forecast_id: str | None = None,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str,
) -> tuple[TeamForecastEvidenceDbRow, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_team_forecast_evidence_rows(
            connection,
            forecast_id=forecast_id,
            team_id=team_id,
            market_slug=market_slug,
            limit=limit,
            table_name=table_name,
        ),
    )


def insert_team_forecast_outcome_with_psycopg(
    dsn: str,
    outcome: TeamForecastOutcome,
    *,
    config_version: str,
    generated_at: datetime,
    table_name: str,
) -> TeamForecastOutcomeDbRow:
    row = team_forecast_outcome_to_db_row(
        outcome,
        config_version=config_version,
        generated_at=generated_at,
    )
    return _with_owned_connection(
        dsn,
        lambda connection: insert_team_forecast_outcome(
            connection,
            row,
            table_name=table_name,
        ),
    )


def load_team_forecast_outcomes_with_psycopg(
    dsn: str,
    *,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str,
) -> tuple[TeamForecastOutcome, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_team_forecast_outcomes(
            connection,
            team_id=team_id,
            market_slug=market_slug,
            limit=limit,
            table_name=table_name,
        ),
    )


def load_team_forecast_outcome_rows_with_psycopg(
    dsn: str,
    *,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str,
) -> tuple[TeamForecastOutcomeDbRow, ...]:
    return _with_owned_connection(
        dsn,
        lambda connection: load_team_forecast_outcome_rows(
            connection,
            team_id=team_id,
            market_slug=market_slug,
            limit=limit,
            table_name=table_name,
        ),
    )


def _with_owned_connection(dsn: str, operation: Callable[[Any], _T]) -> _T:
    validate_local_postgres_dsn(
        dsn,
        env_var_name=TEAM_FORECAST_DB_DSN_ENV_VAR,
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


def _connect(dsn: str) -> Any:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        if exc.name != "psycopg":
            raise
        raise RuntimeError(
            "psycopg is required to use the team forecast psycopg adapter; "
            "install the postgres extra.",
        ) from exc
    try:
        return psycopg.connect(dsn)
    except Exception:
        raise RuntimeError("failed to connect to the team forecast database") from None


def _jsonb_adapter() -> type[Any]:
    try:
        from psycopg.types.json import Jsonb
    except ModuleNotFoundError as exc:
        if exc.name not in ("psycopg", "psycopg.types", "psycopg.types.json"):
            raise
        raise RuntimeError(
            "psycopg is required to use the team forecast psycopg adapter; "
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
    "insert_team_market_route_with_psycopg",
    "insert_team_forecast_evidence_with_psycopg",
    "insert_team_forecast_outcome_with_psycopg",
    "insert_team_forecast_with_psycopg",
    "load_team_forecast_evidence_with_psycopg",
    "load_team_forecast_evidence_rows_with_psycopg",
    "load_team_forecast_outcomes_with_psycopg",
    "load_team_forecast_outcome_rows_with_psycopg",
    "load_team_forecast_rows_with_psycopg",
    "load_team_forecasts_with_psycopg",
)
