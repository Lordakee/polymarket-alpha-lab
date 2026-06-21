"""Read-only DB helper for deriving cost trends from paper trade journal rows."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import paper_trade_journal_store
from polymarket_alpha_lab.paper_trade_cost_audit import (
    PaperTradeCostAuditConfig,
    build_paper_trade_cost_audit_report,
)
from polymarket_alpha_lab.paper_trade_cost_trend import (
    PaperTradeCostTrendConfig,
    PaperTradeCostTrendReport,
    build_paper_trade_cost_trend_report,
)


def load_paper_trade_journal_db_cost_trend_report(
    *,
    generated_at: datetime,
    config_version: str,
    connection: Any,
    limit: int | None = None,
    table_name: str = "paper_trade_journal_records",
) -> PaperTradeCostTrendReport:
    trade_records = paper_trade_journal_store.load_paper_trade_records(
        connection,
        limit=limit,
        table_name=table_name,
    )
    append_order_records = tuple(reversed(trade_records))
    cost_audit_reports = tuple(
        build_paper_trade_cost_audit_report(
            append_order_records[:prefix_size],
            config=PaperTradeCostAuditConfig(
                config_version="paper-trade-cost-audit-v0",
            ),
            generated_at=generated_at,
        )
        for prefix_size in range(1, len(append_order_records) + 1)
    )
    return build_paper_trade_cost_trend_report(
        cost_audit_reports,
        config=PaperTradeCostTrendConfig(
            config_version=config_version,
        ),
        generated_at=generated_at,
    )


__all__ = (
    "load_paper_trade_journal_db_cost_trend_report",
)
