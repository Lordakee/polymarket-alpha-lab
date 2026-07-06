# Strategy Pipeline Architecture Draft

This draft defines the intended strategy pipeline architecture for Phase 1
paper operations. It is a documentation contract only; it does not add code,
execution paths, live trading, or production database behavior.

## Phase 1 Boundary

The strategy pipeline is paper-only, report-only, and readonly. It supports
candidate screening, specialist research, source review, paper cost analysis,
operator-facing reports, and local readback. It must not authorize live
trading, account authentication, wallet access, order signing, order
submission, order cancellation, order replacement, investment advice, position
sizing, or capital allocation.

Paper execution means simulated evidence and reporting only. Any future move
from paper operations to live execution must be designed as a separate phase
with new safety reviews, new interfaces, and explicit approval boundaries.

## Pipeline Shape

1. Candidate intake normalizes market metadata, resolution criteria, available
   prices, liquidity context, and paper-only identifiers.
2. Team routing assigns each candidate to a primary specialist research team
   and may include secondary teams for operator context.
3. Specialist teams produce structured research packets with source references,
   confidence, failure modes, memory references, and paper/report/readonly
   flags.
4. The central strategy layer reviews source quality, long-term memory context,
   forecast-vs-price disagreement, liquidity, and estimated trading costs.
5. Candidate decisions remain paper decisions: research, watch, candidate, or
   blocked. No decision creates an order intent or execution instruction.
6. Durable report evidence is persisted and read back only through approved
   local Supabase/Postgres surfaces.

## Multi-Research-Team Responsibilities

Specialist teams own research responsibility, not execution authority.

| Owner | Responsibility | Must not do |
| --- | --- | --- |
| Central strategy layer | Candidate intake, normalized context, routing, source-quality checks, paper cost review, decision assembly, and report persistence. | Bypass team research, create live order paths, or use memory to size positions. |
| Politics research team | Election-style and political markets where timelines, rules, polling context, and source reliability dominate. | Treat partisan source consensus as sufficient without corroboration. |
| Crypto research teams | BTC-, ETH-, and protocol-linked markets where price context, protocol events, exchange evidence, and recurring source quality matter. | Infer executable edge without supplied market, liquidity, and cost context. |
| Sports and event research teams | Sports, league, and event-driven markets where schedules, injury/status data, rules, and settlement criteria matter. | Treat stale status reports or unofficial summaries as final evidence. |
| Operator review | Review paper reports, reason codes, blocked reasons, and required follow-up research. | Convert paper recommendations into live trades. |

Teams may contribute competing views. The central layer reconciles those views
into auditable paper decisions and preserves the disagreement rather than
silently collapsing it into a single unsupported forecast.

## Long-Term Memory

Long-term memory is already-persisted local Phase 1 evidence: team diagnostics,
forecasts, source observations, assignment history, outcome rows, readiness
digests, cycle snapshots, and report readback. It is used to improve research
quality by surfacing recurring source failures, stale evidence, calibration
patterns, and prior market-resolution lessons.

Memory is not a trading memory, model cache, wallet/account memory,
recommendation store, or allocation engine. Memory may inform source
reliability notes, known failure modes, and operator-facing diagnostics. It
must not approve trades, tune strategy weights, rank investments, size
positions, or authorize execution.

## Information Source Quality

Each research packet should preserve source references, source family, observed
time, corroboration status, contradiction status, and unresolved lessons. Source
quality review should prefer fresh, primary, and independently corroborated
evidence over stale, derivative, anonymous, or single-point claims.

Weak source quality should downgrade the decision to research, watch, or
blocked. It should not be offset by a large apparent forecast edge. A paper
candidate needs both an explainable forecast and enough source reliability to
make the report auditable.

## Trading Costs

Trading costs are research factors only. The central layer should subtract or
flag spread, fees, slippage, liquidity limits, settlement timing, and executable
paper depth before treating any forecast-vs-price gap as an edge.

Cost evidence must stay attached to the paper decision. A candidate should be
blocked or watched when the apparent edge does not survive realistic paper cost
assumptions, when executable depth is insufficient, or when liquidity is stale,
crossed, fragmented, or unavailable at the intended paper notional.

## Local Supabase Durable Data Rule

All durable project data for this strategy pipeline must use local
Supabase/Postgres only. Raw database URLs must be validated as local Postgres
DSNs before any persistence adapter or readback path opens a connection.

Do not introduce SQLite, DuckDB, Redis, MongoDB, hosted database assumptions,
SQLAlchemy-managed durable engines, generic durable-store abstractions, JSONL
durable journals, CSV ledgers, file-backed durable stores, or filesystem
caches as durable substitutes. Compatibility files may exist for legacy
workflows, but they must not become Phase 1 durable memory, report history, or
strategy state.

## Review Checklist

- Every strategy output preserves hard `paper_only`, `report_only`, and
  `readonly` semantics.
- Every candidate has a primary team owner and clear follow-up responsibility.
- Every source-dependent conclusion includes freshness, corroboration, and
  contradiction context.
- Every apparent edge is reviewed after spread, fees, slippage, liquidity, and
  settlement timing.
- Every durable write or readback path targets local Supabase/Postgres only.
- No strategy component creates live trading, wallet, account, order, or
  allocation behavior.
