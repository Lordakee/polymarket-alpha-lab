# Level 1B Paper Forecast Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only forecast evidence layer that scores caller-supplied paper forecast/edge observations for Gate 4 review without fetching outcomes, creating proposals, or touching live-execution surfaces.

**Architecture:** Create `forecast_evidence.py` as a standalone derived layer over strict caller-provided `PaperForecastEvidenceObservation` values. It computes deterministic probability-loss summaries, probability-bucket error rows, executable-edge evidence, gate results, report status, and append-only JSONL reports. The node deliberately does not integrate back into `analytics_history.py`; a later node can wire `PaperForecastEvidenceReport` into the Node 4 `forecast_edge_quality` row once the evidence contract is stable.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, JSONL files, `pytest`, CodeGraph.

---

## Review And Execution Protocol

1. Submit this plan to Claude Code with model `claude-opus-4-8`, effort `max`, read-only permissions before implementation.
2. Do not implement Level 1B Node 5 until Claude Code returns `Proceed` or `Proceed with fixes` and every Critical/Important finding is resolved.
3. Before the node commit and push, run and record this required gate:
   - `git status --short --branch --untracked-files=all`; explicitly list untracked files or `none`.
   - `.venv/bin/python -m pytest tests/test_forecast_evidence.py tests/test_forecast_evidence_scope.py tests/test_init.py -q`.
   - `.venv/bin/python -m pytest tests/test_forecast_evidence_scope.py -q`.
   - `.venv/bin/python -m pytest -q`.
   - `git diff --check`; after staging, also run `git diff --cached --check`.
   - `codegraph status .`; if stale or out of date, run `codegraph sync .` and then `codegraph status .` again.
   - Claude Code implementation review with `claude-opus-4-8`, `--effort max`, covering the node diff, untracked files, verification output, and the next concrete roadmap step.
4. Do not commit or push the node until all required gate items pass, Claude returns `Proceed` or `Proceed with fixes`, and all Claude Critical/Important findings are resolved.
5. After the node, write a Handoff Summary with repo status, verified commands, uncommitted files, Claude review status, pending commit/push fields, and next step. Report the final commit hash and push result in the assistant final response after push.

Plan review command before any implementation:

```bash
{
  printf '%s\n' 'Review this Level 1B Node 5 implementation plan for polymarket-alpha-lab before implementation.'
  printf '%s\n' 'This is a read-only, self-contained plan review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions or plan text.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; plan is implementable as written.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing required review material, unsafe scope, or plan ambiguity that could cause incorrect implementation.'
  printf '%s\n' 'Review specifically: paper-only scope boundaries, forbidden surfaces, target files, TDD steps, Gate 4 semantics, public naming constraints, CodeGraph usage, implementation review self-containment, untracked-file handling, and Critical/Important findings resolution before implementation/commit/push.'
  printf '%s\n' 'Before the final verdict line, report finding counts exactly as:'
  printf '%s\n' 'Critical findings: <integer>'
  printf '%s\n' 'Important findings: <integer>'
  printf '%s\n' 'Minor findings: <integer>'
  printf '%s\n' 'Use 0 for empty categories; do not use "none" in count fields.'
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
  printf '%s\n' 'CodeGraph status:'
  codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Current package-root exports source:'
  codegraph node src/polymarket_alpha_lab/__init__.py
  printf '%s\n' ''
  printf '%s\n' 'Current package-root export tests:'
  codegraph node tests/test_init.py
  printf '%s\n' ''
  printf '%s\n' 'Current analytics-history source and JSONL log pattern:'
  codegraph node src/polymarket_alpha_lab/analytics_history.py
  printf '%s\n' ''
  printf '%s\n' 'Current README, for planned documentation placement:'
  sed -n '1,260p' README.md
  printf '%s\n' ''
  printf '%s\n' 'Existing package-root scope constraints:'
  sed -n '1,340p' tests/test_analytics_scope.py
  printf '%s\n' ''
  printf '%s\n' 'Existing analytics-history scope constraints:'
  sed -n '1,340p' tests/test_analytics_history_scope.py
  printf '%s\n' ''
  printf '%s\n' 'Node 4 handoff and current plan:'
  cat docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-history-validation.md
  printf '%s\n' ''
  printf '%s\n' 'Node 5 plan:'
  cat docs/superpowers/plans/2026-06-13-level-1b-paper-forecast-evidence.md
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted plan-review terminal state: a fresh Claude review response that explicitly reports zero Critical findings, zero Important findings, and a verdict of `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count, ambiguous verdict, unsafe scope, or missing review material is treated as `Blocked`. After fixing any Critical or Important plan-review finding, rerun the same self-contained Claude plan-review prompt and do not implement until the rerun reaches an accepted terminal state.

Recorded Claude plan-review result:

- Review date: 2026-06-14 UTC.
- Model: `claude-opus-4-8`.
- Effort: `max`.
- Scope reviewed: paper-only scope boundaries, forbidden surfaces, target files, TDD steps, Gate 4 semantics, public naming constraints, CodeGraph usage, implementation review self-containment, untracked-file handling, and Critical/Important resolution before implementation/commit/push.
- Critical findings: 0.
- Important findings: 0.
- Minor findings: 4.
- Verdict: `Proceed with fixes`.
- Unresolved findings: four Minor items only: gate result payload prose could be more explicit; standalone forbidden imports could explicitly list analytics/history even though the whitelist blocks them; partial-role message tokens are pinned by tests rather than prose; bucket widths that do not evenly divide `1.0000` are not directly tested. None block implementation under the accepted terminal-state rule.

Level 1B Node 5 must not add:

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
- external outcome loaders
- market/order-book/account data downloaders
- settlement or payout workflow
- scraping, crawling, browser automation, CAPTCHA, anti-bot, or website bypass logic
- compliance, legal, jurisdiction, geofence, or geographic-access analysis
- CLI commands
- dashboards or UI

## Level 1B Node 5 Scope

This node adds only derived paper forecast evidence:

- strict caller-supplied paper forecast observations
- probability-loss summaries from predicted probability versus actual paper outcome value
- probability-bucket evidence rows that approximate Gate 4 bucket review without using public names that trip existing `brier` or `calibration` export guards
- executable-edge evidence from theoretical edge, executable edge, fill probability, residual exposure, and paper return ratios supplied by callers
- deterministic Gate 4 result rows for data integrity, sample size, probability quality, executable-edge quality, and residual exposure
- deterministic report status: `incomplete_data`, `insufficient_evidence`, `blocked_by_quality`, or `paper_review_ready`
- append-only JSONL persistence for forecast evidence reports
- package-root exports and README status/API text

This node intentionally defers:

- loading market outcomes from APIs, files, websites, or chains
- resolving markets or settling positions
- modifying `analytics_history.py` or changing the Node 4 `forecast_edge_quality` row
- strategy validation packets
- proposal generation or human-approval workflows
- dashboards or UI
- CLI commands
- exchange reconciliation or live execution readiness claims

`paper_review_ready` is a Node 5 evidence-artifact status only. It means the paper forecast evidence report is ready for human review inside Level 1B; it does not mean the strategy has passed every validation gate, does not authorize proposal generation, and is not a promotion signal for live or proposal-mode execution.

## Public Naming Constraints

Existing package-root scope tests reject public exports containing these fragments:

- `resolvedoutcome`
- `brier`
- `calibration`
- `execution`
- `proposal`
- `settlement`
- `legal`
- `geographic`
- `auth`
- credential/key/signing/account/broker/client/transport/websocket fragments

Therefore Node 5 public names must use `ForecastEvidence` wording and must not expose names containing `Brier`, `Calibration`, `ResolvedOutcome`, `Execution`, `Proposal`, or `Settlement`.

## Target File Structure

- Create: `src/polymarket_alpha_lab/forecast_evidence.py`
  - Frozen evidence dataclasses, pure evidence builder, strict JSONL forecast evidence log.
- Create: `tests/test_forecast_evidence.py`
  - TDD tests for evidence summaries, bucket rows, validation gate rows, edge cases, validation, and JSONL persistence.
- Create: `tests/test_forecast_evidence_scope.py`
  - Static forbidden-surface tests for Node 5 module and public exports.
- Modify: `src/polymarket_alpha_lab/__init__.py`
  - Export stable Level 1B Node 5 public APIs with names that pass existing package-root scope tests.
- Modify: `tests/test_init.py`
  - Package-root export contract for forecast evidence APIs.
- Modify: `README.md`
  - Add Level 1B Node 5 paper-only status, Python API notes, and repository tree entries.
- Modify: `docs/superpowers/plans/2026-06-13-level-1b-paper-forecast-evidence.md`
  - Update gate results and handoff notes as the node is completed.

## Public API Contract

Create these names:

```python
from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceBucket,
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceGateResult,
    PaperForecastEvidenceLog,
    PaperForecastEvidenceObservation,
    PaperForecastEvidenceReport,
    build_paper_forecast_evidence_report,
)
```

Export all seven from `polymarket_alpha_lab.__init__`.

## Forecast Evidence Semantics

`build_paper_forecast_evidence_report(observations, *, config, generated_at)` returns `PaperForecastEvidenceReport`.

- `observations` must be an iterable of `PaperForecastEvidenceObservation` values and must reject `str`/`bytes`.
- `config` must be a `PaperForecastEvidenceConfig`; invalid config objects raise `ValueError` before a report is constructed.
- Empty `observations` is allowed. It returns a report with `observation_count == 0`, no bucket rows, every gate result set to `incomplete`, and `status == "incomplete_data"`.
- Observations are sorted by `observed_at`; output uses sorted order.
- Duplicate `(observed_at, token_id, source_packet_id)` values raise `ValueError` to avoid ambiguous evidence ordering.
- Every input observation must have `paper_only is True`.
- `generated_at` must be a `datetime`; naive datetimes are treated as UTC.
- The builder never fetches data, reads account state, uses a client/transport, downloads outcomes, scrapes websites, settles markets, places/cancels orders, reconciles accounts, or creates proposals.
- The builder treats caller-supplied observations as paper evidence. It does not infer actual outcomes, settlement state, executable prices, or paper returns from external data.
- All numeric values in the evidence report are finite `Decimal` values or `None`.
- Defined ratio-like values are quantized locally to `Decimal("0.0001")`.
- Undefined ratio values return `None`, never `NaN`, `Infinity`, or zero.

Observation roles:

- A probability observation has both `predicted_probability` and `actual_outcome_value`.
- An executable-edge observation has `theoretical_edge_ratio`, `executable_edge_ratio`, `fill_probability`, `residual_exposure_ratio`, and `paper_return_ratio`.
- An observation may carry both roles.
- An observation must carry at least one role.
- Partially populated roles are invalid even when the other role is complete; callers must omit every field for an unused role or provide every field for a used role.
- `actual_outcome_value` is a paper evidence value supplied by the caller: `Decimal("0")` or `Decimal("1")`. It is not loaded by this node.

Derived probability metrics:

- Per-observation probability loss: `(predicted_probability - actual_outcome_value) ** 2`, quantized to `Decimal("0.0001")`.
- `mean_probability_loss`: average of probability losses, or `None` when no probability observations exist.
- Bucket rows are built from probability observations only.
- Buckets use fixed width from `config.probability_bucket_width`, default `Decimal("0.2000")`.
- `config.probability_bucket_width` must be a finite `Decimal` greater than `Decimal("0")` and less than or equal to `Decimal("1")`.
- Bucket label format is `"0.6000-0.8000"` using lower-inclusive, upper-exclusive ranges except the final bucket includes `1.0000`.
- Bucket rows are returned sorted by `lower_probability`, then `upper_probability`, regardless of the order in which sorted observations first enter buckets.
- `observed_frequency`: average `actual_outcome_value` in the bucket.
- `mean_predicted_probability`: average predicted probability in the bucket.
- `bucket_error`: absolute difference between bucket mean prediction and observed frequency.
- `worst_bucket_error`: max bucket error, or `None` when no bucket rows exist.

Derived executable-edge metrics:

- Per-observation edge gap: `max(theoretical_edge_ratio - executable_edge_ratio, Decimal("0"))`, quantized to `Decimal("0.0001")`.
- `mean_edge_gap_ratio`: average edge gap across executable-edge observations, or `None` when no executable-edge observations exist.
- `positive_edge_hit_rate`: fraction of executable-edge observations with `paper_return_ratio > Decimal("0")`, quantized to `Decimal("0.0001")`, or `None` when no executable-edge observations exist.
- `worst_residual_exposure_ratio`: max residual exposure ratio across executable-edge observations, or `None` when no executable-edge observations exist.

Validation gate rows:

1. `data_integrity`: `pass` when at least one observation exists, observations are paper-only, sorted without duplicate evidence keys, and direct dataclass validation passed; `incomplete` when no observations exist. Invalid inputs raise `ValueError` before a report is constructed.
2. `sample_size`: `pass` when probability and executable-edge observation counts meet config thresholds; `fail` when observations exist and either threshold is missed; `incomplete` when no observations exist.
3. `probability_quality`: `pass` when probability observations exist and `mean_probability_loss` plus `worst_bucket_error` are within config thresholds; `fail` when either metric breaches; `incomplete` when no probability observations exist.
4. `executable_edge_quality`: `pass` when executable-edge observations exist and `mean_edge_gap_ratio` plus `positive_edge_hit_rate` are within config thresholds; `fail` when either metric breaches; `incomplete` when no executable-edge observations exist.
5. `residual_exposure`: `pass` when executable-edge observations exist and `worst_residual_exposure_ratio` is within config threshold; `fail` when the metric breaches; `incomplete` when no executable-edge observations exist.

Final status:

- `incomplete_data`: no observations or data-integrity gate is incomplete.
- `blocked_by_quality`: probability-quality, executable-edge-quality, or residual-exposure gate fails.
- `insufficient_evidence`: sample-size gate fails while quality gates do not fail, or any non-data-integrity gate is `incomplete`.
- `paper_review_ready`: data integrity, sample-size, probability-quality, executable-edge-quality, and residual-exposure gates pass. This status means the evidence artifact is ready for human review only, not that the strategy is approved for proposal or live execution.

## Planned Dataclasses

`forecast_evidence.py` should use frozen dataclasses and direct construction validation:

```python
@dataclass(frozen=True)
class PaperForecastEvidenceConfig:
    config_version: str
    min_probability_observations: int = 30
    min_edge_observations: int = 30
    probability_bucket_width: Decimal = Decimal("0.2000")
    max_mean_probability_loss: Decimal = Decimal("0.2500")
    max_bucket_error: Decimal = Decimal("0.2000")
    max_mean_edge_gap_ratio: Decimal = Decimal("0.0500")
    min_positive_edge_hit_rate: Decimal = Decimal("0.5000")
    max_residual_exposure_ratio: Decimal = Decimal("0.1000")


@dataclass(frozen=True)
class PaperForecastEvidenceObservation:
    observed_at: datetime
    source_packet_id: str
    condition_id: str
    token_id: str
    market_slug: str
    strategy_type: str
    risk_tags: tuple[str, ...]
    predicted_probability: Decimal | None = None
    actual_outcome_value: Decimal | None = None
    theoretical_edge_ratio: Decimal | None = None
    executable_edge_ratio: Decimal | None = None
    fill_probability: Decimal | None = None
    residual_exposure_ratio: Decimal | None = None
    paper_return_ratio: Decimal | None = None
    paper_only: bool = True


@dataclass(frozen=True)
class PaperForecastEvidenceBucket:
    bucket_label: str
    lower_probability: Decimal
    upper_probability: Decimal
    observation_count: int
    mean_predicted_probability: Decimal
    observed_frequency: Decimal
    bucket_error: Decimal
    mean_probability_loss: Decimal


@dataclass(frozen=True)
class PaperForecastEvidenceGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None


@dataclass(frozen=True)
class PaperForecastEvidenceReport:
    generated_at: datetime
    config_version: str
    first_observed_at: datetime | None
    last_observed_at: datetime | None
    observation_count: int
    probability_observation_count: int
    edge_observation_count: int
    unique_market_count: int
    unique_strategy_count: int
    unique_risk_tag_count: int
    mean_probability_loss: Decimal | None
    worst_bucket_error: Decimal | None
    mean_edge_gap_ratio: Decimal | None
    positive_edge_hit_rate: Decimal | None
    worst_residual_exposure_ratio: Decimal | None
    status: str
    gate_results: tuple[PaperForecastEvidenceGateResult, ...]
    buckets: tuple[PaperForecastEvidenceBucket, ...]
    paper_only: bool = True


@dataclass(frozen=True)
class PaperForecastEvidenceLog:
    path: Path | str
```

`PaperForecastEvidenceLog` exposes one public method:

```python
append(self, report: PaperForecastEvidenceReport) -> None
```

Allowed gate names:

- `data_integrity`
- `sample_size`
- `probability_quality`
- `executable_edge_quality`
- `residual_exposure`

Allowed gate result statuses:

- `pass`
- `fail`
- `incomplete`

Allowed report statuses:

- `incomplete_data`
- `insufficient_evidence`
- `blocked_by_quality`
- `paper_review_ready`

Direct dataclass construction must validate every public enum-like string and reject floats in `observed_value` or `threshold`.

## Part 0: Existing Contract Check

**Goal:** Reconfirm current public export constraints, Node 4 handoff, and log patterns before implementing forecast evidence.

**Files:**

- Inspect: `AGENTS.md`
- Inspect: `docs/research/validation-gates.md`
- Inspect: `docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md`
- Inspect: `docs/superpowers/plans/2026-06-13-level-1b-paper-analytics-history-validation.md`
- Inspect: `tests/test_analytics_scope.py`
- Inspect: `tests/test_analytics_history_scope.py`
- Inspect: `src/polymarket_alpha_lab/__init__.py`
- Inspect: `tests/test_init.py`
- Inspect: `src/polymarket_alpha_lab/analytics_history.py`

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
codegraph explore "forecast evidence package root exports scope forbidden public exports analytics history log JSON ready"
codegraph node src/polymarket_alpha_lab/__init__.py
codegraph node tests/test_init.py
codegraph node tests/test_analytics_scope.py
codegraph node tests/test_analytics_history_scope.py
codegraph node src/polymarket_alpha_lab/analytics_history.py
```

Expected: confirm package-root public export guards still reject `brier`, `calibration`, `resolvedoutcome`, and `execution`; confirm `PaperForecastEvidence*` and `build_paper_forecast_evidence_report` naming is safe; confirm JSONL validation-before-open pattern from Node 4 is reusable.

## Part 1: Static Paper-Only Boundary Tests

**Goal:** Lock Node 5 scope before forecast evidence implementation.

**Files:**

- Create: `tests/test_forecast_evidence_scope.py`
- Production target created in Part 3: `src/polymarket_alpha_lab/forecast_evidence.py`

- [ ] **Step 1: Write failing forbidden-surface tests**

Create `tests/test_forecast_evidence_scope.py` with:

```python
import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FORECAST_EVIDENCE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "forecast_evidence.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"


EXPECTED_FORECAST_EVIDENCE_EXPORTS = {
    "PaperForecastEvidenceBucket",
    "PaperForecastEvidenceConfig",
    "PaperForecastEvidenceGateResult",
    "PaperForecastEvidenceLog",
    "PaperForecastEvidenceObservation",
    "PaperForecastEvidenceReport",
    "build_paper_forecast_evidence_report",
}

ALLOWED_IMPORT_PREFIXES = {
    "json",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
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
    "historicalloader",
    "externalhistory",
    "pricehistoryapi",
    "backfill",
    "download",
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


def parse_forecast_evidence():
    return ast.parse(FORECAST_EVIDENCE_PATH.read_text(encoding="utf-8"))


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


def test_forecast_evidence_module_imports_only_allowed_dependencies():
    tree = parse_forecast_evidence()
    for module_name in imported_modules(tree):
        assert any(
            module_name == allowed or module_name.startswith(f"{allowed}.")
            for allowed in ALLOWED_IMPORT_PREFIXES
        ), module_name


def test_forecast_evidence_module_does_not_import_forbidden_surfaces():
    tree = parse_forecast_evidence()
    for module_name in imported_modules(tree):
        assert not any(
            module_name == forbidden or module_name.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_forecast_evidence_module_does_not_define_forbidden_names():
    tree = parse_forecast_evidence()
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


def test_forecast_evidence_public_exports_are_paper_report_only():
    tree = parse_forecast_evidence()
    assigned_exports = module_exports(tree)
    assert set(assigned_exports) == EXPECTED_FORECAST_EVIDENCE_EXPORTS
    for name in assigned_exports:
        assert name.startswith("PaperForecastEvidence") or name.startswith(
            "build_paper_forecast_evidence"
        )
        normalized_name = normalize_identifier(name)
        assert not any(
            fragment in normalized_name for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
        )


def test_package_root_exports_do_not_leak_forbidden_forecast_evidence_surfaces():
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
.venv/bin/python -m pytest tests/test_forecast_evidence_scope.py -q
```

Expected: fail because `src/polymarket_alpha_lab/forecast_evidence.py` does not exist.

## Part 2: Forecast Evidence Behavior Tests

**Goal:** Define the Node 5 behavior before production code.

**Files:**

- Create: `tests/test_forecast_evidence.py`
- Production target created in Part 3: `src/polymarket_alpha_lab/forecast_evidence.py`

- [ ] **Step 1: Write failing forecast evidence tests**

Create `tests/test_forecast_evidence.py` with:

```python
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceGateResult,
    PaperForecastEvidenceLog,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)


def evidence_observation(
    index: int,
    *,
    probability: Decimal,
    actual: Decimal,
    theoretical_edge: Decimal,
    executable_edge: Decimal,
    fill_probability: Decimal,
    residual: Decimal,
    paper_return: Decimal,
) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=datetime(2026, 8, 1, tzinfo=UTC) + timedelta(days=index),
        source_packet_id=f"packet-{index}",
        condition_id=f"condition-{index % 2}",
        token_id=f"token-{index}",
        market_slug=f"market-{index % 2}",
        strategy_type="relative_value" if index % 2 else "market_quality",
        risk_tags=("liquidity", "event-risk") if index == 1 else ("liquidity",),
        predicted_probability=probability,
        actual_outcome_value=actual,
        theoretical_edge_ratio=theoretical_edge,
        executable_edge_ratio=executable_edge,
        fill_probability=fill_probability,
        residual_exposure_ratio=residual,
        paper_return_ratio=paper_return,
    )


def sample_observations():
    return (
        evidence_observation(
            1,
            probability=Decimal("0.7000"),
            actual=Decimal("1"),
            theoretical_edge=Decimal("0.1200"),
            executable_edge=Decimal("0.0900"),
            fill_probability=Decimal("0.8000"),
            residual=Decimal("0.0000"),
            paper_return=Decimal("0.1000"),
        ),
        evidence_observation(
            2,
            probability=Decimal("0.6000"),
            actual=Decimal("0"),
            theoretical_edge=Decimal("0.0800"),
            executable_edge=Decimal("0.0300"),
            fill_probability=Decimal("0.6500"),
            residual=Decimal("0.1000"),
            paper_return=Decimal("-0.0200"),
        ),
        evidence_observation(
            3,
            probability=Decimal("0.3000"),
            actual=Decimal("0"),
            theoretical_edge=Decimal("0.0500"),
            executable_edge=Decimal("0.0400"),
            fill_probability=Decimal("0.7000"),
            residual=Decimal("0.0000"),
            paper_return=Decimal("0.0300"),
        ),
    )
```

Add tests:

```python
def test_build_paper_forecast_evidence_report_summarizes_observations():
    observations = sample_observations()

    report = build_paper_forecast_evidence_report(
        [observations[2], observations[0], observations[1]],
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=3,
            min_edge_observations=3,
            max_mean_probability_loss=Decimal("0.2000"),
            max_bucket_error=Decimal("0.3500"),
            max_mean_edge_gap_ratio=Decimal("0.0500"),
            min_positive_edge_hit_rate=Decimal("0.6000"),
            max_residual_exposure_ratio=Decimal("0.1000"),
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    assert report.generated_at == datetime(2026, 8, 10, tzinfo=UTC)
    assert report.config_version == "node5-test"
    assert report.first_observed_at == observations[0].observed_at
    assert report.last_observed_at == observations[2].observed_at
    assert report.observation_count == 3
    assert report.probability_observation_count == 3
    assert report.edge_observation_count == 3
    assert report.unique_market_count == 2
    assert report.unique_strategy_count == 2
    assert report.unique_risk_tag_count == 2
    assert report.mean_probability_loss == Decimal("0.1800")
    assert report.worst_bucket_error == Decimal("0.3000")
    assert report.mean_edge_gap_ratio == Decimal("0.0300")
    assert report.positive_edge_hit_rate == Decimal("0.6667")
    assert report.worst_residual_exposure_ratio == Decimal("0.1000")
    assert report.status == "paper_review_ready"
    assert [bucket.bucket_label for bucket in report.buckets] == [
        "0.2000-0.4000",
        "0.6000-0.8000",
    ]
    assert report.buckets[0].lower_probability == Decimal("0.2000")
    assert report.buckets[0].upper_probability == Decimal("0.4000")
    assert report.buckets[0].mean_predicted_probability == Decimal("0.3000")
    assert report.buckets[0].observed_frequency == Decimal("0.0000")
    assert report.buckets[0].bucket_error == Decimal("0.3000")
    assert report.buckets[0].mean_probability_loss == Decimal("0.0900")
    assert report.buckets[1].lower_probability == Decimal("0.6000")
    assert report.buckets[1].upper_probability == Decimal("0.8000")
    assert report.buckets[1].mean_predicted_probability == Decimal("0.6500")
    assert report.buckets[1].observed_frequency == Decimal("0.5000")
    assert report.buckets[1].bucket_error == Decimal("0.1500")
    assert report.buckets[1].mean_probability_loss == Decimal("0.2250")
```

```python
def test_build_paper_forecast_evidence_report_records_gate_results():
    observations = sample_observations()

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=4,
            min_edge_observations=4,
            max_mean_probability_loss=Decimal("0.1000"),
            max_bucket_error=Decimal("0.3500"),
            max_mean_edge_gap_ratio=Decimal("0.0500"),
            min_positive_edge_hit_rate=Decimal("0.6000"),
            max_residual_exposure_ratio=Decimal("0.1000"),
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert list(gates) == [
        "data_integrity",
        "sample_size",
        "probability_quality",
        "executable_edge_quality",
        "residual_exposure",
    ]
    assert gates["data_integrity"].status == "pass"
    assert gates["sample_size"].status == "fail"
    assert gates["probability_quality"].status == "fail"
    assert gates["executable_edge_quality"].status == "pass"
    assert gates["residual_exposure"].status == "pass"
    assert "mean_probability_loss" in str(gates["probability_quality"].observed_value)
    assert report.status == "blocked_by_quality"
```

```python
def test_build_paper_forecast_evidence_report_marks_insufficient_evidence_when_only_sample_fails():
    observations = sample_observations()

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=4,
            min_edge_observations=4,
            max_mean_probability_loss=Decimal("0.2000"),
            max_bucket_error=Decimal("0.3500"),
            max_mean_edge_gap_ratio=Decimal("0.0500"),
            min_positive_edge_hit_rate=Decimal("0.6000"),
            max_residual_exposure_ratio=Decimal("0.1000"),
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["sample_size"].status == "fail"
    assert gates["probability_quality"].status == "pass"
    assert gates["executable_edge_quality"].status == "pass"
    assert gates["residual_exposure"].status == "pass"
    assert report.status == "insufficient_evidence"
```

```python
def test_build_paper_forecast_evidence_report_handles_empty_input():
    report = build_paper_forecast_evidence_report(
        [],
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    assert report.observation_count == 0
    assert report.first_observed_at is None
    assert report.last_observed_at is None
    assert report.mean_probability_loss is None
    assert report.buckets == ()
    assert report.status == "incomplete_data"
    assert {gate.status for gate in report.gate_results} == {"incomplete"}
```

```python
def test_build_paper_forecast_evidence_report_supports_probability_only_observations():
    observations = (
        replace(
            sample_observations()[0],
            theoretical_edge_ratio=None,
            executable_edge_ratio=None,
            fill_probability=None,
            residual_exposure_ratio=None,
            paper_return_ratio=None,
        ),
        replace(
            sample_observations()[1],
            theoretical_edge_ratio=None,
            executable_edge_ratio=None,
            fill_probability=None,
            residual_exposure_ratio=None,
            paper_return_ratio=None,
        ),
    )

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=2,
            min_edge_observations=0,
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert report.probability_observation_count == 2
    assert report.edge_observation_count == 0
    assert report.mean_probability_loss == Decimal("0.2250")
    assert report.mean_edge_gap_ratio is None
    assert gates["probability_quality"].status == "pass"
    assert gates["executable_edge_quality"].status == "incomplete"
    assert gates["residual_exposure"].status == "incomplete"
    assert report.status == "insufficient_evidence"
```

```python
def test_build_paper_forecast_evidence_report_supports_edge_only_observations():
    observations = (
        replace(
            sample_observations()[0],
            predicted_probability=None,
            actual_outcome_value=None,
        ),
        replace(
            sample_observations()[1],
            predicted_probability=None,
            actual_outcome_value=None,
        ),
    )

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=0,
            min_edge_observations=2,
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert report.probability_observation_count == 0
    assert report.edge_observation_count == 2
    assert report.mean_probability_loss is None
    assert report.buckets == ()
    assert report.mean_edge_gap_ratio == Decimal("0.0400")
    assert gates["probability_quality"].status == "incomplete"
    assert gates["executable_edge_quality"].status == "pass"
    assert gates["residual_exposure"].status == "pass"
    assert report.status == "insufficient_evidence"
```

```python
def test_forecast_evidence_observation_rejects_partial_roles():
    with pytest.raises(ValueError, match="probability"):
        replace(sample_observations()[0], actual_outcome_value=None)
    with pytest.raises(ValueError, match="probability"):
        replace(sample_observations()[0], predicted_probability=None)
    with pytest.raises(ValueError, match="executable"):
        replace(sample_observations()[0], fill_probability=None)
    with pytest.raises(ValueError, match="executable"):
        replace(sample_observations()[0], paper_return_ratio=None)
```

```python
def test_build_paper_forecast_evidence_report_rejects_duplicate_key_after_utc_normalization():
    base = sample_observations()[0]
    same_instant = replace(
        base,
        observed_at=datetime(2026, 8, 2, 8, tzinfo=timezone(timedelta(hours=-4))),
    )
    utc_instant = replace(
        base,
        observed_at=datetime(2026, 8, 2, 12, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="duplicate"):
        build_paper_forecast_evidence_report(
            [same_instant, utc_instant],
            config=PaperForecastEvidenceConfig(config_version="node5-test"),
            generated_at=datetime(2026, 8, 10, tzinfo=UTC),
        )
```

```python
def test_build_paper_forecast_evidence_report_rejects_duplicate_evidence_key():
    observation = sample_observations()[0]

    with pytest.raises(ValueError, match="duplicate"):
        build_paper_forecast_evidence_report(
            [observation, observation],
            config=PaperForecastEvidenceConfig(config_version="node5-test"),
            generated_at=datetime(2026, 8, 10, tzinfo=UTC),
        )
```

```python
def test_build_paper_forecast_evidence_report_rejects_bad_public_inputs():
    observation = sample_observations()[0]
    config = PaperForecastEvidenceConfig(config_version="node5-test")

    with pytest.raises(ValueError, match="observations"):
        build_paper_forecast_evidence_report(
            "not-observations",
            config=config,
            generated_at=datetime(2026, 8, 10, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="PaperForecastEvidenceObservation"):
        build_paper_forecast_evidence_report(
            [object()],
            config=config,
            generated_at=datetime(2026, 8, 10, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_forecast_evidence_report(
            [observation],
            config=object(),
            generated_at=datetime(2026, 8, 10, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_forecast_evidence_report(
            [observation],
            config=config,
            generated_at=None,
        )
```

```python
def test_forecast_evidence_dataclasses_reject_invalid_values():
    with pytest.raises(ValueError, match="max_mean_probability_loss"):
        PaperForecastEvidenceConfig(
            config_version="node5-test",
            max_mean_probability_loss=1,
        )
    with pytest.raises(ValueError, match="probability_bucket_width"):
        PaperForecastEvidenceConfig(
            config_version="node5-test",
            probability_bucket_width=Decimal("0"),
        )
    with pytest.raises(ValueError, match="probability_bucket_width"):
        PaperForecastEvidenceConfig(
            config_version="node5-test",
            probability_bucket_width=Decimal("1.2000"),
        )
    with pytest.raises(ValueError, match="actual_outcome_value"):
        replace(sample_observations()[0], actual_outcome_value=Decimal("0.5"))
    with pytest.raises(ValueError, match="evidence"):
        PaperForecastEvidenceObservation(
            observed_at=datetime(2026, 8, 1, tzinfo=UTC),
            source_packet_id="packet-empty",
            condition_id="condition-empty",
            token_id="token-empty",
            market_slug="market-empty",
            strategy_type="market_quality",
            risk_tags=("liquidity",),
        )
```

```python
def test_build_paper_forecast_evidence_report_uses_custom_probability_bucket_width_and_boundaries():
    observations = (
        replace(
            sample_observations()[0],
            predicted_probability=Decimal("0.5000"),
            actual_outcome_value=Decimal("1"),
        ),
        replace(
            sample_observations()[1],
            predicted_probability=Decimal("1.0000"),
            actual_outcome_value=Decimal("1"),
        ),
    )

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=2,
            min_edge_observations=2,
            probability_bucket_width=Decimal("0.5000"),
            max_mean_probability_loss=Decimal("0.2000"),
            max_bucket_error=Decimal("0.5000"),
            max_mean_edge_gap_ratio=Decimal("0.0500"),
            min_positive_edge_hit_rate=Decimal("0"),
            max_residual_exposure_ratio=Decimal("0.1000"),
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    assert [bucket.bucket_label for bucket in report.buckets] == [
        "0.5000-1.0000",
    ]
    assert report.buckets[0].lower_probability == Decimal("0.5000")
    assert report.buckets[0].upper_probability == Decimal("1.0000")
    assert report.buckets[0].observation_count == 2
    assert report.buckets[0].mean_predicted_probability == Decimal("0.7500")
    assert report.buckets[0].observed_frequency == Decimal("1.0000")
```

```python
def test_build_paper_forecast_evidence_report_zero_thresholds_pass_on_exact_zero():
    observations = (
        replace(
            sample_observations()[0],
            predicted_probability=Decimal("1.0000"),
            actual_outcome_value=Decimal("1"),
            theoretical_edge_ratio=Decimal("0.0300"),
            executable_edge_ratio=Decimal("0.0300"),
            residual_exposure_ratio=Decimal("0"),
            paper_return_ratio=Decimal("0"),
        ),
    )

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=1,
            min_edge_observations=1,
            max_mean_probability_loss=Decimal("0"),
            max_bucket_error=Decimal("0"),
            max_mean_edge_gap_ratio=Decimal("0"),
            min_positive_edge_hit_rate=Decimal("0"),
            max_residual_exposure_ratio=Decimal("0"),
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    assert report.mean_probability_loss == Decimal("0.0000")
    assert report.worst_bucket_error == Decimal("0.0000")
    assert report.mean_edge_gap_ratio == Decimal("0.0000")
    assert report.positive_edge_hit_rate == Decimal("0.0000")
    assert report.worst_residual_exposure_ratio == Decimal("0.0000")
    assert report.status == "paper_review_ready"
```

```python
def test_build_paper_forecast_evidence_report_zero_thresholds_fail_on_positive_metric():
    observations = (
        replace(
            sample_observations()[0],
            predicted_probability=Decimal("0.9999"),
            actual_outcome_value=Decimal("1"),
            theoretical_edge_ratio=Decimal("0.0301"),
            executable_edge_ratio=Decimal("0.0300"),
            residual_exposure_ratio=Decimal("0.0001"),
            paper_return_ratio=Decimal("0"),
        ),
    )

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=1,
            min_edge_observations=1,
            max_mean_probability_loss=Decimal("0"),
            max_bucket_error=Decimal("0"),
            max_mean_edge_gap_ratio=Decimal("0"),
            min_positive_edge_hit_rate=Decimal("0"),
            max_residual_exposure_ratio=Decimal("0"),
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["probability_quality"].status == "fail"
    assert gates["executable_edge_quality"].status == "fail"
    assert gates["residual_exposure"].status == "fail"
    assert report.status == "blocked_by_quality"
```

```python
def test_forecast_evidence_gate_result_rejects_float_values_and_unknown_status():
    with pytest.raises(ValueError, match="observed_value"):
        PaperForecastEvidenceGateResult(
            gate_name="sample_size",
            status="fail",
            message="bad",
            observed_value=1.0,
        )
    with pytest.raises(ValueError, match="status"):
        PaperForecastEvidenceGateResult(
            gate_name="sample_size",
            status="unknown",
            message="bad",
        )
    with pytest.raises(ValueError, match="threshold"):
        PaperForecastEvidenceGateResult(
            gate_name="sample_size",
            status="fail",
            message="bad",
            threshold=True,
        )
```

```python
def test_forecast_evidence_dataclasses_are_frozen():
    report = build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    with pytest.raises(FrozenInstanceError):
        report.observation_count = 0
    with pytest.raises(FrozenInstanceError):
        report.buckets[0].bucket_error = Decimal("0")
```

```python
def test_paper_forecast_evidence_log_appends_jsonl_report(tmp_path):
    report = build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    log = PaperForecastEvidenceLog(path=tmp_path / "forecast-evidence.jsonl")

    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"buckets"')
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["generated_at"] == "2026-08-10T00:00:00+00:00"
    assert stored["config_version"] == "node5-test"
    assert stored["mean_probability_loss"] == "0.1800"
    assert stored["gate_results"][0]["gate_name"] == "data_integrity"
```

```python
def test_paper_forecast_evidence_log_appends_without_overwriting_and_creates_parent_dirs(
    tmp_path,
):
    report = build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    log = PaperForecastEvidenceLog(path=str(tmp_path / "nested" / "forecast.jsonl"))

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["generated_at"] == "2026-08-10T00:00:00+00:00"
    assert json.loads(lines[1])["generated_at"] == "2026-08-10T00:00:00+00:00"
```

```python
def test_paper_forecast_evidence_log_rejects_invalid_paths(tmp_path):
    with pytest.raises(ValueError, match="path"):
        PaperForecastEvidenceLog(path=object())
    with pytest.raises(ValueError, match="path"):
        PaperForecastEvidenceLog(path=" ")

    existing_dir = tmp_path / "existing-dir"
    existing_dir.mkdir()
    with pytest.raises(ValueError, match="path"):
        PaperForecastEvidenceLog(path=existing_dir)

    existing_file = tmp_path / "parent-file"
    existing_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="parent"):
        PaperForecastEvidenceLog(path=existing_file / "forecast.jsonl")
```

```python
def test_paper_forecast_evidence_log_rejects_invalid_public_input_before_file_creation(
    tmp_path,
):
    path = tmp_path / "forecast.jsonl"
    log = PaperForecastEvidenceLog(path=path)

    with pytest.raises(ValueError, match="PaperForecastEvidenceReport"):
        log.append(object())

    assert not path.exists()
```

```python
def test_paper_forecast_evidence_log_preserves_existing_file_when_serialization_fails(
    tmp_path,
):
    report = build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    object.__setattr__(report, "mean_probability_loss", Decimal("NaN"))
    path = tmp_path / "forecast.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = PaperForecastEvidenceLog(path=path)

    with pytest.raises(ValueError, match="finite|JSON|serializable"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'
```

```python
def test_paper_forecast_evidence_log_preserves_existing_file_when_nested_report_is_invalid(
    tmp_path,
):
    report = build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    object.__setattr__(report.gate_results[0], "status", "unknown")
    path = tmp_path / "forecast.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = PaperForecastEvidenceLog(path=path)

    with pytest.raises(ValueError, match="status"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'
```

```python
def test_paper_forecast_evidence_log_preserves_existing_file_when_nested_bucket_is_invalid(
    tmp_path,
):
    report = build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    object.__setattr__(report.buckets[0], "observation_count", -1)
    path = tmp_path / "forecast.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = PaperForecastEvidenceLog(path=path)

    with pytest.raises(ValueError, match="observation_count"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'
```

- [ ] **Step 2: Run behavior tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_forecast_evidence.py -q
```

Expected: fail because `polymarket_alpha_lab.forecast_evidence` does not exist.

## Part 3: Forecast Evidence Implementation

**Goal:** Implement frozen forecast evidence dataclasses, pure report builder, gate rows, Decimal helpers, and JSONL persistence.

**Files:**

- Create: `src/polymarket_alpha_lab/forecast_evidence.py`

- [ ] **Step 1: Implement `forecast_evidence.py`**

Implementation requirements:

- Define `__all__` with the seven public API names.
- Import only standard library modules:

```python
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
```

- Do not import any `polymarket_alpha_lab.*` module in `forecast_evidence.py`.
- Use `RATIO_QUANTUM = Decimal("0.0001")`.
- Implement local Decimal helpers and strict validators, adapted from Node 4.
- Reject `float`, `int`, `str`, `bool`, and `None` for required `Decimal` fields.
- Reject finite and non-finite floats during JSON-ready validation.
- Enforce `probability_bucket_width` is a finite `Decimal` greater than `Decimal("0")` and less than or equal to `Decimal("1")`.
- Validate direct dataclass construction through `__post_init__()` methods.
- Normalize datetimes to UTC.
- Normalize `risk_tags` to a tuple of canonical strings and require at least one risk tag.
- Require `source_packet_id`, `condition_id`, `token_id`, `market_slug`, and `strategy_type` to be canonical strings.
- Enforce `predicted_probability`, `actual_outcome_value`, `fill_probability`, and `residual_exposure_ratio` domains in `[0, 1]`.
- Enforce `actual_outcome_value` is exactly `Decimal("0")` or `Decimal("1")` when present.
- Allow edge and paper return ratios to be finite signed `Decimal` values.
- Require each observation to provide at least one complete probability role or one complete executable-edge role.
- Build sorted observations by `observed_at`.
- Reject duplicate `(observed_at, token_id, source_packet_id)` keys after UTC normalization.
- Calculate unique market, strategy, and risk-tag counts from observations.
- Calculate probability losses and probability buckets exactly as specified in Forecast Evidence Semantics.
- Return probability buckets sorted by `lower_probability`, then `upper_probability`; do not rely on first-seen bucket order.
- Calculate executable-edge metrics exactly as specified in Forecast Evidence Semantics.
- Build exactly five gate results in this order:
  1. `data_integrity`
  2. `sample_size`
  3. `probability_quality`
  4. `executable_edge_quality`
  5. `residual_exposure`
- Derive final status from gate results in this order:
  1. `incomplete_data` if no observations or `data_integrity` is incomplete.
  2. `blocked_by_quality` if probability-quality, executable-edge-quality, or residual-exposure gate is fail.
  3. `insufficient_evidence` if sample-size gate is fail or any non-data-integrity gate is incomplete.
  4. `paper_review_ready` only when all five gate statuses are `pass`; this means evidence-artifact review readiness only, not proposal/live promotion.
- Implement `PaperForecastEvidenceLog.append(report)` with validation-before-open JSONL behavior matching Node 4 `PaperAnalyticsHistoryLog`: validate public type, revalidate the nested report tree, build the complete JSONL line with `json.dumps(..., allow_nan=False, sort_keys=True)`, then validate the parent path, create parent directories, and open the file in append mode.

- [ ] **Step 2: Run forecast evidence and scope tests to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_forecast_evidence.py tests/test_forecast_evidence_scope.py -q
```

Expected: forecast evidence and scope tests pass.

## Part 4: Public Exports And README

**Goal:** Export Node 5 APIs and document the new paper-only status.

**Files:**

- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Modify: `README.md`

- [ ] **Step 1: Add failing package-root export test**

Modify `tests/test_init.py`:

```python
from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceBucket,
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceGateResult,
    PaperForecastEvidenceLog,
    PaperForecastEvidenceObservation,
    PaperForecastEvidenceReport,
    build_paper_forecast_evidence_report,
)
```

Add:

```python
def test_level_1b_node_5_public_api_exports():
    expected_exports = {
        "PaperForecastEvidenceBucket",
        "PaperForecastEvidenceConfig",
        "PaperForecastEvidenceGateResult",
        "PaperForecastEvidenceLog",
        "PaperForecastEvidenceObservation",
        "PaperForecastEvidenceReport",
        "build_paper_forecast_evidence_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperForecastEvidenceBucket is PaperForecastEvidenceBucket
    assert lab.PaperForecastEvidenceConfig is PaperForecastEvidenceConfig
    assert lab.PaperForecastEvidenceGateResult is PaperForecastEvidenceGateResult
    assert lab.PaperForecastEvidenceLog is PaperForecastEvidenceLog
    assert lab.PaperForecastEvidenceObservation is PaperForecastEvidenceObservation
    assert lab.PaperForecastEvidenceReport is PaperForecastEvidenceReport
    assert lab.build_paper_forecast_evidence_report is build_paper_forecast_evidence_report
```

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py -q
```

Expected: fail because package root does not export Node 5 names.

- [ ] **Step 2: Export forecast evidence APIs from package root**

Modify `src/polymarket_alpha_lab/__init__.py`:

```python
from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceBucket,
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceGateResult,
    PaperForecastEvidenceLog,
    PaperForecastEvidenceObservation,
    PaperForecastEvidenceReport,
    build_paper_forecast_evidence_report,
)
```

Add the seven names to `__all__`, preserving every existing export and avoiding forbidden public export fragments.

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py -q
```

Expected: pass.

- [ ] **Step 3: Update README**

Modify `README.md`:

1. Update the Phase 1 Scope sentence to include paper-only forecast evidence reports.
2. Add after Level 1B Node 4 Python API:

```markdown
## Level 1B Node 5 Status

Level 1B Node 5 adds paper-only forecast evidence reports over caller-supplied `PaperForecastEvidenceObservation` values, including probability-loss summaries, probability-bucket evidence, executable-edge evidence, residual-exposure checks, and evidence-readiness status for later human review. Its `paper_review_ready` status means the evidence artifact is ready for manual review only; it is not a proposal-generation, promotion, or live-execution signal. It does not load outcomes, settle markets, fetch market/order-book/account data, use external loaders, scrape websites, authenticate, handle private keys, place or cancel orders, open user WebSockets, run heartbeat logic, use a trading SDK, create trade proposals, reconcile exchange accounts, or perform compliance/legal/geographic analysis.

## Level 1B Node 5 Python API

Node 5 is exposed through Python APIs:

- Configure forecast evidence thresholds with `PaperForecastEvidenceConfig(...)`.
- Record caller-supplied paper evidence with `PaperForecastEvidenceObservation(...)`.
- Build paper forecast evidence reports with `build_paper_forecast_evidence_report(observations, config=..., generated_at=...)`, which returns `PaperForecastEvidenceReport`.
- Inspect probability bucket rows with `PaperForecastEvidenceBucket` and gate rows with `PaperForecastEvidenceGateResult`.
- Persist forecast evidence snapshots with `PaperForecastEvidenceLog(path).append(report)`.
```

3. Add `2026-06-13-level-1b-paper-forecast-evidence.md` to the plan tree.
4. Add `forecast_evidence.py` under `src/polymarket_alpha_lab`.
5. Add `test_forecast_evidence.py` and `test_forecast_evidence_scope.py` under `tests`.

- [ ] **Step 4: Run node-specific tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_forecast_evidence.py tests/test_forecast_evidence_scope.py tests/test_init.py -q
```

Expected: pass.

## Level 1B Node 5 Completion Criteria

Node 5 is complete only when all of these are true:

- `src/polymarket_alpha_lab/forecast_evidence.py` exists and is paper-only.
- Static scope tests prove the module does not import or define forbidden auth/execution/network/proposal/reconciliation/scraping/compliance surfaces.
- Public exports avoid existing `brier`, `calibration`, `resolvedoutcome`, and `execution` export fragments.
- `build_paper_forecast_evidence_report(...)` consumes `PaperForecastEvidenceObservation` values only, validates sequence ordering, rejects duplicate evidence keys, and returns a frozen `PaperForecastEvidenceReport`.
- The report uses caller-supplied paper evidence only; it does not infer outcomes, settle markets, fetch data, or recompute fills from external books.
- Empty input is represented as `incomplete_data`, not as a false pass.
- Sample-size thresholds, probability-loss summaries, bucket errors, executable-edge gaps, hit rate, and residual exposure map to Gate 4 intent in `docs/research/validation-gates.md`.
- Undefined ratios return `None`; all defined ratios are finite `Decimal` values.
- JSONL persistence validates and serializes before opening files.
- Package-root exports and README document Node 5 APIs and boundaries.

## Part 5: Final Verification, Claude Review, Handoff, Commit, Push

**Goal:** Verify the node, obtain Claude implementation review, record handoff, and push only after all gates pass.

- [ ] **Step 1: Run fresh verification**

Run:

```bash
git status --short --branch --untracked-files=all
.venv/bin/python -m pytest tests/test_forecast_evidence.py tests/test_forecast_evidence_scope.py tests/test_init.py -q
.venv/bin/python -m pytest tests/test_forecast_evidence_scope.py -q
.venv/bin/python -m pytest tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py -q
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

  printf '%s\n' 'Review this Level 1B Node 5 implementation for polymarket-alpha-lab before commit.'
  printf '%s\n' 'This is a read-only, self-contained implementation review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, plan, tests, implementation, or verification output.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; implementation is ready to stage, handoff, commit, and push.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing required review material, unsafe scope, failed verification, stale CodeGraph, missing or unexpected tracked/untracked file, staged content before review, or omitted file content.'
  printf '%s\n' 'Review specifically: paper-only scope boundaries, forbidden surfaces, Gate 4 evidence semantics, public naming constraints, Decimal strictness, JSONL validation-before-open behavior, package exports, README updates, tests, CodeGraph status, and final gate readiness.'
  printf '%s\n' 'Before the final verdict line, report finding counts exactly as:'
  printf '%s\n' 'Critical findings: <integer>'
  printf '%s\n' 'Important findings: <integer>'
  printf '%s\n' 'Minor findings: <integer>'
  printf '%s\n' 'Use 0 for empty categories; do not use "none" in count fields.'
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
  printf '%s\n' 'Node 5 plan:'
  cat docs/superpowers/plans/2026-06-13-level-1b-paper-forecast-evidence.md
  printf '%s\n' ''
  printf '%s\n' 'Existing scope tests:'
  sed -n '1,340p' tests/test_analytics_scope.py
  sed -n '1,340p' tests/test_analytics_history_scope.py
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
  run_review_cmd .venv/bin/python -m pytest tests/test_forecast_evidence.py tests/test_forecast_evidence_scope.py tests/test_init.py -q
  run_review_cmd .venv/bin/python -m pytest tests/test_forecast_evidence_scope.py -q
  run_review_cmd .venv/bin/python -m pytest tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py -q
  run_review_cmd .venv/bin/python -m pytest -q
  run_review_cmd git diff --check
  run_review_cmd git diff --cached --check
  run_review_cmd codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Tracked diff names:'
  git diff --name-only
  printf '%s\n' 'Expected tracked diff files: README.md, src/polymarket_alpha_lab/__init__.py, tests/test_init.py'
  expected_tracked=$(printf '%s\n' README.md src/polymarket_alpha_lab/__init__.py tests/test_init.py | sort)
  actual_tracked=$(git diff --name-only | sort)
  missing_tracked=$(comm -23 <(printf '%s\n' "$expected_tracked") <(printf '%s\n' "$actual_tracked"))
  unexpected_tracked=$(comm -23 <(printf '%s\n' "$actual_tracked") <(printf '%s\n' "$expected_tracked"))
  if [ -n "$missing_tracked" ]; then
    printf '%s\n' 'BLOCKING REVIEW ISSUE: expected tracked files are not modified.'
    printf '%s\n' "$missing_tracked"
  else
    printf '%s\n' 'Missing expected tracked files: none'
  fi
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
  printf '%s\n' 'Full content for expected tracked modified files:'
  for path in README.md src/polymarket_alpha_lab/__init__.py tests/test_init.py; do
    if [ -f "$path" ]; then
      line_count=$(wc -l < "$path")
      printf '\n### Line count for %s\n%s\n' "$path" "$line_count"
      if [ "$line_count" -gt 5000 ]; then
        printf '%s\n' 'BLOCKING REVIEW ISSUE: tracked file exceeds the full-content review cap.'
      fi
      printf '\n### Full content for %s\n' "$path"
      sed -n '1,5000p' "$path"
    else
      printf '%s\n' "BLOCKING REVIEW ISSUE: expected tracked file is missing: $path"
    fi
  done
  printf '%s\n' ''
  printf '%s\n' 'Untracked file list:'
  git ls-files --others --exclude-standard
  printf '%s\n' ''
  printf '%s\n' 'Expected untracked files: docs/superpowers/plans/2026-06-13-level-1b-paper-forecast-evidence.md, src/polymarket_alpha_lab/forecast_evidence.py, tests/test_forecast_evidence.py, tests/test_forecast_evidence_scope.py'
  expected_untracked=$(printf '%s\n' docs/superpowers/plans/2026-06-13-level-1b-paper-forecast-evidence.md src/polymarket_alpha_lab/forecast_evidence.py tests/test_forecast_evidence.py tests/test_forecast_evidence_scope.py | sort)
  actual_untracked=$(git ls-files --others --exclude-standard | sort)
  missing_untracked=$(comm -23 <(printf '%s\n' "$expected_untracked") <(printf '%s\n' "$actual_untracked"))
  unexpected_untracked=$(comm -23 <(printf '%s\n' "$actual_untracked") <(printf '%s\n' "$expected_untracked"))
  if [ -n "$missing_untracked" ]; then
    printf '%s\n' 'BLOCKING REVIEW ISSUE: expected untracked files are missing.'
    printf '%s\n' "$missing_untracked"
  else
    printf '%s\n' 'Missing expected untracked files: none'
  fi
  if [ -n "$unexpected_untracked" ]; then
    printf '%s\n' 'BLOCKING REVIEW ISSUE: unexpected untracked files are present.'
    printf '%s\n' "$unexpected_untracked"
  else
    printf '%s\n' 'Unexpected untracked files: none'
  fi
  for path in docs/superpowers/plans/2026-06-13-level-1b-paper-forecast-evidence.md src/polymarket_alpha_lab/forecast_evidence.py tests/test_forecast_evidence.py tests/test_forecast_evidence_scope.py; do
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
    else
      printf '\n### Missing untracked file %s\n' "$path"
      printf '%s\n' 'BLOCKING REVIEW ISSUE: expected untracked file is missing; full content cannot be included.'
    fi
  done
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted result: explicit count lines showing zero Critical findings and zero Important findings, all required file contents present, every verification command showing `exit_code=0`, CodeGraph up to date, no missing or unexpected tracked/untracked files, no staged content before review, and `Verdict: Proceed` or `Verdict: Proceed with fixes`. Any omitted required material, missing count, missing stderr/exit-code evidence, stale CodeGraph result, failed verification, missing or unexpected tracked/untracked file, staged content before review, Critical finding, or Important finding is `Blocked`.

- [ ] **Step 3: Stage implementation files and run cached diff check**

Run:

```bash
git add README.md src/polymarket_alpha_lab/__init__.py src/polymarket_alpha_lab/forecast_evidence.py tests/test_forecast_evidence.py tests/test_forecast_evidence_scope.py tests/test_init.py docs/superpowers/plans/2026-06-13-level-1b-paper-forecast-evidence.md
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
  - `.venv/bin/python -m pytest tests/test_forecast_evidence.py tests/test_forecast_evidence_scope.py tests/test_init.py -q`: pass/fail and test count.
  - `.venv/bin/python -m pytest tests/test_forecast_evidence_scope.py -q`: pass/fail and test count.
  - `.venv/bin/python -m pytest -q`: pass/fail and test count.
  - `git diff --check`: pass/fail.
  - `codegraph status .`: up to date or stale.
  - `codegraph sync .`: run/not run and result.
  - follow-up `codegraph status .`: up to date or stale.
  - `git diff --cached --check`: pass/fail.
- Untracked files: list or `none`.
- Uncommitted files: list or `none`.
- Data-integrity checks: paper-only scope, forbidden-surface static tests, direct observation validation, duplicate evidence-key rejection, caller-supplied evidence only, probability-loss evidence, bucket evidence, executable-edge evidence, residual-exposure mapping, Decimal-only finite math, undefined ratio handling, JSONL validation-before-open behavior.
- Claude review: model `claude-opus-4-8`, effort `max`, review scope, explicit verdict, unresolved findings.
- Commit/push: commit hash, remote branch, push result. Because this handoff is written before the final commit/push, use `commit hash: pending final commit` and `push result: pending final push` in the committed handoff, then report the actual commit hash and push result in the assistant final response after `git push`.
- Next step: one concrete next action for the next Level 1B node.
```

Because this handoff is written before the final commit and push exist, set the commit hash field to `pending final commit` and the push result field to `pending final push` in the committed handoff. Report the final commit hash and push result in the assistant final response after push.

Then run:

```bash
git add docs/superpowers/plans/2026-06-13-level-1b-paper-forecast-evidence.md
git diff --cached --check
```

- [ ] **Step 5: Commit and push**

Run:

```bash
git commit -m "feat: add paper forecast evidence reports"
git push
git status --short --branch --untracked-files=all
```

Expected: commit succeeds, push updates `origin/main`, and final status is exactly `## main...origin/main` with no additional file lines.

## Handoff Summary

- Repo status: branch `main`, latest pre-node commit `ada52d4`, pushed through `origin/main` before this node commit, dirty only with staged Node 5 files.
- Git status output:

```text
## main...origin/main
M  README.md
A  docs/superpowers/plans/2026-06-13-level-1b-paper-forecast-evidence.md
M  src/polymarket_alpha_lab/__init__.py
A  src/polymarket_alpha_lab/forecast_evidence.py
A  tests/test_forecast_evidence.py
A  tests/test_forecast_evidence_scope.py
M  tests/test_init.py
```

- Verified commands:
  - `git status --short --branch --untracked-files=all`: pass; expected staged Node 5 files listed above.
  - `.venv/bin/python -m pytest tests/test_forecast_evidence.py tests/test_forecast_evidence_scope.py tests/test_init.py -q`: pass, `35 passed`.
  - `.venv/bin/python -m pytest tests/test_forecast_evidence_scope.py -q`: pass, `5 passed`.
  - `.venv/bin/python -m pytest tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py -q`: pass, `16 passed`.
  - `.venv/bin/python -m pytest -q`: pass, `354 passed`.
  - `git diff --check`: pass, no output.
  - `git diff --cached --check`: pass before this handoff entry, no output.
  - `codegraph status .`: pass, index up to date.
  - `codegraph sync .`: run earlier after CodeGraph reported pending changes; synced 3 changed files successfully.
  - follow-up `codegraph status .`: pass, index up to date.
- Untracked files: none after staging.
- Uncommitted files:
  - `README.md`
  - `docs/superpowers/plans/2026-06-13-level-1b-paper-forecast-evidence.md`
  - `src/polymarket_alpha_lab/__init__.py`
  - `src/polymarket_alpha_lab/forecast_evidence.py`
  - `tests/test_forecast_evidence.py`
  - `tests/test_forecast_evidence_scope.py`
  - `tests/test_init.py`
- Data-integrity checks: paper-only scope enforced by observation/report validation and static scope tests; forbidden-surface static tests pass; direct observation validation covers canonical strings, UTC normalization, complete role requirements, finite `Decimal` ratios, zero/one outcome values, and `paper_only=True`; duplicate evidence-key rejection occurs after UTC normalization; reports consume caller-supplied evidence only; probability-loss, probability-bucket, executable-edge, hit-rate, and residual-exposure evidence map to Gate 4 intent; undefined role metrics return `None`; JSONL append validates the report tree and serializes the complete line before opening files.
- Claude review: final implementation review used model `claude-opus-4-8` with effort `max`; scope covered paper-only boundaries, forbidden surfaces, Gate 4 evidence semantics, public naming constraints, Decimal strictness, JSONL validation-before-open behavior, package exports, README updates, tests, CodeGraph status, and final gate readiness; Critical findings `0`, Important findings `0`, Minor findings `0`; verdict `Proceed`; unresolved findings: none.
- Commit/push: commit hash `pending final commit`; remote branch `origin/main`; push result `pending final push`.
- Next step: draft the next Level 1B plan for a paper-only manual-review queue that combines market scores, paper analytics history, and forecast evidence without live actions.
