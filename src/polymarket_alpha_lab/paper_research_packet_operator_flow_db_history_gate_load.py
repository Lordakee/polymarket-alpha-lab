"""Read-only loader composition for the operator-flow DB history gate."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history import (
    PaperResearchPacketOperatorFlowDbHistoryConfig,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate import (
    PaperResearchPacketOperatorFlowDbHistoryGateConfig,
    PaperResearchPacketOperatorFlowDbHistoryGateReport,
    build_paper_research_packet_operator_flow_db_history_gate_report,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_load import (
    load_paper_research_packet_operator_flow_db_history_report,
)

__all__ = ("load_paper_research_packet_operator_flow_db_history_gate_report",)


def load_paper_research_packet_operator_flow_db_history_gate_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    history_config: PaperResearchPacketOperatorFlowDbHistoryConfig,
    gate_config: PaperResearchPacketOperatorFlowDbHistoryGateConfig,
    generated_at: datetime,
) -> PaperResearchPacketOperatorFlowDbHistoryGateReport:
    if type(history_config) is not PaperResearchPacketOperatorFlowDbHistoryConfig:
        raise ValueError(
            "history_config must be a "
            "PaperResearchPacketOperatorFlowDbHistoryConfig",
        )
    if type(gate_config) is not PaperResearchPacketOperatorFlowDbHistoryGateConfig:
        raise ValueError(
            "gate_config must be a "
            "PaperResearchPacketOperatorFlowDbHistoryGateConfig",
        )

    history_report = load_paper_research_packet_operator_flow_db_history_report(
        connection,
        limit=limit,
        table_name=table_name,
        config=history_config,
        generated_at=generated_at,
    )
    return build_paper_research_packet_operator_flow_db_history_gate_report(
        history_report,
        config=gate_config,
        generated_at=generated_at,
    )
