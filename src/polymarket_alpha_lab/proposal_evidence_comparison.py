"""Report-only proposal evidence comparison artifacts for Level 2."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceBucket,
    PaperForecastEvidenceGateResult,
    PaperForecastEvidenceReport,
)
from polymarket_alpha_lab.proposal_review_dossier_batch import (
    TradeProposalReviewDossierBatchConfigVersionSummary,
    TradeProposalReviewDossierBatchDuplicateSummary,
    TradeProposalReviewDossierBatchFindingSummary,
    TradeProposalReviewDossierBatchGateResult,
    TradeProposalReviewDossierBatchReport,
    TradeProposalReviewDossierBatchSourceSummary,
)


__all__ = (
    "TradeProposalEvidenceComparisonConfig",
    "TradeProposalEvidenceComparisonGateResult",
    "TradeProposalEvidenceComparisonSourceRow",
    "TradeProposalEvidenceComparisonMetricRow",
    "TradeProposalEvidenceComparisonFindingRow",
    "TradeProposalEvidenceComparisonReport",
    "TradeProposalEvidenceComparisonLog",
    "build_trade_proposal_evidence_comparison_report",
)

DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_BOUNDARY_STATEMENT = (
    "This is a report-only proposal evidence comparison artifact over supplied "
    "forecast evidence and proposal-review dossier batch reports, not an "
    "approval workflow, proposal approval, approved-proposal selector, "
    "latest-decision selector, decision-resolution process, investment ranking, "
    "trade recommendation, strategy-promotion signal, trade instruction, order "
    "instruction, broker request, order request, account action, account "
    "authentication, private-key handling, wallet signature, live-execution "
    "signal, credential workflow, external-history loader, JSONL reader, "
    "scraping workflow, settlement review, reconciliation process, compliance "
    "review, geographic access analysis, or automatic order-placement "
    "authorization."
)

ZERO = Decimal("0")
ONE = Decimal("1")
GATE_NAMES = (
    "source_sample",
    "forecast_evidence_status",
    "dossier_batch_status",
    "evidence_consistency",
)
GATE_STATUSES = ("pass", "fail", "incomplete")
REPORT_STATUSES = (
    "incomplete_evidence_comparison",
    "divergent_evidence_comparison",
    "unstable_evidence_comparison",
    "proposal_evidence_comparison_complete",
)
FINDING_SEVERITIES = (
    "incomplete",
    "divergent",
    "unstable",
)
SOURCE_NAMES = ("dossier_batch", "forecast_evidence")
FINDING_SOURCE_NAMES = ("comparison", *SOURCE_NAMES)
STATUS_CATEGORIES = ("complete", "incomplete", "inconsistent", "unstable")
FORECAST_STATUSES = (
    "incomplete_data",
    "insufficient_evidence",
    "blocked_by_quality",
    "paper_review_ready",
)
DOSSIER_BATCH_STATUSES = (
    "incomplete_dossier_batch",
    "inconsistent_dossier_batch",
    "unstable_dossier_batch",
    "proposal_review_dossier_batch_ready",
)
METRIC_KEYS = (
    ("dossier_batch", "complete_dossier_count"),
    ("dossier_batch", "dossier_count"),
    ("dossier_batch", "incomplete_dossier_ratio"),
    ("dossier_batch", "inconsistent_dossier_ratio"),
    ("dossier_batch", "unstable_dossier_ratio"),
    ("forecast_evidence", "forecast_edge_observation_count"),
    ("forecast_evidence", "forecast_observation_count"),
    ("forecast_evidence", "forecast_probability_observation_count"),
    ("forecast_evidence", "mean_edge_gap_ratio"),
    ("forecast_evidence", "mean_probability_loss"),
    ("forecast_evidence", "positive_edge_hit_rate"),
    ("forecast_evidence", "worst_bucket_error"),
    ("forecast_evidence", "worst_residual_exposure_ratio"),
)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonConfig:
    config_version: str
    min_forecast_observation_count: int = 1
    min_dossier_count: int = 1
    max_incomplete_dossier_ratio: Decimal = Decimal("0.0000")
    max_inconsistent_dossier_ratio: Decimal = Decimal("0.0000")
    max_unstable_dossier_ratio: Decimal = Decimal("0.0000")
    require_forecast_ready: bool = True
    require_dossier_batch_ready: bool = True
    boundary_statement: str = DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_BOUNDARY_STATEMENT

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_forecast_observation_count",
            self.min_forecast_observation_count,
        )
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
        _require_bool("require_forecast_ready", self.require_forecast_ready)
        _require_bool("require_dossier_batch_ready", self.require_dossier_batch_ready)
        _require_boundary_statement(self.boundary_statement)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonGateResult:
    gate_name: str
    status: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known evidence comparison gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known evidence comparison gate status")
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonSourceRow:
    source_name: str
    source_status: str
    generated_at: datetime
    sample_count: int
    status_category: str

    def __post_init__(self) -> None:
        if self.source_name not in SOURCE_NAMES:
            raise ValueError("source_name must be a known comparison source")
        _require_canonical_string("source_status", self.source_status)
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_nonnegative_int("sample_count", self.sample_count)
        if self.status_category not in STATUS_CATEGORIES:
            raise ValueError("status_category must be a known source status category")


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonMetricRow:
    metric_name: str
    source_name: str
    observed_value: Decimal | int | str | None
    threshold: Decimal | int | str | None
    status: str

    def __post_init__(self) -> None:
        _require_canonical_string("metric_name", self.metric_name)
        if self.source_name not in SOURCE_NAMES:
            raise ValueError("source_name must be a known comparison source")
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known metric status")


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonFindingRow:
    finding_code: str
    severity: str
    source_name: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        _require_canonical_string("finding_code", self.finding_code)
        if self.severity not in FINDING_SEVERITIES:
            raise ValueError("severity must be a known evidence comparison severity")
        if self.source_name not in FINDING_SOURCE_NAMES:
            raise ValueError("source_name must be a known finding source")
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonReport:
    generated_at: datetime
    config_version: str
    report_only: bool
    boundary_statement: str
    forecast_evidence_generated_at: datetime
    dossier_batch_generated_at: datetime
    forecast_status: str
    dossier_batch_status: str
    forecast_observation_count: int
    forecast_probability_observation_count: int
    forecast_edge_observation_count: int
    dossier_count: int
    complete_dossier_count: int
    incomplete_dossier_ratio: Decimal | None
    inconsistent_dossier_ratio: Decimal | None
    unstable_dossier_ratio: Decimal | None
    mean_probability_loss: Decimal | None
    worst_bucket_error: Decimal | None
    mean_edge_gap_ratio: Decimal | None
    positive_edge_hit_rate: Decimal | None
    worst_residual_exposure_ratio: Decimal | None
    status: str
    gate_results: tuple[TradeProposalEvidenceComparisonGateResult, ...]
    source_rows: tuple[TradeProposalEvidenceComparisonSourceRow, ...]
    metric_rows: tuple[TradeProposalEvidenceComparisonMetricRow, ...]
    finding_rows: tuple[TradeProposalEvidenceComparisonFindingRow, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "forecast_evidence_generated_at",
            _as_utc(self.forecast_evidence_generated_at),
        )
        object.__setattr__(
            self,
            "dossier_batch_generated_at",
            _as_utc(self.dossier_batch_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        _require_boundary_statement(self.boundary_statement)
        if self.forecast_status not in FORECAST_STATUSES:
            raise ValueError("forecast_status must be a known forecast status")
        if self.dossier_batch_status not in DOSSIER_BATCH_STATUSES:
            raise ValueError("dossier_batch_status must be a known dossier batch status")
        for field_name in (
            "forecast_observation_count",
            "forecast_probability_observation_count",
            "forecast_edge_observation_count",
            "dossier_count",
            "complete_dossier_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
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
        _require_optional_nonnegative_decimal(
            "mean_probability_loss",
            self.mean_probability_loss,
        )
        _require_optional_nonnegative_decimal("worst_bucket_error", self.worst_bucket_error)
        _require_optional_nonnegative_decimal("mean_edge_gap_ratio", self.mean_edge_gap_ratio)
        _require_optional_probability_decimal(
            "positive_edge_hit_rate",
            self.positive_edge_hit_rate,
        )
        _require_optional_probability_decimal(
            "worst_residual_exposure_ratio",
            self.worst_residual_exposure_ratio,
        )
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known evidence comparison report status")
        object.__setattr__(
            self,
            "gate_results",
            _normalize_typed_tuple(
                "gate_results",
                self.gate_results,
                TradeProposalEvidenceComparisonGateResult,
            ),
        )
        object.__setattr__(
            self,
            "source_rows",
            _normalize_typed_tuple(
                "source_rows",
                self.source_rows,
                TradeProposalEvidenceComparisonSourceRow,
            ),
        )
        object.__setattr__(
            self,
            "metric_rows",
            _normalize_typed_tuple(
                "metric_rows",
                self.metric_rows,
                TradeProposalEvidenceComparisonMetricRow,
            ),
        )
        object.__setattr__(
            self,
            "finding_rows",
            _normalize_typed_tuple(
                "finding_rows",
                self.finding_rows,
                TradeProposalEvidenceComparisonFindingRow,
            ),
        )
        _validate_report_rows(self)
        if self.status != _comparison_status(self.gate_results):
            raise ValueError("status must match evidence comparison gate results")


@dataclass(frozen=True)
class TradeProposalEvidenceComparisonLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: TradeProposalEvidenceComparisonReport) -> None:
        if type(report) is not TradeProposalEvidenceComparisonReport:
            raise ValueError("report must be a TradeProposalEvidenceComparisonReport")
        validated = _validate_report_tree(report)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True)
        line += "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_trade_proposal_evidence_comparison_report(
    *,
    forecast_evidence: PaperForecastEvidenceReport,
    dossier_batch: TradeProposalReviewDossierBatchReport,
    config: TradeProposalEvidenceComparisonConfig,
    generated_at: datetime,
) -> TradeProposalEvidenceComparisonReport:
    if type(config) is not TradeProposalEvidenceComparisonConfig:
        raise ValueError("config must be a TradeProposalEvidenceComparisonConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    forecast = _clone_forecast_report(forecast_evidence)
    batch = _clone_dossier_batch_report(dossier_batch)
    gate_results = _build_gate_results(
        forecast=forecast,
        batch=batch,
        config=config,
    )
    return TradeProposalEvidenceComparisonReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_only=True,
        boundary_statement=config.boundary_statement,
        forecast_evidence_generated_at=forecast.generated_at,
        dossier_batch_generated_at=batch.generated_at,
        forecast_status=forecast.status,
        dossier_batch_status=batch.status,
        forecast_observation_count=forecast.observation_count,
        forecast_probability_observation_count=forecast.probability_observation_count,
        forecast_edge_observation_count=forecast.edge_observation_count,
        dossier_count=batch.dossier_count,
        complete_dossier_count=batch.complete_dossier_count,
        incomplete_dossier_ratio=batch.incomplete_dossier_ratio,
        inconsistent_dossier_ratio=batch.inconsistent_dossier_ratio,
        unstable_dossier_ratio=batch.unstable_dossier_ratio,
        mean_probability_loss=forecast.mean_probability_loss,
        worst_bucket_error=forecast.worst_bucket_error,
        mean_edge_gap_ratio=forecast.mean_edge_gap_ratio,
        positive_edge_hit_rate=forecast.positive_edge_hit_rate,
        worst_residual_exposure_ratio=forecast.worst_residual_exposure_ratio,
        status=_comparison_status(gate_results),
        gate_results=gate_results,
        source_rows=_build_source_rows(forecast, batch),
        metric_rows=_build_metric_rows(forecast, batch, config),
        finding_rows=_build_finding_rows(gate_results, forecast, batch),
    )


def _build_gate_results(
    *,
    forecast: PaperForecastEvidenceReport,
    batch: TradeProposalReviewDossierBatchReport,
    config: TradeProposalEvidenceComparisonConfig,
) -> tuple[TradeProposalEvidenceComparisonGateResult, ...]:
    source_sample_passes = (
        forecast.observation_count >= config.min_forecast_observation_count
        and batch.dossier_count >= config.min_dossier_count
    )
    source_sample = TradeProposalEvidenceComparisonGateResult(
        gate_name="source_sample",
        status="pass" if source_sample_passes else "incomplete",
        message=(
            "Supplied forecast evidence and dossier batch samples meet thresholds."
            if source_sample_passes
            else "Supplied forecast evidence or dossier batch sample is below threshold."
        ),
        observed_value=f"forecast={forecast.observation_count}; dossier={batch.dossier_count}",
        threshold=(
            f"forecast>={config.min_forecast_observation_count}; "
            f"dossier>={config.min_dossier_count}"
        ),
    )
    forecast_gate = _forecast_status_gate(forecast, config)
    batch_gate = _dossier_batch_status_gate(batch, config)
    consistency_passes = forecast_gate.status == batch_gate.status
    consistency = TradeProposalEvidenceComparisonGateResult(
        gate_name="evidence_consistency",
        status="pass" if consistency_passes else "fail",
        message=(
            "Forecast evidence and dossier batch gate statuses match."
            if consistency_passes
            else "Forecast evidence and dossier batch gate statuses differ."
        ),
        observed_value=f"forecast={forecast_gate.status}; dossier={batch_gate.status}",
        threshold="matching_status_categories",
    )
    return (source_sample, forecast_gate, batch_gate, consistency)


def _forecast_status_gate(
    forecast: PaperForecastEvidenceReport,
    config: TradeProposalEvidenceComparisonConfig,
) -> TradeProposalEvidenceComparisonGateResult:
    if not config.require_forecast_ready:
        return TradeProposalEvidenceComparisonGateResult(
            gate_name="forecast_evidence_status",
            status="pass",
            message="Forecast evidence readiness is recorded for context only.",
            observed_value=forecast.status,
            threshold="not_required",
        )
    if forecast.status == "paper_review_ready":
        status = "pass"
        message = "Forecast evidence report is paper-review ready."
    elif forecast.status in ("incomplete_data", "insufficient_evidence"):
        status = "incomplete"
        message = "Forecast evidence report is incomplete or insufficient."
    else:
        status = "fail"
        message = "Forecast evidence report is blocked by quality gates."
    return TradeProposalEvidenceComparisonGateResult(
        gate_name="forecast_evidence_status",
        status=status,
        message=message,
        observed_value=forecast.status,
        threshold="paper_review_ready",
    )


def _dossier_batch_status_gate(
    batch: TradeProposalReviewDossierBatchReport,
    config: TradeProposalEvidenceComparisonConfig,
) -> TradeProposalEvidenceComparisonGateResult:
    threshold = (
        "status=proposal_review_dossier_batch_ready; "
        f"incomplete<={config.max_incomplete_dossier_ratio}; "
        f"inconsistent<={config.max_inconsistent_dossier_ratio}; "
        f"unstable<={config.max_unstable_dossier_ratio}"
    )
    if not config.require_dossier_batch_ready:
        return TradeProposalEvidenceComparisonGateResult(
            gate_name="dossier_batch_status",
            status="pass",
            message="Dossier batch readiness is recorded for context only.",
            observed_value=batch.status,
            threshold="not_required",
        )
    ratios_available = (
        batch.incomplete_dossier_ratio is not None
        and batch.inconsistent_dossier_ratio is not None
        and batch.unstable_dossier_ratio is not None
    )
    ratios_pass = (
        ratios_available
        and batch.incomplete_dossier_ratio <= config.max_incomplete_dossier_ratio
        and batch.inconsistent_dossier_ratio <= config.max_inconsistent_dossier_ratio
        and batch.unstable_dossier_ratio <= config.max_unstable_dossier_ratio
    )
    if batch.status == "proposal_review_dossier_batch_ready" and ratios_pass:
        status = "pass"
        message = "Dossier batch health report is ready and within thresholds."
    elif batch.status == "incomplete_dossier_batch":
        status = "incomplete"
        message = "Dossier batch health report is incomplete."
    else:
        status = "fail"
        message = "Dossier batch health report is unstable or inconsistent."
    return TradeProposalEvidenceComparisonGateResult(
        gate_name="dossier_batch_status",
        status=status,
        message=message,
        observed_value=(
            f"status={batch.status}; "
            f"incomplete={batch.incomplete_dossier_ratio}; "
            f"inconsistent={batch.inconsistent_dossier_ratio}; "
            f"unstable={batch.unstable_dossier_ratio}"
        ),
        threshold=threshold,
    )


def _build_source_rows(
    forecast: PaperForecastEvidenceReport,
    batch: TradeProposalReviewDossierBatchReport,
) -> tuple[TradeProposalEvidenceComparisonSourceRow, ...]:
    return tuple(
        sorted(
            (
                TradeProposalEvidenceComparisonSourceRow(
                    source_name="forecast_evidence",
                    source_status=forecast.status,
                    generated_at=forecast.generated_at,
                    sample_count=forecast.observation_count,
                    status_category=_forecast_status_category(forecast.status),
                ),
                TradeProposalEvidenceComparisonSourceRow(
                    source_name="dossier_batch",
                    source_status=batch.status,
                    generated_at=batch.generated_at,
                    sample_count=batch.dossier_count,
                    status_category=_dossier_batch_status_category(batch.status),
                ),
            ),
            key=lambda row: row.source_name,
        ),
    )


def _build_metric_rows(
    forecast: PaperForecastEvidenceReport,
    batch: TradeProposalReviewDossierBatchReport,
    config: TradeProposalEvidenceComparisonConfig,
) -> tuple[TradeProposalEvidenceComparisonMetricRow, ...]:
    forecast_gates = _gate_by_name(forecast.gate_results)
    sample_gate = forecast_gates["sample_size"]
    probability_gate = forecast_gates["probability_quality"]
    edge_gate = forecast_gates["executable_edge_quality"]
    residual_gate = forecast_gates["residual_exposure"]
    rows = (
        TradeProposalEvidenceComparisonMetricRow(
            metric_name="forecast_observation_count",
            source_name="forecast_evidence",
            observed_value=forecast.observation_count,
            threshold=config.min_forecast_observation_count,
            status=(
                "pass"
                if forecast.observation_count >= config.min_forecast_observation_count
                else "incomplete"
            ),
        ),
        TradeProposalEvidenceComparisonMetricRow(
            metric_name="forecast_probability_observation_count",
            source_name="forecast_evidence",
            observed_value=forecast.probability_observation_count,
            threshold=sample_gate.threshold,
            status=sample_gate.status,
        ),
        TradeProposalEvidenceComparisonMetricRow(
            metric_name="forecast_edge_observation_count",
            source_name="forecast_evidence",
            observed_value=forecast.edge_observation_count,
            threshold=sample_gate.threshold,
            status=sample_gate.status,
        ),
        TradeProposalEvidenceComparisonMetricRow(
            metric_name="mean_probability_loss",
            source_name="forecast_evidence",
            observed_value=forecast.mean_probability_loss,
            threshold=probability_gate.threshold,
            status=probability_gate.status,
        ),
        TradeProposalEvidenceComparisonMetricRow(
            metric_name="worst_bucket_error",
            source_name="forecast_evidence",
            observed_value=forecast.worst_bucket_error,
            threshold=probability_gate.threshold,
            status=probability_gate.status,
        ),
        TradeProposalEvidenceComparisonMetricRow(
            metric_name="mean_edge_gap_ratio",
            source_name="forecast_evidence",
            observed_value=forecast.mean_edge_gap_ratio,
            threshold=edge_gate.threshold,
            status=edge_gate.status,
        ),
        TradeProposalEvidenceComparisonMetricRow(
            metric_name="positive_edge_hit_rate",
            source_name="forecast_evidence",
            observed_value=forecast.positive_edge_hit_rate,
            threshold=edge_gate.threshold,
            status=edge_gate.status,
        ),
        TradeProposalEvidenceComparisonMetricRow(
            metric_name="worst_residual_exposure_ratio",
            source_name="forecast_evidence",
            observed_value=forecast.worst_residual_exposure_ratio,
            threshold=residual_gate.threshold,
            status=residual_gate.status,
        ),
        TradeProposalEvidenceComparisonMetricRow(
            metric_name="dossier_count",
            source_name="dossier_batch",
            observed_value=batch.dossier_count,
            threshold=config.min_dossier_count,
            status="pass" if batch.dossier_count >= config.min_dossier_count else "incomplete",
        ),
        TradeProposalEvidenceComparisonMetricRow(
            metric_name="complete_dossier_count",
            source_name="dossier_batch",
            observed_value=batch.complete_dossier_count,
            threshold=0,
            status="pass",
        ),
        _ratio_metric_row(
            metric_name="incomplete_dossier_ratio",
            observed_value=batch.incomplete_dossier_ratio,
            threshold=config.max_incomplete_dossier_ratio,
        ),
        _ratio_metric_row(
            metric_name="inconsistent_dossier_ratio",
            observed_value=batch.inconsistent_dossier_ratio,
            threshold=config.max_inconsistent_dossier_ratio,
        ),
        _ratio_metric_row(
            metric_name="unstable_dossier_ratio",
            observed_value=batch.unstable_dossier_ratio,
            threshold=config.max_unstable_dossier_ratio,
        ),
    )
    return tuple(sorted(rows, key=lambda row: (row.source_name, row.metric_name)))


def _ratio_metric_row(
    *,
    metric_name: str,
    observed_value: Decimal | None,
    threshold: Decimal,
) -> TradeProposalEvidenceComparisonMetricRow:
    if observed_value is None:
        status = "incomplete"
    elif observed_value <= threshold:
        status = "pass"
    else:
        status = "fail"
    return TradeProposalEvidenceComparisonMetricRow(
        metric_name=metric_name,
        source_name="dossier_batch",
        observed_value=observed_value,
        threshold=threshold,
        status=status,
    )


def _build_finding_rows(
    gate_results: tuple[TradeProposalEvidenceComparisonGateResult, ...],
    forecast: PaperForecastEvidenceReport,
    batch: TradeProposalReviewDossierBatchReport,
) -> tuple[TradeProposalEvidenceComparisonFindingRow, ...]:
    gates = {row.gate_name: row for row in gate_results}
    rows: list[TradeProposalEvidenceComparisonFindingRow] = []
    if gates["forecast_evidence_status"].status == "incomplete":
        rows.append(
            TradeProposalEvidenceComparisonFindingRow(
                finding_code="forecast_evidence_incomplete",
                severity="incomplete",
                source_name="forecast_evidence",
                message="Forecast evidence report is incomplete or insufficient.",
                observed_value=forecast.status,
                threshold="paper_review_ready",
            ),
        )
    if gates["forecast_evidence_status"].status == "fail":
        rows.append(
            TradeProposalEvidenceComparisonFindingRow(
                finding_code="forecast_evidence_unstable",
                severity="unstable",
                source_name="forecast_evidence",
                message="Forecast evidence report is blocked by quality gates.",
                observed_value=forecast.status,
                threshold="paper_review_ready",
            ),
        )
    if gates["dossier_batch_status"].status == "incomplete":
        rows.append(
            TradeProposalEvidenceComparisonFindingRow(
                finding_code="dossier_batch_incomplete",
                severity="incomplete",
                source_name="dossier_batch",
                message="Dossier batch health report is incomplete.",
                observed_value=batch.status,
                threshold="proposal_review_dossier_batch_ready",
            ),
        )
    if gates["dossier_batch_status"].status == "fail":
        rows.append(
            TradeProposalEvidenceComparisonFindingRow(
                finding_code="dossier_batch_unstable",
                severity="unstable",
                source_name="dossier_batch",
                message="Dossier batch health is unstable or inconsistent.",
                observed_value=batch.status,
                threshold="proposal_review_dossier_batch_ready",
            ),
        )
    if gates["evidence_consistency"].status == "fail":
        rows.append(
            TradeProposalEvidenceComparisonFindingRow(
                finding_code="evidence_consistency_divergent",
                severity="divergent",
                source_name="comparison",
                message="Forecast evidence and dossier batch gate statuses differ.",
                observed_value=gates["evidence_consistency"].observed_value,
                threshold="matching_status_categories",
            ),
        )
    return tuple(sorted(rows, key=lambda row: (row.severity, row.source_name, row.finding_code)))


def _comparison_status(
    gate_results: tuple[TradeProposalEvidenceComparisonGateResult, ...],
) -> str:
    gates = {row.gate_name: row.status for row in gate_results}
    if gates["source_sample"] == "incomplete":
        return "incomplete_evidence_comparison"
    if gates["evidence_consistency"] == "fail":
        return "divergent_evidence_comparison"
    if gates["forecast_evidence_status"] == "fail" or gates["dossier_batch_status"] == "fail":
        return "unstable_evidence_comparison"
    if any(status == "incomplete" for status in gates.values()):
        return "incomplete_evidence_comparison"
    return "proposal_evidence_comparison_complete"


def _forecast_status_category(status: str) -> str:
    if status == "paper_review_ready":
        return "complete"
    if status in ("incomplete_data", "insufficient_evidence"):
        return "incomplete"
    return "unstable"


def _dossier_batch_status_category(status: str) -> str:
    if status == "proposal_review_dossier_batch_ready":
        return "complete"
    if status == "incomplete_dossier_batch":
        return "incomplete"
    if status == "inconsistent_dossier_batch":
        return "inconsistent"
    return "unstable"


def _gate_by_name(
    gate_results: tuple[PaperForecastEvidenceGateResult, ...],
) -> dict[str, PaperForecastEvidenceGateResult]:
    return {row.gate_name: row for row in gate_results}


def _clone_forecast_report(
    report: PaperForecastEvidenceReport,
) -> PaperForecastEvidenceReport:
    if type(report) is not PaperForecastEvidenceReport:
        raise ValueError("forecast_evidence must be a PaperForecastEvidenceReport")
    raw_gate_results = _normalize_typed_tuple(
        "gate_results",
        report.gate_results,
        PaperForecastEvidenceGateResult,
    )
    raw_buckets = _normalize_typed_tuple(
        "buckets",
        report.buckets,
        PaperForecastEvidenceBucket,
    )
    gate_results = tuple(
        PaperForecastEvidenceGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in raw_gate_results
    )
    buckets = tuple(
        PaperForecastEvidenceBucket(
            bucket_label=row.bucket_label,
            lower_probability=row.lower_probability,
            upper_probability=row.upper_probability,
            observation_count=row.observation_count,
            mean_predicted_probability=row.mean_predicted_probability,
            observed_frequency=row.observed_frequency,
            bucket_error=row.bucket_error,
            mean_probability_loss=row.mean_probability_loss,
        )
        for row in raw_buckets
    )
    return PaperForecastEvidenceReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        first_observed_at=report.first_observed_at,
        last_observed_at=report.last_observed_at,
        observation_count=report.observation_count,
        probability_observation_count=report.probability_observation_count,
        edge_observation_count=report.edge_observation_count,
        unique_market_count=report.unique_market_count,
        unique_strategy_count=report.unique_strategy_count,
        unique_risk_tag_count=report.unique_risk_tag_count,
        mean_probability_loss=report.mean_probability_loss,
        worst_bucket_error=report.worst_bucket_error,
        mean_edge_gap_ratio=report.mean_edge_gap_ratio,
        positive_edge_hit_rate=report.positive_edge_hit_rate,
        worst_residual_exposure_ratio=report.worst_residual_exposure_ratio,
        status=report.status,
        gate_results=gate_results,
        buckets=buckets,
        paper_only=report.paper_only,
    )


def _clone_dossier_batch_report(
    report: TradeProposalReviewDossierBatchReport,
) -> TradeProposalReviewDossierBatchReport:
    if type(report) is not TradeProposalReviewDossierBatchReport:
        raise ValueError("dossier_batch must be a TradeProposalReviewDossierBatchReport")
    gate_results = tuple(
        TradeProposalReviewDossierBatchGateResult(
            gate_name=row.gate_name,
            status=row.status,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in _normalize_typed_tuple(
            "gate_results",
            report.gate_results,
            TradeProposalReviewDossierBatchGateResult,
        )
    )
    config_version_summaries = tuple(
        TradeProposalReviewDossierBatchConfigVersionSummary(
            dossier_config_version=row.dossier_config_version,
            dossier_count=row.dossier_count,
        )
        for row in _normalize_typed_tuple(
            "config_version_summaries",
            report.config_version_summaries,
            TradeProposalReviewDossierBatchConfigVersionSummary,
        )
    )
    duplicate_summaries = tuple(
        TradeProposalReviewDossierBatchDuplicateSummary(
            dossier_fingerprint=row.dossier_fingerprint,
            dossier_count=row.dossier_count,
        )
        for row in _normalize_typed_tuple(
            "duplicate_summaries",
            report.duplicate_summaries,
            TradeProposalReviewDossierBatchDuplicateSummary,
        )
    )
    finding_summaries = tuple(
        TradeProposalReviewDossierBatchFindingSummary(
            finding_code=row.finding_code,
            severity=row.severity,
            source_report_name=row.source_report_name,
            dossier_count=row.dossier_count,
        )
        for row in _normalize_typed_tuple(
            "finding_summaries",
            report.finding_summaries,
            TradeProposalReviewDossierBatchFindingSummary,
        )
    )
    source_summaries = tuple(
        TradeProposalReviewDossierBatchSourceSummary(
            source_report_name=row.source_report_name,
            complete_count=row.complete_count,
            incomplete_count=row.incomplete_count,
            inconsistent_count=row.inconsistent_count,
            unstable_count=row.unstable_count,
        )
        for row in _normalize_typed_tuple(
            "source_summaries",
            report.source_summaries,
            TradeProposalReviewDossierBatchSourceSummary,
        )
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


def _validate_report_tree(
    report: TradeProposalEvidenceComparisonReport,
) -> TradeProposalEvidenceComparisonReport:
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
        TradeProposalEvidenceComparisonSourceRow(
            source_name=row.source_name,
            source_status=row.source_status,
            generated_at=row.generated_at,
            sample_count=row.sample_count,
            status_category=row.status_category,
        )
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
        TradeProposalEvidenceComparisonFindingRow(
            finding_code=row.finding_code,
            severity=row.severity,
            source_name=row.source_name,
            message=row.message,
            observed_value=row.observed_value,
            threshold=row.threshold,
        )
        for row in _normalize_typed_tuple(
            "finding_rows",
            report.finding_rows,
            TradeProposalEvidenceComparisonFindingRow,
        )
    )
    return TradeProposalEvidenceComparisonReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_only=report.report_only,
        boundary_statement=report.boundary_statement,
        forecast_evidence_generated_at=report.forecast_evidence_generated_at,
        dossier_batch_generated_at=report.dossier_batch_generated_at,
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


def _validate_report_rows(report: TradeProposalEvidenceComparisonReport) -> None:
    if tuple(row.gate_name for row in report.gate_results) != GATE_NAMES:
        raise ValueError("gate_results must contain evidence comparison gates")
    if tuple(row.source_name for row in report.source_rows) != SOURCE_NAMES:
        raise ValueError("source_rows must contain dossier and forecast sources")
    metric_keys = tuple((row.source_name, row.metric_name) for row in report.metric_rows)
    if metric_keys != tuple(sorted(metric_keys)):
        raise ValueError("metric_rows must be sorted")
    if metric_keys != METRIC_KEYS:
        raise ValueError("metric_rows must contain evidence comparison metrics")
    if len(set(metric_keys)) != len(metric_keys):
        raise ValueError("metric_rows must not contain duplicates")
    finding_keys = tuple(
        (row.severity, row.source_name, row.finding_code)
        for row in report.finding_rows
    )
    if finding_keys != tuple(sorted(finding_keys)):
        raise ValueError("finding_rows must be sorted")
    if len(set(finding_keys)) != len(finding_keys):
        raise ValueError("finding_rows must not contain duplicates")


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
    expected = _normalize_boundary_text(
        DEFAULT_PROPOSAL_EVIDENCE_COMPARISON_BOUNDARY_STATEMENT,
    )
    if normalized != expected:
        raise ValueError(
            "boundary_statement must describe report-only proposal evidence comparison",
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


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is not None:
        _require_nonnegative_decimal(field_name, value)


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
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if isinstance(value, Decimal):
        _require_decimal(field_name, value)
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


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        _require_decimal("JSON Decimal value", value)
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

