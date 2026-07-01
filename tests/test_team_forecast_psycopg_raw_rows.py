from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


LOCAL_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


@dataclass(frozen=True)
class FakeForecastDbRow:
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
class FakeEvidenceDbRow:
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
class FakeOutcomeDbRow:
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


class FakeOwnedConnection:
    pass


@pytest.fixture()
def adapter_module() -> types.ModuleType:
    sys.modules.pop("polymarket_alpha_lab.team_forecast_psycopg", None)
    return importlib.import_module("polymarket_alpha_lab.team_forecast_psycopg")


def forecast_row() -> FakeForecastDbRow:
    return FakeForecastDbRow(
        payload_sha256="b" * 64,
        generated_at=GENERATED_AT,
        forecast_id="forecast-btc-1",
        condition_id="condition-btc",
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        config_version="team-forecast-v0",
        selected_side="yes",
        forecast_probability=Decimal("0.620000"),
        confidence=Decimal("0.710000"),
        payload_json={"kind": "forecast"},
    )


def evidence_row() -> FakeEvidenceDbRow:
    return FakeEvidenceDbRow(
        payload_sha256="c" * 64,
        generated_at=GENERATED_AT,
        forecast_id="forecast-btc-1",
        evidence_id="evidence-btc-1",
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        config_version="team-forecast-evidence-v0",
        source_id="source-etf-flow-dashboard",
        data_timestamp=GENERATED_AT,
        data_freshness_seconds=60,
        evidence_type="etf_flow",
        weight=Decimal("0.420000"),
        payload_json={"kind": "evidence"},
    )


def outcome_row() -> FakeOutcomeDbRow:
    return FakeOutcomeDbRow(
        payload_sha256="d" * 64,
        generated_at=GENERATED_AT,
        outcome_id="outcome-btc-1",
        forecast_id="forecast-btc-1",
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        config_version="team-forecast-outcome-v0",
        resolved_at=GENERATED_AT,
        actual_outcome="yes",
        forecast_error=Decimal("0.380000"),
        brier_score=Decimal("0.144400"),
        paper_pnl=Decimal("0.000000"),
        cost_adjusted_return=Decimal("0.000000"),
        directionally_correct=True,
        profitable_after_cost=False,
        resolution_dispute_flag=False,
        payload_json={"kind": "outcome"},
    )


def test_load_team_forecast_rows_with_psycopg_delegates_through_owned_connection(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeOwnedConnection()
    row = forecast_row()
    calls: list[tuple[Any, str | None, str | None, int | None, str]] = []

    def fake_with_owned_connection(dsn: str, operation: Any) -> tuple[FakeForecastDbRow, ...]:
        assert dsn == LOCAL_DSN
        return operation(connection)

    def fake_load(
        connection_arg: Any,
        *,
        team_id: str | None,
        market_slug: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeForecastDbRow, ...]:
        calls.append((connection_arg, team_id, market_slug, limit, table_name))
        return (row,)

    monkeypatch.setattr(adapter_module, "_with_owned_connection", fake_with_owned_connection)
    monkeypatch.setattr(adapter_module, "load_team_forecast_rows", fake_load)

    loaded = adapter_module.load_team_forecast_rows_with_psycopg(
        LOCAL_DSN,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=10,
        table_name="team_forecasts_archive",
    )

    assert loaded == (row,)
    assert calls == [
        (
            connection,
            "crypto_btc",
            "bitcoin-above-120k",
            10,
            "team_forecasts_archive",
        ),
    ]


def test_load_team_forecast_evidence_rows_with_psycopg_passes_all_filters(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeOwnedConnection()
    row = evidence_row()
    calls: list[tuple[Any, str | None, str | None, str | None, int | None, str]] = []

    def fake_with_owned_connection(dsn: str, operation: Any) -> tuple[FakeEvidenceDbRow, ...]:
        assert dsn == LOCAL_DSN
        return operation(connection)

    def fake_load(
        connection_arg: Any,
        *,
        forecast_id: str | None,
        team_id: str | None,
        market_slug: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeEvidenceDbRow, ...]:
        calls.append(
            (connection_arg, forecast_id, team_id, market_slug, limit, table_name),
        )
        return (row,)

    monkeypatch.setattr(adapter_module, "_with_owned_connection", fake_with_owned_connection)
    monkeypatch.setattr(adapter_module, "load_team_forecast_evidence_rows", fake_load)

    loaded = adapter_module.load_team_forecast_evidence_rows_with_psycopg(
        LOCAL_DSN,
        forecast_id="forecast-btc-1",
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=5,
        table_name="team_forecast_evidence_archive",
    )

    assert loaded == (row,)
    assert calls == [
        (
            connection,
            "forecast-btc-1",
            "crypto_btc",
            "bitcoin-above-120k",
            5,
            "team_forecast_evidence_archive",
        ),
    ]


def test_load_team_forecast_outcome_rows_with_psycopg_delegates_query_options(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeOwnedConnection()
    row = outcome_row()
    calls: list[tuple[Any, str | None, str | None, int | None, str]] = []

    def fake_with_owned_connection(dsn: str, operation: Any) -> tuple[FakeOutcomeDbRow, ...]:
        assert dsn == LOCAL_DSN
        return operation(connection)

    def fake_load(
        connection_arg: Any,
        *,
        team_id: str | None,
        market_slug: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeOutcomeDbRow, ...]:
        calls.append((connection_arg, team_id, market_slug, limit, table_name))
        return (row,)

    monkeypatch.setattr(adapter_module, "_with_owned_connection", fake_with_owned_connection)
    monkeypatch.setattr(adapter_module, "load_team_forecast_outcome_rows", fake_load)

    loaded = adapter_module.load_team_forecast_outcome_rows_with_psycopg(
        LOCAL_DSN,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=2,
        table_name="team_forecast_outcomes_archive",
    )

    assert loaded == (row,)
    assert calls == [
        (
            connection,
            "crypto_btc",
            "bitcoin-above-120k",
            2,
            "team_forecast_outcomes_archive",
        ),
    ]
