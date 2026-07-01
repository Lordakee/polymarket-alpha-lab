# Team Agent Framework

This document defines the Phase 1 team-agent framework slice for Polymarket Alpha Lab. Phase 1 is paper-only, report-only, and readonly. The framework adds domain teams that can produce forecasts and evidence, while the existing central pipeline remains responsible for Polymarket market context, costs, recommendations, risk, paper allocation, and outcome measurement.

## First Slice Scope

The first implementation slice proves the team architecture with a generic taxonomy, routing, forecast/evidence packet shape, local persistence boundaries, performance gates, and one runnable domain workflow. The data model is intentionally generic enough for all teams, but the runnable workflow in this slice is only `crypto_btc`.

Included in this slice:

- a 10-team medium-granularity taxonomy,
- paper/report/readonly guardrails on team-facing dataclasses and JSON payloads,
- market routing to exactly one primary team with optional secondary teams and route-correction metadata,
- `TeamForecastPacket` and `TeamForecastEvidencePacket` as the domain-team output contract,
- an adapter from a team forecast plus centrally supplied cost values into the existing side-edge input,
- local Supabase/Postgres configuration and persistence surfaces for team profiles, routes, forecasts, forecast evidence, and outcomes,
- sample-count gates for trust and allocation changes,
- a minimal `crypto_btc` supplied-input workflow.

Out of scope for this slice:

- live trading,
- order signing,
- order submission,
- order cancellation,
- order replacement,
- wallet authentication,
- private keys,
- account reads,
- exchange mutation,
- any mutation of a live Polymarket account or order state.

## Team Taxonomy

The medium taxonomy has 10 teams:

| Team ID | Primary Category | Phase 1 Runnable |
| --- | --- | --- |
| `politics` | `politics` | No |
| `crypto_btc` | `finance.crypto.btc` | Yes |
| `crypto_eth` | `finance.crypto.eth` | No |
| `macro_rates` | `finance.macro.rates` | No |
| `equity_indices` | `finance.equity.indices` | No |
| `commodities_gold` | `finance.commodities.gold` | No |
| `commodities_oil` | `finance.commodities.oil` | No |
| `sports_soccer` | `sports.soccer` | No |
| `sports_basketball` | `sports.basketball` | No |
| `sports_other` | `sports.other` | No |

Every team profile is a frozen paper/report/readonly object. The taxonomy is broad enough to accumulate useful settled samples per team while still separating materially different forecasting domains.

## Runnable Workflow

Only `crypto_btc` is runnable in this slice. Other teams can appear in taxonomy, route outputs, profiles, persisted rows, and future-facing interfaces, but they do not have runnable domain forecast workflows yet.

The `crypto_btc` workflow is supplied-input only. It receives already-collected BTC evidence, base probability, question metadata, and configuration, then returns:

- a `TeamForecastPacket` for `crypto_btc`,
- one or more `TeamForecastEvidencePacket` rows,
- paper/report/readonly flags set to `True`,
- Decimal-normalized probabilities and weights,
- reason codes, source references, memory references, and known failure modes.

It does not fetch Polymarket data, place orders, read accounts, authenticate wallets, or allocate capital.

## Central Boundaries

Domain teams only produce forecast and evidence. They do not own execution, recommendation, allocation, market microstructure collection, or outcome scoring.

Central ownership stays as follows:

| Boundary | Owner | Notes |
| --- | --- | --- |
| Polymarket microstructure | Central layer | Reads market context, bid/ask, spread, depth, price movement, and executable paper size. Domain teams consume immutable snapshots or centrally supplied values. |
| Cost-aware edge | Central layer | Computes fees, spread/slippage, funding, finalization, time, risk, capital cost, gross edge, net edge, and executable paper shares. |
| Recommendation | Central layer | Converts team forecasts and cost-aware edge into recommend/watch/reject decisions. |
| Risk | Central layer | Controls paper notional, domain exposure, duplicate market risk, correlation, and drawdown limits. |
| Paper allocation | Central layer | Applies paper-only allocation logic after cost and risk checks. |
| Outcomes | Central layer | Scores resolved forecasts, updates Brier/hit-rate summaries, and feeds gated performance reports. |
| Forecast/evidence | Domain teams | Produces probabilities, confidence, evidence quality, source references, memory references, and known failure modes. |

The interface into the central cost-aware layer is explicit: a team forecast may be adapted with centrally supplied `TeamForecastCostInterfaceInput` into `PaperProbabilitySideEdgeInput`. The cost interface values are inputs from the central layer; a team must not compute or fetch them independently.

## Persistence

All durable team-framework data in this slice uses local Supabase/Postgres only. The expected tables are:

- `team_profiles`,
- `team_market_routes`,
- `team_forecasts`,
- `team_forecast_evidence`,
- `team_forecast_outcomes`.

The persistence boundary is local by design. Raw DSNs must be validated through the local Postgres DSN validator before psycopg connection setup. The team framework does not introduce SQLite, Redis, MongoDB, hosted database assumptions, or SQLAlchemy persistence.

Durable JSON payloads must be JSON-ready without floats. Decimal values are serialized as strings, safety flags remain explicit, and unsafe live-surface field names are rejected before persistence.

## Sample-Count Gates

Performance summaries are informative at low sample counts, but trust and allocation effects stay neutral until enough settled observations exist.

The Phase 1 gate model is:

- trust adjustment remains neutral until the configured minimum settled sample count is reached,
- allocation multiplier remains neutral until its configured minimum settled sample count is reached,
- insufficient-sample reason codes are included when a team has not reached the gate,
- lessons and performance signals from too few resolved forecasts must not be promoted into active team trust,
- routing corrections must protect calibration so misrouted markets do not silently contaminate a team's record.

The initial plan uses hard minimums for trust and allocation gates. Until those gates pass, team history can be reported, inspected, and persisted, but it must not create non-neutral trust or allocation behavior.

## Phase 1 Operating Rules

Phase 1 remains paper-only, report-only, and readonly. A valid team artifact must carry `paper_only=True`, `report_only=True`, and `readonly=True`.

The framework has no live trading path. It has no order path, no auth path, no wallet path, no private-key path, no account-read path, and no exchange-mutation path. Any future expansion beyond paper reporting must be designed as a separate phase; it is not part of this slice.

The intended operating flow for this slice is:

```text
market metadata
  -> central/router team assignment
  -> crypto_btc supplied-input forecast workflow when primary team is crypto_btc
  -> TeamForecastPacket + TeamForecastEvidencePacket
  -> central microstructure and cost-aware edge layer
  -> central recommendation, risk, and paper allocation
  -> local Supabase persistence
  -> central outcome and gated performance summary
```

For all non-`crypto_btc` teams in this slice, the flow stops at taxonomy, routing, persistence-ready interfaces, or future-facing reports. They are not runnable domain teams yet.
