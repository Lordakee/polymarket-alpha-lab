# Node 8 Plan: Team Evaluation Attempt Latest Read

**Status:** Freeze-compliant first slice; plan text only. The implementation base is
`8f6b1f44` (Node 7 final).

**Goal:** Add one pure read-only report module that reads exactly the latest
team-evaluation attempt through Node 5, reports its persisted status and
publication-gate evidence, and exposes packet information as audit-only data.
It must never fall back to an older attempt, select a strategy side, wire
`strategy_cycle.py`, or alter frozen provider/cost behavior.

## Fixed Handoff And Boundary

Consume only these reviewed Node 5 interfaces:

```python
load_latest_team_evaluation_attempt(
    connection, *, tfr_id=None, scope_version=None, scope_key=None,
    table_name="team_evaluation_attempts",
) -> TeamEvaluationAttemptDbRow | None

load_latest_team_evaluation_attempt_with_psycopg(
    dsn, *, tfr_id=None, scope_version=None, scope_key=None,
    table_name="team_evaluation_attempts",
) -> TeamEvaluationAttemptDbRow | None
```

Node 5 owns ordering (`attempted_at DESC, tea_id DESC`), filtering,
`validate_local_postgres_dsn`, connection lifecycle, and DB errors. The new
module only delegates and projects a validated row. It adds no environment
reads, configuration family, SQL, connection, persistence, CLI command, or
package-root export. Callers pass the existing
`POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_*` values through the Node 5
adapter.

## Locked Public Surface

Create
`src/polymarket_alpha_lab/team_evaluation_attempt_latest_read.py` with exactly
these module-local exports:

```python
__all__ = (
    "TeamEvaluationAttemptLatestReadReport",
    "read_latest_team_evaluation_attempt_report",
    "read_latest_team_evaluation_attempt_report_with_psycopg",
)
```

Use one `@dataclass(frozen=True, slots=True)` report with literal
`paper_only=True`, `report_only=True`, and `readonly=True` hard flags:

```python
TeamEvaluationAttemptLatestReadReport(
    attempt_present: bool,
    absence_reason: str | None,                 # "no_matching_attempt" or None
    tea_id: str | None,
    tfr_id: str | None,
    attempted_at: datetime | None,
    scope_version: str | None,
    scope_key: str | None,
    status: str | None,                         # ready/watch/blocked
    hard_flag: bool | None,
    publication_gate_present: bool | None,
    publication_gate_status: str | None,
    reason_codes: tuple[str, ...],              # Node 2 result codes
    publication_gate_reason_codes: tuple[str, ...],
    packet_presence: str | None,                # projected/suppressed/None
    audit_packet_selected_side: str | None,
    audit_packet_forecast_probability_yes: Decimal | None,
)
```

`read_latest_team_evaluation_attempt_report` delegates to the DB-API store
loader. The `_with_psycopg` function delegates to the Node 5 psycopg wrapper.
Neither catches or rewrites DB errors.

## Projection And Fail-Closed Contract

For `None`, return an explicit empty report: `attempt_present=False`,
`absence_reason="no_matching_attempt"`, every identity/status/gate/packet field
`None`, both reason-code tuples empty, and all report hard flags true. Do not
fabricate a status, probability, packet, or fallback row.

For a row, use read-only dictionary access to
`row.evaluation_scope_payload`; do not reconstruct Node 3 dataclasses and do
not import `TeamForecastPacket`. Recheck the exact eight-key outer payload,
the Node 2 result schema, row/payload status agreement, row hard-flag agreement,
and required hard flags. Reject missing, extra, non-dict, noncanonical, or
tampered values with `ValueError`.

Read `run_metadata.external_publication_gate` only when present. It must be an
exact five-field map (`status`, `reason_codes`, `paper_only`, `report_only`,
`readonly`), with status `ready`, `watch`, or `blocked`, sorted duplicate-free
canonical reason codes, and all hard flags literally true. Report gate reason
codes separately from Node 2 reason codes.

Read `node2_result.result.reason_codes` as a canonical JSON list and preserve it
as a tuple. Parse `publishable_probability_yes` only from its canonical
fixed-six Decimal string. Preserve `None`, zero, and unknown distinctly.
Non-ready Node 2 results must not expose a packet probability.

Derive `packet_presence` from the Node 3 contract:

- `projected` when Node 2 status is `ready` and the publication gate is absent or
  `ready`;
- `suppressed` when Node 2 or the publication gate is `watch` or `blocked`;
- `None` when no row exists.

This is a contract-derived projection state, not proof that packet bytes were
persisted. The row schema does not store `legacy_forecast_packet`, so
`audit_packet_selected_side` is always `None`. If packet-shaped keys such as
`legacy_forecast_packet`, `selected_side`, or `forecast_probability` are injected
into the canonical payload, reject the row rather than infer or trust them.
When `packet_presence=="projected"`, expose
`node2_result.result.publishable_probability_yes` as
`audit_packet_forecast_probability_yes`, explicitly labeled audit-only and
canonical `P(YES)`. It is never a side recommendation. For suppressed or
absent packets, it is `None`.

## Red/Green Work

- [ ] **RED — Public contract:** Add behavior tests for exact `__all__`, frozen/slotted
  hard-flagged dataclass behavior, the two loader signatures, and the no-row
  empty report.

- [ ] **RED — Read behavior:** Add fake-connection and delegation tests for latest
  row selection, one-call/no-fallback behavior when the latest row is
  `watch` or `blocked`, identity/status/hard-flag projection, gate extraction,
  separate reason-code tuples, packet projection states, audit-only probability,
  and permanent `None` selected-side output.

- [ ] **RED — Failure matrix:** Cover malformed payload sections, invalid gate
  status or flags, unsorted or duplicate reason codes, status/hard-flag
  disagreement, noncanonical Decimal values, injected packet-shaped fields,
  forged row types, and DB errors that must propagate unchanged.

- [ ] **GREEN — Pure reader:** Implement only plain payload reads and immutable
  report construction. Do not import `strategy_cycle`, `cli`, a cost engine,
  packet constructors, a writer, SQL, filesystem APIs, or alternate storage.

- [ ] **GREEN — Psycopg delegation:** Prove the wrapper calls only the Node 5
  latest-attempt adapter. Spy on validation and `_connect` to prove invalid DSN
  input fails before connection activity. No real database proof is required;
  the first slice is offline-only.

- [ ] **GREEN — Scope guard:** Add a child-local AST/import/export/forbidden-surface
  test. The production import allowlist is exactly standard-library modules
  plus `team_evidence_aggregation_attempt_store`,
  `team_evidence_aggregation_attempt_psycopg`, and
  `team_evidence_aggregation_db_row`. Assert no package-root export and no
  side-selection or strategy-consumption semantics.

## Documentation And Indexing

Add `docs/team-evaluation-attempt-latest-read.md` documenting the latest-row
ordering, no-fallback rule, empty-report reason, gate semantics, packet
non-persistence, audit-only field labels, local Supabase/Postgres adapter
boundary, and the post-freeze work that remains deferred.

Add one module-index row:

```text
src/polymarket_alpha_lab/team_evaluation_attempt_latest_read.py
tests/test_team_evaluation_attempt_latest_read.py
```

Update `tests/test_phase1_docs_module_index_matches_files.py` by adding the
sorted pair
`("team_evaluation_attempt_latest_read", "test_team_evaluation_attempt_latest_read")`
and changing the expected pair count from `20` to `21`. Do not update
`README.md`; the dedicated documentation page is sufficient. Do not update the
Phase 1 targeted-test manifest, CLI, package root, or frozen strategy files.

## Exact Sorted Allowlist

The plan file is a separate planning artifact. Future implementation may change
only these paths, in this literal sorted order:

```text
docs/index/phase1-module-index.md
docs/team-evaluation-attempt-latest-read.md
src/polymarket_alpha_lab/team_evaluation_attempt_latest_read.py
tests/test_phase1_docs_module_index_matches_files.py
tests/test_team_evaluation_attempt_latest_read.py
tests/test_team_evaluation_attempt_latest_read_scope.py
```

## Line Ceilings

```text
team_evaluation_attempt_latest_read.py                 <= 340
test_team_evaluation_attempt_latest_read.py             <= 720
test_team_evaluation_attempt_latest_read_scope.py       <= 520
team-evaluation-attempt-latest-read.md                  <= 240
new production-source aggregate                         <= 340
new test aggregate                                      <= 1,280
```

## Verification, Stop Conditions, And Evidence

Run the focused offline tests, sanitized full `pytest`, `compileall`, `git
diff --check`, secret and Phase 1 boundary scans, and CodeGraph synchronization.
Obtain the authorized read-only Codex review with `gpt-6-astra` and
`model_reasoning_effort=max`; the final nonblank line must be `VERDICT: PASS`.

Stop immediately for any touch to `strategy_cycle.py`, `cli.py`, the cost engine,
provider dispatch, frozen files, package root, or file-backed persistence; any
YES/NO recommendation or packet-side authority; any fallback through an older
attempt; any connection before DSN validation; any alternate database; malformed
or fabricated audit data; scope/import/export/line violations; failed focused or
full checks; missing CodeGraph or scan evidence; or a review result other than
`VERDICT: PASS`. If `8f6b1f44` is not the exact clean base, stop and reopen the
handoff.

Completion evidence must record `NODE_BASE=8f6b1f44`, the exact allowlist,
public-surface and no-root-export proofs, the empty/no-fallback matrix, gate and
hard-flag extraction, tamper rejection, audit-only packet labeling, DSN-before-
connect proof, offline focused/full/compile/diff/scan results, CodeGraph status,
clean worktree, and the final review verdict.

## Post-Freeze Future Work

After settlement and a separately reviewed node, the reader may become an
observability input to `strategy_cycle.py`. Provider configuration and dispatch
must remain frozen until that work is explicitly reopened. Any future decision
path must pass evidence into the central cost engine, which owns executable
cost/slippage analysis and final `YES`/`NO`/`none` selection. The persisted
packet `selected_side` remains an audit input and never becomes strategy
authority. Provider wiring, ranking, recommendations, trade instructions,
execution, credentials, and order mutations are outside this slice.
