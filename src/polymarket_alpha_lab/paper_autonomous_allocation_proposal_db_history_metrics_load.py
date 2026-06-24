"""Read-only loader composition for persisted allocation proposal metrics.

Operators: v0 aggregates across all persisted proposal statuses and config
versions selected by the table and limit.
"""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics import (
    PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
    PaperAutonomousAllocationProposalDbHistoryMetricsReport,
    build_paper_autonomous_allocation_proposal_db_history_metrics_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
    load_paper_autonomous_allocation_proposal_reports,
)

__all__ = (
    "load_paper_autonomous_allocation_proposal_db_history_metrics_report",
)


def load_paper_autonomous_allocation_proposal_db_history_metrics_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    config: PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryMetricsReport:
    if type(config) is not PaperAutonomousAllocationProposalDbHistoryMetricsConfig:
        raise ValueError(
            "config must be a "
            "PaperAutonomousAllocationProposalDbHistoryMetricsConfig",
        )

    loaded_reports = load_paper_autonomous_allocation_proposal_reports(
        connection,
        limit=limit,
        table_name=table_name,
    )
    chronological_reports = tuple(reversed(tuple(loaded_reports)))
    return build_paper_autonomous_allocation_proposal_db_history_metrics_report(
        chronological_reports,
        config=config,
        generated_at=generated_at,
    )
