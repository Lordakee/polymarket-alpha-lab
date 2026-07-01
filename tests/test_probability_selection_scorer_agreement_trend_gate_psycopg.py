from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest


SECRET_DSN = "postgresql://trend-gate:secret@example.invalid/polymarket"
LOCAL_DSN = "postgresql://trend-gate:secret@localhost:54322/postgres"
ADAPTER_MODULE_NAME = (
    "polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_psycopg"
)


@dataclass(frozen=True)
class FakeReport:
    config_version: str


@dataclass(frozen=True)
class FakeRow:
    report_sha256: str


class FakeConnection:
    def __init__(self) -> None:
        self.close_count = 0
        self.commit_count = 0
        self.rollback_count = 0

    def close(self) -> None:
        self.close_count += 1

    def commit(self) -> None:
        self.commit_count += 1
        raise AssertionError("trend-gate psycopg adapter must not commit")

    def rollback(self) -> None:
        self.rollback_count += 1
        raise AssertionError("trend-gate psycopg adapter must not rollback")


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


def _remove_psycopg_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types.json", raising=False)


@pytest.fixture()
def adapter_module() -> types.ModuleType:
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    return importlib.import_module(ADAPTER_MODULE_NAME)


def test_public_exports_include_insert(adapter_module: types.ModuleType) -> None:
    assert sorted(adapter_module.__all__) == [
        "insert_probability_selection_scorer_agreement_trend_gate_report_with_psycopg",
        "load_probability_selection_scorer_agreement_trend_gate_reports_with_psycopg",
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


def test_insert_opens_autocommit_connection_delegates_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCursorConnection()
    report = FakeReport(config_version="probability-selection-scorer-agreement-trend-gate-v0")
    row = FakeRow(report_sha256="a" * 64)
    connect_calls: list[tuple[str, bool]] = []
    store_calls: list[tuple[Any, Any, str]] = []
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn, *, autocommit=False: (
            connect_calls.append((dsn, autocommit)) or connection
        ),
    )

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        store_calls.append((connection_arg, report_arg, table_name))
        return row

    monkeypatch.setattr(
        adapter_module,
        "insert_probability_selection_scorer_agreement_trend_gate_report",
        fake_insert,
    )

    inserted = (
        adapter_module.insert_probability_selection_scorer_agreement_trend_gate_report_with_psycopg(
            LOCAL_DSN,
            report,
            table_name="probability_selection_scorer_agreement_trend_gate_archive",
        )
    )

    assert inserted == row
    assert connect_calls == [(LOCAL_DSN, True)]
    store_connection, store_report, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_report == report
    assert store_table_name == "probability_selection_scorer_agreement_trend_gate_archive"
    assert connection.cursor_count == 0
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_opens_autocommit_connection_delegates_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCursorConnection()
    report = FakeReport(config_version="probability-selection-scorer-agreement-trend-gate-v0")
    connect_calls: list[tuple[str, bool]] = []
    store_calls: list[dict[str, Any]] = []
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn, *, autocommit=False: (
            connect_calls.append((dsn, autocommit)) or connection
        ),
    )

    def fake_load(connection_arg: Any, **kwargs: Any) -> tuple[FakeReport, ...]:
        store_calls.append({"connection": connection_arg, **kwargs})
        return (report,)

    monkeypatch.setattr(
        adapter_module,
        "load_probability_selection_scorer_agreement_trend_gate_reports",
        fake_load,
    )

    loaded = (
        adapter_module.load_probability_selection_scorer_agreement_trend_gate_reports_with_psycopg(
            LOCAL_DSN,
            config_version="probability-selection-scorer-agreement-trend-gate-v0",
            gate_status="watch",
            limit=7,
            table_name="probability_selection_scorer_agreement_trend_gate_archive",
        )
    )

    assert loaded == (report,)
    assert connect_calls == [(LOCAL_DSN, True)]
    assert len(store_calls) == 1
    store_connection = store_calls[0]["connection"]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_calls[0] == {
        "connection": store_connection,
        "config_version": "probability-selection-scorer-agreement-trend-gate-v0",
        "gate_status": "watch",
        "limit": 7,
        "table_name": "probability_selection_scorer_agreement_trend_gate_archive",
    }
    assert connection.cursor_count == 0
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_json_params_are_adapted_for_store_cursor(
    adapter_module: types.ModuleType,
) -> None:
    cursor = FakeCursor()
    connection = adapter_module._PsycopgJsonConnection(
        FakeCursorConnection(),
        FakeJsonb,
    )
    connection.connection.cursor_instance = cursor

    wrapped_cursor = connection.cursor()
    payload = {"report": "aggregate-only"}
    reason_codes = ["latest_probability_selection_scorer_agreement_trend_watch"]
    wrapped_cursor.execute("SELECT %s, %s, %s", (payload, reason_codes, "plain"))

    _, params = cursor.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == payload
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == reason_codes
    assert params[2] == "plain"


def test_adapter_rejects_remote_dsn_before_importing_psycopg(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    _remove_psycopg_modules(monkeypatch)

    class MissingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg":
                raise AssertionError("psycopg must not be imported for invalid remote DSN")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_probability_selection_scorer_agreement_trend_gate_report_with_psycopg(
            SECRET_DSN,
            FakeReport(config_version="probability-selection-scorer-agreement-trend-gate-v0"),
        )

    message = str(exc_info.value)
    assert "must point to local Postgres/Supabase" in message
    assert SECRET_DSN not in message
    assert "secret" not in message


def test_missing_psycopg_error_is_actionable(
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

    with pytest.raises(RuntimeError, match="trend-gate psycopg adapter"):
        adapter_module.insert_probability_selection_scorer_agreement_trend_gate_report_with_psycopg(
            LOCAL_DSN,
            FakeReport(config_version="probability-selection-scorer-agreement-trend-gate-v0"),
        )


def test_connect_failure_redacts_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn, *, autocommit=False: (_ for _ in ()).throw(
            RuntimeError(f"cannot connect to {dsn}"),
        ),
    )

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.insert_probability_selection_scorer_agreement_trend_gate_report_with_psycopg(
            LOCAL_DSN,
            FakeReport(config_version="probability-selection-scorer-agreement-trend-gate-v0"),
        )

    message = str(exc_info.value)
    assert "failed to connect to the probability selection scorer agreement trend-gate database" in message
    assert LOCAL_DSN not in message
    assert "secret" not in message


def test_close_failure_is_suppressed_after_store_success(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCloseFailingConnection()
    row = FakeRow(report_sha256="a" * 64)
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn, *, autocommit=False: connection,
    )
    monkeypatch.setattr(
        adapter_module,
        "insert_probability_selection_scorer_agreement_trend_gate_report",
        lambda *args, **kwargs: row,
    )

    inserted = (
        adapter_module.insert_probability_selection_scorer_agreement_trend_gate_report_with_psycopg(
            LOCAL_DSN,
            FakeReport(config_version="probability-selection-scorer-agreement-trend-gate-v0"),
        )
    )

    assert inserted == row
    assert connection.close_count == 1
