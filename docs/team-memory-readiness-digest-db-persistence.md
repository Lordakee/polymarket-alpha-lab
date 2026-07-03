# Team Memory Readiness Digest DB Persistence

This document clarifies the narrow persistence boundary for
`team_memory_readiness_digest_reports`.

`team_memory_readiness_digest_reports` is a local Supabase/Postgres durable
report-history exception for generated Team Memory Readiness Digest reports. It
stores internal Phase 1 report evidence so operators can read back readiness
history for long-term team-memory review. It is not a live trading mutation
table, not an execution queue, not a recommendation store, not account or wallet
state, and not an order, trade, signing, submission, cancellation, replacement,
or exchange-mutation surface.

Persistence is not a default CLI side effect. The default
`team-memory-readiness-digest` command builds and prints the read-only digest
from local diagnostics snapshot history sources. A durable insert is allowed
only when the local digest DB environment family explicitly enables it and the
configured DSN passes the local Supabase/Postgres validation path. The CLI must
not add DSN, table, `--persist`, `--live`, auth, wallet, account, order, trade,
execute, submit, recommendation, or sizing flags for this surface.

Hard Phase 1 flags are mandatory:

- `paper_only=True`
- `report_only=True`
- `readonly=True`

Those flags describe the digest report and the persisted history row. They do
not authorize live capital, order placement, position sizing, recommendation
generation, account reads, wallet access, private-key handling, or any exchange
mutation.

The only approved durable backend for this report history is the local
Supabase/Postgres instance on this host. Do not replace it or supplement it with
SQLite, DuckDB, Redis, MongoDB, SQLAlchemy-managed durable engines, generic
database abstraction layers, hosted database assumptions, JSONL durable
journals, CSV ledgers, file-backed durable stores, local filesystem caches, or
any other alternate durable backend. Legacy file surfaces remain
compatibility-only and must not become a durable substitute for
`team_memory_readiness_digest_reports`.

Environment-driven configuration is the only persistence configuration surface:

- `POLYMARKET_ALPHA_LAB_TEAM_MEMORY_READINESS_DIGEST_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_TEAM_MEMORY_READINESS_DIGEST_DB_DSN`
- `POLYMARKET_ALPHA_LAB_TEAM_MEMORY_READINESS_DIGEST_DB_TABLE`

The default table is `team_memory_readiness_digest_reports`. The optional table
environment variable must remain a simple local Postgres identifier. Do not
document real credentials, hosted database URLs, account identifiers, wallet
material, private keys, API tokens, market questions, or raw source payloads in
this persistence surface.

History readback is local report evidence only. It may summarize digest status,
source counts, reason-code counts, latest generated timestamps, duplicate-latest
signals, and the hard Phase 1 flags. It must not rank investments, recommend
markets, tune strategy weights, size positions, provide financial advice, issue
trade instructions, expose account state, or mutate external systems.
