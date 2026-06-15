# Level 2 Proposal Evidence Comparison History Batch Health Trend Batch Health Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a report-only health artifact that summarizes caller-supplied proposal evidence comparison history batch-health trend-batch reports for audit-health checks.

**Architecture:** Create a focused `proposal_evidence_comparison_history_batch_health_trend_batch_health.py` module that consumes only in-memory `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport` objects from Level 2 Node 13. It clones and revalidates each supplied trend-batch report, then summarizes trend-batch status frequencies, Node 13 gate-status frequencies, config-version coverage, duplicate generated-at indicators, duplicate fingerprint indicators, and first/last trend-batch report time bounds for audit only, with append-only JSONL persistence for already-built health snapshots.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, UTC `datetime`, JSONL append-only persistence, pytest, CodeGraph, and local Claude Code review with model `claude-opus-4-8` using effort `max`.

---

## Scope Boundaries

This node consumes only caller-supplied, in-memory `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport` objects from `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch`. The final `health` means a supplied-object audit-health layer over Node 13 trend-batch reports, not file discovery, log replay, archive loading, globbing, external history loading, historical data fetching, performance analysis, profitability analysis, outcome analysis, settlement review, reconciliation, compliance review, or trading readiness.

This node must not consume Node 12 trend reports, Node 11 batch-health reports, raw Node 10 history reports, raw Node 9 comparison reports, raw forecast evidence reports, raw dossier batch reports, raw proposal packets, raw proposal-review records, market scores, order books, paper positions, NAV snapshots, API payloads, JSONL files, archived payloads, external history, web pages, account state, credentials, wallets, broker payloads, execution records, outcome data, settlement data, reconciliation data, or compliance/legal/geographic inputs.

This node must not fetch market/order-book/price/outcome/account data, read JSONL logs, replay history, glob files, scrape websites, run browser automation, authenticate, handle credentials or private keys, open user WebSockets, run heartbeat logic, build order requests, place/submit/sign/send/create/cancel orders, select approved proposals, select latest decisions, resolve conflicting reviews, rank investments, recommend trades, promote strategies, review settlement, reconcile positions or exchange accounts, import manual executions, or perform compliance/legal/geographic analysis.

This node must reject convenience inputs that would imply a loader surface: strings, bytes, mappings/dicts, paths, serialized JSON, JSONL lines, generators, arbitrary iterables, log-shaped objects, and subclasses of `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport`.

Allowed first-party imports in the production module are limited to import-from symbols from `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch`:

```python
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport
```

The production module must not import the Node 13 boundary constant, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog`, private helpers, Node 12/11/10/9 modules, raw upstream modules, HTTP/browser/account/order/execution modules, or any first-party module outside the allowlist above. It must implement its own local `_json_ready` helper for `Decimal`, UTC `datetime`, tuple/list, and dict normalization.

## Public API

Create `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health.py` with:

```python
__all__ = (
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report",
)
```

Define a module-internal boundary constant named `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_BOUNDARY_STATEMENT`. It must state that the artifact is report-only over supplied proposal evidence comparison history batch-health trend-batch reports and explicitly exclude approval workflows, proposal approval, approved-proposal selectors, latest-decision selectors, decision-resolution processes, investment ranking, trade recommendations, strategy-promotion signals, trade/order instructions, broker/order requests, account actions, credential workflows, external-history loaders, JSONL readers, scraping workflows, outcome loaders, settlement review, reconciliation, compliance/legal/geographic analysis, realized false-positive analysis, profitability analysis, and automatic order-placement authorization. This constant must not be in module `__all__`, package-root imports, or package-root `__all__`.

Public dataclasses:

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig:
    config_version: str
    min_trend_batch_report_count: int = 1
    max_incomplete_trend_batch_ratio: Decimal = Decimal("0.0000")
    max_duplicate_generated_at_ratio: Decimal = Decimal("0.0000")
    max_duplicate_fingerprint_ratio: Decimal = Decimal("0.0000")
    boundary_statement: str = (
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_BOUNDARY_STATEMENT
    )
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known trend batch health gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known gate status")
        if self.gate_name == "trend_batch_sample" and self.status == "fail":
            raise ValueError("trend_batch_sample cannot fail")
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow:
    trend_batch_status: str
    trend_batch_count: int
    trend_batch_ratio: Decimal | None
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary:
    trend_batch_config_version: str
    trend_batch_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary:
    gate_name: str
    gate_status: str
    trend_batch_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary:
    generated_at: datetime
    duplicate_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary:
    report_fingerprint: str
    duplicate_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    trend_batch_report_count: int
    ready_trend_batch_report_count: int
    incomplete_trend_batch_report_count: int
    duplicate_generated_at_trend_batch_report_count: int
    duplicate_fingerprint_trend_batch_report_count: int
    duplicate_generated_at_count: int
    duplicate_fingerprint_count: int
    incomplete_trend_batch_ratio: Decimal | None
    duplicate_generated_at_ratio: Decimal | None
    duplicate_fingerprint_ratio: Decimal | None
    first_trend_batch_generated_at: datetime | None
    last_trend_batch_generated_at: datetime | None
    status: str
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult, ...]
    status_rows: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow, ...]
    config_version_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary,
        ...,
    ]
    gate_status_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary,
        ...,
    ]
    duplicate_generated_at_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary,
        ...,
    ]
    duplicate_fingerprint_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary,
        ...,
    ]
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(
        self,
        report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
    ) -> None:
        raise NotImplementedError("implemented in Task 3")
```

Builder signature:

```python
def build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
    trend_batch_reports: (
        list[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport]
        | tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport, ...]
    ),
    *,
    config: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig,
    generated_at: datetime,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport:
    raise NotImplementedError("implemented in Task 3")
```

## Status And Gate Rules

Gate names:

```python
GATE_NAMES = (
    "trend_batch_sample",
    "incomplete_trend_batch_rate",
    "duplicate_generated_at_rate",
    "duplicate_fingerprint_rate",
)
```

Gate statuses are `pass`, `fail`, or `incomplete`.

Report statuses:

```python
REPORT_STATUSES = (
    "incomplete_batch_health_trend_batch_health",
    "duplicate_generated_at_batch_health_trend_batch_health",
    "duplicate_fingerprint_batch_health_trend_batch_health",
    "proposal_evidence_comparison_history_batch_health_trend_batch_health_ready",
)
```

Status mapping:

- If `trend_batch_sample` is `incomplete`, report status is `incomplete_batch_health_trend_batch_health`.
- Else if `duplicate_generated_at_rate` is `fail`, report status is `duplicate_generated_at_batch_health_trend_batch_health`.
- Else if `duplicate_fingerprint_rate` is `fail`, report status is `duplicate_fingerprint_batch_health_trend_batch_health`.
- Else if `incomplete_trend_batch_rate` is `fail`, report status is `incomplete_batch_health_trend_batch_health`.
- Else if any gate is `incomplete`, report status is `incomplete_batch_health_trend_batch_health`.
- Else report status is `proposal_evidence_comparison_history_batch_health_trend_batch_health_ready`.

Node 13 trend-batch statuses must be summarized in this exact sorted order:

```python
TREND_BATCH_STATUSES = (
    "duplicate_fingerprint_batch_health_trend_batch",
    "duplicate_generated_at_batch_health_trend_batch",
    "incomplete_batch_health_trend_batch",
    "proposal_evidence_comparison_history_batch_health_trend_batch_ready",
)
```

Node 13 trend-batch gates must be summarized from supplied reports in this exact allowed set:

```python
NODE_13_TREND_BATCH_GATE_NAMES = (
    "trend_sample",
    "incomplete_trend_rate",
    "duplicate_generated_at_rate",
    "duplicate_fingerprint_rate",
)
```

`TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult` and report-tree gate validation must reject `("trend_batch_sample", "fail", ...)` because the Node 14 sample gate cannot fail. `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary` and upstream summary validation must reject impossible Node 13 `("trend_sample", "fail", ...)` rows because those summaries describe Node 13 gate results, not Node 14 gate results.

## Counting And Ordering Rules

- Clone/revalidate every exact `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport` before aggregation.
- Accept only exact `list` or `tuple` containers; reject strings, bytes, mappings, paths, generators, arbitrary iterables, and log-shaped objects before iteration.
- Sort cloned reports with `sorted(cloned_reports, key=lambda report: (report.generated_at, report.config_version, report.status))`.
- `first_trend_batch_generated_at` and `last_trend_batch_generated_at` come from sorted cloned reports' normalized UTC `generated_at` values.
- Duplicate generated-at groups are keyed by cloned report `generated_at`.
- Duplicate fingerprint groups are keyed by canonical JSON fingerprints built from each cloned report's validated JSON-ready tree.
- Duplicate counts use full collision-group sizes, not extras beyond the first item.
- `incomplete_trend_batch_ratio` counts every supplied Node 13 trend-batch report whose status is not `proposal_evidence_comparison_history_batch_health_trend_batch_ready`.
- `duplicate_generated_at_ratio` and `duplicate_fingerprint_ratio` use the duplicate count over total report count.
- Ratios are `None` when `trend_batch_report_count == 0`; otherwise quantized to `Decimal("0.0001")` with `ROUND_HALF_EVEN`.
- `status_rows` contain exactly one row per `TREND_BATCH_STATUSES`, sorted as the tuple above.
- `config_version_summaries` contain one row per distinct `trend_batch_config_version`, sorted by version.
- `gate_status_summaries` group existing Node 13 `gate_results` by `(gate_name, gate_status)` and count how many trend-batch reports contain each pair once.
- `gate_status_summaries` validation must require both the global total `len(NODE_13_TREND_BATCH_GATE_NAMES) * trend_batch_report_count` and each individual Node 13 gate's total to equal `trend_batch_report_count`.
- Builder tests must verify `gate_status_summaries` are derived exactly from supplied Node 13 reports. Append-time validation cannot reconstruct exact source distributions because persisted health reports do not retain source reports; it must validate structural invariants, totals, sorted/unique keys, known upstream gate names, known statuses, and internally impossible upstream sample failures. Do not add source-report loaders, readers, replay APIs, or checksum-fetching surfaces to solve this.
- `duplicate_generated_at_summaries` must be sorted, unique, within `first_trend_batch_generated_at` and `last_trend_batch_generated_at`, and include only groups with `duplicate_count >= 2`.
- `duplicate_fingerprint_summaries` must be sorted, unique, and include only groups with `duplicate_count >= 2`.

## Task 1: Behavior Tests

**Files:**

- Create: `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health.py`

- [ ] **Step 1: Write deterministic Node 13 fixtures and a minimal failing API test**

Construct static `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport` values directly from Node 13 public dataclasses. Do not import Node 12 builders, Node 11 builders, raw forecast/dossier/proposal/review helpers, or Node 13 log classes.

At the top of the test file, import the planned Node 14 module names before the production module exists:

```python
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
    build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report,
)
```

Add this minimal API test before the broader behavior cases:

```python
def test_trend_batch_health_empty_sample_is_incomplete():
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig(
            config_version="batch-health-trend-batch-health-v1",
        ),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    assert isinstance(report, TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport)
    assert report.status == "incomplete_batch_health_trend_batch_health"
    assert report.trend_batch_report_count == 0
    assert report.incomplete_trend_batch_ratio is None
    assert report.first_trend_batch_generated_at is None
    assert report.last_trend_batch_generated_at is None
```

Import Node 13 public dataclasses and use this complete fixture helper:

```python
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow,
)


TREND_BATCH_BOUNDARY = (
    "This is a report-only proposal evidence comparison history batch health trend batch "
    "artifact over supplied proposal evidence comparison history batch health trend "
    "reports, not an approval workflow, proposal approval, approved-proposal "
    "selector, latest-decision selector, decision-resolution process, investment "
    "ranking, trade recommendation, strategy-promotion signal, trade instruction, "
    "order instruction, broker request, order request, account action, account "
    "authentication, private-key handling, wallet signature, live-execution signal, "
    "credential workflow, external-history loader, JSONL reader, scraping workflow, "
    "outcome loader, settlement review, reconciliation process, compliance review, "
    "geographic access analysis, realized false-positive analysis, profitability "
    "analysis, or automatic order-placement authorization."
)


def _ratio(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(count) / Decimal(total)).quantize(Decimal("0.0001"))


def _health_rate_gate(
    gate_name: str,
    observed_value: Decimal | None,
    threshold: Decimal = Decimal("0.0000"),
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult:
    if observed_value is None:
        status = "incomplete"
    elif observed_value <= threshold:
        status = "pass"
    else:
        status = "fail"
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult(
        gate_name,
        status,
        f"{gate_name} checked",
        observed_value,
        threshold,
    )


def trend_batch_report_fixture(
    *,
    status: str = "proposal_evidence_comparison_history_batch_health_trend_batch_ready",
    index: int = 1,
    generated_at: datetime | None = None,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport:
    generated_at = generated_at or datetime(2026, 9, 16, 12, index, tzinfo=UTC)
    trend_batch_count = 2
    status_counts = {
        "duplicate_fingerprint_batch_health_trend": 0,
        "duplicate_generated_at_batch_health_trend": 0,
        "incomplete_batch_health_trend": 0,
        "proposal_evidence_comparison_history_batch_health_trend_ready": 2,
    }
    duplicate_generated_at_count = 0
    duplicate_fingerprint_count = 0
    if status == "incomplete_batch_health_trend_batch":
        status_counts["incomplete_batch_health_trend"] = 1
        status_counts["proposal_evidence_comparison_history_batch_health_trend_ready"] = 1
    elif status == "duplicate_generated_at_batch_health_trend_batch":
        duplicate_generated_at_count = 2
    elif status == "duplicate_fingerprint_batch_health_trend_batch":
        duplicate_fingerprint_count = 2
    elif status != "proposal_evidence_comparison_history_batch_health_trend_batch_ready":
        raise AssertionError(f"unknown fixture status: {status}")

    incomplete_ratio = _ratio(
        trend_batch_count
        - status_counts["proposal_evidence_comparison_history_batch_health_trend_ready"],
        trend_batch_count,
    )
    duplicate_generated_at_ratio = _ratio(duplicate_generated_at_count, trend_batch_count)
    duplicate_fingerprint_ratio = _ratio(duplicate_fingerprint_count, trend_batch_count)
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport(
        generated_at=generated_at,
        config_version="batch-health-trend-batch-v1",
        report_only=True,
        boundary_statement=TREND_BATCH_BOUNDARY,
        trend_report_count=trend_batch_count,
        ready_trend_report_count=status_counts[
            "proposal_evidence_comparison_history_batch_health_trend_ready"
        ],
        incomplete_trend_report_count=status_counts["incomplete_batch_health_trend"],
        duplicate_generated_at_trend_report_count=status_counts[
            "duplicate_generated_at_batch_health_trend"
        ],
        duplicate_fingerprint_trend_report_count=status_counts[
            "duplicate_fingerprint_batch_health_trend"
        ],
        duplicate_generated_at_count=duplicate_generated_at_count,
        duplicate_fingerprint_count=duplicate_fingerprint_count,
        incomplete_trend_ratio=incomplete_ratio,
        duplicate_generated_at_ratio=duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=duplicate_fingerprint_ratio,
        first_trend_generated_at=generated_at,
        last_trend_generated_at=generated_at,
        status=status,
        gate_results=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult(
                "trend_sample",
                "pass",
                "trend_sample checked",
                trend_batch_count,
                1,
            ),
            _health_rate_gate("incomplete_trend_rate", incomplete_ratio),
            _health_rate_gate("duplicate_generated_at_rate", duplicate_generated_at_ratio),
            _health_rate_gate("duplicate_fingerprint_rate", duplicate_fingerprint_ratio),
        ),
        status_rows=tuple(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow(
                trend_status,
                trend_count,
                _ratio(trend_count, trend_batch_count),
            )
            for trend_status, trend_count in status_counts.items()
        ),
        config_version_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary(
                "batch-health-trend-v1",
                trend_batch_count,
            ),
        ),
        gate_status_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary(
                "batch_health_sample",
                "pass",
                trend_batch_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary(
                "duplicate_fingerprint_rate",
                "pass" if duplicate_fingerprint_count == 0 else "fail",
                trend_batch_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary(
                "duplicate_generated_at_rate",
                "pass" if duplicate_generated_at_count == 0 else "fail",
                trend_batch_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary(
                "incomplete_batch_health_rate",
                "pass" if status != "incomplete_batch_health_trend_batch" else "fail",
                trend_batch_count,
            ),
        ),
        duplicate_generated_at_summaries=(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary(
                    generated_at,
                    duplicate_generated_at_count,
                ),
            )
            if duplicate_generated_at_count
            else ()
        ),
        duplicate_fingerprint_summaries=(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary(
                    "fixture-trend-batch-fingerprint",
                    duplicate_fingerprint_count,
                ),
            )
            if duplicate_fingerprint_count
            else ()
        ),
    )


def trend_batch_health_config(**overrides):
    values = {
        "config_version": "batch-health-trend-batch-health-v1",
        "max_incomplete_trend_batch_ratio": Decimal("1.0000"),
        "max_duplicate_generated_at_ratio": Decimal("1.0000"),
        "max_duplicate_fingerprint_ratio": Decimal("1.0000"),
    }
    values.update(overrides)
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig(
        **values,
    )


def unsafe_trend_batch_health_report(report, **changes):
    clone = object.__new__(type(report))
    for field_name in report.__dataclass_fields__:
        object.__setattr__(clone, field_name, getattr(report, field_name))
    for field_name, value in changes.items():
        object.__setattr__(clone, field_name, value)
    return clone
```

- [ ] **Step 2: Run behavior RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health.py -q
```

Expected: FAIL because `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health` does not exist.

- [ ] **Step 3: Add behavior cases**

Add tests for:

- summarizing one ready, one incomplete, one duplicate-generated-at, and one duplicate-fingerprint trend-batch report
- empty sample yields incomplete status, `None` ratios, and empty time bounds
- status priority for duplicate-generated-at failure, duplicate-fingerprint failure, and incomplete-rate failure
- duplicate generated-at and duplicate fingerprint counts use full collision-group sizes of 2 and 3
- gate-status summaries use existing Node 13 trend-batch gate rows and de-dupe one `(gate_name, gate_status)` pair per report
- ordering normalizes time zones before first/last trend-batch bounds
- rejected input containers: string, bytes, dict, `Path`, serialized JSON string, generator, arbitrary iterable, log-shaped object, and object instance
- subclass rejection and revalidation of mutated nested Node 13 rows
- stale or wrong typed health gate payloads rejected before append writes
- missing, stale, impossible sample status, and compensated stale `gate_status_summaries` rejected before append writes
- duplicate-generated-at summary outside first/last trend-batch time bounds rejected before append writes
- frozen dataclasses, duplicate summary validation, raw boundary equality validation, same-alphanumeric-but-mutated boundary rejection, and append-only JSONL serialization

Use these concrete safety tests for the highest-risk cases:

```python
def test_trend_batch_health_rejects_bad_inputs_before_iteration():
    class ExplodingIterable:
        def __iter__(self):
            raise AssertionError("loader-shaped iterable was consumed")

    class LogShapedInput:
        path = Path("trend-batch-health.jsonl")

        def append(self, report):
            raise AssertionError("append-only log was consumed")

    for bad_input in (
        "[]",
        b"[]",
        {"report": trend_batch_report_fixture()},
        Path("trend-batch-health.jsonl"),
        '{"serialized": true}',
        (item for item in (trend_batch_report_fixture(),)),
        ExplodingIterable(),
        LogShapedInput(),
        object(),
    ):
        with pytest.raises(ValueError, match="trend_batch_reports"):
            build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
                bad_input,
                config=trend_batch_health_config(),
                generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
            )


def test_trend_batch_health_rejects_subclasses_and_mutated_nested_rows(tmp_path):
    source = trend_batch_report_fixture(index=1)

    class TrendBatchSubclass(TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport):
        pass

    subclass_value = TrendBatchSubclass(
        **{
            field_name: getattr(source, field_name)
            for field_name in source.__dataclass_fields__
        },
    )
    with pytest.raises(
        ValueError,
        match="TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport",
    ):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
            [subclass_value],
            config=trend_batch_health_config(),
            generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
        )

    drift = trend_batch_report_fixture(index=2)
    object.__setattr__(drift.gate_results[0], "status", "unknown")
    with pytest.raises(ValueError, match="status"):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
            [drift],
            config=trend_batch_health_config(),
            generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
        )


def test_trend_batch_health_rejects_stale_summaries_before_append_writes(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [trend_batch_report_fixture(index=1), trend_batch_report_fixture(index=2)],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    missing_summaries = unsafe_trend_batch_health_report(report, gate_status_summaries=())
    missing_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "missing-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        missing_log.append(missing_summaries)
    assert not missing_log.path.exists()

    impossible_rows = tuple(
        sorted(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
                    "trend_sample",
                    "fail",
                    report.trend_batch_report_count,
                )
                if row.gate_name == "trend_sample"
                else row
                for row in report.gate_status_summaries
            ),
            key=lambda row: (row.gate_name, row.gate_status),
        ),
    )
    impossible_report = unsafe_trend_batch_health_report(
        report,
        gate_status_summaries=impossible_rows,
    )
    impossible_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "impossible-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        impossible_log.append(impossible_report)
    assert not impossible_log.path.exists()


def test_trend_batch_health_rejects_boundary_mutation_before_append_writes(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [trend_batch_report_fixture(index=1)],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )
    same_alphanumeric_boundary = report.boundary_statement.replace("report-only", "report only")
    mutated_report = unsafe_trend_batch_health_report(
        report,
        boundary_statement=same_alphanumeric_boundary,
    )

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "mutated-boundary.jsonl",
    )
    with pytest.raises(ValueError, match="boundary_statement"):
        log.append(mutated_report)
    assert not log.path.exists()


def test_trend_batch_health_rejects_duplicate_generated_at_summary_outside_bounds(tmp_path):
    shared_time = datetime(2026, 9, 17, 1, tzinfo=UTC)
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [
            replace(trend_batch_report_fixture(index=1), generated_at=shared_time),
            replace(trend_batch_report_fixture(index=2), generated_at=shared_time),
        ],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )
    out_of_bounds_report = unsafe_trend_batch_health_report(
        report,
        duplicate_generated_at_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary(
                shared_time + timedelta(days=1),
                report.duplicate_generated_at_count,
            ),
        ),
    )

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "out-of-bounds-duplicate-generated-at.jsonl",
    )
    with pytest.raises(ValueError, match="duplicate_generated_at_summaries"):
        log.append(out_of_bounds_report)
    assert not log.path.exists()
```

- [ ] **Step 4: Run full behavior RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health.py -q
```

Expected: FAIL because the production module still does not exist. This second RED run happens after the full behavior test file is in place, so every planned behavior case is committed before implementation starts.

## Task 2: Scope And Export Tests

**Files:**

- Create: `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_scope.py`
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
- Modify: `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing scope tests**

Create an AST scope test mirroring `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py` with:

- module `__all__` equal to the ten public names in this plan
- imports limited to standard library plus `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch`
- first-party imports only from the allowed Node 13 public dataclasses listed in this plan
- no raw upstream modules, loaders, readers, replay/glob/from-file/from-log helpers, fetching, scraping/browser, auth/credential/wallet/broker/execution/order/request/session/websocket, approval, selection, decision-resolution, ranking, recommendation, promotion, outcome, settlement/reconciliation, profitability, compliance/legal/geographic identifiers
- package root exports contain only the Node 14 public names for this node
- README Node 14 section states supplied-input, report-only, no-read, no-fetch, no-outcome, no-settlement, no-ranking, no-recommendation, no-approval, and no-execution boundaries

- [ ] **Step 2: Add package-root export tests**

Extend `tests/test_init.py` with `test_level_2_node_14_public_api_exports()` using the existing identity-assertion style for the ten public names. Extend the private-boundary test to verify `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_BOUNDARY_STATEMENT` is present on the module and absent from package-root exports.

Add this exact export set to every sibling scope allowlist file that tracks Level 2 package-root exports:

```python
EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_EXPORTS = {
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report",
}
```

- [ ] **Step 3: Run scope RED**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_scope.py \
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
  tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py \
  -q
```

Expected: FAIL because module/root exports do not exist.

## Task 3: Implementation

**Files:**

- Create: `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `README.md`

- [ ] **Step 1: Create an importable skeleton only**

Create `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health.py` with the planned `__all__`, public dataclass names, and builder/log signatures, but leave `build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report()` and `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog.append()` raising `NotImplementedError`. Do not add aggregation or validation logic in this step.

- [ ] **Step 2: Run behavior RED against the skeleton**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health.py -q
```

Expected: FAIL with `NotImplementedError` or behavior assertion failures from the planned builder/log surfaces. This proves the full behavior tests execute beyond import collection before the full implementation is written.

- [ ] **Step 3: Implement production module**

Implement the module using Node 13 as the immediate pattern:

- frozen dataclasses
- exact public input type checks
- exact list/tuple input container check
- clone/revalidate every Node 13 trend-batch report by reconstructing its public dataclasses
- local `_json_ready`, `_as_utc`, `_require_*`, tuple clone, ratio, path normalization, and report-tree validation helpers
- `_require_boundary_statement` must first validate the value as a canonical string, then require raw `value == DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_BOUNDARY_STATEMENT`; both config and report construction must reject stale, custom, or same-alphanumeric-but-mutated boundary strings before append writes
- duplicate generated-at and duplicate fingerprint summaries by full collision-group size
- duplicate generated-at summary validation must reject summaries outside first/last trend-batch generated-at bounds
- gate-status summary validation with both global and per-Node-13-gate totals
- gate-status summary validation must reject impossible upstream sample gate failures
- gate payload validation before append writes
- append-only JSONL output only
- no file readers, loaders, replay helpers, selectors, ranking, recommendation, approval, outcome, settlement, reconciliation, profitability, compliance/legal/geographic, credential, order, execution, browser, scraping, HTTP, request, session, or WebSocket surfaces

- [ ] **Step 4: Add root exports**

Add the ten Node 14 public names to `src/polymarket_alpha_lab/__init__.py` import blocks and `__all__`. Do not add the boundary constant.

- [ ] **Step 5: Add README sections**

Insert `## Level 2 Node 14 Status` and `## Level 2 Node 14 Python API` before `## Automation Roadmap`. State that Node 14 is report-only over supplied `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport` values, summarizes trend-batch status and Node 13 gate-status frequencies, duplicate generated-at and fingerprint indicators, and append-only JSONL persistence. Explicitly state it does not fetch data, read logs, scrape, authenticate, handle credentials/private keys, place/cancel orders, open WebSockets, run heartbeat, use trading SDK/broker/execution clients, build request payloads, approve proposals, select latest decisions, resolve conflicts, rank investments, recommend trades, perform outcome/settlement/reconciliation/profitability analysis, import manual executions, or perform compliance/legal/geographic analysis.

Update README repository layout entries for:

- `2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch-health.md`
- `proposal_evidence_comparison_history_batch_health_trend_batch_health.py`
- `test_proposal_evidence_comparison_history_batch_health_trend_batch_health.py`
- `test_proposal_evidence_comparison_history_batch_health_trend_batch_health_scope.py`

- [ ] **Step 6: Run focused GREEN**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health.py \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_scope.py \
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
rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----" README.md docs src tests
git status --short --branch --untracked-files=all
```

Expected: all tests pass, diff check exits 0, CodeGraph is up to date, secret scan has no matches, and git status shows only intended Node 14 files.

- [ ] **Step 2: Claude Code implementation review**

Run local Claude Code with model `claude-opus-4-8` and effort `max`. This alias is already verified on this machine by the Node 13 implementation and Node 14 plan reviews.

```bash
claude -p \
  --model claude-opus-4-8 \
  --effort max \
  --permission-mode dontAsk \
  --disallowed-tools "Edit,Write" \
  --append-system-prompt "You are performing a read-only code review. Do not edit files. Do not create files. Report findings only." \
  "Review the Level 2 Node 14 trend-batch-health implementation. Treat any forbidden raw upstream dependency, data fetch/load/read/scrape/auth/credential/wallet/broker/execution/request/session/websocket/order surface, approval workflow, approved-proposal selection, decision resolution, ranking, recommendation, promotion, outcome loading, realized false-positive analysis, profitability analysis, settlement, reconciliation, manual execution import, or compliance/legal/geographic analysis as Critical. Accepted terminal state is Critical findings: 0, Important findings: 0, and Verdict: Proceed."
```

Accepted terminal state is `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed`. Minor findings may remain only if documented as non-blocking.

- [ ] **Step 3: Append Handoff Summary**

Append actual evidence to this plan with node completed, commit/push status, repo status before commit, verification command results, Claude review counts/verdict, changed files, uncommitted files after push, and next safe step.

## Acceptance Criteria

- Public API exports exactly the ten Node 14 names from the module and package root; the default boundary constant exists only inside the module and is not exported.
- The production module imports only Python standard library modules plus the allowed Node 13 public dataclasses.
- The builder accepts only exact `list` or `tuple` containers of exact `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport` values, rejects loader-shaped and iterable-shaped inputs before iteration, and rejects subclasses.
- The report deterministically summarizes supplied Node 13 reports: counts, ratios, status rows, config-version summaries, Node 13 gate-status summaries, first/last UTC `generated_at` bounds, duplicate generated-at summaries, and duplicate fingerprint summaries.
- Gate results and report status are derived only from sample size, incomplete trend-batch ratio, duplicate generated-at ratio, and duplicate fingerprint ratio, using the status priority in this plan.
- `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog.append(report)` validates the full report tree before opening/writing, writes append-only JSONL, and never exposes a JSONL reader, loader, replay, glob, from-file, or from-log API.
- README and scope tests explicitly preserve report-only/no-loader/no-reader/no-execution/no-recommendation/no-compliance boundaries.

## Self-Review

- Spec coverage: The plan creates a supplied-input, report-only health layer over Node 13 trend-batch reports and does not add fetching, scraping, JSONL reads, raw upstream ingestion, outcome loading, realized false-positive analysis, profitability analysis, proposal approval, decision resolution, investment ranking, trade recommendations, credential handling, order placement, settlement/reconciliation work, manual execution import, or compliance/legal/geographic analysis.
- Placeholder scan: The plan contains no TBD/TODO placeholders. Public API, statuses, gate rules, counting rules, validation rules, tests, README requirements, verification commands, Claude review policy, and handoff fields are specified.
- Type consistency: The same names are used throughout: `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog`, and `build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report`.

## Final Handoff Summary (Node 14 Completed)

- Node completed: Level 2 Node 14 proposal evidence comparison history batch-health trend-batch health.
- Base commit before Node 14 work: `fc50067b09c0337313abdcce57591deadd1c77f7` (`feat: add proposal evidence comparison history batch health trend batch`).
- Main production artifact: `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health.py`.
- Main behavior tests: `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health.py`.
- Main scope tests: `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_scope.py`.
- Public API integration: `src/polymarket_alpha_lab/__init__.py` and `tests/test_init.py`.
- Documentation integration: `README.md`.
- Sibling scope allowlists updated for the new Node 14 public root exports.
- Next implementation plan created: `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch-health-trend.md`.

Verification evidence before commit:

- RED behavior test was observed before production module existed: `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health.py` failed with `ModuleNotFoundError`.
- RED scope/export/docs tests were observed before root exports existed: focused scope/API command failed with missing Node 14 exports.
- Review-driven regression RED was observed for non-quantized append-time ratio validation: `test_trend_batch_health_rejects_nonquantized_ratio_values_before_append_writes` failed before the production fix because no `ValueError` was raised.
- Review-driven regression GREEN: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health.py::test_trend_batch_health_rejects_nonquantized_ratio_values_before_append_writes -q` passed with `1 passed`.
- Node 14 behavior suite: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health.py -q` passed with `22 passed`.
- Scope/API combination: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py tests/test_proposal_review_quality_scope.py tests/test_proposal_review_diagnostics_scope.py tests/test_proposal_review_coverage_scope.py tests/test_proposal_review_dossier_scope.py tests/test_proposal_review_dossier_batch_scope.py tests/test_proposal_evidence_comparison_scope.py tests/test_proposal_evidence_comparison_history_scope.py tests/test_proposal_evidence_comparison_history_batch_health_scope.py tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py -q` passed with `168 passed`.
- Full suite after ratio fix: `.venv/bin/python -m pytest -q` passed with `758 passed`.
- `git diff --check` exited 0.
- `codegraph sync && codegraph status .` reported the index up to date.
- Secret scan over `README.md docs src tests` had no matches.

Review evidence:

- Claude Code implementation review (`claude-opus-4-8`, effort `max`, read-only) initially reported `Critical findings: 0`, `Important findings: 1`, `Verdict: Needs fixes` for append-time non-quantized Decimal ratio validation.
- The important finding was fixed by adding `_ratio_value_matches()` and a regression test that rejects non-quantized top-level ratios, status-row ratios, and rate-gate observed values before append writes.
- Claude Code implementation re-review (`claude-opus-4-8`, effort `max`, read-only) reported `Critical findings: 0`, `Important findings: 0`, `Minor findings: 1`, `Verdict: Proceed`.
- Claude Code Node 15 plan review (`claude-opus-4-8`, effort `max`, read-only) initially reported `Critical findings: 0`, `Important findings: 0`, `Minor findings: 2`, `Verdict: Proceed`; those two minor clarity notes were addressed.
- Claude Code Node 15 plan re-review after self-containedness fixes and minor clarity fixes reported `Critical findings: 0`, `Important findings: 0`, `Minor findings: 1`, `Verdict: Proceed`.

Commit and push status:

- Intended commit message: `feat: add proposal evidence comparison history batch health trend batch health`.
- Intended push target: `origin/main`.
- No GitHub token or other secret is stored in the repository.
- After this summary is appended, run the final verification commands again, commit all intended Node 14 and Node 15 plan files, push to `origin/main`, then start Node 15 implementation from the reviewed plan.
