"""List private resolution work; optionally collect one bounded public batch.

The default is metadata-only DB readback. --collect --allow-public-fetch opts
into Gamma reads and unconfirmed evidence storage, never final outcomes/models.
Requires an already initialized native project database; does not initialize it.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_resolution_queue import MAX_WORKLIST_MARKETS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--collect', action='store_true')
    parser.add_argument('--allow-public-fetch', action='store_true')
    parser.add_argument('--max-requests', type=int, default=10)
    parser.add_argument('--max-markets', type=int, default=MAX_WORKLIST_MARKETS)
    parser.add_argument('--recheck-after-seconds', type=int, default=300)
    args = parser.parse_args(argv)
    if args.collect != args.allow_public_fetch:
        parser.error('--collect and --allow-public-fetch must be provided together')
    if not 1 <= args.max_requests <= 20 or not 1 <= args.max_markets <= MAX_WORKLIST_MARKETS:
        parser.error('max-requests must be 1..20 and max-markets must be 1..1000')
    if not 60 <= args.recheck_after_seconds <= 86400:
        parser.error('recheck-after-seconds must be 60..86400')
    try:
        with ProjectPostgres(args.root).session() as session:
            options = dict(max_markets=args.max_markets, recheck_after_seconds=args.recheck_after_seconds)
            if args.collect:
                result = session.collect_resolution_candidates(allow_public_fetch=True,
                    max_requests=args.max_requests, **options).to_dict()
                code = 1 if result['failed_count'] else 0
            else:
                result = session.resolution_worklist(**options).to_dict()
                code = 0
    except Exception:
        print(json.dumps({'status': 'failed', 'reason_code': 'resolution_queue_operation_failed',
            'live_model_called': False, 'confirmed_outcomes_created': 0}))
        return 1
    print(json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
