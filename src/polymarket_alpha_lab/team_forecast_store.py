"""DB-API repository for team forecast persistence rows."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastEvidenceDbRow,
    TeamForecastOutcomeDbRow,
    TeamMarketRouteDbRow,
    team_forecast_evidence_from_db_row,
    team_forecast_from_db_row,
    team_forecast_outcome_from_db_row,
)

if TYPE_CHECKING:
    from polymarket_alpha_lab.team_forecast_db_row import TeamForecastOutcome
    from polymarket_alpha_lab.team_forecast_packet import TeamForecastEvidencePacket
    from polymarket_alpha_lab.team_forecast_packet import TeamForecastPacket


__all__ = (
    "insert_team_market_route",
    "insert_team_forecast",
    "insert_team_forecast_evidence",
    "insert_team_forecast_outcome",
    "load_team_forecast_evidence",
    "load_team_forecast_evidence_rows",
    "load_team_forecast_outcome_rows",
    "load_team_forecasts",
    "load_team_forecast_rows",
    "load_team_forecast_outcomes",
)


_IDENTIFIER_PATTERN = re.compile(r"^[a-z](?:[a-z0-9_]*[a-z0-9])?$")
_TABLE_NAME_ERROR = "table_name must be a lowercase identifier with optional schema prefix"
_DEFAULT_ROUTE_TABLE_NAME = "team_market_routes"
_DEFAULT_FORECAST_TABLE_NAME = "team_forecasts"
_DEFAULT_EVIDENCE_TABLE_NAME = "team_forecast_evidence"
_DEFAULT_OUTCOME_TABLE_NAME = "team_forecast_outcomes"

_ROUTE_COLUMNS = (
    "payload_sha256",
    "generated_at",
    "team_id",
    "market_slug",
    "config_version",
    "condition_id",
    "category_id",
    "event_template",
    "routing_confidence",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)
_FORECAST_COLUMNS = (
    "payload_sha256",
    "generated_at",
    "forecast_id",
    "condition_id",
    "team_id",
    "market_slug",
    "config_version",
    "selected_side",
    "forecast_probability",
    "confidence",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)
_EVIDENCE_COLUMNS = (
    "payload_sha256",
    "generated_at",
    "forecast_id",
    "evidence_id",
    "team_id",
    "market_slug",
    "config_version",
    "source_id",
    "data_timestamp",
    "data_freshness_seconds",
    "evidence_type",
    "weight",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)
_OUTCOME_COLUMNS = (
    "payload_sha256",
    "generated_at",
    "outcome_id",
    "forecast_id",
    "team_id",
    "market_slug",
    "config_version",
    "resolved_at",
    "actual_outcome",
    "forecast_error",
    "brier_score",
    "paper_pnl",
    "cost_adjusted_return",
    "directionally_correct",
    "profitable_after_cost",
    "resolution_dispute_flag",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


def insert_team_market_route(
    connection: Any,
    row: TeamMarketRouteDbRow,
    *,
    table_name: str = _DEFAULT_ROUTE_TABLE_NAME,
) -> TeamMarketRouteDbRow:
    table_name = _validate_table_name(table_name)
    _require_row_type("row", row, TeamMarketRouteDbRow)
    sql = _insert_sql(table_name, _ROUTE_COLUMNS, "payload_sha256")
    _execute_insert(connection, sql, _params_from_row(row, _ROUTE_COLUMNS))
    return row


def insert_team_forecast(
    connection: Any,
    row: TeamForecastDbRow,
    *,
    table_name: str = _DEFAULT_FORECAST_TABLE_NAME,
) -> TeamForecastDbRow:
    table_name = _validate_table_name(table_name)
    _require_row_type("row", row, TeamForecastDbRow)
    sql = _insert_sql(table_name, _FORECAST_COLUMNS, "payload_sha256")
    _execute_insert(connection, sql, _params_from_row(row, _FORECAST_COLUMNS))
    return row


def insert_team_forecast_evidence(
    connection: Any,
    row: TeamForecastEvidenceDbRow,
    *,
    table_name: str = _DEFAULT_EVIDENCE_TABLE_NAME,
) -> TeamForecastEvidenceDbRow:
    table_name = _validate_table_name(table_name)
    _require_row_type("row", row, TeamForecastEvidenceDbRow)
    sql = _insert_sql(table_name, _EVIDENCE_COLUMNS, "payload_sha256")
    _execute_insert(connection, sql, _params_from_row(row, _EVIDENCE_COLUMNS))
    return row


def insert_team_forecast_outcome(
    connection: Any,
    row: TeamForecastOutcomeDbRow,
    *,
    table_name: str = _DEFAULT_OUTCOME_TABLE_NAME,
) -> TeamForecastOutcomeDbRow:
    table_name = _validate_table_name(table_name)
    _require_row_type("row", row, TeamForecastOutcomeDbRow)
    sql = _insert_sql(table_name, _OUTCOME_COLUMNS, "outcome_id")
    _execute_insert(connection, sql, _params_from_row(row, _OUTCOME_COLUMNS))
    return row


def load_team_forecasts(
    connection: Any,
    *,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_FORECAST_TABLE_NAME,
) -> tuple[TeamForecastPacket, ...]:
    rows = load_team_forecast_rows(
        connection,
        team_id=team_id,
        market_slug=market_slug,
        limit=limit,
        table_name=table_name,
    )
    return tuple(team_forecast_from_db_row(row) for row in rows)


def load_team_forecast_rows(
    connection: Any,
    *,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_FORECAST_TABLE_NAME,
) -> tuple[TeamForecastDbRow, ...]:
    table_name = _validate_table_name(table_name)
    where_clause, params = _filter_params(
        team_id=team_id,
        market_slug=market_slug,
        limit=limit,
    )
    limit_clause = _limit_clause(limit)
    columns = ",\n            ".join(_FORECAST_COLUMNS)
    sql = f"""
        SELECT
            {columns}
        FROM {table_name}
        {where_clause}
        ORDER BY generated_at DESC, inserted_at DESC, payload_sha256 DESC
        {limit_clause}
        """
    records = _execute_load(connection, sql, tuple(params))
    return tuple(
        _db_row_from_record(record, TeamForecastDbRow, _FORECAST_COLUMNS)
        for record in records
    )


def load_team_forecast_evidence(
    connection: Any,
    *,
    forecast_id: str | None = None,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_EVIDENCE_TABLE_NAME,
) -> tuple[TeamForecastEvidencePacket, ...]:
    rows = load_team_forecast_evidence_rows(
        connection,
        forecast_id=forecast_id,
        team_id=team_id,
        market_slug=market_slug,
        limit=limit,
        table_name=table_name,
    )
    return tuple(team_forecast_evidence_from_db_row(row) for row in rows)


def load_team_forecast_evidence_rows(
    connection: Any,
    *,
    forecast_id: str | None = None,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_EVIDENCE_TABLE_NAME,
) -> tuple[TeamForecastEvidenceDbRow, ...]:
    table_name = _validate_table_name(table_name)
    where_clause, params = _filter_params(
        forecast_id=forecast_id,
        team_id=team_id,
        market_slug=market_slug,
        limit=limit,
    )
    limit_clause = _limit_clause(limit)
    columns = ",\n            ".join(_EVIDENCE_COLUMNS)
    sql = f"""
        SELECT
            {columns}
        FROM {table_name}
        {where_clause}
        ORDER BY generated_at DESC, inserted_at DESC, payload_sha256 DESC
        {limit_clause}
        """
    records = _execute_load(connection, sql, tuple(params))
    return tuple(
        _db_row_from_record(record, TeamForecastEvidenceDbRow, _EVIDENCE_COLUMNS)
        for record in records
    )


def load_team_forecast_outcomes(
    connection: Any,
    *,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_OUTCOME_TABLE_NAME,
) -> tuple[TeamForecastOutcome, ...]:
    rows = load_team_forecast_outcome_rows(
        connection,
        team_id=team_id,
        market_slug=market_slug,
        limit=limit,
        table_name=table_name,
    )
    return tuple(team_forecast_outcome_from_db_row(row) for row in rows)


def load_team_forecast_outcome_rows(
    connection: Any,
    *,
    team_id: str | None = None,
    market_slug: str | None = None,
    limit: int | None = None,
    table_name: str = _DEFAULT_OUTCOME_TABLE_NAME,
) -> tuple[TeamForecastOutcomeDbRow, ...]:
    table_name = _validate_table_name(table_name)
    where_clause, params = _filter_params(
        team_id=team_id,
        market_slug=market_slug,
        limit=limit,
    )
    limit_clause = _limit_clause(limit)
    columns = ",\n            ".join(_OUTCOME_COLUMNS)
    sql = f"""
        SELECT
            {columns}
        FROM {table_name}
        {where_clause}
        ORDER BY resolved_at DESC, generated_at DESC, inserted_at DESC, outcome_id DESC
        {limit_clause}
        """
    records = _execute_load(connection, sql, tuple(params))
    return tuple(
        _db_row_from_record(record, TeamForecastOutcomeDbRow, _OUTCOME_COLUMNS)
        for record in records
    )


def _insert_sql(
    table_name: str,
    columns: tuple[str, ...],
    conflict_column: str,
) -> str:
    column_sql = ",\n            ".join(columns)
    placeholders = ", ".join("%s" for _column in columns)
    return f"""
        INSERT INTO {table_name} (
            {column_sql}
        ) VALUES ({placeholders})
        ON CONFLICT ({conflict_column}) DO NOTHING
        """


def _params_from_row(row: Any, columns: tuple[str, ...]) -> tuple[Any, ...]:
    return tuple(getattr(row, column) for column in columns)


def _execute_insert(connection: Any, sql: str, params: tuple[Any, ...]) -> None:
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        _require_insert_rowcount(cursor)
    except BaseException:
        _close_cursor_after_operation_error(cursor)
        raise
    cursor.close()


def _execute_load(connection: Any, sql: str, params: tuple[Any, ...]) -> tuple[Any, ...]:
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        records = cursor.fetchall()
    except BaseException:
        _close_cursor_after_operation_error(cursor)
        raise
    cursor.close()
    return tuple(records)


def _filter_params(
    *,
    forecast_id: str | None = None,
    team_id: str | None,
    market_slug: str | None,
    limit: int | None,
) -> tuple[str, list[Any]]:
    if forecast_id is not None:
        _require_canonical_string("forecast_id", forecast_id)
    if team_id is not None:
        _require_canonical_string("team_id", team_id)
    if market_slug is not None:
        _require_canonical_string("market_slug", market_slug)
    if limit is not None:
        _require_positive_int("limit", limit)

    where_parts: list[str] = []
    params: list[Any] = []
    if forecast_id is not None:
        where_parts.append("forecast_id = %s")
        params.append(forecast_id)
    if team_id is not None:
        where_parts.append("team_id = %s")
        params.append(team_id)
    if market_slug is not None:
        where_parts.append("market_slug = %s")
        params.append(market_slug)
    if limit is not None:
        params.append(limit)
    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    return where_clause, params


def _limit_clause(limit: int | None) -> str:
    if limit is None:
        return ""
    return "LIMIT %s"


def _db_row_from_record(
    record: Any,
    row_type: type[Any],
    columns: tuple[str, ...],
) -> Any:
    if isinstance(record, row_type):
        return record
    if isinstance(record, dict):
        values = tuple(record[column] for column in columns)
    elif hasattr(record, "_asdict"):
        as_dict = record._asdict()
        values = tuple(as_dict[column] for column in columns)
    else:
        values = tuple(record)
    if len(values) != len(columns):
        raise ValueError("DB row must contain selected team forecast columns")
    return row_type(
        **{
            column: _normalize_json_object(column, value)
            if column == "payload_json"
            else value
            for column, value in zip(columns, values, strict=True)
        },
    )


def _normalize_json_object(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(value)


def _validate_table_name(value: str) -> str:
    if type(value) is not str:
        raise ValueError(_TABLE_NAME_ERROR)
    parts = value.split(".")
    if len(parts) not in (1, 2):
        raise ValueError(_TABLE_NAME_ERROR)
    for part in parts:
        if len(part.encode("utf-8")) > 63:
            raise ValueError(_TABLE_NAME_ERROR)
        if _IDENTIFIER_PATTERN.fullmatch(part) is None:
            raise ValueError(_TABLE_NAME_ERROR)
    return value


def _require_row_type(field_name: str, value: Any, row_type: type[Any]) -> None:
    if not isinstance(value, row_type):
        raise ValueError(f"{field_name} must be a {row_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_insert_rowcount(cursor: Any) -> None:
    rowcount = getattr(cursor, "rowcount")
    if rowcount not in (0, 1):
        raise ValueError("insert rowcount must be 0 or 1")


def _close_cursor_after_operation_error(cursor: Any) -> None:
    try:
        cursor.close()
    except BaseException:
        pass
