import json
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    PaperForecastEvidenceReport,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.outcome_tracker import (
    OutcomeTrackingConfig,
    OutcomeTrackingLog,
    OutcomeTrackingReport,
)
from polymarket_alpha_lab.nav_risk_metrics import (
    PaperNavRiskMetricsConfig,
    PaperNavRiskMetricsReport,
)
from polymarket_alpha_lab.paper_trade_cost_audit import (
    PaperTradeCostAuditConfig,
    PaperTradeCostAuditReport,
)
from polymarket_alpha_lab.performance_summary import (
    PerformanceSummary,
    PerformanceSummaryConfig,
)
from polymarket_alpha_lab.positions import PaperNavLog, PaperNavSnapshot
from polymarket_alpha_lab.runner import RunLoopSummary
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleLog
from polymarket_alpha_lab.strategy_audit_history import (
    PaperStrategyRiskAuditHistoryConfig,
    build_paper_strategy_risk_audit_history_report,
)
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)
from polymarket_alpha_lab.strategy_risk_audit_log import PaperStrategyRiskAuditLog


def test_scan_cli_builds_read_only_scan_config(tmp_path):
    calls = []

    def fake_client_factory():
        return "fake-client"

    def fake_runner(*, client, config):
        calls.append((client, config))
        return []

    output_path = tmp_path / "scores.json"
    archive_root = tmp_path / "raw"

    exit_code = main(
        [
            "scan",
            "--limit",
            "3",
            "--archive-root",
            str(archive_root),
            "--output",
            str(output_path),
            "--no-books",
        ],
        runner=fake_runner,
        client_factory=fake_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    client, config = calls[0]
    assert client == "fake-client"
    assert config.limit == 3
    assert config.archive_root == archive_root
    assert config.output_path == output_path
    assert config.fetch_books is False


def test_scan_cli_returns_one_when_runner_fails(tmp_path):
    def broken_runner(*, client, config):
        raise RuntimeError("scan failed")

    exit_code = main(
        [
            "scan",
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "scores.json"),
        ],
        runner=broken_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1


def test_strategy_cycle_cli_builds_read_only_cycle_config(tmp_path, capsys):
    calls = []

    def fake_client_factory():
        return "fake-client"

    def fake_cycle_runner(*, client, scan_config, cycle_config):
        calls.append((client, scan_config, cycle_config))
        # Naive forecast: every considered market is blocked (no snapshot_ready),
        # so screening_report must be None per the report invariants.
        return PaperStrategyCycleReport(
            generated_at=datetime.now(UTC),
            config_version="strategy-cycle-v1",
            scan_market_count=10,
            considered_count=5,
            snapshot_ready_count=0,
            cost_aware_report_count=0,
            blocked_counts=(("blocked_fetch_error", 5),),
            screening_report=None,
        )

    output_path = tmp_path / "strategy-cycle.jsonl"
    archive_root = tmp_path / "raw"

    exit_code = main(
        [
            "strategy-cycle",
            "--limit",
            "5",
            "--max-markets",
            "3",
            "--no-prefilter",
            "--archive-root",
            str(archive_root),
            "--output",
            str(output_path),
        ],
        cycle_runner=fake_cycle_runner,
        client_factory=fake_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    client, scan_config, cycle_config = calls[0]
    assert client == "fake-client"
    assert scan_config.limit == 5
    assert scan_config.archive_root == archive_root
    assert scan_config.output_path == output_path
    assert scan_config.fetch_books is True
    assert cycle_config.max_markets_per_cycle == 3
    assert cycle_config.prefilter_by_score is False
    assert cycle_config.config_version == "strategy-cycle-v1"

    captured = capsys.readouterr()
    assert "scanned=10" in captured.out
    assert "considered=5" in captured.out
    assert "snapshot_ready=0" in captured.out
    assert "blocked_fetch_error=5" in captured.out

    # The JSONL report log is appended and must be valid.
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").strip().endswith("}")


def test_strategy_cycle_cli_returns_one_when_cycle_runner_fails(tmp_path):
    def broken_cycle_runner(*, client, scan_config, cycle_config):
        raise RuntimeError("cycle failed")

    exit_code = main(
        [
            "strategy-cycle",
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        cycle_runner=broken_cycle_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1


def test_strategy_cycle_cli_paper_execute_flag_enables_inline_paper_pass(tmp_path):
    calls = []

    def fake_client_factory():
        return "fake-client"

    def fake_cycle_runner(*, client, scan_config, cycle_config):
        calls.append(cycle_config)
        return PaperStrategyCycleReport(
            generated_at=datetime.now(UTC),
            config_version="strategy-cycle-v1",
            scan_market_count=0,
            considered_count=0,
            snapshot_ready_count=0,
            cost_aware_report_count=0,
            blocked_counts=(),
            screening_report=None,
        )

    journal_path = tmp_path / "paper-trades.jsonl"

    exit_code = main(
        [
            "strategy-cycle",
            "--paper-execute",
            "--paper-journal",
            str(journal_path),
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        cycle_runner=fake_cycle_runner,
        client_factory=fake_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    cycle_config = calls[0]
    assert cycle_config.paper_execution_config is not None
    assert cycle_config.paper_execution_config.config_version == "paper-execution-v1"
    assert cycle_config.paper_trade_journal_path == journal_path


def test_strategy_cycle_cli_default_omits_paper_execute(tmp_path):
    calls = []

    def fake_cycle_runner(*, client, scan_config, cycle_config):
        calls.append(cycle_config)
        return PaperStrategyCycleReport(
            generated_at=datetime.now(UTC),
            config_version="strategy-cycle-v1",
            scan_market_count=0,
            considered_count=0,
            snapshot_ready_count=0,
            cost_aware_report_count=0,
            blocked_counts=(),
            screening_report=None,
        )

    exit_code = main(
        [
            "strategy-cycle",
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        cycle_runner=fake_cycle_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    cycle_config = calls[0]
    assert cycle_config.paper_execution_config is None
    assert cycle_config.paper_trade_journal_path is None


def test_strategy_cycle_cli_forecast_provider_llm_wires_transport(tmp_path):
    calls = []

    def fake_cycle_runner(*, client, scan_config, cycle_config):
        calls.append(cycle_config)
        return PaperStrategyCycleReport(
            generated_at=datetime.now(UTC),
            config_version="strategy-cycle-v1",
            scan_market_count=0,
            considered_count=0,
            snapshot_ready_count=0,
            cost_aware_report_count=0,
            blocked_counts=(),
            screening_report=None,
        )

    exit_code = main(
        [
            "strategy-cycle",
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
            "--forecast-provider",
            "llm",
            "--llm-api-token",
            "caller-supplied-token",
        ],
        cycle_runner=fake_cycle_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    cycle_config = calls[0]
    assert cycle_config.forecast_provider == "llm"
    assert cycle_config.llm_transport is not None
    assert cycle_config.llm_transport.api_token == "caller-supplied-token"
    assert cycle_config.llm_forecast_config is not None


def test_strategy_cycle_cli_default_forecast_provider_is_naive(tmp_path):
    calls = []

    def fake_cycle_runner(*, client, scan_config, cycle_config):
        calls.append(cycle_config)
        return PaperStrategyCycleReport(
            generated_at=datetime.now(UTC),
            config_version="strategy-cycle-v1",
            scan_market_count=0,
            considered_count=0,
            snapshot_ready_count=0,
            cost_aware_report_count=0,
            blocked_counts=(),
            screening_report=None,
        )

    exit_code = main(
        [
            "strategy-cycle",
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        cycle_runner=fake_cycle_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert calls[0].forecast_provider == "naive"
    assert calls[0].llm_transport is None


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


def test_portfolio_nav_cli_builds_nav_call_and_prints_summary(tmp_path, capsys):
    calls = []

    def fake_client_factory():
        return "fake-client"

    def fake_nav_runner(*, journal_path, starting_cash, client, marked_at, nav_log_path):
        calls.append(
            {
                "journal_path": journal_path,
                "starting_cash": starting_cash,
                "client": client,
                "marked_at": marked_at,
                "nav_log_path": nav_log_path,
            }
        )
        return _empty_nav_snapshot()

    journal_path = tmp_path / "paper-trades.jsonl"
    nav_log_path = tmp_path / "nav.jsonl"

    exit_code = main(
        [
            "portfolio-nav",
            "--journal",
            str(journal_path),
            "--starting-cash",
            "10000",
            "--nav-log",
            str(nav_log_path),
        ],
        nav_runner=fake_nav_runner,
        client_factory=fake_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    call = calls[0]
    assert call["journal_path"] == journal_path
    assert call["starting_cash"] == Decimal("10000")
    assert call["client"] == "fake-client"
    assert call["nav_log_path"] == nav_log_path
    assert isinstance(call["marked_at"], datetime)

    captured = capsys.readouterr()
    assert "portfolio-nav:" in captured.out
    assert "starting_cash=10000" in captured.out
    assert "exit_nav=10000" in captured.out
    assert "position_count=0" in captured.out


def test_portfolio_nav_cli_defaults_nav_log_to_none(tmp_path):
    calls = []

    def fake_nav_runner(*, journal_path, starting_cash, client, marked_at, nav_log_path):
        calls.append(nav_log_path)
        return _empty_nav_snapshot()

    exit_code = main(
        [
            "portfolio-nav",
            "--journal",
            str(tmp_path / "paper-trades.jsonl"),
            "--starting-cash",
            "10000",
        ],
        nav_runner=fake_nav_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert calls == [None]


def test_portfolio_nav_cli_returns_one_when_nav_runner_fails(tmp_path, capsys):
    def broken_nav_runner(*, journal_path, starting_cash, client, marked_at, nav_log_path):
        raise RuntimeError("nav failed")

    exit_code = main(
        [
            "portfolio-nav",
            "--journal",
            str(tmp_path / "paper-trades.jsonl"),
            "--starting-cash",
            "10000",
        ],
        nav_runner=broken_nav_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "portfolio-nav failed: nav failed" in captured.err


def _empty_summary() -> PerformanceSummary:
    return PerformanceSummary(
        generated_at=datetime(2026, 6, 16, tzinfo=UTC),
        config_version="performance-summary-v1",
        cycle_count=2,
        total_scan_market_count=18,
        total_snapshot_ready_count=5,
        total_cost_aware_report_count=5,
        paper_trade_count=3,
        last_exit_nav=Decimal("10050"),
        last_starting_cash=Decimal("10025"),
        total_realized_pnl=Decimal("25"),
        nav_snapshot_count=2,
        first_cycle_at=datetime(2026, 6, 14, tzinfo=UTC),
        last_cycle_at=datetime(2026, 6, 15, tzinfo=UTC),
    )


def test_history_cli_reads_logs_and_prints_summary(tmp_path, capsys):
    calls = []

    def fake_history_runner(*, cycle_log, trade_log, nav_log, config, generated_at):
        calls.append(
            {
                "cycle_log": cycle_log,
                "trade_log": trade_log,
                "nav_log": nav_log,
                "config": config,
                "generated_at": generated_at,
            }
        )
        return _empty_summary()

    cycle_log = tmp_path / "cycle.jsonl"
    trade_log = tmp_path / "trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"

    exit_code = main(
        [
            "history",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
        ],
        history_runner=fake_history_runner,
    )

    assert exit_code == 0
    assert len(calls) == 1
    call = calls[0]
    assert call["cycle_log"] == cycle_log
    assert call["trade_log"] == trade_log
    assert call["nav_log"] == nav_log
    assert isinstance(call["config"], PerformanceSummaryConfig)
    assert call["config"].config_version == "performance-summary-v1"
    assert isinstance(call["generated_at"], datetime)

    captured = capsys.readouterr()
    assert "history:" in captured.out
    assert "cycles=2" in captured.out
    assert "markets_scanned=18" in captured.out
    assert "paper_trades=3" in captured.out
    assert "last_exit_nav=10050" in captured.out
    assert "total_realized_pnl=25" in captured.out


def test_history_cli_returns_one_when_history_runner_fails(tmp_path, capsys):
    def broken_history_runner(*, cycle_log, trade_log, nav_log, config, generated_at):
        raise RuntimeError("history failed")

    exit_code = main(
        [
            "history",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
            "--trade-log",
            str(tmp_path / "trades.jsonl"),
            "--nav-log",
            str(tmp_path / "nav.jsonl"),
        ],
        history_runner=broken_history_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "history failed: history failed" in captured.err


def _empty_nav_risk_report() -> PaperNavRiskMetricsReport:
    return PaperNavRiskMetricsReport(
        generated_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
        config_version="nav-risk-metrics-v0",
        nav_snapshot_count=1,
        first_marked_at=datetime(2026, 6, 14, tzinfo=UTC),
        last_marked_at=datetime(2026, 6, 14, tzinfo=UTC),
        latest_exit_nav=Decimal("10000"),
        latest_starting_cash=Decimal("10000"),
        latest_cash_balance=Decimal("10000"),
        latest_total_cost_basis=Decimal("0"),
        latest_unrealized_exit_pnl=Decimal("0"),
        peak_exit_nav=Decimal("10000"),
        trough_exit_nav=Decimal("10000"),
        cumulative_return=Decimal("0.000000"),
        max_drawdown=Decimal("0"),
        max_drawdown_pct=Decimal("0.000000"),
        worst_nav_delta=None,
        nav_return_volatility=None,
        pending_notional=Decimal("0"),
        open_position_count=0,
        fully_executable_count=0,
        partially_executable_count=0,
        no_exit_depth_count=0,
        largest_market_exposure_value=None,
        largest_market_exposure_share=None,
        exposure_rows=(),
    )


def _forecast_observation(index: int) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=datetime(2026, 6, 16, 12, index, tzinfo=UTC),
        source_packet_id=f"pkt-{index}",
        condition_id=f"0x{index:04x}",
        token_id=f"{index}",
        market_slug=f"m-{index}",
        strategy_type="market_quality",
        risk_tags=("liquidity",),
        predicted_probability=Decimal("0.60"),
        actual_outcome_value=Decimal("1"),
    )


def _resolved_outcome_report(observation_count: int = 10) -> OutcomeTrackingReport:
    observations = tuple(
        _forecast_observation(index) for index in range(observation_count)
    )
    evidence = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="outcome-tracker-v1",
            min_probability_observations=observation_count,
            min_edge_observations=0,
            max_mean_probability_loss=Decimal("0.3000"),
            max_bucket_error=Decimal("0.5000"),
        ),
        generated_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
    )
    return OutcomeTrackingReport(
        generated_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
        config_version="outcome-tracker-v1",
        total_markets_checked=observation_count,
        resolved_count=observation_count,
        pending_count=0,
        observations=observations,
        forecast_evidence_report=evidence,
    )


def _write_strategy_audit_inputs(tmp_path, outcome_report: OutcomeTrackingReport):
    cycle_log = tmp_path / "cycle.jsonl"
    trade_log = tmp_path / "trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    outcome_log = tmp_path / "outcomes.jsonl"
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
    trade_log.touch()
    PaperNavLog(nav_log).append(_empty_nav_snapshot())
    OutcomeTrackingLog(outcome_log).append(outcome_report)
    return cycle_log, trade_log, nav_log, outcome_log


def test_strategy_audit_cli_reads_local_logs_outcome_log_and_does_not_construct_client(
    tmp_path,
    capsys,
):
    cycle_log, trade_log, nav_log, outcome_log = _write_strategy_audit_inputs(
        tmp_path,
        _resolved_outcome_report(),
    )

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "strategy-audit",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
            "--outcome-log",
            str(outcome_log),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "strategy-audit:" in captured.out
    assert "status=insufficient_evidence" in captured.out
    assert "gates=6" in captured.out
    assert "pass=4" in captured.out
    assert "fail=0" in captured.out
    assert "incomplete=2" in captured.out
    assert "paper_history: status=incomplete" in captured.out
    assert "settlement_evidence: status=pass" in captured.out
    assert "forecast_quality: status=pass" in captured.out
    assert "cost_discipline: status=incomplete" in captured.out
    assert "nav_drawdown: status=pass" in captured.out
    assert "open_exposure: status=pass" in captured.out


def test_strategy_audit_cli_appends_strategy_audit_log_without_client(
    tmp_path,
    capsys,
):
    cycle_log, trade_log, nav_log, outcome_log = _write_strategy_audit_inputs(
        tmp_path,
        _resolved_outcome_report(),
    )
    audit_log = tmp_path / "strategy-audits.jsonl"

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "strategy-audit",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
            "--outcome-log",
            str(outcome_log),
            "--strategy-audit-log",
            str(audit_log),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    reports = PaperStrategyRiskAuditLog.read(audit_log)
    assert len(reports) == 1
    assert reports[0].gate_count == 6
    assert reports[0].status == "insufficient_evidence"
    captured = capsys.readouterr()
    assert "strategy-audit:" in captured.out


def test_strategy_audit_cli_without_outcome_log_marks_outcome_gates_incomplete(
    tmp_path,
    capsys,
):
    cycle_log, trade_log, nav_log, _outcome_log = _write_strategy_audit_inputs(
        tmp_path,
        _resolved_outcome_report(),
    )

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
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "strategy-audit:" in captured.out
    assert "settlement_evidence: status=incomplete" in captured.out
    assert "forecast_quality: status=incomplete" in captured.out


def test_strategy_audit_cli_passes_local_cost_audit_report_to_runner(tmp_path):
    calls = []

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
        calls.append(
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
        return PaperStrategyRiskAuditReport(
            generated_at=generated_at,
            config_version=config.config_version,
            status="insufficient_evidence",
            gate_count=6,
            pass_count=0,
            fail_count=0,
            incomplete_count=6,
            gate_results=(
                PaperStrategyRiskAuditGateResult(
                    gate_name="paper_history",
                    status="incomplete",
                    message="incomplete",
                ),
                PaperStrategyRiskAuditGateResult(
                    gate_name="settlement_evidence",
                    status="incomplete",
                    message="incomplete",
                ),
                PaperStrategyRiskAuditGateResult(
                    gate_name="forecast_quality",
                    status="incomplete",
                    message="incomplete",
                ),
                PaperStrategyRiskAuditGateResult(
                    gate_name="cost_discipline",
                    status="incomplete",
                    message="incomplete",
                ),
                PaperStrategyRiskAuditGateResult(
                    gate_name="nav_drawdown",
                    status="incomplete",
                    message="incomplete",
                ),
                PaperStrategyRiskAuditGateResult(
                    gate_name="open_exposure",
                    status="incomplete",
                    message="incomplete",
                ),
            ),
        )

    cycle_log = tmp_path / "cycle.jsonl"
    trade_log = tmp_path / "trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    trade_log.write_text("", encoding="utf-8")

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
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    call = calls[0]
    assert call["cycle_log"] == cycle_log
    assert call["trade_log"] == trade_log
    assert call["nav_log"] == nav_log
    assert call["outcome_log"] is None
    assert isinstance(call["cost_audit_report"], PaperTradeCostAuditReport)
    assert call["cost_audit_report"].config_version == "paper-trade-cost-audit-v0"
    assert call["cost_audit_report"].trade_count == 0
    assert call["cost_audit_report"].paper_only is True
    assert call["cost_audit_report"].report_only is True
    assert call["config"].config_version == "strategy-risk-audit-v0"
    assert isinstance(call["generated_at"], datetime)


def test_strategy_audit_cli_returns_one_when_runner_fails(tmp_path, capsys):
    trade_log = tmp_path / "trades.jsonl"
    trade_log.write_text("", encoding="utf-8")

    def broken_strategy_audit_runner(
        *,
        cycle_log,
        trade_log,
        nav_log,
        outcome_log,
        cost_audit_report,
        config,
        generated_at,
    ):
        raise RuntimeError("audit failed")

    exit_code = main(
        [
            "strategy-audit",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(tmp_path / "nav.jsonl"),
        ],
        strategy_audit_runner=broken_strategy_audit_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "strategy-audit failed: audit failed" in captured.err


def test_strategy_audit_history_cli_reads_audit_log_and_prints_summary_without_client(
    tmp_path,
    capsys,
):
    audit_log = tmp_path / "strategy-audits.jsonl"
    PaperStrategyRiskAuditLog(audit_log).append(_strategy_audit_report("audit_ready"))
    PaperStrategyRiskAuditLog(audit_log).append(
        _strategy_audit_report("blocked_by_risk"),
    )
    before = audit_log.read_text(encoding="utf-8")

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "strategy-audit-history",
            "--strategy-audit-log",
            str(audit_log),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert audit_log.read_text(encoding="utf-8") == before
    captured = capsys.readouterr()
    assert "strategy-audit-history:" in captured.out
    assert "reports=2" in captured.out
    assert "status=latest_blocked_by_risk" in captured.out
    assert "latest_status=blocked_by_risk" in captured.out
    assert "audit_ready=1" in captured.out
    assert "insufficient_evidence=0" in captured.out
    assert "blocked_by_risk=1" in captured.out
    assert "first=2026-06-17T12:00:00+00:00" in captured.out
    assert "latest=2026-06-17T12:00:00+00:00" in captured.out
    assert "latest_failed_gates=paper_history,settlement_evidence" in captured.out
    assert "paper_history: pass=1 fail=1 incomplete=0" in captured.out


def test_strategy_audit_history_cli_passes_typed_reports_to_runner(tmp_path):
    audit_log = tmp_path / "strategy-audits.jsonl"
    first = _strategy_audit_report("audit_ready")
    second = _strategy_audit_report("insufficient_evidence")
    PaperStrategyRiskAuditLog(audit_log).append(first)
    PaperStrategyRiskAuditLog(audit_log).append(second)
    calls = []

    def fake_strategy_audit_history_runner(*, reports, config, generated_at):
        calls.append(
            {
                "reports": reports,
                "config": config,
                "generated_at": generated_at,
            }
        )
        return build_paper_strategy_risk_audit_history_report(
            reports,
            config=config,
            generated_at=generated_at,
        )

    exit_code = main(
        [
            "strategy-audit-history",
            "--strategy-audit-log",
            str(audit_log),
        ],
        strategy_audit_history_runner=fake_strategy_audit_history_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["reports"] == (first, second)
    assert isinstance(calls[0]["config"], PaperStrategyRiskAuditHistoryConfig)
    assert calls[0]["config"].config_version == "strategy-audit-history-v0"
    assert isinstance(calls[0]["generated_at"], datetime)


def test_strategy_audit_history_cli_empty_log_prints_zero_summary_without_client(
    tmp_path,
    capsys,
):
    audit_log = tmp_path / "strategy-audits.jsonl"
    audit_log.write_text("", encoding="utf-8")
    before = audit_log.read_bytes()

    exit_code = main(
        [
            "strategy-audit-history",
            "--strategy-audit-log",
            str(audit_log),
        ],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert audit_log.read_bytes() == before
    captured = capsys.readouterr()
    assert "strategy-audit-history:" in captured.out
    assert "reports=0" in captured.out
    assert "status=empty_audit_history" in captured.out
    assert "latest_status=none" in captured.out
    assert "first=none" in captured.out
    assert "latest=none" in captured.out


def test_strategy_audit_history_cli_empty_log_passes_empty_reports_to_runner_without_mutation(
    tmp_path,
):
    audit_log = tmp_path / "strategy-audits.jsonl"
    audit_log.write_text("", encoding="utf-8")
    before = audit_log.read_bytes()
    calls = []

    def fake_strategy_audit_history_runner(*, reports, config, generated_at):
        calls.append(
            {
                "reports": reports,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return build_paper_strategy_risk_audit_history_report(
            reports,
            config=config,
            generated_at=generated_at,
        )

    exit_code = main(
        [
            "strategy-audit-history",
            "--strategy-audit-log",
            str(audit_log),
        ],
        strategy_audit_history_runner=fake_strategy_audit_history_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["reports"] == ()
    assert isinstance(calls[0]["config"], PaperStrategyRiskAuditHistoryConfig)
    assert calls[0]["config"].config_version == "strategy-audit-history-v0"
    assert isinstance(calls[0]["generated_at"], datetime)
    assert audit_log.read_bytes() == before


def test_strategy_audit_history_cli_returns_one_when_runner_fails(tmp_path, capsys):
    audit_log = tmp_path / "strategy-audits.jsonl"
    PaperStrategyRiskAuditLog(audit_log).append(_strategy_audit_report("audit_ready"))
    before = audit_log.read_bytes()

    def broken_strategy_audit_history_runner(**kwargs):
        raise RuntimeError("history summary failed")

    exit_code = main(
        [
            "strategy-audit-history",
            "--strategy-audit-log",
            str(audit_log),
        ],
        strategy_audit_history_runner=broken_strategy_audit_history_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    assert audit_log.read_bytes() == before
    captured = capsys.readouterr()
    assert "strategy-audit-history failed: history summary failed" in captured.err


def test_strategy_audit_history_cli_missing_log_returns_one_without_client(
    tmp_path,
    capsys,
):
    audit_log = tmp_path / "missing-strategy-audits.jsonl"
    assert not audit_log.exists()

    exit_code = main(
        [
            "strategy-audit-history",
            "--strategy-audit-log",
            str(audit_log),
        ],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    assert not audit_log.exists()
    captured = capsys.readouterr()
    assert "strategy-audit-history failed:" in captured.err
    assert "missing-strategy-audits.jsonl" in captured.err


def _strategy_evidence_stub_report(
    *,
    status: str = "local_evidence_observed",
    evidence_gap_names: tuple[str, ...] = (),
    outcome_checked_count: int | None = 10,
    outcome_resolved_count: int | None = 8,
    outcome_pending_count: int | None = 2,
    audit_report_count: int | None = 1,
    latest_audit_status: str | None = "audit_ready",
    negative_cost_adjusted_edge_count: int = 3,
    unexecutable_open_position_count: int = 4,
) -> SimpleNamespace:
    return SimpleNamespace(
        status=status,
        evidence_gap_names=evidence_gap_names,
        cycle_count=1,
        paper_trade_count=0,
        nav_snapshot_count=1,
        outcome_checked_count=outcome_checked_count,
        outcome_resolved_count=outcome_resolved_count,
        outcome_pending_count=outcome_pending_count,
        audit_report_count=audit_report_count,
        latest_audit_status=latest_audit_status,
        negative_cost_adjusted_edge_count=negative_cost_adjusted_edge_count,
        unexecutable_open_position_count=unexecutable_open_position_count,
        paper_only=True,
        report_only=True,
    )


def test_strategy_evidence_cli_reads_local_logs_and_prints_summary_without_client(
    tmp_path,
    capsys,
):
    cycle_log = tmp_path / "cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    cycle_log.write_text("", encoding="utf-8")
    trade_log.write_text("", encoding="utf-8")
    nav_log.write_text("", encoding="utf-8")
    before = {
        cycle_log: cycle_log.read_bytes(),
        trade_log: trade_log.read_bytes(),
        nav_log: nav_log.read_bytes(),
    }
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "strategy-evidence",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert {path: path.read_bytes() for path in before} == before
    captured = capsys.readouterr()
    assert "strategy-evidence:" in captured.out
    assert "status=no_local_evidence" in captured.out
    assert "missing_cycles" in captured.out
    assert "missing_paper_trades" in captured.out
    assert "missing_nav_snapshots" in captured.out


def test_strategy_evidence_cli_passes_typed_local_reports_to_runner_without_client(
    tmp_path,
    capsys,
):
    cycle_log, trade_log, nav_log, outcome_log = _write_strategy_audit_inputs(
        tmp_path,
        _resolved_outcome_report(),
    )
    audit_log = tmp_path / "strategy-audits.jsonl"
    PaperStrategyRiskAuditLog(audit_log).append(_strategy_audit_report("audit_ready"))
    before = {
        cycle_log: cycle_log.read_bytes(),
        trade_log: trade_log.read_bytes(),
        nav_log: nav_log.read_bytes(),
        outcome_log: outcome_log.read_bytes(),
        audit_log: audit_log.read_bytes(),
    }
    calls = []
    client_factory_calls = 0

    def fake_strategy_evidence_runner(
        *,
        performance_summary,
        nav_risk_report,
        cost_audit_report,
        outcome_report,
        audit_history_report,
        config,
        generated_at,
    ):
        calls.append(
            {
                "performance_summary": performance_summary,
                "nav_risk_report": nav_risk_report,
                "cost_audit_report": cost_audit_report,
                "outcome_report": outcome_report,
                "audit_history_report": audit_history_report,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return _strategy_evidence_stub_report(
            status="local_evidence_observed",
            evidence_gap_names=(),
        )

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "strategy-evidence",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
            "--outcome-log",
            str(outcome_log),
            "--strategy-audit-log",
            str(audit_log),
        ],
        strategy_evidence_runner=fake_strategy_evidence_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert len(calls) == 1
    call = calls[0]
    assert isinstance(call["performance_summary"], PerformanceSummary)
    assert call["performance_summary"].cycle_count == 1
    assert call["performance_summary"].nav_snapshot_count == 1
    assert isinstance(call["nav_risk_report"], PaperNavRiskMetricsReport)
    assert call["nav_risk_report"].nav_snapshot_count == 1
    assert isinstance(call["cost_audit_report"], PaperTradeCostAuditReport)
    assert call["cost_audit_report"].trade_count == 0
    assert isinstance(call["outcome_report"], OutcomeTrackingReport)
    assert call["outcome_report"].resolved_count == 10
    assert call["audit_history_report"].audit_report_count == 1
    assert call["audit_history_report"].latest_audit_status == "audit_ready"
    assert call["config"].__class__.__name__ == "PaperStrategyEvidenceSnapshotConfig"
    assert call["config"].config_version == "strategy-evidence-snapshot-v0"
    assert isinstance(call["generated_at"], datetime)
    assert {path: path.read_bytes() for path in before} == before
    captured = capsys.readouterr()
    assert "strategy-evidence:" in captured.out
    assert "status=local_evidence_observed" in captured.out
    assert "gaps=none" in captured.out
    assert "cycles=1" in captured.out
    assert "nav_snapshots=1" in captured.out
    assert "outcome_checked=10" in captured.out
    assert "outcome_resolved=8" in captured.out
    assert "outcome_pending=2" in captured.out
    assert "strategy_audits=1" in captured.out
    assert "latest_audit_status=audit_ready" in captured.out
    assert "negative_cost_adjusted_edge=3" in captured.out
    assert "unexecutable_open_positions=4" in captured.out


def test_strategy_evidence_cli_without_optional_logs_passes_none_to_runner(
    tmp_path,
):
    cycle_log = tmp_path / "cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    cycle_log.write_text("", encoding="utf-8")
    trade_log.write_text("", encoding="utf-8")
    nav_log.write_text("", encoding="utf-8")
    calls = []
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    def fake_strategy_evidence_runner(
        *,
        performance_summary,
        nav_risk_report,
        cost_audit_report,
        outcome_report,
        audit_history_report,
        config,
        generated_at,
    ):
        calls.append(
            {
                "outcome_report": outcome_report,
                "audit_history_report": audit_history_report,
            },
        )
        return _strategy_evidence_stub_report(
            status="local_evidence_gaps",
            evidence_gap_names=(
                "missing_outcome_evidence",
                "missing_strategy_audit_history",
            ),
        )

    exit_code = main(
        [
            "strategy-evidence",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
        ],
        strategy_evidence_runner=fake_strategy_evidence_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert calls == [
        {
            "outcome_report": None,
            "audit_history_report": None,
        },
    ]


def test_strategy_evidence_cli_returns_one_when_runner_fails_without_mutating_logs(
    tmp_path,
    capsys,
):
    cycle_log = tmp_path / "cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    cycle_log.write_text("", encoding="utf-8")
    trade_log.write_text("", encoding="utf-8")
    nav_log.write_text("", encoding="utf-8")
    before = {
        cycle_log: cycle_log.read_bytes(),
        trade_log: trade_log.read_bytes(),
        nav_log: nav_log.read_bytes(),
    }
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    def broken_strategy_evidence_runner(**kwargs):
        raise RuntimeError("strategy evidence failed")

    exit_code = main(
        [
            "strategy-evidence",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
        ],
        strategy_evidence_runner=broken_strategy_evidence_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    assert {path: path.read_bytes() for path in before} == before
    captured = capsys.readouterr()
    assert "strategy-evidence failed: strategy evidence failed" in captured.err


def test_strategy_evidence_cli_missing_required_log_returns_one_without_client(
    tmp_path,
    capsys,
):
    cycle_log = tmp_path / "missing-cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    trade_log.write_text("", encoding="utf-8")
    nav_log.write_text("", encoding="utf-8")
    assert not cycle_log.exists()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "strategy-evidence",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    assert not cycle_log.exists()
    captured = capsys.readouterr()
    assert "strategy-evidence failed:" in captured.err
    assert "missing-cycles.jsonl" in captured.err


def _observability_trends_stub_report(
    *,
    strategy_status: str = "local_evidence_observed",
    outcome_status: str = "latest_outcomes_fresh",
    nav_status: str = "latest_nav_risk_observed",
    cost_status: str = "latest_cost_observed",
) -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        config_version="local-observability-trends-v0",
        strategy_evidence_trend=SimpleNamespace(
            snapshot_report_count=2,
            latest_status=strategy_status,
            latest_evidence_gap_names=(),
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
        outcome_freshness=SimpleNamespace(
            outcome_report_count=1,
            status=outcome_status,
            latest_report_age_seconds=0,
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
        nav_risk_trend=SimpleNamespace(
            nav_risk_report_count=1,
            status=nav_status,
            latest_exit_nav=Decimal("10000"),
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
        paper_trade_cost_trend=SimpleNamespace(
            cost_audit_report_count=1,
            status=cost_status,
            latest_mean_edge_cost_drag=Decimal("0.020000"),
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_observability_trends_cli_passes_paths_config_and_prints_without_client(
    tmp_path,
    capsys,
):
    cycle_log, trade_log, nav_log, outcome_log = _write_strategy_audit_inputs(
        tmp_path,
        _resolved_outcome_report(),
    )
    audit_log = tmp_path / "strategy-audits.jsonl"
    PaperStrategyRiskAuditLog(audit_log).append(_strategy_audit_report("audit_ready"))
    before = {
        cycle_log: cycle_log.read_bytes(),
        trade_log: trade_log.read_bytes(),
        nav_log: nav_log.read_bytes(),
        outcome_log: outcome_log.read_bytes(),
        audit_log: audit_log.read_bytes(),
    }
    calls = []
    client_factory_calls = 0

    def fake_observability_trends_runner(
        *,
        cycle_log,
        trade_log,
        nav_log,
        outcome_log,
        strategy_audit_log,
        config,
        generated_at,
    ):
        calls.append(
            {
                "cycle_log": cycle_log,
                "trade_log": trade_log,
                "nav_log": nav_log,
                "outcome_log": outcome_log,
                "strategy_audit_log": strategy_audit_log,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return _observability_trends_stub_report()

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "observability-trends",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
            "--outcome-log",
            str(outcome_log),
            "--strategy-audit-log",
            str(audit_log),
            "--outcome-stale-after-seconds",
            "7200",
        ],
        observability_trends_runner=fake_observability_trends_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert len(calls) == 1
    call = calls[0]
    assert call["cycle_log"] == cycle_log
    assert call["trade_log"] == trade_log
    assert call["nav_log"] == nav_log
    assert call["outcome_log"] == outcome_log
    assert call["strategy_audit_log"] == audit_log
    assert call["config"].__class__.__name__ == "LocalObservabilityTrendsConfig"
    assert call["config"].config_version == "local-observability-trends-v0"
    assert call["config"].outcome_stale_after_seconds == 7200
    assert isinstance(call["generated_at"], datetime)
    assert {path: path.read_bytes() for path in before} == before
    captured = capsys.readouterr()
    assert "observability-trends:" in captured.out
    assert "strategy_evidence_status=local_evidence_observed" in captured.out
    assert "outcome_status=latest_outcomes_fresh" in captured.out
    assert "nav_risk_status=latest_nav_risk_observed" in captured.out
    assert "cost_status=latest_cost_observed" in captured.out
    assert "paper_only=True" in captured.out
    assert "report_only=True" in captured.out
    assert "readonly=True" in captured.out


@pytest.mark.parametrize(
    ("omitted_flag", "provided_args"),
    (
        (
            "--cycle-log",
            ("--trade-log", "paper-trades.jsonl", "--nav-log", "nav.jsonl"),
        ),
        (
            "--trade-log",
            ("--cycle-log", "cycles.jsonl", "--nav-log", "nav.jsonl"),
        ),
        (
            "--nav-log",
            ("--cycle-log", "cycles.jsonl", "--trade-log", "paper-trades.jsonl"),
        ),
    ),
)
def test_observability_trends_cli_requires_local_log_flags_before_runner(
    tmp_path,
    capsys,
    omitted_flag,
    provided_args,
):
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_observability_trends_runner(**kwargs):
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("observability trends should not run")

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    argv = ["observability-trends"]
    argv.extend(
        str(tmp_path / value) if value.endswith(".jsonl") else value
        for value in provided_args
    )

    with pytest.raises(SystemExit) as exc_info:
        main(
            argv,
            observability_trends_runner=forbidden_observability_trends_runner,
            client_factory=forbidden_client_factory,
        )

    assert exc_info.value.code == 2
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert "the following arguments are required" in captured.err
    assert omitted_flag in captured.err


def test_observability_trends_cli_defaults_outcome_stale_threshold(tmp_path):
    cycle_log = tmp_path / "cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    cycle_log.write_text("", encoding="utf-8")
    trade_log.write_text("", encoding="utf-8")
    nav_log.write_text("", encoding="utf-8")
    calls = []
    client_factory_calls = 0

    def fake_observability_trends_runner(
        *,
        cycle_log,
        trade_log,
        nav_log,
        outcome_log,
        strategy_audit_log,
        config,
        generated_at,
    ):
        calls.append(config)
        return _observability_trends_stub_report()

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "observability-trends",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
        ],
        observability_trends_runner=fake_observability_trends_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert len(calls) == 1
    assert calls[0].config_version == "local-observability-trends-v0"
    assert calls[0].outcome_stale_after_seconds == 86_400


def test_observability_trends_cli_without_optional_logs_passes_none(tmp_path):
    cycle_log = tmp_path / "cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    cycle_log.write_text("", encoding="utf-8")
    trade_log.write_text("", encoding="utf-8")
    nav_log.write_text("", encoding="utf-8")
    calls = []
    client_factory_calls = 0

    def fake_observability_trends_runner(
        *,
        cycle_log,
        trade_log,
        nav_log,
        outcome_log,
        strategy_audit_log,
        config,
        generated_at,
    ):
        calls.append(
            {
                "outcome_log": outcome_log,
                "strategy_audit_log": strategy_audit_log,
            },
        )
        return _observability_trends_stub_report(
            strategy_status="local_evidence_gaps",
            outcome_status="empty_outcome_history",
            nav_status="empty_nav_risk_history",
            cost_status="empty_cost_audit_history",
        )

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "observability-trends",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
        ],
        observability_trends_runner=fake_observability_trends_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert calls == [
        {
            "outcome_log": None,
            "strategy_audit_log": None,
        },
    ]


def test_observability_trends_cli_returns_one_when_runner_fails_without_mutating_logs(
    tmp_path,
    capsys,
):
    cycle_log = tmp_path / "cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    cycle_log.write_text("", encoding="utf-8")
    trade_log.write_text("", encoding="utf-8")
    nav_log.write_text("", encoding="utf-8")
    before = {
        cycle_log: cycle_log.read_bytes(),
        trade_log: trade_log.read_bytes(),
        nav_log: nav_log.read_bytes(),
    }
    client_factory_calls = 0

    def broken_observability_trends_runner(**kwargs):
        raise RuntimeError("observability trends failed")

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "observability-trends",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
        ],
        observability_trends_runner=broken_observability_trends_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    assert {path: path.read_bytes() for path in before} == before
    captured = capsys.readouterr()
    assert "observability-trends failed: observability trends failed" in captured.err


def test_observability_trends_cli_missing_required_log_returns_one_without_client(
    tmp_path,
    capsys,
):
    cycle_log = tmp_path / "missing-cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    trade_log.write_text("", encoding="utf-8")
    nav_log.write_text("", encoding="utf-8")
    before = {
        trade_log: trade_log.read_bytes(),
        nav_log: nav_log.read_bytes(),
    }
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "observability-trends",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    assert {path: path.read_bytes() for path in before} == before
    with pytest.raises(FileNotFoundError):
        cycle_log.read_bytes()
    captured = capsys.readouterr()
    assert "observability-trends failed:" in captured.err
    assert "missing-cycles.jsonl" in captured.err


def test_observability_trends_cli_rejects_negative_outcome_stale_threshold(
    tmp_path,
    capsys,
):
    cycle_log = tmp_path / "cycles.jsonl"
    trade_log = tmp_path / "paper-trades.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    cycle_log.write_text("", encoding="utf-8")
    trade_log.write_text("", encoding="utf-8")
    nav_log.write_text("", encoding="utf-8")
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_observability_trends_runner(**kwargs):
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("observability trends should not run")

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "observability-trends",
            "--cycle-log",
            str(cycle_log),
            "--trade-log",
            str(trade_log),
            "--nav-log",
            str(nav_log),
            "--outcome-stale-after-seconds",
            "-1",
        ],
        observability_trends_runner=forbidden_observability_trends_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert "observability-trends failed:" in captured.err
    assert "outcome_stale_after_seconds must be a nonnegative integer" in captured.err


def test_run_and_strategy_cycle_do_not_call_strategy_evidence_runner(tmp_path):
    strategy_evidence_calls = []
    observability_trends_calls = []
    loop_calls = []
    cycle_calls = []

    def forbidden_strategy_evidence_runner(**kwargs):
        strategy_evidence_calls.append(kwargs)
        raise AssertionError("strategy evidence should not run")

    def forbidden_observability_trends_runner(**kwargs):
        observability_trends_calls.append(kwargs)
        raise AssertionError("observability trends should not run")

    def fake_loop_runner(**kwargs):
        loop_calls.append(kwargs)
        return _empty_run_summary()

    def fake_cycle_runner(*, client, scan_config, cycle_config):
        cycle_calls.append(
            {
                "client": client,
                "scan_config": scan_config,
                "cycle_config": cycle_config,
            },
        )
        return PaperStrategyCycleReport(
            generated_at=datetime.now(UTC),
            config_version="strategy-cycle-v1",
            scan_market_count=0,
            considered_count=0,
            snapshot_ready_count=0,
            cost_aware_report_count=0,
            blocked_counts=(),
            screening_report=None,
        )

    run_exit_code = main(
        [
            "run",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(tmp_path / "cycles.jsonl"),
        ],
        loop_runner=fake_loop_runner,
        strategy_evidence_runner=forbidden_strategy_evidence_runner,
        observability_trends_runner=forbidden_observability_trends_runner,
        client_factory=lambda: "fake-client",
    )
    strategy_cycle_exit_code = main(
        [
            "strategy-cycle",
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        cycle_runner=fake_cycle_runner,
        strategy_evidence_runner=forbidden_strategy_evidence_runner,
        observability_trends_runner=forbidden_observability_trends_runner,
        client_factory=lambda: "fake-client",
    )

    assert run_exit_code == 0
    assert strategy_cycle_exit_code == 0
    assert strategy_evidence_calls == []
    assert observability_trends_calls == []
    assert len(loop_calls) == 1
    assert len(cycle_calls) == 1


def test_nav_risk_cli_reads_nav_log_and_prints_summary(tmp_path, capsys):
    calls = []

    def fake_nav_risk_runner(*, nav_snapshots, config, generated_at):
        calls.append(
            {
                "nav_snapshots": nav_snapshots,
                "config": config,
                "generated_at": generated_at,
            }
        )
        return _empty_nav_risk_report()

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    nav_log = tmp_path / "nav.jsonl"
    PaperNavLog(nav_log).append(_empty_nav_snapshot())

    exit_code = main(
        [
            "nav-risk",
            "--nav-log",
            str(nav_log),
        ],
        nav_risk_runner=fake_nav_risk_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    call = calls[0]
    assert call["nav_snapshots"] == (_empty_nav_snapshot(),)
    assert isinstance(call["config"], PaperNavRiskMetricsConfig)
    assert call["config"].config_version == "nav-risk-metrics-v0"
    assert isinstance(call["generated_at"], datetime)

    captured = capsys.readouterr()
    assert "nav-risk:" in captured.out
    assert "snapshots=1" in captured.out
    assert "latest_exit_nav=10000" in captured.out
    assert "max_drawdown=0" in captured.out
    assert "max_drawdown_pct=0.000000" in captured.out


def test_nav_risk_cli_returns_one_when_runner_fails(tmp_path, capsys):
    def broken_nav_risk_runner(*, nav_snapshots, config, generated_at):
        raise RuntimeError("nav risk failed")

    nav_log = tmp_path / "nav.jsonl"
    PaperNavLog(nav_log).append(_empty_nav_snapshot())

    exit_code = main(
        [
            "nav-risk",
            "--nav-log",
            str(nav_log),
        ],
        nav_risk_runner=broken_nav_risk_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "nav-risk failed: nav risk failed" in captured.err


def test_nav_risk_cli_default_runner_reads_nav_log(tmp_path, capsys):
    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    nav_log = tmp_path / "nav.jsonl"
    PaperNavLog(nav_log).append(_empty_nav_snapshot())

    exit_code = main(
        [
            "nav-risk",
            "--nav-log",
            str(nav_log),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "nav-risk:" in captured.out
    assert "snapshots=1" in captured.out
    assert "latest_exit_nav=10000" in captured.out
    assert "max_drawdown=0.000000" not in captured.out
    assert "max_drawdown_pct=0.000000" in captured.out


def test_nav_risk_cli_does_not_construct_client(tmp_path):
    def fake_nav_risk_runner(*, nav_snapshots, config, generated_at):
        return _empty_nav_risk_report()

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    nav_log = tmp_path / "nav.jsonl"
    PaperNavLog(nav_log).append(_empty_nav_snapshot())

    exit_code = main(
        [
            "nav-risk",
            "--nav-log",
            str(nav_log),
        ],
        nav_risk_runner=fake_nav_risk_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0


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


def test_cost_audit_cli_reads_trade_log_and_prints_summary_without_client(
    tmp_path,
    capsys,
):
    calls = []

    def fake_cost_audit_runner(*, trade_records, config, generated_at):
        calls.append(
            {
                "trade_records": trade_records,
                "config": config,
                "generated_at": generated_at,
            }
        )
        return _empty_cost_audit_report()

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    trade_log = tmp_path / "paper-trades.jsonl"
    trade_log.write_text("", encoding="utf-8")

    exit_code = main(
        [
            "cost-audit",
            "--trade-log",
            str(trade_log),
        ],
        cost_audit_runner=fake_cost_audit_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    call = calls[0]
    assert call["trade_records"] == ()
    assert isinstance(call["config"], PaperTradeCostAuditConfig)
    assert call["config"].config_version == "paper-trade-cost-audit-v0"
    assert isinstance(call["generated_at"], datetime)

    captured = capsys.readouterr()
    assert "cost-audit:" in captured.out
    assert "trades=1" in captured.out
    assert "fill_rate=1.000000" in captured.out
    assert "mean_edge_cost_drag=0.020000" in captured.out
    assert "total_edge_cost_drag=2.000000" in captured.out
    assert "partial_fills=0" in captured.out
    assert "negative_cost_adjusted_edge=0" in captured.out


def test_cost_audit_cli_returns_one_when_runner_fails(tmp_path, capsys):
    def broken_cost_audit_runner(*, trade_records, config, generated_at):
        raise RuntimeError("cost audit failed")

    trade_log = tmp_path / "paper-trades.jsonl"
    trade_log.write_text("", encoding="utf-8")

    exit_code = main(
        [
            "cost-audit",
            "--trade-log",
            str(trade_log),
        ],
        cost_audit_runner=broken_cost_audit_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "cost-audit failed: cost audit failed" in captured.err


def _empty_run_summary() -> RunLoopSummary:
    return RunLoopSummary(
        iterations_completed=1,
        iterations_failed=0,
        first_iteration_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
        last_iteration_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
        last_error=None,
    )


def _strategy_audit_report(status="audit_ready") -> PaperStrategyRiskAuditReport:
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


def test_run_cli_builds_loop_call_single_shot(tmp_path, capsys):
    calls = []

    def fake_client_factory():
        return "fake-client"

    def fake_loop_runner(*, client, scan_config, cycle_config, starting_cash,
                         nav_log_path, cycle_report_log_path, repeat_mode,
                         interval_seconds, max_iterations):
        calls.append(
            {
                "client": client,
                "scan_config": scan_config,
                "cycle_config": cycle_config,
                "starting_cash": starting_cash,
                "nav_log_path": nav_log_path,
                "cycle_report_log_path": cycle_report_log_path,
                "repeat_mode": repeat_mode,
                "interval_seconds": interval_seconds,
                "max_iterations": max_iterations,
            }
        )
        return _empty_run_summary()

    cycle_log = tmp_path / "cycle.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    archive_root = tmp_path / "raw"

    exit_code = main(
        [
            "run",
            "--limit",
            "7",
            "--max-markets",
            "4",
            "--no-prefilter",
            "--archive-root",
            str(archive_root),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(cycle_log),
            "--nav-log",
            str(nav_log),
        ],
        loop_runner=fake_loop_runner,
        client_factory=fake_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    call = calls[0]
    assert call["client"] == "fake-client"
    assert call["scan_config"].limit == 7
    assert call["scan_config"].archive_root == archive_root
    assert call["scan_config"].fetch_books is True
    assert call["cycle_config"].max_markets_per_cycle == 4
    assert call["cycle_config"].prefilter_by_score is False
    assert call["cycle_config"].paper_execution_config is None
    assert call["cycle_config"].paper_trade_journal_path is None
    assert call["starting_cash"] == Decimal("10000")
    assert call["nav_log_path"] == nav_log
    assert call["cycle_report_log_path"] == cycle_log
    assert call["repeat_mode"] == "once"
    assert call["interval_seconds"] == 0
    assert call["max_iterations"] == 1

    captured = capsys.readouterr()
    assert "run:" in captured.out
    assert "completed=1" in captured.out
    assert "failed=0" in captured.out


def test_run_cli_maps_positive_repeat_interval_to_interval_mode(tmp_path):
    calls = []

    def fake_loop_runner(*, client, scan_config, cycle_config, starting_cash,
                         nav_log_path, cycle_report_log_path, repeat_mode,
                         interval_seconds, max_iterations):
        calls.append(
            {
                "repeat_mode": repeat_mode,
                "interval_seconds": interval_seconds,
                "max_iterations": max_iterations,
            }
        )
        return _empty_run_summary()

    exit_code = main(
        [
            "run",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "5000",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
            "--repeat-interval",
            "3600",
            "--max-iterations",
            "10",
        ],
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert calls == [
        {
            "repeat_mode": "interval",
            "interval_seconds": 3600,
            "max_iterations": 10,
        },
    ]


def test_run_cli_paper_execute_flag_enables_inline_paper_pass(tmp_path):
    calls = []

    def fake_loop_runner(*, client, scan_config, cycle_config, starting_cash,
                         nav_log_path, cycle_report_log_path, repeat_mode,
                         interval_seconds, max_iterations):
        calls.append(cycle_config)
        return _empty_run_summary()

    journal_path = tmp_path / "paper-trades.jsonl"

    exit_code = main(
        [
            "run",
            "--paper-execute",
            "--paper-journal",
            str(journal_path),
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
        ],
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert len(calls) == 1
    cycle_config = calls[0]
    assert cycle_config.paper_execution_config is not None
    assert cycle_config.paper_execution_config.config_version == "paper-execution-v1"
    assert cycle_config.paper_trade_journal_path == journal_path


def test_run_cli_returns_one_when_loop_runner_fails(tmp_path, capsys):
    def broken_loop_runner(*, client, scan_config, cycle_config, starting_cash,
                           nav_log_path, cycle_report_log_path, repeat_mode,
                           interval_seconds, max_iterations):
        raise RuntimeError("loop failed")

    exit_code = main(
        [
            "run",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
        ],
        loop_runner=broken_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "run failed: loop failed" in captured.err


def test_run_cli_prints_last_error_when_iterations_failed(tmp_path, capsys):
    def partial_loop_runner(*, client, scan_config, cycle_config, starting_cash,
                            nav_log_path, cycle_report_log_path, repeat_mode,
                            interval_seconds, max_iterations):
        return RunLoopSummary(
            iterations_completed=2,
            iterations_failed=1,
            first_iteration_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
            last_iteration_at=datetime(2026, 6, 16, 13, 0, tzinfo=UTC),
            last_error="RuntimeError: boom",
        )

    exit_code = main(
        [
            "run",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
        ],
        loop_runner=partial_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "completed=2" in captured.out
    assert "failed=1" in captured.out
    assert "last_error=RuntimeError: boom" in captured.out


def test_run_cli_strategy_audit_preflight_allows_loop_when_audit_ready(tmp_path):
    audit_calls = []
    history_calls = []
    loop_calls = []

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
        audit_calls.append(
            {
                "cycle_log": cycle_log,
                "trade_log": trade_log,
                "nav_log": nav_log,
                "outcome_log": outcome_log,
                "cost_audit_report": cost_audit_report,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return _strategy_audit_report("audit_ready")

    def fake_loop_runner(**kwargs):
        loop_calls.append(kwargs)
        return _empty_run_summary()

    def forbidden_strategy_audit_history_runner(**kwargs):
        history_calls.append(kwargs)
        raise AssertionError("strategy audit history should not run")

    paper_journal = tmp_path / "paper-trades.jsonl"
    paper_journal.write_text("", encoding="utf-8")
    cycle_log = tmp_path / "cycles.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    outcome_log = tmp_path / "outcomes.jsonl"

    exit_code = main(
        [
            "run",
            "--strategy-audit-preflight",
            "--paper-journal",
            str(paper_journal),
            "--cycle-log",
            str(cycle_log),
            "--nav-log",
            str(nav_log),
            "--outcome-log",
            str(outcome_log),
            "--starting-cash",
            "10000",
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        strategy_audit_history_runner=forbidden_strategy_audit_history_runner,
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert len(audit_calls) == 1
    assert history_calls == []
    assert len(loop_calls) == 1
    assert audit_calls[0]["cycle_log"] == cycle_log
    assert audit_calls[0]["trade_log"] == paper_journal
    assert audit_calls[0]["nav_log"] == nav_log
    assert audit_calls[0]["outcome_log"] == outcome_log
    assert isinstance(audit_calls[0]["cost_audit_report"], PaperTradeCostAuditReport)
    assert loop_calls[0]["client"] == "fake-client"


def test_run_cli_strategy_audit_preflight_appends_audit_ready_log(tmp_path):
    audit_calls = []
    loop_calls = []

    def fake_strategy_audit_runner(**kwargs):
        audit_calls.append(kwargs)
        return _strategy_audit_report("audit_ready")

    def fake_loop_runner(**kwargs):
        loop_calls.append(kwargs)
        return _empty_run_summary()

    paper_journal = tmp_path / "paper-trades.jsonl"
    paper_journal.write_text("", encoding="utf-8")
    audit_log = tmp_path / "strategy-audits.jsonl"

    exit_code = main(
        [
            "run",
            "--strategy-audit-preflight",
            "--strategy-audit-log",
            str(audit_log),
            "--paper-journal",
            str(paper_journal),
            "--cycle-log",
            str(tmp_path / "cycles.jsonl"),
            "--nav-log",
            str(tmp_path / "nav.jsonl"),
            "--starting-cash",
            "10000",
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert len(audit_calls) == 1
    assert len(loop_calls) == 1
    reports = PaperStrategyRiskAuditLog.read(audit_log)
    assert len(reports) == 1
    assert reports[0].status == "audit_ready"


@pytest.mark.parametrize("status", ("insufficient_evidence", "blocked_by_risk"))
def test_run_cli_strategy_audit_preflight_blocks_non_ready_audit(
    tmp_path,
    capsys,
    status,
):
    paper_journal = tmp_path / "paper-trades.jsonl"
    paper_journal.write_text("", encoding="utf-8")

    def fake_strategy_audit_runner(**kwargs):
        return _strategy_audit_report(status)

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    def forbidden_loop_runner(**kwargs):
        raise AssertionError("loop should not run")

    exit_code = main(
        [
            "run",
            "--strategy-audit-preflight",
            "--paper-journal",
            str(paper_journal),
            "--cycle-log",
            str(tmp_path / "cycles.jsonl"),
            "--nav-log",
            str(tmp_path / "nav.jsonl"),
            "--starting-cash",
            "10000",
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        loop_runner=forbidden_loop_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "strategy-audit:" in captured.out
    assert f"status={status}" in captured.out
    assert f"run blocked by strategy audit preflight: status={status}" in captured.err


def test_run_cli_strategy_audit_preflight_appends_blocked_audit_log_before_client(
    tmp_path,
    capsys,
):
    paper_journal = tmp_path / "paper-trades.jsonl"
    paper_journal.write_text("", encoding="utf-8")
    audit_log = tmp_path / "strategy-audits.jsonl"

    def fake_strategy_audit_runner(**kwargs):
        return _strategy_audit_report("blocked_by_risk")

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    def forbidden_loop_runner(**kwargs):
        raise AssertionError("loop should not run")

    exit_code = main(
        [
            "run",
            "--strategy-audit-preflight",
            "--strategy-audit-log",
            str(audit_log),
            "--paper-journal",
            str(paper_journal),
            "--cycle-log",
            str(tmp_path / "cycles.jsonl"),
            "--nav-log",
            str(tmp_path / "nav.jsonl"),
            "--starting-cash",
            "10000",
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        loop_runner=forbidden_loop_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    reports = PaperStrategyRiskAuditLog.read(audit_log)
    assert len(reports) == 1
    assert reports[0].status == "blocked_by_risk"
    captured = capsys.readouterr()
    assert "strategy-audit:" in captured.out
    assert "status=blocked_by_risk" in captured.out
    assert (
        "run blocked by strategy audit preflight: status=blocked_by_risk"
        in captured.err
    )


def test_run_cli_strategy_audit_preflight_requires_nav_log(tmp_path, capsys):
    def forbidden_strategy_audit_runner(**kwargs):
        raise AssertionError("audit should not run")

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    def forbidden_loop_runner(**kwargs):
        raise AssertionError("loop should not run")

    exit_code = main(
        [
            "run",
            "--strategy-audit-preflight",
            "--paper-journal",
            str(tmp_path / "paper-trades.jsonl"),
            "--cycle-log",
            str(tmp_path / "cycles.jsonl"),
            "--starting-cash",
            "10000",
        ],
        strategy_audit_runner=forbidden_strategy_audit_runner,
        loop_runner=forbidden_loop_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "run failed: strategy audit preflight requires --nav-log" in captured.err


def test_run_cli_strategy_audit_preflight_failure_does_not_construct_client(
    tmp_path,
    capsys,
):
    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    def forbidden_loop_runner(**kwargs):
        raise AssertionError("loop should not run")

    exit_code = main(
        [
            "run",
            "--strategy-audit-preflight",
            "--paper-journal",
            str(tmp_path / "missing-trades.jsonl"),
            "--cycle-log",
            str(tmp_path / "cycles.jsonl"),
            "--nav-log",
            str(tmp_path / "nav.jsonl"),
            "--starting-cash",
            "10000",
        ],
        loop_runner=forbidden_loop_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "run failed:" in captured.err
    assert "missing-trades.jsonl" in captured.err


def test_run_cli_omits_strategy_audit_preflight_by_default(tmp_path):
    audit_calls = []
    history_calls = []
    loop_calls = []

    def fake_strategy_audit_runner(**kwargs):
        audit_calls.append(kwargs)
        return _strategy_audit_report("blocked_by_risk")

    def forbidden_strategy_audit_history_runner(**kwargs):
        history_calls.append(kwargs)
        raise AssertionError("strategy audit history should not run")

    def fake_loop_runner(**kwargs):
        loop_calls.append(kwargs)
        return _empty_run_summary()

    exit_code = main(
        [
            "run",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        strategy_audit_history_runner=forbidden_strategy_audit_history_runner,
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert audit_calls == []
    assert history_calls == []
    assert len(loop_calls) == 1


def test_run_cli_json_config_enables_strategy_audit_preflight(tmp_path):
    events = []
    audit_calls = []

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
        events.append("audit")
        audit_calls.append(
            {
                "cycle_log": cycle_log,
                "trade_log": trade_log,
                "nav_log": nav_log,
                "outcome_log": outcome_log,
                "cost_audit_report": cost_audit_report,
                "config": config,
                "generated_at": generated_at,
            },
        )
        return _strategy_audit_report("audit_ready")

    def fake_loop_runner(**kwargs):
        events.append("loop")
        return _empty_run_summary()

    paper_journal = tmp_path / "paper-trades.jsonl"
    paper_journal.write_text("", encoding="utf-8")
    cycle_log = tmp_path / "cycles.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    outcome_log = tmp_path / "outcomes.jsonl"
    config_path = tmp_path / "strategy.json"
    config_path.write_text(
        json.dumps(
            {
                "strategy_audit_preflight": True,
                "outcome_log": str(outcome_log),
            },
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "run",
            "--config",
            str(config_path),
            "--paper-journal",
            str(paper_journal),
            "--cycle-log",
            str(cycle_log),
            "--nav-log",
            str(nav_log),
            "--starting-cash",
            "10000",
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert events == ["audit", "loop"]
    assert len(audit_calls) == 1
    assert audit_calls[0]["cycle_log"] == cycle_log
    assert audit_calls[0]["trade_log"] == paper_journal
    assert audit_calls[0]["nav_log"] == nav_log
    assert audit_calls[0]["outcome_log"] == outcome_log


def test_run_cli_json_config_sets_strategy_audit_log_path(tmp_path):
    events = []

    def fake_strategy_audit_runner(**kwargs):
        events.append("audit")
        return _strategy_audit_report("audit_ready")

    def fake_loop_runner(**kwargs):
        events.append("loop")
        return _empty_run_summary()

    paper_journal = tmp_path / "paper-trades.jsonl"
    paper_journal.write_text("", encoding="utf-8")
    audit_log = tmp_path / "strategy-audits.jsonl"
    config_path = tmp_path / "strategy.json"
    config_path.write_text(
        json.dumps(
            {
                "strategy_audit_preflight": True,
                "strategy_audit_log": str(audit_log),
            },
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "run",
            "--config",
            str(config_path),
            "--paper-journal",
            str(paper_journal),
            "--cycle-log",
            str(tmp_path / "cycles.jsonl"),
            "--nav-log",
            str(tmp_path / "nav.jsonl"),
            "--starting-cash",
            "10000",
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert events == ["audit", "loop"]
    reports = PaperStrategyRiskAuditLog.read(audit_log)
    assert len(reports) == 1
    assert reports[0].status == "audit_ready"


def test_run_cli_json_config_strategy_audit_preflight_requires_nav_log(
    tmp_path,
    capsys,
):
    config_path = tmp_path / "strategy.json"
    config_path.write_text(
        json.dumps({"strategy_audit_preflight": True}),
        encoding="utf-8",
    )

    def forbidden_strategy_audit_runner(**kwargs):
        raise AssertionError("audit should not run")

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    def forbidden_loop_runner(**kwargs):
        raise AssertionError("loop should not run")

    exit_code = main(
        [
            "run",
            "--config",
            str(config_path),
            "--starting-cash",
            "10000",
        ],
        strategy_audit_runner=forbidden_strategy_audit_runner,
        loop_runner=forbidden_loop_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "run failed: strategy audit preflight requires --nav-log" in captured.err


def test_run_cli_no_strategy_audit_preflight_overrides_json_true(tmp_path):
    audit_calls = []
    loop_calls = []
    audit_log = tmp_path / "strategy-audits.jsonl"
    config_path = tmp_path / "strategy.json"
    config_path.write_text(
        json.dumps(
            {
                "strategy_audit_preflight": True,
                "strategy_audit_log": str(audit_log),
            },
        ),
        encoding="utf-8",
    )

    def fake_strategy_audit_runner(**kwargs):
        audit_calls.append(kwargs)
        return _strategy_audit_report("blocked_by_risk")

    def fake_loop_runner(**kwargs):
        loop_calls.append(kwargs)
        return _empty_run_summary()

    exit_code = main(
        [
            "run",
            "--config",
            str(config_path),
            "--no-strategy-audit-preflight",
            "--starting-cash",
            "10000",
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert audit_calls == []
    assert len(loop_calls) == 1
    assert not audit_log.exists()


def test_run_cli_strategy_audit_log_is_inert_without_preflight(tmp_path):
    audit_calls = []
    loop_calls = []
    audit_log = tmp_path / "strategy-audits.jsonl"

    def fake_strategy_audit_runner(**kwargs):
        audit_calls.append(kwargs)
        return _strategy_audit_report("audit_ready")

    def fake_loop_runner(**kwargs):
        loop_calls.append(kwargs)
        return _empty_run_summary()

    exit_code = main(
        [
            "run",
            "--strategy-audit-log",
            str(audit_log),
            "--starting-cash",
            "10000",
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert audit_calls == []
    assert len(loop_calls) == 1
    assert not audit_log.exists()


def _empty_outcome_report() -> OutcomeTrackingReport:
    return OutcomeTrackingReport(
        generated_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
        config_version="outcome-tracker-v1",
        total_markets_checked=0,
        resolved_count=0,
        pending_count=0,
        observations=(),
        forecast_evidence_report=None,
    )


def test_check_outcomes_cli_invokes_runner_and_prints_summary(tmp_path, capsys):
    calls = []

    def fake_outcome_runner(*, client, journal_path, config, generated_at):
        calls.append(
            {
                "client": client,
                "journal_path": journal_path,
                "config": config,
                "generated_at": generated_at,
            }
        )
        return _empty_outcome_report()

    def fake_client_factory():
        return "fake-client"

    journal_path = tmp_path / "paper-trades.jsonl"

    exit_code = main(
        ["check-outcomes", "--journal", str(journal_path)],
        outcome_runner=fake_outcome_runner,
        client_factory=fake_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    call = calls[0]
    assert call["client"] == "fake-client"
    assert call["journal_path"] == journal_path
    assert isinstance(call["config"], OutcomeTrackingConfig)
    assert call["config"].config_version == "outcome-tracker-v1"
    assert isinstance(call["generated_at"], datetime)
    captured = capsys.readouterr()
    assert "check-outcomes:" in captured.out
    assert "checked=0" in captured.out
    assert "resolved=0" in captured.out
    assert "pending=0" in captured.out
    assert "no resolved observations yet" in captured.out


def test_check_outcomes_cli_prints_evidence_status_when_resolved(tmp_path, capsys):
    from polymarket_alpha_lab.forecast_evidence import (
        PaperForecastEvidenceObservation,
    )

    observation = PaperForecastEvidenceObservation(
        observed_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
        source_packet_id="pkt-1",
        condition_id="0x1",
        token_id="111",
        market_slug="m1",
        strategy_type="market_quality",
        risk_tags=("liquidity",),
        predicted_probability=Decimal("0.60"),
        actual_outcome_value=Decimal("1"),
    )
    evidence = build_paper_forecast_evidence_report(
        (observation,),
        config=PaperForecastEvidenceConfig(config_version="outcome-tracker-v1"),
        generated_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
    )
    report = OutcomeTrackingReport(
        generated_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
        config_version="outcome-tracker-v1",
        total_markets_checked=1,
        resolved_count=1,
        pending_count=0,
        observations=(observation,),
        forecast_evidence_report=evidence,
    )

    exit_code = main(
        ["check-outcomes", "--journal", str(tmp_path / "paper-trades.jsonl")],
        outcome_runner=lambda **_: report,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "check-outcomes:" in captured.out
    assert "resolved=1" in captured.out
    assert "forecast_evidence:" in captured.out
    assert f"status={evidence.status}" in captured.out
    assert "observation_count=1" in captured.out


def test_check_outcomes_cli_writes_evidence_log_when_resolved(tmp_path):
    # One resolved observation -> non-None evidence report -> appended to log.
    from polymarket_alpha_lab.forecast_evidence import (
        PaperForecastEvidenceObservation,
    )

    observation = PaperForecastEvidenceObservation(
        observed_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
        source_packet_id="pkt-1",
        condition_id="0x1",
        token_id="111",
        market_slug="m1",
        strategy_type="market_quality",
        risk_tags=("liquidity",),
        predicted_probability=Decimal("0.60"),
        actual_outcome_value=Decimal("1"),
    )
    evidence = build_paper_forecast_evidence_report(
        (observation,),
        config=PaperForecastEvidenceConfig(config_version="outcome-tracker-v1"),
        generated_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
    )
    report = OutcomeTrackingReport(
        generated_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
        config_version="outcome-tracker-v1",
        total_markets_checked=1,
        resolved_count=1,
        pending_count=0,
        observations=(observation,),
        forecast_evidence_report=evidence,
    )

    def fake_outcome_runner(*, client, journal_path, config, generated_at):
        return report

    evidence_log = tmp_path / "evidence.jsonl"
    journal_path = tmp_path / "paper-trades.jsonl"

    exit_code = main(
        [
            "check-outcomes",
            "--journal",
            str(journal_path),
            "--evidence-log",
            str(evidence_log),
        ],
        outcome_runner=fake_outcome_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert evidence_log.exists()
    line = evidence_log.read_text(encoding="utf-8").strip()
    assert '"observation_count": 1' in line
    assert '"config_version": "outcome-tracker-v1"' in line


def test_check_outcomes_cli_writes_outcome_log_even_without_resolved_observations(
    tmp_path,
    capsys,
):
    report = _empty_outcome_report()
    outcome_log = tmp_path / "outcomes.jsonl"

    exit_code = main(
        [
            "check-outcomes",
            "--journal",
            str(tmp_path / "paper-trades.jsonl"),
            "--outcome-log",
            str(outcome_log),
        ],
        outcome_runner=lambda **_: report,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert OutcomeTrackingLog.read(outcome_log) == (report,)
    captured = capsys.readouterr()
    assert "check-outcomes:" in captured.out
    assert "checked=0" in captured.out
    assert "no resolved observations yet" in captured.out


def test_check_outcomes_cli_skips_evidence_log_when_no_observations(tmp_path):
    # Zero observations -> evidence_report is None -> --evidence-log NOT written.
    evidence_log = tmp_path / "evidence.jsonl"

    exit_code = main(
        [
            "check-outcomes",
            "--journal",
            str(tmp_path / "paper-trades.jsonl"),
            "--evidence-log",
            str(evidence_log),
        ],
        outcome_runner=lambda **_: _empty_outcome_report(),
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert not evidence_log.exists()


def test_check_outcomes_cli_returns_one_when_runner_fails(tmp_path, capsys):
    def broken_outcome_runner(*, client, journal_path, config, generated_at):
        raise RuntimeError("outcome failed")

    exit_code = main(
        [
            "check-outcomes",
            "--journal",
            str(tmp_path / "paper-trades.jsonl"),
        ],
        outcome_runner=broken_outcome_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "check-outcomes failed: outcome failed" in captured.err


def test_check_outcomes_cli_uses_default_journal_path(tmp_path):
    calls = []

    def fake_outcome_runner(*, client, journal_path, config, generated_at):
        calls.append(journal_path)
        return _empty_outcome_report()

    exit_code = main(
        ["check-outcomes"],
        outcome_runner=fake_outcome_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0] == __import__("pathlib").Path("artifacts/paper-trades.jsonl")
