from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_market_router import (
    TeamMarketRouteConfig,
    TeamMarketRouteInput,
    TeamMarketRouteReport,
    TeamMarketRouteRow,
    build_team_market_route_report,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def test_router_assigns_exactly_one_primary_team_and_optional_secondary():
    report = build_team_market_route_report(
        (
            TeamMarketRouteInput(
                condition_id="condition-btc",
                market_slug="bitcoin-above-120k",
                question="Will Bitcoin hit 120000 before August 31?",
                category_hint="finance.crypto.btc",
                event_template="btc_hit_price",
                routing_reason_codes=("keyword_bitcoin", "template_hit_price"),
            ),
        ),
        config=TeamMarketRouteConfig(config_version="team-router-v0"),
        generated_at=GENERATED_AT,
    )

    row = report.rows[0]
    assert row.primary_team_id == "crypto_btc"
    assert row.secondary_team_ids == ()
    assert row.routing_confidence == Decimal("0.900000")
    assert report.route_count == 1
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(FrozenInstanceError):
        row.primary_team_id = "crypto_eth"  # type: ignore[misc]


def test_router_maps_sports_unknown_prefix_to_sports_other_only():
    report = build_team_market_route_report(
        (
            TeamMarketRouteInput(
                condition_id="condition-sports",
                market_slug="curling-championship-winner",
                question="Will the home rink win the championship?",
                category_hint="sports.unknown.curling",
                event_template="sports_match_winner",
                routing_reason_codes=("category_hint_sports_unknown",),
            ),
        ),
        config=TeamMarketRouteConfig(config_version="team-router-v0"),
        generated_at=GENERATED_AT,
    )

    row = report.rows[0]
    assert row.category_id == "sports.other"
    assert row.primary_team_id == "sports_other"
    assert row.secondary_team_ids == ()
    assert row.routing_confidence == Decimal("0.700000")

    with pytest.raises(ValueError, match="category_hint must be a known routable category"):
        build_team_market_route_report(
            (
                TeamMarketRouteInput(
                    condition_id="condition-unknown",
                    market_slug="unknown-market",
                    question="Will the unknown thing happen?",
                    category_hint="finance.unknown",
                    event_template="unknown_template",
                    routing_reason_codes=("unknown_category",),
                ),
            ),
            config=TeamMarketRouteConfig(config_version="team-router-v0"),
            generated_at=GENERATED_AT,
        )


def test_row_rejects_secondary_team_that_equals_primary_or_is_not_unique_known_team():
    with pytest.raises(ValueError, match="secondary_team_ids cannot contain primary_team_id"):
        TeamMarketRouteRow(
            condition_id="condition-btc",
            market_slug="bitcoin-above-120k",
            question="Will Bitcoin hit 120000 before August 31?",
            category_id="finance.crypto.btc",
            event_template="btc_hit_price",
            primary_team_id="crypto_btc",
            secondary_team_ids=("crypto_btc",),
            routing_confidence=Decimal("0.900000"),
            routing_reason_codes=("keyword_bitcoin",),
        )

    with pytest.raises(ValueError, match="secondary_team_ids must be unique"):
        TeamMarketRouteRow(
            condition_id="condition-btc",
            market_slug="bitcoin-above-120k",
            question="Will Bitcoin hit 120000 before August 31?",
            category_id="finance.crypto.btc",
            event_template="btc_hit_price",
            primary_team_id="crypto_btc",
            secondary_team_ids=("crypto_eth", "crypto_eth"),
            routing_confidence=Decimal("0.900000"),
            routing_reason_codes=("keyword_bitcoin",),
        )

    with pytest.raises(ValueError, match="secondary_team_ids must be a known team"):
        TeamMarketRouteRow(
            condition_id="condition-btc",
            market_slug="bitcoin-above-120k",
            question="Will Bitcoin hit 120000 before August 31?",
            category_id="finance.crypto.btc",
            event_template="btc_hit_price",
            primary_team_id="crypto_btc",
            secondary_team_ids=("unknown_team",),
            routing_confidence=Decimal("0.900000"),
            routing_reason_codes=("keyword_bitcoin",),
        )


def test_routing_corrected_team_id_must_be_known_when_present():
    row = TeamMarketRouteRow(
        condition_id="condition-btc",
        market_slug="bitcoin-above-120k",
        question="Will Bitcoin hit 120000 before August 31?",
        category_id="finance.crypto.btc",
        event_template="btc_hit_price",
        primary_team_id="crypto_btc",
        secondary_team_ids=(),
        routing_confidence=Decimal("0.900000"),
        routing_reason_codes=("keyword_bitcoin",),
        routing_corrected_team_id="crypto_eth",
        routing_correction_timestamp=GENERATED_AT,
    )

    assert row.routing_corrected_team_id == "crypto_eth"
    assert row.routing_correction_timestamp == GENERATED_AT

    with pytest.raises(ValueError, match="routing_corrected_team_id must be a known team"):
        TeamMarketRouteRow(
            condition_id="condition-btc",
            market_slug="bitcoin-above-120k",
            question="Will Bitcoin hit 120000 before August 31?",
            category_id="finance.crypto.btc",
            event_template="btc_hit_price",
            primary_team_id="crypto_btc",
            secondary_team_ids=(),
            routing_confidence=Decimal("0.900000"),
            routing_reason_codes=("keyword_bitcoin",),
            routing_corrected_team_id="unknown_team",
            routing_correction_timestamp=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="routing_correction_timestamp is required"):
        TeamMarketRouteRow(
            condition_id="condition-btc",
            market_slug="bitcoin-above-120k",
            question="Will Bitcoin hit 120000 before August 31?",
            category_id="finance.crypto.btc",
            event_template="btc_hit_price",
            primary_team_id="crypto_btc",
            secondary_team_ids=(),
            routing_confidence=Decimal("0.900000"),
            routing_reason_codes=("keyword_bitcoin",),
            routing_corrected_team_id="crypto_eth",
        )

    with pytest.raises(ValueError, match="routing_corrected_team_id is required"):
        TeamMarketRouteRow(
            condition_id="condition-btc",
            market_slug="bitcoin-above-120k",
            question="Will Bitcoin hit 120000 before August 31?",
            category_id="finance.crypto.btc",
            event_template="btc_hit_price",
            primary_team_id="crypto_btc",
            secondary_team_ids=(),
            routing_confidence=Decimal("0.900000"),
            routing_reason_codes=("keyword_bitcoin",),
            routing_correction_timestamp=GENERATED_AT,
        )


def test_confidence_must_be_decimal_and_is_quantized_to_six_places():
    row = TeamMarketRouteRow(
        condition_id="condition-btc",
        market_slug="bitcoin-above-120k",
        question="Will Bitcoin hit 120000 before August 31?",
        category_id="finance.crypto.btc",
        event_template="btc_hit_price",
        primary_team_id="crypto_btc",
        secondary_team_ids=(),
        routing_confidence=Decimal("0.8123454"),
        routing_reason_codes=("keyword_bitcoin",),
    )

    assert row.routing_confidence == Decimal("0.812345")
    assert row.routing_confidence.as_tuple().exponent == -6

    with pytest.raises(ValueError, match="routing_confidence must be a Decimal"):
        TeamMarketRouteRow(
            condition_id="condition-btc",
            market_slug="bitcoin-above-120k",
            question="Will Bitcoin hit 120000 before August 31?",
            category_id="finance.crypto.btc",
            event_template="btc_hit_price",
            primary_team_id="crypto_btc",
            secondary_team_ids=(),
            routing_confidence=0.9,  # type: ignore[arg-type]
            routing_reason_codes=("keyword_bitcoin",),
        )


def test_false_safety_flags_raise_for_all_route_objects():
    with pytest.raises(ValueError, match="paper_only must be True"):
        TeamMarketRouteConfig(
            config_version="team-router-v0",
            paper_only=False,
        )

    with pytest.raises(ValueError, match="report_only must be True"):
        TeamMarketRouteInput(
            condition_id="condition-btc",
            market_slug="bitcoin-above-120k",
            question="Will Bitcoin hit 120000 before August 31?",
            category_hint="finance.crypto.btc",
            event_template="btc_hit_price",
            routing_reason_codes=("keyword_bitcoin",),
            report_only=False,
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        TeamMarketRouteRow(
            condition_id="condition-btc",
            market_slug="bitcoin-above-120k",
            question="Will Bitcoin hit 120000 before August 31?",
            category_id="finance.crypto.btc",
            event_template="btc_hit_price",
            primary_team_id="crypto_btc",
            secondary_team_ids=(),
            routing_confidence=Decimal("0.900000"),
            routing_reason_codes=("keyword_bitcoin",),
            readonly=False,
        )

    valid_row = TeamMarketRouteRow(
        condition_id="condition-btc",
        market_slug="bitcoin-above-120k",
        question="Will Bitcoin hit 120000 before August 31?",
        category_id="finance.crypto.btc",
        event_template="btc_hit_price",
        primary_team_id="crypto_btc",
        secondary_team_ids=(),
        routing_confidence=Decimal("0.900000"),
        routing_reason_codes=("keyword_bitcoin",),
    )
    with pytest.raises(ValueError, match="paper_only must be True"):
        TeamMarketRouteReport(
            generated_at=GENERATED_AT,
            config_version="team-router-v0",
            route_count=1,
            rows=(valid_row,),
            paper_only=False,
        )
