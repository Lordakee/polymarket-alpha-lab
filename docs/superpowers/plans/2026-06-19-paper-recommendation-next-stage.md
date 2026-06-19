# Paper Recommendation Next Stage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the next paper-only recommendation stage for probability-event markets by adding side-aware edge scoring, paper capital cost, queue/risk budget/reason-trend reports, and readonly CLI workflows without creating any live trading surface.

**Architecture:** The next stage stays a pure reducer/report layer. Each module consumes already-materialized paper reports or explicit local paper inputs, emits frozen report objects with `paper_only`, `report_only`, and `readonly` flags, uses Decimal-only math, preserves deterministic ordering, and records decisions through append-only or readonly artifacts. No task in this plan may add authentication, wallet access, private-key access, signing, real order construction, order submission, order cancellation, relayer calls, client mutation, or exchange/network mutation.

**Tech Stack:** Python dataclasses, `Decimal`, existing Polymarket Alpha Lab reducer patterns, pytest, existing JSONL recovery helpers, CodeGraph-first navigation, readonly CLI reporting.

---

## Strict Phase Boundary

This plan is paper-only, report-only, and readonly. A recommendation row,
selected side, selected notional, queue admission, risk budget allocation,
readiness pass, or reason trend is a journal artifact only.

Forbidden in every task:

- account authentication or credential reads
- wallet or private-key access
- signing of any payload
- real order construction, order tickets, order intents, or exchange-ready
  payloads
- order submission, cancellation, replacement, or status mutation
- relayer, exchange, or network mutation
- live trading adapters or client code that can mutate external state

Allowed in every task:

- typed paper reports
- Decimal-only scoring and cost reducers
- append-only local JSONL paper logs
- readonly history/trend reducers
- CLI commands that read supplied local files and print reports
- tests that use direct constructors and local temp files only

## Module Map

- `src/polymarket_alpha_lab/paper_probability_side_edge.py`
  - New side-aware reducer for YES/NO probability edge, costs, liquidity, and
    settlement/finalization timing.
- `tests/test_paper_probability_side_edge.py`
  - Constructor, scoring, ordering, and no-live-boundary tests for side edge
    rows.
- `src/polymarket_alpha_lab/paper_capital_cost.py`
  - New reducer for paper-only capital carrying cost and opportunity cost.
- `tests/test_paper_capital_cost.py`
  - Decimal math and validation coverage for capital-cost rows.
- `src/polymarket_alpha_lab/paper_recommendation_queue.py`
  - New reducer that admits ranked paper recommendations into a journal queue
    under capacity, freshness, liquidity, and settlement constraints.
- `tests/test_paper_recommendation_queue.py`
  - Queue ordering, cap, stale, and blocked-row coverage.
- `src/polymarket_alpha_lab/paper_recommendation_risk_budget.py`
  - New reducer for per-cycle, per-market, event/theme, and correlated exposure
    paper budgets.
- `tests/test_paper_recommendation_risk_budget.py`
  - Budget allocation, zero-allocation, and reason-code coverage.
- `src/polymarket_alpha_lab/paper_recommendation_reason_trend.py`
  - New readonly reducer that summarizes reason-code movement over time.
- `tests/test_paper_recommendation_reason_trend.py`
  - Trend, transition, canonical reason-code, and deterministic ordering tests.
- `src/polymarket_alpha_lab/cli.py`
  - Future readonly report commands only after reducers exist.
- `tests/test_cli.py`
  - Command coverage that reads local paper artifacts and prints summary rows
    without constructing clients or writing exchange-facing artifacts.
- `tests/test_strategy_recommendation_layer_scope.py`
  - Extend forbidden-surface checks for the new modules and CLI commands.
- `docs/strategy-recommendation-layer.md`
  - Keep public documentation synchronized with the new paper-only modules.

## Probability-Event Recommendation Logic

The next stage should score probability-event positions at the side level. A
binary event has two paper candidate sides:

- `yes`: pays if the event resolves YES.
- `no`: pays if the event resolves NO.

For a YES row:

- `side_probability = forecast_probability`
- `side_price = conservative executable YES entry price`
- `gross_probability_edge = side_probability - side_price`

For a NO row:

- `side_probability = 1 - forecast_probability`
- `side_price = conservative executable NO entry price`
- `gross_probability_edge = side_probability - side_price`

For both sides:

- `total_cost_per_share = fee_cost + spread_cost + slippage_cost + funding_cost + finalization_cost + time_cost + risk_cost + capital_cost`
- `net_probability_edge = gross_probability_edge - total_cost_per_share`
- `recommendation_score` must be positive only when `net_probability_edge` is
  positive and readiness evidence allows the row to be selected.

Liquidity and settlement/finalization timing should be first-class fields. A
high raw edge with weak liquidity, stale market context, stale settlement
context, unresolved finalization risk, or excessive capital lockup should rank
below a cleaner lower-edge row or become a watch or reject row.

## Task 1: Side-Aware Probability Edge Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_probability_side_edge.py`
- Create: `tests/test_paper_probability_side_edge.py`
- Modify: `tests/test_strategy_recommendation_layer_scope.py`

- [ ] **Step 1: Write failing constructor and scoring tests**

Add tests that construct a YES row and a NO row from the same
`forecast_probability`, assert side probability inversion, and verify that net
edge subtracts every cost component with Decimal precision.

Required test cases:

- YES side with forecast `0.640000`, executable side price `0.570000`, total
  costs `0.015000`, and net probability edge `0.055000`.
- NO side with forecast `0.640000`, side probability `0.360000`, executable
  side price `0.310000`, total costs `0.015000`, and net probability edge
  `0.035000`.
- A zero or negative net edge produces `watch` or `reject`, never `recommend`.
- A row with missing or stale liquidity evidence cannot be selected.
- A row with settlement/finalization timing outside the configured freshness
  window cannot be selected.

Run:

```bash
pytest tests/test_paper_probability_side_edge.py -v
```

Expected before implementation: FAIL because the module does not exist.

- [ ] **Step 2: Implement the side edge dataclasses**

Create frozen dataclasses:

- `PaperProbabilitySideEdgeConfig`
  - `config_version`
  - `min_net_probability_edge`
  - `max_market_context_age_seconds`
  - `max_settlement_context_age_seconds`
  - `min_liquidity_score`
  - `finalization_buffer_seconds`
- `PaperProbabilitySideEdgeRow`
  - `market_slug`
  - `question`
  - `side`
  - `forecast_probability`
  - `side_probability`
  - `side_price`
  - `fee_cost`
  - `spread_cost`
  - `slippage_cost`
  - `funding_cost`
  - `finalization_cost`
  - `time_cost`
  - `risk_cost`
  - `capital_cost`
  - `total_cost_per_share`
  - `gross_probability_edge`
  - `net_probability_edge`
  - `liquidity_score`
  - `market_context_age_seconds`
  - `settlement_context_age_seconds`
  - `finalization_buffer_seconds`
  - `settlement_status`
  - `action`
  - `recommendation_score`
  - `reason_codes`
  - `paper_only`
  - `report_only`
  - `readonly`
- `PaperProbabilitySideEdgeReport`
  - `generated_at`
  - `config_version`
  - `row_count`
  - `recommend_count`
  - `watch_count`
  - `reject_count`
  - `side_edge_rows`
  - `paper_only`
  - `report_only`
  - `readonly`

Validation requirements:

- `side` is `yes` or `no`.
- `forecast_probability`, `side_probability`, `side_price`, all cost fields,
  edge fields, and score fields are `Decimal`.
- Probability and price fields are in `[0, 1]`.
- Cost fields are nonnegative.
- `side_probability` is canonical for side:
  - YES equals `forecast_probability`.
  - NO equals `1 - forecast_probability`.
- `total_cost_per_share` equals the sum of all cost fields.
- `gross_probability_edge` equals `side_probability - side_price`.
- `net_probability_edge` equals `gross_probability_edge - total_cost_per_share`.
- `recommendation_score` is zero when `net_probability_edge <= 0`.
- All flags are exactly `True`.

- [ ] **Step 3: Implement deterministic action logic**

Action rules:

- `reject` when required price, cost, liquidity, or settlement evidence is
  missing or invalid.
- `watch` when evidence is present but stale, liquidity is below threshold,
  settlement/finalization timing is uncertain, or net edge is below threshold.
- `recommend` only when net edge, liquidity, market context, settlement context,
  finalization buffer, and settlement status all pass configured paper gates.

Ordering:

1. action priority: recommend, watch, reject
2. descending `recommendation_score`
3. descending `net_probability_edge`
4. descending `liquidity_score`
5. ascending `total_cost_per_share`
6. `market_slug`
7. `side`

- [ ] **Step 4: Run focused tests**

Run:

```bash
pytest tests/test_paper_probability_side_edge.py tests/test_strategy_recommendation_layer_scope.py -v
```

Expected after implementation: PASS.

## Task 2: Paper-Only Capital Cost Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_capital_cost.py`
- Create: `tests/test_paper_capital_cost.py`
- Modify: `tests/test_strategy_recommendation_layer_scope.py`

- [ ] **Step 1: Write failing capital-cost tests**

Cover paper-only cost of tying up notional until exit, settlement, or
finalization. The reducer should not read balances or NAV from an account. It
receives paper inputs explicitly.

Required test cases:

- `paper_notional * annual_capital_cost_rate * days_locked / 365` produces the
  expected Decimal cost.
- Cost per share divides total paper capital cost by paper share quantity.
- Zero days locked produces zero cost.
- Negative rates, negative notional, negative share quantity, or negative days
  are rejected.
- Output rows preserve `paper_only`, `report_only`, and `readonly` flags.

Run:

```bash
pytest tests/test_paper_capital_cost.py -v
```

Expected before implementation: FAIL because the module does not exist.

- [ ] **Step 2: Implement capital-cost dataclasses**

Create:

- `PaperCapitalCostConfig`
  - `config_version`
  - `annual_capital_cost_rate`
  - `max_days_locked`
- `PaperCapitalCostRow`
  - `market_slug`
  - `side`
  - `paper_notional`
  - `paper_share_quantity`
  - `days_locked`
  - `annual_capital_cost_rate`
  - `paper_capital_cost`
  - `paper_capital_cost_per_share`
  - `reason_codes`
  - `paper_only`
  - `report_only`
  - `readonly`
- `PaperCapitalCostReport`
  - `generated_at`
  - `config_version`
  - `row_count`
  - `total_paper_notional`
  - `total_paper_capital_cost`
  - `capital_cost_rows`
  - `paper_only`
  - `report_only`
  - `readonly`

All math must use `Decimal`. Treat this as a paper accounting estimate, not
portfolio state.

- [ ] **Step 3: Run focused tests**

Run:

```bash
pytest tests/test_paper_capital_cost.py tests/test_strategy_recommendation_layer_scope.py -v
```

Expected after implementation: PASS.

## Task 3: Paper Recommendation Queue

**Files:**
- Create: `src/polymarket_alpha_lab/paper_recommendation_queue.py`
- Create: `tests/test_paper_recommendation_queue.py`
- Modify: `tests/test_strategy_recommendation_layer_scope.py`

- [ ] **Step 1: Write failing queue tests**

The queue is a report that decides which paper recommendations should be
reviewed first. It is not an execution queue.

Required test cases:

- Recommended rows are admitted in deterministic priority order.
- Rows beyond `max_queue_size` are marked `deferred`.
- Rows with stale market context, stale settlement context, missing liquidity,
  negative net edge, or blocked readiness are marked `blocked`.
- Queue rows include selected side, net edge, liquidity score, settlement
  status, and queue reason codes.
- Queue report has hard `paper_only`, `report_only`, and `readonly` flags.

Run:

```bash
pytest tests/test_paper_recommendation_queue.py -v
```

Expected before implementation: FAIL because the module does not exist.

- [ ] **Step 2: Implement queue dataclasses**

Create:

- `PaperRecommendationQueueConfig`
  - `config_version`
  - `max_queue_size`
  - `min_net_probability_edge`
  - `min_liquidity_score`
- `PaperRecommendationQueueRow`
  - `market_slug`
  - `side`
  - `source_action`
  - `queue_status`
  - `queue_rank`
  - `recommendation_score`
  - `net_probability_edge`
  - `liquidity_score`
  - `settlement_status`
  - `reason_codes`
  - `paper_only`
  - `report_only`
  - `readonly`
- `PaperRecommendationQueueReport`
  - `generated_at`
  - `config_version`
  - `row_count`
  - `queued_count`
  - `deferred_count`
  - `blocked_count`
  - `queue_rows`
  - `paper_only`
  - `report_only`
  - `readonly`

Allowed `queue_status` values:

- `queued`
- `deferred`
- `blocked`

Preserve source reason codes and append queue-specific reason codes such as
`queue_capacity_reached`, `queue_stale_market_context`,
`queue_liquidity_below_threshold`, `queue_settlement_context_stale`, and
`queue_net_edge_below_threshold`.

- [ ] **Step 3: Run focused tests**

Run:

```bash
pytest tests/test_paper_recommendation_queue.py tests/test_strategy_recommendation_layer_scope.py -v
```

Expected after implementation: PASS.

## Task 4: Risk Budget and Paper Sizing Allocation

**Files:**
- Create: `src/polymarket_alpha_lab/paper_recommendation_risk_budget.py`
- Create: `tests/test_paper_recommendation_risk_budget.py`
- Modify: `tests/test_strategy_recommendation_layer_scope.py`

- [ ] **Step 1: Write failing risk-budget tests**

Required test cases:

- Per-selection notional cap limits a high-score row.
- Per-market cap applies across YES and NO rows for the same market.
- Event/theme cap limits correlated outcomes.
- Cycle-level cap stops additional paper allocations.
- Negative-edge, blocked, stale, or liquidity-failed rows receive zero paper
  notional.
- Budget rows explain each cap through canonical reason codes.

Run:

```bash
pytest tests/test_paper_recommendation_risk_budget.py -v
```

Expected before implementation: FAIL because the module does not exist.

- [ ] **Step 2: Implement risk-budget dataclasses**

Create:

- `PaperRecommendationRiskBudgetConfig`
  - `config_version`
  - `max_selection_notional`
  - `max_market_notional`
  - `max_event_theme_notional`
  - `max_cycle_notional`
  - `min_net_probability_edge`
  - `score_to_notional_scale`
- `PaperRecommendationRiskBudgetRow`
  - `market_slug`
  - `event_theme`
  - `side`
  - `queue_status`
  - `recommendation_score`
  - `net_probability_edge`
  - `requested_paper_notional`
  - `allocated_paper_notional`
  - `cap_status`
  - `reason_codes`
  - `paper_only`
  - `report_only`
  - `readonly`
- `PaperRecommendationRiskBudgetReport`
  - `generated_at`
  - `config_version`
  - `row_count`
  - `allocated_count`
  - `zero_allocated_count`
  - `total_requested_paper_notional`
  - `total_allocated_paper_notional`
  - `risk_budget_rows`
  - `paper_only`
  - `report_only`
  - `readonly`

Allowed `cap_status` values:

- `allocated`
- `reduced`
- `zero`

No row may represent a real order size. Field names must say `paper` where
notional could be confused with execution.

- [ ] **Step 3: Run focused tests**

Run:

```bash
pytest tests/test_paper_recommendation_risk_budget.py tests/test_strategy_recommendation_layer_scope.py -v
```

Expected after implementation: PASS.

## Task 5: Reason-Code Trend Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_recommendation_reason_trend.py`
- Create: `tests/test_paper_recommendation_reason_trend.py`

- [ ] **Step 1: Write failing trend tests**

The trend reducer summarizes why recommendations change across paper runs. It
consumes recovered local paper reports only.

Required test cases:

- Counts top reason codes across runs.
- Separates recommend, watch, reject, queued, deferred, blocked, allocated, and
  zero-allocation reason counts when source reports provide those statuses.
- Tracks market/side transitions such as watch-to-recommend,
  recommend-to-watch, recommend-to-reject, queued-to-blocked, and
  allocated-to-zero.
- Emits deterministic ordering by descending count and then canonical reason
  code.
- Rejects free-form noncanonical reason strings.

Run:

```bash
pytest tests/test_paper_recommendation_reason_trend.py -v
```

Expected before implementation: FAIL because the module does not exist.

- [ ] **Step 2: Implement trend dataclasses**

Create:

- `PaperRecommendationReasonTrendConfig`
  - `config_version`
  - `window_size`
- `PaperRecommendationReasonTrendRow`
  - `reason_code`
  - `source_status`
  - `count`
  - `first_seen_at`
  - `latest_seen_at`
  - `paper_only`
  - `report_only`
  - `readonly`
- `PaperRecommendationTransitionTrendRow`
  - `market_slug`
  - `side`
  - `from_status`
  - `to_status`
  - `transition_count`
  - `latest_transition_at`
  - `reason_codes`
  - `paper_only`
  - `report_only`
  - `readonly`
- `PaperRecommendationReasonTrendReport`
  - `generated_at`
  - `config_version`
  - `source_report_count`
  - `reason_trend_rows`
  - `transition_trend_rows`
  - `paper_only`
  - `report_only`
  - `readonly`

Use canonical reason-code strings as grouping keys. Explanation text may remain
a display-only layer and must not become the grouping key.

- [ ] **Step 3: Run focused tests**

Run:

```bash
pytest tests/test_paper_recommendation_reason_trend.py -v
```

Expected after implementation: PASS.

## Task 6: CLI Report-Only Workflow

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `docs/strategy-recommendation-layer.md`

- [ ] **Step 1: Write failing CLI tests**

Add CLI tests for local-file, report-only commands. The commands must read
supplied paper artifacts and print summaries. They must not build clients,
fetch live data, authenticate, sign, construct order payloads, submit orders, or
cancel orders.

Recommended commands:

```bash
polymarket-alpha-lab paper-probability-side-edge-report --input <path>
polymarket-alpha-lab paper-recommendation-queue-report --input <path>
polymarket-alpha-lab paper-recommendation-risk-budget-report --input <path>
polymarket-alpha-lab paper-recommendation-reason-trend --recommendation-log <path>
```

Expected CLI output should include:

- source report count or row count
- recommend/watch/reject counts where applicable
- queued/deferred/blocked counts where applicable
- allocated and zero-allocation counts where applicable
- top reason codes where applicable
- explicit text that outputs are paper-only/report-only/readonly

Run:

```bash
pytest tests/test_cli.py -k "paper_probability_side_edge or paper_recommendation_queue or paper_recommendation_risk_budget or paper_recommendation_reason_trend" -v
```

Expected before implementation: FAIL because the commands do not exist.

- [ ] **Step 2: Implement CLI commands**

Implement commands using existing CLI style. Commands may parse local paths,
read local JSON or JSONL paper artifacts, build readonly report reducers from
recovered paper rows, and print deterministic summaries.

Commands may not create exchange clients, perform network fetches, load auth
config, load wallet config, load private keys, sign anything, construct real
orders or exchange payloads, submit/cancel/replace orders, or write live-state
artifacts.

- [ ] **Step 3: Update user-facing docs**

Update `docs/strategy-recommendation-layer.md` near the `Next Stage Modules`
section with:

- side-aware YES/NO probability-event logic
- paper capital cost
- queue, risk budget, and reason trend modules
- CLI/report-only workflow
- strict phase boundary

- [ ] **Step 4: Run focused CLI and scope tests**

Run:

```bash
pytest tests/test_cli.py tests/test_strategy_recommendation_layer_scope.py -v
```

Expected after implementation: PASS.

## Multi-Node Parallel Development Plan

The next stage can be split across parallel workers because the modules are pure
reducers with explicit report contracts.

Recommended ownership:

- Node A: `paper_probability_side_edge.py` and its tests.
- Node B: `paper_capital_cost.py` and its tests.
- Node C: `paper_recommendation_queue.py` and its tests.
- Node D: `paper_recommendation_risk_budget.py` and its tests.
- Node E: `paper_recommendation_reason_trend.py` and its tests.
- Node F: CLI/report-only commands and documentation after Nodes A-E define
  stable report shapes.

Coordination rules:

- Every node must use CodeGraph first because this repository is indexed.
- Every node must stay within assigned files unless the coordinator explicitly
  expands ownership.
- Every node must extend the no-live-trading scope test when adding a module or
  CLI command.
- Shared vocabulary must use `paper`, `report`, `readonly`,
  `probability_edge`, `capital_cost`, `queue_status`, `risk_budget`, and
  canonical `reason_codes`.
- No node may add package-root exports unless the project owner explicitly asks
  for that surface.
- No node may introduce live trading, auth, wallet, signing, real order
  construction, submission, cancellation, relayer mutation, or exchange/network
  mutation.

Merge order:

1. Node A side edge reducer.
2. Node B capital cost reducer.
3. Node C queue reducer after Node A row shape is stable.
4. Node D risk budget reducer after queue statuses are stable.
5. Node E reason trend reducer after source status vocabularies are stable.
6. Node F CLI/docs after report schemas are stable.

## Final Verification

Before marking the next stage complete, run:

```bash
pytest tests/test_paper_probability_side_edge.py \
  tests/test_paper_capital_cost.py \
  tests/test_paper_recommendation_queue.py \
  tests/test_paper_recommendation_risk_budget.py \
  tests/test_paper_recommendation_reason_trend.py \
  tests/test_strategy_recommendation_layer_scope.py \
  tests/test_cli.py -v
python -m compileall src tests
git diff --check
codegraph sync
```

Expected final state:

- All focused tests pass.
- Compileall passes.
- Diff check passes.
- CodeGraph sync completes.
- Documentation describes the new modules and CLI workflow.
- The repository still has no live trading/auth/wallet/private-key/signing/order
  construction/submission/cancellation surface in this phase.
