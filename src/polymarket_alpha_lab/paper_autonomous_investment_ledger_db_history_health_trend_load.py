"""Read-only loader composition for persisted investment ledger health trend."""

from __future__ import annotations

from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
    PaperAutonomousInvestmentLedgerDbHistoryHealthReport,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_store import (
    load_paper_autonomous_investment_ledger_db_history_health_reports,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendReport,
    build_paper_autonomous_investment_ledger_db_history_health_trend_report,
)

__all__ = ("load_paper_autonomous_investment_ledger_db_history_health_trend_report",)


def load_paper_autonomous_investment_ledger_db_history_health_trend_report(
    connection: object,
    *,
    limit: int | None,
    table_name: str,
    health_config: PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
    trend_config: PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig,
    generated_at: datetime,
) -> PaperAutonomousInvestmentLedgerDbHistoryHealthTrendReport:
    if type(health_config) is not PaperAutonomousInvestmentLedgerDbHistoryHealthConfig:
        raise ValueError(
            "health_config must be a "
            "PaperAutonomousInvestmentLedgerDbHistoryHealthConfig",
        )
    if (
        type(trend_config)
        is not PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig
    ):
        raise ValueError(
            "trend_config must be a "
            "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendConfig",
        )

    newest_first_health_reports = (
        load_paper_autonomous_investment_ledger_db_history_health_reports(
            connection,
            config_version=health_config.config_version,
            limit=limit,
            table_name=table_name,
        )
    )
    health_reports: tuple[PaperAutonomousInvestmentLedgerDbHistoryHealthReport, ...] = (
        tuple(reversed(newest_first_health_reports))
    )
    return build_paper_autonomous_investment_ledger_db_history_health_trend_report(
        health_reports,
        config=trend_config,
        generated_at=generated_at,
    )
