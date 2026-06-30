"""Read-only DB helper for paper-trade cost audit source records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import paper_trade_journal_store
from polymarket_alpha_lab.paper_trade_cost_audit import (
    PaperTradeCostAuditConfig,
    PaperTradeCostAuditReport,
    build_paper_trade_cost_audit_report,
)


def load_paper_trade_journal_db_cost_audit_report(
    *,
    generated_at: datetime,
    config_version: str,
    connection: Any,
    condition_id: str | None = None,
    token_id: str | None = None,
    limit: int | None = None,
    table_name: str = "paper_trade_journal_records",
) -> PaperTradeCostAuditReport:
    newest_first_records = paper_trade_journal_store.load_paper_trade_records(
        connection,
        condition_id=condition_id,
        token_id=token_id,
        limit=limit,
        table_name=table_name,
    )
    append_chronology_records = tuple(reversed(newest_first_records))
    return build_paper_trade_cost_audit_report(
        append_chronology_records,
        config=PaperTradeCostAuditConfig(config_version=config_version),
        generated_at=generated_at,
    )


__all__ = (
    "load_paper_trade_journal_db_cost_audit_report",
)
