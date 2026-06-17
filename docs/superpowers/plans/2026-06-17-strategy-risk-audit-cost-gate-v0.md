# Strategy Risk Audit Cost Gate v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a cost discipline gate to Strategy Risk Audit using the local paper trade cost audit report.

**Architecture:** Keep `strategy_risk_audit.py` pure over typed reports. CLI reads local paper trade logs, builds `PaperTradeCostAuditReport`, and passes it into the audit alongside performance/NAV/outcome reports.

**Docs status:** User-facing docs should describe Strategy Risk Audit as a six-gate, Phase 1 paper-only/report-only/read-only audit. The sixth gate is `cost_discipline`, driven by a `PaperTradeCostAuditReport` built from local paper trade logs. Preserve the boundary explicitly: no live trading, no auth, no wallet, no private key handling, no order placement/signing/submission/cancellation, no account read, no recommendation, no ranking, no trade instruction, and no financial advice.

**Docs ownership for this pass:** `README.md` and this plan file only. Do not edit `cli.py`, tests, `strategy_risk_audit.py`, or spec docs in this docs pass.

**Tech Stack:** Python dataclasses, `Decimal`, pytest, CodeGraph, local Claude review.

---

### Task 1: Strategy Risk Audit Core Gate

**Files:**
- Modify: `tests/test_strategy_risk_audit.py`
- Modify: `tests/test_strategy_risk_audit_scope.py`
- Modify: `src/polymarket_alpha_lab/strategy_risk_audit.py`

- [ ] Add RED tests showing `cost_discipline` passes with enough low-drag cost evidence, is incomplete when absent/thin, and fails on excessive mean drag or negative cost-adjusted edge count.
- [ ] Update scope tests to allow importing only `PaperTradeCostAuditReport` from `polymarket_alpha_lab.paper_trade_cost_audit`.
- [ ] Implement `cost_audit_report` argument, config fields, sixth gate, and validation.
- [ ] Run `pytest tests/test_strategy_risk_audit.py tests/test_strategy_risk_audit_scope.py -q`.

### Task 2: CLI Strategy Audit Wiring

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `README.md`

- [ ] Add RED CLI assertions that `strategy-audit` passes a built `PaperTradeCostAuditReport` into the runner/default path while still not constructing a client.
- [ ] Update `_run_strategy_audit(...)` to build the cost audit from the already-read local trade log or typed trade records.
- [ ] Update printed summary expectations for six gates and README documentation.
- [ ] Run `pytest tests/test_cli.py tests/test_strategy_risk_audit.py tests/test_paper_trade_cost_audit.py -q`.

### Task 3: Verification, Review, Commit

**Files:**
- All changed files

- [ ] Run full `pytest -q`.
- [ ] Run `git diff --check`.
- [ ] Run the narrow secret scan.
- [ ] Run Claude review with `claude-opus-4-8` and `--effort max`.
- [ ] Fix any Critical/Important findings.
- [ ] Commit locally with `feat: add strategy cost audit gate`.
