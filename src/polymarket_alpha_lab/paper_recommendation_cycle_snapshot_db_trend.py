"""Read-only DB helper for paper recommendation cycle snapshot trends."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import paper_recommendation_cycle_snapshot_store
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot_trend import (
    PaperRecommendationCycleSnapshotTrendReport,
    build_paper_recommendation_cycle_snapshot_trend_report,
)


def load_paper_recommendation_cycle_snapshot_trend_report(
    *,
    generated_at: datetime,
    config_version: str,
    connection: Any,
    source_config_version: str | None = None,
    limit: int | None = None,
    table_name: str = "paper_recommendation_cycle_snapshots",
) -> PaperRecommendationCycleSnapshotTrendReport:
    snapshots = (
        paper_recommendation_cycle_snapshot_store.load_paper_recommendation_cycle_snapshots(
            connection,
            config_version=source_config_version,
            limit=limit,
            table_name=table_name,
        )
    )
    if not snapshots:
        raise ValueError("no paper recommendation cycle snapshots found")

    return build_paper_recommendation_cycle_snapshot_trend_report(
        generated_at=generated_at,
        config_version=config_version,
        snapshots=tuple(reversed(snapshots)),
    )


__all__ = (
    "load_paper_recommendation_cycle_snapshot_trend_report",
)
