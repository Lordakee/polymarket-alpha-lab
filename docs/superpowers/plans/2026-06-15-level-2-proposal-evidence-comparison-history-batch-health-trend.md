# Level 2 Proposal Evidence Comparison History Batch Health Trend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a report-only trend artifact that summarizes caller-supplied proposal evidence comparison history batch-health reports over time for audit stability checks.

**Architecture:** Create a focused `proposal_evidence_comparison_history_batch_health_trend.py` module that consumes only in-memory `TradeProposalEvidenceComparisonHistoryBatchHealthReport` objects from Level 2 Node 11. It clones and revalidates each supplied batch-health report, then summarizes batch-health status frequencies, gate-status frequencies, config-version coverage, duplicate generated-at indicators, duplicate fingerprint indicators, and first/last report time bounds for audit only, with append-only JSONL persistence for already-built trend snapshots.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, UTC `datetime`, JSONL append-only persistence, pytest, CodeGraph, and local Claude Code review with model `claude-opus-4-8` using effort `max`.

---

## Scope Boundaries

This node consumes only caller-supplied, in-memory `TradeProposalEvidenceComparisonHistoryBatchHealthReport` objects from `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health`. The word "trend" means a supplied-object audit trend over batch-health reports, not file discovery, log replay, archive loading, globbing, historical data fetching, or performance/outcome analysis.

This node must not consume raw Node 10 history reports, raw Node 9 comparison reports, raw forecast evidence reports, raw dossier batch reports, raw proposal packets, raw proposal-review records, market scores, order books, paper positions, NAV snapshots, API payloads, JSONL files, archived payloads, external history, web pages, account state, credentials, wallets, broker payloads, execution records, outcome data, settlement data, reconciliation data, or compliance/legal/geographic inputs.

This node must not fetch market/order-book/price/outcome/account data, read JSONL logs, replay history, glob files, scrape websites, run browser automation, authenticate, handle credentials or private keys, open user WebSockets, run heartbeat logic, build order requests, place/submit/sign/send/create/cancel orders, select approved proposals, select latest decisions, resolve conflicting reviews, rank investments, recommend trades, promote strategies, review settlement, reconcile positions or exchange accounts, import manual executions, or perform compliance/legal/geographic analysis.

This node must reject convenience inputs that would imply a loader surface: strings, bytes, mappings/dicts, paths, serialized JSON, JSONL lines, generators, arbitrary iterables, log-shaped objects, and subclasses of `TradeProposalEvidenceComparisonHistoryBatchHealthReport`.

Allowed first-party imports in the production module are limited to import-from symbols from `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health`:

```python
TradeProposalEvidenceComparisonHistoryBatchHealthGateResult
TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow
TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary
TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary
TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary
TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary
TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary
TradeProposalEvidenceComparisonHistoryBatchHealthReport
```

The production module must not import the Node 11 boundary constant, `TradeProposalEvidenceComparisonHistoryBatchHealthLog`, private helpers, raw upstream modules, HTTP/browser/account/order/execution modules, or any first-party module outside the allowlist above. It must implement its own local `_json_ready` helper for `Decimal`, UTC `datetime`, tuple/list, and dict normalization.

## Public API

Create `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend.py` with:

```python
__all__ = (
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_report",
)
```

Define a module-internal boundary constant named `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT`. It must state that the artifact is report-only over supplied proposal evidence comparison history batch-health reports and explicitly exclude approval workflows, proposal approval, approved-proposal selectors, latest-decision selectors, decision-resolution processes, investment ranking, trade recommendations, strategy-promotion signals, trade/order instructions, broker/order requests, account actions, credential workflows, external-history loaders, JSONL readers, scraping workflows, outcome loaders, settlement review, reconciliation, compliance/legal/geographic analysis, realized false-positive analysis, profitability analysis, and automatic order-placement authorization. This constant must not be in module `__all__`, package-root imports, or package-root `__all__`.

Public dataclasses:

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig:
    config_version: str
    min_batch_health_report_count: int = 1
    max_incomplete_batch_health_ratio: Decimal = Decimal("0.0000")
    max_duplicate_generated_at_ratio: Decimal = Decimal("0.0000")
    max_duplicate_fingerprint_ratio: Decimal = Decimal("0.0000")
    boundary_statement: str = (
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT
    )
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow:
    batch_health_status: str
    batch_health_count: int
    batch_health_ratio: Decimal | None
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary:
    batch_health_config_version: str
    batch_health_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary:
    gate_name: str
    gate_status: str
    batch_health_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary:
    generated_at: datetime
    duplicate_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary:
    report_fingerprint: str
    duplicate_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    batch_health_report_count: int
    ready_batch_health_report_count: int
    incomplete_batch_health_report_count: int
    duplicate_generated_at_batch_health_report_count: int
    duplicate_fingerprint_batch_health_report_count: int
    divergent_batch_health_report_count: int
    unstable_batch_health_report_count: int
    duplicate_generated_at_count: int
    duplicate_fingerprint_count: int
    incomplete_batch_health_ratio: Decimal | None
    duplicate_generated_at_ratio: Decimal | None
    duplicate_fingerprint_ratio: Decimal | None
    first_batch_health_generated_at: datetime | None
    last_batch_health_generated_at: datetime | None
    status: str
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult, ...]
    status_rows: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow, ...]
    config_version_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary,
        ...,
    ]
    gate_status_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary,
        ...,
    ]
    duplicate_generated_at_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary,
        ...,
    ]
    duplicate_fingerprint_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary,
        ...,
    ]
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog:
    path: Path | str

    def append(
        self,
        report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
    ) -> None:
        ...
```

Builder signature:

```python
def build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
    batch_health_reports: (
        list[TradeProposalEvidenceComparisonHistoryBatchHealthReport]
        | tuple[TradeProposalEvidenceComparisonHistoryBatchHealthReport, ...]
    ),
    *,
    config: TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig,
    generated_at: datetime,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport:
    ...
```

## Status And Gate Rules

Gate names:

```python
GATE_NAMES = (
    "batch_health_sample",
    "incomplete_batch_health_rate",
    "duplicate_generated_at_rate",
    "duplicate_fingerprint_rate",
)
```

Gate statuses are `pass`, `fail`, or `incomplete`.

Report statuses:

```python
REPORT_STATUSES = (
    "incomplete_batch_health_trend",
    "duplicate_generated_at_batch_health_trend",
    "duplicate_fingerprint_batch_health_trend",
    "proposal_evidence_comparison_history_batch_health_trend_ready",
)
```

Status mapping:

- If `batch_health_sample` is `incomplete`, report status is `incomplete_batch_health_trend`.
- Else if `duplicate_generated_at_rate` is `fail`, report status is `duplicate_generated_at_batch_health_trend`.
- Else if `duplicate_fingerprint_rate` is `fail`, report status is `duplicate_fingerprint_batch_health_trend`.
- Else if `incomplete_batch_health_rate` is `fail`, report status is `incomplete_batch_health_trend`.
- Else if any gate is `incomplete`, report status is `incomplete_batch_health_trend`.
- Else report status is `proposal_evidence_comparison_history_batch_health_trend_ready`.

Node 11 batch-health statuses must be summarized in this exact sorted order:

```python
BATCH_HEALTH_STATUSES = (
    "divergent_history_batch_health",
    "duplicate_fingerprint_batch_health",
    "duplicate_generated_at_batch_health",
    "incomplete_history_batch_health",
    "proposal_evidence_comparison_history_batch_health_ready",
    "unstable_history_batch_health",
)
```

## Counting And Ordering Rules

- Clone/revalidate every exact `TradeProposalEvidenceComparisonHistoryBatchHealthReport` before aggregation.
- Accept only exact `list` or `tuple` containers; reject strings, bytes, mappings, paths, generators, arbitrary iterables, and log-shaped objects before iteration.
- Sort cloned reports with `sorted(cloned_reports, key=lambda report: (report.generated_at, report.config_version, report.status))`.
- `first_batch_health_generated_at` and `last_batch_health_generated_at` come from sorted cloned reports' normalized UTC `generated_at` values.
- Duplicate generated-at groups are keyed by cloned report `generated_at`.
- Duplicate fingerprint groups are keyed by canonical JSON fingerprints built from each cloned report's validated JSON-ready tree.
- Duplicate counts use full collision-group sizes, not extras beyond the first item.
- `incomplete_batch_health_ratio` counts every supplied Node 11 report whose status is not `proposal_evidence_comparison_history_batch_health_ready`.
- `duplicate_generated_at_ratio` and `duplicate_fingerprint_ratio` use the duplicate count over total report count.
- Ratios are `None` when `batch_health_report_count == 0`; otherwise quantized to `Decimal("0.0001")` with `ROUND_HALF_EVEN`.
- `status_rows` contain exactly one row per `BATCH_HEALTH_STATUSES`, sorted as the tuple above.
- `config_version_summaries` contain one row per distinct `batch_health_config_version`, sorted by version.
- `gate_status_summaries` group existing Node 11 `gate_results` by `(gate_name, gate_status)` and count how many batch-health reports contain each pair once.
- `duplicate_generated_at_summaries` and `duplicate_fingerprint_summaries` include only groups with `duplicate_count >= 2`, sorted by key.

## Task 1: Behavior Tests

**Files:**

- Create: `tests/test_proposal_evidence_comparison_history_batch_health_trend.py`

- [ ] **Step 1: Write deterministic fixtures**

Construct static `TradeProposalEvidenceComparisonHistoryBatchHealthReport` values directly from Node 11 public dataclasses. Do not import Node 10 builders, Node 9 fixtures, raw forecast/dossier/proposal/review helpers, or Node 11 log classes.

Use this fixture shape:

```python
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health import (
    TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow,
)
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog,
    build_trade_proposal_evidence_comparison_history_batch_health_trend_report,
)


def _ratio(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(count) / Decimal(total)).quantize(Decimal("0.0001"))


def batch_health_report_fixture(
    *,
    status: str = "proposal_evidence_comparison_history_batch_health_ready",
    index: int = 1,
    generated_at: datetime | None = None,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthReport:
    generated_at = generated_at or datetime(2026, 9, 12, 12, index, tzinfo=UTC)
    status_counts = {
        "divergent_comparison_history": 0,
        "incomplete_comparison_history": 0,
        "proposal_evidence_comparison_history_ready": 2,
        "unstable_comparison_history": 0,
    }
    degraded_counts = {
        "complete": 1 if status == "proposal_evidence_comparison_history_batch_health_ready" else 0,
        "incomplete": 1 if status == "incomplete_history_batch_health" else 0,
        "duplicate_generated_at": 1 if status == "duplicate_generated_at_batch_health" else 0,
        "duplicate_fingerprint": 1 if status == "duplicate_fingerprint_batch_health" else 0,
        "divergent": 1 if status == "divergent_history_batch_health" else 0,
        "unstable": 1 if status == "unstable_history_batch_health" else 0,
    }
    if sum(degraded_counts.values()) != 1:
        raise AssertionError(f"unknown fixture status: {status}")
    history_count = 2
    duplicate_generated_at_count = 2 if status == "duplicate_generated_at_batch_health" else 0
    duplicate_fingerprint_count = 2 if status == "duplicate_fingerprint_batch_health" else 0
    return TradeProposalEvidenceComparisonHistoryBatchHealthReport(
        generated_at=generated_at,
        config_version="history-batch-health-v1",
        report_only=True,
        boundary_statement=(
            "This is a report-only proposal evidence comparison history batch health artifact over "
            "supplied proposal evidence comparison history reports, not an approval workflow, "
            "proposal approval, approved-proposal selector, latest-decision selector, "
            "decision-resolution process, investment ranking, trade recommendation, "
            "strategy-promotion signal, trade instruction, order instruction, broker "
            "request, order request, account action, account authentication, private-key "
            "handling, wallet signature, live-execution signal, credential workflow, "
            "external-history loader, JSONL reader, scraping workflow, outcome loader, "
            "settlement review, reconciliation process, compliance review, geographic "
            "access analysis, realized false-positive analysis, profitability analysis, "
            "or automatic order-placement authorization."
        ),
        history_report_count=history_count,
        complete_history_report_count=status_counts[
            "proposal_evidence_comparison_history_ready"
        ],
        incomplete_history_report_count=status_counts["incomplete_comparison_history"],
        divergent_history_report_count=status_counts["divergent_comparison_history"],
        unstable_history_report_count=status_counts["unstable_comparison_history"],
        duplicate_generated_at_count=duplicate_generated_at_count,
        duplicate_fingerprint_count=duplicate_fingerprint_count,
        incomplete_history_ratio=Decimal("0.0000"),
        divergent_history_ratio=Decimal("0.0000"),
        unstable_history_ratio=Decimal("0.0000"),
        duplicate_generated_at_ratio=_ratio(duplicate_generated_at_count, history_count),
        duplicate_fingerprint_ratio=_ratio(duplicate_fingerprint_count, history_count),
        first_history_generated_at=generated_at,
        last_history_generated_at=generated_at,
        status=status,
        gate_results=(
            TradeProposalEvidenceComparisonHistoryBatchHealthGateResult(
                "history_sample",
                "pass",
                "sample checked",
                history_count,
                1,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthGateResult(
                "incomplete_history_rate",
                "pass",
                "incomplete checked",
                Decimal("0.0000"),
                Decimal("0.0000"),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthGateResult(
                "divergent_history_rate",
                "pass",
                "divergent checked",
                Decimal("0.0000"),
                Decimal("0.0000"),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthGateResult(
                "unstable_history_rate",
                "pass",
                "unstable checked",
                Decimal("0.0000"),
                Decimal("0.0000"),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthGateResult(
                "duplicate_generated_at_rate",
                "fail" if duplicate_generated_at_count else "pass",
                "duplicate generated checked",
                _ratio(duplicate_generated_at_count, history_count),
                Decimal("0.0000"),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthGateResult(
                "duplicate_fingerprint_rate",
                "fail" if duplicate_fingerprint_count else "pass",
                "duplicate fingerprint checked",
                _ratio(duplicate_fingerprint_count, history_count),
                Decimal("0.0000"),
            ),
        ),
        status_rows=(
            TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow(
                "divergent_comparison_history",
                status_counts["divergent_comparison_history"],
                _ratio(status_counts["divergent_comparison_history"], history_count),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow(
                "incomplete_comparison_history",
                status_counts["incomplete_comparison_history"],
                _ratio(status_counts["incomplete_comparison_history"], history_count),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow(
                "proposal_evidence_comparison_history_ready",
                status_counts["proposal_evidence_comparison_history_ready"],
                _ratio(
                    status_counts["proposal_evidence_comparison_history_ready"],
                    history_count,
                ),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow(
                "unstable_comparison_history",
                status_counts["unstable_comparison_history"],
                _ratio(status_counts["unstable_comparison_history"], history_count),
            ),
        ),
        config_version_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary(
                "comparison-history-v1",
                history_count,
            ),
        ),
        duplicate_generated_at_summaries=(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary(
                    generated_at,
                    duplicate_generated_at_count,
                ),
            )
            if duplicate_generated_at_count
            else ()
        ),
        duplicate_fingerprint_summaries=(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary(
                    "fixture-fingerprint",
                    duplicate_fingerprint_count,
                ),
            )
            if duplicate_fingerprint_count
            else ()
        ),
        finding_summaries=(),
        source_transition_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary(
                "dossier_batch",
                "proposal_review_dossier_batch_ready",
                "proposal_review_dossier_batch_ready",
                1,
            ),
        ),
    )
```

- [ ] **Step 2: Run behavior RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend.py -q
```

Expected: FAIL because `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend` does not exist.

- [ ] **Step 3: Add behavior cases**

Add these concrete tests after the fixture helpers. They are intentionally scoped to supplied Node 11 batch-health reports and must not import Node 10/Node 9 builders or fixtures.

```python
def trend_config(**overrides):
    values = {
        "config_version": "batch-health-trend-v1",
        "max_incomplete_batch_health_ratio": Decimal("1.0000"),
        "max_duplicate_generated_at_ratio": Decimal("1.0000"),
        "max_duplicate_fingerprint_ratio": Decimal("1.0000"),
    }
    values.update(overrides)
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig(**values)


def test_batch_health_trend_summarizes_supplied_reports():
    reports = [
        batch_health_report_fixture(status="unstable_history_batch_health", index=6),
        batch_health_report_fixture(status="duplicate_fingerprint_batch_health", index=3),
        batch_health_report_fixture(status="proposal_evidence_comparison_history_batch_health_ready", index=1),
        batch_health_report_fixture(status="incomplete_history_batch_health", index=4),
        batch_health_report_fixture(status="duplicate_generated_at_batch_health", index=2),
        batch_health_report_fixture(status="divergent_history_batch_health", index=5),
    ]

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        reports,
        config=trend_config(),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )

    assert report.report_only is True
    assert report.status == "proposal_evidence_comparison_history_batch_health_trend_ready"
    assert report.batch_health_report_count == 6
    assert report.ready_batch_health_report_count == 1
    assert report.incomplete_batch_health_report_count == 1
    assert report.duplicate_generated_at_batch_health_report_count == 1
    assert report.duplicate_fingerprint_batch_health_report_count == 1
    assert report.divergent_batch_health_report_count == 1
    assert report.unstable_batch_health_report_count == 1
    assert report.incomplete_batch_health_ratio == Decimal("0.8333")
    assert tuple(row.batch_health_status for row in report.status_rows) == (
        "divergent_history_batch_health",
        "duplicate_fingerprint_batch_health",
        "duplicate_generated_at_batch_health",
        "incomplete_history_batch_health",
        "proposal_evidence_comparison_history_batch_health_ready",
        "unstable_history_batch_health",
    )
    assert tuple(row.batch_health_count for row in report.status_rows) == (
        1,
        1,
        1,
        1,
        1,
        1,
    )
    assert report.config_version_summaries[0].batch_health_config_version == (
        "history-batch-health-v1"
    )
    assert report.gate_status_summaries
```

```python
def test_batch_health_trend_empty_sample_is_incomplete():
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        [],
        config=trend_config(),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )

    assert report.status == "incomplete_batch_health_trend"
    assert report.batch_health_report_count == 0
    assert report.incomplete_batch_health_ratio is None
    assert report.duplicate_generated_at_ratio is None
    assert report.duplicate_fingerprint_ratio is None
    assert report.first_batch_health_generated_at is None
    assert report.last_batch_health_generated_at is None
    assert all(row.batch_health_ratio is None for row in report.status_rows)
    assert tuple(row.status for row in report.gate_results) == (
        "incomplete",
        "incomplete",
        "incomplete",
        "incomplete",
    )
```

```python
def test_batch_health_trend_duplicate_counts_use_full_collision_groups():
    shared_time = datetime(2026, 9, 13, 1, tzinfo=UTC)
    two_time = [
        replace(batch_health_report_fixture(index=1), generated_at=shared_time),
        replace(batch_health_report_fixture(index=2), generated_at=shared_time),
    ]
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        two_time,
        config=trend_config(),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )
    assert report.duplicate_generated_at_count == 2
    assert report.duplicate_generated_at_summaries[0].duplicate_count == 2

    three_time = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        [
            replace(batch_health_report_fixture(index=3), generated_at=shared_time),
            replace(batch_health_report_fixture(index=4), generated_at=shared_time),
            replace(batch_health_report_fixture(index=5), generated_at=shared_time),
        ],
        config=trend_config(),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )
    assert three_time.duplicate_generated_at_count == 3
    assert three_time.duplicate_generated_at_summaries[0].duplicate_count == 3

    identical = batch_health_report_fixture(index=9)
    two_fingerprint = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        [identical, identical],
        config=trend_config(),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )
    assert two_fingerprint.duplicate_fingerprint_count == 2
    assert two_fingerprint.duplicate_fingerprint_summaries[0].duplicate_count == 2

    three_fingerprint = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        [identical, identical, identical],
        config=trend_config(),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )
    assert three_fingerprint.duplicate_fingerprint_count == 3
    assert three_fingerprint.duplicate_fingerprint_summaries[0].duplicate_count == 3
```

```python
def test_batch_health_trend_gate_status_summaries_use_existing_gate_rows():
    first = batch_health_report_fixture(index=1)
    second = batch_health_report_fixture(
        status="duplicate_generated_at_batch_health",
        index=2,
    )

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        [second, first],
        config=trend_config(),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )

    assert (
        "duplicate_generated_at_rate",
        "fail",
        1,
    ) in tuple(
        (row.gate_name, row.gate_status, row.batch_health_count)
        for row in report.gate_status_summaries
    )
    assert (
        "history_sample",
        "pass",
        2,
    ) in tuple(
        (row.gate_name, row.gate_status, row.batch_health_count)
        for row in report.gate_status_summaries
    )
```

```python
def test_batch_health_trend_ordering_uses_normalized_generated_at():
    late = batch_health_report_fixture(index=3)
    early = replace(
        batch_health_report_fixture(index=1),
        generated_at=datetime(2026, 9, 12, 21, tzinfo=timezone(timedelta(hours=-4))),
    )
    middle = batch_health_report_fixture(index=2)

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        [late, middle, early],
        config=trend_config(),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )

    assert report.first_batch_health_generated_at == middle.generated_at
    assert report.last_batch_health_generated_at == datetime(2026, 9, 13, 1, tzinfo=UTC)
```

```python
def test_batch_health_trend_rejects_bad_inputs_before_iteration():
    class ExplodingIterable:
        def __iter__(self):
            raise AssertionError("loader-shaped iterable was consumed")

    class LogShapedInput:
        path = Path("batch-health.jsonl")

        def append(self, report):
            raise AssertionError("append-only log was consumed")

    for bad_input in (
        "[]",
        b"[]",
        {"report": batch_health_report_fixture()},
        Path("batch-health.jsonl"),
        '{"serialized": true}',
        (item for item in (batch_health_report_fixture(),)),
        ExplodingIterable(),
        LogShapedInput(),
        object(),
    ):
        with pytest.raises(ValueError, match="batch_health_reports"):
            build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
                bad_input,
                config=trend_config(),
                generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
            )
```

```python
def unsafe_trend_report(report, **changes):
    clone = object.__new__(type(report))
    for field_name in report.__dataclass_fields__:
        object.__setattr__(clone, field_name, getattr(report, field_name))
    for field_name, value in changes.items():
        object.__setattr__(clone, field_name, value)
    return clone


def test_batch_health_trend_rejects_subclasses_and_mutated_nested_rows(tmp_path):
    source = batch_health_report_fixture(index=1)

    class BatchHealthSubclass(TradeProposalEvidenceComparisonHistoryBatchHealthReport):
        pass

    subclass_value = BatchHealthSubclass(**{
        field_name: getattr(source, field_name)
        for field_name in source.__dataclass_fields__
    })
    with pytest.raises(ValueError, match="TradeProposalEvidenceComparisonHistoryBatchHealthReport"):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
            [subclass_value],
            config=trend_config(),
            generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
        )

    drift = batch_health_report_fixture(index=2)
    object.__setattr__(drift.gate_results[0], "status", "unknown")
    with pytest.raises(ValueError, match="status"):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
            [drift],
            config=trend_config(),
            generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
        )

    valid = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        [source],
        config=trend_config(),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )
    invalid = unsafe_trend_report(valid, duplicate_generated_at_ratio=Decimal("NaN"))
    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog(
        tmp_path / "trend.jsonl",
    )
    with pytest.raises(ValueError, match="finite|duplicate_generated_at_ratio"):
        log.append(invalid)
    assert not log.path.exists()
```

```python
def test_batch_health_trend_rejects_stale_or_wrong_typed_gate_payloads(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        [batch_health_report_fixture(index=1), batch_health_report_fixture(index=2)],
        config=trend_config(),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )

    bad_sample_type = unsafe_trend_report(
        report,
        gate_results=(
            replace(report.gate_results[0], observed_value=Decimal("2")),
            *report.gate_results[1:],
        ),
    )
    with pytest.raises(ValueError, match="batch_health_sample observed_value"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog(
            tmp_path / "bad-sample.jsonl",
        ).append(bad_sample_type)

    bad_rate_type = unsafe_trend_report(
        report,
        gate_results=(
            *report.gate_results[:1],
            replace(report.gate_results[1], observed_value=0),
            *report.gate_results[2:],
        ),
    )
    with pytest.raises(ValueError, match="observed_value must be a Decimal"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog(
            tmp_path / "bad-rate.jsonl",
        ).append(bad_rate_type)
```

## Task 2: Scope And Export Tests

**Files:**

- Create: `tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py`
- Modify: `tests/test_init.py`
- Modify every sibling Level 2 scope allowlist that enumerates package-root exports:
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
- Modify: `README.md`

- [ ] **Step 1: Write failing scope tests**

Create an AST scope test mirroring `tests/test_proposal_evidence_comparison_history_batch_health_scope.py` with:

- module `__all__` equal to the ten public names in this plan
- imports limited to standard library plus `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health`
- first-party imports only from the allowed Node 11 public dataclasses listed in this plan
- no raw upstream modules, loaders, readers, replay/glob/from-file/from-log helpers, fetching, scraping/browser, auth/credential/wallet/broker/execution/order/request/session/websocket, approval, selection, decision-resolution, ranking, recommendation, promotion, outcome, settlement/reconciliation, profitability, compliance/legal/geographic identifiers
- package root exports contain only the Node 12 trend public names for this node
- README Node 12 section states supplied-input, report-only, no-read, no-fetch, no-outcome, no-settlement, no-ranking, no-recommendation, no-approval, and no-execution boundaries

- [ ] **Step 2: Add package-root export tests**

Extend `tests/test_init.py` with `test_level_2_node_12_public_api_exports()` using the existing identity-assertion style for the ten public names. Extend the private-boundary test to verify `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT` is present on the module and absent from package-root exports.

Add this exact export set to every scope allowlist file listed above and include it in `EXPECTED_LEVEL_2_ARTIFACT_EXPORTS`:

```python
EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_EXPORTS = {
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_report",
}
```

- [ ] **Step 3: Run scope RED**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py \
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
  -q
```

Expected: FAIL because module/root exports do not exist.

## Task 3: Implementation

**Files:**

- Create: `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`

- [ ] **Step 1: Implement production module**

Implement the module using Node 11 as the immediate pattern:

- frozen dataclasses
- exact public input type checks
- exact list/tuple input container check
- clone/revalidate every Node 11 batch-health report by reconstructing its public dataclasses
- local `_json_ready`, `_as_utc`, `_require_*`, tuple clone, ratio, path normalization, and report-tree validation helpers
- duplicate generated-at and duplicate fingerprint summaries by full collision-group size
- gate payload validation before append writes
- append-only JSONL output only
- no file readers, loaders, replay helpers, selectors, ranking, recommendation, approval, outcome, settlement, reconciliation, profitability, compliance/legal/geographic, credential, order, execution, browser, scraping, HTTP, request, session, or WebSocket surfaces

- [ ] **Step 2: Add root exports**

Add the ten Node 12 trend public names to `src/polymarket_alpha_lab/__init__.py` import blocks and `__all__`. Do not add the boundary constant.

- [ ] **Step 3: Add README sections**

Insert `## Level 2 Node 12 Status` and `## Level 2 Node 12 Python API` before `## Automation Roadmap`. State that Node 12 is report-only over supplied `TradeProposalEvidenceComparisonHistoryBatchHealthReport` values, summarizes batch-health status and gate status stability, duplicate generated-at and fingerprint indicators, and append-only JSONL persistence. Explicitly state it does not fetch data, read logs, scrape, authenticate, handle credentials/private keys, place/cancel orders, open WebSockets, run heartbeat, use trading SDK/broker/execution clients, build request payloads, approve proposals, select latest decisions, resolve conflicts, rank investments, recommend trades, perform outcome/settlement/reconciliation/profitability analysis, import manual executions, or perform compliance/legal/geographic analysis.

Update README repository layout entries for:

- `2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend.md`
- `proposal_evidence_comparison_history_batch_health_trend.py`
- `test_proposal_evidence_comparison_history_batch_health_trend.py`
- `test_proposal_evidence_comparison_history_batch_health_trend_scope.py`

- [ ] **Step 4: Run focused GREEN**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_proposal_evidence_comparison_history_batch_health_trend.py \
  tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py \
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

Expected: all tests pass, diff check exits 0, CodeGraph is up to date, and git status shows only intended Node 12 files.

- [ ] **Step 2: Claude Code implementation review**

Run local Claude Code with model `claude-opus-4-8` and effort `max`. Treat any forbidden raw upstream dependency, data fetch/load/read/scrape/auth/credential/wallet/broker/execution/request/session/websocket/order surface, approval workflow, approved-proposal selection, decision resolution, ranking, recommendation, promotion, outcome loading, realized false-positive analysis, profitability analysis, settlement, reconciliation, manual execution import, or compliance/legal/geographic analysis as Critical. Accepted terminal state is `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed`. Minor findings may remain only if documented as non-blocking.

- [ ] **Step 3: Append Handoff Summary**

Append actual evidence to this plan with node completed, commit/push status, repo status before commit, verification command results, Claude review counts/verdict, changed files, uncommitted files after push, and next safe step.

## Self-Review

- Spec coverage: The plan creates a supplied-input, report-only trend layer over Node 11 batch-health reports and does not add fetching, scraping, JSONL reads, raw upstream ingestion, outcome loading, realized false-positive analysis, profitability analysis, proposal approval, decision resolution, investment ranking, trade recommendations, credential handling, order placement, settlement/reconciliation work, manual execution import, or compliance/legal/geographic analysis.
- Placeholder scan: The plan contains no TBD/TODO placeholders. Public API, statuses, gate rules, counting rules, validation rules, tests, README requirements, verification commands, Claude review policy, and handoff fields are specified.
- Type consistency: The same names are used throughout: `TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport`, `TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog`, and `build_trade_proposal_evidence_comparison_history_batch_health_trend_report`.

## Handoff Summary

Node 12 implementation status: complete and ready for commit.

RED evidence:

- Behavior RED: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend.py -q` failed with `ModuleNotFoundError` before the production module existed.
- Scope/export RED: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py tests/test_init.py ... -q` failed because package-root/module exports did not exist.
- Review regression RED 1: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend.py::test_batch_health_trend_rejects_missing_or_stale_gate_status_summaries -q` failed because missing `gate_status_summaries` were accepted.
- Review regression RED 2: the same focused test failed after adding a compensated stale case where one Node 11 gate was omitted and another over-counted while the global total remained correct.

GREEN evidence:

- Focused behavior: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend.py -q` -> `11 passed`.
- Focused Node 12/API: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend.py tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py tests/test_init.py -q` -> `40 passed`.
- Scope/export combo: `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py tests/test_proposal_review_quality_scope.py tests/test_proposal_review_diagnostics_scope.py tests/test_proposal_review_coverage_scope.py tests/test_proposal_review_dossier_scope.py tests/test_proposal_review_dossier_batch_scope.py tests/test_proposal_evidence_comparison_scope.py tests/test_proposal_evidence_comparison_history_scope.py tests/test_proposal_evidence_comparison_history_batch_health_scope.py -q` -> `146 passed`.
- Full suite: `.venv/bin/python -m pytest -q` -> `701 passed`.
- `git diff --check` -> clean.
- `codegraph sync` -> already up to date.
- `codegraph status .` -> index up to date, `76 files`, `2,820 nodes`, `9,030 edges`.
- Secret scan: `rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----" README.md docs src tests` -> no findings.

Claude Code implementation review:

- First implementation review: Critical `0`, Important `1`, Minor `0`, Verdict `Do not proceed`; finding was missing/stale `gate_status_summaries` append validation.
- Second implementation review: Critical `0`, Important `1`, Minor `0`, Verdict `Do not proceed`; finding was compensated stale per-gate `gate_status_summaries` could pass a global-total-only check.
- Final implementation review after fixes: Critical `0`, Important `0`, Minor `0`, Verdict `Proceed`.

Next-node plan:

- Added `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch.md`.
- Claude plan review final result: Critical `0`, Important `0`, Minor `0`, Verdict `Proceed`.

Changed files before commit:

- `README.md`
- `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend.md`
- `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch.md`
- `src/polymarket_alpha_lab/__init__.py`
- `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend.py`
- `tests/test_analytics_history_scope.py`
- `tests/test_analytics_scope.py`
- `tests/test_forecast_evidence_scope.py`
- `tests/test_init.py`
- `tests/test_manual_review_queue_scope.py`
- `tests/test_proposal_evidence_comparison_history_batch_health_scope.py`
- `tests/test_proposal_evidence_comparison_history_batch_health_trend.py`
- `tests/test_proposal_evidence_comparison_history_batch_health_trend_scope.py`
- `tests/test_proposal_evidence_comparison_history_scope.py`
- `tests/test_proposal_evidence_comparison_scope.py`
- `tests/test_proposal_packet_scope.py`
- `tests/test_proposal_review_coverage_scope.py`
- `tests/test_proposal_review_diagnostics_scope.py`
- `tests/test_proposal_review_dossier_batch_scope.py`
- `tests/test_proposal_review_dossier_scope.py`
- `tests/test_proposal_review_quality_scope.py`
- `tests/test_proposal_review_scope.py`
- `tests/test_proposal_review_summary_scope.py`

Commit/push status at handoff-write time: pending. Next step is final `git status`, commit, push to `origin/main`, and verify clean post-push status.
