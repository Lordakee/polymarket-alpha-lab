"""Read-only DB helper for outcome-tracking freshness history."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import outcome_tracking_store
from polymarket_alpha_lab.outcome_freshness import (
    OutcomeFreshnessConfig,
    OutcomeFreshnessReport,
    build_outcome_freshness_report,
)


def load_outcome_tracking_db_history_report(
    *,
    generated_at: datetime,
    config_version: str,
    connection: Any,
    stale_after_seconds: int,
    limit: int | None = None,
    table_name: str = outcome_tracking_store._DEFAULT_TABLE_NAME,
) -> OutcomeFreshnessReport:
    reports = outcome_tracking_store.load_outcome_tracking_reports(
        connection,
        limit=limit,
        table_name=table_name,
    )
    return build_outcome_freshness_report(
        tuple(reversed(reports)),
        config=OutcomeFreshnessConfig(
            config_version=config_version,
            stale_after_seconds=stale_after_seconds,
        ),
        generated_at=generated_at,
    )


__all__ = (
    "load_outcome_tracking_db_history_report",
)
