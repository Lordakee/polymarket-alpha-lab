"""Two-venue quality gate -> Gamma intake -> required-source research loop."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime

from polymarket_alpha_lab.team_research_agent import ResearchModel, run_team_research_agent
from polymarket_alpha_lab.team_research_agent_types import (
    ResearchAgentLimits, TeamResearchResult, hard_flags, identifier,
)
from polymarket_alpha_lab.team_research_crypto_candles import CoinbaseCandleSnapshot
from polymarket_alpha_lab.team_research_cross_source import (
    CrossSourcePolicy, CryptoCrossSourceCheck, check_crypto_cross_source,
)
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot, prepare_team_research_from_gamma
from polymarket_alpha_lab.team_research_kraken_candles import KrakenCandleSnapshot
from polymarket_alpha_lab.team_research_market_pipeline import MarketTeamResearchRun


@dataclass(frozen=True, slots=True)
class CrossSourceResearchRun:
    check: CryptoCrossSourceCheck
    market_run: MarketTeamResearchRun | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        hard_flags(self)
        if type(self.check) is not CryptoCrossSourceCheck:
            raise ValueError("expected exact cross-source check")
        self.check.__post_init__()
        if self.check.status == "blocked":
            if self.market_run is not None:
                raise ValueError("blocked sources cannot contain market research")
            return
        if type(self.market_run) is not MarketTeamResearchRun:
            raise ValueError("matched sources require a market intake result")
        self.market_run.__post_init__()
        intake = self.market_run.intake
        for name in ("team_id", "condition_id", "as_of"):
            if getattr(intake, name) != getattr(self.check, name):
                raise ValueError("cross-source research scope mismatch")
        if intake.status == "prepared" and intake.source_receipts != self.check.source_receipts:
            raise ValueError("market research must bind both exact source receipts")
        research = self.market_run.research
        if research is not None and research.status == "completed":
            if set(research.source_ids) != {item.source_id for item in self.check.source_receipts}:
                raise ValueError("completed cross-source research must cite both sources")


def run_cross_source_crypto_research(
    market: GammaMarketSnapshot, coinbase: CoinbaseCandleSnapshot, kraken: KrakenCandleSnapshot, *,
    task_id: str, team_id: str, condition_id: str, as_of: datetime,
    model_factory: Callable[[str], ResearchModel],
    limits: ResearchAgentLimits = ResearchAgentLimits(), policy: CrossSourcePolicy = CrossSourcePolicy(),
    max_context_age_seconds: int = 300,
) -> CrossSourceResearchRun:
    """No fetches or writes. Data disagreements stop before paid model work."""
    identifier("task_id", task_id)
    if type(market) is not GammaMarketSnapshot or type(limits) is not ResearchAgentLimits:
        raise ValueError("expected exact market snapshot and limits")
    if not callable(model_factory):
        raise ValueError("model_factory must be callable")
    market, limits = replace(market), replace(limits)
    check = check_crypto_cross_source(coinbase, kraken, team_id=team_id, condition_id=condition_id,
        as_of=as_of, policy=policy, max_snapshot_age_seconds=max_context_age_seconds,
        max_evidence_age_seconds=limits.max_evidence_age_seconds)
    if check.status == "blocked":
        return CrossSourceResearchRun(check, None)
    intake = prepare_team_research_from_gamma(market, task_id=task_id, team_id=team_id,
        condition_id=condition_id, as_of=as_of, evidence=check.evidence, limits=limits,
        max_context_age_seconds=max_context_age_seconds)
    if intake.status == "blocked":
        return CrossSourceResearchRun(check, MarketTeamResearchRun(intake, None))
    try:
        model = model_factory(team_id)
        if not callable(getattr(model, "complete", None)):
            raise ValueError("invalid model client")
    except Exception:
        result = TeamResearchResult(task_id, team_id, condition_id, intake.market_slug, as_of,
                                    "failed", "model_factory_failed")
    else:
        result = run_team_research_agent(intake.task, model=model, limits=limits,
            required_source_ids=tuple(item.source_id for item in check.source_receipts))
    return CrossSourceResearchRun(check, MarketTeamResearchRun(intake, result))


__all__ = ("CrossSourceResearchRun", "run_cross_source_crypto_research")
