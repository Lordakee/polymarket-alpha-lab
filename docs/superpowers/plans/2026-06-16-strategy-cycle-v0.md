# Strategy Cycle v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` when executing this plan. Land modules in dependency order; never edit two modules in the same task; keep the tree green after every task.

**Goal:** Wire the existing Level 0/1 library into an end-to-end, paper-only, on-demand strategy cycle that turns a Polymarket scan into a deterministic `PaperProjectScreeningReport` research queue, unblocking every downstream promotion gate. Respect the AGENTS.md Phase 1 boundary line-for-line.

**Architecture:** Two paper-only/report-only leaf modules (`forecast_provider.py`, `cost_aware_snapshot_builder.py`) feeding one live-layer orchestrator (`strategy_cycle.py`) that reuses `pipeline.run_market_scan`, `cost_aware_event_strategy`, and `project_screening` unchanged. Plus a `strategy-cycle` CLI subcommand. See `docs/superpowers/specs/2026-06-16-strategy-cycle-v0.md`.

**Tech Stack:** Python 3.11+, stdlib-only for the leaf modules; orchestrator imports the in-package `api`/`normalize`/`pipeline`/`domain` clients already used by `scan`. `Decimal` everywhere, frozen dataclasses, `paper_only=True`/`report_only=True` hard-enforced, append-only JSONL logs. pytest>=8.0.

## Stage split (per claude-opus-4-8 pre-stage review 2026-06-16)

**Initial pre-stage review: VERDICT Block** (one Critical: orchestrator rests on a
contract that does not exist — `ScoredCandidate` is flat per-token, carries no
`NormalizedMarket`/`.tokens`; `run_market_scan` discards it). The two paper-only
leaf modules were endorsed as "clean, self-contained, independently testable" with
zero dependency on the broken contract. Recommendation adopted: split.

- **Stage 1a (THIS plan, in scope now):** Task 1 `forecast_provider` + Task 2
  `cost_aware_snapshot_builder` + Task 5 (wiring for these two only) + Task 6
  (verification) + post-stage gate. Leaf-level review fixes applied to spec:
  I3 (YES/NO resolved by `outcome_name`/`outcome_index`, not tuple position, +
  `blocked_unresolvable_outcome_pair`/`blocked_book_token_mismatch` statuses),
  M1 (basis renamed `midpoint_naive_v0` → `yes_ask_naive_v0`), M2
  (`imminent_resolution_risk_floor` → `imminent_resolution_risk_cap`, logic
  `max` → `min`), I1 (bucket coverage corrected: defer/blocked, not watch).
- **Stage 1b (SEPARATE plan + separate pre-stage gate, deferred):** Task 3
  `strategy_cycle` + Task 4 CLI. Requires first resolving the
  `NormalizedMarket` plumbing (extend `pipeline.run_market_scan` OR have
  `strategy_cycle` self-scan via `normalize_gamma_market`) and the live-layer
  scope-test precedent (pipeline.py has no scope test today; `strategy_cycle`'s
  proposed `api` import is a widening beyond pipeline's actual imports).

## Pre-stage gate — Stage 1a focused re-review (MANDATORY before Task 1)

- [x] 0a. **Initial pre-stage review of full spec+plan: DONE → Block** (see Stage
      split above). Critical C1 recorded; leaf fixes I3/M1/M2/I1 applied to spec.
- [ ] 0b. **Claude code focused re-review of Stage 1a (the two leaves + fixes).**
      Run from repo root:
      `claude -p --model claude-opus-4-8 --effort max "Stage 1a focused re-review. The initial review blocked on orchestrator C1 (now deferred to Stage 1b). Read docs/superpowers/specs/2026-06-16-strategy-cycle-v0.md Module 1 (forecast_provider) + Module 2 (cost_aware_snapshot_builder) ONLY, plus the Stage split note. Verify the leaf-level fixes applied since the initial review are sound: (1) I3 — YES/NO resolution by outcome_name (case-insensitive, YES_NAMES/NO_NAMES sets) with outcome_index fallback + blocked_unresolvable_outcome_pair + blocked_book_token_mismatch token-id verification; (2) M1 — basis renamed to yes_ask_naive_v0, prose/reason-codes consistent; (3) M2 — imminent_resolution_risk_cap with min(base, cap) semantics (risk capped LOW near expiry); (4) I1 — bucket coverage corrected to defer/blocked. Also confirm: Phase 1 boundary intact for both leaves, no float, paper_only/report_only enforced, no forbidden imports (only stdlib + polymarket_alpha_lab.domain for Module 1; + forecast_provider + cost_aware_event_strategy for Module 2). Verdict: Proceed or Block, with any remaining Critical/Important findings on the LEAVES only."`
      Record the verdict below. **Do not start Task 1 unless verdict is Proceed with no Critical findings.**

      Verdict recorded: `<fill after 0b review>`

## File Structure

```text
# Stage 1a (in scope now)
CREATE  src/polymarket_alpha_lab/forecast_provider.py
CREATE  src/polymarket_alpha_lab/cost_aware_snapshot_builder.py
CREATE  tests/test_forecast_provider.py
CREATE  tests/test_forecast_provider_scope.py
CREATE  tests/test_cost_aware_snapshot_builder.py
CREATE  tests/test_cost_aware_snapshot_builder_scope.py
MODIFY  src/polymarket_alpha_lab/__init__.py          # import blocks + __all__ for the two leaves
MODIFY  tests/test_init.py                             # add 2 export-assertion functions
MODIFY  README.md                                      # 4 new sections (Status + API per leaf module)

# Stage 1b (DEFERRED — separate plan + pre-stage gate)
CREATE  src/polymarket_alpha_lab/strategy_cycle.py
CREATE  tests/test_strategy_cycle.py
CREATE  tests/test_strategy_cycle_scope.py
MODIFY  src/polymarket_alpha_lab/cli.py                # add strategy-cycle subcommand
MODIFY  src/polymarket_alpha_lab/__init__.py           # + orchestrator exports
MODIFY  tests/test_init.py                             # + orchestrator export-assertion
MODIFY  README.md                                      # + orchestrator sections
```

Stage 1a landing order: `forecast_provider` → `cost_aware_snapshot_builder` → wiring.

## Task 1 — forecast_provider (paper-only leaf)

- [ ] 1.1 **RED: behavior tests.** Write `tests/test_forecast_provider.py`:
      frozen `GENERATED_AT`; `**overrides` factories for `PaperForecastConfig`, `NormalizedMarket`, `OrderBookSnapshot`, `OrderBookLevel`; helpers `yes_book(...)`/`no_book(...)` building books from quoted-Decimal levels.
      Tests: (a) `build_paper_naive_forecast` returns `fair_probability_yes` == YES best ask (clamped to [0,1]), `confidence` == `high_confidence_value` when depth ≥ min and spread ≤ max, else `low_confidence_value`; (b) missing YES ask → `fair_probability_yes` absent path handled (the naive model still emits a forecast with `low_confidence_value` and `reason_codes` includes `missing_yes_ask` — verify the spec's exact behavior here and pin the test to it); (c) `reason_codes` always ≥1, includes `yes_ask_basis` or `missing_yes_ask` plus the confidence bucket code; (d) `basis == "yes_ask_naive_v0"`; (e) `@pytest.mark.parametrize` rejection grid for config validation (`config_version` blank, `min_book_depth <= 0`, confidence values out of [0,1], `NaN`/`Infinity` Decimal); (f) `FrozenInstanceError` on assignment; (g) `paper_only`/`report_only` `replace(...,False)` raises; (h) JSONL round-trip via `tmp_path` — Decimals serialize as quoted strings, `generated_at` ISO-UTC, existing-file not mutated on bad `append`.
      Run `.venv/bin/python -m pytest tests/test_forecast_provider.py -q` and record the RED failure (import error).
      RED evidence: `<record>`

- [ ] 1.2 **RED: scope tests.** Write `tests/test_forecast_provider_scope.py` cloned from `test_project_screening_scope.py`, swapping names. `ALLOWED_IMPORT_MODULES = {__future__, json, dataclasses, datetime, decimal, pathlib, typing, polymarket_alpha_lab.domain}`. `FORBIDDEN_IMPORT_PREFIXES` includes every live/loader surface. `EXPECTED_EXPORTS = ("PaperForecastConfig","PaperForecast","PaperForecastLog","build_paper_naive_forecast")`. Six canonical scope tests + README fragment list (`paperonly`,`reportonly`,`nofetch`,`noauth`,`nowallet`,`noorder`,`norank`,`norecommend`,`nofinancialadvice`).
      Run and record RED failure.
      RED evidence: `<record>`

- [ ] 1.3 **GREEN: production module.** Implement `src/polymarket_alpha_lab/forecast_provider.py` per spec §Module 1. Clone the validation-helper library verbatim from `cost_aware_event_strategy.py` (`_require_canonical_string` … `_validate_log_parent`, `_json_ready` rejecting float, `_validate_report_tree`, `_as_utc`). Copy the `Log` class verbatim. `COST_QUANTUM = Decimal("0.000001")`. Fixed `BASIS_VALUES = ("yes_ask_naive_v0",)` tuple. Implement `build_paper_naive_forecast` exactly per the spec's model block.
      Run `.venv/bin/python -m pytest tests/test_forecast_provider.py tests/test_forecast_provider_scope.py -q` → green.
      GREEN evidence: `<record>`

## Task 2 — cost_aware_snapshot_builder (paper-only leaf, depends on Task 1)

- [ ] 2.1 **RED: behavior tests.** Write `tests/test_cost_aware_snapshot_builder.py`:
      factories reuse Task 1's market/book builders plus a `forecast(**overrides)` factory.
      Tests: (a) binary market with both books + forecast → `status == "snapshot_ready"`, `snapshot` is a valid `PaperCostAwareEventMarketSnapshot` whose `yes_ask == yes_book.asks[0].price`, `yes_ask_size == asks[0].size`, `spread == yes_ask - yes_bid` (and NO-side fallback when YES-side missing), `resolution_risk` follows the heuristic (missing rules bumps to `missing_rules_resolution_risk`; imminent end_time floors to `imminent_resolution_risk_floor`); (b) non-binary market (1 or 3 tokens) → `status == "blocked_non_binary_market"`, `snapshot is None`; (c) missing YES book asks → snapshot still built with `yes_ask=None` (the upstream dataclass allows None) — verify the spec's exact branch and pin it; (d) `@pytest.mark.parametrize` rejection grid for config validation; (e) immutability; (f) `paper_only`/`report_only` enforcement; (g) JSONL round-trip (the attempt envelope serializes, `snapshot` field round-trips through `_json_ready`).
      Run and record RED.
      RED evidence: `<record>`

- [ ] 2.2 **RED: scope tests.** Clone, swap names. `ALLOWED_IMPORT_MODULES` adds `polymarket_alpha_lab.forecast_provider` and `polymarket_alpha_lab.cost_aware_event_strategy` (needs `PaperCostAwareEventMarketSnapshot`). `EXPECTED_EXPORTS = ("PaperCostAwareSnapshotConfig","PaperCostAwareSnapshotAttempt","PaperCostAwareSnapshotLog","build_paper_cost_aware_event_market_snapshot")`.
      Run and record RED.
      RED evidence: `<record>`

- [ ] 2.3 **GREEN: production module.** Implement `src/polymarket_alpha_lab/cost_aware_snapshot_builder.py` per spec §Module 2. Clone validation helpers + `Log` verbatim. Implement `_resolution_risk` and the binary-market gate. The `PaperCostAwareSnapshotAttempt` envelope is a frozen dataclass with `status` validated against a fixed tuple and the `snapshot is None` ⇔ `status != "snapshot_ready"` invariant asserted in `__post_init__`.
      Run focused tests → green.
      GREEN evidence: `<record>`

## Task 3 — strategy_cycle (live-layer orchestrator) — ⏸ DEFERRED to Stage 1b

> **DEFERRED.** Blocked by Critical C1 (orchestrator cannot source `NormalizedMarket`
> from `run_market_scan`). Move to a separate Stage 1b plan after resolving the
> plumbing decision (extend `pipeline` vs self-scan via `normalize_gamma_market`)
> and re-running a dedicated pre-stage gate. Kept below for reference.

- [ ] 3.1 **RED: behavior tests.** Write `tests/test_strategy_cycle.py`:
      use a fake `MarketDataClient` (the protocol `pipeline.run_market_scan` already accepts) returning canned `ScoredCandidate` lists and canned `OrderBookSnapshot` per `token_id`. No real network.
      Tests: (a) one binary market with both books → `scan_candidate_count==1`, `considered_count==1`, `snapshot_ready_count==1`, `cost_aware_report_count==1`, `screening_report is not None`, and the screening report's `candidate_count == 1`; (b) a non-binary market is counted in `scan_candidate_count` but not `considered_count`, and appears in `blocked_counts` under `blocked_non_binary_market`; (c) a market whose `get_order_book` raises → recorded as blocked, cycle continues, other markets still processed; (d) empty scan → `screening_report is None`, `cost_aware_report_count==0`, and `__post_init__` invariant (`screening_report is None` iff `cost_aware_report_count==0`) holds; (e) `max_markets_per_cycle` truncates the candidate list; (f) `generated_at=None` defaults to a UTC `datetime.now()`; (g) `@pytest.mark.parametrize` config validation; (h) immutability + `paper_only`/`report_only`; (i) JSONL round-trip (the nested `screening_report` serializes via `_json_ready` recursion).
      Run and record RED.
      RED evidence: `<record>`

- [ ] 3.2 **RED: scope tests.** This is the FIRST live-layer scope test. `ALLOWED_IMPORT_MODULES` includes stdlib + `polymarket_alpha_lab.{api,domain,normalize,pipeline,forecast_provider,cost_aware_snapshot_builder,cost_aware_event_strategy,project_screening}`. `FORBIDDEN_IMPORT_PREFIXES` still forbids raw `os`,`subprocess`,`socket`,`ssl`,`sqlite3`,`importlib`,`urllib*`, network/crypto/web/SDK packages (`requests`,`httpx`,`aiohttp`,`web3`,`eth_*`,`py_clob_client`,`polymarket*` non-internal), scraping/browser. **Before writing this test, read `tests/test_pipeline_scope.py` if it exists** — if `pipeline.py` has no scope test today, this becomes the precedent for live-layer scope; document that decision in the test's module docstring and confirm with the claude pre-stage review (Open question 3). `EXPECTED_EXPORTS = ("PaperStrategyCycleConfig","PaperStrategyCycleReport","PaperStrategyCycleLog","run_strategy_cycle")`. Forbidden name fragments include `place_order`,`submit_order`,`sign`,`wallet`,`private_key`,`credential`,`broker`,`kill_switch` (in addition to the usual set).
      Run and record RED.
      RED evidence: `<record>`

- [ ] 3.3 **GREEN: production module.** Implement `src/polymarket_alpha_lab/strategy_cycle.py` per spec §Module 3. `run_strategy_cycle` reuses `pipeline.run_market_scan`, catches per-candidate fetch/normalize errors into `blocked_*` statuses, batches ready snapshots into cost-aware reports, and builds the screening report (or `None`). `PaperStrategyCycleReport.__post_init__` asserts all count invariants and `screening_report is None` ⇔ `cost_aware_report_count==0`.
      Run focused tests → green.
      GREEN evidence: `<record>`

## Task 4 — CLI subcommand — ⏸ DEFERRED to Stage 1b

> **DEFERRED** (depends on Task 3). Kept below for reference.

- [ ] 4.1 Add `strategy-cycle` subparser to `cli.py` mirroring `scan` (default `PolymarketPublicClient`, same scan-config flags) plus `--max-markets`, `--forecast-config-version`, `--strategy-config-version`, `--screening-config-version`, `--output artifacts/strategy-cycle-<timestamp>.jsonl`. The command runs `run_strategy_cycle` and prints a human summary (scan/considered/ready/blocked counts + top-5 queue items). No daemon.
- [ ] 4.2 Add `tests/test_cli.py` coverage for the new subcommand (argv parse → calls `run_strategy_cycle` with a fake client; assert exit code 0 and stdout contains the summary counts). Keep the existing `scan` test intact.
      Evidence: `<record>`

## Task 5 — Wiring (__init__, test_init, README) — Stage 1a: two leaves only

- [ ] 5.1 `src/polymarket_alpha_lab/__init__.py`: add two import blocks (`forecast_provider`, `cost_aware_snapshot_builder`) and extend `__all__` with the 8 new names (4 per leaf) in the existing visual grouping.
- [ ] 5.2 `tests/test_init.py`: add `test_forecast_provider_public_api_exports`, `test_cost_aware_snapshot_builder_public_api_exports`. Each asserts `expected_exports <= set(lab.__all__)` and `lab.<Name> is <Name>` identity.
- [ ] 5.3 `README.md`: add `## Forecast Provider v0 Status` + `## Forecast Provider v0 Python API`, `## Cost-Aware Snapshot Builder v0 Status` + `## Cost-Aware Snapshot Builder v0 Python API` — each with the boundary-shorthand line (`paperonly`,`reportonly`,`nofetch`,`noauth`,`nowallet`,`noorder`,`norank`,`norecommend`,`nofinancialadvice`). The scope tests' `required_fragments` tuples must match these README sections exactly.
- [ ] 5.4 Run export/init/README tests → green.
      Evidence: `<record>`

## Task 6 — Full verification

- [ ] 6.1 `.venv/bin/python -m pytest -q` — full suite green (was 866; record new count + timing).
      Evidence: `<record>`
- [ ] 6.2 `git diff --check` — clean.
- [ ] 6.3 Secret scan: `rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----" README.md docs src tests` — exit 1, no matches.
- [ ] 6.4 `codegraph sync && codegraph status .` — "Index is up to date" with new file count (was 94).
      Evidence: `<record>`

## Post-stage gate — Stage 1a (MANDATORY before declaring stage complete)

- [ ] 7. **Claude code post-stage review of Stage 1a code.** Run from repo root:
      `claude -p --model claude-opus-4-8 --effort max "Stage 1a post-stage review. Spec: docs/superpowers/specs/2026-06-16-strategy-cycle-v0.md (Module 1 + Module 2). Plan: docs/superpowers/plans/2026-06-16-strategy-cycle-v0.md. Read the two new leaf modules in src/polymarket_alpha_lab/{forecast_provider,cost_aware_snapshot_builder}.py and their test pairs (behavior + scope). Verify: (1) Phase 1 boundary intact — no live orders/auth/wallets/credentials anywhere; (2) I3 fix — YES/NO resolution by outcome_name/outcome_index with blocked_unresolvable_outcome_pair + blocked_book_token_mismatch; (3) M1 — basis yes_ask_naive_v0 consistent; (4) M2 — imminent_resolution_risk_cap with min(base, cap); (5) no float, no forbidden imports, paper_only/report_only enforced; (6) JSONL logs append-only, allow_nan=False, sort_keys=True; (7) scope tests enforce allowed-imports + forbidden-fragments + exact __all__. Verdict: Proceed to Stage 1b planning or Block, with Critical/Important/Minor findings."`
      **Do not begin Stage 1b unless verdict is Proceed with no Critical findings.**

      Verdict recorded: `<fill after review>`

## Commit (ONLY when explicitly authorized by the user)

- [ ] 8. `git add README.md docs src tests && git commit -m "feat: add strategy cycle v0"` — single granular commit. **Do NOT `git push`** (AGENTS.md: local-only; remote pinned at `codex-handoff-20260616`).
