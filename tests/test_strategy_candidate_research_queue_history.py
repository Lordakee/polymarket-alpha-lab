"""Tests for strategy candidate research queue history reducer."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_recommendation_cycle_action_gate import (
    PaperRecommendationCycleActionGateReasonCodeCount,
)
from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
    PaperStrategyCandidateResearchQueueRow,
)
from polymarket_alpha_lab.strategy_candidate_research_queue_history import (
    PaperStrategyCandidateResearchQueueHistoryReport,
    build_paper_strategy_candidate_research_queue_history_report,
)


def _reason_count(reason_code: str, count: int) -> PaperRecommendationCycleActionGateReasonCodeCount:
    return PaperRecommendationCycleActionGateReasonCodeCount(
        reason_code=reason_code, count=count,
    )


def _research_row(
    *,
    research_rank: int,
    queue_rank: int,
    market_slug: str,
    source_action: str,
    decision: str,
    queue_status: str,
    research_status: str,
    recommendation_score: Decimal,
    readiness_score: Decimal,
    suggested_notional: Decimal,
    selected_position_notional: Decimal,
    primary_reason_code: str,
    reason_codes: tuple[str, ...],
    selected_side: str = "yes",
) -> PaperStrategyCandidateResearchQueueRow:
    return PaperStrategyCandidateResearchQueueRow(
        research_rank=research_rank,
        queue_rank=queue_rank,
        market_slug=market_slug,
        question=f"Will {market_slug} resolve yes?",
        selected_side=selected_side,
        scoring_side="yes",
        source_action=source_action,
        decision=decision,
        queue_status=queue_status,
        research_status=research_status,
        research_bucket="history_test",
        assessment_status=research_status,
        source_status="active",
        readiness_status="pass" if research_status == "ready" else research_status,
        recommendation_score=recommendation_score,
        readiness_score=readiness_score,
        screening_score=Decimal("0.500000"),
        net_edge_per_share=Decimal("0.100000"),
        total_cost_per_share=Decimal("0.010000"),
        confidence=Decimal("0.900000"),
        spread=Decimal("0.010000"),
        resolution_risk=Decimal("0.020000"),
        suggested_notional=suggested_notional,
        selected_position_notional=selected_position_notional,
        primary_reason_code=primary_reason_code,
        research_priority_score=(
            (recommendation_score + readiness_score) / Decimal("2")
        ).quantize(Decimal("0.000001")),
        evidence_gap_codes=(),
        reason_codes=reason_codes,
        explanation=f"{source_action} because {primary_reason_code}",
    )


def _make_queue_report_from_rows(
    *,
    generated_at: datetime,
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
) -> PaperStrategyCandidateResearchQueueReport:
    return PaperStrategyCandidateResearchQueueReport(
        generated_at=generated_at,
        config_version="test-v1",
        source_config_version="source-v1",
        action_status="research_ready",
        recommended_next_step="review_candidate_research_queue",
        source_reason_code_counts=(_reason_count("cycle_review_research_ready", 1),),
        research_status="ready",
        candidate_count=len(rows),
        research_ready_count=sum(1 for row in rows if row.research_status == "ready"),
        watch_count=sum(1 for row in rows if row.research_status == "watch"),
        blocked_count=sum(1 for row in rows if row.research_status == "blocked"),
        selected_count=sum(1 for row in rows if row.decision == "selected"),
        skipped_count=sum(1 for row in rows if row.decision == "skipped"),
        not_selected_count=sum(1 for row in rows if row.decision == "not_selected"),
        total_ready_notional=sum(
            (
                row.suggested_notional
                for row in rows
                if row.research_status == "ready"
            ),
            Decimal("0"),
        ),
        total_selected_notional=sum(
            (row.selected_position_notional for row in rows),
            Decimal("0"),
        ),
        total_suggested_notional=sum(
            (
                row.suggested_notional
                for row in rows
                if row.source_action == "recommend"
            ),
            Decimal("0"),
        ),
        top_research_priority_score=rows[0].research_priority_score,
        average_research_ready_score=(
            sum(
                (
                    row.research_priority_score
                    for row in rows
                    if row.research_status == "ready"
                ),
                Decimal("0"),
            )
            / Decimal(sum(1 for row in rows if row.research_status == "ready"))
        ).quantize(Decimal("0.000001")),
        primary_reason_code_counts=tuple(
            sorted(
                {
                    row.primary_reason_code: sum(
                        1
                        for counted_row in rows
                        if counted_row.primary_reason_code == row.primary_reason_code
                    )
                    for row in rows
                }.items(),
                key=lambda item: (-item[1], item[0]),
            ),
        ),
        rows=rows,
        reason_codes=("candidate_research_queue_ready",),
    )


def _make_queue_report(
    *,
    generated_at: datetime | None = None,
    action_status: str = "watch",
    research_status: str = "watch",
    config_version: str = "test-v1",
    source_config_version: str = "source-v1",
    total_ready_notional: Decimal = Decimal("0"),
    total_selected_notional: Decimal = Decimal("0"),
    total_suggested_notional: Decimal = Decimal("0"),
    top_research_priority_score: Decimal = Decimal("0"),
    average_research_ready_score: Decimal = Decimal("0"),
) -> PaperStrategyCandidateResearchQueueReport:
    next_step = {
        "research_ready": "review_candidate_research_queue",
        "watch": "await_fresh_cycle_evidence",
        "blocked": "repair_cycle_evidence",
    }[action_status]
    return PaperStrategyCandidateResearchQueueReport(
        generated_at=generated_at or datetime.now(UTC),
        config_version=config_version,
        source_config_version=source_config_version,
        action_status=action_status,
        recommended_next_step=next_step,
        source_reason_code_counts=(_reason_count("cycle_review_watch", 1),),
        research_status=research_status,
        candidate_count=0,
        research_ready_count=0,
        watch_count=0,
        blocked_count=0,
        selected_count=0,
        skipped_count=0,
        not_selected_count=0,
        total_ready_notional=total_ready_notional,
        total_selected_notional=total_selected_notional,
        total_suggested_notional=total_suggested_notional,
        top_research_priority_score=top_research_priority_score,
        average_research_ready_score=average_research_ready_score,
        primary_reason_code_counts=(),
        rows=(),
        reason_codes=(("source_action_status_watch",) if action_status == "watch" else ("source_action_status_blocked",)),
    )


def _history_report_kwargs(**overrides: object) -> dict[str, object]:
    t0 = datetime(2025, 1, 1, tzinfo=UTC)
    values: dict[str, object] = {
        "generated_at": t0,
        "source_report_count": 1,
        "first_source_generated_at": t0,
        "last_source_generated_at": t0,
        "action_status_research_ready_count": 0,
        "action_status_watch_count": 1,
        "action_status_blocked_count": 0,
        "research_status_ready_count": 0,
        "research_status_watch_count": 1,
        "research_status_blocked_count": 0,
        "total_ready_notional": Decimal("0"),
        "total_selected_notional": Decimal("0"),
        "total_suggested_notional": Decimal("0"),
        "latest_action_status": "watch",
        "latest_recommended_next_step": "await_fresh_cycle_evidence",
        "latest_research_status": "watch",
        "latest_top_research_priority_score": Decimal("0"),
        "latest_average_research_ready_score": Decimal("0"),
        "status_transition_count": 0,
        "ready_notional_delta": Decimal("0"),
        "selected_notional_delta": Decimal("0"),
        "latest_selected_count": 0,
        "latest_skipped_count": 0,
        "latest_not_selected_count": 0,
        "latest_primary_reason_code_counts": (),
        "latest_reason_codes": (),
    }
    values.update(overrides)
    return values


class TestBuildEmptyHistoryReport:
    def test_empty_reports_produce_zero_counts(self) -> None:
        now = datetime.now(UTC)
        r = build_paper_strategy_candidate_research_queue_history_report(
            [], generated_at=now,
        )
        assert r.source_report_count == 0
        assert r.first_source_generated_at is None
        assert r.last_source_generated_at is None
        assert r.action_status_research_ready_count == 0
        assert r.action_status_watch_count == 0
        assert r.action_status_blocked_count == 0
        assert r.research_status_ready_count == 0
        assert r.research_status_watch_count == 0
        assert r.research_status_blocked_count == 0
        assert r.total_ready_notional == Decimal("0")
        assert r.total_selected_notional == Decimal("0")
        assert r.total_suggested_notional == Decimal("0")
        assert r.latest_action_status is None
        assert r.latest_recommended_next_step is None
        assert r.latest_research_status is None
        assert r.latest_top_research_priority_score is None
        assert r.latest_average_research_ready_score is None
        assert r.status_transition_count == 0
        assert r.ready_notional_delta == Decimal("0")
        assert r.selected_notional_delta == Decimal("0")
        assert r.latest_selected_count == 0
        assert r.latest_skipped_count == 0
        assert r.latest_not_selected_count == 0
        assert r.latest_primary_reason_code_counts == ()
        assert r.latest_reason_codes == ()
        assert r.paper_only is True
        assert r.report_only is True
        assert r.readonly is True


class TestBuildNonemptyHistoryReport:
    def test_single_watch_report(self) -> None:
        now = datetime.now(UTC)
        report = _make_queue_report(generated_at=now, action_status="watch")
        r = build_paper_strategy_candidate_research_queue_history_report(
            [report], generated_at=now,
        )
        assert r.source_report_count == 1
        assert r.first_source_generated_at == now
        assert r.last_source_generated_at == now
        assert r.action_status_research_ready_count == 0
        assert r.action_status_watch_count == 1
        assert r.action_status_blocked_count == 0
        assert r.research_status_watch_count == 1
        assert r.latest_action_status == "watch"
        assert r.latest_recommended_next_step == "await_fresh_cycle_evidence"
        assert r.latest_research_status == "watch"
        assert r.status_transition_count == 0
        assert r.ready_notional_delta == Decimal("0")
        assert r.selected_notional_delta == Decimal("0")
        assert r.latest_selected_count == 0
        assert r.latest_skipped_count == 0
        assert r.latest_not_selected_count == 0

    def test_multiple_reports_status_transitions(self) -> None:
        t0 = datetime(2025, 1, 1, tzinfo=UTC)
        t1 = datetime(2025, 1, 2, tzinfo=UTC)
        t2 = datetime(2025, 1, 3, tzinfo=UTC)
        r0 = _make_queue_report(generated_at=t0, action_status="watch")
        r1 = _make_queue_report(generated_at=t1, action_status="blocked")
        r2 = _make_queue_report(generated_at=t2, action_status="watch")
        h = build_paper_strategy_candidate_research_queue_history_report(
            [r0, r1, r2], generated_at=t2,
        )
        assert h.source_report_count == 3
        assert h.action_status_watch_count == 2
        assert h.action_status_blocked_count == 1
        assert h.action_status_research_ready_count == 0
        assert h.status_transition_count == 2
        assert h.latest_action_status == "watch"
        assert h.first_source_generated_at == t0
        assert h.last_source_generated_at == t2

    def test_notional_accumulation(self) -> None:
        """Notional sums and deltas track across multiple reports."""
        t0 = datetime(2025, 1, 1, tzinfo=UTC)
        t1 = datetime(2025, 1, 2, tzinfo=UTC)
        r0 = _make_queue_report_from_rows(
            generated_at=t0,
            rows=(
                _research_row(
                    research_rank=1,
                    queue_rank=1,
                    market_slug="alpha-selected",
                    source_action="recommend",
                    decision="selected",
                    queue_status="ready",
                    research_status="ready",
                    recommendation_score=Decimal("0.700000"),
                    readiness_score=Decimal("0.900000"),
                    suggested_notional=Decimal("2.000000"),
                    selected_position_notional=Decimal("2.000000"),
                    primary_reason_code="recommendation_ready",
                    reason_codes=("recommendation_ready",),
                ),
                _research_row(
                    research_rank=2,
                    queue_rank=2,
                    market_slug="beta-ready",
                    source_action="recommend",
                    decision="skipped",
                    queue_status="ready",
                    research_status="ready",
                    recommendation_score=Decimal("0.600000"),
                    readiness_score=Decimal("0.800000"),
                    suggested_notional=Decimal("8.250000"),
                    selected_position_notional=Decimal("0.000000"),
                    primary_reason_code="capacity_watch",
                    reason_codes=("capacity_watch",),
                ),
                _research_row(
                    research_rank=3,
                    queue_rank=3,
                    market_slug="gamma-watch",
                    source_action="recommend",
                    decision="skipped",
                    queue_status="watch",
                    research_status="watch",
                    recommendation_score=Decimal("0.400000"),
                    readiness_score=Decimal("0.600000"),
                    suggested_notional=Decimal("0.750000"),
                    selected_position_notional=Decimal("0.000000"),
                    primary_reason_code="readiness_watch",
                    reason_codes=("readiness_watch",),
                ),
            ),
        )
        r1 = _make_queue_report_from_rows(
            generated_at=t1,
            rows=(
                _research_row(
                    research_rank=1,
                    queue_rank=1,
                    market_slug="delta-selected",
                    source_action="recommend",
                    decision="selected",
                    queue_status="ready",
                    research_status="ready",
                    recommendation_score=Decimal("0.800000"),
                    readiness_score=Decimal("0.900000"),
                    suggested_notional=Decimal("5.500000"),
                    selected_position_notional=Decimal("5.500000"),
                    primary_reason_code="recommendation_ready",
                    reason_codes=("recommendation_ready",),
                ),
                _research_row(
                    research_rank=2,
                    queue_rank=2,
                    market_slug="epsilon-ready",
                    source_action="recommend",
                    decision="skipped",
                    queue_status="ready",
                    research_status="ready",
                    recommendation_score=Decimal("0.600000"),
                    readiness_score=Decimal("0.750000"),
                    suggested_notional=Decimal("11.250000"),
                    selected_position_notional=Decimal("0.000000"),
                    primary_reason_code="capacity_watch",
                    reason_codes=("capacity_watch",),
                ),
                _research_row(
                    research_rank=3,
                    queue_rank=3,
                    market_slug="zeta-watch",
                    source_action="recommend",
                    decision="skipped",
                    queue_status="watch",
                    research_status="watch",
                    recommendation_score=Decimal("0.500000"),
                    readiness_score=Decimal("0.500000"),
                    suggested_notional=Decimal("2.000000"),
                    selected_position_notional=Decimal("0.000000"),
                    primary_reason_code="readiness_watch",
                    reason_codes=("readiness_watch",),
                ),
            ),
        )
        h = build_paper_strategy_candidate_research_queue_history_report(
            [r0, r1], generated_at=t1,
        )
        assert h.total_ready_notional == Decimal("27.000000")
        assert h.ready_notional_delta == Decimal("6.500000")
        assert h.total_selected_notional == Decimal("7.500000")
        assert h.total_suggested_notional == Decimal("29.750000")
        assert h.selected_notional_delta == Decimal("3.500000")

    def test_reports_sorted_by_generated_at(self) -> None:
        t0 = datetime(2025, 1, 1, tzinfo=UTC)
        t1 = datetime(2025, 1, 2, tzinfo=UTC)
        r0 = _make_queue_report(generated_at=t0, action_status="blocked")
        r1 = _make_queue_report(generated_at=t1, action_status="watch")
        # Pass in reverse order - should be sorted
        h = build_paper_strategy_candidate_research_queue_history_report(
            [r1, r0], generated_at=t1,
        )
        assert h.first_source_generated_at == t0
        assert h.last_source_generated_at == t1
        assert h.latest_action_status == "watch"
        assert h.status_transition_count == 1

    def test_rejects_duplicate_source_history_sort_keys(self) -> None:
        t0 = datetime(2025, 1, 1, tzinfo=UTC)
        r0 = _make_queue_report(
            generated_at=t0,
            action_status="watch",
        )
        r1 = _make_queue_report(
            generated_at=t0,
            action_status="blocked",
        )

        with pytest.raises(
            ValueError,
            match="duplicate.*generated_at.*config|duplicate.*config.*generated_at",
        ):
            build_paper_strategy_candidate_research_queue_history_report(
                [r0, r1], generated_at=t0,
            )


class TestValidation:
    def test_rejects_non_iterable(self) -> None:
        with pytest.raises(ValueError, match="iterable"):
            build_paper_strategy_candidate_research_queue_history_report(
                "not a list", generated_at=datetime.now(UTC),  # type: ignore[arg-type]
            )

    def test_rejects_non_report_items(self) -> None:
        with pytest.raises(ValueError, match="PaperStrategyCandidateResearchQueueReport"):
            build_paper_strategy_candidate_research_queue_history_report(
                [42], generated_at=datetime.now(UTC),  # type: ignore[list-item]
            )

    def test_rejects_non_datetime_generated_at(self) -> None:
        with pytest.raises(ValueError, match="datetime"):
            build_paper_strategy_candidate_research_queue_history_report(
                [], generated_at="not-a-datetime",  # type: ignore[arg-type]
            )

    def test_hard_flags_enforced(self) -> None:
        r = build_paper_strategy_candidate_research_queue_history_report(
            [], generated_at=datetime.now(UTC),
        )
        assert r.paper_only is True
        assert r.report_only is True
        assert r.readonly is True

    def test_rejects_paper_only_false(self) -> None:
        with pytest.raises(ValueError, match="paper_only"):
            PaperStrategyCandidateResearchQueueHistoryReport(
                generated_at=datetime.now(UTC),
                source_report_count=0,
                first_source_generated_at=None,
                last_source_generated_at=None,
                action_status_research_ready_count=0,
                action_status_watch_count=0,
                action_status_blocked_count=0,
                research_status_ready_count=0,
                research_status_watch_count=0,
                research_status_blocked_count=0,
                total_ready_notional=Decimal("0"),
                total_selected_notional=Decimal("0"),
                total_suggested_notional=Decimal("0"),
                latest_action_status=None,
                latest_recommended_next_step=None,
                latest_research_status=None,
                latest_top_research_priority_score=None,
                latest_average_research_ready_score=None,
                status_transition_count=0,
                ready_notional_delta=Decimal("0"),
                selected_notional_delta=Decimal("0"),
                latest_selected_count=0,
                latest_skipped_count=0,
                latest_not_selected_count=0,
                latest_primary_reason_code_counts=(),
                latest_reason_codes=(),
                paper_only=False,
            )

    def test_action_status_count_mismatch_raises(self) -> None:
        t0 = datetime(2025, 1, 1, tzinfo=UTC)
        with pytest.raises(ValueError, match="action status counts"):
            PaperStrategyCandidateResearchQueueHistoryReport(
                generated_at=t0,
                source_report_count=1,
                first_source_generated_at=t0,
                last_source_generated_at=t0,
                action_status_research_ready_count=2,
                action_status_watch_count=0,
                action_status_blocked_count=0,
                research_status_ready_count=1,
                research_status_watch_count=0,
                research_status_blocked_count=0,
                total_ready_notional=Decimal("0"),
                total_selected_notional=Decimal("0"),
                total_suggested_notional=Decimal("0"),
                latest_action_status="watch",
                latest_recommended_next_step="await_fresh_cycle_evidence",
                latest_research_status="watch",
                latest_top_research_priority_score=Decimal("0"),
                latest_average_research_ready_score=Decimal("0"),
                status_transition_count=0,
                ready_notional_delta=Decimal("0"),
                selected_notional_delta=Decimal("0"),
                latest_selected_count=0,
                latest_skipped_count=0,
                latest_not_selected_count=0,
                latest_primary_reason_code_counts=(),
                latest_reason_codes=(),
            )

    def test_research_status_count_mismatch_raises(self) -> None:
        t0 = datetime(2025, 1, 1, tzinfo=UTC)
        with pytest.raises(ValueError, match="research status counts"):
            PaperStrategyCandidateResearchQueueHistoryReport(
                generated_at=t0,
                source_report_count=1,
                first_source_generated_at=t0,
                last_source_generated_at=t0,
                action_status_research_ready_count=0,
                action_status_watch_count=1,
                action_status_blocked_count=0,
                research_status_ready_count=2,
                research_status_watch_count=0,
                research_status_blocked_count=0,
                total_ready_notional=Decimal("0"),
                total_selected_notional=Decimal("0"),
                total_suggested_notional=Decimal("0"),
                latest_action_status="watch",
                latest_recommended_next_step="await_fresh_cycle_evidence",
                latest_research_status="watch",
                latest_top_research_priority_score=Decimal("0"),
                latest_average_research_ready_score=Decimal("0"),
                status_transition_count=0,
                ready_notional_delta=Decimal("0"),
                selected_notional_delta=Decimal("0"),
                latest_selected_count=0,
                latest_skipped_count=0,
                latest_not_selected_count=0,
                latest_primary_reason_code_counts=(),
                latest_reason_codes=(),
            )

    def test_nonempty_direct_report_requires_latest_top_research_priority_score(self) -> None:
        with pytest.raises(ValueError, match="latest_top_research_priority_score"):
            PaperStrategyCandidateResearchQueueHistoryReport(
                **_history_report_kwargs(latest_top_research_priority_score=None),
            )

    def test_nonempty_direct_report_requires_latest_average_research_ready_score(self) -> None:
        with pytest.raises(ValueError, match="latest_average_research_ready_score"):
            PaperStrategyCandidateResearchQueueHistoryReport(
                **_history_report_kwargs(latest_average_research_ready_score=None),
            )

    def test_latest_action_status_must_be_represented_by_status_count(self) -> None:
        with pytest.raises(ValueError, match="latest_action_status"):
            PaperStrategyCandidateResearchQueueHistoryReport(
                **_history_report_kwargs(
                    action_status_watch_count=0,
                    action_status_blocked_count=1,
                ),
            )

    def test_latest_research_status_must_be_represented_by_status_count(self) -> None:
        with pytest.raises(ValueError, match="latest_research_status"):
            PaperStrategyCandidateResearchQueueHistoryReport(
                **_history_report_kwargs(
                    research_status_watch_count=0,
                    research_status_ready_count=1,
                ),
            )

    def test_rejects_duplicate_latest_primary_reason_code_count_rows(self) -> None:
        with pytest.raises(
            ValueError,
            match="duplicate.*latest_primary_reason_code_counts",
        ):
            PaperStrategyCandidateResearchQueueHistoryReport(
                **_history_report_kwargs(
                    latest_primary_reason_code_counts=(
                        ("recommendation_ready", 1),
                        ("recommendation_ready", 2),
                    ),
                ),
            )

    def test_rejects_zero_latest_primary_reason_code_counts(self) -> None:
        with pytest.raises(ValueError, match="latest_primary_reason_code_counts.*positive"):
            PaperStrategyCandidateResearchQueueHistoryReport(
                **_history_report_kwargs(
                    latest_primary_reason_code_counts=(("recommendation_ready", 0),),
                ),
            )

    def test_latest_reason_codes_are_deduped_on_direct_construction(self) -> None:
        report = PaperStrategyCandidateResearchQueueHistoryReport(
            **_history_report_kwargs(
                latest_reason_codes=(
                    "source_action_status_watch",
                    "cycle_review_watch",
                    "source_action_status_watch",
                ),
            ),
        )

        assert report.latest_reason_codes == (
            "source_action_status_watch",
            "cycle_review_watch",
        )
