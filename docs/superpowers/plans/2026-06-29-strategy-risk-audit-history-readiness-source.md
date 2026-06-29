# Strategy Risk Audit History Readiness Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert existing paper strategy-risk-audit history into a pure readiness-compatible gate so autonomous readiness can throttle or block when recent risk-audit evidence is insufficient or blocked.

**Architecture:** Add a new pure reducer, `paper_strategy_risk_audit_history_gate`, mirroring the existing `paper_strategy_cycle_report_history_gate` pattern. Then wire its typed report into `paper_autonomous_readiness_gate` as an optional source while preserving legacy three-source reports and existing strategy-cycle four-source compatibility. This node deliberately does not add persistence/schema compatibility for the new source; DB row/schema/store support is a follow-up node.

**Tech Stack:** Python frozen dataclasses, existing paper-only/report-only/readonly report contracts, Decimal-free integer/timestamp gate fields, pytest, CodeGraph.

## Global Constraints

- Durable project data must use local Supabase/Postgres only.
- This node does not add durable storage, new tables, JSONL/file-backed persistence, SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, or a generic DB abstraction layer.
- Existing JSONL/file-backed journals are legacy compatibility surfaces; do not expand them.
- Phase 1 remains paper-only/read-only for market and trading behavior: no live trading, account auth, wallets, private keys, order signing/submission/cancellation/replacement, or exchange mutation.
- This node does not add a live readiness builder, broker adapter, wallet flow, order flow, or trade execution path.
- This node does not add CLI flags, DSN/table flags, env reads, DB loaders, migrations, DB rows, stores, or persistence paths.
- Review gates are read-only through local opencode using model `zhipuai-coding-plan/glm-5.2` and variant `max`.
- Codex worker subagents must use `gpt-5.5` with reasoning effort `xhigh`; fast mode is forbidden.

---

## Parallel Execution Shape

- **Wave 0:** Task 0 fixes strategy-risk-audit history compatibility for legacy six-gate and optional settlement seven-gate audit reports. This is a prerequisite for any gate built on audit history.
- **Wave 1:** Task 1 creates the pure strategy-risk-audit history gate in a new module and tests. This can run in parallel with Task 0 if its fixtures avoid settlement seven-gate reports until Task 0 lands.
- **Wave 2:** Task 2 wires the new gate report into the pure readiness reducer after Task 1 lands.
- **Wave 3:** Task 3 updates docs/scope and package exports if required.
- **Wave 4:** Focused integration tests, full verification, CodeGraph sync, opencode read-only review, push.

## File Structure

- Create `src/polymarket_alpha_lab/paper_strategy_risk_audit_history_gate.py`: pure history gate reducer.
- Create `tests/test_paper_strategy_risk_audit_history_gate.py`: gate reducer behavior and scope tests.
- Modify `src/polymarket_alpha_lab/strategy_audit_history.py`: accept legacy six-gate reports and optional settlement seven-gate reports without hard-coding the latest report count to six.
- Modify `tests/test_strategy_audit_history.py`: regression coverage for settlement seven-gate reports.
- Modify `src/polymarket_alpha_lab/paper_autonomous_readiness_gate.py`: optional strategy-risk source.
- Modify `tests/test_paper_autonomous_readiness_gate.py`: 3-source, strategy-cycle 4-source, strategy-risk 4-source, and 5-source behavior.
- Modify `tests/test_paper_autonomous_readiness_gate_scope.py`: allow the new pure import only.
- Modify `docs/paper-autonomous-readiness-gate.md` and `README.md` only if they list readiness sources.
- Modify `src/polymarket_alpha_lab/__init__.py` and `tests/test_init.py` only if matching the package-root export pattern for `paper_strategy_cycle_report_history_gate`.

---

### Task 0: Strategy Audit History Settlement Gate Compatibility

**Files:**
- Modify: `src/polymarket_alpha_lab/strategy_audit_history.py`
- Modify: `tests/test_strategy_audit_history.py`

**Interfaces:**
- Keeps existing public API unchanged:

```python
def build_paper_strategy_risk_audit_history_report(
    audit_reports: list[PaperStrategyRiskAuditReport]
    | tuple[PaperStrategyRiskAuditReport, ...],
    *,
    config: PaperStrategyRiskAuditHistoryConfig,
    generated_at: datetime,
) -> PaperStrategyRiskAuditHistoryReport:
    ...
```

- Accepts the existing six gate names:

```python
(
    "paper_history",
    "settlement_evidence",
    "forecast_quality",
    "cost_discipline",
    "nav_drawdown",
    "open_exposure",
)
```

- Also accepts optional seventh gate name:

```python
"settlement_nav_risk"
```

- History `gate_status_summaries` must cover the union of known gate names so legacy reports still have zero rows for absent optional gates.
- Latest gate count validation must compare against the latest report's `gate_count`, not a fixed `len(GATE_NAMES)`.
- `latest_failed_gate_names` and `latest_incomplete_gate_names` must include `settlement_nav_risk` when it is present and failed/incomplete.

- [ ] **Step 1: Write failing compatibility tests**

Add tests to `tests/test_strategy_audit_history.py`:

```python
def test_strategy_audit_history_accepts_optional_settlement_nav_risk_gate() -> None:
    ...
```

Expected assertions:

```python
assert history.latest_fail_count == 7
assert "settlement_nav_risk" in history.latest_failed_gate_names
assert gate_rows[("settlement_nav_risk", "fail")].audit_count == 1
assert gate_rows[("settlement_nav_risk", "pass")].audit_count == 0
assert gate_rows[("settlement_nav_risk", "incomplete")].audit_count == 0
```

Add a constructor validation test:

```python
def test_strategy_audit_history_validates_latest_counts_against_latest_report_gate_count() -> None:
    ...
```

It should prove replacing `latest_fail_count` from `7` to `6` on a seven-gate history raises `ValueError`.

- [ ] **Step 2: Run failing tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_strategy_audit_history.py
```

Expected before implementation: the optional `settlement_nav_risk` report fails validation.

- [ ] **Step 3: Implement minimal compatibility fix**

Keep the module pure. Do not add DB, CLI, env, network, execution, auth, wallet, or order imports. Update the known gate set and consistency validation so mixed six/seven-gate history remains deterministic.

- [ ] **Step 4: Run focused tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_strategy_audit_history.py tests/test_strategy_risk_audit.py
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/polymarket_alpha_lab/strategy_audit_history.py tests/test_strategy_audit_history.py
git commit -m "fix: allow settlement gate in strategy audit history"
```

---

### Task 1: Pure Strategy Risk Audit History Gate

**Files:**
- Create: `src/polymarket_alpha_lab/paper_strategy_risk_audit_history_gate.py`
- Create: `tests/test_paper_strategy_risk_audit_history_gate.py`

**Interfaces:**
- Consumes: `polymarket_alpha_lab.strategy_audit_history.PaperStrategyRiskAuditHistoryReport`
- Produces:

```python
DEFAULT_PAPER_STRATEGY_RISK_AUDIT_HISTORY_GATE_CONFIG_VERSION = (
    "paper-strategy-risk-audit-history-gate-v0"
)

class PaperStrategyRiskAuditHistoryGateConfig:
    config_version: str = DEFAULT_PAPER_STRATEGY_RISK_AUDIT_HISTORY_GATE_CONFIG_VERSION
    max_latest_age_seconds: int = 86_400
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

class PaperStrategyRiskAuditHistoryGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

class PaperStrategyRiskAuditHistoryGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[PaperStrategyRiskAuditHistoryGateReasonCodeCount, ...]
    source_history_status: str
    source_report_count: int
    latest_source_generated_at: datetime | None
    latest_source_age_seconds: int | None
    latest_audit_status: str | None
    latest_pass_count: int
    latest_fail_count: int
    latest_incomplete_count: int
    consecutive_non_ready_count: int
    consecutive_blocked_by_risk_count: int
    consecutive_insufficient_evidence_count: int
    latest_failed_gate_names: tuple[str, ...]
    latest_incomplete_gate_names: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

- Status and reason code contract:

```python
NEXT_STEP_BY_STATUS = {
    "pass": "allow_strategy_risk_audit_history_gate",
    "watch": "throttle_strategy_risk_audit_history_gate",
    "blocked": "block_strategy_risk_audit_history_gate",
}

PASS_REASON_CODE = "paper_strategy_risk_audit_history_gate_passed"
SOURCE_BLOCKED_REASON_CODE = "source_strategy_risk_audit_history_blocked_by_risk"
SOURCE_INSUFFICIENT_EVIDENCE_REASON_CODE = (
    "source_strategy_risk_audit_history_insufficient_evidence"
)
STALE_REASON_CODE = "stale_strategy_risk_audit_history"
MISSING_LATEST_REASON_CODE = "missing_latest_strategy_risk_audit_history_timestamp"
```

- Source status mapping:
  - `latest_audit_ready` with fresh latest timestamp -> `pass`
  - `latest_insufficient_evidence` -> `watch`
  - `latest_blocked_by_risk` -> `blocked`
  - `empty_audit_history` -> `blocked`
  - missing latest timestamp -> `blocked`
  - stale latest timestamp -> `watch`
  - future latest timestamp -> `ValueError`

- Source hard-flag handling:
  - `PaperStrategyRiskAuditHistoryReport` currently has `paper_only` and `report_only`, but no declared `readonly` field.
  - Require `paper_only is True` and `report_only is True`.
  - If a source object has a `readonly` attribute and it is not `True`, reject it.
  - Gate outputs must always include `readonly=True`.

- [ ] **Step 1: Write failing tests**

Create tests covering:

```python
def test_strategy_risk_audit_history_gate_passes_fresh_ready_history() -> None:
    ...
```

Expected assertions:

```python
assert gate.gate_status == "pass"
assert gate.recommended_next_step == "allow_strategy_risk_audit_history_gate"
assert gate.reason_codes == ("paper_strategy_risk_audit_history_gate_passed",)
assert gate.source_history_status == "latest_audit_ready"
assert gate.latest_source_age_seconds == 3600
assert gate.latest_audit_status == "audit_ready"
assert gate.paper_only is True
assert gate.report_only is True
assert gate.readonly is True
```

Add tests for:

```python
latest_blocked_by_risk -> blocked / source_strategy_risk_audit_history_blocked_by_risk
latest_insufficient_evidence -> watch / source_strategy_risk_audit_history_insufficient_evidence
empty_audit_history -> blocked / missing_latest_strategy_risk_audit_history_timestamp
fresh ready but stale latest timestamp -> watch / stale_strategy_risk_audit_history
blocked + stale -> blocked with both blocked and stale reasons
future latest timestamp -> ValueError
subclass rejection for config, reason rows, gate report, and source history report
frozen output dataclasses and constructor revalidation
unsafe source paper_only/report_only/readonly tampering rejection
module scope excludes psycopg, requests, httpx, aiohttp, socket, urllib, websocket, websockets, eth_account, CLI/env/order/wallet/auth terms
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_strategy_risk_audit_history_gate.py
```

Expected before implementation: import/module not found failure.

- [ ] **Step 3: Implement the pure reducer**

Use `paper_strategy_cycle_report_history_gate.py` as the structural model. Keep imports limited to:

```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from polymarket_alpha_lab.strategy_audit_history import PaperStrategyRiskAuditHistoryReport
```

Do not import DB, CLI, env, network, browser, paper execution, auth, wallet, or order modules.

- [ ] **Step 4: Run focused tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_strategy_risk_audit_history_gate.py tests/test_strategy_audit_history.py tests/test_strategy_risk_audit.py
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/polymarket_alpha_lab/paper_strategy_risk_audit_history_gate.py tests/test_paper_strategy_risk_audit_history_gate.py
git commit -m "feat: add strategy risk audit history gate"
```

---

### Task 2: Optional Readiness Source

**Files:**
- Modify: `src/polymarket_alpha_lab/paper_autonomous_readiness_gate.py`
- Modify: `tests/test_paper_autonomous_readiness_gate.py`
- Modify: `tests/test_paper_autonomous_readiness_gate_scope.py`

**Interfaces:**
- Consumes: `PaperStrategyRiskAuditHistoryGateReport` from Task 1.
- Adds source constant:

```python
STRATEGY_RISK_AUDIT_HISTORY_GATE_SOURCE_NAME = "strategy_risk_audit_history_gate"
```

- Builder signature:

```python
def build_paper_autonomous_readiness_gate_report(
    screening_report: object,
    allocation_report: object,
    investment_ledger_report: object,
    *,
    config: PaperAutonomousReadinessGateConfig,
    generated_at: datetime,
    strategy_cycle_history_gate_report: object | None = None,
    strategy_risk_audit_history_gate_report: object | None = None,
) -> PaperAutonomousReadinessGateReport:
    ...
```

- Canonical source validation:

```python
STRATEGY_RISK_AUDIT_HISTORY_GATE_SOURCE_NAME = "strategy_risk_audit_history_gate"

CANONICAL_SOURCE_NAMES = (
    SCREENING_SOURCE_NAME,
    STRATEGY_CYCLE_HISTORY_GATE_SOURCE_NAME,
    ALLOCATION_SOURCE_NAME,
    INVESTMENT_LEDGER_SOURCE_NAME,
    STRATEGY_RISK_AUDIT_HISTORY_GATE_SOURCE_NAME,
)

REQUIRED_SOURCE_NAMES = (
    SCREENING_SOURCE_NAME,
    ALLOCATION_SOURCE_NAME,
    INVESTMENT_LEDGER_SOURCE_NAME,
)
```

- Ordering when both optional sources are supplied:

```text
screening -> strategy_cycle_report_history_gate -> allocation -> investment_ledger -> strategy_risk_audit_history_gate
```

- Valid source combinations:

```text
screening -> allocation -> investment_ledger
screening -> strategy_cycle_report_history_gate -> allocation -> investment_ledger
screening -> allocation -> investment_ledger -> strategy_risk_audit_history_gate
screening -> strategy_cycle_report_history_gate -> allocation -> investment_ledger -> strategy_risk_audit_history_gate
```

- [ ] **Step 1: Write failing readiness tests**

Add tests for:

```python
def test_readiness_gate_includes_strategy_risk_audit_history_gate_as_optional_source():
    ...
```

Expected source names:

```python
(
    "screening_decision_support_gate_db_history_health",
    "allocation_proposal_db_history_health_trend_gate",
    "investment_ledger_db_history_health_trend_gate",
    "strategy_risk_audit_history_gate",
)
```

Expected reason code includes:

```python
"strategy_risk_audit_history_gate_pass"
```

Add tests for:

```python
strategy_risk_audit_history_gate watch throttles readiness
strategy_risk_audit_history_gate blocked blocks readiness
both strategy-cycle and strategy-risk optional sources produce five-source canonical order
direct constructor rejects noncanonical optional source ordering
builder rejects non-exact strategy risk audit history gate report type
```

Update `tests/test_paper_autonomous_readiness_gate_scope.py` to allow only:

```python
"polymarket_alpha_lab.paper_strategy_risk_audit_history_gate"
```

- [ ] **Step 2: Run failing focused tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_readiness_gate.py tests/test_paper_autonomous_readiness_gate_scope.py
```

Expected before implementation: missing keyword/source failures.

- [ ] **Step 3: Implement minimal readiness reducer change**

Add strict type check for `PaperStrategyRiskAuditHistoryGateReport`, validate hard flags, append the source at the tail after `investment_ledger_db_history_health_trend_gate`, and replace fixed tuple validation with canonical-order filtering:

```python
observed_names = tuple(row.source_name for row in rows)
if len(set(observed_names)) != len(observed_names):
    raise ValueError("source_statuses must not contain duplicate sources")
if not set(REQUIRED_SOURCE_NAMES).issubset(observed_names):
    raise ValueError("source_statuses must contain required sources")
if observed_names != tuple(name for name in CANONICAL_SOURCE_NAMES if name in observed_names):
    raise ValueError("source_statuses must contain the canonical source sequence")
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_paper_autonomous_readiness_gate.py \
  tests/test_paper_autonomous_readiness_gate_scope.py \
  tests/test_paper_strategy_risk_audit_history_gate.py
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/polymarket_alpha_lab/paper_autonomous_readiness_gate.py tests/test_paper_autonomous_readiness_gate.py tests/test_paper_autonomous_readiness_gate_scope.py
git commit -m "feat: add strategy risk audit source to readiness gate"
```

---

### Task 3: Docs, Exports, And Scope

**Files:**
- Modify: `docs/paper-autonomous-readiness-gate.md`
- Modify: `README.md`
- Modify: `src/polymarket_alpha_lab/__init__.py` only if following the existing package-root export pattern.
- Modify: `tests/test_init.py` only if exports changed.

**Requirements:**
- Document the optional strategy-risk-audit history source.
- State that legacy three-source readiness reports remain valid.
- State that strategy-cycle-only and strategy-risk-only four-source reports remain valid.
- State that five-source reports are produced only when both optional pure sources are supplied.
- State that this node does not add persistence, DB schema/store compatibility, DB loaders, env reads, CLI flags, live trading, auth, wallet handling, private keys, or order submission/cancellation/replacement.

- [ ] **Step 1: Search existing docs**

Run:

```bash
rg -n "Paper Autonomous Readiness Gate|paper autonomous readiness gate|strategy_cycle_report_history_gate|Source Reports|readiness gate" README.md docs tests
```

- [ ] **Step 2: Patch existing focused docs only**

Update existing source lists and boundary language. Do not add a broad new marketing-style doc.

- [ ] **Step 3: Run focused docs/scope tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_docs_paper_autonomous_readiness_gate_scope.py \
  tests/test_paper_autonomous_readiness_gate_scope.py \
  tests/test_init.py
```

- [ ] **Step 4: Commit**

```bash
git add README.md docs/paper-autonomous-readiness-gate.md src/polymarket_alpha_lab/__init__.py tests/test_init.py tests/test_docs_paper_autonomous_readiness_gate_scope.py
git commit -m "docs: document strategy risk audit readiness source"
```

If package exports are not changed, omit `src/polymarket_alpha_lab/__init__.py` and `tests/test_init.py` from the commit.

---

### Task 4: Integration Gate, Review, And Push

**Files:**
- No feature files unless fixing findings.

- [ ] **Step 1: Run focused integration tests**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_paper_strategy_risk_audit_history_gate.py \
  tests/test_strategy_audit_history.py \
  tests/test_strategy_risk_audit.py \
  tests/test_paper_autonomous_readiness_gate.py \
  tests/test_paper_autonomous_readiness_gate_scope.py \
  tests/test_docs_paper_autonomous_readiness_gate_scope.py \
  tests/test_init.py
```

- [ ] **Step 2: Run full verification**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
codegraph sync
git grep -n -E '(ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|sk-live-[A-Za-z0-9_-]{20,}|-----BEGIN (RSA |OPENSSH |EC |DSA |)PRIVATE KEY-----)' HEAD || true
```

- [ ] **Step 3: opencode read-only review**

Run:

```bash
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<read-only review prompt for origin/main..HEAD>"
```

The prompt must include:

```text
Read-only review. Review commits origin/main..HEAD for node: strategy risk audit history readiness source. Requirements: pure strategy risk audit history gate, optional readiness source, legacy 3-source compatibility, strategy-cycle-only 4-source compatibility, strategy-risk-only 4-source compatibility, combined 5-source compatibility, no DB schema/store/persistence/CLI/env changes, local Supabase/Postgres-only durable data, no live trading/auth/wallet/private keys/order signing/submission/cancellation/replacement/exchange mutation. Output Critical/Important/Minor and verdict.
```

- [ ] **Step 4: Push if approved**

```bash
git push origin main
```

---

## Deferred Follow-Up Node

Persistence/schema/store compatibility for the new readiness source is intentionally deferred. A later node should decide whether the local readiness table should accept source arrays of length 3, 4, and 5, and whether store filters should support `strategy_risk_audit_history_gate_config_version`. That later node must use a Supabase/Postgres migration only and must preserve all local-only persistence rules.
