"""Read-only DB helper for strategy risk audit history."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import strategy_risk_audit_store
from polymarket_alpha_lab.strategy_audit_history import (
    PaperStrategyRiskAuditHistoryConfig,
    PaperStrategyRiskAuditHistoryReport,
    build_paper_strategy_risk_audit_history_report,
)


def load_strategy_audit_db_history_report(
    *,
    generated_at: datetime,
    config_version: str,
    connection: Any,
    limit: int | None = None,
    table_name: str = (
        strategy_risk_audit_store.DEFAULT_STRATEGY_RISK_AUDIT_REPORTS_TABLE
    ),
) -> PaperStrategyRiskAuditHistoryReport:
    reports = strategy_risk_audit_store.load_strategy_risk_audit_reports(
        connection,
        limit=limit,
        table_name=table_name,
    )
    return build_paper_strategy_risk_audit_history_report(
        tuple(reversed(reports)),
        config=PaperStrategyRiskAuditHistoryConfig(
            config_version=config_version,
        ),
        generated_at=generated_at,
    )


__all__ = ("load_strategy_audit_db_history_report",)
