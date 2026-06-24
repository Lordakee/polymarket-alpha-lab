"""Read-only loader composition for the allocation proposal DB-history health trend."""

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
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend import (
    PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendReport,
    build_paper_autonomous_allocation_proposal_db_history_health_trend_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_prefix_load import (
    load_paper_autonomous_allocation_proposal_db_history_prefix_reports,
)

__all__ = ("load_paper_autonomous_allocation_proposal_db_history_health_trend_report",)


def load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    health_config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    trend_config: PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendReport:
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
    if (
        type(trend_config)
        is not PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig
    ):
        raise ValueError(
            "trend_config must be a "
            "PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig",
        )

    history_reports = load_paper_autonomous_allocation_proposal_db_history_prefix_reports(
        connection,
        limit=limit,
        table_name=table_name,
        history_config=history_config,
    )
    health_reports: list[PaperAutonomousAllocationProposalDbHistoryHealthReport] = []
    if not history_reports:
        health_reports.append(
            build_paper_autonomous_allocation_proposal_db_history_health_report(
                (),
                config=health_config,
                generated_at=generated_at,
            ),
        )
    else:
        source_history_reports = []
        for history_report in history_reports:
            source_history_reports.append(history_report)
            health_reports.append(
                build_paper_autonomous_allocation_proposal_db_history_health_report(
                    tuple(source_history_reports),
                    config=health_config,
                    generated_at=history_report.generated_at,
                ),
            )
    return build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
        tuple(health_reports),
        config=trend_config,
        generated_at=generated_at,
    )
