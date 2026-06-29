# Paper Autonomous Readiness Digest DB Persistence

This optional local Supabase/Postgres persistence-only surface stores
deterministic `PaperAutonomousReadinessDigestReport` snapshots for later
paper-only/report-only/readonly review.

`paper-autonomous-readiness-digest` writes nothing by default. Only
`paper-autonomous-readiness-digest --persist` reads the readiness digest DB
environment config and inserts the already-built digest report. There are no
DSN or table CLI flags.

Environment:

- `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_DSN`
- `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE`

The default table is `paper_autonomous_readiness_digest_reports`.

Use a local Supabase/Postgres DSN only, such as a localhost, loopback, or local
Unix-socket Postgres endpoint. Do not assume a hosted database or document real
credentials. The table name is selected by env var only and should remain a
simple local Postgres identifier.

Do not put secrets, private keys, wallet credentials, account identifiers, or
API tokens in reports or docs. Persistence is observability history only. It is
not financial advice, investment ranking, permission to trade, an order
instruction, execution authorization, wallet access, auth handling, signing,
submission, cancellation, replacement, or exchange mutation.

All durable data for this surface remains local Supabase/Postgres only. There is
no JSONL/SQLite/file durable store, Redis, Mongo, SQLAlchemy, generic durable
store abstraction, hosted DB assumption, or file-backed cache.
