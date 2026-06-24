# Action-Gated Queue Decision-Support DB Persistence

This persistence-only surface stores deterministic composite snapshots made from
`PaperActionGatedStrategyRecommendationQueuePriorityReport` and
`PaperActionGatedStrategyRecommendationQueueRiskReport`. It is paper-only,
report-only, and readonly. The default table is
`paper_action_gated_queue_decision_support_reports`.

## Environment

Set these variables at the process edge when decision-support DB persistence
should be enabled:

```text
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN
POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE
```

`POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED` accepts
only `1`, `true`, `0`, `false`, or a blank value. The DSN is required only when
the decision-support DB is enabled. The table value must be a lowercase
identifier with an optional lowercase schema prefix, such as
`public.paper_action_gated_queue_decision_support_reports`.

`.env.example` intentionally contains blank variables only. Do not add a sample DSN, credential, wallet value, private key, or account identifier to that file.

## Migration

The Supabase migration creates only
`public.paper_action_gated_queue_decision_support_reports`.
The table stores scalar priority metrics, scalar risk metrics, risk reason codes
as `jsonb`, full priority and risk report payloads as `jsonb`, and hard boundary
flags:

```text
paper_only = true
report_only = true
readonly = true
```

Checks enforce lowercase snapshot digest shape, nonnegative counts, nonnegative
notional and score values, JSON array reason codes, JSON object payloads, risk
status and next-step consistency, priority status-count consistency, and hard
flags.

Priority and risk payloads must be generated from the same source queue set.
Shared scalar source counts are enforced by the row codec and migration.
Detailed risk summary fields remain hydrated from JSON payloads, so consumers
should recover the risk report payload when they need the full risk summary.

## Scope Boundary

This is not an execution or trading path. It provides persistence primitives for
paper decision-support reports only.

There is no live trading. There is no auth. There is no wallet access. There
are no private keys. There are no account reads. There is no order construction.
There is no signing. There is no order submission. There is no cancellation.
There is no replacement. There is no exchange mutation.

The decision-support DB config may read process environment values, validate
them, and return a frozen dataclass. Store and adapter code may persist or load
report rows only. They must not construct orders, authenticate clients, read
exchange accounts, sign payloads, submit orders, cancel orders, replace orders,
or mutate the exchange.
