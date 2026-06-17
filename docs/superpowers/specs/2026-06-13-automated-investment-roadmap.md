# Automated Investment Roadmap

## Purpose

Define the staged path from read-only Polymarket research to controlled automated execution. The goal is not to automate quickly. The goal is to make automation technically feasible, measurable, reversible, and limited to strategies that have earned it through evidence.

## Operating Principles

- Research and execution are separate systems.
- A market score is a priority signal, not a trade instruction.
- Every strategy must pass paper-trading gates before any live capital.
- Every live order must pass risk limits, liquidity checks, and audit logging.
- Every automation level must have a rollback path to the previous level.
- Private-key handling belongs behind a dedicated execution boundary, not inside research or scoring code.

## Automation Levels

### Level 0: Read-Only Market Intelligence

Goal: build the data foundation and market scanner.

Capabilities:

- ingest Gamma, CLOB, Data API, and WebSocket market data
- normalize events, markets, and outcome tokens
- compute liquidity, activity, time, rule-clarity, and duplicate-risk scores
- create watchlists and candidate edge records

Allowed actions:

- read public data
- store raw and normalized data
- generate candidate rankings

Not allowed:

- account authentication
- private-key handling
- order placement

Promotion gate:

- data integrity checks pass
- market snapshots are reproducible
- candidate scores are explainable from stored inputs

### Level 1: Automated Research And Paper Trading

Goal: convert candidates into research packets and simulated trades.

Capabilities:

- generate research packet per candidate
- record thesis, invalidating conditions, rule text, and resolution source
- simulate fills with bid/ask and order book walk
- maintain paper positions and mark them at executable exit prices
- report performance by strategy, market class, price bucket, and holding period
- optionally gate continuous paper runs on the latest local Strategy Risk Audit status before public client construction

Allowed actions:

- automated paper trades
- automated rejection logs
- automated risk reports
- optional local audit preflight for paper-only/report-only continuous runs

Not allowed:

- live orders
- authenticated trading
- treating `audit_ready` as approval for proposals, live orders, authenticated trading, or automatic credential use

Promotion gate:

- strategy passes validation gates in `docs/research/validation-gates.md`
- paper fills are cost-adjusted and not midpoint-only
- rejected candidates are logged with reasons
- local Strategy Risk Audit readiness can support the evidence packet, but the optional run preflight itself is only an operational paper-run pause and is not a strategy-promotion signal

### Level 2: Human-Approved Trade Proposals

Goal: produce actionable proposals while keeping final execution manual.

Capabilities:

- create trade proposal with side, token, expected edge, maximum size, and exit rule
- run pre-trade risk checks
- attach source evidence and audit trail
- require explicit human approval before any order leaves the system

Allowed actions:

- proposal generation
- human approval workflow
- optional manual execution journal import

Not allowed:

- unattended live order placement
- automatic credential use

Promotion gate:

- proposal quality is stable under human review
- false positives and rejected proposals are tracked
- manual execution results match expected fill assumptions within tolerance

### Level 3: Risk-Limited Live Pilot

Goal: test authenticated execution with small capital, hard caps, and tight rollback controls.

Capabilities:

- authenticated execution gateway in a separate module
- paper broker and live broker share one interface
- order lifecycle tracking for submitted, filled, partially filled, canceled, rejected, and expired orders
- position reconciliation between local journal and exchange state
- kill switch that cancels open orders and disables new orders

Allowed actions:

- small live orders for whitelisted strategies
- conservative position sizing
- automatic cancellation under risk or heartbeat failures

Required controls:

- per-order maximum loss cap
- per-market and per-theme exposure caps
- daily loss stop
- drawdown stop
- liquidity participation cap
- stale-data rejection
- manual disable switch

Promotion gate:

- live pilot matches paper assumptions after costs
- no reconciliation breaks remain unresolved
- kill switch and rollback are tested
- strategy remains within drawdown and execution-quality limits

### Level 4: Strategy-Specific Automated Execution

Goal: allow unattended execution only for narrow, validated strategies.

Capabilities:

- whitelist strategy, market class, size range, and order type
- reject anything outside the whitelist
- continuously reconcile orders and positions
- degrade automatically from live broker to proposal-only or paper-only mode when controls fail

Allowed actions:

- automated order placement for approved strategies
- automated cancellation and risk reduction

Not allowed:

- broad autonomous trading across all markets
- strategy self-promotion without validation review
- increasing risk limits without explicit approval

Promotion gate:

- live pilot evidence exceeds the documented threshold
- independent review finds no unresolved execution or reconciliation defect
- risk limits are versioned and auditable

### Level 5: Portfolio Automation Expansion

Goal: expand automation across multiple validated strategies while preserving risk isolation.

Capabilities:

- portfolio-level capital allocation
- strategy-level risk budgets
- cross-strategy correlation controls
- automated de-risking when themes or maturity buckets become crowded

Allowed actions:

- rebalance strategy budgets within approved caps
- pause or shrink underperforming strategies automatically

Promotion gate:

- multiple strategies have independent live evidence
- aggregate risk remains explainable
- drawdown, liquidity, and reconciliation controls continue to hold under stress

## Future Execution Layer

The execution layer should expose one broker interface with multiple implementations:

```text
TradeProposal
  -> RiskGate
  -> Broker
       -> PaperBroker
       -> HumanApprovalBroker
       -> LiveBroker
  -> OrderLifecycleManager
  -> PositionReconciler
  -> AuditJournal
```

The research system should never call the live broker directly. It should emit proposals and let the risk gate and broker mode decide what can happen.

## Required Artifacts Before Live Execution

- strategy validation report
- risk parameter file
- broker interface design
- secret-handling design
- order lifecycle state machine
- reconciliation procedure
- kill-switch procedure
- rollback procedure
- audit log schema
- live pilot checklist

## Rollback Rules

Every level must be able to fall back one level immediately:

- Level 4 falls back to Level 2 proposal-only mode if execution quality degrades.
- Level 3 falls back to Level 1 paper mode if reconciliation fails.
- Level 2 falls back to Level 1 if proposal quality degrades.
- Level 1 falls back to Level 0 if paper fills are not reproducible.

Automatic rollback triggers:

- stale market data
- order API errors above threshold
- unexpected partial-fill behavior
- journal and exchange position mismatch
- drawdown limit breach
- liquidity depth collapse
- strategy calibration drift

## Private-Key And Credential Boundary

Private keys and API credentials must be isolated from data collection, scoring, and research code.

Minimum requirements before implementation:

- no secrets committed to the repository
- no secrets printed to logs
- no secrets available to notebook or research jobs
- dedicated runtime configuration for the execution process
- explicit user approval before any credential storage or signing workflow is added

## Open Engineering Questions

- Which database should store raw market snapshots and journals?
- Which scheduler should run hourly scanning and realtime watchlists?
- Which broker interface shape best matches paper, approval, and live modes?
- What is the smallest useful live pilot capital limit?
- Which strategies are narrow enough for the first Level 3 test?
