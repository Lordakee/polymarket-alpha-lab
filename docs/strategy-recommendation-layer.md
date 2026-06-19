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
plus the latest bundle's selected count and selected notional. It does not
construct clients, fetch data, execute paper trades, append logs, or write
artifacts.

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
