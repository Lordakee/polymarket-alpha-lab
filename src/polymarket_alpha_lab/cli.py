"""Command-line interface for read-only market scans and strategy cycles."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from polymarket_alpha_lab.api import PolymarketPublicClient
from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventStrategyConfig,
    polymarket_default_cost_assumptions,
)
from polymarket_alpha_lab.cost_aware_snapshot_builder import (
    PaperCostAwareSnapshotConfig,
)
from polymarket_alpha_lab.forecast_provider import PaperForecastConfig
from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceLog
from polymarket_alpha_lab.llm_forecast import PaperLLMForecastConfig
from polymarket_alpha_lab.llm_research_transport import GLMChatTransport
from polymarket_alpha_lab.journal import PaperTradeJournal
from polymarket_alpha_lab.local_observability_trends import (
    LocalObservabilityTrendsConfig,
    LocalObservabilityTrendsReport,
    run_local_observability_trends,
)
from polymarket_alpha_lab.outcome_tracker import (
    OutcomeTrackingConfig,
    OutcomeTrackingLog,
    OutcomeTrackingReport,
    check_outcomes,
)
from polymarket_alpha_lab.paper_execution import PaperExecutionConfig
from polymarket_alpha_lab.paper_portfolio_nav import mark_paper_portfolio_nav
from polymarket_alpha_lab.paper_trade_cost_audit import (
    PaperTradeCostAuditConfig,
    PaperTradeCostAuditReport,
    build_paper_trade_cost_audit_report,
)
from polymarket_alpha_lab.pipeline import MarketScanConfig, run_market_scan
from polymarket_alpha_lab.positions import PaperNavLog, PaperNavSnapshot
from polymarket_alpha_lab.performance_summary import (
    PerformanceSummary,
    PerformanceSummaryConfig,
    build_performance_summary,
)
from polymarket_alpha_lab.project_screening import PaperProjectScreeningConfig
from polymarket_alpha_lab.runner import RunLoopSummary, run_strategy_loop
from polymarket_alpha_lab.strategy_cycle import (
    PaperStrategyCycleConfig,
    PaperStrategyCycleLog,
    PaperStrategyCycleReport,
    run_strategy_cycle,
)
from polymarket_alpha_lab.strategy_audit_history import (
    PaperStrategyRiskAuditHistoryConfig,
    PaperStrategyRiskAuditHistoryReport,
    build_paper_strategy_risk_audit_history_report,
)
from polymarket_alpha_lab.strategy_recommendation_history import (
    PaperStrategyRecommendationHistoryReport,
    build_paper_strategy_recommendation_history_report,
)
from polymarket_alpha_lab.strategy_recommendation_log import (
    read_paper_strategy_recommendation_bundle_log,
)
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditConfig,
    PaperStrategyRiskAuditReport,
    build_paper_strategy_risk_audit_report,
)
from polymarket_alpha_lab.strategy_risk_audit_log import PaperStrategyRiskAuditLog

if TYPE_CHECKING:
    from polymarket_alpha_lab.nav_risk_metrics import PaperNavRiskMetricsReport
    from polymarket_alpha_lab.strategy_evidence import (
        PaperStrategyEvidenceSnapshotReport,
    )


Runner = Callable[..., object]
CycleRunner = Callable[..., PaperStrategyCycleReport]
ClientFactory = Callable[[], Any]
NavRunner = Callable[..., PaperNavSnapshot]
HistoryRunner = Callable[..., PerformanceSummary]
LoopRunner = Callable[..., RunLoopSummary]
OutcomeRunner = Callable[..., OutcomeTrackingReport]
NavRiskRunner = Callable[..., "PaperNavRiskMetricsReport"]
StrategyAuditRunner = Callable[..., PaperStrategyRiskAuditReport]
StrategyAuditHistoryRunner = Callable[..., PaperStrategyRiskAuditHistoryReport]
StrategyRecommendationHistoryRunner = Callable[
    ...,
    PaperStrategyRecommendationHistoryReport,
]
CostAuditRunner = Callable[..., PaperTradeCostAuditReport]
StrategyEvidenceRunner = Callable[..., "PaperStrategyEvidenceSnapshotReport"]
ObservabilityTrendsRunner = Callable[..., LocalObservabilityTrendsReport]
_MISSING = object()


def _apply_json_config(args: argparse.Namespace) -> None:
    """Override argparse defaults from a JSON config file (--config flag).

    Reads the JSON file referenced by ``args.config`` and sets any missing
    attributes on ``args`` from the config. Explicit CLI flags always win
    over config values (CLI is checked first via ``hasattr`` + sentinel).
    """
    if not getattr(args, "config", None):
        return
    import json
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    key_map = {
        "forecast_provider": "forecast_provider",
        "llm_api_token": "llm_api_token",
        "max_markets_per_cycle": "max_markets",
        "scan_limit": "limit",
        "prefilter_by_score": "prefilter",
        "paper_execute": "paper_execute",
        "paper_journal": "paper_journal",
        "nav_log": "nav_log",
        "cycle_log": "cycle_log",
        "outcome_log": "outcome_log",
        "archive_root": "archive_root",
        "repeat_interval_seconds": "repeat_interval",
        "max_iterations": "max_iterations",
        "starting_cash": "starting_cash",
        "market_search": "market_search",
        "strategy_audit_preflight": "strategy_audit_preflight",
        "strategy_audit_log": "strategy_audit_log",
    }
    for json_key, arg_key in key_map.items():
        if json_key not in cfg:
            continue
        val = cfg[json_key]
        current = getattr(args, arg_key, None)
        if current is not None and arg_key != "prefilter":
            continue
        if arg_key == "starting_cash" and val is not None:
            val = Decimal(str(val))
        if arg_key in (
            "paper_journal",
            "nav_log",
            "cycle_log",
            "outcome_log",
            "strategy_audit_log",
            "archive_root",
        ) and val is not None:
            val = Path(val)
        setattr(args, arg_key, val)


def main(
    argv: list[str] | None = None,
    *,
    runner: Runner = run_market_scan,
    cycle_runner: CycleRunner = run_strategy_cycle,
    nav_runner: NavRunner = mark_paper_portfolio_nav,
    client_factory: ClientFactory = PolymarketPublicClient,
    history_runner: HistoryRunner | None = None,
    nav_risk_runner: NavRiskRunner | None = None,
    loop_runner: LoopRunner = run_strategy_loop,
    outcome_runner: OutcomeRunner = check_outcomes,
    strategy_audit_runner: StrategyAuditRunner | None = None,
    strategy_audit_history_runner: StrategyAuditHistoryRunner | None = None,
    strategy_recommendation_history_runner: (
        StrategyRecommendationHistoryRunner | None
    ) = None,
    cost_audit_runner: CostAuditRunner | None = None,
    strategy_evidence_runner: StrategyEvidenceRunner | None = None,
    observability_trends_runner: ObservabilityTrendsRunner = (
        run_local_observability_trends
    ),
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
    cycle.add_argument("--search", default=None, dest="market_search")
    cycle.add_argument(
        "--prefilter",
        action=argparse.BooleanOptionalAction,
        default=True,
        dest="prefilter",
    )
    # Stage 8: --forecast-provider selects the per-market forecast model.
    # --llm-api-token is caller-supplied (never read from env/disk); it is
    # threaded into a GLMChatTransport only when the provider is "llm".
    cycle.add_argument(
        "--forecast-provider",
        choices=("naive", "book_imbalance", "llm"),
        default="naive",
        dest="forecast_provider",
    )
    cycle.add_argument(
        "--llm-api-token",
        default=None,
        dest="llm_api_token",
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
        default=None,
        dest="starting_cash",
    )
    nav.add_argument(
        "--nav-log",
        type=Path,
        default=None,
        dest="nav_log",
    )

    nav_risk = subparsers.add_parser("nav-risk")
    nav_risk.add_argument(
        "--nav-log",
        type=Path,
        required=True,
        dest="nav_log",
    )

    cost_audit = subparsers.add_parser("cost-audit")
    cost_audit.add_argument(
        "--trade-log",
        type=Path,
        required=True,
        dest="trade_log",
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

    strategy_audit = subparsers.add_parser("strategy-audit")
    strategy_audit.add_argument(
        "--cycle-log",
        type=Path,
        required=True,
        dest="cycle_log",
    )
    strategy_audit.add_argument(
        "--trade-log",
        type=Path,
        required=True,
        dest="trade_log",
    )
    strategy_audit.add_argument(
        "--nav-log",
        type=Path,
        required=True,
        dest="nav_log",
    )
    strategy_audit.add_argument(
        "--outcome-log",
        type=Path,
        default=None,
        dest="outcome_log",
    )
    strategy_audit.add_argument(
        "--strategy-audit-log",
        type=Path,
        default=None,
        dest="strategy_audit_log",
    )

    strategy_audit_history = subparsers.add_parser("strategy-audit-history")
    strategy_audit_history.add_argument(
        "--strategy-audit-log",
        type=Path,
        required=True,
        dest="strategy_audit_log",
    )

    strategy_recommendation_history = subparsers.add_parser(
        "strategy-recommendation-history",
    )
    strategy_recommendation_history.add_argument(
        "--recommendation-log",
        type=Path,
        required=True,
        dest="recommendation_log",
    )

    strategy_evidence = subparsers.add_parser("strategy-evidence")
    strategy_evidence.add_argument(
        "--cycle-log",
        type=Path,
        required=True,
        dest="cycle_log",
    )
    strategy_evidence.add_argument(
        "--trade-log",
        type=Path,
        required=True,
        dest="trade_log",
    )
    strategy_evidence.add_argument(
        "--nav-log",
        type=Path,
        required=True,
        dest="nav_log",
    )
    strategy_evidence.add_argument(
        "--outcome-log",
        type=Path,
        default=None,
        dest="outcome_log",
    )
    strategy_evidence.add_argument(
        "--strategy-audit-log",
        type=Path,
        default=None,
        dest="strategy_audit_log",
    )

    observability_trends = subparsers.add_parser("observability-trends")
    observability_trends.add_argument(
        "--cycle-log",
        type=Path,
        required=True,
        dest="cycle_log",
    )
    observability_trends.add_argument(
        "--trade-log",
        type=Path,
        required=True,
        dest="trade_log",
    )
    observability_trends.add_argument(
        "--nav-log",
        type=Path,
        required=True,
        dest="nav_log",
    )
    observability_trends.add_argument(
        "--outcome-log",
        type=Path,
        default=None,
        dest="outcome_log",
    )
    observability_trends.add_argument(
        "--strategy-audit-log",
        type=Path,
        default=None,
        dest="strategy_audit_log",
    )
    observability_trends.add_argument(
        "--outcome-stale-after-seconds",
        type=int,
        default=86_400,
        dest="outcome_stale_after_seconds",
    )

    # Stage 17 market search: search Polymarket markets by keyword.
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument(
        "--query", required=True, dest="query",
    )
    search_parser.add_argument("--limit", type=int, default=25)
    search_parser.add_argument("--closed", action="store_true")

    # Stage 9 outcome tracker: re-list closed markets from Gamma and build a
    # forecast-evidence calibration report over resolved paper-trade legs.
    check_outcomes_parser = subparsers.add_parser("check-outcomes")
    check_outcomes_parser.add_argument(
        "--journal",
        type=Path,
        default=Path("artifacts/paper-trades.jsonl"),
        dest="journal",
    )
    check_outcomes_parser.add_argument(
        "--evidence-log",
        type=Path,
        default=None,
        dest="evidence_log",
    )
    check_outcomes_parser.add_argument(
        "--outcome-log",
        type=Path,
        default=None,
        dest="outcome_log",
    )

    # Stage 7 continuous run: chains strategy-cycle + paper-execute + portfolio-nav.
    run_loop = subparsers.add_parser("run")
    run_loop.add_argument("--limit", type=int, default=25)
    run_loop.add_argument("--archive-root", type=Path, default=Path("data/raw"))
    run_loop.add_argument("--max-markets", type=int, default=50)
    run_loop.add_argument(
        "--prefilter",
        action=argparse.BooleanOptionalAction,
        default=True,
        dest="prefilter",
    )
    run_loop.add_argument(
        "--forecast-provider",
        choices=("naive", "book_imbalance", "llm"),
        default="naive",
        dest="forecast_provider",
    )
    run_loop.add_argument(
        "--llm-api-token",
        default=None,
        dest="llm_api_token",
    )
    run_loop.add_argument(
        "--paper-execute",
        action="store_true",
        dest="paper_execute",
    )
    run_loop.add_argument(
        "--paper-journal",
        type=Path,
        default=Path("artifacts/paper-trades.jsonl"),
        dest="paper_journal",
    )
    run_loop.add_argument(
        "--starting-cash",
        type=Decimal,
        default=None,
        dest="starting_cash",
    )
    run_loop.add_argument(
        "--cycle-log",
        type=Path,
        default=Path("artifacts/strategy-cycle.jsonl"),
        dest="cycle_log",
    )
    run_loop.add_argument(
        "--nav-log",
        type=Path,
        default=None,
        dest="nav_log",
    )
    run_loop.add_argument(
        "--outcome-log",
        type=Path,
        default=None,
        dest="outcome_log",
    )
    run_loop.add_argument(
        "--strategy-audit-preflight",
        action=argparse.BooleanOptionalAction,
        default=None,
        dest="strategy_audit_preflight",
    )
    run_loop.add_argument(
        "--strategy-audit-log",
        type=Path,
        default=None,
        dest="strategy_audit_log",
    )
    run_loop.add_argument(
        "--repeat-interval",
        type=int,
        default=0,
        dest="repeat_interval",
    )
    run_loop.add_argument(
        "--max-iterations",
        type=int,
        default=1,
        dest="max_iterations",
    )
    run_loop.add_argument(
        "--config",
        type=Path,
        default=None,
        dest="config",
    )

    args = parser.parse_args(argv)
    _apply_json_config(args)
    if args.command == "run" and args.strategy_audit_preflight is None:
        args.strategy_audit_preflight = False

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
                forecast_provider=args.forecast_provider,
                llm_api_token=args.llm_api_token,
            )
            if args.market_search is not None:
                cycle_config = replace(
                    cycle_config, market_search=args.market_search
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

    if args.command == "nav-risk":
        try:
            report = _run_nav_risk(
                nav_log=args.nav_log,
                runner=nav_risk_runner,
            )
            _print_nav_risk_summary(report)
            return 0
        except Exception as exc:
            print(f"nav-risk failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "cost-audit":
        try:
            report = _run_cost_audit(
                trade_log=args.trade_log,
                runner=cost_audit_runner,
            )
            _print_cost_audit_summary(report)
            return 0
        except Exception as exc:
            print(f"cost-audit failed: {exc}", file=sys.stderr)
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

    if args.command == "strategy-audit":
        try:
            report = _run_strategy_audit(
                cycle_log=args.cycle_log,
                trade_log=args.trade_log,
                nav_log=args.nav_log,
                outcome_log=args.outcome_log,
                runner=strategy_audit_runner,
            )
            if args.strategy_audit_log is not None:
                PaperStrategyRiskAuditLog(args.strategy_audit_log).append(report)
            _print_strategy_audit_summary(report)
            return 0
        except Exception as exc:
            print(f"strategy-audit failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "strategy-audit-history":
        try:
            report = _run_strategy_audit_history(
                strategy_audit_log=args.strategy_audit_log,
                runner=strategy_audit_history_runner,
            )
            _print_strategy_audit_history_summary(report)
            return 0
        except Exception as exc:
            print(f"strategy-audit-history failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "strategy-recommendation-history":
        try:
            (
                report,
                latest_selected_count,
                latest_selected_notional,
                selection_score_metrics,
            ) = _run_strategy_recommendation_history(
                recommendation_log=args.recommendation_log,
                runner=strategy_recommendation_history_runner,
            )
            _print_strategy_recommendation_history_summary(
                report,
                latest_selected_count=latest_selected_count,
                latest_selected_notional=latest_selected_notional,
                selection_score_metrics=selection_score_metrics,
            )
            return 0
        except Exception as exc:
            print(f"strategy-recommendation-history failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "strategy-evidence":
        try:
            report = _run_strategy_evidence(
                cycle_log=args.cycle_log,
                trade_log=args.trade_log,
                nav_log=args.nav_log,
                outcome_log=args.outcome_log,
                strategy_audit_log=args.strategy_audit_log,
                runner=strategy_evidence_runner,
            )
            _print_strategy_evidence_summary(report)
            return 0
        except Exception as exc:
            print(f"strategy-evidence failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "observability-trends":
        try:
            report = observability_trends_runner(
                cycle_log=args.cycle_log,
                trade_log=args.trade_log,
                nav_log=args.nav_log,
                outcome_log=args.outcome_log,
                strategy_audit_log=args.strategy_audit_log,
                config=LocalObservabilityTrendsConfig(
                    config_version="local-observability-trends-v0",
                    outcome_stale_after_seconds=args.outcome_stale_after_seconds,
                ),
                generated_at=datetime.now(UTC),
            )
            _print_observability_trends_summary(report)
            return 0
        except Exception as exc:
            print(f"observability-trends failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "run":
        try:
            scan_config = MarketScanConfig(
                limit=args.limit,
                archive_root=args.archive_root,
                output_path=args.cycle_log,
                fetch_books=True,
            )
            cycle_config = _build_default_cycle_config(
                max_markets_per_cycle=args.max_markets,
                prefilter_by_score=args.prefilter,
                paper_execute=args.paper_execute,
                paper_journal=args.paper_journal,
                forecast_provider=args.forecast_provider,
                llm_api_token=args.llm_api_token,
            )
            repeat_mode = "interval" if args.repeat_interval > 0 else "once"
            if args.strategy_audit_preflight:
                if args.nav_log is None:
                    raise ValueError("strategy audit preflight requires --nav-log")
                audit_report = _run_strategy_audit(
                    cycle_log=args.cycle_log,
                    trade_log=args.paper_journal,
                    nav_log=args.nav_log,
                    outcome_log=args.outcome_log,
                    runner=strategy_audit_runner,
                )
                if args.strategy_audit_log is not None:
                    PaperStrategyRiskAuditLog(args.strategy_audit_log).append(
                        audit_report,
                    )
                _print_strategy_audit_summary(audit_report)
                if audit_report.status != "audit_ready":
                    print(
                        "run blocked by strategy audit preflight: "
                        f"status={audit_report.status}",
                        file=sys.stderr,
                    )
                    return 1
            summary = loop_runner(
                client=client_factory(),
                scan_config=scan_config,
                cycle_config=cycle_config,
                starting_cash=args.starting_cash,
                nav_log_path=args.nav_log,
                cycle_report_log_path=args.cycle_log,
                repeat_mode=repeat_mode,
                interval_seconds=args.repeat_interval,
                max_iterations=args.max_iterations,
            )
            _print_run_loop_summary(summary)
            return 0
        except Exception as exc:
            print(f"run failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "search":
        try:
            client = client_factory()
            payload = client.list_markets(
                active=not args.closed,
                closed=args.closed,
                limit=args.limit,
                search=args.query,
            )
            if isinstance(payload, list):
                for m in payload:
                    slug = m.get("slug", "?") if isinstance(m, dict) else "?"
                    q = m.get("question", "?") if isinstance(m, dict) else "?"
                    outs = m.get("outcomes", []) if isinstance(m, dict) else []
                    print(f"{slug}: {q} [{', '.join(str(o) for o in outs)}]")
                print(f"\n{len(payload) if isinstance(payload, list) else 0} markets found")
            else:
                print("unexpected response format")
            return 0
        except Exception as exc:
            print(f"search failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "check-outcomes":
        try:
            report = outcome_runner(
                client=client_factory(),
                journal_path=args.journal,
                config=OutcomeTrackingConfig(
                    config_version="outcome-tracker-v1",
                ),
                generated_at=datetime.now(UTC),
            )
            if (
                args.evidence_log is not None
                and report.forecast_evidence_report is not None
            ):
                PaperForecastEvidenceLog(args.evidence_log).append(
                    report.forecast_evidence_report,
                )
            if args.outcome_log is not None:
                OutcomeTrackingLog(args.outcome_log).append(report)
            _print_outcome_tracking_summary(report)
            return 0
        except Exception as exc:
            print(f"check-outcomes failed: {exc}", file=sys.stderr)
            return 1

    return 2


def _build_default_cycle_config(
    *,
    max_markets_per_cycle: int,
    prefilter_by_score: bool,
    paper_execute: bool = False,
    paper_journal: Path | None = None,
    forecast_provider: str = "naive",
    llm_api_token: str | None = None,
) -> PaperStrategyCycleConfig:
    """Assemble the frozen paper-only cycle config used by the strategy-cycle CLI.

    All nested configs use the same canonical ``config_version`` and rely on
    their dataclass defaults except ``cost_assumptions`` (no defaults), which
    is given realistic Polymarket fee assumptions via
    ``polymarket_default_cost_assumptions`` (2% taker fee + small slippage).
    When ``paper_execute`` is set, the Stage 4 inline paper-execution pass is
    enabled with the canonical ``PaperExecutionConfig`` and the journal sink.
    When ``forecast_provider`` is ``llm`` and ``llm_api_token`` is supplied, a
    caller-supplied ``GLMChatTransport`` is wired alongside the canonical
    ``PaperLLMForecastConfig`` (the token is never read from env/disk here).
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
        cost_assumptions=polymarket_default_cost_assumptions(),
        max_markets_per_cycle=max_markets_per_cycle,
        prefilter_by_score=prefilter_by_score,
    )
    if forecast_provider == "llm" and llm_api_token:
        base = replace(
            base,
            forecast_provider="llm",
            llm_transport=GLMChatTransport(api_token=llm_api_token),
            llm_forecast_config=PaperLLMForecastConfig(
                config_version="strategy-cycle-v1",
            ),
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


def _run_nav_risk(
    *,
    nav_log: Path,
    runner: NavRiskRunner | None,
) -> "PaperNavRiskMetricsReport":
    """Read typed NAV snapshots and build the paper-only risk report."""

    from polymarket_alpha_lab.nav_risk_metrics import (
        PaperNavRiskMetricsConfig,
        build_paper_nav_risk_metrics_report,
    )

    nav_snapshots = PaperNavLog.read(nav_log)
    config = PaperNavRiskMetricsConfig(config_version="nav-risk-metrics-v0")
    generated_at = datetime.now(UTC)
    if runner is not None:
        return runner(
            nav_snapshots=nav_snapshots,
            config=config,
            generated_at=generated_at,
        )
    return build_paper_nav_risk_metrics_report(
        nav_snapshots,
        config=config,
        generated_at=generated_at,
    )


def _run_cost_audit(
    *,
    trade_log: Path,
    runner: CostAuditRunner | None,
) -> PaperTradeCostAuditReport:
    """Read typed paper trades and build the paper-only cost audit report."""

    trade_records = PaperTradeJournal.read(trade_log)
    config = PaperTradeCostAuditConfig(config_version="paper-trade-cost-audit-v0")
    generated_at = datetime.now(UTC)
    if runner is not None:
        return runner(
            trade_records=trade_records,
            config=config,
            generated_at=generated_at,
        )
    return build_paper_trade_cost_audit_report(
        trade_records,
        config=config,
        generated_at=generated_at,
    )


def _run_strategy_audit(
    *,
    cycle_log: Path,
    trade_log: Path,
    nav_log: Path,
    outcome_log: Path | None,
    runner: StrategyAuditRunner | None,
) -> PaperStrategyRiskAuditReport:
    """Read local paper logs and build a strategy risk audit report."""

    generated_at = datetime.now(UTC)
    config = PaperStrategyRiskAuditConfig(config_version="strategy-risk-audit-v0")
    trade_records = PaperTradeJournal.read(trade_log)
    cost_audit_report = build_paper_trade_cost_audit_report(
        trade_records,
        config=PaperTradeCostAuditConfig(config_version="paper-trade-cost-audit-v0"),
        generated_at=generated_at,
    )
    if runner is not None:
        return runner(
            cycle_log=cycle_log,
            trade_log=trade_log,
            nav_log=nav_log,
            outcome_log=outcome_log,
            cost_audit_report=cost_audit_report,
            config=config,
            generated_at=generated_at,
        )
    performance_summary = _run_history(
        cycle_log=cycle_log,
        trade_log=trade_log,
        nav_log=nav_log,
        runner=None,
    )
    nav_risk_report = _run_nav_risk(nav_log=nav_log, runner=None)
    return build_paper_strategy_risk_audit_report(
        performance_summary=performance_summary,
        nav_risk_report=nav_risk_report,
        outcome_report=_latest_outcome_report(outcome_log),
        cost_audit_report=cost_audit_report,
        config=config,
        generated_at=generated_at,
    )


def _latest_outcome_report(path: Path | None) -> OutcomeTrackingReport | None:
    if path is None:
        return None
    reports = OutcomeTrackingLog.read(path)
    if not reports:
        return None
    return reports[-1]


def _run_strategy_audit_history(
    *,
    strategy_audit_log: Path,
    runner: StrategyAuditHistoryRunner | None,
) -> PaperStrategyRiskAuditHistoryReport:
    reports = PaperStrategyRiskAuditLog.read(strategy_audit_log)
    config = PaperStrategyRiskAuditHistoryConfig(
        config_version="strategy-audit-history-v0",
    )
    generated_at = datetime.now(UTC)
    if runner is not None:
        return runner(
            reports=reports,
            config=config,
            generated_at=generated_at,
        )
    return build_paper_strategy_risk_audit_history_report(
        reports,
        config=config,
        generated_at=generated_at,
    )


def _run_strategy_recommendation_history(
    *,
    recommendation_log: Path,
    runner: StrategyRecommendationHistoryRunner | None,
) -> tuple[PaperStrategyRecommendationHistoryReport, int, Decimal, dict[str, object]]:
    bundles = read_paper_strategy_recommendation_bundle_log(recommendation_log)
    recommendation_reports = tuple(bundle.recommendation_report for bundle in bundles)
    config_version = "strategy-recommendation-history-v0"
    generated_at = datetime.now(UTC)
    if runner is not None:
        report = runner(
            recommendation_reports=recommendation_reports,
            config_version=config_version,
            generated_at=generated_at,
        )
    else:
        report = build_paper_strategy_recommendation_history_report(
            recommendation_reports,
            config_version=config_version,
            generated_at=generated_at,
        )
    latest_bundle = _latest_strategy_recommendation_bundle(bundles)
    latest_selected_count = 0 if latest_bundle is None else latest_bundle.selected_count
    latest_selected_notional = (
        Decimal("0")
        if latest_bundle is None
        else latest_bundle.total_selected_notional
    )
    selection_score_metrics = _strategy_recommendation_history_selection_score_metrics(
        report,
        bundles,
    )
    return (
        report,
        latest_selected_count,
        latest_selected_notional,
        selection_score_metrics,
    )


def _latest_strategy_recommendation_bundle(bundles):
    ordered = _ordered_strategy_recommendation_bundles(bundles)
    if not ordered:
        return None
    return ordered[-1]


def _ordered_strategy_recommendation_bundles(bundles) -> tuple[object, ...]:
    return tuple(
        sorted(
            bundles,
            key=_strategy_recommendation_bundle_order_key,
        ),
    )


def _strategy_recommendation_bundle_order_key(bundle: object) -> tuple[datetime, str]:
    recommendation_report = getattr(bundle, "recommendation_report", None)
    generated_at = getattr(recommendation_report, "generated_at", None)
    if not isinstance(generated_at, datetime):
        generated_at = getattr(bundle, "generated_at", None)
    if not isinstance(generated_at, datetime):
        generated_at = datetime.min.replace(tzinfo=UTC)
    elif generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=UTC)
    else:
        generated_at = generated_at.astimezone(UTC)

    config_version = getattr(recommendation_report, "config_version", None)
    if not isinstance(config_version, str):
        config_version = getattr(bundle, "config_version", "")
    if not isinstance(config_version, str):
        config_version = ""
    return generated_at, config_version


def _strategy_recommendation_history_selection_score_metrics(
    report: PaperStrategyRecommendationHistoryReport,
    bundles: tuple[object, ...],
) -> dict[str, object]:
    metrics: dict[str, object] = {}
    _copy_existing_metrics(
        metrics,
        report,
        (
            "total_selected_count",
            "total_selected",
            "total_selected_notional",
            "latest_selected_count",
            "latest_selected",
            "latest_selected_notional",
            "first_recommendation_score",
            "latest_recommendation_score",
            "latest_selected_score",
        ),
    )
    _copy_matching_selection_score_metrics(metrics, report)

    ordered_bundles = _ordered_strategy_recommendation_bundles(bundles)
    if not ordered_bundles:
        return metrics

    first_bundle = ordered_bundles[0]
    latest_bundle = ordered_bundles[-1]
    _copy_existing_metrics(
        metrics,
        latest_bundle,
        (
            "latest_selected_count",
            "latest_selected",
            "latest_selected_notional",
            "latest_recommendation_score",
            "latest_selected_score",
        ),
    )

    if not _has_any_metric(metrics, ("total_selected", "total_selected_count")):
        total_selected = _sum_bundle_int_metric(ordered_bundles, "selected_count")
        if total_selected is not None:
            metrics["total_selected"] = total_selected
    if "total_selected_notional" not in metrics:
        total_selected_notional = _sum_bundle_decimal_metric(
            ordered_bundles,
            "total_selected_notional",
        )
        if total_selected_notional is not None:
            metrics["total_selected_notional"] = total_selected_notional
    if "first_recommendation_score" not in metrics:
        first_score = _max_recommendation_score(
            getattr(first_bundle, "recommendation_report", None),
        )
        if first_score is not None:
            metrics["first_recommendation_score"] = first_score
    if "latest_recommendation_score" not in metrics:
        latest_score = _max_recommendation_score(
            getattr(latest_bundle, "recommendation_report", None),
        )
        if latest_score is not None:
            metrics["latest_recommendation_score"] = latest_score
    if "latest_selected_score" not in metrics:
        latest_selected_score = _max_selected_score(latest_bundle)
        if latest_selected_score is not None:
            metrics["latest_selected_score"] = latest_selected_score
    _copy_matching_selection_score_metrics(metrics, latest_bundle)
    return metrics


def _copy_existing_metrics(
    metrics: dict[str, object],
    source: object,
    field_names: tuple[str, ...],
) -> None:
    for field_name in field_names:
        value = getattr(source, field_name, _MISSING)
        if value is not _MISSING and field_name not in metrics:
            metrics[field_name] = value


def _copy_matching_selection_score_metrics(
    metrics: dict[str, object],
    source: object,
) -> None:
    for field_name in dir(source):
        if field_name.startswith("_") or field_name in metrics:
            continue
        if not _is_selection_score_metric_name(field_name):
            continue
        try:
            value = getattr(source, field_name)
        except Exception:
            continue
        if _is_printable_metric_value(value):
            metrics[field_name] = value


def _is_selection_score_metric_name(field_name: str) -> bool:
    return (
        "selected" in field_name
        or "selection" in field_name
        or "score" in field_name
    )


def _is_printable_metric_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, Decimal, str))


def _has_any_metric(metrics: dict[str, object], field_names: tuple[str, ...]) -> bool:
    return any(field_name in metrics for field_name in field_names)


def _sum_bundle_int_metric(bundles: tuple[object, ...], field_name: str) -> int | None:
    total = 0
    observed = False
    for bundle in bundles:
        value = getattr(bundle, field_name, None)
        if isinstance(value, bool) or not isinstance(value, int):
            continue
        total += value
        observed = True
    return total if observed else None


def _sum_bundle_decimal_metric(
    bundles: tuple[object, ...],
    field_name: str,
) -> Decimal | None:
    total = Decimal("0")
    observed = False
    for bundle in bundles:
        value = getattr(bundle, field_name, None)
        if not isinstance(value, Decimal):
            continue
        total += value
        observed = True
    return total if observed else None


def _max_recommendation_score(report: object) -> Decimal | None:
    rows = _tuple_or_empty(getattr(report, "recommendation_rows", ()))
    scores = tuple(
        score
        for row in rows
        if isinstance((score := getattr(row, "recommendation_score", None)), Decimal)
    )
    return max(scores) if scores else None


def _max_selected_score(bundle: object) -> Decimal | None:
    selection_report = getattr(bundle, "selection_policy_report", None)
    rows = _tuple_or_empty(getattr(selection_report, "selection_rows", ()))
    scores = tuple(
        score
        for row in rows
        if getattr(row, "decision", None) == "selected"
        and isinstance((score := getattr(row, "recommendation_score", None)), Decimal)
    )
    return max(scores) if scores else None


def _tuple_or_empty(value: object) -> tuple[object, ...]:
    if value is None or isinstance(value, (str, bytes)):
        return ()
    try:
        return tuple(value)
    except TypeError:
        return ()


def _run_strategy_evidence(
    *,
    cycle_log: Path,
    trade_log: Path,
    nav_log: Path,
    outcome_log: Path | None,
    strategy_audit_log: Path | None,
    runner: StrategyEvidenceRunner | None,
) -> "PaperStrategyEvidenceSnapshotReport":
    from polymarket_alpha_lab.strategy_evidence import (
        PaperStrategyEvidenceSnapshotConfig,
        build_paper_strategy_evidence_snapshot_report,
    )

    generated_at = datetime.now(UTC)
    performance_summary = _run_history(
        cycle_log=cycle_log,
        trade_log=trade_log,
        nav_log=nav_log,
        runner=None,
    )
    nav_risk_report = _run_nav_risk(nav_log=nav_log, runner=None)
    cost_audit_report = _run_cost_audit(trade_log=trade_log, runner=None)
    strategy_audit_history_report = (
        None
        if strategy_audit_log is None
        else _run_strategy_audit_history(
            strategy_audit_log=strategy_audit_log,
            runner=None,
        )
    )
    outcome_report = _latest_outcome_report(outcome_log)
    config = PaperStrategyEvidenceSnapshotConfig(
        config_version="strategy-evidence-snapshot-v0",
    )
    if runner is not None:
        return runner(
            performance_summary=performance_summary,
            nav_risk_report=nav_risk_report,
            cost_audit_report=cost_audit_report,
            outcome_report=outcome_report,
            audit_history_report=strategy_audit_history_report,
            config=config,
            generated_at=generated_at,
        )
    return build_paper_strategy_evidence_snapshot_report(
        performance_summary=performance_summary,
        nav_risk_report=nav_risk_report,
        cost_audit_report=cost_audit_report,
        outcome_report=outcome_report,
        audit_history_report=strategy_audit_history_report,
        config=config,
        generated_at=generated_at,
    )


def _print_nav_risk_summary(report: "PaperNavRiskMetricsReport") -> None:
    """Print a compact NAV risk report summary to stdout."""

    print(
        "nav-risk: "
        f"snapshots={report.nav_snapshot_count} "
        f"latest_exit_nav={report.latest_exit_nav} "
        f"max_drawdown={report.max_drawdown} "
        f"max_drawdown_pct={report.max_drawdown_pct}",
    )


def _print_cost_audit_summary(report: PaperTradeCostAuditReport) -> None:
    """Print a compact paper trade cost audit summary."""

    print(
        "cost-audit: "
        f"trades={report.trade_count} "
        f"filled={report.total_filled_size} "
        f"requested={report.total_requested_size} "
        f"fill_rate={report.fill_rate} "
        f"mean_edge_cost_drag={report.mean_edge_cost_drag} "
        f"total_edge_cost_drag={report.total_edge_cost_drag} "
        f"partial_fills={report.partial_fill_count} "
        "negative_cost_adjusted_edge="
        f"{report.negative_cost_adjusted_edge_count}",
    )
    if report.mean_research_slippage is not None:
        print(f"  mean_research_slippage={report.mean_research_slippage}")
    if report.mean_fill_slippage is not None:
        print(f"  mean_fill_slippage={report.mean_fill_slippage}")
    if report.largest_single_trade_cost_drag is not None:
        print(
            "  largest_single_trade_cost_drag="
            f"{report.largest_single_trade_cost_drag}",
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


def _print_strategy_audit_summary(report: PaperStrategyRiskAuditReport) -> None:
    """Print a compact local strategy audit summary."""

    print(
        "strategy-audit: "
        f"status={report.status} "
        f"gates={report.gate_count} "
        f"pass={report.pass_count} "
        f"fail={report.fail_count} "
        f"incomplete={report.incomplete_count}",
    )
    for gate in report.gate_results:
        print(
            f"  {gate.gate_name}: "
            f"status={gate.status} "
            f"observed={gate.observed_value} "
            f"threshold={gate.threshold}",
        )


def _print_strategy_audit_history_summary(
    report: PaperStrategyRiskAuditHistoryReport,
) -> None:
    status_counts = {
        row.audit_status: row.audit_count for row in report.status_rows
    }
    first = _iso_or_none(report.first_audit_generated_at)
    latest = _iso_or_none(report.latest_audit_generated_at)
    latest_status = report.latest_audit_status or "none"
    print(
        "strategy-audit-history: "
        f"reports={report.audit_report_count} "
        f"status={report.status} "
        f"latest_status={latest_status} "
        f"audit_ready={status_counts['audit_ready']} "
        f"insufficient_evidence={status_counts['insufficient_evidence']} "
        f"blocked_by_risk={status_counts['blocked_by_risk']} "
        f"first={first} "
        f"latest={latest} "
        f"consecutive_non_ready={report.consecutive_non_ready_count}",
    )
    print(
        "  latest_failed_gates="
        f"{_csv_or_none(report.latest_failed_gate_names)}",
    )
    print(
        "  latest_incomplete_gates="
        f"{_csv_or_none(report.latest_incomplete_gate_names)}",
    )
    gate_counts = {
        (row.gate_name, row.gate_status): row.audit_count
        for row in report.gate_status_summaries
    }
    for gate_name in (
        "paper_history",
        "settlement_evidence",
        "forecast_quality",
        "cost_discipline",
        "nav_drawdown",
        "open_exposure",
    ):
        print(
            f"  {gate_name}: "
            f"pass={gate_counts[(gate_name, 'pass')]} "
            f"fail={gate_counts[(gate_name, 'fail')]} "
            f"incomplete={gate_counts[(gate_name, 'incomplete')]}",
        )


def _print_strategy_recommendation_history_summary(
    report: PaperStrategyRecommendationHistoryReport,
    *,
    latest_selected_count: int,
    latest_selected_notional: Decimal,
    selection_score_metrics: dict[str, object] | None = None,
) -> None:
    print(
        "strategy-recommendation-history: "
        f"source_reports={report.source_report_count} "
        f"total_candidates={report.total_candidate_count} "
        f"total_recommend={report.total_recommend_count} "
        f"total_watch={report.total_watch_count} "
        f"total_reject={report.total_reject_count} "
        f"latest_candidates={report.latest_candidate_count} "
        f"latest_recommend={report.latest_recommend_count} "
        f"latest_selected={latest_selected_count} "
        f"latest_selected_notional={latest_selected_notional} "
        f"first={_iso_or_none(report.first_generated_at)} "
        f"latest={_iso_or_none(report.latest_generated_at)}",
    )
    _print_selection_score_trend_metrics(selection_score_metrics or {})


def _print_selection_score_trend_metrics(metrics: dict[str, object]) -> None:
    metric_order = (
        "total_selected",
        "total_selected_count",
        "total_selected_notional",
        "latest_selected",
        "latest_selected_count",
        "latest_selected_notional",
        "first_recommendation_score",
        "latest_recommendation_score",
        "latest_selected_score",
    )
    parts = [
        f"{field_name}={metrics[field_name]}"
        for field_name in metric_order
        if field_name in metrics
    ]
    parts.extend(
        f"{field_name}={value}"
        for field_name, value in metrics.items()
        if field_name not in metric_order
    )
    if parts:
        print("  selection_score_trend: " + " ".join(parts))


def _print_strategy_evidence_summary(
    report: "PaperStrategyEvidenceSnapshotReport",
) -> None:
    print(
        "strategy-evidence: "
        f"status={report.status} "
        f"gaps={_csv_or_none(report.evidence_gap_names)} "
        f"cycles={report.cycle_count} "
        f"paper_trades={report.paper_trade_count} "
        f"nav_snapshots={report.nav_snapshot_count} "
        f"outcome_checked={_none_or_value(report.outcome_checked_count)} "
        f"outcome_resolved={_none_or_value(report.outcome_resolved_count)} "
        f"outcome_pending={_none_or_value(report.outcome_pending_count)} "
        f"strategy_audits={_none_or_value(report.audit_report_count)} "
        f"latest_audit_status={_none_or_value(report.latest_audit_status)} "
        "negative_cost_adjusted_edge="
        f"{report.negative_cost_adjusted_edge_count} "
        "unexecutable_open_positions="
        f"{report.unexecutable_open_position_count} "
        f"paper_only={report.paper_only} "
        f"report_only={report.report_only}",
    )


def _print_observability_trends_summary(
    report: LocalObservabilityTrendsReport,
) -> None:
    strategy = report.strategy_evidence_trend
    outcome = report.outcome_freshness
    nav = report.nav_risk_trend
    cost = report.paper_trade_cost_trend
    print(
        "observability-trends: "
        f"strategy_evidence_status={strategy.latest_status} "
        f"strategy_evidence_snapshots={strategy.snapshot_report_count} "
        f"outcome_status={outcome.status} "
        f"outcome_reports={outcome.outcome_report_count} "
        f"nav_risk_status={nav.status} "
        f"nav_risk_reports={nav.nav_risk_report_count} "
        f"cost_status={cost.status} "
        f"cost_audit_reports={cost.cost_audit_report_count} "
        f"paper_only={report.paper_only} "
        f"report_only={report.report_only} "
        f"readonly={report.readonly}",
    )
    print(
        "  strategy_evidence_latest_gaps="
        f"{_csv_or_none(strategy.latest_evidence_gap_names)}",
    )
    print(
        "  outcome_latest_age_seconds="
        f"{_none_or_value(outcome.latest_report_age_seconds)}",
    )
    print(
        "  nav_latest_exit_nav="
        f"{_none_or_value(nav.latest_exit_nav)}",
    )
    print(
        "  cost_latest_mean_edge_cost_drag="
        f"{_none_or_value(cost.latest_mean_edge_cost_drag)}",
    )


def _iso_or_none(value: datetime | None) -> str:
    return "none" if value is None else value.isoformat()


def _csv_or_none(values: tuple[str, ...]) -> str:
    return "none" if not values else ",".join(values)


def _none_or_value(value: object | None) -> str:
    return "none" if value is None else str(value)


def _print_run_loop_summary(summary: RunLoopSummary) -> None:
    print(
        "run: "
        f"completed={summary.iterations_completed} "
        f"failed={summary.iterations_failed} "
        f"nav_skipped={summary.nav_marks_skipped} "
        f"span={summary.first_iteration_at.isoformat()} "
        f"to {summary.last_iteration_at.isoformat()}",
    )
    if summary.last_error is not None:
        print(f"  last_error={summary.last_error}")


def _print_outcome_tracking_summary(report: OutcomeTrackingReport) -> None:
    """Print a human-readable outcome-tracking summary to stdout."""

    print(
        "check-outcomes: "
        f"checked={report.total_markets_checked} "
        f"resolved={report.resolved_count} "
        f"pending={report.pending_count} "
        f"observations={len(report.observations)}",
    )
    evidence = report.forecast_evidence_report
    if evidence is None:
        print("  forecast_evidence: none (no resolved observations yet)")
        return
    print(
        "  forecast_evidence: "
        f"status={evidence.status} "
        f"observation_count={evidence.observation_count} "
        f"unique_markets={evidence.unique_market_count}",
    )
    if evidence.mean_probability_loss is not None:
        print(f"  mean_probability_loss={evidence.mean_probability_loss}")
    if evidence.worst_bucket_error is not None:
        print(f"  worst_bucket_error={evidence.worst_bucket_error}")


if __name__ == "__main__":  # pragma: no cover - thin entry shim
    import sys as _sys

    _sys.exit(main())
