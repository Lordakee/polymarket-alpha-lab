# Level 2 Proposal-Review Dossier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a report-only Level 2 proposal-review dossier that assembles supplied summary, quality, diagnostic, and coverage reports into one deterministic audit artifact.

**Architecture:** Create a new `proposal_review_dossier.py` module that clones and validates caller-supplied report artifacts, compares stable aggregate counts and statuses, emits frozen dataclasses, and appends JSONL snapshots only after full tree validation. The dossier is an audit artifact only: it never approves, ranks, recommends, promotes, routes, resolves latest decisions, selects winning decisions, fetches data, reads logs, handles credentials, or touches execution surfaces.

**Tech Stack:** Python dataclasses, `Decimal`, `datetime` values normalized to UTC using existing sibling-module conventions, local JSON serialization helpers, append-only UTF-8 JSONL logs, pytest, existing `polymarket_alpha_lab` Level 2 report dataclasses, CodeGraph.

---

## Scope Boundaries

This node consumes only these supplied in-memory artifacts:

- `TradeProposalReviewSummaryReport`
- `TradeProposalReviewQualityReport`
- `TradeProposalReviewDiagnosticReport`
- `TradeProposalReviewCoverageReport`

This node must not import raw proposal packets or raw proposal-review records. It must not import or define market/API clients, broker/client/request/session/websocket/order/execution/account/credential/scraping/browser automation/settlement/reconciliation/compliance/legal/geographic surfaces. It must not read JSONL files, load history, open dashboards, create background workers, rank investments, recommend trades, pick a latest review decision, select a winning decision, or route proposals.

The artifact may report that the supplied review dossier is complete, incomplete, inconsistent, or unstable. It must not say that a proposal is approved, promotable, executable, profitable, investable, or ready for live trading.

## Public API

Create `src/polymarket_alpha_lab/proposal_review_dossier.py` with:

```python
__all__ = (
    "TradeProposalReviewDossierConfig",
    "TradeProposalReviewDossierFindingRow",
    "TradeProposalReviewDossierGateResult",
    "TradeProposalReviewDossierLog",
    "TradeProposalReviewDossierReport",
    "TradeProposalReviewDossierSourceRow",
    "build_trade_proposal_review_dossier_report",
)
```

Dataclasses:

```python
@dataclass(frozen=True)
class TradeProposalReviewDossierConfig:
    config_version: str
    require_summary_ready: bool = True
    require_quality_ready: bool = True
    require_diagnostics_ready: bool = True
    require_coverage_ready: bool = True
    boundary_statement: str = DEFAULT_REVIEW_DOSSIER_BOUNDARY_STATEMENT


@dataclass(frozen=True)
class TradeProposalReviewDossierGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None


@dataclass(frozen=True)
class TradeProposalReviewDossierSourceRow:
    report_name: str
    report_status: str
    generated_at: datetime
    review_record_count: int | None
    proposal_packet_count: int | None
    approved_decision_count: int | None
    rejected_decision_count: int | None
    status_category: str


@dataclass(frozen=True)
class TradeProposalReviewDossierFindingRow:
    finding_code: str
    severity: str
    source_report_name: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None


@dataclass(frozen=True)
class TradeProposalReviewDossierReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    summary_generated_at: datetime
    quality_generated_at: datetime
    diagnostic_generated_at: datetime
    coverage_generated_at: datetime
    review_record_count: int
    proposal_packet_count: int
    reviewed_proposal_packet_count: int
    unreviewed_proposal_packet_count: int
    orphan_review_record_count: int
    duplicate_reviewed_proposal_packet_count: int
    conflicting_decision_proposal_packet_count: int
    approved_decision_count: int
    rejected_decision_count: int
    review_coverage_ratio: Decimal | None
    rejection_ratio: Decimal | None
    summary_status: str
    quality_status: str
    diagnostic_status: str
    coverage_status: str
    status: str
    gate_results: tuple[TradeProposalReviewDossierGateResult, ...]
    source_rows: tuple[TradeProposalReviewDossierSourceRow, ...]
    finding_rows: tuple[TradeProposalReviewDossierFindingRow, ...]


@dataclass(frozen=True)
class TradeProposalReviewDossierLog:
    path: Path | str

    def append(self, report: TradeProposalReviewDossierReport) -> None:
        ...
```

Builder:

```python
def build_trade_proposal_review_dossier_report(
    *,
    summary: TradeProposalReviewSummaryReport,
    quality: TradeProposalReviewQualityReport,
    diagnostics: TradeProposalReviewDiagnosticReport,
    coverage: TradeProposalReviewCoverageReport,
    config: TradeProposalReviewDossierConfig,
    generated_at: datetime,
) -> TradeProposalReviewDossierReport:
    ...
```

## Status And Gate Rules

Gate names:

```python
GATE_NAMES = (
    "count_consistency",
    "summary_evidence",
    "quality_evidence",
    "diagnostic_evidence",
    "coverage_evidence",
)
```

Gate statuses:

```python
GATE_STATUSES = ("pass", "fail", "incomplete")
```

Report statuses:

```python
REPORT_STATUSES = (
    "incomplete_review_dossier",
    "inconsistent_review_dossier",
    "unstable_review_dossier",
    "proposal_review_dossier_complete",
)
```

`count_consistency` is an aggregate-count compatibility gate. It does not prove that summary, quality, diagnostics, and coverage were built from the same raw proposal/review identity set because this node intentionally consumes only supplied report artifacts, not raw records or packet identities.

`count_consistency`:

- `pass` when these cross-report counts match:
  - `summary.review_record_count == diagnostics.review_record_count == coverage.review_record_count`
  - `summary.approved_decision_count == diagnostics.approved_decision_count == coverage.approved_decision_count`
  - `summary.rejected_decision_count == diagnostics.rejected_decision_count == coverage.rejected_decision_count`
- Include `quality` in exact count consistency only when `quality.summary_report_count == 1`; then require:
  - `quality.total_review_record_count == summary.review_record_count`
  - `quality.approved_decision_count == summary.approved_decision_count`
  - `quality.rejected_decision_count == summary.rejected_decision_count`
  - `quality.first_summary_generated_at == summary.generated_at`
  - `quality.last_summary_generated_at == summary.generated_at`
- When `quality.summary_report_count > 1`, quality is historical context. Do not force its totals to equal the latest summary, but require:
  - `quality.total_review_record_count >= summary.review_record_count`
  - `quality.approved_decision_count >= summary.approved_decision_count`
  - `quality.rejected_decision_count >= summary.rejected_decision_count`
  - `quality.first_summary_generated_at < quality.last_summary_generated_at`
  - `quality.last_summary_generated_at == summary.generated_at`
- When `quality.summary_report_count == 0`, quality has no summary timestamp identity. Treat it as count-consistent only when:
  - `summary.review_record_count == 0`
  - `summary.approved_decision_count == 0`
  - `summary.rejected_decision_count == 0`
  - `quality.total_review_record_count == 0`
  - `quality.approved_decision_count == 0`
  - `quality.rejected_decision_count == 0`
  - `quality.first_summary_generated_at is None`
  - `quality.last_summary_generated_at is None`
- `fail` otherwise.

`summary_evidence`:

- `pass` when `config.require_summary_ready` is false or `summary.status == "summary_ready"`.
- `incomplete` when `summary.status == "insufficient_review_sample"` and `config.require_summary_ready` is true.
- `fail` when `summary.status == "high_rejection_ratio"` and `config.require_summary_ready` is true.

`quality_evidence`:

- `pass` when `config.require_quality_ready` is false or `quality.status == "proposal_review_quality_ready"`.
- `incomplete` when `quality.status in ("incomplete_review_data", "insufficient_review_sample")` and `config.require_quality_ready` is true.
- `fail` when `quality.status == "unstable_review_quality"` and `config.require_quality_ready` is true.

`diagnostic_evidence`:

- `pass` when `config.require_diagnostics_ready` is false or `diagnostics.status == "diagnostics_ready"`.
- `incomplete` when `diagnostics.status in ("incomplete_review_data", "insufficient_review_sample")` and `config.require_diagnostics_ready` is true.
- `fail` when `diagnostics.status == "high_rejection_proxy"` and `config.require_diagnostics_ready` is true.

`coverage_evidence`:

- `pass` when `config.require_coverage_ready` is false or `coverage.status == "proposal_review_coverage_ready"`.
- `incomplete` when `coverage.status in ("incomplete_proposal_sample", "incomplete_review_coverage")` and `config.require_coverage_ready` is true.
- `fail` when `coverage.status == "inconsistent_review_coverage"` and `config.require_coverage_ready` is true.

Report status:

```python
def _dossier_status(gate_results):
    gates = {row.gate_name: row.status for row in gate_results}
    if (
        gates["count_consistency"] == "fail"
        or gates["coverage_evidence"] == "fail"
    ):
        return "inconsistent_review_dossier"
    if any(row.status == "incomplete" for row in gate_results):
        return "incomplete_review_dossier"
    if any(row.status == "fail" for row in gate_results):
        return "unstable_review_dossier"
    return "proposal_review_dossier_complete"
```

When a `require_*_ready` flag is false, the corresponding source report status is informational for source rows only. In that configuration, `proposal_review_dossier_complete` means all enabled dossier gates passed; it does not require every source row `status_category` to be `complete`.

`count_consistency` failures and required `coverage_evidence` failures produce top-level `inconsistent_review_dossier`; source-level inconsistent coverage remains visible through the coverage source row and as a failed evidence gate.

Gate result rows:

- Gate rows are ordered exactly by `GATE_NAMES`.
- Every gate row must have deterministic `message`, `observed_value`, and `threshold` values.
- `count_consistency` pass:
  - `message="Cross-report aggregate review counts are consistent."`
  - `observed_value="summary=1/1/0; quality=1/1/0; diagnostics=1/1/0; coverage=1/1/0; proposal_counts=1/1/1/1; summary_generated_at=2026-09-08T12:00:00+00:00; quality_last_summary_generated_at=2026-09-08T12:00:00+00:00"` for the one approved complete fixture.
  - In general, format `observed_value` as `summary=<reviews>/<approved>/<rejected>; quality=<reviews>/<approved>/<rejected>; diagnostics=<reviews>/<approved>/<rejected>; coverage=<reviews>/<approved>/<rejected>; proposal_counts=<summary.unique_source_proposal_count>/<quality.summed_unique_source_proposal_count>/<diagnostics.unique_source_proposal_count>/<coverage.proposal_packet_count>; summary_generated_at=<summary.generated_at.isoformat()>; quality_last_summary_generated_at=<quality.last_summary_generated_at.isoformat() or None>`.
  - `threshold="summary/diagnostics/coverage counts match; quality counts match latest summary or contain historical totals"`
- `count_consistency` fail:
  - `message="Cross-report aggregate review counts are inconsistent."`
  - `observed_value` uses the same deterministic count string as the pass row.
  - `threshold="summary/diagnostics/coverage counts match; quality counts match latest summary or contain historical totals"`
- `summary_evidence`:
  - pass and required: `message="Summary evidence is ready."`, `observed_value=summary.status`, `threshold="summary_ready"`.
  - pass and optional: `message="Summary evidence is optional."`, `observed_value=summary.status`, `threshold="not_required"`.
  - incomplete: `message="Summary evidence is incomplete."`, `observed_value=summary.status`, `threshold="summary_ready"`.
  - fail: `message="Summary evidence is unstable."`, `observed_value=summary.status`, `threshold="summary_ready"`.
- `quality_evidence`:
  - pass and required: `message="Quality evidence is ready."`, `observed_value=quality.status`, `threshold="proposal_review_quality_ready"`.
  - pass and optional: `message="Quality evidence is optional."`, `observed_value=quality.status`, `threshold="not_required"`.
  - incomplete: `message="Quality evidence is incomplete."`, `observed_value=quality.status`, `threshold="proposal_review_quality_ready"`.
  - fail: `message="Quality evidence is unstable."`, `observed_value=quality.status`, `threshold="proposal_review_quality_ready"`.
- `diagnostic_evidence`:
  - pass and required: `message="Diagnostic evidence is ready."`, `observed_value=diagnostics.status`, `threshold="diagnostics_ready"`.
  - pass and optional: `message="Diagnostic evidence is optional."`, `observed_value=diagnostics.status`, `threshold="not_required"`.
  - incomplete: `message="Diagnostic evidence is incomplete."`, `observed_value=diagnostics.status`, `threshold="diagnostics_ready"`.
  - fail: `message="Diagnostic evidence is unstable."`, `observed_value=diagnostics.status`, `threshold="diagnostics_ready"`.
- `coverage_evidence`:
  - pass and required: `message="Coverage evidence is ready."`, `observed_value=coverage.status`, `threshold="proposal_review_coverage_ready"`.
  - pass and optional: `message="Coverage evidence is optional."`, `observed_value=coverage.status`, `threshold="not_required"`.
  - incomplete: `message="Coverage evidence is incomplete."`, `observed_value=coverage.status`, `threshold="proposal_review_coverage_ready"`.
  - fail: `message="Coverage evidence is inconsistent."`, `observed_value=coverage.status`, `threshold="proposal_review_coverage_ready"`.

Finding rows:

- Emit one finding row per non-pass gate.
- `severity == "incomplete"` for incomplete gates.
- `severity == "inconsistent"` for `count_consistency` failures and `coverage_evidence` failures.
- `severity == "unstable"` for failed summary, quality, and diagnostic evidence gates.
- Finding rows are sorted by `(severity, source_report_name, finding_code)`.
- Exact finding-row mapping:
  - `count_consistency` fail: `finding_code="count_consistency_failed"`, `source_report_name="dossier"`, `message="Cross-report aggregate review counts are inconsistent."`.
  - `summary_evidence` incomplete: `finding_code="summary_evidence_incomplete"`, `source_report_name="summary"`, `message="Summary evidence is incomplete."`.
  - `summary_evidence` fail: `finding_code="summary_evidence_unstable"`, `source_report_name="summary"`, `message="Summary evidence is unstable."`.
  - `quality_evidence` incomplete: `finding_code="quality_evidence_incomplete"`, `source_report_name="quality"`, `message="Quality evidence is incomplete."`.
  - `quality_evidence` fail: `finding_code="quality_evidence_unstable"`, `source_report_name="quality"`, `message="Quality evidence is unstable."`.
  - `diagnostic_evidence` incomplete: `finding_code="diagnostic_evidence_incomplete"`, `source_report_name="diagnostics"`, `message="Diagnostic evidence is incomplete."`.
  - `diagnostic_evidence` fail: `finding_code="diagnostic_evidence_unstable"`, `source_report_name="diagnostics"`, `message="Diagnostic evidence is unstable."`.
  - `coverage_evidence` incomplete: `finding_code="coverage_evidence_incomplete"`, `source_report_name="coverage"`, `message="Coverage evidence is incomplete."`.
  - `coverage_evidence` fail: `finding_code="coverage_evidence_inconsistent"`, `source_report_name="coverage"`, `message="Coverage evidence is inconsistent."`.

Source rows:

- Emit one row each for `coverage`, `diagnostics`, `quality`, and `summary`.
- Source rows are sorted by `report_name`.
- Exact source-row field mapping:
  - `coverage`: `report_status=coverage.status`, `generated_at=coverage.generated_at`, `review_record_count=coverage.review_record_count`, `proposal_packet_count=coverage.proposal_packet_count`, `approved_decision_count=coverage.approved_decision_count`, `rejected_decision_count=coverage.rejected_decision_count`.
  - `diagnostics`: `report_status=diagnostics.status`, `generated_at=diagnostics.generated_at`, `review_record_count=diagnostics.review_record_count`, `proposal_packet_count=diagnostics.unique_source_proposal_count`, `approved_decision_count=diagnostics.approved_decision_count`, `rejected_decision_count=diagnostics.rejected_decision_count`.
  - `quality`: `report_status=quality.status`, `generated_at=quality.generated_at`, `review_record_count=quality.total_review_record_count`, `proposal_packet_count=quality.summed_unique_source_proposal_count`, `approved_decision_count=quality.approved_decision_count`, `rejected_decision_count=quality.rejected_decision_count`.
  - `summary`: `report_status=summary.status`, `generated_at=summary.generated_at`, `review_record_count=summary.review_record_count`, `proposal_packet_count=summary.unique_source_proposal_count`, `approved_decision_count=summary.approved_decision_count`, `rejected_decision_count=summary.rejected_decision_count`.
- `status_category` is one of `complete`, `incomplete`, `inconsistent`, or `unstable`.
- Status category mapping:
  - `summary_ready`, `proposal_review_quality_ready`, `diagnostics_ready`, and `proposal_review_coverage_ready` map to `complete`.
  - `insufficient_review_sample`, `incomplete_review_data`, `incomplete_proposal_sample`, and `incomplete_review_coverage` map to `incomplete`.
  - `inconsistent_review_coverage` maps to `inconsistent`.
  - `high_rejection_ratio`, `unstable_review_quality`, and `high_rejection_proxy` map to `unstable`.
  - Unknown statuses are hard validation failures during report cloning or source-row construction.

Validation helper requirements:

- `_expected_source_rows(summary, quality, diagnostics, coverage)` must build the exact four source rows above in `build_trade_proposal_review_dossier_report`.
- `TradeProposalReviewDossierReport.__post_init__` cannot reconstruct the complete quality and diagnostics source rows because it intentionally stores no raw source-report objects. It must validate `source_rows` structurally: exactly four rows named `coverage`, `diagnostics`, `quality`, and `summary`; no duplicates; sorted by `report_name`; each row status equals the corresponding `summary_status`, `quality_status`, `diagnostic_status`, or `coverage_status`; each row `generated_at` equals the corresponding top-level source generated-at field; each row `status_category` matches the source status mapping; the summary row review/approved/rejected counts match summary-derived top-level review/decision counts; the coverage row proposal count matches coverage-derived top-level proposal count; and every source row proposal/review/approved/rejected count matches the deterministic `count_consistency.observed_value` source-count evidence.
- `_expected_finding_rows(gate_results)` must build exactly one finding row for each non-pass gate, no finding rows for pass gates, sorted by `(severity, source_report_name, finding_code)`.
- Finding rows must copy `observed_value` and `threshold` from the corresponding non-pass gate result so the public finding evidence cannot drift from the public gate evidence.
- `TradeProposalReviewDossierReport.__post_init__` validates dossier-internal invariants only. It may validate that top-level summary-derived fields match the summary source row, top-level coverage-derived fields match the coverage source row, gate rows are ordered, source rows are structurally consistent with the report, finding rows match non-pass gates, and `status == _dossier_status(gate_results)`. It must not validate cross-report aggregate equality by raising; cross-report aggregate mismatches are represented as `count_consistency=fail` plus finding rows.
- `generated_at`, `summary_generated_at`, `quality_generated_at`, `diagnostic_generated_at`, `coverage_generated_at`, and every `TradeProposalReviewDossierSourceRow.generated_at` must be normalized with `_as_utc` before storage or comparison.
- `TradeProposalReviewDossierConfig.__post_init__` must call exact `_require_bool` validation for `require_summary_ready`, `require_quality_ready`, `require_diagnostics_ready`, and `require_coverage_ready`; values such as `1`, `"true"`, and `None` are invalid.
- Decimal policy follows summary/quality/diagnostics helpers: reject floats and bools, require finite `Decimal` values, require probability ratios to be between zero and one, serialize `Decimal` values as strings, and do not add coverage's extra four-decimal-place cap to dossier fields beyond what cloned source reports already enforce.

Boundary statement:

```python
DEFAULT_REVIEW_DOSSIER_BOUNDARY_STATEMENT = (
    "This is a report-only proposal-review dossier artifact, not an approval "
    "workflow, trade instruction, order instruction, broker request, order "
    "request, account action, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflow, manual "
    "execution import, strategy-promotion signal, settlement review, "
    "reconciliation process, compliance review, geographic access analysis, "
    "investment ranking, trade recommendation, or automatic order-placement "
    "authorization."
)
```

`_require_boundary_statement` must normalize by lowercasing and keeping only alphanumeric characters, then require the value to equal the normalized `DEFAULT_REVIEW_DOSSIER_BOUNDARY_STATEMENT`. This preserves punctuation/spacing flexibility while rejecting weakened or contradictory custom boundary text.

## File Structure

Create:

- `src/polymarket_alpha_lab/proposal_review_dossier.py`
- `tests/test_proposal_review_dossier.py`
- `tests/test_proposal_review_dossier_scope.py`
- Update this plan file: `docs/superpowers/plans/2026-06-15-level-2-proposal-review-dossier.md`

Modify:

- `src/polymarket_alpha_lab/__init__.py`
- `tests/test_init.py`
- Package-root scope allowlist tests:
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
- `README.md`

## Task 1: Functional Dossier Tests

**Files:**

- Create: `tests/test_proposal_review_dossier.py`

- [ ] **Step 1: Write failing tests for complete, incomplete, unstable, and inconsistent dossier states**

Use helper artifacts from existing proposal-review tests. The test file must import:

```python
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from tests.test_proposal_review_coverage import (
    approved_record,
    coverage_report,
    packet,
    rejected_record,
)
from polymarket_alpha_lab.proposal_review_diagnostics import (
    TradeProposalReviewDiagnosticConfig,
    TradeProposalReviewDiagnosticBucketRow,
    TradeProposalReviewDiagnosticReasonRow,
    build_trade_proposal_review_diagnostic_report,
)
from polymarket_alpha_lab.proposal_review_dossier import (
    TradeProposalReviewDossierConfig,
    TradeProposalReviewDossierFindingRow,
    TradeProposalReviewDossierGateResult,
    TradeProposalReviewDossierLog,
    TradeProposalReviewDossierReport,
    TradeProposalReviewDossierSourceRow,
    build_trade_proposal_review_dossier_report,
)
from polymarket_alpha_lab.proposal_review_quality import (
    TradeProposalReviewQualityConfig,
    TradeProposalReviewQualityGateResult,
    TradeProposalReviewQualityReasonTrend,
    build_trade_proposal_review_quality_report,
)
from polymarket_alpha_lab.proposal_review_summary import (
    TradeProposalReviewBucketSummary,
    TradeProposalReviewReasonCodeSummary,
    TradeProposalReviewSummaryConfig,
    build_trade_proposal_review_summary_report,
)
```

Define helpers:

```python
def dossier_inputs(records, proposals):
    summary = build_trade_proposal_review_summary_report(
        records,
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 12, tzinfo=UTC),
    )
    quality = build_trade_proposal_review_quality_report(
        [summary],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_overall_rejection_ratio=Decimal("1.0000"),
            max_worst_summary_rejection_ratio=Decimal("1.0000"),
            max_reason_code_rejection_share=Decimal("1.0000"),
            max_duplicate_source_proposal_ratio=Decimal("1.0000"),
            max_duplicate_source_proposal_count=10,
        ),
        generated_at=datetime(2026, 9, 8, 13, tzinfo=UTC),
    )
    diagnostics = build_trade_proposal_review_diagnostic_report(
        records,
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("1.0000"),
            max_rejected_source_proposal_ratio=Decimal("1.0000"),
            max_reason_code_rejected_decision_share=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 14, tzinfo=UTC),
    )
    coverage = coverage_report(
        proposals,
        records,
        generated_at=datetime(2026, 9, 8, 15, tzinfo=UTC),
    )
    return summary, quality, diagnostics, coverage


def dossier_report(summary, quality, diagnostics, coverage, **overrides):
    values = {
        "summary": summary,
        "quality": quality,
        "diagnostics": diagnostics,
        "coverage": coverage,
        "config": TradeProposalReviewDossierConfig(config_version="dossier-v1"),
        "generated_at": datetime(2026, 9, 8, 16, tzinfo=UTC),
    }
    values.update(overrides)
    return build_trade_proposal_review_dossier_report(**values)
```

Add complete-state test:

```python
def test_build_trade_proposal_review_dossier_report_combines_supplied_reports():
    source = packet(1)
    records = [approved_record(source, minute=1)]
    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])

    report = dossier_report(summary, quality, diagnostics, coverage)

    assert report.generated_at == datetime(2026, 9, 8, 16, tzinfo=UTC)
    assert report.config_version == "dossier-v1"
    assert report.report_only is True
    assert report.review_record_count == 1
    assert report.proposal_packet_count == 1
    assert report.reviewed_proposal_packet_count == 1
    assert report.unreviewed_proposal_packet_count == 0
    assert report.orphan_review_record_count == 0
    assert report.duplicate_reviewed_proposal_packet_count == 0
    assert report.conflicting_decision_proposal_packet_count == 0
    assert report.approved_decision_count == 1
    assert report.rejected_decision_count == 0
    assert report.review_coverage_ratio == Decimal("1.0000")
    assert report.rejection_ratio == Decimal("0.0000")
    assert report.summary_status == "summary_ready"
    assert report.quality_status == "proposal_review_quality_ready"
    assert report.diagnostic_status == "diagnostics_ready"
    assert report.coverage_status == "proposal_review_coverage_ready"
    assert report.status == "proposal_review_dossier_complete"
    assert tuple(row.gate_name for row in report.gate_results) == (
        "count_consistency",
        "summary_evidence",
        "quality_evidence",
        "diagnostic_evidence",
        "coverage_evidence",
    )
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.report_name for row in report.source_rows) == (
        "coverage",
        "diagnostics",
        "quality",
        "summary",
    )
    gates = {row.gate_name: row for row in report.gate_results}
    assert gates["count_consistency"].message == "Cross-report aggregate review counts are consistent."
    assert gates["count_consistency"].observed_value == (
        "summary=1/1/0; quality=1/1/0; diagnostics=1/1/0; coverage=1/1/0; "
        "proposal_counts=1/1/1/1; "
        "summary_generated_at=2026-09-08T12:00:00+00:00; "
        "quality_last_summary_generated_at=2026-09-08T12:00:00+00:00"
    )
    assert gates["count_consistency"].threshold == (
        "summary/diagnostics/coverage counts match; "
        "quality counts match latest summary or contain historical totals"
    )
    assert gates["summary_evidence"].message == "Summary evidence is ready."
    assert gates["summary_evidence"].observed_value == "summary_ready"
    assert gates["summary_evidence"].threshold == "summary_ready"
    assert gates["quality_evidence"].message == "Quality evidence is ready."
    assert gates["quality_evidence"].observed_value == "proposal_review_quality_ready"
    assert gates["quality_evidence"].threshold == "proposal_review_quality_ready"
    assert gates["diagnostic_evidence"].message == "Diagnostic evidence is ready."
    assert gates["diagnostic_evidence"].observed_value == "diagnostics_ready"
    assert gates["diagnostic_evidence"].threshold == "diagnostics_ready"
    assert gates["coverage_evidence"].message == "Coverage evidence is ready."
    assert gates["coverage_evidence"].observed_value == "proposal_review_coverage_ready"
    assert gates["coverage_evidence"].threshold == "proposal_review_coverage_ready"
    source_rows = {row.report_name: row for row in report.source_rows}
    assert source_rows["summary"] == TradeProposalReviewDossierSourceRow(
        report_name="summary",
        report_status="summary_ready",
        generated_at=summary.generated_at,
        review_record_count=summary.review_record_count,
        proposal_packet_count=summary.unique_source_proposal_count,
        approved_decision_count=summary.approved_decision_count,
        rejected_decision_count=summary.rejected_decision_count,
        status_category="complete",
    )
    assert source_rows["quality"] == TradeProposalReviewDossierSourceRow(
        report_name="quality",
        report_status="proposal_review_quality_ready",
        generated_at=quality.generated_at,
        review_record_count=quality.total_review_record_count,
        proposal_packet_count=quality.summed_unique_source_proposal_count,
        approved_decision_count=quality.approved_decision_count,
        rejected_decision_count=quality.rejected_decision_count,
        status_category="complete",
    )
    assert source_rows["diagnostics"] == TradeProposalReviewDossierSourceRow(
        report_name="diagnostics",
        report_status="diagnostics_ready",
        generated_at=diagnostics.generated_at,
        review_record_count=diagnostics.review_record_count,
        proposal_packet_count=diagnostics.unique_source_proposal_count,
        approved_decision_count=diagnostics.approved_decision_count,
        rejected_decision_count=diagnostics.rejected_decision_count,
        status_category="complete",
    )
    assert source_rows["coverage"] == TradeProposalReviewDossierSourceRow(
        report_name="coverage",
        report_status="proposal_review_coverage_ready",
        generated_at=coverage.generated_at,
        review_record_count=coverage.review_record_count,
        proposal_packet_count=coverage.proposal_packet_count,
        approved_decision_count=coverage.approved_decision_count,
        rejected_decision_count=coverage.rejected_decision_count,
        status_category="complete",
    )
    assert report.finding_rows == ()
```

Add state-precedence test:

```python
def test_trade_proposal_review_dossier_statuses_cover_incomplete_unstable_and_inconsistent_inputs():
    source = packet(2)
    records = [approved_record(source, minute=2)]
    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])

    empty_summary, empty_quality, empty_diagnostics, empty_coverage = dossier_inputs([], [])
    incomplete = dossier_report(
        empty_summary,
        empty_quality,
        empty_diagnostics,
        empty_coverage,
    )
    assert incomplete.status == "incomplete_review_dossier"
    assert any(row.status == "incomplete" for row in incomplete.gate_results)
    assert any(row.severity == "incomplete" for row in incomplete.finding_rows)

    rejected_source = packet(3)
    rejected_records = [rejected_record(rejected_source, minute=3)]
    unstable_summary = build_trade_proposal_review_summary_report(
        rejected_records,
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("0.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 17, tzinfo=UTC),
    )
    unstable_quality = build_trade_proposal_review_quality_report(
        [unstable_summary],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_overall_rejection_ratio=Decimal("1.0000"),
            max_worst_summary_rejection_ratio=Decimal("1.0000"),
            max_reason_code_rejection_share=Decimal("1.0000"),
            max_duplicate_source_proposal_ratio=Decimal("1.0000"),
            max_duplicate_source_proposal_count=10,
        ),
        generated_at=datetime(2026, 9, 8, 18, tzinfo=UTC),
    )
    unstable_diagnostics = build_trade_proposal_review_diagnostic_report(
        rejected_records,
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("1.0000"),
            max_rejected_source_proposal_ratio=Decimal("1.0000"),
            max_reason_code_rejected_decision_share=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 19, tzinfo=UTC),
    )
    unstable_coverage = coverage_report(
        [rejected_source],
        rejected_records,
        generated_at=datetime(2026, 9, 8, 20, tzinfo=UTC),
    )
    unstable = dossier_report(
        unstable_summary,
        unstable_quality,
        unstable_diagnostics,
        unstable_coverage,
    )
    assert unstable.status == "unstable_review_dossier"
    assert any(row.gate_name == "summary_evidence" and row.status == "fail" for row in unstable.gate_results)

    _, _, _, mismatched_coverage = dossier_inputs([], [])
    inconsistent = dossier_report(summary, quality, diagnostics, mismatched_coverage)
    assert inconsistent.status == "inconsistent_review_dossier"
    inconsistent_gate = next(row for row in inconsistent.gate_results if row.gate_name == "count_consistency")
    assert inconsistent_gate.status == "fail"
    assert inconsistent_gate.message == "Cross-report aggregate review counts are inconsistent."
    assert inconsistent.finding_rows == (
        TradeProposalReviewDossierFindingRow(
            finding_code="count_consistency_failed",
            severity="inconsistent",
            source_report_name="dossier",
            message="Cross-report aggregate review counts are inconsistent.",
            observed_value=inconsistent_gate.observed_value,
            threshold=inconsistent_gate.threshold,
        ),
    )
```

Add historical quality consistency test:

```python
def test_trade_proposal_review_dossier_accepts_historical_quality_when_latest_summary_is_covered():
    first_source = packet(9)
    second_source = packet(10)
    first_records = [approved_record(first_source, minute=9)]
    second_records = [approved_record(second_source, minute=10)]
    first_summary = build_trade_proposal_review_summary_report(
        first_records,
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 11, tzinfo=UTC),
    )
    latest_summary = build_trade_proposal_review_summary_report(
        second_records,
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 12, tzinfo=UTC),
    )
    latest_diagnostics = build_trade_proposal_review_diagnostic_report(
        second_records,
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("1.0000"),
            max_rejected_source_proposal_ratio=Decimal("1.0000"),
            max_reason_code_rejected_decision_share=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 14, tzinfo=UTC),
    )
    latest_coverage = coverage_report(
        [second_source],
        second_records,
        generated_at=datetime(2026, 9, 8, 15, tzinfo=UTC),
    )
    historical_quality = build_trade_proposal_review_quality_report(
        [first_summary, latest_summary],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_overall_rejection_ratio=Decimal("1.0000"),
            max_worst_summary_rejection_ratio=Decimal("1.0000"),
            max_reason_code_rejection_share=Decimal("1.0000"),
            max_duplicate_source_proposal_ratio=Decimal("1.0000"),
            max_duplicate_source_proposal_count=10,
        ),
        generated_at=datetime(2026, 9, 8, 21, tzinfo=UTC),
    )

    report = dossier_report(
        latest_summary,
        historical_quality,
        latest_diagnostics,
        latest_coverage,
    )

    assert report.status == "proposal_review_dossier_complete"
    assert report.review_record_count == latest_summary.review_record_count
    assert any(row.gate_name == "count_consistency" and row.status == "pass" for row in report.gate_results)

    stale_quality = replace(
        historical_quality,
        last_summary_generated_at=first_summary.generated_at,
    )
    stale = dossier_report(
        latest_summary,
        stale_quality,
        latest_diagnostics,
        latest_coverage,
    )
    assert stale.status == "inconsistent_review_dossier"
    assert any(row.gate_name == "count_consistency" and row.status == "fail" for row in stale.gate_results)

    rejected_older = build_trade_proposal_review_summary_report(
        [rejected_record(packet(11), minute=11)],
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 13, tzinfo=UTC),
    )
    rejected_latest = build_trade_proposal_review_summary_report(
        [rejected_record(packet(12), minute=12)],
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 14, tzinfo=UTC),
    )
    incompatible_quality = build_trade_proposal_review_quality_report(
        [rejected_older, rejected_latest],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_overall_rejection_ratio=Decimal("1.0000"),
            max_worst_summary_rejection_ratio=Decimal("1.0000"),
            max_reason_code_rejection_share=Decimal("1.0000"),
            max_duplicate_source_proposal_ratio=Decimal("1.0000"),
            max_duplicate_source_proposal_count=10,
        ),
        generated_at=datetime(2026, 9, 8, 22, tzinfo=UTC),
    )
    incompatible = dossier_report(
        latest_summary,
        incompatible_quality,
        latest_diagnostics,
        latest_coverage,
    )
    assert incompatible.status == "inconsistent_review_dossier"
    assert any(row.gate_name == "count_consistency" and row.status == "fail" for row in incompatible.gate_results)

    rejected_latest_summary = build_trade_proposal_review_summary_report(
        [rejected_record(packet(13), minute=13)],
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 23, tzinfo=UTC),
    )
    rejected_latest_diagnostics = build_trade_proposal_review_diagnostic_report(
        [rejected_record(packet(13), minute=13)],
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("1.0000"),
            max_rejected_source_proposal_ratio=Decimal("1.0000"),
            max_reason_code_rejected_decision_share=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 23, 10, tzinfo=UTC),
    )
    rejected_latest_coverage = coverage_report(
        [packet(13)],
        [rejected_record(packet(13), minute=13)],
        generated_at=datetime(2026, 9, 8, 23, 20, tzinfo=UTC),
    )
    approved_at_rejected_time_summary = build_trade_proposal_review_summary_report(
        [approved_record(packet(14), minute=14)],
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 23, tzinfo=UTC),
    )
    approved_before_rejected_summary = build_trade_proposal_review_summary_report(
        [approved_record(packet(15), minute=15)],
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 22, tzinfo=UTC),
    )
    approved_only_historical_quality = build_trade_proposal_review_quality_report(
        [approved_before_rejected_summary, approved_at_rejected_time_summary],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_overall_rejection_ratio=Decimal("1.0000"),
            max_worst_summary_rejection_ratio=Decimal("1.0000"),
            max_reason_code_rejection_share=Decimal("1.0000"),
            max_duplicate_source_proposal_ratio=Decimal("1.0000"),
            max_duplicate_source_proposal_count=10,
        ),
        generated_at=datetime(2026, 9, 8, 23, 30, tzinfo=UTC),
    )
    rejected_mismatch = dossier_report(
        rejected_latest_summary,
        approved_only_historical_quality,
        rejected_latest_diagnostics,
        rejected_latest_coverage,
    )
    assert rejected_mismatch.status == "inconsistent_review_dossier"
    assert any(row.gate_name == "count_consistency" and row.status == "fail" for row in rejected_mismatch.gate_results)
```

Add config override test:

```python
def test_trade_proposal_review_dossier_config_can_make_source_statuses_optional():
    empty_summary, empty_quality, empty_diagnostics, empty_coverage = dossier_inputs([], [])

    report = dossier_report(
        empty_summary,
        empty_quality,
        empty_diagnostics,
        empty_coverage,
        config=TradeProposalReviewDossierConfig(
            config_version="dossier-v1",
            require_summary_ready=False,
            require_quality_ready=False,
            require_diagnostics_ready=False,
            require_coverage_ready=False,
        ),
    )

    assert report.status == "proposal_review_dossier_complete"
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.message for row in report.gate_results[1:]) == (
        "Summary evidence is optional.",
        "Quality evidence is optional.",
        "Diagnostic evidence is optional.",
        "Coverage evidence is optional.",
    )
    assert tuple(row.threshold for row in report.gate_results[1:]) == (
        "not_required",
        "not_required",
        "not_required",
        "not_required",
    )
    assert tuple(row.status_category for row in report.source_rows) == (
        "incomplete",
        "incomplete",
        "incomplete",
        "incomplete",
    )
```

Add validation/log tests:

```python
def test_trade_proposal_review_dossier_rejects_bad_inputs_and_revalidates_mutated_reports():
    source = packet(5)
    records = [approved_record(source, minute=5)]
    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])

    with pytest.raises(ValueError, match="summary"):
        dossier_report(object(), quality, diagnostics, coverage)
    with pytest.raises(ValueError, match="quality"):
        dossier_report(summary, object(), diagnostics, coverage)
    with pytest.raises(ValueError, match="diagnostics"):
        dossier_report(summary, quality, object(), coverage)
    with pytest.raises(ValueError, match="coverage"):
        dossier_report(summary, quality, diagnostics, object())
    with pytest.raises(ValueError, match="config"):
        dossier_report(summary, quality, diagnostics, coverage, config=object())
    with pytest.raises(ValueError, match="generated_at"):
        dossier_report(summary, quality, diagnostics, coverage, generated_at="2026-09-08")

    object.__setattr__(coverage, "review_coverage_ratio", Decimal("NaN"))
    with pytest.raises(ValueError, match="finite|review_coverage_ratio"):
        dossier_report(summary, quality, diagnostics, coverage)

    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])
    object.__setattr__(coverage.gate_results[0], "status", "maybe")
    with pytest.raises(ValueError, match="status"):
        dossier_report(summary, quality, diagnostics, coverage)

    with pytest.raises(ValueError, match="require_summary_ready"):
        TradeProposalReviewDossierConfig(
            config_version="dossier-v1",
            require_summary_ready=1,
        )


def test_trade_proposal_review_dossier_dataclasses_are_frozen_and_validate_invariants():
    source = packet(6)
    records = [approved_record(source, minute=6)]
    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])
    report = dossier_report(summary, quality, diagnostics, coverage)
    config = TradeProposalReviewDossierConfig(config_version="dossier-v1")
    gate_row = report.gate_results[0]
    source_row = report.source_rows[0]

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(FrozenInstanceError):
        report.status = "other"
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(config, boundary_statement="dossier")
    with pytest.raises(ValueError, match="gate_name"):
        replace(gate_row, gate_name="approval")
    with pytest.raises(ValueError, match="source_rows"):
        replace(report, source_rows=tuple(reversed(report.source_rows)))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="incomplete_review_dossier")
    with pytest.raises(ValueError, match="report_name"):
        replace(source_row, report_name="approval")


def test_trade_proposal_review_dossier_log_appends_jsonl_report(tmp_path):
    source = packet(7)
    records = [approved_record(source, minute=7)]
    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])
    report = dossier_report(summary, quality, diagnostics, coverage)
    log = TradeProposalReviewDossierLog(path=tmp_path / "proposal-review-dossier.jsonl")

    log.append(report)

    stored = json.loads(log.path.read_text(encoding="utf-8").splitlines()[0])
    assert len(log.path.read_text(encoding="utf-8").splitlines()) == 1
    assert stored["generated_at"] == "2026-09-08T16:00:00+00:00"
    assert stored["report_only"] is True
    assert stored["status"] == "proposal_review_dossier_complete"
    assert stored["review_coverage_ratio"] == "1.0000"
    assert stored["gate_results"][0]["message"] == "Cross-report aggregate review counts are consistent."
    assert stored["gate_results"][0]["observed_value"] == (
        "summary=1/1/0; quality=1/1/0; diagnostics=1/1/0; coverage=1/1/0; "
        "proposal_counts=1/1/1/1; "
        "summary_generated_at=2026-09-08T12:00:00+00:00; "
        "quality_last_summary_generated_at=2026-09-08T12:00:00+00:00"
    )
    assert [row["report_name"] for row in stored["source_rows"]] == [
        "coverage",
        "diagnostics",
        "quality",
        "summary",
    ]


def test_trade_proposal_review_dossier_log_validates_before_open(tmp_path):
    source = packet(8)
    records = [approved_record(source, minute=8)]
    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])
    report = dossier_report(summary, quality, diagnostics, coverage)
    object.__setattr__(report, "review_coverage_ratio", Decimal("NaN"))
    log = TradeProposalReviewDossierLog(path=tmp_path / "proposal-review-dossier.jsonl")

    with pytest.raises(ValueError, match="finite|review_coverage_ratio"):
        log.append(report)

    assert not log.path.exists()
```

- [ ] **Step 2: Run functional tests and confirm RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_dossier.py -q
```

Expected before implementation: `ModuleNotFoundError: No module named 'polymarket_alpha_lab.proposal_review_dossier'`.

## Task 2: Scope And Export Tests

**Files:**

- Create: `tests/test_proposal_review_dossier_scope.py`
- Modify: `tests/test_init.py`
- Modify existing Level 2 scope allowlist tests listed above.

- [ ] **Step 1: Write failing scope and export tests**

`tests/test_proposal_review_dossier_scope.py` must parse `src/polymarket_alpha_lab/proposal_review_dossier.py` with `ast`.

Allowed imports:

```python
ALLOWED_IMPORT_PREFIXES = {
    "__future__",
    "json",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
    "polymarket_alpha_lab.proposal_review_summary",
    "polymarket_alpha_lab.proposal_review_quality",
    "polymarket_alpha_lab.proposal_review_diagnostics",
    "polymarket_alpha_lab.proposal_review_coverage",
}
```

Expected first-party imports:

```python
EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.proposal_review_summary": {
        "TradeProposalReviewBucketSummary",
        "TradeProposalReviewReasonCodeSummary",
        "TradeProposalReviewSummaryReport",
    },
    "polymarket_alpha_lab.proposal_review_quality": {
        "TradeProposalReviewQualityGateResult",
        "TradeProposalReviewQualityReasonTrend",
        "TradeProposalReviewQualityReport",
    },
    "polymarket_alpha_lab.proposal_review_diagnostics": {
        "TradeProposalReviewDiagnosticBucketRow",
        "TradeProposalReviewDiagnosticReasonRow",
        "TradeProposalReviewDiagnosticReport",
        "TradeProposalReviewDiagnosticSourceRow",
    },
    "polymarket_alpha_lab.proposal_review_coverage": {
        "TradeProposalReviewCoverageBucketRow",
        "TradeProposalReviewCoverageGateResult",
        "TradeProposalReviewCoveragePacketRow",
        "TradeProposalReviewCoverageReport",
    },
}
```

Expected exports:

```python
EXPECTED_PROPOSAL_REVIEW_DOSSIER_EXPORTS = {
    "TradeProposalReviewDossierConfig",
    "TradeProposalReviewDossierFindingRow",
    "TradeProposalReviewDossierGateResult",
    "TradeProposalReviewDossierLog",
    "TradeProposalReviewDossierReport",
    "TradeProposalReviewDossierSourceRow",
    "build_trade_proposal_review_dossier_report",
}
```

Forbidden import prefixes must include all direct data, account, network, trading, scraping, and loader surfaces:

```python
FORBIDDEN_IMPORT_PREFIXES = {
    "polymarket_alpha_lab.analytics",
    "polymarket_alpha_lab.analytics_history",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.forecast_evidence",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.manual_review_queue",
    "polymarket_alpha_lab.normalize",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.proposal_packet",
    "polymarket_alpha_lab.proposal_review",
    "polymarket_alpha_lab.rejections",
    "polymarket_alpha_lab.research",
    "polymarket_alpha_lab.risk",
    "polymarket_alpha_lab.scoring",
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
```

The forbidden-import matcher must use exact-module-or-dot-boundary matching, not raw string prefix matching:

```python
def module_matches_prefix(module_name, prefix):
    return module_name == prefix or module_name.startswith(f"{prefix}.")
```

This preserves the required allowed imports from `polymarket_alpha_lab.proposal_review_summary`, `polymarket_alpha_lab.proposal_review_quality`, `polymarket_alpha_lab.proposal_review_diagnostics`, and `polymarket_alpha_lab.proposal_review_coverage` while still forbidding the exact raw modules `polymarket_alpha_lab.proposal_review` and `polymarket_alpha_lab.proposal_packet`.

The scope test must normalize both tested examples and forbidden fragments before matching:

```python
FORBIDDEN_NAME_FRAGMENTS = {
    "accountaction",
    "accountauthentication",
    "accountclient",
    "apikey",
    "apitoken",
    "approvalat",
    "approvalby",
    "approvalgate",
    "approvalready",
    "approvalworkflow",
    "approvedat",
    "approvedby",
    "approvedpacketselector",
    "authenticationclient",
    "brokerclient",
    "brokerrequest",
    "brokersession",
    "browsersession",
    "clientsession",
    "cloudscraper",
    "compliancecheck",
    "compliancereview",
    "crawler",
    "credentialpath",
    "credentialworkflow",
    "executionclient",
    "executionreadiness",
    "fetchsummaryreport",
    "geographicanalysis",
    "geographicaccessanalysis",
    "geoanalysis",
    "goliveready",
    "identitydata",
    "investmentranking",
    "jurisdictioncheck",
    "latestdecisionselector",
    "legalreview",
    "liveexecution",
    "liveexecutionsignal",
    "orderclient",
    "orderinstruction",
    "orderplacement",
    "orderrequest",
    "privatekey",
    "privatekeypath",
    "playwrightbrowser",
    "profitable",
    "profitablestatus",
    "promotionready",
    "promotablestatus",
    "rankinvestments",
    "readjsonlhistory",
    "readyforlivetrading",
    "recommendtrade",
    "reconciliationprocess",
    "reconciliationstatus",
    "requestsession",
    "scrapingevidenceloader",
    "settlementreview",
    "strategypromotion",
    "strategypromotionsignal",
    "tradeinstruction",
    "traderecommendation",
    "transportclient",
    "walletsignature",
    "websocketclient",
    "websocketsession",
    "winningdecision",
}

FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS = {
    "account",
    "api",
    "approval",
    "authentication",
    "broker",
    "browser",
    "client",
    "compliance",
    "crawler",
    "credential",
    "execution",
    "geo",
    "jurisdiction",
    "legal",
    "privatekey",
    "profit",
    "promotion",
    "ranking",
    "recommendation",
    "reconciliation",
    "scraping",
    "settlement",
    "wallet",
    "websocket",
}

def normalize_identifier(value):
    return "".join(character for character in value.lower() if character.isalnum())


def forbidden_fragment_matches(example):
    normalized = normalize_identifier(example)
    return any(
        normalize_identifier(fragment) in normalized
        for fragment in FORBIDDEN_NAME_FRAGMENTS
    )
```

The scope test must include examples proving forbidden fragments catch:

```python
(
    "account_action",
    "account_authentication",
    "credential_path",
    "private_key_path",
    "api_token",
    "client_session",
    "order_client",
    "execution_client",
    "websocket_session",
    "broker_session",
    "request_session",
    "browser_session",
    "playwright_browser",
    "crawler",
    "scraping_evidence_loader",
    "fetch_summary_report",
    "read_jsonl_history",
    "approval_ready",
    "approval_gate",
    "approval_workflow",
    "approved_packet_selector",
    "latest_decision_selector",
    "winning_decision",
    "promotion_ready",
    "promotable_status",
    "profitable_status",
    "execution_readiness",
    "go_live_ready",
    "ready_for_live_trading",
    "trade_recommendation",
    "recommend_trade",
    "investment_ranking",
    "rank_investments",
    "settlement_review",
    "reconciliation_status",
    "compliance_review",
    "legal_review",
    "jurisdiction_check",
    "geo_analysis",
    "geographic_access_analysis",
)
```

The forbidden fragment list must avoid broad fragments that would block required audit fields. In particular, do not include bare `approved`, bare `approval`, bare `decision`, bare `proposal`, or bare `review` as `FORBIDDEN_NAME_FRAGMENTS`. Use narrower normalized fragments such as `approvalready`, `approvalgate`, `approvedpacketselector`, `latestdecisionselector`, `winningdecision`, `promotionready`, `executionreadiness`, and `goliveready`.

The forbidden-name AST scan must inspect identifiers only: module/class/function names, argument names, assigned variable names, attribute names, and imported alias names. It must not scan string literal contents. The required `DEFAULT_REVIEW_DOSSIER_BOUNDARY_STATEMENT` intentionally contains phrases such as `order instruction`, `broker request`, `settlement review`, `compliance review`, `geographic access analysis`, and `trade recommendation` as explicit exclusions, and those safety strings must not make the identifier-scope test fail.

Explicitly assert that required audit/count identifiers are allowed:

```python
for allowed in (
    "approved_decision_count",
    "rejected_decision_count",
    "proposal_review_dossier_complete",
):
    assert not forbidden_fragment_matches(allowed)
```

Also explicitly assert that all expected public exports are allowed by the public-export fragment guard:

```python
for export_name in EXPECTED_PROPOSAL_REVIEW_DOSSIER_EXPORTS:
    assert not public_export_fragment_matches(export_name)
```

The new scope test must include these tests:

- `test_forbidden_name_fragments_cover_level_2_node_7_scope_variants`
- `test_forbidden_name_fragments_allow_required_dossier_audit_identifiers`
- `test_proposal_review_dossier_module_imports_only_allowed_dependencies`
- `test_proposal_review_dossier_module_does_not_import_forbidden_surfaces`
- `test_proposal_review_dossier_module_uses_only_allowed_first_party_symbols`
- `test_proposal_review_dossier_module_does_not_define_forbidden_live_or_workflow_names`
- `test_trade_proposal_review_dossier_public_exports_are_report_only`
- `test_package_root_exports_do_not_leak_forbidden_level_2_node_7_surfaces`
- `test_readme_level_2_node_7_section_keeps_report_only_boundaries`

The README test must read `README.md`, require the `## Level 2 Node 7 Status` and `## Level 2 Node 7 Python API` headings, require normalized fragments for `reportonlyproposalreviewdossierartifacts`, `notanapprovalworkflowtradeinstructionorderinstructionbrokerrequestorderrequestaccountaction`, `strategypromotionsignal`, and `liveexecutionsignal`, and require normalized exclusions for `credentials`, `scrapewebsites`, `tradingsdk`, `brokerclient`, `executionclient`, `settlement`, `reconciliation`, `approvalworkflows`, `rankinvestments`, `recommendtrades`, and `compliancelegalgeographicanalysis`.

Add `tests/test_init.py::test_level_2_node_7_public_api_exports` asserting root package exports and identity bindings for all dossier names.

Add the dossier exports to every existing package-root artifact export allowlist so package root additions do not fail older scope tests:

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

- [ ] **Step 2: Run scope/export tests and confirm RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_dossier_scope.py tests/test_init.py \
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
  -q
```

Expected before implementation/export wiring: `ModuleNotFoundError` or missing file/export assertion failure.

## Task 3: Implement Dossier Module

**Files:**

- Create: `src/polymarket_alpha_lab/proposal_review_dossier.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`

- [ ] **Step 1: Implement minimal module and package root exports to satisfy Task 1 and Task 2**

Follow sibling modules:

- Use local helpers for `_as_utc`, `_json_ready`, `_normalize_log_path`, `_validate_log_parent`, `_normalize_typed_tuple`, `_normalize_string_tuple`, `_require_*`.
- Clone every supplied report by reconstructing its public dataclass tree. Do not retain caller-mutated nested objects.
  - Summary clone must reconstruct `TradeProposalReviewReasonCodeSummary`, `TradeProposalReviewBucketSummary`, and `TradeProposalReviewSummaryReport`.
  - Quality clone must reconstruct `TradeProposalReviewQualityGateResult`, `TradeProposalReviewQualityReasonTrend`, and `TradeProposalReviewQualityReport`.
  - Diagnostics clone must reconstruct `TradeProposalReviewDiagnosticReasonRow`, `TradeProposalReviewDiagnosticBucketRow`, `TradeProposalReviewDiagnosticSourceRow`, and `TradeProposalReviewDiagnosticReport`.
  - Coverage clone must reconstruct `TradeProposalReviewCoverageGateResult`, `TradeProposalReviewCoverageBucketRow`, `TradeProposalReviewCoveragePacketRow`, and `TradeProposalReviewCoverageReport`.
- `TradeProposalReviewDossierLog.append(report)` must call `_validate_report_tree(report)` and `json.dumps(..., allow_nan=False, sort_keys=True)` before opening or creating the file.
- Source rows are sorted by `report_name`.
- Finding rows are sorted by `(severity, source_report_name, finding_code)`.
- Gate rows are ordered exactly by `GATE_NAMES`.
- Report validates that status equals `_dossier_status(gate_results)`.
- `count_consistency.observed_value` is canonical and must contain exactly seven semicolon-separated segments in order: `summary=`, `quality=`, `diagnostics=`, `coverage=`, `proposal_counts=`, `summary_generated_at=`, and `quality_last_summary_generated_at=`. Report validation must reject extra or reordered evidence segments.
- Report validation must recompute whether `count_consistency` evidence supports pass/fail and reject mismatched gate status. Summary, quality, diagnostics, and coverage review decision triplets must match the evidence. Summary, quality, and diagnostics proposal counts must not exceed their review counts; coverage proposal count may exceed review count because unreviewed supplied proposals are represented there.
- Report top-level fields are derived from designated source reports: review decision counts and `rejection_ratio` come from `summary`; proposal coverage counts and `review_coverage_ratio` come from `coverage`; source statuses come from their corresponding report family. Cross-report mismatches must be represented by `count_consistency=fail` plus finding rows, not by constructor failure, unless a source report or dossier row is internally impossible.
- Report validates that finding rows match every non-pass gate.
- Implement `_expected_source_rows`, `_validate_source_rows_match_report`, `_expected_finding_rows`, `_validate_finding_rows_match_gate_results`, `_count_consistency_observed_value`, `_require_bool`, `_require_gate_value`, `_require_optional_probability_decimal`, and `_require_boundary_statement` according to the Status And Gate Rules section.
- Normalize all dossier and source-row datetimes through `_as_utc` before comparing or storing.
- Follow the summary/quality/diagnostics Decimal policy: no floats or bools in gate values, finite `Decimal` only, probability ratios between zero and one, and JSON serialization to strings.

Add root import block after `proposal_review_coverage`:

```python
from polymarket_alpha_lab.proposal_review_dossier import (
    TradeProposalReviewDossierConfig,
    TradeProposalReviewDossierFindingRow,
    TradeProposalReviewDossierGateResult,
    TradeProposalReviewDossierLog,
    TradeProposalReviewDossierReport,
    TradeProposalReviewDossierSourceRow,
    build_trade_proposal_review_dossier_report,
)
```

Add the same names to `__all__` in sorted style near other `TradeProposalReview...` entries.

- [ ] **Step 2: Run functional and scope tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_dossier.py tests/test_proposal_review_dossier_scope.py tests/test_init.py \
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
  -q
```

Expected after implementation: PASS.

## Task 4: Package Root And README

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Update README**

Add Level 2 Node 7 Status and Python API sections after Node 6:

```markdown
## Level 2 Node 7 Status

Level 2 Node 7 adds report-only proposal-review dossier artifacts over supplied `TradeProposalReviewSummaryReport`, `TradeProposalReviewQualityReport`, `TradeProposalReviewDiagnosticReport`, and `TradeProposalReviewCoverageReport` values. It assembles review evidence, gaps, gate rows, source rows, and finding rows for audit only; it is not an approval workflow, trade instruction, order instruction, broker request, order request, account action, strategy-promotion signal, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, execution client, or transport client; build broker or order request payloads; reconcile exchange accounts; review settlement; import manual executions; run approval workflows; select latest decisions; resolve conflicting reviews; rank investments; recommend trades; or perform compliance/legal/geographic analysis.

## Level 2 Node 7 Python API

Node 7 is exposed through Python APIs:

- Configure proposal-review dossiers with `TradeProposalReviewDossierConfig(config_version="dossier-v1")`.
- Build proposal-review dossier reports with `build_trade_proposal_review_dossier_report(summary=summary, quality=quality, diagnostics=diagnostics, coverage=coverage, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalReviewDossierReport`.
- Inspect dossier gates with `TradeProposalReviewDossierGateResult`, source rows with `TradeProposalReviewDossierSourceRow`, and finding rows with `TradeProposalReviewDossierFindingRow`.
- Persist proposal-review dossier snapshots with `TradeProposalReviewDossierLog(path).append(report)`.
```

Also update the Phase 1 Scope line, repository layout, tests layout, and plan list with the new dossier artifacts.

- [ ] **Step 2: Run package and README-sensitive tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py tests/test_proposal_review_dossier_scope.py -q
```

Expected: PASS.

## Task 5: Verification, opencode Implementation Review, Handoff, Commit

**Files:**

- Modify: `docs/superpowers/plans/2026-06-15-level-2-proposal-review-dossier.md`

- [ ] **Step 1: Run full verification**

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
- Git status: only intended Node 7 files modified/untracked.

- [ ] **Step 2: opencode implementation review**

Run local opencode with model `zhipuai-coding-plan/glm-5.2` and variant `max`. Give it:

- this plan,
- `git status --short --branch --untracked-files=all`,
- tracked diff,
- full contents of untracked new files.

Ask for:

```text
Critical findings: <number>
Important findings: <number>
Minor findings: <number>
Findings:
- <severity> <file:line> <concrete issue and why it matters>
Verdict: Proceed | Proceed with fixes | Blocked
```

Accepted implementation-review terminal state: `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed` or `Verdict: Proceed with fixes`. Fix every Critical or Important finding and rerun review before commit.

- [ ] **Step 3: Append Handoff Summary**

Append actual evidence before commit:

```markdown
## Handoff Summary

- Node completed: Level 2 Node 7 proposal-review dossier.
- Commit: pending at handoff-write time; final assistant response must report the commit hash after commit.
- Pushed: pending at handoff-write time; final assistant response must report the push result after push.
- Repo status before commit: <git status output>
- Verification commands:
  - `.venv/bin/python -m pytest -q`: <pass/fail summary>
  - `git diff --check`: <pass/fail summary>
  - `codegraph sync`: <pass/fail summary>
  - `codegraph status .`: <up-to-date/stale summary>
  - opencode implementation review: <Critical/Important/Minor counts and verdict>
- Files changed:
  - `src/polymarket_alpha_lab/proposal_review_dossier.py`
  - `src/polymarket_alpha_lab/__init__.py`
  - `tests/test_proposal_review_dossier.py`
  - `tests/test_proposal_review_dossier_scope.py`
  - `tests/test_init.py`
  - scope allowlist tests
  - `README.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-review-dossier.md`
- Uncommitted files after push: pending at handoff-write time; final assistant response must report post-push status.
- Next safe step: offline backtest evidence can consume dossier reports as supplied inputs, but it must remain report-only and require a new plan plus opencode review before implementation.
```

- [ ] **Step 4: Run post-handoff mini-gate**

Run this after appending the handoff summary and before staging files:

```bash
git diff --check
git status --short --branch --untracked-files=all
```

Expected:

- `git diff --check`: exit 0.
- Git status: only intended Node 7 files modified/untracked.

- [ ] **Step 5: Commit and push**

Run:

```bash
git add src/polymarket_alpha_lab/proposal_review_dossier.py \
  src/polymarket_alpha_lab/__init__.py \
  tests/test_proposal_review_dossier.py \
  tests/test_proposal_review_dossier_scope.py \
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
  AGENTS.md \
  README.md \
  docs/superpowers/plans/2026-06-15-level-2-proposal-review-dossier.md \
  docs/superpowers/plans/2026-06-15-level-2-proposal-review-dossier-batch-health.md
git commit -m "feat: add proposal review dossier reports"
git push origin main
git status --short --branch --untracked-files=all
```

Expected: push succeeds and final status is clean against `origin/main`.

## Self-Review

- Spec coverage: The plan advances the automated investment project by adding an audit-only dossier layer over the existing Level 2 review artifacts. It does not implement approval, execution, trade recommendation, investment ranking, scraping, credentials, settlement, reconciliation, or compliance analysis.
- Placeholder scan: No implementation task uses TBD/TODO language. Required public API, status rules, gates, input contracts, scope tests, verification commands, opencode review policy, and handoff fields are specified.
- Type consistency: The same names are used throughout: `TradeProposalReviewDossierConfig`, `TradeProposalReviewDossierGateResult`, `TradeProposalReviewDossierSourceRow`, `TradeProposalReviewDossierFindingRow`, `TradeProposalReviewDossierReport`, `TradeProposalReviewDossierLog`, and `build_trade_proposal_review_dossier_report`.

## Handoff Summary

- Node completed: Level 2 Node 7 proposal-review dossier.
- Commit: pending at handoff-write time; final assistant response must report the commit hash after commit.
- Pushed: pending at handoff-write time; final assistant response must report the push result after push.
- Repo status before commit: `main...origin/main` with modified `AGENTS.md`, `README.md`, package exports, `tests/test_init.py`, and Level 2 scope allowlist tests; untracked Node 7 plan/source/tests plus the Node 8 batch-health plan.
- Verification commands:
  - `.venv/bin/python -m pytest tests/test_proposal_review_dossier.py tests/test_proposal_review_dossier_scope.py tests/test_init.py -q`: 35 passed.
  - `.venv/bin/python -m pytest tests/test_*_scope.py tests/test_init.py -q`: 83 passed.
  - `.venv/bin/python -m pytest -q`: 575 passed.
  - `git diff --check`: exit 0.
  - `codegraph sync`: already up to date.
  - `codegraph status .`: index up to date.
  - opencode next-plan review (`zhipuai-coding-plan/glm-5.2`, variant `max`): Critical findings 0, Important findings 0, Minor findings 2, Verdict Proceed.
  - opencode implementation review (`zhipuai-coding-plan/glm-5.2`, variant `max`): Critical findings 0, Important findings 0, Minor findings 0, Verdict Proceed.
- Files changed:
  - `AGENTS.md`
  - `README.md`
  - `src/polymarket_alpha_lab/proposal_review_dossier.py`
  - `src/polymarket_alpha_lab/__init__.py`
  - `tests/test_proposal_review_dossier.py`
  - `tests/test_proposal_review_dossier_scope.py`
  - `tests/test_init.py`
  - Level 2 scope allowlist tests.
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-review-dossier.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-review-dossier-batch-health.md`
- Uncommitted files after push: pending at handoff-write time; final assistant response must report post-push status.
- Next safe step: implement the Level 2 Node 8 proposal-review dossier batch-health plan as supplied-input, report-only work, with local opencode review before committing.
