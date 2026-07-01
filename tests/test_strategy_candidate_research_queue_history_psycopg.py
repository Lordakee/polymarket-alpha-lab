from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest


LOCAL_SUPABASE_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
REMOTE_SECRET_DSN = (
    "postgresql://worker:super-secret-token@db.remote-supabase.co:5432/polymarket"
)
DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN"
STORE_MODULE_NAME = (
    "polymarket_alpha_lab.strategy_candidate_research_queue_history_store"
)
ADAPTER_MODULE_NAME = (
    "polymarket_alpha_lab.strategy_candidate_research_queue_history_psycopg"
)


@dataclass(frozen=True)
class FakeReport:
    source_report_count: int


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


class FakeCommitFailingConnection(FakeConnection):
    def commit(self) -> None:
        self.commit_count += 1
        raise RuntimeError("commit failed without dsn")


class FakeCloseFailingConnection(FakeConnection):
    def close(self) -> None:
        self.close_count += 1
        raise RuntimeError("close failed without dsn")


class FakeCommitAndCloseFailingConnection(FakeCloseFailingConnection):
    def commit(self) -> None:
        self.commit_count += 1
        raise RuntimeError("commit failed without dsn")


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


class FakeJsonb:
    def __init__(self, value: Any) -> None:
        self.value = value


def _install_fake_psycopg(monkeypatch: pytest.MonkeyPatch, *, connect: Any) -> None:
    psycopg = types.SimpleNamespace(connect=connect)
    json_module = types.SimpleNamespace(Jsonb=FakeJsonb)
    monkeypatch.setitem(sys.modules, "psycopg", psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.types.json", json_module)


def _forbid_psycopg_import(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types.json", raising=False)

    class ForbiddenPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg" or fullname.startswith("psycopg."):
                raise AssertionError("psycopg imported before dsn validation")
            return None

    monkeypatch.setattr(sys, "meta_path", [ForbiddenPsycopgFinder(), *sys.meta_path])


def _install_fake_store(
    monkeypatch: pytest.MonkeyPatch,
    *,
    insert: Any | None = None,
    load: Any | None = None,
) -> None:
    store_module = types.ModuleType(STORE_MODULE_NAME)
    store_module.DEFAULT_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_TABLE = (
        "paper_strategy_candidate_research_queue_history_reports"
    )
    store_module.insert_paper_strategy_candidate_research_queue_history_report = (
        insert if insert is not None else _unexpected_store_call("insert")
    )
    store_module.load_paper_strategy_candidate_research_queue_history_reports = (
        load if load is not None else _unexpected_store_call("load")
    )
    monkeypatch.setitem(sys.modules, STORE_MODULE_NAME, store_module)


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

    adapter_module = _import_adapter(monkeypatch)

    assert hasattr(
        adapter_module,
        "insert_paper_strategy_candidate_research_queue_history_report_with_psycopg",
    )


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

    monkeypatch.setattr(sys, "meta_path", [MissingPsycopgFinder(), *sys.meta_path])

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_strategy_candidate_research_queue_history_reports_with_psycopg(
            LOCAL_SUPABASE_DSN,
        )

    message = str(exc_info.value)
    assert "psycopg is required" in message
    assert "postgres extra" in message
    assert "postgresql://" not in message
    assert "postgres:postgres" not in message
    assert "localhost" not in message


def test_successful_insert_delegates_to_store_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    report = FakeReport(source_report_count=3)
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
        adapter_module.insert_paper_strategy_candidate_research_queue_history_report_with_psycopg(
            LOCAL_SUPABASE_DSN,
            report,
            table_name="paper_strategy_candidate_queue_history_archive",
        )
    )

    assert inserted == row
    assert connect_calls == [LOCAL_SUPABASE_DSN]
    store_connection, store_report, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_report == report
    assert store_table_name == "paper_strategy_candidate_queue_history_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_successful_load_delegates_filters_to_store_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    report = FakeReport(source_report_count=3)
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, str | None, str | None, int | None, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_load(
        connection_arg: Any,
        *,
        latest_action_status: str | None,
        latest_research_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        store_calls.append(
            (
                connection_arg,
                latest_action_status,
                latest_research_status,
                limit,
                table_name,
            ),
        )
        return (report,)

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    loaded = (
        adapter_module.load_paper_strategy_candidate_research_queue_history_reports_with_psycopg(
            LOCAL_SUPABASE_DSN,
            latest_action_status="paper_review_ready",
            latest_research_status="research_ready",
            limit=25,
            table_name="paper_strategy_candidate_queue_history_archive",
        )
    )

    assert loaded == (report,)
    assert connect_calls == [LOCAL_SUPABASE_DSN]
    (
        store_connection,
        latest_action_status,
        latest_research_status,
        limit,
        table_name,
    ) = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert latest_action_status == "paper_review_ready"
    assert latest_research_status == "research_ready"
    assert limit == 25
    assert table_name == "paper_strategy_candidate_queue_history_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        latest_action_status: str | None,
        latest_research_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        raise ValueError("store failed without dsn")

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(ValueError) as exc_info:
        adapter_module.load_paper_strategy_candidate_research_queue_history_reports_with_psycopg(
            LOCAL_SUPABASE_DSN,
        )

    message = str(exc_info.value)
    assert "store failed without dsn" in message
    assert "postgresql://" not in message
    assert "postgres:postgres" not in message
    assert "localhost" not in message
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_load_commit_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCommitFailingConnection()
    report = FakeReport(source_report_count=3)
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        latest_action_status: str | None,
        latest_research_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        return (report,)

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_strategy_candidate_research_queue_history_reports_with_psycopg(
            LOCAL_SUPABASE_DSN,
        )

    message = str(exc_info.value)
    assert "commit failed without dsn" in message
    assert "postgresql://" not in message
    assert "postgres:postgres" not in message
    assert "localhost" not in message
    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_load_commit_failure_close_failure_is_swallowed_without_echoing_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCommitAndCloseFailingConnection()
    report = FakeReport(source_report_count=3)
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        latest_action_status: str | None,
        latest_research_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        return (report,)

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_strategy_candidate_research_queue_history_reports_with_psycopg(
            LOCAL_SUPABASE_DSN,
        )

    message = str(exc_info.value)
    assert "commit failed without dsn" in message
    assert "close failed" not in message
    assert "postgresql://" not in message
    assert "postgres:postgres" not in message
    assert "localhost" not in message
    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_load_success_close_failure_propagates_without_echoing_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCloseFailingConnection()
    report = FakeReport(source_report_count=3)
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        latest_action_status: str | None,
        latest_research_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        return (report,)

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_strategy_candidate_research_queue_history_reports_with_psycopg(
            LOCAL_SUPABASE_DSN,
        )

    message = str(exc_info.value)
    assert "close failed without dsn" in message
    assert "postgresql://" not in message
    assert "postgres:postgres" not in message
    assert "localhost" not in message
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_operation_failure_close_failure_is_swallowed_without_echoing_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCloseFailingConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        latest_action_status: str | None,
        latest_research_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        raise ValueError("store failed without dsn")

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(ValueError) as exc_info:
        adapter_module.load_paper_strategy_candidate_research_queue_history_reports_with_psycopg(
            LOCAL_SUPABASE_DSN,
        )

    message = str(exc_info.value)
    assert "store failed without dsn" in message
    assert "close failed" not in message
    assert "postgresql://" not in message
    assert "postgres:postgres" not in message
    assert "localhost" not in message
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_load_rejects_remote_dsn_before_psycopg_import_without_echoing_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter_module = _import_adapter(monkeypatch)
    _forbid_psycopg_import(monkeypatch)

    with pytest.raises(ValueError) as exc_info:
        adapter_module.load_paper_strategy_candidate_research_queue_history_reports_with_psycopg(
            REMOTE_SECRET_DSN,
        )

    message = str(exc_info.value)
    assert DSN_ENV_VAR in message
    assert REMOTE_SECRET_DSN not in message
    assert "postgresql://" not in message
    assert "super-secret-token" not in message
    assert "db.remote-supabase.co" not in message


def test_connect_failure_raises_redacted_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_connect(dsn: str) -> FakeConnection:
        raise RuntimeError(f"connection failed for {dsn}")

    _install_fake_psycopg(monkeypatch, connect=fail_connect)
    adapter_module = _import_adapter(monkeypatch)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_strategy_candidate_research_queue_history_reports_with_psycopg(
            LOCAL_SUPABASE_DSN,
        )

    message = str(exc_info.value)
    assert "failed to connect" in message
    assert "postgresql://" not in message
    assert "postgres:postgres" not in message
    assert "localhost" not in message


def test_json_params_are_wrapped_as_jsonb(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = FakeCursorConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)
    _install_fake_store(monkeypatch)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)
    wrapped = adapter_module._PsycopgJsonConnection(connection, FakeJsonb)

    cursor = wrapped.cursor()
    cursor.execute("select %s, %s, %s", ({"a": 1}, [1, 2], "plain"))

    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == {"a": 1}
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == [1, 2]
    assert params[2] == "plain"
