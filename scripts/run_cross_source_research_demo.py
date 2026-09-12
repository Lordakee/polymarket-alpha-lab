"""Synthetic two-venue -> Gamma -> two-source-cited Agent demo. No network."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import json

from polymarket_alpha_lab.team_research_agent_types import ResearchModelReply, ResearchToolCall
from polymarket_alpha_lab.team_research_crypto_candles import CoinbaseCandleSnapshot, CryptoCandleWindow, EPOCH, PRODUCTS
from polymarket_alpha_lab.team_research_cross_source_pipeline import run_cross_source_crypto_research
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot
from polymarket_alpha_lab.team_research_kraken_candles import KrakenCandleSnapshot, PAIRS


class SyntheticModel:
    """Deterministic protocol fixture, not an LLM or forecasting strategy."""
    def __init__(self) -> None:
        self.step = 0
        self.ids = []

    def complete(self, *, messages_json: str, max_output_tokens: int) -> ResearchModelReply:
        self.step += 1
        messages = json.loads(messages_json)
        if self.step == 1:
            calls = (ResearchToolCall("search", "search_evidence", '{"query":"*"}'),)
        elif self.step == 2:
            self.ids = [row["source_id"] for row in json.loads(messages[-1]["content"])["sources"]]
            calls = tuple(ResearchToolCall(f"read-{index}", "read_evidence", json.dumps({"source_id": source}))
                          for index, source in enumerate(self.ids))
        else:
            calls = (ResearchToolCall("finish", "finish_research", json.dumps({
                "probability_yes": "0.5", "confidence": "0.1", "source_ids": self.ids,
                "summary": "Synthetic demonstration only; not a market forecast.",
            })),)
        return ResearchModelReply(calls, 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team", choices=tuple(PRODUCTS), default="crypto_eth")
    args = parser.parse_args(argv)
    now = datetime(2026, 9, 12, tzinfo=UTC)
    w = CryptoCandleWindow(PRODUCTS[args.team], now-timedelta(hours=2), now)
    start = (w.start-EPOCH)//timedelta(seconds=1)
    cb = CoinbaseCandleSnapshot(w, now, json.dumps([[start+n*3600, 90, 110, 100, 100, 2] for n in range(2)]).encode())
    kr = KrakenCandleSnapshot(w, now, json.dumps({"error":[],"result":{
        PAIRS[w.product_id][1]: [[start+n*3600,"100","110","90","100.1","100","2",3] for n in range(3)],
        "last":start+3600}}).encode())
    market = GammaMarketSnapshot("demo-market", now, json.dumps(dict(slug="demo-market",conditionId="demo",
        question="Synthetic event?",description="Synthetic criterion only.",active=True,closed=False,
        outcomes='["Yes","No"]',endDate="2026-09-13T00:00:00Z")).encode())
    run = run_cross_source_crypto_research(market, cb, kr, task_id="demo", team_id=args.team,
        condition_id="demo", as_of=now, model_factory=lambda _: SyntheticModel())
    research = run.market_run.research if run.market_run else None
    print(json.dumps({"synthetic_demo":True,"public_network_called":False,"live_model_called":False,
        "cross_source_status":run.check.status,"max_close_divergence_bps":str(run.check.max_observed_divergence_bps),
        "research_status":research.status if research else None,
        "cited_source_count":len(research.source_ids) if research else 0,
        "tool_trace":research.tool_trace if research else (),
        "paper_only":True,"report_only":True,"readonly":True},indent=2))
    return 0 if research is not None and research.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
