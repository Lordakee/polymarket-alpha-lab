import json
import sys
from datetime import UTC, datetime, timedelta
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
from polymarket_alpha_lab.strategy_cycle_action_gated_queue_source import (
    build_strategy_cycle_action_gated_queue_source_report,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_db_row import (
    paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_db_row import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SCHEMA_VERSION,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority import (
    build_paper_action_gated_strategy_recommendation_queue_priority_report,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_psycopg_read import (
    PaperActionGatedStrategyRecommendationQueueReadOptions,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk import (
    PaperActionGatedStrategyRecommendationQueueRiskConfig,
    build_paper_action_gated_strategy_recommendation_queue_risk_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_config import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_trend_config import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_config import (
    ACTION_GATED_QUEUE_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_history_config import (
    ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_local_observability_trends_config import (
    LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR,
    LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR,
    LOCAL_OBSERVABILITY_TRENDS_DB_TABLE_ENV_VAR,
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
from polymarket_alpha_lab.supabase_paper_autonomous_screening_decision_support_gate_config import (
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_config import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_project_screening_rank_stability_config import (
    PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_DSN_ENV_VAR,
    PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_ENABLED_ENV_VAR,
    PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_research_packet_operator_flow_config import (
    PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR,
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


def test_paper_autonomous_screening_decision_support_gate_cli_prints_concise_summary(
    monkeypatch,
    capsys,
):
    command = "paper-autonomous-screening-decision-support-gate"
    rank_stability_dsn = "postgresql://rank-stability-gate.example.invalid/db"
    operator_flow_dsn = "postgresql://operator-flow-gate.example.invalid/db"
    action_queue_dsn = "postgresql://action-queue-gate.example.invalid/db"
    monkeypatch.setenv(
        PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_DSN_ENV_VAR,
        rank_stability_dsn,
    )
    monkeypatch.setenv(
        PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_TABLE_ENV_VAR,
        "paper_project_screening_rank_stability_reports",
    )
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(
        PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR,
        operator_flow_dsn,
    )
    monkeypatch.setenv(
        PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR,
        "paper_research_packet_operator_flow_reports",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
        action_queue_dsn,
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
        "paper_action_gated_queue_decision_support_reports",
    )
    calls = []

    def fake_gate_runner(**kwargs):
        calls.append(kwargs)
        assert kwargs["limit"] == 5
        gate_config = kwargs["gate_config"]
        assert (
            gate_config.config_version
            == "paper-autonomous-screening-decision-support-gate-v0"
        )
        assert gate_config.paper_only is True
        assert gate_config.report_only is True
        assert gate_config.readonly is True
        return SimpleNamespace(
            gate_status="pass",
            recommended_next_step=(
                "advance_paper_autonomous_screening_recommendations"
            ),
            queue_source_report_count=4,
            operator_flow_gate_status="pass",
            queue_risk_status="pass",
            queue_research_ready_count=4,
            trend_source_snapshot_count=None,
            rank_stability_status=None,
            gate_signal_counts=(
                SimpleNamespace(gate_signal="pass", report_count=4),
            ),
            reason_code_counts=(),
        )

    exit_code = main(
        [command, "--limit", "5"],
        paper_autonomous_screening_decision_support_gate_runner=fake_gate_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{command}: gate_status=pass "
            "recommended_next_step="
            "advance_paper_autonomous_screening_recommendations "
            "source_report_count=4 "
            "operator_flow_gate_status=pass "
            "queue_risk_status=pass "
            "queue_research_ready_count=4 "
            "trend_present=False "
            "rank_stability_present=False"
        ),
        "gate_signal_counts: pass=4",
        "reason_code_counts: none",
    ]
    assert captured.err == ""
    assert rank_stability_dsn not in captured.out
    assert operator_flow_dsn not in captured.out
    assert action_queue_dsn not in captured.out


def test_paper_autonomous_allocation_proposal_cli_prints_aggregate_summary(
    monkeypatch,
    capsys,
):
    command = "paper-autonomous-allocation-proposal"
    shared_dsn = "postgresql://allocation-proposal.example.invalid/db"
    screening_gate_table_name = "paper_autonomous_screening_decision_support_gate_reports"
    decision_support_table_name = (
        "paper_action_gated_queue_decision_support_reports"
    )
    source_queue_table_name = "paper_action_gated_strategy_recommendation_queue_reports"
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR,
        shared_dsn,
    )
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE_ENV_VAR,
        screening_gate_table_name,
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
        shared_dsn,
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
        decision_support_table_name,
    )
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, shared_dsn)
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR, source_queue_table_name)
    calls = []

    def fake_runner(**kwargs):
        calls.append(kwargs)
        assert kwargs["limit"] == 5
        assert kwargs["screening_gate_dsn"] == shared_dsn
        assert kwargs["screening_gate_table_name"] == screening_gate_table_name
        assert kwargs["action_gated_queue_decision_support_dsn"] == shared_dsn
        assert (
            kwargs["action_gated_queue_decision_support_table_name"]
            == decision_support_table_name
        )
        assert kwargs["source_queue_dsn"] == shared_dsn
        assert kwargs["source_queue_table_name"] == source_queue_table_name
        return SimpleNamespace(
            proposal_status="watch",
            recommended_next_step="hold_paper_autonomous_allocation_proposal",
            source_queue_count=3,
            screening_gate_status="pass",
            queue_risk_status="watch",
            allocation_report=SimpleNamespace(
                input_count=3,
                row_count=3,
                allocated_count=1,
                capped_count=1,
                no_budget_count=0,
                non_recommend_count=1,
                skipped_count=0,
                total_allocated_paper_notional=Decimal("25.000000"),
                remaining_paper_budget=Decimal("75.000000"),
                rows=(
                    SimpleNamespace(
                        market_slug="hidden-market-slug",
                        question="Will hidden market resolve yes?",
                    ),
                ),
            ),
            reason_code_counts=(
                SimpleNamespace(
                    reason_code="queue_risk_watch",
                    report_count=1,
                ),
                SimpleNamespace(
                    reason_code="allocation_capped",
                    report_count=1,
                ),
            ),
        )

    exit_code = main(
        [command, "--limit", "5"],
        paper_autonomous_allocation_proposal_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{command}: proposal_status=watch "
            "recommended_next_step=hold_paper_autonomous_allocation_proposal "
            "source_queue_count=3 "
            "screening_gate_status=pass "
            "queue_risk_status=watch "
            "input_count=3 "
            "row_count=3 "
            "allocated_count=1 "
            "capped_count=1 "
            "no_budget_count=0 "
            "non_recommend_count=1 "
            "skipped_count=0 "
            "total_allocated_paper_notional=25.000000 "
            "remaining_paper_budget=75.000000"
        ),
        "reason_code_counts: queue_risk_watch=1 allocation_capped=1",
    ]
    assert captured.err == ""
    for hidden in (
        shared_dsn,
        screening_gate_table_name,
        decision_support_table_name,
        source_queue_table_name,
        "hidden-market-slug",
        "Will hidden market resolve yes?",
    ):
        assert hidden not in captured.out
        assert hidden not in captured.err


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


def _paper_reason_trend_recommendation_row(
    market_slug: str,
    *,
    action: str,
    selected_side: str,
    scoring_side: str = "yes",
    score: Decimal,
    reason_codes: tuple[str, ...],
    assessment_status: str = "ready",
) -> PaperStrategyCandidateRecommendationRow:
    return PaperStrategyCandidateRecommendationRow(
        market_slug=market_slug,
        question=f"Will {market_slug} resolve yes?",
        action=action,
        assessment_status=assessment_status,
        readiness_status="pass",
        selected_side=selected_side,
        scoring_side=scoring_side,
        recommendation_score=score,
        reason_codes=reason_codes,
    )


def _paper_reason_trend_bundle_report(
    *,
    generated_at: datetime,
    rows: tuple[PaperStrategyCandidateRecommendationRow, ...],
) -> PaperStrategyRecommendationBundleReport:
    action_rank = {"recommend": 0, "watch": 1, "reject": 2}
    recommendation_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                action_rank[row.action],
                -row.recommendation_score,
                row.market_slug,
            ),
        ),
    )
    recommendation_report = PaperStrategyCandidateRecommendationReport(
        generated_at=generated_at,
        config_version="strategy-candidate-recommendation-v1",
        readiness_overall_status="pass",
        candidate_count=len(recommendation_rows),
        recommend_count=sum(
            1 for row in recommendation_rows if row.action == "recommend"
        ),
        watch_count=sum(1 for row in recommendation_rows if row.action == "watch"),
        reject_count=sum(1 for row in recommendation_rows if row.action == "reject"),
        recommendation_rows=recommendation_rows,
    )

    selection_rows = []
    for row in recommendation_rows:
        selected = row.action == "recommend"
        selected_notional = Decimal("5.000000") if selected else Decimal("0.000000")
        selection_rows.append(
            PaperStrategySelectionPolicyRow(
                market_slug=row.market_slug,
                question=row.question,
                source_action=row.action,
                selected_side=row.selected_side,
                recommendation_score=row.recommendation_score,
                decision="selected" if selected else "not_selected",
                suggested_position_notional=selected_notional,
                selected_position_notional=selected_notional,
                reason_codes=(
                    ("selected_by_policy", *row.reason_codes)
                    if selected
                    else (f"source_action_{row.action}", *row.reason_codes)
                ),
            ),
        )

    explanation_rows = tuple(
        PaperStrategyRecommendationExplanationRow(
            market_slug=row.market_slug,
            action=row.action,
            selected_side=row.selected_side,
            recommendation_score=row.recommendation_score,
            primary_reason_code=row.reason_codes[0],
            reason_codes=row.reason_codes,
            explanation=(
                f"{row.action} {row.selected_side} because {row.reason_codes[0]} "
                f"(score {row.recommendation_score})"
            ),
        )
        for row in recommendation_rows
    )
    selection_policy_report = PaperStrategySelectionPolicyReport(
        generated_at=generated_at,
        config_version="paper-strategy-selection-policy-v1",
        row_count=len(selection_rows),
        selected_count=sum(1 for row in selection_rows if row.decision == "selected"),
        skipped_count=0,
        not_selected_count=sum(
            1 for row in selection_rows if row.decision == "not_selected"
        ),
        total_selected_notional=sum(
            (row.selected_position_notional for row in selection_rows),
            Decimal("0.000000"),
        ),
        selection_rows=tuple(selection_rows),
    )
    explanation_report = PaperStrategyRecommendationExplanationReport(
        generated_at=generated_at,
        source_config_version=recommendation_report.config_version,
        recommendation_count=len(explanation_rows),
        recommend_count=sum(
            1 for row in explanation_rows if row.action == "recommend"
        ),
        watch_count=sum(1 for row in explanation_rows if row.action == "watch"),
        reject_count=sum(1 for row in explanation_rows if row.action == "reject"),
        explanation_rows=explanation_rows,
    )
    return PaperStrategyRecommendationBundleReport(
        generated_at=generated_at,
        config_version="strategy-recommendation-bundle-v1",
        candidate_count=recommendation_report.candidate_count,
        recommend_count=recommendation_report.recommend_count,
        selected_count=selection_policy_report.selected_count,
        total_selected_notional=selection_policy_report.total_selected_notional,
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


def test_paper_recommendation_reason_trend_cli_reads_bundle_log_report_only_without_client(
    tmp_path,
    capsys,
):
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _paper_reason_trend_bundle_report(
            generated_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
            rows=(
                _paper_reason_trend_recommendation_row(
                    "alpha-shift",
                    action="watch",
                    selected_side="yes",
                    score=Decimal("0.200000"),
                    reason_codes=("assessment_ready",),
                ),
                _paper_reason_trend_recommendation_row(
                    "beta-recommend",
                    action="recommend",
                    selected_side="yes",
                    score=Decimal("0.800000"),
                    reason_codes=("assessment_ready", "readiness_passed"),
                ),
                _paper_reason_trend_recommendation_row(
                    "gamma-reject",
                    action="reject",
                    selected_side="none",
                    scoring_side="none",
                    score=Decimal("0.000000"),
                    assessment_status="blocked",
                    reason_codes=("assessment_blocked",),
                ),
            ),
        ),
    )
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _paper_reason_trend_bundle_report(
            generated_at=datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
            rows=(
                _paper_reason_trend_recommendation_row(
                    "alpha-shift",
                    action="recommend",
                    selected_side="yes",
                    score=Decimal("0.900000"),
                    reason_codes=("assessment_ready", "readiness_passed"),
                ),
                _paper_reason_trend_recommendation_row(
                    "delta-watch",
                    action="watch",
                    selected_side="yes",
                    score=Decimal("0.100000"),
                    reason_codes=("readiness_watch",),
                ),
                _paper_reason_trend_recommendation_row(
                    "epsilon-reject",
                    action="reject",
                    selected_side="none",
                    scoring_side="none",
                    score=Decimal("0.000000"),
                    assessment_status="blocked",
                    reason_codes=("assessment_blocked",),
                ),
            ),
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
            "paper-recommendation-reason-trend",
            "--recommendation-log",
            str(recommendation_log),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert recommendation_log.read_bytes() == before
    captured = capsys.readouterr()
    assert "paper-recommendation-reason-trend:" in captured.out
    assert "source_reports=2" in captured.out
    assert "paper_only=True report_only=True readonly=True" in captured.out
    assert "recommend=2" in captured.out
    assert "watch=2" in captured.out
    assert "reject=2" in captured.out
    assert "assessment_ready" in captured.out
    assert "readiness_passed" in captured.out
    assert "transitions:" in captured.out
    assert "alpha-shift" in captured.out
    assert "watch->recommend" in captured.out


def _paper_reason_trend_minimal_bundle_report() -> PaperStrategyRecommendationBundleReport:
    return _paper_reason_trend_bundle_report(
        generated_at=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
        rows=(
            _paper_reason_trend_recommendation_row(
                "alpha-recommend",
                action="recommend",
                selected_side="yes",
                score=Decimal("0.800000"),
                reason_codes=("assessment_ready", "readiness_passed"),
            ),
        ),
    )


def test_paper_recommendation_reason_trend_cli_defaults_to_no_persist_without_db_config(
    monkeypatch,
    tmp_path,
    capsys,
):
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _paper_reason_trend_minimal_bundle_report(),
    )
    before = recommendation_log.read_bytes()
    config_calls = []
    sink_calls = []
    client_factory_calls = 0

    def forbidden_db_config():
        config_calls.append("from_db_env")
        raise AssertionError("reason trend DB config should not be read")

    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.supabase_paper_recommendation_reason_trend_config",
        SimpleNamespace(
            from_paper_recommendation_reason_trend_db_env=forbidden_db_config,
        ),
    )

    def forbidden_reason_trend_sink(dsn, report, *, table_name):
        sink_calls.append((dsn, report, table_name))
        raise AssertionError("reason trend DB sink should not run")

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-reason-trend",
            "--recommendation-log",
            str(recommendation_log),
        ],
        paper_recommendation_reason_trend_db_sink=forbidden_reason_trend_sink,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert config_calls == []
    assert sink_calls == []
    assert recommendation_log.read_bytes() == before
    captured = capsys.readouterr()
    assert "paper-recommendation-reason-trend:" in captured.out
    assert "persisted=" not in captured.out


def test_paper_recommendation_reason_trend_cli_persists_built_report_when_requested(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://reason-trend-secret.example.invalid/reports"
    table_name = "paper_reason_trend_archive"
    config_calls = _install_paper_recommendation_reason_trend_db_config(
        monkeypatch,
        dsn=dsn,
        table_name=table_name,
    )
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _paper_reason_trend_minimal_bundle_report(),
    )
    before = recommendation_log.read_bytes()
    sink_calls = []
    client_factory_calls = 0

    def fake_reason_trend_sink(sink_dsn, report, *, table_name):
        sink_calls.append((sink_dsn, report, table_name))
        return SimpleNamespace(report_sha256="c" * 64)

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-reason-trend",
            "--recommendation-log",
            str(recommendation_log),
            "--persist",
        ],
        paper_recommendation_reason_trend_db_sink=fake_reason_trend_sink,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert config_calls == ["from_db_env"]
    assert len(sink_calls) == 1
    sink_dsn, report, sink_table_name = sink_calls[0]
    assert sink_dsn == dsn
    assert sink_table_name == table_name
    assert report.source_report_count == 1
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert recommendation_log.read_bytes() == before
    captured = capsys.readouterr()
    assert "paper-recommendation-reason-trend:" in captured.out
    assert "persisted=" not in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert table_name not in captured.out


def test_paper_recommendation_reason_trend_cli_redacts_db_sink_error(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://reason-trend-secret.example.invalid/reports"
    table_name = "paper_reason_trend_archive"
    _install_paper_recommendation_reason_trend_db_config(
        monkeypatch,
        dsn=dsn,
        table_name=table_name,
    )
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _paper_reason_trend_minimal_bundle_report(),
    )

    def broken_reason_trend_sink(sink_dsn, report, *, table_name):
        raise RuntimeError(f"failed to write {sink_dsn} {table_name}")

    exit_code = main(
        [
            "paper-recommendation-reason-trend",
            "--recommendation-log",
            str(recommendation_log),
            "--persist",
        ],
        paper_recommendation_reason_trend_db_sink=broken_reason_trend_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "paper-recommendation-reason-trend failed: "
        "failed to write <redacted-dsn> <redacted-table>"
    ) in captured.err
    assert "paper-recommendation-reason-trend:" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert table_name not in captured.out
    assert table_name not in captured.err


@pytest.mark.parametrize(
    ("enabled", "dsn", "expected_message"),
    (
        (
            False,
            "postgresql://reason-trend-secret.example.invalid/reports",
            "paper recommendation reason trend DB to be enabled",
        ),
        (
            True,
            None,
            "a paper recommendation reason trend DB DSN",
        ),
    ),
)
def test_paper_recommendation_reason_trend_cli_validates_persist_db_config(
    monkeypatch,
    tmp_path,
    capsys,
    enabled,
    dsn,
    expected_message,
):
    table_name = "paper_reason_trend_archive"
    config_calls = _install_paper_recommendation_reason_trend_db_config(
        monkeypatch,
        enabled=enabled,
        dsn=dsn,
        table_name=table_name,
    )
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    append_paper_strategy_recommendation_bundle_log(
        recommendation_log,
        _paper_reason_trend_minimal_bundle_report(),
    )
    before = recommendation_log.read_bytes()
    sink_calls = []

    def forbidden_reason_trend_sink(sink_dsn, report, *, table_name):
        sink_calls.append((sink_dsn, report, table_name))
        raise AssertionError("reason trend DB sink should not run")

    exit_code = main(
        [
            "paper-recommendation-reason-trend",
            "--recommendation-log",
            str(recommendation_log),
            "--persist",
        ],
        paper_recommendation_reason_trend_db_sink=forbidden_reason_trend_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    assert config_calls == ["from_db_env"]
    assert sink_calls == []
    assert recommendation_log.read_bytes() == before
    captured = capsys.readouterr()
    assert "paper-recommendation-reason-trend:" in captured.out
    assert "paper-recommendation-reason-trend failed:" in captured.err
    assert expected_message in captured.err
    if dsn is not None:
        assert dsn not in captured.out
        assert dsn not in captured.err
    assert table_name not in captured.out
    assert table_name not in captured.err


def test_paper_recommendation_reason_trend_cli_empty_log_prints_zero_without_mutation(
    tmp_path,
    capsys,
):
    recommendation_log = tmp_path / "strategy-recommendations.jsonl"
    recommendation_log.write_text("", encoding="utf-8")
    before = recommendation_log.read_bytes()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-reason-trend",
            "--recommendation-log",
            str(recommendation_log),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert recommendation_log.read_bytes() == before
    captured = capsys.readouterr()
    assert "paper-recommendation-reason-trend:" in captured.out
    assert "source_reports=0" in captured.out


def test_paper_recommendation_reason_trend_cli_missing_log_returns_one_without_client(
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
            "paper-recommendation-reason-trend",
            "--recommendation-log",
            str(recommendation_log),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    assert not recommendation_log.exists()
    captured = capsys.readouterr()
    assert "paper-recommendation-reason-trend failed:" in captured.err
    assert "missing-strategy-recommendations.jsonl" in captured.err


def _paper_probability_side_edge_input_row(
    *,
    market_slug: str,
    side: str,
    forecast_probability: Decimal,
    side_price: Decimal,
    fee_cost_per_share: Decimal,
    spread_cost_per_share: Decimal = Decimal("0"),
    slippage_cost_per_share: Decimal = Decimal("0"),
    funding_cost_per_share: Decimal = Decimal("0"),
    finalization_cost_per_share: Decimal = Decimal("0"),
    time_cost_per_share: Decimal = Decimal("0"),
    risk_cost_per_share: Decimal = Decimal("0"),
    capital_cost_per_share: Decimal = Decimal("0"),
    requested_paper_shares: Decimal = Decimal("100.000000"),
    max_executable_shares: Decimal = Decimal("100.000000"),
    market_context_fresh: bool = True,
    settlement_context_fresh: bool = True,
    reason_codes: tuple[str, ...] = ("seed",),
) -> dict[str, object]:
    return {
        "market_slug": market_slug,
        "question": "Will alpha happen?",
        "side": side,
        "forecast_probability": str(forecast_probability),
        "side_price": str(side_price),
        "fee_cost_per_share": str(fee_cost_per_share),
        "spread_cost_per_share": str(spread_cost_per_share),
        "slippage_cost_per_share": str(slippage_cost_per_share),
        "funding_cost_per_share": str(funding_cost_per_share),
        "finalization_cost_per_share": str(finalization_cost_per_share),
        "time_cost_per_share": str(time_cost_per_share),
        "risk_cost_per_share": str(risk_cost_per_share),
        "capital_cost_per_share": str(capital_cost_per_share),
        "requested_paper_shares": str(requested_paper_shares),
        "max_executable_shares": str(max_executable_shares),
        "market_context_fresh": market_context_fresh,
        "settlement_context_fresh": settlement_context_fresh,
        "reason_codes": list(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _write_jsonl(path, rows):
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_json(path, payload):
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _paper_probability_side_edge_sample_rows() -> tuple[dict[str, object], ...]:
    return (
        _paper_probability_side_edge_input_row(
            market_slug="recommend-row",
            side="yes",
            forecast_probability=Decimal("0.640000"),
            side_price=Decimal("0.570000"),
            fee_cost_per_share=Decimal("0.010000"),
            spread_cost_per_share=Decimal("0.002000"),
            slippage_cost_per_share=Decimal("0.003000"),
            funding_cost_per_share=Decimal("0.004000"),
            finalization_cost_per_share=Decimal("0.005000"),
            time_cost_per_share=Decimal("0.006000"),
            risk_cost_per_share=Decimal("0.007000"),
            capital_cost_per_share=Decimal("0.008000"),
            reason_codes=("recommend_seed",),
        ),
        _paper_probability_side_edge_input_row(
            market_slug="watch-row",
            side="yes",
            forecast_probability=Decimal("0.640000"),
            side_price=Decimal("0.610000"),
            fee_cost_per_share=Decimal("0.010000"),
            market_context_fresh=False,
            reason_codes=("watch_seed",),
        ),
        _paper_probability_side_edge_input_row(
            market_slug="reject-row",
            side="yes",
            forecast_probability=Decimal("0.550000"),
            side_price=Decimal("0.570000"),
            fee_cost_per_share=Decimal("0.010000"),
            reason_codes=("reject_seed",),
        ),
    )


def _assert_paper_probability_side_edge_summary(
    output: str,
    *,
    input_rows: int = 3,
    row_count: int = 3,
    recommend: int = 1,
    watch: int = 1,
    reject: int = 1,
    reason_tokens: tuple[str, ...] = (
        "recommend_seed",
        "watch_seed",
        "reject_seed",
    ),
) -> None:
    assert "paper-probability-side-edge-report:" in output
    assert f"input_rows={input_rows}" in output
    assert f"row_count={row_count}" in output
    assert f"recommend={recommend}" in output
    assert f"watch={watch}" in output
    assert f"reject={reject}" in output
    assert "paper_only=True report_only=True readonly=True" in output
    for reason_token in reason_tokens:
        assert reason_token in output
    assert "reason_code_counts:" in output


def _paper_recommendation_queue_side_edge_row(
    market_slug: str,
    *,
    action: str,
    side_probability: Decimal,
    market_implied_probability: Decimal,
    total_cost_per_share: Decimal,
    requested_paper_shares: Decimal = Decimal("100.000000"),
    max_executable_shares: Decimal = Decimal("100.000000"),
    reason_codes: tuple[str, ...] = ("queue_seed",),
) -> dict[str, object]:
    gross_probability_edge = side_probability - market_implied_probability
    net_probability_edge = gross_probability_edge - total_cost_per_share
    if requested_paper_shares <= Decimal("0") or max_executable_shares <= Decimal("0"):
        depth_status = "no_depth"
        executable_paper_shares = Decimal("0.000000")
    elif max_executable_shares < requested_paper_shares:
        depth_status = "partial_depth"
        executable_paper_shares = max_executable_shares
    else:
        depth_status = "sufficient_depth"
        executable_paper_shares = requested_paper_shares
    recommendation_score = Decimal("0.000000") if action == "reject" else net_probability_edge
    return {
        "market_slug": market_slug,
        "question": f"Will {market_slug} resolve yes?",
        "side": "yes",
        "side_probability": str(side_probability.quantize(Decimal("0.000001"))),
        "market_implied_probability": str(
            market_implied_probability.quantize(Decimal("0.000001")),
        ),
        "gross_probability_edge": str(gross_probability_edge.quantize(Decimal("0.000001"))),
        "total_cost_per_share": str(total_cost_per_share.quantize(Decimal("0.000001"))),
        "net_probability_edge": str(net_probability_edge.quantize(Decimal("0.000001"))),
        "recommendation_score": str(recommendation_score.quantize(Decimal("0.000001"))),
        "action": action,
        "depth_status": depth_status,
        "requested_paper_shares": str(requested_paper_shares.quantize(Decimal("0.000001"))),
        "max_executable_shares": str(max_executable_shares.quantize(Decimal("0.000001"))),
        "executable_paper_shares": str(executable_paper_shares.quantize(Decimal("0.000001"))),
        "reason_codes": list(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _paper_recommendation_queue_sample_rows() -> tuple[dict[str, object], ...]:
    return (
        _paper_recommendation_queue_side_edge_row(
            "queue-recommend",
            action="recommend",
            side_probability=Decimal("0.740000"),
            market_implied_probability=Decimal("0.600000"),
            total_cost_per_share=Decimal("0.010000"),
            reason_codes=("queue_recommend_seed",),
        ),
        _paper_recommendation_queue_side_edge_row(
            "queue-watch",
            action="watch",
            side_probability=Decimal("0.640000"),
            market_implied_probability=Decimal("0.600000"),
            total_cost_per_share=Decimal("0.010000"),
            reason_codes=("queue_watch_seed",),
        ),
        _paper_recommendation_queue_side_edge_row(
            "queue-reject",
            action="reject",
            side_probability=Decimal("0.550000"),
            market_implied_probability=Decimal("0.570000"),
            total_cost_per_share=Decimal("0.010000"),
            reason_codes=("queue_reject_seed",),
        ),
    )


def _assert_paper_recommendation_queue_report_summary(
    output: str,
    *,
    input_count: int = 3,
    queue_count: int = 3,
    research_review_count: int = 1,
    await_fresh_context_count: int = 1,
    skip_count: int = 1,
    excluded_count: int = 0,
) -> None:
    assert "paper-recommendation-queue-report:" in output
    assert f"input_count={input_count}" in output
    assert f"queue_count={queue_count}" in output
    assert f"research_review={research_review_count}" in output
    assert f"await_fresh_context={await_fresh_context_count}" in output
    assert f"skip={skip_count}" in output
    assert f"excluded={excluded_count}" in output
    assert "paper_only=True report_only=True readonly=True" in output
    assert "reason_code_counts:" in output


def _paper_recommendation_risk_budget_sample_rows() -> tuple[dict[str, object], ...]:
    return (
        {
            "decision": "selected",
            "selected_position_notional": "12.345678",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "decision": "skipped",
            "selected_position_notional": "0.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "decision": "not_selected",
            "selected_position_notional": "0.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )


def _assert_paper_recommendation_risk_budget_report_summary(
    output: str,
    *,
    status: str = "pass",
    selected_count: int = 1,
    blocked_count: int = 0,
    zero_allocation_count: int = 2,
) -> None:
    assert "paper-recommendation-risk-budget-report:" in output
    assert f"status={status}" in output
    assert f"selected_count={selected_count}" in output
    assert f"blocked_count={blocked_count}" in output
    assert f"zero_allocation_count={zero_allocation_count}" in output
    assert "total_suggested_notional=" in output
    assert "remaining_total_notional=" in output
    assert "total_notional_utilization=" in output
    assert "largest_single_recommendation_share=" in output
    assert "nav_notional=" in output
    assert "paper_only=True report_only=True readonly=True" in output
    assert "reason_codes:" in output


def _install_paper_recommendation_queue_report_db_config(
    monkeypatch,
    *,
    enabled: bool = True,
    dsn: str | None,
    table_name: str,
) -> list[str]:
    config_calls: list[str] = []

    def from_db_env():
        config_calls.append("from_db_env")
        return SimpleNamespace(enabled=enabled, dsn=dsn, table_name=table_name)

    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab."
        "supabase_paper_probability_recommendation_queue_config",
        SimpleNamespace(
            from_paper_probability_recommendation_queue_db_env=from_db_env,
        ),
    )
    return config_calls


def _install_paper_recommendation_risk_budget_report_db_config(
    monkeypatch,
    *,
    enabled: bool = True,
    dsn: str | None,
    table_name: str,
) -> list[str]:
    config_calls: list[str] = []

    def from_db_env():
        config_calls.append("from_db_env")
        return SimpleNamespace(enabled=enabled, dsn=dsn, table_name=table_name)

    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.supabase_paper_recommendation_risk_budget_config",
        SimpleNamespace(
            from_paper_recommendation_risk_budget_db_env=from_db_env,
        ),
    )
    return config_calls


def _install_paper_recommendation_reason_trend_db_config(
    monkeypatch,
    *,
    enabled: bool = True,
    dsn: str | None,
    table_name: str,
) -> list[str]:
    config_calls: list[str] = []

    def from_db_env():
        config_calls.append("from_db_env")
        return SimpleNamespace(enabled=enabled, dsn=dsn, table_name=table_name)

    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.supabase_paper_recommendation_reason_trend_config",
        SimpleNamespace(
            from_paper_recommendation_reason_trend_db_env=from_db_env,
        ),
    )
    return config_calls


def test_paper_probability_side_edge_report_cli_reads_local_jsonl_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "paper-probability-side-edge.jsonl"
    _write_jsonl(input_path, _paper_probability_side_edge_sample_rows())
    before = input_path.read_bytes()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-probability-side-edge-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert input_path.read_bytes() == before
    captured = capsys.readouterr()
    _assert_paper_probability_side_edge_summary(captured.out)


def test_paper_probability_side_edge_report_cli_reads_local_json_array_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "paper-probability-side-edge.json"
    _write_json(input_path, list(_paper_probability_side_edge_sample_rows()))
    before = input_path.read_bytes()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-probability-side-edge-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert input_path.read_bytes() == before
    captured = capsys.readouterr()
    _assert_paper_probability_side_edge_summary(captured.out)


def test_paper_probability_side_edge_report_cli_reads_rows_object_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "paper-probability-side-edge.json"
    _write_json(input_path, {"rows": list(_paper_probability_side_edge_sample_rows())})
    before = input_path.read_bytes()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-probability-side-edge-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert input_path.read_bytes() == before
    captured = capsys.readouterr()
    _assert_paper_probability_side_edge_summary(captured.out)


def test_paper_probability_side_edge_report_cli_empty_input_prints_zero_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "empty-paper-probability-side-edge.jsonl"
    input_path.write_text("", encoding="utf-8")
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-probability-side-edge-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert input_path.read_bytes() == b""
    captured = capsys.readouterr()
    _assert_paper_probability_side_edge_summary(
        captured.out,
        input_rows=0,
        row_count=0,
        recommend=0,
        watch=0,
        reject=0,
        reason_tokens=(),
    )


@pytest.mark.parametrize("envelope_key", ("inputs", "input_rows"))
def test_paper_probability_side_edge_report_cli_reads_other_envelope_keys_without_client(
    tmp_path,
    capsys,
    envelope_key,
):
    input_path = tmp_path / f"paper-probability-side-edge-{envelope_key}.json"
    _write_json(
        input_path,
        {envelope_key: list(_paper_probability_side_edge_sample_rows())},
    )
    before = input_path.read_bytes()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-probability-side-edge-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert input_path.read_bytes() == before
    captured = capsys.readouterr()
    _assert_paper_probability_side_edge_summary(captured.out)


@pytest.mark.parametrize(
    ("payload", "expected_fragment"),
    (
        ([[]], "input row 1 must be a JSON object"),
        ([{"foo": "bar"}], "input row 1 is not a valid PaperSideEdgeAdapterInput"),
    ),
)
def test_paper_probability_side_edge_report_cli_invalid_row_returns_one_without_client(
    tmp_path,
    capsys,
    payload,
    expected_fragment,
):
    input_path = tmp_path / "invalid-paper-probability-side-edge.json"
    _write_json(input_path, payload)
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-probability-side-edge-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert "paper-probability-side-edge-report failed:" in captured.err
    assert expected_fragment in captured.err


def test_paper_probability_side_edge_report_cli_malformed_jsonl_returns_one_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "bad-paper-probability-side-edge.jsonl"
    _write_jsonl(input_path, (_paper_probability_side_edge_sample_rows()[0],))
    with input_path.open("a", encoding="utf-8") as handle:
        handle.write("{not-json}\n")
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-probability-side-edge-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert "paper-probability-side-edge-report failed:" in captured.err
    assert "bad-paper-probability-side-edge.jsonl" in captured.err
    assert "line 2 is not valid JSON" in captured.err


def test_paper_probability_side_edge_report_cli_missing_input_returns_one_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "missing-paper-probability-side-edge.jsonl"
    assert not input_path.exists()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-probability-side-edge-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    assert not input_path.exists()
    captured = capsys.readouterr()
    assert "paper-probability-side-edge-report failed:" in captured.err
    assert "missing-paper-probability-side-edge.jsonl" in captured.err


def test_paper_recommendation_queue_report_cli_reads_local_jsonl_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "paper-recommendation-queue.jsonl"
    _write_jsonl(input_path, _paper_recommendation_queue_sample_rows())
    before = input_path.read_bytes()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-queue-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert input_path.read_bytes() == before
    captured = capsys.readouterr()
    _assert_paper_recommendation_queue_report_summary(captured.out)
    assert "queue_recommend_seed" in captured.out
    assert "queue_watch_seed" in captured.out
    assert "queue_reject_seed" in captured.out


def test_paper_recommendation_queue_report_cli_defaults_to_no_persist_without_db_config(
    monkeypatch,
    tmp_path,
    capsys,
):
    input_path = tmp_path / "paper-recommendation-queue.jsonl"
    _write_jsonl(input_path, _paper_recommendation_queue_sample_rows())
    before = input_path.read_bytes()
    config_calls = []
    sink_calls = []
    client_factory_calls = 0

    def forbidden_db_config():
        config_calls.append("from_db_env")
        raise AssertionError("queue report DB config should not be read")

    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab."
        "supabase_paper_probability_recommendation_queue_config",
        SimpleNamespace(
            from_paper_probability_recommendation_queue_db_env=forbidden_db_config,
        ),
    )

    def forbidden_queue_report_sink(dsn, report, *, table_name):
        sink_calls.append((dsn, report, table_name))
        raise AssertionError("queue report DB sink should not run")

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-queue-report",
            "--input",
            str(input_path),
        ],
        paper_probability_recommendation_queue_db_sink=forbidden_queue_report_sink,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert config_calls == []
    assert sink_calls == []
    assert input_path.read_bytes() == before
    captured = capsys.readouterr()
    _assert_paper_recommendation_queue_report_summary(captured.out)
    assert "persisted=" not in captured.out


def test_paper_recommendation_queue_report_cli_persists_built_report_when_requested(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://queue-secret.example.invalid/reports"
    table_name = "paper_probability_queue_archive"
    config_calls = _install_paper_recommendation_queue_report_db_config(
        monkeypatch,
        dsn=dsn,
        table_name=table_name,
    )
    input_path = tmp_path / "paper-recommendation-queue.jsonl"
    _write_jsonl(input_path, _paper_recommendation_queue_sample_rows())
    before = input_path.read_bytes()
    sink_calls = []
    client_factory_calls = 0

    def fake_queue_report_sink(sink_dsn, report, *, table_name):
        sink_calls.append((sink_dsn, report, table_name))
        return SimpleNamespace(report_sha256="a" * 64)

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-queue-report",
            "--input",
            str(input_path),
            "--persist",
        ],
        paper_probability_recommendation_queue_db_sink=fake_queue_report_sink,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert config_calls == ["from_db_env"]
    assert len(sink_calls) == 1
    sink_dsn, report, sink_table_name = sink_calls[0]
    assert sink_dsn == dsn
    assert sink_table_name == table_name
    assert report.queue_count == 3
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert input_path.read_bytes() == before
    captured = capsys.readouterr()
    _assert_paper_recommendation_queue_report_summary(captured.out)
    assert "persisted=" not in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert table_name not in captured.out


def test_paper_recommendation_queue_report_cli_redacts_db_sink_error(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://queue-secret.example.invalid/reports"
    table_name = "paper_probability_queue_archive"
    _install_paper_recommendation_queue_report_db_config(
        monkeypatch,
        dsn=dsn,
        table_name=table_name,
    )
    input_path = tmp_path / "paper-recommendation-queue.jsonl"
    _write_jsonl(input_path, _paper_recommendation_queue_sample_rows())

    def broken_queue_report_sink(sink_dsn, report, *, table_name):
        raise RuntimeError(f"failed to write {sink_dsn} {table_name}")

    exit_code = main(
        [
            "paper-recommendation-queue-report",
            "--input",
            str(input_path),
            "--persist",
        ],
        paper_probability_recommendation_queue_db_sink=broken_queue_report_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "paper-recommendation-queue-report failed: "
        "failed to write <redacted-dsn> <redacted-table>"
    ) in captured.err
    _assert_paper_recommendation_queue_report_summary(captured.out)
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert table_name not in captured.out
    assert table_name not in captured.err


def test_paper_recommendation_queue_report_cli_empty_input_prints_zero_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "empty-paper-recommendation-queue.json"
    input_path.write_text("", encoding="utf-8")
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-queue-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert input_path.read_bytes() == b""
    captured = capsys.readouterr()
    _assert_paper_recommendation_queue_report_summary(
        captured.out,
        input_count=0,
        queue_count=0,
        research_review_count=0,
        await_fresh_context_count=0,
        skip_count=0,
        excluded_count=0,
    )


def test_paper_recommendation_queue_report_cli_invalid_row_returns_one_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "bad-paper-recommendation-queue.json"
    _write_json(input_path, [{"market_slug": "missing-fields"}])
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-queue-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert "paper-recommendation-queue-report failed:" in captured.err
    assert "bad-paper-recommendation-queue.json" in captured.err


def test_paper_recommendation_queue_report_cli_missing_input_returns_one_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "missing-paper-recommendation-queue.jsonl"
    assert not input_path.exists()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-queue-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    assert not input_path.exists()
    captured = capsys.readouterr()
    assert "paper-recommendation-queue-report failed:" in captured.err
    assert "missing-paper-recommendation-queue.jsonl" in captured.err


def test_paper_recommendation_risk_budget_report_cli_reads_local_json_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "paper-recommendation-risk-budget.json"
    _write_json(
        input_path,
        {"selection_rows": list(_paper_recommendation_risk_budget_sample_rows())},
    )
    before = input_path.read_bytes()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-risk-budget-report",
            "--input",
            str(input_path),
            "--nav-notional",
            "1000.000000",
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert input_path.read_bytes() == before
    captured = capsys.readouterr()
    _assert_paper_recommendation_risk_budget_report_summary(captured.out)
    assert "risk_budget_passed" in captured.out


def test_paper_recommendation_risk_budget_report_cli_defaults_to_no_persist_without_db_config(
    monkeypatch,
    tmp_path,
    capsys,
):
    input_path = tmp_path / "paper-recommendation-risk-budget.json"
    _write_json(
        input_path,
        {"selection_rows": list(_paper_recommendation_risk_budget_sample_rows())},
    )
    before = input_path.read_bytes()
    config_calls = []
    sink_calls = []
    client_factory_calls = 0

    def forbidden_db_config():
        config_calls.append("from_db_env")
        raise AssertionError("risk budget report DB config should not be read")

    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.supabase_paper_recommendation_risk_budget_config",
        SimpleNamespace(
            from_paper_recommendation_risk_budget_db_env=forbidden_db_config,
        ),
    )

    def forbidden_risk_budget_report_sink(dsn, report, *, table_name):
        sink_calls.append((dsn, report, table_name))
        raise AssertionError("risk budget report DB sink should not run")

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-risk-budget-report",
            "--input",
            str(input_path),
            "--nav-notional",
            "1000.000000",
        ],
        paper_recommendation_risk_budget_db_sink=forbidden_risk_budget_report_sink,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert config_calls == []
    assert sink_calls == []
    assert input_path.read_bytes() == before
    captured = capsys.readouterr()
    _assert_paper_recommendation_risk_budget_report_summary(captured.out)
    assert "persisted=" not in captured.out


def test_paper_recommendation_risk_budget_report_cli_persists_built_report_when_requested(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://risk-budget-secret.example.invalid/reports"
    table_name = "paper_risk_budget_archive"
    config_calls = _install_paper_recommendation_risk_budget_report_db_config(
        monkeypatch,
        dsn=dsn,
        table_name=table_name,
    )
    input_path = tmp_path / "paper-recommendation-risk-budget.json"
    _write_json(
        input_path,
        {"selection_rows": list(_paper_recommendation_risk_budget_sample_rows())},
    )
    before = input_path.read_bytes()
    sink_calls = []
    client_factory_calls = 0

    def fake_risk_budget_report_sink(sink_dsn, report, *, table_name):
        sink_calls.append((sink_dsn, report, table_name))
        return SimpleNamespace(report_sha256="b" * 64)

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-risk-budget-report",
            "--input",
            str(input_path),
            "--nav-notional",
            "1000.000000",
            "--persist",
        ],
        paper_recommendation_risk_budget_db_sink=fake_risk_budget_report_sink,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert config_calls == ["from_db_env"]
    assert len(sink_calls) == 1
    sink_dsn, report, sink_table_name = sink_calls[0]
    assert sink_dsn == dsn
    assert sink_table_name == table_name
    assert report.status == "pass"
    assert report.selected_count == 1
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert input_path.read_bytes() == before
    captured = capsys.readouterr()
    _assert_paper_recommendation_risk_budget_report_summary(captured.out)
    assert "persisted=" not in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert table_name not in captured.out


def test_paper_recommendation_risk_budget_report_cli_redacts_db_sink_error(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://risk-budget-secret.example.invalid/reports"
    table_name = "paper_risk_budget_archive"
    _install_paper_recommendation_risk_budget_report_db_config(
        monkeypatch,
        dsn=dsn,
        table_name=table_name,
    )
    input_path = tmp_path / "paper-recommendation-risk-budget.json"
    _write_json(
        input_path,
        {"selection_rows": list(_paper_recommendation_risk_budget_sample_rows())},
    )

    def broken_risk_budget_report_sink(sink_dsn, report, *, table_name):
        raise RuntimeError(f"failed to write {sink_dsn} {table_name}")

    exit_code = main(
        [
            "paper-recommendation-risk-budget-report",
            "--input",
            str(input_path),
            "--nav-notional",
            "1000.000000",
            "--persist",
        ],
        paper_recommendation_risk_budget_db_sink=broken_risk_budget_report_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "paper-recommendation-risk-budget-report failed: "
        "failed to write <redacted-dsn> <redacted-table>"
    ) in captured.err
    _assert_paper_recommendation_risk_budget_report_summary(captured.out)
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert table_name not in captured.out
    assert table_name not in captured.err


def test_paper_recommendation_risk_budget_report_cli_empty_input_prints_blocked_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "empty-paper-recommendation-risk-budget.jsonl"
    input_path.write_text("", encoding="utf-8")
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-risk-budget-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert input_path.read_bytes() == b""
    captured = capsys.readouterr()
    _assert_paper_recommendation_risk_budget_report_summary(
        captured.out,
        status="blocked",
        selected_count=0,
        blocked_count=1,
        zero_allocation_count=0,
    )
    assert "empty_selection" in captured.out


def test_paper_recommendation_risk_budget_report_cli_invalid_row_returns_one_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "bad-paper-recommendation-risk-budget.json"
    _write_json(input_path, [{"decision": "selected", "selected_position_notional": 1.0}])
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-risk-budget-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert "paper-recommendation-risk-budget-report failed:" in captured.err
    assert "bad-paper-recommendation-risk-budget.json" in captured.err
    assert "float" in captured.err


def test_paper_recommendation_risk_budget_report_cli_invalid_nav_notional_is_argparse_error(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "paper-recommendation-risk-budget.json"
    _write_json(
        input_path,
        {"selection_rows": list(_paper_recommendation_risk_budget_sample_rows())},
    )
    before = input_path.read_bytes()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "paper-recommendation-risk-budget-report",
                "--input",
                str(input_path),
                "--nav-notional",
                "not-a-decimal",
            ],
            client_factory=forbidden_client_factory,
        )

    assert exc_info.value.code == 2
    assert client_factory_calls == 0
    assert input_path.read_bytes() == before
    captured = capsys.readouterr()
    assert "--nav-notional" in captured.err
    assert "must be a decimal value" in captured.err


def test_paper_recommendation_risk_budget_report_cli_missing_input_returns_one_without_client(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "missing-paper-recommendation-risk-budget.jsonl"
    assert not input_path.exists()
    client_factory_calls = 0

    def forbidden_client_factory():
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-risk-budget-report",
            "--input",
            str(input_path),
        ],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    assert not input_path.exists()
    captured = capsys.readouterr()
    assert "paper-recommendation-risk-budget-report failed:" in captured.err
    assert "missing-paper-recommendation-risk-budget.jsonl" in captured.err


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
            reason_code_counts=(
                ("blocked_snapshot", 2),
                ("watch_snapshot", 1),
            ),
            latest_reason_codes=("blocked_snapshot", "thin_liquidity"),
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
    assert "trend_reason_codes: blocked_snapshot:2,watch_snapshot:1" in captured.out
    assert "latest_reason_codes: blocked_snapshot,thin_liquidity" in captured.out
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
    assert "trend_reason_codes:" in captured.out
    assert "blocked_snapshot:1" in captured.out
    assert "pass_snapshot:1" in captured.out
    assert "pipeline_final_status_pass:2" in captured.out
    assert (
        "latest_reason_codes: "
        "artifact_index_blocked,blocked_snapshot,pipeline_final_status_pass"
    ) in captured.out
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


def test_paper_recommendation_cycle_review_cli_requires_enabled_db_config(
    monkeypatch,
    capsys,
):
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", raising=False)
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", raising=False)

    def forbidden_runner(**kwargs):
        raise AssertionError("review runner should not run")

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    exit_code = main(
        ["paper-recommendation-cycle-review"],
        cycle_snapshot_db_review_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "paper-recommendation-cycle-review failed:" in captured.err
    assert "requires cycle snapshot DB to be enabled" in captured.err


def test_paper_recommendation_cycle_review_cli_reads_db_config_and_prints_summary(
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

    def fake_review_runner(
        *,
        dsn,
        generated_at,
        config,
        source_config_version,
        limit,
        table_name,
    ):
        calls.append(
            {
                "dsn": dsn,
                "generated_at": generated_at,
                "config": config,
                "source_config_version": source_config_version,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return SimpleNamespace(
            snapshot_count=3,
            latest_generated_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
            latest_final_status="watch",
            blocked_snapshot_count=1,
            watch_snapshot_count=1,
            pass_snapshot_count=1,
            blocked_artifact_count=2,
            watch_artifact_count=3,
            missing_required_artifact_names=("strategy_cycle_screening_report",),
            reason_code_counts=(
                SimpleNamespace(reason_code="artifact_index_blocked", count=1),
                SimpleNamespace(reason_code="watch_spread", count=2),
            ),
            review_status="watch",
            stale_history=False,
            paper_only=True,
            report_only=True,
            readonly=True,
        )

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-cycle-review",
            "--source-config-version",
            "paper-recommendation-cycle-snapshot-v0",
            "--limit",
            "25",
            "--stale-after-hours",
            "12.000000",
        ],
        cycle_snapshot_db_review_runner=fake_review_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["dsn"] == "test-dsn-value"
    assert calls[0]["config"].config_version == "paper-recommendation-cycle-review-v0"
    assert calls[0]["config"].stale_after_hours == Decimal("12.000000")
    assert (
        calls[0]["source_config_version"]
        == "paper-recommendation-cycle-snapshot-v0"
    )
    assert calls[0]["limit"] == 25
    assert calls[0]["table_name"] == "cycle_snapshot_archive"
    assert isinstance(calls[0]["generated_at"], datetime)

    captured = capsys.readouterr()
    assert "paper-recommendation-cycle-review:" in captured.out
    assert "snapshots=3" in captured.out
    assert "pass=1" in captured.out
    assert "watch=1" in captured.out
    assert "blocked=1" in captured.out
    assert "latest_status=watch" in captured.out
    assert "blocked_artifacts=2" in captured.out
    assert "watch_artifacts=3" in captured.out
    assert "missing_required_artifacts=strategy_cycle_screening_report" in captured.out
    assert "reason_codes=artifact_index_blocked:1,watch_spread:2" in captured.out
    assert "review_status=watch" in captured.out
    assert "test-dsn-value" not in captured.out
    assert "test-dsn-value" not in captured.err


def test_paper_recommendation_cycle_review_cli_quantizes_stale_after_hours(
    monkeypatch,
):
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", "test-dsn-value")
    calls = []

    def fake_review_runner(
        *,
        dsn,
        generated_at,
        config,
        source_config_version,
        limit,
        table_name,
    ):
        calls.append(config)
        return SimpleNamespace(
            snapshot_count=0,
            latest_generated_at=None,
            latest_final_status=None,
            blocked_snapshot_count=0,
            watch_snapshot_count=0,
            pass_snapshot_count=0,
            blocked_artifact_count=0,
            watch_artifact_count=0,
            missing_required_artifact_names=(),
            reason_code_counts=(),
            review_status="blocked",
            stale_history=False,
            paper_only=True,
            report_only=True,
            readonly=True,
        )

    exit_code = main(
        [
            "paper-recommendation-cycle-review",
            "--stale-after-hours",
            "6",
        ],
        cycle_snapshot_db_review_runner=fake_review_runner,
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0].stale_after_hours == Decimal("6.000000")
    assert calls[0].stale_after_hours.as_tuple().exponent == -6


def test_paper_recommendation_cycle_review_cli_default_psycopg_load_path_no_network(
    monkeypatch,
    capsys,
):
    fake_dsn = "postgresql://fake.example.invalid/cycle-review"
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", fake_dsn)
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_TABLE",
        "cycle_snapshot_archive",
    )

    config_version = "paper-recommendation-cycle-snapshot-v0"

    def snapshot_row(generated_at, *, final_status, artifact_status):
        pipeline_report = build_paper_recommendation_pipeline_report(
            generated_at=generated_at,
            config_version="paper-recommendation-pipeline-v0",
            stages=(
                PaperRecommendationPipelineStage(
                    stage_name=f"{final_status}_stage",
                    status=final_status,
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
                    artifact_name="strategy_cycle_blocked_counts",
                    config_version="paper-recommendation-artifact-index-v0",
                    generated_at=generated_at,
                    status=artifact_status,
                    item_count=1,
                    reason_codes=(f"{artifact_status}_artifact",),
                    flags=("paper_only", "report_only", "readonly"),
                    paper_only=True,
                    report_only=True,
                    readonly=True,
                ),
                SimpleNamespace(
                    artifact_name="strategy_cycle_screening_report",
                    config_version="paper-recommendation-artifact-index-v0",
                    generated_at=generated_at,
                    status="pass",
                    item_count=1,
                    reason_codes=("screening_ready_candidates",),
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
        snapshot_row(
            datetime(2026, 6, 19, 14, 0, tzinfo=UTC),
            final_status="watch",
            artifact_status="watch",
        ),
        snapshot_row(
            datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
            final_status="pass",
            artifact_status="pass",
        ),
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
            "paper-recommendation-cycle-review",
            "--source-config-version",
            config_version,
            "--limit",
            "2",
            "--stale-after-hours",
            "24.000000",
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
    assert "paper-recommendation-cycle-review:" in captured.out
    assert "snapshots=2" in captured.out
    assert "pass=1" in captured.out
    assert "watch=1" in captured.out
    assert "blocked=0" in captured.out
    assert "latest_status=watch" in captured.out
    assert "watch_artifacts=1" in captured.out
    assert "missing_required_artifacts=none" in captured.out
    assert "review_status=watch" in captured.out
    assert fake_dsn not in captured.out
    assert fake_dsn not in captured.err


def test_paper_recommendation_cycle_review_cli_runner_failure_redacts_dsn(
    monkeypatch,
    capsys,
):
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", "test-dsn-value")

    def broken_runner(**kwargs):
        raise RuntimeError("could not connect to test-dsn-value")

    exit_code = main(
        ["paper-recommendation-cycle-review"],
        cycle_snapshot_db_review_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "paper-recommendation-cycle-review failed: "
        "could not connect to <redacted-dsn>"
    ) in captured.err
    assert "test-dsn-value" not in captured.err


def test_paper_recommendation_cycle_action_gate_cli_requires_enabled_db_config(
    monkeypatch,
    capsys,
):
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", raising=False)
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", raising=False)

    def forbidden_runner(**kwargs):
        raise AssertionError("action gate runner should not run")

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    exit_code = main(
        ["paper-recommendation-cycle-action-gate"],
        cycle_snapshot_db_action_gate_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "paper-recommendation-cycle-action-gate failed:" in captured.err
    assert "requires cycle snapshot DB to be enabled" in captured.err


def test_paper_recommendation_cycle_action_gate_cli_reads_db_config_and_prints_summary(
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

    def fake_action_gate_runner(
        *,
        dsn,
        generated_at,
        review_config,
        action_gate_config,
        source_config_version,
        limit,
        table_name,
    ):
        calls.append(
            {
                "dsn": dsn,
                "generated_at": generated_at,
                "review_config": review_config,
                "action_gate_config": action_gate_config,
                "source_config_version": source_config_version,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return SimpleNamespace(
            source_config_version="paper-recommendation-cycle-review-v0",
            review_status="pass",
            latest_final_status="pass",
            action_status="research_ready",
            recommended_next_step="build_candidate_research_queue",
            missing_required_artifact_count=0,
            blocked_reason_count=0,
            watch_reason_count=0,
            reason_code_counts=(
                SimpleNamespace(reason_code="cycle_review_pass", count=1),
            ),
            paper_only=True,
            report_only=True,
            readonly=True,
        )

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [
            "paper-recommendation-cycle-action-gate",
            "--source-config-version",
            "paper-recommendation-cycle-snapshot-v0",
            "--limit",
            "25",
            "--stale-after-hours",
            "12.000000",
        ],
        cycle_snapshot_db_action_gate_runner=fake_action_gate_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["dsn"] == "test-dsn-value"
    assert (
        calls[0]["review_config"].config_version
        == "paper-recommendation-cycle-review-v0"
    )
    assert calls[0]["review_config"].stale_after_hours == Decimal("12.000000")
    assert (
        calls[0]["action_gate_config"].config_version
        == "paper-recommendation-cycle-action-gate-v0"
    )
    assert (
        calls[0]["source_config_version"]
        == "paper-recommendation-cycle-snapshot-v0"
    )
    assert calls[0]["limit"] == 25
    assert calls[0]["table_name"] == "cycle_snapshot_archive"
    assert isinstance(calls[0]["generated_at"], datetime)

    captured = capsys.readouterr()
    assert "paper-recommendation-cycle-action-gate:" in captured.out
    assert "review_status=pass" in captured.out
    assert "latest_status=pass" in captured.out
    assert "action_status=research_ready" in captured.out
    assert "next_step=build_candidate_research_queue" in captured.out
    assert "missing_required_artifacts=0" in captured.out
    assert "blocked_reasons=0" in captured.out
    assert "watch_reasons=0" in captured.out
    assert "reason_codes=cycle_review_pass:1" in captured.out
    assert "test-dsn-value" not in captured.out
    assert "test-dsn-value" not in captured.err


def test_paper_recommendation_cycle_action_gate_cli_default_psycopg_load_path_no_network(
    monkeypatch,
    capsys,
):
    fake_dsn = "postgresql://fake.example.invalid/action-gate"
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", fake_dsn)
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_TABLE",
        "cycle_snapshot_archive",
    )

    config_version = "paper-recommendation-cycle-snapshot-v0"

    def snapshot_row(generated_at, *, final_status, artifact_status):
        pipeline_report = build_paper_recommendation_pipeline_report(
            generated_at=generated_at,
            config_version="paper-recommendation-pipeline-v0",
            stages=(
                PaperRecommendationPipelineStage(
                    stage_name=f"{final_status}_stage",
                    status=final_status,
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
                    artifact_name="strategy_cycle_blocked_counts",
                    config_version="paper-recommendation-artifact-index-v0",
                    generated_at=generated_at,
                    status=artifact_status,
                    item_count=1,
                    reason_codes=(f"{artifact_status}_artifact",),
                    flags=("paper_only", "report_only", "readonly"),
                    paper_only=True,
                    report_only=True,
                    readonly=True,
                ),
                SimpleNamespace(
                    artifact_name="strategy_cycle_screening_report",
                    config_version="paper-recommendation-artifact-index-v0",
                    generated_at=generated_at,
                    status="pass",
                    item_count=1,
                    reason_codes=("screening_ready_candidates",),
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

    now = datetime.now(UTC)
    rows = (
        snapshot_row(
            now - timedelta(hours=1),
            final_status="pass",
            artifact_status="pass",
        ),
        snapshot_row(
            now - timedelta(hours=2),
            final_status="pass",
            artifact_status="pass",
        ),
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
            "paper-recommendation-cycle-action-gate",
            "--source-config-version",
            config_version,
            "--limit",
            "2",
            "--stale-after-hours",
            "24.000000",
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
    assert "paper-recommendation-cycle-action-gate:" in captured.out
    assert "review_status=pass" in captured.out
    assert "latest_status=pass" in captured.out
    assert "action_status=research_ready" in captured.out
    assert "next_step=build_candidate_research_queue" in captured.out
    assert fake_dsn not in captured.out
    assert fake_dsn not in captured.err


def test_paper_recommendation_cycle_action_gate_cli_runner_failure_redacts_dsn(
    monkeypatch,
    capsys,
):
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", "test-dsn-value")

    def broken_runner(**kwargs):
        raise RuntimeError("could not connect to test-dsn-value")

    exit_code = main(
        ["paper-recommendation-cycle-action-gate"],
        cycle_snapshot_db_action_gate_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "paper-recommendation-cycle-action-gate failed: "
        "could not connect to <redacted-dsn>"
    ) in captured.err
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


def _observability_trends_real_report():
    from polymarket_alpha_lab.local_observability_trends import (
        LocalObservabilityTrendsReport,
    )
    from polymarket_alpha_lab.nav_risk_trend import (
        PaperNavRiskTrendConfig,
        build_paper_nav_risk_trend_report,
    )
    from polymarket_alpha_lab.outcome_freshness import (
        OutcomeFreshnessConfig,
        build_outcome_freshness_report,
    )
    from polymarket_alpha_lab.paper_trade_cost_trend import (
        PaperTradeCostTrendConfig,
        build_paper_trade_cost_trend_report,
    )
    from polymarket_alpha_lab.strategy_evidence_trend import (
        PaperStrategyEvidenceTrendConfig,
        build_paper_strategy_evidence_trend_report,
    )

    generated_at = datetime(2026, 6, 20, 18, 30, tzinfo=UTC)
    return LocalObservabilityTrendsReport(
        generated_at=generated_at,
        config_version="local-observability-trends-v0",
        strategy_evidence_trend=build_paper_strategy_evidence_trend_report(
            (),
            config=PaperStrategyEvidenceTrendConfig(
                config_version="strategy-evidence-trend-v0",
            ),
            generated_at=generated_at,
        ),
        outcome_freshness=build_outcome_freshness_report(
            (),
            config=OutcomeFreshnessConfig(
                config_version="outcome-freshness-v0",
                stale_after_seconds=60,
            ),
            generated_at=generated_at,
        ),
        nav_risk_trend=build_paper_nav_risk_trend_report(
            (),
            config=PaperNavRiskTrendConfig(config_version="nav-risk-trend-v0"),
            generated_at=generated_at,
        ),
        paper_trade_cost_trend=build_paper_trade_cost_trend_report(
            (),
            config=PaperTradeCostTrendConfig(
                config_version="paper-trade-cost-trend-v0",
            ),
            generated_at=generated_at,
        ),
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


def test_observability_trends_cli_defaults_to_no_persist_without_db(
    monkeypatch,
    tmp_path,
    capsys,
):
    cycle_log, trade_log, nav_log, outcome_log = _write_strategy_audit_inputs(
        tmp_path,
        _resolved_outcome_report(),
    )
    monkeypatch.delenv(LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.setenv(
        LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR,
        "postgresql://observability.example.invalid/ignored",
    )
    sink_calls = []
    client_factory_calls = 0

    def fake_observability_trends_runner(**kwargs):
        return _observability_trends_stub_report()

    def forbidden_observability_trends_sink(**kwargs):
        sink_calls.append(kwargs)
        raise AssertionError("observability trends DB sink should not run")

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
        ],
        observability_trends_runner=fake_observability_trends_runner,
        local_observability_trends_db_sink=forbidden_observability_trends_sink,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert sink_calls == []
    captured = capsys.readouterr()
    assert "observability-trends:" in captured.out
    assert "persisted=False" in captured.out
    assert "observability.example.invalid" not in captured.out
    assert "observability.example.invalid" not in captured.err


def test_observability_trends_cli_persists_report_when_requested(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://observability.example.invalid/persist"
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        LOCAL_OBSERVABILITY_TRENDS_DB_TABLE_ENV_VAR,
        "local_observability_trends_archive",
    )
    cycle_log, trade_log, nav_log, outcome_log = _write_strategy_audit_inputs(
        tmp_path,
        _resolved_outcome_report(),
    )
    report = _observability_trends_stub_report()
    sink_calls = []

    def fake_observability_trends_runner(**kwargs):
        return report

    def fake_observability_trends_sink(*, dsn, report, table_name):
        sink_calls.append((dsn, report, table_name))
        return SimpleNamespace(report_sha256="a" * 64)

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
            "--persist",
        ],
        observability_trends_runner=fake_observability_trends_runner,
        local_observability_trends_db_sink=fake_observability_trends_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert sink_calls == [
        (dsn, report, "local_observability_trends_archive"),
    ]
    captured = capsys.readouterr()
    assert "observability-trends:" in captured.out
    assert "persisted=True" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "local_observability_trends_archive" not in captured.out


def test_observability_trends_cli_requires_db_config_before_persisting(
    monkeypatch,
    tmp_path,
    capsys,
):
    monkeypatch.delenv(LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(LOCAL_OBSERVABILITY_TRENDS_DB_TABLE_ENV_VAR, raising=False)
    cycle_log, trade_log, nav_log, outcome_log = _write_strategy_audit_inputs(
        tmp_path,
        _resolved_outcome_report(),
    )
    calls = []

    def forbidden_observability_trends_runner(**kwargs):
        calls.append(("runner", kwargs))
        raise AssertionError("observability trends runner should not run")

    def forbidden_observability_trends_sink(**kwargs):
        calls.append(("sink", kwargs))
        raise AssertionError("observability trends DB sink should not run")

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
            "--persist",
        ],
        observability_trends_runner=forbidden_observability_trends_runner,
        local_observability_trends_db_sink=forbidden_observability_trends_sink,
    )

    assert exit_code == 1
    assert calls == []
    captured = capsys.readouterr()
    assert "observability-trends failed:" in captured.err
    assert "persistence requires local observability trends DB to be enabled" in captured.err


def test_observability_trends_cli_redacts_dsn_on_persistence_failure(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://observability-secret.example.invalid/persist"
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR, dsn)
    cycle_log, trade_log, nav_log, outcome_log = _write_strategy_audit_inputs(
        tmp_path,
        _resolved_outcome_report(),
    )

    def fake_observability_trends_runner(**kwargs):
        return _observability_trends_stub_report()

    def broken_observability_trends_sink(*, dsn, report, table_name):
        raise RuntimeError(f"failed to persist to {dsn}")

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
            "--persist",
        ],
        observability_trends_runner=fake_observability_trends_runner,
        local_observability_trends_db_sink=broken_observability_trends_sink,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "observability-trends failed: failed to persist to <redacted-dsn>" in (
        captured.err
    )
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "observability-secret" not in captured.out
    assert "observability-secret" not in captured.err


def test_observability_trends_cli_default_psycopg_persist_path_no_network(
    monkeypatch,
    tmp_path,
    capsys,
):
    dsn = "postgresql://observability.example.invalid/persist"
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(LOCAL_OBSERVABILITY_TRENDS_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(
        LOCAL_OBSERVABILITY_TRENDS_DB_TABLE_ENV_VAR,
        "local_observability_trends_archive",
    )
    cycle_log, trade_log, nav_log, outcome_log = _write_strategy_audit_inputs(
        tmp_path,
        _resolved_outcome_report(),
    )
    report = _observability_trends_real_report()

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
    sys.modules.pop("polymarket_alpha_lab.local_observability_trends_store", None)
    sys.modules.pop("polymarket_alpha_lab.local_observability_trends_psycopg", None)

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
            "--persist",
        ],
        observability_trends_runner=lambda **kwargs: report,
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
    assert "INSERT INTO local_observability_trends_archive" in sql
    assert len(params) == 15
    assert isinstance(params[11], FakeJsonb)
    assert params[11].value["config_version"] == "local-observability-trends-v0"
    captured = capsys.readouterr()
    assert "observability-trends:" in captured.out
    assert "persisted=True" in captured.out
    assert dsn not in captured.out
    assert dsn not in captured.err
    assert "local_observability_trends_archive" not in captured.out


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
                         action_gated_queue_source=None,
                         action_gated_queue_sink=None,
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
                "action_gated_queue_source": action_gated_queue_source,
                "action_gated_queue_sink": action_gated_queue_sink,
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
    assert call["action_gated_queue_source"] is None
    assert call["action_gated_queue_sink"] is None
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
                         action_gated_queue_source=None,
                         action_gated_queue_sink=None,
                         paper_trade_record_sink=None, nav_snapshot_sink=None):
        calls.append(
            {
                "repeat_mode": repeat_mode,
                "interval_seconds": interval_seconds,
                "max_iterations": max_iterations,
                "cycle_snapshot_source": cycle_snapshot_source,
                "cycle_snapshot_sink": cycle_snapshot_sink,
                "action_gated_queue_source": action_gated_queue_source,
                "action_gated_queue_sink": action_gated_queue_sink,
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
            "action_gated_queue_source": None,
            "action_gated_queue_sink": None,
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
                         action_gated_queue_source=None,
                         action_gated_queue_sink=None,
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
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR, raising=False)
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
    assert "action_gated_queue_source" not in calls[0]
    assert "action_gated_queue_sink" not in calls[0]
    assert calls[0]["paper_trade_record_sink"] is None
    assert calls[0]["nav_snapshot_sink"] is None


def test_run_cli_leaves_action_gated_queue_db_disabled_by_default(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR, raising=False)
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
    assert "action_gated_queue_source" not in calls[0]
    assert "action_gated_queue_sink" not in calls[0]


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


def test_run_cli_wires_action_gated_queue_db_sink_when_env_enabled(
    tmp_path,
    monkeypatch,
    capsys,
):
    action_gated_dsn = "postgresql://action-gated.example.invalid/db"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, action_gated_dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR,
        "action_gated_queue_archive",
    )
    queue_report = SimpleNamespace(paper_only=True, report_only=True, readonly=True)
    sink_calls = []
    loop_calls = []

    def fake_loop_runner(**kwargs):
        loop_calls.append(kwargs)
        assert kwargs["action_gated_queue_source"] is fake_action_gated_queue_source
        assert kwargs["action_gated_queue_sink"] is not None
        report = kwargs["action_gated_queue_source"](
            cycle_report=object(),
            iteration_started_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
        )
        kwargs["action_gated_queue_sink"](report)
        return RunLoopSummary(
            iterations_completed=1,
            iterations_failed=0,
            first_iteration_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
            last_iteration_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
            last_error=None,
            action_gated_queues_persisted=1,
        )

    def fake_action_gated_queue_source(*, cycle_report, iteration_started_at):
        return queue_report

    def fake_action_gated_queue_db_sink(*, dsn, report, table_name):
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
        action_gated_queue_source=fake_action_gated_queue_source,
        action_gated_queue_db_sink=fake_action_gated_queue_db_sink,
    )

    assert exit_code == 0
    assert len(loop_calls) == 1
    assert sink_calls == [
        (
            action_gated_dsn,
            queue_report,
            "action_gated_queue_archive",
        ),
    ]
    captured = capsys.readouterr()
    assert "action_gated_queues_persisted=1" in captured.out
    assert action_gated_dsn not in captured.out
    assert action_gated_dsn not in captured.err


def test_run_cli_uses_default_action_gated_queue_source_when_db_enabled_without_injection(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, "test-action-gated-dsn")
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR,
        "action_gated_queue_archive",
    )
    calls = []

    def fake_loop_runner(**kwargs):
        calls.append(kwargs)
        assert (
            kwargs["action_gated_queue_source"]
            is build_strategy_cycle_action_gated_queue_source_report
        )
        assert kwargs["action_gated_queue_sink"] is not None
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
        action_gated_queue_db_sink=lambda **kwargs: None,
    )

    assert exit_code == 0
    assert len(calls) == 1


def test_run_cli_redacts_dsn_when_action_gated_queue_db_sink_failure_is_reported(
    tmp_path,
    monkeypatch,
    capsys,
):
    action_gated_dsn = "postgresql://action-gated.example.invalid/db"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, action_gated_dsn)
    queue_report = SimpleNamespace(paper_only=True, report_only=True, readonly=True)

    def fake_loop_runner(**kwargs):
        assert kwargs["action_gated_queue_sink"] is not None
        try:
            kwargs["action_gated_queue_sink"](queue_report)
        except Exception as exc:
            return RunLoopSummary(
                iterations_completed=0,
                iterations_failed=1,
                first_iteration_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
                last_iteration_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
                last_error=f"{type(exc).__name__}: {exc}",
            )
        raise AssertionError("sink should fail")

    def broken_action_gated_queue_db_sink(*, dsn, report, table_name):
        raise RuntimeError(f"could not connect to {dsn}")

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
        action_gated_queue_db_sink=broken_action_gated_queue_db_sink,
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert action_gated_dsn not in captured.out
    assert action_gated_dsn not in captured.err
    assert "last_error=RuntimeError: could not connect to <redacted-dsn>" in (
        captured.out
    )


def test_run_cli_prints_action_gated_queue_persisted_summary_when_present(
    tmp_path,
    capsys,
):
    def fake_loop_runner(**kwargs):
        return RunLoopSummary(
            iterations_completed=2,
            iterations_failed=0,
            first_iteration_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
            last_iteration_at=datetime(2026, 6, 20, 13, 0, tzinfo=UTC),
            last_error=None,
            action_gated_queues_persisted=2,
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
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "action_gated_queues_persisted=2" in captured.out


def test_action_gated_queue_decision_support_cli_requires_enabled_db_config(
    monkeypatch,
    capsys,
):
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR, raising=False)

    def forbidden_loader(**kwargs):
        raise AssertionError("read-only loader should not run")

    def forbidden_builder(**kwargs):
        raise AssertionError("pure builders should not run")

    exit_code = main(
        ["action-gated-queue-decision-support"],
        action_gated_queue_loader=forbidden_loader,
        action_gated_queue_priority_builder=forbidden_builder,
        action_gated_queue_risk_builder=forbidden_builder,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "action-gated-queue-decision-support failed:" in captured.err
    assert "requires action-gated queue read-only DB config to be enabled" in (
        captured.err
    )


def test_action_gated_queue_decision_support_cli_uses_injected_loader_and_builders(
    monkeypatch,
    capsys,
):
    action_gated_dsn = "postgresql://action-gated.example.invalid/db"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, action_gated_dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR,
        "action_gated_queue_archive",
    )
    source_reports = (
        SimpleNamespace(payload_json={"raw": "payload-secret-marker"}),
        SimpleNamespace(payload_json={"raw": "second-payload-secret"}),
    )
    loader_calls = []
    priority_calls = []
    risk_calls = []

    def fake_loader(dsn, *, options):
        loader_calls.append((dsn, options))
        return source_reports

    def fake_priority_builder(reports, *, generated_at):
        priority_calls.append((reports, generated_at))
        return SimpleNamespace(
            source_report_count=2,
            research_ready_count=1,
            watch_count=1,
            blocked_count=0,
            total_ready_notional=Decimal("123.456000"),
            top_research_priority_score=Decimal("4.000000"),
            average_research_priority_score=Decimal("2.000000"),
            priority_rows=(
                SimpleNamespace(
                    priority_rank=1,
                    source_generated_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
                    action_status="research_ready",
                    research_priority="research_review",
                    candidate_count=5,
                    ready_count=2,
                    total_ready_notional=Decimal("123.456000"),
                    research_priority_score=Decimal("4.000000"),
                ),
            ),
            paper_only=True,
            report_only=True,
            readonly=True,
        )

    def fake_risk_builder(queue_reports, *, config, generated_at):
        risk_calls.append((queue_reports, config, generated_at))
        return SimpleNamespace(
            status="watch",
            recommended_next_step="throttle_paper_research_queue",
            reason_codes=("near_total_ready_notional_cap",),
            source_queue_count=2,
            research_ready_source_count=1,
            watch_source_count=1,
            blocked_source_count=0,
            candidate_count=5,
            ready_count=2,
            watch_count=3,
            blocked_count=0,
            blocked_reason_count=0,
            watch_reason_count=1,
            total_ready_notional=Decimal("123.456000"),
            largest_queue_ready_notional=Decimal("100.000000"),
            total_ready_notional_utilization=Decimal("0.617280"),
            largest_queue_ready_notional_utilization=Decimal("0.500000"),
            source_config_versions=("action-gated-v0",),
            paper_only=True,
            report_only=True,
            readonly=True,
        )

    exit_code = main(
        [
            "action-gated-queue-decision-support",
            "--source-config-version",
            "paper-recommendation-cycle-action-gate-v0",
            "--action-status",
            "research_ready",
            "--limit",
            "25",
            "--max-total-ready-notional",
            "200",
            "--max-single-queue-ready-notional",
            "200",
            "--max-ready-candidate-count",
            "10",
            "--max-total-candidate-count",
            "20",
            "--throttle-utilization-threshold",
            "0.750000",
        ],
        action_gated_queue_loader=fake_loader,
        action_gated_queue_priority_builder=fake_priority_builder,
        action_gated_queue_risk_builder=fake_risk_builder,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(loader_calls) == 1
    assert loader_calls[0][0] == action_gated_dsn
    read_options = loader_calls[0][1]
    assert isinstance(read_options, PaperActionGatedStrategyRecommendationQueueReadOptions)
    assert (
        read_options.source_config_version
        == "paper-recommendation-cycle-action-gate-v0"
    )
    assert read_options.action_status == "research_ready"
    assert read_options.limit == 25
    assert read_options.table_name == "action_gated_queue_archive"

    assert priority_calls == [(source_reports, priority_calls[0][1])]
    assert isinstance(priority_calls[0][1], datetime)
    assert risk_calls[0][0] is source_reports
    assert risk_calls[0][1].config_version == "action-gated-queue-risk-v0"
    assert risk_calls[0][1].max_total_ready_notional == Decimal("200.000000")
    assert risk_calls[0][1].max_single_queue_ready_notional == Decimal("200.000000")
    assert risk_calls[0][1].max_ready_candidate_count == 10
    assert risk_calls[0][1].max_total_candidate_count == 20
    assert risk_calls[0][1].throttle_utilization_threshold == Decimal("0.750000")
    assert isinstance(risk_calls[0][2], datetime)

    captured = capsys.readouterr()
    assert "action-gated-queue-decision-support:" in captured.out
    assert "sources=2" in captured.out
    assert "priority_research_ready=1" in captured.out
    assert "priority_watch=1" in captured.out
    assert "priority_blocked=0" in captured.out
    assert "risk_status=watch" in captured.out
    assert "risk_next_step=throttle_paper_research_queue" in captured.out
    assert "risk_reasons=near_total_ready_notional_cap" in captured.out
    assert "queue_risk:" in captured.out
    assert "source_config_versions=action-gated-v0" in captured.out
    assert "top_priority:" in captured.out
    assert "payload-secret-marker" not in captured.out
    assert "second-payload-secret" not in captured.out
    assert action_gated_dsn not in captured.out
    assert action_gated_dsn not in captured.err


def _watch_action_gated_queue_report(
    generated_at: datetime,
) -> PaperActionGatedStrategyRecommendationQueueReport:
    return PaperActionGatedStrategyRecommendationQueueReport(
        generated_at=generated_at,
        config_version="action-gated-queue-v0",
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status="watch",
        recommended_next_step="await_fresh_cycle_evidence",
        reason_code_counts=(
            PaperRecommendationCycleActionGateReasonCodeCount(
                reason_code="cycle_review_watch",
                count=1,
            ),
        ),
        candidate_count=0,
        ready_count=0,
        watch_count=0,
        blocked_count=0,
        total_ready_notional=Decimal("0"),
    )


def _blocked_action_gated_queue_report(
    generated_at: datetime,
) -> PaperActionGatedStrategyRecommendationQueueReport:
    return PaperActionGatedStrategyRecommendationQueueReport(
        generated_at=generated_at,
        config_version="action-gated-queue-v0",
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status="blocked",
        recommended_next_step="repair_cycle_evidence",
        reason_code_counts=(
            PaperRecommendationCycleActionGateReasonCodeCount(
                reason_code="cycle_review_blocked",
                count=1,
            ),
        ),
        candidate_count=0,
        ready_count=0,
        watch_count=0,
        blocked_count=0,
        total_ready_notional=Decimal("0"),
    )


def test_action_gated_queue_decision_support_cli_default_builder_wiring(
    monkeypatch,
    capsys,
):
    action_gated_dsn = "postgresql://action-gated.example.invalid/db"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, action_gated_dsn)
    reports = (
        _blocked_action_gated_queue_report(
            datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
        ),
        _watch_action_gated_queue_report(
            datetime(2026, 6, 20, 11, 0, tzinfo=UTC),
        ),
    )

    def fake_loader(dsn, *, options):
        assert dsn == action_gated_dsn
        assert options.limit == 100
        return reports

    exit_code = main(
        ["action-gated-queue-decision-support"],
        action_gated_queue_loader=fake_loader,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "action-gated-queue-decision-support:" in captured.out
    assert "sources=2" in captured.out
    assert "priority_research_ready=0" in captured.out
    assert "priority_watch=1" in captured.out
    assert "priority_blocked=1" in captured.out
    assert "risk_status=blocked" in captured.out
    assert "risk_next_step=block_paper_research_queue" in captured.out
    assert "risk_reasons=source_queue_blocked" in captured.out
    assert "top_priority:" in captured.out
    assert "action_status=watch" in captured.out
    assert action_gated_dsn not in captured.out
    assert action_gated_dsn not in captured.err


def test_action_gated_queue_decision_support_cli_redacts_dsn_on_loader_failure(
    monkeypatch,
    capsys,
):
    action_gated_dsn = "postgresql://action-gated.example.invalid/db"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, action_gated_dsn)

    def broken_loader(dsn, *, options):
        raise RuntimeError(f"could not connect to {dsn}")

    exit_code = main(
        ["action-gated-queue-decision-support"],
        action_gated_queue_loader=broken_loader,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "action-gated-queue-decision-support failed: "
        "could not connect to <redacted-dsn>"
    ) in captured.err
    assert action_gated_dsn not in captured.out
    assert action_gated_dsn not in captured.err


def test_action_gated_queue_decision_support_cli_rejects_dsn_flag(capsys):
    with pytest.raises(SystemExit):
        main(
            [
                "action-gated-queue-decision-support",
                "--action-gated-queue-db-dsn",
                "forbidden-value",
            ],
            client_factory=lambda: "fake-client",
        )

    captured = capsys.readouterr()
    assert "unrecognized arguments: --action-gated-queue-db-dsn" in captured.err


def test_action_gated_queue_decision_support_trend_cli_requires_source_db_config(
    monkeypatch,
    capsys,
):
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
        raising=False,
    )

    def forbidden_runner(**kwargs):
        raise AssertionError("trend runner should not run")

    exit_code = main(
        ["action-gated-queue-decision-support-trend"],
        action_gated_queue_decision_support_trend_runner=forbidden_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "action-gated-queue-decision-support-trend failed:" in captured.err
    assert "requires action-gated queue decision-support DB to be enabled" in (
        captured.err
    )


def test_action_gated_queue_decision_support_trend_cli_uses_injected_runner(
    monkeypatch,
    capsys,
):
    source_dsn = "postgresql://decision-support.example.invalid/source"
    trend_dsn = "postgresql://decision-support.example.invalid/trend"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
        "decision_support_archive",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR,
        trend_dsn,
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR,
        "trend_reports_archive",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR,
        "trend_sources_archive",
    )
    calls = []

    def fake_trend_runner(
        *,
        source_dsn,
        generated_at,
        config_version,
        source_limit,
        source_risk_status,
        source_table_name,
        persist,
        trend_dsn,
        trend_reports_table_name,
        trend_sources_table_name,
    ):
        calls.append(
            {
                "source_dsn": source_dsn,
                "generated_at": generated_at,
                "config_version": config_version,
                "source_limit": source_limit,
                "source_risk_status": source_risk_status,
                "source_table_name": source_table_name,
                "persist": persist,
                "trend_dsn": trend_dsn,
                "trend_reports_table_name": trend_reports_table_name,
                "trend_sources_table_name": trend_sources_table_name,
            },
        )
        return (
            SimpleNamespace(
                source_snapshot_count=3,
                first_generated_at=datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
                latest_generated_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
                latest_risk_status="watch",
                risk_status_counts=(("pass", 1), ("watch", 2), ("blocked", 0)),
                ready_notional_delta=Decimal("12.500000"),
                top_priority_score_delta=Decimal("1.000000"),
                average_priority_score_delta=Decimal("0.500000"),
                duplicate_generated_at_count=1,
                repeated_reason_code_counts=(("source_queue_watch", 2),),
                paper_only=True,
                report_only=True,
                readonly=True,
            ),
            True,
        )

    exit_code = main(
        [
            "action-gated-queue-decision-support-trend",
            "--source-limit",
            "25",
            "--source-risk-status",
            "watch",
            "--persist",
        ],
        action_gated_queue_decision_support_trend_runner=fake_trend_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["source_dsn"] == source_dsn
    assert isinstance(calls[0]["generated_at"], datetime)
    assert calls[0]["config_version"] == (
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_SCHEMA_VERSION
    )
    assert calls[0]["source_limit"] == 25
    assert calls[0]["source_risk_status"] == "watch"
    assert calls[0]["source_table_name"] == "decision_support_archive"
    assert calls[0]["persist"] is True
    assert calls[0]["trend_dsn"] == trend_dsn
    assert calls[0]["trend_reports_table_name"] == "trend_reports_archive"
    assert calls[0]["trend_sources_table_name"] == "trend_sources_archive"

    captured = capsys.readouterr()
    assert "action-gated-queue-decision-support-trend:" in captured.out
    assert "snapshots=3" in captured.out
    assert "latest_risk_status=watch" in captured.out
    assert "pass=1" in captured.out
    assert "watch=2" in captured.out
    assert "blocked=0" in captured.out
    assert "ready_notional_delta=12.500000" in captured.out
    assert "duplicate_generated_at_count=1" in captured.out
    assert "persisted=True" in captured.out
    assert "trend_reason_codes: source_queue_watch:2" in captured.out
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert trend_dsn not in captured.out
    assert trend_dsn not in captured.err


def test_action_gated_queue_decision_support_trend_cli_injected_runner_requires_trend_db_when_persisting(
    monkeypatch,
    capsys,
):
    source_dsn = "postgresql://decision-support.example.invalid/source"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
        "decision_support_archive",
    )
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR,
        raising=False,
    )

    def forbidden_runner(**kwargs):
        raise AssertionError("trend runner should not run")

    exit_code = main(
        [
            "action-gated-queue-decision-support-trend",
            "--persist",
        ],
        action_gated_queue_decision_support_trend_runner=forbidden_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "action-gated-queue-decision-support-trend failed:" in captured.err
    assert "trend DB to be enabled" in captured.err


def test_action_gated_queue_decision_support_trend_cli_injected_runner_redacts_both_dsns(
    monkeypatch,
    capsys,
):
    source_dsn = "postgresql://decision-support.example.invalid/source"
    trend_dsn = "postgresql://decision-support.example.invalid/trend"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
        "decision_support_archive",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR,
        trend_dsn,
    )

    def failing_runner(**kwargs):
        raise RuntimeError(f"source={source_dsn} trend={trend_dsn}")

    exit_code = main(
        [
            "action-gated-queue-decision-support-trend",
            "--persist",
        ],
        action_gated_queue_decision_support_trend_runner=failing_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert source_dsn not in captured.err
    assert trend_dsn not in captured.err
    assert "<redacted-dsn>" in captured.err


def _decision_support_snapshot_db_record(
    generated_at: datetime,
    *,
    queue_reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
):
    priority_report = (
        build_paper_action_gated_strategy_recommendation_queue_priority_report(
            queue_reports,
            generated_at=generated_at,
        )
    )
    risk_report = build_paper_action_gated_strategy_recommendation_queue_risk_report(
        queue_reports,
        config=PaperActionGatedStrategyRecommendationQueueRiskConfig(
            config_version="action-gated-queue-risk-v0",
            max_total_ready_notional=Decimal("1000.000000"),
            max_single_queue_ready_notional=Decimal("500.000000"),
            max_ready_candidate_count=100,
            max_total_candidate_count=200,
            throttle_utilization_threshold=Decimal("0.900000"),
        ),
        generated_at=generated_at,
    )
    row = paper_action_gated_strategy_recommendation_queue_decision_support_to_db_row(
        priority_report,
        risk_report,
    )
    return (
        row.snapshot_sha256,
        row.generated_at,
        row.priority_source_report_count,
        row.priority_research_ready_count,
        row.priority_watch_count,
        row.priority_blocked_count,
        row.priority_total_ready_notional,
        row.top_research_priority_score,
        row.average_research_priority_score,
        row.risk_config_version,
        row.risk_status,
        row.risk_recommended_next_step,
        row.risk_source_queue_count,
        row.risk_candidate_count,
        row.risk_ready_count,
        row.risk_total_ready_notional,
        row.risk_largest_queue_ready_notional,
        list(row.risk_reason_codes_json),
        row.priority_payload_json,
        row.risk_payload_json,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def test_action_gated_queue_decision_support_trend_cli_default_psycopg_paths_no_network(
    monkeypatch,
    capsys,
):
    source_dsn = "postgresql://decision-support.example.invalid/source"
    trend_dsn = "postgresql://decision-support.example.invalid/trend"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
        "decision_support_archive",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR,
        trend_dsn,
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_REPORTS_TABLE_ENV_VAR,
        "trend_reports_archive",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_SOURCES_TABLE_ENV_VAR,
        "trend_sources_archive",
    )

    first_at = datetime(2026, 6, 20, 10, 0, tzinfo=UTC)
    latest_at = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
    source_records = (
        _decision_support_snapshot_db_record(
            latest_at,
            queue_reports=(_watch_action_gated_queue_report(latest_at),),
        ),
        _decision_support_snapshot_db_record(
            first_at,
            queue_reports=(_blocked_action_gated_queue_report(first_at),),
        ),
    )

    class FakeCursor:
        def __init__(self, rows=()):
            self.rows = rows
            self.calls = []
            self.closed = False

        def execute(self, sql, params=()):
            self.calls.append((" ".join(sql.split()), params))

        def fetchall(self):
            return self.rows

        def close(self):
            self.closed = True

    class FakeConnection:
        def __init__(self, rows=()):
            self.cursor_instance = FakeCursor(rows)
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

    source_connection = FakeConnection(source_records)
    trend_connection = FakeConnection()
    connect_calls = []

    def fake_connect(dsn):
        connect_calls.append(dsn)
        if dsn == source_dsn:
            return source_connection
        if dsn == trend_dsn:
            return trend_connection
        raise AssertionError(f"unexpected dsn: {dsn}")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setitem(
        sys.modules,
        "psycopg.types.json",
        SimpleNamespace(Jsonb=FakeJsonb),
    )
    sys.modules.pop(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_store",
        None,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_psycopg",
        None,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_store",
        None,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_psycopg",
        None,
    )

    exit_code = main(
        [
            "action-gated-queue-decision-support-trend",
            "--source-limit",
            "2",
            "--persist",
        ],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert connect_calls == [source_dsn, trend_dsn]
    assert source_connection.commit_count == 1
    assert source_connection.rollback_count == 0
    assert source_connection.close_count == 1
    assert trend_connection.commit_count == 1
    assert trend_connection.rollback_count == 0
    assert trend_connection.close_count == 1
    source_sql, source_params = source_connection.cursor_instance.calls[0]
    assert "FROM decision_support_archive" in source_sql
    assert (
        "ORDER BY generated_at DESC, inserted_at DESC, snapshot_sha256 DESC"
        in source_sql
    )
    assert source_params == (2,)
    trend_sql_calls = tuple(call[0] for call in trend_connection.cursor_instance.calls)
    assert any("INSERT INTO trend_reports_archive" in sql for sql in trend_sql_calls)
    assert sum("INSERT INTO trend_sources_archive" in sql for sql in trend_sql_calls) == 2

    captured = capsys.readouterr()
    assert "action-gated-queue-decision-support-trend:" in captured.out
    assert "snapshots=2" in captured.out
    assert "latest_risk_status=watch" in captured.out
    assert "pass=0" in captured.out
    assert "watch=1" in captured.out
    assert "blocked=1" in captured.out
    assert "persisted=True" in captured.out
    assert "trend_reason_codes:" in captured.out
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert trend_dsn not in captured.out
    assert trend_dsn not in captured.err


def test_action_gated_queue_decision_support_trend_cli_default_psycopg_no_persist_uses_only_source_db(
    monkeypatch,
    capsys,
):
    source_dsn = "postgresql://decision-support.example.invalid/source"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
        "decision_support_archive",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR,
        "false",
    )
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR,
        raising=False,
    )

    first_at = datetime(2026, 6, 20, 10, 0, tzinfo=UTC)
    latest_at = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
    source_records = (
        _decision_support_snapshot_db_record(
            latest_at,
            queue_reports=(_watch_action_gated_queue_report(latest_at),),
        ),
        _decision_support_snapshot_db_record(
            first_at,
            queue_reports=(_blocked_action_gated_queue_report(first_at),),
        ),
    )

    class FakeCursor:
        def __init__(self, rows=()):
            self.rows = rows
            self.calls = []
            self.closed = False

        def execute(self, sql, params=()):
            self.calls.append((" ".join(sql.split()), params))

        def fetchall(self):
            return self.rows

        def close(self):
            self.closed = True

    class FakeConnection:
        def __init__(self, rows=()):
            self.cursor_instance = FakeCursor(rows)
            self.commit_count = 0
            self.rollback_count = 0
            self.close_count = 0

        def cursor(self):
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

    source_connection = FakeConnection(source_records)
    connect_calls = []

    def fake_connect(dsn):
        connect_calls.append(dsn)
        if dsn == source_dsn:
            return source_connection
        raise AssertionError(f"unexpected dsn: {dsn}")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setitem(
        sys.modules,
        "psycopg.types.json",
        SimpleNamespace(Jsonb=FakeJsonb),
    )
    sys.modules.pop(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_store",
        None,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_psycopg",
        None,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_store",
        None,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_psycopg",
        None,
    )

    exit_code = main(
        [
            "action-gated-queue-decision-support-trend",
            "--source-limit",
            "2",
        ],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert connect_calls == [source_dsn]
    captured = capsys.readouterr()
    assert "persisted=False" in captured.out
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err


def test_action_gated_queue_decision_support_trend_cli_injected_runner_defaults_to_no_persist_without_trend_db(
    monkeypatch,
    capsys,
):
    source_dsn = "postgresql://decision-support.example.invalid/source"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
        "decision_support_archive",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED_ENV_VAR,
        "false",
    )
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_DSN_ENV_VAR,
        raising=False,
    )
    calls = []

    def fake_trend_runner(
        *,
        source_dsn,
        generated_at,
        config_version,
        source_limit,
        source_risk_status,
        source_table_name,
        persist,
        trend_dsn,
        trend_reports_table_name,
        trend_sources_table_name,
    ):
        calls.append(
            {
                "source_dsn": source_dsn,
                "generated_at": generated_at,
                "config_version": config_version,
                "source_limit": source_limit,
                "source_risk_status": source_risk_status,
                "source_table_name": source_table_name,
                "persist": persist,
                "trend_dsn": trend_dsn,
                "trend_reports_table_name": trend_reports_table_name,
                "trend_sources_table_name": trend_sources_table_name,
            },
        )
        return (
            SimpleNamespace(
                source_snapshot_count=2,
                first_generated_at=datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
                latest_generated_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
                latest_risk_status="watch",
                risk_status_counts=(("watch", 1), ("blocked", 1)),
                ready_notional_delta=Decimal("0.000000"),
                top_priority_score_delta=Decimal("0.000000"),
                average_priority_score_delta=Decimal("0.000000"),
                duplicate_generated_at_count=0,
                repeated_reason_code_counts=(),
                paper_only=True,
                report_only=True,
                readonly=True,
            ),
            False,
        )

    exit_code = main(
        [
            "action-gated-queue-decision-support-trend",
            "--source-limit",
            "2",
        ],
        action_gated_queue_decision_support_trend_runner=fake_trend_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["source_dsn"] == source_dsn
    assert calls[0]["persist"] is False
    assert calls[0]["trend_dsn"] is None
    assert calls[0]["trend_reports_table_name"] is None
    assert calls[0]["trend_sources_table_name"] is None
    captured = capsys.readouterr()
    assert "persisted=False" in captured.out


def test_action_gated_queue_decision_support_trend_cli_rejects_dsn_flag(capsys):
    with pytest.raises(SystemExit):
        main(
            [
                "action-gated-queue-decision-support-trend",
                "--decision-support-db-dsn",
                "forbidden-value",
            ],
            client_factory=lambda: "fake-client",
        )

    captured = capsys.readouterr()
    assert "unrecognized arguments: --decision-support-db-dsn" in captured.err


def test_action_gated_queue_history_cli_requires_enabled_db_config(
    monkeypatch,
    capsys,
):
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR, raising=False)

    def forbidden_loader(**kwargs):
        raise AssertionError("read-only loader should not run")

    def forbidden_builder(**kwargs):
        raise AssertionError("pure history builder should not run")

    exit_code = main(
        ["action-gated-queue-history"],
        action_gated_queue_loader=forbidden_loader,
        action_gated_queue_history_builder=forbidden_builder,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "action-gated-queue-history failed:" in captured.err
    assert "requires action-gated queue read-only DB config to be enabled" in (
        captured.err
    )


def test_action_gated_queue_history_cli_uses_injected_loader_and_builder(
    monkeypatch,
    capsys,
):
    action_gated_dsn = "postgresql://action-gated-history.example.invalid/db"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, action_gated_dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR,
        "action_gated_queue_archive",
    )
    source_reports = (
        SimpleNamespace(payload_json={"raw": "history-payload-secret-marker"}),
        SimpleNamespace(payload_json={"raw": "history-second-payload-secret"}),
    )
    loader_calls = []
    builder_calls = []

    def fake_loader(dsn, *, options):
        loader_calls.append((dsn, options))
        return source_reports

    def fake_history_builder(reports, *, generated_at):
        builder_calls.append((reports, generated_at))
        return SimpleNamespace(
            source_report_count=2,
            first_source_generated_at=datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
            last_source_generated_at=datetime(2026, 6, 20, 11, 0, tzinfo=UTC),
            research_ready_count=1,
            watch_count=1,
            blocked_count=0,
            total_ready_notional=Decimal("123.456000"),
            latest_action_status="watch",
            latest_recommended_next_step="await_fresh_cycle_evidence",
            status_transition_count=1,
            ready_notional_delta=Decimal("-10.000000"),
            latest_reason_code_counts=(
                PaperRecommendationCycleActionGateReasonCodeCount(
                    reason_code="cycle_review_watch",
                    count=2,
                ),
                PaperRecommendationCycleActionGateReasonCodeCount(
                    reason_code="manual_review",
                    count=1,
                ),
            ),
            paper_only=True,
            report_only=True,
            readonly=True,
        )

    exit_code = main(
        [
            "action-gated-queue-history",
            "--source-config-version",
            "paper-recommendation-cycle-action-gate-v0",
            "--action-status",
            "watch",
            "--limit",
            "25",
        ],
        action_gated_queue_loader=fake_loader,
        action_gated_queue_history_builder=fake_history_builder,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(loader_calls) == 1
    assert loader_calls[0][0] == action_gated_dsn
    read_options = loader_calls[0][1]
    assert isinstance(read_options, PaperActionGatedStrategyRecommendationQueueReadOptions)
    assert (
        read_options.source_config_version
        == "paper-recommendation-cycle-action-gate-v0"
    )
    assert read_options.action_status == "watch"
    assert read_options.limit == 25
    assert read_options.table_name == "action_gated_queue_archive"
    assert builder_calls == [(source_reports, builder_calls[0][1])]
    assert isinstance(builder_calls[0][1], datetime)

    captured = capsys.readouterr()
    assert "action-gated-queue-history:" in captured.out
    assert "source_report_count=2" in captured.out
    assert "first_source_generated_at=2026-06-20T10:00:00+00:00" in captured.out
    assert "last_source_generated_at=2026-06-20T11:00:00+00:00" in captured.out
    assert "research_ready_count=1" in captured.out
    assert "watch_count=1" in captured.out
    assert "blocked_count=0" in captured.out
    assert "total_ready_notional=123.456000" in captured.out
    assert "latest_action_status=watch" in captured.out
    assert "latest_recommended_next_step=await_fresh_cycle_evidence" in captured.out
    assert "status_transition_count=1" in captured.out
    assert "ready_notional_delta=-10.000000" in captured.out
    assert "latest_reason_code_counts=cycle_review_watch=2,manual_review=1" in (
        captured.out
    )
    assert "history-payload-secret-marker" not in captured.out
    assert "history-second-payload-secret" not in captured.out
    assert action_gated_dsn not in captured.out
    assert action_gated_dsn not in captured.err
    assert "action_gated_queue_archive" not in captured.out


def test_action_gated_queue_history_cli_default_builder_wiring(
    monkeypatch,
    capsys,
):
    action_gated_dsn = "postgresql://action-gated-history.example.invalid/db"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, action_gated_dsn)
    reports = (
        _blocked_action_gated_queue_report(
            datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
        ),
        _watch_action_gated_queue_report(
            datetime(2026, 6, 20, 11, 0, tzinfo=UTC),
        ),
    )

    def fake_loader(dsn, *, options):
        assert dsn == action_gated_dsn
        assert options.limit == 100
        return reports

    exit_code = main(
        ["action-gated-queue-history"],
        action_gated_queue_loader=fake_loader,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "action-gated-queue-history:" in captured.out
    assert "source_report_count=2" in captured.out
    assert "first_source_generated_at=2026-06-20T10:00:00+00:00" in captured.out
    assert "last_source_generated_at=2026-06-20T11:00:00+00:00" in captured.out
    assert "research_ready_count=0" in captured.out
    assert "watch_count=1" in captured.out
    assert "blocked_count=1" in captured.out
    assert "total_ready_notional=0.000000" in captured.out
    assert "latest_action_status=watch" in captured.out
    assert "latest_recommended_next_step=await_fresh_cycle_evidence" in captured.out
    assert "status_transition_count=1" in captured.out
    assert "ready_notional_delta=0.000000" in captured.out
    assert "latest_reason_code_counts=cycle_review_watch=1" in captured.out
    assert action_gated_dsn not in captured.out
    assert action_gated_dsn not in captured.err


def test_action_gated_queue_history_cli_persists_built_history_report_when_requested(
    monkeypatch,
    capsys,
):
    source_dsn = "postgresql://action-gated-history.example.invalid/source"
    history_dsn = "postgresql://action-gated-history.example.invalid/history"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR,
        "action_gated_queue_archive",
    )
    monkeypatch.setenv(ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR, history_dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR,
        "action_gated_queue_history_archive",
    )

    source_reports = (SimpleNamespace(payload_json={"raw": "secret"}),)
    history_report = SimpleNamespace(
        source_report_count=1,
        first_source_generated_at=datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
        last_source_generated_at=datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
        research_ready_count=1,
        watch_count=0,
        blocked_count=0,
        total_ready_notional=Decimal("42.000000"),
        latest_action_status="research_ready",
        latest_recommended_next_step="review_candidate_research_queue",
        status_transition_count=0,
        ready_notional_delta=Decimal("0.000000"),
        latest_reason_code_counts=(
            PaperRecommendationCycleActionGateReasonCodeCount(
                reason_code="cycle_review_pass",
                count=1,
            ),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    loader_calls = []
    builder_calls = []
    sink_calls = []

    def fake_loader(dsn, *, options):
        loader_calls.append((dsn, options))
        return source_reports

    def fake_history_builder(reports, *, generated_at):
        builder_calls.append((reports, generated_at))
        return history_report

    def fake_history_sink(*, dsn, report, table_name):
        sink_calls.append((dsn, report, table_name))
        return SimpleNamespace(report_sha256="a" * 64)

    exit_code = main(
        [
            "action-gated-queue-history",
            "--source-config-version",
            "paper-recommendation-cycle-action-gate-v0",
            "--action-status",
            "research_ready",
            "--limit",
            "5",
            "--persist",
        ],
        action_gated_queue_loader=fake_loader,
        action_gated_queue_history_builder=fake_history_builder,
        action_gated_queue_history_db_sink=fake_history_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert loader_calls[0][0] == source_dsn
    assert builder_calls == [(source_reports, builder_calls[0][1])]
    assert sink_calls == [
        (
            history_dsn,
            history_report,
            "action_gated_queue_history_archive",
        ),
    ]
    captured = capsys.readouterr()
    assert "action-gated-queue-history:" in captured.out
    assert "persisted=True" in captured.out
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert history_dsn not in captured.out
    assert history_dsn not in captured.err
    assert "action_gated_queue_history_archive" not in captured.out


def test_action_gated_queue_history_cli_requires_history_db_when_persisting(
    monkeypatch,
    capsys,
):
    source_dsn = "postgresql://action-gated-history.example.invalid/source"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.delenv(ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR, raising=False)
    monkeypatch.delenv(ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR, raising=False)
    calls = []

    def forbidden_loader(*args, **kwargs):
        calls.append(("loader", args, kwargs))
        raise AssertionError("source loader should not run")

    def forbidden_builder(*args, **kwargs):
        calls.append(("builder", args, kwargs))
        raise AssertionError("history builder should not run")

    def forbidden_sink(*args, **kwargs):
        calls.append(("sink", args, kwargs))
        raise AssertionError("history sink should not run")

    exit_code = main(
        ["action-gated-queue-history", "--persist"],
        action_gated_queue_loader=forbidden_loader,
        action_gated_queue_history_builder=forbidden_builder,
        action_gated_queue_history_db_sink=forbidden_sink,
    )

    assert exit_code == 1
    assert calls == []
    captured = capsys.readouterr()
    assert "action-gated-queue-history failed:" in captured.err
    assert "history DB to be enabled" in captured.err
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err


def test_action_gated_queue_history_cli_redacts_dsns_on_history_sink_failure(
    monkeypatch,
    capsys,
):
    source_dsn = "postgresql://action-gated-history.example.invalid/source"
    history_dsn = "postgresql://action-gated-history.example.invalid/history"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR, history_dsn)

    source_reports = (SimpleNamespace(payload_json={"raw": "secret"}),)
    history_report = SimpleNamespace(
        source_report_count=1,
        first_source_generated_at=datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
        last_source_generated_at=datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
        research_ready_count=1,
        watch_count=0,
        blocked_count=0,
        total_ready_notional=Decimal("42.000000"),
        latest_action_status="research_ready",
        latest_recommended_next_step="review_candidate_research_queue",
        status_transition_count=0,
        ready_notional_delta=Decimal("0.000000"),
        latest_reason_code_counts=(),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    def fake_loader(dsn, *, options):
        return source_reports

    def fake_history_builder(reports, *, generated_at):
        return history_report

    def broken_history_sink(*, dsn, report, table_name):
        raise RuntimeError(f"source={source_dsn} history={history_dsn}")

    exit_code = main(
        ["action-gated-queue-history", "--persist"],
        action_gated_queue_loader=fake_loader,
        action_gated_queue_history_builder=fake_history_builder,
        action_gated_queue_history_db_sink=broken_history_sink,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "action-gated-queue-history failed: "
        "source=<redacted-dsn> history=<redacted-dsn>"
    ) in captured.err
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert history_dsn not in captured.out
    assert history_dsn not in captured.err


def test_action_gated_queue_history_cli_default_psycopg_persist_path_no_network(
    monkeypatch,
    capsys,
):
    from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_db_row import (
        paper_action_gated_strategy_recommendation_queue_report_to_db_row,
    )

    source_dsn = "postgresql://action-gated-history.example.invalid/source"
    history_dsn = "postgresql://action-gated-history.example.invalid/history"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, source_dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR,
        "action_gated_queue_archive",
    )
    monkeypatch.setenv(ACTION_GATED_QUEUE_HISTORY_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_HISTORY_DB_DSN_ENV_VAR, history_dsn)
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_HISTORY_DB_TABLE_ENV_VAR,
        "action_gated_queue_history_archive",
    )

    first_at = datetime(2026, 6, 20, 10, 0, tzinfo=UTC)
    latest_at = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)

    def source_record(report):
        row = paper_action_gated_strategy_recommendation_queue_report_to_db_row(
            report,
        )
        return (
            row.report_sha256,
            row.generated_at,
            row.config_version,
            row.source_config_version,
            row.action_status,
            row.recommended_next_step,
            row.candidate_count,
            row.ready_count,
            row.watch_count,
            row.blocked_count,
            row.total_ready_notional,
            row.reason_code_counts_json,
            row.payload_json,
            row.paper_only,
            row.report_only,
            row.readonly,
        )

    source_records = (
        source_record(_watch_action_gated_queue_report(latest_at)),
        source_record(_blocked_action_gated_queue_report(first_at)),
    )

    class FakeCursor:
        def __init__(self, rows=()):
            self.rows = rows
            self.calls = []
            self.closed = False

        def execute(self, sql, params=()):
            self.calls.append((" ".join(sql.split()), params))

        def fetchall(self):
            return self.rows

        def close(self):
            self.closed = True

    class FakeConnection:
        def __init__(self, rows=()):
            self.cursor_instance = FakeCursor(rows)
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

    source_connection = FakeConnection(source_records)
    history_connection = FakeConnection()
    connect_calls = []

    def fake_connect(dsn, **kwargs):
        connect_calls.append((dsn, kwargs))
        if dsn == source_dsn:
            assert kwargs == {"autocommit": True}
            return source_connection
        if dsn == history_dsn:
            assert kwargs == {}
            return history_connection
        raise AssertionError(f"unexpected dsn: {dsn}")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setitem(
        sys.modules,
        "psycopg.types.json",
        SimpleNamespace(Jsonb=FakeJsonb),
    )
    sys.modules.pop(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_store",
        None,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_psycopg",
        None,
    )

    exit_code = main(
        [
            "action-gated-queue-history",
            "--source-config-version",
            "paper-recommendation-cycle-action-gate-v0",
            "--limit",
            "2",
            "--persist",
        ],
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert connect_calls == [
        (source_dsn, {"autocommit": True}),
        (history_dsn, {}),
    ]
    assert source_connection.close_count == 1
    assert source_connection.commit_count == 0
    assert source_connection.rollback_count == 0
    assert history_connection.close_count == 1
    assert history_connection.commit_count == 1
    assert history_connection.rollback_count == 0
    source_sql, source_params = source_connection.cursor_instance.calls[0]
    assert "FROM action_gated_queue_archive" in source_sql
    assert "ORDER BY generated_at DESC, report_sha256 DESC" in source_sql
    assert source_params == ("paper-recommendation-cycle-action-gate-v0", 2)
    history_sql, history_params = history_connection.cursor_instance.calls[0]
    assert "INSERT INTO action_gated_queue_history_archive" in history_sql
    assert len(history_params) == 18
    assert isinstance(history_params[13], FakeJsonb)
    assert isinstance(history_params[14], FakeJsonb)

    captured = capsys.readouterr()
    assert "action-gated-queue-history:" in captured.out
    assert "source_report_count=2" in captured.out
    assert "latest_action_status=watch" in captured.out
    assert "persisted=True" in captured.out
    assert source_dsn not in captured.out
    assert source_dsn not in captured.err
    assert history_dsn not in captured.out
    assert history_dsn not in captured.err
    assert "action_gated_queue_history_archive" not in captured.out


def test_action_gated_queue_history_cli_redacts_dsn_on_loader_failure(
    monkeypatch,
    capsys,
):
    action_gated_dsn = "postgresql://action-gated-history.example.invalid/db"
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, action_gated_dsn)

    def broken_loader(dsn, *, options):
        raise RuntimeError(f"could not connect to {dsn}")

    exit_code = main(
        ["action-gated-queue-history"],
        action_gated_queue_loader=broken_loader,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "action-gated-queue-history failed: "
        "could not connect to <redacted-dsn>"
    ) in captured.err
    assert action_gated_dsn not in captured.out
    assert action_gated_dsn not in captured.err


def test_action_gated_queue_history_cli_rejects_dsn_flag(capsys):
    with pytest.raises(SystemExit):
        main(
            [
                "action-gated-queue-history",
                "--action-gated-queue-db-dsn",
                "forbidden-value",
            ],
            client_factory=lambda: "fake-client",
        )

    captured = capsys.readouterr()
    assert "unrecognized arguments: --action-gated-queue-db-dsn" in captured.err


def test_run_cli_rejects_action_gated_queue_dsn_flag(tmp_path):
    with pytest.raises(SystemExit):
        main(
            [
                "run",
                "--archive-root",
                str(tmp_path / "raw"),
                "--starting-cash",
                "10000",
                "--cycle-log",
                str(tmp_path / "cycle.jsonl"),
                "--action-gated-queue-db-dsn",
                "forbidden-value",
            ],
            client_factory=lambda: "fake-client",
        )


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
    # The default strategy-cycle snapshot source emits four pipeline stages and
    # rich cycle artifacts; this integration test should catch wiring drift.
    assert report.stage_count == 4
    assert report.artifact_count == 3
    assert "cost_aware_paper_review_ready" in report.reason_codes
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
                           action_gated_queue_source=None,
                           action_gated_queue_sink=None,
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
                            action_gated_queue_source=None,
                            action_gated_queue_sink=None,
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
