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
REMOTE_SECRET_DSN = "postgresql://sensitive-token@fake.example.invalid/db"
GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


@dataclass(frozen=True)
class FakeRouteReport:
    market_slug: str


@dataclass(frozen=True)
class FakeRouteDbRow:
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


class FakeConnection:
    def __init__(self) -> None:
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.close_count += 1


class FakeCursor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.close_count = 0
        self.rowcount = 1

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))

    def close(self) -> None:
        self.close_count += 1


class FakeCursorConnection(FakeConnection):
    def __init__(self) -> None:
        super().__init__()
        self.cursor_instance = FakeCursor()
        self.cursor_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance


class FakeJsonb:
    def __init__(self, value: Any) -> None:
        self.value = value


def route_row(**overrides: Any) -> FakeRouteDbRow:
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
    return FakeRouteDbRow(**values)


def _install_fake_psycopg(
    monkeypatch: pytest.MonkeyPatch,
    *,
    connect: Any,
) -> None:
    psycopg = types.SimpleNamespace(connect=connect)
    json_module = types.SimpleNamespace(Jsonb=FakeJsonb)
    monkeypatch.setitem(sys.modules, "psycopg", psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.types.json", json_module)


@pytest.fixture()
def adapter_module() -> types.ModuleType:
    sys.modules.pop("polymarket_alpha_lab.team_forecast_psycopg", None)
    return importlib.import_module("polymarket_alpha_lab.team_forecast_psycopg")


def test_insert_team_market_route_opens_psycopg_converts_delegates_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeRouteReport(market_slug="bitcoin-above-120k")
    row = route_row()
    connect_calls: list[str] = []
    converter_calls: list[Any] = []
    store_calls: list[tuple[Any, Any, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_converter(report_arg: Any) -> FakeRouteDbRow:
        converter_calls.append(report_arg)
        return row

    def fake_insert(connection_arg: Any, row_arg: Any, *, table_name: str) -> FakeRouteDbRow:
        store_calls.append((connection_arg, row_arg, table_name))
        return row

    monkeypatch.setattr(adapter_module, "team_route_to_db_row", fake_converter, raising=False)
    monkeypatch.setattr(adapter_module, "insert_team_market_route", fake_insert, raising=False)

    inserted = adapter_module.insert_team_market_route_with_psycopg(
        LOCAL_DSN,
        report,
        table_name="team_market_routes_archive",
    )

    assert inserted == row
    assert connect_calls == [LOCAL_DSN]
    assert converter_calls == [report]
    store_connection, store_row, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_row == row
    assert store_table_name == "team_market_routes_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_insert_team_market_route_real_store_path_delegates_psycopg_cursor_rowcount(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    store_module = importlib.import_module("polymarket_alpha_lab.team_forecast_store")
    connection = FakeCursorConnection()
    row = route_row()
    connect_calls: list[str] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )
    monkeypatch.setattr(adapter_module, "team_route_to_db_row", lambda report_arg: row, raising=False)
    monkeypatch.setattr(store_module, "TeamMarketRouteDbRow", FakeRouteDbRow)

    inserted = adapter_module.insert_team_market_route_with_psycopg(
        LOCAL_DSN,
        FakeRouteReport(market_slug="bitcoin-above-120k"),
        table_name="team_market_routes_archive",
    )

    assert inserted == row
    assert connect_calls == [LOCAL_DSN]
    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_insert_team_market_route_remote_dsn_is_rejected_before_connect_without_echoing_secret(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connect_calls: list[str] = []
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or FakeConnection(),
    )
    monkeypatch.setattr(
        adapter_module,
        "team_route_to_db_row",
        lambda report_arg: route_row(),
        raising=False,
    )

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_team_market_route_with_psycopg(
            REMOTE_SECRET_DSN,
            FakeRouteReport(market_slug="bitcoin-above-120k"),
            table_name="team_market_routes_archive",
        )

    assert connect_calls == []
    message = str(exc_info.value)
    assert "local Postgres/Supabase" in message
    assert REMOTE_SECRET_DSN not in message
    assert "sensitive-token" not in message
    assert "fake.example.invalid" not in message


def test_public_exports_include_team_market_route_psycopg_wrapper(
    adapter_module: types.ModuleType,
) -> None:
    assert "insert_team_market_route_with_psycopg" in adapter_module.__all__


def test_missing_store_module_route_public_wrapper_raises_clean_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "polymarket_alpha_lab.team_forecast_store", None)
    sys.modules.pop("polymarket_alpha_lab.team_forecast_psycopg", None)
    module = importlib.import_module("polymarket_alpha_lab.team_forecast_psycopg")
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)
    monkeypatch.setattr(
        module,
        "team_route_to_db_row",
        lambda report_arg: route_row(),
        raising=False,
    )

    with pytest.raises(RuntimeError, match="team forecast store module is required"):
        module.insert_team_market_route_with_psycopg(
            LOCAL_DSN,
            FakeRouteReport(market_slug="bitcoin-above-120k"),
            table_name="team_market_routes",
        )
