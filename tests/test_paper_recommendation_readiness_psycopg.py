from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeReport:
    config_version: str
    blocked_count: int = 1


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


class FakeRollbackFailingConnection(FakeConnection):
    def rollback(self) -> None:
        self.rollback_count += 1
        raise RuntimeError("rollback failed without dsn")


class FakeJsonb:
    def __init__(self, value: Any) -> None:
        self.value = value


def _install_fake_psycopg(
    monkeypatch: pytest.MonkeyPatch,
    *,
    connect: Any,
) -> None:
    psycopg = types.ModuleType("psycopg")
    psycopg.connect = connect
    types_module = types.ModuleType("psycopg.types")
    json_module = types.ModuleType("psycopg.types.json")
    json_module.Jsonb = FakeJsonb
    monkeypatch.setitem(sys.modules, "psycopg", psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.types", types_module)
    monkeypatch.setitem(sys.modules, "psycopg.types.json", json_module)


def _remove_psycopg_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types.json", raising=False)


@pytest.fixture()
def adapter_module() -> types.ModuleType:
    sys.modules.pop("polymarket_alpha_lab.paper_recommendation_readiness_psycopg", None)
    return importlib.import_module("polymarket_alpha_lab.paper_recommendation_readiness_psycopg")


def test_public_exports_include_insert_and_load(adapter_module: types.ModuleType) -> None:
    assert sorted(adapter_module.__all__) == [
        "insert_paper_recommendation_readiness_report_with_psycopg",
        "load_paper_recommendation_readiness_reports_with_psycopg",
    ]


def test_import_does_not_require_psycopg(monkeypatch: pytest.MonkeyPatch) -> None:
    _remove_psycopg_modules(monkeypatch)
    sys.modules.pop("polymarket_alpha_lab.paper_recommendation_readiness_psycopg", None)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg":
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    module = importlib.import_module("polymarket_alpha_lab.paper_recommendation_readiness_psycopg")

    assert module.__name__ == "polymarket_alpha_lab.paper_recommendation_readiness_psycopg"


def test_insert_opens_psycopg_connection_delegates_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCursorConnection()
    report = FakeReport(config_version="paper-recommendation-readiness-v0")
    row = FakeRow(report_sha256="a" * 64)
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, Any, str]] = []
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connect_calls.append(dsn) or connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        store_calls.append((connection_arg, report_arg, table_name))
        return row

    monkeypatch.setattr(
        adapter_module,
        "insert_paper_recommendation_readiness_report",
        fake_insert,
        raising=False,
    )

    inserted = adapter_module.insert_paper_recommendation_readiness_report_with_psycopg(
        "postgresql://user:secret@example.invalid/db",
        report,
        table_name="readiness_archive",
    )

    assert inserted is None
    assert connect_calls == ["postgresql://user:secret@example.invalid/db"]
    store_connection, store_report, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_report == report
    assert store_table_name == "readiness_archive"
    assert connection.cursor_count == 0
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_opens_psycopg_connection_delegates_query_options_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCursorConnection()
    report = FakeReport(config_version="paper-recommendation-readiness-v0")
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, str | None, int | None, int | None, str]] = []
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connect_calls.append(dsn) or connection)

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        min_blocked_count: int | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        store_calls.append((connection_arg, config_version, min_blocked_count, limit, table_name))
        return (report,)

    monkeypatch.setattr(
        adapter_module,
        "load_paper_recommendation_readiness_reports",
        fake_load,
        raising=False,
    )

    loaded = adapter_module.load_paper_recommendation_readiness_reports_with_psycopg(
        "postgresql://user:secret@example.invalid/db",
        config_version="paper-recommendation-readiness-v0",
        min_blocked_count=1,
        limit=10,
        table_name="readiness_archive",
    )

    assert loaded == (report,)
    assert connect_calls == ["postgresql://user:secret@example.invalid/db"]
    store_connection, config_version, min_blocked_count, limit, table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert config_version == "paper-recommendation-readiness-v0"
    assert min_blocked_count == 1
    assert limit == 10
    assert table_name == "readiness_archive"
    assert connection.cursor_count == 0
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_insert_adapts_json_values_for_psycopg_without_wrapping_scalars(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCursorConnection()
    connect_calls: list[str] = []
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connect_calls.append(dsn) or connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        cursor = connection_arg.cursor()
        try:
            cursor.execute(
                "insert",
                (
                    {"ready": 1, "watch": 1, "blocked": 1},
                    {"payload": {"readonly": True}},
                    Decimal("0.045000"),
                    "paper-recommendation-readiness-v0",
                    3,
                    None,
                ),
            )
        finally:
            cursor.close()
        return FakeRow(report_sha256="a" * 64)

    monkeypatch.setattr(
        adapter_module,
        "insert_paper_recommendation_readiness_report",
        fake_insert,
        raising=False,
    )

    adapter_module.insert_paper_recommendation_readiness_report_with_psycopg(
        "postgresql://user:secret@example.invalid/db",
        FakeReport(config_version="paper-recommendation-readiness-v0"),
    )

    assert connect_calls == ["postgresql://user:secret@example.invalid/db"]
    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == {"ready": 1, "watch": 1, "blocked": 1}
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == {"payload": {"readonly": True}}
    assert params[2] == Decimal("0.045000")
    assert not isinstance(params[2], FakeJsonb)
    assert params[3] == "paper-recommendation-readiness-v0"
    assert params[4] == 3
    assert params[5] is None
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_delegates_filter_and_table_validation_to_store(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCursorConnection()
    store_calls: list[tuple[str | None, int | None, int | None, str]] = []
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        min_blocked_count: int | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        store_calls.append((config_version, min_blocked_count, limit, table_name))
        raise ValueError("store validation failed without dsn")

    monkeypatch.setattr(
        adapter_module,
        "load_paper_recommendation_readiness_reports",
        fake_load,
        raising=False,
    )

    with pytest.raises(ValueError, match="store validation failed"):
        adapter_module.load_paper_recommendation_readiness_reports_with_psycopg(
            "postgresql://user:secret@example.invalid/db",
            config_version="bad config",
            min_blocked_count=-1,
            limit=0,
            table_name="bad-table",
        )

    assert store_calls == [("bad config", -1, 0, "bad-table")]
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_insert_rolls_back_and_closes_on_store_failure(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeRollbackFailingConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        raise RuntimeError("insert failed without dsn")

    monkeypatch.setattr(
        adapter_module,
        "insert_paper_recommendation_readiness_report",
        fake_insert,
        raising=False,
    )

    with pytest.raises(RuntimeError, match="insert failed"):
        adapter_module.insert_paper_recommendation_readiness_report_with_psycopg(
            "postgresql://user:secret@example.invalid/db",
            FakeReport(config_version="paper-recommendation-readiness-v0"),
        )

    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_load_rolls_back_and_closes_on_commit_failure(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCommitFailingConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        min_blocked_count: int | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        return (FakeReport(config_version="paper-recommendation-readiness-v0"),)

    monkeypatch.setattr(
        adapter_module,
        "load_paper_recommendation_readiness_reports",
        fake_load,
        raising=False,
    )

    with pytest.raises(RuntimeError, match="commit failed"):
        adapter_module.load_paper_recommendation_readiness_reports_with_psycopg(
            "postgresql://user:secret@example.invalid/db",
        )

    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_connect_failure_raises_clean_error_without_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    secret_dsn = "postgresql://user:secret-token@example.invalid/db"

    def fail_connect(dsn: str) -> FakeConnection:
        raise RuntimeError(f"connection failed for {dsn}")

    _install_fake_psycopg(monkeypatch, connect=fail_connect)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_recommendation_readiness_reports_with_psycopg(secret_dsn)

    message = str(exc_info.value)
    assert "failed to connect" in message
    assert secret_dsn not in message
    assert "secret-token" not in message


def test_missing_psycopg_raises_clean_error_without_import_time_dependency(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    _remove_psycopg_modules(monkeypatch)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg":
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_recommendation_readiness_reports_with_psycopg(
            "postgresql://user:secret@example.invalid/db",
        )

    message = str(exc_info.value)
    assert "psycopg is required" in message
    assert "postgresql://user:secret" not in message
