"""Readback loader for persisted paper research packet operator-flow DB history."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history import (
    PaperResearchPacketOperatorFlowDbHistoryConfig,
    PaperResearchPacketOperatorFlowDbHistoryReport,
    build_paper_research_packet_operator_flow_db_history_report,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow_store import (
    load_paper_research_packet_operator_flow_reports,
)

__all__ = ("load_paper_research_packet_operator_flow_db_history_report",)


def load_paper_research_packet_operator_flow_db_history_report(
    connection: object,
    *,
    config_version: str | None = None,
    flow_status: str | None = None,
    limit: int | None,
    table_name: str,
    config: PaperResearchPacketOperatorFlowDbHistoryConfig,
    generated_at: datetime,
) -> PaperResearchPacketOperatorFlowDbHistoryReport:
    if type(config) is not PaperResearchPacketOperatorFlowDbHistoryConfig:
        raise ValueError("config must be a PaperResearchPacketOperatorFlowDbHistoryConfig")

    loaded_reports = load_paper_research_packet_operator_flow_reports(
        connection,
        config_version=config_version,
        flow_status=flow_status,
        limit=limit,
        table_name=table_name,
    )
    chronological_reports = tuple(reversed(tuple(loaded_reports)))
    return build_paper_research_packet_operator_flow_db_history_report(
        chronological_reports,
        config=config,
        generated_at=generated_at,
    )
