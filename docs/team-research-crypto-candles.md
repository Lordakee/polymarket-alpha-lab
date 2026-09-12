# BTC/ETH spot-candle evidence for research agents

## Delivered scope

This node supplies the first independent crypto price-history collector for
this research-agent pipeline. Coinbase Exchange public candles are separate
from Gamma market descriptions/prices. They are **single-venue spot evidence**,
not a settlement oracle, probability model, or a collection of independent
source votes. Forty-eight candles still produce exactly one research source.

The explicitly assigned team determines the permitted product:
`crypto_btc` -> `BTC-USD`; `crypto_eth` -> `ETH-USD`. This does not infer that a
market uses Coinbase or USD for resolution. Matching the actual question,
asset, quoted currency, source and settlement rule remains an application and
operator responsibility. Do not use these candles alone to settle a contract,
infer first-touch events, or claim calibrated forecasting performance.

The new modules are separate from legacy clients and strategy logic:

- `team_research_crypto_candles`: pure window/snapshot contracts, OHLCV
  validation, coverage checks, normalized evidence and content-bound receipts.
- `team_research_coinbase.CoinbaseCandleReader`: opt-in, fixed-origin public GET.
- `team_research_crypto_pipeline.run_crypto_research_from_snapshots`: validated
  candles -> existing Gamma intake -> existing bounded model/tool loop.

No dependency, package-root export, database schema, persistence, strategy-cycle,
BTC publication gate, order, account or wallet change is required. All research
objects retain paper_only/report_only/readonly. The engineering source-snapshot
workflow used for development remains separate and is not part of this node.

## Evidence contract and quality checks

The reader calls only `https://api.exchange.coinbase.com/products/{product}/candles`
with an explicit start, end and granularity. Windows are UTC-normalized,
epoch-aligned half-open intervals `[start, end)`. Supported bucket lengths are
60, 300, 900, 3600, 21600 and 86400 seconds. This application limits a window to
1–48 candles, below the provider's 300-candle response limit, to bound the Agent
context. The parser accepts at most 300 response rows and 128 KiB of raw bytes.

Each row must contain exactly `[time, low, high, open, close, volume]`. Time is
an integer bucket start. Price and volume are parsed as Decimal (not binary
float); strings, booleans, nonfinite constants and unbounded numeric forms are
rejected. Values have at most 24 coefficient digits, exponents from -12 to 18,
and magnitude at most 1e18; prices are positive and volume is nonnegative.
Open/close must lie within low/high. Unknown row shapes fail closed.

All returned rows are structurally checked. Rows outside the requested interval
are counted and excluded, and accepted rows are sorted by bucket start. Duplicate
buckets, even outside the selected window, block the snapshot. Every requested
bucket must be present; missing/no-trade intervals are **not** zero-filled,
forward-filled or silently omitted. A blocked intake has no evidence or receipt.

The provider documents that candle data can be incomplete, that intervals with
no ticks have no published row, and that results may precede the requested start.
Our coverage policy is intentionally stricter than provider success. Receiving
HTTP 200 is not evidence acceptance.

`fetched_at` is recorded after the raw body is read. The entire window must have
ended by retrieval, retrieval must be no later than `as_of`, and retrieval must
be recent (300 seconds by default). Candle freshness is measured from the last
bucket's **end**, not its start or the current fetch time. A recent download of
old candles does not make them fresh. The window-end age limit is shared with
`ResearchAgentLimits.max_evidence_age_seconds`, default 86,400 seconds.

The evidence body includes the selected OHLCV rows, currencies, window, actual
retrieval time, raw-byte SHA256, and a six-decimal first-open-to-last-close return
fraction. It contains no source URL supplied by a provider payload. The source
ID binds request URL, UTC retrieval time and raw digest; the existing receipt
hash binds the complete normalized evidence record, including team/condition.
These hashes detect content differences, not fabricated timestamps, provider
identity in a reconstructed snapshot, or source authenticity.

## Research pipeline and output binding

`run_crypto_research_from_snapshots` performs no automatic public fetch. It
constructs no model when candle intake blocks. On valid candles, the existing
Gamma identity/open-state/binary-outcome/rules/time checks still apply. Invalid
Gamma context also suppresses the model. A successful research result must cite
the single exact receipt accepted from the candle collector; replacing the
source or mixing another market run is rejected by the result contract.

`prepared` means data passed structural, coverage and time checks. `completed`
still means an uncalibrated model research candidate. Neither grants publication,
allocation, execution, source diversity or semantic evidence-quality approval.
The existing Agent's read-before-cite rule and tool/token limits remain active.
Other teams continue to use their existing supplied evidence; this node does
not add sports/political/macro news collectors, DB readback or durable jobs.

## Run the synthetic end-to-end example

After the normal editable installation:

```bash
python scripts/run_crypto_research_demo.py --team crypto_eth
python scripts/run_crypto_research_demo.py --team crypto_btc
```

This uses synthetic market/candle snapshots and `ScriptedDemoModel`, not an LLM.
Output explicitly states `synthetic_demo=true`, `public_network_called=false`,
`live_model_called=false`. Tests execute the demo with network audit guards.

## Explicit public-data probe (no model)

```bash
python scripts/probe_crypto_candles.py
python scripts/probe_crypto_candles.py --allow-public-fetch --team crypto_btc
```

The first command is inert. The second performs one uncredentialed public GET
for three completed hourly candles, leaving an extra hour for publication lag.
It prints timestamps, quality counts and hashes, not raw bodies or model output.
It never calls a language model, opens a database, reads credentials or writes
a data file. Historical candles should not be polled frequently. This probe's
condition identifier is `public-probe-only`, not a real prediction-market claim.

The reader disables redirects, cookie/auth headers, automatic retries,
compressed bodies and environment-proxy discovery. Product names cannot contain
arbitrary paths or URLs. Timeouts are per blocking operation, not an absolute
wall-clock deadline. A network failure remains a fixed redacted error, with no
alternate provider or synthetic data fallback. Raw bytes are retained in memory
before pure normalization. No completed live probe is implied by these docs;
actual execution evidence belongs in the PR.

## Application integration

```python
from datetime import UTC, datetime, timedelta
from polymarket_alpha_lab.team_research_coinbase import CoinbaseCandleReader
from polymarket_alpha_lab.team_research_crypto_candles import CryptoCandleWindow
from polymarket_alpha_lab.team_research_crypto_pipeline import run_crypto_research_from_snapshots

# gamma_snapshot, task_id, expected_condition_id and model_factory are supplied
# by the application. Real model calls require that client's separate opt-in.
end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
window = CryptoCandleWindow("BTC-USD", end - timedelta(hours=24), end)
candles = CoinbaseCandleReader(allow_public_fetch=True).fetch(window)
run = run_crypto_research_from_snapshots(
    gamma_snapshot, candles, task_id=task_id, team_id="crypto_btc",
    condition_id=expected_condition_id, as_of=datetime.now(UTC),
    model_factory=model_factory,
)
```

Applications needing additional sources may use `prepare_crypto_candle_evidence`
and combine the accepted record with separately approved evidence through the
existing generic market pipeline. That is not automatic multi-source validation.
No raw research estimate is promoted to an approved TeamForecastPacket here.

## Verification and authority

The owner authorized self-review and merge without external-review/CodeGraph
gates. No external review or index-sync result is claimed. Focused tests cover
both products, all bucket sizes, Decimal precision, out-of-window filtering,
gaps/duplicates, time boundaries, request restrictions, error cleanup, result
binding, and no-I/O demos. Full sanitized tests and exact Git tree verification
are required before merge; actual totals and any live probe are recorded in the PR.

Primary API contract:
https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles
