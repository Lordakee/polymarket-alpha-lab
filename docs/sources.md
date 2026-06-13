# Sources

These are the primary sources used for the initial research pass.

## Official Polymarket Documentation

- API introduction: https://docs.polymarket.com/api-reference/introduction
- Market data overview: https://docs.polymarket.com/market-data/overview
- Markets list API: https://docs.polymarket.com/api-reference/markets/list-markets
- Events list API: https://docs.polymarket.com/api-reference/events/list-events
- Tags list API: https://docs.polymarket.com/api-reference/tags/list-tags
- Order book API: https://docs.polymarket.com/api-reference/market-data/get-order-book
- Prices history API: https://docs.polymarket.com/api-reference/markets/get-prices-history
- Rate limits: https://docs.polymarket.com/api-reference/rate-limits
- WebSocket market channel: https://docs.polymarket.com/market-data/websocket/market-channel
- Prices and order book concepts: https://docs.polymarket.com/concepts/prices-orderbook
- Resolution concepts: https://docs.polymarket.com/concepts/resolution
- Trading overview: https://docs.polymarket.com/trading/overview
- Authentication: https://docs.polymarket.com/api-reference/authentication
- Create order: https://docs.polymarket.com/trading/orders/create
- Order lifecycle: https://docs.polymarket.com/concepts/order-lifecycle
- User WebSocket channel: https://docs.polymarket.com/market-data/websocket/user-channel
- Heartbeat endpoint: https://docs.polymarket.com/api-reference/trade/send-heartbeat
- Matching engine restarts: https://docs.polymarket.com/trading/matching-engine
- Fees: https://docs.polymarket.com/trading/fees
- Liquidity rewards: https://docs.polymarket.com/market-makers/liquidity-rewards
- Blockchain data resources: https://docs.polymarket.com/resources/blockchain-data

## Live Sampling Performed

- `https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=5`
- `https://gamma-api.polymarket.com/events?active=true&closed=false&limit=5&order=volume24hr&ascending=false`
- `https://clob.polymarket.com/markets?limit=2`
- Polymarket homepage and event page via Chrome DevTools:
  - https://polymarket.com/
  - https://polymarket.com/event/world-cup-winner

## Secondary Research

- Multi-outcome prediction-market arbitrage reference: https://arxiv.org/html/2508.03474v1
- Kelly criterion reference: https://en.wikipedia.org/wiki/Kelly_criterion
- Position sizing overview: https://www.investopedia.com/articles/trading/09/determine-position-size.asp
