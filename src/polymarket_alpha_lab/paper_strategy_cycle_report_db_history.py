"""Read-only DB loader for paper strategy cycle report history."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import paper_strategy_cycle_report_store
from polymarket_alpha_lab.paper_strategy_cycle_report_history import (
    PaperStrategyCycleReportHistoryConfig,
    PaperStrategyCycleReportHistoryReport,
    build_paper_strategy_cycle_report_history_report,
)


__all__ = ("load_paper_strategy_cycle_report_history_report",)


def load_paper_strategy_cycle_report_history_report(
    *,
    generated_at: datetime,
    config: PaperStrategyCycleReportHistoryConfig,
    connection: Any,
    source_config_version: str | None = None,
    limit: int | None = None,
    table_name: str = "paper_strategy_cycle_reports",
) -> PaperStrategyCycleReportHistoryReport:
    reports = paper_strategy_cycle_report_store.load_paper_strategy_cycle_reports(
        connection,
        config_version=source_config_version,
        limit=limit,
        table_name=table_name,
    )
    if not reports:
        raise ValueError("no paper strategy cycle reports found")
    return build_paper_strategy_cycle_report_history_report(
        tuple(reversed(reports)),
        config=config,
        generated_at=generated_at,
    )
