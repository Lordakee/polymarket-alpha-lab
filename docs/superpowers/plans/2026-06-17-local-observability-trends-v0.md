# Local Observability Trends v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add four pure local trend reducers over already-built Phase 1 report objects without introducing live trading, file IO, clients, ranking, recommendations, trade instructions, or financial advice.

**Architecture:** Implement four independent leaf modules: `strategy_evidence_trend.py`, `outcome_freshness.py`, `nav_risk_trend.py`, and `paper_trade_cost_trend.py`. Each module accepts caller-supplied typed report objects, validates exact types and flags, and returns a frozen report with `paper_only`, `report_only`, and `readonly` set to `True`; no module reads files or constructs clients.

**Tech Stack:** Python frozen dataclasses, `datetime`, `Decimal`, stdlib-only pure reducers, pytest, AST scope tests, CodeGraph-aware repo navigation.

---

## Commit Boundary

These modules are next-node candidates. Do not mix any implementation from this
plan into the Strategy Evidence Snapshot v0 commit unless the user explicitly
selects this node for that commit. This planning node creates only docs.

## Planned File Structure

- Create: `src/polymarket_alpha_lab/strategy_evidence_trend.py`
- Create: `tests/test_strategy_evidence_trend.py`
- Create: `src/polymarket_alpha_lab/outcome_freshness.py`
- Create: `tests/test_outcome_freshness.py`
- Create: `src/polymarket_alpha_lab/nav_risk_trend.py`
- Create: `tests/test_nav_risk_trend.py`
- Create: `src/polymarket_alpha_lab/paper_trade_cost_trend.py`
- Create: `tests/test_paper_trade_cost_trend.py`
- Create: `tests/test_local_observability_trend_scope.py`

Do not modify `README.md`, existing docs, CLI, source modules, package-root
exports, or current Strategy Evidence Snapshot v0 files unless a later selected
node explicitly expands scope.

### Task 1: Strategy Evidence Trend

**Files:**
- Create: `src/polymarket_alpha_lab/strategy_evidence_trend.py`
- Create: `tests/test_strategy_evidence_trend.py`

- [ ] **Step 1: Write failing empty and validation tests**

Create tests covering empty input, exact config validation, exact report-type
validation, rejection of strings/bytes/mappings, and hard flags.

```python
def test_strategy_evidence_trend_empty_report():
    report = build_paper_strategy_evidence_trend_report(
        [],
        config=PaperStrategyEvidenceTrendConfig(config_version="trend-v0"),
        generated_at=GENERATED_AT,
    )

    assert report.snapshot_report_count == 0
    assert report.first_report_generated_at is None
    assert report.latest_report_generated_at is None
    assert report.latest_status is None
    assert report.latest_evidence_gap_names == ()
    assert report.consecutive_local_risk_flags_count == 0
    assert report.consecutive_non_observed_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
```

```python
def test_strategy_evidence_trend_rejects_wrong_inputs():
    config = PaperStrategyEvidenceTrendConfig(config_version="trend-v0")

    with pytest.raises(ValueError, match="list or tuple"):
        build_paper_strategy_evidence_trend_report(
            "not reports",
            config=config,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="PaperStrategyEvidenceSnapshotReport"):
        build_paper_strategy_evidence_trend_report(
            [object()],
            config=config,
            generated_at=GENERATED_AT,
        )
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_evidence_trend.py -q
```

Expected: fail during collection with
`ModuleNotFoundError: No module named 'polymarket_alpha_lab.strategy_evidence_trend'`.

- [ ] **Step 3: Implement minimal pure module**

Implement these public names:

```python
__all__ = (
    "PaperStrategyEvidenceTrendConfig",
    "PaperStrategyEvidenceTrendStatusRow",
    "PaperStrategyEvidenceTrendGapRow",
    "PaperStrategyEvidenceTrendReport",
    "build_paper_strategy_evidence_trend_report",
)
```

Use append order. Status rows cover `SNAPSHOT_STATUSES` from
`strategy_evidence.py`. Gap rows cover `EVIDENCE_GAP_NAMES` from
`strategy_evidence.py`. Each ratio is `None` for zero reports or a
`Decimal` quantized to `Decimal("0.000001")`.

- [ ] **Step 4: Write populated trend tests**

Cover:

- status counts and ratios
- evidence-gap counts and ratios
- latest status from the last supplied report
- latest evidence gaps from the last supplied report
- consecutive `local_risk_flags`
- consecutive non-`local_evidence_observed`
- duplicate timestamps preserving append-order latest

- [ ] **Step 5: Run tests to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_evidence_trend.py -q
```

Expected: pass.

### Task 2: Outcome Freshness

**Files:**
- Create: `src/polymarket_alpha_lab/outcome_freshness.py`
- Create: `tests/test_outcome_freshness.py`

- [ ] **Step 1: Write failing empty and validation tests**

Create tests covering empty input, exact config validation, exact
`OutcomeTrackingReport` validation, hard flags, and no-float ratio behavior.

```python
def test_outcome_freshness_empty_report():
    report = build_outcome_freshness_report(
        (),
        config=OutcomeFreshnessConfig(
            config_version="outcome-freshness-v0",
            stale_after_seconds=3600,
        ),
        generated_at=GENERATED_AT,
    )

    assert report.outcome_report_count == 0
    assert report.status == "empty_outcome_history"
    assert report.latest_report_age_seconds is None
    assert report.latest_resolved_ratio is None
    assert report.latest_pending_ratio is None
    assert report.consecutive_pending_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_outcome_freshness.py -q
```

Expected: fail during collection with
`ModuleNotFoundError: No module named 'polymarket_alpha_lab.outcome_freshness'`.

- [ ] **Step 3: Implement minimal pure module**

Implement these public names:

```python
__all__ = (
    "OutcomeFreshnessConfig",
    "OutcomeFreshnessStatusRow",
    "OutcomeFreshnessReport",
    "build_outcome_freshness_report",
)
```

Use only `OutcomeTrackingReport` inputs. Do not call `check_outcomes`,
`OutcomeTrackingLog.read`, `PaperTradeJournal.read`, clients, network, or paths.

Suggested statuses:

- `empty_outcome_history`
- `latest_outcomes_fresh`
- `latest_outcomes_pending`
- `latest_outcomes_stale`

`latest_report_age_seconds` is computed as
`int((generated_at - latest.generated_at).total_seconds())` and must reject a
negative age. `latest_outcomes_stale` applies when age is greater than
`stale_after_seconds`. `latest_outcomes_pending` applies when the latest report
has pending outcomes and is not stale.

- [ ] **Step 4: Write populated freshness tests**

Cover:

- latest counts copied from the append-order latest report
- resolved and pending ratios as `Decimal("0.000001")` precision
- stale status by configured age
- pending status by latest pending count
- consecutive latest reports with pending outcomes
- duplicate timestamps preserving append-order latest

- [ ] **Step 5: Run tests to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_outcome_freshness.py -q
```

Expected: pass.

### Task 3: NAV Risk Trend

**Files:**
- Create: `src/polymarket_alpha_lab/nav_risk_trend.py`
- Create: `tests/test_nav_risk_trend.py`

- [ ] **Step 1: Write failing empty and validation tests**

Create tests covering empty input, exact config validation, exact
`PaperNavRiskMetricsReport` validation, hard flags, and Decimal-only metrics.

```python
def test_nav_risk_trend_empty_report():
    report = build_paper_nav_risk_trend_report(
        [],
        config=PaperNavRiskTrendConfig(config_version="nav-risk-trend-v0"),
        generated_at=GENERATED_AT,
    )

    assert report.nav_risk_report_count == 0
    assert report.latest_exit_nav is None
    assert report.latest_open_position_count == 0
    assert report.latest_no_exit_depth_count == 0
    assert report.worst_observed_max_drawdown_pct is None
    assert report.consecutive_unexecutable_open_position_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_nav_risk_trend.py -q
```

Expected: fail during collection with
`ModuleNotFoundError: No module named 'polymarket_alpha_lab.nav_risk_trend'`.

- [ ] **Step 3: Implement minimal pure module**

Implement these public names:

```python
__all__ = (
    "PaperNavRiskTrendConfig",
    "PaperNavRiskTrendStatusRow",
    "PaperNavRiskTrendReport",
    "build_paper_nav_risk_trend_report",
)
```

Use only `PaperNavRiskMetricsReport` inputs. Do not call `PaperNavLog.read`,
NAV marking functions, market-data clients, order books, network, or paths.

Suggested statuses:

- `empty_nav_risk_history`
- `latest_nav_risk_observed`
- `latest_nav_has_unexecutable_positions`

An unexecutable open-position count should be derived as
`max(no_exit_depth_count, open_position_count - fully_executable_count - partially_executable_count, 0)`.

- [ ] **Step 4: Write populated trend tests**

Cover:

- latest NAV metrics copied from append-order latest report
- worst observed max drawdown percent across supplied reports
- latest exposure value and share
- consecutive latest reports with unexecutable open positions
- status rows and ratios
- duplicate timestamps preserving append-order latest

- [ ] **Step 5: Run tests to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_nav_risk_trend.py -q
```

Expected: pass.

### Task 4: Paper Trade Cost Trend

**Files:**
- Create: `src/polymarket_alpha_lab/paper_trade_cost_trend.py`
- Create: `tests/test_paper_trade_cost_trend.py`

- [ ] **Step 1: Write failing empty and validation tests**

Create tests covering empty input, exact config validation, exact
`PaperTradeCostAuditReport` validation, hard flags, and no-float Decimal
behavior.

```python
def test_paper_trade_cost_trend_empty_report():
    report = build_paper_trade_cost_trend_report(
        (),
        config=PaperTradeCostTrendConfig(config_version="cost-trend-v0"),
        generated_at=GENERATED_AT,
    )

    assert report.cost_audit_report_count == 0
    assert report.latest_trade_count == 0
    assert report.latest_fill_rate is None
    assert report.worst_observed_mean_edge_cost_drag is None
    assert report.worst_observed_negative_cost_adjusted_edge_count == 0
    assert report.consecutive_negative_cost_adjusted_edge_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_trade_cost_trend.py -q
```

Expected: fail during collection with
`ModuleNotFoundError: No module named 'polymarket_alpha_lab.paper_trade_cost_trend'`.

- [ ] **Step 3: Implement minimal pure module**

Implement these public names:

```python
__all__ = (
    "PaperTradeCostTrendConfig",
    "PaperTradeCostTrendStatusRow",
    "PaperTradeCostTrendReport",
    "build_paper_trade_cost_trend_report",
)
```

Use only `PaperTradeCostAuditReport` inputs. Do not call
`PaperTradeJournal.read`, simulate fills, place paper trades, construct clients,
network, or paths.

Suggested statuses:

- `empty_cost_audit_history`
- `latest_cost_observed`
- `latest_negative_cost_adjusted_edges`

- [ ] **Step 4: Write populated trend tests**

Cover:

- latest metrics copied from append-order latest report
- worst observed mean edge cost drag, ignoring `None`
- worst observed negative cost-adjusted edge count
- consecutive latest reports with negative cost-adjusted edges
- status rows and ratios
- duplicate timestamps preserving append-order latest

- [ ] **Step 5: Run tests to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_trade_cost_trend.py -q
```

Expected: pass.

### Task 5: Scope Tests And Verification

**Files:**
- Create: `tests/test_local_observability_trend_scope.py`

- [ ] **Step 1: Write failing AST import-scope tests**

The test should parse each new module and allow only stdlib imports plus the one
typed report module required by that trend reducer.

Allowed project imports:

- `polymarket_alpha_lab.strategy_evidence` for `strategy_evidence_trend.py`
- `polymarket_alpha_lab.outcome_tracker` for `outcome_freshness.py`
- `polymarket_alpha_lab.nav_risk_metrics` for `nav_risk_trend.py`
- `polymarket_alpha_lab.paper_trade_cost_audit` for `paper_trade_cost_trend.py`

Forbidden import/name fragments:

```python
FORBIDDEN_FRAGMENTS = (
    "api",
    "auth",
    "wallet",
    "private_key",
    "order",
    "client",
    "network",
    "request",
    "http",
    "urllib",
    "path",
    "open",
    "read",
    "write",
    "journal",
    "log",
    "rank",
    "recommend",
    "instruction",
    "advice",
    "trade_instruction",
    "financial_advice",
)
```

- [ ] **Step 2: Run scope tests to verify RED before modules exist**

Run:

```bash
.venv/bin/python -m pytest tests/test_local_observability_trend_scope.py -q
```

Expected: fail because target modules do not exist.

- [ ] **Step 3: Update modules until scope tests pass**

Keep the pure modules free of file IO, clients, network, auth, wallet, order,
ranking, recommendation, trade-instruction, and financial-advice surfaces. Do
not add CLI wiring or package-root exports in this node.

- [ ] **Step 4: Run targeted test suite**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_strategy_evidence_trend.py \
  tests/test_outcome_freshness.py \
  tests/test_nav_risk_trend.py \
  tests/test_paper_trade_cost_trend.py \
  tests/test_local_observability_trend_scope.py \
  -q
```

Expected: pass.

- [ ] **Step 5: Run compile and whitespace checks**

Run:

```bash
.venv/bin/python -m compileall src/polymarket_alpha_lab
git diff --check
```

Expected: compileall succeeds and `git diff --check` prints no whitespace
errors.

- [ ] **Step 6: Final implementation review**

Confirm:

- No existing docs, README, CLI, source behavior, tests, or Strategy Evidence
  Snapshot v0 files were edited unless explicitly selected.
- No pure trend module performs file IO.
- No pure trend module imports or defines client, network, auth, wallet, order,
  ranking, recommendation, trade-instruction, or financial-advice surfaces.
- Every trend report enforces `paper_only is True`, `report_only is True`, and
  `readonly is True`.
- These modules remain separate next-node candidates unless explicitly selected
  for implementation.
