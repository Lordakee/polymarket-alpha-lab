from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_event_type_router import (
    ResearchMarketEventTypeInput,
    ResearchMarketEventTypeRoute,
    ResearchMarketEventTypeRouterConfig,
    research_market_event_type_router_payload,
    route_research_market_event_type,
)


def event(**overrides: object) -> ResearchMarketEventTypeInput:
    values = {
        "public_event_type": "bitcoin_etf_flow",
        "public_category_hint": "finance.crypto",
        "public_feature_tags": ("bitcoin", "etf"),
    }
    values.update(overrides)
    return ResearchMarketEventTypeInput(**values)


def route(value: ResearchMarketEventTypeInput | None = None) -> ResearchMarketEventTypeRoute:
    return route_research_market_event_type(value if value is not None else event())


def assert_no_float_int_or_unsafe_surface(value: Any) -> None:
    unsafe_key_fragments = (
        "raw",
        "candidate",
        "condition",
        "market",
        "slug",
        "question",
        "source",
        "ref",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    unsafe_value_terms = (
        "raw",
        "candidate id",
        "market id",
        "market slug",
        "question",
        "source ref",
        "source url",
        "source text",
        "http://",
        "https://",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert not any(fragment in key.casefold() for fragment in unsafe_key_fragments)
            assert_no_float_int_or_unsafe_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_int_or_unsafe_surface(item)
        return
    assert not isinstance(value, float)
    if type(value) is int:
        raise AssertionError("public payload must not contain ints")
    if type(value) is str:
        lowered = value.casefold()
        assert not any(term in lowered for term in unsafe_value_terms)


@pytest.mark.parametrize(
    ("sample", "expected_queue", "expected_reason"),
    (
        (
            event(
                public_event_type="election_turnout",
                public_category_hint="politics.elections",
                public_feature_tags=("president",),
            ),
            "politics",
            "pass_category_politics",
        ),
        (
            event(
                public_event_type="inflation_release",
                public_category_hint="finance.macro.rates",
                public_feature_tags=("cpi", "fed"),
            ),
            "macro",
            "pass_category_macro",
        ),
        (
            event(),
            "crypto",
            "pass_category_crypto",
        ),
        (
            event(
                public_event_type="index_close",
                public_category_hint="finance.equity.indices",
                public_feature_tags=("spx",),
            ),
            "equities",
            "pass_category_equities",
        ),
        (
            event(
                public_event_type="gold_fixing",
                public_category_hint="finance.commodities.gold",
                public_feature_tags=("xau",),
            ),
            "metals",
            "pass_category_metals",
        ),
        (
            event(
                public_event_type="champions_league_result",
                public_category_hint="sports.football",
                public_feature_tags=("football", "uefa"),
            ),
            "football",
            "pass_category_football",
        ),
        (
            event(
                public_event_type="nba_finals_result",
                public_category_hint="sports.basketball",
                public_feature_tags=("nba",),
            ),
            "basketball",
            "pass_category_basketball",
        ),
    ),
)
def test_routes_clear_sanitized_event_types_to_team_queues(
    sample: ResearchMarketEventTypeInput,
    expected_queue: str,
    expected_reason: str,
) -> None:
    result = route(sample)
    payload = research_market_event_type_router_payload(result)

    assert result.team_queue_id == expected_queue
    assert result.route_status == "pass"
    assert result.route_confidence == Decimal("0.920000")
    assert result.reason_codes == (expected_reason,)
    assert payload["team_queue_id"] == expected_queue
    assert payload["route_confidence"] == "0.920000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_int_or_unsafe_surface(payload)


def test_routes_fuzzy_multi_signal_event_to_watch_without_queue_assignment() -> None:
    result = route(
        event(
            public_event_type="inflation_bitcoin_cross_signal",
            public_category_hint="public.unspecified",
            public_feature_tags=("bitcoin", "inflation"),
        ),
    )

    assert result.team_queue_id is None
    assert result.route_status == "watch"
    assert result.route_confidence == Decimal("0.000000")
    assert result.reason_codes == ("watch_multiple_public_signals",)


def test_routes_unknown_sanitized_event_to_block_without_queue_assignment() -> None:
    result = route(
        event(
            public_event_type="entertainment_release_window",
            public_category_hint="culture.general",
            public_feature_tags=("streaming",),
        ),
    )

    assert result.team_queue_id is None
    assert result.route_status == "block"
    assert result.route_confidence == Decimal("0.000000")
    assert result.reason_codes == ("block_no_public_signal",)


def test_type_validation_rejects_non_strict_inputs_and_tampered_outputs() -> None:
    with pytest.raises(ValueError, match="event must be a ResearchMarketEventTypeInput"):
        route_research_market_event_type("crypto")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public_feature_tags must be a tuple"):
        event(public_feature_tags=["bitcoin"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public_event_type must contain canonical strings"):
        event(public_event_type=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="route_confidence must be exactly Decimal"):
        ResearchMarketEventTypeRoute(
            config_version="research-event-type-router-v1",
            public_event_type="bitcoin_etf_flow",
            public_category_hint="finance.crypto",
            public_feature_tags=("bitcoin",),
            team_queue_id="crypto",
            route_status="pass",
            route_confidence=0.86,  # type: ignore[arg-type]
            reason_codes=("pass_category_crypto",),
        )
    with pytest.raises(ValueError, match="team_queue_id must match routed event features"):
        replace(route(), team_queue_id="macro")


def test_rejects_public_payload_leaks_and_unsafe_sanitized_values() -> None:
    for overrides in (
        {"public_event_type": "raw candidate id abc"},
        {"public_event_type": "market id abc"},
        {"public_category_hint": "source ref official"},
        {"public_feature_tags": ("https://example.test/path",)},
        {"public_feature_tags": ("wallet auth token",)},
        {"public_feature_tags": ("buy recommendation",)},
        {"public_feature_tags": ("open position",)},
        {"public_feature_tags": ("orders table",)},
    ):
        with pytest.raises(ValueError, match="unsafe public value"):
            event(**overrides)

    with pytest.raises(ValueError, match="unsafe public field"):
        research_market_event_type_router_payload(
            {
                "market_id": "abc",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        research_market_event_type_router_payload(
            {
                "public_event_type": "source text leaked",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_dataclasses_are_frozen_and_hard_flags_cannot_be_downgraded() -> None:
    config = ResearchMarketEventTypeRouterConfig()
    sample = event()
    result = route(sample)

    for item in (config, sample, result):
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in {"paper_only", "report_only", "readonly"}:
                assert getattr(item, field.name) is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(sample, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        research_market_event_type_router_payload(
            {
                "config_version": "research-event-type-router-v1",
                "paper_only": False,
                "report_only": True,
                "readonly": True,
            },
        )


def test_route_output_is_deterministic_and_json_ready() -> None:
    sample = event(
        public_event_type="spx_close",
        public_category_hint="public.unspecified",
        public_feature_tags=("nasdaq", "spx", "spx"),
    )

    first = route(sample)
    second = route(sample)
    first_payload = research_market_event_type_router_payload(first)
    second_payload = research_market_event_type_router_payload(second)

    assert first == second
    assert first_payload == second_payload
    assert first.team_queue_id == "equities"
    assert first.route_status == "pass"
    assert first.reason_codes == ("pass_feature_equities",)
    assert first.public_feature_tags == ("nasdaq", "spx")
    assert_no_float_int_or_unsafe_surface(first_payload)
