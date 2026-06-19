from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_recommendation_health import (
    PaperRecommendationHealthConfig,
    PaperRecommendationHealthInputRow,
    PaperRecommendationHealthReasonCodeCount,
    PaperRecommendationHealthReport,
    build_paper_recommendation_health_report,
)


GENERATED_AT = datetime(2026, 6, 19, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


@dataclass(frozen=True)
class SuppliedRecommendationShape:
    market_slug: str
    side: str
    status: str
    net_probability_edge: Decimal
    total_cost_per_share: Decimal
    recommendation_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    *,
    max_average_cost_per_share: Decimal = d("0.030000"),
    min_recommend_share: Decimal = d("0.500000"),
) -> PaperRecommendationHealthConfig:
    return PaperRecommendationHealthConfig(
        config_version="paper-recommendation-health-v0",
        max_average_cost_per_share=max_average_cost_per_share,
        min_recommend_share=min_recommend_share,
    )


def health_row(
    market_slug: str = "market-alpha",
    *,
    side: str = "yes",
    action: str = "recommend",
    net_probability_edge: Decimal = d("0.0800004"),
    total_cost_per_share: Decimal = d("0.0100004"),
    recommendation_score: Decimal = d("0.0800004"),
    reason_codes: tuple[str, ...] = ("positive_net_edge",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperRecommendationHealthInputRow:
    return PaperRecommendationHealthInputRow(
        market_slug=market_slug,
        side=side,
        action=action,
        net_probability_edge=net_probability_edge,
        total_cost_per_share=total_cost_per_share,
        recommendation_score=recommendation_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: PaperRecommendationHealthConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperRecommendationHealthReport:
    return build_paper_recommendation_health_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_health_report_summarizes_counts_averages_top_score_and_reasons():
    summary = report(
        (
            health_row(
                "beta-watch",
                action="watch",
                net_probability_edge=d("0.0200004"),
                total_cost_per_share=d("0.0400004"),
                recommendation_score=d("0.0200004"),
                reason_codes=("below_min_edge", "wide_spread"),
            ),
            health_row(
                "alpha-recommend",
                net_probability_edge=d("0.0800004"),
                total_cost_per_share=d("0.0100004"),
                recommendation_score=d("0.0800004"),
                reason_codes=("positive_net_edge", "wide_spread"),
            ),
            health_row(
                "gamma-reject",
                action="reject",
                net_probability_edge=d("-0.0300004"),
                total_cost_per_share=d("0.0200004"),
                recommendation_score=d("0.0000004"),
                reason_codes=("nonpositive_net_edge",),
            ),
            health_row(
                "delta-recommend",
                side="no",
                net_probability_edge=d("0.0500004"),
                total_cost_per_share=d("0.0100004"),
                recommendation_score=d("0.0500004"),
                reason_codes=("positive_net_edge",),
            ),
        ),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == "paper-recommendation-health-v0"
    assert summary.row_count == 4
    assert summary.recommend_count == 2
    assert summary.watch_count == 1
    assert summary.reject_count == 1
    assert summary.average_net_probability_edge == d("0.030000")
    assert summary.average_total_cost_per_share == d("0.020000")
    assert summary.top_recommendation_score == d("0.080000")
    assert summary.max_average_cost_per_share == d("0.030000")
    assert summary.min_recommend_share == d("0.500000")
    assert summary.reason_code_counts == (
        PaperRecommendationHealthReasonCodeCount(
            reason_code="positive_net_edge",
            count=2,
        ),
        PaperRecommendationHealthReasonCodeCount(reason_code="wide_spread", count=2),
        PaperRecommendationHealthReasonCodeCount(reason_code="below_min_edge", count=1),
        PaperRecommendationHealthReasonCodeCount(
            reason_code="nonpositive_net_edge",
            count=1,
        ),
    )
    assert summary.health_status == "pass"
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_health_report_accepts_supplied_rows_with_status_instead_of_action():
    summary = report(
        (
            SuppliedRecommendationShape(
                market_slug="market-alpha",
                side="yes",
                status="recommend",
                net_probability_edge=d("0.090000"),
                total_cost_per_share=d("0.010000"),
                recommendation_score=d("0.090000"),
                reason_codes=("supplied_shape",),
            ),
        ),
    )

    assert summary.row_count == 1
    assert summary.recommend_count == 1
    assert summary.health_status == "pass"
    assert summary.reason_code_counts == (
        PaperRecommendationHealthReasonCodeCount(reason_code="supplied_shape", count=1),
    )


def test_health_report_blocks_empty_or_no_recommend_rows():
    empty = report(())
    no_recommend = report(
        (
            health_row("watch-only", action="watch"),
            health_row(
                "reject-only",
                action="reject",
                net_probability_edge=d("-0.020000"),
                recommendation_score=d("0.000000"),
            ),
        ),
    )

    assert empty.row_count == 0
    assert empty.recommend_count == 0
    assert empty.average_net_probability_edge == ZERO
    assert empty.average_total_cost_per_share == ZERO
    assert empty.top_recommendation_score == ZERO
    assert empty.reason_code_counts == ()
    assert empty.health_status == "blocked"

    assert no_recommend.row_count == 2
    assert no_recommend.recommend_count == 0
    assert no_recommend.watch_count == 1
    assert no_recommend.reject_count == 1
    assert no_recommend.health_status == "blocked"


def test_health_report_watches_high_average_cost_or_low_recommend_share():
    high_cost = report(
        (
            health_row("high-cost", total_cost_per_share=d("0.060000")),
            health_row(
                "normal-cost",
                total_cost_per_share=d("0.020000"),
                net_probability_edge=d("0.070000"),
                recommendation_score=d("0.070000"),
            ),
        ),
        cfg=config(max_average_cost_per_share=d("0.030000")),
    )
    low_recommend_share = report(
        (
            health_row("alpha-recommend"),
            health_row("beta-watch", action="watch"),
            health_row(
                "gamma-reject",
                action="reject",
                net_probability_edge=d("-0.010000"),
                recommendation_score=d("0.000000"),
            ),
        ),
        cfg=config(min_recommend_share=d("0.500000")),
    )

    assert high_cost.average_total_cost_per_share == d("0.040000")
    assert high_cost.health_status == "watch"
    assert low_recommend_share.recommend_count == 1
    assert low_recommend_share.health_status == "watch"


def test_health_report_validates_inputs_config_quantization_and_hard_flags():
    with pytest.raises(ValueError, match="config_version"):
        PaperRecommendationHealthConfig(
            config_version=" paper-recommendation-health-v0",
            max_average_cost_per_share=d("0.030000"),
            min_recommend_share=d("0.500000"),
        )
    with pytest.raises(ValueError, match="max_average_cost_per_share"):
        config(max_average_cost_per_share=d("-0.000001"))
    with pytest.raises(ValueError, match="max_average_cost_per_share"):
        config(max_average_cost_per_share=_DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="min_recommend_share"):
        config(min_recommend_share=d("1.000001"))

    with pytest.raises(ValueError, match="side"):
        health_row(side="maybe")
    with pytest.raises(ValueError, match="action"):
        health_row(action="hold")
    with pytest.raises(ValueError, match="net_probability_edge"):
        health_row(net_probability_edge=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="total_cost_per_share"):
        health_row(total_cost_per_share=d("-0.000001"))
    with pytest.raises(ValueError, match="recommendation_score"):
        health_row(recommendation_score=d("-0.000001"))
    with pytest.raises(ValueError, match="reason_codes"):
        health_row(reason_codes=("duplicate", "duplicate"))
    with pytest.raises(ValueError, match="paper_only"):
        report((health_row(paper_only=False),))
    with pytest.raises(ValueError, match="report_only"):
        report((health_row(report_only=False),))
    with pytest.raises(ValueError, match="readonly"):
        report((health_row(readonly=False),))


def test_health_report_normalizes_generated_at_to_utc_and_rejects_public_type_subclasses():
    summary = report(
        (health_row(),),
        generated_at=datetime(2026, 6, 19, 8, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC

    with pytest.raises(FrozenInstanceError):
        summary.health_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="generated_at"):
        report((health_row(),), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (health_row(),),
            generated_at=_DatetimeSubclass(2026, 6, 19, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="count"):
        PaperRecommendationHealthReasonCodeCount(
            reason_code="positive_net_edge",
            count=_IntSubclass(1),
        )


def test_health_report_constructor_rejects_inconsistent_summaries():
    summary = report((health_row("alpha"), health_row("beta", action="watch")))

    with pytest.raises(ValueError, match="row_count"):
        replace(summary, row_count=3)
    with pytest.raises(ValueError, match="recommend_count"):
        replace(summary, recommend_count=2)
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=())
    with pytest.raises(ValueError, match="health_status"):
        replace(summary, health_status="blocked")

    empty = report(())
    with pytest.raises(ValueError, match="average_net_probability_edge"):
        replace(empty, average_net_probability_edge=d("0.000001"))
    with pytest.raises(ValueError, match="average_total_cost_per_share"):
        replace(empty, average_total_cost_per_share=d("0.000001"))
    with pytest.raises(ValueError, match="top_recommendation_score"):
        replace(empty, top_recommendation_score=d("0.000001"))
