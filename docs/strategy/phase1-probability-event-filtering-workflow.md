# Phase 1 Probability Event Filtering Workflow

This strategy-system node defines the Phase 1 workflow for filtering
Polymarket probability-event markets. It is a documentation contract for
paper-only, report-only, readonly strategy operations. It does not authorize
live trading, investment advice, trade instructions, position sizing, wallet
handling, account authentication, order signing, order submission, order
cancellation, order replacement, exchange mutation, or account mutation.

The purpose of Phase 1 filtering is to decide which probability events deserve
research attention, which should be watched, which can become paper candidates,
and which must be blocked before any operator considers separate manual action
outside the automated system boundary.

## Workflow Summary

```text
market discovery
  -> market metadata normalization
  -> evidence acquisition
  -> specialist team research
  -> forecast-vs-market comparison
  -> cost, EV, liquidity, and settlement-risk review
  -> manual go/no-go packet
  -> operator review
  -> local Supabase/Postgres report persistence and readonly readback
```

Every stage preserves `paper_only=True`, `report_only=True`, and
`readonly=True` wherever flags exist. A passing packet creates decision support,
not an order, not an execution instruction, and not approval to trade.

## Market Discovery

Market discovery starts with read-only candidate intake. The intake layer may
screen Polymarket probability-event markets for research relevance, but it must
not mutate markets, accounts, orders, wallets, or exchange state.

Discovery records should capture:

- market slug or public market reference;
- event question and outcome labels;
- event category, event template, and likely specialist team route;
- close time, expected resolution time, and settlement-timing notes;
- official resolution rules and linked resolution sources;
- current YES/NO executable-price context if supplied by an approved readonly
  source;
- market activity, spread, depth, and stale-market warning signals when
  available;
- initial reason for inclusion, watch, or rejection.

Discovery should reject or block markets with missing questions, unclear outcome
labels, missing resolution rules, unavailable source hierarchy, closed or
unusable market state, or any requirement to authenticate, use private account
state, place orders, or inspect live account data.

## Evidence Acquisition

Evidence acquisition builds an auditable source base for the event probability.
It should prefer primary, official, timestamped, and independently corroborated
sources over commentary, anonymous claims, stale summaries, or single-point
claims.

Each evidence item should preserve:

- source name, URL/API reference, or named official publication;
- source family: official, primary, secondary, derived, commentary, or market
  data;
- retrieval timestamp in UTC and the source data timestamp when available;
- freshness status and expected refresh cadence;
- claim summary tied to the market's exact resolution criteria;
- corroborating and contradicting sources;
- source limitations, missing facts, and known failure modes;
- whether the item is safe for operator-facing report output after redaction.

Evidence acquisition does not scrape private accounts, bypass access controls,
use credentials, read hosted account state, collect wallet data, or create a
browser/exchange automation path. If the event cannot be supported by safe,
traceable, readonly evidence, the candidate remains `research`, `watch`, or
`blocked`.

## Specialist Team Research

Each candidate routes to one primary specialist team and may include secondary
teams for context. Teams own research judgment only; the central strategy layer
continues to own normalization, cross-market comparability, cost-aware review,
report assembly, and persistence boundaries.

Specialist research packets should include:

- primary team id and any secondary team ids;
- event-template classification and why the team owns it;
- source-quality assessment, including freshness and contradiction notes;
- resolution-rule interpretation and edge cases;
- canonical event `P(YES)` forecast probability with confidence and uncertainty
  range;
- evidence that moved the team away from the market price;
- memory policy status: `allow`, `throttle`, or `block`;
- relevant long-term memory references, stale-memory warnings, and prior
  failure modes;
- required follow-up owner and deadline when the packet is incomplete.

forecast_probability always denotes canonical Decimal P(YES), regardless of selected_side; selected_side identifies the paper-review side being evaluated and never reorients forecast_probability; P(NO) is 1 - P(YES).

Team memory is local, durable Phase 1 research context only. It can explain
source reliability, calibration, recurring mistakes, and reviewer concerns. It
must not approve trades, rank investments, size positions, tune allocations,
authorize execution, or convert a research packet into an order path.

## Cost, EV, Liquidity, and Settlement Review

The central strategy layer converts the research packet into paper decision
support by reviewing whether the forecast survives realistic market frictions.

Required review dimensions:

| Dimension | Required Phase 1 Question | Common Blockers |
| --- | --- | --- |
| Gross edge | Is the team's forecast probability meaningfully different from the executable YES/NO price? | No explainable forecast delta, stale market price, midpoint-only comparison, unsupported side selection. |
| Expected value | Does side-aware EV remain positive after costs and uncertainty? | EV depends on optimistic fill assumptions, ignores uncertainty, or reverses after cost adjustment. |
| Spread and fees | Does the apparent edge survive spread, fees, and quoted executable price? | Wide spread, fee drag, crossed book, stale quote, or cost estimate missing. |
| Slippage and fill | Can the intended paper size be filled without consuming the edge? | Thin depth, fragmented depth, partial-fill risk, volatile book, unavailable order-book evidence. |
| Liquidity | Is there enough current market activity and depth to make the paper candidate meaningful? | Illiquid market, stale activity, close-time instability, depth below intended paper notional. |
| Settlement timing | Does lockup, delayed finalization, dispute timing, or source lag reduce the decision quality? | Unclear finalization time, long lockup, ambiguous proof date, revision/dispute risk. |
| Resolution risk | Can the team explain exactly how the market resolves and what source proves it? | Ambiguous wording, missing source hierarchy, manual adjudication risk, contradictory proof sources. |

Side probability and net edge should be written as paper research calculations:

```text
YES side probability = forecast_probability
NO side probability = 1 - forecast_probability
YES net edge = forecast_probability - executable_yes_price - total_cost_probability
NO net edge = (1 - forecast_probability) - executable_no_price - total_cost_probability
```

Positive net edge is necessary but not sufficient. A packet can still be
`research`, `watch`, or `blocked` when source quality, liquidity, settlement,
resolution, or memory gates are not ready.

## Manual Go/No-Go Packet

The output of Phase 1 filtering is a manual go/no-go packet for operator review.
The packet is decision support only and must remain paper-only, report-only, and
readonly.

The packet should contain:

- event and market identifiers;
- market question, outcomes, close time, and resolution criteria;
- primary team owner and specialist packet digest;
- evidence summary with source freshness, corroboration, and contradictions;
- canonical event forecast, side-aware executable price, gross edge, total
  cost, net edge, and EV summary;
- liquidity, depth, fill, spread, fee, slippage, settlement, and resolution-risk
  notes;
- memory policy and relevant prior lessons;
- recommended status: `go_for_manual_review`, `no_go`, `research`, `watch`, or
  `blocked`;
- reason codes and blocked reasons;
- required human follow-ups before any separate manual action;
- redaction status and local persistence status.

`go_for_manual_review` means the packet is complete enough for a human operator
to read. It does not mean buy, sell, place an order, approve capital, size a
position, or execute. Any manual action remains outside the automated Phase 1
system boundary.

## Readonly Boundary

Allowed Phase 1 behavior:

- read-only market discovery and supplied market-context review;
- source-backed event research;
- specialist team forecasts over supplied and safe readonly evidence;
- paper-only cost, EV, liquidity, settlement, and resolution-risk calculations;
- manual go/no-go packet assembly;
- local Supabase/Postgres persistence of report rows;
- readonly readback, diagnostics, trend analysis, and outcome learning.

Forbidden Phase 1 behavior:

- live trading or automated investing;
- investment advice, trade instructions, position advice, or position sizing;
- wallet handling, private-key handling, account authentication, or hosted
  account reads;
- order signing, order submission, order cancellation, order replacement, or
  exchange/account mutation;
- credential collection, private account scraping, or browser automation that
  depends on authenticated state;
- persistence to alternate durable stores outside the approved local
  Supabase/Postgres boundary.

## Local Supabase/Postgres Persistence Principles

Durable Phase 1 data belongs in local Supabase/Postgres only. Persistence should
store auditable report evidence and derived readonly summaries, not execution
state.

Approved durable content includes:

- discovered market screening rows;
- research packet digests and source-quality summaries;
- specialist assignment reports;
- cost, EV, liquidity, and settlement-risk review rows;
- manual go/no-go packet rows;
- operator review status, reason codes, and follow-up tasks;
- readonly readback, diagnostics, and post-resolution learning summaries.

Persistence must not introduce SQLite, DuckDB, Redis, MongoDB, hosted database
assumptions, SQLAlchemy-managed durable engines, JSONL durable journals, CSV
durable ledgers, file-backed durable stores, or generic durable-store
abstractions as Phase 1 substitutes. Raw DSNs must be validated as local
Postgres DSNs before any connection is opened. Reports, logs, examples, and
operator packets must redact raw DSNs, secrets, tokens, wallet material, account
identifiers, and order-like sensitive values.

## Decision States

| State | Meaning | Required Next Step |
| --- | --- | --- |
| `go_for_manual_review` | Evidence, forecast, costs, liquidity, settlement, resolution, and memory gates are complete enough for human packet review. | Operator reviews the packet outside any automated execution path. |
| `no_go` | Packet is complete and the market should not advance because net edge or risk quality is insufficient. | Persist reason codes and only reopen after a material change. |
| `research` | A specific evidence, cost, liquidity, settlement, resolution, or memory gap remains answerable. | Assign owner, required source, and recheck deadline. |
| `watch` | Current decision quality is insufficient, but a future price, source, or event update could matter. | Record trigger conditions and refresh cadence. |
| `blocked` | The market violates Phase 1 boundaries or has unresolvable data, source, liquidity, settlement, or resolution blockers. | Persist blocking reason and do not reopen without explicit changed evidence. |

## Documentation Links

- Operator runbook:
  [Phase 1 Probability Event Go/No-Go Runbook](../operators/phase1-probability-event-go-no-go-runbook.md)
- Boundary and persistence principles:
  [Phase 1 Probability Event Readonly Persistence Principles](../phase1/probability-event-readonly-supabase-principles.md)
- Existing candidate matrix:
  [Strategy Candidate Decision Matrix](../strategy-candidate-decision-matrix.md)
- Existing multi-team model:
  [Phase 1 Multi-Team Operating Model](../phase-1-multi-team-operating-model.md)
