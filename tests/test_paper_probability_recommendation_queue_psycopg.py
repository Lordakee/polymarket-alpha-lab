from __future__ import annotations

import ast
import importlib
import inspect
import sys
import types
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest

from polymarket_alpha_lab.supabase_paper_probability_recommendation_queue_config import (
    PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_DSN_ENV_VAR,
)

LOCAL_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
REMOTE_HOST = "fake.example.invalid"
REMOTE_SECRET_DSN = f"postgresql://worker:remote-token@{REMOTE_HOST}/polymarket"
STORE_MODULE_NAME = (
    "polymarket_alpha_lab.paper_probability_recommendation_queue_store"
)
ADAPTER_MODULE_NAME = (
    "polymarket_alpha_lab.paper_probability_recommendation_queue_psycopg"
)


@dataclass(frozen=True)
class FakeReport:
    source_config_version: str


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


class FakeCloseFailingConnection(FakeConnection):
    def close(self) -> None:
        self.close_count += 1
        raise RuntimeError("close failed without dsn")


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


def _install_fake_store(
    monkeypatch: pytest.MonkeyPatch,
    *,
    insert: Any | None = None,
    load: Any | None = None,
) -> types.ModuleType:
    store_module = types.ModuleType(STORE_MODULE_NAME)
    store_module.insert_paper_probability_recommendation_queue_report = (
        insert
        if insert is not None
        else _unexpected_store_call("insert")
    )
    store_module.load_paper_probability_recommendation_queue_reports = (
        load if load is not None else _unexpected_store_call("load")
    )
    monkeypatch.setitem(sys.modules, STORE_MODULE_NAME, store_module)
    return store_module


def _unexpected_store_call(name: str) -> Any:
    def raise_unexpected_call(*args: Any, **kwargs: Any) -> None:
        raise AssertionError(f"unexpected {name} store call")

    return raise_unexpected_call


def _import_adapter(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    _install_fake_store(monkeypatch)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    return importlib.import_module(ADAPTER_MODULE_NAME)


def test_importing_adapter_does_not_import_psycopg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg":
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    adapter_module = _import_adapter(monkeypatch)

    assert hasattr(
        adapter_module,
        "insert_paper_probability_recommendation_queue_report_with_psycopg",
    )
    assert sorted(adapter_module.__all__) == [
        "insert_paper_probability_recommendation_queue_report_with_psycopg",
        "load_paper_probability_recommendation_queue_reports_with_psycopg",
    ]


def test_missing_psycopg_error_mentions_install_extra_without_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter_module = _import_adapter(monkeypatch)
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg":
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_probability_recommendation_queue_reports_with_psycopg(
            LOCAL_DSN,
        )

    message = str(exc_info.value)
    assert "psycopg is required" in message
    assert "postgres extra" in message
    assert "postgresql://" not in message
    assert "postgres:postgres" not in message
    assert "localhost" not in message


def test_owned_connection_validates_dsn_before_psycopg_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter_module = _import_adapter(monkeypatch)
    helper_source = inspect.getsource(adapter_module._with_owned_connection)
    first_statement = ast.parse(helper_source).body[0].body[0]

    assert isinstance(first_statement, ast.Expr)
    assert isinstance(first_statement.value, ast.Call)
    assert isinstance(first_statement.value.func, ast.Name)
    assert first_statement.value.func.id == "validate_local_postgres_dsn"
    assert len(first_statement.value.args) == 1
    assert isinstance(first_statement.value.args[0], ast.Name)
    assert first_statement.value.args[0].id == "dsn"
    assert len(first_statement.value.keywords) == 1
    keyword = first_statement.value.keywords[0]
    assert keyword.arg == "env_var_name"
    assert isinstance(keyword.value, ast.Name)
    assert keyword.value.id == "PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_DSN_ENV_VAR"

    monkeypatch.setattr(
        adapter_module,
        "_jsonb_adapter",
        lambda: (_ for _ in ()).throw(AssertionError("_jsonb_adapter must not run")),
    )
    monkeypatch.setattr(
        adapter_module,
        "_connect",
        lambda dsn: (_ for _ in ()).throw(AssertionError("_connect must not run")),
    )

    with pytest.raises(ValueError) as exc_info:
        adapter_module.load_paper_probability_recommendation_queue_reports_with_psycopg(
            REMOTE_SECRET_DSN,
        )

    message = str(exc_info.value)
    assert PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_DSN_ENV_VAR in message
    assert REMOTE_SECRET_DSN not in message
    assert "remote-token" not in message
    assert REMOTE_HOST not in message


def test_remote_dsn_is_rejected_before_psycopg_import_or_connect_without_leak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter_module = _import_adapter(monkeypatch)
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types.json", raising=False)

    class RejectingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname.startswith("psycopg"):
                raise AssertionError("psycopg must not be imported for remote DSN")
            return None

    finder = RejectingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])
    monkeypatch.setattr(
        adapter_module,
        "_connect",
        lambda dsn: (_ for _ in ()).throw(AssertionError("_connect must not run")),
    )
    monkeypatch.setattr(
        adapter_module,
        "_jsonb_adapter",
        lambda: (_ for _ in ()).throw(AssertionError("_jsonb_adapter must not run")),
    )

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_probability_recommendation_queue_report_with_psycopg(
            REMOTE_SECRET_DSN,
            FakeReport(source_config_version="paper-probability-queue-v0"),
        )

    message = str(exc_info.value)
    assert "must point to local Postgres/Supabase" in message
    assert PAPER_PROBABILITY_RECOMMENDATION_QUEUE_DB_DSN_ENV_VAR in message
    assert REMOTE_SECRET_DSN not in message
    assert "remote-token" not in message
    assert REMOTE_HOST not in message


def test_successful_insert_delegates_to_store_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    report = FakeReport(source_config_version="paper-probability-queue-v0")
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

    _install_fake_store(monkeypatch, insert=fake_insert)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    inserted = (
        adapter_module.insert_paper_probability_recommendation_queue_report_with_psycopg(
            LOCAL_DSN,
            report,
            table_name="paper_probability_queue_archive",
        )
    )

    assert inserted is None
    assert connect_calls == [LOCAL_DSN]
    store_connection, store_report, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_report == report
    assert store_table_name == "paper_probability_queue_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_successful_load_delegates_to_store_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    report = FakeReport(source_config_version="paper-probability-queue-v0")
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, str | None, int | None, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_load(
        connection_arg: Any,
        *,
        source_config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        store_calls.append(
            (
                connection_arg,
                source_config_version,
                limit,
                table_name,
            ),
        )
        return (report,)

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    loaded = (
        adapter_module.load_paper_probability_recommendation_queue_reports_with_psycopg(
            LOCAL_DSN,
            source_config_version="paper-probability-queue-v0",
            limit=25,
            table_name="paper_probability_queue_archive",
        )
    )

    assert loaded == (report,)
    assert connect_calls == [LOCAL_DSN]
    store_connection, source_config_version, limit, table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert source_config_version == "paper-probability-queue-v0"
    assert limit == 25
    assert table_name == "paper_probability_queue_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_store_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        raise ValueError("store failed without dsn")

    _install_fake_store(monkeypatch, insert=fake_insert)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_probability_recommendation_queue_report_with_psycopg(
            LOCAL_DSN,
            FakeReport(source_config_version="paper-probability-queue-v0"),
        )

    message = str(exc_info.value)
    assert "store failed without dsn" in message
    assert "postgresql://" not in message
    assert "postgres:postgres" not in message
    assert "localhost" not in message
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_success_close_failure_propagates_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCloseFailingConnection()
    report = FakeReport(source_config_version="paper-probability-queue-v0")
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        source_config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        return (report,)

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_probability_recommendation_queue_reports_with_psycopg(
            LOCAL_DSN,
        )

    message = str(exc_info.value)
    assert "close failed without dsn" in message
    assert "postgresql://" not in message
    assert "postgres:postgres" not in message
    assert "localhost" not in message
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_operation_failure_close_failure_is_swallowed_and_preserves_original_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCloseFailingConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        raise ValueError("store failed without dsn")

    _install_fake_store(monkeypatch, insert=fake_insert)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_probability_recommendation_queue_report_with_psycopg(
            LOCAL_DSN,
            FakeReport(source_config_version="paper-probability-queue-v0"),
        )

    assert str(exc_info.value) == "store failed without dsn"
    assert "close failed" not in str(exc_info.value)
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


@pytest.mark.parametrize(
    "connection",
    (
        FakeRollbackFailingConnection(),
        FakeCloseFailingConnection(),
    ),
)
def test_cleanup_failure_does_not_mask_store_exception(
    monkeypatch: pytest.MonkeyPatch,
    connection: FakeConnection,
) -> None:
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        raise ValueError("store failed without dsn")

    _install_fake_store(monkeypatch, insert=fake_insert)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_probability_recommendation_queue_report_with_psycopg(
            LOCAL_DSN,
            FakeReport(source_config_version="paper-probability-queue-v0"),
        )

    assert str(exc_info.value) == "store failed without dsn"
    assert "rollback failed" not in str(exc_info.value)
    assert "close failed" not in str(exc_info.value)
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_cleanup_failure_does_not_mask_commit_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeCommitAndRollbackFailingConnection(FakeRollbackFailingConnection):
        def commit(self) -> None:
            self.commit_count += 1
            raise RuntimeError("commit failed without dsn")

    connection = FakeCommitAndRollbackFailingConnection()
    report = FakeReport(source_config_version="paper-probability-queue-v0")
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        source_config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        return (report,)

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_probability_recommendation_queue_reports_with_psycopg(
            LOCAL_DSN,
        )

    assert str(exc_info.value) == "commit failed without dsn"
    assert "rollback failed" not in str(exc_info.value)
    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_commit_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCommitFailingConnection()
    report = FakeReport(source_config_version="paper-probability-queue-v0")
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        source_config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        return (report,)

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_probability_recommendation_queue_reports_with_psycopg(
            LOCAL_DSN,
        )

    message = str(exc_info.value)
    assert "commit failed without dsn" in message
    assert "postgresql://" not in message
    assert "postgres:postgres" not in message
    assert "localhost" not in message
    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_connect_failure_raises_redacted_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_connect(dsn: str) -> FakeConnection:
        raise RuntimeError(f"connection failed for {dsn}")

    _install_fake_psycopg(monkeypatch, connect=fail_connect)
    adapter_module = _import_adapter(monkeypatch)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_probability_recommendation_queue_reports_with_psycopg(
            LOCAL_DSN,
        )

    message = str(exc_info.value)
    assert "failed to connect" in message
    assert "postgresql://" not in message
    assert "postgres:postgres" not in message
    assert "localhost" not in message


def test_dict_and_list_params_are_wrapped_in_jsonb(
    monkeypatch: pytest.MonkeyPatch,
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
                    ["fresh_context_needed"],
                    "scalar",
                    3,
                ),
            )
        finally:
            cursor.close()
        return FakeRow(report_sha256="a" * 64)

    _install_fake_store(monkeypatch, insert=fake_insert)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    adapter_module.insert_paper_probability_recommendation_queue_report_with_psycopg(
        LOCAL_DSN,
        FakeReport(source_config_version="paper-probability-queue-v0"),
    )

    assert connect_calls == [LOCAL_DSN]
    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == {"payload": {"paper_only": True}}
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == ["fresh_context_needed"]
    assert params[2] == "scalar"
    assert params[3] == 3
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1
