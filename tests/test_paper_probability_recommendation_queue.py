from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_probability_recommendation_queue import (
    PaperProbabilityRecommendationQueueConfig,
    PaperProbabilityRecommendationQueueReport,
    PaperProbabilityRecommendationQueueRow,
    build_paper_probability_recommendation_queue_report,
)
from polymarket_alpha_lab.paper_probability_side_edge import (
    PaperProbabilitySideEdgeRow,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def side_edge_row(
    market_slug: str,
    *,
    question: str | None = None,
    side: str = "yes",
    side_probability: Decimal = d("0.700000"),
    market_implied_probability: Decimal = d("0.600000"),
    total_cost_per_share: Decimal = d("0.010000"),
    recommendation_score: Decimal | None = None,
    action: str = "recommend",
    depth_status: str | None = None,
    requested_paper_shares: Decimal = d("100.000000"),
    max_executable_shares: Decimal = d("100.000000"),
    reason_codes: tuple[str, ...] = ("source_reason",),
) -> PaperProbabilitySideEdgeRow:
    gross_probability_edge = side_probability - market_implied_probability
    net_probability_edge = gross_probability_edge - total_cost_per_share
    executable_paper_shares = min(requested_paper_shares, max_executable_shares)
    if requested_paper_shares <= ZERO or max_executable_shares <= ZERO:
        executable_paper_shares = ZERO
        inferred_depth_status = "no_depth"
    elif max_executable_shares < requested_paper_shares:
        inferred_depth_status = "partial_depth"
    else:
        inferred_depth_status = "sufficient_depth"
    if recommendation_score is None:
        recommendation_score = net_probability_edge if action != "reject" else ZERO
    return PaperProbabilitySideEdgeRow(
        market_slug=market_slug,
        question=question or f"Will {market_slug} resolve yes?",
        side=side,
        side_probability=side_probability,
        market_implied_probability=market_implied_probability,
        gross_probability_edge=gross_probability_edge,
        total_cost_per_share=total_cost_per_share,
        net_probability_edge=net_probability_edge,
        recommendation_score=recommendation_score,
        action=action,
        depth_status=depth_status or inferred_depth_status,
        requested_paper_shares=requested_paper_shares,
        max_executable_shares=max_executable_shares,
        executable_paper_shares=executable_paper_shares,
        reason_codes=reason_codes,
    )


def config(
    *,
    max_queue_rows: int = 3,
    min_recommendation_score: Decimal = d("0.050000"),
    include_watch: bool = True,
) -> PaperProbabilityRecommendationQueueConfig:
    return PaperProbabilityRecommendationQueueConfig(
        config_version="probability-recommendation-queue-v0",
        max_queue_rows=max_queue_rows,
        min_recommendation_score=min_recommendation_score,
        include_watch=include_watch,
    )


def build_queue(
    rows: tuple[PaperProbabilitySideEdgeRow, ...],
    *,
    queue_config: PaperProbabilityRecommendationQueueConfig | None = None,
) -> PaperProbabilityRecommendationQueueReport:
    return build_paper_probability_recommendation_queue_report(
        rows,
        config=queue_config or config(),
        generated_at=GENERATED_AT,
    )


def test_queue_ranks_recommendations_before_watch_and_skips_rejects():
    report = build_queue(
        (
            side_edge_row(
                "beta-watch",
                side_probability=d("0.640000"),
                market_implied_probability=d("0.600000"),
                total_cost_per_share=d("0.010000"),
                recommendation_score=d("0.030000"),
                action="watch",
                reason_codes=("below_min_net_probability_edge",),
            ),
            side_edge_row(
                "zeta-recommend-low",
                side_probability=d("0.680000"),
                market_implied_probability=d("0.600000"),
                total_cost_per_share=d("0.010000"),
                recommendation_score=d("0.070000"),
                action="recommend",
                reason_codes=("lower_score",),
            ),
            side_edge_row(
                "alpha-recommend-high",
                side_probability=d("0.740000"),
                market_implied_probability=d("0.600000"),
                total_cost_per_share=d("0.010000"),
                recommendation_score=d("0.130000"),
                action="recommend",
                reason_codes=("higher_score",),
            ),
            side_edge_row(
                "delta-reject",
                side_probability=d("0.520000"),
                market_implied_probability=d("0.600000"),
                total_cost_per_share=d("0.010000"),
                action="reject",
                reason_codes=("nonpositive_net_probability_edge",),
            ),
        ),
    )

    assert isinstance(report, PaperProbabilityRecommendationQueueReport)
    assert report.generated_at == GENERATED_AT
    assert report.source_config_version == "probability-recommendation-queue-v0"
    assert report.input_count == 4
    assert report.queue_count == 3
    assert report.research_review_count == 2
    assert report.await_fresh_context_count == 1
    assert report.skip_count == 0
    assert report.excluded_count == 1
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_slug for row in report.queue_rows) == (
        "alpha-recommend-high",
        "zeta-recommend-low",
        "beta-watch",
    )
    assert tuple(row.queue_rank for row in report.queue_rows) == (1, 2, 3)
    assert tuple(row.review_priority for row in report.queue_rows) == (
        "research_review",
        "research_review",
        "watch",
    )
    assert tuple(row.recommended_next_step for row in report.queue_rows) == (
        "research_review",
        "research_review",
        "await_fresh_context",
    )
    assert "higher_score" in report.queue_rows[0].reason_codes
    assert "below_min_net_probability_edge" in report.queue_rows[2].reason_codes


def test_queue_excludes_watch_unless_requested_and_uses_deterministic_tie_breakers():
    rows = (
        side_edge_row(
            "gamma-equal",
            side_probability=d("0.700000"),
            market_implied_probability=d("0.630000"),
            total_cost_per_share=d("0.010000"),
            requested_paper_shares=d("100.000000"),
            max_executable_shares=d("20.000000"),
            reason_codes=("same_score",),
        ),
        side_edge_row(
            "alpha-equal",
            side_probability=d("0.700000"),
            market_implied_probability=d("0.630000"),
            total_cost_per_share=d("0.010000"),
            requested_paper_shares=d("100.000000"),
            max_executable_shares=d("80.000000"),
            reason_codes=("same_score",),
        ),
        side_edge_row(
            "beta-equal",
            side_probability=d("0.700000"),
            market_implied_probability=d("0.630000"),
            total_cost_per_share=d("0.010000"),
            requested_paper_shares=d("100.000000"),
            max_executable_shares=d("80.000000"),
            reason_codes=("same_score",),
        ),
        side_edge_row(
            "delta-watch",
            side_probability=d("0.660000"),
            market_implied_probability=d("0.630000"),
            total_cost_per_share=d("0.010000"),
            action="watch",
            recommendation_score=d("0.020000"),
            reason_codes=("below_min_net_probability_edge",),
        ),
    )

    report = build_queue(rows, queue_config=config(max_queue_rows=4, include_watch=False))

    assert tuple(row.market_slug for row in report.queue_rows) == (
        "alpha-equal",
        "beta-equal",
        "gamma-equal",
    )
    assert report.excluded_count == 1
    assert all(row.recommended_next_step == "research_review" for row in report.queue_rows)


def test_queue_fills_remaining_capacity_with_skipped_rejects_after_watch():
    report = build_queue(
        (
            side_edge_row(
                "alpha-recommend",
                side_probability=d("0.740000"),
                market_implied_probability=d("0.600000"),
                total_cost_per_share=d("0.010000"),
                reason_codes=("strong_edge",),
            ),
            side_edge_row(
                "beta-watch",
                side_probability=d("0.640000"),
                market_implied_probability=d("0.600000"),
                total_cost_per_share=d("0.010000"),
                recommendation_score=d("0.030000"),
                action="watch",
                reason_codes=("below_min_net_probability_edge",),
            ),
            side_edge_row(
                "delta-reject",
                side_probability=d("0.520000"),
                market_implied_probability=d("0.600000"),
                total_cost_per_share=d("0.010000"),
                action="reject",
                reason_codes=("nonpositive_net_probability_edge",),
            ),
        ),
        queue_config=config(max_queue_rows=5, include_watch=True),
    )

    assert tuple(row.market_slug for row in report.queue_rows) == (
        "alpha-recommend",
        "beta-watch",
        "delta-reject",
    )
    assert tuple(row.recommended_next_step for row in report.queue_rows) == (
        "research_review",
        "await_fresh_context",
        "skip",
    )
    assert tuple(row.review_priority for row in report.queue_rows) == (
        "research_review",
        "watch",
        "skip",
    )
    assert report.skip_count == 1
    assert report.excluded_count == 0


def test_queue_accepts_empty_input_and_normalizes_generated_at_to_utc():
    eastern = timezone(timedelta(hours=-4))

    report = build_paper_probability_recommendation_queue_report(
        (),
        config=config(max_queue_rows=5),
        generated_at=datetime(2026, 6, 19, 8, 30, tzinfo=eastern),
    )

    assert report.generated_at == GENERATED_AT
    assert report.input_count == 0
    assert report.queue_count == 0
    assert report.research_review_count == 0
    assert report.await_fresh_context_count == 0
    assert report.skip_count == 0
    assert report.excluded_count == 0
    assert report.queue_rows == ()


def test_queue_dataclasses_are_frozen_and_validate_invariants():
    report = build_queue(
        (
            side_edge_row(
                "alpha-recommend",
                side_probability=d("0.740000"),
                market_implied_probability=d("0.600000"),
                total_cost_per_share=d("0.010000"),
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.queue_count = 0
    with pytest.raises(FrozenInstanceError):
        report.queue_rows[0].queue_rank = 0
    with pytest.raises(ValueError, match="queue_count"):
        replace(report, queue_count=99)
    with pytest.raises(ValueError, match="queue_rank"):
        replace(report.queue_rows[0], queue_rank=0)
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(report.queue_rows[0], recommended_next_step="skip")
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)


def test_queue_quantizes_decimal_fields_and_rejects_non_decimal_values():
    report = build_queue(
        (
            side_edge_row(
                "alpha-quantized",
                side_probability=d("0.7000004"),
                market_implied_probability=d("0.6000001"),
                total_cost_per_share=d("0.0100001"),
                requested_paper_shares=d("100.0000004"),
                max_executable_shares=d("80.0000004"),
            ),
        ),
    )

    row = report.queue_rows[0]
    assert row.recommendation_score == d("0.090000")
    assert row.net_probability_edge == d("0.090000")
    assert row.total_cost_per_share == d("0.010000")
    assert row.executable_paper_shares == d("80.000000")

    with pytest.raises(ValueError, match="min_recommendation_score"):
        PaperProbabilityRecommendationQueueConfig(
            config_version="probability-recommendation-queue-v0",
            max_queue_rows=3,
            min_recommendation_score=0.05,
            include_watch=True,
        )
    with pytest.raises(ValueError, match="recommendation_score"):
        PaperProbabilityRecommendationQueueRow(
            queue_rank=1,
            market_slug="alpha-row",
            question="Will alpha resolve yes?",
            side="yes",
            action="recommend",
            recommendation_score="0.100000",
            net_probability_edge=d("0.100000"),
            total_cost_per_share=d("0.010000"),
            depth_status="sufficient_depth",
            executable_paper_shares=d("100.000000"),
            review_priority="research_review",
            recommended_next_step="research_review",
            reason_codes=("source_reason",),
        )


def test_queue_rejects_unsafe_inputs_and_config():
    good_row = side_edge_row(
        "alpha-recommend",
        side_probability=d("0.740000"),
        market_implied_probability=d("0.600000"),
        total_cost_per_share=d("0.010000"),
    )

    with pytest.raises(ValueError, match="config"):
        build_paper_probability_recommendation_queue_report(
            (good_row,),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_probability_recommendation_queue_report(
            (good_row,),
            config=config(),
            generated_at="2026-06-19T12:30:00Z",
        )
    with pytest.raises(ValueError, match="inputs"):
        build_paper_probability_recommendation_queue_report(
            (object(),),
            config=config(),
            generated_at=GENERATED_AT,
        )

    unsafe_row = side_edge_row(
        "unsafe-row",
        side_probability=d("0.740000"),
        market_implied_probability=d("0.600000"),
        total_cost_per_share=d("0.010000"),
    )
    object.__setattr__(unsafe_row, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        build_queue((unsafe_row,))

    unsafe_config = config()
    object.__setattr__(unsafe_config, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        build_paper_probability_recommendation_queue_report(
            (good_row,),
            config=unsafe_config,
            generated_at=GENERATED_AT,
        )
