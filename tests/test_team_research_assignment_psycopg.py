from __future__ import annotations

import importlib
import sys
import types
from datetime import UTC, datetime
from typing import Any

import pytest

from polymarket_alpha_lab.supabase_team_research_assignment_config import (
    TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR,
    TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR,
    TEAM_RESEARCH_ASSIGNMENT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.team_research_assignment import TeamResearchAssignmentReport


ADAPTER_MODULE_NAME = "polymarket_alpha_lab.team_research_assignment_psycopg"
STORE_MODULE_NAME = "polymarket_alpha_lab.team_research_assignment_store"
LOCAL_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
LOCAL_SECRET_DSN = "postgresql://assignment:secret@localhost:54322/postgres"
LOCAL_KEYWORD_SECRET_DSN = (
    "host=localhost port=54322 dbname=postgres user=assignment password=secret"
)
REMOTE_SECRET_DSN = "postgresql://assignment:secret@example.invalid/postgres"


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


@pytest.fixture()
def adapter_module() -> types.ModuleType:
    sys.modules.pop(ADAPTER_MODULE_NAME, None)
    return importlib.import_module(ADAPTER_MODULE_NAME)


def _report() -> TeamResearchAssignmentReport:
    return TeamResearchAssignmentReport(
        generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        config_version="team-research-assignment-v0",
        source_queue_config_version="strategy-candidate-research-queue-v0",
        source_route_config_version="team-market-route-v0",
        source_memory_config_version="team-memory-readiness-digest-v0",
        assignment_status="blocked",
        recommended_next_step="block_team_research_assignment",
        assignment_count=0,
        assigned_count=0,
        watch_count=0,
        blocked_count=0,
        team_summaries=(),
        rows=(),
        reason_codes=("team_research_assignment_empty_queue",),
    )


def test_public_exports_and_import_do_not_require_psycopg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delitem(sys.modules, "psycopg", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types", raising=False)
    monkeypatch.delitem(sys.modules, "psycopg.types.json", raising=False)
    sys.modules.pop(ADAPTER_MODULE_NAME, None)

    module = importlib.import_module(ADAPTER_MODULE_NAME)

    assert module.__all__ == (
        "insert_team_research_assignment_report_from_env",
        "load_team_research_assignment_reports",
        "load_team_research_assignment_reports_from_env",
    )


def test_disabled_insert_from_env_returns_none_without_connecting(
    adapter_module: types.ModuleType,
) -> None:
    connect_calls: list[str] = []
    insert_calls: list[object] = []

    result = adapter_module.insert_team_research_assignment_report_from_env(
        _report(),
        env={TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR: "false"},
        connect=lambda dsn: connect_calls.append(dsn),
        insert_report=lambda *args, **kwargs: insert_calls.append((args, kwargs)),
    )

    assert result is None
    assert connect_calls == []
    assert insert_calls == []


def test_disabled_load_from_env_returns_none_without_connecting(
    adapter_module: types.ModuleType,
) -> None:
    connect_calls: list[str] = []
    load_calls: list[object] = []

    result = adapter_module.load_team_research_assignment_reports_from_env(
        env={},
        assignment_status="ready",
        config_version="team-research-assignment-v0",
        limit=10,
        connect=lambda dsn: connect_calls.append(dsn),
        load_reports=lambda *args, **kwargs: load_calls.append((args, kwargs)),
    )

    assert result is None
    assert connect_calls == []
    assert load_calls == []


def test_enabled_insert_from_env_uses_local_dsn_table_connector_and_store_boundary(
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = _report()
    expected_result = object()
    connect_calls: list[str] = []
    insert_calls: list[tuple[Any, TeamResearchAssignmentReport, str]] = []

    def connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        return connection

    def insert_report(
        connection_arg: Any,
        report_arg: TeamResearchAssignmentReport,
        *,
        table_name: str,
    ) -> object:
        insert_calls.append((connection_arg, report_arg, table_name))
        return expected_result

    result = adapter_module.insert_team_research_assignment_report_from_env(
        report,
        env={
            TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR: "true",
            TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR: LOCAL_SECRET_DSN,
            TEAM_RESEARCH_ASSIGNMENT_DB_TABLE_ENV_VAR: (
                "team_research_assignment_report_archive"
            ),
        },
        connect=connect,
        insert_report=insert_report,
    )

    assert result is expected_result
    assert connect_calls == [LOCAL_SECRET_DSN]
    store_connection, store_report, table_name = insert_calls[0]
    assert store_connection is connection
    assert store_report is report
    assert table_name == "team_research_assignment_report_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_enabled_insert_from_env_uses_store_with_result_by_default(
    adapter_module: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()
    report = _report()
    expected_result = object()
    store_module = types.ModuleType(STORE_MODULE_NAME)
    insert_calls: list[tuple[object, object, str]] = []

    def forbidden_bare_insert(*args: object, **kwargs: object) -> object:
        raise AssertionError("bare insert must not be used by default")

    def insert_with_result(
        connection_arg: object,
        report_arg: object,
        *,
        table_name: str,
    ) -> object:
        insert_calls.append((connection_arg, report_arg, table_name))
        return expected_result

    store_module.insert_team_research_assignment_report = forbidden_bare_insert
    store_module.insert_team_research_assignment_report_with_result = insert_with_result
    monkeypatch.setitem(sys.modules, STORE_MODULE_NAME, store_module)

    result = adapter_module.insert_team_research_assignment_report_from_env(
        report,
        env={
            TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR: "true",
            TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR: LOCAL_SECRET_DSN,
            TEAM_RESEARCH_ASSIGNMENT_DB_TABLE_ENV_VAR: (
                "team_research_assignment_report_archive"
            ),
        },
        connect=lambda dsn: connection,
    )

    assert result is expected_result
    assert insert_calls == [
        (connection, report, "team_research_assignment_report_archive"),
    ]
    assert connection.commit_count == 1
    assert connection.close_count == 1


def test_enabled_load_from_env_uses_filters_connector_and_store_boundary(
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    expected_reports = (_report(),)
    connect_calls: list[str] = []
    load_calls: list[tuple[Any, str | None, str | None, int | None, str]] = []

    def connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        return connection

    def load_reports(
        connection_arg: Any,
        *,
        assignment_status: str | None,
        config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[TeamResearchAssignmentReport, ...]:
        load_calls.append(
            (
                connection_arg,
                assignment_status,
                config_version,
                limit,
                table_name,
            ),
        )
        return expected_reports

    result = adapter_module.load_team_research_assignment_reports_from_env(
        env={
            TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR: "true",
            TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR: LOCAL_SECRET_DSN,
            TEAM_RESEARCH_ASSIGNMENT_DB_TABLE_ENV_VAR: (
                "team_research_assignment_report_archive"
            ),
        },
        assignment_status="ready",
        config_version="team-research-assignment-v0",
        limit=10,
        connect=connect,
        load_reports=load_reports,
    )

    assert result == expected_reports
    assert connect_calls == [LOCAL_SECRET_DSN]
    store_connection, assignment_status, config_version, limit, table_name = load_calls[0]
    assert store_connection is connection
    assert assignment_status == "ready"
    assert config_version == "team-research-assignment-v0"
    assert limit == 10
    assert table_name == "team_research_assignment_report_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_uses_resolved_local_dsn_table_connector_and_store_boundary(
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    expected_reports = (_report(),)
    connect_calls: list[str] = []
    load_calls: list[tuple[Any, str | None, str | None, int | None, str]] = []

    def connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        return connection

    def load_reports(
        connection_arg: Any,
        *,
        assignment_status: str | None,
        config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[TeamResearchAssignmentReport, ...]:
        load_calls.append(
            (
                connection_arg,
                assignment_status,
                config_version,
                limit,
                table_name,
            ),
        )
        return expected_reports

    result = adapter_module.load_team_research_assignment_reports(
        dsn=LOCAL_SECRET_DSN,
        table_name="team_research_assignment_report_archive",
        assignment_status="ready",
        config_version="team-research-assignment-v0",
        limit=10,
        connect=connect,
        load_reports=load_reports,
    )

    assert result == expected_reports
    assert connect_calls == [LOCAL_SECRET_DSN]
    store_connection, assignment_status, config_version, limit, table_name = load_calls[0]
    assert store_connection is connection
    assert assignment_status == "ready"
    assert config_version == "team-research-assignment-v0"
    assert limit == 10
    assert table_name == "team_research_assignment_report_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


@pytest.mark.parametrize(
    ("entrypoint_name", "call_kwargs"),
    (
        (
            "insert_team_research_assignment_report_from_env",
            {"report": _report(), "insert_report": lambda *args, **kwargs: object()},
        ),
        (
            "load_team_research_assignment_reports_from_env",
            {"load_reports": lambda *args, **kwargs: ()},
        ),
    ),
)
def test_enabled_env_rejects_remote_dsn_before_connecting(
    adapter_module: types.ModuleType,
    entrypoint_name: str,
    call_kwargs: dict[str, object],
) -> None:
    connect_calls: list[str] = []

    with pytest.raises(ValueError) as exc_info:
        getattr(adapter_module, entrypoint_name)(
            env={
                TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR: "true",
                TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR: REMOTE_SECRET_DSN,
            },
            connect=lambda dsn: connect_calls.append(dsn) or FakeConnection(),
            **call_kwargs,
        )

    message = str(exc_info.value)
    assert TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert REMOTE_SECRET_DSN not in message
    assert "postgresql://" not in message
    assert "secret" not in message.lower()
    assert "example.invalid" not in message
    assert connect_calls == []


def test_enabled_insert_validates_local_dsn_and_report_before_connecting(
    adapter_module: types.ModuleType,
) -> None:
    connect_calls: list[str] = []

    def fail_if_called(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        raise AssertionError("connect should not be reached by this test")

    with pytest.raises(ValueError, match="report must be a TeamResearchAssignmentReport"):
        adapter_module.insert_team_research_assignment_report_from_env(
            object(),
            env={
                TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR: "true",
                TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR: LOCAL_DSN,
            },
            connect=fail_if_called,
            insert_report=lambda *args, **kwargs: object(),
        )

    assert connect_calls == []


def test_operation_errors_redact_dsn_and_secret(
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    def insert_report(*args: object, **kwargs: object) -> object:
        raise RuntimeError(f"failed for {LOCAL_SECRET_DSN}")

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.insert_team_research_assignment_report_from_env(
            _report(),
            env={
                TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR: "true",
                TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR: LOCAL_SECRET_DSN,
            },
            connect=lambda dsn: connection,
            insert_report=insert_report,
        )

    message = str(exc_info.value)
    assert LOCAL_SECRET_DSN not in message
    assert "postgresql://" not in message
    assert "secret" not in message.lower()
    assert connection.rollback_count == 1
    assert connection.close_count == 1


@pytest.mark.parametrize("dsn", (LOCAL_SECRET_DSN, LOCAL_KEYWORD_SECRET_DSN))
def test_operation_errors_redact_host_table_payload_market_hash_and_order_fields(
    adapter_module: types.ModuleType,
    dsn: str,
) -> None:
    connection = FakeConnection()
    table_name = "team_research_assignment_report_archive"
    market_slug = "btc-up-or-down-july-2"
    market_question = "Will BTC close above 100000 on July 2?"
    report_hash = "a" * 64

    def insert_report(*args: object, **kwargs: object) -> object:
        raise RuntimeError(
            "insert failed on localhost table "
            f"{table_name} payload_json market_slug {market_slug} "
            f"question {market_question} report_sha256 {report_hash} "
            "api_secret leaked order_id ord_123",
        )

    with pytest.raises(RuntimeError) as exc_info:
        adapter_module.insert_team_research_assignment_report_from_env(
            _report(),
            env={
                TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR: "true",
                TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR: dsn,
                TEAM_RESEARCH_ASSIGNMENT_DB_TABLE_ENV_VAR: table_name,
            },
            connect=lambda dsn: connection,
            insert_report=insert_report,
        )

    message = str(exc_info.value)
    assert message == "team research assignment database operation failed for <redacted>"
    assert "localhost" not in message
    assert table_name not in message
    assert "payload_json" not in message
    assert market_slug not in message
    assert market_question not in message
    assert report_hash not in message
    assert "api_secret" not in message
    assert "order_id" not in message
    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_psycopg_owned_connection_adapts_json_params_only_inside_adapter(
    adapter_module: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Jsonb:
        def __init__(self, value: object) -> None:
            self.value = value

    class FakeCursor:
        def __init__(self) -> None:
            self.executed_params: tuple[object, ...] | None = None

        def execute(self, sql: str, params: tuple[object, ...] = ()) -> None:
            self.executed_params = params

        def close(self) -> None:
            pass

    class FakePsycopgConnection(FakeConnection):
        def __init__(self) -> None:
            super().__init__()
            self.cursor_instance = FakeCursor()

        def cursor(self) -> FakeCursor:
            return self.cursor_instance

    connection = FakePsycopgConnection()
    psycopg_module = types.ModuleType("psycopg")
    json_module = types.ModuleType("psycopg.types.json")
    types_module = types.ModuleType("psycopg.types")
    psycopg_module.connect = lambda dsn: connection  # type: ignore[attr-defined]
    json_module.Jsonb = Jsonb  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "psycopg", psycopg_module)
    monkeypatch.setitem(sys.modules, "psycopg.types", types_module)
    monkeypatch.setitem(sys.modules, "psycopg.types.json", json_module)

    store_module = types.ModuleType(STORE_MODULE_NAME)

    def insert_with_result(
        connection_arg: object,
        report_arg: object,
        *,
        table_name: str,
    ) -> str:
        cursor = connection_arg.cursor()
        cursor.execute("insert", ({"payload": True}, ["reason"], table_name))
        cursor.close()
        return "inserted"

    store_module.insert_team_research_assignment_report_with_result = insert_with_result
    monkeypatch.setitem(sys.modules, STORE_MODULE_NAME, store_module)

    result = adapter_module.insert_team_research_assignment_report_from_env(
        _report(),
        env={
            TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED_ENV_VAR: "true",
            TEAM_RESEARCH_ASSIGNMENT_DB_DSN_ENV_VAR: LOCAL_DSN,
        },
    )

    assert result == "inserted"
    assert connection.cursor_instance.executed_params is not None
    payload_param, reason_param, table_param = connection.cursor_instance.executed_params
    assert isinstance(payload_param, Jsonb)
    assert payload_param.value == {"payload": True}
    assert isinstance(reason_param, Jsonb)
    assert reason_param.value == ["reason"]
    assert table_param == "team_research_assignment_reports"
    assert connection.commit_count == 1
    assert connection.close_count == 1
