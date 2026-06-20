from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend import (
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReasonCodeRow,
    PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport,
    build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority import (
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
    PaperActionGatedStrategyRecommendationQueuePriorityRow,
)
from polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk import (
    PaperActionGatedStrategyRecommendationQueueRiskReport,
)


GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
BASE_AT = datetime(2026, 6, 20, 8, 0, tzinfo=UTC)

NEXT_STEP_BY_ACTION_STATUS = {
    "research_ready": "review_candidate_research_queue",
    "watch": "await_fresh_cycle_evidence",
    "blocked": "repair_cycle_evidence",
}
RESEARCH_PRIORITY_BY_ACTION_STATUS = {
    "research_ready": "research_review",
    "watch": "await_fresh_context",
    "blocked": "repair_evidence",
}
ACTION_STATUS_SCORE = {
    "research_ready": Decimal("3.000000"),
    "watch": Decimal("1.000000"),
    "blocked": Decimal("0.000000"),
}
NEXT_STEP_BY_RISK_STATUS = {
    "pass": "allocate_paper_research_queue",
    "watch": "throttle_paper_research_queue",
    "blocked": "block_paper_research_queue",
}


class PriorityReportSubclass(PaperActionGatedStrategyRecommendationQueuePriorityReport):
    pass


class RiskReportSubclass(PaperActionGatedStrategyRecommendationQueueRiskReport):
    pass


def _priority_row(
    *,
    priority_rank: int = 1,
    generated_at: datetime = BASE_AT,
    action_status: str = "research_ready",
    candidate_count: int = 1,
    ready_count: int = 1,
    watch_count: int = 0,
    blocked_count: int = 0,
    total_ready_notional: Decimal = Decimal("10.000000"),
    top_queue_score: Decimal = Decimal("0.400000"),
    average_ready_score: Decimal = Decimal("0.300000"),
) -> PaperActionGatedStrategyRecommendationQueuePriorityRow:
    return PaperActionGatedStrategyRecommendationQueuePriorityRow(
        priority_rank=priority_rank,
        source_generated_at=generated_at - timedelta(minutes=5),
        config_version="action-gated-strategy-recommendation-queue-v0",
        source_config_version="paper-recommendation-cycle-action-gate-v0",
        action_status=action_status,
        recommended_next_step=NEXT_STEP_BY_ACTION_STATUS[action_status],
        research_priority=RESEARCH_PRIORITY_BY_ACTION_STATUS[action_status],
        candidate_count=candidate_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        total_ready_notional=total_ready_notional,
        top_queue_score=top_queue_score,
        average_ready_score=average_ready_score,
        research_priority_score=(
            ACTION_STATUS_SCORE[action_status]
            + Decimal(ready_count)
            + top_queue_score
            + average_ready_score
        ).quantize(Decimal("0.000001")),
    )


def _priority_report(
    *,
    generated_at: datetime = BASE_AT,
    rows: tuple[PaperActionGatedStrategyRecommendationQueuePriorityRow, ...] | None = None,
) -> PaperActionGatedStrategyRecommendationQueuePriorityReport:
    if rows is None:
        rows = (_priority_row(generated_at=generated_at),)
    return PaperActionGatedStrategyRecommendationQueuePriorityReport(
        generated_at=generated_at,
        source_report_count=len(rows),
        research_ready_count=sum(1 for row in rows if row.action_status == "research_ready"),
        watch_count=sum(1 for row in rows if row.action_status == "watch"),
        blocked_count=sum(1 for row in rows if row.action_status == "blocked"),
        total_ready_notional=sum((row.total_ready_notional for row in rows), Decimal("0")),
        top_research_priority_score=max(
            (row.research_priority_score for row in rows),
            default=Decimal("0.000000"),
        ),
        average_research_priority_score=(
            (
                sum((row.research_priority_score for row in rows), Decimal("0"))
                / Decimal(len(rows))
            ).quantize(Decimal("0.000001"))
            if rows
            else Decimal("0.000000")
        ),
        priority_rows=rows,
    )


def _risk_report(
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    *,
    status: str = "pass",
    reason_codes: tuple[str, ...] = ("queue_risk_passed",),
    max_total_ready_notional: Decimal = Decimal("100.000000"),
    max_single_queue_ready_notional: Decimal = Decimal("200.000000"),
    max_ready_candidate_count: int = 10,
    max_total_candidate_count: int = 20,
    throttle_utilization_threshold: Decimal = Decimal("0.900000"),
) -> PaperActionGatedStrategyRecommendationQueueRiskReport:
    ready_notional = priority_report.total_ready_notional
    largest_notional = max(
        (row.total_ready_notional for row in priority_report.priority_rows),
        default=Decimal("0.000000"),
    )
    source_queue_count = priority_report.source_report_count
    candidate_count = sum(row.candidate_count for row in priority_report.priority_rows)
    ready_count = sum(row.ready_count for row in priority_report.priority_rows)
    watch_count = sum(row.watch_count for row in priority_report.priority_rows)
    blocked_count = sum(row.blocked_count for row in priority_report.priority_rows)
    blocking_reasons = {
        "empty_queue_reports",
        "source_queue_blocked",
        "total_ready_notional_cap_exceeded",
        "single_queue_ready_notional_cap_exceeded",
        "ready_candidate_count_cap_exceeded",
        "candidate_count_cap_exceeded",
    }
    watch_reasons = {
        "source_queue_watch",
        "near_total_ready_notional_cap",
        "near_single_queue_ready_notional_cap",
        "near_ready_candidate_count_cap",
        "near_candidate_count_cap",
    }
    return PaperActionGatedStrategyRecommendationQueueRiskReport(
        generated_at=priority_report.generated_at,
        config_version="action-gated-queue-risk-v0",
        source_config_versions=("action-gated-strategy-recommendation-queue-v0",),
        status=status,
        recommended_next_step=NEXT_STEP_BY_RISK_STATUS[status],
        reason_codes=reason_codes,
        source_queue_count=source_queue_count,
        research_ready_source_count=priority_report.research_ready_count,
        watch_source_count=priority_report.watch_count,
        blocked_source_count=priority_report.blocked_count,
        candidate_count=candidate_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        blocked_reason_count=sum(1 for reason in reason_codes if reason in blocking_reasons),
        watch_reason_count=sum(1 for reason in reason_codes if reason in watch_reasons),
        total_ready_notional=ready_notional,
        largest_queue_ready_notional=largest_notional,
        total_ready_notional_utilization=(
            (ready_notional / max_total_ready_notional).quantize(Decimal("0.000001"))
            if max_total_ready_notional > Decimal("0")
            else None
        ),
        largest_queue_ready_notional_utilization=(
            (largest_notional / max_single_queue_ready_notional).quantize(
                Decimal("0.000001"),
            )
            if max_single_queue_ready_notional > Decimal("0")
            else None
        ),
        max_total_ready_notional=max_total_ready_notional,
        max_single_queue_ready_notional=max_single_queue_ready_notional,
        max_ready_candidate_count=max_ready_candidate_count,
        max_total_candidate_count=max_total_candidate_count,
        throttle_utilization_threshold=throttle_utilization_threshold,
    )


def _snapshot(
    *,
    generated_at: datetime,
    rows: tuple[PaperActionGatedStrategyRecommendationQueuePriorityRow, ...] | None = None,
    risk_status: str = "pass",
    risk_reason_codes: tuple[str, ...] = ("queue_risk_passed",),
    max_total_ready_notional: Decimal = Decimal("100.000000"),
) -> tuple[
    PaperActionGatedStrategyRecommendationQueuePriorityReport,
    PaperActionGatedStrategyRecommendationQueueRiskReport,
]:
    priority_report = _priority_report(generated_at=generated_at, rows=rows)
    return (
        priority_report,
        _risk_report(
            priority_report,
            status=risk_status,
            reason_codes=risk_reason_codes,
            max_total_ready_notional=max_total_ready_notional,
        ),
    )


def test_decision_support_trend_empty_input_is_paper_report_readonly():
    trend = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
        (),
        generated_at=GENERATED_AT,
    )

    assert isinstance(
        trend,
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport,
    )
    assert trend.generated_at == GENERATED_AT
    assert trend.source_snapshot_count == 0
    assert trend.first_generated_at is None
    assert trend.latest_generated_at is None
    assert trend.latest_risk_status is None
    assert trend.risk_status_counts == ()
    assert trend.consecutive_latest_watch_count == 0
    assert trend.consecutive_latest_blocked_count == 0
    assert trend.ready_notional_first is None
    assert trend.ready_notional_latest is None
    assert trend.ready_notional_delta is None
    assert trend.top_priority_score_first is None
    assert trend.top_priority_score_latest is None
    assert trend.top_priority_score_delta is None
    assert trend.average_priority_score_first is None
    assert trend.average_priority_score_latest is None
    assert trend.average_priority_score_delta is None
    assert trend.source_queue_count_first is None
    assert trend.source_queue_count_latest is None
    assert trend.source_queue_count_delta is None
    assert trend.duplicate_generated_at_count == 0
    assert trend.latest_reason_code_counts == ()
    assert trend.total_reason_code_counts == ()
    assert trend.repeated_reason_code_counts == ()
    assert trend.reason_code_rows == ()
    assert trend.source_summaries == ()
    assert trend.paper_only is True
    assert trend.report_only is True
    assert trend.readonly is True


def test_decision_support_trend_sorts_reverse_loaded_snapshots_chronologically():
    older = _snapshot(
        generated_at=BASE_AT,
        rows=(
            _priority_row(
                generated_at=BASE_AT,
                total_ready_notional=Decimal("10.000000"),
                top_queue_score=Decimal("0.200000"),
                average_ready_score=Decimal("0.100000"),
            ),
        ),
    )
    latest_at = BASE_AT + timedelta(hours=2)
    latest = _snapshot(
        generated_at=latest_at,
        rows=(
            _priority_row(
                priority_rank=1,
                generated_at=latest_at,
                total_ready_notional=Decimal("30.000000"),
                top_queue_score=Decimal("0.600000"),
                average_ready_score=Decimal("0.500000"),
            ),
            _priority_row(
                priority_rank=2,
                generated_at=latest_at,
                action_status="watch",
                candidate_count=1,
                ready_count=0,
                watch_count=1,
                total_ready_notional=Decimal("0.000000"),
                top_queue_score=Decimal("0.000000"),
                average_ready_score=Decimal("0.000000"),
            ),
        ),
        risk_status="watch",
        risk_reason_codes=("source_queue_watch",),
    )

    trend = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
        (latest, older),
        generated_at=GENERATED_AT,
    )

    assert trend.source_snapshot_count == 2
    assert trend.first_generated_at == BASE_AT
    assert trend.latest_generated_at == latest_at
    assert trend.latest_risk_status == "watch"
    assert trend.risk_status_counts == (("pass", 1), ("watch", 1))
    assert trend.ready_notional_first == Decimal("10.000000")
    assert trend.ready_notional_latest == Decimal("30.000000")
    assert trend.ready_notional_delta == Decimal("20.000000")
    assert trend.top_priority_score_first == Decimal("4.300000")
    assert trend.top_priority_score_latest == Decimal("5.100000")
    assert trend.top_priority_score_delta == Decimal("0.800000")
    assert trend.average_priority_score_first == Decimal("4.300000")
    assert trend.average_priority_score_latest == Decimal("3.050000")
    assert trend.average_priority_score_delta == Decimal("-1.250000")
    assert trend.source_queue_count_first == 1
    assert trend.source_queue_count_latest == 2
    assert trend.source_queue_count_delta == 1
    assert tuple(summary.generated_at for summary in trend.source_summaries) == (
        BASE_AT,
        latest_at,
    )


def test_decision_support_trend_counts_latest_streaks_and_duplicate_timestamps():
    first = _snapshot(
        generated_at=BASE_AT,
        rows=(
            _priority_row(
                generated_at=BASE_AT,
                action_status="watch",
                candidate_count=1,
                ready_count=0,
                watch_count=1,
                total_ready_notional=Decimal("0.000000"),
                top_queue_score=Decimal("0.000000"),
                average_ready_score=Decimal("0.000000"),
            ),
        ),
        risk_status="watch",
        risk_reason_codes=("source_queue_watch",),
    )
    duplicate_timestamp = _snapshot(
        generated_at=BASE_AT + timedelta(hours=1),
        rows=(
            _priority_row(
                generated_at=BASE_AT + timedelta(hours=1),
                action_status="blocked",
                candidate_count=1,
                ready_count=0,
                watch_count=0,
                blocked_count=1,
                total_ready_notional=Decimal("0.000000"),
                top_queue_score=Decimal("0.000000"),
                average_ready_score=Decimal("0.000000"),
            ),
        ),
        risk_status="blocked",
        risk_reason_codes=("source_queue_blocked",),
    )
    latest_same_time = _snapshot(
        generated_at=BASE_AT + timedelta(hours=1),
        rows=(
            _priority_row(
                generated_at=BASE_AT + timedelta(hours=1),
                action_status="blocked",
                candidate_count=1,
                ready_count=0,
                watch_count=0,
                blocked_count=1,
                total_ready_notional=Decimal("0.000000"),
                top_queue_score=Decimal("0.000000"),
                average_ready_score=Decimal("0.000000"),
            ),
        ),
        risk_status="blocked",
        risk_reason_codes=("source_queue_blocked",),
    )

    trend = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
        (first, duplicate_timestamp, latest_same_time),
        generated_at=GENERATED_AT,
    )

    assert trend.latest_risk_status == "blocked"
    assert trend.risk_status_counts == (("watch", 1), ("blocked", 2))
    assert trend.consecutive_latest_watch_count == 0
    assert trend.consecutive_latest_blocked_count == 2
    assert trend.duplicate_generated_at_count == 1
    assert tuple(summary.input_position for summary in trend.source_summaries) == (1, 2, 3)


def test_decision_support_trend_aggregates_latest_total_and_repeated_reason_codes():
    first = _snapshot(
        generated_at=BASE_AT,
        rows=(
            _priority_row(
                generated_at=BASE_AT,
                action_status="watch",
                candidate_count=1,
                ready_count=0,
                watch_count=1,
                total_ready_notional=Decimal("0.000000"),
                top_queue_score=Decimal("0.000000"),
                average_ready_score=Decimal("0.000000"),
            ),
        ),
        risk_status="watch",
        risk_reason_codes=("source_queue_watch",),
    )
    middle_at = BASE_AT + timedelta(hours=1)
    middle = _snapshot(
        generated_at=middle_at,
        rows=(
            _priority_row(
                generated_at=middle_at,
                total_ready_notional=Decimal("90.000000"),
            ),
        ),
        risk_status="watch",
        risk_reason_codes=("near_total_ready_notional_cap",),
        max_total_ready_notional=Decimal("100.000000"),
    )
    latest_at = BASE_AT + timedelta(hours=2)
    latest = _snapshot(
        generated_at=latest_at,
        rows=(
            _priority_row(
                generated_at=latest_at,
                action_status="watch",
                candidate_count=1,
                ready_count=0,
                watch_count=1,
                total_ready_notional=Decimal("0.000000"),
                top_queue_score=Decimal("0.000000"),
                average_ready_score=Decimal("0.000000"),
            ),
        ),
        risk_status="watch",
        risk_reason_codes=("source_queue_watch",),
    )

    trend = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
        (first, middle, latest),
        generated_at=GENERATED_AT,
    )

    assert trend.latest_reason_code_counts == (("source_queue_watch", 1),)
    assert trend.total_reason_code_counts == (
        ("source_queue_watch", 2),
        ("near_total_ready_notional_cap", 1),
    )
    assert trend.repeated_reason_code_counts == (("source_queue_watch", 2),)
    assert tuple(
        (row.reason_code, row.total_count, row.latest_count, row.snapshot_count)
        for row in trend.reason_code_rows
    ) == (
        ("source_queue_watch", 2, 1, 2),
        ("near_total_ready_notional_cap", 1, 0, 1),
    )


def test_decision_support_trend_normalizes_datetimes_to_utc_and_rejects_bad_inputs():
    generated_at = datetime(2026, 6, 20, 14, 0, tzinfo=timezone(timedelta(hours=2)))
    source_at = datetime(2026, 6, 20, 11, 0, tzinfo=timezone(timedelta(hours=2)))
    snapshot = _snapshot(generated_at=source_at)

    trend = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
        (snapshot,),
        generated_at=generated_at,
    )

    assert trend.generated_at == datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
    assert trend.first_generated_at == datetime(2026, 6, 20, 9, 0, tzinfo=UTC)
    assert trend.latest_generated_at == datetime(2026, 6, 20, 9, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at"):
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
            (snapshot,),
            generated_at="2026-06-20",
        )
    with pytest.raises(ValueError, match="snapshot_pairs"):
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
            "not snapshots",
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="snapshot_pairs"):
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
            (object(),),
            generated_at=GENERATED_AT,
        )


def test_decision_support_trend_rejects_mismatched_snapshot_pairs_and_false_flags():
    priority_report, risk_report = _snapshot(generated_at=BASE_AT)

    mismatched_risk = PaperActionGatedStrategyRecommendationQueueRiskReport(
        **{
            **risk_report.__dict__,
            "source_queue_count": 2,
            "research_ready_source_count": 2,
        },
    )
    with pytest.raises(ValueError, match="same source snapshot"):
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
            ((priority_report, mismatched_risk),),
            generated_at=GENERATED_AT,
        )

    mismatched_largest_risk = PaperActionGatedStrategyRecommendationQueueRiskReport(
        **{
            **risk_report.__dict__,
            "largest_queue_ready_notional": Decimal("0.000000"),
            "largest_queue_ready_notional_utilization": Decimal("0.000000"),
        },
    )
    with pytest.raises(ValueError, match="same source snapshot"):
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
            ((priority_report, mismatched_largest_risk),),
            generated_at=GENERATED_AT,
        )

    for flag_name in ("paper_only", "report_only", "readonly"):
        priority_with_false_flag = PaperActionGatedStrategyRecommendationQueuePriorityReport(
            **priority_report.__dict__,
        )
        object.__setattr__(priority_with_false_flag, flag_name, False)
        with pytest.raises(ValueError, match=flag_name):
            build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
                ((priority_with_false_flag, risk_report),),
                generated_at=GENERATED_AT,
            )

    with pytest.raises(ValueError, match="PriorityReport"):
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
            ((PriorityReportSubclass(**priority_report.__dict__), risk_report),),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="RiskReport"):
        build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
            ((priority_report, RiskReportSubclass(**risk_report.__dict__)),),
            generated_at=GENERATED_AT,
        )


def test_decision_support_trend_dataclasses_are_frozen_and_revalidate_invariants():
    older = _snapshot(generated_at=BASE_AT)
    latest = _snapshot(
        generated_at=BASE_AT + timedelta(hours=1),
        rows=(
            _priority_row(
                generated_at=BASE_AT + timedelta(hours=1),
                action_status="watch",
                candidate_count=1,
                ready_count=0,
                watch_count=1,
                total_ready_notional=Decimal("0.000000"),
                top_queue_score=Decimal("0.000000"),
                average_ready_score=Decimal("0.000000"),
            ),
        ),
        risk_status="watch",
        risk_reason_codes=("source_queue_watch",),
    )
    trend = build_paper_action_gated_strategy_recommendation_queue_decision_support_trend_report(
        (latest, older),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        trend.latest_risk_status = "watch"
    with pytest.raises(ValueError, match="paper_only"):
        replace(trend, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(trend, readonly=False)
    with pytest.raises(ValueError, match="source_snapshot_count"):
        replace(trend, source_snapshot_count=3)
    with pytest.raises(ValueError, match="latest_risk_status"):
        replace(trend, latest_risk_status="blocked")
    with pytest.raises(ValueError, match="source_summaries"):
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport(
            generated_at=trend.generated_at,
            source_snapshot_count=trend.source_snapshot_count,
            first_generated_at=trend.source_summaries[1].generated_at,
            latest_generated_at=trend.source_summaries[0].generated_at,
            latest_risk_status=trend.source_summaries[0].risk_status,
            risk_status_counts=trend.risk_status_counts,
            consecutive_latest_watch_count=0,
            consecutive_latest_blocked_count=0,
            ready_notional_first=trend.source_summaries[1].ready_notional,
            ready_notional_latest=trend.source_summaries[0].ready_notional,
            ready_notional_delta=(
                trend.source_summaries[0].ready_notional
                - trend.source_summaries[1].ready_notional
            ),
            top_priority_score_first=trend.source_summaries[1].top_priority_score,
            top_priority_score_latest=trend.source_summaries[0].top_priority_score,
            top_priority_score_delta=(
                trend.source_summaries[0].top_priority_score
                - trend.source_summaries[1].top_priority_score
            ),
            average_priority_score_first=trend.source_summaries[
                1
            ].average_priority_score,
            average_priority_score_latest=trend.source_summaries[
                0
            ].average_priority_score,
            average_priority_score_delta=(
                trend.source_summaries[0].average_priority_score
                - trend.source_summaries[1].average_priority_score
            ),
            source_queue_count_first=trend.source_summaries[1].source_queue_count,
            source_queue_count_latest=trend.source_summaries[0].source_queue_count,
            source_queue_count_delta=(
                trend.source_summaries[0].source_queue_count
                - trend.source_summaries[1].source_queue_count
            ),
            duplicate_generated_at_count=0,
            latest_reason_code_counts=(("source_queue_watch", 1),),
            total_reason_code_counts=trend.total_reason_code_counts,
            repeated_reason_code_counts=trend.repeated_reason_code_counts,
            reason_code_rows=(
                PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReasonCodeRow(
                    reason_code="source_queue_watch",
                    total_count=1,
                    latest_count=1,
                    snapshot_count=1,
                ),
                PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReasonCodeRow(
                    reason_code="queue_risk_passed",
                    total_count=1,
                    latest_count=0,
                    snapshot_count=1,
                ),
            ),
            source_summaries=tuple(reversed(trend.source_summaries)),
        )
    with pytest.raises(ValueError, match="input_position"):
        replace(
            trend,
            source_summaries=(
                replace(trend.source_summaries[0], input_position=1),
                replace(trend.source_summaries[1], input_position=1),
            ),
        )
