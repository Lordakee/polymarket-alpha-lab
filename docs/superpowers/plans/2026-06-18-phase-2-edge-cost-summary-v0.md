# Phase 2 Edge Cost Summary v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a module-local pure `edge_cost_summary` reducer over caller-supplied `PaperForecastEvidenceObservation` values with complete executable-edge roles.

**Architecture:** Implement one leaf module that validates exact in-memory forecast evidence observations, filters to complete executable-edge role data, and returns a frozen paper-only/report-only/readonly descriptive summary. Keep the API module-local; do not add CLI, package-root exports, readers, writers, live-data wrappers, clients, auth/account/wallet/order behavior, ranking, recommendations, trade instructions, or financial advice.

**Tech Stack:** Python frozen dataclasses, `datetime`, `Decimal`, existing `PaperForecastEvidenceObservation` values, pytest, AST scope tests, CodeGraph-aware repo navigation.

---

## Commit Boundary

This plan is for a future implementation node. The current docs-only node must
not modify source, tests, README, package root, CLI, trend docs, evidence
snapshot docs, or unrelated docs.

## Planned File Structure

- Create: `src/polymarket_alpha_lab/edge_cost_summary.py`
  - Pure reducer only.
  - Module-local `__all__` only.
  - No file IO, network, clients, client Protocols, CLI, package-root export,
    reader, writer, replay, from-file API, live-data wrapper,
    auth/account/wallet/order behavior, ranking, recommendation, trade
    instruction, selection signal, or financial advice.
- Create: `tests/test_edge_cost_summary.py`
  - Behavior tests for validation, empty input, append-order first/latest
    semantics, complete-edge-role validation, aggregate metrics, ratios, and
    hard report flags.
- Create: `tests/test_edge_cost_summary_scope.py`
  - AST/source scope tests for imports, exports, forbidden names, forbidden
    calls, forbidden strings, and package-root/CLI non-integration.

Do not modify:

- `src/polymarket_alpha_lab/__init__.py`
- `src/polymarket_alpha_lab/cli.py`
- existing readers, writers, logs, replay helpers, package-root files, README, or
  unrelated docs

## TDD Tasks

### Task 1: Behavior Tests

- [ ] Add failing tests for empty input:
  - `edge_observation_count == 0`
  - first/latest observation timestamps are `None`
  - unique market, strategy, and risk-tag counts are zero
  - all mean/worst metrics are `None`
  - ratio fields are `None`
  - `status == "empty_edge_cost_summary"` if a status field is implemented
  - `paper_only is True`, `report_only is True`, and `readonly is True`

- [ ] Add failing validation tests:
  - config must be exact `PaperEdgeCostSummaryConfig`
  - `generated_at` must be a `datetime`
  - observations must be a `list` or `tuple`
  - strings, bytes, mappings, arbitrary iterables, wrong types, and mixed types
    are rejected
  - every input must be exact `PaperForecastEvidenceObservation`
  - every input must have `paper_only is True`
  - every input must have all complete executable-edge role fields:
    `theoretical_edge_ratio`, `executable_edge_ratio`, `fill_probability`,
    `residual_exposure_ratio`, and `paper_return_ratio`

- [ ] Add failing append-order tests:
  - `first_observed_at` comes from `observations[0]`
  - `latest_observed_at` comes from `observations[-1]`
  - duplicate timestamps are allowed
  - non-monotonic timestamps do not cause sorting

- [ ] Add failing aggregate metric tests:
  - mean theoretical edge and mean executable edge use all complete edge
    observations
  - edge cost gap is `max(theoretical_edge_ratio - executable_edge_ratio, 0)`
  - mean and worst edge cost gap are quantized to `Decimal("0.000001")`
  - negative executable-edge count and ratio are descriptive only
  - mean fill probability and low fill probability count/ratio are descriptive
  - mean residual exposure, worst residual exposure, and high residual exposure
    count/ratio are descriptive
  - mean paper return and positive paper return count/ratio are descriptive
  - none of these metrics are represented as ranking, recommendation, selection,
    trade instruction, or financial-advice signals

Run:

```bash
.venv/bin/python -m pytest tests/test_edge_cost_summary.py -q
```

Expected before implementation: fail during collection or behavior assertions.

### Task 2: Scope Tests

- [ ] Add AST/import tests proving the module imports only stdlib plus
  `polymarket_alpha_lab.forecast_evidence`.
- [ ] Assert `__all__` is exactly:

```python
(
    "PaperEdgeCostSummaryConfig",
    "PaperEdgeCostSummaryReport",
    "build_paper_edge_cost_summary_report",
)
```

- [ ] Assert there is no package-root export in
  `src/polymarket_alpha_lab/__init__.py`.
- [ ] Assert there is no CLI import, parser branch, command, or command text in
  `src/polymarket_alpha_lab/cli.py`.
- [ ] Assert symbol names and source text do not expose readers, writers, JSONL
  helpers, replay helpers, from-file APIs, live-data wrappers, network calls,
  auth, accounts, wallets, private keys, orders, clients, signing, submission,
  cancellation, fills, rankings, recommendations, selections, trade
  instructions, position sizing, promotion, transition, or financial advice.

Run:

```bash
.venv/bin/python -m pytest tests/test_edge_cost_summary_scope.py -q
```

Expected before implementation: fail because the module does not exist.

### Task 3: Implement Pure Reducer

- [ ] Create `src/polymarket_alpha_lab/edge_cost_summary.py`.
- [ ] Add a module docstring that states the boundary plainly:
  paper-only, report-only, readonly, no live trading, no auth, no wallet, no
  account reads, no order behavior, no ranking, no recommendation, no trade
  instruction, and no financial advice.
- [ ] Define frozen `PaperEdgeCostSummaryConfig`.
  - Suggested thresholds are descriptive only:
    `low_fill_probability_threshold=Decimal("0.500000")`
    and `high_residual_exposure_threshold=Decimal("0.100000")`.
- [ ] Define frozen `PaperEdgeCostSummaryReport`.
  - Include `generated_at`, counts, first/latest timestamps, unique counts, mean
    and worst cost-gap metrics, fill-probability metrics, residual-exposure
    metrics, paper-return metrics, optional descriptive status, and hard
    `paper_only`, `report_only`, `readonly` flags.
- [ ] Validate exact config type and `generated_at`.
- [ ] Normalize observations from only `list` or `tuple`.
- [ ] Validate every source observation is exact
  `PaperForecastEvidenceObservation`, is paper-only, and has the complete edge
  role fields: theoretical edge, executable edge, fill probability, residual
  exposure, and paper return.
- [ ] Build the summary using append order only.
- [ ] Quantize all ratios and means to `Decimal("0.000001")`.
- [ ] Keep all metric names and statuses descriptive; do not encode ranking,
  recommendation, selection, trade instruction, promotion, transition, or
  financial-advice semantics.

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_edge_cost_summary.py \
  tests/test_edge_cost_summary_scope.py -q
```

Expected after implementation: pass.

### Task 4: Verification

- [ ] Run targeted summary tests:

```bash
.venv/bin/python -m pytest \
  tests/test_edge_cost_summary.py \
  tests/test_edge_cost_summary_scope.py -q
```

- [ ] Run adjacent evidence and cost tests to catch contract drift:

```bash
.venv/bin/python -m pytest \
  tests/test_forecast_evidence.py \
  tests/test_paper_trade_cost_audit.py \
  tests/test_cost_aware_event_strategy.py \
  tests/test_edge_cost_summary.py \
  tests/test_edge_cost_summary_scope.py -q
```

- [ ] Run full suite:

```bash
.venv/bin/python -m pytest -q
```

- [ ] Run whitespace check:

```bash
git diff --check
```

- [ ] Review final diff and confirm only the planned implementation and test
  files changed, with no package-root export, CLI behavior, reader/writer,
  live-data wrapper, auth/account/wallet/order behavior, ranking,
  recommendation, selection signal, trade instruction, or financial advice.

## Notes For Implementers

- This plan does not claim any tests have passed.
- Use CodeGraph first in indexed workspaces before grep/find or manual file
  reads.
- Metrics are descriptive cost/slippage/liquidity-adjacent evidence only, not a
  selection signal or trade signal.
- Keep commits small: tests RED, implementation GREEN, refactor only after the
  targeted tests pass.
