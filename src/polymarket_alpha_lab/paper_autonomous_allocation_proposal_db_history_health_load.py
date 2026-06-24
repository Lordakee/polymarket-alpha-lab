"""Read-only loader composition for the allocation proposal DB-history health node."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    PaperAutonomousAllocationProposalDbHistoryConfig,
    PaperAutonomousAllocationProposalDbHistoryReport,
    build_paper_autonomous_allocation_proposal_db_history_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
    PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    PaperAutonomousAllocationProposalDbHistoryHealthReport,
    build_paper_autonomous_allocation_proposal_db_history_health_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
    load_paper_autonomous_allocation_proposal_reports,
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

    proposal_reports = tuple(
        reversed(
            tuple(
                load_paper_autonomous_allocation_proposal_reports(
                    connection,
                    limit=limit,
                    table_name=table_name,
                ),
            ),
        ),
    )

    source_history_reports: list[PaperAutonomousAllocationProposalDbHistoryReport] = []
    minimum_report_count_index = history_config.min_report_count - 1
    for report_index in range(minimum_report_count_index, len(proposal_reports)):
        source_history_reports.append(
            build_paper_autonomous_allocation_proposal_db_history_report(
                proposal_reports[: report_index + 1],
                config=history_config,
                generated_at=proposal_reports[report_index].generated_at,
            ),
        )

    return build_paper_autonomous_allocation_proposal_db_history_health_report(
        tuple(source_history_reports),
        config=health_config,
        generated_at=generated_at,
    )
