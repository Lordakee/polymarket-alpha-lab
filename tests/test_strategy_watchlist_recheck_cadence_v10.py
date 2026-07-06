from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from importlib import import_module
import inspect
import json

import pytest


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return import_module("polymarket_alpha_lab.strategy_watchlist_recheck_cadence_v10")


def _config(**overrides: object):
    values = {
        "config_version": "strategy-watchlist-recheck-cadence-v10",
        "tier_1_recheck_minutes": d("30.000000"),
        "tier_2_recheck_minutes": d("120.000000"),
        "tier_3_recheck_minutes": d("360.000000"),
        "moderate_market_move_bps": d("50.000000"),
        "large_market_move_bps": d("100.000000"),
        "near_resolution_minutes": d("360.000000"),
        "imminent_resolution_minutes": d("60.000000"),
        "low_capacity_score": d("0.250000"),
        "accelerated_multiplier": d("0.500000"),
        "deferred_multiplier": d("2.000000"),
        "min_recheck_minutes": d("5.000000"),
    }
    values.update(overrides)
    return _api().StrategyWatchlistRecheckCadenceV10Config(**values)


def _watchlist_input(**overrides: object):
    values = {
        "market_id": "market-btc-etf-approval",
        "watchlist_tier": "tier_1",
        "edge_status": "actionable_edge",
        "data_gap_status": "none",
        "market_move_bps": d("0.000000"),
        "source_freshness_status": "fresh",
        "time_to_resolution_minutes": d("1440.000000"),
        "team_capacity_score": d("0.800000"),
    }
    values.update(overrides)
    return _api().StrategyWatchlistRecheckCadenceV10Input(**values)


def _decision(**overrides: object):
    return _api().build_strategy_watchlist_recheck_cadence_v10_decision(
        _watchlist_input(**overrides),
        config=_config(),
    )


def test_cadence_v10_prioritizes_immediate_recheck_triggers_and_payload() -> None:
    api = _api()
    decision = _decision(
        data_gap_status="blocking_gap",
        market_move_bps=d("125.000000"),
        source_freshness_status="stale",
        time_to_resolution_minutes=d("45.000000"),
    )

    assert type(decision) is api.StrategyWatchlistRecheckCadenceV10Decision
    assert decision.market_id == "market-btc-etf-approval"
    assert decision.cadence_status == "recheck_now"
    assert decision.next_recheck_minutes == d("0.000000")
    assert decision.recheck_reason == (
        "Immediate recheck required: blocking data gap, large market move, "
        "stale source, and imminent resolution."
    )
    assert decision.reason_codes == (
        "actionable_edge",
        "blocking_data_gap",
        "large_market_move",
        "resolution_imminent",
        "source_stale",
        "tier_1_watchlist",
    )
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True

    payload = api.strategy_watchlist_recheck_cadence_v10_payload(decision)
    json.dumps(payload, sort_keys=True)
    assert payload["market_move_bps"] == "125.000000"
    assert payload["next_recheck_minutes"] == "0.000000"
    assert payload["reason_codes"] == [
        "actionable_edge",
        "blocking_data_gap",
        "large_market_move",
        "resolution_imminent",
        "source_stale",
        "tier_1_watchlist",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    def walk(value: object) -> None:
        assert not isinstance(value, float)
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)


def test_cadence_v10_sets_accelerated_standard_and_deferred_minutes() -> None:
    accelerated = _decision(
        market_id="market-fed-cut-watch",
        watchlist_tier="tier_2",
        edge_status="monitoring_edge",
        data_gap_status="major_gap",
        market_move_bps=d("0.000000"),
        source_freshness_status="fresh",
        time_to_resolution_minutes=d("1000.000000"),
        team_capacity_score=d("0.700000"),
    )
    standard = _decision(
        market_id="market-election-baseline",
        watchlist_tier="tier_2",
        edge_status="monitoring_edge",
        data_gap_status="none",
        market_move_bps=d("0.000000"),
        source_freshness_status="fresh",
        time_to_resolution_minutes=d("1000.000000"),
        team_capacity_score=d("0.700000"),
    )
    deferred = _decision(
        market_id="market-long-tail",
        watchlist_tier="tier_3",
        edge_status="monitoring_edge",
        data_gap_status="none",
        market_move_bps=d("0.000000"),
        source_freshness_status="fresh",
        time_to_resolution_minutes=d("2000.000000"),
        team_capacity_score=d("0.200000"),
    )

    assert accelerated.cadence_status == "accelerated_recheck"
    assert accelerated.next_recheck_minutes == d("60.000000")
    assert accelerated.reason_codes == (
        "data_gap_major",
        "monitoring_edge",
        "tier_2_watchlist",
    )
    assert standard.cadence_status == "standard_recheck"
    assert standard.next_recheck_minutes == d("120.000000")
    assert standard.reason_codes == (
        "cadence_standard",
        "monitoring_edge",
        "tier_2_watchlist",
    )
    assert deferred.cadence_status == "deferred_recheck"
    assert deferred.next_recheck_minutes == d("720.000000")
    assert deferred.reason_codes == (
        "capacity_constrained",
        "monitoring_edge",
        "tier_3_watchlist",
    )


def test_cadence_v10_dataclasses_are_frozen_strict_and_consistent() -> None:
    api = _api()
    decision = _decision()

    assert api.__all__ == (
        "DEFAULT_CONFIG_VERSION",
        "StrategyWatchlistRecheckCadenceV10Config",
        "StrategyWatchlistRecheckCadenceV10Decision",
        "StrategyWatchlistRecheckCadenceV10Input",
        "build_strategy_watchlist_recheck_cadence_v10_decision",
        "strategy_watchlist_recheck_cadence_v10_payload",
    )
    for exported_name in api.__all__:
        exported = getattr(api, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    with pytest.raises(FrozenInstanceError):
        decision.cadence_status = "recheck_now"  # type: ignore[misc]
    with pytest.raises(ValueError, match="market_move_bps must be a Decimal"):
        _watchlist_input(market_move_bps=1)
    with pytest.raises(ValueError, match="team_capacity_score must be between"):
        _watchlist_input(team_capacity_score=d("1.000001"))
    with pytest.raises(ValueError, match="tier_1_recheck_minutes must be a Decimal"):
        _config(tier_1_recheck_minutes=DecimalSubclass("30.000000"))
    with pytest.raises(ValueError, match="market_id"):
        _watchlist_input(market_id=" market-btc-etf-approval")
    with pytest.raises(ValueError, match="watchlist_tier"):
        _watchlist_input(watchlist_tier="vip")
    with pytest.raises(ValueError, match="edge_status"):
        _watchlist_input(edge_status="buy")
    with pytest.raises(ValueError, match="paper_only"):
        replace(_watchlist_input(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(_config(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(decision, readonly=False)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(decision, reason_codes=("cadence_standard",))
    with pytest.raises(ValueError, match="next_recheck_minutes"):
        replace(decision, next_recheck_minutes=d("999.000000"))


def test_cadence_v10_payload_and_source_are_readonly_local_scope() -> None:
    api = _api()
    decision = _decision()

    with pytest.raises(ValueError, match="Decision"):
        api.strategy_watchlist_recheck_cadence_v10_payload(object())
    payload = api.strategy_watchlist_recheck_cadence_v10_payload(decision)
    payload_text = repr(payload).lower()
    assert payload["market_id"] == "market-btc-etf-approval"
    assert "wallet" not in payload_text
    assert "private_key" not in payload_text

    source = inspect.getsource(api).lower()
    for banned in (
        "wallet",
        "auth",
        "private_key",
        "place_order",
        "requests",
        "httpx",
        "psycopg",
        "sqlite",
        "open(",
        ".write(",
    ):
        assert banned not in source
