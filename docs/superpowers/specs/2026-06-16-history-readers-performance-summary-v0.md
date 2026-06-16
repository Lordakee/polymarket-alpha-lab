# History Readers + Performance Summary v0 (Stage 6)

## Purpose

The system now persists three JSONL streams per run (cycle reports via
PaperStrategyCycleLog, paper trades via PaperTradeJournal [reader exists from
Stage 5], NAV snapshots via PaperNavLog) — but only paper trades can be read back.
Stage 6 adds readers for the other two + a performance-summary aggregator so the
user can see cumulative system performance over time (cycles run, markets scanned,
candidates ready, paper trades executed, realized/unrealized P&L, win rate).

Read-only data analysis. No live orders/auth/wallets/credentials/exchange writes.
No fetch (reads local JSONL only).

## Architecture

```text
strategy_cycle.py — ADDITIVE: PaperStrategyCycleLog.read() staticmethod (like Stage 5 journal reader)
positions.py      — ADDITIVE: PaperNavLog.read() staticmethod (same pattern)
performance_summary.py (NEW pure leaf):
  build_performance_summary(
    cycle_reports: tuple[PaperStrategyCycleReport, ...],
    trade_records: tuple[PaperTradeRecord, ...],
    nav_snapshots: tuple[PaperNavSnapshot, ...],
    *, config: PerformanceSummaryConfig, generated_at: datetime
  ) -> PerformanceSummary
cli.py — history subcommand: reads the 3 JSONL logs → build_performance_summary → prints
```

## Public API

```text
# strategy_cycle.py — additive reader
class PaperStrategyCycleLog:
    @staticmethod
    def read(path) -> tuple[PaperStrategyCycleReport, ...]: ...   # type-keyed coercion (get_type_hints)

# positions.py — additive reader
class PaperNavLog:
    @staticmethod
    def read(path) -> tuple[PaperNavSnapshot, ...]: ...           # same pattern

# performance_summary.py — NEW
__all__ = ("PerformanceSummaryConfig", "PerformanceSummary", "build_performance_summary")

PerformanceSummaryConfig (frozen):
    config_version: str

PerformanceSummary (frozen, paper_only=True, report_only=True):
    generated_at: datetime
    config_version: str
    cycle_count: int
    total_scan_market_count: int
    total_snapshot_ready_count: int
    total_cost_aware_report_count: int
    paper_trade_count: int
    last_exit_nav: Decimal | None              # from most-recent nav snapshot
    last_starting_cash: Decimal | None
    total_realized_pnl: Decimal | None         # from most-recent nav (cumulative)
    nav_snapshot_count: int
    first_cycle_at: datetime | None
    last_cycle_at: datetime | None
    paper_only: bool = True
    report_only: bool = True

build_performance_summary(
    cycle_reports, trade_records, nav_snapshots, *, config, generated_at
) -> PerformanceSummary
```

## Reader coercion (RECURSIVE — claude CRITICAL fix)

**Unlike Stage 5's PaperTradeRecord (no `__post_init__`), PaperStrategyCycleReport
and PaperNavSnapshot HAVE validating `__post_init__`** that checks nested fields via
`isinstance`. A flat `Report(**coerced_row)` with nested-as-dict will RAISE. The
reader MUST recursively reconstruct the entire nested dataclass tree.

**Shared helper (claude IMPORTANT fix):** extract a single `_from_jsonable(cls, row)`
into a new `json_recovery.py` (or promote journal.py's Stage 5 coercion into a shared
helper). All three readers (journal/strategy_cycle/positions) reuse it. NO triplicate.

```python
# json_recovery.py (NEW shared helper, ~70 lines)
def from_jsonable(cls, row: dict):
    """Recursively reconstruct a frozen dataclass from a _json_ready dict.
    Resolves field types via get_type_hints; for each field:
    - if type is a dataclass → recurse from_jsonable(FieldType, row[name])
    - if type is tuple[X, ...]:
        - if X is a dataclass → tuple(from_jsonable(X, e) for e in row[name])
        - if X is itself a tuple (e.g. tuple[str, int]) → tuple(tuple(_coerce_inner(x, v) for x,v in zip(X_args, e)) for e in row[name])
        - else → tuple(e for e in row[name])  # flat list→tuple
    - if type is Decimal/datetime → coerce (str→Decimal/ISO→datetime)
    - if value is None → None
    - else → pass-through
    Constructs cls(**reconstructed). The cls __post_init__ re-validates."""
```

**CRITICAL coverage (claude case a/b/c):** This handles (a) nested dataclasses,
(b) tuple[dataclass, ...], AND (c) nested non-dataclass tuples like
`blocked_counts: tuple[tuple[str, int], ...]` (JSON list-of-lists → tuple-of-tuples,
not tuple-of-lists). Without case (c), `_normalize_blocked_counts` rejects on every
cycle that blocked any market (almost always). The helper must deep-convert
list→tuple at EVERY tuple level. Enumerate every field in the full
PaperProjectScreeningReport subtree (candidates/queue_items/gate_results + their
Decimal/datetime/optional/nested-tuple fields) and confirm coverage before implementing.

## Performance summary logic

Pure arithmetic over the three tuples:
- cycle_count = len(cycle_reports)
- total_scan/ready/cost_aware = sum across cycle_reports
- paper_trade_count = len(trade_records)
- last_exit_nav / last_starting_cash / total_realized_pnl = from nav_snapshots[-1] if any
- first/last_cycle_at = min/max of cycle_reports.generated_at
All counts int; Decimals quantized. Empty inputs → zeros/None.

## CLI

`history --cycle-log <path> --trade-log <path> --nav-log <path>` → reads the 3 JSONL
files → build_performance_summary → prints summary (cycle_count, total markets scanned,
candidates ready, paper trades, last NAV, realized P&L, time span).

## Scope tests

- `test_performance_summary_scope.py` (NEW pure leaf): ALLOWED stdlib +
  `polymarket_alpha_lab.{strategy_cycle, journal, positions}` (it imports the report
  types). NO api. Six canonical tests.
- strategy_cycle/positions scope tests: adding `read()` staticmethod does NOT change
  `__all__` (read is a method, not export) and imports unchanged (stdlib only).

## Non-goals

No fetch. No live orders/auth/wallets. No time-series replay. No per-market drill-down
(v0 is aggregate counts only). No charting.

## Risks

1. Reader coercion correctness (same as Stage 5; mitigated by type-keyed get_type_hints).
2. PaperStrategyCycleReport has nested screening_report (PaperProjectScreeningReport |
   None) — which itself nests candidates/queue_items/gate_results. The recursive
   `from_jsonable` (see §"Reader coercion") reconstructs the FULL tree so __post_init__
   passes. performance_summary v0 only reads top-level count fields, but the reader
   returns fully-valid reconstructed reports (not partial). This is correct + future-proof.

## Open questions

1. Should readers live as staticmethods on the Log classes (colocated, like Stage 5
   journal) or as free functions in a new reader module? (Log classes = idiomatic.)
2. Should PerformanceSummary carry per-cycle breakdown or just aggregates? (Aggregates
   for v0; breakdown is a later stage.)
