# Strategy Evidence Snapshot v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local paper-only Strategy Evidence Snapshot over existing paper logs and audit-history evidence.

**Architecture:** Keep strategy-cycle behavior, run-loop behavior, Strategy Risk Audit math, and package-root exports unchanged. Add a pure `strategy_evidence.py` reducer over already-built typed reports, then add a local-only `strategy-evidence` CLI command that reads caller-selected logs and prints the pure report without constructing a public client.

**Tech Stack:** Python frozen dataclasses, `Decimal`, pytest, existing CLI injection style, CodeGraph, Claude post-stage audit.

---

### Task 1: RED Pure Module Tests

**Files:**
- Create: `tests/test_strategy_evidence.py`
- Later create: `src/polymarket_alpha_lab/strategy_evidence.py`

- [x] **Step 1: Add tests for evidence status, gaps, optional inputs, and validation**

Add tests that construct minimal valid `PerformanceSummary`,
`PaperNavRiskMetricsReport`, `PaperTradeCostAuditReport`,
`OutcomeTrackingReport`, and `PaperStrategyRiskAuditHistoryReport` values, then
assert:

- full evidence with no flags returns `local_evidence_observed`
- missing cycles/trades/nav/outcome/audit history returns deterministic gaps
- negative cost-adjusted edges and unexecutable open positions return
  `local_risk_flags`
- invalid config, generated_at, or wrong report input types raise `ValueError`
- `paper_only` and `report_only` are hard-enforced on the snapshot report

- [x] **Step 2: Run RED tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_evidence.py -q
```

Expected: collection fails with `ModuleNotFoundError` for `strategy_evidence`.

### Task 2: GREEN Pure Module

**Files:**
- Create: `src/polymarket_alpha_lab/strategy_evidence.py`

- [x] **Step 1: Implement frozen dataclasses and builder**

Add:

- `PaperStrategyEvidenceSnapshotConfig`
- `PaperStrategyEvidenceSnapshotReport`
- `build_paper_strategy_evidence_snapshot_report(...)`

Implementation constraints:

- Accept exact report types only.
- Use only caller-supplied typed reports.
- Do not read files, write logs, fetch, authenticate, rank, recommend, or import
  client/execution modules.
- Preserve `paper_only=True` and `report_only=True`.
- Use deterministic evidence-gap ordering.

- [x] **Step 2: Run GREEN tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_evidence.py -q
```

Expected: pass.

### Task 3: RED CLI Tests

**Files:**
- Modify: `tests/test_cli.py`
- Later modify: `src/polymarket_alpha_lab/cli.py`

- [x] **Step 1: Add CLI tests**

Add tests that:

- write local cycle/trade/nav/outcome/audit logs
- run `strategy-evidence --cycle-log <path> --trade-log <path> --nav-log <path> [--outcome-log <path>] [--strategy-audit-log <path>]`
- assert exit `0`, printed `strategy-evidence:` summary, evidence status, gap
  names, and no public client construction
- assert injected runner receives typed reports, config, and generated_at
- assert missing logs and runner failure return `1` without constructing a
  client or mutating logs
- assert `run` and `strategy-cycle` do not call a `strategy_evidence_runner`

- [x] **Step 2: Run RED CLI tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -k "strategy_evidence" -q
```

Expected: fail because the CLI command does not exist yet.

### Task 4: GREEN CLI

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`

- [x] **Step 1: Wire imports, runner type, parser, command branch, and printer**

Add:

- imports from `strategy_evidence`
- `StrategyEvidenceRunner` injection hook
- `strategy-evidence` parser with required local log paths and optional
  `--outcome-log` / `--strategy-audit-log`
- `_run_strategy_evidence(...)`
- `_print_strategy_evidence_summary(...)`

The command must not call `client_factory()`.

- [x] **Step 2: Run GREEN CLI tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -k "strategy_evidence" -q
```

Expected: pass.

### Task 5: Docs, Verification, Audit, Commit

**Files:**
- Modify: `README.md`
- Modify: `docs/research/validation-gates.md`
- Create/update: docs/spec files as needed

- [x] **Step 1: Document command and boundaries**

Document `strategy-evidence` as local evidence observability only. Avoid
approval, recommendation, ranking, trade instruction, financial advice,
strategy-promotion, and live-execution wording.

- [x] **Step 2: Run verification**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_evidence.py tests/test_cli.py tests/test_strategy_audit_history.py tests/test_strategy_risk_audit_log.py tests/test_strategy_risk_audit_scope.py tests/test_runner_scope.py -q
.venv/bin/python -m pytest -q
git diff --check
rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----" --glob '!docs/superpowers/plans/**' --glob '!docs/superpowers/specs/**' .
codegraph sync && codegraph status .
```

Expected: tests pass, diff check exits `0`, secret scan has no matches, and
CodeGraph is up to date.

- [x] **Step 3: Claude post-stage audit**

Stage the diff and run Claude Code with `claude-opus-4-8`, effort `max`, asking
for Phase 1 boundary, CLI local-only behavior, tests, docs, and regression risk
review. Fix Critical/Important findings.

- [ ] **Step 4: Commit locally**

Commit:

```bash
git commit -m "feat: summarize strategy evidence"
```

Do not push `origin/main` unless the user explicitly overrides the pinned remote
rule.
