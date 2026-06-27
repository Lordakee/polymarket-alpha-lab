from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.paper_probability_selection_summary_history import (
    PaperProbabilitySelectionSummaryHistoryConfig,
)
from polymarket_alpha_lab.supabase_paper_probability_selection_summary_history_config import (
    PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_DSN_ENV_VAR,
    PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_ENABLED_ENV_VAR,
    PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_probability_selection_summary_config import (
    DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_DB_TABLE,
    PAPER_PROBABILITY_SELECTION_SUMMARY_DB_DSN_ENV_VAR,
    PAPER_PROBABILITY_SELECTION_SUMMARY_DB_ENABLED_ENV_VAR,
    PAPER_PROBABILITY_SELECTION_SUMMARY_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-probability-selection-summary-history"
HISTORY_CONFIG_VERSION = "paper-probability-selection-summary-history-v0"


def _history_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 27, 12, 0, tzinfo=UTC),
        config_version=HISTORY_CONFIG_VERSION,
        source_report_count=4,
        first_generated_at=datetime(2026, 6, 27, 8, 0, tzinfo=UTC),
        latest_generated_at=datetime(2026, 6, 27, 11, 30, tzinfo=UTC),
        history_span_seconds=12_600,
        latest_age_seconds=1_800,
        latest_queue_count=5,
        latest_selected_count=2,
        latest_pending_count=2,
        latest_rejected_count=1,
        latest_skipped_count=1,
        aggregate_queue_count=20,
        aggregate_selected_count=9,
        aggregate_pending_count=7,
        aggregate_rejected_count=4,
        aggregate_skipped_count=2,
        latest_selected_share=Decimal("0.400000"),
        average_selected_share=Decimal("0.450000"),
        distinct_config_versions=("paper-probability-selection-summary-v0",),
        reason_code_counts=(
            ("cost_stress_passed", 9),
            ("latest_selection_has_watch_rows", 2),
            ("source_next_step_skip", 1),
        ),
        history_status="watch",
        recommended_next_step="review_probability_selection",
        reason_codes=("latest_selection_has_watch_rows",),
        rows=(SimpleNamespace(market_slug="secret-market", question="secret question"),),
        source_reports=(SimpleNamespace(question="do not print source detail"),),
        payload_json='{"secret":"payload-json-secret"}',
        report_sha256="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _set_source_summary_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_DB_TABLE,
) -> None:
    monkeypatch.setenv(PAPER_PROBABILITY_SELECTION_SUMMARY_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_PROBABILITY_SELECTION_SUMMARY_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_DB_TABLE_ENV_VAR,
        table_name,
    )


def _clear_source_summary_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(PAPER_PROBABILITY_SELECTION_SUMMARY_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(
        PAPER_PROBABILITY_SELECTION_SUMMARY_DB_TABLE_ENV_VAR,
        raising=False,
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


def test_parser_help_includes_paper_probability_selection_summary_history(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert COMMAND in captured.out


@pytest.mark.parametrize(
    "flag",
    (
        "--dsn",
        "--db-dsn",
        "--table",
        "--db-table",
        "--history-status",
        "--paper-probability-selection-summary-db-dsn",
        "--paper-probability-selection-summary-db-table",
        "--paper-probability-selection-summary-history-db-dsn",
        "--paper-probability-selection-summary-history-db-table",
        "--live",
        "--wallet",
        "--order",
        "--execute",
        "--auth",
        "--private-key",
        "--account",
    ),
)
def test_history_cli_rejects_db_live_wallet_order_execute_auth_and_account_flags(
    flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, flag, "forbidden-value"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert f"unrecognized arguments: {flag}" in captured.err


def test_disabled_source_summary_db_config_does_not_connect_or_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _clear_source_summary_db_env(monkeypatch)
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("history runner should not run without source DB config")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND],
        paper_probability_selection_summary_history_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert (
        f"{COMMAND} requires paper probability selection summary DB to be enabled"
        in captured.err
    )


@pytest.mark.parametrize("raw_limit", ("0", "-1"))
def test_history_cli_rejects_non_positive_limit_before_env_runner_or_connect(
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
        raise AssertionError("source summary DB env should not be read")

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("history runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setattr(
        cli,
        "from_paper_probability_selection_summary_db_env",
        forbidden_env,
        raising=False,
    )
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", raw_limit],
        paper_probability_selection_summary_history_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} limit must be positive" in captured.err


def test_history_cli_uses_source_env_config_and_prints_aggregate_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://selection-summary.example.invalid/db"
    table_name = "paper_probability_selection_summary_reports"
    _set_source_summary_db_env(monkeypatch, dsn, table_name=table_name)
    calls: list[dict[str, object]] = []
    report = _history_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == table_name
        assert kwargs["limit"] == 25
        config = kwargs["config"]
        assert type(config) is PaperProbabilitySelectionSummaryHistoryConfig
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
        paper_probability_selection_summary_history_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "source_report_count=4" in captured.out
    assert "first_generated_at=2026-06-27T08:00:00+00:00" in captured.out
    assert "latest_generated_at=2026-06-27T11:30:00+00:00" in captured.out
    assert "history_span_seconds=12600" in captured.out
    assert "latest_age_seconds=1800" in captured.out
    assert "latest_queue_count=5" in captured.out
    assert "latest_selected_count=2" in captured.out
    assert "latest_pending_count=2" in captured.out
    assert "latest_rejected_count=1" in captured.out
    assert "latest_skipped_count=1" in captured.out
    assert "aggregate_queue_count=20" in captured.out
    assert "aggregate_selected_count=9" in captured.out
    assert "aggregate_pending_count=7" in captured.out
    assert "aggregate_rejected_count=4" in captured.out
    assert "aggregate_skipped_count=2" in captured.out
    assert "latest_selected_share=0.400000" in captured.out
    assert "average_selected_share=0.450000" in captured.out
    assert (
        "distinct_config_versions=paper-probability-selection-summary-v0"
        in captured.out
    )
    assert "history_status=watch" in captured.out
    assert "recommended_next_step=review_probability_selection" in captured.out
    assert "reason_codes=latest_selection_has_watch_rows" in captured.out
    assert (
        "reason_code_counts: "
        "cost_stress_passed:9,"
        "latest_selection_has_watch_rows:2,"
        "source_next_step_skip:1"
    ) in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert table_name not in captured.out
    assert table_name not in captured.err
    assert "secret-market" not in captured.out
    assert "secret question" not in captured.out
    assert "do not print source detail" not in captured.out
    assert "payload-json-secret" not in captured.out
    assert "abcdef0123456789" not in captured.out


def test_history_cli_without_persist_does_not_read_history_db_env_or_sink(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://selection-summary.example.invalid/db"
    history_dsn = "postgresql://history-destination.example.invalid/db"
    _set_source_summary_db_env(monkeypatch, dsn)
    _set_history_db_env(monkeypatch, history_dsn)
    history_env_calls = 0
    sink_calls = 0

    def forbidden_history_env() -> object:
        nonlocal history_env_calls
        history_env_calls += 1
        raise AssertionError("history DB env should not be read without --persist")

    def forbidden_sink(**kwargs: Any) -> object:
        nonlocal sink_calls
        sink_calls += 1
        raise AssertionError("history sink should not run without --persist")

    monkeypatch.setattr(
        cli,
        "from_paper_probability_selection_summary_history_db_env",
        forbidden_history_env,
        raising=False,
    )

    exit_code = main(
        [COMMAND],
        paper_probability_selection_summary_history_runner=lambda **kwargs: (
            _history_report()
        ),
        paper_probability_selection_summary_history_db_sink=forbidden_sink,
    )

    assert exit_code == 0
    assert history_env_calls == 0
    assert sink_calls == 0
    captured = capsys.readouterr()
    assert "persisted=" not in captured.out
    assert history_dsn not in captured.out
    assert history_dsn not in captured.err


def test_history_cli_db_read_errors_redact_dsn_table_payload_and_hash(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = (
        "postgresql://history_user:super-secret-password@"
        "selection-source-secret.example.invalid/db?sslmode=require"
    )
    table_name = "paper_probability_selection_summary_reports"
    _set_source_summary_db_env(monkeypatch, dsn, table_name=table_name)

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
        paper_probability_selection_summary_history_runner=broken_runner,
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
        "secret-question",
        "secret-market",
        "payload-json-secret",
        "abcdef0123456789",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


def test_history_cli_optional_persistence_uses_history_env_db_config_not_local_files(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Any,
) -> None:
    source_dsn = "postgresql://selection-summary.example.invalid/db"
    history_dsn = "postgresql://selection-summary-history.example.invalid/db"
    source_table_name = "paper_probability_selection_summary_reports"
    history_table_name = "paper_probability_selection_summary_history_reports"
    _set_source_summary_db_env(monkeypatch, source_dsn, table_name=source_table_name)
    _set_history_db_env(monkeypatch, history_dsn, table_name=history_table_name)
    runner_report = _history_report()
    runner_calls: list[dict[str, object]] = []
    sink_calls: list[dict[str, object]] = []

    def fake_runner(**kwargs: Any) -> object:
        runner_calls.append(dict(kwargs))
        return runner_report

    def fake_sink(**kwargs: Any) -> SimpleNamespace:
        sink_calls.append(dict(kwargs))
        assert kwargs["dsn"] == history_dsn
        assert kwargs["table_name"] == history_table_name
        assert kwargs["report"] is runner_report
        return SimpleNamespace(inserted=True)

    exit_code = main(
        [COMMAND, "--persist"],
        paper_probability_selection_summary_history_runner=fake_runner,
        paper_probability_selection_summary_history_db_sink=fake_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    assert len(sink_calls) == 1
    captured = capsys.readouterr()
    assert f"{COMMAND}: persisted=True" in captured.out
    assert source_dsn not in captured.out
    assert history_dsn not in captured.out
    assert source_table_name not in captured.out
    assert history_table_name not in captured.out
    assert not list(tmp_path.iterdir())


def test_history_cli_persistence_errors_redact_source_history_payload_and_hash(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dsn = (
        "postgresql://source_user:source-secret-password@"
        "selection-source-secret.example.invalid/db?sslmode=require"
    )
    history_dsn = (
        "postgresql://history_user:history-secret-password@"
        "selection-history-secret.example.invalid/db?sslmode=require"
    )
    source_table_name = "paper_probability_selection_summary_reports_secret"
    history_table_name = "paper_probability_selection_summary_history_reports_secret"
    _set_source_summary_db_env(
        monkeypatch,
        source_dsn,
        table_name=source_table_name,
    )
    _set_history_db_env(
        monkeypatch,
        history_dsn,
        table_name=history_table_name,
    )
    report = _history_report()

    def broken_sink(**kwargs: Any) -> object:
        assert kwargs["dsn"] == history_dsn
        assert kwargs["table_name"] == history_table_name
        assert kwargs["report"] is report
        raise RuntimeError(
            f"persist failed source_dsn={source_dsn} "
            f"source_table={source_table_name} history_dsn={history_dsn} "
            f"history_table={history_table_name} question=secret-question "
            "market_slug=secret-market "
            "payload_json={\"secret\":\"payload-json-secret\"} "
            "report_sha256="
            "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        )

    exit_code = main(
        [COMMAND, "--persist"],
        paper_probability_selection_summary_history_runner=lambda **kwargs: report,
        paper_probability_selection_summary_history_db_sink=broken_sink,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "source_dsn=<redacted-dsn>" in captured.err
    assert "history_dsn=<redacted-dsn>" in captured.err
    assert "source_table=<redacted-table>" in captured.err
    assert "history_table=<redacted-table>" in captured.err
    for leaked_fragment in (
        source_dsn,
        history_dsn,
        "source-secret-password",
        "history-secret-password",
        source_table_name,
        history_table_name,
        "reports_secret",
        "secret-question",
        "secret-market",
        "payload-json-secret",
        "abcdef0123456789",
    ):
        assert leaked_fragment not in captured.err
        assert leaked_fragment not in captured.out


@pytest.mark.parametrize("bad_limit", (0, -1, True, "1", Decimal("1")))
def test_history_helper_rejects_invalid_limit_before_runner_or_psycopg(
    bad_limit: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))
    helper = getattr(cli, "_run_paper_probability_selection_summary_history")

    with pytest.raises(ValueError, match=f"{COMMAND} limit must be positive"):
        helper(
            dsn="postgresql://selection-summary.example.invalid/db",
            table_name="paper_probability_selection_summary_reports",
            limit=bad_limit,
            runner=forbidden_runner,
        )

    assert runner_calls == 0
    assert connect_calls == 0


def test_history_helper_default_load_path_reads_source_summaries_chronologically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dsn = "postgresql://selection-summary.example.invalid/db"
    table_name = "paper_probability_selection_summary_reports"
    report = _history_report()
    newest = SimpleNamespace(generated_at=datetime(2026, 6, 27, 11, 0, tzinfo=UTC))
    oldest = SimpleNamespace(generated_at=datetime(2026, 6, 27, 10, 0, tzinfo=UTC))
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
        config: PaperProbabilitySelectionSummaryHistoryConfig,
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
        assert type(config) is PaperProbabilitySelectionSummaryHistoryConfig
        assert config.config_version == HISTORY_CONFIG_VERSION
        assert generated_at.tzinfo is UTC
        return report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_probability_selection_summary_store."
        "load_paper_probability_selection_summary_reports",
        fake_load,
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_probability_selection_summary_history."
        "build_paper_probability_selection_summary_history_report",
        fake_builder,
    )

    helper = getattr(cli, "_run_paper_probability_selection_summary_history")
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
