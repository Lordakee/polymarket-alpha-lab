# Strategy Candidate Research Queue History DB Persistence

This persistence-only surface stores deterministic
`PaperStrategyCandidateResearchQueueHistoryReport` snapshots in Supabase. It is
paper-only, report-only, and readonly. The default table is
`paper_strategy_candidate_research_queue_history_reports`.

The reducer lives in
`polymarket_alpha_lab.strategy_candidate_research_queue_history` and produces
`PaperStrategyCandidateResearchQueueHistoryReport`. The row codec lives in
`polymarket_alpha_lab.strategy_candidate_research_queue_history_db_row` and
materializes `PaperStrategyCandidateResearchQueueHistoryDbRow`.

## Environment

Set these variables at the process edge when history DB persistence should be
enabled, including when the CLI is run with `--persist`:

```text
POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED
POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN
POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_TABLE
```

`POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED`
accepts only `1`, `true`, `0`, `false`, or a blank value. The DSN is required
only when the history DB is enabled. The table value must be a lowercase
identifier with an optional lowercase schema prefix.

Do not add sample DSN values, credentials, wallet values, private keys, account
identifiers, or environment contents to examples or logs. Error paths and CLI
output must redact the DSN and must not print DSNs, table names, payload JSON,
raw DB records, secrets, or env contents.

## Migration

The Supabase migration creates only
`public.paper_strategy_candidate_research_queue_history_reports`. The table
stores scalar history metrics, latest primary reason-code counts as `jsonb`,
latest reason-code lists as `jsonb`, the full report payload as `jsonb`, and
hard boundary flags:

```text
paper_only = true
report_only = true
readonly = true
```

Checks enforce lowercase digest shape, nonnegative counts and total notional,
score bounds, JSON object and array shapes, latest status and next-step
consistency, and empty-history null fields when `source_report_count = 0`.

## CLI Command

`polymarket-alpha-lab strategy-candidate-research-queue-history` reads
already-persisted strategy candidate research queue reports from the source
strategy candidate research queue read-only DB config and builds an
aggregate-only summary with
`PaperStrategyCandidateResearchQueueHistoryReport`.

Without --persist, the command emits only the redacted aggregate-only summary.
It does not write history rows unless --persist is provided. With --persist, it
persists only the generated aggregate history report row through the
strategy candidate research queue history DB config. The persisted row is the
same paper-only, report-only, readonly history artifact described by this
migration.

The `--persist` flag remains within the same exclusions listed in the Scope
Boundary. Command output is a redacted aggregate-only summary. It must not print
DSNs, table names, payload JSON, raw DB records, secrets, or env contents.

## Scope Boundary

Strict Phase 1 boundary: this is not an execution path. It provides persistence
primitives for paper history reports only.

There is no live trading. There is no auth. There is no wallet access. There
are no private keys. There are no account reads. There is no order
construction. There is no signing. There is no order submission. There is no
cancellation. There is no replacement. There is no exchange mutation.

The history DB config may read process environment values, validate them, and
return a frozen dataclass. Store and adapter code may persist or load report
rows only. The CLI may write only the generated history report row when
`--persist` is supplied. They must not construct orders, authenticate clients,
read exchange accounts, sign payloads, submit orders, cancel orders, replace
orders, or mutate the exchange.
