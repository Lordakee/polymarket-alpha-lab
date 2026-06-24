"""Read-only loader composition for the allocation proposal DB-history health node."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    PaperAutonomousAllocationProposalDbHistoryConfig,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
    PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    PaperAutonomousAllocationProposalDbHistoryHealthReport,
    build_paper_autonomous_allocation_proposal_db_history_health_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_prefix_load import (
    load_paper_autonomous_allocation_proposal_db_history_prefix_reports,
)

__all__ = ("load_paper_autonomous_allocation_proposal_db_history_health_report",)


def load_paper_autonomous_allocation_proposal_db_history_health_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    health_config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryHealthReport:
    if type(history_config) is not PaperAutonomousAllocationProposalDbHistoryConfig:
        raise ValueError(
            "history_config must be a "
            "PaperAutonomousAllocationProposalDbHistoryConfig",
        )
    if (
        type(health_config)
        is not PaperAutonomousAllocationProposalDbHistoryHealthConfig
    ):
        raise ValueError(
            "health_config must be a "
            "PaperAutonomousAllocationProposalDbHistoryHealthConfig",
        )

    source_history_reports = load_paper_autonomous_allocation_proposal_db_history_prefix_reports(
        connection,
        limit=limit,
        table_name=table_name,
        history_config=history_config,
    )
    return build_paper_autonomous_allocation_proposal_db_history_health_report(
        source_history_reports,
        config=health_config,
        generated_at=generated_at,
    )
