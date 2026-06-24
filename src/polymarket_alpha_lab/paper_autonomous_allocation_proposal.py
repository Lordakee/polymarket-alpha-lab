"""Pure paper-only autonomous allocation proposal reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority import (
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk import (
    PaperActionGatedStrategyRecommendationQueueRiskReport,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    PaperAutonomousScreeningDecisionSupportGateReport,
)
from polymarket_alpha_lab.paper_recommendation_allocation import (
    PaperRecommendationAllocationConfig,
    PaperRecommendationAllocationInput,
    PaperRecommendationAllocationReport,
    build_paper_recommendation_allocation_report,
)


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION",
    "PaperAutonomousAllocationProposalConfig",
    "PaperAutonomousAllocationProposalReasonCodeCount",
    "PaperAutonomousAllocationProposalSourceQueueSummary",
    "PaperAutonomousAllocationProposalReport",
    "build_paper_autonomous_allocation_proposal_report",
)


DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION = (
    "paper-autonomous-allocation-proposal-v0"
)
ZERO = Decimal("0.000000")
FALLBACK_PRICE = Decimal("1.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
PROPOSAL_STATUSES = ("pass", "watch", "blocked")
SOURCE_ACTION_STATUSES = ("research_ready", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "review_paper_autonomous_allocation_proposal",
    "watch": "hold_paper_autonomous_allocation_proposal",
    "blocked": "block_paper_autonomous_allocation_proposal",
}
PASS_REASON_CODE = "paper_autonomous_allocation_proposal_passed"
BLOCKED_REASON_CODES = frozenset(
    (
        "screening_gate_blocked",
        "queue_risk_blocked",
        "empty_source_queue_reports",
        "empty_allocation_inputs",
        "no_allocated_or_capped_rows",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "screening_gate_watch",
        "queue_risk_watch",
        "allocation_capped",
        "allocation_no_budget",
        "allocation_skipped",
        "allocation_non_recommend",
    ),
)
ALLOWED_REASON_CODES = BLOCKED_REASON_CODES | WATCH_REASON_CODES | {PASS_REASON_CODE}


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalConfig:
    config_version: str
    allocation_config: PaperRecommendationAllocationConfig
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if type(self.allocation_config) is not PaperRecommendationAllocationConfig:
            raise ValueError(
                "allocation_config must be a PaperRecommendationAllocationConfig",
            )
        _require_hard_flags("allocation_config", self.allocation_config)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalSourceQueueSummary:
    source_generated_at: datetime
    config_version: str
    source_config_version: str
    action_status: str
    queue_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    total_ready_notional: Decimal
    allocation_input_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc("source_generated_at", self.source_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_source_action_status("action_status", self.action_status)
        for field_name in (
            "queue_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "allocation_input_count",
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
        _validate_source_summary(self)
        _require_hard_flags("source queue summary", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalReport:
    generated_at: datetime
    config_version: str
    proposal_status: str
    recommended_next_step: str
    reason_code_counts: tuple[PaperAutonomousAllocationProposalReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    screening_gate_config_version: str
    screening_gate_generated_at: datetime
    screening_gate_status: str
    screening_gate_recommended_next_step: str
    queue_priority_generated_at: datetime
    queue_risk_generated_at: datetime
    queue_risk_config_version: str
    queue_risk_status: str
    queue_risk_recommended_next_step: str
    source_queue_count: int
    source_queue_summaries: tuple[
        PaperAutonomousAllocationProposalSourceQueueSummary,
        ...,
    ]
    allocation_config_version: str
    allocation_input_count: int
    allocation_report: PaperRecommendationAllocationReport
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "screening_gate_generated_at",
            _as_utc("screening_gate_generated_at", self.screening_gate_generated_at),
        )
        object.__setattr__(
            self,
            "queue_priority_generated_at",
            _as_utc("queue_priority_generated_at", self.queue_priority_generated_at),
        )
        object.__setattr__(
            self,
            "queue_risk_generated_at",
            _as_utc("queue_risk_generated_at", self.queue_risk_generated_at),
        )
        for field_name in (
            "config_version",
            "recommended_next_step",
            "screening_gate_config_version",
            "screening_gate_recommended_next_step",
            "queue_risk_config_version",
            "queue_risk_recommended_next_step",
            "allocation_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_proposal_status("proposal_status", self.proposal_status)
        _require_proposal_status("screening_gate_status", self.screening_gate_status)
        _require_proposal_status("queue_risk_status", self.queue_risk_status)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_nonnegative_int("source_queue_count", self.source_queue_count)
        _require_nonnegative_int("allocation_input_count", self.allocation_input_count)
        object.__setattr__(
            self,
            "source_queue_summaries",
            _normalize_source_summaries(self.source_queue_summaries),
        )
        if type(self.allocation_report) is not PaperRecommendationAllocationReport:
            raise ValueError(
                "allocation_report must be a PaperRecommendationAllocationReport",
            )
        _require_hard_flags("allocation_report", self.allocation_report)
        _validate_allocation_rows_hard_flags(self.allocation_report)
        _validate_report_consistency(self)
        _require_hard_flags("proposal report", self)


def build_paper_autonomous_allocation_proposal_report(
    *,
    screening_gate_report: PaperAutonomousScreeningDecisionSupportGateReport,
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
    source_queue_reports: Iterable[PaperActionGatedStrategyRecommendationQueueReport],
    config: PaperAutonomousAllocationProposalConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalReport:
    if type(screening_gate_report) is not PaperAutonomousScreeningDecisionSupportGateReport:
        raise ValueError(
            "screening_gate_report must be a "
            "PaperAutonomousScreeningDecisionSupportGateReport",
        )
    if type(priority_report) is not PaperActionGatedStrategyRecommendationQueuePriorityReport:
        raise ValueError(
            "priority_report must be a "
            "PaperActionGatedStrategyRecommendationQueuePriorityReport",
        )
    if type(risk_report) is not PaperActionGatedStrategyRecommendationQueueRiskReport:
        raise ValueError(
            "risk_report must be a PaperActionGatedStrategyRecommendationQueueRiskReport",
        )
    if type(config) is not PaperAutonomousAllocationProposalConfig:
        raise ValueError(
            "config must be a PaperAutonomousAllocationProposalConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _validate_input_hard_flags(
        screening_gate_report=screening_gate_report,
        priority_report=priority_report,
        risk_report=risk_report,
        config=config,
    )
    reports = _normalize_source_queue_reports(source_queue_reports)
    _validate_priority_risk_gate_consistency(
        screening_gate_report=screening_gate_report,
        priority_report=priority_report,
        risk_report=risk_report,
    )
    _validate_source_queue_reports_consistency(
        priority_report=priority_report,
        risk_report=risk_report,
        source_queue_reports=reports,
    )

    source_queue_summaries, allocation_inputs = _proposal_sources(reports)
    allocation_report = build_paper_recommendation_allocation_report(
        allocation_inputs,
        config=config.allocation_config,
        generated_at=generated_at_utc,
    )
    reason_codes = _proposal_reason_codes(
        screening_gate_status=screening_gate_report.gate_status,
        queue_risk_status=risk_report.status,
        source_queue_count=len(reports),
        allocation_input_count=len(allocation_inputs),
        allocation_report=allocation_report,
    )
    proposal_status = _proposal_status(reason_codes)

    return PaperAutonomousAllocationProposalReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        proposal_status=proposal_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[proposal_status],
        reason_code_counts=_reason_code_counts(reason_codes),
        reason_codes=reason_codes,
        screening_gate_config_version=screening_gate_report.config_version,
        screening_gate_generated_at=screening_gate_report.generated_at,
        screening_gate_status=screening_gate_report.gate_status,
        screening_gate_recommended_next_step=screening_gate_report.recommended_next_step,
        queue_priority_generated_at=priority_report.generated_at,
        queue_risk_generated_at=risk_report.generated_at,
        queue_risk_config_version=risk_report.config_version,
        queue_risk_status=risk_report.status,
        queue_risk_recommended_next_step=risk_report.recommended_next_step,
        source_queue_count=len(reports),
        source_queue_summaries=source_queue_summaries,
        allocation_config_version=allocation_report.config_version,
        allocation_input_count=len(allocation_inputs),
        allocation_report=allocation_report,
    )


def _validate_input_hard_flags(
    *,
    screening_gate_report: PaperAutonomousScreeningDecisionSupportGateReport,
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
    config: PaperAutonomousAllocationProposalConfig,
) -> None:
    _require_hard_flags("screening_gate_report", screening_gate_report)
    _require_hard_flags("priority_report", priority_report)
    for row in priority_report.priority_rows:
        _require_hard_flags("priority_report row", row)
    _require_hard_flags("risk_report", risk_report)
    _require_hard_flags("config", config)
    _require_hard_flags("allocation_config", config.allocation_config)


def _normalize_source_queue_reports(
    value: Iterable[PaperActionGatedStrategyRecommendationQueueReport],
) -> tuple[PaperActionGatedStrategyRecommendationQueueReport, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("source_queue_reports must be an iterable")
    try:
        reports = tuple(value)
    except TypeError as exc:
        raise ValueError("source_queue_reports must be an iterable") from exc
    for report in reports:
        if type(report) is not PaperActionGatedStrategyRecommendationQueueReport:
            raise ValueError(
                "source_queue_reports must contain "
                "PaperActionGatedStrategyRecommendationQueueReport values",
            )
        _require_hard_flags("source_queue_reports", report)
        _validate_source_queue_nested_hard_flags(report)
    return reports


def _validate_source_queue_nested_hard_flags(
    report: PaperActionGatedStrategyRecommendationQueueReport,
) -> None:
    for field_name in (
        "candidate_assessment_report",
        "bundle_report",
        "queue_summary_report",
    ):
        nested = getattr(report, field_name)
        if nested is not None:
            _require_hard_flags(field_name, nested)
    queue_summary_report = report.queue_summary_report
    if queue_summary_report is None:
        return
    for queue_row in queue_summary_report.queue_rows:
        _require_hard_flags("queue row", queue_row)


def _validate_priority_risk_gate_consistency(
    *,
    screening_gate_report: PaperAutonomousScreeningDecisionSupportGateReport,
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
) -> None:
    message = (
        "screening_gate_report, priority_report, and risk_report must describe "
        "the same source snapshot"
    )
    if screening_gate_report.queue_priority_generated_at != priority_report.generated_at:
        raise ValueError(message)
    if screening_gate_report.queue_risk_generated_at != risk_report.generated_at:
        raise ValueError(message)
    if screening_gate_report.queue_risk_config_version != risk_report.config_version:
        raise ValueError(message)
    if screening_gate_report.queue_risk_status != risk_report.status:
        raise ValueError(message)
    if screening_gate_report.queue_risk_recommended_next_step != risk_report.recommended_next_step:
        raise ValueError(message)
    if priority_report.generated_at != risk_report.generated_at:
        raise ValueError(message)
    if priority_report.source_report_count != risk_report.source_queue_count:
        raise ValueError(message)
    if priority_report.research_ready_count != risk_report.research_ready_source_count:
        raise ValueError(message)
    if priority_report.watch_count != risk_report.watch_source_count:
        raise ValueError(message)
    if priority_report.blocked_count != risk_report.blocked_source_count:
        raise ValueError(message)
    if priority_report.total_ready_notional != risk_report.total_ready_notional:
        raise ValueError(message)
    if _largest_priority_ready_notional(priority_report) != risk_report.largest_queue_ready_notional:
        raise ValueError(message)
    if _priority_source_config_versions(priority_report) != tuple(
        sorted(risk_report.source_config_versions),
    ):
        raise ValueError(message)
    if screening_gate_report.queue_source_report_count != priority_report.source_report_count:
        raise ValueError(message)
    if screening_gate_report.queue_research_ready_count != priority_report.research_ready_count:
        raise ValueError(message)
    if screening_gate_report.queue_watch_count != priority_report.watch_count:
        raise ValueError(message)
    if screening_gate_report.queue_blocked_count != priority_report.blocked_count:
        raise ValueError(message)
    if screening_gate_report.queue_candidate_count != risk_report.candidate_count:
        raise ValueError(message)
    if screening_gate_report.queue_ready_count != risk_report.ready_count:
        raise ValueError(message)
    if screening_gate_report.queue_candidate_watch_count != risk_report.watch_count:
        raise ValueError(message)
    if screening_gate_report.queue_candidate_blocked_count != risk_report.blocked_count:
        raise ValueError(message)
    if screening_gate_report.queue_total_ready_notional != risk_report.total_ready_notional:
        raise ValueError(message)
    if screening_gate_report.queue_largest_ready_notional != risk_report.largest_queue_ready_notional:
        raise ValueError(message)
    if (
        screening_gate_report.queue_top_research_priority_score
        != priority_report.top_research_priority_score
    ):
        raise ValueError(message)
    if (
        screening_gate_report.queue_average_research_priority_score
        != priority_report.average_research_priority_score
    ):
        raise ValueError(message)
    for field_name in ("candidate_count", "ready_count", "watch_count", "blocked_count"):
        if _sum_priority_rows(field_name, priority_report) != getattr(risk_report, field_name):
            raise ValueError(message)


def _validate_source_queue_reports_consistency(
    *,
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
    source_queue_reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> None:
    message = "source_queue_reports must match priority_report and risk_report"
    if len(source_queue_reports) != priority_report.source_report_count:
        raise ValueError(message)
    if len(source_queue_reports) != risk_report.source_queue_count:
        raise ValueError(message)
    if _source_priority_keys(source_queue_reports) != _priority_report_keys(priority_report):
        raise ValueError(message)

    source_status_counts = Counter(report.action_status for report in source_queue_reports)
    if source_status_counts["research_ready"] != risk_report.research_ready_source_count:
        raise ValueError(message)
    if source_status_counts["watch"] != risk_report.watch_source_count:
        raise ValueError(message)
    if source_status_counts["blocked"] != risk_report.blocked_source_count:
        raise ValueError(message)
    if _source_config_versions(source_queue_reports) != tuple(
        sorted(risk_report.source_config_versions),
    ):
        raise ValueError(message)
    if _source_candidate_count(source_queue_reports) != risk_report.candidate_count:
        raise ValueError(message)
    if _source_ready_count(source_queue_reports) != risk_report.ready_count:
        raise ValueError(message)
    if _source_watch_count(source_queue_reports) != risk_report.watch_count:
        raise ValueError(message)
    if _source_blocked_count(source_queue_reports) != risk_report.blocked_count:
        raise ValueError(message)
    if _source_total_ready_notional(source_queue_reports) != risk_report.total_ready_notional:
        raise ValueError(message)
    if _source_largest_ready_notional(source_queue_reports) != risk_report.largest_queue_ready_notional:
        raise ValueError(message)


def _proposal_sources(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> tuple[
    tuple[PaperAutonomousAllocationProposalSourceQueueSummary, ...],
    tuple[PaperRecommendationAllocationInput, ...],
]:
    summaries: list[PaperAutonomousAllocationProposalSourceQueueSummary] = []
    allocation_inputs: list[PaperRecommendationAllocationInput] = []
    for report in reports:
        source_inputs = _allocation_inputs_from_source_queue_report(report)
        summaries.append(_source_queue_summary(report, len(source_inputs)))
        allocation_inputs.extend(source_inputs)
    return tuple(summaries), tuple(allocation_inputs)


def _source_queue_summary(
    report: PaperActionGatedStrategyRecommendationQueueReport,
    allocation_input_count: int,
) -> PaperAutonomousAllocationProposalSourceQueueSummary:
    return PaperAutonomousAllocationProposalSourceQueueSummary(
        source_generated_at=report.generated_at,
        config_version=report.config_version,
        source_config_version=report.source_config_version,
        action_status=report.action_status,
        queue_count=report.candidate_count,
        ready_count=report.ready_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        total_ready_notional=report.total_ready_notional,
        allocation_input_count=allocation_input_count,
    )


def _allocation_inputs_from_source_queue_report(
    report: PaperActionGatedStrategyRecommendationQueueReport,
) -> tuple[PaperRecommendationAllocationInput, ...]:
    queue_summary_report = report.queue_summary_report
    if report.action_status != "research_ready" or queue_summary_report is None:
        return ()

    inputs: list[PaperRecommendationAllocationInput] = []
    for queue_row in queue_summary_report.queue_rows:
        if queue_row.queue_status != "ready":
            continue
        price, shares = _notional_preserving_price_and_shares(queue_row)
        inputs.append(
            PaperRecommendationAllocationInput(
                market_slug=queue_row.market_slug,
                side=queue_row.selected_side,
                action=queue_row.action,
                recommendation_score=queue_row.recommendation_score,
                net_probability_edge=None,
                executable_paper_shares=shares,
                side_price=price,
                reason_codes=(queue_row.primary_reason_code,),
            ),
        )
    return tuple(inputs)


def _notional_preserving_price_and_shares(queue_row: object) -> tuple[Decimal, Decimal]:
    return FALLBACK_PRICE, _quantize_nonnegative_decimal(
        "suggested_notional",
        queue_row.suggested_notional,
    )


def _proposal_reason_codes(
    *,
    screening_gate_status: str,
    queue_risk_status: str,
    source_queue_count: int,
    allocation_input_count: int,
    allocation_report: PaperRecommendationAllocationReport,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if screening_gate_status != "pass":
        reason_codes.append(f"screening_gate_{screening_gate_status}")
    if queue_risk_status != "pass":
        reason_codes.append(f"queue_risk_{queue_risk_status}")
    if source_queue_count == 0:
        reason_codes.append("empty_source_queue_reports")
    if allocation_input_count == 0:
        reason_codes.append("empty_allocation_inputs")
    if (
        allocation_report.allocated_count + allocation_report.capped_count == 0
        and allocation_report.non_recommend_count == 0
    ):
        reason_codes.append("no_allocated_or_capped_rows")
    if allocation_report.capped_count > 0:
        reason_codes.append("allocation_capped")
    if allocation_report.no_budget_count > 0:
        reason_codes.append("allocation_no_budget")
    if allocation_report.skipped_count > 0:
        reason_codes.append("allocation_skipped")
    if allocation_report.non_recommend_count > 0:
        reason_codes.append("allocation_non_recommend")
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(sorted(set(reason_codes)))


def _proposal_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[PaperAutonomousAllocationProposalReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for reason_code in reason_codes:
        counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperAutonomousAllocationProposalReasonCodeCount(
            reason_code=reason_code,
            report_count=report_count,
        )
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _validate_report_consistency(
    report: PaperAutonomousAllocationProposalReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.proposal_status]:
        raise ValueError("recommended_next_step must match proposal_status")
    if tuple(row.reason_code for row in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.proposal_status != _proposal_status(report.reason_codes):
        raise ValueError("proposal_status must match reason_codes")
    if PASS_REASON_CODE in report.reason_codes and len(report.reason_codes) != 1:
        raise ValueError("pass reason must not be mixed with watch or blocked reasons")
    expected_reason_codes = _proposal_reason_codes(
        screening_gate_status=report.screening_gate_status,
        queue_risk_status=report.queue_risk_status,
        source_queue_count=report.source_queue_count,
        allocation_input_count=report.allocation_input_count,
        allocation_report=report.allocation_report,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match proposal inputs")
    if report.source_queue_count != len(report.source_queue_summaries):
        raise ValueError("source_queue_count must match source_queue_summaries")
    if report.allocation_input_count != sum(
        summary.allocation_input_count for summary in report.source_queue_summaries
    ):
        raise ValueError("allocation_input_count must match source_queue_summaries")
    if report.allocation_input_count != report.allocation_report.input_count:
        raise ValueError("allocation_input_count must match allocation_report")
    if report.allocation_config_version != report.allocation_report.config_version:
        raise ValueError("allocation_config_version must match allocation_report")
    if report.generated_at != report.allocation_report.generated_at:
        raise ValueError("generated_at must match allocation_report")


def _validate_source_summary(
    summary: PaperAutonomousAllocationProposalSourceQueueSummary,
) -> None:
    if summary.queue_count != (
        summary.ready_count + summary.watch_count + summary.blocked_count
    ):
        raise ValueError("queue_count must match source status counts")
    if summary.allocation_input_count > summary.ready_count:
        raise ValueError("allocation_input_count must not exceed ready_count")


def _validate_allocation_rows_hard_flags(
    allocation_report: PaperRecommendationAllocationReport,
) -> None:
    for row in allocation_report.rows:
        _require_hard_flags("allocation row", row)


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperAutonomousAllocationProposalReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_code_counts is required")
    previous_key: tuple[int, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not PaperAutonomousAllocationProposalReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason rows")
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.report_count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} is required")
    previous: str | None = None
    seen: set[str] = set()
    for code in codes:
        _require_canonical_string(field_name, code)
        if code not in ALLOWED_REASON_CODES:
            raise ValueError(f"{field_name} must match proposal semantics")
        if code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > code:
            raise ValueError(f"{field_name} must be sorted")
        previous = code
        seen.add(code)
    return codes


def _normalize_source_summaries(
    value: object,
) -> tuple[PaperAutonomousAllocationProposalSourceQueueSummary, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("source_queue_summaries must be an iterable")
    try:
        summaries = tuple(value)
    except TypeError as exc:
        raise ValueError("source_queue_summaries must be an iterable") from exc
    for summary in summaries:
        if type(summary) is not PaperAutonomousAllocationProposalSourceQueueSummary:
            raise ValueError(
                "source_queue_summaries must contain exact source summary rows",
            )
    return summaries


def _source_priority_keys(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        sorted(
            (
                report.config_version,
                report.generated_at,
                report.source_config_version,
                report.action_status,
                report.recommended_next_step,
                report.candidate_count,
                report.ready_count,
                report.watch_count,
                report.blocked_count,
                report.total_ready_notional,
                _source_top_queue_score(report),
                _source_average_ready_score(report),
            )
            for report in reports
        )
    )


def _priority_report_keys(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        sorted(
            (
                row.config_version,
                row.source_generated_at,
                row.source_config_version,
                row.action_status,
                row.recommended_next_step,
                row.candidate_count,
                row.ready_count,
                row.watch_count,
                row.blocked_count,
                row.total_ready_notional,
                row.top_queue_score,
                row.average_ready_score,
            )
            for row in priority_report.priority_rows
        )
    )


def _priority_source_config_versions(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> tuple[str, ...]:
    return tuple(sorted({row.config_version for row in priority_report.priority_rows}))


def _source_config_versions(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> tuple[str, ...]:
    return tuple(sorted({report.config_version for report in reports}))


def _source_top_queue_score(report: PaperActionGatedStrategyRecommendationQueueReport) -> Decimal:
    if report.queue_summary_report is None:
        return ZERO
    return report.queue_summary_report.top_score


def _source_average_ready_score(
    report: PaperActionGatedStrategyRecommendationQueueReport,
) -> Decimal:
    if report.queue_summary_report is None:
        return ZERO
    return report.queue_summary_report.average_ready_score


def _largest_priority_ready_notional(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> Decimal:
    return _quantize_nonnegative_decimal(
        "largest_queue_ready_notional",
        max(
            (row.total_ready_notional for row in priority_report.priority_rows),
            default=ZERO,
        ),
    )


def _source_largest_ready_notional(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> Decimal:
    return _quantize_nonnegative_decimal(
        "largest_queue_ready_notional",
        max((report.total_ready_notional for report in reports), default=ZERO),
    )


def _sum_priority_rows(
    field_name: str,
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> int:
    return sum(getattr(row, field_name) for row in priority_report.priority_rows)


def _source_candidate_count(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> int:
    return sum(report.candidate_count for report in reports)


def _source_ready_count(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> int:
    return sum(report.ready_count for report in reports)


def _source_watch_count(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> int:
    return sum(report.watch_count for report in reports)


def _source_blocked_count(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> int:
    return sum(report.blocked_count for report in reports)


def _source_total_ready_notional(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> Decimal:
    return _quantize_nonnegative_decimal(
        "total_ready_notional",
        sum((report.total_ready_notional for report in reports), ZERO),
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
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


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_proposal_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PROPOSAL_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_source_action_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_ACTION_STATUSES:
        raise ValueError(f"{field_name} must be research_ready, watch, or blocked")


def _quantize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(DECIMAL_QUANTUM)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")
