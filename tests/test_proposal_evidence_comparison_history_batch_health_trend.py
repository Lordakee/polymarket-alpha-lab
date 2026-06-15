import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health import (
    TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow,
)
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow,
    build_trade_proposal_evidence_comparison_history_batch_health_trend_report,
)


BATCH_HEALTH_BOUNDARY = (
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


def _ratio(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(count) / Decimal(total)).quantize(Decimal("0.0001"))


def _rate_gate(
    gate_name: str,
    observed_value: Decimal | None,
    threshold: Decimal = Decimal("0.0000"),
) -> TradeProposalEvidenceComparisonHistoryBatchHealthGateResult:
    if observed_value is None:
        status = "incomplete"
    elif observed_value <= threshold:
        status = "pass"
    else:
        status = "fail"
    return TradeProposalEvidenceComparisonHistoryBatchHealthGateResult(
        gate_name,
        status,
        f"{gate_name} checked",
        observed_value,
        threshold,
    )


def batch_health_report_fixture(
    *,
    status: str = "proposal_evidence_comparison_history_batch_health_ready",
    index: int = 1,
    generated_at: datetime | None = None,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthReport:
    generated_at = generated_at or datetime(2026, 9, 12, 12, index, tzinfo=UTC)
    history_count = 2
    counts = {
        "divergent_comparison_history": 0,
        "incomplete_comparison_history": 0,
        "proposal_evidence_comparison_history_ready": 2,
        "unstable_comparison_history": 0,
    }
    duplicate_generated_at_count = 0
    duplicate_fingerprint_count = 0
    if status == "divergent_history_batch_health":
        counts["divergent_comparison_history"] = 1
        counts["proposal_evidence_comparison_history_ready"] = 1
    elif status == "incomplete_history_batch_health":
        counts["incomplete_comparison_history"] = 1
        counts["proposal_evidence_comparison_history_ready"] = 1
    elif status == "unstable_history_batch_health":
        counts["unstable_comparison_history"] = 1
        counts["proposal_evidence_comparison_history_ready"] = 1
    elif status == "duplicate_generated_at_batch_health":
        duplicate_generated_at_count = 2
    elif status == "duplicate_fingerprint_batch_health":
        duplicate_fingerprint_count = 2
    elif status != "proposal_evidence_comparison_history_batch_health_ready":
        raise AssertionError(f"unknown fixture status: {status}")

    incomplete_ratio = _ratio(counts["incomplete_comparison_history"], history_count)
    divergent_ratio = _ratio(counts["divergent_comparison_history"], history_count)
    unstable_ratio = _ratio(counts["unstable_comparison_history"], history_count)
    duplicate_generated_at_ratio = _ratio(duplicate_generated_at_count, history_count)
    duplicate_fingerprint_ratio = _ratio(duplicate_fingerprint_count, history_count)
    return TradeProposalEvidenceComparisonHistoryBatchHealthReport(
        generated_at=generated_at,
        config_version="history-batch-health-v1",
        report_only=True,
        boundary_statement=BATCH_HEALTH_BOUNDARY,
        history_report_count=history_count,
        complete_history_report_count=counts[
            "proposal_evidence_comparison_history_ready"
        ],
        incomplete_history_report_count=counts["incomplete_comparison_history"],
        divergent_history_report_count=counts["divergent_comparison_history"],
        unstable_history_report_count=counts["unstable_comparison_history"],
        duplicate_generated_at_count=duplicate_generated_at_count,
        duplicate_fingerprint_count=duplicate_fingerprint_count,
        incomplete_history_ratio=incomplete_ratio,
        divergent_history_ratio=divergent_ratio,
        unstable_history_ratio=unstable_ratio,
        duplicate_generated_at_ratio=duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=duplicate_fingerprint_ratio,
        first_history_generated_at=generated_at,
        last_history_generated_at=generated_at,
        status=status,
        gate_results=(
            TradeProposalEvidenceComparisonHistoryBatchHealthGateResult(
                "history_sample",
                "pass",
                "history_sample checked",
                history_count,
                1,
            ),
            _rate_gate("incomplete_history_rate", incomplete_ratio),
            _rate_gate("divergent_history_rate", divergent_ratio),
            _rate_gate("unstable_history_rate", unstable_ratio),
            _rate_gate("duplicate_generated_at_rate", duplicate_generated_at_ratio),
            _rate_gate("duplicate_fingerprint_rate", duplicate_fingerprint_ratio),
        ),
        status_rows=(
            TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow(
                "divergent_comparison_history",
                counts["divergent_comparison_history"],
                divergent_ratio,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow(
                "incomplete_comparison_history",
                counts["incomplete_comparison_history"],
                incomplete_ratio,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow(
                "proposal_evidence_comparison_history_ready",
                counts["proposal_evidence_comparison_history_ready"],
                _ratio(
                    counts["proposal_evidence_comparison_history_ready"],
                    history_count,
                ),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow(
                "unstable_comparison_history",
                counts["unstable_comparison_history"],
                unstable_ratio,
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


def trend_config(**overrides):
    values = {
        "config_version": "batch-health-trend-v1",
        "max_incomplete_batch_health_ratio": Decimal("1.0000"),
        "max_duplicate_generated_at_ratio": Decimal("1.0000"),
        "max_duplicate_fingerprint_ratio": Decimal("1.0000"),
    }
    values.update(overrides)
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig(**values)


def unsafe_trend_report(report, **changes):
    clone = object.__new__(type(report))
    for field_name in report.__dataclass_fields__:
        object.__setattr__(clone, field_name, getattr(report, field_name))
    for field_name, value in changes.items():
        object.__setattr__(clone, field_name, value)
    return clone


def test_batch_health_trend_summarizes_supplied_reports():
    reports = [
        batch_health_report_fixture(status="unstable_history_batch_health", index=6),
        batch_health_report_fixture(
            status="duplicate_fingerprint_batch_health",
            index=3,
        ),
        batch_health_report_fixture(
            status="proposal_evidence_comparison_history_batch_health_ready",
            index=1,
        ),
        batch_health_report_fixture(status="incomplete_history_batch_health", index=4),
        batch_health_report_fixture(
            status="duplicate_generated_at_batch_health",
            index=2,
        ),
        batch_health_report_fixture(status="divergent_history_batch_health", index=5),
    ]

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        reports,
        config=trend_config(),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )

    assert report.generated_at == datetime(2026, 9, 13, 12, tzinfo=UTC)
    assert report.config_version == "batch-health-trend-v1"
    assert report.report_only is True
    assert report.status == (
        "proposal_evidence_comparison_history_batch_health_trend_ready"
    )
    assert report.batch_health_report_count == 6
    assert report.ready_batch_health_report_count == 1
    assert report.incomplete_batch_health_report_count == 1
    assert report.duplicate_generated_at_batch_health_report_count == 1
    assert report.duplicate_fingerprint_batch_health_report_count == 1
    assert report.divergent_batch_health_report_count == 1
    assert report.unstable_batch_health_report_count == 1
    assert report.duplicate_generated_at_count == 0
    assert report.duplicate_fingerprint_count == 0
    assert report.incomplete_batch_health_ratio == Decimal("0.8333")
    assert report.duplicate_generated_at_ratio == Decimal("0.0000")
    assert report.duplicate_fingerprint_ratio == Decimal("0.0000")
    assert tuple(row.gate_name for row in report.gate_results) == (
        "batch_health_sample",
        "incomplete_batch_health_rate",
        "duplicate_generated_at_rate",
        "duplicate_fingerprint_rate",
    )
    assert all(row.status == "pass" for row in report.gate_results)
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
    assert tuple(
        row.batch_health_config_version for row in report.config_version_summaries
    ) == ("history-batch-health-v1",)
    assert report.config_version_summaries[0].batch_health_count == 6
    assert (
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
            "history_sample",
            "pass",
            6,
        )
        in report.gate_status_summaries
    )


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


def test_batch_health_trend_statuses_cover_rate_failures():
    duplicate_time = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        [
            batch_health_report_fixture(index=1),
            replace(
                batch_health_report_fixture(index=2),
                generated_at=batch_health_report_fixture(index=1).generated_at,
            ),
        ],
        config=trend_config(
            max_duplicate_generated_at_ratio=Decimal("0.0000"),
            max_duplicate_fingerprint_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )
    assert duplicate_time.status == "duplicate_generated_at_batch_health_trend"

    identical = batch_health_report_fixture(index=4)
    duplicate_fingerprint = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        [identical, identical],
        config=trend_config(
            max_duplicate_generated_at_ratio=Decimal("1.0000"),
            max_duplicate_fingerprint_ratio=Decimal("0.0000"),
        ),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )
    assert duplicate_fingerprint.status == "duplicate_fingerprint_batch_health_trend"

    incomplete = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        [
            batch_health_report_fixture(index=1),
            batch_health_report_fixture(
                status="incomplete_history_batch_health",
                index=2,
            ),
        ],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig(
            config_version="batch-health-trend-v1",
            max_duplicate_fingerprint_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )
    assert incomplete.status == "incomplete_batch_health_trend"


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
    assert three_time.duplicate_generated_at_summaries == (
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary(
            shared_time,
            3,
        ),
    )

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

    rows = tuple(
        (row.gate_name, row.gate_status, row.batch_health_count)
        for row in report.gate_status_summaries
    )
    assert ("duplicate_generated_at_rate", "fail", 1) in rows
    assert ("history_sample", "pass", 2) in rows


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


def test_batch_health_trend_rejects_subclasses_and_mutated_nested_rows(tmp_path):
    source = batch_health_report_fixture(index=1)

    class BatchHealthSubclass(TradeProposalEvidenceComparisonHistoryBatchHealthReport):
        pass

    subclass_value = BatchHealthSubclass(
        **{
            field_name: getattr(source, field_name)
            for field_name in source.__dataclass_fields__
        },
    )
    with pytest.raises(
        ValueError,
        match="TradeProposalEvidenceComparisonHistoryBatchHealthReport",
    ):
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


def test_batch_health_trend_rejects_missing_or_stale_gate_status_summaries(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        [batch_health_report_fixture(index=1), batch_health_report_fixture(index=2)],
        config=trend_config(),
        generated_at=datetime(2026, 9, 13, 12, tzinfo=UTC),
    )

    missing_summaries = unsafe_trend_report(report, gate_status_summaries=())
    missing_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog(
        tmp_path / "missing-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        missing_log.append(missing_summaries)
    assert not missing_log.path.exists()

    stale_summaries = unsafe_trend_report(
        report,
        gate_status_summaries=(
            replace(
                report.gate_status_summaries[0],
                batch_health_count=report.gate_status_summaries[0].batch_health_count
                - 1,
            ),
            *report.gate_status_summaries[1:],
        ),
    )
    stale_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog(
        tmp_path / "stale-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        stale_log.append(stale_summaries)
    assert not stale_log.path.exists()

    compensated_rows = [
        row
        for row in report.gate_status_summaries
        if row.gate_name != "duplicate_fingerprint_rate"
    ]
    compensated_rows.append(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
            "history_sample",
            "fail",
            report.batch_health_report_count,
        ),
    )
    compensated_summaries = unsafe_trend_report(
        report,
        gate_status_summaries=tuple(
            sorted(
                compensated_rows,
                key=lambda row: (row.gate_name, row.gate_status),
            ),
        ),
    )
    compensated_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog(
        tmp_path / "compensated-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        compensated_log.append(compensated_summaries)
    assert not compensated_log.path.exists()


def test_batch_health_trend_config_dataclasses_and_log_validate_invariants(tmp_path):
    with pytest.raises(ValueError, match="config_version"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig(config_version="")
    with pytest.raises(ValueError, match="min_batch_health_report_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig(
            config_version="batch-health-trend-v1",
            min_batch_health_report_count=-1,
        )
    with pytest.raises(ValueError, match="max_duplicate_fingerprint_ratio"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig(
            config_version="batch-health-trend-v1",
            max_duplicate_fingerprint_ratio=Decimal("1.0001"),
        )

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
        [batch_health_report_fixture(index=1), batch_health_report_fixture(index=2)],
        config=trend_config(),
        generated_at=datetime(2026, 9, 13, 22, 30, tzinfo=timezone(timedelta(hours=8))),
    )
    with pytest.raises(FrozenInstanceError):
        report.status = "other"
    with pytest.raises(ValueError, match="gate_name"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult(
            "approval_workflow",
            "pass",
            "bad",
        )
    with pytest.raises(ValueError, match="batch_health_status"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow(
            "approval_workflow",
            1,
            Decimal("1.0000"),
        )
    with pytest.raises(ValueError, match="gate_status"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
            "history_sample",
            "unknown",
            1,
        )
    with pytest.raises(ValueError, match="duplicate_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary(
            report.generated_at,
            1,
        )
    with pytest.raises(ValueError, match="duplicate_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary(
            "fingerprint",
            1,
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="status_rows"):
        replace(report, status_rows=list(report.status_rows))

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog(
        tmp_path / "nested" / "trend.jsonl",
    )
    log.append(report)
    log.append(report)
    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0].startswith('{"batch_health_report_count"')
    stored = json.loads(lines[0])
    assert stored["report_only"] is True
    assert stored["generated_at"] == "2026-09-13T14:30:00+00:00"
    assert stored["incomplete_batch_health_ratio"] == "0.0000"
    assert stored["gate_results"][0]["observed_value"] == 2
