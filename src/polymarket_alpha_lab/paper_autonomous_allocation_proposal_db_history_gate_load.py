"""Read-only loader composition for the allocation proposal DB-history gate."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    PaperAutonomousAllocationProposalDbHistoryConfig,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate import (
    PaperAutonomousAllocationProposalDbHistoryGateConfig,
    PaperAutonomousAllocationProposalDbHistoryGateReport,
    build_paper_autonomous_allocation_proposal_db_history_gate_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_load import (
    load_paper_autonomous_allocation_proposal_db_history_report,
)

__all__ = ("load_paper_autonomous_allocation_proposal_db_history_gate_report",)


def load_paper_autonomous_allocation_proposal_db_history_gate_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    gate_config: PaperAutonomousAllocationProposalDbHistoryGateConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryGateReport:
    if type(history_config) is not PaperAutonomousAllocationProposalDbHistoryConfig:
        raise ValueError(
            "history_config must be a "
            "PaperAutonomousAllocationProposalDbHistoryConfig",
        )
    if type(gate_config) is not PaperAutonomousAllocationProposalDbHistoryGateConfig:
        raise ValueError(
            "gate_config must be a "
            "PaperAutonomousAllocationProposalDbHistoryGateConfig",
        )

    history_report = load_paper_autonomous_allocation_proposal_db_history_report(
        connection,
        limit=limit,
        table_name=table_name,
        config=history_config,
        generated_at=generated_at,
    )
    return build_paper_autonomous_allocation_proposal_db_history_gate_report(
        history_report,
        config=gate_config,
        generated_at=generated_at,
    )
