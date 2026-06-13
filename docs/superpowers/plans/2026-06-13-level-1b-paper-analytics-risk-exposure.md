# Level 1B Paper Analytics Risk Exposure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add paper-only portfolio analytics, exposure concentration, liquidity-risk, and executable-NAV drawdown reports from existing paper portfolio and NAV artifacts.

**Architecture:** Keep analytics as a pure derived layer in `analytics.py`: consume already-built `PaperPortfolio` values and already-created `PaperNavSnapshot` values, join positions to marks by token id, and return frozen report dataclasses. The node does not fetch data, mutate journal/NAV semantics, create proposals, reconcile exchange accounts, or touch execution/auth surfaces.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, JSONL files, existing `PaperPortfolio`, `PaperNavSnapshot`, `PaperPosition`, `PaperPositionMark`, `pytest`, CodeGraph.

---

## Review And Execution Protocol

1. Submit this plan to Claude Code with model `claude-opus-4-8`, effort `max`, read-only permissions before implementation.
2. Do not implement Level 1B Node 3 until Claude Code returns `Proceed` or `Proceed with fixes` and every Critical/Important finding is resolved.
3. Before the node commit and push, run and record this required gate:
   - `git status --short --branch --untracked-files=all`; explicitly list untracked files or `none`.
   - `.venv/bin/python -m pytest tests/test_analytics.py tests/test_analytics_scope.py tests/test_init.py -q`.
   - `.venv/bin/python -m pytest -q`.
   - `git diff --check`; after staging, also run `git diff --cached --check`.
   - `codegraph status .`; if stale or out of date, run `codegraph sync .` and then `codegraph status .` again.
   - A focused boundary check over the Node 3 module, normally `.venv/bin/python -m pytest tests/test_analytics_scope.py -q`.
   - Claude Code implementation review with `claude-opus-4-8`, `--effort max`, covering the node diff, untracked files, verification output, and any next-node plan.
4. Do not commit or push the node until all required gate items pass, Claude returns `Proceed` or `Proceed with fixes`, and all Claude Critical/Important findings are resolved.
5. After the node, write a Handoff Summary with repo status, verified commands, uncommitted files, Claude review status, commit/push result, and next step.

Plan review command before any implementation:

```bash
{
  printf '%s\n' 'Review this Level 1B Node 3 implementation plan for polymarket-alpha-lab before implementation.'
  printf '%s\n' 'This is a read-only, self-contained plan review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions or plan text.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; plan is implementable as written.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing required review material, unsafe scope, or plan ambiguity that could cause incorrect implementation.'
  printf '%s\n' 'Review specifically: scope boundaries, forbidden surfaces, target files, TDD steps, verification gates, CodeGraph usage, implementation review command self-containment, untracked-file handling, and whether Critical/Important findings must be resolved before implementation/commit/push.'
  printf '%s\n' 'Finish with exactly one verdict line: Verdict: Proceed | Proceed with fixes | Blocked.'
  printf '%s\n' ''
  printf '%s\n' 'Repository instructions:'
  cat AGENTS.md
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'Plan:'
  cat docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-risk-exposure.md
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted plan-review terminal state: a fresh Claude review response that explicitly reports zero Critical findings, zero Important findings, and a verdict of `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count, ambiguous verdict, unsafe scope, or missing review material is treated as `Blocked`. After fixing any Critical/Important finding, rerun the same Claude plan-review prompt.

Level 1B Node 3 must not add:

- account authentication
- private-key handling
- live trading
- automated order placement
- order cancellation
- user WebSocket
- REST heartbeat
- trading SDK
- trade proposal generation
- human approval proposal workflow
- broker abstraction
- order lifecycle manager
- exchange account position reconciliation
- external historical loaders
- resolution settlement
- scraping, crawling, browser automation, CAPTCHA, anti-bot, or website bypass logic
- compliance, legal, jurisdiction, geofence, or geographic-access analysis

## Level 1B Node 3 Scope

This node adds only derived paper analytics:

- point-in-time paper performance summary from a `PaperPortfolio` and matching `PaperNavSnapshot`
- per-position exposure rows joined from `PaperPosition` and `PaperPositionMark`
- exposure buckets by stable existing dimensions: `token_id`, `condition_id`, `market_slug`, `strategy_type`, `risk_tag`, `resolution_source`, and `mark_status`
- liquidity-risk metrics from mark status, filled/unfilled exit size, and executable exit value
- executable-NAV drawdown points from supplied `PaperNavSnapshot` history
- report-level threshold breaches from a paper-only `PaperAnalyticsConfig`
- append-only JSONL report persistence, if callers want durable analytics snapshots
- package-root exports and README status/API text

This node intentionally defers:

- resolved-outcome calibration, Brier score, and settlement analytics
- edge decay and holding-period analytics
- strategy promotion packets or proposal generation
- dashboards or UI
- CLI commands
- local JSONL readers or external historical loaders
- theme, maturity, market-class, or event-group analytics unless those fields are later carried into journal/position artifacts
- exchange reconciliation or live execution readiness claims

## Target File Structure

- Create: `src/polymarket_alpha_lab/analytics.py`
  - Frozen report dataclasses, pure analytics functions, and JSONL report log.
- Create: `tests/test_analytics.py`
  - TDD tests for report math, exposure buckets, drawdown, validation, and JSONL persistence.
- Create: `tests/test_analytics_scope.py`
  - Static forbidden-surface tests for Node 3 module and public exports.
- Modify: `src/polymarket_alpha_lab/__init__.py`
  - Export stable Level 1B Node 3 public APIs.
- Modify: `tests/test_init.py`
  - Package-root export contract for analytics APIs.
- Modify: `README.md`
  - Add Level 1B Node 3 paper-only status, Python API notes, and repository tree entries.
- Modify: `docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-risk-exposure.md`
  - Update gate results and handoff notes as the node is completed.

## Public API Contract

Create these names:

```python
from polymarket_alpha_lab.analytics import (
    PaperAnalyticsBreach,
    PaperAnalyticsBucket,
    PaperAnalyticsConfig,
    PaperAnalyticsLog,
    PaperAnalyticsReport,
    PaperDrawdownPoint,
    PaperPerformanceSummary,
    PaperPositionExposure,
    build_paper_analytics_report,
    build_paper_drawdown_points,
)
```

Export all ten from `polymarket_alpha_lab.__init__`.

## Analytics Semantics

`build_paper_analytics_report(portfolio, snapshot, *, config, generated_at, drawdown_snapshots=())` returns `PaperAnalyticsReport`.

- `portfolio` must be a `PaperPortfolio`.
- `snapshot` must be a `PaperNavSnapshot`.
- `config` must be a `PaperAnalyticsConfig`.
- `generated_at` must be a `datetime`; naive datetimes are treated as UTC, matching existing journal/NAV behavior.
- `drawdown_snapshots` may be empty. When empty, the report computes drawdown points from `(snapshot,)`.
- `portfolio.starting_cash` and `snapshot.starting_cash` must be strictly positive. Existing `PaperPortfolio` and `PaperNavSnapshot` constructors enforce this; analytics also validates the positive value before computing starting-cash-denominator ratios so corrupted objects cannot produce divide-by-zero output.
- The function validates that `portfolio` and `snapshot` describe the same paper state:
  - `starting_cash`, `cash_balance`, and `realized_pnl` match.
  - open token ids match mark token ids exactly.
  - position token ids and mark token ids are unique before maps are built, even if a corrupted object bypassed constructor validation.
  - per-token `condition_id`, `market_slug`, `outcome_name`, `open_size`, `cost_basis`, and `average_entry_price` match.
  - `snapshot.paper_only is True`.
- `drawdown_snapshots` must be an iterable of `PaperNavSnapshot` values and must reject `str`/`bytes` inputs before iterating characters.
- The function never fetches books, reads account state, uses a client/transport, places/cancels orders, reconciles exchange accounts, or creates trade proposals.
- The function never recomputes executable NAV from `exit_average_price`, midpoint, best bid, model probability, or fair value. It uses `PaperPositionMark.exit_value` and `PaperNavSnapshot.exit_nav`.
- `midpoint_nav` and `midpoint_value` are informational only. If midpoint is unavailable, midpoint gap fields are `None`; executable analytics still use exit NAV.
- All monetary, share, and ratio math uses finite `Decimal` values only. Undefined ratios return `None`, never `NaN`, `Infinity`, or a misleading zero.
- Ratio fields are quantized to `Decimal("0.0001")` with half-even rounding:
  - `exit_return_ratio = (exit_nav - starting_cash) / starting_cash`
  - `realized_return_ratio = realized_pnl / starting_cash`
  - `unrealized_exit_return_ratio = unrealized_exit_pnl / starting_cash`
  - `cash_ratio = cash_balance / starting_cash`
  - `open_cost_basis_ratio = total_cost_basis / starting_cash`
  - `midpoint_nav_gap_ratio = midpoint_nav_gap / midpoint_nav` when `midpoint_nav` is present and nonzero
  - `exit_depth_coverage_ratio = sum(exit_filled_size) / sum(open_size)`, or `None` when there are no open positions
  - `exit_depth_shortfall_ratio = sum(exit_unfilled_size) / sum(open_size)`, or `None` when there are no open positions
  - `no_exit_depth_cost_basis_ratio = sum(cost_basis for no_exit_depth positions) / starting_cash`, or `None` when there are no open positions
  - per-position `exit_coverage_ratio = exit_filled_size / open_size`
  - per-position `exit_shortfall_ratio = exit_unfilled_size / open_size`
  - bucket `cost_basis_ratio_to_starting_cash = bucket.cost_basis / starting_cash`
  - bucket `cost_basis_ratio_to_total_open_basis = bucket.cost_basis / total_cost_basis`, or `None` when total open basis is zero
  - bucket `exit_value_ratio_to_exit_nav = bucket.exit_value / exit_nav`, or `None` when exit NAV is zero
- `midpoint_nav_gap = midpoint_nav - exit_nav` is a monetary difference, not a ratio. Compute it with exact `Decimal` arithmetic and do not quantize it to `RATIO_QUANTUM`.
- Output ordering is deterministic:
  - `position_exposures` follows `portfolio.positions`.
  - `buckets` are sorted by `(bucket_type, bucket_value)`.
  - drawdown points are sorted by `marked_at`.
  - breaches are sorted by stable detection order.

`build_paper_drawdown_points(snapshots)` returns a tuple of `PaperDrawdownPoint` values.

- `snapshots` must be an iterable of `PaperNavSnapshot` values.
- `snapshots` must reject `str`/`bytes` inputs before iterating characters.
- Empty input returns `()`.
- Duplicate `marked_at` values raise `ValueError` to avoid ambiguous time-series ordering.
- Drawdown is computed from `exit_nav`, not `midpoint_nav`.
- `high_watermark_nav` is the maximum exit NAV observed up to that point.
- `drawdown` equals `high_watermark_nav - exit_nav`.
- `drawdown_ratio` equals `drawdown / high_watermark_nav`, or `None` when the high watermark is zero.
- `is_new_high` is true when the point sets or matches a new high watermark.

`PaperAnalyticsLog(path).append(report)` persists a report as strict append-only JSONL.

- Validate and serialize the report before opening the file.
- Create parent directories.
- Use sorted keys and `allow_nan=False`.
- Serialize finite `Decimal` values as strings and UTC datetimes as ISO strings.
- Preserve an existing file when serialization fails before open.
- Follow the strict `PaperNavLog` and `RejectedCandidateLog` validation-before-open pattern, not the older looser `PaperTradeJournal` pattern.

## Planned Dataclasses

`analytics.py` should use frozen dataclasses and direct construction validation:

```python
@dataclass(frozen=True)
class PaperAnalyticsConfig:
    config_version: str
    max_open_cost_basis_ratio: Decimal = Decimal("1.00")
    max_single_position_cost_basis_ratio: Decimal = Decimal("0.25")
    max_strategy_cost_basis_ratio: Decimal = Decimal("0.50")
    max_market_cost_basis_ratio: Decimal = Decimal("0.50")
    max_risk_tag_cost_basis_ratio: Decimal = Decimal("0.50")
    max_no_exit_depth_cost_basis_ratio: Decimal = Decimal("0.10")
    min_cash_ratio: Decimal = Decimal("0.00")


@dataclass(frozen=True)
class PaperAnalyticsBreach:
    code: str
    message: str
    field_name: str
    observed_value: Decimal | str | None = None
    threshold: Decimal | str | None = None


@dataclass(frozen=True)
class PaperPerformanceSummary:
    starting_cash: Decimal
    cash_balance: Decimal
    realized_pnl: Decimal
    unrealized_exit_pnl: Decimal
    total_exit_pnl: Decimal
    exit_nav: Decimal
    midpoint_nav: Decimal | None
    total_cost_basis: Decimal
    exit_return_ratio: Decimal
    realized_return_ratio: Decimal
    unrealized_exit_return_ratio: Decimal
    cash_ratio: Decimal
    open_cost_basis_ratio: Decimal
    midpoint_nav_gap: Decimal | None
    midpoint_nav_gap_ratio: Decimal | None


@dataclass(frozen=True)
class PaperPositionExposure:
    source_packet_ids: tuple[str, ...]
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    strategy_type: str
    risk_tags: tuple[str, ...]
    rule_text_hash: str
    resolution_source: str
    market_raw_archive_path: str
    last_order_book_raw_archive_path: str
    last_order_book_raw_payload_sha256: str
    last_order_book_snapshot_sha256: str
    opened_at: datetime
    updated_at: datetime
    open_size: Decimal
    cost_basis: Decimal
    average_entry_price: Decimal
    realized_pnl: Decimal
    entry_trade_count: int
    exit_trade_count: int
    max_loss_to_zero: Decimal
    max_profit_to_one: Decimal
    exit_value: Decimal
    midpoint_value: Decimal | None
    unrealized_exit_pnl: Decimal
    exit_filled_size: Decimal
    exit_unfilled_size: Decimal
    exit_coverage_ratio: Decimal
    exit_shortfall_ratio: Decimal
    cost_basis_ratio_to_starting_cash: Decimal
    cost_basis_ratio_to_total_open_basis: Decimal | None
    exit_value_ratio_to_exit_nav: Decimal | None
    mark_status: str
    order_book_captured_at: datetime
    order_book_snapshot_sha256: str


@dataclass(frozen=True)
class PaperAnalyticsBucket:
    bucket_type: str
    bucket_value: str
    additive: bool
    position_count: int
    token_ids: tuple[str, ...]
    open_size: Decimal
    cost_basis: Decimal
    max_loss_to_zero: Decimal
    exit_value: Decimal
    unrealized_exit_pnl: Decimal
    exit_unfilled_size: Decimal
    cost_basis_ratio_to_starting_cash: Decimal
    cost_basis_ratio_to_total_open_basis: Decimal | None
    exit_value_ratio_to_exit_nav: Decimal | None


@dataclass(frozen=True)
class PaperDrawdownPoint:
    marked_at: datetime
    exit_nav: Decimal
    high_watermark_nav: Decimal
    drawdown: Decimal
    drawdown_ratio: Decimal | None
    is_new_high: bool


@dataclass(frozen=True)
class PaperAnalyticsReport:
    generated_at: datetime
    config_version: str
    marked_at: datetime
    performance: PaperPerformanceSummary
    position_count: int
    portfolio_mark_status: str
    exit_depth_coverage_ratio: Decimal | None
    exit_depth_shortfall_ratio: Decimal | None
    no_exit_depth_cost_basis_ratio: Decimal | None
    oldest_order_book_captured_at: datetime | None
    newest_order_book_captured_at: datetime | None
    position_exposures: tuple[PaperPositionExposure, ...]
    buckets: tuple[PaperAnalyticsBucket, ...]
    drawdown_points: tuple[PaperDrawdownPoint, ...]
    breaches: tuple[PaperAnalyticsBreach, ...]
    paper_only: bool = True


@dataclass(frozen=True)
class PaperAnalyticsLog:
    path: Path | str
```

`PaperAnalyticsLog` exposes one public method with this exact signature:

```python
append(self, report: PaperAnalyticsReport) -> None
```

Direct dataclass construction must validate nonblank strings, finite `Decimal` fields, nonnegative counts/sizes where applicable, ratios that are either `None` or finite `Decimal`, tuple field contents, UTC-normalizable timestamps, `paper_only is True`, valid breach codes and breach value types, and JSON-serializable values before file writes.

`PaperPerformanceSummary.starting_cash` must be strictly positive. Starting-cash-denominator ratio fields are non-optional `Decimal` values because zero starting cash is rejected instead of represented as `None`.

`PaperPositionExposure` carries all stable `PaperPosition` fields plus joined mark fields. Holding-period analytics are deferred, but `opened_at`, `updated_at`, `average_entry_price`, `realized_pnl`, and trade counts remain part of the exposure row so downstream paper-only analysis does not need to rejoin the position ledger.

## Breach Semantics

`PaperAnalyticsConfig` thresholds are report-only. They produce `PaperAnalyticsBreach` entries but never create orders, proposals, cancellations, or execution decisions.

Stable breach codes:

- `open_cost_basis_limit`
- `single_position_cost_basis_limit`
- `strategy_cost_basis_limit`
- `market_cost_basis_limit`
- `risk_tag_cost_basis_limit`
- `no_exit_depth_limit`
- `low_cash_ratio`

`PaperAnalyticsBreach.code` must be one of these stable breach codes. Direct construction with any other code raises `ValueError`.

`PaperAnalyticsConfig` threshold fields must be nonnegative finite `Decimal` values. Ratios above `1` are allowed because paper portfolios can contain reinvested profits or intentionally loose report thresholds. `config_version` must be a nonblank canonical string.

Detection order:

1. open cost basis
2. single position, in `position_exposures` order
3. strategy buckets
4. market buckets
5. risk tag buckets
6. no-exit-depth cost basis
7. cash ratio

Aggregate `portfolio_mark_status` values:

- `no_open_positions` when the report has no position exposures
- `fully_executable` when every mark is fully executable
- `no_exit_depth` when every mark has no exit depth
- `partially_executable` for every other open-portfolio case, including any partially executable mark or a mixture of fully executable and no-exit-depth marks

## Part 0: Existing Contract Check

**Goal:** Reconfirm current Level 1B Node 2 contracts before implementing analytics.

**Files:**

- Inspect: `src/polymarket_alpha_lab/positions.py`
- Inspect: `src/polymarket_alpha_lab/journal.py`
- Inspect: `src/polymarket_alpha_lab/__init__.py`
- Inspect: `tests/test_positions.py`
- Inspect: `tests/test_init.py`

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
codegraph explore "PaperPortfolio PaperPosition PaperPositionMark PaperNavSnapshot build_paper_portfolio mark_paper_nav PaperNavLog PaperTradeRecord package exports"
codegraph node src/polymarket_alpha_lab/positions.py
codegraph node src/polymarket_alpha_lab/journal.py
codegraph node src/polymarket_alpha_lab/__init__.py
codegraph node tests/test_positions.py
codegraph node tests/test_init.py
```

Expected: confirm `PaperPortfolio` and `PaperNavSnapshot` enforce accounting identities; marks include executable `exit_value`, mark status, filled/unfilled exit size, midpoint metadata, and order-book provenance; positions include strategy/risk/provenance metadata; package exports follow explicit import plus explicit `__all__`.

If these contracts differ, update this plan before writing implementation tests.

## Part 1: Static Paper-Only Boundary Tests

**Goal:** Lock Node 3 scope before analytics implementation.

**Files:**

- Create: `tests/test_analytics_scope.py`
- Production target created in Part 4: `src/polymarket_alpha_lab/analytics.py`

- [ ] **Step 1: Write failing forbidden-surface tests**

Create `tests/test_analytics_scope.py`:

```python
import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYTICS_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "analytics.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"


EXPECTED_ANALYTICS_EXPORTS = {
    "PaperAnalyticsBreach",
    "PaperAnalyticsBucket",
    "PaperAnalyticsConfig",
    "PaperAnalyticsLog",
    "PaperAnalyticsReport",
    "PaperDrawdownPoint",
    "PaperPerformanceSummary",
    "PaperPositionExposure",
    "build_paper_analytics_report",
    "build_paper_drawdown_points",
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
    "polymarket_alpha_lab.positions",
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
    "historical",
    "historicalloader",
    "externalhistory",
    "readjsonl",
    "loadjsonl",
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


def parse_analytics():
    return ast.parse(ANALYTICS_PATH.read_text(encoding="utf-8"))


def normalize_identifier(value):
    return "".join(character for character in value.lower() if character.isalnum())


def imported_modules(tree):
    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
            imported_modules.extend(alias.asname for alias in node.names if alias.asname)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
            imported_modules.extend(alias.asname for alias in node.names if alias.asname)
    return imported_modules


def module_exports(tree):
    assigned_exports = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def test_analytics_module_imports_only_allowed_dependencies():
    tree = parse_analytics()
    for module_name in imported_modules(tree):
        assert any(
            module_name == allowed or module_name.startswith(f"{allowed}.")
            for allowed in ALLOWED_IMPORT_PREFIXES
        ), module_name


def test_analytics_module_does_not_import_forbidden_surfaces():
    tree = parse_analytics()
    for module_name in imported_modules(tree):
        assert not any(
            module_name == forbidden or module_name.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_analytics_module_does_not_define_forbidden_names():
    tree = parse_analytics()
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


def test_analytics_public_exports_are_paper_report_only():
    tree = parse_analytics()
    assigned_exports = module_exports(tree)
    assert set(assigned_exports) == EXPECTED_ANALYTICS_EXPORTS
    for name in assigned_exports:
        assert name.startswith("Paper") or name.startswith("build_paper")
        normalized_name = normalize_identifier(name)
        assert not any(
            fragment in normalized_name for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
        )


def test_package_root_exports_do_not_leak_forbidden_analytics_surfaces():
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
.venv/bin/python -m pytest tests/test_analytics_scope.py -q
```

Expected: fail because `src/polymarket_alpha_lab/analytics.py` does not exist.

## Part 2: Analytics Report Tests

**Goal:** Define point-in-time performance, exposure, liquidity, breach, and validation behavior.

**Files:**

- Create: `tests/test_analytics.py`
- Production target created in Part 4: `src/polymarket_alpha_lab/analytics.py`

- [ ] **Step 1: Write failing analytics tests**

Create `tests/test_analytics.py` with this import block and helper fixture setup:

```python
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Context, Decimal, localcontext

import pytest

from polymarket_alpha_lab.analytics import (
    PaperAnalyticsBreach,
    PaperAnalyticsBucket,
    PaperAnalyticsConfig,
    PaperAnalyticsLog,
    PaperAnalyticsReport,
    PaperDrawdownPoint,
    PaperPerformanceSummary,
    PaperPositionExposure,
    build_paper_analytics_report,
    build_paper_drawdown_points,
)
from polymarket_alpha_lab.domain import OrderBookLevel, OrderBookSnapshot
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill
from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.positions import build_paper_portfolio, mark_paper_nav
from polymarket_alpha_lab.research import build_research_packet


def complete_packet(**overrides):
    values = {
        "candidate": ScoredCandidate(
            condition_id="0xabc",
            token_id="111",
            market_slug="example-market",
            question="Will the example resolve yes?",
            total_score="78.500",
            raw_archive_path="data/raw/gamma/markets.json",
        ),
        "created_at": datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        "market_url": "https://polymarket.com/event/example-market",
        "outcome_name": "Yes",
        "strategy_type": "market_quality",
        "model_probability": Decimal("0.56"),
        "bid": Decimal("0.50"),
        "ask": Decimal("0.52"),
        "midpoint": Decimal("0.51"),
        "expected_entry_price": Decimal("0.514"),
        "fair_value_estimate": Decimal("0.56"),
        "theoretical_edge": Decimal("0.046"),
        "spread": Decimal("0.02"),
        "slippage_estimate": Decimal("0.004"),
        "cost_adjusted_edge": Decimal("0.026"),
        "confidence": Decimal("0.60"),
        "max_executable_size": Decimal("100"),
        "risk_tags": ("liquidity",),
        "thesis": "Tight spread and clear rules.",
        "invalidating_conditions": "Spread widens.",
        "rule_text": "Example rule.",
        "resolution_source": "Example source",
    }
    values.update(overrides)
    return build_research_packet(**values)


def complete_fill(**overrides):
    values = {
        "token_id": "111",
        "side": "buy",
        "requested_size": Decimal("100"),
        "order_book_captured_at": datetime(2026, 6, 13, 12, 30, 30, tzinfo=UTC),
        "order_book_snapshot_sha256": "a" * 64,
        "filled_size": Decimal("100"),
        "unfilled_size": Decimal("0"),
        "average_price": Decimal("0.514"),
        "worst_price": Decimal("0.52"),
        "best_bid": Decimal("0.49"),
        "best_ask": Decimal("0.51"),
        "midpoint": Decimal("0.500"),
        "spread": Decimal("0.020"),
        "slippage_estimate": Decimal("0.004"),
    }
    values.update(overrides)
    return PaperFill(**values)


def record_from(packet=None, fill=None, **overrides):
    values = {
        "packet": packet or complete_packet(),
        "fill": fill or complete_fill(),
        "decision_timestamp": datetime(2026, 6, 13, 12, 31),
        "order_book_raw_archive_path": "data/raw/clob/book-111.json",
        "order_book_raw_payload_sha256": "b" * 64,
        "account_equity_before_trade": Decimal("10000"),
        "sizing_limiter": "max_executable_size",
        "planned_exit_rule": "Mark at executable bid on review.",
    }
    values.update(overrides)
    return PaperTradeRecord.from_packet_and_fill(**values)


def packet_at(minute: int, **overrides):
    values = {"created_at": datetime(2026, 6, 13, 12, minute, tzinfo=UTC)}
    values.update(overrides)
    return complete_packet(**values)
```

Add these required tests:

```python
def two_position_report():
    first = record_from()
    second_packet = packet_at(
        32,
        candidate=ScoredCandidate(
            condition_id="0xaaa",
            token_id="222",
            market_slug="another-market",
            question="Will another market resolve yes?",
            total_score="80.000",
            raw_archive_path="data/raw/gamma/markets-2.json",
        ),
        market_url="https://polymarket.com/event/another-market",
        outcome_name="Yes",
        strategy_type="relative_value",
        risk_tags=("liquidity", "event-risk"),
        resolution_source="Another source",
    )
    second = record_from(
        packet=second_packet,
        fill=complete_fill(
            token_id="222",
            requested_size=Decimal("50"),
            filled_size=Decimal("50"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.200"),
            worst_price=Decimal("0.20"),
        ),
        order_book_raw_archive_path="data/raw/clob/book-222.json",
        order_book_raw_payload_sha256="c" * 64,
    )
    portfolio = build_paper_portfolio([first, second], starting_cash=Decimal("10000"))
    snapshot = mark_paper_nav(
        portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(OrderBookLevel(Decimal("0.50"), Decimal("100")),),
                asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
                captured_at=datetime(2026, 6, 14, 0, 0, tzinfo=UTC),
            ),
            "222": OrderBookSnapshot(
                token_id="222",
                bids=(OrderBookLevel(Decimal("0.10"), Decimal("10")),),
                asks=(OrderBookLevel(Decimal("0.22"), Decimal("50")),),
                captured_at=datetime(2026, 6, 14, 0, 1, tzinfo=UTC),
            ),
        },
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )
    report = build_paper_analytics_report(
        portfolio,
        snapshot,
        config=PaperAnalyticsConfig(
            config_version="node3-test",
            max_open_cost_basis_ratio=Decimal("0.0100"),
            max_single_position_cost_basis_ratio=Decimal("0.0040"),
            max_strategy_cost_basis_ratio=Decimal("0.0040"),
            max_market_cost_basis_ratio=Decimal("0.0040"),
            max_risk_tag_cost_basis_ratio=Decimal("0.0040"),
            max_no_exit_depth_cost_basis_ratio=Decimal("0.0001"),
            min_cash_ratio=Decimal("0.9900"),
        ),
        generated_at=datetime(2026, 6, 14, 12, tzinfo=UTC),
    )
    return portfolio, snapshot, report


def test_build_paper_analytics_report_summarizes_performance_and_liquidity():
    _portfolio, snapshot, report = two_position_report()

    assert report.generated_at == datetime(2026, 6, 14, 12, tzinfo=UTC)
    assert report.config_version == "node3-test"
    assert report.marked_at == snapshot.marked_at
    assert report.paper_only is True
    assert report.position_count == 2
    assert report.portfolio_mark_status == "partially_executable"
    assert report.performance.starting_cash == Decimal("10000")
    assert report.performance.cash_balance == Decimal("9938.600")
    assert report.performance.realized_pnl == Decimal("0")
    assert report.performance.unrealized_exit_pnl == Decimal("-10.400")
    assert report.performance.total_exit_pnl == Decimal("-10.400")
    assert report.performance.exit_nav == Decimal("9989.600")
    assert report.performance.midpoint_nav == Decimal("9997.600")
    assert report.performance.total_cost_basis == Decimal("61.400")
    assert report.performance.exit_return_ratio == Decimal("-0.0010")
    assert report.performance.realized_return_ratio == Decimal("0.0000")
    assert report.performance.unrealized_exit_return_ratio == Decimal("-0.0010")
    assert report.performance.cash_ratio == Decimal("0.9939")
    assert report.performance.open_cost_basis_ratio == Decimal("0.0061")
    assert report.performance.midpoint_nav_gap == Decimal("8.000")
    assert report.performance.midpoint_nav_gap_ratio == Decimal("0.0008")
    assert report.exit_depth_coverage_ratio == Decimal("0.7333")
    assert report.exit_depth_shortfall_ratio == Decimal("0.2667")
    assert report.no_exit_depth_cost_basis_ratio == Decimal("0.0000")
    assert report.oldest_order_book_captured_at == datetime(2026, 6, 14, 0, 0, tzinfo=UTC)
    assert report.newest_order_book_captured_at == datetime(2026, 6, 14, 0, 1, tzinfo=UTC)
```

```python
def test_build_paper_analytics_report_builds_position_exposures_and_buckets():
    _portfolio, _snapshot, report = two_position_report()

    assert [row.token_id for row in report.position_exposures] == ["222", "111"]
    first = report.position_exposures[0]
    assert first.token_id == "222"
    assert first.strategy_type == "relative_value"
    assert first.risk_tags == ("liquidity", "event-risk")
    assert first.open_size == Decimal("50")
    assert first.cost_basis == Decimal("10.000")
    assert first.max_loss_to_zero == Decimal("10.000")
    assert first.max_profit_to_one == Decimal("40.000")
    assert first.exit_value == Decimal("1.000")
    assert first.midpoint_value == Decimal("8.000")
    assert first.unrealized_exit_pnl == Decimal("-9.000")
    assert first.exit_filled_size == Decimal("10")
    assert first.exit_unfilled_size == Decimal("40")
    assert first.exit_coverage_ratio == Decimal("0.2000")
    assert first.exit_shortfall_ratio == Decimal("0.8000")
    assert first.cost_basis_ratio_to_starting_cash == Decimal("0.0010")
    assert first.cost_basis_ratio_to_total_open_basis == Decimal("0.1629")
    assert first.exit_value_ratio_to_exit_nav == Decimal("0.0001")
    assert first.mark_status == "partially_executable"
    assert first.source_packet_ids
    assert first.market_url == "https://polymarket.com/event/another-market"
    assert first.last_order_book_raw_payload_sha256 == "c" * 64
    assert first.opened_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert first.updated_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert first.average_entry_price == Decimal("0.200")
    assert first.realized_pnl == Decimal("0")
    assert first.entry_trade_count == 1
    assert first.exit_trade_count == 0

    buckets = {(bucket.bucket_type, bucket.bucket_value): bucket for bucket in report.buckets}
    assert buckets[("strategy_type", "relative_value")].cost_basis == Decimal("10.000")
    assert buckets[("market_slug", "another-market")].token_ids == ("222",)
    assert buckets[("risk_tag", "liquidity")].additive is False
    assert buckets[("risk_tag", "liquidity")].position_count == 2
    assert buckets[("risk_tag", "liquidity")].cost_basis == Decimal("61.400")
    assert buckets[("risk_tag", "event-risk")].additive is False
    assert buckets[("risk_tag", "event-risk")].token_ids == ("222",)
    assert buckets[("risk_tag", "event-risk")].cost_basis == Decimal("10.000")
    risk_tag_buckets = [
        bucket for bucket in report.buckets if bucket.bucket_type == "risk_tag"
    ]
    assert sum(bucket.cost_basis for bucket in risk_tag_buckets) > report.performance.total_cost_basis
    assert buckets[("mark_status", "partially_executable")].exit_unfilled_size == Decimal("40")
```

```python
def test_build_paper_analytics_report_records_threshold_breaches():
    _portfolio, _snapshot, report = two_position_report()

    codes = [breach.code for breach in report.breaches]
    assert codes == [
        "single_position_cost_basis_limit",
        "strategy_cost_basis_limit",
        "market_cost_basis_limit",
        "risk_tag_cost_basis_limit",
    ]
    assert report.breaches[0].field_name == "position:111"
    assert report.breaches[0].observed_value == Decimal("0.0051")
    assert report.breaches[0].threshold == Decimal("0.0040")
```

```python
def test_build_paper_analytics_report_rejects_mismatched_portfolio_and_snapshot():
    portfolio, snapshot, _report = two_position_report()
    other_portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    mismatched_snapshot = mark_paper_nav(
        other_portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(OrderBookLevel(Decimal("0.50"), Decimal("100")),),
                asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
                captured_at=datetime(2026, 6, 14, tzinfo=UTC),
            )
        },
        marked_at=snapshot.marked_at,
    )

    with pytest.raises(ValueError, match="cash_balance|token"):
        build_paper_analytics_report(
            portfolio,
            mismatched_snapshot,
            config=PaperAnalyticsConfig(config_version="node3-test"),
            generated_at=datetime(2026, 6, 14, tzinfo=UTC),
        )
```

```python
def test_build_paper_analytics_report_rejects_corrupted_zero_starting_cash():
    portfolio, snapshot, _report = two_position_report()
    object.__setattr__(portfolio, "starting_cash", Decimal("0"))
    object.__setattr__(snapshot, "starting_cash", Decimal("0"))

    with pytest.raises(ValueError, match="starting_cash"):
        build_paper_analytics_report(
            portfolio,
            snapshot,
            config=PaperAnalyticsConfig(config_version="node3-test"),
            generated_at=datetime(2026, 6, 14, tzinfo=UTC),
        )
```

```python
def test_build_paper_analytics_report_handles_empty_portfolio():
    portfolio = build_paper_portfolio([], starting_cash=Decimal("10000"))
    snapshot = mark_paper_nav(portfolio, {}, marked_at=datetime(2026, 6, 14, tzinfo=UTC))

    report = build_paper_analytics_report(
        portfolio,
        snapshot,
        config=PaperAnalyticsConfig(config_version="node3-test"),
        generated_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert report.position_count == 0
    assert report.portfolio_mark_status == "no_open_positions"
    assert report.position_exposures == ()
    assert report.buckets == ()
    assert report.exit_depth_coverage_ratio is None
    assert report.exit_depth_shortfall_ratio is None
    assert report.no_exit_depth_cost_basis_ratio is None
    assert report.performance.cash_balance == Decimal("10000")
    assert report.performance.exit_nav == Decimal("10000")
    assert report.performance.midpoint_nav == Decimal("10000")
    assert report.performance.total_cost_basis == Decimal("0")
    assert report.performance.unrealized_exit_pnl == Decimal("0")
    assert report.performance.exit_return_ratio == Decimal("0.0000")
    assert report.performance.cash_ratio == Decimal("1.0000")
    assert report.performance.open_cost_basis_ratio == Decimal("0.0000")
    assert report.performance.midpoint_nav_gap == Decimal("0")
    assert report.performance.midpoint_nav_gap_ratio == Decimal("0.0000")
    assert report.oldest_order_book_captured_at is None
    assert report.newest_order_book_captured_at is None
    assert len(report.drawdown_points) == 1
```

```python
def test_build_paper_analytics_report_handles_missing_midpoint_without_nav_fallback():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    snapshot = mark_paper_nav(
        portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(OrderBookLevel(Decimal("0.50"), Decimal("100")),),
                asks=(),
                captured_at=datetime(2026, 6, 14, tzinfo=UTC),
            )
        },
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    report = build_paper_analytics_report(
        portfolio,
        snapshot,
        config=PaperAnalyticsConfig(config_version="node3-test"),
        generated_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert snapshot.exit_nav == Decimal("9998.600")
    assert snapshot.midpoint_nav is None
    assert report.portfolio_mark_status == "fully_executable"
    assert report.performance.midpoint_nav is None
    assert report.performance.midpoint_nav_gap is None
    assert report.performance.midpoint_nav_gap_ratio is None
    assert report.exit_depth_coverage_ratio == Decimal("1.0000")
    assert report.position_exposures[0].exit_value == Decimal("50.00")
    assert report.position_exposures[0].midpoint_value is None


def test_build_paper_analytics_report_handles_all_no_exit_depth():
    portfolio, _snapshot, _report = two_position_report()
    snapshot = mark_paper_nav(
        portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(),
                asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
                captured_at=datetime(2026, 6, 14, tzinfo=UTC),
            ),
            "222": OrderBookSnapshot(
                token_id="222",
                bids=(),
                asks=(OrderBookLevel(Decimal("0.22"), Decimal("50")),),
                captured_at=datetime(2026, 6, 14, 0, 1, tzinfo=UTC),
            ),
        },
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    report = build_paper_analytics_report(
        portfolio,
        snapshot,
        config=PaperAnalyticsConfig(
            config_version="node3-test",
            max_no_exit_depth_cost_basis_ratio=Decimal("0.0001"),
        ),
        generated_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert snapshot.exit_nav == Decimal("9938.600")
    assert snapshot.midpoint_nav is None
    assert snapshot.total_cost_basis == Decimal("61.400")
    assert report.portfolio_mark_status == "no_exit_depth"
    assert report.exit_depth_coverage_ratio == Decimal("0.0000")
    assert report.exit_depth_shortfall_ratio == Decimal("1.0000")
    assert report.no_exit_depth_cost_basis_ratio == Decimal("0.0061")
    assert {row.mark_status for row in report.position_exposures} == {"no_exit_depth"}
    assert [b.code for b in report.breaches if b.code == "no_exit_depth_limit"] == [
        "no_exit_depth_limit"
    ]


def test_build_paper_analytics_report_handles_zero_exit_nav_without_dividing_by_zero():
    packet = complete_packet(max_executable_size=Decimal("1"))
    fill = complete_fill(
        requested_size=Decimal("1"),
        filled_size=Decimal("1"),
        unfilled_size=Decimal("0"),
        average_price=Decimal("1"),
        worst_price=Decimal("1"),
        best_bid=Decimal("1"),
        best_ask=Decimal("1"),
        midpoint=Decimal("1"),
        spread=Decimal("0"),
        slippage_estimate=Decimal("0"),
    )
    portfolio = build_paper_portfolio(
        [record_from(packet=packet, fill=fill)],
        starting_cash=Decimal("1"),
    )
    snapshot = mark_paper_nav(
        portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(),
                asks=(OrderBookLevel(Decimal("1"), Decimal("1")),),
                captured_at=datetime(2026, 6, 14, tzinfo=UTC),
            )
        },
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    report = build_paper_analytics_report(
        portfolio,
        snapshot,
        config=PaperAnalyticsConfig(config_version="node3-test"),
        generated_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert snapshot.exit_nav == Decimal("0")
    assert report.performance.exit_return_ratio == Decimal("-1.0000")
    assert report.performance.cash_ratio == Decimal("0.0000")
    assert report.position_exposures[0].exit_value_ratio_to_exit_nav is None
    assert report.buckets
    assert all(bucket.exit_value_ratio_to_exit_nav is None for bucket in report.buckets)
    assert report.drawdown_points[0].high_watermark_nav == Decimal("0")
    assert report.drawdown_points[0].drawdown_ratio is None
```

```python
@pytest.mark.parametrize(
    "bad_value",
    [
        Decimal("NaN"),
        Decimal("sNaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
        0.1,
        1,
        "0.1",
        None,
    ],
)
def test_analytics_config_rejects_non_decimal_or_non_finite_thresholds(bad_value):
    with pytest.raises(ValueError, match="max_open_cost_basis_ratio"):
        PaperAnalyticsConfig(
            config_version="node3-test",
            max_open_cost_basis_ratio=bad_value,
        )


def test_analytics_breach_rejects_float_values():
    with pytest.raises(ValueError, match="observed_value"):
        PaperAnalyticsBreach(
            code="open_cost_basis_limit",
            message="Example breach.",
            field_name="example",
            observed_value=0.1,
            threshold=Decimal("0.1000"),
        )


def test_analytics_breach_rejects_unknown_code():
    with pytest.raises(ValueError, match="code"):
        PaperAnalyticsBreach(
            code="unknown_limit",
            message="Example breach.",
            field_name="example",
            observed_value=Decimal("0.1000"),
            threshold=Decimal("0.0500"),
        )


def test_paper_analytics_log_appends_jsonl_report(tmp_path):
    _portfolio, _snapshot, report = two_position_report()
    log = PaperAnalyticsLog(path=tmp_path / "analytics.jsonl")

    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"breaches"')
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["generated_at"] == "2026-06-14T12:00:00+00:00"
    assert stored["marked_at"] == "2026-06-14T00:00:00+00:00"
    assert stored["performance"]["starting_cash"] == "10000"
    assert stored["performance"]["cash_ratio"] == "0.9939"
    assert stored["breaches"][0]["observed_value"] == "0.0051"
    assert stored["position_exposures"][0]["risk_tags"] == ["liquidity", "event-risk"]


def test_paper_analytics_log_appends_without_overwriting(tmp_path):
    _portfolio, _snapshot, report = two_position_report()
    second = replace(report, generated_at=datetime(2026, 6, 14, 13, tzinfo=UTC))
    log = PaperAnalyticsLog(path=tmp_path / "analytics.jsonl")

    log.append(report)
    log.append(second)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["generated_at"] == "2026-06-14T12:00:00+00:00"
    assert json.loads(lines[1])["generated_at"] == "2026-06-14T13:00:00+00:00"


def test_paper_analytics_log_creates_parent_directories_from_string_path(tmp_path):
    _portfolio, _snapshot, report = two_position_report()
    log = PaperAnalyticsLog(path=str(tmp_path / "nested" / "analytics.jsonl"))

    log.append(report)

    assert log.path.exists()
    assert len(log.path.read_text(encoding="utf-8").splitlines()) == 1


def test_paper_analytics_log_rejects_invalid_paths(tmp_path):
    with pytest.raises(ValueError, match="path"):
        PaperAnalyticsLog(path=object())
    with pytest.raises(ValueError, match="path"):
        PaperAnalyticsLog(path="")
    with pytest.raises(ValueError, match="path"):
        PaperAnalyticsLog(path=tmp_path)
    parent_file = tmp_path / "not-a-directory"
    parent_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="path"):
        PaperAnalyticsLog(path=parent_file / "analytics.jsonl")


def test_paper_analytics_log_rejects_invalid_public_input_before_open(tmp_path):
    log = PaperAnalyticsLog(path=tmp_path / "analytics.jsonl")

    with pytest.raises(ValueError, match="report"):
        log.append(object())

    assert not log.path.exists()


@pytest.mark.parametrize("bad_value", [Decimal("NaN"), float("nan"), object()])
def test_paper_analytics_log_preserves_existing_file_when_serialization_fails(
    tmp_path,
    bad_value,
):
    _portfolio, _snapshot, report = two_position_report()
    object.__setattr__(report.performance, "cash_ratio", bad_value)
    path = tmp_path / "analytics.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = PaperAnalyticsLog(path=path)

    with pytest.raises(ValueError, match="finite|JSON|serializable"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'
```

- [ ] **Step 2: Run analytics tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_analytics.py -q
```

Expected: fail because `polymarket_alpha_lab.analytics` does not exist.

## Part 3: Drawdown Tests

**Goal:** Define executable-NAV drawdown behavior independent of midpoint NAV.

**Files:**

- Modify: `tests/test_analytics.py`
- Production target created in Part 4: `src/polymarket_alpha_lab/analytics.py`

- [ ] **Step 1: Add failing drawdown tests**

Append:

```python
def snapshot_with_exit_nav(marked_at, exit_nav):
    empty_portfolio = build_paper_portfolio([], starting_cash=exit_nav)
    return mark_paper_nav(empty_portfolio, {}, marked_at=marked_at)


def one_position_snapshot(marked_at, bid, ask):
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    return mark_paper_nav(
        portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(OrderBookLevel(bid, Decimal("100")),),
                asks=(OrderBookLevel(ask, Decimal("100")),),
                captured_at=marked_at,
            )
        },
        marked_at=marked_at,
    )


def test_build_paper_drawdown_points_uses_exit_nav_not_midpoint_nav():
    first = one_position_snapshot(
        datetime(2026, 6, 14, tzinfo=UTC),
        Decimal("0.50"),
        Decimal("0.90"),
    )
    second = one_position_snapshot(
        datetime(2026, 6, 15, tzinfo=UTC),
        Decimal("0.40"),
        Decimal("0.40"),
    )
    third = one_position_snapshot(
        datetime(2026, 6, 16, tzinfo=UTC),
        Decimal("0.70"),
        Decimal("0.70"),
    )

    points = build_paper_drawdown_points([third, first, second])

    assert [point.marked_at for point in points] == [
        datetime(2026, 6, 14, tzinfo=UTC),
        datetime(2026, 6, 15, tzinfo=UTC),
        datetime(2026, 6, 16, tzinfo=UTC),
    ]
    assert first.midpoint_nav != first.exit_nav
    assert first.midpoint_nav > second.midpoint_nav
    assert points[0].exit_nav == Decimal("9998.600")
    assert points[0].high_watermark_nav == Decimal("9998.600")
    assert points[0].drawdown == Decimal("0")
    assert points[0].drawdown_ratio == Decimal("0.0000")
    assert points[0].is_new_high is True
    assert points[1].high_watermark_nav == Decimal("9998.600")
    assert points[1].drawdown == Decimal("10.000")
    assert points[1].drawdown_ratio == Decimal("0.0010")
    assert points[1].is_new_high is False
    assert points[2].high_watermark_nav == Decimal("10018.600")
    assert points[2].drawdown == Decimal("0")
    assert points[2].is_new_high is True


def test_build_paper_drawdown_points_rejects_duplicate_marked_at():
    snapshot = snapshot_with_exit_nav(datetime(2026, 6, 14, tzinfo=UTC), Decimal("100"))

    with pytest.raises(ValueError, match="duplicate.*marked_at"):
        build_paper_drawdown_points([snapshot, snapshot])


def test_build_paper_drawdown_points_returns_none_ratio_when_high_watermark_is_zero():
    packet = complete_packet(max_executable_size=Decimal("1"))
    fill = complete_fill(
        requested_size=Decimal("1"),
        filled_size=Decimal("1"),
        unfilled_size=Decimal("0"),
        average_price=Decimal("1"),
        worst_price=Decimal("1"),
        best_bid=Decimal("1"),
        best_ask=Decimal("1"),
        midpoint=Decimal("1"),
        spread=Decimal("0"),
        slippage_estimate=Decimal("0"),
    )
    portfolio = build_paper_portfolio(
        [record_from(packet=packet, fill=fill)],
        starting_cash=Decimal("1"),
    )
    snapshot = mark_paper_nav(
        portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(),
                asks=(OrderBookLevel(Decimal("1"), Decimal("1")),),
                captured_at=datetime(2026, 6, 14, tzinfo=UTC),
            )
        },
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    points = build_paper_drawdown_points([snapshot])

    assert points[0].exit_nav == Decimal("0")
    assert points[0].high_watermark_nav == Decimal("0")
    assert points[0].drawdown == Decimal("0")
    assert points[0].drawdown_ratio is None
    assert points[0].is_new_high is True


def test_build_paper_drawdown_points_treats_equal_high_as_new_high():
    first = snapshot_with_exit_nav(datetime(2026, 6, 14, tzinfo=UTC), Decimal("100"))
    second = snapshot_with_exit_nav(datetime(2026, 6, 15, tzinfo=UTC), Decimal("90"))
    third = snapshot_with_exit_nav(datetime(2026, 6, 16, tzinfo=UTC), Decimal("100"))

    points = build_paper_drawdown_points([first, second, third])

    assert points[2].high_watermark_nav == Decimal("100")
    assert points[2].drawdown == Decimal("0")
    assert points[2].drawdown_ratio == Decimal("0.0000")
    assert points[2].is_new_high is True
```

- [ ] **Step 2: Run drawdown tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_analytics.py -q
```

Expected: fail because drawdown APIs are not implemented.

## Part 4: Analytics Implementation

**Goal:** Implement frozen analytics dataclasses, report builder, drawdown builder, validation, Decimal helpers, and JSONL persistence.

**Files:**

- Create: `src/polymarket_alpha_lab/analytics.py`

- [ ] **Step 1: Implement `analytics.py`**

Implementation requirements:

- Define `__all__` with the ten public API names.
- Import only standard library modules and existing `positions` classes:

```python
import json
from collections import defaultdict
from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from pathlib import Path
from typing import Any, Iterator

from polymarket_alpha_lab.positions import (
    PaperNavSnapshot,
    PaperPortfolio,
    PaperPosition,
    PaperPositionMark,
)
```

- Use `RATIO_QUANTUM = Decimal("0.0001")`.
- Implement local Decimal helpers `_add`, `_subtract`, `_multiply`, `_divide`, `_exact_sum`, `_ratio_or_none`, and `_quantize_ratio`.
- Keep all arithmetic under local high-precision Decimal contexts.
- Reject `float`, `int`, `str`, `bool`, and `None` for required `Decimal` fields; do not coerce numeric values into `Decimal`.
- Reject finite floats during JSON-ready validation instead of serializing them.
- Validate direct dataclass construction through `__post_init__()` methods.
- Join `portfolio.positions` to `snapshot.marks` by `token_id`; reject mismatches.
- Build position rows in `portfolio.positions` order.
- Build buckets for:
  - `token_id`
  - `condition_id`
  - `market_slug`
  - `strategy_type`
  - `risk_tag`
  - `resolution_source`
  - `mark_status`
- Mark `risk_tag` buckets as `additive=False`; all other bucket types are `additive=True`.
- Build breaches from config thresholds in the stable order defined above.
- Build drawdown points from `drawdown_snapshots` if provided, otherwise from `(snapshot,)`.
- Implement `PaperAnalyticsLog.append(report)` with validation-before-open JSONL behavior matching existing logs.

- [ ] **Step 2: Run analytics and scope tests to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_analytics.py tests/test_analytics_scope.py -q
```

Expected: analytics and scope tests pass.

## Part 5: Public Exports And README

**Goal:** Export Node 3 APIs and document the new paper-only status.

**Files:**

- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Modify: `README.md`

- [ ] **Step 1: Add failing package-root export test**

Modify `tests/test_init.py`:

```python
from polymarket_alpha_lab.analytics import (
    PaperAnalyticsBreach,
    PaperAnalyticsBucket,
    PaperAnalyticsConfig,
    PaperAnalyticsLog,
    PaperAnalyticsReport,
    PaperDrawdownPoint,
    PaperPerformanceSummary,
    PaperPositionExposure,
    build_paper_analytics_report,
    build_paper_drawdown_points,
)
```

Add:

```python
def test_level_1b_node_3_public_api_exports():
    expected_exports = {
        "PaperAnalyticsBreach",
        "PaperAnalyticsBucket",
        "PaperAnalyticsConfig",
        "PaperAnalyticsLog",
        "PaperAnalyticsReport",
        "PaperDrawdownPoint",
        "PaperPerformanceSummary",
        "PaperPositionExposure",
        "build_paper_analytics_report",
        "build_paper_drawdown_points",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperAnalyticsBreach is PaperAnalyticsBreach
    assert lab.PaperAnalyticsBucket is PaperAnalyticsBucket
    assert lab.PaperAnalyticsConfig is PaperAnalyticsConfig
    assert lab.PaperAnalyticsLog is PaperAnalyticsLog
    assert lab.PaperAnalyticsReport is PaperAnalyticsReport
    assert lab.PaperDrawdownPoint is PaperDrawdownPoint
    assert lab.PaperPerformanceSummary is PaperPerformanceSummary
    assert lab.PaperPositionExposure is PaperPositionExposure
    assert lab.build_paper_analytics_report is build_paper_analytics_report
    assert lab.build_paper_drawdown_points is build_paper_drawdown_points
```

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py -q
```

Expected: fail because package root does not export Node 3 names.

- [ ] **Step 2: Export analytics APIs from package root**

Modify `src/polymarket_alpha_lab/__init__.py`:

```python
from polymarket_alpha_lab.analytics import (
    PaperAnalyticsBreach,
    PaperAnalyticsBucket,
    PaperAnalyticsConfig,
    PaperAnalyticsLog,
    PaperAnalyticsReport,
    PaperDrawdownPoint,
    PaperPerformanceSummary,
    PaperPositionExposure,
    build_paper_analytics_report,
    build_paper_drawdown_points,
)
```

Preserve every existing package-root public export. Do not remove or reorder unrelated exports. Add only the ten Node 3 names unless Part 0 shows the current pre-Node 3 `__all__` differs from the snapshot below; if it differs, update this plan before editing `__init__.py`.

The expected post-Node 3 `__all__` list, based on the current Part 0 snapshot, is:

```python
__all__ = [
    "MarketScore",
    "MarketSnapshot",
    "NormalizedMarket",
    "OrderBookLevel",
    "OrderBookSnapshot",
    "OutcomeToken",
    "PaperAnalyticsBreach",
    "PaperAnalyticsBucket",
    "PaperAnalyticsConfig",
    "PaperAnalyticsLog",
    "PaperAnalyticsReport",
    "PaperDrawdownPoint",
    "PaperFill",
    "PaperNavLog",
    "PaperNavSnapshot",
    "PaperOrder",
    "PaperPerformanceSummary",
    "PaperPortfolio",
    "PaperPosition",
    "PaperPositionExposure",
    "PaperPositionMark",
    "PaperTradeJournal",
    "PaperTradeRecord",
    "RejectedCandidateLog",
    "RejectedCandidateRecord",
    "ResearchPacket",
    "RiskGateConfig",
    "RiskGateDecision",
    "RiskGateReason",
    "build_paper_analytics_report",
    "build_paper_drawdown_points",
    "build_paper_portfolio",
    "build_research_packet",
    "evaluate_research_packet_risk",
    "mark_paper_nav",
    "simulate_order_book_fill",
]
```

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py -q
```

Expected: pass.

- [ ] **Step 3: Update README**

Modify `README.md`:

1. Update the Phase 1 Scope sentence to include paper-only portfolio analytics, exposure reports, and executable-NAV drawdown reports.
2. Add after Level 1B Node 2 Python API:

```markdown
## Level 1B Node 3 Status

Level 1B Node 3 adds paper-only portfolio analytics, exposure concentration, liquidity-risk, report-only threshold breaches, and executable-NAV drawdown reports derived from paper portfolio and NAV artifacts. It does not fetch market, order-book, or account data, place or cancel orders, authenticate, handle private keys, open user WebSockets, run heartbeat logic, use a trading SDK, create trade proposals, reconcile exchange accounts, scrape websites, or perform compliance/legal/geographic analysis.

## Level 1B Node 3 Python API

Node 3 is exposed through Python APIs:

- Configure report thresholds with `PaperAnalyticsConfig(...)`.
- Build paper analytics reports with `build_paper_analytics_report(portfolio, snapshot, config=..., generated_at=...)`, which returns `PaperAnalyticsReport`.
- Build executable-NAV drawdown points with `build_paper_drawdown_points(snapshots)`.
- Persist report snapshots with `PaperAnalyticsLog(path).append(report)`.
```

3. Add `2026-06-13-level-1b-paper-analytics-risk-exposure.md` to the plan tree.
4. Add `analytics.py` under `src/polymarket_alpha_lab`.
5. Add `test_analytics.py` and `test_analytics_scope.py` under `tests`.

- [ ] **Step 4: Run node-specific tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_analytics.py tests/test_analytics_scope.py tests/test_init.py -q
```

Expected: pass.

## Level 1B Node 3 Completion Criteria

Node 3 is complete only when all of these are true:

- `src/polymarket_alpha_lab/analytics.py` exists and is paper-only.
- Static scope tests prove the module does not import or define forbidden auth/execution/network/proposal/reconciliation/scraping/compliance surfaces.
- `build_paper_analytics_report(...)` consumes `PaperPortfolio` and `PaperNavSnapshot` values only, validates they describe the same paper state, and returns a frozen `PaperAnalyticsReport`.
- The report uses executable `exit_nav` and mark `exit_value`, never midpoint/fair value/model probability/best bid fallback, for executable performance and drawdown metrics.
- The report preserves provenance in per-position exposure rows.
- Exposure buckets are deterministic and cover `token_id`, `condition_id`, `market_slug`, `strategy_type`, `risk_tag`, `resolution_source`, and `mark_status`.
- `risk_tag` buckets are explicitly non-additive.
- Liquidity metrics preserve `fully_executable`, `partially_executable`, and `no_exit_depth` distinctions.
- Drawdown points are computed from supplied `PaperNavSnapshot.exit_nav` history, sorted by `marked_at`, and reject duplicate timestamps.
- Undefined ratios return `None`; all defined ratios are finite `Decimal` values quantized to `Decimal("0.0001")`.
- Direct dataclass construction rejects impossible or non-finite state and enforces `paper_only is True`.
- `PaperAnalyticsLog` appends strict JSONL, serializes Decimal strings and UTC datetimes, and validates before file open.
- Package-root exports and `tests/test_init.py` cover all stable Node 3 APIs.
- README documents Node 3 status and API in the existing concise style and lists new files.
- Required verification gate passes, CodeGraph is up to date, and Claude Opus 4.8 implementation review has no unresolved Critical/Important findings.

## Part 6: Node Verification, Claude Review, Commit, Push, Handoff

**Goal:** Verify, review, commit, push, and document Level 1B Node 3.

**Files:**

- Modify: `docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-risk-exposure.md`
- Stage and commit all Node 3 files after verification and Claude approval.

- [ ] **Step 1: Run full verification gate before Claude implementation review**

Run:

```bash
git status --short --branch --untracked-files=all
.venv/bin/python -m pytest tests/test_analytics.py tests/test_analytics_scope.py tests/test_init.py -q
.venv/bin/python -m pytest tests/test_analytics_scope.py -q
.venv/bin/python -m pytest -q
git diff --check
codegraph status .
```

If CodeGraph is stale:

```bash
codegraph sync .
codegraph status .
```

- [ ] **Step 2: Submit implementation diff and verification output to Claude**

Run a self-contained Claude review with:

```bash
{
  printf '%s\n' 'Review this Level 1B Node 3 implementation for polymarket-alpha-lab.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Return one of: Proceed, Proceed with fixes, or Blocked.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the diff.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; all included verification evidence is present and passing; CodeGraph is up to date.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing or omitted file contents, failed or missing verification output, stale CodeGraph, unsafe scope, or inability to review the full implementation.'
  printf '%s\n' 'Do not return Proceed or Proceed with fixes if any Critical/Important finding remains.'
  printf '%s\n' ''
  printf '%s\n' 'Plan:'
  cat docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-risk-exposure.md
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'Verification run: git status --short --branch --untracked-files=all'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'Verification run: .venv/bin/python -m pytest tests/test_analytics.py tests/test_analytics_scope.py tests/test_init.py -q'
  .venv/bin/python -m pytest tests/test_analytics.py tests/test_analytics_scope.py tests/test_init.py -q
  printf '%s\n' ''
  printf '%s\n' 'Verification run: .venv/bin/python -m pytest tests/test_analytics_scope.py -q'
  .venv/bin/python -m pytest tests/test_analytics_scope.py -q
  printf '%s\n' ''
  printf '%s\n' 'Verification run: .venv/bin/python -m pytest -q'
  .venv/bin/python -m pytest -q
  printf '%s\n' ''
  printf '%s\n' 'Verification run: git diff --check'
  git diff --check
  printf '%s\n' ''
  printf '%s\n' 'Verification run: codegraph status .'
  codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Verification run: conditional codegraph sync .'
  if .venv/bin/python - <<'PY'
import json
import subprocess
import sys

result = subprocess.run(
    ["codegraph", "status", "--json", "."],
    check=True,
    capture_output=True,
    text=True,
)
status = json.loads(result.stdout)
pending = status.get("pendingChanges") or {}
needs_sync = (
    any(pending.get(key, 0) for key in ("added", "modified", "removed"))
    or bool(status.get("worktreeMismatch"))
    or bool(status.get("reindexRecommended"))
)
sys.exit(1 if needs_sync else 0)
PY
  then
    printf '%s\n' 'codegraph sync .: not required'
  else
    codegraph sync .
  fi
  printf '%s\n' ''
  printf '%s\n' 'Verification run: follow-up codegraph status . after conditional sync'
  codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Tracked diff:'
  git diff -- README.md src/polymarket_alpha_lab/__init__.py src/polymarket_alpha_lab/analytics.py tests/test_analytics.py tests/test_analytics_scope.py tests/test_init.py docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-risk-exposure.md
  printf '%s\n' ''
  printf '%s\n' 'Untracked file diffs or contents:'
  unexpected_untracked_found=0
  expected_untracked_paths='
README.md
src/polymarket_alpha_lab/__init__.py
src/polymarket_alpha_lab/analytics.py
tests/test_analytics.py
tests/test_analytics_scope.py
tests/test_init.py
docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-risk-exposure.md
'
  untracked_paths="$(git ls-files --others --exclude-standard)"
  if [ -z "$untracked_paths" ]; then
    printf '%s\n' 'none'
  else
    while IFS= read -r path; do
    if ! printf '%s\n' "$expected_untracked_paths" | grep -Fx -- "$path" >/dev/null; then
      unexpected_untracked_found=1
      printf '\n--- UNEXPECTED UNTRACKED FILE: %s ---\n' "$path"
    fi
    if [ -f "$path" ]; then
      printf '\n--- BEGIN UNTRACKED FILE DIFF: %s ---\n' "$path"
      git diff --no-index -- /dev/null "$path" || true
      printf '\n--- END UNTRACKED FILE DIFF: %s ---\n' "$path"
    else
      printf '\n--- UNTRACKED PATH IS NOT A REGULAR FILE: %s ---\n' "$path"
    fi
    done <<EOF_UNTRACKED
$untracked_paths
EOF_UNTRACKED
  fi
  if [ "$unexpected_untracked_found" -eq 1 ]; then
    printf '%s\n' 'BLOCKING REVIEW ISSUE: unexpected untracked files are present.'
  fi
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Run this review only after the fresh verification commands above have already passed. Accepted implementation-review terminal state: a fresh Claude review response that explicitly reports zero Critical findings, zero Important findings, all required file contents present, all verification evidence passing, CodeGraph up to date, and a verdict of `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count, ambiguous verdict, failed verification, stale CodeGraph result, or omitted untracked file content is treated as `Blocked`. Resolve all Critical/Important findings and repeat review until no Critical/Important findings remain.

- [ ] **Step 3: Stage implementation files and run cached diff check**

Run:

```bash
git add README.md src/polymarket_alpha_lab/__init__.py src/polymarket_alpha_lab/analytics.py tests/test_analytics.py tests/test_analytics_scope.py tests/test_init.py docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-risk-exposure.md
git diff --cached --check
```

Expected: cached diff check has no output and exit code 0. Record this command result for the Handoff Summary.

- [ ] **Step 4: Record Handoff Summary, restage the plan, and rerun cached diff check**

Append:

```text
## Handoff Summary

- Repo status: branch, latest commit SHA if known outside the committed file, pushed/not pushed, clean/dirty state.
- Git status output: paste `git status --short --branch --untracked-files=all`.
- Verified commands:
  - `git status --short --branch --untracked-files=all`: pass/fail and notable output.
  - `.venv/bin/python -m pytest tests/test_analytics.py tests/test_analytics_scope.py tests/test_init.py -q`: pass/fail and test count.
  - `.venv/bin/python -m pytest tests/test_analytics_scope.py -q`: pass/fail and test count.
  - `.venv/bin/python -m pytest -q`: pass/fail and test count.
  - `git diff --check`: pass/fail.
  - `codegraph status .`: up to date or stale.
  - `codegraph sync .`: run/not run and result.
  - follow-up `codegraph status .`: up to date or stale.
  - `git diff --cached --check`: pass/fail.
- Untracked files: list or `none`.
- Uncommitted files: list or `none`.
- Data-integrity checks: paper-only scope, forbidden-surface static tests, portfolio/snapshot join validation, executable-NAV-only performance, no midpoint fallback, deterministic exposure buckets, risk-tag non-additive buckets, drawdown from exit NAV, Decimal-only finite math, undefined ratio handling, JSONL validation-before-open behavior.
- Claude review: model `claude-opus-4-8`, effort `max`, review scope, explicit verdict, unresolved findings.
- Commit/push: commit hash, remote branch, push result.
- Next step: one concrete next action for the next Level 1B node.
```

Because this handoff is written before the final commit exists, set the commit hash field to `pending final commit` in the committed handoff and report the final commit hash in the assistant final response after push.

After appending the handoff, run:

```bash
git add docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-risk-exposure.md
git diff --cached --check
```

Expected: cached diff check still has no output and exit code 0.

- [ ] **Step 5: Commit and push**

Run:

```bash
git commit -m "feat: add paper analytics reports"
git push
```

Expected: commit succeeds and push updates `origin/main`. After push, run `git status --short --branch --untracked-files=all`; expected output is `## main...origin/main` with no additional file lines. Report the final commit hash and push result in the assistant final response.

## Handoff Summary

- Repo status: branch `main`, upstream `origin/main`, latest pre-node commit `00efee38dad8a52e4bf8acfebdea01224db15926`, final node commit hash `pending final commit`, push result `pending final push`.
- Git status output before final commit:

```text
## main...origin/main
M  README.md
A  docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-risk-exposure.md
M  src/polymarket_alpha_lab/__init__.py
A  src/polymarket_alpha_lab/analytics.py
A  tests/test_analytics.py
A  tests/test_analytics_scope.py
M  tests/test_init.py
```

- Verified commands:
  - `git status --short --branch --untracked-files=all`: passed; before staging it listed only expected Node 3 tracked edits plus expected untracked plan, analytics module, and tests.
  - `.venv/bin/python -m pytest tests/test_analytics.py tests/test_analytics_scope.py tests/test_init.py -q`: passed, `41 passed in 0.34s`.
  - `.venv/bin/python -m pytest tests/test_analytics_scope.py -q`: passed, `5 passed in 0.12s`.
  - `.venv/bin/python -m pytest -q`: passed, `302 passed in 0.78s`.
  - `git diff --check`: passed with no output.
  - `codegraph status .`: initially reported pending changes after new Node 3 Python files.
  - `codegraph sync .`: run; synced 3 changed Python files.
  - follow-up `codegraph status .`: passed; index is up to date with 31 files, 713 nodes, 2,455 edges.
  - `git diff --cached --check`: passed with no output after staging Node 3 files.

- Untracked files: none after staging the planned Node 3 files.
- Uncommitted files: staged `README.md`, this plan, `src/polymarket_alpha_lab/__init__.py`, `src/polymarket_alpha_lab/analytics.py`, `tests/test_analytics.py`, `tests/test_analytics_scope.py`, and `tests/test_init.py`.
- Data-integrity checks: static scope tests confirm paper-only boundaries and forbidden-surface exclusions; report builder validates matching `PaperPortfolio` and `PaperNavSnapshot` token/state; executable performance uses `PaperNavSnapshot.exit_nav` and `PaperPositionMark.exit_value`; midpoint fields do not fall back to executable values; exposure buckets are deterministic; risk-tag buckets are non-additive; drawdown uses exit NAV and rejects duplicate timestamps; all defined ratios use finite `Decimal` values quantized to `Decimal("0.0001")`; undefined ratios return `None`; JSONL append validates and serializes before opening the file.
- Claude review: model `claude-opus-4-8`, effort `max`, read-only implementation review covering plan, status, verification output, tracked diff, and all untracked Node 3 file contents. Result: Critical `None`, Important `None`, Minor `None`, `Verdict: Proceed`. Unresolved findings: none.
- Commit/push: commit hash `pending final commit`; remote branch `origin/main`; push result `pending final push`.
- Next step: draft a reviewed Level 1B Node 4 plan for paper-only analytics history validation from existing local paper artifacts before adding any new execution or live-capital surfaces.
