# History Readers + Performance Summary v0 Plan (Stage 6)

**Goal:** Read the 3 persisted JSONL streams → cumulative performance summary. Read-only.

## Pre-stage gate
- [ ] 0. Claude pre-stage (claude-opus-4-8 / effort max). Codex fallback after 2 failures.

## Tasks
- [ ] 1. `strategy_cycle.py`: add `PaperStrategyCycleLog.read(path)` staticmethod (type-keyed coercion via get_type_hints; nested screening_report stays as dict — only top-level fields needed). RED (append→read round-trip) + GREEN.
- [ ] 2. `positions.py`: add `PaperNavLog.read(path)` staticmethod (same pattern). RED + GREEN.
- [ ] 3. `performance_summary.py` (NEW pure leaf): `build_performance_summary(cycle_reports, trade_records, nav_snapshots, *, config, generated_at) -> PerformanceSummary`. RED + GREEN (empty inputs → zeros/None; populated → correct aggregates).
- [ ] 4. `test_performance_summary_scope.py` (NEW): ALLOWED stdlib + {strategy_cycle, journal, positions}. NO api. Six canonical.
- [ ] 5. CLI `history --cycle-log --trade-log --nav-log` + test_cli coverage.
- [ ] 6. Wiring: __init__ export build_performance_summary + test_init + README + scope unskip.
- [ ] 7. Full verify.

## Post-stage gate
- [ ] 8. Claude post-stage (reader coercion; no float; Phase 1 read-only; nested-as-dict limitation documented).

## Commit (user-authorized)
- [ ] 9. `feat: add history readers and performance summary v0`.
