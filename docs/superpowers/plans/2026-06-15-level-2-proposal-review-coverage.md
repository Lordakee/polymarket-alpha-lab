# Level 2 Proposal Review Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Level 2 Node 6 proposal-review coverage reports that compare supplied proposal packets against supplied human-review records, without adding approval routing, manual-execution import, live execution, or credential surfaces.

**Architecture:** Add a pure report-only module, `proposal_review_coverage.py`, over caller-supplied `TradeProposalPacket` and `TradeProposalReviewRecord` values. It reconstructs every supplied packet and record to validate integrity, computes deterministic coverage, duplicate-review, conflict, orphan-review, gate, bucket, and packet rows, emits frozen report dataclasses, and optionally appends report snapshots to JSONL. The module has no readers, loaders, approval routers, latest-decision selectors, broker clients, account state, credentials, browser automation, order payloads, manual-execution imports, execution lifecycle, live-order behavior, realized-outcome matching, settlement, reconciliation, or compliance analysis.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, UTC `datetime`, JSONL, pytest, CodeGraph, Claude Code reviews with `claude-opus-4-8` and effort `max`.

---

## Review And Execution Protocol

1. Submit this plan to Claude Code with model `claude-opus-4-8`, effort `max`, and read-only permissions before implementation.
2. Do not implement until Claude returns `Proceed` or `Proceed with fixes` with zero Critical findings and zero Important findings.
3. Use TDD for implementation:
   - Write focused failing tests first.
   - Run the focused test and capture the expected failure.
   - Implement the minimum code.
   - Rerun the focused test and capture the pass.
4. Use parallel agents only with non-overlapping write ownership:
   - Functional-test worker owns `tests/test_proposal_review_coverage.py`.
   - Scope/export-test worker owns `tests/test_proposal_review_coverage_scope.py`, `tests/test_init.py`, and root-export allowlists in existing scope tests.
   - Main integrator owns `src/polymarket_alpha_lab/proposal_review_coverage.py`, `src/polymarket_alpha_lab/__init__.py`, `README.md`, and this plan.
   - Codex subagents use model `gpt-5.5` with reasoning effort `xhigh`.
5. Do not let two agents edit the same file or same tightly coupled file batch at the same time.
6. Close completed subagents promptly, then redeploy only to a fresh independent task.
7. Before commit, run fresh local verification and a self-contained Claude implementation review covering all modified and untracked files.
8. Resolve every Critical or Important implementation-review finding before staging for final commit.
9. Append a Handoff Summary to this plan before final commit.
10. Commit and push only after all gates pass.
11. Pause after this node is committed and pushed.

## Plan Review Command Before Any Implementation

Run this exact self-contained command before implementation:

```bash
{
  printf '%s\n' 'Review this Level 2 proposal-review-coverage implementation plan for polymarket-alpha-lab before implementation.'
  printf '%s\n' 'This is a read-only, self-contained plan review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, roadmap/spec material, validation gates, existing tests, or plan text.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; plan is implementable as written.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing required review material, unsafe scope, or plan ambiguity that could cause incorrect implementation.'
  printf '%s\n' 'Review specifically: Level 2 proposal-review coverage boundary, report-only semantics, supplied proposal packets as coverage denominator, supplied review records as observed review evidence, no realized false-positive confirmation, no latest-decision resolver, no approval workflow engine, no approval queue/router, no broker/request/client surfaces, no private-key handling, no automatic credential use, no account authentication, no unattended execution, no live order placement, no order lifecycle/reconciliation/settlement surfaces, no manual execution import, no scraping/browser automation, no compliance/legal/geographic analysis, supplied TradeProposalPacket validation, supplied TradeProposalReviewRecord validation, duplicate proposal_packet_id rejection, duplicate review_record_id rejection, orphan review record reporting without rejection, duplicate source review reporting without collapsing decisions, conflicting review decision reporting without selecting a winner, deterministic ordering, Decimal and UTC validation, JSONL validate-before-open behavior, public API/export surface, root-export scope-test migration, TDD steps, CodeGraph usage, verification gates, implementation-review self-containment, untracked-file handling, Handoff Summary, and commit/push order.'
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
  printf '%s\n' 'Relevant Level 2 roadmap and validation gate context:'
  sed -n '70,115p' docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md
  sed -n '97,152p' docs/research/validation-gates.md
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'CodeGraph status:'
  codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Current proposal packet and review record contracts:'
  codegraph node src/polymarket_alpha_lab/proposal_packet.py
  codegraph node src/polymarket_alpha_lab/proposal_review.py
  codegraph node tests/test_proposal_packet.py
  codegraph node tests/test_proposal_review.py
  printf '%s\n' ''
  printf '%s\n' 'Current sibling Level 2 report patterns:'
  codegraph node src/polymarket_alpha_lab/proposal_review_summary.py
  codegraph node tests/test_proposal_review_summary.py
  codegraph node src/polymarket_alpha_lab/proposal_review_quality.py
  codegraph node tests/test_proposal_review_quality.py
  codegraph node src/polymarket_alpha_lab/proposal_review_diagnostics.py
  codegraph node tests/test_proposal_review_diagnostics.py
  printf '%s\n' ''
  printf '%s\n' 'Current package root and export tests:'
  codegraph node src/polymarket_alpha_lab/__init__.py
  codegraph node tests/test_init.py
  printf '%s\n' ''
  printf '%s\n' 'Current root-export scope tests that must be migrated safely:'
  codegraph node tests/test_analytics_scope.py
  codegraph node tests/test_analytics_history_scope.py
  codegraph node tests/test_forecast_evidence_scope.py
  codegraph node tests/test_manual_review_queue_scope.py
  codegraph node tests/test_proposal_packet_scope.py
  codegraph node tests/test_proposal_review_scope.py
  codegraph node tests/test_proposal_review_summary_scope.py
  codegraph node tests/test_proposal_review_quality_scope.py
  codegraph node tests/test_proposal_review_diagnostics_scope.py
  printf '%s\n' ''
  printf '%s\n' 'Plan under review:'
  cat docs/superpowers/plans/2026-06-15-level-2-proposal-review-coverage.md
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted plan-review terminal state: a fresh Claude review response that explicitly reports `Critical findings: 0`, `Important findings: 0`, and a verdict of `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count line, ambiguous verdict, unsafe scope, missing repository instructions, missing Level 2 context, missing plan text, or transport failure is treated as `Blocked`. After fixing any Critical or Important plan-review finding, rerun the same self-contained Claude plan-review prompt and do not implement until the rerun reaches an accepted terminal state.

If the full prompt is blocked by transport size, rerun a compact prompt that still includes `AGENTS.md`, the Level 2 roadmap excerpt, Gate 6 through Gate 8 excerpts, fresh git status, the full `TradeProposalPacket` public contract, the full `TradeProposalReviewRecord` public contract, current package-root exports, current export tests, all root-export scope-test snippets, the full target plan text, and the same count/verdict policy.

## Level 2 Node 6 Scope

Level 2 Node 6 adds append-only proposal-review coverage reports over supplied `TradeProposalPacket` and `TradeProposalReviewRecord` values. A coverage report treats proposal packets as the review denominator and review records as observed review evidence. It answers which supplied proposal packets have review coverage, which remain unreviewed, which have duplicate reviews, which have conflicting review decisions, and which review records point to proposal packets absent from the supplied packet set.

The module must:

- Consume only caller-supplied `TradeProposalPacket` and `TradeProposalReviewRecord` values.
- Reconstruct every supplied proposal packet before coverage construction so mutated frozen objects or wrong types fail before report construction or log writes.
- Reconstruct every supplied review record before coverage construction so mutated frozen objects or wrong types fail before report construction or log writes.
- Cross-check every non-orphan review record against the supplied proposal packet with the same `source_proposal_packet_id`; the review record's `source_proposal_fingerprint` and source snapshot fields must match the supplied packet snapshot.
- Sort proposal packets deterministically by UTC `generated_at`, then `proposal_packet_id`.
- Sort review records deterministically by UTC `recorded_at`, then `review_record_id`.
- Reject duplicate `proposal_packet_id` values.
- Reject duplicate `review_record_id` values.
- Report orphan review records whose `source_proposal_packet_id` is absent from the supplied proposal packet set without rejecting the whole report.
- Track proposal packet count, review record count, reviewed proposal packet count, unreviewed proposal packet count, duplicate-reviewed proposal packet count, conflicting-decision proposal packet count, orphan review record count, approved decision count, rejected decision count, review coverage ratio, unreviewed proposal packet ratio, duplicate-reviewed proposal packet ratio, conflicting-decision proposal packet ratio, and orphan review record ratio.
- Track first and last proposal `generated_at` timestamps when proposal packets are present.
- Track first and last review `recorded_at` timestamps when review records are present.
- Emit one gate row for each gate name: `data_integrity`, `proposal_sample`, `review_coverage`, `duplicate_review_volume`, `decision_consistency`.
- Emit deterministic bucket rows by `bucket_name`: `reviewed`, `unreviewed`, `duplicate_reviewed`, `conflicting_decision`, and `orphan_review_record`.
- Emit deterministic packet rows for every supplied proposal packet and for every orphan `(source_proposal_packet_id, source_proposal_fingerprint)` group.
- Keep duplicate review tracking as a report-only signal; do not collapse duplicate records, choose the latest decision, or select a winning review decision.
- Keep conflicting decision tracking as a report-only signal; do not resolve conflicts or route proposals.
- Emit frozen report dataclasses.
- Persist report snapshots through `TradeProposalReviewCoverageLog(path).append(report)` using append-only JSONL.
- Serialize `Decimal` values as exact strings and datetimes as UTC ISO strings.
- Validate before opening or writing JSONL files.

The module must not:

- Confirm realized false positives, infer outcomes, import manual execution results, compare expected fills to fills, inspect realized slippage, reconcile positions, or read settlement data.
- Add an approval workflow engine, approval queue, approval router, approver registry, role-based permissions, reviewer authentication, identity verification, latest-decision resolver, finalization state machine, or strategy-promotion signal.
- Convert coverage into order instructions, order requests, broker requests, execution decisions, order lifecycle states, or strategy-promotion packets.
- Fetch market, order-book, price-history, outcome, account, credential, or identity data.
- Read JSONL logs or external history.
- Scrape websites, run browser automation, bypass anti-bot controls, or handle CAPTCHA.
- Authenticate, handle credentials, handle private keys, sign messages, use wallets, or use trading SDKs.
- Create broker clients, transport clients, request payloads, response objects, sessions, WebSockets, heartbeats, reconciliation, settlement, or account-state surfaces.
- Place, submit, sign, send, create, or cancel orders.
- Add CLI, UI, dashboard, scheduler, notification, compliance, legal, jurisdiction, geofence, KYC, AML, sanctions, or geographic-access analysis surfaces.

## Target File Structure

Create:

- `src/polymarket_alpha_lab/proposal_review_coverage.py`
- `tests/test_proposal_review_coverage.py`
- `tests/test_proposal_review_coverage_scope.py`
- `docs/superpowers/plans/2026-06-15-level-2-proposal-review-coverage.md`

Modify:

- `src/polymarket_alpha_lab/__init__.py`
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
- `README.md`

Do not modify:

- `src/polymarket_alpha_lab/api.py`
- `src/polymarket_alpha_lab/archive.py`
- `src/polymarket_alpha_lab/cli.py`
- `src/polymarket_alpha_lab/pipeline.py`
- `src/polymarket_alpha_lab/scoring.py`
- `src/polymarket_alpha_lab/research.py`
- `src/polymarket_alpha_lab/risk.py`
- `src/polymarket_alpha_lab/paper.py`
- `src/polymarket_alpha_lab/journal.py`
- `src/polymarket_alpha_lab/positions.py`
- `src/polymarket_alpha_lab/analytics.py`
- `src/polymarket_alpha_lab/analytics_history.py`
- `src/polymarket_alpha_lab/forecast_evidence.py`
- `src/polymarket_alpha_lab/manual_review_queue.py`
- `src/polymarket_alpha_lab/proposal_packet.py`
- `src/polymarket_alpha_lab/proposal_review.py`
- `src/polymarket_alpha_lab/proposal_review_summary.py`
- `src/polymarket_alpha_lab/proposal_review_quality.py`
- `src/polymarket_alpha_lab/proposal_review_diagnostics.py`

## Public API Contract

`src/polymarket_alpha_lab/proposal_review_coverage.py` must export exactly:

```python
__all__ = (
    "TradeProposalReviewCoverageBucketRow",
    "TradeProposalReviewCoverageConfig",
    "TradeProposalReviewCoverageGateResult",
    "TradeProposalReviewCoverageLog",
    "TradeProposalReviewCoveragePacketRow",
    "TradeProposalReviewCoverageReport",
    "build_trade_proposal_review_coverage_report",
)
```

### Boundary Statement

`DEFAULT_REVIEW_COVERAGE_BOUNDARY_STATEMENT` must be exactly:

```python
(
    "This is a report-only proposal-review coverage artifact, not an approval "
    "workflow, trade instruction, order instruction, broker request, order "
    "request, account action, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflow, manual "
    "execution import, strategy-promotion signal, or automatic order-placement "
    "authorization."
)
```

Boundary statement validation must require these lowercase substrings:

- `report-only`
- `proposal-review coverage`
- `not`
- `approval workflow`
- `trade instruction`
- `order instruction`
- `broker request`
- `order request`
- `account authentication`
- `private-key handling`
- `wallet signature`
- `live-execution signal`
- `credential workflow`
- `manual execution import`
- `strategy-promotion signal`
- `automatic order-placement authorization`

### Constants

```python
RATIO_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")

GATE_NAMES = (
    "data_integrity",
    "proposal_sample",
    "review_coverage",
    "duplicate_review_volume",
    "decision_consistency",
)
GATE_STATUSES = ("pass", "fail")
REPORT_STATUSES = (
    "incomplete_proposal_sample",
    "incomplete_review_coverage",
    "inconsistent_review_coverage",
    "proposal_review_coverage_ready",
)
COVERAGE_BUCKETS = (
    "reviewed",
    "unreviewed",
    "duplicate_reviewed",
    "conflicting_decision",
    "orphan_review_record",
)
```

### Dataclasses

Create exactly these frozen dataclasses.

```python
@dataclass(frozen=True)
class TradeProposalReviewCoverageConfig:
    config_version: str
    min_proposal_packet_count: int = 1
    min_review_coverage_ratio: Decimal = Decimal("1.0000")
    max_duplicate_reviewed_proposal_packet_ratio: Decimal = Decimal("1.0000")
    max_duplicate_reviewed_proposal_packet_count: int = 0
    max_conflicting_decision_proposal_packet_ratio: Decimal = Decimal("1.0000")
    max_conflicting_decision_proposal_packet_count: int = 0
    max_orphan_review_record_ratio: Decimal = Decimal("1.0000")
    max_orphan_review_record_count: int = 0
    boundary_statement: str = DEFAULT_REVIEW_COVERAGE_BOUNDARY_STATEMENT


@dataclass(frozen=True)
class TradeProposalReviewCoverageGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None


@dataclass(frozen=True)
class TradeProposalReviewCoverageBucketRow:
    bucket_name: str
    proposal_packet_count: int
    review_record_count: int
    coverage_ratio: Decimal | None


@dataclass(frozen=True)
class TradeProposalReviewCoveragePacketRow:
    coverage_status: str
    proposal_packet_id: str
    source_proposal_fingerprint: str | None
    first_proposal_generated_at: datetime | None
    last_proposal_generated_at: datetime | None
    first_recorded_at: datetime | None
    last_recorded_at: datetime | None
    review_record_count: int
    approved_decision_count: int
    rejected_decision_count: int
    market_slug: str | None
    strategy_type: str | None
    risk_tags: tuple[str, ...]
    review_record_ids: tuple[str, ...]


@dataclass(frozen=True)
class TradeProposalReviewCoverageReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    proposal_packet_count: int
    review_record_count: int
    reviewed_proposal_packet_count: int
    unreviewed_proposal_packet_count: int
    duplicate_reviewed_proposal_packet_count: int
    conflicting_decision_proposal_packet_count: int
    orphan_review_record_count: int
    approved_decision_count: int
    rejected_decision_count: int
    review_coverage_ratio: Decimal | None
    unreviewed_proposal_packet_ratio: Decimal | None
    duplicate_reviewed_proposal_packet_ratio: Decimal | None
    conflicting_decision_proposal_packet_ratio: Decimal | None
    orphan_review_record_ratio: Decimal | None
    first_proposal_generated_at: datetime | None
    last_proposal_generated_at: datetime | None
    first_recorded_at: datetime | None
    last_recorded_at: datetime | None
    status: str
    gate_results: tuple[TradeProposalReviewCoverageGateResult, ...]
    bucket_rows: tuple[TradeProposalReviewCoverageBucketRow, ...]
    packet_rows: tuple[TradeProposalReviewCoveragePacketRow, ...]


@dataclass(frozen=True)
class TradeProposalReviewCoverageLog:
    path: Path | str
```

### Builder Signature

```python
def build_trade_proposal_review_coverage_report(
    proposals: Iterable[TradeProposalPacket],
    records: Iterable[TradeProposalReviewRecord],
    *,
    config: TradeProposalReviewCoverageConfig,
    generated_at: datetime,
) -> TradeProposalReviewCoverageReport:
    ...
```

The builder must reject strings and bytes for both iterable inputs because they are technically iterable but not valid collections of artifacts.

### Ratio Definitions

All ratios are `Decimal` values quantized to `Decimal("0.0001")` with `ROUND_HALF_EVEN`. Proposal-denominator ratios are absent (`None`) when `proposal_packet_count == 0`. The orphan review record ratio is absent when `review_record_count == 0`.

| Field | Definition |
| --- | --- |
| `review_coverage_ratio` | `reviewed_proposal_packet_count / proposal_packet_count` |
| `unreviewed_proposal_packet_ratio` | `unreviewed_proposal_packet_count / proposal_packet_count` |
| `duplicate_reviewed_proposal_packet_ratio` | `duplicate_reviewed_proposal_packet_count / proposal_packet_count` |
| `conflicting_decision_proposal_packet_ratio` | `conflicting_decision_proposal_packet_count / proposal_packet_count` |
| `orphan_review_record_ratio` | `orphan_review_record_count / review_record_count` |

`review_record_count` is observed review evidence, not the arithmetic numerator for `review_coverage_ratio`. Duplicate review records can make `review_record_count` exceed `proposal_packet_count`; this must not make review coverage exceed `1.0000`.

`duplicate_reviewed_proposal_packet_count` counts every supplied proposal packet with more than one matched review record, including packets whose duplicate reviews have conflicting decisions. The `duplicate_reviewed` bucket row uses the same inclusive duplicate-review definition, so it can overlap with the `conflicting_decision` bucket. Packet rows remain mutually exclusive through their `coverage_status`.

Duplicate `proposal_packet_id` values, duplicate `review_record_id` values, and matched-record source-snapshot mismatches are hard validation failures before report construction. They are not gate failures and must not produce partial reports.

## TDD Tasks

### Task 1: Functional Coverage Tests

**Files:**

- Create: `tests/test_proposal_review_coverage.py`

- [ ] **Step 1: Write the failing functional tests**

Use helper imports from existing tests:

```python
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from tests.test_proposal_review_summary import proposal_for_source, review_record
from polymarket_alpha_lab.proposal_review_coverage import (
    TradeProposalReviewCoverageBucketRow,
    TradeProposalReviewCoverageConfig,
    TradeProposalReviewCoverageGateResult,
    TradeProposalReviewCoverageLog,
    TradeProposalReviewCoveragePacketRow,
    TradeProposalReviewCoverageReport,
    build_trade_proposal_review_coverage_report,
)
```

Add helpers:

```python
def packet(index, **overrides):
    values = {
        "market_slug": f"market-{index}",
    }
    values.update(overrides)
    return proposal_for_source(index, **values)


def coverage_report(proposals, records, **overrides):
    values = {
        "proposals": proposals,
        "records": records,
        "config": TradeProposalReviewCoverageConfig(
            config_version="coverage-v1",
            min_proposal_packet_count=1,
            min_review_coverage_ratio=Decimal("1.0000"),
            max_duplicate_reviewed_proposal_packet_count=10,
            max_conflicting_decision_proposal_packet_count=10,
            max_orphan_review_record_count=10,
            max_orphan_review_record_ratio=Decimal("0.0000"),
        ),
        "generated_at": datetime(2026, 9, 7, 9, tzinfo=timezone(timedelta(hours=-4))),
    }
    values.update(overrides)
    return build_trade_proposal_review_coverage_report(**values)


def approved_record(source, minute=0, reviewer_label="human-reviewer-1"):
    return review_record(
        proposal=source,
        decision="approved",
        review_reason_codes=(),
        reviewer_label=reviewer_label,
        recorded_at=datetime(2026, 9, 4, 12, minute, tzinfo=UTC),
    )


def rejected_record(source, minute=0, reviewer_label="human-reviewer-1"):
    return review_record(
        proposal=source,
        decision="rejected",
        review_reason_codes=("liquidity_exit_risk",),
        review_rationale="Rejected after checking coverage test evidence.",
        reviewer_label=reviewer_label,
        recorded_at=datetime(2026, 9, 4, 12, minute, tzinfo=UTC),
    )
```

Add these tests with exact expected behavior:

```python
def test_build_trade_proposal_review_coverage_report_counts_packet_denominator():
    reviewed = packet(1, market_slug="alpha-market")
    unreviewed = packet(2, market_slug="beta-market")
    duplicate = packet(3, market_slug="gamma-market")
    conflict = packet(4, market_slug="delta-market")
    orphan = packet(99, market_slug="orphan-market")
    records = [
        approved_record(reviewed, minute=1),
        approved_record(duplicate, minute=2, reviewer_label="human-reviewer-2"),
        rejected_record(duplicate, minute=3, reviewer_label="human-reviewer-3"),
        approved_record(conflict, minute=4, reviewer_label="human-reviewer-4"),
        rejected_record(conflict, minute=5, reviewer_label="human-reviewer-5"),
        rejected_record(orphan, minute=6, reviewer_label="human-reviewer-6"),
    ]

    report = coverage_report(
        [conflict, unreviewed, duplicate, reviewed],
        list(reversed(records)),
    )

    assert report.generated_at == datetime(2026, 9, 7, 13, tzinfo=UTC)
    assert report.config_version == "coverage-v1"
    assert report.report_only is True
    assert report.proposal_packet_count == 4
    assert report.review_record_count == 6
    assert report.reviewed_proposal_packet_count == 3
    assert report.unreviewed_proposal_packet_count == 1
    assert report.duplicate_reviewed_proposal_packet_count == 2
    assert report.conflicting_decision_proposal_packet_count == 2
    assert report.orphan_review_record_count == 1
    assert report.approved_decision_count == 3
    assert report.rejected_decision_count == 3
    assert report.review_coverage_ratio == Decimal("0.7500")
    assert report.unreviewed_proposal_packet_ratio == Decimal("0.2500")
    assert report.duplicate_reviewed_proposal_packet_ratio == Decimal("0.5000")
    assert report.conflicting_decision_proposal_packet_ratio == Decimal("0.5000")
    assert report.orphan_review_record_ratio == Decimal("0.1667")
    assert report.first_proposal_generated_at == datetime(2026, 9, 3, 12, 1, tzinfo=UTC)
    assert report.last_proposal_generated_at == datetime(2026, 9, 3, 12, 4, tzinfo=UTC)
    assert report.first_recorded_at == datetime(2026, 9, 4, 12, 1, tzinfo=UTC)
    assert report.last_recorded_at == datetime(2026, 9, 4, 12, 6, tzinfo=UTC)
    assert report.status == "incomplete_review_coverage"
    assert tuple(row.gate_name for row in report.gate_results) == (
        "data_integrity",
        "proposal_sample",
        "review_coverage",
        "duplicate_review_volume",
        "decision_consistency",
    )
    assert tuple(row.bucket_name for row in report.bucket_rows) == (
        "conflicting_decision",
        "duplicate_reviewed",
        "orphan_review_record",
        "reviewed",
        "unreviewed",
    )
    rows_by_id = {row.proposal_packet_id: row for row in report.packet_rows}
    assert rows_by_id[reviewed.proposal_packet_id].coverage_status == "reviewed"
    assert rows_by_id[unreviewed.proposal_packet_id].coverage_status == "unreviewed"
    assert rows_by_id[duplicate.proposal_packet_id].coverage_status == "conflicting"
    assert rows_by_id[conflict.proposal_packet_id].coverage_status == "conflicting"
    assert rows_by_id[orphan.proposal_packet_id].coverage_status == "orphan"
    assert rows_by_id[orphan.proposal_packet_id].source_proposal_fingerprint is not None
    assert rows_by_id[orphan.proposal_packet_id].market_slug == "orphan-market"
```

Also add tests for:

- `test_trade_proposal_review_coverage_statuses_cover_empty_sample_thresholds_and_ready_state`
  - empty proposal list with zero records returns `incomplete_proposal_sample`, all proposal ratios are `None`, and all rows are empty except gate rows.
  - one proposal and zero records returns `incomplete_review_coverage`.
  - all proposals reviewed but duplicate ratio above threshold returns `inconsistent_review_coverage`.
  - all proposals reviewed but conflict ratio above threshold returns `inconsistent_review_coverage`.
  - all proposals reviewed but orphan ratio above threshold returns `inconsistent_review_coverage`.
  - all proposals reviewed with relaxed duplicate/conflict/orphan thresholds returns `proposal_review_coverage_ready`.
- `test_trade_proposal_review_coverage_rows_are_deterministic`
  - pass proposals and records in reversed order and assert `bucket_rows` sort by `bucket_name`, `packet_rows` sort by `coverage_status`, `proposal_packet_id`, `source_proposal_fingerprint or ""`.
- `test_trade_proposal_review_coverage_groups_orphans_by_source_id_and_fingerprint`
  - create two orphan review records with the same `source_proposal_packet_id` but different `source_proposal_fingerprint` values by mutating one valid orphan record source snapshot and rebuilding a consistent `TradeProposalReviewRecord`.
  - the test helper must recompute both `source_proposal_fingerprint` and `review_record_id` using local test-only `hashlib.sha256` helpers that mirror `proposal_review.py`; do not import underscored production helpers.
  - assert the report emits two `coverage_status == "orphan"` packet rows for that shared source id, one per fingerprint, without selecting a winner.
  - assert `orphan_review_record_count` counts both review records and the orphan bucket `review_record_count` counts both records while `proposal_packet_count == 0`.
- `test_trade_proposal_review_coverage_rejects_invalid_inputs`
  - wrong config type, wrong generated_at type, string proposal iterable, bytes review iterable, wrong packet item type, wrong record item type, duplicate proposal IDs, duplicate record IDs.
- `test_trade_proposal_review_coverage_revalidates_mutated_artifacts`
  - use `object.__setattr__` to mutate `proposal_only=False` and expect `ValueError`.
  - use `object.__setattr__` to mutate `review_record_id="bad-id"` and expect `ValueError`.
- `test_trade_proposal_review_coverage_rejects_matching_ids_with_stale_source_fingerprint`
  - build a proposal packet and review record from it.
  - use `object.__setattr__` to mutate a supplied packet source field that is part of review-source fingerprinting, such as `market_slug`, while leaving `proposal_packet_id` unchanged.
  - pass that mutated packet with the original review record and expect `ValueError` mentioning `source_proposal_fingerprint` or `source proposal`.
- `test_trade_proposal_review_coverage_dataclasses_are_frozen_and_validate_invariants`
  - mutate a report and expect `FrozenInstanceError`.
  - instantiate invalid gate, bucket, packet, and report rows and expect `ValueError`.
- `test_trade_proposal_review_coverage_boundary_statement_contract`
  - assert the default boundary statement is exact and config rejects a statement missing required substrings.
- `test_trade_proposal_review_coverage_log_appends_jsonl`
  - append a report, load one JSONL line, assert Decimal values are strings and datetimes are UTC ISO strings.
- `test_trade_proposal_review_coverage_log_appends_without_overwriting_and_creates_parent_dirs`
  - append twice and assert two lines exist.
- `test_trade_proposal_review_coverage_log_validates_before_opening_file`
  - create an existing file, try appending wrong type and a report mutated with non-finite Decimal via `object.__setattr__`, assert file content unchanged.

- [ ] **Step 2: Run the new test file and verify the expected import failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_coverage.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'polymarket_alpha_lab.proposal_review_coverage'`.

### Task 2: Scope And Export Tests

**Files:**

- Create: `tests/test_proposal_review_coverage_scope.py`
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

- [ ] **Step 1: Write the failing scope/export tests**

Create `tests/test_proposal_review_coverage_scope.py` by mirroring `tests/test_proposal_review_diagnostics_scope.py` with these changes:

```python
PROPOSAL_REVIEW_COVERAGE_PATH = (
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "proposal_review_coverage.py"
)

EXPECTED_PROPOSAL_REVIEW_COVERAGE_EXPORTS = {
    "TradeProposalReviewCoverageBucketRow",
    "TradeProposalReviewCoverageConfig",
    "TradeProposalReviewCoverageGateResult",
    "TradeProposalReviewCoverageLog",
    "TradeProposalReviewCoveragePacketRow",
    "TradeProposalReviewCoverageReport",
    "build_trade_proposal_review_coverage_report",
}

ALLOWED_IMPORT_PREFIXES = {
    "__future__",
    "hashlib",
    "json",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
    "polymarket_alpha_lab.proposal_packet",
    "polymarket_alpha_lab.proposal_review",
}

EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.proposal_packet": {"TradeProposalPacket"},
    "polymarket_alpha_lab.proposal_review": {"TradeProposalReviewRecord"},
}
```

In the new coverage scope test, the package-root allowlist must include:

```python
EXPECTED_LEVEL_2_ARTIFACT_EXPORTS = (
    EXPECTED_LEVEL_2_PROPOSAL_PACKET_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_SUMMARY_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_QUALITY_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_DIAGNOSTIC_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_COVERAGE_EXPORTS
)
```

The new scope test must include forbidden import prefixes and forbidden name fragments from `tests/test_proposal_review_diagnostics_scope.py`. It must reject forbidden names containing execution, broker, account, credential, settlement, reconciliation, manual execution, scraping, dashboard, compliance, legal, and geographic fragments. It must allow `proposal`, `tradeproposal`, `review`, `coverage`, `packet`, `record`, `approved_decision_count`, and `rejected_decision_count`.

Modify `tests/test_init.py` imports to include:

```python
from polymarket_alpha_lab.proposal_review_coverage import (
    TradeProposalReviewCoverageBucketRow,
    TradeProposalReviewCoverageConfig,
    TradeProposalReviewCoverageGateResult,
    TradeProposalReviewCoverageLog,
    TradeProposalReviewCoveragePacketRow,
    TradeProposalReviewCoverageReport,
    build_trade_proposal_review_coverage_report,
)
```

Add:

```python
def test_level_2_node_6_public_api_exports():
    expected_exports = {
        "TradeProposalReviewCoverageBucketRow",
        "TradeProposalReviewCoverageConfig",
        "TradeProposalReviewCoverageGateResult",
        "TradeProposalReviewCoverageLog",
        "TradeProposalReviewCoveragePacketRow",
        "TradeProposalReviewCoverageReport",
        "build_trade_proposal_review_coverage_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.TradeProposalReviewCoverageBucketRow is TradeProposalReviewCoverageBucketRow
    assert lab.TradeProposalReviewCoverageConfig is TradeProposalReviewCoverageConfig
    assert lab.TradeProposalReviewCoverageGateResult is TradeProposalReviewCoverageGateResult
    assert lab.TradeProposalReviewCoverageLog is TradeProposalReviewCoverageLog
    assert lab.TradeProposalReviewCoveragePacketRow is TradeProposalReviewCoveragePacketRow
    assert lab.TradeProposalReviewCoverageReport is TradeProposalReviewCoverageReport
    assert (
        lab.build_trade_proposal_review_coverage_report
        is build_trade_proposal_review_coverage_report
    )
```

In every existing scope test that defines `EXPECTED_LEVEL_2_ARTIFACT_EXPORTS`, add `EXPECTED_PROPOSAL_REVIEW_COVERAGE_EXPORTS` and union it into `EXPECTED_LEVEL_2_ARTIFACT_EXPORTS`. These files are:

- `tests/test_analytics_scope.py`
- `tests/test_analytics_history_scope.py`
- `tests/test_forecast_evidence_scope.py`
- `tests/test_manual_review_queue_scope.py`
- `tests/test_proposal_packet_scope.py`
- `tests/test_proposal_review_scope.py`
- `tests/test_proposal_review_summary_scope.py`
- `tests/test_proposal_review_quality_scope.py`
- `tests/test_proposal_review_diagnostics_scope.py`

- [ ] **Step 2: Run the focused scope/export tests and verify the expected failures**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_coverage_scope.py tests/test_init.py -q
```

Expected: FAIL because `proposal_review_coverage.py` and root exports do not exist yet.

### Task 3: Implement Coverage Module

**Files:**

- Create: `src/polymarket_alpha_lab/proposal_review_coverage.py`

- [ ] **Step 1: Implement the module to satisfy Task 1 and Task 2 tests**

Follow sibling module style from `proposal_review_diagnostics.py`:

- use CodeGraph before any additional source exploration beyond the material already included in this plan.
- imports: `hashlib`, `json`, `Iterable`, `asdict`, `dataclass`, `fields`, `UTC`, `datetime`, `ROUND_HALF_EVEN`, `Decimal`, `Path`, `Any`, `TradeProposalPacket`, `TradeProposalReviewRecord`.
- use `allow_nan=False`, `sort_keys=True`, append mode, UTF-8.
- define `_json_ready`, `_validate_report_tree`, `_normalize_log_path`, `_validate_log_parent`, `_require_*` helpers locally.
- clone packets by reconstructing `TradeProposalPacket(...)` from every public field.
- clone records by reconstructing `TradeProposalReviewRecord(...)` from every public field.
- implement `_source_fields_from_proposal(packet)` and `_source_proposal_fingerprint(packet)` locally by mirroring the public source snapshot fields in `proposal_review.py`; use them only to validate that a matched review record was created from the same supplied proposal snapshot.
- for each matched non-orphan record, directly compare every reconstructed source snapshot field from `_source_fields_from_proposal(packet)` with the corresponding `TradeProposalReviewRecord` source field, then compare `record.source_proposal_fingerprint` with `_source_proposal_fingerprint(packet)`.
- calculate ratios with:

```python
def _ratio_from_counts(numerator: int, denominator: int) -> Decimal:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )
```

Coverage status rules for packet rows:

- supplied proposal packet with zero matching records: `unreviewed`
- supplied proposal packet with exactly one matching record: `reviewed`
- supplied proposal packet with more than one matching record and one decision value: `duplicate_reviewed`
- supplied proposal packet with more than one matching record and both approved/rejected decisions: `conflicting`
- absent proposal packet referenced by one or more review records: `orphan`

Report status rules:

```python
if proposal_packet_count == 0:
    status = "incomplete_proposal_sample"
elif any(row.gate_name == "review_coverage" and row.status == "fail" for row in gate_results):
    status = "incomplete_review_coverage"
elif any(row.status == "fail" for row in gate_results):
    status = "inconsistent_review_coverage"
else:
    status = "proposal_review_coverage_ready"
```

Gate rules:

- `data_integrity`: fail when orphan review record ratio exceeds `max_orphan_review_record_ratio` or orphan review record count exceeds `max_orphan_review_record_count`, otherwise pass.
- `proposal_sample`: fail when `proposal_packet_count < min_proposal_packet_count`, otherwise pass.
- `review_coverage`: fail when proposal packets exist and `review_coverage_ratio < min_review_coverage_ratio`; fail when proposal packets are absent; otherwise pass.
- `duplicate_review_volume`: fail when duplicate-reviewed proposal packet ratio exceeds `max_duplicate_reviewed_proposal_packet_ratio` or duplicate-reviewed proposal packet count exceeds `max_duplicate_reviewed_proposal_packet_count`, otherwise pass.
- `decision_consistency`: fail when conflicting-decision proposal packet ratio exceeds `max_conflicting_decision_proposal_packet_ratio` or conflicting-decision proposal packet count exceeds `max_conflicting_decision_proposal_packet_count`, otherwise pass.

Bucket row counts:

- `reviewed`: packet rows with `coverage_status == "reviewed"`
- `unreviewed`: packet rows with `coverage_status == "unreviewed"`
- `duplicate_reviewed`: supplied proposal packet rows with more than one matched review record, including conflicting rows; this bucket uses the inclusive duplicate-review definition and can overlap with `conflicting_decision`.
- `conflicting_decision`: packet rows with `coverage_status == "conflicting"`
- `orphan_review_record`: orphan review records whose `source_proposal_packet_id` is absent from the supplied packet set. Orphan packet rows are grouped by `(source_proposal_packet_id, source_proposal_fingerprint)`, not only by `source_proposal_packet_id`, because no supplied proposal packet exists to act as the canonical source snapshot. For this bucket, `proposal_packet_count` must be `0` because orphan records are not supplied proposal packets; `review_record_count` describes the orphan review records.

Packet rows must be sorted by `(coverage_status, proposal_packet_id, source_proposal_fingerprint or "")`. Bucket rows must be sorted by `bucket_name`.

- [ ] **Step 2: Run functional and scope tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_coverage.py tests/test_proposal_review_coverage_scope.py -q
```

Expected: PASS after implementation.

### Task 4: Package Root Exports

**Files:**

- Modify: `src/polymarket_alpha_lab/__init__.py`

- [ ] **Step 1: Add coverage exports to package root**

Add a new import block after `proposal_review_diagnostics`:

```python
from polymarket_alpha_lab.proposal_review_coverage import (
    TradeProposalReviewCoverageBucketRow,
    TradeProposalReviewCoverageConfig,
    TradeProposalReviewCoverageGateResult,
    TradeProposalReviewCoverageLog,
    TradeProposalReviewCoveragePacketRow,
    TradeProposalReviewCoverageReport,
    build_trade_proposal_review_coverage_report,
)
```

Add the same names to `__all__` near the other Level 2 review artifacts, keeping the existing alphabetical-ish grouping:

```python
"TradeProposalReviewCoverageBucketRow",
"TradeProposalReviewCoverageConfig",
"TradeProposalReviewCoverageGateResult",
"TradeProposalReviewCoverageLog",
"TradeProposalReviewCoveragePacketRow",
"TradeProposalReviewCoverageReport",
"build_trade_proposal_review_coverage_report",
```

- [ ] **Step 2: Run export tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py tests/test_*_scope.py -q
```

Expected: PASS.

### Task 5: README Documentation

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Update Phase 1 scope sentence**

Add `proposal-review coverage report artifacts` after `proposal-review diagnostic artifacts`.

- [ ] **Step 2: Add Level 2 Node 6 Status and API sections after Level 2 Node 5**

Add:

```markdown
## Level 2 Node 6 Status

Level 2 Node 6 adds report-only proposal-review coverage artifacts over supplied `TradeProposalPacket` and `TradeProposalReviewRecord` values. It treats proposal packets as the review denominator and review records as observed review evidence, reporting reviewed, unreviewed, duplicate-reviewed, conflicting-decision, and orphan-review coverage without selecting a winning decision or routing proposals.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, execution client, or transport client; build broker or order request payloads; reconcile exchange accounts; review settlement; import manual executions; run approval workflows; select latest decisions; or perform compliance/legal/geographic analysis.

## Level 2 Node 6 Python API

Node 6 is exposed through Python APIs:

- Configure proposal-review coverage with `TradeProposalReviewCoverageConfig(config_version="coverage-v1")`.
- Build proposal-review coverage reports with `build_trade_proposal_review_coverage_report(proposals, records, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalReviewCoverageReport`.
- Inspect coverage gates with `TradeProposalReviewCoverageGateResult`, bucket rows with `TradeProposalReviewCoverageBucketRow`, and packet rows with `TradeProposalReviewCoveragePacketRow`.
- Persist proposal-review coverage snapshots with `TradeProposalReviewCoverageLog(path).append(report)`.
```

- [ ] **Step 3: Update repository layout**

Add these entries:

- `docs/superpowers/plans/2026-06-15-level-2-proposal-review-coverage.md`
- `src/polymarket_alpha_lab/proposal_review_coverage.py`
- `tests/test_proposal_review_coverage.py`
- `tests/test_proposal_review_coverage_scope.py`

- [ ] **Step 4: Run docs-adjacent tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py -q
```

Expected: PASS.

### Task 6: Verification, Claude Implementation Review, Handoff, Commit, Push

**Files:**

- Modify: `docs/superpowers/plans/2026-06-15-level-2-proposal-review-coverage.md`

- [ ] **Step 1: Format and run full local verification**

Run:

```bash
.venv/bin/python -m pytest -q
git diff --check
codegraph sync
codegraph status .
git status --short --branch --untracked-files=all
```

Expected:

- pytest passes.
- `git diff --check` exits 0.
- CodeGraph status is clean/up to date after sync.
- Git status shows only intended Node 6 files.

- [ ] **Step 2: Run Claude implementation review**

Run a self-contained implementation review:

```bash
{
  printf '%s\n' 'Review the implemented Level 2 proposal-review-coverage node for polymarket-alpha-lab before commit.'
  printf '%s\n' 'This is a read-only code review. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical findings: unsafe live execution/credential/scraping/compliance scope, broken report-only boundary, data integrity bugs, missing validation-before-open behavior, failing tests, or public API/scope leaks.'
  printf '%s\n' 'Important findings: incorrect coverage counts, status/gate logic bugs, deterministic ordering bugs, missing mutation revalidation, missing root export migration, or docs that misstate the boundary.'
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
  printf '%s\n' 'Plan:'
  cat docs/superpowers/plans/2026-06-15-level-2-proposal-review-coverage.md
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'Tracked-file diff:'
  git diff -- src/polymarket_alpha_lab/proposal_review_coverage.py src/polymarket_alpha_lab/__init__.py tests/test_proposal_review_coverage.py tests/test_proposal_review_coverage_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py tests/test_proposal_review_quality_scope.py tests/test_proposal_review_diagnostics_scope.py README.md docs/superpowers/plans/2026-06-15-level-2-proposal-review-coverage.md
  printf '%s\n' ''
  printf '%s\n' 'Full contents for new untracked files, if any:'
  for path in \
    src/polymarket_alpha_lab/proposal_review_coverage.py \
    tests/test_proposal_review_coverage.py \
    tests/test_proposal_review_coverage_scope.py \
    docs/superpowers/plans/2026-06-15-level-2-proposal-review-coverage.md
  do
    if git ls-files --others --exclude-standard -- "$path" | grep -q .; then
      printf '%s\n' ""
      printf '===== %s =====\n' "$path"
      cat "$path"
    fi
  done
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted implementation-review terminal state: `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed` or `Verdict: Proceed with fixes`. Fix every Critical or Important finding and rerun the review before commit.

- [ ] **Step 3: Append Handoff Summary**

Append this section with actual command outputs and current commit hash:

```markdown
## Handoff Summary

- Node completed: Level 2 Node 6 proposal-review coverage.
- Commit: pending at handoff-write time; final assistant response must report the commit hash after commit.
- Pushed: pending at handoff-write time; final assistant response must report the push result after push.
- Repo status before commit: <git status output>
- Verification commands:
  - `.venv/bin/python -m pytest -q`: <pass/fail summary>
  - `git diff --check`: <pass/fail summary>
  - `codegraph sync`: <pass/fail summary>
  - `codegraph status .`: <up-to-date/stale summary>
  - Claude implementation review: <Critical/Important/Minor counts and verdict>
- Files changed:
  - `src/polymarket_alpha_lab/proposal_review_coverage.py`
  - `src/polymarket_alpha_lab/__init__.py`
  - `tests/test_proposal_review_coverage.py`
  - `tests/test_proposal_review_coverage_scope.py`
  - `tests/test_init.py`
  - scope allowlist tests
  - `README.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-review-coverage.md`
- Uncommitted files after push: <git status output>
- Next safe step: Level 2 readiness/evidence dossier can consume summary, quality, diagnostics, and coverage artifacts as supplied inputs, but it must remain report-only and require a new plan plus Claude review before implementation.
```

## Handoff Summary

- Node completed: Level 2 Node 6 proposal-review coverage.
- Commit: pending at handoff-write time; final assistant response must report the commit hash after commit.
- Pushed: pending at handoff-write time; final assistant response must report the push result after push.
- Repo status before commit:
  - `## main...origin/main`
  - Modified tracked files: `README.md`, `src/polymarket_alpha_lab/__init__.py`, `tests/test_analytics_history_scope.py`, `tests/test_analytics_scope.py`, `tests/test_forecast_evidence_scope.py`, `tests/test_init.py`, `tests/test_manual_review_queue_scope.py`, `tests/test_proposal_packet_scope.py`, `tests/test_proposal_review_diagnostics_scope.py`, `tests/test_proposal_review_quality_scope.py`, `tests/test_proposal_review_scope.py`, `tests/test_proposal_review_summary_scope.py`.
  - Untracked new files: `docs/superpowers/plans/2026-06-15-level-2-proposal-review-coverage.md`, `src/polymarket_alpha_lab/proposal_review_coverage.py`, `tests/test_proposal_review_coverage.py`, `tests/test_proposal_review_coverage_scope.py`.
- Verification commands:
  - `.venv/bin/python -m pytest tests/test_proposal_review_coverage.py tests/test_proposal_review_coverage_scope.py tests/test_init.py -q`: `40 passed`.
  - `.venv/bin/python -m pytest -q`: `553 passed`.
  - `git diff --check`: exit 0.
  - `codegraph sync`: completed; index already up to date.
  - `codegraph status .`: index up to date.
  - Claude implementation review with `claude-opus-4-8 --effort max`: `Critical findings: 0`, `Important findings: 0`, `Minor findings: 0`, `Verdict: Proceed`.
- Files changed:
  - `src/polymarket_alpha_lab/proposal_review_coverage.py`
  - `src/polymarket_alpha_lab/__init__.py`
  - `tests/test_proposal_review_coverage.py`
  - `tests/test_proposal_review_coverage_scope.py`
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
  - `README.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-review-coverage.md`
- Uncommitted files after push: pending at handoff-write time; final assistant response must report the post-push `git status`.
- Next safe step: Level 2 readiness/evidence dossier can consume summary, quality, diagnostics, and coverage artifacts as supplied inputs, but it must remain report-only and require a new plan plus Claude review before implementation.

- [ ] **Step 4: Commit and push**

Run:

```bash
git add src/polymarket_alpha_lab/proposal_review_coverage.py \
  src/polymarket_alpha_lab/__init__.py \
  tests/test_proposal_review_coverage.py \
  tests/test_proposal_review_coverage_scope.py \
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
  README.md \
  docs/superpowers/plans/2026-06-15-level-2-proposal-review-coverage.md
git commit -m "feat: add proposal review coverage reports"
git push origin main
git status --short --branch --untracked-files=all
```

Expected: push succeeds and final status is clean against `origin/main`.

## Self-Review

- Spec coverage: The plan covers the next Level 2 report-only gap identified by the existing artifacts: packet-denominator review coverage. It advances proposal quality under human review without entering manual execution import, broker integration, credentials, live order placement, scraping, or compliance analysis.
- Placeholder scan: No implementation task uses TBD/TODO language. The tests, public API, status rules, gate rules, file list, verification commands, Claude review policy, and handoff fields are specified.
- Type consistency: The same names are used throughout: `TradeProposalReviewCoverageConfig`, `TradeProposalReviewCoverageGateResult`, `TradeProposalReviewCoverageBucketRow`, `TradeProposalReviewCoveragePacketRow`, `TradeProposalReviewCoverageReport`, `TradeProposalReviewCoverageLog`, and `build_trade_proposal_review_coverage_report`.
