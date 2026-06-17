# Strategy Audit CLI v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local-only `strategy-audit` CLI command and full outcome-tracking report persistence so existing paper evidence can feed the Strategy Risk Audit without Python glue.

**Architecture:** Keep `strategy_risk_audit.py` pure. Add JSONL persistence for `OutcomeTrackingReport` in `outcome_tracker.py`, wire CLI orchestration in `cli.py`, and document the local-only boundary in README.

**Tech Stack:** Python dataclasses, Decimal-only domain values, JSONL logs, pytest, CodeGraph.

---

### Task 1: Outcome Tracking Log

**Files:**
- Modify: `tests/test_outcome_tracker.py`
- Modify: `src/polymarket_alpha_lab/outcome_tracker.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`

- [ ] **Step 1: Write RED tests**

Add tests for `OutcomeTrackingLog` append/read round-trip, empty file, blank lines, invalid JSON line number, invalid append input, and public API export.

- [ ] **Step 2: Run RED tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_outcome_tracker.py tests/test_init.py -q
```

Expected: fail because `OutcomeTrackingLog` is not implemented/exported.

- [ ] **Step 3: Implement log**

Add `OutcomeTrackingLog` to `outcome_tracker.py` using `asdict`, `_json_ready`, `_normalize_log_path`, `_validate_log_parent`, and `from_jsonable(OutcomeTrackingReport, row)`.

- [ ] **Step 4: Run GREEN tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_outcome_tracker.py tests/test_init.py -q
```

Expected: pass.

### Task 2: CLI Wiring

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `README.md`

- [ ] **Step 1: Write RED tests**

Add CLI tests for `check-outcomes --outcome-log`, `strategy-audit` runner seam, default local log read without client construction, optional outcome-log usage, and failure behavior.

- [ ] **Step 2: Run RED tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -q
```

Expected: fail because the new flags/command do not exist.

- [ ] **Step 3: Implement CLI**

Add `StrategyAuditRunner`, parser flags, `_run_strategy_audit`, `_latest_outcome_report`, `_print_strategy_audit_summary`, and `check-outcomes --outcome-log` append logic. Keep `strategy-audit` local-only and do not call `client_factory()`.

- [ ] **Step 4: Update README**

Document the local command, optional outcome log, and boundary language.

- [ ] **Step 5: Run GREEN tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_outcome_tracker.py tests/test_strategy_risk_audit.py tests/test_strategy_risk_audit_scope.py tests/test_init.py -q
```

Expected: pass.

### Task 3: Verification and Review

**Files:**
- All changed files

- [ ] **Step 1: Run full verification**

Run:

```bash
.venv/bin/python -m pytest -q
git diff --check
rg -n "ghp_|api[_-]?key|private[_-]?key|secret|token" --glob '!docs/superpowers/plans/**' --glob '!docs/superpowers/specs/**' .
codegraph sync
codegraph status .
```

Expected: tests pass, diff check clean, no committed secret matches, CodeGraph up to date.

- [ ] **Step 2: Request Claude review**

Run local Claude review with model `claude-opus-4-8`, effort `max`, over the staged diff, focused on Phase 1 boundaries, `strategy-audit` client isolation, outcome-log type recovery, and tests.

- [ ] **Step 3: Commit locally**

Commit all intended changes locally. Do not push unless the project push convention is explicitly changed.
