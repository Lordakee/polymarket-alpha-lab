from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_config import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_trend_config import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR,
)


COMMAND = "action-gated-queue-decision-support-trend-db-history"


def _history_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 21, 12, 0, tzinfo=UTC),
        config_version="action-gated-queue-decision-support-trend-db-history-v0",
        trend_count=3,
        total_source_snapshot_count=12,
        first_trend_generated_at=datetime(2026, 6, 21, 8, 0, tzinfo=UTC),
        latest_trend_generated_at=datetime(2026, 6, 21, 10, 0, tzinfo=UTC),
        latest_risk_status="blocked",
        risk_status_counts=(("pass", 1), ("watch", 1), ("blocked", 1)),
        duplicate_generated_at_count=1,
        consecutive_latest_watch_count=0,
        consecutive_latest_blocked_count=2,
        ready_notional_delta=Decimal("-15.000000"),
        top_priority_score_delta=Decimal("-0.500000"),
        average_priority_score_delta=Decimal("-0.250000"),
        source_queue_count_delta=-2,
        latest_reason_code_counts=(
            ("candidate_count_cap_exceeded", 2),
            ("source_queue_blocked", 1),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _set_trend_db_env(monkeypatch: pytest.MonkeyPatch, dsn: str) -> None:
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR,
        "paper_action_gated_queue_decision_support_trend_reports_archive",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR,
        "paper_action_gated_queue_decision_support_trend_sources_archive",
    )


def test_trend_db_history_cli_requires_enabled_trend_db_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR,
        raising=False,
    )
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("trend DB history runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND],
        action_gated_queue_decision_support_trend_db_history_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert (
        f"{COMMAND} requires action-gated queue decision-support trend DB "
        "to be enabled"
    ) in captured.err


def test_trend_db_history_cli_uses_injected_runner_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://trend-db-history.example.invalid/db"
    _set_trend_db_env(monkeypatch, dsn)
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
        raising=False,
    )
    calls: list[dict[str, object]] = []
    report = _history_report()

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["dsn"] == dsn
        assert (
            kwargs["reports_table_name"]
            == "paper_action_gated_queue_decision_support_trend_reports_archive"
        )
        assert (
            kwargs["sources_table_name"]
            == "paper_action_gated_queue_decision_support_trend_sources_archive"
        )
        assert kwargs["latest_risk_status"] == "blocked"
        assert kwargs["limit"] == 25
        assert kwargs["config_version"] == (
            "action-gated-queue-decision-support-trend-db-history-v0"
        )
        assert isinstance(kwargs["generated_at"], datetime)
        return report

    exit_code = main(
        [
            COMMAND,
            "--latest-risk-status",
            "blocked",
            "--limit",
            "25",
        ],
        action_gated_queue_decision_support_trend_db_history_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "trend_count=3" in captured.out
    assert "total_source_snapshot_count=12" in captured.out
    assert "first_trend_generated_at=2026-06-21T08:00:00+00:00" in captured.out
    assert "latest_trend_generated_at=2026-06-21T10:00:00+00:00" in captured.out
    assert "latest_risk_status=blocked" in captured.out
    assert "pass=1" in captured.out
    assert "watch=1" in captured.out
    assert "blocked=1" in captured.out
    assert "ready_notional_delta=-15.000000" in captured.out
    assert "top_priority_score_delta=-0.500000" in captured.out
    assert "average_priority_score_delta=-0.250000" in captured.out
    assert "source_queue_count_delta=-2" in captured.out
    assert "duplicate_generated_at_count=1" in captured.out
    assert "consecutive_latest_watch_count=0" in captured.out
    assert "consecutive_latest_blocked_count=2" in captured.out
    assert (
        "latest_reason_codes: "
        "candidate_count_cap_exceeded:2,source_queue_blocked:1"
    ) in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "reports_archive" not in captured.out
    assert "sources_archive" not in captured.out


def test_trend_db_history_cli_default_load_path_uses_persisted_trend_rows_only(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://trend-db-history.example.invalid/db"
    _set_trend_db_env(monkeypatch, dsn)
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
        raising=False,
    )
    load_calls: list[dict[str, object]] = []

    def fake_load(
        load_dsn: str,
        *,
        latest_risk_status: str | None,
        limit: int,
        reports_table_name: str,
        sources_table_name: str,
    ) -> tuple[object, ...]:
        load_calls.append(
            {
                "dsn": load_dsn,
                "latest_risk_status": latest_risk_status,
                "limit": limit,
                "reports_table_name": reports_table_name,
                "sources_table_name": sources_table_name,
            },
        )
        return ()

    monkeypatch.setattr(
        "polymarket_alpha_lab."
        "action_gated_strategy_recommendation_queue_decision_support_trend_psycopg."
        "load_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg",
        fake_load,
    )

    exit_code = main([COMMAND, "--limit", "7"], client_factory=lambda: object())

    assert exit_code == 0
    assert load_calls == [
        {
            "dsn": dsn,
            "latest_risk_status": None,
            "limit": 7,
            "reports_table_name": (
                "paper_action_gated_queue_decision_support_trend_reports_archive"
            ),
            "sources_table_name": (
                "paper_action_gated_queue_decision_support_trend_sources_archive"
            ),
        },
    ]
    captured = capsys.readouterr()
    assert "trend_count=0" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err


def test_trend_db_history_cli_read_failure_redacts_dsn(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://trend-db-history-secret.example.invalid/db"
    _set_trend_db_env(monkeypatch, dsn)

    def fake_runner(**kwargs: Any) -> object:
        raise RuntimeError(f"could not connect to {kwargs['dsn']}")

    exit_code = main(
        [COMMAND],
        action_gated_queue_decision_support_trend_db_history_runner=fake_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "<redacted-dsn>" in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err


def test_trend_db_history_cli_rejects_non_positive_limit_before_runner(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://trend-db-history.example.invalid/db"
    _set_trend_db_env(monkeypatch, dsn)
    runner_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("trend DB history runner should not run")

    exit_code = main(
        [COMMAND, "--limit", "0"],
        action_gated_queue_decision_support_trend_db_history_runner=forbidden_runner,
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
        "--action-gated-queue-decision-support-trend-db-dsn",
        "--action-gated-queue-decision-support-trend-db-reports-table",
        "--action-gated-queue-decision-support-trend-db-sources-table",
    ),
)
def test_trend_db_history_cli_rejects_db_plumbing_flags(
    flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, flag, "value"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert f"unrecognized arguments: {flag}" in captured.err
