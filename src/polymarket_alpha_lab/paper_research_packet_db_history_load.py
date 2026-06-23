"""DB-API load helper for paper research packet history readback."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_research_packet_db_history import (
    PaperResearchPacketDbHistoryConfig,
    PaperResearchPacketDbHistoryReport,
    build_paper_research_packet_db_history_report,
)
from polymarket_alpha_lab.paper_research_packet_store import (
    load_paper_research_packet_reports,
)


__all__ = ("load_paper_research_packet_db_history_report",)


def load_paper_research_packet_db_history_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    config: PaperResearchPacketDbHistoryConfig,
    generated_at: datetime,
) -> PaperResearchPacketDbHistoryReport:
    loaded_reports = load_paper_research_packet_reports(
        connection,
        limit=limit,
        table_name=table_name,
    )
    chronological_reports = tuple(reversed(tuple(loaded_reports)))
    return build_paper_research_packet_db_history_report(
        chronological_reports,
        config=config,
        generated_at=generated_at,
    )
