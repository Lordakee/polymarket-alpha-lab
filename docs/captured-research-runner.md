# Explicit captured research runner

## Delivered boundary

This application entry point connects an already prepared `TeamResearchIntake`
to the existing model/tool loop and prospective local Supabase/Postgres capture.
It replaces the unsafe application pattern "run model, then remember to save".
It does not schedule background work, fetch sources, enable a model, migrate a
user database, discover credentials, infer settlement, or fit a calibrator.

```text
validate and copy complete request
        |
short local transaction: register/check cutoff + immutable execution claim
        | commit acknowledged and connection CLOSED
        |
new claim only: existing model -> tools -> result
        |
short local transaction: capture success, failure or blocked intake
        | commit acknowledged
        v
committed research record + text-free receipt
```

Only the invocation that successfully commits a NEW claim starts the loop. A
repeat with identical input reads its existing state. A changed request with
the same record ID conflicts; the same task cannot be relabeled with another
record ID. A new task for the same team/model/protocol/condition cannot start
while an earlier claim in that cohort remains incomplete. Once completed,
subsequent explicit tasks remain possible, with existing first-recorded-attempt
evaluation. Claims are immutable and have no TTL, reclaim or automatic restart.
Independent conditions/teams can still run concurrently through explicit caller
invocations; this is not a distributed task-queue implementation.

This is **at-most-once loop start per claimed task**, not exactly-once provider
request delivery, guaranteed completion, crash recovery or an absolute billing
cap. A loop can intentionally make several model calls. The supplied client
owns its own HTTP timeouts/retry behavior; use the existing non-retrying adapter
where applicable. Database receipt times are not exact commit-visibility times.

## Request and result binding

`CapturedResearchRequest` includes record ID, honest model identity, protocol
version, the predeclared forecast cutoff, the full normalized intake (including
evidence text and receipts), Agent limits, required source IDs and maximum
start delay. Its closed canonical versioned JSON and SHA256 cover ALL those
fields. Every nested object is copied, validated and normalized to UTC before
registration, so callback-side changes to the caller's original data do not
change the claimed request. Changing budget or sources is not an identical retry.

The database stamps the claim using `clock_timestamp()`. Data `as_of` must not
be later than the claim, the forecast cutoff must be strictly later, and start
delay from `as_of` defaults to at most 300 seconds (configurable 1–3600). The
cutoff must agree with an existing market registration, or is atomically
registered before the first claim. A queued/stale request cannot start simply
because its original intake was valid. Model runtime can still cross the
cutoff; its late result is saved and excluded by the existing evaluator, not
backdated or discarded. A successful COMMIT acknowledgement is required before
the model factory is called. No connection/transaction spans model execution.

Results must bind the exact claimed intake and required citations. A migration
adds a trigger to the existing attempts table so even the older capture API
cannot write a different intake or omit required citations for a claimed task.
Unclaimed legacy capture remains supported. This guard validates structure and
content identity, not that a supplied recovery result truly came from a model.
The original read-before-cite protocol remains in the actual execution loop.

The model factory is application code. Declared `model_id` and protocol must
match the real configuration; this runner cannot authenticate those labels.
Provide only public/redacted evidence approved for the provider. Hashing is
neither encryption nor source authentication; normalized input text is stored
locally, not automatically redacted. No keys belong in request metadata.

## Application integration

After applying BOTH migrations to the authorized local Supabase/Postgres:

```python
from polymarket_alpha_lab.research_execution import CapturedResearchRequest
from polymarket_alpha_lab.research_execution_psycopg import (
    run_captured_research_with_psycopg,
    inspect_captured_research_with_psycopg,
    retry_research_capture_with_psycopg,
    load_captured_research_evaluation_with_psycopg,
)
from polymarket_alpha_lab.team_research_agent_types import ResearchAgentLimits
from polymarket_alpha_lab.team_research_intake import prepare_team_research_from_gamma

limits = ResearchAgentLimits()
# gamma_snapshot, approved_evidence and as_of come from explicit source intake.
# expected_condition_id/team_id come from the application's approved assignment.
intake = prepare_team_research_from_gamma(
    gamma_snapshot, task_id=task_id, team_id=team_id,
    condition_id=expected_condition_id, as_of=as_of,
    evidence=approved_evidence, limits=limits,
)
request = CapturedResearchRequest(
    record_id=record_id, model_id=actual_model_id, protocol_version="research-v1",
    forecast_cutoff_at=predeclared_forecast_cutoff, intake=intake, limits=limits,
    required_source_ids=tuple(r.source_id for r in intake.source_receipts),
)
execution = run_captured_research_with_psycopg(
    local_dsn, request=request, model_factory=configured_model_factory,
)
print(execution.to_dict())  # IDs/times/status/hashes, no evidence or model text.
```

For the existing Coinbase/Kraken flow, call `check_crypto_cross_source` first.
Only a `matched` result supplies `approved_evidence = check.evidence`; pass both
receipt IDs as required sources. Do not run the old pipeline and then call this
runner, because that would intentionally perform the research twice. A source
check blocked before any `TeamResearchIntake` still lies outside this runner;
this node does not fabricate evidence or a market run for such failures.

Keep the exact immutable request for retries, rather than refreshing snapshots
under the same ID. After a process restart, `inspect_captured_research_with_psycopg`
loads and revalidates the stored request and any captured record by record ID.
It is read-only and does not need a model factory. A missing record returns None.

## Failure states and explicit recovery

| State | Meaning / permitted next step |
| --- | --- |
| `captured` | The new run (successful, failed or blocked) was committed. Inspect the nested research status separately. |
| `already_captured` | Exact existing committed record, preserving the original receipt time. No model was started. |
| `incomplete` | Claimed but no committed result is visible. This could be active work, a crash, an unknown commit acknowledgement, or an unexpected execution failure. Do not automatically rerun. |
| `capture_failed` | The run exists in memory, but saving/validating commit acknowledgement failed. The original `pending_run` is retained in memory and hidden from repr/export. |

To retry ONLY storage, keeping the ORIGINAL result:

```python
if execution.status == "capture_failed":
    execution = retry_research_capture_with_psycopg(
        local_dsn, request=execution.request, run=execution.pending_run,
    )
```

This function has no model argument. It also handles an already-committed result
whose acknowledgement was lost: an identical result returns its original record.
Changed results conflict. If the original result was lost with the process,
this release cannot reconstruct it: retain the incomplete claim and investigate.
Do not invent a failure/success report, delete a claim, or mint another task to
hide the interruption. No automatic retry, file journal or alternate database
fallback is introduced. Regular factory/model failures DO produce the existing
fixed-code failed research records and are captured normally.

## Complete-history evaluation

Use `load_captured_research_evaluation_with_psycopg(local_dsn)`. It enables the
new `require_execution_complete=True` option of the existing evaluator reader.
In the SAME REPEATABLE READ / READ ONLY snapshot, any visible claim without a
result visible at the evaluation cutoff raises
`research_execution_history_incomplete`, before loading report bodies. A later
successful recovery does not make a historical incomplete snapshot complete.
The reader retains the existing all-history count/byte bounds and scoring rules.

The older `load_research_evaluation_with_psycopg` keeps its default False for
compatibility with PR #8 installations without the new migration. That legacy
mode alone does not check outstanding execution claims; do not use it to claim
complete runner coverage. This conservative new guard blocks the whole supplied
history, not only a filtered cohort. A claim before data validation or an
application invocation that never reached registration still is not counted.

## Deployment, tests and scope

Apply once, in order, using the existing local migration-owner procedure:

1. `20260912000000_research_evaluation_capture.sql` (PR #8, if not already applied).
2. `20260912010000_research_execution_claims.sql` (this node).

No migration is applied automatically. The second migration creates only the
execution-claims table and related functions/triggers/index, and adds a binding
trigger to attempts; it does not edit stored history or reset existing cutoffs.
It revokes PUBLIC access. Before application use, extend the existing limited
local role with SELECT/INSERT on execution_claims and EXECUTE on its trigger
functions. The old attempts INSERT trigger now reads execution_claims, so the
same role also needs that SELECT right when using old capture functions.
Do not grant ownership, UPDATE/DELETE/TRUNCATE or trigger-management rights.
Administrators, source truth and database clocks remain trusted.

```bash
python -m pytest -q tests/test_research_execution.py tests/test_research_execution_psycopg.py
python scripts/verify_local.py --full
```

`test_research_execution_disposable.py` is separately opt-in and refuses an
existing capture schema or a database other than the dedicated
`polymarket_research_capture_test` on a centrally validated local DSN. It tests
actual concurrent claim/replay, result capture, failure retention, capture-only
recovery, original-input SQL binding, rollback, immutable claims and the strict
history guard. It must never be pointed at the user's working Supabase data.
Actual final test counts/revisions and separate PostgreSQL proof belong in the
PR acceptance record; these docs do not assert a live provider test.

The owner authorized self-review/merge without external-review/CodeGraph gates.
There are no new dependencies, credentials, scheduled jobs, settlement collectors,
model-probability changes, publication permissions or execution/order paths.
Paper/report/readonly flags describe research scope; the explicit capture APIs
DO INSERT local evidence. The user database still requires separate deployment.

Primary transaction references:
- https://www.postgresql.org/docs/16/explicit-locking.html
- https://www.postgresql.org/docs/16/sql-createtrigger.html
- https://www.psycopg.org/psycopg3/docs/basic/transactions.html
