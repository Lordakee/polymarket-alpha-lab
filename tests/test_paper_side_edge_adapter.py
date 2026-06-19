from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_probability_side_edge import (
    PaperProbabilitySideEdgeInput,
    PaperProbabilitySideEdgeReport,
)
from polymarket_alpha_lab.paper_side_edge_adapter import (
    PaperSideEdgeAdapterConfig,
    PaperSideEdgeStrategyRow,
    build_paper_side_edge_report_from_strategy_rows,
    paper_side_edge_inputs_from_strategy_rows,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def strategy_row(
    *,
    market_slug: str = "event-alpha",
    question: str = "Will alpha happen?",
    side: str = "yes",
    forecast_probability: Decimal = d("0.640000"),
    side_price: Decimal = d("0.570000"),
    fee_cost_per_share: Decimal = d("0.010000"),
    spread_cost_per_share: Decimal = d("0.002000"),
    slippage_cost_per_share: Decimal = d("0.003000"),
    funding_cost_per_share: Decimal = d("0.004000"),
    finalization_cost_per_share: Decimal = d("0.005000"),
    time_cost_per_share: Decimal = d("0.006000"),
    risk_cost_per_share: Decimal = d("0.007000"),
    capital_cost_per_share: Decimal = d("0.008000"),
    requested_paper_shares: Decimal = d("100.000000"),
    max_executable_shares: Decimal = d("100.000000"),
    market_context_fresh: bool = True,
    settlement_context_fresh: bool = True,
    reason_codes: tuple[str, ...] = ("strategy_candidate",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperSideEdgeStrategyRow:
    return PaperSideEdgeStrategyRow(
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
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def adapter_config(
    *,
    config_version: str = "paper-side-edge-adapter-v0",
    min_net_probability_edge: Decimal = d("0.010000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperSideEdgeAdapterConfig:
    return PaperSideEdgeAdapterConfig(
        config_version=config_version,
        min_net_probability_edge=min_net_probability_edge,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def field_values(instance):
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_adapter_converts_strategy_rows_to_canonical_probability_side_edge_inputs():
    rows = (
        strategy_row(
            market_slug="yes-event",
            side="yes",
            forecast_probability=d("0.640000"),
            side_price=d("0.570000"),
            reason_codes=("strategy_candidate", "ranked"),
        ),
        strategy_row(
            market_slug="no-event",
            side="no",
            forecast_probability=d("0.640000"),
            side_price=d("0.310000"),
            max_executable_shares=d("40.000000"),
        ),
    )

    inputs = paper_side_edge_inputs_from_strategy_rows(rows)

    assert all(type(value) is PaperProbabilitySideEdgeInput for value in inputs)
    assert inputs[0] == PaperProbabilitySideEdgeInput(
        market_slug="yes-event",
        question="Will alpha happen?",
        side="yes",
        forecast_probability=d("0.640000"),
        side_price=d("0.570000"),
        fee_cost_per_share=d("0.010000"),
        spread_cost_per_share=d("0.002000"),
        slippage_cost_per_share=d("0.003000"),
        funding_cost_per_share=d("0.004000"),
        finalization_cost_per_share=d("0.005000"),
        time_cost_per_share=d("0.006000"),
        risk_cost_per_share=d("0.007000"),
        capital_cost_per_share=d("0.008000"),
        requested_paper_shares=d("100.000000"),
        max_executable_shares=d("100.000000"),
        market_context_fresh=True,
        settlement_context_fresh=True,
        reason_codes=("ranked", "strategy_candidate"),
    )
    assert inputs[1].side == "no"
    assert inputs[1].forecast_probability == d("0.640000")
    assert inputs[1].max_executable_shares == d("40.000000")


def test_adapter_builds_canonical_report_with_side_specific_probability_semantics_and_all_costs():
    report = build_paper_side_edge_report_from_strategy_rows(
        (
            strategy_row(
                market_slug="yes-event",
                side="yes",
                forecast_probability=d("0.700000"),
                side_price=d("0.620000"),
                fee_cost_per_share=d("0.010000"),
                spread_cost_per_share=d("0.002000"),
                slippage_cost_per_share=d("0.003000"),
                funding_cost_per_share=d("0.004000"),
                finalization_cost_per_share=d("0.005000"),
                time_cost_per_share=d("0.006000"),
                risk_cost_per_share=d("0.007000"),
                capital_cost_per_share=d("0.008000"),
            ),
            strategy_row(
                market_slug="no-event",
                side="no",
                forecast_probability=d("0.700000"),
                side_price=d("0.260000"),
                fee_cost_per_share=d("0.010000"),
                spread_cost_per_share=d("0.001000"),
                slippage_cost_per_share=d("0.001000"),
                funding_cost_per_share=d("0.001000"),
                finalization_cost_per_share=d("0.001000"),
                time_cost_per_share=d("0.001000"),
                risk_cost_per_share=d("0.001000"),
                capital_cost_per_share=d("0.001000"),
            ),
        ),
        config=adapter_config(min_net_probability_edge=d("0.010000")),
        generated_at=GENERATED_AT,
    )

    assert type(report) is PaperProbabilitySideEdgeReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-side-edge-adapter-v0"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    yes = next(row for row in report.rows if row.market_slug == "yes-event")
    assert yes.side_probability == d("0.700000")
    assert yes.market_implied_probability == d("0.620000")
    assert yes.total_cost_per_share == d("0.045000")
    assert yes.gross_probability_edge == d("0.080000")
    assert yes.net_probability_edge == d("0.035000")
    assert yes.action == "recommend"

    no = next(row for row in report.rows if row.market_slug == "no-event")
    assert no.side_probability == d("0.300000")
    assert no.market_implied_probability == d("0.260000")
    assert no.total_cost_per_share == d("0.017000")
    assert no.gross_probability_edge == d("0.040000")
    assert no.net_probability_edge == d("0.023000")
    assert no.action == "recommend"


def test_adapter_uses_canonical_report_threshold_and_context_reasons():
    report = build_paper_side_edge_report_from_strategy_rows(
        (
            strategy_row(
                market_slug="below-threshold",
                forecast_probability=d("0.600000"),
                side_price=d("0.570000"),
                fee_cost_per_share=d("0.010000"),
                spread_cost_per_share=ZERO,
                slippage_cost_per_share=ZERO,
                funding_cost_per_share=ZERO,
                finalization_cost_per_share=ZERO,
                time_cost_per_share=ZERO,
                risk_cost_per_share=ZERO,
                capital_cost_per_share=ZERO,
            ),
            strategy_row(
                market_slug="stale-market",
                forecast_probability=d("0.700000"),
                side_price=d("0.600000"),
                market_context_fresh=False,
            ),
        ),
        config=adapter_config(min_net_probability_edge=d("0.025000")),
        generated_at=GENERATED_AT,
    )

    below_threshold = next(row for row in report.rows if row.market_slug == "below-threshold")
    assert below_threshold.net_probability_edge == d("0.020000")
    assert below_threshold.action == "watch"
    assert "below_min_net_probability_edge" in below_threshold.reason_codes

    stale_market = next(row for row in report.rows if row.market_slug == "stale-market")
    assert stale_market.action == "watch"
    assert stale_market.recommendation_score == ZERO
    assert "market_context_stale" in stale_market.reason_codes


def test_adapter_dataclasses_normalize_utc_quantize_values_and_are_frozen():
    eastern = timezone(timedelta(hours=-4))
    report = build_paper_side_edge_report_from_strategy_rows(
        (strategy_row(forecast_probability=d("0.7000004"), side_price=d("0.6200004")),),
        config=adapter_config(min_net_probability_edge=d("0.0100004")),
        generated_at=datetime(2026, 6, 19, 8, 0, tzinfo=eastern),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].side_probability == d("0.700000")
    assert report.rows[0].market_implied_probability == d("0.620000")

    row = strategy_row()
    cfg = adapter_config()
    assert PaperSideEdgeStrategyRow(**field_values(row)) == row
    assert PaperSideEdgeAdapterConfig(**field_values(cfg)) == cfg

    with pytest.raises(FrozenInstanceError):
        row.side = "no"
    with pytest.raises(FrozenInstanceError):
        cfg.min_net_probability_edge = d("0.020000")


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    (
        ("forecast_probability", Decimal("-0.000001"), "forecast_probability"),
        ("forecast_probability", Decimal("1.000001"), "forecast_probability"),
        ("side_price", Decimal("1.000001"), "side_price"),
        ("fee_cost_per_share", Decimal("-0.000001"), "fee_cost_per_share"),
        ("capital_cost_per_share", Decimal("-0.000001"), "capital_cost_per_share"),
        ("requested_paper_shares", Decimal("-0.000001"), "requested_paper_shares"),
        ("max_executable_shares", Decimal("NaN"), "max_executable_shares"),
    ),
)
def test_strategy_row_rejects_invalid_probability_price_cost_and_share_values(
    field_name,
    bad_value,
    match,
):
    with pytest.raises(ValueError, match=match):
        replace(strategy_row(), **{field_name: bad_value})


def test_strategy_row_and_config_reject_float_math_inputs():
    with pytest.raises(ValueError, match="forecast_probability"):
        replace(strategy_row(), forecast_probability=0.64)
    with pytest.raises(ValueError, match="capital_cost_per_share"):
        replace(strategy_row(), capital_cost_per_share=0.01)
    with pytest.raises(ValueError, match="min_net_probability_edge"):
        PaperSideEdgeAdapterConfig(
            config_version="paper-side-edge-adapter-v0",
            min_net_probability_edge=0.01,
        )
