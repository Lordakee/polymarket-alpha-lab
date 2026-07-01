"""Pure bundled diagnostics reducer for materialized team forecast rows."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import UTC, datetime
from typing import Any

from polymarket_alpha_lab.team_event_template_performance import (
    TeamEventTemplatePerformanceConfig,
    TeamEventTemplatePerformanceReport,
    build_team_event_template_performance_report,
)
from polymarket_alpha_lab.team_evidence_quality import (
    TeamEvidenceQualityConfig,
    TeamEvidenceQualityReport,
    build_team_evidence_quality_report,
)
from polymarket_alpha_lab.team_forecast_calibration import (
    TeamForecastCalibrationConfig,
    TeamForecastCalibrationReport,
    build_team_forecast_calibration_report,
)
from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastEvidenceDbRow,
    TeamForecastOutcomeDbRow,
)
from polymarket_alpha_lab.team_memory_synthesis import (
    TeamMemorySynthesisConfig,
    TeamMemorySynthesisReport,
    build_team_memory_synthesis_report,
)
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_source_reliability import (
    TeamSourceReliabilityConfig,
    TeamSourceReliabilityReport,
    build_team_source_reliability_report,
)


@dataclass(frozen=True)
class TeamDiagnosticsBundleConfig:
    config_version: str = "team-diagnostics-bundle-v0"
    memory_synthesis_config: TeamMemorySynthesisConfig = field(
        default_factory=TeamMemorySynthesisConfig,
    )
    forecast_calibration_config: TeamForecastCalibrationConfig = field(
        default_factory=TeamForecastCalibrationConfig,
    )
    event_template_performance_config: TeamEventTemplatePerformanceConfig = field(
        default_factory=TeamEventTemplatePerformanceConfig,
    )
    source_reliability_config: TeamSourceReliabilityConfig = field(
        default_factory=TeamSourceReliabilityConfig,
    )
    evidence_quality_config: TeamEvidenceQualityConfig = field(
        default_factory=TeamEvidenceQualityConfig,
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_exact_config(
            "memory_synthesis_config",
            self.memory_synthesis_config,
            TeamMemorySynthesisConfig,
        )
        _require_exact_config(
            "forecast_calibration_config",
            self.forecast_calibration_config,
            TeamForecastCalibrationConfig,
        )
        _require_exact_config(
            "event_template_performance_config",
            self.event_template_performance_config,
            TeamEventTemplatePerformanceConfig,
        )
        _require_exact_config(
            "source_reliability_config",
            self.source_reliability_config,
            TeamSourceReliabilityConfig,
        )
        _require_exact_config(
            "evidence_quality_config",
            self.evidence_quality_config,
            TeamEvidenceQualityConfig,
        )
        require_paper_only_flags("team diagnostics bundle config", self)


@dataclass(frozen=True)
class TeamDiagnosticsBundleReport:
    generated_at: datetime
    config_version: str
    forecast_row_count: int
    evidence_row_count: int
    outcome_row_count: int
    memory_synthesis_report: TeamMemorySynthesisReport
    forecast_calibration_report: TeamForecastCalibrationReport
    event_template_performance_report: TeamEventTemplatePerformanceReport
    source_reliability_report: TeamSourceReliabilityReport
    evidence_quality_report: TeamEvidenceQualityReport
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "forecast_row_count",
            "evidence_row_count",
            "outcome_row_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_exact_report(
            "memory_synthesis_report",
            self.memory_synthesis_report,
            TeamMemorySynthesisReport,
        )
        _require_exact_report(
            "forecast_calibration_report",
            self.forecast_calibration_report,
            TeamForecastCalibrationReport,
        )
        _require_exact_report(
            "event_template_performance_report",
            self.event_template_performance_report,
            TeamEventTemplatePerformanceReport,
        )
        _require_exact_report(
            "source_reliability_report",
            self.source_reliability_report,
            TeamSourceReliabilityReport,
        )
        _require_exact_report(
            "evidence_quality_report",
            self.evidence_quality_report,
            TeamEvidenceQualityReport,
        )
        _validate_report_alignment(self)
        require_paper_only_flags("team diagnostics bundle report", self)


def build_team_diagnostics_bundle_report(
    forecast_rows: list[TeamForecastDbRow] | tuple[TeamForecastDbRow, ...],
    evidence_rows: list[TeamForecastEvidenceDbRow] | tuple[TeamForecastEvidenceDbRow, ...],
    outcome_rows: list[TeamForecastOutcomeDbRow] | tuple[TeamForecastOutcomeDbRow, ...],
    *,
    config: TeamDiagnosticsBundleConfig,
    generated_at: datetime,
) -> TeamDiagnosticsBundleReport:
    if type(config) is not TeamDiagnosticsBundleConfig:
        raise ValueError("config must be a TeamDiagnosticsBundleConfig")
    require_paper_only_flags("team diagnostics bundle config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    forecasts = _normalize_rows("forecast_rows", forecast_rows, TeamForecastDbRow)
    evidence = _normalize_rows("evidence_rows", evidence_rows, TeamForecastEvidenceDbRow)
    outcomes = _normalize_rows("outcome_rows", outcome_rows, TeamForecastOutcomeDbRow)

    memory_synthesis_report = build_team_memory_synthesis_report(
        forecasts,
        evidence,
        outcomes,
        config=config.memory_synthesis_config,
        generated_at=generated_at_utc,
    )
    forecast_calibration_report = build_team_forecast_calibration_report(
        forecasts,
        outcomes,
        config=config.forecast_calibration_config,
        generated_at=generated_at_utc,
    )
    event_template_performance_report = build_team_event_template_performance_report(
        forecasts,
        outcomes,
        config=config.event_template_performance_config,
        generated_at=generated_at_utc,
    )
    source_reliability_report = build_team_source_reliability_report(
        evidence,
        outcomes,
        config=config.source_reliability_config,
        generated_at=generated_at_utc,
    )
    evidence_quality_report = build_team_evidence_quality_report(
        evidence,
        config=config.evidence_quality_config,
        generated_at=generated_at_utc,
    )

    return TeamDiagnosticsBundleReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        forecast_row_count=len(forecasts),
        evidence_row_count=len(evidence),
        outcome_row_count=len(outcomes),
        memory_synthesis_report=memory_synthesis_report,
        forecast_calibration_report=forecast_calibration_report,
        event_template_performance_report=event_template_performance_report,
        source_reliability_report=source_reliability_report,
        evidence_quality_report=evidence_quality_report,
    )


def _normalize_rows(field_name: str, value: object, row_type: type[Any]) -> tuple[Any, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    rows = tuple(value)
    normalized: list[Any] = []
    for row in rows:
        if type(row) is not row_type:
            raise ValueError(f"{field_name} must contain {row_type.__name__} values")
        require_paper_only_flags(field_name, row)
        normalized.append(
            row_type(**{field.name: getattr(row, field.name) for field in fields(row_type)}),
        )
    return tuple(normalized)


def _validate_report_alignment(report: TeamDiagnosticsBundleReport) -> None:
    nested_reports = (
        report.memory_synthesis_report,
        report.forecast_calibration_report,
        report.event_template_performance_report,
        report.source_reliability_report,
        report.evidence_quality_report,
    )
    for nested_report in nested_reports:
        if nested_report.generated_at != report.generated_at:
            raise ValueError("nested report generated_at must match bundle report")
        require_paper_only_flags("team diagnostics nested report", nested_report)

    if report.memory_synthesis_report.forecast_row_count != report.forecast_row_count:
        raise ValueError("memory forecast_row_count must match bundle")
    if report.memory_synthesis_report.evidence_row_count != report.evidence_row_count:
        raise ValueError("memory evidence_row_count must match bundle")
    if report.memory_synthesis_report.outcome_row_count != report.outcome_row_count:
        raise ValueError("memory outcome_row_count must match bundle")
    if report.source_reliability_report.evidence_count != report.evidence_row_count:
        raise ValueError("source reliability evidence_count must match bundle")
    if report.source_reliability_report.outcome_count != report.outcome_row_count:
        raise ValueError("source reliability outcome_count must match bundle")
    if report.evidence_quality_report.total_count != report.evidence_row_count:
        raise ValueError("evidence quality total_count must match bundle")


def _require_exact_config(field_name: str, value: object, config_type: type[Any]) -> None:
    if type(value) is not config_type:
        raise ValueError(f"{field_name} must be a {config_type.__name__}")
    require_paper_only_flags(field_name, value)


def _require_exact_report(field_name: str, value: object, report_type: type[Any]) -> None:
    if type(value) is not report_type:
        raise ValueError(f"{field_name} must be a {report_type.__name__}")
    require_paper_only_flags(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=UTC,
            fold=value.fold,
        )
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


__all__ = (
    "TeamDiagnosticsBundleConfig",
    "TeamDiagnosticsBundleReport",
    "build_team_diagnostics_bundle_report",
)
