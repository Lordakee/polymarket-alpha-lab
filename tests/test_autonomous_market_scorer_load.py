from __future__ import annotations

import importlib
import sys
import types
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.supabase_autonomous_market_scorer_config import (
    AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR,
    AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR,
    AUTONOMOUS_MARKET_SCORER_DB_TABLE_ENV_VAR,
)


SECRET_DSN = "postgresql://worker:secret@example.invalid/polymarket"


class FakeConnection:
    def __init__(self) -> None:
        self.close_count = 0
        self.commit_count = 0
        self.rollback_count = 0

    def close(self) -> None:
        self.close_count += 1

    def commit(self) -> None:
        self.commit_count += 1
        raise AssertionError("readonly scorer load helper must not commit")

    def rollback(self) -> None:
        self.rollback_count += 1
        raise AssertionError("readonly scorer load helper must not rollback")


def _read_module() -> types.ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.autonomous_market_scorer_load",
    )


def test_disabled_env_returns_empty_tuple_without_connect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, "false")
    connect_calls: list[str] = []

    reports = read_module.load_autonomous_market_scorer_reports_from_env(
        limit=10,
        connect=lambda dsn: connect_calls.append(dsn) or FakeConnection(),
    )

    assert reports == ()
    assert type(reports) is tuple
    assert connect_calls == []


def test_missing_enabled_env_returns_empty_tuple_without_connect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    monkeypatch.delenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, raising=False)
    connect_calls: list[str] = []

    reports = read_module.load_autonomous_market_scorer_reports_from_env(
        limit=10,
        connect=lambda dsn: connect_calls.append(dsn) or FakeConnection(),
    )

    assert reports == ()
    assert type(reports) is tuple
    assert connect_calls == []


@pytest.mark.parametrize("limit", (0, -1, True, 1.5, "10"))
def test_invalid_limit_is_rejected_before_env_or_connect(
    monkeypatch: pytest.MonkeyPatch,
    limit: object,
) -> None:
    read_module = _read_module()
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, SECRET_DSN)
    env_calls = 0
    connect_calls = 0

    def read_env() -> object:
        nonlocal env_calls
        env_calls += 1
        return {}

    def connect(_dsn: str) -> FakeConnection:
        nonlocal connect_calls
        connect_calls += 1
        return FakeConnection()

    monkeypatch.setattr(read_module, "from_autonomous_market_scorer_db_env", read_env)

    with pytest.raises(ValueError, match="limit"):
        read_module.load_autonomous_market_scorer_reports_from_env(
            limit=limit,
            connect=connect,
        )

    assert env_calls == 0
    assert connect_calls == 0


def test_enabled_env_loads_configured_table_limit_and_closes_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    connection = FakeConnection()
    report_a = object()
    report_b = object()
    load_calls: list[dict[str, object]] = []
    connect_calls: list[str] = []

    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, SECRET_DSN)
    monkeypatch.setenv(
        AUTONOMOUS_MARKET_SCORER_DB_TABLE_ENV_VAR,
        "autonomous_market_scorer_archive",
    )

    def connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        return connection

    def load_reports(received_connection: object, **kwargs: object) -> list[object]:
        load_calls.append({"connection": received_connection, **kwargs})
        return [report_a, report_b]

    reports = read_module.load_autonomous_market_scorer_reports_from_env(
        limit=25,
        connect=connect,
        loader=load_reports,
    )

    assert reports == (report_a, report_b)
    assert type(reports) is tuple
    assert connect_calls == [SECRET_DSN]
    assert load_calls == [
        {
            "connection": connection,
            "limit": 25,
            "table_name": "autonomous_market_scorer_archive",
        },
    ]
    assert connection.close_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_enabled_config_without_dsn_fails_before_connect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    connect_calls = 0

    def env_config() -> SimpleNamespace:
        return SimpleNamespace(
            enabled=True,
            dsn=None,
            table_name="autonomous_market_scorer_reports",
        )

    def connect(_dsn: str) -> FakeConnection:
        nonlocal connect_calls
        connect_calls += 1
        return FakeConnection()

    monkeypatch.setattr(read_module, "from_autonomous_market_scorer_db_env", env_config)

    with pytest.raises(RuntimeError, match="DB DSN is required"):
        read_module.load_autonomous_market_scorer_reports_from_env(
            limit=5,
            connect=connect,
        )

    assert connect_calls == 0


def test_load_error_is_redacted_and_connection_is_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    connection = FakeConnection()
    secret_table = "autonomous_market_scorer_archive"
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, SECRET_DSN)
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_TABLE_ENV_VAR, secret_table)

    def load_reports(_connection: object, **_kwargs: object) -> tuple[object, ...]:
        raise RuntimeError(
            f"failed for {SECRET_DSN} table {secret_table} "
            "question Who wins? market market-slug hash "
            f"{'a' * 64}",
        )

    with pytest.raises(RuntimeError) as exc_info:
        read_module.load_autonomous_market_scorer_reports_from_env(
            limit=5,
            connect=lambda _dsn: connection,
            loader=load_reports,
        )

    message = str(exc_info.value)
    assert "failed to load autonomous market scorer reports" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message
    assert secret_table not in message
    assert "Who wins?" not in message
    assert "market-slug" not in message
    assert "a" * 64 not in message
    assert connection.close_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_connect_error_is_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    secret_table = "autonomous_market_scorer_archive"
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, SECRET_DSN)
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_TABLE_ENV_VAR, secret_table)

    def connect(_dsn: str) -> FakeConnection:
        raise RuntimeError(f"connect failed for {SECRET_DSN} and {secret_table}")

    with pytest.raises(RuntimeError) as exc_info:
        read_module.load_autonomous_market_scorer_reports_from_env(
            limit=5,
            connect=connect,
        )

    message = str(exc_info.value)
    assert "failed to connect to the autonomous market scorer database" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message
    assert secret_table not in message


def test_injected_connect_psycopg_prefix_error_is_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    secret_table = "autonomous_market_scorer_archive"
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, SECRET_DSN)
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_TABLE_ENV_VAR, secret_table)

    def connect(_dsn: str) -> FakeConnection:
        raise RuntimeError(
            f"psycopg is required but leaked {SECRET_DSN} table={secret_table} "
            "question=Who wins? market=market-slug "
            f"report_sha256={'a' * 64}",
        )

    with pytest.raises(RuntimeError) as exc_info:
        read_module.load_autonomous_market_scorer_reports_from_env(
            limit=5,
            connect=connect,
        )

    message = str(exc_info.value)
    assert "failed to connect to the autonomous market scorer database" in message
    assert "psycopg is required but leaked" not in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message
    assert secret_table not in message
    assert "Who wins?" not in message
    assert "market-slug" not in message
    assert "a" * 64 not in message


def test_missing_psycopg_message_does_not_leak_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, SECRET_DSN)
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg":
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(RuntimeError) as exc_info:
        read_module.load_autonomous_market_scorer_reports_from_env(limit=5)

    message = str(exc_info.value)
    assert "psycopg is required" in message
    assert "postgres extra" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message


def test_default_connect_uses_psycopg_autocommit_and_no_commit_or_rollback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    connection = FakeConnection()
    connect_calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(AUTONOMOUS_MARKET_SCORER_DB_DSN_ENV_VAR, SECRET_DSN)

    def connect(dsn: str, **kwargs: object) -> FakeConnection:
        connect_calls.append((dsn, kwargs))
        return connection

    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=connect))

    reports = read_module.load_autonomous_market_scorer_reports_from_env(
        limit=3,
        loader=lambda _connection, **_kwargs: (object(),),
    )

    assert len(reports) == 1
    assert type(reports) is tuple
    assert connect_calls == [(SECRET_DSN, {"autocommit": True})]
    assert connection.close_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
