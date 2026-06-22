"""Read-only DB helper for paper recommendation risk budget history."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from polymarket_alpha_lab import paper_recommendation_risk_budget_store
from polymarket_alpha_lab.paper_recommendation_risk_budget_db_history import (
    PaperRecommendationRiskBudgetDbHistoryConfig,
    PaperRecommendationRiskBudgetDbHistoryReport,
    build_paper_recommendation_risk_budget_db_history_report,
)


def load_paper_recommendation_risk_budget_db_history_report(
    *,
    generated_at: datetime,
    config_version: str,
    connection: Any,
    risk_budget_config_version: str | None = None,
    risk_budget_status: str | None = None,
    limit: int | None = None,
    table_name: str = "paper_recommendation_risk_budget_reports",
) -> PaperRecommendationRiskBudgetDbHistoryReport:
    reports = (
        paper_recommendation_risk_budget_store.load_paper_recommendation_risk_budget_reports(
            connection,
            config_version=risk_budget_config_version,
            status=risk_budget_status,
            limit=limit,
            table_name=table_name,
        )
    )
    return build_paper_recommendation_risk_budget_db_history_report(
        tuple(reversed(reports)),
        config=PaperRecommendationRiskBudgetDbHistoryConfig(
            config_version=config_version,
        ),
        generated_at=generated_at,
    )


__all__ = ("load_paper_recommendation_risk_budget_db_history_report",)
