# Strategy Risk Audit DB Persistence

This optional Supabase/Postgres persistence-only surface stores deterministic
`PaperStrategyRiskAuditReport` snapshots. It is paper-only, report-only, and
readonly. The default table is `strategy_risk_audit_reports`.

This remains a persistence-only boundary. The surface is default-off and
env-driven: it reads process environment config only when persistence is
enabled. There are no DSN CLI flags.

## Environment

Set these variables at the process edge when strategy risk audit DB persistence
should be enabled:

```text
POLYMARKET_ALPHA_LAB_STRATEGY_RISK_AUDIT_DB_ENABLED
POLYMARKET_ALPHA_LAB_STRATEGY_RISK_AUDIT_DB_DSN
POLYMARKET_ALPHA_LAB_STRATEGY_RISK_AUDIT_DB_TABLE
```

`POLYMARKET_ALPHA_LAB_STRATEGY_RISK_AUDIT_DB_ENABLED` accepts only `1`,
`true`, `0`, `false`, or a blank value. The DSN is required only when the DB is
enabled. The table value defaults to `strategy_risk_audit_reports` and must be a
lowercase identifier with an optional lowercase schema prefix; each identifier
part must fit the 63-byte Postgres identifier limit.

Do not add sample DSNs, credentials, wallet values, private keys, account
identifiers, or other secrets to example env files or docs.

## Table

The Supabase migration creates only `public.strategy_risk_audit_reports`. The
table stores the report digest, generation timestamp, config version, audit
status/count scalars, gate results as `gate_results_json`, the full report
payload as `payload_json`, and hard boundary flags:

```text
paper_only = true
report_only = true
readonly = true
```

`payload_json` is the canonical report payload and must be treated as read-only.
The scalar columns are query aids for filtering and ordering strategy risk audit
reports without unpacking the full JSON payload:

```text
generated_at
config_version
status
gate_count
pass_count
fail_count
incomplete_count
```

Checks enforce lowercase digest shape, known audit status values, nonnegative
counts, gate count parity, JSON array gate results, JSON object payloads,
payload/scalar parity, and the hard `paper_only`, `report_only`, and `readonly`
flags.

## Scope Boundary

This is not an execution, market-data, or trading path. It stores and loads
paper/report snapshots only.

There is no live trading. There is no auth. There is no wallet access. There are
no private keys. There are no account reads. There is no order construction.
There is no signing. There is no order submission. There is no cancellation.
There is no replacement. There is no exchange mutation.

The config may read process environment values, validate them, and return a
frozen dataclass. Store and adapter code may connect to Supabase/Postgres and
insert or load strategy risk audit rows only. These paths must not add DSN CLI
flags, authenticate exchange clients, read exchange accounts, construct orders,
sign payloads, submit orders, cancel orders, replace orders, or mutate the
exchange.
