# Phase 2 Edge Cost Summary v0 Spec

## Goal

Add a pure module-local `edge_cost_summary` reducer that summarizes
cost/slippage/liquidity-adjacent evidence across caller-supplied
`PaperForecastEvidenceObservation` values with a complete executable-edge role.

This is a paper-only, report-only, readonly Phase 2 reporting node. It consumes
already-typed in-memory observations and returns an in-memory descriptive report.
It does not read evidence, write logs, fetch data, construct clients, execute
orders, rank markets, recommend trades, or change strategy behavior.

## Scope

Future implementation should add one leaf module:

- `src/polymarket_alpha_lab/edge_cost_summary.py`

Expected module-local public API:

- `PaperEdgeCostSummaryConfig`
- `PaperEdgeCostSummaryReport`
- `build_paper_edge_cost_summary_report(observations, *, config, generated_at)`

The API is module-local only. Do not add package-root exports, CLI commands,
readers, writers, replay helpers, from-file APIs, path validators, live-data
wrappers, client Protocols, or orchestration surfaces.

## Inputs

The builder accepts only a caller-supplied `list` or `tuple` of exact
`PaperForecastEvidenceObservation` values, plus an exact
`PaperEdgeCostSummaryConfig` and a `datetime` `generated_at`.

Each observation must be paper-only and must have the complete executable-edge
role already enforced by `forecast_evidence.py`:

- `theoretical_edge_ratio`
- `executable_edge_ratio`
- `fill_probability`
- `residual_exposure_ratio`
- `paper_return_ratio`

Reject strings, bytes, mappings, arbitrary iterables, mixed types, wrong
observation values, wrong config values, invalid `generated_at`, non-paper
observations, and observations missing any field in the complete edge role.

## Semantics

The reducer is descriptive only. It should summarize edge degradation and
execution-quality evidence that is already present on the supplied observations:

- edge observation count
- first and latest `observed_at` in append order
- unique market, strategy, and risk-tag counts
- mean theoretical edge
- mean executable edge
- mean edge cost gap: `max(theoretical_edge_ratio - executable_edge_ratio, 0)`
- worst edge cost gap
- negative executable-edge count and ratio
- mean fill probability
- low fill probability count and ratio
- mean residual exposure
- worst residual exposure
- high residual exposure count and ratio
- mean paper return
- positive paper return count and ratio

Input order is append order for first/latest fields. Do not sort observations by
timestamp. Empty input yields a deterministic empty report with zero counts,
absent timestamps, absent means/worst values, and `None` ratios where the
denominator is zero.

Ratios and means use `Decimal` and the local ratio quantum convention
(`0.000001`).

## Status Framing

This module should not add trading gates or selection semantics. Any optional
status field must describe report completeness or descriptive evidence state
only, for example:

- `empty_edge_cost_summary`
- `edge_cost_evidence_observed`

Metrics are descriptive cost/slippage/liquidity-adjacent evidence only. They are
not a selection signal, ranking signal, recommendation, trade instruction, or
financial advice.

## Hard Boundaries

The module must remain:

- paper-only
- report-only
- readonly
- pure local reduction over caller-supplied `PaperForecastEvidenceObservation`
  values
- module-local API only

The module must not:

- add CLI behavior
- add package-root exports
- read files or JSONL logs
- write files or JSONL logs
- add readers, writers, replay helpers, from-file APIs, path validators, or
  repair utilities
- add live-data wrappers
- fetch market data
- construct clients or client Protocols
- authenticate
- read accounts, balances, positions, fills, orders, wallets, private keys, or
  user exchange state
- place, sign, submit, cancel, amend, or simulate orders
- change paper execution, screening, strategy-cycle, NAV, outcome tracking,
  forecast evidence, cost-aware strategy, or paper trade cost-audit behavior
- rank markets, strategies, reports, observations, or models
- recommend trades or investments
- provide trade instructions
- provide financial advice

## Acceptance Criteria

- The builder is pure and deterministic for supplied observation order.
- The output report is frozen and hard-enforces `paper_only is True`,
  `report_only is True`, and `readonly is True`.
- Validation accepts only list/tuple inputs of exact
  `PaperForecastEvidenceObservation` values with complete edge roles.
- Empty input produces a deterministic empty descriptive summary.
- Non-empty input preserves append order for first/latest fields.
- Cost-gap, fill-probability, residual-exposure, and paper-return metrics are
  descriptive aggregates only.
- Scope tests reject imports, exports, names, and strings that would create live
  trading, auth, wallet, private-key, account, order, reader/writer, CLI,
  ranking, recommendation, trade-instruction, selection-signal, or
  financial-advice surfaces.

## Verification Commands

Future implementation should run:

```bash
.venv/bin/python -m pytest \
  tests/test_edge_cost_summary.py \
  tests/test_edge_cost_summary_scope.py -q
.venv/bin/python -m pytest -q
git diff --check
```
