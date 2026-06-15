"""Report-only proposal evidence comparison history artifacts for Level 2."""

from __future__ import annotations

from collections.abc import Iterable
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.proposal_evidence_comparison import (
    TradeProposalEvidenceComparisonFindingRow,
    TradeProposalEvidenceComparisonGateResult,
    TradeProposalEvidenceComparisonMetricRow,
    TradeProposalEvidenceComparisonReport,
    TradeProposalEvidenceComparisonSourceRow,
)


__all__ = (
    "TradeProposalEvidenceComparisonHistoryConfig",
    "TradeProposalEvidenceComparisonHistoryGateResult",
    "TradeProposalEvidenceComparisonHistoryStatusRow",
    "TradeProposalEvidenceComparisonHistoryFindingSummary",
    "TradeProposalEvidenceComparisonHistoryConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistorySourceTransition",
    "TradeProposalEvidenceComparisonHistoryReport",
    "TradeProposalEvidenceComparisonHistoryLog",
    "build_trade_proposal_evidence_comparison_history_report",
)

DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT = (
    "This is a report-only proposal evidence comparison history artifact over "
    "supplied proposal evidence comparison reports, not an approval workflow, "
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
    "comparison_sample",
    "incomplete_comparison_rate",
    "divergent_comparison_rate",
    "unstable_comparison_rate",
)
GATE_STATUSES = ("pass", "fail", "incomplete")
REPORT_STATUSES = (
    "incomplete_comparison_history",
    "divergent_comparison_history",
    "unstable_comparison_history",
    "proposal_evidence_comparison_history_ready",
)
COMPARISON_STATUSES = (
    "divergent_evidence_comparison",
    "incomplete_evidence_comparison",
    "proposal_evidence_comparison_complete",
    "unstable_evidence_comparison",
)
FINDING_SEVERITIES = ("divergent", "incomplete", "unstable")
SOURCE_NAMES = ("dossier_batch", "forecast_evidence")
FINDING_SOURCE_NAMES = ("comparison", *SOURCE_NAMES)
COMPARISON_SOURCE_STATUSES = {
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
COMPARISON_FINDINGS = (
    ("dossier_batch_incomplete", "incomplete", "dossier_batch"),
    ("dossier_batch_unstable", "unstable", "dossier_batch"),
    ("evidence_consistency_divergent", "divergent", "comparison"),
    ("forecast_evidence_incomplete", "incomplete", "forecast_evidence"),
    ("forecast_evidence_unstable", "unstable", "forecast_evidence"),
)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryConfig:
    config_version: str
    min_comparison_count: int = 1
    max_incomplete_comparison_ratio: Decimal = Decimal("0.0000")
    max_divergent_comparison_ratio: Decimal = Decimal("0.0000")
    max_unstable_comparison_ratio: Decimal = Decimal("0.0000")
    boundary_statement: str = (
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT
    )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("min_comparison_count", self.min_comparison_count)
        _require_probability_decimal(
            "max_incomplete_comparison_ratio",
            self.max_incomplete_comparison_ratio,
        )
        _require_probability_decimal(
            "max_divergent_comparison_ratio",
            self.max_divergent_comparison_ratio,
        )
        _require_probability_decimal(
            "max_unstable_comparison_ratio",
            self.max_unstable_comparison_ratio,
        )
        _require_boundary_statement(self.boundary_statement)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known comparison history gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known comparison history gate status")
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryStatusRow:
    comparison_status: str
    comparison_count: int
    comparison_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.comparison_status not in COMPARISON_STATUSES:
            raise ValueError("comparison_status must be a known comparison status")
        _require_nonnegative_int("comparison_count", self.comparison_count)
        _require_optional_probability_decimal("comparison_ratio", self.comparison_ratio)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryFindingSummary:
    finding_code: str
    severity: str
    source_name: str
    comparison_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("finding_code", self.finding_code)
        if self.severity not in FINDING_SEVERITIES:
            raise ValueError("severity must be a known comparison history severity")
        if self.source_name not in FINDING_SOURCE_NAMES:
            raise ValueError("source_name must be a known finding source")
        _require_comparison_finding_tuple(
            self.finding_code,
            self.severity,
            self.source_name,
        )
        _require_positive_int("comparison_count", self.comparison_count)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryConfigVersionSummary:
    comparison_config_version: str
    comparison_count: int

    def __post_init__(self) -> None:
        _require_canonical_string(
            "comparison_config_version",
            self.comparison_config_version,
        )
        _require_positive_int("comparison_count", self.comparison_count)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistorySourceTransition:
    source_name: str
    from_source_status: str
    to_source_status: str
    transition_count: int

    def __post_init__(self) -> None:
        if self.source_name not in SOURCE_NAMES:
            raise ValueError("source_name must be a known comparison source")
        _require_canonical_string("from_source_status", self.from_source_status)
        _require_canonical_string("to_source_status", self.to_source_status)
        _require_comparison_source_status(self.source_name, self.from_source_status)
        _require_comparison_source_status(self.source_name, self.to_source_status)
        _require_positive_int("transition_count", self.transition_count)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    comparison_count: int
    complete_comparison_count: int
    incomplete_comparison_count: int
    divergent_comparison_count: int
    unstable_comparison_count: int
    incomplete_comparison_ratio: Decimal | None
    divergent_comparison_ratio: Decimal | None
    unstable_comparison_ratio: Decimal | None
    first_comparison_generated_at: datetime | None
    last_comparison_generated_at: datetime | None
    status: str
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryGateResult, ...]
    status_rows: tuple[TradeProposalEvidenceComparisonHistoryStatusRow, ...]
    finding_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryFindingSummary,
        ...,
    ]
    config_version_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryConfigVersionSummary,
        ...,
    ]
    source_transitions: tuple[
        TradeProposalEvidenceComparisonHistorySourceTransition,
        ...,
    ]

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_comparison_generated_at",
            _as_optional_utc(self.first_comparison_generated_at),
        )
        object.__setattr__(
            self,
            "last_comparison_generated_at",
            _as_optional_utc(self.last_comparison_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        _require_boundary_statement(self.boundary_statement)
        for field_name in (
            "comparison_count",
            "complete_comparison_count",
            "incomplete_comparison_count",
            "divergent_comparison_count",
            "unstable_comparison_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_optional_probability_decimal(
            "incomplete_comparison_ratio",
            self.incomplete_comparison_ratio,
        )
        _require_optional_probability_decimal(
            "divergent_comparison_ratio",
            self.divergent_comparison_ratio,
        )
        _require_optional_probability_decimal(
            "unstable_comparison_ratio",
            self.unstable_comparison_ratio,
        )
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known comparison history status")
        object.__setattr__(
            self,
            "gate_results",
            _clone_history_gate_results(self.gate_results),
        )
        object.__setattr__(
            self,
            "status_rows",
            _clone_status_rows(self.status_rows),
        )
        object.__setattr__(
            self,
            "finding_summaries",
            _clone_finding_summaries(self.finding_summaries),
        )
        object.__setattr__(
            self,
            "config_version_summaries",
            _clone_config_version_summaries(self.config_version_summaries),
        )
        object.__setattr__(
            self,
            "source_transitions",
            _clone_source_transitions(self.source_transitions),
        )
        _validate_history_report_rows(self)
        if self.status != _history_status(self.gate_results):
            raise ValueError("status must match comparison history gate results")


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: TradeProposalEvidenceComparisonHistoryReport) -> None:
        if type(report) is not TradeProposalEvidenceComparisonHistoryReport:
            raise ValueError(
                "report must be a TradeProposalEvidenceComparisonHistoryReport"
            )
        validated = _validate_history_report_tree(report)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True)
        line += "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_trade_proposal_evidence_comparison_history_report(
    comparisons: Iterable[TradeProposalEvidenceComparisonReport],
    *,
    config: TradeProposalEvidenceComparisonHistoryConfig,
    generated_at: datetime,
) -> TradeProposalEvidenceComparisonHistoryReport:
    if type(config) is not TradeProposalEvidenceComparisonHistoryConfig:
        raise ValueError(
            "config must be a TradeProposalEvidenceComparisonHistoryConfig"
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    comparison_reports = _normalize_comparison_inputs(comparisons)
    comparison_count = len(comparison_reports)
    status_counts = _build_status_counts(comparison_reports)
    complete_count = status_counts["proposal_evidence_comparison_complete"]
    incomplete_count = status_counts["incomplete_evidence_comparison"]
    divergent_count = status_counts["divergent_evidence_comparison"]
    unstable_count = status_counts["unstable_evidence_comparison"]
    incomplete_ratio = _ratio(incomplete_count, comparison_count)
    divergent_ratio = _ratio(divergent_count, comparison_count)
    unstable_ratio = _ratio(unstable_count, comparison_count)
    gate_results = _build_gate_results(
        comparison_count=comparison_count,
        incomplete_ratio=incomplete_ratio,
        divergent_ratio=divergent_ratio,
        unstable_ratio=unstable_ratio,
        config=config,
    )
    return TradeProposalEvidenceComparisonHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_only=True,
        boundary_statement=config.boundary_statement,
        comparison_count=comparison_count,
        complete_comparison_count=complete_count,
        incomplete_comparison_count=incomplete_count,
        divergent_comparison_count=divergent_count,
        unstable_comparison_count=unstable_count,
        incomplete_comparison_ratio=incomplete_ratio,
        divergent_comparison_ratio=divergent_ratio,
        unstable_comparison_ratio=unstable_ratio,
        first_comparison_generated_at=(
            comparison_reports[0].generated_at if comparison_reports else None
        ),
        last_comparison_generated_at=(
            comparison_reports[-1].generated_at if comparison_reports else None
        ),
        status=_history_status(gate_results),
        gate_results=gate_results,
        status_rows=_build_status_rows(status_counts, comparison_count),
        finding_summaries=_build_finding_summaries(comparison_reports),
        config_version_summaries=_build_config_version_summaries(comparison_reports),
        source_transitions=_build_source_transitions(comparison_reports),
    )


def _normalize_comparison_inputs(
    comparisons: Iterable[TradeProposalEvidenceComparisonReport],
) -> tuple[TradeProposalEvidenceComparisonReport, ...]:
    if type(comparisons) not in (list, tuple):
        raise ValueError("comparisons must be an iterable of comparison reports")
    supplied = tuple(comparisons)
    cloned = tuple(_clone_comparison_report(item) for item in supplied)
    seen_generated_at = set()
    for report in cloned:
        if report.generated_at in seen_generated_at:
            raise ValueError("duplicate comparison generated_at values are not allowed")
        seen_generated_at.add(report.generated_at)
    return tuple(
        sorted(
            cloned,
            key=lambda report: (
                report.generated_at,
                report.config_version,
                report.forecast_status,
                report.dossier_batch_status,
            ),
        )
    )


def _clone_comparison_report(
    report: TradeProposalEvidenceComparisonReport,
) -> TradeProposalEvidenceComparisonReport:
    if type(report) is not TradeProposalEvidenceComparisonReport:
        raise ValueError(
            "comparisons must contain TradeProposalEvidenceComparisonReport values"
        )
    gate_results = tuple(
        TradeProposalEvidenceComparisonGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in _normalize_typed_tuple(
            "gate_results",
            report.gate_results,
            TradeProposalEvidenceComparisonGateResult,
        )
    )
    source_rows = tuple(
        _clone_comparison_source_row(row)
        for row in _normalize_typed_tuple(
            "source_rows",
            report.source_rows,
            TradeProposalEvidenceComparisonSourceRow,
        )
    )
    metric_rows = tuple(
        TradeProposalEvidenceComparisonMetricRow(
            metric_name=row.metric_name,
            source_name=row.source_name,
            observed_value=row.observed_value,
            threshold=row.threshold,
            status=row.status,
        )
        for row in _normalize_typed_tuple(
            "metric_rows",
            report.metric_rows,
            TradeProposalEvidenceComparisonMetricRow,
        )
    )
    finding_rows = tuple(
        _clone_comparison_finding_row(row)
        for row in _normalize_typed_tuple(
            "finding_rows",
            report.finding_rows,
            TradeProposalEvidenceComparisonFindingRow,
        )
    )
    return TradeProposalEvidenceComparisonReport(
        generated_at=_as_utc(report.generated_at),
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        forecast_evidence_generated_at=_as_utc(report.forecast_evidence_generated_at),
        dossier_batch_generated_at=_as_utc(report.dossier_batch_generated_at),
        forecast_status=report.forecast_status,
        dossier_batch_status=report.dossier_batch_status,
        forecast_observation_count=report.forecast_observation_count,
        forecast_probability_observation_count=(
            report.forecast_probability_observation_count
        ),
        forecast_edge_observation_count=report.forecast_edge_observation_count,
        dossier_count=report.dossier_count,
        complete_dossier_count=report.complete_dossier_count,
        incomplete_dossier_ratio=report.incomplete_dossier_ratio,
        inconsistent_dossier_ratio=report.inconsistent_dossier_ratio,
        unstable_dossier_ratio=report.unstable_dossier_ratio,
        mean_probability_loss=report.mean_probability_loss,
        worst_bucket_error=report.worst_bucket_error,
        mean_edge_gap_ratio=report.mean_edge_gap_ratio,
        positive_edge_hit_rate=report.positive_edge_hit_rate,
        worst_residual_exposure_ratio=report.worst_residual_exposure_ratio,
        status=report.status,
        gate_results=gate_results,
        source_rows=source_rows,
        metric_rows=metric_rows,
        finding_rows=finding_rows,
    )


def _clone_comparison_source_row(
    row: TradeProposalEvidenceComparisonSourceRow,
) -> TradeProposalEvidenceComparisonSourceRow:
    clone = TradeProposalEvidenceComparisonSourceRow(
        source_name=row.source_name,
        source_status=row.source_status,
        generated_at=_as_utc(row.generated_at),
        sample_count=row.sample_count,
        status_category=row.status_category,
    )
    _require_comparison_source_status(clone.source_name, clone.source_status)
    return clone


def _clone_comparison_finding_row(
    row: TradeProposalEvidenceComparisonFindingRow,
) -> TradeProposalEvidenceComparisonFindingRow:
    clone = TradeProposalEvidenceComparisonFindingRow(
        finding_code=row.finding_code,
        severity=row.severity,
        source_name=row.source_name,
        message=row.message,
        observed_value=row.observed_value,
        threshold=row.threshold,
    )
    _require_comparison_finding_tuple(
        clone.finding_code,
        clone.severity,
        clone.source_name,
    )
    return clone


def _build_status_counts(
    comparisons: tuple[TradeProposalEvidenceComparisonReport, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in COMPARISON_STATUSES}
    for report in comparisons:
        counts[report.status] += 1
    return counts


def _build_gate_results(
    *,
    comparison_count: int,
    incomplete_ratio: Decimal | None,
    divergent_ratio: Decimal | None,
    unstable_ratio: Decimal | None,
    config: TradeProposalEvidenceComparisonHistoryConfig,
) -> tuple[TradeProposalEvidenceComparisonHistoryGateResult, ...]:
    sample_passes = comparison_count >= config.min_comparison_count
    return (
        TradeProposalEvidenceComparisonHistoryGateResult(
            gate_name="comparison_sample",
            status="pass" if sample_passes else "incomplete",
            message=(
                "Supplied comparison report sample meets the threshold."
                if sample_passes
                else "Supplied comparison report sample is below the threshold."
            ),
            observed_value=comparison_count,
            threshold=config.min_comparison_count,
        ),
        _rate_gate(
            gate_name="incomplete_comparison_rate",
            ratio=incomplete_ratio,
            threshold=config.max_incomplete_comparison_ratio,
            label="Incomplete comparison",
        ),
        _rate_gate(
            gate_name="divergent_comparison_rate",
            ratio=divergent_ratio,
            threshold=config.max_divergent_comparison_ratio,
            label="Divergent comparison",
        ),
        _rate_gate(
            gate_name="unstable_comparison_rate",
            ratio=unstable_ratio,
            threshold=config.max_unstable_comparison_ratio,
            label="Unstable comparison",
        ),
    )


def _rate_gate(
    *,
    gate_name: str,
    ratio: Decimal | None,
    threshold: Decimal,
    label: str,
) -> TradeProposalEvidenceComparisonHistoryGateResult:
    if ratio is None:
        status = "incomplete"
        message = f"{label} rate is unavailable without comparison reports."
    elif ratio <= threshold:
        status = "pass"
        message = f"{label} rate is within the threshold."
    else:
        status = "fail"
        message = f"{label} rate exceeds the threshold."
    return TradeProposalEvidenceComparisonHistoryGateResult(
        gate_name=gate_name,
        status=status,
        message=message,
        observed_value=ratio,
        threshold=threshold,
    )


def _build_status_rows(
    status_counts: dict[str, int],
    comparison_count: int,
) -> tuple[TradeProposalEvidenceComparisonHistoryStatusRow, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryStatusRow(
            comparison_status=status,
            comparison_count=status_counts[status],
            comparison_ratio=_ratio(status_counts[status], comparison_count),
        )
        for status in COMPARISON_STATUSES
    )


def _build_finding_summaries(
    comparisons: tuple[TradeProposalEvidenceComparisonReport, ...],
) -> tuple[TradeProposalEvidenceComparisonHistoryFindingSummary, ...]:
    counts: dict[tuple[str, str, str], int] = {}
    for report in comparisons:
        report_keys = {
            (row.severity, row.source_name, row.finding_code)
            for row in report.finding_rows
        }
        for key in report_keys:
            counts[key] = counts.get(key, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryFindingSummary(
            finding_code=finding_code,
            severity=severity,
            source_name=source_name,
            comparison_count=count,
        )
        for (severity, source_name, finding_code), count in sorted(counts.items())
    )


def _build_config_version_summaries(
    comparisons: tuple[TradeProposalEvidenceComparisonReport, ...],
) -> tuple[TradeProposalEvidenceComparisonHistoryConfigVersionSummary, ...]:
    counts: dict[str, int] = {}
    for report in comparisons:
        counts[report.config_version] = counts.get(report.config_version, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryConfigVersionSummary(
            comparison_config_version=config_version,
            comparison_count=count,
        )
        for config_version, count in sorted(counts.items())
    )


def _build_source_transitions(
    comparisons: tuple[TradeProposalEvidenceComparisonReport, ...],
) -> tuple[TradeProposalEvidenceComparisonHistorySourceTransition, ...]:
    counts: dict[tuple[str, str, str], int] = {}
    for previous, current in zip(comparisons, comparisons[1:]):
        previous_sources = _source_status_map(previous)
        current_sources = _source_status_map(current)
        for source_name in SOURCE_NAMES:
            key = (
                source_name,
                previous_sources[source_name],
                current_sources[source_name],
            )
            counts[key] = counts.get(key, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistorySourceTransition(
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


def _source_status_map(report: TradeProposalEvidenceComparisonReport) -> dict[str, str]:
    return {row.source_name: row.source_status for row in report.source_rows}


def _history_status(
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryGateResult, ...],
) -> str:
    gates = {row.gate_name: row.status for row in gate_results}
    if gates["comparison_sample"] == "incomplete":
        return "incomplete_comparison_history"
    if gates["divergent_comparison_rate"] == "fail":
        return "divergent_comparison_history"
    if gates["unstable_comparison_rate"] == "fail":
        return "unstable_comparison_history"
    if gates["incomplete_comparison_rate"] == "fail":
        return "incomplete_comparison_history"
    if any(status == "incomplete" for status in gates.values()):
        return "incomplete_comparison_history"
    return "proposal_evidence_comparison_history_ready"


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _clone_history_gate_results(
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryGateResult, ...],
) -> tuple[TradeProposalEvidenceComparisonHistoryGateResult, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in _normalize_typed_tuple(
            "gate_results",
            gate_results,
            TradeProposalEvidenceComparisonHistoryGateResult,
        )
    )


def _clone_status_rows(
    status_rows: tuple[TradeProposalEvidenceComparisonHistoryStatusRow, ...],
) -> tuple[TradeProposalEvidenceComparisonHistoryStatusRow, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryStatusRow(
            comparison_status=row.comparison_status,
            comparison_count=row.comparison_count,
            comparison_ratio=row.comparison_ratio,
        )
        for row in _normalize_typed_tuple(
            "status_rows",
            status_rows,
            TradeProposalEvidenceComparisonHistoryStatusRow,
        )
    )


def _clone_finding_summaries(
    finding_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryFindingSummary,
        ...,
    ],
) -> tuple[TradeProposalEvidenceComparisonHistoryFindingSummary, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryFindingSummary(
            finding_code=row.finding_code,
            severity=row.severity,
            source_name=row.source_name,
            comparison_count=row.comparison_count,
        )
        for row in _normalize_typed_tuple(
            "finding_summaries",
            finding_summaries,
            TradeProposalEvidenceComparisonHistoryFindingSummary,
        )
    )


def _clone_config_version_summaries(
    config_version_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryConfigVersionSummary,
        ...,
    ],
) -> tuple[TradeProposalEvidenceComparisonHistoryConfigVersionSummary, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryConfigVersionSummary(
            comparison_config_version=row.comparison_config_version,
            comparison_count=row.comparison_count,
        )
        for row in _normalize_typed_tuple(
            "config_version_summaries",
            config_version_summaries,
            TradeProposalEvidenceComparisonHistoryConfigVersionSummary,
        )
    )


def _clone_source_transitions(
    source_transitions: tuple[
        TradeProposalEvidenceComparisonHistorySourceTransition,
        ...,
    ],
) -> tuple[TradeProposalEvidenceComparisonHistorySourceTransition, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistorySourceTransition(
            source_name=row.source_name,
            from_source_status=row.from_source_status,
            to_source_status=row.to_source_status,
            transition_count=row.transition_count,
        )
        for row in _normalize_typed_tuple(
            "source_transitions",
            source_transitions,
            TradeProposalEvidenceComparisonHistorySourceTransition,
        )
    )


def _validate_history_report_tree(
    report: TradeProposalEvidenceComparisonHistoryReport,
) -> TradeProposalEvidenceComparisonHistoryReport:
    return TradeProposalEvidenceComparisonHistoryReport(
        generated_at=report.generated_at,
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
        gate_results=report.gate_results,
        status_rows=report.status_rows,
        finding_summaries=report.finding_summaries,
        config_version_summaries=report.config_version_summaries,
        source_transitions=report.source_transitions,
    )


def _validate_history_report_rows(
    report: TradeProposalEvidenceComparisonHistoryReport,
) -> None:
    if tuple(row.gate_name for row in report.gate_results) != GATE_NAMES:
        raise ValueError("gate_results must contain comparison history gates")
    _validate_gate_payloads(report)
    status_row_keys = tuple(row.comparison_status for row in report.status_rows)
    if status_row_keys != COMPARISON_STATUSES:
        raise ValueError("status_rows must contain sorted comparison statuses")
    status_counts = {row.comparison_status: row.comparison_count for row in report.status_rows}
    if status_counts["proposal_evidence_comparison_complete"] != (
        report.complete_comparison_count
    ):
        raise ValueError("status_rows must match complete comparison count")
    if status_counts["incomplete_evidence_comparison"] != (
        report.incomplete_comparison_count
    ):
        raise ValueError("status_rows must match incomplete comparison count")
    if status_counts["divergent_evidence_comparison"] != (
        report.divergent_comparison_count
    ):
        raise ValueError("status_rows must match divergent comparison count")
    if status_counts["unstable_evidence_comparison"] != (
        report.unstable_comparison_count
    ):
        raise ValueError("status_rows must match unstable comparison count")
    total_status_count = sum(status_counts.values())
    if total_status_count != report.comparison_count:
        raise ValueError("status_rows must sum to comparison_count")
    expected_ratios = {
        status: _ratio(count, report.comparison_count)
        for status, count in status_counts.items()
    }
    for row in report.status_rows:
        if row.comparison_ratio != expected_ratios[row.comparison_status]:
            raise ValueError("status_rows must contain expected ratios")
    if report.incomplete_comparison_ratio != expected_ratios[
        "incomplete_evidence_comparison"
    ]:
        raise ValueError("incomplete_comparison_ratio must match status rows")
    if report.divergent_comparison_ratio != expected_ratios[
        "divergent_evidence_comparison"
    ]:
        raise ValueError("divergent_comparison_ratio must match status rows")
    if report.unstable_comparison_ratio != expected_ratios[
        "unstable_evidence_comparison"
    ]:
        raise ValueError("unstable_comparison_ratio must match status rows")
    if report.comparison_count == 0:
        if (
            report.first_comparison_generated_at is not None
            or report.last_comparison_generated_at is not None
        ):
            raise ValueError("comparison time bounds must be empty without reports")
    else:
        if (
            report.first_comparison_generated_at is None
            or report.last_comparison_generated_at is None
        ):
            raise ValueError("comparison time bounds must be present with reports")
        if report.first_comparison_generated_at > report.last_comparison_generated_at:
            raise ValueError("comparison time bounds must be ordered")
    finding_keys = tuple(
        (row.severity, row.source_name, row.finding_code)
        for row in report.finding_summaries
    )
    if finding_keys != tuple(sorted(finding_keys)):
        raise ValueError("finding_summaries must be sorted")
    if len(set(finding_keys)) != len(finding_keys):
        raise ValueError("finding_summaries must not contain duplicates")
    for row in report.finding_summaries:
        if row.comparison_count > report.comparison_count:
            raise ValueError("finding_summaries must not exceed comparison_count")
    config_versions = tuple(
        row.comparison_config_version for row in report.config_version_summaries
    )
    if config_versions != tuple(sorted(config_versions)):
        raise ValueError("config_version_summaries must be sorted")
    if len(set(config_versions)) != len(config_versions):
        raise ValueError("config_version_summaries must not contain duplicates")
    if sum(row.comparison_count for row in report.config_version_summaries) != (
        report.comparison_count
    ):
        raise ValueError("config_version_summaries must sum to comparison_count")
    transition_keys = tuple(
        (row.source_name, row.from_source_status, row.to_source_status)
        for row in report.source_transitions
    )
    if transition_keys != tuple(sorted(transition_keys)):
        raise ValueError("source_transitions must be sorted")
    if len(set(transition_keys)) != len(transition_keys):
        raise ValueError("source_transitions must not contain duplicates")
    max_transition_count = max(0, report.comparison_count - 1)
    for row in report.source_transitions:
        if row.transition_count > max_transition_count:
            raise ValueError("source_transitions must not exceed comparison intervals")
    expected_transition_total = max_transition_count * len(SOURCE_NAMES)
    if sum(row.transition_count for row in report.source_transitions) != (
        expected_transition_total
    ):
        raise ValueError("source_transitions must not exceed comparison intervals")
    for source_name in SOURCE_NAMES:
        source_total = sum(
            row.transition_count
            for row in report.source_transitions
            if row.source_name == source_name
        )
        if source_total != max_transition_count:
            raise ValueError("source_transitions must cover every comparison interval")


def _validate_gate_payloads(
    report: TradeProposalEvidenceComparisonHistoryReport,
) -> None:
    gates = {row.gate_name: row for row in report.gate_results}
    sample_gate = gates["comparison_sample"]
    if type(sample_gate.observed_value) is not int:
        raise ValueError("gate_results comparison_sample observed_value must be an int")
    if sample_gate.observed_value != report.comparison_count:
        raise ValueError("gate_results must match comparison_count")
    if type(sample_gate.threshold) is not int:
        raise ValueError("gate_results comparison_sample threshold must be an int")
    _require_nonnegative_int(
        "gate_results comparison_sample threshold",
        sample_gate.threshold,
    )
    expected_sample_status = (
        "pass"
        if report.comparison_count >= sample_gate.threshold
        else "incomplete"
    )
    if sample_gate.status != expected_sample_status:
        raise ValueError("gate_results comparison_sample status must match threshold")
    _validate_rate_gate_payload(
        gates["incomplete_comparison_rate"],
        report.incomplete_comparison_ratio,
        "gate_results incomplete_comparison_rate",
    )
    _validate_rate_gate_payload(
        gates["divergent_comparison_rate"],
        report.divergent_comparison_ratio,
        "gate_results divergent_comparison_rate",
    )
    _validate_rate_gate_payload(
        gates["unstable_comparison_rate"],
        report.unstable_comparison_ratio,
        "gate_results unstable_comparison_rate",
    )


def _validate_rate_gate_payload(
    gate: TradeProposalEvidenceComparisonHistoryGateResult,
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
        raise ValueError("datetime value is required")
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
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BOUNDARY_STATEMENT
    ):
        raise ValueError("boundary_statement must match the report-only boundary")


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_comparison_source_status(source_name: str, source_status: str) -> None:
    if source_status not in COMPARISON_SOURCE_STATUSES[source_name]:
        raise ValueError("source_status must be a known comparison source status")


def _require_comparison_finding_tuple(
    finding_code: str,
    severity: str,
    source_name: str,
) -> None:
    if (finding_code, severity, source_name) not in COMPARISON_FINDINGS:
        raise ValueError(
            "finding_code, severity, and source_name must match a known comparison finding"
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
