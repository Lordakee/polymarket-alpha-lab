"""Read-only loader composition for rank stability DB-history health."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from polymarket_alpha_lab.paper_project_screening_rank_stability_db_history_health import (
    PaperProjectScreeningRankStabilityDbHistoryHealthConfig,
    PaperProjectScreeningRankStabilityDbHistoryHealthReport,
    build_paper_project_screening_rank_stability_db_history_health_report,
)
from polymarket_alpha_lab.paper_project_screening_rank_stability_store import (
    DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_REPORTS_TABLE,
    load_paper_project_screening_rank_stability_reports,
)


__all__ = (
    "load_paper_project_screening_rank_stability_db_history_health_report",
)


def load_paper_project_screening_rank_stability_db_history_health_report(
    connection: object,
    *,
    config_version: str | None = None,
    stability_status: str | None = None,
    limit: int | None,
    table_name: str = DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_REPORTS_TABLE,
    config: PaperProjectScreeningRankStabilityDbHistoryHealthConfig,
    generated_at: datetime,
    report_loader: Callable[..., object] | None = None,
) -> PaperProjectScreeningRankStabilityDbHistoryHealthReport:
    if type(config) is not PaperProjectScreeningRankStabilityDbHistoryHealthConfig:
        raise ValueError(
            "config must be a "
            "PaperProjectScreeningRankStabilityDbHistoryHealthConfig",
        )
    if report_loader is None:
        report_loader = load_paper_project_screening_rank_stability_reports
    elif not callable(report_loader):
        raise ValueError("report_loader must be callable")

    loaded_reports = report_loader(
        connection,
        config_version=config_version,
        stability_status=stability_status,
        limit=limit,
        table_name=table_name,
    )
    chronological_reports = tuple(reversed(tuple(loaded_reports)))  # type: ignore[arg-type]
    return build_paper_project_screening_rank_stability_db_history_health_report(
        chronological_reports,
        config=config,
        generated_at=generated_at,
    )
