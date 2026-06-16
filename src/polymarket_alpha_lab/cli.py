"""Command-line interface for read-only market scans and strategy cycles."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from polymarket_alpha_lab.api import PolymarketPublicClient
from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventStrategyConfig,
)
from polymarket_alpha_lab.cost_aware_snapshot_builder import (
    PaperCostAwareSnapshotConfig,
)
from polymarket_alpha_lab.forecast_provider import PaperForecastConfig
from polymarket_alpha_lab.journal import PaperTradeJournal
from polymarket_alpha_lab.paper_execution import PaperExecutionConfig
from polymarket_alpha_lab.paper_portfolio_nav import mark_paper_portfolio_nav
from polymarket_alpha_lab.pipeline import MarketScanConfig, run_market_scan
from polymarket_alpha_lab.positions import PaperNavLog, PaperNavSnapshot
from polymarket_alpha_lab.performance_summary import (
    PerformanceSummary,
    PerformanceSummaryConfig,
    build_performance_summary,
)
from polymarket_alpha_lab.project_screening import PaperProjectScreeningConfig
from polymarket_alpha_lab.strategy_cycle import (
    PaperStrategyCycleConfig,
    PaperStrategyCycleLog,
    PaperStrategyCycleReport,
    run_strategy_cycle,
)


Runner = Callable[..., object]
CycleRunner = Callable[..., PaperStrategyCycleReport]
ClientFactory = Callable[[], Any]
NavRunner = Callable[..., PaperNavSnapshot]
HistoryRunner = Callable[..., PerformanceSummary]


def main(
    argv: list[str] | None = None,
    *,
    runner: Runner = run_market_scan,
    cycle_runner: CycleRunner = run_strategy_cycle,
    nav_runner: NavRunner = mark_paper_portfolio_nav,
    client_factory: ClientFactory = PolymarketPublicClient,
    history_runner: HistoryRunner | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="polymarket-alpha-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan")
    scan.add_argument("--limit", type=int, default=25)
    scan.add_argument("--archive-root", type=Path, default=Path("data/raw"))
    scan.add_argument("--output", type=Path, default=Path("artifacts/market-scores.json"))
    scan.add_argument("--no-books", action="store_true")

    cycle = subparsers.add_parser("strategy-cycle")
    cycle.add_argument("--limit", type=int, default=25)
    cycle.add_argument("--archive-root", type=Path, default=Path("data/raw"))
    cycle.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/strategy-cycle.jsonl"),
    )
    cycle.add_argument("--max-markets", type=int, default=50)
    cycle.add_argument(
        "--prefilter",
        action=argparse.BooleanOptionalAction,
        default=True,
        dest="prefilter",
    )
    # Stage 4 (default-off): --paper-execute turns on the inline paper-execution
    # pass inside run_strategy_cycle; --paper-journal selects the JSONL sink.
    cycle.add_argument(
        "--paper-execute",
        action="store_true",
        dest="paper_execute",
    )
    cycle.add_argument(
        "--paper-journal",
        type=Path,
        default=Path("artifacts/paper-trades.jsonl"),
        dest="paper_journal",
    )

    nav = subparsers.add_parser("portfolio-nav")
    nav.add_argument(
        "--journal",
        type=Path,
        default=Path("artifacts/paper-trades.jsonl"),
        dest="journal",
    )
    nav.add_argument(
        "--starting-cash",
        type=Decimal,
        required=True,
        dest="starting_cash",
    )
    nav.add_argument(
        "--nav-log",
        type=Path,
        default=None,
        dest="nav_log",
    )

    history = subparsers.add_parser("history")
    history.add_argument(
        "--cycle-log",
        type=Path,
        required=True,
        dest="cycle_log",
    )
    history.add_argument(
        "--trade-log",
        type=Path,
        required=True,
        dest="trade_log",
    )
    history.add_argument(
        "--nav-log",
        type=Path,
        required=True,
        dest="nav_log",
    )

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

    if args.command == "strategy-cycle":
        try:
            scan_config = MarketScanConfig(
                limit=args.limit,
                archive_root=args.archive_root,
                output_path=args.output,
                fetch_books=True,
            )
            cycle_config = _build_default_cycle_config(
                max_markets_per_cycle=args.max_markets,
                prefilter_by_score=args.prefilter,
                paper_execute=args.paper_execute,
                paper_journal=args.paper_journal,
            )
            report = cycle_runner(
                client=client_factory(),
                scan_config=scan_config,
                cycle_config=cycle_config,
            )
            PaperStrategyCycleLog(args.output).append(report)
            _print_strategy_cycle_summary(report)
            return 0
        except Exception as exc:
            print(f"strategy-cycle failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "portfolio-nav":
        try:
            snapshot = nav_runner(
                journal_path=args.journal,
                starting_cash=args.starting_cash,
                client=client_factory(),
                marked_at=datetime.now(UTC),
                nav_log_path=args.nav_log,
            )
            _print_portfolio_nav_summary(snapshot)
            return 0
        except Exception as exc:
            print(f"portfolio-nav failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "history":
        try:
            summary = _run_history(
                cycle_log=args.cycle_log,
                trade_log=args.trade_log,
                nav_log=args.nav_log,
                runner=history_runner,
            )
            _print_performance_summary(summary)
            return 0
        except Exception as exc:
            print(f"history failed: {exc}", file=sys.stderr)
            return 1

    return 2


def _build_default_cycle_config(
    *,
    max_markets_per_cycle: int,
    prefilter_by_score: bool,
    paper_execute: bool = False,
    paper_journal: Path | None = None,
) -> PaperStrategyCycleConfig:
    """Assemble the frozen paper-only cycle config used by the strategy-cycle CLI.

    All nested configs use the same canonical ``config_version`` and rely on
    their dataclass defaults except ``cost_assumptions`` (no defaults), which
    is given zero-cost Decimal assumptions for the research/paper baseline.
    When ``paper_execute`` is set, the Stage 4 inline paper-execution pass is
    enabled with the canonical ``PaperExecutionConfig`` and the journal sink.
    """

    base = PaperStrategyCycleConfig(
        config_version="strategy-cycle-v1",
        forecast_config=PaperForecastConfig(config_version="strategy-cycle-v1"),
        snapshot_config=PaperCostAwareSnapshotConfig(
            config_version="strategy-cycle-v1",
        ),
        strategy_config=PaperCostAwareEventStrategyConfig(
            config_version="strategy-cycle-v1",
        ),
        screening_config=PaperProjectScreeningConfig(
            config_version="strategy-cycle-v1",
        ),
        cost_assumptions=PaperCostAwareEventCostAssumptions(
            taker_fee_rate=Decimal("0"),
            slippage_cost_per_share=Decimal("0"),
            funding_cost_per_share=Decimal("0"),
            finalization_cost_per_share=Decimal("0"),
            time_cost_per_share=Decimal("0"),
            risk_cost_per_share=Decimal("0"),
        ),
        max_markets_per_cycle=max_markets_per_cycle,
        prefilter_by_score=prefilter_by_score,
    )
    if not paper_execute:
        return base
    journal_path = paper_journal if paper_journal is not None else Path(
        "artifacts/paper-trades.jsonl",
    )
    return replace(
        base,
        paper_execution_config=PaperExecutionConfig(
            config_version="paper-execution-v1",
        ),
        paper_trade_journal_path=journal_path,
    )


def _print_strategy_cycle_summary(report: PaperStrategyCycleReport) -> None:
    """Print a human-readable summary of one strategy-cycle run to stdout.

    Handles a ``screening_report`` of ``None`` (naive forecast defers/blocks
    every market) and a screening queue with few/no ``research_ready`` items.
    """

    print(
        "strategy-cycle: "
        f"scanned={report.scan_market_count} "
        f"considered={report.considered_count} "
        f"snapshot_ready={report.snapshot_ready_count} "
        f"cost_aware_reports={report.cost_aware_report_count}",
    )
    if report.blocked_counts:
        blocked_text = ", ".join(
            f"{status}={count}" for status, count in report.blocked_counts
        )
        print(f"blocked: {blocked_text}")
    screening = report.screening_report
    if screening is None:
        return
    print(
        "screening: "
        f"ready={screening.ready_count} "
        f"watch={screening.watch_count} "
        f"defer={screening.defer_count} "
        f"blocked={screening.blocked_count}",
    )
    for item in screening.queue_items[:5]:
        print(
            f"  #{item.queue_position} [{item.research_bucket}] "
            f"{item.market_slug} score={item.screening_score}",
        )


def _print_portfolio_nav_summary(snapshot: PaperNavSnapshot) -> None:
    """Print a human-readable NAV summary (starting cash, balances, P&L)."""

    print(
        "portfolio-nav: "
        f"starting_cash={snapshot.starting_cash} "
        f"cash_balance={snapshot.cash_balance} "
        f"realized_pnl={snapshot.realized_pnl} "
        f"exit_nav={snapshot.exit_nav} "
        f"unrealized_pnl={snapshot.unrealized_exit_pnl} "
        f"position_count={len(snapshot.marks)}",
    )


def _run_history(
    *,
    cycle_log: Path,
    trade_log: Path,
    nav_log: Path,
    runner: HistoryRunner | None,
) -> PerformanceSummary:
    """Read the three JSONL history logs and build a performance summary.

    When ``runner`` is supplied (for tests), it is called with the three paths
    and returns the summary directly -- no file reads. Otherwise the default
    reads each JSONL log via its typed reader and aggregates via
    ``build_performance_summary``. ``generated_at`` is stamped now.
    """
    generated_at = datetime.now(UTC)
    config = PerformanceSummaryConfig(config_version="performance-summary-v1")
    if runner is not None:
        return runner(
            cycle_log=cycle_log,
            trade_log=trade_log,
            nav_log=nav_log,
            config=config,
            generated_at=generated_at,
        )
    cycle_reports = PaperStrategyCycleLog.read(cycle_log)
    trade_records = PaperTradeJournal.read(trade_log)
    nav_snapshots = PaperNavLog.read(nav_log)
    return build_performance_summary(
        cycle_reports,
        trade_records,
        nav_snapshots,
        config=config,
        generated_at=generated_at,
    )


def _print_performance_summary(summary: PerformanceSummary) -> None:
    """Print a human-readable performance summary to stdout."""

    print(
        "history: "
        f"cycles={summary.cycle_count} "
        f"markets_scanned={summary.total_scan_market_count} "
        f"candidates_ready={summary.total_snapshot_ready_count} "
        f"cost_aware_reports={summary.total_cost_aware_report_count} "
        f"paper_trades={summary.paper_trade_count} "
        f"nav_snapshots={summary.nav_snapshot_count}",
    )
    if summary.last_exit_nav is not None:
        print(f"  last_exit_nav={summary.last_exit_nav}")
    if summary.last_starting_cash is not None:
        print(f"  last_starting_cash={summary.last_starting_cash}")
    if summary.total_realized_pnl is not None:
        print(f"  total_realized_pnl={summary.total_realized_pnl}")
    if summary.first_cycle_at is not None and summary.last_cycle_at is not None:
        print(
            f"  cycle_span={summary.first_cycle_at.isoformat()} "
            f"to {summary.last_cycle_at.isoformat()}",
        )
