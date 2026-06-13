"""Command-line interface for read-only market scans."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Callable

from polymarket_alpha_lab.api import PolymarketPublicClient
from polymarket_alpha_lab.pipeline import MarketScanConfig, run_market_scan


Runner = Callable[..., object]
ClientFactory = Callable[[], Any]


def main(
    argv: list[str] | None = None,
    *,
    runner: Runner = run_market_scan,
    client_factory: ClientFactory = PolymarketPublicClient,
) -> int:
    parser = argparse.ArgumentParser(prog="polymarket-alpha-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan")
    scan.add_argument("--limit", type=int, default=25)
    scan.add_argument("--archive-root", type=Path, default=Path("data/raw"))
    scan.add_argument("--output", type=Path, default=Path("artifacts/market-scores.json"))
    scan.add_argument("--no-books", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "scan":
        try:
            runner(
                client=client_factory(),
                config=MarketScanConfig(
                    limit=args.limit,
                    archive_root=args.archive_root,
                    output_path=args.output,
                    fetch_books=not args.no_books,
                ),
            )
            return 0
        except Exception as exc:
            print(f"scan failed: {exc}", file=sys.stderr)
            return 1

    return 2
