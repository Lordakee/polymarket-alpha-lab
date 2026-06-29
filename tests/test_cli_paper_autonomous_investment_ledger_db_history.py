from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.cli import (
    _load_paper_autonomous_investment_ledger_db_history,
    main,
)
from polymarket_alpha_lab.supabase_paper_autonomous_investment_ledger_config import (
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-autonomous-investment-ledger-db-history"


def _enable_ledger_db(monkeypatch, *, dsn: str, table_name: str) -> None:
    monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_TABLE_ENV_VAR, table_name)


def _ledger_report(
    *,
    generated_at: datetime,
    ledger_status: str,
    source_record_count: int,
    submitted_count: int,
    held_count: int,
    blocked_count: int,
    total_submitted_notional: Decimal,
    latest_age_seconds: int | None,
) -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=generated_at,
        config_version="paper-autonomous-investment-ledger-v0",
        ledger_status=ledger_status,
        recommended_next_step=f"{ledger_status}_next_step",
        source_record_count=source_record_count,
        submitted_count=submitted_count,
        held_count=held_count,
        blocked_count=blocked_count,
        total_submitted_notional=total_submitted_notional,
        held_zero_notional_count=held_count,
        blocked_zero_notional_count=blocked_count,
        latest_generated_at=generated_at,
        latest_age_seconds=latest_age_seconds,
        reason_code_counts=(
            SimpleNamespace(
                reason_code=f"{ledger_status}_reason",
                source_record_count=source_record_count,
            ),
        ),
        entries=(),
        reason_codes=(f"{ledger_status}_reason",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_investment_ledger_db_history_cli_requires_ledger_db_enabled(capsys) -> None:
    runner_calls = 0

    def forbidden_runner(**_kwargs: object) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("runner should not run without ledger DB")

    exit_code = main(
        [COMMAND],
        paper_autonomous_investment_ledger_db_history_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert runner_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} requires paper autonomous investment ledger DB to be enabled" in (
        captured.err
    )


def test_investment_ledger_db_history_cli_uses_injected_runner_and_prints_recent_summaries(
    monkeypatch,
    capsys,
) -> None:
    dsn = "postgresql://paper-ledger:secret@localhost:54322/db"
    _enable_ledger_db(
        monkeypatch,
        dsn=dsn,
        table_name="paper_investment_ledger_archive",
    )
    reports = (
        _ledger_report(
            generated_at=datetime(2026, 6, 25, 12, 0, tzinfo=UTC),
            ledger_status="pass",
            source_record_count=4,
            submitted_count=4,
            held_count=0,
            blocked_count=0,
            total_submitted_notional=Decimal("80.000000"),
            latest_age_seconds=60,
        ),
        _ledger_report(
            generated_at=datetime(2026, 6, 25, 11, 0, tzinfo=UTC),
            ledger_status="watch",
            source_record_count=3,
            submitted_count=1,
            held_count=2,
            blocked_count=0,
            total_submitted_notional=Decimal("20.000000"),
            latest_age_seconds=3600,
        ),
    )
    runner_calls = []

    def fake_runner(**kwargs: object) -> object:
        runner_calls.append(kwargs)
        return reports

    exit_code = main(
        [
            COMMAND,
            "--limit",
            "9",
            "--config-version",
            "paper-autonomous-investment-ledger-v0",
            "--ledger-status",
            "watch",
        ],
        paper_autonomous_investment_ledger_db_history_runner=fake_runner,
    )

    assert exit_code == 0
    assert runner_calls == [
        {
            "dsn": dsn,
            "table_name": "paper_investment_ledger_archive",
            "limit": 9,
            "config_version": "paper-autonomous-investment-ledger-v0",
            "ledger_status": "watch",
        },
    ]
    captured = capsys.readouterr()
    assert f"{COMMAND}: 2 reports" in captured.out
    assert (
        "[1] generated_at=2026-06-25T12:00:00+00:00 ledger_status=pass "
        "source_record_count=4 submitted_count=4 held_count=0 blocked_count=0 "
        "total_submitted_notional=80.000000 latest_age_seconds=60"
    ) in captured.out
    assert (
        "[2] generated_at=2026-06-25T11:00:00+00:00 ledger_status=watch "
        "source_record_count=3 submitted_count=1 held_count=2 blocked_count=0 "
        "total_submitted_notional=20.000000 latest_age_seconds=3600"
    ) in captured.out
    assert "reason_code_counts: pass_reason=4" in captured.out
    assert "reason_code_counts: watch_reason=3" in captured.out


def test_investment_ledger_db_history_cli_prints_empty_history(
    monkeypatch,
    capsys,
) -> None:
    _enable_ledger_db(
        monkeypatch,
        dsn="postgresql://paper-ledger:secret@localhost:54322/db",
        table_name="paper_investment_ledger_archive",
    )

    exit_code = main(
        [COMMAND],
        paper_autonomous_investment_ledger_db_history_runner=lambda **_kwargs: (),
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert f"{COMMAND}: no reports found" in captured.out


def test_investment_ledger_db_history_cli_runner_failure_redacts_db_and_payload(
    monkeypatch,
    capsys,
) -> None:
    dsn = "postgresql://paper-ledger:secret@localhost:54322/db"
    table_name = "paper_ledger_secret_archive"
    payload_json = '{"market_slug":"secret-market","question":"hidden question"}'
    _enable_ledger_db(monkeypatch, dsn=dsn, table_name=table_name)

    def broken_runner(**_kwargs: object) -> object:
        raise RuntimeError(
            f"dsn={dsn} table={table_name} payload_json={payload_json} "
            "report_sha256=abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
        )

    exit_code = main(
        [COMMAND],
        paper_autonomous_investment_ledger_db_history_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "dsn=<redacted-dsn>" in captured.err
    assert "table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    for secret in (
        dsn,
        table_name,
        payload_json,
        "secret-market",
        "hidden question",
        "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_load_investment_ledger_db_history_uses_psycopg_loader(
    monkeypatch,
) -> None:
    reports = (
        _ledger_report(
            generated_at=datetime(2026, 6, 25, 12, 0, tzinfo=UTC),
            ledger_status="watch",
            source_record_count=3,
            submitted_count=1,
            held_count=2,
            blocked_count=0,
            total_submitted_notional=Decimal("20.000000"),
            latest_age_seconds=3600,
        ),
    )
    loader_calls = []

    def fake_loader(**kwargs: object) -> object:
        loader_calls.append(kwargs)
        return reports

    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_psycopg."
        "load_paper_autonomous_investment_ledger_reports_with_psycopg",
        fake_loader,
    )

    actual = _load_paper_autonomous_investment_ledger_db_history(
        dsn="postgresql://paper-ledger:secret@localhost:54322/db",
        table_name="paper_investment_ledger_archive",
        limit=13,
        config_version="paper-autonomous-investment-ledger-v0",
        ledger_status="watch",
    )

    assert actual == reports
    assert loader_calls == [
        {
            "dsn": "postgresql://paper-ledger:secret@localhost:54322/db",
            "table_name": "paper_investment_ledger_archive",
            "limit": 13,
            "config_version": "paper-autonomous-investment-ledger-v0",
            "ledger_status": "watch",
        },
    ]


@pytest.mark.parametrize("limit", (0, -1, True, "1", 1.0))
def test_load_investment_ledger_db_history_rejects_invalid_limit_before_load(
    monkeypatch,
    limit: object,
) -> None:
    loader_calls = 0

    def forbidden_loader(**_kwargs: object) -> object:
        nonlocal loader_calls
        loader_calls += 1
        raise AssertionError("loader should not run after invalid limit")

    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_psycopg."
        "load_paper_autonomous_investment_ledger_reports_with_psycopg",
        forbidden_loader,
    )

    with pytest.raises(ValueError, match="limit must be positive"):
        _load_paper_autonomous_investment_ledger_db_history(
            dsn="postgresql://paper-ledger:secret@localhost:54322/db",
            table_name="paper_investment_ledger_archive",
            limit=limit,  # type: ignore[arg-type]
        )

    assert loader_calls == 0


@pytest.mark.parametrize(
    "flag",
    (
        "--dsn",
        "--table",
        "--fast",
        "--live",
        "--auth",
        "--wallet",
        "--private-key",
        "--api-key",
        "--account",
        "--order",
        "--trade",
        "--execute",
        "--submit",
        "--approve",
        "--cancel",
        "--sign",
        "--persist",
    ),
)
def test_investment_ledger_db_history_cli_rejects_db_fast_live_auth_wallet_order_execution_and_persist_flags(
    capsys,
    flag: str,
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, flag, "value"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err
    assert flag in captured.err
