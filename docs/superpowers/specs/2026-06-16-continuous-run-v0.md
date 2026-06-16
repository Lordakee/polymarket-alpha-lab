# Continuous Run v0 Design (Stage 7)

## Purpose

The system can run one-shot (scan → paper trade → NAV → history) but lacks
continuous operation. Stage 7 ships a `run` command that chains
strategy-cycle + paper-execute + portfolio-nav in a loop, manufacturing the
longitudinal data (≥30 obs, ≥50 trades) needed for Level 2 promotion gates
and future forecast calibration.

No live orders/auth/wallets/credentials/exchange writes. Pure composition of
existing paper-only + read-only primitives, repeated.

## Architecture

```text
runner.py (NEW live-layer orchestrator)
  run_strategy_loop(
    *, client, scan_config, cycle_config, starting_cash,
    nav_log_path, cycle_report_log_path,
    repeat_mode: "once" | "interval",
    interval_seconds: int = 3600,
    max_iterations: int | None = None,
    on_cycle_error: "log_and_continue" | "raise" = "log_and_continue",
    generated_at_for_test: datetime | None = None,
  ) -> RunLoopSummary

  per iteration:
    1. report = run_strategy_cycle(client, scan_config, cycle_config)  # paper-execute ON if configured
    2. PaperStrategyCycleLog(cycle_report_log_path).append(report)
    3. mark_paper_portfolio_nav(trade_journal_path, starting_cash=..., client=..., marked_at=now, nav_log_path=nav_log_path)
    4. if repeat_mode == "interval" and iterations < max: sleep(interval_seconds)
    5. repeat until max_iterations or once

  each iteration wrapped in try/except (on_cycle_error="log_and_continue" → record error, continue)

RunLoopSummary (frozen, paper_only=True, report_only=True):
    iterations_completed: int
    iterations_failed: int
    first_iteration_at: datetime
    last_iteration_at: datetime
    last_error: str | None
    paper_only: bool = True
    report_only: bool = True
```

## CLI

`run` subparser: reuses `strategy-cycle` args (--limit, --archive-root,
--max-markets, --prefilter/--no-prefilter, --paper-execute, --paper-journal)
+ `--starting-cash`, `--cycle-log`, `--nav-log`, `--repeat-interval` (seconds,
default 0 = single shot), `--max-iterations` (default 1).

Single-shot mode (repeat_interval=0, max_iterations=1) == one cycle + one NAV
mark, identical to running strategy-cycle then portfolio-nav manually.

## Validation rules

- interval_seconds >= 0; max_iterations >= 1 (bool rejected).
- iterations_completed + iterations_failed == total attempted.
- RunLoopSummary.paper_only/report_only with `is`.
- On error: if on_cycle_error="log_and_continue", record last_error + increment
  iterations_failed; if "raise", propagate.

## Scope tests

- `runner.py` is a live-layer (like strategy_cycle). ALLOWED stdlib + {api,
  domain, normalize, pipeline, archive, scoring, forecast_provider,
  cost_aware_snapshot_builder, cost_aware_event_strategy, project_screening,
  strategy_cycle, journal, positions, paper_execution, paper_portfolio_nav}.
  NO book_imbalance_forecast (not needed — the cycle config carries forecast
  provider selection). Actually it may not need to import most of these —
  runner.py is a thin orchestrator that calls run_strategy_cycle +
  mark_paper_portfolio_nav. Minimal imports: strategy_cycle, paper_portfolio_nav,
  positions (for PaperStrategyCycleLog), journal (PaperTradeJournal path). Confirm
  during implementation.
- Forbidden execution fragments.

## Non-goals

No live orders/auth/wallets/credentials/exchange writes. No scheduler daemon
(uses time.sleep loop; external cron is the user's choice for production). No
async (thread pool is a later stage). No forecast log persistence (bonus
feature — defer if complex).

## Risks

1. **time.sleep blocks.** Acceptable for v0 (synchronous loop). A later stage
   can add async/scheduler.
2. **API rate limits over long runs.** Per-cycle try/except handles failures;
   the caller sets interval_seconds to control frequency.
3. **State accumulation.** Journals grow unbounded. Acceptable for v0;
   rotation is a later operational stage.
