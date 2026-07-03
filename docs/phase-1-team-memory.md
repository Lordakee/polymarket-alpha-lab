# Phase 1 Team Memory Contract

This document is the docs-to-code contract for the current Phase 1 multi-team module. It narrows the team-agent framework into an auditable boundary for politics, finance, and sports research teams, long-term team memory, and local durable readback.

Polymarket is a probability event market. Phase 1 supports automatic screening, research, and paper execution only.

Phase 1 team memory is paper-only, report-only, and readonly. It is research operations infrastructure only: no live trading, no auth, no wallet, no account, no order, no recommendation, no investment advice, no trade instruction, no financial advice, no position advice, and no position sizing. Costs and fees are research factors only, including spread, slippage, liquidity, settlement timing, and paper cost evidence.

## Multi-Team Ownership

Team routing assigns each market to one primary team, with optional secondary teams for operator context. The assigned team owns research responsibility only. It does not own execution, capital allocation, recommendation generation, risk limits, outcome scoring, position advice, or Polymarket account state.

The Phase 1 taxonomy separates politics, finance, and sports:

| Team Group | Team IDs | Responsibility |
| --- | --- | --- |
| Political research team | `politics` | Research politics and election-style markets where rule interpretation, source quality, and event timelines dominate. |
| Financial research teams | `crypto_btc`, `crypto_eth`, `macro_rates`, `equity_indices`, `commodities_gold`, `commodities_oil` | Research crypto, macro rates, index, and commodity markets using supplied evidence, local forecast artifacts, and local history. |
| Sports research teams | `sports_soccer`, `sports_basketball`, `sports_other` | Research sports markets where fixture context, roster/event evidence, and source freshness dominate. |

Only the current runnable workflow has executable code paths for supplied-input forecasting. Non-runnable teams may appear in taxonomy, routing, persistence-ready rows, diagnostics, memory readiness, and assignment reports, but those appearances are not live team agents and do not create an execution surface.

## Long-Term Team Memory

Long-term team memory means already-persisted local team diagnostics, forecast, evidence, outcome, diagnostics snapshot history, memory readiness, and assignment-history report rows. It is not a model cache, trading memory, account memory, wallet memory, or recommendation store.

The team memory readiness digest converts team diagnostics snapshot history gates into a per-team memory policy:

- `allow`: the selected team's local memory source is passing and can be used as research context.
- `throttle`: the selected team's local memory source is watch-level and can be used only with reduced reliance and operator review.
- `block`: the selected team's local memory source is blocked or missing and must not be used for that assignment row.

The team research assignment report carries the memory use policy into the operator handoff. The policy gates long-term team memory only; it must not tune strategy weights, size positions, rank investments, approve trades, generate recommendations, or authorize execution.

## Durable-Only Storage

Phase 1 durable project data for this surface is local Supabase/Postgres durable-only. Raw DSNs must be validated through `validate_local_postgres_dsn` before any psycopg connection or persistence adapter uses them.

The durable surfaces covered by this contract are:

- team framework tables such as `team_profiles`, `team_market_routes`, `team_forecasts`, `team_forecast_evidence`, and `team_forecast_outcomes`;
- diagnostics snapshot history in `team_diagnostics_snapshots`;
- memory readiness digest report rows when the local digest DB env family is enabled;
- team research assignment reports in `team_research_assignment_reports`.

See [team-memory-readiness-digest-db-persistence.md](team-memory-readiness-digest-db-persistence.md)
for the narrow `team_memory_readiness_digest_reports` persistence exception. It
is local Supabase/Postgres durable report history only, not a live trading
mutation, not a default CLI side effect, and not replaceable by an alternate
durable backend.

These rows are internal report evidence and readback material only. Do not replace them with SQLite fallback, SQLite substitute, Redis fallback, Mongo fallback, JSONL durable substitute, file-backed durable substitute, hosted database assumptions, SQLAlchemy-managed durable engines, or a generic durable-store abstraction.

Configuration stays env-driven. The team-memory and team-assignment CLI surfaces must not add DSN, table, persist, live, auth, wallet, private-key, account, order, trade, execute, submit, recommend, or recommendation flags.

## CLI Contract

The Phase 1 team-memory operator commands are report-scoped only:

- `polymarket-alpha-lab team-memory-readiness-digest --team-id crypto_btc --limit 100`
- `polymarket-alpha-lab team-memory-readiness-digest-history --digest-status blocked --limit 100`
- `polymarket-alpha-lab team-research-assignment --team-id crypto_btc --queue-limit 1 --route-limit 25 --memory-limit 100`
- `polymarket-alpha-lab team-research-assignment-history --limit 100`

The commands read local Supabase/Postgres report evidence through env-gated config families, emit aggregate paper-only/report-only/readonly output, and fail closed when required local DB config is missing or invalid. They must not expose source payloads, raw DSNs, table names, market questions in history output, credentials, wallet material, auth material, account identifiers, or order-like data.

## Negative Scope

This Phase 1 contract is intentionally narrow:

- no live trading;
- no auth;
- no wallet;
- no private-key handling;
- no account reads;
- no order signing, submission, cancellation, replacement, or mutation;
- no recommendation generation;
- no investment ranking;
- no trade instruction;
- no financial advice;
- no strategy-weight tuning;
- no position sizing.

Any future expansion beyond paper-only/report-only/readonly research operations must be designed and reviewed as a separate phase.
