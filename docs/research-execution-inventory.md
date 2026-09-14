# Read-only execution claim inventory

## Find task IDs without running anything

The single-task inspector needs a record ID. This companion lists ALL visible
execution claims in a bounded, consistent read, including missing results. It
uses the project-private native PostgreSQL instance and existing claim/result
codecs; it is not a scheduler, new backend, market selector or model launcher.

After the existing locked postgres environment has been installed, run from an
already initialized project or pass the original actual project root explicitly:

```powershell
.\.venv\Scripts\python.exe scripts/list_project_research.py
.\.venv\Scripts\python.exe scripts/list_project_research.py --root "C:\path\to\actual-project"
```

Use the root containing the original initialized `.local/postgres`, not an
extraction wrapper. Do not copy `.local`, overlay a new kit or initialize a new
instance to make a read succeed. This command has no initialization, migration,
restore, retry, historical-time, DSN, model or public-fetch argument. Help and
invalid arguments do not construct a manager. No SQL migration is needed.

The manager can start a stopped owned server for this read and stops only one it
started. A previously running managed instance remains running. Engine logs/WAL
can change normally; read-only means no application business-record writes, not
an unchanged database directory at the byte level.

## One complete bounded snapshot, not a latest-N sample

`--max-records` defaults to 1,000 and accepts 1..1,000. It is an admission limit,
not a query LIMIT: more visible claims causes a block with `inventory=null`.
There is no silent truncation, success-only filter, incomplete-only filter or
pagination in this first inventory. Never increase it by editing a guard to
obtain an apparently complete report.

Claim count, matching-result count, aggregate payload sizes, standalone-attempt
count and both payload sets use one existing read-only REPEATABLE READ transaction.
Counts cannot describe one concurrent state while the detail rows describe another.
A task/result committed after that transaction's snapshot appears on the next
read, not midway through this one. The report is not a continuously live view.

Before reading payload bodies, the loader checks the claim count and the combined
request/result UTF-8 byte size against the existing 32-MiB read bound. The sums
apply to claims and their matching results, not unrelated standalone attempts.
Queries have the existing statement/lock timeouts; aggregate scans can still be
costly on a large database. There is no per-record query or network/model call.

The database clock labels the report. A visible claim or matched result stamped
after that clock causes `research_execution_inventory_future_record`, rather
than being silently omitted after a clock regression or bad timestamp. No caller
historical date is accepted and no claim age determines worker liveness.

Each loaded claim/result is decoded, content-hash checked and bound through the
same original request/record validation as the single-task inspector. Counts and
loaded byte lengths must match the earlier aggregates. Invalid links, flags,
hashes or cardinalities fail the entire read; there is no partial-result fallback.

## States, counts and limits of interpretation

Exit 0 / `status=listed` means the inventory and session cleanup completed. It
does not imply that research succeeded or that forecasts are good. Nested states:

| inventory_status | Meaning |
| --- | --- |
| no_claims | No execution claims in this snapshot; NOT necessarily an empty database. |
| incomplete_claims_present | At least one claim has no captured result; investigate without rerunning it. |
| all_claims_have_results | Every visible claim has a valid bound result, including failed/blocked ones. |

`claim_count = captured_result_count + incomplete_claim_count`. Rows sort by
claim time ascending and then record ID. `state_counts` separates completed,
failed, model-blocked, intake-blocked and not-yet-captured results. A settled
market's incomplete claim remains visible: the inventory never filters on outcomes.

`unclaimed_attempt_count` separately counts standalone attempts that have no claim
of the same record ID. These legacy rows are NOT decoded, certified or scored by
this read. They are not silently treated as execution claims. Markets and outcomes
are not inventoried; use the separate resolution worklist or strict evaluator.

`claim_inventory_complete=true` refers only to all visible claims in the one read
snapshot. `entire_history_checked=false` remains explicit: this is not a global
historical audit, provider authentication, event-finality check or validation of
standalone attempts. An incomplete claim still blocks the original evaluator;
absence of incomplete claims does not guarantee that every other scoring check
will pass. Unregistered work cannot be inferred from these tables.

No result is not the same as zero model calls or a dead worker. Unavailable result
times, hashes and usage remain null, worker liveness stays unknown and automatic
retry is never permitted. No worker process is inspected or killed. To inspect a
particular listed claim, use the existing command once with its ID:

```powershell
.\.venv\Scripts\python.exe scripts/inspect_project_research.py --record-id YOUR_RECORD_ID
```

This output reuses the inspector's metadata: original request/record hashes,
identity labels, timestamps, source counts, configured limits and stored usage.
It excludes source text/URLs, question/rules, model summaries, probabilities,
confidence, tool traces and raw API bodies. Labels/hashes can still be sensitive;
stdout is not anonymized data or authorization for uploading business history.
The command writes no new file-backed report or journal.

## Failures and acceptance

Argument errors exit 2. Inventory count/byte caps and future receipts return exit1,
`status=blocked` and no inventory. Other read/validation/cleanup errors return exit1
with fixed `research_execution_inventory_failed`, without raw DSN/path/exception
text. Success is emitted only after the managed session exits. Interrupts propagate.
No automatic retries, repairs, claim resets or fallback queries are performed.

Offline tests exercise mixed states, aggregate caps before body reads, corrupt
payloads/links, stable ordering, missing-vs-zero, metadata privacy and cleanup
failures. The opt-in native test commits a new claim on a separate connection
between the count and payload queries, verifying that the current inventory
retains its snapshot and a subsequent one sees the new claim. It also covers
standalone attempts, missing results, actual CLI bounds, record identity, restart
and unchanged strict evaluation refusal. The actual extracted-kit test invokes
this shipped CLI in its own environment. All business inputs are synthetic;
measured revisions/counts are recorded in the PR, not inferred from skips.

PostgreSQL snapshot semantics (reviewed 2026-09-14):
https://www.postgresql.org/docs/17/transaction-iso.html#XACT-REPEATABLE-READ
