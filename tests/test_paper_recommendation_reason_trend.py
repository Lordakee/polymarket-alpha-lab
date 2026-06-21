from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_probability_recommendation_queue import (
    PaperProbabilityRecommendationQueueConfig,
    PaperProbabilityRecommendationQueueReport,
    build_paper_probability_recommendation_queue_report,
)
from polymarket_alpha_lab.paper_probability_side_edge import PaperProbabilitySideEdgeRow
from polymarket_alpha_lab.paper_recommendation_allocation import (
    PaperRecommendationAllocationReport,
    PaperRecommendationAllocationRow,
)
from polymarket_alpha_lab.paper_recommendation_reason_trend import (
    PaperRecommendationReasonTrendConfig,
    PaperRecommendationReasonTrendReport,
    PaperRecommendationReasonTrendRow,
    PaperRecommendationTransitionTrendRow,
    build_paper_recommendation_reason_trend_report,
)


GENERATED_AT = datetime(2026, 6, 19, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


@dataclass(frozen=True)
class QueueStatusRowShape:
    market_slug: str
    side: str
    queue_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class QueueStatusReportShape:
    generated_at: datetime
    config_version: str
    row_count: int
    queued_count: int
    deferred_count: int
    blocked_count: int
    queue_rows: tuple[QueueStatusRowShape, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class ActionRowShape:
    market_slug: str
    side: str
    action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class ActionReportShape:
    generated_at: datetime
    rows: tuple[ActionRowShape, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> PaperRecommendationReasonTrendConfig:
    values = {
        "config_version": "paper-recommendation-reason-trend-v0",
        "window_size": 10,
    }
    values.update(overrides)
    return PaperRecommendationReasonTrendConfig(**values)


def _side_edge_row(
    market_slug: str,
    *,
    side: str = "yes",
    action: str = "recommend",
    recommendation_score: Decimal | None = None,
    reason_codes: tuple[str, ...] = ("source_reason",),
) -> PaperProbabilitySideEdgeRow:
    side_probability = d("0.700000")
    market_implied_probability = d("0.600000")
    total_cost_per_share = d("0.010000")
    gross_probability_edge = side_probability - market_implied_probability
    net_probability_edge = gross_probability_edge - total_cost_per_share
    if recommendation_score is None:
        if action == "recommend":
            recommendation_score = d("0.090000")
        elif action == "watch":
            recommendation_score = ZERO
        else:
            recommendation_score = ZERO
    depth_status = "no_depth" if action == "reject" else "sufficient_depth"
    executable_paper_shares = ZERO if action == "reject" else d("100.000000")
    return PaperProbabilitySideEdgeRow(
        market_slug=market_slug,
        question=f"Will {market_slug} resolve yes?",
        side=side,
        side_probability=side_probability,
        market_implied_probability=market_implied_probability,
        gross_probability_edge=gross_probability_edge,
        total_cost_per_share=total_cost_per_share,
        net_probability_edge=net_probability_edge,
        recommendation_score=recommendation_score,
        action=action,
        depth_status=depth_status,
        requested_paper_shares=d("100.000000"),
        max_executable_shares=executable_paper_shares,
        executable_paper_shares=executable_paper_shares,
        reason_codes=reason_codes,
    )


def _action_report(
    *rows: PaperProbabilitySideEdgeRow,
    generated_at: datetime,
) -> PaperProbabilityRecommendationQueueReport:
    return build_paper_probability_recommendation_queue_report(
        rows,
        config=PaperProbabilityRecommendationQueueConfig(
            config_version="probability-recommendation-queue-v0",
            max_queue_rows=100,
            min_recommendation_score=d("0.050000"),
            include_watch=True,
        ),
        generated_at=generated_at,
    )


def _queue_status_row(
    market_slug: str,
    *,
    side: str = "yes",
    queue_status: str,
    reason_codes: tuple[str, ...],
) -> QueueStatusRowShape:
    return QueueStatusRowShape(
        market_slug=market_slug,
        side=side,
        queue_status=queue_status,
        reason_codes=reason_codes,
    )


def _queue_status_report(
    *rows: QueueStatusRowShape,
    generated_at: datetime,
) -> QueueStatusReportShape:
    return QueueStatusReportShape(
        generated_at=generated_at,
        config_version="paper-recommendation-queue-v0",
        row_count=len(rows),
        queued_count=sum(1 for row in rows if row.queue_status == "queued"),
        deferred_count=sum(1 for row in rows if row.queue_status == "deferred"),
        blocked_count=sum(1 for row in rows if row.queue_status == "blocked"),
        queue_rows=rows,
    )


def _allocation_row(
    market_slug: str,
    *,
    side: str = "yes",
    source_status: str = "allocated",
    reason_codes: tuple[str, ...],
) -> PaperRecommendationAllocationRow:
    allocated = source_status == "allocated"
    allocated_notional = ONE if allocated else ZERO
    allocated_shares = ONE if allocated else ZERO
    recommendation_score = d("0.100000") if allocated else ZERO
    return PaperRecommendationAllocationRow(
        market_slug=market_slug,
        side=side,
        action="recommend",
        recommendation_score=recommendation_score,
        net_probability_edge=recommendation_score,
        executable_paper_shares=ONE,
        side_price=ONE,
        market_implied_probability=ONE,
        event_id=None,
        theme_id=None,
        correlation_group=None,
        requested_paper_notional=ONE,
        allocated_paper_notional=allocated_notional,
        allocated_paper_shares=allocated_shares,
        cap_status="allocated" if allocated else "skipped",
        reason_codes=reason_codes,
    )


def _allocation_report(
    *rows: PaperRecommendationAllocationRow,
    generated_at: datetime,
) -> PaperRecommendationAllocationReport:
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                -(row.recommendation_score or ZERO),
                -(row.net_probability_edge or ZERO),
                -row.executable_paper_shares,
                row.market_slug,
                row.side,
            ),
        ),
    )
    total_requested = sum(
        (row.requested_paper_notional for row in sorted_rows),
        ZERO,
    )
    total_allocated = sum(
        (row.allocated_paper_notional for row in sorted_rows),
        ZERO,
    )
    total_budget = d("1000.000000")
    return PaperRecommendationAllocationReport(
        generated_at=generated_at,
        config_version="allocation-v0",
        input_count=len(sorted_rows),
        row_count=len(sorted_rows),
        allocated_count=sum(1 for row in sorted_rows if row.cap_status == "allocated"),
        capped_count=sum(1 for row in sorted_rows if row.cap_status == "capped"),
        no_budget_count=sum(1 for row in sorted_rows if row.cap_status == "no_budget"),
        non_recommend_count=sum(
            1 for row in sorted_rows if row.cap_status == "non_recommend"
        ),
        skipped_count=sum(1 for row in sorted_rows if row.cap_status == "skipped"),
        total_requested_paper_notional=total_requested,
        total_allocated_paper_notional=total_allocated,
        remaining_paper_budget=total_budget - total_allocated,
        total_paper_budget=total_budget,
        max_paper_notional_per_market=total_budget,
        max_paper_notional_per_event=total_budget,
        max_paper_notional_per_theme=total_budget,
        max_paper_notional_per_correlation_group=total_budget,
        rows=sorted_rows,
    )


def _trend(
    *reports: object,
    config: PaperRecommendationReasonTrendConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperRecommendationReasonTrendReport:
    return build_paper_recommendation_reason_trend_report(
        reports,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_reason_trend_counts_reason_codes_by_status_across_recovered_reports():
    first = _action_report(
        _side_edge_row(
            "alpha-recommend-one",
            action="recommend",
            reason_codes=("alpha_recommend",),
        ),
        _side_edge_row(
            "bravo-watch-one",
            action="watch",
            reason_codes=("bravo_watch",),
        ),
        _side_edge_row(
            "charlie-reject-one",
            action="reject",
            reason_codes=("charlie_reject",),
        ),
        generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
    )
    second = _action_report(
        _side_edge_row(
            "alpha-recommend-two",
            action="recommend",
            reason_codes=("alpha_recommend",),
        ),
        _side_edge_row(
            "bravo-watch-two",
            action="watch",
            reason_codes=("bravo_watch",),
        ),
        _side_edge_row(
            "charlie-reject-two",
            action="reject",
            reason_codes=("charlie_reject",),
        ),
        generated_at=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
    )
    third = _action_report(
        _side_edge_row(
            "alpha-recommend-three",
            action="recommend",
            reason_codes=("alpha_recommend",),
        ),
        generated_at=datetime(2026, 6, 19, 11, 0, tzinfo=UTC),
    )
    queued = _queue_status_report(
        _queue_status_row(
            "delta-queued",
            queue_status="queued",
            reason_codes=("delta_queued",),
        ),
        _queue_status_row(
            "echo-deferred",
            queue_status="deferred",
            reason_codes=("echo_deferred",),
        ),
        _queue_status_row(
            "foxtrot-blocked",
            queue_status="blocked",
            reason_codes=("foxtrot_blocked",),
        ),
        generated_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
    )
    allocated = _allocation_report(
        _allocation_row(
            "golf-allocated",
            source_status="allocated",
            reason_codes=("golf_allocated",),
        ),
        _allocation_row(
            "hotel-zero",
            source_status="zero",
            reason_codes=("skipped",),
        ),
        generated_at=datetime(2026, 6, 19, 13, 0, tzinfo=UTC),
    )

    report = _trend(first, second, third, queued, allocated)

    assert isinstance(report, PaperRecommendationReasonTrendReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-recommendation-reason-trend-v0"
    assert report.source_report_count == 5
    assert tuple(
        (
            row.reason_code,
            row.source_status,
            row.count,
            row.first_seen_at,
            row.latest_seen_at,
        )
        for row in report.reason_trend_rows
    ) == (
        (
            "alpha_recommend",
            "recommend",
            3,
            first.generated_at,
            third.generated_at,
        ),
        ("bravo_watch", "watch", 2, first.generated_at, second.generated_at),
        ("charlie_reject", "reject", 2, first.generated_at, second.generated_at),
        ("delta_queued", "queued", 1, queued.generated_at, queued.generated_at),
        ("echo_deferred", "deferred", 1, queued.generated_at, queued.generated_at),
        ("foxtrot_blocked", "blocked", 1, queued.generated_at, queued.generated_at),
        (
            "golf_allocated",
            "allocated",
            1,
            allocated.generated_at,
            allocated.generated_at,
        ),
        ("skipped", "zero", 1, allocated.generated_at, allocated.generated_at),
    )
    assert all(
        isinstance(row, PaperRecommendationReasonTrendRow)
        for row in report.reason_trend_rows
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_reason_trend_tracks_market_side_status_transitions_across_runs():
    action_before = _action_report(
        _side_edge_row(
            "watch-to-recommend",
            action="watch",
            side="yes",
            reason_codes=("watch_to_recommend",),
        ),
        _side_edge_row(
            "recommend-to-watch",
            action="recommend",
            side="no",
            reason_codes=("recommend_to_watch",),
        ),
        _side_edge_row(
            "recommend-to-reject",
            action="recommend",
            side="yes",
            reason_codes=("recommend_to_reject",),
        ),
        generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
    )
    action_after = _action_report(
        _side_edge_row(
            "watch-to-recommend",
            action="recommend",
            side="yes",
            reason_codes=("watch_to_recommend",),
        ),
        _side_edge_row(
            "recommend-to-watch",
            action="watch",
            side="no",
            reason_codes=("recommend_to_watch",),
        ),
        _side_edge_row(
            "recommend-to-reject",
            action="reject",
            side="yes",
            reason_codes=("recommend_to_reject",),
        ),
        generated_at=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
    )
    queued_before = _queue_status_report(
        _queue_status_row(
            "queued-to-blocked",
            queue_status="queued",
            side="yes",
            reason_codes=("queued_to_blocked",),
        ),
        generated_at=datetime(2026, 6, 19, 11, 0, tzinfo=UTC),
    )
    queued_after = _queue_status_report(
        _queue_status_row(
            "queued-to-blocked",
            queue_status="blocked",
            side="yes",
            reason_codes=("queued_to_blocked",),
        ),
        generated_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
    )
    allocated_before = _allocation_report(
        _allocation_row(
            "allocated-to-zero",
            side="no",
            source_status="allocated",
            reason_codes=("allocated_to_zero", "skipped"),
        ),
        generated_at=datetime(2026, 6, 19, 13, 0, tzinfo=UTC),
    )
    allocated_after = _allocation_report(
        _allocation_row(
            "allocated-to-zero",
            side="no",
            source_status="zero",
            reason_codes=("allocated_to_zero", "skipped"),
        ),
        generated_at=datetime(2026, 6, 19, 14, 0, tzinfo=UTC),
    )

    report = _trend(
        action_before,
        action_after,
        queued_before,
        queued_after,
        allocated_before,
        allocated_after,
    )

    transitions = {
        (row.market_slug, row.side, row.from_status, row.to_status): row
        for row in report.transition_trend_rows
    }
    assert set(transitions) == {
        ("watch-to-recommend", "yes", "watch", "recommend"),
        ("recommend-to-watch", "no", "recommend", "watch"),
        ("recommend-to-reject", "yes", "recommend", "reject"),
        ("queued-to-blocked", "yes", "queued", "blocked"),
        ("allocated-to-zero", "no", "allocated", "zero"),
    }
    assert transitions[
        ("watch-to-recommend", "yes", "watch", "recommend")
    ].latest_transition_at == action_after.generated_at
    assert transitions[
        ("recommend-to-watch", "no", "recommend", "watch")
    ].reason_codes == ("recommend_to_watch",)
    assert transitions[
        ("recommend-to-reject", "yes", "recommend", "reject")
    ].transition_count == 1
    assert transitions[
        ("queued-to-blocked", "yes", "queued", "blocked")
    ].latest_transition_at == queued_after.generated_at
    assert transitions[
        ("allocated-to-zero", "no", "allocated", "zero")
    ].reason_codes == ("allocated_to_zero", "skipped")
    assert all(
        isinstance(row, PaperRecommendationTransitionTrendRow)
        for row in report.transition_trend_rows
    )


def test_reason_trend_accepts_none_side_and_rejects_invalid_side():
    none_before = ActionReportShape(
        generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
        rows=(
            ActionRowShape(
                market_slug="none-side-transition",
                side="none",
                action="watch",
                reason_codes=("none_side_watch",),
            ),
        ),
    )
    none_after = ActionReportShape(
        generated_at=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        rows=(
            ActionRowShape(
                market_slug="none-side-transition",
                side="none",
                action="reject",
                reason_codes=("none_side_reject",),
            ),
        ),
    )

    report = _trend(none_before, none_after)

    assert tuple(
        (
            row.market_slug,
            row.side,
            row.from_status,
            row.to_status,
            row.reason_codes,
        )
        for row in report.transition_trend_rows
    ) == (
        (
            "none-side-transition",
            "none",
            "watch",
            "reject",
            ("none_side_reject",),
        ),
    )

    invalid_side = ActionReportShape(
        generated_at=datetime(2026, 6, 19, 11, 0, tzinfo=UTC),
        rows=(
            ActionRowShape(
                market_slug="invalid-side",
                side="both",
                action="watch",
                reason_codes=("invalid_side",),
            ),
        ),
    )
    with pytest.raises(ValueError, match="yes, no, or none"):
        _trend(invalid_side)


def test_reason_trend_rejects_free_form_noncanonical_reason_strings():
    source = _action_report(
        _side_edge_row(
            "noncanonical-source",
            action="recommend",
            reason_codes=("canonical_reason",),
        ),
        generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
    )
    object.__setattr__(
        source.queue_rows[0],
        "reason_codes",
        ("free form reason",),
    )

    with pytest.raises(ValueError, match="canonical"):
        _trend(source)

    with pytest.raises(ValueError, match="canonical"):
        PaperRecommendationReasonTrendRow(
            reason_code="free form reason",
            source_status="recommend",
            count=1,
            first_seen_at=GENERATED_AT,
            latest_seen_at=GENERATED_AT,
        )


def test_reason_trend_rejects_unsafe_source_report_flags():
    for flag_name in ("paper_only", "report_only", "readonly"):
        source = _action_report(
            _side_edge_row(
                f"unsafe-{flag_name}",
                action="recommend",
                reason_codes=("safe_reason",),
            ),
            generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
        )
        object.__setattr__(source, flag_name, False)

        with pytest.raises(ValueError, match=flag_name):
            _trend(source)


def test_reason_trend_dataclasses_are_frozen_and_revalidate_phase_flags():
    config = _config()
    first = _action_report(
        _side_edge_row(
            "phase-safety",
            action="watch",
            reason_codes=("phase_safety",),
        ),
        generated_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
    )
    second = _action_report(
        _side_edge_row(
            "phase-safety",
            action="recommend",
            reason_codes=("phase_safety",),
        ),
        generated_at=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
    )

    report = _trend(first, second, config=config)
    reason_row = report.reason_trend_rows[0]
    transition_row = report.transition_trend_rows[0]

    assert reason_row.paper_only is True
    assert reason_row.report_only is True
    assert reason_row.readonly is True
    assert transition_row.paper_only is True
    assert transition_row.report_only is True
    assert transition_row.readonly is True

    with pytest.raises(FrozenInstanceError):
        config.window_size = 1  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.source_report_count = 0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_row.count = 99  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        transition_row.transition_count = 99  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(reason_row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(transition_row, readonly=False)
    with pytest.raises(ValueError, match="window_size"):
        PaperRecommendationReasonTrendConfig(
            config_version="paper-recommendation-reason-trend-v0",
            window_size=0,
        )
