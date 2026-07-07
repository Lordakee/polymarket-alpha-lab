"""Pure paper-only router from sanitized event features to research queues."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


RESEARCH_EVENT_TYPE_ROUTER_CONFIG_VERSION = "research-event-type-router-v1"

CONFIDENCE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
CATEGORY_CONFIDENCE = Decimal("0.920000")
FEATURE_CONFIDENCE = Decimal("0.860000")

TEAM_QUEUE_IDS = (
    "politics",
    "macro",
    "crypto",
    "equities",
    "metals",
    "football",
    "basketball",
)
ROUTE_STATUSES = ("pass", "watch", "block")

_QUEUE_INDEX = {
    "politics": 0,
    "macro": 1,
    "crypto": 2,
    "equities": 3,
    "metals": 4,
    "football": 5,
    "basketball": 6,
}

_CATEGORY_TO_QUEUE = {
    "politics": "politics",
    "politics.elections": "politics",
    "economics": "macro",
    "economics.macro": "macro",
    "economics.central_banks": "macro",
    "finance.macro": "macro",
    "finance.macro.rates": "macro",
    "macro": "macro",
    "macro.rates": "macro",
    "finance.crypto": "crypto",
    "finance.crypto.btc": "crypto",
    "finance.crypto.eth": "crypto",
    "crypto": "crypto",
    "crypto.btc": "crypto",
    "crypto.eth": "crypto",
    "equities": "equities",
    "equities.indices": "equities",
    "finance.equity.indices": "equities",
    "finance.equities": "equities",
    "finance.equities.indices": "equities",
    "finance.indices": "equities",
    "commodities.metals": "metals",
    "commodities.gold": "metals",
    "finance.commodities.gold": "metals",
    "metals": "metals",
    "precious_metals": "metals",
    "sports.football": "football",
    "sports.soccer": "football",
    "football": "football",
    "soccer": "football",
    "sports.basketball": "basketball",
    "basketball": "basketball",
}

_CATEGORY_PREFIX_TO_QUEUE = (
    ("politics.", "politics"),
    ("economics.", "macro"),
    ("macro.", "macro"),
    ("finance.macro.", "macro"),
    ("finance.crypto.", "crypto"),
    ("crypto.", "crypto"),
    ("finance.equity.", "equities"),
    ("finance.equities.", "equities"),
    ("equities.", "equities"),
    ("commodities.gold.", "metals"),
    ("commodities.metals.", "metals"),
    ("finance.commodities.gold.", "metals"),
    ("sports.football.", "football"),
    ("sports.soccer.", "football"),
    ("football.", "football"),
    ("soccer.", "football"),
    ("sports.basketball.", "basketball"),
    ("basketball.", "basketball"),
)

_QUEUE_TERMS = {
    "politics": (
        "ballot",
        "congress",
        "election",
        "governor",
        "mayor",
        "polling",
        "president",
        "senate",
        "white house",
    ),
    "macro": (
        "central bank",
        "cpi",
        "fed",
        "federal reserve",
        "fomc",
        "gdp",
        "inflation",
        "interest rate",
        "jobs report",
        "rate cut",
        "rate hike",
        "recession",
        "treasury",
        "unemployment",
    ),
    "crypto": (
        "bitcoin",
        "bitcoin etf",
        "blockchain",
        "btc",
        "crypto",
        "eth",
        "ethereum",
        "solana",
        "stablecoin",
    ),
    "equities": (
        "dow",
        "dow jones",
        "earnings",
        "equity index",
        "nasdaq",
        "qqq",
        "russell 2000",
        "s p 500",
        "sp 500",
        "spy",
        "spx",
        "stock index",
    ),
    "metals": (
        "bullion",
        "gold",
        "gold futures",
        "precious metal",
        "precious metals",
        "silver",
        "xag",
        "xau",
    ),
    "football": (
        "champions league",
        "fifa",
        "football",
        "nfl",
        "premier league",
        "soccer",
        "uefa",
        "world cup",
    ),
    "basketball": (
        "basketball",
        "march madness",
        "nba",
        "ncaa basketball",
        "wnba",
    ),
}

_UNSAFE_KEY_FRAGMENTS = (
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
_UNSAFE_VALUE_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\braw\b",
        r"\bcandidate(?:[-_ ]?id|\b)",
        r"\bcondition[-_ ]?id\b",
        r"\bmarket[-_ ]?(?:id|slug|question)\b",
        r"\bmarket slug\b",
        r"\bquestion\b",
        r"\bsource(?:[-_ ]?(?:ref|url|text))?\b",
        r"\bref\b",
        r"https?://",
        r"\burl\b",
        r"\btext\b",
        r"\bdsn\b",
        r"\bdatabase\b",
        r"\btable\b",
        r"\btoken\b",
        r"\bwallet\b",
        r"\bauth(?:entication|orization)?\b",
        r"\border\b",
        r"\btrade\b",
        r"\bposition\b",
        r"\bbuy\b",
        r"\bsell\b",
        r"\brecommend(?:ation|ed|ing)?\b",
    )
)


@dataclass(frozen=True)
class ResearchMarketEventTypeRouterConfig:
    config_version: str = RESEARCH_EVENT_TYPE_ROUTER_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        require_paper_only_flags("ResearchMarketEventTypeRouterConfig", self)


@dataclass(frozen=True)
class ResearchMarketEventTypeInput:
    public_event_type: str
    public_category_hint: str
    public_feature_tags: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("public_event_type", self.public_event_type)
        _require_canonical_public_string("public_category_hint", self.public_category_hint)
        object.__setattr__(
            self,
            "public_feature_tags",
            _normalize_public_string_tuple(
                "public_feature_tags",
                self.public_feature_tags,
            ),
        )
        require_paper_only_flags("ResearchMarketEventTypeInput", self)


@dataclass(frozen=True)
class ResearchMarketEventTypeRoute:
    config_version: str
    public_event_type: str
    public_category_hint: str
    public_feature_tags: tuple[str, ...]
    team_queue_id: str | None
    route_status: str
    route_confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        _require_canonical_public_string("public_event_type", self.public_event_type)
        _require_canonical_public_string("public_category_hint", self.public_category_hint)
        object.__setattr__(
            self,
            "public_feature_tags",
            _normalize_public_string_tuple(
                "public_feature_tags",
                self.public_feature_tags,
            ),
        )
        object.__setattr__(
            self,
            "team_queue_id",
            _normalize_team_queue_id("team_queue_id", self.team_queue_id),
        )
        object.__setattr__(
            self,
            "route_status",
            _require_route_status("route_status", self.route_status),
        )
        object.__setattr__(
            self,
            "route_confidence",
            _normalize_confidence("route_confidence", self.route_confidence),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_nonempty_public_string_tuple("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("ResearchMarketEventTypeRoute", self)
        _validate_route(self)
        _reject_unsafe_public_payload("ResearchMarketEventTypeRoute", self)


def route_research_market_event_type(
    event: ResearchMarketEventTypeInput,
    *,
    config: ResearchMarketEventTypeRouterConfig | None = None,
) -> ResearchMarketEventTypeRoute:
    if type(event) is not ResearchMarketEventTypeInput:
        raise ValueError("event must be a ResearchMarketEventTypeInput")
    active_config = ResearchMarketEventTypeRouterConfig() if config is None else config
    if type(active_config) is not ResearchMarketEventTypeRouterConfig:
        raise ValueError("config must be a ResearchMarketEventTypeRouterConfig")
    require_paper_only_flags("ResearchMarketEventTypeInput", event)
    require_paper_only_flags("ResearchMarketEventTypeRouterConfig", active_config)

    team_queue_id, route_status, route_confidence, reason_codes = _route_components(
        event.public_event_type,
        event.public_category_hint,
        event.public_feature_tags,
    )
    return ResearchMarketEventTypeRoute(
        config_version=active_config.config_version,
        public_event_type=event.public_event_type,
        public_category_hint=event.public_category_hint,
        public_feature_tags=event.public_feature_tags,
        team_queue_id=team_queue_id,
        route_status=route_status,
        route_confidence=route_confidence,
        reason_codes=reason_codes,
    )


def research_market_event_type_router_payload(
    route: ResearchMarketEventTypeRoute | dict[str, Any],
) -> dict[str, Any]:
    if type(route) is ResearchMarketEventTypeRoute:
        require_paper_only_flags("ResearchMarketEventTypeRoute", route)
        _reject_unsafe_public_payload("route", route)
        payload = _json_ready(route)
    elif type(route) is dict:
        _reject_unsafe_public_payload("payload", route)
        payload = _json_ready(route)
    else:
        raise ValueError("route must be a ResearchMarketEventTypeRoute")
    if type(payload) is not dict:
        raise ValueError("route payload must be a JSON object")
    require_paper_only_flags("route payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _route_components(
    public_event_type: str,
    public_category_hint: str,
    public_feature_tags: tuple[str, ...],
) -> tuple[str | None, str, Decimal, tuple[str, ...]]:
    category_queue = _queue_from_category(public_category_hint)
    feature_queues = _feature_queue_ids(
        public_event_type,
        public_category_hint,
        public_feature_tags,
    )
    unique_feature_queues = tuple(dict.fromkeys(feature_queues))

    if category_queue is not None:
        if not unique_feature_queues or unique_feature_queues == (category_queue,):
            return (
                category_queue,
                "pass",
                CATEGORY_CONFIDENCE,
                (f"pass_category_{category_queue}",),
            )
        return (
            None,
            "watch",
            ZERO,
            ("watch_conflicting_public_signals",),
        )

    if len(unique_feature_queues) > 1:
        return (
            None,
            "watch",
            ZERO,
            ("watch_multiple_public_signals",),
        )
    if len(unique_feature_queues) == 1:
        feature_queue = unique_feature_queues[0]
        return (
            feature_queue,
            "pass",
            FEATURE_CONFIDENCE,
            (f"pass_feature_{feature_queue}",),
        )
    return (
        None,
        "block",
        ZERO,
        ("block_no_public_signal",),
    )


def _queue_from_category(public_category_hint: str) -> str | None:
    category = public_category_hint.casefold()
    if category in _CATEGORY_TO_QUEUE:
        return _require_team_queue_id("team_queue_id", _CATEGORY_TO_QUEUE[category])
    for prefix, queue_id in _CATEGORY_PREFIX_TO_QUEUE:
        if category.startswith(prefix):
            return _require_team_queue_id("team_queue_id", queue_id)
    return None


def _feature_queue_ids(
    public_event_type: str,
    public_category_hint: str,
    public_feature_tags: tuple[str, ...],
) -> tuple[str, ...]:
    public_text = _normalize_text(
        " ".join((public_event_type, public_category_hint, " ".join(public_feature_tags))),
    )
    matches: list[tuple[int, str]] = []
    for queue_id in TEAM_QUEUE_IDS:
        positions = [
            position
            for term in _QUEUE_TERMS[queue_id]
            if (position := _phrase_position(public_text, _normalize_text(term))) is not None
        ]
        if positions:
            matches.append((min(positions), queue_id))
    return tuple(
        item[1]
        for item in sorted(
            matches,
            key=lambda item: (item[0], _QUEUE_INDEX[item[1]]),
        )
    )


def _validate_route(route: ResearchMarketEventTypeRoute) -> None:
    expected_team_queue_id, expected_status, expected_confidence, expected_reasons = (
        _route_components(
            route.public_event_type,
            route.public_category_hint,
            route.public_feature_tags,
        )
    )
    if route.team_queue_id != expected_team_queue_id:
        raise ValueError("team_queue_id must match routed event features")
    if route.route_status != expected_status:
        raise ValueError("route_status must match routed event features")
    if route.route_confidence != expected_confidence:
        raise ValueError("route_confidence must match routed event features")
    if route.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match routed event features")
    if route.route_status == "pass":
        if route.team_queue_id is None:
            raise ValueError("team_queue_id is required when route_status is pass")
        if route.route_confidence <= ZERO:
            raise ValueError("route_confidence must be positive when route_status is pass")
        return
    if route.team_queue_id is not None:
        raise ValueError("team_queue_id must be None when route_status is watch or block")
    if route.route_confidence != ZERO:
        raise ValueError("route_confidence must be zero when route_status is watch or block")


def _normalize_team_queue_id(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_team_queue_id(field_name, value)


def _require_team_queue_id(field_name: str, value: object) -> str:
    if type(value) is not str or value not in TEAM_QUEUE_IDS:
        raise ValueError(f"{field_name} must be a known research team queue")
    return value


def _require_route_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in ROUTE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _normalize_confidence(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(CONFIDENCE_QUANTUM)


def _normalize_nonempty_public_string_tuple(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    items = _normalize_public_string_tuple(field_name, value)
    if not items:
        raise ValueError(f"{field_name} must contain canonical strings")
    return items


def _normalize_public_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple of canonical strings")
    for item in value:
        _require_canonical_public_string(field_name, item)
    return tuple(sorted(dict.fromkeys(value)))


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical strings")
    if _has_unsafe_public_text(value):
        raise ValueError(f"unsafe public value in {field_name}")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_key(key):
                raise ValueError(f"unsafe public field in payload: {key}")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_text(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_key(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_public_key(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in _UNSAFE_KEY_FRAGMENTS)


def _has_unsafe_public_text(value: str) -> bool:
    lowered = value.casefold()
    return any(pattern.search(lowered) is not None for pattern in _UNSAFE_VALUE_PATTERNS)


def _phrase_position(normalized_text: str, normalized_phrase: str) -> int | None:
    index = f" {normalized_text} ".find(f" {normalized_phrase} ")
    if index < 0:
        return None
    return index


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


__all__ = (
    "CONFIDENCE_QUANTUM",
    "RESEARCH_EVENT_TYPE_ROUTER_CONFIG_VERSION",
    "ROUTE_STATUSES",
    "TEAM_QUEUE_IDS",
    "ResearchMarketEventTypeInput",
    "ResearchMarketEventTypeRoute",
    "ResearchMarketEventTypeRouterConfig",
    "research_market_event_type_router_payload",
    "route_research_market_event_type",
)
