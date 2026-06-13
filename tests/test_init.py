import polymarket_alpha_lab as lab
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
