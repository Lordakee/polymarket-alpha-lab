# Strategy Cycle v0 Design

## Purpose

Strategy Cycle v0 closes the longest-standing deadlock in the project: the
`cost_aware_event_strategy` and `project_screening` modules are pure,
test-enforced, caller-supplied-input evaluators, and **nothing in the codebase
produces the inputs they consume** (`fair_probability_yes`, `confidence`, and
the YES/NO bid/ask/size bundle). As a result the entire Level 1/2 chain has
never run against live data — there is no `data/`, `runs/`, or `artifacts/`
directory, the CLI exposes only `scan`, and `model_probability` /
`fair_value_estimate` are assigned only inside unit tests.

Strategy Cycle v0 wires the existing library into an end-to-end, paper-only,
hourly-runnable pipeline that turns a Polymarket market scan into a
deterministic `PaperProjectScreeningReport` research queue — without crossing
the AGENTS.md Phase 1 boundary (no live trading, no auth, no wallets, no order
placement, no credentials).

It does not fetch beyond what `scan` already fetches, does not authenticate,
does not handle wallets / private keys / signatures / relayers, does not place
or route orders, does not produce capital instructions or investment
recommendations, does not rank investments, and does not perform
compliance / legal / geographic analysis.

## Background — the deadlock

`build_paper_cost_aware_event_strategy_report` (cost_aware_event_strategy.py:262)
requires a caller-built `PaperCostAwareEventMarketSnapshot` whose fields are:

- `fair_probability_yes: Decimal` — a **forecast-model output** (no module computes this)
- `confidence: Decimal` — a **forecast-model output** (no module computes this)
- `yes_bid/yes_ask/yes_ask_size/no_bid/no_ask/no_ask_size` — order-book-derived
  (no extractor exists)
- `spread: Decimal` — derivable from the book
- `resolution_risk: Decimal` — derivable from market metadata (no producer exists)
- `market_slug`, `question` — from `NormalizedMarket.market`

The scope test `test_cost_aware_event_strategy_does_not_import_live_or_loader_surfaces`
forbids the cost-aware module from fetching any of these itself. The correct
architecture — already established by `project_screening.py`, which is one
layer up and consumes cost-aware reports — is **unidirectional layering**: new
modules prepare the inputs and hand them to cost-aware; cost-aware never
reaches up.

Strategy Cycle v0 adds the missing preparation + orchestration layers in that
same direction.

## Stage split (per claude-opus-4-8 pre-stage review 2026-06-16)

The pre-stage review (Block verdict) found that the orchestrator (Module 3)
rests on a contract that does not exist: `ScoredCandidate` is flat
(`condition_id, token_id, market_slug, question, total_score, raw_archive_path`)
with no `.market` / `.tokens` / `NormalizedMarket`, and `run_market_scan`
discards the `NormalizedMarket` it builds internally, emitting one flat row per
token. The orchestrator therefore cannot source the `NormalizedMarket` + YES/NO
token books + `rules_text`/`resolution_source`/`end_time` that the snapshot
builder requires, without either extending `pipeline.py` or running its own
scan via `normalize_gamma_market`.

The two paper-only leaf modules have **zero dependency** on that broken
contract — they take caller-supplied `NormalizedMarket` + `OrderBookSnapshot`
inputs and are independently testable. So this design is split:

- **Stage 1a (in scope for this gate, immediately implementable):** Module 1
  `forecast_provider` + Module 2 `cost_aware_snapshot_builder`. Both paper-only,
  report-only, fully specified below with the review fixes (I3/M1/M2/I1)
  applied.
- **Stage 1b (DEFERRED — separate pre-stage gate required):** Module 3
  `strategy_cycle` + CLI. Requires first resolving the `NormalizedMarket`
  plumbing decision (extend `pipeline.run_market_scan` to retain the
  `NormalizedMarket`, OR have `strategy_cycle` run its own scan via
  `normalize_gamma_market`). The Module 3 / CLI sections below are retained for
  context but are NOT in scope for Stage 1a.

## Architecture

Three new modules, in two layers, plus a CLI subcommand.

```text
LIVE ORCHESTRATION LAYER  (may import api / normalize / pipeline / domain)
  ┌──────────────────────────────────────────────────────────────────┐
  │ strategy_cycle.py                                                │
  │   run_strategy_cycle(client, scan_config, cycle_config, *)       │
  │     1. pipeline.run_market_scan(...)  → list[ScoredCandidate]    │
  │     2. for each candidate market:                                │
  │          client.get_order_book(yes_token)  → OrderBookSnapshot   │
  │          client.get_order_book(no_token)   → OrderBookSnapshot   │
  │          forecast = build_paper_naive_forecast(...)              │
  │          snapshot = build_paper_cost_aware_event_snapshot(...)   │
  │          report   = build_paper_cost_aware_event_strategy_report │
  │     3. build_paper_project_screening_report(all reports, ...)    │
  │     4. return PaperStrategyCycleReport                           │
  └──────────────────────────────────────────────────────────────────┘
                 │ imports (one-way, downward)
                 ▼
PAPER-ONLY / REPORT-ONLY LEAF LAYER  (stdlib + whitelisted intra-package only)
  ┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
  │ forecast_provider.py                 │  │ cost_aware_snapshot_builder.py        │
  │  PaperForecast (frozen dataclass)    │  │  build_paper_cost_aware_event_        │
  │  PaperForecastConfig                 │  │    market_snapshot(                   │
  │  build_paper_naive_forecast(         │  │      market, yes_book, no_book,       │
  │    market, yes_book, no_book, *,     │  │      forecast, *, config,             │
  │    config, generated_at)             │  │      generated_at)                    │
  │    → PaperForecast                   │  │    → PaperCostAwareEventMarketSnapshot│
  └──────────────────────────────────────┘  └──────────────────────────────────────┘
```

The two leaf modules are **paper-only / report-only** and follow the exact
conventions of `cost_aware_event_strategy.py` / `project_screening.py`
(frozen dataclasses, `__post_init__` validation, `Decimal`-only,
`paper_only=True` / `report_only=True` hard-enforced, append-only JSONL log,
verbatim validation-helper library, full scope-test coverage). The orchestrator
is a **live layer** like `pipeline.py` and is allowed to import `api`,
`normalize`, `pipeline`, `domain` — but it itself emits a paper-only report and
performs no exchange writes.

## Module 1 — forecast_provider.py (paper-only, report-only)

### Role

Produce the forecast-model outputs (`fair_probability_yes`, `confidence`) that
cost-aware consumes. v0 ships a single **naive baseline**: treat the executable
YES ask as the fair probability and derive confidence from book quality.
The module is structured so a real forecast model can be added later as a
sibling builder without touching cost-aware or the snapshot builder.

### Public API

```text
__all__ = (
    "PaperForecastConfig",
    "PaperForecast",
    "PaperForecastLog",
    "build_paper_naive_forecast",
)

PaperForecastConfig (frozen dataclass):
    config_version: str                         # canonical, e.g. "naive-forecast-v1"
    min_book_depth:        Decimal = 1.0000      # shares at best ask required to be non-low-confidence
    low_confidence_value:  Decimal = 0.5000      # confidence assigned when book is thin / lopsided
    high_confidence_value: Decimal = 0.7500      # confidence assigned when book is deep and balanced
    max_spread_for_high_confidence: Decimal = 0.0300

PaperForecast (frozen dataclass, paper_only=True, report_only=True):
    generated_at: datetime                      # UTC-normalized
    config_version: str
    market_slug: str
    question: str
    fair_probability_yes: Decimal               # ∈ [0,1], quantized to COST_QUANTUM
    confidence: Decimal                         # ∈ [0,1], quantized
    basis: str                                  # "yes_ask_naive_v0"
    reason_codes: tuple[str, ...]               # ≥1 canonical, e.g. ("yes_ask_basis","thin_book_low_confidence")
    paper_only: bool = True
    report_only: bool = True

PaperForecastLog (frozen dataclass):
    path: Path | str
    def append(self, forecast: PaperForecast) -> None    # append-only JSONL, allow_nan=False, sort_keys=True

build_paper_naive_forecast(
    market: NormalizedMarket,
    yes_book: OrderBookSnapshot,
    no_book: OrderBookSnapshot,
    *,
    config: PaperForecastConfig,
    generated_at: datetime,
) -> PaperForecast
```

### Naive forecast model

All values use `Decimal`. Inputs are caller-supplied (the orchestrator supplies
the live-fetched books; tests supply fixture books).

```text
# Best-quote extraction (asks are buys, bids are sells; both sides used only to
# sanity-check the no-arbitrage relationship, not to price the forecast).
yes_best_ask  = yes_book.asks[0].price  if yes_book.asks  else None
yes_best_bid  = yes_book.bids[0].price  if yes_book.bids  else None
no_best_ask   = no_book.asks[0].price   if no_book.asks   else None

# Fair probability = executable YES ask, clipped to [0,1].
# (Executable ask is the price a buyer actually pays; using the executable ask
# matches cost-aware's own buy-side edge convention.)
if yes_best_ask is None:
    # fair_probability_yes is a required Decimal (NOT Optional); use the
    # low-confidence value as a placeholder so the forecast dataclass stays
    # valid. Downstream cost-aware receives a valid snapshot; with no YES ask
    # it cannot price gross edge and emits blocked_by_inputs / no_paper_edge.
    # (Fixes claude Stage-1a Important #1.)
    fair_probability_yes = config.low_confidence_value
    confidence = config.low_confidence_value
    reason_codes += ("missing_yes_ask", "low_confidence_book")
else:
    fair_probability_yes = clamp(yes_best_ask, 0, 1)
    reason_codes += "yes_ask_basis"

# Confidence from book quality (depth + balance + spread), bucketed to two
# levels for v0 simplicity.
yes_ask_depth = yes_book.asks[0].size if yes_book.asks else ZERO
spread = (yes_best_ask - yes_best_bid) if (yes_best_ask and yes_best_bid) else None
deep_and_tight = (
    yes_ask_depth >= config.min_book_depth
    and spread is not None
    and spread <= config.max_spread_for_high_confidence
)
confidence = config.high_confidence_value if deep_and_tight else config.low_confidence_value
reason_codes += "high_confidence_book" if deep_and_tight else "low_confidence_book"
```

Non-goals for v0: no LSTM, no evidence weighting, no calibration, no multi-source
blend. The naive baseline exists solely to unblock the chain; its `basis`
field names the model so downstream audits know this is a placeholder.

### Validation rules

- `config_version` canonical nonblank string.
- All `Decimal` thresholds finite, nonnegative; `min_book_depth > 0`.
- `low_confidence_value`, `high_confidence_value` ∈ [0,1].
- `fair_probability_yes`, `confidence` ∈ [0,1], quantized to `COST_QUANTUM` (1e-6).
- `reason_codes` ≥ 1 canonical string tuple.
- `paper_only is True` and `report_only is True` asserted with `is`.
- `basis` must be a canonical nonblank string from a fixed set (`{"yes_ask_naive_v0"}` for v0).

### Scope tests (test_forecast_provider_scope.py)

- Imports only stdlib + `polymarket_alpha_lab.domain` (whitelisted for `NormalizedMarket`, `OrderBookSnapshot`, `OrderBookLevel`).
- Does not import any live/loader surface (`api`, `pipeline`, `normalize`, network/crypto/web/SDK).
- `__all__` exactly equals the 4-tuple above.
- No forbidden name fragments (`account`, `auth`, `wallet`, `client`, `live`, `order`, `rank`, `recommend`, `credential`, `broker`, `execution`, `fetch`, `websocket`, `sdk`).
- Package root exports the 4 symbols; README sections preserve paper boundaries.

## Module 2 — cost_aware_snapshot_builder.py (paper-only, report-only)

### Role

Convert `(market, order books, forecast)` into the exact
`PaperCostAwareEventMarketSnapshot` that `cost_aware_event_strategy.build_paper_cost_aware_event_strategy_report`
consumes. This is the mechanical extractor that has been missing.

### Public API

```text
__all__ = (
    "PaperCostAwareSnapshotConfig",
    "PaperCostAwareSnapshotAttempt",
    "PaperCostAwareSnapshotLog",
    "build_paper_cost_aware_event_market_snapshot",
)

PaperCostAwareSnapshotConfig (frozen dataclass):
    config_version: str                                # canonical, e.g. "snapshot-builder-v1"
    default_resolution_risk: Decimal = 0.1000           # baseline when market metadata is complete
    missing_rules_resolution_risk: Decimal = 0.3000     # bumped when rules_text/resolution_source absent
    imminent_resolution_risk_cap: Decimal = 0.0500      # CAP when resolution is very near (risk capped LOW = less ambiguity near expiry)
    imminent_resolution_horizon_hours: int = 24         # <= horizon → "imminent"

PaperCostAwareSnapshotAttempt (frozen dataclass, paper_only=True, report_only=True):
    # A "snapshot or reason it could not be built" envelope. The orchestrator
    # collects these and only feeds successful attempts into cost-aware.
    generated_at: datetime
    config_version: str
    market_slug: str
    question: str
    status: str                                # "snapshot_ready" | "blocked_missing_yes_book"
                                               # | "blocked_missing_no_book" | "blocked_non_binary_market"
                                               # | "blocked_unresolvable_outcome_pair" | "blocked_book_token_mismatch"
                                               # | "blocked_missing_forecast"
    snapshot: PaperCostAwareEventMarketSnapshot | None    # present iff status == "snapshot_ready"
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True

PaperCostAwareSnapshotLog (frozen dataclass):
    path: Path | str
    def append(self, attempt: PaperCostAwareSnapshotAttempt) -> None

build_paper_cost_aware_event_market_snapshot(
    market: NormalizedMarket,
    yes_book: OrderBookSnapshot,
    no_book: OrderBookSnapshot,
    forecast: PaperForecast,
    *,
    config: PaperCostAwareSnapshotConfig,
    generated_at: datetime,
) -> PaperCostAwareSnapshotAttempt
```

### Extraction logic

```text
# Binary-market gate: exactly two tokens required.
if len(market.tokens) != 2:
    return attempt(status="blocked_non_binary_market", snapshot=None, reason_codes=("non_binary_market",))

# Resolve YES/NO by outcome_name (case-insensitive), fall back to outcome_index.
# (Polymarket convention: outcome_name "Yes"/"No"; outcome_index 0/1. Do NOT
#  rely on tuple position — see claude I3 finding.)
YES_NAMES = {"yes", "true", "long"}
NO_NAMES  = {"no", "false", "short"}
yes_token = next((t for t in market.tokens if t.outcome_name.strip().lower() in YES_NAMES), None)
no_token  = next((t for t in market.tokens if t.outcome_name.strip().lower() in NO_NAMES), None)
if yes_token is None or no_token is None:
    # Fall back to outcome_index (0=YES, 1=NO) when names are non-standard.
    indexed = {t.outcome_index: t for t in market.tokens}
    yes_token = yes_token or indexed.get(0)
    no_token  = no_token  or indexed.get(1)
if yes_token is None or no_token is None or yes_token.token_id == no_token.token_id:
    return attempt(status="blocked_unresolvable_outcome_pair", snapshot=None,
                   reason_codes=("unresolvable_outcome_pair",))

# Defense against mislabeled books: verify the caller-supplied books match the
# resolved token_ids. (Catches orchestrator wiring bugs; see claude I3.)
if yes_book.token_id != yes_token.token_id or no_book.token_id != no_token.token_id:
    return attempt(status="blocked_book_token_mismatch", snapshot=None,
                   reason_codes=("book_token_mismatch",))

# Best-quote extraction per side.
yes_ask  = yes_book.asks[0] if yes_book.asks  else None   # OrderBookLevel | None
yes_bid  = yes_book.bids[0] if yes_book.bids  else None
no_ask   = no_book.asks[0]  if no_book.asks   else None
no_bid   = no_book.bids[0]  if no_book.bids   else None

yes_ask_price = yes_ask.price if yes_ask else None
yes_ask_size  = yes_ask.size  if yes_ask else None
yes_bid_price = yes_bid.price if yes_bid else None
no_ask_price  = no_ask.price  if no_ask  else None
no_ask_size   = no_ask.size   if no_ask  else None
no_bid_price  = no_bid.price  if no_bid  else None

# Spread = best YES ask - best YES bid (the executable buy-side spread). If
# either leg missing, spread falls back to the NO-side spread, else ZERO.
spread = _first_present(yes_ask_price - yes_bid_price, no_ask_price - no_bid_price, ZERO)

# Resolution risk: heuristic from market metadata.
resolution_risk = _resolution_risk(market, config, generated_at)

snapshot = PaperCostAwareEventMarketSnapshot(
    market_slug        = market.market.market_slug,
    question           = market.market.question,
    fair_probability_yes = forecast.fair_probability_yes,
    confidence         = forecast.confidence,
    yes_bid            = yes_bid_price,
    yes_ask            = yes_ask_price,
    yes_ask_size       = yes_ask_size,
    no_bid             = no_bid_price,
    no_ask             = no_ask_price,
    no_ask_size        = no_ask_size,
    spread             = spread,
    resolution_risk    = resolution_risk,
)
return attempt(status="snapshot_ready", snapshot=snapshot, reason_codes=("snapshot_built",))
```

`_resolution_risk` heuristic (v0):
```text
base = config.default_resolution_risk
if market.rules_text is None or market.resolution_source is None:
    base = max(base, config.missing_rules_resolution_risk)   # unclear rules → more risk
if market.market.end_time is not None:
    hours_to_resolution = (market.market.end_time - generated_at).total_seconds() / 3600
    if hours_to_resolution <= config.imminent_resolution_horizon_hours:
        base = min(config.imminent_resolution_risk_cap, base)   # about to resolve → cap risk LOW (less ambiguity, fixes claude M2)
return quantize(base)
```

(The `forecast` arg's existence is the gate: a `PaperForecast` with
`fair_probability_yes = None` cannot exist because the dataclass requires a
`Decimal`; the naive forecaster instead emits `low_confidence_value` when the
ask is missing. A `None` forecast object passed in raises `ValueError`.)

### Validation rules

- All `Decimal` thresholds finite, nonnegative; `imminent_resolution_horizon_hours` positive int (bool rejected).
- `status` must be in the fixed status tuple.
- When `status == "snapshot_ready"`, `snapshot` must be non-None and a `PaperCostAwareEventMarketSnapshot`; otherwise `snapshot` must be `None`.
- `reason_codes` ≥ 1 canonical string.
- `paper_only is True` and `report_only is True` asserted with `is`.

### Scope tests (test_cost_aware_snapshot_builder_scope.py)

- Imports only stdlib + `polymarket_alpha_lab.domain` + `polymarket_alpha_lab.forecast_provider` + `polymarket_alpha_lab.cost_aware_event_strategy` (whitelisted: needs `PaperCostAwareEventMarketSnapshot` and `PaperForecast`).
- Does not import any live/loader surface.
- `__all__` exactly equals the 4-tuple above.
- No forbidden name fragments.

## Module 3 — strategy_cycle.py (live orchestration layer)

### Role

The orchestrator. Like `pipeline.py`, this module lives in the **live layer**:
it imports `api`, `normalize`, `pipeline`, `domain`, and the two new leaf
modules. It produces a paper-only report and performs no exchange writes.

### Public API

```text
__all__ = (
    "PaperStrategyCycleConfig",
    "PaperStrategyCycleReport",
    "PaperStrategyCycleLog",
    "run_strategy_cycle",
)

PaperStrategyCycleConfig (frozen dataclass):
    config_version: str                              # canonical, e.g. "strategy-cycle-v1"
    forecast_config: PaperForecastConfig
    snapshot_config: PaperCostAwareSnapshotConfig
    strategy_config: PaperCostAwareEventStrategyConfig
    screening_config: PaperProjectScreeningConfig
    cost_assumptions: PaperCostAwareEventCostAssumptions
    max_markets_per_cycle: int = 50                  # positive, bool rejected

PaperStrategyCycleReport (frozen dataclass, paper_only=True, report_only=True):
    generated_at: datetime
    config_version: str
    scan_candidate_count: int                        # markets returned by scan
    considered_count: int                            # binary markets with both books fetched
    snapshot_ready_count: int
    blocked_counts: tuple[(status, int), ...]        # deterministic, sorted by status
    cost_aware_report_count: int                     # == snapshot_ready_count
    screening_report: PaperProjectScreeningReport | None   # None when no snapshots ready
    paper_only: bool = True
    report_only: bool = True

PaperStrategyCycleLog (frozen dataclass):
    path: Path | str
    def append(self, report: PaperStrategyCycleReport) -> None

run_strategy_cycle(
    *,
    client: MarketDataClient,                  # the same protocol pipeline.run_market_scan uses
    scan_config: MarketScanConfig,
    cycle_config: PaperStrategyCycleConfig,
    generated_at: datetime | None = None,      # default: datetime.now(UTC)
) -> PaperStrategyCycleReport
```

### Orchestration logic

```text
generated_at = generated_at or datetime.now(UTC)
candidates = pipeline.run_market_scan(client=client, config=scan_config, captured_at=generated_at)
candidates = candidates[: cycle_config.max_markets_per_cycle]

attempts = []
for candidate in candidates:
    market = candidate.market          # the NormalizedMarket carried by ScoredCandidate
    if len(market.tokens) != 2:
        record blocked_non_binary_market; continue
    yes_token, no_token = market.tokens[0].token_id, market.tokens[1].token_id
    yes_book = client.get_order_book(yes_token)
    no_book  = client.get_order_book(no_token)
    forecast = build_paper_naive_forecast(market, yes_book, no_book,
                                          config=cycle_config.forecast_config,
                                          generated_at=generated_at)
    attempt  = build_paper_cost_aware_event_market_snapshot(market, yes_book, no_book, forecast,
                                                            config=cycle_config.snapshot_config,
                                                            generated_at=generated_at)
    attempts.append(attempt)

ready_snapshots = [a.snapshot for a in attempts if a.status == "snapshot_ready"]
cost_aware_reports = [
    build_paper_cost_aware_event_strategy_report(
        snapshot=s,
        cost_assumptions=cycle_config.cost_assumptions,
        config=cycle_config.strategy_config,
        generated_at=generated_at,
    )
    for s in ready_snapshots
]
screening_report = (
    build_paper_project_screening_report(
        reports=tuple(cost_aware_reports),
        config=cycle_config.screening_config,
        generated_at=generated_at,
    )
    if cost_aware_reports else None
)

return PaperStrategyCycleReport(
    scan_candidate_count=len(candidates),
    considered_count=<binary markets with both books>,
    snapshot_ready_count=len(ready_snapshots),
    blocked_counts=<deterministic status tallies>,
    cost_aware_report_count=len(cost_aware_reports),
    screening_report=screening_report,
    ...
)
```

The orchestrator **catches per-market fetch/normalize errors**, records them as
`blocked_*` statuses on the attempt envelope, and continues — a single bad
market never aborts a cycle. The cycle's output is a complete audit envelope:
how many markets were scanned, how many were blocked and why, how many
produced cost-aware reports, and the final screening queue (or `None`).

### Validation rules

- All nested config objects validated by their own `__post_init__`.
- `max_markets_per_cycle` positive int (bool rejected).
- Counts must be internally consistent: `snapshot_ready_count <= considered_count <= scan_candidate_count`; `cost_aware_report_count == snapshot_ready_count`; `screening_report is None` iff `cost_aware_report_count == 0`.
- `blocked_counts` is a sorted tuple of `(status, int)` pairs covering every non-ready status observed.
- `paper_only is True` and `report_only is True` asserted with `is`.

### Scope tests (test_strategy_cycle_scope.py)

- This is a LIVE-LAYER module (like `pipeline.py`), so its allowed-imports set includes: stdlib + `polymarket_alpha_lab.api` + `polymarket_alpha_lab.domain` + `polymarket_alpha_lab.normalize` + `polymarket_alpha_lab.pipeline` + `polymarket_alpha_lab.forecast_provider` + `polymarket_alpha_lab.cost_aware_snapshot_builder` + `polymarket_alpha_lab.cost_aware_event_strategy` + `polymarket_alpha_lab.project_screening`.
- Still forbidden: network/crypto/web/SDK beyond the in-package `api` client, `os`/`subprocess`/`socket`/`ssl`/`sqlite3`/`importlib` direct use, and any live-execution/broker/order-placement surface.
- `__all__` exactly equals the 4-tuple above.
- No forbidden name fragments relating to execution (`place_order`, `submit_order`, `sign`, `wallet`, `private_key`, `credential`, `broker`, `kill_switch`).

## CLI

Extend `cli.py` with a `strategy-cycle` subcommand mirroring `scan`'s shape
(uses the default `PolymarketPublicClient`, reads the same scan config knobs,
adds `--max-markets`, `--forecast-config-version`, etc.). Output:
`artifacts/strategy-cycle-<timestamp>.jsonl` (one `PaperStrategyCycleReport`)
plus human-readable stdout summary (scan/considered/ready/blocked counts +
top-5 queue items). No daemon, no scheduler in v0 — the user runs it on demand
or via external cron. (A `while True: sleep` scheduler is explicitly a later
stage.)

## Data flow (end to end)

```text
PolymarketPublicClient (Gamma /markets + CLOB /book)
   │
   ▼
pipeline.run_market_scan → list[ScoredCandidate]   (already wired, unchanged)
   │
   ▼  per candidate:
   ├── client.get_order_book(yes_token), client.get_order_book(no_token)
   ├── forecast_provider.build_paper_naive_forecast → PaperForecast
   └── cost_aware_snapshot_builder.build_paper_cost_aware_event_market_snapshot → PaperCostAwareSnapshotAttempt
          │ (status=="snapshot_ready" only)
          ▼
   cost_aware_event_strategy.build_paper_cost_aware_event_strategy_report → PaperCostAwareEventStrategyReport
   │ (batch)
   ▼
project_screening.build_paper_project_screening_report → PaperProjectScreeningReport  (the research queue)
   │
   ▼
PaperStrategyCycleReport (audit envelope)  →  artifacts/*.jsonl
```

## Non-goals (Phase 1 boundary, enforced)

- No live order placement, cancellation, signing, or routing.
- No authentication, API keys, wallets, private keys, relayers.
- No account / position / balance / fill / history reads.
- No broker interface, no kill switch, no `HumanApprovalBroker`, no `LiveBroker`.
- No paper-trade execution loop (that is the next stage: approved-proposal → `simulate_order_book_fill` → journal).
- No real forecast model — the naive baseline is explicitly a placeholder; the
  `basis` field makes this auditable.
- No manual-execution-journal importer.
- No scheduler / daemon / cron wrapper inside the package (external cron is the
  user's choice).
- No compliance / legal / geographic analysis.

## Risks

1. **Naive forecast quality.** Using executable YES ask as `fair_probability_yes`
   produces ~zero gross edge against the same ask (the cost-aware module will
   emit `no_paper_edge` for most markets). This is **expected and correct** for
   v0: the naive baseline proves the pipeline runs end-to-end; meaningful edges
   arrive only when a real forecast model replaces it. The screening queue will
   defer / blocked buckets usefully. The `watch` / `research_ready` buckets are
   essentially unreachable under the naive model (gross edge ≈ 0 ⇒ net edge < 0
   ⇒ `no_paper_edge` / `blocked_by_cost` are the dominant cost-aware statuses),
   so an empty `watch` queue is EXPECTED, not a regression. Risk
   mitigation: the `basis` field flags every report as `yes_ask_naive_v0` so
   no one mistakes these for real signals.

2. **Resolution-risk heuristic is a guess.** v0 derives it from rules-text
   presence and time-to-resolution. It will mis-rate some markets. Acceptable
   for v0; documented; flagged in the report's reason codes.

3. **Rate limiting / partial fetch failure.** The orchestrator fetches 2 order
   books per candidate (up to `max_markets_per_cycle` × 2 calls). For 50
   markets that is 100 CLOB calls per cycle. Per-market errors are caught and
   recorded as blocked statuses; the cycle completes with whatever succeeded.
   No retry/backoff in v0 — added in a later operational stage if needed.

4. **Multi-outcome markets are skipped.** Only binary markets (2 tokens) are
   processed. This is the common Polymarket case but excludes some markets;
   recorded as `blocked_non_binary_market`.

5. **Scope-test layering is novel.** This is the first LIVE-LAYER module since
   `pipeline.py`. Its scope test must permit in-package `api`/`normalize`/`pipeline`
   imports while still forbidding network/crypto/SDK/exec surfaces. The pattern
   exists (pipeline.py is the precedent) but must be written carefully.

6. **Stage size.** Three modules + CLI is larger than the project's typical
   one-module-per-commit cadence. The plan addresses this by landing modules in
   dependency order (forecast → snapshot builder → orchestrator → CLI), each
   with its own RED-then-GREEN test cycle, so the tree is always green.

## Open questions for the reviewer (claude code)

1. Is the **naive-forecast design** (executable ask as fair probability,
   two-bucket confidence) an acceptable v0 unblocker, or should v0 instead
   ship *only* the `ForecastProvider` protocol with no concrete baseline,
   forcing the user to plug a model before any cycle runs?
2. Is the **resolution-risk heuristic** defensible for v0, or should
   `resolution_risk` be a required caller-supplied field (no heuristic)?
3. Is the **live-layer scope-test** approach (allow in-package `api` etc. while
   forbidding raw network/crypto/SDK) consistent with how `pipeline.py`'s
   scope is enforced, or does `pipeline.py` have no scope test today (making
   this the first such test and thus a precedent-setting decision)?
4. Is **three modules in one stage** too large given the project's one-module
   cadence? Should this be split into Stage 1a (two paper-only leaves) and
   Stage 1b (orchestrator + CLI)?
