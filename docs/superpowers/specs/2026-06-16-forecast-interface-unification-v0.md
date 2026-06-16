# Forecast Interface Unification v0 Design (Stage 3)

## Purpose

Stage 2 shipped `book_imbalance_forecast` (a second forecast provider) + a
`forecast_provider` selector on `strategy_cycle`, but the chain is **inert
end-to-end** when `forecast_provider="book_imbalance"`: `cost_aware_snapshot_builder.py:135`
hard-enforces `isinstance(forecast, PaperForecast)`, and `PaperBookImbalanceForecast`
is a separate dataclass (not a subclass), so `build_paper_cost_aware_event_market_snapshot`
raises `ValueError("forecast must be a PaperForecast")`, which `strategy_cycle`'s
per-market `except Exception` catches → every market records `blocked_fetch_error` →
`snapshot_ready_count == 0` → empty screening queue. This is the exact opposite of
Stage 2's goal ("produce a non-zero edge so the screening queue carries candidates").

Stage 3 unifies the forecast interface so the snapshot builder accepts ANY forecast
whose contract it actually relies on (`fair_probability_yes` + `confidence`). This
unlocks the `book_imbalance` path end-to-end and establishes a clean extension point
for future forecast providers.

It does NOT change any forecast model, does NOT fetch, does NOT authenticate, handle
wallets/keys/credentials, place orders, or perform any exchange write.

## Approach — structural Protocol (no inheritance, no leaf coupling)

`cost_aware_snapshot_builder` reads ONLY `forecast.fair_probability_yes` and
`forecast.confidence` (lines 212-213). Both `PaperForecast` and
`PaperBookImbalanceForecast` carry these (plus 8 more shared audit fields). A
`runtime_checkable` structural `Forecast` Protocol capturing the fields the builder
actually uses lets both concrete forecasts satisfy it WITHOUT inheritance and WITHOUT
`book_imbalance_forecast` importing anything new (structural typing).

This keeps `book_imbalance_forecast` a pure leaf (stdlib + domain) — it does not need
to import the Protocol. Only `cost_aware_snapshot_builder` imports the Protocol
(replacing its current `PaperForecast` import).

## Public API change

### `forecast_provider.py` — add the Protocol (additive)

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Forecast(Protocol):
    """Structural contract for any forecast the cost-aware snapshot builder consumes.

    Satisfied structurally by PaperForecast (naive) and PaperBookImbalanceForecast
    (book-imbalance), and by any future forecast provider that carries these fields.
    The snapshot builder reads only fair_probability_yes and confidence; the remaining
    fields are declared for audit completeness (every existing Paper* forecast carries them).
    """
    generated_at: datetime
    config_version: str
    market_slug: str
    question: str
    fair_probability_yes: Decimal
    confidence: Decimal
    basis: str
    reason_codes: tuple[str, ...]
    paper_only: bool
    report_only: bool
```

`__all__` gains `"Forecast"` (it is a public interface other modules type against).
`PaperForecast` is unchanged (it already satisfies `Forecast` structurally).

### `cost_aware_snapshot_builder.py` — accept the Protocol

- Import: `from polymarket_alpha_lab.forecast_provider import PaperForecast` →
  `from polymarket_alpha_lab.forecast_provider import Forecast`.
- Type annotation: `forecast: PaperForecast` → `forecast: Forecast`.
- Guard: `if not isinstance(forecast, PaperForecast): raise ValueError("forecast must be a PaperForecast")`
  → `if not isinstance(forecast, Forecast): raise ValueError("forecast must satisfy the Forecast protocol")`.
- No other logic change — the builder still reads only `fair_probability_yes` + `confidence`.

`book_imbalance_forecast.py` is **unchanged** — `PaperBookImbalanceForecast` satisfies
`Forecast` structurally (it has all 10 declared fields). Its scope test is untouched
(imports only stdlib + domain).

## Validation rules

- `Forecast` is `@runtime_checkable` so `isinstance(x, Forecast)` works.
- `isinstance(PaperForecast(...), Forecast)` is True (regression — naive path unaffected).
- `isinstance(PaperBookImbalanceForecast(...), Forecast)` is True (the fix).
- The snapshot builder still raises on objects missing `fair_probability_yes`/`confidence`
  (e.g. a bare dict or a non-forecast dataclass) — the Protocol guard is a real check.

## Scope tests

- `test_forecast_provider_scope.py`: `Forecast` is a new public export → `EXPECTED_EXPORTS`
  gains `"Forecast"`. The forbidden-fragment/name sweeps must still pass (`Forecast` contains
  no forbidden fragment). Confirm `Forecast` does NOT trip the "does not define forbidden
  live/advice surface names" AST test.
- `test_cost_aware_snapshot_builder_scope.py`: `ALLOWED_IMPORT_MODULES` already includes
  `polymarket_alpha_lab.forecast_provider` — NO change needed (still imports from it, just
  a different name). Confirm `PaperForecast` is no longer referenced if the scope test
  asserted specific imported names.
- `test_book_imbalance_forecast_scope.py`: NO change (leaf unchanged, still stdlib + domain).

## Behavior tests

- `test_cost_aware_snapshot_builder.py`: add a test that a `PaperBookImbalanceForecast`
  is accepted by `build_paper_cost_aware_event_market_snapshot` and produces a
  `snapshot_ready` attempt (status == "snapshot_ready", snapshot is a valid
  `PaperCostAwareEventMarketSnapshot`). Keep the existing naive-forecast tests.
- `test_strategy_cycle.py`: add/strengthen a test that `forecast_provider="book_imbalance"`
  produces `snapshot_ready_count >= 1` and a non-None `screening_report` on a bid-heavy
  binary market (the end-to-end unlock — this is the Stage 3 acceptance criterion).
- `test_forecast_provider.py`: add `isinstance(naive_forecast, Forecast) is True`.

## Non-goals (Phase 1 boundary, enforced)

- No forecast model change. No fetch/auth/wallet/credential/order/exchange-write.
- No new module. No change to `book_imbalance_forecast.py` or `strategy_cycle.py`
  (the selector already exists from Stage 2; Stage 3 only unblocks it downstream).
- No removal of `PaperForecast` (it remains the naive provider's concrete type).

## Risks

1. **`runtime_checkable` Protocol subtlety.** `isinstance` against a runtime_checkable
   Protocol checks only the presence of declared attributes/methods, NOT their types.
   A malicious/wrong object with a `fair_probability_yes` attribute of the wrong type
   could pass the isinstance check and fail later. Mitigation: the snapshot builder
   still validates the downstream `PaperCostAwareEventMarketSnapshot` fields (Decimal
   range checks), so a wrong-typed forecast surfaces as a `blocked_*`/ValueError at
   snapshot construction — fail-loud, not silent. Acceptable.
2. **Scope-test EXPECTED_EXPORTS drift.** Adding `Forecast` to forecast_provider's
   `__all__` requires updating `test_forecast_provider_scope.py`'s `EXPECTED_EXPORTS`
   and `test_init.py`'s export assertion. Mechanical.
3. **Audit-field parity.** The Protocol declares 10 fields all current forecasts share.
   A future forecast that omits, say, `reason_codes` would fail the isinstance check —
   desirable (forces audit completeness), but document it.

## Open questions for the reviewer (claude code pre-stage)

1. Is a structural `runtime_checkable` Protocol the right shape vs a Union
   (`PaperForecast | PaperBookImbalanceForecast`) or making `PaperBookImbalanceForecast`
   inherit `PaperForecast`? Protocol keeps leaves decoupled; Union couples the builder
   to every concrete type; inheritance fights the frozen-dataclass + distinct-basis design.
2. Should `Forecast` declare only the 2 fields the builder reads (`fair_probability_yes`,
   `confidence`) for a minimal contract, or all 10 shared fields for audit completeness?
3. Should the Protocol live in `forecast_provider.py` (alongside `PaperForecast`) or in
   `domain.py` (the shared vocabulary module)? `forecast_provider.py` avoids widening
   `domain.py` and keeps forecast concepts together.
