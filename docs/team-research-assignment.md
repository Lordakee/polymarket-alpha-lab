# Team Research Assignment Report

Purpose: the team research assignment report is a Phase 1 read-only operations report for assigning existing strategy candidate research queue rows to specialist research teams. It answers one operator question: which specialist team is responsible for researching each queued market, and what long-term memory policy applies to that team for this assignment?

This document defines the report boundary only. It does not define a live strategy, an execution path, or an investment recommendation; durable assignment evidence is limited to internal local Supabase/Postgres report persistence and history readback.

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

Configuration for any persisted read path stays in existing environment modules. Do not add DSN, table, wallet, auth, order, live, execution, account, or key-material CLI flags for this report. After the required env gates pass, runtime source/runner errors are wrapped by the CLI redaction path for DSNs, table names, raw payloads, hashes, market questions, market slugs, credentials, account identifiers, wallet material, auth material, key material, and order-like data. Argparse usage errors and env-gate failures are fail-closed validation surfaces, not a supported way to pass secrets.

The assignment report is a read-only composition. It should not create, alter, repair, delete, backfill, upsert, or refresh source rows.

This node adds the composed team-research-assignment DB-source and CLI path over those existing sources. It is an env-only local Supabase/Postgres read-only composition: the CLI loads queue reports, persisted one-row route reports, and the memory readiness digest through existing env config modules, then passes typed source reports to the assignment reducer. It does not add a generic DB abstraction, JSONL durable substitute, or direct DB configuration flags.

The CLI fails closed before source loading when any required DB family is disabled or lacks a DSN: strategy candidate research queue, team forecast route, or team diagnostics snapshot. CLI limits must be positive and are validated before env reads. The default limits are `--queue-limit 1`, `--route-limit 500`, and `--memory-limit 100`; omitting `--team-id` selects all known teams.

Relevant env config families:

- Queue reports: `POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED`, `POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN`, and `POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE`.
- Team route readback: `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_ENABLED`, `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_DSN`, and `POLYMARKET_ALPHA_LAB_TEAM_ROUTE_DB_TABLE` for the `team_market_routes` source. Other team forecast tables remain part of the broader team forecast config family but are not assignment output tables.
- Team-memory readiness: `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED`, `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN`, and `POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE`, consumed through the existing diagnostics snapshot history and memory-readiness digest read path.

The operator CLI is `polymarket-alpha-lab team-research-assignment`. Its report-scoped options are `--team-id`, `--queue-source-config-version`, `--memory-config-version`, `--queue-limit`, `--route-limit`, and `--memory-limit`. `--queue-source-config-version` filters the queue source readback, and `--memory-config-version` is passed to the memory-readiness source. There is no generic assignment `--config-version`, `--market-slug`, or `--forecast-id` option. It must not expose `--dsn`, `--table`, `--persist`, `--live`, `--auth`, `--wallet`, `--private-key`, `--api-key`, `--account`, `--order`, `--trade`, `--execute`, or `--submit`.

## Assignment Report Persistence

The generated assignment report can be persisted as internal Phase 1 report evidence when the assignment DB env family is enabled:

- `POLYMARKET_ALPHA_LAB_TEAM_RESEARCH_ASSIGNMENT_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_TEAM_RESEARCH_ASSIGNMENT_DB_DSN`
- `POLYMARKET_ALPHA_LAB_TEAM_RESEARCH_ASSIGNMENT_DB_TABLE`

The default table is `team_research_assignment_reports`. The table is local Supabase/Postgres only and stores:

- a canonical `payload_json` copy of the typed `TeamResearchAssignmentReport`,
- `report_sha256`,
- source config versions,
- aggregate assignment status and counts,
- reason codes,
- top-level hard `paper_only`, `report_only`, and `readonly` flags.

The table also enforces materialized-field checks against `payload_json`, JSON object/array checks, `ready`/`watch`/`blocked` report status values, count alignment, and hard flags. Lookup indexes follow the store's newest-first order: `generated_at desc`, `inserted_at desc`, and `report_sha256 desc`.

Persistence is intentionally env-only. There is no `--persist`, `--dsn`, `--table`, `--live`, auth, wallet, account, order, trade, execute, or submit flag. If assignment DB persistence is disabled, `team-research-assignment` still builds and prints the report without opening that assignment DB connection. If persistence is enabled, the generated report is inserted with `ON CONFLICT (report_sha256) DO NOTHING`.

## Assignment History Readback

`polymarket-alpha-lab team-research-assignment-history --limit 100` reads persisted assignment reports through the assignment DB env family and builds a pure report-only history summary. Options are limited to:

- `--assignment-status`
- `--config-version`
- `--limit`

The history report is aggregate only. It prints `history_status`, report counts, `status_rows`, latest assignment counts, count deltas, duplicate-latest detection, reason codes, and hard flags. It does not print market slugs, questions, selected sides, scoring sides, routing confidence, source payloads, DB DSNs, or table names.

History status is `blocked` when there is insufficient persisted history or duplicate latest timestamps; otherwise it is `observed`. This is observability for long-term team-memory operations, not investment ranking, recommendation generation, trade approval, execution readiness, or position sizing.

## Operator Output

The useful operator fields are aggregate and assignment-oriented:

- report assignment status and recommended next step,
- total assignment, assigned, watch, and blocked counts,
- per-team summary counts,
- per-row market slug, assigned team, category id, assignment status, memory use policy, evidence gaps, and reason codes,
- source config versions,
- hard `paper_only`, `report_only`, and `readonly` flags.

If a queue row has no matching route inside an otherwise nonempty route readback, the report uses `team_id=unassigned` with `memory_readiness_status=missing` and `memory_use_policy=block`; this is an operator-visible blocked-routing sentinel, not a specialist team. If the DB-source route readback itself is empty, or if any persisted route report is not a one-row `TeamMarketRouteReport`, the DB-source fails closed before memory loading and assignment composition.

Output should make blocked and watch reasons visible enough for operators to route follow-up work, while avoiding source payloads, credentials, DB internals, wallet/account details, and order-like data.

## Non-Goals

Team research assignment is not a recommendation layer. It must not use recommendation score, research priority score, suggested notional, selected notional, or position-sizing fields to decide whether a team can research a market.

The report is not investment advice, not a trading signal, not investment ranking, not order sizing, not an order queue, not execution authorization, and not an approval workflow. It only assigns research responsibility and gates long-term team-memory use for Phase 1 paper operations.
