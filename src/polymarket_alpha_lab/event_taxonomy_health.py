"""Read-only Phase 1 health report for event taxonomy routing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import (
    TEAM_CATEGORIES,
    TEAM_IDS,
    TEAM_ID_TO_PRIMARY_CATEGORY,
)


DEFAULT_CONFIG_VERSION = "event-taxonomy-health-v0"
REQUIRED_DOMAIN_IDS = ("politics", "crypto_btc", "macro_rates", "sports")
SPORTS_CATEGORY_IDS = ("sports.soccer", "sports.basketball", "sports.other")
SPORTS_TEAM_IDS = ("sports_soccer", "sports_basketball", "sports_other")
CATEGORY_TO_DOMAIN_ID = {
    "politics": "politics",
    "finance.crypto.btc": "crypto_btc",
    "finance.crypto.eth": "crypto_btc",
    "finance.macro.rates": "macro_rates",
    "finance.equity.indices": "macro_rates",
    "finance.commodities.gold": "macro_rates",
    "finance.commodities.oil": "macro_rates",
    "sports.soccer": "sports",
    "sports.basketball": "sports",
    "sports.other": "sports",
}
TEAM_TO_DOMAIN_ID = {
    "politics": "politics",
    "crypto_btc": "crypto_btc",
    "crypto_eth": "crypto_btc",
    "macro_rates": "macro_rates",
    "equity_indices": "macro_rates",
    "commodities_gold": "macro_rates",
    "commodities_oil": "macro_rates",
    "sports_soccer": "sports",
    "sports_basketball": "sports",
    "sports_other": "sports",
}
EXPECTED_TEMPLATES_BY_CATEGORY = {
    "politics": ("politics_event", "election_winner", "political_approval"),
    "finance.crypto.btc": ("btc_hit_price", "btc_range", "crypto_btc_event"),
    "finance.crypto.eth": ("eth_hit_price", "eth_range", "crypto_eth_event"),
    "finance.macro.rates": (
        "fed_rate_decision",
        "macro_rates_event",
        "rate_cut_count",
    ),
    "finance.equity.indices": ("index_close_above", "equity_indices_event"),
    "finance.commodities.gold": ("gold_hit_price", "commodities_gold_event"),
    "finance.commodities.oil": ("oil_hit_price", "commodities_oil_event"),
    "sports.soccer": ("sports_match_winner", "soccer_match_winner"),
    "sports.basketball": ("sports_match_winner", "basketball_match_winner"),
    "sports.other": ("sports_match_winner", "sports_event"),
}
STATUSES = frozenset(("blocked", "watch", "pass"))
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")


@dataclass(frozen=True)
class EventTaxonomyHealthConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    required_domain_ids: tuple[str, ...] = REQUIRED_DOMAIN_IDS
    min_events_per_domain: Decimal = COUNT_QUANTUM
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_domain_ids",
            _normalize_domain_ids("required_domain_ids", self.required_domain_ids),
        )
        object.__setattr__(
            self,
            "min_events_per_domain",
            _normalize_count_decimal(
                "min_events_per_domain",
                self.min_events_per_domain,
            ),
        )
        require_paper_only_flags("event taxonomy health config", self)


@dataclass(frozen=True)
class EventTaxonomyObservation:
    event_fingerprint: str
    category_hint: str
    routed_category_id: str | None
    routed_team_id: str | None
    event_template: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("event_fingerprint", "category_hint", "event_template"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "routed_category_id",
            _normalize_optional_known_category(
                "routed_category_id",
                self.routed_category_id,
            ),
        )
        object.__setattr__(
            self,
            "routed_team_id",
            _normalize_optional_known_team("routed_team_id", self.routed_team_id),
        )
        require_paper_only_flags("event taxonomy observation", self)


@dataclass(frozen=True)
class EventTaxonomyHealthRow:
    domain_id: str
    expected_category_count: Decimal
    observed_event_count: Decimal
    covered_category_count: Decimal
    missing_category_count: Decimal
    unknown_category_count: Decimal
    unroutable_unknown_category_count: Decimal
    template_drift_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_domain_id("domain_id", self.domain_id)
        for field_name in (
            "expected_category_count",
            "observed_event_count",
            "covered_category_count",
            "missing_category_count",
            "unknown_category_count",
            "unroutable_unknown_category_count",
            "template_drift_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("event taxonomy health row", self)


@dataclass(frozen=True)
class EventTaxonomyHealthReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    required_domain_count: Decimal
    covered_domain_count: Decimal
    missing_domain_count: Decimal
    unknown_category_count: Decimal
    unroutable_unknown_category_count: Decimal
    template_drift_count: Decimal
    coverage_ratio: Decimal
    rows: tuple[EventTaxonomyHealthRow, ...]
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "required_domain_count",
            "covered_domain_count",
            "missing_domain_count",
            "unknown_category_count",
            "unroutable_unknown_category_count",
            "template_drift_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "coverage_ratio",
            _normalize_ratio("coverage_ratio", self.coverage_ratio),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("event taxonomy health report", self)


def build_event_taxonomy_health_report(
    observations: object,
    *,
    config: EventTaxonomyHealthConfig,
    generated_at: datetime,
) -> EventTaxonomyHealthReport:
    if type(config) is not EventTaxonomyHealthConfig:
        raise ValueError("config must be an EventTaxonomyHealthConfig")
    require_paper_only_flags("event taxonomy health config", config)
    generated_at = _as_utc("generated_at", generated_at)
    observation_rows = _normalize_observations(observations)

    rows = tuple(
        _build_domain_row(
            domain_id=domain_id,
            observations=observation_rows,
            min_events_per_domain=config.min_events_per_domain,
        )
        for domain_id in config.required_domain_ids
    )
    covered_domain_count = _count_decimal(
        sum(1 for row in rows if row.observed_event_count >= config.min_events_per_domain),
    )
    required_domain_count = _count_decimal(len(config.required_domain_ids))
    missing_domain_count = required_domain_count - covered_domain_count
    unknown_category_count = _count_decimal(
        sum(1 for item in observation_rows if _is_unknown_category(item)),
    )
    unroutable_unknown_category_count = _count_decimal(
        sum(1 for item in observation_rows if _is_unroutable_unknown_category(item)),
    )
    template_drift_count = _count_decimal(
        sum(1 for item in observation_rows if _has_template_drift(item)),
    )
    status = _report_status(
        missing_domain_count=missing_domain_count,
        unroutable_unknown_category_count=unroutable_unknown_category_count,
        template_drift_count=template_drift_count,
        unknown_category_count=unknown_category_count,
    )
    return EventTaxonomyHealthReport(
        generated_at=generated_at,
        config_version=config.config_version,
        event_count=_count_decimal(len(observation_rows)),
        required_domain_count=required_domain_count,
        covered_domain_count=covered_domain_count,
        missing_domain_count=missing_domain_count,
        unknown_category_count=unknown_category_count,
        unroutable_unknown_category_count=unroutable_unknown_category_count,
        template_drift_count=template_drift_count,
        coverage_ratio=_safe_ratio(covered_domain_count, required_domain_count),
        rows=rows,
        status=status,
        reason_codes=_report_reason_codes(
            missing_domain_count=missing_domain_count,
            unroutable_unknown_category_count=unroutable_unknown_category_count,
            template_drift_count=template_drift_count,
            unknown_category_count=unknown_category_count,
        ),
    )


def _build_domain_row(
    *,
    domain_id: str,
    observations: tuple[EventTaxonomyObservation, ...],
    min_events_per_domain: Decimal,
) -> EventTaxonomyHealthRow:
    expected_categories = _expected_categories_for_domain(domain_id)
    domain_observations = tuple(
        item for item in observations if _observation_domain_id(item) == domain_id
    )
    covered_categories = frozenset(
        item.routed_category_id
        for item in domain_observations
        if item.routed_category_id in expected_categories
    )
    missing_category_count = len(expected_categories) - len(covered_categories)
    unknown_category_count = sum(1 for item in domain_observations if _is_unknown_category(item))
    unroutable_unknown_category_count = sum(
        1 for item in domain_observations if _is_unroutable_unknown_category(item)
    )
    template_drift_count = sum(1 for item in domain_observations if _has_template_drift(item))
    observed_event_count = _count_decimal(len(domain_observations))
    status = _row_status(
        observed_event_count=observed_event_count,
        min_events_per_domain=min_events_per_domain,
        unroutable_unknown_category_count=_count_decimal(unroutable_unknown_category_count),
        template_drift_count=_count_decimal(template_drift_count),
    )
    return EventTaxonomyHealthRow(
        domain_id=domain_id,
        expected_category_count=_count_decimal(len(expected_categories)),
        observed_event_count=observed_event_count,
        covered_category_count=_count_decimal(len(covered_categories)),
        missing_category_count=_count_decimal(missing_category_count),
        unknown_category_count=_count_decimal(unknown_category_count),
        unroutable_unknown_category_count=_count_decimal(unroutable_unknown_category_count),
        template_drift_count=_count_decimal(template_drift_count),
        status=status,
        reason_codes=_row_reason_codes(
            observed_event_count=observed_event_count,
            min_events_per_domain=min_events_per_domain,
            unroutable_unknown_category_count=_count_decimal(
                unroutable_unknown_category_count,
            ),
            template_drift_count=_count_decimal(template_drift_count),
            unknown_category_count=_count_decimal(unknown_category_count),
        ),
    )


def _report_status(
    *,
    missing_domain_count: Decimal,
    unroutable_unknown_category_count: Decimal,
    template_drift_count: Decimal,
    unknown_category_count: Decimal,
) -> str:
    if missing_domain_count > ZERO or unroutable_unknown_category_count > ZERO:
        return "blocked"
    if template_drift_count > ZERO or unknown_category_count > ZERO:
        return "watch"
    return "pass"


def _row_status(
    *,
    observed_event_count: Decimal,
    min_events_per_domain: Decimal,
    unroutable_unknown_category_count: Decimal,
    template_drift_count: Decimal,
) -> str:
    if (
        observed_event_count < min_events_per_domain
        or unroutable_unknown_category_count > ZERO
    ):
        return "blocked"
    if template_drift_count > ZERO:
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    missing_domain_count: Decimal,
    unroutable_unknown_category_count: Decimal,
    template_drift_count: Decimal,
    unknown_category_count: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if missing_domain_count > ZERO:
        codes.append("event_taxonomy_missing_domain_coverage")
    if unroutable_unknown_category_count > ZERO:
        codes.append("event_taxonomy_unroutable_unknown_category")
    if template_drift_count > ZERO:
        codes.append("event_taxonomy_template_drift")
    if unknown_category_count > unroutable_unknown_category_count:
        codes.append("event_taxonomy_sports_unknown_category")
    if not codes:
        codes.append("event_taxonomy_health_passed")
    return tuple(codes)


def _row_reason_codes(
    *,
    observed_event_count: Decimal,
    min_events_per_domain: Decimal,
    unroutable_unknown_category_count: Decimal,
    template_drift_count: Decimal,
    unknown_category_count: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if observed_event_count < min_events_per_domain:
        codes.append("event_taxonomy_missing_domain_coverage")
    if unroutable_unknown_category_count > ZERO:
        codes.append("event_taxonomy_unroutable_unknown_category")
    if template_drift_count > ZERO:
        codes.append("event_taxonomy_template_drift")
    if unknown_category_count > unroutable_unknown_category_count:
        codes.append("event_taxonomy_sports_unknown_category")
    if not codes:
        codes.append("event_taxonomy_domain_health_passed")
    return tuple(codes)


def _normalize_observations(value: object) -> tuple[EventTaxonomyObservation, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for item in items:
        if type(item) is not EventTaxonomyObservation:
            raise ValueError("observations must contain EventTaxonomyObservation values")
        require_paper_only_flags("event taxonomy observation", item)
    return items


def _normalize_rows(value: object) -> tuple[EventTaxonomyHealthRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        if type(item) is not EventTaxonomyHealthRow:
            raise ValueError("rows must contain EventTaxonomyHealthRow values")
        require_paper_only_flags("event taxonomy health row", item)
    return items


def _observation_domain_id(item: EventTaxonomyObservation) -> str | None:
    if item.routed_category_id in CATEGORY_TO_DOMAIN_ID:
        return CATEGORY_TO_DOMAIN_ID[item.routed_category_id]
    if item.routed_team_id in TEAM_TO_DOMAIN_ID:
        return TEAM_TO_DOMAIN_ID[item.routed_team_id]
    if item.category_hint.startswith("sports.unknown"):
        return "sports"
    if item.category_hint in CATEGORY_TO_DOMAIN_ID:
        return CATEGORY_TO_DOMAIN_ID[item.category_hint]
    return None


def _expected_categories_for_domain(domain_id: str) -> tuple[str, ...]:
    return tuple(
        category_id
        for category_id, candidate_domain_id in CATEGORY_TO_DOMAIN_ID.items()
        if candidate_domain_id == domain_id
    )


def _is_unknown_category(item: EventTaxonomyObservation) -> bool:
    return item.category_hint not in TEAM_CATEGORIES


def _is_unroutable_unknown_category(item: EventTaxonomyObservation) -> bool:
    return _is_unknown_category(item) and item.routed_category_id is None


def _has_template_drift(item: EventTaxonomyObservation) -> bool:
    if item.routed_category_id not in EXPECTED_TEMPLATES_BY_CATEGORY:
        return True
    return item.event_template not in EXPECTED_TEMPLATES_BY_CATEGORY[item.routed_category_id]


def _normalize_domain_ids(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one domain")
    for item in items:
        _require_domain_id(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must be unique")
    return items


def _normalize_optional_known_category(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    if value not in TEAM_CATEGORIES:
        raise ValueError(f"{field_name} must be a known category")
    return value


def _normalize_optional_known_team(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    if value not in TEAM_IDS:
        raise ValueError(f"{field_name} must be a known team")
    return value


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return value.quantize(COUNT_QUANTUM)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return value.quantize(RATIO_QUANTUM)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain canonical strings") from exc
    if not items:
        raise ValueError("reason_codes must contain canonical strings")
    for item in items:
        _require_canonical_string("reason_codes", item)
    return items


def _require_domain_id(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REQUIRED_DOMAIN_IDS:
        raise ValueError(f"{field_name} must be a known required domain")


def _require_status(value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError("status must be a known status")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "EventTaxonomyHealthConfig",
    "EventTaxonomyHealthReport",
    "EventTaxonomyHealthRow",
    "EventTaxonomyObservation",
    "build_event_taxonomy_health_report",
)
