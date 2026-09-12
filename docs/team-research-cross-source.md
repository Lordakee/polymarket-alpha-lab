# Coinbase / Kraken cross-source research

## Delivered scope

Two separately operated public spot venues now feed a single checked research
path for `crypto_btc` (BTC/USD) and `crypto_eth` (ETH/USD). This is **data
consistency**, not two statistically independent probability estimates. Both
venues reflect the same underlying market and can share errors or biases.
No average price, confidence boost, consensus probability, calibration claim,
settlement verdict, publication approval or execution instruction is produced.

```text
explicit Coinbase GET + explicit Kraken GET
                  -> same-window / freshness / coverage checks
                  -> per-bucket closing-price comparison
                  -> existing Gamma market/rules intake
                  -> model reads and cites BOTH exact source records
```

The existing single-source API and BTC publication/strategy-cycle paths are
unchanged. The only existing production edit adds an optional, validated
`required_source_ids=()` argument to `run_team_research_agent`. Default calls
and the existing batch API still behave as before. Required sources are
included in model context, and finishing without all required citations blocks
with `invalid_citations`; the existing actual-read requirement still applies.

## Source contract

`team_research_kraken.KrakenCandleReader` is inert unless explicitly enabled.
It makes one unauthenticated HTTPS GET to the fixed Kraken OHLC endpoint, using
only BTC/USD or ETH/USD. Internal result keys are checked exactly; another
pair, a stablecoin quote or an extra result series is not guessed into place.
There are no redirects, cookies, environment proxy discovery, retries, arbitrary
URL tools, credential reads, database writes or caches. Response reads are
bounded at 256 KiB; timestamps are taken after reading the body. Network
timeouts bound blocking operations, not a universal wall-clock deadline.

The window type is reused from Coinbase. The supported intersection is
60, 300, 900, 3600 and 86400 seconds, with 1–48 requested buckets. Coinbase's
six-hour interval is NOT silently mapped to Kraken's four-hour interval.
Requests use Kraken's minute units and one preceding bucket in `since` to
avoid relying on inclusive/exclusive cursor interpretation. The end boundary
is enforced locally. No provider pagination or unlimited historical backfill
is promised: Kraken documents a maximum of 720 recent entries.

Kraken's eight-column rows are strictly decoded as time, open, high, low,
close, VWAP, volume and trade count. Its decimal strings use the same bounded
Decimal values as the existing Coinbase parser, but a different wire schema.
Duplicates, out-of-order timestamps, bad OHLC, malformed/error envelopes and
unexpected pair keys block. Selected zero-trade buckets block rather than
being treated as new price observations. No gaps are filled.

**The final Kraken row is always discarded as uncommitted**, even if its
reported start would appear closed relative to local retrieval time. All
remaining buckets outside `[start,end)` are excluded. Every requested bucket
must remain present. An incomplete historical response stays blocked rather
than being substituted with the most recent data. Discarded-row counts include
the uncommitted final row; they do not imply every discarded row is malformed.

## Cross-source gate

`check_crypto_cross_source` accepts exact Coinbase/Kraken snapshots, not a
caller-proclaimed successful provider report. It independently normalizes the
raw snapshots. Product, interval, start and end must match exactly. Both
captures must be recent, no later than `as_of`, and after the requested window
has closed. Capture skew is at most 60 seconds by default. Observation freshness
uses the common final bucket end, not download time. Existing snapshot/evidence
age limits are shared with the Agent pipeline.

For EVERY aligned bucket, the reported symmetric close-price discrepancy is:

`basis points = 20000 * abs(Coinbase close - Kraken close) / (Coinbase close + Kraken close)`

`CrossSourcePolicy.max_close_divergence_bps` defaults to Decimal `100` (1% of
the two-price midpoint). This is an explicit engineering tolerance, not an
empirically calibrated rule. Any bucket above the threshold blocks, even when
the latest closes agree. Calculations use a fixed Decimal context; diagnostics
round outward to six decimal places so tiny breaches are not displayed as an
acceptable equality. Configured thresholds have at most six decimal places.
OHLC validity is checked per venue; **only closes** are cross-compared. Volume,
venue liquidity, intrabucket paths, oracle basis and market semantics are not
compared. Do not use this gate as proof of a first-touch or settlement outcome.

A `matched` result contains two distinct, content-bound source receipts and
evidence records. A `blocked` result contains no usable evidence or receipts;
raw snapshot digests, capture times, fixed reason codes and any computed
comparison values remain diagnostic metadata. No raw provider error text is
returned. Hashes bind content, not source authenticity or genuine historical
capture times in caller-reconstructed snapshots.

## Application entry point and demos

Import `run_cross_source_crypto_research` from
`polymarket_alpha_lab.team_research_cross_source_pipeline`. Pass a Gamma
snapshot, the two venue snapshots, task/team/condition IDs, `as_of`, and an
explicit application-owned model factory. Market and source validation happen
before the factory is called. A matched source check can still be rejected by
Gamma intake. A completed result must cite both sources that the Agent actually
read. A model that ignores the second source blocks; it is not retried, fixed
up or silently replaced with a default probability. Model providers and model
credentials retain their separate opt-in; the pipeline performs no public GETs.

After normal project installation:

```bash
python scripts/run_cross_source_research_demo.py --team crypto_eth
python scripts/probe_crypto_cross_source.py
python scripts/probe_crypto_cross_source.py --allow-public-fetch --team crypto_btc
```

The demo uses synthetic venue/market snapshots and a scripted model, not an
LLM. The default probe is inert. The enabled probe performs at most one public
GET per venue for three closed hourly buckets, prints counts/times/hashes and
discrepancy diagnostics, and calls no model or database. Failure remains a
failure, with no source substitution or synthetic fallback. Do not run historical
candle probes as high-frequency real-time polling.

## Verification and remaining boundaries

Tests cover provider schema, uncommitted rows, gaps, time/asset/interval mismatch,
all five shared intervals, exact threshold boundaries and tiny breaches, earlier
bucket divergence, two-source read/citation requirements, content binding,
provider-error cleanup and no-network demos. Run the three new test modules
and `scripts/verify_local.py --full`; actual counts, final Git trees and public
probe results are recorded in the PR rather than implied by this document.

This session uses owner-authorized self-review and merge, without external
review/CodeGraph requirements. All results remain paper-only/report-only/readonly.
No new persistence is added; approved durable data remains local Supabase/Postgres.
Public-source interoperability is separate from live-model quality and real-DB
acceptance. This node does not implement calibration, all-domain collectors,
open-web agents, inter-agent debate, durable jobs or automatic forecast promotion.

Primary provider contracts:
- https://docs.kraken.com/api-reference/market-data/get-ohlc-data
- https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles
