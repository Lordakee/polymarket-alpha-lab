from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeSnapshot:
    snapshot_id: str


@dataclass(frozen=True)
class FakeRow:
    snapshot_sha256: str


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
    sys.modules.pop("polymarket_alpha_lab.paper_nav_snapshot_psycopg", None)
    return importlib.import_module("polymarket_alpha_lab.paper_nav_snapshot_psycopg")


def test_insert_opens_psycopg_connection_delegates_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    snapshot = FakeSnapshot(snapshot_id="snapshot-1")
    row = FakeRow(snapshot_sha256="a" * 64)
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, Any, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_insert(connection_arg: Any, snapshot_arg: Any, *, table_name: str) -> FakeRow:
        store_calls.append((connection_arg, snapshot_arg, table_name))
        return row

    monkeypatch.setattr(adapter_module, "insert_paper_nav_snapshot", fake_insert)

    inserted = adapter_module.insert_paper_nav_snapshot_with_psycopg(
        "postgresql://fake.example.invalid/db",
        snapshot,
        table_name="nav_snapshot_archive",
    )

    assert inserted == row
    assert connect_calls == ["postgresql://fake.example.invalid/db"]
    store_connection, store_snapshot, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_snapshot == snapshot
    assert store_table_name == "nav_snapshot_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_opens_psycopg_connection_delegates_query_options_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    snapshot = FakeSnapshot(snapshot_id="snapshot-1")
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, int | None, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_load(
        connection_arg: Any,
        *,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeSnapshot, ...]:
        store_calls.append((connection_arg, limit, table_name))
        return (snapshot,)

    monkeypatch.setattr(adapter_module, "load_paper_nav_snapshots", fake_load)

    loaded = adapter_module.load_paper_nav_snapshots_with_psycopg(
        "postgresql://fake.example.invalid/db",
        limit=10,
        table_name="nav_snapshot_archive",
    )

    assert loaded == (snapshot,)
    assert connect_calls == ["postgresql://fake.example.invalid/db"]
    store_connection, limit, table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert limit == 10
    assert table_name == "nav_snapshot_archive"
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

    def fake_insert(connection_arg: Any, snapshot_arg: Any, *, table_name: str) -> FakeRow:
        cursor = connection_arg.cursor()
        try:
            cursor.execute(
                "insert",
                (
                    {"payload": {"paper_only": True}},
                    ["mark_status"],
                    "scalar",
                    1,
                ),
            )
        finally:
            cursor.close()
        return FakeRow(snapshot_sha256="a" * 64)

    monkeypatch.setattr(adapter_module, "insert_paper_nav_snapshot", fake_insert)

    adapter_module.insert_paper_nav_snapshot_with_psycopg(
        "postgresql://fake.example.invalid/db",
        FakeSnapshot(snapshot_id="snapshot-1"),
    )

    assert connect_calls == ["postgresql://fake.example.invalid/db"]
    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == {"payload": {"paper_only": True}}
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == ["mark_status"]
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

    def fake_insert(connection_arg: Any, snapshot_arg: Any, *, table_name: str) -> FakeRow:
        raise ValueError("store failed without dsn")

    monkeypatch.setattr(adapter_module, "insert_paper_nav_snapshot", fake_insert)

    with pytest.raises(ValueError, match="store failed without dsn"):
        adapter_module.insert_paper_nav_snapshot_with_psycopg(
            "postgresql://fake.example.invalid/db",
            FakeSnapshot(snapshot_id="snapshot-1"),
        )

    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_load_rolls_back_closes_and_reraises_commit_exception(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCommitFailingConnection()
    snapshot = FakeSnapshot(snapshot_id="snapshot-1")
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeSnapshot, ...]:
        return (snapshot,)

    monkeypatch.setattr(adapter_module, "load_paper_nav_snapshots", fake_load)

    with pytest.raises(RuntimeError, match="commit failed without dsn"):
        adapter_module.load_paper_nav_snapshots_with_psycopg(
            "postgresql://fake.example.invalid/db",
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
        adapter_module.load_paper_nav_snapshots_with_psycopg(
            "postgresql://fake.example.invalid/db",
        )

    assert "failed to connect" in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
    assert "example.invalid" not in str(exc_info.value)


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
        adapter_module.load_paper_nav_snapshots_with_psycopg(
            "postgresql://fake.example.invalid/db",
        )

    assert "psycopg is required" in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
