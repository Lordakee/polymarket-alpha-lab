# Level 2 Proposal Review Summary Reports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Level 2 Node 3 proposal-review summary reports that track supplied human-review outcomes and rejected proposal reason patterns without creating an approval workflow, execution workflow, broker handoff, manual execution import, or live-order surface.

**Architecture:** Add a new pure derived-artifact module, `proposal_review_summary.py`, over caller-supplied `TradeProposalReviewRecord` values. It reconstructs each supplied record to validate integrity, computes deterministic review counts and breakdown rows, emits frozen report dataclasses, and optionally appends report snapshots to JSONL. The module is report-only and has no readers, loaders, API clients, browser automation, account state, credentials, order payloads, execution lifecycle, or approval routing.

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
   - Functional-test worker owns `tests/test_proposal_review_summary.py`.
   - Scope/export-test worker owns `tests/test_proposal_review_summary_scope.py`, `tests/test_init.py`, and the root-export allowlists in existing scope tests.
   - Main integrator owns `src/polymarket_alpha_lab/proposal_review_summary.py`, `src/polymarket_alpha_lab/__init__.py`, `README.md`, and this plan.
   - Codex subagents use model `gpt-5.5` with reasoning effort `xhigh`, matching `AGENTS.md`.
5. Do not let two agents edit the same file or same tightly coupled file batch at the same time.
6. Close completed subagents promptly, then redeploy only to a fresh independent task.
7. Before commit, run fresh local verification and a self-contained Claude implementation review covering all modified and untracked files.
8. Resolve every Critical or Important implementation-review finding before staging for final commit.
9. Append a Handoff Summary to this plan before final commit.
10. Commit and push only after all gates pass.

## Plan Review Command Before Any Implementation

Run this exact self-contained command before implementation:

```bash
{
  printf '%s\n' 'Review this Level 2 proposal-review-summary implementation plan for polymarket-alpha-lab before implementation.'
  printf '%s\n' 'This is a read-only, self-contained plan review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, roadmap/spec material, validation gates, existing tests, or plan text.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; plan is implementable as written.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing required review material, unsafe scope, or plan ambiguity that could cause incorrect implementation.'
  printf '%s\n' 'Review specifically: Level 2 proposal-review summary boundary, report-only semantics, no approval workflow engine, no approval queue/router, no broker/request/client surfaces, no private-key handling, no automatic credential use, no account authentication, no unattended execution, no live order placement, no order lifecycle/reconciliation/settlement surfaces, no manual execution import, no scraping/browser automation, no compliance/legal/geographic analysis, supplied TradeProposalReviewRecord validation, rejected proposal tracking, false-positive proxy wording, duplicate source proposal counting without latest-decision selection, deterministic ordering, Decimal and UTC validation, JSONL validate-before-open behavior, public API/export surface, root-export scope-test migration, TDD steps, CodeGraph usage, verification gates, implementation-review self-containment, untracked-file handling, Handoff Summary, and commit/push order.'
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
  sed -n '97,130p' docs/research/validation-gates.md
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'CodeGraph status:'
  codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Current proposal review source contract:'
  codegraph node src/polymarket_alpha_lab/proposal_review.py
  codegraph node tests/test_proposal_review.py
  codegraph node tests/test_proposal_review_scope.py
  printf '%s\n' ''
  printf '%s\n' 'Current report/log patterns:'
  codegraph node src/polymarket_alpha_lab/analytics_history.py
  codegraph node src/polymarket_alpha_lab/forecast_evidence.py
  printf '%s\n' ''
  printf '%s\n' 'Current package root and export tests:'
  codegraph node src/polymarket_alpha_lab/__init__.py
  codegraph node tests/test_init.py
  printf '%s\n' ''
  printf '%s\n' 'Current root-export scope tests that must be migrated safely:'
  codegraph node tests/test_proposal_packet_scope.py
  codegraph node tests/test_proposal_review_scope.py
  sed -n '1,340p' tests/test_analytics_scope.py
  sed -n '1,340p' tests/test_analytics_history_scope.py
  sed -n '1,340p' tests/test_forecast_evidence_scope.py
  sed -n '1,365p' tests/test_manual_review_queue_scope.py
  printf '%s\n' ''
  printf '%s\n' 'Plan under review:'
  cat docs/superpowers/plans/2026-06-14-level-2-proposal-review-summary-reports.md
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted plan-review terminal state: a fresh Claude review response that explicitly reports `Critical findings: 0`, `Important findings: 0`, and a verdict of `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count line, ambiguous verdict, unsafe scope, missing repository instructions, missing Level 2 context, missing plan text, or transport failure is treated as `Blocked`. After fixing any Critical or Important plan-review finding, rerun the same self-contained Claude plan-review prompt and do not implement until the rerun reaches an accepted terminal state.

If the full prompt is blocked by transport size, rerun a compact prompt that still includes `AGENTS.md`, the Level 2 roadmap excerpt, Gate 6 and Gate 7 excerpts, fresh git status, the full `TradeProposalReviewRecord` public contract, current package-root exports, current export tests, all root-export scope-test snippets, the full target plan text, and the same count/verdict policy.

## Level 2 Node 3 Scope

Level 2 Node 3 adds append-only proposal-review summary report artifacts over supplied `TradeProposalReviewRecord` values. A proposal-review summary tracks proposal review volume, human approved/rejected counts, rejected proposal reason-code concentration, duplicate source proposal review volume, strategy/market/risk-tag review breakdowns, and report-only status. It is audit/reporting material only and does not select trades, route approval, promote strategies, import executions, place orders, or operate accounts.

The module must:

- Consume only caller-supplied `TradeProposalReviewRecord` values.
- Reconstruct each supplied review record before summarizing so mutated frozen objects or wrong types fail before report construction or log writes.
- Sort records deterministically by UTC `recorded_at`, then `review_record_id`.
- Reject duplicate `review_record_id` values.
- Count duplicate `source_proposal_packet_id` occurrences without selecting a latest decision or resolving conflicts.
- Track approved and rejected review decision counts.
- Track rejected reason-code frequencies over rejected records only.
- Track grouped review counts for `market_slug`, `strategy_type`, and each `risk_tags` value.
- Expose `rejection_ratio` as `rejected_decision_count / review_record_count` quantized to `Decimal("0.0001")`, or `None` when there are no records.
- Expose reason-code row ratios as `rejected_decision_count / total_rejected_decision_count` quantized to `Decimal("0.0001")`.
- Expose bucket row ratios as `rejected_decision_count / review_record_count in that bucket` quantized to `Decimal("0.0001")`.
- Emit frozen report dataclasses.
- Persist report snapshots through `TradeProposalReviewSummaryLog(path).append(report)` using append-only JSONL.
- Serialize `Decimal` values as exact strings and datetimes as UTC ISO strings.
- Validate before opening or writing JSONL files.

The module must not:

- Add an approval workflow engine, approval queue, approval router, approver registry, role-based permissions, reviewer authentication, identity verification, latest-decision resolver, or finalization state machine.
- Convert approved records into order instructions, order requests, broker requests, execution decisions, order lifecycle states, or strategy-promotion signals.
- Import manual execution journals, manual execution results, fill outcomes, realized slippage, or post-trade matching data.
- Fetch market, order-book, price-history, outcome, account, credential, or identity data.
- Read JSONL logs or external history.
- Scrape websites, run browser automation, bypass anti-bot controls, or handle CAPTCHA.
- Authenticate, handle credentials, handle private keys, sign messages, use wallets, or use trading SDKs.
- Create broker clients, transport clients, request payloads, response objects, sessions, WebSockets, heartbeats, reconciliation, settlement, or account-state surfaces.
- Place, submit, sign, send, create, or cancel orders.
- Add CLI, UI, dashboard, scheduler, notification, compliance, legal, jurisdiction, geofence, KYC, AML, sanctions, or geographic-access analysis surfaces.

## Target File Structure

Create:

- `src/polymarket_alpha_lab/proposal_review_summary.py`
- `tests/test_proposal_review_summary.py`
- `tests/test_proposal_review_summary_scope.py`
- `docs/superpowers/plans/2026-06-14-level-2-proposal-review-summary-reports.md`

Modify:

- `src/polymarket_alpha_lab/__init__.py`
- `tests/test_init.py`
- `tests/test_analytics_scope.py`
- `tests/test_analytics_history_scope.py`
- `tests/test_forecast_evidence_scope.py`
- `tests/test_manual_review_queue_scope.py`
- `tests/test_proposal_packet_scope.py`
- `tests/test_proposal_review_scope.py`
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

## Public API Contract

`src/polymarket_alpha_lab/proposal_review_summary.py` must export exactly:

```python
__all__ = (
    "TradeProposalReviewBucketSummary",
    "TradeProposalReviewReasonCodeSummary",
    "TradeProposalReviewSummaryConfig",
    "TradeProposalReviewSummaryLog",
    "TradeProposalReviewSummaryReport",
    "build_trade_proposal_review_summary_report",
)
```

### Boundary Statement

`DEFAULT_REVIEW_SUMMARY_BOUNDARY_STATEMENT` must be exactly:

```python
(
    "This is a report-only proposal-review summary artifact, not an approval "
    "workflow, trade instruction, order instruction, broker request, order "
    "request, account action, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflow, manual "
    "execution import, strategy-promotion signal, or automatic order-placement "
    "authorization."
)
```

Boundary statement validation must require these lowercase substrings:

- `report-only`
- `proposal-review summary`
- `not an approval workflow`
- `trade instruction`
- `order instruction`
- `broker request`
- `order request`
- `account action`
- `account authentication`
- `private-key handling`
- `wallet signature`
- `live-execution signal`
- `credential workflow`
- `manual execution import`
- `strategy-promotion signal`
- `automatic order-placement authorization`

### TradeProposalReviewSummaryConfig

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewSummaryConfig:
    config_version: str
    min_review_record_count: int = 1
    max_rejection_ratio: Decimal = Decimal("1.0000")
    boundary_statement: str = DEFAULT_REVIEW_SUMMARY_BOUNDARY_STATEMENT
```

Validation:

- `config_version` and `boundary_statement` must be canonical nonblank strings.
- `min_review_record_count` must be a nonnegative `int`, not `bool`.
- `max_rejection_ratio` must be a finite `Decimal` between `0` and `1`.
- `boundary_statement` must satisfy the boundary statement contract above.

### TradeProposalReviewReasonCodeSummary

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewReasonCodeSummary:
    reason_code: str
    rejected_decision_count: int
    rejected_source_proposal_count: int
    rejected_decision_ratio: Decimal
```

Validation:

- `reason_code` must be a canonical nonblank string.
- `rejected_decision_count` and `rejected_source_proposal_count` must be positive `int` values, not `bool`.
- `rejected_decision_ratio` must be a finite `Decimal` between `0` and `1`.

### TradeProposalReviewBucketSummary

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewBucketSummary:
    bucket_type: str
    bucket_value: str
    review_record_count: int
    unique_source_proposal_count: int
    approved_decision_count: int
    rejected_decision_count: int
    rejection_ratio: Decimal
```

Validation:

- `bucket_type` must be one of `("market_slug", "strategy_type", "risk_tag")`.
- `bucket_value` must be a canonical nonblank string.
- `review_record_count` and `unique_source_proposal_count` must be positive `int` values, not `bool`.
- `approved_decision_count` and `rejected_decision_count` must be nonnegative `int` values, not `bool`.
- `review_record_count == approved_decision_count + rejected_decision_count`.
- `unique_source_proposal_count <= review_record_count`.
- `rejection_ratio` must equal `rejected_decision_count / review_record_count` quantized to `Decimal("0.0001")`.

### TradeProposalReviewSummaryReport

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewSummaryReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    review_record_count: int
    unique_source_proposal_count: int
    duplicate_source_proposal_count: int
    first_recorded_at: datetime | None
    last_recorded_at: datetime | None
    approved_decision_count: int
    rejected_decision_count: int
    rejection_ratio: Decimal | None
    status: str
    reason_code_summaries: tuple[TradeProposalReviewReasonCodeSummary, ...]
    bucket_summaries: tuple[TradeProposalReviewBucketSummary, ...]
```

Validation:

- `generated_at`, `first_recorded_at`, and `last_recorded_at` are normalized to UTC.
- `config_version` must be a canonical nonblank string.
- `report_only` must be `True`.
- `boundary_statement` must satisfy the boundary statement contract above.
- `review_record_count`, `unique_source_proposal_count`, `duplicate_source_proposal_count`, `approved_decision_count`, and `rejected_decision_count` must be nonnegative `int` values, not `bool`.
- `review_record_count == approved_decision_count + rejected_decision_count`.
- `duplicate_source_proposal_count == review_record_count - unique_source_proposal_count`.
- `unique_source_proposal_count <= review_record_count`.
- If `review_record_count == 0`, `first_recorded_at`, `last_recorded_at`, and `rejection_ratio` must be `None`; `reason_code_summaries` and `bucket_summaries` must be empty.
- If `review_record_count > 0`, `first_recorded_at`, `last_recorded_at`, and `rejection_ratio` must be present, `first_recorded_at <= last_recorded_at`, and `rejection_ratio` must equal `rejected_decision_count / review_record_count` quantized to `Decimal("0.0001")`.
- `status` must be one of `("insufficient_review_sample", "high_rejection_ratio", "summary_ready")`.
- `reason_code_summaries` must be a tuple of `TradeProposalReviewReasonCodeSummary` values sorted by `reason_code`.
- `bucket_summaries` must be a tuple of `TradeProposalReviewBucketSummary` values sorted by `(bucket_type, bucket_value)`.

### Builder Contract

```python
def build_trade_proposal_review_summary_report(
    records: Iterable[TradeProposalReviewRecord],
    *,
    config: TradeProposalReviewSummaryConfig,
    generated_at: datetime,
) -> TradeProposalReviewSummaryReport:
    ...
```

Builder behavior:

- Reject `records` when it is a `str` or `bytes`.
- Convert `records` to a tuple exactly once and raise `ValueError("records must be an iterable of TradeProposalReviewRecord values")` for non-iterables.
- Reject non-`TradeProposalReviewRecord` elements.
- Reconstruct each record through `TradeProposalReviewRecord(...)` with every public field copied from the supplied record before summarizing.
- Reject duplicate `review_record_id` values with `ValueError("duplicate review_record_id values are not allowed")`.
- Reject non-`TradeProposalReviewSummaryConfig` config values.
- Reject non-`datetime` `generated_at` values.
- Normalize `generated_at` and record timestamps to UTC.
- Sort validated records by `(_as_utc(record.recorded_at), record.review_record_id)`.
- Do not collapse records by `source_proposal_packet_id`; count duplicates only.
- Build `reason_code_summaries` from rejected records only. For each reason code:
  - `rejected_decision_count` is the number of rejected records containing that reason code.
  - `rejected_source_proposal_count` is the number of unique `source_proposal_packet_id` values among those rejected records.
  - `rejected_decision_ratio` is reason-code rejected count divided by total rejected count, quantized to `Decimal("0.0001")`.
- Build `bucket_summaries` for these bucket types:
  - one `market_slug` row per record market slug
  - one `strategy_type` row per record strategy type
  - one `risk_tag` row per distinct risk tag on each record
- Sort reason-code rows by `reason_code`.
- Sort bucket rows by `(bucket_type, bucket_value)`.
- Determine `status`:
  - `insufficient_review_sample` when `review_record_count < config.min_review_record_count`
  - `high_rejection_ratio` when there is a rejection ratio and it is greater than `config.max_rejection_ratio`
  - `summary_ready` otherwise

### Log Contract

`TradeProposalReviewSummaryLog(path).append(report)`:

- Accepts only `TradeProposalReviewSummaryReport`.
- Reconstructs and validates the report tree before serialization.
- Serializes with `json.dumps(_json_ready(asdict(report)), allow_nan=False, sort_keys=True) + "\n"`.
- Uses append-only mode.
- Creates missing parent directories only after validation and serialization have succeeded.
- Revalidates the nearest existing parent before opening the file.
- Does not expose a reader, loader, updater, deleter, importer, exporter, dispatcher, replay API, external-history API, or manual-execution import.

## Task 1: Functional Tests

**Files:**
- Create: `tests/test_proposal_review_summary.py`

- [x] **Step 1: Write the failing import and fixture stack**

Create `tests/test_proposal_review_summary.py` by duplicating the local fixture stack from `tests/test_proposal_review.py`:

- Imports: `json`, `FrozenInstanceError`, `replace`, `UTC`, `datetime`, `timedelta`, `timezone`, `Decimal`, `pytest`.
- Existing fixture helpers copied locally: `market_score`, `ready_history_report`, `forecast_observation`, `ready_forecast_report`, `candidate`, `ready_queue_item`, `proposal_packet`, `review_record`.
- New imports from `polymarket_alpha_lab.proposal_review_summary`:

```python
from polymarket_alpha_lab.proposal_review_summary import (
    TradeProposalReviewBucketSummary,
    TradeProposalReviewReasonCodeSummary,
    TradeProposalReviewSummaryConfig,
    TradeProposalReviewSummaryLog,
    build_trade_proposal_review_summary_report,
)
```

Append this first failing test:

```python
def summary_report(records, **overrides):
    values = {
        "records": records,
        "config": TradeProposalReviewSummaryConfig(config_version="summary-v1"),
        "generated_at": datetime(2026, 9, 4, 9, tzinfo=timezone(timedelta(hours=-4))),
    }
    values.update(overrides)
    return build_trade_proposal_review_summary_report(**values)


def test_build_trade_proposal_review_summary_report_counts_review_outcomes():
    approved = review_record(recorded_at=datetime(2026, 9, 3, 12, tzinfo=UTC))
    rejected = review_record(
        decision="rejected",
        review_reason_codes=("liquidity_exit_risk", "resolution_ambiguity"),
        review_rationale="Rejected after checking exit depth and resolution language.",
        recorded_at=datetime(2026, 9, 3, 8, 30, tzinfo=timezone(timedelta(hours=-4))),
    )

    report = summary_report([rejected, approved])

    assert report.generated_at == datetime(2026, 9, 4, 13, tzinfo=UTC)
    assert report.config_version == "summary-v1"
    assert report.report_only is True
    assert report.review_record_count == 2
    assert report.unique_source_proposal_count == 1
    assert report.duplicate_source_proposal_count == 1
    assert report.first_recorded_at == datetime(2026, 9, 3, 12, tzinfo=UTC)
    assert report.last_recorded_at == datetime(2026, 9, 3, 12, 30, tzinfo=UTC)
    assert report.approved_decision_count == 1
    assert report.rejected_decision_count == 1
    assert report.rejection_ratio == Decimal("0.5000")
    assert report.status == "summary_ready"
    assert tuple(row.reason_code for row in report.reason_code_summaries) == (
        "liquidity_exit_risk",
        "resolution_ambiguity",
    )
    assert tuple((row.bucket_type, row.bucket_value) for row in report.bucket_summaries) == (
        ("market_slug", "market-1"),
        ("risk_tag", "event-risk"),
        ("risk_tag", "liquidity"),
        ("strategy_type", "relative_value"),
    )
```

- [x] **Step 2: Run the first failing test**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_summary.py::test_build_trade_proposal_review_summary_report_counts_review_outcomes -q
```

Expected: FAIL during import with `ModuleNotFoundError` or `ImportError` because `proposal_review_summary.py` does not exist yet.

- [x] **Step 3: Add remaining failing functional tests**

Add these tests in `tests/test_proposal_review_summary.py`:

- `test_trade_proposal_review_summary_report_statuses_cover_sample_and_rejection_thresholds`
  - Empty records with `min_review_record_count=1` produce count `0`, `rejection_ratio is None`, empty row tuples, and status `insufficient_review_sample`.
  - One rejected record with `max_rejection_ratio=Decimal("0.2500")` produces status `high_rejection_ratio`.
  - One approved record with the same config produces status `summary_ready`.
- `test_trade_proposal_review_summary_reason_rows_are_rejected_only_and_deterministic`
  - Two rejected records with overlapping reason codes produce sorted reason-code rows.
  - Approved records with empty reason codes do not add reason rows.
  - `rejected_decision_ratio` values are quantized to four places.
- `test_trade_proposal_review_summary_bucket_rows_count_market_strategy_and_risk_tags`
  - Records from two markets and two risk-tag combinations produce deterministic `market_slug`, `strategy_type`, and `risk_tag` rows.
  - Each bucket row has correct approved/rejected counts, unique source proposal count, and rejection ratio.
- `test_trade_proposal_review_summary_rejects_bad_inputs_and_duplicates`
  - Non-iterable `records`, string `records`, non-record element, non-config config, non-datetime `generated_at`, and duplicate `review_record_id` all raise `ValueError`.
- `test_trade_proposal_review_summary_revalidates_mutated_records`
  - Mutate `maximum_size` to `Decimal("NaN")` through `object.__setattr__`; builder raises before summarizing.
  - Mutate `review_record_id` to `"bad"`; builder raises before summarizing.
- `test_trade_proposal_review_summary_dataclasses_are_frozen_and_validate_invariants`
  - `TradeProposalReviewSummaryConfig`, `TradeProposalReviewReasonCodeSummary`, `TradeProposalReviewBucketSummary`, and `TradeProposalReviewSummaryReport` are frozen.
  - `replace(...)` rejects invalid counts, invalid status, unsorted rows, wrong ratio, `report_only=False`, and invalid boundary text.
- `test_trade_proposal_review_summary_boundary_statement_contract`
  - The default boundary statement equals the contract in this plan.
  - Incomplete boundary statements raise `ValueError`.
- `test_trade_proposal_review_summary_log_appends_jsonl_report`
  - Append one report and assert JSON values: `generated_at`, `report_only`, `review_record_count`, `rejection_ratio` as string, nested reason rows, and nested bucket rows.
- `test_trade_proposal_review_summary_log_appends_without_overwriting_and_creates_parent_dirs`
  - Append the same report twice to a nested path and assert two JSONL lines.
- `test_trade_proposal_review_summary_log_rejects_invalid_paths_and_inputs`
  - Reject non-path path, blank path, existing directory path, parent-file path, and non-report append input.
- `test_trade_proposal_review_summary_log_preserves_existing_file_when_validation_fails`
  - Mutate a report field to `Decimal("NaN")`, append to an existing file, assert content is unchanged.
- `test_trade_proposal_review_summary_log_rejects_non_finite_decimal_before_open`
  - Mutate `rejection_ratio` to `Decimal("NaN")`, append to a missing file, assert file does not exist.

- [x] **Step 4: Run the full new functional test file and keep the expected failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_summary.py -q
```

Expected: FAIL because the new module and public API do not exist yet.

## Task 2: Scope And Export Tests

**Files:**
- Create: `tests/test_proposal_review_summary_scope.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_analytics_scope.py`
- Modify: `tests/test_analytics_history_scope.py`
- Modify: `tests/test_forecast_evidence_scope.py`
- Modify: `tests/test_manual_review_queue_scope.py`
- Modify: `tests/test_proposal_packet_scope.py`
- Modify: `tests/test_proposal_review_scope.py`

- [x] **Step 1: Add the new module scope test**

Create `tests/test_proposal_review_summary_scope.py` with the AST helper structure used by `tests/test_proposal_review_scope.py`.

Use these expected exports:

```python
EXPECTED_PROPOSAL_REVIEW_SUMMARY_EXPORTS = {
    "TradeProposalReviewBucketSummary",
    "TradeProposalReviewReasonCodeSummary",
    "TradeProposalReviewSummaryConfig",
    "TradeProposalReviewSummaryLog",
    "TradeProposalReviewSummaryReport",
    "build_trade_proposal_review_summary_report",
}
```

Use these allowed imports:

```python
ALLOWED_IMPORT_PREFIXES = {
    "__future__",
    "json",
    "collections",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
    "polymarket_alpha_lab.proposal_review",
}
```

Use this first-party symbol allowlist:

```python
EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.proposal_review": {"TradeProposalReviewRecord"},
}
```

The forbidden import prefixes must include at least:

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

Use compound forbidden name fragments so intended inert review-summary names survive:

```python
FORBIDDEN_NAME_FRAGMENTS = (
    "privatekey",
    "privkey",
    "apikey",
    "secret",
    "credentialrequest",
    "credentialworkflow",
    "credentialstore",
    "credentialmanager",
    "credentialprovider",
    "credentialloader",
    "password",
    "mnemonic",
    "seedphrase",
    "accountaction",
    "accountauthentication",
    "accountlogin",
    "accountsession",
    "accountstate",
    "accountposition",
    "accountbalance",
    "bearertoken",
    "jwttoken",
    "walletsignature",
    "walletsigner",
    "walletclient",
    "signedorder",
    "signorder",
    "signmessage",
    "signtransaction",
    "placeorder",
    "createorder",
    "cancelorder",
    "submitorder",
    "sendorder",
    "orderinstruction",
    "orderrequest",
    "orderpayload",
    "orderplacement",
    "orderlifecycle",
    "ordermanager",
    "orderrouter",
    "tradeinstruction",
    "executionclient",
    "executiondecision",
    "executionengine",
    "executionqueue",
    "executionrequest",
    "executionrouter",
    "executionworkflow",
    "liveexecution",
    "approvalworkflow",
    "approvalqueue",
    "approvalrouter",
    "approvalbroker",
    "approvalstatus",
    "approvedby",
    "approvedat",
    "autoapproval",
    "autoapprove",
    "automaticapproval",
    "unattendedapproval",
    "approver",
    "brokerclient",
    "brokerrequest",
    "tradingbroker",
    "tradingclient",
    "transportclient",
    "transportrequest",
    "httpclient",
    "marketclient",
    "requestpayload",
    "requestbody",
    "requestparams",
    "responsebody",
    "urlopen",
    "getjson",
    "fetchmarket",
    "fetchorderbook",
    "fetchpricehistory",
    "fetchoutcome",
    "fetchaccount",
    "websocket",
    "heartbeat",
    "reconciler",
    "reconciliation",
    "exchangeaccount",
    "clobclient",
    "tradesdk",
    "settlement",
    "settle",
    "manualexecution",
    "manualexecutionimport",
    "resolvedoutcome",
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
    "compliance",
    "legal",
    "jurisdiction",
    "geofence",
    "geographic",
    "geoblock",
    "kyc",
    "aml",
    "sanction",
)
```

Tests to include:

- `test_proposal_review_summary_module_imports_only_allowed_dependencies`
- `test_proposal_review_summary_module_does_not_import_forbidden_surfaces`
- `test_proposal_review_summary_module_uses_only_allowed_first_party_symbols`
- `test_proposal_review_summary_module_does_not_define_forbidden_live_or_workflow_names`
- `test_trade_proposal_review_summary_public_exports_are_report_only`
- `test_package_root_exports_do_not_leak_forbidden_level_2_node_3_surfaces`

`test_trade_proposal_review_summary_public_exports_are_report_only` must assert exact module export equality and per-name shape:

```python
assert set(assigned_exports) == EXPECTED_PROPOSAL_REVIEW_SUMMARY_EXPORTS
for name in assigned_exports:
    assert name.startswith("TradeProposalReview") or name == (
        "build_trade_proposal_review_summary_report"
    )
```

- [x] **Step 2: Update package export tests**

In `tests/test_init.py`, import the six new public objects from `polymarket_alpha_lab.proposal_review_summary` and add:

```python
def test_level_2_node_3_public_api_exports():
    expected_exports = {
        "TradeProposalReviewBucketSummary",
        "TradeProposalReviewReasonCodeSummary",
        "TradeProposalReviewSummaryConfig",
        "TradeProposalReviewSummaryLog",
        "TradeProposalReviewSummaryReport",
        "build_trade_proposal_review_summary_report",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.TradeProposalReviewBucketSummary is TradeProposalReviewBucketSummary
    assert lab.TradeProposalReviewReasonCodeSummary is TradeProposalReviewReasonCodeSummary
    assert lab.TradeProposalReviewSummaryConfig is TradeProposalReviewSummaryConfig
    assert lab.TradeProposalReviewSummaryLog is TradeProposalReviewSummaryLog
    assert lab.TradeProposalReviewSummaryReport is TradeProposalReviewSummaryReport
    assert (
        lab.build_trade_proposal_review_summary_report
        is build_trade_proposal_review_summary_report
    )
```

- [x] **Step 3: Update existing root-export scope allowlists**

In these files, add `EXPECTED_PROPOSAL_REVIEW_SUMMARY_EXPORTS` with the six exports above and include it in `EXPECTED_LEVEL_2_ARTIFACT_EXPORTS`:

- `tests/test_analytics_scope.py`
- `tests/test_analytics_history_scope.py`
- `tests/test_forecast_evidence_scope.py`
- `tests/test_manual_review_queue_scope.py`
- `tests/test_proposal_packet_scope.py`
- `tests/test_proposal_review_scope.py`

Keep existing forbidden-fragment checks intact. Do not weaken unrelated scope tests.

- [x] **Step 4: Run the new and changed scope/export tests and keep the expected failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_summary_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py -q
```

Expected: FAIL because the implementation module and package-root exports do not exist yet.

## Task 3: Implement Proposal Review Summary Module

**Files:**
- Create: `src/polymarket_alpha_lab/proposal_review_summary.py`

- [x] **Step 1: Create the module shell and public dataclasses**

Create `src/polymarket_alpha_lab/proposal_review_summary.py` with:

- Standard-library imports only: `json`, `defaultdict`, `Iterable`, `asdict`, `dataclass`, `UTC`, `datetime`, `Decimal`, `ROUND_HALF_EVEN`, `Path`, `Any`.
- First-party import only: `from polymarket_alpha_lab.proposal_review import TradeProposalReviewRecord`.
- Constants:
  - `RATIO_QUANTUM = Decimal("0.0001")`
  - `ZERO = Decimal("0")`
  - `ONE = Decimal("1")`
  - `REPORT_STATUSES = ("insufficient_review_sample", "high_rejection_ratio", "summary_ready")`
  - `BUCKET_TYPES = ("market_slug", "strategy_type", "risk_tag")`
  - the default boundary statement from this plan.
- The six public exports from the Public API Contract section.
- Frozen dataclasses from the Public API Contract section.

- [x] **Step 2: Implement validation helpers**

Implement helpers consistent with `proposal_review.py` and existing report modules:

- `_as_utc(value: datetime) -> datetime`
- `_require_canonical_string(field_name: str, value: str) -> None`
- `_require_boundary_statement(value: str) -> None`
- `_require_int(field_name: str, value: int) -> None`
- `_require_nonnegative_int(field_name: str, value: int) -> None`
- `_require_positive_int(field_name: str, value: int) -> None`
- `_require_decimal(field_name: str, value: Decimal) -> None`
- `_require_probability_decimal(field_name: str, value: Decimal) -> None`
- `_require_optional_probability_decimal(field_name: str, value: Decimal | None) -> None`
- `_quantize_ratio(value: Decimal) -> Decimal`
- `_ratio_or_none(numerator: int, denominator: int) -> Decimal | None`
- `_normalize_typed_tuple(field_name: str, values: Iterable[Any], expected_type: type) -> tuple[Any, ...]`

`_quantize_ratio` must use `value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)` and reject non-finite values.

- [x] **Step 3: Implement record/report cloning and JSON helpers**

Implement:

- `_clone_review_record(record: TradeProposalReviewRecord) -> TradeProposalReviewRecord`, reconstructing every public field from `TradeProposalReviewRecord`.
- `_validate_report_tree(report: TradeProposalReviewSummaryReport) -> TradeProposalReviewSummaryReport`, reconstructing config-free nested report dataclasses and returning a validated report.
- `_json_ready(value: Any) -> Any`, matching existing behavior: `Decimal` to `str`, `datetime` to UTC ISO string, reject `float`, recurse into dict/list/tuple, require dict keys to be strings.
- `_normalize_log_path(value: Path | str) -> Path`
- `_validate_log_parent(path: Path) -> None`

The log append method must compute JSON before creating parent directories or opening files.

- [x] **Step 4: Implement summary builders**

Implement:

- `build_trade_proposal_review_summary_report(...)`
- `_build_reason_code_summaries(records: tuple[TradeProposalReviewRecord, ...]) -> tuple[TradeProposalReviewReasonCodeSummary, ...]`
- `_build_bucket_summaries(records: tuple[TradeProposalReviewRecord, ...]) -> tuple[TradeProposalReviewBucketSummary, ...]`
- `_summary_status(review_record_count: int, rejection_ratio: Decimal | None, config: TradeProposalReviewSummaryConfig) -> str`

Use deterministic grouping:

```python
reason_rows = []
for reason_code in sorted(grouped_reason_codes):
    rows = grouped_reason_codes[reason_code]
    reason_rows.append(
        TradeProposalReviewReasonCodeSummary(
            reason_code=reason_code,
            rejected_decision_count=len(rows),
            rejected_source_proposal_count=len({row.source_proposal_packet_id for row in rows}),
            rejected_decision_ratio=_ratio_or_none(len(rows), rejected_total),
        )
    )
```

For bucket summaries, append one row for each `(bucket_type, bucket_value)` key in sorted order. For risk tags, add a record to each of its risk-tag buckets.

- [x] **Step 5: Run focused functional tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_summary.py -q
```

Expected: PASS after implementation.

## Task 4: Package Exports, Scope Migration, And README

**Files:**
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `README.md`

Ownership rule: the scope/export-test worker owns every test file listed in Task 2 while that worker is active. The main integrator must not edit those files concurrently. If the scope/export-test worker is not used, or after it is closed, the main integrator may update any remaining Task 2 files and then becomes their sole writer.

- [x] **Step 1: Export the new API from package root**

In `src/polymarket_alpha_lab/__init__.py`, add:

```python
from polymarket_alpha_lab.proposal_review_summary import (
    TradeProposalReviewBucketSummary,
    TradeProposalReviewReasonCodeSummary,
    TradeProposalReviewSummaryConfig,
    TradeProposalReviewSummaryLog,
    TradeProposalReviewSummaryReport,
    build_trade_proposal_review_summary_report,
)
```

Add the same six names to `__all__` near the existing proposal-review exports.

- [x] **Step 2: Update README status and API sections**

In `README.md`:

- Extend the Phase 1 Scope sentence to mention `proposal-review summary report artifacts`.
- Add `Level 2 Node 3 Status` after Level 2 Node 2:

```markdown
## Level 2 Node 3 Status

Level 2 Node 3 adds report-only proposal-review summary artifacts over supplied `TradeProposalReviewRecord` values. A proposal-review summary tracks review volume, approved/rejected decision counts, rejected proposal reason-code concentration, duplicate source proposal review volume, and market/strategy/risk-tag review breakdowns for audit only; it is not an approval workflow, trade instruction, order instruction, broker request, order request, account action, strategy-promotion signal, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, execution client, or transport client; build broker or order request payloads; reconcile exchange accounts; import manual executions; or perform compliance/legal/geographic analysis.
```

- Add `Level 2 Node 3 Python API`:

```markdown
## Level 2 Node 3 Python API

Node 3 is exposed through Python APIs:

- Configure proposal-review summary boundaries with `TradeProposalReviewSummaryConfig(config_version="summary-v1")`.
- Build proposal-review summary reports with `build_trade_proposal_review_summary_report(records, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalReviewSummaryReport`.
- Inspect reason-code rows with `TradeProposalReviewReasonCodeSummary` and grouped market/strategy/risk-tag rows with `TradeProposalReviewBucketSummary`.
- Persist proposal-review summary snapshots with `TradeProposalReviewSummaryLog(path).append(report)`.
```

- Add `proposal_review_summary.py`, `test_proposal_review_summary.py`, and `test_proposal_review_summary_scope.py` to Repository Layout.
- Add the new plan file to the plans list.

- [x] **Step 3: Run export and scope tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_summary_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py -q
```

Expected: PASS.

## Task 5: Verification, Claude Implementation Review, Handoff, Commit, Push

**Files:**
- Modify: `docs/superpowers/plans/2026-06-14-level-2-proposal-review-summary-reports.md`

- [x] **Step 1: Run local verification**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_summary.py tests/test_proposal_review_summary_scope.py tests/test_init.py -q
.venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py -q
.venv/bin/python -m pytest -q
git diff --check
codegraph sync
codegraph status .
git status --short --branch --untracked-files=all
```

Expected:

- Focused tests PASS.
- Full suite PASS.
- `git diff --check` reports no whitespace errors.
- CodeGraph index is up to date after sync.
- Git status shows only intended modified and untracked files.

- [x] **Step 2: Run implementation review**

Run this self-contained command after implementation and before commit:

```bash
{
  printf '%s\n' 'Review this completed Level 2 proposal-review-summary implementation for polymarket-alpha-lab.'
  printf '%s\n' 'This is a read-only implementation review. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, roadmap/spec material, validation gates, implementation diff, tests, or plan text.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; implementation is ready to commit.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, unsafe scope, failing/missing verification, missing review material, or ambiguity that could cause incorrect behavior.'
  printf '%s\n' 'Review specifically: report-only review-summary boundary, no approval workflow/queue/router, no broker/request/client/order/account/credential surfaces, no live execution, no manual execution import, no scraping/browser automation, no compliance/legal/geographic analysis, validation of supplied TradeProposalReviewRecord values, duplicate review_record_id rejection, duplicate source proposal count semantics, deterministic sorting, reason-code rows over rejected records only, market/strategy/risk-tag bucket rows, Decimal ratio quantization, UTC datetime normalization, JSONL validate-before-open behavior, package exports, scope tests, README updates, local verification output, CodeGraph status, Handoff Summary, and commit readiness.'
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
  sed -n '97,130p' docs/research/validation-gates.md
  printf '%s\n' ''
  printf '%s\n' 'Plan:'
  cat docs/superpowers/plans/2026-06-14-level-2-proposal-review-summary-reports.md
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'CodeGraph status:'
  codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Verification output:'
  printf '%s\n' '$ .venv/bin/python -m pytest tests/test_proposal_review_summary.py tests/test_proposal_review_summary_scope.py tests/test_init.py -q'
  .venv/bin/python -m pytest tests/test_proposal_review_summary.py tests/test_proposal_review_summary_scope.py tests/test_init.py -q
  printf '%s\n' '$ .venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py -q'
  .venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py -q
  printf '%s\n' '$ .venv/bin/python -m pytest -q'
  .venv/bin/python -m pytest -q
  printf '%s\n' '$ git diff --check'
  git diff --check && printf '%s\n' 'git diff --check passed'
  printf '%s\n' ''
  printf '%s\n' 'Tracked diff:'
  git diff -- src/polymarket_alpha_lab/__init__.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py README.md docs/superpowers/plans/2026-06-14-level-2-proposal-review-summary-reports.md
  printf '%s\n' ''
  printf '%s\n' 'Full contents of changed and untracked files:'
  cat src/polymarket_alpha_lab/proposal_review_summary.py
  cat tests/test_proposal_review_summary.py
  cat tests/test_proposal_review_summary_scope.py
  cat src/polymarket_alpha_lab/__init__.py
  cat tests/test_init.py
  cat tests/test_analytics_scope.py
  cat tests/test_analytics_history_scope.py
  cat tests/test_forecast_evidence_scope.py
  cat tests/test_manual_review_queue_scope.py
  cat tests/test_proposal_packet_scope.py
  cat tests/test_proposal_review_scope.py
  cat README.md
  cat docs/superpowers/plans/2026-06-14-level-2-proposal-review-summary-reports.md
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted implementation-review terminal state: a fresh Claude review response that explicitly reports `Critical findings: 0`, `Important findings: 0`, and a verdict of `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count line, ambiguous verdict, unsafe scope, missing tracked diff, missing full contents for changed or untracked files, missing verification, missing repository instructions, missing plan text, or transport failure is treated as `Blocked`.

- [x] **Step 3: Resolve Critical and Important review findings**

If Claude reports any Critical or Important finding:

1. Fix the issue with scoped edits.
2. Rerun the focused tests affected by the fix.
3. Rerun the full verification commands from Task 5 Step 1.
4. Rerun the Claude implementation review command from Task 5 Step 2.
5. Continue until Critical and Important counts are both zero.

- [x] **Step 4: Append final Handoff Summary**

Append a dated Handoff Summary to this plan containing:

- Files changed.
- Verification command outputs.
- Claude plan review counts and verdict.
- Claude implementation review counts and verdict.
- Any remaining Minor findings and why they are non-blocking.
- Next recommended safe node, or explicit stop point if no safe node remains under current constraints.

The Handoff Summary is committed before the final commit hash exists, so it must not claim to contain its own commit hash. Report the final commit hash after commit and push in the assistant final response for the node.

- [x] **Step 5: Commit and push**

Run:

```bash
git add src/polymarket_alpha_lab/proposal_review_summary.py src/polymarket_alpha_lab/__init__.py tests/test_proposal_review_summary.py tests/test_proposal_review_summary_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py README.md docs/superpowers/plans/2026-06-14-level-2-proposal-review-summary-reports.md
git commit -m "feat: add level 2 proposal review summary reports"
git push origin main
```

Expected: commit succeeds and push updates `origin/main`.

## Handoff Summary

### 2026-06-14 Node 3 Handoff Summary

Repo state before final commit:

- Branch: `main`, tracking `origin/main`.
- Base before this node: `bd263d3 feat: add level 2 proposal review records`.
- Dirty files are the intended Node 3 set only.

Files changed:

- Added `src/polymarket_alpha_lab/proposal_review_summary.py`.
- Added `tests/test_proposal_review_summary.py`.
- Added `tests/test_proposal_review_summary_scope.py`.
- Added this plan file, `docs/superpowers/plans/2026-06-14-level-2-proposal-review-summary-reports.md`.
- Modified `src/polymarket_alpha_lab/__init__.py`.
- Modified `tests/test_init.py`.
- Modified root-export scope allowlists in `tests/test_analytics_scope.py`, `tests/test_analytics_history_scope.py`, `tests/test_forecast_evidence_scope.py`, `tests/test_manual_review_queue_scope.py`, `tests/test_proposal_packet_scope.py`, and `tests/test_proposal_review_scope.py`.
- Modified `README.md`.

Verification commands:

- RED functional test: `.venv/bin/python -m pytest tests/test_proposal_review_summary.py::test_build_trade_proposal_review_summary_report_counts_review_outcomes -q` failed during collection with `ModuleNotFoundError: No module named 'polymarket_alpha_lab.proposal_review_summary'`.
- RED scope/export command: `.venv/bin/python -m pytest tests/test_proposal_review_summary_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py -q` failed during collection with the same missing module error.
- Focused functional tests: `.venv/bin/python -m pytest tests/test_proposal_review_summary.py -q` passed with `13 passed`.
- Focused combined tests after final review fix: `.venv/bin/python -m pytest tests/test_proposal_review_summary.py tests/test_proposal_review_summary_scope.py tests/test_init.py -q` passed with `29 passed`.
- Scope/export tests after final review fix: `.venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py -q` passed with `33 passed`.
- Full suite after final review fix: `.venv/bin/python -m pytest -q` passed with `483 passed`.
- Whitespace check: `git diff --check` passed with no output.
- CodeGraph: `codegraph sync` completed after final code change, then `codegraph status .` reported `Index is up to date`.
- Pre-commit status: `git status --short --branch --untracked-files=all` showed only the intended modified files and new Node 3 files.

Review results:

- Plan review: Claude Code `claude-opus-4-8`, effort `max`; final accepted review reported `Critical findings: 0`, `Important findings: 0`, `Minor findings: 4`, `Verdict: Proceed with fixes`.
- Implementation review: per latest thread objective, local opencode with `zhipuai-coding-plan/glm-5.2`; first review reported `Critical findings: 0`, `Important findings: 0`, `Minor findings: 1`, `Verdict: Proceed with fixes`.
- Review fix applied: `_quantize_ratio` now passes `rounding=ROUND_HALF_EVEN` explicitly.
- Implementation re-review: local opencode with `zhipuai-coding-plan/glm-5.2`; final review reported `Critical findings: 0`, `Important findings: 0`, `Minor findings: 0`, `Verdict: Proceed`.
- Remaining Minor findings: none.

Next step:

- Commit and push this Node 3 work to `origin/main`, then pause per user instruction. No next node is started in this handoff.
