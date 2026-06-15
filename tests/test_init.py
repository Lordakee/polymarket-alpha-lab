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
from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill, PaperOrder, simulate_order_book_fill
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
    )

    for module, boundary_constant in boundary_constants:
        assert hasattr(module, boundary_constant)
        assert boundary_constant not in lab.__all__
        assert not hasattr(lab, boundary_constant)
    assert not any(name.startswith("_") for name in lab.__all__)
    assert not any("BOUNDARY" in name for name in lab.__all__)
