"""Read-only DB helper for paper recommendation cycle snapshot reviews."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import paper_recommendation_cycle_snapshot_store
from polymarket_alpha_lab.paper_recommendation_cycle_review import (
    PaperRecommendationCycleReviewConfig,
    PaperRecommendationCycleReviewReport,
    build_paper_recommendation_cycle_review_report,
)


def load_paper_recommendation_cycle_review_report(
    *,
    generated_at: datetime,
    config: PaperRecommendationCycleReviewConfig,
    connection: Any,
    source_config_version: str | None = None,
    limit: int | None = None,
    table_name: str = "paper_recommendation_cycle_snapshots",
) -> PaperRecommendationCycleReviewReport:
    snapshots = (
        paper_recommendation_cycle_snapshot_store.load_paper_recommendation_cycle_snapshots(
            connection,
            config_version=source_config_version,
            limit=limit,
            table_name=table_name,
        )
    )
    return build_paper_recommendation_cycle_review_report(
        tuple(reversed(snapshots)),
        config=config,
        generated_at=generated_at,
    )


__all__ = (
    "load_paper_recommendation_cycle_review_report",
)
