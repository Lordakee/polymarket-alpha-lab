# Team Agent Operating Model

This design note makes the future medium-scale team memory model concrete for
Polymarket Alpha Lab implementation. It is a strategy and team-memory note, not
production code and not a live trading design.

The boundary is Phase 1 paper-only/report-only/readonly. The system may screen
markets, research evidence, build operator-facing decision support, produce
paper-only reports, and read local durable history. It must provide no live
order placement, no wallet handling, no account authentication, no private-key
handling, no order signing, no order submission, no order cancellation, no order
replacement, and no exchange or account mutation.

## Medium-Scale Team Design

The target operating model is a medium-scale team design: teams are organized by
domain and event type, and each team has 3-5 roles/agents. This is deliberately
larger than a single generalist worker and smaller than one worker per market.
Each team should accumulate enough settled history for useful long-term memory
while staying specialized enough to know its domain.

Initial team families:

| Team family | Example team IDs | Typical scope |
| --- | --- | --- |
| Politics | `politics` | Elections, government actions, litigation, policy milestones, rule interpretation, source credibility, and resolution criteria. |
| Crypto/BTC | `crypto_btc` | Bitcoin price, ETF flow, macro sensitivity, mining, halving, exchange/news events, and BTC-specific source reliability. |
| Crypto/ETH | `crypto_eth` | Ethereum price, protocol upgrades, staking, ETF flow, ecosystem events, and ETH-specific source reliability. |
| Equities/indexes | `equity_indices` | Index closes, broad equity moves, earnings-sensitive index events, volatility, macro/equity cross-signals, and calendar risk. |
| Gold/rates | `commodities_gold`, `macro_rates` | Gold, rates, central banks, inflation, auctions, real yields, policy expectations, and macro release surprise risk. |
| Oil/energy | `commodities_oil` | Inventory releases, OPEC, supply disruptions, demand indicators, geopolitical energy risk, and settlement definitions. |
| Football | `sports_football` or a future football subteam under `sports_other` | Fixtures, injuries, weather, roster depth, market calendar, and sports-source freshness. |
| Basketball | `sports_basketball` | Fixtures, injuries, rest, travel, lineup availability, schedule spots, and source freshness. |
| Other sports | `sports_other` | Sports domains that do not yet have a dedicated subteam. |

The taxonomy may evolve, but it should keep the medium-scale principle: split
only when a domain has distinct evidence patterns and enough settled examples to
justify separate long-term memory.

## Roles Per Team

Every team should have 3-5 roles/agents. Roles can be implemented as separate
agent prompts, typed reducers, scheduled jobs, or explicit sections in a single
workflow, but the interface should preserve these responsibilities.

| Role/agent | Required for | Main job | Memory maintained | Candidate decision score contribution |
| --- | --- | --- | --- | --- |
| Source scout | All teams | Find and refresh domain-relevant source candidates, distinguish official/primary sources from commentary, and flag stale or duplicated sources. | Source allowlist notes, source freshness history, source latency, source reliability, recurring bad-source patterns. | Improves evidence availability and freshness inputs; penalizes missing, stale, duplicated, or low-reliability sources. |
| Evidence analyst | All teams | Turn raw research context into structured evidence claims, contradiction notes, resolution-rule checks, and uncertainty factors. | Evidence-quality history, contradiction patterns, resolution-rule failure modes, market-template notes. | Feeds evidence strength, contradiction penalty, resolution-risk penalty, and source quorum features. |
| Probability forecaster | All teams | Convert the evidence packet and memory context into calibrated probability deltas, confidence, uncertainty bands, and known failure modes. | Forecast calibration, Brier/hit-rate summaries, overconfidence patterns, domain/event-template performance. | Feeds base probability adjustment, confidence, calibration modifier, and forecast uncertainty features. |
| Market microstructure/cost analyst | Financial and tradeable-market review surfaces; optional but recommended for sports and politics when liquidity is thin | Review centrally supplied bid/ask, spread, depth, slippage, fees, settlement timing, and paper cost evidence. This role consumes central snapshots and must not fetch exchange state independently. | Cost/liquidity sensitivity notes, recurring spread/slippage failure modes, settlement timing issues, low-depth patterns. | Feeds cost-adjusted edge, liquidity penalty, settlement-risk penalty, and avoid/research-more reason codes. |
| Memory steward/reviewer | All teams when long-term memory is available; can be combined with evidence analyst in the smallest teams | Gate memory use, summarize reusable lessons, detect stale lessons, review post-resolution outcomes, and prevent memory leakage into execution. | Long-term memory index, memory readiness policy, lesson freshness, team playbooks, resolved-error postmortems. | Feeds memory reliability adjustment, replay-gap penalty, source reliability weighting, and reviewer-required flags. |

Minimum staffing should be three roles: source scout, evidence analyst, and
probability forecaster. Medium teams should add the market microstructure/cost
analyst and memory steward/reviewer as separate roles once the team has enough
markets, enough settled outcomes, or enough cost sensitivity to justify the
separation.

## Long-Term Memory

Long-term memory means local, durable, already-persisted research and outcome
history for a team. It is team context for screening, research, decision support,
and paper/report-only analysis. It is not a model cache, not a wallet memory,
not account state, not live trading memory, not an order history, not a
recommendation store, not a position-sizing engine, and not a strategy-weight
tuner.

Each team maintains memory in these categories:

- Source memory: approved and rejected source families, source freshness,
  latency, reliability, source quorum behavior, and known source failure modes.
- Evidence memory: recurring evidence templates, contradiction patterns,
  source-disagreement cases, resolution-rule ambiguities, and stale-evidence
  failure modes.
- Forecast memory: team and event-template calibration, Brier-style error
  summaries, overconfidence/underconfidence patterns, and uncertainty bands that
  worked or failed.
- Cost and market memory: spread, liquidity, slippage, fee drag, settlement
  timing, thin-book patterns, and paper cost sensitivity. These are research
  factors only.
- Review memory: post-resolution lessons, reviewer overrides, memory freshness,
  replay gaps, source recheck cadence, and stale playbook warnings.

Memory use is gated before it can influence a candidate:

- `allow`: the local memory source passes readiness checks and may be used as
  research context.
- `throttle`: the memory source is watch-level and may be used only with reduced
  reliance and operator review.
- `block`: the memory source is missing, stale, duplicated, invalid, or blocked;
  the team must not rely on long-term memory for the candidate.

Memory can explain why a candidate needs more research, why a source deserves a
lower weight, why a probability forecast should carry lower confidence, or why a
cost/liquidity feature should penalize a paper score. Memory must not approve a
trade, authorize execution, submit an order, size a position, read a wallet,
change account state, or mutate exchange state.

## Durable Data Policy

All durable project data for this model belongs in local Supabase/Postgres.
Local Supabase/Postgres is the only durable persistence target for team profiles,
team routes, forecasts, forecast evidence, outcomes, diagnostics snapshots,
memory readiness reports, research assignment reports, candidate decision score
inputs, and operator-facing paper reports.

Durable data must not be stored in sqlite, SQLite fallback files, jsonl durable
journals, JSONL durable substitutes, CSV ledgers, file-backed durable stores,
DuckDB, Redis, MongoDB, hosted database assumptions, generic durable-store
abstractions, or SQLAlchemy-managed durable engines. Files may be used only for
local fixtures, supplied test inputs, generated reports, or temporary artifacts
where an existing workflow explicitly treats them as non-durable.

Any future implementation that persists team memory must validate raw DSNs with
the project local Postgres validator before connecting. Documentation examples
must use placeholders rather than real DSNs, credentials, account identifiers,
wallet material, or tokens.

## Candidate Decision Score Flow

The team model feeds candidate decision scores through research features and
paper/report-only score inputs. It does not create a live execution path.

Expected flow:

```text
market metadata and supplied read-only evidence
  -> route to primary domain/event team and optional secondary context team
  -> source scout freshness and reliability notes
  -> evidence analyst structured evidence and contradiction notes
  -> probability forecaster calibrated probability packet
  -> market microstructure/cost analyst review of centrally supplied cost snapshot
  -> memory steward/reviewer memory policy and reusable lesson summary
  -> candidate decision score inputs
  -> paper-only/report-only/readonly screening, research packet, and operator report
  -> local Supabase/Postgres durable report history
```

Candidate decision score inputs should include:

- team route and event-template identifiers;
- source freshness, source reliability, and source quorum status;
- evidence strength, contradiction level, and resolution-rule risk;
- forecast probability, confidence, uncertainty, and calibration adjustment;
- centrally supplied spread, depth, slippage, fee, liquidity, settlement timing,
  and paper cost factors;
- long-term memory policy: `allow`, `throttle`, or `block`;
- memory references, stale-memory warnings, and replay-gap flags;
- required operator-review reasons and blocked/watch/pass reason codes;
- explicit `paper_only=True`, `report_only=True`, and `readonly=True` flags.

The score layer may rank candidates for research priority, screening priority,
watch status, rejection, or operator review. It must not produce investment
advice, trade instructions, live recommendations, live order placement, position
sizing, wallet operations, account operations, order signing, order submission,
order cancellation, order replacement, or exchange mutation.

## Domain Examples

Politics teams should weight source authority, rule interpretation, event
timeline, polling/source quality, litigation or certification dependencies, and
resolution criteria. Their long-term memory should emphasize resolution-rule
mistakes, stale poll narratives, weak source families, and overconfidence around
ambiguous event definitions.

Crypto/BTC teams should weight BTC-specific source freshness, macro sensitivity,
ETF flow context, on-chain/mining context where supplied, volatility regime, and
event-template calibration. Their long-term memory should separate BTC lessons
from ETH and broader crypto lessons so market-regime and source reliability
patterns do not blur together.

Equities/indexes teams should weight official calendars, index methodology,
macro release timing, market close definitions, volatility regime, and broad
equity cross-signals. Their memory should track close-price definition mistakes,
late-session reversal patterns, and source timing failures.

Gold/rates teams should weight central-bank calendars, inflation and labor
releases, auction tails, real-yield context, dollar moves, and commodity/rates
cross-signals. Their memory should record whether prior surprises came from
release interpretation, market reaction, settlement timing, or source freshness.

Football and basketball subteams should weight fixtures, injuries, lineup or
roster status, schedule congestion, rest/travel, weather where applicable, and
source recency. Their memory should track team-news latency, stale injury
reports, roster-source reliability, and event-specific settlement quirks.

## Implementation Notes For Future Work

Future implementation should start with data contracts, not agent autonomy:

- define typed role outputs for source, evidence, forecast, cost, and memory
  review sections;
- persist only the durable rows approved for local Supabase/Postgres;
- expose memory policy as an explicit field on candidate decision score inputs;
- keep central ownership of Polymarket market snapshots, cost-aware edge,
  risk, paper allocation, outcome scoring, and reporting;
- add tests that reject live trading, auth, wallet, account, order, and exchange
  mutation imports or identifiers in team-memory code paths;
- add report tests that require paper-only/report-only/readonly language and
  no live order placement language in operator-facing output.

Any future expansion beyond this paper-only/report-only/readonly model requires
a separate phase design and review. This note does not authorize live trading,
credential handling, wallet handling, account access, or order mutation.
