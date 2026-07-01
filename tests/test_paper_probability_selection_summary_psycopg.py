from __future__ import annotations

import importlib
import sys
import traceback
import types
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import pytest


SECRET_DSN = "postgresql://worker:secret@localhost:54322/polymarket"
REMOTE_DSN = "postgresql://worker:remote-token@db.remote-supabase.example/polymarket"
REMOTE_HOST = "db.remote-supabase.example"
ADAPTER_MODULE_NAME = (
    "polymarket_alpha_lab.paper_probability_selection_summary_psycopg"
)


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
        "insert_paper_probability_selection_summary_report_with_psycopg",
        "load_paper_probability_selection_summary_reports_with_psycopg",
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
    report = FakeReport(config_version="paper-probability-selection-summary-v0")
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
        "insert_paper_probability_selection_summary_report",
        fake_insert,
    )

    inserted = adapter_module.insert_paper_probability_selection_summary_report_with_psycopg(
        SECRET_DSN,
        report,
        table_name="selection_summary_archive",
    )

    assert inserted == row
    assert connect_calls == [SECRET_DSN]
    store_connection, store_report, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_report == report
    assert store_table_name == "selection_summary_archive"
    assert connection.cursor_count == 0
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_delegates_all_selection_summary_filters_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeReport(config_version="paper-probability-selection-summary-v0")
    connect_calls: list[str] = []
    store_calls: list[
        tuple[Any, str | None, str | None, str | None, str | None, int | None, str]
    ] = []
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        source_queue_config_version: str | None,
        source_cost_stress_config_version: str | None,
        selection_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        store_calls.append(
            (
                connection_arg,
                config_version,
                source_queue_config_version,
                source_cost_stress_config_version,
                selection_status,
                limit,
                table_name,
            ),
        )
        return (report,)

    monkeypatch.setattr(
        adapter_module,
        "load_paper_probability_selection_summary_reports",
        fake_load,
    )

    loaded = adapter_module.load_paper_probability_selection_summary_reports_with_psycopg(
        SECRET_DSN,
        config_version="paper-probability-selection-summary-v0",
        source_queue_config_version="paper-probability-queue-v0",
        source_cost_stress_config_version="paper-cost-stress-v0",
        selection_status="watch",
        limit=10,
        table_name="selection_summary_archive",
    )

    assert loaded == (report,)
    assert connect_calls == [SECRET_DSN]
    (
        store_connection,
        config_version,
        source_queue_config_version,
        source_cost_stress_config_version,
        selection_status,
        limit,
        table_name,
    ) = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert config_version == "paper-probability-selection-summary-v0"
    assert source_queue_config_version == "paper-probability-queue-v0"
    assert source_cost_stress_config_version == "paper-cost-stress-v0"
    assert selection_status == "watch"
    assert limit == 10
    assert table_name == "selection_summary_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_success_connection_close_failure_propagates_without_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCloseFailingConnection()
    report = FakeReport(config_version="paper-probability-selection-summary-v0")
    connect_calls: list[str] = []
    store_calls: list[Any] = []
    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        source_queue_config_version: str | None,
        source_cost_stress_config_version: str | None,
        selection_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        store_calls.append(connection_arg)
        return (report,)

    monkeypatch.setattr(
        adapter_module,
        "load_paper_probability_selection_summary_reports",
        fake_load,
    )

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_probability_selection_summary_reports_with_psycopg(
            SECRET_DSN,
            config_version="paper-probability-selection-summary-v0",
            selection_status="watch",
            table_name="selection_summary_archive",
        )

    assert str(exc_info.value) == "close failed without dsn"
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
    assert "localhost" not in str(exc_info.value)
    assert "54322" not in str(exc_info.value)
    assert connect_calls == [SECRET_DSN]
    assert store_calls[0] is not connection
    assert store_calls[0].connection is connection
    assert connection.commit_count == 1
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
        adapter_module.load_paper_probability_selection_summary_reports_with_psycopg(
            REMOTE_DSN,
        )

    message = str(exc_info.value)
    assert "POLYMARKET_ALPHA_LAB_PAPER_PROBABILITY_SELECTION_SUMMARY_DB_DSN" in message
    assert REMOTE_DSN not in message
    assert "remote-token" not in message
    assert REMOTE_HOST not in message


def test_cursor_exposes_rowcount_and_wraps_dict_list_params_only(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCursorConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        cursor = connection_arg.cursor()
        try:
            cursor.execute(
                "insert",
                (
                    [{"selection_status": "watch"}],
                    ["cost_stress_watch"],
                    {"payload": {"readonly": True}},
                    Decimal("0.250000"),
                    "watch",
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
        "insert_paper_probability_selection_summary_report",
        fake_insert,
    )

    adapter_module.insert_paper_probability_selection_summary_report_with_psycopg(
        SECRET_DSN,
        FakeReport(config_version="paper-probability-selection-summary-v0"),
    )

    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == [{"selection_status": "watch"}]
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == ["cost_stress_watch"]
    assert isinstance(params[2], FakeJsonb)
    assert params[2].value == {"payload": {"readonly": True}}
    assert params[3] == Decimal("0.250000")
    assert not isinstance(params[3], FakeJsonb)
    assert params[4] == "watch"
    assert params[5] == 2
    assert params[6] is None
    assert connection.commit_count == 1


def test_store_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        raise ValueError("store failed without dsn")

    monkeypatch.setattr(
        adapter_module,
        "insert_paper_probability_selection_summary_report",
        fake_insert,
    )

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_probability_selection_summary_report_with_psycopg(
            SECRET_DSN,
            FakeReport(config_version="paper-probability-selection-summary-v0"),
        )

    message = str(exc_info.value)
    assert "store failed without dsn" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "localhost" not in message
    assert "54322" not in message
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
    adapter_module: types.ModuleType,
    connection: FakeConnection,
) -> None:
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        raise ValueError("store failed without dsn")

    monkeypatch.setattr(
        adapter_module,
        "insert_paper_probability_selection_summary_report",
        fake_insert,
    )

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_probability_selection_summary_report_with_psycopg(
            SECRET_DSN,
            FakeReport(config_version="paper-probability-selection-summary-v0"),
        )

    assert str(exc_info.value) == "store failed without dsn"
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_commit_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCommitFailingConnection()
    report = FakeReport(config_version="paper-probability-selection-summary-v0")
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        source_queue_config_version: str | None,
        source_cost_stress_config_version: str | None,
        selection_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        return (report,)

    monkeypatch.setattr(
        adapter_module,
        "load_paper_probability_selection_summary_reports",
        fake_load,
    )

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_probability_selection_summary_reports_with_psycopg(
            SECRET_DSN,
        )

    message = str(exc_info.value)
    assert "commit failed without dsn" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "localhost" not in message
    assert "54322" not in message
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
        adapter_module.load_paper_probability_selection_summary_reports_with_psycopg(
            SECRET_DSN,
        )

    assert "failed to connect" in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
    assert "localhost" not in str(exc_info.value)
    assert "54322" not in str(exc_info.value)
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
            if fullname == "psycopg":
                raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
            return None

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_probability_selection_summary_reports_with_psycopg(
            SECRET_DSN,
        )

    message = str(exc_info.value)
    assert "psycopg is required" in message
    assert "postgres extra" in message
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "localhost" not in message
    assert "54322" not in message
