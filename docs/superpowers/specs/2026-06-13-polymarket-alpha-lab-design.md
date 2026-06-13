# Polymarket Alpha Lab Design

## Purpose

Build a research-first workspace for identifying and validating Polymarket markets with measurable edge. The project starts as a data, scoring, paper-trading, and risk-analysis system. It does not start as a trading bot.

## Non-Goals

- No live trading.
- No account authentication.
- No wallet or private-key handling.
- No automated order placement.
- No compliance, geographic, regulatory, or legal analysis.

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

The project is split into five eventual modules:

1. Data ingestion: fetch raw Gamma, CLOB, Data API, and WebSocket data.
2. Normalization: convert raw payloads into event, market, and outcome-token models.
3. Scoring and edge scanning: rank markets and detect measurable anomalies.
4. Paper trading and journals: simulate bid/ask fills and record decision context.
5. Risk engine: enforce position, theme, maturity, liquidity, and drawdown constraints.

The current repository only implements the documentation and a thin domain model skeleton. Implementation modules will be planned separately.

## Data Flow

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

## Open Questions

The first implementation plan must choose one of these starting modes:

1. Data-only scanner: build ingestion and ranking first.
2. Research workstation: build scanner plus paper-trading journal.
3. Strategy lab: build scanner, journal, risk model, and initial edge scanners.

Given the current goal, the recommended first implementation is the data-only scanner plus enough domain modeling to support future journal and risk work.

