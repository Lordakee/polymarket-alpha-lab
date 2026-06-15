# Level 2 Proposal Review Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Level 2 Node 5 proposal-review diagnostic reports that aggregate supplied human-review records into rejected-proposal proxy diagnostics, without confirming realized false positives or touching execution surfaces.

**Architecture:** Add a pure report-only module, `proposal_review_diagnostics.py`, over caller-supplied `TradeProposalReviewRecord` values. It reconstructs each supplied review record to validate integrity, computes deterministic diagnostic reason rows, bucket rows, and rejected-source rows, emits frozen report dataclasses, and optionally appends report snapshots to JSONL. The module has no readers, loaders, approval routers, broker clients, account state, credentials, browser automation, order payloads, manual-execution imports, execution lifecycle, live-order behavior, or realized-outcome matching.

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
   - Functional-test worker owns `tests/test_proposal_review_diagnostics.py`.
   - Scope/export-test worker owns `tests/test_proposal_review_diagnostics_scope.py`, `tests/test_init.py`, and root-export allowlists in existing scope tests.
   - Main integrator owns `src/polymarket_alpha_lab/proposal_review_diagnostics.py`, `src/polymarket_alpha_lab/__init__.py`, `README.md`, and this plan.
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
  printf '%s\n' 'Review this Level 2 proposal-review-diagnostics implementation plan for polymarket-alpha-lab before implementation.'
  printf '%s\n' 'This is a read-only, self-contained plan review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, roadmap/spec material, validation gates, existing tests, or plan text.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; plan is implementable as written.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing required review material, unsafe scope, or plan ambiguity that could cause incorrect implementation.'
  printf '%s\n' 'Review specifically: Level 2 proposal-review diagnostics boundary, report-only semantics, rejected human-review decision as false-positive proxy only, no realized false-positive confirmation, no approval workflow engine, no approval queue/router, no broker/request/client surfaces, no private-key handling, no automatic credential use, no account authentication, no unattended execution, no live order placement, no order lifecycle/reconciliation/settlement surfaces, no manual execution import, no scraping/browser automation, no compliance/legal/geographic analysis, supplied TradeProposalReviewRecord validation, duplicate review_record_id rejection, duplicate source proposal tracking without latest-decision selection, rejected source proposal proxy counts, reason-code diagnostics, bucket diagnostics, source diagnostics, deterministic ordering, Decimal and UTC validation, JSONL validate-before-open behavior, public API/export surface, root-export scope-test migration, TDD steps, CodeGraph usage, verification gates, implementation-review self-containment, untracked-file handling, Handoff Summary, and commit/push order.'
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
  sed -n '97,138p' docs/research/validation-gates.md
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'CodeGraph status:'
  codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Current proposal review record source contract:'
  codegraph node src/polymarket_alpha_lab/proposal_review.py
  codegraph node tests/test_proposal_review.py
  codegraph node tests/test_proposal_review_scope.py
  printf '%s\n' ''
  printf '%s\n' 'Current proposal review summary and quality sibling patterns:'
  codegraph node src/polymarket_alpha_lab/proposal_review_summary.py
  codegraph node tests/test_proposal_review_summary.py
  codegraph node tests/test_proposal_review_summary_scope.py
  codegraph node src/polymarket_alpha_lab/proposal_review_quality.py
  codegraph node tests/test_proposal_review_quality.py
  codegraph node tests/test_proposal_review_quality_scope.py
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
  printf '%s\n' ''
  printf '%s\n' 'Plan under review:'
  cat docs/superpowers/plans/2026-06-14-level-2-proposal-review-diagnostics.md
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted plan-review terminal state: a fresh Claude review response that explicitly reports `Critical findings: 0`, `Important findings: 0`, and a verdict of `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count line, ambiguous verdict, unsafe scope, missing repository instructions, missing Level 2 context, missing plan text, or transport failure is treated as `Blocked`. After fixing any Critical or Important plan-review finding, rerun the same self-contained Claude plan-review prompt and do not implement until the rerun reaches an accepted terminal state.

If the full prompt is blocked by transport size, rerun a compact prompt that still includes `AGENTS.md`, the Level 2 roadmap excerpt, Gate 6 through Gate 8 excerpts, fresh git status, the full `TradeProposalReviewRecord` public contract, current package-root exports, current export tests, all root-export scope-test snippets, the full target plan text, and the same count/verdict policy.

## Level 2 Node 5 Scope

Level 2 Node 5 adds append-only proposal-review diagnostic reports over supplied `TradeProposalReviewRecord` values. A diagnostic report treats rejected human-review decisions as a false-positive proxy for proposal quality investigation. It does not claim a proposal was a realized false positive, because no post-review fill, outcome, live-result, settlement, reconciliation, or manual-execution data is consumed.

The module must:

- Consume only caller-supplied `TradeProposalReviewRecord` values.
- Reconstruct each supplied review record before diagnostic construction so mutated frozen objects or wrong types fail before report construction or log writes.
- Sort review records deterministically by UTC `recorded_at`, then `review_record_id`.
- Reject duplicate `review_record_id` values.
- Track total review record count, unique source proposal count, duplicate source proposal review count, approved decision count, rejected decision count, rejected source proposal count, rejected decision ratio, rejected source proposal ratio, and timestamp bounds.
- Track rejected reason-code rows from `review_reason_codes` on rejected records.
- Track bucket rows for `market_slug`, `strategy_type`, `risk_tag`, and `review_focus` values.
- Track rejected-source rows grouped by `source_proposal_packet_id` and `source_proposal_fingerprint`.
- Keep duplicate source proposal tracking as a proxy only; do not resolve conflicts, select latest decisions, collapse records, or promote a proposal.
- Emit frozen report dataclasses.
- Persist report snapshots through `TradeProposalReviewDiagnosticLog(path).append(report)` using append-only JSONL.
- Serialize `Decimal` values as exact strings and datetimes as UTC ISO strings.
- Validate before opening or writing JSONL files.

The module must not:

- Confirm realized false positives, infer outcomes, import manual execution results, compare expected fills to fills, inspect realized slippage, reconcile positions, or read settlement data.
- Add an approval workflow engine, approval queue, approval router, approver registry, role-based permissions, reviewer authentication, identity verification, latest-decision resolver, finalization state machine, or strategy-promotion signal.
- Convert diagnostics into order instructions, order requests, broker requests, execution decisions, order lifecycle states, or strategy-promotion packets.
- Fetch market, order-book, price-history, outcome, account, credential, or identity data.
- Read JSONL logs or external history.
- Scrape websites, run browser automation, bypass anti-bot controls, or handle CAPTCHA.
- Authenticate, handle credentials, handle private keys, sign messages, use wallets, or use trading SDKs.
- Create broker clients, transport clients, request payloads, response objects, sessions, WebSockets, heartbeats, reconciliation, settlement, or account-state surfaces.
- Place, submit, sign, send, create, or cancel orders.
- Add CLI, UI, dashboard, scheduler, notification, compliance, legal, jurisdiction, geofence, KYC, AML, sanctions, or geographic-access analysis surfaces.

## Target File Structure

Create:

- `src/polymarket_alpha_lab/proposal_review_diagnostics.py`
- `tests/test_proposal_review_diagnostics.py`
- `tests/test_proposal_review_diagnostics_scope.py`
- `docs/superpowers/plans/2026-06-14-level-2-proposal-review-diagnostics.md`

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

## Public API Contract

`src/polymarket_alpha_lab/proposal_review_diagnostics.py` must export exactly:

```python
__all__ = (
    "TradeProposalReviewDiagnosticBucketRow",
    "TradeProposalReviewDiagnosticConfig",
    "TradeProposalReviewDiagnosticLog",
    "TradeProposalReviewDiagnosticReasonRow",
    "TradeProposalReviewDiagnosticReport",
    "TradeProposalReviewDiagnosticSourceRow",
    "build_trade_proposal_review_diagnostic_report",
)
```

### Boundary Statement

`DEFAULT_REVIEW_DIAGNOSTIC_BOUNDARY_STATEMENT` must be exactly:

```python
(
    "This is a report-only proposal-review diagnostic artifact using rejected "
    "human-review decisions as a false-positive proxy, not realized false-positive "
    "confirmation, approval workflow, trade instruction, order instruction, broker "
    "request, order request, account action, account authentication, private-key "
    "handling, wallet signature, live-execution signal, credential workflow, "
    "manual execution import, strategy-promotion signal, settlement review, "
    "reconciliation process, or automatic order-placement authorization."
)
```

Boundary statement validation must require these lowercase substrings:

- `report-only`
- `proposal-review diagnostic`
- `rejected human-review decisions`
- `false-positive proxy`
- `not realized false-positive confirmation`
- `approval workflow`
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
- `settlement review`
- `reconciliation process`
- `automatic order-placement authorization`

These words are allowed in string literals for boundary text, but must not appear as identifiers that trigger scope tests.

### TradeProposalReviewDiagnosticConfig

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewDiagnosticConfig:
    config_version: str
    min_review_record_count: int = 1
    max_rejected_decision_ratio: Decimal = Decimal("0.5000")
    max_rejected_source_proposal_ratio: Decimal = Decimal("0.5000")
    max_reason_code_rejected_decision_share: Decimal = Decimal("0.7500")
    include_market_slug_buckets: bool = True
    include_strategy_type_buckets: bool = True
    include_risk_tag_buckets: bool = True
    include_review_focus_buckets: bool = True
    max_source_rows: int = 20
    boundary_statement: str = DEFAULT_REVIEW_DIAGNOSTIC_BOUNDARY_STATEMENT
```

Validation:

- `config_version` and `boundary_statement` must be canonical nonblank strings.
- `min_review_record_count` and `max_source_rows` must be nonnegative `int` values, not `bool`.
- Ratio fields must be finite `Decimal` values between `0` and `1`.
- Include fields must be exact `bool` values.
- `boundary_statement` must satisfy the boundary statement contract above.

### TradeProposalReviewDiagnosticReasonRow

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewDiagnosticReasonRow:
    reason_code: str
    rejected_decision_count: int
    rejected_source_proposal_count: int
    rejected_decision_share: Decimal
```

Validation:

- `reason_code` must be a canonical nonblank string.
- Count fields must be positive `int` values, not `bool`.
- `rejected_source_proposal_count <= rejected_decision_count`.
- `rejected_decision_share` must be a finite probability `Decimal`.

### TradeProposalReviewDiagnosticBucketRow

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewDiagnosticBucketRow:
    bucket_type: str
    bucket_value: str
    review_record_count: int
    unique_source_proposal_count: int
    rejected_decision_count: int
    rejected_source_proposal_count: int
    rejected_decision_ratio: Decimal
```

Validation:

- `bucket_type` must be one of `("market_slug", "strategy_type", "risk_tag", "review_focus")`.
- `bucket_value` must be a canonical nonblank string.
- `review_record_count` and `unique_source_proposal_count` must be positive `int` values, not `bool`.
- Rejected count fields must be nonnegative `int` values, not `bool`.
- `unique_source_proposal_count <= review_record_count`.
- `rejected_decision_count <= review_record_count`.
- `rejected_source_proposal_count <= unique_source_proposal_count`.
- `rejected_decision_ratio` must equal `rejected_decision_count / review_record_count`, quantized to `Decimal("0.0001")`.

### TradeProposalReviewDiagnosticSourceRow

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewDiagnosticSourceRow:
    source_proposal_packet_id: str
    source_proposal_fingerprint: str
    first_recorded_at: datetime
    last_recorded_at: datetime
    review_record_count: int
    rejected_decision_count: int
    reason_codes: tuple[str, ...]
    market_slug: str
    strategy_type: str
    risk_tags: tuple[str, ...]
    review_focus: tuple[str, ...]
```

Validation:

- String fields must be canonical nonblank strings.
- Timestamps are normalized to UTC and ordered.
- `review_record_count` and `rejected_decision_count` must be positive `int` values, not `bool`.
- `rejected_decision_count <= review_record_count`.
- `reason_codes`, `risk_tags`, and `review_focus` must be canonical string tuples sorted ascending and duplicate-free.
- Source rows represent rejected source proposal groups only, so `rejected_decision_count > 0`.

### TradeProposalReviewDiagnosticReport

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewDiagnosticReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    review_record_count: int
    unique_source_proposal_count: int
    duplicate_source_proposal_review_count: int
    approved_decision_count: int
    rejected_decision_count: int
    rejected_source_proposal_count: int
    rejected_decision_ratio: Decimal | None
    rejected_source_proposal_ratio: Decimal | None
    max_reason_code_rejected_decision_share: Decimal | None
    first_recorded_at: datetime | None
    last_recorded_at: datetime | None
    status: str
    reason_rows: tuple[TradeProposalReviewDiagnosticReasonRow, ...]
    bucket_rows: tuple[TradeProposalReviewDiagnosticBucketRow, ...]
    source_rows: tuple[TradeProposalReviewDiagnosticSourceRow, ...]
```

Validation:

- `generated_at`, `first_recorded_at`, and `last_recorded_at` are normalized to UTC.
- `config_version` must be a canonical nonblank string.
- `report_only` must be `True`.
- `boundary_statement` must satisfy the boundary statement contract above.
- Count fields must be nonnegative `int` values, not `bool`.
- `review_record_count == approved_decision_count + rejected_decision_count`.
- `unique_source_proposal_count <= review_record_count`.
- `duplicate_source_proposal_review_count == review_record_count - unique_source_proposal_count`.
- `rejected_source_proposal_count <= unique_source_proposal_count`.
- If `review_record_count == 0`, timestamp bounds, ratios, reason rows, bucket rows, and source rows must be absent/empty.
- If `review_record_count > 0`, timestamp bounds must be present and ordered, and `rejected_decision_ratio` must equal `rejected_decision_count / review_record_count`, quantized to `Decimal("0.0001")`.
- If `unique_source_proposal_count == 0`, `rejected_source_proposal_ratio` must be `None`; otherwise it must equal `rejected_source_proposal_count / unique_source_proposal_count`, quantized to `Decimal("0.0001")`.
- If `rejected_decision_count == 0`, reason rows and source rows must be empty and `max_reason_code_rejected_decision_share` must be `None`.
- If `rejected_decision_count > 0`, reason rows must be present and `max_reason_code_rejected_decision_share` must equal the largest reason row count divided by `rejected_decision_count`, quantized to `Decimal("0.0001")`.
- `source_rows` may be empty even when rejected decisions exist because `config.max_source_rows=0` intentionally suppresses retained source rows while keeping report-level counts populated.
- `status` must be one of `("incomplete_review_data", "insufficient_review_sample", "high_rejection_proxy", "diagnostics_ready")`.
- `reason_rows` must be sorted by `reason_code`.
- `bucket_rows` must be sorted by `(bucket_type, bucket_value)`.
- `source_rows` must be sorted by `(-rejected_decision_count, -review_record_count, source_proposal_packet_id, source_proposal_fingerprint)`.

### Builder Contract

```python
def build_trade_proposal_review_diagnostic_report(
    records: Iterable[TradeProposalReviewRecord],
    *,
    config: TradeProposalReviewDiagnosticConfig,
    generated_at: datetime,
) -> TradeProposalReviewDiagnosticReport:
    ...
```

Builder behavior:

- Reject `records` when it is a `str` or `bytes`.
- Convert `records` to a tuple exactly once and raise `ValueError("records must be an iterable of TradeProposalReviewRecord values")` for non-iterables.
- Reject non-`TradeProposalReviewRecord` elements.
- Reconstruct each record through `TradeProposalReviewRecord(...)` using all dataclass fields before diagnostic construction.
- Reject duplicate `review_record_id` values with `ValueError("duplicate review_record_id values are not allowed")`.
- Reject non-`TradeProposalReviewDiagnosticConfig` config values.
- Reject non-`datetime` `generated_at` values.
- Normalize `generated_at` and record timestamps to UTC.
- Sort validated records by `(_as_utc(record.recorded_at), record.review_record_id)`.
- Do not collapse records by source proposal or choose a latest decision.
- Compute:
  - `review_record_count = len(records)`
  - `unique_source_proposal_count = len({record.source_proposal_packet_id})`
  - `duplicate_source_proposal_review_count = review_record_count - unique_source_proposal_count`
  - `approved_decision_count`
  - `rejected_decision_count`
  - `rejected_source_proposal_count = len({source_proposal_packet_id for rejected records})`
  - `rejected_decision_ratio = rejected_decision_count / review_record_count` when records exist, else `None`
  - `rejected_source_proposal_ratio = rejected_source_proposal_count / unique_source_proposal_count` when source proposals exist, else `None`
- Build reason rows from rejected records only:
  - count each distinct `review_reason_codes` value once per rejected record by iterating `frozenset(record.review_reason_codes)`;
  - `rejected_decision_share = reason_count / rejected_decision_count`;
  - sort rows by `reason_code`.
- Build bucket rows for enabled bucket types:
  - market slug bucket from every record when `include_market_slug_buckets` is true;
  - strategy type bucket from every record when `include_strategy_type_buckets` is true;
  - one risk-tag bucket per distinct risk tag per record when `include_risk_tag_buckets` is true;
  - one review-focus bucket per distinct review focus per record when `include_review_focus_buckets` is true;
  - sort rows by `(bucket_type, bucket_value)`.
- Build source rows for source proposal groups with one or more rejected records:
  - group by `(source_proposal_packet_id, source_proposal_fingerprint)`;
  - include all records in each group for `review_record_count` and timestamp bounds;
  - include only rejected records for `rejected_decision_count` and reason-code union;
  - use the group records' source proposal fields directly after record reconstruction; the record fingerprint already covers source proposal fields such as `market_slug`, `strategy_type`, `risk_tags`, and `review_focus`;
  - union `risk_tags` and `review_focus` across all group records and sort them;
  - sort rows by `(-rejected_decision_count, -review_record_count, source_proposal_packet_id, source_proposal_fingerprint)`;
  - retain at most `config.max_source_rows` rows; `0` means retain none.
- Determine status:
  - `incomplete_review_data` when no review records exist;
  - `insufficient_review_sample` when `review_record_count < config.min_review_record_count`;
  - `high_rejection_proxy` when any present diagnostic ratio breaches its threshold:
    - `rejected_decision_ratio is not None and rejected_decision_ratio > config.max_rejected_decision_ratio`
    - `rejected_source_proposal_ratio is not None and rejected_source_proposal_ratio > config.max_rejected_source_proposal_ratio`
    - `max_reason_code_rejected_decision_share is not None and max_reason_code_rejected_decision_share > config.max_reason_code_rejected_decision_share`
  - `diagnostics_ready` otherwise.

### Log Contract

`TradeProposalReviewDiagnosticLog(path).append(report)`:

- Accepts only `TradeProposalReviewDiagnosticReport`.
- Reconstructs and validates the report tree before serialization.
- Serializes with `json.dumps(_json_ready(asdict(report)), allow_nan=False, sort_keys=True) + "\n"`.
- Uses append-only mode.
- Creates missing parent directories only after validation and serialization have succeeded.
- Revalidates the nearest existing parent before opening the file.
- Does not expose a reader, loader, updater, deleter, importer, exporter, dispatcher, replay API, external-history API, outcome API, or manual-execution import.

## Task 1: Functional Tests

**Files:**
- Create: `tests/test_proposal_review_diagnostics.py`

- [ ] **Step 1: Write the failing import and fixture stack**

Create `tests/test_proposal_review_diagnostics.py` with:

- Imports: `json`, `FrozenInstanceError`, `replace`, `UTC`, `datetime`, `timedelta`, `timezone`, `Decimal`, `pytest`.
- Import existing Node 3 fixtures and helpers from `tests.test_proposal_review_summary`: `proposal_for_source`, `review_record`.
- Do not pass unsupported fields such as `review_focus` into `proposal_for_source`; current review-focus values flow from the existing manual-review queue fixture stack into proposal packets and review records.
- New imports from `polymarket_alpha_lab.proposal_review_diagnostics`:

```python
from polymarket_alpha_lab.proposal_review_diagnostics import (
    TradeProposalReviewDiagnosticBucketRow,
    TradeProposalReviewDiagnosticConfig,
    TradeProposalReviewDiagnosticLog,
    TradeProposalReviewDiagnosticReasonRow,
    TradeProposalReviewDiagnosticReport,
    TradeProposalReviewDiagnosticSourceRow,
    build_trade_proposal_review_diagnostic_report,
)
```

Append this first failing test:

```python
DEFAULT_REVIEW_DIAGNOSTIC_BOUNDARY_STATEMENT = (
    "This is a report-only proposal-review diagnostic artifact using rejected "
    "human-review decisions as a false-positive proxy, not realized false-positive "
    "confirmation, approval workflow, trade instruction, order instruction, broker "
    "request, order request, account action, account authentication, private-key "
    "handling, wallet signature, live-execution signal, credential workflow, "
    "manual execution import, strategy-promotion signal, settlement review, "
    "reconciliation process, or automatic order-placement authorization."
)


def diagnostic_report(records, **overrides):
    values = {
        "records": records,
        "config": TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            min_review_record_count=1,
            max_source_rows=20,
        ),
        "generated_at": datetime(2026, 9, 6, 9, tzinfo=timezone(timedelta(hours=-4))),
    }
    values.update(overrides)
    return build_trade_proposal_review_diagnostic_report(**values)


def approved_review(index, **overrides):
    values = {
        "proposal": proposal_for_source(index, market_slug=f"market-{index}"),
        "recorded_at": datetime(2026, 9, 3, 12, index, tzinfo=UTC),
    }
    values.update(overrides)
    return review_record(**values)


def rejected_review(index, reason_codes=("liquidity_exit_risk",), **overrides):
    values = {
        "proposal": proposal_for_source(index, market_slug=f"market-{index}"),
        "decision": "rejected",
        "review_reason_codes": reason_codes,
        "review_rationale": "Rejected after checking proposal-review diagnostic proxy inputs.",
        "recorded_at": datetime(2026, 9, 3, 12, index, tzinfo=UTC),
    }
    values.update(overrides)
    return review_record(**values)


def test_build_trade_proposal_review_diagnostic_report_counts_rejection_proxy_rows():
    duplicate_proposal = proposal_for_source(4, market_slug="duplicate-market")
    records = [
        rejected_review(
            2,
            ("liquidity_exit_risk", "model_confidence"),
            proposal=proposal_for_source(
                2,
                market_slug="alpha-market",
                strategy_type="mean_reversion",
                risk_tags=("liquidity", "resolution"),
            ),
        ),
        approved_review(
            1,
            proposal=proposal_for_source(
                1,
                market_slug="alpha-market",
                strategy_type="mean_reversion",
                risk_tags=("liquidity",),
            ),
        ),
        rejected_review(
            3,
            ("resolution_ambiguity",),
            proposal=proposal_for_source(
                3,
                market_slug="beta-market",
                strategy_type="event_value",
                risk_tags=("resolution",),
            ),
        ),
        rejected_review(
            4,
            ("liquidity_exit_risk",),
            proposal=duplicate_proposal,
            recorded_at=datetime(2026, 9, 3, 12, 4, tzinfo=UTC),
        ),
        approved_review(
            5,
            proposal=duplicate_proposal,
            recorded_at=datetime(2026, 9, 3, 12, 5, tzinfo=UTC),
        ),
    ]

    report = diagnostic_report(list(reversed(records)))

    assert report.generated_at == datetime(2026, 9, 6, 13, tzinfo=UTC)
    assert report.config_version == "diagnostic-v1"
    assert report.report_only is True
    assert report.review_record_count == 5
    assert report.unique_source_proposal_count == 4
    assert report.duplicate_source_proposal_review_count == 1
    assert report.approved_decision_count == 2
    assert report.rejected_decision_count == 3
    assert report.rejected_source_proposal_count == 3
    assert report.rejected_decision_ratio == Decimal("0.6000")
    assert report.rejected_source_proposal_ratio == Decimal("0.7500")
    assert report.max_reason_code_rejected_decision_share == Decimal("0.6667")
    assert report.first_recorded_at == datetime(2026, 9, 3, 12, 1, tzinfo=UTC)
    assert report.last_recorded_at == datetime(2026, 9, 3, 12, 5, tzinfo=UTC)
    assert report.status == "high_rejection_proxy"
    assert tuple(row.reason_code for row in report.reason_rows) == (
        "liquidity_exit_risk",
        "model_confidence",
        "resolution_ambiguity",
    )
    assert tuple(row.bucket_type for row in report.bucket_rows).count("market_slug") == 3
    expected_source_ids = tuple(
        row[0]
        for row in sorted(
            (
                (
                    duplicate_proposal.proposal_packet_id,
                    duplicate_proposal.proposal_packet_id,
                ),
                (
                    records[0].source_proposal_packet_id,
                    records[0].source_proposal_packet_id,
                ),
                (
                    records[2].source_proposal_packet_id,
                    records[2].source_proposal_packet_id,
                ),
            ),
            key=lambda item: (
                0 if item[0] == duplicate_proposal.proposal_packet_id else 1,
                item[1],
            ),
        )
    )
    assert tuple(row.source_proposal_packet_id for row in report.source_rows) == (
        expected_source_ids
    )
```

- [ ] **Step 2: Run the first failing test**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_diagnostics.py::test_build_trade_proposal_review_diagnostic_report_counts_rejection_proxy_rows -q
```

Expected: FAIL during import with `ModuleNotFoundError` or `ImportError` because `proposal_review_diagnostics.py` does not exist yet.

- [ ] **Step 3: Add remaining failing functional tests**

Add these tests in `tests/test_proposal_review_diagnostics.py`:

- `test_trade_proposal_review_diagnostic_statuses_cover_empty_sample_and_thresholds`
  - Empty records produce count `0`, all ratios `None`, empty rows, and status `incomplete_review_data`.
  - One approved record with `min_review_record_count=2` produces status `insufficient_review_sample`.
  - One rejected-only report with `max_rejected_decision_ratio=Decimal("0.2500")` produces status `high_rejection_proxy`.
  - One report whose rejected source proposal ratio exceeds threshold produces status `high_rejection_proxy`.
  - One report whose reason-code share exceeds threshold produces status `high_rejection_proxy`.
  - An approved-only report or a mixed report with relaxed rejection thresholds produces status `diagnostics_ready`.
- `test_trade_proposal_review_diagnostic_reason_rows_are_deterministic`
  - Rejected records with overlapping reason codes produce sorted reason rows.
  - `rejected_decision_count`, `rejected_source_proposal_count`, and `rejected_decision_share` are correct.
- `test_trade_proposal_review_diagnostic_bucket_rows_respect_config`
  - Default config includes `market_slug`, `strategy_type`, `risk_tag`, and `review_focus` buckets.
  - Config with `include_risk_tag_buckets=False` and `include_review_focus_buckets=False` omits those bucket types.
  - Bucket ratios and unique source proposal counts are correct.
- `test_trade_proposal_review_diagnostic_source_rows_are_limited_and_sorted`
  - More rejected source groups than `max_source_rows` are trimmed.
  - Sorting uses highest rejected count, then highest review count, then source identifiers.
  - `max_source_rows=0` produces no source rows while report-level counts remain populated.
- `test_trade_proposal_review_diagnostic_rejects_bad_inputs_and_duplicates`
  - Non-iterable `records`, string `records`, bytes `records`, non-record element, non-config config, non-datetime `generated_at`, and duplicate `review_record_id` all raise `ValueError`.
- `test_trade_proposal_review_diagnostic_revalidates_mutated_records`
  - Mutate a record `recorded_at` to a string; builder raises before report construction.
  - Mutate a record `review_reason_codes` to a duplicate tuple without recomputing the derived `review_record_id`; builder raises before report construction because the record identity no longer matches the record fields.
  - Mutate a record `source_proposal_fingerprint` to a stale value; builder raises before report construction.
- `test_trade_proposal_review_diagnostic_dataclasses_are_frozen_and_validate_invariants`
  - `TradeProposalReviewDiagnosticConfig`, `TradeProposalReviewDiagnosticReasonRow`, `TradeProposalReviewDiagnosticBucketRow`, `TradeProposalReviewDiagnosticSourceRow`, and `TradeProposalReviewDiagnosticReport` are frozen.
  - `replace(...)` rejects invalid counts, invalid ratios, invalid include flags, invalid status, invalid row ordering, bad source row tuple ordering, inconsistent counts, wrong ratios, `report_only=False`, and invalid boundary text.
- `test_trade_proposal_review_diagnostic_boundary_statement_contract`
  - The default boundary statement equals the contract in this plan.
  - Incomplete boundary statements raise `ValueError`.
- `test_trade_proposal_review_diagnostic_log_appends_jsonl_report`
  - Append one report and assert JSON values: `generated_at`, `report_only`, counts, ratios as strings, nested reason rows, bucket rows, and source rows.
- `test_trade_proposal_review_diagnostic_log_appends_without_overwriting_and_creates_parent_dirs`
  - Append the same report twice to a nested path and assert two JSONL lines.
- `test_trade_proposal_review_diagnostic_log_rejects_invalid_paths_and_inputs`
  - Reject non-path path, blank path, existing directory path, parent-file path, and non-report append input.
- `test_trade_proposal_review_diagnostic_log_preserves_existing_file_when_validation_fails`
  - Mutate a nested reason row field to `Decimal("NaN")`, append to an existing file, assert content is unchanged.
- `test_trade_proposal_review_diagnostic_log_rejects_non_finite_decimal_before_open`
  - Mutate `rejected_decision_ratio` to `Decimal("NaN")`, append to a missing file, assert file does not exist.

- [ ] **Step 4: Run the full new functional test file and keep the expected failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_diagnostics.py -q
```

Expected: FAIL because the new module and public API do not exist yet.

## Task 2: Scope And Export Tests

**Files:**
- Create: `tests/test_proposal_review_diagnostics_scope.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_analytics_scope.py`
- Modify: `tests/test_analytics_history_scope.py`
- Modify: `tests/test_forecast_evidence_scope.py`
- Modify: `tests/test_manual_review_queue_scope.py`
- Modify: `tests/test_proposal_packet_scope.py`
- Modify: `tests/test_proposal_review_scope.py`
- Modify: `tests/test_proposal_review_summary_scope.py`
- Modify: `tests/test_proposal_review_quality_scope.py`

- [ ] **Step 1: Add the new module scope test**

Create `tests/test_proposal_review_diagnostics_scope.py` with the AST helper structure used by `tests/test_proposal_review_quality_scope.py`.

Use these expected exports:

```python
EXPECTED_PROPOSAL_REVIEW_DIAGNOSTIC_EXPORTS = {
    "TradeProposalReviewDiagnosticBucketRow",
    "TradeProposalReviewDiagnosticConfig",
    "TradeProposalReviewDiagnosticLog",
    "TradeProposalReviewDiagnosticReasonRow",
    "TradeProposalReviewDiagnosticReport",
    "TradeProposalReviewDiagnosticSourceRow",
    "build_trade_proposal_review_diagnostic_report",
}
```

Also define the existing Level 2 artifact export sets for proposal packets, review records, review summaries, and review quality, then include diagnostics in the new file's root-export allowlist:

```python
EXPECTED_LEVEL_2_ARTIFACT_EXPORTS = (
    EXPECTED_LEVEL_2_PROPOSAL_PACKET_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_SUMMARY_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_QUALITY_EXPORTS
    | EXPECTED_PROPOSAL_REVIEW_DIAGNOSTIC_EXPORTS
)
```

Use these allowed imports:

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
    "polymarket_alpha_lab.proposal_review",
}
```

Use this first-party symbol allowlist:

```python
EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.proposal_review": {
        "TradeProposalReviewRecord",
    },
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
    "polymarket_alpha_lab.proposal_review_summary",
    "polymarket_alpha_lab.proposal_review_quality",
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

Use compound forbidden name fragments so intended inert diagnostic names survive. The AST name scan must include identifiers, attributes, function/class names, args, and keywords; string literals are not scanned. Include at least the current Node 4 forbidden fragments, but do not include bare `falsepositive` because the boundary statement is intentionally a false-positive proxy. Keep compound live/execution/order/account/compliance fragments such as:

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

- `test_proposal_review_diagnostics_module_imports_only_allowed_dependencies`
- `test_proposal_review_diagnostics_module_does_not_import_forbidden_surfaces`
- `test_proposal_review_diagnostics_module_uses_only_allowed_first_party_symbols`
- `test_proposal_review_diagnostics_module_does_not_define_forbidden_live_or_workflow_names`
- `test_trade_proposal_review_diagnostic_public_exports_are_report_only`
- `test_package_root_exports_do_not_leak_forbidden_level_2_node_5_surfaces`

- [ ] **Step 2: Update package export tests**

In `tests/test_init.py`, import the seven new public objects from `polymarket_alpha_lab.proposal_review_diagnostics` and add `test_level_2_node_5_public_api_exports()` asserting package-root identity bindings and `lab.__all__` membership for:

```python
{
    "TradeProposalReviewDiagnosticBucketRow",
    "TradeProposalReviewDiagnosticConfig",
    "TradeProposalReviewDiagnosticLog",
    "TradeProposalReviewDiagnosticReasonRow",
    "TradeProposalReviewDiagnosticReport",
    "TradeProposalReviewDiagnosticSourceRow",
    "build_trade_proposal_review_diagnostic_report",
}
```

- [ ] **Step 3: Update existing root-export scope allowlists**

In these files, add `EXPECTED_PROPOSAL_REVIEW_DIAGNOSTIC_EXPORTS` with the seven exports above and include it in `EXPECTED_LEVEL_2_ARTIFACT_EXPORTS`:

- `tests/test_analytics_scope.py`
- `tests/test_analytics_history_scope.py`
- `tests/test_forecast_evidence_scope.py`
- `tests/test_manual_review_queue_scope.py`
- `tests/test_proposal_packet_scope.py`
- `tests/test_proposal_review_scope.py`
- `tests/test_proposal_review_summary_scope.py`
- `tests/test_proposal_review_quality_scope.py`

Keep existing forbidden-fragment checks intact. Do not weaken unrelated scope tests.

- [ ] **Step 4: Run the new and changed scope/export tests and keep the expected failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_diagnostics_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py tests/test_proposal_review_quality_scope.py -q
```

Expected: FAIL because the implementation module and package-root exports do not exist yet.

## Task 3: Implement Proposal Review Diagnostics Module

**Files:**
- Create: `src/polymarket_alpha_lab/proposal_review_diagnostics.py`

- [ ] **Step 1: Create the module shell and public dataclasses**

Create `src/polymarket_alpha_lab/proposal_review_diagnostics.py` with:

- Standard-library imports only: `json`, `Iterable`, `fields`, `asdict`, `dataclass`, `UTC`, `datetime`, `Decimal`, `ROUND_HALF_EVEN`, `Path`, `Any`.
- First-party imports only:

```python
from polymarket_alpha_lab.proposal_review import TradeProposalReviewRecord
```

- Constants:
  - `RATIO_QUANTUM = Decimal("0.0001")`
  - `ZERO = Decimal("0")`
  - `ONE = Decimal("1")`
  - `BUCKET_TYPES = ("market_slug", "strategy_type", "risk_tag", "review_focus")`
  - `REPORT_STATUSES = ("incomplete_review_data", "insufficient_review_sample", "high_rejection_proxy", "diagnostics_ready")`
  - the default boundary statement from this plan.
- The seven public exports from the Public API Contract section.
- Frozen dataclasses from the Public API Contract section.

- [ ] **Step 2: Implement validation helpers**

Implement helpers consistent with `proposal_review_summary.py` and `proposal_review_quality.py`:

- `_as_utc(value: datetime) -> datetime`
- `_require_canonical_string(field_name: str, value: str) -> None`
- `_require_boundary_statement(value: str) -> None`
- `_require_bool(field_name: str, value: bool) -> None`
- `_require_nonnegative_int(field_name: str, value: int) -> None`
- `_require_positive_int(field_name: str, value: int) -> None`
- `_require_decimal(field_name: str, value: Decimal) -> None`
- `_require_finite_decimal(field_name: str, value: Decimal) -> None`
- `_require_probability_decimal(field_name: str, value: Decimal) -> None`
- `_require_optional_probability_decimal(field_name: str, value: Decimal | None) -> None`
- `_normalize_string_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]`
- `_normalize_sorted_unique_string_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]`
- `_normalize_typed_tuple(field_name: str, values: Iterable[Any], expected_type: type[Any]) -> tuple[Any, ...]`
- `_quantize_ratio(value: Decimal) -> Decimal`
- `_ratio_from_counts(numerator: int, denominator: int) -> Decimal`
- `_optional_ratio_from_counts(numerator: int, denominator: int) -> Decimal | None`

`_quantize_ratio` must use `value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)` and reject non-finite values.

- [ ] **Step 3: Implement record/report cloning and JSON helpers**

Implement:

- `_clone_review_record(record: TradeProposalReviewRecord) -> TradeProposalReviewRecord`, using `fields(TradeProposalReviewRecord)` to reconstruct the entire record and trigger validation.
- `_validate_report_tree(report: TradeProposalReviewDiagnosticReport) -> TradeProposalReviewDiagnosticReport`, reconstructing nested reason, bucket, and source rows and returning a validated report.
- `_json_ready(value: Any) -> Any`, matching existing behavior: `Decimal` to `str`, `datetime` to UTC ISO string, reject `float`, recurse into dict/list/tuple, require dict keys to be strings.
- `_normalize_log_path(value: Path | str) -> Path`
- `_validate_log_parent(path: Path) -> None`

The log append method must compute JSON before creating parent directories or opening files.

- [ ] **Step 4: Implement diagnostic builders**

Implement:

- `build_trade_proposal_review_diagnostic_report(...)`
- `_build_reason_rows(records: tuple[TradeProposalReviewRecord, ...]) -> tuple[TradeProposalReviewDiagnosticReasonRow, ...]`
- `_build_bucket_rows(records: tuple[TradeProposalReviewRecord, ...], config: TradeProposalReviewDiagnosticConfig) -> tuple[TradeProposalReviewDiagnosticBucketRow, ...]`
- `_build_source_rows(records: tuple[TradeProposalReviewRecord, ...], max_source_rows: int) -> tuple[TradeProposalReviewDiagnosticSourceRow, ...]`
- `_diagnostic_status(...) -> str`
- `_source_group_key(record: TradeProposalReviewRecord) -> tuple[str, str]`
- `_add_bucket_record(...) -> None`

Use deterministic grouping:

```python
rejected_records = tuple(record for record in records if record.decision == "rejected")
reason_counts: dict[str, int] = {}
reason_sources: dict[str, set[str]] = {}
for record in rejected_records:
    for reason_code in frozenset(record.review_reason_codes):
        reason_counts[reason_code] = reason_counts.get(reason_code, 0) + 1
        reason_sources.setdefault(reason_code, set()).add(record.source_proposal_packet_id)
```

Bucket rows should use all records in each bucket for denominators and rejected records for rejected counts. Source rows should group all records by source id/fingerprint, then retain only groups where at least one record is rejected. Do not add a separate source-field stability check; `TradeProposalReviewRecord` reconstruction already validates the source fingerprint before diagnostics are built.

- [ ] **Step 5: Run focused functional tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_diagnostics.py -q
```

Expected: PASS after implementation.

## Task 4: Package Exports, Scope Migration, And README

**Files:**
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `README.md`

Ownership rule: the scope/export-test worker owns every test file listed in Task 2 while that worker is active. The main integrator must not edit those files concurrently. If the scope/export-test worker is not used, or after it is closed, the main integrator may update any remaining Task 2 files and then becomes their sole writer.

- [ ] **Step 1: Export the new API from package root**

In `src/polymarket_alpha_lab/__init__.py`, add:

```python
from polymarket_alpha_lab.proposal_review_diagnostics import (
    TradeProposalReviewDiagnosticBucketRow,
    TradeProposalReviewDiagnosticConfig,
    TradeProposalReviewDiagnosticLog,
    TradeProposalReviewDiagnosticReasonRow,
    TradeProposalReviewDiagnosticReport,
    TradeProposalReviewDiagnosticSourceRow,
    build_trade_proposal_review_diagnostic_report,
)
```

Add the same seven names to `__all__`, preserving the existing alphabetical-ish grouping around Level 2 proposal review exports.

- [ ] **Step 2: Update README**

Modify `README.md`:

- In the Phase 1 Scope paragraph, append `proposal-review diagnostic artifacts`.
- Add `## Level 2 Node 5 Status` after the Node 4 Python API section:

```markdown
## Level 2 Node 5 Status

Level 2 Node 5 adds report-only proposal-review diagnostic artifacts over supplied `TradeProposalReviewRecord` values. It treats rejected human-review decisions as a false-positive proxy for proposal quality investigation only; it does not confirm realized false positives, import outcomes, compare fills, reconcile positions, or move any proposal toward execution.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, execution client, or transport client; build broker or order request payloads; reconcile exchange accounts; import manual executions; inspect settlement; or perform compliance/legal/geographic analysis.
```

- Add `## Level 2 Node 5 Python API`:

```markdown
## Level 2 Node 5 Python API

Node 5 is exposed through Python APIs:

- Configure proposal-review diagnostics with `TradeProposalReviewDiagnosticConfig(config_version="diagnostic-v1")`.
- Build proposal-review diagnostic reports with `build_trade_proposal_review_diagnostic_report(records, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalReviewDiagnosticReport`.
- Inspect rejected reason-code proxy rows with `TradeProposalReviewDiagnosticReasonRow`, bucket rows with `TradeProposalReviewDiagnosticBucketRow`, and rejected source proposal rows with `TradeProposalReviewDiagnosticSourceRow`.
- Persist proposal-review diagnostic snapshots with `TradeProposalReviewDiagnosticLog(path).append(report)`.
```

- Update the repository layout tree to include:
  - `docs/superpowers/plans/2026-06-14-level-2-proposal-review-diagnostics.md`
  - `src/polymarket_alpha_lab/proposal_review_diagnostics.py`
  - `tests/test_proposal_review_diagnostics.py`
  - `tests/test_proposal_review_diagnostics_scope.py`

- [ ] **Step 3: Run scope/export and README-adjacent tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py tests/test_proposal_review_diagnostics_scope.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py tests/test_proposal_review_quality_scope.py -q
```

Expected: PASS after exports and allowlists are updated.

## Task 5: Verification, Claude Implementation Review, Handoff, Commit, Push

**Files:**
- Modify: `docs/superpowers/plans/2026-06-14-level-2-proposal-review-diagnostics.md`

- [ ] **Step 1: Run focused verification**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_diagnostics.py tests/test_proposal_review_diagnostics_scope.py tests/test_init.py -q
```

Expected: PASS.

- [ ] **Step 2: Run Level 2/scope verification subset**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_packet.py tests/test_proposal_review.py tests/test_proposal_review_summary.py tests/test_proposal_review_quality.py tests/test_proposal_review_diagnostics.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py tests/test_proposal_review_quality_scope.py tests/test_proposal_review_diagnostics_scope.py tests/test_init.py -q
```

Expected: PASS.

- [ ] **Step 3: Run full verification**

Run:

```bash
.venv/bin/python -m pytest -q
git diff --check
codegraph sync
codegraph status .
git status --short --branch --untracked-files=all
```

Expected:

- Full pytest suite passes.
- `git diff --check` exits 0.
- CodeGraph sync exits 0 and status reports index up to date.
- Git status shows only intentional Node 5 modifications before staging.

- [ ] **Step 4: Submit self-contained Claude implementation review**

Run:

```bash
{
  printf '%s\n' 'Review the implemented Level 2 proposal-review-diagnostics node for polymarket-alpha-lab.'
  printf '%s\n' 'This is a read-only implementation review. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, roadmap/spec material, validation gates, tests, implementation, or verification output.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; implementation is ready to commit.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, unsafe scope, missing required review material, missing verification, or implementation ambiguity.'
  printf '%s\n' 'Review specifically: report-only diagnostics boundary, rejected human-review decision as false-positive proxy only, no realized false-positive confirmation, no approval workflow/queue/router/client surfaces, no credentials/private keys/account auth, no unattended execution or live orders, no order lifecycle/reconciliation/settlement behavior, no manual execution import, no scraping/browser automation, no compliance/legal/geographic analysis, TradeProposalReviewRecord revalidation, duplicate review_record_id rejection, deterministic ordering, reason/bucket/source row correctness, max_source_rows behavior, no redundant source group stability check beyond record fingerprint validation, Decimal/UTC validation, JSONL validate-before-open behavior, package exports, scope tests, README docs, TDD evidence, CodeGraph status, full test output, handoff summary, and commit/push readiness.'
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
  sed -n '97,138p' docs/research/validation-gates.md
  printf '%s\n' ''
  printf '%s\n' 'Plan:'
  cat docs/superpowers/plans/2026-06-14-level-2-proposal-review-diagnostics.md
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'Diff stat:'
  git diff --stat
  printf '%s\n' ''
  printf '%s\n' 'Implementation diff:'
  git diff -- src/polymarket_alpha_lab/proposal_review_diagnostics.py src/polymarket_alpha_lab/__init__.py README.md tests/test_proposal_review_diagnostics.py tests/test_proposal_review_diagnostics_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py tests/test_proposal_review_quality_scope.py docs/superpowers/plans/2026-06-14-level-2-proposal-review-diagnostics.md
  printf '%s\n' ''
  printf '%s\n' 'Verification output:'
  .venv/bin/python -m pytest -q
  git diff --check
  codegraph status .
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted implementation-review terminal state: `Critical findings: 0`, `Important findings: 0`, and a verdict of `Proceed` or `Proceed with fixes`. Fix every Critical and Important finding, rerun local verification, and rerun this implementation review until accepted.

- [ ] **Step 5: Append Handoff Summary**

Append a `## Handoff Summary` section to this plan with:

- Node name and status.
- Files created/modified.
- Final verification commands and pass counts.
- Claude implementation review counts and verdict.
- Explicit pre-commit status and pause note: this node ends here unless the user asks to continue.

The Handoff Summary is committed before the final commit hash and push result exist, so it must not claim to contain its own commit hash or final push status. Report the final commit hash and push result in the assistant final response after commit and push.

- [ ] **Step 6: Commit and push**

Run:

```bash
git status --short --branch --untracked-files=all
git add src/polymarket_alpha_lab/proposal_review_diagnostics.py tests/test_proposal_review_diagnostics.py tests/test_proposal_review_diagnostics_scope.py src/polymarket_alpha_lab/__init__.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py tests/test_proposal_review_quality_scope.py README.md docs/superpowers/plans/2026-06-14-level-2-proposal-review-diagnostics.md
git commit -m "feat: add proposal review diagnostics"
git push origin main
git status --short --branch --untracked-files=all
```

Expected: commit succeeds, push succeeds, and final status is clean against `origin/main`.

## Handoff Summary

Node: Level 2 Node 5 proposal-review diagnostics.

Status before commit: implementation complete locally, full local verification is passing, and final Claude re-review has passed with zero findings. The code is ready for final staging, commit, and push.

Files created:

- `src/polymarket_alpha_lab/proposal_review_diagnostics.py`
- `tests/test_proposal_review_diagnostics.py`
- `tests/test_proposal_review_diagnostics_scope.py`
- `docs/superpowers/plans/2026-06-14-level-2-proposal-review-diagnostics.md`

Files modified:

- `README.md`
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

TDD and verification evidence:

- RED functional import failure captured with `.venv/bin/python -m pytest tests/test_proposal_review_diagnostics.py::test_build_trade_proposal_review_diagnostic_report_counts_rejection_proxy_rows -q`: `ModuleNotFoundError: No module named 'polymarket_alpha_lab.proposal_review_diagnostics'`.
- RED scope/export failure captured by the scope/export worker: `tests/test_init.py` collection failed with the same missing diagnostics module.
- Focused diagnostics tests: `.venv/bin/python -m pytest tests/test_proposal_review_diagnostics.py -q` passed with `15 passed`.
- Scope/export tests: `.venv/bin/python -m pytest tests/test_proposal_review_diagnostics_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py tests/test_proposal_review_quality_scope.py -q` passed with `63 passed`.
- Focused final subset: `.venv/bin/python -m pytest tests/test_proposal_review_diagnostics.py tests/test_proposal_review_diagnostics_scope.py tests/test_init.py -q` passed with `33 passed`.
- Level 2/scope subset: `.venv/bin/python -m pytest tests/test_proposal_packet.py tests/test_proposal_review.py tests/test_proposal_review_summary.py tests/test_proposal_review_quality.py tests/test_proposal_review_diagnostics.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py tests/test_proposal_review_quality_scope.py tests/test_proposal_review_diagnostics_scope.py tests/test_init.py -q` passed with `157 passed`.
- Full suite: `.venv/bin/python -m pytest -q` passed with `525 passed`.
- `git diff --check` exited 0.
- `codegraph sync` completed and `codegraph status .` reported the index up to date.

Claude implementation review:

- Model: `claude-opus-4-8`
- Effort: `max`
- Critical findings: 0
- Important findings: 0
- Minor findings: 3
- Verdict: `Proceed with fixes`
- Follow-up applied before commit: README Node 5 negative-scope paragraph restored, README repo-tree order adjusted, and this Handoff Summary appended. The remaining helper-name comment was cosmetic and did not require implementation change.
- Additional read-only Codex implementation review found four Important dataclass invariant gaps after the first Claude review. Those were fixed with a new RED/GREEN regression test covering impossible rejected-source counts, reason-share mismatch, and duplicate grouped rows. Final Claude re-review after these fixes is pending because the Claude Code gateway currently has no available `claude-opus-4-8` accounts.
- Resume attempt: refreshed `.venv/bin/python -m pytest -q` still passed with `525 passed`; a minimal `claude-opus-4-8` ping and a full retry both failed with `503 No available accounts`, so the final Claude re-review remains the only incomplete gate before commit/push.
- Second resume attempt: refreshed repo state, `git diff --check`, and `codegraph status .`; `.venv/bin/python -m pytest -q` still passed with `525 passed`. A full `claude-opus-4-8` retry again failed with `503 No available accounts`, so commit/push remains intentionally held behind the required Claude review gate.
- 2026-06-15 resume attempt: refreshed repo state, `git diff --check`, and `codegraph status .`; `.venv/bin/python -m pytest -q` still passed with `525 passed`. A 120-second minimal `claude-opus-4-8` ping timed out, and a full retry again failed with `503 No available accounts`, so final Claude re-review remains the only incomplete gate before commit/push.
- Later 2026-06-15 resume attempt: refreshed repo state, `git diff --check`, `codegraph status .`, and `.venv/bin/python -m pytest -q`; full test suite still passed with `525 passed`. A full `claude-opus-4-8` retry again failed with `503 No available accounts`, so final Claude re-review remains the only incomplete gate before commit/push.
- Additional 2026-06-15 resume attempt: refreshed repo state, `git diff --check`, `codegraph status .`, process status, and `.venv/bin/python -m pytest -q`; full test suite still passed with `525 passed`. A full `claude-opus-4-8` retry again failed with `503 No available accounts`, so final Claude re-review remains the only incomplete gate before commit/push.
- Final 2026-06-15 Claude implementation review: `claude-opus-4-8` with effort `max` passed with Critical findings: 0, Important findings: 0, Minor findings: 0, Verdict: `Proceed`.

Pause note:

- Next step is to commit and push this node. Do not start the next node unless the user explicitly asks to continue.
