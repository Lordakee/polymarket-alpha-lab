"""Pure deterministic specialist team assignment from market metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import re
from typing import Any

from polymarket_alpha_lab.team_market_router import (
    CATEGORY_TO_PRIMARY_TEAM,
    DEFAULT_ROUTING_CONFIDENCE,
    SPORTS_UNKNOWN_ROUTING_CONFIDENCE,
    TeamMarketRouteReport,
    TeamMarketRouteRow,
)
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


_CATEGORY_BY_TEAM_ID = {
    team_id: category_id for category_id, team_id in CATEGORY_TO_PRIMARY_TEAM.items()
}

_SOURCE_PRIORITY = (
    "category",
    "tag",
    "event",
    "series",
    "market_slug",
    "question",
    "description",
)

_TEAM_RULE_ORDER = (
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

_TEAM_RULES = {
    "politics": (
        "election",
        "president",
        "senate",
        "congress",
        "governor",
        "mayor",
        "politics",
        "white house",
        "democrat",
        "republican",
        "trump",
        "biden",
    ),
    "crypto_btc": (
        "bitcoin",
        "btc",
        "satoshi",
    ),
    "crypto_eth": (
        "ethereum",
        "ether",
        "eth",
        "dencun",
    ),
    "macro_rates": (
        "fomc",
        "fed",
        "federal reserve",
        "interest rate",
        "rate cut",
        "rate hike",
        "rates",
        "cpi",
        "inflation",
        "jobs report",
        "treasury yield",
        "central bank",
    ),
    "equity_indices": (
        "s p 500",
        "sp500",
        "nasdaq",
        "dow jones",
        "russell 2000",
        "equity index",
        "stock index",
        "spy",
        "qqq",
    ),
    "commodities_gold": (
        "gold",
        "gold futures",
        "xau",
        "precious metal",
    ),
    "commodities_oil": (
        "brent",
        "wti",
        "crude",
        "crude oil",
        "oil",
        "oil futures",
        "opec",
        "barrel",
    ),
    "sports_soccer": (
        "soccer",
        "uefa",
        "fifa",
        "champions league",
        "premier league",
        "la liga",
        "serie a",
        "bundesliga",
        "mls",
        "world cup",
        "europa league",
        "copa",
    ),
    "sports_basketball": (
        "basketball",
        "nba",
        "wnba",
        "ncaa basketball",
        "march madness",
        "warriors",
        "lakers",
        "celtics",
        "knicks",
        "nuggets",
        "mavericks",
        "bucks",
        "heat",
        "sixers",
        "bulls",
    ),
    "sports_other": (
        "tennis",
        "baseball",
        "nfl",
        "football",
        "american football",
        "hockey",
        "golf",
        "mma",
        "ufc",
        "boxing",
        "cricket",
        "rugby",
        "curling",
        "formula 1",
        "f1",
        "nascar",
        "motorsport",
        "olympics",
        "volleyball",
    ),
}

_TEAM_RULE_INDEX = {team_id: index for index, team_id in enumerate(_TEAM_RULE_ORDER)}

_OIL_SERVICE_CONTEXT = (
    "oil change",
    "auto shop",
    "car service",
    "automotive",
)

_OIL_COMMODITY_CONTEXT = (
    "brent",
    "wti",
    "crude",
    "opec",
    "barrel",
    "oil futures",
)


@dataclass(frozen=True)
class TeamSpecialistMarketMetadata:
    condition_id: str
    market_slug: str
    question: str
    category: str | None = None
    event: str | None = None
    series: str | None = None
    tag: str | None = None
    description: str | None = None
    rules: str | None = None
    resolution: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        for field_name in (
            "category",
            "event",
            "series",
            "tag",
            "description",
            "rules",
            "resolution",
        ):
            _require_optional_canonical_string(field_name, getattr(self, field_name))
        require_paper_only_flags("TeamSpecialistMarketMetadata", self)


@dataclass(frozen=True)
class TeamSpecialistAssignmentConfig:
    config_version: str
    max_secondary_team_ids: int = 2
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if type(self.max_secondary_team_ids) is not int:
            raise ValueError("max_secondary_team_ids must be an int")
        if self.max_secondary_team_ids < 0:
            raise ValueError("max_secondary_team_ids must be nonnegative")
        require_paper_only_flags("TeamSpecialistAssignmentConfig", self)


@dataclass(frozen=True)
class _TextMatch:
    team_id: str
    position: int


@dataclass(frozen=True)
class _PrimaryRoute:
    category_id: str
    team_id: str
    confidence: Decimal
    source_reason_code: str
    fallback_reason_code: str | None = None


def build_team_specialist_assignment_report(
    markets: tuple[TeamSpecialistMarketMetadata, ...] | list[TeamSpecialistMarketMetadata],
    *,
    config: TeamSpecialistAssignmentConfig,
    generated_at: datetime,
) -> TeamMarketRouteReport:
    if type(config) is not TeamSpecialistAssignmentConfig:
        raise ValueError("config must be a TeamSpecialistAssignmentConfig")
    source_markets = _normalize_markets(markets)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(_route_market(market, config=config) for market in source_markets)
    return TeamMarketRouteReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        route_count=len(rows),
        rows=rows,
    )


def _route_market(
    market: TeamSpecialistMarketMetadata,
    *,
    config: TeamSpecialistAssignmentConfig,
) -> TeamMarketRouteRow:
    primary_route = _primary_route(market)
    secondary_team_ids = _secondary_team_ids(
        market,
        primary_team_id=primary_route.team_id,
        max_secondary_team_ids=config.max_secondary_team_ids,
    )
    return TeamMarketRouteRow(
        condition_id=market.condition_id,
        market_slug=market.market_slug,
        question=market.question,
        category_id=primary_route.category_id,
        event_template=_event_template(market),
        primary_team_id=primary_route.team_id,
        secondary_team_ids=secondary_team_ids,
        routing_confidence=primary_route.confidence,
        routing_reason_codes=_routing_reason_codes(primary_route, secondary_team_ids),
    )


def _primary_route(market: TeamSpecialistMarketMetadata) -> _PrimaryRoute:
    category_route = _route_from_category(market.category)
    if category_route is not None:
        return category_route

    for source_name in _SOURCE_PRIORITY[1:]:
        matches = _matches_for_text(_source_value(market, source_name))
        if matches:
            return _primary_from_team_id(
                matches[0].team_id,
                source_reason_code=f"primary_source_{source_name}",
            )
    raise ValueError("market metadata must resolve to a known specialist route")


def _route_from_category(category: str | None) -> _PrimaryRoute | None:
    if category is None:
        return None
    if category in CATEGORY_TO_PRIMARY_TEAM:
        return _PrimaryRoute(
            category_id=category,
            team_id=CATEGORY_TO_PRIMARY_TEAM[category],
            confidence=DEFAULT_ROUTING_CONFIDENCE,
            source_reason_code="primary_source_category",
        )

    matches = _matches_for_text(category)
    if matches:
        return _primary_from_team_id(
            matches[0].team_id,
            source_reason_code="primary_source_category",
        )
    if _is_sports_category(category):
        return _PrimaryRoute(
            category_id="sports.other",
            team_id="sports_other",
            confidence=SPORTS_UNKNOWN_ROUTING_CONFIDENCE,
            source_reason_code="primary_source_category",
            fallback_reason_code="sports_unknown_fallback",
        )
    raise ValueError("market metadata must resolve to a known specialist route")


def _primary_from_team_id(team_id: str, *, source_reason_code: str) -> _PrimaryRoute:
    fallback_reason_code = None
    confidence = DEFAULT_ROUTING_CONFIDENCE
    if team_id == "sports_other":
        confidence = SPORTS_UNKNOWN_ROUTING_CONFIDENCE
        fallback_reason_code = "sports_unknown_fallback"
    return _PrimaryRoute(
        category_id=_CATEGORY_BY_TEAM_ID[team_id],
        team_id=team_id,
        confidence=confidence,
        source_reason_code=source_reason_code,
        fallback_reason_code=fallback_reason_code,
    )


def _secondary_team_ids(
    market: TeamSpecialistMarketMetadata,
    *,
    primary_team_id: str,
    max_secondary_team_ids: int,
) -> tuple[str, ...]:
    secondary_team_ids: list[str] = []
    for source_name in _SOURCE_PRIORITY:
        for match in _matches_for_source(market, source_name):
            if match.team_id == primary_team_id:
                continue
            if match.team_id in secondary_team_ids:
                continue
            secondary_team_ids.append(match.team_id)
            if len(secondary_team_ids) >= max_secondary_team_ids:
                return tuple(secondary_team_ids)
    return tuple(secondary_team_ids)


def _matches_for_source(
    market: TeamSpecialistMarketMetadata,
    source_name: str,
) -> tuple[_TextMatch, ...]:
    if source_name == "category" and market.category in CATEGORY_TO_PRIMARY_TEAM:
        return (
            _TextMatch(
                team_id=CATEGORY_TO_PRIMARY_TEAM[market.category],
                position=0,
            ),
        )
    return _matches_for_text(_source_value(market, source_name))


def _matches_for_text(value: str | None) -> tuple[_TextMatch, ...]:
    if value is None:
        return ()
    normalized_text = _normalize_text(value)
    if not normalized_text:
        return ()

    matches: list[_TextMatch] = []
    for team_id in _TEAM_RULE_ORDER:
        if team_id == "commodities_oil" and _is_noncommodity_oil_context(
            normalized_text,
        ):
            continue
        position = _first_phrase_position(normalized_text, _TEAM_RULES[team_id])
        if position is not None:
            matches.append(_TextMatch(team_id=team_id, position=position))
    return tuple(
        sorted(
            matches,
            key=lambda match: (match.position, _TEAM_RULE_INDEX[match.team_id]),
        ),
    )


def _first_phrase_position(
    normalized_text: str,
    phrases: tuple[str, ...],
) -> int | None:
    positions = tuple(
        position
        for phrase in phrases
        if (position := _phrase_position(normalized_text, phrase)) is not None
    )
    if not positions:
        return None
    return min(positions)


def _phrase_position(normalized_text: str, phrase: str) -> int | None:
    normalized_phrase = _normalize_text(phrase)
    index = f" {normalized_text} ".find(f" {normalized_phrase} ")
    if index < 0:
        return None
    return index


def _is_noncommodity_oil_context(normalized_text: str) -> bool:
    return any(
        _phrase_position(normalized_text, phrase) is not None
        for phrase in _OIL_SERVICE_CONTEXT
    ) and not any(
        _phrase_position(normalized_text, phrase) is not None
        for phrase in _OIL_COMMODITY_CONTEXT
    )


def _routing_reason_codes(
    primary_route: _PrimaryRoute,
    secondary_team_ids: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = [
        primary_route.source_reason_code,
        f"primary_team_{primary_route.team_id}",
    ]
    if primary_route.fallback_reason_code is not None:
        reason_codes.append(primary_route.fallback_reason_code)
    reason_codes.extend(f"secondary_team_{team_id}" for team_id in secondary_team_ids)
    return _unique_strings(reason_codes)


def _event_template(market: TeamSpecialistMarketMetadata) -> str:
    for value in (market.event, market.series, market.tag, market.category):
        if value is not None:
            return value
    return market.market_slug


def _source_value(market: TeamSpecialistMarketMetadata, source_name: str) -> str | None:
    return getattr(market, source_name)


def _normalize_markets(
    markets: tuple[TeamSpecialistMarketMetadata, ...] | list[TeamSpecialistMarketMetadata],
) -> tuple[TeamSpecialistMarketMetadata, ...]:
    if isinstance(markets, (str, bytes)) or type(markets) not in (list, tuple):
        raise ValueError("markets must be a list or tuple")
    items = tuple(markets)
    for item in items:
        if type(item) is not TeamSpecialistMarketMetadata:
            raise ValueError("markets must contain TeamSpecialistMarketMetadata values")
        require_paper_only_flags("TeamSpecialistMarketMetadata", item)
    return items


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _is_sports_category(category: str) -> bool:
    normalized = _normalize_text(category)
    return normalized == "sports" or normalized.startswith("sports ")


def _unique_strings(values: list[str]) -> tuple[str, ...]:
    items: list[str] = []
    for value in values:
        if value not in items:
            items.append(value)
    return tuple(items)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_optional_canonical_string(field_name: str, value: Any) -> None:
    if value is None:
        return
    _require_canonical_string(field_name, value)


__all__ = (
    "TeamSpecialistAssignmentConfig",
    "TeamSpecialistMarketMetadata",
    "build_team_specialist_assignment_report",
)
