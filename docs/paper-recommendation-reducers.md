# Paper Recommendation Reducers

This page summarizes the paper recommendation reducers in the current stage.
They are paper-only, report-only, readonly reducers over supplied local inputs.
They do not fetch live markets, authenticate accounts, read wallets or private
keys, sign payloads, build exchange orders, place orders, cancel orders, or
mutate exchange, relayer, client, wallet, account, or network state.

Each reducer should be treated as deterministic report infrastructure. A score,
rank, queue row, gate pass, readiness state, research packet row, allocation, or
shadow NAV impact is a paper journal artifact only. It is not a live trading
instruction, order ticket, order intent, approval, or wallet action.

## Shared Contract

All reducer families in this stage follow the same boundary:

- Inputs are caller-supplied dataclass rows, report rows, or report-shaped local
  objects.
- Outputs are frozen paper reports with hard `paper_only=True`,
  `report_only=True`, and `readonly=True` flags.
- Calculations are Decimal-oriented and deterministic, with stable sorting,
  explicit counts, status fields, and canonical reason codes.
- Reducers may summarize, gate, rank, group, allocate paper notional, or prepare
  research-review artifacts, but they never open a live execution path.

## CLI and Planning Status

The following reducer commands are available CLI surfaces. They read local
paper artifacts, build paper-only/report-only/readonly reports, and print
deterministic summaries:

| Command | Status | Persistence |
| --- | --- | --- |
| `paper-probability-side-edge-report --input <path>` | Available CLI | Print-only local report command; no `--persist` flag. |
| `paper-recommendation-queue-report --input <path> [--persist]` | Available CLI | Optional default-off, env-driven, local Supabase/Postgres report-only DB persistence. |
| `paper-recommendation-risk-budget-report --input <path> [--nav-notional <amount>] [--persist]` | Available CLI | Optional default-off, env-driven, local Supabase/Postgres report-only DB persistence. |
| `paper-recommendation-reason-trend --recommendation-log <path> [--persist]` | Available CLI | Optional default-off, env-driven, local Supabase/Postgres report-only DB persistence. |

`--persist` is local report-only DB persistence, not live trading. It does not
create live clients, read accounts, read wallets, sign payloads, submit orders,
approve trades, or mutate exchange state. The persist-capable commands read
their matching `POLYMARKET_ALPHA_LAB_*_DB_*` environment configuration only
when `--persist` is passed; there are no DSN/table CLI flags.

`paper_capital_cost` is an available module-local reducer for explicit paper
capital-cost estimates and has no standalone CLI in this phase.
`paper_capital_cost_side_edge_adapter` is an available module-local adapter that
converts capital-cost-aware rows into canonical side-edge inputs with computed
`capital_cost_per_share`; it has no standalone CLI in this phase. Planned-only
reducer families remain planning names until a source module and tests exist:

- `paper_recommendation_queue` is a planned-only generic readonly review queue;
  the available queue CLI uses `paper_probability_recommendation_queue`.

## Reducer Families

| Family | Purpose |
| --- | --- |
| Probability side edge | Available reducer and available CLI surface for side-aware YES/NO probability-event edge rows. |
| Side-edge adapter | Converts supplied strategy-like side rows into canonical YES/NO probability side-edge inputs, preserving costs, freshness flags, executable depth, and reason codes before delegating to the side-edge reducer. |
| Side-edge queue | Ranks canonical side-edge rows into a bounded research-review queue. It separates research review, await-fresh-context, skip, and excluded rows; it is a review queue, not an execution queue. |
| Capital cost | Available module-local reducer family for explicit local paper carrying-cost estimates; no standalone CLI in this phase. |
| Capital-cost side-edge adapter | Available module-local adapter that converts capital-cost-aware rows into canonical side-edge inputs with computed `capital_cost_per_share`; no standalone CLI in this phase. |
| Cost stress | Applies supplied per-share cost-shock scenarios to side-edge candidates and reports whether net probability edge still survives as `pass`, `watch`, or `fail`. |
| Allocation | Assigns paper notional and paper shares under local paper caps: total budget, per-market cap, event cap, theme cap, and correlation-group cap. Zero or reduced allocation is still only paper sizing. |
| Risk budget | Available reducer and available CLI surface for local paper allocation caps and budget status. |
| Liquidity/depth gate | Checks requested paper shares against executable paper shares, max executable depth, fill ratio, and spread cost. It emits pass/watch/blocked liquidity status and liquidity cost. |
| Settlement timing | Scores supplied resolution timing and settlement-context freshness. It applies timing penalties, blocks unknown/overdue/excessive horizon cases, and emits adjusted net edge. |
| Outcome uncertainty | Scores supplied ambiguity and resolution-source evidence. It applies ambiguity and missing-source penalties and marks outcome definitions as clear, watch, or blocked. |
| Calibration gate | Joins supplied recommendation rows with supplied forecaster calibration metrics, applies sample/Brier/status thresholds, and emits pass/watch/blocked calibration rows plus adjusted net edge. |
| Correlation grouping | Groups supplied recommendations by event, theme, and correlation group. It reports group counts, requested notional, pass/watch/blocked cap status, and group-level reason codes before allocation. |
| Shadow NAV | Reduces supplied paper allocation rows into shadow NAV impact: allocated notional, max loss, expected value, NAV-at-risk ratio, expected drawdown ratio, and pass/watch/blocked status. |
| Gate summary | Aggregates supplied gate rows by gate name, summarizing pass/watch/blocked counts, total gate cost, primary status, and reason-code counts. |
| Readiness | Combines supplied gate rows per market side into ready/watch/blocked readiness rows. It uses blocked-gate count, watch-gate count, minimum adjusted edge, and total gate cost. |
| Research packet | Builds ranked analyst packet rows from supplied recommendation/queue rows. It assigns high/medium/low/skip priority and required checks such as outcome definition, liquidity/depth, cost sensitivity, and settlement timing. |
| Thresholds | Applies explicit recommendation thresholds for minimum net probability edge, minimum score, minimum executable paper shares, and maximum total cost per share. |
| Health | Summarizes supplied recommendation rows into report health: action counts, average edge, average cost, top score, reason-code counts, and pass/watch/blocked health status. |
| Manifest | Summarizes the set of supplied recommendation reports. It checks required report names, item counts, pass/watch/blocked status, missing reports, and manifest-level reason codes. |
| Consistency | Compares supplied recommendation facts for the same market side across sources. It watches missing/disagreeing sources and blocks excessive edge or score spread across reducers. |
| Generic recommendation queue | Planned-only reducer family for a future generic readonly review queue. |
| Reason trend | Available reducer and available CLI surface for canonical reason-code counts and status-transition trends over recovered local recommendation reports. |

## Suggested Pipeline

The recommended local pipeline is:

```text
market snapshot + forecast probability
-> supplied side rows with executable side price, costs, depth, freshness, and
   settlement inputs
-> side-edge adapter
-> canonical side-edge report
-> thresholds
-> liquidity/depth gate
-> settlement timing
-> outcome uncertainty
-> calibration gate
-> cost stress
-> gate summary
-> readiness
-> side-edge queue
-> correlation grouping
-> paper allocation
-> shadow NAV
-> consistency
-> health
-> manifest
-> research packet
```

Allocation can also be run immediately after readiness when the caller wants a
paper sizing view before research packet assembly:

```text
readiness
-> side-edge queue
-> correlation grouping
-> paper allocation
-> shadow NAV
-> research packet
```

Use the first order when the goal is a complete audit bundle. Use the shorter
order when the goal is to review paper sizing and then package the selected
rows for analyst research. In both cases, every step consumes already-supplied
paper inputs or prior paper reports and emits only readonly report artifacts.
