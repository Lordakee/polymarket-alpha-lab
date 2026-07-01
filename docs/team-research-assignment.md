# Team Research Assignment Report

Purpose: the team research assignment report is a Phase 1 read-only operations report for assigning existing strategy candidate research queue rows to specialist research teams. It answers one operator question: which specialist team is responsible for researching each queued market, and what long-term memory policy applies to that team for this assignment?

This document defines the report boundary only. It does not define a live strategy, an execution path, an investment recommendation, or a new durable store.

## Phase 1 Boundary

The report is paper-only, report-only, and readonly. A valid report and its rows must preserve `paper_only=True`, `report_only=True`, and `readonly=True`.

Do not add or route any of the following through team research assignment:

- No live trading.
- No auth flow.
- No wallet access.
- No key-material handling.
- No account reads.
- No order signing.
- No order submission.
- No order cancellation.
- No order replacement.
- No exchange mutation.
- No investment advice.
- No investment ranking.
- No trade recommendations or trade instructions.
- No strategy-weight tuning.
- No position sizing.

The assignment report is an operations handoff for research responsibility only. It does not approve a trade, create an order intent, authorize capital deployment, or promote a paper recommendation into execution.

## Inputs

The report composes three already-built Phase 1 reports:

- `PaperStrategyCandidateResearchQueueReport`: the existing candidate research queue, including market slug, question, selected side, scoring side, queue research status, readiness status, evidence gaps, and queue reason codes.
- `TeamMarketRouteReport`: the specialist-team routing report, including primary team, corrected team when present, category id, routing confidence, and secondary teams.
- `TeamMemoryReadinessDigestReport`: the long-term team-memory readiness digest, including per-team `pass`, `watch`, or `blocked` source status.

The assignment reducer should treat those inputs as supplied evidence. It should not fetch markets, recompute recommendations, inspect accounts, read wallets, generate forecasts, or repair missing upstream data.

## Assignment Semantics

The report preserves the queue order exactly. Queue order remains an upstream research queue ordering, not a new investment ranking by the assignment report.

Each queue row is matched to a team route by `market_slug`. The assigned `team_id` is the corrected routed team when route correction exists; otherwise it is the primary routed team. The assigned team is then matched to the memory readiness digest by `team_id`.

Row assignment statuses are operational statuses:

- `assigned`: the queued row has a route, the queue row is research-ready, and the assigned team's memory readiness allows normal use.
- `watch`: the queued row or the assigned team's memory readiness has a non-blocking watch condition, so the work needs operator review or throttled memory use.
- `blocked`: the row cannot be assigned safely because the queue is blocked, the route is missing, the team's memory readiness is missing, or the team's memory readiness is blocked.

Report status is the aggregate operations status:

- `ready`: at least one row is assigned and no row is watch or blocked.
- `watch`: no row is blocked, but at least one row is watch.
- `blocked`: any row is blocked, or the source queue is empty.

Recommended next steps stay inside the paper operations boundary:

- `assign_team_research_work` for ready reports.
- `review_team_research_assignments` for watch reports.
- `block_team_research_assignment` for blocked reports.

These next steps are not execution readiness, trading approval, or financial advice.

## Memory Policy

Long-term memory use is gated per assigned team:

- `allow`: the assigned team's memory readiness source is `pass`; the team may use its existing local long-term memory for the research assignment.
- `throttle`: the assigned team's memory readiness source is `watch`; downstream research should reduce reliance on long-term memory and keep the assignment under operator review.
- `block`: the assigned team's memory readiness source is `blocked` or missing, or the assignment has no valid team route; downstream research must not use long-term memory for that row.

Long-term memory means already-persisted local team diagnostics, forecast, evidence, outcome, and snapshot history rows. The assignment report must not synthesize durable memory outside the local Supabase/Postgres boundary and must not use memory status to tune strategy weights, size positions, or rank investments.

## Durable Data Boundary

The report can be built from caller-supplied in-memory typed reports. When persisted inputs are used, they must be read only from existing env-driven local Supabase/Postgres sources:

- persisted strategy candidate research queue reports,
- persisted team market routes or route-derived reports,
- persisted team diagnostics snapshot history used by the memory readiness digest.

Durable project data for this surface must not move to SQLite, Redis, MongoDB, SQLAlchemy-managed durable engines, JSONL durable substitutes, file-backed caches, hosted database assumptions, or a generic durable-store abstraction.

Configuration for any persisted read path stays in existing environment modules. Do not add DSN, table, wallet, auth, order, live, execution, account, or key-material CLI flags for this report. Error output should avoid printing DSNs, table names, raw payloads, hashes, market questions, market slugs, credentials, account identifiers, wallet material, auth material, key material, or order-like data.

The assignment report is a read-only composition. It should not create, alter, repair, delete, backfill, upsert, or refresh source rows.

A composed team-research-assignment DB source and CLI are deferred until env-scoped local Supabase/Postgres `team_market_routes` readback exists; see [team-research-assignment-db-source-gap.md](team-research-assignment-db-source-gap.md).

## Operator Output

The useful operator fields are aggregate and assignment-oriented:

- report assignment status and recommended next step,
- total assignment, assigned, watch, and blocked counts,
- per-team summary counts,
- per-row market slug, selected side, assigned team, category id, assignment status, memory use policy, evidence gaps, and reason codes,
- source config versions,
- hard `paper_only`, `report_only`, and `readonly` flags.

If a queue row has no matching route, the report uses `team_id=unassigned` with `memory_readiness_status=missing` and `memory_use_policy=block`; this is an operator-visible blocked-routing sentinel, not a specialist team.

Output should make blocked and watch reasons visible enough for operators to route follow-up work, while avoiding source payloads, credentials, DB internals, wallet/account details, and order-like data.

## Non-Goals

Team research assignment is not a recommendation layer. It must not use recommendation score, research priority score, suggested notional, selected notional, or position-sizing fields to decide whether a team can research a market.

The report is not investment advice, not a trading signal, not investment ranking, not order sizing, not an order queue, not execution authorization, and not an approval workflow. It only assigns research responsibility and gates long-term team-memory use for Phase 1 paper operations.
