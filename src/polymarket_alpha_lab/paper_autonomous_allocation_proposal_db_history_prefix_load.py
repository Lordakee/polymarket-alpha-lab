"""Read-only prefix-window loader for allocation proposal DB-history reports."""

from __future__ import annotations

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    PaperAutonomousAllocationProposalDbHistoryConfig,
    PaperAutonomousAllocationProposalDbHistoryReport,
    build_paper_autonomous_allocation_proposal_db_history_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
    load_paper_autonomous_allocation_proposal_reports,
)

__all__ = ("load_paper_autonomous_allocation_proposal_db_history_prefix_reports",)


def load_paper_autonomous_allocation_proposal_db_history_prefix_reports(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
) -> tuple[PaperAutonomousAllocationProposalDbHistoryReport, ...]:
    if type(history_config) is not PaperAutonomousAllocationProposalDbHistoryConfig:
        raise ValueError(
            "history_config must be a "
            "PaperAutonomousAllocationProposalDbHistoryConfig",
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
    history_reports: list[PaperAutonomousAllocationProposalDbHistoryReport] = []
    minimum_report_count_index = history_config.min_report_count - 1
    for report_index in range(minimum_report_count_index, len(proposal_reports)):
        history_reports.append(
            build_paper_autonomous_allocation_proposal_db_history_report(
                proposal_reports[: report_index + 1],
                config=history_config,
                generated_at=proposal_reports[report_index].generated_at,
            ),
        )
    return tuple(history_reports)
