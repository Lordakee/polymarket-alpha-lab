from __future__ import annotations

import pytest

from polymarket_alpha_lab.cli import main


COMMAND = "paper-autonomous-investment-ledger-db-history-health-trend-gate"


@pytest.mark.parametrize(
    "argv",
    (
        [COMMAND, "--dsn", "postgresql://investment-ledger.example.invalid/db"],
        [COMMAND, "--table", "paper_autonomous_investment_ledger_reports"],
        [COMMAND, "--db-dsn", "postgresql://investment-ledger.example.invalid/db"],
        [COMMAND, "--db-table", "paper_autonomous_investment_ledger_reports"],
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
def test_investment_ledger_db_history_health_trend_gate_cli_rejects_db_fast_live_auth_wallet_order_trade_execution_persist_config_and_status_flags(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err


def test_investment_ledger_db_history_health_trend_gate_cli_rejects_abbreviated_limit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, "--lim", "7"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err
