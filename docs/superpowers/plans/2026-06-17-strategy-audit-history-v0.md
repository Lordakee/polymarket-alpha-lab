# Strategy Audit History Summary v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Strategy Risk Audit history summary over `strategy-audits.jsonl`.

**Architecture:** Keep `strategy_risk_audit.py`, `runner.py`, and package-root exports unchanged. Add a pure `strategy_audit_history.py` module that summarizes already-loaded `PaperStrategyRiskAuditReport` values. Add a CLI-only `strategy-audit-history` command that reads `PaperStrategyRiskAuditLog` and prints the pure report without constructing a public client.

**Tech Stack:** Python frozen dataclasses, `Decimal`, pytest, existing CLI injection style, CodeGraph, Claude post-stage audit.

---

### Task 1: RED History Module Tests

**Files:**
- Create: `tests/test_strategy_audit_history.py`
- Later create: `src/polymarket_alpha_lab/strategy_audit_history.py`

- [x] **Step 1: Add tests for builder counts, latest fields, and validation**

Create `tests/test_strategy_audit_history.py` with:

```python
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_audit_history import (
    PaperStrategyRiskAuditHistoryConfig,
    build_paper_strategy_risk_audit_history_report,
)
from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)


def _audit_report(status: str, generated_at: datetime) -> PaperStrategyRiskAuditReport:
    status_map = {
        "audit_ready": ("pass", 6, 0, 0),
        "insufficient_evidence": ("incomplete", 0, 0, 6),
        "blocked_by_risk": ("fail", 0, 6, 0),
    }
    gate_status, pass_count, fail_count, incomplete_count = status_map[status]
    return PaperStrategyRiskAuditReport(
        generated_at=generated_at,
        config_version="strategy-risk-audit-v0",
        status=status,
        gate_count=6,
        pass_count=pass_count,
        fail_count=fail_count,
        incomplete_count=incomplete_count,
        gate_results=(
            PaperStrategyRiskAuditGateResult("paper_history", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("settlement_evidence", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("forecast_quality", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("cost_discipline", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("nav_drawdown", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("open_exposure", gate_status, "m"),
        ),
    )


def test_strategy_audit_history_summarizes_statuses_and_latest_gates():
    config = PaperStrategyRiskAuditHistoryConfig(
        config_version="strategy-audit-history-v0",
    )
    reports = (
        _audit_report("audit_ready", datetime(2026, 6, 17, 12, 0, tzinfo=UTC)),
        _audit_report(
            "insufficient_evidence",
            datetime(2026, 6, 17, 13, 0, tzinfo=UTC),
        ),
        _audit_report(
            "blocked_by_risk",
            datetime(2026, 6, 17, 14, 0, tzinfo=UTC),
        ),
    )

    history = build_paper_strategy_risk_audit_history_report(
        reports,
        config=config,
        generated_at=datetime(2026, 6, 17, 15, 0, tzinfo=UTC),
    )

    assert history.status == "latest_blocked_by_risk"
    assert history.audit_report_count == 3
    assert history.audit_ready_count == 1
    assert history.insufficient_evidence_count == 1
    assert history.blocked_by_risk_count == 1
    assert history.latest_audit_status == "blocked_by_risk"
    assert history.first_audit_generated_at == reports[0].generated_at
    assert history.latest_audit_generated_at == reports[-1].generated_at
    assert history.consecutive_non_ready_count == 2
    assert history.consecutive_blocked_by_risk_count == 1
    assert history.consecutive_insufficient_evidence_count == 0
    assert history.latest_failed_gate_names == (
        "paper_history",
        "settlement_evidence",
        "forecast_quality",
        "cost_discipline",
        "nav_drawdown",
        "open_exposure",
    )
    assert history.latest_incomplete_gate_names == ()
    rows = {row.audit_status: row for row in history.status_rows}
    assert rows["audit_ready"].audit_count == 1
    assert rows["audit_ready"].audit_ratio == Decimal("0.3333")
    gate_rows = {
        (row.gate_name, row.gate_status): row
        for row in history.gate_status_summaries
    }
    assert gate_rows[("nav_drawdown", "pass")].audit_count == 1
    assert gate_rows[("nav_drawdown", "incomplete")].audit_count == 1
    assert gate_rows[("nav_drawdown", "fail")].audit_count == 1
    assert history.paper_only is True
    assert history.report_only is True


def test_strategy_audit_history_empty_input_is_report_only():
    history = build_paper_strategy_risk_audit_history_report(
        (),
        config=PaperStrategyRiskAuditHistoryConfig(
            config_version="strategy-audit-history-v0",
        ),
        generated_at=datetime(2026, 6, 17, 15, 0, tzinfo=UTC),
    )

    assert history.status == "empty_audit_history"
    assert history.audit_report_count == 0
    assert history.latest_audit_status is None
    assert history.first_audit_generated_at is None
    assert history.latest_audit_generated_at is None
    assert history.latest_failed_gate_names == ()
    assert history.latest_incomplete_gate_names == ()
    assert all(row.audit_count == 0 for row in history.status_rows)
    assert all(row.audit_count == 0 for row in history.gate_status_summaries)


def test_strategy_audit_history_rejects_invalid_inputs():
    config = PaperStrategyRiskAuditHistoryConfig(
        config_version="strategy-audit-history-v0",
    )

    with pytest.raises(ValueError, match="audit_reports must be a list or tuple"):
        build_paper_strategy_risk_audit_history_report(
            object(),
            config=config,
            generated_at=datetime(2026, 6, 17, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="audit_reports must contain"):
        build_paper_strategy_risk_audit_history_report(
            (object(),),
            config=config,
            generated_at=datetime(2026, 6, 17, tzinfo=UTC),
        )
```

- [x] **Step 2: Run RED tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_audit_history.py -q
```

Expected: collection fails with `ModuleNotFoundError` for `strategy_audit_history`.

### Task 2: GREEN History Module

**Files:**
- Create: `src/polymarket_alpha_lab/strategy_audit_history.py`

- [x] **Step 1: Implement frozen dataclasses and builder**

Add:

- `PaperStrategyRiskAuditHistoryConfig`
- `PaperStrategyRiskAuditHistoryStatusRow`
- `PaperStrategyRiskAuditHistoryGateStatusSummary`
- `PaperStrategyRiskAuditHistoryReport`
- `build_paper_strategy_risk_audit_history_report(...)`

Implementation constraints:

- Accept only list/tuple input.
- Clone each `PaperStrategyRiskAuditReport`.
- Preserve append order.
- Use `Decimal("0.0001")` ratios with `ROUND_HALF_EVEN`.
- Set `paper_only=True` and `report_only=True`.
- Do not import `api`, `runner`, `cli`, network, auth, wallet, order, ranking, or recommendation modules.

- [x] **Step 2: Run GREEN tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_audit_history.py -q
```

Expected: pass.

### Task 3: RED CLI Tests

**Files:**
- Modify: `tests/test_cli.py`
- Later modify: `src/polymarket_alpha_lab/cli.py`

- [x] **Step 1: Add CLI tests**

Add tests that:

- Write a local `PaperStrategyRiskAuditLog`.
- Run `strategy-audit-history --strategy-audit-log <path>`.
- Assert exit `0`, printed `strategy-audit-history:` summary, latest status, counts, and no public client construction.
- Assert a missing/invalid history runner failure returns `1`.

- [x] **Step 2: Run RED CLI tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -k "strategy_audit_history" -q
```

Expected: fail because the CLI command does not exist yet.

### Task 4: GREEN CLI

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`

- [x] **Step 1: Wire imports, runner type, parser, command branch, and printer**

Add:

- imports from `strategy_audit_history`
- `StrategyAuditHistoryRunner` injection hook
- `strategy-audit-history` parser with required `--strategy-audit-log`
- `_run_strategy_audit_history(...)`
- `_print_strategy_audit_history_summary(...)`

The command must not call `client_factory()`.

- [x] **Step 2: Run GREEN CLI tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -k "strategy_audit_history" -q
```

Expected: pass.

### Task 5: Docs, Verification, Audit, Commit

**Files:**
- Modify: `README.md`
- Create/update: docs/spec files as needed

- [x] **Step 1: Document command and boundaries**

Document `strategy-audit-history --strategy-audit-log <path>` as local evidence
summary only. Avoid approval, recommendation, ranking, trade instruction,
financial advice, and live-execution wording.

- [x] **Step 2: Run verification**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_audit_history.py tests/test_cli.py tests/test_strategy_risk_audit_log.py tests/test_strategy_risk_audit_scope.py tests/test_runner_scope.py -q
.venv/bin/python -m pytest -q
git diff --check
rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----" --glob '!docs/superpowers/plans/**' --glob '!docs/superpowers/specs/**' .
codegraph sync && codegraph status .
```

Expected: tests pass, diff check exits `0`, secret scan exits `1` with no
matches, CodeGraph is up to date.

- [x] **Step 3: Claude post-stage audit**

Stage the diff and run Claude Code with `claude-opus-4-8`, effort `max`, asking
for Phase 1 boundary, CLI local-only behavior, tests, docs, and regression risk
review. Fix Critical/Important findings.

- [ ] **Step 4: Commit locally**

Commit:

```bash
git commit -m "feat: summarize strategy audit history"
```

Do not push `origin/main` unless the user explicitly overrides the pinned remote
rule.
