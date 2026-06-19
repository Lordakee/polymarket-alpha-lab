from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_probability_side_edge import (
    PaperProbabilitySideEdgeConfig,
    PaperProbabilitySideEdgeInput,
    PaperProbabilitySideEdgeReport,
    PaperProbabilitySideEdgeRow,
    build_paper_probability_side_edge_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def edge_input(
    *,
    market_slug: str = "event-alpha",
    question: str = "Will alpha happen?",
    side: str = "yes",
    forecast_probability: Decimal = d("0.640000"),
    side_price: Decimal = d("0.570000"),
    fee_cost_per_share: Decimal = d("0.015000"),
    spread_cost_per_share: Decimal = ZERO,
    slippage_cost_per_share: Decimal = ZERO,
    funding_cost_per_share: Decimal = ZERO,
    finalization_cost_per_share: Decimal = ZERO,
    time_cost_per_share: Decimal = ZERO,
    risk_cost_per_share: Decimal = ZERO,
    capital_cost_per_share: Decimal = ZERO,
    requested_paper_shares: Decimal = d("100.000000"),
    max_executable_shares: Decimal = d("100.000000"),
    market_context_fresh: bool = True,
    settlement_context_fresh: bool = True,
    reason_codes: tuple[str, ...] = ("seed",),
) -> PaperProbabilitySideEdgeInput:
    return PaperProbabilitySideEdgeInput(
        market_slug=market_slug,
        question=question,
        side=side,
        forecast_probability=forecast_probability,
        side_price=side_price,
        fee_cost_per_share=fee_cost_per_share,
        spread_cost_per_share=spread_cost_per_share,
        slippage_cost_per_share=slippage_cost_per_share,
        funding_cost_per_share=funding_cost_per_share,
        finalization_cost_per_share=finalization_cost_per_share,
        time_cost_per_share=time_cost_per_share,
        risk_cost_per_share=risk_cost_per_share,
        capital_cost_per_share=capital_cost_per_share,
        requested_paper_shares=requested_paper_shares,
        max_executable_shares=max_executable_shares,
        market_context_fresh=market_context_fresh,
        settlement_context_fresh=settlement_context_fresh,
        reason_codes=reason_codes,
    )


def config(
    *,
    min_net_probability_edge: Decimal = d("0.010000"),
) -> PaperProbabilitySideEdgeConfig:
    return PaperProbabilitySideEdgeConfig(
        config_version="probability-side-edge-v0",
        min_net_probability_edge=min_net_probability_edge,
    )


def build_report(*inputs: PaperProbabilitySideEdgeInput) -> PaperProbabilitySideEdgeReport:
    return build_paper_probability_side_edge_report(
        inputs,
        config=config(),
        generated_at=GENERATED_AT,
    )


def field_values(instance):
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_build_report_preserves_yes_and_no_probability_event_economics():
    report = build_report(
        edge_input(
            market_slug="event-yes",
            side="yes",
            forecast_probability=d("0.640000"),
            side_price=d("0.570000"),
            fee_cost_per_share=d("0.015000"),
        ),
        edge_input(
            market_slug="event-no",
            side="no",
            forecast_probability=d("0.640000"),
            side_price=d("0.310000"),
            fee_cost_per_share=d("0.015000"),
        ),
    )

    yes = next(row for row in report.rows if row.side == "yes")
    assert yes.side_probability == d("0.640000")
    assert yes.market_implied_probability == d("0.570000")
    assert yes.gross_probability_edge == d("0.070000")
    assert yes.total_cost_per_share == d("0.015000")
    assert yes.net_probability_edge == d("0.055000")
    assert yes.recommendation_score == d("0.055000")
    assert yes.action == "recommend"
    assert yes.depth_status == "sufficient_depth"

    no = next(row for row in report.rows if row.side == "no")
    assert no.side_probability == d("0.360000")
    assert no.market_implied_probability == d("0.310000")
    assert no.gross_probability_edge == d("0.050000")
    assert no.total_cost_per_share == d("0.015000")
    assert no.net_probability_edge == d("0.035000")
    assert no.recommendation_score == d("0.035000")
    assert no.action == "recommend"
    assert no.depth_status == "sufficient_depth"

    assert report.generated_at == GENERATED_AT
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.row_count == 2
    assert report.recommend_count == 2
    assert report.watch_count == 0
    assert report.reject_count == 0


def test_stale_market_or_settlement_context_can_only_watch_with_zero_score():
    report = build_report(
        edge_input(market_slug="stale-market", market_context_fresh=False),
        edge_input(market_slug="stale-settlement", settlement_context_fresh=False),
    )

    stale_market = next(row for row in report.rows if row.market_slug == "stale-market")
    assert stale_market.action == "watch"
    assert stale_market.recommendation_score == ZERO
    assert "market_context_stale" in stale_market.reason_codes

    stale_settlement = next(
        row for row in report.rows if row.market_slug == "stale-settlement"
    )
    assert stale_settlement.action == "watch"
    assert stale_settlement.recommendation_score == ZERO
    assert "settlement_context_stale" in stale_settlement.reason_codes


def test_no_depth_rejects_and_partial_depth_can_recommend_executable_size():
    report = build_report(
        edge_input(market_slug="no-depth", max_executable_shares=ZERO),
        edge_input(
            market_slug="partial-depth",
            requested_paper_shares=d("100.000000"),
            max_executable_shares=d("40.000000"),
        ),
    )

    partial = next(row for row in report.rows if row.market_slug == "partial-depth")
    assert partial.depth_status == "partial_depth"
    assert partial.executable_paper_shares == d("40.000000")
    assert partial.action == "recommend"
    assert partial.recommendation_score == d("0.055000")
    assert "partial_depth" in partial.reason_codes

    no_depth = next(row for row in report.rows if row.market_slug == "no-depth")
    assert no_depth.depth_status == "no_depth"
    assert no_depth.executable_paper_shares == ZERO
    assert no_depth.action == "reject"
    assert no_depth.recommendation_score == ZERO
    assert "no_depth" in no_depth.reason_codes


def test_negative_or_zero_net_probability_edge_rejects_with_zero_score():
    report = build_report(
        edge_input(
            forecast_probability=d("0.540000"),
            side_price=d("0.550000"),
            fee_cost_per_share=d("0.010000"),
        ),
    )

    row = report.rows[0]
    assert row.gross_probability_edge == d("-0.010000")
    assert row.net_probability_edge == d("-0.020000")
    assert row.action == "reject"
    assert row.recommendation_score == ZERO
    assert "nonpositive_net_probability_edge" in row.reason_codes


def test_positive_edge_below_configured_recommend_threshold_watches():
    report = build_paper_probability_side_edge_report(
        [
            edge_input(
                forecast_probability=d("0.600000"),
                side_price=d("0.560000"),
                fee_cost_per_share=d("0.015000"),
            )
        ],
        config=config(min_net_probability_edge=d("0.030000")),
        generated_at=GENERATED_AT,
    )

    row = report.rows[0]
    assert row.net_probability_edge == d("0.025000")
    assert row.action == "watch"
    assert row.recommendation_score == d("0.025000")
    assert "below_min_net_probability_edge" in row.reason_codes


def test_rows_sort_by_action_score_edge_depth_cost_and_identity():
    report = build_report(
        edge_input(
            market_slug="reject-negative",
            forecast_probability=d("0.500000"),
            side_price=d("0.560000"),
            fee_cost_per_share=d("0.010000"),
            max_executable_shares=d("100.000000"),
        ),
        edge_input(
            market_slug="watch-stale",
            forecast_probability=d("0.800000"),
            side_price=d("0.500000"),
            fee_cost_per_share=d("0.010000"),
            market_context_fresh=False,
            max_executable_shares=d("100.000000"),
        ),
        edge_input(
            market_slug="recommend-low",
            forecast_probability=d("0.650000"),
            side_price=d("0.590000"),
            fee_cost_per_share=d("0.010000"),
            max_executable_shares=d("100.000000"),
        ),
        edge_input(
            market_slug="recommend-high",
            forecast_probability=d("0.700000"),
            side_price=d("0.600000"),
            fee_cost_per_share=d("0.010000"),
            max_executable_shares=d("100.000000"),
        ),
    )

    assert [row.market_slug for row in report.rows] == [
        "recommend-high",
        "recommend-low",
        "watch-stale",
        "reject-negative",
    ]

    tied = build_report(
        edge_input(
            market_slug="depth-20",
            forecast_probability=d("0.700000"),
            side_price=d("0.640000"),
            fee_cost_per_share=d("0.010000"),
            requested_paper_shares=d("100.000000"),
            max_executable_shares=d("20.000000"),
        ),
        edge_input(
            market_slug="depth-80",
            forecast_probability=d("0.700000"),
            side_price=d("0.640000"),
            fee_cost_per_share=d("0.010000"),
            requested_paper_shares=d("100.000000"),
            max_executable_shares=d("80.000000"),
        ),
        edge_input(
            market_slug="cost-low",
            forecast_probability=d("0.700000"),
            side_price=d("0.630000"),
            fee_cost_per_share=d("0.020000"),
            requested_paper_shares=d("100.000000"),
            max_executable_shares=d("100.000000"),
        ),
        edge_input(
            market_slug="cost-high",
            forecast_probability=d("0.700000"),
            side_price=d("0.600000"),
            fee_cost_per_share=d("0.050000"),
            requested_paper_shares=d("100.000000"),
            max_executable_shares=d("100.000000"),
        ),
    )

    assert [row.market_slug for row in tied.rows] == [
        "cost-low",
        "cost-high",
        "depth-80",
        "depth-20",
    ]


def test_direct_constructors_validate_consistency_utc_and_safety_flags():
    eastern = timezone(timedelta(hours=-4))
    report = build_paper_probability_side_edge_report(
        [edge_input()],
        config=config(),
        generated_at=datetime(2026, 6, 19, 8, 0, tzinfo=eastern),
    )
    assert report.generated_at == GENERATED_AT

    rebuilt_row = PaperProbabilitySideEdgeRow(**field_values(report.rows[0]))
    assert rebuilt_row == report.rows[0]

    with pytest.raises(ValueError, match="net_probability_edge"):
        replace(report.rows[0], net_probability_edge=d("0.000001"))
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=3)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(edge_input(), readonly=False)


def test_dataclasses_are_frozen():
    input_row = edge_input()
    cfg = config()
    report = build_report(input_row)
    row = report.rows[0]

    with pytest.raises(FrozenInstanceError):
        input_row.side = "no"
    with pytest.raises(FrozenInstanceError):
        cfg.min_net_probability_edge = d("0.020000")
    with pytest.raises(FrozenInstanceError):
        row.action = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows = ()


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    (
        ("forecast_probability", Decimal("-0.000001"), "forecast_probability"),
        ("forecast_probability", Decimal("1.000001"), "forecast_probability"),
        ("side_price", Decimal("1.000001"), "side_price"),
        ("fee_cost_per_share", Decimal("-0.000001"), "fee_cost_per_share"),
        ("requested_paper_shares", Decimal("-0.000001"), "requested_paper_shares"),
        ("max_executable_shares", Decimal("NaN"), "max_executable_shares"),
    ),
)
def test_input_constructor_rejects_invalid_probability_price_cost_and_share_values(
    field_name,
    bad_value,
    match,
):
    with pytest.raises(ValueError, match=match):
        replace(edge_input(), **{field_name: bad_value})


def test_decimal_only_inputs_configs_and_rows_reject_floats():
    with pytest.raises(ValueError, match="forecast_probability"):
        replace(edge_input(), forecast_probability=0.64)
    with pytest.raises(ValueError, match="min_net_probability_edge"):
        PaperProbabilitySideEdgeConfig(
            config_version="probability-side-edge-v0",
            min_net_probability_edge=0.01,
        )
    with pytest.raises(ValueError, match="side_probability"):
        PaperProbabilitySideEdgeRow(
            market_slug="float-row",
            question="Float row?",
            side="yes",
            side_probability=0.64,
            market_implied_probability=d("0.570000"),
            gross_probability_edge=d("0.070000"),
            total_cost_per_share=d("0.015000"),
            net_probability_edge=d("0.055000"),
            recommendation_score=d("0.055000"),
            action="recommend",
            depth_status="sufficient_depth",
            requested_paper_shares=d("100.000000"),
            max_executable_shares=d("100.000000"),
            executable_paper_shares=d("100.000000"),
            reason_codes=("seed",),
        )


def test_builder_rejects_non_exact_public_types():
    with pytest.raises(ValueError, match="config"):
        build_paper_probability_side_edge_report(
            [edge_input()],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_probability_side_edge_report(
            [edge_input()],
            config=config(),
            generated_at="2026-06-19T12:00:00Z",
        )
    with pytest.raises(ValueError, match="inputs"):
        build_paper_probability_side_edge_report(
            [object()],
            config=config(),
            generated_at=GENERATED_AT,
        )
