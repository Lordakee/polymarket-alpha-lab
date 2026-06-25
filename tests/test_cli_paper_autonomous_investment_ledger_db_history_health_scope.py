from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main


COMMAND = "paper-autonomous-investment-ledger-db-history-health"


def _reason_count(reason_code: str, report_count: int) -> SimpleNamespace:
    return SimpleNamespace(reason_code=reason_code, report_count=report_count)


@pytest.mark.parametrize(
    "argv",
    (
        [COMMAND, "--dsn", "postgresql://investment-ledger.example.invalid/db"],
        [COMMAND, "--table", "paper_autonomous_investment_ledger_reports"],
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
        [COMMAND, "--cancel"],
        [COMMAND, "--sign"],
        [COMMAND, "--persist"],
        [COMMAND, "--config-version", "paper-autonomous-investment-ledger-v0"],
        [COMMAND, "--ledger-status", "submitted"],
    ),
)
def test_investment_ledger_db_history_health_cli_rejects_db_fast_live_auth_wallet_order_trade_execution_persist_config_and_status_flags(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err


def test_investment_ledger_db_history_health_summary_prints_only_aggregate_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = SimpleNamespace(
        generated_at=datetime(2026, 6, 24, 13, 0, tzinfo=UTC),
        config_version="paper-autonomous-investment-ledger-db-history-health-v0",
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
        latest_total_submitted_notional="123.450000",
        latest_source_generated_at=datetime(2026, 6, 25, 12, 0, tzinfo=UTC),
        latest_source_age_seconds=3600,
        max_source_age_seconds=18_000,
        duplicate_latest_generated_at_count=1,
        reason_code_counts=(
            _reason_count("latest_paper_autonomous_investment_ledger_watch", 1),
            _reason_count("stale_paper_autonomous_investment_ledger_source_history", 1),
        ),
        market_slug="secret-market-slug",
        question="Will hidden investment ledger market resolve yes?",
        account="secret-account-id",
        wallet="secret-wallet-address",
        order_id="secret-order-id",
        trade_id="secret-trade-id",
        payload_json={"wallet": "secret-wallet-address"},
        raw_payload={"order_id": "secret-order-id"},
        report_sha256=(
            "abcdef0123456789abcdef0123456789"
            "abcdef0123456789abcdef0123456789"
        ),
        api_key="secret-api-key",
        private_key="secret-private-key",
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    printer = getattr(
        cli,
        "_print_paper_autonomous_investment_ledger_db_history_health_summary",
    )
    printer(report)

    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: health_status=watch "
            "recommended_next_step="
            "throttle_paper_autonomous_investment_ledger_review "
            "ledger_report_count=4 latest_ledger_status=watch "
            "latest_source_record_count=9 latest_submitted_count=5 "
            "latest_held_count=3 latest_blocked_count=1 "
            "latest_total_submitted_notional=123.450000 "
            "latest_source_generated_at=2026-06-25T12:00:00+00:00 "
            "latest_source_age_seconds=3600 max_source_age_seconds=18000 "
            "pass_ledger_report_count=2 watch_ledger_report_count=1 "
            "blocked_ledger_report_count=1 "
            "duplicate_latest_generated_at_count=1"
        ),
        (
            "reason_code_counts: "
            "latest_paper_autonomous_investment_ledger_watch=1 "
            "stale_paper_autonomous_investment_ledger_source_history=1"
        ),
    ]
    assert captured.err == ""
    for forbidden in (
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
        "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "api_key",
        "secret-api-key",
        "private_key",
        "secret-private-key",
    ):
        assert forbidden not in captured.out
        assert forbidden not in captured.err
