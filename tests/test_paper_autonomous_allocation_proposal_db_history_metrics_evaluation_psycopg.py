from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest


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
    sys.modules.pop(
        (
            "polymarket_alpha_lab"
            ".paper_autonomous_allocation_proposal_db_history_metrics_evaluation_psycopg"
        ),
        None,
    )
    return importlib.import_module(
        (
            "polymarket_alpha_lab"
            ".paper_autonomous_allocation_proposal_db_history_metrics_evaluation_psycopg"
        ),
    )


def test_insert_opens_psycopg_connection_delegates_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeReport(
        config_version="paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0",
    )
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
        "insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report",
        fake_insert,
    )

    insert_report = (
        adapter_module
        .insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report_with_psycopg
    )
    inserted = insert_report(
        "postgresql://user:secret@example.invalid/db",
        report,
        table_name="metrics_evaluation_archive",
    )

    assert inserted == row
    assert connect_calls == ["postgresql://user:secret@example.invalid/db"]
    store_connection, store_report, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_report == report
    assert store_table_name == "metrics_evaluation_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_uses_autocommit_connection_delegates_query_options_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeReport(
        config_version="paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0",
    )
    connect_calls: list[tuple[str, dict[str, object]]] = []
    store_calls: list[tuple[Any, str | None, str | None, int | None, str]] = []

    def connect(dsn: str, **kwargs: object) -> FakeConnection:
        connect_calls.append((dsn, kwargs))
        return connection

    _install_fake_psycopg(monkeypatch, connect=connect)

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        evaluation_status: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        store_calls.append(
            (
                connection_arg,
                config_version,
                evaluation_status,
                limit,
                table_name,
            ),
        )
        return (report,)

    monkeypatch.setattr(
        adapter_module,
        "load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_reports",
        fake_load,
    )

    load_reports = (
        adapter_module
        .load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_reports_with_psycopg
    )
    loaded = load_reports(
        "postgresql://user:secret@example.invalid/db",
        config_version="paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0",
        evaluation_status="watch",
        limit=10,
        table_name="metrics_evaluation_archive",
    )

    assert loaded == (report,)
    assert connect_calls == [
        ("postgresql://user:secret@example.invalid/db", {"autocommit": True}),
    ]
    store_connection, config_version, evaluation_status, limit, table_name = store_calls[0]
    assert store_connection is connection
    assert config_version == (
        "paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0"
    )
    assert evaluation_status == "watch"
    assert limit == 10
    assert table_name == "metrics_evaluation_archive"
    assert connection.commit_count == 0
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
                    {"metrics_churn_share_watch": 1},
                    ["metrics_churn_share_watch"],
                    {"diagnostics": {"readonly": True}},
                    {"payload": {"paper_only": True}},
                    "watch",
                    4,
                ),
            )
        finally:
            cursor.close()
        return FakeRow(report_sha256="a" * 64)

    monkeypatch.setattr(
        adapter_module,
        "insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report",
        fake_insert,
    )

    insert_report = (
        adapter_module
        .insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report_with_psycopg
    )
    insert_report(
        "postgresql://user:secret@example.invalid/db",
        FakeReport(
            config_version=(
                "paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0"
            ),
        ),
    )

    assert connect_calls == ["postgresql://user:secret@example.invalid/db"]
    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == {"metrics_churn_share_watch": 1}
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == ["metrics_churn_share_watch"]
    assert isinstance(params[2], FakeJsonb)
    assert params[2].value == {"diagnostics": {"readonly": True}}
    assert isinstance(params[3], FakeJsonb)
    assert params[3].value == {"payload": {"paper_only": True}}
    assert params[4] == "watch"
    assert params[5] == 4
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
        "insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report",
        fake_insert,
    )

    insert_report = (
        adapter_module
        .insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report_with_psycopg
    )
    with pytest.raises(ValueError, match="store failed without dsn"):
        insert_report(
            "postgresql://user:secret@example.invalid/db",
            FakeReport(
                config_version=(
                    "paper-autonomous-allocation-proposal-db-history-metrics-"
                    "evaluation-v0"
                ),
            ),
        )

    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_insert_rolls_back_closes_and_reraises_commit_exception(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCommitFailingConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        return FakeRow(report_sha256="a" * 64)

    monkeypatch.setattr(
        adapter_module,
        "insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report",
        fake_insert,
    )

    insert_report = (
        adapter_module
        .insert_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report_with_psycopg
    )
    with pytest.raises(RuntimeError, match="commit failed without dsn"):
        insert_report(
            "postgresql://user:secret@example.invalid/db",
            FakeReport(
                config_version=(
                    "paper-autonomous-allocation-proposal-db-history-metrics-"
                    "evaluation-v0"
                ),
            ),
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
    load_reports = (
        adapter_module
        .load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_reports_with_psycopg
    )

    with pytest.raises(RuntimeError) as exc_info:
        load_reports("postgresql://user:secret@example.invalid/db")

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
    load_reports = (
        adapter_module
        .load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_reports_with_psycopg
    )

    with pytest.raises(RuntimeError) as exc_info:
        load_reports("postgresql://user:secret@example.invalid/db")

    assert "psycopg is required" in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
