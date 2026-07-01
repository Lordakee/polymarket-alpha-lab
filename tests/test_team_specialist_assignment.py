from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
from pathlib import Path

import pytest

import polymarket_alpha_lab as lab
from polymarket_alpha_lab.team_market_router import TeamMarketRouteReport


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _IntSubclass(int):
    pass


def config(**overrides: object) -> TeamSpecialistAssignmentConfig:
    values = {"config_version": "team-specialist-assignment-v0"}
    values.update(overrides)
    module = importlib.import_module("polymarket_alpha_lab.team_specialist_assignment")
    return module.TeamSpecialistAssignmentConfig(**values)


def market(**overrides: object) -> TeamSpecialistMarketMetadata:
    values = {
        "condition_id": "condition-alpha",
        "market_slug": "neutral-market",
        "question": "Will the neutral market resolve yes?",
    }
    values.update(overrides)
    module = importlib.import_module("polymarket_alpha_lab.team_specialist_assignment")
    return module.TeamSpecialistMarketMetadata(**values)


def report(
    markets: tuple[TeamSpecialistMarketMetadata, ...],
    *,
    cfg: TeamSpecialistAssignmentConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> TeamMarketRouteReport:
    module = importlib.import_module("polymarket_alpha_lab.team_specialist_assignment")
    return module.build_team_specialist_assignment_report(
        markets,
        config=cfg or config(),
        generated_at=generated_at,
    )


@pytest.mark.parametrize(
    ("category", "expected_team_id"),
    (
        ("politics", "politics"),
        ("finance.crypto.btc", "crypto_btc"),
        ("finance.crypto.eth", "crypto_eth"),
        ("finance.macro.rates", "macro_rates"),
        ("finance.equity.indices", "equity_indices"),
        ("finance.commodities.gold", "commodities_gold"),
        ("finance.commodities.oil", "commodities_oil"),
        ("sports.soccer", "sports_soccer"),
        ("sports.basketball", "sports_basketball"),
        ("sports.other", "sports_other"),
    ),
)
def test_assignment_routes_known_taxonomy_categories_for_all_specialist_teams(
    category: str,
    expected_team_id: str,
) -> None:
    assignment = report(
        (
            market(
                category=category,
                event="Category route smoke test",
            ),
        ),
    )

    row = assignment.rows[0]
    assert assignment.generated_at == GENERATED_AT
    assert assignment.generated_at.tzinfo is UTC
    assert assignment.config_version == "team-specialist-assignment-v0"
    assert assignment.route_count == 1
    assert assignment.paper_only is True
    assert assignment.report_only is True
    assert assignment.readonly is True
    assert row.category_id == category
    assert row.event_template == "Category route smoke test"
    assert row.primary_team_id == expected_team_id
    assert row.secondary_team_ids == ()
    assert row.routing_confidence == Decimal("0.900000")
    assert row.routing_confidence.as_tuple().exponent == -6
    assert "primary_source_category" in row.routing_reason_codes


def test_assignment_uses_metadata_precedence_and_capped_unique_secondaries() -> None:
    assignment = report(
        (
            market(
                category="finance.crypto.btc",
                question=(
                    "Will Ethereum outperform Bitcoin if Fed rate cuts lift "
                    "the S&P 500?"
                ),
                description="Gold and Brent crude oil are also relevant macro hedges.",
            ),
        ),
        cfg=config(max_secondary_team_ids=2),
    )

    row = assignment.rows[0]
    assert row.primary_team_id == "crypto_btc"
    assert row.category_id == "finance.crypto.btc"
    assert row.secondary_team_ids == ("crypto_eth", "macro_rates")
    assert row.primary_team_id not in row.secondary_team_ids
    assert len(row.secondary_team_ids) == len(set(row.secondary_team_ids))
    assert len(row.secondary_team_ids) == 2
    assert "primary_source_category" in row.routing_reason_codes
    assert "secondary_team_crypto_eth" in row.routing_reason_codes
    assert "secondary_team_macro_rates" in row.routing_reason_codes


@pytest.mark.parametrize(
    ("overrides", "expected_team_id", "expected_source_reason"),
    (
        ({"tag": "BTC"}, "crypto_btc", "primary_source_tag"),
        ({"event": "Ethereum Dencun upgrade"}, "crypto_eth", "primary_source_event"),
        ({"series": "FOMC rate cut probabilities"}, "macro_rates", "primary_source_series"),
        (
            {"market_slug": "sp500-above-6000-by-year-end"},
            "equity_indices",
            "primary_source_market_slug",
        ),
        ({"question": "Will gold close above 2500?"}, "commodities_gold", "primary_source_question"),
        (
            {"description": "Settlement follows Brent crude oil futures."},
            "commodities_oil",
            "primary_source_description",
        ),
    ),
)
def test_assignment_routes_from_each_supported_metadata_source(
    overrides: dict[str, object],
    expected_team_id: str,
    expected_source_reason: str,
) -> None:
    row = report((market(**overrides),)).rows[0]

    assert row.primary_team_id == expected_team_id
    assert expected_source_reason in row.routing_reason_codes
    assert row.routing_confidence == Decimal("0.900000")


def test_assignment_routes_unknown_sport_to_sports_other_with_lower_confidence() -> None:
    row = report(
        (
            market(
                category="sports.unknown.curling",
                question="Will the home rink win the championship?",
            ),
        ),
    ).rows[0]

    assert row.category_id == "sports.other"
    assert row.primary_team_id == "sports_other"
    assert row.secondary_team_ids == ()
    assert row.routing_confidence == Decimal("0.700000")
    assert "sports_unknown_fallback" in row.routing_reason_codes


def test_assignment_rejects_unknown_non_sports_markets() -> None:
    with pytest.raises(ValueError, match="known specialist route"):
        report(
            (
                market(
                    category="entertainment",
                    question="Will the album be released in July?",
                    description="A music release market with no supported specialist team.",
                ),
            ),
        )


def test_assignment_false_positive_guards_for_gold_football_and_oil_change() -> None:
    golden_state = report(
        (
            market(
                question="Will Golden State Warriors win the NBA Finals?",
            ),
        ),
    ).rows[0]
    assert golden_state.primary_team_id == "sports_basketball"
    assert "commodities_gold" not in golden_state.secondary_team_ids

    football = report(
        (
            market(
                category="sports.unknown.football",
                question="Will the football team win the championship?",
            ),
        ),
    ).rows[0]
    assert football.primary_team_id == "sports_other"
    assert football.primary_team_id != "sports_soccer"
    assert football.routing_confidence == Decimal("0.700000")

    soccer_specific = report(
        (
            market(
                event="UEFA Champions League football final",
                question="Will the home football club win?",
            ),
        ),
    ).rows[0]
    assert soccer_specific.primary_team_id == "sports_soccer"

    with pytest.raises(ValueError, match="known specialist route"):
        report(
            (
                market(
                    category="automotive",
                    market_slug="oil-change-promotion-under-40",
                    question="Will the oil change promotion cost under 40 dollars?",
                    description="Auto shop service pricing market.",
                ),
            ),
        )


def test_assignment_validates_flags_inputs_config_and_generated_at() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        market(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="max_secondary_team_ids"):
        config(max_secondary_team_ids=-1)
    with pytest.raises(ValueError, match="max_secondary_team_ids"):
        config(max_secondary_team_ids=_IntSubclass(1))
    with pytest.raises(ValueError, match="description"):
        market(description="")
    with pytest.raises(ValueError, match="config"):
        module = importlib.import_module("polymarket_alpha_lab.team_specialist_assignment")
        module.build_team_specialist_assignment_report(
            (market(category="politics"),),
            config="bad",  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="markets"):
        module = importlib.import_module("polymarket_alpha_lab.team_specialist_assignment")
        module.build_team_specialist_assignment_report(
            "bad",  # type: ignore[arg-type]
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="markets"):
        module = importlib.import_module("polymarket_alpha_lab.team_specialist_assignment")
        module.build_team_specialist_assignment_report(
            (object(),),  # type: ignore[arg-type]
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report((market(category="politics"),), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (market(category="politics"),),
            generated_at=_DatetimeSubclass(2026, 7, 1, 12, 0, tzinfo=UTC),
        )

    shifted = report(
        (market(category="politics"),),
        generated_at=datetime(2026, 7, 1, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    assert shifted.generated_at == GENERATED_AT
    assert shifted.generated_at.tzinfo is UTC


def test_assignment_module_is_pure_and_api_is_module_local() -> None:
    module = importlib.import_module("polymarket_alpha_lab.team_specialist_assignment")

    assert module.__all__ == (
        "TeamSpecialistAssignmentConfig",
        "TeamSpecialistMarketMetadata",
        "build_team_specialist_assignment_report",
    )
    assert not hasattr(lab, "TeamSpecialistAssignmentConfig")
    assert not hasattr(lab, "TeamSpecialistMarketMetadata")
    assert not hasattr(lab, "build_team_specialist_assignment_report")

    source = Path("src/polymarket_alpha_lab/team_specialist_assignment.py").read_text(
        encoding="utf-8",
    )
    lower_source = source.lower()
    for banned in (
        "psycopg",
        "sqlalchemy",
        "supabase",
        "requests",
        "httpx",
        "urllib",
        "strategy",
        "allocation",
        "memory",
        "candidate",
        "team_forecast",
        "private_key",
        "wallet",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live_trading",
    ):
        assert banned not in lower_source
