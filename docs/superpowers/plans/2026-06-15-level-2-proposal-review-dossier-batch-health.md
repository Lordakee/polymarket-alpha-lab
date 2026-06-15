# Level 2 Proposal-Review Dossier Batch Health Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a report-only batch health artifact that summarizes supplied `TradeProposalReviewDossierReport` values across a review window.

**Architecture:** Create a focused `proposal_review_dossier_batch.py` module that accepts only caller-supplied dossier report objects, clones/revalidates them, computes deterministic aggregate health rows, and optionally appends a JSONL snapshot after full validation. The artifact is batch observability only: it never fetches data, reads JSONL history, scrapes websites, ranks investments, recommends trades, approves proposals, resolves decisions, handles credentials, or touches execution surfaces.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, UTC `datetime`, JSONL append-only persistence, pytest, CodeGraph, and local opencode review with model `zhipuai-coding-plan/glm-5.2` using variant `max`.

---

## Scope Boundaries

This node consumes only an in-memory iterable of `TradeProposalReviewDossierReport` values from `polymarket_alpha_lab.proposal_review_dossier`.

This node must not import raw proposal packets, raw proposal-review records, market/API clients, broker/client/request/session/websocket/order/execution/account/credential modules, scraping/browser automation modules, settlement/reconciliation modules, compliance/legal/geographic modules, or any existing JSONL log classes except its own append-only writer.

This node must not read JSONL files, load external history, fetch market/order-book/price data, rank investments, recommend trades, select approved proposals, select latest decisions, resolve conflicting reviews, create background workers, or produce execution readiness signals.

## Public API

Create `src/polymarket_alpha_lab/proposal_review_dossier_batch.py` with:

```python
__all__ = (
    "TradeProposalReviewDossierBatchConfig",
    "TradeProposalReviewDossierBatchGateResult",
    "TradeProposalReviewDossierBatchConfigVersionSummary",
    "TradeProposalReviewDossierBatchDuplicateSummary",
    "TradeProposalReviewDossierBatchFindingSummary",
    "TradeProposalReviewDossierBatchSourceSummary",
    "TradeProposalReviewDossierBatchReport",
    "TradeProposalReviewDossierBatchLog",
    "build_trade_proposal_review_dossier_batch_report",
)
```

Define `DEFAULT_REVIEW_DOSSIER_BATCH_BOUNDARY_STATEMENT` exactly as:

```python
DEFAULT_REVIEW_DOSSIER_BATCH_BOUNDARY_STATEMENT = (
    "This is a report-only proposal-review dossier batch artifact over supplied "
    "dossier reports, not an approval workflow, proposal approval, "
    "approved-proposal selector, latest-decision selector, decision-resolution "
    "process, investment ranking, trade recommendation, trade instruction, "
    "order instruction, broker request, order request, account action, account "
    "authentication, private-key handling, wallet signature, live-execution "
    "signal, credential workflow, external-history loader, JSONL reader, "
    "scraping workflow, strategy-promotion signal, settlement review, "
    "reconciliation process, compliance review, geographic access analysis, or "
    "automatic order-placement authorization."
)
```

`_require_boundary_statement` must normalize by lowercasing and keeping only alphanumeric characters, then require the value to equal the normalized `DEFAULT_REVIEW_DOSSIER_BATCH_BOUNDARY_STATEMENT`. This preserves punctuation/spacing flexibility while rejecting weakened or contradictory custom boundary text.

Public dataclasses:

```python
@dataclass(frozen=True)
class TradeProposalReviewDossierBatchConfig:
    config_version: str
    min_dossier_count: int = 1
    max_incomplete_dossier_ratio: Decimal = Decimal("0.0000")
    max_inconsistent_dossier_ratio: Decimal = Decimal("0.0000")
    max_unstable_dossier_ratio: Decimal = Decimal("0.0000")
    boundary_statement: str = DEFAULT_REVIEW_DOSSIER_BATCH_BOUNDARY_STATEMENT
```

```python
@dataclass(frozen=True)
class TradeProposalReviewDossierBatchGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None
```

```python
@dataclass(frozen=True)
class TradeProposalReviewDossierBatchConfigVersionSummary:
    dossier_config_version: str
    dossier_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalReviewDossierBatchDuplicateSummary:
    dossier_fingerprint: str
    dossier_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalReviewDossierBatchFindingSummary:
    finding_code: str
    severity: str
    source_report_name: str
    dossier_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalReviewDossierBatchSourceSummary:
    source_report_name: str
    complete_count: int
    incomplete_count: int
    inconsistent_count: int
    unstable_count: int
```

```python
@dataclass(frozen=True)
class TradeProposalReviewDossierBatchReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    dossier_count: int
    complete_dossier_count: int
    incomplete_dossier_count: int
    inconsistent_dossier_count: int
    unstable_dossier_count: int
    incomplete_dossier_ratio: Decimal | None
    inconsistent_dossier_ratio: Decimal | None
    unstable_dossier_ratio: Decimal | None
    first_dossier_generated_at: datetime | None
    last_dossier_generated_at: datetime | None
    status: str
    gate_results: tuple[TradeProposalReviewDossierBatchGateResult, ...]
    config_version_summaries: tuple[TradeProposalReviewDossierBatchConfigVersionSummary, ...]
    duplicate_summaries: tuple[TradeProposalReviewDossierBatchDuplicateSummary, ...]
    finding_summaries: tuple[TradeProposalReviewDossierBatchFindingSummary, ...]
    source_summaries: tuple[TradeProposalReviewDossierBatchSourceSummary, ...]
```

```python
@dataclass(frozen=True)
class TradeProposalReviewDossierBatchLog:
    path: Path | str

    def append(self, report: TradeProposalReviewDossierBatchReport) -> None:
        ...
```

Builder signature:

```python
def build_trade_proposal_review_dossier_batch_report(
    dossiers: Iterable[TradeProposalReviewDossierReport],
    *,
    config: TradeProposalReviewDossierBatchConfig,
    generated_at: datetime,
) -> TradeProposalReviewDossierBatchReport:
    ...
```

## Status And Gate Rules

Gate names:

```python
GATE_NAMES = (
    "dossier_sample",
    "incomplete_dossier_rate",
    "inconsistent_dossier_rate",
    "unstable_dossier_rate",
)
```

Gate statuses are `pass` or `fail`.

Report statuses:

```python
REPORT_STATUSES = (
    "incomplete_dossier_batch",
    "inconsistent_dossier_batch",
    "unstable_dossier_batch",
    "proposal_review_dossier_batch_ready",
)
```

Status mapping:

- If `dossier_sample` fails, report status is `incomplete_dossier_batch`.
- Else if `inconsistent_dossier_rate` fails, report status is `inconsistent_dossier_batch`.
- Else if `incomplete_dossier_rate` fails, report status is `incomplete_dossier_batch`.
- Else if `unstable_dossier_rate` fails, report status is `unstable_dossier_batch`.
- Else report status is `proposal_review_dossier_batch_ready`.

Gate semantics:

- `dossier_sample`: pass when `dossier_count >= config.min_dossier_count`; observed value is `dossier_count`; threshold is `config.min_dossier_count`; pass message is `Dossier sample size meets the configured minimum.`; fail message is `Dossier sample size is below the configured minimum.`
- `incomplete_dossier_rate`: pass when `incomplete_dossier_ratio is not None` and `incomplete_dossier_ratio <= config.max_incomplete_dossier_ratio`; observed value is the quantized `incomplete_dossier_ratio` `Decimal` on pass and on non-zero fail; for zero dossiers, fail with observed value `None`; threshold is `config.max_incomplete_dossier_ratio`; pass message is `Incomplete dossier rate is within threshold.`; fail message is `Incomplete dossier rate exceeds threshold or is unavailable.`
- `inconsistent_dossier_rate`: pass when `inconsistent_dossier_ratio is not None` and `inconsistent_dossier_ratio <= config.max_inconsistent_dossier_ratio`; observed value is the quantized `inconsistent_dossier_ratio` `Decimal` on pass and on non-zero fail; for zero dossiers, fail with observed value `None`; threshold is `config.max_inconsistent_dossier_ratio`; pass message is `Inconsistent dossier rate is within threshold.`; fail message is `Inconsistent dossier rate exceeds threshold or is unavailable.`
- `unstable_dossier_rate`: pass when `unstable_dossier_ratio is not None` and `unstable_dossier_ratio <= config.max_unstable_dossier_ratio`; observed value is the quantized `unstable_dossier_ratio` `Decimal` on pass and on non-zero fail; for zero dossiers, fail with observed value `None`; threshold is `config.max_unstable_dossier_ratio`; pass message is `Unstable dossier rate is within threshold.`; fail message is `Unstable dossier rate exceeds threshold or is unavailable.`

Counting:

- `complete_dossier_count`: count of dossier reports with `status == "proposal_review_dossier_complete"`.
- `incomplete_dossier_count`: count of dossier reports with `status == "incomplete_review_dossier"`.
- `inconsistent_dossier_count`: count of dossier reports with `status == "inconsistent_review_dossier"`.
- `unstable_dossier_count`: count of dossier reports with `status == "unstable_review_dossier"`.
- `*_dossier_ratio`: quantized to four decimal places with `ROUND_HALF_EVEN`, or `None` when `dossier_count == 0`.
- `first_dossier_generated_at` and `last_dossier_generated_at`: UTC-normalized bounds over dossier `generated_at`, or `None` when no dossiers are supplied.

Config-version summaries:

- Group supplied dossiers by `config_version`.
- Emit one `TradeProposalReviewDossierBatchConfigVersionSummary` per config version.
- Sort rows by `dossier_config_version`.

Duplicate summaries:

- Build a deterministic non-ranking `dossier_fingerprint` from each supplied dossier's public dataclass values after UTC/Decimal normalization.
- Fingerprint algorithm: `dossier_fingerprint = json.dumps(_json_ready(asdict(dossier)), allow_nan=False, sort_keys=True)`, where `_json_ready` encodes `Decimal` values as strings, UTC-normalized datetimes as ISO strings, recursively handles dict/list/tuple values, and rejects floats or non-string JSON object keys.
- Emit one `TradeProposalReviewDossierBatchDuplicateSummary` only for fingerprints seen more than once.
- Sort rows by `dossier_fingerprint`.
- Duplicates are informational batch-health evidence, not a constructor failure and not a claim that the underlying raw proposal/review identities are duplicated.

Finding summaries:

- Group every supplied dossier finding row by `(severity, source_report_name, finding_code)`.
- Emit one `TradeProposalReviewDossierBatchFindingSummary` per group.
- Sort rows by `(severity, source_report_name, finding_code)`.
- `dossier_count` counts distinct supplied dossier reports containing at least one matching finding row.

Source summaries:

- For each `source_report_name` in `("coverage", "diagnostics", "quality", "summary")`, count supplied dossier source rows by `status_category`.
- Emit exactly four rows sorted by `source_report_name`.

Validation requirements:

- Reject strings/bytes as dossier iterables.
- Reject non-`TradeProposalReviewDossierReport` items.
- Clone/revalidate each supplied dossier by reconstructing a `TradeProposalReviewDossierReport` from its public dataclass tree, including gate rows, source rows, and finding rows.
- Do not reject duplicate object references or duplicate report contents. This batch layer has no raw identity model, so duplicates must be surfaced only through `duplicate_summaries`.
- Do not raise for batches with inconsistent or unstable dossiers; represent those through counts, ratios, gates, and status.
- Validate `finding_summaries` and `source_summaries` match the supplied aggregate counts.
- Validate `config_version_summaries` and `duplicate_summaries` match the supplied dossier set.
- For each `source_summary`, `complete_count + incomplete_count + inconsistent_count + unstable_count == dossier_count`.
- `source_summaries` must contain exactly `("coverage", "diagnostics", "quality", "summary")` sorted by `source_report_name`.
- `finding_summaries` must be sorted by `(severity, source_report_name, finding_code)` and must contain no duplicate `(severity, source_report_name, finding_code)` keys.
- Validate `gate_results` order equals `GATE_NAMES`.
- Validate `status` matches gate results.
- Validate `report_only is True`.
- Validate `boundary_statement` with the required normalized batch boundary fragments.
- Validate all ratios are finite `Decimal` values between zero and one.
- Reject floats and bools in gate values.
- JSON serialization must encode `Decimal` values as strings and datetimes as UTC ISO strings.
- `TradeProposalReviewDossierBatchLog.append(report)` must validate the full report tree and call `json.dumps(..., allow_nan=False, sort_keys=True)` before opening or creating the file. Production code must not provide any JSONL reader, loader, replay helper, glob helper, or `from_file`/`from_log` constructor.

## Task 1: Batch Report Behavior Tests

**Files:**

- Create: `tests/test_proposal_review_dossier_batch.py`

- [ ] **Step 0: Add deterministic dossier fixtures**

Import existing helpers from `tests/test_proposal_review_dossier.py` and `tests/test_proposal_review_coverage.py` rather than duplicating raw setup logic:

```python
from dataclasses import FrozenInstanceError, asdict, replace
from tests.test_proposal_review_coverage import approved_record, packet, rejected_record
from tests.test_proposal_review_dossier import dossier_inputs, dossier_report
```

Define helpers with a required `index: int = 1` argument. Each helper must pass a unique `generated_at=datetime(2026, 9, 9, index % 24, index % 60, tzinfo=UTC)` override into `dossier_report` so duplicate tests can distinguish unique reports from repeated object references.

- Restrict helper `index` values to `1 <= index <= 9` so existing `packet(index)` helpers never receive an invalid datetime minute.
- `complete_dossier_fixture(index=1)`: one approved record for `packet(index)`, with the normal `dossier_inputs` and `dossier_report`.
- `incomplete_dossier_fixture(index=1)`: `dossier_inputs([], [])`, producing `status == "incomplete_review_dossier"`.
- `inconsistent_dossier_fixture(index=1)`: build summary/quality/diagnostics from one approved record for `packet(20 + index)`, but build coverage from one rejected record for `packet(30 + index)`, producing `count_consistency=fail` and `status == "inconsistent_review_dossier"`.
- `unstable_dossier_fixture(index=1)`: build one rejected record for `packet(40 + index)` with `TradeProposalReviewSummaryConfig(max_rejection_ratio=Decimal("0.0000"))`, quality/diagnostics/coverage thresholds that stay ready, and `dossier_report`, producing `status == "unstable_review_dossier"` through `summary_evidence=fail`.
- `expected_dossier_fingerprint(dossier)`: local test helper mirroring production fingerprint rules by calling `asdict(dossier)`, recursively converting `Decimal` to strings and UTC datetimes to ISO strings, rejecting floats, and returning `json.dumps(..., allow_nan=False, sort_keys=True)`.

- [ ] **Step 1: Write failing tests for happy-path aggregation**

Use the Step 0 helpers to build complete, incomplete, inconsistent, and unstable dossier reports.

Test expectations:

```python
def test_build_trade_proposal_review_dossier_batch_report_summarizes_supplied_dossiers():
    complete = complete_dossier_fixture(index=1)
    incomplete = incomplete_dossier_fixture()
    inconsistent = inconsistent_dossier_fixture(index=2)
    unstable = unstable_dossier_fixture(index=3)

    report = build_trade_proposal_review_dossier_batch_report(
        [unstable, incomplete, complete, inconsistent],
        config=TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            max_incomplete_dossier_ratio=Decimal("1.0000"),
            max_inconsistent_dossier_ratio=Decimal("1.0000"),
            max_unstable_dossier_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 9, 12, tzinfo=UTC),
    )

    assert report.report_only is True
    assert report.dossier_count == 4
    assert report.complete_dossier_count == 1
    assert report.incomplete_dossier_count == 1
    assert report.inconsistent_dossier_count == 1
    assert report.unstable_dossier_count == 1
    assert report.incomplete_dossier_ratio == Decimal("0.2500")
    assert report.inconsistent_dossier_ratio == Decimal("0.2500")
    assert report.unstable_dossier_ratio == Decimal("0.2500")
    assert report.config_version == "dossier-batch-v1"
    assert report.status == "proposal_review_dossier_batch_ready"
    assert tuple(row.gate_name for row in report.gate_results) == GATE_NAMES
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.source_report_name for row in report.source_summaries) == (
        "coverage",
        "diagnostics",
        "quality",
        "summary",
    )
    assert tuple(row.dossier_config_version for row in report.config_version_summaries) == (
        "dossier-v1",
    )
    assert report.duplicate_summaries == ()
    assert (
        report.complete_dossier_count
        + report.incomplete_dossier_count
        + report.inconsistent_dossier_count
        + report.unstable_dossier_count
    ) == report.dossier_count
    assert report.first_dossier_generated_at == min(
        row.generated_at for row in (complete, incomplete, inconsistent, unstable)
    )
    assert report.last_dossier_generated_at == max(
        row.generated_at for row in (complete, incomplete, inconsistent, unstable)
    )
    assert report.finding_summaries == (
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="coverage_evidence_incomplete",
            severity="incomplete",
            source_report_name="coverage",
            dossier_count=1,
        ),
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="diagnostic_evidence_incomplete",
            severity="incomplete",
            source_report_name="diagnostics",
            dossier_count=1,
        ),
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="quality_evidence_incomplete",
            severity="incomplete",
            source_report_name="quality",
            dossier_count=1,
        ),
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="summary_evidence_incomplete",
            severity="incomplete",
            source_report_name="summary",
            dossier_count=1,
        ),
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="count_consistency_failed",
            severity="inconsistent",
            source_report_name="dossier",
            dossier_count=1,
        ),
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="summary_evidence_unstable",
            severity="unstable",
            source_report_name="summary",
            dossier_count=1,
        ),
    )
    assert report.source_summaries == (
        TradeProposalReviewDossierBatchSourceSummary("coverage", 3, 1, 0, 0),
        TradeProposalReviewDossierBatchSourceSummary("diagnostics", 3, 1, 0, 0),
        TradeProposalReviewDossierBatchSourceSummary("quality", 3, 1, 0, 0),
        TradeProposalReviewDossierBatchSourceSummary("summary", 2, 1, 0, 1),
    )
```

- [ ] **Step 2: Run test and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_dossier_batch.py -q
```

Expected: FAIL because `polymarket_alpha_lab.proposal_review_dossier_batch` does not exist.

- [ ] **Step 3: Write failing tests for status gates**

Add cases:

```python
def test_trade_proposal_review_dossier_batch_statuses_cover_sample_and_rate_failures():
    complete = complete_dossier_fixture(index=4)
    incomplete = incomplete_dossier_fixture()
    inconsistent = inconsistent_dossier_fixture(index=5)
    unstable = unstable_dossier_fixture(index=6)

    empty = build_trade_proposal_review_dossier_batch_report(
        [],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 13, tzinfo=UTC),
    )
    assert empty.status == "incomplete_dossier_batch"
    assert next(row for row in empty.gate_results if row.gate_name == "dossier_sample").status == "fail"
    assert all(
        row.observed_value is None
        for row in empty.gate_results
        if row.gate_name.endswith("_rate")
    )
    assert empty.source_summaries == (
        TradeProposalReviewDossierBatchSourceSummary("coverage", 0, 0, 0, 0),
        TradeProposalReviewDossierBatchSourceSummary("diagnostics", 0, 0, 0, 0),
        TradeProposalReviewDossierBatchSourceSummary("quality", 0, 0, 0, 0),
        TradeProposalReviewDossierBatchSourceSummary("summary", 0, 0, 0, 0),
    )

    inconsistent_batch = build_trade_proposal_review_dossier_batch_report(
        [complete, inconsistent],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 14, tzinfo=UTC),
    )
    assert inconsistent_batch.status == "inconsistent_dossier_batch"

    incomplete_batch = build_trade_proposal_review_dossier_batch_report(
        [complete, incomplete],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 15, tzinfo=UTC),
    )
    assert incomplete_batch.status == "incomplete_dossier_batch"
    incomplete_rate = next(
        row
        for row in incomplete_batch.gate_results
        if row.gate_name == "incomplete_dossier_rate"
    )
    assert incomplete_rate.status == "fail"
    assert incomplete_rate.message == "Incomplete dossier rate exceeds threshold or is unavailable."
    assert incomplete_rate.observed_value == Decimal("0.5000")
    assert incomplete_rate.threshold == Decimal("0.0000")

    unstable_batch = build_trade_proposal_review_dossier_batch_report(
        [complete, unstable],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 16, tzinfo=UTC),
    )
    assert unstable_batch.status == "unstable_dossier_batch"

    multi_failure = build_trade_proposal_review_dossier_batch_report(
        [complete, inconsistent, incomplete, unstable],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 17, tzinfo=UTC),
    )
    assert multi_failure.status == "inconsistent_dossier_batch"
```

- [ ] **Step 4: Run test and verify RED**

Run the same pytest command. Expected: FAIL for missing module.

- [ ] **Step 5: Write failing tests for bad inputs, mutation revalidation, and JSONL append**

Add cases:

```python
def test_trade_proposal_review_dossier_batch_rejects_bad_inputs_and_mutated_dossiers():
    complete = complete_dossier_fixture(index=7)

    with pytest.raises(ValueError, match="dossiers"):
        build_trade_proposal_review_dossier_batch_report(
            "not dossiers",
            config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
            generated_at=datetime(2026, 9, 9, 17, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="TradeProposalReviewDossierReport"):
        build_trade_proposal_review_dossier_batch_report(
            [object()],
            config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
            generated_at=datetime(2026, 9, 9, 18, tzinfo=UTC),
        )

    object.__setattr__(complete, "review_coverage_ratio", Decimal("NaN"))
    with pytest.raises(ValueError, match="finite|review_coverage_ratio"):
        build_trade_proposal_review_dossier_batch_report(
            [complete],
            config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
            generated_at=datetime(2026, 9, 9, 19, tzinfo=UTC),
        )
```

```python
def test_trade_proposal_review_dossier_batch_log_appends_jsonl_report(tmp_path):
    report = build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=8)],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 20, tzinfo=UTC),
    )
    log = TradeProposalReviewDossierBatchLog(path=tmp_path / "dossier-batch.jsonl")

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    stored = json.loads(lines[0])
    assert stored["report_only"] is True
    assert stored["dossier_count"] == 1
    assert stored["complete_dossier_count"] == 1
    assert stored["config_version"] == "dossier-batch-v1"
    assert stored["config_version_summaries"][0]["dossier_config_version"] == "dossier-v1"
```

```python
def test_trade_proposal_review_dossier_batch_log_validates_before_open(tmp_path):
    report = build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=8)],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 22, tzinfo=UTC),
    )
    object.__setattr__(report, "incomplete_dossier_ratio", Decimal("NaN"))
    log = TradeProposalReviewDossierBatchLog(path=tmp_path / "dossier-batch.jsonl")

    with pytest.raises(ValueError, match="finite|incomplete_dossier_ratio"):
        log.append(report)

    assert not log.path.exists()
```

```python
def test_trade_proposal_review_dossier_batch_reports_duplicate_dossier_fingerprints():
    complete = complete_dossier_fixture(index=9)
    duplicate_content = replace(complete)
    assert duplicate_content is not complete

    report = build_trade_proposal_review_dossier_batch_report(
        [complete, duplicate_content],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 21, tzinfo=UTC),
    )

    assert report.dossier_count == 2
    assert len(report.duplicate_summaries) == 1
    assert report.duplicate_summaries[0].dossier_fingerprint == expected_dossier_fingerprint(complete)
    assert report.duplicate_summaries[0].dossier_count == 2
```

- [ ] **Step 6: Write failing tests for config validation and frozen dataclass invariants**

Add cases:

```python
def test_trade_proposal_review_dossier_batch_config_validates_thresholds():
    with pytest.raises(ValueError, match="config_version"):
        TradeProposalReviewDossierBatchConfig(config_version="")
    with pytest.raises(ValueError, match="min_dossier_count"):
        TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            min_dossier_count=-1,
        )
    with pytest.raises(ValueError, match="max_incomplete_dossier_ratio"):
        TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            max_incomplete_dossier_ratio=Decimal("1.5000"),
        )
    with pytest.raises(ValueError, match="max_inconsistent_dossier_ratio"):
        TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            max_inconsistent_dossier_ratio=0.5,
        )
    with pytest.raises(ValueError, match="boundary_statement"):
        TradeProposalReviewDossierBatchConfig(
            config_version="dossier-batch-v1",
            boundary_statement="dossier batch",
        )
```

```python
def test_trade_proposal_review_dossier_batch_dataclasses_are_frozen_and_validate_invariants():
    report = build_trade_proposal_review_dossier_batch_report(
        [complete_dossier_fixture(index=9)],
        config=TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1"),
        generated_at=datetime(2026, 9, 9, 22, tzinfo=UTC),
    )
    config = TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1")

    with pytest.raises(FrozenInstanceError):
        report.status = "other"
    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(ValueError, match="status"):
        replace(report, status="incomplete_dossier_batch")
    with pytest.raises(ValueError, match="gate_results"):
        replace(report, gate_results=tuple(reversed(report.gate_results)))
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(config, boundary_statement="dossier batch")
    with pytest.raises(ValueError, match="dossier_config_version"):
        replace(report.config_version_summaries[0], dossier_config_version="")
    with pytest.raises(ValueError, match="gate_name"):
        replace(report.gate_results[0], gate_name="approval_workflow")
    with pytest.raises(ValueError, match="source_report_name"):
        replace(report.source_summaries[0], source_report_name="approval_workflow")
    with pytest.raises(ValueError, match="finding_code"):
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code="",
            severity="incomplete",
            source_report_name="summary",
            dossier_count=1,
        )
```

`TradeProposalReviewDossierBatchConfig.__post_init__` must call `_require_canonical_string`, `_require_nonnegative_int`, `_require_probability_decimal`, and `_require_boundary_statement`.

- [ ] **Step 7: Run test and verify RED**

Run the same pytest command. Expected: FAIL for missing module.

## Task 2: Scope And Export Tests

**Files:**

- Create: `tests/test_proposal_review_dossier_batch_scope.py`
- Modify: `tests/test_init.py`
- Modify existing root scope allowlists that enumerate Level 2 artifact exports:
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

- [ ] **Step 1: Write failing scope tests**

Create `tests/test_proposal_review_dossier_batch_scope.py` with the same AST pattern as `tests/test_proposal_review_dossier_scope.py`, adjusted for the batch module.

Required checks:

- `__all__` equals `EXPECTED_PROPOSAL_REVIEW_DOSSIER_BATCH_EXPORTS`.
- imports are limited to exactly these prefixes:

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
    "polymarket_alpha_lab.proposal_review_dossier",
}
```

- first-party imports are import-from symbols only, not whole-module imports. `EXPECTED_FIRST_PARTY_IMPORTS` must be exactly:

```python
{
    "polymarket_alpha_lab.proposal_review_dossier": {
        "TradeProposalReviewDossierFindingRow",
        "TradeProposalReviewDossierGateResult",
        "TradeProposalReviewDossierReport",
        "TradeProposalReviewDossierSourceRow",
    },
}
```

- no raw proposal, raw review, market/API, broker/client/request/session/websocket/order/execution/account/credential, scraping/browser automation, settlement/reconciliation, compliance/legal/geographic, JSONL-read, load, replay, glob, or from-file/from-log identifiers appear.
- `FORBIDDEN_NAME_FRAGMENTS` must carry forward the Node 7 narrow fragments and include these batch-specific/prohibited variants: `approvalworkflow`, `proposalapproval`, `approvedproposalselector`, `latestdecisionselector`, `winningdecision`, `decisionresolution`, `decisionresolver`, `conflictreviewer`, `conflictresolver`, `investmentranking`, `rankinvestments`, `traderecommendation`, `recommendtrade`, `externalhistory`, `externalhistoryloader`, `historicalloader`, `downloadhistory`, `jsonlreader`, `readjsonl`, `loadjsonl`, `replayjsonl`, `globjsonl`, `fromfile`, `fromlog`, `scrape`, `scrapehtml`, `browserautomation`, `seleniumdriver`, `httpclient`, `requestpayload`, `marketclient`, `tradingclient`, `executionengine`, `orderpayload`, `credentialloader`, `credentialmanager`, `secret`, `password`, and `authtoken`.
- The root `EXPECTED_LEVEL_2_ARTIFACT_EXPORTS` sets in every modified sibling scope test must include `EXPECTED_PROPOSAL_REVIEW_DOSSIER_BATCH_EXPORTS` and must not allow broad public export fragments such as account, approval, broker, browser, client, credential, execution, geo, legal, ranking, recommendation, reconciliation, settlement, wallet, or websocket.
- README batch section must state report-only boundaries in its own section.
- Summary dataclass validation must be explicit: `TradeProposalReviewDossierBatchConfigVersionSummary` validates `dossier_config_version` and `dossier_count`; `TradeProposalReviewDossierBatchDuplicateSummary` validates `dossier_fingerprint` and `dossier_count`; `TradeProposalReviewDossierBatchFindingSummary` validates `finding_code`, `severity`, `source_report_name`, and `dossier_count`; `TradeProposalReviewDossierBatchSourceSummary` validates `source_report_name` and all four count fields.
- Update `tests/test_proposal_review_dossier_scope.py` so the existing Node 7 README test uses `readme.index("## Level 2 Node 8 Status", start)` as the Node 7 section end instead of `readme.index("## Automation Roadmap", start)`.

- [ ] **Step 2: Add package-root export tests**

Extend `tests/test_init.py` with:

```python
def test_package_root_exports_proposal_review_dossier_batch_artifacts():
    from polymarket_alpha_lab import (
        TradeProposalReviewDossierBatchConfig,
        TradeProposalReviewDossierBatchConfigVersionSummary,
        TradeProposalReviewDossierBatchDuplicateSummary,
        TradeProposalReviewDossierBatchFindingSummary,
        TradeProposalReviewDossierBatchGateResult,
        TradeProposalReviewDossierBatchLog,
        TradeProposalReviewDossierBatchReport,
        TradeProposalReviewDossierBatchSourceSummary,
        build_trade_proposal_review_dossier_batch_report,
    )

    assert TradeProposalReviewDossierBatchConfig.__name__ == "TradeProposalReviewDossierBatchConfig"
    assert TradeProposalReviewDossierBatchConfigVersionSummary.__name__ == "TradeProposalReviewDossierBatchConfigVersionSummary"
    assert TradeProposalReviewDossierBatchDuplicateSummary.__name__ == "TradeProposalReviewDossierBatchDuplicateSummary"
    assert callable(build_trade_proposal_review_dossier_batch_report)
```

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_dossier_batch_scope.py tests/test_init.py -q
```

Expected: FAIL because batch module/root exports do not exist.

## Task 3: Implement Batch Module And Root Exports

**Files:**

- Create: `src/polymarket_alpha_lab/proposal_review_dossier_batch.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`

- [ ] **Step 1: Implement minimal production module**

Implementation requirements:

- Follow `proposal_review_dossier.py` helper patterns for `_as_utc`, `_json_ready`, `_normalize_log_path`, `_validate_log_parent`, `_normalize_typed_tuple`, `_require_*`, and validation-before-open JSONL append.
- Reconstruct each supplied `TradeProposalReviewDossierReport` from public rows before aggregation.
- Build aggregate counts and ratios deterministically.
- Build gate rows ordered by `GATE_NAMES`.
- Build config-version summaries sorted by config version.
- Build duplicate summaries from normalized public dossier fingerprints; do not reject duplicates.
- Build finding summaries sorted by `(severity, source_report_name, finding_code)`.
- Build source summaries sorted by `source_report_name`.
- Report validates its own aggregate invariants in `__post_init__`.
- Avoid importing any sibling modules except `polymarket_alpha_lab.proposal_review_dossier`.

- [ ] **Step 2: Add root exports**

Add the batch public names to `src/polymarket_alpha_lab/__init__.py` near other proposal-review dossier exports and to `__all__`.

- [ ] **Step 3: Run focused tests and verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_dossier_batch.py tests/test_proposal_review_dossier_batch_scope.py tests/test_init.py -q
```

Expected: PASS.

## Task 4: README And Plan Layout

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Add Level 2 Node 8 documentation**

Add:

- `## Level 2 Node 8 Status`
- `## Level 2 Node 8 Python API`
- phase scope mention for proposal-review dossier batch health artifacts.
- repository layout entries for plan, source, and tests.

Add this exact README status/API text before `## Automation Roadmap`:

```markdown
## Level 2 Node 8 Status

Level 2 Node 8 adds report-only proposal-review dossier batch health artifacts over supplied `TradeProposalReviewDossierReport` values. It treats supplied dossier reports as caller-provided audit inputs and summarizes dossier counts, status ratios, config-version rows, duplicate dossier fingerprints, finding summaries, source summaries, and gate rows for audit only; it is not an approval workflow, proposal approval step, approved-proposal selector, latest-decision selector, decision-resolution process, investment ranking, trade recommendation, trade instruction, order instruction, broker request, order request, account action, strategy-promotion signal, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle credentials/private keys; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use trading SDK/broker/execution/transport clients; build broker or order request payloads; reconcile exchange accounts; perform reconciliation; review settlement; approve proposals; select latest decisions; resolve conflicting reviews; rank investments; recommend trades; or perform compliance/legal/geographic analysis.

## Level 2 Node 8 Python API

Node 8 is exposed through Python APIs:

- Configure proposal-review dossier batches with `TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1")`.
- Build proposal-review dossier batch health reports with `build_trade_proposal_review_dossier_batch_report(dossiers, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalReviewDossierBatchReport`.
- Inspect batch gates with `TradeProposalReviewDossierBatchGateResult`, config rows with `TradeProposalReviewDossierBatchConfigVersionSummary`, duplicate rows with `TradeProposalReviewDossierBatchDuplicateSummary`, finding rows with `TradeProposalReviewDossierBatchFindingSummary`, and source rows with `TradeProposalReviewDossierBatchSourceSummary`.
- Persist proposal-review dossier batch snapshots with `TradeProposalReviewDossierBatchLog(path).append(report)`.
```

Node 8 README boundary text must explicitly say it does not fetch/read external history or JSONL logs, scrape, authenticate, handle credentials/private keys, place/submit/sign/send/create/cancel orders, use trading SDK/broker/execution/transport clients, reconcile accounts, review settlement, rank investments, recommend trades, approve proposals, select latest decisions, resolve conflicting reviews, or perform compliance/legal/geographic analysis.

README scope tests must use these delimiters:

- Node 7 section start: `## Level 2 Node 7 Status`; Node 7 section end: `## Level 2 Node 8 Status`.
- Node 8 section start: `## Level 2 Node 8 Status`; Node 8 section end: `## Automation Roadmap` or the next `## ` heading after the Node 8 API subsection.

The Node 8 README test must require normalized fragments for `reportonlyproposalreviewdossierbatch`, `supplieddossierreports`, `notanapprovalworkflow`, `proposalapproval`, `approvedproposalselector`, `latestdecisionselector`, `decisionresolution`, `externalhistory`, `jsonllogs`, `scrape`, `credentialsprivatekeys`, `tradingsdkbrokerexecutiontransportclients`, `rankinvestments`, `recommendtrades`, `approveproposals`, `resolveconflictingreviews`, and `compliancelegalgeographicanalysis`.

- [ ] **Step 2: Run README-sensitive tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_dossier_batch_scope.py -q
```

Expected: PASS.

## Task 5: Verification, opencode Review, Handoff, Commit, Push

**Files:**

- Modify: `docs/superpowers/plans/2026-06-15-level-2-proposal-review-dossier-batch-health.md`

- [ ] **Step 1: Run verification**

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
- Git status: only intended Node 8 files modified/untracked.

- [ ] **Step 2: opencode implementation review**

Run local opencode:

```bash
opencode run \
  --model zhipuai-coding-plan/glm-5.2 \
  --variant max \
  --dir /home/ubuntu/polymarket-alpha-lab \
  --file docs/superpowers/plans/2026-06-15-level-2-proposal-review-dossier-batch-health.md \
  "Review the Level 2 Node 8 implementation. Return exactly: Critical findings: <number>; Important findings: <number>; Minor findings: <number>; Findings: ...; Verdict: Proceed | Proceed with fixes | Blocked. Treat any live trading, market/API fetch dependency, broker/client/request/session/websocket/order/account/authentication surface, execution dependency, credential/private-key/wallet handling, browser automation, scraping, JSONL-read, external-history loading, approval workflow, proposal approval, approved-proposal selection, investment ranking, trade recommendation, latest/winning decision selection, decision-resolution, settlement/reconciliation, compliance/legal/geographic, or raw-record/raw-packet dependency as Critical."
```

Accepted terminal state: `Critical findings: 0`, `Important findings: 0`, and `Verdict: Proceed` or `Verdict: Proceed with fixes`. Fix every Critical and Important finding before commit.

- [ ] **Step 3: Append Handoff Summary**

Append actual evidence:

```markdown
## Handoff Summary

- Node completed: Level 2 Node 8 proposal-review dossier batch health.
- Commit: pending at handoff-write time; final assistant response must report commit hash after commit.
- Pushed: pending at handoff-write time; final assistant response must report push result after push.
- Repo status before commit: <git status output>
- Verification commands:
  - `.venv/bin/python -m pytest -q`: <pass/fail summary>
  - `git diff --check`: <pass/fail summary>
  - `codegraph sync`: <pass/fail summary>
  - `codegraph status .`: <up-to-date/stale summary>
  - opencode implementation review: <Critical/Important/Minor counts and verdict>
- Files changed:
  - `src/polymarket_alpha_lab/proposal_review_dossier_batch.py`
  - `src/polymarket_alpha_lab/__init__.py`
  - `tests/test_proposal_review_dossier_batch.py`
  - `tests/test_proposal_review_dossier_batch_scope.py`
  - `tests/test_init.py`
  - scope allowlist tests
  - `README.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-review-dossier-batch-health.md`
- Uncommitted files after push: pending at handoff-write time; final assistant response must report post-push status.
- Next safe step: offline model-evidence comparison can consume batch health reports as supplied inputs, but it must remain report-only and require a new opencode-reviewed plan before implementation.
```

- [ ] **Step 4: Commit and push**

Stage every intended Node 8 file, commit with:

```bash
git commit -m "feat: add proposal review dossier batch health reports"
git push origin main
```

Expected: push succeeds and final status is clean against `origin/main`.

## Self-Review

- Spec coverage: The plan adds a report-only batch observability layer over supplied dossier reports and does not add fetching, scraping, JSONL reads, proposal approval, decision resolution, investment ranking, trade recommendations, credential handling, order placement, settlement/reconciliation work, or compliance/legal/geographic analysis.
- Placeholder scan: No implementation task uses TBD/TODO language. Public API, status rules, validation rules, scope tests, verification commands, opencode review policy, and handoff fields are specified.
- Type consistency: The same names are used throughout: `TradeProposalReviewDossierBatchConfig`, `TradeProposalReviewDossierBatchGateResult`, `TradeProposalReviewDossierBatchConfigVersionSummary`, `TradeProposalReviewDossierBatchDuplicateSummary`, `TradeProposalReviewDossierBatchFindingSummary`, `TradeProposalReviewDossierBatchSourceSummary`, `TradeProposalReviewDossierBatchReport`, `TradeProposalReviewDossierBatchLog`, and `build_trade_proposal_review_dossier_batch_report`.

## Handoff Summary

- Node completed: Level 2 Node 8 proposal-review dossier batch health.
- Commit: pending at handoff-write time; final assistant response must report commit hash after commit.
- Pushed: pending at handoff-write time; final assistant response must report push result after push.
- Repo status before commit:
  - `## main...origin/main`
  - Modified: `README.md`, `src/polymarket_alpha_lab/__init__.py`, `tests/test_analytics_history_scope.py`, `tests/test_analytics_scope.py`, `tests/test_forecast_evidence_scope.py`, `tests/test_init.py`, `tests/test_manual_review_queue_scope.py`, `tests/test_proposal_packet_scope.py`, `tests/test_proposal_review_coverage_scope.py`, `tests/test_proposal_review_diagnostics_scope.py`, `tests/test_proposal_review_dossier_scope.py`, `tests/test_proposal_review_quality_scope.py`, `tests/test_proposal_review_scope.py`, `tests/test_proposal_review_summary_scope.py`.
  - Untracked: `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison.md`, `src/polymarket_alpha_lab/proposal_review_dossier_batch.py`, `tests/test_proposal_review_dossier_batch.py`, `tests/test_proposal_review_dossier_batch_scope.py`.
- Verification commands:
  - `.venv/bin/python -m pytest -q`: `605 passed in 3.97s`.
  - `git diff --check`: passed with exit 0.
  - `codegraph sync`: passed; synced changed files.
  - `codegraph status .`: index is up to date.
  - opencode implementation review: `Critical findings: 0; Important findings: 0; Minor findings: 2; Verdict: Proceed`.
  - opencode next-plan review for `2026-06-15-level-2-proposal-evidence-comparison.md`: first pass `Critical findings: 0; Important findings: 3; Minor findings: 3; Verdict: Proceed with fixes`; after plan fixes, re-review `Critical findings: 0; Important findings: 0; Minor findings: 3; Verdict: Proceed`.
- Files changed:
  - `src/polymarket_alpha_lab/proposal_review_dossier_batch.py`
  - `src/polymarket_alpha_lab/__init__.py`
  - `tests/test_proposal_review_dossier_batch.py`
  - `tests/test_proposal_review_dossier_batch_scope.py`
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
  - `README.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-review-dossier-batch-health.md`
  - `docs/superpowers/plans/2026-06-15-level-2-proposal-evidence-comparison.md`
- Uncommitted files after push: pending at handoff-write time; final assistant response must report post-push status.
- Next safe step: Level 2 Node 9 proposal evidence comparison can consume supplied `PaperForecastEvidenceReport` and `TradeProposalReviewDossierBatchReport` values, but it must remain report-only and require a fresh opencode-reviewed implementation pass before code changes.
