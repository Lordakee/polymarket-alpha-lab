from __future__ import annotations

import ast
import importlib
import inspect
import sys
import traceback
import types
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.supabase_candidate_decision_score_config import (
    CANDIDATE_DECISION_SCORE_DB_DSN_ENV_VAR,
)


LOCAL_DSN = "postgresql://candidate:secret@localhost:54322/polymarket"
REMOTE_DSN = "postgresql://candidate:remote-token@db.remote.example/polymarket"
ADAPTER_MODULE_NAME = "polymarket_alpha_lab.candidate_decision_score_psycopg"


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
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    return importlib.import_module(ADAPTER_MODULE_NAME)


def test_public_exports_include_insert_and_load(adapter_module: types.ModuleType) -> None:
    assert sorted(adapter_module.__all__) == [
        "insert_candidate_decision_score_report_with_psycopg",
        "load_candidate_decision_score_reports_with_psycopg",
    ]


def test_import_does_not_require_psycopg(monkeypatch: pytest.MonkeyPatch) -> None:
    _remove_psycopg_modules(monkeypatch)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg":
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    module = importlib.import_module(ADAPTER_MODULE_NAME)

    assert module.__name__ == ADAPTER_MODULE_NAME


def test_insert_opens_psycopg_connection_delegates_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCursorConnection()
    report = FakeReport(config_version="candidate-decision-score-v0")
    row = FakeRow(report_sha256="a" * 64)
    connect_calls: list[tuple[str, dict[str, Any]]] = []
    store_calls: list[tuple[Any, Any, str]] = []
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn, **kwargs: connect_calls.append((dsn, kwargs)) or connection,
    )

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        store_calls.append((connection_arg, report_arg, table_name))
        return row

    monkeypatch.setattr(
        adapter_module,
        "insert_candidate_decision_score_report",
        fake_insert,
    )

    inserted = adapter_module.insert_candidate_decision_score_report_with_psycopg(
        LOCAL_DSN,
        report,
        table_name="candidate_decision_score_archive",
    )

    assert inserted == row
    assert connect_calls == [(LOCAL_DSN, {})]
    store_connection, store_report, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_report == report
    assert store_table_name == "candidate_decision_score_archive"
    assert connection.cursor_count == 0
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_uses_autocommit_connection_delegates_filters_and_closes_without_commit(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeReport(config_version="candidate-decision-score-v0")
    connect_calls: list[tuple[str, dict[str, Any]]] = []
    store_calls: list[tuple[Any, str | None, str | None, int | None, str]] = []
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn, **kwargs: connect_calls.append((dsn, kwargs)) or connection,
    )

    def fake_load(
        connection_arg: Any,
        *,
        action: str | None,
        primary_team_id: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        store_calls.append((connection_arg, action, primary_team_id, limit, table_name))
        return (report,)

    monkeypatch.setattr(
        adapter_module,
        "load_candidate_decision_score_reports",
        fake_load,
    )

    loaded = adapter_module.load_candidate_decision_score_reports_with_psycopg(
        LOCAL_DSN,
        action="research_ready",
        primary_team_id="alpha_team",
        limit=25,
        table_name="candidate_decision_score_archive",
    )

    assert loaded == (report,)
    assert connect_calls == [(LOCAL_DSN, {"autocommit": True})]
    store_connection, action, primary_team_id, limit, table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert action == "research_ready"
    assert primary_team_id == "alpha_team"
    assert limit == 25
    assert table_name == "candidate_decision_score_archive"
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_dict_and_list_params_are_wrapped_in_jsonb(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCursorConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn, **kwargs: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        cursor = connection_arg.cursor()
        try:
            cursor.execute(
                "insert",
                (
                    ["secondary_team"],
                    {"payload": {"paper_only": True, "readonly": True}},
                    Decimal("0.250000"),
                    "research_ready",
                    2,
                    None,
                ),
            )
            assert cursor.rowcount == 1
        finally:
            cursor.close()
        return FakeRow(report_sha256="a" * 64)

    monkeypatch.setattr(
        adapter_module,
        "insert_candidate_decision_score_report",
        fake_insert,
    )

    adapter_module.insert_candidate_decision_score_report_with_psycopg(
        LOCAL_DSN,
        FakeReport(config_version="candidate-decision-score-v0"),
    )

    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == ["secondary_team"]
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == {"payload": {"paper_only": True, "readonly": True}}
    assert params[2] == Decimal("0.250000")
    assert not isinstance(params[2], FakeJsonb)
    assert params[3] == "research_ready"
    assert params[4] == 2
    assert params[5] is None
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_write_failure_rolls_back_closes_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn, **kwargs: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        raise ValueError("store failed without dsn")

    monkeypatch.setattr(
        adapter_module,
        "insert_candidate_decision_score_report",
        fake_insert,
    )

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_candidate_decision_score_report_with_psycopg(
            LOCAL_DSN,
            FakeReport(config_version="candidate-decision-score-v0"),
        )

    message = str(exc_info.value)
    assert "store failed without dsn" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_read_failure_closes_without_commit_or_rollback(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn, **kwargs: connection)

    def fake_load(
        connection_arg: Any,
        *,
        action: str | None,
        primary_team_id: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        raise ValueError("read failed without dsn")

    monkeypatch.setattr(
        adapter_module,
        "load_candidate_decision_score_reports",
        fake_load,
    )

    with pytest.raises(ValueError) as exc_info:
        adapter_module.load_candidate_decision_score_reports_with_psycopg(
            LOCAL_DSN,
            action="research_ready",
        )

    assert str(exc_info.value) == "read failed without dsn"
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_remote_dsn_is_rejected_before_psycopg_import_without_echoing_secret(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    _remove_psycopg_modules(monkeypatch)

    class ForbiddenPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg" or fullname.startswith("psycopg."):
                raise AssertionError("psycopg must not be imported for invalid DSNs")
            return None

    finder = ForbiddenPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(ValueError) as exc_info:
        adapter_module.load_candidate_decision_score_reports_with_psycopg(REMOTE_DSN)

    message = str(exc_info.value)
    assert CANDIDATE_DECISION_SCORE_DB_DSN_ENV_VAR in message
    assert REMOTE_DSN not in message
    assert "remote-token" not in message
    assert "db.remote.example" not in message


def test_connect_failure_raises_clean_error_without_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    def fail_connect(dsn: str, **kwargs: Any) -> FakeConnection:
        raise RuntimeError(f"connection failed for {dsn}")

    _install_fake_psycopg(monkeypatch, connect=fail_connect)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_candidate_decision_score_reports_with_psycopg(LOCAL_DSN)

    message = str(exc_info.value)
    assert "failed to connect" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "localhost" not in message
    assert "54322" not in message
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__ is True
    formatted = "".join(
        traceback.format_exception(exc_info.type, exc_info.value, exc_info.tb),
    )
    assert "postgresql://" not in formatted
    assert "secret" not in formatted


def test_missing_psycopg_raises_clean_runtime_error_without_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    _remove_psycopg_modules(monkeypatch)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg" or fullname.startswith("psycopg."):
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_candidate_decision_score_reports_with_psycopg(LOCAL_DSN)

    message = str(exc_info.value)
    assert "psycopg is required" in message
    assert "postgres extra" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "localhost" not in message
    assert "54322" not in message


def test_adapter_source_has_no_live_trading_or_non_postgres_network_surface(
    adapter_module: types.ModuleType,
) -> None:
    source = inspect.getsource(adapter_module)
    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncpg",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "urllib",
    }
    forbidden_public_parameter_names = {
        "account",
        "auth",
        "client",
        "exchange",
        "live_trading",
        "order",
        "private_key",
        "signing",
        "wallet",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.partition(".")[0])

    assert imported_roots.isdisjoint(forbidden_import_roots)
    for public_name in adapter_module.__all__:
        parameter_names = set(inspect.signature(getattr(adapter_module, public_name)).parameters)
        assert parameter_names.isdisjoint(forbidden_public_parameter_names)
