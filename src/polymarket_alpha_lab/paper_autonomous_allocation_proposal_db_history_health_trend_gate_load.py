"""Read-only loader composition for the DB-history health trend gate."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    PaperAutonomousAllocationProposalDbHistoryConfig,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
    PaperAutonomousAllocationProposalDbHistoryHealthConfig,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend import (
    PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_gate import (
    PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig,
    PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport,
    build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_load import (
    load_paper_autonomous_allocation_proposal_db_history_health_trend_report,
)

__all__ = (
    "load_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report",
)


def load_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    history_config: PaperAutonomousAllocationProposalDbHistoryConfig,
    health_config: PaperAutonomousAllocationProposalDbHistoryHealthConfig,
    trend_config: PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig,
    gate_config: PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport:
    if type(history_config) is not PaperAutonomousAllocationProposalDbHistoryConfig:
        raise ValueError(
            "history_config must be a PaperAutonomousAllocationProposalDbHistoryConfig",
        )
    if type(health_config) is not PaperAutonomousAllocationProposalDbHistoryHealthConfig:
        raise ValueError(
            "health_config must be a PaperAutonomousAllocationProposalDbHistoryHealthConfig",
        )
    if type(trend_config) is not PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig:
        raise ValueError(
            "trend_config must be a PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig",
        )
    if (
        type(gate_config)
        is not PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig
    ):
        raise ValueError(
            "gate_config must be a PaperAutonomousAllocationProposalDbHistoryHealthTrendGateConfig",
        )
    trend_report = load_paper_autonomous_allocation_proposal_db_history_health_trend_report(
        connection,
        limit=limit,
        table_name=table_name,
        history_config=history_config,
        health_config=health_config,
        trend_config=trend_config,
        generated_at=generated_at,
    )
    return build_paper_autonomous_allocation_proposal_db_history_health_trend_gate_report(
        trend_report,
        config=gate_config,
        generated_at=generated_at,
    )
