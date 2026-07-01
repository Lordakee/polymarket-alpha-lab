from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest


LOCAL_SUPABASE_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
REMOTE_SECRET_DSN = (
    "postgresql://postgres:remote-secret-token@db.remote-project.supabase.co:5432/postgres"
)


@dataclass(frozen=True)
class FakeReport:
    config_version: str


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
    psycopg = types.SimpleNamespace(connect=connect)
    json_module = types.SimpleNamespace(Jsonb=FakeJsonb)
    monkeypatch.setitem(sys.modules, "psycopg", psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.types.json", json_module)


@pytest.fixture()
def adapter_module() -> types.ModuleType:
    sys.modules.pop("polymarket_alpha_lab.paper_recommendation_cycle_snapshot_psycopg", None)
    return importlib.import_module(
        "polymarket_alpha_lab.paper_recommendation_cycle_snapshot_psycopg",
    )


def test_insert_opens_psycopg_connection_delegates_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeReport(config_version="paper-recommendation-cycle-snapshot-v0")
    row = FakeRow(snapshot_sha256="a" * 64)
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
        "insert_paper_recommendation_cycle_snapshot",
        fake_insert,
    )

    inserted = adapter_module.insert_paper_recommendation_cycle_snapshot_with_psycopg(
        LOCAL_SUPABASE_DSN,
        report,
        table_name="cycle_snapshot_archive",
    )

    assert inserted == row
    assert connect_calls == [LOCAL_SUPABASE_DSN]
    store_connection, store_report, store_table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_report == report
    assert store_table_name == "cycle_snapshot_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_opens_psycopg_connection_delegates_query_options_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeReport(config_version="paper-recommendation-cycle-snapshot-v0")
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, str | None, int | None, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        store_calls.append((connection_arg, config_version, limit, table_name))
        return (report,)

    monkeypatch.setattr(
        adapter_module,
        "load_paper_recommendation_cycle_snapshots",
        fake_load,
    )

    loaded = adapter_module.load_paper_recommendation_cycle_snapshots_with_psycopg(
        LOCAL_SUPABASE_DSN,
        config_version="paper-recommendation-cycle-snapshot-v0",
        limit=10,
        table_name="cycle_snapshot_archive",
    )

    assert loaded == (report,)
    assert connect_calls == [LOCAL_SUPABASE_DSN]
    store_connection, config_version, limit, table_name = store_calls[0]
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert config_version == "paper-recommendation-cycle-snapshot-v0"
    assert limit == 10
    assert table_name == "cycle_snapshot_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_successful_insert_close_failure_propagates_without_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCloseFailingConnection()
    report = FakeReport(config_version="paper-recommendation-cycle-snapshot-v0")
    row = FakeRow(snapshot_sha256="a" * 64)
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        return row

    monkeypatch.setattr(
        adapter_module,
        "insert_paper_recommendation_cycle_snapshot",
        fake_insert,
    )

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.insert_paper_recommendation_cycle_snapshot_with_psycopg(
            LOCAL_SUPABASE_DSN,
            report,
        )

    message = str(exc_info.value)
    assert message == "close failed without dsn"
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_successful_load_close_failure_propagates_without_dsn(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCloseFailingConnection()
    report = FakeReport(config_version="paper-recommendation-cycle-snapshot-v0")
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        return (report,)

    monkeypatch.setattr(
        adapter_module,
        "load_paper_recommendation_cycle_snapshots",
        fake_load,
    )

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_recommendation_cycle_snapshots_with_psycopg(
            LOCAL_SUPABASE_DSN,
        )

    message = str(exc_info.value)
    assert message == "close failed without dsn"
    assert "postgresql://" not in message
    assert "secret" not in message
    assert "example.invalid" not in message
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

    def fake_insert(connection_arg: Any, report_arg: Any, *, table_name: str) -> FakeRow:
        cursor = connection_arg.cursor()
        try:
            cursor.execute(
                "insert",
                (
                    {"stage_count": 1},
                    {"artifact_count": 1},
                    ["pipeline_final_status_pass"],
                    {"payload": {"readonly": True}},
                ),
            )
        finally:
            cursor.close()
        return FakeRow(snapshot_sha256="a" * 64)

    monkeypatch.setattr(
        adapter_module,
        "insert_paper_recommendation_cycle_snapshot",
        fake_insert,
    )

    adapter_module.insert_paper_recommendation_cycle_snapshot_with_psycopg(
        LOCAL_SUPABASE_DSN,
        FakeReport(config_version="paper-recommendation-cycle-snapshot-v0"),
    )

    assert connect_calls == [LOCAL_SUPABASE_DSN]
    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == {"stage_count": 1}
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == {"artifact_count": 1}
    assert isinstance(params[2], FakeJsonb)
    assert params[2].value == ["pipeline_final_status_pass"]
    assert isinstance(params[3], FakeJsonb)
    assert params[3].value == {"payload": {"readonly": True}}
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
        "insert_paper_recommendation_cycle_snapshot",
        fake_insert,
    )

    with pytest.raises(ValueError, match="store failed without dsn"):
        adapter_module.insert_paper_recommendation_cycle_snapshot_with_psycopg(
            LOCAL_SUPABASE_DSN,
            FakeReport(config_version="paper-recommendation-cycle-snapshot-v0"),
        )

    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_load_rolls_back_closes_and_reraises_commit_exception(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeCommitFailingConnection()
    report = FakeReport(config_version="paper-recommendation-cycle-snapshot-v0")
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[FakeReport, ...]:
        return (report,)

    monkeypatch.setattr(
        adapter_module,
        "load_paper_recommendation_cycle_snapshots",
        fake_load,
    )

    with pytest.raises(RuntimeError, match="commit failed without dsn"):
        adapter_module.load_paper_recommendation_cycle_snapshots_with_psycopg(
            LOCAL_SUPABASE_DSN,
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
        adapter_module.load_paper_recommendation_cycle_snapshots_with_psycopg(
            LOCAL_SUPABASE_DSN,
        )

    assert "failed to connect" in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
    assert "example.invalid" not in str(exc_info.value)


def test_remote_dsn_rejected_before_psycopg_connect_or_json_adapter(
    monkeypatch: pytest.MonkeyPatch,
    adapter_module: types.ModuleType,
) -> None:
    json_adapter_calls: list[None] = []
    connect_calls: list[str] = []

    def fail_jsonb_adapter() -> type[Any]:
        json_adapter_calls.append(None)
        raise AssertionError("json adapter must not be imported for remote DSN")

    def fail_connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        raise AssertionError("psycopg connect must not run for remote DSN")

    monkeypatch.setattr(adapter_module, "_jsonb_adapter", fail_jsonb_adapter)
    monkeypatch.setattr(adapter_module, "_connect", fail_connect)

    with pytest.raises(ValueError) as exc_info:
        adapter_module.load_paper_recommendation_cycle_snapshots_with_psycopg(
            REMOTE_SECRET_DSN,
        )

    message = str(exc_info.value)
    assert adapter_module.CYCLE_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert "postgresql://" not in message
    assert "remote-secret-token" not in message
    assert "db.remote-project.supabase.co" not in message
    assert json_adapter_calls == []
    assert connect_calls == []


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
        adapter_module.load_paper_recommendation_cycle_snapshots_with_psycopg(
            LOCAL_SUPABASE_DSN,
        )

    assert "psycopg is required" in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
