"""Pure paper-only strategy team taxonomy and market routing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


CONFIDENCE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
DEFAULT_STRATEGY_TEAM_TAXONOMY_CONFIG_VERSION = "strategy-taxonomy-v1"

STRATEGY_TEAM_IDS = (
    "politics",
    "crypto_btc",
    "equity_index",
    "commodities_gold",
    "soccer",
    "basketball",
    "other_sports",
    "general",
)

_CATEGORY_HINT_TO_TEAM_REASON = {
    "politics": ("politics", "category_hint_politics"),
    "finance.crypto.btc": ("crypto_btc", "category_hint_crypto_btc"),
    "finance.equity.indices": ("equity_index", "category_hint_equity_index"),
    "finance.commodities.gold": ("commodities_gold", "category_hint_commodities_gold"),
    "commodities.gold": ("commodities_gold", "category_hint_commodities_gold"),
    "sports.soccer": ("soccer", "category_hint_soccer"),
    "sports.football": ("soccer", "category_hint_soccer"),
    "sports.basketball": ("basketball", "category_hint_basketball"),
}


@dataclass(frozen=True)
class StrategyTeamTaxonomyConfig:
    config_version: str = DEFAULT_STRATEGY_TEAM_TAXONOMY_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("StrategyTeamTaxonomyConfig", self)


@dataclass(frozen=True)
class StrategyTeamProfile:
    team_id: str
    display_name: str
    market_scope: str
    routing_keywords: tuple[str, ...]
    default_routing_confidence: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_strategy_team_id("team_id", self.team_id))
        _require_canonical_string("display_name", self.display_name)
        _require_canonical_string("market_scope", self.market_scope)
        object.__setattr__(
            self,
            "routing_keywords",
            _normalize_nonempty_string_tuple("routing_keywords", self.routing_keywords),
        )
        object.__setattr__(
            self,
            "default_routing_confidence",
            _normalize_confidence(
                "default_routing_confidence",
                self.default_routing_confidence,
            ),
        )
        require_paper_only_flags("StrategyTeamProfile", self)


@dataclass(frozen=True)
class StrategyMarketRoutingInput:
    condition_id: str
    market_slug: str
    question: str
    category_hint: str
    tags: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_canonical_string("category_hint", self.category_hint)
        object.__setattr__(self, "tags", _normalize_string_tuple("tags", self.tags))
        require_paper_only_flags("StrategyMarketRoutingInput", self)


@dataclass(frozen=True)
class StrategyMarketRouteRow:
    condition_id: str
    market_slug: str
    question: str
    category_hint: str
    tags: tuple[str, ...]
    primary_team_id: str
    routing_confidence: Decimal
    routing_reason_codes: tuple[str, ...]
    matched_terms: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_canonical_string("category_hint", self.category_hint)
        object.__setattr__(self, "tags", _normalize_string_tuple("tags", self.tags))
        object.__setattr__(
            self,
            "primary_team_id",
            require_strategy_team_id("primary_team_id", self.primary_team_id),
        )
        object.__setattr__(
            self,
            "routing_confidence",
            _normalize_confidence("routing_confidence", self.routing_confidence),
        )
        object.__setattr__(
            self,
            "routing_reason_codes",
            _normalize_nonempty_string_tuple(
                "routing_reason_codes",
                self.routing_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "matched_terms",
            _normalize_string_tuple("matched_terms", self.matched_terms),
        )
        require_paper_only_flags("StrategyMarketRouteRow", self)


@dataclass(frozen=True)
class StrategyMarketRouteReport:
    generated_at: datetime
    config_version: str
    route_count: Decimal
    rows: tuple[StrategyMarketRouteRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "route_count",
            _normalize_count("route_count", self.route_count),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if self.route_count != Decimal(len(self.rows)).quantize(COUNT_QUANT):
            raise ValueError("route_count must match rows")
        require_paper_only_flags("StrategyMarketRouteReport", self)


def build_default_strategy_team_profiles() -> tuple[StrategyTeamProfile, ...]:
    return tuple(
        StrategyTeamProfile(
            team_id=team_id,
            display_name=display_name,
            market_scope=market_scope,
            routing_keywords=routing_keywords,
            default_routing_confidence=default_routing_confidence,
        )
        for (
            team_id,
            display_name,
            market_scope,
            routing_keywords,
            default_routing_confidence,
        ) in (
            (
                "politics",
                "Politics",
                "Election, policy, polling, officeholder, and geopolitical ballot markets.",
                ("politics", "election", "president", "senate", "congress", "poll"),
                Decimal("0.900000"),
            ),
            (
                "crypto_btc",
                "Crypto BTC",
                "Bitcoin price, ETF, dominance, mining, and BTC-native crypto markets.",
                ("bitcoin", "btc", "satoshi", "halving"),
                Decimal("0.900000"),
            ),
            (
                "equity_index",
                "Equity Index",
                "Broad equity index, futures, volatility, and index-close markets.",
                ("s&p", "spx", "nasdaq", "dow", "equity index", "stock index"),
                Decimal("0.850000"),
            ),
            (
                "commodities_gold",
                "Commodities Gold",
                "Gold, XAU, precious-metals, real-rates, and USD gold-price markets.",
                ("gold", "xau", "precious metal"),
                Decimal("0.850000"),
            ),
            (
                "soccer",
                "Soccer",
                "Soccer match, league, cup, transfer, and tournament markets.",
                ("soccer", "football", "champions league", "uefa", "fifa"),
                Decimal("0.850000"),
            ),
            (
                "basketball",
                "Basketball",
                "Basketball game, player, NBA, WNBA, NCAA, and playoff markets.",
                ("basketball", "nba", "wnba", "ncaa basketball", "march madness"),
                Decimal("0.850000"),
            ),
            (
                "other_sports",
                "Other Sports",
                "Sports markets outside the dedicated soccer and basketball desks.",
                ("tennis", "baseball", "football", "hockey", "golf", "ufc", "wimbledon"),
                Decimal("0.750000"),
            ),
            (
                "general",
                "General",
                "Cross-domain markets that need broad research triage before specialization.",
                ("general", "technology", "entertainment", "weather", "culture"),
                Decimal("0.650000"),
            ),
        )
    )


def build_strategy_market_route_report(
    inputs: tuple[StrategyMarketRoutingInput, ...] | list[StrategyMarketRoutingInput],
    *,
    config: StrategyTeamTaxonomyConfig,
    generated_at: datetime,
) -> StrategyMarketRouteReport:
    if type(config) is not StrategyTeamTaxonomyConfig:
        raise ValueError("config must be a StrategyTeamTaxonomyConfig")
    source_inputs = _normalize_inputs(inputs)
    rows = tuple(route_strategy_market(market, config=config) for market in source_inputs)
    return StrategyMarketRouteReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        route_count=Decimal(len(rows)).quantize(COUNT_QUANT),
        rows=rows,
    )


def route_strategy_market(
    market: StrategyMarketRoutingInput,
    *,
    config: StrategyTeamTaxonomyConfig,
) -> StrategyMarketRouteRow:
    if type(market) is not StrategyMarketRoutingInput:
        raise ValueError("market must be a StrategyMarketRoutingInput")
    if type(config) is not StrategyTeamTaxonomyConfig:
        raise ValueError("config must be a StrategyTeamTaxonomyConfig")
    require_paper_only_flags("StrategyMarketRoutingInput", market)
    require_paper_only_flags("StrategyTeamTaxonomyConfig", config)

    primary_team_id, confidence, reason_codes, matched_terms = _route_market(market)
    return StrategyMarketRouteRow(
        condition_id=market.condition_id,
        market_slug=market.market_slug,
        question=market.question,
        category_hint=market.category_hint,
        tags=market.tags,
        primary_team_id=primary_team_id,
        routing_confidence=confidence,
        routing_reason_codes=reason_codes,
        matched_terms=matched_terms,
    )


def require_strategy_team_id(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STRATEGY_TEAM_IDS:
        raise ValueError(f"{field_name} must be a known strategy team")
    return value


def _route_market(
    market: StrategyMarketRoutingInput,
) -> tuple[str, Decimal, tuple[str, ...], tuple[str, ...]]:
    category_hint = market.category_hint.lower()
    if category_hint in _CATEGORY_HINT_TO_TEAM_REASON:
        team_id, reason_code = _CATEGORY_HINT_TO_TEAM_REASON[category_hint]
        return team_id, _confidence_for_team(team_id), (reason_code,), ()
    if category_hint.startswith("politics."):
        return "politics", Decimal("0.900000"), ("category_hint_politics",), ()
    if category_hint.startswith("sports."):
        if "soccer" in category_hint:
            return "soccer", Decimal("0.850000"), ("category_hint_soccer",), ()
        if "basketball" in category_hint:
            return "basketball", Decimal("0.850000"), ("category_hint_basketball",), ()
        return "other_sports", Decimal("0.750000"), ("category_hint_other_sports",), ()

    haystack = _market_text(market)
    for team_id, reason_code, terms in (
        ("crypto_btc", "keyword_bitcoin", ("bitcoin", "btc", "satoshi")),
        (
            "equity_index",
            "keyword_equity_index",
            ("s&p", "spx", "nasdaq", "dow", "equity index", "stock index"),
        ),
        ("commodities_gold", "keyword_gold", ("gold", "xau", "precious metal")),
        ("politics", "keyword_politics", ("election", "president", "senate", "congress")),
        ("soccer", "keyword_soccer", ("soccer", "champions league", "uefa", "fifa")),
        ("basketball", "keyword_basketball", ("basketball", "nba", "wnba")),
        (
            "other_sports",
            "keyword_other_sports",
            ("tennis", "wimbledon", "baseball", "hockey", "golf", "ufc"),
        ),
    ):
        matched_terms = tuple(term for term in terms if term in haystack)
        if matched_terms:
            return team_id, _confidence_for_team(team_id), (reason_code,), matched_terms

    return (
        "general",
        Decimal("0.650000"),
        ("default_general_fallback",),
        (),
    )


def _confidence_for_team(team_id: str) -> Decimal:
    profile_by_team_id = {
        profile.team_id: profile for profile in build_default_strategy_team_profiles()
    }
    return profile_by_team_id[require_strategy_team_id("team_id", team_id)].default_routing_confidence


def _market_text(market: StrategyMarketRoutingInput) -> str:
    return " ".join(
        (
            market.condition_id,
            market.market_slug,
            market.question,
            market.category_hint,
            " ".join(market.tags),
        )
    ).casefold()


def _normalize_inputs(
    inputs: tuple[StrategyMarketRoutingInput, ...] | list[StrategyMarketRoutingInput],
) -> tuple[StrategyMarketRoutingInput, ...]:
    if isinstance(inputs, (str, bytes)) or type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    items = tuple(inputs)
    for item in items:
        if type(item) is not StrategyMarketRoutingInput:
            raise ValueError("inputs must contain StrategyMarketRoutingInput values")
        require_paper_only_flags("StrategyMarketRoutingInput", item)
    return items


def _normalize_rows(
    rows: tuple[StrategyMarketRouteRow, ...],
) -> tuple[StrategyMarketRouteRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain StrategyMarketRouteRow values")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must contain StrategyMarketRouteRow values") from exc
    for item in items:
        if type(item) is not StrategyMarketRouteRow:
            raise ValueError("rows must contain StrategyMarketRouteRow values")
        require_paper_only_flags("StrategyMarketRouteRow", item)
    return items


def _normalize_confidence(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0") or value > Decimal("1"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(CONFIDENCE_QUANT)


def _normalize_count(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < Decimal("0") or value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative integral Decimal")
    return value.quantize(COUNT_QUANT)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_nonempty_string_tuple(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    items = _normalize_string_tuple(field_name, value)
    if not items:
        raise ValueError(f"{field_name} must contain canonical strings")
    return items


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


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical strings")


__all__ = (
    "CONFIDENCE_QUANT",
    "DEFAULT_STRATEGY_TEAM_TAXONOMY_CONFIG_VERSION",
    "STRATEGY_TEAM_IDS",
    "StrategyMarketRouteReport",
    "StrategyMarketRouteRow",
    "StrategyMarketRoutingInput",
    "StrategyTeamProfile",
    "StrategyTeamTaxonomyConfig",
    "build_default_strategy_team_profiles",
    "build_strategy_market_route_report",
    "require_strategy_team_id",
    "route_strategy_market",
)
