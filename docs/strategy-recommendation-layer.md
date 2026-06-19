# Strategy Recommendation Layer

This page documents the paper-only recommendation layer that sits after market
scanning, forecasting, cost-aware strategy checks, candidate assessment, and
readiness gates. It is selection and reporting infrastructure only. It does not
execute live trades, authenticate accounts, use wallets or private keys, call
relayers, place real orders, or cancel real orders.

## Why Polymarket Is Different

Polymarket markets are binary outcome contracts, not normal price-investing
assets. A Yes share pays out if the event resolves Yes, and a No share pays out
if the event resolves No. A market price can therefore be read as an implied
probability, subject to market microstructure and costs.

The relevant signal is not "cheap" or "expensive" in the equity sense. The
basic paper edge is forecast-vs-price after costs:

- forecast probability from the model or analyst input
- executable market price as the current implied probability
- cost assumptions for fees and execution friction
- net edge after taker fee, spread, slippage, funding, finalization, time, and
  risk cost assumptions

All numeric calculations in this layer should stay Decimal-only, matching the
rest of the project.

## Current Boundary

The recommendation layer is paper-only, report-only, and readonly. Its job is to
rank, select, and explain candidates for a paper journal. It may produce
recommendation reports, paper selection decisions, and deterministic
explanations, but those reports are not order instructions. Selection policy
output is a paper sizing suggestion only. It is not an exchange order, order
ticket, order intent, or approval to place an order.

Package-root exports are not part of this surface. Import any layer API directly
from the module that defines it.

## Data Flow

The intended flow is:

```text
scan
-> forecast
-> cost-aware snapshot
-> candidate assessment
-> readiness gates
-> recommendation bundle
   -> recommendation ranking
   -> paper selection policy
   -> deterministic explanation report
-> append-only JSONL recommendation log
-> readonly recommendation history
-> strategy_cycle/runner integration later
```

The recommendation layer consumes prior paper reports. Assessment and readiness
reports remain the gate into the recommendation bundle. The bundle combines the
candidate recommendation report, the paper selection policy report, and the
deterministic explanation report for the same generated-at cycle. The JSONL log
then records bundle reports as append-only paper history. Existing
recommendation history summaries are built from the `recommendation_report`
inside each recovered bundle entry.

Later `strategy_cycle` and `runner` integration should call this bundle/log
stage after assessment and readiness reports are available. That later
integration is still report generation and paper journaling; it should not fetch
live market data or mutate external state by itself.

## Cost-Aware Recommendation

Recommendation must be cost-aware because a positive probability gap can vanish
after transaction and timing costs. The existing cost-aware strategy report
models the important paper inputs:

- taker fee, including the Polymarket-style price-dependent fee calculation
- spread, because the displayed midpoint is not the executable price
- slippage cost placeholder
- funding cost placeholder
- finalization cost placeholder
- time cost placeholder
- risk cost placeholder
- total cost per share and net edge per share

The recommendation score should therefore use net edge and readiness evidence,
not gross forecast error alone. A candidate with a higher raw forecast gap but
poor spread, weak liquidity, stale settlement context, or high risk cost can be
less attractive than a smaller but cleaner edge.

## Next-Stage Recommendation Loop

The next stage should turn the current bundle/log/history pieces into a
repeatable paper recommendation loop for probability markets. The loop is still
paper-only and report-only:

```text
event probability input
-> executable side price and cost assumptions
-> side-level probability edge
-> cost-aware candidate selection
-> paper-only sizing suggestion
-> reason-code and history trend summaries
-> readiness gates
-> append-only recommendation bundle log
-> readonly history review
```

The loop should score Yes and No as separate probability positions, because the
same event can have asymmetric price, liquidity, and cost evidence on each side.
For each candidate side:

- `forecast_probability` is the paper fair probability for Yes.
- `side_probability` is `forecast_probability` for Yes and
  `1 - forecast_probability` for No.
- `side_price` is the executable ask or conservative executable entry price for
  the side, not an optimistic midpoint.
- `gross_probability_edge` is `side_probability - side_price`.
- `total_cost_per_share` is the Decimal-only sum of fee, spread, slippage,
  funding, finalization, time, and risk costs assigned to that side.
- `net_probability_edge` is `gross_probability_edge - total_cost_per_share`.
- `recommendation_score` should be derived from positive net edge plus
  readiness quality. It must not reward a side whose cost-adjusted edge is zero
  or negative.

Selection should rank by cost-aware score first, then use deterministic
tiebreakers such as stronger readiness status, lower total cost, fresher market
context, higher liquidity confidence, and stable market slug ordering. The
ranking report should preserve rejected and watched rows so later reviewers can
see whether high raw-edge ideas were filtered by costs, readiness, or
insufficient evidence.

## Paper-Only Sizing

Sizing in this layer is a journal suggestion only. It exists to make paper
history comparable across runs and should never be represented as an order
instruction. Suggested notional should be capped by local paper policy:

- per-selection notional cap
- per-market cap across both sides
- event or theme exposure cap for correlated outcomes
- daily or cycle-level total selected notional cap
- minimum positive net-edge threshold after all costs
- optional score-to-size scale that increases size only after readiness passes
- zero size for blocked, rejected, negative-edge, stale, or missing-liquidity
  rows

All size math should remain Decimal-only and quantized consistently with the
existing reports. The selection policy should emit the selected side, selected
notional, selected share quantity when available, cap reason codes, and a clear
paper-only/report-only/readonly flag set. If a selected side later becomes
stale, blocked, or cost-negative in a later cycle, the loop should record a new
paper recommendation state rather than editing prior history.

## History and Reason Trends

Recommendation history should summarize both volume and decision quality over
time. The current history reducer can remain the base, but the next trend layer
should add readonly metrics that explain why the loop is changing:

- recommendation, watch, reject, and selected counts by run
- selected notional and average selected notional by run
- average, minimum, and maximum recommendation score
- average gross probability edge, total cost, and net probability edge for
  recommended rows
- reason-code concentration, including top blocking reasons and cost reasons
- transition counts for the same market and side, such as watch-to-recommend,
  recommend-to-watch, and recommend-to-reject
- readiness status trend, including pass, warn, and blocked counts
- stale-input, liquidity, cost-drag, exposure-cap, and threshold-failure rates
- latest-run deltas against the prior run and rolling windows

Reason-code trend rows should be deterministic and stable for review. Use
canonical reason code strings, preserve source config versions, and avoid
free-form text as the grouping key. Explanation text can remain a deterministic
view over action, side, score, and primary reason code.

## Readiness Gates for the Loop

The recommendation loop should be gated before selection and again before
history promotion. A candidate can be recommended only when all required paper
evidence is fresh enough and internally consistent. Readiness should include:

- forecast calibration evidence exists for the relevant event class or segment
- executable side price, spread, and fee assumptions are present
- liquidity evidence supports the suggested paper share quantity
- market context and settlement context are fresh for the cycle timestamp
- exposure caps leave room for the suggested paper notional
- cost sensitivity does not flip the net edge negative under configured stress
- prior history does not show repeated reason-code failures for the same market
  or side
- append-only log recovery succeeds before any new summary is trusted

Gate output should be explicit: `pass` allows paper selection, `warn` allows
watch rows or reduced paper size, and `blocked` forces watch or reject with zero
selected notional. These gates are evidence gates for paper recommendations
only; they are not execution readiness gates for live orders.

## Phase Boundary

This stage ends at append-only paper bundle history and readonly trend reports.
There is no live trading layer in this phase. No module in the recommendation
loop should add account authentication, wallet access, signing, order request
construction, order submission, order cancellation, relayer mutation, private
state reads, or exchange-state mutation. Any future phase that considers those
surfaces must be documented separately and cannot be inferred from a
recommendation, selected side, selected notional, readiness pass, or history
trend.

## Bundle and Log Stage

The recommendation bundle is the cycle-level handoff object for paper review.
It should contain:

- the candidate recommendation report produced from assessment/readiness inputs
- the paper selection policy report with Decimal-only sizing suggestions
- the deterministic explanation report for the recommendation rows
- hard safety flags showing the bundle is paper-only, report-only, and readonly

The JSONL recommendation log is an append-only record of those bundle reports.
It exists to make recommendation history auditable for paper review and later
cycle summaries. Reading the log should recover prior bundle entries; writing
the log should append paper reports only. To build the existing readonly
recommendation history summary, pass each recovered bundle's
`recommendation_report` to the history reducer.

The CLI exposes this as a read-only slice with:

```bash
polymarket-alpha-lab strategy-recommendation-history --recommendation-log <path>
```

The command reads the supplied bundle log with
`read_paper_strategy_recommendation_bundle_log(...)`, summarizes the nested
`recommendation_report` values with config version
`strategy-recommendation-history-v0`, and prints source recommendation counts
plus the latest bundle's selected count and selected notional. When the history
report or recovered bundle log exposes selection and recommendation-score
metrics, the CLI also prints a selection/score trend summary, such as total
paper selections, total selected notional, first/latest recommendation score,
and latest selected score. It does not construct clients, fetch data, execute
paper trades, append logs, or write artifacts.

Selected rows and selected notional values are paper sizing suggestions for
journal analysis. They are not executable instructions, exchange orders, live
orders, wallet actions, or private-key-backed actions.

## Readiness Before Live Automation

Live automation is out of scope for this project state. Before it could even be
considered, the paper layer would need evidence that the system is reliable
under market-like conditions:

- calibration evidence showing forecasts match realized outcomes over time
- settlement and outcome freshness checks for current market state
- liquidity evidence that selected sides can be entered at realistic prices
- exposure limits across markets, themes, and correlated events
- NAV risk limits and drawdown controls
- an immutable audit trail for inputs, decisions, and paper outcomes
- dry-run history showing stable behavior across full recommendation cycles

These are prerequisites for a future discussion only. They are not permission to
add live execution, auth, wallets, private keys, relayers, or real orders.

## Likely Modules

The recommendation-layer work is expected to use module-level reducers named:

- `strategy_candidate_recommendation` for turning assessed candidates and
  readiness state into ranked paper recommendations
- `paper_strategy_selection_policy` for applying Decimal-only paper sizing caps
  and paper selection decisions
- `strategy_recommendation_explain` for deterministic explanation text and
  reason-code summaries
- `strategy_recommendation_history` for readonly history summaries across
  recommendation report runs
- `strategy_recommendation_bundle` for combining recommendation, paper
  selection, and explanation reports into one paper cycle artifact
- `strategy_recommendation_log` for append-only JSONL persistence and recovery
  of bundle reports

Those modules should preserve the existing reducer style: frozen dataclasses,
validated paper/report/readonly flags, deterministic ordering, Decimal-only
numeric fields, and module-local public APIs. Package-root exports remain out of
scope for recommendation-layer modules; callers should import bundle/log helpers
from their defining modules when they need to append, recover, and inspect paper
artifacts.

## Parallel Development Plan

The next implementation phase can be split across independent nodes with
disjoint ownership:

- Node A, probability-edge scoring: own a new score/edge reducer module and
  focused tests. Define side-level gross edge, cost-adjusted net edge, score
  quantization, and deterministic ranking inputs. Do not edit bundle/log/history
  code.
- Node B, cost-aware paper selection: own the selection policy module and tests.
  Add cap reason codes, zero-size blocking semantics, Decimal-only selected
  notional/share outputs, and deterministic tiebreakers. Do not edit edge trend
  or CLI code.
- Node C, history and reason trends: own a readonly trend reducer and tests over
  recovered recommendation bundles. Add score, edge, cost, readiness, reason,
  transition, and selected-notional summaries. Do not edit selection or scoring
  modules.
- Node D, readiness gate integration: own readiness adapter tests and the
  minimal reducer changes needed to consume calibration, freshness, liquidity,
  cost sensitivity, exposure, and log-recovery signals. Do not edit trend or CLI
  presentation.
- Node E, CLI/report presentation: own CLI tests and documentation for a
  read-only command that prints recommendation-loop trends from a user-supplied
  local log path. The command must only read local files and print summaries.
- Node F, documentation and verification: own docs updates, scope tests, and
  cross-node review notes. Confirm every public report keeps paper-only,
  report-only, and readonly flags and that no execution surface appears.

Nodes should coordinate through typed report contracts rather than shared
mutable state. Each node should keep module-local public APIs, direct imports
from defining modules, deterministic ordering, Decimal arithmetic, and append-only
history semantics.
