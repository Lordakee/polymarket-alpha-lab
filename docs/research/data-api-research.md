# Data And API Research

## Conclusion

Polymarket has enough public data to support a market-screening and paper-trading MVP. The recommended source priority is:

1. Gamma API for market discovery, events, tags, search, series, and rich metadata.
2. CLOB API for order books, prices, spreads, midpoints, last trade price, and price history.
3. Data API for public trades, activity, positions, holders, open interest, and leaderboards.
4. WebSocket market channel for real-time updates on a smaller watchlist.
5. Officially documented third-party chain data for historical backfill and verification.

Website browsing should stay a secondary verification tool, not a core data pipeline.

## Available Data Surfaces

Gamma API covers:

- events
- markets
- tags
- series
- search
- comments
- sports metadata
- public profiles

CLOB API covers:

- order book
- batch order books
- prices
- midpoint prices
- spreads
- last trade prices
- historical prices
- market-level CLOB configuration

Data API covers:

- trades
- activity
- positions
- holders
- open interest
- trader rankings

WebSocket market channel covers:

- `book`
- `price_change`
- `last_trade_price`
- `best_bid_ask`
- `new_market`
- `market_resolved`
- `tick_size_change`

## Important Fields

Hard filters:

- `active`
- `closed`
- `acceptingOrders`
- `enableOrderBook`
- `clobTokenIds`
- `orderMinSize`
- `orderPriceMinTickSize`
- `endDate`

Activity:

- `volume24hr`
- recent trade count
- recent notional volume
- `volume1wk`
- `volumeNum`
- `openInterest`

Liquidity and book quality:

- `bestBid`
- `bestAsk`
- `spread`
- bid and ask levels
- top-of-book depth
- depth within 1 percent and 5 percent
- book timestamp
- book hash

Price behavior:

- `outcomePrices`
- `lastTradePrice`
- midpoint
- price history
- 1 hour, 24 hour, and 7 day price changes
- realized volatility
- jump score

Resolution and text:

- `question`
- `description`
- `rules`
- `resolutionSource`
- `endDate`
- `eventSlug`
- `tags`
- `series`
- `groupItemTitle`
- `groupItemThreshold`

Deduplication and clustering:

- `conditionId`
- `clobTokenIds`
- `eventSlug`
- event id
- market slug
- normalized question
- end date
- outcomes
- thresholds

## Technical Difficulties

Rate limits are generous enough for a staged MVP but require scheduling. The documented limits include separate caps for Gamma, Data API, CLOB book, CLOB books, and price-history endpoints.

Historical order book depth is the biggest data gap. Official price history exists, but historical L2 book depth must be collected from the moment this project starts unless a third-party dataset is later added.

Market naming is messy. The project should treat events as containers and outcome tokens as the tradable unit. Use `conditionId + outcome_index` or token id as the core tradable key.

Field types are inconsistent in live samples. Some fields are numeric, some are string numeric, and some important arrays like outcomes, prices, and CLOB token ids can arrive as stringified JSON.

Order books are noisy. A tiny top-level order can distort best bid or best ask. Screening should calculate effective spread after ignoring dust-sized levels and should use multi-level depth.

End time is not resolution time. The system must track closed, resolved, winning outcome, and resolution-status fields separately.

## MVP Data Pipeline

Daily:

- fetch Gamma events, markets, tags, series, and search metadata
- update market lifecycle state
- preserve raw API JSON
- normalize event, market, and outcome-token dimensions
- compute text and resolution-rule features

Hourly:

- refresh active markets
- refresh active pool order books
- refresh short-window price history
- ingest recent trades
- compute market quality scores

Realtime:

- subscribe only to watchlist and high-activity token ids
- process order book, price change, last trade, best bid/ask, new market, market resolved, and tick-size changes
- resync REST order book after WebSocket reconnects

## Initial Scoring Weights

- activity: 25 percent
- book quality: 30 percent
- time structure: 10 percent
- information structure: 15 percent
- price behavior: 15 percent
- duplicate or clustering penalty: 5 percent

This is a research ranking score, not a trading instruction.

