import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

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
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow,
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
            (
                "incomplete"
                if incomplete_ratio is None
                else "fail"
                if incomplete_ratio > Decimal("0.0000")
                else "pass"
            ),
            "incomplete comparison rate checked",
            incomplete_ratio,
            Decimal("0.0000"),
        ),
        TradeProposalEvidenceComparisonHistoryGateResult(
            "divergent_comparison_rate",
            (
                "incomplete"
                if divergent_ratio is None
                else "fail"
                if divergent_ratio > Decimal("0.0000")
                else "pass"
            ),
            "divergent comparison rate checked",
            divergent_ratio,
            Decimal("0.0000"),
        ),
        TradeProposalEvidenceComparisonHistoryGateResult(
            "unstable_comparison_rate",
            (
                "incomplete"
                if unstable_ratio is None
                else "fail"
                if unstable_ratio > Decimal("0.0000")
                else "pass"
            ),
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
                _ratio(counts["proposal_evidence_comparison_complete"], comparison_count),
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


def duplicate_batch_health_report_fixture():
    shared = complete_history_fixture(index=1)
    same_generated_at = replace(
        divergent_history_fixture(index=2),
        generated_at=shared.generated_at,
    )
    identical = complete_history_fixture(index=3)
    return build_trade_proposal_evidence_comparison_history_batch_health_report(
        [shared, same_generated_at, identical, identical],
        config=relaxed_batch_health_config(),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )


def unsafe_batch_health_report(report, **changes):
    clone = object.__new__(type(report))
    for field_name in report.__dataclass_fields__:
        object.__setattr__(clone, field_name, getattr(report, field_name))
    for field_name, value in changes.items():
        object.__setattr__(clone, field_name, value)
    return clone


def test_build_trade_proposal_evidence_comparison_history_batch_health_report_summarizes_reports():
    complete = complete_history_fixture(index=1)
    divergent = divergent_history_fixture(index=2)
    unstable = unstable_history_fixture(index=3)

    report = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [unstable, complete, divergent],
        config=relaxed_batch_health_config(),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )

    assert report.generated_at == datetime(2026, 9, 11, 12, tzinfo=UTC)
    assert report.config_version == "history-batch-health-v1"
    assert report.report_only is True
    assert report.status == "proposal_evidence_comparison_history_batch_health_ready"
    assert report.history_report_count == 3
    assert report.complete_history_report_count == 1
    assert report.incomplete_history_report_count == 0
    assert report.divergent_history_report_count == 1
    assert report.unstable_history_report_count == 1
    assert report.duplicate_generated_at_count == 0
    assert report.duplicate_fingerprint_count == 0
    assert report.incomplete_history_ratio == Decimal("0.0000")
    assert report.divergent_history_ratio == Decimal("0.3333")
    assert report.unstable_history_ratio == Decimal("0.3333")
    assert report.duplicate_generated_at_ratio == Decimal("0.0000")
    assert report.duplicate_fingerprint_ratio == Decimal("0.0000")
    assert report.first_history_generated_at == complete.generated_at
    assert report.last_history_generated_at == unstable.generated_at
    assert tuple(row.gate_name for row in report.gate_results) == (
        "history_sample",
        "incomplete_history_rate",
        "divergent_history_rate",
        "unstable_history_rate",
        "duplicate_generated_at_rate",
        "duplicate_fingerprint_rate",
    )
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.history_status for row in report.status_rows) == (
        "divergent_comparison_history",
        "incomplete_comparison_history",
        "proposal_evidence_comparison_history_ready",
        "unstable_comparison_history",
    )
    assert tuple(row.history_count for row in report.status_rows) == (1, 0, 1, 1)
    assert tuple(row.history_ratio for row in report.status_rows) == (
        Decimal("0.3333"),
        Decimal("0.0000"),
        Decimal("0.3333"),
        Decimal("0.3333"),
    )
    assert tuple(
        row.history_config_version for row in report.config_version_summaries
    ) == ("comparison-history-v1",)
    assert tuple(row.history_count for row in report.config_version_summaries) == (3,)
    assert report.finding_summaries == (
        TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary(
            "evidence_consistency_divergent",
            "divergent",
            "comparison",
            1,
        ),
        TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary(
            "dossier_batch_unstable",
            "unstable",
            "dossier_batch",
            1,
        ),
    )
    assert report.source_transition_summaries == (
        TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary(
            "dossier_batch",
            "proposal_review_dossier_batch_ready",
            "proposal_review_dossier_batch_ready",
            1,
        ),
        TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary(
            "forecast_evidence",
            "paper_review_ready",
            "paper_review_ready",
            1,
        ),
    )


def test_batch_health_statuses_cover_rate_failures_and_empty_samples():
    empty = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [],
        config=relaxed_batch_health_config(),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )
    assert empty.status == "incomplete_history_batch_health"
    assert empty.history_report_count == 0
    assert empty.first_history_generated_at is None
    assert empty.last_history_generated_at is None
    assert empty.finding_summaries == ()
    assert empty.source_transition_summaries == ()
    assert tuple(row.status for row in empty.gate_results) == (
        "incomplete",
        "incomplete",
        "incomplete",
        "incomplete",
        "incomplete",
        "incomplete",
    )
    assert all(row.history_ratio is None for row in empty.status_rows)

    below_sample = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [complete_history_fixture(1)],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            min_history_report_count=2,
            max_duplicate_fingerprint_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )
    assert below_sample.status == "incomplete_history_batch_health"
    assert below_sample.gate_results[0].status == "incomplete"

    duplicate_time = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [
            complete_history_fixture(index=1),
            replace(divergent_history_fixture(index=2), generated_at=complete_history_fixture(index=1).generated_at),
        ],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            max_divergent_history_ratio=Decimal("1.0000"),
            max_duplicate_fingerprint_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )
    assert duplicate_time.status == "duplicate_generated_at_batch_health"
    assert duplicate_time.gate_results[4].status == "fail"

    duplicate_fingerprint = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [complete_history_fixture(1), complete_history_fixture(1)],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            max_duplicate_generated_at_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )
    assert duplicate_fingerprint.status == "duplicate_fingerprint_batch_health"
    assert duplicate_fingerprint.gate_results[5].status == "fail"

    divergent = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [complete_history_fixture(1), divergent_history_fixture(2)],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            max_duplicate_fingerprint_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )
    assert divergent.status == "divergent_history_batch_health"

    unstable = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [complete_history_fixture(1), unstable_history_fixture(2)],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            max_divergent_history_ratio=Decimal("1.0000"),
            max_duplicate_fingerprint_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )
    assert unstable.status == "unstable_history_batch_health"

    incomplete = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [complete_history_fixture(1), incomplete_history_fixture(2)],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            max_divergent_history_ratio=Decimal("1.0000"),
            max_unstable_history_ratio=Decimal("1.0000"),
            max_duplicate_fingerprint_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )
    assert incomplete.status == "incomplete_history_batch_health"


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

    bad_threshold_type = unsafe_batch_health_report(
        report,
        gate_results=(
            *report.gate_results[:2],
            replace(report.gate_results[2], threshold=0),
            *report.gate_results[3:],
        ),
    )
    with pytest.raises(ValueError, match="threshold must be a Decimal"):
        TradeProposalEvidenceComparisonHistoryBatchHealthLog(
            tmp_path / "bad-threshold-type.jsonl",
        ).append(bad_threshold_type)

    inconsistent_status = unsafe_batch_health_report(
        report,
        gate_results=(
            *report.gate_results[:1],
            replace(report.gate_results[1], status="fail"),
            *report.gate_results[2:],
        ),
    )
    with pytest.raises(ValueError, match="status must match threshold"):
        TradeProposalEvidenceComparisonHistoryBatchHealthLog(
            tmp_path / "inconsistent-status.jsonl",
        ).append(inconsistent_status)


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


def test_batch_health_rejects_bad_inputs():
    config = relaxed_batch_health_config()
    generated_at = datetime(2026, 9, 11, 12, tzinfo=UTC)

    class ExplodingIterable:
        def __iter__(self):
            raise AssertionError("loader-shaped iterable was consumed")

    class LogShapedInput:
        path = Path("comparison-history.jsonl")

        def append(self, report):
            raise AssertionError("append-only log was consumed")

    for bad_input in (
        "[]",
        b"[]",
        {"history": complete_history_fixture()},
        Path("history.jsonl"),
        '{"serialized": true}',
        (item for item in (complete_history_fixture(),)),
        ExplodingIterable(),
        LogShapedInput(),
        object(),
    ):
        with pytest.raises(ValueError, match="history_reports"):
            build_trade_proposal_evidence_comparison_history_batch_health_report(
                bad_input,
                config=config,
                generated_at=generated_at,
            )

    with pytest.raises(ValueError, match="config"):
        build_trade_proposal_evidence_comparison_history_batch_health_report(
            [complete_history_fixture()],
            config=object(),
            generated_at=generated_at,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_trade_proposal_evidence_comparison_history_batch_health_report(
            [complete_history_fixture()],
            config=config,
            generated_at="2026-09-11T12:00:00+00:00",
        )


def test_batch_health_rejects_subclasses_and_revalidates_supplied_history_reports():
    history = complete_history_fixture()

    class HistorySubclass(TradeProposalEvidenceComparisonHistoryReport):
        pass

    history_subclass = HistorySubclass(
        generated_at=history.generated_at,
        config_version=history.config_version,
        report_only=history.report_only,
        boundary_statement=history.boundary_statement,
        comparison_count=history.comparison_count,
        complete_comparison_count=history.complete_comparison_count,
        incomplete_comparison_count=history.incomplete_comparison_count,
        divergent_comparison_count=history.divergent_comparison_count,
        unstable_comparison_count=history.unstable_comparison_count,
        incomplete_comparison_ratio=history.incomplete_comparison_ratio,
        divergent_comparison_ratio=history.divergent_comparison_ratio,
        unstable_comparison_ratio=history.unstable_comparison_ratio,
        first_comparison_generated_at=history.first_comparison_generated_at,
        last_comparison_generated_at=history.last_comparison_generated_at,
        status=history.status,
        gate_results=history.gate_results,
        status_rows=history.status_rows,
        finding_summaries=history.finding_summaries,
        config_version_summaries=history.config_version_summaries,
        source_transitions=history.source_transitions,
    )
    with pytest.raises(ValueError, match="TradeProposalEvidenceComparisonHistoryReport"):
        build_trade_proposal_evidence_comparison_history_batch_health_report(
            [history_subclass],
            config=relaxed_batch_health_config(),
            generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
        )

    gate_drift = complete_history_fixture(index=1)
    object.__setattr__(gate_drift.gate_results[0], "status", "unknown")
    with pytest.raises(ValueError, match="status"):
        build_trade_proposal_evidence_comparison_history_batch_health_report(
            [gate_drift],
            config=relaxed_batch_health_config(),
            generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
        )

    status_row_drift = complete_history_fixture(index=2)
    object.__setattr__(status_row_drift.status_rows[2], "comparison_count", 999)
    with pytest.raises(ValueError, match="status_rows|history_count|comparison_count"):
        build_trade_proposal_evidence_comparison_history_batch_health_report(
            [status_row_drift],
            config=relaxed_batch_health_config(),
            generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
        )

    config_summary_drift = complete_history_fixture(index=3)
    object.__setattr__(
        config_summary_drift.config_version_summaries[0],
        "comparison_count",
        999,
    )
    with pytest.raises(ValueError, match="config_version_summaries"):
        build_trade_proposal_evidence_comparison_history_batch_health_report(
            [config_summary_drift],
            config=relaxed_batch_health_config(),
            generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
        )

    finding_drift = divergent_history_fixture(index=4)
    object.__setattr__(finding_drift.finding_summaries[0], "severity", "approval")
    with pytest.raises(ValueError, match="severity"):
        build_trade_proposal_evidence_comparison_history_batch_health_report(
            [finding_drift],
            config=relaxed_batch_health_config(),
            generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
        )

    transition_drift = complete_history_fixture(index=5)
    object.__setattr__(transition_drift.source_transitions[0], "transition_count", 999)
    with pytest.raises(ValueError, match="source_transitions"):
        build_trade_proposal_evidence_comparison_history_batch_health_report(
            [transition_drift],
            config=relaxed_batch_health_config(),
            generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
        )


def test_batch_health_report_rejects_mutated_nested_rows(tmp_path):
    report = duplicate_batch_health_report_fixture()

    bad_gate_order = unsafe_batch_health_report(
        report,
        gate_results=report.gate_results[1:] + report.gate_results[:1],
    )
    with pytest.raises(ValueError, match="gate_results must contain batch health gates"):
        TradeProposalEvidenceComparisonHistoryBatchHealthLog(tmp_path / "bad.jsonl").append(
            bad_gate_order,
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


def test_batch_health_config_and_dataclasses_validate_invariants():
    with pytest.raises(ValueError, match="config_version"):
        TradeProposalEvidenceComparisonHistoryBatchHealthConfig(config_version="")
    with pytest.raises(ValueError, match="min_history_report_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            min_history_report_count=-1,
        )
    with pytest.raises(ValueError, match="max_duplicate_fingerprint_ratio"):
        TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            max_duplicate_fingerprint_ratio=Decimal("1.0001"),
        )
    with pytest.raises(ValueError, match="max_unstable_history_ratio"):
        TradeProposalEvidenceComparisonHistoryBatchHealthConfig(
            config_version="history-batch-health-v1",
            max_unstable_history_ratio=1,
        )

    report = duplicate_batch_health_report_fixture()
    with pytest.raises(FrozenInstanceError):
        report.status = "other"
    with pytest.raises(ValueError, match="gate_name"):
        TradeProposalEvidenceComparisonHistoryBatchHealthGateResult(
            gate_name="approval_workflow",
            status="pass",
            message="bad",
        )
    with pytest.raises(ValueError, match="observed_value"):
        replace(report.gate_results[0], observed_value=True)
    with pytest.raises(ValueError, match="observed_value"):
        replace(report.gate_results[0], observed_value=1.0)
    with pytest.raises(ValueError, match="history_status"):
        TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow(
            history_status="approval_workflow",
            history_count=1,
            history_ratio=Decimal("1.0000"),
        )
    with pytest.raises(ValueError, match="duplicate_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary(
            report.generated_at,
            1,
        )
    with pytest.raises(ValueError, match="duplicate_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary(
            "fingerprint",
            1,
        )
    with pytest.raises(ValueError, match="source_name"):
        TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary(
            "approval",
            "paper_review_ready",
            "paper_review_ready",
            1,
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        replace(report, generated_at="2026-09-11T12:00:00+00:00")
    with pytest.raises(ValueError, match="status_rows"):
        replace(report, status_rows=list(report.status_rows))
    with pytest.raises(ValueError, match="duplicate_generated_at_count"):
        replace(report, duplicate_generated_at_count=99)
    with pytest.raises(ValueError, match="duplicate_fingerprint_ratio"):
        replace(report, duplicate_fingerprint_ratio=Decimal("0.0000"))


def test_batch_health_copies_supplied_reports():
    supplied = complete_history_fixture(index=1)
    report = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [supplied],
        config=relaxed_batch_health_config(),
        generated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )
    source_transition_summaries = report.source_transition_summaries
    status_rows = report.status_rows

    object.__setattr__(supplied.source_transitions[0], "transition_count", 999)
    object.__setattr__(supplied.status_rows[2], "comparison_count", 999)
    object.__setattr__(supplied.gate_results[0], "status", "unknown")

    assert report.source_transition_summaries == source_transition_summaries
    assert report.status_rows == status_rows


def test_batch_health_log_appends_jsonl_report(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_report(
        [complete_history_fixture(1), divergent_history_fixture(2)],
        config=relaxed_batch_health_config(),
        generated_at=datetime(2026, 9, 11, 22, 30, tzinfo=timezone(timedelta(hours=8))),
    )
    log = TradeProposalEvidenceComparisonHistoryBatchHealthLog(
        path=tmp_path / "nested" / "batch-health.jsonl",
    )

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0].startswith('{"boundary_statement"')
    stored = json.loads(lines[0])
    assert stored["report_only"] is True
    assert stored["generated_at"] == "2026-09-11T14:30:00+00:00"
    assert stored["divergent_history_ratio"] == "0.5000"
    assert stored["status_rows"][0]["history_ratio"] == "0.5000"
    assert stored["gate_results"][0]["observed_value"] == 2


def test_batch_health_log_validates_before_open(tmp_path):
    report = duplicate_batch_health_report_fixture()
    invalid = unsafe_batch_health_report(report, duplicate_generated_at_ratio=Decimal("NaN"))
    log = TradeProposalEvidenceComparisonHistoryBatchHealthLog(
        path=tmp_path / "batch-health.jsonl",
    )

    with pytest.raises(ValueError, match="finite|duplicate_generated_at_ratio"):
        log.append(invalid)

    assert not log.path.exists()

    existing_log = TradeProposalEvidenceComparisonHistoryBatchHealthLog(
        path=tmp_path / "existing.jsonl",
    )
    existing_log.path.write_text("existing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="finite|duplicate_generated_at_ratio"):
        existing_log.append(invalid)
    assert existing_log.path.read_text(encoding="utf-8") == "existing\n"

    with pytest.raises(
        ValueError,
        match="TradeProposalEvidenceComparisonHistoryBatchHealthReport",
    ):
        TradeProposalEvidenceComparisonHistoryBatchHealthLog(
            path=tmp_path / "bad-input.jsonl",
        ).append(object())
    assert not (tmp_path / "bad-input.jsonl").exists()
