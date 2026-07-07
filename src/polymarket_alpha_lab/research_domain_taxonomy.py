"""Pure paper-only Polymarket event research domain taxonomy."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


CONFIDENCE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
DEFAULT_RESEARCH_DOMAIN_TAXONOMY_CONFIG_VERSION = "research-domain-taxonomy-v1"

RESEARCH_DOMAIN_IDS = (
    "politics",
    "macro",
    "crypto",
    "equity_index",
    "gold",
    "soccer",
    "basketball",
    "general",
)
PUBLIC_STATUSES = ("pass", "watch", "block")

_DOMAIN_CONFIDENCE = {
    "politics": Decimal("0.900000"),
    "macro": Decimal("0.850000"),
    "crypto": Decimal("0.900000"),
    "equity_index": Decimal("0.850000"),
    "gold": Decimal("0.850000"),
    "soccer": Decimal("0.850000"),
    "basketball": Decimal("0.850000"),
    "general": Decimal("0.500000"),
}

_CATEGORY_HINT_TO_DOMAIN_REASON = {
    "politics": ("politics", "category_hint_politics"),
    "politics.elections": ("politics", "category_hint_politics"),
    "economics": ("macro", "category_hint_macro"),
    "economics.macro": ("macro", "category_hint_macro"),
    "economics.central_banks": ("macro", "category_hint_macro"),
    "finance.macro": ("macro", "category_hint_macro"),
    "macro": ("macro", "category_hint_macro"),
    "finance.crypto": ("crypto", "category_hint_crypto"),
    "finance.crypto.etf": ("crypto", "category_hint_crypto"),
    "crypto": ("crypto", "category_hint_crypto"),
    "finance.equity.indices": ("equity_index", "category_hint_equity_index"),
    "finance.equities.indices": ("equity_index", "category_hint_equity_index"),
    "finance.indices": ("equity_index", "category_hint_equity_index"),
    "commodities.gold": ("gold", "category_hint_gold"),
    "finance.commodities.gold": ("gold", "category_hint_gold"),
    "sports.soccer": ("soccer", "category_hint_soccer"),
    "sports.basketball": ("basketball", "category_hint_basketball"),
}

_DOMAIN_KEYWORD_RULES = (
    (
        "crypto",
        "keyword_crypto",
        ("bitcoin", "btc", "ethereum", "eth", "solana", "crypto", "stablecoin"),
    ),
    (
        "equity_index",
        "keyword_equity_index",
        ("s&p", "spx", "s&p 500", "nasdaq", "dow", "equity index", "stock index"),
    ),
    ("gold", "keyword_gold", ("gold", "xau", "precious metal")),
    (
        "macro",
        "keyword_macro",
        (
            "federal reserve",
            "fed",
            "interest rate",
            "rate cut",
            "inflation",
            "cpi",
            "gdp",
            "unemployment",
            "recession",
            "treasury",
        ),
    ),
    (
        "politics",
        "keyword_politics",
        ("election", "president", "senate", "congress", "governor", "polling"),
    ),
    (
        "soccer",
        "keyword_soccer",
        (
            "soccer",
            "champions league",
            "uefa",
            "fifa",
            "world cup",
            "premier league",
            "real madrid",
        ),
    ),
    (
        "basketball",
        "keyword_basketball",
        ("basketball", "nba", "wnba", "ncaa basketball", "march madness"),
    ),
)

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
        r"\bmarket[-_ ]?(?:id|slug)\b",
        r"\bmarket slug\b",
        r"\bquestion\b",
        r"\bsource\b",
        r"\bref\b",
        r"https?://",
        r"\burl\b",
        r"\btext\b",
        r"\bdsn\b",
        r"\btable\b",
        r"\btoken\b",
        r"\bwallet\b",
        r"\bauth\b",
        r"\border\b",
        r"\btrade\b",
        r"\bposition\b",
        r"\bbuy\b",
        r"\bsell\b",
        r"\brecommend(?:ation|ed|ing)?\b",
    )
)


@dataclass(frozen=True)
class ResearchDomainTaxonomyConfig:
    config_version: str = DEFAULT_RESEARCH_DOMAIN_TAXONOMY_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        require_paper_only_flags("ResearchDomainTaxonomyConfig", self)


@dataclass(frozen=True)
class ResearchDomainClassificationInput:
    public_event_label: str
    public_category_hint: str
    public_tags: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("public_event_label", self.public_event_label)
        _require_canonical_public_string("public_category_hint", self.public_category_hint)
        object.__setattr__(
            self,
            "public_tags",
            _normalize_public_string_tuple("public_tags", self.public_tags),
        )
        require_paper_only_flags("ResearchDomainClassificationInput", self)


@dataclass(frozen=True)
class ResearchDomainClassificationRow:
    public_sequence: Decimal
    public_event_label: str
    research_domain_id: str
    research_subdomain_id: str
    public_status: str
    classification_confidence: Decimal
    reason_codes: tuple[str, ...]
    matched_public_terms: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "public_sequence",
            _normalize_count("public_sequence", self.public_sequence),
        )
        _require_canonical_public_string("public_event_label", self.public_event_label)
        object.__setattr__(
            self,
            "research_domain_id",
            _require_research_domain_id("research_domain_id", self.research_domain_id),
        )
        _require_canonical_public_string("research_subdomain_id", self.research_subdomain_id)
        object.__setattr__(
            self,
            "public_status",
            _require_public_status("public_status", self.public_status),
        )
        object.__setattr__(
            self,
            "classification_confidence",
            _normalize_confidence(
                "classification_confidence",
                self.classification_confidence,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_nonempty_public_string_tuple("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "matched_public_terms",
            _normalize_public_string_tuple(
                "matched_public_terms",
                self.matched_public_terms,
            ),
        )
        require_paper_only_flags("ResearchDomainClassificationRow", self)


@dataclass(frozen=True)
class ResearchDomainClassificationReport:
    generated_at: datetime
    config_version: str
    classification_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    rows: tuple[ResearchDomainClassificationRow, ...]
    reason_codes: tuple[str, ...] = ("research_domain_classification_report",)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "classification_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_nonempty_public_string_tuple("reason_codes", self.reason_codes),
        )
        _validate_report_counts(self)
        require_paper_only_flags("ResearchDomainClassificationReport", self)


def classify_research_domain(
    event: ResearchDomainClassificationInput,
    *,
    config: ResearchDomainTaxonomyConfig,
    public_sequence: Decimal = Decimal("1"),
) -> ResearchDomainClassificationRow:
    if type(event) is not ResearchDomainClassificationInput:
        raise ValueError("event must be a ResearchDomainClassificationInput")
    if type(config) is not ResearchDomainTaxonomyConfig:
        raise ValueError("config must be a ResearchDomainTaxonomyConfig")
    require_paper_only_flags("ResearchDomainClassificationInput", event)
    require_paper_only_flags("ResearchDomainTaxonomyConfig", config)

    domain_id, status, confidence, reason_codes, matched_terms = _classify_event(event)
    subdomain_id, subdomain_reason = _subdomain_for(domain_id, event)
    return ResearchDomainClassificationRow(
        public_sequence=public_sequence,
        public_event_label=event.public_event_label,
        research_domain_id=domain_id,
        research_subdomain_id=subdomain_id,
        public_status=status,
        classification_confidence=confidence,
        reason_codes=reason_codes + (subdomain_reason,),
        matched_public_terms=matched_terms,
    )


def build_research_domain_classification_report(
    inputs: tuple[ResearchDomainClassificationInput, ...] | list[ResearchDomainClassificationInput],
    *,
    config: ResearchDomainTaxonomyConfig,
    generated_at: datetime,
) -> ResearchDomainClassificationReport:
    if type(config) is not ResearchDomainTaxonomyConfig:
        raise ValueError("config must be a ResearchDomainTaxonomyConfig")
    source_inputs = _normalize_inputs(inputs)
    rows = tuple(
        classify_research_domain(
            event,
            config=config,
            public_sequence=Decimal(index).quantize(COUNT_QUANT),
        )
        for index, event in enumerate(source_inputs, start=1)
    )
    return ResearchDomainClassificationReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        classification_count=Decimal(len(rows)).quantize(COUNT_QUANT),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        rows=rows,
    )


def research_domain_classification_payload(
    report: ResearchDomainClassificationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainClassificationReport:
        require_paper_only_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchDomainClassificationReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
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


def _classify_event(
    event: ResearchDomainClassificationInput,
) -> tuple[str, str, Decimal, tuple[str, ...], tuple[str, ...]]:
    category_hint = event.public_category_hint.casefold()
    if category_hint == "sports.football":
        return _watch_result("ambiguous_football_domain")

    if category_hint in _CATEGORY_HINT_TO_DOMAIN_REASON:
        domain_id, reason_code = _CATEGORY_HINT_TO_DOMAIN_REASON[category_hint]
        return (
            domain_id,
            "pass",
            _DOMAIN_CONFIDENCE[domain_id],
            (reason_code,),
            (),
        )
    for prefix, domain_id, reason_code in (
        ("politics.", "politics", "category_hint_politics"),
        ("economics.", "macro", "category_hint_macro"),
        ("macro.", "macro", "category_hint_macro"),
        ("finance.crypto.", "crypto", "category_hint_crypto"),
        ("crypto.", "crypto", "category_hint_crypto"),
        ("finance.equity.", "equity_index", "category_hint_equity_index"),
        ("finance.equities.", "equity_index", "category_hint_equity_index"),
        ("commodities.gold.", "gold", "category_hint_gold"),
        ("finance.commodities.gold.", "gold", "category_hint_gold"),
        ("sports.soccer.", "soccer", "category_hint_soccer"),
        ("sports.basketball.", "basketball", "category_hint_basketball"),
    ):
        if category_hint.startswith(prefix):
            return (
                domain_id,
                "pass",
                _DOMAIN_CONFIDENCE[domain_id],
                (reason_code,),
                (),
            )

    haystack = _public_text(event)
    matches = tuple(
        (
            domain_id,
            reason_code,
            tuple(term for term in terms if term in haystack),
        )
        for domain_id, reason_code, terms in _DOMAIN_KEYWORD_RULES
    )
    nonempty_matches = tuple(match for match in matches if match[2])
    matched_domains = tuple(dict.fromkeys(match[0] for match in nonempty_matches))
    if len(matched_domains) > 1:
        return _watch_result("ambiguous_multi_domain_terms")
    if len(nonempty_matches) == 1:
        domain_id, reason_code, matched_terms = nonempty_matches[0]
        return (
            domain_id,
            "pass",
            _DOMAIN_CONFIDENCE[domain_id],
            (reason_code,),
            matched_terms,
        )
    return _watch_result("needs_human_triage")


def _watch_result(reason_code: str) -> tuple[str, str, Decimal, tuple[str, ...], tuple[str, ...]]:
    return (
        "general",
        "watch",
        _DOMAIN_CONFIDENCE["general"],
        ("needs_human_triage", reason_code),
        (),
    )


def _subdomain_for(
    domain_id: str,
    event: ResearchDomainClassificationInput,
) -> tuple[str, str]:
    category_hint = event.public_category_hint.casefold()
    haystack = _public_text(event)
    if domain_id == "politics":
        if any(term in haystack for term in ("senate", "congress", "house")):
            return "us_congress", "subdomain_us_congress"
        if any(term in haystack for term in ("president", "election", "polling")):
            return "elections", "subdomain_elections"
        return "politics_general", "subdomain_politics_general"
    if domain_id == "macro":
        if any(term in haystack for term in ("fed", "federal reserve", "rate", "treasury")):
            return "rates", "subdomain_rates"
        if any(term in haystack for term in ("inflation", "cpi")):
            return "inflation", "subdomain_inflation"
        return "macro_general", "subdomain_macro_general"
    if domain_id == "crypto":
        if "etf" in haystack and any(term in haystack for term in ("bitcoin", "btc")):
            return "btc_etf", "subdomain_btc_etf"
        if any(term in haystack for term in ("bitcoin", "btc")):
            return "bitcoin", "subdomain_bitcoin"
        if any(term in haystack for term in ("ethereum", "eth")):
            return "ethereum", "subdomain_ethereum"
        return "crypto_general", "subdomain_crypto_general"
    if domain_id == "equity_index":
        if "nasdaq" in haystack:
            return "nasdaq", "subdomain_nasdaq"
        if any(term in haystack for term in ("s&p", "spx", "s&p 500")):
            return "sp500", "subdomain_sp500"
        if "dow" in haystack:
            return "dow", "subdomain_dow"
        return "equity_index_general", "subdomain_equity_index_general"
    if domain_id == "gold":
        return "gold_price", "subdomain_gold_price"
    if domain_id == "soccer":
        if any(term in haystack for term in ("champions league", "uefa", "premier league")):
            return "club_competition", "subdomain_club_competition"
        if any(term in haystack for term in ("fifa", "world cup")):
            return "international", "subdomain_international"
        return "soccer_general", "subdomain_soccer_general"
    if domain_id == "basketball":
        if "wnba" in haystack:
            return "wnba", "subdomain_wnba"
        if "nba" in haystack:
            return "nba", "subdomain_nba"
        if any(term in haystack for term in ("ncaa", "march madness")):
            return "college", "subdomain_college"
        return "basketball_general", "subdomain_basketball_general"
    if domain_id == "general" and category_hint == "sports.football":
        return "needs_triage", "subdomain_needs_triage"
    return "needs_triage", "subdomain_needs_triage"


def _public_text(event: ResearchDomainClassificationInput) -> str:
    return " ".join(
        (
            event.public_event_label,
            event.public_category_hint,
            " ".join(event.public_tags),
        )
    ).casefold()


def _normalize_inputs(
    inputs: tuple[ResearchDomainClassificationInput, ...] | list[ResearchDomainClassificationInput],
) -> tuple[ResearchDomainClassificationInput, ...]:
    if isinstance(inputs, (str, bytes)) or type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    items = tuple(inputs)
    for item in items:
        if type(item) is not ResearchDomainClassificationInput:
            raise ValueError("inputs must contain ResearchDomainClassificationInput values")
        require_paper_only_flags("ResearchDomainClassificationInput", item)
    return items


def _normalize_rows(
    rows: tuple[ResearchDomainClassificationRow, ...],
) -> tuple[ResearchDomainClassificationRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain ResearchDomainClassificationRow values")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must contain ResearchDomainClassificationRow values") from exc
    for item in items:
        if type(item) is not ResearchDomainClassificationRow:
            raise ValueError("rows must contain ResearchDomainClassificationRow values")
        require_paper_only_flags("ResearchDomainClassificationRow", item)
    return items


def _status_count(
    rows: tuple[ResearchDomainClassificationRow, ...],
    public_status: str,
) -> Decimal:
    return Decimal(
        sum(1 for row in rows if row.public_status == public_status),
    ).quantize(COUNT_QUANT)


def _validate_report_counts(report: ResearchDomainClassificationReport) -> None:
    if report.classification_count != Decimal(len(report.rows)).quantize(COUNT_QUANT):
        raise ValueError("classification_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")


def _require_research_domain_id(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_DOMAIN_IDS:
        raise ValueError(f"{field_name} must be a known research domain")
    return value


def _require_public_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _normalize_confidence(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0") or value > Decimal("1"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(CONFIDENCE_QUANT)


def _normalize_count(field_name: str, value: object) -> Decimal:
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


def _normalize_nonempty_public_string_tuple(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    items = _normalize_public_string_tuple(field_name, value)
    if not items:
        raise ValueError(f"{field_name} must contain canonical strings")
    return items


def _normalize_public_string_tuple(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    for item in items:
        _require_canonical_public_string(field_name, item)
    return items


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical strings")
    if _has_unsafe_public_text(value):
        raise ValueError(f"unsafe public value in {field_name}")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
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
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
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


__all__ = (
    "CONFIDENCE_QUANT",
    "COUNT_QUANT",
    "DEFAULT_RESEARCH_DOMAIN_TAXONOMY_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "RESEARCH_DOMAIN_IDS",
    "ResearchDomainClassificationInput",
    "ResearchDomainClassificationReport",
    "ResearchDomainClassificationRow",
    "ResearchDomainTaxonomyConfig",
    "build_research_domain_classification_report",
    "classify_research_domain",
    "research_domain_classification_payload",
)
