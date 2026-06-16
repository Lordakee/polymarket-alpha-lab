# Operational Freeze + NAV Risk Metrics v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze Phase 1 decision logic and add read-only NAV risk metrics over existing paper NAV logs.

**Architecture:** Add one pure `nav_risk_metrics.py` module that consumes typed `PaperNavSnapshot` values and computes Decimal-only risk metrics. Wire it into a separate `nav-risk` CLI command so no strategy cycle, NAV marking, outcome tracking, or paper execution behavior changes.

**Boundary:** NAV Risk Metrics v0 has no `PaperTradeRecord`, no `PaperTradeJournal`, no trade-log input, and no paper-trade count metric.

**Tech Stack:** Python stdlib, frozen dataclasses, Decimal, pytest, CodeGraph.

---

## File Structure

- Create `src/polymarket_alpha_lab/nav_risk_metrics.py`
  - Frozen config/report/exposure row dataclasses and pure metrics builder.
- Create `tests/test_nav_risk_metrics.py`
  - RED/GREEN behavior and validation tests.
- Create `tests/test_nav_risk_metrics_scope.py`
  - Static scope tests for read-only/import/export boundaries and README text.
- Modify `src/polymarket_alpha_lab/cli.py`
  - Add `nav-risk`, a `nav_risk_runner` injection hook, and risk summary printing.
- Modify `src/polymarket_alpha_lab/__init__.py`
  - Export the new API.
- Modify `tests/test_cli.py`
  - Assert `nav-risk --nav-log` reads through the injected runner and prints metrics.
- Modify `tests/test_init.py`
  - Assert package-root exports.
- Modify `README.md`
  - Document the operational freeze and NAV Risk Metrics v0.

## Task 1: RED Behavior Tests

- [ ] **Step 1: Add `tests/test_nav_risk_metrics.py`**

Tests must import the intended API and initially fail because the module does not exist. They should cover:

- empty snapshots collapse to counts and `None` metrics;
- sorted NAV time series computes peak/trough, cumulative return, max drawdown, worst NAV delta, and return volatility;
- latest marks compute open-position and mark-status counts;
- latest mark exit values produce deterministic exposure rows and concentration shares;
- invalid config/report values raise `ValueError`;
- all report dataclasses are frozen and `paper_only` / `report_only` are hard-enforced.

- [ ] **Step 2: Run RED behavior tests**

```bash
.venv/bin/python -m pytest tests/test_nav_risk_metrics.py -q
```

Expected: import failure for `polymarket_alpha_lab.nav_risk_metrics`.

## Task 2: RED Scope, Export, CLI Tests

- [ ] **Step 1: Add `tests/test_nav_risk_metrics_scope.py`**

Scope tests must assert:

- imports are limited to stdlib plus `positions`;
- no live API, browser, wallet, auth, account, order-placement, ranking, recommendation, or advice surfaces;
- public exports exactly match the four API names;
- package root exports only those four names from the module;
- README contains the operational-freeze and NAV-risk boundary text.

- [ ] **Step 2: Extend CLI and export tests as RED**

Add failing tests for:

- package-root exports in `tests/test_init.py`;
- `nav-risk` in `tests/test_cli.py`, using injected runners only and no client factory.

Run:

```bash
.venv/bin/python -m pytest tests/test_nav_risk_metrics_scope.py tests/test_init.py tests/test_cli.py -q
```

Expected: failures because module, exports, README, and CLI flag are not implemented yet.

## Task 3: Implement NAV Risk Metrics

- [ ] **Step 1: Create `nav_risk_metrics.py`**

Implement:

- `PaperNavRiskMetricsConfig(config_version: str)`
- `PaperNavRiskExposureRow(condition_id, market_slug, token_count, open_size, cost_basis, exit_value, share_of_exit_nav)`
- `PaperNavRiskMetricsReport(...)`
- `build_paper_nav_risk_metrics_report(nav_snapshots, *, config, generated_at)`

- [ ] **Step 2: Use Decimal-only math**

Compute all ratios with `Decimal`; quantize ratios and derived metrics to `Decimal("0.000001")`. Reject floats and non-finite Decimals.

- [ ] **Step 3: Run behavior tests**

```bash
.venv/bin/python -m pytest tests/test_nav_risk_metrics.py -q
```

Expected: pass.

## Task 4: CLI, Exports, README

- [ ] **Step 1: Add package-root exports**

Add the four API names to `src/polymarket_alpha_lab/__init__.py`.

- [ ] **Step 2: Add `nav-risk`**

In `cli.py`, add a `nav-risk` subcommand. It must build/print `PaperNavRiskMetricsReport` from typed local NAV logs. Existing `history` output remains unchanged.

- [ ] **Step 3: Add README sections**

Add:

- `## Phase 1 Operational Freeze`
- `## NAV Risk Metrics v0 Status`
- `## NAV Risk Metrics v0 Python API`

- [ ] **Step 4: Run focused tests**

```bash
.venv/bin/python -m pytest tests/test_nav_risk_metrics.py tests/test_nav_risk_metrics_scope.py tests/test_init.py tests/test_cli.py -q
```

Expected: pass.

## Task 5: Verification, Review, Commit

- [ ] **Step 1: Full tests**

```bash
.venv/bin/python -m pytest -q
```

- [ ] **Step 2: Static checks**

```bash
git diff --check
rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----" README.md docs src tests
codegraph sync
codegraph status .
```

- [ ] **Step 3: Local Claude review**

Use:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --no-session-persistence --tools ""
```

Review full staged diff for Critical/Important/Minor and Proceed/Block.

- [ ] **Step 4: Commit locally**

Commit locally but do not push `origin/main`, because the remote is intentionally pinned at `codex-handoff-20260616`.
