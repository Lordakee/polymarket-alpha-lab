from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.paper_probability_selection_summary_history_trend import (
    PaperProbabilitySelectionSummaryHistoryTrendConfig,
)
from polymarket_alpha_lab.supabase_paper_probability_selection_summary_history_config import (
    PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR,
    PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR,
    PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-probability-selection-summary-history-trend"
TREND_CONFIG_VERSION = "paper-probability-selection-summary-history-trend-v0"


def _trend_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 28, 12, 0, tzinfo=UTC),
        config_version=TREND_CONFIG_VERSION,
        source_history_count=4,
        first_generated_at=datetime(2026, 6, 28, 8, 0, tzinfo=UTC),
        latest_generated_at=datetime(2026, 6, 28, 11, 30, tzinfo=UTC),
        history_span_seconds=12_600,
        latest_history_status="watch",
        latest_status_streak=2,
        latest_selected_share=Decimal("0.400000"),
        average_selected_share=Decimal("0.450000"),
        selected_share_delta=Decimal("-0.050000"),
        stale_history_count=1,
        thin_history_count=1,
        trend_status="watch",
        recommended_next_step="review_probability_selection_trend",
        reason_codes=(
            "latest_history_watch",
            "selected_share_deteriorated",
            "stale_history_reports_present",
        ),
        recurring_reason_code_counts=(
            ("latest_selection_has_watch_rows", 2),
            ("source_next_step_skip", 2),
        ),
        rows=(SimpleNamespace(market_slug="secret-market", question="secret question"),),
        source_reports=(SimpleNamespace(question="do not print source detail"),),
        payload_json='{"secret":"payload-json-secret"}',
        report_sha256="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _set_history_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = "paper_probability_selection_summary_history_reports",
) -> None:
    monkeypatch.setenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE_ENV_VAR,
        table_name,
    )


def _clear_history_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE_ENV_VAR,
        raising=False,
    )


def test_parser_help_includes_paper_probability_selection_summary_history_trend(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert COMMAND in capsys.readouterr().out


@pytest.mark.parametrize(
    "flag",
    (
        "--persist",
        "--dsn",
        "--db-dsn",
        "--table",
        "--db-table",
        "--input",
        "--output",
        "--live",
        "--wallet",
        "--order",
        "--execute",
        "--auth",
        "--private-key",
        "--account",
    ),
)
def test_history_trend_cli_rejects_persist_db_file_live_wallet_order_and_auth_flags(
    flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, flag, "forbidden-value"])

    assert exc_info.value.code == 2
    assert f"unrecognized arguments: {flag}" in capsys.readouterr().err


def test_history_trend_disabled_history_db_config_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _clear_history_db_env(monkeypatch)
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("trend runner should not run without history DB config")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND],
        paper_probability_selection_summary_history_trend_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires paper probability selection summary history DB" in captured.err


def test_history_trend_enabled_history_db_without_dsn_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.delenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR,
        raising=False,
    )
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("trend runner should not run without a history DB DSN")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND],
        paper_probability_selection_summary_history_trend_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert (
        f"{PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR} "
        "must be set when DB is enabled"
    ) in captured.err


@pytest.mark.parametrize("raw_limit", ("0", "-1"))
def test_history_trend_cli_rejects_non_positive_limit_before_env_runner_or_connect(
    raw_limit: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    connect_calls = 0

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("history DB env should not be read")

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("trend runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setattr(
        cli,
        "from_paper_probability_selection_summary_history_db_env",
        forbidden_env,
        raising=False,
    )
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", raw_limit],
        paper_probability_selection_summary_history_trend_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert f"{COMMAND} limit must be positive" in capsys.readouterr().err


def test_history_trend_cli_uses_history_env_config_and_prints_aggregate_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://selection-history:secret@localhost:54322/db"
    table_name = "paper_probability_selection_summary_history_reports"
    _set_history_db_env(monkeypatch, dsn, table_name=table_name)
    calls: list[dict[str, object]] = []
    report = _trend_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 25
        config = kwargs["config"]
        assert type(config) is PaperProbabilitySelectionSummaryHistoryTrendConfig
        assert config.config_version == TREND_CONFIG_VERSION
        assert config.paper_only is True
        assert config.report_only is True
        assert config.readonly is True
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return report

    exit_code = main(
        [COMMAND, "--limit", "25"],
        paper_probability_selection_summary_history_trend_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "source_history_count=4" in captured.out
    assert "first_generated_at=2026-06-28T08:00:00+00:00" in captured.out
    assert "latest_generated_at=2026-06-28T11:30:00+00:00" in captured.out
    assert "history_span_seconds=12600" in captured.out
    assert "latest_history_status=watch" in captured.out
    assert "latest_status_streak=2" in captured.out
    assert "latest_selected_share=0.400000" in captured.out
    assert "average_selected_share=0.450000" in captured.out
    assert "selected_share_delta=-0.050000" in captured.out
    assert "stale_history_count=1" in captured.out
    assert "thin_history_count=1" in captured.out
    assert "trend_status=watch" in captured.out
    assert "recommended_next_step=review_probability_selection_trend" in captured.out
    assert (
        "reason_codes="
        "latest_history_watch,selected_share_deteriorated,stale_history_reports_present"
    ) in captured.out
    assert (
        "recurring_reason_code_counts: "
        "latest_selection_has_watch_rows:2,source_next_step_skip:2"
    ) in captured.out
    for leaked_fragment in (
        dsn,
        table_name,
        "secret-market",
        "secret question",
        "do not print source detail",
        "payload-json-secret",
        "abcdef0123456789",
    ):
        assert leaked_fragment not in captured.out
        assert leaked_fragment not in captured.err


def test_history_trend_cli_read_errors_redact_dsn_table_payload_and_hash(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = (
        "postgresql://history_user:super-secret-password@"
        "localhost:54322/db?sslmode=require"
    )
    table_name = "paper_probability_selection_summary_history_reports_secret"
    _set_history_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(
            f"read failed dsn={dsn} table={table_name} "
            "question=secret-question market_slug=secret-market "
            "payload_json={\"secret\":\"payload-json-secret\"} "
            "report_sha256="
            "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        )

    exit_code = main(
        [COMMAND],
        paper_probability_selection_summary_history_trend_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "dsn=<redacted-dsn>" in captured.err
    assert "table=<redacted-table>" in captured.err
    for leaked_fragment in (
        dsn,
        "super-secret-password",
        table_name,
        "reports_secret",
        "secret-question",
        "secret-market",
        "payload-json-secret",
        "abcdef0123456789",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_history_trend_cli_read_errors_redact_market_detail_and_secret_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://selection-history:secret@localhost:54322/db"
    table_name = "paper_probability_selection_summary_history_reports"
    _set_history_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(
            "read failed "
            "market_question=will-secret-event-resolve "
            '"market_details": "classified-market-detail" '
            "details=internal-detail "
            "description=private-description "
            "title=private-title "
            "secret=raw-secret "
            "password=raw-password "
            "token=raw-token "
            "api_key=raw-api-key "
            "private_key=raw-private-key "
            "authorization=raw-authorization "
            "credential=raw-credential",
        )

    exit_code = main(
        [COMMAND],
        paper_probability_selection_summary_history_trend_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "market_question=<redacted-market-detail>" in captured.err
    assert '"market_details": "<redacted-market-detail>"' in captured.err
    assert "secret=<redacted-secret>" in captured.err
    assert "password=<redacted-secret>" in captured.err
    assert "token=<redacted-secret>" in captured.err
    assert "api_key=<redacted-secret>" in captured.err
    assert "private_key=<redacted-secret>" in captured.err
    assert "authorization=<redacted-secret>" in captured.err
    assert "credential=<redacted-secret>" in captured.err
    for leaked_fragment in (
        "will-secret-event-resolve",
        "classified-market-detail",
        "internal-detail",
        "private-description",
        "private-title",
        "raw-secret",
        "raw-password",
        "raw-token",
        "raw-api-key",
        "raw-private-key",
        "raw-authorization",
        "raw-credential",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_history_trend_cli_read_errors_redact_case_variant_secret_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://selection-history:secret@localhost:54322/db"
    table_name = "paper_probability_selection_summary_history_reports"
    _set_history_db_env(monkeypatch, dsn, table_name=table_name)

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(
            "read failed "
            "Authorization: Bearer raw-authorization-token "
            "Password=Raw-Password "
            '"API_KEY": "Raw-Api-Key" '
            "access_token=raw-access-token "
            "refresh_token=raw-refresh-token "
            "auth_token=raw-auth-token "
            "client_secret=raw-client-secret "
            "secret_key=raw-secret-key "
            '"bearer_token": "raw-bearer-token" '
            "jwt_token=raw-jwt-token",
        )

    exit_code = main(
        [COMMAND],
        paper_probability_selection_summary_history_trend_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "<redacted-secret>" in captured.err
    for leaked_fragment in (
        "raw-authorization-token",
        "Raw-Password",
        "Raw-Api-Key",
        "raw-access-token",
        "raw-refresh-token",
        "raw-auth-token",
        "raw-client-secret",
        "raw-secret-key",
        "raw-bearer-token",
        "raw-jwt-token",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_history_trend_cli_sanitizes_reason_code_output_from_runner(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://selection-history:secret@localhost:54322/db"
    table_name = "paper_probability_selection_summary_history_reports"
    _set_history_db_env(monkeypatch, dsn, table_name=table_name)
    report = _trend_report()
    report.reason_codes = (
        "latest_history_watch",
        "market_question_secret_event",
        "credential_token_leak",
    )
    report.recurring_reason_code_counts = (
        ("source_next_step_skip", 2),
        ("wallet_address_leak", 3),
        ("market_slug_secret_event", 4),
    )

    exit_code = main(
        [COMMAND],
        paper_probability_selection_summary_history_trend_runner=lambda **kwargs: report,
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert (
        "reason_codes=latest_history_watch,"
        "<redacted-reason-code>,<redacted-reason-code>"
    ) in captured.out
    assert "source_next_step_skip:2" in captured.out
    assert "<redacted-reason-code>:3" in captured.out
    assert "<redacted-reason-code>:4" in captured.out
    for leaked_fragment in (
        "market_question_secret_event",
        "credential_token_leak",
        "wallet_address_leak",
        "market_slug_secret_event",
    ):
        assert leaked_fragment not in captured.out
        assert leaked_fragment not in captured.err


def test_history_trend_helper_default_load_path_reads_history_chronologically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dsn = "postgresql://selection-history:secret@localhost:54322/db"
    table_name = "paper_probability_selection_summary_history_reports"
    report = _trend_report()
    newest = SimpleNamespace(generated_at=datetime(2026, 6, 28, 11, 0, tzinfo=UTC))
    oldest = SimpleNamespace(generated_at=datetime(2026, 6, 28, 10, 0, tzinfo=UTC))
    load_calls: list[dict[str, object]] = []
    build_calls: list[dict[str, object]] = []
    connect_calls: list[tuple[str, bool]] = []

    class FakeConnection:
        def __init__(self) -> None:
            self.close_count = 0

        def commit(self) -> None:
            raise AssertionError("read-only helper should not commit")

        def rollback(self) -> None:
            raise AssertionError("read-only helper should not rollback")

        def close(self) -> None:
            self.close_count += 1

    connection = FakeConnection()

    def fake_connect(connect_dsn: str, *, autocommit: bool = False) -> FakeConnection:
        connect_calls.append((connect_dsn, autocommit))
        return connection

    def fake_load(
        load_connection: object,
        *,
        limit: int,
        table_name: str,
    ) -> tuple[object, ...]:
        load_calls.append(
            {
                "connection": load_connection,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return (newest, oldest)

    def fake_builder(
        reports: tuple[object, ...],
        *,
        config: PaperProbabilitySelectionSummaryHistoryTrendConfig,
        generated_at: datetime,
    ) -> object:
        build_calls.append(
            {
                "reports": reports,
                "config": config,
                "generated_at": generated_at,
            },
        )
        assert reports == (oldest, newest)
        assert type(config) is PaperProbabilitySelectionSummaryHistoryTrendConfig
        assert config.config_version == TREND_CONFIG_VERSION
        assert generated_at.tzinfo is UTC
        return report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_probability_selection_summary_history_store."
        "load_paper_probability_selection_summary_history_reports",
        fake_load,
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_probability_selection_summary_history_trend."
        "build_paper_probability_selection_summary_history_trend_report",
        fake_builder,
    )

    helper = getattr(cli, "_run_paper_probability_selection_summary_history_trend")
    result = helper(
        dsn=dsn,
        table_name=table_name,
        limit=7,
        runner=None,
    )

    assert result is report
    assert connect_calls == [(dsn, True)]
    assert load_calls == [
        {"connection": connection, "limit": 7, "table_name": table_name},
    ]
    assert len(build_calls) == 1
    assert connection.close_count == 1
