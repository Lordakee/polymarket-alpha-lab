# Strategy Recommendation Layer

This page documents the paper-only recommendation layer that sits after market
scanning, forecasting, cost-aware strategy checks, candidate assessment, and
readiness gates. It is selection and reporting infrastructure only. It does not
execute live trades, authenticate accounts, use wallets or private keys, call
relayers, place real orders, cancel real orders, inspect accounts, or deploy
capital.

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
ticket, order intent, or approval to place an order. The current phase boundary
is paper-only/report-only/read-only: no live trading, authentication, wallet or
private-key access, signing, order construction, order submission, order
cancellation, account mutation, account reads, relayer mutation, or exchange/network
mutation.

Package-root exports are not part of this surface. Import any layer API directly
from the module that defines it.

## Data Flow

The intended flow is:

```text
strategy cycle
-> rich paper recommendation artifacts
-> cycle snapshot
-> Supabase/Postgres persistence
-> DB-backed cycle review
-> paper cycle action gate
-> action-gated candidate research/recommendation queue reducer
-> candidate research/recommendation queue review
```

The strategy cycle consumes prior paper reports and exposes already-built local
evidence, including cost-aware reports and screening/readiness summaries. That
evidence can be converted into rich paper recommendation artifacts:
recommendation ranking, paper selection policy, deterministic explanation,
side-edge, queue, allocation, research, manifest, consistency, health, and
bundle reports. Assessment and readiness reports remain the gate into those
artifacts.

The artifact index and pipeline report normalize the heterogeneous artifact set
for one generated-at cycle. The cycle snapshot combines that index and pipeline
rollup into a stable `pass`/`watch`/`blocked` paper cycle result. Local
Supabase/Postgres persistence stores validated snapshots for durable report
history and later read-only review. Documentation should mention this
persistence only at a high level and should never include real DSNs, passwords,
tokens, service keys, wallet material, or other secrets.

The DB-backed cycle review reads persisted snapshot history and produces
concise observability summaries: latest status, pass/watch/blocked counts,
blocked or watch artifact pressure, missing required artifacts, stale-history
state, and reason-code counts. It is not live approval, not an execution
workflow, not order management, not account inspection, not wallet/private-key
access, and not capital deployment.

The paper cycle action gate consumes the DB-backed review report and converts
review status plus evidence pressure into one of three paper next steps only:

- `build_candidate_research_queue` when the cycle review passes and required
  evidence is present and fresh enough to build a candidate
  research/recommendation queue;
- `await_fresh_cycle_evidence` when the review is watch or cycle evidence is
  stale enough that the paper layer should wait for a fresher persisted cycle;
- `repair_cycle_evidence` when the review is blocked or required cycle evidence
  is missing, malformed, or blocked.

The gate's `build_candidate_research_queue` result means "paper research queue
construction may proceed." It does not approve a live trade, create order
intent, manage orders, inspect accounts, read wallets or private keys, sign
payloads, or deploy capital. A candidate research/recommendation queue remains a
paper-only/report-only/readonly review queue.

The action-gated candidate research/recommendation queue reducer is the only
handoff from the paper cycle action gate into downstream candidate assessment,
strategy bundle, and strategy queue construction. It may build the downstream
queue only when the gate recommends `build_candidate_research_queue`. Otherwise
it returns a paper-only/report-only/readonly watch or blocked artifact copied
from the gate evidence, and it does not repair missing, stale, malformed, or
blocked cycle data itself.

Action-gated queue reports can also be persisted as local Supabase/Postgres
audit artifacts. That persistence path stores the exact paper queue report plus
denormalized status/count fields for readonly review, replay, and later
automation research. The reducer remains DB-free, and persistence stays at the
process boundary behind default-off environment configuration. Persisted
`research_ready`, `watch`, and `blocked` rows are evidence records only; they
are not live trade approvals, order intents, signed payloads, account reads,
wallet interactions, or exchange mutations.

Runtime action-gated queue persistence is opt-in and env-driven at the CLI
process boundary. When enabled, it runs only after a paper cycle completes and
persists the resulting queue report as an audit artifact. A persisted queue row
does not approve trading, elevate a paper recommendation into an order, or
authorize any live execution step.

Decision-support modules over action-gated queue reports remain module-local
paper-only/report-only/readonly APIs. The priority reducer ranks queue reports
for human research attention, the read adapter loads already-persisted
Supabase/Postgres queue reports for readonly review, and the risk reducer
summarizes ready-notional and candidate-count pressure. These outputs are
evidence and operator-review aids only; they are not package-root exports, live
approvals, order intents, account reads, wallet/private-key access, signing, or
exchange mutations.

DB-backed trend reporting remains separate readonly observability over
persisted cycle state. It can summarize blocker/watch movement across stored
snapshots, aggregate reason-code counts across persisted snapshot history, and
show latest snapshot reason codes from the same snapshot used for latest status,
but it must not become an approval workflow, execution workflow, account review,
or capital-deployment workflow.

JSONL bundle logs may remain as append-only debug/export artifacts for local
paper review, regression fixtures, or portability, but DB-backed snapshot
persistence is the primary normal history surface for cycle-level review and
trend reporting.

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

## Next Stage Modules

The next stage should split the paper recommendation loop into small reducer
modules that can be developed in parallel. Each module consumes local paper
inputs or prior paper reports, emits deterministic report rows, and keeps hard
`paper_only`, `report_only`, and `readonly` flags.

Reducer modules for this stage are:

- `paper_probability_side_edge` for side-level YES/NO probability edge rows.
- `paper_capital_cost` for explicit paper capital carrying-cost estimates.
- `paper_side_edge_adapter` for converting supplied strategy/economics rows into
  canonical side-edge inputs.
- `paper_probability_recommendation_queue` for side-edge review/research queue
  status reports.
- `paper_cost_stress` for checking whether recommendations survive extra cost
  shocks.
- `paper_liquidity_depth_gate` for supplied depth/fill-ratio gates.
- `paper_settlement_timing` for time-to-resolution and settlement freshness
  penalties.
- `paper_outcome_uncertainty` for ambiguous outcome-definition penalties.
- `paper_recommendation_calibration_gate` for supplied forecaster calibration
  gates.
- `paper_recommendation_thresholds` for edge, score, depth, and cost threshold
  checks.
- `paper_recommendation_allocation` for row-level paper notional allocation.
- `paper_correlation_grouping` for event/theme/correlation exposure summaries.
- `paper_recommendation_risk_budget` for local paper allocation caps.
- `paper_recommendation_shadow_nav` for paper NAV-at-risk summaries.
- `paper_recommendation_gate_summary` for cross-gate status summaries.
- `paper_recommendation_readiness` for per-market readiness aggregation.
- `paper_research_packet` for analyst/research review packets.
- `paper_recommendation_health` for batch-level recommendation quality health.
- `paper_recommendation_manifest` for supplied report-presence manifests.
- `paper_recommendation_consistency` for cross-reducer consistency checks.
- `paper_recommendation_queue` for a planned generic readonly review queue.
- `paper_recommendation_reason_trend` for readonly reason-code and transition
  trend summaries.

Those reducer modules are paper-only/report-only/readonly surfaces. They should
not be package-root exports, and Phase 2 modules should not import them. Until a
parallel worker creates a planned module, documentation and boundary tests should
treat its name as planned scope only rather than importing it.

### Probability Side Edge

Probability-event recommendations should be scored at the side level, not only
at the market level. The side edge report should produce one paper row for each
eligible YES or NO side:

- YES side probability is the forecast probability for the event resolving YES.
- NO side probability is `1 - forecast_probability`.
- Side price is the conservative executable entry price for that side, not an
  optimistic midpoint.
- Gross probability edge is `side_probability - side_price`.
- Total cost per share includes fee, spread, slippage, funding, finalization,
  time, risk, and paper capital cost.
- Net probability edge is gross probability edge minus total cost per share.
- Recommendation score can be positive only when net probability edge is
  positive and all required readiness evidence allows selection.

Liquidity and settlement/finalization timing should be first-class inputs. A
candidate side with high raw edge but weak liquidity, stale market context,
stale settlement context, uncertain finalization timing, or high capital lockup
should become watch/reject or rank below a cleaner lower-edge side.

### Paper Capital Cost

Paper sizing should include an explicit capital cost estimate for notional that
would be tied up until exit, settlement, or finalization. This is paper
accounting only. The module should receive paper notional, paper share quantity,
days locked, and an annual paper capital cost rate as inputs; it must not read
balances, NAV, wallets, accounts, or exchange state.

The capital-cost output should include total paper capital cost and per-share
paper capital cost so the side edge reducer can subtract it from gross
probability edge. Zero or negative evidence should never be hidden by sizing;
blocked, stale, missing-liquidity, or cost-negative rows keep zero selected
notional.

### Queue, Risk Budget, and Reason Trends

The queue module is a research/recommendation review queue, not an execution
queue. It should admit ranked paper recommendations under local limits such as
maximum queue size, minimum net edge, liquidity threshold, market-context
freshness, settlement freshness, and finalization buffer. Queue statuses should
be deterministic, for example `queued`, `deferred`, and `blocked`, with reason
codes explaining capacity, stale inputs, liquidity failures, settlement timing,
or net-edge threshold failures.

The risk budget module should allocate paper notional under local caps:

- per-selection notional cap
- per-market cap across YES and NO sides
- event or theme exposure cap for correlated outcomes
- cycle-level total paper notional cap
- minimum net probability edge
- zero allocation for blocked, stale, liquidity-failed, or cost-negative rows

Risk budget rows are paper allocations for journal analysis only. They are not
order sizes, order tickets, exchange intents, or approval to trade.

The reason-trend module should summarize why recommendations change across
paper runs. It should group by canonical reason codes, not free-form
explanation text, and report counts and transitions such as
watch-to-recommend, recommend-to-watch, recommend-to-reject, queued-to-blocked,
and allocated-to-zero. Trend reports should remain readonly summaries over
recovered local paper logs.

### CLI Report Workflow

Any CLI added for these modules should be report-only. Commands may read local
paper artifacts, recover append-only JSONL bundle entries, build readonly
reducers, and print deterministic summaries. Useful commands would print side
edge counts, queue counts, risk-budget allocations, top reason codes, and
latest-run deltas.

CLI commands in this phase must not create live clients, fetch live exchange
state, authenticate, read wallet or private-key material, sign payloads,
construct real order payloads, submit orders, cancel orders, or mutate exchange
or network state.

### Parallel Development Boundaries

The modules can be built by separate workers if their report contracts stay
explicit:

- Node A: `paper_side_edge_adapter` and `paper_probability_side_edge` side-edge
  reports.
- Node B: `paper_cost_stress`, `paper_liquidity_depth_gate`,
  `paper_settlement_timing`, `paper_outcome_uncertainty`,
  `paper_recommendation_calibration_gate`, and
  `paper_recommendation_thresholds` recommendation gates.
- Node C: `paper_probability_recommendation_queue`, `paper_research_packet`,
  `paper_recommendation_manifest`, and `paper_recommendation_consistency`
  review/research summaries.
- Node D: `paper_recommendation_allocation`, `paper_correlation_grouping`,
  `paper_recommendation_risk_budget`, and `paper_recommendation_shadow_nav`
  paper allocation and risk reports.
- Node E: `paper_recommendation_gate_summary`,
  `paper_recommendation_readiness`, `paper_recommendation_health`, and
  `paper_recommendation_reason_trend` aggregate health/trend reports.
- Node F: CLI/report-only workflow and documentation after report shapes are
  stable.

Each node should use CodeGraph before locating code, stay within assigned file
ownership, extend scope tests for any new module or command, and preserve the
strict phase boundary. No node should add package-root exports, live trading
adapters, auth, wallet access, signing, real order construction, submission,
cancellation, relayer mutation, or exchange/network mutation.

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

After persisted cycle review exists, the paper cycle action gate is the only
cycle-level handoff into candidate research/recommendation queue construction.
It still operates inside the paper-only/report-only/read-only boundary: it maps
review status and evidence pressure to `build_candidate_research_queue`,
`await_fresh_cycle_evidence`, or `repair_cycle_evidence`, and nothing beyond
those paper next steps.

The action-gated queue reducer then converts those next steps into operator
outcomes:

- `research_ready` means review the candidate research/recommendation queue.
- `watch` means await fresh paper-cycle evidence before queue construction.
- `blocked` means repair cycle evidence before queue construction.

## Phase Boundary

This stage ends at append-only paper bundle history and readonly trend reports.
The DB-backed cycle review and paper cycle action gate extend that report-only
chain into persisted cycle observability and paper next-step selection only.
There is no live trading layer in this phase. No module in the recommendation
loop should add live approval, order management, account inspection, account
authentication, wallet access, private-key access, signing, order request
construction, order submission, order cancellation, relayer mutation, capital
deployment, private state reads, or exchange-state mutation. Any future phase
that considers those surfaces must be documented separately and cannot be
inferred from a recommendation, selected side, selected notional, readiness
pass, DB-backed review pass, action-gate `build_candidate_research_queue`
result, or history trend.

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
- `paper_probability_side_edge` for side-aware probability-event scoring
- `paper_capital_cost` for local paper capital carrying-cost reports
- `paper_side_edge_adapter` for canonical supplied-input side-edge conversion
- `paper_probability_recommendation_queue` for readonly side-edge review-queue
  summaries
- `paper_cost_stress`, `paper_liquidity_depth_gate`,
  `paper_settlement_timing`, `paper_outcome_uncertainty`,
  `paper_recommendation_calibration_gate`, and
  `paper_recommendation_thresholds` for paper-only gates
- `paper_recommendation_allocation`, `paper_correlation_grouping`, and
  `paper_recommendation_shadow_nav` for paper allocation and exposure views
- `paper_research_packet`, `paper_recommendation_gate_summary`,
  `paper_recommendation_readiness`, `paper_recommendation_health`,
  `paper_recommendation_manifest`, and `paper_recommendation_consistency` for
  review packets, aggregate readiness, report presence, and consistency checks
- `paper_recommendation_queue` for a planned generic readonly review queue
- `paper_recommendation_risk_budget` for paper allocation caps and budget
  status
- `paper_recommendation_reason_trend` for readonly reason-code and transition
  trend summaries
- `action_gated_strategy_recommendation_queue` for the paper-only reducer that
  requires `build_candidate_research_queue` before building downstream
  candidate assessment, bundle, and strategy queue artifacts
- `action_gated_strategy_recommendation_queue_priority` for readonly
  research-attention ranking across action-gated queue reports
- `action_gated_strategy_recommendation_queue_psycopg_read` for readonly
  loading of already-persisted action-gated queue reports
- `action_gated_strategy_recommendation_queue_risk` for paper-only
  ready-notional and candidate-count risk pressure summaries

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
