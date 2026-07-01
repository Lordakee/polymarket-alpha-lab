# Paper Trade Cost Audit DB Persistence

This optional Supabase/Postgres persistence-only surface stores deterministic
`PaperTradeCostAuditReport` snapshots. It is paper-only, report-only, and
readonly. The default table is `paper_trade_cost_audit_reports`.

This remains default-off and env-driven. There are no DSN CLI flags.

## Phase 1 Local DB Contract

Phase 1 durable DB persistence and readback are allowed only against a local
Supabase/Postgres instance. The DB URL must be a raw Postgres DSN read from
process environment only, and the raw DSN must pass
`validate_local_postgres_dsn` before any store, adapter, migration helper, or
readback path opens a connection.

Hosted Postgres and external database services are out of scope. SQLite, Redis,
Mongo, SQLAlchemy-managed engines, ORM-managed engine factories, non-Postgres
datastores, and any externally hosted DB connection are forbidden for this
persistence/readback surface.

The DSN must not be accepted through CLI flags, positional arguments, config
files, checked-in examples, generated reports, logs, exception messages, or
tracebacks. Errors may identify that local DSN validation failed, but they must
redact credentials, hosts, ports, database names, query strings, and any other
raw DSN material.

## Environment

Set these variables at the process edge when paper trade cost audit DB
persistence should be enabled:

```text
POLYMARKET_ALPHA_LAB_PAPER_TRADE_COST_AUDIT_DB_ENABLED
POLYMARKET_ALPHA_LAB_PAPER_TRADE_COST_AUDIT_DB_DSN
POLYMARKET_ALPHA_LAB_PAPER_TRADE_COST_AUDIT_DB_TABLE
```

`POLYMARKET_ALPHA_LAB_PAPER_TRADE_COST_AUDIT_DB_ENABLED` accepts only `1`,
`true`, `0`, `false`, or a blank value. The DSN is required only when the DB is
enabled. The table value must be a lowercase identifier with an optional
lowercase schema prefix.

`.env.example` intentionally keeps these values blank. Do not add a sample DSN,
credential, wallet value, private key, or account identifier to example env
files or docs.

## Table

The default table is `paper_trade_cost_audit_reports`. The persisted row stores
the report digest, generation timestamp, config version, trade count, cost
summary scalars, the full report payload as `payload_json`, and hard boundary
flags:

```text
paper_only = true
report_only = true
readonly = true
```

`payload_json` is canonical and read-only. The scalar columns are query aids for
filtering and ordering paper trade cost audit reports without unpacking the full
JSON payload.

Checks enforce lowercase digest shape, nonnegative counts, valid decimal
summary values, JSON object payloads, and the hard `paper_only`,
`report_only`, and `readonly` flags.

## Scope Boundary

This is not an execution, market-data, or trading path. It stores and loads
paper trade cost audit reports only.

There is no live trading. There is no auth. There is no wallet access. There
are no private keys. There are no account reads. There is no order
construction. There is no signing. There is no order submission. There is no
cancellation. There is no replacement. There is no order mutation. There is no
exchange mutation.

The config may read process environment values, validate them, and return a
frozen dataclass. Store and adapter code may connect only to local
Supabase/Postgres after `validate_local_postgres_dsn` accepts the env-provided
raw DSN, then insert or load paper trade cost audit rows only. These paths must
not authenticate exchange clients, read exchange accounts, construct orders,
sign payloads, submit orders, cancel orders, replace orders, mutate orders, or
mutate the exchange.
