"""Read-only loader composition for the investment-ledger health trend gate."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_gate import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig,
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport,
    build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_load import (
    load_paper_autonomous_investment_ledger_db_history_health_trend_report,
)

__all__ = (
    "load_paper_autonomous_investment_ledger_db_history_health_trend_gate_report",
)


def load_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    health_config: PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
    trend_config: PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
    gate_config: PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig,
    generated_at: datetime,
) -> PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport:
    if type(health_config) is not PaperAutonomousInvestmentLedgerDbHistoryHealthConfig:
        raise ValueError(
            "health_config must be a "
            "PaperAutonomousInvestmentLedgerDbHistoryHealthConfig",
        )
    if type(trend_config) is not PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig:
        raise ValueError(
            "trend_config must be a "
            "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig",
        )
    if type(gate_config) is not PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig:
        raise ValueError(
            "gate_config must be a "
            "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateConfig",
        )
    trend_report = load_paper_autonomous_investment_ledger_db_history_health_trend_report(
        connection,
        limit=limit,
        table_name=table_name,
        health_config=health_config,
        trend_config=trend_config,
        generated_at=generated_at,
    )
    return build_paper_autonomous_investment_ledger_db_history_health_trend_gate_report(
        trend_report,
        config=gate_config,
        generated_at=generated_at,
    )
