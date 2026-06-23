from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.paper_research_packet_db_history import (
    DEFAULT_PAPER_RESEARCH_PACKET_DB_HISTORY_CONFIG_VERSION,
    PaperResearchPacketDbHistoryConfig,
)
from polymarket_alpha_lab.supabase_paper_research_packet_config import (
    PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-research-packet-db-history"
HISTORY_CONFIG_VERSION = DEFAULT_PAPER_RESEARCH_PACKET_DB_HISTORY_CONFIG_VERSION


def _set_packet_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = "paper_research_packet_archive",
) -> None:
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR, table_name)


def _history_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
        config_version=HISTORY_CONFIG_VERSION,
        report_count=2,
        first_report_generated_at=datetime(2026, 6, 23, 8, 0, tzinfo=UTC),
        latest_report_generated_at=datetime(2026, 6, 23, 10, 0, tzinfo=UTC),
        duplicate_generated_at_count=1,
        latest_packet_config_version="paper-research-packet-v1",
        latest_input_row_count=5,
        latest_packet_row_count=2,
        latest_included_count=2,
        latest_skipped_count=0,
        latest_high_priority_count=1,
        latest_medium_priority_count=1,
        latest_low_priority_count=0,
        latest_top_packet_rank=1,
        latest_top_packet_market_slug="market-alpha",
        latest_top_packet_side="yes",
        latest_top_packet_research_priority="high",
        latest_top_packet_recommendation_score=Decimal("0.910000"),
        latest_top_packet_net_edge=Decimal("0.080000"),
        latest_top_packet_allocated_notional=Decimal("12.500000"),
        latest_top_packet_requested_notional=Decimal("15.000000"),
        latest_top_packet_reason_codes=("positive_edge", "settlement_review"),
        question="Will secret market resolve yes?",
        required_checks=("secret_check",),
        packet_rows=(SimpleNamespace(question="Do not print this question"),),
        payload_json='{"secret":"payload-json-secret"}',
        report_sha256="report-sha-secret",
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_packet_db_history_cli_requires_enabled_packet_db_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR, raising=False)
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("paper research packet DB history runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND],
        paper_research_packet_db_history_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires paper research packet DB to be enabled" in captured.err


def test_packet_db_history_cli_requires_packet_db_dsn(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.delenv(PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.setenv(
        PAPER_RESEARCH_PACKET_DB_TABLE_ENV_VAR,
        "paper_research_packet_archive",
    )
    runner_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("paper research packet DB history runner should not run")

    exit_code = main(
        [COMMAND],
        paper_research_packet_db_history_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert runner_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{PAPER_RESEARCH_PACKET_DB_DSN_ENV_VAR} must be set when DB is enabled" in (
        captured.err
    )


def test_packet_db_history_cli_rejects_non_positive_limit_before_env_runner_or_connect(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("packet DB env should not be read")

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("paper research packet DB history runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    monkeypatch.setattr(cli, "from_paper_research_packet_db_env", forbidden_env)

    exit_code = main(
        [COMMAND, "--limit", "0"],
        paper_research_packet_db_history_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed: {COMMAND} limit must be positive" in captured.err


@pytest.mark.parametrize("bad_limit", (0, -1, True, "1"))
def test_packet_db_history_helper_rejects_invalid_limit_before_runner_or_connect(
    bad_limit: object,
) -> None:
    runner_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("paper research packet DB history runner should not run")

    helper = getattr(cli, "_run_paper_research_packet_db_history")

    with pytest.raises(ValueError, match=f"{COMMAND} limit must be positive"):
        helper(
            dsn="postgresql://packet-history.example.invalid/db",
            table_name="paper_research_packet_archive",
            limit=bad_limit,
            runner=forbidden_runner,
        )

    assert runner_calls == 0


def test_packet_db_history_cli_uses_injected_runner_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://packet-db-history.example.invalid/db"
    table_name = "paper_research_packet_archive"
    _set_packet_db_env(monkeypatch, dsn, table_name=table_name)
    calls: list[dict[str, object]] = []
    report = _history_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 25
        config = kwargs["config"]
        assert type(config) is PaperResearchPacketDbHistoryConfig
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
        paper_research_packet_db_history_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "report_count=2" in captured.out
    assert "first_report_generated_at=2026-06-23T08:00:00+00:00" in captured.out
    assert "latest_report_generated_at=2026-06-23T10:00:00+00:00" in captured.out
    assert "duplicate_generated_at_count=1" in captured.out
    assert "latest_packet_config_version=paper-research-packet-v1" in captured.out
    assert "latest_input_row_count=5" in captured.out
    assert "latest_packet_row_count=2" in captured.out
    assert "latest_included_count=2" in captured.out
    assert "latest_skipped_count=0" in captured.out
    assert "latest_high_priority_count=1" in captured.out
    assert "latest_medium_priority_count=1" in captured.out
    assert "latest_low_priority_count=0" in captured.out
    assert "top_packet: rank=1 market_slug=market-alpha" in captured.out
    assert "side=yes" in captured.out
    assert "research_priority=high" in captured.out
    assert "recommendation_score=0.910000" in captured.out
    assert "net_edge=0.080000" in captured.out
    assert "allocated_notional=12.500000" in captured.out
    assert "requested_notional=15.000000" in captured.out
    assert "reason_codes=positive_edge,settlement_review" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert table_name not in captured.out
    assert table_name not in captured.err
    assert "Will secret market resolve yes?" not in captured.out
    assert "Do not print this question" not in captured.out
    assert "required_checks" not in captured.out
    assert "payload-json-secret" not in captured.out
    assert "report-sha-secret" not in captured.out


def test_packet_db_history_cli_runner_failure_redacts_dsn_schema_table_and_tail(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://packet-db-history-secret.example.invalid/db"
    table_name = "analytics.paper_research_packet_archive"
    payload_json = '{"secret":"payload-json-secret"}'
    question = "Will secret market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    _set_packet_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(
            f"read failed dsn={dsn} table={table_name} "
            "tail=paper_research_packet_archive "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256}",
        )

    exit_code = main(
        [COMMAND],
        paper_research_packet_db_history_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "dsn=<redacted-dsn>" in captured.err
    assert "table=<redacted-table>" in captured.err
    assert "tail=<redacted-table>" in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert table_name not in captured.out
    assert table_name not in captured.err
    assert "paper_research_packet_archive" not in captured.err
    assert payload_json not in captured.err
    assert "payload-json-secret" not in captured.err
    assert question not in captured.err
    assert report_sha256 not in captured.err


def test_packet_db_history_helper_default_load_path_uses_autocommit_and_closes_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dsn = "postgresql://packet-db-history.example.invalid/db"
    table_name = "paper_research_packet_archive"
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
        config: PaperResearchPacketDbHistoryConfig,
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
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_research_packet_db_history_load."
        "load_paper_research_packet_db_history_report",
        fake_load,
    )

    helper = getattr(cli, "_run_paper_research_packet_db_history")
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
    assert type(config) is PaperResearchPacketDbHistoryConfig
    assert config.config_version == HISTORY_CONFIG_VERSION
    generated_at = loader_calls[0]["generated_at"]
    assert isinstance(generated_at, datetime)
    assert generated_at.tzinfo is UTC
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_packet_db_history_helper_connect_failure_raises_static_redacted_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dsn = (
        "postgresql://packet_user:super-secret-password@"
        "packet-db-history-secret.example.invalid/db?sslmode=require"
    )
    table_name = "secret_schema.paper_research_packet_archive"
    table_tail = "paper_research_packet_archive"
    payload_json = '{"secret":"payload-json-secret"}'
    question = "Will secret market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    connect_calls: list[tuple[str, bool]] = []
    loader_calls = 0

    def fake_connect(connect_dsn: str, *, autocommit: bool = False) -> object:
        connect_calls.append((connect_dsn, autocommit))
        raise RuntimeError(
            f"connect failed dsn={dsn} table={table_name} tail={table_tail} "
            f"schema=secret_schema payload={payload_json} question={question} "
            f"report_sha256={report_sha256}",
        )

    def forbidden_load(*args: Any, **kwargs: Any) -> object:
        nonlocal loader_calls
        loader_calls += 1
        raise AssertionError("loader should not run when connect fails")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_research_packet_db_history_load."
        "load_paper_research_packet_db_history_report",
        forbidden_load,
    )

    helper = getattr(cli, "_run_paper_research_packet_db_history")
    with pytest.raises(RuntimeError) as exc_info:
        helper(
            dsn=dsn,
            table_name=table_name,
            limit=7,
            runner=None,
        )

    message = str(exc_info.value)
    assert message == "failed to connect to the paper research packet database"
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__ is True
    assert connect_calls == [(dsn, True)]
    assert loader_calls == 0
    for leaked_fragment in (
        dsn,
        "super-secret-password",
        table_name,
        table_tail,
        "secret_schema",
        payload_json,
        "payload-json-secret",
        question,
        report_sha256,
    ):
        assert leaked_fragment not in message


def test_packet_db_history_helper_default_read_failure_redacts_and_closes_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dsn = "postgresql://packet-db-history-secret.example.invalid/db"
    table_name = "analytics.paper_research_packet_archive"

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
        assert connect_dsn == dsn
        assert autocommit is True
        return connection

    def broken_load(*args: Any, **kwargs: Any) -> object:
        raise RuntimeError(
            f"read failed dsn={dsn} table={table_name} "
            "tail=paper_research_packet_archive",
        )

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_research_packet_db_history_load."
        "load_paper_research_packet_db_history_report",
        broken_load,
    )

    helper = getattr(cli, "_run_paper_research_packet_db_history")
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
    assert "tail=<redacted-table>" in message
    assert dsn not in message
    assert table_name not in message
    assert "paper_research_packet_archive" not in message
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


@pytest.mark.parametrize(
    "flag",
    (
        "--dsn",
        "--db-dsn",
        "--paper-research-packet-db-dsn",
        "--paper-research-packet-db-table",
        "--paper-research-packet-db-enabled",
        "--source-config-version",
        "--action-status",
        "--research-status",
        "--packet-config-version",
        "--max-packet-rows",
        "--min-score",
        "--persist",
        "--config-version",
        "--table",
    ),
)
def test_packet_db_history_cli_rejects_db_source_generation_and_table_flags(
    flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, flag, "forbidden-value"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert f"unrecognized arguments: {flag}" in captured.err
