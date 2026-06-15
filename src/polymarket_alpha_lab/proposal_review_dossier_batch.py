"""Report-only proposal-review dossier batch health artifacts for Level 2."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.proposal_review_dossier import (
    TradeProposalReviewDossierFindingRow,
    TradeProposalReviewDossierGateResult,
    TradeProposalReviewDossierReport,
    TradeProposalReviewDossierSourceRow,
)


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
RATIO_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")
GATE_NAMES = (
    "dossier_sample",
    "incomplete_dossier_rate",
    "inconsistent_dossier_rate",
    "unstable_dossier_rate",
)
GATE_STATUSES = ("pass", "fail")
REPORT_STATUSES = (
    "incomplete_dossier_batch",
    "inconsistent_dossier_batch",
    "unstable_dossier_batch",
    "proposal_review_dossier_batch_ready",
)
DOSSIER_STATUSES = (
    "incomplete_review_dossier",
    "inconsistent_review_dossier",
    "unstable_review_dossier",
    "proposal_review_dossier_complete",
)
SOURCE_REPORT_NAMES = ("coverage", "diagnostics", "quality", "summary")
STATUS_CATEGORIES = ("complete", "incomplete", "inconsistent", "unstable")


@dataclass(frozen=True)
class TradeProposalReviewDossierBatchConfig:
    config_version: str
    min_dossier_count: int = 1
    max_incomplete_dossier_ratio: Decimal = Decimal("0.0000")
    max_inconsistent_dossier_ratio: Decimal = Decimal("0.0000")
    max_unstable_dossier_ratio: Decimal = Decimal("0.0000")
    boundary_statement: str = DEFAULT_REVIEW_DOSSIER_BATCH_BOUNDARY_STATEMENT

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("min_dossier_count", self.min_dossier_count)
        _require_probability_decimal(
            "max_incomplete_dossier_ratio",
            self.max_incomplete_dossier_ratio,
        )
        _require_probability_decimal(
            "max_inconsistent_dossier_ratio",
            self.max_inconsistent_dossier_ratio,
        )
        _require_probability_decimal(
            "max_unstable_dossier_ratio",
            self.max_unstable_dossier_ratio,
        )
        _require_boundary_statement(self.boundary_statement)


@dataclass(frozen=True)
class TradeProposalReviewDossierBatchGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known dossier batch gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known dossier batch gate status")
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class TradeProposalReviewDossierBatchConfigVersionSummary:
    dossier_config_version: str
    dossier_count: int

    def __post_init__(self) -> None:
        _require_canonical_string(
            "dossier_config_version",
            self.dossier_config_version,
        )
        _require_nonnegative_int("dossier_count", self.dossier_count)
        if self.dossier_count == 0:
            raise ValueError("dossier_count must be positive")


@dataclass(frozen=True)
class TradeProposalReviewDossierBatchDuplicateSummary:
    dossier_fingerprint: str
    dossier_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("dossier_fingerprint", self.dossier_fingerprint)
        _require_nonnegative_int("dossier_count", self.dossier_count)
        if self.dossier_count < 2:
            raise ValueError("dossier_count must be at least 2 for duplicates")


@dataclass(frozen=True)
class TradeProposalReviewDossierBatchFindingSummary:
    finding_code: str
    severity: str
    source_report_name: str
    dossier_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("finding_code", self.finding_code)
        if self.severity not in ("incomplete", "inconsistent", "unstable"):
            raise ValueError("severity must be incomplete, inconsistent, or unstable")
        if self.source_report_name not in (*SOURCE_REPORT_NAMES, "dossier"):
            raise ValueError("source_report_name must be a known dossier finding source")
        _require_nonnegative_int("dossier_count", self.dossier_count)
        if self.dossier_count == 0:
            raise ValueError("dossier_count must be positive")


@dataclass(frozen=True)
class TradeProposalReviewDossierBatchSourceSummary:
    source_report_name: str
    complete_count: int
    incomplete_count: int
    inconsistent_count: int
    unstable_count: int

    def __post_init__(self) -> None:
        if self.source_report_name not in SOURCE_REPORT_NAMES:
            raise ValueError("source_report_name must be a known dossier source")
        for field_name in (
            "complete_count",
            "incomplete_count",
            "inconsistent_count",
            "unstable_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))


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
    config_version_summaries: tuple[
        TradeProposalReviewDossierBatchConfigVersionSummary,
        ...,
    ]
    duplicate_summaries: tuple[TradeProposalReviewDossierBatchDuplicateSummary, ...]
    finding_summaries: tuple[TradeProposalReviewDossierBatchFindingSummary, ...]
    source_summaries: tuple[TradeProposalReviewDossierBatchSourceSummary, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        for field_name in ("first_dossier_generated_at", "last_dossier_generated_at"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _as_utc(value))
        _require_canonical_string("config_version", self.config_version)
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        _require_boundary_statement(self.boundary_statement)
        for field_name in (
            "dossier_count",
            "complete_dossier_count",
            "incomplete_dossier_count",
            "inconsistent_dossier_count",
            "unstable_dossier_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.dossier_count != (
            self.complete_dossier_count
            + self.incomplete_dossier_count
            + self.inconsistent_dossier_count
            + self.unstable_dossier_count
        ):
            raise ValueError("dossier_count must equal dossier status counts")
        _require_optional_probability_decimal(
            "incomplete_dossier_ratio",
            self.incomplete_dossier_ratio,
        )
        _require_optional_probability_decimal(
            "inconsistent_dossier_ratio",
            self.inconsistent_dossier_ratio,
        )
        _require_optional_probability_decimal(
            "unstable_dossier_ratio",
            self.unstable_dossier_ratio,
        )
        _validate_report_ratios(self)
        if self.dossier_count == 0:
            if (
                self.first_dossier_generated_at is not None
                or self.last_dossier_generated_at is not None
            ):
                raise ValueError("dossier timestamp bounds must be None for empty batches")
        else:
            if (
                self.first_dossier_generated_at is None
                or self.last_dossier_generated_at is None
            ):
                raise ValueError("dossier timestamp bounds are required")
            if self.first_dossier_generated_at > self.last_dossier_generated_at:
                raise ValueError("first_dossier_generated_at must not exceed last")
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known dossier batch status")
        object.__setattr__(
            self,
            "gate_results",
            _normalize_typed_tuple(
                "gate_results",
                self.gate_results,
                TradeProposalReviewDossierBatchGateResult,
            ),
        )
        object.__setattr__(
            self,
            "config_version_summaries",
            _normalize_typed_tuple(
                "config_version_summaries",
                self.config_version_summaries,
                TradeProposalReviewDossierBatchConfigVersionSummary,
            ),
        )
        object.__setattr__(
            self,
            "duplicate_summaries",
            _normalize_typed_tuple(
                "duplicate_summaries",
                self.duplicate_summaries,
                TradeProposalReviewDossierBatchDuplicateSummary,
            ),
        )
        object.__setattr__(
            self,
            "finding_summaries",
            _normalize_typed_tuple(
                "finding_summaries",
                self.finding_summaries,
                TradeProposalReviewDossierBatchFindingSummary,
            ),
        )
        object.__setattr__(
            self,
            "source_summaries",
            _normalize_typed_tuple(
                "source_summaries",
                self.source_summaries,
                TradeProposalReviewDossierBatchSourceSummary,
            ),
        )
        if tuple(row.gate_name for row in self.gate_results) != GATE_NAMES:
            raise ValueError("gate_results must contain dossier batch gates")
        _validate_gate_semantics(self)
        if self.status != _batch_status(self.gate_results):
            raise ValueError("status must match dossier batch gate results")
        _validate_config_version_summaries(self)
        _validate_duplicate_summaries(self)
        _validate_finding_summaries(self)
        _validate_source_summaries(self)


@dataclass(frozen=True)
class TradeProposalReviewDossierBatchLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: TradeProposalReviewDossierBatchReport) -> None:
        if type(report) is not TradeProposalReviewDossierBatchReport:
            raise ValueError("report must be a TradeProposalReviewDossierBatchReport")
        validated = _validate_report_tree(report)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True)
        line += "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_trade_proposal_review_dossier_batch_report(
    dossiers: Iterable[TradeProposalReviewDossierReport],
    *,
    config: TradeProposalReviewDossierBatchConfig,
    generated_at: datetime,
) -> TradeProposalReviewDossierBatchReport:
    if type(config) is not TradeProposalReviewDossierBatchConfig:
        raise ValueError("config must be a TradeProposalReviewDossierBatchConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    dossier_items = _normalize_dossier_inputs(dossiers)
    counts = _dossier_status_counts(dossier_items)
    dossier_count = len(dossier_items)
    incomplete_ratio = _optional_ratio_from_counts(
        counts["incomplete_review_dossier"],
        dossier_count,
    )
    inconsistent_ratio = _optional_ratio_from_counts(
        counts["inconsistent_review_dossier"],
        dossier_count,
    )
    unstable_ratio = _optional_ratio_from_counts(
        counts["unstable_review_dossier"],
        dossier_count,
    )
    gate_results = _build_gate_results(
        dossier_count=dossier_count,
        incomplete_ratio=incomplete_ratio,
        inconsistent_ratio=inconsistent_ratio,
        unstable_ratio=unstable_ratio,
        config=config,
    )
    generated_values = tuple(row.generated_at for row in dossier_items)
    return TradeProposalReviewDossierBatchReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_only=True,
        boundary_statement=config.boundary_statement,
        dossier_count=dossier_count,
        complete_dossier_count=counts["proposal_review_dossier_complete"],
        incomplete_dossier_count=counts["incomplete_review_dossier"],
        inconsistent_dossier_count=counts["inconsistent_review_dossier"],
        unstable_dossier_count=counts["unstable_review_dossier"],
        incomplete_dossier_ratio=incomplete_ratio,
        inconsistent_dossier_ratio=inconsistent_ratio,
        unstable_dossier_ratio=unstable_ratio,
        first_dossier_generated_at=min(generated_values) if generated_values else None,
        last_dossier_generated_at=max(generated_values) if generated_values else None,
        status=_batch_status(gate_results),
        gate_results=gate_results,
        config_version_summaries=_config_version_summaries(dossier_items),
        duplicate_summaries=_duplicate_summaries(dossier_items),
        finding_summaries=_finding_summaries(dossier_items),
        source_summaries=_source_summaries(dossier_items),
    )


def _build_gate_results(
    *,
    dossier_count: int,
    incomplete_ratio: Decimal | None,
    inconsistent_ratio: Decimal | None,
    unstable_ratio: Decimal | None,
    config: TradeProposalReviewDossierBatchConfig,
) -> tuple[TradeProposalReviewDossierBatchGateResult, ...]:
    sample_passes = dossier_count >= config.min_dossier_count
    return (
        TradeProposalReviewDossierBatchGateResult(
            gate_name="dossier_sample",
            status="pass" if sample_passes else "fail",
            message=(
                "Dossier sample size meets the configured minimum."
                if sample_passes
                else "Dossier sample size is below the configured minimum."
            ),
            observed_value=dossier_count,
            threshold=config.min_dossier_count,
        ),
        _rate_gate(
            gate_name="incomplete_dossier_rate",
            ratio=incomplete_ratio,
            threshold=config.max_incomplete_dossier_ratio,
            pass_message="Incomplete dossier rate is within threshold.",
            fail_message="Incomplete dossier rate exceeds threshold or is unavailable.",
        ),
        _rate_gate(
            gate_name="inconsistent_dossier_rate",
            ratio=inconsistent_ratio,
            threshold=config.max_inconsistent_dossier_ratio,
            pass_message="Inconsistent dossier rate is within threshold.",
            fail_message="Inconsistent dossier rate exceeds threshold or is unavailable.",
        ),
        _rate_gate(
            gate_name="unstable_dossier_rate",
            ratio=unstable_ratio,
            threshold=config.max_unstable_dossier_ratio,
            pass_message="Unstable dossier rate is within threshold.",
            fail_message="Unstable dossier rate exceeds threshold or is unavailable.",
        ),
    )


def _rate_gate(
    *,
    gate_name: str,
    ratio: Decimal | None,
    threshold: Decimal,
    pass_message: str,
    fail_message: str,
) -> TradeProposalReviewDossierBatchGateResult:
    passes = ratio is not None and ratio <= threshold
    return TradeProposalReviewDossierBatchGateResult(
        gate_name=gate_name,
        status="pass" if passes else "fail",
        message=pass_message if passes else fail_message,
        observed_value=ratio,
        threshold=threshold,
    )


def _batch_status(
    gate_results: tuple[TradeProposalReviewDossierBatchGateResult, ...],
) -> str:
    gates = {row.gate_name: row.status for row in gate_results}
    if gates["dossier_sample"] == "fail":
        return "incomplete_dossier_batch"
    if gates["inconsistent_dossier_rate"] == "fail":
        return "inconsistent_dossier_batch"
    if gates["incomplete_dossier_rate"] == "fail":
        return "incomplete_dossier_batch"
    if gates["unstable_dossier_rate"] == "fail":
        return "unstable_dossier_batch"
    return "proposal_review_dossier_batch_ready"


def _normalize_dossier_inputs(
    dossiers: Iterable[TradeProposalReviewDossierReport],
) -> tuple[TradeProposalReviewDossierReport, ...]:
    if isinstance(dossiers, (str, bytes)):
        raise ValueError("dossiers must be an iterable of dossier reports")
    try:
        raw_items = tuple(dossiers)
    except TypeError as exc:
        raise ValueError("dossiers must be an iterable of dossier reports") from exc
    return tuple(_clone_dossier_report(item) for item in raw_items)


def _clone_dossier_report(
    dossier: TradeProposalReviewDossierReport,
) -> TradeProposalReviewDossierReport:
    if type(dossier) is not TradeProposalReviewDossierReport:
        raise ValueError("dossiers must contain TradeProposalReviewDossierReport values")
    raw_gate_results = _normalize_typed_tuple(
        "gate_results",
        dossier.gate_results,
        TradeProposalReviewDossierGateResult,
    )
    raw_source_rows = _normalize_typed_tuple(
        "source_rows",
        dossier.source_rows,
        TradeProposalReviewDossierSourceRow,
    )
    raw_finding_rows = _normalize_typed_tuple(
        "finding_rows",
        dossier.finding_rows,
        TradeProposalReviewDossierFindingRow,
    )
    gate_results = tuple(
        TradeProposalReviewDossierGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in raw_gate_results
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
        for row in raw_source_rows
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
        for row in raw_finding_rows
    )
    return TradeProposalReviewDossierReport(
        generated_at=dossier.generated_at,
        config_version=dossier.config_version,
        report_only=dossier.report_only,
        boundary_statement=dossier.boundary_statement,
        summary_generated_at=dossier.summary_generated_at,
        quality_generated_at=dossier.quality_generated_at,
        diagnostic_generated_at=dossier.diagnostic_generated_at,
        coverage_generated_at=dossier.coverage_generated_at,
        review_record_count=dossier.review_record_count,
        proposal_packet_count=dossier.proposal_packet_count,
        reviewed_proposal_packet_count=dossier.reviewed_proposal_packet_count,
        unreviewed_proposal_packet_count=dossier.unreviewed_proposal_packet_count,
        orphan_review_record_count=dossier.orphan_review_record_count,
        duplicate_reviewed_proposal_packet_count=(
            dossier.duplicate_reviewed_proposal_packet_count
        ),
        conflicting_decision_proposal_packet_count=(
            dossier.conflicting_decision_proposal_packet_count
        ),
        approved_decision_count=dossier.approved_decision_count,
        rejected_decision_count=dossier.rejected_decision_count,
        review_coverage_ratio=dossier.review_coverage_ratio,
        rejection_ratio=dossier.rejection_ratio,
        summary_status=dossier.summary_status,
        quality_status=dossier.quality_status,
        diagnostic_status=dossier.diagnostic_status,
        coverage_status=dossier.coverage_status,
        status=dossier.status,
        gate_results=gate_results,
        source_rows=source_rows,
        finding_rows=finding_rows,
    )


def _dossier_status_counts(
    dossiers: tuple[TradeProposalReviewDossierReport, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in DOSSIER_STATUSES}
    for dossier in dossiers:
        counts[dossier.status] += 1
    return counts


def _config_version_summaries(
    dossiers: tuple[TradeProposalReviewDossierReport, ...],
) -> tuple[TradeProposalReviewDossierBatchConfigVersionSummary, ...]:
    counts: dict[str, int] = {}
    for dossier in dossiers:
        counts[dossier.config_version] = counts.get(dossier.config_version, 0) + 1
    return tuple(
        TradeProposalReviewDossierBatchConfigVersionSummary(
            dossier_config_version=config_version,
            dossier_count=counts[config_version],
        )
        for config_version in sorted(counts)
    )


def _duplicate_summaries(
    dossiers: tuple[TradeProposalReviewDossierReport, ...],
) -> tuple[TradeProposalReviewDossierBatchDuplicateSummary, ...]:
    counts: dict[str, int] = {}
    for dossier in dossiers:
        fingerprint = _dossier_fingerprint(dossier)
        counts[fingerprint] = counts.get(fingerprint, 0) + 1
    return tuple(
        TradeProposalReviewDossierBatchDuplicateSummary(
            dossier_fingerprint=fingerprint,
            dossier_count=counts[fingerprint],
        )
        for fingerprint in sorted(counts)
        if counts[fingerprint] > 1
    )


def _dossier_fingerprint(dossier: TradeProposalReviewDossierReport) -> str:
    return json.dumps(_json_ready(asdict(dossier)), allow_nan=False, sort_keys=True)


def _finding_summaries(
    dossiers: tuple[TradeProposalReviewDossierReport, ...],
) -> tuple[TradeProposalReviewDossierBatchFindingSummary, ...]:
    counts: dict[tuple[str, str, str], int] = {}
    for dossier in dossiers:
        dossier_keys = {
            (row.severity, row.source_report_name, row.finding_code)
            for row in dossier.finding_rows
        }
        for key in dossier_keys:
            counts[key] = counts.get(key, 0) + 1
    return tuple(
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code=finding_code,
            severity=severity,
            source_report_name=source_report_name,
            dossier_count=counts[(severity, source_report_name, finding_code)],
        )
        for severity, source_report_name, finding_code in sorted(counts)
    )


def _source_summaries(
    dossiers: tuple[TradeProposalReviewDossierReport, ...],
) -> tuple[TradeProposalReviewDossierBatchSourceSummary, ...]:
    counts = {
        source_name: {category: 0 for category in STATUS_CATEGORIES}
        for source_name in SOURCE_REPORT_NAMES
    }
    for dossier in dossiers:
        for row in dossier.source_rows:
            counts[row.report_name][row.status_category] += 1
    return tuple(
        TradeProposalReviewDossierBatchSourceSummary(
            source_report_name=source_name,
            complete_count=counts[source_name]["complete"],
            incomplete_count=counts[source_name]["incomplete"],
            inconsistent_count=counts[source_name]["inconsistent"],
            unstable_count=counts[source_name]["unstable"],
        )
        for source_name in SOURCE_REPORT_NAMES
    )


def _validate_report_tree(
    report: TradeProposalReviewDossierBatchReport,
) -> TradeProposalReviewDossierBatchReport:
    gate_results = tuple(
        TradeProposalReviewDossierBatchGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in report.gate_results
    )
    config_version_summaries = tuple(
        TradeProposalReviewDossierBatchConfigVersionSummary(
            dossier_config_version=row.dossier_config_version,
            dossier_count=row.dossier_count,
        )
        for row in report.config_version_summaries
    )
    duplicate_summaries = tuple(
        TradeProposalReviewDossierBatchDuplicateSummary(
            dossier_fingerprint=row.dossier_fingerprint,
            dossier_count=row.dossier_count,
        )
        for row in report.duplicate_summaries
    )
    finding_summaries = tuple(
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code=row.finding_code,
            severity=row.severity,
            source_report_name=row.source_report_name,
            dossier_count=row.dossier_count,
        )
        for row in report.finding_summaries
    )
    source_summaries = tuple(
        TradeProposalReviewDossierBatchSourceSummary(
            source_report_name=row.source_report_name,
            complete_count=row.complete_count,
            incomplete_count=row.incomplete_count,
            inconsistent_count=row.inconsistent_count,
            unstable_count=row.unstable_count,
        )
        for row in report.source_summaries
    )
    return TradeProposalReviewDossierBatchReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        dossier_count=report.dossier_count,
        complete_dossier_count=report.complete_dossier_count,
        incomplete_dossier_count=report.incomplete_dossier_count,
        inconsistent_dossier_count=report.inconsistent_dossier_count,
        unstable_dossier_count=report.unstable_dossier_count,
        incomplete_dossier_ratio=report.incomplete_dossier_ratio,
        inconsistent_dossier_ratio=report.inconsistent_dossier_ratio,
        unstable_dossier_ratio=report.unstable_dossier_ratio,
        first_dossier_generated_at=report.first_dossier_generated_at,
        last_dossier_generated_at=report.last_dossier_generated_at,
        status=report.status,
        gate_results=gate_results,
        config_version_summaries=config_version_summaries,
        duplicate_summaries=duplicate_summaries,
        finding_summaries=finding_summaries,
        source_summaries=source_summaries,
    )


def _validate_report_ratios(report: TradeProposalReviewDossierBatchReport) -> None:
    expected = {
        "incomplete_dossier_ratio": _optional_ratio_from_counts(
            report.incomplete_dossier_count,
            report.dossier_count,
        ),
        "inconsistent_dossier_ratio": _optional_ratio_from_counts(
            report.inconsistent_dossier_count,
            report.dossier_count,
        ),
        "unstable_dossier_ratio": _optional_ratio_from_counts(
            report.unstable_dossier_count,
            report.dossier_count,
        ),
    }
    for field_name, expected_value in expected.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match dossier counts")


def _validate_gate_semantics(report: TradeProposalReviewDossierBatchReport) -> None:
    sample_threshold = report.gate_results[0].threshold
    if isinstance(sample_threshold, Decimal):
        raise ValueError("gate_results sample threshold must be an int")
    if not isinstance(sample_threshold, int) or isinstance(sample_threshold, bool):
        raise ValueError("gate_results sample threshold must be an int")
    expected = _build_gate_results(
        dossier_count=report.dossier_count,
        incomplete_ratio=report.incomplete_dossier_ratio,
        inconsistent_ratio=report.inconsistent_dossier_ratio,
        unstable_ratio=report.unstable_dossier_ratio,
        config=TradeProposalReviewDossierBatchConfig(
            config_version=report.config_version,
            min_dossier_count=sample_threshold,
            max_incomplete_dossier_ratio=_require_decimal_gate_threshold(
                "incomplete_dossier_rate",
                report.gate_results[1].threshold,
            ),
            max_inconsistent_dossier_ratio=_require_decimal_gate_threshold(
                "inconsistent_dossier_rate",
                report.gate_results[2].threshold,
            ),
            max_unstable_dossier_ratio=_require_decimal_gate_threshold(
                "unstable_dossier_rate",
                report.gate_results[3].threshold,
            ),
            boundary_statement=report.boundary_statement,
        ),
    )
    if report.gate_results != expected:
        raise ValueError("gate_results must match dossier batch counts and thresholds")


def _require_decimal_gate_threshold(gate_name: str, value: Decimal | int | str | None) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"gate_results {gate_name} threshold must be a Decimal")
    _require_probability_decimal(f"{gate_name} threshold", value)
    return value


def _validate_config_version_summaries(
    report: TradeProposalReviewDossierBatchReport,
) -> None:
    keys = tuple(row.dossier_config_version for row in report.config_version_summaries)
    if keys != tuple(sorted(keys)):
        raise ValueError("config_version_summaries must be sorted")
    if len(set(keys)) != len(keys):
        raise ValueError("config_version_summaries must not contain duplicates")
    if sum(row.dossier_count for row in report.config_version_summaries) != report.dossier_count:
        raise ValueError("config_version_summaries must match dossier_count")


def _validate_duplicate_summaries(report: TradeProposalReviewDossierBatchReport) -> None:
    keys = tuple(row.dossier_fingerprint for row in report.duplicate_summaries)
    if keys != tuple(sorted(keys)):
        raise ValueError("duplicate_summaries must be sorted")
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate_summaries must not contain duplicate fingerprints")
    for row in report.duplicate_summaries:
        if row.dossier_count > report.dossier_count:
            raise ValueError("duplicate_summaries counts must not exceed dossier_count")


def _validate_finding_summaries(report: TradeProposalReviewDossierBatchReport) -> None:
    keys = tuple(
        (row.severity, row.source_report_name, row.finding_code)
        for row in report.finding_summaries
    )
    if keys != tuple(sorted(keys)):
        raise ValueError("finding_summaries must be sorted")
    if len(set(keys)) != len(keys):
        raise ValueError("finding_summaries must not contain duplicate keys")
    for row in report.finding_summaries:
        if row.dossier_count > report.dossier_count:
            raise ValueError("finding_summaries counts must not exceed dossier_count")


def _validate_source_summaries(report: TradeProposalReviewDossierBatchReport) -> None:
    if tuple(row.source_report_name for row in report.source_summaries) != SOURCE_REPORT_NAMES:
        raise ValueError("source_summaries must contain dossier sources")
    if len({row.source_report_name for row in report.source_summaries}) != len(
        report.source_summaries,
    ):
        raise ValueError("source_summaries must not contain duplicate sources")
    for row in report.source_summaries:
        if (
            row.complete_count
            + row.incomplete_count
            + row.inconsistent_count
            + row.unstable_count
            != report.dossier_count
        ):
            raise ValueError("source_summaries must match dossier_count")


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
    expected = _normalize_boundary_text(DEFAULT_REVIEW_DOSSIER_BATCH_BOUNDARY_STATEMENT)
    if normalized != expected:
        raise ValueError(
            "boundary_statement must describe report-only proposal-review dossier batch",
        )


def _normalize_boundary_text(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


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
