from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest


SECRET_DSN = "postgresql://agreement:secret@localhost:54322/polymarket"
REMOTE_DSN = (
    "postgresql://agreement:remote-token@db.remote-supabase.example/polymarket"
)
REMOTE_HOST = "db.remote-supabase.example"
ADAPTER_MODULE_NAME = (
    "polymarket_alpha_lab.probability_selection_scorer_agreement_psycopg"
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
        raise AssertionError("agreement psycopg adapter must not commit")

    def rollback(self) -> None:
        self.rollback_count += 1
        raise AssertionError("agreement psycopg adapter must not rollback")


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
        "insert_probability_selection_scorer_agreement_report_with_psycopg",
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
    report = FakeReport(config_version="probability-selection-scorer-agreement-v0")
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
        "insert_probability_selection_scorer_agreement_report",
        fake_insert,
    )

    inserted = (
        adapter_module.insert_probability_selection_scorer_agreement_report_with_psycopg(
            SECRET_DSN,
            report,
            table_name="probability_selection_scorer_agreement_archive",
        )
    )

    assert inserted == row
    assert connect_calls == [(SECRET_DSN, True)]
    store_connection, store_report, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_report == report
    assert store_table_name == "probability_selection_scorer_agreement_archive"
    assert connection.cursor_count == 0
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_remote_dsn_is_rejected_before_psycopg_import_without_echoing_secret(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    _remove_psycopg_modules(monkeypatch)

    class RejectingPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname.startswith("psycopg"):
                raise AssertionError("psycopg must not be imported for remote DSN")
            return None

    finder = RejectingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_probability_selection_scorer_agreement_report_with_psycopg(
            REMOTE_DSN,
            FakeReport(config_version="probability-selection-scorer-agreement-v0"),
        )

    message = str(exc_info.value)
    assert "POLYMARKET_ALPHA_LAB_PROBABILITY_SELECTION_SCORER_AGREEMENT_DB_DSN" in message
    assert REMOTE_DSN not in message
    assert "remote-token" not in message
    assert REMOTE_HOST not in message


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
    reason_codes = ["aligned"]
    wrapped_cursor.execute("SELECT %s, %s, %s", (payload, reason_codes, "plain"))

    _, params = cursor.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == payload
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == reason_codes
    assert params[2] == "plain"


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

    with pytest.raises(RuntimeError, match="agreement psycopg adapter"):
        adapter_module.insert_probability_selection_scorer_agreement_report_with_psycopg(
            SECRET_DSN,
            FakeReport(config_version="probability-selection-scorer-agreement-v0"),
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
        adapter_module.insert_probability_selection_scorer_agreement_report_with_psycopg(
            SECRET_DSN,
            FakeReport(config_version="probability-selection-scorer-agreement-v0"),
        )

    message = str(exc_info.value)
    assert "failed to connect to the probability selection scorer agreement database" in message
    assert SECRET_DSN not in message
    assert "secret" not in message


def test_insert_success_close_failure_propagates_without_dsn(
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
        "insert_probability_selection_scorer_agreement_report",
        lambda *args, **kwargs: row,
    )

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.insert_probability_selection_scorer_agreement_report_with_psycopg(
            SECRET_DSN,
            FakeReport(config_version="probability-selection-scorer-agreement-v0"),
        )

    message = str(exc_info.value)
    assert "close failed without dsn" in message
    assert SECRET_DSN not in message
    assert "secret" not in message
    assert connection.close_count == 1


def test_insert_operation_failure_close_failure_is_swallowed_without_echoing_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCloseFailingConnection()
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn, *, autocommit=False: connection,
    )

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        raise ValueError("store failed without dsn")

    monkeypatch.setattr(
        adapter_module,
        "insert_probability_selection_scorer_agreement_report",
        fake_insert,
    )

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_probability_selection_scorer_agreement_report_with_psycopg(
            SECRET_DSN,
            FakeReport(config_version="probability-selection-scorer-agreement-v0"),
        )

    message = str(exc_info.value)
    assert "store failed without dsn" in message
    assert "close failed" not in message
    assert SECRET_DSN not in message
    assert "secret" not in message
    assert connection.close_count == 1
