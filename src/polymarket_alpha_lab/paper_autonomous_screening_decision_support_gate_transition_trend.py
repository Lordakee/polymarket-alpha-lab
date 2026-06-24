"""Pure trend reducer for autonomous screening gate transition reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition import (
    PaperAutonomousScreeningDecisionSupportGateTransitionReport,
)


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_CONFIG_VERSION",
    "PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport",
    "build_paper_autonomous_screening_decision_support_gate_transition_trend_report",
)


DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_CONFIG_VERSION = (
    "paper-autonomous-screening-decision-support-gate-transition-trend-v0"
)
RATIO_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport:
    generated_at: datetime
    config_version: str
    transition_report_count: int
    first_transition_generated_at: datetime | None
    latest_transition_generated_at: datetime | None
    latest_from_gate_status: str | None
    latest_to_gate_status: str | None
    latest_introduced_reason_code_count: int
    latest_cleared_reason_code_count: int
    latest_persistent_reason_code_count: int
    latest_transition_count: int
    latest_instability_ratio: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(self, "first_transition_generated_at", _as_optional_utc(self.first_transition_generated_at))
        object.__setattr__(self, "latest_transition_generated_at", _as_optional_utc(self.latest_transition_generated_at))
        if not isinstance(self.config_version, str) or not self.config_version or self.config_version.strip() != self.config_version:
            raise ValueError("config_version must be a canonical nonblank string")
        if self.transition_report_count < 0:
            raise ValueError("transition_report_count must be nonnegative")
        if self.latest_introduced_reason_code_count < 0 or self.latest_cleared_reason_code_count < 0 or self.latest_persistent_reason_code_count < 0:
            raise ValueError("reason code counts must be nonnegative")
        if self.latest_transition_count < 0:
            raise ValueError("latest_transition_count must be nonnegative")
        if self.latest_instability_ratio is not None:
            if not isinstance(self.latest_instability_ratio, Decimal):
                raise ValueError("latest_instability_ratio must be a Decimal")
            if self.latest_instability_ratio.quantize(RATIO_QUANTUM) != self.latest_instability_ratio:
                raise ValueError("latest_instability_ratio must be quantized to 0.000001")
            if self.latest_instability_ratio < 0 or self.latest_instability_ratio > 1:
                raise ValueError("latest_instability_ratio must be between 0 and 1")
        if self.paper_only is not True or self.report_only is not True or self.readonly is not True:
            raise ValueError("report must remain paper-only/report-only/readonly")


def build_paper_autonomous_screening_decision_support_gate_transition_trend_report(
    transition_reports: list[PaperAutonomousScreeningDecisionSupportGateTransitionReport]
    | tuple[PaperAutonomousScreeningDecisionSupportGateTransitionReport, ...],
    *,
    config_version: str = DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_TREND_CONFIG_VERSION,
    generated_at: datetime,
) -> PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport:
    if not isinstance(config_version, str) or not config_version or config_version.strip() != config_version:
        raise ValueError("config_version must be a canonical nonblank string")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    normalized_reports = _normalize_reports(transition_reports)
    latest = normalized_reports[-1] if normalized_reports else None
    introduced = 0 if latest is None else len(latest.latest_introduced_reason_codes)
    cleared = 0 if latest is None else len(latest.latest_cleared_reason_codes)
    persistent = 0 if latest is None else len(latest.latest_persistent_reason_codes)
    latest_transition_count = 0 if latest is None else latest.transition_count
    total_reason_changes = introduced + cleared
    latest_instability_ratio = _ratio(total_reason_changes, total_reason_changes + persistent)
    return PaperAutonomousScreeningDecisionSupportGateTransitionTrendReport(
        generated_at=generated_at,
        config_version=config_version,
        transition_report_count=len(normalized_reports),
        first_transition_generated_at=normalized_reports[0].generated_at if normalized_reports else None,
        latest_transition_generated_at=normalized_reports[-1].generated_at if normalized_reports else None,
        latest_from_gate_status=None if latest is None else latest.latest_from_gate_status,
        latest_to_gate_status=None if latest is None else latest.latest_to_gate_status,
        latest_introduced_reason_code_count=introduced,
        latest_cleared_reason_code_count=cleared,
        latest_persistent_reason_code_count=persistent,
        latest_transition_count=latest_transition_count,
        latest_instability_ratio=latest_instability_ratio,
    )


def _normalize_reports(
    transition_reports: list[PaperAutonomousScreeningDecisionSupportGateTransitionReport]
    | tuple[PaperAutonomousScreeningDecisionSupportGateTransitionReport, ...],
) -> tuple[PaperAutonomousScreeningDecisionSupportGateTransitionReport, ...]:
    if type(transition_reports) not in (list, tuple):
        raise ValueError("transition_reports must be a list or tuple")
    normalized = tuple(transition_reports)
    for report in normalized:
        if type(report) is not PaperAutonomousScreeningDecisionSupportGateTransitionReport:
            raise ValueError("transition_reports must contain exact PaperAutonomousScreeningDecisionSupportGateTransitionReport values")
        if report.paper_only is not True or report.report_only is not True or report.readonly is not True:
            raise ValueError("transition_reports must contain paper-only/report-only/readonly reports")
    return normalized


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator <= 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(value)
