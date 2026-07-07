"""Pure deterministic routing from market metadata to specialist teams."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


CONFIDENCE_QUANTUM = Decimal("0.000001")
CATEGORY_CONFIDENCE = Decimal("0.920000")
KEYWORD_CONFIDENCE = Decimal("0.860000")
SPORTS_OTHER_CONFIDENCE = Decimal("0.700000")
UNROUTED_CONFIDENCE = Decimal("0.000000")
REDACTED_MARKET_REF_PREFIX = "market-ref-"
MAX_REPORT_ROUTE_INDEX = 0xFFFFFFFFFFFFFFFF

ROUTE_STATUSES = frozenset(("pass", "watch", "block"))
_PUBLIC_REASON_CODE_FORBIDDEN_TERMS = (
    "candidate",
    "candidate id",
    "condition id",
    "market id",
    "market slug",
    "question",
    "source",
    "source ref",
    "url",
    "http",
    "https",
    "www",
    "text",
    "dsn",
    "database",
    "table",
    "token",
    "private",
    "auth",
    "wallet",
    "account",
    "order",
    "submit",
    "sign",
    "cancel",
    "replace",
    "exchange mutation",
    "trade",
    "position",
    "sizing",
    "buy",
    "sell",
    "recommend",
    "recommendation",
    "secondary team",
    "matched",
    "ambiguous",
    "unrouted",
    "blocked",
)

_TEAM_ORDER = (
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
_TEAM_INDEX = {
    "politics": Decimal("0"),
    "crypto_btc": Decimal("1"),
    "crypto_eth": Decimal("2"),
    "macro_rates": Decimal("3"),
    "equity_indices": Decimal("4"),
    "commodities_gold": Decimal("5"),
    "commodities_oil": Decimal("6"),
    "sports_soccer": Decimal("7"),
    "sports_basketball": Decimal("8"),
    "sports_other": Decimal("9"),
}

_CATEGORY_TO_TEAM = {
    "politics": "politics",
    "finance.politics": "politics",
    "finance.crypto.btc": "crypto_btc",
    "crypto.btc": "crypto_btc",
    "finance.crypto.eth": "crypto_eth",
    "crypto.eth": "crypto_eth",
    "finance.macro.rates": "macro_rates",
    "macro.rates": "macro_rates",
    "finance.equity.indices": "equity_indices",
    "finance.equities": "equity_indices",
    "equities.indexes": "equity_indices",
    "equities.indices": "equity_indices",
    "finance.commodities.gold": "commodities_gold",
    "commodities.gold": "commodities_gold",
    "finance.commodities.oil": "commodities_oil",
    "commodities.oil": "commodities_oil",
    "sports.soccer": "sports_soccer",
    "sports.football.soccer": "sports_soccer",
    "sports.basketball": "sports_basketball",
    "sports.other": "sports_other",
}

_TEAM_TERMS = {
    "politics": (
        "ballot",
        "biden",
        "congress",
        "democrat",
        "election",
        "governor",
        "mayor",
        "policy",
        "politics",
        "president",
        "presidential",
        "republican",
        "senate",
        "supreme court",
        "trump",
        "white house",
    ),
    "crypto_btc": (
        "bitcoin",
        "bitcoin etf",
        "btc",
        "halving",
        "satoshi",
    ),
    "crypto_eth": (
        "dencun",
        "eth",
        "eth etf",
        "ether",
        "ethereum",
        "staking",
    ),
    "macro_rates": (
        "central bank",
        "cpi",
        "fed",
        "federal reserve",
        "fomc",
        "inflation",
        "interest rate",
        "jobs report",
        "rate cut",
        "rate hike",
        "rates",
        "real rates",
        "real yields",
        "treasury",
        "yield",
    ),
    "equity_indices": (
        "dow",
        "dow jones",
        "equity index",
        "index close",
        "nasdaq",
        "qqq",
        "russell 2000",
        "s p 500",
        "sp 500",
        "spy",
        "spx",
        "stock index",
    ),
    "commodities_gold": (
        "bullion",
        "gold",
        "gold futures",
        "precious metal",
        "precious metals",
        "xau",
    ),
    "commodities_oil": (
        "barrel",
        "brent",
        "crude",
        "crude oil",
        "energy",
        "inventories",
        "inventory",
        "oil",
        "oil futures",
        "opec",
        "wti",
    ),
    "sports_soccer": (
        "bundesliga",
        "champions league",
        "copa",
        "europa league",
        "fifa",
        "la liga",
        "mls",
        "premier league",
        "serie a",
        "soccer",
        "uefa",
        "world cup",
    ),
    "sports_basketball": (
        "basketball",
        "bucks",
        "bulls",
        "celtics",
        "heat",
        "knicks",
        "lakers",
        "march madness",
        "mavericks",
        "nba",
        "ncaa basketball",
        "nuggets",
        "sixers",
        "warriors",
        "wnba",
    ),
    "sports_other": (
        "american football",
        "baseball",
        "boxing",
        "cricket",
        "f1",
        "formula 1",
        "golf",
        "hockey",
        "mma",
        "mlb",
        "motorsport",
        "nascar",
        "nfl",
        "nhl",
        "olympics",
        "rugby",
        "tennis",
        "ufc",
        "volleyball",
        "wimbledon",
    ),
}

_OIL_SERVICE_TERMS = ("auto shop", "automotive", "car service", "oil change")
_OIL_COMMODITY_TERMS = (
    "barrel",
    "brent",
    "crude",
    "crude oil",
    "oil futures",
    "opec",
    "wti",
)


@dataclass(frozen=True)
class MarketTeamRoutingInput:
    condition_id: str
    market_slug: str
    question: str
    category: str | None = None
    event: str | None = None
    series: str | None = None
    tags: tuple[str, ...] = ()
    description: str | None = None
    rules: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        for field_name in ("category", "event", "series", "description", "rules"):
            _require_optional_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "tags", _normalize_tags(self.tags))
        require_paper_only_flags("MarketTeamRoutingInput", self)
        _reject_unsafe_surface("MarketTeamRoutingInput", self)


@dataclass(frozen=True)
class MarketTeamRoute:
    redacted_market_ref: str
    primary_team_id: str | None
    secondary_team_ids: tuple[str, ...]
    confidence: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_market_ref(self.redacted_market_ref)
        if self.status not in ROUTE_STATUSES:
            raise ValueError("status must be pass, watch, or block")
        primary_team_id = _normalize_primary_team_id(
            "primary_team_id",
            self.primary_team_id,
            status=self.status,
        )
        object.__setattr__(self, "primary_team_id", primary_team_id)
        object.__setattr__(
            self,
            "secondary_team_ids",
            _normalize_secondary_team_ids(
                self.secondary_team_ids,
                primary_team_id=primary_team_id,
            ),
        )
        object.__setattr__(
            self,
            "confidence",
            _normalize_confidence("confidence", self.confidence),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_nonempty_string_tuple("reason_codes", self.reason_codes),
        )
        _reject_public_route_reason_codes(self.reason_codes)
        _validate_route_assignment(
            status=self.status,
            primary_team_id=primary_team_id,
            secondary_team_ids=self.secondary_team_ids,
            confidence=self.confidence,
        )
        require_paper_only_flags("MarketTeamRoute", self)
        _reject_unsafe_surface("MarketTeamRoute", self)


@dataclass(frozen=True)
class _TeamScore:
    team_id: str
    first_position: Decimal


def route_market_team(market: MarketTeamRoutingInput) -> MarketTeamRoute:
    return _route_market_team(
        market,
        redacted_market_ref=_redacted_market_ref(1),
    )


def _route_market_team(
    market: MarketTeamRoutingInput,
    *,
    redacted_market_ref: str,
) -> MarketTeamRoute:
    if type(market) is not MarketTeamRoutingInput:
        raise ValueError("market must be a MarketTeamRoutingInput")
    require_paper_only_flags("MarketTeamRoutingInput", market)
    _reject_unsafe_surface("MarketTeamRoutingInput", market)
    _require_redacted_market_ref(redacted_market_ref)

    category_team_id = _team_from_category(market.category)
    if category_team_id is not None:
        return _build_route(
            redacted_market_ref=redacted_market_ref,
            primary_team_id=category_team_id,
            secondary_team_ids=(),
            confidence=(
                SPORTS_OTHER_CONFIDENCE
                if category_team_id == "sports_other"
                else CATEGORY_CONFIDENCE
            ),
            status="pass",
            primary_reason_code=f"pass_category_{category_team_id}",
        )

    scores = _team_scores(market)
    if not scores:
        return _build_route(
            redacted_market_ref=redacted_market_ref,
            primary_team_id=None,
            secondary_team_ids=(),
            confidence=UNROUTED_CONFIDENCE,
            status="block",
            primary_reason_code="block_no_taxonomy_signal",
        )
    if len(scores) > 1:
        return _build_route(
            redacted_market_ref=redacted_market_ref,
            primary_team_id=None,
            secondary_team_ids=(),
            confidence=UNROUTED_CONFIDENCE,
            status="watch",
            primary_reason_code="watch_multiple_taxonomy_signals",
        )

    primary = scores[0]
    return _build_route(
        redacted_market_ref=redacted_market_ref,
        primary_team_id=primary.team_id,
        secondary_team_ids=(),
        confidence=KEYWORD_CONFIDENCE,
        status="pass",
        primary_reason_code=f"pass_keyword_{primary.team_id}",
    )


def route_market_teams(
    markets: tuple[MarketTeamRoutingInput, ...] | list[MarketTeamRoutingInput],
) -> tuple[MarketTeamRoute, ...]:
    items = _normalize_markets(markets)
    return tuple(
        _route_market_team(
            market,
            redacted_market_ref=_redacted_market_ref(route_index),
        )
        for route_index, market in enumerate(
            sorted(
                items,
                key=lambda item: (item.condition_id, item.market_slug, item.question),
            ),
            start=1,
        )
    )


def _build_route(
    *,
    redacted_market_ref: str,
    primary_team_id: str | None,
    secondary_team_ids: tuple[str, ...],
    confidence: Decimal,
    status: str,
    primary_reason_code: str,
) -> MarketTeamRoute:
    if secondary_team_ids:
        raise ValueError("secondary_team_ids must be empty for public route payloads")
    return MarketTeamRoute(
        redacted_market_ref=redacted_market_ref,
        primary_team_id=primary_team_id,
        secondary_team_ids=(),
        confidence=confidence,
        status=status,
        reason_codes=(primary_reason_code,),
    )


def _team_from_category(category: str | None) -> str | None:
    if category is None:
        return None
    normalized_category = category.casefold()
    if normalized_category in _CATEGORY_TO_TEAM:
        return require_team_id("primary_team_id", _CATEGORY_TO_TEAM[normalized_category])
    return None


def _normalize_primary_team_id(
    field_name: str,
    value: object,
    *,
    status: str,
) -> str | None:
    if status == "pass":
        if value is None:
            raise ValueError(f"{field_name} is required when status is pass")
        return require_team_id(field_name, value)
    if status in ("watch", "block"):
        if value is None:
            return None
        require_team_id(field_name, value)
        raise ValueError(f"{field_name} must be None when status is watch or block")
    raise ValueError("status must be pass, watch, or block")


def _redacted_market_ref(report_route_index: int) -> str:
    if type(report_route_index) is not int:
        raise ValueError("report_route_index must be an int")
    if report_route_index < 1 or report_route_index > MAX_REPORT_ROUTE_INDEX:
        raise ValueError("report_route_index must fit a positive 64-bit sequence")
    return f"{REDACTED_MARKET_REF_PREFIX}{report_route_index:016x}"


def _team_scores(market: MarketTeamRoutingInput) -> tuple[_TeamScore, ...]:
    normalized_text = _market_text(market)
    scores: list[_TeamScore] = []
    for team_id in _TEAM_ORDER:
        terms = _TEAM_TERMS[team_id]
        if team_id == "commodities_oil" and _is_noncommodity_oil_context(
            normalized_text,
        ):
            continue
        positions = []
        for term in terms:
            position = _phrase_position(normalized_text, _normalize_text(term))
            if position is not None:
                positions.append(position)
        if positions:
            scores.append(
                _TeamScore(
                    team_id=team_id,
                    first_position=min(positions),
                )
            )
    return tuple(
        sorted(
            scores,
            key=lambda item: (item.first_position, _TEAM_INDEX[item.team_id]),
        )
    )


def _market_text(market: MarketTeamRoutingInput) -> str:
    values = (
        market.question,
        market.category,
        market.event,
        market.series,
        " ".join(market.tags),
        market.description,
        market.rules,
        market.market_slug,
    )
    return _normalize_text(" ".join(value for value in values if value is not None))


def _is_noncommodity_oil_context(normalized_text: str) -> bool:
    return any(
        _phrase_position(normalized_text, _normalize_text(term)) is not None
        for term in _OIL_SERVICE_TERMS
    ) and not any(
        _phrase_position(normalized_text, _normalize_text(term)) is not None
        for term in _OIL_COMMODITY_TERMS
    )


def _normalize_markets(
    markets: tuple[MarketTeamRoutingInput, ...] | list[MarketTeamRoutingInput],
) -> tuple[MarketTeamRoutingInput, ...]:
    if isinstance(markets, (str, bytes)) or type(markets) not in (list, tuple):
        raise ValueError("markets must be a list or tuple")
    items = tuple(markets)
    for item in items:
        if type(item) is not MarketTeamRoutingInput:
            raise ValueError("markets must contain MarketTeamRoutingInput values")
        require_paper_only_flags("MarketTeamRoutingInput", item)
        _reject_unsafe_surface("MarketTeamRoutingInput", item)
    return items


def _normalize_tags(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("tags must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("tags must contain canonical strings") from exc
    for item in items:
        _require_canonical_string("tags", item)
    return tuple(sorted(dict.fromkeys(items)))


def _normalize_secondary_team_ids(
    value: tuple[str, ...],
    *,
    primary_team_id: str | None,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("secondary_team_ids must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("secondary_team_ids must be an iterable") from exc
    if items:
        raise ValueError("secondary_team_ids must be empty for public route payloads")
    if primary_team_id is None:
        return ()
    normalized = tuple(require_team_id("secondary_team_ids", item) for item in items)
    if primary_team_id in normalized:
        raise ValueError("secondary_team_ids cannot contain primary_team_id")
    if len(set(normalized)) != len(normalized):
        raise ValueError("secondary_team_ids must be unique")
    return tuple(sorted(normalized, key=lambda team_id: _TEAM_INDEX[team_id]))


def _normalize_confidence(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0") or value > Decimal("1"):
        raise ValueError(f"{field_name} must be between zero and one")
    return value.quantize(CONFIDENCE_QUANTUM)


def _validate_route_assignment(
    *,
    status: str,
    primary_team_id: str | None,
    secondary_team_ids: tuple[str, ...],
    confidence: Decimal,
) -> None:
    if secondary_team_ids:
        raise ValueError("secondary_team_ids must be empty for public route payloads")
    if status in ("watch", "block"):
        if primary_team_id is not None:
            raise ValueError("primary_team_id must be None when status is watch or block")
        if confidence != UNROUTED_CONFIDENCE:
            raise ValueError("confidence must be zero when status is watch or block")
        return
    if primary_team_id is None:
        raise ValueError("primary_team_id is required when status is pass")
    if confidence == UNROUTED_CONFIDENCE:
        raise ValueError("confidence must be positive when status is pass")


def _reject_public_route_reason_codes(reason_codes: tuple[str, ...]) -> None:
    for reason_code in reason_codes:
        normalized_reason_code = _normalize_text(reason_code)
        for term in _PUBLIC_REASON_CODE_FORBIDDEN_TERMS:
            if (
                _phrase_position(normalized_reason_code, _normalize_text(term))
                is not None
            ):
                raise ValueError(f"unsafe public route reason code: {term}")


def _normalize_nonempty_string_tuple(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    items = _normalize_string_tuple(field_name, value)
    if not items:
        raise ValueError(f"{field_name} must contain canonical strings")
    return _dedupe(list(items))


def _normalize_string_tuple(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _reject_unsafe_surface(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    normalized_values = _normalize_text(" ".join(_iter_string_values(value)))
    for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS:
        term = _normalize_text(fragment)
        if _phrase_position(normalized_values, term) is not None:
            raise ValueError(f"unsafe live surface term in {label}: {fragment}")


def _iter_string_values(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if value is None or isinstance(value, (bool, Decimal)):
        return ()
    if isinstance(value, (tuple, list)):
        values: list[str] = []
        for item in value:
            values.extend(_iter_string_values(item))
        return tuple(values)
    if type(value) in (MarketTeamRoutingInput, MarketTeamRoute):
        values = []
        for item in value.__dict__.values():
            values.extend(_iter_string_values(item))
        return tuple(values)
    return ()


def _phrase_position(normalized_text: str, normalized_phrase: str) -> Decimal | None:
    index = f" {normalized_text} ".find(f" {normalized_phrase} ")
    if index < 0:
        return None
    return Decimal(index)


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _dedupe(values: list[str]) -> tuple[str, ...]:
    items: list[str] = []
    for value in values:
        if value not in items:
            items.append(value)
    return tuple(items)


def _require_redacted_market_ref(value: object) -> None:
    if (
        type(value) is not str
        or re.fullmatch(r"market-ref-[0-9a-f]{16}", value) is None
    ):
        raise ValueError("redacted_market_ref must be a redacted market reference")


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
    "CONFIDENCE_QUANTUM",
    "MarketTeamRoute",
    "MarketTeamRoutingInput",
    "route_market_team",
    "route_market_teams",
)
