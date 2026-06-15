import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tests.test_proposal_review_coverage import (
    approved_record,
    coverage_report,
    packet,
    rejected_record,
)
from polymarket_alpha_lab.proposal_review_diagnostics import (
    TradeProposalReviewDiagnosticConfig,
    build_trade_proposal_review_diagnostic_report,
)
from polymarket_alpha_lab.proposal_review_coverage import (
    TradeProposalReviewCoverageConfig,
)
from polymarket_alpha_lab.proposal_review_dossier import (
    TradeProposalReviewDossierConfig,
    TradeProposalReviewDossierFindingRow,
    TradeProposalReviewDossierLog,
    TradeProposalReviewDossierSourceRow,
    build_trade_proposal_review_dossier_report,
)
from polymarket_alpha_lab.proposal_review_quality import (
    TradeProposalReviewQualityConfig,
    build_trade_proposal_review_quality_report,
)
from polymarket_alpha_lab.proposal_review_summary import (
    TradeProposalReviewSummaryConfig,
    build_trade_proposal_review_summary_report,
)


def dossier_inputs(records, proposals):
    summary = build_trade_proposal_review_summary_report(
        records,
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 12, tzinfo=UTC),
    )
    quality = build_trade_proposal_review_quality_report(
        [summary],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_overall_rejection_ratio=Decimal("1.0000"),
            max_worst_summary_rejection_ratio=Decimal("1.0000"),
            max_reason_code_rejection_share=Decimal("1.0000"),
            max_duplicate_source_proposal_ratio=Decimal("1.0000"),
            max_duplicate_source_proposal_count=10,
        ),
        generated_at=datetime(2026, 9, 8, 13, tzinfo=UTC),
    )
    diagnostics = build_trade_proposal_review_diagnostic_report(
        records,
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("1.0000"),
            max_rejected_source_proposal_ratio=Decimal("1.0000"),
            max_reason_code_rejected_decision_share=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 14, tzinfo=UTC),
    )
    coverage = coverage_report(
        proposals,
        records,
        generated_at=datetime(2026, 9, 8, 15, tzinfo=UTC),
    )
    return summary, quality, diagnostics, coverage


def dossier_report(summary, quality, diagnostics, coverage, **overrides):
    values = {
        "summary": summary,
        "quality": quality,
        "diagnostics": diagnostics,
        "coverage": coverage,
        "config": TradeProposalReviewDossierConfig(config_version="dossier-v1"),
        "generated_at": datetime(2026, 9, 8, 16, tzinfo=UTC),
    }
    values.update(overrides)
    return build_trade_proposal_review_dossier_report(**values)


def test_build_trade_proposal_review_dossier_report_combines_supplied_reports():
    source = packet(1)
    records = [approved_record(source, minute=1)]
    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])

    report = dossier_report(summary, quality, diagnostics, coverage)

    assert report.generated_at == datetime(2026, 9, 8, 16, tzinfo=UTC)
    assert report.config_version == "dossier-v1"
    assert report.report_only is True
    assert report.review_record_count == 1
    assert report.proposal_packet_count == 1
    assert report.reviewed_proposal_packet_count == 1
    assert report.unreviewed_proposal_packet_count == 0
    assert report.orphan_review_record_count == 0
    assert report.duplicate_reviewed_proposal_packet_count == 0
    assert report.conflicting_decision_proposal_packet_count == 0
    assert report.approved_decision_count == 1
    assert report.rejected_decision_count == 0
    assert report.review_coverage_ratio == Decimal("1.0000")
    assert report.rejection_ratio == Decimal("0.0000")
    assert report.summary_status == "summary_ready"
    assert report.quality_status == "proposal_review_quality_ready"
    assert report.diagnostic_status == "diagnostics_ready"
    assert report.coverage_status == "proposal_review_coverage_ready"
    assert report.status == "proposal_review_dossier_complete"
    assert tuple(row.gate_name for row in report.gate_results) == (
        "count_consistency",
        "summary_evidence",
        "quality_evidence",
        "diagnostic_evidence",
        "coverage_evidence",
    )
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.report_name for row in report.source_rows) == (
        "coverage",
        "diagnostics",
        "quality",
        "summary",
    )
    gates = {row.gate_name: row for row in report.gate_results}
    assert gates["count_consistency"].message == (
        "Cross-report aggregate review counts are consistent."
    )
    assert gates["count_consistency"].observed_value == (
        "summary=1/1/0; quality=1/1/0; diagnostics=1/1/0; coverage=1/1/0; "
        "proposal_counts=1/1/1/1; "
        "summary_generated_at=2026-09-08T12:00:00+00:00; "
        "quality_last_summary_generated_at=2026-09-08T12:00:00+00:00"
    )
    assert gates["count_consistency"].threshold == (
        "summary/diagnostics/coverage counts match; "
        "quality counts match latest summary or contain historical totals"
    )
    assert gates["summary_evidence"].message == "Summary evidence is ready."
    assert gates["summary_evidence"].observed_value == "summary_ready"
    assert gates["summary_evidence"].threshold == "summary_ready"
    assert gates["quality_evidence"].message == "Quality evidence is ready."
    assert gates["quality_evidence"].observed_value == "proposal_review_quality_ready"
    assert gates["quality_evidence"].threshold == "proposal_review_quality_ready"
    assert gates["diagnostic_evidence"].message == "Diagnostic evidence is ready."
    assert gates["diagnostic_evidence"].observed_value == "diagnostics_ready"
    assert gates["diagnostic_evidence"].threshold == "diagnostics_ready"
    assert gates["coverage_evidence"].message == "Coverage evidence is ready."
    assert gates["coverage_evidence"].observed_value == "proposal_review_coverage_ready"
    assert gates["coverage_evidence"].threshold == "proposal_review_coverage_ready"

    source_rows = {row.report_name: row for row in report.source_rows}
    assert source_rows["summary"] == TradeProposalReviewDossierSourceRow(
        report_name="summary",
        report_status="summary_ready",
        generated_at=summary.generated_at,
        review_record_count=summary.review_record_count,
        proposal_packet_count=summary.unique_source_proposal_count,
        approved_decision_count=summary.approved_decision_count,
        rejected_decision_count=summary.rejected_decision_count,
        status_category="complete",
    )
    assert source_rows["quality"] == TradeProposalReviewDossierSourceRow(
        report_name="quality",
        report_status="proposal_review_quality_ready",
        generated_at=quality.generated_at,
        review_record_count=quality.total_review_record_count,
        proposal_packet_count=quality.summed_unique_source_proposal_count,
        approved_decision_count=quality.approved_decision_count,
        rejected_decision_count=quality.rejected_decision_count,
        status_category="complete",
    )
    assert source_rows["diagnostics"] == TradeProposalReviewDossierSourceRow(
        report_name="diagnostics",
        report_status="diagnostics_ready",
        generated_at=diagnostics.generated_at,
        review_record_count=diagnostics.review_record_count,
        proposal_packet_count=diagnostics.unique_source_proposal_count,
        approved_decision_count=diagnostics.approved_decision_count,
        rejected_decision_count=diagnostics.rejected_decision_count,
        status_category="complete",
    )
    assert source_rows["coverage"] == TradeProposalReviewDossierSourceRow(
        report_name="coverage",
        report_status="proposal_review_coverage_ready",
        generated_at=coverage.generated_at,
        review_record_count=coverage.review_record_count,
        proposal_packet_count=coverage.proposal_packet_count,
        approved_decision_count=coverage.approved_decision_count,
        rejected_decision_count=coverage.rejected_decision_count,
        status_category="complete",
    )
    assert report.finding_rows == ()


def test_trade_proposal_review_dossier_statuses_cover_incomplete_unstable_and_inconsistent_inputs():
    source = packet(2)
    records = [approved_record(source, minute=2)]
    summary, quality, diagnostics, _ = dossier_inputs(records, [source])

    empty_summary, empty_quality, empty_diagnostics, empty_coverage = dossier_inputs([], [])
    incomplete = dossier_report(
        empty_summary,
        empty_quality,
        empty_diagnostics,
        empty_coverage,
    )
    assert incomplete.status == "incomplete_review_dossier"
    assert any(row.status == "incomplete" for row in incomplete.gate_results)
    assert any(row.severity == "incomplete" for row in incomplete.finding_rows)

    rejected_source = packet(3)
    rejected_records = [rejected_record(rejected_source, minute=3)]
    unstable_summary = build_trade_proposal_review_summary_report(
        rejected_records,
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("0.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 17, tzinfo=UTC),
    )
    unstable_quality = build_trade_proposal_review_quality_report(
        [unstable_summary],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_overall_rejection_ratio=Decimal("1.0000"),
            max_worst_summary_rejection_ratio=Decimal("1.0000"),
            max_reason_code_rejection_share=Decimal("1.0000"),
            max_duplicate_source_proposal_ratio=Decimal("1.0000"),
            max_duplicate_source_proposal_count=10,
        ),
        generated_at=datetime(2026, 9, 8, 18, tzinfo=UTC),
    )
    unstable_diagnostics = build_trade_proposal_review_diagnostic_report(
        rejected_records,
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("1.0000"),
            max_rejected_source_proposal_ratio=Decimal("1.0000"),
            max_reason_code_rejected_decision_share=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 19, tzinfo=UTC),
    )
    unstable_coverage = coverage_report(
        [rejected_source],
        rejected_records,
        generated_at=datetime(2026, 9, 8, 20, tzinfo=UTC),
    )
    unstable = dossier_report(
        unstable_summary,
        unstable_quality,
        unstable_diagnostics,
        unstable_coverage,
    )
    assert unstable.status == "unstable_review_dossier"
    assert any(
        row.gate_name == "summary_evidence" and row.status == "fail"
        for row in unstable.gate_results
    )

    mismatch_source = packet(4)
    mismatched_coverage = coverage_report(
        [mismatch_source],
        [rejected_record(mismatch_source, minute=4)],
        generated_at=datetime(2026, 9, 8, 20, tzinfo=UTC),
    )
    inconsistent = dossier_report(summary, quality, diagnostics, mismatched_coverage)
    assert inconsistent.status == "inconsistent_review_dossier"
    inconsistent_gate = next(
        row for row in inconsistent.gate_results if row.gate_name == "count_consistency"
    )
    assert inconsistent_gate.status == "fail"
    assert inconsistent_gate.message == (
        "Cross-report aggregate review counts are inconsistent."
    )
    assert inconsistent.finding_rows == (
        TradeProposalReviewDossierFindingRow(
            finding_code="count_consistency_failed",
            severity="inconsistent",
            source_report_name="dossier",
            message="Cross-report aggregate review counts are inconsistent.",
            observed_value=inconsistent_gate.observed_value,
            threshold=inconsistent_gate.threshold,
        ),
    )

    duplicate_source = packet(41)
    duplicate_records = [
        approved_record(duplicate_source, minute=41),
        approved_record(duplicate_source, minute=42),
    ]
    duplicate_summary, duplicate_quality, duplicate_diagnostics, _ = dossier_inputs(
        duplicate_records,
        [duplicate_source],
    )
    inconsistent_coverage = coverage_report(
        [duplicate_source],
        duplicate_records,
        config=TradeProposalReviewCoverageConfig(
            config_version="coverage-v1",
            max_duplicate_reviewed_proposal_packet_count=0,
            max_conflicting_decision_proposal_packet_count=10,
            max_orphan_review_record_count=10,
        ),
        generated_at=datetime(2026, 9, 8, 20, tzinfo=UTC),
    )
    coverage_inconsistent = dossier_report(
        duplicate_summary,
        duplicate_quality,
        duplicate_diagnostics,
        inconsistent_coverage,
    )
    assert coverage_inconsistent.status == "inconsistent_review_dossier"
    coverage_gate = next(
        row
        for row in coverage_inconsistent.gate_results
        if row.gate_name == "coverage_evidence"
    )
    assert coverage_gate.status == "fail"
    assert coverage_gate.message == "Coverage evidence is inconsistent."
    assert coverage_inconsistent.finding_rows == (
        TradeProposalReviewDossierFindingRow(
            finding_code="coverage_evidence_inconsistent",
            severity="inconsistent",
            source_report_name="coverage",
            message="Coverage evidence is inconsistent.",
            observed_value="inconsistent_review_coverage",
            threshold="proposal_review_coverage_ready",
        ),
    )


def test_trade_proposal_review_dossier_accepts_historical_quality_when_latest_summary_is_covered():
    first_source = packet(9)
    second_source = packet(10)
    first_records = [approved_record(first_source, minute=9)]
    second_records = [approved_record(second_source, minute=10)]
    first_summary = build_trade_proposal_review_summary_report(
        first_records,
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 11, tzinfo=UTC),
    )
    latest_summary = build_trade_proposal_review_summary_report(
        second_records,
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 12, tzinfo=UTC),
    )
    latest_diagnostics = build_trade_proposal_review_diagnostic_report(
        second_records,
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("1.0000"),
            max_rejected_source_proposal_ratio=Decimal("1.0000"),
            max_reason_code_rejected_decision_share=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 14, tzinfo=UTC),
    )
    latest_coverage = coverage_report(
        [second_source],
        second_records,
        generated_at=datetime(2026, 9, 8, 15, tzinfo=UTC),
    )
    historical_quality = build_trade_proposal_review_quality_report(
        [first_summary, latest_summary],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_overall_rejection_ratio=Decimal("1.0000"),
            max_worst_summary_rejection_ratio=Decimal("1.0000"),
            max_reason_code_rejection_share=Decimal("1.0000"),
            max_duplicate_source_proposal_ratio=Decimal("1.0000"),
            max_duplicate_source_proposal_count=10,
        ),
        generated_at=datetime(2026, 9, 8, 21, tzinfo=UTC),
    )

    report = dossier_report(
        latest_summary,
        historical_quality,
        latest_diagnostics,
        latest_coverage,
    )

    assert report.status == "proposal_review_dossier_complete"
    assert report.review_record_count == latest_summary.review_record_count
    assert any(
        row.gate_name == "count_consistency" and row.status == "pass"
        for row in report.gate_results
    )

    stale_quality = replace(
        historical_quality,
        last_summary_generated_at=first_summary.generated_at,
    )
    stale = dossier_report(
        latest_summary,
        stale_quality,
        latest_diagnostics,
        latest_coverage,
    )
    assert stale.status == "inconsistent_review_dossier"
    assert any(
        row.gate_name == "count_consistency" and row.status == "fail"
        for row in stale.gate_results
    )

    rejected_older = build_trade_proposal_review_summary_report(
        [rejected_record(packet(11), minute=11)],
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 13, tzinfo=UTC),
    )
    rejected_latest = build_trade_proposal_review_summary_report(
        [rejected_record(packet(12), minute=12)],
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 14, tzinfo=UTC),
    )
    incompatible_quality = build_trade_proposal_review_quality_report(
        [rejected_older, rejected_latest],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_overall_rejection_ratio=Decimal("1.0000"),
            max_worst_summary_rejection_ratio=Decimal("1.0000"),
            max_reason_code_rejection_share=Decimal("1.0000"),
            max_duplicate_source_proposal_ratio=Decimal("1.0000"),
            max_duplicate_source_proposal_count=10,
        ),
        generated_at=datetime(2026, 9, 8, 22, tzinfo=UTC),
    )
    incompatible = dossier_report(
        latest_summary,
        incompatible_quality,
        latest_diagnostics,
        latest_coverage,
    )
    assert incompatible.status == "inconsistent_review_dossier"
    assert any(
        row.gate_name == "count_consistency" and row.status == "fail"
        for row in incompatible.gate_results
    )

    rejected_source = packet(13)
    rejected_latest_records = [rejected_record(rejected_source, minute=13)]
    rejected_latest_summary = build_trade_proposal_review_summary_report(
        rejected_latest_records,
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 23, tzinfo=UTC),
    )
    rejected_latest_diagnostics = build_trade_proposal_review_diagnostic_report(
        rejected_latest_records,
        config=TradeProposalReviewDiagnosticConfig(
            config_version="diagnostic-v1",
            max_rejected_decision_ratio=Decimal("1.0000"),
            max_rejected_source_proposal_ratio=Decimal("1.0000"),
            max_reason_code_rejected_decision_share=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 23, 10, tzinfo=UTC),
    )
    rejected_latest_coverage = coverage_report(
        [rejected_source],
        rejected_latest_records,
        generated_at=datetime(2026, 9, 8, 23, 20, tzinfo=UTC),
    )
    approved_at_rejected_time_summary = build_trade_proposal_review_summary_report(
        [approved_record(packet(14), minute=14)],
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 23, tzinfo=UTC),
    )
    approved_before_rejected_summary = build_trade_proposal_review_summary_report(
        [approved_record(packet(15), minute=15)],
        config=TradeProposalReviewSummaryConfig(
            config_version="summary-v1",
            max_rejection_ratio=Decimal("1.0000"),
        ),
        generated_at=datetime(2026, 9, 8, 22, tzinfo=UTC),
    )
    approved_only_historical_quality = build_trade_proposal_review_quality_report(
        [approved_before_rejected_summary, approved_at_rejected_time_summary],
        config=TradeProposalReviewQualityConfig(
            config_version="quality-v1",
            max_overall_rejection_ratio=Decimal("1.0000"),
            max_worst_summary_rejection_ratio=Decimal("1.0000"),
            max_reason_code_rejection_share=Decimal("1.0000"),
            max_duplicate_source_proposal_ratio=Decimal("1.0000"),
            max_duplicate_source_proposal_count=10,
        ),
        generated_at=datetime(2026, 9, 8, 23, 30, tzinfo=UTC),
    )
    rejected_mismatch = dossier_report(
        rejected_latest_summary,
        approved_only_historical_quality,
        rejected_latest_diagnostics,
        rejected_latest_coverage,
    )
    assert rejected_mismatch.status == "inconsistent_review_dossier"
    assert any(
        row.gate_name == "count_consistency" and row.status == "fail"
        for row in rejected_mismatch.gate_results
    )


def test_trade_proposal_review_dossier_accepts_independently_empty_quality_as_incomplete():
    empty_summary, _, empty_diagnostics, empty_coverage = dossier_inputs([], [])
    empty_quality = build_trade_proposal_review_quality_report(
        [],
        config=TradeProposalReviewQualityConfig(config_version="quality-v1"),
        generated_at=datetime(2026, 9, 8, 13, tzinfo=UTC),
    )

    report = dossier_report(
        empty_summary,
        empty_quality,
        empty_diagnostics,
        empty_coverage,
    )

    assert report.status == "incomplete_review_dossier"
    assert next(
        row for row in report.gate_results if row.gate_name == "count_consistency"
    ).status == "pass"
    assert next(
        row for row in report.gate_results if row.gate_name == "quality_evidence"
    ).status == "incomplete"


def test_trade_proposal_review_dossier_config_can_make_source_statuses_optional():
    empty_summary, empty_quality, empty_diagnostics, empty_coverage = dossier_inputs([], [])

    report = dossier_report(
        empty_summary,
        empty_quality,
        empty_diagnostics,
        empty_coverage,
        config=TradeProposalReviewDossierConfig(
            config_version="dossier-v1",
            require_summary_ready=False,
            require_quality_ready=False,
            require_diagnostics_ready=False,
            require_coverage_ready=False,
        ),
    )

    assert report.status == "proposal_review_dossier_complete"
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.message for row in report.gate_results[1:]) == (
        "Summary evidence is optional.",
        "Quality evidence is optional.",
        "Diagnostic evidence is optional.",
        "Coverage evidence is optional.",
    )
    assert tuple(row.threshold for row in report.gate_results[1:]) == (
        "not_required",
        "not_required",
        "not_required",
        "not_required",
    )
    assert tuple(row.status_category for row in report.source_rows) == (
        "incomplete",
        "incomplete",
        "incomplete",
        "incomplete",
    )


def test_trade_proposal_review_dossier_rejects_bad_inputs_and_revalidates_mutated_reports():
    source = packet(5)
    records = [approved_record(source, minute=5)]
    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])

    with pytest.raises(ValueError, match="summary"):
        dossier_report(object(), quality, diagnostics, coverage)
    with pytest.raises(ValueError, match="quality"):
        dossier_report(summary, object(), diagnostics, coverage)
    with pytest.raises(ValueError, match="diagnostics"):
        dossier_report(summary, quality, object(), coverage)
    with pytest.raises(ValueError, match="coverage"):
        dossier_report(summary, quality, diagnostics, object())
    with pytest.raises(ValueError, match="config"):
        dossier_report(summary, quality, diagnostics, coverage, config=object())
    with pytest.raises(ValueError, match="generated_at"):
        dossier_report(
            summary,
            quality,
            diagnostics,
            coverage,
            generated_at="2026-09-08",
        )

    object.__setattr__(coverage, "review_coverage_ratio", Decimal("NaN"))
    with pytest.raises(ValueError, match="finite|review_coverage_ratio"):
        dossier_report(summary, quality, diagnostics, coverage)

    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])
    object.__setattr__(coverage.gate_results[0], "status", "maybe")
    with pytest.raises(ValueError, match="status"):
        dossier_report(summary, quality, diagnostics, coverage)

    with pytest.raises(ValueError, match="require_summary_ready"):
        TradeProposalReviewDossierConfig(
            config_version="dossier-v1",
            require_summary_ready=1,
        )


def test_trade_proposal_review_dossier_dataclasses_are_frozen_and_validate_invariants():
    source = packet(6)
    records = [approved_record(source, minute=6)]
    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])
    report = dossier_report(summary, quality, diagnostics, coverage)
    config = TradeProposalReviewDossierConfig(config_version="dossier-v1")
    gate_row = report.gate_results[0]
    source_row = report.source_rows[0]

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(FrozenInstanceError):
        report.status = "other"
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(config, boundary_statement="dossier")
    alternate_boundary = (
        "This is a report only proposal review dossier artifact, not an approval "
        "workflow, trade instruction, order instruction, broker request, order "
        "request, account action, account authentication, private key handling, "
        "wallet signature, live execution signal, credential workflow, manual "
        "execution import, strategy promotion signal, settlement review, "
        "reconciliation process, compliance review, geographic access analysis, "
        "investment ranking, trade recommendation, or automatic order placement "
        "authorization."
    )
    assert replace(config, boundary_statement=alternate_boundary).boundary_statement == (
        alternate_boundary
    )
    contradictory_boundary = (
        "This is a report-only proposal-review dossier artifact, not an approval "
        "workflow, and it is a trade instruction, order instruction, broker "
        "request, order request, account action, account authentication, "
        "private-key handling, wallet signature, live-execution signal, "
        "credential workflow, manual execution import, strategy-promotion "
        "signal, settlement review, reconciliation process, compliance review, "
        "geographic access analysis, investment ranking, trade recommendation, "
        "or automatic order-placement authorization."
    )
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(config, boundary_statement=contradictory_boundary)
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(
            config,
            boundary_statement=(
                f"{alternate_boundary} This is a trade instruction."
            ),
        )
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(
            config,
            boundary_statement=(
                f"{alternate_boundary} It is private-key handling."
            ),
        )
    with pytest.raises(ValueError, match="gate_name"):
        replace(gate_row, gate_name="approval")
    with pytest.raises(ValueError, match="source_rows"):
        replace(report, source_rows=tuple(reversed(report.source_rows)))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="incomplete_review_dossier")
    with pytest.raises(ValueError, match="report_name"):
        replace(source_row, report_name="approval")


def test_trade_proposal_review_dossier_report_rejects_drifted_source_row_counts():
    source = packet(16)
    records = [approved_record(source, minute=16)]
    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])
    report = dossier_report(summary, quality, diagnostics, coverage)
    coverage_index = next(
        index
        for index, row in enumerate(report.source_rows)
        if row.report_name == "coverage"
    )

    for drifted_row in (
        replace(
            report.source_rows[coverage_index],
            review_record_count=2,
            approved_decision_count=2,
            rejected_decision_count=0,
        ),
        replace(
            report.source_rows[coverage_index],
            review_record_count=2,
            approved_decision_count=1,
            rejected_decision_count=1,
        ),
    ):
        source_rows = list(report.source_rows)
        source_rows[coverage_index] = drifted_row
        with pytest.raises(ValueError, match="source_rows coverage counts"):
            replace(report, source_rows=tuple(source_rows))

    for source_name in ("coverage", "diagnostics", "quality", "summary"):
        source_index = next(
            index
            for index, row in enumerate(report.source_rows)
            if row.report_name == source_name
        )
        if source_name != "coverage":
            with pytest.raises(ValueError, match="proposal_packet_count"):
                replace(
                    report.source_rows[source_index],
                    proposal_packet_count=999,
                )
            continue
        source_rows = list(report.source_rows)
        source_rows[source_index] = replace(
            report.source_rows[source_index],
            proposal_packet_count=999,
        )
        with pytest.raises(ValueError, match=f"source_rows {source_name} proposal count"):
            replace(report, source_rows=tuple(source_rows))

    gate_results = list(report.gate_results)
    gate_results[0] = replace(
        gate_results[0],
        observed_value=(
            "summary=1/1/0; quality=999/999/0; "
            "diagnostics=999/999/0; coverage=999/999/0; "
            "proposal_counts=1/1/1/1; "
            "summary_generated_at=2026-09-08T12:00:00+00:00; "
            "quality_last_summary_generated_at=2026-09-08T12:00:00+00:00"
        ),
    )
    source_rows = []
    for row in report.source_rows:
        if row.report_name == "summary":
            source_rows.append(row)
        else:
            source_rows.append(
                replace(
                    row,
                    review_record_count=999,
                    approved_decision_count=999,
                    rejected_decision_count=0,
                ),
            )
    with pytest.raises(ValueError, match="count_consistency status"):
        replace(
            report,
            gate_results=tuple(gate_results),
            source_rows=tuple(source_rows),
        )

    gate_results = list(report.gate_results)
    gate_results[0] = replace(
        gate_results[0],
        observed_value=(
            f"{gate_results[0].observed_value}; summary=999/999/0"
        ),
    )
    with pytest.raises(ValueError, match="count_consistency observed_value"):
        replace(report, gate_results=tuple(gate_results))


def test_trade_proposal_review_dossier_log_appends_jsonl_report(tmp_path):
    source = packet(7)
    records = [approved_record(source, minute=7)]
    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])
    report = dossier_report(summary, quality, diagnostics, coverage)
    log = TradeProposalReviewDossierLog(path=tmp_path / "proposal-review-dossier.jsonl")

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    stored = json.loads(lines[0])
    assert len(lines) == 2
    assert json.loads(lines[1])["status"] == "proposal_review_dossier_complete"
    assert stored["generated_at"] == "2026-09-08T16:00:00+00:00"
    assert stored["report_only"] is True
    assert stored["status"] == "proposal_review_dossier_complete"
    assert stored["review_coverage_ratio"] == "1.0000"
    assert stored["gate_results"][0]["message"] == (
        "Cross-report aggregate review counts are consistent."
    )
    assert stored["gate_results"][0]["observed_value"] == (
        "summary=1/1/0; quality=1/1/0; diagnostics=1/1/0; coverage=1/1/0; "
        "proposal_counts=1/1/1/1; "
        "summary_generated_at=2026-09-08T12:00:00+00:00; "
        "quality_last_summary_generated_at=2026-09-08T12:00:00+00:00"
    )
    assert [row["report_name"] for row in stored["source_rows"]] == [
        "coverage",
        "diagnostics",
        "quality",
        "summary",
    ]


def test_trade_proposal_review_dossier_log_validates_before_open(tmp_path):
    source = packet(8)
    records = [approved_record(source, minute=8)]
    summary, quality, diagnostics, coverage = dossier_inputs(records, [source])
    report = dossier_report(summary, quality, diagnostics, coverage)
    object.__setattr__(report, "review_coverage_ratio", Decimal("NaN"))
    log = TradeProposalReviewDossierLog(path=tmp_path / "proposal-review-dossier.jsonl")

    with pytest.raises(ValueError, match="finite|review_coverage_ratio"):
        log.append(report)

    assert not log.path.exists()
