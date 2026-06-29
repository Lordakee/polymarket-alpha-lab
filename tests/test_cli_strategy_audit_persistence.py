import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.paper_trade_cost_audit import PaperTradeCostAuditReport
from polymarket_alpha_lab.positions import PaperNavLog, PaperNavSnapshot
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleLog, PaperStrategyCycleReport
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)
from polymarket_alpha_lab.supabase_strategy_risk_audit_config import (
    STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR,
    STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR,
    STRATEGY_RISK_AUDIT_DB_TABLE_ENV_VAR,
)


def _empty_nav_snapshot() -> PaperNavSnapshot:
    return PaperNavSnapshot(
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
        starting_cash=Decimal("10000"),
        cash_balance=Decimal("10000"),
        realized_pnl=Decimal("0"),
        exit_nav=Decimal("10000"),
        midpoint_nav=Decimal("10000"),
        total_cost_basis=Decimal("0"),
        unrealized_exit_pnl=Decimal("0"),
        marks=(),
    )


def _strategy_audit_report(
    status: str = "insufficient_evidence",
) -> PaperStrategyRiskAuditReport:
    statuses = {
        "audit_ready": ("pass", 6, 0, 0),
        "insufficient_evidence": ("incomplete", 0, 0, 6),
        "blocked_by_risk": ("fail", 0, 6, 0),
    }
    gate_status, pass_count, fail_count, incomplete_count = statuses[status]
    return PaperStrategyRiskAuditReport(
        generated_at=datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        config_version="strategy-risk-audit-v0",
        status=status,
        gate_count=6,
        pass_count=pass_count,
        fail_count=fail_count,
        incomplete_count=incomplete_count,
        gate_results=(
            PaperStrategyRiskAuditGateResult("paper_history", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("settlement_evidence", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("forecast_quality", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("cost_discipline", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("nav_drawdown", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("open_exposure", gate_status, "m"),
        ),
    )


def _write_strategy_audit_runner_inputs(tmp_path):
    cycle_log = tmp_path / "cycle.jsonl"
    trade_log = tmp_path / "trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    PaperStrategyCycleLog(cycle_log).append(
        PaperStrategyCycleReport(
            generated_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
            config_version="strategy-cycle-v1",
            scan_market_count=1,
            considered_count=0,
            snapshot_ready_count=0,
            cost_aware_report_count=0,
            blocked_counts=(),
            screening_report=None,
        )
    )
    trade_log.write_text("", encoding="utf-8")
    PaperNavLog(nav_log).append(_empty_nav_snapshot())
    return cycle_log, trade_log, nav_log


def _assert_real_cost_audit_report(
    value: PaperTradeCostAuditReport,
    *,
    trade_log,
) -> None:
    assert isinstance(value, PaperTradeCostAuditReport)
    assert value.config_version == "paper-trade-cost-audit-v0"
    assert value.trade_count == 0
    assert value.paper_only is True
    assert value.report_only is True
    assert trade_log.read_text(encoding="utf-8") == ""


def test_strategy_audit_cli_defaults_to_no_persist_without_flag(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://strategy-audit:secret@localhost:54322/db"
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        STRATEGY_RISK_AUDIT_DB_TABLE_ENV_VAR,
        "strategy_risk_audit_archive",
    )
    cycle_log, trade_log, nav_log = _write_strategy_audit_runner_inputs(tmp_path)
    report = _strategy_audit_report()
    runner_calls = []
    sink_calls = []

    def fake_strategy_audit_runner(
        *,
        cycle_log,
        trade_log,
        nav_log,
        outcome_log,
        cost_audit_report,
        config,
        generated_at,
    ):
        runner_calls.append(
            {
                "cycle_log": cycle_log,
                "trade_log": trade_log,
                "nav_log": nav_log,
                "outcome_log": outcome_log,
                "cost_audit_report": cost_audit_report,
                "config": config,
                "generated_at": generated_at,
            }
        )
        return report

    def forbidden_strategy_audit_sink(*, dsn, report, table_name):
        sink_calls.append((dsn, report, table_name))
        raise AssertionError("strategy audit DB sink should not run")

    exit_code = main(
        [
            "strategy-audit",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        strategy_risk_audit_db_sink=forbidden_strategy_audit_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    assert sink_calls == []
    call = runner_calls[0]
    assert call["cycle_log"] == cycle_log
    assert call["trade_log"] == trade_log
    assert call["nav_log"] == nav_log
    assert call["outcome_log"] is None
    _assert_real_cost_audit_report(call["cost_audit_report"], trade_log=trade_log)
    assert call["config"].config_version == "strategy-risk-audit-v0"
    assert isinstance(call["generated_at"], datetime)
    captured = capsys.readouterr()
    assert "strategy-audit:" in captured.out
    assert "persisted=False" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "strategy_risk_audit_archive" not in captured.out


def test_strategy_audit_cli_persists_report_when_requested(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://strategy-audit:secret@localhost:54322/db"
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        STRATEGY_RISK_AUDIT_DB_TABLE_ENV_VAR,
        "strategy_risk_audit_archive",
    )
    cycle_log, trade_log, nav_log = _write_strategy_audit_runner_inputs(tmp_path)
    report = _strategy_audit_report()
    runner_calls = []
    sink_calls = []

    def fake_strategy_audit_runner(
        *,
        cycle_log,
        trade_log,
        nav_log,
        outcome_log,
        cost_audit_report,
        config,
        generated_at,
    ):
        runner_calls.append(cost_audit_report)
        return report

    def fake_strategy_audit_sink(*, dsn, report, table_name):
        sink_calls.append((dsn, report, table_name))
        return SimpleNamespace(report_sha256="a" * 64)

    exit_code = main(
        [
            "strategy-audit",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
            "--persist",
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        strategy_risk_audit_db_sink=fake_strategy_audit_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    _assert_real_cost_audit_report(runner_calls[0], trade_log=trade_log)
    assert sink_calls == [
        (
            dsn,
            report,
            "strategy_risk_audit_archive",
        ),
    ]
    captured = capsys.readouterr()
    assert "strategy-audit:" in captured.out
    assert "persisted=True" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "strategy_risk_audit_archive" not in captured.out

def test_strategy_audit_cli_requires_db_config_before_persisting(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://strategy-audit:secret@localhost:54322/db"
    monkeypatch.delenv(STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR, dsn)
    monkeypatch.delenv(STRATEGY_RISK_AUDIT_DB_TABLE_ENV_VAR, raising=False)
    cycle_log, trade_log, nav_log = _write_strategy_audit_runner_inputs(tmp_path)
    calls = []

    def forbidden_strategy_audit_runner(**kwargs):
        calls.append(("runner", kwargs))
        raise AssertionError("strategy audit runner should not run")

    def forbidden_strategy_audit_sink(**kwargs):
        calls.append(("sink", kwargs))
        raise AssertionError("strategy audit DB sink should not run")

    exit_code = main(
        [
            "strategy-audit",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
            "--persist",
        ],
        strategy_audit_runner=forbidden_strategy_audit_runner,
        strategy_risk_audit_db_sink=forbidden_strategy_audit_sink,
    )

    assert exit_code == 1
    assert calls == []
    captured = capsys.readouterr()
    assert "strategy-audit failed:" in captured.err
    assert "persistence requires strategy risk audit DB to be enabled" in captured.err
    assert dsn not in captured.out
    assert dsn not in captured.err


def test_strategy_audit_cli_redacts_dsn_on_persistence_failure(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://strategy-audit:secret@localhost:54322/db"
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR, dsn)
    cycle_log, trade_log, nav_log = _write_strategy_audit_runner_inputs(tmp_path)

    def fake_strategy_audit_runner(**kwargs):
        _assert_real_cost_audit_report(
            kwargs["cost_audit_report"],
            trade_log=trade_log,
        )
        return _strategy_audit_report()

    def broken_strategy_audit_sink(*, dsn, report, table_name):
        raise RuntimeError(f"failed to persist to {dsn}")

    exit_code = main(
        [
            "strategy-audit",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
            "--persist",
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        strategy_risk_audit_db_sink=broken_strategy_audit_sink,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "strategy-audit failed: failed to persist to <redacted-dsn>" in (
        captured.err
    )
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "localhost:54322" not in captured.out
    assert "localhost:54322" not in captured.err


def test_strategy_audit_cli_default_psycopg_persist_path_no_network(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://strategy-audit:secret@localhost:54322/db"
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(STRATEGY_RISK_AUDIT_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        STRATEGY_RISK_AUDIT_DB_TABLE_ENV_VAR,
        "strategy_risk_audit_archive",
    )
    cycle_log, trade_log, nav_log = _write_strategy_audit_runner_inputs(tmp_path)
    report = _strategy_audit_report()
    runner_calls = []

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

    def fake_strategy_audit_runner(**kwargs):
        runner_calls.append(kwargs["cost_audit_report"])
        return report

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
    sys.modules.pop("polymarket_alpha_lab.strategy_risk_audit_psycopg", None)

    exit_code = main(
        [
            "strategy-audit",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
            "--persist",
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    _assert_real_cost_audit_report(runner_calls[0], trade_log=trade_log)
    assert connect_calls == [dsn]
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert "INSERT INTO strategy_risk_audit_archive" in sql
    assert len(params) == 13
    assert params[2] == "strategy-risk-audit-v0"
    assert params[3] == "insufficient_evidence"
    assert isinstance(params[8], FakeJsonb)
    assert isinstance(params[9], FakeJsonb)
    captured = capsys.readouterr()
    assert "strategy-audit:" in captured.out
    assert "persisted=True" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "strategy_risk_audit_archive" not in captured.out
