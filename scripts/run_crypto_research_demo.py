"""Synthetic Coinbase candles + Gamma context -> actual Agent loop, with no I/O."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import json

from polymarket_alpha_lab.team_research_crypto_candles import CoinbaseCandleSnapshot, CryptoCandleWindow, PRODUCTS
from polymarket_alpha_lab.team_research_crypto_pipeline import run_crypto_research_from_snapshots
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot
from run_team_research_demo import ScriptedDemoModel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team", choices=tuple(PRODUCTS), default="crypto_eth")
    args = parser.parse_args(argv)
    now = datetime(2026, 9, 12, tzinfo=UTC)
    window = CryptoCandleWindow(PRODUCTS[args.team], now - timedelta(hours=2), now)
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    stamp = (window.start - epoch) // timedelta(seconds=1)
    candles = CoinbaseCandleSnapshot(window, now, json.dumps([
        [stamp, 95, 110, 100, 105, 2], [stamp + 3600, 100, 115, 105, 110, 3],
    ]).encode())
    market = GammaMarketSnapshot("demo-crypto-market", now, json.dumps(dict(
        slug="demo-crypto-market", conditionId="demo-condition", question="Synthetic future price event?",
        description="Synthetic YES/NO rule; not a real contract or settlement oracle.",
        outcomes=["Yes", "No"], active=True, closed=False, endDate="2026-09-13T00:00:00Z",
    )).encode())
    result = run_crypto_research_from_snapshots(market, candles, task_id="demo", team_id=args.team,
        condition_id="demo-condition", as_of=now, model_factory=lambda _: ScriptedDemoModel())
    research = result.market_run.research if result.market_run else None
    print(json.dumps(dict(
        synthetic_demo=True, public_network_called=False, live_model_called=False,
        team_id=args.team, candle_status=result.candles.status, candle_count=result.candles.accepted_count,
        source_count=1 if result.candles.evidence else 0, raw_content_sha256=result.candles.raw_content_sha256,
        research_status=research.status if research else None,
        probability_yes=str(research.probability_yes) if research else None,
        tool_trace=research.tool_trace if research else (), paper_only=True, report_only=True, readonly=True,
    ), indent=2))
    return 0 if research is not None and research.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
