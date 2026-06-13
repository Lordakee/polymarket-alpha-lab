import polymarket_alpha_lab as lab
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
