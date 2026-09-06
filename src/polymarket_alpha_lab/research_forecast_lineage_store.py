"""Transaction-neutral store for immutable research forecast lineage."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .research_forecast_lineage_db_row import ResearchForecastLineageRow


LINEAGE_TABLE = "research_settlement.research_forecast_lineage"
_COLUMNS = (
    "forecast_payload_sha256",
    "forecast_id",
    "condition_id",
    "team_id",
    "config_version",
    "event_id",
    "event_slug",
    "market_end_at",
    "event_lineage_state",
    "metadata_observed_at",
    "metadata_payload_sha256",
    "paper_only",
    "report_only",
    "readonly",
)


class ResearchForecastLineageStoreError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ResearchForecastLineageInsertResult:
    forecast_id: str
    status: str


def _values(record: Any) -> tuple[Any, ...]:
    if isinstance(record, Mapping):
        return tuple(record[column] for column in _COLUMNS)
    return tuple(record)


def _normalized(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return value


class ResearchForecastLineageStore:
    def __init__(self, connection: Any) -> None:
        if connection is None or not hasattr(connection, "cursor"):
            raise ValueError("connection must provide cursor()")
        self.connection = connection

    def insert(
        self, row: ResearchForecastLineageRow
    ) -> ResearchForecastLineageInsertResult:
        if type(row) is not ResearchForecastLineageRow:
            raise ValueError("row must be a ResearchForecastLineageRow")
        columns = ", ".join(_COLUMNS)
        placeholders = ", ".join("%s" for _ in _COLUMNS)
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                f"INSERT INTO {LINEAGE_TABLE} ({columns}) VALUES ({placeholders}) "
                "ON CONFLICT (forecast_payload_sha256) DO NOTHING "
                "RETURNING forecast_payload_sha256",
                row.as_parameters(),
            )
            if cursor.fetchone() is not None:
                return ResearchForecastLineageInsertResult(row.forecast_id, "inserted")
            cursor.execute(
                f"SELECT {columns} FROM {LINEAGE_TABLE} "
                "WHERE forecast_payload_sha256 = %s",
                (row.forecast_payload_sha256,),
            )
            existing = cursor.fetchone()
            expected = row.as_parameters()
            if existing is None or tuple(map(_normalized, _values(existing))) != tuple(
                map(_normalized, expected)
            ):
                raise ResearchForecastLineageStoreError("identity_collision")
            return ResearchForecastLineageInsertResult(row.forecast_id, "already_present")
        finally:
            cursor.close()


__all__ = (
    "LINEAGE_TABLE",
    "ResearchForecastLineageInsertResult",
    "ResearchForecastLineageStore",
    "ResearchForecastLineageStoreError",
)
