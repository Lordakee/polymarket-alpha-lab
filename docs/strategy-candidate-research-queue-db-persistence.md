# Strategy Candidate Research Queue DB Persistence

This persistence-only surface stores deterministic
`PaperStrategyCandidateResearchQueueReport` snapshots in Supabase/Postgres. It
is paper-only, report-only, and readonly. The default table is
`paper_strategy_candidate_research_queue_reports`.

This remains a persistence-only boundary. The surface is default-off and
env-driven: it reads process environment config only when persistence is
enabled. There are no DSN CLI flags.

## Environment

Set these variables at the process edge when strategy candidate research queue
DB persistence should be enabled:

```text
POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED
POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_DSN
POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_TABLE
```

`POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_DB_ENABLED` accepts
only `1`, `true`, `0`, `false`, or a blank value. The DSN is required only when
the DB is enabled. The table value defaults to
`paper_strategy_candidate_research_queue_reports` and must be a lowercase
identifier with an optional lowercase schema prefix, such as
`public.paper_strategy_candidate_research_queue_reports`.

Do not add sample DSNs, credentials, wallet values, private keys, account
identifiers, or other secrets to example env files or docs.

## Table

The Supabase migration creates only
`public.paper_strategy_candidate_research_queue_reports`. The table stores the
report digest, generation timestamp, source queue status fields, research queue
status/count scalars, notional/score scalars, JSONB count maps, row material,
the full report payload, and hard boundary flags:

```text
paper_only = true
report_only = true
readonly = true
```

`payload` is the canonical report payload and must be treated as read-only. The
scalar columns are query aids for filtering and ordering persisted research
queue reports without unpacking the full JSON payload:

```text
generated_at
config_version
source_config_version
action_status
recommended_next_step
research_status
candidate_count
research_ready_count
watch_count
blocked_count
selected_count
skipped_count
not_selected_count
total_ready_notional
total_selected_notional
total_suggested_notional
top_research_priority_score
average_research_ready_score
```

Checks enforce lowercase digest shape, known action/research status values,
known next-step values, nonnegative counts and score/notional values, candidate
count parity across research-status and decision-status breakdowns, JSON object
shape for `source_reason_code_counts`, `primary_reason_code_counts`, and
`payload`, JSON array shape for `reason_codes` and `rows`, and the hard
`paper_only`, `report_only`, and `readonly` flags.

## Phase 1 Boundary

Phase 1 exposes both of the persistence adapters needed for deterministic
storage and read-only recovery of strategy candidate research queue reports:

- `insert_paper_strategy_candidate_research_queue_report_with_psycopg(...)`
- `load_paper_strategy_candidate_research_queue_reports_with_psycopg(...)`

The write and read adapters stay distinct on purpose:

- the write adapter owns connection lifecycle, JSONB parameter adaptation,
  commit/rollback semantics, and insert-only persistence;
- the read adapter owns autocommit read-only connections, bounded filtered
  selects, and recovery of immutable reports from stored rows.

Neither adapter expands Phase 1 beyond paper/report persistence. They do not
introduce live trading, auth, wallet access, private keys, account reads,
order construction, signing, submission, cancellation, replacement, or any
exchange mutation.

## Write/Read Relationship

Writes flow through three layers:

1. `build_paper_strategy_candidate_research_queue_report(...)` produces the
   immutable report.
2. `insert_paper_strategy_candidate_research_queue_report(...)` converts the
   report to `PaperStrategyCandidateResearchQueueDbRow`, materializes the JSONB
   fields, and issues the SQL insert.
3. `insert_paper_strategy_candidate_research_queue_report_with_psycopg(...)`
   owns the psycopg connection lifecycle, JSONB parameter adaptation,
   commit/rollback semantics, and close semantics.

Reads remain available through two aligned layers:

1. `load_paper_strategy_candidate_research_queue_reports(...)` provides the
   DB-API store read surface.
2. `load_paper_strategy_candidate_research_queue_reports_with_psycopg(...)`
   provides the read-only psycopg adapter and reconstructs immutable reports
   from stored rows via
   `paper_strategy_candidate_research_queue_report_from_db_row(...)`.

The write adapter does not replace either read path, and the read-only psycopg
module remains select-only and separate from the write adapter.

## Scope Boundary

This is not an execution, market-data, or trading path. It stores and loads
paper/report snapshots only.

There is no live trading. There is no auth. There is no wallet access. There
are no private keys. There are no account reads. There is no order construction.
There is no signing. There is no order submission. There is no cancellation.
There is no replacement. There is no exchange mutation.

The config may read process environment values, validate them, and return a
frozen dataclass. Store and adapter code may connect to Supabase/Postgres and
insert or load strategy candidate research queue rows only. These paths must
not add DSN CLI flags, authenticate exchange clients, read exchange accounts,
construct orders, sign payloads, submit orders, cancel orders, replace orders,
or mutate the exchange.
