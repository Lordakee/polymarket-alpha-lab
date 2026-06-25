from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

import polymarket_alpha_lab.cli as cli_module
from polymarket_alpha_lab.cli import (
    _load_paper_autonomous_investment_ledger_from_broker_db,
    _print_paper_autonomous_investment_ledger_summary,
    main,
)
from polymarket_alpha_lab.supabase_paper_autonomous_investment_ledger_config import (
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_broker_config import (
    PAPER_BROKER_DB_DSN_ENV_VAR,
    PAPER_BROKER_DB_ENABLED_ENV_VAR,
    PAPER_BROKER_DB_TABLE_ENV_VAR,
)


def _ledger_report(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "ledger_status": "watch",
        "recommended_next_step": "review_paper_autonomous_investment_ledger",
        "source_record_count": 3,
        "submitted_count": 1,
        "held_count": 2,
        "blocked_count": 0,
        "total_submitted_notional": Decimal("42.500000"),
        "held_zero_notional_count": 2,
        "blocked_zero_notional_count": 0,
        "latest_generated_at": datetime(2026, 6, 25, 12, 30, tzinfo=UTC),
        "latest_age_seconds": 90,
        "reason_code_counts": (
            SimpleNamespace(
                reason_code="paper_broker_gate_held",
                source_record_count=2,
            ),
            SimpleNamespace(
                reason_code="paper_broker_execution_submitted",
                source_record_count=1,
            ),
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _enable_broker_db(monkeypatch, *, dsn: str, table_name: str) -> None:
    monkeypatch.setenv(PAPER_BROKER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_BROKER_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(PAPER_BROKER_DB_TABLE_ENV_VAR, table_name)


def _enable_ledger_db(monkeypatch, *, dsn: str, table_name: str) -> None:
    monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_TABLE_ENV_VAR, table_name)


def test_paper_autonomous_investment_ledger_cli_requires_broker_db_enabled(
    capsys,
) -> None:
    runner_calls = 0

    def forbidden_runner(**_kwargs: object) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("runner should not run without broker DB config")

    exit_code = main(
        ["paper-autonomous-investment-ledger"],
        paper_autonomous_investment_ledger_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert runner_calls == 0
    captured = capsys.readouterr()
    assert (
        "paper-autonomous-investment-ledger requires paper broker DB to be enabled"
        in captured.err
    )


@pytest.mark.parametrize("limit", ("0", "-1"))
def test_paper_autonomous_investment_ledger_cli_rejects_non_positive_limit_before_env(
    monkeypatch,
    capsys,
    limit: str,
) -> None:
    env_calls = 0

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("broker DB env should not be read after invalid limit")

    monkeypatch.setattr(cli_module, "from_paper_broker_db_env", forbidden_env)

    exit_code = main(
        ["paper-autonomous-investment-ledger", "--limit", limit],
        paper_autonomous_investment_ledger_runner=(
            lambda **_kwargs: (_ for _ in ()).throw(
                AssertionError("runner should not run after invalid limit"),
            )
        ),
    )

    assert exit_code == 1
    assert env_calls == 0
    captured = capsys.readouterr()
    assert "paper-autonomous-investment-ledger limit must be positive" in captured.err


def test_paper_autonomous_investment_ledger_cli_loads_broker_records_and_prints_summary(
    monkeypatch,
    capsys,
) -> None:
    broker_dsn = "postgresql://paper-broker.example.invalid/db"
    _enable_broker_db(
        monkeypatch,
        dsn=broker_dsn,
        table_name="paper_broker_archive",
    )
    runner_calls = []

    def fake_runner(**kwargs: object) -> object:
        runner_calls.append(kwargs)
        return _ledger_report()

    exit_code = main(
        [
            "paper-autonomous-investment-ledger",
            "--limit",
            "17",
            "--source-config-version",
            "paper-broker-v0",
            "--execution-status",
            "paper_submitted",
            "--source-gate-status",
            "pass",
            "--max-latest-source-age-seconds",
            "600",
        ],
        paper_autonomous_investment_ledger_runner=fake_runner,
    )

    assert exit_code == 0
    assert runner_calls == [
        {
            "broker_dsn": broker_dsn,
            "broker_table_name": "paper_broker_archive",
            "limit": 17,
            "source_config_version": "paper-broker-v0",
            "execution_status": "paper_submitted",
            "source_gate_status": "pass",
            "max_latest_source_age_seconds": 600,
        },
    ]
    captured = capsys.readouterr()
    assert "paper-autonomous-investment-ledger:" in captured.out
    assert "ledger_status=watch" in captured.out
    assert (
        "recommended_next_step=review_paper_autonomous_investment_ledger"
        in captured.out
    )
    assert "source_record_count=3" in captured.out
    assert "submitted_count=1" in captured.out
    assert "held_count=2" in captured.out
    assert "blocked_count=0" in captured.out
    assert "held_zero_notional_count=2" in captured.out
    assert "blocked_zero_notional_count=0" in captured.out
    assert "total_submitted_notional=42.500000" in captured.out
    assert "latest_generated_at=2026-06-25T12:30:00+00:00" in captured.out
    assert "latest_age_seconds=90" in captured.out
    assert (
        "reason_code_counts: paper_broker_gate_held=2 "
        "paper_broker_execution_submitted=1"
    ) in captured.out


def test_paper_autonomous_investment_ledger_cli_without_persist_skips_ledger_db_env_and_sink(
    monkeypatch,
    capsys,
) -> None:
    _enable_broker_db(
        monkeypatch,
        dsn="postgresql://paper-broker.example.invalid/db",
        table_name="paper_broker_archive",
    )
    _enable_ledger_db(
        monkeypatch,
        dsn="postgresql://paper-ledger.example.invalid/db",
        table_name="paper_investment_ledger_archive",
    )
    ledger_env_calls = 0

    def forbidden_ledger_env() -> object:
        nonlocal ledger_env_calls
        ledger_env_calls += 1
        raise AssertionError("ledger DB env should not be read without --persist")

    monkeypatch.setattr(
        cli_module,
        "from_paper_autonomous_investment_ledger_db_env",
        forbidden_ledger_env,
    )

    exit_code = main(
        ["paper-autonomous-investment-ledger"],
        paper_autonomous_investment_ledger_runner=lambda **_kwargs: _ledger_report(),
        paper_autonomous_investment_ledger_db_sink=(
            lambda **_kwargs: (_ for _ in ()).throw(
                AssertionError("sink should not run without --persist"),
            )
        ),
    )

    assert exit_code == 0
    assert ledger_env_calls == 0
    captured = capsys.readouterr()
    assert "persisted=" not in captured.out


def test_paper_autonomous_investment_ledger_cli_persists_when_requested(
    monkeypatch,
    capsys,
) -> None:
    broker_dsn = "postgresql://paper-broker.example.invalid/db"
    ledger_dsn = "postgresql://paper-ledger.example.invalid/db"
    _enable_broker_db(
        monkeypatch,
        dsn=broker_dsn,
        table_name="paper_broker_archive",
    )
    _enable_ledger_db(
        monkeypatch,
        dsn=ledger_dsn,
        table_name="paper_investment_ledger_archive",
    )
    report = _ledger_report(ledger_status="pass")
    sink_calls = []

    def fake_runner(**_kwargs: object) -> object:
        return report

    def fake_sink(**kwargs: object) -> object:
        sink_calls.append(kwargs)
        return SimpleNamespace(inserted=True)

    exit_code = main(
        ["paper-autonomous-investment-ledger", "--persist"],
        paper_autonomous_investment_ledger_runner=fake_runner,
        paper_autonomous_investment_ledger_db_sink=fake_sink,
    )

    assert exit_code == 0
    assert sink_calls == [
        {
            "dsn": ledger_dsn,
            "report": report,
            "table_name": "paper_investment_ledger_archive",
        },
    ]
    captured = capsys.readouterr()
    assert "paper-autonomous-investment-ledger: persisted=True" in captured.out
    assert "ledger_status=pass" in captured.out


def test_paper_autonomous_investment_ledger_cli_reports_duplicate_persist_noop(
    monkeypatch,
    capsys,
) -> None:
    _enable_broker_db(
        monkeypatch,
        dsn="postgresql://paper-broker.example.invalid/db",
        table_name="paper_broker_archive",
    )
    _enable_ledger_db(
        monkeypatch,
        dsn="postgresql://paper-ledger.example.invalid/db",
        table_name="paper_investment_ledger_archive",
    )

    exit_code = main(
        ["paper-autonomous-investment-ledger", "--persist"],
        paper_autonomous_investment_ledger_runner=lambda **_kwargs: _ledger_report(),
        paper_autonomous_investment_ledger_db_sink=(
            lambda **_kwargs: SimpleNamespace(inserted=False)
        ),
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "paper-autonomous-investment-ledger: persisted=False" in captured.out


def test_paper_autonomous_investment_ledger_cli_persist_requires_ledger_db_enabled(
    monkeypatch,
    capsys,
) -> None:
    _enable_broker_db(
        monkeypatch,
        dsn="postgresql://paper-broker.example.invalid/db",
        table_name="paper_broker_archive",
    )

    exit_code = main(
        ["paper-autonomous-investment-ledger", "--persist"],
        paper_autonomous_investment_ledger_runner=lambda **_kwargs: _ledger_report(),
        paper_autonomous_investment_ledger_db_sink=lambda **_kwargs: None,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "paper-autonomous-investment-ledger persistence requires paper autonomous "
        "investment ledger DB to be enabled"
    ) in captured.err


def test_paper_autonomous_investment_ledger_cli_runner_failure_redacts_source_db(
    monkeypatch,
    capsys,
) -> None:
    broker_dsn = "postgresql://paper-broker-secret.example.invalid/db"
    broker_table = "paper_broker_secret_archive"
    _enable_broker_db(monkeypatch, dsn=broker_dsn, table_name=broker_table)
    payload_json = '{"market_slug":"secret-market","question":"hidden question"}'

    def broken_runner(**_kwargs: object) -> object:
        raise RuntimeError(
            f"broker_dsn={broker_dsn} broker_table={broker_table} "
            f"payload_json={payload_json}"
        )

    exit_code = main(
        ["paper-autonomous-investment-ledger"],
        paper_autonomous_investment_ledger_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "broker_dsn=<redacted-dsn>" in captured.err
    assert "broker_table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    for secret in (
        broker_dsn,
        broker_table,
        "paper_broker_secret_archive",
        payload_json,
        "secret-market",
        "hidden question",
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_paper_autonomous_investment_ledger_cli_sink_failure_redacts_source_and_target_db(
    monkeypatch,
    capsys,
) -> None:
    broker_dsn = "postgresql://paper-broker-secret.example.invalid/db"
    broker_table = "paper_broker_secret_archive"
    ledger_dsn = "postgresql://paper-ledger-secret.example.invalid/db"
    ledger_table = "paper_ledger_secret_archive"
    _enable_broker_db(monkeypatch, dsn=broker_dsn, table_name=broker_table)
    _enable_ledger_db(monkeypatch, dsn=ledger_dsn, table_name=ledger_table)

    def broken_sink(**_kwargs: object) -> object:
        raise RuntimeError(
            f"broker={broker_dsn} broker_table={broker_table} "
            f"ledger={ledger_dsn} ledger_table={ledger_table} "
            "report_sha256=abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
        )

    exit_code = main(
        ["paper-autonomous-investment-ledger", "--persist"],
        paper_autonomous_investment_ledger_runner=lambda **_kwargs: _ledger_report(),
        paper_autonomous_investment_ledger_db_sink=broken_sink,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "broker=<redacted-dsn>" in captured.err
    assert "broker_table=<redacted-table>" in captured.err
    assert "ledger=<redacted-dsn>" in captured.err
    assert "ledger_table=<redacted-table>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    for secret in (
        broker_dsn,
        broker_table,
        ledger_dsn,
        ledger_table,
        "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
    ):
        assert secret not in captured.err


def test_load_paper_autonomous_investment_ledger_from_broker_db_uses_psycopg_loader_and_builder(
    monkeypatch,
) -> None:
    broker_records = (SimpleNamespace(generated_at=datetime(2026, 6, 25, tzinfo=UTC)),)
    report = _ledger_report(latest_generated_at=datetime(2026, 6, 25, tzinfo=UTC))
    loader_calls = []
    builder_calls = []

    def fake_loader(**kwargs: object) -> object:
        loader_calls.append(kwargs)
        return broker_records

    def fake_builder(**kwargs: object) -> object:
        builder_calls.append(kwargs)
        return report

    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_broker_psycopg."
        "load_paper_broker_execution_records_with_psycopg",
        fake_loader,
    )
    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_autonomous_investment_ledger."
        "build_paper_autonomous_investment_ledger_report",
        fake_builder,
    )

    actual = _load_paper_autonomous_investment_ledger_from_broker_db(
        broker_dsn="postgresql://paper-broker.example.invalid/db",
        broker_table_name="paper_broker_archive",
        limit=11,
        source_config_version="paper-broker-v0",
        execution_status="paper_held",
        source_gate_status="watch",
        max_latest_source_age_seconds=120,
        generated_at=datetime(2026, 6, 25, 12, 0, tzinfo=UTC),
    )

    assert actual is report
    assert loader_calls == [
        {
            "dsn": "postgresql://paper-broker.example.invalid/db",
            "table_name": "paper_broker_archive",
            "limit": 11,
            "config_version": "paper-broker-v0",
            "execution_status": "paper_held",
            "source_gate_status": "watch",
        },
    ]
    assert len(builder_calls) == 1
    assert builder_calls[0]["broker_execution_records"] == broker_records
    assert builder_calls[0]["generated_at"] == datetime(
        2026,
        6,
        25,
        12,
        0,
        tzinfo=UTC,
    )
    assert builder_calls[0]["config"].max_latest_source_age_seconds == 120


@pytest.mark.parametrize("limit", (0, -1, True, "1", 1.0))
def test_load_paper_autonomous_investment_ledger_from_broker_db_rejects_invalid_limit_before_load(
    monkeypatch,
    limit: object,
) -> None:
    loader_calls = 0

    def forbidden_loader(**_kwargs: object) -> object:
        nonlocal loader_calls
        loader_calls += 1
        raise AssertionError("loader should not run after invalid limit")

    monkeypatch.setattr(
        "polymarket_alpha_lab.paper_broker_psycopg."
        "load_paper_broker_execution_records_with_psycopg",
        forbidden_loader,
    )

    with pytest.raises(ValueError, match="limit must be positive"):
        _load_paper_autonomous_investment_ledger_from_broker_db(
            broker_dsn="postgresql://paper-broker.example.invalid/db",
            broker_table_name="paper_broker_archive",
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
    ),
)
def test_paper_autonomous_investment_ledger_cli_rejects_db_fast_live_auth_wallet_account_order_and_execution_flags(
    capsys,
    flag: str,
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["paper-autonomous-investment-ledger", flag, "value"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err
    assert flag in captured.err


def test_paper_autonomous_investment_ledger_summary_omits_entry_payload_and_account_fields(
    capsys,
) -> None:
    report = _ledger_report(
        entries=(
            SimpleNamespace(
                payload_json='{"market_slug":"secret-market"}',
                market_slug="secret-market",
                question="hidden question",
                account="account-secret",
                wallet="wallet-secret",
                order="order-secret",
                report_sha256=(
                    "abcdef0123456789abcdef0123456789"
                    "abcdef0123456789abcdef0123456789"
                ),
            ),
        ),
    )

    _print_paper_autonomous_investment_ledger_summary(report)

    captured = capsys.readouterr()
    assert "ledger_status=watch" in captured.out
    assert "source_record_count=3" in captured.out
    for secret in (
        "payload_json",
        "secret-market",
        "hidden question",
        "account-secret",
        "wallet-secret",
        "order-secret",
        "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
    ):
        assert secret not in captured.out
