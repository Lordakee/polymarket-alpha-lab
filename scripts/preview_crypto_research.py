"""Preview a selected BTC/ETH research task using three public sources.

No database, model, key reader or registration. No network without explicit opt-in.
Review event rules/source applicability before approving a separate captured run.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json

from polymarket_alpha_lab.research_crypto_launch import CryptoLaunchBlocked, CryptoResearchSpec
from polymarket_alpha_lab.research_crypto_launch_service import fetch_crypto_research_preview


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record-id', required=True)
    parser.add_argument('--team', choices=('crypto_btc', 'crypto_eth'), required=True)
    parser.add_argument('--condition-id', required=True)
    parser.add_argument('--market-slug', required=True)
    parser.add_argument('--forecast-cutoff', required=True, help='explicit aware ISO timestamp, before scheduled event end')
    parser.add_argument('--model', required=True, help='caller-selected model label, not a model invocation')
    parser.add_argument('--lookback-hours', type=int, default=3)
    parser.add_argument('--allow-public-fetch', action='store_true')
    args = parser.parse_args(argv)
    try:
        cutoff = datetime.fromisoformat(args.forecast_cutoff.replace('Z', '+00:00'))
        spec = CryptoResearchSpec(args.record_id, args.team, args.condition_id, args.market_slug,
                                  cutoff, args.model, args.lookback_hours)
    except (TypeError, ValueError, OverflowError):
        parser.error('invalid research specification; timestamps must include an explicit timezone')
    if not args.allow_public_fetch:
        print(json.dumps(dict(status='disabled', public_fetch_enabled=False, model_called=False, database_written=False)))
        return 0
    try:
        result = fetch_crypto_research_preview(spec, allow_public_fetch=True).to_dict()
    except CryptoLaunchBlocked as error:
        print(json.dumps(dict(status='blocked', reason_code=str(error), model_called=False, database_written=False)))
        return 1
    except Exception:
        print(json.dumps(dict(status='failed', reason_code='crypto_launch_preview_failed',
                              model_called=False, database_written=False)))
        return 1
    print(json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
