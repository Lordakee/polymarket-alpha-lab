"""Read-only DB helper for paper recommendation cycle action gates."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import paper_recommendation_cycle_snapshot_store
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateConfig,
    PaperRecommendationCycleActionGateReport,
    build_paper_recommendation_cycle_action_gate_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_review import (
    PaperRecommendationCycleReviewConfig,
    build_paper_recommendation_cycle_review_report,
)


def load_paper_recommendation_cycle_action_gate_report(
    *,
    generated_at: datetime,
    review_config: PaperRecommendationCycleReviewConfig,
    action_gate_config: PaperRecommendationCycleActionGateConfig,
    connection: Any,
    source_config_version: str | None = None,
    limit: int | None = None,
    table_name: str = "paper_recommendation_cycle_snapshots",
) -> PaperRecommendationCycleActionGateReport:
    snapshots = (
        paper_recommendation_cycle_snapshot_store.load_paper_recommendation_cycle_snapshots(
            connection,
            config_version=source_config_version,
            limit=limit,
            table_name=table_name,
        )
    )
    review_report = build_paper_recommendation_cycle_review_report(
        tuple(reversed(snapshots)),
        config=review_config,
        generated_at=generated_at,
    )
    return build_paper_recommendation_cycle_action_gate_report(
        review_report,
        config=action_gate_config,
        generated_at=generated_at,
    )


__all__ = (
    "load_paper_recommendation_cycle_action_gate_report",
)
