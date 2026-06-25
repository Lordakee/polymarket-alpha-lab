"""DB-API load helper for paper execution reconciliation history."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from polymarket_alpha_lab.paper_execution_reconciliation_store import (
    load_paper_execution_reconciliation_reports,
)
from polymarket_alpha_lab.paper_execution_reconciliation_db_history import (
    PaperExecutionReconciliationDbHistoryConfig,
    PaperExecutionReconciliationDbHistoryReport,
    build_paper_execution_reconciliation_db_history_report,
)


__all__ = ("load_paper_execution_reconciliation_db_history_report",)


def load_paper_execution_reconciliation_db_history_report(
    connection: object,
    *,
    config_version: str | None = None,
    reconciliation_status: str | None = None,
    limit: int | None,
    table_name: str,
    config: PaperExecutionReconciliationDbHistoryConfig,
    generated_at: datetime,
    report_loader: Callable[..., object] | None = None,
) -> PaperExecutionReconciliationDbHistoryReport:
    if type(config) is not PaperExecutionReconciliationDbHistoryConfig:
        raise ValueError(
            "config must be a PaperExecutionReconciliationDbHistoryConfig",
        )

    loader = (
        load_paper_execution_reconciliation_reports
        if report_loader is None
        else report_loader
    )
    loaded_reports = loader(
        connection,
        config_version=config_version,
        reconciliation_status=reconciliation_status,
        limit=limit,
        table_name=table_name,
    )
    chronological_reports = tuple(reversed(tuple(loaded_reports)))
    return build_paper_execution_reconciliation_db_history_report(
        chronological_reports,
        config=config,
        generated_at=generated_at,
    )
