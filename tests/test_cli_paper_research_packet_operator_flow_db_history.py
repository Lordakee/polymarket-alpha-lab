from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.supabase_paper_research_packet_operator_flow_config import (
    PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-research-packet-operator-flow-db-history"
HISTORY_CONFIG_VERSION = "paper-research-packet-operator-flow-db-history-v0"
HISTORY_MODULE = "polymarket_alpha_lab.paper_research_packet_operator_flow_db_history"
LOADER_MODULE = (
    "polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_load"
)


def _set_operator_flow_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = "paper_research_packet_operator_flow_reports",
) -> None:
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR,
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
    class PaperResearchPacketOperatorFlowDbHistoryConfig:
        config_version: str = HISTORY_CONFIG_VERSION
        min_report_count: int = 3
        max_blocked_flow_report_count: int = 0
        max_watch_flow_report_count: int = 0
        max_duplicate_generated_at_count: int = 0
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    class PaperResearchPacketOperatorFlowDbHistoryReport:
        pass

    module.DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_HISTORY_CONFIG_VERSION = (
        HISTORY_CONFIG_VERSION
    )
    module.PaperResearchPacketOperatorFlowDbHistoryConfig = (
        PaperResearchPacketOperatorFlowDbHistoryConfig
    )
    module.PaperResearchPacketOperatorFlowDbHistoryReport = (
        PaperResearchPacketOperatorFlowDbHistoryReport
    )
    monkeypatch.setitem(sys.modules, HISTORY_MODULE, module)
    return module


def _install_loader(
    monkeypatch: pytest.MonkeyPatch,
    load_paper_research_packet_operator_flow_db_history_report: object,
) -> None:
    module = ModuleType(LOADER_MODULE)
    module.load_paper_research_packet_operator_flow_db_history_report = (
        load_paper_research_packet_operator_flow_db_history_report
    )
    monkeypatch.setitem(sys.modules, LOADER_MODULE, module)


def _status_row(flow_status: str, status_count: int) -> SimpleNamespace:
    return SimpleNamespace(flow_status=flow_status, status_count=status_count)


def _reason_row(reason_code: str, report_count: int) -> SimpleNamespace:
    return SimpleNamespace(reason_code=reason_code, report_count=report_count)


def _history_report(
    *,
    latest_reason_codes: tuple[str, ...] = ("operator_flow_watch",),
    reason_code_rows: tuple[object, ...] = (
        _reason_row("operator_flow_pass", 2),
        _reason_row("operator_flow_watch", 1),
    ),
    reason_codes: tuple[str, ...] = (
        "duplicate_generated_at_threshold_exceeded",
    ),
) -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 23, 13, 0, tzinfo=UTC),
        config_version=HISTORY_CONFIG_VERSION,
        history_status="watch",
        report_count=3,
        first_report_generated_at=datetime(2026, 6, 23, 8, 0, tzinfo=UTC),
        latest_report_generated_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
        latest_flow_status="watch",
        latest_packet_row_count=3,
        latest_quality_status="watch",
        latest_history_status="pass",
        flow_status_rows=(
            _status_row("pass", 2),
            _status_row("watch", 1),
            _status_row("blocked", 0),
        ),
        duplicate_generated_at_count=1,
        consecutive_latest_pass_count=0,
        consecutive_latest_watch_count=1,
        consecutive_latest_blocked_count=0,
        latest_reason_codes=latest_reason_codes,
        reason_code_rows=reason_code_rows,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_operator_flow_db_history_cli_requires_enabled_operator_flow_db_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(
        PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(
        PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR,
        raising=False,
    )
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("operator-flow DB history runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND],
        paper_research_packet_operator_flow_db_history_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert (
        f"{COMMAND} requires paper research packet operator-flow DB to be enabled"
        in captured.err
    )


@pytest.mark.parametrize("limit", ("0", "-1"))
def test_operator_flow_db_history_cli_rejects_non_positive_limit_before_env_runner_or_connect(
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
        raise AssertionError("operator-flow DB env should not be read")

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("operator-flow DB history runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("operator-flow DB connect should not run")

    monkeypatch.setattr(cli, "from_paper_research_packet_operator_flow_db_env", forbidden_env)
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", limit],
        paper_research_packet_operator_flow_db_history_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed: {COMMAND} limit must be positive" in captured.err


@pytest.mark.parametrize("bad_limit", (0, -1, True, "1", 1.0))
def test_operator_flow_db_history_helper_rejects_invalid_limit_before_runner_or_connect(
    bad_limit: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("operator-flow DB history runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("operator-flow DB connect should not run")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))
    helper = getattr(cli, "_run_paper_research_packet_operator_flow_db_history")

    with pytest.raises(ValueError, match=f"{COMMAND} limit must be positive"):
        helper(
            dsn="postgresql://operator-flow-history.example.invalid/db",
            table_name="paper_research_packet_operator_flow_reports",
            limit=bad_limit,
            runner=forbidden_runner,
        )

    assert runner_calls == 0
    assert connect_calls == 0


def test_operator_flow_db_history_cli_uses_injected_runner_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    api = _install_or_get_history_api(monkeypatch)
    dsn = "postgresql://operator-flow-history.example.invalid/db"
    table_name = "analytics.paper_research_packet_operator_flow_reports"
    _set_operator_flow_db_env(monkeypatch, dsn, table_name=table_name)
    calls: list[dict[str, object]] = []
    report = _history_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 25
        config = kwargs["config"]
        assert type(config) is api.PaperResearchPacketOperatorFlowDbHistoryConfig
        assert config.config_version == HISTORY_CONFIG_VERSION
        assert config.paper_only is True
        assert config.report_only is True
        assert config.readonly is True
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND, "--limit", "25"],
        paper_research_packet_operator_flow_db_history_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: history_status=watch report_count=3 "
            "first_report_generated_at=2026-06-23T08:00:00+00:00 "
            "latest_report_generated_at=2026-06-23T12:00:00+00:00 "
            "latest_flow_status=watch latest_packet_row_count=3 "
            "latest_quality_status=watch latest_history_status=pass "
            "pass=2 watch=1 blocked=0 duplicate_generated_at_count=1 "
            "consecutive_latest_pass_count=0 consecutive_latest_watch_count=1 "
            "consecutive_latest_blocked_count=0"
        ),
        "flow_status_rows: pass=2 watch=1 blocked=0",
        "latest_reason_codes: operator_flow_watch",
        "reason_code_rows: operator_flow_pass=2 operator_flow_watch=1",
        "reason_codes: duplicate_generated_at_threshold_exceeded",
    ]
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert table_name not in captured.out
    assert table_name not in captured.err
    assert "paper_research_packet_operator_flow_reports" not in captured.out
    assert "paper_research_packet_operator_flow_reports" not in captured.err


def test_operator_flow_db_history_helper_default_load_path_uses_autocommit_and_closes_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _install_or_get_history_api(monkeypatch)
    dsn = "postgresql://operator-flow-history.example.invalid/db"
    table_name = "paper_research_packet_operator_flow_reports"
    report = _history_report()
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
        config: object,
        generated_at: datetime,
    ) -> object:
        loader_calls.append(
            {
                "connection": received_connection,
                "limit": limit,
                "table_name": table_name,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    _install_loader(monkeypatch, fake_load)

    helper = getattr(cli, "_run_paper_research_packet_operator_flow_db_history")
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
    config = loader_calls[0]["config"]
    assert type(config) is api.PaperResearchPacketOperatorFlowDbHistoryConfig
    assert config.config_version == HISTORY_CONFIG_VERSION
    generated_at = loader_calls[0]["generated_at"]
    assert isinstance(generated_at, datetime)
    assert generated_at.tzinfo is UTC
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_operator_flow_db_history_cli_runner_failure_redacts_dsn_schema_table_tail_and_payloads(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_history_api(monkeypatch)
    dsn = "postgresql://operator-flow-history-secret.example.invalid/db"
    table_name = "analytics.paper_research_packet_operator_flow_reports"
    payload_json = '{"secret":"operator-flow-payload-json-secret"}'
    question = "Will hidden operator-flow market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    _set_operator_flow_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(
            f"read failed dsn={dsn} table={table_name} "
            "tail=paper_research_packet_operator_flow_reports "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    exit_code = main(
        [COMMAND],
        paper_research_packet_operator_flow_db_history_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "dsn=<redacted-dsn>" in captured.err
    assert "table=<redacted-table>" in captured.err
    assert "tail=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    assert "bare_hash=<redacted-sha256>" in captured.err
    for secret in (
        dsn,
        table_name,
        "paper_research_packet_operator_flow_reports",
        payload_json,
        "operator-flow-payload-json-secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


@pytest.mark.parametrize(
    "argv",
    (
        [COMMAND, "--dsn", "postgresql://operator-flow-history.example.invalid/db"],
        [COMMAND, "--table", "paper_research_packet_operator_flow_reports"],
        [COMMAND, "--persist"],
    ),
)
def test_operator_flow_db_history_cli_rejects_dsn_table_and_persist_flags(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err
