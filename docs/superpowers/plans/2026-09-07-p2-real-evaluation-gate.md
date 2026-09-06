# P2 Stage Plan: Infrastructure Then Genuine Evaluation

Date: 2026-09-07
Stage: P2a and P2 of the [Project Completion Plan](../../roadmap/2026-09-07-project-completion-plan.md)
Status: P2a implementation accepted; Claude hard review and follow-up PASS
Depends on: accepted and pushed P1 commit `030491bc` (P1 only; it does not
contain any P2a work described below)

## Parent-Plan Traceability

P2 is split into two separately reviewed and pushed nodes because genuine
settlement is an external dependency:

- **P2a, evaluation infrastructure:** event lineage, outcome-as-of export,
  complete paired metrics and a deterministic report command. N=0 is acceptable
  only as an honest P2a verification state. P2a does not complete P2.
- **P2, genuine settlement evaluation:** freeze and collect a prospective
  short-duration control cohort, import at least one verifiable settlement,
  publish the real report and record the exact continue/improve/stop decision.
  P2 completion requires N >= 1.

P2a is entirely new, not-yet-implemented work built on P1's persistence and
baseline contracts; event lineage and the separate outcome cutoff were not
delivered by P1. Statements under "P2a Work Items" and "P2a Acceptance" are
prospective requirements, not claims about commit `030491bc`. Each node follows
the mandatory loop: detailed plan -> Claude plan review -> disposition ->
implement -> verify -> Claude hard review until PASS -> commit -> push before
the next node. P3 does not begin before P2 has a genuine report or the
completion plan's constrained-closure disposition has explicitly ended P2.

## Verified Starting Facts

- P1 has two genuine conditions with two forecast snapshots each. Both current
  markets end around 2027-01-01 and remain open. The accepted export is
  `included=0`, `pending=2`; it is P1 plumbing evidence, not P2 evaluation.
- A read-only 2026-09-07 UTC inventory of the pinned Gamma tag feeds used
  `GET /markets?tag_id={235|39}&closed=false&limit=100&offset=0`, then applied
  the planned binary/active/not-closed/team-keyword and `now < endDate <=
  2026-10-07T00:00:00Z` predicates without reading outcome prices. It found BTC
  2 candidates (both ending 2026-10-01) and ETH 32 candidates (29 ending
  2026-09-07 and 3 ending 2026-10-01). This is plan-scoping evidence gathered
  outside commit `030491bc`; P2 must repeat and persist the inventory before
  freezing its checkpoint. Availability can change and related rows may share
  events, so these are candidates, not promised settlements or independent
  samples.
- The P1 exporter accepts only a forecast cutoff and currently selects the
  latest outcome at any time. The completion plan requires a distinct outcome
  observation cutoff and correction-safe immutable exports. This is P2a work
  completing the export contract, not an inherited P1 capability.
- The evaluator supplies team and market Brier, team clipped log loss,
  calibration and team counts. It lacks market clipped log loss, verified event
  concentration, condition counts, settlement-lag statistics and a bounded
  hand-check subset.
- Gamma normalized metadata contains condition/slug but not nested event
  identity. Live responses expose `events[0].id` and `events[0].slug`. Event
  lineage is P2a infrastructure; conditions with absent or ambiguous mapping
  remain event-unknown and cannot be called independent events.
- The crypto forecast equals its contemporaneous market midpoint. The evaluated
  hypothesis is `zero_impact_market_control`; no independent predictive
  hypothesis exists, and P2 may not invent an impact or tune from outcomes.

## Frozen Prospective Design

The P2 checkpoint is created before any outcome refresh for its selected rows:

1. Teams/configs are exactly `crypto_btc` / `p1-crypto_btc-v1` and
   `crypto_eth` / `p1-crypto_eth-v1`.
2. Gamma prefilter tags are pinned to Bitcoin `235` and Ethereum `39`. Each team
   fetches exactly the first page with `limit=100`, `offset=0`, `closed=false`;
   the frozen local binary/active/not-closed/team-keyword selector applies after
   the prefilter. Changing a tag or page bound starts a new cohort. Tag removal
   is a recorded blocker, never an invitation to substitute an unreviewed feed.
3. A condition is prospective only when its verified Gamma `endDate` is later
   than forecast generation by at least 30 minutes and no later than the frozen
   cohort horizon. A market that is still `closed=false` after its end time is
   not prospective. The checkpoint stores the end time and lead time.
4. Primary forecast selection remains earliest eligible forecast per
   `(condition_id, team_id, config_version)`, tie-broken by
   `(generated_at, forecast_id)`. Retries and snapshots do not increase N.
5. Conditions sharing a verified Gamma event ID remain one event group.
   Missing/ambiguous event lineage is reported unknown and never increases the
   verified unique-event count.
6. Baseline is the persisted contemporaneous YES-book midpoint on that exact
   forecast row. Constants are never labeled market baselines.
7. The timezone-aware forecast cutoff (the P1 export parameter
   `as_of_evaluation_cutoff`) is frozen immediately after collection and before
   settlement refresh. P2a adds the distinct timezone-aware
   `as_of_outcome_cutoff`, frozen separately for each export. Only outcome
   observations at or before it may be selected.
8. This is a prospective control checkpoint with no training or parameter
   change. Its outcomes cannot tune a future hypothesis. Any independent model
   requires a reviewed new version and future holdout.
9. Verdicts remain exact: N < 30 `insufficient_sample`; N >= 30 with team Brier
   >= market Brier `no_consistent_edge`; 30 <= N < 100 with lower team Brier
   `indicative_edge`; N >= 100 with lower team Brier `comparative_edge`.
10. First-run P2 publishes as soon as N >= 1. The bounded reassessment is
    2026-10-07 UTC or 30 settled unique conditions, whichever comes first. If
    the bound ends with 1 <= N < 30, publish `insufficient_sample` and choose,
    under a new reviewed plan, either an explicit finite extension with the
    same hypothesis or terminal constrained closure. Never silently extend,
    relabel the cohort, or add long-duration markets after seeing outcomes.

## P2a Work Items

### 1. Event Lineage

- Extend Gamma normalization with `event_id`, `event_slug` and `market_end_at`
  only when exactly one canonical nested event maps to the market. Missing,
  multiple or malformed mappings remain `None` with reason-coded lineage state.
- Add additive schema `research_settlement.research_forecast_lineage`, keyed by
  immutable forecast `payload_sha256` and carrying the logical `forecast_id`,
  condition/team/config/event identity, market end, metadata observation
  time/hash and hard `paper_only/report_only/readonly` flags. During local
  acceptance the real P1 table proved that `forecast_id` repeats across
  additive observation snapshots, so using it as the primary key would make a
  normal rerun collide. Migration `20260907000002` corrects the initially
  applied empty-table shape and refuses any unaudited backfill. The migrations
  are local-Postgres-only with RLS and restricted roles.
- Persist lineage after a ready forecast using an idempotent psycopg adapter.
  Same identity replays succeed; conflicting identity fails closed. Partial
  failure remains visible and recoverable by rerun, without deleting forecasts.
- Existing P1 forecast rows have event status `unknown`; no later metadata is
  backdated to claim contemporaneous event provenance.

### 2. Outcome-As-Of Export

- Make `as_of_outcome_cutoff` required in the pure exporter and CLI. Filter
  outcome rows to `observed_at <= outcome_cutoff`, then choose the latest per
  condition deterministically.
- Outcomes observed before the selected forecast are excluded with
  `outcome_before_forecast`; later outcomes are `outcome_after_cutoff`; latest
  disputed outcomes remain pending. Invalid outcome rows are counted.
- The current primary key `(condition_id, observed_at)` makes two outcomes at
  the exact same timestamp impossible. Import replay with a different outcome
  at the same identity is an adapter-level conflict and must fail closed. A
  later opposite outcome is a correction, not an ambiguous same-time row: it
  produces a new immutable export linked by `prior_export_id`.
- Add manifest schema/version, both cutoffs, exact config cohorts, input and
  selected forecast IDs/payload hashes, selected outcome IDs/payload hashes,
  event IDs/unknown counts, all exclusions/pending/disputes, query/selection
  rules and optional prior export ID. Preserve deterministic exact-byte hashes;
  bounds cannot silently truncate.

### 3a. Paired Market Log Loss

Compute market clipped log loss with the same epsilon, actual outcomes and
included rows as team log loss. Add hand-calculated fixtures for YES/NO and
clipping edges.

### 3b. Condition And Event Concentration

Report unique condition count, verified unique event count, unknown-event row
count, per-event counts and maximum verified event concentration. Unknown event
rows stay outside the verified denominator and are shown separately.

### 3c. Settlement Lag

Report minimum, median and maximum `settled_at - generated_at` for included
samples, with deterministic Decimal seconds and odd/even median fixtures.
Negative lag remains an invalid sample.

### 3d. Hand-Check Subset

Emit at most five samples ordered by `(condition_id, team_id, generated_at)`,
including forecast/baseline P(YES), actual outcome, both squared errors and both
clipped log-loss contributions. N=0 produces an empty subset, not zero metrics.

### 4. Deterministic Report Command

Add exactly one not-yet-implemented command; its target compatibility change is
CLI inventory 84 -> 85:

```text
evaluate-settlement-cohort \
  --samples FILE \
  --manifest FILE \
  --checkpoint FILE \
  --out PREFIX
```

- It reads files only and writes `PREFIX.json`, `PREFIX.md` and
  `PREFIX.manifest.json` atomically. It never writes a database.
- It verifies sample exact-byte hash, manifest schema, both cutoffs, counts,
  selected IDs/configs and checkpoint cohort identity before evaluation.
- Checkpoint fixes `cohort_id`, hypothesis label
  `zero_impact_market_control`, independent-hypothesis status
  `not_implemented`, team/config/tag/page/end/lead/cutoff rules and creation
  time. These values are inputs to verification, not CLI-selectable labels.
- Report manifest contains `schema_version`, `cohort_id`, `sample_export_id`,
  `evaluator_version`, exact verdict/disposition, hypothesis status,
  `generated_at` supplied by the checkpoint (not wall clock), report JSON and
  Markdown hashes, and hard flags.
- Disposition mapping is fixed: N < 30 -> `continue_bounded_collection` before
  the reassessment bound or `reassess_extension_or_stop` at the bound;
  `no_consistent_edge` -> `stop_or_new_reviewed_hypothesis`;
  `indicative_edge` -> `continue_prospective_comparison`;
  `comparative_edge` -> `proceed_to_applicable_p5_evidence`. It never stores a
  favorable label outside the immutable report files.
- Outputs explicitly separate engineering acceptance, control behavior and
  independent-hypothesis evidence. N=0 metrics and coverage render
  `undefined`, never `0`.

### 5. P2a Tests And Operations

- Gamma event extraction: one, none, multiple, malformed ID/slug/endDate.
- Lineage migration/adapter: local DSN, idempotent replay, identity conflict,
  partial-write recovery, RLS and hard flags.
- Export: dual cutoffs, future/pre-forecast outcomes, disputed latest revision,
  correction linkage, unknown lineage, config separation, malformed rows,
  duplicate accounting and deterministic replay.
- Evaluator: paired Brier/log losses, condition/event concentration, lag
  median, N=0 undefined rendering, bounded subset and unchanged verdicts.
- Report command: hash/count/cutoff/ID mismatch, checkpoint mismatch,
  deterministic atomic files and every disposition branch.
- Update runbook and CLI inventory. Verify with focused tests, opt-in DB
  lifecycle, full Python 3.11 regression, compileall, diff check and credential
  scan.

## P2a Acceptance

P2a may close with N=0 only when all infrastructure and failure tests pass, the
real P1 zero-sample export is reproduced with both cutoffs and explicit
undefined metrics, Claude hard review returns PASS, and the node is committed
and pushed. Its record must state that P2 remains open and no predictive verdict
has been established.

## P2 Genuine Evaluation Node

After P2a is pushed:

1. Re-inventory the pinned first 100 tag rows without outcome inspection and
   write the exact query, retrieval time, row identities, count/end-date/event
   concentration and exclusions to
   `docs/verification/p2/inventory-{cohort_id}.json`. The checkpoint stores
   that artifact's SHA-256. If no condition retains the 30-minute lead, record
   the blocker and invoke constrained closure rather than use an expired market.
2. Persist ready forecasts and lineage for every bounded eligible condition
   selected before the horizon. Write blocked/missed attempt status lines and
   reason codes to `docs/verification/p2/collection-{cohort_id}.json`; payloads
   and secrets are excluded. Freeze and hash the checkpoint before any outcome
   refresh.
3. At or after resolution, import only verifiable Gamma outcomes, freeze the
   outcome cutoff, export and run `evaluate-settlement-cohort`.
4. Hand-check the deterministic subset and publish command, counts, per-team and
   per-event concentration, exclusions, pending, lag, Brier, paired log loss,
   calibration and coverage. State correlation/uncertainty limits; evaluator
   labels are not significance tests or profitability claims.
5. Record the exact verdict and mapped disposition. With N < 30, this completes
   only the first-run checkpoint and continues bounded collection to the frozen
   reassessment bound. Every later immutable correction/report links its prior
   export ID.

## P2 Acceptance

P2 completes only with N >= 1 genuine settled samples, audited prospective
lineage, a reproducible immutable report, a hand-checked subset, the exact
verdict and a recorded disposition satisfying all four parent acceptance
criteria. Synthetic fixtures never enter the real report. If qualifying
collection or settlement cannot occur within the frozen operating scope,
produce the completion plan's constrained-closure evidence instead of a sample.
P2 receives its own Claude hard review, commit and push before P3.

## Rollback

P2a rollback reverts its code/docs and drops only its additive lineage schema;
it never deletes P1 forecasts, evidence or outcomes. P2 reports/exports are
immutable evidence labeled with checkpoint and producing commit and remain
preserved if later code is reverted.

## Plan Review Disposition (2026-09-07)

Claude Code (`opus`, effort `max`) returned `REQUEST_CHANGES`: three CRITICAL,
three MEDIUM and two LOW findings. All eight are accepted as plan changes. The
plan text now splits P2a/P2 and assigns future event/outcome-cutoff work to
P2a; records measured short-duration availability; replaces impossible
same-timestamp outcome logic with adapter conflict and later-correction rules;
splits future evaluator work into four testable components; specifies the
future report command and target 85-command inventory; defines expiry handling
without silent extension; and pins Gamma tag/page bounds and deprecation
behavior. This disposition records revisions to the plan only; it makes no
claim that P2a code exists in the P1 dependency commit.

A final pre-implementation review returned `VERDICT: PASS`. Its non-blocking
MEDIUM recommendation is accepted by fixing the repeated inventory artifact at
`docs/verification/p2/inventory-{cohort_id}.json` and hashing it from the
checkpoint. Its cutoff-name and blocked-attempt-location clarifications are
also accepted: the forecast cutoff is explicitly mapped to
`as_of_evaluation_cutoff`, and redacted attempt records go to
`collection-{cohort_id}.json`. Event extraction details and exact DDL remain
implementation details under the already frozen contracts.

The first follow-up review returned `REQUEST_CHANGES` after interpreting the
prospective work items as implementation claims against commit `030491bc`.
Those implementation-missing findings are not accepted as technical defects
because this is a pre-implementation stage plan. The clarity issue is accepted:
the status, dependency, work-item tense, CLI inventory target and measurement
provenance now explicitly state that `030491bc` is P1 only and P2a has not
started. The measured availability command and predicates are recorded above
and must be rerun into a P2 checkpoint artifact.
