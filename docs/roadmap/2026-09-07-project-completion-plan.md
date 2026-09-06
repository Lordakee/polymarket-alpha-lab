# Project Completion Plan

Plan identifier: 2026-09-07
Evidence baseline: 2026-09-06, HEAD `8b2025f0`
Status: proposed completion roadmap; P1-P6 below are not accepted deliveries
Scope: complete the research and paper-evaluation phase, including an honest
decision on predictive value and a reproducible release or stop record

## Assessment

The M0-M6 infrastructure delivery is complete and accepted. The core research
question remains unanswered: does this method add predictive value to
Polymarket probability-event forecasts beyond the contemporaneous market?
Acceptance of the transport, persistence, bundles, crypto cycles, diagnostics
and evaluator establishes an engineering foundation, not an empirical result.

The accepted handoff records zero real settled samples. Only `crypto_btc` and
`crypto_eth`, two of ten teams, have operational workflows. Each spot item has
one evidence family, `kraken_public`, satisfying a 1/1 minimum without
independent corroboration. Forecasts are not yet being collected on a verified
recurring schedule; persistence is optional at the command boundary. The
settlement export is a protocol awaiting implementation. Cost-adjusted paper
results and memory-as-context benefit remain unactivated.

There is also a modeling limitation: both crypto adapters deliberately assign
zero probability impact to descriptive evidence. The current forecast follows
the YES-book midpoint-derived base, subject to canonicalization. This is a
useful control and collection path, but adding samples or providers alone does
not create an independent probability model. A predictive-value claim needs a
reviewed hypothesis, prospective forecasts and honest held-out comparison; an
evidence-backed decision to stop is an admissible project outcome.

## Evidence And Limits

- Inspected branch: `codex/m0-baseline-persistence-acceptance`; initial tree
  clean; HEAD `8b2025f0`. The accepted delivery range is
  `72d0a23a..8b2025f0`, including the M0 commit as the starting delivery.
- Ran `codegraph sync /home/ubuntu/polymarket-alpha-lab`, then
  `codegraph status`: up to date, with the existing v0.9.9 builder warning.
  Queried all eight requested symbols and inspected their module inventories
  with `codegraph node --symbols-only`, then followed relevant source paths.
  The index locates implementation; it does not prove runtime correctness.
- Read the delivery plan, domain matrix, M0 decisions, operator runbook and
  all seven accepted M0-M6 stage plans, including their review records.
- Historical final verification records 34,284 passed and 8 skipped on
  Python 3.11, an 80-command CLI inventory, and green opt-in network smoke
  for Gamma, CLOB and Kraken BTC/ETH. These are delivery-time results, not
  fresh verification of this roadmap or guarantees of current source access.
- This assessment performed no new acquisition, DB census, migration,
  forecast collection or settlement evaluation. Zero settled samples and
  absent recurring collection describe the accepted handoff; P1 must establish
  the actual operational inventory before relying on it.

| Accepted stage | Commit | Recorded disposition |
| --- | --- | --- |
| M0 baseline and persistence acceptance | `72d0a23a` | PASS |
| M1 parameterized requests and adapters | `c2920a0b` | PASS |
| M2 evidence bundles and dispatch | `68d03355` | PASS |
| M3 BTC vertical slice | `76c0a48e` | PASS, with the documented multipart review and finding dispositions |
| M4 operational quality | `b28edd97` | PASS |
| M5 Wave 1 ETH and domain matrix | `ba424e73` | PASS; later waves remain conditional |
| M6 settlement evaluator | `58638b0b` | FAIL -> fix -> PASS; real evaluation remains outstanding |
| Delivery-status record | `8b2025f0` | Records the accepted stages and remaining triggers |

## Implementation Boundaries

| Module or symbol | Delivered behavior | Completion implication |
| --- | --- | --- |
| `SafeGETTransport` | Registered public HTTPS GET, typed queries, host/DNS/peer checks, bounded responses and attempts | New sources and outcome acquisition must preserve this boundary. |
| `CentralDataStore` | Transaction-neutral raw/normalized storage, identity checks, provenance and retention health gate | Collection needs real readback and recovery evidence; a ready packet alone does not prove persistence. |
| `acquire_once` | Bounded acquisition, refusal handling and raw-before-normalized writes | Reuse its failure vocabulary and caller-owned transaction semantics. |
| `build_evidence_bundle` | Per-item freshness/quorum, mirror deduplication, typed-value contradictions and zero-weight placeholders | P3 must demonstrate independent price families under an explicit comparison policy. |
| `run_crypto_research_cycle` | Pure BTC/ETH observation-to-forecast reducer; CLI composes acquisition and optional persistence | P1 adds recurring operation and auditable forecast/outcome lineage around this owner. |
| `evaluate_settlement_samples` | Pure metrics over materialized samples, forecast-cutoff filtering and declared verdicts | It does not perform DB joins, deduplicate cycles or establish outcome provenance. |
| `run_strategy_cycle` | Separate market-to-cost/report workflow with optional local paper simulation | P5 needs an explicit bridge from research forecasts to this existing cost/paper ownership. |
| `build_default_source_registry` | Registered sources and ten team IDs; BTC/ETH spot feeds share one family | Registry entries and supplied-input builders do not establish operational domain coverage. |

## Standing Constraints

- Preserve `paper_only=True`, `report_only=True` and `readonly=True` on
  research contracts. External activity is public read-only acquisition;
  internal writes are the existing local research persistence and reporting
  operations. No live trading, order submission, wallet, account, private-key
  or new credential surface is in scope.
- Use local Postgres only, through the existing local-DSN validators and
  configuration boundaries. Existing database secrets stay in the process
  environment, never in reports, fixtures, prompts or committed files.
- Preserve bounded transport, refusal policy, raw-before-normalized ordering,
  identity integrity and retention. The existing raw policy is 29-day expiry
  with the 15-minute pg_cron job and audit-before-delete. Durable evaluation
  must remain reproducible from accepted normalized facts and hashes after
  raw expiry; extending raw retention is not a substitute.
- Never fabricate source availability, timestamps, probabilities, settlement
  labels, fills, costs or memory benefit. Missing, stale, contradictory,
  unknown, refused and unsupported states remain explicit.
- Keep the declared evaluation gates: indicative N >= 30, comparative
  N >= 100, cost-arm activation at settled N >= 30, log-loss epsilon 0.001
  and ten calibration buckets. This roadmap introduces no new numerical
  profitability, significance, freshness or disagreement threshold.
- Keep changes scoped to demonstrated completion gaps. No wholesale CLI
  rewrite, new database backend, general agent platform or automatic merger
  of preserved branches. Scraping and other deferred acquisition mechanisms
  remain outside the default source route.
- A later execution phase requires a separate user decision and design.
  Even a favorable research verdict or completed paper-cost arm grants no
  execution authority.

## Stage Review And Delivery

Every P milestone, domain wave and triggered arm follows this mandatory loop:

1. Write a bounded stage plan with parent traceability, inspected code facts,
   dependencies, acceptance criteria, verification and rollback/recovery.
2. Obtain a read-only Claude Code plan review using model `claude-opus-5`,
   effort `max`, with fast mode off. Pass model and effort explicitly at
   invocation; do not rely on persisted defaults.
3. Disposition every finding as accepted, rejected with evidence, or an
   explicitly documented limitation; revise the stage plan accordingly.
4. Implement the dispositioned scope and verify the acceptance criteria.
   Record revision, commands, results, data provenance and remaining gaps.
5. Run the read-only Claude Code hard review under the same settings. Fix,
   re-verify and re-review until PASS on the final change. An unavailable
   reviewer leaves the gate pending; no fallback is allowed unless the user
   explicitly changes the review rule.
6. Commit the accepted stage and its evidence record. Commit acceptance does
   not itself decide push or merge; P6 records that disposition.

This roadmap is not a claim that those reviews have already occurred. Each
milestone below inherits this loop; a blocked dependency or unfired trigger
must be recorded as such, rather than converted into PASS. Historical reviews
retain the model and circumstances that actually produced them.

## P1: Settlement-Sample Pipeline

Priority: immediate critical path. Dependencies: accepted M0-M6 contracts and
working local persistence. Review: the mandatory stage loop above.

### Work

- Establish an operational inventory of forecast, evidence and outcome rows,
  schema readiness, retention health and persistence configuration. Run the
  existing bounded BTC/ETH commands recurrently, either by an accountable
  manual procedure or a supervised local schedule. Choose the cadence and
  market universe from event horizons, documented source cadence and measured
  request behavior; do not invent a fixed frequency or settlement date here.
- Enable both central evidence persistence and
  `POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_ENABLED` with their existing local
  DSN settings. Verify forecast and evidence readback. Log attempted markets,
  ready/blocked status, persistence success, missed runs and retry reasons.
  Fetch-only runs and partial persistence must not count as collected samples.
  Scheduling must cover overlap prevention, interruption, restart and stop;
  manual operation must have the same audit trail.
- Freeze an eligible event cohort and forecast-selection rule before outcome
  inspection. Retain immutable forecast payload identity, condition/team,
  model/config/parser versions, generation and evidence as-of times, source
  references and the contemporaneous YES-market baseline. Multiple observation
  windows and repeated `forecast_id` values require explicit snapshot
  selection; row-level idempotency alone does not define the evaluation unit.
- Resolve baseline provenance before admitting forecasts to an evaluable
  cohort. The current CLI constructs
  BTC/ETH configs without overriding `market_implied_probability_hint`, whose
  default is `0.500000`. The builders copy that hint into
  `market_implied_probability_observed`, although the cycle derives its base
  from the YES-book midpoint. P1 must persist the actual contemporaneous
  baseline and prove its link to the forecast's accepted book observation.
  Historical rows may use a proven, version-aware reconstruction from accepted
  facts; otherwise exclude them with reasons. A default hint must never be
  relabeled as an observed market price.
- Acquire or import auditable resolved outcomes for the persisted forecast
  universe, including forecasts that never produced a paper trade. Join by
  event identity and the chosen forecast snapshot, validate the YES/NO mapping,
  and retain resolution source, actual settlement time, observation time,
  dispute/revision status and pending reasons. A closed flag, scheduled event
  end or current price alone is not proof of a final outcome. The existing
  outcome tracker scores paper-trade legs; reuse compatible parts only after
  reconciling that orientation with canonical P(YES).
- Implement the read-only local-DB export feeding the existing
  `settlement-evaluation --samples <json-file>` command. Prefer existing row
  codecs and stores. `TeamForecastOutcome` requires paper-cost fields; do not
  manufacture PnL to fit a forecast-only outcome into that contract. Any small
  persistence extension needed for truthful outcome or snapshot lineage must
  be explicit in the P1 stage plan and receive lifecycle verification.

Baseline source anchors at the inspected revision:
[CLI composition](../../src/polymarket_alpha_lab/crypto_research_cycle_cli.py),
[cycle reducer](../../src/polymarket_alpha_lab/crypto_research_cycle.py),
[BTC config/builder](../../src/polymarket_alpha_lab/crypto_btc_team.py) and
[ETH config/builder](../../src/polymarket_alpha_lab/crypto_eth_team.py).

### Export Contract

Produce the JSON object already consumed by `load_samples_document`:

| Field | Required origin and meaning |
| --- | --- |
| `as_of_evaluation_cutoff` | Frozen forecast-cohort cutoff; forecasts after it are ineligible. |
| `pending_count` | Eligible selected forecasts still unresolved or not verifiably settled at the recorded outcome-observation cutoff. |
| `samples` | Deterministically ordered, selected settled forecast/outcome pairs. |
| `condition_id`, `team_id` | Persisted event and team identity, checked against outcome lineage. |
| `forecast_p_yes` | Persisted canonical Decimal P(YES), serialized as a decimal string regardless of selected side. |
| `market_implied_p_yes` | Proven contemporaneous YES baseline for that same forecast snapshot, serialized as a decimal string. |
| `actual_outcome` | Verified event outcome `yes` or `no`, never whether a selected trade leg won. |
| `generated_at`, `settled_at` | Original forecast generation and evidenced settlement timestamps in UTC. |

Keep a versioned export manifest with the query/selection rules, source-row
identities and hashes, model/config cohorts, export identity, exclusions,
pending/disputed counts and the separate outcome-observation cutoff. The
forecast cutoff closes collection; later settlement is valid when evidenced
by the outcome cutoff. The evaluator currently checks only the forecast
cutoff and sample invariants, so the exporter must enforce outcome as-of
provenance, duplicate handling and revision rules itself.

Respect the current sample contract: finite probabilities strictly between
0 and 1, valid outcome labels and UTC timestamps. Invalid probability rows
are excluded with reasons; log-loss clipping does not make them admissible.
Preserve original exports when resolutions are corrected, and publish a new
version with correction lineage rather than silently rewriting past results.

Use the earliest eligible pre-resolution forecast per condition/team/model
cohort as the default primary selection, with deterministic tie-breaking
specified before collection. Keep model versions in separate evaluations,
report unique events as well as rows, and do not inflate N with retries,
multiple snapshots or duplicated paper legs. Related events remain correlated
even after deduplication. Forecasts recorded too late to establish prospective
provenance, unavailable baseline lineage and conflicting outcomes are
excluded or pending with explicit reasons. No later observation may be
backdated into a forecast.

### Acceptance Criteria

1. Recurring BTC and ETH operation is demonstrated with real persisted
   forecasts/evidence and independent readback, including interrupted-run
   recovery and visible blocked/missed attempts. A scheduler is optional;
   repeatable collection and an accountable operating procedure are required.
2. Fixtures and local-DB integration prove selection, retry idempotency,
   partial-write recovery, snapshot/version handling, YES/NO orientation,
   paired baseline provenance, pending/disputed outcomes and timestamp guards.
3. The baseline wiring issue is resolved and regression-tested. The current
   zero-impact forecast is tested against its actual market control under the
   same Decimal policy, not against the default hint.
4. Exported counts reconcile with eligible selected rows, exclusions and
   pending rows; bounds cannot silently truncate the cohort. Re-exporting an
   unchanged snapshot produces the same canonical file and manifest.
5. The file loads through the existing evaluator, survives offline replay
   after raw expiry, and contains no secret or refused payload. Synthetic
   outcome fixtures remain labeled and separate from real evaluation data.
6. The operator procedure covers both crypto commands, persistence gates,
   cohort selection, outcome refresh, export, recovery and stop. If nothing
   has settled, the real export records that honestly; P1 plumbing acceptance
   does not claim that P2 has produced a result.

## P2: Real Evaluation And Improve-Or-Stop Gate

Priority: critical path after P1. Dependencies: P1 and genuine resolved
outcomes; neither P3 nor domain expansion is required to evaluate the current
control. Review: stage plan, dispositions, verification and hard PASS before
committing the evaluation deliverable.

### Work

- Before inspecting outcomes, freeze model/config versions, event eligibility,
  forecast selection, training/development versus held-out periods, baseline
  definitions and evaluation checkpoints. Keep related event snapshots in
  the same partition. New source/model versions start future cohorts; they
  cannot rewrite or tune against the already evaluated holdout.
- Run the first real export through the evaluator as soon as verifiable
  settlements exist, even when the verdict must remain insufficient. Publish
  the manifest, command, counts, per-team/event concentration, exclusions,
  pending status, settlement lag, Brier scores, clipped log loss, calibration
  and settled coverage `N / (N + pending)`; report empty coverage as undefined.
- Compare the team forecast and contemporaneous market on exactly the same
  samples. Retain the zero-impact control and predeclared simple controls,
  clearly labeled; a supplied constant is not the market baseline. State
  uncertainty and correlation limits. The existing evaluator supplies no
  confidence interval or significance test, and its verdict labels cannot
  be interpreted as either.
- Treat zero-impact results as a control evaluation. If an independent
  research hypothesis is justified, write a reviewed P2 follow-on plan for
  the specific event archetype, evidence-to-probability rule, versioning and
  prospective held-out comparison. Develop from permitted earlier data,
  then collect new forecasts through P1. Do not invent a probability impact
  merely to make forecasts differ, or present a control tie as a test of a
  signal model that has never been implemented.

### Verdict Discipline

Here N is the included count after P1's frozen selection and exclusions.
Report event concentration alongside N; meeting a row-count gate does not
establish statistical independence.

| Declared condition | Exact verdict | Required disposition |
| --- | --- | --- |
| N < 30 | `insufficient_sample` | Continue the predeclared collection scope when feasible, or close inconclusive with an explicit stop rationale. No edge claim. |
| N >= 30 and team Brier >= market Brier | `no_consistent_edge` | Record the negative/tied result. Propose a specific, justified improvement on a new cohort or stop that hypothesis. |
| 30 <= N < 100 and team Brier < market Brier | `indicative_edge` | Preserve the hypothesis and collect prospective comparative evidence. No profitability or generalization claim. |
| N >= 100 and team Brier < market Brier | `comparative_edge` | Report the observed paired advantage with uncertainty, concentration and applicability limits; proceed to applicable P5 evidence, not live execution. |

### Acceptance Criteria

1. A real, reproducible settled-outcome report exists with audited provenance
   and the exact declared verdict. The first small-sample report completes
   the first-run checkpoint, not the project's predictive-value gate.
2. A hand-checkable sample subset agrees with the joins, canonical P(YES),
   baseline and metric calculations. Prospective timing, selected revisions,
   exclusions and outcome cutoffs withstand review.
3. The report distinguishes engineering acceptance, the control's behavior,
   and evidence for any independently specified predictive hypothesis. No
   result is promoted because tests pass or the program exits successfully.
4. Each evaluated hypothesis receives a recorded continue, improve or stop
   decision. Improvements explain a plausible mechanism and receive a new
   reviewed stage and future holdout; absent such a remedy, stop expansion of
   that hypothesis. Do not run open-ended tuning until a favorable label
   appears. Insufficient collection receives a bounded operating/reassessment
   decision, not a promised resolution date.

## P3: Independent Evidence And Real Quorum

Priority: evidence quality, concurrent with settlement waiting when useful.
Dependencies: accepted M1/M2/M5 contracts, qualifying source access and P1's
versioned cohorts before comparing changed forecasts. Review: its own stage
loop, including source and comparison-policy review.

### Work

- Qualify a second independent public price family for both `btc_spot_price`
  and `eth_spot_price` under the domain matrix's source criteria. Two Kraken
  pairs, mirrors or differently named endpoints from the same provider do
  not create a second family. Record actual endpoint/access evidence,
  documented cadence, persistence compatibility and provenance of independence.
- Define comparable spot observations: asset, quote currency, measurement
  meaning, observation time, Decimal units and parser version. Current
  dispatch compares typed values exactly and blocks unequal comparable values;
  genuine cross-provider differences can therefore block a bundle. Examine
  real fixtures before declaring a usable corroboration policy. This roadmap
  assigns no numerical tolerance and authorizes no silent averaging or
  relaxation of the accepted contradiction contract.
- Activate the two-family requirement only for item sets whose sources and
  comparison semantics have passed review. Preserve all participating source
  references through selection, conflict reporting, forecast lineage and
  export; selecting one representative must not erase corroboration evidence.
  If the current contract cannot represent a sound comparison, review that
  specific change before claiming corroboration.

### Acceptance Criteria

1. Both spot items have a verified second independent family and a documented
   current/required family policy; contemporaneous live acquisition confirms
   usability. An unavailable candidate remains a documented blocker.
2. Replay and failure tests demonstrate agreement, genuine disagreement,
   mirror deduplication, stale/missing/parse-failed/unknown inputs and loss of
   quorum. Contradictions preserve references and block required evidence;
   blocked inputs cannot become neutral forecasts.
3. A one-family observation cannot satisfy an active two-family requirement,
   and the old 1/1 cohort is never retroactively labeled corroborated.
4. Operational readiness/block counts and provenance survive readback and
   export for both teams. P2 reports any resulting coverage or predictive
   change on a new cohort; source diversity alone is not an edge verdict.

## P4: Source-Gated Team Waves

Priority: conditional breadth. Dependencies: reusable accepted cycle/export
contracts and a qualifying source for each team's required evidence. Review:
one stage plan and hard-review loop per small wave.

Macro rates is the next source investigation and first expansion candidate.
The accepted matrix records no viable rates source; FRED and BLS were rejected
for their evaluated API-key requirements, and scraped news calendars were
outside the default route. A public treasury yield feed remains a candidate
category, not a verified endpoint or availability claim.

Apply the existing source acceptance criteria before registration: public
HTTPS GET without authentication or keys, host allowlisting, compatibility
with persistence refusal policy and documented update cadence. Also establish
relevance to the team's event/resolution rules. Record unsuccessful candidates
and the reason, rather than weakening the criteria to fill the matrix.

After the rates assessment, consider politics, equity indices, gold and oil;
sports soccer, basketball and other sports follow only as source access and
resolution semantics qualify. A blocked rates source does not justify an
invented adapter or prevent separately qualified work. Give shared dispatch,
registry and CLI changes one integration owner per wave; reuse evidence and
persistence contracts without transplanting a crypto probability model into
another domain.

### Acceptance Criteria Per Team

1. Source qualification, required items, freshness, family independence,
   event identity and resolution semantics are documented with actual evidence.
2. The domain adapter and reviewed forecast rule traverse the full workflow
   for normal, stale, contradictory, missing, unknown and refused inputs.
   Unsupported routing stays explicit until those requirements are met.
3. Deterministic replay, bounded live operational smoke, local persistence
   readback and inclusion in P1's prospective collection/export are verified.
4. Update every matrix column separately: sources, adapter, fixtures, replay,
   smoke, settlement and families. Operational acceptance does not imply a
   settled result; P2/P5 conclusions remain specific to evaluated domains.
5. All ten IDs retain an explicit disposition. Ten-team completion means ten
   verified workflows. A narrower release or a stopped source search must
   name unsupported domains and cannot be described as ten-team completion.

## P5: Trigger-Gated Cost And Memory Arms

Priority: conditional research validation. Dependencies: P1 lineage and P2
evaluation discipline, plus each arm's trigger below. Review: separate stage
plans, verification and hard PASS for each activated arm.

### Cost-Adjusted Paper Results

Activation trigger: settled N >= 30 under the frozen evaluation selection.
Crossing it activates the work; it does not prove that suitable paper-decision
records already exist. Preserve needed decision-time context during P1 so it
is not reconstructed from later prices.

- Bridge canonical team forecasts into the existing central cost/liquidity/
  risk and paper-simulation path, including YES/NO conversion at that boundary.
  Reuse `team_forecast_to_side_edge_input` and existing strategy/paper ownership
  where compatible; do not create another competing orchestrator.
- Persist the link from forecast and accepted book to decision, abstention or
  simulated fill, with versioned fee/slippage/fill assumptions and settlement.
  Replay uses only information available at decision time. Missing historical
  inputs require new prospective paper records or an explicit limitation.
- Report settled paper results, costs, drawdown, capital lockup, unfilled and
  blocked cases, and fee/slippage/fill sensitivity. Report the cost cohort's
  own settled/pending counts. Forecast N must not stand in for missing fills,
  and pending NAV must not be used to tune the held-out method.

Acceptance: the report is reproducible from linked local records, distinguishes
gross from cost-adjusted results, preserves abstentions and failures, and
states whether the observed predictive advantage survives the declared paper
assumptions. Nonpositive, inconclusive or unmeasurable results remain valid
reported outcomes. No invented PnL or live execution is permitted.

### Memory-As-Context Benefit

Activation trigger: actual memory-gated handoffs have settled outcomes.
Existing memory-reference strings or readiness reports do not satisfy it.
Before such handoffs are generated, review and freeze their context selection,
comparison design and audit fields; outcome evaluation waits for the trigger.

- Use traceable, relevant and fresh historical research context available as
  of each handoff. Settled history and any learned summaries must precede the
  new forecast; held-out outcomes cannot enter their own context.
- Collect matched prospective forecasts with and without memory, retaining
  context identities/versions, handoff times, model/config and source inputs.
  Compare on the same settled events and report eligible, missing and excluded
  pairs, concentration and the limits of attributing changes to memory.
- State incremental predictive benefit, harm or insufficient evidence. Keep
  sample discipline consistent with P2 when using its verdict labels; this
  roadmap declares no separate memory-effect threshold.

Acceptance: the handoff lineage and as-of isolation are verified, the paired
settled comparison is reproducible, and the benefit claim matches the evidence.
If memory never enters the accepted workflow, record the unfired trigger and
its explicit final disposition. A triggered but unfinished arm remains open;
it cannot be relabeled untriggered to close the project.

## P6: Release State And Project Completion

Priority: final closure. Dependencies: the P1 pipeline, the applicable P2
research decision, and explicit completed, blocked or stopped dispositions
for P3/P4 and each P5 arm. Review: final stage plan and hard-review PASS on
the release state or documented stop package.

### Release Acceptance

1. Refresh the delivery-status narrative, ten-team matrix and operator runbook
   to the final revision. Cover BTC/ETH and later accepted commands, recurring
   operation, forecast persistence, export, evaluation, cohort versions,
   pending/dispute handling, raw expiry, recovery and backup/restore. Replace
   the runbook's obsolete reviewer-fallback guidance with the current rule;
   preserve historical stage-review records unchanged.
2. An operator can reproduce collection/readback, offline replay and the
   final evaluation from documented local setup and approved inputs. Verify
   recovery and backup/restore without erasing ordinary research data; M0's
   empty-schema repair record is not permission to drop populated schemas.
3. Record fresh regression evidence on the exact release revision: full
   Python 3.11 suite, relevant interpreter compatibility, compilation,
   whitespace and non-echoing secret checks, CLI inventory/help compatibility,
   deterministic replay/failure injection and opt-in local-DB lifecycle tests
   for changed persistence. Record every skip and its reason. Use bounded,
   opt-in public-source smoke to substantiate operational source claims;
   outages remain visible and cannot be replaced with fixture-only claims.
4. Compare import/help and representative cycle measurements with the M0/M4
   records on a stated workload. Explain regressions and operational bounds
   from measurements; do not manufacture a latency target or treat a large
   test count as evidence of predictive value.
5. Reconcile preserved-branch dispositions from the M0 decisions against any
   actual reuse. Record the final branch/commit, accepted changes, remaining
   limitations and rollback/recovery procedure. Historical governance remains
   historical; preservation alone does not imply integration.
6. Record a concrete push/merge/hold decision with destination and rationale.
   Execute publication or merging only under the user's authorization;
   document whether it occurred. An explicit hold is a valid release
   disposition, not a claim that this branch is merged. This roadmap does
   not itself authorize a push, merge or deployment.

### What Complete Means

Completion means a finite, auditable answer for the declared research scope,
plus a reproducible final state. It does not require a favorable answer and
must identify which of the following outcomes applies:

| Closure outcome | Required evidence |
| --- | --- |
| Research completed with observed predictive advantage | A prospective held-out `comparative_edge` result under the declared N >= 100 rule, valid paired market provenance, stated uncertainty/domain limits, and completed applicable cost and memory comparisons. It is an observed research result, not proof of future profit. |
| Research completed with no demonstrated edge | A valid settled `no_consistent_edge` result and a reasoned decision to stop the evaluated hypothesis, or a documented negative applicable cost/memory result that ends its use. Identify the tested method and limits; do not generalize to all possible methods. |
| Project closed inconclusive or constrained | Collection, source qualification, outcome provenance or a conditional arm cannot be completed within the documented operating scope, and the final record explicitly ends that work with counts, evidence, blocker and stop rationale. Preserve `insufficient_sample` where applicable. This is honest closure, not successful empirical validation. |

For every outcome, the final record must account for all P milestones, all
ten team IDs and both P5 triggers. A full ten-team delivery requires ten
verified workflows; narrower closure explicitly records the unfinished
coverage. An active trigger with missing work requires completion or a
terminal stop disposition, never an open-ended "later" entry in a document
marked complete. An early stop may close unfinished stages only through the
inconclusive/constrained route, with their acceptance criteria clearly unmet.

The core method cannot be called validated solely because the zero-impact
control ties the market, a small sample receives an indicative label, or the
infrastructure passes regression. A failed prospective-provenance or DB/replay
gate pauses affected collection/evaluation for repair; if repair is not
feasible, close with that limitation. Absent a justified improvement after a
negative result, stop the hypothesis rather than scale its automation.

## Sequence And Estimates

Critical path: P1 prospective collection and export -> actual market
settlement -> P2 evaluation/decision -> applicable P5 arms -> P6 closure.
P3 qualification and P4 source investigations can proceed during settlement
waiting. Their accepted changes enter new, versioned P1 cohorts and return
to P2. Failed gates can lead to a documented stop package and P6 without
pretending the blocked work was delivered.

Settlement waiting is controlled by eligible events and resolution, not by
engineering throughput. The mention of 2026-09-05+ cycles in M6 is a cohort
reference, not proof of persisted forecasts or a promised evaluation date.
No calendar completion date or sample-arrival rate is asserted here.

Use the predecessor's ranges only as estimation references pending each
reviewed stage's actual scope: M6 allowed 4-7 engineering days for initial
settlement plumbing; M1/M2 allowed 4-7 and 3-5 days for source/bundle work;
M5 allowed 2-5 days per small source-dependent wave; M4 allowed 3-5 days for
operational quality. These ranges are neither fresh commitments nor additive
estimates for P1-P6. Re-estimate the remaining work as ranges after P1's data
inventory, source qualification and each P5 trigger, separating implementation,
review/verification and market-driven waiting. Do not reuse the old 4-6 week
first-slice envelope as a project-completion forecast.

The next implementation batch is a reviewed P1 plan: establish the persisted
inventory, resolve baseline provenance, freeze prospective cohort rules, run
recurring collection and implement the auditable settlement export. This
document creates no scheduler, collection job, new source or evaluation result.

## How This Plan Relates To Its Predecessors

This plan supersedes the scheduling assumptions and "next batch" directions
of the [2026-09-05 delivery plan](2026-09-05-project-delivery-plan.md) for work
after `8b2025f0`. Its appended Delivery Status table and the accepted
[M0](../superpowers/plans/2026-09-05-m0-baseline-and-persistence-acceptance.md),
[M1](../superpowers/plans/2026-09-05-m1-parameterized-requests-and-adapters.md),
[M2](../superpowers/plans/2026-09-05-m2-evidence-bundle-and-dispatch.md),
[M3](../superpowers/plans/2026-09-05-m3-btc-vertical-slice.md),
[M4](../superpowers/plans/2026-09-06-m4-operational-quality.md),
[M5](../superpowers/plans/2026-09-06-m5-wave1-eth.md) and
[M6](../superpowers/plans/2026-09-06-m6-settlement-evaluation.md) plans remain
the delivery and review record, including their historical review exceptions.

The [domain matrix](2026-09-06-m5-domain-status-matrix.md) remains the source
qualification and per-team baseline; P1 makes its settlement-export protocol
executable. The [M0 decisions](2026-09-05-m0-baseline-decisions.md) retain
branch dispositions, DB acceptance evidence and latency measurements. The
[operations runbook](../runbooks/research-cycle-operations.md) remains the
operator entry point and is updated by the implementing stages and P6. The
current Claude Code review rule governs new reviews; historical fallback
records neither change that rule nor need rewriting.
