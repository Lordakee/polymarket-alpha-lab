"""Read-only loader composition for persisted allocation proposal health trend."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
    PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    PaperAutonomousAllocationProposalDbHistoryHealthReport,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend import (
    PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendReport,
    build_paper_autonomous_allocation_proposal_db_history_health_trend_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
    load_paper_autonomous_allocation_proposal_db_history_health_reports,
)

__all__ = ("load_paper_autonomous_allocation_proposal_db_history_health_trend_report",)


def load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    health_config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    trend_config: PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
    if (
        type(health_config)
        is not PaperAutonomousAllocationProposalDbHistoryHealthConfig
    ):
        raise ValueError(
            "health_config must be a "
            "PaperAutonomousAllocationProposalDbHistoryHealthConfig",
        )
    if (
        type(trend_config)
        is not PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig
    ):
        raise ValueError(
            "trend_config must be a "
            "PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig",
        )

    newest_first_health_reports = (
        load_paper_autonomous_allocation_proposal_db_history_health_reports(
            connection,
            config_version=health_config.config_version,
            limit=limit,
            table_name=table_name,
        )
    )
    health_reports: tuple[PaperAutonomousAllocationProposalDbHistoryHealthReport, ...] = (
        tuple(reversed(newest_first_health_reports))
    )
    return build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
        health_reports,
        config=trend_config,
        generated_at=generated_at,
    )
