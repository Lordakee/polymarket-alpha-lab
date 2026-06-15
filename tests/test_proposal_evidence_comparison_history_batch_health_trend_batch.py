import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow,
)
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow,
    build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report,
)


TREND_BOUNDARY = (
    "This is a report-only proposal evidence comparison history batch health trend artifact over "
    "supplied proposal evidence comparison history batch health reports, not an "
    "approval workflow, proposal approval, approved-proposal selector, "
    "latest-decision selector, decision-resolution process, investment ranking, "
    "trade recommendation, strategy-promotion signal, trade instruction, order "
    "instruction, broker request, order request, account action, account "
    "authentication, private-key handling, wallet signature, live-execution "
    "signal, credential workflow, external-history loader, JSONL reader, "
    "scraping workflow, outcome loader, settlement review, reconciliation "
    "process, compliance review, geographic access analysis, realized "
    "false-positive analysis, profitability analysis, or automatic "
    "order-placement authorization."
)


def _ratio(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(count) / Decimal(total)).quantize(Decimal("0.0001"))


def _trend_rate_gate(
    gate_name: str,
    observed_value: Decimal | None,
    threshold: Decimal = Decimal("0.0000"),
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult:
    if observed_value is None:
        status = "incomplete"
    elif observed_value <= threshold:
        status = "pass"
    else:
        status = "fail"
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult(
        gate_name,
        status,
        f"{gate_name} checked",
        observed_value,
        threshold,
    )


def trend_report_fixture(
    *,
    status: str = "proposal_evidence_comparison_history_batch_health_trend_ready",
    index: int = 1,
    generated_at: datetime | None = None,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport:
    generated_at = generated_at or datetime(2026, 9, 14, 12, index, tzinfo=UTC)
    trend_count = 2
    status_counts = {
        "divergent_history_batch_health": 0,
        "duplicate_fingerprint_batch_health": 0,
        "duplicate_generated_at_batch_health": 0,
        "incomplete_history_batch_health": 0,
        "proposal_evidence_comparison_history_batch_health_ready": 2,
        "unstable_history_batch_health": 0,
    }
    duplicate_generated_at_count = 0
    duplicate_fingerprint_count = 0
    if status == "incomplete_batch_health_trend":
        status_counts["incomplete_history_batch_health"] = 1
        status_counts["proposal_evidence_comparison_history_batch_health_ready"] = 1
    elif status == "duplicate_generated_at_batch_health_trend":
        duplicate_generated_at_count = 2
    elif status == "duplicate_fingerprint_batch_health_trend":
        duplicate_fingerprint_count = 2
    elif status != "proposal_evidence_comparison_history_batch_health_trend_ready":
        raise AssertionError(f"unknown fixture status: {status}")

    incomplete_ratio = _ratio(
        trend_count
        - status_counts["proposal_evidence_comparison_history_batch_health_ready"],
        trend_count,
    )
    duplicate_generated_at_ratio = _ratio(duplicate_generated_at_count, trend_count)
    duplicate_fingerprint_ratio = _ratio(duplicate_fingerprint_count, trend_count)
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport(
        generated_at=generated_at,
        config_version="batch-health-trend-v1",
        report_only=True,
        boundary_statement=TREND_BOUNDARY,
        batch_health_report_count=trend_count,
        ready_batch_health_report_count=status_counts[
            "proposal_evidence_comparison_history_batch_health_ready"
        ],
        incomplete_batch_health_report_count=status_counts[
            "incomplete_history_batch_health"
        ],
        duplicate_generated_at_batch_health_report_count=status_counts[
            "duplicate_generated_at_batch_health"
        ],
        duplicate_fingerprint_batch_health_report_count=status_counts[
            "duplicate_fingerprint_batch_health"
        ],
        divergent_batch_health_report_count=status_counts[
            "divergent_history_batch_health"
        ],
        unstable_batch_health_report_count=status_counts["unstable_history_batch_health"],
        duplicate_generated_at_count=duplicate_generated_at_count,
        duplicate_fingerprint_count=duplicate_fingerprint_count,
        incomplete_batch_health_ratio=incomplete_ratio,
        duplicate_generated_at_ratio=duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=duplicate_fingerprint_ratio,
        first_batch_health_generated_at=generated_at,
        last_batch_health_generated_at=generated_at,
        status=status,
        gate_results=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult(
                "batch_health_sample",
                "pass",
                "batch_health_sample checked",
                trend_count,
                1,
            ),
            _trend_rate_gate("incomplete_batch_health_rate", incomplete_ratio),
            _trend_rate_gate(
                "duplicate_generated_at_rate",
                duplicate_generated_at_ratio,
            ),
            _trend_rate_gate(
                "duplicate_fingerprint_rate",
                duplicate_fingerprint_ratio,
            ),
        ),
        status_rows=tuple(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow(
                batch_health_status,
                batch_health_count,
                _ratio(batch_health_count, trend_count),
            )
            for batch_health_status, batch_health_count in status_counts.items()
        ),
        config_version_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary(
                "history-batch-health-v1",
                trend_count,
            ),
        ),
        gate_status_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
                "divergent_history_rate",
                "pass",
                trend_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
                "duplicate_fingerprint_rate",
                "pass" if duplicate_fingerprint_count == 0 else "fail",
                trend_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
                "duplicate_generated_at_rate",
                "pass" if duplicate_generated_at_count == 0 else "fail",
                trend_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
                "history_sample",
                "pass",
                trend_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
                "incomplete_history_rate",
                "pass",
                trend_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
                "unstable_history_rate",
                "pass",
                trend_count,
            ),
        ),
        duplicate_generated_at_summaries=(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary(
                    generated_at,
                    duplicate_generated_at_count,
                ),
            )
            if duplicate_generated_at_count
            else ()
        ),
        duplicate_fingerprint_summaries=(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary(
                    "fixture-fingerprint",
                    duplicate_fingerprint_count,
                ),
            )
            if duplicate_fingerprint_count
            else ()
        ),
    )


def trend_batch_config(**overrides):
    values = {
        "config_version": "batch-health-trend-batch-v1",
        "max_incomplete_trend_ratio": Decimal("1.0000"),
        "max_duplicate_generated_at_ratio": Decimal("1.0000"),
        "max_duplicate_fingerprint_ratio": Decimal("1.0000"),
    }
    values.update(overrides)
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig(**values)


def unsafe_trend_batch_report(report, **changes):
    clone = object.__new__(type(report))
    for field_name in report.__dataclass_fields__:
        object.__setattr__(clone, field_name, getattr(report, field_name))
    for field_name, value in changes.items():
        object.__setattr__(clone, field_name, value)
    return clone


def test_trend_batch_summarizes_supplied_trend_reports():
    reports = [
        trend_report_fixture(
            status="duplicate_fingerprint_batch_health_trend",
            index=3,
        ),
        trend_report_fixture(
            status="proposal_evidence_comparison_history_batch_health_trend_ready",
            index=1,
        ),
        trend_report_fixture(status="incomplete_batch_health_trend", index=4),
        trend_report_fixture(
            status="duplicate_generated_at_batch_health_trend",
            index=2,
        ),
    ]

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        reports,
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )

    assert report.generated_at == datetime(2026, 9, 15, 12, tzinfo=UTC)
    assert report.config_version == "batch-health-trend-batch-v1"
    assert report.report_only is True
    assert report.status == (
        "proposal_evidence_comparison_history_batch_health_trend_batch_ready"
    )
    assert report.trend_report_count == 4
    assert report.ready_trend_report_count == 1
    assert report.incomplete_trend_report_count == 1
    assert report.duplicate_generated_at_trend_report_count == 1
    assert report.duplicate_fingerprint_trend_report_count == 1
    assert report.duplicate_generated_at_count == 0
    assert report.duplicate_fingerprint_count == 0
    assert report.incomplete_trend_ratio == Decimal("0.7500")
    assert report.duplicate_generated_at_ratio == Decimal("0.0000")
    assert report.duplicate_fingerprint_ratio == Decimal("0.0000")
    assert tuple(row.gate_name for row in report.gate_results) == (
        "trend_sample",
        "incomplete_trend_rate",
        "duplicate_generated_at_rate",
        "duplicate_fingerprint_rate",
    )
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.trend_status for row in report.status_rows) == (
        "duplicate_fingerprint_batch_health_trend",
        "duplicate_generated_at_batch_health_trend",
        "incomplete_batch_health_trend",
        "proposal_evidence_comparison_history_batch_health_trend_ready",
    )
    assert tuple(row.trend_count for row in report.status_rows) == (1, 1, 1, 1)
    assert report.config_version_summaries[0].trend_config_version == (
        "batch-health-trend-v1"
    )
    assert report.config_version_summaries[0].trend_count == 4
    assert (
        "duplicate_generated_at_rate",
        "fail",
        1,
    ) in tuple(
        (row.gate_name, row.gate_status, row.trend_count)
        for row in report.gate_status_summaries
    )


def test_trend_batch_empty_sample_is_incomplete():
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [],
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )

    assert report.status == "incomplete_batch_health_trend_batch"
    assert report.trend_report_count == 0
    assert report.incomplete_trend_ratio is None
    assert report.duplicate_generated_at_ratio is None
    assert report.duplicate_fingerprint_ratio is None
    assert report.first_trend_generated_at is None
    assert report.last_trend_generated_at is None
    assert all(row.trend_ratio is None for row in report.status_rows)
    assert tuple(row.status for row in report.gate_results) == (
        "incomplete",
        "incomplete",
        "incomplete",
        "incomplete",
    )


def test_trend_batch_statuses_cover_rate_failures():
    shared_time = trend_report_fixture(index=1).generated_at
    duplicate_time = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [
            trend_report_fixture(index=1),
            replace(trend_report_fixture(index=2), generated_at=shared_time),
        ],
        config=trend_batch_config(
            max_duplicate_generated_at_ratio=Decimal("0.0000"),
            max_duplicate_fingerprint_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )
    assert duplicate_time.status == "duplicate_generated_at_batch_health_trend_batch"

    identical = trend_report_fixture(index=4)
    duplicate_fingerprint = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [identical, identical],
        config=trend_batch_config(
            max_duplicate_generated_at_ratio=Decimal("1.0000"),
            max_duplicate_fingerprint_ratio=Decimal("0.0000"),
        ),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )
    assert duplicate_fingerprint.status == (
        "duplicate_fingerprint_batch_health_trend_batch"
    )

    incomplete = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [
            trend_report_fixture(index=1),
            trend_report_fixture(status="incomplete_batch_health_trend", index=2),
        ],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig(
            config_version="batch-health-trend-batch-v1",
            max_duplicate_fingerprint_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )
    assert incomplete.status == "incomplete_batch_health_trend_batch"


def test_trend_batch_duplicate_counts_use_full_collision_groups():
    shared_time = datetime(2026, 9, 15, 1, tzinfo=UTC)
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [
            replace(trend_report_fixture(index=1), generated_at=shared_time),
            replace(trend_report_fixture(index=2), generated_at=shared_time),
        ],
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )
    assert report.duplicate_generated_at_count == 2
    assert report.duplicate_generated_at_summaries[0].duplicate_count == 2

    three_time = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [
            replace(trend_report_fixture(index=3), generated_at=shared_time),
            replace(trend_report_fixture(index=4), generated_at=shared_time),
            replace(trend_report_fixture(index=5), generated_at=shared_time),
        ],
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )
    assert three_time.duplicate_generated_at_count == 3
    assert three_time.duplicate_generated_at_summaries == (
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary(
            shared_time,
            3,
        ),
    )

    identical = trend_report_fixture(index=9)
    two_fingerprint = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [identical, identical],
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )
    assert two_fingerprint.duplicate_fingerprint_count == 2
    assert two_fingerprint.duplicate_fingerprint_summaries[0].duplicate_count == 2

    three_fingerprint = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [identical, identical, identical],
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )
    assert three_fingerprint.duplicate_fingerprint_count == 3
    assert three_fingerprint.duplicate_fingerprint_summaries[0].duplicate_count == 3


def test_trend_batch_gate_status_summaries_use_existing_trend_gate_rows():
    first = trend_report_fixture(index=1)
    second = trend_report_fixture(
        status="duplicate_generated_at_batch_health_trend",
        index=2,
    )

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [second, first],
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )

    rows = tuple(
        (row.gate_name, row.gate_status, row.trend_count)
        for row in report.gate_status_summaries
    )
    assert ("duplicate_generated_at_rate", "fail", 1) in rows
    assert ("duplicate_generated_at_rate", "pass", 1) in rows
    assert ("batch_health_sample", "pass", 2) in rows


def test_trend_batch_ordering_uses_normalized_generated_at():
    late = trend_report_fixture(index=3)
    early = replace(
        trend_report_fixture(index=1),
        generated_at=datetime(2026, 9, 14, 21, tzinfo=timezone(timedelta(hours=-4))),
    )
    middle = trend_report_fixture(index=2)

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [late, middle, early],
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )

    assert report.first_trend_generated_at == middle.generated_at
    assert report.last_trend_generated_at == datetime(2026, 9, 15, 1, tzinfo=UTC)


def test_trend_batch_rejects_bad_inputs_before_iteration():
    class ExplodingIterable:
        def __iter__(self):
            raise AssertionError("loader-shaped iterable was consumed")

    class LogShapedInput:
        path = Path("trend.jsonl")

        def append(self, report):
            raise AssertionError("append-only log was consumed")

    for bad_input in (
        "[]",
        b"[]",
        {"report": trend_report_fixture()},
        Path("trend.jsonl"),
        '{"serialized": true}',
        (item for item in (trend_report_fixture(),)),
        ExplodingIterable(),
        LogShapedInput(),
        object(),
    ):
        with pytest.raises(ValueError, match="trend_reports"):
            build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
                bad_input,
                config=trend_batch_config(),
                generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
            )


def test_trend_batch_rejects_subclasses_and_mutated_nested_rows(tmp_path):
    source = trend_report_fixture(index=1)

    class TrendSubclass(TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport):
        pass

    subclass_value = TrendSubclass(
        **{
            field_name: getattr(source, field_name)
            for field_name in source.__dataclass_fields__
        },
    )
    with pytest.raises(
        ValueError,
        match="TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport",
    ):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
            [subclass_value],
            config=trend_batch_config(),
            generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
        )

    drift = trend_report_fixture(index=2)
    object.__setattr__(drift.gate_results[0], "status", "unknown")
    with pytest.raises(ValueError, match="status"):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
            [drift],
            config=trend_batch_config(),
            generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
        )

    valid = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [source],
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )
    invalid = unsafe_trend_batch_report(
        valid,
        duplicate_generated_at_ratio=Decimal("NaN"),
    )
    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog(
        tmp_path / "trend-batch.jsonl",
    )
    with pytest.raises(ValueError, match="finite|duplicate_generated_at_ratio"):
        log.append(invalid)
    assert not log.path.exists()


def test_trend_batch_rejects_stale_or_wrong_typed_gate_payloads(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [trend_report_fixture(index=1), trend_report_fixture(index=2)],
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )

    bad_sample_type = unsafe_trend_batch_report(
        report,
        gate_results=(
            replace(report.gate_results[0], observed_value=Decimal("2")),
            *report.gate_results[1:],
        ),
    )
    with pytest.raises(ValueError, match="trend_sample observed_value"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog(
            tmp_path / "bad-sample.jsonl",
        ).append(bad_sample_type)

    bad_rate_type = unsafe_trend_batch_report(
        report,
        gate_results=(
            *report.gate_results[:1],
            replace(report.gate_results[1], observed_value=0),
            *report.gate_results[2:],
        ),
    )
    with pytest.raises(ValueError, match="observed_value must be a Decimal"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog(
            tmp_path / "bad-rate.jsonl",
        ).append(bad_rate_type)


def test_trend_batch_rejects_missing_or_stale_gate_status_summaries(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [trend_report_fixture(index=1), trend_report_fixture(index=2)],
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )

    missing_summaries = unsafe_trend_batch_report(report, gate_status_summaries=())
    missing_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog(
        tmp_path / "missing-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        missing_log.append(missing_summaries)
    assert not missing_log.path.exists()

    stale_summaries = unsafe_trend_batch_report(
        report,
        gate_status_summaries=(
            replace(
                report.gate_status_summaries[0],
                trend_count=report.gate_status_summaries[0].trend_count - 1,
            ),
            *report.gate_status_summaries[1:],
        ),
    )
    stale_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog(
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
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary(
            "batch_health_sample",
            "fail",
            report.trend_report_count,
        ),
    )
    compensated_summaries = unsafe_trend_batch_report(
        report,
        gate_status_summaries=tuple(
            sorted(
                compensated_rows,
                key=lambda row: (row.gate_name, row.gate_status),
            ),
        ),
    )
    compensated_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog(
        tmp_path / "compensated-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        compensated_log.append(compensated_summaries)
    assert not compensated_log.path.exists()


def test_trend_batch_rejects_impossible_sample_gate_status_summary(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [trend_report_fixture(index=1), trend_report_fixture(index=2)],
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )
    impossible_rows = tuple(
        sorted(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary(
                    "batch_health_sample",
                    "fail",
                    report.trend_report_count,
                )
                if row.gate_name == "batch_health_sample"
                else row
                for row in report.gate_status_summaries
            ),
            key=lambda row: (row.gate_name, row.gate_status),
        ),
    )
    impossible_report = unsafe_trend_batch_report(
        report,
        gate_status_summaries=impossible_rows,
    )

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog(
        tmp_path / "impossible-sample-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        log.append(impossible_report)
    assert not log.path.exists()


def test_trend_batch_rejects_duplicate_generated_at_summary_outside_bounds(tmp_path):
    shared_time = datetime(2026, 9, 15, 1, tzinfo=UTC)
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [
            replace(trend_report_fixture(index=1), generated_at=shared_time),
            replace(trend_report_fixture(index=2), generated_at=shared_time),
        ],
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 12, tzinfo=UTC),
    )
    out_of_bounds_report = unsafe_trend_batch_report(
        report,
        duplicate_generated_at_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary(
                shared_time + timedelta(days=1),
                report.duplicate_generated_at_count,
            ),
        ),
    )

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog(
        tmp_path / "out-of-bounds-duplicate-generated-at.jsonl",
    )
    with pytest.raises(ValueError, match="duplicate_generated_at_summaries"):
        log.append(out_of_bounds_report)
    assert not log.path.exists()


def test_trend_batch_config_dataclasses_and_log_validate_invariants(tmp_path):
    with pytest.raises(ValueError, match="config_version"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig(
            config_version="",
        )
    with pytest.raises(ValueError, match="min_trend_report_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig(
            config_version="batch-health-trend-batch-v1",
            min_trend_report_count=-1,
        )
    with pytest.raises(ValueError, match="max_duplicate_fingerprint_ratio"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig(
            config_version="batch-health-trend-batch-v1",
            max_duplicate_fingerprint_ratio=Decimal("1.0001"),
        )

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(
        [trend_report_fixture(index=1), trend_report_fixture(index=2)],
        config=trend_batch_config(),
        generated_at=datetime(2026, 9, 15, 22, 30, tzinfo=timezone(timedelta(hours=8))),
    )
    with pytest.raises(FrozenInstanceError):
        report.status = "other"
    with pytest.raises(ValueError, match="gate_name"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult(
            "approval_workflow",
            "pass",
            "bad",
        )
    with pytest.raises(ValueError, match="trend_status"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow(
            "approval_workflow",
            1,
            Decimal("1.0000"),
        )
    with pytest.raises(ValueError, match="gate_status"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary(
            "batch_health_sample",
            "unknown",
            1,
        )
    with pytest.raises(ValueError, match="duplicate_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary(
            report.generated_at,
            1,
        )
    with pytest.raises(ValueError, match="duplicate_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary(
            "fingerprint",
            1,
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="status_rows"):
        replace(report, status_rows=list(report.status_rows))
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(report, boundary_statement="too short")

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog(
        tmp_path / "nested" / "trend-batch.jsonl",
    )
    log.append(report)
    log.append(report)
    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0].startswith('{"boundary_statement"')
    stored = json.loads(lines[0])
    assert stored["report_only"] is True
    assert stored["generated_at"] == "2026-09-15T14:30:00+00:00"
    assert stored["incomplete_trend_ratio"] == "0.0000"
    assert stored["gate_results"][0]["observed_value"] == 2
