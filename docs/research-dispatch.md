# Durable bounded research batches (WP-03)

## Delivered slice, not an unattended scheduler

An explicit application can now persist a bounded BTC/ETH batch, drain a limited
number of pending requests, stop admitting new work, and inspect/resume the same
batch after restart. This reuses the existing request codec, project-private
PostgreSQL, instance binding, execution claim and capture-only recovery paths.
There is no file-backed queue, broker, alternate driver or implicit model choice.

**This is WP-03 partial integration, not G3/V1 completion.** There is no calendar
service, automatic fresh-market collection, global provider budget, administrative
cancellation or repair of lost model outputs. The explicit multi-batch rotation
below adds a durable cursor; it is not a recurring or fleet-wide scheduler.
WP-02 model/data/cost decisions remain required before real provider use. A run
starts only with an explicit factory and `allow_model_calls=True`; no model or
credential is discovered. This delivery is tested with synthetic models only.

## Persist first, then explicitly execute

The application supplies existing `CapturedResearchRequest` objects. For the V1
crypto workflow, build them from freshly validated `CryptoResearchPreview.request`
with independently reviewed terms. Do not treat selection JSON, queue membership,
a model label, or a boolean as authenticated approval or source verification.
This is not another contract parser: direct generic requests retain the existing
caller's responsibility for source suitability and authorization.

```python
from pathlib import Path
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_dispatch import ResearchBatch
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop

# reviewed_requests: a tuple of existing typed requests with approved public input.
# approved_model_factory: supplied by the authorized application, never a key scan.
batch = ResearchBatch(batch_id='operator-chosen-unique-id', requests=reviewed_requests)
with ProjectPostgres(Path(actual_project_root)).session() as research:
    receipt = research.enqueue_research_batch(batch=batch, allow_queue_write=True)
    before = research.inspect_research_batch(batch_id=batch.batch_id)
    stop = ResearchDispatchStop()
    result = research.run_research_batch(
        batch_id=batch.batch_id, model_factory=approved_model_factory,
        allow_model_calls=True, max_tasks=10, max_workers=2, stop=stop,
    )
    after = research.inspect_research_batch(batch_id=batch.batch_id)
    metadata = after.to_dict()
```

The queue stores all canonical inputs in one immutable row BEFORE a dispatch run.
Admission is all-or-nothing. An exact same-ID/same-payload retry returns its
original database timestamp, even after the requests expire. Changed content or
order under the same batch ID is rejected. Admission does not create markets,
claim tasks or call a model. New requests must already be prospective and fresh
against database time; the original claim checks DB time again before execution.
It never extends a cutoff or refreshes evidence to make an expired request run.

One batch has 1..100 requests, unique record and logical task identities, only
BTC/ETH teams, and at most 8 MiB encoded bytes. Every request retains the existing
2 MiB limit. Readback caps the associated claim/result bodies at 32 MiB before
loading them. These are complete reads of one specified batch, not paginated
whole-project lists. Exceeding a cap fails rather than silently truncating data.

## States and restart semantics

`inspect_research_batch` uses one repeatable-read snapshot and DB clock:

| State | Meaning |
| --- | --- |
| pending | No execution claim is visible and the original request is still startable. |
| expired | No execution claim is visible, but the cutoff/start-delay window has elapsed. Inputs remain stored. |
| incomplete | A claim exists but no result was captured. Worker liveness is unknown; never automatically reclaim. |
| captured | The original result is stored, including completed, failed or blocked research. Never execute it again. |

All request/claim/result bindings and canonical hashes are revalidated. Existing
claims may predate batch admission; an exact original request remains the same
request rather than authorizing a duplicate. A mismatched existing record blocks
readback, not adoption. Current queue state is derived, not written back into a
second execution ledger. The original evaluator is unchanged: incomplete claims
block strict history scoring, but unstarted queued inputs are not predictions and
are not counted as executed research. A complete batch is not a statistical sample
or evidence of profitability.

Each run reloads stored inputs; a caller can continue by the SAME batch ID without
reconstructing requests or preserving a process-local list. Captured/incomplete
claims are skipped. A process dying before a claim leaves a pending request; dying
after the original claim commits leaves incomplete. No age-based worker-death
inference, TTL reclaim or automatic paid-model retry is added.

## Limits, concurrency and stopping

Each explicit drain submits at most `max_tasks` pending items (1..100, default10)
in original order, with at most `max_workers` futures (1..8, default2). There is
no hidden executor backlog of the entire batch. Returned attempts retain input
order; concurrently admitted operations need not START or finish in that order.
Each worker gets its own copied context so managed database identity checks apply
inside its actual transactions. No transaction stays open over model execution.

These limits are per invocation, not process-wide/fleet/financial caps. Two
simultaneous dispatchers can select overlapping work; the existing immutable
per-request claim still controls loop start. Simultaneous requests for the same
team/model/protocol/condition may be rejected by the existing prior-incomplete
guard. This code never disables that protection to keep workers busy.

Another application thread may call `stop.request_stop()`. Once that returns,
no later admission passes this token. An operation admitted earlier may still
reach its claim/model later. Already admitted operations are joined before return;
there is no thread kill or universal elapsed-time deadline. A hung injected client
can delay shutdown, so the authorized model client must bound its own I/O. A stop
is process-local, one-way and not a durable cancellation; a new explicit run uses
a new token and reloads pending jobs from PostgreSQL.

A pre-claim database/identity failure returns `operation_failed`, not a stored
research failure and not proof that no transaction committed. Snapshot again before
another run. A persistent failure at the head can consume later run limits; this
slice does not implement durable error rotation, backoff or cross-batch fairness.
The explicit rotation below prevents this repeated head-of-line monopolization
within its fixed roster; the single-batch API deliberately retains its old FIFO
semantics. Unified operation and full WP-02 integration remain G3 gaps. Actual model/factory failures use the original captured result
and are skipped subsequently, not retried.

`capture_failed` retains the exact `execution.pending_run` only in memory for the
existing explicit `retry_capture(request=..., run=...)` API. The queue stores inputs,
not a lost output. Never reconstruct a forecast to replace a missing result. The
run report describes its selection/attempts, not a final database rescan; use
`inspect_research_batch` after a drain. A failure or interrupt cannot be reported
as a complete final snapshot. Interrupts propagate after admitted workers drain.

## Migration and operating boundaries

Original batch tail: `20260914000000_research_dispatch_batches.sql` brought the
catalog to 64 migrations. The current catalog also includes the rotation tail
described below. The original 63 SQL files are unchanged.
The new append-only table holds public/redacted request evidence; no passwords,
model clients or credentials. It rejects UPDATE/DELETE/TRUNCATE and uses the
existing restricted app role/grant procedure. SQL independently checks batch
size/hash, flags, team/identity and enqueue-time constraints; application decoding
also enforces the complete canonical request schema.

A SOURCE-based initialized project whose checked-in catalog includes this tail
requires the existing explicit `project_database.py migrate` operation before
using the batch API. There is no automatic migration in admission/inspection/run.
The native proof upgrades a disposable 63-migration source instance and verifies
its old record unchanged. This is not authorization to change a user's database.

An immutable old kit's catalog remains at its original version. Do NOT overlay a
new kit, copy `.local`, or edit its integrity manifest. Calling new code with an
old kit root does not install the missing table; it must fail rather than select
another database. WP-06 must define the safe user upgrade route before deployment.
The module/runbook are included in future newly-built kits. No new long-term
Release or existing local installation is changed by this code commit.

Queue payloads contain approved business evidence even though successful API
summaries omit source text. Metadata IDs/hashes are not anonymized. Do not upload
raw batches or business records to GitHub. No real project input or provider key
is needed for the regression/native tests.

## Acceptance evidence

Focused offline tests cover canonical copying, invalid input, exact admission
replay, consistent read bounds, selection states, stop, concurrency/context,
unknown commit failures and capture-only recovery. An opt-in native test uses
actual private PostgreSQL and production managed APIs to check explicit 63->64
migration, identical concurrent admission, multiple bounded rounds with BTC/ETH,
stop/restart, captured factory failure, expiry, SQL mutation/identity guards and a
separate Python process exiting after a real claim. The next run must preserve
that incomplete claim and execute only the remaining request. Old records and
strict evaluator behavior remain unchanged.

Actual final counts/revisions and unexecuted steps belong in the implementation
PR and DELIVERY_PLAN.md; synthetic results are not approved live provider tests.
Primary transaction/context references reviewed 2026-09-14:
https://www.postgresql.org/docs/current/transaction-iso.html
https://docs.python.org/3/library/contextvars.html


## Fair multi-batch turns with a durable cursor (WP-03)

The application can group 1..10 existing batches into a fixed rotation, with at
most100 requests and8MiB of combined canonical batch input. Batch membership and
order are immutable under `rotation_id`. Unequal lengths are interleaved by
position: A0,B0,C0,A1,B1,... . This is finite slot fairness inside this explicit
roster, not weighted team fairness or automatic discovery of all queued batches.

```python
with ProjectPostgres(Path(actual_project_root)).session() as research:
    report = research.run_research_rotation(
        rotation_id='approved-roster-1', turn_id='operator-turn-1',
        batch_ids_to_run=('approved-btc-batch', 'approved-eth-batch'),
        model_factory=approved_model_factory, allow_model_calls=True,
        max_tasks=2, max_workers=2,
    )
    original_turn = research.inspect_research_turn(
        rotation_id='approved-roster-1', turn_id='operator-turn-1',
    )
```

These names are placeholders for already admitted, independently approved inputs
and a separately authorized client, not a runnable provider configuration. No
client/credential is loaded by name, and no model call is authorized by this doc.
There is still no operator CLI that silently imports an arbitrary factory.

Each NEW turn reads bounded per-batch snapshots, then under a per-rotation DB lock
records its selection and next cursor in one append-only transaction. Only after
COMMIT and cleanup succeed may it enter the existing bounded executor. The cursor
moves past every considered slot, including a pending request whose later claim
operation fails. A later explicit turn continues after that slot instead of
repeatedly spending its entire limit on the same failing head. It scans at most
one circuit, never immediately retries inside a turn, and never refreshes inputs.
Captured/incomplete/expired slots are skipped according to their selection hints;
the original per-request claim transaction rechecks actual state and DB time.

The snapshots are SEPARATE consistent per-batch reads, not one atomic whole-roster
snapshot or a promise that pending remains pending. Claims created in the meantime
still prevent a duplicate loop. Aggregate input/result limits are checked as each
batch arrives; malformed/missing/oversized batches abort the entire turn, without
reserving a partial roster. Read failures that prevent validating the roster do
not advance the cursor and require operator investigation; they are not skipped.

### Replay, failure and stop are different operations

- The same `rotation_id` + `turn_id` returns its ORIGINAL reservation and starts
  nothing, even after crash, expiry, unknown COMMIT acknowledgement or stop.
  Changing its batch IDs or task/worker limits is a conflict. Replay is not a
  rescan of the prior turn's execution outcomes.
- A NEW turn ID explicitly requests the next bounded slice. A fixed roster may
  change per-turn limits but not its batch identities/content/request bindings.
  Creating another rotation starts a different cursor, not a global fairness
  guarantee or a way to bypass the original immutable execution claim.
- A process can die after reserving but before claiming. Those inputs remain
  unclaimed in the original batch; they can be considered when a future explicit
  circuit reaches them. If it dies AFTER claiming, the request remains incomplete
  and is NEVER reclaimed. No lost result is reconstructed or relabeled failed.
- Stop requested before reservation returns `stopped_before_reservation` with no
  cursor row. A concurrent stop may arrive after the last check: that turn can
  commit a cursor yet start no worker. Its selected but unclaimed jobs remain
  stored; later turns eventually revisit them. The prior cooperative admission,
  drain and bounded-client-I/O rules apply unchanged.
- `operation_failed` still does not prove absence of a committed claim. Only the
  original claim/capture tables determine execution. The turn stores selection
  metadata, NOT worker heartbeats, actual model-call counts or final outcomes.
  Inspect original batch/task records when investigating an interrupted turn.

The report retains cyclic selection order (e.g.3,0,1), rather than sorting it into
an incorrect numeric order. Returned execution IDs/hashes must match the selected
original request keys. Successful reports omit source bodies and provider error
text. IDs/hashes remain business metadata and are not automatically public data.
A committed reservation is not a forecast, operator authorization or paid-call
receipt. Monetary enforcement remains WP-02; all task/worker caps are per call.

### Migration and evidence

`20260915000000_research_dispatch_turns.sql` is the new65th migration; all original
64SQL files are unchanged. The table independently enforces ordered predecessor
and cursor transitions, binds roster hashes and interleaved request IDs/hashes to
the existing immutable batches, and refuses mutation/truncation. The application
also uses a closed canonical codec. Selection states are historical hints, not an
independent authentication of the source or proof the result remains current.

Only the normal explicit migration operation may install it. The real integration
proof upgrades a disposable64-schema source instance, preserves an existing batch
and captured record, exercises failed-head rotation, same-turn concurrent replay,
restart and post-claim process loss. The earlier63-to64 test retains its original
catalog target, so its old upgrade assertions are not silently replaced. User
instances and old immutable kits are not upgraded or overlaid by this change.
Final fixed-revision evidence is recorded in the implementation PR; G3 remains
PARTIAL until the unified operating path and approved provider budget integration
are complete. No synthetic test can close the real-model gates.
