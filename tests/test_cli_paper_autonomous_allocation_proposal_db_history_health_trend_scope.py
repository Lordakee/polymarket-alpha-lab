from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main


COMMAND = "paper-autonomous-allocation-proposal-db-history-health-trend"


@pytest.mark.parametrize(
    "argv",
    (
        [COMMAND, "--dsn", "postgresql://allocation-proposal.example.invalid/db"],
        [
            COMMAND,
            "--table",
            "paper_autonomous_allocation_proposal_db_history_health_reports",
        ],
        [COMMAND, "--persist"],
        [COMMAND, "--lim", "7"],
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
def test_allocation_proposal_db_history_health_trend_cli_rejects_db_persist_fast_live_auth_wallet_account_order_and_execution_flags(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err


def test_allocation_proposal_db_history_health_trend_summary_prints_only_aggregate_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = SimpleNamespace(
        generated_at=datetime(2026, 6, 24, 13, 0, tzinfo=UTC),
        config_version="paper-autonomous-allocation-proposal-db-history-health-trend-v0",
        source_health_report_count=4,
        latest_health_status="watch",
        history_report_count_delta=1,
        pass_report_count_delta=0,
        watch_report_count_delta=1,
        blocked_report_count_delta=0,
        latest_allocated_count_delta=2,
        latest_total_allocated_paper_notional_delta="15.750000",
        duplicate_generated_at_count=1,
        consecutive_latest_watch_count=2,
        consecutive_latest_blocked_count=0,
        latest_reason_code_counts=(
            ("latest_allocation_proposal_db_history_watch", 1),
            ("stale_allocation_proposal_db_history", 1),
        ),
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
        "_print_paper_autonomous_allocation_proposal_db_history_health_trend_summary",
    )
    printer(report)

    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: trend_count=4 latest_health_status=watch "
            "history_report_count_delta=1 pass_report_count_delta=0 "
            "watch_report_count_delta=1 blocked_report_count_delta=0 "
            "latest_allocated_count_delta=2 "
            "latest_total_allocated_paper_notional_delta=15.750000 "
            "duplicate_generated_at_count=1 "
            "consecutive_latest_watch_count=2 "
            "consecutive_latest_blocked_count=0 "
            "latest_reason_code_counts="
            "latest_allocation_proposal_db_history_watch=1,"
            "stale_allocation_proposal_db_history=1"
        ),
    ]
    assert captured.err == ""
    for forbidden in (
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
