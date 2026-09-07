# P3 Source Scouting Report — Second Independent Public Price Family (BTC + ETH spot)

- **Server:** /home/ubuntu/polymarket-alpha-lab (probes run from this host)
- **Date (UTC):** 2026-09-07, 11:36–11:38
- **Method:** plain `curl -s -m 10` GET requests only, no headers/keys/cookies sent, one BTC + one ETH probe per provider, plus freshness re-samples 5–6 s apart for top contenders.
- **Egress context:** all Cloudflare-fronted responses returned `cf-ray: ...-SIN` and Binance was served via CloudFront pop `KUL50` — this server's traffic egresses via the Singapore region. This matters for geo-restricted providers (Binance).
- **Cookie note:** several providers *set* CDN/bot cookies in responses (`__cf_bm` on Coinbase/OKX/Kraken, Imperva `visid_incap`/`incap_ses` on Bitstamp). None of them *require* cookies — every plain keyless curl succeeded. "NO cookies" is interpreted as "no cookies required for access".
- **Baseline (current source, for comparison):** `https://api.kraken.com/0/public/Ticker?pair=XBTUSD` and `?pair=ETHUSD` → HTTP 200, ~0.09–0.11 s, last trade in `result.XXBTZUSD.c[0]` / `result.XETHZUSD.c[0]`, `cache-control: max-age=2`. Operator: Kraken / Payward, Inc.

Cross-source sanity at probe time (BTC, 11:36–11:38 UTC): Coinbase Exchange 79,412.96–79,430.55 · Coinbase retail spot 79,419.025–79,450.405 · Bitstamp 79,420.24–79,449.38 · Kraken 79,447.70 · Gemini 79,442.58 · Bitfinex 79,560 — all within ~0.2 %, i.e. genuine independent quotes, no mirroring.

---

## 1. Coinbase — Coinbase Global, Inc. (NASDAQ: COIN, USA)

Tested two flavors; both fully public.

### 1a. Coinbase Exchange ticker (preferred flavor)
- **endpoint_btc:** `https://api.exchange.coinbase.com/products/BTC-USD/ticker`
- **endpoint_eth:** `https://api.exchange.coinbase.com/products/ETH-USD/ticker`
- **auth_required:** no (no key, no registration; public REST endpoint)
- **http_status_btc:** 200 · **http_status_eth:** 200
- **price_field:** `price` (string) = last trade price in USD. Other fields: `bid`, `ask`, `volume`, `size`, `time` (ISO-8601, nanosecond precision), `trade_id`, `rfq_volume`.
- **observed latency:** 0.107 s (BTC) / 0.291 s (ETH)
- **update cadence:** real-time. `cache-control: public, max-age=1`; two samples 6 s apart returned different `trade_id` (1089810632 → 1089810650), `price` and `time` — true exchange last-trade feed.
- **rate_limit_note:** no explicit rate-limit headers observed on responses; documented public REST limit is 10 req/s per IP — vastly above the ~4 req/min a 30 s poll needs.
- **independence_note:** operated by Coinbase Global, Inc.; entirely separate company from Kraken (Payward, Inc.). One of the deepest BTC-USD/ETH-USD liquidity venues.
- **verdict:** **qualified-candidate (strong)**

### 1b. Coinbase retail "spot" price
- **endpoint_btc:** `https://api.coinbase.com/v2/prices/BTC-USD/spot`
- **endpoint_eth:** `https://api.coinbase.com/v2/prices/ETH-USD/spot`
- **auth_required:** no
- **http_status_btc:** 200 · **http_status_eth:** 200
- **price_field:** `data.amount` (string); `data.base` / `data.currency` = "BTC"/"ETH" and "USD"
- **observed latency:** 0.114 s / 0.080 s
- **update cadence:** ~60 s — `grpc-metadata-cache-control: public, max-age=60`, `cf-cache-status: HIT`; two probes 6 s apart returned an identical amount (79419.025). Too coarse for 30 s polling without repeats.
- **rate_limit_note:** none observed (Cloudflare-fronted).
- **independence_note:** same as 1a.
- **verdict:** **qualified-candidate (backup only — CDN-cached up to ~60 s; prefer 1a)**

---

## 2. Bitstamp — Bitstamp (EU, founded 2011); owned by Robinhood Markets, Inc. since 2025-06-02

- **endpoint_btc:** `https://www.bitstamp.net/api/v2/ticker/btcusd/`
- **endpoint_eth:** `https://www.bitstamp.net/api/v2/ticker/ethusd/`
- **auth_required:** no (Imperva CDN sets `visid_incap_*` / `incap_ses_*` cookies in responses, but plain cookieless curl works)
- **http_status_btc:** 200 · **http_status_eth:** 200
- **price_field:** `last` (string) = last trade price in USD. Other fields: `bid`, `ask`, `vwap`, `volume`, `high`, `low`, `open`, `open_24`, `percent_change_24`, `timestamp` (unix s), `side`, `market_type: "SPOT"`.
- **observed latency:** 0.074 s (BTC) / 0.276 s (ETH)
- **update cadence:** real-time. `cache-control: max-age=1, public`; `last-modified` within 1 s of response; two samples 5–6 s apart: `last` 79424.33 → 79420.24 with `timestamp` 1788781097 → 1788781102.
- **rate_limit_note:** no explicit headers; documented allowance 8000 requests / 10 min per IP — ample for 30 s polling.
- **independence_note:** Bitstamp is one of the oldest continuously operating crypto exchanges; acquired by Robinhood Markets (announced June 2024, completed June 2025). Fully independent from Kraken — separate order book, separate company/group.
- **verdict:** **qualified-candidate (strong)**

---

## 3. CryptoCompare — CryptoCompare (owned by CoinDesk / Bullish group)

- **endpoint_btc:** `https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD`
- **endpoint_eth:** `https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD`
- **auth_required:** **YES** — both requests returned HTTP 401 with body:
  `{"Data":{},"Err":{"message":"API key required, please refer to the documentation at https://developers.coindesk.com/","http_status_code":401,...}}`
- **http_status_btc:** 401 · **http_status_eth:** 401
- **price_field:** n/a (no price returned). Historically `USD`.
- **observed latency:** 0.106 s / 0.102 s (for the 401)
- **rate_limit_note:** n/a.
- **independence_note:** CryptoCompare was acquired by CoinDesk; it is also an *aggregator* (volume-weighted composite across many exchanges), not a single-venue feed.
- **verdict:** **auth-required — disqualified** (keyless access to /data/price has been removed; no signup attempted per constraints)

---

## 4. CoinGecko — CoinGecko (Holdings) Pte Ltd / Sdn Bhd (Singapore/Malaysia, founded 2014)

- **endpoint_btc:** `https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd`
- **endpoint_eth:** `https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd`
- (single combined request also verified: `?ids=bitcoin,ethereum&vs_currencies=usd` → `{"bitcoin":{"usd":79445},"ethereum":{"usd":2491.11}}`, HTTP 200, 0.089 s — one call per poll covers both assets)
- **auth_required:** no (works keyless on the free public tier)
- **http_status_btc:** 200 · **http_status_eth:** 200
- **price_field:** `<id>.usd` (number) — e.g. `bitcoin.usd`, `ethereum.usd`
- **observed latency:** 0.104 s / 0.081 s
- **update cadence:** `cache-control: max-age=30, public, must-revalidate, s-maxage=60`, observed `age: 18–19`, `cf-cache-status: HIT` → data can lag 30–60 s; with 30 s polling, consecutive samples will sometimes repeat. Aggregated/index price, not a single-venue last trade.
- **rate_limit_note:** no explicit headers observed; free public tier is documented around ~30 calls/min (Cloudflare-throttled). 1–2 calls per 30 s is well within it.
- **independence_note:** company-wise independent from Kraken, **but** the price is a volume-weighted aggregate across many exchanges — Kraken is plausibly one of the constituents, so as a *measurement* it is not fully independent of the primary source.
- **verdict:** **qualified-candidate (with caveats: aggregated price may include Kraken; 30–60 s cache → repeats at 30 s cadence)**

---

## 5. Binance — Binance Holdings Ltd. group

- **endpoint_btc:** `https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT`
- **endpoint_eth:** `https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT`
- **auth_required:** no
- **http_status_btc:** 200 · **http_status_eth:** 200 (no geo-block from this server — egress is Singapore; via CloudFront pop KUL50. US egress IPs get HTTP 451 from this API.)
- **price_field:** `price` (string); `symbol` echoes the pair
- **observed latency:** 0.151 s / 0.129 s
- **rate_limit_note:** explicit weight headers observed: `x-mbx-used-weight: 2`, `x-mbx-used-weight-1m: 2` (price ticker weight 2 against a 6000/min IP budget) — excellent headroom.
- **update cadence:** `cache-control: no-cache, no-store` — real-time last trade (but vs USDT).
- **independence_note:** Binance group, fully independent from Kraken.
- **caveats:** (1) quote currency is **USDT, not fiat USD** — Binance spot has no fiat-USD book, so this fails the strict "BTC/USD, ETH/USD" requirement (USDT typically within ~0.05 % of USD, but that is a stablecoin-basis risk for a research oracle). (2) Geo fragility: works only because this server egresses via SG; a US egress path returns 451.
- **verdict:** **unsuitable for the strict USD requirement (USDT-quoted; geo-restriction risk)** — only viable if USDT≈USD is explicitly accepted

---

## 6. OKX — OKX / Aux Cayes Fintech Co. Ltd (OK Group)

- **endpoint_btc:** `https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT`
- **endpoint_eth:** `https://www.okx.com/api/v5/market/ticker?instId=ETH-USDT`
- **auth_required:** no
- **http_status_btc:** 200 · **http_status_eth:** 200
- **price_field:** `data[0].last` (string). Other fields: `askPx`, `askSz`, `bidPx`, `bidSz`, `lastSz`, `open24h`, `high24h`, `low24h`, `vol24h`, `volCcy24h`, `ts` (ms), `instType: "SPOT"`.
- **observed latency:** 0.177 s / 0.150 s (routed `x-routed-to: TKY`)
- **update cadence:** `cache-control: no-cache, no-store` — real-time (`ts` at response second).
- **rate_limit_note:** no headers; documented public market-data limit ~20 req / 2 s per IP — ample.
- **independence_note:** OKX group, independent from Kraken.
- **caveats:** the *spot* book is **BTC-USDT / ETH-USDT**; the USD-quoted instruments (BTC-USD, ETH-USD) on OKX are perpetual swaps (derivatives), not spot. So OKX cannot supply a true fiat-USD spot last.
- **verdict:** **unsuitable for the strict USD requirement (USDT-quoted spot)**

---

## 7. Bitfinex — iFinex Inc. (BVI); also parent company of Tether

- **endpoint_btc:** `https://api-pub.bitfinex.com/v2/ticker/tBTCUSD`
- **endpoint_eth:** `https://api-pub.bitfinex.com/v2/ticker/tETHUSD`
- **auth_required:** no
- **http_status_btc:** 200 · **http_status_eth:** 200
- **price_field:** response is a **positional JSON array**: `[BID, BID_SIZE, ASK, ASK_SIZE, DAILY_CHANGE, DAILY_CHANGE_RELATIVE, LAST_PRICE, VOLUME, HIGH, LOW, TIMESTAMP]` — last price = **index 6** (BTC sample: 79560; ETH sample: 2495.1); trade timestamp = index 11. No named fields (field names above are from the documented order).
- **observed latency:** 0.090 s / 0.107 s (recheck 0.118 s)
- **update cadence:** real-time; `last-modified`/`age` show only ~6 s of CDN cache (`cf-cache-status: HIT`).
- **rate_limit_note:** no headers observed; documented public REST allowance in the tens of requests/min per endpoint — fine for 30 s polling.
- **independence_note:** Bitfinex (iFinex Inc.) — independent exchange group from Kraken; note the Tether affiliation is a corporate (not price-mirroring) consideration.
- **verdict:** **qualified-candidate (USD-quoted, keyless; minor ergonomic cost: positional array response)**

---

## 8. Gemini — Gemini Trust Company, LLC (USA; founded 2014, Winklevoss)

- **endpoint_btc:** `https://api.gemini.com/v1/pubticker/BTCUSD`
- **endpoint_eth:** `https://api.gemini.com/v1/pubticker/ETHUSD`
- (also verified the newer `https://api.gemini.com/v2/ticker/btcusd|ethusd` → 200; v2 exposes `open/high/low/close/bid/ask` where `close` is the 24-h histogram close — `v1.pubticker.last` is the cleaner "last trade")
- **auth_required:** no
- **http_status_btc:** 200 · **http_status_eth:** 200
- **price_field:** `last` (string). Other fields: `bid`, `ask`, `volume.{BTC|ETH, USD, timestamp}`.
- **observed latency:** 1.05–1.09 s consistently (slowest of the batch; direct US origins, no CDN caching) — still negligible against a 30 s poll.
- **update cadence:** `last` is real-time last trade; `volume.timestamp` ticks on a ~60 s boundary (observed 16–19 s behind response time).
- **rate_limit_note:** no headers; documented public API allowance ~120 req/min per IP.
- **independence_note:** Gemini Trust Company LLC, NY-regulated US exchange — fully independent from Kraken.
- **verdict:** **qualified-candidate (USD-quoted, keyless; ~1 s latency, smaller liquidity venue)**

---

## Summary matrix

| # | Provider | BTC/ETH endpoints | Auth | Status | Price field | Latency | True USD? | Verdict |
|---|----------|-------------------|------|--------|-------------|---------|-----------|---------|
| 1 | Coinbase Exchange | /products/{BTC-USD,ETH-USD}/ticker | none | 200/200 | `price` | 0.11–0.29 s | yes | **qualified-candidate (strong)** |
| 1b | Coinbase retail spot | /v2/prices/{BTC,ETH}-USD/spot | none | 200/200 | `data.amount` | 0.08–0.11 s | yes (cached ~60 s) | qualified-candidate (backup) |
| 2 | Bitstamp | /api/v2/ticker/{btcusd,ethusd}/ | none | 200/200 | `last` | 0.07–0.28 s | yes (SPOT) | **qualified-candidate (strong)** |
| 3 | CryptoCompare | /data/price?fsym=…&tsyms=USD | API KEY | 401/401 | n/a | n/a | n/a | auth-required → disqualified |
| 4 | CoinGecko | /simple/price?ids=…&vs_currencies=usd | none | 200/200 | `<id>.usd` | ~0.09–0.10 s | aggregated USD | qualified-candidate (caveats) |
| 5 | Binance | /api/v3/ticker/price?symbol={BTC,ETH}USDT | none | 200/200 | `price` | 0.13–0.15 s | **no (USDT)** | unsuitable (USDT quote + geo risk) |
| 6 | OKX | /api/v5/market/ticker?instId={BTC,ETH}-USDT | none | 200/200 | `data[0].last` | 0.15–0.18 s | **no (USDT)** | unsuitable (USDT spot) |
| 7 | Bitfinex | /v2/ticker/t{BTC,ETH}USD | none | 200/200 | array index 6 (`LAST_PRICE`) | 0.09–0.12 s | yes | qualified-candidate |
| 8 | Gemini | /v1/pubticker/{BTC,ETH}USD | none | 200/200 | `last` | ~1.05 s | yes | qualified-candidate |

---

## Ranked recommendation — top 2

### #1 — Coinbase Exchange public ticker (`api.exchange.coinbase.com`)
`https://api.exchange.coinbase.com/products/BTC-USD/ticker` and `.../ETH-USD/ticker`, read `price`.
Why: keyless GET, genuine fiat-USD **last-trade** price (with `bid`/`ask`/`time`/`trade_id` for validation) from one of the deepest USD liquidity venues; observed real-time freshness (trade_id advanced within 6 s, `max-age=1`); 0.1–0.3 s latency; documented 10 req/s public limit versus the ~4 req/min needed; operator Coinbase Global, Inc. — completely independent from Kraken, so any Kraken outage/mispricing will not propagate. The retail `/v2/prices/.../spot` endpoint works keyless as an emergency fallback (but is CDN-cached up to ~60 s).

### #2 — Bitstamp v2 ticker (`www.bitstamp.net/api/v2/ticker`)
`https://www.bitstamp.net/api/v2/ticker/btcusd/` and `.../ethusd/`, read `last`.
Why: keyless GET (Imperva cookies are set but not required), explicit `market_type: "SPOT"` fiat-USD last trade with rich context fields (`vwap`, `volume`, `timestamp`); observed real-time freshness (`max-age=1`, value moved between samples 5 s apart); fastest first-byte of the batch (0.07 s); documented 8000 req/10 min limit — effectively unlimited for 30 s polling; operated by Bitstamp (Robinhood-owned since June 2025), a separate exchange and order book from both Kraken and Coinbase. Using Coinbase + Bitstamp gives two mutually independent deep USD venues, and cross-checks against the existing Kraken family form a natural 3-way sanity oracle.

**Runner-ups / notes:**
- Gemini (`v1/pubticker`, field `last`) is a solid USD-quoted third option — keyless and clean, just ~1 s latency and thinner liquidity.
- Bitfinex is USD-quoted and fast, but the positional-array response is more fragile to parse; keep as a fourth fallback.
- CoinGecko works keyless (single combined call for both assets) but is an aggregate that may include Kraken as a constituent and caches 30–60 s — usable as a tertiary sanity source, not as the independent P3 family.
- Binance and OKX were reachable and fast from this server but quote **USDT**, not USD (and Binance is geo-fragile: 451 on US egress). Rejected for the strict USD requirement.
- CryptoCompare is no longer keyless (HTTP 401, "API key required") — disqualified under the no-key constraint.

*All probes were read-only public GETs; nothing was installed, no accounts created, no keys used, no POSTs sent.*
