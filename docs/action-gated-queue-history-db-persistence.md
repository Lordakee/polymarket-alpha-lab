# Action-Gated Queue History DB Persistence

This persistence-only surface stores deterministic
`PaperActionGatedStrategyRecommendationQueueHistoryReport` snapshots in Supabase.
It is paper-only, report-only, and readonly. The default table is
`paper_action_gated_strategy_recommendation_queue_history_reports`.

## Environment

Set these variables at the process edge when history DB persistence should be
enabled:

```text
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_HISTORY_DB_ENABLED
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_HISTORY_DB_DSN
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_HISTORY_DB_TABLE
```

`POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_HISTORY_DB_ENABLED` accepts only
`1`, `true`, `0`, `false`, or a blank value. The DSN is required only when the
history DB is enabled. The table value must be a lowercase identifier with an
optional lowercase schema prefix, such as
`public.paper_action_gated_strategy_recommendation_queue_history_reports`.

`.env.example` intentionally contains blank variables only. Do not add a sample
DSN, credential, wallet value, private key, or account identifier to that file.

The `action-gated-queue-history --persist` CLI path uses this environment
boundary only after it has loaded source paper queue reports and built the
aggregate history report. Without `--persist`, the CLI does not write history
rows. With `--persist`, it stores only the aggregate history report and keeps
CLI output redacted and aggregate-only.

## Migration

The Supabase migration creates only
`public.paper_action_gated_strategy_recommendation_queue_history_reports`. The
table stores scalar history metrics, the latest reason-code counts as `jsonb`,
the full report payload as `jsonb`, and hard boundary flags:

```text
paper_only = true
report_only = true
readonly = true
```

Checks enforce lowercase digest shape, nonnegative counts and total notional,
JSON object payloads, latest status and next-step consistency, and empty-history
null fields when `source_report_count = 0`.

## Scope Boundary

This is not an execution or trading path. It provides persistence primitives for
paper history reports only.

There is no live trading. There is no auth. There is no wallet access. There are
no private keys. There are no account reads. There is no order construction.
There is no signing. There is no order submission. There is no cancellation.
There is no replacement. There is no exchange mutation.

The history DB config may read process environment values, validate them, and
return a frozen dataclass. Store and adapter code may persist or load report
rows only. They must not construct orders, authenticate clients, read exchange
accounts, sign payloads, submit orders, cancel orders, replace orders, or mutate
the exchange.
