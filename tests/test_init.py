import importlib
from pathlib import Path

import polymarket_alpha_lab as lab
from polymarket_alpha_lab import (
    proposal_evidence_comparison_history_batch_health as comparison_history_batch_health,
    proposal_evidence_comparison_history_batch_health_trend as batch_health_trend,
    proposal_evidence_comparison_history_batch_health_trend_batch as batch_health_trend_batch,
    proposal_evidence_comparison_history_batch_health_trend_batch_health as batch_health_trend_batch_health,
    proposal_evidence_comparison_history as comparison_history,
)
from polymarket_alpha_lab.analytics import (
    PaperAnalyticsBreach,
    PaperAnalyticsBucket,
    PaperAnalyticsConfig,
    PaperAnalyticsLog,
    PaperAnalyticsReport,
    PaperDrawdownPoint,
    PaperPerformanceSummary,
    PaperPositionExposure,
    build_paper_analytics_report,
    build_paper_drawdown_points,
)
from polymarket_alpha_lab.analytics_history import (
    PaperAnalyticsHistoryConfig,
    PaperAnalyticsHistoryGateResult,
    PaperAnalyticsHistoryLog,
    PaperAnalyticsHistoryReport,
    PaperAnalyticsHistoryTrend,
    build_paper_analytics_history_report,
)
from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventMarketSnapshot,
    PaperCostAwareEventSideResult,
    PaperCostAwareEventStrategyConfig,
    PaperCostAwareEventStrategyGateResult,
    PaperCostAwareEventStrategyLog,
    PaperCostAwareEventStrategyReport,
    build_paper_cost_aware_event_strategy_report,
    polymarket_default_cost_assumptions,
)
from polymarket_alpha_lab.forecast_provider import (
    PaperForecast,
    PaperForecastConfig,
    PaperForecastLog,
    build_paper_naive_forecast,
)
from polymarket_alpha_lab.book_imbalance_forecast import (
    PaperBookImbalanceForecast,
    PaperBookImbalanceForecastConfig,
    PaperBookImbalanceForecastLog,
    build_paper_book_imbalance_forecast,
)
from polymarket_alpha_lab.llm_forecast import (
    PaperLLMForecast,
    PaperLLMForecastConfig,
    PaperLLMForecastLog,
    build_paper_llm_forecast,
)
from polymarket_alpha_lab.cost_aware_snapshot_builder import (
    PaperCostAwareSnapshotAttempt,
    PaperCostAwareSnapshotConfig,
    PaperCostAwareSnapshotLog,
    build_paper_cost_aware_event_market_snapshot,
)
from polymarket_alpha_lab.strategy_cycle import (
    PaperStrategyCycleConfig,
    PaperStrategyCycleReport,
    PaperStrategyCycleLog,
    run_strategy_cycle,
)
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditConfig,
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
    build_paper_strategy_risk_audit_report,
)
from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningCandidate,
    PaperProjectScreeningConfig,
    PaperProjectScreeningGateResult,
    PaperProjectScreeningLog,
    PaperProjectScreeningQueueItem,
    PaperProjectScreeningReport,
    build_paper_project_screening_report,
)
from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceBucket,
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceGateResult,
    PaperForecastEvidenceLog,
    PaperForecastEvidenceObservation,
    PaperForecastEvidenceReport,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.manual_review_queue import (
    PaperManualReviewCandidate,
    PaperManualReviewConfig,
    PaperManualReviewLog,
    PaperManualReviewQueue,
    PaperManualReviewQueueItem,
    build_paper_manual_review_queue,
)
from polymarket_alpha_lab.proposal_packet import (
    TradeProposalPacket,
    TradeProposalPacketConfig,
    TradeProposalPacketLog,
    build_trade_proposal_packet,
)
from polymarket_alpha_lab.proposal_review import (
    TradeProposalReviewConfig,
    TradeProposalReviewLog,
    TradeProposalReviewRecord,
    build_trade_proposal_review_record,
)
from polymarket_alpha_lab.proposal_review_summary import (
    TradeProposalReviewBucketSummary,
    TradeProposalReviewReasonCodeSummary,
    TradeProposalReviewSummaryConfig,
    TradeProposalReviewSummaryLog,
    TradeProposalReviewSummaryReport,
    build_trade_proposal_review_summary_report,
)
from polymarket_alpha_lab.proposal_review_quality import (
    TradeProposalReviewQualityConfig,
    TradeProposalReviewQualityGateResult,
    TradeProposalReviewQualityLog,
    TradeProposalReviewQualityReasonTrend,
    TradeProposalReviewQualityReport,
    build_trade_proposal_review_quality_report,
)
from polymarket_alpha_lab.proposal_review_diagnostics import (
    TradeProposalReviewDiagnosticBucketRow,
    TradeProposalReviewDiagnosticConfig,
    TradeProposalReviewDiagnosticLog,
    TradeProposalReviewDiagnosticReasonRow,
    TradeProposalReviewDiagnosticReport,
    TradeProposalReviewDiagnosticSourceRow,
    build_trade_proposal_review_diagnostic_report,
)
from polymarket_alpha_lab.proposal_review_coverage import (
    TradeProposalReviewCoverageBucketRow,
    TradeProposalReviewCoverageConfig,
    TradeProposalReviewCoverageGateResult,
    TradeProposalReviewCoverageLog,
    TradeProposalReviewCoveragePacketRow,
    TradeProposalReviewCoverageReport,
    build_trade_proposal_review_coverage_report,
)
from polymarket_alpha_lab.proposal_review_dossier import (
    TradeProposalReviewDossierConfig,
    TradeProposalReviewDossierFindingRow,
    TradeProposalReviewDossierGateResult,
    TradeProposalReviewDossierLog,
    TradeProposalReviewDossierReport,
    TradeProposalReviewDossierSourceRow,
    build_trade_proposal_review_dossier_report,
)
from polymarket_alpha_lab.proposal_review_dossier_batch import (
    TradeProposalReviewDossierBatchConfig,
    TradeProposalReviewDossierBatchConfigVersionSummary,
    TradeProposalReviewDossierBatchDuplicateSummary,
    TradeProposalReviewDossierBatchFindingSummary,
    TradeProposalReviewDossierBatchGateResult,
    TradeProposalReviewDossierBatchLog,
    TradeProposalReviewDossierBatchReport,
    TradeProposalReviewDossierBatchSourceSummary,
    build_trade_proposal_review_dossier_batch_report,
)
from polymarket_alpha_lab.proposal_evidence_comparison import (
    TradeProposalEvidenceComparisonConfig,
    TradeProposalEvidenceComparisonFindingRow,
    TradeProposalEvidenceComparisonGateResult,
    TradeProposalEvidenceComparisonLog,
    TradeProposalEvidenceComparisonMetricRow,
    TradeProposalEvidenceComparisonReport,
    TradeProposalEvidenceComparisonSourceRow,
    build_trade_proposal_evidence_comparison_report,
)
from polymarket_alpha_lab.proposal_evidence_comparison_history import (
    TradeProposalEvidenceComparisonHistoryConfig,
    TradeProposalEvidenceComparisonHistoryConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryFindingSummary,
    TradeProposalEvidenceComparisonHistoryGateResult,
    TradeProposalEvidenceComparisonHistoryLog,
    TradeProposalEvidenceComparisonHistoryReport,
    TradeProposalEvidenceComparisonHistorySourceTransition,
    TradeProposalEvidenceComparisonHistoryStatusRow,
    build_trade_proposal_evidence_comparison_history_report,
)
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health import (
    TradeProposalEvidenceComparisonHistoryBatchHealthConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow,
    build_trade_proposal_evidence_comparison_history_batch_health_report,
)
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow,
    build_trade_proposal_evidence_comparison_history_batch_health_trend_report,
)
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow,
    build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report,
)
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow,
    build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report,
)
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health_trend import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow,
    build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report,
)
from polymarket_alpha_lab.proposal_evidence_comparison_artifact_registry import (
    PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS,
    REPORT_ONLY_FORBIDDEN_SURFACES,
    ProposalEvidenceComparisonArtifactDefinition,
    get_proposal_evidence_comparison_artifact,
    list_proposal_evidence_comparison_artifacts,
)
from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill, PaperOrder, simulate_order_book_fill
from polymarket_alpha_lab.paper_execution import (
    PaperExecutionConfig,
    PaperExecutionResult,
    PaperExecutionLog,
    execute_paper_trade_from_screening,
)
from polymarket_alpha_lab.nav_risk_metrics import (
    PaperNavRiskMetricsConfig,
    PaperNavRiskExposureRow,
    PaperNavRiskMetricsReport,
    build_paper_nav_risk_metrics_report,
)
from polymarket_alpha_lab.paper_trade_cost_audit import (
    PaperTradeCostAuditConfig,
    PaperTradeCostAuditReport,
    build_paper_trade_cost_audit_report,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate import (
    PaperResearchPacketOperatorFlowDbHistoryGateConfig,
    PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount,
    PaperResearchPacketOperatorFlowDbHistoryGateReport,
    build_paper_research_packet_operator_flow_db_history_gate_report,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION,
    PaperAutonomousScreeningDecisionSupportGateReasonCodeCount,
    PaperAutonomousScreeningDecisionSupportGateReport,
    build_paper_autonomous_screening_decision_support_gate_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal import (
    DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION,
    PaperAutonomousAllocationProposalConfig,
    PaperAutonomousAllocationProposalReasonCodeCount,
    PaperAutonomousAllocationProposalReport,
    PaperAutonomousAllocationProposalSourceQueueSummary,
    build_paper_autonomous_allocation_proposal_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION,
    PaperAutonomousAllocationProposalDbHistoryConfig,
    PaperAutonomousAllocationProposalDbHistoryReasonCodeRow,
    PaperAutonomousAllocationProposalDbHistoryReport,
    PaperAutonomousAllocationProposalDbHistoryStatusRow,
    build_paper_autonomous_allocation_proposal_db_history_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate import (
    PaperAutonomousAllocationProposalDbHistoryGateConfig,
    PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount,
    PaperAutonomousAllocationProposalDbHistoryGateReport,
    build_paper_autonomous_allocation_proposal_db_history_gate_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
    PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount,
    PaperAutonomousAllocationProposalDbHistoryHealthReport,
    build_paper_autonomous_allocation_proposal_db_history_health_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend import (
    PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendReport,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary,
    build_paper_autonomous_allocation_proposal_db_history_health_trend_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_gate import (
    PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport,
    build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendReasonCodeRow,
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendReport,
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendSnapshotSummary,
    build_paper_autonomous_investment_ledger_db_history_health_trend_report,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_gate import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig,
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReasonCodeCount,
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport,
    build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics import (
    PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow,
    PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow,
    PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
    PaperAutonomousAllocationProposalDbHistoryMetricsReport,
    PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary,
    build_paper_autonomous_allocation_proposal_db_history_metrics_report,
)
from polymarket_alpha_lab.paper_portfolio_nav import mark_paper_portfolio_nav
from polymarket_alpha_lab.outcome_tracker import (
    OutcomeTrackingConfig,
    OutcomeTrackingLog,
    OutcomeTrackingReport,
    check_outcomes,
)
from polymarket_alpha_lab.positions import (
    PaperNavLog,
    PaperNavSnapshot,
    PaperPortfolio,
    PaperPosition,
    PaperPositionMark,
    build_paper_portfolio,
    mark_paper_nav,
)
from polymarket_alpha_lab.rejections import RejectedCandidateLog, RejectedCandidateRecord
from polymarket_alpha_lab.research import ResearchPacket, build_research_packet
from polymarket_alpha_lab.risk import (
    RiskGateConfig,
    RiskGateDecision,
    RiskGateReason,
    evaluate_research_packet_risk,
)
from polymarket_alpha_lab.runner import RunLoopSummary, run_strategy_loop


def test_level_1_public_api_exports():
    expected_exports = {
        "PaperFill",
        "PaperOrder",
        "PaperTradeJournal",
        "PaperTradeRecord",
        "ResearchPacket",
        "build_research_packet",
        "simulate_order_book_fill",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperFill is PaperFill
    assert lab.PaperOrder is PaperOrder
    assert lab.PaperTradeJournal is PaperTradeJournal
    assert lab.PaperTradeRecord is PaperTradeRecord
    assert lab.ResearchPacket is ResearchPacket
    assert lab.build_research_packet is build_research_packet
    assert lab.simulate_order_book_fill is simulate_order_book_fill


def test_level_1b_node_1_public_api_exports():
    expected_exports = {
        "RejectedCandidateLog",
        "RejectedCandidateRecord",
        "RiskGateConfig",
        "RiskGateDecision",
        "RiskGateReason",
        "evaluate_research_packet_risk",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.RejectedCandidateLog is RejectedCandidateLog
    assert lab.RejectedCandidateRecord is RejectedCandidateRecord
    assert lab.RiskGateConfig is RiskGateConfig
    assert lab.RiskGateDecision is RiskGateDecision
    assert lab.RiskGateReason is RiskGateReason
    assert lab.evaluate_research_packet_risk is evaluate_research_packet_risk


def test_level_1b_node_2_public_api_exports():
    expected_exports = {
        "PaperNavLog",
        "PaperNavSnapshot",
        "PaperPortfolio",
        "PaperPosition",
        "PaperPositionMark",
        "build_paper_portfolio",
        "mark_paper_nav",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperNavLog is PaperNavLog
    assert lab.PaperNavSnapshot is PaperNavSnapshot
    assert lab.PaperPortfolio is PaperPortfolio
    assert lab.PaperPosition is PaperPosition
    assert lab.PaperPositionMark is PaperPositionMark
    assert lab.build_paper_portfolio is build_paper_portfolio
    assert lab.mark_paper_nav is mark_paper_nav


def test_level_1b_node_3_public_api_exports():
    expected_exports = {
        "PaperAnalyticsBreach",
        "PaperAnalyticsBucket",
        "PaperAnalyticsConfig",
        "PaperAnalyticsLog",
        "PaperAnalyticsReport",
        "PaperDrawdownPoint",
        "PaperPerformanceSummary",
        "PaperPositionExposure",
        "build_paper_analytics_report",
        "build_paper_drawdown_points",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperAnalyticsBreach is PaperAnalyticsBreach
    assert lab.PaperAnalyticsBucket is PaperAnalyticsBucket
    assert lab.PaperAnalyticsConfig is PaperAnalyticsConfig
    assert lab.PaperAnalyticsLog is PaperAnalyticsLog
    assert lab.PaperAnalyticsReport is PaperAnalyticsReport
    assert lab.PaperDrawdownPoint is PaperDrawdownPoint
    assert lab.PaperPerformanceSummary is PaperPerformanceSummary
    assert lab.PaperPositionExposure is PaperPositionExposure
    assert lab.build_paper_analytics_report is build_paper_analytics_report
    assert lab.build_paper_drawdown_points is build_paper_drawdown_points


def test_level_1b_node_4_public_api_exports():
    expected_exports = {
        "PaperAnalyticsHistoryConfig",
        "PaperAnalyticsHistoryGateResult",
        "PaperAnalyticsHistoryLog",
        "PaperAnalyticsHistoryReport",
        "PaperAnalyticsHistoryTrend",
        "build_paper_analytics_history_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperAnalyticsHistoryConfig is PaperAnalyticsHistoryConfig
    assert lab.PaperAnalyticsHistoryGateResult is PaperAnalyticsHistoryGateResult
    assert lab.PaperAnalyticsHistoryLog is PaperAnalyticsHistoryLog
    assert lab.PaperAnalyticsHistoryReport is PaperAnalyticsHistoryReport
    assert lab.PaperAnalyticsHistoryTrend is PaperAnalyticsHistoryTrend
    assert lab.build_paper_analytics_history_report is build_paper_analytics_history_report


def test_level_1b_node_5_public_api_exports():
    expected_exports = {
        "PaperForecastEvidenceBucket",
        "PaperForecastEvidenceConfig",
        "PaperForecastEvidenceGateResult",
        "PaperForecastEvidenceLog",
        "PaperForecastEvidenceObservation",
        "PaperForecastEvidenceReport",
        "build_paper_forecast_evidence_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperForecastEvidenceBucket is PaperForecastEvidenceBucket
    assert lab.PaperForecastEvidenceConfig is PaperForecastEvidenceConfig
    assert lab.PaperForecastEvidenceGateResult is PaperForecastEvidenceGateResult
    assert lab.PaperForecastEvidenceLog is PaperForecastEvidenceLog
    assert lab.PaperForecastEvidenceObservation is PaperForecastEvidenceObservation
    assert lab.PaperForecastEvidenceReport is PaperForecastEvidenceReport
    assert (
        lab.build_paper_forecast_evidence_report
        is build_paper_forecast_evidence_report
    )


def test_level_1b_node_6_public_api_exports():
    expected_exports = {
        "PaperManualReviewCandidate",
        "PaperManualReviewConfig",
        "PaperManualReviewLog",
        "PaperManualReviewQueue",
        "PaperManualReviewQueueItem",
        "build_paper_manual_review_queue",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperManualReviewCandidate is PaperManualReviewCandidate
    assert lab.PaperManualReviewConfig is PaperManualReviewConfig
    assert lab.PaperManualReviewLog is PaperManualReviewLog
    assert lab.PaperManualReviewQueue is PaperManualReviewQueue
    assert lab.PaperManualReviewQueueItem is PaperManualReviewQueueItem
    assert lab.build_paper_manual_review_queue is build_paper_manual_review_queue


def test_cost_aware_event_strategy_public_api_exports():
    expected_exports = {
        "PaperCostAwareEventCostAssumptions",
        "PaperCostAwareEventMarketSnapshot",
        "PaperCostAwareEventSideResult",
        "PaperCostAwareEventStrategyConfig",
        "PaperCostAwareEventStrategyGateResult",
        "PaperCostAwareEventStrategyLog",
        "PaperCostAwareEventStrategyReport",
        "build_paper_cost_aware_event_strategy_report",
        "polymarket_default_cost_assumptions",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperCostAwareEventCostAssumptions is PaperCostAwareEventCostAssumptions
    assert lab.PaperCostAwareEventMarketSnapshot is PaperCostAwareEventMarketSnapshot
    assert lab.PaperCostAwareEventSideResult is PaperCostAwareEventSideResult
    assert lab.PaperCostAwareEventStrategyConfig is PaperCostAwareEventStrategyConfig
    assert (
        lab.PaperCostAwareEventStrategyGateResult
        is PaperCostAwareEventStrategyGateResult
    )
    assert lab.PaperCostAwareEventStrategyLog is PaperCostAwareEventStrategyLog
    assert lab.PaperCostAwareEventStrategyReport is PaperCostAwareEventStrategyReport
    assert (
        lab.build_paper_cost_aware_event_strategy_report
        is build_paper_cost_aware_event_strategy_report
    )
    assert (
        lab.polymarket_default_cost_assumptions
        is polymarket_default_cost_assumptions
    )


def test_project_screening_public_api_exports():
    expected_exports = {
        "PaperProjectScreeningConfig",
        "PaperProjectScreeningCandidate",
        "PaperProjectScreeningGateResult",
        "PaperProjectScreeningQueueItem",
        "PaperProjectScreeningReport",
        "PaperProjectScreeningLog",
        "build_paper_project_screening_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperProjectScreeningConfig is PaperProjectScreeningConfig
    assert lab.PaperProjectScreeningCandidate is PaperProjectScreeningCandidate
    assert lab.PaperProjectScreeningGateResult is PaperProjectScreeningGateResult
    assert lab.PaperProjectScreeningQueueItem is PaperProjectScreeningQueueItem
    assert lab.PaperProjectScreeningReport is PaperProjectScreeningReport
    assert lab.PaperProjectScreeningLog is PaperProjectScreeningLog
    assert (
        lab.build_paper_project_screening_report
        is build_paper_project_screening_report
    )


def test_forecast_provider_public_api_exports():
    expected_exports = {
        "PaperForecastConfig",
        "PaperForecast",
        "PaperForecastLog",
        "build_paper_naive_forecast",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperForecastConfig is PaperForecastConfig
    assert lab.PaperForecast is PaperForecast
    assert lab.PaperForecastLog is PaperForecastLog
    assert lab.build_paper_naive_forecast is build_paper_naive_forecast


def test_book_imbalance_forecast_public_api_exports():
    expected_exports = {
        "PaperBookImbalanceForecastConfig",
        "PaperBookImbalanceForecast",
        "PaperBookImbalanceForecastLog",
        "build_paper_book_imbalance_forecast",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperBookImbalanceForecastConfig is PaperBookImbalanceForecastConfig
    assert lab.PaperBookImbalanceForecast is PaperBookImbalanceForecast
    assert lab.PaperBookImbalanceForecastLog is PaperBookImbalanceForecastLog
    assert (
        lab.build_paper_book_imbalance_forecast
        is build_paper_book_imbalance_forecast
    )


def test_llm_forecast_public_api_exports():
    expected_exports = {
        "PaperLLMForecastConfig",
        "PaperLLMForecast",
        "PaperLLMForecastLog",
        "build_paper_llm_forecast",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperLLMForecastConfig is PaperLLMForecastConfig
    assert lab.PaperLLMForecast is PaperLLMForecast
    assert lab.PaperLLMForecastLog is PaperLLMForecastLog
    assert lab.build_paper_llm_forecast is build_paper_llm_forecast


def test_cost_aware_snapshot_builder_public_api_exports():
    expected_exports = {
        "PaperCostAwareSnapshotConfig",
        "PaperCostAwareSnapshotAttempt",
        "PaperCostAwareSnapshotLog",
        "build_paper_cost_aware_event_market_snapshot",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperCostAwareSnapshotConfig is PaperCostAwareSnapshotConfig
    assert lab.PaperCostAwareSnapshotAttempt is PaperCostAwareSnapshotAttempt
    assert lab.PaperCostAwareSnapshotLog is PaperCostAwareSnapshotLog
    assert (
        lab.build_paper_cost_aware_event_market_snapshot
        is build_paper_cost_aware_event_market_snapshot
    )


def test_strategy_cycle_public_api_exports():
    expected_exports = {
        "PaperStrategyCycleConfig",
        "PaperStrategyCycleReport",
        "PaperStrategyCycleLog",
        "run_strategy_cycle",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperStrategyCycleConfig is PaperStrategyCycleConfig
    assert lab.PaperStrategyCycleReport is PaperStrategyCycleReport
    assert lab.PaperStrategyCycleLog is PaperStrategyCycleLog
    assert lab.run_strategy_cycle is run_strategy_cycle


def test_paper_strategy_cycle_report_history_gate_public_api_exports():
    gate_module = importlib.import_module(
        "polymarket_alpha_lab.paper_strategy_cycle_report_history_gate",
    )
    expected_exports = {
        "DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_CONFIG_VERSION",
        "PaperStrategyCycleReportHistoryGateConfig",
        "PaperStrategyCycleReportHistoryGateReasonCodeCount",
        "PaperStrategyCycleReportHistoryGateReport",
        "build_paper_strategy_cycle_report_history_gate_report",
    }
    forbidden_exports = {
        "DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_DB_TABLE",
        "DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_REPORTS_TABLE",
        "MISSING_LATEST_REASON_CODE",
        "NEXT_STEP_BY_STATUS",
        "PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_DB_DSN_ENV_VAR",
        "PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_DB_ENABLED_ENV_VAR",
        "PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_DB_TABLE_ENV_VAR",
        "PASS_REASON_CODE",
        "PaperStrategyCycleReportHistoryGateDbRow",
        "PaperStrategyCycleReportHistoryGateInsertResult",
        "SOURCE_BLOCKED_REASON_CODE",
        "SOURCE_WATCH_REASON_CODE",
        "STALE_REASON_CODE",
        "SupabasePaperStrategyCycleReportHistoryGateConfig",
        "from_paper_strategy_cycle_report_history_gate_db_env",
        "insert_paper_strategy_cycle_report_history_gate_report",
        "insert_paper_strategy_cycle_report_history_gate_report_with_psycopg",
        "insert_paper_strategy_cycle_report_history_gate_report_with_result",
        "load_paper_strategy_cycle_report_history_gate_reports",
        "load_paper_strategy_cycle_report_history_gate_reports_with_psycopg",
        "paper_strategy_cycle_report_history_gate_report_from_db_row",
        "paper_strategy_cycle_report_history_gate_report_to_db_row",
    }

    assert expected_exports <= set(lab.__all__)
    assert not (forbidden_exports & set(lab.__all__))
    assert (
        lab.DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_CONFIG_VERSION
        is gate_module.DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_CONFIG_VERSION
    )
    assert (
        lab.PaperStrategyCycleReportHistoryGateConfig
        is gate_module.PaperStrategyCycleReportHistoryGateConfig
    )
    assert (
        lab.PaperStrategyCycleReportHistoryGateReasonCodeCount
        is gate_module.PaperStrategyCycleReportHistoryGateReasonCodeCount
    )
    assert (
        lab.PaperStrategyCycleReportHistoryGateReport
        is gate_module.PaperStrategyCycleReportHistoryGateReport
    )
    assert (
        lab.build_paper_strategy_cycle_report_history_gate_report
        is gate_module.build_paper_strategy_cycle_report_history_gate_report
    )
    for name in forbidden_exports:
        assert not hasattr(lab, name)


def test_paper_strategy_cycle_report_history_gate_runbook_documents_scope():
    runbook_path = Path("docs/paper-strategy-cycle-report-history-gate.md")

    assert runbook_path.is_file()

    runbook = runbook_path.read_text(encoding="utf-8")
    required_snippets = (
        "POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED",
        "POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_DSN",
        "POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_TABLE",
        "POLYMARKET_ALPHA_LAB_STRATEGY_CYCLE_HISTORY_GATE_DB_ENABLED",
        "POLYMARKET_ALPHA_LAB_STRATEGY_CYCLE_HISTORY_GATE_DB_DSN",
        "POLYMARKET_ALPHA_LAB_STRATEGY_CYCLE_HISTORY_GATE_DB_TABLE",
        "polymarket-alpha-lab strategy-cycle-history-gate --limit 50",
        "polymarket-alpha-lab strategy-cycle-history-gate --limit 50 --persist",
        "strategy-cycle-history-gate: status=<status> "
        "source_history_status=<status> reports=<count> "
        "latest_snapshot_ready_share=<rate> blocked_market_share=<rate> "
        "persisted=<true|false>",
        "no live trading",
        "account auth",
        "wallet",
        "private keys",
        "order signing",
        "order submission",
        "order cancellation",
        "order replacement",
        "exchange mutation",
    )

    for snippet in required_snippets:
        assert snippet in runbook


def test_strategy_risk_audit_public_api_exports():
    expected_exports = {
        "PaperStrategyRiskAuditConfig",
        "PaperStrategyRiskAuditGateResult",
        "PaperStrategyRiskAuditReport",
        "build_paper_strategy_risk_audit_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperStrategyRiskAuditConfig is PaperStrategyRiskAuditConfig
    assert (
        lab.PaperStrategyRiskAuditGateResult
        is PaperStrategyRiskAuditGateResult
    )
    assert lab.PaperStrategyRiskAuditReport is PaperStrategyRiskAuditReport
    assert (
        lab.build_paper_strategy_risk_audit_report
        is build_paper_strategy_risk_audit_report
    )


def test_paper_execution_public_api_exports():
    expected_exports = {
        "PaperExecutionConfig",
        "PaperExecutionResult",
        "PaperExecutionLog",
        "execute_paper_trade_from_screening",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperExecutionConfig is PaperExecutionConfig
    assert lab.PaperExecutionResult is PaperExecutionResult
    assert lab.PaperExecutionLog is PaperExecutionLog
    assert lab.execute_paper_trade_from_screening is execute_paper_trade_from_screening


def test_paper_portfolio_nav_public_api_exports():
    expected_exports = {"mark_paper_portfolio_nav"}

    assert expected_exports <= set(lab.__all__)
    assert lab.mark_paper_portfolio_nav is mark_paper_portfolio_nav


def test_nav_risk_metrics_public_api_exports():
    expected_exports = {
        "PaperNavRiskMetricsConfig",
        "PaperNavRiskExposureRow",
        "PaperNavRiskMetricsReport",
        "build_paper_nav_risk_metrics_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperNavRiskMetricsConfig is PaperNavRiskMetricsConfig
    assert lab.PaperNavRiskExposureRow is PaperNavRiskExposureRow
    assert lab.PaperNavRiskMetricsReport is PaperNavRiskMetricsReport
    assert (
        lab.build_paper_nav_risk_metrics_report
        is build_paper_nav_risk_metrics_report
    )


def test_paper_trade_cost_audit_public_api_exports():
    expected_exports = {
        "PaperTradeCostAuditConfig",
        "PaperTradeCostAuditReport",
        "build_paper_trade_cost_audit_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperTradeCostAuditConfig is PaperTradeCostAuditConfig
    assert lab.PaperTradeCostAuditReport is PaperTradeCostAuditReport
    assert (
        lab.build_paper_trade_cost_audit_report
        is build_paper_trade_cost_audit_report
    )


def test_paper_research_packet_operator_flow_db_history_gate_public_api_exports():
    expected_exports = {
        "PaperResearchPacketOperatorFlowDbHistoryGateConfig",
        "PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount",
        "PaperResearchPacketOperatorFlowDbHistoryGateReport",
        "build_paper_research_packet_operator_flow_db_history_gate_report",
    }
    forbidden_exports = {
        "DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_HISTORY_GATE_CONFIG_VERSION",
        "NEXT_STEP_BY_STATUS",
        "load_paper_research_packet_operator_flow_db_history_gate_report",
        "PaperResearchPacketOperatorFlowDbHistoryGateRunner",
        "_run_paper_research_packet_operator_flow_db_history_gate",
        "_print_paper_research_packet_operator_flow_db_history_gate_summary",
    }

    assert expected_exports <= set(lab.__all__)
    assert not (forbidden_exports & set(lab.__all__))
    assert (
        lab.PaperResearchPacketOperatorFlowDbHistoryGateConfig
        is PaperResearchPacketOperatorFlowDbHistoryGateConfig
    )
    assert (
        lab.PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount
        is PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount
    )
    assert (
        lab.PaperResearchPacketOperatorFlowDbHistoryGateReport
        is PaperResearchPacketOperatorFlowDbHistoryGateReport
    )
    assert (
        lab.build_paper_research_packet_operator_flow_db_history_gate_report
        is build_paper_research_packet_operator_flow_db_history_gate_report
    )
    for name in forbidden_exports:
        assert not hasattr(lab, name)


def test_paper_autonomous_screening_decision_support_gate_public_api_exports():
    expected_exports = {
        "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION",
        "PaperAutonomousScreeningDecisionSupportGateReasonCodeCount",
        "PaperAutonomousScreeningDecisionSupportGateReport",
        "build_paper_autonomous_screening_decision_support_gate_report",
    }
    forbidden_exports = {
        "PaperAutonomousScreeningDecisionSupportGateConfig",
        "PaperAutonomousScreeningDecisionSupportGateRunner",
        "_PaperAutonomousScreeningDecisionSupportGateConfig",
    }

    assert expected_exports <= set(lab.__all__)
    assert not (forbidden_exports & set(lab.__all__))
    assert (
        lab.DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION
        is DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION
    )
    assert (
        lab.PaperAutonomousScreeningDecisionSupportGateReasonCodeCount
        is PaperAutonomousScreeningDecisionSupportGateReasonCodeCount
    )
    assert (
        lab.PaperAutonomousScreeningDecisionSupportGateReport
        is PaperAutonomousScreeningDecisionSupportGateReport
    )
    assert (
        lab.build_paper_autonomous_screening_decision_support_gate_report
        is build_paper_autonomous_screening_decision_support_gate_report
    )
    for name in forbidden_exports:
        assert not hasattr(lab, name)


def test_paper_autonomous_readiness_gate_public_api_exports():
    gate_module = importlib.import_module(
        "polymarket_alpha_lab.paper_autonomous_readiness_gate"
    )
    expected_exports = {
        "PaperAutonomousReadinessGateConfig",
        "PaperAutonomousReadinessGateReasonCodeCount",
        "PaperAutonomousReadinessGateReport",
        "build_paper_autonomous_readiness_gate_report",
    }
    forbidden_exports = {
        "DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_CONFIG_VERSION",
        "PaperAutonomousReadinessGateRunner",
        "load_paper_autonomous_readiness_gate_report",
        "_run_paper_autonomous_readiness_gate",
        "_print_paper_autonomous_readiness_gate_summary",
        "PaperAutonomousReadinessGateLiveConfig",
        "PaperAutonomousReadinessGateOrder",
        "PaperAutonomousReadinessGateBroker",
        "PaperAutonomousReadinessGateSink",
    }

    assert expected_exports <= set(lab.__all__)
    assert not (forbidden_exports & set(lab.__all__))
    assert (
        lab.PaperAutonomousReadinessGateConfig
        is gate_module.PaperAutonomousReadinessGateConfig
    )
    assert (
        lab.PaperAutonomousReadinessGateReasonCodeCount
        is gate_module.PaperAutonomousReadinessGateReasonCodeCount
    )
    assert (
        lab.PaperAutonomousReadinessGateReport
        is gate_module.PaperAutonomousReadinessGateReport
    )
    assert (
        lab.build_paper_autonomous_readiness_gate_report
        is gate_module.build_paper_autonomous_readiness_gate_report
    )
    for name in forbidden_exports:
        assert not hasattr(lab, name)
    readiness_exports = {
        name
        for name in lab.__all__
        if "readiness" in name.lower()
        or "PaperAutonomousReadinessGate" in name
    }
    assert not {
        name
        for name in readiness_exports
        if any(surface in name.lower() for surface in ("live", "order", "broker", "sink"))
    }


def test_paper_autonomous_allocation_proposal_public_api_exports():
    expected_exports = {
        "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION",
        "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION",
        "PaperAutonomousAllocationProposalConfig",
        "PaperAutonomousAllocationProposalDbHistoryConfig",
        "PaperAutonomousAllocationProposalDbHistoryGateConfig",
        "PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount",
        "PaperAutonomousAllocationProposalDbHistoryGateReport",
        "PaperAutonomousAllocationProposalDbHistoryReasonCodeRow",
        "PaperAutonomousAllocationProposalDbHistoryReport",
        "PaperAutonomousAllocationProposalDbHistoryStatusRow",
        "PaperAutonomousAllocationProposalReasonCodeCount",
        "PaperAutonomousAllocationProposalSourceQueueSummary",
        "PaperAutonomousAllocationProposalReport",
        "build_paper_autonomous_allocation_proposal_db_history_gate_report",
        "build_paper_autonomous_allocation_proposal_db_history_report",
        "build_paper_autonomous_allocation_proposal_report",
    }
    forbidden_exports = {
        "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_GATE_CONFIG_VERSION",
        "PaperAutonomousAllocationProposalRunner",
        "PaperAutonomousAllocationProposalDbRow",
        "load_paper_autonomous_allocation_proposal_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert not (forbidden_exports & set(lab.__all__))
    assert (
        lab.DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION
        is DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION
    )
    assert (
        lab.DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION
        is DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_CONFIG_VERSION
    )
    assert (
        lab.PaperAutonomousAllocationProposalConfig
        is PaperAutonomousAllocationProposalConfig
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryConfig
        is PaperAutonomousAllocationProposalDbHistoryConfig
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryGateConfig
        is PaperAutonomousAllocationProposalDbHistoryGateConfig
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount
        is PaperAutonomousAllocationProposalDbHistoryGateReasonCodeCount
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryGateReport
        is PaperAutonomousAllocationProposalDbHistoryGateReport
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryReasonCodeRow
        is PaperAutonomousAllocationProposalDbHistoryReasonCodeRow
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryReport
        is PaperAutonomousAllocationProposalDbHistoryReport
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryStatusRow
        is PaperAutonomousAllocationProposalDbHistoryStatusRow
    )
    assert (
        lab.PaperAutonomousAllocationProposalReasonCodeCount
        is PaperAutonomousAllocationProposalReasonCodeCount
    )
    assert (
        lab.PaperAutonomousAllocationProposalSourceQueueSummary
        is PaperAutonomousAllocationProposalSourceQueueSummary
    )
    assert (
        lab.PaperAutonomousAllocationProposalReport
        is PaperAutonomousAllocationProposalReport
    )
    assert (
        lab.build_paper_autonomous_allocation_proposal_report
        is build_paper_autonomous_allocation_proposal_report
    )
    assert (
        lab.build_paper_autonomous_allocation_proposal_db_history_gate_report
        is build_paper_autonomous_allocation_proposal_db_history_gate_report
    )
    assert (
        lab.build_paper_autonomous_allocation_proposal_db_history_report
        is build_paper_autonomous_allocation_proposal_db_history_report
    )
    for name in forbidden_exports:
        assert not hasattr(lab, name)


def test_paper_autonomous_allocation_proposal_db_history_health_public_api_exports():
    expected_exports = {
        "PaperAutonomousAllocationProposalDbHistoryHealthConfig",
        "PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount",
        "PaperAutonomousAllocationProposalDbHistoryHealthReport",
        "PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig",
        "PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig",
        "PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount",
        "PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport",
        "PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow",
        "PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary",
        "PaperAutonomousAllocationProposalDbHistoryHealthTrendReport",
        "PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow",
        "PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow",
        "PaperAutonomousAllocationProposalDbHistoryMetricsConfig",
        "PaperAutonomousAllocationProposalDbHistoryMetricsReport",
        "PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary",
        "build_paper_autonomous_allocation_proposal_db_history_health_report",
        "build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report",
        "build_paper_autonomous_allocation_proposal_db_history_health_trend_report",
        "build_paper_autonomous_allocation_proposal_db_history_metrics_report",
    }
    forbidden_exports = {
        "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_CONFIG_VERSION",
        "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_TREND_GATE_CONFIG_VERSION",
        "PaperAutonomousAllocationProposalDbHistoryMetricsRunner",
        "PaperAutonomousAllocationProposalDbHistoryHealthRunner",
        "PaperAutonomousAllocationProposalDbHistoryHealthTrendGateRunner",
        "load_paper_autonomous_allocation_proposal_db_history_metrics_report",
        "load_paper_autonomous_allocation_proposal_db_history_health_report",
        "load_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report",
        "_run_paper_autonomous_allocation_proposal_db_history_metrics",
        "_run_paper_autonomous_allocation_proposal_db_history_health",
        "_run_paper_autonomous_allocation_proposal_db_history_health_trend_gate",
        "_print_paper_autonomous_allocation_proposal_db_history_metrics_summary",
        "_print_paper_autonomous_allocation_proposal_db_history_health_summary",
        "_print_paper_autonomous_allocation_proposal_db_history_health_trend_gate_summary",
    }

    assert expected_exports <= set(lab.__all__)
    assert not (forbidden_exports & set(lab.__all__))
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryHealthConfig
        is PaperAutonomousAllocationProposalDbHistoryHealthConfig
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount
        is PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryHealthReport
        is PaperAutonomousAllocationProposalDbHistoryHealthReport
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig
        is PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig
        is PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount
        is PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReasonCodeCount
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport
        is PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow
        is PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary
        is PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryHealthTrendReport
        is PaperAutonomousAllocationProposalDbHistoryHealthTrendReport
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow
        is PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow
        is PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryMetricsConfig
        is PaperAutonomousAllocationProposalDbHistoryMetricsConfig
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryMetricsReport
        is PaperAutonomousAllocationProposalDbHistoryMetricsReport
    )
    assert (
        lab.PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary
        is PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary
    )
    assert (
        lab.build_paper_autonomous_allocation_proposal_db_history_health_report
        is build_paper_autonomous_allocation_proposal_db_history_health_report
    )
    assert (
        lab.build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report
        is build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report
    )
    assert (
        lab.build_paper_autonomous_allocation_proposal_db_history_health_trend_report
        is build_paper_autonomous_allocation_proposal_db_history_health_trend_report
    )
    assert (
        lab.build_paper_autonomous_allocation_proposal_db_history_metrics_report
        is build_paper_autonomous_allocation_proposal_db_history_metrics_report
    )
    for name in forbidden_exports:
        assert not hasattr(lab, name)


def test_paper_autonomous_investment_ledger_db_history_health_trend_public_api_exports():
    expected_exports = {
        "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig",
        "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig",
        "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReasonCodeCount",
        "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport",
        "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendReasonCodeRow",
        "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendReport",
        "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendSnapshotSummary",
        "build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report",
        "build_paper_autonomous_investment_ledger_db_history_health_trend_report",
    }
    forbidden_exports = {
        "DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_HISTORY_HEALTH_TREND_GATE_CONFIG_VERSION",
        "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateRunner",
        "load_paper_autonomous_investment_ledger_db_history_health_trend_gate_report",
        "_run_paper_autonomous_investment_ledger_db_history_health_trend_gate",
        "_print_paper_autonomous_investment_ledger_db_history_health_trend_gate_summary",
    }

    assert expected_exports <= set(lab.__all__)
    assert not (forbidden_exports & set(lab.__all__))
    assert (
        lab.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig
        is PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig
    )
    assert (
        lab.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig
        is PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig
    )
    assert (
        lab.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReasonCodeCount
        is PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReasonCodeCount
    )
    assert (
        lab.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport
        is PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport
    )
    assert (
        lab.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendReasonCodeRow
        is PaperAutonomousInvestmentLedgerDbHistoryHealthTrendReasonCodeRow
    )
    assert (
        lab.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendReport
        is PaperAutonomousInvestmentLedgerDbHistoryHealthTrendReport
    )
    assert (
        lab.PaperAutonomousInvestmentLedgerDbHistoryHealthTrendSnapshotSummary
        is PaperAutonomousInvestmentLedgerDbHistoryHealthTrendSnapshotSummary
    )
    assert (
        lab.build_paper_autonomous_investment_ledger_db_history_health_trend_report
        is build_paper_autonomous_investment_ledger_db_history_health_trend_report
    )
    assert (
        lab.build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report
        is build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report
    )
    for name in forbidden_exports:
        assert not hasattr(lab, name)


def test_outcome_tracker_public_api_exports():
    expected_exports = {
        "OutcomeTrackingConfig",
        "OutcomeTrackingLog",
        "OutcomeTrackingReport",
        "check_outcomes",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.OutcomeTrackingConfig is OutcomeTrackingConfig
    assert lab.OutcomeTrackingLog is OutcomeTrackingLog
    assert lab.OutcomeTrackingReport is OutcomeTrackingReport
    assert lab.check_outcomes is check_outcomes


def test_runner_public_api_exports():
    expected_exports = {"RunLoopSummary", "run_strategy_loop"}

    assert expected_exports <= set(lab.__all__)
    assert lab.RunLoopSummary is RunLoopSummary
    assert lab.run_strategy_loop is run_strategy_loop


def test_level_2_node_1_public_api_exports():
    expected_exports = {
        "TradeProposalPacket",
        "TradeProposalPacketConfig",
        "TradeProposalPacketLog",
        "build_trade_proposal_packet",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.TradeProposalPacket is TradeProposalPacket
    assert lab.TradeProposalPacketConfig is TradeProposalPacketConfig
    assert lab.TradeProposalPacketLog is TradeProposalPacketLog
    assert lab.build_trade_proposal_packet is build_trade_proposal_packet


def test_level_2_node_2_public_api_exports():
    expected_exports = {
        "TradeProposalReviewConfig",
        "TradeProposalReviewLog",
        "TradeProposalReviewRecord",
        "build_trade_proposal_review_record",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.TradeProposalReviewConfig is TradeProposalReviewConfig
    assert lab.TradeProposalReviewLog is TradeProposalReviewLog
    assert lab.TradeProposalReviewRecord is TradeProposalReviewRecord
    assert (
        lab.build_trade_proposal_review_record
        is build_trade_proposal_review_record
    )


def test_level_2_node_3_public_api_exports():
    expected_exports = {
        "TradeProposalReviewBucketSummary",
        "TradeProposalReviewReasonCodeSummary",
        "TradeProposalReviewSummaryConfig",
        "TradeProposalReviewSummaryLog",
        "TradeProposalReviewSummaryReport",
        "build_trade_proposal_review_summary_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.TradeProposalReviewBucketSummary is TradeProposalReviewBucketSummary
    assert (
        lab.TradeProposalReviewReasonCodeSummary
        is TradeProposalReviewReasonCodeSummary
    )
    assert lab.TradeProposalReviewSummaryConfig is TradeProposalReviewSummaryConfig
    assert lab.TradeProposalReviewSummaryLog is TradeProposalReviewSummaryLog
    assert lab.TradeProposalReviewSummaryReport is TradeProposalReviewSummaryReport
    assert (
        lab.build_trade_proposal_review_summary_report
        is build_trade_proposal_review_summary_report
    )


def test_level_2_node_4_public_api_exports():
    expected_exports = {
        "TradeProposalReviewQualityConfig",
        "TradeProposalReviewQualityGateResult",
        "TradeProposalReviewQualityLog",
        "TradeProposalReviewQualityReasonTrend",
        "TradeProposalReviewQualityReport",
        "build_trade_proposal_review_quality_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.TradeProposalReviewQualityConfig is TradeProposalReviewQualityConfig
    assert (
        lab.TradeProposalReviewQualityGateResult
        is TradeProposalReviewQualityGateResult
    )
    assert lab.TradeProposalReviewQualityLog is TradeProposalReviewQualityLog
    assert (
        lab.TradeProposalReviewQualityReasonTrend
        is TradeProposalReviewQualityReasonTrend
    )
    assert lab.TradeProposalReviewQualityReport is TradeProposalReviewQualityReport
    assert (
        lab.build_trade_proposal_review_quality_report
        is build_trade_proposal_review_quality_report
    )


def test_level_2_node_5_public_api_exports():
    expected_exports = {
        "TradeProposalReviewDiagnosticBucketRow",
        "TradeProposalReviewDiagnosticConfig",
        "TradeProposalReviewDiagnosticLog",
        "TradeProposalReviewDiagnosticReasonRow",
        "TradeProposalReviewDiagnosticReport",
        "TradeProposalReviewDiagnosticSourceRow",
        "build_trade_proposal_review_diagnostic_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert (
        lab.TradeProposalReviewDiagnosticBucketRow
        is TradeProposalReviewDiagnosticBucketRow
    )
    assert lab.TradeProposalReviewDiagnosticConfig is TradeProposalReviewDiagnosticConfig
    assert lab.TradeProposalReviewDiagnosticLog is TradeProposalReviewDiagnosticLog
    assert (
        lab.TradeProposalReviewDiagnosticReasonRow
        is TradeProposalReviewDiagnosticReasonRow
    )
    assert lab.TradeProposalReviewDiagnosticReport is TradeProposalReviewDiagnosticReport
    assert (
        lab.TradeProposalReviewDiagnosticSourceRow
        is TradeProposalReviewDiagnosticSourceRow
    )
    assert (
        lab.build_trade_proposal_review_diagnostic_report
        is build_trade_proposal_review_diagnostic_report
    )


def test_level_2_node_6_public_api_exports():
    expected_exports = {
        "TradeProposalReviewCoverageBucketRow",
        "TradeProposalReviewCoverageConfig",
        "TradeProposalReviewCoverageGateResult",
        "TradeProposalReviewCoverageLog",
        "TradeProposalReviewCoveragePacketRow",
        "TradeProposalReviewCoverageReport",
        "build_trade_proposal_review_coverage_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.TradeProposalReviewCoverageBucketRow is TradeProposalReviewCoverageBucketRow
    assert lab.TradeProposalReviewCoverageConfig is TradeProposalReviewCoverageConfig
    assert (
        lab.TradeProposalReviewCoverageGateResult
        is TradeProposalReviewCoverageGateResult
    )
    assert lab.TradeProposalReviewCoverageLog is TradeProposalReviewCoverageLog
    assert lab.TradeProposalReviewCoveragePacketRow is TradeProposalReviewCoveragePacketRow
    assert lab.TradeProposalReviewCoverageReport is TradeProposalReviewCoverageReport
    assert (
        lab.build_trade_proposal_review_coverage_report
        is build_trade_proposal_review_coverage_report
    )


def test_level_2_node_7_public_api_exports():
    expected_exports = {
        "TradeProposalReviewDossierConfig",
        "TradeProposalReviewDossierFindingRow",
        "TradeProposalReviewDossierGateResult",
        "TradeProposalReviewDossierLog",
        "TradeProposalReviewDossierReport",
        "TradeProposalReviewDossierSourceRow",
        "build_trade_proposal_review_dossier_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.TradeProposalReviewDossierConfig is TradeProposalReviewDossierConfig
    assert (
        lab.TradeProposalReviewDossierFindingRow
        is TradeProposalReviewDossierFindingRow
    )
    assert (
        lab.TradeProposalReviewDossierGateResult
        is TradeProposalReviewDossierGateResult
    )
    assert lab.TradeProposalReviewDossierLog is TradeProposalReviewDossierLog
    assert lab.TradeProposalReviewDossierReport is TradeProposalReviewDossierReport
    assert (
        lab.TradeProposalReviewDossierSourceRow
        is TradeProposalReviewDossierSourceRow
    )
    assert (
        lab.build_trade_proposal_review_dossier_report
        is build_trade_proposal_review_dossier_report
    )


def test_level_2_node_8_public_api_exports():
    expected_exports = {
        "TradeProposalReviewDossierBatchConfig",
        "TradeProposalReviewDossierBatchConfigVersionSummary",
        "TradeProposalReviewDossierBatchDuplicateSummary",
        "TradeProposalReviewDossierBatchFindingSummary",
        "TradeProposalReviewDossierBatchGateResult",
        "TradeProposalReviewDossierBatchLog",
        "TradeProposalReviewDossierBatchReport",
        "TradeProposalReviewDossierBatchSourceSummary",
        "build_trade_proposal_review_dossier_batch_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.TradeProposalReviewDossierBatchConfig is TradeProposalReviewDossierBatchConfig
    assert (
        lab.TradeProposalReviewDossierBatchConfigVersionSummary
        is TradeProposalReviewDossierBatchConfigVersionSummary
    )
    assert (
        lab.TradeProposalReviewDossierBatchDuplicateSummary
        is TradeProposalReviewDossierBatchDuplicateSummary
    )
    assert (
        lab.TradeProposalReviewDossierBatchFindingSummary
        is TradeProposalReviewDossierBatchFindingSummary
    )
    assert (
        lab.TradeProposalReviewDossierBatchGateResult
        is TradeProposalReviewDossierBatchGateResult
    )
    assert lab.TradeProposalReviewDossierBatchLog is TradeProposalReviewDossierBatchLog
    assert (
        lab.TradeProposalReviewDossierBatchReport
        is TradeProposalReviewDossierBatchReport
    )
    assert (
        lab.TradeProposalReviewDossierBatchSourceSummary
        is TradeProposalReviewDossierBatchSourceSummary
    )
    assert (
        lab.build_trade_proposal_review_dossier_batch_report
        is build_trade_proposal_review_dossier_batch_report
    )


def test_level_2_node_9_public_api_exports():
    expected_exports = {
        "TradeProposalEvidenceComparisonConfig",
        "TradeProposalEvidenceComparisonFindingRow",
        "TradeProposalEvidenceComparisonGateResult",
        "TradeProposalEvidenceComparisonLog",
        "TradeProposalEvidenceComparisonMetricRow",
        "TradeProposalEvidenceComparisonReport",
        "TradeProposalEvidenceComparisonSourceRow",
        "build_trade_proposal_evidence_comparison_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert (
        lab.TradeProposalEvidenceComparisonConfig
        is TradeProposalEvidenceComparisonConfig
    )
    assert (
        lab.TradeProposalEvidenceComparisonFindingRow
        is TradeProposalEvidenceComparisonFindingRow
    )
    assert (
        lab.TradeProposalEvidenceComparisonGateResult
        is TradeProposalEvidenceComparisonGateResult
    )
    assert lab.TradeProposalEvidenceComparisonLog is TradeProposalEvidenceComparisonLog
    assert (
        lab.TradeProposalEvidenceComparisonMetricRow
        is TradeProposalEvidenceComparisonMetricRow
    )
    assert (
        lab.TradeProposalEvidenceComparisonReport
        is TradeProposalEvidenceComparisonReport
    )
    assert (
        lab.TradeProposalEvidenceComparisonSourceRow
        is TradeProposalEvidenceComparisonSourceRow
    )
    assert (
        lab.build_trade_proposal_evidence_comparison_report
        is build_trade_proposal_evidence_comparison_report
    )


def test_level_2_node_10_public_api_exports():
    expected_exports = {
        "TradeProposalEvidenceComparisonHistoryConfig",
        "TradeProposalEvidenceComparisonHistoryConfigVersionSummary",
        "TradeProposalEvidenceComparisonHistoryFindingSummary",
        "TradeProposalEvidenceComparisonHistoryGateResult",
        "TradeProposalEvidenceComparisonHistoryLog",
        "TradeProposalEvidenceComparisonHistoryReport",
        "TradeProposalEvidenceComparisonHistorySourceTransition",
        "TradeProposalEvidenceComparisonHistoryStatusRow",
        "build_trade_proposal_evidence_comparison_history_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert (
        lab.TradeProposalEvidenceComparisonHistoryConfig
        is TradeProposalEvidenceComparisonHistoryConfig
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryConfigVersionSummary
        is TradeProposalEvidenceComparisonHistoryConfigVersionSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryFindingSummary
        is TradeProposalEvidenceComparisonHistoryFindingSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryGateResult
        is TradeProposalEvidenceComparisonHistoryGateResult
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryLog
        is TradeProposalEvidenceComparisonHistoryLog
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryReport
        is TradeProposalEvidenceComparisonHistoryReport
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistorySourceTransition
        is TradeProposalEvidenceComparisonHistorySourceTransition
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryStatusRow
        is TradeProposalEvidenceComparisonHistoryStatusRow
    )
    assert (
        lab.build_trade_proposal_evidence_comparison_history_report
        is build_trade_proposal_evidence_comparison_history_report
    )


def test_level_2_node_11_public_api_exports():
    expected_exports = {
        "TradeProposalEvidenceComparisonHistoryBatchHealthConfig",
        "TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthGateResult",
        "TradeProposalEvidenceComparisonHistoryBatchHealthLog",
        "TradeProposalEvidenceComparisonHistoryBatchHealthReport",
        "TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow",
        "build_trade_proposal_evidence_comparison_history_batch_health_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthConfig
        is TradeProposalEvidenceComparisonHistoryBatchHealthConfig
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthGateResult
        is TradeProposalEvidenceComparisonHistoryBatchHealthGateResult
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthLog
        is TradeProposalEvidenceComparisonHistoryBatchHealthLog
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthReport
        is TradeProposalEvidenceComparisonHistoryBatchHealthReport
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow
        is TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow
    )
    assert (
        lab.build_trade_proposal_evidence_comparison_history_batch_health_report
        is build_trade_proposal_evidence_comparison_history_batch_health_report
    )


def test_level_2_node_12_public_api_exports():
    expected_exports = {
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow",
        "build_trade_proposal_evidence_comparison_history_batch_health_trend_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow
    )
    assert (
        lab.build_trade_proposal_evidence_comparison_history_batch_health_trend_report
        is build_trade_proposal_evidence_comparison_history_batch_health_trend_report
    )


def test_level_2_node_13_public_api_exports():
    expected_exports = {
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow",
        "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow
    )
    assert (
        lab.build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report
        is build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report
    )


def test_level_2_node_14_public_api_exports():
    expected_exports = {
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow",
        "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow
    )
    assert (
        lab.build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report
        is build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report
    )


def test_level_2_node_15_public_api_exports():
    expected_exports = {
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow",
        "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport
    )
    assert (
        lab.TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow
        is TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow
    )
    assert (
        lab.build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report
        is build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report
    )


def test_proposal_evidence_comparison_artifact_registry_public_api_exports():
    expected_exports = {
        "PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS",
        "REPORT_ONLY_FORBIDDEN_SURFACES",
        "ProposalEvidenceComparisonArtifactDefinition",
        "get_proposal_evidence_comparison_artifact",
        "list_proposal_evidence_comparison_artifacts",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS is PROPOSAL_EVIDENCE_COMPARISON_ARTIFACTS
    assert lab.REPORT_ONLY_FORBIDDEN_SURFACES is REPORT_ONLY_FORBIDDEN_SURFACES
    assert (
        lab.ProposalEvidenceComparisonArtifactDefinition
        is ProposalEvidenceComparisonArtifactDefinition
    )
    assert (
        lab.get_proposal_evidence_comparison_artifact
        is get_proposal_evidence_comparison_artifact
    )
    assert (
        lab.list_proposal_evidence_comparison_artifacts
        is list_proposal_evidence_comparison_artifacts
    )


def test_public_api_does_not_export_private_or_boundary_constants():
    boundary_constants = (
        (
            comparison_history,
            "DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT",
        ),
        (
            comparison_history_batch_health,
            "DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_BOUNDARY_STATEMENT",
        ),
        (
            batch_health_trend,
            "DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT",
        ),
        (
            batch_health_trend_batch,
            "DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_BOUNDARY_STATEMENT",
        ),
        (
            batch_health_trend_batch_health,
            "DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_BOUNDARY_STATEMENT",
        ),
        (
            importlib.import_module(
                "polymarket_alpha_lab."
                "proposal_evidence_comparison_history_batch_health_trend_batch_health_trend",
            ),
            "DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT",
        ),
    )

    for module, boundary_constant in boundary_constants:
        assert hasattr(module, boundary_constant)
        assert boundary_constant not in lab.__all__
        assert not hasattr(lab, boundary_constant)
    assert not any(name.startswith("_") for name in lab.__all__)
    assert not any("BOUNDARY" in name for name in lab.__all__)
