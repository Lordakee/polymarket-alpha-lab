# Project Delivery Plan

Date: 2026-09-05
Status: current planning baseline; milestones below are proposed, not completed
Scope: research data, team evidence, paper evaluation and maintainability

## Assessment

The project remains in Phase 1: a broad research and paper-evidence codebase,
not an integrated autonomous investment service. The next delivery target is
one reproducible BTC probability-event cycle with traceable evidence,
cost-aware decisions, durable readback and eventual settlement evaluation.
Connecting existing capabilities takes priority over adding more report families.

This plan supersedes the July progress checkpoint and the status/scheduling
assumptions of the July central-data plan. Historical documents remain design
references, not current agent instructions. This plan introduces no mandatory
model, reviewer vendor, delegation tool or push policy. Existing implementation
contracts use paper_only, report_only and readonly. This plan does not authorize
live trading or wallet/private-key handling.

## Evidence And Limits

- Inspected branch: `codex/central-data-node-b-persistence`, HEAD `f1344db8`.
- Node A: `93587738`; Node B: `38c7c5d5`; Python 3.11 repair: `6079ad13`.
- CodeGraph 1.6.0 reports an up-to-date index containing 5,844 Python files,
  284,741 nodes and 772,260 edges. It warns that v0.9.9 built the index.
  Indexed references locate implementation; they do not prove runtime behavior.
- The preceding rule-removal validation completed with 34,218 passed and
  2 skipped on Python 3.11 in 721.33 seconds. Compilation covered 5,844 files.
  These results precede this documentation update.
- No fresh external acquisition, migration or DB lifecycle test was performed
  for this assessment. Earlier cleanup records describe a manual local DB
  lifecycle check; that is not a checked-in, repeatable integration test.
- `tests/test_central_data_supabase_smoke.py` validates configuration and builds
  an adapter, but does not connect, migrate or read/write rows.
- The worktree contains intentional, uncommitted rule deletions. This update
  does not restore them, commit them or assume the branch has merged into main.

## Current Capability Map

| Area | Implementation evidence | Delivery gap |
| --- | --- | --- |
| Market acquisition | `api.py`, `pipeline.py`, Gamma/CLOB client | Existing callers are not connected to the new central transport. |
| Strategy/paper cycle | `strategy_cycle.py`, cost snapshots, paper journals/NAV | Central evidence through settlement is not demonstrated end to end. |
| Central Node A | Contracts, registry and safe transport modules | Production acquisition/dispatch integration. |
| Central Node B | Normalization, policy, codecs, store, psycopg and migration | Repeatable real-DB acceptance and operational integration. |
| Teams | Ten-team taxonomy, supplied-input builders, runnable BTC slice | Ten builders do not equal ten data-backed operational workflows. |
| Memory | Diagnostics, assignment/readiness and persisted history | Demonstrate useful, fresh, settled-outcome context in actual handoffs. |
| Reports/risk | Extensive calibration, cost, liquidity and proposal artifacts | One concise operator flow consuming genuine cycle outputs. |
| Delivery structure | CLI, tests, module index and local Postgres boundaries | Large CLI/report surface increases integration and verification cost. |

Primary source navigation:

- `src/polymarket_alpha_lab/cli.py`: command composition, approximately 15,000 lines.
- `src/polymarket_alpha_lab/strategy_cycle.py`: current market-to-paper orchestration.
- `src/polymarket_alpha_lab/crypto_btc_team.py`: supplied-input BTC workflow.
- `src/polymarket_alpha_lab/central_data_contracts.py`: acquisition/value states.
- `src/polymarket_alpha_lab/central_data_transport.py`: bounded public GET boundary.
- `src/polymarket_alpha_lab/central_data_psycopg.py`: central DB transaction boundary.
- `tests/test_central_data_supabase_smoke.py`: DB acceptance gap.
- `docs/index/phase1-module-index.md`: broader module navigation.

## Preserved Versus Integrated Work

Cleanup preserved unique work rather than indiscriminately merging branches.
Compare dependencies and semantic overlap before reusing these references:

| Work | Preserved reference | Proposed disposition |
| --- | --- | --- |
| Node 2C aggregation | `origin/codex/node2c-reviewed-assembly`, `05b5703a` | Evaluate exact implementation/tests for M2/M3; integrate only if needed. |
| Paper execution reducer | `origin/codex/20260629-execution-pipeline`, `f7843574` | Compare with strategy-cycle ownership before M3; avoid duplicate orchestration. |
| Historical governance | `origin/codex/node2c-governance-v8-20260722`, `886beadb` | Historical only; do not restore deleted governance. |

Preservation is not integration into the current branch or main. This planning
update performs no historical merge, commit, push or branch deletion.

## Target Flow

Registered source request -> bounded transport -> accepted raw provenance ->
normalized observations -> central evidence bundle -> team supplied inputs ->
canonical Decimal P(YES) forecast -> central cost/liquidity/risk decision ->
operator packet and optional paper simulation -> durable readback -> settlement
outcome -> calibration and research memory.

Each cycle has stable identity, as-of time, configuration/parser versions,
source references and explicit status. Replay uses accepted normalized inputs
and an injected clock without network calls. Zero, null, unknown, missing and
stale remain distinguishable. Teams own domain evidence and forecasts; central
components own cost, risk and allocation. Reuse local Supabase/Postgres and
existing codecs to avoid introducing another persistence architecture.

## M0: Baseline And Persistence Acceptance

Priority: P0. Dependencies: none. Estimate: 2-4 engineering days.

- Record current CLI commands/payloads and reconcile the preserved branches into
  explicit reuse, defer or reject decisions with dependency explanations.
- Convert earlier manual DB lifecycle verification into an opt-in test using a
  dedicated disposable local Supabase/Postgres test database, not ordinary data.
- Exercise migration/catalog constraints, insert/readback, idempotent retries,
  conflicting identities, rollback, retention cleanup/audit, observation
  references and sensitive-payload refusal.
- Test intended application-role permissions and sanitized errors without
  printing DSNs. Keep fake tests distinct from real integration results.
- Measure CLI import/help latency and representative cycle duration before
  refactoring. Select performance targets from measurements, not guesses.

Exit: rerunnable lifecycle command and fixtures provide real DB evidence;
branch reuse decisions and compatibility baseline are documented.

## M1: Parameterized Requests And Sources (Node C0/C1)

Priority: P0. Dependencies: M0 baseline; pure work can overlap DB tests.
Estimate: 4-7 engineering days.

- Design typed per-source parameters first. Current endpoint templates reject
  query strings and placeholders; do not replace that with arbitrary URL access.
- Specify allowed names, types/ranges, canonical encoding, request identity,
  pagination ceilings and budgets. Preserve host/DNS/redirect/proxy protections,
  credential rejection, response-size caps and timeout limits.
- Start with Gamma metadata, CLOB executable books and one registered BTC public
  source needed by one BTC event archetype. Document access model, freshness and
  domain relevance. Provider availability was not externally verified here.
- Defer account-oriented Data API coverage. Any additional public endpoint needs
  fixture proof that its fields are compatible with persistence refusal policy.
- Persist accepted raw provenance before publishing normalized observations.
  Refused sensitive payloads produce sanitized failure metadata, not raw storage.
- Add bounded retries/backoff, rate-limit and Retry-After handling where applicable,
  explicit exhaustion, timeout, parse-failure and schema-drift outcomes.

Exit: deterministic fixture adapters and negative tests cover parameter abuse,
pagination exhaustion, parser version changes and provenance. A bounded real
network smoke remains optional and separate from offline regression tests.

## M2: Bundle And Dispatch (Node C2)

Priority: P0. Dependencies: stable M1 contracts. Estimate: 3-5 engineering days.

- Implement source selection and deterministic bundles carrying market/team,
  as-of time, availability, hashes, timestamps, parser versions and lineage.
- Configure quorum per required item; provider mirrors are not independent
  sources. Meeting a one-family minimum does not establish corroboration.
- Missing/stale/unknown/parse-failed required evidence produces blocked
  availability and canonical zero-weight placeholders, not valid neutral input.
- Preserve contradictory source references and expose the conflict explicitly.

Exit: routing covers all ten IDs or explicitly reports unsupported status;
fixtures prove freshness, quorum, deduplication and deterministic ordering.
Routing coverage alone does not count as an operational team workflow.

## M3: BTC Vertical Slice (First Node D/E Delivery)

Priority: P0. Dependencies: M0 DB acceptance and M2. Estimate: 4-7 engineering days.

- Implement one pure BTC adapter and connect the existing builder while preserving
  canonical Decimal P(YES), including NO-side evaluation.
- Select one orchestration owner after comparing the preserved paper reducer
  with existing strategy-cycle behavior; do not create a second parallel pipeline.
- Add a bounded single-market/batch CLI entry with stable cycle status/readback.
  Reuse existing packet/report shapes where they fit.
- Block forecast use of unavailable required evidence. Any supplied probability
  baseline retains explicit origin, assumptions and version.
- Produce a concise operator packet: event/resolution criteria, evidence/as-of
  references, forecast, executable prices, cost-adjusted edge, liquidity,
  capital-lockup risk and blocked/watch/candidate explanations.
- Cover retry, restart and partial failure with stable event/cycle identities.

Exit: positive and blocked BTC fixtures traverse source, persistence, forecast,
operator packet and readback. Evidence is traceable; replay yields identical
canonical outputs; retries do not duplicate facts. No live trading or order
submission is introduced.

## M4: Operational Quality And Focused Refactoring

Priority: P1. Starts alongside M1; final acceptance follows M3.
Estimate: 3-5 engineering days, partly overlapping.

- Separate acquisition, parsing, persistence, forecast and paper-simulation
  failures. Current strategy-cycle broad exception handling can classify unrelated
  errors as fetch failures and silently skip simulation failures.
- Add redacted diagnostics for source latency/freshness, rate limits, parser/DB
  errors, blocked causes and retries with cycle correlation.
- Extract only CLI command groups touched by this delivery after compatibility
  tests for help, defaults, payloads and errors. Avoid wholesale CLI rewrites,
  mass module renames or new abstractions without demonstrated need.
- Create one runbook for setup, replay, opt-in DB/network tests, retention,
  recovery and backup/restore testing.
- Compare latency/resource use with M0 and then define workload budgets.
  Consider a CodeGraph rebuild separately because of its approximately 1.8 GB
  index and builder-version warning; it is not a feature prerequisite.

Exit: failure injection is diagnosable, outputs remain sanitized, CLI behavior
is compatible, and operators can reproduce success/failure from the runbook.

## M5: Staged Multi-Team Expansion

Priority: P1. Dependencies: accepted M3 contracts.
Estimate: 2-5 engineering days per small wave, highly source-dependent.

- Start with ETH and macro rates if accessible sources support their required
  evidence. Then assess politics, indices and commodities. Sports follows when
  source access, fixtures and resolution semantics are demonstrated.
- Maintain separate columns for source availability, adapter implementation,
  fixture coverage, end-to-end replay, operational smoke and settlement data.
- Parallelize independent adapters/tests after contract stabilization. Give
  shared dispatch/orchestration files one integration owner per wave.
- Reuse evidence contracts, not domain probability models. Unsupported teams
  remain explicitly unsupported or blocked rather than receiving invented data.

Exit per team: normal, stale, contradictory and missing-input cases traverse
its full workflow with domain resolution rules. Ten-team completion means ten
verified workflows, not ten builders or stubs.

## M6: Settlement And Research Value

Priority: P1. Dependencies: M3; collection can overlap M4/M5.
Estimate: 4-7 engineering days of initial plumbing plus market-driven waiting.

- Join forecasts/paper decisions to resolved outcomes with event identity,
  cutoff, revision history, settlement lag and pending status.
- Evaluate Brier score, log loss with declared clipping, calibration, coverage
  and cost-adjusted paper results against market-implied and simple baselines.
- Use as-of data and time-ordered held-out evaluation to prevent look-ahead
  leakage. Do not tune from pending NAV or the held-out evaluation set.
- Report sample counts, uncertainty, domain concentration, exclusions, drawdown,
  capital lockup and fee/slippage/fill sensitivity.
- Use memory as traceable research context when freshness, relevance and settled
  outcomes support it; measure out-of-sample benefit rather than assuming it.

Exit: a repeatable settled-outcome report states both results and limitations.
Small samples remain insufficient evidence. Choose numeric sample/performance
thresholds before evaluation based on event frequency and statistical purpose;
this assessment supplies no invented profitability target.

## Sequence And Estimates

Critical path: M0 -> M1 -> M2 -> M3 -> operational acceptance -> M6 evaluation.
M4 can overlap adapter work; M5 starts after the vertical slice stabilizes.
A first-slice planning envelope is roughly 4-6 working weeks for one primary
engineer plus independent testing/documentation support, excluding settlement
waiting. These are estimates, not promised dates. Re-estimate after M0 and M1.

Useful parallel lanes: isolated DB tests, source fixtures/pure adapters,
post-contract domain adapters, and runbook/acceptance evidence. Avoid multiple
workers editing shared contracts or the same CLI functions. No fixed model,
provider or concurrency count is required by this plan.

## Verification And Delivery

Each milestone records files/revision, commands/results, fixture provenance,
known gaps and rollback/compatibility notes. Verification layers are:

1. Pure contracts, codecs, reducers and fake transport.
2. Real local DB migration/lifecycle in isolated test resources.
3. Optional bounded public-source smoke with provider/time recorded.
4. End-to-end deterministic replay and failure injection.
5. Python 3.11 and deployment-interpreter compatibility, full regression tests,
   patch whitespace checks and non-echoing secret scans.

Skip counts/reasons stay visible. Skipped integration tests are not DB acceptance;
green unit tests do not prove operational reliability or economic value. Source
changes receive appropriate review without restoring vendor-specific mandates.

## Deferred Scope And Stop Conditions

Defer HTML/browser scraping, WebSockets, new database backends, general-purpose
agent platforms and further report-history combinations unless a concrete
workflow requires them. When a provider is unavailable or incompatible with
persistence policy, narrow coverage or replace it; never fabricate evidence.

If DB acceptance/replay fails, repair the contract before team expansion. If
out-of-sample value is absent, improve sources/hypotheses or stop the strategy
instead of scaling automation. A later execution phase needs a separate user
decision and design for authorization, credential isolation, reconciliation,
audit, capital limits, emergency stop and rollback; M6 does not authorize it.

## Next Implementation Batch

The next code batch is M0 plus pure M1 request-contract design: settle branch
reuse decisions, make DB lifecycle tests reproducible, specify bounded request
parameters and choose one BTC event/source fixture set. These tasks are planned,
not claimed complete by this documentation change.
