"""Report-only proposal evidence comparison history batch health trend artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health import (
    TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow,
)


__all__ = (
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_report",
)

DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT = (
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

ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.0001")
GATE_NAMES = (
    "batch_health_sample",
    "incomplete_batch_health_rate",
    "duplicate_generated_at_rate",
    "duplicate_fingerprint_rate",
)
NODE_11_GATE_NAMES = (
    "history_sample",
    "incomplete_history_rate",
    "divergent_history_rate",
    "unstable_history_rate",
    "duplicate_generated_at_rate",
    "duplicate_fingerprint_rate",
)
GATE_STATUSES = ("pass", "fail", "incomplete")
BATCH_HEALTH_STATUSES = (
    "divergent_history_batch_health",
    "duplicate_fingerprint_batch_health",
    "duplicate_generated_at_batch_health",
    "incomplete_history_batch_health",
    "proposal_evidence_comparison_history_batch_health_ready",
    "unstable_history_batch_health",
)
REPORT_STATUSES = (
    "incomplete_batch_health_trend",
    "duplicate_generated_at_batch_health_trend",
    "duplicate_fingerprint_batch_health_trend",
    "proposal_evidence_comparison_history_batch_health_trend_ready",
)
NODE_10_HISTORY_STATUSES = (
    "divergent_comparison_history",
    "incomplete_comparison_history",
    "proposal_evidence_comparison_history_ready",
    "unstable_comparison_history",
)
HISTORY_FINDINGS = (
    ("dossier_batch_incomplete", "incomplete", "dossier_batch"),
    ("dossier_batch_unstable", "unstable", "dossier_batch"),
    ("evidence_consistency_divergent", "divergent", "comparison"),
    ("forecast_evidence_incomplete", "incomplete", "forecast_evidence"),
    ("forecast_evidence_unstable", "unstable", "forecast_evidence"),
)
SOURCE_STATUSES = {
    "dossier_batch": (
        "incomplete_dossier_batch",
        "inconsistent_dossier_batch",
        "unstable_dossier_batch",
        "proposal_review_dossier_batch_ready",
    ),
    "forecast_evidence": (
        "incomplete_data",
        "insufficient_evidence",
        "blocked_by_quality",
        "paper_review_ready",
    ),
}


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig:
    config_version: str
    min_batch_health_report_count: int = 1
    max_incomplete_batch_health_ratio: Decimal = Decimal("0.0000")
    max_duplicate_generated_at_ratio: Decimal = Decimal("0.0000")
    max_duplicate_fingerprint_ratio: Decimal = Decimal("0.0000")
    boundary_statement: str = (
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT
    )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_batch_health_report_count",
            self.min_batch_health_report_count,
        )
        _require_probability_decimal(
            "max_incomplete_batch_health_ratio",
            self.max_incomplete_batch_health_ratio,
        )
        _require_probability_decimal(
            "max_duplicate_generated_at_ratio",
            self.max_duplicate_generated_at_ratio,
        )
        _require_probability_decimal(
            "max_duplicate_fingerprint_ratio",
            self.max_duplicate_fingerprint_ratio,
        )
        _require_boundary_statement(self.boundary_statement)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known batch health trend gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known batch health trend gate status")
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow:
    batch_health_status: str
    batch_health_count: int
    batch_health_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.batch_health_status not in BATCH_HEALTH_STATUSES:
            raise ValueError("batch_health_status must be known")
        _require_nonnegative_int("batch_health_count", self.batch_health_count)
        _require_optional_probability_decimal(
            "batch_health_ratio",
            self.batch_health_ratio,
        )


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary:
    batch_health_config_version: str
    batch_health_count: int

    def __post_init__(self) -> None:
        _require_canonical_string(
            "batch_health_config_version",
            self.batch_health_config_version,
        )
        _require_positive_int("batch_health_count", self.batch_health_count)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary:
    gate_name: str
    gate_status: str
    batch_health_count: int

    def __post_init__(self) -> None:
        if self.gate_name not in NODE_11_GATE_NAMES:
            raise ValueError("gate_name must be a known batch health gate")
        if self.gate_status not in GATE_STATUSES:
            raise ValueError("gate_status must be a known gate status")
        _require_positive_int("batch_health_count", self.batch_health_count)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary:
    generated_at: datetime
    duplicate_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_nonnegative_int("duplicate_count", self.duplicate_count)
        if self.duplicate_count < 2:
            raise ValueError("duplicate_count must be at least 2")


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary:
    report_fingerprint: str
    duplicate_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("report_fingerprint", self.report_fingerprint)
        _require_nonnegative_int("duplicate_count", self.duplicate_count)
        if self.duplicate_count < 2:
            raise ValueError("duplicate_count must be at least 2")


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    batch_health_report_count: int
    ready_batch_health_report_count: int
    incomplete_batch_health_report_count: int
    duplicate_generated_at_batch_health_report_count: int
    duplicate_fingerprint_batch_health_report_count: int
    divergent_batch_health_report_count: int
    unstable_batch_health_report_count: int
    duplicate_generated_at_count: int
    duplicate_fingerprint_count: int
    incomplete_batch_health_ratio: Decimal | None
    duplicate_generated_at_ratio: Decimal | None
    duplicate_fingerprint_ratio: Decimal | None
    first_batch_health_generated_at: datetime | None
    last_batch_health_generated_at: datetime | None
    status: str
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult, ...]
    status_rows: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow, ...]
    config_version_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary,
        ...,
    ]
    gate_status_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary,
        ...,
    ]
    duplicate_generated_at_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary,
        ...,
    ]
    duplicate_fingerprint_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary,
        ...,
    ]

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_batch_health_generated_at",
            _as_optional_utc(self.first_batch_health_generated_at),
        )
        object.__setattr__(
            self,
            "last_batch_health_generated_at",
            _as_optional_utc(self.last_batch_health_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        _require_boundary_statement(self.boundary_statement)
        for field_name in (
            "batch_health_report_count",
            "ready_batch_health_report_count",
            "incomplete_batch_health_report_count",
            "duplicate_generated_at_batch_health_report_count",
            "duplicate_fingerprint_batch_health_report_count",
            "divergent_batch_health_report_count",
            "unstable_batch_health_report_count",
            "duplicate_generated_at_count",
            "duplicate_fingerprint_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "incomplete_batch_health_ratio",
            "duplicate_generated_at_ratio",
            "duplicate_fingerprint_ratio",
        ):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known batch health trend status")
        object.__setattr__(
            self,
            "gate_results",
            _clone_trend_gate_results(self.gate_results),
        )
        object.__setattr__(self, "status_rows", _clone_status_rows(self.status_rows))
        object.__setattr__(
            self,
            "config_version_summaries",
            _clone_config_version_summaries(self.config_version_summaries),
        )
        object.__setattr__(
            self,
            "gate_status_summaries",
            _clone_gate_status_summaries(self.gate_status_summaries),
        )
        object.__setattr__(
            self,
            "duplicate_generated_at_summaries",
            _clone_duplicate_generated_at_summaries(
                self.duplicate_generated_at_summaries,
            ),
        )
        object.__setattr__(
            self,
            "duplicate_fingerprint_summaries",
            _clone_duplicate_fingerprint_summaries(
                self.duplicate_fingerprint_summaries,
            ),
        )
        _validate_trend_report_rows(self)
        if self.status != _trend_status(self.gate_results):
            raise ValueError("status must match batch health trend gate results")


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(
        self,
        report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
    ) -> None:
        if type(report) is not TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport:
            raise ValueError(
                "report must be a "
                "TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport"
            )
        validated = _validate_trend_report_tree(report)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True)
        line += "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_trade_proposal_evidence_comparison_history_batch_health_trend_report(
    batch_health_reports: (
        list[TradeProposalEvidenceComparisonHistoryBatchHealthReport]
        | tuple[TradeProposalEvidenceComparisonHistoryBatchHealthReport, ...]
    ),
    *,
    config: TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig,
    generated_at: datetime,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport:
    if type(config) is not TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig:
        raise ValueError(
            "config must be a TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig"
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    reports = _normalize_batch_health_report_inputs(batch_health_reports)
    total = len(reports)
    status_counts = _build_status_counts(reports)
    ready_count = status_counts[
        "proposal_evidence_comparison_history_batch_health_ready"
    ]
    incomplete_count = total - ready_count
    duplicate_generated_at_summaries = _duplicate_generated_at_summaries(reports)
    duplicate_fingerprint_summaries = _duplicate_fingerprint_summaries(reports)
    duplicate_generated_at_count = sum(
        row.duplicate_count for row in duplicate_generated_at_summaries
    )
    duplicate_fingerprint_count = sum(
        row.duplicate_count for row in duplicate_fingerprint_summaries
    )
    incomplete_ratio = _ratio(incomplete_count, total)
    duplicate_generated_at_ratio = _ratio(duplicate_generated_at_count, total)
    duplicate_fingerprint_ratio = _ratio(duplicate_fingerprint_count, total)
    gate_results = _build_gate_results(
        batch_health_report_count=total,
        incomplete_ratio=incomplete_ratio,
        duplicate_generated_at_ratio=duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=duplicate_fingerprint_ratio,
        config=config,
    )
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_only=True,
        boundary_statement=config.boundary_statement,
        batch_health_report_count=total,
        ready_batch_health_report_count=ready_count,
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
        first_batch_health_generated_at=reports[0].generated_at if reports else None,
        last_batch_health_generated_at=reports[-1].generated_at if reports else None,
        status=_trend_status(gate_results),
        gate_results=gate_results,
        status_rows=_build_status_rows(status_counts, total),
        config_version_summaries=_config_version_summaries(reports),
        gate_status_summaries=_gate_status_summaries(reports),
        duplicate_generated_at_summaries=duplicate_generated_at_summaries,
        duplicate_fingerprint_summaries=duplicate_fingerprint_summaries,
    )


def _normalize_batch_health_report_inputs(
    batch_health_reports: (
        list[TradeProposalEvidenceComparisonHistoryBatchHealthReport]
        | tuple[TradeProposalEvidenceComparisonHistoryBatchHealthReport, ...]
    ),
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthReport, ...]:
    if type(batch_health_reports) not in (list, tuple):
        raise ValueError(
            "batch_health_reports must be a list or tuple of batch health reports"
        )
    supplied = tuple(batch_health_reports)
    cloned = tuple(_clone_batch_health_report(item) for item in supplied)
    return tuple(
        sorted(
            cloned,
            key=lambda report: (
                report.generated_at,
                report.config_version,
                report.status,
            ),
        )
    )


def _clone_batch_health_report(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthReport,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthReport:
    if type(report) is not TradeProposalEvidenceComparisonHistoryBatchHealthReport:
        raise ValueError(
            "batch_health_reports must contain "
            "TradeProposalEvidenceComparisonHistoryBatchHealthReport values"
        )
    gate_results = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in _normalize_typed_tuple(
            "gate_results",
            report.gate_results,
            TradeProposalEvidenceComparisonHistoryBatchHealthGateResult,
        )
    )
    status_rows = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow(
            history_status=row.history_status,
            history_count=row.history_count,
            history_ratio=row.history_ratio,
        )
        for row in _normalize_typed_tuple(
            "status_rows",
            report.status_rows,
            TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow,
        )
    )
    config_version_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary(
            history_config_version=row.history_config_version,
            history_count=row.history_count,
        )
        for row in _normalize_typed_tuple(
            "config_version_summaries",
            report.config_version_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary,
        )
    )
    duplicate_generated_at_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary(
            generated_at=row.generated_at,
            duplicate_count=row.duplicate_count,
        )
        for row in _normalize_typed_tuple(
            "duplicate_generated_at_summaries",
            report.duplicate_generated_at_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary,
        )
    )
    duplicate_fingerprint_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary(
            report_fingerprint=row.report_fingerprint,
            duplicate_count=row.duplicate_count,
        )
        for row in _normalize_typed_tuple(
            "duplicate_fingerprint_summaries",
            report.duplicate_fingerprint_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary,
        )
    )
    finding_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary(
            finding_code=row.finding_code,
            severity=row.severity,
            source_name=row.source_name,
            history_count=row.history_count,
        )
        for row in _normalize_typed_tuple(
            "finding_summaries",
            report.finding_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary,
        )
    )
    source_transition_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary(
            source_name=row.source_name,
            from_source_status=row.from_source_status,
            to_source_status=row.to_source_status,
            transition_count=row.transition_count,
        )
        for row in _normalize_typed_tuple(
            "source_transition_summaries",
            report.source_transition_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary,
        )
    )
    return TradeProposalEvidenceComparisonHistoryBatchHealthReport(
        generated_at=_as_utc(report.generated_at),
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        history_report_count=report.history_report_count,
        complete_history_report_count=report.complete_history_report_count,
        incomplete_history_report_count=report.incomplete_history_report_count,
        divergent_history_report_count=report.divergent_history_report_count,
        unstable_history_report_count=report.unstable_history_report_count,
        duplicate_generated_at_count=report.duplicate_generated_at_count,
        duplicate_fingerprint_count=report.duplicate_fingerprint_count,
        incomplete_history_ratio=report.incomplete_history_ratio,
        divergent_history_ratio=report.divergent_history_ratio,
        unstable_history_ratio=report.unstable_history_ratio,
        duplicate_generated_at_ratio=report.duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=report.duplicate_fingerprint_ratio,
        first_history_generated_at=report.first_history_generated_at,
        last_history_generated_at=report.last_history_generated_at,
        status=report.status,
        gate_results=gate_results,
        status_rows=status_rows,
        config_version_summaries=config_version_summaries,
        duplicate_generated_at_summaries=duplicate_generated_at_summaries,
        duplicate_fingerprint_summaries=duplicate_fingerprint_summaries,
        finding_summaries=finding_summaries,
        source_transition_summaries=source_transition_summaries,
    )


def _build_status_counts(
    reports: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthReport, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in BATCH_HEALTH_STATUSES}
    for report in reports:
        counts[report.status] += 1
    return counts


def _build_gate_results(
    *,
    batch_health_report_count: int,
    incomplete_ratio: Decimal | None,
    duplicate_generated_at_ratio: Decimal | None,
    duplicate_fingerprint_ratio: Decimal | None,
    config: TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig,
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult, ...]:
    sample_passes = batch_health_report_count >= config.min_batch_health_report_count
    return (
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult(
            "batch_health_sample",
            "pass" if sample_passes else "incomplete",
            (
                "Supplied batch-health report sample meets the threshold."
                if sample_passes
                else "Supplied batch-health report sample is below the threshold."
            ),
            batch_health_report_count,
            config.min_batch_health_report_count,
        ),
        _rate_gate(
            "incomplete_batch_health_rate",
            incomplete_ratio,
            config.max_incomplete_batch_health_ratio,
            "Incomplete batch-health",
        ),
        _rate_gate(
            "duplicate_generated_at_rate",
            duplicate_generated_at_ratio,
            config.max_duplicate_generated_at_ratio,
            "Duplicate generated-at",
        ),
        _rate_gate(
            "duplicate_fingerprint_rate",
            duplicate_fingerprint_ratio,
            config.max_duplicate_fingerprint_ratio,
            "Duplicate fingerprint",
        ),
    )


def _rate_gate(
    gate_name: str,
    ratio: Decimal | None,
    threshold: Decimal,
    label: str,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult:
    if ratio is None:
        status = "incomplete"
        message = f"{label} rate is unavailable without batch-health reports."
    elif ratio <= threshold:
        status = "pass"
        message = f"{label} rate is within the threshold."
    else:
        status = "fail"
        message = f"{label} rate exceeds the threshold."
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult(
        gate_name,
        status,
        message,
        ratio,
        threshold,
    )


def _build_status_rows(
    status_counts: dict[str, int],
    total: int,
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow(
            status,
            status_counts[status],
            _ratio(status_counts[status], total),
        )
        for status in BATCH_HEALTH_STATUSES
    )


def _config_version_summaries(
    reports: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthReport, ...],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary,
    ...,
]:
    counts: dict[str, int] = {}
    for report in reports:
        counts[report.config_version] = counts.get(report.config_version, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary(
            config_version,
            count,
        )
        for config_version, count in sorted(counts.items())
    )


def _gate_status_summaries(
    reports: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthReport, ...],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary,
    ...,
]:
    counts: dict[tuple[str, str], int] = {}
    for report in reports:
        report_keys = {(row.gate_name, row.status) for row in report.gate_results}
        for key in report_keys:
            counts[key] = counts.get(key, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
            gate_name,
            gate_status,
            count,
        )
        for (gate_name, gate_status), count in sorted(counts.items())
    )


def _duplicate_generated_at_summaries(
    reports: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthReport, ...],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary,
    ...,
]:
    counts: dict[datetime, int] = {}
    for report in reports:
        counts[report.generated_at] = counts.get(report.generated_at, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary(
            generated_at,
            count,
        )
        for generated_at, count in sorted(counts.items())
        if count >= 2
    )


def _duplicate_fingerprint_summaries(
    reports: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthReport, ...],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary,
    ...,
]:
    counts: dict[str, int] = {}
    for report in reports:
        fingerprint = _batch_health_report_fingerprint(report)
        counts[fingerprint] = counts.get(fingerprint, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary(
            fingerprint,
            count,
        )
        for fingerprint, count in sorted(counts.items())
        if count >= 2
    )


def _batch_health_report_fingerprint(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthReport,
) -> str:
    return json.dumps(_json_ready(asdict(report)), allow_nan=False, sort_keys=True)


def _trend_status(
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult, ...],
) -> str:
    gates = {row.gate_name: row.status for row in gate_results}
    if gates["batch_health_sample"] == "incomplete":
        return "incomplete_batch_health_trend"
    if gates["duplicate_generated_at_rate"] == "fail":
        return "duplicate_generated_at_batch_health_trend"
    if gates["duplicate_fingerprint_rate"] == "fail":
        return "duplicate_fingerprint_batch_health_trend"
    if gates["incomplete_batch_health_rate"] == "fail":
        return "incomplete_batch_health_trend"
    if any(status == "incomplete" for status in gates.values()):
        return "incomplete_batch_health_trend"
    return "proposal_evidence_comparison_history_batch_health_trend_ready"


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _validate_trend_report_tree(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport:
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        batch_health_report_count=report.batch_health_report_count,
        ready_batch_health_report_count=report.ready_batch_health_report_count,
        incomplete_batch_health_report_count=report.incomplete_batch_health_report_count,
        duplicate_generated_at_batch_health_report_count=(
            report.duplicate_generated_at_batch_health_report_count
        ),
        duplicate_fingerprint_batch_health_report_count=(
            report.duplicate_fingerprint_batch_health_report_count
        ),
        divergent_batch_health_report_count=report.divergent_batch_health_report_count,
        unstable_batch_health_report_count=report.unstable_batch_health_report_count,
        duplicate_generated_at_count=report.duplicate_generated_at_count,
        duplicate_fingerprint_count=report.duplicate_fingerprint_count,
        incomplete_batch_health_ratio=report.incomplete_batch_health_ratio,
        duplicate_generated_at_ratio=report.duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=report.duplicate_fingerprint_ratio,
        first_batch_health_generated_at=report.first_batch_health_generated_at,
        last_batch_health_generated_at=report.last_batch_health_generated_at,
        status=report.status,
        gate_results=report.gate_results,
        status_rows=report.status_rows,
        config_version_summaries=report.config_version_summaries,
        gate_status_summaries=report.gate_status_summaries,
        duplicate_generated_at_summaries=report.duplicate_generated_at_summaries,
        duplicate_fingerprint_summaries=report.duplicate_fingerprint_summaries,
    )


def _validate_trend_report_rows(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
) -> None:
    if tuple(row.gate_name for row in report.gate_results) != GATE_NAMES:
        raise ValueError("gate_results must contain batch health trend gates")
    status_row_keys = tuple(row.batch_health_status for row in report.status_rows)
    if status_row_keys != BATCH_HEALTH_STATUSES:
        raise ValueError("status_rows must contain sorted batch health statuses")
    status_counts = {
        row.batch_health_status: row.batch_health_count for row in report.status_rows
    }
    if status_counts["proposal_evidence_comparison_history_batch_health_ready"] != (
        report.ready_batch_health_report_count
    ):
        raise ValueError("status_rows must match ready batch health count")
    if status_counts["incomplete_history_batch_health"] != (
        report.incomplete_batch_health_report_count
    ):
        raise ValueError("status_rows must match incomplete batch health count")
    if status_counts["duplicate_generated_at_batch_health"] != (
        report.duplicate_generated_at_batch_health_report_count
    ):
        raise ValueError("status_rows must match duplicate generated-at status count")
    if status_counts["duplicate_fingerprint_batch_health"] != (
        report.duplicate_fingerprint_batch_health_report_count
    ):
        raise ValueError("status_rows must match duplicate fingerprint status count")
    if status_counts["divergent_history_batch_health"] != (
        report.divergent_batch_health_report_count
    ):
        raise ValueError("status_rows must match divergent batch health count")
    if status_counts["unstable_history_batch_health"] != (
        report.unstable_batch_health_report_count
    ):
        raise ValueError("status_rows must match unstable batch health count")
    if sum(status_counts.values()) != report.batch_health_report_count:
        raise ValueError("status_rows must sum to batch_health_report_count")
    expected_ratios = {
        status: _ratio(count, report.batch_health_report_count)
        for status, count in status_counts.items()
    }
    for row in report.status_rows:
        if row.batch_health_ratio != expected_ratios[row.batch_health_status]:
            raise ValueError("status_rows must contain expected ratios")
    expected_incomplete = report.batch_health_report_count - (
        report.ready_batch_health_report_count
    )
    _validate_ratio_field(
        report,
        "incomplete_batch_health_ratio",
        expected_incomplete,
    )
    _validate_duplicate_summaries(report)
    _validate_time_bounds(report)
    _validate_config_version_summaries(report)
    _validate_gate_status_summaries(report)
    _validate_gate_payloads(report)


def _validate_ratio_field(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
    field_name: str,
    count: int,
) -> None:
    expected = _ratio(count, report.batch_health_report_count)
    if getattr(report, field_name) != expected:
        raise ValueError(f"{field_name} must match derived ratio")


def _validate_time_bounds(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
) -> None:
    if report.batch_health_report_count == 0:
        if (
            report.first_batch_health_generated_at is not None
            or report.last_batch_health_generated_at is not None
        ):
            raise ValueError("batch health time bounds must be empty without reports")
    else:
        if (
            report.first_batch_health_generated_at is None
            or report.last_batch_health_generated_at is None
        ):
            raise ValueError("batch health time bounds must be present with reports")
        if report.first_batch_health_generated_at > report.last_batch_health_generated_at:
            raise ValueError("batch health time bounds must be ordered")


def _validate_duplicate_summaries(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
) -> None:
    generated_at_keys = tuple(
        row.generated_at for row in report.duplicate_generated_at_summaries
    )
    if generated_at_keys != tuple(sorted(generated_at_keys)):
        raise ValueError("duplicate_generated_at_summaries must be sorted")
    if len(set(generated_at_keys)) != len(generated_at_keys):
        raise ValueError("duplicate_generated_at_summaries must not contain duplicates")
    fingerprint_keys = tuple(
        row.report_fingerprint for row in report.duplicate_fingerprint_summaries
    )
    if fingerprint_keys != tuple(sorted(fingerprint_keys)):
        raise ValueError("duplicate_fingerprint_summaries must be sorted")
    if len(set(fingerprint_keys)) != len(fingerprint_keys):
        raise ValueError("duplicate_fingerprint_summaries must not contain duplicates")
    for row in report.duplicate_generated_at_summaries:
        if row.duplicate_count > report.batch_health_report_count:
            raise ValueError("duplicate_generated_at_summaries must not exceed count")
    for row in report.duplicate_fingerprint_summaries:
        if row.duplicate_count > report.batch_health_report_count:
            raise ValueError("duplicate_fingerprint_summaries must not exceed count")
    if report.duplicate_generated_at_count != sum(
        row.duplicate_count for row in report.duplicate_generated_at_summaries
    ):
        raise ValueError("duplicate_generated_at_count must match duplicate summaries")
    if report.duplicate_fingerprint_count != sum(
        row.duplicate_count for row in report.duplicate_fingerprint_summaries
    ):
        raise ValueError("duplicate_fingerprint_count must match duplicate summaries")
    _validate_ratio_field(
        report,
        "duplicate_generated_at_ratio",
        report.duplicate_generated_at_count,
    )
    _validate_ratio_field(
        report,
        "duplicate_fingerprint_ratio",
        report.duplicate_fingerprint_count,
    )


def _validate_config_version_summaries(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
) -> None:
    versions = tuple(
        row.batch_health_config_version for row in report.config_version_summaries
    )
    if versions != tuple(sorted(versions)):
        raise ValueError("config_version_summaries must be sorted")
    if len(set(versions)) != len(versions):
        raise ValueError("config_version_summaries must not contain duplicates")
    if sum(row.batch_health_count for row in report.config_version_summaries) != (
        report.batch_health_report_count
    ):
        raise ValueError("config_version_summaries must sum to report count")


def _validate_gate_status_summaries(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
) -> None:
    keys = tuple(
        (row.gate_name, row.gate_status) for row in report.gate_status_summaries
    )
    if keys != tuple(sorted(keys)):
        raise ValueError("gate_status_summaries must be sorted")
    if len(set(keys)) != len(keys):
        raise ValueError("gate_status_summaries must not contain duplicates")
    expected_gate_status_count = (
        len(NODE_11_GATE_NAMES) * report.batch_health_report_count
    )
    observed_gate_status_count = sum(
        row.batch_health_count for row in report.gate_status_summaries
    )
    if observed_gate_status_count != expected_gate_status_count:
        raise ValueError("gate_status_summaries must account for all gate rows")
    for gate_name in NODE_11_GATE_NAMES:
        gate_count = sum(
            row.batch_health_count
            for row in report.gate_status_summaries
            if row.gate_name == gate_name
        )
        if gate_count != report.batch_health_report_count:
            raise ValueError("gate_status_summaries must account for every gate")
    for row in report.gate_status_summaries:
        if row.batch_health_count > report.batch_health_report_count:
            raise ValueError("gate_status_summaries must not exceed report count")


def _validate_gate_payloads(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport,
) -> None:
    gates = {row.gate_name: row for row in report.gate_results}
    sample_gate = gates["batch_health_sample"]
    if type(sample_gate.observed_value) is not int:
        raise ValueError("gate_results batch_health_sample observed_value must be an int")
    if sample_gate.observed_value != report.batch_health_report_count:
        raise ValueError("gate_results must match batch_health_report_count")
    if type(sample_gate.threshold) is not int:
        raise ValueError("gate_results batch_health_sample threshold must be an int")
    _require_nonnegative_int(
        "gate_results batch_health_sample threshold",
        sample_gate.threshold,
    )
    expected_sample_status = (
        "pass"
        if report.batch_health_report_count >= sample_gate.threshold
        else "incomplete"
    )
    if sample_gate.status != expected_sample_status:
        raise ValueError("gate_results batch_health_sample status must match threshold")
    _validate_rate_gate_payload(
        gates["incomplete_batch_health_rate"],
        report.incomplete_batch_health_ratio,
        "gate_results incomplete_batch_health_rate",
    )
    _validate_rate_gate_payload(
        gates["duplicate_generated_at_rate"],
        report.duplicate_generated_at_ratio,
        "gate_results duplicate_generated_at_rate",
    )
    _validate_rate_gate_payload(
        gates["duplicate_fingerprint_rate"],
        report.duplicate_fingerprint_ratio,
        "gate_results duplicate_fingerprint_rate",
    )


def _validate_rate_gate_payload(
    gate: TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult,
    ratio: Decimal | None,
    field_name: str,
) -> None:
    if type(gate.threshold) is not Decimal:
        raise ValueError(f"{field_name} threshold must be a Decimal")
    _require_probability_decimal(f"{field_name} threshold", gate.threshold)
    if ratio is None:
        if gate.observed_value is not None:
            raise ValueError(f"{field_name} observed_value must match report ratio")
        if gate.status != "incomplete":
            raise ValueError(f"{field_name} status must be incomplete")
        return
    if type(gate.observed_value) is not Decimal:
        raise ValueError(f"{field_name} observed_value must be a Decimal")
    if gate.observed_value != ratio:
        raise ValueError(f"{field_name} observed_value must match report ratio")
    expected_status = "pass" if ratio <= gate.threshold else "fail"
    if gate.status != expected_status:
        raise ValueError(f"{field_name} status must match threshold")


def _clone_trend_gate_results(
    gate_results: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult,
        ...,
    ],
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult(
            row.gate_name,
            row.status,
            row.message,
            row.observed_value,
            row.threshold,
        )
        for row in _normalize_typed_tuple(
            "gate_results",
            gate_results,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult,
        )
    )


def _clone_status_rows(
    status_rows: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow,
        ...,
    ],
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow(
            row.batch_health_status,
            row.batch_health_count,
            row.batch_health_ratio,
        )
        for row in _normalize_typed_tuple(
            "status_rows",
            status_rows,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow,
        )
    )


def _clone_config_version_summaries(
    summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary,
        ...,
    ],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary,
    ...,
]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary(
            row.batch_health_config_version,
            row.batch_health_count,
        )
        for row in _normalize_typed_tuple(
            "config_version_summaries",
            summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary,
        )
    )


def _clone_gate_status_summaries(
    summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary,
        ...,
    ],
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary(
            row.gate_name,
            row.gate_status,
            row.batch_health_count,
        )
        for row in _normalize_typed_tuple(
            "gate_status_summaries",
            summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary,
        )
    )


def _clone_duplicate_generated_at_summaries(
    summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary,
        ...,
    ],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary,
    ...,
]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary(
            row.generated_at,
            row.duplicate_count,
        )
        for row in _normalize_typed_tuple(
            "duplicate_generated_at_summaries",
            summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary,
        )
    )


def _clone_duplicate_fingerprint_summaries(
    summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary,
        ...,
    ],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary,
    ...,
]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary(
            row.report_fingerprint,
            row.duplicate_count,
        )
        for row in _normalize_typed_tuple(
            "duplicate_fingerprint_summaries",
            summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary,
        )
    )


def _normalize_typed_tuple(
    field_name: str,
    value: tuple[Any, ...],
    expected_type: type,
) -> tuple[Any, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        if type(item) is not expected_type:
            raise ValueError(f"{field_name} must contain {expected_type.__name__} values")
    return value


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(value)


def _normalize_boundary(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _require_boundary_statement(value: str) -> None:
    _require_canonical_string("boundary_statement", value)
    if _normalize_boundary(value) != _normalize_boundary(
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BOUNDARY_STATEMENT
    ):
        raise ValueError(
            "boundary_statement must describe report-only proposal evidence comparison "
            "history batch health trend"
        )


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: int) -> None:
    _require_nonnegative_int(field_name, value)
    if value == 0:
        raise ValueError(f"{field_name} must be positive")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_probability_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
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
    if isinstance(value, Decimal):
        _require_decimal(field_name, value)
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if isinstance(value, str):
        _require_canonical_string(field_name, value)
        return
    raise ValueError(f"{field_name} must be a Decimal, int, string, or None")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        _require_decimal("Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("float values are not JSON serializable")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value must be JSON serializable")


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
    parent = path.parent
    while not parent.exists():
        if parent == parent.parent:
            break
        parent = parent.parent
    if parent.exists() and not parent.is_dir():
        raise ValueError("parent path must be a directory")
