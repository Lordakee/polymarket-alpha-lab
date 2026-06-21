"""Read-only DB helper for local observability trend history."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import local_observability_trends_store
from polymarket_alpha_lab.local_observability_trends_db_history import (
    LocalObservabilityTrendsDbHistoryConfig,
    LocalObservabilityTrendsDbHistoryReport,
    build_local_observability_trends_db_history_report,
)


def load_local_observability_trends_db_history_report(
    *,
    generated_at: datetime,
    config_version: str,
    connection: Any,
    limit: int | None = None,
    table_name: str = (
        local_observability_trends_store.DEFAULT_LOCAL_OBSERVABILITY_TRENDS_TABLE
    ),
) -> LocalObservabilityTrendsDbHistoryReport:
    reports = local_observability_trends_store.load_local_observability_trends_reports(
        connection,
        limit=limit,
        table_name=table_name,
    )
    return build_local_observability_trends_db_history_report(
        tuple(reversed(reports)),
        config=LocalObservabilityTrendsDbHistoryConfig(
            config_version=config_version,
        ),
        generated_at=generated_at,
    )


__all__ = (
    "load_local_observability_trends_db_history_report",
)
