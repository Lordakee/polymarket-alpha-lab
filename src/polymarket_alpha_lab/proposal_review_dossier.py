"""Report-only proposal-review dossier artifacts for Level 2."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.proposal_review_coverage import (
    TradeProposalReviewCoverageBucketRow,
    TradeProposalReviewCoverageGateResult,
    TradeProposalReviewCoveragePacketRow,
    TradeProposalReviewCoverageReport,
)
from polymarket_alpha_lab.proposal_review_diagnostics import (
    TradeProposalReviewDiagnosticBucketRow,
    TradeProposalReviewDiagnosticReasonRow,
    TradeProposalReviewDiagnosticReport,
    TradeProposalReviewDiagnosticSourceRow,
)
from polymarket_alpha_lab.proposal_review_quality import (
    TradeProposalReviewQualityGateResult,
    TradeProposalReviewQualityReasonTrend,
    TradeProposalReviewQualityReport,
)
from polymarket_alpha_lab.proposal_review_summary import (
    TradeProposalReviewBucketSummary,
    TradeProposalReviewReasonCodeSummary,
    TradeProposalReviewSummaryReport,
)


__all__ = (
    "TradeProposalReviewDossierConfig",
    "TradeProposalReviewDossierFindingRow",
    "TradeProposalReviewDossierGateResult",
    "TradeProposalReviewDossierLog",
    "TradeProposalReviewDossierReport",
    "TradeProposalReviewDossierSourceRow",
    "build_trade_proposal_review_dossier_report",
)


DEFAULT_REVIEW_DOSSIER_BOUNDARY_STATEMENT = (
    "This is a report-only proposal-review dossier artifact, not an approval "
    "workflow, trade instruction, order instruction, broker request, order "
    "request, account action, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflow, manual "
    "execution import, strategy-promotion signal, settlement review, "
    "reconciliation process, compliance review, geographic access analysis, "
    "investment ranking, trade recommendation, or automatic order-placement "
    "authorization."
)
RATIO_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")
GATE_NAMES = (
    "count_consistency",
    "summary_evidence",
    "quality_evidence",
    "diagnostic_evidence",
    "coverage_evidence",
)
GATE_STATUSES = ("pass", "fail", "incomplete")
REPORT_STATUSES = (
    "incomplete_review_dossier",
    "inconsistent_review_dossier",
    "unstable_review_dossier",
    "proposal_review_dossier_complete",
)
SOURCE_REPORT_NAMES = ("coverage", "diagnostics", "quality", "summary")
STATUS_CATEGORIES = ("complete", "incomplete", "inconsistent", "unstable")
STATUS_CATEGORY_BY_STATUS = {
    "summary_ready": "complete",
    "proposal_review_quality_ready": "complete",
    "diagnostics_ready": "complete",
    "proposal_review_coverage_ready": "complete",
    "insufficient_review_sample": "incomplete",
    "incomplete_review_data": "incomplete",
    "incomplete_proposal_sample": "incomplete",
    "incomplete_review_coverage": "incomplete",
    "inconsistent_review_coverage": "inconsistent",
    "high_rejection_ratio": "unstable",
    "unstable_review_quality": "unstable",
    "high_rejection_proxy": "unstable",
}


@dataclass(frozen=True)
class TradeProposalReviewDossierConfig:
    config_version: str
    require_summary_ready: bool = True
    require_quality_ready: bool = True
    require_diagnostics_ready: bool = True
    require_coverage_ready: bool = True
    boundary_statement: str = DEFAULT_REVIEW_DOSSIER_BOUNDARY_STATEMENT

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_bool("require_summary_ready", self.require_summary_ready)
        _require_bool("require_quality_ready", self.require_quality_ready)
        _require_bool("require_diagnostics_ready", self.require_diagnostics_ready)
        _require_bool("require_coverage_ready", self.require_coverage_ready)
        _require_boundary_statement(self.boundary_statement)


@dataclass(frozen=True)
class TradeProposalReviewDossierGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known proposal review dossier gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known proposal review dossier gate status")
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class TradeProposalReviewDossierSourceRow:
    report_name: str
    report_status: str
    generated_at: datetime
    review_record_count: int | None
    proposal_packet_count: int | None
    approved_decision_count: int | None
    rejected_decision_count: int | None
    status_category: str

    def __post_init__(self) -> None:
        if self.report_name not in SOURCE_REPORT_NAMES:
            raise ValueError("report_name must be a known proposal review dossier source")
        _require_canonical_string("report_status", self.report_status)
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        for field_name in (
            "review_record_count",
            "proposal_packet_count",
            "approved_decision_count",
            "rejected_decision_count",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _require_nonnegative_int(field_name, value)
        if (
            self.review_record_count is not None
            and self.approved_decision_count is not None
            and self.rejected_decision_count is not None
            and self.review_record_count
            != self.approved_decision_count + self.rejected_decision_count
        ):
            raise ValueError(
                "review_record_count must equal approved and rejected decision counts"
            )
        if (
            self.report_name in ("diagnostics", "quality", "summary")
            and self.review_record_count is not None
            and self.proposal_packet_count is not None
            and self.proposal_packet_count > self.review_record_count
        ):
            raise ValueError(
                "proposal_packet_count must not exceed review_record_count"
            )
        if self.status_category not in STATUS_CATEGORIES:
            raise ValueError("status_category must be a known dossier source category")
        expected_category = _status_category(self.report_status)
        if self.status_category != expected_category:
            raise ValueError("status_category must match report_status")


@dataclass(frozen=True)
class TradeProposalReviewDossierFindingRow:
    finding_code: str
    severity: str
    source_report_name: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        _require_canonical_string("finding_code", self.finding_code)
        if self.severity not in ("incomplete", "inconsistent", "unstable"):
            raise ValueError("severity must be incomplete, inconsistent, or unstable")
        if self.source_report_name not in (*SOURCE_REPORT_NAMES, "dossier"):
            raise ValueError("source_report_name must be a known dossier finding source")
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class TradeProposalReviewDossierReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    summary_generated_at: datetime
    quality_generated_at: datetime
    diagnostic_generated_at: datetime
    coverage_generated_at: datetime
    review_record_count: int
    proposal_packet_count: int
    reviewed_proposal_packet_count: int
    unreviewed_proposal_packet_count: int
    orphan_review_record_count: int
    duplicate_reviewed_proposal_packet_count: int
    conflicting_decision_proposal_packet_count: int
    approved_decision_count: int
    rejected_decision_count: int
    review_coverage_ratio: Decimal | None
    rejection_ratio: Decimal | None
    summary_status: str
    quality_status: str
    diagnostic_status: str
    coverage_status: str
    status: str
    gate_results: tuple[TradeProposalReviewDossierGateResult, ...]
    source_rows: tuple[TradeProposalReviewDossierSourceRow, ...]
    finding_rows: tuple[TradeProposalReviewDossierFindingRow, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "generated_at",
            "summary_generated_at",
            "quality_generated_at",
            "diagnostic_generated_at",
            "coverage_generated_at",
        ):
            object.__setattr__(self, field_name, _as_utc(getattr(self, field_name)))
        _require_canonical_string("config_version", self.config_version)
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        _require_boundary_statement(self.boundary_statement)
        for field_name in (
            "review_record_count",
            "proposal_packet_count",
            "reviewed_proposal_packet_count",
            "unreviewed_proposal_packet_count",
            "orphan_review_record_count",
            "duplicate_reviewed_proposal_packet_count",
            "conflicting_decision_proposal_packet_count",
            "approved_decision_count",
            "rejected_decision_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.review_record_count != (
            self.approved_decision_count + self.rejected_decision_count
        ):
            raise ValueError(
                "review_record_count must equal approved and rejected decision counts"
            )
        if self.proposal_packet_count != (
            self.reviewed_proposal_packet_count + self.unreviewed_proposal_packet_count
        ):
            raise ValueError("proposal_packet_count must equal coverage packet counts")
        if self.duplicate_reviewed_proposal_packet_count > self.proposal_packet_count:
            raise ValueError(
                "duplicate_reviewed_proposal_packet_count must not exceed proposal_packet_count"
            )
        if self.conflicting_decision_proposal_packet_count > self.proposal_packet_count:
            raise ValueError(
                "conflicting_decision_proposal_packet_count must not exceed proposal_packet_count"
            )
        _require_optional_probability_decimal(
            "review_coverage_ratio",
            self.review_coverage_ratio,
        )
        _require_optional_probability_decimal("rejection_ratio", self.rejection_ratio)
        expected_rejection = _optional_ratio_from_counts(
            self.rejected_decision_count,
            self.review_record_count,
        )
        if self.rejection_ratio != expected_rejection:
            raise ValueError("rejection_ratio must match rejected decision count")
        expected_coverage = _optional_ratio_from_counts(
            self.reviewed_proposal_packet_count,
            self.proposal_packet_count,
        )
        if self.review_coverage_ratio != expected_coverage:
            raise ValueError("review_coverage_ratio must match reviewed proposals")
        for field_name in (
            "summary_status",
            "quality_status",
            "diagnostic_status",
            "coverage_status",
        ):
            _status_category(getattr(self, field_name))
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known proposal review dossier status")
        object.__setattr__(
            self,
            "gate_results",
            _normalize_typed_tuple(
                "gate_results",
                self.gate_results,
                TradeProposalReviewDossierGateResult,
            ),
        )
        object.__setattr__(
            self,
            "source_rows",
            _normalize_typed_tuple(
                "source_rows",
                self.source_rows,
                TradeProposalReviewDossierSourceRow,
            ),
        )
        object.__setattr__(
            self,
            "finding_rows",
            _normalize_typed_tuple(
                "finding_rows",
                self.finding_rows,
                TradeProposalReviewDossierFindingRow,
            ),
        )
        if tuple(row.gate_name for row in self.gate_results) != GATE_NAMES:
            raise ValueError("gate_results must contain proposal review dossier gates")
        _validate_source_rows_match_report(self)
        _validate_count_consistency_gate_matches_evidence(self)
        expected_findings = _expected_finding_rows(self.gate_results)
        if self.finding_rows != expected_findings:
            raise ValueError("finding_rows must match non-pass gate results")
        if self.status != _dossier_status(self.gate_results):
            raise ValueError("status must match proposal review dossier gate results")


@dataclass(frozen=True)
class TradeProposalReviewDossierLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: TradeProposalReviewDossierReport) -> None:
        if type(report) is not TradeProposalReviewDossierReport:
            raise ValueError("report must be a TradeProposalReviewDossierReport")
        validated = _validate_report_tree(report)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_trade_proposal_review_dossier_report(
    *,
    summary: TradeProposalReviewSummaryReport,
    quality: TradeProposalReviewQualityReport,
    diagnostics: TradeProposalReviewDiagnosticReport,
    coverage: TradeProposalReviewCoverageReport,
    config: TradeProposalReviewDossierConfig,
    generated_at: datetime,
) -> TradeProposalReviewDossierReport:
    if type(config) is not TradeProposalReviewDossierConfig:
        raise ValueError("config must be a TradeProposalReviewDossierConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    summary = _clone_summary_report(summary)
    quality = _clone_quality_report(quality)
    diagnostics = _clone_diagnostic_report(diagnostics)
    coverage = _clone_coverage_report(coverage)
    gate_results = _build_gate_results(
        summary=summary,
        quality=quality,
        diagnostics=diagnostics,
        coverage=coverage,
        config=config,
    )
    return TradeProposalReviewDossierReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_only=True,
        boundary_statement=config.boundary_statement,
        summary_generated_at=summary.generated_at,
        quality_generated_at=quality.generated_at,
        diagnostic_generated_at=diagnostics.generated_at,
        coverage_generated_at=coverage.generated_at,
        review_record_count=summary.review_record_count,
        proposal_packet_count=coverage.proposal_packet_count,
        reviewed_proposal_packet_count=coverage.reviewed_proposal_packet_count,
        unreviewed_proposal_packet_count=coverage.unreviewed_proposal_packet_count,
        orphan_review_record_count=coverage.orphan_review_record_count,
        duplicate_reviewed_proposal_packet_count=(
            coverage.duplicate_reviewed_proposal_packet_count
        ),
        conflicting_decision_proposal_packet_count=(
            coverage.conflicting_decision_proposal_packet_count
        ),
        approved_decision_count=summary.approved_decision_count,
        rejected_decision_count=summary.rejected_decision_count,
        review_coverage_ratio=coverage.review_coverage_ratio,
        rejection_ratio=summary.rejection_ratio,
        summary_status=summary.status,
        quality_status=quality.status,
        diagnostic_status=diagnostics.status,
        coverage_status=coverage.status,
        status=_dossier_status(gate_results),
        gate_results=gate_results,
        source_rows=_expected_source_rows(summary, quality, diagnostics, coverage),
        finding_rows=_expected_finding_rows(gate_results),
    )


def _build_gate_results(
    *,
    summary: TradeProposalReviewSummaryReport,
    quality: TradeProposalReviewQualityReport,
    diagnostics: TradeProposalReviewDiagnosticReport,
    coverage: TradeProposalReviewCoverageReport,
    config: TradeProposalReviewDossierConfig,
) -> tuple[TradeProposalReviewDossierGateResult, ...]:
    return (
        _count_consistency_gate(summary, quality, diagnostics, coverage),
        _source_gate(
            gate_name="summary_evidence",
            ready_required=config.require_summary_ready,
            observed_status=summary.status,
            ready_status="summary_ready",
            incomplete_statuses=("insufficient_review_sample",),
            incomplete_message="Summary evidence is incomplete.",
            fail_message="Summary evidence is unstable.",
            ready_message="Summary evidence is ready.",
            optional_message="Summary evidence is optional.",
        ),
        _source_gate(
            gate_name="quality_evidence",
            ready_required=config.require_quality_ready,
            observed_status=quality.status,
            ready_status="proposal_review_quality_ready",
            incomplete_statuses=("incomplete_review_data", "insufficient_review_sample"),
            incomplete_message="Quality evidence is incomplete.",
            fail_message="Quality evidence is unstable.",
            ready_message="Quality evidence is ready.",
            optional_message="Quality evidence is optional.",
        ),
        _source_gate(
            gate_name="diagnostic_evidence",
            ready_required=config.require_diagnostics_ready,
            observed_status=diagnostics.status,
            ready_status="diagnostics_ready",
            incomplete_statuses=("incomplete_review_data", "insufficient_review_sample"),
            incomplete_message="Diagnostic evidence is incomplete.",
            fail_message="Diagnostic evidence is unstable.",
            ready_message="Diagnostic evidence is ready.",
            optional_message="Diagnostic evidence is optional.",
        ),
        _source_gate(
            gate_name="coverage_evidence",
            ready_required=config.require_coverage_ready,
            observed_status=coverage.status,
            ready_status="proposal_review_coverage_ready",
            incomplete_statuses=(
                "incomplete_proposal_sample",
                "incomplete_review_coverage",
            ),
            incomplete_message="Coverage evidence is incomplete.",
            fail_message="Coverage evidence is inconsistent.",
            ready_message="Coverage evidence is ready.",
            optional_message="Coverage evidence is optional.",
        ),
    )


def _count_consistency_gate(
    summary: TradeProposalReviewSummaryReport,
    quality: TradeProposalReviewQualityReport,
    diagnostics: TradeProposalReviewDiagnosticReport,
    coverage: TradeProposalReviewCoverageReport,
) -> TradeProposalReviewDossierGateResult:
    passes = _aggregate_counts_are_consistent(summary, quality, diagnostics, coverage)
    return TradeProposalReviewDossierGateResult(
        gate_name="count_consistency",
        status="pass" if passes else "fail",
        message=(
            "Cross-report aggregate review counts are consistent."
            if passes
            else "Cross-report aggregate review counts are inconsistent."
        ),
        observed_value=_count_consistency_observed_value(
            summary,
            quality,
            diagnostics,
            coverage,
        ),
        threshold=(
            "summary/diagnostics/coverage counts match; "
            "quality counts match latest summary or contain historical totals"
        ),
    )


def _source_gate(
    *,
    gate_name: str,
    ready_required: bool,
    observed_status: str,
    ready_status: str,
    incomplete_statuses: tuple[str, ...],
    incomplete_message: str,
    fail_message: str,
    ready_message: str,
    optional_message: str,
) -> TradeProposalReviewDossierGateResult:
    if not ready_required:
        return TradeProposalReviewDossierGateResult(
            gate_name=gate_name,
            status="pass",
            message=optional_message,
            observed_value=observed_status,
            threshold="not_required",
        )
    if observed_status == ready_status:
        return TradeProposalReviewDossierGateResult(
            gate_name=gate_name,
            status="pass",
            message=ready_message,
            observed_value=observed_status,
            threshold=ready_status,
        )
    if observed_status in incomplete_statuses:
        return TradeProposalReviewDossierGateResult(
            gate_name=gate_name,
            status="incomplete",
            message=incomplete_message,
            observed_value=observed_status,
            threshold=ready_status,
        )
    _status_category(observed_status)
    return TradeProposalReviewDossierGateResult(
        gate_name=gate_name,
        status="fail",
        message=fail_message,
        observed_value=observed_status,
        threshold=ready_status,
    )


def _aggregate_counts_are_consistent(
    summary: TradeProposalReviewSummaryReport,
    quality: TradeProposalReviewQualityReport,
    diagnostics: TradeProposalReviewDiagnosticReport,
    coverage: TradeProposalReviewCoverageReport,
) -> bool:
    shared_counts_match = (
        summary.review_record_count == diagnostics.review_record_count
        and summary.review_record_count == coverage.review_record_count
        and summary.approved_decision_count == diagnostics.approved_decision_count
        and summary.approved_decision_count == coverage.approved_decision_count
        and summary.rejected_decision_count == diagnostics.rejected_decision_count
        and summary.rejected_decision_count == coverage.rejected_decision_count
    )
    if not shared_counts_match:
        return False
    if quality.summary_report_count == 0:
        return (
            summary.review_record_count == 0
            and summary.approved_decision_count == 0
            and summary.rejected_decision_count == 0
            and quality.total_review_record_count == 0
            and quality.approved_decision_count == 0
            and quality.rejected_decision_count == 0
            and quality.first_summary_generated_at is None
            and quality.last_summary_generated_at is None
        )
    if quality.summary_report_count == 1:
        return (
            quality.total_review_record_count == summary.review_record_count
            and quality.approved_decision_count == summary.approved_decision_count
            and quality.rejected_decision_count == summary.rejected_decision_count
            and quality.first_summary_generated_at == summary.generated_at
            and quality.last_summary_generated_at == summary.generated_at
        )
    return (
        quality.total_review_record_count >= summary.review_record_count
        and quality.approved_decision_count >= summary.approved_decision_count
        and quality.rejected_decision_count >= summary.rejected_decision_count
        and quality.first_summary_generated_at is not None
        and quality.last_summary_generated_at is not None
        and quality.first_summary_generated_at < quality.last_summary_generated_at
        and quality.last_summary_generated_at == summary.generated_at
    )


def _count_consistency_observed_value(
    summary: TradeProposalReviewSummaryReport,
    quality: TradeProposalReviewQualityReport,
    diagnostics: TradeProposalReviewDiagnosticReport,
    coverage: TradeProposalReviewCoverageReport,
) -> str:
    latest_at = (
        "None"
        if quality.last_summary_generated_at is None
        else _as_utc(quality.last_summary_generated_at).isoformat()
    )
    return (
        f"summary={summary.review_record_count}/"
        f"{summary.approved_decision_count}/{summary.rejected_decision_count}; "
        f"quality={quality.total_review_record_count}/"
        f"{quality.approved_decision_count}/{quality.rejected_decision_count}; "
        f"diagnostics={diagnostics.review_record_count}/"
        f"{diagnostics.approved_decision_count}/{diagnostics.rejected_decision_count}; "
        f"coverage={coverage.review_record_count}/"
        f"{coverage.approved_decision_count}/{coverage.rejected_decision_count}; "
        f"proposal_counts={summary.unique_source_proposal_count}/"
        f"{quality.summed_unique_source_proposal_count}/"
        f"{diagnostics.unique_source_proposal_count}/"
        f"{coverage.proposal_packet_count}; "
        f"summary_generated_at={_as_utc(summary.generated_at).isoformat()}; "
        f"quality_last_summary_generated_at={latest_at}"
    )


def _dossier_status(
    gate_results: tuple[TradeProposalReviewDossierGateResult, ...],
) -> str:
    gates = {row.gate_name: row.status for row in gate_results}
    if (
        gates["count_consistency"] == "fail"
        or gates["coverage_evidence"] == "fail"
    ):
        return "inconsistent_review_dossier"
    if any(row.status == "incomplete" for row in gate_results):
        return "incomplete_review_dossier"
    if any(row.status == "fail" for row in gate_results):
        return "unstable_review_dossier"
    return "proposal_review_dossier_complete"


def _expected_source_rows(
    summary: TradeProposalReviewSummaryReport,
    quality: TradeProposalReviewQualityReport,
    diagnostics: TradeProposalReviewDiagnosticReport,
    coverage: TradeProposalReviewCoverageReport,
) -> tuple[TradeProposalReviewDossierSourceRow, ...]:
    return tuple(
        sorted(
            (
                TradeProposalReviewDossierSourceRow(
                    report_name="coverage",
                    report_status=coverage.status,
                    generated_at=coverage.generated_at,
                    review_record_count=coverage.review_record_count,
                    proposal_packet_count=coverage.proposal_packet_count,
                    approved_decision_count=coverage.approved_decision_count,
                    rejected_decision_count=coverage.rejected_decision_count,
                    status_category=_status_category(coverage.status),
                ),
                TradeProposalReviewDossierSourceRow(
                    report_name="diagnostics",
                    report_status=diagnostics.status,
                    generated_at=diagnostics.generated_at,
                    review_record_count=diagnostics.review_record_count,
                    proposal_packet_count=diagnostics.unique_source_proposal_count,
                    approved_decision_count=diagnostics.approved_decision_count,
                    rejected_decision_count=diagnostics.rejected_decision_count,
                    status_category=_status_category(diagnostics.status),
                ),
                TradeProposalReviewDossierSourceRow(
                    report_name="quality",
                    report_status=quality.status,
                    generated_at=quality.generated_at,
                    review_record_count=quality.total_review_record_count,
                    proposal_packet_count=quality.summed_unique_source_proposal_count,
                    approved_decision_count=quality.approved_decision_count,
                    rejected_decision_count=quality.rejected_decision_count,
                    status_category=_status_category(quality.status),
                ),
                TradeProposalReviewDossierSourceRow(
                    report_name="summary",
                    report_status=summary.status,
                    generated_at=summary.generated_at,
                    review_record_count=summary.review_record_count,
                    proposal_packet_count=summary.unique_source_proposal_count,
                    approved_decision_count=summary.approved_decision_count,
                    rejected_decision_count=summary.rejected_decision_count,
                    status_category=_status_category(summary.status),
                ),
            ),
            key=lambda row: row.report_name,
        )
    )


def _validate_source_rows_match_report(
    report: TradeProposalReviewDossierReport,
) -> None:
    if tuple(row.report_name for row in report.source_rows) != SOURCE_REPORT_NAMES:
        raise ValueError("source_rows must contain the four dossier source reports")
    rows = {row.report_name: row for row in report.source_rows}
    if len(rows) != len(report.source_rows):
        raise ValueError("source_rows must not contain duplicate report names")
    expected_statuses = {
        "coverage": report.coverage_status,
        "diagnostics": report.diagnostic_status,
        "quality": report.quality_status,
        "summary": report.summary_status,
    }
    expected_times = {
        "coverage": report.coverage_generated_at,
        "diagnostics": report.diagnostic_generated_at,
        "quality": report.quality_generated_at,
        "summary": report.summary_generated_at,
    }
    for name, row in rows.items():
        if row.report_status != expected_statuses[name]:
            raise ValueError("source_rows report_status must match report statuses")
        if row.generated_at != expected_times[name]:
            raise ValueError("source_rows generated_at must match report timestamps")
        if row.status_category != _status_category(row.report_status):
            raise ValueError("source_rows status_category must match report_status")
    summary_row = rows["summary"]
    if (
        summary_row.review_record_count != report.review_record_count
        or summary_row.approved_decision_count != report.approved_decision_count
        or summary_row.rejected_decision_count != report.rejected_decision_count
    ):
        raise ValueError("source_rows summary counts must match report counts")
    coverage_row = rows["coverage"]
    if coverage_row.proposal_packet_count != report.proposal_packet_count:
        raise ValueError("source_rows coverage proposal count must match report count")
    expected_source_counts = _source_counts_from_count_consistency_gate(report)
    expected_source_proposal_counts = _source_proposal_counts_from_count_consistency_gate(
        report,
    )
    for source_name, row in rows.items():
        expected_counts = expected_source_counts[source_name]
        if (
            row.review_record_count != expected_counts[0]
            or row.approved_decision_count != expected_counts[1]
            or row.rejected_decision_count != expected_counts[2]
        ):
            raise ValueError(
                f"source_rows {source_name} counts must match count_consistency evidence"
            )
        if row.proposal_packet_count != expected_source_proposal_counts[source_name]:
            raise ValueError(
                f"source_rows {source_name} proposal count must match count_consistency evidence"
            )


def _validate_count_consistency_gate_matches_evidence(
    report: TradeProposalReviewDossierReport,
) -> None:
    gate = report.gate_results[0]
    source_counts = _source_counts_from_count_consistency_gate(report)
    summary_generated_at, quality_last_summary_generated_at = (
        _generated_at_values_from_count_consistency_gate(report)
    )
    if summary_generated_at != report.summary_generated_at:
        raise ValueError("count_consistency evidence must match summary timestamp")
    expected_status = (
        "pass"
        if _count_consistency_evidence_passes(
            source_counts,
            summary_generated_at,
            quality_last_summary_generated_at,
        )
        else "fail"
    )
    if gate.status != expected_status:
        raise ValueError("count_consistency status must match count evidence")


def _count_consistency_evidence_passes(
    source_counts: dict[str, tuple[int, int, int]],
    summary_generated_at: datetime,
    quality_last_summary_generated_at: datetime | None,
) -> bool:
    summary_counts = source_counts["summary"]
    shared_counts_match = (
        summary_counts == source_counts["diagnostics"]
        and summary_counts == source_counts["coverage"]
    )
    if not shared_counts_match:
        return False
    quality_counts = source_counts["quality"]
    if quality_last_summary_generated_at is None:
        return summary_counts == (0, 0, 0) and quality_counts == (0, 0, 0)
    if quality_last_summary_generated_at != summary_generated_at:
        return False
    if quality_counts == summary_counts:
        return True
    return (
        quality_counts[0] >= summary_counts[0]
        and quality_counts[1] >= summary_counts[1]
        and quality_counts[2] >= summary_counts[2]
    )


def _source_counts_from_count_consistency_gate(
    report: TradeProposalReviewDossierReport,
) -> dict[str, tuple[int, int, int]]:
    gate = report.gate_results[0]
    if gate.gate_name != "count_consistency":
        raise ValueError("gate_results must begin with count_consistency")
    segments = _count_consistency_segments(gate)
    counts: dict[str, tuple[int, int, int]] = {}
    for segment in segments[:4]:
        source_name, separator, raw_counts = segment.partition("=")
        if separator != "=" or source_name not in SOURCE_REPORT_NAMES:
            raise ValueError("count_consistency observed_value must contain source counts")
        raw_parts = raw_counts.split("/")
        if len(raw_parts) != 3:
            raise ValueError("count_consistency observed_value must contain count triplets")
        try:
            parsed_counts = tuple(int(part) for part in raw_parts)
        except ValueError as exc:
            raise ValueError(
                "count_consistency observed_value counts must be integers"
            ) from exc
        for count_name, count_value in zip(
            (
                "review_record_count",
                "approved_decision_count",
                "rejected_decision_count",
            ),
            parsed_counts,
            strict=True,
        ):
            _require_nonnegative_int(count_name, count_value)
        counts[source_name] = parsed_counts
    if set(counts) != {"summary", "quality", "diagnostics", "coverage"}:
        raise ValueError("count_consistency observed_value must contain all source counts")
    return counts


def _source_proposal_counts_from_count_consistency_gate(
    report: TradeProposalReviewDossierReport,
) -> dict[str, int]:
    gate = report.gate_results[0]
    segments = _count_consistency_segments(gate)
    proposal_prefix = "proposal_counts="
    segment = segments[4]
    if not segment.startswith(proposal_prefix):
        raise ValueError("count_consistency observed_value must contain proposal counts")
    raw_counts = segment[len(proposal_prefix) :]
    raw_parts = raw_counts.split("/")
    if len(raw_parts) != 4:
        raise ValueError("count_consistency observed_value must contain proposal count quartet")
    try:
        parsed_counts = tuple(int(part) for part in raw_parts)
    except ValueError as exc:
        raise ValueError(
            "count_consistency observed_value proposal counts must be integers"
        ) from exc
    for count_value in parsed_counts:
        _require_nonnegative_int("proposal_packet_count", count_value)
    source_names = ("summary", "quality", "diagnostics", "coverage")
    return dict(zip(source_names, parsed_counts, strict=True))


def _generated_at_values_from_count_consistency_gate(
    report: TradeProposalReviewDossierReport,
) -> tuple[datetime, datetime | None]:
    gate = report.gate_results[0]
    segments = _count_consistency_segments(gate)
    values: dict[str, str] = {}
    for segment in segments[5:]:
        key, separator, raw_value = segment.partition("=")
        if key in ("summary_generated_at", "quality_last_summary_generated_at"):
            if separator != "=":
                raise ValueError(
                    "count_consistency observed_value must contain generated_at values"
                )
            values[key] = raw_value
    if set(values) != {"summary_generated_at", "quality_last_summary_generated_at"}:
        raise ValueError("count_consistency observed_value must contain generated_at values")
    return (
        _parse_count_consistency_datetime(
            "summary_generated_at",
            values["summary_generated_at"],
        ),
        None
        if values["quality_last_summary_generated_at"] == "None"
        else _parse_count_consistency_datetime(
            "quality_last_summary_generated_at",
            values["quality_last_summary_generated_at"],
        ),
    )


def _count_consistency_segments(
    gate: TradeProposalReviewDossierGateResult,
) -> tuple[str, ...]:
    if not isinstance(gate.observed_value, str):
        raise ValueError("count_consistency observed_value must be a string")
    segments = tuple(gate.observed_value.split("; "))
    expected_prefixes = (
        "summary=",
        "quality=",
        "diagnostics=",
        "coverage=",
        "proposal_counts=",
        "summary_generated_at=",
        "quality_last_summary_generated_at=",
    )
    if len(segments) != len(expected_prefixes) or any(
        not segment.startswith(prefix)
        for segment, prefix in zip(segments, expected_prefixes, strict=True)
    ):
        raise ValueError("count_consistency observed_value must use canonical segments")
    return segments


def _parse_count_consistency_datetime(field_name: str, raw_value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(raw_value)
    except ValueError as exc:
        raise ValueError(
            "count_consistency observed_value generated_at values must be ISO datetimes"
        ) from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone")
    return _as_utc(parsed)


def _expected_finding_rows(
    gate_results: tuple[TradeProposalReviewDossierGateResult, ...],
) -> tuple[TradeProposalReviewDossierFindingRow, ...]:
    rows: list[TradeProposalReviewDossierFindingRow] = []
    for gate in gate_results:
        if gate.status == "pass":
            continue
        finding_code, severity, source_name, message = _finding_metadata(gate)
        rows.append(
            TradeProposalReviewDossierFindingRow(
                finding_code=finding_code,
                severity=severity,
                source_report_name=source_name,
                message=message,
                observed_value=gate.observed_value,
                threshold=gate.threshold,
            )
        )
    return tuple(
        sorted(rows, key=lambda row: (row.severity, row.source_report_name, row.finding_code))
    )


def _finding_metadata(
    gate: TradeProposalReviewDossierGateResult,
) -> tuple[str, str, str, str]:
    if gate.gate_name == "count_consistency":
        return (
            "count_consistency_failed",
            "inconsistent",
            "dossier",
            "Cross-report aggregate review counts are inconsistent.",
        )
    if gate.gate_name == "summary_evidence":
        return (
            "summary_evidence_incomplete",
            "incomplete",
            "summary",
            "Summary evidence is incomplete.",
        ) if gate.status == "incomplete" else (
            "summary_evidence_unstable",
            "unstable",
            "summary",
            "Summary evidence is unstable.",
        )
    if gate.gate_name == "quality_evidence":
        return (
            "quality_evidence_incomplete",
            "incomplete",
            "quality",
            "Quality evidence is incomplete.",
        ) if gate.status == "incomplete" else (
            "quality_evidence_unstable",
            "unstable",
            "quality",
            "Quality evidence is unstable.",
        )
    if gate.gate_name == "diagnostic_evidence":
        return (
            "diagnostic_evidence_incomplete",
            "incomplete",
            "diagnostics",
            "Diagnostic evidence is incomplete.",
        ) if gate.status == "incomplete" else (
            "diagnostic_evidence_unstable",
            "unstable",
            "diagnostics",
            "Diagnostic evidence is unstable.",
        )
    return (
        "coverage_evidence_incomplete",
        "incomplete",
        "coverage",
        "Coverage evidence is incomplete.",
    ) if gate.status == "incomplete" else (
        "coverage_evidence_inconsistent",
        "inconsistent",
        "coverage",
        "Coverage evidence is inconsistent.",
    )


def _status_category(status: str) -> str:
    try:
        return STATUS_CATEGORY_BY_STATUS[status]
    except KeyError as exc:
        raise ValueError("status must be a known proposal review dossier source status") from exc


def _clone_summary_report(
    summary: TradeProposalReviewSummaryReport,
) -> TradeProposalReviewSummaryReport:
    if type(summary) is not TradeProposalReviewSummaryReport:
        raise ValueError("summary must be a TradeProposalReviewSummaryReport")
    reason_code_summaries = tuple(
        TradeProposalReviewReasonCodeSummary(
            reason_code=row.reason_code,
            rejected_decision_count=row.rejected_decision_count,
            rejected_source_proposal_count=row.rejected_source_proposal_count,
            rejected_decision_ratio=row.rejected_decision_ratio,
        )
        for row in summary.reason_code_summaries
    )
    bucket_summaries = tuple(
        TradeProposalReviewBucketSummary(
            bucket_type=row.bucket_type,
            bucket_value=row.bucket_value,
            review_record_count=row.review_record_count,
            unique_source_proposal_count=row.unique_source_proposal_count,
            approved_decision_count=row.approved_decision_count,
            rejected_decision_count=row.rejected_decision_count,
            rejection_ratio=row.rejection_ratio,
        )
        for row in summary.bucket_summaries
    )
    return TradeProposalReviewSummaryReport(
        generated_at=summary.generated_at,
        config_version=summary.config_version,
        report_only=summary.report_only,
        boundary_statement=summary.boundary_statement,
        review_record_count=summary.review_record_count,
        unique_source_proposal_count=summary.unique_source_proposal_count,
        duplicate_source_proposal_count=summary.duplicate_source_proposal_count,
        first_recorded_at=summary.first_recorded_at,
        last_recorded_at=summary.last_recorded_at,
        approved_decision_count=summary.approved_decision_count,
        rejected_decision_count=summary.rejected_decision_count,
        rejection_ratio=summary.rejection_ratio,
        status=summary.status,
        reason_code_summaries=reason_code_summaries,
        bucket_summaries=bucket_summaries,
    )


def _clone_quality_report(
    quality: TradeProposalReviewQualityReport,
) -> TradeProposalReviewQualityReport:
    if type(quality) is not TradeProposalReviewQualityReport:
        raise ValueError("quality must be a TradeProposalReviewQualityReport")
    gate_results = tuple(
        TradeProposalReviewQualityGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in quality.gate_results
    )
    reason_trends = tuple(
        TradeProposalReviewQualityReasonTrend(
            reason_code=row.reason_code,
            summary_report_count=row.summary_report_count,
            total_rejected_decision_count=row.total_rejected_decision_count,
            max_rejected_decision_ratio=row.max_rejected_decision_ratio,
            latest_rejected_decision_ratio=row.latest_rejected_decision_ratio,
        )
        for row in quality.reason_trends
    )
    return TradeProposalReviewQualityReport(
        generated_at=quality.generated_at,
        config_version=quality.config_version,
        report_only=quality.report_only,
        boundary_statement=quality.boundary_statement,
        summary_report_count=quality.summary_report_count,
        first_summary_generated_at=quality.first_summary_generated_at,
        last_summary_generated_at=quality.last_summary_generated_at,
        total_review_record_count=quality.total_review_record_count,
        summed_unique_source_proposal_count=quality.summed_unique_source_proposal_count,
        total_duplicate_source_proposal_count=quality.total_duplicate_source_proposal_count,
        approved_decision_count=quality.approved_decision_count,
        rejected_decision_count=quality.rejected_decision_count,
        overall_rejection_ratio=quality.overall_rejection_ratio,
        latest_summary_rejection_ratio=quality.latest_summary_rejection_ratio,
        worst_summary_rejection_ratio=quality.worst_summary_rejection_ratio,
        max_reason_code_rejection_share=quality.max_reason_code_rejection_share,
        duplicate_source_proposal_ratio=quality.duplicate_source_proposal_ratio,
        status=quality.status,
        gate_results=gate_results,
        reason_trends=reason_trends,
    )


def _clone_diagnostic_report(
    diagnostics: TradeProposalReviewDiagnosticReport,
) -> TradeProposalReviewDiagnosticReport:
    if type(diagnostics) is not TradeProposalReviewDiagnosticReport:
        raise ValueError("diagnostics must be a TradeProposalReviewDiagnosticReport")
    reason_rows = tuple(
        TradeProposalReviewDiagnosticReasonRow(
            reason_code=row.reason_code,
            rejected_decision_count=row.rejected_decision_count,
            rejected_source_proposal_count=row.rejected_source_proposal_count,
            rejected_decision_share=row.rejected_decision_share,
        )
        for row in diagnostics.reason_rows
    )
    bucket_rows = tuple(
        TradeProposalReviewDiagnosticBucketRow(
            bucket_type=row.bucket_type,
            bucket_value=row.bucket_value,
            review_record_count=row.review_record_count,
            unique_source_proposal_count=row.unique_source_proposal_count,
            rejected_decision_count=row.rejected_decision_count,
            rejected_source_proposal_count=row.rejected_source_proposal_count,
            rejected_decision_ratio=row.rejected_decision_ratio,
        )
        for row in diagnostics.bucket_rows
    )
    source_rows = tuple(
        TradeProposalReviewDiagnosticSourceRow(
            source_proposal_packet_id=row.source_proposal_packet_id,
            source_proposal_fingerprint=row.source_proposal_fingerprint,
            first_recorded_at=row.first_recorded_at,
            last_recorded_at=row.last_recorded_at,
            review_record_count=row.review_record_count,
            rejected_decision_count=row.rejected_decision_count,
            reason_codes=row.reason_codes,
            market_slug=row.market_slug,
            strategy_type=row.strategy_type,
            risk_tags=row.risk_tags,
            review_focus=row.review_focus,
        )
        for row in diagnostics.source_rows
    )
    return TradeProposalReviewDiagnosticReport(
        generated_at=diagnostics.generated_at,
        config_version=diagnostics.config_version,
        report_only=diagnostics.report_only,
        boundary_statement=diagnostics.boundary_statement,
        review_record_count=diagnostics.review_record_count,
        unique_source_proposal_count=diagnostics.unique_source_proposal_count,
        duplicate_source_proposal_review_count=(
            diagnostics.duplicate_source_proposal_review_count
        ),
        approved_decision_count=diagnostics.approved_decision_count,
        rejected_decision_count=diagnostics.rejected_decision_count,
        rejected_source_proposal_count=diagnostics.rejected_source_proposal_count,
        rejected_decision_ratio=diagnostics.rejected_decision_ratio,
        rejected_source_proposal_ratio=diagnostics.rejected_source_proposal_ratio,
        max_reason_code_rejected_decision_share=(
            diagnostics.max_reason_code_rejected_decision_share
        ),
        first_recorded_at=diagnostics.first_recorded_at,
        last_recorded_at=diagnostics.last_recorded_at,
        status=diagnostics.status,
        reason_rows=reason_rows,
        bucket_rows=bucket_rows,
        source_rows=source_rows,
    )


def _clone_coverage_report(
    coverage: TradeProposalReviewCoverageReport,
) -> TradeProposalReviewCoverageReport:
    if type(coverage) is not TradeProposalReviewCoverageReport:
        raise ValueError("coverage must be a TradeProposalReviewCoverageReport")
    gate_results = tuple(
        TradeProposalReviewCoverageGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in coverage.gate_results
    )
    bucket_rows = tuple(
        TradeProposalReviewCoverageBucketRow(
            bucket_name=row.bucket_name,
            proposal_packet_count=row.proposal_packet_count,
            review_record_count=row.review_record_count,
            coverage_ratio=row.coverage_ratio,
        )
        for row in coverage.bucket_rows
    )
    packet_rows = tuple(
        TradeProposalReviewCoveragePacketRow(
            coverage_status=row.coverage_status,
            proposal_packet_id=row.proposal_packet_id,
            source_proposal_fingerprint=row.source_proposal_fingerprint,
            first_proposal_generated_at=row.first_proposal_generated_at,
            last_proposal_generated_at=row.last_proposal_generated_at,
            first_recorded_at=row.first_recorded_at,
            last_recorded_at=row.last_recorded_at,
            review_record_count=row.review_record_count,
            approved_decision_count=row.approved_decision_count,
            rejected_decision_count=row.rejected_decision_count,
            market_slug=row.market_slug,
            strategy_type=row.strategy_type,
            risk_tags=row.risk_tags,
            review_record_ids=row.review_record_ids,
        )
        for row in coverage.packet_rows
    )
    return TradeProposalReviewCoverageReport(
        generated_at=coverage.generated_at,
        config_version=coverage.config_version,
        report_only=coverage.report_only,
        boundary_statement=coverage.boundary_statement,
        proposal_packet_count=coverage.proposal_packet_count,
        review_record_count=coverage.review_record_count,
        reviewed_proposal_packet_count=coverage.reviewed_proposal_packet_count,
        unreviewed_proposal_packet_count=coverage.unreviewed_proposal_packet_count,
        duplicate_reviewed_proposal_packet_count=(
            coverage.duplicate_reviewed_proposal_packet_count
        ),
        conflicting_decision_proposal_packet_count=(
            coverage.conflicting_decision_proposal_packet_count
        ),
        orphan_review_record_count=coverage.orphan_review_record_count,
        approved_decision_count=coverage.approved_decision_count,
        rejected_decision_count=coverage.rejected_decision_count,
        review_coverage_ratio=coverage.review_coverage_ratio,
        unreviewed_proposal_packet_ratio=coverage.unreviewed_proposal_packet_ratio,
        duplicate_reviewed_proposal_packet_ratio=(
            coverage.duplicate_reviewed_proposal_packet_ratio
        ),
        conflicting_decision_proposal_packet_ratio=(
            coverage.conflicting_decision_proposal_packet_ratio
        ),
        orphan_review_record_ratio=coverage.orphan_review_record_ratio,
        first_proposal_generated_at=coverage.first_proposal_generated_at,
        last_proposal_generated_at=coverage.last_proposal_generated_at,
        first_recorded_at=coverage.first_recorded_at,
        last_recorded_at=coverage.last_recorded_at,
        status=coverage.status,
        gate_results=gate_results,
        bucket_rows=bucket_rows,
        packet_rows=packet_rows,
    )


def _validate_report_tree(
    report: TradeProposalReviewDossierReport,
) -> TradeProposalReviewDossierReport:
    gate_results = tuple(
        TradeProposalReviewDossierGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in report.gate_results
    )
    source_rows = tuple(
        TradeProposalReviewDossierSourceRow(
            report_name=row.report_name,
            report_status=row.report_status,
            generated_at=row.generated_at,
            review_record_count=row.review_record_count,
            proposal_packet_count=row.proposal_packet_count,
            approved_decision_count=row.approved_decision_count,
            rejected_decision_count=row.rejected_decision_count,
            status_category=row.status_category,
        )
        for row in report.source_rows
    )
    finding_rows = tuple(
        TradeProposalReviewDossierFindingRow(
            finding_code=row.finding_code,
            severity=row.severity,
            source_report_name=row.source_report_name,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in report.finding_rows
    )
    return TradeProposalReviewDossierReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        summary_generated_at=report.summary_generated_at,
        quality_generated_at=report.quality_generated_at,
        diagnostic_generated_at=report.diagnostic_generated_at,
        coverage_generated_at=report.coverage_generated_at,
        review_record_count=report.review_record_count,
        proposal_packet_count=report.proposal_packet_count,
        reviewed_proposal_packet_count=report.reviewed_proposal_packet_count,
        unreviewed_proposal_packet_count=report.unreviewed_proposal_packet_count,
        orphan_review_record_count=report.orphan_review_record_count,
        duplicate_reviewed_proposal_packet_count=(
            report.duplicate_reviewed_proposal_packet_count
        ),
        conflicting_decision_proposal_packet_count=(
            report.conflicting_decision_proposal_packet_count
        ),
        approved_decision_count=report.approved_decision_count,
        rejected_decision_count=report.rejected_decision_count,
        review_coverage_ratio=report.review_coverage_ratio,
        rejection_ratio=report.rejection_ratio,
        summary_status=report.summary_status,
        quality_status=report.quality_status,
        diagnostic_status=report.diagnostic_status,
        coverage_status=report.coverage_status,
        status=report.status,
        gate_results=gate_results,
        source_rows=source_rows,
        finding_rows=finding_rows,
    )


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        _require_finite_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError("path is required")
    try:
        path = Path(value)
    except TypeError as exc:
        raise ValueError("path must be path-like") from exc
    if path.exists() and path.is_dir():
        raise ValueError("path must be a file path")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    for parent in (path.parent, *path.parent.parents):
        if parent.exists():
            if not parent.is_dir():
                raise ValueError("path parent must be a directory")
            return


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_boundary_statement(value: str) -> None:
    _require_canonical_string("boundary_statement", value)
    normalized = _normalize_boundary_text(value)
    if normalized != _normalize_boundary_text(DEFAULT_REVIEW_DOSSIER_BOUNDARY_STATEMENT):
        raise ValueError(
            "boundary_statement must describe report-only proposal-review dossier"
        )


def _normalize_boundary_text(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)


def _require_probability_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_optional_probability_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is not None:
        _require_probability_decimal(field_name, value)


def _require_gate_value(
    field_name: str,
    value: Decimal | int | str | None,
) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a bool")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if isinstance(value, Decimal):
        _require_finite_decimal(field_name, value)
        return
    if isinstance(value, int):
        return
    if isinstance(value, str):
        _require_canonical_string(field_name, value)
        return
    raise ValueError(f"{field_name} must be a Decimal, int, string, or None")


def _normalize_typed_tuple(
    field_name: str,
    values: Iterable[Any],
    expected_type: type[Any],
) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for item in items:
        if type(item) is not expected_type:
            raise ValueError(f"{field_name} must contain {expected_type.__name__} values")
    return items


def _optional_ratio_from_counts(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )
