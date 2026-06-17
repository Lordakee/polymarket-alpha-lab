# Local Observability Trends v0 Spec

## Goal

Define the next pure local observability modules over already-built Phase 1
reports so operators can inspect append-order trends across local paper evidence
without changing strategy behavior.

These modules are next-node candidates. They must not be mixed into the
Strategy Evidence Snapshot v0 commit unless explicitly selected.

## Scope

Add four pure leaf modules in future implementation work:

- `strategy_evidence_trend.py`
- `outcome_freshness.py`
- `nav_risk_trend.py`
- `paper_trade_cost_trend.py`

Each module consumes already-built typed report values supplied by the caller.
The pure modules do not read logs, discover files, fetch markets, construct
clients, or write artifacts. Any future CLI or log-reader orchestration is a
separate node and must remain outside these pure modules.

Default behavior of existing commands is unchanged.

## Phase 1 Boundary

Hard requirements for every module:

- `paper_only is True`
- `report_only is True`
- `readonly is True`
- Pure local report reduction over caller-supplied report objects only.
- No live trading.
- No account authentication.
- No wallet or private-key handling.
- No account reads.
- No order placement, signing, submission, cancellation, or order-client types.
- No network calls.
- No file IO in pure modules, including no JSONL reads, writes, repairs, or path
  validation.
- No public client construction and no client Protocol definitions.
- No market ranking, project selection, recommendation, trade instruction, or
  financial advice.
- No changes to Strategy Evidence Snapshot v0 unless explicitly selected.
- No changes to `runner.py`, paper execution, screening weights, order sizing,
  strategy-cycle behavior, NAV marking behavior, outcome tracking behavior, or
  Strategy Risk Audit math.

Allowed:

- Validate exact report dataclass types.
- Validate all supplied inputs preserve `paper_only is True` and
  `report_only is True`.
- Build frozen in-memory trend reports.
- Use `Decimal` for ratios and numeric trend metrics.
- Use append order as the source of truth for `first_*`, `latest_*`, and
  consecutive counts.
- Return `None` for ratios or time deltas that cannot be computed from empty or
  insufficient input.

## Shared Semantics

Input order is append order. `latest_*` fields refer to the last report supplied,
not the maximum timestamp after sorting. Duplicate timestamps are allowed because
local reports can be produced close together and because the append-only artifact
is the source of truth.

Every trend report should include:

- `generated_at`
- `config_version`
- `<source>_report_count`
- `first_report_generated_at`
- `latest_report_generated_at`
- module-specific latest descriptive fields
- module-specific count rows and ratios
- `paper_only`
- `report_only`
- `readonly`

Ratios should be `Decimal` values quantized to `0.000001`. Empty input yields
zero counts, absent timestamps, empty rows where appropriate, and `None`
aggregate ratios/means.

Status labels and row names describe local paper evidence only. They do not
approve, rank, recommend, instruct, authorize, or block any trade or strategy
action.

## Module Semantics

### `strategy_evidence_trend.py`

Consumes a list or tuple of already-built
`PaperStrategyEvidenceSnapshotReport` values.

Expected public API:

- `PaperStrategyEvidenceTrendConfig`
- `PaperStrategyEvidenceTrendStatusRow`
- `PaperStrategyEvidenceTrendGapRow`
- `PaperStrategyEvidenceTrendReport`
- `build_paper_strategy_evidence_trend_report(reports, *, config, generated_at)`

The report summarizes local evidence snapshot status movement:

- snapshot report count
- first/latest snapshot timestamps
- latest snapshot status
- status counts and ratios for known Strategy Evidence Snapshot statuses
- evidence-gap counts and ratios for known snapshot evidence-gap names
- latest evidence-gap names
- consecutive latest `local_risk_flags` count
- consecutive latest non-observed count

The module must not import log readers, CLI code, clients, paper journals,
NAV logs, outcome logs, or Strategy Risk Audit logs.

### `outcome_freshness.py`

Consumes a list or tuple of already-built `OutcomeTrackingReport` values.

Expected public API:

- `OutcomeFreshnessConfig`
- `OutcomeFreshnessStatusRow`
- `OutcomeFreshnessReport`
- `build_outcome_freshness_report(reports, *, config, generated_at)`

The report summarizes how fresh local outcome tracking evidence is:

- outcome report count
- first/latest outcome report timestamps
- latest total checked, resolved, and pending counts
- latest resolved ratio and pending ratio
- latest report age in seconds
- consecutive latest reports with pending outcomes
- counts and ratios for descriptive freshness statuses such as
  `empty_outcome_history`, `latest_outcomes_fresh`,
  `latest_outcomes_pending`, and `latest_outcomes_stale`

Freshness status is descriptive only. It must not trigger refreshes, fetch
markets, call `check_outcomes`, construct an `OutcomeTrackerClient`, or imply a
trade action.

### `nav_risk_trend.py`

Consumes a list or tuple of already-built `PaperNavRiskMetricsReport` values.

Expected public API:

- `PaperNavRiskTrendConfig`
- `PaperNavRiskTrendStatusRow`
- `PaperNavRiskTrendReport`
- `build_paper_nav_risk_trend_report(reports, *, config, generated_at)`

The report summarizes local NAV risk metric movement:

- NAV risk report count
- first/latest report timestamps
- latest exit NAV
- latest cumulative return, max drawdown, max drawdown percent, and volatility
- latest open position count
- latest fully executable, partially executable, and no-exit-depth counts
- latest largest market exposure value and share
- worst observed max drawdown percent across supplied reports
- consecutive latest reports with unexecutable open positions

The module is observational only. It must not call `PaperNavLog.read`, mark NAV,
fetch order books, construct market-data clients, or change NAV risk gate
thresholds.

### `paper_trade_cost_trend.py`

Consumes a list or tuple of already-built `PaperTradeCostAuditReport` values.

Expected public API:

- `PaperTradeCostTrendConfig`
- `PaperTradeCostTrendStatusRow`
- `PaperTradeCostTrendReport`
- `build_paper_trade_cost_trend_report(reports, *, config, generated_at)`

The report summarizes local paper trade cost-audit movement:

- cost audit report count
- first/latest report timestamps
- latest trade count
- latest fill rate
- latest mean theoretical edge
- latest mean cost-adjusted edge
- latest mean edge cost drag
- latest total edge cost drag
- latest partial fill and negative cost-adjusted edge counts
- worst observed mean edge cost drag
- worst observed negative cost-adjusted edge count
- consecutive latest reports with negative cost-adjusted edges

The module is observational only. It must not call `PaperTradeJournal.read`,
simulate fills, place paper trades, construct clients, or alter cost-audit math.

## Acceptance Criteria

- Each builder accepts only a list or tuple of the exact expected report type and
  rejects strings, bytes, mappings, arbitrary iterables if not allowed by the
  module, mixed types, and wrong report types.
- Each builder validates exact config type and `generated_at` datetime.
- Each builder rejects any source report whose `paper_only` or `report_only`
  flag is not exactly `True`.
- Each output report is frozen and enforces `paper_only is True`,
  `report_only is True`, and `readonly is True`.
- Empty inputs produce deterministic empty reports with zero counts, no latest
  values, no timestamps, and `None` ratios where denominator data is absent.
- Non-empty inputs preserve append order for first/latest values and
  consecutive counts.
- Count rows cover the module's known statuses or names in deterministic order.
- Ratio rows use `Decimal` and are quantized to `0.000001`.
- Scope tests prove the four pure modules import only stdlib plus the one
  required typed report module each.
- Scope tests reject imports or public names related to live trading, auth,
  wallets, orders, clients, network, file IO, ranking, recommendations, trade
  instructions, or financial advice.
- Existing Strategy Evidence Snapshot v0 spec, plan, source, and tests are not
  modified by this node unless explicitly selected later.

## Verification Commands

Future implementation should run:

```bash
.venv/bin/python -m pytest \
  tests/test_strategy_evidence_trend.py \
  tests/test_outcome_freshness.py \
  tests/test_nav_risk_trend.py \
  tests/test_paper_trade_cost_trend.py \
  tests/test_local_observability_trend_scope.py \
  -q
```

```bash
.venv/bin/python -m compileall src/polymarket_alpha_lab
```

```bash
git diff --check
```
