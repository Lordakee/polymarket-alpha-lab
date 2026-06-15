# Level 2 Proposal Evidence Comparison History Batch Health Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a report-only batch-health artifact that summarizes caller-supplied proposal evidence comparison history reports for audit and quality checks.

**Architecture:** Create a focused `proposal_evidence_comparison_history_batch_health.py` module that consumes only in-memory `TradeProposalEvidenceComparisonHistoryReport` objects from Level 2 Node 10. It clones and revalidates each supplied history report, then summarizes status frequencies, config-version coverage, duplicate generated-at indicators, duplicate fingerprint indicators, finding-code frequencies, source-transition coverage, and rate gates. The artifact stays report-only and offline: it never reads history files, discovers logs, fetches data, ranks investments, recommends trades, approves proposals, handles credentials, or touches execution.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, UTC `datetime`, JSONL append-only persistence, pytest, CodeGraph, and local Claude Code review with model `claude-opus-4-8` using effort `max`.

---

## Scope Boundaries

This node consumes only caller-supplied, in-memory `TradeProposalEvidenceComparisonHistoryReport` objects from `polymarket_alpha_lab.proposal_evidence_comparison_history`. The word "batch" means an ordered summary over objects supplied by the caller, not file discovery, log replay, archive loading, globbing, or historical data fetching.

This node must not consume raw `TradeProposalEvidenceComparisonReport` values, raw `PaperForecastEvidenceReport` values, raw `TradeProposalReviewDossierBatchReport` values, raw forecast observations, raw proposal packets, raw proposal-review records, dossier reports, market scores, order books, paper positions, NAV snapshots, API payloads, JSONL files, archived payloads, external history, web pages, account state, credentials, wallets, broker payloads, execution records, outcome data, settlement data, or reconciliation data.

This node must not fetch market/order-book/price/outcome/account data, read JSONL logs, replay history, glob files, scrape websites, run browser automation, authenticate, handle credentials or private keys, open user WebSockets, run heartbeat logic, build order requests, place/submit/sign/send/create/cancel orders, select approved proposals, select latest decisions, resolve conflicting reviews, rank investments, recommend trades, promote strategies, review settlement, reconcile positions or exchange accounts, import manual executions, or perform compliance/legal/geographic analysis.

This node must reject convenience inputs that would imply a loader surface: strings, bytes, mappings/dicts, paths, serialized JSON, JSONL lines, and subclasses of `TradeProposalEvidenceComparisonHistoryReport`.

Use the phrase "batch health" for the output artifact. Do not call the output realized false-positive analysis, trade outcome analysis, settlement analysis, or profitability analysis.

Allowed first-party imports in the production module are limited to import-from symbols from `polymarket_alpha_lab.proposal_evidence_comparison_history`:

```python
TradeProposalEvidenceComparisonHistoryGateResult
TradeProposalEvidenceComparisonHistoryStatusRow
TradeProposalEvidenceComparisonHistoryConfigVersionSummary
TradeProposalEvidenceComparisonHistoryFindingSummary
TradeProposalEvidenceComparisonHistorySourceTransition
TradeProposalEvidenceComparisonHistoryReport
```

Behavior tests may additionally import `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT` from `polymarket_alpha_lab.proposal_evidence_comparison_history` to construct static Node 10 history-report fixtures. The production module must not import that constant.

Do not import `TradeProposalEvidenceComparisonHistoryLog` into the Node 11 production module, tests, or README examples, and do not accept it as a history-report iterable, history-report element, loader, reader, replay handle, or other input source. It is only a Node 10 append-only output sink for history reports, not a source of supplied `TradeProposalEvidenceComparisonHistoryReport` objects for this node. The only log class exposed by this node is `TradeProposalEvidenceComparisonHistoryBatchHealthLog`, and it is an output-only append sink for validated batch-health reports.

The new module must implement its own local `_json_ready` helper for `Decimal`, UTC `datetime`, tuple/list, and dict normalization. Do not import private helpers such as `_json_ready`, `_as_utc`, `_require_*`, clone helpers, or validation helpers from Node 10 or any other first-party module.

Do not import raw Node 9 comparison modules or builders; this node summarizes already-built Node 10 history reports and must not rebuild Node 9 reports or fetch raw inputs.

## Public API

Create `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health.py` with:

```python
__all__ = (
    "TradeProposalEvidenceComparisonHistoryBatchHealthConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_report",
)
```

Define `DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_BOUNDARY_STATEMENT` exactly as:

```python
DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_BOUNDARY_STATEMENT = (
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
)
```

This boundary constant is module-internal despite its uppercase name. It must not be included in the module `__all__`, package-root imports, package-root `__all__`, or public export scope allowlists.

Public dataclasses:

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthConfig:
    config_version: str
    min_history_report_count: int = 1
    max_incomplete_history_ratio: Decimal = Decimal("0.0000")
    max_divergent_history_ratio: Decimal = Decimal("0.0000")
    max_unstable_history_ratio: Decimal = Decimal("0.0000")
    max_duplicate_generated_at_ratio: Decimal = Decimal("0.0000")
    max_duplicate_fingerprint_ratio: Decimal = Decimal("0.0000")
    boundary_statement: str = (
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_BOUNDARY_STATEMENT
    )
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow:
    history_status: str
    history_count: int
    history_ratio: Decimal | None
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary:
    history_config_version: str
    history_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary:
    generated_at: datetime
    duplicate_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary:
    report_fingerprint: str
    duplicate_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary:
    finding_code: str
    severity: str
    source_name: str
    history_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary:
    source_name: str
    from_source_status: str
    to_source_status: str
    transition_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    history_report_count: int
    complete_history_report_count: int
    incomplete_history_report_count: int
    divergent_history_report_count: int
    unstable_history_report_count: int
    duplicate_generated_at_count: int
    duplicate_fingerprint_count: int
    incomplete_history_ratio: Decimal | None
    divergent_history_ratio: Decimal | None
    unstable_history_ratio: Decimal | None
    duplicate_generated_at_ratio: Decimal | None
    duplicate_fingerprint_ratio: Decimal | None
    first_history_generated_at: datetime | None
    last_history_generated_at: datetime | None
    status: str
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthGateResult, ...]
    status_rows: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow, ...]
    config_version_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary,
        ...,
    ]
    duplicate_generated_at_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary,
        ...,
    ]
    duplicate_fingerprint_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary,
        ...,
    ]
    finding_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary,
        ...,
    ]
    source_transition_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary,
        ...,
    ]
```

```python
@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthLog:
    path: Path | str

    def append(self, report: TradeProposalEvidenceComparisonHistoryBatchHealthReport) -> None:
        ...
```

Builder signature:

```python
def build_trade_proposal_evidence_comparison_history_batch_health_report(
    history_reports: Iterable[TradeProposalEvidenceComparisonHistoryReport],
    *,
    config: TradeProposalEvidenceComparisonHistoryBatchHealthConfig,
    generated_at: datetime,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthReport:
    ...
```

## Status And Gate Rules

Gate names:

```python
GATE_NAMES = (
    "history_sample",
    "incomplete_history_rate",
    "divergent_history_rate",
    "unstable_history_rate",
    "duplicate_generated_at_rate",
    "duplicate_fingerprint_rate",
)
```

Gate statuses are `pass`, `fail`, or `incomplete`.

Report statuses:

```python
REPORT_STATUSES = (
    "incomplete_history_batch_health",
    "duplicate_generated_at_batch_health",
    "duplicate_fingerprint_batch_health",
    "divergent_history_batch_health",
    "unstable_history_batch_health",
    "proposal_evidence_comparison_history_batch_health_ready",
)
```

Status mapping:

- If `history_sample` is `incomplete`, report status is `incomplete_history_batch_health`.
- Else if `duplicate_generated_at_rate` is `fail`, report status is `duplicate_generated_at_batch_health`.
- Else if `duplicate_fingerprint_rate` is `fail`, report status is `duplicate_fingerprint_batch_health`.
- Else if `divergent_history_rate` is `fail`, report status is `divergent_history_batch_health`.
- Else if `unstable_history_rate` is `fail`, report status is `unstable_history_batch_health`.
- Else if `incomplete_history_rate` is `fail`, report status is `incomplete_history_batch_health`.
- Else if any gate is `incomplete`, report status is `incomplete_history_batch_health`.
- Else report status is `proposal_evidence_comparison_history_batch_health_ready`.

Gate semantics:

- `history_sample`: pass when `history_report_count >= config.min_history_report_count`; incomplete otherwise. Observed value is `history_report_count`; threshold is `config.min_history_report_count`.
- `incomplete_history_rate`: incomplete when `incomplete_history_ratio is None`, pass when ratio is less than or equal to `config.max_incomplete_history_ratio`, fail otherwise.
- `divergent_history_rate`: incomplete when `divergent_history_ratio is None`, pass when ratio is less than or equal to `config.max_divergent_history_ratio`, fail otherwise.
- `unstable_history_rate`: incomplete when `unstable_history_ratio is None`, pass when ratio is less than or equal to `config.max_unstable_history_ratio`, fail otherwise.
- `duplicate_generated_at_rate`: incomplete when no history reports are supplied, pass when duplicate ratio is less than or equal to `config.max_duplicate_generated_at_ratio`, fail otherwise.
- `duplicate_fingerprint_rate`: incomplete when no history reports are supplied, pass when duplicate ratio is less than or equal to `config.max_duplicate_fingerprint_ratio`, fail otherwise.

Gate payload rules:

- `history_sample.observed_value` must be the exact `int` `history_report_count`; `history_sample.threshold` must be the exact nonnegative `int` `config.min_history_report_count`; `history_sample.status` must match those values.
- Each rate gate's `observed_value` must equal the corresponding derived ratio as an exact `Decimal`, or be `None` when that ratio is unavailable because `history_report_count == 0`.
- The builder must set each rate gate's `threshold` to the corresponding config max threshold as an exact `Decimal`.
- Because the built report does not store its originating config thresholds, report-tree validation and `append()` validation must verify rate gate threshold type/range and status-vs-observed/threshold consistency, but must not claim to recover or compare against the original config object.
- Each rate gate's `status` must match the derived payload: `incomplete` when observed value is `None`, `pass` when observed value is less than or equal to threshold, and `fail` otherwise.
- Reject bools, floats, strings, stale counts, stale ratios, wrong threshold types, wrong observed-value types, and statuses that do not match the observed/threshold payloads.

Counting rules:

- `complete_history_report_count`: number of supplied history reports with status `proposal_evidence_comparison_history_ready`.
- `incomplete_history_report_count`: number of supplied history reports with status `incomplete_comparison_history`.
- `divergent_history_report_count`: number of supplied history reports with status `divergent_comparison_history`.
- `unstable_history_report_count`: number of supplied history reports with status `unstable_comparison_history`.
- Duplicate generated-at count: count all supplied history reports that belong to a duplicate normalized-`generated_at` collision group, not only extras beyond the first item. Examples: `[A, A, B]` produces `duplicate_generated_at_count == 2`; `[A, A, A, B, B]` produces `duplicate_generated_at_count == 5`.
- Duplicate fingerprint count: count all supplied history reports that belong to a duplicate canonical-fingerprint collision group, not only extras beyond the first item. Examples: `[fp1, fp1, fp2]` produces `duplicate_fingerprint_count == 2`; `[fp1, fp1, fp1, fp2, fp2]` produces `duplicate_fingerprint_count == 5`.
- Ratios are `None` when `history_report_count == 0`; otherwise quantize to `Decimal("0.0001")` with `ROUND_HALF_EVEN`.

Ordering and aggregation rules:

- Clone/revalidate every exact `TradeProposalEvidenceComparisonHistoryReport` first. All aggregation must use the cloned objects, whose dataclass construction has normalized datetimes to UTC.
- Sort cloned history reports with `sorted(cloned_reports, key=lambda report: (report.generated_at, report.config_version, report.status))`. Python sort stability preserves caller order for reports with identical `(generated_at, config_version, status)` keys as an internal implementation detail, but this tied-key order is not a public report assertion because the aggregate report exposes no per-input sequence field.
- `first_history_generated_at` and `last_history_generated_at` come from the sorted cloned reports' normalized `generated_at` values, not from unvalidated caller objects.
- Duplicate generated-at groups are keyed by each cloned report's normalized `generated_at`; duplicate fingerprint groups are keyed by each cloned report's canonical JSON fingerprint.
- `source_transition_summaries` aggregate each cloned history report's existing Node 10 `source_transitions` rows by `(source_name, from_source_status, to_source_status)` and sum their existing `transition_count` values. Do not derive new source transitions by comparing one history report with another history report unless a future plan explicitly adds that behavior.

Rows:

- `status_rows`: exactly one row per Node 10 history status, sorted by `history_status`. `history_ratio` is `None` when `history_report_count == 0`; otherwise it is `status_count / history_report_count` quantized to `Decimal("0.0001")` with `ROUND_HALF_EVEN`.
- `config_version_summaries`: one row per distinct `history_config_version`, sorted by `history_config_version`.
- `duplicate_generated_at_summaries`: one row per duplicate normalized `generated_at`, sorted by `generated_at`; each row's `duplicate_count` is the full collision-group size. Example: three reports sharing the same normalized timestamp produce one summary row with `duplicate_count == 3`, not `2`.
- `duplicate_fingerprint_summaries`: one row per duplicate fingerprint, sorted by `report_fingerprint`; each row's `duplicate_count` is the full collision-group size. Example: two reports sharing the same fingerprint produce one summary row with `duplicate_count == 2`, not `1`.
- `finding_summaries`: one row per distinct `(severity, source_name, finding_code)` found across supplied history reports, sorted by that tuple. `history_count` counts cloned history reports containing that key at least once, not the sum of Node 10 `comparison_count` values from the nested finding summaries. A single cloned history report contributes at most one count for a key.
- `source_transition_summaries`: grouped sums of the existing Node 10 `source_transitions` already present on cloned history reports, sorted by `(source_name, from_source_status, to_source_status)`. They must not be inferred by comparing adjacent reports or any other pair of history reports.

Validation requirements:

- Distinguish builder provenance invariants from persisted-report invariants. The builder must derive status totals, duplicate groups, finding counts, and source-transition grouped sums from cloned caller-supplied history reports. `__post_init__`, report-tree validation, and `append()` must validate only self-contained facts stored on the batch-health report; they must not claim to rederive provenance from original history reports, reload source inputs, or replay logs.
- Reject strings, bytes, mappings/dicts, `Path` values, serialized JSON, JSONL lines, append-only log objects such as `TradeProposalEvidenceComparisonHistoryLog`, and any non-iterable convenience input before iterating history-report values.
- Reject non-exact `TradeProposalEvidenceComparisonHistoryReport` inputs.
- Clone/revalidate every history report by reconstructing all Node 10 dataclasses.
- Do not reject duplicate history-report `generated_at` values; summarize and gate them as a collision signal. Do not silently deduplicate, resolve, or select a latest object.
- Validate all row tuples are exact typed tuples.
- Validate `gate_results` order equals `GATE_NAMES`.
- Validate every gate payload exactly: sample gate observed value is an exact nonnegative `int` matching `history_report_count`; sample gate threshold is an exact nonnegative `int`; rate gate observed values are exact `Decimal` values matching their report ratios or `None` when unavailable; rate gate thresholds are exact finite probability `Decimal` values; each gate status matches its observed/threshold payload. Builder tests must separately assert thresholds are copied from the supplied config.
- Validate `status_rows` contain exactly the four Node 10 history report statuses sorted by `history_status`.
- Builder tests must prove `complete_history_report_count`, `incomplete_history_report_count`, `divergent_history_report_count`, and `unstable_history_report_count` are derived from cloned history-report statuses. Report-tree validation must verify those top-level counts match the corresponding `status_rows` counts.
- Validate `history_report_count` equals the sum of the four stored history-status totals.
- Validate each `status_rows` row's `history_count` equals the corresponding stored top-level status total and each `history_ratio` equals that row's count over `history_report_count`, quantized to `Decimal("0.0001")` with `ROUND_HALF_EVEN`; `status_rows.history_ratio` is `None` only when `history_report_count == 0`.
- Validate `config_version_summaries` are sorted by `history_config_version`, contain no duplicate versions, and counts sum to `history_report_count`.
- Builder tests must prove `duplicate_generated_at_summaries` and `duplicate_fingerprint_summaries` use full collision-group sizes. Report-tree validation must verify duplicate summaries are sorted by their key fields, contain no duplicate keys, and contain `duplicate_count` values greater than or equal to `2` and no greater than `history_report_count`.
- Validate `duplicate_generated_at_count` equals the sum of `duplicate_count` values in `duplicate_generated_at_summaries`, and `duplicate_generated_at_ratio` equals `duplicate_generated_at_count / history_report_count` quantized to `Decimal("0.0001")` with `ROUND_HALF_EVEN`.
- Validate `duplicate_fingerprint_count` equals the sum of `duplicate_count` values in `duplicate_fingerprint_summaries`, and `duplicate_fingerprint_ratio` equals `duplicate_fingerprint_count / history_report_count` quantized to `Decimal("0.0001")` with `ROUND_HALF_EVEN`.
- Validate `finding_summaries` are sorted by `(severity, source_name, finding_code)` and contain no duplicate keys.
- Builder tests must prove every `finding_summaries.history_count` reflects the number of cloned history reports containing that finding key at least once and is not a sum of nested Node 10 `comparison_count` values. Report-tree validation must verify every `finding_summaries.history_count` is positive and no greater than `history_report_count`; append-time validation cannot prove finding-count provenance without the original history reports and must not reload or replay inputs to try.
- Builder tests must prove `source_transition_summaries` equal grouped sums of existing Node 10 `source_transitions` rows from cloned history reports, without comparing history reports to derive transitions. Report-tree validation must verify `source_transition_summaries` are sorted by `(source_name, from_source_status, to_source_status)`, contain no duplicate keys, and contain positive transition counts.
- Validate `first_history_generated_at` and `last_history_generated_at` are both `None` when `history_report_count == 0`, both present when `history_report_count > 0`, and `first_history_generated_at <= last_history_generated_at`.
- Validate `status` matches gate results.
- Validate `report_only is True`.
- Validate the exact normalized boundary statement.
- Validate all ratio fields are `None` only when `history_report_count == 0`; otherwise they are finite `Decimal` values between zero and one and equal the corresponding derived count over `history_report_count`, quantized to `Decimal("0.0001")` with `ROUND_HALF_EVEN`.
- Reject floats and bools in gate values.
- `TradeProposalEvidenceComparisonHistoryBatchHealthLog.append(report)` must validate the full report tree and call `json.dumps(..., allow_nan=False, sort_keys=True)` before opening or creating the file.
- Production code must not provide JSONL readers, loaders, replay helpers, glob helpers, `from_file`, `from_log`, selectors, ranking helpers, recommendation helpers, approval helpers, outcome helpers, settlement helpers, reconciliation helpers, profitability helpers, or execution helpers.

## Task 1: Behavior Tests

**Files:**

- Create: `tests/test_proposal_evidence_comparison_history_batch_health.py`

- [ ] **Step 1: Write deterministic fixtures**

Use static, minimal, in-memory `TradeProposalEvidenceComparisonHistoryReport` fixtures. Do not import `tests.test_proposal_evidence_comparison_history`, `build_history`, Node 9 comparison fixtures, raw forecast fixtures, raw dossier fixtures, or any helper that rebuilds upstream Node 9 forecast/dossier/comparison inputs. The behavior tests should construct the Node 10 history reports directly from the Node 10 default boundary constant and public Node 10 dataclasses:

```python
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

from polymarket_alpha_lab.proposal_evidence_comparison_history import (
    DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT,
    TradeProposalEvidenceComparisonHistoryConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryFindingSummary,
    TradeProposalEvidenceComparisonHistoryGateResult,
    TradeProposalEvidenceComparisonHistoryReport,
    TradeProposalEvidenceComparisonHistorySourceTransition,
    TradeProposalEvidenceComparisonHistoryStatusRow,
)
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health import (
    TradeProposalEvidenceComparisonHistoryBatchHealthConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary,
    build_trade_proposal_evidence_comparison_history_batch_health_report,
)


def _ratio(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(count) / Decimal(total)).quantize(Decimal("0.0001"))


def _history_gate_rows(
    *,
    comparison_count: int,
    incomplete_ratio: Decimal | None,
    divergent_ratio: Decimal | None,
    unstable_ratio: Decimal | None,
) -> tuple[TradeProposalEvidenceComparisonHistoryGateResult, ...]:
    return (
        TradeProposalEvidenceComparisonHistoryGateResult(
            "comparison_sample",
            "pass" if comparison_count >= 1 else "incomplete",
            "comparison sample checked",
            comparison_count,
            1,
        ),
        TradeProposalEvidenceComparisonHistoryGateResult(
            "incomplete_comparison_rate",
            "incomplete"
            if incomplete_ratio is None
            else "fail"
            if incomplete_ratio > Decimal("0.0000")
            else "pass",
            "incomplete comparison rate checked",
            incomplete_ratio,
            Decimal("0.0000"),
        ),
        TradeProposalEvidenceComparisonHistoryGateResult(
            "divergent_comparison_rate",
            "incomplete"
            if divergent_ratio is None
            else "fail"
            if divergent_ratio > Decimal("0.0000")
            else "pass",
            "divergent comparison rate checked",
            divergent_ratio,
            Decimal("0.0000"),
        ),
        TradeProposalEvidenceComparisonHistoryGateResult(
            "unstable_comparison_rate",
            "incomplete"
            if unstable_ratio is None
            else "fail"
            if unstable_ratio > Decimal("0.0000")
            else "pass",
            "unstable comparison rate checked",
            unstable_ratio,
            Decimal("0.0000"),
        ),
    )


def history_report_fixture(
    *,
    status: str = "proposal_evidence_comparison_history_ready",
    index: int = 1,
    generated_at: datetime | None = None,
) -> TradeProposalEvidenceComparisonHistoryReport:
    generated_at = generated_at or datetime(2026, 9, 10, 12, index, tzinfo=UTC)
    counts = {
        "divergent_evidence_comparison": 0,
        "incomplete_evidence_comparison": 0,
        "proposal_evidence_comparison_complete": 1,
        "unstable_evidence_comparison": 0,
    }
    if status == "divergent_comparison_history":
        counts["divergent_evidence_comparison"] = 1
        counts["proposal_evidence_comparison_complete"] = 0
    elif status == "incomplete_comparison_history":
        counts["incomplete_evidence_comparison"] = 1
        counts["proposal_evidence_comparison_complete"] = 0
    elif status == "unstable_comparison_history":
        counts["unstable_evidence_comparison"] = 1
        counts["proposal_evidence_comparison_complete"] = 0
    elif status != "proposal_evidence_comparison_history_ready":
        raise AssertionError(f"unknown fixture status: {status}")

    comparison_count = sum(counts.values())
    incomplete_ratio = _ratio(counts["incomplete_evidence_comparison"], comparison_count)
    divergent_ratio = _ratio(counts["divergent_evidence_comparison"], comparison_count)
    unstable_ratio = _ratio(counts["unstable_evidence_comparison"], comparison_count)
    finding_summaries = ()
    if status == "divergent_comparison_history":
        finding_summaries = (
            TradeProposalEvidenceComparisonHistoryFindingSummary(
                "evidence_consistency_divergent",
                "divergent",
                "comparison",
                1,
            ),
        )
    elif status == "incomplete_comparison_history":
        finding_summaries = (
            TradeProposalEvidenceComparisonHistoryFindingSummary(
                "forecast_evidence_incomplete",
                "incomplete",
                "forecast_evidence",
                1,
            ),
        )
    elif status == "unstable_comparison_history":
        finding_summaries = (
            TradeProposalEvidenceComparisonHistoryFindingSummary(
                "dossier_batch_unstable",
                "unstable",
                "dossier_batch",
                1,
            ),
        )

    return TradeProposalEvidenceComparisonHistoryReport(
        generated_at=generated_at,
        config_version="comparison-history-v1",
        report_only=True,
        boundary_statement=DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT,
        comparison_count=comparison_count,
        complete_comparison_count=counts["proposal_evidence_comparison_complete"],
        incomplete_comparison_count=counts["incomplete_evidence_comparison"],
        divergent_comparison_count=counts["divergent_evidence_comparison"],
        unstable_comparison_count=counts["unstable_evidence_comparison"],
        incomplete_comparison_ratio=incomplete_ratio,
        divergent_comparison_ratio=divergent_ratio,
        unstable_comparison_ratio=unstable_ratio,
        first_comparison_generated_at=generated_at,
        last_comparison_generated_at=generated_at,
        status=status,
        gate_results=_history_gate_rows(
            comparison_count=comparison_count,
            incomplete_ratio=incomplete_ratio,
            divergent_ratio=divergent_ratio,
            unstable_ratio=unstable_ratio,
        ),
        status_rows=(
            TradeProposalEvidenceComparisonHistoryStatusRow(
                "divergent_evidence_comparison",
                counts["divergent_evidence_comparison"],
                _ratio(counts["divergent_evidence_comparison"], comparison_count),
            ),
            TradeProposalEvidenceComparisonHistoryStatusRow(
                "incomplete_evidence_comparison",
                counts["incomplete_evidence_comparison"],
                _ratio(counts["incomplete_evidence_comparison"], comparison_count),
            ),
            TradeProposalEvidenceComparisonHistoryStatusRow(
                "proposal_evidence_comparison_complete",
                counts["proposal_evidence_comparison_complete"],
                _ratio(
                    counts["proposal_evidence_comparison_complete"],
                    comparison_count,
                ),
            ),
            TradeProposalEvidenceComparisonHistoryStatusRow(
                "unstable_evidence_comparison",
                counts["unstable_evidence_comparison"],
                _ratio(counts["unstable_evidence_comparison"], comparison_count),
            ),
        ),
        finding_summaries=finding_summaries,
        config_version_summaries=(
            TradeProposalEvidenceComparisonHistoryConfigVersionSummary(
                "evidence-comparison-v1",
                comparison_count,
            ),
        ),
        source_transitions=(),
    )


def complete_history_fixture(index=1):
    report = history_report_fixture(
        status="proposal_evidence_comparison_history_ready",
        index=index,
    )
    return replace(
        report,
        comparison_count=2,
        complete_comparison_count=2,
        first_comparison_generated_at=report.generated_at,
        last_comparison_generated_at=report.generated_at,
        status_rows=(
            TradeProposalEvidenceComparisonHistoryStatusRow(
                "divergent_evidence_comparison",
                0,
                Decimal("0.0000"),
            ),
            TradeProposalEvidenceComparisonHistoryStatusRow(
                "incomplete_evidence_comparison",
                0,
                Decimal("0.0000"),
            ),
            TradeProposalEvidenceComparisonHistoryStatusRow(
                "proposal_evidence_comparison_complete",
                2,
                Decimal("1.0000"),
            ),
            TradeProposalEvidenceComparisonHistoryStatusRow(
                "unstable_evidence_comparison",
                0,
                Decimal("0.0000"),
            ),
        ),
        gate_results=_history_gate_rows(
            comparison_count=2,
            incomplete_ratio=Decimal("0.0000"),
            divergent_ratio=Decimal("0.0000"),
            unstable_ratio=Decimal("0.0000"),
        ),
        config_version_summaries=(
            TradeProposalEvidenceComparisonHistoryConfigVersionSummary(
                "evidence-comparison-v1",
                2,
            ),
        ),
        source_transitions=(
            TradeProposalEvidenceComparisonHistorySourceTransition(
                "dossier_batch",
                "proposal_review_dossier_batch_ready",
                "proposal_review_dossier_batch_ready",
                1,
            ),
            TradeProposalEvidenceComparisonHistorySourceTransition(
                "forecast_evidence",
                "paper_review_ready",
                "paper_review_ready",
                1,
            ),
        ),
    )


def divergent_history_fixture(index=2):
    return history_report_fixture(status="divergent_comparison_history", index=index)


def unstable_history_fixture(index=3):
    return history_report_fixture(status="unstable_comparison_history", index=index)


def incomplete_history_fixture(index=4):
    return history_report_fixture(status="incomplete_comparison_history", index=index)


def relaxed_batch_health_config():
    return TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
        config_version="history-batch-health-v1",
        max_incomplete_history_ratio=Decimal("1.0000"),
        max_divergent_history_ratio=Decimal("1.0000"),
        max_unstable_history_ratio=Decimal("1.0000"),
        max_duplicate_generated_at_ratio=Decimal("1.0000"),
        max_duplicate_fingerprint_ratio=Decimal("1.0000"),
    )
```

Use `dataclasses.replace(report, generated_at=datetime(...))` on already-built Node 10 reports; the Node 11 clone/revalidate step must accept valid replacement reports and reject invalid mutated reports.

- [ ] **Step 2: Write happy-path batch-health test**

```python
def test_build_trade_proposal_evidence_comparison_history_batch_health_report_summarizes_reports():
    complete = complete_history_fixture(index=1)
    divergent = divergent_history_fixture(index=2)
    unstable = unstable_history_fixture(index=3)

    report = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [unstable, complete, divergent],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            max_incomplete_history_ratio=Decimal("1.0000"),
            max_divergent_history_ratio=Decimal("1.0000"),
            max_unstable_history_ratio=Decimal("1.0000"),
            max_duplicate_generated_at_ratio=Decimal("1.0000"),
            max_duplicate_fingerprint_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )

    assert report.report_only is True
    assert report.status == "proposal_evidence_comparison_history_batch_health_ready"
    assert report.history_report_count == 3
    assert report.complete_history_report_count == 1
    assert report.divergent_history_report_count == 1
    assert report.unstable_history_report_count == 1
    assert report.divergent_history_ratio == Decimal("0.3333")
    assert tuple(row.gate_name for row in report.gate_results) == (
        "history_sample",
        "incomplete_history_rate",
        "divergent_history_rate",
        "unstable_history_rate",
        "duplicate_generated_at_rate",
        "duplicate_fingerprint_rate",
    )
    assert tuple(row.history_status for row in report.status_rows) == (
        "divergent_comparison_history",
        "incomplete_comparison_history",
        "proposal_evidence_comparison_history_ready",
        "unstable_comparison_history",
    )
    assert tuple(
        row.history_config_version for row in report.config_version_summaries
    ) == ("comparison-history-v1",)
    assert report.finding_summaries
    assert report.source_transition_summaries
```

- [ ] **Step 3: Run test and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health.py -q
```

Expected: FAIL because `polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health` does not exist.

- [ ] **Step 4: Add status and gate tests**

Add tests for:

- empty history input produces `incomplete_history_batch_health`
- duplicate `generated_at` values are summarized and gated when above threshold
- duplicate fingerprint collisions are summarized and gated when above threshold
- duplicate `generated_at` and duplicate fingerprint assertions prove full collision-group semantics: two colliding reports produce `duplicate_count == 2` and three colliding reports produce `duplicate_count == 3`; no test should expect "extras only" counts such as `1` for a two-item collision
- too many divergent history reports produce `divergent_history_batch_health`
- too many unstable history reports produce `unstable_history_batch_health`
- too many incomplete history reports produce `incomplete_history_batch_health`
- relaxed thresholds produce `proposal_evidence_comparison_history_batch_health_ready`
- gate payload assertions prove sample observed/threshold values use exact `int` types, rate gate observed values use exact `Decimal` values or `None` for empty samples, rate gate thresholds equal the config thresholds, and gate statuses are derived from those payloads
- ratio rows use `None` when the sample is empty and quantized ratios otherwise
- cloned reports are aggregated in normalized `(generated_at, config_version, status)` order for observable first/last timestamp bounds; tied-key caller-order stability is an internal sorting property and should not be asserted through public batch-health report fields
- source-transition summaries sum existing Node 10 `history_report.source_transitions` rows; they are not inferred by comparing adjacent history reports or any other pair of history reports

- [ ] **Step 5: Add validation and log tests**

Add tests that:

- reject non-exact history report objects
- reject strings, bytes, dicts, `Path` values, serialized JSON strings, log-shaped append-only sentinel objects that represent invalid `TradeProposalEvidenceComparisonHistoryLog`-style inputs, and non-history sentinel objects; do not import the Node 10 `TradeProposalEvidenceComparisonHistoryLog` class, and do not build raw Node 9 comparison reports, raw forecast evidence reports, or raw dossier batch reports for these tests
- reject mutated nested Node 10 history gate rows, status rows, config summaries, finding summaries, and source-transition summaries on supplied history reports, and reject mutated batch-health duplicate summaries on the built batch-health report
- reject stale or wrong-typed batch-health gate payloads, including sample observed `Decimal("3")`, sample threshold `-1`, rate observed `0`, stale rate ratios, wrong-type or out-of-range threshold decimals, and gate statuses inconsistent with observed/threshold values; original-config threshold exactness is a builder-only assertion because persisted reports do not store the originating config object
- prove finding summaries count cloned history reports containing a finding key at most once each and do not sum nested Node 10 `comparison_count` values
- prove a built batch-health report keeps copied summary values stable after the caller mutates an original supplied history report
- reject non-`datetime` `generated_at`
- reject weak or contradictory boundary statements
- validate frozen dataclasses and row invariants
- append JSONL lines through `TradeProposalEvidenceComparisonHistoryBatchHealthLog`
- prove invalid reports are rejected before creating or modifying the log path

Required concrete test bodies for the tightened semantics:

```python
def test_batch_health_gate_payloads_are_exact_and_derived():
    config = TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
        config_version="history-batch-health-v1",
        max_divergent_history_ratio=Decimal("1.0000"),
        max_duplicate_generated_at_ratio=Decimal("1.0000"),
        max_duplicate_fingerprint_ratio=Decimal("1.0000"),
    )
    report = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [complete_history_fixture(1), divergent_history_fixture(2)],
        config=config,
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )
    gates = {row.gate_name: row for row in report.gate_results}

    assert type(gates["history_sample"].observed_value) is int
    assert gates["history_sample"].observed_value == report.history_report_count
    assert type(gates["history_sample"].threshold) is int
    assert gates["history_sample"].threshold == config.min_history_report_count
    assert gates["history_sample"].status == "pass"

    for gate_name, ratio, threshold in (
        (
            "incomplete_history_rate",
            report.incomplete_history_ratio,
            config.max_incomplete_history_ratio,
        ),
        (
            "divergent_history_rate",
            report.divergent_history_ratio,
            config.max_divergent_history_ratio,
        ),
        (
            "unstable_history_rate",
            report.unstable_history_ratio,
            config.max_unstable_history_ratio,
        ),
        (
            "duplicate_generated_at_rate",
            report.duplicate_generated_at_ratio,
            config.max_duplicate_generated_at_ratio,
        ),
        (
            "duplicate_fingerprint_rate",
            report.duplicate_fingerprint_ratio,
            config.max_duplicate_fingerprint_ratio,
        ),
    ):
        assert type(gates[gate_name].observed_value) is Decimal
        assert gates[gate_name].observed_value == ratio
        assert type(gates[gate_name].threshold) is Decimal
        assert gates[gate_name].threshold == threshold
        assert gates[gate_name].status == ("pass" if ratio <= threshold else "fail")
```

```python
def test_batch_health_rejects_stale_or_wrong_typed_gate_payloads(tmp_path):
    report = duplicate_batch_health_report_fixture()

    bad_sample_type = unsafe_batch_health_report(
        report,
        gate_results=(
            replace(report.gate_results[0], observed_value=Decimal("3")),
            *report.gate_results[1:],
        ),
    )
    with pytest.raises(ValueError, match="history_sample observed_value"):
        TradeProposalEvidenceComparisonHistoryBatchHealthLog(
            tmp_path / "bad-sample-type.jsonl",
        ).append(bad_sample_type)

    bad_rate_type = unsafe_batch_health_report(
        report,
        gate_results=(
            *report.gate_results[:1],
            replace(report.gate_results[1], observed_value=0),
            *report.gate_results[2:],
        ),
    )
    with pytest.raises(ValueError, match="observed_value must be a Decimal"):
        TradeProposalEvidenceComparisonHistoryBatchHealthLog(
            tmp_path / "bad-rate-type.jsonl",
        ).append(bad_rate_type)

    stale_ratio = unsafe_batch_health_report(
        report,
        gate_results=(
            *report.gate_results[:2],
            replace(report.gate_results[2], observed_value=Decimal("0.9999")),
            *report.gate_results[3:],
        ),
    )
    with pytest.raises(ValueError, match="observed_value must match report ratio"):
        TradeProposalEvidenceComparisonHistoryBatchHealthLog(
            tmp_path / "stale-ratio.jsonl",
        ).append(stale_ratio)
```

```python
def test_batch_health_duplicate_counts_use_full_collision_groups():
    shared = complete_history_fixture(index=1)
    same_generated_at = replace(
        divergent_history_fixture(index=2),
        generated_at=shared.generated_at,
    )
    same_fingerprint_a = complete_history_fixture(index=3)
    same_fingerprint_b = complete_history_fixture(index=3)

    report = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [shared, same_generated_at, same_fingerprint_a, same_fingerprint_b],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            max_duplicate_generated_at_ratio=Decimal("1.0000"),
            max_duplicate_fingerprint_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )

    assert report.duplicate_generated_at_count == 4
    assert tuple(
        row.duplicate_count for row in report.duplicate_generated_at_summaries
    ) == (2, 2)
    assert report.duplicate_fingerprint_count == 2
    assert report.duplicate_fingerprint_summaries[0].duplicate_count == 2

    shared_timestamp = datetime(2026, 9, 12, 1, tzinfo=UTC)
    three_generated_at = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [
            replace(complete_history_fixture(index=10), generated_at=shared_timestamp),
            replace(divergent_history_fixture(index=11), generated_at=shared_timestamp),
            replace(unstable_history_fixture(index=12), generated_at=shared_timestamp),
        ],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            max_duplicate_generated_at_ratio=Decimal("1.0000"),
            max_duplicate_fingerprint_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )
    assert three_generated_at.duplicate_generated_at_count == 3
    assert three_generated_at.duplicate_generated_at_summaries == (
        TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary(
            shared_timestamp,
            3,
        ),
    )

    identical = complete_history_fixture(index=20)
    three_fingerprints = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [identical, identical, identical],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            max_duplicate_generated_at_ratio=Decimal("1.0000"),
            max_duplicate_fingerprint_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )
    assert three_fingerprints.duplicate_fingerprint_count == 3
    assert three_fingerprints.duplicate_fingerprint_summaries[0].duplicate_count == 3
```

```python
def test_batch_health_finding_counts_history_reports_not_nested_comparisons():
    source = complete_history_fixture(index=1)
    repeated_nested_finding = replace(
        source,
        finding_summaries=(
            TradeProposalEvidenceComparisonHistoryFindingSummary(
                "evidence_consistency_divergent",
                "divergent",
                "comparison",
                2,
            ),
        ),
    )

    report = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [repeated_nested_finding],
        config=relaxed_batch_health_config(),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )

    assert report.finding_summaries == (
        TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary(
            "evidence_consistency_divergent",
            "divergent",
            "comparison",
            1,
        ),
    )
```

```python
def test_batch_health_source_transitions_aggregate_existing_rows_only():
    first = complete_history_fixture(index=1)
    second = complete_history_fixture(index=2)

    report = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [second, first],
        config=relaxed_batch_health_config(),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )

    assert report.source_transition_summaries == (
        TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary(
            "dossier_batch",
            "proposal_review_dossier_batch_ready",
            "proposal_review_dossier_batch_ready",
            2,
        ),
        TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary(
            "forecast_evidence",
            "paper_review_ready",
            "paper_review_ready",
            2,
        ),
    )
```

```python
def test_batch_health_ordering_uses_normalized_generated_at_then_config_then_status():
    late = complete_history_fixture(index=3)
    early = replace(
        divergent_history_fixture(index=1),
        generated_at=datetime(2026, 9, 10, 21, tzinfo=timezone(timedelta(hours=-4))),
    )
    middle = unstable_history_fixture(index=2)

    report = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [late, middle, early],
        config=relaxed_batch_health_config(),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )

    assert report.first_history_generated_at == middle.generated_at
    assert report.last_history_generated_at == datetime(2026, 9, 11, 1, tzinfo=UTC)
    assert tuple(row.history_status for row in report.status_rows) == (
        "divergent_comparison_history",
        "incomplete_comparison_history",
        "proposal_evidence_comparison_history_ready",
        "unstable_comparison_history",
    )
```

Build `duplicate_batch_health_report_fixture()` from the static history fixtures above by passing at least two cloned history reports with the same normalized `generated_at` and at least two identical history-report fingerprints, using relaxed duplicate thresholds when the test needs a valid report. Use exact mutation/error examples for report-level invariant tests. These examples define the intended Node 11 error strings:

```python
def unsafe_batch_health_report(report, **changes):
    clone = object.__new__(type(report))
    for field_name in report.__dataclass_fields__:
        object.__setattr__(clone, field_name, getattr(report, field_name))
    for field_name, value in changes.items():
        object.__setattr__(clone, field_name, value)
    return clone


def test_batch_health_report_rejects_mutated_nested_rows(tmp_path):
    report = duplicate_batch_health_report_fixture()

    bad_gate_order = unsafe_batch_health_report(
        report,
        gate_results=report.gate_results[1:] + report.gate_results[:1],
    )
    with pytest.raises(ValueError, match="gate_results must contain batch health gates"):
        TradeProposalEvidenceComparisonHistoryBatchHealthLog(tmp_path / "bad.jsonl").append(
            bad_gate_order
        )
    assert not (tmp_path / "bad.jsonl").exists()

    with pytest.raises(ValueError, match="status_rows must match divergent history count"):
        replace(
            report,
            status_rows=(
                replace(report.status_rows[0], history_count=99),
                *report.status_rows[1:],
            ),
        )

    with pytest.raises(
        ValueError,
        match="config_version_summaries must not contain duplicates",
    ):
        replace(
            report,
            config_version_summaries=(
                report.config_version_summaries[0],
                report.config_version_summaries[0],
            ),
        )

    with pytest.raises(
        ValueError,
        match="duplicate_generated_at_summaries must not contain duplicates",
    ):
        replace(
            report,
            duplicate_generated_at_summaries=(
                report.duplicate_generated_at_summaries[0],
                report.duplicate_generated_at_summaries[0],
            ),
        )

    with pytest.raises(
        ValueError,
        match="duplicate_fingerprint_summaries must not contain duplicates",
    ):
        replace(
            report,
            duplicate_fingerprint_summaries=(
                report.duplicate_fingerprint_summaries[0],
                report.duplicate_fingerprint_summaries[0],
            ),
        )

    with pytest.raises(ValueError, match="finding_summaries must not contain duplicates"):
        replace(
            report,
            finding_summaries=(
                report.finding_summaries[0],
                report.finding_summaries[0],
            ),
        )

    with pytest.raises(
        ValueError,
        match="source_transition_summaries must not contain duplicates",
    ):
        replace(
            report,
            source_transition_summaries=(
                report.source_transition_summaries[0],
                report.source_transition_summaries[0],
            ),
        )

    with pytest.raises(
        ValueError,
        match=(
            "boundary_statement must describe report-only proposal evidence comparison "
            "history batch health"
        ),
    ):
        TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            boundary_statement="report-only batch health",
        )
```

The `unsafe_batch_health_report` helper is only for log-path tests that must pass an invalid exact-typed report to `append()`. Normal dataclass validation tests should use `dataclasses.replace(...)` so invalid rows fail at construction time.

## Task 2: Scope And Export Tests

**Files:**

- Create: `tests/test_proposal_evidence_comparison_history_batch_health_scope.py`
- Modify: `tests/test_init.py`
- Modify every sibling scope allowlist that enumerates Level 2 package-root exports
- Modify: `README.md`

- [ ] **Step 1: Write failing scope tests**

Create `tests/test_proposal_evidence_comparison_history_batch_health_scope.py` with the same AST pattern as the Node 10 scope test. Required checks:

- module `__all__` equals the eleven public names in this plan
- imports are limited to standard library plus `polymarket_alpha_lab.proposal_evidence_comparison_history`
- first-party imports are import-from symbols only, not whole-module imports
- no raw forecast/dossier/proposal/review, market/API, broker/client/request/session/websocket/order/execution/account/credential, scraping/browser automation, outcome, settlement/reconciliation, compliance/legal/geographic, JSONL-read, load, replay, glob, from-file/from-log, selector, ranking, recommendation, promotion, approval, profitability, or realized false-positive identifiers appear in imports, exported names, public API names, function/class/variable/argument names, or other executable identifiers. This identifier scan must exclude required negative boundary string literals and README/doc text that explicitly state what the node does not do.
- package root exports contain only the Node 11 batch-health public names for this node
- README batch-health section states supplied-input, report-only, no-read, no-fetch, no-outcome, no-settlement, no-ranking, no-recommendation, no-approval, no-execution boundaries
- README batch-health scope test asserts the normalized fragments inside the section from `## Level 2 Node 11 Status` to `## Automation Roadmap`

Required normalized fragments:

```python
(
    "level2node11status",
    "level2node11pythonapi",
    "reportonlyproposalevidencecomparisonhistorybatchhealthartifacts",
    "suppliedtradeproposalevidencecomparisonhistoryreport",
    "duplicategeneratedat",
    "duplicatefingerprint",
    "appendonlyjsonl",
    "notanapprovalworkflow",
    "proposalapproval",
    "approvedproposalselector",
    "latestdecisionselector",
    "decisionresolution",
    "investmentranking",
    "traderecommendation",
    "strategypromotionsignal",
    "tradeinstruction",
    "orderinstruction",
    "brokerrequest",
    "orderrequest",
    "accountaction",
    "outcomeloader",
    "realizedfalsepositiveanalysis",
    "profitabilityanalysis",
    "liveexecutionsignal",
    "doesnotfetchmarketorderbookpricehistoryoutcomeaccountcredentialidentityorsettlementdata",
    "readexternalhistoryorjsonllogs",
    "scrapewebsites",
    "authenticate",
    "credentialsprivatekeys",
    "placesubmitsignsendcreateorcancelorders",
    "openuserwebsockets",
    "heartbeat",
    "tradingsdkbrokerexecutiontransportclients",
    "brokerororderrequestpayloads",
    "reconcileexchangeaccounts",
    "reconciliation",
    "settlement",
    "importmanualexecutions",
    "approveproposals",
    "selectlatestdecisions",
    "resolveconflictingreviews",
    "rankinvestments",
    "recommendtrades",
    "compliancelegalgeographicanalysis",
)
```

- README repository-layout scope test asserts these exact paths/names are present:
  - `2026-06-15-level-2-proposal-evidence-comparison-history-batch-health.md`
  - `proposal_evidence_comparison_history_batch_health.py`
  - `test_proposal_evidence_comparison_history_batch_health.py`
  - `test_proposal_evidence_comparison_history_batch_health_scope.py`

- [ ] **Step 2: Add package-root export tests**

Extend `tests/test_init.py` with `test_level_2_node_11_public_api_exports()` using the existing identity-assertion pattern for all eleven public names.

Update every duplicated Level 2 package-root allowlist by adding `EXPECTED_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_EXPORTS` and including it in `EXPECTED_LEVEL_2_ARTIFACT_EXPORTS`:

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

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_proposal_evidence_comparison_history_batch_health_scope.py \
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
  -q
```

Expected: FAIL because module/root exports do not exist.

## Task 3: Implementation

**Files:**

- Create: `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`

- [ ] **Step 1: Implement minimal production module**

Implementation requirements:

- read `proposal_evidence_comparison_history.py`, `proposal_evidence_comparison.py`, and `proposal_review_dossier_batch.py` only as style references for local dataclass validation, exact cloning, ratio quantization, JSON-ready serialization, and append-only JSONL validation; do not import their private helpers, do not import first-party symbols outside the allowlist above, and do not copy Node 10's duplicate-`generated_at` rejection behavior because this node must summarize and gate duplicate history-report timestamps
- clone/revalidate every supplied Node 10 history report before aggregation; reject non-exact report objects before cloning
- sort cloned reports with `key=lambda report: (report.generated_at, report.config_version, report.status)` before computing first/last bounds and summaries
- compute a stable canonical fingerprint for each supplied history report from its validated JSON-ready tree
- summarize duplicate generated-at and duplicate fingerprint collisions without reading from files or replay logs
- count duplicate collision groups by full group size, not extras beyond the first item
- build gate rows ordered by `GATE_NAMES`
- build gate payloads from derived counts/ratios and config thresholds only; validate payload exactness symmetrically before JSONL append
- build status rows sorted by `history_status`
- build config-version summaries sorted by `history_config_version`
- build duplicate summaries sorted by their key fields
- build finding summaries sorted by `(severity, source_name, finding_code)`
- build finding summaries by counting cloned history reports containing each `(severity, source_name, finding_code)` at least once, not by summing nested Node 10 comparison counts
- build source-transition summaries by grouping each cloned report's existing `source_transitions` rows and summing their existing `transition_count` values, sorted by `(source_name, from_source_status, to_source_status)`
- validate all self-contained row/report invariants in `__post_init__`; provenance invariants that require original history-report inputs must be proven in builder tests and encoded by builder construction, not rederived during append-time validation
- implement a local `_json_ready` helper in this module; use `_json_ready(asdict(report))` with `allow_nan=False` and `sort_keys=True`; do not import private `_json_ready` or validation helpers from Node 10
- write JSONL only after full validation
- do not import raw forecast reports, dossier batch reports, raw observations, proposal packets, review records, market data, browser tooling, HTTP clients, account modules, order modules, outcome modules, settlement modules, reconciliation modules, profitability modules, or credential modules

- [ ] **Step 2: Add root exports**

Add the eleven Node 11 batch-health public names to `src/polymarket_alpha_lab/__init__.py` import blocks and `__all__`.

- [ ] **Step 3: Run focused tests and verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health.py tests/test_proposal_evidence_comparison_history_batch_health_scope.py tests/test_init.py -q
```

Expected: PASS.

## Task 4: README And Plan Layout

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Add Level 2 Node 11 documentation**

Insert sections before `## Automation Roadmap`:

```markdown
## Level 2 Node 11 Status

Level 2 Node 11 adds report-only proposal evidence comparison history batch health artifacts over supplied `TradeProposalEvidenceComparisonHistoryReport` values. It summarizes history status frequencies, duplicate generated-at indicators, duplicate fingerprint indicators, config-version coverage, finding-code frequencies, source-transition coverage, and append-only JSONL persistence for audit only; it is not an approval workflow, proposal approval step, approved-proposal selector, latest-decision selector, decision-resolution process, investment ranking, trade recommendation, strategy-promotion signal, trade instruction, order instruction, broker request, order request, account action, outcome loader, realized false-positive analysis, profitability analysis, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, identity, or settlement data; read external history or JSONL logs; scrape websites; authenticate; handle credentials/private keys; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use trading SDK/broker/execution/transport clients; build broker or order request payloads; reconcile exchange accounts; perform reconciliation; review settlement; import manual executions; approve proposals; select latest decisions; resolve conflicting reviews; rank investments; recommend trades; or perform compliance/legal/geographic analysis.

## Level 2 Node 11 Python API

Node 11 is exposed through Python APIs:

- Configure batch-health reports with `TradeProposalEvidenceComparisonHistoryBatchHealthConfig(config_version="history-batch-health-v1")`.
- Build batch-health reports with `build_trade_proposal_evidence_comparison_history_batch_health_report(history_reports, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalEvidenceComparisonHistoryBatchHealthReport`.
- Inspect batch-health gates with `TradeProposalEvidenceComparisonHistoryBatchHealthGateResult`, status rows with `TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow`, config-version summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary`, duplicate-generated-at summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary`, duplicate-fingerprint summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary`, finding summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary`, and source-transition summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary`.
- Persist batch-health snapshots with `TradeProposalEvidenceComparisonHistoryBatchHealthLog(path).append(report)`.
```

Update repository layout entries for the new plan, source module, behavior test, and scope test.

- [ ] **Step 2: Run README-sensitive tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_scope.py -q
```

Expected: PASS after implementation.

## Task 5: Verification, Claude Review, Handoff, Commit, Push

**Files:**

- Modify this plan file with checkbox progress and handoff evidence during execution.

- [x] **Step 1: Run verification**

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
- Git status: only intended Node 11 files modified/untracked.

- [x] **Step 2: Claude Code implementation review**

Run local Claude Code with model `claude-opus-4-8` and effort `max`. The implementation review prompt must treat any raw upstream report dependency beyond Node 10 history reports, raw observation/proposal/review dependency, data fetch, external-history load, JSONL read, scraping/browser automation, auth/credential/wallet/broker/execution/request/session/websocket/order surface, approval workflow, approved-proposal selection, decision resolution, ranking, recommendation, promotion, outcome loading, realized false-positive analysis, profitability analysis, settlement, reconciliation, manual execution import, or compliance/legal/geographic analysis as Critical.

Review-note terminology must stay explicit:

- "Claude Code implementation review" means the local Claude review run, with model, effort, prompt, Critical/Important/Minor counts, and verdict recorded.
- "CodeGraph" means indexed context and dependency checks from `codegraph explore`, `codegraph node`, `codegraph sync`, and `codegraph status .`. CodeGraph output is not a Claude finding unless the Claude prompt includes that output and Claude independently reports it.
- If Claude and CodeGraph notes disagree, record both notes separately, fix Critical/Important Claude findings, and use CodeGraph to verify symbol context and index freshness.

Accepted terminal state: `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed` or `Verdict: Proceed with fixes`. Fix every Critical and Important finding before commit.

- [x] **Step 3: Append Handoff Summary**

Append actual evidence:

```markdown
## Handoff Summary

- Node completed: Level 2 Node 11 proposal evidence comparison history batch health.
- Commit: pending at handoff-write time; final assistant response must report commit hash after commit.
- Pushed: pending at handoff-write time; final assistant response must report push result after push.
- Repo status before commit: <git status output>
- Verification commands:
  - `.venv/bin/python -m pytest -q`: <pass/fail summary>
  - `git diff --check`: <pass/fail summary>
  - `codegraph sync`: <pass/fail summary>
  - `codegraph status .`: <up-to-date/stale summary>
  - Claude Code implementation review: <Critical/Important/Minor counts and verdict>
- Files changed:
  - `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health.py`
  - `src/polymarket_alpha_lab/__init__.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_scope.py`
  - `tests/test_init.py`
  - scope allowlist tests
  - `README.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health.md`
- Uncommitted files after push: pending at handoff-write time; final assistant response must report post-push status.
- Next safe step: human analysts can compare batch-health reports using the history batch-health artifact, but any automated routing, ranking, recommendation, settlement/outcome analysis, or execution planning requires a new Claude-reviewed plan.
```

- [ ] **Step 4: Commit and push**

Stage every intended Node 11 file, commit with:

```bash
git commit -m "feat: add proposal evidence comparison history batch health"
git push origin main
```

Expected: push succeeds and final status is clean against `origin/main`.

## Self-Review

- Spec coverage: The plan creates a supplied-input, report-only batch-health layer over Node 10 history reports and does not add fetching, scraping, JSONL reads, raw upstream report ingestion, outcome loading, realized false-positive analysis, profitability analysis, proposal approval, decision resolution, investment ranking, trade recommendations, credential handling, order placement, settlement/reconciliation work, manual execution import, or compliance/legal/geographic analysis.
- Placeholder scan: The plan contains no TBD/TODO placeholders. Public API, statuses, gate rules, counting rules, validation rules, scope tests, README requirements, verification commands, Claude review policy, and handoff fields are specified.
- Type consistency: The same names are used throughout: `TradeProposalEvidenceComparisonHistoryBatchHealthConfig`, `TradeProposalEvidenceComparisonHistoryBatchHealthGateResult`, `TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow`, `TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary`, `TradeProposalEvidenceComparisonHistoryBatchHealthReport`, `TradeProposalEvidenceComparisonHistoryBatchHealthLog`, and `build_trade_proposal_evidence_comparison_history_batch_health_report`.

## Handoff Summary

- Node completed: Level 2 Node 11 proposal evidence comparison history batch health.
- Commit: pending at handoff-write time; final assistant response must report commit hash after commit.
- Pushed: pending at handoff-write time; final assistant response must report push result after push.
- Repo status before commit:

```text
## main...origin/main
 M README.md
 M src/polymarket_alpha_lab/__init__.py
 M tests/test_analytics_history_scope.py
 M tests/test_analytics_scope.py
 M tests/test_forecast_evidence_scope.py
 M tests/test_init.py
 M tests/test_manual_review_queue_scope.py
 M tests/test_proposal_evidence_comparison_history_scope.py
 M tests/test_proposal_evidence_comparison_scope.py
 M tests/test_proposal_packet_scope.py
 M tests/test_proposal_review_coverage_scope.py
 M tests/test_proposal_review_diagnostics_scope.py
 M tests/test_proposal_review_dossier_batch_scope.py
 M tests/test_proposal_review_dossier_scope.py
 M tests/test_proposal_review_quality_scope.py
 M tests/test_proposal_review_scope.py
 M tests/test_proposal_review_summary_scope.py
?? docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend.md
?? src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health.py
?? tests/test_proposal_evidence_comparison_history_batch_health.py
?? tests/test_proposal_evidence_comparison_history_batch_health_scope.py
```

- Verification commands:
  - `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health.py -q`: `15 passed`
  - `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health_scope.py tests/test_init.py ... -q`: `136 passed`
  - `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history_batch_health.py tests/test_proposal_evidence_comparison_history_batch_health_scope.py tests/test_init.py -q`: `46 passed`
  - `.venv/bin/python -m pytest tests/test_proposal_evidence_comparison_history.py tests/test_proposal_evidence_comparison_history_scope.py tests/test_proposal_evidence_comparison_history_batch_health.py tests/test_proposal_evidence_comparison_history_batch_health_scope.py -q`: `50 passed`
  - `.venv/bin/python -m pytest -q`: `680 passed`
  - `git diff --check`: exit 0
  - `codegraph sync`: synced 19 changed files; 3 added and 16 modified source/test files indexed
  - `codegraph status .`: index up to date; 73 files, 2,658 nodes, 8,575 edges
  - Secret scan over current diff: no `ghp_`, GitHub PAT, private-key, API-key, password, or token strings found
  - Claude Code implementation review (`claude-opus-4-8`, effort `max`): Critical findings 0, Important findings 0, Minor findings 0, Verdict: Proceed
  - Claude Code next-node plan review (`claude-opus-4-8`, effort `max`): first review Critical 0, Important 4, Minor 1; fixed plan; second review Critical 0, Important 0, Minor 0, Verdict: Proceed
- Files changed:
  - `src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health.py`
  - `src/polymarket_alpha_lab/__init__.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health.py`
  - `tests/test_proposal_evidence_comparison_history_batch_health_scope.py`
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
  - `tests/test_proposal_review_coverage_scope.py`
  - `tests/test_proposal_review_dossier_scope.py`
  - `tests/test_proposal_review_dossier_batch_scope.py`
  - `tests/test_proposal_evidence_comparison_scope.py`
  - `tests/test_proposal_evidence_comparison_history_scope.py`
  - `README.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend.md`
- Uncommitted files after push: pending at handoff-write time; final assistant response must report post-push status.
- Next safe step: execute the Claude-reviewed Node 12 batch-health trend plan. Human analysts can compare batch-health reports using the history batch-health artifact, but any automated routing, ranking, recommendation, settlement/outcome analysis, or execution planning requires a new Claude-reviewed plan.
