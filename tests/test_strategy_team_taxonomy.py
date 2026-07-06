from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_team_taxonomy import (
    STRATEGY_TEAM_IDS,
    StrategyMarketRouteReport,
    StrategyMarketRouteRow,
    StrategyMarketRoutingInput,
    StrategyTeamProfile,
    StrategyTeamTaxonomyConfig,
    build_default_strategy_team_profiles,
    build_strategy_market_route_report,
    route_strategy_market,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def test_default_profiles_are_frozen_medium_sized_and_readonly() -> None:
    profiles = build_default_strategy_team_profiles()

    assert STRATEGY_TEAM_IDS == (
        "politics",
        "crypto_btc",
        "equity_index",
        "commodities_gold",
        "soccer",
        "basketball",
        "other_sports",
        "general",
    )
    assert tuple(profile.team_id for profile in profiles) == STRATEGY_TEAM_IDS
    assert all(type(profile.default_routing_confidence) is Decimal for profile in profiles)
    assert all(profile.paper_only is True for profile in profiles)
    assert all(profile.report_only is True for profile in profiles)
    assert all(profile.readonly is True for profile in profiles)

    with pytest.raises(FrozenInstanceError):
        profiles[0].display_name = "Changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("market", "expected_team_id", "expected_reason"),
    (
        (
            StrategyMarketRoutingInput(
                condition_id="condition-politics",
                market_slug="will-democrat-win-2028-presidential-election",
                question="Will a Democrat win the 2028 US presidential election?",
                category_hint="politics",
                tags=("election",),
            ),
            "politics",
            "category_hint_politics",
        ),
        (
            StrategyMarketRoutingInput(
                condition_id="condition-btc",
                market_slug="bitcoin-above-150k-in-2026",
                question="Will Bitcoin trade above $150,000 in 2026?",
                category_hint="finance.crypto",
                tags=("btc",),
            ),
            "crypto_btc",
            "keyword_bitcoin",
        ),
        (
            StrategyMarketRoutingInput(
                condition_id="condition-spx",
                market_slug="sp-500-close-above-7000",
                question="Will the S&P 500 close above 7,000 this year?",
                category_hint="finance.equities",
                tags=("spx",),
            ),
            "equity_index",
            "keyword_equity_index",
        ),
        (
            StrategyMarketRoutingInput(
                condition_id="condition-gold",
                market_slug="gold-above-3000",
                question="Will gold trade above $3,000 before December 31?",
                category_hint="commodities",
                tags=("xau",),
            ),
            "commodities_gold",
            "keyword_gold",
        ),
        (
            StrategyMarketRoutingInput(
                condition_id="condition-soccer",
                market_slug="champions-league-final-real-madrid-win",
                question="Will Real Madrid win the Champions League final?",
                category_hint="sports.soccer",
                tags=("uefa",),
            ),
            "soccer",
            "category_hint_soccer",
        ),
        (
            StrategyMarketRoutingInput(
                condition_id="condition-nba",
                market_slug="nba-finals-celtics-win",
                question="Will the Celtics win the NBA Finals?",
                category_hint="sports.basketball",
                tags=("nba",),
            ),
            "basketball",
            "category_hint_basketball",
        ),
        (
            StrategyMarketRoutingInput(
                condition_id="condition-tennis",
                market_slug="wimbledon-mens-final-alcaraz-win",
                question="Will Alcaraz win the Wimbledon men's final?",
                category_hint="sports.tennis",
                tags=("tennis",),
            ),
            "other_sports",
            "category_hint_other_sports",
        ),
        (
            StrategyMarketRoutingInput(
                condition_id="condition-general",
                market_slug="openai-release-new-model-before-september",
                question="Will OpenAI release a new model before September?",
                category_hint="technology",
                tags=("ai",),
            ),
            "general",
            "default_general_fallback",
        ),
    ),
)
def test_routes_representative_polymarket_markets_to_strategy_teams(
    market: StrategyMarketRoutingInput,
    expected_team_id: str,
    expected_reason: str,
) -> None:
    row = route_strategy_market(market, config=StrategyTeamTaxonomyConfig())

    assert row.primary_team_id == expected_team_id
    assert row.routing_confidence.as_tuple().exponent == -6
    assert expected_reason in row.routing_reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_builds_readonly_route_report_with_deterministic_input_order() -> None:
    markets = (
        StrategyMarketRoutingInput(
            condition_id="condition-btc",
            market_slug="bitcoin-above-150k-in-2026",
            question="Will Bitcoin trade above $150,000 in 2026?",
            category_hint="finance.crypto",
            tags=("btc",),
        ),
        StrategyMarketRoutingInput(
            condition_id="condition-nba",
            market_slug="nba-finals-celtics-win",
            question="Will the Celtics win the NBA Finals?",
            category_hint="sports.basketball",
            tags=("nba",),
        ),
    )

    report = build_strategy_market_route_report(
        markets,
        config=StrategyTeamTaxonomyConfig(config_version="strategy-taxonomy-v1"),
        generated_at=GENERATED_AT,
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-taxonomy-v1"
    assert report.route_count == Decimal("2")
    assert tuple(row.market_slug for row in report.rows) == (
        "bitcoin-above-150k-in-2026",
        "nba-finals-celtics-win",
    )
    assert tuple(row.primary_team_id for row in report.rows) == ("crypto_btc", "basketball")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_decimal_inputs_and_safety_flags_are_strict() -> None:
    with pytest.raises(ValueError, match="default_routing_confidence must be a Decimal"):
        StrategyTeamProfile(
            team_id="general",
            display_name="General",
            market_scope="General cross-domain research",
            routing_keywords=("general",),
            default_routing_confidence=0.5,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="routing_confidence must be a Decimal"):
        StrategyMarketRouteRow(
            condition_id="condition-general",
            market_slug="unknown-market",
            question="Will the unknown event happen?",
            category_hint="technology",
            tags=("ai",),
            primary_team_id="general",
            routing_confidence=0.5,  # type: ignore[arg-type]
            routing_reason_codes=("default_general_fallback",),
            matched_terms=(),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        StrategyTeamTaxonomyConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        StrategyMarketRoutingInput(
            condition_id="condition-general",
            market_slug="unknown-market",
            question="Will the unknown event happen?",
            category_hint="technology",
            tags=("ai",),
            report_only=False,
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        StrategyMarketRouteReport(
            generated_at=GENERATED_AT,
            config_version="strategy-taxonomy-v1",
            route_count=Decimal("0"),
            rows=(),
            readonly=False,
        )


def test_public_dataclasses_expose_no_live_trading_surface_fields() -> None:
    unsafe_fragments = (
        "auth",
        "private_key",
        "wallet",
        "account",
        "balance",
        "order",
        "cancel",
        "replace",
        "sign",
        "exchange_mutation",
    )

    for cls in (
        StrategyTeamTaxonomyConfig,
        StrategyTeamProfile,
        StrategyMarketRoutingInput,
        StrategyMarketRouteRow,
        StrategyMarketRouteReport,
    ):
        for field in fields(cls):
            assert not any(fragment in field.name.lower() for fragment in unsafe_fragments)
