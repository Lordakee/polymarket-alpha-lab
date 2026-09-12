"""Explicit one-shot public candle probe; no model, credentials, DB or writes."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import json

from polymarket_alpha_lab.team_research_coinbase import CoinbaseCandleReader
from polymarket_alpha_lab.team_research_crypto_candles import (
    CryptoCandleWindow, PRODUCTS, prepare_crypto_candle_evidence,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team", choices=tuple(PRODUCTS), default="crypto_btc")
    parser.add_argument("--allow-public-fetch", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_public_fetch:
        print(json.dumps({"public_fetch_enabled": False, "live_model_called": False}))
        return 0
    # Leave one closed hour for publication lag; never request an open bucket.
    end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    window = CryptoCandleWindow(PRODUCTS[args.team], end - timedelta(hours=3), end)
    try:
        snapshot = CoinbaseCandleReader(allow_public_fetch=True).fetch(window)
        result = prepare_crypto_candle_evidence(snapshot, team_id=args.team,
            condition_id="public-probe-only", as_of=snapshot.fetched_at)
    except ValueError:
        print(json.dumps({"public_fetch_enabled": True, "status": "failed",
                          "reason_code": "public_probe_failed", "live_model_called": False}))
        return 1
    print(json.dumps({
        "public_fetch_enabled": True, "public_network_called": True, "live_model_called": False,
        "status": result.status, "reason_code": result.reason_code,
        "product_id": window.product_id, "window_start": window.start.isoformat(),
        "window_end": window.end.isoformat(), "fetched_at": snapshot.fetched_at.isoformat(),
        "accepted_count": result.accepted_count, "excluded_count": result.excluded_count,
        "missing_count": result.missing_count, "raw_content_sha256": result.raw_content_sha256,
        "evidence_content_sha256": result.receipt.content_sha256 if result.receipt else None,
        "paper_only": True, "report_only": True, "readonly": True,
    }, indent=2))
    return 0 if result.status == "prepared" else 1


if __name__ == "__main__":
    raise SystemExit(main())
