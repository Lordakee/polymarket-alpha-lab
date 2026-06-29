from __future__ import annotations

import builtins
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_db_history_health_config import (
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-autonomous-allocation-proposal-db-history-health-trend"
HEALTH_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-health-v0"
TREND_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-health-trend-v0"
HEALTH_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health"
)
TREND_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend"
)
TREND_LOADER_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_load"
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


def _install_or_get_health_api(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    import importlib

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


def _install_or_get_trend_api(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    import importlib

    try:
        return importlib.import_module(TREND_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name != TREND_MODULE:
            raise

    module = ModuleType(TREND_MODULE)

    @dataclass(frozen=True)
    class PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig:
        config_version: str = TREND_CONFIG_VERSION
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    module.PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig = (
        PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig
    )
    monkeypatch.setitem(sys.modules, TREND_MODULE, module)
    return module


def _install_trend_loader(
    monkeypatch: pytest.MonkeyPatch,
    load_paper_autonomous_allocation_proposal_db_history_health_trend_report: object,
) -> None:
    module = ModuleType(TREND_LOADER_MODULE)
    module.load_paper_autonomous_allocation_proposal_db_history_health_trend_report = (
        load_paper_autonomous_allocation_proposal_db_history_health_trend_report
    )
    monkeypatch.setitem(sys.modules, TREND_LOADER_MODULE, module)


def _trend_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 24, 13, 0, tzinfo=UTC),
        config_version=TREND_CONFIG_VERSION,
        source_health_report_count=4,
        latest_health_status="watch",
        history_report_count_delta=1,
        pass_report_count_delta=0,
        watch_report_count_delta=1,
        blocked_report_count_delta=0,
        latest_allocated_count_delta=2,
        latest_total_allocated_paper_notional_delta=Decimal("15.750000"),
        duplicate_generated_at_count=1,
        consecutive_latest_watch_count=2,
        consecutive_latest_blocked_count=0,
        latest_reason_code_counts=(
            ("latest_allocation_proposal_db_history_watch", 1),
            ("stale_allocation_proposal_db_history", 1),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_allocation_proposal_db_history_health_trend_cli_requires_enabled_db_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR,
        raising=False,
    )

    exit_code = main([COMMAND])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires DB-history health DB to be enabled" in captured.err


@pytest.mark.parametrize("limit", ("0", "-1"))
def test_allocation_proposal_db_history_health_trend_cli_rejects_non_positive_limit_before_env_runner_or_connect_or_psycopg_import(
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
        raise AssertionError(
            "allocation proposal DB history health trend runner should not run",
        )

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
        "from_paper_autonomous_allocation_proposal_db_history_health_db_env",
        forbidden_env,
    )
    monkeypatch.setattr(builtins, "__import__", forbidden_import)
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", limit],
        paper_autonomous_allocation_proposal_db_history_health_trend_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert psycopg_import_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed: {COMMAND} limit must be positive" in captured.err


@pytest.mark.parametrize("bad_limit", (0, -1, True, "1", 1.0))
def test_allocation_proposal_db_history_health_trend_helper_rejects_invalid_limit_before_runner_or_connect_or_psycopg_import(
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
        raise AssertionError(
            "allocation proposal DB history health trend runner should not run",
        )

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
        "_run_paper_autonomous_allocation_proposal_db_history_health_trend",
    )

    with pytest.raises(ValueError, match=f"{COMMAND} limit must be positive"):
        helper(
            dsn="postgresql://allocation-proposal:secret@localhost:54322/db",
            table_name="paper_autonomous_allocation_proposal_db_history_health_reports",
            limit=bad_limit,
            runner=forbidden_runner,
        )

    assert runner_calls == 0
    assert connect_calls == 0
    assert psycopg_import_calls == 0


def test_allocation_proposal_db_history_health_trend_cli_uses_injected_runner_and_prints_aggregate_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    health_api = _install_or_get_health_api(monkeypatch)
    trend_api = _install_or_get_trend_api(monkeypatch)
    dsn = "postgresql://allocation-proposal:secret@localhost:54322/db"
    table_name = (
        "analytics.paper_autonomous_allocation_proposal_db_history_health_reports"
    )
    _set_allocation_proposal_db_history_health_db_env(
        monkeypatch,
        dsn,
        table_name=table_name,
    )
    calls: list[dict[str, object]] = []
    report = _trend_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert "history_config" not in kwargs
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 25
        health_config = kwargs["health_config"]
        assert (
            type(health_config)
            is health_api.PaperAutonomousAllocationProposalDbHistoryHealthConfig
        )
        trend_config = kwargs["trend_config"]
        assert (
            type(trend_config)
            is trend_api.PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig
        )
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND, "--limit", "25"],
        paper_autonomous_allocation_proposal_db_history_health_trend_runner=fake_runner,
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: trend_count=4 latest_health_status=watch "
            "history_report_count_delta=1 pass_report_count_delta=0 "
            "watch_report_count_delta=1 blocked_report_count_delta=0 "
            "latest_allocated_count_delta=2 "
            "latest_total_allocated_paper_notional_delta=15.750000 "
            "duplicate_generated_at_count=1 "
            "consecutive_latest_watch_count=2 "
            "consecutive_latest_blocked_count=0 "
            "latest_reason_code_counts="
            "latest_allocation_proposal_db_history_watch=1,"
            "stale_allocation_proposal_db_history=1"
        ),
    ]
    assert captured.err == ""
    for secret in (
        dsn,
        table_name,
        "analytics",
        "paper_autonomous_allocation_proposal_db_history_health_reports",
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_allocation_proposal_db_history_health_trend_summary_prints_real_reducer_report(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend import (
        PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
        build_paper_autonomous_allocation_proposal_db_history_health_trend_report,
    )

    report = build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
        (),
        config=PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig(),
        generated_at=datetime(2026, 6, 24, 13, 0, tzinfo=UTC),
    )

    printer = getattr(
        cli,
        "_print_paper_autonomous_allocation_proposal_db_history_health_trend_summary",
    )
    printer(report)

    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: trend_count=0 latest_health_status=none "
            "history_report_count_delta=none pass_report_count_delta=none "
            "watch_report_count_delta=none blocked_report_count_delta=none "
            "latest_allocated_count_delta=none "
            "latest_total_allocated_paper_notional_delta=none "
            "duplicate_generated_at_count=0 "
            "consecutive_latest_watch_count=0 "
            "consecutive_latest_blocked_count=0 "
            "latest_reason_code_counts=none"
        ),
    ]
    assert captured.err == ""


def test_allocation_proposal_db_history_health_trend_helper_default_load_path_uses_autocommit_and_closes_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    health_api = _install_or_get_health_api(monkeypatch)
    trend_api = _install_or_get_trend_api(monkeypatch)
    dsn = "postgresql://allocation-proposal:secret@localhost:54322/db"
    table_name = "paper_autonomous_allocation_proposal_db_history_health_reports"
    report = _trend_report()
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
        health_config: object,
        trend_config: object,
        generated_at: datetime,
    ) -> object:
        loader_calls.append(
            {
                "connection": received_connection,
                "limit": limit,
                "table_name": table_name,
                "health_config": health_config,
                "trend_config": trend_config,
                "generated_at": generated_at,
            },
        )
        return report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    _install_trend_loader(monkeypatch, fake_load)

    helper = getattr(
        cli,
        "_run_paper_autonomous_allocation_proposal_db_history_health_trend",
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
    assert (
        type(loader_calls[0]["health_config"])
        is health_api.PaperAutonomousAllocationProposalDbHistoryHealthConfig
    )
    assert (
        type(loader_calls[0]["trend_config"])
        is trend_api.PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig
    )
    assert isinstance(loader_calls[0]["generated_at"], datetime)
    assert loader_calls[0]["generated_at"].tzinfo is UTC
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_allocation_proposal_db_history_health_trend_helper_raises_on_missing_psycopg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_or_get_health_api(monkeypatch)
    _install_or_get_trend_api(monkeypatch)
    _install_trend_loader(
        monkeypatch,
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("loader should not run without psycopg"),
        ),
    )
    monkeypatch.setitem(sys.modules, "psycopg", None)
    helper = getattr(
        cli,
        "_run_paper_autonomous_allocation_proposal_db_history_health_trend",
    )

    with pytest.raises(RuntimeError, match="psycopg is required"):
        helper(
            dsn="postgresql://allocation-proposal:secret@localhost:54322/db",
            table_name="paper_autonomous_allocation_proposal_db_history_health_reports",
            limit=7,
            runner=None,
        )


def test_allocation_proposal_db_history_health_trend_helper_uses_shared_redaction_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_or_get_health_api(monkeypatch)
    _install_or_get_trend_api(monkeypatch)
    dsn = "postgresql://allocation-proposal:secret@localhost:54322/db"
    table_name = "paper_autonomous_allocation_proposal_db_history_health_reports"
    calls: list[dict[str, object]] = []

    def fake_redaction_helper(exc: Exception, *, dsn: str, table_name: str) -> RuntimeError:
        calls.append({"exc": exc, "dsn": dsn, "table_name": table_name})
        return RuntimeError("sentinel redacted health trend error")

    def broken_runner(**_kwargs: Any) -> object:
        raise RuntimeError("raw secret should be redacted")

    monkeypatch.setattr(
        cli,
        "_redacted_paper_research_packet_db_history_error",
        fake_redaction_helper,
    )
    helper = getattr(
        cli,
        "_run_paper_autonomous_allocation_proposal_db_history_health_trend",
    )

    with pytest.raises(RuntimeError, match="sentinel redacted health trend error"):
        helper(
            dsn=dsn,
            table_name=table_name,
            limit=7,
            runner=broken_runner,
        )

    assert len(calls) == 1
    assert calls[0]["dsn"] == dsn
    assert calls[0]["table_name"] == table_name
