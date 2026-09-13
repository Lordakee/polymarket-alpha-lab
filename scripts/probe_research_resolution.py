"""Read one public Gamma resolution candidate; never confirm, write or trade."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import UTC, datetime
import json

from polymarket_alpha_lab.research_resolution import ResolutionSubmission, assess_resolution, condition
from polymarket_alpha_lab.team_research_gamma import GammaResearchReader
from polymarket_alpha_lab.team_research_intake import require_market_slug


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--condition-id', required=True)
    parser.add_argument('--market-slug', required=True)
    parser.add_argument('--allow-public-fetch', action='store_true')
    args = parser.parse_args(argv)
    try:
        condition(args.condition_id)
        require_market_slug(args.market_slug)
    except ValueError:
        parser.error('a canonical condition ID and market slug are required')
    if not args.allow_public_fetch:
        parser.error('--allow-public-fetch is required; this command reads public data only')
    try:
        snapshot = GammaResearchReader(allow_public_fetch=True).fetch(market_slug=args.market_slug)
        result = assess_resolution(ResolutionSubmission('public-probe', args.condition_id, snapshot, datetime.now(UTC)))
    except Exception:
        print(json.dumps({'status':'failed','reason_code':'resolution_public_probe_failed',
                          'outcome_recorded':False,'live_model_called':False}))
        return 1
    print(json.dumps({'assessment':asdict(result),'snapshot_sha256':snapshot.content_sha256,
        'fetched_at':snapshot.fetched_at.isoformat(),'outcome_recorded':False,
        'independent_confirmation_performed':False,'live_model_called':False},indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
