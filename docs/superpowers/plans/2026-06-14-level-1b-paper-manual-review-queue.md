# Level 1B Paper Manual Review Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a paper-only manual-review queue that combines caller-supplied market scores, normalized candidate context, paper analytics history, and forecast evidence into deterministic review artifacts.

**Architecture:** Add a new `manual_review_queue.py` derived layer. It accepts already-supplied paper artifacts, builds frozen dataclasses, ranks review items deterministically, and writes append-only JSONL snapshots after validation. It does not fetch data, read JSONL, generate trade proposals, run approval workflows, place orders, authenticate, or interact with live accounts.

**Tech Stack:** Python 3.11+, standard library, frozen dataclasses, `Decimal`, UTC `datetime`, JSONL, pytest, CodeGraph, Claude Code reviews with `claude-opus-4-8` and effort `max`.

---

## Review And Execution Protocol

1. Submit this plan to Claude Code with model `claude-opus-4-8`, effort `max`, read-only permissions before implementation.
2. Do not implement until Claude returns `Proceed` or `Proceed with fixes` with zero Critical and zero Important findings.
3. Use TDD for implementation:
   - Write focused failing tests first.
   - Run the focused test and capture the expected failure.
   - Implement the minimum code.
   - Rerun the focused test and capture the pass.
4. Before commit, run fresh verification and a self-contained Claude implementation review covering all modified and untracked files.
5. Resolve every Critical or Important implementation-review finding before staging for final commit.
6. Append a Handoff Summary to this plan before final commit.
7. Commit and push only after all gates pass.

## Plan Review Command Before Any Implementation

Run this exact self-contained command before implementation:

```bash
{
  printf '%s\n' 'Review this Level 1B Node 6 implementation plan for polymarket-alpha-lab.'
  printf '%s\n' 'This is a read-only, self-contained plan review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, roadmap, validation gates, existing code, tests, or plan text.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; plan is implementable as written.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, unsafe scope, missing required material, ambiguous implementation surface, or plan gap that could lead to live/proposal/approval behavior.'
  printf '%s\n' 'Review specifically: paper-only scope boundaries, forbidden surfaces, target files, TDD steps, manual-review semantics, public naming constraints, allowed imports, CodeGraph usage, verification gates, implementation-review self-containment, Handoff Summary, and commit/push order.'
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
  printf '%s\n' 'Roadmap:'
  cat docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md
  printf '%s\n' ''
  printf '%s\n' 'Validation gates:'
  cat docs/research/validation-gates.md
  printf '%s\n' ''
  printf '%s\n' 'CodeGraph status:'
  codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Current public API root:'
  codegraph node src/polymarket_alpha_lab/__init__.py
  printf '%s\n' ''
  printf '%s\n' 'Current public API tests:'
  codegraph node tests/test_init.py
  printf '%s\n' ''
  printf '%s\n' 'Relevant source contracts:'
  codegraph node src/polymarket_alpha_lab/domain.py
  codegraph node src/polymarket_alpha_lab/analytics_history.py
  codegraph node src/polymarket_alpha_lab/forecast_evidence.py
  printf '%s\n' ''
  printf '%s\n' 'Existing scope tests:'
  sed -n '1,340p' tests/test_analytics_scope.py
  sed -n '1,340p' tests/test_analytics_history_scope.py
  sed -n '1,360p' tests/test_forecast_evidence_scope.py
  printf '%s\n' ''
  printf '%s\n' 'README current scope and Node 1-5 sections:'
  sed -n '1,180p' README.md
  printf '%s\n' ''
  printf '%s\n' 'Previous Node 5 plan and handoff:'
  cat docs/superpowers/plans/2026-06-13-level-1b-paper-forecast-evidence.md
  printf '%s\n' ''
  printf '%s\n' 'Node 6 plan under review:'
  cat docs/superpowers/plans/2026-06-14-level-1b-paper-manual-review-queue.md
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted plan-review terminal state: a fresh Claude review response that explicitly reports zero Critical findings, zero Important findings, and a verdict of `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count, ambiguous verdict, unsafe scope, or missing review material is treated as `Blocked`. After fixing any Critical or Important plan-review finding, rerun the same self-contained Claude plan-review prompt and do not implement until the rerun reaches an accepted terminal state.

## Level 1B Node 6 Scope

Node 6 adds a paper-only manual-review queue. It is the last Level 1B-style derived artifact before Level 2 proposal work. It helps a human inspect which paper candidates have enough evidence to review, but it does not create proposal packets or authorization states.

The module must:

- Consume caller-supplied `PaperManualReviewCandidate` values.
- Consume caller-supplied `MarketScore` values.
- Consume one caller-supplied `PaperAnalyticsHistoryReport`.
- Consume one caller-supplied `PaperForecastEvidenceReport`.
- Emit a frozen `PaperManualReviewQueue` containing sorted `PaperManualReviewQueueItem` values.
- Persist queue snapshots through `PaperManualReviewLog(path).append(queue)`.
- Enforce `paper_only=True` on queue artifacts.
- Use deterministic sorting and deterministic tie-breaking.
- Preserve review reasons, risk/evidence summaries, and source identifiers.
- Treat `paper_review_ready` as a manual inspection status only.

The module must not:

- Import or call API clients, scanners, archives, normalization, paper fill simulation, paper journals, risk evaluators, analytics builders, or forecast builders.
- Fetch market, order-book, price-history, outcome, or account data.
- Read JSONL logs or external history.
- Generate trade proposals, approval requests, order instructions, live-readiness states, strategy-promotion packets, or execution decisions.
- Handle credentials, private keys, wallets, signing, authentication, account state, broker interfaces, user WebSockets, heartbeats, or reconciliation.
- Add CLI, UI, dashboard, scheduler, notification, scraping, browser automation, compliance, legal, or geographic analysis surfaces.

## Target File Structure

Create:

- `src/polymarket_alpha_lab/manual_review_queue.py`
- `tests/test_manual_review_queue.py`
- `tests/test_manual_review_queue_scope.py`

Modify:

- `src/polymarket_alpha_lab/__init__.py`
- `tests/test_init.py`
- `README.md`
- `docs/superpowers/plans/2026-06-14-level-1b-paper-manual-review-queue.md`

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

## Part 0: Pre-Implementation Contract Check

**Files:**

- Read only.

- [ ] **Step 1: Inspect current contracts with CodeGraph**

Run before writing implementation tests:

```bash
codegraph status .
codegraph node src/polymarket_alpha_lab/domain.py
codegraph node src/polymarket_alpha_lab/analytics_history.py
codegraph node src/polymarket_alpha_lab/forecast_evidence.py
codegraph node src/polymarket_alpha_lab/__init__.py
codegraph node tests/test_init.py
```

Expected: CodeGraph is up to date, and the current source confirms `MarketScore`, `PaperAnalyticsHistoryReport`, and `PaperForecastEvidenceReport` field names used by this plan.

## Public API Contract

`src/polymarket_alpha_lab/manual_review_queue.py` must export exactly:

```python
__all__ = (
    "PaperManualReviewCandidate",
    "PaperManualReviewConfig",
    "PaperManualReviewLog",
    "PaperManualReviewQueue",
    "PaperManualReviewQueueItem",
    "build_paper_manual_review_queue",
)
```

### PaperManualReviewConfig

Fields:

```python
config_version: str
min_source_score: Decimal = Decimal("0.0000")
min_ready_items: int = 1
include_blocked_items: bool = True
boundary_statement: str = DEFAULT_BOUNDARY_STATEMENT
```

`DEFAULT_BOUNDARY_STATEMENT` must be exactly:

```python
"This is a paper-only manual-review artifact for human inspection, not a trade instruction or order instruction."
```

Validation:

- `config_version` and `boundary_statement` must be canonical nonblank strings.
- `min_source_score` must be a finite nonnegative `Decimal`.
- `min_ready_items` must be a nonnegative integer and not a `bool`.
- `include_blocked_items` must be a `bool`.
- `boundary_statement` must say the artifact is paper-only manual review and not a trade instruction. This is checked with simple string containment in tests, not legal/compliance logic.

### PaperManualReviewCandidate

Fields:

```python
queued_at: datetime
packet_id: str
condition_id: str
token_id: str
market_slug: str
market_url: str
question: str
outcome_name: str
source_score: Decimal
raw_archive_path: str
strategy_type: str
risk_tags: tuple[str, ...]
thesis: str
invalidating_conditions: str
rule_text_hash: str
resolution_source: str
model_probability: Decimal | None
expected_entry_price: Decimal | None
fair_value_estimate: Decimal | None
theoretical_edge: Decimal | None
cost_adjusted_edge: Decimal | None
confidence: Decimal | None
max_executable_size: Decimal | None
risk_gate_passed: bool
risk_reason_codes: tuple[str, ...] = ()
risk_reason_summary: str | None = None
paper_only: bool = True
```

Validation:

- `queued_at` is normalized to UTC.
- Identity and descriptive strings are canonical nonblank except `market_url`, which may be an empty string only if the candidate is incomplete.
- `source_score` is a finite nonnegative `Decimal`.
- Optional ratio/price/size fields are `Decimal | None`, finite when present, and never floats.
- `risk_tags` and `risk_reason_codes` normalize to tuples of canonical nonblank strings.
- `risk_gate_passed=True` requires `risk_reason_codes == ()`.
- `risk_gate_passed=False` requires at least one risk reason code.
- `risk_reason_summary` is `None` or a canonical nonblank string.
- `paper_only` must be `True`.

### PaperManualReviewQueueItem

Fields:

```python
queue_item_id: str
rank: int
status: str
status_rank: int
hard_block_count: int
evidence_pass_count: int
source_score: Decimal
market_score_total: Decimal | None
queued_at: datetime
packet_id: str
condition_id: str
token_id: str
market_slug: str
market_url: str
question: str
outcome_name: str
strategy_type: str
risk_tags: tuple[str, ...]
thesis: str
invalidating_conditions: str
rule_text_hash: str
resolution_source: str
model_probability: Decimal | None
expected_entry_price: Decimal | None
fair_value_estimate: Decimal | None
theoretical_edge: Decimal | None
cost_adjusted_edge: Decimal | None
confidence: Decimal | None
max_executable_size: Decimal | None
risk_gate_passed: bool
risk_reason_codes: tuple[str, ...]
history_status: str
forecast_status: str
history_gate_pass_count: int
forecast_gate_pass_count: int
history_gate_fail_count: int
forecast_gate_fail_count: int
readiness_summary: str
risk_summary: str
evidence_summary: str
why_in_queue: str
primary_reason_code: str
supporting_reason_codes: tuple[str, ...]
blocking_reason_codes: tuple[str, ...]
review_focus: tuple[str, ...]
evidence_scope: str
boundary_statement: str
paper_only: bool = True
```

Validation:

- All dataclass invariants are validated in `__post_init__`.
- `rank` must be a positive integer.
- Counts and ranks must be nonnegative/positive as appropriate and not `bool`.
- `status` must be one of `incomplete_data`, `insufficient_evidence`, `blocked_by_risk`, `blocked_by_quality`, `paper_review_ready`.
- `status_rank` must match the status map:
  - `paper_review_ready`: `0`
  - `insufficient_evidence`: `1`
  - `blocked_by_quality`: `2`
  - `blocked_by_risk`: `3`
  - `incomplete_data`: `4`
- `queue_item_id` must equal `condition_id:token_id:packet_id`.
- `boundary_statement` must equal the config boundary statement.
- `paper_only` must be `True`.

### PaperManualReviewQueue

Fields:

```python
generated_at: datetime
config_version: str
first_queued_at: datetime | None
last_queued_at: datetime | None
candidate_count: int
item_count: int
ready_item_count: int
insufficient_item_count: int
blocked_risk_item_count: int
blocked_quality_item_count: int
incomplete_item_count: int
unique_market_count: int
unique_strategy_count: int
unique_risk_tag_count: int
top_queue_item_id: str | None
status: str
items: tuple[PaperManualReviewQueueItem, ...]
boundary_statement: str
paper_only: bool = True
```

Validation:

- `generated_at`, `first_queued_at`, and `last_queued_at` normalize to UTC.
- `config_version` and `boundary_statement` are canonical nonblank strings.
- Counts are nonnegative integers and not `bool`.
- `item_count == len(items)`.
- Status counts equal the actual item statuses.
- `top_queue_item_id` equals the first item id when items exist and is `None` when empty.
- Empty queues require absent queued-at bounds and `status == "incomplete_data"`.
- Non-empty queues require queued-at bounds and sorted items.
- `paper_only` must be `True`.

### PaperManualReviewLog

Fields:

```python
path: Path | str
```

Behavior:

- Normalize path like analytics/history logs.
- `append(queue)` checks type, validates nested tree, serializes with `json.dumps(..., allow_nan=False, sort_keys=True) + "\n"`, validates parent, creates parent directories, then opens the file in append mode.
- Existing file content must be preserved when validation or serialization fails.

### build_paper_manual_review_queue

Signature:

```python
def build_paper_manual_review_queue(
    candidates: Iterable[PaperManualReviewCandidate],
    *,
    market_scores: Iterable[MarketScore],
    analytics_history: PaperAnalyticsHistoryReport,
    forecast_evidence: PaperForecastEvidenceReport,
    config: PaperManualReviewConfig,
    generated_at: datetime,
) -> PaperManualReviewQueue:
```

Validation:

- `candidates` and `market_scores` reject `str` and `bytes`.
- Every candidate is `PaperManualReviewCandidate`.
- Every market score is `MarketScore`.
- Reports must be the exact expected report types and paper-only.
- Config must be `PaperManualReviewConfig`.
- `generated_at` must be `datetime`.
- Duplicate candidate key `(queued_at_utc, token_id, packet_id)` is rejected after UTC normalization.
- Duplicate queue item id `(condition_id, token_id, packet_id)` is rejected even if `queued_at` differs.
- Duplicate market score key `(condition_id, token_id)` is rejected.
- Duplicate validation happens before `include_blocked_items` filtering, so duplicate blocked or incomplete candidates are rejected even when they would later be dropped from the final queue.
- Missing market score for a candidate is allowed; `market_score_total` becomes `None` and the candidate's `source_score` remains the ranking score.
- Market scores without matching candidates are ignored.

Status derivation:

1. If a candidate has missing core fields or report inputs are incomplete, item status is `incomplete_data`.
2. Else if `risk_gate_passed` is false or analytics history status is `blocked_by_risk`, item status is `blocked_by_risk`.
3. Else if forecast evidence status is `blocked_by_quality`, item status is `blocked_by_quality`.
4. Else if analytics history status or forecast evidence status is `insufficient_evidence`, item status is `insufficient_evidence`.
5. Else if source score is below `config.min_source_score`, item status is `insufficient_evidence`.
6. Else if analytics history and forecast evidence are both `paper_review_ready`, item status is `paper_review_ready`.
7. Otherwise item status is `insufficient_evidence`.

Queue status:

- Empty queue: `incomplete_data`.
- Any `paper_review_ready` count greater than or equal to `config.min_ready_items`: `paper_review_ready`.
- Else any `blocked_by_quality`: `blocked_by_quality`.
- Else any `blocked_by_risk`: `blocked_by_risk`.
- Else any `insufficient_evidence`: `insufficient_evidence`.
- Else `incomplete_data`.

Sorting:

Items are sorted by this deterministic tuple:

```python
(
    status_rank,
    hard_block_count,
    -evidence_pass_count,
    -source_score,
    -cost_adjusted_edge_or_zero,
    -confidence_or_zero,
    -max_executable_size_or_zero,
    risk_drag_ratio,
    -freshness_timestamp,
    market_slug,
    token_id,
    packet_id,
)
```

The implementation can represent negative `Decimal` values by multiplying by `Decimal("-1")`; no floats are allowed.

`risk_drag_ratio` is a finite `Decimal` derived only from queue inputs:

```python
risk_drag_ratio = (
    Decimal(hard_block_count)
    + Decimal(history_gate_fail_count) / Decimal("10")
    + Decimal(forecast_gate_fail_count) / Decimal("10")
).quantize(Decimal("0.0001"))
```

`freshness_timestamp` is an integer microsecond key derived without `datetime.timestamp()`:

```python
freshness_source = max(candidate.queued_at, analytics_history.generated_at, forecast_evidence.generated_at)
freshness_timestamp = (
    freshness_source.toordinal() * 86400000000
    + freshness_source.hour * 3600000000
    + freshness_source.minute * 60000000
    + freshness_source.second * 1000000
    + freshness_source.microsecond
)
```

Source datetimes must be Python `datetime` values normalized through this module's dataclass validators before this key is computed. This follows the existing project convention: naive datetimes are treated as UTC, aware datetimes are converted to UTC, and non-`datetime` values are rejected. The ordinal microsecond integer stays within Python's supported `datetime` year range and avoids float conversion entirely. This key is used only for sorting and is not exported.

If `config.include_blocked_items` is `False`, retain only items with statuses `paper_review_ready` or `insufficient_evidence`; drop `blocked_by_risk`, `blocked_by_quality`, and `incomplete_data`. Queue aggregate fields except `candidate_count` are computed from the final retained `items`; `candidate_count` remains the original validated candidate input count. If all derived items are filtered out, return an empty queue with `candidate_count > 0`, `item_count == 0`, no queued-at bounds, `top_queue_item_id is None`, and `status == "incomplete_data"`.

Reason fields:

- `primary_reason_code` must be one of `paper_evidence_ready`, `needs_more_sample`, `blocked_risk_drawdown`, `blocked_forecast_quality`, `incomplete_data`, `below_source_score`.
- `supporting_reason_codes` includes deterministic tokens such as `high_source_score`, `risk_gate_passed`, `history_ready`, `forecast_ready`, `sample_size_passed`, `edge_quality_passed`.
- `blocking_reason_codes` includes deterministic tokens sourced from candidate risk reasons and report gate failures, prefixed with `risk_gate:`, `analytics_history:`, or `forecast_evidence:`.
- `review_focus` is deterministic and ordered by this exact token mapping:
  - Always include `resolution_rule_ambiguity`.
  - Add `liquidity_exit_risk` when the candidate has risk tag `liquidity`, when analytics history gate `execution_cost_reality` is not `pass`, when `analytics_history.worst_exit_depth_shortfall_ratio` is positive, or when the latest trend by `marked_at` has a positive `exit_depth_shortfall_ratio`.
  - Add `probability_quality` when forecast evidence gate `probability_quality` has status `pass`, `fail`, or `incomplete`, when `forecast_evidence.probability_observation_count > 0`, or when `forecast_evidence.mean_probability_loss` or `forecast_evidence.worst_bucket_error` is not `None`.
  - Add `edge_quality` when forecast evidence gate `executable_edge_quality` has status `pass`, `fail`, or `incomplete`, when `forecast_evidence.edge_observation_count > 0`, or when `forecast_evidence.mean_edge_gap_ratio` or `forecast_evidence.positive_edge_hit_rate` is not `None`.
  - Add `residual_exposure` when forecast evidence gate `residual_exposure` has status `pass` or `fail`, or when `forecast_evidence.worst_residual_exposure_ratio` is not `None`.
  - Add `theme_concentration` when analytics history has a nonzero largest-market ratio or nonzero largest-risk-tag ratio.
- `evidence_scope` must be exactly `portfolio_and_forecast_aggregate`.
- `boundary_statement` must be included in every item and report.

## Part 1: Behavior Tests And Minimal Implementation

**Files:**

- Create: `tests/test_manual_review_queue.py`
- Create: `src/polymarket_alpha_lab/manual_review_queue.py`

- [ ] **Step 1: Write the first failing behavior test**

Add helpers in `tests/test_manual_review_queue.py`:

```python
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.analytics_history import (
    PaperAnalyticsHistoryGateResult,
    PaperAnalyticsHistoryReport,
    PaperAnalyticsHistoryTrend,
)
from polymarket_alpha_lab.domain import MarketScore
from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.manual_review_queue import (
    PaperManualReviewCandidate,
    PaperManualReviewConfig,
    PaperManualReviewLog,
    build_paper_manual_review_queue,
)


def market_score(token_id: str, total_bias: Decimal = Decimal("0")) -> MarketScore:
    return MarketScore(
        condition_id="condition-1",
        token_id=token_id,
        activity=Decimal("90") + total_bias,
        liquidity=Decimal("80"),
        spread_quality=Decimal("85"),
        time_structure=Decimal("70"),
        information_structure=Decimal("75"),
        price_behavior=Decimal("65"),
        duplicate_penalty=Decimal("0"),
    )


def ready_history_report():
    gate_results = tuple(
        PaperAnalyticsHistoryGateResult(
            gate_name=gate_name,
            status="pass",
            message=f"{gate_name} is ready for manual review.",
        )
        for gate_name in (
            "data_integrity",
            "sample_size",
            "execution_cost_reality",
            "forecast_edge_quality",
            "risk_drawdown",
        )
    )
    trend = PaperAnalyticsHistoryTrend(
        marked_at=datetime(2026, 9, 1, tzinfo=UTC),
        exit_nav=Decimal("10100"),
        total_exit_pnl=Decimal("100"),
        drawdown=Decimal("0"),
        drawdown_ratio=Decimal("0.0000"),
        exit_depth_shortfall_ratio=Decimal("0.0000"),
        no_exit_depth_cost_basis_ratio=Decimal("0.0000"),
        midpoint_nav_gap_ratio=Decimal("0.0000"),
        breach_count=0,
    )
    return PaperAnalyticsHistoryReport(
        generated_at=datetime(2026, 9, 1, tzinfo=UTC),
        config_version="history-test",
        first_marked_at=datetime(2026, 9, 1, tzinfo=UTC),
        last_marked_at=datetime(2026, 9, 1, tzinfo=UTC),
        report_count=1,
        candidate_observation_count=10,
        simulated_trade_count=10,
        exited_trade_count=10,
        forward_window_days=30,
        unique_market_count=1,
        unique_strategy_count=1,
        unique_risk_tag_count=1,
        latest_exit_nav=Decimal("10100"),
        latest_total_exit_pnl=Decimal("100"),
        max_drawdown=Decimal("0"),
        max_drawdown_ratio=Decimal("0.0000"),
        worst_exit_depth_shortfall_ratio=Decimal("0.0000"),
        worst_no_exit_depth_cost_basis_ratio=Decimal("0.0000"),
        worst_midpoint_nav_gap_ratio=Decimal("0.0000"),
        largest_market_cost_basis_ratio=Decimal("0.1000"),
        largest_risk_tag_cost_basis_ratio=Decimal("0.1000"),
        max_breach_count=0,
        status="paper_review_ready",
        gate_results=gate_results,
        trends=(trend,),
    )


def ready_forecast_report():
    observations = tuple(
        PaperForecastEvidenceObservation(
            observed_at=datetime(2026, 8, 1 + index, tzinfo=UTC),
            source_packet_id=f"packet-{index}",
            condition_id="condition-1",
            token_id=f"token-{index}",
            market_slug=f"market-{index}",
            strategy_type="relative_value",
            risk_tags=("liquidity",),
            predicted_probability=Decimal("1.0000"),
            actual_outcome_value=Decimal("1"),
            theoretical_edge_ratio=Decimal("0.0300"),
            executable_edge_ratio=Decimal("0.0300"),
            fill_probability=Decimal("1.0000"),
            residual_exposure_ratio=Decimal("0.0000"),
            paper_return_ratio=Decimal("0.0100"),
        )
        for index in range(2)
    )
    return build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="forecast-test",
            min_probability_observations=2,
            min_edge_observations=2,
            max_mean_probability_loss=Decimal("0"),
            max_bucket_error=Decimal("0"),
            max_mean_edge_gap_ratio=Decimal("0"),
            min_positive_edge_hit_rate=Decimal("0.5000"),
            max_residual_exposure_ratio=Decimal("0"),
        ),
        generated_at=datetime(2026, 9, 1, tzinfo=UTC),
    )


def candidate(index: int, *, score: Decimal, risk_gate_passed: bool = True):
    return PaperManualReviewCandidate(
        queued_at=datetime(2026, 9, 2, index, tzinfo=UTC),
        packet_id=f"packet-{index}",
        condition_id="condition-1",
        token_id=f"token-{index}",
        market_slug=f"market-{index}",
        market_url=f"https://polymarket.com/event/market-{index}",
        question=f"Will event {index} happen?",
        outcome_name="Yes",
        source_score=score,
        raw_archive_path=f"data/raw/market-{index}.json",
        strategy_type="relative_value",
        risk_tags=("liquidity", "rules"),
        thesis="Paper thesis for manual review.",
        invalidating_conditions="Rule ambiguity or liquidity decay.",
        rule_text_hash="a" * 64,
        resolution_source="official source",
        model_probability=Decimal("0.6500"),
        expected_entry_price=Decimal("0.6000"),
        fair_value_estimate=Decimal("0.7000"),
        theoretical_edge=Decimal("0.1000"),
        cost_adjusted_edge=Decimal("0.0700"),
        confidence=Decimal("0.8000"),
        max_executable_size=Decimal("100"),
        risk_gate_passed=risk_gate_passed,
        risk_reason_codes=() if risk_gate_passed else ("low_confidence",),
        risk_reason_summary=None if risk_gate_passed else "confidence is below minimum",
    )
```

Add the first test:

```python
def test_build_paper_manual_review_queue_summarizes_and_sorts_items():
    report = build_paper_manual_review_queue(
        [candidate(2, score=Decimal("80.0000")), candidate(1, score=Decimal("90.0000"))],
        market_scores=(market_score("token-1"), market_score("token-2")),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(config_version="node6-test"),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )

    assert report.generated_at == datetime(2026, 9, 3, tzinfo=UTC)
    assert report.config_version == "node6-test"
    assert report.candidate_count == 2
    assert report.item_count == 2
    assert report.ready_item_count == 2
    assert report.status == "paper_review_ready"
    assert [item.packet_id for item in report.items] == ["packet-1", "packet-2"]
    assert [item.rank for item in report.items] == [1, 2]
    assert report.top_queue_item_id == "condition-1:token-1:packet-1"
    assert report.first_queued_at == datetime(2026, 9, 2, 1, tzinfo=UTC)
    assert report.last_queued_at == datetime(2026, 9, 2, 2, tzinfo=UTC)
    assert report.items[0].status == "paper_review_ready"
    assert report.items[0].status_rank == 0
    assert report.items[0].source_score == Decimal("90.0000")
    assert report.items[0].history_status == "paper_review_ready"
    assert report.items[0].forecast_status == "paper_review_ready"
    assert report.items[0].primary_reason_code == "paper_evidence_ready"
    assert "paper-only manual-review artifact" in report.items[0].boundary_statement
```

- [ ] **Step 2: Run the first test and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_manual_review_queue.py::test_build_paper_manual_review_queue_summarizes_and_sorts_items -q
```

Expected: fail with `ModuleNotFoundError: No module named 'polymarket_alpha_lab.manual_review_queue'`.

- [ ] **Step 3: Implement the minimal module skeleton and builder**

Create `src/polymarket_alpha_lab/manual_review_queue.py` with:

- The six exported public names.
- `DEFAULT_BOUNDARY_STATEMENT`.
- Status constants and status-rank map.
- Frozen dataclasses described in the public API contract.
- Builder logic enough for the first test.
- Local validators copied in style from analytics history and forecast evidence.
- No imports outside the allowed import set.

- [ ] **Step 4: Run the first test and verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_manual_review_queue.py::test_build_paper_manual_review_queue_summarizes_and_sorts_items -q
```

Expected: pass.

## Part 2: Status, Sorting, And Validation Coverage

**Files:**

- Modify: `tests/test_manual_review_queue.py`
- Modify: `src/polymarket_alpha_lab/manual_review_queue.py`

- [ ] **Step 1: Add status tests**

Add tests for:

- Empty input returns `status == "incomplete_data"`, zero counts, no items, no bounds, `top_queue_item_id is None`.
- Risk gate rejected returns item `blocked_by_risk`, hard block count greater than zero, and blocking reason code prefixed with `risk_gate:`.
- Forecast evidence `blocked_by_quality` returns item `blocked_by_quality`.
- History or forecast `insufficient_evidence` returns item `insufficient_evidence`.
- `include_blocked_items=False` filters blocked risk and blocked quality items out of the final queue.
- `min_source_score` below threshold produces `insufficient_evidence` with primary reason `below_source_score`.

Run each focused test after writing it; each must fail before implementation and pass after implementation.

- [ ] **Step 2: Add duplicate and UTC normalization tests**

Add:

```python
def test_build_paper_manual_review_queue_rejects_duplicate_candidate_key_after_utc_normalization():
    base = candidate(1, score=Decimal("90.0000"))
    shifted = replace(
        base,
        queued_at=datetime(2026, 9, 1, 20, tzinfo=timezone(timedelta(hours=-4))),
    )
    utc_value = replace(base, queued_at=datetime(2026, 9, 2, 0, tzinfo=UTC))

    with pytest.raises(ValueError, match="duplicate"):
        build_paper_manual_review_queue(
            [shifted, utc_value],
            market_scores=(market_score("token-1"),),
            analytics_history=ready_history_report(),
            forecast_evidence=ready_forecast_report(),
            config=PaperManualReviewConfig(config_version="node6-test"),
            generated_at=datetime(2026, 9, 3, tzinfo=UTC),
        )
```

Add duplicate market score key coverage.

- [ ] **Step 3: Add bad public input tests**

Add tests that reject:

- `candidates="not-candidates"`.
- `market_scores="not-scores"`.
- Candidate iterable containing `object()`.
- Market score iterable containing `object()`.
- `analytics_history=object()`.
- `forecast_evidence=object()`.
- `config=object()`.
- `generated_at=None`.
- Non-paper reports via `object.__setattr__(report, "paper_only", False)`.

- [ ] **Step 4: Add dataclass value validation tests**

Add tests that reject:

- Non-Decimal `source_score`.
- `Decimal("NaN")` and `Decimal("Infinity")`.
- Negative `min_source_score`.
- `min_ready_items=True` and negative integers.
- `include_blocked_items="yes"`.
- Empty or whitespace config version.
- Empty candidate strings for identity fields.
- `risk_gate_passed=True` with reason codes.
- `risk_gate_passed=False` without reason codes.
- Unknown item/report status through direct construction or `replace`.
- `paper_only=False`.
- Incorrect queue item id.
- Incorrect queue status counts.
- Non-empty report without queued-at bounds.
- Empty report with queued-at bounds.

- [ ] **Step 5: Add frozen dataclass tests**

Add:

```python
def test_manual_review_queue_dataclasses_are_frozen():
    report = build_paper_manual_review_queue(
        [candidate(1, score=Decimal("90.0000"))],
        market_scores=(market_score("token-1"),),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(config_version="node6-test"),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )

    with pytest.raises(FrozenInstanceError):
        report.item_count = 0
    with pytest.raises(FrozenInstanceError):
        report.items[0].rank = 0
```

## Part 3: JSONL Persistence

**Files:**

- Modify: `tests/test_manual_review_queue.py`
- Modify: `src/polymarket_alpha_lab/manual_review_queue.py`

- [ ] **Step 1: Add JSONL append test**

Add:

```python
def test_paper_manual_review_log_appends_jsonl_queue(tmp_path):
    report = build_paper_manual_review_queue(
        [candidate(1, score=Decimal("90.0000"))],
        market_scores=(market_score("token-1"),),
        analytics_history=ready_history_report(),
        forecast_evidence=ready_forecast_report(),
        config=PaperManualReviewConfig(config_version="node6-test"),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )
    log = PaperManualReviewLog(path=tmp_path / "manual-review.jsonl")

    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["generated_at"] == "2026-09-03T00:00:00+00:00"
    assert stored["config_version"] == "node6-test"
    assert stored["items"][0]["source_score"] == "90.0000"
    assert stored["items"][0]["status"] == "paper_review_ready"
```

Expected initial failure before log implementation; pass after `PaperManualReviewLog` implementation.

- [ ] **Step 2: Add append safety tests**

Add tests for:

- Appending twice without overwriting.
- Creating parent directories for string paths.
- Rejecting invalid paths: `object()`, whitespace string, existing directory, parent path that is a file.
- Rejecting non-queue input before file creation.
- Preserving existing file when serialization fails due to `Decimal("NaN")` inserted with `object.__setattr__`.
- Preserving existing file when nested item is invalid.

Implementation must validate the queue tree and serialize before opening the target path.

## Part 4: Scope Tests

**Files:**

- Create: `tests/test_manual_review_queue_scope.py`

- [ ] **Step 1: Add scope test file**

The scope test must:

- Parse `src/polymarket_alpha_lab/manual_review_queue.py`.
- Verify exact module exports.
- Verify only allowed imports.
- Verify first-party import-from symbols:
  - `polymarket_alpha_lab.domain`: `MarketScore`
  - `polymarket_alpha_lab.analytics_history`: `PaperAnalyticsHistoryReport`
  - `polymarket_alpha_lab.forecast_evidence`: `PaperForecastEvidenceReport`
- Reject forbidden imports, including API, archive, CLI, analytics, journal, normalize, paper, pipeline, positions, rejections, research, risk, scoring, network libraries, trading SDKs, scraping/browser automation, SQL/dataframe libraries, `os`, and `subprocess`.
- Reject forbidden internal name fragments that imply credentials, auth, clients, transport, requests, responses, sessions, order actions, direct execution verbs, proposals, approval, promotion, brokers, accounts, reconciliation, settlement, loaders, scraping, browser automation, dashboards, compliance, legal, or geographic surfaces.
- Reject forbidden public export fragments in the package root.

Allowed imports:

```python
ALLOWED_IMPORT_PREFIXES = {
    "json",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.analytics_history",
    "polymarket_alpha_lab.forecast_evidence",
}
```

Expected exports:

```python
EXPECTED_MANUAL_REVIEW_QUEUE_EXPORTS = {
    "PaperManualReviewCandidate",
    "PaperManualReviewConfig",
    "PaperManualReviewLog",
    "PaperManualReviewQueue",
    "PaperManualReviewQueueItem",
    "build_paper_manual_review_queue",
}
```

- [ ] **Step 2: Run scope test and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_manual_review_queue_scope.py -q
```

Expected before implementation/root export completion: fail on missing module or missing expected exports.

- [ ] **Step 3: Fix implementation names/imports until scope test passes**

Run:

```bash
.venv/bin/python -m pytest tests/test_manual_review_queue_scope.py -q
```

Expected: pass.

## Part 5: Package Root Exports

**Files:**

- Modify: `tests/test_init.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`

- [ ] **Step 1: Add failing root export test**

Add import block to `tests/test_init.py`:

```python
from polymarket_alpha_lab.manual_review_queue import (
    PaperManualReviewCandidate,
    PaperManualReviewConfig,
    PaperManualReviewLog,
    PaperManualReviewQueue,
    PaperManualReviewQueueItem,
    build_paper_manual_review_queue,
)
```

Add:

```python
def test_level_1b_node_6_public_api_exports():
    expected_exports = {
        "PaperManualReviewCandidate",
        "PaperManualReviewConfig",
        "PaperManualReviewLog",
        "PaperManualReviewQueue",
        "PaperManualReviewQueueItem",
        "build_paper_manual_review_queue",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperManualReviewCandidate is PaperManualReviewCandidate
    assert lab.PaperManualReviewConfig is PaperManualReviewConfig
    assert lab.PaperManualReviewLog is PaperManualReviewLog
    assert lab.PaperManualReviewQueue is PaperManualReviewQueue
    assert lab.PaperManualReviewQueueItem is PaperManualReviewQueueItem
    assert lab.build_paper_manual_review_queue is build_paper_manual_review_queue
```

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py -q
```

Expected: fail because package root does not export Node 6 names.

- [ ] **Step 2: Export manual review queue APIs from package root**

Add to `src/polymarket_alpha_lab/__init__.py` after the forecast evidence import block and before journal/paper imports:

```python
from polymarket_alpha_lab.manual_review_queue import (
    PaperManualReviewCandidate,
    PaperManualReviewConfig,
    PaperManualReviewLog,
    PaperManualReviewQueue,
    PaperManualReviewQueueItem,
    build_paper_manual_review_queue,
)
```

Add the six public names to `__all__` after forecast evidence names and before `PaperNavLog`, with the builder after `build_paper_forecast_evidence_report`.

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py -q
```

Expected: pass.

## Part 6: README Updates

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Update Phase 1 Scope**

Append paper-only manual-review queues to the Phase 1 scope sentence.

- [ ] **Step 2: Add Node 6 status/API section**

Add after Level 1B Node 5 Python API and before Automation Roadmap:

```markdown
## Level 1B Node 6 Status

Level 1B Node 6 adds a paper-only manual-review queue over supplied market score rows, `PaperAnalyticsHistoryReport` values, and `PaperForecastEvidenceReport` values, including deterministic queue rows, review-priority reasons, evidence completeness checks, and append-only JSONL snapshots. Its manual-review status means the paper artifact is ready for human inspection inside Level 1B only; it is not a promotion, trade, approval, proposal, or live-execution signal. It does not fetch market, order-book, price-history, or account data, use external loaders, scrape websites, authenticate, handle private keys, place or cancel orders, open user WebSockets, run heartbeat logic, use a trading SDK, reconcile exchange accounts, or perform compliance/legal/geographic analysis.

## Level 1B Node 6 Python API

Node 6 is exposed through Python APIs:

- Configure queue rules with `PaperManualReviewConfig(...)`.
- Create normalized paper candidates with `PaperManualReviewCandidate(...)`.
- Build paper manual-review queues with `build_paper_manual_review_queue(candidates, market_scores=..., analytics_history=..., forecast_evidence=..., config=..., generated_at=...)`, which returns `PaperManualReviewQueue`.
- Inspect queued rows with `PaperManualReviewQueueItem`.
- Persist manual-review queue snapshots with `PaperManualReviewLog(path).append(queue)`.
```

- [ ] **Step 3: Update Repository Layout**

Add:

- `docs/superpowers/plans/2026-06-14-level-1b-paper-manual-review-queue.md`
- `src/polymarket_alpha_lab/manual_review_queue.py`
- `tests/test_manual_review_queue.py`
- `tests/test_manual_review_queue_scope.py`

## Level 1B Node 6 Completion Criteria

Node 6 is complete only when all of these are true:

- `src/polymarket_alpha_lab/manual_review_queue.py` exists and is paper-only.
- Static scope tests prove the module does not import or define forbidden auth, network, proposal, approval, promotion, live-action, broker, reconciliation, scraping, dashboard, compliance, legal, or geographic surfaces.
- Public exports avoid forbidden fragments, including `proposal`, `approval`, `execution`, `auth`, `client`, `request`, `broker`, `wallet`, `reconciliation`, `legal`, and `geographic`.
- Builder consumes caller-supplied artifacts only.
- Builder does not fetch market, order-book, price-history, outcome, or account data.
- Builder does not create proposals, approvals, order instructions, live-readiness states, strategy-promotion packets, or execution decisions.
- Empty input produces `incomplete_data`.
- Queue item statuses are deterministic and limited to `incomplete_data`, `insufficient_evidence`, `blocked_by_risk`, `blocked_by_quality`, and `paper_review_ready`.
- Sorting is deterministic and stable.
- Duplicate candidate keys and duplicate market-score keys are rejected.
- All numeric fields are finite `Decimal` values or `None`; floats, NaN, and Infinity are rejected.
- UTC normalization is applied to all datetime fields.
- JSONL append validates and serializes before opening files.
- Package-root exports and README document Node 6 APIs and boundaries.
- TDD red/green evidence exists for focused behavior groups.
- Final verification passes, CodeGraph is up to date, Claude implementation review reports zero Critical and zero Important findings, Handoff Summary is appended, commit is pushed, and final git status is clean.

## Part 7: Final Verification, Claude Review, Handoff, Commit, Push

- [ ] **Step 1: Run fresh verification**

Run:

```bash
git status --short --branch --untracked-files=all
.venv/bin/python -m pytest tests/test_manual_review_queue.py tests/test_manual_review_queue_scope.py tests/test_init.py -q
.venv/bin/python -m pytest tests/test_manual_review_queue_scope.py -q
.venv/bin/python -m pytest tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py -q
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

Run this exact self-contained command after Step 1 passes and before staging:

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

  printf '%s\n' 'Review this Level 1B Node 6 implementation for polymarket-alpha-lab before commit.'
  printf '%s\n' 'This is a read-only, self-contained implementation review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, plan, tests, implementation, or verification output.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; implementation is ready to stage, handoff, commit, and push.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing required review material, unsafe scope, failed verification, stale CodeGraph, missing or unexpected tracked/untracked file, staged content before review, or omitted file content.'
  printf '%s\n' 'Review specifically: paper-only scope boundaries, forbidden surfaces, manual-review semantics, public naming constraints, Decimal strictness, JSONL validation-before-open behavior, package exports, README updates, tests, CodeGraph status, and final gate readiness.'
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
  printf '%s\n' 'Node 6 plan:'
  cat docs/superpowers/plans/2026-06-14-level-1b-paper-manual-review-queue.md
  printf '%s\n' ''
  printf '%s\n' 'Existing scope tests:'
  sed -n '1,340p' tests/test_analytics_scope.py
  sed -n '1,340p' tests/test_analytics_history_scope.py
  sed -n '1,360p' tests/test_forecast_evidence_scope.py
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
  run_review_cmd .venv/bin/python -m pytest tests/test_manual_review_queue.py tests/test_manual_review_queue_scope.py tests/test_init.py -q
  run_review_cmd .venv/bin/python -m pytest tests/test_manual_review_queue_scope.py -q
  run_review_cmd .venv/bin/python -m pytest tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py -q
  run_review_cmd .venv/bin/python -m pytest -q
  run_review_cmd git diff --check
  run_review_cmd git diff --cached --check
  run_review_cmd codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Tracked diff names:'
  git diff --name-only
  printf '%s\n' 'Expected tracked diff files: AGENTS.md, README.md, src/polymarket_alpha_lab/__init__.py, tests/test_init.py'
  expected_tracked=$(printf '%s\n' AGENTS.md README.md src/polymarket_alpha_lab/__init__.py tests/test_init.py | sort)
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
  for path in AGENTS.md README.md src/polymarket_alpha_lab/__init__.py tests/test_init.py; do
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
  printf '%s\n' 'Expected untracked files: docs/superpowers/plans/2026-06-14-level-1b-paper-manual-review-queue.md, src/polymarket_alpha_lab/manual_review_queue.py, tests/test_manual_review_queue.py, tests/test_manual_review_queue_scope.py'
  expected_untracked=$(printf '%s\n' docs/superpowers/plans/2026-06-14-level-1b-paper-manual-review-queue.md src/polymarket_alpha_lab/manual_review_queue.py tests/test_manual_review_queue.py tests/test_manual_review_queue_scope.py | sort)
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
  for path in docs/superpowers/plans/2026-06-14-level-1b-paper-manual-review-queue.md src/polymarket_alpha_lab/manual_review_queue.py tests/test_manual_review_queue.py tests/test_manual_review_queue_scope.py; do
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

Accepted result: explicit `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed` or `Verdict: Proceed with fixes`.

If the full self-contained implementation review prompt is blocked by transport/proxy truncation before Claude can see the implementation files and verification output, rerun a compact implementation review prompt that still includes:

- The relevant repository instructions from `AGENTS.md`.
- A concise Node 6 contract summary covering paper-only scope, allowed files, allowed imports, public exports, status semantics, duplicate rules, sorting rules, filtering rules, JSONL safety, and forbidden surfaces.
- Fresh verification output for the focused tests, scope tests, full suite, `git diff --check`, and `codegraph status .`.
- `git status --short --branch --untracked-files=all`.
- Full content for every modified or untracked file in this Node 6 change set.
- The same required count lines and verdict policy.

The compact rerun is accepted only under the same terminal condition: explicit `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed` or `Verdict: Proceed with fixes`.

- [ ] **Step 3: Stage files and run cached diff check**

Run:

```bash
git add README.md src/polymarket_alpha_lab/__init__.py src/polymarket_alpha_lab/manual_review_queue.py tests/test_manual_review_queue.py tests/test_manual_review_queue_scope.py tests/test_init.py docs/superpowers/plans/2026-06-14-level-1b-paper-manual-review-queue.md
git diff --cached --check
```

Expected: no output and exit code 0.

- [ ] **Step 4: Record Handoff Summary, restage plan, rerun cached diff check**

Append:

```text
## Handoff Summary

- Repo status: branch, latest commit SHA before final commit, pushed/not pushed, clean/dirty state.
- Git status output: paste `git status --short --branch --untracked-files=all`.
- Verified commands:
  - `git status --short --branch --untracked-files=all`: pass/fail and notable output.
  - `.venv/bin/python -m pytest tests/test_manual_review_queue.py tests/test_manual_review_queue_scope.py tests/test_init.py -q`: pass/fail and test count.
  - `.venv/bin/python -m pytest tests/test_manual_review_queue_scope.py -q`: pass/fail and test count.
  - `.venv/bin/python -m pytest tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py -q`: pass/fail and test count.
  - `.venv/bin/python -m pytest -q`: pass/fail and test count.
  - `git diff --check`: pass/fail.
  - `codegraph status .`: up to date or stale.
  - `codegraph sync .`: run/not run and result.
  - follow-up `codegraph status .`: up to date or stale.
  - `git diff --cached --check`: pass/fail.
- Untracked files: list or `none`.
- Uncommitted files: list or `none`.
- Data-integrity checks: paper-only scope, forbidden-surface static tests, caller-supplied artifacts only, duplicate candidate key rejection, duplicate market-score key rejection, deterministic sorting, status derivation, finite Decimal math, UTC normalization, JSONL validation-before-open behavior.
- Claude review: model `claude-opus-4-8`, effort `max`, review scope, explicit verdict, unresolved findings.
- Commit/push: commit hash `pending final commit`; remote branch `origin/main`; push result `pending final push`.
- Next step: one concrete next action for the next roadmap node.
```

Then run:

```bash
git add docs/superpowers/plans/2026-06-14-level-1b-paper-manual-review-queue.md
git diff --cached --check
```

- [ ] **Step 5: Commit and push**

This project's established node workflow commits directly to `main` and pushes to `origin/main`; use the same target for Node 6.

Run:

```bash
git commit -m "feat: add paper manual review queue"
git push
git status --short --branch --untracked-files=all
```

Expected: commit succeeds, push updates `origin/main`, and final status is exactly `## main...origin/main` with no additional file lines.

## Handoff Summary

- Repo status before final commit: branch `main`, latest commit before Node 6 final commit `f7f088576476c84ca0a1ef65a6b944190026bfb6` (`feat: add paper forecast evidence reports`), not yet pushed for this Node 6 change, dirty with expected modified and untracked files.
- Git status output before staging:
  ```text
  ## main...origin/main
   M AGENTS.md
   M README.md
   M src/polymarket_alpha_lab/__init__.py
   M tests/test_init.py
  ?? docs/superpowers/plans/2026-06-14-level-1b-paper-manual-review-queue.md
  ?? src/polymarket_alpha_lab/manual_review_queue.py
  ?? tests/test_manual_review_queue.py
  ?? tests/test_manual_review_queue_scope.py
  ```
- Verified commands:
  - `git status --short --branch --untracked-files=all`: pass; output listed the expected 4 modified tracked files and 4 untracked Node 6 files.
  - `.venv/bin/python -m pytest tests/test_manual_review_queue.py tests/test_manual_review_queue_scope.py tests/test_init.py -q`: pass, `27 passed`.
  - `.venv/bin/python -m pytest tests/test_manual_review_queue_scope.py -q`: pass, `6 passed`.
  - `.venv/bin/python -m pytest tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py -q`: pass, `28 passed`.
  - `.venv/bin/python -m pytest -q`: pass, `375 passed`.
  - `git diff --check`: pass, no output.
  - `codegraph status .`: initially stale after source/test additions, then up to date after sync.
  - `codegraph sync .`: run; synced changed files successfully.
  - follow-up `codegraph status .`: up to date.
  - `git diff --cached --check`: pending staging step at handoff-summary append time.
- Untracked files before staging: `docs/superpowers/plans/2026-06-14-level-1b-paper-manual-review-queue.md`, `src/polymarket_alpha_lab/manual_review_queue.py`, `tests/test_manual_review_queue.py`, `tests/test_manual_review_queue_scope.py`.
- Uncommitted files before staging: `AGENTS.md`, `README.md`, `src/polymarket_alpha_lab/__init__.py`, `tests/test_init.py`, plus the four untracked files listed above.
- Data-integrity checks covered: paper-only scope, forbidden-surface static tests, caller-supplied artifacts only, duplicate candidate key rejection after UTC normalization, duplicate queue item id rejection, duplicate market-score key rejection, missing market score allowed, extra market score ignored, deterministic sorting, status derivation precedence, queue status and filtered aggregate behavior, finite Decimal validation and string JSON serialization, UTC normalization, append-only JSONL validation-before-open behavior, root exports, README documentation, and project-level agent-memory persistence.
- Claude review: compact implementation review rerun used model `claude-opus-4-8` with effort `max` after the first full prompt was blocked by transport truncation. Review scope included repository instructions, Node 6 contract summary, fresh verification output, git status, CodeGraph status, and full content for every modified/untracked file. Result: `Critical findings: 0`, `Important findings: 0`, `Minor findings: 0`, `Verdict: Proceed`.
- Commit/push: commit hash `pending final commit`; remote branch `origin/main`; push result `pending final push`.
- Next step: start the next roadmap node by planning Level 2 proposal packet boundaries with the same Claude plan-review gate before any proposal-related implementation.
