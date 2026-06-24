from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_config import (
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR,
)


COMMAND = "paper-autonomous-allocation-proposal-db-history-health"


def _reason_count(reason_code: str, report_count: int) -> SimpleNamespace:
    return SimpleNamespace(reason_code=reason_code, report_count=report_count)


@pytest.mark.parametrize(
    "argv",
    (
        [COMMAND, "--dsn", "postgresql://allocation-proposal.example.invalid/db"],
        [COMMAND, "--table", "paper_autonomous_allocation_proposal_reports"],
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
def test_allocation_proposal_db_history_health_cli_rejects_db_fast_live_auth_wallet_account_order_and_execution_flags(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err


def test_allocation_proposal_db_history_health_cli_accepts_persist_flag_at_parser_boundary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR, raising=False)

    exit_code = main([COMMAND, "--persist"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "unrecognized arguments" not in captured.err
    assert f"{COMMAND} requires autonomous allocation proposal DB to be enabled" in (
        captured.err
    )


def test_allocation_proposal_db_history_health_summary_prints_only_aggregate_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = SimpleNamespace(
        generated_at=datetime(2026, 6, 24, 13, 0, tzinfo=UTC),
        config_version="paper-autonomous-allocation-proposal-db-history-health-v0",
        health_status="watch",
        recommended_next_step=(
            "throttle_paper_autonomous_allocation_proposal_history_review"
        ),
        history_report_count=4,
        latest_history_status="watch",
        latest_allocated_count=3,
        latest_total_allocated_paper_notional="42.000000",
        max_source_age_seconds=18_000,
        latest_source_age_seconds=3600,
        pass_report_count=2,
        watch_report_count=1,
        blocked_report_count=1,
        duplicate_latest_report_generated_at_count=1,
        reason_code_counts=(
            _reason_count("latest_allocation_proposal_watch", 1),
            _reason_count("source_allocation_proposal_db_history_watch", 1),
        ),
        latest_proposal_status="secret_proposal_status",
        market_slug="secret-market-slug",
        question="Will hidden allocation proposal market resolve yes?",
        payload_json={"market_slug": "secret-market-slug"},
        report_sha256=(
            "abcdef0123456789abcdef0123456789"
            "abcdef0123456789abcdef0123456789"
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    printer = getattr(
        cli,
        "_print_paper_autonomous_allocation_proposal_db_history_health_summary",
    )
    printer(report)

    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: health_status=watch "
            "recommended_next_step="
            "throttle_paper_autonomous_allocation_proposal_history_review "
            "history_report_count=4 latest_history_status=watch "
            "latest_allocated_count=3 "
            "latest_total_allocated_paper_notional=42.000000 "
            "latest_source_age_seconds=3600 max_source_age_seconds=18000 "
            "pass_report_count=2 watch_report_count=1 blocked_report_count=1 "
            "duplicate_latest_report_generated_at_count=1"
        ),
        (
            "reason_code_counts: latest_allocation_proposal_watch=1 "
            "source_allocation_proposal_db_history_watch=1"
        ),
    ]
    assert captured.err == ""
    for forbidden in (
        "latest_proposal_status",
        "secret_proposal_status",
        "market_slug",
        "secret-market-slug",
        "question",
        "Will hidden allocation proposal market resolve yes?",
        "payload_json",
        "report_sha256",
        "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
    ):
        assert forbidden not in captured.out
        assert forbidden not in captured.err
