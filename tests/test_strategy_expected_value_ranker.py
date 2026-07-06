from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_expected_value_ranker import (
    StrategyExpectedValueRankerCandidate,
    StrategyExpectedValueRankerConfig,
    StrategyExpectedValueRankerReport,
    rank_strategy_expected_value_candidates,
)


class _DecimalSubclass(Decimal):
    pass


def _candidate(
    *,
    candidate_id: str = "market-a",
    event_payoff: Decimal = Decimal("1.000000"),
    market_probability: Decimal = Decimal("0.480000"),
    forecast_probability: Decimal = Decimal("0.620000"),
    fee_drag: Decimal = Decimal("0.010000"),
    slippage_buffer: Decimal = Decimal("0.005000"),
    resolution_risk: Decimal = Decimal("0.200000"),
    liquidity_capacity: Decimal = Decimal("150.000000"),
) -> StrategyExpectedValueRankerCandidate:
    return StrategyExpectedValueRankerCandidate(
        candidate_id=candidate_id,
        event_payoff=event_payoff,
        market_probability=market_probability,
        forecast_probability=forecast_probability,
        fee_drag=fee_drag,
        slippage_buffer=slippage_buffer,
        resolution_risk=resolution_risk,
        liquidity_capacity=liquidity_capacity,
    )


def _config() -> StrategyExpectedValueRankerConfig:
    return StrategyExpectedValueRankerConfig(
        minimum_cost_adjusted_edge=Decimal("0.020000"),
        maximum_resolution_risk=Decimal("0.300000"),
        minimum_liquidity_capacity=Decimal("10.000000"),
    )


def test_expected_value_ranker_sorts_by_payoff_edge_risk_and_capacity():
    report = rank_strategy_expected_value_candidates(
        (
            _candidate(
                candidate_id="resolution-risk",
                market_probability=Decimal("0.350000"),
                forecast_probability=Decimal("0.600000"),
                resolution_risk=Decimal("0.700000"),
                liquidity_capacity=Decimal("100.000000"),
            ),
            _candidate(
                candidate_id="thin-high-edge",
                market_probability=Decimal("0.200000"),
                forecast_probability=Decimal("0.420000"),
                resolution_risk=Decimal("0.050000"),
                liquidity_capacity=Decimal("20.000000"),
            ),
            _candidate(
                candidate_id="small-positive",
                market_probability=Decimal("0.510000"),
                forecast_probability=Decimal("0.540000"),
                fee_drag=Decimal("0.015000"),
                resolution_risk=Decimal("0.100000"),
                liquidity_capacity=Decimal("100.000000"),
            ),
            _candidate(
                candidate_id="deep-capacity",
                market_probability=Decimal("0.480000"),
                forecast_probability=Decimal("0.620000"),
                resolution_risk=Decimal("0.200000"),
                liquidity_capacity=Decimal("150.000000"),
            ),
            _candidate(
                candidate_id="illiquid",
                market_probability=Decimal("0.300000"),
                forecast_probability=Decimal("0.600000"),
                resolution_risk=Decimal("0.050000"),
                liquidity_capacity=Decimal("5.000000"),
            ),
        ),
        config=_config(),
    )

    assert isinstance(report, StrategyExpectedValueRankerReport)
    assert tuple(row.candidate_id for row in report.rows) == (
        "deep-capacity",
        "thin-high-edge",
        "small-positive",
        "resolution-risk",
        "illiquid",
    )
    assert tuple(row.rank for row in report.rows) == (
        Decimal("1.000000"),
        Decimal("2.000000"),
        Decimal("3.000000"),
        Decimal("4.000000"),
        Decimal("5.000000"),
    )
    assert tuple(row.rank_status for row in report.rows) == (
        "ranked",
        "ranked",
        "watch",
        "blocked",
        "blocked",
    )

    deep_capacity = report.rows[0]
    assert deep_capacity.forecast_expected_payoff == Decimal("0.620000")
    assert deep_capacity.market_implied_cost == Decimal("0.480000")
    assert deep_capacity.probability_edge == Decimal("0.140000")
    assert deep_capacity.cost_adjustment == Decimal("0.015000")
    assert deep_capacity.cost_adjusted_edge == Decimal("0.125000")
    assert deep_capacity.resolution_risk_adjusted_edge == Decimal("0.100000")
    assert deep_capacity.capacity_adjusted_expected_value == Decimal("15.000000")
    assert deep_capacity.reason_codes == (
        "probability_event_payoff_model",
        "ev_cost_adjusted_edge_ranked",
        "ev_resolution_risk_accepted",
        "ev_liquidity_capacity_accepted",
    )

    assert report.rows[2].reason_codes == (
        "probability_event_payoff_model",
        "ev_cost_adjusted_edge_watch",
        "ev_resolution_risk_accepted",
        "ev_liquidity_capacity_accepted",
    )
    assert "ev_resolution_risk_blocked" in report.rows[3].reason_codes
    assert "ev_liquidity_capacity_blocked" in report.rows[4].reason_codes
    assert report.candidate_count == Decimal("5.000000")
    assert report.ranked_count == Decimal("2.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.blocked_count == Decimal("2.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_expected_value_ranker_uses_probability_event_payoff_not_asset_return():
    report = rank_strategy_expected_value_candidates(
        (
            _candidate(
                candidate_id="two-dollar-payoff",
                event_payoff=Decimal("2.000000"),
                market_probability=Decimal("0.400000"),
                forecast_probability=Decimal("0.500000"),
                fee_drag=Decimal("0.020000"),
                slippage_buffer=Decimal("0.010000"),
                resolution_risk=Decimal("0.100000"),
                liquidity_capacity=Decimal("10.000000"),
            ),
        ),
        config=_config(),
    )

    row = report.rows[0]
    assert row.forecast_expected_payoff == Decimal("1.000000")
    assert row.market_implied_cost == Decimal("0.800000")
    assert row.probability_edge == Decimal("0.100000")
    assert row.cost_adjusted_edge == Decimal("0.170000")
    assert row.resolution_risk_adjusted_edge == Decimal("0.153000")
    assert row.capacity_adjusted_expected_value == Decimal("1.530000")
    assert row.rank_status == "ranked"


def test_expected_value_ranker_has_deterministic_tie_breaks():
    report = rank_strategy_expected_value_candidates(
        (
            _candidate(
                candidate_id="lower-raw-edge",
                market_probability=Decimal("0.410000"),
                forecast_probability=Decimal("0.500000"),
                fee_drag=Decimal("0.000000"),
                slippage_buffer=Decimal("0.000000"),
                resolution_risk=Decimal("0.000000"),
                liquidity_capacity=Decimal("10.000000"),
            ),
            _candidate(
                candidate_id="higher-raw-edge",
                market_probability=Decimal("0.400000"),
                forecast_probability=Decimal("0.500000"),
                fee_drag=Decimal("0.000000"),
                slippage_buffer=Decimal("0.000000"),
                resolution_risk=Decimal("0.100000"),
                liquidity_capacity=Decimal("10.000000"),
            ),
        ),
        config=_config(),
    )

    assert tuple(row.candidate_id for row in report.rows) == (
        "higher-raw-edge",
        "lower-raw-edge",
    )
    assert tuple(row.capacity_adjusted_expected_value for row in report.rows) == (
        Decimal("0.900000"),
        Decimal("0.900000"),
    )


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("event_payoff", Decimal("0")),
        ("market_probability", Decimal("-0.000001")),
        ("market_probability", Decimal("1.000001")),
        ("forecast_probability", Decimal("-0.000001")),
        ("forecast_probability", Decimal("1.000001")),
        ("fee_drag", Decimal("-0.000001")),
        ("slippage_buffer", Decimal("-0.000001")),
        ("resolution_risk", Decimal("-0.000001")),
        ("resolution_risk", Decimal("1.000001")),
        ("liquidity_capacity", Decimal("-0.000001")),
    ),
)
def test_expected_value_candidate_rejects_invalid_ranges(
    field_name: str,
    field_value: Decimal,
):
    with pytest.raises(ValueError, match=field_name):
        _candidate(**{field_name: field_value})


def test_expected_value_candidate_rejects_non_decimal_inputs():
    with pytest.raises(ValueError, match="market_probability"):
        _candidate(market_probability=0.48)
    with pytest.raises(ValueError, match="event_payoff"):
        _candidate(event_payoff=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="fee_drag"):
        _candidate(fee_drag="0.010000")


def test_expected_value_ranker_rejects_invalid_top_level_inputs():
    with pytest.raises(ValueError, match="config"):
        rank_strategy_expected_value_candidates((), config=object())
    with pytest.raises(ValueError, match="candidates"):
        rank_strategy_expected_value_candidates((_candidate(), object()), config=_config())
    with pytest.raises(ValueError, match="candidate_id"):
        rank_strategy_expected_value_candidates(
            (_candidate(candidate_id="dup"), _candidate(candidate_id="dup")),
            config=_config(),
        )


def test_expected_value_ranker_outputs_are_frozen_and_revalidated():
    report = rank_strategy_expected_value_candidates((_candidate(),), config=_config())
    row = report.rows[0]

    with pytest.raises(FrozenInstanceError):
        report.candidate_count = Decimal("0")
    with pytest.raises(FrozenInstanceError):
        row.rank_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        _candidate().market_probability = Decimal("0")

    with pytest.raises(ValueError, match="cost_adjusted_edge"):
        replace(row, cost_adjusted_edge=Decimal("0.124000"))
    with pytest.raises(ValueError, match="rank_status"):
        replace(row, rank_status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_config(), readonly=False)
