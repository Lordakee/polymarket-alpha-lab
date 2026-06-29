from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_config import (
    ACTION_GATED_QUEUE_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_history_config import (
    ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR,
)


COMMAND = "action-gated-queue-history-db-history"


def _history_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 21, 12, 0, tzinfo=UTC),
        config_version="action-gated-queue-history-db-history-v0",
        history_report_count=3,
        first_history_generated_at=datetime(2026, 6, 21, 8, 0, tzinfo=UTC),
        latest_history_generated_at=datetime(2026, 6, 21, 10, 0, tzinfo=UTC),
        latest_source_report_count=12,
        latest_action_status="research_ready",
        latest_recommended_next_step="review_candidate_research_queue",
        action_status_counts=(("research_ready", 2), ("watch", 1), ("blocked", 0)),
        duplicate_generated_at_count=1,
        consecutive_latest_research_ready_count=2,
        consecutive_latest_watch_count=0,
        consecutive_latest_blocked_count=0,
        latest_total_ready_notional=Decimal("42.000000"),
        latest_ready_notional_delta=Decimal("12.000000"),
        latest_status_transition_count=2,
        latest_reason_code_counts=(
            ("queue_ready", 2),
            ("risk_review_clear", 1),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _set_history_db_env(monkeypatch: pytest.MonkeyPatch, dsn: str) -> None:
    monkeypatch.setenv(ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR,
        "paper_action_gated_queue_history_reports_archive",
    )


def test_queue_history_db_history_cli_requires_enabled_history_db_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR, raising=False)
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("queue history DB history runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND],
        action_gated_queue_history_db_history_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires action-gated queue history DB to be enabled" in (
        captured.err
    )


def test_queue_history_db_history_cli_requires_history_db_dsn(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.delenv(ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR,
        "paper_action_gated_queue_history_reports_archive",
    )
    runner_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("queue history DB history runner should not run")

    exit_code = main(
        [COMMAND],
        action_gated_queue_history_db_history_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert runner_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert (
        f"{ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR} must be set when DB is enabled"
        in captured.err
    )


def test_queue_history_db_history_cli_uses_injected_runner_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://queue-history-db-history:secret@localhost:54322/db"
    _set_history_db_env(monkeypatch, dsn)
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, raising=False)
    calls: list[dict[str, object]] = []
    report = _history_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert kwargs["table_name"] == "paper_action_gated_queue_history_reports_archive"
        assert kwargs["latest_action_status"] == "research_ready"
        assert kwargs["limit"] == 25
        assert kwargs["config_version"] == "action-gated-queue-history-db-history-v0"
        assert isinstance(kwargs["generated_at"], datetime)
        return report

    exit_code = main(
        [
            COMMAND,
            "--latest-action-status",
            "research_ready",
            "--limit",
            "25",
        ],
        action_gated_queue_history_db_history_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "history_report_count=3" in captured.out
    assert "first_history_generated_at=2026-06-21T08:00:00+00:00" in captured.out
    assert "latest_history_generated_at=2026-06-21T10:00:00+00:00" in captured.out
    assert "latest_source_report_count=12" in captured.out
    assert "latest_action_status=research_ready" in captured.out
    assert "latest_recommended_next_step=review_candidate_research_queue" in (
        captured.out
    )
    assert "research_ready=2" in captured.out
    assert "watch=1" in captured.out
    assert "blocked=0" in captured.out
    assert "duplicate_generated_at_count=1" in captured.out
    assert "consecutive_latest_research_ready_count=2" in captured.out
    assert "consecutive_latest_watch_count=0" in captured.out
    assert "consecutive_latest_blocked_count=0" in captured.out
    assert "latest_total_ready_notional=42.000000" in captured.out
    assert "latest_ready_notional_delta=12.000000" in captured.out
    assert "latest_status_transition_count=2" in captured.out
    assert "latest_reason_codes: queue_ready:2,risk_review_clear:1" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "reports_archive" not in captured.out


def test_queue_history_db_history_cli_default_load_path_reads_persisted_history_only(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://queue-history-db-history:secret@localhost:54322/db"
    _set_history_db_env(monkeypatch, dsn)
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, raising=False)
    load_calls: list[dict[str, object]] = []

    def fake_load(
        load_dsn: str,
        *,
        latest_action_status: str | None,
        limit: int,
        table_name: str,
    ) -> tuple[object, ...]:
        load_calls.append(
            {
                "dsn": load_dsn,
                "latest_action_status": latest_action_status,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return ()

    monkeypatch.setattr(
        "polymarket_alpha_lab."
        "action_gated_strategy_recommendation_queue_history_psycopg."
        "load_paper_action_gated_strategy_recommendation_queue_history_reports_with_psycopg",
        fake_load,
    )

    exit_code = main([COMMAND, "--limit", "7"], client_factory=lambda: object())

    assert exit_code == 0
    assert load_calls == [
        {
            "dsn": dsn,
            "latest_action_status": None,
            "limit": 7,
            "table_name": "paper_action_gated_queue_history_reports_archive",
        },
    ]
    captured = capsys.readouterr()
    assert "history_report_count=0" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err


def test_queue_history_db_history_cli_read_failure_redacts_dsn(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://queue-history-secret:secret@localhost:54322/db"
    _set_history_db_env(monkeypatch, dsn)

    def fake_runner(**kwargs: Any) -> object:
        raise RuntimeError(f"could not connect to {kwargs['dsn']}")

    exit_code = main(
        [COMMAND],
        action_gated_queue_history_db_history_runner=fake_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "<redacted-dsn>" in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err


def test_queue_history_db_history_cli_rejects_non_positive_limit_before_runner(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://queue-history-db-history:secret@localhost:54322/db"
    _set_history_db_env(monkeypatch, dsn)
    runner_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("queue history DB history runner should not run")

    exit_code = main(
        [COMMAND, "--limit", "0"],
        action_gated_queue_history_db_history_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert runner_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} limit must be positive" in captured.err


@pytest.mark.parametrize(
    "flag",
    (
        "--dsn",
        "--db-dsn",
        "--action-gated-queue-history-db-dsn",
        "--action-gated-queue-history-db-table",
        "--source-config-version",
        "--action-status",
        "--persist",
    ),
)
def test_queue_history_db_history_cli_rejects_db_plumbing_and_source_flags(
    flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, flag, "value"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert f"unrecognized arguments: {flag}" in captured.err
