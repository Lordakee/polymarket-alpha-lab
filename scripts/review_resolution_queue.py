"""List, collect, or explicitly confirm private resolution work.

The default is metadata-only DB readback. --collect --allow-public-fetch opts
into Gamma reads and unconfirmed evidence storage, never final outcomes/models.
The separate --confirm --allow-resolution-write mode consumes reviewed stdin
and may atomically store an operator-confirmed outcome; it never fetches/models.
Requires an already initialized native project database; does not initialize it.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# The data-root option must not select a different version of Python code.
ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'src/polymarket_alpha_lab/__init__.py').is_file():
    raise SystemExit('project_entry_source_missing')
sys.path.insert(0, str(ROOT / 'src'))

from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_resolution_queue import MAX_WORKLIST_MARKETS
from polymarket_alpha_lab.research_resolution_confirmation_cli import _emit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--confirm', action='store_true',
        help='Read one reviewed settlement JSON from stdin; requires --allow-resolution-write')
    parser.add_argument('--allow-resolution-write', action='store_true')
    parser.add_argument('--collect', action='store_true')
    parser.add_argument('--allow-public-fetch', action='store_true')
    parser.add_argument('--max-requests', type=int, default=10)
    parser.add_argument('--max-markets', type=int, default=MAX_WORKLIST_MARKETS)
    parser.add_argument('--recheck-after-seconds', type=int, default=300)
    args = parser.parse_args(argv)
    if args.confirm:
        if args.collect or args.allow_public_fetch or not args.allow_resolution_write:
            parser.error('--confirm requires --allow-resolution-write and forbids collection')
        from polymarket_alpha_lab.research_resolution_confirmation_cli import confirm_from_stdin
        return confirm_from_stdin(root=args.root, allow_resolution_write=True)
    if args.allow_resolution_write:
        parser.error('--allow-resolution-write requires --confirm')
    if args.collect != args.allow_public_fetch:
        parser.error('--collect and --allow-public-fetch must be provided together')
    if not 1 <= args.max_requests <= 20 or not 1 <= args.max_markets <= MAX_WORKLIST_MARKETS:
        parser.error('max-requests must be 1..20 and max-markets must be 1..1000')
    if not 60 <= args.recheck_after_seconds <= 86400:
        parser.error('recheck-after-seconds must be 60..86400')
    # Once entering the managed path, a collection may already have fetched or
    # committed evidence even when the receipt/cleanup fails. Never retry here.
    failure = dict(live_model_called=False, confirmed_outcomes_created=0,
        operation_entered=True, public_network_calls_possible=args.collect,
        business_writes_possible=args.collect, automatic_retry_permitted=False,
        paper_only=True, report_only=True, readonly=True)
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
    except KeyboardInterrupt:
        return _emit(dict(failure, status='interrupted', reason_code='resolution_queue_interrupted'), 130)
    except (Exception, SystemExit):
        return _emit(dict(failure, status='failed', reason_code='resolution_queue_operation_failed'), 1)
    return _emit(result, code)


if __name__ == '__main__':
    raise SystemExit(main())
