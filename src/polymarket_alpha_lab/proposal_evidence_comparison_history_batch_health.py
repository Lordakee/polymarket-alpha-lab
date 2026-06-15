"""Report-only proposal evidence comparison history batch health artifacts for Level 2."""

from __future__ import annotations

from collections.abc import Iterable
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.proposal_evidence_comparison_history import (
    TradeProposalEvidenceComparisonHistoryConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryFindingSummary,
    TradeProposalEvidenceComparisonHistoryGateResult,
    TradeProposalEvidenceComparisonHistoryReport,
    TradeProposalEvidenceComparisonHistorySourceTransition,
    TradeProposalEvidenceComparisonHistoryStatusRow,
)


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

ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.0001")
GATE_NAMES = (
    "history_sample",
    "incomplete_history_rate",
    "divergent_history_rate",
    "unstable_history_rate",
    "duplicate_generated_at_rate",
    "duplicate_fingerprint_rate",
)
GATE_STATUSES = ("pass", "fail", "incomplete")
HISTORY_STATUSES = (
    "divergent_comparison_history",
    "incomplete_comparison_history",
    "proposal_evidence_comparison_history_ready",
    "unstable_comparison_history",
)
REPORT_STATUSES = (
    "incomplete_history_batch_health",
    "duplicate_generated_at_batch_health",
    "duplicate_fingerprint_batch_health",
    "divergent_history_batch_health",
    "unstable_history_batch_health",
    "proposal_evidence_comparison_history_batch_health_ready",
)
FINDING_SEVERITIES = ("divergent", "incomplete", "unstable")
SOURCE_NAMES = ("dossier_batch", "forecast_evidence")
FINDING_SOURCE_NAMES = ("comparison", *SOURCE_NAMES)
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

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_history_report_count",
            self.min_history_report_count,
        )
        _require_probability_decimal(
            "max_incomplete_history_ratio",
            self.max_incomplete_history_ratio,
        )
        _require_probability_decimal(
            "max_divergent_history_ratio",
            self.max_divergent_history_ratio,
        )
        _require_probability_decimal(
            "max_unstable_history_ratio",
            self.max_unstable_history_ratio,
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
class TradeProposalEvidenceComparisonHistoryBatchHealthGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known batch health gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known batch health gate status")
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow:
    history_status: str
    history_count: int
    history_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.history_status not in HISTORY_STATUSES:
            raise ValueError("history_status must be a known comparison history status")
        _require_nonnegative_int("history_count", self.history_count)
        _require_optional_probability_decimal("history_ratio", self.history_ratio)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary:
    history_config_version: str
    history_count: int

    def __post_init__(self) -> None:
        _require_canonical_string(
            "history_config_version",
            self.history_config_version,
        )
        _require_positive_int("history_count", self.history_count)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary:
    generated_at: datetime
    duplicate_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_nonnegative_int("duplicate_count", self.duplicate_count)
        if self.duplicate_count < 2:
            raise ValueError("duplicate_count must be at least 2")


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary:
    report_fingerprint: str
    duplicate_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("report_fingerprint", self.report_fingerprint)
        _require_nonnegative_int("duplicate_count", self.duplicate_count)
        if self.duplicate_count < 2:
            raise ValueError("duplicate_count must be at least 2")


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary:
    finding_code: str
    severity: str
    source_name: str
    history_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("finding_code", self.finding_code)
        if self.severity not in FINDING_SEVERITIES:
            raise ValueError("severity must be a known batch health severity")
        if self.source_name not in FINDING_SOURCE_NAMES:
            raise ValueError("source_name must be a known finding source")
        _require_history_finding_tuple(
            self.finding_code,
            self.severity,
            self.source_name,
        )
        _require_positive_int("history_count", self.history_count)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary:
    source_name: str
    from_source_status: str
    to_source_status: str
    transition_count: int

    def __post_init__(self) -> None:
        if self.source_name not in SOURCE_NAMES:
            raise ValueError("source_name must be a known comparison source")
        _require_canonical_string("from_source_status", self.from_source_status)
        _require_canonical_string("to_source_status", self.to_source_status)
        _require_source_status(self.source_name, self.from_source_status)
        _require_source_status(self.source_name, self.to_source_status)
        _require_positive_int("transition_count", self.transition_count)


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

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_history_generated_at",
            _as_optional_utc(self.first_history_generated_at),
        )
        object.__setattr__(
            self,
            "last_history_generated_at",
            _as_optional_utc(self.last_history_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        _require_boundary_statement(self.boundary_statement)
        for field_name in (
            "history_report_count",
            "complete_history_report_count",
            "incomplete_history_report_count",
            "divergent_history_report_count",
            "unstable_history_report_count",
            "duplicate_generated_at_count",
            "duplicate_fingerprint_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "incomplete_history_ratio",
            "divergent_history_ratio",
            "unstable_history_ratio",
            "duplicate_generated_at_ratio",
            "duplicate_fingerprint_ratio",
        ):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known batch health status")
        object.__setattr__(
            self,
            "gate_results",
            _clone_batch_health_gate_results(self.gate_results),
        )
        object.__setattr__(
            self,
            "status_rows",
            _clone_status_rows(self.status_rows),
        )
        object.__setattr__(
            self,
            "config_version_summaries",
            _clone_config_version_summaries(self.config_version_summaries),
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
        object.__setattr__(
            self,
            "finding_summaries",
            _clone_finding_summaries(self.finding_summaries),
        )
        object.__setattr__(
            self,
            "source_transition_summaries",
            _clone_source_transition_summaries(self.source_transition_summaries),
        )
        _validate_batch_health_report_rows(self)
        if self.status != _batch_health_status(self.gate_results):
            raise ValueError("status must match batch health gate results")


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(
        self,
        report: TradeProposalEvidenceComparisonHistoryBatchHealthReport,
    ) -> None:
        if type(report) is not TradeProposalEvidenceComparisonHistoryBatchHealthReport:
            raise ValueError(
                "report must be a "
                "TradeProposalEvidenceComparisonHistoryBatchHealthReport"
            )
        validated = _validate_batch_health_report_tree(report)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True)
        line += "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_trade_proposal_evidence_comparison_history_batch_health_report(
    history_reports: Iterable[TradeProposalEvidenceComparisonHistoryReport],
    *,
    config: TradeProposalEvidenceComparisonHistoryBatchHealthConfig,
    generated_at: datetime,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthReport:
    if type(config) is not TradeProposalEvidenceComparisonHistoryBatchHealthConfig:
        raise ValueError(
            "config must be a TradeProposalEvidenceComparisonHistoryBatchHealthConfig"
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    reports = _normalize_history_report_inputs(history_reports)
    history_report_count = len(reports)
    status_counts = _build_status_counts(reports)
    complete_count = status_counts["proposal_evidence_comparison_history_ready"]
    incomplete_count = status_counts["incomplete_comparison_history"]
    divergent_count = status_counts["divergent_comparison_history"]
    unstable_count = status_counts["unstable_comparison_history"]
    duplicate_generated_at_summaries = _duplicate_generated_at_summaries(reports)
    duplicate_fingerprint_summaries = _duplicate_fingerprint_summaries(reports)
    duplicate_generated_at_count = sum(
        row.duplicate_count for row in duplicate_generated_at_summaries
    )
    duplicate_fingerprint_count = sum(
        row.duplicate_count for row in duplicate_fingerprint_summaries
    )
    incomplete_ratio = _ratio(incomplete_count, history_report_count)
    divergent_ratio = _ratio(divergent_count, history_report_count)
    unstable_ratio = _ratio(unstable_count, history_report_count)
    duplicate_generated_at_ratio = _ratio(
        duplicate_generated_at_count,
        history_report_count,
    )
    duplicate_fingerprint_ratio = _ratio(
        duplicate_fingerprint_count,
        history_report_count,
    )
    gate_results = _build_gate_results(
        history_report_count=history_report_count,
        incomplete_ratio=incomplete_ratio,
        divergent_ratio=divergent_ratio,
        unstable_ratio=unstable_ratio,
        duplicate_generated_at_ratio=duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=duplicate_fingerprint_ratio,
        config=config,
    )
    return TradeProposalEvidenceComparisonHistoryBatchHealthReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_only=True,
        boundary_statement=config.boundary_statement,
        history_report_count=history_report_count,
        complete_history_report_count=complete_count,
        incomplete_history_report_count=incomplete_count,
        divergent_history_report_count=divergent_count,
        unstable_history_report_count=unstable_count,
        duplicate_generated_at_count=duplicate_generated_at_count,
        duplicate_fingerprint_count=duplicate_fingerprint_count,
        incomplete_history_ratio=incomplete_ratio,
        divergent_history_ratio=divergent_ratio,
        unstable_history_ratio=unstable_ratio,
        duplicate_generated_at_ratio=duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=duplicate_fingerprint_ratio,
        first_history_generated_at=reports[0].generated_at if reports else None,
        last_history_generated_at=reports[-1].generated_at if reports else None,
        status=_batch_health_status(gate_results),
        gate_results=gate_results,
        status_rows=_build_status_rows(status_counts, history_report_count),
        config_version_summaries=_config_version_summaries(reports),
        duplicate_generated_at_summaries=duplicate_generated_at_summaries,
        duplicate_fingerprint_summaries=duplicate_fingerprint_summaries,
        finding_summaries=_finding_summaries(reports),
        source_transition_summaries=_source_transition_summaries(reports),
    )


def _normalize_history_report_inputs(
    history_reports: Iterable[TradeProposalEvidenceComparisonHistoryReport],
) -> tuple[TradeProposalEvidenceComparisonHistoryReport, ...]:
    if type(history_reports) not in (list, tuple):
        raise ValueError("history_reports must be a list or tuple of history reports")
    supplied = tuple(history_reports)
    cloned = tuple(_clone_history_report(item) for item in supplied)
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


def _clone_history_report(
    report: TradeProposalEvidenceComparisonHistoryReport,
) -> TradeProposalEvidenceComparisonHistoryReport:
    if type(report) is not TradeProposalEvidenceComparisonHistoryReport:
        raise ValueError(
            "history_reports must contain "
            "TradeProposalEvidenceComparisonHistoryReport values"
        )
    gate_results = tuple(
        TradeProposalEvidenceComparisonHistoryGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in _normalize_typed_tuple(
            "gate_results",
            report.gate_results,
            TradeProposalEvidenceComparisonHistoryGateResult,
        )
    )
    status_rows = tuple(
        TradeProposalEvidenceComparisonHistoryStatusRow(
            comparison_status=row.comparison_status,
            comparison_count=row.comparison_count,
            comparison_ratio=row.comparison_ratio,
        )
        for row in _normalize_typed_tuple(
            "status_rows",
            report.status_rows,
            TradeProposalEvidenceComparisonHistoryStatusRow,
        )
    )
    finding_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryFindingSummary(
            finding_code=row.finding_code,
            severity=row.severity,
            source_name=row.source_name,
            comparison_count=row.comparison_count,
        )
        for row in _normalize_typed_tuple(
            "finding_summaries",
            report.finding_summaries,
            TradeProposalEvidenceComparisonHistoryFindingSummary,
        )
    )
    config_version_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryConfigVersionSummary(
            comparison_config_version=row.comparison_config_version,
            comparison_count=row.comparison_count,
        )
        for row in _normalize_typed_tuple(
            "config_version_summaries",
            report.config_version_summaries,
            TradeProposalEvidenceComparisonHistoryConfigVersionSummary,
        )
    )
    source_transitions = tuple(
        TradeProposalEvidenceComparisonHistorySourceTransition(
            source_name=row.source_name,
            from_source_status=row.from_source_status,
            to_source_status=row.to_source_status,
            transition_count=row.transition_count,
        )
        for row in _normalize_typed_tuple(
            "source_transitions",
            report.source_transitions,
            TradeProposalEvidenceComparisonHistorySourceTransition,
        )
    )
    return TradeProposalEvidenceComparisonHistoryReport(
        generated_at=_as_utc(report.generated_at),
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        comparison_count=report.comparison_count,
        complete_comparison_count=report.complete_comparison_count,
        incomplete_comparison_count=report.incomplete_comparison_count,
        divergent_comparison_count=report.divergent_comparison_count,
        unstable_comparison_count=report.unstable_comparison_count,
        incomplete_comparison_ratio=report.incomplete_comparison_ratio,
        divergent_comparison_ratio=report.divergent_comparison_ratio,
        unstable_comparison_ratio=report.unstable_comparison_ratio,
        first_comparison_generated_at=report.first_comparison_generated_at,
        last_comparison_generated_at=report.last_comparison_generated_at,
        status=report.status,
        gate_results=gate_results,
        status_rows=status_rows,
        finding_summaries=finding_summaries,
        config_version_summaries=config_version_summaries,
        source_transitions=source_transitions,
    )


def _build_status_counts(
    reports: tuple[TradeProposalEvidenceComparisonHistoryReport, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in HISTORY_STATUSES}
    for report in reports:
        counts[report.status] += 1
    return counts


def _build_gate_results(
    *,
    history_report_count: int,
    incomplete_ratio: Decimal | None,
    divergent_ratio: Decimal | None,
    unstable_ratio: Decimal | None,
    duplicate_generated_at_ratio: Decimal | None,
    duplicate_fingerprint_ratio: Decimal | None,
    config: TradeProposalEvidenceComparisonHistoryBatchHealthConfig,
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthGateResult, ...]:
    sample_passes = history_report_count >= config.min_history_report_count
    return (
        TradeProposalEvidenceComparisonHistoryBatchHealthGateResult(
            gate_name="history_sample",
            status="pass" if sample_passes else "incomplete",
            message=(
                "Supplied history report sample meets the threshold."
                if sample_passes
                else "Supplied history report sample is below the threshold."
            ),
            observed_value=history_report_count,
            threshold=config.min_history_report_count,
        ),
        _rate_gate(
            gate_name="incomplete_history_rate",
            ratio=incomplete_ratio,
            threshold=config.max_incomplete_history_ratio,
            label="Incomplete history",
        ),
        _rate_gate(
            gate_name="divergent_history_rate",
            ratio=divergent_ratio,
            threshold=config.max_divergent_history_ratio,
            label="Divergent history",
        ),
        _rate_gate(
            gate_name="unstable_history_rate",
            ratio=unstable_ratio,
            threshold=config.max_unstable_history_ratio,
            label="Unstable history",
        ),
        _rate_gate(
            gate_name="duplicate_generated_at_rate",
            ratio=duplicate_generated_at_ratio,
            threshold=config.max_duplicate_generated_at_ratio,
            label="Duplicate generated-at",
        ),
        _rate_gate(
            gate_name="duplicate_fingerprint_rate",
            ratio=duplicate_fingerprint_ratio,
            threshold=config.max_duplicate_fingerprint_ratio,
            label="Duplicate fingerprint",
        ),
    )


def _rate_gate(
    *,
    gate_name: str,
    ratio: Decimal | None,
    threshold: Decimal,
    label: str,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthGateResult:
    if ratio is None:
        status = "incomplete"
        message = f"{label} rate is unavailable without history reports."
    elif ratio <= threshold:
        status = "pass"
        message = f"{label} rate is within the threshold."
    else:
        status = "fail"
        message = f"{label} rate exceeds the threshold."
    return TradeProposalEvidenceComparisonHistoryBatchHealthGateResult(
        gate_name=gate_name,
        status=status,
        message=message,
        observed_value=ratio,
        threshold=threshold,
    )


def _build_status_rows(
    status_counts: dict[str, int],
    history_report_count: int,
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow(
            history_status=status,
            history_count=status_counts[status],
            history_ratio=_ratio(status_counts[status], history_report_count),
        )
        for status in HISTORY_STATUSES
    )


def _config_version_summaries(
    reports: tuple[TradeProposalEvidenceComparisonHistoryReport, ...],
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary, ...]:
    counts: dict[str, int] = {}
    for report in reports:
        counts[report.config_version] = counts.get(report.config_version, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary(
            history_config_version=config_version,
            history_count=count,
        )
        for config_version, count in sorted(counts.items())
    )


def _duplicate_generated_at_summaries(
    reports: tuple[TradeProposalEvidenceComparisonHistoryReport, ...],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary,
    ...,
]:
    counts: dict[datetime, int] = {}
    for report in reports:
        counts[report.generated_at] = counts.get(report.generated_at, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary(
            generated_at=generated_at,
            duplicate_count=count,
        )
        for generated_at, count in sorted(counts.items())
        if count >= 2
    )


def _duplicate_fingerprint_summaries(
    reports: tuple[TradeProposalEvidenceComparisonHistoryReport, ...],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary,
    ...,
]:
    counts: dict[str, int] = {}
    for report in reports:
        fingerprint = _history_report_fingerprint(report)
        counts[fingerprint] = counts.get(fingerprint, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary(
            report_fingerprint=fingerprint,
            duplicate_count=count,
        )
        for fingerprint, count in sorted(counts.items())
        if count >= 2
    )


def _history_report_fingerprint(
    report: TradeProposalEvidenceComparisonHistoryReport,
) -> str:
    return json.dumps(_json_ready(asdict(report)), allow_nan=False, sort_keys=True)


def _finding_summaries(
    reports: tuple[TradeProposalEvidenceComparisonHistoryReport, ...],
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary, ...]:
    counts: dict[tuple[str, str, str], int] = {}
    for report in reports:
        report_keys = {
            (row.severity, row.source_name, row.finding_code)
            for row in report.finding_summaries
        }
        for key in report_keys:
            counts[key] = counts.get(key, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary(
            finding_code=finding_code,
            severity=severity,
            source_name=source_name,
            history_count=count,
        )
        for (severity, source_name, finding_code), count in sorted(counts.items())
    )


def _source_transition_summaries(
    reports: tuple[TradeProposalEvidenceComparisonHistoryReport, ...],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary,
    ...,
]:
    counts: dict[tuple[str, str, str], int] = {}
    for report in reports:
        for row in report.source_transitions:
            key = (row.source_name, row.from_source_status, row.to_source_status)
            counts[key] = counts.get(key, 0) + row.transition_count
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary(
            source_name=source_name,
            from_source_status=from_source_status,
            to_source_status=to_source_status,
            transition_count=count,
        )
        for (
            source_name,
            from_source_status,
            to_source_status,
        ), count in sorted(counts.items())
    )


def _batch_health_status(
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthGateResult, ...],
) -> str:
    gates = {row.gate_name: row.status for row in gate_results}
    if gates["history_sample"] == "incomplete":
        return "incomplete_history_batch_health"
    if gates["duplicate_generated_at_rate"] == "fail":
        return "duplicate_generated_at_batch_health"
    if gates["duplicate_fingerprint_rate"] == "fail":
        return "duplicate_fingerprint_batch_health"
    if gates["divergent_history_rate"] == "fail":
        return "divergent_history_batch_health"
    if gates["unstable_history_rate"] == "fail":
        return "unstable_history_batch_health"
    if gates["incomplete_history_rate"] == "fail":
        return "incomplete_history_batch_health"
    if any(status == "incomplete" for status in gates.values()):
        return "incomplete_history_batch_health"
    return "proposal_evidence_comparison_history_batch_health_ready"


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _validate_batch_health_report_tree(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthReport,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthReport:
    return TradeProposalEvidenceComparisonHistoryBatchHealthReport(
        generated_at=report.generated_at,
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
        gate_results=report.gate_results,
        status_rows=report.status_rows,
        config_version_summaries=report.config_version_summaries,
        duplicate_generated_at_summaries=report.duplicate_generated_at_summaries,
        duplicate_fingerprint_summaries=report.duplicate_fingerprint_summaries,
        finding_summaries=report.finding_summaries,
        source_transition_summaries=report.source_transition_summaries,
    )


def _validate_batch_health_report_rows(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthReport,
) -> None:
    if tuple(row.gate_name for row in report.gate_results) != GATE_NAMES:
        raise ValueError("gate_results must contain batch health gates")
    status_row_keys = tuple(row.history_status for row in report.status_rows)
    if status_row_keys != HISTORY_STATUSES:
        raise ValueError("status_rows must contain sorted history statuses")
    status_counts = {row.history_status: row.history_count for row in report.status_rows}
    if status_counts["divergent_comparison_history"] != (
        report.divergent_history_report_count
    ):
        raise ValueError("status_rows must match divergent history count")
    if status_counts["incomplete_comparison_history"] != (
        report.incomplete_history_report_count
    ):
        raise ValueError("status_rows must match incomplete history count")
    if status_counts["proposal_evidence_comparison_history_ready"] != (
        report.complete_history_report_count
    ):
        raise ValueError("status_rows must match complete history count")
    if status_counts["unstable_comparison_history"] != (
        report.unstable_history_report_count
    ):
        raise ValueError("status_rows must match unstable history count")
    if sum(status_counts.values()) != report.history_report_count:
        raise ValueError("status_rows must sum to history_report_count")
    if report.history_report_count != (
        report.complete_history_report_count
        + report.incomplete_history_report_count
        + report.divergent_history_report_count
        + report.unstable_history_report_count
    ):
        raise ValueError("history_report_count must equal history status counts")
    expected_ratios = {
        status: _ratio(count, report.history_report_count)
        for status, count in status_counts.items()
    }
    for row in report.status_rows:
        if row.history_ratio != expected_ratios[row.history_status]:
            raise ValueError("status_rows must contain expected ratios")
    _validate_ratio_field(
        report,
        "incomplete_history_ratio",
        report.incomplete_history_report_count,
    )
    _validate_ratio_field(
        report,
        "divergent_history_ratio",
        report.divergent_history_report_count,
    )
    _validate_ratio_field(
        report,
        "unstable_history_ratio",
        report.unstable_history_report_count,
    )
    _validate_duplicate_summaries(report)
    _validate_time_bounds(report)
    _validate_config_version_summaries(report)
    _validate_finding_summaries(report)
    _validate_source_transition_summaries(report)
    _validate_gate_payloads(report)


def _validate_ratio_field(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthReport,
    field_name: str,
    count: int,
) -> None:
    expected = _ratio(count, report.history_report_count)
    if getattr(report, field_name) != expected:
        raise ValueError(f"{field_name} must match derived ratio")


def _validate_time_bounds(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthReport,
) -> None:
    if report.history_report_count == 0:
        if (
            report.first_history_generated_at is not None
            or report.last_history_generated_at is not None
        ):
            raise ValueError("history time bounds must be empty without reports")
    else:
        if (
            report.first_history_generated_at is None
            or report.last_history_generated_at is None
        ):
            raise ValueError("history time bounds must be present with reports")
        if report.first_history_generated_at > report.last_history_generated_at:
            raise ValueError("history time bounds must be ordered")


def _validate_duplicate_summaries(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthReport,
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
        if row.duplicate_count > report.history_report_count:
            raise ValueError("duplicate_generated_at_summaries must not exceed count")
    for row in report.duplicate_fingerprint_summaries:
        if row.duplicate_count > report.history_report_count:
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
    report: TradeProposalEvidenceComparisonHistoryBatchHealthReport,
) -> None:
    versions = tuple(
        row.history_config_version for row in report.config_version_summaries
    )
    if versions != tuple(sorted(versions)):
        raise ValueError("config_version_summaries must be sorted")
    if len(set(versions)) != len(versions):
        raise ValueError("config_version_summaries must not contain duplicates")
    if sum(row.history_count for row in report.config_version_summaries) != (
        report.history_report_count
    ):
        raise ValueError("config_version_summaries must sum to history_report_count")


def _validate_finding_summaries(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthReport,
) -> None:
    finding_keys = tuple(
        (row.severity, row.source_name, row.finding_code)
        for row in report.finding_summaries
    )
    if finding_keys != tuple(sorted(finding_keys)):
        raise ValueError("finding_summaries must be sorted")
    if len(set(finding_keys)) != len(finding_keys):
        raise ValueError("finding_summaries must not contain duplicates")
    for row in report.finding_summaries:
        if row.history_count > report.history_report_count:
            raise ValueError("finding_summaries must not exceed history_report_count")


def _validate_source_transition_summaries(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthReport,
) -> None:
    transition_keys = tuple(
        (row.source_name, row.from_source_status, row.to_source_status)
        for row in report.source_transition_summaries
    )
    if transition_keys != tuple(sorted(transition_keys)):
        raise ValueError("source_transition_summaries must be sorted")
    if len(set(transition_keys)) != len(transition_keys):
        raise ValueError("source_transition_summaries must not contain duplicates")


def _validate_gate_payloads(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthReport,
) -> None:
    gates = {row.gate_name: row for row in report.gate_results}
    sample_gate = gates["history_sample"]
    if type(sample_gate.observed_value) is not int:
        raise ValueError("gate_results history_sample observed_value must be an int")
    if sample_gate.observed_value != report.history_report_count:
        raise ValueError("gate_results must match history_report_count")
    if type(sample_gate.threshold) is not int:
        raise ValueError("gate_results history_sample threshold must be an int")
    _require_nonnegative_int(
        "gate_results history_sample threshold",
        sample_gate.threshold,
    )
    expected_sample_status = (
        "pass"
        if report.history_report_count >= sample_gate.threshold
        else "incomplete"
    )
    if sample_gate.status != expected_sample_status:
        raise ValueError("gate_results history_sample status must match threshold")
    _validate_rate_gate_payload(
        gates["incomplete_history_rate"],
        report.incomplete_history_ratio,
        "gate_results incomplete_history_rate",
    )
    _validate_rate_gate_payload(
        gates["divergent_history_rate"],
        report.divergent_history_ratio,
        "gate_results divergent_history_rate",
    )
    _validate_rate_gate_payload(
        gates["unstable_history_rate"],
        report.unstable_history_ratio,
        "gate_results unstable_history_rate",
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
    gate: TradeProposalEvidenceComparisonHistoryBatchHealthGateResult,
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


def _clone_batch_health_gate_results(
    gate_results: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthGateResult,
        ...,
    ],
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthGateResult, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in _normalize_typed_tuple(
            "gate_results",
            gate_results,
            TradeProposalEvidenceComparisonHistoryBatchHealthGateResult,
        )
    )


def _clone_status_rows(
    status_rows: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow,
        ...,
    ],
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow(
            history_status=row.history_status,
            history_count=row.history_count,
            history_ratio=row.history_ratio,
        )
        for row in _normalize_typed_tuple(
            "status_rows",
            status_rows,
            TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow,
        )
    )


def _clone_config_version_summaries(
    config_version_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary,
        ...,
    ],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary,
    ...,
]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary(
            history_config_version=row.history_config_version,
            history_count=row.history_count,
        )
        for row in _normalize_typed_tuple(
            "config_version_summaries",
            config_version_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary,
        )
    )


def _clone_duplicate_generated_at_summaries(
    summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary,
        ...,
    ],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary,
    ...,
]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary(
            generated_at=row.generated_at,
            duplicate_count=row.duplicate_count,
        )
        for row in _normalize_typed_tuple(
            "duplicate_generated_at_summaries",
            summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary,
        )
    )


def _clone_duplicate_fingerprint_summaries(
    summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary,
        ...,
    ],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary,
    ...,
]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary(
            report_fingerprint=row.report_fingerprint,
            duplicate_count=row.duplicate_count,
        )
        for row in _normalize_typed_tuple(
            "duplicate_fingerprint_summaries",
            summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary,
        )
    )


def _clone_finding_summaries(
    finding_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary,
        ...,
    ],
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary(
            finding_code=row.finding_code,
            severity=row.severity,
            source_name=row.source_name,
            history_count=row.history_count,
        )
        for row in _normalize_typed_tuple(
            "finding_summaries",
            finding_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary,
        )
    )


def _clone_source_transition_summaries(
    summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary,
        ...,
    ],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary,
    ...,
]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary(
            source_name=row.source_name,
            from_source_status=row.from_source_status,
            to_source_status=row.to_source_status,
            transition_count=row.transition_count,
        )
        for row in _normalize_typed_tuple(
            "source_transition_summaries",
            summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary,
        )
    )


def _normalize_typed_tuple(
    field_name: str,
    value: tuple[Any, ...],
    expected_type: type,
) -> tuple[Any, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    items = value
    for item in items:
        if type(item) is not expected_type:
            raise ValueError(f"{field_name} must contain {expected_type.__name__} values")
    return items


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
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_BOUNDARY_STATEMENT
    ):
        raise ValueError(
            "boundary_statement must describe report-only proposal evidence comparison "
            "history batch health"
        )


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_source_status(source_name: str, source_status: str) -> None:
    if source_status not in SOURCE_STATUSES[source_name]:
        raise ValueError("source_status must be a known comparison source status")


def _require_history_finding_tuple(
    finding_code: str,
    severity: str,
    source_name: str,
) -> None:
    if (finding_code, severity, source_name) not in HISTORY_FINDINGS:
        raise ValueError(
            "finding_code, severity, and source_name must match a known history finding"
        )


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
