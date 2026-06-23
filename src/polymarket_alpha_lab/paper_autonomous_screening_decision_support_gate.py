"""Pure paper-only gate for autonomous screening decision support."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend import (
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority import (
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk import (
    NEXT_STEP_BY_STATUS as QUEUE_RISK_NEXT_STEP_BY_STATUS,
    PaperActionGatedStrategyRecommendationQueueRiskReport,
)
from polymarket_alpha_lab.paper_project_screening_rank_stability import (
    PaperProjectScreeningRankStabilityReport,
)
from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate import (
    NEXT_STEP_BY_STATUS as OPERATOR_FLOW_NEXT_STEP_BY_STATUS,
    PaperResearchPacketOperatorFlowDbHistoryGateReport,
)


DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION = (
    "paper-autonomous-screening-decision-support-gate-v0"
)
GATE_STATUSES = ("pass", "watch", "blocked")
RANK_STABILITY_STATUSES = ("stable", "watch", "blocked")
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO_DECIMAL = Decimal("0.000000")
NEXT_STEP_BY_STATUS = {
    "pass": "advance_paper_autonomous_screening_recommendations",
    "watch": "throttle_paper_autonomous_screening_recommendations",
    "blocked": "block_paper_autonomous_screening_recommendations",
}
PASS_REASON_CODE = "paper_autonomous_screening_decision_support_gate_passed"
BLOCKED_REASON_CODES = frozenset(
    (
        "operator_flow_db_history_gate_blocked",
        "project_screening_rank_stability_blocked",
        "queue_decision_support_trend_consecutive_latest_blocked",
        "queue_decision_support_trend_latest_risk_blocked",
        "queue_risk_blocked",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "operator_flow_db_history_gate_watch",
        "project_screening_rank_stability_watch",
        "queue_decision_support_trend_consecutive_latest_watch",
        "queue_decision_support_trend_duplicate_generated_at",
        "queue_decision_support_trend_latest_risk_watch",
        "queue_risk_watch",
    ),
)
OPERATOR_FLOW_REASON_CODE_BY_STATUS = {
    "watch": "operator_flow_db_history_gate_watch",
    "blocked": "operator_flow_db_history_gate_blocked",
}
QUEUE_RISK_REASON_CODE_BY_STATUS = {
    "watch": "queue_risk_watch",
    "blocked": "queue_risk_blocked",
}
TREND_REASON_CODES = frozenset(
    (
        "queue_decision_support_trend_consecutive_latest_blocked",
        "queue_decision_support_trend_consecutive_latest_watch",
        "queue_decision_support_trend_duplicate_generated_at",
        "queue_decision_support_trend_latest_risk_blocked",
        "queue_decision_support_trend_latest_risk_watch",
    ),
)
RANK_STABILITY_REASON_CODE_BY_STATUS = {
    "watch": "project_screening_rank_stability_watch",
    "blocked": "project_screening_rank_stability_blocked",
}

__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION",
    "PaperAutonomousScreeningDecisionSupportGateReasonCodeCount",
    "PaperAutonomousScreeningDecisionSupportGateReport",
    "build_paper_autonomous_screening_decision_support_gate_report",
)


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateReasonCodeCount:
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
class PaperAutonomousScreeningDecisionSupportGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[
        PaperAutonomousScreeningDecisionSupportGateReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    operator_flow_gate_config_version: str
    operator_flow_gate_generated_at: datetime
    operator_flow_gate_status: str
    operator_flow_recommended_next_step: str
    queue_priority_generated_at: datetime
    queue_risk_generated_at: datetime
    queue_risk_config_version: str
    queue_risk_status: str
    queue_risk_recommended_next_step: str
    queue_source_report_count: int
    queue_research_ready_count: int
    queue_watch_count: int
    queue_blocked_count: int
    queue_candidate_count: int
    queue_ready_count: int
    queue_candidate_watch_count: int
    queue_candidate_blocked_count: int
    queue_total_ready_notional: Decimal
    queue_largest_ready_notional: Decimal
    queue_top_research_priority_score: Decimal
    queue_average_research_priority_score: Decimal
    trend_source_snapshot_count: int | None
    trend_latest_risk_status: str | None
    trend_consecutive_latest_watch_count: int | None
    trend_consecutive_latest_blocked_count: int | None
    trend_duplicate_generated_at_count: int | None
    rank_stability_status: str | None
    rank_stable_ready_count: int | None
    rank_unstable_ready_count: int | None
    rank_blocked_count: int | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "operator_flow_gate_generated_at",
            _as_utc(
                "operator_flow_gate_generated_at",
                self.operator_flow_gate_generated_at,
            ),
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
            "operator_flow_gate_config_version",
            "operator_flow_recommended_next_step",
            "queue_risk_config_version",
            "queue_risk_recommended_next_step",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_gate_status("gate_status", self.gate_status)
        _require_gate_status("operator_flow_gate_status", self.operator_flow_gate_status)
        _require_gate_status("queue_risk_status", self.queue_risk_status)
        if self.trend_latest_risk_status is not None:
            _require_gate_status("trend_latest_risk_status", self.trend_latest_risk_status)
        if self.rank_stability_status is not None:
            _require_rank_stability_status(
                "rank_stability_status",
                self.rank_stability_status,
            )
        for field_name in (
            "queue_source_report_count",
            "queue_research_ready_count",
            "queue_watch_count",
            "queue_blocked_count",
            "queue_candidate_count",
            "queue_ready_count",
            "queue_candidate_watch_count",
            "queue_candidate_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "trend_source_snapshot_count",
            "trend_consecutive_latest_watch_count",
            "trend_consecutive_latest_blocked_count",
            "trend_duplicate_generated_at_count",
            "rank_stable_ready_count",
            "rank_unstable_ready_count",
            "rank_blocked_count",
        ):
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "queue_total_ready_notional",
            "queue_largest_ready_notional",
            "queue_top_research_priority_score",
            "queue_average_research_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
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
        _validate_report_consistency(self)
        _require_hard_flags("gate report", self)


def build_paper_autonomous_screening_decision_support_gate_report(
    *,
    operator_flow_gate_report: PaperResearchPacketOperatorFlowDbHistoryGateReport,
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
    generated_at: datetime,
    trend_report: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport
    | None = None,
    rank_stability_report: PaperProjectScreeningRankStabilityReport | None = None,
    config_version: str = (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION
    ),
) -> PaperAutonomousScreeningDecisionSupportGateReport:
    _validate_inputs(
        operator_flow_gate_report=operator_flow_gate_report,
        priority_report=priority_report,
        risk_report=risk_report,
        trend_report=trend_report,
        rank_stability_report=rank_stability_report,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_canonical_string("config_version", config_version)
    reason_codes = _gate_reason_codes(
        operator_flow_gate_report=operator_flow_gate_report,
        risk_report=risk_report,
        trend_report=trend_report,
        rank_stability_report=rank_stability_report,
    )
    gate_status = _gate_status(reason_codes)

    return PaperAutonomousScreeningDecisionSupportGateReport(
        generated_at=generated_at_utc,
        config_version=config_version,
        gate_status=gate_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[gate_status],
        reason_code_counts=_reason_code_counts(reason_codes),
        reason_codes=reason_codes,
        operator_flow_gate_config_version=operator_flow_gate_report.config_version,
        operator_flow_gate_generated_at=operator_flow_gate_report.generated_at,
        operator_flow_gate_status=operator_flow_gate_report.gate_status,
        operator_flow_recommended_next_step=(
            operator_flow_gate_report.recommended_next_step
        ),
        queue_priority_generated_at=priority_report.generated_at,
        queue_risk_generated_at=risk_report.generated_at,
        queue_risk_config_version=risk_report.config_version,
        queue_risk_status=risk_report.status,
        queue_risk_recommended_next_step=risk_report.recommended_next_step,
        queue_source_report_count=priority_report.source_report_count,
        queue_research_ready_count=priority_report.research_ready_count,
        queue_watch_count=priority_report.watch_count,
        queue_blocked_count=priority_report.blocked_count,
        queue_candidate_count=risk_report.candidate_count,
        queue_ready_count=risk_report.ready_count,
        queue_candidate_watch_count=risk_report.watch_count,
        queue_candidate_blocked_count=risk_report.blocked_count,
        queue_total_ready_notional=risk_report.total_ready_notional,
        queue_largest_ready_notional=risk_report.largest_queue_ready_notional,
        queue_top_research_priority_score=(
            priority_report.top_research_priority_score
        ),
        queue_average_research_priority_score=(
            priority_report.average_research_priority_score
        ),
        trend_source_snapshot_count=(
            trend_report.source_snapshot_count if trend_report is not None else None
        ),
        trend_latest_risk_status=(
            trend_report.latest_risk_status if trend_report is not None else None
        ),
        trend_consecutive_latest_watch_count=(
            trend_report.consecutive_latest_watch_count
            if trend_report is not None
            else None
        ),
        trend_consecutive_latest_blocked_count=(
            trend_report.consecutive_latest_blocked_count
            if trend_report is not None
            else None
        ),
        trend_duplicate_generated_at_count=(
            trend_report.duplicate_generated_at_count
            if trend_report is not None
            else None
        ),
        rank_stability_status=(
            rank_stability_report.stability_status
            if rank_stability_report is not None
            else None
        ),
        rank_stable_ready_count=(
            rank_stability_report.stable_ready_count
            if rank_stability_report is not None
            else None
        ),
        rank_unstable_ready_count=(
            rank_stability_report.unstable_ready_count
            if rank_stability_report is not None
            else None
        ),
        rank_blocked_count=(
            rank_stability_report.blocked_count
            if rank_stability_report is not None
            else None
        ),
    )


def _validate_inputs(
    *,
    operator_flow_gate_report: object,
    priority_report: object,
    risk_report: object,
    trend_report: object | None,
    rank_stability_report: object | None,
) -> None:
    if type(operator_flow_gate_report) is not PaperResearchPacketOperatorFlowDbHistoryGateReport:
        raise ValueError(
            "operator_flow_gate_report must be a "
            "PaperResearchPacketOperatorFlowDbHistoryGateReport",
        )
    if type(priority_report) is not PaperActionGatedStrategyRecommendationQueuePriorityReport:
        raise ValueError(
            "priority_report must be a "
            "PaperActionGatedStrategyRecommendationQueuePriorityReport",
        )
    if type(risk_report) is not PaperActionGatedStrategyRecommendationQueueRiskReport:
        raise ValueError(
            "risk_report must be a "
            "PaperActionGatedStrategyRecommendationQueueRiskReport",
        )
    if (
        trend_report is not None
        and type(trend_report)
        is not PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport
    ):
        raise ValueError(
            "trend_report must be a "
            "PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport",
        )
    if (
        rank_stability_report is not None
        and type(rank_stability_report) is not PaperProjectScreeningRankStabilityReport
    ):
        raise ValueError(
            "rank_stability_report must be a PaperProjectScreeningRankStabilityReport",
        )

    _require_hard_flags("operator_flow_gate_report", operator_flow_gate_report)
    _require_hard_flags("priority_report", priority_report)
    _require_hard_flags("risk_report", risk_report)
    _validate_priority_rows_hard_flags(priority_report)
    _validate_priority_risk_consistency(priority_report, risk_report)
    if trend_report is not None:
        _require_hard_flags("trend_report", trend_report)
        _validate_trend_current_snapshot(priority_report, risk_report, trend_report)
    if rank_stability_report is not None:
        _require_hard_flags("rank_stability_report", rank_stability_report)
        _validate_rank_stability_rows_hard_flags(rank_stability_report)


def _gate_reason_codes(
    *,
    operator_flow_gate_report: PaperResearchPacketOperatorFlowDbHistoryGateReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
    trend_report: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport
    | None,
    rank_stability_report: PaperProjectScreeningRankStabilityReport | None,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if operator_flow_gate_report.gate_status != "pass":
        reason_codes.append(
            f"operator_flow_db_history_gate_{operator_flow_gate_report.gate_status}",
        )
    if risk_report.status != "pass":
        reason_codes.append(f"queue_risk_{risk_report.status}")
    if trend_report is not None:
        reason_codes.extend(_trend_reason_codes(trend_report))
    if (
        rank_stability_report is not None
        and rank_stability_report.stability_status != "stable"
    ):
        reason_codes.append(
            f"project_screening_rank_stability_{rank_stability_report.stability_status}",
        )
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(sorted(set(reason_codes)))


def _trend_reason_codes(
    trend_report: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if trend_report.latest_risk_status in ("watch", "blocked"):
        reason_codes.append(
            f"queue_decision_support_trend_latest_risk_{trend_report.latest_risk_status}",
        )
    if trend_report.consecutive_latest_blocked_count > 0:
        reason_codes.append("queue_decision_support_trend_consecutive_latest_blocked")
    elif trend_report.consecutive_latest_watch_count > 0:
        reason_codes.append("queue_decision_support_trend_consecutive_latest_watch")
    if trend_report.duplicate_generated_at_count > 0:
        reason_codes.append("queue_decision_support_trend_duplicate_generated_at")
    return tuple(reason_codes)


def _gate_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[PaperAutonomousScreeningDecisionSupportGateReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for reason_code in reason_codes:
        counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperAutonomousScreeningDecisionSupportGateReasonCodeCount(
            reason_code=reason_code,
            report_count=report_count,
        )
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _validate_priority_rows_hard_flags(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> None:
    for row in priority_report.priority_rows:
        _require_hard_flags("priority_row", row)


def _validate_rank_stability_rows_hard_flags(
    rank_stability_report: PaperProjectScreeningRankStabilityReport,
) -> None:
    for row in rank_stability_report.rows:
        _require_hard_flags("rank_stability_row", row)


def _validate_priority_risk_consistency(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
) -> None:
    message = "priority_report and risk_report must describe the same source snapshot"
    if _as_utc("priority_report.generated_at", priority_report.generated_at) != _as_utc(
        "risk_report.generated_at",
        risk_report.generated_at,
    ):
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
    for field_name in ("candidate_count", "ready_count", "watch_count", "blocked_count"):
        if _sum_priority_rows(field_name, priority_report) != getattr(risk_report, field_name):
            raise ValueError(message)


def _validate_trend_current_snapshot(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
    trend_report: PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport,
) -> None:
    if trend_report.source_snapshot_count == 0:
        return
    message = "trend_report latest snapshot must match priority_report and risk_report"
    if trend_report.latest_generated_at != risk_report.generated_at:
        raise ValueError(message)
    if trend_report.latest_risk_status != risk_report.status:
        raise ValueError(message)
    if trend_report.source_queue_count_latest != risk_report.source_queue_count:
        raise ValueError(message)
    if trend_report.ready_notional_latest != risk_report.total_ready_notional:
        raise ValueError(message)
    if trend_report.top_priority_score_latest != priority_report.top_research_priority_score:
        raise ValueError(message)
    if (
        trend_report.average_priority_score_latest
        != priority_report.average_research_priority_score
    ):
        raise ValueError(message)


def _priority_source_config_versions(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> tuple[str, ...]:
    return tuple(sorted({row.config_version for row in priority_report.priority_rows}))


def _largest_priority_ready_notional(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> Decimal:
    return _quantize_nonnegative_decimal(
        "largest_queue_ready_notional",
        max(
            (row.total_ready_notional for row in priority_report.priority_rows),
            default=ZERO_DECIMAL,
        ),
    )


def _sum_priority_rows(
    field_name: str,
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
) -> int:
    return sum(getattr(row, field_name) for row in priority_report.priority_rows)


def _validate_report_consistency(
    report: PaperAutonomousScreeningDecisionSupportGateReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.gate_status]:
        raise ValueError("recommended_next_step must match gate_status")
    if (
        report.operator_flow_recommended_next_step
        != OPERATOR_FLOW_NEXT_STEP_BY_STATUS[report.operator_flow_gate_status]
    ):
        raise ValueError(
            "operator_flow_recommended_next_step must match operator_flow_gate_status",
        )
    if (
        report.queue_risk_recommended_next_step
        != QUEUE_RISK_NEXT_STEP_BY_STATUS[report.queue_risk_status]
    ):
        raise ValueError(
            "queue_risk_recommended_next_step must match queue_risk_status",
        )
    if tuple(row.reason_code for row in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
    if report.gate_status != _gate_status(report.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    has_pass_reason = PASS_REASON_CODE in report.reason_codes
    has_gate_reason = any(
        reason_code in BLOCKED_REASON_CODES or reason_code in WATCH_REASON_CODES
        for reason_code in report.reason_codes
    )
    if has_pass_reason and has_gate_reason:
        raise ValueError("pass reason must not be mixed with watch or blocked reasons")
    _validate_status_reason_codes(
        status_field_name="operator_flow_gate_status",
        status=report.operator_flow_gate_status,
        reason_code_by_status=OPERATOR_FLOW_REASON_CODE_BY_STATUS,
        reason_codes=report.reason_codes,
    )
    _validate_status_reason_codes(
        status_field_name="queue_risk_status",
        status=report.queue_risk_status,
        reason_code_by_status=QUEUE_RISK_REASON_CODE_BY_STATUS,
        reason_codes=report.reason_codes,
    )
    if (
        report.queue_source_report_count
        != report.queue_research_ready_count
        + report.queue_watch_count
        + report.queue_blocked_count
    ):
        raise ValueError("queue_source_report_count must match source status counts")
    if (
        report.queue_candidate_count
        != report.queue_ready_count
        + report.queue_candidate_watch_count
        + report.queue_candidate_blocked_count
    ):
        raise ValueError("queue_candidate_count must match candidate status counts")
    _validate_optional_trend_fields(report)
    _validate_optional_rank_fields(report)


def _validate_status_reason_codes(
    *,
    status_field_name: str,
    status: str,
    reason_code_by_status: dict[str, str],
    reason_codes: tuple[str, ...],
) -> None:
    source_reason_codes = set(reason_codes) & set(reason_code_by_status.values())
    expected_reason_code = reason_code_by_status.get(status)
    if expected_reason_code is None:
        if source_reason_codes:
            raise ValueError(f"{status_field_name} must match reason_codes")
        return
    if source_reason_codes != {expected_reason_code}:
        raise ValueError(f"{status_field_name} must match reason_codes")


def _validate_optional_trend_fields(
    report: PaperAutonomousScreeningDecisionSupportGateReport,
) -> None:
    trend_values = (
        report.trend_source_snapshot_count,
        report.trend_latest_risk_status,
        report.trend_consecutive_latest_watch_count,
        report.trend_consecutive_latest_blocked_count,
        report.trend_duplicate_generated_at_count,
    )
    if all(value is None for value in trend_values):
        if set(report.reason_codes) & TREND_REASON_CODES:
            raise ValueError("trend reason_codes require trend fields")
        return
    if report.trend_source_snapshot_count is None:
        raise ValueError("trend_source_snapshot_count is required with trend fields")
    if report.trend_source_snapshot_count == 0:
        if set(report.reason_codes) & TREND_REASON_CODES:
            raise ValueError("trend reason_codes require trend fields")
        if any(value is not None for value in trend_values[1:]):
            raise ValueError("trend fields must be absent without snapshots")
        return
    for field_name in (
        "trend_latest_risk_status",
        "trend_consecutive_latest_watch_count",
        "trend_consecutive_latest_blocked_count",
        "trend_duplicate_generated_at_count",
    ):
        if getattr(report, field_name) is None:
            raise ValueError(f"{field_name} is required with trend snapshots")


def _validate_optional_rank_fields(
    report: PaperAutonomousScreeningDecisionSupportGateReport,
) -> None:
    rank_values = (
        report.rank_stability_status,
        report.rank_stable_ready_count,
        report.rank_unstable_ready_count,
        report.rank_blocked_count,
    )
    if all(value is None for value in rank_values):
        if set(report.reason_codes) & set(RANK_STABILITY_REASON_CODE_BY_STATUS.values()):
            raise ValueError("rank_stability_status must match reason_codes")
        return
    if any(value is None for value in rank_values):
        raise ValueError("rank fields must be present together")
    _validate_status_reason_codes(
        status_field_name="rank_stability_status",
        status="pass" if report.rank_stability_status == "stable" else report.rank_stability_status,
        reason_code_by_status=RANK_STABILITY_REASON_CODE_BY_STATUS,
        reason_codes=report.reason_codes,
    )


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperAutonomousScreeningDecisionSupportGateReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_code_counts is required")
    previous_key: tuple[int, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not PaperAutonomousScreeningDecisionSupportGateReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason rows")
        if row.report_count != 1:
            raise ValueError("reason_code_counts report_count must be 1")
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
    allowed = BLOCKED_REASON_CODES | WATCH_REASON_CODES | {PASS_REASON_CODE}
    for code in codes:
        _require_canonical_string(field_name, code)
        if code not in allowed:
            raise ValueError(f"{field_name} must match gate semantics")
        if code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > code:
            raise ValueError(f"{field_name} must be sorted")
        previous = code
        seen.add(code)
    return codes


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


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_rank_stability_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RANK_STABILITY_STATUSES:
        raise ValueError(f"{field_name} must be stable, watch, or blocked")


def _require_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_positive_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _quantize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_DECIMAL:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = value.quantize(DECIMAL_QUANTUM)
    if quantized < ZERO_DECIMAL:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")
