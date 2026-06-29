from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
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


COMMAND = "paper-autonomous-allocation-proposal-db-history-gate"
HISTORY_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-v0"
GATE_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-gate-v0"
HISTORY_MODULE = "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history"
GATE_MODULE = "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate"
GATE_LOADER_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate_load"
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

    class PaperAutonomousAllocationProposalDbHistoryReport:
        pass

    module.DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION = (
        HISTORY_CONFIG_VERSION
    )
    module.PaperAutonomousAllocationProposalDbHistoryConfig = (
        PaperAutonomousAllocationProposalDbHistoryConfig
    )
    module.PaperAutonomousAllocationProposalDbHistoryReport = (
        PaperAutonomousAllocationProposalDbHistoryReport
    )
    monkeypatch.setitem(sys.modules, HISTORY_MODULE, module)
    return module


def _install_or_get_gate_api(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    try:
        return importlib.import_module(GATE_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name != GATE_MODULE:
            raise

    module = ModuleType(GATE_MODULE)

    @dataclass(frozen=True)
    class PaperAutonomousAllocationProposalDbHistoryGateConfig:
        config_version: str = GATE_CONFIG_VERSION
        min_history_report_count: int = 3
        max_latest_age_seconds: int = 86_400
        max_consecutive_latest_watch_count: int = 0
        max_consecutive_latest_blocked_count: int = 0
        max_duplicate_generated_at_count: int = 0
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    @dataclass(frozen=True)
    class PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount:
        reason_code: str
        report_count: int

    @dataclass(frozen=True)
    class PaperAutonomousAllocationProposalDbHistoryGateReport:
        generated_at: datetime
        config_version: str
        gate_status: str
        recommended_next_step: str
        source_report_count: int
        source_history_status: str
        latest_proposal_status: str | None
        latest_screening_gate_status: str | None
        latest_queue_risk_status: str | None
        latest_allocation_input_count: int | None
        latest_allocation_row_count: int | None
        latest_allocated_count: int | None
        latest_total_allocated_paper_notional: Decimal | None
        duplicate_generated_at_count: int
        latest_source_age_seconds: int | None
        reason_code_counts: tuple[
            PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount,
            ...,
        ]
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    module.DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_GATE_CONFIG_VERSION = (
        GATE_CONFIG_VERSION
    )
    module.PaperAutonomousAllocationProposalDbHistoryGateConfig = (
        PaperAutonomousAllocationProposalDbHistoryGateConfig
    )
    module.PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount = (
        PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount
    )
    module.PaperAutonomousAllocationProposalDbHistoryGateReport = (
        PaperAutonomousAllocationProposalDbHistoryGateReport
    )
    monkeypatch.setitem(sys.modules, GATE_MODULE, module)
    return module


def _install_gate_loader(
    monkeypatch: pytest.MonkeyPatch,
    load_paper_autonomous_allocation_proposal_db_history_gate_report: object,
) -> None:
    module = ModuleType(GATE_LOADER_MODULE)
    module.load_paper_autonomous_allocation_proposal_db_history_gate_report = (
        load_paper_autonomous_allocation_proposal_db_history_gate_report
    )
    monkeypatch.setitem(sys.modules, GATE_LOADER_MODULE, module)


def _reason_count(reason_code: str, report_count: int) -> SimpleNamespace:
    return SimpleNamespace(reason_code=reason_code, report_count=report_count)


def _gate_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 24, 13, 0, tzinfo=UTC),
        config_version=GATE_CONFIG_VERSION,
        gate_status="watch",
        recommended_next_step=(
            "throttle_paper_autonomous_allocation_proposal_history_review"
        ),
        source_report_count=3,
        source_history_status="watch",
        latest_proposal_status="watch",
        latest_screening_gate_status="pass",
        latest_queue_risk_status="pass",
        latest_allocation_input_count=2,
        latest_allocation_row_count=2,
        latest_allocated_count=1,
        latest_total_allocated_paper_notional=Decimal("25.000000"),
        duplicate_generated_at_count=0,
        latest_source_age_seconds=3600,
        reason_code_counts=(
            _reason_count("latest_allocation_proposal_watch", 1),
            _reason_count("source_allocation_proposal_db_history_watch", 1),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_allocation_proposal_db_history_gate_cli_requires_enabled_db_config(
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
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE_ENV_VAR,
        raising=False,
    )

    exit_code = main([COMMAND])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires autonomous allocation proposal DB to be enabled" in (
        captured.err
    )


@pytest.mark.parametrize("limit", ("0", "-1"))
def test_allocation_proposal_db_history_gate_cli_rejects_non_positive_limit_before_env_runner_or_connect(
    limit: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    connect_calls = 0

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("allocation proposal DB env should not be read")

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("allocation proposal DB history gate runner should not run")

    def forbidden_connect(*_args: Any, **_kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("allocation proposal DB connect should not run")

    monkeypatch.setattr(
        cli,
        "from_paper_autonomous_allocation_proposal_db_env",
        forbidden_env,
    )
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main([COMMAND, "--limit", limit])

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed: {COMMAND} limit must be positive" in captured.err


@pytest.mark.parametrize("bad_limit", (0, -1, True, "1", 1.0))
def test_allocation_proposal_db_history_gate_helper_rejects_invalid_limit_before_runner_or_connect(
    bad_limit: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("allocation proposal DB history gate runner should not run")

    def forbidden_connect(*_args: Any, **_kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("allocation proposal DB connect should not run")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))
    helper = getattr(cli, "_run_paper_autonomous_allocation_proposal_db_history_gate")

    with pytest.raises(ValueError, match=f"{COMMAND} limit must be positive"):
        helper(
            dsn="postgresql://allocation-proposal-history-gate@localhost/db",
            table_name="paper_autonomous_allocation_proposal_reports",
            limit=bad_limit,
            runner=forbidden_runner,
        )

    assert runner_calls == 0
    assert connect_calls == 0


def test_allocation_proposal_db_history_gate_cli_uses_injected_runner_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    history_api = _install_or_get_history_api(monkeypatch)
    gate_api = _install_or_get_gate_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-gate@localhost/db"
    table_name = "analytics.paper_autonomous_allocation_proposal_reports"
    _set_allocation_proposal_db_env(monkeypatch, dsn, table_name=table_name)
    calls: list[dict[str, object]] = []
    report = _gate_report()

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
        gate_config = kwargs["gate_config"]
        assert (
            type(gate_config)
            is gate_api.PaperAutonomousAllocationProposalDbHistoryGateConfig
        )
        assert gate_config.config_version == GATE_CONFIG_VERSION
        assert gate_config.paper_only is True
        assert gate_config.report_only is True
        assert gate_config.readonly is True
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND, "--limit", "25"],
        paper_autonomous_allocation_proposal_db_history_gate_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: gate_status=watch "
            "recommended_next_step="
            "throttle_paper_autonomous_allocation_proposal_history_review "
            "source_report_count=3 source_history_status=watch "
            "latest_proposal_status=watch latest_screening_gate_status=pass "
            "latest_queue_risk_status=pass latest_allocation_input_count=2 "
            "latest_allocation_row_count=2 latest_allocated_count=1 "
            "latest_total_allocated_paper_notional=25.000000 "
            "duplicate_generated_at_count=0 latest_source_age_seconds=3600"
        ),
        (
            "reason_code_counts: "
            "latest_allocation_proposal_watch=1 "
            "source_allocation_proposal_db_history_watch=1"
        ),
    ]
    assert captured.err == ""
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert table_name not in captured.out
    assert table_name not in captured.err
    assert "paper_autonomous_allocation_proposal_reports" not in captured.out
    assert "paper_autonomous_allocation_proposal_reports" not in captured.err


def test_allocation_proposal_db_history_gate_helper_default_load_path_uses_autocommit_and_closes_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history_api = _install_or_get_history_api(monkeypatch)
    gate_api = _install_or_get_gate_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-gate@localhost/db"
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
        gate_config: object,
        generated_at: datetime,
    ) -> object:
        loader_calls.append(
            {
                "connection": received_connection,
                "limit": limit,
                "table_name": table_name,
                "history_config": history_config,
                "gate_config": gate_config,
                "generated_at": generated_at,
            },
        )
        return report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    _install_gate_loader(monkeypatch, fake_load)

    helper = getattr(cli, "_run_paper_autonomous_allocation_proposal_db_history_gate")
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
    gate_config = loader_calls[0]["gate_config"]
    assert (
        type(gate_config)
        is gate_api.PaperAutonomousAllocationProposalDbHistoryGateConfig
    )
    assert gate_config.config_version == GATE_CONFIG_VERSION
    generated_at = loader_calls[0]["generated_at"]
    assert isinstance(generated_at, datetime)
    assert generated_at.tzinfo is UTC
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_allocation_proposal_db_history_gate_helper_raises_on_missing_psycopg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_or_get_history_api(monkeypatch)
    _install_gate_loader(
        monkeypatch,
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("loader should not run without psycopg"),
        ),
    )
    monkeypatch.setitem(sys.modules, "psycopg", None)
    helper = getattr(cli, "_run_paper_autonomous_allocation_proposal_db_history_gate")
    dsn = "postgresql://allocation-proposal-history-gate-secret@localhost/db"

    with pytest.raises(RuntimeError, match="psycopg is required"):
        helper(
            dsn=dsn,
            table_name="paper_autonomous_allocation_proposal_reports",
            limit=7,
            runner=None,
        )


def test_allocation_proposal_db_history_gate_helper_uses_shared_redaction_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_or_get_history_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-gate-secret@localhost/db"
    table_name = "paper_autonomous_allocation_proposal_reports"
    calls: list[dict[str, object]] = []

    def fake_redaction_helper(exc: Exception, *, dsn: str, table_name: str) -> RuntimeError:
        calls.append({"exc": exc, "dsn": dsn, "table_name": table_name})
        return RuntimeError("sentinel redacted history gate error")

    def broken_runner(**_kwargs: Any) -> object:
        raise RuntimeError("raw secret should be redacted")

    monkeypatch.setattr(
        cli,
        "_redacted_paper_research_packet_db_history_error",
        fake_redaction_helper,
    )
    helper = getattr(cli, "_run_paper_autonomous_allocation_proposal_db_history_gate")

    with pytest.raises(RuntimeError, match="sentinel redacted history gate error"):
        helper(
            dsn=dsn,
            table_name=table_name,
            limit=7,
            runner=broken_runner,
        )

    assert len(calls) == 1
    assert calls[0]["dsn"] == dsn
    assert calls[0]["table_name"] == table_name


def test_allocation_proposal_db_history_gate_cli_runner_failure_redacts_dsn_schema_table_tail_and_payloads(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_history_api(monkeypatch)
    dsn = "postgresql://allocation-proposal-history-gate-secret@localhost/db"
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
        paper_autonomous_allocation_proposal_db_history_gate_runner=broken_runner,
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
        payload_json,
        "secret-market-slug",
        "nested secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


@pytest.mark.parametrize(
    "argv",
    (
        [COMMAND, "--dsn", "postgresql://allocation-proposal@localhost/db"],
        [COMMAND, "--table", "paper_autonomous_allocation_proposal_reports"],
        [COMMAND, "--persist"],
        [COMMAND, "--fast"],
        [COMMAND, "--live"],
        [COMMAND, "--auth", "token"],
        [COMMAND, "--wallet", "wallet"],
        [COMMAND, "--private-key", "secret"],
        [COMMAND, "--api-key", "secret"],
        [COMMAND, "--account", "account"],
        [COMMAND, "--order", "order"],
        [COMMAND, "--trade"],
        [COMMAND, "--execute"],
        [COMMAND, "--submit"],
        [COMMAND, "--approve"],
    ),
)
def test_allocation_proposal_db_history_gate_cli_rejects_db_persist_fast_live_auth_wallet_account_order_and_execution_flags(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err
