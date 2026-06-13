import polymarket_alpha_lab as lab
from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill, PaperOrder, simulate_order_book_fill
from polymarket_alpha_lab.research import ResearchPacket, build_research_packet


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
