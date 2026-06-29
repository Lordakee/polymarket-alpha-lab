from __future__ import annotations

import builtins
import importlib
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_config import (
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_db_history_health_config import (
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-autonomous-allocation-proposal-db-history-health"
HISTORY_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-v0"
HEALTH_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-health-v0"
HISTORY_MODULE = "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history"
HEALTH_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health"
)
HEALTH_LOADER_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_load"
)
HEALTH_PSYCOPG_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_psycopg"
)


def _set_allocation_proposal_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = "paper_autonomous_allocation_proposal_reports",
) -> None:
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE_ENV_VAR,
        table_name,
    )


def _set_allocation_proposal_db_history_health_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = "paper_autonomous_allocation_proposal_db_history_health_reports",
) -> None:
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR,
        dsn,
    )
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR,
        table_name,
    )


def _install_or_get_history_api(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    try:
        return importlib.import_module(HISTORY_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name != HISTORY_MODULE:
            raise

    module = ModuleType(HISTORY_MODULE)

    @dataclass(frozen=True)
    class PaperAutonomousAllocationProposalDbHistoryConfig:
        config_version: str = HISTORY_CONFIG_VERSION
        min_report_count: int = 3
        max_blocked_proposal_report_count: int = 0
        max_watch_proposal_report_count: int = 0
        max_duplicate_generated_at_count: int = 0
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    module.PaperAutonomousAllocationProposalDbHistoryConfig = (
        PaperAutonomousAllocationProposalDbHistoryConfig
    )
    monkeypatch.setitem(sys.modules, HISTORY_MODULE, module)
    return module


def _install_or_get_health_api(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    try:
        return importlib.import_module(HEALTH_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name != HEALTH_MODULE:
            raise

    module = ModuleType(HEALTH_MODULE)

    @dataclass(frozen=True)
    class PaperAutonomousAllocationProposalDbHistoryHealthConfig:
        config_version: str = HEALTH_CONFIG_VERSION
        min_history_report_count: int = 3
        max_watch_history_report_count: int = 0
        max_blocked_history_report_count: int = 0
        max_duplicate_latest_report_generated_at_count: int = 0
        max_latest_age_seconds: int = 86_400
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    module.PaperAutonomousAllocationProposalDbHistoryHealthConfig = (
        PaperAutonomousAllocationProposalDbHistoryHealthConfig
    )
    monkeypatch.setitem(sys.modules, HEALTH_MODULE, module)
    return module


def _install_health_loader(
    monkeypatch: pytest.MonkeyPatch,
    load_paper_autonomous_allocation_proposal_db_history_health_report: object,
) -> None:
    module = ModuleType(HEALTH_LOADER_MODULE)
    module.load_paper_autonomous_allocation_proposal_db_history_health_report = (
        load_paper_autonomous_allocation_proposal_db_history_health_report
    )
    monkeypatch.setitem(sys.modules, HEALTH_LOADER_MODULE, module)


def _reason_count(reason_code: str, report_count: int) -> SimpleNamespace:
    return SimpleNamespace(reason_code=reason_code, report_count=report_count)


def _health_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 24, 13, 0, tzinfo=UTC),
        config_version=HEALTH_CONFIG_VERSION,
        health_status="watch",
        recommended_next_step=(
            "throttle_paper_autonomous_allocation_proposal_history_review"
        ),
        history_report_count=4,
        latest_history_status="watch",
        latest_proposal_status="watch",
        latest_allocated_count=3,
        latest_total_allocated_paper_notional="42.000000",
        max_source_age_seconds=18_000,
        latest_source_age_seconds=3600,
        pass_report_count=2,
        watch_report_count=1,
        blocked_report_count=1,
        duplicate_latest_report_generated_at_count=1,
        reason_code_counts=(
            _reason_count("latest_allocation_proposal_watch", 1),
            _reason_count("source_allocation_proposal_db_history_watch", 1),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_allocation_proposal_db_history_health_cli_requires_enabled_db_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR,
        raising=False,
    )
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("allocation proposal DB history health runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND],
        paper_autonomous_allocation_proposal_db_history_health_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires autonomous allocation proposal DB to be enabled" in (
        captured.err
    )


@pytest.mark.parametrize("limit", ("0", "-1"))
def test_allocation_proposal_db_history_health_cli_rejects_non_positive_limit_before_env_runner_or_connect_or_psycopg_import(
    limit: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    connect_calls = 0
    psycopg_import_calls = 0
    real_import = builtins.__import__

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("allocation proposal DB env should not be read")

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("allocation proposal DB history health runner should not run")

    def forbidden_connect(*_args: Any, **_kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("allocation proposal DB connect should not run")

    def forbidden_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        nonlocal psycopg_import_calls
        if name == "psycopg":
            psycopg_import_calls += 1
            raise AssertionError("psycopg should not be imported")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(
        cli,
        "from_paper_autonomous_allocation_proposal_db_env",
        forbidden_env,
    )
    monkeypatch.setattr(builtins, "__import__", forbidden_import)
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", limit],
        paper_autonomous_allocation_proposal_db_history_health_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert psycopg_import_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed: {COMMAND} limit must be positive" in captured.err


@pytest.mark.parametrize("bad_limit", (0, -1, True, "1", 1.0))
def test_allocation_proposal_db_history_health_helper_rejects_invalid_limit_before_runner_or_connect_or_psycopg_import(
    bad_limit: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner_calls = 0
    connect_calls = 0
    psycopg_import_calls = 0
    real_import = builtins.__import__

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("allocation proposal DB history health runner should not run")

    def forbidden_connect(*_args: Any, **_kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("allocation proposal DB connect should not run")

    def forbidden_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        nonlocal psycopg_import_calls
        if name == "psycopg":
            psycopg_import_calls += 1
            raise AssertionError("psycopg should not be imported")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", forbidden_import)
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))
    helper = getattr(
        cli,
        "_run_paper_autonomous_allocation_proposal_db_history_health",
    )

    with pytest.raises(ValueError, match=f"{COMMAND} limit must be positive"):
        helper(
            dsn="postgresql://allocation-proposal-history-health@localhost/db",
            table_name="paper_autonomous_allocation_proposal_reports",
            limit=bad_limit,
            runner=forbidden_runner,
        )

    assert runner_calls == 0
    assert connect_calls == 0
    assert psycopg_import_calls == 0


def test_allocation_proposal_db_history_health_cli_uses_injected_runner_and_prints_aggregate_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    history_api = _install_or_get_history_api(monkeypatch)
    health_api = _install_or_get_health_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-health@localhost/db"
    table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    _set_allocation_proposal_db_env(monkeypatch, dsn, table_name=table_name)
    calls: list[dict[str, object]] = []
    report = _health_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 25
        history_config = kwargs["history_config"]
        assert (
            type(history_config)
            is history_api.PaperAutonomousAllocationProposalDbHistoryConfig
        )
        assert history_config.config_version == HISTORY_CONFIG_VERSION
        assert history_config.paper_only is True
        assert history_config.report_only is True
        assert history_config.readonly is True
        health_config = kwargs["health_config"]
        assert (
            type(health_config)
            is health_api.PaperAutonomousAllocationProposalDbHistoryHealthConfig
        )
        assert health_config.config_version == HEALTH_CONFIG_VERSION
        assert health_config.paper_only is True
        assert health_config.report_only is True
        assert health_config.readonly is True
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND, "--limit", "25"],
        paper_autonomous_allocation_proposal_db_history_health_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: health_status=watch "
            "recommended_next_step="
            "throttle_paper_autonomous_allocation_proposal_history_review "
            "history_report_count=4 latest_history_status=watch "
            "latest_allocated_count=3 "
            "latest_total_allocated_paper_notional=42.000000 "
            "latest_source_age_seconds=3600 max_source_age_seconds=18000 "
            "pass_report_count=2 watch_report_count=1 blocked_report_count=1 "
            "duplicate_latest_report_generated_at_count=1"
        ),
        (
            "reason_code_counts: latest_allocation_proposal_watch=1 "
            "source_allocation_proposal_db_history_watch=1"
        ),
    ]
    assert captured.err == ""
    for secret in (
        dsn,
        table_name,
        "analytics",
        "paper_autonomous_allocation_proposal_reports",
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_allocation_proposal_db_history_health_cli_without_persist_does_not_read_health_db_env_or_sink(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_history_api(monkeypatch)
    _install_or_get_health_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-health@localhost/db"
    table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    tempting_health_dsn = "postgresql://unused-health-target@localhost/db"
    tempting_health_table_name = "audit.db_history_health_archive"
    _set_allocation_proposal_db_env(monkeypatch, dsn, table_name=table_name)
    _set_allocation_proposal_db_history_health_db_env(
        monkeypatch,
        tempting_health_dsn,
        table_name=tempting_health_table_name,
    )
    env_calls = 0
    sink_calls = 0
    report = _health_report()

    def forbidden_health_db_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("health DB env should not be read without --persist")

    def forbidden_sink(**_kwargs: Any) -> object:
        nonlocal sink_calls
        sink_calls += 1
        raise AssertionError("health DB sink should not run without --persist")

    monkeypatch.setattr(
        cli,
        "from_paper_autonomous_allocation_proposal_db_history_health_db_env",
        forbidden_health_db_env,
    )

    exit_code = main(
        [COMMAND, "--limit", "7"],
        paper_autonomous_allocation_proposal_db_history_health_runner=(
            lambda **_kwargs: report
        ),
        paper_autonomous_allocation_proposal_db_history_health_db_sink=forbidden_sink,
    )

    assert exit_code == 0
    assert env_calls == 0
    assert sink_calls == 0
    captured = capsys.readouterr()
    assert "persisted=" not in captured.out
    for secret in (
        tempting_health_dsn,
        tempting_health_table_name,
        "audit",
        "db_history_health_archive",
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_allocation_proposal_db_history_health_cli_persist_uses_health_db_env_and_prints_marker(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_history_api(monkeypatch)
    _install_or_get_health_api(monkeypatch)
    source_dsn = "postgresql://allocation-proposal-history-health@localhost/db"
    source_table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    health_dsn = "postgresql://allocation-proposal-history-health-target@localhost/db"
    health_table_name = "audit.db_history_health_archive"
    _set_allocation_proposal_db_env(
        monkeypatch,
        source_dsn,
        table_name=source_table_name,
    )
    _set_allocation_proposal_db_history_health_db_env(
        monkeypatch,
        health_dsn,
        table_name=health_table_name,
    )
    report = _health_report()
    runner_calls: list[dict[str, object]] = []
    sink_calls: list[dict[str, object]] = []

    def fake_runner(**kwargs: Any) -> object:
        runner_calls.append(dict(kwargs))
        return report

    def fake_sink(**kwargs: Any) -> object:
        sink_calls.append(dict(kwargs))
        return SimpleNamespace(inserted=True)

    exit_code = main(
        [COMMAND, "--limit", "9", "--persist"],
        paper_autonomous_allocation_proposal_db_history_health_runner=fake_runner,
        paper_autonomous_allocation_proposal_db_history_health_db_sink=fake_sink,
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    assert runner_calls[0]["dsn"] == source_dsn
    assert runner_calls[0]["table_name"] == source_table_name
    assert runner_calls[0]["limit"] == 9
    assert sink_calls == [
        {
            "dsn": health_dsn,
            "report": report,
            "table_name": health_table_name,
        },
    ]
    captured = capsys.readouterr()
    assert captured.out.splitlines()[-1] == f"{COMMAND}: persisted=True"
    assert captured.err == ""
    for secret in (
        source_dsn,
        source_table_name,
        health_dsn,
        health_table_name,
        "analytics",
        "paper_autonomous_allocation_proposal_reports",
        "audit",
        "db_history_health_archive",
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_allocation_proposal_db_history_health_cli_persist_uses_default_health_db_sink(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_history_api(monkeypatch)
    _install_or_get_health_api(monkeypatch)
    source_dsn = "postgresql://allocation-proposal-history-health@localhost/db"
    source_table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    health_dsn = "postgresql://allocation-proposal-history-health-target@localhost/db"
    health_table_name = "audit.db_history_health_archive"
    _set_allocation_proposal_db_env(
        monkeypatch,
        source_dsn,
        table_name=source_table_name,
    )
    _set_allocation_proposal_db_history_health_db_env(
        monkeypatch,
        health_dsn,
        table_name=health_table_name,
    )
    report = _health_report()
    sink_calls: list[dict[str, object]] = []
    fake_psycopg_module = ModuleType(HEALTH_PSYCOPG_MODULE)

    def fake_default_sink(**kwargs: Any) -> object:
        sink_calls.append(dict(kwargs))
        return SimpleNamespace(inserted=True)

    fake_psycopg_module.insert_paper_autonomous_allocation_proposal_db_history_health_report_with_psycopg = (
        fake_default_sink
    )
    monkeypatch.setitem(sys.modules, HEALTH_PSYCOPG_MODULE, fake_psycopg_module)

    exit_code = main(
        [COMMAND, "--persist"],
        paper_autonomous_allocation_proposal_db_history_health_runner=(
            lambda **_kwargs: report
        ),
    )

    assert exit_code == 0
    assert sink_calls == [
        {
            "dsn": health_dsn,
            "report": report,
            "table_name": health_table_name,
        },
    ]
    captured = capsys.readouterr()
    assert captured.out.splitlines()[-1] == f"{COMMAND}: persisted=True"
    assert captured.err == ""


def test_allocation_proposal_db_history_health_cli_persist_prints_false_for_duplicate_sink_noop(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_history_api(monkeypatch)
    _install_or_get_health_api(monkeypatch)
    _set_allocation_proposal_db_env(
        monkeypatch,
        "postgresql://allocation-proposal-history-health@localhost/db",
        table_name="analytics.paper_autonomous_allocation_proposal_reports",
    )
    _set_allocation_proposal_db_history_health_db_env(
        monkeypatch,
        "postgresql://allocation-proposal-history-health-target@localhost/db",
        table_name="audit.db_history_health_archive",
    )
    report = _health_report()

    exit_code = main(
        [COMMAND, "--persist"],
        paper_autonomous_allocation_proposal_db_history_health_runner=(
            lambda **_kwargs: report
        ),
        paper_autonomous_allocation_proposal_db_history_health_db_sink=(
            lambda **_kwargs: SimpleNamespace(inserted=False)
        ),
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines()[-1] == f"{COMMAND}: persisted=False"
    assert captured.err == ""


def test_allocation_proposal_db_history_health_cli_persist_requires_enabled_health_db_before_runner_or_sink(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://allocation-proposal-history-health@localhost/db"
    source_table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    _set_allocation_proposal_db_env(
        monkeypatch,
        source_dsn,
        table_name=source_table_name,
    )
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR,
        raising=False,
    )
    runner_calls = 0
    sink_calls = 0

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("runner should not run without enabled health DB")

    def forbidden_sink(**_kwargs: Any) -> object:
        nonlocal sink_calls
        sink_calls += 1
        raise AssertionError("sink should not run without enabled health DB")

    exit_code = main(
        [COMMAND, "--persist"],
        paper_autonomous_allocation_proposal_db_history_health_runner=forbidden_runner,
        paper_autonomous_allocation_proposal_db_history_health_db_sink=forbidden_sink,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert sink_calls == 0
    captured = capsys.readouterr()
    assert (
        f"{COMMAND} failed: {COMMAND} --persist requires DB-history health DB "
        "to be enabled"
    ) in captured.err
    for secret in (source_dsn, source_table_name, "analytics"):
        assert secret not in captured.out
        assert secret not in captured.err


def test_allocation_proposal_db_history_health_cli_persist_requires_health_db_dsn_before_runner_or_sink(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = "postgresql://allocation-proposal-history-health@localhost/db"
    source_table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    _set_allocation_proposal_db_env(
        monkeypatch,
        source_dsn,
        table_name=source_table_name,
    )
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR,
        raising=False,
    )
    runner_calls = 0
    sink_calls = 0

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("runner should not run without health DB DSN")

    def forbidden_sink(**_kwargs: Any) -> object:
        nonlocal sink_calls
        sink_calls += 1
        raise AssertionError("sink should not run without health DB DSN")

    exit_code = main(
        [COMMAND, "--persist"],
        paper_autonomous_allocation_proposal_db_history_health_runner=forbidden_runner,
        paper_autonomous_allocation_proposal_db_history_health_db_sink=forbidden_sink,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert sink_calls == 0
    captured = capsys.readouterr()
    assert (
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR
        in captured.err
    )
    assert "must be set when DB-history health DB is enabled" in captured.err
    for secret in (source_dsn, source_table_name, "analytics"):
        assert secret not in captured.out
        assert secret not in captured.err


def test_allocation_proposal_db_history_health_cli_persist_runner_failure_redacts_source_and_health_db_secrets_without_sink(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_history_api(monkeypatch)
    _install_or_get_health_api(monkeypatch)
    source_dsn = "postgresql://allocation-proposal-history-health-secret@localhost/db"
    source_table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    health_dsn = "postgresql://allocation-proposal-health-target-secret@localhost/db"
    health_table_name = "audit.db_history_health_archive"
    payload_json = '{"market_slug":"secret-market-slug","question":"nested secret"}'
    question = "Will hidden allocation proposal market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    _set_allocation_proposal_db_env(
        monkeypatch,
        source_dsn,
        table_name=source_table_name,
    )
    _set_allocation_proposal_db_history_health_db_env(
        monkeypatch,
        health_dsn,
        table_name=health_table_name,
    )
    sink_calls = 0

    def broken_runner(**_kwargs: Any) -> object:
        raise RuntimeError(
            f"read failed source_dsn={source_dsn} source_table={source_table_name} "
            f"dsn={health_dsn} table={health_table_name} "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    def forbidden_sink(**_kwargs: Any) -> object:
        nonlocal sink_calls
        sink_calls += 1
        raise AssertionError("sink should not run after runner failure")

    exit_code = main(
        [COMMAND, "--persist"],
        paper_autonomous_allocation_proposal_db_history_health_runner=broken_runner,
        paper_autonomous_allocation_proposal_db_history_health_db_sink=forbidden_sink,
    )

    assert exit_code == 1
    assert sink_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "source_dsn=<redacted-dsn>" in captured.err
    assert "source_table=<redacted-table>" in captured.err
    assert "dsn=<redacted-dsn>" in captured.err
    assert "table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    assert "bare_hash=<redacted-sha256>" in captured.err
    for secret in (
        source_dsn,
        source_table_name,
        health_dsn,
        health_table_name,
        "analytics",
        "paper_autonomous_allocation_proposal_reports",
        "audit",
        "db_history_health_archive",
        payload_json,
        "secret-market-slug",
        "nested secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_allocation_proposal_db_history_health_cli_persist_sink_failure_redacts_source_and_health_db_secrets(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_history_api(monkeypatch)
    _install_or_get_health_api(monkeypatch)
    source_dsn = "postgresql://allocation-proposal-history-health-secret@localhost/db"
    source_table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    health_dsn = "postgresql://allocation-proposal-health-target-secret@localhost/db"
    health_table_name = "audit.db_history_health_archive"
    payload_json = '{"market_slug":"secret-market-slug","question":"nested secret"}'
    question = "Will hidden allocation proposal market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    _set_allocation_proposal_db_env(
        monkeypatch,
        source_dsn,
        table_name=source_table_name,
    )
    _set_allocation_proposal_db_history_health_db_env(
        monkeypatch,
        health_dsn,
        table_name=health_table_name,
    )
    report = _health_report()

    def broken_sink(**_kwargs: Any) -> object:
        raise RuntimeError(
            f"write failed source_dsn={source_dsn} source_table={source_table_name} "
            f"dsn={health_dsn} table={health_table_name} "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    exit_code = main(
        [COMMAND, "--persist"],
        paper_autonomous_allocation_proposal_db_history_health_runner=(
            lambda **_kwargs: report
        ),
        paper_autonomous_allocation_proposal_db_history_health_db_sink=broken_sink,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "source_dsn=<redacted-dsn>" in captured.err
    assert "source_table=<redacted-table>" in captured.err
    assert "dsn=<redacted-dsn>" in captured.err
    assert "table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    assert "bare_hash=<redacted-sha256>" in captured.err
    for secret in (
        source_dsn,
        source_table_name,
        health_dsn,
        health_table_name,
        "analytics",
        "paper_autonomous_allocation_proposal_reports",
        "audit",
        "db_history_health_archive",
        payload_json,
        "secret-market-slug",
        "nested secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_allocation_proposal_db_history_health_summary_prints_real_reducer_report(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
        PaperAutonomousAllocationProposalDbHistoryHealthConfig,
        build_paper_autonomous_allocation_proposal_db_history_health_report,
    )

    report = build_paper_autonomous_allocation_proposal_db_history_health_report(
        (),
        config=PaperAutonomousAllocationProposalDbHistoryHealthConfig(),
        generated_at=datetime(2026, 6, 24, 13, 0, tzinfo=UTC),
    )

    printer = getattr(
        cli,
        "_print_paper_autonomous_allocation_proposal_db_history_health_summary",
    )
    printer(report)

    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: health_status=blocked "
            "recommended_next_step="
            "block_paper_autonomous_allocation_proposal_history_review "
            "history_report_count=0 latest_history_status=none "
            "latest_allocated_count=none "
            "latest_total_allocated_paper_notional=none "
            "latest_source_age_seconds=none max_source_age_seconds=none "
            "pass_report_count=0 watch_report_count=0 blocked_report_count=0 "
            "duplicate_latest_report_generated_at_count=0"
        ),
        "reason_code_counts: none",
    ]
    assert captured.err == ""


def test_allocation_proposal_db_history_health_helper_default_load_path_uses_autocommit_and_closes_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history_api = _install_or_get_history_api(monkeypatch)
    health_api = _install_or_get_health_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-health@localhost/db"
    table_name = "paper_autonomous_allocation_proposal_reports"
    report = _health_report()
    connect_calls: list[tuple[str, bool]] = []
    loader_calls: list[dict[str, object]] = []

    class FakeConnection:
        def __init__(self) -> None:
            self.close_count = 0
            self.commit_count = 0
            self.rollback_count = 0

        def commit(self) -> None:
            self.commit_count += 1
            raise AssertionError("read-only helper must not commit")

        def rollback(self) -> None:
            self.rollback_count += 1
            raise AssertionError("read-only helper must not rollback")

        def close(self) -> None:
            self.close_count += 1

    connection = FakeConnection()

    def fake_connect(connect_dsn: str, *, autocommit: bool = False) -> FakeConnection:
        connect_calls.append((connect_dsn, autocommit))
        return connection

    def fake_load(
        received_connection: object,
        *,
        limit: int,
        table_name: str,
        history_config: object,
        health_config: object,
        generated_at: datetime,
    ) -> object:
        loader_calls.append(
            {
                "connection": received_connection,
                "limit": limit,
                "table_name": table_name,
                "history_config": history_config,
                "health_config": health_config,
                "generated_at": generated_at,
            },
        )
        return report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    _install_health_loader(monkeypatch, fake_load)

    helper = getattr(
        cli,
        "_run_paper_autonomous_allocation_proposal_db_history_health",
    )
    result = helper(
        dsn=dsn,
        table_name=table_name,
        limit=7,
        runner=None,
    )

    assert result is report
    assert connect_calls == [(dsn, True)]
    assert len(loader_calls) == 1
    assert loader_calls[0]["connection"] is connection
    assert loader_calls[0]["limit"] == 7
    assert loader_calls[0]["table_name"] == table_name
    history_config = loader_calls[0]["history_config"]
    assert (
        type(history_config)
        is history_api.PaperAutonomousAllocationProposalDbHistoryConfig
    )
    assert history_config.config_version == HISTORY_CONFIG_VERSION
    health_config = loader_calls[0]["health_config"]
    assert (
        type(health_config)
        is health_api.PaperAutonomousAllocationProposalDbHistoryHealthConfig
    )
    assert health_config.config_version == HEALTH_CONFIG_VERSION
    generated_at = loader_calls[0]["generated_at"]
    assert isinstance(generated_at, datetime)
    assert generated_at.tzinfo is UTC
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_allocation_proposal_db_history_health_helper_raises_on_missing_psycopg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_or_get_history_api(monkeypatch)
    _install_or_get_health_api(monkeypatch)
    _install_health_loader(
        monkeypatch,
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("loader should not run without psycopg"),
        ),
    )
    monkeypatch.setitem(sys.modules, "psycopg", None)
    helper = getattr(
        cli,
        "_run_paper_autonomous_allocation_proposal_db_history_health",
    )
    dsn = "postgresql://allocation-proposal-history-health-secret@localhost/db"

    with pytest.raises(RuntimeError, match="psycopg is required"):
        helper(
            dsn=dsn,
            table_name="paper_autonomous_allocation_proposal_reports",
            limit=7,
            runner=None,
        )


def test_allocation_proposal_db_history_health_helper_uses_shared_redaction_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_or_get_history_api(monkeypatch)
    _install_or_get_health_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-health-secret@localhost/db"
    table_name = "paper_autonomous_allocation_proposal_reports"
    calls: list[dict[str, object]] = []

    def fake_redaction_helper(exc: Exception, *, dsn: str, table_name: str) -> RuntimeError:
        calls.append({"exc": exc, "dsn": dsn, "table_name": table_name})
        return RuntimeError("sentinel redacted health error")

    def broken_runner(**_kwargs: Any) -> object:
        raise RuntimeError("raw secret should be redacted")

    monkeypatch.setattr(
        cli,
        "_redacted_paper_research_packet_db_history_error",
        fake_redaction_helper,
    )
    helper = getattr(
        cli,
        "_run_paper_autonomous_allocation_proposal_db_history_health",
    )

    with pytest.raises(RuntimeError, match="sentinel redacted health error"):
        helper(
            dsn=dsn,
            table_name=table_name,
            limit=7,
            runner=broken_runner,
        )

    assert len(calls) == 1
    assert calls[0]["dsn"] == dsn
    assert calls[0]["table_name"] == table_name


def test_allocation_proposal_db_history_health_cli_runner_failure_redacts_dsn_schema_table_tail_payloads_questions_hashes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_history_api(monkeypatch)
    _install_or_get_health_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-health-secret@localhost/db"
    table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    payload_json = '{"market_slug":"secret-market-slug","question":"nested secret"}'
    question = "Will hidden allocation proposal market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    _set_allocation_proposal_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**_kwargs: Any) -> object:
        raise RuntimeError(
            f"read failed dsn={dsn} table={table_name} "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    exit_code = main(
        [COMMAND],
        paper_autonomous_allocation_proposal_db_history_health_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "dsn=<redacted-dsn>" in captured.err
    assert "table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    assert "bare_hash=<redacted-sha256>" in captured.err
    for secret in (
        dsn,
        table_name,
        "analytics",
        "paper_autonomous_allocation_proposal_reports",
        payload_json,
        "secret-market-slug",
        "nested secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_allocation_proposal_db_history_health_helper_loader_failure_redacts_dsn_schema_table_tail_payloads_questions_hashes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_or_get_history_api(monkeypatch)
    _install_or_get_health_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-health-secret@localhost/db"
    table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    payload_json = '{"market_slug":"secret-market-slug","question":"nested secret"}'
    question = "Will hidden allocation proposal market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"

    class FakeConnection:
        def close(self) -> None:
            pass

    def fake_connect(connect_dsn: str, *, autocommit: bool = False) -> FakeConnection:
        assert connect_dsn == dsn
        assert autocommit is True
        return FakeConnection()

    def fake_load(*_args: Any, **_kwargs: Any) -> object:
        raise RuntimeError(
            f"read failed dsn={dsn} table={table_name} "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    _install_health_loader(monkeypatch, fake_load)
    helper = getattr(
        cli,
        "_run_paper_autonomous_allocation_proposal_db_history_health",
    )

    with pytest.raises(RuntimeError) as exc_info:
        helper(
            dsn=dsn,
            table_name=table_name,
            limit=7,
            runner=None,
        )

    message = str(exc_info.value)
    assert "dsn=<redacted-dsn>" in message
    assert "table=<redacted-table>" in message
    assert "payload_json=<redacted-payload>" in message
    assert "question=<redacted-question>" in message
    assert "report_sha256=<redacted-sha256>" in message
    assert "bare_hash=<redacted-sha256>" in message
    for secret in (
        dsn,
        table_name,
        "analytics",
        "paper_autonomous_allocation_proposal_reports",
        payload_json,
        "secret-market-slug",
        "nested secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in message
