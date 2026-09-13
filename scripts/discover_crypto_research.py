"""Discover BTC/ETH candidates; optionally preview inputs. Never a model or DB run."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import json
import uuid

from polymarket_alpha_lab.research_crypto_discovery import discover_crypto_markets, TEAMS
from polymarket_alpha_lab.research_crypto_launch import CryptoResearchSpec, CryptoLaunchBlocked
from polymarket_alpha_lab.research_crypto_launch_service import fetch_crypto_research_preview


def inspect_team(team: str, *, attempts: int, preview: bool) -> dict:
    search = discover_crypto_markets(team, allow_public_fetch=True, max_attempts=attempts)
    report = search.to_dict()
    report.update(preview_invocations=0, public_gets_upper_bound=report['request_attempts'])
    if preview and search.candidates():
        item = search.candidates()[0]
        spec = CryptoResearchSpec('discovery-preview-' + uuid.uuid4().hex, team, item.condition_id,
            item.market_slug, datetime.now(UTC) + timedelta(minutes=30), 'operator-model-not-selected')
        report.update(preview_invocations=1, public_gets_upper_bound=report['request_attempts']+3)
        try:
            result = fetch_crypto_research_preview(spec, allow_public_fetch=True).to_dict()
            report.update(status='prepared', preview=result)
        except CryptoLaunchBlocked as error:
            report.update(status='preview_blocked', preview_reason_code=str(error))
        except Exception:
            report.update(status='preview_failed', preview_reason_code='crypto_preview_failed')
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--team', action='append', choices=tuple(TEAMS), required=True)
    parser.add_argument('--attempts', type=int, choices=(1, 2, 3), default=1,
                        help='explicit maximum discovery GET attempts per team; default no retry')
    parser.add_argument('--preview', action='store_true', help='up to 3 additional single-attempt public GETs per team')
    parser.add_argument('--allow-public-fetch', action='store_true')
    args = parser.parse_args(argv)
    teams = tuple(dict.fromkeys(args.team))
    ceiling = len(teams) * (args.attempts + (3 if args.preview else 0))
    if not args.allow_public_fetch:
        print(json.dumps(dict(status='disabled', public_gets_upper_bound=0,
                              model_called=False, database_written=False)))
        return 0
    results = [inspect_team(t, attempts=args.attempts, preview=args.preview) for t in teams]
    print(json.dumps(dict(results=results, configured_public_gets_ceiling=ceiling,
        discovery_request_attempts=sum(x['request_attempts'] for x in results),
        public_gets_upper_bound=sum(x['public_gets_upper_bound'] for x in results),
        model_called=False, database_written=False, paper_only=True, report_only=True, readonly=True),
        ensure_ascii=True, allow_nan=False, indent=2))
    accepted = ('prepared',) if args.preview else ('candidates', 'no_candidates')
    return 0 if all(r['status'] in accepted for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
