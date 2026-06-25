"""Read-only loader composition for investment ledger DB-history health."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
    PaperAutonomousInvestmentLedgerDbHistoryHealthReport,
    build_paper_autonomous_investment_ledger_db_history_health_report,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_store import (
    DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_REPORTS_TABLE,
    load_paper_autonomous_investment_ledger_reports,
)


__all__ = ("load_paper_autonomous_investment_ledger_db_history_health_report",)


def load_paper_autonomous_investment_ledger_db_history_health_report(
    connection: object,
    *,
    config_version: str | None = None,
    ledger_status: str | None = None,
    limit: int | None,
    table_name: str = DEFAULT_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_REPORTS_TABLE,
    config: PaperAutonomousInvestmentLedgerDbHistoryHealthConfig,
    generated_at: datetime,
    report_loader: Callable[..., object] | None = None,
) -> PaperAutonomousInvestmentLedgerDbHistoryHealthReport:
    if type(config) is not PaperAutonomousInvestmentLedgerDbHistoryHealthConfig:
        raise ValueError(
            "config must be a PaperAutonomousInvestmentLedgerDbHistoryHealthConfig",
        )
    if report_loader is None:
        report_loader = load_paper_autonomous_investment_ledger_reports
    elif not callable(report_loader):
        raise ValueError("report_loader must be callable")

    loaded_reports = report_loader(
        connection,
        config_version=config_version,
        ledger_status=ledger_status,
        limit=limit,
        table_name=table_name,
    )
    chronological_reports = tuple(reversed(tuple(loaded_reports)))  # type: ignore[arg-type]
    return build_paper_autonomous_investment_ledger_db_history_health_report(
        chronological_reports,
        config=config,
        generated_at=generated_at,
    )
