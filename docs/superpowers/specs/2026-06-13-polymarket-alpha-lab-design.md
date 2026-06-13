# Polymarket Alpha Lab Design

## Purpose

Build a research-first workspace for identifying and validating Polymarket markets with measurable edge. The project starts as a data, scoring, paper-trading, and risk-analysis system. It does not start as a trading bot, but it is intended to support staged, validated automation later.

## Phase 1 Scope Boundaries

- No live trading in Phase 1.
- No account authentication in Phase 1.
- No wallet or private-key handling in Phase 1.
- No automated order placement in Phase 1.
- No compliance, geographic, regulatory, or legal analysis.

These boundaries keep the first build testable and read-only. They are not permanent non-goals. The long-term execution path is defined in `2026-06-13-automated-investment-roadmap.md`.

## Long-Term Vision

The intended end state is a system that can:

1. Automatically discover and rank Polymarket markets.
2. Build research packets for candidate opportunities.
3. Paper trade every strategy against executable bid/ask prices.
4. Generate trade proposals with risk-adjusted sizing and clear rejection reasons.
5. Move selected, validated strategies through human approval and limited live pilots.
6. Eventually run constrained automated execution for whitelisted strategies that pass validation gates.

The project must never treat a score or model output as a direct buy or sell instruction. Execution requires a separate risk gate, broker mode, audit record, and rollback path.

## Recommended First Product

The recommended first product is a market quality and edge scanner:

1. Ingest official market metadata, order book, trade, and price-history data.
2. Normalize markets into events, markets, and outcome tokens.
3. Score each token by activity, liquidity, spread quality, time structure, information structure, price behavior, and duplicate risk.
4. Detect measurable candidate edges:
   - multi-outcome price-sum anomalies
   - related-market logical constraint violations
   - spread/depth opportunities
   - liquidity reward efficiency
   - post-fill adverse drift
5. Send every candidate to paper trading before any execution automation.
6. Evaluate strategies by cost-adjusted edge, drawdown, calibration, and return per capital day.

## Architecture

The project is split into six eventual modules:

1. Data ingestion: fetch raw Gamma, CLOB, Data API, and WebSocket data.
2. Normalization: convert raw payloads into event, market, and outcome-token models.
3. Scoring and edge scanning: rank markets and detect measurable anomalies.
4. Paper trading and journals: simulate bid/ask fills and record decision context.
5. Risk engine: enforce position, theme, maturity, liquidity, and drawdown constraints.
6. Execution gateway: route approved decisions through paper, human-approval, or live broker modes.

The execution gateway is a future module, not a Phase 1 implementation. Its expected submodules are:

- paper broker for deterministic simulation
- human approval broker for proposal review and manual confirmation
- live broker for authenticated order submission
- order lifecycle manager for placement, cancellation, fills, and error states
- key/signing boundary isolated from research code
- position reconciliation against exchange and local journal state

The current repository only implements the documentation and a thin domain model skeleton. Implementation modules will be planned separately.

## Data Flow

Phase 1 research flow:

```text
official APIs
  -> raw JSON archive
  -> normalized dimensions
  -> order book and trade facts
  -> hourly market scores
  -> edge candidates
  -> risk checks
  -> paper trades
  -> analytics and review
```

Future execution flow:

```text
edge candidate
  -> research packet
  -> risk gate
  -> broker mode selection
  -> paper broker | human approval broker | live broker
  -> order lifecycle tracking
  -> position reconciliation
  -> post-trade review
```

## Data Sources

Primary:

- Gamma API for markets, events, tags, series, and search.
- CLOB API for books, prices, spreads, midpoints, and price history.
- Data API for trades, activity, holders, open interest, and public aggregates.
- WebSocket market channel for watchlist realtime updates.

Secondary:

- Officially documented Dune, Goldsky, Allium, and CryptoHouse data for historical backfill and verification.
- Website browsing only for manual comparison or fields missing from official APIs.

## Key Design Decisions

Use outcome token as the tradable unit. Events are containers and markets are condition-level structures, but order books and price history are tied to CLOB token ids.

Preserve raw payloads before normalization. API fields can be inconsistent, nullable, string numeric, or stringified JSON.

Use executable prices in research. Displayed probability and midpoint are not enough for strategy validation.

Treat historical L2 depth as unavailable until collected. Price history can backfill price studies, but the system must collect order book snapshots going forward.

Keep strategy signals separate from execution decisions. A signal can say there is a possible anomaly; execution still needs risk, liquidity, and journal checks.

Keep execution interchangeable. Strategy code should emit proposals; broker modules should decide whether the proposal is simulated, queued for approval, or eligible for live execution.

## Initial Scoring Model

```text
total_score =
  25% activity
+ 30% book quality
+ 10% time structure
+ 15% information structure
+ 15% price behavior
-  5% duplicate penalty
```

This score is a research priority score, not a buy or sell instruction.

## Validation Rules

Paper trading must use bid/ask and order book walk simulation, not midpoint.

Each paper trade must include:

- thesis
- invalidating conditions
- rule text or rule hash
- model probability if used
- executable entry price
- estimated spread and slippage
- sizing limiter
- exit rule
- post-trade review

Promotion beyond paper trading requires documented validation gates. The default gates are maintained in `docs/research/validation-gates.md`.

## Open Questions

The first implementation plan must choose one of these starting modes:

1. Data-only scanner: build ingestion and ranking first.
2. Research workstation: build scanner plus paper-trading journal.
3. Strategy lab: build scanner, journal, risk model, and initial edge scanners.

Given the current goal, the recommended first implementation is the data-only scanner plus enough domain modeling to support future journal and risk work.
