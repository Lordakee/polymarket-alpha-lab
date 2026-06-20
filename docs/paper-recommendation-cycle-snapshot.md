# Paper Recommendation Cycle Snapshot

This page documents the paper recommendation cycle snapshot,
Supabase/Postgres-first persistence, and trend layer. The layer is paper-only,
report-only, and read-only/readonly. The phase boundary is explicit:
paper-only/report-only/read-only. It summarizes already-built local paper
reports; it does not fetch market data, perform live trading, authenticate,
read accounts, mutate accounts, read wallets or private keys, sign payloads,
construct exchange orders, submit orders, place orders, cancel orders, mutate
clients, mutate networks, or provide trade instructions or financial advice.

A snapshot, persisted snapshot row, optional JSONL debug row, trend status,
reason code, artifact status, or blocked/watch/pass result is a local report
artifact only. It may help future paper-review workflows understand whether a
paper cycle was complete, consistent, cost-aware, and ready for human
inspection, but it is not an approval workflow, live execution signal, or
exchange-facing payload.

A DB-backed review or trend CLI is observability over persisted paper evidence.
It is not approval, execution, order management, live account review, or
permission to move from paper reports into exchange-facing behavior.

## Purpose

The paper recommendation pipeline produces a sequence of reducer outputs:
side-edge reports, queue reports, cost/liquidity/settlement/outcome/calibration
gates, gate summaries, allocation reports, research packets, manifest checks,
consistency checks, health reports, readiness reports, pipeline reports, and
cycle bundle reports. Those artifacts are intentionally heterogeneous. Each one
has its own fields, row vocabulary, and local validation rules.

The cycle snapshot layer converts that arbitrary artifact set into a stable
typed report surface:

- a pipeline rollup with stage count and final status;
- an artifact index with canonical artifact names, item counts, status counts,
  flags, and reason codes;
- a cycle snapshot report with the cycle timestamp, config version,
  `pass`/`watch`/`blocked` final status, stage count, artifact count,
  blocked/watch artifact counts, and normalized reason codes.
- a database-first persistence record in Supabase/Postgres for durable local
  history and later readonly trend/report queries.

This keeps later local observability from depending on every reducer's full
shape. Trend, history, dashboards, and audit summaries can read the stable
snapshot fields instead of reopening arbitrary bundle artifacts and re-deriving
status rules.

## Placement

The DB-backed review path starts with the strategy cycle and keeps each later
step inside the paper-report boundary:

```text
strategy cycle
-> rich paper recommendation artifacts
-> artifact index + pipeline report
-> cycle snapshot
-> Supabase/Postgres persistence
-> DB-backed review/trend CLI
```

The strategy cycle answers: "Which local paper reports were produced for this
cycle, including cost-aware and screening evidence that was already available
in memory?"

The rich paper recommendation artifacts answer: "Which paper-only/report-only
recommendation, cost, readiness, queue, allocation, research, manifest,
consistency, health, and bundle reports should be indexed for this cycle?"

The pipeline report answers: "Did each supplied reducer stage finish as
`pass`, `watch`, or `blocked`?"

The artifact index answers: "Which supplied paper artifacts exist for this
cycle, how many rows/items do they contain, what status did each artifact
report, and which reason codes or safety flags are attached?"

The cycle snapshot answers: "For this generated-at cycle timestamp, what is the
stable paper-only/report-only/readonly cycle state after combining the pipeline
rollup with the artifact index?"

The persistence layer answers: "Which already-built snapshots were durably
recorded in the local Supabase/Postgres store for later readonly inspection?"
This is local Supabase/Postgres persistence at a high level only; documents,
logs, and CLI output should not include real DSNs, passwords, tokens, service
keys, wallet material, or other secrets.

The DB-backed review/trend CLI answers: "Across persisted local paper
snapshots, how often did the paper cycle pass, watch, or block, what is the
latest status, whether blocker pressure is increasing, and which reason codes
or required artifacts explain the trend?" It must load persisted snapshot
history only for read-only observability and must not approve, submit, cancel,
sign, allocate real capital, read accounts, mutate accounts, or construct order
payloads.

Optional JSONL export/debug may still exist after persistence as a non-primary
diagnostic copy, but it is outside the required DB-backed review path and
should not become the source of truth for normal trend or history reads.

## Snapshot Contract

The snapshot should be built only from already-materialized local paper reports.
It should receive a `PaperRecommendationPipelineReport` and a
`PaperRecommendationArtifactIndexReport` or exact report-shaped equivalents
approved by the implementation. It must not recover missing reports by reading
live services, repository state, external APIs, account state, wallet state, or
exchange state.

The snapshot report should preserve these invariants:

- `generated_at` is a concrete `datetime` normalized to UTC.
- `config_version` is a canonical nonblank string.
- nested pipeline and artifact-index reports have exactly matching
  `generated_at` values.
- every nested report crossing the snapshot boundary has
  `paper_only=True`, `report_only=True`, and `readonly=True`.
- status vocabulary is `pass`, `watch`, and `blocked`.
- blocked status takes precedence over watch, and watch takes precedence over
  pass.
- `stage_count` matches the nested pipeline report.
- `artifact_count`, `blocked_artifact_count`, and `watch_artifact_count` match
  the nested artifact index.
- reason codes are canonical, deterministic, deduplicated, and derived from
  pipeline final status, artifact-index status, and indexed artifact reasons.

The snapshot should fail closed. If nested timestamps differ, safety flags are
missing, nested reports are the wrong type, counts disagree, status values are
outside the paper vocabulary, or reason codes are malformed, the correct result
is a local validation failure rather than an inferred pass.

## Persistence Contract

Supabase/Postgres is the primary persistence target for already-built cycle
snapshots. Persistence should be local evidence for report history: one fully
validated snapshot record per completed paper cycle, plus any normalized child
records or JSON payload columns the implementation explicitly defines for
artifact status, reason codes, and trend inputs.

Database-first persistence rules:

- validate the complete snapshot before opening a database transaction;
- persist only caller-supplied, already-materialized paper report values;
- store `datetime` values as concrete UTC timestamps;
- preserve exact numeric values without binary-float coercion;
- use deterministic canonical keys, status vocabulary, reason-code vocabulary,
  and config version values;
- keep writes scoped to paper snapshot/report history tables;
- reject partial writes with a failed transaction if any nested report,
  timestamp, status, count, reason code, or safety flag is invalid;
- treat persisted rows as report evidence, not as commands or decisions;
- keep read helpers readonly and explicit about which local tables or views they
  query.

Postgres rows are for local audit continuity and trend/report queries only.
Inserting a snapshot must not change strategy behavior, mutate a client, write
an order ticket, mark a trade as approved, allocate real capital, or communicate
with external services beyond the configured local Supabase/Postgres runtime.

## Optional JSONL Export/Debug

JSONL, if retained, is a non-primary export/debug surface. It may be useful for
manual inspection, one-off regression fixtures, or portability of already-built
snapshot evidence, but it must not replace Supabase/Postgres as the primary
history store.

JSONL export/debug rules:

- export only a fully validated snapshot or a readonly result loaded from the
  primary database;
- serialize `datetime` values as UTC ISO strings;
- serialize exact numeric values as strings if JSON cannot represent them
  safely;
- write JSON with deterministic keys and no non-finite numeric values;
- write only to a caller-selected local path;
- never scan directories, infer snapshots from arbitrary files, repair invalid
  rows, refresh inputs, or load live data;
- keep JSONL readers, if added for debugging or fixture loading, readonly and
  line-numbered in their error messages;
- do not use JSONL as the normal trend source unless a separate local
  debug/test plan explicitly passes those rows to a readonly reducer.

Exporting or reading JSONL must not change strategy behavior, mutate a client,
write an order ticket, mark a trade as approved, allocate real capital, or
communicate with external services.

## Local Runtime Findings

Local persistence work should account for these environment findings observed
so far:

- Supabase CLI binary: `/home/ubuntu/supabase/node_modules/.bin/supabase`
- self-hosted Supabase stack path: `/home/ubuntu/supabase-selfhost`
- exposed local container ports include Kong on `8000`/`8443` and the Postgres
  pooler on `5432`/`6543`
- `psql` is not currently on the host `PATH`
- Docker access for the current user requires `sudo -n`

Do not record secrets, service-role keys, JWT secrets, database passwords,
wallet material, private keys, or `.env` values in this document, snapshot rows,
debug exports, plans, tests, or logs.

## Trend Contract

The trend reducer should consume supplied historical snapshots or compatible
cycle reports that already carry `generated_at`, `final_status`, a count field
such as `stage_count` or `artifact_count`, and hard safety flags. Normal history
should come from the DB-first Supabase/Postgres persistence surface or from
explicitly supplied in-memory reports. It should not discover history on its
own.

Expected trend outputs:

- source report count;
- pass/watch/blocked counts;
- first and latest generated-at timestamps;
- average stage/artifact count;
- blocked share;
- latest status;
- optional future reason-code movement summaries when persisted history exposes
  enough stable reason-code history.

Trend status is paper observability only. It can show that recent cycles are
blocked more often, that a blocker persists, or that the latest cycle is watch,
but it must not promote a paper recommendation, approve a row, rank
investments, create order intent, or provide trade instruction.

## Cost Assumption Artifacts

Cost reducers must be upstream artifacts before snapshot construction. This is
required so future paper recommendation reports account for frictions before a
cycle is summarized.

At minimum, the artifact set should include paper-only/report-only/readonly
outputs for:

- spread and bid/ask execution quality;
- executable depth and shallow-depth penalties;
- modeled slippage or liquidity cost;
- taker fee assumptions and any maker/rebate assumptions that affect the paper
  comparison;
- funding, carrying, time, finalization, settlement, and risk costs where
  supplied;
- external frictions supplied as paper inputs, such as deposit, withdrawal,
  bridge, network, gas, relayer, intermediary, or opportunity-cost assumptions.

The snapshot layer should not calculate these costs itself and should not fetch
or infer them from accounts, wallets, chains, exchanges, relayers, or brokers.
If a future caller wants those frictions reflected in paper recommendation
decisions, the caller must first include the relevant fee/external-cost reducer
reports in the artifact index and cycle bundle. The snapshot then records
whether those cost artifacts were present, passing, watch, or blocked.

## Verification Checklist

Before accepting a snapshot/persistence/trend implementation or wiring change,
verify:

- the entry point consumes only caller-supplied local paper reports or already
  built snapshot values;
- every generated row/report has `paper_only=True`, `report_only=True`, and
  `readonly=True`;
- nested pipeline, artifact index, and cost/friction artifacts are validated
  before snapshot construction;
- cost and external-friction reports appear in the artifact index before the
  snapshot is built;
- missing cost artifacts produce an explicit watch or blocked report state when
  the cycle contract requires them;
- generated-at consistency is enforced across reports that expose
  `generated_at`;
- artifact names are canonical and duplicate names are rejected before a pass
  state is emitted;
- status precedence is deterministic: blocked before watch before pass;
- reason codes are canonical and stable enough for future trend summaries;
- DB-first Supabase/Postgres persistence validates before opening a transaction
  and rolls back on any invalid nested report or snapshot field;
- DB writes are limited to local paper snapshot/report history tables and never
  create exchange-facing artifacts;
- optional JSONL export/debug validates before opening the target file and is
  clearly non-primary;
- optional JSONL readers, if present, are readonly and fail with clear row
  numbers on malformed data;
- trend reducers consume supplied history only and do not scan JSONL files
  unless a caller explicitly passes a local debug/test reader result;
- tests include malformed nested reports, timestamp mismatch, unsafe flags,
  count inconsistency, duplicate artifacts, malformed reason codes, empty
  histories where applicable, and no-live-boundary source checks.

## Future Wiring Checklist

Future CLI, orchestration, or runner wiring must stay inside the same boundary:

- read/write Supabase/Postgres persistence only after a separate plan approves
  the local table/view surface and transaction behavior;
- read caller-selected local JSONL files only as non-primary export/debug
  inputs after a separate plan approves the file surface;
- never construct HTTP clients, exchange clients, relayer clients, wallet
  adapters, signers, private-key readers, account readers, or order builders;
- never fetch market, order-book, balance, position, allowance, settlement,
  chain, wallet, or exchange state to fill a missing snapshot field;
- never write exchange-facing artifacts, order tickets, order intents, signed
  payloads, broker requests, or recovery commands;
- keep CLI output framed as paper-only/report-only/readonly local
  observability;
- make absent optional inputs visible as local evidence gaps rather than
  refreshing them from external systems;
- ensure pipeline, artifact index, snapshot, persistence, optional JSONL
  export/debug, and trend docs all describe outputs as research/report artifacts
  only;
- update scope tests when any new module, command, DB helper, optional JSONL
  helper, or trend helper is added.

When a required upstream artifact cannot be supplied, the wiring should record
that as a blocked or watch paper report with a reason code. It should not try to
recover by using live market access, account inspection, wallet inspection,
order-status lookup, chain queries, network calls, or browser automation.
