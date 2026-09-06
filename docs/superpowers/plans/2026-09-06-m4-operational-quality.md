# M4 Stage Plan: Operational Quality And Focused Refactoring

Date: 2026-09-06
Stage: M4 of the [Project Delivery Plan](../../roadmap/2026-09-05-project-delivery-plan.md)
Status: plan review completed; findings dispositioned (see the final section)
Depends on: M3 (accepted; commit `76c0a48e`)

## Parent-Plan Traceability

This stage implements the M4 milestone: stage-specific failure
classification in the strategy cycle, structured redacted cycle
diagnostics, one focused CLI extraction with a compatibility contract, a
single discoverable operations runbook, and a measured latency comparison
against the M0 baseline. Multi-team expansion (M5) and settlement
evaluation (M6) stay out of scope.

## Current-Code Facts

- `strategy_cycle.py` collapses every market-pipeline exception into
  `blocked_fetch_error` (one broad `except Exception` spanning fetch,
  normalization, and cost-snapshot stages) and silently `continue`s past
  paper-execution failures, so simulation defects are invisible.
- The M3 CLI handler `_run_btc_research_cycle_command` and its
  `_DiscardingCentralStore` live inside `cli.py` (~15k lines); the CLI
  inventory contract is 78 commands.
- `AcquisitionOutcome` already carries attempts, retry-after, failure
  status, and reason codes; the M3 cycle result carries blocked reasons.
- The M0 baseline recorded interpreter 0.0264 s, CLI import 1.8527 s,
  help 0.9643 s on this workstation.

## Design Decisions

1. Failure classification is stage-scoped, not exception-message-based.
   The market pipeline's broad try block is split into sequential guarded
   segments at the stage boundaries actually present in the code
   (fetch, normalization, forecast selection, cost snapshot, report
   assembly — the exact boundary list is verified against the code during
   implementation and pinned by tests), appending
   `blocked_<stage>_error` per segment. The existing skip-to-next-market
   semantic is preserved unchanged: today ANY failure in the block
   already skips `paper_trade_context` population and dedupe
   first-occurrence behavior; segmented guards reproduce exactly that
   control flow, so no contract changes. Exception TYPE NAMES only are
   recorded in a parallel per-market diagnostics tuple (never messages,
   so no payload can leak). `blocked_fetch_error` remains emitted for
   fetch-stage failures; the vocabulary strictly gains granularity, and
   the plan documents that consumers matching the literal string for
   non-fetch failures will now see the new stage codes instead
   (migration note, no dual-writing).
2. Paper-execution failures become visible but non-fatal. Each failed
   candidate appends the exception type name to a new additive report
   field `paper_execution_failure_types: tuple[str, ...] = ()` appended
   at the very END of the frozen dataclass (after all defaulted flag
   fields), keeping every existing positional and keyword constructor
   valid; constructor patterns across the test corpus are verified before
   the change lands. The sink contract is unchanged and sink failures
   still propagate. No DB row codec or schema changes in this stage, so
   nothing persisted changes and rollback is trivially safe.
3. Diagnostics are a pure text reducer over accepted contracts with an
   explicit signature: `format_btc_cycle_diagnostics(outcomes:
   Sequence[AcquisitionOutcome], bundle: EvidenceBundle, result:
   BtcCycleResult) -> str` summarizes per-source failure status,
   attempts, retry-after, and reason codes, bundle item availability,
   and cycle block reasons into deterministic, redacted lines. The CLI
   is the impure composer that gathers outcomes and calls the reducer;
   the reducer imports nothing impure.
4. The CLI extraction moves only the handler implementation (the
   private `_run_btc_research_cycle_command` and `_DiscardingCentralStore`)
   into `btc_research_cycle_cli.py`; command REGISTRATION stays in
   `cli.py`, which imports and dispatches unchanged. Compatibility is
   pinned two ways: the 78-command inventory (command names) diffs empty,
   and `btc-research-cycle --help` output is byte-identical before and
   after. No other command group is touched.
5. One runbook becomes the operator entry point:
   `docs/runbooks/research-cycle-operations.md` covering setup, offline
   replay, opt-in DB lifecycle and network smokes (env gates and the
   disposable forward procedure), retention and repair, failure
   recovery, backup/restore pointers to the existing supabase document,
   and the latency baseline table with fresh measurements.
6. Latency is measured, not optimized: rerun
   `scripts/m0_baseline_measure.py`, record the comparison in the
   runbook, and only then discuss budgets. CodeGraph rebuild (~1.8 GB
   index, version-mismatched builder) is explicitly deferred again.

## Work Items

1. `src/polymarket_alpha_lab/strategy_cycle.py` (edit): stage-scoped
   classification + `paper_execution_failure_types` additive field.
2. `src/polymarket_alpha_lab/btc_cycle_diagnostics.py` (new): pure
   diagnostics reducer.
3. `src/polymarket_alpha_lab/btc_research_cycle_cli.py` (new) +
   `cli.py` (edit): the bounded extraction; inventory unchanged.
4. `docs/runbooks/research-cycle-operations.md` (new): the runbook.
5. Tests:
   - extend `tests/test_paper_strategy_cycle_report.py`-adjacent cycle
     tests: fetch-stage vs normalization-stage vs cost-stage
     classifications; paper-execution failure visibility (type names
     recorded, candidate skipped, sink still called for successes).
   - `tests/test_btc_cycle_diagnostics.py`: determinism, redaction
     (no payload/URL text), coverage of failure/attempt/retry fields.
   - CLI test: command still registered, dispatch reaches the extracted
     module; inventory file regenerated and diffed empty.
6. Latency measurement recorded in the runbook with the M0 comparison.

## Verification

- Focused new/extended suites green; full Python 3.11 regression;
  compile checks; `git diff --check`; credential scan; CLI inventory
  diff empty; live opt-in smoke still green.

## Acceptance Criteria (mirrors delivery-plan M4 exit)

1. Injected failures are diagnosable by stage; paper-execution failures
   are counted and typed instead of silently swallowed.
2. Diagnostics output is structured, deterministic, and redacted.
3. CLI behavior is byte-compatible for `--help` and the command
   inventory; only the one touched command group moves.
4. An operator can reproduce setup, offline replay, opt-in tests,
   retention, recovery, and backup from one runbook.
5. Latency comparison versus M0 is recorded from real measurements.
6. No new persistence surfaces, no batch mode, no team expansion.

## Rollback

Revert the six work items; no schema or data dependency.

## Plan Review Response (2026-09-06)

Claude Code reviewed this plan read-only (default model; the opus-5
route was still unavailable) and returned REQUEST_CHANGES: two Critical,
two Major, two Minor. Dispositions:

1. Critical stage-classification soundness: ACCEPTED with correction.
   The reviewer's impossibility claim was overstated (any failure today
   already skips context population), but the substantive point stands:
   the guarded segments must follow the code's real stage boundaries
   (five, not three) and the plan must state explicitly that the
   skip-to-next-market and first-occurrence semantics are preserved,
   which it now does, with tests pinning the boundary list.
2. Critical additive-field placement: ACCEPTED; the field is appended at
   the very end of the dataclass and constructor patterns are verified
   across the test corpus before landing.
3. Major CLI extraction scope: ACCEPTED; handler-implementation-only
   move, registration stays, inventory plus byte-identical command help
   as the dual compatibility contract.
4. Minor blocked_fetch_error vocabulary: ACCEPTED; documented as a
   strict granularity gain with an explicit consumer migration note.
5. Major diagnostics purity: ACCEPTED; explicit reducer signature with
   the CLI as the impure composer.
6. Minor rollback/DB: ACCEPTED and strengthened; this stage changes no
   DB codec or schema, so persisted data is untouched.

## Recorded Verification (2026-09-06)

- Focused: stage-classification suite 5 passed (fetch/normalization/
  forecast stage codes, exception-type recording, paper-execution
  visibility, field defaults/validation); diagnostics suite 2 passed
  (determinism, structure, redaction); full strategy-cycle and BTC
  suites green.
- CLI compatibility: `btc-research-cycle --help` byte-identical after the
  extraction; command inventory regenerated — 78 commands unchanged
  (header comment only).
- Latency measured and recorded in the runbook (import 0.9579 s vs M0
  1.8527 s; help 1.0724 s vs 0.9643 s; interpreter 0.0293 s).
- Two pre-existing guard tests needed mechanical updates caused by this
  stage, both without weakening: the scope test's vocabulary carve-out
  gained `paper_execution_failure_types` (same paper-execution family as
  the existing carve-outs), and the persistence iron-rule allowlist
  repinned two pre-existing legacy-file violations whose line numbers
  shifted (identical violations, new lines).
- Full Python 3.11 regression: 34273 passed, 7 skipped in 702.20 s.
- Compile checks, `git diff --check`, credential scan: clean.
