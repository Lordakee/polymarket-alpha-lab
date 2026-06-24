# Paper-Only Proposal/Broker Design Spec (2026-06-24)

## Goal

Define the future paper-only internal architecture for proposal generation, risk gating, broker abstraction, order lifecycle tracking, position reconciliation, and audit logging while preserving the current Phase 1 boundary.

This document is intentionally a design spec, not an implementation mandate. It exists so future implementation work can expand the autonomous pipeline without rediscovering the intended boundaries.

## Current Boundary

Today the system remains:

- paper-only
- report-only
- read-only where CLI inspection exists
- module-local for most Phase 2 reporting surfaces
- free of live trading, authenticated trading, wallet handling, private-key handling, account mutation, and order submission

Any future execution surface must respect that boundary until explicitly promoted through the roadmap stages in `docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md`.

## Target Internal Shape

The next useful execution abstraction should be internal first, not user-facing automation.

### Proposal Surface

A proposal object should be the first internal boundary between research/scoring and any future execution mode.

A future internal proposal should describe:

- proposal id
- generated_at
- market/event identifier
- selected side
- recommended paper notional
- source reason codes
- source evidence pointers
- paper-only hard flags
- explicit status such as `candidate`, `blocked`, `watch`, `approved_candidate`, or `retired`

A proposal is not an order. It should not contain:

- wallet material
- signing inputs
- exchange-specific order payloads
- live execution preference
- financial advice

### Risk Gate Surface

The risk gate should consume proposals and emit proposal risk verdicts.

A future risk gate should check:

- screening/readiness gate state
- queue/risk budget state
- duplicate exposure
- theme/event concentration
- stale evidence age
- cost/liquidity stress
- research packet quality

Risk verdicts should stay deterministic and paper-only:

- `pass`
- `watch`
- `blocked`

A `pass` verdict should not mean “submit now.” It should mean “this proposal remains eligible for the next controlled execution stage.”

### Broker Interface

The broker interface should be the first live-boundary abstraction, but it must still start in paper mode.

Recommended internal interface:

```text
submit_proposal(proposal, risk_verdict, mode) -> broker_result
```

Recommended mode progression:

1. `paper_only`
2. `human_approval_required`
3. `live_pilot`
4. `strategy_whitelisted_live`

The paper-only implementation should:

- accept the proposal
- simulate fill assumptions
- emit a paper execution record
- persist lifecycle metadata
- never contact exchange auth or signing code

### Order Lifecycle Manager

Even in paper mode, the system should track lifecycle states explicitly.

Useful lifecycle states:

- `proposed`
- `risk_passed`
- `risk_blocked`
- `paper_submitted`
- `paper_filled`
- `paper_cancelled`
- `human_approval_pending`
- `approved`
- `rejected`
- `expired`

This makes later live reconciliation far easier because paper and live modes share one lifecycle vocabulary.

### Position Reconciler

The reconciler should not be live-first. It should start by reconciling:

- paper proposal intent
- paper simulated fill
- paper journal entry
- NAV snapshot
- outcome tracker state

That paper reconciler becomes the safety template for any later live reconciler.

### Audit Journal

Every proposal and execution-mode transition should produce an audit record with:

- proposal id
- mode
- source reports
- risk verdict
- decision reason codes
- resulting lifecycle state
- operator-readable summary
- timestamp

The audit journal is the bridge between research diagnostics and later operational controls.

## Module-Local vs Shared Interface Boundaries

### Should stay module-local first

- proposal/risk diagnostics that depend on unstable report families
- experimental screening heuristics
- queue-specific or segment-specific policy logic

### Should become shared internal interfaces later

- `Proposal`
- `ProposalRiskVerdict`
- `Broker`
- `OrderLifecycleRecord`
- `ReconciliationRecord`
- `AuditEvent`

The rule of thumb: shared interfaces should only emerge after at least two internal consumers need the same stable contract.

## Promotion Gates

The design should assume staged promotion, not sudden automation.

### Gate 1: Paper proposal stability

Evidence needed:

- proposal diagnostics are deterministic
- risk diagnostics are deterministic
- proposal/risk verdicts match operator inspection
- paper journal and NAV remain consistent

### Gate 2: Internal broker simulation stability

Evidence needed:

- paper execution assumptions are reproducible
- lifecycle transitions are complete and logged
- paper reconciliation breaks fall below an accepted threshold

### Gate 3: Human approval workflow readiness

Evidence needed:

- proposals can be paused for operator approval
- approval/rejection is persisted and auditable
- approval workflow does not leak live-execution capability

### Gate 4: Live pilot boundary

Evidence needed:

- paper-to-live mode boundary is explicit
- live mode requires separate auth/secret handling
- kill switch and rollback are tested
- live reconciliation equals paper assumptions under controlled capital

## Anti-Goals

This design should not:

- rush live execution
- turn proposals into implicit orders
- hide live-auth code inside research modules
- mix financial advice with diagnostics
- allow research modules to control broker mode directly
- expose live broker mode through research CLI commands

## Recommended Implementation Posture

The next implementation step is not live trading. The next step is an internal paper-only proposal record family:

1. proposal reducer/store
2. proposal risk gate reducer
3. paper broker adapter
4. paper order lifecycle state machine
5. paper reconciler
6. audit journal sink

That sequence keeps the system measurable while staying inside the current safe boundary.
