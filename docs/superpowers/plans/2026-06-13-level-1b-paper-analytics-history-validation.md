# Level 1B Paper Analytics History Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only analytics history validation layer that summarizes a sequence of `PaperAnalyticsReport` values and reports whether paper evidence is sufficient for later human review, without creating proposals or touching any live-execution surface.

**Architecture:** Create `analytics_history.py` as a pure derived layer over Node 3 `PaperAnalyticsReport` values. It computes deterministic history summaries, validation gate results, trend extrema, and append-only JSONL reports; callers supply already-created report objects and optional paper sample counts. The node does not fetch data, read account state, deserialize external history, create proposals, reconcile exchange accounts, or place/cancel orders.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, JSONL files, existing `polymarket_alpha_lab.analytics` public dataclasses, `pytest`, CodeGraph.

---

## Review And Execution Protocol

1. Submit this plan to Claude Code with model `claude-opus-4-8`, effort `max`, read-only permissions before implementation.
2. Do not implement Level 1B Node 4 until Claude Code returns `Proceed` or `Proceed with fixes` and every Critical/Important finding is resolved.
3. Before the node commit and push, run and record this required gate:
   - `git status --short --branch --untracked-files=all`; explicitly list untracked files or `none`.
   - `.venv/bin/python -m pytest tests/test_analytics_history.py tests/test_analytics_history_scope.py tests/test_init.py -q`.
   - `.venv/bin/python -m pytest tests/test_analytics_history_scope.py -q`.
   - `.venv/bin/python -m pytest -q`.
   - `git diff --check`; after staging, also run `git diff --cached --check`.
   - `codegraph status .`; if stale or out of date, run `codegraph sync .` and then `codegraph status .` again.
   - Claude Code implementation review with `claude-opus-4-8`, `--effort max`, covering the node diff, untracked files, verification output, and the next concrete roadmap step.
4. Do not commit or push the node until all required gate items pass, Claude returns `Proceed` or `Proceed with fixes`, and all Claude Critical/Important findings are resolved.
5. After the node, write a Handoff Summary with repo status, verified commands, uncommitted files, Claude review status, pending commit/push fields, and next step. Report the final commit hash and push result in the assistant final response after push.

Plan review command before any implementation:

```bash
{
  printf '%s\n' 'Review this Level 1B Node 4 implementation plan for polymarket-alpha-lab before implementation.'
  printf '%s\n' 'This is a read-only, self-contained plan review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions or plan text.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; plan is implementable as written.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing required review material, unsafe scope, or plan ambiguity that could cause incorrect implementation.'
  printf '%s\n' 'Review specifically: scope boundaries, forbidden surfaces, target files, TDD steps, validation-gate semantics, CodeGraph usage, implementation review self-containment, untracked-file handling, and Critical/Important findings resolution before implementation/commit/push.'
  printf '%s\n' 'Finish with exactly one verdict line: Verdict: Proceed | Proceed with fixes | Blocked.'
  printf '%s\n' ''
  printf '%s\n' 'Repository instructions:'
  cat AGENTS.md
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'Pytest/project configuration:'
  cat pyproject.toml
  printf '%s\n' ''
  printf '%s\n' 'Current roadmap:'
  cat docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md
  printf '%s\n' ''
  printf '%s\n' 'Validation gates:'
  cat docs/research/validation-gates.md
  printf '%s\n' ''
  printf '%s\n' 'Node 3 handoff and current plan:'
  cat docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-risk-exposure.md
  printf '%s\n' ''
  printf '%s\n' 'Node 4 plan:'
  cat docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-history-validation.md
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted plan-review terminal state: a fresh Claude review response that explicitly reports zero Critical findings, zero Important findings, and a verdict of `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count, ambiguous verdict, unsafe scope, or missing review material is treated as `Blocked`. After fixing any Critical or Important plan-review finding, rerun the same self-contained Claude plan-review prompt and do not implement until the rerun reaches an accepted terminal state.

Level 1B Node 4 must not add:

- account authentication
- private-key handling
- live trading
- automated order placement
- order cancellation
- user WebSocket
- REST heartbeat
- trading SDK
- trade proposal generation
- human approval workflow
- broker abstraction
- order lifecycle manager
- exchange account position reconciliation
- external historical loaders
- market/order-book/account data downloaders
- resolution settlement
- scraping, crawling, browser automation, CAPTCHA, anti-bot, or website bypass logic
- compliance, legal, jurisdiction, geofence, or geographic-access analysis
- CLI commands
- dashboards or UI

## Level 1B Node 4 Scope

This node adds only derived paper analytics history validation:

- point-in-time history summary from a sequence of `PaperAnalyticsReport` values
- validation-gate result rows for data integrity, sample size, execution-cost reality, and risk/drawdown evidence
- explicit incomplete result for forecast/edge-quality evidence that is not yet represented in paper artifacts
- trend extrema for executable NAV, drawdown, liquidity shortfall, no-exit-depth cost basis, midpoint NAV gap, market concentration, risk-tag concentration, and breach counts
- deterministic history status: `insufficient_evidence`, `paper_review_ready`, `blocked_by_risk`, or `incomplete_data`
- append-only JSONL persistence for history reports
- package-root exports and README status/API text

This node intentionally defers:

- reading local analytics JSONL back into `PaperAnalyticsReport` objects
- resolved-outcome quality, calibration, or Brier-score analytics
- edge decay and holding-period analytics
- proposal generation or human-approval workflows
- strategy promotion packets
- dashboards or UI
- CLI commands
- exchange reconciliation or live execution readiness claims

`paper_review_ready` is a Node 4 history-artifact status only. It means the paper analytics history report is ready for human review inside Level 1B; it does not mean the strategy has passed every validation gate, does not authorize proposal generation, and is not a promotion signal for live or proposal-mode execution. Forecast/edge-quality evidence is deliberately incomplete in Node 4.

## Target File Structure

- Create: `src/polymarket_alpha_lab/analytics_history.py`
  - Frozen history dataclasses, pure history builder, strict JSONL history log.
- Create: `tests/test_analytics_history.py`
  - TDD tests for history summaries, validation gate rows, trend extrema, edge cases, validation, and JSONL persistence.
- Create: `tests/test_analytics_history_scope.py`
  - Static forbidden-surface tests for Node 4 module and public exports.
- Modify: `src/polymarket_alpha_lab/__init__.py`
  - Export stable Level 1B Node 4 public APIs.
- Modify: `tests/test_init.py`
  - Package-root export contract for analytics history APIs.
- Modify: `README.md`
  - Add Level 1B Node 4 paper-only status, Python API notes, and repository tree entries.
- Modify: `docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-history-validation.md`
  - Update gate results and handoff notes as the node is completed.

## Public API Contract

Create these names:

```python
from polymarket_alpha_lab.analytics_history import (
    PaperAnalyticsHistoryConfig,
    PaperAnalyticsHistoryGateResult,
    PaperAnalyticsHistoryLog,
    PaperAnalyticsHistoryReport,
    PaperAnalyticsHistoryTrend,
    build_paper_analytics_history_report,
)
```

Export all six from `polymarket_alpha_lab.__init__`.

## Analytics History Semantics

`build_paper_analytics_history_report(reports, *, config, generated_at, candidate_observation_count=0, simulated_trade_count=0, exited_trade_count=0)` returns `PaperAnalyticsHistoryReport`.

- `reports` must be an iterable of `PaperAnalyticsReport` values and must reject `str`/`bytes`.
- Empty `reports` is allowed. It returns a report with `report_count == 0`, no trend rows, every gate result set to `incomplete`, and `status == "incomplete_data"`.
- Duplicate `marked_at` values raise `ValueError` to avoid ambiguous history ordering.
- Reports are sorted by `marked_at`; output trend rows follow sorted order.
- Every input report must have `paper_only is True`.
- `generated_at` must be a `datetime`; naive datetimes are treated as UTC.
- Counts must be nonnegative `int` values, not `bool`.
- The builder never fetches data, reads account state, uses a client/transport, downloads history, scrapes websites, places/cancels orders, reconciles accounts, or creates proposals.
- The builder treats Node 3 reports as authoritative. It does not recompute executable NAV from midpoint, best bid, model probability, fair value, or average price.
- The builder computes history-level drawdown from the sorted sequence of `report.performance.exit_nav` values with an executable-NAV high-watermark. It must not rely only on each input report's embedded `drawdown_points`, because those points may cover only the report itself.
- All numeric values in the history report are finite `Decimal` values or `None`.
- Defined ratio-like values remain 4-place `Decimal` values inherited from Node 3 reports or quantized locally to `Decimal("0.0001")`.
- Undefined ratio values return `None`, never `NaN`, `Infinity`, or zero.

Validation gate rows:

- `data_integrity`: `pass` when at least one report exists, all input values are `PaperAnalyticsReport` instances with `paper_only is True`, reports can be sorted by `marked_at`, no duplicate `marked_at` values exist, output trend rows are in sorted order, and exposure provenance exists through Node 3 validated reports; `incomplete` when no reports exist. Invalid inputs raise `ValueError` before a history report is constructed, so the builder does not emit a `data_integrity` `fail` status.
- `sample_size`: `pass` when reports exist and candidate observations, simulated trades, exited trades, and forward window days meet config thresholds; `fail` when reports exist and any sample threshold is missed; `incomplete` when no reports exist.
- `execution_cost_reality`: `pass` when reports exist and worst exit-depth shortfall and no-exit-depth cost-basis ratio are each within their config thresholds; `fail` when either metric breaches; `incomplete` when no reports exist.
- `forecast_edge_quality`: always `incomplete` in Node 4 because resolved-outcome quality and edge-decay artifacts are intentionally deferred.
- `risk_drawdown`: `pass` when reports exist and max drawdown ratio, market concentration, risk-tag concentration, midpoint gap, and breach-count thresholds are within config limits; `fail` when any limit is breached; `incomplete` when no reports exist. Absolute `max_drawdown` is reported for evidence only; the configured drawdown threshold is `max_drawdown_ratio`.

For non-empty histories, an undefined optional ratio (`None`) is treated as no observed breach for that individual threshold. The whole gate is `incomplete` only when there are no reports.

Gate result payload convention: combined gates use `observed_value` and `threshold` as compact review strings containing every checked submetric and threshold; single-metric or simple gates may use `Decimal`, `int`, `str`, or `None`. Floats are never accepted in `observed_value` or `threshold`.

Allowed gate names are exactly:

1. `data_integrity`
2. `sample_size`
3. `execution_cost_reality`
4. `forecast_edge_quality`
5. `risk_drawdown`

Final status:

- `incomplete_data`: no reports or `data_integrity` is incomplete. Invalid `generated_at` values raise `ValueError` instead of producing a report.
- `blocked_by_risk`: risk/drawdown or execution-cost gate fails.
- `insufficient_evidence`: sample-size gate fails while risk gates do not fail.
- `paper_review_ready`: data integrity, sample size, execution-cost reality, and risk/drawdown gates pass; forecast/edge quality may still be `incomplete` because it is explicitly deferred and non-blocking in Node 4. This status means the history artifact is ready for human review only, not that the strategy is approved for proposal or live execution.

## Planned Dataclasses

`analytics_history.py` should use frozen dataclasses and direct construction validation:

```python
@dataclass(frozen=True)
class PaperAnalyticsHistoryConfig:
    config_version: str
    min_candidate_observations: int = 200
    min_simulated_trades: int = 50
    min_exited_trades: int = 30
    min_forward_days: int = 28
    max_drawdown_ratio: Decimal = Decimal("0.2000")
    max_market_cost_basis_ratio: Decimal = Decimal("0.5000")
    max_risk_tag_cost_basis_ratio: Decimal = Decimal("0.5000")
    max_no_exit_depth_cost_basis_ratio: Decimal = Decimal("0.1000")
    max_exit_depth_shortfall_ratio: Decimal = Decimal("0.2500")
    max_midpoint_nav_gap_ratio: Decimal = Decimal("0.0500")
    max_breach_count: int = 0


@dataclass(frozen=True)
class PaperAnalyticsHistoryGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None


@dataclass(frozen=True)
class PaperAnalyticsHistoryTrend:
    marked_at: datetime
    exit_nav: Decimal
    total_exit_pnl: Decimal
    drawdown: Decimal
    drawdown_ratio: Decimal | None
    exit_depth_shortfall_ratio: Decimal | None
    no_exit_depth_cost_basis_ratio: Decimal | None
    midpoint_nav_gap_ratio: Decimal | None
    breach_count: int


@dataclass(frozen=True)
class PaperAnalyticsHistoryReport:
    generated_at: datetime
    config_version: str
    first_marked_at: datetime | None
    last_marked_at: datetime | None
    report_count: int
    candidate_observation_count: int
    simulated_trade_count: int
    exited_trade_count: int
    forward_window_days: int
    unique_market_count: int
    unique_strategy_count: int
    unique_risk_tag_count: int
    latest_exit_nav: Decimal | None
    latest_total_exit_pnl: Decimal | None
    max_drawdown: Decimal | None
    max_drawdown_ratio: Decimal | None
    worst_exit_depth_shortfall_ratio: Decimal | None
    worst_no_exit_depth_cost_basis_ratio: Decimal | None
    worst_midpoint_nav_gap_ratio: Decimal | None
    largest_market_cost_basis_ratio: Decimal | None
    largest_risk_tag_cost_basis_ratio: Decimal | None
    max_breach_count: int
    status: str
    gate_results: tuple[PaperAnalyticsHistoryGateResult, ...]
    trends: tuple[PaperAnalyticsHistoryTrend, ...]
    paper_only: bool = True


@dataclass(frozen=True)
class PaperAnalyticsHistoryLog:
    path: Path | str
```

`PaperAnalyticsHistoryLog` exposes one public method:

```python
append(self, report: PaperAnalyticsHistoryReport) -> None
```

Allowed gate result statuses:

- `pass`
- `fail`
- `incomplete`

Allowed history report statuses:

- `incomplete_data`
- `insufficient_evidence`
- `blocked_by_risk`
- `paper_review_ready`

Direct dataclass construction must validate every public enum-like string:

- `PaperAnalyticsHistoryGateResult.gate_name` must be one of the five allowed gate names.
- `PaperAnalyticsHistoryGateResult.status` must be one of `pass`, `fail`, or `incomplete`.
- `PaperAnalyticsHistoryReport.status` must be one of `incomplete_data`, `insufficient_evidence`, `blocked_by_risk`, or `paper_review_ready`.

## Part 0: Existing Contract Check

**Goal:** Reconfirm current Level 1B Node 3 analytics contracts before implementing history validation.

**Files:**

- Inspect: `src/polymarket_alpha_lab/analytics.py`
- Inspect: `tests/test_analytics.py`
- Inspect: `tests/test_analytics_scope.py`
- Inspect: `src/polymarket_alpha_lab/__init__.py`
- Inspect: `tests/test_init.py`
- Inspect: `README.md`
- Inspect: `docs/research/validation-gates.md`
- Inspect: `docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md`

- [ ] **Step 1: Inspect current contracts with CodeGraph**

Run:

```bash
codegraph status .
```

If CodeGraph reports pending changes, stale/out-of-date index state, reindex recommended, or worktree mismatch, run:

```bash
codegraph sync .
codegraph status .
```

Then run:

```bash
codegraph explore "PaperAnalyticsReport PaperPerformanceSummary PaperPositionExposure PaperAnalyticsBucket PaperDrawdownPoint PaperAnalyticsBreach PaperAnalyticsLog package exports"
codegraph node src/polymarket_alpha_lab/analytics.py
codegraph node src/polymarket_alpha_lab/__init__.py
codegraph node tests/test_analytics.py
codegraph node tests/test_analytics_scope.py
codegraph node tests/test_init.py
```

Then verify the planned test-helper import is available under the current `pyproject.toml` pytest configuration:

```bash
.venv/bin/python -c "from tests.test_analytics import two_position_report; print(two_position_report.__name__)"
```

Then verify the planned `dataclasses.replace()` helper pattern survives Node 3 direct construction validation:

```bash
.venv/bin/python - <<'PY'
from dataclasses import replace
from decimal import Decimal
from tests.test_analytics import two_position_report

_portfolio, _snapshot, report = two_position_report()
performance = replace(
    report.performance,
    exit_nav=Decimal("9500"),
    exit_return_ratio=Decimal("-0.0500"),
)
shifted = replace(report, performance=performance)
print(shifted.performance.exit_nav)
print(shifted.performance.exit_return_ratio)
PY
```

Expected: confirm Node 3 report dataclasses are frozen, paper-only, strict about `Decimal`, and carry executable NAV, drawdown, bucket, breach, and provenance fields needed for history summaries. The helper import prints `two_position_report`; the replace probe prints `9500` and `-0.0500`. If these contracts, the helper import, or the replace probe differ, update this plan before writing implementation tests.

## Part 1: Static Paper-Only Boundary Tests

**Goal:** Lock Node 4 scope before analytics history implementation.

**Files:**

- Create: `tests/test_analytics_history_scope.py`
- Production target created in Part 4: `src/polymarket_alpha_lab/analytics_history.py`

- [ ] **Step 1: Write failing forbidden-surface tests**

Create `tests/test_analytics_history_scope.py` with:

```python
import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HISTORY_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "analytics_history.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"


EXPECTED_HISTORY_EXPORTS = {
    "PaperAnalyticsHistoryConfig",
    "PaperAnalyticsHistoryGateResult",
    "PaperAnalyticsHistoryLog",
    "PaperAnalyticsHistoryReport",
    "PaperAnalyticsHistoryTrend",
    "build_paper_analytics_history_report",
}

ALLOWED_IMPORT_PREFIXES = {
    "json",
    "collections",
    "collections.abc",
    "contextlib",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
    "polymarket_alpha_lab.analytics",
}

FORBIDDEN_IMPORT_PREFIXES = {
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.normalize",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.rejections",
    "polymarket_alpha_lab.research",
    "polymarket_alpha_lab.risk",
    "urllib",
    "urllib3",
    "http",
    "socket",
    "ssl",
    "websocket",
    "websockets",
    "requests",
    "httpx",
    "aiohttp",
    "importlib",
    "runpy",
    "subprocess",
    "py_clob_client",
    "clob_client",
    "web3",
    "eth_account",
    "eth_keys",
    "eth_utils",
    "selenium",
    "playwright",
    "bs4",
    "scrapy",
    "requests_html",
    "mechanize",
    "cloudscraper",
    "curl_cffi",
    "csv",
    "sqlite3",
    "pandas",
    "polars",
    "duckdb",
    "os",
}

FORBIDDEN_NAME_FRAGMENTS = (
    "privatekey",
    "privkey",
    "apikey",
    "secret",
    "credential",
    "password",
    "mnemonic",
    "seedphrase",
    "auth",
    "authentication",
    "bearer",
    "jwt",
    "wallet",
    "signer",
    "signature",
    "signedorder",
    "signorder",
    "signmessage",
    "signtransaction",
    "placeorder",
    "createorder",
    "cancelorder",
    "submitorder",
    "sendorder",
    "orderlifecycle",
    "ordermanager",
    "orderrouter",
    "executiondecision",
    "liveexecution",
    "client",
    "transport",
    "fetch",
    "request",
    "response",
    "session",
    "urlopen",
    "getjson",
    "websocket",
    "heartbeat",
    "proposal",
    "tradeproposal",
    "approval",
    "broker",
    "reconciler",
    "reconciliation",
    "exchangeaccount",
    "accountstate",
    "accountposition",
    "accountbalance",
    "compliance",
    "legal",
    "jurisdiction",
    "geofence",
    "geographic",
    "geoblock",
    "kyc",
    "aml",
    "sanction",
    "simulateorderbookfill",
    "clobclient",
    "tradesdk",
    "settlement",
    "settle",
    "resolvedoutcome",
    "brier",
    "calibration",
    "edgedecay",
    "holdingperiod",
    "promotionpacket",
    "strategypromotion",
    "dashboard",
    "externalhistory",
    "historicalloader",
    "pricehistoryapi",
    "backfill",
    "download",
    "scrape",
    "crawler",
    "captcha",
    "antibot",
    "bypass",
    "browserautomation",
)

FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS = (
    "broker",
    "proposal",
    "tradeproposal",
    "execution",
    "credential",
    "wallet",
    "reconciliation",
    "compliance",
    "auth",
    "privatekey",
    "apikey",
    "signer",
    "signature",
    "placeorder",
    "createorder",
    "cancelorder",
    "submitorder",
    "signedorder",
    "orderlifecycle",
    "ordermanager",
    "orderrouter",
    "client",
    "transport",
    "fetch",
    "request",
    "session",
    "websocket",
    "heartbeat",
    "settlement",
    "resolvedoutcome",
    "brier",
    "calibration",
    "dashboard",
    "legal",
    "jurisdiction",
    "geofence",
    "geographic",
)


def parse_history():
    return ast.parse(HISTORY_PATH.read_text(encoding="utf-8"))


def normalize_identifier(value):
    return "".join(character for character in value.lower() if character.isalnum())


def imported_modules(tree):
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
            modules.extend(alias.asname for alias in node.names if alias.asname)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
            modules.extend(alias.asname for alias in node.names if alias.asname)
    return modules


def module_exports(tree):
    assigned_exports = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def test_history_module_imports_only_allowed_dependencies():
    tree = parse_history()
    for module_name in imported_modules(tree):
        assert any(
            module_name == allowed or module_name.startswith(f"{allowed}.")
            for allowed in ALLOWED_IMPORT_PREFIXES
        ), module_name


def test_history_module_does_not_import_forbidden_surfaces():
    tree = parse_history()
    for module_name in imported_modules(tree):
        assert not any(
            module_name == forbidden or module_name.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_history_module_does_not_define_forbidden_names():
    tree = parse_history()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.add(node.arg)

    lowered = {normalize_identifier(name) for name in names}
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(fragment in name for name in lowered), fragment


def test_history_public_exports_are_paper_history_only():
    tree = parse_history()
    assigned_exports = module_exports(tree)
    assert set(assigned_exports) == EXPECTED_HISTORY_EXPORTS
    for name in assigned_exports:
        assert name.startswith("PaperAnalyticsHistory") or name.startswith(
            "build_paper_analytics_history"
        )
        normalized_name = normalize_identifier(name)
        assert not any(
            fragment in normalized_name for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
        )


def test_package_root_exports_do_not_leak_forbidden_history_surfaces():
    tree = ast.parse(PACKAGE_ROOT_PATH.read_text(encoding="utf-8"))
    assigned_exports = module_exports(tree)
    for name in assigned_exports:
        normalized_name = normalize_identifier(name)
        assert not any(
            fragment in normalized_name for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
        )
```

- [ ] **Step 2: Run scope tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_analytics_history_scope.py -q
```

Expected: fail because `src/polymarket_alpha_lab/analytics_history.py` does not exist.

## Part 2: Analytics History Behavior Tests

**Goal:** Define history summaries, validation gates, status classification, edge cases, and JSONL behavior.

**Files:**

- Create: `tests/test_analytics_history.py`
- Production target created in Part 4: `src/polymarket_alpha_lab/analytics_history.py`

- [ ] **Step 1: Write failing analytics history tests**

Create tests that import existing Node 3 fixtures and public APIs:

```python
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.analytics import PaperAnalyticsReport
from polymarket_alpha_lab.analytics_history import (
    PaperAnalyticsHistoryConfig,
    PaperAnalyticsHistoryGateResult,
    PaperAnalyticsHistoryLog,
    build_paper_analytics_history_report,
)
from tests.test_analytics import two_position_report
```

Add a helper:

```python
def shifted_report(report: PaperAnalyticsReport, *, days: int, exit_nav: Decimal | None = None):
    marked_at = report.marked_at + timedelta(days=days)
    performance = report.performance
    if exit_nav is not None:
        performance = replace(
            performance,
            exit_nav=exit_nav,
            exit_return_ratio=((exit_nav - performance.starting_cash) / performance.starting_cash).quantize(
                Decimal("0.0001")
            ),
        )
    return replace(
        report,
        marked_at=marked_at,
        generated_at=report.generated_at + timedelta(days=days),
        performance=performance,
        drawdown_points=tuple(
            replace(point, marked_at=point.marked_at + timedelta(days=days))
            for point in report.drawdown_points
        ),
    )
```

Add tests:

```python
def test_build_paper_analytics_history_report_summarizes_sorted_reports():
    _portfolio, _snapshot, first = two_position_report()
    second = shifted_report(first, days=7)
    third = shifted_report(first, days=35)

    report = build_paper_analytics_history_report(
        [third, first, second],
        config=PaperAnalyticsHistoryConfig(
            config_version="node4-test",
            max_exit_depth_shortfall_ratio=Decimal("0.5000"),
            max_breach_count=4,
        ),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        candidate_observation_count=250,
        simulated_trade_count=55,
        exited_trade_count=31,
    )

    assert report.generated_at == datetime(2026, 7, 20, tzinfo=UTC)
    assert report.config_version == "node4-test"
    assert report.first_marked_at == first.marked_at
    assert report.last_marked_at == third.marked_at
    assert report.report_count == 3
    assert report.candidate_observation_count == 250
    assert report.simulated_trade_count == 55
    assert report.exited_trade_count == 31
    assert report.forward_window_days == 35
    assert report.unique_market_count == 2
    assert report.unique_strategy_count == 2
    assert report.unique_risk_tag_count == 2
    assert report.latest_exit_nav == third.performance.exit_nav
    assert report.latest_total_exit_pnl == third.performance.total_exit_pnl
    assert report.max_drawdown == Decimal("0")
    assert report.max_drawdown_ratio == Decimal("0.0000")
    assert report.worst_exit_depth_shortfall_ratio == Decimal("0.2667")
    assert report.worst_no_exit_depth_cost_basis_ratio == Decimal("0.0000")
    assert report.worst_midpoint_nav_gap_ratio == Decimal("0.0008")
    assert report.largest_market_cost_basis_ratio == Decimal("0.0051")
    assert report.largest_risk_tag_cost_basis_ratio == Decimal("0.0061")
    assert report.max_breach_count == 4
    assert report.status == "paper_review_ready"
    assert [point.marked_at for point in report.trends] == [
        first.marked_at,
        second.marked_at,
        third.marked_at,
    ]
```

```python
def test_build_paper_analytics_history_report_records_gate_results():
    _portfolio, _snapshot, source = two_position_report()

    report = build_paper_analytics_history_report(
        [source],
        config=PaperAnalyticsHistoryConfig(
            config_version="node4-test",
            max_exit_depth_shortfall_ratio=Decimal("0.1000"),
            max_breach_count=4,
        ),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        candidate_observation_count=10,
        simulated_trade_count=2,
        exited_trade_count=1,
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["data_integrity"].status == "pass"
    assert gates["sample_size"].status == "fail"
    assert gates["execution_cost_reality"].status == "fail"
    assert gates["forecast_edge_quality"].status == "incomplete"
    assert gates["risk_drawdown"].status == "pass"
    assert report.status == "blocked_by_risk"
```

```python
def test_build_paper_analytics_history_report_marks_insufficient_evidence_when_only_sample_fails():
    _portfolio, _snapshot, source = two_position_report()

    report = build_paper_analytics_history_report(
        [source],
        config=PaperAnalyticsHistoryConfig(
            config_version="node4-test",
            max_exit_depth_shortfall_ratio=Decimal("0.5000"),
            max_breach_count=4,
        ),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        candidate_observation_count=10,
        simulated_trade_count=2,
        exited_trade_count=1,
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["sample_size"].status == "fail"
    assert gates["execution_cost_reality"].status == "pass"
    assert gates["risk_drawdown"].status == "pass"
    assert report.status == "insufficient_evidence"
```

```python
def test_build_paper_analytics_history_report_computes_sequence_drawdown_from_exit_nav():
    _portfolio, _snapshot, source = two_position_report()
    first = shifted_report(source, days=0, exit_nav=Decimal("10000"))
    second = shifted_report(source, days=7, exit_nav=Decimal("9500"))
    third = shifted_report(source, days=14, exit_nav=Decimal("9900"))

    report = build_paper_analytics_history_report(
        [third, first, second],
        config=PaperAnalyticsHistoryConfig(
            config_version="node4-test",
            max_drawdown_ratio=Decimal("0.0100"),
            max_exit_depth_shortfall_ratio=Decimal("0.5000"),
            max_breach_count=4,
        ),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        candidate_observation_count=250,
        simulated_trade_count=55,
        exited_trade_count=31,
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert report.trends[0].drawdown == Decimal("0")
    assert report.trends[1].drawdown == Decimal("500")
    assert report.trends[1].drawdown_ratio == Decimal("0.0500")
    assert report.trends[2].drawdown == Decimal("100")
    assert report.max_drawdown == Decimal("500")
    assert report.max_drawdown_ratio == Decimal("0.0500")
    assert gates["risk_drawdown"].status == "fail"
    assert report.status == "blocked_by_risk"
```

```python
def test_build_paper_analytics_history_report_handles_empty_input():
    report = build_paper_analytics_history_report(
        [],
        config=PaperAnalyticsHistoryConfig(config_version="node4-test"),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
    )

    assert report.report_count == 0
    assert report.first_marked_at is None
    assert report.last_marked_at is None
    assert report.forward_window_days == 0
    assert report.latest_exit_nav is None
    assert report.trends == ()
    assert report.status == "incomplete_data"
    assert {gate.status for gate in report.gate_results} == {"incomplete"}
```

```python
def test_build_paper_analytics_history_report_rejects_duplicate_marked_at():
    _portfolio, _snapshot, source = two_position_report()

    with pytest.raises(ValueError, match="duplicate.*marked_at"):
        build_paper_analytics_history_report(
            [source, source],
            config=PaperAnalyticsHistoryConfig(config_version="node4-test"),
            generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        )
```

```python
def test_build_paper_analytics_history_report_rejects_bad_public_inputs():
    _portfolio, _snapshot, source = two_position_report()
    config = PaperAnalyticsHistoryConfig(config_version="node4-test")

    with pytest.raises(ValueError, match="reports"):
        build_paper_analytics_history_report(
            "not-reports",
            config=config,
            generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="candidate_observation_count"):
        build_paper_analytics_history_report(
            [source],
            config=config,
            generated_at=datetime(2026, 7, 20, tzinfo=UTC),
            candidate_observation_count=True,
        )
    with pytest.raises(ValueError, match="PaperAnalyticsReport"):
        build_paper_analytics_history_report(
            [object()],
            config=config,
            generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_analytics_history_report(
            [source],
            config=object(),
            generated_at=datetime(2026, 7, 20, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_analytics_history_report(
            [source],
            config=config,
            generated_at=None,
        )
```

```python
def test_analytics_history_config_rejects_non_decimal_thresholds():
    with pytest.raises(ValueError, match="max_drawdown_ratio"):
        PaperAnalyticsHistoryConfig(
            config_version="node4-test",
            max_drawdown_ratio=1,
        )
```

```python
def test_analytics_history_gate_result_rejects_float_values():
    with pytest.raises(ValueError, match="observed_value"):
        PaperAnalyticsHistoryGateResult(
            gate_name="sample_size",
            status="fail",
            message="bad",
            observed_value=1.0,
        )
    with pytest.raises(ValueError, match="threshold"):
        PaperAnalyticsHistoryGateResult(
            gate_name="sample_size",
            status="fail",
            message="bad",
            threshold=1.0,
        )
```

```python
def test_analytics_history_dataclasses_are_frozen():
    _portfolio, _snapshot, source = two_position_report()
    report = build_paper_analytics_history_report(
        [source],
        config=PaperAnalyticsHistoryConfig(config_version="node4-test"),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
    )

    with pytest.raises(FrozenInstanceError):
        report.report_count = 0
    with pytest.raises(FrozenInstanceError):
        report.trends[0].breach_count = 0
```

```python
def test_paper_analytics_history_log_appends_jsonl_report(tmp_path):
    _portfolio, _snapshot, source = two_position_report()
    report = build_paper_analytics_history_report(
        [source],
        config=PaperAnalyticsHistoryConfig(config_version="node4-test"),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
    )
    log = PaperAnalyticsHistoryLog(path=tmp_path / "history.jsonl")

    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"candidate_observation_count"')
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["generated_at"] == "2026-07-20T00:00:00+00:00"
    assert stored["config_version"] == "node4-test"
    assert stored["latest_exit_nav"] == "9989.600"
    assert stored["gate_results"][0]["gate_name"] == "data_integrity"
```

```python
def test_paper_analytics_history_log_appends_without_overwriting_and_creates_parent_dirs(
    tmp_path,
):
    _portfolio, _snapshot, source = two_position_report()
    report = build_paper_analytics_history_report(
        [source],
        config=PaperAnalyticsHistoryConfig(config_version="node4-test"),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
    )
    log = PaperAnalyticsHistoryLog(path=str(tmp_path / "nested" / "history.jsonl"))

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["generated_at"] == "2026-07-20T00:00:00+00:00"
    assert json.loads(lines[1])["generated_at"] == "2026-07-20T00:00:00+00:00"
```

```python
def test_paper_analytics_history_log_rejects_invalid_public_input_before_file_creation(
    tmp_path,
):
    path = tmp_path / "history.jsonl"
    log = PaperAnalyticsHistoryLog(path=path)

    with pytest.raises(ValueError, match="PaperAnalyticsHistoryReport"):
        log.append(object())

    assert not path.exists()
```

```python
def test_paper_analytics_history_log_preserves_existing_file_when_serialization_fails(
    tmp_path,
):
    _portfolio, _snapshot, source = two_position_report()
    report = build_paper_analytics_history_report(
        [source],
        config=PaperAnalyticsHistoryConfig(config_version="node4-test"),
        generated_at=datetime(2026, 7, 20, tzinfo=UTC),
    )
    object.__setattr__(report.trends[0], "exit_nav", Decimal("NaN"))
    path = tmp_path / "history.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = PaperAnalyticsHistoryLog(path=path)

    with pytest.raises(ValueError, match="finite|JSON|serializable"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'
```

- [ ] **Step 2: Run behavior tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_analytics_history.py -q
```

Expected: fail because `polymarket_alpha_lab.analytics_history` does not exist.

## Part 3: Analytics History Implementation

**Goal:** Implement frozen analytics history dataclasses, history builder, validation gate rows, Decimal helpers, and JSONL persistence.

**Files:**

- Create: `src/polymarket_alpha_lab/analytics_history.py`

- [ ] **Step 1: Implement `analytics_history.py`**

Implementation requirements:

- Define `__all__` with the six public API names.
- Import only standard library modules and Node 3 analytics classes:

```python
import json
from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from pathlib import Path
from typing import Any, Iterator

from polymarket_alpha_lab.analytics import (
    PaperAnalyticsBucket,
    PaperAnalyticsReport,
)
```

- Do not import `positions`, `journal`, `research`, `risk`, `api`, `archive`, `cli`, network/browser/dataframe/db modules, or `os`.
- Use `RATIO_QUANTUM = Decimal("0.0001")`.
- Implement local Decimal helpers and strict validators, adapted from Node 3, rather than importing private helpers.
- Reject `float`, `int`, `str`, `bool`, and `None` for required `Decimal` fields.
- Reject finite and non-finite floats during JSON-ready validation.
- Validate direct dataclass construction through `__post_init__()` methods.
- `max_breach_count=0` is strict: a non-empty history with any report breach fails the `risk_drawdown` gate unless the caller raises the threshold.
- `PaperAnalyticsHistoryGateResult` must reject float `observed_value` and float `threshold` values.
- Build sorted trends from report `marked_at`.
- Calculate `forward_window_days` as `(last_marked_at.date() - first_marked_at.date()).days` when at least one report exists; otherwise `0`.
- Calculate unique market, strategy, and risk-tag counts from report position exposures:
  - `unique_market_count`: count unique `position_exposure.market_slug` values across all reports.
  - `unique_strategy_count`: count unique `position_exposure.strategy_type` values across all reports.
  - `unique_risk_tag_count`: flatten every `position_exposure.risk_tags` tuple across all reports, then count unique tag strings.
- Calculate concentration extrema from report buckets:
  - `largest_market_cost_basis_ratio`: max `market_slug` bucket `cost_basis_ratio_to_starting_cash`.
  - `largest_risk_tag_cost_basis_ratio`: max `risk_tag` bucket `cost_basis_ratio_to_starting_cash`.
- Calculate drawdown extrema from the sorted sequence of `report.performance.exit_nav` values:
  - Maintain a history-level high-watermark NAV as reports are processed in `marked_at` order.
  - Each trend row's `drawdown` equals `history_high_watermark_nav - report.performance.exit_nav`.
  - Each trend row's `drawdown_ratio` equals `drawdown / history_high_watermark_nav`, or `None` when the high watermark is zero.
  - `max_drawdown`: max history-level trend drawdown.
  - `max_drawdown_ratio`: max non-`None` history-level trend drawdown ratio.
  - Do not use each report's embedded `drawdown_points` as the sole source of history drawdown; Node 3 reports may contain only one point when built without prior snapshots.
- Build each `PaperAnalyticsHistoryTrend` row with these exact field mappings:
  - `marked_at`: `report.marked_at`.
  - `exit_nav`: `report.performance.exit_nav`.
  - `total_exit_pnl`: `report.performance.total_exit_pnl`.
  - `drawdown`: history-level high-watermark calculation above.
  - `drawdown_ratio`: history-level high-watermark ratio above.
  - `exit_depth_shortfall_ratio`: `report.exit_depth_shortfall_ratio`.
  - `no_exit_depth_cost_basis_ratio`: `report.no_exit_depth_cost_basis_ratio`.
  - `midpoint_nav_gap_ratio`: `report.performance.midpoint_nav_gap_ratio`.
  - `breach_count`: `len(report.breaches)`.
- Calculate liquidity extrema:
  - `worst_exit_depth_shortfall_ratio`: max non-`None` report `exit_depth_shortfall_ratio`.
  - `worst_no_exit_depth_cost_basis_ratio`: max non-`None` report `no_exit_depth_cost_basis_ratio`.
  - `worst_midpoint_nav_gap_ratio`: max absolute non-`None` `performance.midpoint_nav_gap_ratio`; use `abs()` when comparing magnitude and store the absolute value.
- For any extrema derived from an optional ratio, when reports exist but every sampled value is `None`, the extrema field is `None`. When no reports exist, extrema fields are `None`.
- Calculate `max_breach_count` as the largest `len(report.breaches)` across input reports; for empty history, it is `0`.
- Build exactly five gate results in this order:
  1. `data_integrity`
  2. `sample_size`
  3. `execution_cost_reality`
  4. `forecast_edge_quality`
  5. `risk_drawdown`
- Derive final status from gate results in this order:
  1. `incomplete_data` if no reports or `data_integrity` is incomplete.
  2. `blocked_by_risk` if `execution_cost_reality` or `risk_drawdown` is fail.
  3. `insufficient_evidence` if `sample_size` is fail.
  4. `paper_review_ready` otherwise; this means history-artifact review readiness only, not proposal/live promotion.
- Implement `PaperAnalyticsHistoryLog.append(report)` with validation-before-open JSONL behavior matching `PaperAnalyticsLog`.

- [ ] **Step 2: Run analytics history and scope tests to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_analytics_history.py tests/test_analytics_history_scope.py -q
```

Expected: analytics history and scope tests pass.

## Part 4: Public Exports And README

**Goal:** Export Node 4 APIs and document the new paper-only status.

**Files:**

- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Modify: `README.md`

- [ ] **Step 1: Add failing package-root export test**

Modify `tests/test_init.py`:

```python
from polymarket_alpha_lab.analytics_history import (
    PaperAnalyticsHistoryConfig,
    PaperAnalyticsHistoryGateResult,
    PaperAnalyticsHistoryLog,
    PaperAnalyticsHistoryReport,
    PaperAnalyticsHistoryTrend,
    build_paper_analytics_history_report,
)
```

Add:

```python
def test_level_1b_node_4_public_api_exports():
    expected_exports = {
        "PaperAnalyticsHistoryConfig",
        "PaperAnalyticsHistoryGateResult",
        "PaperAnalyticsHistoryLog",
        "PaperAnalyticsHistoryReport",
        "PaperAnalyticsHistoryTrend",
        "build_paper_analytics_history_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperAnalyticsHistoryConfig is PaperAnalyticsHistoryConfig
    assert lab.PaperAnalyticsHistoryGateResult is PaperAnalyticsHistoryGateResult
    assert lab.PaperAnalyticsHistoryLog is PaperAnalyticsHistoryLog
    assert lab.PaperAnalyticsHistoryReport is PaperAnalyticsHistoryReport
    assert lab.PaperAnalyticsHistoryTrend is PaperAnalyticsHistoryTrend
    assert lab.build_paper_analytics_history_report is build_paper_analytics_history_report
```

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py -q
```

Expected: fail because package root does not export Node 4 names.

- [ ] **Step 2: Export analytics history APIs from package root**

Modify `src/polymarket_alpha_lab/__init__.py`:

```python
from polymarket_alpha_lab.analytics_history import (
    PaperAnalyticsHistoryConfig,
    PaperAnalyticsHistoryGateResult,
    PaperAnalyticsHistoryLog,
    PaperAnalyticsHistoryReport,
    PaperAnalyticsHistoryTrend,
    build_paper_analytics_history_report,
)
```

Add the six names to `__all__`, preserving every existing export.

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py -q
```

Expected: pass.

- [ ] **Step 3: Update README**

Modify `README.md`:

1. Update the Phase 1 Scope sentence to include paper-only analytics history validation.
2. Add after Level 1B Node 3 Python API:

```markdown
## Level 1B Node 4 Status

Level 1B Node 4 adds paper-only analytics history validation over existing `PaperAnalyticsReport` values, including validation-gate summaries, trend extrema, and evidence-readiness status for later human review. Its `paper_review_ready` status means the history artifact is ready for manual review only; it is not a proposal-generation, promotion, or live-execution signal. It does not fetch historical market, order-book, or account data, use external loaders, scrape websites, authenticate, handle private keys, place or cancel orders, open user WebSockets, run heartbeat logic, use a trading SDK, create trade proposals, reconcile exchange accounts, or perform compliance/legal/geographic analysis.

## Level 1B Node 4 Python API

Node 4 is exposed through Python APIs:

- Configure history thresholds with `PaperAnalyticsHistoryConfig(...)`.
- Build paper analytics history reports with `build_paper_analytics_history_report(reports, config=..., generated_at=...)`, which returns `PaperAnalyticsHistoryReport`.
- Inspect validation rows with `PaperAnalyticsHistoryGateResult` and trend rows with `PaperAnalyticsHistoryTrend`.
- Persist history snapshots with `PaperAnalyticsHistoryLog(path).append(report)`.
```

3. Add `2026-06-13-level-1b-paper-analytics-history-validation.md` to the plan tree.
4. Add `analytics_history.py` under `src/polymarket_alpha_lab`.
5. Add `test_analytics_history.py` and `test_analytics_history_scope.py` under `tests`.

- [ ] **Step 4: Run node-specific tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_analytics_history.py tests/test_analytics_history_scope.py tests/test_init.py -q
```

Expected: pass.

## Level 1B Node 4 Completion Criteria

Node 4 is complete only when all of these are true:

- `src/polymarket_alpha_lab/analytics_history.py` exists and is paper-only.
- Static scope tests prove the module does not import or define forbidden auth/execution/network/proposal/reconciliation/scraping/compliance surfaces.
- `build_paper_analytics_history_report(...)` consumes `PaperAnalyticsReport` values only, validates sequence ordering, rejects duplicates, and returns a frozen `PaperAnalyticsHistoryReport`.
- The report uses Node 3 executable NAV, drawdown, bucket, breach, and liquidity fields only; it does not recompute executable values from midpoint/fair value/model probability/best bid.
- Empty input is represented as `incomplete_data`, not as a false pass.
- Sample-size thresholds map to the validation gate counts in `docs/research/validation-gates.md`.
- Risk/drawdown thresholds map to Node 3 drawdown, concentration, liquidity, midpoint-gap, and breach-count evidence.
- Forecast/edge-quality evidence is explicitly `incomplete` because resolved-outcome quality is deferred.
- Undefined ratios return `None`; all defined ratios are finite `Decimal` values.
- JSONL persistence validates and serializes before opening files.
- Package-root exports and README document Node 4 APIs and boundaries.

## Part 5: Final Verification, Claude Review, Handoff, Commit, Push

**Goal:** Verify the node, obtain Claude implementation review, record handoff, and push only after all gates pass.

- [ ] **Step 1: Run fresh verification**

Run:

```bash
git status --short --branch --untracked-files=all
.venv/bin/python -m pytest tests/test_analytics_history.py tests/test_analytics_history_scope.py tests/test_init.py -q
.venv/bin/python -m pytest tests/test_analytics_history_scope.py -q
.venv/bin/python -m pytest -q
git diff --check
codegraph status .
```

If CodeGraph reports pending changes or stale index:

```bash
codegraph sync .
codegraph status .
```

- [ ] **Step 2: Run Claude implementation review**

Run this exact self-contained review command only after Step 1 passes:

```bash
{
  run_review_cmd() {
    stdout_file=$(mktemp)
    stderr_file=$(mktemp)
    printf '\n### COMMAND:'
    printf ' %s' "$@"
    printf '\n'
    "$@" >"$stdout_file" 2>"$stderr_file"
    status=$?
    printf 'exit_code=%s\n' "$status"
    printf '%s\n' '--- stdout ---'
    cat "$stdout_file"
    printf '%s\n' '--- stderr ---'
    cat "$stderr_file"
    rm -f "$stdout_file" "$stderr_file"
  }

  printf '%s\n' 'Review this Level 1B Node 4 implementation for polymarket-alpha-lab before commit.'
  printf '%s\n' 'This is a read-only, self-contained implementation review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, plan, tests, implementation, or verification output.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; implementation is ready to stage, handoff, commit, and push.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing required review material, unsafe scope, failed verification, stale CodeGraph, unexpected tracked or untracked file, staged content before review, or omitted file content.'
  printf '%s\n' 'Review specifically: paper-only scope boundaries, forbidden surfaces, analytics-history drawdown semantics, gate status semantics, Decimal strictness, JSONL validation-before-open behavior, package exports, README updates, tests, CodeGraph status, and final gate readiness.'
  printf '%s\n' 'Finish with exactly one verdict line: Verdict: Proceed | Proceed with fixes | Blocked.'
  printf '%s\n' ''
  printf '%s\n' 'Repository instructions:'
  cat AGENTS.md
  printf '%s\n' ''
  printf '%s\n' 'Roadmap:'
  cat docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md
  printf '%s\n' ''
  printf '%s\n' 'Pytest/project configuration:'
  cat pyproject.toml
  printf '%s\n' ''
  printf '%s\n' 'Validation gates:'
  cat docs/research/validation-gates.md
  printf '%s\n' ''
  printf '%s\n' 'Review payload source line counts:'
  wc -l src/polymarket_alpha_lab/analytics.py docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-history-validation.md README.md src/polymarket_alpha_lab/__init__.py tests/test_init.py 2>&1
  printf '%s\n' 'Expected review caps: analytics.py <= 2000 lines; untracked files <= 5000 lines each.'
  analytics_lines=$(wc -l < src/polymarket_alpha_lab/analytics.py)
  if [ "$analytics_lines" -gt 2000 ]; then
    printf '%s\n' 'BLOCKING REVIEW ISSUE: analytics.py exceeds the review source cap.'
  fi
  printf '%s\n' ''
  printf '%s\n' 'Node 3 analytics source contract:'
  sed -n '1,2000p' src/polymarket_alpha_lab/analytics.py
  printf '%s\n' ''
  printf '%s\n' 'Node 4 plan:'
  cat docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-history-validation.md
  printf '%s\n' ''
  printf '%s\n' 'Next concrete roadmap step:'
  printf '%s\n' 'After Node 4, the next Level 1B planning target is resolved-outcome / forecast-edge quality evidence for paper histories, so forecast_edge_quality can eventually move from incomplete to validated. This is roadmap context only and is not part of the Node 4 implementation.'
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'Cached diff names, expected empty before review:'
  git diff --cached --name-only
  if [ -n "$(git diff --cached --name-only)" ]; then
    printf '%s\n' 'BLOCKING REVIEW ISSUE: staged content is present before implementation review; include or unstage it before review.'
    git diff --cached --stat
    git diff --cached
  else
    printf '%s\n' 'Staged content: none'
  fi
  printf '%s\n' ''
  printf '%s\n' 'Verification output:'
  run_review_cmd git status --short --branch --untracked-files=all
  run_review_cmd .venv/bin/python -m pytest tests/test_analytics_history.py tests/test_analytics_history_scope.py tests/test_init.py -q
  run_review_cmd .venv/bin/python -m pytest tests/test_analytics_history_scope.py -q
  run_review_cmd .venv/bin/python -m pytest -q
  run_review_cmd git diff --check
  run_review_cmd git diff --cached --check
  run_review_cmd codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Tracked diff names:'
  git diff --name-only
  printf '%s\n' 'Expected tracked diff files: README.md, src/polymarket_alpha_lab/__init__.py, tests/test_init.py'
  unexpected_tracked=$(comm -23 <(git diff --name-only | sort) <(printf '%s\n' README.md src/polymarket_alpha_lab/__init__.py tests/test_init.py | sort))
  if [ -n "$unexpected_tracked" ]; then
    printf '%s\n' 'BLOCKING REVIEW ISSUE: unexpected tracked files are modified.'
    printf '%s\n' "$unexpected_tracked"
  else
    printf '%s\n' 'Unexpected tracked files: none'
  fi
  printf '%s\n' ''
  printf '%s\n' 'Tracked diff, all tracked modifications:'
  git diff
  printf '%s\n' ''
  printf '%s\n' 'Untracked file list:'
  git ls-files --others --exclude-standard
  printf '%s\n' ''
  printf '%s\n' 'Expected untracked files: docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-history-validation.md, src/polymarket_alpha_lab/analytics_history.py, tests/test_analytics_history.py, tests/test_analytics_history_scope.py'
  unexpected=$(comm -23 <(git ls-files --others --exclude-standard | sort) <(printf '%s\n' docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-history-validation.md src/polymarket_alpha_lab/analytics_history.py tests/test_analytics_history.py tests/test_analytics_history_scope.py | sort))
  if [ -n "$unexpected" ]; then
    printf '%s\n' 'BLOCKING REVIEW ISSUE: unexpected untracked files are present.'
    printf '%s\n' "$unexpected"
  else
    printf '%s\n' 'Unexpected untracked files: none'
  fi
  for path in docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-history-validation.md src/polymarket_alpha_lab/analytics_history.py tests/test_analytics_history.py tests/test_analytics_history_scope.py; do
    if [ -f "$path" ]; then
      line_count=$(wc -l < "$path")
      printf '\n### Line count for %s\n%s\n' "$path" "$line_count"
      if [ "$line_count" -gt 5000 ]; then
        printf '%s\n' 'BLOCKING REVIEW ISSUE: untracked file exceeds the full-content review cap.'
      fi
      printf '\n### Untracked diff for %s\n' "$path"
      git diff --no-index -- /dev/null "$path" || true
      printf '\n### Full content for %s\n' "$path"
      sed -n '1,5000p' "$path"
    fi
  done
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted result: zero Critical findings, zero Important findings, all required file contents present, every verification command showing `exit_code=0`, CodeGraph up to date, no unexpected tracked or untracked files, no staged content before review, and `Verdict: Proceed` or `Verdict: Proceed with fixes`. Any omitted required material, missing stderr/exit-code evidence, stale CodeGraph result, failed verification, unexpected tracked or untracked file, staged content before review, Critical finding, or Important finding is `Blocked`.

- [ ] **Step 3: Stage implementation files and run cached diff check**

Run:

```bash
git add README.md src/polymarket_alpha_lab/__init__.py src/polymarket_alpha_lab/analytics_history.py tests/test_analytics_history.py tests/test_analytics_history_scope.py tests/test_init.py docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-history-validation.md
git diff --cached --check
```

Expected: cached diff check has no output and exit code 0.

- [ ] **Step 4: Record Handoff Summary, restage the plan, and rerun cached diff check**

Append:

```text
## Handoff Summary

- Repo status: branch, latest commit SHA if known outside the committed file, pushed/not pushed, clean/dirty state.
- Git status output: paste `git status --short --branch --untracked-files=all`.
- Verified commands:
  - `git status --short --branch --untracked-files=all`: pass/fail and notable output.
  - `.venv/bin/python -m pytest tests/test_analytics_history.py tests/test_analytics_history_scope.py tests/test_init.py -q`: pass/fail and test count.
  - `.venv/bin/python -m pytest tests/test_analytics_history_scope.py -q`: pass/fail and test count.
  - `.venv/bin/python -m pytest -q`: pass/fail and test count.
  - `git diff --check`: pass/fail.
  - `codegraph status .`: up to date or stale.
  - `codegraph sync .`: run/not run and result.
  - follow-up `codegraph status .`: up to date or stale.
  - `git diff --cached --check`: pass/fail.
- Untracked files: list or `none`.
- Uncommitted files: list or `none`.
- Data-integrity checks: paper-only scope, forbidden-surface static tests, report sequence validation, duplicate timestamp rejection, executable-NAV-only trend evidence, risk gate status mapping, Decimal-only finite math, undefined ratio handling, JSONL validation-before-open behavior.
- Claude review: model `claude-opus-4-8`, effort `max`, review scope, explicit verdict, unresolved findings.
- Commit/push: commit hash, remote branch, push result. Because this handoff is written before the final commit/push, use `commit hash: pending final commit` and `push result: pending final push` in the committed handoff, then report the actual commit hash and push result in the assistant final response after `git push`.
- Next step: one concrete next action for the next Level 1B node.
```

Because this handoff is written before the final commit and push exist, set the commit hash field to `pending final commit` and the push result field to `pending final push` in the committed handoff. Report the final commit hash and push result in the assistant final response after push.

Then run:

```bash
git add docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-history-validation.md
git diff --cached --check
```

- [ ] **Step 5: Commit and push**

Run:

```bash
git commit -m "feat: add paper analytics history validation"
git push
git status --short --branch --untracked-files=all
```

Expected: commit succeeds, push updates `origin/main`, and final status is exactly `## main...origin/main` with no additional file lines.

## Handoff Summary

- Repo status: branch `main`, latest commit before Node 4 `f9b6518641c887754067513c4faaaaaf54cebbcc`, final Node 4 commit pending, final push pending.
- Git status output before final commit:
  ```text
  ## main...origin/main
  M  README.md
  A  docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-history-validation.md
  M  src/polymarket_alpha_lab/__init__.py
  A  src/polymarket_alpha_lab/analytics_history.py
  A  tests/test_analytics_history.py
  A  tests/test_analytics_history_scope.py
  M  tests/test_init.py
  ```
- Verified commands:
  - `git status --short --branch --untracked-files=all`: pass; showed expected tracked modifications and untracked Node 4 files before staging.
  - `.venv/bin/python -m pytest tests/test_analytics_history.py tests/test_analytics_history_scope.py tests/test_init.py -q`: pass, `26 passed`.
  - `.venv/bin/python -m pytest tests/test_analytics_history_scope.py -q`: pass, `5 passed`.
  - `.venv/bin/python -m pytest -q`: pass, `324 passed`.
  - `git diff --check`: pass.
  - `codegraph status .`: initially reported pending changes after new files.
  - `codegraph sync .`: run, synced 3 changed files.
  - follow-up `codegraph status .`: pass, index up to date.
  - `git diff --cached --check`: pass.
- Untracked files: none after staging.
- Uncommitted files: staged Node 4 files listed in the git status block above.
- Data-integrity checks: paper-only scope locked by static tests; builder consumes only `PaperAnalyticsReport` values, rejects bad report sequences and duplicate timestamps, sorts by `marked_at`, computes history drawdown from executable NAV, maps risk/execution/sample gate statuses deterministically, uses finite `Decimal` math with `None` for undefined ratios, and validates/serializes JSONL before opening files.
- Claude review: model `claude-opus-4-8`, effort `max`; implementation review covered scope, forbidden surfaces, drawdown semantics, gates, Decimal strictness, JSONL behavior, exports, README, tests, CodeGraph, status, diffs, and untracked file content. Verdict: `Proceed with fixes`. Critical: none. Important: none. Minor unresolved: trend midpoint row stores absolute magnitude, arithmetic helpers use direct `Decimal` operations, and scope imports are stricter than the plan example.
- Commit/push: commit hash: pending final commit; remote branch: `origin/main`; push result: pending final push.
- Next step: plan the next Level 1B node for resolved-outcome / forecast-edge quality evidence so `forecast_edge_quality` can eventually move from `incomplete` to validated.
