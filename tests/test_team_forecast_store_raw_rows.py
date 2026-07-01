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


@dataclass(frozen=True)
class FakeTeamForecastPacket:
    forecast_id: str
    payload_json: dict[str, Any]


@dataclass(frozen=True)
class FakeTeamForecastEvidencePacket:
    evidence_id: str
    payload_json: dict[str, Any]


@dataclass(frozen=True)
class FakeTeamForecastOutcome:
    outcome_id: str
    payload_json: dict[str, Any]


class FakeCursor:
    def __init__(self, rows: tuple[Any, ...]) -> None:
        self.rows = rows
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))

    def fetchall(self) -> tuple[Any, ...]:
        return self.rows

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, rows: tuple[Any, ...]) -> None:
        self.cursor_instance = FakeCursor(rows)
        self.cursor_count = 0
        self.commit_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


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
        "payload_json": {"kind": "forecast", "extra_recovery_field": "kept"},
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
        "payload_json": {"kind": "evidence", "extra_recovery_field": "kept"},
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
        "payload_json": {"kind": "outcome", "extra_recovery_field": "kept"},
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
        return FakeTeamForecastPacket(row.forecast_id, {"converted": row.payload_json})

    def team_forecast_evidence_from_db_row(
        row: FakeTeamForecastEvidenceDbRow,
    ) -> FakeTeamForecastEvidencePacket:
        return FakeTeamForecastEvidencePacket(row.evidence_id, {"converted": row.payload_json})

    def team_forecast_outcome_from_db_row(
        row: FakeTeamForecastOutcomeDbRow,
    ) -> FakeTeamForecastOutcome:
        return FakeTeamForecastOutcome(row.outcome_id, {"converted": row.payload_json})

    companion.TeamMarketRouteDbRow = FakeTeamMarketRouteDbRow
    companion.TeamForecastDbRow = FakeTeamForecastDbRow
    companion.TeamForecastEvidenceDbRow = FakeTeamForecastEvidenceDbRow
    companion.TeamForecastOutcomeDbRow = FakeTeamForecastOutcomeDbRow
    companion.team_forecast_from_db_row = team_forecast_from_db_row
    companion.team_forecast_evidence_from_db_row = team_forecast_evidence_from_db_row
    companion.team_forecast_outcome_from_db_row = team_forecast_outcome_from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.team_forecast_db_row",
        companion,
    )
    sys.modules.pop("polymarket_alpha_lab.team_forecast_store", None)
    return importlib.import_module("polymarket_alpha_lab.team_forecast_store")


def test_load_team_forecast_rows_returns_db_rows_with_filters_order_and_limit(
    store_module: types.ModuleType,
) -> None:
    row = forecast_row()
    connection = FakeConnection((row,))

    loaded = store_module.load_team_forecast_rows(
        connection,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=5,
        table_name="research.team_forecasts",
    )

    assert loaded == (row,)
    assert loaded[0].forecast_probability == Decimal("0.620000")
    assert loaded[0].payload_json == {"kind": "forecast", "extra_recovery_field": "kept"}
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
    assert params == ("crypto_btc", "bitcoin-above-120k", 5)


def test_load_team_forecast_evidence_rows_filters_by_forecast_team_market_and_limit(
    store_module: types.ModuleType,
) -> None:
    row = evidence_row()
    connection = FakeConnection((row,))

    loaded = store_module.load_team_forecast_evidence_rows(
        connection,
        forecast_id="forecast-btc-1",
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=3,
        table_name="research.team_forecast_evidence",
    )

    assert loaded == (row,)
    assert loaded[0].weight == Decimal("0.420000")
    assert connection.commit_count == 0
    sql, params = connection.cursor_instance.calls[0]
    assert "FROM research.team_forecast_evidence" in normalize_sql(sql)
    assert (
        "WHERE forecast_id = %s AND team_id = %s AND market_slug = %s"
        in normalize_sql(sql)
    )
    assert (
        "ORDER BY generated_at DESC, inserted_at DESC, payload_sha256 DESC"
        in normalize_sql(sql)
    )
    assert normalize_sql(sql).endswith("LIMIT %s")
    assert params == ("forecast-btc-1", "crypto_btc", "bitcoin-above-120k", 3)


def test_load_team_forecast_outcome_rows_returns_rows_newest_resolution_first(
    store_module: types.ModuleType,
) -> None:
    row = outcome_row()
    connection = FakeConnection((row,))

    loaded = store_module.load_team_forecast_outcome_rows(
        connection,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=2,
        table_name="research.team_forecast_outcomes",
    )

    assert loaded == (row,)
    assert loaded[0].forecast_error == Decimal("0.380000")
    assert connection.commit_count == 0
    sql, params = connection.cursor_instance.calls[0]
    assert "FROM research.team_forecast_outcomes" in normalize_sql(sql)
    assert "WHERE team_id = %s AND market_slug = %s" in normalize_sql(sql)
    assert (
        "ORDER BY resolved_at DESC, generated_at DESC, inserted_at DESC, "
        "outcome_id DESC"
    ) in normalize_sql(sql)
    assert normalize_sql(sql).endswith("LIMIT %s")
    assert params == ("crypto_btc", "bitcoin-above-120k", 2)


def test_existing_packet_loaders_delegate_through_raw_row_loaders(
    store_module: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forecast = forecast_row()
    evidence = evidence_row()
    outcome = outcome_row()
    calls: list[tuple[str, object, str | None, str | None, int | None, str]] = []

    def fake_forecast_rows(
        connection_arg: object,
        *,
        team_id: str | None,
        market_slug: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeTeamForecastDbRow, ...]:
        calls.append(("forecast", connection_arg, team_id, market_slug, limit, table_name))
        return (forecast,)

    def fake_evidence_rows(
        connection_arg: object,
        *,
        forecast_id: str | None,
        team_id: str | None,
        market_slug: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeTeamForecastEvidenceDbRow, ...]:
        calls.append(
            (
                f"evidence:{forecast_id}",
                connection_arg,
                team_id,
                market_slug,
                limit,
                table_name,
            ),
        )
        return (evidence,)

    def fake_outcome_rows(
        connection_arg: object,
        *,
        team_id: str | None,
        market_slug: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeTeamForecastOutcomeDbRow, ...]:
        calls.append(("outcome", connection_arg, team_id, market_slug, limit, table_name))
        return (outcome,)

    monkeypatch.setattr(store_module, "load_team_forecast_rows", fake_forecast_rows)
    monkeypatch.setattr(
        store_module,
        "load_team_forecast_evidence_rows",
        fake_evidence_rows,
    )
    monkeypatch.setattr(store_module, "load_team_forecast_outcome_rows", fake_outcome_rows)

    connection = FakeConnection(())

    assert store_module.load_team_forecasts(
        connection,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=5,
        table_name="team_forecasts",
    ) == (
        FakeTeamForecastPacket(
            "forecast-btc-1",
            {"converted": {"kind": "forecast", "extra_recovery_field": "kept"}},
        ),
    )
    assert store_module.load_team_forecast_evidence(
        connection,
        forecast_id="forecast-btc-1",
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=4,
        table_name="team_forecast_evidence",
    ) == (
        FakeTeamForecastEvidencePacket(
            "evidence-btc-1",
            {"converted": {"kind": "evidence", "extra_recovery_field": "kept"}},
        ),
    )
    assert store_module.load_team_forecast_outcomes(
        connection,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=3,
        table_name="team_forecast_outcomes",
    ) == (
        FakeTeamForecastOutcome(
            "outcome-btc-1",
            {"converted": {"kind": "outcome", "extra_recovery_field": "kept"}},
        ),
    )
    assert calls == [
        ("forecast", connection, "crypto_btc", "bitcoin-above-120k", 5, "team_forecasts"),
        (
            "evidence:forecast-btc-1",
            connection,
            "crypto_btc",
            "bitcoin-above-120k",
            4,
            "team_forecast_evidence",
        ),
        (
            "outcome",
            connection,
            "crypto_btc",
            "bitcoin-above-120k",
            3,
            "team_forecast_outcomes",
        ),
    ]
