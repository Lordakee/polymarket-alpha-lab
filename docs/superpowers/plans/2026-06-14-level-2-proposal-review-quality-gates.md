# Level 2 Proposal Review Quality Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Level 2 Node 4 proposal-review quality gate reports that summarize supplied proposal-review summary reports and identify whether proposal quality appears stable under human review, without approving trades or touching execution surfaces.

**Architecture:** Add a new pure derived-artifact module, `proposal_review_quality.py`, over caller-supplied `TradeProposalReviewSummaryReport` values. It reconstructs each supplied summary report to validate integrity, computes deterministic quality-gate rows and reason-code trend rows, emits frozen report dataclasses, and optionally appends report snapshots to JSONL. The module is report-only and has no readers, loaders, approval routers, broker clients, account state, credentials, browser automation, order payloads, manual-execution imports, execution lifecycle, or live-order behavior.

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
   - Functional-test worker owns `tests/test_proposal_review_quality.py`.
   - Scope/export-test worker owns `tests/test_proposal_review_quality_scope.py`, `tests/test_init.py`, and root-export allowlists in existing scope tests.
   - Main integrator owns `src/polymarket_alpha_lab/proposal_review_quality.py`, `src/polymarket_alpha_lab/__init__.py`, `README.md`, and this plan.
   - Codex subagents use model `gpt-5.5` with reasoning effort `xhigh`.
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
  printf '%s\n' 'Review this Level 2 proposal-review-quality-gates implementation plan for polymarket-alpha-lab before implementation.'
  printf '%s\n' 'This is a read-only, self-contained plan review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, roadmap/spec material, validation gates, existing tests, or plan text.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; plan is implementable as written.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing required review material, unsafe scope, or plan ambiguity that could cause incorrect implementation.'
  printf '%s\n' 'Review specifically: Level 2 proposal-review quality boundary, report-only semantics, no approval workflow engine, no approval queue/router, no broker/request/client surfaces, no private-key handling, no automatic credential use, no account authentication, no unattended execution, no live order placement, no order lifecycle/reconciliation/settlement surfaces, no manual execution import, no scraping/browser automation, no compliance/legal/geographic analysis, supplied TradeProposalReviewSummaryReport validation, duplicate generated_at rejection, no latest-decision selection, sample-size gates, rejection-ratio gates, reason-code concentration gates, duplicate source-proposal proxy gates, deterministic ordering, Decimal and UTC validation, JSONL validate-before-open behavior, public API/export surface, root-export scope-test migration, TDD steps, CodeGraph usage, verification gates, implementation-review self-containment, untracked-file handling, Handoff Summary, and commit/push order.'
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
  printf '%s\n' 'Current proposal review summary source contract:'
  codegraph node src/polymarket_alpha_lab/proposal_review_summary.py
  codegraph node tests/test_proposal_review_summary.py
  codegraph node tests/test_proposal_review_summary_scope.py
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
  printf '%s\n' ''
  printf '%s\n' 'Plan under review:'
  cat docs/superpowers/plans/2026-06-14-level-2-proposal-review-quality-gates.md
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted plan-review terminal state: a fresh Claude review response that explicitly reports `Critical findings: 0`, `Important findings: 0`, and a verdict of `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count line, ambiguous verdict, unsafe scope, missing repository instructions, missing Level 2 context, missing plan text, or transport failure is treated as `Blocked`. After fixing any Critical or Important plan-review finding, rerun the same self-contained Claude plan-review prompt and do not implement until the rerun reaches an accepted terminal state.

If the full prompt is blocked by transport size, rerun a compact prompt that still includes `AGENTS.md`, the Level 2 roadmap excerpt, Gate 6 and Gate 7 excerpts, fresh git status, the full `TradeProposalReviewSummaryReport` public contract, current package-root exports, current export tests, all root-export scope-test snippets, the full target plan text, and the same count/verdict policy.

## Level 2 Node 4 Scope

Level 2 Node 4 adds append-only proposal-review quality gate reports over supplied `TradeProposalReviewSummaryReport` values. A proposal-review quality report tracks summary volume, total review decision volume, rejection-rate stability, rejected reason-code concentration, duplicate source proposal review volume, and report-only quality status. It is audit/reporting material only and does not select trades, route approval, promote strategies, import executions, place orders, or operate accounts.

The module must:

- Consume only caller-supplied `TradeProposalReviewSummaryReport` values.
- Reconstruct each supplied summary report before quality-gate construction so mutated frozen objects or wrong types fail before report construction or log writes.
- Sort summary reports deterministically by UTC `generated_at`, then `config_version`.
- Reject duplicate `generated_at` values.
- Treat duplicate source proposal counts as a proxy metric only; do not resolve conflicts, select latest decisions, or collapse summaries.
- Track total review record count, summed unique source proposal count, duplicate source proposal count, approved decision count, and rejected decision count.
- Track overall rejection ratio as `total_rejected_decision_count / total_review_record_count`, quantized to `Decimal("0.0001")`, or `None` when there are no review records.
- Track latest summary rejection ratio and worst summary rejection ratio from non-empty summaries.
- Track rejected reason-code concentration across supplied summaries without re-reading records.
- Emit exactly five gate rows in this order:
  - `data_integrity`
  - `sample_size`
  - `rejection_ratio`
  - `reason_concentration`
  - `duplicate_source_review_volume`
- Emit a reason-code trend row per reason code with total count, summary-report count, max ratio, and latest ratio.
- Emit frozen report dataclasses.
- Persist report snapshots through `TradeProposalReviewQualityLog(path).append(report)` using append-only JSONL.
- Serialize `Decimal` values as exact strings and datetimes as UTC ISO strings.
- Validate before opening or writing JSONL files.

The module must not:

- Add an approval workflow engine, approval queue, approval router, approver registry, role-based permissions, reviewer authentication, identity verification, latest-decision resolver, finalization state machine, or strategy-promotion signal.
- Convert ready or passing quality reports into order instructions, order requests, broker requests, execution decisions, order lifecycle states, or strategy-promotion packets.
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

- `src/polymarket_alpha_lab/proposal_review_quality.py`
- `tests/test_proposal_review_quality.py`
- `tests/test_proposal_review_quality_scope.py`
- `docs/superpowers/plans/2026-06-14-level-2-proposal-review-quality-gates.md`

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

## Public API Contract

`src/polymarket_alpha_lab/proposal_review_quality.py` must export exactly:

```python
__all__ = (
    "TradeProposalReviewQualityConfig",
    "TradeProposalReviewQualityGateResult",
    "TradeProposalReviewQualityLog",
    "TradeProposalReviewQualityReasonTrend",
    "TradeProposalReviewQualityReport",
    "build_trade_proposal_review_quality_report",
)
```

### Boundary Statement

`DEFAULT_REVIEW_QUALITY_BOUNDARY_STATEMENT` must be exactly:

```python
(
    "This is a report-only proposal-review quality artifact, not an approval "
    "workflow, trade instruction, order instruction, broker request, order "
    "request, account action, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflow, manual "
    "execution import, strategy-promotion signal, or automatic order-placement "
    "authorization."
)
```

Boundary statement validation must require these lowercase substrings:

- `report-only`
- `proposal-review quality`
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

### TradeProposalReviewQualityConfig

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewQualityConfig:
    config_version: str
    min_summary_report_count: int = 1
    min_total_review_record_count: int = 1
    max_overall_rejection_ratio: Decimal = Decimal("0.5000")
    max_worst_summary_rejection_ratio: Decimal = Decimal("0.7500")
    max_reason_code_rejection_share: Decimal = Decimal("0.7500")
    max_duplicate_source_proposal_ratio: Decimal = Decimal("0.2500")
    max_duplicate_source_proposal_count: int = 0
    boundary_statement: str = DEFAULT_REVIEW_QUALITY_BOUNDARY_STATEMENT
```

Validation:

- `config_version` and `boundary_statement` must be canonical nonblank strings.
- Count fields must be nonnegative `int` values, not `bool`.
- Ratio fields must be finite `Decimal` values between `0` and `1`.
- `boundary_statement` must satisfy the boundary statement contract above.

### TradeProposalReviewQualityGateResult

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewQualityGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None
```

Validation:

- `gate_name` must be one of `("data_integrity", "sample_size", "rejection_ratio", "reason_concentration", "duplicate_source_review_volume")`.
- `status` must be one of `("pass", "fail", "incomplete")`.
- `message` must be a canonical nonblank string.
- `observed_value` and `threshold` may be `Decimal`, `int`, canonical string, or `None`; floats and bools are rejected; Decimal values must be finite.

### TradeProposalReviewQualityReasonTrend

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewQualityReasonTrend:
    reason_code: str
    summary_report_count: int
    total_rejected_decision_count: int
    max_rejected_decision_ratio: Decimal
    latest_rejected_decision_ratio: Decimal
```

Validation:

- `reason_code` must be a canonical nonblank string.
- `summary_report_count` and `total_rejected_decision_count` must be positive `int` values, not `bool`.
- Ratios must be finite `Decimal` values between `0` and `1`.

### TradeProposalReviewQualityReport

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewQualityReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    summary_report_count: int
    first_summary_generated_at: datetime | None
    last_summary_generated_at: datetime | None
    total_review_record_count: int
    summed_unique_source_proposal_count: int
    total_duplicate_source_proposal_count: int
    approved_decision_count: int
    rejected_decision_count: int
    overall_rejection_ratio: Decimal | None
    latest_summary_rejection_ratio: Decimal | None
    worst_summary_rejection_ratio: Decimal | None
    max_reason_code_rejection_share: Decimal | None
    duplicate_source_proposal_ratio: Decimal | None
    status: str
    gate_results: tuple[TradeProposalReviewQualityGateResult, ...]
    reason_trends: tuple[TradeProposalReviewQualityReasonTrend, ...]
```

Validation:

- `generated_at`, `first_summary_generated_at`, and `last_summary_generated_at` are normalized to UTC.
- `config_version` must be a canonical nonblank string.
- `report_only` must be `True`.
- `boundary_statement` must satisfy the boundary statement contract above.
- Count fields must be nonnegative `int` values, not `bool`.
- `total_review_record_count == approved_decision_count + rejected_decision_count`.
- `total_duplicate_source_proposal_count <= total_review_record_count`.
- `summed_unique_source_proposal_count <= total_review_record_count`.
- If `summary_report_count == 0`, summary timestamp bounds, all ratios, and `reason_trends` must be absent/empty.
- If `summary_report_count > 0`, summary timestamp bounds must be present and ordered.
- If `total_review_record_count == 0`, decision ratios must be `None`.
- If `total_review_record_count > 0`, `overall_rejection_ratio` must equal `rejected_decision_count / total_review_record_count`, quantized to `Decimal("0.0001")`, and `duplicate_source_proposal_ratio` must equal `total_duplicate_source_proposal_count / total_review_record_count`, quantized to `Decimal("0.0001")`.
- `latest_summary_rejection_ratio`, `worst_summary_rejection_ratio`, and `max_reason_code_rejection_share` must be finite probabilities when present.
- `status` must be one of `("incomplete_review_data", "insufficient_review_sample", "unstable_review_quality", "proposal_review_quality_ready")`.
- `gate_results` must contain exactly the five gate rows in `GATE_NAMES` order.
- `reason_trends` must be a tuple of `TradeProposalReviewQualityReasonTrend` values sorted by `reason_code`.

### Builder Contract

```python
def build_trade_proposal_review_quality_report(
    summaries: Iterable[TradeProposalReviewSummaryReport],
    *,
    config: TradeProposalReviewQualityConfig,
    generated_at: datetime,
) -> TradeProposalReviewQualityReport:
    ...
```

Builder behavior:

- Reject `summaries` when it is a `str` or `bytes`.
- Convert `summaries` to a tuple exactly once and raise `ValueError("summaries must be an iterable of TradeProposalReviewSummaryReport values")` for non-iterables.
- Reject non-`TradeProposalReviewSummaryReport` elements.
- Reconstruct each summary report through `TradeProposalReviewSummaryReport(...)` with nested `TradeProposalReviewReasonCodeSummary` and `TradeProposalReviewBucketSummary` rows copied from the supplied summary before quality-gate construction.
- Reject duplicate `generated_at` values with `ValueError("duplicate summary generated_at values are not allowed")`.
- Reject non-`TradeProposalReviewQualityConfig` config values.
- Reject non-`datetime` `generated_at` values.
- Normalize `generated_at` and summary timestamps to UTC.
- Sort validated summaries by `(_as_utc(summary.generated_at), summary.config_version)`.
- Do not collapse summaries by source proposal; count duplicate-source metrics only.
- Build `reason_trends` from summary `reason_code_summaries`, without reading review records:
  - `summary_report_count` is the number of summaries where the reason code appears.
  - `total_rejected_decision_count` is the sum of `rejected_decision_count` for that reason code.
  - `max_rejected_decision_ratio` is the maximum row ratio across summaries.
  - `latest_rejected_decision_ratio` is the row ratio from the latest summary containing that reason code.
- Sort reason trend rows by `reason_code`.
- Determine gates:
  - `data_integrity`: `incomplete` when no summaries, else `pass`.
  - `sample_size`: `pass` when `summary_report_count >= config.min_summary_report_count` and `total_review_record_count >= config.min_total_review_record_count`, else `fail`, or `incomplete` when no summaries.
  - `rejection_ratio`: `incomplete` when there are no review records, `fail` when `overall_rejection_ratio > config.max_overall_rejection_ratio` or `worst_summary_rejection_ratio > config.max_worst_summary_rejection_ratio`, else `pass`.
  - `reason_concentration`: `incomplete` when there are no rejected decisions or no reason rows, `fail` when `max_reason_code_rejection_share > config.max_reason_code_rejection_share`, else `pass`.
  - `duplicate_source_review_volume`: `incomplete` when there are no review records, `fail` when `duplicate_source_proposal_ratio > config.max_duplicate_source_proposal_ratio` or `total_duplicate_source_proposal_count > config.max_duplicate_source_proposal_count`, else `pass`.
- Determine `status`:
  - `incomplete_review_data` when `summary_report_count == 0` or the data-integrity gate is `incomplete`.
  - `insufficient_review_sample` when the sample-size gate is `fail` or `incomplete`.
  - `unstable_review_quality` when any of the rejection-ratio, reason-concentration, or duplicate-source gates is `fail`.
  - `proposal_review_quality_ready` otherwise.

### Log Contract

`TradeProposalReviewQualityLog(path).append(report)`:

- Accepts only `TradeProposalReviewQualityReport`.
- Reconstructs and validates the report tree before serialization.
- Serializes with `json.dumps(_json_ready(asdict(report)), allow_nan=False, sort_keys=True) + "\n"`.
- Uses append-only mode.
- Creates missing parent directories only after validation and serialization have succeeded.
- Revalidates the nearest existing parent before opening the file.
- Does not expose a reader, loader, updater, deleter, importer, exporter, dispatcher, replay API, external-history API, or manual-execution import.

## Task 1: Functional Tests

**Files:**
- Create: `tests/test_proposal_review_quality.py`

- [x] **Step 1: Write the failing import and fixture stack**

Create `tests/test_proposal_review_quality.py` with:

- Imports: `json`, `FrozenInstanceError`, `replace`, `UTC`, `datetime`, `timedelta`, `timezone`, `Decimal`, `pytest`.
- Import existing Node 3 fixtures and helper from `tests.test_proposal_review_summary`: `proposal_for_source`, `review_record`, `summary_report`.
- New imports from `polymarket_alpha_lab.proposal_review_quality`:

```python
from polymarket_alpha_lab.proposal_review_quality import (
    TradeProposalReviewQualityConfig,
    TradeProposalReviewQualityGateResult,
    TradeProposalReviewQualityLog,
    TradeProposalReviewQualityReasonTrend,
    TradeProposalReviewQualityReport,
    build_trade_proposal_review_quality_report,
)
```

Append this first failing test:

```python
DEFAULT_REVIEW_QUALITY_BOUNDARY_STATEMENT = (
    "This is a report-only proposal-review quality artifact, not an approval "
    "workflow, trade instruction, order instruction, broker request, order "
    "request, account action, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflow, manual "
    "execution import, strategy-promotion signal, or automatic order-placement "
    "authorization."
)


def quality_report(summaries, **overrides):
    values = {
        "summaries": summaries,
        "config": TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            min_summary_report_count=1,
            min_total_review_record_count=1,
            max_duplicate_source_proposal_count=10,
        ),
        "generated_at": datetime(2026, 9, 5, 9, tzinfo=timezone(timedelta(hours=-4))),
    }
    values.update(overrides)
    return build_trade_proposal_review_quality_report(**values)


def rejected_review(index, reason_codes=("liquidity_exit_risk",), **overrides):
    values = {
        "proposal": proposal_for_source(index, market_slug=f"market-{index}"),
        "decision": "rejected",
        "review_reason_codes": reason_codes,
        "review_rationale": "Rejected after checking review-quality proxy inputs.",
        "recorded_at": datetime(2026, 9, 3, 12, index, tzinfo=UTC),
    }
    values.update(overrides)
    return review_record(**values)


def test_build_trade_proposal_review_quality_report_counts_quality_gates():
    first = summary_report(
        [
            review_record(
                proposal=proposal_for_source(1, market_slug="alpha-market"),
                recorded_at=datetime(2026, 9, 3, 12, 1, tzinfo=UTC),
            ),
            rejected_review(2, ("liquidity_exit_risk",)),
        ],
        generated_at=datetime(2026, 9, 4, 8, tzinfo=UTC),
    )
    second = summary_report(
        [
            review_record(
                proposal=proposal_for_source(3, market_slug="beta-market"),
                recorded_at=datetime(2026, 9, 4, 12, 3, tzinfo=UTC),
            ),
            rejected_review(4, ("resolution_ambiguity",)),
        ],
        generated_at=datetime(2026, 9, 5, 8, tzinfo=UTC),
    )

    report = quality_report([second, first])

    assert report.generated_at == datetime(2026, 9, 5, 13, tzinfo=UTC)
    assert report.config_version == "quality-v1"
    assert report.report_only is True
    assert report.summary_report_count == 2
    assert report.first_summary_generated_at == datetime(2026, 9, 4, 8, tzinfo=UTC)
    assert report.last_summary_generated_at == datetime(2026, 9, 5, 8, tzinfo=UTC)
    assert report.total_review_record_count == 4
    assert report.summed_unique_source_proposal_count == 4
    assert report.total_duplicate_source_proposal_count == 0
    assert report.approved_decision_count == 2
    assert report.rejected_decision_count == 2
    assert report.overall_rejection_ratio == Decimal("0.5000")
    assert report.latest_summary_rejection_ratio == Decimal("0.5000")
    assert report.worst_summary_rejection_ratio == Decimal("0.5000")
    assert report.max_reason_code_rejection_share == Decimal("0.5000")
    assert report.duplicate_source_proposal_ratio == Decimal("0.0000")
    assert report.status == "proposal_review_quality_ready"
    assert tuple(row.gate_name for row in report.gate_results) == (
        "data_integrity",
        "sample_size",
        "rejection_ratio",
        "reason_concentration",
        "duplicate_source_review_volume",
    )
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.reason_code for row in report.reason_trends) == (
        "liquidity_exit_risk",
        "resolution_ambiguity",
    )
```

- [x] **Step 2: Run the first failing test**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_quality.py::test_build_trade_proposal_review_quality_report_counts_quality_gates -q
```

Expected: FAIL during import with `ModuleNotFoundError` or `ImportError` because `proposal_review_quality.py` does not exist yet.

- [x] **Step 3: Add remaining failing functional tests**

Add these tests in `tests/test_proposal_review_quality.py`:

- `test_trade_proposal_review_quality_statuses_cover_empty_sample_and_thresholds`
  - Empty summaries produce count `0`, all ratios `None`, empty reason trends, and status `incomplete_review_data`.
  - One summary with two approved records and `min_total_review_record_count=3` produces status `insufficient_review_sample`.
  - One rejected-only summary with `max_overall_rejection_ratio=Decimal("0.2500")` produces status `unstable_review_quality`.
  - One summary whose reason rows have a single reason share over threshold produces status `unstable_review_quality`.
  - One summary with duplicate source proposal count over threshold produces status `unstable_review_quality`.
- `test_trade_proposal_review_quality_reason_trends_are_deterministic`
  - Three summaries with overlapping reason codes produce sorted reason trend rows.
  - `summary_report_count`, `total_rejected_decision_count`, `max_rejected_decision_ratio`, and `latest_rejected_decision_ratio` are correct.
- `test_trade_proposal_review_quality_gate_results_explain_thresholds`
  - Build a failing quality report and assert gate names/statuses/messages plus compact observed/threshold values are populated for sample, rejection-ratio, reason-concentration, and duplicate-source gates.
- `test_trade_proposal_review_quality_rejects_bad_inputs_and_duplicates`
  - Non-iterable `summaries`, string `summaries`, non-summary element, non-config config, non-datetime `generated_at`, and duplicate summary `generated_at` all raise `ValueError`.
- `test_trade_proposal_review_quality_revalidates_mutated_summaries`
  - Mutate a summary `rejection_ratio` to `Decimal("NaN")`; builder raises before quality construction.
  - Mutate nested `reason_code_summaries` into reversed order; builder raises before quality construction.
- `test_trade_proposal_review_quality_dataclasses_are_frozen_and_validate_invariants`
  - `TradeProposalReviewQualityConfig`, `TradeProposalReviewQualityGateResult`, `TradeProposalReviewQualityReasonTrend`, and `TradeProposalReviewQualityReport` are frozen.
  - `replace(...)` rejects invalid counts, invalid ratio thresholds, invalid gate names/statuses, invalid reason trend ratios, invalid status, wrong gate order, unsorted reason trends, `report_only=False`, inconsistent counts, wrong ratios, and invalid boundary text.
- `test_trade_proposal_review_quality_boundary_statement_contract`
  - The default boundary statement equals the contract in this plan.
  - Incomplete boundary statements raise `ValueError`.
- `test_trade_proposal_review_quality_log_appends_jsonl_report`
  - Append one report and assert JSON values: `generated_at`, `report_only`, counts, ratios as strings, nested gate rows, and nested reason trend rows.
- `test_trade_proposal_review_quality_log_appends_without_overwriting_and_creates_parent_dirs`
  - Append the same report twice to a nested path and assert two JSONL lines.
- `test_trade_proposal_review_quality_log_rejects_invalid_paths_and_inputs`
  - Reject non-path path, blank path, existing directory path, parent-file path, and non-report append input.
- `test_trade_proposal_review_quality_log_preserves_existing_file_when_validation_fails`
  - Mutate a nested gate result field to `Decimal("NaN")`, append to an existing file, assert content is unchanged.
- `test_trade_proposal_review_quality_log_rejects_non_finite_decimal_before_open`
  - Mutate `overall_rejection_ratio` to `Decimal("NaN")`, append to a missing file, assert file does not exist.

- [ ] **Step 4: Run the full new functional test file and keep the expected failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_quality.py -q
```

Expected: FAIL because the new module and public API do not exist yet.

## Task 2: Scope And Export Tests

**Files:**
- Create: `tests/test_proposal_review_quality_scope.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_analytics_scope.py`
- Modify: `tests/test_analytics_history_scope.py`
- Modify: `tests/test_forecast_evidence_scope.py`
- Modify: `tests/test_manual_review_queue_scope.py`
- Modify: `tests/test_proposal_packet_scope.py`
- Modify: `tests/test_proposal_review_scope.py`
- Modify: `tests/test_proposal_review_summary_scope.py`

- [x] **Step 1: Add the new module scope test**

Create `tests/test_proposal_review_quality_scope.py` with the AST helper structure used by `tests/test_proposal_review_summary_scope.py`.

Use these expected exports:

```python
EXPECTED_PROPOSAL_REVIEW_QUALITY_EXPORTS = {
    "TradeProposalReviewQualityConfig",
    "TradeProposalReviewQualityGateResult",
    "TradeProposalReviewQualityLog",
    "TradeProposalReviewQualityReasonTrend",
    "TradeProposalReviewQualityReport",
    "build_trade_proposal_review_quality_report",
}
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
    "polymarket_alpha_lab.proposal_review_summary",
}
```

Use this first-party symbol allowlist:

```python
EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.proposal_review_summary": {
        "TradeProposalReviewBucketSummary",
        "TradeProposalReviewReasonCodeSummary",
        "TradeProposalReviewSummaryReport",
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

Use compound forbidden name fragments so intended inert review-quality names survive:

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

- `test_proposal_review_quality_module_imports_only_allowed_dependencies`
- `test_proposal_review_quality_module_does_not_import_forbidden_surfaces`
- `test_proposal_review_quality_module_uses_only_allowed_first_party_symbols`
- `test_proposal_review_quality_module_does_not_define_forbidden_live_or_workflow_names`
- `test_trade_proposal_review_quality_public_exports_are_report_only`
- `test_package_root_exports_do_not_leak_forbidden_level_2_node_4_surfaces`

- [x] **Step 2: Update package export tests**

In `tests/test_init.py`, import the six new public objects from `polymarket_alpha_lab.proposal_review_quality` and add `test_level_2_node_4_public_api_exports()` asserting package-root identity bindings and `lab.__all__` membership for:

```python
{
    "TradeProposalReviewQualityConfig",
    "TradeProposalReviewQualityGateResult",
    "TradeProposalReviewQualityLog",
    "TradeProposalReviewQualityReasonTrend",
    "TradeProposalReviewQualityReport",
    "build_trade_proposal_review_quality_report",
}
```

- [x] **Step 3: Update existing root-export scope allowlists**

In these files, add `EXPECTED_PROPOSAL_REVIEW_QUALITY_EXPORTS` with the six exports above and include it in `EXPECTED_LEVEL_2_ARTIFACT_EXPORTS`:

- `tests/test_analytics_scope.py`
- `tests/test_analytics_history_scope.py`
- `tests/test_forecast_evidence_scope.py`
- `tests/test_manual_review_queue_scope.py`
- `tests/test_proposal_packet_scope.py`
- `tests/test_proposal_review_scope.py`
- `tests/test_proposal_review_summary_scope.py`

Keep existing forbidden-fragment checks intact. Do not weaken unrelated scope tests.

- [x] **Step 4: Run the new and changed scope/export tests and keep the expected failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_quality_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py -q
```

Expected: FAIL because the implementation module and package-root exports do not exist yet.

## Task 3: Implement Proposal Review Quality Module

**Files:**
- Create: `src/polymarket_alpha_lab/proposal_review_quality.py`

- [x] **Step 1: Create the module shell and public dataclasses**

Create `src/polymarket_alpha_lab/proposal_review_quality.py` with:

- Standard-library imports only: `json`, `Iterable`, `asdict`, `dataclass`, `UTC`, `datetime`, `Decimal`, `ROUND_HALF_EVEN`, `Path`, `Any`.
- First-party imports only:

```python
from polymarket_alpha_lab.proposal_review_summary import (
    TradeProposalReviewBucketSummary,
    TradeProposalReviewReasonCodeSummary,
    TradeProposalReviewSummaryReport,
)
```

- Constants:
  - `RATIO_QUANTUM = Decimal("0.0001")`
  - `ZERO = Decimal("0")`
  - `ONE = Decimal("1")`
  - `GATE_NAMES = ("data_integrity", "sample_size", "rejection_ratio", "reason_concentration", "duplicate_source_review_volume")`
  - `GATE_STATUSES = ("pass", "fail", "incomplete")`
  - `REPORT_STATUSES = ("incomplete_review_data", "insufficient_review_sample", "unstable_review_quality", "proposal_review_quality_ready")`
  - the default boundary statement from this plan.
- The six public exports from the Public API Contract section.
- Frozen dataclasses from the Public API Contract section.

- [x] **Step 2: Implement validation helpers**

Implement helpers consistent with `proposal_review_summary.py`:

- `_as_utc(value: datetime) -> datetime`
- `_require_canonical_string(field_name: str, value: str) -> None`
- `_require_boundary_statement(value: str) -> None`
- `_require_nonnegative_int(field_name: str, value: int) -> None`
- `_require_positive_int(field_name: str, value: int) -> None`
- `_require_decimal(field_name: str, value: Decimal) -> None`
- `_require_finite_decimal(field_name: str, value: Decimal) -> None`
- `_require_probability_decimal(field_name: str, value: Decimal) -> None`
- `_require_optional_probability_decimal(field_name: str, value: Decimal | None) -> None`
- `_require_gate_value(field_name: str, value: Decimal | int | str | None) -> None`
- `_quantize_ratio(value: Decimal) -> Decimal`
- `_ratio_from_counts(numerator: int, denominator: int) -> Decimal`
- `_optional_ratio_from_counts(numerator: int, denominator: int) -> Decimal | None`
- `_normalize_typed_tuple(field_name: str, values: Iterable[Any], expected_type: type[Any]) -> tuple[Any, ...]`

`_quantize_ratio` must use `value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)` and reject non-finite values.

- [x] **Step 3: Implement summary/report cloning and JSON helpers**

Implement:

- `_clone_summary_report(summary: TradeProposalReviewSummaryReport) -> TradeProposalReviewSummaryReport`, reconstructing nested `TradeProposalReviewReasonCodeSummary` and `TradeProposalReviewBucketSummary` rows and then the summary report.
- `_validate_report_tree(report: TradeProposalReviewQualityReport) -> TradeProposalReviewQualityReport`, reconstructing nested gate and reason-trend rows and returning a validated report.
- `_json_ready(value: Any) -> Any`, matching existing behavior: `Decimal` to `str`, `datetime` to UTC ISO string, reject `float`, recurse into dict/list/tuple, require dict keys to be strings.
- `_normalize_log_path(value: Path | str) -> Path`
- `_validate_log_parent(path: Path) -> None`

The log append method must compute JSON before creating parent directories or opening files.

- [x] **Step 4: Implement quality builders**

Implement:

- `build_trade_proposal_review_quality_report(...)`
- `_build_reason_trends(summaries: tuple[TradeProposalReviewSummaryReport, ...]) -> tuple[TradeProposalReviewQualityReasonTrend, ...]`
- `_build_gate_results(...) -> tuple[TradeProposalReviewQualityGateResult, ...]`
- `_quality_status(gate_results: tuple[TradeProposalReviewQualityGateResult, ...]) -> str`
- `_max_optional_ratio(values: Iterable[Decimal | None]) -> Decimal | None`

Use deterministic grouping:

```python
reason_rows_by_code: dict[str, list[TradeProposalReviewReasonCodeSummary]] = {}
for summary in summaries:
    for row in summary.reason_code_summaries:
        reason_rows_by_code.setdefault(row.reason_code, []).append(row)

reason_trends = []
for reason_code in sorted(reason_rows_by_code):
    rows = reason_rows_by_code[reason_code]
    reason_trends.append(
        TradeProposalReviewQualityReasonTrend(
            reason_code=reason_code,
            summary_report_count=len(rows),
            total_rejected_decision_count=sum(row.rejected_decision_count for row in rows),
            max_rejected_decision_ratio=max(row.rejected_decision_ratio for row in rows),
            latest_rejected_decision_ratio=rows[-1].rejected_decision_ratio,
        )
    )
```

Rows are safe because summaries are sorted before calling `_build_reason_trends`.

- [x] **Step 5: Run focused functional tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_quality.py -q
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
from polymarket_alpha_lab.proposal_review_quality import (
    TradeProposalReviewQualityConfig,
    TradeProposalReviewQualityGateResult,
    TradeProposalReviewQualityLog,
    TradeProposalReviewQualityReasonTrend,
    TradeProposalReviewQualityReport,
    build_trade_proposal_review_quality_report,
)
```

Add the same six names to `__all__` near the existing proposal-review exports.

- [x] **Step 2: Update README status and API sections**

In `README.md`:

- Extend the Phase 1 Scope sentence to mention `proposal-review quality gate artifacts`.
- Add `Level 2 Node 4 Status` after Level 2 Node 3:

```markdown
## Level 2 Node 4 Status

Level 2 Node 4 adds report-only proposal-review quality gate artifacts over supplied `TradeProposalReviewSummaryReport` values. It tracks summary volume, review decision volume, rejection-rate stability, rejected reason-code concentration, and duplicate source proposal review volume for audit only; it is not an approval workflow, trade instruction, order instruction, broker request, order request, account action, strategy-promotion signal, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, execution client, or transport client; build broker or order request payloads; reconcile exchange accounts; import manual executions; or perform compliance/legal/geographic analysis.
```

- Add `Level 2 Node 4 Python API`:

```markdown
## Level 2 Node 4 Python API

Node 4 is exposed through Python APIs:

- Configure proposal-review quality gates with `TradeProposalReviewQualityConfig(config_version="quality-v1")`.
- Build proposal-review quality reports with `build_trade_proposal_review_quality_report(summaries, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalReviewQualityReport`.
- Inspect quality gate rows with `TradeProposalReviewQualityGateResult` and rejected reason-code trends with `TradeProposalReviewQualityReasonTrend`.
- Persist proposal-review quality snapshots with `TradeProposalReviewQualityLog(path).append(report)`.
```

- Add `proposal_review_quality.py`, `test_proposal_review_quality.py`, and `test_proposal_review_quality_scope.py` to Repository Layout.
- Add the new plan file to the plans list.

- [x] **Step 3: Run export and scope tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_quality_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py -q
```

Expected: PASS.

## Task 5: Verification, Claude Implementation Review, Handoff, Commit, Push

**Files:**
- Modify: `docs/superpowers/plans/2026-06-14-level-2-proposal-review-quality-gates.md`

- [x] **Step 1: Run local verification**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_quality.py tests/test_proposal_review_quality_scope.py tests/test_init.py -q
.venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py -q
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

- [x] **Step 2: Run Claude implementation review**

Run this self-contained command after implementation and before commit:

```bash
{
  printf '%s\n' 'Review this completed Level 2 proposal-review-quality-gates implementation for polymarket-alpha-lab.'
  printf '%s\n' 'This is a read-only implementation review. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, roadmap/spec material, validation gates, implementation diff, tests, or plan text.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; implementation is ready to commit.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, unsafe scope, failing/missing verification, missing review material, or ambiguity that could cause incorrect behavior.'
  printf '%s\n' 'Review specifically: report-only review-quality boundary, no approval workflow/queue/router, no broker/request/client/order/account/credential surfaces, no live execution, no manual execution import, no scraping/browser automation, no compliance/legal/geographic analysis, validation of supplied TradeProposalReviewSummaryReport values, duplicate generated_at rejection, no latest-decision selection, sample-size gates, rejection-ratio gates, reason-code concentration gates, duplicate-source proxy gates, deterministic sorting, Decimal ratio quantization, UTC datetime normalization, JSONL validate-before-open behavior, package exports, scope tests, README updates, local verification output, CodeGraph status, Handoff Summary, and commit readiness.'
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
  cat docs/superpowers/plans/2026-06-14-level-2-proposal-review-quality-gates.md
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'CodeGraph status:'
  codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Verification output:'
  printf '%s\n' '$ .venv/bin/python -m pytest tests/test_proposal_review_quality.py tests/test_proposal_review_quality_scope.py tests/test_init.py -q'
  .venv/bin/python -m pytest tests/test_proposal_review_quality.py tests/test_proposal_review_quality_scope.py tests/test_init.py -q
  printf '%s\n' '$ .venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py -q'
  .venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py -q
  printf '%s\n' '$ .venv/bin/python -m pytest -q'
  .venv/bin/python -m pytest -q
  printf '%s\n' '$ git diff --check'
  git diff --check && printf '%s\n' 'git diff --check passed'
  printf '%s\n' ''
  printf '%s\n' 'Tracked diff:'
  git diff -- src/polymarket_alpha_lab/__init__.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py README.md docs/superpowers/plans/2026-06-14-level-2-proposal-review-quality-gates.md
  printf '%s\n' ''
  printf '%s\n' 'Full contents of changed and untracked files:'
  cat src/polymarket_alpha_lab/proposal_review_quality.py
  cat tests/test_proposal_review_quality.py
  cat tests/test_proposal_review_quality_scope.py
  cat src/polymarket_alpha_lab/__init__.py
  cat tests/test_init.py
  cat tests/test_analytics_scope.py
  cat tests/test_analytics_history_scope.py
  cat tests/test_forecast_evidence_scope.py
  cat tests/test_manual_review_queue_scope.py
  cat tests/test_proposal_packet_scope.py
  cat tests/test_proposal_review_scope.py
  cat tests/test_proposal_review_summary_scope.py
  cat README.md
  cat docs/superpowers/plans/2026-06-14-level-2-proposal-review-quality-gates.md
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

- [ ] **Step 4: Append final Handoff Summary**

Append a dated Handoff Summary to this plan containing:

- Files changed.
- Verification command outputs.
- Claude plan review counts and verdict.
- Claude implementation review counts and verdict.
- Any remaining Minor findings and why they are non-blocking.
- Next recommended safe node, or explicit stop point if no safe node remains under current constraints.

The Handoff Summary is committed before the final commit hash exists, so it must not claim to contain its own commit hash. Report the final commit hash after commit and push in the assistant final response for the node.

- [ ] **Step 5: Commit and push**

Run:

```bash
git add src/polymarket_alpha_lab/proposal_review_quality.py src/polymarket_alpha_lab/__init__.py tests/test_proposal_review_quality.py tests/test_proposal_review_quality_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py README.md docs/superpowers/plans/2026-06-14-level-2-proposal-review-quality-gates.md
git commit -m "feat: add level 2 proposal review quality gates"
git push origin main
```

Expected: commit succeeds and push updates `origin/main`.

## Handoff Summary

Initial plan drafted on 2026-06-14. Claude plan review passed before implementation with `Critical findings: 0`, `Important findings: 0`, `Minor findings: 5`, and `Verdict: Proceed`.

Post-implementation, pre-final-review handoff on 2026-06-14:

- Implementation has been completed for `src/polymarket_alpha_lab/proposal_review_quality.py`.
- Package-root exports have been added in `src/polymarket_alpha_lab/__init__.py`.
- Functional tests have been added in `tests/test_proposal_review_quality.py`, including additional RED/GREEN coverage for non-empty zero-review summaries, status-priority invariants, and latest/worst/max ratio relationships after local implementation review found those edge cases.
- Scope/export tests have been added or migrated in `tests/test_proposal_review_quality_scope.py`, `tests/test_init.py`, `tests/test_analytics_scope.py`, `tests/test_analytics_history_scope.py`, `tests/test_forecast_evidence_scope.py`, `tests/test_manual_review_queue_scope.py`, `tests/test_proposal_packet_scope.py`, `tests/test_proposal_review_scope.py`, and `tests/test_proposal_review_summary_scope.py`.
- README now documents Level 2 Node 4 status, Python API, and repository layout entries.
- Local verification before Claude implementation review:
  - `.venv/bin/python -m pytest tests/test_proposal_review_quality.py -q` -> `13 passed`
  - `.venv/bin/python -m pytest tests/test_proposal_review_quality_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py -q` -> `56 passed`
  - `.venv/bin/python -m pytest -q` -> `503 passed`
  - `git diff --check` -> passed
  - `codegraph sync` -> synced changed files
  - `codegraph status .` -> index is up to date
- Task 1 Step 4 was not separately run as a full-file RED command before production code was created; the focused import RED and scope/export RED were captured before implementation.
- Claude implementation review passed with `Critical findings: 0`, `Important findings: 0`, `Minor findings: 3`, and `Verdict: Proceed`.
- Remaining Claude Minor findings are non-blocking:
  - Task 1 Step 4 full-file RED command was not separately executed before implementation; the focused import RED and scope/export RED were captured before implementation, and final focused/full suites pass.
  - Handoff wording was clarified from "Pre-implementation-review" to "Post-implementation, pre-final-review".
  - Additional edge-case tests for non-empty zero-review summaries and ratio relationship invariants were added during local implementation review beyond the original plan.
- Final handoff, commit, and push remain pending.

Final handoff on 2026-06-14:

- Files changed:
  - `README.md`
  - `src/polymarket_alpha_lab/__init__.py`
  - `src/polymarket_alpha_lab/proposal_review_quality.py`
  - `tests/test_proposal_review_quality.py`
  - `tests/test_proposal_review_quality_scope.py`
  - `tests/test_init.py`
  - `tests/test_analytics_scope.py`
  - `tests/test_analytics_history_scope.py`
  - `tests/test_forecast_evidence_scope.py`
  - `tests/test_manual_review_queue_scope.py`
  - `tests/test_proposal_packet_scope.py`
  - `tests/test_proposal_review_scope.py`
  - `tests/test_proposal_review_summary_scope.py`
  - `docs/superpowers/plans/2026-06-14-level-2-proposal-review-quality-gates.md`
- Verification before final commit:
  - `.venv/bin/python -m pytest tests/test_proposal_review_quality.py tests/test_proposal_review_quality_scope.py tests/test_init.py -q` -> `30 passed`
  - `.venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py tests/test_proposal_packet_scope.py tests/test_proposal_review_scope.py tests/test_proposal_review_summary_scope.py -q` -> `39 passed`
  - `.venv/bin/python -m pytest -q` -> `503 passed`
  - `git diff --check` -> passed
  - `codegraph sync` -> synced changed files
  - `codegraph status .` -> index is up to date
- Claude plan review: `Critical findings: 0`, `Important findings: 0`, `Minor findings: 5`, `Verdict: Proceed`.
- Claude implementation review: `Critical findings: 0`, `Important findings: 0`, `Minor findings: 3`, `Verdict: Proceed`.
- Stop point: Level 2 Node 4 is ready to commit and push. Per latest user instruction, pause after this node instead of starting the next node.
