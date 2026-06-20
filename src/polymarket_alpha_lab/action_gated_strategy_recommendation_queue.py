"""Pure paper-only action-gated strategy recommendation queue reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.candidate_assessment import (
    PaperCandidateAssessmentConfig,
    PaperCandidateAssessmentReport,
    build_paper_candidate_assessment_report,
)
from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
    PaperRecommendationCycleActionGateReport,
)
from polymarket_alpha_lab.project_screening import PaperProjectScreeningReport
from polymarket_alpha_lab.strategy_readiness_state import (
    PaperStrategyReadinessSignal,
    PaperStrategyReadinessStateReport,
    build_paper_strategy_readiness_state_report,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleConfig,
    PaperStrategyRecommendationBundleReport,
    build_paper_strategy_recommendation_bundle_report,
)
from polymarket_alpha_lab.strategy_recommendation_queue import (
    PaperStrategyRecommendationQueueSummaryReport,
    build_paper_strategy_recommendation_queue_summary_report,
)


__all__ = (
    "PaperActionGatedStrategyRecommendationQueueConfig",
    "PaperActionGatedStrategyRecommendationQueueReport",
    "build_paper_action_gated_strategy_recommendation_queue_report",
)


ZERO_NOTIONAL = Decimal("0.000000")
QUANTUM = Decimal("0.000001")
READY_GATE_NEXT_STEP = "build_candidate_research_queue"
READY_QUEUE_NEXT_STEP = "review_candidate_research_queue"
ACTION_STATUSES = ("research_ready", "watch", "blocked")
QUEUE_NEXT_STEPS = (
    READY_QUEUE_NEXT_STEP,
    "await_fresh_cycle_evidence",
    "repair_cycle_evidence",
)
NEXT_STEP_BY_ACTION_STATUS = {
    "research_ready": READY_QUEUE_NEXT_STEP,
    "watch": "await_fresh_cycle_evidence",
    "blocked": "repair_cycle_evidence",
}


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueConfig:
    config_version: str
    candidate_assessment_config: PaperCandidateAssessmentConfig
    readiness_config_version: str
    bundle_config: PaperStrategyRecommendationBundleConfig
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if type(self.candidate_assessment_config) is not PaperCandidateAssessmentConfig:
            raise ValueError(
                "candidate_assessment_config must be a "
                "PaperCandidateAssessmentConfig",
            )
        _require_canonical_string(
            "readiness_config_version",
            self.readiness_config_version,
        )
        if type(self.bundle_config) is not PaperStrategyRecommendationBundleConfig:
            raise ValueError(
                "bundle_config must be a PaperStrategyRecommendationBundleConfig",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    action_status: str
    recommended_next_step: str
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...]
    candidate_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    total_ready_notional: Decimal
    candidate_assessment_report: PaperCandidateAssessmentReport | None = None
    bundle_report: PaperStrategyRecommendationBundleReport | None = None
    queue_summary_report: PaperStrategyRecommendationQueueSummaryReport | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_action_status("action_status", self.action_status)
        _require_queue_next_step("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        for field_name in (
            "candidate_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "total_ready_notional",
            _quantize_nonnegative_decimal(
                "total_ready_notional",
                self.total_ready_notional,
            ),
        )
        _validate_optional_report_type(
            "candidate_assessment_report",
            self.candidate_assessment_report,
            PaperCandidateAssessmentReport,
        )
        _validate_optional_report_type(
            "bundle_report",
            self.bundle_report,
            PaperStrategyRecommendationBundleReport,
        )
        _validate_optional_report_type(
            "queue_summary_report",
            self.queue_summary_report,
            PaperStrategyRecommendationQueueSummaryReport,
        )
        _validate_report_consistency(self)
        _require_hard_flags("queue_report", self)


def build_paper_action_gated_strategy_recommendation_queue_report(
    action_gate_report: object,
    screening_report: object,
    cost_reports: Iterable[object],
    *,
    config: PaperActionGatedStrategyRecommendationQueueConfig,
    generated_at: datetime,
) -> PaperActionGatedStrategyRecommendationQueueReport:
    _validate_action_gate_report(action_gate_report)
    if type(config) is not PaperActionGatedStrategyRecommendationQueueConfig:
        raise ValueError(
            "config must be a PaperActionGatedStrategyRecommendationQueueConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("config", config)

    if action_gate_report.recommended_next_step != READY_GATE_NEXT_STEP:
        return PaperActionGatedStrategyRecommendationQueueReport(
            generated_at=generated_at,
            config_version=config.config_version,
            source_config_version=action_gate_report.config_version,
            action_status=action_gate_report.action_status,
            recommended_next_step=action_gate_report.recommended_next_step,
            reason_code_counts=action_gate_report.reason_code_counts,
            candidate_count=0,
            ready_count=0,
            watch_count=0,
            blocked_count=0,
            total_ready_notional=ZERO_NOTIONAL,
        )

    _validate_screening_report(screening_report)
    assessment_report = build_paper_candidate_assessment_report(
        screening_report,
        cost_reports,
        config=config.candidate_assessment_config,
        generated_at=generated_at,
    )
    readiness_report = _build_readiness_report(
        action_gate_report,
        config_version=config.readiness_config_version,
        generated_at=generated_at,
    )
    bundle_report = build_paper_strategy_recommendation_bundle_report(
        assessment_report,
        readiness_report,
        config=config.bundle_config,
        generated_at=generated_at,
    )
    queue_summary_report = build_paper_strategy_recommendation_queue_summary_report(
        bundle_report,
    )

    return PaperActionGatedStrategyRecommendationQueueReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_config_version=action_gate_report.config_version,
        action_status=action_gate_report.action_status,
        recommended_next_step=READY_QUEUE_NEXT_STEP,
        reason_code_counts=action_gate_report.reason_code_counts,
        candidate_count=queue_summary_report.queue_count,
        ready_count=queue_summary_report.ready_count,
        watch_count=queue_summary_report.watch_count,
        blocked_count=queue_summary_report.blocked_count,
        total_ready_notional=queue_summary_report.total_ready_notional,
        candidate_assessment_report=assessment_report,
        bundle_report=bundle_report,
        queue_summary_report=queue_summary_report,
    )


def _build_readiness_report(
    action_gate_report: PaperRecommendationCycleActionGateReport,
    *,
    config_version: str,
    generated_at: datetime,
) -> PaperStrategyReadinessStateReport:
    readiness_item = PaperStrategyReadinessSignal(
        source_name="cycle_action_gate",
        status="pass",
        reason_codes=("action_gate_research_ready",),
        severity=10,
        observed_value=action_gate_report.action_status,
        threshold="research_ready",
    )
    return build_paper_strategy_readiness_state_report(
        (readiness_item,),
        config_version=config_version,
        generated_at=generated_at,
    )


def _validate_action_gate_report(report: object) -> None:
    if type(report) is not PaperRecommendationCycleActionGateReport:
        raise ValueError(
            "action_gate_report must be a PaperRecommendationCycleActionGateReport",
        )
    _require_hard_flags("action_gate_report", report)


def _validate_screening_report(report: object) -> None:
    if type(report) is not PaperProjectScreeningReport:
        raise ValueError("screening_report must be a PaperProjectScreeningReport")
    _require_source_flags("screening_report", report)


def _validate_optional_report_type(
    field_name: str,
    report: Any,
    expected_type: type[Any],
) -> None:
    if report is None:
        return
    if type(report) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_hard_flags(field_name, report)


def _validate_report_consistency(
    report: PaperActionGatedStrategyRecommendationQueueReport,
) -> None:
    if (
        report.recommended_next_step
        != NEXT_STEP_BY_ACTION_STATUS[report.action_status]
    ):
        raise ValueError("recommended_next_step must match action_status")

    nested_reports = (
        report.candidate_assessment_report,
        report.bundle_report,
        report.queue_summary_report,
    )
    has_nested_reports = all(item is not None for item in nested_reports)
    has_partial_reports = any(item is not None for item in nested_reports)

    if report.action_status == "research_ready":
        if not has_nested_reports:
            raise ValueError("research_ready reports must include nested reports")
        queue_summary_report = report.queue_summary_report
        if queue_summary_report is None:
            raise ValueError("queue_summary_report is required")
        if report.candidate_count != queue_summary_report.queue_count:
            raise ValueError("candidate_count must match queue_summary_report")
        if report.ready_count != queue_summary_report.ready_count:
            raise ValueError("ready_count must match queue_summary_report")
        if report.watch_count != queue_summary_report.watch_count:
            raise ValueError("watch_count must match queue_summary_report")
        if report.blocked_count != queue_summary_report.blocked_count:
            raise ValueError("blocked_count must match queue_summary_report")
        if report.total_ready_notional != queue_summary_report.total_ready_notional:
            raise ValueError("total_ready_notional must match queue_summary_report")
        return

    if has_partial_reports:
        raise ValueError("watch and blocked reports must not include nested reports")
    if report.candidate_count != 0:
        raise ValueError("candidate_count must be zero without nested reports")
    if report.ready_count != 0:
        raise ValueError("ready_count must be zero without nested reports")
    if report.watch_count != 0:
        raise ValueError("watch_count must be zero without nested reports")
    if report.blocked_count != 0:
        raise ValueError("blocked_count must be zero without nested reports")
    if report.total_ready_notional != ZERO_NOTIONAL:
        raise ValueError("total_ready_notional must be zero without nested reports")


def _normalize_reason_code_counts(
    value: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...],
) -> tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in counts:
        if type(item) is not PaperRecommendationCycleActionGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "PaperRecommendationCycleActionGateReasonCodeCount values",
            )
    return counts


def _require_action_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTION_STATUSES:
        raise ValueError(f"{field_name} must be research_ready, watch, or blocked")


def _require_queue_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUEUE_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a known next step")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _require_source_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")
    if hasattr(value, "readonly") and getattr(value, "readonly") is not True:
        raise ValueError(f"{field_name} must be readonly")


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


def _quantize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(QUANTUM)


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
