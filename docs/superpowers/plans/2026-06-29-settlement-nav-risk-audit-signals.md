# Settlement NAV Risk Audit Signals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Feed existing paper settlement/NAV overlay risk into strategy audit and readiness signals so autonomous selection can throttle on Polymarket-specific settlement and exit-risk evidence.

**Architecture:** Keep this node pure and backward-compatible. `strategy_risk_audit` gets an optional `PaperNavSettlementRiskOverlayReport` source that adds a seventh gate only when supplied; old six-gate reports remain valid. `strategy_signal_adapter` gets a direct adapter from `PaperNavSettlementRiskOverlayReport` to `PaperStrategyReadinessSignal`. No runner, CLI, database write, broker, wallet, or live order path is added.

**Tech Stack:** Python frozen dataclasses, Decimal-only risk values, existing paper-only/report-only/readonly report contracts, pytest.

## Global Constraints

- Durable project data must use local Supabase/Postgres only.
- This node does not add durable storage, new tables, JSONL/file-backed persistence, SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, or a generic DB abstraction layer.
- Existing JSONL/file-backed journals are legacy compatibility surfaces; do not expand them.
- Phase 1 remains paper-only/read-only for market and trading behavior: no live trading, account auth, wallets, private keys, order signing/submission/cancellation/replacement, or exchange mutation.
- This node does not add a live readiness builder, broker adapter, wallet flow, order flow, or trade execution path.
- This node does not add CLI flags, DSN/table flags, env reads, DB loaders, or persistence paths.
- Review gates are read-only through local opencode using model `zhipuai-coding-plan/glm-5.2` and variant `max`.
- Codex worker subagents must use `gpt-5.5` with reasoning effort `xhigh`; fast mode is forbidden.

---

## Parallel Execution Shape

- **Task 1:** Strategy audit optional settlement/NAV gate. Write scope: `src/polymarket_alpha_lab/strategy_risk_audit.py`, `tests/test_strategy_risk_audit.py`.
- **Task 2:** Readiness signal adapter for settlement/NAV overlay. Write scope: `src/polymarket_alpha_lab/strategy_signal_adapter.py`, `tests/test_strategy_signal_adapter.py`.
- **Task 3:** Docs and package/scope verification only after Tasks 1 and 2 interfaces are known. Write scope: docs/tests only.
- **Task 4:** Final integration verification, CodeGraph sync, opencode review, push.

## File Structure

- Modify `src/polymarket_alpha_lab/strategy_risk_audit.py`: optional `settlement_nav_risk_report` input and optional gate.
- Modify `tests/test_strategy_risk_audit.py`: legacy six-gate compatibility and seven-gate overlay behavior.
- Modify `src/polymarket_alpha_lab/strategy_signal_adapter.py`: adapter from `PaperNavSettlementRiskOverlayReport` to readiness signal.
- Modify `tests/test_strategy_signal_adapter.py`: mapping, ordering, hard-flag, subclass rejection coverage.
- Modify docs only if an existing strategy audit/readiness signal doc already describes supported sources.

---

### Task 1: Optional Settlement NAV Gate In Strategy Audit

**Files:**
- Modify: `src/polymarket_alpha_lab/strategy_risk_audit.py`
- Test: `tests/test_strategy_risk_audit.py`

**Interfaces:**
- Consumes: `polymarket_alpha_lab.paper_nav_settlement_risk_overlay.PaperNavSettlementRiskOverlayReport`
- Produces: optional builder keyword:

```python
def build_paper_strategy_risk_audit_report(
    *,
    performance_summary: PerformanceSummary,
    nav_risk_report: PaperNavRiskMetricsReport,
    outcome_report: OutcomeTrackingReport | None,
    cost_audit_report: PaperTradeCostAuditReport | None,
    config: PaperStrategyRiskAuditConfig,
    generated_at: datetime,
    settlement_nav_risk_report: PaperNavSettlementRiskOverlayReport | None = None,
) -> PaperStrategyRiskAuditReport:
    ...
```

- Preserve legacy direct reports with the old gate order:

```python
GATE_NAMES = (
    "paper_history",
    "settlement_evidence",
    "forecast_quality",
    "cost_discipline",
    "nav_drawdown",
    "open_exposure",
)
```

- Add optional order:

```python
SETTLEMENT_NAV_RISK_GATE_NAME = "settlement_nav_risk"
SETTLEMENT_NAV_RISK_GATE_NAMES = (
    "paper_history",
    "settlement_evidence",
    "forecast_quality",
    "cost_discipline",
    "nav_drawdown",
    "open_exposure",
    "settlement_nav_risk",
)
```

- Status mapping:
  - `settlement_nav_risk_clear` -> `pass`
  - `empty_nav_settlement_risk_overlay` -> `incomplete`
  - `settlement_nav_risk_watch` -> `fail`
  - `settlement_nav_risk_blocked` -> `fail`

- Observed value:
  - `blocked_or_missing_exit_nav_share` when present
  - otherwise `blocked_or_missing_exit_value`
- Threshold: `max_blocked_settlement_exposure_share`

- [ ] **Step 1: Write failing tests**

Add these tests to `tests/test_strategy_risk_audit.py`:

```python
from polymarket_alpha_lab.paper_nav_settlement_risk_overlay import (
    PaperNavSettlementRiskOverlayReport,
    PaperNavSettlementRiskOverlayRow,
)


def _settlement_nav_overlay(**overrides) -> PaperNavSettlementRiskOverlayReport:
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "paper-nav-settlement-risk-overlay-v0",
        "nav_risk_config_version": "nav-risk-metrics-v0",
        "settlement_timing_config_version": "settlement-timing-v0",
        "nav_snapshot_count": 8,
        "first_marked_at": datetime(2026, 6, 1, tzinfo=UTC),
        "last_marked_at": GENERATED_AT,
        "settlement_row_count": 1,
        "exposure_row_count": 1,
        "acceptable_count": 1,
        "watch_count": 0,
        "blocked_count": 0,
        "missing_settlement_count": 0,
        "acceptable_exit_value": Decimal("100.0000"),
        "watch_exit_value": Decimal("0"),
        "blocked_exit_value": Decimal("0"),
        "missing_settlement_exit_value": Decimal("0"),
        "blocked_or_missing_exit_value": Decimal("0"),
        "blocked_or_missing_exit_nav_share": Decimal("0.000000"),
        "max_blocked_settlement_exposure_share": Decimal("0.100000"),
        "status": "settlement_nav_risk_clear",
        "rows": (
            PaperNavSettlementRiskOverlayRow(
                condition_id="condition-0",
                market_slug="market-0",
                token_count=1,
                open_size=Decimal("100.0000"),
                cost_basis=Decimal("100.0000"),
                exit_value=Decimal("100.0000"),
                share_of_exit_nav=Decimal("0.009950"),
                overlay_status="acceptable",
                settlement_timing_status="acceptable",
                timing_cost_per_share=Decimal("0.010000"),
                adjusted_net_probability_edge=Decimal("0.050000"),
                reason_codes=("settlement_timing_clear",),
            ),
        ),
    }
    values.update(overrides)
    return PaperNavSettlementRiskOverlayReport(**values)
```

```python
def test_strategy_risk_audit_keeps_legacy_six_gate_report_without_settlement_nav_overlay():
    report = _report(outcomes=_outcomes(), cost_audit=_cost_audit())

    assert report.status == "audit_ready"
    assert report.gate_count == 6
    assert tuple(gate.gate_name for gate in report.gate_results) == (
        "paper_history",
        "settlement_evidence",
        "forecast_quality",
        "cost_discipline",
        "nav_drawdown",
        "open_exposure",
    )
```

```python
def test_strategy_risk_audit_adds_settlement_nav_risk_gate_when_overlay_supplied():
    report = _report(
        outcomes=_outcomes(),
        cost_audit=_cost_audit(),
        settlement_nav_risk=_settlement_nav_overlay(),
    )

    assert report.status == "audit_ready"
    assert report.gate_count == 7
    gate = report.gate_results[-1]
    assert gate == PaperStrategyRiskAuditGateResult(
        gate_name="settlement_nav_risk",
        status="pass",
        message="Settlement NAV risk overlay is clear.",
        observed_value=Decimal("0.000000"),
        threshold=Decimal("0.100000"),
    )
```

```python
@pytest.mark.parametrize(
    ("overlay_status", "expected_status", "expected_report_status"),
    (
        ("empty_nav_settlement_risk_overlay", "incomplete", "insufficient_evidence"),
        ("settlement_nav_risk_watch", "fail", "blocked_by_risk"),
        ("settlement_nav_risk_blocked", "fail", "blocked_by_risk"),
    ),
)
def test_strategy_risk_audit_maps_settlement_nav_overlay_statuses(
    overlay_status,
    expected_status,
    expected_report_status,
):
    row = PaperNavSettlementRiskOverlayRow(
        condition_id="condition-risky",
        market_slug="market-risky",
        token_count=1,
        open_size=Decimal("100.0000"),
        cost_basis=Decimal("100.0000"),
        exit_value=Decimal("100.0000"),
        share_of_exit_nav=Decimal("0.009950"),
        overlay_status="blocked" if overlay_status == "settlement_nav_risk_blocked" else "watch",
        settlement_timing_status="blocked" if overlay_status == "settlement_nav_risk_blocked" else "watch",
        timing_cost_per_share=Decimal("0.020000"),
        adjusted_net_probability_edge=Decimal("-0.010000"),
        reason_codes=("settlement_timing_risk",),
    )
    overlay = _settlement_nav_overlay(
        acceptable_count=0,
        watch_count=1 if overlay_status == "settlement_nav_risk_watch" else 0,
        blocked_count=1 if overlay_status == "settlement_nav_risk_blocked" else 0,
        acceptable_exit_value=Decimal("0"),
        watch_exit_value=Decimal("100.0000") if overlay_status == "settlement_nav_risk_watch" else Decimal("0"),
        blocked_exit_value=Decimal("100.0000") if overlay_status == "settlement_nav_risk_blocked" else Decimal("0"),
        blocked_or_missing_exit_value=Decimal("100.0000") if overlay_status == "settlement_nav_risk_blocked" else Decimal("0"),
        blocked_or_missing_exit_nav_share=Decimal("0.150000") if overlay_status == "settlement_nav_risk_blocked" else Decimal("0.000000"),
        status=overlay_status,
        rows=() if overlay_status == "empty_nav_settlement_risk_overlay" else (row,),
        exposure_row_count=0 if overlay_status == "empty_nav_settlement_risk_overlay" else 1,
        settlement_row_count=0 if overlay_status == "empty_nav_settlement_risk_overlay" else 1,
    )

    report = _report(
        outcomes=_outcomes(),
        cost_audit=_cost_audit(),
        settlement_nav_risk=overlay,
    )

    assert report.status == expected_report_status
    assert report.gate_results[-1].gate_name == "settlement_nav_risk"
    assert report.gate_results[-1].status == expected_status
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_strategy_risk_audit.py
```

Expected before implementation: failure because `settlement_nav_risk` is not an accepted helper argument and the builder has no `settlement_nav_risk_report` keyword.

- [ ] **Step 3: Implement the minimal reducer change**

Implement:

```python
from polymarket_alpha_lab.paper_nav_settlement_risk_overlay import (
    PaperNavSettlementRiskOverlayReport,
)
```

Add `SETTLEMENT_NAV_RISK_GATE_NAME`, `SETTLEMENT_NAV_RISK_GATE_NAMES`, optional validation in `PaperStrategyRiskAuditReport.__post_init__`, optional builder keyword, input type check, `_require_report_flags("settlement_nav_risk_report", settlement_nav_risk_report)`, append `_build_settlement_nav_risk_gate(settlement_nav_risk_report)` only when supplied, and implement:

```python
def _build_settlement_nav_risk_gate(
    value: PaperNavSettlementRiskOverlayReport,
) -> PaperStrategyRiskAuditGateResult:
    observed_value = (
        value.blocked_or_missing_exit_nav_share
        if value.blocked_or_missing_exit_nav_share is not None
        else value.blocked_or_missing_exit_value
    )
    threshold = value.max_blocked_settlement_exposure_share
    if value.status == "settlement_nav_risk_clear":
        status = "pass"
        message = "Settlement NAV risk overlay is clear."
    elif value.status == "empty_nav_settlement_risk_overlay":
        status = "incomplete"
        message = "Settlement NAV risk overlay has no exposure rows."
    elif value.status in ("settlement_nav_risk_watch", "settlement_nav_risk_blocked"):
        status = "fail"
        message = "Settlement NAV risk overlay requires paper review."
    else:
        raise ValueError("settlement_nav_risk_report status must be known")
    return PaperStrategyRiskAuditGateResult(
        gate_name=SETTLEMENT_NAV_RISK_GATE_NAME,
        status=status,
        message=message,
        observed_value=observed_value,
        threshold=threshold,
    )
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_strategy_risk_audit.py
```

Expected: all tests in `tests/test_strategy_risk_audit.py` pass.

- [ ] **Step 5: Commit**

```bash
git add src/polymarket_alpha_lab/strategy_risk_audit.py tests/test_strategy_risk_audit.py
git commit -m "feat: add settlement nav risk to strategy audit"
```

---

### Task 2: Settlement NAV Overlay Readiness Signals

**Files:**
- Modify: `src/polymarket_alpha_lab/strategy_signal_adapter.py`
- Test: `tests/test_strategy_signal_adapter.py`

**Interfaces:**
- Consumes: `PaperNavSettlementRiskOverlayReport`
- Produces:

```python
def signals_from_nav_settlement_risk_overlay_report(
    report: PaperNavSettlementRiskOverlayReport,
) -> tuple[PaperStrategyReadinessSignal, ...]:
    ...
```

- Signal:
  - `source_name="nav_settlement_risk_overlay"`
  - status mapping:
    - `settlement_nav_risk_clear` -> `pass`
    - `empty_nav_settlement_risk_overlay` -> `watch`
    - `settlement_nav_risk_watch` -> `watch`
    - `settlement_nav_risk_blocked` -> `blocked`
  - observed value: `blocked_or_missing_exit_nav_share` else `blocked_or_missing_exit_value`
  - threshold: `max_blocked_settlement_exposure_share`

- [ ] **Step 1: Write failing adapter tests**

Add imports:

```python
from polymarket_alpha_lab.paper_nav_settlement_risk_overlay import (
    PaperNavSettlementRiskOverlayReport,
    PaperNavSettlementRiskOverlayRow,
)
```

Add a helper `_settlement_nav_overlay_report(status: str)` with the same row construction style as Task 1.

Add:

```python
@pytest.mark.parametrize(
    ("overlay_status", "readiness_status", "severity", "reason_codes", "observed_value"),
    (
        (
            "empty_nav_settlement_risk_overlay",
            "watch",
            50,
            ("nav_settlement_risk_overlay_empty",),
            Decimal("0"),
        ),
        (
            "settlement_nav_risk_clear",
            "pass",
            0,
            ("nav_settlement_risk_overlay_passed",),
            Decimal("0.000000"),
        ),
        (
            "settlement_nav_risk_watch",
            "watch",
            50,
            ("settlement_timing_risk",),
            Decimal("0.000000"),
        ),
        (
            "settlement_nav_risk_blocked",
            "blocked",
            100,
            ("settlement_timing_risk",),
            Decimal("0.150000"),
        ),
    ),
)
def test_adapter_builds_readiness_signals_from_nav_settlement_risk_overlay_reports(
    overlay_status,
    readiness_status,
    severity,
    reason_codes,
    observed_value,
):
    adapter = _adapter_module()
    report = _settlement_nav_overlay_report(overlay_status)

    signals = adapter.signals_from_nav_settlement_risk_overlay_report(report)

    assert signals == (
        PaperStrategyReadinessSignal(
            source_name="nav_settlement_risk_overlay",
            status=readiness_status,
            reason_codes=reason_codes,
            severity=severity,
            observed_value=observed_value,
            threshold=Decimal("0.100000"),
        ),
    )
```

Also extend `test_adapter_builds_signals_in_deterministic_readiness_order`, subclass rejection, tampered hard-flag rejection, and `build_paper_strategy_readiness_signals(report)` dispatch coverage.

- [ ] **Step 2: Run the failing tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_strategy_signal_adapter.py
```

Expected before implementation: missing function/import or unsupported report errors.

- [ ] **Step 3: Implement the adapter**

Import `PaperNavSettlementRiskOverlayReport`; add the type to the builder union and dispatcher; export `signals_from_nav_settlement_risk_overlay_report`.

Implement:

```python
def signals_from_nav_settlement_risk_overlay_report(
    report: PaperNavSettlementRiskOverlayReport,
) -> tuple[PaperStrategyReadinessSignal, ...]:
    if type(report) is not PaperNavSettlementRiskOverlayReport:
        raise ValueError("report must be a PaperNavSettlementRiskOverlayReport")
    _require_report_flags(report)
    status = _map_nav_settlement_risk_overlay_status(report.status)
    return (
        PaperStrategyReadinessSignal(
            source_name="nav_settlement_risk_overlay",
            status=status,
            reason_codes=_nav_settlement_risk_overlay_reason_codes(report, status=status),
            severity=SEVERITY_BY_STATUS[status],
            observed_value=_nav_settlement_risk_overlay_observed_value(report),
            threshold=report.max_blocked_settlement_exposure_share,
        ),
    )
```

Implement helpers:

```python
def _map_nav_settlement_risk_overlay_status(status: str) -> str:
    if status == "empty_nav_settlement_risk_overlay":
        return "watch"
    if status == "settlement_nav_risk_clear":
        return "pass"
    if status == "settlement_nav_risk_watch":
        return "watch"
    if status == "settlement_nav_risk_blocked":
        return "blocked"
    raise ValueError("status must be a known settlement NAV risk overlay status")
```

```python
def _nav_settlement_risk_overlay_reason_codes(
    report: PaperNavSettlementRiskOverlayReport,
    *,
    status: str,
) -> tuple[str, ...]:
    if report.status == "empty_nav_settlement_risk_overlay":
        return ("nav_settlement_risk_overlay_empty",)
    if status == "pass":
        return ("nav_settlement_risk_overlay_passed",)
    row_codes = tuple(
        sorted(
            {
                reason_code
                for row in report.rows
                if row.overlay_status != "acceptable"
                for reason_code in row.reason_codes
            },
        ),
    )
    return row_codes or (f"nav_settlement_risk_overlay_{status}",)
```

```python
def _nav_settlement_risk_overlay_observed_value(
    report: PaperNavSettlementRiskOverlayReport,
) -> Decimal:
    if report.blocked_or_missing_exit_nav_share is not None:
        return report.blocked_or_missing_exit_nav_share
    return report.blocked_or_missing_exit_value
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_strategy_signal_adapter.py
```

Expected: all tests in `tests/test_strategy_signal_adapter.py` pass.

- [ ] **Step 5: Commit**

```bash
git add src/polymarket_alpha_lab/strategy_signal_adapter.py tests/test_strategy_signal_adapter.py
git commit -m "feat: add settlement nav risk readiness signal"
```

---

### Task 3: Docs And Boundary Tests

**Files:**
- Modify existing docs only if they mention strategy audit or readiness signal sources.
- Modify existing docs tests only if they assert supported source names.

**Interfaces:**
- Documents that this node consumes existing paper-only settlement/NAV overlay reports and does not persist or execute anything.

- [ ] **Step 1: Locate docs with CodeGraph or `rg`**

Run:

```bash
rg -n "strategy risk audit|readiness signal|nav_settlement|settlement NAV|settlement_nav" README.md docs tests
```

- [ ] **Step 2: Patch only existing relevant docs**

If `README.md` or `docs/*.md` already lists strategy audit gates or readiness signal sources, add `settlement_nav_risk` / `nav_settlement_risk_overlay` to that existing list. Include these exact boundary phrases near the source description:

```text
paper-only/report-only/readonly
does not add live trading
does not add auth or wallet handling
does not add order submission, cancellation, or replacement
does not add persistence, DB loaders, env reads, or CLI flags
```

- [ ] **Step 3: Run focused docs/scope tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_strategy_risk_audit.py tests/test_strategy_signal_adapter.py
```

Expected: strategy audit and adapter tests pass after documentation edits.

- [ ] **Step 4: Commit if docs changed**

```bash
git add README.md docs tests
git commit -m "docs: document settlement nav risk audit signals"
```

---

### Task 4: Integration Gate, Review, And Push

**Files:**
- No feature files unless fixing findings.

- [ ] **Step 1: Run focused integration tests**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_strategy_risk_audit.py \
  tests/test_strategy_signal_adapter.py \
  tests/test_paper_nav_settlement_risk_overlay.py
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
Read-only review. Review commits origin/main..HEAD for node: settlement NAV risk audit signals. Requirements: optional settlement NAV overlay source in strategy risk audit, legacy six-gate compatibility, readiness signal adapter support, no new persistence/CLI/env/DB loaders, local Supabase/Postgres-only durable data, no live trading/auth/wallet/private keys/order signing/submission/cancellation/replacement/exchange mutation. Output Critical/Important/Minor and verdict.
```

- [ ] **Step 4: Push if approved**

```bash
git push origin main
```

