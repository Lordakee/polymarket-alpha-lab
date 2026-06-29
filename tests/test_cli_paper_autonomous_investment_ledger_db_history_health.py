from __future__ import annotations

import builtins
import sys
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health import (
    DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_CONFIG_VERSION,
    PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
)
from polymarket_alpha_lab.supabase_paper_autonomous_investment_ledger_config import (
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-autonomous-investment-ledger-db-history-health"
LOADER_MODULE = (
    "polymarket_alpha_lab."
    "paper_autonomous_investment_ledger_db_history_health_load"
)
SECRET_DSN = "postgresql://paper-ledger:secret@localhost:54322/db"
SECRET_TABLE = "paper_ledger_secret_archive"
SECRET_PAYLOAD = '{"market_slug":"hidden-market","question":"hidden question"}'
SECRET_QUESTION = "Will hidden investment ledger market resolve yes?"
SECRET_MARKET = "hidden-market"
SECRET_SHA256 = (
    "abcdef0123456789abcdef0123456789"
    "abcdef0123456789abcdef0123456789"
)


def _enable_ledger_db(
    monkeypatch: pytest.MonkeyPatch,
    *,
    dsn: str = "postgresql://paper-ledger:secret@localhost:54322/db",
    table_name: str = "paper_autonomous_investment_ledger_reports",
) -> None:
    monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_TABLE_ENV_VAR, table_name)


def _health_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 25, 18, 0, tzinfo=UTC),
        config_version=(
            DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_CONFIG_VERSION
        ),
        health_status="watch",
        recommended_next_step="throttle_paper_autonomous_investment_ledger_review",
        ledger_report_count=4,
        pass_ledger_report_count=2,
        watch_ledger_report_count=1,
        blocked_ledger_report_count=1,
        latest_ledger_status="watch",
        latest_source_record_count=9,
        latest_submitted_count=5,
        latest_held_count=3,
        latest_blocked_count=1,
        latest_total_submitted_notional="42.000000",
        latest_source_generated_at=datetime(2026, 6, 25, 17, 0, tzinfo=UTC),
        latest_source_age_seconds=3600,
        max_source_age_seconds=18_000,
        duplicate_latest_generated_at_count=1,
        reason_code_counts=(
            SimpleNamespace(
                reason_code="latest_paper_autonomous_investment_ledger_watch",
                report_count=1,
            ),
            SimpleNamespace(
                reason_code="stale_paper_autonomous_investment_ledger_source_history",
                report_count=2,
            ),
        ),
        reason_codes=(
            "latest_paper_autonomous_investment_ledger_watch",
            "stale_paper_autonomous_investment_ledger_source_history",
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _secret_failure_message() -> str:
    return (
        f"read failed dsn={SECRET_DSN} table={SECRET_TABLE} "
        f"payload_json={SECRET_PAYLOAD} question={SECRET_QUESTION} "
        f"market_slug={SECRET_MARKET} report_sha256={SECRET_SHA256}"
    )


def _assert_redacted_failure_message(message: str) -> None:
    assert "dsn=<redacted-dsn>" in message
    assert "table=<redacted-table>" in message
    assert "payload_json=<redacted-payload>" in message
    assert "question=<redacted-question>" in message
    assert "market_slug=<redacted-market-slug>" in message
    assert "report_sha256=<redacted-sha256>" in message
    for secret in (
        SECRET_DSN,
        SECRET_TABLE,
        SECRET_PAYLOAD,
        SECRET_QUESTION,
        SECRET_MARKET,
        SECRET_SHA256,
    ):
        assert secret not in message


@pytest.mark.parametrize(
    ("enabled", "dsn", "expected_message"),
    (
        (
            None,
            None,
            f"{COMMAND} requires paper autonomous investment ledger DB to be enabled",
        ),
        (
            "false",
            None,
            f"{COMMAND} requires paper autonomous investment ledger DB to be enabled",
        ),
        (
            "true",
            None,
            PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_DSN_ENV_VAR,
        ),
    ),
)
def test_investment_ledger_db_history_health_cli_requires_enabled_db_and_dsn_before_runner(
    enabled: str | None,
    dsn: str | None,
    expected_message: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    if enabled is None:
        monkeypatch.delenv(
            PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_ENABLED_ENV_VAR,
            raising=False,
        )
    else:
        monkeypatch.setenv(
            PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_ENABLED_ENV_VAR,
            enabled,
        )
    if dsn is None:
        monkeypatch.delenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_DSN_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_DSN_ENV_VAR, dsn)
    runner_calls = 0

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("history health runner should not run")

    exit_code = main(
        [COMMAND],
        paper_autonomous_investment_ledger_db_history_health_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert runner_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert expected_message in captured.err


@pytest.mark.parametrize("limit", ("0", "-1"))
def test_investment_ledger_db_history_health_cli_rejects_non_positive_limit_before_env_runner_or_psycopg(
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
        raise AssertionError("ledger DB env should not be read")

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("history health runner should not run")

    def forbidden_connect(*_args: Any, **_kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    def guarded_import(
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

    monkeypatch.setattr(cli, "from_paper_autonomous_investment_ledger_db_env", forbidden_env)
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", limit],
        paper_autonomous_investment_ledger_db_history_health_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert psycopg_import_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed: {COMMAND} limit must be positive" in captured.err


@pytest.mark.parametrize("bad_limit", (0, -1, True, "1", 1.0))
def test_run_investment_ledger_db_history_health_rejects_invalid_limit_before_runner_or_psycopg(
    bad_limit: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = getattr(cli, "_run_paper_autonomous_investment_ledger_db_history_health")
    runner_calls = 0
    connect_calls = 0
    psycopg_import_calls = 0
    real_import = builtins.__import__

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("history health runner should not run")

    def forbidden_connect(*_args: Any, **_kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    def guarded_import(
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

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    with pytest.raises(ValueError, match=f"{COMMAND} limit must be positive"):
        helper(
            dsn="postgresql://paper-ledger:secret@localhost:54322/db",
            table_name="paper_autonomous_investment_ledger_reports",
            limit=bad_limit,
            runner=forbidden_runner,
        )

    assert runner_calls == 0
    assert connect_calls == 0
    assert psycopg_import_calls == 0


def test_investment_ledger_db_history_health_cli_uses_injected_runner_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://paper-ledger:secret@localhost:54322/db"
    table_name = "paper_autonomous_investment_ledger_reports"
    _enable_ledger_db(monkeypatch, dsn=dsn, table_name=table_name)
    calls: list[dict[str, object]] = []
    report = _health_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 25
        config = kwargs["config"]
        assert type(config) is PaperAutonomousInvestmentLedgerDbHistoryHealthConfig
        assert config.config_version == (
            DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_CONFIG_VERSION
        )
        assert config.paper_only is True
        assert config.report_only is True
        assert config.readonly is True
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND, "--limit", "25"],
        paper_autonomous_investment_ledger_db_history_health_runner=fake_runner,
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: health_status=watch "
            "recommended_next_step=throttle_paper_autonomous_investment_ledger_review "
            "ledger_report_count=4 latest_ledger_status=watch "
            "latest_source_record_count=9 latest_submitted_count=5 "
            "latest_held_count=3 latest_blocked_count=1 "
            "latest_total_submitted_notional=42.000000 "
            "latest_source_generated_at=2026-06-25T17:00:00+00:00 "
            "latest_source_age_seconds=3600 max_source_age_seconds=18000 "
            "pass_ledger_report_count=2 watch_ledger_report_count=1 "
            "blocked_ledger_report_count=1 duplicate_latest_generated_at_count=1"
        ),
        (
            "reason_code_counts: "
            "latest_paper_autonomous_investment_ledger_watch=1 "
            "stale_paper_autonomous_investment_ledger_source_history=2"
        ),
    ]
    assert captured.err == ""


def test_run_investment_ledger_db_history_health_default_loader_owns_connection_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = getattr(cli, "_run_paper_autonomous_investment_ledger_db_history_health")
    dsn = "postgresql://paper-ledger:secret@localhost:54322/db"
    table_name = "paper_autonomous_investment_ledger_reports"
    expected_report = object()
    connect_calls: list[dict[str, object]] = []
    loader_calls: list[dict[str, object]] = []

    class FakeConnection:
        close_calls = 0

        def close(self) -> None:
            self.close_calls += 1

        def commit(self) -> None:
            raise AssertionError("read-only history health helper must not commit")

        def rollback(self) -> None:
            raise AssertionError("read-only history health helper must not rollback")

    connection = FakeConnection()

    def fake_connect(received_dsn: str, *, autocommit: bool) -> FakeConnection:
        connect_calls.append({"dsn": received_dsn, "autocommit": autocommit})
        return connection

    def fake_loader(
        received_connection: object,
        *,
        limit: int,
        table_name: str,
        config: PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
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
        return expected_report

    loader_module = ModuleType(LOADER_MODULE)
    loader_module.load_paper_autonomous_investment_ledger_db_history_health_report = (
        fake_loader
    )
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setitem(sys.modules, LOADER_MODULE, loader_module)

    actual = helper(dsn=dsn, table_name=table_name, limit=7, runner=None)

    assert actual is expected_report
    assert connect_calls == [{"dsn": dsn, "autocommit": True}]
    assert len(loader_calls) == 1
    assert loader_calls[0]["connection"] is connection
    assert loader_calls[0]["limit"] == 7
    assert loader_calls[0]["table_name"] == table_name
    assert type(loader_calls[0]["config"]) is PaperAutonomousInvestmentLedgerDbHistoryHealthConfig
    generated_at = loader_calls[0]["generated_at"]
    assert isinstance(generated_at, datetime)
    assert generated_at.tzinfo is UTC
    assert connection.close_calls == 1


def test_run_investment_ledger_db_history_health_missing_psycopg_error_is_clean_and_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = getattr(cli, "_run_paper_autonomous_investment_ledger_db_history_health")
    real_import = builtins.__import__

    def missing_psycopg_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "psycopg":
            raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.delitem(sys.modules, "psycopg", raising=False)
    monkeypatch.setattr(builtins, "__import__", missing_psycopg_import)

    with pytest.raises(RuntimeError) as exc_info:
        helper(dsn=SECRET_DSN, table_name=SECRET_TABLE, limit=1, runner=None)

    message = str(exc_info.value)
    assert "psycopg is required" in message
    assert "postgres extra" in message
    assert SECRET_DSN not in message
    assert SECRET_TABLE not in message
    assert "Traceback" not in message


def test_investment_ledger_db_history_health_cli_runner_failure_redacts_sensitive_values(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_ledger_db(monkeypatch, dsn=SECRET_DSN, table_name=SECRET_TABLE)

    def broken_runner(**_kwargs: Any) -> object:
        raise RuntimeError(_secret_failure_message())

    exit_code = main(
        [COMMAND],
        paper_autonomous_investment_ledger_db_history_health_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    _assert_redacted_failure_message(captured.err)
    assert captured.out == ""


def test_run_investment_ledger_db_history_health_loader_failure_redacts_sensitive_values_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = getattr(cli, "_run_paper_autonomous_investment_ledger_db_history_health")

    class FakeConnection:
        close_calls = 0

        def close(self) -> None:
            self.close_calls += 1

        def commit(self) -> None:
            raise AssertionError("read-only history health helper must not commit")

        def rollback(self) -> None:
            raise AssertionError("read-only history health helper must not rollback")

    connection = FakeConnection()

    def fake_loader(*_args: Any, **_kwargs: Any) -> object:
        raise RuntimeError(_secret_failure_message())

    loader_module = ModuleType(LOADER_MODULE)
    loader_module.load_paper_autonomous_investment_ledger_db_history_health_report = (
        fake_loader
    )
    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(
            connect=lambda _dsn, *, autocommit: connection,
        ),
    )
    monkeypatch.setitem(sys.modules, LOADER_MODULE, loader_module)

    with pytest.raises(RuntimeError) as exc_info:
        helper(dsn=SECRET_DSN, table_name=SECRET_TABLE, limit=3, runner=None)

    _assert_redacted_failure_message(str(exc_info.value))
    assert connection.close_calls == 1


def test_investment_ledger_db_history_health_summary_printer_emits_aggregates_and_reason_counts_only(
    capsys: pytest.CaptureFixture[str],
) -> None:
    printer = getattr(
        cli,
        "_print_paper_autonomous_investment_ledger_db_history_health_summary",
    )

    printer(_health_report())

    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: health_status=watch "
            "recommended_next_step=throttle_paper_autonomous_investment_ledger_review "
            "ledger_report_count=4 latest_ledger_status=watch "
            "latest_source_record_count=9 latest_submitted_count=5 "
            "latest_held_count=3 latest_blocked_count=1 "
            "latest_total_submitted_notional=42.000000 "
            "latest_source_generated_at=2026-06-25T17:00:00+00:00 "
            "latest_source_age_seconds=3600 max_source_age_seconds=18000 "
            "pass_ledger_report_count=2 watch_ledger_report_count=1 "
            "blocked_ledger_report_count=1 duplicate_latest_generated_at_count=1"
        ),
        (
            "reason_code_counts: "
            "latest_paper_autonomous_investment_ledger_watch=1 "
            "stale_paper_autonomous_investment_ledger_source_history=2"
        ),
    ]
    assert captured.err == ""
    for omitted_field in (
        "config_version",
        "reason_codes",
    ):
        assert omitted_field not in captured.out
    assert f"{COMMAND}: generated_at=" not in captured.out
