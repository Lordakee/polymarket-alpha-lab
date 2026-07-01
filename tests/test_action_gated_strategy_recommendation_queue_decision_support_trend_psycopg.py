from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest

from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_trend_config import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR,
)

LOCAL_DSN = "postgresql://postgres:local-secret@localhost:54322/postgres"
REMOTE_DSN = (
    "postgresql://worker:remote-secret-token@db.remote.supabase.co:5432/polymarket"
)
STORE_MODULE_NAME = (
    "polymarket_alpha_lab."
    "action_gated_strategy_recommendation_queue_decision_support_trend_store"
)
ADAPTER_MODULE_NAME = (
    "polymarket_alpha_lab."
    "action_gated_strategy_recommendation_queue_decision_support_trend_psycopg"
)


@dataclass(frozen=True)
class FakeTrendReport:
    name: str


@dataclass(frozen=True)
class FakeSnapshotPair:
    input_position: int


@dataclass(frozen=True)
class FakeRows:
    trend_sha256: str


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


def _install_fake_store(
    monkeypatch: pytest.MonkeyPatch,
    *,
    insert: Any | None = None,
    load: Any | None = None,
) -> types.ModuleType:
    store_module = types.ModuleType(STORE_MODULE_NAME)
    store_module.DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_REPORTS_TABLE = (
        "paper_action_gated_queue_decision_support_trend_reports"
    )
    store_module.DEFAULT_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SOURCES_TABLE = (
        "paper_action_gated_queue_decision_support_trend_sources"
    )
    store_module.insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows = (
        insert if insert is not None else _unexpected_store_call("insert")
    )
    store_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows = (
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
        "insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg",
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

    finder = MissingPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
            LOCAL_DSN,
        )

    message = str(exc_info.value)
    assert "psycopg is required" in message
    assert "postgres extra" in message
    assert "postgresql://" not in message
    assert "local-secret" not in message
    assert "localhost" not in message


def test_remote_dsn_is_rejected_before_psycopg_import_without_echoing_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter_module = _import_adapter(monkeypatch)
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types.json", raising=False)

    class ForbiddenPsycopgFinder:
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname == "psycopg" or fullname.startswith("psycopg."):
                raise AssertionError("psycopg must not be imported for invalid DSNs")
            return None

    finder = ForbiddenPsycopgFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(ValueError) as exc_info:
        adapter_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
            REMOTE_DSN,
        )

    message = str(exc_info.value)
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR in message
    assert REMOTE_DSN not in message
    assert "remote-secret-token" not in message
    assert "db.remote.supabase.co" not in message


def test_successful_insert_delegates_to_store_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    trend_report = FakeTrendReport(name="trend")
    snapshot_pairs = (FakeSnapshotPair(input_position=1),)
    rows = FakeRows(trend_sha256="a" * 64)
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, Any, Any, str, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_insert(
        connection_arg: Any,
        trend_report_arg: Any,
        snapshot_pairs_arg: Any,
        *,
        reports_table_name: str,
        sources_table_name: str,
    ) -> FakeRows:
        store_calls.append(
            (
                connection_arg,
                trend_report_arg,
                snapshot_pairs_arg,
                reports_table_name,
                sources_table_name,
            ),
        )
        return rows

    _install_fake_store(monkeypatch, insert=fake_insert)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    inserted = (
        adapter_module.insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
            LOCAL_DSN,
            trend_report,
            snapshot_pairs,
            reports_table_name="audit.trend_reports",
            sources_table_name="audit.trend_sources",
        )
    )

    assert inserted == rows
    assert connect_calls == [LOCAL_DSN]
    store_connection, store_trend_report, store_snapshot_pairs, reports_table, sources_table = (
        store_calls[0]
    )
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert store_trend_report == trend_report
    assert store_snapshot_pairs == snapshot_pairs
    assert reports_table == "audit.trend_reports"
    assert sources_table == "audit.trend_sources"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_successful_load_delegates_to_store_commits_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    rows = (FakeRows(trend_sha256="a" * 64),)
    connect_calls: list[str] = []
    store_calls: list[tuple[Any, str | None, int | None, str, str]] = []

    _install_fake_psycopg(
        monkeypatch,
        connect=lambda dsn: connect_calls.append(dsn) or connection,
    )

    def fake_load(
        connection_arg: Any,
        *,
        latest_risk_status: str | None,
        limit: int | None,
        reports_table_name: str,
        sources_table_name: str,
    ) -> tuple[FakeRows, ...]:
        store_calls.append(
            (
                connection_arg,
                latest_risk_status,
                limit,
                reports_table_name,
                sources_table_name,
            ),
        )
        return rows

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    loaded = (
        adapter_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
            LOCAL_DSN,
            latest_risk_status="watch",
            limit=25,
            reports_table_name="audit.trend_reports",
            sources_table_name="audit.trend_sources",
        )
    )

    assert loaded == rows
    assert connect_calls == [LOCAL_DSN]
    store_connection, latest_risk_status, limit, reports_table, sources_table = (
        store_calls[0]
    )
    assert store_connection is not connection
    assert store_connection.connection is connection
    assert latest_risk_status == "watch"
    assert limit == 25
    assert reports_table == "audit.trend_reports"
    assert sources_table == "audit.trend_sources"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(
        connection_arg: Any,
        trend_report_arg: Any,
        snapshot_pairs_arg: Any,
        *,
        reports_table_name: str,
        sources_table_name: str,
    ) -> FakeRows:
        raise ValueError("store failed without dsn")

    _install_fake_store(monkeypatch, insert=fake_insert)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
            LOCAL_DSN,
            FakeTrendReport(name="trend"),
            (FakeSnapshotPair(input_position=1),),
        )

    message = str(exc_info.value)
    assert "store failed without dsn" in message
    assert "postgresql://" not in message
    assert "local-secret" not in message
    assert "localhost" not in message
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_commit_failure_rolls_back_closes_reraises_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCommitFailingConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        latest_risk_status: str | None,
        limit: int | None,
        reports_table_name: str,
        sources_table_name: str,
    ) -> tuple[FakeRows, ...]:
        return (FakeRows(trend_sha256="a" * 64),)

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
            LOCAL_DSN,
        )

    message = str(exc_info.value)
    assert "commit failed without dsn" in message
    assert "postgresql://" not in message
    assert "local-secret" not in message
    assert "localhost" not in message
    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_success_close_failure_propagates_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCloseFailingConnection()
    rows = (FakeRows(trend_sha256="a" * 64),)
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_load(
        connection_arg: Any,
        *,
        latest_risk_status: str | None,
        limit: int | None,
        reports_table_name: str,
        sources_table_name: str,
    ) -> tuple[FakeRows, ...]:
        return rows

    _install_fake_store(monkeypatch, load=fake_load)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
            LOCAL_DSN,
        )

    message = str(exc_info.value)
    assert "close failed without dsn" in message
    assert "postgresql://" not in message
    assert "local-secret" not in message
    assert "localhost" not in message
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_operation_failure_close_failure_is_swallowed_and_does_not_echo_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeCloseFailingConnection()
    _install_fake_psycopg(monkeypatch, connect=lambda dsn: connection)

    def fake_insert(
        connection_arg: Any,
        trend_report_arg: Any,
        snapshot_pairs_arg: Any,
        *,
        reports_table_name: str,
        sources_table_name: str,
    ) -> FakeRows:
        raise ValueError("store failed without dsn")

    _install_fake_store(monkeypatch, insert=fake_insert)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    with pytest.raises(ValueError) as exc_info:
        adapter_module.insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
            LOCAL_DSN,
            FakeTrendReport(name="trend"),
            (FakeSnapshotPair(input_position=1),),
        )

    message = str(exc_info.value)
    assert "store failed without dsn" in message
    assert "close failed" not in message
    assert "postgresql://" not in message
    assert "local-secret" not in message
    assert "localhost" not in message
    assert connection.commit_count == 0
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
        adapter_module.load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
            LOCAL_DSN,
        )

    message = str(exc_info.value)
    assert "failed to connect" in message
    assert "postgresql://" not in message
    assert "local-secret" not in message
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

    def fake_insert(
        connection_arg: Any,
        trend_report_arg: Any,
        snapshot_pairs_arg: Any,
        *,
        reports_table_name: str,
        sources_table_name: str,
    ) -> FakeRows:
        cursor = connection_arg.cursor()
        try:
            cursor.execute(
                "insert",
                (
                    {"payload": {"paper_only": True, "reasons": ["ok"]}},
                    ["portfolio_exposure_ok"],
                    "scalar",
                    3,
                ),
            )
        finally:
            cursor.close()
        return FakeRows(trend_sha256="a" * 64)

    _install_fake_store(monkeypatch, insert=fake_insert)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    adapter_module = importlib.import_module(ADAPTER_MODULE_NAME)

    adapter_module.insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(
        LOCAL_DSN,
        FakeTrendReport(name="trend"),
        (FakeSnapshotPair(input_position=1),),
    )

    assert connect_calls == [LOCAL_DSN]
    assert connection.cursor_count == 1
    assert connection.cursor_instance.close_count == 1
    _, params = connection.cursor_instance.calls[0]
    assert isinstance(params[0], FakeJsonb)
    assert params[0].value == {
        "payload": {"paper_only": True, "reasons": ["ok"]},
    }
    assert isinstance(params[1], FakeJsonb)
    assert params[1].value == ["portfolio_exposure_ok"]
    assert params[2] == "scalar"
    assert params[3] == 3
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_public_exports_include_adapter_functions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter_module = _import_adapter(monkeypatch)

    assert adapter_module.__all__ == (
        "insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg",
        "load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg",
    )
