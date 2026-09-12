"""Closed spot candles -> Gamma intake -> cited research, without implicit I/O."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime

from polymarket_alpha_lab.team_research_agent import ResearchModel
from polymarket_alpha_lab.team_research_agent_types import ResearchAgentLimits, hard_flags
from polymarket_alpha_lab.team_research_crypto_candles import (
    CoinbaseCandleSnapshot, CryptoCandleIntake, prepare_crypto_candle_evidence,
)
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot
from polymarket_alpha_lab.team_research_market_pipeline import (
    MarketTeamResearchRun, run_team_research_from_market_snapshot,
)


@dataclass(frozen=True, slots=True)
class CryptoMarketResearchRun:
    candles: CryptoCandleIntake
    market_run: MarketTeamResearchRun | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        hard_flags(self)
        if type(self.candles) is not CryptoCandleIntake:
            raise ValueError("expected exact candle intake")
        self.candles.__post_init__()
        if self.candles.status == "blocked":
            if self.market_run is not None:
                raise ValueError("blocked candles cannot contain a research run")
            return
        if type(self.market_run) is not MarketTeamResearchRun:
            raise ValueError("prepared candles require a market intake result")
        self.market_run.__post_init__()
        intake = self.market_run.intake
        for name in ("team_id", "condition_id", "as_of"):
            if getattr(intake, name) != getattr(self.candles, name):
                raise ValueError("crypto research scope mismatch")
        if intake.status == "prepared" and intake.source_receipts != (self.candles.receipt,):
            raise ValueError("research must bind the collected candle evidence")


def run_crypto_research_from_snapshots(
    market_snapshot: GammaMarketSnapshot, candle_snapshot: CoinbaseCandleSnapshot, *,
    task_id: str, team_id: str, condition_id: str, as_of: datetime,
    model_factory: Callable[[str], ResearchModel],
    limits: ResearchAgentLimits = ResearchAgentLimits(), max_context_age_seconds: int = 300,
) -> CryptoMarketResearchRun:
    """Reject malformed/gapped/stale/unclosed candles before model construction.

    Callers explicitly retrieve snapshots; this function performs no fetches.
    Only BTC/ETH USD spot observations are collected, not source diversity or
    semantic settlement matching. Completed research is not forecast approval.
    """
    if not callable(model_factory):
        raise ValueError("model_factory must be callable")
    if type(market_snapshot) is not GammaMarketSnapshot or type(limits) is not ResearchAgentLimits:
        raise ValueError("expected exact Gamma snapshot and limits")
    market_snapshot, limits = replace(market_snapshot), replace(limits)
    candles = prepare_crypto_candle_evidence(
        candle_snapshot, team_id=team_id, condition_id=condition_id, as_of=as_of,
        max_snapshot_age_seconds=max_context_age_seconds,
        max_evidence_age_seconds=limits.max_evidence_age_seconds,
    )
    if candles.status == "blocked":
        return CryptoMarketResearchRun(candles, None)
    run = run_team_research_from_market_snapshot(
        market_snapshot, task_id=task_id, team_id=team_id, condition_id=condition_id, as_of=as_of,
        evidence=(candles.evidence,), model_factory=model_factory, limits=limits,
        max_context_age_seconds=max_context_age_seconds,
    )
    return CryptoMarketResearchRun(candles, run)


__all__ = ("CryptoMarketResearchRun", "run_crypto_research_from_snapshots")
