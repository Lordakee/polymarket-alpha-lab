import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.paper_trade_cost_audit import PaperTradeCostAuditReport
from polymarket_alpha_lab.supabase_paper_trade_cost_audit_config import (
    PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR,
    PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR,
    PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR,
)


def _empty_cost_audit_report() -> PaperTradeCostAuditReport:
    return PaperTradeCostAuditReport(
        generated_at=datetime(2026, 6, 17, 10, 0, tzinfo=UTC),
        config_version="paper-trade-cost-audit-v0",
        trade_count=1,
        total_filled_size=Decimal("100"),
        total_requested_size=Decimal("100"),
        fill_rate=Decimal("1.000000"),
        mean_theoretical_edge=Decimal("0.060000"),
        mean_cost_adjusted_edge=Decimal("0.040000"),
        mean_edge_cost_drag=Decimal("0.020000"),
        total_edge_cost_drag=Decimal("2.000000"),
        mean_research_slippage=Decimal("0.004000"),
        mean_fill_slippage=Decimal("0.006000"),
        partial_fill_count=0,
        negative_cost_adjusted_edge_count=0,
        largest_single_trade_cost_drag=Decimal("2.000000"),
    )


def test_cost_audit_cli_ignores_db_env_without_persist_flag(
    monkeypatch,
    tmp_path,
    capsys,
):
    trade_log = tmp_path / "paper-trades.jsonl"
    trade_log.write_text("", encoding="utf-8")
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR, "not-a-bool")
    monkeypatch.setenv(
        PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR,
        "postgresql://cost-audit.example.invalid/ignored",
    )
    sink_calls = []

    def fake_cost_audit_runner(*, trade_records, config, generated_at):
        return _empty_cost_audit_report()

    def forbidden_cost_audit_sink(**kwargs):
        sink_calls.append(kwargs)
        raise AssertionError("paper trade cost audit DB sink should not run")

    exit_code = main(
        [
            "cost-audit",
            "--trade-log",
            str(trade_log),
        ],
        cost_audit_runner=fake_cost_audit_runner,
        paper_trade_cost_audit_db_sink=forbidden_cost_audit_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert sink_calls == []
    captured = capsys.readouterr()
    assert "cost-audit:" in captured.out
    assert "cost-audit failed:" not in captured.err
    assert "cost-audit.example.invalid" not in captured.out
    assert "cost-audit.example.invalid" not in captured.err


def test_cost_audit_cli_persists_report_when_requested(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://cost-audit.example.invalid/persist"
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR,
        "paper_trade_cost_audit_archive",
    )
    trade_log = tmp_path / "paper-trades.jsonl"
    trade_log.write_text("", encoding="utf-8")
    report = _empty_cost_audit_report()
    sink_calls = []

    def fake_cost_audit_runner(*, trade_records, config, generated_at):
        return report

    def fake_cost_audit_sink(*, dsn, report, table_name):
        sink_calls.append((dsn, report, table_name))
        return SimpleNamespace(report_sha256="a" * 64)

    exit_code = main(
        [
            "cost-audit",
            "--trade-log",
            str(trade_log),
            "--persist",
        ],
        cost_audit_runner=fake_cost_audit_runner,
        paper_trade_cost_audit_db_sink=fake_cost_audit_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert sink_calls == [
        (
            dsn,
            report,
            "paper_trade_cost_audit_archive",
        ),
    ]
    captured = capsys.readouterr()
    assert "cost-audit:" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "paper_trade_cost_audit_archive" not in captured.out


def test_cost_audit_cli_requires_db_config_before_persisting(
    monkeypatch,
    tmp_path,
    capsys,
):
    monkeypatch.delenv(PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR, raising=False)
    trade_log = tmp_path / "paper-trades.jsonl"
    trade_log.write_text("", encoding="utf-8")
    calls = []

    def forbidden_cost_audit_runner(*, trade_records, config, generated_at):
        calls.append(("runner", trade_records, config, generated_at))
        raise AssertionError("cost audit runner should not run")

    def forbidden_cost_audit_sink(**kwargs):
        calls.append(("sink", kwargs))
        raise AssertionError("paper trade cost audit DB sink should not run")

    exit_code = main(
        [
            "cost-audit",
            "--trade-log",
            str(trade_log),
            "--persist",
        ],
        cost_audit_runner=forbidden_cost_audit_runner,
        paper_trade_cost_audit_db_sink=forbidden_cost_audit_sink,
    )

    assert exit_code == 1
    assert calls == []
    captured = capsys.readouterr()
    assert "cost-audit failed:" in captured.err
    assert (
        "cost-audit persistence requires paper trade cost audit DB to be enabled"
        in captured.err
    )


def test_cost_audit_cli_redacts_dsn_on_persistence_failure(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://cost-audit-secret.example.invalid/persist"
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR, dsn)
    trade_log = tmp_path / "paper-trades.jsonl"
    trade_log.write_text("", encoding="utf-8")

    def fake_cost_audit_runner(*, trade_records, config, generated_at):
        return _empty_cost_audit_report()

    def broken_cost_audit_sink(*, dsn, report, table_name):
        raise RuntimeError(f"failed to persist to {dsn}")

    exit_code = main(
        [
            "cost-audit",
            "--trade-log",
            str(trade_log),
            "--persist",
        ],
        cost_audit_runner=fake_cost_audit_runner,
        paper_trade_cost_audit_db_sink=broken_cost_audit_sink,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "cost-audit failed: failed to persist to <redacted-dsn>" in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "cost-audit-secret" not in captured.out
    assert "cost-audit-secret" not in captured.err


def test_cost_audit_cli_default_psycopg_persist_path_no_network(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://cost-audit.example.invalid/persist"
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_COST_AUDIT_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        PAPER_TRADE_COST_AUDIT_DB_TABLE_ENV_VAR,
        "paper_trade_cost_audit_archive",
    )
    trade_log = tmp_path / "paper-trades.jsonl"
    trade_log.write_text("", encoding="utf-8")
    report = _empty_cost_audit_report()

    class FakeCursor:
        def __init__(self):
            self.calls = []
            self.closed = False

        def execute(self, sql, params=()):
            self.calls.append((" ".join(sql.split()), params))

        def close(self):
            self.closed = True

    class FakeConnection:
        def __init__(self):
            self.cursor_instance = FakeCursor()
            self.cursor_count = 0
            self.commit_count = 0
            self.rollback_count = 0
            self.close_count = 0

        def cursor(self):
            self.cursor_count += 1
            return self.cursor_instance

        def commit(self):
            self.commit_count += 1

        def rollback(self):
            self.rollback_count += 1

        def close(self):
            self.close_count += 1

    class FakeJsonb:
        def __init__(self, value):
            self.value = value

    connection = FakeConnection()
    connect_calls = []

    def fake_connect(connect_dsn):
        connect_calls.append(connect_dsn)
        if connect_dsn != dsn:
            raise AssertionError(f"unexpected dsn: {connect_dsn}")
        return connection

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setitem(
        sys.modules,
        "psycopg.types.json",
        SimpleNamespace(Jsonb=FakeJsonb),
    )

    exit_code = main(
        [
            "cost-audit",
            "--trade-log",
            str(trade_log),
            "--persist",
        ],
        cost_audit_runner=lambda **kwargs: report,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert connect_calls == [dsn]
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert "INSERT INTO paper_trade_cost_audit_archive" in sql
    assert len(params) == 20
    assert isinstance(params[16], FakeJsonb)
    assert params[16].value["config_version"] == "paper-trade-cost-audit-v0"
    captured = capsys.readouterr()
    assert "cost-audit:" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "paper_trade_cost_audit_archive" not in captured.out
