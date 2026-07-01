from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
RESOLVED_AT = datetime(2026, 7, 1, 13, 0, tzinfo=UTC)
DATA_TIMESTAMP = datetime(2026, 7, 1, 11, 58, tzinfo=UTC)


@dataclass(frozen=True)
class FakeTeamForecastPacket:
    forecast_id: str
    team_id: str
    market_slug: str


@dataclass(frozen=True)
class FakeTeamForecastEvidencePacket:
    evidence_id: str
    team_id: str
    market_slug: str


@dataclass(frozen=True)
class FakeTeamForecastOutcome:
    outcome_id: str
    team_id: str
    market_slug: str


@dataclass(frozen=True)
class FakeTeamMarketRouteReport:
    team_id: str
    market_slug: str
    category_id: str


@dataclass(frozen=True)
class FakeTeamMarketRouteDbRow:
    payload_sha256: str
    generated_at: datetime
    team_id: str
    market_slug: str
    config_version: str
    condition_id: str
    category_id: str
    event_template: str
    routing_confidence: Decimal
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class FakeTeamForecastDbRow:
    payload_sha256: str
    generated_at: datetime
    forecast_id: str
    condition_id: str
    team_id: str
    market_slug: str
    config_version: str
    selected_side: str
    forecast_probability: Decimal
    confidence: Decimal
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class FakeTeamForecastEvidenceDbRow:
    payload_sha256: str
    generated_at: datetime
    forecast_id: str
    evidence_id: str
    team_id: str
    market_slug: str
    config_version: str
    source_id: str
    data_timestamp: datetime
    data_freshness_seconds: int
    evidence_type: str
    weight: Decimal
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class FakeTeamForecastOutcomeDbRow:
    payload_sha256: str
    generated_at: datetime
    outcome_id: str
    forecast_id: str
    team_id: str
    market_slug: str
    config_version: str
    resolved_at: datetime
    actual_outcome: str
    forecast_error: Decimal
    brier_score: Decimal
    paper_pnl: Decimal
    cost_adjusted_return: Decimal
    directionally_correct: bool
    profitable_after_cost: bool
    resolution_dispute_flag: bool
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class FakeCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        rowcount: int = 1,
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.rows = rows
        self.rowcount = rowcount
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False
        self.close_count = 0
        self.execute_error = execute_error
        self.fetchall_error = fetchall_error
        self.close_error = close_error

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchall(self) -> tuple[Any, ...]:
        if self.fetchall_error is not None:
            raise self.fetchall_error
        return self.rows

    def close(self) -> None:
        self.close_count += 1
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FakeConnection:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        rowcount: int = 1,
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(
            rows,
            rowcount=rowcount,
            execute_error=execute_error,
            fetchall_error=fetchall_error,
            close_error=close_error,
        )
        self.cursor_count = 0
        self.commit_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def route_row(**overrides: Any) -> FakeTeamMarketRouteDbRow:
    values = {
        "payload_sha256": "a" * 64,
        "generated_at": GENERATED_AT,
        "team_id": "crypto_btc",
        "market_slug": "bitcoin-above-120k",
        "config_version": "team-router-v0",
        "condition_id": "condition-btc",
        "category_id": "finance.crypto.btc",
        "event_template": "btc_hit_price",
        "routing_confidence": Decimal("0.900000"),
        "payload_json": {"kind": "route", "paper_only": True},
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return FakeTeamMarketRouteDbRow(**values)


def forecast_row(**overrides: Any) -> FakeTeamForecastDbRow:
    values = {
        "payload_sha256": "b" * 64,
        "generated_at": GENERATED_AT,
        "forecast_id": "forecast-btc-1",
        "condition_id": "condition-btc",
        "team_id": "crypto_btc",
        "market_slug": "bitcoin-above-120k",
        "config_version": "team-forecast-v0",
        "selected_side": "yes",
        "forecast_probability": Decimal("0.620000"),
        "confidence": Decimal("0.710000"),
        "payload_json": {"kind": "forecast", "paper_only": True},
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return FakeTeamForecastDbRow(**values)


def evidence_row(**overrides: Any) -> FakeTeamForecastEvidenceDbRow:
    values = {
        "payload_sha256": "c" * 64,
        "generated_at": GENERATED_AT,
        "forecast_id": "forecast-btc-1",
        "evidence_id": "evidence-btc-1",
        "team_id": "crypto_btc",
        "market_slug": "bitcoin-above-120k",
        "config_version": "team-forecast-evidence-v0",
        "source_id": "source-etf-flow-dashboard",
        "data_timestamp": DATA_TIMESTAMP,
        "data_freshness_seconds": 120,
        "evidence_type": "etf_flow",
        "weight": Decimal("0.420000"),
        "payload_json": {"kind": "evidence", "paper_only": True},
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return FakeTeamForecastEvidenceDbRow(**values)


def outcome_row(**overrides: Any) -> FakeTeamForecastOutcomeDbRow:
    values = {
        "payload_sha256": "d" * 64,
        "generated_at": GENERATED_AT,
        "outcome_id": "outcome-btc-1",
        "forecast_id": "forecast-btc-1",
        "team_id": "crypto_btc",
        "market_slug": "bitcoin-above-120k",
        "config_version": "team-forecast-outcome-v0",
        "resolved_at": RESOLVED_AT,
        "actual_outcome": "yes",
        "forecast_error": Decimal("0.380000"),
        "brier_score": Decimal("0.144400"),
        "paper_pnl": Decimal("0.000000"),
        "cost_adjusted_return": Decimal("0.000000"),
        "directionally_correct": True,
        "profitable_after_cost": False,
        "resolution_dispute_flag": False,
        "payload_json": {"kind": "outcome", "paper_only": True},
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return FakeTeamForecastOutcomeDbRow(**values)


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType("polymarket_alpha_lab.team_forecast_db_row")

    def team_forecast_from_db_row(row: FakeTeamForecastDbRow) -> FakeTeamForecastPacket:
        return FakeTeamForecastPacket(
            forecast_id=row.forecast_id,
            team_id=row.team_id,
            market_slug=row.market_slug,
        )

    def team_forecast_evidence_from_db_row(
        row: FakeTeamForecastEvidenceDbRow,
    ) -> FakeTeamForecastEvidencePacket:
        return FakeTeamForecastEvidencePacket(
            evidence_id=row.evidence_id,
            team_id=row.team_id,
            market_slug=row.market_slug,
        )

    def team_forecast_outcome_from_db_row(
        row: FakeTeamForecastOutcomeDbRow,
    ) -> FakeTeamForecastOutcome:
        return FakeTeamForecastOutcome(
            outcome_id=row.outcome_id,
            team_id=row.team_id,
            market_slug=row.market_slug,
        )

    def team_route_from_db_row(
        row: FakeTeamMarketRouteDbRow,
    ) -> FakeTeamMarketRouteReport:
        return FakeTeamMarketRouteReport(
            team_id=row.team_id,
            market_slug=row.market_slug,
            category_id=row.category_id,
        )

    companion.TeamMarketRouteDbRow = FakeTeamMarketRouteDbRow
    companion.TeamForecastDbRow = FakeTeamForecastDbRow
    companion.TeamForecastEvidenceDbRow = FakeTeamForecastEvidenceDbRow
    companion.TeamForecastOutcomeDbRow = FakeTeamForecastOutcomeDbRow
    companion.team_forecast_from_db_row = team_forecast_from_db_row
    companion.team_forecast_evidence_from_db_row = team_forecast_evidence_from_db_row
    companion.team_forecast_outcome_from_db_row = team_forecast_outcome_from_db_row
    companion.team_route_from_db_row = team_route_from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.team_forecast_db_row",
        companion,
    )
    sys.modules.pop("polymarket_alpha_lab.team_forecast_store", None)
    return importlib.import_module("polymarket_alpha_lab.team_forecast_store")


def test_insert_team_market_route_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    row = route_row()

    inserted = store_module.insert_team_market_route(
        connection,
        row,
        table_name="research.team_market_routes",
    )

    assert inserted == row
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO research.team_market_routes (
            payload_sha256,
            generated_at,
            team_id,
            market_slug,
            config_version,
            condition_id,
            category_id,
            event_template,
            routing_confidence,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (payload_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        GENERATED_AT,
        "crypto_btc",
        "bitcoin-above-120k",
        "team-router-v0",
        "condition-btc",
        "finance.crypto.btc",
        "btc_hit_price",
        Decimal("0.900000"),
        {"kind": "route", "paper_only": True},
        True,
        True,
        True,
    )


def test_insert_team_forecast_uses_payload_sha256_conflict_key(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    row = forecast_row()

    inserted = store_module.insert_team_forecast(
        connection,
        row,
        table_name="research.team_forecasts",
    )

    assert inserted == row
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO research.team_forecasts (
            payload_sha256,
            generated_at,
            forecast_id,
            condition_id,
            team_id,
            market_slug,
            config_version,
            selected_side,
            forecast_probability,
            confidence,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (payload_sha256) DO NOTHING
        """,
    )
    assert params == (
        "b" * 64,
        GENERATED_AT,
        "forecast-btc-1",
        "condition-btc",
        "crypto_btc",
        "bitcoin-above-120k",
        "team-forecast-v0",
        "yes",
        Decimal("0.620000"),
        Decimal("0.710000"),
        {"kind": "forecast", "paper_only": True},
        True,
        True,
        True,
    )


def test_insert_team_forecast_evidence_uses_payload_sha256_conflict_key(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    row = evidence_row()

    inserted = store_module.insert_team_forecast_evidence(
        connection,
        row,
        table_name="research.team_forecast_evidence",
    )

    assert inserted == row
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO research.team_forecast_evidence (
            payload_sha256,
            generated_at,
            forecast_id,
            evidence_id,
            team_id,
            market_slug,
            config_version,
            source_id,
            data_timestamp,
            data_freshness_seconds,
            evidence_type,
            weight,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (payload_sha256) DO NOTHING
        """,
    )
    assert params == (
        "c" * 64,
        GENERATED_AT,
        "forecast-btc-1",
        "evidence-btc-1",
        "crypto_btc",
        "bitcoin-above-120k",
        "team-forecast-evidence-v0",
        "source-etf-flow-dashboard",
        DATA_TIMESTAMP,
        120,
        "etf_flow",
        Decimal("0.420000"),
        {"kind": "evidence", "paper_only": True},
        True,
        True,
        True,
    )


def test_insert_team_forecast_outcome_uses_outcome_id_conflict_key(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    row = outcome_row()

    inserted = store_module.insert_team_forecast_outcome(
        connection,
        row,
        table_name="research.team_forecast_outcomes",
    )

    assert inserted == row
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO research.team_forecast_outcomes (
            payload_sha256,
            generated_at,
            outcome_id,
            forecast_id,
            team_id,
            market_slug,
            config_version,
            resolved_at,
            actual_outcome,
            forecast_error,
            brier_score,
            paper_pnl,
            cost_adjusted_return,
            directionally_correct,
            profitable_after_cost,
            resolution_dispute_flag,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (outcome_id) DO NOTHING
        """,
    )
    assert params == (
        "d" * 64,
        GENERATED_AT,
        "outcome-btc-1",
        "forecast-btc-1",
        "crypto_btc",
        "bitcoin-above-120k",
        "team-forecast-outcome-v0",
        RESOLVED_AT,
        "yes",
        Decimal("0.380000"),
        Decimal("0.144400"),
        Decimal("0.000000"),
        Decimal("0.000000"),
        True,
        False,
        False,
        {"kind": "outcome", "paper_only": True},
        True,
        True,
        True,
    )


@pytest.mark.parametrize("rowcount", (0, 1))
def test_insert_allows_zero_or_one_rowcount(
    store_module: types.ModuleType,
    rowcount: int,
) -> None:
    connection = FakeConnection(rowcount=rowcount)
    row = forecast_row()

    inserted = store_module.insert_team_forecast(
        connection,
        row,
        table_name="team_forecasts",
    )

    assert inserted == row
    assert connection.cursor_instance.close_count == 1


@pytest.mark.parametrize("rowcount", (-1, 2))
def test_insert_rejects_unexpected_rowcount_and_closes_cursor(
    store_module: types.ModuleType,
    rowcount: int,
) -> None:
    connection = FakeConnection(rowcount=rowcount)

    with pytest.raises(ValueError, match="rowcount"):
        store_module.insert_team_forecast(
            connection,
            forecast_row(),
            table_name="team_forecasts",
        )

    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.closed is True


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_team_forecast(
            connection,
            forecast_row(),
            table_name="team_forecasts; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_insert_preserves_execute_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    execute_error = RuntimeError("execute failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        execute_error=execute_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError) as exc_info:
        store_module.insert_team_forecast(
            connection,
            forecast_row(),
            table_name="team_forecasts",
        )

    assert exc_info.value is execute_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.closed is True


def test_insert_propagates_cursor_close_error_after_successful_execute(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(close_error=close_error)

    with pytest.raises(RuntimeError) as exc_info:
        store_module.insert_team_forecast(
            connection,
            forecast_row(),
            table_name="team_forecasts",
        )

    assert exc_info.value is close_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.calls


def test_load_team_market_routes_filters_limits_newest_first_and_restores_reports(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection(rows=(route_row(),))

    routes = store_module.load_team_market_routes(
        connection,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=25,
        table_name="research.team_market_routes",
    )

    assert routes == (
        FakeTeamMarketRouteReport(
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
            category_id="finance.crypto.btc",
        ),
    )
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            payload_sha256,
            generated_at,
            team_id,
            market_slug,
            config_version,
            condition_id,
            category_id,
            event_template,
            routing_confidence,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM research.team_market_routes
        WHERE team_id = %s AND market_slug = %s
        ORDER BY generated_at DESC, inserted_at DESC, payload_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("crypto_btc", "bitcoin-above-120k", 25)


def test_public_exports_include_all_team_forecast_store_helpers(
    store_module: types.ModuleType,
) -> None:
    assert set(store_module.__all__) == {
        "insert_team_market_route",
        "insert_team_forecast",
        "insert_team_forecast_evidence",
        "insert_team_forecast_outcome",
        "load_team_market_routes",
        "load_team_market_route_rows",
        "load_team_forecasts",
        "load_team_forecast_rows",
        "load_team_forecast_evidence",
        "load_team_forecast_evidence_rows",
        "load_team_forecast_outcomes",
        "load_team_forecast_outcome_rows",
    }


def test_load_team_forecasts_filters_limits_newest_first_and_restores_packets(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection(rows=(forecast_row(),))

    packets = store_module.load_team_forecasts(
        connection,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=25,
        table_name="research.team_forecasts",
    )

    assert packets == (
        FakeTeamForecastPacket(
            forecast_id="forecast-btc-1",
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
        ),
    )
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            payload_sha256,
            generated_at,
            forecast_id,
            condition_id,
            team_id,
            market_slug,
            config_version,
            selected_side,
            forecast_probability,
            confidence,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM research.team_forecasts
        WHERE team_id = %s AND market_slug = %s
        ORDER BY generated_at DESC, inserted_at DESC, payload_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("crypto_btc", "bitcoin-above-120k", 25)


def test_load_team_forecast_evidence_filters_limits_newest_first_and_restores_packets(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection(rows=(evidence_row(),))

    packets = store_module.load_team_forecast_evidence(
        connection,
        forecast_id="forecast-btc-1",
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=25,
        table_name="research.team_forecast_evidence",
    )

    assert packets == (
        FakeTeamForecastEvidencePacket(
            evidence_id="evidence-btc-1",
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
        ),
    )
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            payload_sha256,
            generated_at,
            forecast_id,
            evidence_id,
            team_id,
            market_slug,
            config_version,
            source_id,
            data_timestamp,
            data_freshness_seconds,
            evidence_type,
            weight,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM research.team_forecast_evidence
        WHERE forecast_id = %s AND team_id = %s AND market_slug = %s
        ORDER BY generated_at DESC, inserted_at DESC, payload_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("forecast-btc-1", "crypto_btc", "bitcoin-above-120k", 25)


def test_load_team_forecast_outcomes_filters_limits_newest_first_and_restores_outcomes(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection(rows=(outcome_row(),))

    outcomes = store_module.load_team_forecast_outcomes(
        connection,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=10,
        table_name="research.team_forecast_outcomes",
    )

    assert outcomes == (
        FakeTeamForecastOutcome(
            outcome_id="outcome-btc-1",
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
        ),
    )
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            payload_sha256,
            generated_at,
            outcome_id,
            forecast_id,
            team_id,
            market_slug,
            config_version,
            resolved_at,
            actual_outcome,
            forecast_error,
            brier_score,
            paper_pnl,
            cost_adjusted_return,
            directionally_correct,
            profitable_after_cost,
            resolution_dispute_flag,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM research.team_forecast_outcomes
        WHERE team_id = %s AND market_slug = %s
        ORDER BY resolved_at DESC, generated_at DESC, inserted_at DESC, outcome_id DESC
        LIMIT %s
        """,
    )
    assert params == ("crypto_btc", "bitcoin-above-120k", 10)


def test_load_accepts_mapping_and_positional_rows(
    store_module: types.ModuleType,
) -> None:
    forecast_mapping = {
        "payload_sha256": "e" * 64,
        "generated_at": GENERATED_AT,
        "forecast_id": "forecast-btc-2",
        "condition_id": "condition-btc",
        "team_id": "crypto_btc",
        "market_slug": "bitcoin-above-120k",
        "config_version": "team-forecast-v0",
        "selected_side": "yes",
        "forecast_probability": Decimal("0.630000"),
        "confidence": Decimal("0.720000"),
        "payload_json": {"kind": "forecast-2", "paper_only": True},
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    outcome_tuple = (
        "f" * 64,
        GENERATED_AT,
        "outcome-btc-2",
        "forecast-btc-2",
        "crypto_btc",
        "bitcoin-above-120k",
        "team-forecast-outcome-v0",
        RESOLVED_AT,
        "yes",
        Decimal("0.370000"),
        Decimal("0.136900"),
        Decimal("0.000000"),
        Decimal("0.000000"),
        True,
        False,
        False,
        {"kind": "outcome-2", "paper_only": True},
        True,
        True,
        True,
    )
    evidence_tuple = (
        "g" * 64,
        GENERATED_AT,
        "forecast-btc-2",
        "evidence-btc-2",
        "crypto_btc",
        "bitcoin-above-120k",
        "team-forecast-evidence-v0",
        "source-coinbase-premium",
        DATA_TIMESTAMP,
        90,
        "coinbase_premium",
        Decimal("0.510000"),
        {"kind": "evidence-2", "paper_only": True},
        True,
        True,
        True,
    )

    packets = store_module.load_team_forecasts(
        FakeConnection(rows=(forecast_mapping,)),
        table_name="team_forecasts",
    )
    evidence_packets = store_module.load_team_forecast_evidence(
        FakeConnection(rows=(evidence_tuple,)),
        table_name="team_forecast_evidence",
    )
    outcomes = store_module.load_team_forecast_outcomes(
        FakeConnection(rows=(outcome_tuple,)),
        table_name="team_forecast_outcomes",
    )

    assert packets == (
        FakeTeamForecastPacket(
            forecast_id="forecast-btc-2",
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
        ),
    )
    assert evidence_packets == (
        FakeTeamForecastEvidencePacket(
            evidence_id="evidence-btc-2",
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
        ),
    )
    assert outcomes == (
        FakeTeamForecastOutcome(
            outcome_id="outcome-btc-2",
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
        ),
    )


def test_load_preserves_fetchall_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    fetchall_error = RuntimeError("fetchall failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        fetchall_error=fetchall_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError) as exc_info:
        store_module.load_team_forecasts(connection, table_name="team_forecasts")

    assert exc_info.value is fetchall_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.closed is True


def test_load_propagates_cursor_close_error_after_successful_query(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(close_error=close_error)

    with pytest.raises(RuntimeError) as exc_info:
        store_module.load_team_forecasts(connection, table_name="team_forecasts")

    assert exc_info.value is close_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.calls


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.too.many.parts"}, "table_name"),
        ({"table_name": "_team_market_routes"}, "table_name"),
        ({"table_name": "team_market_routes_"}, "table_name"),
        ({"team_id": ""}, "team_id"),
        ({"team_id": " crypto_btc"}, "team_id"),
        ({"market_slug": ""}, "market_slug"),
        ({"market_slug": " bitcoin-above-120k"}, "market_slug"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_team_market_routes_rejects_invalid_query_inputs_without_executing_sql(
    store_module: types.ModuleType,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()
    kwargs.setdefault("table_name", "team_market_routes")

    with pytest.raises(ValueError, match=message):
        store_module.load_team_market_routes(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.too.many.parts"}, "table_name"),
        ({"forecast_id": ""}, "forecast_id"),
        ({"forecast_id": " forecast-btc-1"}, "forecast_id"),
        ({"team_id": ""}, "team_id"),
        ({"team_id": " crypto_btc"}, "team_id"),
        ({"market_slug": ""}, "market_slug"),
        ({"market_slug": " bitcoin-above-120k"}, "market_slug"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_team_forecast_evidence_rejects_invalid_query_inputs_without_executing_sql(
    store_module: types.ModuleType,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()
    kwargs.setdefault("table_name", "team_forecast_evidence")

    with pytest.raises(ValueError, match=message):
        store_module.load_team_forecast_evidence(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.too.many.parts"}, "table_name"),
        ({"team_id": ""}, "team_id"),
        ({"team_id": " crypto_btc"}, "team_id"),
        ({"market_slug": ""}, "market_slug"),
        ({"market_slug": " bitcoin-above-120k"}, "market_slug"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_team_forecast_outcomes_rejects_invalid_query_inputs_without_executing_sql(
    store_module: types.ModuleType,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()
    kwargs.setdefault("table_name", "team_forecast_outcomes")

    with pytest.raises(ValueError, match=message):
        store_module.load_team_forecast_outcomes(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.too.many.parts"}, "table_name"),
        ({"table_name": "_team_forecasts"}, "table_name"),
        ({"table_name": "team_forecasts_"}, "table_name"),
        ({"team_id": ""}, "team_id"),
        ({"team_id": " crypto_btc"}, "team_id"),
        ({"market_slug": ""}, "market_slug"),
        ({"market_slug": " bitcoin-above-120k"}, "market_slug"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_rejects_invalid_query_inputs_without_executing_sql(
    store_module: types.ModuleType,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()
    kwargs.setdefault("table_name", "team_forecasts")

    with pytest.raises(ValueError, match=message):
        store_module.load_team_forecasts(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
