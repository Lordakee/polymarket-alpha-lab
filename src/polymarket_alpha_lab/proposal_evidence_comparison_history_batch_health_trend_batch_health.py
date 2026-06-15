"""Report-only proposal evidence comparison history batch health trend batch health artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow,
)


__all__ = (
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
    "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog",
    "build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report",
)

DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_BOUNDARY_STATEMENT = (
    "This is a report-only proposal evidence comparison history batch health trend batch health "
    "artifact over supplied proposal evidence comparison history batch health trend batch "
    "reports, not an approval workflow, proposal approval, approved-proposal "
    "selector, latest-decision selector, decision-resolution process, investment "
    "ranking, trade recommendation, strategy-promotion signal, trade instruction, "
    "order instruction, broker request, order request, account action, account "
    "authentication, private-key handling, wallet signature, live-execution signal, "
    "credential workflow, external-history loader, JSONL reader, scraping workflow, "
    "outcome loader, settlement review, reconciliation process, compliance review, "
    "geographic access analysis, realized false-positive analysis, profitability "
    "analysis, or automatic order-placement authorization."
)

ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.0001")
GATE_NAMES = (
    "trend_batch_sample",
    "incomplete_trend_batch_rate",
    "duplicate_generated_at_rate",
    "duplicate_fingerprint_rate",
)
NODE_13_TREND_BATCH_GATE_NAMES = (
    "trend_sample",
    "incomplete_trend_rate",
    "duplicate_generated_at_rate",
    "duplicate_fingerprint_rate",
)
GATE_STATUSES = ("pass", "fail", "incomplete")
TREND_BATCH_STATUSES = (
    "duplicate_fingerprint_batch_health_trend_batch",
    "duplicate_generated_at_batch_health_trend_batch",
    "incomplete_batch_health_trend_batch",
    "proposal_evidence_comparison_history_batch_health_trend_batch_ready",
)
REPORT_STATUSES = (
    "incomplete_batch_health_trend_batch_health",
    "duplicate_generated_at_batch_health_trend_batch_health",
    "duplicate_fingerprint_batch_health_trend_batch_health",
    "proposal_evidence_comparison_history_batch_health_trend_batch_health_ready",
)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig:
    config_version: str
    min_trend_batch_report_count: int = 1
    max_incomplete_trend_batch_ratio: Decimal = Decimal("0.0000")
    max_duplicate_generated_at_ratio: Decimal = Decimal("0.0000")
    max_duplicate_fingerprint_ratio: Decimal = Decimal("0.0000")
    boundary_statement: str = (
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_BOUNDARY_STATEMENT
    )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("min_trend_batch_report_count", self.min_trend_batch_report_count)
        _require_probability_decimal(
            "max_incomplete_trend_batch_ratio",
            self.max_incomplete_trend_batch_ratio,
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
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known trend batch health gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known trend batch health gate status")
        if self.gate_name == "trend_batch_sample" and self.status == "fail":
            raise ValueError("trend_batch_sample cannot fail")
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow:
    trend_batch_status: str
    trend_batch_count: int
    trend_batch_ratio: Decimal | None

    def __post_init__(self) -> None:
        if self.trend_batch_status not in TREND_BATCH_STATUSES:
            raise ValueError("trend_batch_status must be a known trend batch status")
        _require_nonnegative_int("trend_batch_count", self.trend_batch_count)
        _require_optional_probability_decimal("trend_batch_ratio", self.trend_batch_ratio)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary:
    trend_batch_config_version: str
    trend_batch_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("trend_batch_config_version", self.trend_batch_config_version)
        _require_positive_int("trend_batch_count", self.trend_batch_count)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary:
    gate_name: str
    gate_status: str
    trend_batch_count: int

    def __post_init__(self) -> None:
        if self.gate_name not in NODE_13_TREND_BATCH_GATE_NAMES:
            raise ValueError("gate_name must be a known trend batch gate")
        if self.gate_status not in GATE_STATUSES:
            raise ValueError("gate_status must be a known gate status")
        _require_positive_int("trend_batch_count", self.trend_batch_count)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary:
    generated_at: datetime
    duplicate_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_nonnegative_int("duplicate_count", self.duplicate_count)
        if self.duplicate_count < 2:
            raise ValueError("duplicate_count must be at least 2")


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary:
    report_fingerprint: str
    duplicate_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("report_fingerprint", self.report_fingerprint)
        _require_nonnegative_int("duplicate_count", self.duplicate_count)
        if self.duplicate_count < 2:
            raise ValueError("duplicate_count must be at least 2")


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    trend_batch_report_count: int
    ready_trend_batch_report_count: int
    incomplete_trend_batch_report_count: int
    duplicate_generated_at_trend_batch_report_count: int
    duplicate_fingerprint_trend_batch_report_count: int
    duplicate_generated_at_count: int
    duplicate_fingerprint_count: int
    incomplete_trend_batch_ratio: Decimal | None
    duplicate_generated_at_ratio: Decimal | None
    duplicate_fingerprint_ratio: Decimal | None
    first_trend_batch_generated_at: datetime | None
    last_trend_batch_generated_at: datetime | None
    status: str
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult, ...]
    status_rows: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow, ...]
    config_version_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary,
        ...,
    ]
    gate_status_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary,
        ...,
    ]
    duplicate_generated_at_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary,
        ...,
    ]
    duplicate_fingerprint_summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary,
        ...,
    ]

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_trend_batch_generated_at",
            _as_optional_utc(self.first_trend_batch_generated_at),
        )
        object.__setattr__(
            self,
            "last_trend_batch_generated_at",
            _as_optional_utc(self.last_trend_batch_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        _require_boundary_statement(self.boundary_statement)
        for field_name in (
            "trend_batch_report_count",
            "ready_trend_batch_report_count",
            "incomplete_trend_batch_report_count",
            "duplicate_generated_at_trend_batch_report_count",
            "duplicate_fingerprint_trend_batch_report_count",
            "duplicate_generated_at_count",
            "duplicate_fingerprint_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "incomplete_trend_batch_ratio",
            "duplicate_generated_at_ratio",
            "duplicate_fingerprint_ratio",
        ):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known trend batch health status")
        object.__setattr__(
            self,
            "gate_results",
            _clone_trend_batch_gate_results(self.gate_results),
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
        _validate_trend_batch_report_rows(self)
        if self.status != _trend_batch_status(self.gate_results):
            raise ValueError("status must match trend batch health gate results")


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(
        self,
        report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
    ) -> None:
        if type(report) is not TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport:
            raise ValueError(
                "report must be a "
                "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport"
            )
        validated = _validate_trend_batch_report_tree(report)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True)
        line += "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
    trend_batch_reports: (
        list[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport]
        | tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport, ...]
    ),
    *,
    config: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig,
    generated_at: datetime,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport:
    if type(config) is not TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig:
        raise ValueError(
            "config must be a "
            "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig"
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    reports = _normalize_trend_batch_report_inputs(trend_batch_reports)
    total = len(reports)
    status_counts = _build_status_counts(reports)
    ready_count = status_counts[
        "proposal_evidence_comparison_history_batch_health_trend_batch_ready"
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
        trend_batch_report_count=total,
        incomplete_ratio=incomplete_ratio,
        duplicate_generated_at_ratio=duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=duplicate_fingerprint_ratio,
        config=config,
    )
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_only=True,
        boundary_statement=config.boundary_statement,
        trend_batch_report_count=total,
        ready_trend_batch_report_count=ready_count,
        incomplete_trend_batch_report_count=status_counts[
            "incomplete_batch_health_trend_batch"
        ],
        duplicate_generated_at_trend_batch_report_count=status_counts[
            "duplicate_generated_at_batch_health_trend_batch"
        ],
        duplicate_fingerprint_trend_batch_report_count=status_counts[
            "duplicate_fingerprint_batch_health_trend_batch"
        ],
        duplicate_generated_at_count=duplicate_generated_at_count,
        duplicate_fingerprint_count=duplicate_fingerprint_count,
        incomplete_trend_batch_ratio=incomplete_ratio,
        duplicate_generated_at_ratio=duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=duplicate_fingerprint_ratio,
        first_trend_batch_generated_at=reports[0].generated_at if reports else None,
        last_trend_batch_generated_at=reports[-1].generated_at if reports else None,
        status=_trend_batch_status(gate_results),
        gate_results=gate_results,
        status_rows=_build_status_rows(status_counts, total),
        config_version_summaries=_config_version_summaries(reports),
        gate_status_summaries=_gate_status_summaries(reports),
        duplicate_generated_at_summaries=duplicate_generated_at_summaries,
        duplicate_fingerprint_summaries=duplicate_fingerprint_summaries,
    )


def _normalize_trend_batch_report_inputs(
    trend_batch_reports: (
        list[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport]
        | tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport, ...]
    ),
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport, ...]:
    if type(trend_batch_reports) not in (list, tuple):
        raise ValueError("trend_batch_reports must be a list or tuple of trend reports")
    supplied = tuple(trend_batch_reports)
    cloned = tuple(_clone_trend_batch_report(item) for item in supplied)
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


def _clone_trend_batch_report(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport:
    if type(report) is not TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport:
        raise ValueError(
            "trend_batch_reports must contain "
            "TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport values"
        )
    gate_results = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult(
            row.gate_name,
            row.status,
            row.message,
            row.observed_value,
            row.threshold,
        )
        for row in _normalize_typed_tuple(
            "gate_results",
            report.gate_results,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult,
        )
    )
    status_rows = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow(
            row.trend_status,
            row.trend_count,
            row.trend_ratio,
        )
        for row in _normalize_typed_tuple(
            "status_rows",
            report.status_rows,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow,
        )
    )
    config_version_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary(
            row.trend_config_version,
            row.trend_count,
        )
        for row in _normalize_typed_tuple(
            "config_version_summaries",
            report.config_version_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary,
        )
    )
    gate_status_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary(
            row.gate_name,
            row.gate_status,
            row.trend_count,
        )
        for row in _normalize_typed_tuple(
            "gate_status_summaries",
            report.gate_status_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary,
        )
    )
    duplicate_generated_at_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary(
            row.generated_at,
            row.duplicate_count,
        )
        for row in _normalize_typed_tuple(
            "duplicate_generated_at_summaries",
            report.duplicate_generated_at_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary,
        )
    )
    duplicate_fingerprint_summaries = tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary(
            row.report_fingerprint,
            row.duplicate_count,
        )
        for row in _normalize_typed_tuple(
            "duplicate_fingerprint_summaries",
            report.duplicate_fingerprint_summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary,
        )
    )
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport(
        generated_at=_as_utc(report.generated_at),
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        trend_report_count=report.trend_report_count,
        ready_trend_report_count=report.ready_trend_report_count,
        incomplete_trend_report_count=report.incomplete_trend_report_count,
        duplicate_generated_at_trend_report_count=(
            report.duplicate_generated_at_trend_report_count
        ),
        duplicate_fingerprint_trend_report_count=(
            report.duplicate_fingerprint_trend_report_count
        ),
        duplicate_generated_at_count=report.duplicate_generated_at_count,
        duplicate_fingerprint_count=report.duplicate_fingerprint_count,
        incomplete_trend_ratio=report.incomplete_trend_ratio,
        duplicate_generated_at_ratio=report.duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=report.duplicate_fingerprint_ratio,
        first_trend_generated_at=report.first_trend_generated_at,
        last_trend_generated_at=report.last_trend_generated_at,
        status=report.status,
        gate_results=gate_results,
        status_rows=status_rows,
        config_version_summaries=config_version_summaries,
        gate_status_summaries=gate_status_summaries,
        duplicate_generated_at_summaries=duplicate_generated_at_summaries,
        duplicate_fingerprint_summaries=duplicate_fingerprint_summaries,
    )


def _build_status_counts(
    reports: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport, ...],
) -> dict[str, int]:
    counts = {status: 0 for status in TREND_BATCH_STATUSES}
    for report in reports:
        counts[report.status] += 1
    return counts


def _build_gate_results(
    *,
    trend_batch_report_count: int,
    incomplete_ratio: Decimal | None,
    duplicate_generated_at_ratio: Decimal | None,
    duplicate_fingerprint_ratio: Decimal | None,
    config: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig,
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult, ...]:
    sample_passes = trend_batch_report_count >= config.min_trend_batch_report_count
    return (
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult(
            "trend_batch_sample",
            "pass" if sample_passes else "incomplete",
            (
                "Supplied trend batch report sample meets the threshold."
                if sample_passes
                else "Supplied trend batch report sample is below the threshold."
            ),
            trend_batch_report_count,
            config.min_trend_batch_report_count,
        ),
        _rate_gate(
            "incomplete_trend_batch_rate",
            incomplete_ratio,
            config.max_incomplete_trend_batch_ratio,
            "Incomplete trend batch",
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
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult:
    if ratio is None:
        status = "incomplete"
        message = f"{label} rate is unavailable without trend batch reports."
    elif ratio <= threshold:
        status = "pass"
        message = f"{label} rate is within the threshold."
    else:
        status = "fail"
        message = f"{label} rate exceeds the threshold."
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult(
        gate_name,
        status,
        message,
        ratio,
        threshold,
    )


def _build_status_rows(
    status_counts: dict[str, int],
    total: int,
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow(
            status,
            status_counts[status],
            _ratio(status_counts[status], total),
        )
        for status in TREND_BATCH_STATUSES
    )


def _config_version_summaries(
    reports: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport, ...],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary,
    ...,
]:
    counts: dict[str, int] = {}
    for report in reports:
        counts[report.config_version] = counts.get(report.config_version, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary(
            config_version,
            count,
        )
        for config_version, count in sorted(counts.items())
    )


def _gate_status_summaries(
    reports: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport, ...],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary,
    ...,
]:
    counts: dict[tuple[str, str], int] = {}
    for report in reports:
        report_keys = {(row.gate_name, row.status) for row in report.gate_results}
        for key in report_keys:
            counts[key] = counts.get(key, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
            gate_name,
            gate_status,
            count,
        )
        for (gate_name, gate_status), count in sorted(counts.items())
    )


def _duplicate_generated_at_summaries(
    reports: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport, ...],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary,
    ...,
]:
    counts: dict[datetime, int] = {}
    for report in reports:
        counts[report.generated_at] = counts.get(report.generated_at, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary(
            generated_at,
            count,
        )
        for generated_at, count in sorted(counts.items())
        if count >= 2
    )


def _duplicate_fingerprint_summaries(
    reports: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport, ...],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary,
    ...,
]:
    counts: dict[str, int] = {}
    for report in reports:
        fingerprint = _trend_batch_report_fingerprint(report)
        counts[fingerprint] = counts.get(fingerprint, 0) + 1
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary(
            fingerprint,
            count,
        )
        for fingerprint, count in sorted(counts.items())
        if count >= 2
    )


def _trend_batch_report_fingerprint(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport,
) -> str:
    return json.dumps(_json_ready(asdict(report)), allow_nan=False, sort_keys=True)


def _trend_batch_status(
    gate_results: tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult, ...],
) -> str:
    gates = {row.gate_name: row.status for row in gate_results}
    if gates["trend_batch_sample"] == "incomplete":
        return "incomplete_batch_health_trend_batch_health"
    if gates["duplicate_generated_at_rate"] == "fail":
        return "duplicate_generated_at_batch_health_trend_batch_health"
    if gates["duplicate_fingerprint_rate"] == "fail":
        return "duplicate_fingerprint_batch_health_trend_batch_health"
    if gates["incomplete_trend_batch_rate"] == "fail":
        return "incomplete_batch_health_trend_batch_health"
    if any(status == "incomplete" for status in gates.values()):
        return "incomplete_batch_health_trend_batch_health"
    return "proposal_evidence_comparison_history_batch_health_trend_batch_health_ready"


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _validate_trend_batch_report_tree(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport:
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        trend_batch_report_count=report.trend_batch_report_count,
        ready_trend_batch_report_count=report.ready_trend_batch_report_count,
        incomplete_trend_batch_report_count=report.incomplete_trend_batch_report_count,
        duplicate_generated_at_trend_batch_report_count=(
            report.duplicate_generated_at_trend_batch_report_count
        ),
        duplicate_fingerprint_trend_batch_report_count=(
            report.duplicate_fingerprint_trend_batch_report_count
        ),
        duplicate_generated_at_count=report.duplicate_generated_at_count,
        duplicate_fingerprint_count=report.duplicate_fingerprint_count,
        incomplete_trend_batch_ratio=report.incomplete_trend_batch_ratio,
        duplicate_generated_at_ratio=report.duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=report.duplicate_fingerprint_ratio,
        first_trend_batch_generated_at=report.first_trend_batch_generated_at,
        last_trend_batch_generated_at=report.last_trend_batch_generated_at,
        status=report.status,
        gate_results=report.gate_results,
        status_rows=report.status_rows,
        config_version_summaries=report.config_version_summaries,
        gate_status_summaries=report.gate_status_summaries,
        duplicate_generated_at_summaries=report.duplicate_generated_at_summaries,
        duplicate_fingerprint_summaries=report.duplicate_fingerprint_summaries,
    )


def _validate_trend_batch_report_rows(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
) -> None:
    if tuple(row.gate_name for row in report.gate_results) != GATE_NAMES:
        raise ValueError("gate_results must contain trend batch health gates")
    status_row_keys = tuple(row.trend_batch_status for row in report.status_rows)
    if status_row_keys != TREND_BATCH_STATUSES:
        raise ValueError("status_rows must contain sorted trend batch statuses")
    status_counts = {row.trend_batch_status: row.trend_batch_count for row in report.status_rows}
    if status_counts[
        "proposal_evidence_comparison_history_batch_health_trend_batch_ready"
    ] != report.ready_trend_batch_report_count:
        raise ValueError("status_rows must match ready trend batch count")
    if status_counts["incomplete_batch_health_trend_batch"] != (
        report.incomplete_trend_batch_report_count
    ):
        raise ValueError("status_rows must match incomplete trend batch count")
    if status_counts["duplicate_generated_at_batch_health_trend_batch"] != (
        report.duplicate_generated_at_trend_batch_report_count
    ):
        raise ValueError("status_rows must match duplicate generated-at trend batch count")
    if status_counts["duplicate_fingerprint_batch_health_trend_batch"] != (
        report.duplicate_fingerprint_trend_batch_report_count
    ):
        raise ValueError("status_rows must match duplicate fingerprint trend batch count")
    if sum(status_counts.values()) != report.trend_batch_report_count:
        raise ValueError("status_rows must sum to trend_batch_report_count")
    expected_ratios = {
        status: _ratio(count, report.trend_batch_report_count)
        for status, count in status_counts.items()
    }
    for row in report.status_rows:
        if not _ratio_value_matches(
            row.trend_batch_ratio,
            expected_ratios[row.trend_batch_status],
        ):
            raise ValueError("status_rows must contain expected ratios")
    expected_incomplete = report.trend_batch_report_count - report.ready_trend_batch_report_count
    _validate_ratio_field(report, "incomplete_trend_batch_ratio", expected_incomplete)
    _validate_duplicate_summaries(report)
    _validate_time_bounds(report)
    _validate_config_version_summaries(report)
    _validate_gate_status_summaries(report)
    _validate_gate_payloads(report)


def _validate_ratio_field(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
    field_name: str,
    count: int,
) -> None:
    expected = _ratio(count, report.trend_batch_report_count)
    if not _ratio_value_matches(getattr(report, field_name), expected):
        raise ValueError(f"{field_name} must match derived ratio")


def _ratio_value_matches(value: Decimal | None, expected: Decimal | None) -> bool:
    if value != expected:
        return False
    if expected is None:
        return value is None
    if type(value) is not Decimal:
        return False
    return (
        value == value.quantize(RATIO_QUANTUM)
        and value.as_tuple().exponent == RATIO_QUANTUM.as_tuple().exponent
    )


def _validate_time_bounds(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
) -> None:
    if report.trend_batch_report_count == 0:
        if (
            report.first_trend_batch_generated_at is not None
            or report.last_trend_batch_generated_at is not None
        ):
            raise ValueError("trend batch time bounds must be empty without reports")
    else:
        if (
            report.first_trend_batch_generated_at is None
            or report.last_trend_batch_generated_at is None
        ):
            raise ValueError("trend batch time bounds must be present with reports")
        if report.first_trend_batch_generated_at > report.last_trend_batch_generated_at:
            raise ValueError("trend batch time bounds must be ordered")


def _validate_duplicate_summaries(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
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
        if (
            report.first_trend_batch_generated_at is None
            or report.last_trend_batch_generated_at is None
            or row.generated_at < report.first_trend_batch_generated_at
            or row.generated_at > report.last_trend_batch_generated_at
        ):
            raise ValueError("duplicate_generated_at_summaries must be within time bounds")
        if row.duplicate_count > report.trend_batch_report_count:
            raise ValueError("duplicate_generated_at_summaries must not exceed count")
    for row in report.duplicate_fingerprint_summaries:
        if row.duplicate_count > report.trend_batch_report_count:
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
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
) -> None:
    versions = tuple(row.trend_batch_config_version for row in report.config_version_summaries)
    if versions != tuple(sorted(versions)):
        raise ValueError("config_version_summaries must be sorted")
    if len(set(versions)) != len(versions):
        raise ValueError("config_version_summaries must not contain duplicates")
    if sum(row.trend_batch_count for row in report.config_version_summaries) != (
        report.trend_batch_report_count
    ):
        raise ValueError("config_version_summaries must sum to report count")


def _validate_gate_status_summaries(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
) -> None:
    keys = tuple((row.gate_name, row.gate_status) for row in report.gate_status_summaries)
    if keys != tuple(sorted(keys)):
        raise ValueError("gate_status_summaries must be sorted")
    if len(set(keys)) != len(keys):
        raise ValueError("gate_status_summaries must not contain duplicates")
    expected_gate_status_count = (
        len(NODE_13_TREND_BATCH_GATE_NAMES) * report.trend_batch_report_count
    )
    observed_gate_status_count = sum(
        row.trend_batch_count for row in report.gate_status_summaries
    )
    if observed_gate_status_count != expected_gate_status_count:
        raise ValueError("gate_status_summaries must account for all gate rows")
    for gate_name in NODE_13_TREND_BATCH_GATE_NAMES:
        gate_count = sum(
            row.trend_batch_count
            for row in report.gate_status_summaries
            if row.gate_name == gate_name
        )
        if gate_count != report.trend_batch_report_count:
            raise ValueError("gate_status_summaries must account for every gate")
    for row in report.gate_status_summaries:
        if row.gate_name == "trend_sample" and row.gate_status == "fail":
            raise ValueError("gate_status_summaries contain impossible sample gate status")
        if row.trend_batch_count > report.trend_batch_report_count:
            raise ValueError("gate_status_summaries must not exceed report count")


def _validate_gate_payloads(
    report: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
) -> None:
    gates = {row.gate_name: row for row in report.gate_results}
    sample_gate = gates["trend_batch_sample"]
    if type(sample_gate.observed_value) is not int:
        raise ValueError("gate_results trend_batch_sample observed_value must be an int")
    if sample_gate.observed_value != report.trend_batch_report_count:
        raise ValueError("gate_results must match trend_batch_report_count")
    if type(sample_gate.threshold) is not int:
        raise ValueError("gate_results trend_batch_sample threshold must be an int")
    _require_nonnegative_int(
        "gate_results trend_batch_sample threshold",
        sample_gate.threshold,
    )
    expected_sample_status = (
        "pass" if report.trend_batch_report_count >= sample_gate.threshold else "incomplete"
    )
    if sample_gate.status != expected_sample_status:
        raise ValueError("gate_results trend_batch_sample status must match threshold")
    _validate_rate_gate_payload(
        gates["incomplete_trend_batch_rate"],
        report.incomplete_trend_batch_ratio,
        "gate_results incomplete_trend_batch_rate",
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
    gate: TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult,
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
    if not _ratio_value_matches(gate.observed_value, ratio):
        raise ValueError(f"{field_name} observed_value must match report ratio")
    expected_status = "pass" if ratio <= gate.threshold else "fail"
    if gate.status != expected_status:
        raise ValueError(f"{field_name} status must match threshold")


def _clone_trend_batch_gate_results(
    gate_results: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult,
        ...,
    ],
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult(
            row.gate_name,
            row.status,
            row.message,
            row.observed_value,
            row.threshold,
        )
        for row in _normalize_typed_tuple(
            "gate_results",
            gate_results,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult,
        )
    )


def _clone_status_rows(
    status_rows: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow,
        ...,
    ],
) -> tuple[TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow, ...]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow(
            row.trend_batch_status,
            row.trend_batch_count,
            row.trend_batch_ratio,
        )
        for row in _normalize_typed_tuple(
            "status_rows",
            status_rows,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow,
        )
    )


def _clone_config_version_summaries(
    summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary,
        ...,
    ],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary,
    ...,
]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary(
            row.trend_batch_config_version,
            row.trend_batch_count,
        )
        for row in _normalize_typed_tuple(
            "config_version_summaries",
            summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary,
        )
    )


def _clone_gate_status_summaries(
    summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary,
        ...,
    ],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary,
    ...,
]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
            row.gate_name,
            row.gate_status,
            row.trend_batch_count,
        )
        for row in _normalize_typed_tuple(
            "gate_status_summaries",
            summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary,
        )
    )


def _clone_duplicate_generated_at_summaries(
    summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary,
        ...,
    ],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary,
    ...,
]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary(
            row.generated_at,
            row.duplicate_count,
        )
        for row in _normalize_typed_tuple(
            "duplicate_generated_at_summaries",
            summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary,
        )
    )


def _clone_duplicate_fingerprint_summaries(
    summaries: tuple[
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary,
        ...,
    ],
) -> tuple[
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary,
    ...,
]:
    return tuple(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary(
            row.report_fingerprint,
            row.duplicate_count,
        )
        for row in _normalize_typed_tuple(
            "duplicate_fingerprint_summaries",
            summaries,
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary,
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


def _require_boundary_statement(value: str) -> None:
    _require_canonical_string("boundary_statement", value)
    if (
        value
        != DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_HISTORY_BATCH_HEALTH_TREND_BATCH_HEALTH_BOUNDARY_STATEMENT
    ):
        raise ValueError(
            "boundary_statement must describe report-only proposal evidence comparison "
            "history batch health trend batch health"
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
