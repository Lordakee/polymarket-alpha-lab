"""Read-only loader composition for probability selection/scorer agreement."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from polymarket_alpha_lab.autonomous_market_scorer_store import (
    DEFAULT_AUTONOMOUS_MARKET_SCORER_REPORTS_TABLE,
    load_autonomous_market_scorer_reports,
)
from polymarket_alpha_lab.paper_probability_selection_summary_store import (
    DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_REPORTS_TABLE,
    load_paper_probability_selection_summary_reports,
)
from polymarket_alpha_lab.probability_selection_scorer_agreement import (
    ProbabilitySelectionScorerAgreementConfig,
    ProbabilitySelectionScorerAgreementReport,
    build_probability_selection_scorer_agreement_report,
)


__all__ = ("load_probability_selection_scorer_agreement_report",)


def load_probability_selection_scorer_agreement_report(
    selection_connection: object,
    scorer_connection: object,
    *,
    generated_at: datetime,
    config: ProbabilitySelectionScorerAgreementConfig | None = None,
    selection_config_version: str | None = None,
    selection_source_queue_config_version: str | None = None,
    selection_source_cost_stress_config_version: str | None = None,
    selection_status: str | None = None,
    scorer_config_version: str | None = None,
    scorer_gate_status: str | None = None,
    selection_limit: int = 1,
    scorer_limit: int = 1,
    selection_table_name: str = DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_REPORTS_TABLE,
    scorer_table_name: str = DEFAULT_AUTONOMOUS_MARKET_SCORER_REPORTS_TABLE,
    selection_report_loader: Callable[..., object] | None = None,
    scorer_report_loader: Callable[..., object] | None = None,
) -> ProbabilitySelectionScorerAgreementReport:
    if (
        config is not None
        and type(config) is not ProbabilitySelectionScorerAgreementConfig
    ):
        raise ValueError("config must be a ProbabilitySelectionScorerAgreementConfig")
    if selection_report_loader is None:
        selection_report_loader = load_paper_probability_selection_summary_reports
    elif not callable(selection_report_loader):
        raise ValueError("selection_report_loader must be callable")
    if scorer_report_loader is None:
        scorer_report_loader = load_autonomous_market_scorer_reports
    elif not callable(scorer_report_loader):
        raise ValueError("scorer_report_loader must be callable")

    selection_reports = selection_report_loader(
        selection_connection,
        config_version=selection_config_version,
        source_queue_config_version=selection_source_queue_config_version,
        source_cost_stress_config_version=selection_source_cost_stress_config_version,
        selection_status=selection_status,
        limit=selection_limit,
        table_name=selection_table_name,
    )
    scorer_reports = scorer_report_loader(
        scorer_connection,
        config_version=scorer_config_version,
        gate_status=scorer_gate_status,
        limit=scorer_limit,
        table_name=scorer_table_name,
    )
    return build_probability_selection_scorer_agreement_report(
        selection_input=_latest_or_none(selection_reports),
        scorer_input=_latest_or_none(scorer_reports),
        generated_at=generated_at,
        config=config,
    )


def _latest_or_none(reports: object) -> object | None:
    values = tuple(reports)  # type: ignore[arg-type]
    if not values:
        return None
    return values[0]
