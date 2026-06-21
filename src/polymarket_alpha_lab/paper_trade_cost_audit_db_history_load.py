"""Read-only DB helper for paper-trade cost trend history."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import paper_trade_cost_audit_store
from polymarket_alpha_lab.paper_trade_cost_trend import (
    PaperTradeCostTrendConfig,
    PaperTradeCostTrendReport,
    build_paper_trade_cost_trend_report,
)


def load_paper_trade_cost_audit_db_history_report(
    *,
    generated_at: datetime,
    config_version: str,
    connection: Any,
    limit: int | None = None,
    table_name: str = (
        paper_trade_cost_audit_store.DEFAULT_PAPER_TRADE_COST_AUDIT_REPORTS_TABLE
    ),
) -> PaperTradeCostTrendReport:
    reports = paper_trade_cost_audit_store.load_paper_trade_cost_audit_reports(
        connection,
        limit=limit,
        table_name=table_name,
    )
    return build_paper_trade_cost_trend_report(
        tuple(reversed(reports)),
        config=PaperTradeCostTrendConfig(
            config_version=config_version,
        ),
        generated_at=generated_at,
    )


__all__ = (
    "load_paper_trade_cost_audit_db_history_report",
)
