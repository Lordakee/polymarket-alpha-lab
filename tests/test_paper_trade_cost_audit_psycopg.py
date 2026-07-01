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
class FakeReport:
    config_version: str


@dataclass(frozen=True)
class FakeRow:
    report_sha256: str


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
    sys.modules.pop("polymarket_alpha_lab.paper_trade_cost_audit_psycopg", None)
    return importlib.import_module("polymarket_alpha_lab.paper_trade_cost_audit_psycopg")


def test_insert_opens_psycopg_connection_delegates_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeReport(config_version="paper-trade-cost-audit-db-v0")
    row = FakeRow(report_sha256="a" * 64)
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, Any, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        store_calls.append((connection_arg, report_arg, table_name))
        return row

    monkeypatch.setattr(
        adapter_module,
        "insert_paper_trade_cost_audit_report",
        fake_insert,
    )

    inserted = adapter_module.insert_paper_trade_cost_audit_report_with_psycopg(
        LOCAL_DSN,
        report,
        table_name="paper_trade_cost_audit_archive",
    )

    assert inserted == row
    assert connect_calls == [LOCAL_DSN]
    store_connection, store_report, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_report == report
    assert store_table_name == "paper_trade_cost_audit_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_opens_psycopg_connection_delegates_query_options_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeReport(config_version="paper-trade-cost-audit-db-v0")
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, str | None, int | None, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        store_calls.append((connection_arg, config_version, limit, table_name))
        return (report,)

    monkeypatch.setattr(
        adapter_module,
        "load_paper_trade_cost_audit_reports",
        fake_load,
    )

    loaded = adapter_module.load_paper_trade_cost_audit_reports_with_psycopg(
        LOCAL_DSN,
        config_version="paper-trade-cost-audit-db-v0",
        limit=10,
        table_name="paper_trade_cost_audit_archive",
    )

    assert loaded == (report,)
    assert connect_calls == [LOCAL_DSN]
    store_connection, config_version, limit, table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert config_version == "paper-trade-cost-audit-db-v0"
    assert limit == 10
    assert table_name == "paper_trade_cost_audit_archive"
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

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        cursor = connection_arg.cursor()
        try:
            cursor.execute(
                "insert",
                (
                    {"payload": {"paper_only": True}},
                    ["paper", "readonly"],
                    "scalar",
                    1,
                ),
            )
        finally:
            cursor.close()
        return FakeRow(report_sha256="a" * 64)

    monkeypatch.setattr(
        adapter_module,
        "insert_paper_trade_cost_audit_report",
        fake_insert,
    )

    adapter_module.insert_paper_trade_cost_audit_report_with_psycopg(
        LOCAL_DSN,
        FakeReport(config_version="paper-trade-cost-audit-db-v0"),
    )

    assert connect_calls == [LOCAL_DSN]
    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == {"payload": {"paper_only": True}}
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == ["paper", "readonly"]
    assert params[2] == "scalar"
    assert params[3] == 1
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_insert_rolls_back_closes_and_reraises_store_exception(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        raise ValueError("store failed without dsn")

    monkeypatch.setattr(
        adapter_module,
        "insert_paper_trade_cost_audit_report",
        fake_insert,
    )

    with pytest.raises(ValueError, match="store failed without dsn"):
        adapter_module.insert_paper_trade_cost_audit_report_with_psycopg(
            LOCAL_DSN,
            FakeReport(config_version="paper-trade-cost-audit-db-v0"),
        )

    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_load_rolls_back_closes_and_reraises_commit_exception(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCommitFailingConnection()
    report = FakeReport(config_version="paper-trade-cost-audit-db-v0")
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        return (report,)

    monkeypatch.setattr(
        adapter_module,
        "load_paper_trade_cost_audit_reports",
        fake_load,
    )

    with pytest.raises(RuntimeError, match="commit failed without dsn"):
        adapter_module.load_paper_trade_cost_audit_reports_with_psycopg(LOCAL_DSN)

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
        adapter_module.load_paper_trade_cost_audit_reports_with_psycopg(LOCAL_DSN)

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
        adapter_module.load_paper_trade_cost_audit_reports_with_psycopg(
            REMOTE_SECRET_DSN,
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
        adapter_module.load_paper_trade_cost_audit_reports_with_psycopg(
            REMOTE_SECRET_DSN,
        )

    message = str(exc_info.value)
    assert "local Postgres/Supabase" in message
    assert REMOTE_SECRET_DSN not in message
    assert "sensitive-token" not in message
    assert "fake.example.invalid" not in message


def test_missing_psycopg_raises_clean_error_without_import_time_dependency(
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
        adapter_module.load_paper_trade_cost_audit_reports_with_psycopg(LOCAL_DSN)

    assert "psycopg is required" in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
