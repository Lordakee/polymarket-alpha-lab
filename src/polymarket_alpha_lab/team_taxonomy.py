"""Paper-only domain team taxonomy for specialist forecast workflows."""

from __future__ import annotations

from dataclasses import dataclass


TEAM_IDS = (
    "politics",
    "crypto_btc",
    "crypto_eth",
    "macro_rates",
    "equity_indices",
    "commodities_gold",
    "commodities_oil",
    "sports_soccer",
    "sports_basketball",
    "sports_other",
)

TEAM_CATEGORIES = (
    "politics",
    "finance.crypto.btc",
    "finance.crypto.eth",
    "finance.macro.rates",
    "finance.equity.indices",
    "finance.commodities.gold",
    "finance.commodities.oil",
    "sports.soccer",
    "sports.basketball",
    "sports.other",
)

TEAM_ID_TO_PRIMARY_CATEGORY = dict(zip(TEAM_IDS, TEAM_CATEGORIES, strict=True))


@dataclass(frozen=True)
class TeamProfile:
    team_id: str
    display_name: str
    primary_categories: tuple[str, ...]
    agent_roles: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("display_name", self.display_name)
        categories = _normalize_categories(self.primary_categories)
        for category_id in categories:
            require_team_category_pair("team_id", self.team_id, "category_id", category_id)
        object.__setattr__(self, "primary_categories", categories)
        object.__setattr__(
            self,
            "agent_roles",
            _normalize_string_tuple("agent_roles", self.agent_roles),
        )
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_default_team_profiles() -> tuple[TeamProfile, ...]:
    return tuple(
        TeamProfile(
            team_id=team_id,
            display_name=display_name,
            primary_categories=categories,
            agent_roles=agent_roles,
        )
        for team_id, display_name, categories, agent_roles in (
            (
                "politics",
                "Politics",
                ("politics",),
                (
                    "politics_lead_forecaster",
                    "polling_fundamentals",
                    "news_event_shock",
                    "electoral_rules_resolution",
                    "political_base_rate_modeler",
                    "politics_memory_postmortem",
                ),
            ),
            (
                "crypto_btc",
                "Crypto BTC",
                ("finance.crypto.btc",),
                (
                    "btc_lead_forecaster",
                    "spot_derivatives",
                    "etf_flow",
                    "volatility_path_modeler",
                    "btc_market_context",
                    "btc_memory_postmortem",
                ),
            ),
            (
                "crypto_eth",
                "Crypto ETH",
                ("finance.crypto.eth",),
                (
                    "eth_lead_forecaster",
                    "eth_relative_value",
                    "etf_staking_ecosystem",
                    "eth_volatility_market_context",
                    "eth_memory_postmortem",
                ),
            ),
            (
                "macro_rates",
                "Macro Rates",
                ("finance.macro.rates",),
                (
                    "macro_lead_forecaster",
                    "economic_calendar",
                    "rates_fed_pricing",
                    "data_surprise_modeler",
                    "macro_resolution",
                    "macro_memory_postmortem",
                ),
            ),
            (
                "equity_indices",
                "Equity Indices",
                ("finance.equity.indices",),
                (
                    "index_lead_forecaster",
                    "futures_breadth",
                    "earnings_event_calendar",
                    "index_volatility_path",
                    "index_memory_postmortem",
                ),
            ),
            (
                "commodities_gold",
                "Commodities Gold",
                ("finance.commodities.gold",),
                (
                    "gold_lead_forecaster",
                    "real_rates_usd",
                    "inflation_geopolitical",
                    "gold_volatility_market_context",
                    "gold_memory_postmortem",
                ),
            ),
            (
                "commodities_oil",
                "Commodities Oil",
                ("finance.commodities.oil",),
                (
                    "oil_lead_forecaster",
                    "supply_opec",
                    "inventory_demand",
                    "oil_volatility_market_context",
                    "oil_memory_postmortem",
                ),
            ),
            (
                "sports_soccer",
                "Sports Soccer",
                ("sports.soccer",),
                (
                    "soccer_lead_forecaster",
                    "team_strength_form",
                    "lineup_injury",
                    "odds_consensus",
                    "tournament_rules",
                    "soccer_memory_postmortem",
                ),
            ),
            (
                "sports_basketball",
                "Sports Basketball",
                ("sports.basketball",),
                (
                    "basketball_lead_forecaster",
                    "team_strength_matchup",
                    "injury_rotation",
                    "schedule_fatigue",
                    "odds_market_context",
                    "basketball_memory_postmortem",
                ),
            ),
            (
                "sports_other",
                "Sports Other",
                ("sports.other",),
                (
                    "other_sports_lead_forecaster",
                    "sport_specific_scout",
                    "odds_market_context",
                    "other_sports_memory_risk",
                ),
            ),
        )
    )


def require_team_id(field_name: str, value: object) -> str:
    if type(value) is not str or value not in TEAM_IDS:
        raise ValueError(f"{field_name} must be a known team")
    return value


def require_category_id(field_name: str, value: object) -> str:
    if type(value) is not str or value not in TEAM_CATEGORIES:
        raise ValueError(f"{field_name} must be a known category")
    return value


def require_team_category_pair(
    team_field_name: str,
    team_value: object,
    category_field_name: str,
    category_value: object,
) -> tuple[str, str]:
    team_id = require_team_id(team_field_name, team_value)
    category_id = require_category_id(category_field_name, category_value)
    if TEAM_ID_TO_PRIMARY_CATEGORY[team_id] != category_id:
        raise ValueError(f"{category_field_name} must match {team_field_name}")
    return team_id, category_id


def _normalize_categories(value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("primary_categories must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("primary_categories must be an iterable") from exc
    if not items:
        raise ValueError("primary_categories must contain at least one category")
    return tuple(require_category_id("category_id", item) for item in items)


def _normalize_string_tuple(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain canonical strings")
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical strings")


__all__ = (
    "TEAM_CATEGORIES",
    "TEAM_IDS",
    "TEAM_ID_TO_PRIMARY_CATEGORY",
    "TeamProfile",
    "build_default_team_profiles",
    "require_category_id",
    "require_team_category_pair",
    "require_team_id",
)
