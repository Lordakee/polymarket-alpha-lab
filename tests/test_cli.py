import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.paper_recommendation_artifact_index import (
    build_paper_recommendation_artifact_index_report,
)
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    PaperForecastEvidenceReport,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.outcome_tracker import (
    OutcomeTrackingConfig,
    OutcomeTrackingLog,
    OutcomeTrackingReport,
)
from polymarket_alpha_lab.paper_trade_journal_db_row import (
    paper_trade_record_to_db_row,
)
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot import (
    PaperRecommendationCycleSnapshotReport,
    build_paper_recommendation_cycle_snapshot_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot_db_row import (
    paper_recommendation_cycle_snapshot_to_db_row,
)
from polymarket_alpha_lab.paper_recommendation_pipeline import (
    PaperRecommendationPipelineStage,
    build_paper_recommendation_pipeline_report,
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
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationReport,
    PaperStrategyCandidateRecommendationRow,
)
from polymarket_alpha_lab.strategy_audit_history import (
    PaperStrategyRiskAuditHistoryConfig,
    build_paper_strategy_risk_audit_history_report,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleReport,
)
from polymarket_alpha_lab.strategy_recommendation_explain import (
    PaperStrategyRecommendationExplanationReport,
    PaperStrategyRecommendationExplanationRow,
)
from polymarket_alpha_lab.strategy_recommendation_history import (
    build_paper_strategy_recommendation_history_report,
)
from polymarket_alpha_lab.strategy_recommendation_log import (
    append_paper_strategy_recommendation_bundle_log,
)
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)
from polymarket_alpha_lab.strategy_risk_audit_log import PaperStrategyRiskAuditLog
from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyReport,
    PaperStrategySelectionPolicyRow,
)
from polymarket_alpha_lab.strategy_cycle_snapshot_source import (
    build_strategy_cycle_snapshot_source_report,
)
from polymarket_alpha_lab.supabase_outcome_tracking_config import (
    OUTCOME_TRACKING_DB_DSN_ENV_VAR,
    OUTCOME_TRACKING_DB_ENABLED_ENV_VAR,
    OUTCOME_TRACKING_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_nav_snapshot_config import (
    PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR,
    PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR,
    PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_trade_journal_config import (
    PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR,
    PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR,
    PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR,
)


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

    def fake_cycle_runner(
        *,
        client,
        scan_config,
        cycle_config,
        paper_trade_record_sink=None,
    ):
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


def test_strategy_cycle_cli_wires_paper_trade_db_sink_when_enabled(
    tmp_path,
    monkeypatch,
    capsys,
):
    fake_dsn = "postgresql://paper-trade.example.invalid/db"
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR, fake_dsn)
    monkeypatch.setenv(
        PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR,
        "paper_trade_archive",
    )
    record = SimpleNamespace(packet_id="packet-1")
    sink_calls = []

    def fake_cycle_runner(*, client, scan_config, cycle_config, paper_trade_record_sink):
        assert paper_trade_record_sink is not None
        paper_trade_record_sink(record)
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

    def fake_paper_trade_record_db_sink(*, dsn, record, table_name):
        sink_calls.append((dsn, record, table_name))

    exit_code = main(
        [
            "strategy-cycle",
            "--paper-execute",
            "--paper-journal",
            str(tmp_path / "paper-trades.jsonl"),
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        cycle_runner=fake_cycle_runner,
        paper_trade_record_db_sink=fake_paper_trade_record_db_sink,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert sink_calls == [
        (
            fake_dsn,
            record,
            "paper_trade_archive",
        ),
    ]
    captured = capsys.readouterr()
    assert fake_dsn not in captured.out
    assert fake_dsn not in captured.err


def test_strategy_cycle_cli_redacts_dsn_when_paper_trade_db_sink_fails(
    tmp_path,
    monkeypatch,
    capsys,
):
    fake_dsn = "postgresql://paper-trade.example.invalid/db"
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR, fake_dsn)
    monkeypatch.setenv(
        PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR,
        "paper_trade_archive",
    )
    record = SimpleNamespace(packet_id="packet-1")

    def fake_cycle_runner(*, client, scan_config, cycle_config, paper_trade_record_sink):
        paper_trade_record_sink(record)
        raise AssertionError("unreachable after sink failure")

    def broken_paper_trade_record_db_sink(*, dsn, record, table_name):
        raise RuntimeError(f"could not connect to {dsn}")

    exit_code = main(
        [
            "strategy-cycle",
            "--paper-execute",
            "--paper-journal",
            str(tmp_path / "paper-trades.jsonl"),
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        cycle_runner=fake_cycle_runner,
        paper_trade_record_db_sink=broken_paper_trade_record_db_sink,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert fake_dsn not in captured.out
    assert fake_dsn not in captured.err
    assert "<redacted-dsn>" in captured.err


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

    def fake_nav_runner(
        *,
        journal_path,
        starting_cash,
        client,
        marked_at,
        nav_log_path,
        nav_snapshot_sink=None,
    ):
        calls.append(
            {
                "journal_path": journal_path,
                "starting_cash": starting_cash,
                "client": client,
                "marked_at": marked_at,
                "nav_log_path": nav_log_path,
                "nav_snapshot_sink": nav_snapshot_sink,
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
    assert call["nav_snapshot_sink"] is None
    assert isinstance(call["marked_at"], datetime)

    captured = capsys.readouterr()
    assert "portfolio-nav:" in captured.out
    assert "starting_cash=10000" in captured.out
    assert "exit_nav=10000" in captured.out
    assert "position_count=0" in captured.out


def test_portfolio_nav_cli_defaults_nav_log_to_none(tmp_path):
    calls = []

    def fake_nav_runner(
        *,
        journal_path,
        starting_cash,
        client,
        marked_at,
        nav_log_path,
        nav_snapshot_sink=None,
    ):
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


def test_portfolio_nav_cli_wires_nav_snapshot_db_sink_when_enabled(
    tmp_path,
    monkeypatch,
    capsys,
):
    fake_dsn = "postgresql://paper-nav.example.invalid/db"
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR, fake_dsn)
    monkeypatch.setenv(
        PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR,
        "paper_nav_archive",
    )
    snapshot = _empty_nav_snapshot()
    sink_calls = []

    def fake_nav_runner(
        *,
        journal_path,
        starting_cash,
        client,
        marked_at,
        nav_log_path,
        nav_snapshot_sink,
    ):
        assert nav_snapshot_sink is not None
        nav_snapshot_sink(snapshot)
        return snapshot

    def fake_paper_nav_snapshot_db_sink(*, dsn, snapshot, table_name):
        sink_calls.append((dsn, snapshot, table_name))

    exit_code = main(
        [
            "portfolio-nav",
            "--journal",
            str(tmp_path / "paper-trades.jsonl"),
            "--starting-cash",
            "10000",
        ],
        nav_runner=fake_nav_runner,
        paper_nav_snapshot_db_sink=fake_paper_nav_snapshot_db_sink,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert sink_calls == [
        (
            fake_dsn,
            snapshot,
            "paper_nav_archive",
        ),
    ]
    captured = capsys.readouterr()
    assert fake_dsn not in captured.out
    assert fake_dsn not in captured.err


def test_portfolio_nav_cli_redacts_dsn_when_nav_snapshot_db_sink_fails(
    tmp_path,
    monkeypatch,
    capsys,
):
    fake_dsn = "postgresql://paper-nav.example.invalid/db"
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR, fake_dsn)
    monkeypatch.setenv(
        PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR,
        "paper_nav_archive",
    )
    snapshot = _empty_nav_snapshot()

    def fake_nav_runner(
        *,
        journal_path,
        starting_cash,
        client,
        marked_at,
        nav_log_path,
        nav_snapshot_sink,
    ):
        nav_snapshot_sink(snapshot)
        raise AssertionError("unreachable after sink failure")

    def broken_paper_nav_snapshot_db_sink(*, dsn, snapshot, table_name):
        raise RuntimeError(f"could not connect to {dsn}")

    exit_code = main(
        [
            "portfolio-nav",
            "--journal",
            str(tmp_path / "paper-trades.jsonl"),
            "--starting-cash",
            "10000",
        ],
        nav_runner=fake_nav_runner,
        paper_nav_snapshot_db_sink=broken_paper_nav_snapshot_db_sink,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert fake_dsn not in captured.out
    assert fake_dsn not in captured.err
    assert "<redacted-dsn>" in captured.err


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


def _recommendation_bundle_report(
    *,
    generated_at: datetime = datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
    market_slug: str = "market-alpha",
    notional: Decimal = Decimal("7.500000"),
    score: Decimal = Decimal("0.750000"),
) -> PaperStrategyRecommendationBundleReport:
    recommendation_report = PaperStrategyCandidateRecommendationReport(
        generated_at=generated_at,
        config_version="strategy-candidate-recommendation-v1",
        readiness_overall_status="pass",
        candidate_count=1,
        recommend_count=1,
        watch_count=0,
        reject_count=0,
        recommendation_rows=(
            PaperStrategyCandidateRecommendationRow(
                market_slug=market_slug,
                question=f"Will {market_slug} resolve yes?",
                action="recommend",
                assessment_status="ready",
                readiness_status="pass",
                selected_side="yes",
                scoring_side="yes",
                recommendation_score=score,
                reason_codes=("assessment_ready", "readiness_passed"),
            ),
        ),
    )
    selection_policy_report = PaperStrategySelectionPolicyReport(
        generated_at=generated_at,
        config_version="paper-strategy-selection-policy-v1",
        row_count=1,
        selected_count=1,
        skipped_count=0,
        not_selected_count=0,
        total_selected_notional=notional,
        selection_rows=(
            PaperStrategySelectionPolicyRow(
                market_slug=market_slug,
                question=f"Will {market_slug} resolve yes?",
                source_action="recommend",
                selected_side="yes",
                recommendation_score=score,
                decision="selected",
                suggested_position_notional=notional,
                selected_position_notional=notional,
                reason_codes=(
                    "selected_by_policy",
                    "assessment_ready",
                    "readiness_passed",
                ),
            ),
        ),
    )
    explanation_report = PaperStrategyRecommendationExplanationReport(
        generated_at=generated_at,
        source_config_version="strategy-candidate-recommendation-v1",
        recommendation_count=1,
        recommend_count=1,
        watch_count=0,
        reject_count=0,
        explanation_rows=(
            PaperStrategyRecommendationExplanationRow(
                market_slug=market_slug,
                action="recommend",
                selected_side="yes",
                recommendation_score=score,
                primary_reason_code="assessment_ready",
                reason_codes=("assessment_ready", "readiness_passed"),
                explanation=f"recommend yes because assessment_ready (score {score})",
            ),
        ),
    )
    return PaperStrategyRecommendationBundleReport(
        generated_at=generated_at,
        config_version="strategy-recommendation-bundle-v1",
        candidate_count=1,
        recommend_count=1,
        selected_count=1,
        total_selected_notional=notional,
        recommendation_report=recommendation_report,
        selection_policy_report=selection_policy_report,
        explanation_report=explanation_report,
    )


def test_strategy_recommendation_history_cli_reads_log_and_prints_summary_without_client(
    tmp_path,
    capsys,
):
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _recommendation_bundle_report(
            generated_at=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
            market_slug="market-alpha",
            notional=Decimal("7.500000"),
        ),
    )
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _recommendation_bundle_report(
            generated_at=datetime(2026, 6, 18, 16, 5, tzinfo=UTC),
            market_slug="market-beta",
            notional=Decimal("12.500000"),
        ),
    )
    before = recommendation_log.read_bytes()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "strategy-recommendation-history",
            "--recommendation-log",
            str(recommendation_log),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert recommendation_log.read_bytes() == before
    captured = capsys.readouterr()
    assert "strategy-recommendation-history:" in captured.out
    assert "source_reports=2" in captured.out
    assert "total_candidates=2" in captured.out
    assert "total_recommend=2" in captured.out
    assert "latest_selected=1" in captured.out
    assert "latest_selected_notional=12.500000" in captured.out


def test_strategy_recommendation_history_cli_prints_bundle_score_selection_trend(
    tmp_path,
    capsys,
):
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _recommendation_bundle_report(
            generated_at=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
            market_slug="market-alpha",
            notional=Decimal("7.500000"),
            score=Decimal("0.250000"),
        ),
    )
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _recommendation_bundle_report(
            generated_at=datetime(2026, 6, 18, 16, 5, tzinfo=UTC),
            market_slug="market-beta",
            notional=Decimal("12.500000"),
            score=Decimal("0.800000"),
        ),
    )
    before = recommendation_log.read_bytes()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "strategy-recommendation-history",
            "--recommendation-log",
            str(recommendation_log),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert recommendation_log.read_bytes() == before
    captured = capsys.readouterr()
    assert "selection_score_trend:" in captured.out
    assert "total_selected=2" in captured.out
    assert "total_selected_notional=20.000000" in captured.out
    assert "first_recommendation_score=0.250000" in captured.out
    assert "latest_recommendation_score=0.800000" in captured.out
    assert "latest_selected_score=0.800000" in captured.out


def test_strategy_recommendation_history_cli_prints_optional_report_metrics(
    tmp_path,
    capsys,
):
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    recommendation_log.write_text("", encoding="utf-8")

    def fake_strategy_recommendation_history_runner(
        *,
        recommendation_reports,
        config_version,
        generated_at,
    ):
        report = build_paper_strategy_recommendation_history_report(
            recommendation_reports,
            config_version=config_version,
            generated_at=generated_at,
        )
        object.__setattr__(report, "total_selected_count", 3)
        object.__setattr__(report, "total_selected_notional", Decimal("31.000000"))
        object.__setattr__(report, "selection_rate", Decimal("0.6000"))
        object.__setattr__(
            report,
            "latest_recommendation_score",
            Decimal("0.660000"),
        )
        return report

    exit_code = main(
        [
            "strategy-recommendation-history",
            "--recommendation-log",
            str(recommendation_log),
        ],
        strategy_recommendation_history_runner=(
            fake_strategy_recommendation_history_runner
        ),
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "selection_score_trend:" in captured.out
    assert "total_selected_count=3" in captured.out
    assert "total_selected_notional=31.000000" in captured.out
    assert "selection_rate=0.6000" in captured.out
    assert "latest_recommendation_score=0.660000" in captured.out


def test_strategy_recommendation_history_cli_aligns_latest_selection_with_history_order(
    tmp_path,
    capsys,
):
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _recommendation_bundle_report(
            generated_at=datetime(2026, 6, 18, 16, 5, tzinfo=UTC),
            market_slug="market-newer",
            notional=Decimal("12.500000"),
        ),
    )
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _recommendation_bundle_report(
            generated_at=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
            market_slug="market-older",
            notional=Decimal("7.500000"),
        ),
    )

    exit_code = main(
        [
            "strategy-recommendation-history",
            "--recommendation-log",
            str(recommendation_log),
        ],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "latest=2026-06-18T16:05:00+00:00" in captured.out
    assert "latest_selected=1" in captured.out
    assert "latest_selected_notional=12.500000" in captured.out


def test_strategy_recommendation_history_cli_uses_last_stable_tie_for_latest_selection(
    tmp_path,
    capsys,
):
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    tied_generated_at = datetime(2026, 6, 18, 16, 5, tzinfo=UTC)
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _recommendation_bundle_report(
            generated_at=tied_generated_at,
            market_slug="market-first-tie",
            notional=Decimal("4.000000"),
        ),
    )
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _recommendation_bundle_report(
            generated_at=tied_generated_at,
            market_slug="market-last-tie",
            notional=Decimal("9.000000"),
        ),
    )

    exit_code = main(
        [
            "strategy-recommendation-history",
            "--recommendation-log",
            str(recommendation_log),
        ],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "latest=2026-06-18T16:05:00+00:00" in captured.out
    assert "latest_selected=1" in captured.out
    assert "latest_selected_notional=9.000000" in captured.out


def test_strategy_recommendation_history_cli_passes_nested_reports_to_runner(
    tmp_path,
):
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    first = _recommendation_bundle_report(
        generated_at=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
        market_slug="market-alpha",
    )
    second = _recommendation_bundle_report(
        generated_at=datetime(2026, 6, 18, 16, 5, tzinfo=UTC),
        market_slug="market-beta",
    )
    append_paper_strategy_recommendation_bundle_log(recommendation_log, first)
    append_paper_strategy_recommendation_bundle_log(recommendation_log, second)
    calls = []

    def fake_strategy_recommendation_history_runner(
        *,
        recommendation_reports,
        config_version,
        generated_at,
    ):
        calls.append(
            {
                "recommendation_reports": recommendation_reports,
                "config_version": config_version,
                "generated_at": generated_at,
            },
        )
        return build_paper_strategy_recommendation_history_report(
            recommendation_reports,
            config_version=config_version,
            generated_at=generated_at,
        )

    exit_code = main(
        [
            "strategy-recommendation-history",
            "--recommendation-log",
            str(recommendation_log),
        ],
        strategy_recommendation_history_runner=(
            fake_strategy_recommendation_history_runner
        ),
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["recommendation_reports"] == (
        first.recommendation_report,
        second.recommendation_report,
    )
    assert calls[0]["config_version"] == "strategy-recommendation-history-v0"
    assert isinstance(calls[0]["generated_at"], datetime)


def test_strategy_recommendation_history_cli_empty_log_prints_zero_summary_without_mutation(
    tmp_path,
    capsys,
):
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    recommendation_log.write_text("", encoding="utf-8")
    before = recommendation_log.read_bytes()

    exit_code = main(
        [
            "strategy-recommendation-history",
            "--recommendation-log",
            str(recommendation_log),
        ],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert recommendation_log.read_bytes() == before
    captured = capsys.readouterr()
    assert "strategy-recommendation-history:" in captured.out
    assert "source_reports=0" in captured.out
    assert "total_candidates=0" in captured.out
    assert "latest_selected=0" in captured.out
    assert "latest_selected_notional=0" in captured.out
    assert "first=none" in captured.out
    assert "latest=none" in captured.out


def test_strategy_recommendation_history_cli_missing_log_returns_one_without_client(
    tmp_path,
    capsys,
):
    recommendation_log = tmp_path / "missing-strategy-recommendations.jsonl"
    assert not recommendation_log.exists()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "strategy-recommendation-history",
            "--recommendation-log",
            str(recommendation_log),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    assert not recommendation_log.exists()
    captured = capsys.readouterr()
    assert "strategy-recommendation-history failed:" in captured.err
    assert "missing-strategy-recommendations.jsonl" in captured.err


def test_strategy_recommendation_history_cli_returns_one_when_runner_fails(
    tmp_path,
    capsys,
):
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _recommendation_bundle_report(),
    )
    before = recommendation_log.read_bytes()

    def broken_strategy_recommendation_history_runner(**kwargs):
        raise RuntimeError("recommendation history failed")

    exit_code = main(
        [
            "strategy-recommendation-history",
            "--recommendation-log",
            str(recommendation_log),
        ],
        strategy_recommendation_history_runner=(
            broken_strategy_recommendation_history_runner
        ),
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    assert recommendation_log.read_bytes() == before
    captured = capsys.readouterr()
    assert (
        "strategy-recommendation-history failed: recommendation history failed"
        in captured.err
    )


def test_cycle_snapshot_db_trend_cli_requires_enabled_db_config(
    monkeypatch,
    capsys,
):
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", raising=False)
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", raising=False)

    def forbidden_runner(**kwargs):
        raise AssertionError("trend runner should not run")

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    exit_code = main(
        ["cycle-snapshot-db-trend"],
        cycle_snapshot_db_trend_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "cycle-snapshot-db-trend failed:" in captured.err
    assert "requires cycle snapshot DB to be enabled" in captured.err


def test_cycle_snapshot_db_trend_cli_reads_db_config_and_prints_summary(
    monkeypatch,
    capsys,
):
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", "test-dsn-value")
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_TABLE",
        "cycle_snapshot_archive",
    )
    calls = []

    def fake_trend_runner(
        *,
        dsn,
        generated_at,
        config_version,
        source_config_version,
        limit,
        table_name,
    ):
        calls.append(
            {
                "dsn": dsn,
                "generated_at": generated_at,
                "config_version": config_version,
                "source_config_version": source_config_version,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return SimpleNamespace(
            snapshot_count=3,
            pass_count=1,
            watch_count=1,
            blocked_count=1,
            latest_status="blocked",
            first_generated_at=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
            last_generated_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
            blocked_share=Decimal("0.333333"),
            watch_share=Decimal("0.333333"),
            average_stage_count=Decimal("4.000000"),
            average_artifact_count=Decimal("7.000000"),
            paper_only=True,
            report_only=True,
            readonly=True,
        )

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "cycle-snapshot-db-trend",
            "--source-config-version",
            "paper-recommendation-cycle-snapshot-v0",
            "--limit",
            "25",
        ],
        cycle_snapshot_db_trend_runner=fake_trend_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["dsn"] == "test-dsn-value"
    assert calls[0]["config_version"] == "cycle-snapshot-db-trend-v0"
    assert (
        calls[0]["source_config_version"]
        == "paper-recommendation-cycle-snapshot-v0"
    )
    assert calls[0]["limit"] == 25
    assert calls[0]["table_name"] == "cycle_snapshot_archive"
    assert isinstance(calls[0]["generated_at"], datetime)

    captured = capsys.readouterr()
    assert "cycle-snapshot-db-trend:" in captured.out
    assert "snapshots=3" in captured.out
    assert "pass=1" in captured.out
    assert "watch=1" in captured.out
    assert "blocked=1" in captured.out
    assert "latest_status=blocked" in captured.out
    assert "blocked_share=0.333333" in captured.out
    assert "test-dsn-value" not in captured.out
    assert "test-dsn-value" not in captured.err


def test_cycle_snapshot_db_trend_cli_default_psycopg_load_path_no_network(
    monkeypatch,
    capsys,
):
    fake_dsn = "postgresql://fake.example.invalid/cycle-snapshots"
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", fake_dsn)
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_TABLE",
        "cycle_snapshot_archive",
    )

    config_version = "paper-recommendation-cycle-snapshot-v0"

    def snapshot_row(generated_at, *, final_status):
        pipeline_report = build_paper_recommendation_pipeline_report(
            generated_at=generated_at,
            config_version="paper-recommendation-pipeline-v0",
            stages=(
                PaperRecommendationPipelineStage(
                    stage_name=f"{final_status}_stage",
                    status="pass",
                    message=f"{final_status} stage",
                    input_count=1,
                    output_count=1,
                ),
            ),
        )
        artifact_index_report = build_paper_recommendation_artifact_index_report(
            generated_at=generated_at,
            config_version="paper-recommendation-artifact-index-v0",
            artifacts=(
                SimpleNamespace(
                    artifact_name=f"{final_status}_artifact",
                    config_version="paper-recommendation-artifact-index-v0",
                    generated_at=generated_at,
                    status=final_status,
                    item_count=1,
                    reason_codes=(f"{final_status}_snapshot",),
                    flags=("paper_only", "report_only", "readonly"),
                    paper_only=True,
                    report_only=True,
                    readonly=True,
                ),
            ),
        )
        row = paper_recommendation_cycle_snapshot_to_db_row(
            build_paper_recommendation_cycle_snapshot_report(
                generated_at=generated_at,
                config_version=config_version,
                pipeline_report=pipeline_report,
                artifact_index_report=artifact_index_report,
            ),
        )
        return (
            row.snapshot_sha256,
            row.generated_at,
            row.config_version,
            row.final_status,
            row.stage_counts_json,
            row.artifact_counts_json,
            list(row.reason_codes),
            row.payload_json,
            row.paper_only,
            row.report_only,
            row.readonly,
        )

    rows = (
        snapshot_row(datetime(2026, 6, 19, 14, 0, tzinfo=UTC), final_status="blocked"),
        snapshot_row(datetime(2026, 6, 19, 12, 0, tzinfo=UTC), final_status="pass"),
    )

    class FakeCursor:
        def __init__(self):
            self.calls = []
            self.closed = False

        def execute(self, sql, params=()):
            self.calls.append((" ".join(sql.split()), params))

        def fetchall(self):
            return rows

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
    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=lambda dsn: connect_calls.append(dsn) or connection),
    )
    monkeypatch.setitem(
        sys.modules,
        "psycopg.types.json",
        SimpleNamespace(Jsonb=FakeJsonb),
    )

    exit_code = main(
        [
            "cycle-snapshot-db-trend",
            "--source-config-version",
            config_version,
            "--limit",
            "2",
        ],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert connect_calls == [fake_dsn]
    assert connection.cursor_count == 1
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert "FROM cycle_snapshot_archive" in sql
    assert "ORDER BY generated_at DESC, inserted_at DESC, snapshot_sha256 DESC" in sql
    assert params == (config_version, 2)

    captured = capsys.readouterr()
    assert "cycle-snapshot-db-trend:" in captured.out
    assert "snapshots=2" in captured.out
    assert "pass=1" in captured.out
    assert "blocked=1" in captured.out
    assert "latest_status=blocked" in captured.out
    assert fake_dsn not in captured.out
    assert fake_dsn not in captured.err


def test_cycle_snapshot_db_trend_cli_runner_failure_redacts_dsn(
    monkeypatch,
    capsys,
):
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", "test-dsn-value")

    def broken_runner(**kwargs):
        raise RuntimeError("database unavailable")

    exit_code = main(
        ["cycle-snapshot-db-trend"],
        cycle_snapshot_db_trend_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "cycle-snapshot-db-trend failed: database unavailable" in captured.err
    assert "test-dsn-value" not in captured.err


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
                         interval_seconds, max_iterations,
                         cycle_snapshot_source=None, cycle_snapshot_sink=None,
                         paper_trade_record_sink=None, nav_snapshot_sink=None):
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
                "cycle_snapshot_source": cycle_snapshot_source,
                "cycle_snapshot_sink": cycle_snapshot_sink,
                "paper_trade_record_sink": paper_trade_record_sink,
                "nav_snapshot_sink": nav_snapshot_sink,
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
    assert call["cycle_snapshot_source"] is None
    assert call["cycle_snapshot_sink"] is None
    assert call["paper_trade_record_sink"] is None
    assert call["nav_snapshot_sink"] is None

    captured = capsys.readouterr()
    assert "run:" in captured.out
    assert "completed=1" in captured.out
    assert "failed=0" in captured.out


def test_run_cli_maps_positive_repeat_interval_to_interval_mode(tmp_path):
    calls = []

    def fake_loop_runner(*, client, scan_config, cycle_config, starting_cash,
                         nav_log_path, cycle_report_log_path, repeat_mode,
                         interval_seconds, max_iterations,
                         cycle_snapshot_source=None, cycle_snapshot_sink=None,
                         paper_trade_record_sink=None, nav_snapshot_sink=None):
        calls.append(
            {
                "repeat_mode": repeat_mode,
                "interval_seconds": interval_seconds,
                "max_iterations": max_iterations,
                "cycle_snapshot_source": cycle_snapshot_source,
                "cycle_snapshot_sink": cycle_snapshot_sink,
                "paper_trade_record_sink": paper_trade_record_sink,
                "nav_snapshot_sink": nav_snapshot_sink,
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
            "cycle_snapshot_source": None,
            "cycle_snapshot_sink": None,
            "paper_trade_record_sink": None,
            "nav_snapshot_sink": None,
        },
    ]


def test_run_cli_paper_execute_flag_enables_inline_paper_pass(tmp_path):
    calls = []

    def fake_loop_runner(*, client, scan_config, cycle_config, starting_cash,
                         nav_log_path, cycle_report_log_path, repeat_mode,
                         interval_seconds, max_iterations,
                         cycle_snapshot_source=None, cycle_snapshot_sink=None,
                         paper_trade_record_sink=None, nav_snapshot_sink=None):
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


def test_run_cli_leaves_cycle_snapshot_db_disabled_by_default(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", raising=False)
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", raising=False)
    monkeypatch.delenv(PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR, raising=False)
    calls = []

    def fake_loop_runner(**kwargs):
        calls.append(kwargs)
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
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["cycle_snapshot_source"] is None
    assert calls[0]["cycle_snapshot_sink"] is None
    assert calls[0]["paper_trade_record_sink"] is None
    assert calls[0]["nav_snapshot_sink"] is None


def test_run_cli_wires_paper_trade_and_nav_db_sinks_when_env_enabled(
    tmp_path,
    monkeypatch,
    capsys,
):
    trade_dsn = "postgresql://paper-trade.example.invalid/db"
    nav_dsn = "postgresql://paper-nav.example.invalid/db"
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR, trade_dsn)
    monkeypatch.setenv(
        PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR,
        "paper_trade_archive",
    )
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR, nav_dsn)
    monkeypatch.setenv(
        PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR,
        "paper_nav_archive",
    )
    trade_record = SimpleNamespace(packet_id="packet-1")
    nav_snapshot = _empty_nav_snapshot()
    trade_sink_calls = []
    nav_sink_calls = []
    loop_calls = []

    def fake_loop_runner(**kwargs):
        loop_calls.append(kwargs)
        assert kwargs["paper_trade_record_sink"] is not None
        assert kwargs["nav_snapshot_sink"] is not None
        kwargs["paper_trade_record_sink"](trade_record)
        kwargs["nav_snapshot_sink"](nav_snapshot)
        return _empty_run_summary()

    def fake_paper_trade_record_db_sink(*, dsn, record, table_name):
        trade_sink_calls.append((dsn, record, table_name))

    def fake_paper_nav_snapshot_db_sink(*, dsn, snapshot, table_name):
        nav_sink_calls.append((dsn, snapshot, table_name))

    exit_code = main(
        [
            "run",
            "--paper-execute",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
        ],
        loop_runner=fake_loop_runner,
        paper_trade_record_db_sink=fake_paper_trade_record_db_sink,
        paper_nav_snapshot_db_sink=fake_paper_nav_snapshot_db_sink,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert len(loop_calls) == 1
    assert trade_sink_calls == [
        (
            trade_dsn,
            trade_record,
            "paper_trade_archive",
        ),
    ]
    assert nav_sink_calls == [
        (
            nav_dsn,
            nav_snapshot,
            "paper_nav_archive",
        ),
    ]
    captured = capsys.readouterr()
    assert trade_dsn not in captured.out
    assert trade_dsn not in captured.err
    assert nav_dsn not in captured.out
    assert nav_dsn not in captured.err


def test_run_cli_redacts_dsn_when_paper_trade_db_sink_failure_is_reported(
    tmp_path,
    monkeypatch,
    capsys,
):
    trade_dsn = "postgresql://paper-trade.example.invalid/db"
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR, trade_dsn)
    monkeypatch.setenv(
        PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR,
        "paper_trade_archive",
    )
    trade_record = SimpleNamespace(packet_id="packet-1")

    def fake_loop_runner(**kwargs):
        assert kwargs["paper_trade_record_sink"] is not None
        try:
            kwargs["paper_trade_record_sink"](trade_record)
        except Exception as exc:
            return RunLoopSummary(
                iterations_completed=0,
                iterations_failed=1,
                first_iteration_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
                last_iteration_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
                last_error=f"{type(exc).__name__}: {exc}",
            )
        raise AssertionError("sink should fail")

    def broken_paper_trade_record_db_sink(*, dsn, record, table_name):
        raise RuntimeError(f"could not connect to {dsn}")

    exit_code = main(
        [
            "run",
            "--paper-execute",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
        ],
        loop_runner=fake_loop_runner,
        paper_trade_record_db_sink=broken_paper_trade_record_db_sink,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert trade_dsn not in captured.out
    assert trade_dsn not in captured.err
    assert "last_error=RuntimeError: could not connect to <redacted-dsn>" in (
        captured.out
    )


def test_run_cli_wires_cycle_snapshot_db_sink_when_env_enabled(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", "test-dsn-value")
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_TABLE",
        "cycle_snapshot_archive",
    )
    calls = []
    sink_calls = []
    source_value = SimpleNamespace(paper_only=True, report_only=True, readonly=True)

    def fake_loop_runner(**kwargs):
        calls.append(kwargs)
        assert kwargs["cycle_snapshot_source"] is fake_cycle_snapshot_source
        assert kwargs["cycle_snapshot_source"] is not None
        snapshot = kwargs["cycle_snapshot_source"](
            cycle_report=object(),
            iteration_started_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
        )
        kwargs["cycle_snapshot_sink"](snapshot)
        return RunLoopSummary(
            iterations_completed=1,
            iterations_failed=0,
            first_iteration_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
            last_iteration_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
            last_error=None,
            cycle_snapshots_persisted=1,
        )

    def fake_cycle_snapshot_source(*, cycle_report, iteration_started_at):
        return source_value

    def fake_cycle_snapshot_sink(*, dsn, report, table_name):
        sink_calls.append((dsn, report, table_name))

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
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
        cycle_snapshot_source=fake_cycle_snapshot_source,
        cycle_snapshot_db_sink=fake_cycle_snapshot_sink,
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert sink_calls == [
        (
            "test-dsn-value",
            source_value,
            "cycle_snapshot_archive",
        ),
    ]


def test_run_cli_uses_default_cycle_snapshot_source_when_db_enabled_without_injection(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", "test-dsn-value")
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_TABLE",
        "cycle_snapshot_archive",
    )
    calls = []
    sink_calls = []
    cycle_report = PaperStrategyCycleReport(
        generated_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
        config_version="strategy-cycle-v1",
        scan_market_count=4,
        considered_count=3,
        snapshot_ready_count=0,
        cost_aware_report_count=0,
        blocked_counts=(("blocked_fetch_error", 3),),
        screening_report=None,
    )

    def fake_loop_runner(**kwargs):
        calls.append(kwargs)
        assert kwargs["cycle_snapshot_source"] is build_strategy_cycle_snapshot_source_report
        snapshot = kwargs["cycle_snapshot_source"](
            cycle_report=cycle_report,
            iteration_started_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
        )
        kwargs["cycle_snapshot_sink"](snapshot)
        return RunLoopSummary(
            iterations_completed=1,
            iterations_failed=0,
            first_iteration_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
            last_iteration_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
            last_error=None,
            cycle_snapshots_persisted=1,
        )

    def fake_cycle_snapshot_sink(*, dsn, report, table_name):
        sink_calls.append((dsn, report, table_name))

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
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
        cycle_snapshot_db_sink=fake_cycle_snapshot_sink,
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert len(sink_calls) == 1
    dsn, report, table_name = sink_calls[0]
    assert dsn == "test-dsn-value"
    assert table_name == "cycle_snapshot_archive"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.final_status == "blocked"
    captured = capsys.readouterr()
    assert "cycle_snapshots_persisted=1" in captured.out
    assert "test-dsn-value" not in captured.out
    assert "test-dsn-value" not in captured.err


def test_run_cli_default_loop_persists_default_snapshot_report_from_real_cycle(
    tmp_path,
    monkeypatch,
    capsys,
):
    fake_dsn = "postgresql://fake.example.invalid/paper-only"
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", fake_dsn)
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_TABLE",
        "cycle_snapshot_archive",
    )

    yes_token_id = "fake-yes-token"
    no_token_id = "fake-no-token"
    raw_market = {
        "conditionId": "0xfakecondition",
        "slug": "fake-local-market",
        "question": "Will the local fake event resolve yes?",
        "active": True,
        "closed": False,
        "acceptingOrders": True,
        "enableOrderBook": True,
        "endDate": "2030-01-01T00:00:00Z",
        "volume24hr": "5000",
        "liquidity": "10000",
        "orderMinSize": "5",
        "orderPriceMinTickSize": "0.01",
        "outcomes": ["Yes", "No"],
        "clobTokenIds": [yes_token_id, no_token_id],
        "description": "Resolves according to a local fake public source.",
        "resolutionSource": "https://example.invalid/fake-resolution",
    }
    raw_books = {
        yes_token_id: {
            "asset_id": yes_token_id,
            "bids": [{"price": "0.5300", "size": "100.0000"}],
            "asks": [{"price": "0.5500", "size": "100.0000"}],
        },
        no_token_id: {
            "asset_id": no_token_id,
            "bids": [{"price": "0.3700", "size": "100.0000"}],
            "asks": [{"price": "0.4000", "size": "100.0000"}],
        },
    }
    list_markets_calls = []
    order_book_calls = []
    sink_calls = []

    class FakeMarketDataClient:
        def list_markets(self, *, active, closed, limit, search=None):
            list_markets_calls.append(
                {
                    "active": active,
                    "closed": closed,
                    "limit": limit,
                    "search": search,
                }
            )
            return [raw_market]

        def get_order_book(self, *, token_id):
            order_book_calls.append(token_id)
            return raw_books[token_id]

    fake_client = FakeMarketDataClient()

    def fake_cycle_snapshot_db_sink(*, dsn, report, table_name):
        sink_calls.append((dsn, report, table_name))

    archive_root = tmp_path / "raw"
    cycle_log = tmp_path / "cycle.jsonl"
    nav_log = tmp_path / "nav.jsonl"

    exit_code = main(
        [
            "run",
            "--limit",
            "1",
            "--max-markets",
            "1",
            "--no-prefilter",
            "--archive-root",
            str(archive_root),
            "--cycle-log",
            str(cycle_log),
            "--nav-log",
            str(nav_log),
            "--starting-cash",
            "10000",
            "--max-iterations",
            "1",
        ],
        client_factory=lambda: fake_client,
        cycle_snapshot_db_sink=fake_cycle_snapshot_db_sink,
    )

    assert exit_code == 0
    assert list_markets_calls == [
        {
            "active": True,
            "closed": False,
            "limit": 1,
            "search": None,
        },
    ]
    assert order_book_calls == [yes_token_id, no_token_id]
    assert len(sink_calls) == 1
    dsn, report, table_name = sink_calls[0]
    assert dsn == fake_dsn
    assert table_name == "cycle_snapshot_archive"
    assert isinstance(report, PaperRecommendationCycleSnapshotReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.final_status == "pass"
    # The default strategy-cycle snapshot source currently emits four pipeline
    # stages and two artifacts; this integration test should catch wiring drift.
    assert report.stage_count == 4
    assert report.artifact_count == 2
    assert "screening_ready_candidates" in report.reason_codes

    captured = capsys.readouterr()
    assert "completed=1" in captured.out
    assert "failed=0" in captured.out
    assert "cycle_snapshots_persisted=1" in captured.out
    assert fake_dsn not in captured.out
    assert fake_dsn not in captured.err

    cycle_reports = PaperStrategyCycleLog.read(cycle_log)
    assert len(cycle_reports) == 1
    cycle_report = cycle_reports[0]
    assert isinstance(cycle_report, PaperStrategyCycleReport)
    assert cycle_report.paper_only is True
    assert cycle_report.report_only is True
    assert cycle_report.scan_market_count == 1
    assert cycle_report.considered_count == 1
    assert cycle_report.snapshot_ready_count == 1
    assert cycle_report.cost_aware_report_count == 1
    assert cycle_report.screening_report is not None


def test_run_cli_default_loop_persists_paper_trade_and_nav_db_sinks_from_real_cycle(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", raising=False)
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", raising=False)
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_TABLE", raising=False)
    monkeypatch.chdir(tmp_path)
    trade_dsn = "postgresql://paper-trade.example.invalid/default-loop"
    nav_dsn = "postgresql://paper-nav.example.invalid/default-loop"
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR, trade_dsn)
    monkeypatch.setenv(
        PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR,
        "paper_trade_archive",
    )
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_NAV_SNAPSHOT_DB_DSN_ENV_VAR, nav_dsn)
    monkeypatch.setenv(
        PAPER_NAV_SNAPSHOT_DB_TABLE_ENV_VAR,
        "paper_nav_archive",
    )

    yes_token_id = "fake-yes-token"
    no_token_id = "fake-no-token"
    raw_market = {
        "conditionId": "0xfakecondition",
        "slug": "fake-local-market",
        "question": "Will the local fake event resolve yes?",
        "active": True,
        "closed": False,
        "acceptingOrders": True,
        "enableOrderBook": True,
        "endDate": "2030-01-01T00:00:00Z",
        "volume24hr": "5000",
        "liquidity": "10000",
        "orderMinSize": "5",
        "orderPriceMinTickSize": "0.01",
        "outcomes": ["Yes", "No"],
        "clobTokenIds": [yes_token_id, no_token_id],
        "description": "Resolves according to a local fake public source.",
        "resolutionSource": "https://example.invalid/fake-resolution",
    }
    raw_books = {
        yes_token_id: {
            "asset_id": yes_token_id,
            "bids": [{"price": "0.5300", "size": "100.0000"}],
            "asks": [{"price": "0.5500", "size": "100.0000"}],
        },
        no_token_id: {
            "asset_id": no_token_id,
            "bids": [{"price": "0.3700", "size": "100.0000"}],
            "asks": [{"price": "0.4000", "size": "100.0000"}],
        },
    }
    list_markets_calls = []
    order_book_calls = []
    trade_sink_calls = []
    nav_sink_calls = []

    class FakeMarketDataClient:
        def list_markets(self, *, active, closed, limit, search=None):
            list_markets_calls.append(
                {
                    "active": active,
                    "closed": closed,
                    "limit": limit,
                    "search": search,
                }
            )
            return [raw_market]

        def get_order_book(self, *, token_id):
            order_book_calls.append(token_id)
            return raw_books[token_id]

    fake_client = FakeMarketDataClient()
    paper_journal_path = tmp_path / "artifacts" / "paper-trades.jsonl"
    archive_root = tmp_path / "raw"
    cycle_log = tmp_path / "cycle.jsonl"
    nav_log = tmp_path / "nav.jsonl"

    def fake_trade_sink(*, dsn, record, table_name):
        journal_lines = paper_journal_path.read_text(encoding="utf-8").splitlines()
        trade_sink_calls.append((dsn, record, table_name, len(journal_lines)))

    def fake_nav_sink(*, dsn, snapshot, table_name):
        nav_lines = nav_log.read_text(encoding="utf-8").splitlines()
        nav_sink_calls.append((dsn, snapshot, table_name, len(nav_lines)))

    exit_code = main(
        [
            "run",
            "--paper-execute",
            "--limit",
            "1",
            "--max-markets",
            "1",
            "--no-prefilter",
            "--archive-root",
            str(archive_root),
            "--cycle-log",
            str(cycle_log),
            "--nav-log",
            str(nav_log),
            "--starting-cash",
            "10000",
            "--max-iterations",
            "1",
        ],
        client_factory=lambda: fake_client,
        paper_trade_record_db_sink=fake_trade_sink,
        paper_nav_snapshot_db_sink=fake_nav_sink,
    )

    assert exit_code == 0
    assert list_markets_calls == [
        {
            "active": True,
            "closed": False,
            "limit": 1,
            "search": None,
        },
    ]
    assert order_book_calls[:2] == [yes_token_id, no_token_id]

    local_trades = PaperTradeJournal.read(paper_journal_path)
    assert len(local_trades) == 1
    local_trade = local_trades[0]
    assert isinstance(local_trade, PaperTradeRecord)
    assert paper_trade_record_to_db_row(local_trade).paper_only is True
    assert trade_sink_calls == [
        (
            trade_dsn,
            local_trade,
            "paper_trade_archive",
            1,
        ),
    ]
    _, trade_record, _, journal_line_count_at_sink = trade_sink_calls[0]
    assert isinstance(trade_record, PaperTradeRecord)
    assert paper_trade_record_to_db_row(trade_record).paper_only is True
    assert journal_line_count_at_sink == 1

    local_nav_snapshots = PaperNavLog.read(nav_log)
    assert len(local_nav_snapshots) == 1
    local_nav_snapshot = local_nav_snapshots[0]
    assert isinstance(local_nav_snapshot, PaperNavSnapshot)
    assert local_nav_snapshot.paper_only is True
    assert nav_sink_calls == [
        (
            nav_dsn,
            local_nav_snapshot,
            "paper_nav_archive",
            1,
        ),
    ]
    _, nav_snapshot, _, nav_line_count_at_sink = nav_sink_calls[0]
    assert isinstance(nav_snapshot, PaperNavSnapshot)
    assert nav_snapshot.paper_only is True
    assert nav_line_count_at_sink == 1

    captured = capsys.readouterr()
    assert "completed=1" in captured.out
    assert "failed=0" in captured.out
    assert trade_dsn not in captured.out
    assert trade_dsn not in captured.err
    assert nav_dsn not in captured.out
    assert nav_dsn not in captured.err


def test_run_cli_returns_one_when_loop_runner_fails(tmp_path, capsys):
    def broken_loop_runner(*, client, scan_config, cycle_config, starting_cash,
                           nav_log_path, cycle_report_log_path, repeat_mode,
                           interval_seconds, max_iterations,
                           cycle_snapshot_source=None, cycle_snapshot_sink=None,
                           paper_trade_record_sink=None, nav_snapshot_sink=None):
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
                            interval_seconds, max_iterations,
                            cycle_snapshot_source=None, cycle_snapshot_sink=None,
                            paper_trade_record_sink=None, nav_snapshot_sink=None):
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


def test_check_outcomes_cli_leaves_outcome_tracking_db_sink_inert_when_disabled(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv(OUTCOME_TRACKING_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(OUTCOME_TRACKING_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(OUTCOME_TRACKING_DB_TABLE_ENV_VAR, raising=False)
    sink_calls = []

    def forbidden_outcome_tracking_db_sink(**kwargs):
        sink_calls.append(kwargs)
        raise AssertionError("outcome tracking DB sink should not run")

    exit_code = main(
        [
            "check-outcomes",
            "--journal",
            str(tmp_path / "paper-trades.jsonl"),
        ],
        outcome_runner=lambda **_: _empty_outcome_report(),
        outcome_tracking_db_sink=forbidden_outcome_tracking_db_sink,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert sink_calls == []


def test_check_outcomes_cli_wires_outcome_tracking_db_sink_when_enabled(
    tmp_path,
    monkeypatch,
    capsys,
):
    fake_dsn = "postgresql://outcome-db.example.invalid/outcomes"
    monkeypatch.setenv(OUTCOME_TRACKING_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(OUTCOME_TRACKING_DB_DSN_ENV_VAR, fake_dsn)
    monkeypatch.setenv(
        OUTCOME_TRACKING_DB_TABLE_ENV_VAR,
        "outcome_tracking_archive",
    )
    report = _empty_outcome_report()
    sink_calls = []
    outcome_log = tmp_path / "outcomes.jsonl"

    def fake_outcome_tracking_db_sink(*, dsn, report, table_name):
        assert OutcomeTrackingLog.read(outcome_log) == (report,)
        sink_calls.append((dsn, report, table_name))

    exit_code = main(
        [
            "check-outcomes",
            "--journal",
            str(tmp_path / "paper-trades.jsonl"),
            "--outcome-log",
            str(outcome_log),
        ],
        outcome_runner=lambda **_: report,
        outcome_tracking_db_sink=fake_outcome_tracking_db_sink,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert sink_calls == [
        (
            fake_dsn,
            report,
            "outcome_tracking_archive",
        ),
    ]
    captured = capsys.readouterr()
    assert fake_dsn not in captured.out
    assert fake_dsn not in captured.err


def test_check_outcomes_cli_returns_one_when_outcome_tracking_db_sink_fails_without_dsn(
    tmp_path,
    monkeypatch,
    capsys,
):
    fake_dsn = "postgresql://outcome-db.example.invalid/outcomes"
    monkeypatch.setenv(OUTCOME_TRACKING_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(OUTCOME_TRACKING_DB_DSN_ENV_VAR, fake_dsn)
    monkeypatch.setenv(
        OUTCOME_TRACKING_DB_TABLE_ENV_VAR,
        "outcome_tracking_archive",
    )
    sink_calls = []

    def broken_outcome_tracking_db_sink(*, dsn, report, table_name):
        sink_calls.append((dsn, report, table_name))
        raise RuntimeError("database unavailable")

    exit_code = main(
        [
            "check-outcomes",
            "--journal",
            str(tmp_path / "paper-trades.jsonl"),
        ],
        outcome_runner=lambda **_: _empty_outcome_report(),
        outcome_tracking_db_sink=broken_outcome_tracking_db_sink,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1
    assert len(sink_calls) == 1
    captured = capsys.readouterr()
    assert "check-outcomes failed: database unavailable" in captured.err
    assert fake_dsn not in captured.out
    assert fake_dsn not in captured.err


def test_check_outcomes_cli_redacts_dsn_when_outcome_tracking_db_sink_fails(
    tmp_path,
    monkeypatch,
    capsys,
):
    fake_dsn = "postgresql://outcome-db.example.invalid/outcomes"
    monkeypatch.setenv(OUTCOME_TRACKING_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(OUTCOME_TRACKING_DB_DSN_ENV_VAR, fake_dsn)
    monkeypatch.setenv(
        OUTCOME_TRACKING_DB_TABLE_ENV_VAR,
        "outcome_tracking_archive",
    )

    def broken_outcome_tracking_db_sink(*, dsn, report, table_name):
        raise RuntimeError(f"could not connect to {dsn}")

    exit_code = main(
        [
            "check-outcomes",
            "--journal",
            str(tmp_path / "paper-trades.jsonl"),
        ],
        outcome_runner=lambda **_: _empty_outcome_report(),
        outcome_tracking_db_sink=broken_outcome_tracking_db_sink,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert fake_dsn not in captured.out
    assert fake_dsn not in captured.err
    assert "<redacted-dsn>" in captured.err


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
