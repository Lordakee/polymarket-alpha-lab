# Level 2 Proposal Evidence Comparison History Batch Health Trend Batch Health Trend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a report-only trend artifact over caller-supplied, in-memory Level 2 Node 14 `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport` values.

**Architecture:** Create a focused `proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py` module that consumes only exact Node 14 trend-batch-health report objects supplied by the caller. It clones and revalidates every supplied report, sorts by normalized `generated_at`, `config_version`, and `status`, then summarizes Node 14 status frequencies, Node 14 gate-status frequencies, config-version coverage, duplicate generated-at collisions, duplicate fingerprint collisions, and first/last Node 14 report time bounds. Persistence is append-only JSONL for already-built reports only, with validation before opening or writing and no reader, loader, replay, glob, API-client, scraping, account, execution, trading, or financial-advice surfaces.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, UTC `datetime`, JSONL append-only persistence, pytest, CodeGraph, Codex subagents using `gpt-5.5` with reasoning `xhigh`, and local Claude Code review with model `claude-opus-4-8` using effort `max`.

---

## Project Rules To Preserve

- Codex implementation subagents must be launched with model `gpt-5.5` and reasoning effort `xhigh`.
- Implementation review and audit must be local Claude Code with model `claude-opus-4-8` and effort `max`; Claude review is read-only and must not edit or create files.
- Do not run multiple agents that edit the same files at the same time. Assign file ownership per task, finish and review each task before another agent touches the same file.
- Use CodeGraph before grep, find, or manual file reads when locating or understanding code because this repository has `.codegraph/`.
- This node must not add web scraping, browser automation, account automation, live execution, trading, order placement, order cancellation, API clients, HTTP clients, request/session/WebSocket clients, credential workflows, wallet/private-key handling, approval workflows, recommendation/ranking logic, or financial advice.
- The artifact is report-only and supplied-input only. It must not fetch, discover, load, replay, glob, or read upstream reports from disk or external systems.

## Scope Boundaries

This node consumes only caller-supplied, in-memory `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport` objects from `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health`. The final `trend` means a supplied-object audit trend over Node 14 trend-batch-health reports, not file discovery, JSONL reading, log replay, archive loading, globbing, external history loading, live execution, market monitoring, portfolio analytics, profitability analysis, outcome analysis, settlement review, reconciliation, compliance review, legal/geographic analysis, trading readiness, or financial advice.

This node must not consume Node 13 trend-batch reports, Node 12 trend reports, Node 11 batch-health reports, raw Node 10 history reports, raw Node 9 comparison reports, raw forecast evidence reports, raw dossier batch reports, raw proposal packets, raw proposal-review records, market scores, order books, paper positions, NAV snapshots, API payloads, JSONL files, archived payloads, external history, web pages, account state, credentials, wallets, broker payloads, execution records, outcome data, settlement data, reconciliation data, compliance/legal/geographic inputs, or financial-advice inputs.

This node must not fetch market/order-book/price/outcome/account data, read JSONL logs, replay history, glob files, scrape websites, run browser automation, automate accounts, authenticate, handle credentials or private keys, open user WebSockets, run heartbeat logic, instantiate API clients, build order requests, place/submit/sign/send/create/cancel orders, select approved proposals, select latest decisions, resolve conflicting reviews, rank investments, recommend trades, promote strategies, review settlement, reconcile positions or exchange accounts, import manual executions, provide financial advice, or perform compliance/legal/geographic analysis.

This node must reject convenience inputs that would imply a loader or automation surface: strings, bytes, mappings/dicts, paths, serialized JSON, JSONL lines, generators, arbitrary iterables, log-shaped objects, and subclasses of `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport`.

Allowed first-party imports in the production module are limited to import-from symbols from `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health`:

```python
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary
TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport
```

The production module must not import the Node 14 boundary constant, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog`, private helpers, Node 13/12/11/10/9 modules, raw upstream modules, HTTP/browser/account/order/execution/client/request/session/WebSocket modules, or any first-party module outside the allowlist above. It must implement its own local `_json_ready` helper for `Decimal`, UTC `datetime`, tuple/list, and dict normalization.

## Public API

Create `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py` with:

```python
__all__ = (
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report",
)
```

Define a module-internal boundary constant named `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT`. It must state that the artifact is report-only over supplied proposal evidence comparison history batch-health trend-batch-health reports and explicitly exclude approval workflows, proposal approval, approved-proposal selectors, latest-decision selectors, decision-resolution processes, investment ranking, trade recommendations, financial advice, strategy-promotion signals, trade/order instructions, broker/order requests, API clients, account actions, account automation, credential workflows, private-key handling, external-history loaders, JSONL readers, scraping workflows, browser automation, outcome loaders, settlement review, reconciliation, compliance/legal/geographic analysis, realized false-positive analysis, profitability analysis, live execution, and automatic order-placement authorization. This constant must not be in module `__all__`, package-root imports, or package-root `__all__`.

Public dataclasses:

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig:
    config_version: str
    min_trend_batch_health_report_count: int = 1
    max_incomplete_trend_batch_health_ratio: Decimal = Decimal("0.0000")
    max_duplicate_generated_at_ratio: Decimal = Decimal("0.0000")
    max_duplicate_fingerprint_ratio: Decimal = Decimal("0.0000")
    boundary_statement: str = (
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT
    )
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known trend batch health trend gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known trend batch health trend gate status")
        if self.gate_name == "trend_batch_health_sample" and self.status == "fail":
            raise ValueError("trend_batch_health_sample cannot fail")
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow:
    trend_batch_health_status: str
    trend_batch_health_count: int
    trend_batch_health_ratio: Decimal | None
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary:
    trend_batch_health_config_version: str
    trend_batch_health_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary:
    gate_name: str
    gate_status: str
    trend_batch_health_count: int

    def __post_init__(self) -> None:
        if self.gate_name not in NODE_14_TREND_BATCH_HEALTH_GATE_NAMES:
            raise ValueError("gate_name must be a known trend batch health gate")
        if self.gate_status not in GATE_STATUSES:
            raise ValueError("gate_status must be a known gate status")
        if self.gate_name == "trend_batch_sample" and self.gate_status == "fail":
            raise ValueError("trend_batch_sample cannot fail")
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary:
    generated_at: datetime
    duplicate_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary:
    report_fingerprint: str
    duplicate_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    trend_batch_health_report_count: int
    ready_trend_batch_health_report_count: int
    incomplete_trend_batch_health_report_count: int
    duplicate_generated_at_trend_batch_health_report_count: int
    duplicate_fingerprint_trend_batch_health_report_count: int
    duplicate_generated_at_count: int
    duplicate_fingerprint_count: int
    incomplete_trend_batch_health_ratio: Decimal | None
    duplicate_generated_at_ratio: Decimal | None
    duplicate_fingerprint_ratio: Decimal | None
    first_trend_batch_health_generated_at: datetime | None
    last_trend_batch_health_generated_at: datetime | None
    status: str
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult, ...]
    status_rows: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow, ...]
    config_version_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary,
        ...,
    ]
    gate_status_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary,
        ...,
    ]
    duplicate_generated_at_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary,
        ...,
    ]
    duplicate_fingerprint_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary,
        ...,
    ]
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(
        self,
        report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport,
    ) -> None:
        raise NotImplementedError("implemented in Task 3")
```

Builder signature:

```python
def build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
    trend_batch_health_reports: (
        list[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport]
        | tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport, ...]
    ),
    *,
    config: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig,
    generated_at: datetime,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport:
    raise NotImplementedError("implemented in Task 3")
```

## Status And Gate Rules

Own Node 15 gate names:

```python
GATE_NAMES = (
    "trend_batch_health_sample",
    "incomplete_trend_batch_health_rate",
    "duplicate_generated_at_rate",
    "duplicate_fingerprint_rate",
)
```

Gate statuses are `pass`, `fail`, or `incomplete`. `trend_batch_health_sample` cannot fail; it is `pass` when the supplied Node 14 report count meets `min_trend_batch_health_report_count` and `incomplete` otherwise.

Own Node 15 report statuses:

```python
REPORT_STATUSES = (
    "incomplete_batch_health_trend_batch_health_trend",
    "duplicate_generated_at_batch_health_trend_batch_health_trend",
    "duplicate_fingerprint_batch_health_trend_batch_health_trend",
    "proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_ready",
)
```

Status priority:

- If `trend_batch_health_sample` is `incomplete`, report status is `incomplete_batch_health_trend_batch_health_trend`.
- Else if `duplicate_generated_at_rate` is `fail`, report status is `duplicate_generated_at_batch_health_trend_batch_health_trend`.
- Else if `duplicate_fingerprint_rate` is `fail`, report status is `duplicate_fingerprint_batch_health_trend_batch_health_trend`.
- Else if `incomplete_trend_batch_health_rate` is `fail`, report status is `incomplete_batch_health_trend_batch_health_trend`.
- Else if any gate is `incomplete`, report status is `incomplete_batch_health_trend_batch_health_trend`.
- Else report status is `proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_ready`.

Node 14 trend-batch-health statuses must be summarized in this exact sorted order:

```python
TREND_BATCH_HEALTH_STATUSES = (
    "duplicate_fingerprint_batch_health_trend_batch_health",
    "duplicate_generated_at_batch_health_trend_batch_health",
    "incomplete_batch_health_trend_batch_health",
    "proposal_evidence_comparison_history_batch_health_trend_batch_health_ready",
)
```

Node 14 gates must be summarized from supplied reports in this exact allowed set:

```python
NODE_14_TREND_BATCH_HEALTH_GATE_NAMES = (
    "trend_batch_sample",
    "incomplete_trend_batch_rate",
    "duplicate_generated_at_rate",
    "duplicate_fingerprint_rate",
)
```

`TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult` and report-tree gate validation must reject `("trend_batch_health_sample", "fail", ...)` because the Node 15 sample gate cannot fail. `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary` and upstream summary validation must reject impossible Node 14 `("trend_batch_sample", "fail", ...)` rows because those summaries describe Node 14 gate results, not Node 15 gate results.

Node 14 `trend_batch_sample` failure summaries are impossible because the Node 14 sample gate cannot fail. Node 15 tests must explicitly assert this impossible upstream summary is rejected before append writes.

## Counting And Ordering Rules

- Clone/revalidate every exact `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport` before aggregation.
- Accept only exact `list` or `tuple` containers; reject strings, bytes, mappings, paths, serialized JSON strings, generators, arbitrary iterables, log-shaped objects, object instances, and subclasses before iteration.
- Sort cloned reports with `sorted(cloned_reports, key=lambda report: (report.generated_at, report.config_version, report.status))`.
- `first_trend_batch_health_generated_at` and `last_trend_batch_health_generated_at` come from sorted cloned reports' normalized UTC `generated_at` values.
- Duplicate generated-at groups are keyed by cloned Node 14 report `generated_at`.
- Duplicate fingerprint groups are keyed by canonical JSON fingerprints built from each cloned Node 14 report's validated JSON-ready tree.
- Duplicate counts use full collision-group sizes, not extras beyond the first item. A collision group of 2 contributes 2; a collision group of 3 contributes 3.
- `incomplete_trend_batch_health_ratio` counts every supplied Node 14 trend-batch-health report whose status is not `proposal_evidence_comparison_history_batch_health_trend_batch_health_ready`.
- `duplicate_generated_at_ratio` and `duplicate_fingerprint_ratio` use the duplicate count over total Node 14 report count.
- Ratios are `None` when `trend_batch_health_report_count == 0`; otherwise quantized to `Decimal("0.0001")` with `ROUND_HALF_EVEN`.
- `status_rows` contain exactly one row per `TREND_BATCH_HEALTH_STATUSES`, sorted as the tuple above.
- `config_version_summaries` contain one row per distinct `trend_batch_health_config_version`, sorted by version.
- `gate_status_summaries` group existing Node 14 `gate_results` by `(gate_name, gate_status)` and count how many trend-batch-health reports contain each pair once.
- `gate_status_summaries` validation must require both the global total `len(NODE_14_TREND_BATCH_HEALTH_GATE_NAMES) * trend_batch_health_report_count` and each individual Node 14 gate's total to equal `trend_batch_health_report_count`.
- Builder tests must verify `gate_status_summaries` are derived exactly from supplied Node 14 reports. Append-time validation cannot reconstruct exact source distributions because persisted Node 15 trend reports do not retain source reports; it must validate structural invariants, totals, sorted/unique keys, known upstream gate names, known statuses, and impossible upstream sample failures. Do not add source-report loaders, readers, replay APIs, or checksum-fetching surfaces to solve this.
- `duplicate_generated_at_summaries` must be sorted, unique, within `first_trend_batch_health_generated_at` and `last_trend_batch_health_generated_at`, and include only groups with `duplicate_count >= 2`.
- `duplicate_fingerprint_summaries` must be sorted, unique, and include only groups with `duplicate_count >= 2`.

## Task 1: Behavior Tests RED

**Files:**

- Create: `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py`

- [ ] **Step 1: Write deterministic Node 14 fixtures and a minimal failing API test**

Construct static `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport` values directly from Node 14 public dataclasses. Do not import Node 13 builders, Node 12 builders, Node 11 builders, raw forecast/dossier/proposal/review helpers, Node 14 log classes, API clients, HTTP clients, browser tools, account tools, or order/execution helpers.

At the top of the behavior test file, import the planned Node 15 module names before the production module exists:

```python
from datetime import UTC, datetime, timedelta
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

import pytest

from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health_trend import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport,
    build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report,
)
```

Add this minimal API test before the broader behavior cases:

```python
def test_trend_batch_health_trend_empty_sample_is_incomplete():
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig(
            config_version="batch-health-trend-batch-health-trend-v1",
        ),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    assert isinstance(
        report,
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport,
    )
    assert report.status == "incomplete_batch_health_trend_batch_health_trend"
    assert report.trend_batch_health_report_count == 0
    assert report.incomplete_trend_batch_health_ratio is None
    assert report.first_trend_batch_health_generated_at is None
    assert report.last_trend_batch_health_generated_at is None
```

Import Node 14 public dataclasses and use this complete fixture helper:

```python
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow,
)


TREND_BATCH_HEALTH_BOUNDARY = (
    "This is a report-only proposal evidence comparison history batch health trend batch health "
    "artifact over supplied proposal evidence comparison history batch health trend batch "
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
    return (Decimal(count) / Decimal(total)).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_EVEN,
    )


def _node14_rate_gate(
    gate_name: str,
    observed_value: Decimal | None,
    threshold: Decimal = Decimal("0.0000"),
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult:
    if observed_value is None:
        status = "incomplete"
    elif observed_value <= threshold:
        status = "pass"
    else:
        status = "fail"
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult(
        gate_name,
        status,
        f"{gate_name} checked",
        observed_value,
        threshold,
    )


def trend_batch_health_report_fixture(
    *,
    status: str = "proposal_evidence_comparison_history_batch_health_trend_batch_health_ready",
    index: int = 1,
    generated_at: datetime | None = None,
    config_version: str = "batch-health-trend-batch-health-v1",
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport:
    generated_at = generated_at or datetime(2026, 9, 17, 12, index, tzinfo=UTC)
    trend_batch_report_count = 2
    status_counts = {
        "duplicate_fingerprint_batch_health_trend_batch": 0,
        "duplicate_generated_at_batch_health_trend_batch": 0,
        "incomplete_batch_health_trend_batch": 0,
        "proposal_evidence_comparison_history_batch_health_trend_batch_ready": 2,
    }
    duplicate_generated_at_count = 0
    duplicate_fingerprint_count = 0
    if status == "incomplete_batch_health_trend_batch_health":
        status_counts["incomplete_batch_health_trend_batch"] = 1
        status_counts["proposal_evidence_comparison_history_batch_health_trend_batch_ready"] = 1
    elif status == "duplicate_generated_at_batch_health_trend_batch_health":
        duplicate_generated_at_count = 2
    elif status == "duplicate_fingerprint_batch_health_trend_batch_health":
        duplicate_fingerprint_count = 2
    elif status != "proposal_evidence_comparison_history_batch_health_trend_batch_health_ready":
        raise AssertionError(f"unknown fixture status: {status}")

    incomplete_ratio = _ratio(
        trend_batch_report_count
        - status_counts["proposal_evidence_comparison_history_batch_health_trend_batch_ready"],
        trend_batch_report_count,
    )
    duplicate_generated_at_ratio = _ratio(
        duplicate_generated_at_count,
        trend_batch_report_count,
    )
    duplicate_fingerprint_ratio = _ratio(
        duplicate_fingerprint_count,
        trend_batch_report_count,
    )
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport(
        generated_at=generated_at,
        config_version=config_version,
        report_only=True,
        boundary_statement=TREND_BATCH_HEALTH_BOUNDARY,
        trend_batch_report_count=trend_batch_report_count,
        ready_trend_batch_report_count=status_counts[
            "proposal_evidence_comparison_history_batch_health_trend_batch_ready"
        ],
        incomplete_trend_batch_report_count=status_counts[
            "incomplete_batch_health_trend_batch"
        ],
        duplicate_generated_at_trend_batch_report_count=status_counts[
            "duplicate_generated_at_batch_health_trend_batch"
        ],
        duplicate_fingerprint_trend_batch_report_count=status_counts[
            "duplicate_fingerprint_batch_health_trend_batch"
        ],
        duplicate_generated_at_count=duplicate_generated_at_count,
        duplicate_fingerprint_count=duplicate_fingerprint_count,
        incomplete_trend_batch_ratio=incomplete_ratio,
        duplicate_generated_at_ratio=duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=duplicate_fingerprint_ratio,
        first_trend_batch_generated_at=generated_at,
        last_trend_batch_generated_at=generated_at,
        status=status,
        gate_results=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult(
                "trend_batch_sample",
                "pass",
                "trend_batch_sample checked",
                trend_batch_report_count,
                1,
            ),
            _node14_rate_gate("incomplete_trend_batch_rate", incomplete_ratio),
            _node14_rate_gate("duplicate_generated_at_rate", duplicate_generated_at_ratio),
            _node14_rate_gate("duplicate_fingerprint_rate", duplicate_fingerprint_ratio),
        ),
        status_rows=tuple(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow(
                trend_batch_status,
                trend_batch_count,
                _ratio(trend_batch_count, trend_batch_report_count),
            )
            for trend_batch_status, trend_batch_count in status_counts.items()
        ),
        config_version_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary(
                "batch-health-trend-batch-v1",
                trend_batch_report_count,
            ),
        ),
        gate_status_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
                "trend_sample",
                "pass",
                trend_batch_report_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
                "duplicate_fingerprint_rate",
                "pass",
                trend_batch_report_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
                "duplicate_generated_at_rate",
                "pass",
                trend_batch_report_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
                "incomplete_trend_rate",
                "pass",
                trend_batch_report_count,
            ),
        ),
        duplicate_generated_at_summaries=(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary(
                    generated_at,
                    duplicate_generated_at_count,
                ),
            )
            if duplicate_generated_at_count
            else ()
        ),
        duplicate_fingerprint_summaries=(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary(
                    "fixture-trend-batch-health-fingerprint",
                    duplicate_fingerprint_count,
                ),
            )
            if duplicate_fingerprint_count
            else ()
        ),
    )


def trend_batch_health_trend_config(**overrides):
    values = {
        "config_version": "batch-health-trend-batch-health-trend-v1",
        "max_incomplete_trend_batch_health_ratio": Decimal("1.0000"),
        "max_duplicate_generated_at_ratio": Decimal("1.0000"),
        "max_duplicate_fingerprint_ratio": Decimal("1.0000"),
    }
    values.update(overrides)
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig(
        **values,
    )


def unsafe_trend_batch_health_trend_report(report, **changes):
    clone = object.__new__(type(report))
    for field_name in report.__dataclass_fields__:
        object.__setattr__(clone, field_name, getattr(report, field_name))
    for field_name, value in changes.items():
        object.__setattr__(clone, field_name, value)
    return clone
```

- [ ] **Step 2: Run behavior RED for missing module**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py -q
```

Expected: FAIL during collection because `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health_trend` does not exist.

- [ ] **Step 3: Add full behavior cases**

Implement the complete Node 15 behavior test file by copying the structure of `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health.py` and applying this exact semantic map:

| Node 14 test/helper term | Node 15 test/helper term |
| --- | --- |
| `trend_batch_health` | `trend_batch_health_trend` for Node 15 artifact names |
| `trend_batch_report_fixture` | `trend_batch_health_report_fixture` for supplied Node 14 reports |
| `trend_batch_health_config` | `trend_batch_health_trend_config` |
| `unsafe_trend_batch_health_report` | `unsafe_trend_batch_health_trend_report` |
| `trend_batch_report_count` | `trend_batch_health_report_count` |
| `ready_trend_batch_report_count` | `ready_trend_batch_health_report_count` |
| `incomplete_trend_batch_report_count` | `incomplete_trend_batch_health_report_count` |
| `incomplete_trend_batch_ratio` | `incomplete_trend_batch_health_ratio` |
| `first_trend_batch_generated_at` | `first_trend_batch_health_generated_at` |
| `last_trend_batch_generated_at` | `last_trend_batch_health_generated_at` |
| `trend_batch_sample` | `trend_batch_health_sample` for Node 15 own gates |
| `incomplete_trend_batch_rate` | `incomplete_trend_batch_health_rate` for Node 15 own gates |
| `trend_sample` | `trend_batch_sample` for upstream Node 14 gate summaries |
| `incomplete_trend_rate` | `incomplete_trend_batch_rate` for upstream Node 14 gate summaries |

The test file must contain these exact test functions, renamed to the Node 15 `test_trend_batch_health_trend_*` prefix and with the mapped fields/statuses above: `test_trend_batch_health_trend_empty_sample_is_incomplete`, `test_trend_batch_health_trend_nonempty_sample_below_configured_min_is_incomplete`, `test_trend_batch_health_trend_summarizes_supplied_node14_reports`, `test_trend_batch_health_trend_status_priority_for_rate_failures`, `test_trend_batch_health_trend_sample_incomplete_prioritizes_duplicate_rate_failures`, `test_trend_batch_health_trend_duplicate_counts_use_full_collision_groups`, `test_trend_batch_health_trend_duplicate_fingerprint_detection_is_structural`, `test_trend_batch_health_trend_gate_status_summaries_use_existing_node14_gate_rows`, `test_trend_batch_health_trend_gate_status_summaries_count_each_upstream_gate_result`, `test_trend_batch_health_trend_ordering_uses_normalized_generated_at`, `test_trend_batch_health_trend_rejects_upstream_trend_batch_sample_fail_payload`, `test_trend_batch_health_trend_rejects_bad_inputs_before_iteration`, `test_trend_batch_health_trend_rejects_subclasses_and_mutated_nested_rows`, `test_trend_batch_health_trend_rejects_stale_or_wrong_typed_gate_payloads`, `test_trend_batch_health_trend_rejects_stale_summaries_before_append_writes`, `test_trend_batch_health_trend_boundary_statement_is_exact_and_config_rejects_mutation`, `test_trend_batch_health_trend_rejects_boundary_mutation_before_append_writes`, `test_trend_batch_health_trend_invalid_append_preserves_existing_log_bytes`, `test_trend_batch_health_trend_rejects_nonquantized_ratio_values_before_append_writes`, `test_trend_batch_health_trend_rejects_duplicate_generated_at_summary_outside_bounds`, `test_trend_batch_health_trend_gate_thresholds_preserve_caller_config_values`, and `test_trend_batch_health_trend_config_dataclasses_and_log_validate_invariants`.

Each listed function must assert the same contract as its Node 14 counterpart, with these Node 15-specific expected values:

- ready status: `proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_ready`
- incomplete status: `incomplete_batch_health_trend_batch_health_trend`
- duplicate generated-at status: `duplicate_generated_at_batch_health_trend_batch_health_trend`
- duplicate fingerprint status: `duplicate_fingerprint_batch_health_trend_batch_health_trend`
- supplied upstream ready status: `proposal_evidence_comparison_history_batch_health_trend_batch_health_ready`
- supplied upstream incomplete status: `incomplete_batch_health_trend_batch_health`
- supplied upstream duplicate generated-at status: `duplicate_generated_at_batch_health_trend_batch_health`
- supplied upstream duplicate fingerprint status: `duplicate_fingerprint_batch_health_trend_batch_health`
- own gate order: `("trend_batch_health_sample", "incomplete_trend_batch_health_rate", "duplicate_generated_at_rate", "duplicate_fingerprint_rate")`
- upstream gate summary names: `("duplicate_fingerprint_rate", "duplicate_generated_at_rate", "incomplete_trend_batch_rate", "trend_batch_sample")`
- non-quantized append validation rejects `Decimal("0.5")` when the canonical value is `Decimal("0.5000")` for top-level ratio fields, status-row ratios, and rate-gate observed values

Use these concrete safety tests for the highest-risk cases:

```python
def test_trend_batch_health_trend_summarizes_supplied_node14_reports():
    reports = [
        trend_batch_health_report_fixture(index=1),
        trend_batch_health_report_fixture(
            status="incomplete_batch_health_trend_batch_health",
            index=2,
        ),
        trend_batch_health_report_fixture(
            status="duplicate_generated_at_batch_health_trend_batch_health",
            index=3,
        ),
        trend_batch_health_report_fixture(
            status="duplicate_fingerprint_batch_health_trend_batch_health",
            index=4,
        ),
    ]

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        reports,
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    assert report.report_only is True
    assert report.trend_batch_health_report_count == 4
    assert report.ready_trend_batch_health_report_count == 1
    assert report.incomplete_trend_batch_health_report_count == 1
    assert report.duplicate_generated_at_trend_batch_health_report_count == 1
    assert report.duplicate_fingerprint_trend_batch_health_report_count == 1
    assert report.incomplete_trend_batch_health_ratio == Decimal("0.7500")
    assert tuple(row.trend_batch_health_status for row in report.status_rows) == (
        "duplicate_fingerprint_batch_health_trend_batch_health",
        "duplicate_generated_at_batch_health_trend_batch_health",
        "incomplete_batch_health_trend_batch_health",
        "proposal_evidence_comparison_history_batch_health_trend_batch_health_ready",
    )
    assert tuple(row.trend_batch_health_count for row in report.status_rows) == (1, 1, 1, 1)
```

```python
def test_trend_batch_health_trend_status_priority_for_rate_failures():
    shared_time = datetime(2026, 9, 17, 1, tzinfo=UTC)

    sample_report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [],
        config=trend_batch_health_trend_config(min_trend_batch_health_report_count=1),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    assert sample_report.status == "incomplete_batch_health_trend_batch_health_trend"

    generated_at_report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [
            replace(trend_batch_health_report_fixture(index=1), generated_at=shared_time),
            replace(trend_batch_health_report_fixture(index=2), generated_at=shared_time),
        ],
        config=trend_batch_health_trend_config(max_duplicate_generated_at_ratio=Decimal("0.0000")),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    assert generated_at_report.status == "duplicate_generated_at_batch_health_trend_batch_health_trend"

    duplicate_fingerprint_report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [
            trend_batch_health_report_fixture(index=1),
            trend_batch_health_report_fixture(index=1),
        ],
        config=trend_batch_health_trend_config(
            max_duplicate_generated_at_ratio=Decimal("1.0000"),
            max_duplicate_fingerprint_ratio=Decimal("0.0000"),
        ),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    assert duplicate_fingerprint_report.status == "duplicate_fingerprint_batch_health_trend_batch_health_trend"

    incomplete_rate_report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [
            trend_batch_health_report_fixture(index=1),
            trend_batch_health_report_fixture(
                status="incomplete_batch_health_trend_batch_health",
                index=2,
            ),
        ],
        config=trend_batch_health_trend_config(max_incomplete_trend_batch_health_ratio=Decimal("0.0000")),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    assert incomplete_rate_report.status == "incomplete_batch_health_trend_batch_health_trend"
```

```python
def test_trend_batch_health_trend_rejects_bad_inputs_before_iteration():
    class ExplodingIterable:
        def __iter__(self):
            raise AssertionError("loader-shaped iterable was consumed")

    class LogShapedInput:
        path = Path("trend-batch-health-trend.jsonl")

        def append(self, report):
            raise AssertionError("append-only log was consumed")

    for bad_input in (
        "[]",
        b"[]",
        {"report": trend_batch_health_report_fixture()},
        Path("trend-batch-health-trend.jsonl"),
        '{"serialized": true}',
        (item for item in (trend_batch_health_report_fixture(),)),
        ExplodingIterable(),
        LogShapedInput(),
        object(),
    ):
        with pytest.raises(ValueError, match="trend_batch_health_reports"):
            build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
                bad_input,
                config=trend_batch_health_trend_config(),
                generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
            )
```

```python
def test_trend_batch_health_trend_rejects_subclasses_and_mutated_nested_rows():
    source = trend_batch_health_report_fixture(index=1)

    class TrendBatchHealthSubclass(TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport):
        pass

    subclass_value = TrendBatchHealthSubclass(
        **{
            field_name: getattr(source, field_name)
            for field_name in source.__dataclass_fields__
        },
    )
    with pytest.raises(
        ValueError,
        match="TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
    ):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
            [subclass_value],
            config=trend_batch_health_trend_config(),
            generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
        )

    drift = trend_batch_health_report_fixture(index=2)
    object.__setattr__(drift.gate_results[0], "status", "unknown")
    with pytest.raises(ValueError, match="status"):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
            [drift],
            config=trend_batch_health_trend_config(),
            generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
        )
```

```python
def test_trend_batch_health_trend_rejects_stale_summaries_before_append_writes(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [trend_batch_health_report_fixture(index=1), trend_batch_health_report_fixture(index=2)],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    missing_summaries = unsafe_trend_batch_health_trend_report(report, gate_status_summaries=())
    missing_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "missing-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        missing_log.append(missing_summaries)
    assert not missing_log.path.exists()

    impossible_rows = tuple(
        sorted(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary(
                    "trend_batch_sample",
                    "fail",
                    report.trend_batch_health_report_count,
                )
                if row.gate_name == "trend_batch_sample"
                else row
                for row in report.gate_status_summaries
            ),
            key=lambda row: (row.gate_name, row.gate_status),
        ),
    )
    impossible_report = unsafe_trend_batch_health_trend_report(
        report,
        gate_status_summaries=impossible_rows,
    )
    impossible_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "impossible-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        impossible_log.append(impossible_report)
    assert not impossible_log.path.exists()
```

```python
def test_trend_batch_health_trend_rejects_boundary_mutation_before_append_writes(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [trend_batch_health_report_fixture(index=1)],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    same_alphanumeric_boundary = report.boundary_statement.replace("report-only", "report only")
    mutated_report = unsafe_trend_batch_health_trend_report(
        report,
        boundary_statement=same_alphanumeric_boundary,
    )

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "mutated-boundary.jsonl",
    )
    with pytest.raises(ValueError, match="boundary_statement"):
        log.append(mutated_report)
    assert not log.path.exists()
```

```python
def test_trend_batch_health_trend_rejects_duplicate_generated_at_summary_outside_bounds(tmp_path):
    shared_time = datetime(2026, 9, 17, 1, tzinfo=UTC)
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [
            replace(trend_batch_health_report_fixture(index=1), generated_at=shared_time),
            replace(trend_batch_health_report_fixture(index=2), generated_at=shared_time),
        ],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    out_of_bounds_report = unsafe_trend_batch_health_trend_report(
        report,
        duplicate_generated_at_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary(
                shared_time + timedelta(days=1),
                report.duplicate_generated_at_count,
            ),
        ),
    )

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "out-of-bounds-duplicate-generated-at.jsonl",
    )
    with pytest.raises(ValueError, match="duplicate_generated_at_summaries"):
        log.append(out_of_bounds_report)
    assert not log.path.exists()
```

- [ ] **Step 4: Run full behavior RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py -q
```

Expected: FAIL because the production module still does not exist. This second RED run happens after the full behavior test file is in place, so every planned behavior case is committed before implementation starts.

## Task 2: Scope, Export, And Docs Tests RED

**Files:**

- Create: `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_scope.py`
- Modify: `tests/test_init.py`
- Modify these exact sibling scope allowlist tests that track Level 2 package-root exports:
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
  - `tests/test_proposal_evidence_comparison_history_scope.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_scope.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_scope.py`

- [ ] **Step 1: Write failing scope tests**

Create an AST scope test mirroring `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_scope.py` with Node 15 names and boundaries:

- module `__all__` equals the ten public names in this plan
- imports are limited to Python standard library modules plus `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health`
- first-party imports only from the allowed Node 14 public dataclasses listed in this plan
- no raw upstream modules, loaders, readers, replay/glob/from-file/from-log helpers, fetching, scraping/browser, auth/credential/wallet/broker/execution/order/request/session/websocket/client identifiers, account automation, approval, selection, decision-resolution, ranking, recommendation, financial-advice, promotion, outcome, settlement/reconciliation, profitability, compliance/legal/geographic identifiers
- package root exports include the ten Node 15 public names for this node, do not export the Node 15 boundary constant, and continue allowing unrelated public exports from earlier nodes
- README Node 15 section states supplied-input, report-only, no-read, no-fetch, no-scrape, no-browser-automation, no-account-automation, no-API-client, no-outcome, no-settlement, no-ranking, no-recommendation, no-financial-advice, no-approval, and no-execution boundaries

The new scope test file must define these exact Node 15 test functions: `test_trend_batch_health_trend_module_imports_only_allowed_dependencies`, `test_trend_batch_health_trend_module_does_not_import_forbidden_surfaces`, `test_trend_batch_health_trend_uses_only_allowed_first_party_symbols`, `test_trend_batch_health_trend_does_not_import_first_party_modules_wholesale`, `test_trend_batch_health_trend_does_not_define_forbidden_names`, `test_trend_batch_health_trend_public_exports_are_report_only`, `test_package_root_exports_batch_health_trend_batch_health_trend_names_only_for_node_15`, `test_readme_level_2_node_15_section_keeps_report_only_boundaries`, and `test_readme_repository_layout_lists_level_2_node_15_artifacts`.

Use the helper functions from the Node 14 scope file with only the Node 15 path/name substitutions in this plan; do not add new fixture discovery, filesystem globbing, browser checks, network checks, or runtime imports beyond AST parsing and package-root export inspection.

The scope test should include allowlists like:

```python
EXPECTED_PUBLIC_NAMES = {
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report",
}

ALLOWED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health": {
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary",
        "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
    },
}
```

- [ ] **Step 2: Add package-root export tests**

Extend `tests/test_init.py` with `test_level_2_node_15_public_api_exports()` using the existing identity-assertion style for the ten public names. Extend the private-boundary test to verify `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT` is present on the module and absent from package-root exports.

Add this exact export set to each sibling scope allowlist file listed above. In files that already special-case longer prefixes before shorter ones, place the Node 15 check before the Node 14, Node 13, and shorter prefix checks so the `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrend...` names are not matched by a shorter Node prefix:

```python
EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_EXPORTS = {
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report",
}
```

- [ ] **Step 3: Add README assertion expectations**

The new scope/docs test must require README coverage for:

- `## Level 2 Node 15 Status`
- `## Level 2 Node 15 Python API`
- `2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch-health-trend.md`
- `proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py`
- `test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py`
- `test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_scope.py`
- report-only supplied `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport` values
- no JSONL readers, no external loaders, no scraping, no browser automation, no account automation, no API clients, no live execution, no order placement, no ranking/recommendations, no financial advice, no settlement/reconciliation, and no compliance/legal/geographic analysis

- [ ] **Step 4: Run scope/export/docs RED**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_scope.py \
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
  tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_scope.py \
  -q
```

Expected: FAIL because the Node 15 production module, package-root exports, sibling allowlists, and README sections do not exist yet.

## Task 3: Production Implementation GREEN

**Files:**

- Create: `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py`

- [ ] **Step 1: Create an importable skeleton only**

Create `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py` with the planned `__all__`, boundary constant, constants, public dataclass names, builder signature, and log signature, but leave `build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report()` and `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog.append()` raising `NotImplementedError`. Do not add aggregation or validation logic in this step.

The skeleton must already use the allowed imports only:

```python
"""Report-only proposal evidence comparison history batch health trend batch health trend artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow,
)
```

- [ ] **Step 2: Run behavior RED against the skeleton**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py -q
```

Expected: FAIL with `NotImplementedError` or behavior assertion failures from the planned builder/log surfaces. This proves the behavior tests execute beyond import collection before the full implementation is written.

- [ ] **Step 3: Implement production module**

Implement the module by using `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health.py` as the immediate template and applying this exact production mapping. This is a mechanical successor node, not a redesign:

| Node 14 production name | Node 15 production name |
| --- | --- |
| `proposal_evidence_comparison_history_batch_health_trend_batch_health.py` | `proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py` |
| `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealth` | `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrend` |
| `build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report` | `build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report` |
| `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_BOUNDARY_STATEMENT` | `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT` |
| `trend_batch_reports` | `trend_batch_health_reports` |
| `_normalize_trend_batch_report_inputs` | `_normalize_trend_batch_health_report_inputs` |
| `_clone_trend_batch_report` | `_clone_trend_batch_health_report` |
| `_clone_trend_batch_gate_results` | `_clone_trend_batch_health_gate_results` |
| `_trend_batch_report_fingerprint` | `_trend_batch_health_report_fingerprint` |
| `_trend_batch_status` | `_trend_batch_health_trend_status` |
| `_validate_trend_batch_report_tree` | `_validate_trend_batch_health_trend_report_tree` |
| `_validate_trend_batch_report_rows` | `_validate_trend_batch_health_trend_report_rows` |
| `trend_batch_report_count` | `trend_batch_health_report_count` |
| `ready_trend_batch_report_count` | `ready_trend_batch_health_report_count` |
| `incomplete_trend_batch_report_count` | `incomplete_trend_batch_health_report_count` |
| `duplicate_generated_at_trend_batch_report_count` | `duplicate_generated_at_trend_batch_health_report_count` |
| `duplicate_fingerprint_trend_batch_report_count` | `duplicate_fingerprint_trend_batch_health_report_count` |
| `incomplete_trend_batch_ratio` | `incomplete_trend_batch_health_ratio` |
| `first_trend_batch_generated_at` | `first_trend_batch_health_generated_at` |
| `last_trend_batch_generated_at` | `last_trend_batch_health_generated_at` |
| `trend_batch_status` | `trend_batch_health_status` |
| `trend_batch_count` | `trend_batch_health_count` |
| `trend_batch_ratio` | `trend_batch_health_ratio` |
| `trend_batch_config_version` | `trend_batch_health_config_version` |
| `GATE_NAMES = ("trend_batch_sample", "incomplete_trend_batch_rate", "duplicate_generated_at_rate", "duplicate_fingerprint_rate")` | `GATE_NAMES = ("trend_batch_health_sample", "incomplete_trend_batch_health_rate", "duplicate_generated_at_rate", "duplicate_fingerprint_rate")` |
| `TREND_BATCH_STATUSES` | `TREND_BATCH_HEALTH_STATUSES` |
| `NODE_13_TREND_BATCH_GATE_NAMES` | `NODE_14_TREND_BATCH_HEALTH_GATE_NAMES` |

The Node 15 production module must define the same ordered class/function set as Node 14 after applying the mapping table: the nine public dataclasses, the public builder, input normalization, source-report clone, status counts, gate result construction, rate gate construction, status rows, config-version summaries, gate-status summaries, duplicate generated-at summaries, duplicate fingerprint summaries, canonical source-report fingerprinting, deterministic report-status mapping, ratio calculation, full report-tree validation, row validation, derived-ratio validation, `_ratio_value_matches`, time-bound validation, duplicate-summary validation, config-version-summary validation, gate-status-summary validation, gate-payload validation, rate-gate-payload validation, typed tuple clone helpers, UTC datetime helpers, boundary-statement validation, canonical string validation, integer and Decimal validators, gate-value validation, JSON-ready serialization, log-path normalization, and log-parent validation. Do not add extra public functions.

Use the Node 14 helper bodies with the mapped field names above. Keep these exact Node 15-specific logic changes:

- frozen dataclasses
- exact public input type checks
- exact `list`/`tuple` input container check
- clone/revalidate every Node 14 trend-batch-health report by reconstructing its public dataclasses
- local `_json_ready`, `_as_utc`, `_as_optional_utc`, `_require_*`, tuple clone, ratio, path normalization, and report-tree validation helpers
- `_require_boundary_statement` first validates the value as a canonical string, then requires raw equality to `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT`; config and report construction must reject stale, custom, or same-alphanumeric-but-mutated boundary strings before append writes
- `_normalize_trend_batch_health_report_inputs()` rejects non-list/tuple inputs before iteration, clones exact Node 14 report values, and sorts by `(generated_at, config_version, status)`
- `_clone_trend_batch_health_report()` rejects subclasses, clones every nested Node 14 public row, and reconstructs the Node 14 report to force Node 14 validation
- `_build_status_counts()` counts Node 14 report statuses from `TREND_BATCH_HEALTH_STATUSES`
- `_build_gate_results()` creates Node 15 gates in `GATE_NAMES` order; sample gate is only `pass` or `incomplete`
- `_trend_batch_health_trend_status()` implements the status priority exactly as listed in this plan
- `_gate_status_summaries()` derives summaries from Node 14 report `gate_results`, counting each unique `(gate_name, status)` pair once per report
- duplicate generated-at and duplicate fingerprint summaries count full collision-group sizes
- duplicate generated-at summary validation rejects summaries outside first/last trend-batch-health generated-at bounds
- gate-status summary validation requires sorted unique keys, known Node 14 gate names, known statuses, no impossible upstream `trend_batch_sample` failure, global total equality, and per-gate total equality
- gate payload validation rejects missing gates, extra gates, wrong order, stale sample status, stale rate gate status, stale observed values, and stale thresholds before append writes
- append-only JSONL output only; append validates the full report tree before `_validate_log_parent()`, parent creation, file open, or write
- no file readers, loaders, replay helpers, selectors, ranking, recommendation, financial-advice, approval, outcome, settlement, reconciliation, profitability, compliance/legal/geographic, credential, order, execution, API-client, browser, scraping, HTTP, request, session, or WebSocket surfaces

- [ ] **Step 4: Run behavior GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py -q
```

Expected: PASS.

## Task 4: Exports And Docs Integration GREEN

**Files:**

- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Modify: sibling scope allowlist tests that track Level 2 package-root exports
- Modify: `README.md`

- [ ] **Step 1: Add root exports**

Add the ten Node 15 public names to `src/polymarket_alpha_lab/__init__.py` import blocks and `__all__`. Do not add `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT`.

The root import block must expose:

```python
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health_trend import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow,
    build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report,
)
```

- [ ] **Step 2: Update tests and sibling allowlists**

Make `tests/test_init.py` and sibling scope allowlist tests match the exact ten public exports from Task 2. Keep the boundary constant private: module attribute present, package-root attribute absent, package-root `__all__` absent.

- [ ] **Step 3: Update README**

Insert `## Level 2 Node 15 Status` and `## Level 2 Node 15 Python API` before `## Automation Roadmap`. State that Node 15 is report-only over supplied `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport` values, summarizes Node 14 status and gate-status frequencies, duplicate generated-at and fingerprint indicators, config-version coverage, first/last generated-at bounds, and append-only JSONL persistence.

Explicitly state Node 15 does not fetch data, read logs, load files, replay history, glob paths, scrape, run browser automation, automate accounts, authenticate, handle credentials/private keys, place/cancel orders, open WebSockets, run heartbeat, use trading SDK/broker/execution/API clients, build request payloads, approve proposals, select latest decisions, resolve conflicts, rank investments, recommend trades, provide financial advice, perform outcome/settlement/reconciliation/profitability analysis, import manual executions, or perform compliance/legal/geographic analysis.

Update README repository layout entries for:

- `2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch-health-trend.md`
- `proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py`
- `test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py`
- `test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_scope.py`

- [ ] **Step 4: Run focused integration GREEN**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_scope.py \
  tests/test_init.py \
  -q
```

Expected: PASS.

## Task 5: Verification, Reviews, Handoff, Commit, Push

**Files:**

- Modify this plan with final handoff evidence after implementation.
- Commit and push only after verification and reviews pass.

- [ ] **Step 1: Run full verification**

Run:

```bash
.venv/bin/python -m pytest -q
git diff --check
codegraph sync
codegraph status .
rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----" README.md docs src tests
git status --short --branch --untracked-files=all
```

Expected: all tests pass, `git diff --check` exits 0, CodeGraph is up to date, secret scan has no matches, and git status shows only intended Node 15 files plus any explicitly known pre-existing work from other agents. If other agents' unrelated files remain dirty, record them in the handoff and do not revert them.

- [ ] **Step 2: Claude Code implementation review**

Run local Claude Code with model `claude-opus-4-8` and effort `max` in read-only mode:

```bash
claude -p \
  --model claude-opus-4-8 \
  --effort max \
  --permission-mode dontAsk \
  --disallowed-tools "Edit,Write" \
  --append-system-prompt "You are performing a read-only code review. Do not edit files. Do not create files. Report findings only." \
  "Review the Level 2 Node 15 trend-batch-health-trend implementation. Treat any forbidden raw upstream dependency, data fetch/load/read/scrape/browser/account-automation/auth/credential/wallet/broker/execution/API-client/request/session/websocket/order surface, live execution, approval workflow, approved-proposal selection, decision resolution, ranking, recommendation, financial advice, promotion, outcome loading, realized false-positive analysis, profitability analysis, settlement, reconciliation, manual execution import, or compliance/legal/geographic analysis as Critical. Accepted terminal state is Critical findings: 0, Important findings: 0, and Verdict: Proceed."
```

Accepted terminal state is `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed`. Minor findings may remain only if documented as non-blocking and not related to safety scope, correctness, tests, or public API.

- [ ] **Step 3: Claude Code plan-review evidence**

Before committing Node 15 implementation work, ensure the next implementation plan to execute has a read-only Claude Code plan review with `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed`. If this Node 15 plan already has a pre-implementation review recorded with that accepted terminal state, record that evidence in the Node 15 handoff. If a successor Node 16 plan has been created during Node 15 work, review that successor plan instead.

```bash
claude -p \
  --model claude-opus-4-8 \
  --effort max \
  --permission-mode dontAsk \
  --disallowed-tools "Edit,Write" \
  --append-system-prompt "You are performing a read-only implementation-plan review. Do not edit files. Do not create files. Report findings only." \
  "Review docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch-health-trend.md as the next Level 2 implementation plan. Verify it is self-contained, TDD-oriented, uses Codex subagents with model gpt-5.5 and reasoning xhigh, uses local Claude Code claude-opus-4-8 effort max for implementation audit, avoids multiple agents editing the same files, and preserves the supplied-input/report-only boundary with no web scraping, browser automation, account automation, live execution, trading/order placement, API clients, or financial advice. Accepted terminal state is Critical findings: 0, Important findings: 0, and Verdict: Proceed."
```

Use the command above only to produce or re-check pre-implementation review evidence for this Node 15 plan. If a successor Node 16 plan exists by the time Node 15 is complete, run the same review command against that exact successor plan path instead and record that exact reviewed path plus accepted terminal state in the handoff. The accepted terminal state remains `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed`.

- [ ] **Step 4: Append handoff evidence**

Append actual implementation evidence under `## Final Handoff Summary (Node 15 Worker Completes)` at the end of this plan. Include the node completed, exact changed files, verification command results, Claude implementation-review counts/verdict, Claude next-plan-review counts/verdict, git status before commit, commit hash, push target, uncommitted files after push, known unrelated dirty files, and next safe step.

- [ ] **Step 5: Commit**

Run:

```bash
git status --short --branch --untracked-files=all
git add \
  README.md \
  src/polymarket_alpha_lab/__init__.py \
  src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py \
  tests/test_init.py \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_scope.py \
  docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch-health-trend.md
git add tests/test_*_scope.py
git commit -m "feat: add proposal evidence comparison history batch health trend batch health trend"
```

Expected: commit succeeds and includes only intended Node 15 changes. If `git add tests/test_*_scope.py` stages unrelated files from other agents, unstage those unrelated files with `git restore --staged <path>` and stage only the scope allowlist files that Node 15 intentionally changed.

- [ ] **Step 6: Push**

Run:

```bash
git push
git status --short --branch --untracked-files=all
```

Expected: push succeeds. Final git status shows the branch is up to date with the remote and no uncommitted Node 15 changes remain. If unrelated dirty files from other agents remain, list them in the handoff and do not revert them.

## Acceptance Criteria

- Public API exports exactly the ten Node 15 names from the module and package root; the default boundary constant exists only inside the module and is not exported.
- The production module imports only Python standard library modules plus the allowed Node 14 public dataclasses.
- The builder accepts only exact `list` or `tuple` containers of exact `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport` values, rejects loader-shaped and iterable-shaped inputs before iteration, and rejects subclasses.
- The report deterministically summarizes supplied Node 14 reports: counts, ratios, status rows, config-version summaries, Node 14 gate-status summaries, first/last UTC `generated_at` bounds, duplicate generated-at summaries, and duplicate fingerprint summaries.
- Gate results and report status are derived only from sample size, incomplete trend-batch-health ratio, duplicate generated-at ratio, and duplicate fingerprint ratio, using the status priority in this plan.
- Node 15 `trend_batch_health_sample` cannot fail, and Node 14 upstream `trend_batch_sample` failure summaries are rejected as impossible.
- `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog.append(report)` validates the full report tree before opening/writing, writes append-only JSONL, and never exposes a JSONL reader, loader, replay, glob, from-file, from-log, API-client, browser-automation, account-automation, trading, order-placement, or financial-advice API.
- README and scope tests explicitly preserve report-only/no-loader/no-reader/no-scraping/no-browser-automation/no-account-automation/no-API-client/no-execution/no-order-placement/no-recommendation/no-financial-advice/no-compliance boundaries.

## Self-Review

- Spec coverage: The plan creates a supplied-input, report-only trend layer over Node 14 trend-batch-health reports and does not add fetching, scraping, browser automation, account automation, JSONL reads, raw upstream ingestion, API clients, outcome loading, realized false-positive analysis, profitability analysis, proposal approval, decision resolution, investment ranking, trade recommendations, financial advice, credential handling, order placement, live execution, settlement/reconciliation work, manual execution import, or compliance/legal/geographic analysis.
- Placeholder scan: The plan contains no vague implementation gaps. Public API, statuses, gate rules, counting rules, validation rules, tests, README requirements, verification commands, Claude review policy, commit/push flow, and handoff fields are specified.
- Type consistency: The same names are used throughout: `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog`, and `build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report`.

## Final Handoff Evidence Template (Node 15 Worker Completes)

This section is the required evidence schema for the Node 15 worker to populate after implementation, verification, review, commit, and push. It is not an implementation placeholder; it defines the exact evidence fields that must be recorded in the completed handoff:

- Node completed: Level 2 Node 15 Proposal Evidence Comparison History Batch Health Trend Batch Health Trend.
- Changed files: list every Node 15 source, test, docs, README, and export file changed by the implementation.
- Verification evidence: record command, exit code, and concise result for `.venv/bin/python -m pytest -q`, focused pytest commands, `git diff --check`, `codegraph sync`, `codegraph status .`, secret scan, and final `git status --short --branch --untracked-files=all`.
- Claude implementation review: record exact command target, `Critical findings` count, `Important findings` count, verdict, and any non-blocking minor findings.
- Claude next-plan review: record exact plan path reviewed, `Critical findings` count, `Important findings` count, verdict, and any non-blocking minor findings.
- Commit and push: record commit hash, branch, remote, push result, and whether the branch is up to date.
- Uncommitted files after push: list remaining files and mark which are unrelated pre-existing work from other agents.
- Next safe step: state the next node or review action that can proceed without overlapping file edits.

## Final Handoff Summary (Node 15 Worker Completes)

- Node completed: Level 2 Node 15 Proposal Evidence Comparison History Batch Health Trend Batch Health Trend.
- Changed files:
  - `README.md`
  - `src/polymarket_alpha_lab/__init__.py`
  - `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py`
  - `tests/test_init.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_scope.py`
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
  - `tests/test_proposal_evidence_comparison_history_scope.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_scope.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_scope.py`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch-health-trend.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-artifact-registry.md`
- Verification evidence before commit:
  - `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_scope.py tests/test_init.py -q` exited 0 with `54 passed in 0.64s`.
  - `.venv/bin/python -m pytest tests/test_api.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py tests/test_proposal_review_quality_scope.py tests/test_proposal_review_diagnostics_scope.py tests/test_proposal_review_coverage_scope.py tests/test_proposal_review_dossier_scope.py tests/test_proposal_review_dossier_batch_scope.py tests/test_proposal_evidence_comparison_scope.py tests/test_proposal_evidence_comparison_history_scope.py tests/test_proposal_evidence_comparison_history_batch_health_scope.py tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_scope.py tests/test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_scope.py -q` exited 0 with `158 passed in 3.84s`.
  - `.venv/bin/python -m pytest -q` exited 0 with `791 passed in 7.02s`.
  - `git diff --check` exited 0.
  - `codegraph sync && codegraph status .` exited 0 and reported the index is up to date.
  - `rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----" README.md docs src tests` exited 1 with no matches.
- Claude implementation review:
  - Command target: current Node 15 implementation against this plan using local Claude Code with `--model claude-opus-4-8`, `--effort max`, `--permission-mode dontAsk`, and `--disallowed-tools "Edit,Write"`.
  - Result: Critical findings count 0, Important findings count 0, Minor findings count 0, Verdict Proceed.
- Claude next-plan review:
  - Reviewed plan: `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-artifact-registry.md`.
  - Final result after fixing earlier plan review findings: Critical findings count 0, Important findings count 0, Minor findings count 2, Verdict Proceed.
  - Non-blocking minor findings: import instruction in Task 2 Step 2 could be formatted as a full import statement, and package `__all__` insertion ordering is left to existing local convention.
- Known residual risks:
  - Public leaf dataclasses still allow standalone non-canonical Decimal scale outside full report-tree validation, matching Node 14 behavior. Persisted reports and append paths reject noncanonical top-level ratios, status-row ratios, and rate-gate observed values before writes.
  - Next plan is intentionally small and static; it does not continue the recursive batch/trend chain to avoid a plan that depends on copying a 1300-line implementation.
- Commit and push:
  - A pre-amend local commit was created as `d5e8d669427b5bfcbe3cc8e332b402a2e807fe6d` on branch `main`, then superseded by a handoff-only amend.
  - Final commit hash, push target, and final clean status are recorded in the assistant closeout after commit finalization and `git push`; embedding the final commit hash in this same committed file would change that hash again.
- Next safe step:
  - After Node 15 is committed and pushed, execute `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-artifact-registry.md` with disjoint agent file ownership.
