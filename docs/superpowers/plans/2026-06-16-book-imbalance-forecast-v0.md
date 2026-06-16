# Book-Imbalance Forecast Provider v0 Implementation Plan (Stage 2)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. RED-first per module; tree green after every task.

**Goal:** Ship a second pluggable paper-only forecast primitive (book-imbalance) whose `fair_probability_yes` is non-zero where the naive baseline is zero, so the screening research queue finally carries candidates. Additive — naive provider stays. Respects AGENTS.md Phase 1 boundary.

**Architecture:** One new paper-only leaf `book_imbalance_forecast.py` (mirrors `forecast_provider.py` structure) + a small additive `forecast_provider` selector on `PaperStrategyCycleConfig` (default `"naive"`, no behavior change). See `docs/superpowers/specs/2026-06-16-book-imbalance-forecast-v0.md`.

**Tech Stack:** Python 3.11+, Decimal-only, frozen dataclasses, paper_only/report_only hard-enforced, append-only JSONL. pytest>=8.0.

## Pre-stage gate (MANDATORY before Task 1)

- [ ] 0. **Claude code pre-stage review** (primary, claude-opus-4-8 / effort max) of spec + this plan. Run from repo root. Fallback to codex (bypass) after 2 consecutive Claude failures (AGENTS.md rule). **Do not start Task 1 unless verdict is Proceed with no Critical findings.**

      Verdict recorded: `<fill after review>`

## File Structure

```text
CREATE  src/polymarket_alpha_lab/book_imbalance_forecast.py
CREATE  tests/test_book_imbalance_forecast.py
CREATE  tests/test_book_imbalance_forecast_scope.py
MODIFY  src/polymarket_alpha_lab/strategy_cycle.py        # additive forecast_provider selector (default "naive")
MODIFY  tests/test_strategy_cycle.py                       # cover selector dispatch
MODIFY  tests/test_strategy_cycle_scope.py                 # add book_imbalance_forecast to ALLOWED_IMPORT_MODULES
MODIFY  src/polymarket_alpha_lab/__init__.py               # import block + 4 __all__ names
MODIFY  tests/test_init.py                                 # export-assertion function
MODIFY  README.md                                          # Book-Imbalance Forecast v0 Status + Python API
```

## Task 1 — book_imbalance_forecast (paper-only leaf)

- [ ] 1.1 **RED: behavior tests** (`tests/test_book_imbalance_forecast.py`): frozen `GENERATED_AT`; `**overrides` factories for config/market/books. Tests: (a) bid-heavy YES book (bid_size > ask_size) → `fair_probability_yes > yes_ask` by a bounded positive nudge; (b) ask-heavy → nudge negative; (c) balanced → nudge ≈ 0; (d) nudge magnitude ≤ `max_nudge`; (e) missing yes ask or zero depth → `fair_probability_yes == low_confidence_value`, `nudge == ZERO`, reason_codes include `missing_yes_ask_or_depth`; (f) `imbalance` field ∈ [-1,1] and quantized; (g) confidence two-bucket (deep+tight → high); (h) `basis == "book_imbalance_v0"`; (i) `@pytest.mark.parametrize` config-validation rejection grid; (j) immutability + `paper_only`/`report_only` `replace(...,False)` raises; (k) JSONL round-trip via `tmp_path`. Record RED (ImportError).
- [ ] 1.2 **RED: scope tests** (`tests/test_book_imbalance_forecast_scope.py`): clone from `test_forecast_provider_scope.py`. `ALLOWED_IMPORT_MODULES` = stdlib + `polymarket_alpha_lab.domain`. Six canonical scope tests; README scope test COMMENTED OUT + package-root SKIPPED (`# TODO Stage-2 wiring`) until wiring lands. Record RED.
- [ ] 1.3 **GREEN**: implement `book_imbalance_forecast.py` per spec §"Forecast model" + §"Validation rules". Clone validation-helper library + Log pattern verbatim from `forecast_provider.py`. `BASIS_VALUES = ("book_imbalance_v0",)`. `_clamp`/`_clamp_signed` quantize to COST_QUANTUM. Focused green → full suite green.

## Task 2 — strategy_cycle selector (additive)

- [ ] 2.1 Add `forecast_provider: str = "naive"` AND `book_imbalance_config: PaperBookImbalanceForecastConfig | None = None` to `PaperStrategyCycleConfig`. In `__post_init__`: validate `forecast_provider ∈ {"naive","book_imbalance"}`; require `book_imbalance_config is not None` IFF `forecast_provider == "book_imbalance"` (C1 fix — otherwise dispatch hands a PaperForecastConfig to a builder that rejects it). Default `"naive"` + `None` = no behavior change for existing callers. In `run_strategy_cycle`, dispatch: `"naive"` → `build_paper_naive_forecast(..., config=cycle_config.forecast_config, ...)`; `"book_imbalance"` → `build_paper_book_imbalance_forecast(..., config=cycle_config.book_imbalance_config, ...)` (assert non-None). Import `PaperBookImbalanceForecastConfig` from `book_imbalance_forecast`.
- [ ] 2.2 Update `tests/test_strategy_cycle.py`: add a test that `forecast_provider="book_imbalance"` routes through the new builder (assert the report's basis via downstream audit, or that the new provider is invoked). Update `tests/test_strategy_cycle_scope.py` `ALLOWED_IMPORT_MODULES` to include `polymarket_alpha_lab.book_imbalance_forecast`.

## Task 3 — Wiring

- [ ] 3.1 `__init__.py`: import block + 4 `__all__` names.
- [ ] 3.2 `test_init.py`: `test_book_imbalance_forecast_public_api_exports` + imports.
- [ ] 3.3 `README.md`: `## Book-Imbalance Forecast v0 Status` + `## Book-Imbalance Forecast v0 Python API` (boundary shorthand: paper-only, report-only, no fetch, no auth, no wallet, no order, no rank, no recommend, no financial advice).
- [ ] 3.4 Re-enable `test_book_imbalance_forecast_scope.py` README + package-root tests.

## Task 4 — Full verification

- [ ] 4.1 `.venv/bin/python -m pytest -q` green (was 971; record new count).
- [ ] 4.2 `git diff --check` clean.
- [ ] 4.3 Secret scan (no matches).
- [ ] 4.4 `codegraph sync && codegraph status .` up-to-date.

## Post-stage gate (MANDATORY)

- [ ] 5. **Claude code post-stage review** (primary; fallback codex after 2 failures). Verify Phase 1 boundary, additive selector (default naive = no behavior change), no float, paper_only/report_only enforced, book-imbalance math bounded + audited. **Do not begin next stage unless Proceed with no Critical.**

## Commit (ONLY when explicitly authorized by the user)

- [ ] 6. Per AGENTS.md, do NOT commit unless user explicitly authorizes. When authorized: `feat: add book imbalance forecast v0`. Do NOT push.
