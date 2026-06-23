"""Readback loader for persisted paper research packet quality history."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_research_packet_quality_history import (
    PaperResearchPacketQualityHistoryConfig,
    PaperResearchPacketQualityHistoryReport,
    build_paper_research_packet_quality_history_report,
)
from polymarket_alpha_lab.paper_research_packet_quality_store import (
    load_paper_research_packet_quality_reports,
)


__all__ = ("load_paper_research_packet_quality_history_report",)


def load_paper_research_packet_quality_history_report(
    connection: object,
    *,
    config_version: str | None = None,
    quality_status: str | None = None,
    limit: int | None,
    table_name: str,
    config: PaperResearchPacketQualityHistoryConfig,
    generated_at: datetime,
) -> PaperResearchPacketQualityHistoryReport:
    if type(config) is not PaperResearchPacketQualityHistoryConfig:
        raise ValueError("config must be a PaperResearchPacketQualityHistoryConfig")

    loaded_reports = load_paper_research_packet_quality_reports(
        connection,
        config_version=config_version,
        quality_status=quality_status,
        limit=limit,
        table_name=table_name,
    )
    chronological_reports = tuple(reversed(tuple(loaded_reports)))
    return build_paper_research_packet_quality_history_report(
        chronological_reports,
        config=config,
        generated_at=generated_at,
    )
