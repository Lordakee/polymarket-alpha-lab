from __future__ import annotations

import importlib
import sys
import types
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.supabase_team_diagnostics_snapshot_config import (
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR,
    TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.team_diagnostics_snapshot import (
    TeamDiagnosticsSnapshotReport,
)


ADAPTER_MODULE_NAME = "polymarket_alpha_lab.team_diagnostics_snapshot_psycopg"
LOCAL_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"
LOCAL_SECRET_DSN = "postgresql://team-diagnostics:secret@localhost:54322/postgres"
REMOTE_SECRET_DSN = "postgresql://team-diagnostics:secret@example.invalid/postgres"


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


def _report() -> TeamDiagnosticsSnapshotReport:
    return TeamDiagnosticsSnapshotReport(
        generated_at=datetime(2026, 6, 30, 12, 30, tzinfo=UTC),
        config_version="team-diagnostics-snapshot-v0",
        source_config_version="team-diagnostics-bundle-v0",
        filters=(("team_id", "crypto_btc"),),
        forecast_row_count=1,
        evidence_row_count=1,
        outcome_row_count=0,
        memory_eligible_reference_count=0,
        calibration_status="candidate",
        calibration_settled_count=0,
        calibration_group_count=0,
        event_template_row_count=0,
        event_template_status="candidate",
        source_reliability_row_count=0,
        source_reliability_missing_source_evidence_count=0,
        evidence_quality_status="evidence_quality_pass",
        evidence_quality_pass_count=1,
        evidence_quality_watch_count=0,
        evidence_quality_blocked_count=0,
        evidence_quality_average_quality_score=Decimal("0.900000"),
        reason_codes=(
            "team_diagnostics_snapshot_psycopg_test",
        ),
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
        "insert_team_diagnostics_snapshot_report_from_env",
        "load_team_diagnostics_snapshot_reports_from_env",
    )


def test_disabled_insert_from_env_returns_none_without_connecting(
    adapter_module: types.ModuleType,
) -> None:
    connect_calls: list[str] = []
    insert_calls: list[object] = []

    result = adapter_module.insert_team_diagnostics_snapshot_report_from_env(
        _report(),
        env={TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR: "false"},
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

    result = adapter_module.load_team_diagnostics_snapshot_reports_from_env(
        env={},
        config_version="team-diagnostics-v0",
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
    insert_calls: list[tuple[Any, TeamDiagnosticsSnapshotReport, str]] = []

    def connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        return connection

    def insert_report(
        connection_arg: Any,
        report_arg: TeamDiagnosticsSnapshotReport,
        *,
        table_name: str,
    ) -> object:
        insert_calls.append((connection_arg, report_arg, table_name))
        return expected_result

    result = adapter_module.insert_team_diagnostics_snapshot_report_from_env(
        report,
        env={
            TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR: "true",
            TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR: LOCAL_SECRET_DSN,
            TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR: "team_diagnostics_snapshot_archive",
        },
        connect=connect,
        insert_report=insert_report,
    )

    assert result is expected_result
    assert connect_calls == [LOCAL_SECRET_DSN]
    store_connection, store_report, table_name = insert_calls[0]
    assert store_connection is connection
    assert store_report is report
    assert table_name == "team_diagnostics_snapshot_archive"
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
    store_module = types.ModuleType(
        "polymarket_alpha_lab.team_diagnostics_snapshot_store",
    )
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

    store_module.insert_team_diagnostics_snapshot_report = forbidden_bare_insert
    store_module.insert_team_diagnostics_snapshot_report_with_result = insert_with_result
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.team_diagnostics_snapshot_store",
        store_module,
    )

    result = adapter_module.insert_team_diagnostics_snapshot_report_from_env(
        report,
        env={
            TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR: "true",
            TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR: LOCAL_SECRET_DSN,
            TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR: "team_diagnostics_snapshot_archive",
        },
        connect=lambda dsn: connection,
    )

    assert result is expected_result
    assert insert_calls == [
        (connection, report, "team_diagnostics_snapshot_archive"),
    ]
    assert connection.commit_count == 1
    assert connection.close_count == 1


def test_enabled_load_from_env_uses_filters_connector_and_store_boundary(
    adapter_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    expected_reports = (_report(),)
    connect_calls: list[str] = []
    load_calls: list[
        tuple[Any, str | None, str | None, str | None, str | None, int | None, str]
    ] = []

    def connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        return connection

    def load_reports(
        connection_arg: Any,
        *,
        team_id: str | None,
        market_slug: str | None,
        forecast_id: str | None,
        config_version: str | None,
        limit: int | None,
        table_name: str,
    ) -> tuple[TeamDiagnosticsSnapshotReport, ...]:
        load_calls.append(
            (
                connection_arg,
                team_id,
                market_slug,
                forecast_id,
                config_version,
                limit,
                table_name,
            ),
        )
        return expected_reports

    result = adapter_module.load_team_diagnostics_snapshot_reports_from_env(
        env={
            TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR: "true",
            TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR: LOCAL_SECRET_DSN,
            TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE_ENV_VAR: "team_diagnostics_snapshot_archive",
        },
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        forecast_id="forecast-btc-1",
        config_version="team-diagnostics-v0",
        limit=10,
        connect=connect,
        load_reports=load_reports,
    )

    assert result == expected_reports
    assert connect_calls == [LOCAL_SECRET_DSN]
    (
        store_connection,
        team_id,
        market_slug,
        forecast_id,
        config_version,
        limit,
        table_name,
    ) = load_calls[0]
    assert store_connection is connection
    assert team_id == "crypto_btc"
    assert market_slug == "bitcoin-above-120k"
    assert forecast_id == "forecast-btc-1"
    assert config_version == "team-diagnostics-v0"
    assert limit == 10
    assert table_name == "team_diagnostics_snapshot_archive"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


@pytest.mark.parametrize(
    ("entrypoint_name", "call_kwargs"),
    (
        (
            "insert_team_diagnostics_snapshot_report_from_env",
            {"report": _report(), "insert_report": lambda *args, **kwargs: object()},
        ),
        (
            "load_team_diagnostics_snapshot_reports_from_env",
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
                TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR: "true",
                TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR: REMOTE_SECRET_DSN,
            },
            connect=lambda dsn: connect_calls.append(dsn) or FakeConnection(),
            **call_kwargs,
        )

    message = str(exc_info.value)
    assert TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR in message
    assert "local Postgres/Supabase" in message
    assert REMOTE_SECRET_DSN not in message
    assert "postgresql://" not in message
    assert "secret" not in message.lower()
    assert "example.invalid" not in message
    assert connect_calls == []


def test_enabled_env_validates_local_dsn_before_connecting(
    adapter_module: types.ModuleType,
) -> None:
    connect_calls: list[str] = []

    def fail_if_called(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        raise AssertionError("connect should not be reached by this test")

    with pytest.raises(ValueError, match="report must be a TeamDiagnosticsSnapshotReport"):
        adapter_module.insert_team_diagnostics_snapshot_report_from_env(
            object(),
            env={
                TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED_ENV_VAR: "true",
                TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN_ENV_VAR: LOCAL_DSN,
            },
            connect=fail_if_called,
            insert_report=lambda *args, **kwargs: object(),
        )

    assert connect_calls == []
