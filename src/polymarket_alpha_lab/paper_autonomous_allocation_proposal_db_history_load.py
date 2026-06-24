"""DB-API load helper for paper autonomous allocation proposal history."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
    load_paper_autonomous_allocation_proposal_reports,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    PaperAutonomousAllocationProposalDbHistoryConfig,
    PaperAutonomousAllocationProposalDbHistoryReport,
    build_paper_autonomous_allocation_proposal_db_history_report,
)


__all__ = ("load_paper_autonomous_allocation_proposal_db_history_report",)


def load_paper_autonomous_allocation_proposal_db_history_report(
    connection: object,
    *,
    config_version: str | None = None,
    proposal_status: str | None = None,
    screening_gate_status: str | None = None,
    allocation_config_version: str | None = None,
    limit: int | None,
    table_name: str,
    config: PaperAutonomousAllocationProposalDbHistoryConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryReport:
    if type(config) is not PaperAutonomousAllocationProposalDbHistoryConfig:
        raise ValueError(
            "config must be a PaperAutonomousAllocationProposalDbHistoryConfig",
        )

    loaded_reports = load_paper_autonomous_allocation_proposal_reports(
        connection,
        config_version=config_version,
        proposal_status=proposal_status,
        screening_gate_status=screening_gate_status,
        allocation_config_version=allocation_config_version,
        limit=limit,
        table_name=table_name,
    )
    chronological_reports = tuple(reversed(tuple(loaded_reports)))
    return build_paper_autonomous_allocation_proposal_db_history_report(
        chronological_reports,
        config=config,
        generated_at=generated_at,
    )
