# Strategy-First Roadmap

This roadmap note documents the current strategy-first phase for Polymarket
Alpha Lab. The project priority is selecting and analyzing Polymarket
probability-event markets, not ordinary asset-price investing.

The current phase is about screening, evidence, cost-aware decisioning, team
memory, and manual/operator execution before any live automation. It is an
operator-facing research and decision-support roadmap, not a promise of
automated execution.

## Current Phase Priority

The lab should first become good at choosing which probability-event markets
are worth research attention and which should be skipped, watched, or blocked.
That means the primary product surface is a disciplined market-selection and
decision packet flow:

- screen event markets for specificity, evidence availability, and timing;
- assemble source-backed evidence that explains the event probability;
- compare that probability with side-aware executable YES/NO prices;
- decide whether the evidence, costs, and risks justify candidate status;
- preserve enough local context for later review and team learning.

Ordinary asset-price investing asks whether an asset will appreciate or
depreciate. Polymarket probability-event markets ask whether a defined event
will resolve to a defined outcome under stated rules. This roadmap therefore
prioritizes event questions, outcome definitions, resolution sources, timing,
market structure, and repeatable research memory over generic asset trend
analysis.

## Decision Inputs

Every candidate decision must account for event probability, outcome criteria,
resolution risk, market microstructure, spread/liquidity, fees/cost drag, cash
lockup, finalization/settlement timing, and team memory.

The required decision packet should make these inputs explicit:

- `event probability`: the team's side-aware probability forecast, with the
  evidence and assumptions that moved it away from the market price;
- `outcome criteria`: the exact market question, outcome labels, close time,
  resolution rules, source hierarchy, and proof needed for final resolution;
- `resolution risk`: ambiguity, disputed-source risk, delayed reporting,
  revision risk, human adjudication risk, and off-platform dependency risk;
- `market microstructure`: executable bid/ask context, stale markets, crossed
  or unstable books, partial-fill assumptions, and price impact;
- `spread/liquidity`: whether depth and spread support the intended paper or
  operator-reviewed size without consuming the edge;
- `fees/cost drag`: explicit fees, expected slippage, spread cost, fill cost,
  and any other friction that reduces gross edge to net edge;
- `cash lockup`: capital tied up until outcome finalization, including the
  opportunity cost of waiting for markets with slow or uncertain settlement;
- `finalization/settlement timing`: expected resolution date, possible lag,
  dispute window, and when cash can realistically be reused;
- `team memory`: settled examples, calibration history, source-reliability
  memory, prior failure modes, and memory readiness policy for the owning team.

Candidate status should require positive net edge after cost, liquidity,
resolution, and timing adjustments. A large apparent probability gap is not
enough if the outcome criteria are unclear, the order book is too thin, costs
consume the edge, or team memory shows a repeated failure mode.

## Durable Data Boundary

All durable data is local Supabase/Postgres only.

Durable data includes screened-market records, research packets, score inputs,
candidate decision scores, team-memory evidence, diagnostics, review reports,
paper reports, and post-resolution learning records. These records are local
project evidence. They are not exchange state, account state, wallet state, or
live execution state.

The current phase must keep durable storage as local Supabase/Postgres report
and memory evidence only. Documentation, tests, and implementation plans should
not imply an alternate durable storage target or a hosted production database
target for this phase.

## Operating Model Connection

This roadmap extends the medium-scale team model. Specialist teams remain the
right unit of ownership because probability-event markets need domain-specific
research without fragmenting memory into one-off single-market agents.

The medium-scale team model should own:

- initial market triage by domain and event archetype;
- evidence collection and source-quality notes;
- probability forecasts and uncertainty notes;
- resolution-rule interpretation and dispute risks;
- memory updates from settled outcomes and postmortems.

The central layer should continue to own shared scoring discipline, cost and
liquidity normalization, decision packet assembly, and report boundaries. That
keeps teams focused on evidence quality while allowing comparable decisions
across politics, crypto, macro, commodities, equities, sports, and other event
categories.

The candidate decision score engine is the shared reducer that should connect
team research to candidate selection. It should use the team packet as input,
then score decision quality across evidence strength, probability edge,
outcome clarity, resolution risk, cost-adjusted liquidity, cash lockup,
settlement timing, and team memory. The score engine should explain why a
market is a candidate, research item, watch item, or blocked item; it should
not bypass review or turn scores into automatic execution.

## Execution Boundary

The boundary rule is: live trading/order placement is out of scope for the
current phase.

The permitted manual path is: operator/manual execution can be used after
report review. That means an
operator may review the candidate report, inspect the evidence and cost
assumptions, and then make any separate manual decision outside the automated
system boundary. The project may produce a report, checklist, or operator
ticket, but it must not submit, sign, cancel, replace, or route orders.

The current boundary is:

- no live trading/order placement;
- no order submission;
- no order signing;
- no wallet handling;
- no auth handling;
- no exchange mutation;
- no automated execution after a score threshold;
- no conversion of candidate status into an order instruction.

Manual/operator execution after report review is deliberately outside the
automation boundary. The roadmap goal is to improve market selection,
evidence quality, cost-aware decisioning, and team learning first. Any later
phase that proposes live automation must be documented separately with explicit
authorization, credential handling, audit logging, risk controls, dry-run
comparisons, and kill-switch design before it can be considered.
