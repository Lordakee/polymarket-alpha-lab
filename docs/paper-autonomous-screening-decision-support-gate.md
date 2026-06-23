# Paper Autonomous Screening Decision Support Gate

## Scope

The Paper Autonomous Screening Decision Support Gate is paper-only/report-only/read-only decision support for Polymarket probability-event screening. It combines upstream paper reports into a gate status and recommended next step for operator review.

The gate consumes already-produced and persisted upstream paper reports. It does not create new market research, change screening weights, mutate source reports, or introduce execution behavior.

Gate status and recommended-next-step fields are operator review aids, not approvals. They help an operator decide whether the persisted paper evidence is ready for another paper review step, needs more evidence, or should stay blocked for manual inspection.

This surface is not financial advice, not investment ranking, not automatic live investing, not order instruction, and not execution authorization.

## Source Reports

The source of truth is the set of already-produced and persisted upstream paper reports selected by the caller or DB history loader. The gate should treat those reports as immutable evidence:

- persisted paper project-screening and packet/operator-flow reports
- persisted paper quality and history reports
- persisted paper risk, cost, and evidence summaries when they are already part of the upstream report set
- source timestamps, status counts, reason codes, and report freshness signals

The gate may summarize report status, freshness, duplicate timestamps, reason-code pressure, and upstream paper evidence completeness. It must not fetch live market data, refresh upstream evidence, read accounts, or repair missing reports.

## Operator Flow

1. Upstream paper workflows produce and persist their own report artifacts.
2. The gate loader selects the requested persisted upstream paper report window.
3. The gate reducer evaluates the already-persisted reports for decision-support status and reason codes.
4. The operator reads the gate status, recommended next step, source counts, freshness signals, and reason-code summary.
5. Any follow-up action remains a paper review action outside the gate reducer.

The flow ends at report output. It is a paper evidence checkpoint, not an execution workflow.

## CLI Contract

The shipped command is a read-only env-only CLI:

```bash
polymarket-alpha-lab paper-autonomous-screening-decision-support-gate --limit 25
```

The operator-flow DB and action-gated queue decision-support DB are required
upstream persisted-report sources. The rank-stability DB is optional; when it
is enabled, the default single-connection read helper expects the optional
rank-stability DB and the two required upstream DBs to use the same DSN.

The command accepts only `--limit`. It does not accept command-line DB targets,
does not persist the final report, and does not create missing upstream inputs.

## Gate Status and Next Step

Gate status should communicate whether the selected upstream paper evidence is usable for the next paper screening review:

- `pass`: upstream paper evidence is complete enough for the configured paper review step.
- `watch`: upstream paper evidence exists but has freshness, completeness, duplicate-timestamp, or recurring-reason concerns.
- `blocked`: upstream paper evidence is missing, stale, internally inconsistent, or blocked by upstream risk/status signals.

The recommended next step should be a paper review label such as continue paper review, refresh upstream paper evidence through the normal upstream workflow, inspect reason codes, or hold for manual review.

A `pass` gate is not permission to trade. A `watch` gate is not a live monitoring instruction. A `blocked` gate is not an exchange action. All three statuses are report labels for paper screening operators.

## Transaction and Cost Awareness

Transaction/cost awareness is upstream evidence. The gate may report whether upstream paper cost, fee-drag, slippage, fill-quality, or cost-discipline summaries are present and whether their already-computed statuses contribute to the gate result.

There is no live fee estimation, no live trading, no order construction, no order signing, no order submission, no order cancellation, no order replacement, and no exchange mutation in this gate.

The gate must not compute live transaction costs, query current fee schedules, request order books, build order payloads, or transform cost awareness into capital allocation.

## Review Boundaries

The Phase 1 boundary is explicit:

- no live trading
- no automatic live investing
- no auth
- no key handling
- no wallet handling
- no account handling
- no account reads
- no order instruction
- no order construction
- no order signing
- no order submission
- no order cancellation
- no order replacement
- no execution authorization
- no exchange mutation
- no investment ranking
- no financial advice

Operator notes and runbooks should describe report fields, reason codes, and paper review outcomes only. Do not document secret values, credentials, DSNs, env contents, wallet material, private keys, account identifiers, or raw payloads that could expose operational secrets.

The gate is a paper/report/read-only reducer over persisted evidence. It must stay separate from authentication, key or wallet handling, account handling, exchange clients, live execution, and any component that can mutate exchange state.
