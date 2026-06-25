from __future__ import annotations

import builtins
import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_store import (
    DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_REPORTS_TABLE,
)
from polymarket_alpha_lab.supabase_paper_autonomous_investment_ledger_db_history_health_config import (
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-autonomous-investment-ledger-db-history-health-trend"
LOADER_MODULE = (
    "polymarket_alpha_lab."
    "paper_autonomous_investment_ledger_db_history_health_trend_load"
)
SECRET_DSN = "postgresql://paper-ledger-trend-secret.example.invalid/db"
SECRET_TABLE = "secret_schema.paper_ledger_secret_archive"
SECRET_PAYLOAD = '{"market_slug":"hidden-market","question":"hidden question"}'
SECRET_QUESTION = "Will hidden investment ledger trend resolve yes?"
SECRET_MARKET = "hidden-market"
SECRET_SHA256 = (
    "abcdef0123456789abcdef0123456789"
    "abcdef0123456789abcdef0123456789"
)


def _enable_ledger_db(
    monkeypatch: pytest.MonkeyPatch,
    *,
    dsn: str = "postgresql://paper-ledger-trend.example.invalid/db",
    table_name: str = "paper_autonomous_investment_ledger_db_history_health_reports",
) -> None:
    monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR, table_name)


def _trend_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 25, 18, 0, tzinfo=UTC),
        config_version="paper-autonomous-investment-ledger-db-history-health-trend-v0",
        source_health_report_count=4,
        first_generated_at=datetime(2026, 6, 25, 14, 0, tzinfo=UTC),
        latest_generated_at=datetime(2026, 6, 25, 17, 0, tzinfo=UTC),
        latest_health_status="watch",
        health_status_counts=(("pass", 2), ("watch", 2)),
        consecutive_latest_watch_count=2,
        consecutive_latest_blocked_count=0,
        duplicate_generated_at_count=1,
        ledger_report_count_first=3,
        ledger_report_count_latest=4,
        ledger_report_count_delta=1,
        pass_ledger_report_count_first=2,
        pass_ledger_report_count_latest=2,
        pass_ledger_report_count_delta=0,
        watch_ledger_report_count_first=0,
        watch_ledger_report_count_latest=1,
        watch_ledger_report_count_delta=1,
        blocked_ledger_report_count_first=1,
        blocked_ledger_report_count_latest=1,
        blocked_ledger_report_count_delta=0,
        latest_source_record_count_first=6,
        latest_source_record_count_latest=9,
        latest_source_record_count_delta=3,
        latest_submitted_count_first=3,
        latest_submitted_count_latest=5,
        latest_submitted_count_delta=2,
        latest_held_count_first=2,
        latest_held_count_latest=3,
        latest_held_count_delta=1,
        latest_blocked_count_first=1,
        latest_blocked_count_latest=1,
        latest_blocked_count_delta=0,
        latest_total_submitted_notional_first=Decimal("10.000000"),
        latest_total_submitted_notional_latest=Decimal("22.500000"),
        latest_total_submitted_notional_delta=Decimal("12.500000"),
        latest_source_generated_at_first=datetime(2026, 6, 25, 14, 30, tzinfo=UTC),
        latest_source_generated_at_latest=datetime(2026, 6, 25, 14, 40, tzinfo=UTC),
        latest_source_generated_at_delta_seconds=600,
        latest_source_age_seconds_first=3900,
        latest_source_age_seconds_latest=3600,
        latest_source_age_seconds_delta=-300,
        max_source_age_seconds_first=2700,
        max_source_age_seconds_latest=3600,
        max_source_age_seconds_delta=900,
        duplicate_latest_generated_at_count_first=0,
        duplicate_latest_generated_at_count_latest=1,
        duplicate_latest_generated_at_count_delta=1,
        latest_reason_code_counts=(
            ("latest_paper_autonomous_investment_ledger_watch", 1),
            ("stale_paper_autonomous_investment_ledger_source_history", 1),
        ),
        total_reason_code_counts=(
            ("latest_paper_autonomous_investment_ledger_watch", 2),
            ("stale_paper_autonomous_investment_ledger_source_history", 1),
        ),
        repeated_reason_code_counts=(
            ("latest_paper_autonomous_investment_ledger_watch", 2),
        ),
        reason_code_rows=(),
        source_summaries=(),
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
        "secret_schema",
        "paper_ledger_secret_archive",
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
            f"{COMMAND} requires paper autonomous investment ledger DB-history health DB to be enabled",
        ),
        (
            "false",
            None,
            f"{COMMAND} requires paper autonomous investment ledger DB-history health DB to be enabled",
        ),
        (
            "true",
            None,
            PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR,
        ),
    ),
)
def test_investment_ledger_db_history_health_trend_cli_requires_enabled_db_and_dsn_before_runner(
    enabled: str | None,
    dsn: str | None,
    expected_message: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    if enabled is None:
        monkeypatch.delenv(
            PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR,
            raising=False,
        )
    else:
        monkeypatch.setenv(
            PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR,
            enabled,
        )
    if dsn is None:
        monkeypatch.delenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR, dsn)
    runner_calls = 0

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("history health trend runner should not run")

    exit_code = main(
        [COMMAND],
        paper_autonomous_investment_ledger_db_history_health_trend_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert runner_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert expected_message in captured.err


@pytest.mark.parametrize("limit", ("0", "-1"))
def test_investment_ledger_db_history_health_trend_cli_rejects_non_positive_limit_before_env_runner_or_psycopg(
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
        raise AssertionError("history health trend runner should not run")

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

    monkeypatch.setattr(cli, "from_paper_autonomous_investment_ledger_db_history_health_db_env", forbidden_env)
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", limit],
        paper_autonomous_investment_ledger_db_history_health_trend_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert psycopg_import_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed: {COMMAND} limit must be positive" in captured.err


@pytest.mark.parametrize("bad_limit", (0, -1, True, "1", 1.0))
def test_run_investment_ledger_db_history_health_trend_rejects_invalid_limit_before_runner_or_psycopg(
    bad_limit: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = getattr(cli, "_run_paper_autonomous_investment_ledger_db_history_health_trend")
    runner_calls = 0
    connect_calls = 0
    psycopg_import_calls = 0
    real_import = builtins.__import__

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("history health trend runner should not run")

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
            dsn="postgresql://paper-ledger-trend.example.invalid/db",
            table_name="paper_autonomous_investment_ledger_db_history_health_reports",
            limit=bad_limit,
            runner=forbidden_runner,
        )

    assert runner_calls == 0
    assert connect_calls == 0
    assert psycopg_import_calls == 0


def test_investment_ledger_db_history_health_trend_cli_uses_injected_runner_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://paper-ledger-trend.example.invalid/db"
    table_name = "paper_autonomous_investment_ledger_db_history_health_reports"
    _enable_ledger_db(monkeypatch, dsn=dsn, table_name=table_name)
    calls: list[dict[str, object]] = []
    report = _trend_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 25
        assert (
            type(kwargs["health_config"])
            is PaperAutonomousInvestmentLedgerDbHistoryHealthConfig
        )
        assert (
            type(kwargs["trend_config"])
            is PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig
        )
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND, "--limit", "25"],
        paper_autonomous_investment_ledger_db_history_health_trend_runner=fake_runner,
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: trend_count=4 latest_health_status=watch "
            "ledger_report_count_delta=1 pass_ledger_report_count_delta=0 "
            "watch_ledger_report_count_delta=1 blocked_ledger_report_count_delta=0 "
            "latest_source_record_count_delta=3 latest_submitted_count_delta=2 "
            "latest_held_count_delta=1 latest_blocked_count_delta=0 "
            "latest_total_submitted_notional_delta=12.500000 "
            "latest_source_generated_at_delta_seconds=600 "
            "latest_source_age_seconds_delta=-300 "
            "max_source_age_seconds_delta=900 "
            "duplicate_latest_generated_at_count_delta=1 "
            "duplicate_generated_at_count=1 "
            "consecutive_latest_watch_count=2 consecutive_latest_blocked_count=0 "
            "latest_reason_code_counts="
            "latest_paper_autonomous_investment_ledger_watch=1,"
            "stale_paper_autonomous_investment_ledger_source_history=1"
        ),
    ]
    assert captured.err == ""


def test_investment_ledger_db_history_health_trend_cli_uses_default_health_table_when_table_env_absent(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://paper-ledger-trend.example.invalid/db"
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_DSN_ENV_VAR,
        dsn,
    )
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_DB_TABLE_ENV_VAR,
        raising=False,
    )
    calls: list[dict[str, object]] = []

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        return _trend_report()

    exit_code = main(
        [COMMAND],
        paper_autonomous_investment_ledger_db_history_health_trend_runner=fake_runner,
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["dsn"] == dsn
    assert calls[0]["table_name"] == (
        DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_REPORTS_TABLE
    )
    assert capsys.readouterr().err == ""


def test_run_investment_ledger_db_history_health_trend_default_loader_owns_connection_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = getattr(cli, "_run_paper_autonomous_investment_ledger_db_history_health_trend")
    dsn = "postgresql://paper-ledger-trend.example.invalid/db"
    table_name = "paper_autonomous_investment_ledger_db_history_health_reports"
    expected_report = object()
    connect_calls: list[dict[str, object]] = []
    loader_calls: list[dict[str, object]] = []

    class FakeConnection:
        close_calls = 0

        def close(self) -> None:
            self.close_calls += 1

        def commit(self) -> None:
            raise AssertionError("read-only history health trend helper must not commit")

        def rollback(self) -> None:
            raise AssertionError("read-only history health trend helper must not rollback")

    connection = FakeConnection()

    def fake_connect(received_dsn: str, *, autocommit: bool) -> FakeConnection:
        connect_calls.append({"dsn": received_dsn, "autocommit": autocommit})
        return connection

    def fake_loader(
        received_connection: object,
        *,
        limit: int,
        table_name: str,
        health_config: PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
        trend_config: PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
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
        return expected_report

    loader_module = ModuleType(LOADER_MODULE)
    loader_module.load_paper_autonomous_investment_ledger_db_history_health_trend_report = (
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
    assert (
        type(loader_calls[0]["health_config"])
        is PaperAutonomousInvestmentLedgerDbHistoryHealthConfig
    )
    assert (
        type(loader_calls[0]["trend_config"])
        is PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig
    )
    generated_at = loader_calls[0]["generated_at"]
    assert isinstance(generated_at, datetime)
    assert generated_at.tzinfo is UTC
    assert connection.close_calls == 1


def test_run_investment_ledger_db_history_health_trend_connect_failure_names_health_report_db(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = getattr(cli, "_run_paper_autonomous_investment_ledger_db_history_health_trend")
    connect_calls: list[dict[str, object]] = []

    def broken_connect(received_dsn: str, *, autocommit: bool) -> object:
        connect_calls.append({"dsn": received_dsn, "autocommit": autocommit})
        raise RuntimeError(f"connection failed for {SECRET_DSN} {SECRET_TABLE}")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=broken_connect))

    with pytest.raises(RuntimeError) as exc_info:
        helper(dsn=SECRET_DSN, table_name=SECRET_TABLE, limit=3, runner=None)

    message = str(exc_info.value)
    assert message == (
        "failed to connect to the paper autonomous investment ledger "
        "DB-history health report database"
    )
    assert "paper autonomous investment ledger database" not in message
    assert SECRET_DSN not in message
    assert SECRET_TABLE not in message
    assert connect_calls == [{"dsn": SECRET_DSN, "autocommit": True}]


def test_investment_ledger_db_history_health_trend_cli_runner_failure_redacts_sensitive_values(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _enable_ledger_db(monkeypatch, dsn=SECRET_DSN, table_name=SECRET_TABLE)

    def broken_runner(**_kwargs: Any) -> object:
        raise RuntimeError(_secret_failure_message())

    exit_code = main(
        [COMMAND],
        paper_autonomous_investment_ledger_db_history_health_trend_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    _assert_redacted_failure_message(captured.err)
    assert captured.out == ""


def test_run_investment_ledger_db_history_health_trend_loader_failure_redacts_sensitive_values_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = getattr(cli, "_run_paper_autonomous_investment_ledger_db_history_health_trend")

    class FakeConnection:
        close_calls = 0

        def close(self) -> None:
            self.close_calls += 1

        def commit(self) -> None:
            raise AssertionError("read-only history health trend helper must not commit")

        def rollback(self) -> None:
            raise AssertionError("read-only history health trend helper must not rollback")

    connection = FakeConnection()

    def fake_loader(*_args: Any, **_kwargs: Any) -> object:
        raise RuntimeError(_secret_failure_message())

    loader_module = ModuleType(LOADER_MODULE)
    loader_module.load_paper_autonomous_investment_ledger_db_history_health_trend_report = (
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


def test_investment_ledger_db_history_health_trend_summary_printer_emits_aggregates_only(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = _trend_report()
    report.market_slug = "secret-market-slug"
    report.question = "Will hidden investment ledger market resolve yes?"
    report.account = "secret-account-id"
    report.wallet = "secret-wallet-address"
    report.order_id = "secret-order-id"
    report.trade_id = "secret-trade-id"
    report.payload_json = {"wallet": "secret-wallet-address"}
    report.raw_payload = {"order_id": "secret-order-id"}
    report.report_sha256 = SECRET_SHA256
    report.api_key = "secret-api-key"
    report.private_key = "secret-private-key"

    printer = getattr(
        cli,
        "_print_paper_autonomous_investment_ledger_db_history_health_trend_summary",
    )
    printer(report)

    captured = capsys.readouterr()
    assert f"{COMMAND}: trend_count=4 latest_health_status=watch" in captured.out
    assert "ledger_report_count_delta=1" in captured.out
    assert "latest_reason_code_counts=latest_paper_autonomous_investment_ledger_watch=1" in captured.out
    assert captured.err == ""
    for forbidden in (
        "config_version",
        "first_generated_at",
        "latest_generated_at=",
        "source_summaries",
        "reason_code_rows",
        "total_reason_code_counts",
        "repeated_reason_code_counts",
        "market_slug",
        "secret-market-slug",
        "question",
        "Will hidden investment ledger market resolve yes?",
        "account",
        "secret-account-id",
        "wallet",
        "secret-wallet-address",
        "order_id",
        "secret-order-id",
        "trade_id",
        "secret-trade-id",
        "payload_json",
        "raw_payload",
        "report_sha256",
        SECRET_SHA256,
        "api_key",
        "secret-api-key",
        "private_key",
        "secret-private-key",
    ):
        assert forbidden not in captured.out
        assert forbidden not in captured.err
