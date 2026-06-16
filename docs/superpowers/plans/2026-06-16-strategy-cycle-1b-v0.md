# Strategy Cycle v0 — Stage 1b Implementation Plan (orchestrator + CLI)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development`. Land the orchestrator module in RED-then-GREEN order; keep the tree green after every task. The two Stage 1a leaves are already implemented and frozen — import from them, do not modify them.

**Goal:** Wire the Stage 1a leaf modules into a self-contained, paper-only, on-demand strategy cycle that scans Polymarket, evaluates each binary market through the cost-aware + screening chain, and emits a deterministic `PaperStrategyCycleReport` research envelope + a `strategy-cycle` CLI. Resolves Critical C1 via approach (b2). Respects the AGENTS.md Phase 1 boundary line-for-line.

**Architecture:** `strategy_cycle.py` is a live-layer orchestrator (imports `api`/`normalize`/`archive`/`scoring` + the Stage 1a leaves + `cost_aware_event_strategy` + `project_screening`). It runs its own scan loop (does NOT call `pipeline.run_market_scan`), retains `NormalizedMarket` + paired YES/NO books end-to-end, and wraps each market in try/except so a single failure is recorded as a `blocked_*` status without aborting the cycle. See `docs/superpowers/specs/2026-06-16-strategy-cycle-1b-v0.md`.

**Tech Stack:** Python 3.11+, `Decimal`-only for numeric report fields, frozen dataclasses, `paper_only=True`/`report_only=True` hard-enforced on the report, append-only JSONL log. pytest>=8.0. Run tests with `.venv/bin/python -m pytest`.

## Pre-stage gate — Stage 1b (MANDATORY before Task 1)

- [ ] 0. **Claude code pre-stage review of the Stage 1b spec + this plan** (primary reviewer, claude-opus-4-8 / effort max). Run from repo root:
      `claude -p --model claude-opus-4-8 --effort max "Stage 1b pre-stage review. Read docs/superpowers/specs/2026-06-16-strategy-cycle-1b-v0.md + this plan (docs/superpowers/plans/2026-06-16-strategy-cycle-1b-v0.md) + AGENTS.md (Phase 1 boundary) + src/polymarket_alpha_lab/pipeline.py (the precedent live-layer module) + src/polymarket_alpha_lib/cost_aware_event_strategy.py + project_screening.py + the two Stage 1a leaves. This stage resolves Critical C1 (ScoredCandidate is flat, no NormalizedMarket) via approach (b2): strategy_cycle runs its own scan. Check: (1) b2 vs (a) — is self-contained scan correct over extending pipeline.run_market_scan? (2) Is asserting paper_only/report_only on the report correct given the module does live network reads? (3) Is the first live-layer scope test (pipeline.py has none) precedent acceptable, and is the api import widening justified? (4) Any Phase 1 boundary violation (orders/auth/wallets/credentials/exchange writes)? (5) Are the 5 open questions in the spec resolvable, or does any block implementation? Verdict: Proceed or Block, with Critical/Important/Minor findings + a one-paragraph answer to each of (1)-(5)."`
      Per AGENTS.md fallback rule: if Claude Code fails 2× consecutively (API/connection/gateway), fall back to `codex exec -m gpt-5.5 --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -c model_reasoning_effort=xhigh` with a HARD read-only constraint appended to the prompt.
      **Do not start Task 1 unless verdict is Proceed with no Critical findings.**

      Verdict recorded: `<fill after review>`

## File Structure

```text
CREATE  src/polymarket_alpha_lab/strategy_cycle.py
CREATE  tests/test_strategy_cycle.py
CREATE  tests/test_strategy_cycle_scope.py
MODIFY  src/polymarket_alpha_lab/__init__.py          # import block + 4 __all__ names
MODIFY  src/polymarket_alpha_lab/cli.py                # add strategy-cycle subcommand
MODIFY  tests/test_init.py                             # add test_strategy_cycle_public_api_exports
MODIFY  README.md                                      # Strategy Cycle v0 Status + Python API sections
```

## Task 1 — strategy_cycle (live-layer orchestrator)

- [ ] 1.1 **RED: behavior tests.** Write `tests/test_strategy_cycle.py`.
      Use a FAKE `MarketDataClient` (a small class implementing `list_markets`/`get_order_book` returning canned raw Gamma/CLOB payloads keyed by token_id; no real network). Build `NormalizedMarket` fixtures by calling `normalize_gamma_market` on canned payloads, or construct `NormalizedMarket` directly for determinism.
      Tests (cover the spec's orchestration + count invariants + per-market isolation):
      (a) One binary market, both books present → `scan_market_count==1`, `considered_count==1`, `snapshot_ready_count==1`, `cost_aware_report_count==1`, `screening_report is not None`, `screening_report.candidate_count==1`.
      (b) Non-binary market (1 or 3 tokens) → counted in `scan_market_count`/`considered`, recorded under `blocked_non_binary_market` in `blocked_counts`, no book fetch attempted.
      (c) A market whose `get_order_book` raises → recorded under `blocked_fetch_error`, cycle continues, OTHER markets still processed and counted.
      (d) Empty scan (list_markets returns []) → `screening_report is None`, `cost_aware_report_count==0`, invariant `screening_report is None ⇔ cost_aware_report_count==0` holds.
      (e) `max_markets_per_cycle` truncates the retained list (with `prefilter_by_score=False` to make truncation deterministic by input order).
      (f) `generated_at=None` → defaults to a UTC `datetime.now()` (assert `.tzinfo` is UTC).
      (g) `@pytest.mark.parametrize` config-validation rejection grid (`config_version` blank, `max_markets_per_cycle <= 0`, bool rejected, missing nested config).
      (h) Immutability (`FrozenInstanceError` on assignment) + `replace(report, paper_only=False)`/`report_only=False` raising `ValueError`.
      (i) JSONL round-trip via `tmp_path` — nested `screening_report` serializes (Decimals as quoted strings, `generated_at` ISO-UTC, `allow_nan=False`), existing file NOT mutated when a bad `append(object())` raises.
      (j) Count-invariant violations raise in `__post_init__` (e.g. construct a report with `cost_aware_report_count != snapshot_ready_count` → ValueError).
      (k) `blocked_counts` is sorted by status and `sum(blocked_counts values) + snapshot_ready_count == considered_count`.
      (l) **C1b — duplicate market_slug robustness:** two binary markets with the SAME `market_slug` both `snapshot_ready` → cycle does NOT crash on `build_paper_project_screening_report` (which raises on duplicate slug); dedupe keeps first, `screening_report.candidate_count == 1`, both still counted in `cost_aware_report_count==2`/`snapshot_ready_count==2`. Verify via `tmp_path` archive that no ValueError propagates.
      (m) **C2b — distinct per-token archive files:** run a cycle with ≥2 binary markets using a fake client + `tmp_path` archive_root; assert each market's YES/NO books land in DISTINCT files (name contains token_id, e.g. `book-<yes_token_id>.json`), not overwriting each other — verify `>= 4` distinct book archive files exist after a 2-market cycle.
      Run `.venv/bin/python -m pytest tests/test_strategy_cycle.py -q` and RECORD the RED failure (ImportError).
      RED evidence: `<record>`

- [ ] 1.2 **RED: scope tests.** Write `tests/test_strategy_cycle_scope.py` cloned from `test_project_screening_scope.py`, swapping names.       Module docstring MUST record: "First live-layer scope contract (pipeline.py has none); strategy_cycle.py is Protocol-only (does NOT import api — depends on a local MarketDataClient Protocol; cli.py constructs the concrete client and injects it), setting a tighter live-layer precedent than pipeline.py."
      `ALLOWED_IMPORT_MODULES` = stdlib + `polymarket_alpha_lab.{domain, normalize, archive, scoring, forecast_provider, cost_aware_snapshot_builder, cost_aware_event_strategy, project_screening}`. (Q5 RESOLVED per pre-stage review: `api` is NOT imported — strategy_cycle.py defines a local `MarketDataClient` Protocol and depends on it only; `cli.py` constructs the concrete `PolymarketPublicClient` and injects it. This removes the `api` widening and sets a tighter live-layer precedent than pipeline.py.)
      `FORBIDDEN_IMPORT_PREFIXES`: raw os/subprocess/socket/ssl/sqlite3/importlib/urllib* + network/crypto/web/SDK packages + non-internal polymarket*.
      `FORBIDDEN_NAME_FRAGMENTS`/`FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS`: usual set PLUS `place_order`, `submit_order`, `sign`, `wallet`, `private_key`, `credential`, `broker`, `kill_switch`, `liveexecution`, `orderplacement`.
      `EXPECTED_EXPORTS = ("PaperStrategyCycleConfig", "PaperStrategyCycleReport", "PaperStrategyCycleLog", "run_strategy_cycle")`.
      Six canonical scope tests. README scope test must be COMMENTED OUT with `# TODO Stage-1b wiring: re-enable when README section lands` (README is Task 3); package-root export test SKIPPED with the same reason until `__init__.py` wiring lands.
      Run and record RED.
      RED evidence: `<record>`

- [ ] 1.3 **GREEN: production module.** Implement `src/polymarket_alpha_lab/strategy_cycle.py` per spec §Architecture + §"Orchestration logic". Clone the validation-helper library + `Log` pattern verbatim from `cost_aware_event_strategy.py`/`project_screening.py`. Key implementation points:
      - `run_strategy_cycle` keyword-only after `*`; `generated_at` defaults to UTC now.
      - Step 1: `client.list_markets(active=True, closed=False, limit=scan_config.limit)`; `RawArchive(scan_config.archive_root).write("gamma_markets", payload, captured_at=generated_at)`.
      - Step 2: normalize each raw market (try/except skip malformed); optional `score_market` prefilter; truncate to `max_markets_per_cycle`.
      - Step 3: per-market try/except — binary gate, fetch+archive+normalize both books, forecast, snapshot attempt; on any Exception → `blocked_fetch_error` cycle-layer status; collect cost-aware reports for `snapshot_ready` attempts.
      - Step 4: screening report (or None).
      - Step 5: `PaperStrategyCycleReport` with ALL count invariants asserted in `__post_init__` (see spec §Validation rules), `blocked_counts` sorted, `paper_only is True`/`report_only is True` asserted with `is`.
      Run focused tests → green. Then `.venv/bin/python -m pytest -q` → full suite green (record count + timing).
      GREEN evidence: `<record>`

## Task 2 — CLI subcommand

- [ ] 2.1 Add `strategy-cycle` subparser to `cli.py` mirroring `scan` (default `PolymarketPublicClient`, same `--limit`/`--archive-root`/`--output` flags) + `--max-markets` (default 50), `--prefilter`/`--no-prefilter` (default prefilter). Constructs the concrete client (this is where `PolymarketPublicClient` is instantiated, per open-question Q5 decision). Runs `run_strategy_cycle`, writes `artifacts/strategy-cycle-<timestamp>.jsonl`, prints human summary (scan/considered/ready/blocked counts + top-5 queue items). No daemon.
- [ ] 2.2 Add `tests/test_cli.py` coverage: argv parse → calls `run_strategy_cycle` with a fake client injected (monkeypatch the client factory); assert exit 0 + stdout contains the summary counts. Keep existing `scan` test intact.
      Evidence: `<record>`

## Task 3 — Wiring (__init__, test_init, README)

- [ ] 3.1 `src/polymarket_alpha_lab/__init__.py`: add the `strategy_cycle` import block + extend `__all__` with the 4 new names (`PaperStrategyCycleConfig`, `PaperStrategyCycleReport`, `PaperStrategyCycleLog`, `run_strategy_cycle`) in the correct visual grouping. NOTE: `run_strategy_cycle` does NOT start with `build_`/`Paper` — place it among the lowercase action helpers (`evaluate_*`, `get_*`, `simulate_*`, `mark_*`) near the end of `__all__`.
- [ ] 3.2 `tests/test_init.py`: add `test_strategy_cycle_public_api_exports` (asserts `expected_exports <= set(lab.__all__)` + `lab.<Name> is <Name>` identity for all 4). Add the 4 imports at the top from `polymarket_alpha_lab.strategy_cycle`.
- [ ] 3.3 `README.md`: add `## Strategy Cycle v0 Status` + `## Strategy Cycle v0 Python API` after the Cost-Aware Snapshot Builder sections. Include boundary-shorthand line (`paperonly`, `reportonly`, `nofetch` (the module fetches but the REPORT is paper-only — phrase carefully), `noauth`, `nowallet`, `noorder`, `norank`, `norecommend`, `nofinancialadvice`). State explicitly: fetches read-only public market data, places NO orders, holds NO credentials.
- [ ] 3.4 Re-enable the scope test's README + package-root checks (uncomment/unskip from Task 1.2). Run export/init/README tests → green.
      Evidence: `<record>`

## Task 4 — Full verification

- [ ] 4.1 `.venv/bin/python -m pytest -q` — full suite green (was 940 after Stage 1a; record new count + timing).
- [ ] 4.2 `git diff --check` — clean.
- [ ] 4.3 Secret scan: `rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----" README.md docs src tests` — no matches.
- [ ] 4.4 `codegraph sync && codegraph status .` — "Index is up to date".
      Evidence: `<record>`

## Post-stage gate — Stage 1b (MANDATORY before declaring stage complete)

- [ ] 5. **Claude code post-stage review** (primary, claude-opus-4-8 / effort max). Run from repo root:
      `claude -p --model claude-opus-4-8 --effort max "Stage 1b post-stage review. Spec: docs/superpowers/specs/2026-06-16-strategy-cycle-1b-v0.md. Read src/polymarket_alpha_lab/strategy_cycle.py + tests/test_strategy_cycle.py + tests/test_strategy_cycle_scope.py + cli.py changes. Verify: (1) Phase 1 boundary intact — no orders/auth/wallets/credentials/exchange writes, only read-only Gamma/CLOB fetches; (2) C1 resolved — strategy_cycle retains NormalizedMarket end-to-end and never assumes ScoredCandidate.market; (3) per-market try/except isolation works (one bad market never aborts the cycle); (4) all count invariants in PaperStrategyCycleReport.__post_init__ hold; (5) paper_only/report_only asserted with is despite live fetches; (6) no float, no forbidden imports, scope test enforces the live-layer allowed set; (7) the first live-layer scope test is sound. Verdict: Proceed to next stage or Block, with Critical/Important/Minor findings."`
      Fallback to codex (bypass) after 2 consecutive Claude failures.
      **Do not begin the next stage unless verdict is Proceed with no Critical findings.**

      Verdict recorded: `<fill after review>`

## Commit (ONLY when explicitly authorized by the user)

- [ ] 6. Per AGENTS.md, do NOT commit unless the user explicitly authorizes. When authorized: `git add README.md docs src tests && git commit -m "feat: add strategy cycle v0 orchestrator and cli"` (granular). **Do NOT `git push`** (remote pinned at `codex-handoff-20260616`).
