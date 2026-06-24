"""Read-only loader composition for allocation proposal metrics evaluation."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics import (
    PaperAutonomousAllocationProposalDbHistoryMetricsConfig,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_evaluation import (
    PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig,
    PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport,
    build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_load import (
    load_paper_autonomous_allocation_proposal_db_history_metrics_report,
)

__all__ = (
    "load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report",
)


def load_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    config: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport:
    if (
        type(config)
        is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig
    ):
        raise ValueError(
            "config must be a "
            "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig",
        )
    metrics_report = load_paper_autonomous_allocation_proposal_db_history_metrics_report(
        connection,
        limit=limit,
        table_name=table_name,
        config=PaperAutonomousAllocationProposalDbHistoryMetricsConfig(),
        generated_at=generated_at,
    )
    return build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
        metrics_report,
        config=config,
        generated_at=generated_at,
    )
