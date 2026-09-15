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

## Confirm a retained candidate against its original BTC/ETH forecast (WP-04)

The same command now has a separate explicit confirmation mode:

```powershell
# Paste one complete, independently reviewed JSON object. Keep it in memory for
# an explicit same-input retry after an uncertain commit. Never regenerate dates.
$review = Read-Host 'Paste the reviewed confirmation JSON (ASCII or JSON Unicode escapes)'
$review | .\.venv\Scripts\python.exe scripts/review_resolution_queue.py --confirm --allow-resolution-write
$code = $LASTEXITCODE
```

`--confirm` and `--allow-resolution-write` are both required. They cannot be
combined with `--collect` or `--allow-public-fetch`. This path performs NO public
fetch and NO model call. It consumes one UTF-8 stdin object of at most 65,536
bytes; there is no file path, file-backed queue, key discovery or JSONL history.
With PowerShell 5.1 use ASCII JSON with `\uXXXX` escapes for non-ASCII evidence,
so its default pipeline encoding cannot silently alter reviewed source text.
The default listing and explicit unconfirmed collection retain their old behavior.
The existing installed environment is required; this does not initialize or
migrate a project and must not be overlaid on an old immutable kit.

### Review before sending the confirmation

Use `inspect_project_research.py --record-id ...` for the original request hash
and `inspect_project_resolution.py --review-id ...` for the candidate payload and
snapshot hashes. Use the existing typed inspection APIs privately to read the
complete original rules and retained source bytes. Metadata is not a substitute
for reviewing those bytes. Do not copy an ID/hash from a different event or
regenerate an expired candidate under a new timestamp.

The closed top-level input fields are:

| Field | Required content |
| --- | --- |
| `review_id` | New immutable confirmation review ID, different from the candidate ID. |
| `record_id`, `request_sha256` | Exact original completed forecast and its canonical request hash. |
| `candidate_review_id`, `candidate_payload_sha256` | Exact retained, unconfirmed binary candidate and its canonical payload hash. |
| `source_venue`, `source_pair` | `binance` and `BTCUSDT` or `ETHUSDT`, matching the original team's rule. |
| `source_interval`, `source_price_field` | `1m`, `close`. Coinbase/Kraken USD hourly reference feeds do not qualify. |
| `source_candle_open_at` | Aware ISO timestamp for the actual rule's minute OPEN; normalized to UTC. |
| `confirmation` | The complete operator assertion object described below. |

`confirmation` has exactly ten fields: `condition_id`, `market_slug`, `actual_yes`
(a JSON boolean, never a missing/default NO), `resolved_at`, `confirmed_at`,
`gamma_content_sha256`, `reviewer_id`, `source_reference` (an independent HTTPS
reference), `source_text` (the approved public evidence, at most 16,000 characters)
and `independently_verified` (exact JSON `true`). Both times must be explicit,
aware ISO timestamps. Unknown keys, duplicate keys, missing approvals, invalid
booleans, non-finite JSON values and over-limit input fail before project access.
The final encoded source envelope also remains subject to the existing 32,000
character cap; heavy escaping may lower the usable original-text size.

The operator must independently verify the original complete rule, actual source,
pair, interval, candle time, Close value, resulting YES/NO and resolution time.
**Venue labels, a source URL, hashes and `independently_verified=true` are assertions,
not authenticated data or independent verification by this program.** The code
checks agreement of the declared source descriptor with a narrow Binance pair
hint in the already-supported original rule; it does not fetch the reference,
parse a price from free text, certify reviewer identity or verify oracle finality.
It does not broaden the original contract/time gates or authenticate model use.

### What is bound and what remains unchanged

The service loads the original execution and original candidate through the same
managed project instance. It requires a saved completed BTC/ETH forecast, exact
request/candidate hashes, the same condition/slug, and byte-exact question/rules
between the original task and candidate snapshot. It reuses the original terminal
contract/observation-time gate. The forecast must have been recorded before its
cutoff, with cutoff before candle open. Declared minute must match; resolution
cannot precede minute close, and confirmation cannot precede candidate recording.
The existing binary/finality/disagreement/freshness checks still apply.

The source descriptor, record/request hashes, candidate ID/hash, original market
snapshot hash, computed observation metadata and original source text/hash are
retained in a canonical `crypto-settlement-attestation-v1` JSON envelope INSIDE
the existing confirmation `source_text`. No migration or new table is needed.
The original text is preserved verbatim as an embedded string; its own digest is
`original_source_content_sha256`. The normal confirmation source hash now covers
the whole envelope, while the outcome's source hash still covers the canonical
complete resolution submission. These hashes must not be confused.

The existing writer atomically saves the NEW confirmed review and linked outcome.
It leaves the original forecast and unconfirmed candidate unchanged. Inspecting
the old candidate continues to show no linked outcome. It does not rewrite failed
or incomplete forecasts, or bypass the strict original evaluator. Legacy direct
`record_resolution` / `capture_outcome` APIs remain compatible; this assembly is
not a claim that all historical outcomes used these stricter workflow checks.

The two original lookups are separate read snapshots, not an atomic whole-project
snapshot. Their rows are immutable. The existing condition lock and unique outcome
prevent concurrent confirmations from overwriting a result. Reusing the exact
instruction rebuilds the same times/payload in the same fixed software version;
existing committed replay returns its original receipt even after expiry. A new
ID cannot overwrite an outcome. There is no automatic retry, refresh or rollback
of a possibly committed result. Rule/time dependency changes across versions can
cause an old instruction to conflict; do not reinterpret old evidence to force it.

### Results, errors and acceptance

Only after managed cleanup succeeds does the console print the existing
metadata-only resolution receipt. It rechecks that the receipt binds the supplied
original record, candidate, source and assertion, not merely its new review ID.
Exit 0 means the operator-confirmed review was saved or exactly replayed, not that
the source is objectively true or the strategy is validated. Exit 1 means an
operation/validation/cleanup failure; a write may already have committed. Exit 2
means invalid input/flags or missing write opt-in, before project access. Exit 130
means interruption. Raw source text, references, reviewer IDs and exception details
are not emitted. Business IDs/hashes are still potentially sensitive metadata.

Rejected instructions are not promoted or stored as replacement outcomes. The
original candidate remains auditable, but rejected stdin/transport/CLI errors are
NOT a new durable rejection journal. Preserve and inspect the original IDs after
failure; do not manufacture a new prediction or claim finality from the exit code.
No file business persistence or parallel scoring system is introduced.

The same workflow is available to an explicitly authorized application:

```python
with ProjectPostgres(Path(actual_project_root)).session() as research:
    # instruction: a fully reviewed CryptoSettlementReview, not inferred approval.
    saved = research.confirm_crypto_resolution(
        instruction=instruction, allow_resolution_write=True,
    )
```

Offline tests: `tests/test_research_resolution_confirmation.py` and the separate
same-assistant adversarial `tests/test_research_resolution_confirmation_review.py`.
The first adversarial pass exposed three accepted-but-mismatched console receipts;
the final handler checks original instruction bindings without weakening those
assertions. This is self-review, not an external audit or a zero-defect guarantee.
The native opt-in proof `tests/test_project_postgres_confirmation_native.py` uses
real clock ordering, two synthetic prospective forecasts, waits for the declared
minute to close, invokes the actual console in child processes, checks manual
YES/NO outcomes, exact replay/restart, old-record preservation and original
assessment. It never accesses a user's data or a real provider/source.

**WP-04 remains PARTIAL and G4 remains open:** real BTC/ETH forecasts, real matching
settlement evidence and independent human verification are still required. The
known WP-06 PowerShell first-run reliability issue is not cured by this change.
Final-revision CI counts, initial failures and unexecuted checks belong in the PR.
