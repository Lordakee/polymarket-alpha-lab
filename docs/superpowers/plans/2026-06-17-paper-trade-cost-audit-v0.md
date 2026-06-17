# Paper Trade Cost Audit v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local-only cost audit over paper trade journal rows so Phase 1 can measure fee/slippage/edge drag without live trading or recommendations.

**Architecture:** Create a new leaf module `paper_trade_cost_audit.py` that accepts already-typed `PaperTradeRecord` values and returns a frozen report. Add a CLI command that reads `PaperTradeJournal.read(...)`, builds the report, and prints compact metrics without constructing a client.

**Tech Stack:** Python dataclasses, `Decimal`, pytest, existing CLI/parser patterns, CodeGraph-aware repo navigation.

---

### Task 1: Core Report Module

**Files:**
- Create: `src/polymarket_alpha_lab/paper_trade_cost_audit.py`
- Create: `tests/test_paper_trade_cost_audit.py`

- [ ] Write failing tests for:
  - empty input collapsing to zero counts and `None` means
  - aggregate metrics across complete and partial paper fills
  - rejection of non-`PaperTradeRecord` inputs
  - frozen dataclasses and hard `paper_only` / `report_only` flags
- [ ] Run `pytest tests/test_paper_trade_cost_audit.py -q` and verify it fails because the module is missing.
- [ ] Implement `PaperTradeCostAuditConfig`, `PaperTradeCostAuditReport`, and `build_paper_trade_cost_audit_report(...)`.
- [ ] Run `pytest tests/test_paper_trade_cost_audit.py -q` and verify it passes.

### Task 2: Public Exports And Scope Tests

**Files:**
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Create: `tests/test_paper_trade_cost_audit_scope.py`

- [ ] Write failing export tests in `tests/test_init.py`.
- [ ] Write failing scope tests that restrict imports to stdlib plus `polymarket_alpha_lab.journal`, restrict public exports to the new paper report API, and reject live/advice/order/auth/wallet naming surfaces.
- [ ] Run targeted tests and verify they fail before implementation.
- [ ] Add root exports and module `__all__`.
- [ ] Run targeted tests and verify they pass.

### Task 3: CLI Command

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `README.md`

- [ ] Write failing CLI tests for `cost-audit --trade-log <path>` that inject a forbidden `client_factory`.
- [ ] Implement parser branch, runner hook, local log read helper, and compact summary printer.
- [ ] Document the command in README under the Phase 1 report sections.
- [ ] Run `pytest tests/test_cli.py tests/test_paper_trade_cost_audit.py tests/test_paper_trade_cost_audit_scope.py tests/test_init.py -q` and verify it passes.

### Task 4: Verification, Review, Commit

**Files:**
- All changed files from Tasks 1-3

- [ ] Run full `pytest -q`.
- [ ] Run `git diff --check`.
- [ ] Run the narrow secret scan used in prior nodes.
- [ ] Run Claude review with `claude-opus-4-8` and `--effort max`.
- [ ] Fix any Critical/Important findings.
- [ ] Commit locally with `feat: add paper trade cost audit`.
