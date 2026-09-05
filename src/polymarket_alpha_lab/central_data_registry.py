"""Validated registry for official and public internet source definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlsplit

from .central_data_contracts import RequestParamSpec, SourceDefinition
from .central_data_request_params import PaginationPolicy
from .team_taxonomy import require_team_id


@dataclass(frozen=True)
class TeamSourceRequirement:
    team_id: str
    source_ids: tuple[str, ...]
    minimum_current_source_families: int = 1
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        if isinstance(self.source_ids, (str, bytes)):
            raise ValueError("source_ids must be an iterable of source ids")
        source_ids = tuple(self.source_ids)
        if not source_ids or any(
            type(source_id) is not str or not source_id or source_id.strip() != source_id
            for source_id in source_ids
        ):
            raise ValueError("source_ids must contain canonical ids")
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("source_ids must not contain duplicates")
        object.__setattr__(self, "source_ids", source_ids)
        if type(self.minimum_current_source_families) is not int or self.minimum_current_source_families < 1:
            raise ValueError("minimum_current_source_families must be positive")
        for field_name in ("paper_only", "report_only", "readonly"):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must be True")


class SourceRegistry:
    """Mutable registration boundary with deterministic readback."""

    def __init__(self, *, minimum_current_source_families: int = 1) -> None:
        if type(minimum_current_source_families) is not int or minimum_current_source_families < 1:
            raise ValueError("minimum_current_source_families must be positive")
        self._sources: dict[str, SourceDefinition] = {}
        self._requirements: dict[str, TeamSourceRequirement] = {}
        self.minimum_current_source_families = minimum_current_source_families

    def register(self, source_def: SourceDefinition) -> None:
        if type(source_def) is not SourceDefinition:
            raise ValueError("source_def must be a SourceDefinition")
        if source_def.source_id in self._sources:
            raise ValueError("source_id is already registered")
        self._sources[source_def.source_id] = source_def

    def register_many(self, source_defs: Iterable[SourceDefinition]) -> None:
        for source_def in source_defs:
            self.register(source_def)

    def register_requirement(self, requirement: TeamSourceRequirement) -> None:
        if type(requirement) is not TeamSourceRequirement:
            raise ValueError("requirement must be a TeamSourceRequirement")
        if requirement.team_id in self._requirements:
            raise ValueError("team requirement is already registered")
        missing = tuple(source_id for source_id in requirement.source_ids if source_id not in self._sources)
        if missing:
            raise ValueError("team requirement references an unregistered source")
        if requirement.minimum_current_source_families < self.minimum_current_source_families:
            raise ValueError("team requirement is below the registry family threshold")
        source_families = {
            self._sources[source_id].source_family
            for source_id in requirement.source_ids
        }
        if requirement.minimum_current_source_families > len(source_families):
            raise ValueError("team requirement exceeds its registered source families")
        self._requirements[requirement.team_id] = requirement

    def get(self, source_id: str) -> SourceDefinition:
        if type(source_id) is not str or not source_id.strip():
            raise ValueError("source_id must be a canonical string")
        try:
            return self._sources[source_id]
        except KeyError as exc:
            raise ValueError("source_id is not registered") from exc

    @property
    def source_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._sources))

    @property
    def requirements(self) -> tuple[TeamSourceRequirement, ...]:
        return tuple(self._requirements[key] for key in sorted(self._requirements))

    def list_current_families(self) -> tuple[str, ...]:
        return tuple(sorted({source.source_family for source in self._sources.values()}))

    def has_family(self, family: str) -> bool:
        return type(family) is str and family in self.list_current_families()


GAMMA_MARKETS_PAGINATION = PaginationPolicy(
    max_pages=10,
    min_items_per_page=1,
    max_items_per_page=100,
)

DEFAULT_SOURCE_DEFINITIONS = (
    SourceDefinition(
        source_id="polymarket_gamma_markets",
        source_family="polymarket_gamma",
        url_template="https://gamma-api.polymarket.com/markets",
        content_type="application/json",
        freshness_policy_seconds=300,
        is_official=True,
        query_params=(
            RequestParamSpec("condition_id", "pattern", pattern=r"[0-9a-fA-Fx]{1,66}"),
            RequestParamSpec("slug", "pattern", pattern=r"[a-z0-9-]{1,80}"),
            RequestParamSpec("limit", "int_range", min_value=1, max_value=100),
            RequestParamSpec("offset", "int_range", min_value=0, max_value=100000),
        ),
    ),
    SourceDefinition(
        source_id="polymarket_clob_book",
        source_family="polymarket_clob",
        url_template="https://clob.polymarket.com/book",
        content_type="application/json",
        freshness_policy_seconds=30,
        is_official=True,
        query_params=(
            RequestParamSpec("token_id", "pattern", pattern=r"[0-9]{1,19}"),
        ),
    ),
    SourceDefinition(
        source_id="polymarket_data_trades",
        source_family="polymarket_data",
        url_template="https://data-api.polymarket.com/trades",
        content_type="application/json",
        freshness_policy_seconds=300,
        is_official=True,
    ),
    SourceDefinition(
        source_id="kraken_btc_ticker",
        source_family="kraken_public",
        url_template="https://api.kraken.com/0/public/Ticker",
        content_type="application/json",
        # Conservative default: the provider documents no update guarantee;
        # retune only with recorded smoke evidence.
        freshness_policy_seconds=300,
        is_official=False,
        query_params=(
            RequestParamSpec("pair", "enum", required=True, choices=("XBTUSD",)),
        ),
    ),
)

DEFAULT_PAGINATION_POLICIES = {
    "polymarket_gamma_markets": GAMMA_MARKETS_PAGINATION,
}


def default_allowed_hosts() -> frozenset[str]:
    """Hosts of every default source, for transport construction."""

    return frozenset(
        urlsplit(source.url_template).hostname.lower()
        for source in DEFAULT_SOURCE_DEFINITIONS
        if urlsplit(source.url_template).hostname
    )

DEFAULT_TEAM_SOURCE_REQUIREMENTS = tuple(
    TeamSourceRequirement(
        team_id=team_id,
        source_ids=tuple(item.source_id for item in DEFAULT_SOURCE_DEFINITIONS),
        minimum_current_source_families=1,
    )
    for team_id in (
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
)


def build_default_source_registry() -> SourceRegistry:
    registry = SourceRegistry()
    registry.register_many(DEFAULT_SOURCE_DEFINITIONS)
    for requirement in DEFAULT_TEAM_SOURCE_REQUIREMENTS:
        registry.register_requirement(requirement)
    return registry


__all__ = (
    "DEFAULT_PAGINATION_POLICIES",
    "DEFAULT_SOURCE_DEFINITIONS",
    "DEFAULT_TEAM_SOURCE_REQUIREMENTS",
    "GAMMA_MARKETS_PAGINATION",
    "SourceRegistry",
    "TeamSourceRequirement",
    "build_default_source_registry",
    "default_allowed_hosts",
)
