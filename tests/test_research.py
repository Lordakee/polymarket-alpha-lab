from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256

from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.research import build_research_packet


def candidate(raw_archive_path: str = "data/raw/gamma/markets.json") -> ScoredCandidate:
    return ScoredCandidate(
        condition_id="0xabc",
        token_id="111",
        market_slug="example-market",
        question="Will the example resolve yes?",
        total_score="78.500",
        raw_archive_path=raw_archive_path,
    )


def test_build_research_packet_records_required_review_fields():
    packet = build_research_packet(
        candidate=candidate(),
        created_at=datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        market_url="https://polymarket.com/event/example-market",
        outcome_name="Yes",
        strategy_type="market_quality",
        model_probability=Decimal("0.56"),
        bid=Decimal("0.50"),
        ask=Decimal("0.52"),
        midpoint=Decimal("0.51"),
        expected_entry_price=Decimal("0.514"),
        fair_value_estimate=Decimal("0.56"),
        theoretical_edge=Decimal("0.046"),
        spread=Decimal("0.02"),
        slippage_estimate=Decimal("0.004"),
        cost_adjusted_edge=Decimal("0.026"),
        confidence=Decimal("0.60"),
        max_executable_size=Decimal("100"),
        risk_tags=("liquidity", "rules"),
        thesis="Market is active with tight spread and clear rules.",
        invalidating_conditions="Spread widens above threshold or rules change.",
        rule_text="Example resolution source text.",
        resolution_source="Example source",
    )

    assert packet.packet_id == "0xabc:111:20260613T123000Z"
    assert packet.condition_id == "0xabc"
    assert packet.token_id == "111"
    assert packet.market_url == "https://polymarket.com/event/example-market"
    assert packet.expected_entry_price == Decimal("0.514")
    assert packet.rule_text_hash == sha256(
        "Example resolution source text.".encode("utf-8")
    ).hexdigest()
    assert packet.is_complete is True
    assert packet.missing_required_fields() == []


def test_research_packet_reports_missing_required_fields():
    packet = build_research_packet(
        candidate=candidate(raw_archive_path=""),
        created_at=datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        market_url="",
        outcome_name="",
        strategy_type="market_quality",
        model_probability=None,
        bid=None,
        ask=None,
        midpoint=None,
        expected_entry_price=None,
        fair_value_estimate=None,
        theoretical_edge=None,
        spread=None,
        slippage_estimate=None,
        cost_adjusted_edge=None,
        confidence=None,
        max_executable_size=Decimal("0"),
        risk_tags=(),
        thesis="",
        invalidating_conditions="",
        rule_text="",
        resolution_source="",
    )

    assert packet.is_complete is False
    assert packet.missing_required_fields() == [
        "market_url",
        "outcome_name",
        "model_probability",
        "bid",
        "ask",
        "midpoint",
        "expected_entry_price",
        "fair_value_estimate",
        "theoretical_edge",
        "spread",
        "slippage_estimate",
        "cost_adjusted_edge",
        "confidence",
        "raw_archive_path",
        "risk_tags",
        "thesis",
        "invalidating_conditions",
        "rule_text",
        "resolution_source",
        "positive_max_executable_size",
    ]


def test_research_packet_reports_blank_risk_tags_missing():
    packet = build_research_packet(
        candidate=candidate(),
        created_at=datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        market_url="https://polymarket.com/event/example-market",
        outcome_name="Yes",
        strategy_type="market_quality",
        model_probability=Decimal("0.56"),
        bid=Decimal("0.50"),
        ask=Decimal("0.52"),
        midpoint=Decimal("0.51"),
        expected_entry_price=Decimal("0.514"),
        fair_value_estimate=Decimal("0.56"),
        theoretical_edge=Decimal("0.046"),
        spread=Decimal("0.02"),
        slippage_estimate=Decimal("0.004"),
        cost_adjusted_edge=Decimal("0.026"),
        confidence=Decimal("0.60"),
        max_executable_size=Decimal("100"),
        risk_tags=("liquidity", "   "),
        thesis="Tight spread.",
        invalidating_conditions="Spread widens.",
        rule_text="Example rule.",
        resolution_source="Example source",
    )

    assert "risk_tags" in packet.missing_required_fields()


def test_research_packet_reports_non_finite_decimals_missing():
    packet = build_research_packet(
        candidate=candidate(),
        created_at=datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        market_url="https://polymarket.com/event/example-market",
        outcome_name="Yes",
        strategy_type="market_quality",
        model_probability=Decimal("NaN"),
        bid=Decimal("Infinity"),
        ask=Decimal("0.52"),
        midpoint=Decimal("0.51"),
        expected_entry_price=Decimal("0.514"),
        fair_value_estimate=Decimal("-Infinity"),
        theoretical_edge=Decimal("0.046"),
        spread=Decimal("0.02"),
        slippage_estimate=Decimal("0.004"),
        cost_adjusted_edge=Decimal("0.026"),
        confidence=Decimal("NaN"),
        max_executable_size=Decimal("NaN"),
        risk_tags=("liquidity",),
        thesis="Tight spread.",
        invalidating_conditions="Spread widens.",
        rule_text="Example rule.",
        resolution_source="Example source",
    )

    assert packet.is_complete is False
    assert packet.missing_required_fields() == [
        "model_probability",
        "bid",
        "fair_value_estimate",
        "confidence",
        "positive_max_executable_size",
    ]


def test_research_packet_requires_strategy_type_and_non_whitespace_strings():
    packet = build_research_packet(
        candidate=candidate(),
        created_at=datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        market_url="   ",
        outcome_name="\t",
        strategy_type="",
        model_probability=Decimal("0.56"),
        bid=Decimal("0.50"),
        ask=Decimal("0.52"),
        midpoint=Decimal("0.51"),
        expected_entry_price=Decimal("0.514"),
        fair_value_estimate=Decimal("0.56"),
        theoretical_edge=Decimal("0.046"),
        spread=Decimal("0.02"),
        slippage_estimate=Decimal("0.004"),
        cost_adjusted_edge=Decimal("0.026"),
        confidence=Decimal("0.60"),
        max_executable_size=Decimal("100"),
        risk_tags=("liquidity", "rules"),
        thesis="  ",
        invalidating_conditions="\n",
        rule_text=" \t ",
        resolution_source="  ",
    )

    assert packet.is_complete is False
    assert packet.missing_required_fields() == [
        "market_url",
        "outcome_name",
        "strategy_type",
        "thesis",
        "invalidating_conditions",
        "rule_text",
        "resolution_source",
    ]


def test_build_research_packet_treats_naive_datetime_as_utc():
    packet = build_research_packet(
        candidate=candidate(),
        created_at=datetime(2026, 6, 13, 12, 30),
        market_url="https://polymarket.com/event/example-market",
        outcome_name="Yes",
        strategy_type="market_quality",
        model_probability=Decimal("0.56"),
        bid=Decimal("0.50"),
        ask=Decimal("0.52"),
        midpoint=Decimal("0.51"),
        expected_entry_price=Decimal("0.514"),
        fair_value_estimate=Decimal("0.56"),
        theoretical_edge=Decimal("0.046"),
        spread=Decimal("0.02"),
        slippage_estimate=Decimal("0.004"),
        cost_adjusted_edge=Decimal("0.026"),
        confidence=Decimal("0.60"),
        max_executable_size=Decimal("100"),
        risk_tags=("liquidity", "rules"),
        thesis="Market is active with tight spread and clear rules.",
        invalidating_conditions="Spread widens above threshold or rules change.",
        rule_text="Example resolution source text.",
        resolution_source="Example source",
    )

    assert packet.packet_id == "0xabc:111:20260613T123000Z"
    assert packet.created_at.tzinfo is UTC
