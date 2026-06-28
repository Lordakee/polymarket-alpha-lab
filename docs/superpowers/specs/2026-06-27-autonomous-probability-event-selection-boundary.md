# Autonomous Probability Event Selection Boundary Spec (2026-06-27)

## Purpose

Define the near-term boundary for autonomous probability event selection. This
is a report-only architecture boundary: it may scan, research, score, compare,
summarize, gate, and track paper outcomes, but it must not create an execution
surface.

The objective is to make future parallel nodes easier to assign without turning
selection reports into implicit trade instructions.

## Operating Boundary

Current Phase 1 and near-term work is limited to:

- Paper-only outputs.
- Report-only diagnostics.
- Read-only inspection paths unless a node explicitly persists a derived report
  to local Supabase/Postgres.
- No live trading.
- No authentication.
- No wallet, private-key, account, credential, or signing access.
- No order creation, order submission, order cancellation, order replacement, or
  exchange mutation.
- No new ranking, sizing, allocation, selection, or capital behavior unless a
  separate spec/plan is reviewed and accepted first.

A positive score, agreement result, gate result, or allocation proposal means
"eligible for report review." It does not mean "place an order."

## Durable Data Boundary

All durable project data must use local Supabase/Postgres only.

Future nodes must not introduce:

- SQLite durable persistence.
- JSONL durable persistence.
- Redis.
- Mongo.
- Hosted database assumptions.
- Generic database abstraction layers.
- File-backed durable stores.
- Local files as durable project data stores.

Legacy file-backed surfaces are read-only compatibility surfaces unless a
specific migration node is approved. New stores, loaders, migrations, runbooks,
fixtures, and tests must preserve the local Supabase/Postgres-only assumption.

## Report-Only Chain

The autonomous probability event selection chain should remain an auditable
series of derived reports.

1. Market scan
   - Reads public market/event/order book data.
   - Emits candidate scan diagnostics and rejection reasons.
   - Must not emit orders, order intents, auth requests, or wallet references.

2. Research
   - Builds paper research packets from candidate markets.
   - Captures rule text, resolution source, thesis, invalidating conditions,
     liquidity context, and source timestamps.
   - Produces evidence for later scoring, not execution instructions.

3. Forecast and evidence
   - Runs forecast providers, calibration checks, evidence snapshots, and
     quality gates.
   - Preserves source evidence and generated-at timestamps.
   - Keeps forecast probabilities separate from allocation or execution logic.

4. Probability selection summary and history
   - Summarizes selected probability candidates from prior reports.
   - Persists summary/history reports only through local Supabase/Postgres.
   - History commands should default to read/reduce/print behavior unless a
     reviewed node explicitly adds derived-report persistence.

5. Scorer reports
   - Autonomous market scorer outputs are priority diagnostics.
   - Scorer reports may explain liquidity, time, edge, evidence, and quality
     features.
   - Scorer reports must not become trade tickets or broker requests.

6. Agreement audit
   - Compares probability summaries, scorer reports, forecast evidence, and
     gate states for consistency.
   - Emits agreement/disagreement reason codes, stale-source flags, missing
     evidence flags, and review recommendations.
   - Agreement is an audit signal only; it cannot bypass readiness gates.

7. Allocation proposal
   - Produces paper-only allocation proposal reports from approved report inputs.
   - May summarize notional recommendations only as paper diagnostics.
   - Must not add new sizing behavior, allocation policy, or portfolio budgets
     without a separate reviewed plan.

8. Readiness and gates
   - Readiness gates consume upstream reports and emit pass/watch/blocked style
     diagnostics.
   - Gates should preserve `paper_only`, `report_only`, and `readonly` hard
     flags where the current report family uses them.
   - A gate pass is not approval for live trading, auth, signing, or exchange
     mutation.

9. Paper ledger, NAV, and outcome tracking
   - Paper ledger reports track simulated lifecycle effects from paper proposal
     reports.
   - NAV reports track paper portfolio state and risk trends.
   - Outcome tracking records market resolution and forecast/selection
     performance.
   - These reports close the measurement loop; they do not open a live execution
     loop.

## Parallel Development Map

Future workers should split ownership by report family and avoid editing shared
CLI or README surfaces unless the node explicitly owns them.

| Node | Suggested exclusive ownership | Avoid concurrent edits |
| --- | --- | --- |
| Market scan/research source report | `src/polymarket_alpha_lab/project_screening*.py`, research packet modules, matching tests | Probability summary, scorer, allocation, ledger files |
| Forecast/evidence report | `forecast_*`, `strategy_evidence*`, `phase_2_evidence*`, matching tests | Allocation proposal and readiness gate files |
| Probability selection summary/history | `paper_probability_selection_summary*`, `supabase_probability_selection_summary*`, matching tests | Scorer and allocation proposal files |
| Scorer report persistence | `autonomous_market_scorer*`, `supabase_autonomous_market_scorer_config.py`, matching tests | Probability history and readiness digest files |
| Agreement audit | New agreement-audit modules and tests only | Existing scorer/probability/allocation behavior unless separately owned |
| Allocation proposal/report history | `paper_autonomous_allocation_proposal*`, related Supabase config/store/history tests | Ledger, NAV, outcome tracking files |
| Readiness/gates/digest | `paper_autonomous_readiness_*`, screening gate/transition modules, matching tests | Allocation proposal internals unless the interface is already stable |
| Paper ledger | `paper_autonomous_investment_ledger*`, related Supabase config/store/history tests | NAV and outcome tracking files |
| NAV/risk trends | `paper_nav_*`, `nav_risk_*`, matching tests | Ledger and outcome tracking files |
| Outcome tracking | `outcome_*`, `paper_outcome_*`, matching tests | NAV, ledger, and scorer files |
| CLI/report viewer | One command family at a time in `cli.py` plus command-specific tests | Any other worker editing `cli.py` |
| Docs/handoff | One markdown file at a time under explicit ownership | README unless specifically assigned |

If two workers need `cli.py`, migrations, README, or a shared config module, the
work should be serialized or split so only one worker owns that file at a time.

## Acceptance Checklist For Future Nodes

Every implementation node that touches this boundary should complete this
checklist before handoff:

- Scope guard: tests or static checks prove no live trading, auth, wallet,
  private-key, signing, order creation/submission/cancel/replace, or exchange
  mutation surface was added.
- Persistence guard: tests or static checks prove durable writes use local
  Supabase/Postgres only and do not add SQLite, JSONL durable persistence,
  Redis, Mongo, hosted DB assumptions, generic DB abstraction, or file-backed
  durable stores.
- Report contract tests: focused tests cover the new report dataclasses,
  reducers, DB row conversion, stores/readers, and CLI output where applicable.
- Target tests: run the smallest focused test slice for the changed report
  family and record exact commands/results in the handoff.
- Full tests: run the full suite before a node is considered merge/push ready.
  If the main integrator explicitly defers full-suite verification, the node is
  a non-push handoff only and must not be pushed.
- Scope tests: add or update command/module scope tests when a new CLI command,
  persistence config, or boundary-sensitive report is introduced.
- Opencode review: route the read-only review gate to local opencode with
  `zhipuai-coding-plan/glm-5.2` and variant/thinking `max`; do not use fast
  mode.
- CodeGraph sync: run `codegraph sync` when `.codegraph/` exists after code
  changes and before claiming the node is ready.
- Diff hygiene: run `git diff --check` and compile verification for code nodes.
- Push policy: do not push until the node is committed, target tests pass, full
  tests pass, diff/compile checks pass, CodeGraph is synced, secret scan is
  clean, and opencode review is approved.

## Explicit Non-Goals

This boundary spec does not authorize:

- Live broker integration.
- Human approval workflow changes.
- Credential or secret-management work.
- Wallet/account discovery.
- Exchange order mutation.
- New ranking or sizing policy.
- New allocation behavior.
- New durable persistence outside local Supabase/Postgres.

Any one of those requires its own reviewed spec and implementation plan.
