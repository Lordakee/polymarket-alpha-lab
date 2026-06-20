# Local Observability Trends DB Persistence

This optional Supabase/Postgres persistence-only surface stores deterministic
`LocalObservabilityTrendsReport` snapshots. It is paper-only, report-only, and
readonly. The default table is `local_observability_trends_reports`.

This is a persistence foundation only. It adds no CLI wiring; callers must opt
in explicitly from their own paper/report path.

## Environment

Set these variables at the process edge when local observability trends DB
persistence should be enabled:

```text
POLYMARKET_ALPHA_LAB_LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED
POLYMARKET_ALPHA_LAB_LOCAL_OBSERVABILITY_TRENDS_DB_DSN
POLYMARKET_ALPHA_LAB_LOCAL_OBSERVABILITY_TRENDS_DB_TABLE
```

`POLYMARKET_ALPHA_LAB_LOCAL_OBSERVABILITY_TRENDS_DB_ENABLED` accepts only `1`,
`true`, `0`, `false`, or a blank value. The DSN is required only when the DB is
enabled. The table value must be a lowercase identifier with an optional
lowercase schema prefix, such as `public.local_observability_trends_reports`.

Do not add sample DSNs, credentials, wallet values, private keys, account
identifiers, or other secrets to example env files or docs.

## Table

The Supabase migration creates only
`public.local_observability_trends_reports`. The table stores the report digest,
generation timestamp, config version, local trend status/count scalars, the full
report payload as `payload_json`, and hard boundary flags:

```text
paper_only = true
report_only = true
readonly = true
```

`payload_json` is the canonical report payload. The scalar columns are query aids
for filtering and ordering local observability trend reports without unpacking
the full JSON payload:

```text
strategy_evidence_snapshot_count
strategy_evidence_latest_status
outcome_freshness_status
outcome_report_count
nav_risk_status
nav_risk_report_count
paper_trade_cost_status
paper_trade_cost_report_count
```

Checks enforce lowercase digest shape, nonnegative counts, known local status
values, JSON object payloads, strategy evidence status/count consistency, and
the hard `paper_only`, `report_only`, and `readonly` flags.

## Scope Boundary

This is not an execution, market-data, or trading path. It stores and loads
paper/report snapshots only.

There is no live trading. There is no auth. There is no wallet access. There are
no private keys. There are no account reads. There is no order construction.
There is no signing. There is no order submission. There is no cancellation.
There is no replacement. There is no exchange mutation.

The config may read process environment values, validate them, and return a
frozen dataclass. Store and adapter code may connect to Supabase/Postgres and
insert or load local observability trend rows only. They must not authenticate
exchange clients, read exchange accounts, construct orders, sign payloads,
submit orders, cancel orders, replace orders, or mutate the exchange.
