"""Intake -> bounded agent composition. No implicit network or persistence."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime

from polymarket_alpha_lab.team_research_agent import ResearchModel, run_team_research_agent
from polymarket_alpha_lab.team_research_agent_types import (
    ResearchAgentLimits, ResearchEvidence, TeamResearchResult, hard_flags,
)
from polymarket_alpha_lab.team_research_intake import (
    GammaMarketSnapshot, TeamResearchIntake, prepare_team_research_from_gamma,
)


@dataclass(frozen=True, slots=True)
class MarketTeamResearchRun:
    intake: TeamResearchIntake
    research: TeamResearchResult | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        hard_flags(self)
        if type(self.intake) is not TeamResearchIntake:
            raise ValueError("expected exact intake")
        self.intake.__post_init__()
        if self.intake.status == "blocked":
            if self.research is not None:
                raise ValueError("blocked intake cannot contain model research")
            return
        if type(self.research) is not TeamResearchResult:
            raise ValueError("prepared intake requires research outcome")
        self.research.__post_init__()
        for name in ("task_id", "team_id", "condition_id", "market_slug", "as_of"):
            if getattr(self.research, name) != getattr(self.intake, name):
                raise ValueError("research scope does not match intake")
        if not set(self.research.source_ids).issubset(item.source_id for item in self.intake.source_receipts):
            raise ValueError("research citations do not match intake receipts")


def run_team_research_from_market_snapshot(
    snapshot: GammaMarketSnapshot, *, task_id: str, team_id: str, condition_id: str,
    as_of: datetime, evidence: tuple[ResearchEvidence, ...],
    model_factory: Callable[[str], ResearchModel],
    limits: ResearchAgentLimits = ResearchAgentLimits(), max_context_age_seconds: int = 300,
) -> MarketTeamResearchRun:
    """Reject unsuitable data before constructing a possibly paid model client.

    Gamma retrieval is a separate explicit caller action. Models see only the
    validated question/rules and eligible evidence, not raw Gamma JSON/prices.
    A completed result is still an uncalibrated candidate, not approval.
    """
    if not callable(model_factory):
        raise ValueError("model_factory must be callable")
    if type(limits) is not ResearchAgentLimits:
        raise ValueError("expected exact limits")
    limits = replace(limits)
    intake = prepare_team_research_from_gamma(
        snapshot, task_id=task_id, team_id=team_id, condition_id=condition_id,
        as_of=as_of, evidence=evidence, limits=limits,
        max_context_age_seconds=max_context_age_seconds,
    )
    if intake.status == "blocked":
        return MarketTeamResearchRun(intake, None)
    try:
        model = model_factory(team_id)
        if not callable(getattr(model, "complete", None)):
            raise ValueError("invalid model client")
    except Exception:
        result = TeamResearchResult(task_id, team_id, condition_id, intake.market_slug,
                                    as_of, "failed", "model_factory_failed")
    else:
        result = run_team_research_agent(intake.task, model=model, limits=limits)
    return MarketTeamResearchRun(intake, result)


__all__ = ("MarketTeamResearchRun", "run_team_research_from_market_snapshot")
