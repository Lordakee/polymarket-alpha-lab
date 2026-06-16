# Book-Imbalance Forecast Provider v0 Design (Stage 2)

## Purpose

Stage 1a's `forecast_provider` naive baseline (`fair_probability_yes == yes_ask`,
`basis="yes_ask_naive_v0"`) makes YES gross edge exactly 0 for every market, so the
entire strategy-cycle chain emits only `no_paper_edge`/`blocked_by_*` and the
screening research queue never populates `research_ready`/`watch`. The pipeline
runs end-to-end (proved by Stage 1b) but produces no actionable signal — the
root cause is upstream (forecast), not downstream (execution).

Stage 2 ships a second, pluggable paper-only forecast primitive whose
`fair_probability_yes` is derived from YES/NO order-book **depth imbalance** (a
real market-microstructure signal: persistent bid-side pressure on YES implies
the executable ask underprices the outcome). This yields a non-zero,
explainable gross edge so the screening queue finally carries candidates a
human (or a later real model) can act on.

It does NOT fetch market data, authenticate, handle wallets/private keys/
credentials, use API clients, place/submit/sign/cancel orders, rank investments,
recommend trades, provide financial advice, or perform compliance/legal/
geographic analysis. It is paper-only and report-only.

## Why book imbalance (and what it is NOT)

- It is NOT a calibrated probabilistic forecast and NOT a research-grade model.
  It is an **improved baseline** — a deterministic, explainable transform of
  caller-supplied order books that produces a non-zero edge where the naive
  baseline produces zero. `basis="book_imbalance_v0"` makes this auditable.
- Microstructure rationale: for a binary Polymarket outcome, if the YES best-bid
  size materially exceeds the YES best-ask size, buy-side pressure exceeds
  near-term sell-side supply, a weak signal that the executable YES ask may be
  below the crowd's implied fair value. The reverse implies the opposite. The
  magnitude of the imbalance modulates how far the fair value is nudged off the
  ask. This is a placeholder signal, not alpha — its job is to unblock the chain
  and give downstream review something non-degenerate to triage.
- It is deliberately conservative: the nudge is bounded by a configurable cap
  so a lopsided book cannot push `fair_probability_yes` outside a sane band.

## Public API

```text
__all__ = (
    "PaperBookImbalanceForecastConfig",
    "PaperBookImbalanceForecast",
    "PaperBookImbalanceForecastLog",
    "build_paper_book_imbalance_forecast",
)

PaperBookImbalanceForecastConfig (frozen dataclass):
    config_version: str                              # canonical, e.g. "book-imbalance-forecast-v1"
    imbalance_strength: Decimal = 0.0200             # > 0; nudge per unit of imbalance (cap-bound)
    max_nudge: Decimal = 0.0500                       # > 0; |fair_p - yes_ask| cap
    min_book_depth: Decimal = 1.0000                  # > 0; shares at best bid+ask to be confident
    low_confidence_value: Decimal = 0.5000            # ∈ [0,1]
    high_confidence_value: Decimal = 0.7500           # ∈ [0,1]
    max_spread_for_high_confidence: Decimal = 0.0300

PaperBookImbalanceForecast (frozen, paper_only=True, report_only=True):
    generated_at: datetime                           # UTC-normalized
    config_version: str
    market_slug: str
    question: str
    fair_probability_yes: Decimal                    # ∈ [0,1], = clamp(yes_ask + imbalance_nudge, 0, 1), quantized
    confidence: Decimal                              # ∈ [0,1], quantized
    basis: str                                       # "book_imbalance_v0"
    yes_best_ask: Decimal | None                     # audit: executable ask used as the nudge origin
    yes_bid_size: Decimal | None                     # audit
    yes_ask_size: Decimal | None                     # audit
    imbalance: Decimal | None                        # audit: (bid_size - ask_size)/(bid_size+ask_size), None when unavailable
    nudge: Decimal                                   # audit: signed nudge applied (quantized), ZERO when inputs missing
    reason_codes: tuple[str, ...]                    # ≥1 canonical
    paper_only: bool = True
    report_only: bool = True

PaperBookImbalanceForecastLog (frozen):
    path: Path | str
    def append(self, forecast: PaperBookImbalanceForecast) -> None   # append-only JSONL, allow_nan=False, sort_keys=True

build_paper_book_imbalance_forecast(
    market: NormalizedMarket,
    yes_book: OrderBookSnapshot,
    no_book: OrderBookSnapshot,
    *,
    config: PaperBookImbalanceForecastConfig,
    generated_at: datetime,
) -> PaperBookImbalanceForecast
```

`no_book` is accepted for signature parity with the naive provider (so the
orchestrator can swap providers without changing call shape) and for future
cross-side sanity checks, but v0's nudge math uses only the YES book.

## Forecast model (all Decimal; caller-supplied books)

```text
yes_best_ask = yes_book.asks[0].price if yes_book.asks else None
yes_best_bid = yes_book.bids[0].price if yes_book.bids else None
yes_bid_size = yes_book.bids[0].size  if yes_book.bids  else ZERO
yes_ask_size = yes_book.asks[0].size  if yes_book.asks  else ZERO

# Imbalance ∈ [-1, 1]: positive = bid-side pressure (buyers stacked).
# I2 (audit reproducibility): quantize imbalance FIRST, then derive nudge from
# the quantized value, so the whole chain (imbalance -> nudge -> fair_p) is
# exactly reconstructable from stored audit fields.
total = yes_bid_size + yes_ask_size
imbalance = _quantize((yes_bid_size - yes_ask_size) / total)   if total > 0 else None

# Nudge origin = executable YES ask (buy-side edge convention, same as naive).
if yes_best_ask is None or imbalance is None:
    # Cannot form a nudge under the v0 model: fall back to a low-confidence
    # placeholder fair value (the low-confidence value), nudge ZERO.
    fair_probability_yes = config.low_confidence_value
    nudge = ZERO
    reason_codes += ("missing_yes_ask_or_depth", "low_confidence_book")
else:
    # Bounded nudge derived from the QUANTIZED imbalance; cap at max_nudge magnitude.
    raw_nudge = imbalance * config.imbalance_strength
    nudge = _quantize(_clamp_signed(raw_nudge, -config.max_nudge, config.max_nudge))
    fair_probability_yes = _quantize(_clamp(yes_best_ask + nudge, ZERO, ONE))
    reason_codes += ("book_imbalance_nudge",)

# Confidence from book quality (depth + spread), same two-bucket scheme as naive.
spread = (yes_best_ask - yes_best_bid) if (yes_best_ask is not None and yes_best_bid is not None) else None
deep_and_tight = (
    yes_ask_size >= config.min_book_depth
    and yes_bid_size >= config.min_book_depth
    and spread is not None
    and spread <= config.max_spread_for_high_confidence
)
confidence = config.high_confidence_value if deep_and_tight else config.low_confidence_value
reason_codes += ("high_confidence_book" if deep_and_tight else "low_confidence_book",)

basis = "book_imbalance_v0"
```

Notes:
- `imbalance` is the only non-Decimal intermediate (a ratio); it is stored as
  an audit field (Decimal, quantized) and `nudge` (the value actually applied to
  a Decimal) is always Decimal. `_clamp_signed` and `_clamp` quantize to
  COST_QUANTUM (`Decimal("0.000001")`).
- When the YES ask or depth is missing, the forecast still emits a valid
  `PaperBookImbalanceForecast` (required Decimal `fair_probability_yes` =
  `low_confidence_value`, `nudge = ZERO`) — downstream cost-aware then computes
  no executable gross edge and emits `blocked_by_inputs`/`no_paper_edge`. Same
  fail-safe pattern as the Stage 1a naive provider.

## Validation rules

- `config_version` canonical nonblank.
- All `Decimal` thresholds finite; `imbalance_strength > 0`, `max_nudge > 0`,
  `min_book_depth > 0`; `low_confidence_value`/`high_confidence_value` ∈ [0,1].
- `fair_probability_yes`, `confidence`, `nudge`, `imbalance` (when not None)
  quantized to COST_QUANTUM.
- `fair_probability_yes`, `confidence` ∈ [0,1].
- `nudge` magnitude ≤ `max_nudge` (when inputs present).
- `reason_codes` ≥ 1 canonical string.
- `basis == "book_imbalance_v0"`, validated against `BASIS_VALUES`.
- `paper_only is True` and `report_only is True` asserted with `is`.

## Scope tests (test_book_imbalance_forecast_scope.py)

- Imports only stdlib + `polymarket_alpha_lab.domain` (whitelisted for
  `NormalizedMarket`, `OrderBookSnapshot`, `OrderBookLevel`). No live/loader
  surface, no other intra-package module.
- `__all__` exactly equals the 4-tuple above.
- No forbidden name fragments (`account`, `auth`, `wallet`, `client`, `live`,
  `order`, `rank`, `recommend`, `credential`, `broker`, `execution`, `fetch`,
  `websocket`, `sdk`). NOTE: `OrderBookSnapshot`/`OrderBookLevel` are imported
  types — mirror how `test_cost_aware_snapshot_builder_scope.py` permits
  `cost_aware_event_strategy` imports while forbidding live surfaces.
- Six canonical scope tests + README boundary fragments.

## Strategy-cycle integration (Stage 2 also wires this)

The orchestrator does NOT hardcode the naive provider. Stage 2 adds a
`forecast_provider` selector to `PaperStrategyCycleConfig` (an enum-like string:
`"naive"` | `"book_imbalance"`) so the cycle can use either. Default stays
`"naive"` (no behavior change for existing callers); `"book_imbalance"` routes
through `build_paper_book_imbalance_forecast`. This is a small, additive change
to `strategy_cycle.py` (dispatch on the selector) — detailed in the plan.

## Non-goals (Phase 1 boundary, enforced)

- No live order placement/auth/wallets/credentials/exchange writes.
- No calibrated probabilistic model, no historical backtest, no external data
  ingestion. This is an improved baseline, not a research model.
- No removal of the naive provider (kept for parity/audit).
- No change to cost-aware, screening, or any Stage 1a leaf's contract.

## Risks

1. **Book-imbalance is a weak/placeholder signal.** It produces a non-zero,
   explainable edge but is NOT alpha. Markets with strong bid pressure that
   nonetheless resolve NO will generate false-positive `research_ready`
   candidates. This is acceptable for v0: the point is to unblock the chain and
   give review something to triage; `basis="book_imbalance_v0"` flags every
   report as this placeholder.
2. **Single-level depth only.** v0 reads only best-bid/best-ask sizes. Spoofable
   and noisy. A multi-level or volume-weighted variant is a later stage.
3. **No `no_book` use in v0.** Accepted for signature parity + future cross-side
   sanity checks, but unused now (flagged as dead-but-validated input, same as
   the naive provider's `no_book`).
4. **strategy_cycle selector change** touches a Stage 1b module — must stay
   additive (default `"naive"`, no behavior change) and re-pass the Stage 1b
   scope test (which may need `polymarket_alpha_lab.book_imbalance_forecast`
   added to its `ALLOWED_IMPORT_MODULES`).

## Open questions for the reviewer (claude code pre-stage)

1. Is book-imbalance the right "improved baseline" vs alternatives (e.g.
   midpoint-based, NO-side reverse, volume-weighted)? The reviewer may prefer a
   different microstructure signal — be decisive.
2. Should the strategy_cycle `forecast_provider` selector be a string enum or a
   callable/Protocol injection (more extensible but more surface)?
3. Is adding `book_imbalance_forecast` to strategy_cycle's scope-test
   `ALLOWED_IMPORT_MODULES` acceptable, or should the dispatch stay in a thin
   adapter outside strategy_cycle to avoid widening its scope?
4. Should `imbalance` use only YES-book levels, or combine YES+NO book imbalance
   (cross-side) for a more robust signal in v0?
