from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest


SECRET_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
STORE_MODULE_NAME = (
    "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store"
)
ADAPTER_MODULE_NAME = (
    "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_psycopg"
)


@dataclass(frozen=True)
class FakeReport:
    latest_to_gate_status: str


@dataclass(frozen=True)
class FakeResult:
    inserted: bool


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


def _install_fake_store(
    monkeypatch: pytest.MonkeyPatch,
    *,
    insert: Any | None = None,
    load: Any | None = None,
) -> None:
    store_module = types.ModuleType(STORE_MODULE_NAME)
    store_module.DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_REPORTS_TABLE = (
        "paper_autonomous_screening_gate_transition_reports"
    )
    store_module.insert_paper_autonomous_screening_decision_support_gate_transition_report_with_result = (
        insert if insert is not None else _unexpected_store_call("insert")
    )
    store_module.load_paper_autonomous_screening_decision_support_gate_transition_reports = (
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
        "insert_paper_autonomous_screening_decision_support_gate_transition_report_with_psycopg",
    )
    assert hasattr(
        adapter_module,
        "load_paper_autonomous_screening_decision_support_gate_transition_reports_with_psycopg",
    )


def test_successful_insert_delegates_to_store_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    report = FakeReport(latest_to_gate_status="watch")
    result = FakeResult(inserted=True)
    connect_calls: list[tuple[str, dict[str, object]]] = []
    store_calls: list[tuple[Any, Any, str]] = []

    def connect(dsn: str, **kwargs: object) -> FakeConnection:
        connect_calls.append((dsn, kwargs))
        return connection

    _install_fake_psycopg(monkeypatch, connect=connect)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeResult:
        store_calls.append((connection_arg, report_arg, table_name))
        return result

    _install_fake_store(monkeypatch, insert=fake_insert)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    inserted = (
        adapter_module.insert_paper_autonomous_screening_decision_support_gate_transition_report_with_psycopg(
            SECRET_DSN,
            report,
            table_name="paper_autonomous_screening_gate_transition_archive",
        )
    )

    assert inserted == result
    assert connect_calls == [(SECRET_DSN, {})]
    store_connection, store_report, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_report == report
    assert store_table_name == "paper_autonomous_screening_gate_transition_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_successful_load_uses_autocommit_connection_delegates_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    report = FakeReport(latest_to_gate_status="watch")
    connect_calls: list[tuple[str, dict[str, object]]] = []
    store_calls: list[dict[str, object]] = []

    def connect(dsn: str, **kwargs: object) -> FakeConnection:
        connect_calls.append((dsn, kwargs))
        return connection

    _install_fake_psycopg(monkeypatch, connect=connect)

    def fake_load(connection_arg: Any, **kwargs: object) -> tuple[FakeReport, ...]:
        store_calls.append({"connection": connection_arg, **kwargs})
        return (report,)

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    loaded = (
        adapter_module.load_paper_autonomous_screening_decision_support_gate_transition_reports_with_psycopg(
            SECRET_DSN,
            config_version="transition-v0",
            latest_to_gate_status="watch",
            limit=3,
            table_name="paper_autonomous_screening_gate_transition_archive",
        )
    )

    assert loaded == (report,)
    assert connect_calls == [(SECRET_DSN, {"autocommit": True})]
    assert store_calls == [
        {
            "connection": connection,
            "config_version": "transition-v0",
            "latest_from_gate_status": None,
            "latest_to_gate_status": "watch",
            "limit": 3,
            "table_name": "paper_autonomous_screening_gate_transition_archive",
        },
    ]
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_store_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn, **kwargs: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeResult:
        raise ValueError("store failed without dsn")

    _install_fake_store(monkeypatch, insert=fake_insert)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_autonomous_screening_decision_support_gate_transition_report_with_psycopg(
            SECRET_DSN,
            FakeReport(latest_to_gate_status="watch"),
        )

    message = str(exc_info.value)
    assert "store failed without dsn" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_commit_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCommitFailingConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn, **kwargs: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeResult:
        return FakeResult(inserted=True)

    _install_fake_store(monkeypatch, insert=fake_insert)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.insert_paper_autonomous_screening_decision_support_gate_transition_report_with_psycopg(
            SECRET_DSN,
            FakeReport(latest_to_gate_status="watch"),
        )

    message = str(exc_info.value)
    assert "commit failed without dsn" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message
    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_connect_failure_raises_redacted_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_connect(dsn: str, **kwargs: object) -> FakeConnection:
        raise RuntimeError(f"connection failed for {dsn}")

    _install_fake_psycopg(monkeypatch, connect=fail_connect)
    adapter_module = _import_adapter(monkeypatch)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.insert_paper_autonomous_screening_decision_support_gate_transition_report_with_psycopg(
            SECRET_DSN,
            FakeReport(latest_to_gate_status="watch"),
        )

    message = str(exc_info.value)
    assert "failed to connect" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message


def test_dict_and_list_params_are_wrapped_in_jsonb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCursorConnection()
    connect_calls: list[str] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn, **kwargs: connect_calls.append(dsn) or connection,
    )

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeResult:
        cursor = connection_arg.cursor()
        try:
            cursor.execute(
                "insert",
                (
                    {"payload": {"paper_only": True}},
                    ["screening_gate_passed"],
                    "scalar",
                    1,
                ),
            )
        finally:
            cursor.close()
        return FakeResult(inserted=True)

    _install_fake_store(monkeypatch, insert=fake_insert)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    adapter_module.insert_paper_autonomous_screening_decision_support_gate_transition_report_with_psycopg(
        SECRET_DSN,
        FakeReport(latest_to_gate_status="watch"),
    )

    assert connect_calls == [SECRET_DSN]
    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == {"payload": {"paper_only": True}}
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == ["screening_gate_passed"]
    assert params[2] == "scalar"
    assert params[3] == 1
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_public_exports_include_insert_and_load() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_psycopg as adapter_module

    assert adapter_module.__all__ == (
        "insert_paper_autonomous_screening_decision_support_gate_transition_report_with_psycopg",
        "load_paper_autonomous_screening_decision_support_gate_transition_reports_with_psycopg",
    )
