# Level 2 Proposal Evidence Comparison History Batch Health Trend Batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a report-only batch artifact that summarizes caller-supplied proposal evidence comparison history batch-health trend reports for audit-health checks.

**Architecture:** Create a focused `proposal_evidence_comparison_history_batch_health_trend_batch.py` module that consumes only in-memory `TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport` objects from Level 2 Node 12. It clones and revalidates each supplied trend report, then summarizes trend-report status frequencies, trend-gate status frequencies, config-version coverage, duplicate generated-at indicators, duplicate fingerprint indicators, and first/last trend-report time bounds for audit only, with append-only JSONL persistence for already-built trend-batch snapshots.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, UTC `datetime`, JSONL append-only persistence, pytest, CodeGraph, and local Claude Code review with model `claude-opus-4-8` using effort `max`.

---

## Scope Boundaries

This node consumes only caller-supplied, in-memory `TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport` objects from `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend`. The word "batch" means a supplied-object audit batch over Node 12 trend reports, not file discovery, log replay, archive loading, globbing, historical data fetching, or performance/outcome analysis.

This node must not consume Node 11 batch-health reports, raw Node 10 history reports, raw Node 9 comparison reports, raw forecast evidence reports, raw dossier batch reports, raw proposal packets, raw proposal-review records, market scores, order books, paper positions, NAV snapshots, API payloads, JSONL files, archived payloads, external history, web pages, account state, credentials, wallets, broker payloads, execution records, outcome data, settlement data, reconciliation data, or compliance/legal/geographic inputs.

This node must not fetch market/order-book/price/outcome/account data, read JSONL logs, replay history, glob files, scrape websites, run browser automation, authenticate, handle credentials or private keys, open user WebSockets, run heartbeat logic, build order requests, place/submit/sign/send/create/cancel orders, select approved proposals, select latest decisions, resolve conflicting reviews, rank investments, recommend trades, promote strategies, review settlement, reconcile positions or exchange accounts, import manual executions, or perform compliance/legal/geographic analysis.

This node must reject convenience inputs that would imply a loader surface: strings, bytes, mappings/dicts, paths, serialized JSON, JSONL lines, generators, arbitrary iterables, log-shaped objects, and subclasses of `TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport`.

Allowed first-party imports in the production module are limited to import-from symbols from `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend`:

```python
TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult
TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow
TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary
TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary
TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary
TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary
TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport
```

The production module must not import the Node 12 boundary constant, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog`, private helpers, Node 11/10/9 modules, raw upstream modules, HTTP/browser/account/order/execution modules, or any first-party module outside the allowlist above. It must implement its own local `_json_ready` helper for `Decimal`, UTC `datetime`, tuple/list, and dict normalization.

## Public API

Create `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch.py` with:

```python
__all__ = (
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report",
)
```

Define a module-internal boundary constant named `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_BOUNDARY_STATEMENT`. It must state that the artifact is report-only over supplied proposal evidence comparison history batch-health trend reports and explicitly exclude approval workflows, proposal approval, approved-proposal selectors, latest-decision selectors, decision-resolution processes, investment ranking, trade recommendations, strategy-promotion signals, trade/order instructions, broker/order requests, account actions, credential workflows, external-history loaders, JSONL readers, scraping workflows, outcome loaders, settlement review, reconciliation, compliance/legal/geographic analysis, realized false-positive analysis, profitability analysis, and automatic order-placement authorization. This constant must not be in module `__all__`, package-root imports, or package-root `__all__`.

Public dataclasses:

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig:
    config_version: str
    min_trend_report_count: int = 1
    max_incomplete_trend_ratio: Decimal = Decimal("0.0000")
    max_duplicate_generated_at_ratio: Decimal = Decimal("0.0000")
    max_duplicate_fingerprint_ratio: Decimal = Decimal("0.0000")
    boundary_statement: str = (
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_BOUNDARY_STATEMENT
    )
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow:
    trend_status: str
    trend_count: int
    trend_ratio: Decimal | None
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary:
    trend_config_version: str
    trend_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary:
    gate_name: str
    gate_status: str
    trend_count: int

    def __post_init__(self) -> None:
        if self.gate_name not in NODE_12_TREND_GATE_NAMES:
            raise ValueError("gate_name must be a known trend gate")
        if self.gate_status not in GATE_STATUSES:
            raise ValueError("gate_status must be a known gate status")
        _require_positive_int("trend_count", self.trend_count)
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary:
    generated_at: datetime
    duplicate_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary:
    report_fingerprint: str
    duplicate_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    trend_report_count: int
    ready_trend_report_count: int
    incomplete_trend_report_count: int
    duplicate_generated_at_trend_report_count: int
    duplicate_fingerprint_trend_report_count: int
    duplicate_generated_at_count: int
    duplicate_fingerprint_count: int
    incomplete_trend_ratio: Decimal | None
    duplicate_generated_at_ratio: Decimal | None
    duplicate_fingerprint_ratio: Decimal | None
    first_trend_generated_at: datetime | None
    last_trend_generated_at: datetime | None
    status: str
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult, ...]
    status_rows: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow, ...]
    config_version_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary,
        ...,
    ]
    gate_status_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary,
        ...,
    ]
    duplicate_generated_at_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary,
        ...,
    ]
    duplicate_fingerprint_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary,
        ...,
    ]
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(
        self,
        report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport,
    ) -> None:
        raise NotImplementedError("implemented in Task 3")
```

Builder signature:

```python
def build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
    trend_reports: (
        list[TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport]
        | tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport, ...]
    ),
    *,
    config: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig,
    generated_at: datetime,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport:
    raise NotImplementedError("implemented in Task 3")
```

## Status And Gate Rules

Gate names:

```python
GATE_NAMES = (
    "trend_sample",
    "incomplete_trend_rate",
    "duplicate_generated_at_rate",
    "duplicate_fingerprint_rate",
)
```

Gate statuses are `pass`, `fail`, or `incomplete`.

Report statuses:

```python
REPORT_STATUSES = (
    "incomplete_batch_health_trend_batch",
    "duplicate_generated_at_batch_health_trend_batch",
    "duplicate_fingerprint_batch_health_trend_batch",
    "proposal_evidence_comparison_history_batch_health_trend_batch_ready",
)
```

Status mapping:

- If `trend_sample` is `incomplete`, report status is `incomplete_batch_health_trend_batch`.
- Else if `duplicate_generated_at_rate` is `fail`, report status is `duplicate_generated_at_batch_health_trend_batch`.
- Else if `duplicate_fingerprint_rate` is `fail`, report status is `duplicate_fingerprint_batch_health_trend_batch`.
- Else if `incomplete_trend_rate` is `fail`, report status is `incomplete_batch_health_trend_batch`.
- Else if any gate is `incomplete`, report status is `incomplete_batch_health_trend_batch`.
- Else report status is `proposal_evidence_comparison_history_batch_health_trend_batch_ready`.

Node 12 trend statuses must be summarized in this exact sorted order:

```python
TREND_STATUSES = (
    "duplicate_fingerprint_batch_health_trend",
    "duplicate_generated_at_batch_health_trend",
    "incomplete_batch_health_trend",
    "proposal_evidence_comparison_history_batch_health_trend_ready",
)
```

Node 12 trend gates must be summarized from supplied reports in this exact allowed set:

```python
NODE_12_TREND_GATE_NAMES = (
    "batch_health_sample",
    "incomplete_batch_health_rate",
    "duplicate_generated_at_rate",
    "duplicate_fingerprint_rate",
)
```

## Counting And Ordering Rules

- Clone/revalidate every exact `TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport` before aggregation.
- Accept only exact `list` or `tuple` containers; reject strings, bytes, mappings, paths, generators, arbitrary iterables, and log-shaped objects before iteration.
- Sort cloned reports with `sorted(cloned_reports, key=lambda report: (report.generated_at, report.config_version, report.status))`.
- `first_trend_generated_at` and `last_trend_generated_at` come from sorted cloned reports' normalized UTC `generated_at` values.
- Duplicate generated-at groups are keyed by cloned report `generated_at`.
- Duplicate fingerprint groups are keyed by canonical JSON fingerprints built from each cloned report's validated JSON-ready tree.
- Duplicate counts use full collision-group sizes, not extras beyond the first item.
- `incomplete_trend_ratio` counts every supplied Node 12 trend report whose status is not `proposal_evidence_comparison_history_batch_health_trend_ready`.
- `duplicate_generated_at_ratio` and `duplicate_fingerprint_ratio` use the duplicate count over total report count.
- Ratios are `None` when `trend_report_count == 0`; otherwise quantized to `Decimal("0.0001")` with `ROUND_HALF_EVEN`.
- `status_rows` contain exactly one row per `TREND_STATUSES`, sorted as the tuple above.
- `config_version_summaries` contain one row per distinct `trend_config_version`, sorted by version.
- `gate_status_summaries` group existing Node 12 `gate_results` by `(gate_name, gate_status)` and count how many trend reports contain each pair once.
- `gate_status_summaries` validation must require both the global total `len(NODE_12_TREND_GATE_NAMES) * trend_report_count` and each individual Node 12 gate's total to equal `trend_report_count`.
- `duplicate_generated_at_summaries` and `duplicate_fingerprint_summaries` include only groups with `duplicate_count >= 2`, sorted by key.

## Task 1: Behavior Tests

**Files:**

- Create: `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch.py`

- [ ] **Step 1: Write deterministic fixtures**

Construct static `TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport` values directly from Node 12 public dataclasses. Do not import Node 11 builders, Node 10 builders, Node 9 fixtures, raw forecast/dossier/proposal/review helpers, or Node 12 log classes.

Use this concrete fixture shape:

```python
TREND_BOUNDARY = (
    "This is a report-only proposal evidence comparison history batch health trend artifact over "
    "supplied proposal evidence comparison history batch health reports, not an "
    "approval workflow, proposal approval, approved-proposal selector, "
    "latest-decision selector, decision-resolution process, investment ranking, "
    "trade recommendation, strategy-promotion signal, trade instruction, order "
    "instruction, broker request, order request, account action, account "
    "authentication, private-key handling, wallet signature, live-execution "
    "signal, credential workflow, external-history loader, JSONL reader, "
    "scraping workflow, outcome loader, settlement review, reconciliation "
    "process, compliance review, geographic access analysis, realized "
    "false-positive analysis, profitability analysis, or automatic "
    "order-placement authorization."
)


def _ratio(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(count) / Decimal(total)).quantize(Decimal("0.0001"))


def _trend_rate_gate(
    gate_name: str,
    observed_value: Decimal | None,
    threshold: Decimal = Decimal("0.0000"),
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult:
    if observed_value is None:
        status = "incomplete"
    elif observed_value <= threshold:
        status = "pass"
    else:
        status = "fail"
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult(
        gate_name,
        status,
        f"{gate_name} checked",
        observed_value,
        threshold,
    )


def trend_report_fixture(
    *,
    status: str = "proposal_evidence_comparison_history_batch_health_trend_ready",
    index: int = 1,
    generated_at: datetime | None = None,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport:
    generated_at = generated_at or datetime(2026, 9, 14, 12, index, tzinfo=UTC)
    trend_count = 2
    status_counts = {
        "divergent_history_batch_health": 0,
        "duplicate_fingerprint_batch_health": 0,
        "duplicate_generated_at_batch_health": 0,
        "incomplete_history_batch_health": 0,
        "proposal_evidence_comparison_history_batch_health_ready": 2,
        "unstable_history_batch_health": 0,
    }
    duplicate_generated_at_count = 0
    duplicate_fingerprint_count = 0
    if status == "incomplete_batch_health_trend":
        status_counts["incomplete_history_batch_health"] = 1
        status_counts["proposal_evidence_comparison_history_batch_health_ready"] = 1
    elif status == "duplicate_generated_at_batch_health_trend":
        duplicate_generated_at_count = 2
    elif status == "duplicate_fingerprint_batch_health_trend":
        duplicate_fingerprint_count = 2
    elif status != "proposal_evidence_comparison_history_batch_health_trend_ready":
        raise AssertionError(f"unknown fixture status: {status}")

    incomplete_ratio = _ratio(
        trend_count
        - status_counts["proposal_evidence_comparison_history_batch_health_ready"],
        trend_count,
    )
    duplicate_generated_at_ratio = _ratio(duplicate_generated_at_count, trend_count)
    duplicate_fingerprint_ratio = _ratio(duplicate_fingerprint_count, trend_count)
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport(
        generated_at=generated_at,
        config_version="batch-health-trend-v1",
        report_only=True,
        boundary_statement=TREND_BOUNDARY,
        batch_health_report_count=trend_count,
        ready_batch_health_report_count=status_counts[
            "proposal_evidence_comparison_history_batch_health_ready"
        ],
        incomplete_batch_health_report_count=status_counts[
            "incomplete_history_batch_health"
        ],
        duplicate_generated_at_batch_health_report_count=status_counts[
            "duplicate_generated_at_batch_health"
        ],
        duplicate_fingerprint_batch_health_report_count=status_counts[
            "duplicate_fingerprint_batch_health"
        ],
        divergent_batch_health_report_count=status_counts[
            "divergent_history_batch_health"
        ],
        unstable_batch_health_report_count=status_counts[
            "unstable_history_batch_health"
        ],
        duplicate_generated_at_count=duplicate_generated_at_count,
        duplicate_fingerprint_count=duplicate_fingerprint_count,
        incomplete_batch_health_ratio=incomplete_ratio,
        duplicate_generated_at_ratio=duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=duplicate_fingerprint_ratio,
        first_batch_health_generated_at=generated_at,
        last_batch_health_generated_at=generated_at,
        status=status,
        gate_results=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult(
                "batch_health_sample",
                "pass",
                "batch_health_sample checked",
                trend_count,
                1,
            ),
            _trend_rate_gate("incomplete_batch_health_rate", incomplete_ratio),
            _trend_rate_gate(
                "duplicate_generated_at_rate",
                duplicate_generated_at_ratio,
            ),
            _trend_rate_gate(
                "duplicate_fingerprint_rate",
                duplicate_fingerprint_ratio,
            ),
        ),
        status_rows=tuple(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow(
                batch_health_status,
                batch_health_count,
                _ratio(batch_health_count, trend_count),
            )
            for batch_health_status, batch_health_count in status_counts.items()
        ),
        config_version_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary(
                "history-batch-health-v1",
                trend_count,
            ),
        ),
        gate_status_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
                "divergent_history_rate",
                "pass",
                trend_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
                "duplicate_fingerprint_rate",
                "pass" if duplicate_fingerprint_count == 0 else "fail",
                trend_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
                "duplicate_generated_at_rate",
                "pass" if duplicate_generated_at_count == 0 else "fail",
                trend_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
                "history_sample",
                "pass",
                trend_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
                "incomplete_history_rate",
                "pass",
                trend_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
                "unstable_history_rate",
                "pass",
                trend_count,
            ),
        ),
        duplicate_generated_at_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary(
                generated_at,
                duplicate_generated_at_count,
            ),
        )
        if duplicate_generated_at_count
        else (),
        duplicate_fingerprint_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary(
                "fixture-fingerprint",
                duplicate_fingerprint_count,
            ),
        )
        if duplicate_fingerprint_count
        else (),
    )
```

For non-ready fixture statuses, adjust counts, ratios, and gate results so the Node 12 report constructor accepts the value and derives the requested status.

- [ ] **Step 2: Run behavior RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch.py -q
```

Expected: FAIL because `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch` does not exist.

- [ ] **Step 3: Add behavior cases**

Add tests for:

- summarizing one ready, one incomplete, one duplicate-generated-at, and one duplicate-fingerprint trend report
- empty sample yields incomplete status, `None` ratios, and empty time bounds
- status priority for duplicate-generated-at failure, duplicate-fingerprint failure, and incomplete-rate failure
- duplicate generated-at and duplicate fingerprint counts use full collision-group sizes of 2 and 3
- gate-status summaries use existing Node 12 trend gate rows and de-dupe one `(gate_name, gate_status)` pair per report
- ordering normalizes time zones before first/last trend bounds
- rejected input containers: string, bytes, dict, `Path`, serialized JSON string, generator, arbitrary iterable, log-shaped object, and object instance
- subclass rejection and revalidation of mutated nested Node 12 rows
- stale or wrong typed trend-batch gate payloads rejected before append writes
- missing, stale, and compensated stale `gate_status_summaries` rejected before append writes
- frozen dataclasses, duplicate summary validation, canonical boundary validation, and append-only JSONL serialization

## Task 2: Scope And Export Tests

**Files:**

- Create: `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_analytics_scope.py`
- Modify: `tests/test_analytics_history_scope.py`
- Modify: `tests/test_forecast_evidence_scope.py`
- Modify: `tests/test_manual_review_queue_scope.py`
- Modify: `tests/test_proposal_packet_scope.py`
- Modify: `tests/test_proposal_review_scope.py`
- Modify: `tests/test_proposal_review_summary_scope.py`
- Modify: `tests/test_proposal_review_quality_scope.py`
- Modify: `tests/test_proposal_review_diagnostics_scope.py`
- Modify: `tests/test_proposal_review_coverage_scope.py`
- Modify: `tests/test_proposal_review_dossier_scope.py`
- Modify: `tests/test_proposal_review_dossier_batch_scope.py`
- Modify: `tests/test_proposal_evidence_comparison_scope.py`
- Modify: `tests/test_proposal_evidence_comparison_history_scope.py`
- Modify: `tests/test_proposal_evidence_comparison_history_batch_health_scope.py`
- Modify: `tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing scope tests**

Create an AST scope test mirroring `tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py` with:

- module `__all__` equal to the ten public names in this plan
- imports limited to standard library plus `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend`
- first-party imports only from the allowed Node 12 public dataclasses listed in this plan
- no raw upstream modules, loaders, readers, replay/glob/from-file/from-log helpers, fetching, scraping/browser, auth/credential/wallet/broker/execution/order/request/session/websocket, approval, selection, decision-resolution, ranking, recommendation, promotion, outcome, settlement/reconciliation, profitability, compliance/legal/geographic identifiers
- package root exports contain only the Node 13 trend-batch public names for this node
- README Node 13 section states supplied-input, report-only, no-read, no-fetch, no-outcome, no-settlement, no-ranking, no-recommendation, no-approval, and no-execution boundaries

- [ ] **Step 2: Add package-root export tests**

Extend `tests/test_init.py` with `test_level_2_node_13_public_api_exports()` using the existing identity-assertion style for the ten public names. Extend the private-boundary test to verify `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_BOUNDARY_STATEMENT` is present on the module and absent from package-root exports.

Add this exact export set to every sibling scope allowlist file that tracks Level 2 package-root exports:

```python
EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_EXPORTS = {
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report",
}
```

- [ ] **Step 3: Run scope RED**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py \
  tests/test_init.py \
  tests/test_analytics_scope.py \
  tests/test_analytics_history_scope.py \
  tests/test_forecast_evidence_scope.py \
  tests/test_manual_review_queue_scope.py \
  tests/test_proposal_packet_scope.py \
  tests/test_proposal_review_scope.py \
  tests/test_proposal_review_summary_scope.py \
  tests/test_proposal_review_quality_scope.py \
  tests/test_proposal_review_diagnostics_scope.py \
  tests/test_proposal_review_coverage_scope.py \
  tests/test_proposal_review_dossier_scope.py \
  tests/test_proposal_review_dossier_batch_scope.py \
  tests/test_proposal_evidence_comparison_scope.py \
  tests/test_proposal_evidence_comparison_history_scope.py \
  tests/test_proposal_evidence_comparison_history_batch_health_scope.py \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py \
  -q
```

Expected: FAIL because module/root exports do not exist.

## Task 3: Implementation

**Files:**

- Create: `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`

- [ ] **Step 1: Implement production module**

Implement the module using Node 12 as the immediate pattern:

- frozen dataclasses
- exact public input type checks
- exact list/tuple input container check
- clone/revalidate every Node 12 trend report by reconstructing its public dataclasses
- local `_json_ready`, `_as_utc`, `_require_*`, tuple clone, ratio, path normalization, and report-tree validation helpers
- `_require_boundary_statement` must require the normalized supplied boundary statement to exactly match `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_BOUNDARY_STATEMENT`; both config and report construction must reject stale or custom boundary strings before append writes
- duplicate generated-at and duplicate fingerprint summaries by full collision-group size
- gate-status summary validation with both global and per-Node-12-gate totals
- gate-status summary dataclass validation must reject unknown Node 12 gate names and unknown gate statuses before append writes
- gate payload validation before append writes
- append-only JSONL output only
- no file readers, loaders, replay helpers, selectors, ranking, recommendation, approval, outcome, settlement, reconciliation, profitability, compliance/legal/geographic, credential, order, execution, browser, scraping, HTTP, request, session, or WebSocket surfaces

Use these concrete helper shapes for the high-risk paths:

```python
def _normalize_trend_report_inputs(
    trend_reports: (
        list[TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport]
        | tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport, ...]
    ),
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport, ...]:
    if type(trend_reports) not in (list, tuple):
        raise ValueError("trend_reports must be a list or tuple of trend reports")
    cloned = tuple(_clone_trend_report(item) for item in tuple(trend_reports))
    return tuple(
        sorted(
            cloned,
            key=lambda report: (
                report.generated_at,
                report.config_version,
                report.status,
            ),
        )
    )
```

```python
def _clone_trend_report(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport:
    if type(report) is not TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport:
        raise ValueError(
            "trend_reports must contain "
            "TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport values"
        )
    gate_results = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult(
            row.gate_name,
            row.status,
            row.message,
            row.observed_value,
            row.threshold,
        )
        for row in _normalize_typed_tuple(
            "gate_results",
            report.gate_results,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult,
        )
    )
    status_rows = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow(
            row.batch_health_status,
            row.batch_health_count,
            row.batch_health_ratio,
        )
        for row in _normalize_typed_tuple(
            "status_rows",
            report.status_rows,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow,
        )
    )
    config_version_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary(
            row.batch_health_config_version,
            row.batch_health_count,
        )
        for row in _normalize_typed_tuple(
            "config_version_summaries",
            report.config_version_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary,
        )
    )
    gate_status_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
            row.gate_name,
            row.gate_status,
            row.batch_health_count,
        )
        for row in _normalize_typed_tuple(
            "gate_status_summaries",
            report.gate_status_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary,
        )
    )
    duplicate_generated_at_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary(
            row.generated_at,
            row.duplicate_count,
        )
        for row in _normalize_typed_tuple(
            "duplicate_generated_at_summaries",
            report.duplicate_generated_at_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary,
        )
    )
    duplicate_fingerprint_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary(
            row.report_fingerprint,
            row.duplicate_count,
        )
        for row in _normalize_typed_tuple(
            "duplicate_fingerprint_summaries",
            report.duplicate_fingerprint_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary,
        )
    )
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport(
        generated_at=_as_utc(report.generated_at),
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        batch_health_report_count=report.batch_health_report_count,
        ready_batch_health_report_count=report.ready_batch_health_report_count,
        incomplete_batch_health_report_count=report.incomplete_batch_health_report_count,
        duplicate_generated_at_batch_health_report_count=(
            report.duplicate_generated_at_batch_health_report_count
        ),
        duplicate_fingerprint_batch_health_report_count=(
            report.duplicate_fingerprint_batch_health_report_count
        ),
        divergent_batch_health_report_count=report.divergent_batch_health_report_count,
        unstable_batch_health_report_count=report.unstable_batch_health_report_count,
        duplicate_generated_at_count=report.duplicate_generated_at_count,
        duplicate_fingerprint_count=report.duplicate_fingerprint_count,
        incomplete_batch_health_ratio=report.incomplete_batch_health_ratio,
        duplicate_generated_at_ratio=report.duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=report.duplicate_fingerprint_ratio,
        first_batch_health_generated_at=report.first_batch_health_generated_at,
        last_batch_health_generated_at=report.last_batch_health_generated_at,
        status=report.status,
        gate_results=gate_results,
        status_rows=status_rows,
        config_version_summaries=config_version_summaries,
        gate_status_summaries=gate_status_summaries,
        duplicate_generated_at_summaries=duplicate_generated_at_summaries,
        duplicate_fingerprint_summaries=duplicate_fingerprint_summaries,
    )
```

```python
def _trend_report_fingerprint(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
) -> str:
    return json.dumps(_json_ready(asdict(report)), allow_nan=False, sort_keys=True)
```

```python
def _validate_gate_status_summaries(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport,
) -> None:
    keys = tuple((row.gate_name, row.gate_status) for row in report.gate_status_summaries)
    if keys != tuple(sorted(keys)):
        raise ValueError("gate_status_summaries must be sorted")
    if len(set(keys)) != len(keys):
        raise ValueError("gate_status_summaries must not contain duplicates")
    expected_gate_status_count = len(NODE_12_TREND_GATE_NAMES) * report.trend_report_count
    observed_gate_status_count = sum(
        row.trend_count for row in report.gate_status_summaries
    )
    if observed_gate_status_count != expected_gate_status_count:
        raise ValueError("gate_status_summaries must account for all gate rows")
    for gate_name in NODE_12_TREND_GATE_NAMES:
        gate_count = sum(
            row.trend_count
            for row in report.gate_status_summaries
            if row.gate_name == gate_name
        )
        if gate_count != report.trend_report_count:
            raise ValueError("gate_status_summaries must account for every gate")
    for row in report.gate_status_summaries:
        if row.trend_count > report.trend_report_count:
            raise ValueError("gate_status_summaries must not exceed report count")
```

```python
def append(
    self,
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport,
) -> None:
    if type(report) is not TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport:
        raise ValueError(
            "report must be a "
            "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport"
        )
    validated = _validate_trend_batch_report_tree(report)
    line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True)
    line += "\n"
    path = _normalize_log_path(self.path)
    _validate_log_parent(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
```

- [ ] **Step 2: Add root exports**

Add the ten Node 13 trend-batch public names to `src/polymarket_alpha_lab/__init__.py` import blocks and `__all__`. Do not add the boundary constant.

- [ ] **Step 3: Add README sections**

Insert `## Level 2 Node 13 Status` and `## Level 2 Node 13 Python API` before `## Automation Roadmap`. State that Node 13 is report-only over supplied `TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport` values, summarizes trend status and gate status frequencies, duplicate generated-at and fingerprint indicators, and append-only JSONL persistence. Explicitly state it does not fetch data, read logs, scrape, authenticate, handle credentials/private keys, place/cancel orders, open WebSockets, run heartbeat, use trading SDK/broker/execution clients, build request payloads, approve proposals, select latest decisions, resolve conflicts, rank investments, recommend trades, perform outcome/settlement/reconciliation/profitability analysis, import manual executions, or perform compliance/legal/geographic analysis.

Update README repository layout entries for:

- `2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch.md`
- `proposal_evidence_comparison_history_batch_health_trend_batch.py`
- `test_proposal_evidence_comparison_history_batch_health_trend_batch.py`
- `test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py`

- [ ] **Step 4: Run focused GREEN**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_batch.py \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py \
  tests/test_init.py \
  -q
```

Expected: PASS.

## Task 4: Verification, Claude Review, Handoff, Commit, Push

**Files:**

- Modify this plan with handoff evidence

- [ ] **Step 1: Run verification**

Run:

```bash
.venv/bin/python -m pytest -q
git diff --check
codegraph sync
codegraph status .
git status --short --branch --untracked-files=all
```

Expected: all tests pass, diff check exits 0, CodeGraph is up to date, and git status shows only intended Node 13 files.

- [ ] **Step 2: Claude Code implementation review**

Run local Claude Code with model `claude-opus-4-8` and effort `max`:

```bash
claude -p \
  --model claude-opus-4-8 \
  --effort max \
  --permission-mode dontAsk \
  --disallowed-tools "Edit,Write" \
  --append-system-prompt "You are performing a read-only code review. Do not edit files. Do not create files. Report findings only." \
  "Review the Level 2 Node 13 trend-batch implementation. Treat any forbidden raw upstream dependency, data fetch/load/read/scrape/auth/credential/wallet/broker/execution/request/session/websocket/order surface, approval workflow, approved-proposal selection, decision resolution, ranking, recommendation, promotion, outcome loading, realized false-positive analysis, profitability analysis, settlement, reconciliation, manual execution import, or compliance/legal/geographic analysis as Critical. Accepted terminal state is Critical findings: 0, Important findings: 0, and Verdict: Proceed."
```

Accepted terminal state is `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed`. Minor findings may remain only if documented as non-blocking.

- [ ] **Step 3: Append Handoff Summary**

Append actual evidence to this plan with node completed, commit/push status, repo status before commit, verification command results, Claude review counts/verdict, changed files, uncommitted files after push, and next safe step.

## Self-Review

- Spec coverage: The plan creates a supplied-input, report-only trend-batch layer over Node 12 batch-health trend reports and does not add fetching, scraping, JSONL reads, raw upstream ingestion, outcome loading, realized false-positive analysis, profitability analysis, proposal approval, decision resolution, investment ranking, trade recommendations, credential handling, order placement, settlement/reconciliation work, manual execution import, or compliance/legal/geographic analysis.
- Placeholder scan: The plan contains no TBD/TODO placeholders. Public API, statuses, gate rules, counting rules, validation rules, tests, README requirements, verification commands, Claude review policy, and handoff fields are specified.
- Type consistency: The same names are used throughout: `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog`, and `build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report`.

## Pre-Commit Handoff Summary

Node completed: Level 2 Node 13 `proposal_evidence_comparison_history_batch_health_trend_batch`.

Implementation delivered:

- Added `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch.py`.
- Added behavior coverage in `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch.py`.
- Added scope/API boundary coverage in `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py`.
- Added package-root exports in `src/polymarket_alpha_lab/__init__.py` and `tests/test_init.py`.
- Updated sibling scope allowlists for the new Node 13 public API.
- Updated `README.md` with Level 2 Node 13 status/API and repository layout.
- Added the next-node plan `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch-health.md`.

Review-driven fixes applied:

- Added exact root exports for all ten Node 13 public names.
- Added validation that `gate_status_summaries` cannot contain impossible `batch_health_sample/fail` rows.
- Added validation that duplicate generated-at summaries are within `first_trend_generated_at` and `last_trend_generated_at`.
- Strengthened Node 13 scope guardrails for internal `glob`, `replay`, `readlog`, `readlogs`, `logreader`, and `logreaders` names.

Verification evidence before commit:

- Focused Node 13 behavior: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch.py -q` -> `13 passed`.
- Focused Node 13 scope: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py -q` -> `9 passed`.
- Node 13 plus scope/API combo: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch.py tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py tests/test_proposal_review_quality_scope.py tests/test_proposal_review_diagnostics_scope.py tests/test_proposal_review_coverage_scope.py tests/test_proposal_review_dossier_scope.py tests/test_proposal_review_dossier_batch_scope.py tests/test_proposal_evidence_comparison_scope.py tests/test_proposal_evidence_comparison_history_scope.py tests/test_proposal_evidence_comparison_history_batch_health_scope.py tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py -q` -> `170 passed`.
- Full suite: `.venv/bin/python -m pytest -q` -> `725 passed`.
- Whitespace check: `git diff --check` -> clean.
- CodeGraph: `codegraph status .` -> index up to date, `79 files`, `2,983 nodes`, `9,570 edges`.
- Secret scan over `README.md docs src tests` for common token/key patterns -> no matches.

Claude review evidence:

- Node 13 implementation review: `claude -p --model claude-opus-4-8 --effort max ...` -> `Critical findings: 0`, `Important findings: 0`, `Minor findings: 0`, `Verdict: Proceed`.
- Next-node plan review for Node 14 trend-batch-health: after three review/fix rounds, final result -> `Critical findings: 0`, `Important findings: 0`, `Minor findings: 0`, `Verdict: Proceed`.

Pre-commit git status:

- Modified: `README.md`, `src/polymarket_alpha_lab/__init__.py`, `tests/test_init.py`, sibling scope allowlist tests, and this Node 13 plan.
- Added: `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch.py`, `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch.py`, `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py`, and `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch-health.md`.

Commit/push status:

- Pending at the time this handoff summary was written. This summary is intended to be included in the Node 13 commit before push.

Next safe step:

- Commit and push Node 13.
- Begin Level 2 Node 14 from `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch-health.md` using TDD and subagent-driven development, with local Claude Code review fixed to `claude-opus-4-8` and effort `max`.
