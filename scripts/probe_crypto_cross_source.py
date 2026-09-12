"""One-shot public Coinbase/Kraken comparison; no models, credentials or DB."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import json

from polymarket_alpha_lab.team_research_coinbase import CoinbaseCandleReader
from polymarket_alpha_lab.team_research_crypto_candles import CryptoCandleWindow, PRODUCTS
from polymarket_alpha_lab.team_research_cross_source import check_crypto_cross_source
from polymarket_alpha_lab.team_research_kraken import KrakenCandleReader


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team", choices=tuple(PRODUCTS), default="crypto_btc")
    parser.add_argument("--allow-public-fetch", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_public_fetch:
        print(json.dumps({"public_fetch_enabled": False, "live_model_called": False}))
        return 0
    end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    window = CryptoCandleWindow(PRODUCTS[args.team], end-timedelta(hours=3), end)
    try:
        coinbase = CoinbaseCandleReader(True).fetch(window)
        kraken = KrakenCandleReader(True).fetch(window)
        result = check_crypto_cross_source(coinbase, kraken, team_id=args.team,
            condition_id="public-probe-only", as_of=datetime.now(UTC))
    except ValueError:
        print(json.dumps({"public_fetch_enabled": True, "status": "failed",
                          "reason_code": "cross_source_public_probe_failed", "live_model_called": False}))
        return 1
    print(json.dumps({
        "public_fetch_enabled": True, "public_network_called": True, "live_model_called": False,
        "status": result.status, "reason_code": result.reason_code, "product_id": window.product_id,
        "window_start": window.start.isoformat(), "window_end": window.end.isoformat(),
        "coinbase_fetched_at": coinbase.fetched_at.isoformat(), "kraken_fetched_at": kraken.fetched_at.isoformat(),
        "coinbase_raw_sha256": result.coinbase_raw_sha256, "kraken_raw_sha256": result.kraken_raw_sha256,
        "compared_count": len(result.close_divergences_bps), "kraken_excluded_count": result.kraken_excluded_count,
        "max_close_divergence_bps": str(result.max_observed_divergence_bps) if result.close_divergences_bps else None,
        "threshold_bps": str(result.policy.max_close_divergence_bps),
        "evidence_hashes": [item.content_sha256 for item in result.source_receipts],
        "paper_only": True, "report_only": True, "readonly": True,
    }, indent=2))
    return 0 if result.status == "matched" else 1


if __name__ == "__main__":
    raise SystemExit(main())
