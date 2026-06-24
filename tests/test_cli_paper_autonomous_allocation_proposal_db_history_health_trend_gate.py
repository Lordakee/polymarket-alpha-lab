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


COMMAND = "paper-autonomous-allocation-proposal-db-history-health-trend-gate"
HISTORY_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-v0"
HEALTH_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-health-v0"
TREND_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-health-trend-v0"
GATE_CONFIG_VERSION = (
    "paper-autonomous-allocation-proposal-db-history-health-trend-gate-v0"
)
HISTORY_MODULE = "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history"
HEALTH_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health"
)
TREND_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend"
)
GATE_MODULE = (
    "polymarket_alpha_lab."
    "paper_autonomous_allocation_proposal_db_history_health_trend_gate"
)
GATE_LOADER_MODULE = (
    "polymarket_alpha_lab."
    "paper_autonomous_allocation_proposal_db_history_health_trend_gate_load"
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


def _install_or_get_trend_api(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
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


def _install_or_get_gate_api(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    try:
        return importlib.import_module(GATE_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name != GATE_MODULE:
            raise

    module = ModuleType(GATE_MODULE)

    @dataclass(frozen=True)
    class PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig:
        config_version: str = GATE_CONFIG_VERSION
        min_health_report_count: int = 3
        max_latest_age_seconds: int = 86_400
        max_consecutive_latest_watch_count: int = 0
        max_consecutive_latest_blocked_count: int = 0
        max_duplicate_generated_at_count: int = 0
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    module.PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig = (
        PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig
    )
    monkeypatch.setitem(sys.modules, GATE_MODULE, module)
    return module


def _install_gate_loader(
    monkeypatch: pytest.MonkeyPatch,
    load_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report: object,
) -> None:
    module = ModuleType(GATE_LOADER_MODULE)
    module.load_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report = (
        load_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report
    )
    monkeypatch.setitem(sys.modules, GATE_LOADER_MODULE, module)


def _reason_count(reason_code: str, report_count: int) -> SimpleNamespace:
    return SimpleNamespace(reason_code=reason_code, report_count=report_count)


def _gate_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 24, 13, 0, tzinfo=UTC),
        config_version=GATE_CONFIG_VERSION,
        gate_status="pass",
        recommended_next_step=(
            "allow_paper_autonomous_allocation_proposal_db_history_health_trend_review"
        ),
        source_health_report_count=3,
        latest_health_status="pass",
        latest_source_age_seconds=300,
        duplicate_generated_at_count=0,
        consecutive_latest_watch_count=0,
        consecutive_latest_blocked_count=0,
        watch_report_count_delta=0,
        blocked_report_count_delta=0,
        reason_code_counts=(
            _reason_count(
                "paper_autonomous_allocation_proposal_db_history_health_trend_gate_passed",
                1,
            ),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_allocation_proposal_db_history_health_trend_gate_command_uses_injected_runner(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    history_api = _install_or_get_history_api(monkeypatch)
    health_api = _install_or_get_health_api(monkeypatch)
    trend_api = _install_or_get_trend_api(monkeypatch)
    gate_api = _install_or_get_gate_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-health-trend-gate.example.invalid/db"
    table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    _set_allocation_proposal_db_env(monkeypatch, dsn, table_name=table_name)
    runner_calls: list[dict[str, object]] = []
    report = _gate_report()

    def runner(**kwargs: Any) -> object:
        runner_calls.append(kwargs)
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 7
        assert (
            type(kwargs["history_config"])
            is history_api.PaperAutonomousAllocationProposalDbHistoryConfig
        )
        assert (
            type(kwargs["health_config"])
            is health_api.PaperAutonomousAllocationProposalDbHistoryHealthConfig
        )
        assert (
            type(kwargs["trend_config"])
            is trend_api.PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig
        )
        assert (
            type(kwargs["gate_config"])
            is gate_api.PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig
        )
        assert isinstance(kwargs["generated_at"], datetime)
        assert kwargs["generated_at"].tzinfo is UTC
        return report

    result = main(
        [COMMAND, "--limit", "7"],
        paper_autonomous_allocation_proposal_db_history_health_trend_gate_runner=runner,
    )

    assert result == 0
    assert len(runner_calls) == 1
    out = capsys.readouterr().out
    assert f"{COMMAND}:" in out
    assert "gate_status=pass" in out
    assert (
        "recommended_next_step="
        "allow_paper_autonomous_allocation_proposal_db_history_health_trend_review"
        in out
    )
    assert "persisted=" not in out
    for secret in (
        dsn,
        table_name,
        "analytics",
        "paper_autonomous_allocation_proposal_reports",
    ):
        assert secret not in out


@pytest.mark.parametrize("limit", ("0", "-1"))
def test_health_trend_gate_helper_validates_limit_before_runner_or_imports(
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
        raise AssertionError("health trend gate runner should not run")

    def forbidden_connect(*_args: Any, **_kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg connect should not run")

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
        paper_autonomous_allocation_proposal_db_history_health_trend_gate_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert psycopg_import_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed: {COMMAND} limit must be positive" in captured.err


def test_health_trend_gate_helper_uses_psycopg_autocommit_and_closes_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history_api = _install_or_get_history_api(monkeypatch)
    health_api = _install_or_get_health_api(monkeypatch)
    trend_api = _install_or_get_trend_api(monkeypatch)
    gate_api = _install_or_get_gate_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-health-trend-gate.example.invalid/db"
    table_name = "paper_autonomous_allocation_proposal_reports"
    report = _gate_report()
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
        trend_config: object,
        gate_config: object,
        generated_at: datetime,
    ) -> object:
        loader_calls.append(
            {
                "connection": received_connection,
                "limit": limit,
                "table_name": table_name,
                "history_config": history_config,
                "health_config": health_config,
                "trend_config": trend_config,
                "gate_config": gate_config,
                "generated_at": generated_at,
            },
        )
        return report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    _install_gate_loader(monkeypatch, fake_load)

    helper = getattr(
        cli,
        "_run_paper_autonomous_allocation_proposal_db_history_health_trend_gate",
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
        type(loader_calls[0]["history_config"])
        is history_api.PaperAutonomousAllocationProposalDbHistoryConfig
    )
    assert (
        type(loader_calls[0]["health_config"])
        is health_api.PaperAutonomousAllocationProposalDbHistoryHealthConfig
    )
    assert (
        type(loader_calls[0]["trend_config"])
        is trend_api.PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig
    )
    assert (
        type(loader_calls[0]["gate_config"])
        is gate_api.PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig
    )
    assert isinstance(loader_calls[0]["generated_at"], datetime)
    assert loader_calls[0]["generated_at"].tzinfo is UTC
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_health_trend_gate_default_path_redacts_dsn_and_table_on_loader_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_history_api(monkeypatch)
    _install_or_get_health_api(monkeypatch)
    _install_or_get_trend_api(monkeypatch)
    _install_or_get_gate_api(monkeypatch)
    dsn = "postgresql://user:secret@example.invalid/db"
    table_name = "private_schema.paper_autonomous_allocation_proposal_reports"
    _set_allocation_proposal_db_env(monkeypatch, dsn, table_name=table_name)

    class FakeConnection:
        def close(self) -> None:
            pass

    def fake_connect(connect_dsn: str, *, autocommit: bool = False) -> FakeConnection:
        assert connect_dsn == dsn
        assert autocommit is True
        return FakeConnection()

    def broken_load(*_args: Any, **_kwargs: Any) -> object:
        raise RuntimeError(
            f"loader failed dsn={dsn} table={table_name} "
            "tail=paper_autonomous_allocation_proposal_reports",
        )

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    _install_gate_loader(monkeypatch, broken_load)

    exit_code = main([COMMAND])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "dsn=<redacted-dsn>" in captured.err
    assert "table=<redacted-table>" in captured.err
    assert "tail=<redacted-table>" in captured.err
    for secret in (
        dsn,
        table_name,
        "private_schema",
        "paper_autonomous_allocation_proposal_reports",
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_health_trend_gate_runner_failure_redacts_direct_operator_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_history_api(monkeypatch)
    _install_or_get_health_api(monkeypatch)
    _install_or_get_trend_api(monkeypatch)
    _install_or_get_gate_api(monkeypatch)
    dsn = "postgresql://user:secret@example.invalid/db"
    table_name = "private_schema.paper_autonomous_allocation_proposal_reports"
    market_slug = "secret-market-slug"
    question = "Will the direct secret question resolve yes?"
    account = "secret-account-id"
    wallet = "0xsecretwallet"
    order_identifier = "secret-order-id"
    _set_allocation_proposal_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**_kwargs: Any) -> object:
        raise RuntimeError(
            f"runner failed dsn={dsn} table={table_name} "
            f"market_slug={market_slug} question={question} side=YES action=buy "
            "recommendation_score=0.99 "
            "allocation_rows_json=[{'side':'YES','action':'buy'}] "
            f"account={account} wallet={wallet} order_id={order_identifier}",
        )

    exit_code = main(
        [COMMAND],
        paper_autonomous_allocation_proposal_db_history_health_trend_gate_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    for redacted in (
        "dsn=<redacted-dsn>",
        "table=<redacted-table>",
        "market_slug=<redacted-market-slug>",
        "question=<redacted-question>",
        "side=<redacted-side>",
        "action=<redacted-action>",
        "recommendation_score=<redacted-recommendation-score>",
        "allocation_rows_json=<redacted-allocation-rows>",
        "account=<redacted-account>",
        "wallet=<redacted-wallet>",
        "order_id=<redacted-order>",
    ):
        assert redacted in captured.err
    for secret in (
        dsn,
        table_name,
        "private_schema",
        "paper_autonomous_allocation_proposal_reports",
        market_slug,
        question,
        "YES",
        "buy",
        "0.99",
        "[{'side':'YES','action':'buy'}]",
        account,
        wallet,
        order_identifier,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_health_trend_gate_summary_suppresses_sensitive_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = SimpleNamespace(
        gate_status="pass",
        recommended_next_step=(
            "allow_paper_autonomous_allocation_proposal_db_history_health_trend_review"
        ),
        source_health_report_count=3,
        latest_health_status="pass",
        latest_source_age_seconds=300,
        duplicate_generated_at_count=0,
        consecutive_latest_watch_count=0,
        consecutive_latest_blocked_count=0,
        watch_report_count_delta=0,
        blocked_report_count_delta=0,
        reason_code_counts=(
            SimpleNamespace(
                reason_code=(
                    "paper_autonomous_allocation_proposal_db_history_health_trend_gate_passed"
                ),
                report_count=1,
            ),
        ),
        dsn="postgresql://user:secret@example.invalid/db",
        table_name="private_schema.paper_autonomous_allocation_proposal_reports",
        payload_json={"market_slug": "secret-market", "question": "secret question"},
        report_sha256="a" * 64,
        allocation_rows_json=[{"side": "YES", "action": "buy"}],
        recommendation_score="0.99",
        market_slug="secret-market",
        question="secret question",
        side="YES",
        action="buy",
    )
    printer = getattr(
        cli,
        "_print_paper_autonomous_allocation_proposal_db_history_health_trend_gate_summary",
    )

    printer(report)

    captured = capsys.readouterr()
    assert captured.err == ""
    assert f"{COMMAND}:" in captured.out
    assert "gate_status=pass" in captured.out
    assert "source_health_report_count=3" in captured.out
    assert (
        "reason_code_counts="
        "paper_autonomous_allocation_proposal_db_history_health_trend_gate_passed=1"
        in captured.out
    )
    for forbidden in (
        "postgresql://user:secret@example.invalid/db",
        "private_schema.paper_autonomous_allocation_proposal_reports",
        "private_schema",
        "payload_json",
        "secret-market",
        "secret question",
        "report_sha256",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "allocation_rows_json",
        "YES",
        "buy",
        "recommendation_score",
        "0.99",
        "market_slug",
        "question",
        "side=",
        "action=",
        "account",
        "wallet",
        "order",
    ):
        assert forbidden not in captured.out
