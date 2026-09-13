# Resolution worklist and one-shot candidate collection

## What this adds

The project can now list its own registered markets that have no captured
outcome, then explicitly collect a bounded batch of fresh Gamma observations.
It reuses the operator-confirmed resolution gate and append-only evidence store:

**Registered market -> worklist -> opt-in public snapshot -> unconfirmed review
-> independent operator confirmation (separate API) -> existing evaluation.**

There is no new database, migration, file journal, model call, automatic outcome,
recurring schedule, background worker or trade. Use the project-private native
PostgreSQL instance, not a caller-chosen external service. The existing 63
migration files and their manifest are unchanged. A source workspace already at
the resolution-review schema needs no new SQL migration for this node.

## Operator commands

After normal project initialization, the default command reads metadata only:

```powershell
.\.venv\Scripts\python.exe scripts/review_resolution_queue.py
```

This uses `ProjectPostgres.session()`: it may start the already-initialized
private server for the query, and stops only a server it started itself. It does
not initialize a database. Pending migrations or failed instance checks block.
No public fetch happens without both flags below:

```powershell
.\.venv\Scripts\python.exe scripts/review_resolution_queue.py --collect --allow-public-fetch --max-requests 10
```

The second command makes public Gamma GETs and writes **unconfirmed evidence**
to the existing native PostgreSQL store. It does not authenticate exchange
accounts, call a model or independently confirm an outcome. Each request uses
the existing fixed-origin, no-redirect Gamma reader. Snapshot bodies remain
untrusted. A closed flag or 0/1 price is not a verified outcome.

Both commands print metadata-only JSON and exit. Raw snapshots, source texts,
operator attestations, passwords and DSNs are excluded from this output. Use the
existing explicit `inspect_resolution(review_id=...)` API to inspect retained
raw evidence privately. Do not redirect business history into a new file journal.

## Selection and counts

All registered markets lacking a visible captured outcome are included, not
only markets with successful forecasts. The worklist uses one read-only
repeatable-read database snapshot and the database clock. Registration, review,
attempt, claim and outcome visibility use that same time. No user-supplied
historical/future selection clock is accepted.

| State | Meaning / next action |
| --- | --- |
| `fetch_due` | Forecast cutoff reached with no check, pending-check interval elapsed, or candidate snapshot expired. Eligible for this one-shot collector. |
| `waiting` | A previous pending check is still inside the configured refresh interval. |
| `needs_confirmation` | Fresh canonical binary hints exist. Operator must independently confirm the result and actual resolution time. |
| `blocked_review` | Latest check is contradictory, malformed or unsupported. Inspect it; the batch does not automatically retry it. |
| `awaiting_cutoff` | Prospective forecast cutoff not yet reached; do not fetch here yet. |
| `unsupported_market` | A legacy noncanonical condition ID remains visible, but is not sent to the public reader. |

The forecast cutoff determines when a status check becomes eligible; it is NOT
the event's end date or proof of resolution. The latest visible review is chosen
by `checked_at DESC, recorded_at DESC, review_id DESC`, and its full canonical
payload/hash is decoded and its assessment recomputed. Older reviews remain
stored but are not all audited by this view. Recorded outcomes are omitted from
the worklist; this omission does not independently verify their source truth.

A pending check's interval defaults to 300 seconds, configurable from 60 to
86,400. Candidate confirmation freshness uses the existing 600-second bound
from **snapshot fetched_at**, not its later check/receipt time. At exactly 600
seconds the gate still accepts freshness; after it expires the item is due for
a new snapshot, and any new confirmation must bind to that snapshot's hash.

Order is earliest forecast cutoff, then condition ID. The default complete-list
bound is 1,000 unresolved markets; `--max-markets` may lower this. Above the bound,
or above 16 MiB of latest-review payloads, the query fails before loading bodies.
It never returns a silently truncated list. Total registered/settled/unresolved
counts are distinguished. Per-market attempt counts include failed/blocked
attempts; incomplete claims are counted separately. A **global incomplete
execution count includes already-settled markets too**, so an empty worklist
cannot imply complete execution history. The existing evaluator still refuses
incomplete history; the queue does not repair claims or generate a quality score.

## Batch, failures and races

`--max-requests` is 1..20 (default 10). Failures consume the same request allowance
as successes. The report lists every attempted market and the number of due
markets not selected because of that bound. Requests are sequential and there
are no retries, continuation threads or recursive calls. No DB transaction is
kept open while HTTP runs; each review is captured in its own existing short
transaction. Per-request socket timeouts are not a universal run deadline.

Each valid transport snapshot, even malformed JSON, is retained as pending,
blocked or needs-confirmation evidence. No confirmation input is exposed to
this collector; it cannot return `ready` or create an evaluation outcome.
A transport failure has no genuine snapshot: it returns a fixed failure code,
not a made-up empty JSON evidence row. Transport failure history is NOT durable
in this first slice. Persistently failing oldest markets can use the batch cap
repeatedly; inspect/fix those failures rather than assuming a fleet scheduler
will rotate them. `unprocessed_due_count` describes the original selection,
not a fresh post-collection queue. Rerun the read-only command to see new states.

A capture error yields `capture_failed`, not a committed receipt. The Python
result retains the exact immutable submission in memory for explicit retry via
`session.record_resolution(submission=attempt.submission)`. Do not regenerate
its timestamp or repeat the public fetch to retry an uncertain commit. A
byte-identical retry preserves the original receipt. The CLI does not persist
this recovery object; losing it requires inspection, not a false success claim.

A worklist is NOT an execution claim/lease. Two collectors using the same session
can select/fetch the same event, or an operator can confirm an outcome after
selection. Additional unconfirmed observations may then be retained; no outcome
is overwritten and the next listing omits that settled event. This is not
exactly-once network delivery, an aggregate fleet quota or a scheduling service.
Unconfirmed stale snapshots remain distinguishable from human-approved outcomes.

## Python integration

```python
from pathlib import Path
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres

with ProjectPostgres(Path(project_root)).session() as research:
    worklist = research.resolution_worklist(max_markets=1000)
    # Explicitly authorize public requests AND unconfirmed evidence storage.
    result = research.collect_resolution_candidates(
        allow_public_fetch=True, max_requests=10, recheck_after_seconds=300,
    )
    metadata = result.to_dict()
    # For a capture_failed attempt, retain its original submission in memory and
    # inspect/retry storage explicitly; never invent a confirmation or outcome.
```

## Acceptance and remaining scope

Offline tests use synthetic snapshots and transaction doubles. The opt-in native
Windows proof uses a fresh private PostgreSQL instance and synthetic HTTP/model
replies, exercising actual queries, evidence storage, limits, cooldown, blocked
items, failed requests, incomplete claims, manual promotion, restart readback and
continued evaluator refusal of incomplete history. It does not touch a user DB or
use live provider credentials. Actual counts/revisions are recorded in the PR.

This is not automatic chain/oracle finality, authenticated source verification,
confirmed-outcome correction, continuous polling, calibration fitting, or a
prediction of trading profitability. Existing Phase 1 boundaries remain intact.

Primary API reference (checked 2026-09-13):
https://docs.polymarket.com/api-reference/markets/get-market-by-slug
