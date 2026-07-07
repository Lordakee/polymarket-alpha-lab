from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_team_routing import (
    MarketTeamRoute,
    MarketTeamRoutingInput,
    route_market_team,
    route_market_teams,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


def route_payload(
    *,
    primary_team_id: str | None = "crypto_btc",
    secondary_team_ids: tuple[str, ...] = (),
    confidence: Decimal = Decimal("0.900000"),
    status: str = "pass",
    reason_codes: tuple[str, ...] = ("pass_keyword_crypto_btc",),
    redacted_market_ref: str = "market-ref-aaaaaaaaaaaaaaaa",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketTeamRoute:
    return MarketTeamRoute(
        redacted_market_ref=redacted_market_ref,
        primary_team_id=primary_team_id,
        secondary_team_ids=secondary_team_ids,
        confidence=confidence,
        status=status,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def market(
    *,
    condition_id: str = "condition-test",
    market_slug: str = "test-market",
    question: str = "Will the test market resolve yes?",
    category: str | None = None,
    event: str | None = None,
    series: str | None = None,
    tags: tuple[str, ...] = (),
    description: str | None = None,
    rules: str | None = None,
) -> MarketTeamRoutingInput:
    return MarketTeamRoutingInput(
        condition_id=condition_id,
        market_slug=market_slug,
        question=question,
        category=category,
        event=event,
        series=series,
        tags=tags,
        description=description,
        rules=rules,
    )


@pytest.mark.parametrize(
    ("metadata", "expected_team_id", "expected_status", "expected_reason"),
    (
        (
            market(
                condition_id="condition-politics",
                market_slug="us-presidential-election-winner-2028",
                question="Will a Democrat win the 2028 US presidential election?",
                category="politics",
            ),
            "politics",
            "pass",
            "pass_category_politics",
        ),
        (
            market(
                condition_id="condition-btc",
                market_slug="bitcoin-above-150k-in-2026",
                question="Will Bitcoin trade above 150000 in 2026?",
                category="finance.crypto.btc",
                tags=("btc",),
            ),
            "crypto_btc",
            "pass",
            "pass_category_crypto_btc",
        ),
        (
            market(
                condition_id="condition-eth",
                market_slug="ethereum-above-12000-in-2026",
                question="Will ETH trade above 12000 in 2026?",
                category="finance.crypto.eth",
                tags=("ethereum",),
            ),
            "crypto_eth",
            "pass",
            "pass_category_crypto_eth",
        ),
        (
            market(
                condition_id="condition-indices",
                market_slug="sp-500-close-above-7000",
                question="Will the S&P 500 close above 7000?",
                category="finance.equity.indices",
                tags=("spx",),
            ),
            "equity_indices",
            "pass",
            "pass_category_equity_indices",
        ),
        (
            market(
                condition_id="condition-gold",
                market_slug="gold-above-3000-and-real-rates-lower",
                question="Will gold trade above 3000 after the next Fed rate cut?",
                category="finance.commodities.gold",
                tags=("xau", "rates"),
            ),
            "commodities_gold",
            "pass",
            "pass_category_commodities_gold",
        ),
        (
            market(
                condition_id="condition-oil",
                market_slug="brent-crude-above-100",
                question="Will Brent crude oil trade above 100?",
                category="finance.commodities.oil",
                tags=("opec",),
            ),
            "commodities_oil",
            "pass",
            "pass_category_commodities_oil",
        ),
        (
            market(
                condition_id="condition-football",
                market_slug="champions-league-final-real-madrid-win",
                question="Will Real Madrid win the Champions League final?",
                category="sports.soccer",
                tags=("football", "uefa"),
            ),
            "sports_soccer",
            "pass",
            "pass_category_sports_soccer",
        ),
        (
            market(
                condition_id="condition-basketball",
                market_slug="nba-finals-celtics-win",
                question="Will the Celtics win the NBA Finals?",
                category="sports.basketball",
                tags=("nba",),
            ),
            "sports_basketball",
            "pass",
            "pass_category_sports_basketball",
        ),
        (
            market(
                condition_id="condition-tennis",
                market_slug="wimbledon-mens-final-winner",
                question="Will Alcaraz win the Wimbledon final?",
                category="sports.tennis",
                tags=("tennis",),
            ),
            "sports_other",
            "pass",
            "pass_keyword_sports_other",
        ),
        (
            market(
                condition_id="condition-fallback",
                market_slug="openai-release-new-model-before-september",
                question="Will OpenAI release a new model before September?",
                category="technology",
                tags=("ai",),
            ),
            None,
            "block",
            "block_no_taxonomy_signal",
        ),
    ),
)
def test_routes_supplied_market_metadata_to_medium_scale_team_or_unroutes(
    metadata: MarketTeamRoutingInput,
    expected_team_id: str | None,
    expected_status: str,
    expected_reason: str,
) -> None:
    route = route_market_team(metadata)

    assert route.primary_team_id == expected_team_id
    if expected_team_id is not None:
        assert require_team_id("primary_team_id", route.primary_team_id) == expected_team_id
    else:
        assert route.primary_team_id is None
        assert route.confidence == Decimal("0.000000")
        assert "sports_other" not in (
            route.primary_team_id,
            *route.secondary_team_ids,
            *route.reason_codes,
        )
    assert route.secondary_team_ids == ()
    assert route.confidence.as_tuple().exponent == -6
    assert route.status == expected_status
    assert expected_reason in route.reason_codes
    assert route.paper_only is True
    assert route.report_only is True
    assert route.readonly is True
    assert "fallback_research" not in (
        route.primary_team_id,
        route.status,
        *route.reason_codes,
    )

    with pytest.raises(FrozenInstanceError):
        route.primary_team_id = "politics"  # type: ignore[misc]


def test_unrouted_markets_do_not_use_sports_other_as_general_fallback() -> None:
    routes = (
        route_market_team(
            market(
                condition_id="condition-technology",
                market_slug="openai-release-new-model-before-september",
                question="Will OpenAI release a new model before September?",
                category="technology",
                tags=("ai",),
            )
        ),
        route_market_team(
            market(
                condition_id="condition-broad-sports",
                market_slug="general-sports-market",
                question="Will the market resolve yes?",
                category="sports",
            )
        ),
        route_market_team(
            market(
                condition_id="condition-sports-unknown",
                market_slug="sports-market-without-supported-subcategory",
                question="Will the sports market resolve yes?",
                category="sports.misc",
            )
        ),
        route_market_team(
            market(
                condition_id="condition-football-ambiguous",
                market_slug="football-winner-without-league-context",
                question="Will the football club win its match?",
            )
        ),
    )

    for route in routes:
        assert route.primary_team_id is None
        assert route.secondary_team_ids == ()
        assert route.status == "block"
        assert route.confidence == Decimal("0.000000")
        assert route.reason_codes == ("block_no_taxonomy_signal",)


def test_text_metadata_routes_btc_eth_indices_gold_oil_politics_and_sports() -> None:
    routes = route_market_teams(
        (
            market(
                condition_id="condition-btc",
                market_slug="bitcoin-etf-flow-week",
                question="Will Bitcoin ETF net flow be positive this week?",
            ),
            market(
                condition_id="condition-eth",
                market_slug="eth-above-10000",
                question="Will Ethereum trade above 10000?",
            ),
            market(
                condition_id="condition-indices",
                market_slug="nasdaq-close-higher",
                question="Will Nasdaq close higher today?",
            ),
            market(
                condition_id="condition-gold",
                market_slug="xau-above-3000",
                question="Will XAU gold futures trade above 3000?",
            ),
            market(
                condition_id="condition-oil",
                market_slug="wti-crude-above-90",
                question="Will WTI crude oil trade above 90?",
            ),
            market(
                condition_id="condition-politics",
                market_slug="senate-control-after-election",
                question="Will Republicans control the Senate after the election?",
            ),
            market(
                condition_id="condition-football",
                market_slug="premier-league-title-winner",
                question="Will Arsenal win the Premier League?",
            ),
            market(
                condition_id="condition-basketball",
                market_slug="lakers-win-playoff-series",
                question="Will the Lakers win the NBA playoff series?",
            ),
        )
    )

    assert tuple(route.primary_team_id for route in routes) == (
        "sports_basketball",
        "crypto_btc",
        "crypto_eth",
        "sports_soccer",
        "commodities_gold",
        "equity_indices",
        "commodities_oil",
        "politics",
    )
    assert all(route.status == "pass" for route in routes)


def test_ambiguous_team_matches_are_held_without_public_candidate_ids() -> None:
    route = route_market_team(
        market(
            condition_id="condition-ambiguous",
            market_slug="bitcoin-ethereum-nasdaq-fed-election-oil-gold",
            question="Will Bitcoin and Ethereum outperform the Nasdaq if the Fed cuts rates after the election while oil and gold rally?",
            tags=("eth", "btc", "spx", "fomc", "election", "wti", "xau"),
        )
    )

    assert route.primary_team_id is None
    assert route.secondary_team_ids == ()
    assert route.status == "watch"
    assert route.confidence == Decimal("0.000000")
    assert route.reason_codes == (
        "watch_multiple_taxonomy_signals",
    )

    repeated = tuple(
        route_market_team(
            market(
                condition_id="condition-ambiguous",
                market_slug="oil-gold-election-fed-nasdaq-ethereum-bitcoin",
                question="Will Bitcoin and Ethereum outperform the Nasdaq if the Fed cuts rates after the election while oil and gold rally?",
                tags=("xau", "wti", "election", "fomc", "spx", "eth", "btc"),
            )
        ).reason_codes
        for _ in range(3)
    )
    assert repeated == (
            (
                "watch_multiple_taxonomy_signals",
            ),
            (
                "watch_multiple_taxonomy_signals",
            ),
            (
                "watch_multiple_taxonomy_signals",
            ),
    )


def test_unsafe_terms_rejection_and_paper_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="unsafe live surface term"):
        route_market_team(
            market(
                market_slug="wallet-account-check",
                question="Will account wallet balance be enough to sign an order?",
            )
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        MarketTeamRoutingInput(
            condition_id="condition-btc",
            market_slug="bitcoin-above-150k",
            question="Will Bitcoin trade above 150000?",
            paper_only=False,
        )

    with pytest.raises(ValueError, match="report_only must be True"):
        route_payload(report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        route_payload(readonly=False)


def test_no_forbidden_live_execution_surface_fields() -> None:
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

    for cls in (MarketTeamRoutingInput, MarketTeamRoute):
        for field in fields(cls):
            assert not any(fragment in field.name.lower() for fragment in unsafe_fragments)


def test_input_validation_uses_decimal_confidence_known_teams_and_deterministic_sorting() -> None:
    with pytest.raises(ValueError, match="confidence must be a Decimal"):
        route_payload(confidence=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="confidence must be positive when status is pass"):
        route_payload(confidence=Decimal("0.000000"))

    with pytest.raises(ValueError, match="primary_team_id must be a known team"):
        route_payload(primary_team_id="research")

    with pytest.raises(ValueError, match="primary_team_id must be a known team"):
        route_payload(
            primary_team_id="fallback_research",
            status="block",
            reason_codes=("block_no_taxonomy_signal",),
            confidence=Decimal("0.000000"),
        )

    with pytest.raises(ValueError, match="secondary_team_ids must be empty"):
        route_payload(
            secondary_team_ids=("crypto_eth",),
        )

    with pytest.raises(ValueError, match="primary_team_id is required when status is pass"):
        route_payload(primary_team_id=None)

    with pytest.raises(ValueError, match="primary_team_id must be None when status is watch or block"):
        route_payload(
            status="watch",
            reason_codes=("watch_multiple_taxonomy_signals",),
            confidence=Decimal("0.000000"),
        )

    with pytest.raises(ValueError, match="secondary_team_ids must be empty"):
        route_payload(
            primary_team_id=None,
            secondary_team_ids=("crypto_eth",),
            status="block",
            reason_codes=("block_no_taxonomy_signal",),
            confidence=Decimal("0.000000"),
        )

    with pytest.raises(ValueError, match="confidence must be zero when status is watch or block"):
        route_payload(
            primary_team_id=None,
            status="block",
            reason_codes=("block_no_taxonomy_signal",),
        )

    routes = route_market_teams(
        (
            market(
                condition_id="condition-z",
                market_slug="lakers-win-finals",
                question="Will the Lakers win the NBA Finals?",
            ),
            market(
                condition_id="condition-a",
                market_slug="bitcoin-above-150k",
                question="Will Bitcoin trade above 150000?",
            ),
            market(
                condition_id="condition-m",
                market_slug="gold-above-3000",
                question="Will gold trade above 3000?",
            ),
        )
    )

    assert tuple(route.primary_team_id for route in routes) == (
        "crypto_btc",
        "commodities_gold",
        "sports_basketball",
    )
    assert tuple(route.redacted_market_ref for route in routes) == (
        "market-ref-0000000000000001",
        "market-ref-0000000000000002",
        "market-ref-0000000000000003",
    )


def test_public_route_status_vocabulary_uses_pass_watch_block() -> None:
    assert route_payload(status="pass").status == "pass"
    assert route_payload(
        primary_team_id=None,
        confidence=Decimal("0.000000"),
        status="watch",
        reason_codes=("watch_multiple_taxonomy_signals",),
    ).status == "watch"
    assert route_payload(
        primary_team_id=None,
        confidence=Decimal("0.000000"),
        status="block",
        reason_codes=("block_no_taxonomy_signal",),
    ).status == "block"

    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        route_payload(status="blocked")


@pytest.mark.parametrize(
    "reason_code",
    (
        "raw_candidate_id_candidate_123",
        "secondary_team_crypto_eth",
        "market_slug_private_market",
        "source_ref_https_example_com",
        "dsn_postgres_table_routes",
        "private_token_present",
        "buy_sell_recommendation",
        "position_sizing_hint",
        "matched_status_leak",
        "ambiguous_status_leak",
        "unrouted_status_leak",
        "blocked_status_leak",
    ),
)
def test_public_route_reason_codes_reject_disallowed_payload_terms(
    reason_code: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public route reason code"):
        route_payload(reason_codes=(reason_code,))


def test_public_route_payload_uses_report_local_refs_without_market_digests() -> None:
    source_market = market(
        condition_id="condition-private-123",
        market_slug="private-market-slug",
        question="Will this private raw question be hidden?",
        category="politics",
        tags=("private-tag",),
    )

    route = route_market_team(source_market)
    route_field_names = {field.name for field in fields(MarketTeamRoute)}

    assert "condition_id" not in route_field_names
    assert "market_slug" not in route_field_names
    assert "question" not in route_field_names
    assert "market_digest" not in route_field_names
    assert route.redacted_market_ref.startswith("market-ref-")
    assert len(route.redacted_market_ref) == len("market-ref-") + 16
    assert route.redacted_market_ref == "market-ref-0000000000000001"

    public_payload_text = repr(tuple(getattr(route, field.name) for field in fields(route)))
    assert source_market.condition_id not in public_payload_text
    assert source_market.market_slug not in public_payload_text
    assert source_market.question not in public_payload_text
    assert "sha256:" not in public_payload_text

    report_routes = route_market_teams(
        (
            source_market,
            market(
                condition_id="condition-alpha",
                market_slug="bitcoin-report-local-sequence",
                question="Will Bitcoin trade above 150000?",
            ),
        )
    )

    assert tuple(route.redacted_market_ref for route in report_routes) == (
        "market-ref-0000000000000001",
        "market-ref-0000000000000002",
    )
    assert report_routes[1].primary_team_id == "politics"
    assert report_routes[1].redacted_market_ref != route.redacted_market_ref
