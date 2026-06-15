# Level 2 Proposal Evidence Comparison History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a report-only history artifact that summarizes caller-supplied proposal evidence comparison reports for human audit.

**Architecture:** Create a focused `proposal_evidence_comparison_history.py` module that accepts only in-memory `TradeProposalEvidenceComparisonReport` objects from Level 2 Node 9. It clones/revalidates each comparison report tree, summarizes status counts, finding-code frequencies, config-version coverage, source-status transitions, and rate gates, then optionally appends a validated JSONL snapshot. The artifact is an offline divergence proxy only: it never reads logs, fetches outcomes, ranks investments, recommends trades, approves proposals, handles credentials, or touches execution surfaces.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, UTC `datetime`, JSONL append-only persistence, pytest, CodeGraph, and local opencode review with model `zhipuai-coding-plan/glm-5.2` using variant `max`.

---

## Scope Boundaries

This node consumes only caller-supplied, in-memory `TradeProposalEvidenceComparisonReport` objects from `polymarket_alpha_lab.proposal_evidence_comparison`. The word "history" means an ordered summary over objects supplied by the caller, not file discovery, log replay, archive loading, or historical data fetching.

This node must not consume raw `PaperForecastEvidenceReport` values, raw `TradeProposalReviewDossierBatchReport` values, raw forecast observations, raw proposal packets, raw proposal-review records, dossier reports, market scores, order books, paper positions, NAV snapshots, API payloads, JSONL files, archived payloads, external history, web pages, account state, credentials, wallets, broker payloads, execution records, outcome data, settlement data, or reconciliation data.

This node must not fetch market/order-book/price/outcome/account data, read JSONL logs, replay history, glob files, scrape websites, run browser automation, authenticate, handle credentials or private keys, open user WebSockets, run heartbeat logic, build order requests, place/submit/sign/send/create/cancel orders, select approved proposals, select latest decisions, resolve conflicting reviews, rank investments, recommend trades, promote strategies, review settlement, reconcile positions or exchange accounts, import manual executions, or perform compliance/legal/geographic analysis.

This node must reject convenience inputs that would imply a loader surface: strings, bytes, mappings/dicts, paths, serialized JSON, JSONL lines, and subclasses of `TradeProposalEvidenceComparisonReport`.

Use the phrase "divergence proxy" for repeated mismatch summaries. Do not call the output realized false-positive analysis, trade outcome analysis, settlement analysis, or profitability analysis.

Allowed first-party imports are limited to import-from symbols from `polymarket_alpha_lab.proposal_evidence_comparison`:

```python
TradeProposalEvidenceComparisonFindingRow
TradeProposalEvidenceComparisonGateResult
TradeProposalEvidenceComparisonMetricRow
TradeProposalEvidenceComparisonReport
TradeProposalEvidenceComparisonSourceRow
```

Do not import `TradeProposalEvidenceComparisonLog`; it is an output persistence helper and is not an input source for this node.

Do not import `TradeProposalEvidenceComparisonConfig` or `build_trade_proposal_evidence_comparison_report`; this node summarizes already-built comparison reports and must not rebuild Node 9 reports.

## Public API

Create `src/polymarket_alpha_lab/proposal_evidence_comparison_history.py` with:

```python
__all__ = (
    "TradeProposalEvidenceComparisonHistoryConfig",
    "TradeProposalEvidenceComparisonHistoryGateResult",
    "TradeProposalEvidenceComparisonHistoryStatusRow",
    "TradeProposalEvidenceComparisonHistoryFindingSummary",
    "TradeProposalEvidenceComparisonHistoryConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistorySourceTransition",
    "TradeProposalEvidenceComparisonHistoryReport",
    "TradeProposalEvidenceComparisonHistoryLog",
    "build_trade_proposal_evidence_comparison_history_report",
)
```

Define `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT` exactly as:

```python
DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT = (
    "This is a report-only proposal evidence comparison history artifact over "
    "supplied proposal evidence comparison reports, not an approval workflow, "
    "proposal approval, approved-proposal selector, latest-decision selector, "
    "decision-resolution process, investment ranking, trade recommendation, "
    "strategy-promotion signal, trade instruction, order instruction, broker "
    "request, order request, account action, account authentication, private-key "
    "handling, wallet signature, live-execution signal, credential workflow, "
    "external-history loader, JSONL reader, scraping workflow, outcome loader, "
    "settlement review, reconciliation process, compliance review, geographic "
    "access analysis, realized false-positive analysis, profitability analysis, "
    "or automatic order-placement authorization."
)
```

`_require_boundary_statement` must normalize by lowercasing and keeping only alphanumeric characters, then require equality to the normalized default boundary statement.

Public dataclasses:

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryConfig:
    config_version: str
    min_comparison_count: int = 1
    max_incomplete_comparison_ratio: Decimal = Decimal("0.0000")
    max_divergent_comparison_ratio: Decimal = Decimal("0.0000")
    max_unstable_comparison_ratio: Decimal = Decimal("0.0000")
    boundary_statement: str = (
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT
    )
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryStatusRow:
    comparison_status: str
    comparison_count: int
    comparison_ratio: Decimal | None
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryFindingSummary:
    finding_code: str
    severity: str
    source_name: str
    comparison_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryConfigVersionSummary:
    comparison_config_version: str
    comparison_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistorySourceTransition:
    source_name: str
    from_source_status: str
    to_source_status: str
    transition_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    comparison_count: int
    complete_comparison_count: int
    incomplete_comparison_count: int
    divergent_comparison_count: int
    unstable_comparison_count: int
    incomplete_comparison_ratio: Decimal | None
    divergent_comparison_ratio: Decimal | None
    unstable_comparison_ratio: Decimal | None
    first_comparison_generated_at: datetime | None
    last_comparison_generated_at: datetime | None
    status: str
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryGateResult, ...]
    status_rows: tuple[TradeProposalEvidenceComparisonHistoryStatusRow, ...]
    finding_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryFindingSummary,
        ...,
    ]
    config_version_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryConfigVersionSummary,
        ...,
    ]
    source_transitions: tuple[
        TradeProposalEvidenceComparisonHistorySourceTransition,
        ...,
    ]
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryLog:
    path: Path | str

    def append(self, report: TradeProposalEvidenceComparisonHistoryReport) -> None:
        ...
```

Builder signature:

```python
def build_trade_proposal_evidence_comparison_history_report(
    comparisons: Iterable[TradeProposalEvidenceComparisonReport],
    *,
    config: TradeProposalEvidenceComparisonHistoryConfig,
    generated_at: datetime,
) -> TradeProposalEvidenceComparisonHistoryReport:
    ...
```

## Status And Gate Rules

Gate names:

```python
GATE_NAMES = (
    "comparison_sample",
    "incomplete_comparison_rate",
    "divergent_comparison_rate",
    "unstable_comparison_rate",
)
```

Gate statuses are `pass`, `fail`, or `incomplete`.

Report statuses:

```python
REPORT_STATUSES = (
    "incomplete_comparison_history",
    "divergent_comparison_history",
    "unstable_comparison_history",
    "proposal_evidence_comparison_history_ready",
)
```

Status mapping:

- If `comparison_sample` is `incomplete`, report status is `incomplete_comparison_history`.
- Else if `divergent_comparison_rate` is `fail`, report status is `divergent_comparison_history`.
- Else if `unstable_comparison_rate` is `fail`, report status is `unstable_comparison_history`.
- Else if `incomplete_comparison_rate` is `fail`, report status is `incomplete_comparison_history`.
- Else if any gate is `incomplete`, report status is `incomplete_comparison_history`.
- Else report status is `proposal_evidence_comparison_history_ready`.

Gate semantics:

- `comparison_sample`: pass when `comparison_count >= config.min_comparison_count`; incomplete otherwise. Observed value is `comparison_count`; threshold is `config.min_comparison_count`.
- `incomplete_comparison_rate`: incomplete when `incomplete_comparison_ratio is None`, pass when ratio is less than or equal to `config.max_incomplete_comparison_ratio`, fail otherwise.
- `divergent_comparison_rate`: incomplete when `divergent_comparison_ratio is None`, pass when ratio is less than or equal to `config.max_divergent_comparison_ratio`, fail otherwise.
- `unstable_comparison_rate`: incomplete when `unstable_comparison_ratio is None`, pass when ratio is less than or equal to `config.max_unstable_comparison_ratio`, fail otherwise.

Counting rules:

- `complete_comparison_count`: number of supplied reports with status `proposal_evidence_comparison_complete`.
- `incomplete_comparison_count`: number of supplied reports with status `incomplete_evidence_comparison`.
- `divergent_comparison_count`: number of supplied reports with status `divergent_evidence_comparison`.
- `unstable_comparison_count`: number of supplied reports with status `unstable_evidence_comparison`.
- Ratios are `None` when `comparison_count == 0`; otherwise quantize to `Decimal("0.0001")` with `ROUND_HALF_EVEN`.

Rows:

- `status_rows`: exactly one row per Node 9 comparison status, sorted by `comparison_status`. `comparison_ratio` is `None` when `comparison_count == 0`; otherwise it is `status_count / comparison_count` quantized to `Decimal("0.0001")` with `ROUND_HALF_EVEN`.
- `finding_summaries`: one row per distinct `(severity, source_name, finding_code)` found across supplied comparison reports, sorted by that tuple. Count each finding code at most once per comparison report, even if a malformed input duplicates a row; malformed input should be rejected during clone/revalidation before summary.
- `config_version_summaries`: one row per distinct comparison `config_version`, sorted by `comparison_config_version`.
- `source_transitions`: source-status transitions within each `source_name`, sorted by `(source_name, from_source_status, to_source_status)`. Build transitions by sorting cloned comparison reports by `(generated_at, config_version, forecast_status, dossier_batch_status)` and comparing adjacent source rows with the same `source_name`. This is a descriptive transition count only, not a forecast, promotion signal, or recommendation.

Validation requirements:

- Reject strings, bytes, mappings/dicts, `Path` values, serialized JSON, JSONL lines, and any non-iterable convenience input before iterating comparison values.
- Reject non-exact `TradeProposalEvidenceComparisonReport` inputs.
- Clone/revalidate every comparison report by reconstructing all Node 9 gate, source, metric, finding, and report dataclasses.
- Reject duplicate comparison `generated_at` values rather than resolving, deduplicating, selecting, or preferring a latest object.
- Validate all row tuples are exact typed tuples.
- Validate `gate_results` order equals `GATE_NAMES`.
- Validate `status_rows` contain exactly the four Node 9 comparison statuses sorted by `comparison_status`.
- Validate `complete_comparison_count + incomplete_comparison_count + divergent_comparison_count + unstable_comparison_count == comparison_count`.
- Validate `finding_summaries` are sorted by `(severity, source_name, finding_code)` and contain no duplicate keys.
- Validate `config_version_summaries` are sorted by `comparison_config_version`, contain no duplicate versions, and counts sum to `comparison_count`.
- Validate `source_transitions` are sorted by `(source_name, from_source_status, to_source_status)` and contain no duplicate keys.
- Validate `first_comparison_generated_at` and `last_comparison_generated_at` are both `None` when `comparison_count == 0`, both present when `comparison_count > 0`, and `first_comparison_generated_at <= last_comparison_generated_at`.
- Validate `status` matches gate results.
- Validate `report_only is True`.
- Validate the exact normalized boundary statement.
- Validate all ratio fields are finite `Decimal` values between zero and one when present.
- Reject floats and bools in gate values.
- `TradeProposalEvidenceComparisonHistoryLog.append(report)` must validate the full report tree and call `json.dumps(..., allow_nan=False, sort_keys=True)` before opening or creating the file.
- Production code must not provide JSONL readers, loaders, replay helpers, glob helpers, `from_file`, `from_log`, selectors, ranking helpers, recommendation helpers, approval helpers, outcome helpers, settlement helpers, reconciliation helpers, profitability helpers, or execution helpers.

## Task 1: Behavior Tests

**Files:**

- Create: `tests/test_proposal_evidence_comparison_history.py`

- [ ] **Step 1: Write deterministic fixtures**

Reuse Node 9 behavior-test fixtures rather than duplicating raw setup:

```python
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

from tests.test_proposal_evidence_comparison import (
    build_comparison,
    insufficient_forecast_fixture,
    ready_dossier_batch_fixture,
    ready_forecast_fixture,
    unstable_dossier_batch_fixture,
    unstable_forecast_fixture,
)


def complete_comparison_fixture(index=1):
    report = build_comparison(
        forecast=ready_forecast_fixture(),
        dossier_batch=ready_dossier_batch_fixture(),
    )
    return replace(report, generated_at=datetime(2026, 9, 11, index, tzinfo=UTC))


def divergent_comparison_fixture(index=2):
    report = build_comparison(
        forecast=insufficient_forecast_fixture(),
        dossier_batch=ready_dossier_batch_fixture(),
    )
    return replace(report, generated_at=datetime(2026, 9, 11, index, tzinfo=UTC))


def unstable_comparison_fixture(index=3):
    report = build_comparison(
        forecast=unstable_forecast_fixture(),
        dossier_batch=unstable_dossier_batch_fixture(),
    )
    return replace(report, generated_at=datetime(2026, 9, 11, index, tzinfo=UTC))
```

Use `dataclasses.replace(report, generated_at=datetime(...))` on already-built Node 9 reports; the Node 10 clone/revalidate step must accept valid replacement reports and reject invalid mutated reports.

- [ ] **Step 2: Write happy-path history test**

```python
def test_build_trade_proposal_evidence_comparison_history_report_summarizes_reports():
    complete = complete_comparison_fixture()
    divergent = divergent_comparison_fixture()
    unstable = unstable_comparison_fixture()

    report = build_trade_proposal_evidence_comparison_history_report(
        [complete, divergent, unstable],
        config=TradeProposalEvidenceComparisonHistoryConfig(
            config_version="comparison-history-v1",
            max_divergent_comparison_ratio=Decimal("1.0000"),
            max_unstable_comparison_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )

    assert report.report_only is True
    assert report.status == "proposal_evidence_comparison_history_ready"
    assert report.comparison_count == 3
    assert report.complete_comparison_count == 1
    assert report.divergent_comparison_count == 1
    assert report.unstable_comparison_count == 1
    assert report.divergent_comparison_ratio == Decimal("0.3333")
    assert tuple(row.gate_name for row in report.gate_results) == GATE_NAMES
    assert tuple(row.comparison_status for row in report.status_rows) == (
        "divergent_evidence_comparison",
        "incomplete_evidence_comparison",
        "proposal_evidence_comparison_complete",
        "unstable_evidence_comparison",
    )
    assert tuple(
        row.comparison_config_version for row in report.config_version_summaries
    ) == ("comparison-v1",)
    assert report.finding_summaries
    assert all(row.transition_count >= 1 for row in report.source_transitions)
```

- [ ] **Step 3: Run test and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history.py -q
```

Expected: FAIL because `polymarket_alpha_lab.proposal_evidence_comparison_history` does not exist.

- [ ] **Step 4: Add status and gate tests**

Add tests for:

- empty comparison input produces `incomplete_comparison_history`
- duplicate `generated_at` values are rejected
- too many divergent reports produces `divergent_comparison_history`
- too many unstable reports produces `unstable_comparison_history`
- too many incomplete reports produces `incomplete_comparison_history`
- relaxed thresholds produce `proposal_evidence_comparison_history_ready`
- rate rows use `None` when the sample is empty and quantized ratios otherwise

- [ ] **Step 5: Add validation and log tests**

Add tests that:

- reject non-exact comparison report objects
- reject strings, bytes, dicts, `Path` values, serialized JSON strings, raw `PaperForecastEvidenceReport` values, and raw `TradeProposalReviewDossierBatchReport` values
- reject mutated nested comparison gate rows, source rows, metric rows, and finding rows
- prove a built history report keeps copied summary values stable after the caller mutates an original supplied comparison report
- reject non-`datetime` `generated_at`
- reject weak or contradictory boundary statements
- validate frozen dataclasses and row invariants
- append JSONL lines through `TradeProposalEvidenceComparisonHistoryLog`
- prove invalid reports are rejected before creating or modifying the log path

## Task 2: Scope And Export Tests

**Files:**

- Create: `tests/test_proposal_evidence_comparison_history_scope.py`
- Modify: `tests/test_init.py`
- Modify every sibling scope allowlist that enumerates Level 2 package-root exports
- Modify: `README.md`

- [ ] **Step 1: Write failing scope tests**

Create `tests/test_proposal_evidence_comparison_history_scope.py` with the same AST pattern as the Node 9 scope test. Required checks:

- module `__all__` equals the nine public names in this plan
- imports are limited to standard library plus `polymarket_alpha_lab.proposal_evidence_comparison`
- first-party imports are import-from symbols only, not whole-module imports
- no raw forecast/dossier/proposal/review, market/API, broker/client/request/session/websocket/order/execution/account/credential, scraping/browser automation, outcome, settlement/reconciliation, compliance/legal/geographic, JSONL-read, load, replay, glob, from-file/from-log, selector, ranking, recommendation, promotion, approval, profitability, or realized false-positive identifiers appear
- package root exports contain only the nine comparison-history public names for this node
- README comparison-history section states supplied-input, report-only, no-read, no-fetch, no-outcome, no-settlement, no-ranking, no-recommendation, no-approval, no-execution boundaries
- README comparison-history scope test asserts these exact normalized fragments inside the section from `## Level 2 Node 10 Status` to `## Automation Roadmap`:
  - `level2node10status`
  - `level2node10pythonapi`
  - `reportonlyproposalevidencecomparisonhistoryartifacts`
  - `suppliedtradeproposalevidencecomparisonreport`
  - `divergenceproxy`
  - `appendonlyjsonl`
  - `notanapprovalworkflow`
  - `proposalapproval`
  - `approvedproposalselector`
  - `latestdecisionselector`
  - `decisionresolution`
  - `investmentranking`
  - `traderecommendation`
  - `strategypromotionsignal`
  - `tradeinstruction`
  - `orderinstruction`
  - `brokerrequest`
  - `orderrequest`
  - `accountaction`
  - `outcomeloader`
  - `realizedfalsepositiveanalysis`
  - `profitabilityanalysis`
  - `liveexecutionsignal`
  - `doesnotfetchmarketorderbookpricehistoryoutcomeaccountcredentialidentityorsettlementdata`
  - `readexternalhistoryorjsonllogs`
  - `scrapewebsites`
  - `authenticate`
  - `credentialsprivatekeys`
  - `placesubmitsignsendcreateorcancelorders`
  - `openuserwebsockets`
  - `heartbeat`
  - `tradingsdkbrokerexecutiontransportclients`
  - `brokerororderrequestpayloads`
  - `reconcileexchangeaccounts`
  - `reconciliation`
  - `settlement`
  - `importmanualexecutions`
  - `approveproposals`
  - `selectlatestdecisions`
  - `resolveconflictingreviews`
  - `rankinvestments`
  - `recommendtrades`
  - `compliancelegalgeographicanalysis`
- README repository-layout scope test `test_readme_repository_layout_lists_level_2_node_10_artifacts()` asserts these exact paths/names are present:
  - `2026-06-15-level-2-proposal-evidence-comparison-history.md`
  - `proposal_evidence_comparison_history.py`
  - `test_proposal_evidence_comparison_history.py`
  - `test_proposal_evidence_comparison_history_scope.py`

- [ ] **Step 2: Add package-root export tests**

Extend `tests/test_init.py` with `test_level_2_node_10_public_api_exports()` using the existing identity-assertion pattern for all nine public names.

Update every duplicated Level 2 package-root allowlist by adding `EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_EXPORTS` and including it in `EXPECTED_LEVEL_2_ARTIFACT_EXPORTS`:

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
- `tests/test_proposal_evidence_comparison_scope.py`

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_scope.py tests/test_init.py -q
```

Expected: FAIL because module/root exports do not exist.

## Task 3: Implementation

**Files:**

- Create: `src/polymarket_alpha_lab/proposal_evidence_comparison_history.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`

- [ ] **Step 1: Implement minimal production module**

Implementation requirements:

- follow helper patterns from `proposal_evidence_comparison.py` and `proposal_review_dossier_batch.py`
- clone/revalidate every supplied Node 9 comparison report before aggregation
- reject duplicate comparison `generated_at` values instead of resolving or selecting between them
- build gate rows ordered by `GATE_NAMES`
- build status rows sorted by `comparison_status`
- build finding summaries sorted by `(severity, source_name, finding_code)`
- build config-version summaries sorted by `comparison_config_version`
- build source transitions sorted by `(source_name, from_source_status, to_source_status)`
- validate all row/report invariants in `__post_init__`
- use `_json_ready(asdict(report))` with `allow_nan=False` and `sort_keys=True`
- write JSONL only after full validation
- do not import raw forecast reports, dossier batch reports, raw observations, proposal packets, review records, market data, browser tooling, HTTP clients, account modules, order modules, outcome modules, settlement modules, reconciliation modules, profitability modules, or credential modules

- [ ] **Step 2: Add root exports**

Add the nine comparison-history public names to `src/polymarket_alpha_lab/__init__.py` import blocks and `__all__`.

- [ ] **Step 3: Run focused tests and verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history.py tests/test_proposal_evidence_comparison_history_scope.py tests/test_init.py -q
```

Expected: PASS.

## Task 4: README And Plan Layout

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Add Level 2 Node 10 documentation**

Insert sections before `## Automation Roadmap`:

```markdown
## Level 2 Node 10 Status

Level 2 Node 10 adds report-only proposal evidence comparison history artifacts over supplied `TradeProposalEvidenceComparisonReport` values. It summarizes comparison statuses, divergence proxy rates, finding-code frequencies, config-version coverage, source-status transitions, and append-only JSONL persistence for audit only; it is not an approval workflow, proposal approval step, approved-proposal selector, latest-decision selector, decision-resolution process, investment ranking, trade recommendation, strategy-promotion signal, trade instruction, order instruction, broker request, order request, account action, outcome loader, realized false-positive analysis, profitability analysis, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, identity, or settlement data; read external history or JSONL logs; scrape websites; authenticate; handle credentials/private keys; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use trading SDK/broker/execution/transport clients; build broker or order request payloads; reconcile exchange accounts; perform reconciliation; review settlement; import manual executions; approve proposals; select latest decisions; resolve conflicting reviews; rank investments; recommend trades; or perform compliance/legal/geographic analysis.

## Level 2 Node 10 Python API

Node 10 is exposed through Python APIs:

- Configure comparison-history reports with `TradeProposalEvidenceComparisonHistoryConfig(config_version="comparison-history-v1")`.
- Build comparison-history reports with `build_trade_proposal_evidence_comparison_history_report(comparisons, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalEvidenceComparisonHistoryReport`.
- Inspect history gates with `TradeProposalEvidenceComparisonHistoryGateResult`, status rows with `TradeProposalEvidenceComparisonHistoryStatusRow`, finding summaries with `TradeProposalEvidenceComparisonHistoryFindingSummary`, config-version summaries with `TradeProposalEvidenceComparisonHistoryConfigVersionSummary`, and source transitions with `TradeProposalEvidenceComparisonHistorySourceTransition`.
- Persist comparison-history snapshots with `TradeProposalEvidenceComparisonHistoryLog(path).append(report)`.
```

Update repository layout entries for the new plan, source module, behavior test, and scope test.

- [ ] **Step 2: Run README-sensitive tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_scope.py -q
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
- Git status: only intended Node 10 files modified/untracked.

- [ ] **Step 2: opencode implementation review**

Run local opencode with model `zhipuai-coding-plan/glm-5.2` and variant `max`. The implementation review prompt must treat any raw upstream report dependency beyond Node 9 comparison reports, raw observation/proposal/review dependency, data fetch, external-history load, JSONL read, scraping/browser automation, auth/credential/wallet/broker/execution/request/session/websocket/order surface, approval workflow, approved-proposal selection, decision resolution, ranking, recommendation, promotion, outcome loading, realized false-positive analysis, profitability analysis, settlement, reconciliation, manual execution import, or compliance/legal/geographic analysis as Critical.

Accepted terminal state: `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed` or `Verdict: Proceed with fixes`. Fix every Critical and Important finding before commit.

- [ ] **Step 3: Append Handoff Summary**

Append actual evidence:

```markdown
## Handoff Summary

- Node completed: Level 2 Node 10 proposal evidence comparison history.
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
  - `src/polymarket_alpha_lab/proposal_evidence_comparison_history.py`
  - `src/polymarket_alpha_lab/__init__.py`
  - `tests/test_proposal_evidence_comparison_history.py`
  - `tests/test_proposal_evidence_comparison_history_scope.py`
  - `tests/test_init.py`
  - scope allowlist tests
  - `README.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history.md`
- Uncommitted files after push: pending at handoff-write time; final assistant response must report post-push status.
- Next safe step: forecast and review dossier evidence can be compared by human analysts using the history report, but any automated routing, ranking, recommendation, settlement/outcome analysis, or execution planning requires a new opencode-reviewed plan.
```

- [ ] **Step 4: Commit and push**

Stage every intended Node 10 file, commit with:

```bash
git commit -m "feat: add proposal evidence comparison history reports"
git push origin main
```

Expected: push succeeds and final status is clean against `origin/main`.

## Self-Review

- Spec coverage: The plan creates a supplied-input, report-only comparison-history layer over Node 9 reports and does not add fetching, scraping, JSONL reads, raw upstream report ingestion, outcome loading, realized false-positive analysis, profitability analysis, proposal approval, decision resolution, investment ranking, trade recommendations, credential handling, order placement, settlement/reconciliation work, manual execution import, or compliance/legal/geographic analysis.
- Placeholder scan: The plan contains no TBD/TODO placeholders. Public API, statuses, gate rules, counting rules, validation rules, scope tests, README requirements, verification commands, opencode review policy, and handoff fields are specified.
- Type consistency: The same names are used throughout: `TradeProposalEvidenceComparisonHistoryConfig`, `TradeProposalEvidenceComparisonHistoryGateResult`, `TradeProposalEvidenceComparisonHistoryStatusRow`, `TradeProposalEvidenceComparisonHistoryFindingSummary`, `TradeProposalEvidenceComparisonHistoryConfigVersionSummary`, `TradeProposalEvidenceComparisonHistorySourceTransition`, `TradeProposalEvidenceComparisonHistoryReport`, `TradeProposalEvidenceComparisonHistoryLog`, and `build_trade_proposal_evidence_comparison_history_report`.
