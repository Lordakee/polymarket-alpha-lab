# Polymarket Alpha Lab Team-Agent Architecture Review Report

Date: 2026-07-01
Status: planning and external review request
Project boundary: Phase 1 remains paper-only, report-only, readonly.
Claude review status: reviewed with `claude-opus-4-8` at `max` effort; final decision is to adopt the review's hardening changes.

## Objective

The project is moving from a generic Polymarket paper-recommendation pipeline into a domain-specialized research system. The long-term user goal is an automated system that can:

- scan Polymarket markets,
- route each market to the right specialist team,
- research the event with domain-specific evidence,
- produce calibrated probability forecasts,
- calculate cost-adjusted edge,
- recommend paper trades,
- learn from outcomes, and
- eventually support a gated transition toward live-capital design after sufficient paper evidence.

This report proposes a medium-granularity team architecture with long-term team memory. It is intended for Claude Code review before implementation planning.

## Non-Negotiable Constraints

The following constraints are fixed project rules:

- Phase 1 must remain paper-only, report-only, and readonly.
- No live trading, no wallet auth, no private keys, no account reads, no order signing, no order submission, no order cancellation, no order replacement, and no exchange/order mutation.
- All durable data must use local Supabase/Postgres only.
- No SQLite, Redis, MongoDB, hosted database assumption, or SQLAlchemy persistence path.
- Any raw DSN must be validated via `validate_local_postgres_dsn(...)` before psycopg import/connect/wrapper setup.
- Decimal-only arithmetic is required for money, probabilities, scores, costs, and JSON persistence. No floats in durable payloads.
- Dataclass report objects should stay frozen and explicit.
- Existing cost-aware, paper-only pipeline should be reused rather than replaced.
- Teams may research and forecast, but final recommendation, cost calculation, allocation, risk budgeting, and outcome scoring should remain centralized.

## Current System Context

The current project already has these relevant capabilities:

- active market scanning and normalized market snapshots,
- forecast generation,
- cost-aware event strategy reports,
- project screening,
- candidate assessment,
- strategy candidate recommendation,
- paper execution,
- NAV/history/outcome tracking,
- cost and risk audit layers,
- recommendation reducers,
- readiness gates,
- Supabase/Postgres persistence hardening,
- local DSN validation,
- paper-only/live-surface guardrails.

The proposed team architecture should sit above the existing cost-aware and recommendation layers. It should not fork cost calculations inside each team.

## Recommended Architecture

Use a two-level architecture:

1. Domain teams generate probability forecasts and evidence packets.
2. Central layer standardizes cost, edge, allocation, readiness, audit, outcomes, and team performance.

The team layer must not read wallet/account state or call any exchange mutation surface. Team agents receive normalized inputs and produce paper-only forecast packets. Polymarket market-state reads are centralized in the microstructure layer and passed to teams as immutable snapshots.

High-level flow:

```text
Polymarket market scan
  -> Market Router
  -> Team Memory Retrieval
  -> Specialist Domain Team Forecast
  -> Team Forecast Packet
  -> Central Cost & Edge Engine
  -> Central Recommendation and Risk Budget
  -> Paper Execution / Journal / NAV
  -> Outcome Tracking
  -> Team Calibration and Memory Update
```

## Medium-Granularity Teams

The recommended first version has 10 domain teams:

- `politics`
- `crypto_btc`
- `crypto_eth`
- `macro_rates`
- `equity_indices`
- `commodities_gold`
- `commodities_oil`
- `sports_soccer`
- `sports_basketball`
- `sports_other`

This is intentionally more detailed than broad categories, but not so detailed that each category lacks enough observations to learn from.

## Central Layer Agents

The central layer has 8 logical agents:

1. `market_router`
   - Classifies markets into primary and secondary teams.
   - Produces category, event template, routing confidence, and routing reason codes.

2. `global_memory_retrieval`
   - Retrieves similar markets, team historical performance, memory lessons, source reliability, and prior postmortems from local Supabase.

3. `polymarket_microstructure`
   - Reads Polymarket market context, best bid/ask, spread, depth, price movement, and executable paper size.
   - Must remain readonly.
   - Owns all Polymarket market-state reads. Domain teams may interpret the snapshot but must not re-fetch Polymarket order book, market, wallet, account, or execution state.

4. `cost_edge`
   - Computes taker fees, spread/slippage cost, capital/time/risk/finalization cost, gross edge, net edge, and executable paper shares.
   - Uses the existing cost-aware/reducer semantics.

5. `central_recommendation`
   - Converts team forecast packets plus cost-aware edge into recommend/watch/reject.

6. `portfolio_risk_budget`
   - Controls paper notional, team exposure, domain exposure, correlation, duplicate market risk, and drawdown limits.

7. `outcome_calibration`
   - Updates outcomes, Brier score, calibration error, hit rate, cost-adjusted paper returns, and team performance summaries.

8. `audit_red_team`
   - Reviews evidence quality, overconfidence, stale data, team-memory misuse, resolution risk, and Phase 1 boundary compliance.

Fast Phase 1 boundary checks must also run during triage. The full evidence-quality audit can remain a high-priority-market path, but paper-only/readonly/live-surface invariants are not deferred.

## Domain Team Agent Design

Each domain team is a long-lived logical unit with fixed roles, persistent memory, and measurable performance. Runtime should instantiate only the agents required by market priority.

### Politics Team

Agent count: 6.

- `politics_lead_forecaster`: final probability synthesis.
- `polling_fundamentals`: polls, turnout, historical base rates, candidate fundamentals.
- `news_event_shock`: debates, withdrawals, endorsements, legal events, news overreaction.
- `electoral_rules_resolution`: election mechanics, nomination rules, market wording, resolution source risk.
- `political_base_rate_modeler`: historical analogs and structured probability adjustments.
- `politics_memory_postmortem`: retrieves and updates political lessons and failures.

Focus:

- US elections, Congress, state races, nominations, political/legal decisions, major international politics.

Main risks:

- polling bias, small-sample state markets, news overreaction, ambiguous resolution wording.

### Crypto BTC Team

Agent count: 6.

- `btc_lead_forecaster`: final BTC event probability.
- `spot_derivatives`: spot price, futures basis, funding, open interest, liquidation zones.
- `etf_flow`: ETF flow, stablecoin liquidity, exchange flows.
- `volatility_path_modeler`: hit-price and path-dependent probability modeling.
- `btc_market_context`: Polymarket BTC market lag, spread, depth, and dislocation.
- `btc_memory_postmortem`: BTC event lessons and forecast failures.

Focus:

- BTC hit-price, close-price, ETF, dominance, and short-window crypto event markets.

Main risks:

- high volatility, short-window noise, weekend liquidity, hit-price vs close-price confusion.

### Crypto ETH Team

Agent count: 5.

- `eth_lead_forecaster`: final ETH event probability.
- `eth_relative_value`: ETH/BTC, beta, rotation, correlation.
- `etf_staking_ecosystem`: ETF, staking, fees, ecosystem catalysts.
- `eth_volatility_market_context`: path and market context analysis.
- `eth_memory_postmortem`: ETH-specific lessons.

Focus:

- ETH hit-price, close-price, ETF/staking/ecosystem events.

Main risks:

- confusing BTC beta with ETH-specific edge, liquidity differences, event-driven ecosystem noise.

### Macro / Rates Team

Agent count: 6.

- `macro_lead_forecaster`: final macro forecast.
- `economic_calendar`: release schedule, consensus, historical surprise.
- `rates_fed_pricing`: Fed funds, SOFR, bond yields, rate-path pricing.
- `data_surprise_modeler`: CPI/PCE/NFP/GDP distribution and surprise modeling.
- `macro_resolution`: initial vs revised releases, seasonal adjustment, wording and source rules.
- `macro_memory_postmortem`: macro lessons and source reliability.

Focus:

- Fed decisions, inflation, jobs, GDP, rate-path events, macro threshold markets.

Main risks:

- wrong data vintage, market already pricing consensus, release-time context shifts.

### Equity Indices Team

Agent count: 5.

- `index_lead_forecaster`: final index forecast.
- `futures_breadth`: index futures, market breadth, sector rotation.
- `earnings_event_calendar`: earnings season, major index constituents, macro event schedule.
- `index_volatility_path`: intraday touch vs close probability.
- `index_memory_postmortem`: index-market historical lessons.

Focus:

- S&P 500, Nasdaq, Dow, Russell events.

Main risks:

- confusing intraday touch with close conditions, macro event overlap, major constituent concentration.

### Commodities Gold Team

Agent count: 5.

- `gold_lead_forecaster`: final gold forecast.
- `real_rates_usd`: real rates, USD, Treasury yields.
- `inflation_geopolitical`: inflation expectations and safe-haven shocks.
- `gold_volatility_market_context`: spot/futures context and touch probability.
- `gold_memory_postmortem`: gold market lessons.

Focus:

- Gold touch/close markets and related macro/geopolitical commodity events.

Main risks:

- real-rate regime shifts, USD shock, event-driven safe-haven overreaction.

### Commodities Oil Team

Agent count: 5.

- `oil_lead_forecaster`: final oil forecast.
- `supply_opec`: OPEC, production, sanctions, geopolitical supply risk.
- `inventory_demand`: EIA/API inventory, demand, refinery, seasonality.
- `oil_volatility_market_context`: oil price path and Polymarket dislocation.
- `oil_memory_postmortem`: oil and energy market lessons.

Focus:

- Oil, OPEC, inventory, energy-price events. Natural gas can remain here until sample size supports a separate team.

Main risks:

- inventory-release surprise, geopolitical reversals, futures roll/context mismatches.

### Soccer Team

Agent count: 6.

- `soccer_lead_forecaster`: final soccer forecast.
- `team_strength_form`: team strength, ELO, form, attack/defense quality.
- `lineup_injury`: injuries, lineup, suspensions, rotation.
- `odds_consensus`: mature sportsbook consensus vs Polymarket.
- `tournament_rules`: extra time, penalties, advancement and settlement wording.
- `soccer_memory_postmortem`: soccer lessons and failures.

Focus:

- Soccer match outcomes, advancement, tournaments, championships, and initially transfer markets.

Main risks:

- lineup uncertainty, wording ambiguity, mature odds already priced in.

### Basketball Team

Agent count: 6.

- `basketball_lead_forecaster`: final basketball forecast.
- `team_strength_matchup`: team strength, offensive/defensive efficiency, matchup.
- `injury_rotation`: injuries, rest, starters, minutes, player availability.
- `schedule_fatigue`: back-to-back, travel, rest days, schedule density.
- `odds_market_context`: sportsbook consensus and Polymarket dislocation.
- `basketball_memory_postmortem`: basketball lessons and failures.

Focus:

- NBA, NCAA, game outcomes, player-stat events, playoff/championship markets.

Main risks:

- late injuries, rest/rotation changes, line movement after new information.

### Other Sports Team

Agent count: 4.

- `other_sports_lead_forecaster`: final decision and split-candidate detection.
- `sport_specific_scout`: temporary domain-specific data and rules for NFL, MLB, tennis, F1, MMA, golf, etc.
- `odds_market_context`: mature odds comparison and Polymarket dislocation.
- `other_sports_memory_risk`: sub-sport performance tracking and split recommendations.

Focus:

- Sports that do not yet justify a dedicated team.

Main risks:

- heterogeneous rules and data sources, insufficient sample size, category contamination.

## Agent Count Summary

Domain teams:

- Politics: 6
- Crypto BTC: 6
- Crypto ETH: 5
- Macro/Rates: 6
- Equity Indices: 5
- Gold: 5
- Oil/Energy: 5
- Soccer: 6
- Basketball: 6
- Other Sports: 4

Total domain logical agents: 54.

Central layer logical agents: 8.

Total logical roles: 62.

These are logical roles, not a requirement to run 62 child processes concurrently.

## Runtime Priority Levels

To avoid overusing compute and to keep outputs accountable, runtime dispatch should depend on market priority:

```text
Level 1: quick triage
  - market_router
  - relevant team lead
  - team memory/postmortem
  - polymarket_microstructure

Level 2: research-ready/watch market
  - full primary team
  - global_memory_retrieval
  - cost_edge
  - central_recommendation

Level 3: high-edge/high-notional candidate
  - full primary team
  - targeted secondary team
  - central recommendation
  - portfolio risk budget
  - audit/red-team
```

This design supports high concurrency, but avoids treating every market as equally important.

## Long-Term Team Memory

Each team must have persistent memory. Without it, domain teams would only be labels over the same stateless research process.

Required memory layers:

1. Forecast ledger
   - immutable record of each team forecast, market state, probability, confidence, evidence, and config version.

2. Outcome feedback
   - actual outcome, settlement source, Brier score, log loss, paper PnL, cost-adjusted return, resolution errors.

3. Team lessons
   - supported generalizations from repeated wins/failures, with sample count, category scope, and confidence.

4. Source reliability
   - source coverage, latency, historical accuracy, known bias, and failure count by team/category.

5. Calibration and performance summaries
   - rolling team/category Brier score, calibration error, paper PnL, drawdown, hit rate, trust score, and allowed paper notional.

All memory must be stored in local Supabase/Postgres, and every row must be scoped by `team_id`.

Memory retrieval defaults to `team_id + category + event_template` scope. Cross-team analogs are allowed only when explicitly requested with a `cross_team` flag, must be lower weighted than same-team lessons, and must be marked in the forecast packet reason codes. Team lessons must include sample count, supporting forecast identifiers, contradicting forecast identifiers, market regime, creation timestamp, optional validity window, and decay metadata.

Lessons are not promoted to retrievable generalizations until they clear a hard sample gate. Candidate observations can be stored earlier, but central memory retrieval must not treat them as validated lessons. The default gate is:

- at least 30 settled forecasts for a category-level lesson,
- at least 10 settled forecasts for a rare event-template observation,
- at least 50 settled forecasts before a team/category calibration score can affect allocation or confidence adjustment.

## Proposed Supabase-Backed Tables

Initial table families:

- `team_profiles`
- `team_market_routes`
- `team_forecasts`
- `team_forecast_evidence`
- `team_memory_lessons`
- `team_source_reliability`
- `team_forecast_outcomes`
- `team_calibration_snapshots`
- `team_performance_summaries`
- `team_postmortems`

The first implementation should prioritize:

- `team_profiles`
- `team_market_routes`
- `team_forecasts`
- `team_forecast_evidence`
- `team_forecast_outcomes`
- `team_performance_summaries`
- `team_memory_lessons`

`team_market_routes` must persist `routing_confidence`, `routing_reason_codes`, and correction metadata. Calibration and team performance summaries must use corrected routes when a route has been reconciled.

`team_forecast_evidence` is required from the first implementation slice. A forecast without persisted evidence is not suitable for later postmortem, source reliability scoring, or stale-data diagnosis.

## Unified Team Forecast Packet

All teams must emit a common forecast packet:

```text
team_id
market_slug
condition_id
category
event_template
selected_side
forecast_probability
confidence
evidence_quality
data_freshness
resolution_risk
base_rate
market_implied_probability_observed
reason_codes
memory_references
source_references
known_failure_modes
config_version
prompt_version
paper_only
report_only
readonly
```

The central layer can then compare forecasts across teams consistently.

All team forecast packets must be constructed through a structural paper-only guard:

```text
paper_only must be true
report_only must be true
readonly must be true
all probability/score/cost/notional values must be Decimal
no float may survive JSON serialization
no packet may include auth, wallet, account, order, cancel, replacement, or exchange mutation fields
```

The packet is an input to central cost and recommendation logic. It does not replace the existing cost-aware event strategy. It supplies the team's forecast probability, confidence, evidence, memory references, and resolution-risk assessment. Central adapters then combine that forecast packet with the centralized microstructure snapshot to produce the existing cost-aware side/edge inputs and downstream paper recommendation reports.

## Team Performance and Trust

Central recommendation should eventually adjust confidence using team performance:

```text
adjusted_confidence =
    raw_confidence
  * team_trust_score
  * category_calibration_score
  * data_freshness_score
  * source_reliability_score
```

This should be introduced only after enough settled samples exist. Before that, team trust should default to neutral and reason codes should mark insufficient sample size.

The hard threshold for using a non-neutral trust score is 30 settled forecasts for the same team/category. The hard threshold for allowing trust or calibration to affect allocation is 50 settled forecasts for the same team/category. Until then, the neutral multiplier is 1.0 and reports must include an insufficient-sample reason code.

## Implementation Phasing

Recommended implementation sequence:

1. Team taxonomy and exact team/profile dataclasses.
2. Structural `PaperOnlyGuard` for team packets and team DB rows.
3. Market router report with exactly one primary team, optional secondary teams, confidence, reason codes, and correction metadata.
4. Team forecast packet dataclasses, evidence dataclasses, and explicit interface contract to the existing cost-aware pipeline.
5. Local Supabase persistence for routes, forecasts, forecast evidence, and outcomes.
6. Outcome feedback table and idempotent loader.
7. Team performance summary report with neutral trust until sample thresholds clear.
8. Generic memory lesson schema with candidate/validated states and hard sample gates.
9. One concrete domain workflow for `crypto_btc`.
10. Central recommendation integration using team forecast packets after the first workflow is persisted and scored.

Deferred until enough settled forecasts exist:

- team trust adjustment in allocation,
- cross-team memory analog retrieval,
- automated lesson promotion,
- source reliability scoring,
- full team-specific prompt profiles for all teams.

## Initial Team Build Priority

Recommended priority:

1. `crypto_btc`
2. `politics`
3. `sports_soccer`
4. `sports_basketball`
5. `macro_rates`
6. `crypto_eth`
7. `equity_indices`
8. `commodities_gold`
9. `commodities_oil`
10. `sports_other`

BTC and sports should generate faster feedback. Politics and macro have high strategic value but slower settlement cycles.

## Open Design Questions for Review

Claude Code should review the following:

- Is the team granularity appropriate, or should some teams be merged/split before implementation?
- Are the logical agents well-bounded, or are there role overlaps that will produce duplicate work?
- Is the proposed memory layer enough to make teams learn over time?
- Are there missing Phase 1 guardrails?
- Is centralizing cost, risk, and allocation the right boundary?
- Are any table families premature or under-specified?
- What is the smallest useful implementation slice that proves the architecture without overbuilding?
- What additional tests or invariants should be required?

## Proposed Decision Before Review

The final decision after Claude review is:

- Adopt the 10-team medium granularity.
- Implement central team router, paper-only guard, explicit forecast interface, evidence persistence, and team memory schema first.
- Keep all team outputs paper-only forecast packets.
- Keep cost, recommendation, allocation, and outcome scoring centralized.
- Do not implement live trading or team-controlled execution.
- Start with a narrow implementation slice: generic taxonomy, paper-only guard, router, forecast packet, evidence persistence, local Supabase persistence, outcome feedback, performance summary skeleton, and one runnable `crypto_btc` workflow.

## Accepted Review Changes

The Claude Code review produced an "approve with changes" verdict. The following changes are accepted:

- Phase 1 readonly enforcement must be structural, not metadata-only.
- The team forecast packet must have a concrete adapter/interface into the existing cost-aware pipeline.
- Forecast evidence persistence is part of Slice 1.
- Memory lessons require sample gates and staged promotion.
- Memory retrieval is team/category scoped by default.
- Memory lessons include market-regime and staleness metadata.
- Routes include correction metadata, and calibration uses corrected routes.
- Trust-score and allocation adjustments require hard settled-sample thresholds.
- Polymarket microstructure reads are centralized.
- The first runnable workflow is generic framework plus `crypto_btc`, not all teams at once.
