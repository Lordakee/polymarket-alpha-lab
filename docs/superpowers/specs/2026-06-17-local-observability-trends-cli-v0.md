# Local Observability Trends CLI/Runner v0 Spec

## Goal

Expose the already-built local observability trend reducers through one
paper-only CLI report over local JSONL logs. The command lets an operator inspect
local paper evidence trends without writing Python glue and without changing any
strategy, run, execution, or live-market behavior.

## Command

Add:

```bash
polymarket-alpha-lab observability-trends \
  --cycle-log artifacts/strategy-cycle.jsonl \
  --trade-log artifacts/paper-trades.jsonl \
  --nav-log artifacts/nav.jsonl \
  --outcome-log artifacts/outcomes.jsonl \
  --strategy-audit-log artifacts/strategy-audits.jsonl \
  --outcome-stale-after-seconds 86400
```

Required options:

- `--cycle-log <path>`: read with `PaperStrategyCycleLog.read`.
- `--trade-log <path>`: read with `PaperTradeJournal.read`.
- `--nav-log <path>`: read with `PaperNavLog.read`.

Optional options:

- `--outcome-log <path>`: when present, read with `OutcomeTrackingLog.read`;
  when omitted, use no outcome reports.
- `--strategy-audit-log <path>`: when present, read with
  `PaperStrategyRiskAuditLog.read`; when omitted, use no audit reports.
- `--outcome-stale-after-seconds <int>`: forwarded to
  `OutcomeFreshnessConfig.stale_after_seconds`; default is `86400`.

The command prints a compact stdout report and exits nonzero on invalid local
input. It must not append to any log, write an artifact, repair files, or create
directories.

## Scope

In scope:

- Add `src/polymarket_alpha_lab/local_observability_trends.py`.
- Add a CLI command named `observability-trends`.
- Build a frozen container report named `LocalObservabilityTrendsReport` with:
  - `strategy_evidence_trend: PaperStrategyEvidenceTrendReport`
  - `outcome_freshness: OutcomeFreshnessReport`
  - `nav_risk_trend: PaperNavRiskTrendReport`
  - `paper_trade_cost_trend: PaperTradeCostTrendReport`
- Read only the caller-supplied local JSONL paths through existing typed log
  readers.
- Reuse existing local reducers for performance summary, NAV risk metrics, paper
  trade cost audit, strategy audit history, strategy evidence snapshot, and the
  four trend reducers.
- Preserve source/append order from the typed readers exactly for local trend
  prefixes. Do not sort by timestamp.

Out of scope:

- No network calls.
- No public client construction or client Protocol additions.
- No auth, wallet, private-key, credential, account, or position-account reads.
- No order placement, signing, submission, cancellation, or order-client types.
- No live trading.
- No market ranking, project selection, recommendation, trade instruction,
  approval workflow, or financial advice.
- No changes to `run`, `runner.py`, `strategy-cycle`, `strategy_cycle.py`,
  screening weights, strategy math, paper execution, NAV marking behavior,
  outcome tracking behavior, or Strategy Risk Audit math.
- No package-root export changes for this node.

## Runner Architecture

The new module exposes:

- `LocalObservabilityTrendsConfig`
- `LocalObservabilityTrendsReport`
- `run_local_observability_trends(...)`

`LocalObservabilityTrendsReport` includes:

- `generated_at`
- `config_version`
- `strategy_evidence_trend`
- `outcome_freshness`
- `nav_risk_trend`
- `paper_trade_cost_trend`
- `paper_only is True`
- `report_only is True`
- `readonly is True`

`run_local_observability_trends(...)` is the local IO adapter. It reads the
explicitly supplied paths and builds the four child trend reports. It must not
construct clients, call `client_factory`, call `check_outcomes`, fetch markets,
fetch order books, write files, or append to logs.

## Prefix Semantics

Required local histories are append-only streams. The source order returned by
the typed readers is the only ordering authority for local trend prefixes.

- `trade-log`: build a `PaperTradeCostAuditReport` sequence from non-empty
  append-order prefixes of the `PaperTradeRecord` tuple, then pass that sequence
  to `build_paper_trade_cost_trend_report`. If the trade log is empty, pass an
  empty sequence.
- `nav-log`: build a `PaperNavRiskMetricsReport` sequence from non-empty
  append-order prefixes of the `PaperNavSnapshot` tuple, then pass that sequence
  to `build_paper_nav_risk_trend_report`. Do not timestamp-sort NAV snapshots
  before building local observability trend prefixes. The standalone NAV risk
  metrics reducer may keep its shared chronological metric behavior, but this
  runner's local trend prefix order is still source/append order. If the NAV log
  is empty, pass an empty sequence.
- `cycle-log`, `trade-log`, and `nav-log`: build a
  `PaperStrategyEvidenceSnapshotReport` sequence over append-order prefixes of
  the required histories, then pass that sequence to
  `build_paper_strategy_evidence_trend_report`. Use one prefix step from `1` to
  `max(len(cycle_reports), len(trade_records), len(nav_snapshots))`; each stream
  contributes `stream[:step]`, naturally capped by Python slicing. If all three
  required histories are empty, pass an empty snapshot sequence.

Optional histories are not independent prefix drivers:

- `outcome-log`: use all `OutcomeTrackingReport` entries for
  `build_outcome_freshness_report`. For strategy evidence prefix snapshots, use
  the latest outcome report within the matching prefix slice, or `None` when the
  log is omitted or empty.
- `strategy-audit-log`: use the matching prefix slice to build
  `PaperStrategyRiskAuditHistoryReport` for strategy evidence prefix snapshots.
  Use `None` when the log is omitted or empty.

Duplicate timestamps are allowed. Latest means last by append order, not max
timestamp, for local observability prefix selection and container reporting.
Lower-level reducers may keep their own shared metric semantics, but that does
not permit this runner to reorder local trend prefixes.

## CLI Output

The command prints a compact summary containing:

- strategy evidence trend status, snapshot count, and latest gaps
- outcome freshness status, report count, and latest age seconds
- NAV risk trend status, report count, and latest exit NAV
- paper trade cost trend status, report count, and latest mean edge cost drag
- container `paper_only`, `report_only`, and `readonly` flags

Printed text is observational only. It must not approve, block, rank,
recommend, or instruct any trade or strategy action.

## Acceptance Criteria

- `observability-trends` requires `--cycle-log`, `--trade-log`, and `--nav-log`.
- `--outcome-stale-after-seconds` defaults to `86400`, rejects invalid values
  through config validation, and is passed to `OutcomeFreshnessConfig`.
- Omitted optional logs are treated as empty optional histories.
- Supplied optional logs are read fully in append order.
- Required histories use source/append-order prefix semantics exactly as
  specified, including NAV prefixes supplied to NAV risk trend inputs.
- All child reports are produced by already-existing reducers.
- The container report enforces `paper_only is True`, `report_only is True`, and
  `readonly is True`.
- Empty local files yield deterministic empty child trend reports where the
  underlying reducers support empty input.
- Invalid JSONL or invalid typed recovery from any supplied log fails the command
  nonzero with an error message on stderr.
- The command does not call `client_factory`, construct
  `PolymarketPublicClient`, call `check_outcomes`, fetch markets, fetch books,
  read credentials, or write any file.
- There are no changes to `run`, `runner.py`, `strategy-cycle`, or
  `strategy_cycle.py`.

## Verification Commands

```bash
.venv/bin/python -m pytest \
  tests/test_local_observability_trends.py \
  tests/test_local_observability_trends_report_validation.py \
  tests/test_local_observability_trends_runner.py \
  tests/test_local_observability_trends_scope.py \
  tests/test_cli.py \
  -q
```

```bash
.venv/bin/python -m compileall src/polymarket_alpha_lab
```

```bash
git diff --check
```
