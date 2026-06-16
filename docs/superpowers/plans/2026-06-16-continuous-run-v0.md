# Continuous Run v0 Plan (Stage 7)

**Goal:** `run` command: strategy-cycle + paper-execute + portfolio-nav in a loop. Starts accumulating longitudinal data for promotion gates. Pure composition.

## Pre-stage gate
- [ ] 0. Claude pre-stage (claude-opus-4-8 / effort max). Codex fallback after 2 failures.

## Tasks
- [ ] 1. `runner.py` (NEW): `run_strategy_loop(*, client, scan_config, cycle_config, starting_cash, nav_log_path, cycle_report_log_path, repeat_mode, interval_seconds, max_iterations, on_cycle_error) -> RunLoopSummary`. Per iteration: run_strategy_cycle → PaperStrategyCycleLog.append → mark_paper_portfolio_nav → optional sleep. try/except per iteration (log_and_continue default). RED+GREEN (fake client + mock sleep; single-shot; multi-iteration; error isolation).
- [ ] 2. `test_runner_scope.py` (NEW): live-layer. ALLOWED stdlib + minimal {strategy_cycle, paper_portfolio_nav, positions}. Forbidden execution fragments. Six canonical.
- [ ] 3. CLI `run` subparser + test_cli.
- [ ] 4. Wiring: __init__ + test_init + README + scope unskip.
- [ ] 5. Full verify.

## Post-stage gate
- [ ] 6. Claude post-stage (Phase 1; per-iteration isolation; no float).

## Commit (user-authorized)
- [ ] 7. `feat: add continuous run v0`.
