from datetime import UTC, datetime
from decimal import Decimal

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
from polymarket_alpha_lab.performance_summary import (
    PerformanceSummary,
    PerformanceSummaryConfig,
)
from polymarket_alpha_lab.positions import PaperNavLog, PaperNavSnapshot
from polymarket_alpha_lab.runner import RunLoopSummary
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleLog


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
    assert "pass=4" in captured.out
    assert "fail=0" in captured.out
    assert "incomplete=1" in captured.out
    assert "paper_history: status=incomplete" in captured.out
    assert "settlement_evidence: status=pass" in captured.out
    assert "forecast_quality: status=pass" in captured.out
    assert "nav_drawdown: status=pass" in captured.out
    assert "open_exposure: status=pass" in captured.out


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


def test_strategy_audit_cli_returns_one_when_runner_fails(tmp_path, capsys):
    def broken_strategy_audit_runner(
        *,
        cycle_log,
        trade_log,
        nav_log,
        outcome_log,
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
            str(tmp_path / "trades.jsonl"),
            "--nav-log",
            str(tmp_path / "nav.jsonl"),
        ],
        strategy_audit_runner=broken_strategy_audit_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "strategy-audit failed: audit failed" in captured.err


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


def _empty_run_summary() -> RunLoopSummary:
    return RunLoopSummary(
        iterations_completed=1,
        iterations_failed=0,
        first_iteration_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
        last_iteration_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
        last_error=None,
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
