# Level 2 Proposal Evidence Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a report-only comparison artifact that contrasts supplied forecast-evidence reports with supplied proposal-review dossier batch health reports for human audit.

**Architecture:** Create a focused `proposal_evidence_comparison.py` module that accepts only caller-supplied `PaperForecastEvidenceReport` and `TradeProposalReviewDossierBatchReport` objects. It clones/revalidates both report trees, copies aggregate evidence metrics into deterministic rows, emits comparison gates and findings, and optionally appends a validated JSONL snapshot. The artifact is offline observability only: it never reads logs, fetches market data, ranks investments, recommends trades, approves proposals, resolves decisions, handles credentials, or touches execution surfaces.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, UTC `datetime`, JSONL append-only persistence, pytest, CodeGraph, and local opencode review with model `zhipuai-coding-plan/glm-5.2` using variant `max`.

---

## Scope Boundaries

This node consumes only in-memory, caller-supplied report objects:

- `PaperForecastEvidenceReport` from `polymarket_alpha_lab.forecast_evidence`
- `TradeProposalReviewDossierBatchReport` from `polymarket_alpha_lab.proposal_review_dossier_batch`

This node must not consume raw `PaperForecastEvidenceObservation` rows, raw `TradeProposalPacket` values, raw `TradeProposalReviewRecord` values, `MarketScore` rows, order books, paper positions, NAV snapshots, API payloads, JSONL files, archived payloads, external history, web pages, account state, credentials, wallets, broker payloads, or execution records.

This node must not fetch market/order-book/price/outcome/account data, read JSONL logs, replay history, glob files, scrape websites, run browser automation, authenticate, handle credentials or private keys, open user WebSockets, run heartbeat logic, build order requests, place/submit/sign/send/create/cancel orders, select approved proposals, select latest decisions, resolve conflicting reviews, rank investments, recommend trades, promote strategies, review settlement, reconcile positions or exchange accounts, import manual executions, or perform compliance/legal/geographic analysis.

## Public API

Create `src/polymarket_alpha_lab/proposal_evidence_comparison.py` with:

```python
__all__ = (
    "TradeProposalEvidenceComparisonConfig",
    "TradeProposalEvidenceComparisonGateResult",
    "TradeProposalEvidenceComparisonSourceRow",
    "TradeProposalEvidenceComparisonMetricRow",
    "TradeProposalEvidenceComparisonFindingRow",
    "TradeProposalEvidenceComparisonReport",
    "TradeProposalEvidenceComparisonLog",
    "build_trade_proposal_evidence_comparison_report",
)
```

Define `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_BOUNDARY_STATEMENT` exactly as:

```python
DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_BOUNDARY_STATEMENT = (
    "This is a report-only proposal evidence comparison artifact over supplied "
    "forecast evidence and proposal-review dossier batch reports, not an "
    "approval workflow, proposal approval, approved-proposal selector, "
    "latest-decision selector, decision-resolution process, investment ranking, "
    "trade recommendation, strategy-promotion signal, trade instruction, order "
    "instruction, broker request, order request, account action, account "
    "authentication, private-key handling, wallet signature, live-execution "
    "signal, credential workflow, external-history loader, JSONL reader, "
    "scraping workflow, settlement review, reconciliation process, compliance "
    "review, geographic access analysis, or automatic order-placement "
    "authorization."
)
```

`_require_boundary_statement` must normalize by lowercasing and keeping only alphanumeric characters, then require equality to the normalized default boundary statement.

Public dataclasses:

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonConfig:
    config_version: str
    min_forecast_observation_count: int = 1
    min_dossier_count: int = 1
    max_incomplete_dossier_ratio: Decimal = Decimal("0.0000")
    max_inconsistent_dossier_ratio: Decimal = Decimal("0.0000")
    max_unstable_dossier_ratio: Decimal = Decimal("0.0000")
    require_forecast_ready: bool = True
    require_dossier_batch_ready: bool = True
    boundary_statement: str = DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_BOUNDARY_STATEMENT
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonSourceRow:
    source_name: str
    source_status: str
    generated_at: datetime
    sample_count: int
    status_category: str
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonMetricRow:
    metric_name: str
    source_name: str
    observed_value: Decimal | int | str | None
    threshold: Decimal | int | str | None
    status: str
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonFindingRow:
    finding_code: str
    severity: str
    source_name: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    forecast_evidence_generated_at: datetime
    dossier_batch_generated_at: datetime
    forecast_status: str
    dossier_batch_status: str
    forecast_observation_count: int
    forecast_probability_observation_count: int
    forecast_edge_observation_count: int
    dossier_count: int
    complete_dossier_count: int
    incomplete_dossier_ratio: Decimal | None
    inconsistent_dossier_ratio: Decimal | None
    unstable_dossier_ratio: Decimal | None
    mean_probability_loss: Decimal | None
    worst_bucket_error: Decimal | None
    mean_edge_gap_ratio: Decimal | None
    positive_edge_hit_rate: Decimal | None
    worst_residual_exposure_ratio: Decimal | None
    status: str
    gate_results: tuple[TradeProposalEvidenceComparisonGateResult, ...]
    source_rows: tuple[TradeProposalEvidenceComparisonSourceRow, ...]
    metric_rows: tuple[TradeProposalEvidenceComparisonMetricRow, ...]
    finding_rows: tuple[TradeProposalEvidenceComparisonFindingRow, ...]
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonLog:
    path: Path | str

    def append(self, report: TradeProposalEvidenceComparisonReport) -> None:
        ...
```

Builder signature:

```python
def build_trade_proposal_evidence_comparison_report(
    *,
    forecast_evidence: PaperForecastEvidenceReport,
    dossier_batch: TradeProposalReviewDossierBatchReport,
    config: TradeProposalEvidenceComparisonConfig,
    generated_at: datetime,
) -> TradeProposalEvidenceComparisonReport:
    ...
```

## Status And Gate Rules

Gate names:

```python
GATE_NAMES = (
    "source_sample",
    "forecast_evidence_status",
    "dossier_batch_status",
    "evidence_consistency",
)
```

Gate statuses are `pass`, `fail`, or `incomplete`.

Report statuses:

```python
REPORT_STATUSES = (
    "incomplete_evidence_comparison",
    "divergent_evidence_comparison",
    "unstable_evidence_comparison",
    "proposal_evidence_comparison_complete",
)
```

Finding severities:

```python
FINDING_SEVERITIES = (
    "incomplete",
    "divergent",
    "unstable",
)
```

Status mapping:

- If `source_sample` is `incomplete`, report status is `incomplete_evidence_comparison`.
- Else if `evidence_consistency` is `fail`, report status is `divergent_evidence_comparison`.
- Else if `forecast_evidence_status` or `dossier_batch_status` is `fail`, report status is `unstable_evidence_comparison`.
- Else if any gate is `incomplete`, report status is `incomplete_evidence_comparison`.
- Else report status is `proposal_evidence_comparison_complete`.

Gate semantics:

- `source_sample`: pass when `forecast_observation_count >= config.min_forecast_observation_count` and `dossier_count >= config.min_dossier_count`; incomplete otherwise. Observed value is `forecast=<count>; dossier=<count>` and threshold is `forecast>=<min>; dossier>=<min>`.
- `forecast_evidence_status`: pass when `forecast_status == "paper_review_ready"`. If `config.require_forecast_ready is False`, pass with threshold `not_required`. If the forecast status is `incomplete_data` or `insufficient_evidence`, status is `incomplete`; otherwise status is `fail`.
- `dossier_batch_status`: pass when `dossier_batch_status == "proposal_review_dossier_batch_ready"` and all three dossier ratios are available and within configured thresholds. If `config.require_dossier_batch_ready is False`, pass with threshold `not_required`. If batch status is `incomplete_dossier_batch`, status is `incomplete`; if batch status is `inconsistent_dossier_batch` or `unstable_dossier_batch`, status is `fail`.
- `evidence_consistency`: compare only the statuses of `forecast_evidence_status` and `dossier_batch_status`. Pass when both are `pass`, both are `incomplete`, or both are `fail`. Fail when they differ in any way: `pass/incomplete`, `incomplete/pass`, `pass/fail`, `fail/pass`, `incomplete/fail`, or `fail/incomplete`. This is audit evidence only, not a promotion or execution signal.

Finding rows:

- Emit `forecast_evidence_incomplete` with severity `incomplete` when `forecast_evidence_status` is incomplete.
- Emit `forecast_evidence_unstable` with severity `unstable` when `forecast_evidence_status` is fail.
- Emit `dossier_batch_incomplete` with severity `incomplete` when `dossier_batch_status` is incomplete.
- Emit `dossier_batch_unstable` with severity `unstable` when `dossier_batch_status` is fail.
- Emit `evidence_consistency_divergent` with severity `divergent` when `evidence_consistency` is fail.
- Sort finding rows by `(severity, source_name, finding_code)`.

Source rows:

- Emit exactly two rows sorted by `source_name`: `("dossier_batch", "forecast_evidence")`.
- `source_name="forecast_evidence"` uses `source_status=forecast_evidence.status`, `generated_at=forecast_evidence.generated_at`, `sample_count=forecast_evidence.observation_count`, and `status_category` from forecast status.
- `source_name="dossier_batch"` uses `source_status=dossier_batch.status`, `generated_at=dossier_batch.generated_at`, `sample_count=dossier_batch.dossier_count`, and `status_category` from dossier batch status.

Metric rows:

- Emit rows sorted by `(source_name, metric_name)`.
- Forecast rows: `forecast_observation_count`, `forecast_probability_observation_count`, `forecast_edge_observation_count`, `mean_probability_loss`, `worst_bucket_error`, `mean_edge_gap_ratio`, `positive_edge_hit_rate`, `worst_residual_exposure_ratio`.
- Dossier batch rows: `dossier_count`, `complete_dossier_count`, `incomplete_dossier_ratio`, `inconsistent_dossier_ratio`, `unstable_dossier_ratio`.
- Metric row statuses are `pass`, `fail`, or `incomplete`.
- `forecast_observation_count`: threshold is `config.min_forecast_observation_count`; status is `pass` when the count is at least the threshold, otherwise `incomplete`.
- `forecast_probability_observation_count`: threshold is the threshold from the supplied forecast report's `sample_size` gate when present, otherwise `None`; status mirrors the supplied forecast report's `sample_size` gate status.
- `forecast_edge_observation_count`: threshold is the threshold from the supplied forecast report's `sample_size` gate when present, otherwise `None`; status mirrors the supplied forecast report's `sample_size` gate status.
- `mean_probability_loss` and `worst_bucket_error`: threshold is copied from the supplied forecast report's `probability_quality` gate; status mirrors that gate status.
- `mean_edge_gap_ratio` and `positive_edge_hit_rate`: threshold is copied from the supplied forecast report's `executable_edge_quality` gate; status mirrors that gate status.
- `worst_residual_exposure_ratio`: threshold is copied from the supplied forecast report's `residual_exposure` gate; status mirrors that gate status.
- `dossier_count`: threshold is `config.min_dossier_count`; status is `pass` when the count is at least the threshold, otherwise `incomplete`.
- `complete_dossier_count`: threshold is `0`; status is `pass` because this row is copied for context and is not a standalone gate.
- `incomplete_dossier_ratio`: threshold is `config.max_incomplete_dossier_ratio`; status is `incomplete` when the ratio is `None`, `pass` when it is less than or equal to threshold, and `fail` otherwise.
- `inconsistent_dossier_ratio`: threshold is `config.max_inconsistent_dossier_ratio`; status is `incomplete` when the ratio is `None`, `pass` when it is less than or equal to threshold, and `fail` otherwise.
- `unstable_dossier_ratio`: threshold is `config.max_unstable_dossier_ratio`; status is `incomplete` when the ratio is `None`, `pass` when it is less than or equal to threshold, and `fail` otherwise.
- Metric rows are observational rows only and must not rank, select, or recommend trades.

Validation requirements:

- Reject non-exact `PaperForecastEvidenceReport` and non-exact `TradeProposalReviewDossierBatchReport` inputs.
- Clone/revalidate the forecast report by reconstructing `PaperForecastEvidenceGateResult`, `PaperForecastEvidenceBucket`, and `PaperForecastEvidenceReport`.
- Clone/revalidate the dossier batch report by reconstructing all Node 8 batch gate, config-version, duplicate, finding, source, and report dataclasses.
- Validate all row tuples are exact typed tuples.
- Validate `gate_results` order equals `GATE_NAMES`.
- Validate `source_rows` contain exactly `("dossier_batch", "forecast_evidence")`.
- Validate `metric_rows` are sorted by `(source_name, metric_name)` and contain no duplicate keys.
- Validate `finding_rows` are sorted by `(severity, source_name, finding_code)` and contain no duplicate keys.
- Validate finding severities are exactly one of `FINDING_SEVERITIES`.
- Validate metric row statuses are exactly one of `GATE_STATUSES`.
- Validate `status` matches gate results.
- Validate `report_only is True`.
- Validate the exact normalized boundary statement.
- Validate all ratio fields are finite `Decimal` values between zero and one when present.
- Reject floats and bools in gate values, metric values, and finding values.
- `TradeProposalEvidenceComparisonLog.append(report)` must validate the full report tree and call `json.dumps(..., allow_nan=False, sort_keys=True)` before opening or creating the file.
- Production code must not provide JSONL readers, loaders, replay helpers, glob helpers, `from_file`, `from_log`, selectors, ranking helpers, recommendation helpers, approval helpers, or execution helpers.

## Task 1: Behavior Tests

**Files:**

- Create: `tests/test_proposal_evidence_comparison.py`

- [ ] **Step 1: Write deterministic fixtures**

Add fixtures that reuse existing test helpers rather than duplicating raw setup:

```python
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from tests.test_forecast_evidence import sample_observations
from tests.test_proposal_review_dossier_batch import complete_dossier_fixture
from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.proposal_review_dossier_batch import (
    TradeProposalReviewDossierBatchConfig,
    build_trade_proposal_review_dossier_batch_report,
)


def ready_forecast_fixture():
    return build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(
            config_version="forecast-v1",
            min_probability_observations=1,
            min_edge_observations=1,
            max_mean_probability_loss=Decimal("1.0000"),
            max_bucket_error=Decimal("1.0000"),
            max_mean_edge_gap_ratio=Decimal("1.0000"),
            min_positive_edge_hit_rate=Decimal("0.0000"),
            max_residual_exposure_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 10, 12, tzinfo=UTC),
    )


def ready_dossier_batch_fixture():
    return build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=1)],
        config=TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
        ),
        generated_at=datetime(2026, 9, 10, 13, tzinfo=UTC),
    )
```

- [ ] **Step 2: Write happy-path comparison test**

```python
def test_build_trade_proposal_evidence_comparison_report_copies_supplied_metrics():
    forecast = ready_forecast_fixture()
    dossier_batch = ready_dossier_batch_fixture()

    report = build_trade_proposal_evidence_comparison_report(
        forecast_evidence=forecast,
        dossier_batch=dossier_batch,
        config=TradeProposalEvidenceComparisonConfig(
            config_version="comparison-v1",
            min_forecast_observation_count=1,
            min_dossier_count=1,
        ),
        generated_at=datetime(2026, 9, 10, 14, tzinfo=UTC),
    )

    assert report.report_only is True
    assert report.status == "proposal_evidence_comparison_complete"
    assert report.forecast_status == "paper_review_ready"
    assert report.dossier_batch_status == "proposal_review_dossier_batch_ready"
    assert report.forecast_observation_count == forecast.observation_count
    assert report.forecast_probability_observation_count == forecast.probability_observation_count
    assert report.forecast_edge_observation_count == forecast.edge_observation_count
    assert report.dossier_count == dossier_batch.dossier_count
    assert report.complete_dossier_count == dossier_batch.complete_dossier_count
    assert report.mean_probability_loss == forecast.mean_probability_loss
    assert report.worst_bucket_error == forecast.worst_bucket_error
    assert tuple(row.gate_name for row in report.gate_results) == GATE_NAMES
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.source_name for row in report.source_rows) == (
        "dossier_batch",
        "forecast_evidence",
    )
    assert report.finding_rows == ()
```

- [ ] **Step 3: Run test and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison.py -q
```

Expected: FAIL because `polymarket_alpha_lab.proposal_evidence_comparison` does not exist.

- [ ] **Step 4: Add status and finding tests**

Add tests for:

- empty or insufficient forecast evidence produces `incomplete_evidence_comparison`
- incomplete dossier batch produces `incomplete_evidence_comparison`
- ready forecast plus unstable dossier batch produces `divergent_evidence_comparison`
- unstable forecast plus ready dossier batch produces `divergent_evidence_comparison`
- finding rows match non-pass gates and are sorted by `(severity, source_name, finding_code)`

- [ ] **Step 5: Add validation and log tests**

Add tests that:

- reject non-exact forecast and dossier batch objects
- reject mutated nested forecast gate rows, forecast bucket rows, batch gate rows, and batch source rows
- reject non-`datetime` `generated_at`
- reject weak or contradictory boundary statements
- validate frozen dataclasses and row invariants
- append JSONL lines through `TradeProposalEvidenceComparisonLog`
- prove invalid reports are rejected before creating or modifying the log path

## Task 2: Scope And Export Tests

**Files:**

- Create: `tests/test_proposal_evidence_comparison_scope.py`
- Modify: `tests/test_init.py`
- Modify every sibling scope allowlist that enumerates Level 2 package-root exports
- Modify: `README.md`

- [ ] **Step 1: Write failing scope tests**

Create `tests/test_proposal_evidence_comparison_scope.py` with the same AST pattern as the Node 8 batch scope test. Required checks:

- module `__all__` equals the eight public names in this plan
- imports are limited to standard library plus `polymarket_alpha_lab.forecast_evidence` and `polymarket_alpha_lab.proposal_review_dossier_batch`
- first-party imports are import-from symbols only, not whole-module imports
- no raw observation/proposal/review, market/API, broker/client/request/session/websocket/order/execution/account/credential, scraping/browser automation, settlement/reconciliation, compliance/legal/geographic, JSONL-read, load, replay, glob, from-file/from-log, selector, ranking, recommendation, promotion, or approval identifiers appear
- package root exports contain only the eight comparison public names for this node
- README comparison section states supplied-input, report-only, no-read, no-fetch, no-ranking, no-recommendation, no-approval, no-execution boundaries

- [ ] **Step 2: Add package-root export tests**

Extend `tests/test_init.py` with `test_level_2_node_9_public_api_exports()` using the existing identity-assertion pattern for all eight public names.

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_scope.py tests/test_init.py -q
```

Expected: FAIL because module/root exports do not exist.

## Task 3: Implementation

**Files:**

- Create: `src/polymarket_alpha_lab/proposal_evidence_comparison.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`

- [ ] **Step 1: Implement minimal production module**

Implementation requirements:

- follow the helper patterns from `forecast_evidence.py` and `proposal_review_dossier_batch.py`
- clone/revalidate both supplied report trees before aggregation
- build gate rows ordered by `GATE_NAMES`
- build source rows sorted by `source_name`
- build metric rows sorted by `(source_name, metric_name)`
- build finding rows from non-pass gates
- validate all row/report invariants in `__post_init__`
- use `_json_ready(asdict(report))` with `allow_nan=False` and `sort_keys=True`
- write JSONL only after full validation
- do not import raw observations, proposal packets, review records, market data, browser tooling, HTTP clients, account modules, order modules, or credential modules

- [ ] **Step 2: Add root exports**

Add the eight comparison public names to `src/polymarket_alpha_lab/__init__.py` import blocks and `__all__`.

- [ ] **Step 3: Run focused tests and verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison.py tests/test_proposal_evidence_comparison_scope.py tests/test_init.py -q
```

Expected: PASS.

## Task 4: README And Plan Layout

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Add Level 2 Node 9 documentation**

Insert sections before `## Automation Roadmap`:

```markdown
## Level 2 Node 9 Status

Level 2 Node 9 adds report-only proposal evidence comparison artifacts over supplied `PaperForecastEvidenceReport` and `TradeProposalReviewDossierBatchReport` values. It compares forecast evidence health and proposal-review dossier batch health for audit only; it is not an approval workflow, proposal approval step, approved-proposal selector, latest-decision selector, decision-resolution process, investment ranking, trade recommendation, strategy-promotion signal, trade instruction, order instruction, broker request, order request, account action, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle credentials/private keys; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use trading SDK/broker/execution/transport clients; build broker or order request payloads; reconcile exchange accounts; perform reconciliation; review settlement; import manual executions; approve proposals; select latest decisions; resolve conflicting reviews; rank investments; recommend trades; or perform compliance/legal/geographic analysis.

## Level 2 Node 9 Python API

Node 9 is exposed through Python APIs:

- Configure evidence comparisons with `TradeProposalEvidenceComparisonConfig(config_version="comparison-v1")`.
- Build evidence comparison reports with `build_trade_proposal_evidence_comparison_report(forecast_evidence=forecast, dossier_batch=batch, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalEvidenceComparisonReport`.
- Inspect comparison gates with `TradeProposalEvidenceComparisonGateResult`, source rows with `TradeProposalEvidenceComparisonSourceRow`, metric rows with `TradeProposalEvidenceComparisonMetricRow`, and finding rows with `TradeProposalEvidenceComparisonFindingRow`.
- Persist comparison snapshots with `TradeProposalEvidenceComparisonLog(path).append(report)`.
```

Update repository layout entries for the new plan, source module, behavior test, and scope test.

- [ ] **Step 2: Run README-sensitive tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_scope.py -q
```

Expected: PASS after implementation.

## Task 5: Verification, opencode Review, Handoff, Commit, Push

**Files:**

- Modify this plan file with checkbox progress and handoff evidence during execution.

- [ ] **Step 1: Run verification**

Run:

```bash
.venv/bin/python -m pytest -q
git diff --check
codegraph sync
codegraph status .
git status --short --branch --untracked-files=all
```

Expected:

- pytest: all tests pass.
- `git diff --check`: exit 0.
- CodeGraph: index up to date.
- Git status: only intended Node 9 files modified/untracked.

- [ ] **Step 2: opencode implementation review**

Run local opencode with model `zhipuai-coding-plan/glm-5.2` and variant `max`. The implementation review prompt must treat any raw observation/proposal/review dependency, data fetch, external-history load, JSONL read, scraping/browser automation, auth/credential/wallet/broker/execution/request/session/websocket/order surface, approval workflow, approved-proposal selection, decision resolution, ranking, recommendation, promotion, settlement, reconciliation, manual execution import, or compliance/legal/geographic analysis as Critical.

Accepted terminal state: `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed` or `Verdict: Proceed with fixes`. Fix every Critical and Important finding before commit.

- [ ] **Step 3: Append Handoff Summary**

Append actual evidence:

```markdown
## Handoff Summary

- Node completed: Level 2 Node 9 proposal evidence comparison.
- Commit: pending at handoff-write time; final assistant response must report commit hash after commit.
- Pushed: pending at handoff-write time; final assistant response must report push result after push.
- Repo status before commit: <git status output>
- Verification commands:
  - `.venv/bin/python -m pytest -q`: <pass/fail summary>
  - `git diff --check`: <pass/fail summary>
  - `codegraph sync`: <pass/fail summary>
  - `codegraph status .`: <up-to-date/stale summary>
  - opencode implementation review: <Critical/Important/Minor counts and verdict>
- Files changed:
  - `src/polymarket_alpha_lab/proposal_evidence_comparison.py`
  - `src/polymarket_alpha_lab/__init__.py`
  - `tests/test_proposal_evidence_comparison.py`
  - `tests/test_proposal_evidence_comparison_scope.py`
  - `tests/test_init.py`
  - scope allowlist tests
  - `README.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison.md`
- Uncommitted files after push: pending at handoff-write time; final assistant response must report post-push status.
- Next safe step: proposal review false-positive analysis over supplied comparison reports can be planned, but it must remain report-only and require a new opencode-reviewed plan before implementation.
```

- [ ] **Step 4: Commit and push**

Stage every intended Node 9 file, commit with:

```bash
git commit -m "feat: add proposal evidence comparison reports"
git push origin main
```

Expected: push succeeds and final status is clean against `origin/main`.

## Self-Review

- Spec coverage: The plan creates a supplied-input, report-only evidence comparison layer and does not add fetching, scraping, JSONL reads, proposal approval, decision resolution, investment ranking, trade recommendations, credential handling, order placement, settlement/reconciliation work, manual execution import, or compliance/legal/geographic analysis.
- Placeholder scan: The plan contains no TBD/TODO placeholders. Public API, statuses, gate rules, validation rules, scope tests, README requirements, verification commands, opencode review policy, and handoff fields are specified.
- Type consistency: The same names are used throughout: `TradeProposalEvidenceComparisonConfig`, `TradeProposalEvidenceComparisonGateResult`, `TradeProposalEvidenceComparisonSourceRow`, `TradeProposalEvidenceComparisonMetricRow`, `TradeProposalEvidenceComparisonFindingRow`, `TradeProposalEvidenceComparisonReport`, `TradeProposalEvidenceComparisonLog`, and `build_trade_proposal_evidence_comparison_report`.

## Handoff Summary

- Node completed: Level 2 Node 9 proposal evidence comparison.
- Commit: pending at handoff-write time; final assistant response must report commit hash after commit.
- Pushed: pending at handoff-write time; final assistant response must report push result after push.
- Repo status before commit:

```text
## main...origin/main
 M README.md
 M docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison.md
 M src/polymarket_alpha_lab/__init__.py
 M tests/test_analytics_history_scope.py
 M tests/test_analytics_scope.py
 M tests/test_forecast_evidence_scope.py
 M tests/test_init.py
 M tests/test_manual_review_queue_scope.py
 M tests/test_proposal_packet_scope.py
 M tests/test_proposal_review_coverage_scope.py
 M tests/test_proposal_review_diagnostics_scope.py
 M tests/test_proposal_review_dossier_batch_scope.py
 M tests/test_proposal_review_dossier_scope.py
 M tests/test_proposal_review_quality_scope.py
 M tests/test_proposal_review_scope.py
 M tests/test_proposal_review_summary_scope.py
?? docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history.md
?? src/polymarket_alpha_lab/proposal_evidence_comparison.py
?? tests/test_proposal_evidence_comparison.py
?? tests/test_proposal_evidence_comparison_scope.py
```

- Verification commands:
  - `.venv/bin/python -m pytest -q`: `627 passed in 4.51s`
  - `git diff --check`: exit 0, no output
  - `codegraph sync`: already up to date
  - `codegraph status .`: index up to date, 67 Python files, 2,286 nodes, 7,378 edges
  - opencode implementation review: Critical 0, Important 0, Minor 3, Verdict: Proceed
  - opencode next-stage Node 10 plan first review: Critical 0, Important 2, Minor 4, Verdict: Proceed with fixes
  - opencode next-stage Node 10 plan re-review: Critical 0, Important 0, Minor 3, Verdict: Proceed
- Files changed:
  - `src/polymarket_alpha_lab/proposal_evidence_comparison.py`
  - `src/polymarket_alpha_lab/__init__.py`
  - `tests/test_proposal_evidence_comparison.py`
  - `tests/test_proposal_evidence_comparison_scope.py`
  - `tests/test_init.py`
  - `tests/test_analytics_scope.py`
  - `tests/test_analytics_history_scope.py`
  - `tests/test_forecast_evidence_scope.py`
  - `tests/test_manual_review_queue_scope.py`
  - `tests/test_proposal_packet_scope.py`
  - `tests/test_proposal_review_scope.py`
  - `tests/test_proposal_review_summary_scope.py`
  - `tests/test_proposal_review_quality_scope.py`
  - `tests/test_proposal_review_diagnostics_scope.py`
  - `tests/test_proposal_review_coverage_scope.py`
  - `tests/test_proposal_review_dossier_scope.py`
  - `tests/test_proposal_review_dossier_batch_scope.py`
  - `README.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history.md`
- Uncommitted files after push: pending at handoff-write time; final assistant response must report post-push status.
- Next safe step: implement the opencode-reviewed Level 2 Node 10 proposal evidence comparison history plan, keeping it report-only over supplied Node 9 comparison reports and avoiding JSONL readers, data fetching, approval, ranking, recommendation, outcome/settlement analysis, credentials, and execution surfaces.
