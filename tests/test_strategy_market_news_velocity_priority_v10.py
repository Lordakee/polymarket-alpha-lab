from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.strategy_market_news_velocity_priority_v10",
    )


def market(**overrides: object):
    values: dict[str, object] = {
        "market_id": "market-election-injunction",
        "market_slug": "will-election-injunction-stand",
        "new_source_count": d("5"),
        "high_reliability_source_share": d("0.800000"),
        "probability_move_bps": d("650.000000"),
        "source_contradiction_score": d("0.700000"),
        "time_to_resolution_minutes": d("45.000000"),
    }
    values.update(overrides)
    return api().StrategyMarketNewsVelocityPriorityV10Market(**values)


def build(markets: object):
    return api().build_strategy_market_news_velocity_priority_v10(markets)


def assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_float_or_int(item)


def test_news_velocity_report_ranks_fresh_research_by_all_priority_inputs() -> None:
    report = build(
        (
            market(
                market_id="market-low-noise",
                market_slug="low-news-market",
                new_source_count=d("0"),
                high_reliability_source_share=d("0.200000"),
                probability_move_bps=d("20.000000"),
                source_contradiction_score=d("0.000000"),
                time_to_resolution_minutes=d("2880.000000"),
            ),
            market(
                market_id="market-fed-cut",
                market_slug="fed-cut-next-meeting",
                new_source_count=d("3"),
                high_reliability_source_share=d("0.900000"),
                probability_move_bps=d("400.000000"),
                source_contradiction_score=d("0.200000"),
                time_to_resolution_minutes=d("180.000000"),
            ),
            market(),
        ),
    )

    assert report.market_count == d("3")
    assert report.research_now_count == d("1")
    assert report.accelerated_recheck_count == d("1")
    assert report.top_market_id == "market-election-injunction"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_id for row in report.rows) == (
        "market-election-injunction",
        "market-fed-cut",
        "market-low-noise",
    )
    assert tuple(row.research_rank for row in report.rows) == (
        d("1"),
        d("2"),
        d("3"),
    )

    top = report.rows[0]
    assert top.priority_score == d("82.750000")
    assert top.priority_tier == "research_now"
    assert top.research_cadence == "now"
    assert top.reason_codes == (
        "new_source_count_high",
        "high_reliability_source_share_high",
        "probability_move_large",
        "source_contradiction_high",
        "time_sensitive_immediate",
        "priority_tier_research_now",
    )

    assert report.rows[1].priority_score == d("54.000000")
    assert report.rows[1].priority_tier == "accelerated_recheck"
    assert report.rows[1].research_cadence == "within_60_minutes"

    assert report.rows[2].priority_score == d("4.500000")
    assert report.rows[2].priority_tier == "monitor"
    assert report.rows[2].research_cadence == "next_cycle"
    assert report.rows[2].reason_codes == (
        "no_new_sources",
        "high_reliability_source_share_low",
        "probability_move_small",
        "source_contradiction_low",
        "time_sensitive_low",
        "priority_tier_monitor",
    )


def test_payload_is_readonly_report_only_and_decimal_stringified() -> None:
    report = build((market(),))

    payload = report.payload

    assert payload["config_version"] == "strategy-market-news-velocity-priority-v10"
    assert payload["market_count"] == "1"
    assert payload["research_now_count"] == "1"
    assert payload["accelerated_recheck_count"] == "0"
    assert payload["top_market_id"] == "market-election-injunction"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["research_rank"] == "1"
    assert payload["rows"][0]["new_source_count"] == "5"
    assert payload["rows"][0]["high_reliability_source_share"] == "0.800000"
    assert payload["rows"][0]["probability_move_bps"] == "650.000000"
    assert payload["rows"][0]["source_contradiction_score"] == "0.700000"
    assert payload["rows"][0]["time_to_resolution_minutes"] == "45.000000"
    assert payload["rows"][0]["priority_score"] == "82.750000"
    assert_no_public_float_or_int(payload)


def test_empty_input_builds_readonly_empty_report() -> None:
    report = build(())

    assert report.market_count == d("0")
    assert report.research_now_count == d("0")
    assert report.accelerated_recheck_count == d("0")
    assert report.top_market_id is None
    assert report.rows == ()
    assert report.payload["rows"] == []


def test_dataclasses_are_frozen_and_numeric_inputs_must_be_exact_decimals() -> None:
    module = api()
    subject = market()
    report = build((subject,))

    for klass in (
        module.StrategyMarketNewsVelocityPriorityV10Market,
        module.StrategyMarketNewsVelocityPriorityV10Row,
        module.StrategyMarketNewsVelocityPriorityV10Report,
    ):
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        subject.market_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].priority_tier = "monitor"  # type: ignore[misc]

    with pytest.raises(ValueError, match="new_source_count must be a Decimal"):
        market(new_source_count=5)
    with pytest.raises(ValueError, match="high_reliability_source_share must be a Decimal"):
        market(high_reliability_source_share=0.8)
    with pytest.raises(ValueError, match="probability_move_bps must be a Decimal"):
        market(probability_move_bps=650)
    with pytest.raises(ValueError, match="source_contradiction_score must be a Decimal"):
        market(source_contradiction_score=0.7)
    with pytest.raises(ValueError, match="time_to_resolution_minutes must be a Decimal"):
        market(time_to_resolution_minutes=45)
    with pytest.raises(ValueError, match="paper_only must be True"):
        market(paper_only=False)


def test_validation_rejects_bad_domains_and_tampered_payload_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="markets must contain"):
        build((object(),))
    with pytest.raises(ValueError, match="market_id"):
        market(market_id=" market")
    with pytest.raises(ValueError, match="market_slug"):
        market(market_slug="")
    with pytest.raises(ValueError, match="new_source_count"):
        market(new_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="high_reliability_source_share"):
        market(high_reliability_source_share=d("1.000001"))
    with pytest.raises(ValueError, match="source_contradiction_score"):
        market(source_contradiction_score=d("-0.000001"))
    with pytest.raises(ValueError, match="time_to_resolution_minutes"):
        market(time_to_resolution_minutes=d("-1.000000"))

    with pytest.raises(ValueError, match="report"):
        module.strategy_market_news_velocity_priority_v10_payload(object())


def test_public_payload_validation_is_tamper_evident_and_rejects_unsafe_surfaces() -> None:
    module = api()
    payload = build((market(),)).payload

    assert module.strategy_market_news_velocity_priority_v10_payload(payload) == payload

    tampered_count = dict(payload)
    tampered_count["research_now_count"] = "0"
    with pytest.raises(ValueError, match="research_now_count"):
        module.strategy_market_news_velocity_priority_v10_payload(tampered_count)

    tampered_row = dict(payload)
    tampered_row["rows"] = [dict(payload["rows"][0], priority_score="1.000000")]
    with pytest.raises(ValueError, match="priority_score"):
        module.strategy_market_news_velocity_priority_v10_payload(tampered_row)

    missing_top_flag = dict(payload)
    del missing_top_flag["readonly"]
    with pytest.raises(ValueError, match="readonly must be True"):
        module.strategy_market_news_velocity_priority_v10_payload(missing_top_flag)

    missing_row_flag = dict(payload)
    missing_row_flag["rows"] = [
        {key: value for key, value in payload["rows"][0].items() if key != "readonly"},
    ]
    with pytest.raises(ValueError, match="readonly must be True"):
        module.strategy_market_news_velocity_priority_v10_payload(missing_row_flag)

    unsafe_key = dict(payload)
    unsafe_key["wallet_address"] = "0xabc"
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_market_news_velocity_priority_v10_payload(unsafe_key)

    unsafe_value = dict(payload)
    unsafe_value["top_market_id"] = "submit_order"
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_market_news_velocity_priority_v10_payload(unsafe_value)

    public_numeric_literal = dict(payload)
    public_numeric_literal["market_count"] = 1
    with pytest.raises(ValueError, match="Decimal-derived string"):
        module.strategy_market_news_velocity_priority_v10_payload(public_numeric_literal)


def test_module_is_pure_readonly_report_only_and_unwired_from_io_or_execution() -> None:
    module = api()
    source = inspect.getsource(module)

    assert module.__all__ == (
        "PRIORITY_TIERS",
        "REASON_CODES",
        "StrategyMarketNewsVelocityPriorityV10Market",
        "StrategyMarketNewsVelocityPriorityV10Row",
        "StrategyMarketNewsVelocityPriorityV10Report",
        "build_strategy_market_news_velocity_priority_v10",
        "strategy_market_news_velocity_priority_v10_payload",
    )

    forbidden_terms = (
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "clob",
        "wallet",
        "private_key",
        "signing",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    assert all(term not in source for term in forbidden_terms)
