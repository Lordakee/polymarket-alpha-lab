from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest


LOCAL_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
REMOTE_SECRET_DSN = "postgresql://sensitive-token@fake.example.invalid/db"


@dataclass(frozen=True)
class FakePacket:
    forecast_id: str


@dataclass(frozen=True)
class FakeRow:
    payload_sha256: str


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

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))

    def fetchall(self) -> list[tuple[Any, ...]]:
        return []

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


class FakeCommitFailingConnection(FakeConnection):
    def commit(self) -> None:
        self.commit_count += 1
        raise RuntimeError("commit failed without dsn")


class FakeJsonb:
    def __init__(self, value: Any) -> None:
        self.value = value


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


def test_insert_opens_psycopg_connection_delegates_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    packet = FakePacket(forecast_id="forecast-btc-1")
    row = FakeRow(payload_sha256="a" * 64)
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, Any, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_insert(connection_arg: Any, packet_arg: Any, *, table_name: str) -> FakeRow:
        store_calls.append((connection_arg, packet_arg, table_name))
        return row

    monkeypatch.setattr(adapter_module, "insert_team_forecast", fake_insert)

    inserted = adapter_module.insert_team_forecast_with_psycopg(
        LOCAL_DSN,
        packet,
        table_name="team_forecasts_archive",
    )

    assert inserted == row
    assert connect_calls == [LOCAL_DSN]
    store_connection, store_packet, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_packet == packet
    assert store_table_name == "team_forecasts_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_opens_psycopg_connection_delegates_query_options_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    packet = FakePacket(forecast_id="forecast-btc-1")
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, str | None, str | None, int | None, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_load(
        connection_arg: Any,
        *,
        team_id: str | None,
        market_slug: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakePacket, ...]:
        store_calls.append(
            (connection_arg, team_id, market_slug, limit, table_name),
        )
        return (packet,)

    monkeypatch.setattr(adapter_module, "load_team_forecasts", fake_load)

    loaded = adapter_module.load_team_forecasts_with_psycopg(
        LOCAL_DSN,
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        limit=10,
        table_name="team_forecasts_archive",
    )

    assert loaded == (packet,)
    assert connect_calls == [LOCAL_DSN]
    store_connection, team_id, market_slug, limit, table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert team_id == "crypto_btc"
    assert market_slug == "bitcoin-above-120k"
    assert limit == 10
    assert table_name == "team_forecasts_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_insert_adapts_json_values_for_psycopg_without_wrapping_scalars(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCursorConnection()
    connect_calls: list[str] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_insert(connection_arg: Any, packet_arg: Any, *, table_name: str) -> FakeRow:
        cursor = connection_arg.cursor()
        try:
            cursor.execute(
                "insert",
                (
                    {"payload": {"paper_only": True, "readonly": True}},
                    ["paper", "report_only"],
                    "scalar",
                    1,
                    None,
                ),
            )
        finally:
            cursor.close()
        return FakeRow(payload_sha256="a" * 64)

    monkeypatch.setattr(adapter_module, "insert_team_forecast", fake_insert)

    adapter_module.insert_team_forecast_with_psycopg(
        LOCAL_DSN,
        FakePacket(forecast_id="forecast-btc-1"),
        table_name="team_forecasts_archive",
    )

    assert connect_calls == [LOCAL_DSN]
    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == {"payload": {"paper_only": True, "readonly": True}}
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == ["paper", "report_only"]
    assert params[2] == "scalar"
    assert params[3] == 1
    assert params[4] is None
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_insert_rolls_back_closes_and_reraises_store_exception(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(connection_arg: Any, packet_arg: Any, *, table_name: str) -> FakeRow:
        raise ValueError("store failed without dsn")

    monkeypatch.setattr(adapter_module, "insert_team_forecast", fake_insert)

    with pytest.raises(ValueError, match="store failed without dsn"):
        adapter_module.insert_team_forecast_with_psycopg(
            LOCAL_DSN,
            FakePacket(forecast_id="forecast-btc-1"),
            table_name="team_forecasts_archive",
        )

    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_load_rolls_back_closes_and_reraises_commit_exception(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCommitFailingConnection()
    packet = FakePacket(forecast_id="forecast-btc-1")
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        team_id: str | None,
        market_slug: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakePacket, ...]:
        return (packet,)

    monkeypatch.setattr(adapter_module, "load_team_forecasts", fake_load)

    with pytest.raises(RuntimeError, match="commit failed without dsn"):
        adapter_module.load_team_forecasts_with_psycopg(
            LOCAL_DSN,
            table_name="team_forecasts_archive",
        )

    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_connect_failure_raises_clean_error_without_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    def fail_connect(dsn: str) -> FakeConnection:
        raise RuntimeError(f"connection failed for {dsn}")

    _install_fake_psycopg(monkeypatch, connect=fail_connect)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_team_forecasts_with_psycopg(
            LOCAL_DSN,
            table_name="team_forecasts_archive",
        )

    assert "failed to connect" in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
    assert "example.invalid" not in str(exc_info.value)


def test_remote_dsn_is_rejected_before_connect_without_echoing_secret(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connect_calls: list[str] = []
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or FakeConnection(),
    )

    with pytest.raises(ValueError) as exc_info:
        adapter_module.load_team_forecasts_with_psycopg(
            REMOTE_SECRET_DSN,
            table_name="team_forecasts_archive",
        )

    assert connect_calls == []
    message = str(exc_info.value)
    assert "local Postgres/Supabase" in message
    assert REMOTE_SECRET_DSN not in message
    assert "sensitive-token" not in message
    assert "fake.example.invalid" not in message


def test_remote_dsn_is_rejected_before_importing_psycopg(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg":
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(ValueError) as exc_info:
        adapter_module.load_team_forecasts_with_psycopg(
            REMOTE_SECRET_DSN,
            table_name="team_forecasts_archive",
        )

    message = str(exc_info.value)
    assert "local Postgres/Supabase" in message
    assert REMOTE_SECRET_DSN not in message
    assert "sensitive-token" not in message
    assert "fake.example.invalid" not in message


def test_missing_psycopg_raises_clean_error_after_dsn_validation(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg":
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_team_forecasts_with_psycopg(
            LOCAL_DSN,
            table_name="team_forecasts_archive",
        )

    assert "psycopg is required" in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
