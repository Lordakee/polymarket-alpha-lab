"""Read-only Phase 1 health report for event archetype registry coverage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import TEAM_CATEGORIES


DEFAULT_CONFIG_VERSION = "event-archetype-registry-health-v0"
DEFAULT_DOMAIN_IDS = ("politics", "crypto", "macro", "commodities", "sports")
DOMAIN_TO_CATEGORY_IDS = {
    "politics": ("politics",),
    "crypto": ("finance.crypto.btc", "finance.crypto.eth"),
    "macro": ("finance.macro.rates", "finance.equity.indices"),
    "commodities": ("finance.commodities.gold", "finance.commodities.oil"),
    "sports": ("sports.soccer", "sports.basketball", "sports.other"),
}
CATEGORY_TO_DOMAIN_ID = {
    category_id: domain_id
    for domain_id, category_ids in DOMAIN_TO_CATEGORY_IDS.items()
    for category_id in category_ids
}
HEALTH_STATUSES = frozenset(("blocked", "watch", "pass"))
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECOND_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DEFAULT_MAX_TEMPLATE_AGE_SECONDS = Decimal("7776000")
SECONDS_PER_DAY = 86_400
MICROSECONDS_PER_SECOND = Decimal("1000000")


@dataclass(frozen=True)
class EventArchetypeRegistryHealthConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    required_domain_ids: tuple[str, ...] = DEFAULT_DOMAIN_IDS
    max_template_age_seconds: Decimal = DEFAULT_MAX_TEMPLATE_AGE_SECONDS
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
            "max_template_age_seconds",
            _normalize_seconds_decimal(
                "max_template_age_seconds",
                self.max_template_age_seconds,
            ),
        )
        require_paper_only_flags("event archetype registry health config", self)


@dataclass(frozen=True)
class EventArchetypeRegistryEntry:
    domain_id: str
    category_id: str
    archetype_id: str
    template_version: str
    updated_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain_id", _require_domain_id("domain_id", self.domain_id))
        object.__setattr__(
            self,
            "category_id",
            _require_category_id("category_id", self.category_id),
        )
        _require_category_domain_pair(self.domain_id, self.category_id)
        _require_canonical_string("archetype_id", self.archetype_id)
        _require_canonical_string("template_version", self.template_version)
        object.__setattr__(self, "updated_at", _as_utc("updated_at", self.updated_at))
        require_paper_only_flags("event archetype registry entry", self)


@dataclass(frozen=True)
class EventArchetypeRegistryObservation:
    event_fingerprint: str
    domain_id: str
    category_id: str
    archetype_id: str
    template_version: str
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("event_fingerprint", self.event_fingerprint)
        object.__setattr__(self, "domain_id", _require_domain_id("domain_id", self.domain_id))
        object.__setattr__(
            self,
            "category_id",
            _require_category_id("category_id", self.category_id),
        )
        _require_category_domain_pair(self.domain_id, self.category_id)
        _require_canonical_string("archetype_id", self.archetype_id)
        _require_canonical_string("template_version", self.template_version)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        require_paper_only_flags("event archetype registry observation", self)


@dataclass(frozen=True)
class EventArchetypeRegistryHealthRow:
    domain_id: str
    registered_archetype_count: Decimal
    observed_archetype_count: Decimal
    covered_archetype_count: Decimal
    missing_archetype_count: Decimal
    unknown_archetype_count: Decimal
    stale_template_count: Decimal
    template_version_mismatch_count: Decimal
    health_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain_id", _require_domain_id("domain_id", self.domain_id))
        for field_name in (
            "registered_archetype_count",
            "observed_archetype_count",
            "covered_archetype_count",
            "missing_archetype_count",
            "unknown_archetype_count",
            "stale_template_count",
            "template_version_mismatch_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_health_status("health_status", self.health_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        require_paper_only_flags("event archetype registry health row", self)


@dataclass(frozen=True)
class EventArchetypeRegistryHealthReport:
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    covered_domain_count: Decimal
    missing_domain_count: Decimal
    registered_archetype_count: Decimal
    observed_archetype_count: Decimal
    covered_archetype_count: Decimal
    unknown_archetype_count: Decimal
    stale_template_count: Decimal
    template_version_mismatch_count: Decimal
    archetype_coverage_ratio: Decimal
    rows: tuple[EventArchetypeRegistryHealthRow, ...]
    health_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "domain_count",
            "covered_domain_count",
            "missing_domain_count",
            "registered_archetype_count",
            "observed_archetype_count",
            "covered_archetype_count",
            "unknown_archetype_count",
            "stale_template_count",
            "template_version_mismatch_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "archetype_coverage_ratio",
            _normalize_ratio("archetype_coverage_ratio", self.archetype_coverage_ratio),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_health_status("health_status", self.health_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        require_paper_only_flags("event archetype registry health report", self)
        _validate_report_consistency(self)


def build_event_archetype_registry_health_report(
    registry_entries: object,
    observations: object,
    *,
    config: EventArchetypeRegistryHealthConfig,
    generated_at: datetime,
) -> EventArchetypeRegistryHealthReport:
    if type(config) is not EventArchetypeRegistryHealthConfig:
        raise ValueError("config must be an EventArchetypeRegistryHealthConfig")
    require_paper_only_flags("event archetype registry health config", config)
    generated_at = _as_utc("generated_at", generated_at)
    entries = _normalize_entries(registry_entries, generated_at=generated_at)
    observed = _normalize_observations(observations, generated_at=generated_at)

    rows = tuple(
        _build_domain_row(
            domain_id=domain_id,
            entries=entries,
            observations=observed,
            generated_at=generated_at,
            max_template_age_seconds=config.max_template_age_seconds,
        )
        for domain_id in config.required_domain_ids
    )
    covered_domain_count = _count_decimal(
        sum(1 for row in rows if row.registered_archetype_count > ZERO),
    )
    domain_count = _count_decimal(len(rows))
    missing_domain_count = domain_count - covered_domain_count
    unknown_archetype_count = sum((row.unknown_archetype_count for row in rows), ZERO)
    stale_template_count = sum((row.stale_template_count for row in rows), ZERO)
    template_version_mismatch_count = sum(
        (row.template_version_mismatch_count for row in rows),
        ZERO,
    )
    health_status = _report_health_status(
        missing_domain_count=missing_domain_count,
        unknown_archetype_count=unknown_archetype_count,
        stale_template_count=stale_template_count,
        template_version_mismatch_count=template_version_mismatch_count,
    )
    registered_archetype_count = sum(
        (row.registered_archetype_count for row in rows),
        ZERO,
    )
    covered_archetype_count = sum((row.covered_archetype_count for row in rows), ZERO)
    return EventArchetypeRegistryHealthReport(
        generated_at=generated_at,
        config_version=config.config_version,
        domain_count=domain_count,
        covered_domain_count=covered_domain_count,
        missing_domain_count=missing_domain_count,
        registered_archetype_count=registered_archetype_count,
        observed_archetype_count=sum((row.observed_archetype_count for row in rows), ZERO),
        covered_archetype_count=covered_archetype_count,
        unknown_archetype_count=unknown_archetype_count,
        stale_template_count=stale_template_count,
        template_version_mismatch_count=template_version_mismatch_count,
        archetype_coverage_ratio=_safe_ratio(covered_domain_count, domain_count),
        rows=rows,
        health_status=health_status,
        reason_codes=_report_reason_codes(
            missing_domain_count=missing_domain_count,
            unknown_archetype_count=unknown_archetype_count,
            stale_template_count=stale_template_count,
            template_version_mismatch_count=template_version_mismatch_count,
        ),
    )


def _build_domain_row(
    *,
    domain_id: str,
    entries: tuple[EventArchetypeRegistryEntry, ...],
    observations: tuple[EventArchetypeRegistryObservation, ...],
    generated_at: datetime,
    max_template_age_seconds: Decimal,
) -> EventArchetypeRegistryHealthRow:
    domain_entries = tuple(entry for entry in entries if entry.domain_id == domain_id)
    domain_observations = tuple(item for item in observations if item.domain_id == domain_id)
    entry_keys = frozenset(_archetype_key(entry) for entry in domain_entries)
    observed_keys = frozenset(_archetype_key(item) for item in domain_observations)
    covered_keys = entry_keys & observed_keys
    unknown_keys = observed_keys - entry_keys
    stale_template_count = _count_decimal(
        sum(
            1
            for entry in domain_entries
            if _age_seconds(generated_at, entry.updated_at) > max_template_age_seconds
        ),
    )
    template_version_mismatch_count = _count_decimal(
        sum(1 for item in domain_observations if _has_template_version_mismatch(item, entries)),
    )
    registered_archetype_count = _count_decimal(len(entry_keys))
    unknown_archetype_count = _count_decimal(len(unknown_keys))
    health_status = _row_health_status(
        registered_archetype_count=registered_archetype_count,
        unknown_archetype_count=unknown_archetype_count,
        stale_template_count=stale_template_count,
        template_version_mismatch_count=template_version_mismatch_count,
    )
    return EventArchetypeRegistryHealthRow(
        domain_id=domain_id,
        registered_archetype_count=registered_archetype_count,
        observed_archetype_count=_count_decimal(len(observed_keys)),
        covered_archetype_count=_count_decimal(len(covered_keys)),
        missing_archetype_count=_count_decimal(len(entry_keys - observed_keys)),
        unknown_archetype_count=unknown_archetype_count,
        stale_template_count=stale_template_count,
        template_version_mismatch_count=template_version_mismatch_count,
        health_status=health_status,
        reason_codes=_row_reason_codes(
            registered_archetype_count=registered_archetype_count,
            unknown_archetype_count=unknown_archetype_count,
            stale_template_count=stale_template_count,
            template_version_mismatch_count=template_version_mismatch_count,
        ),
    )


def _has_template_version_mismatch(
    item: EventArchetypeRegistryObservation,
    entries: tuple[EventArchetypeRegistryEntry, ...],
) -> bool:
    for entry in entries:
        if _archetype_key(entry) == _archetype_key(item):
            return entry.template_version != item.template_version
    return False


def _archetype_key(
    value: EventArchetypeRegistryEntry | EventArchetypeRegistryObservation,
) -> tuple[str, str, str]:
    return value.domain_id, value.category_id, value.archetype_id


def _row_health_status(
    *,
    registered_archetype_count: Decimal,
    unknown_archetype_count: Decimal,
    stale_template_count: Decimal,
    template_version_mismatch_count: Decimal,
) -> str:
    if registered_archetype_count == ZERO or unknown_archetype_count > ZERO:
        return "blocked"
    if stale_template_count > ZERO or template_version_mismatch_count > ZERO:
        return "watch"
    return "pass"


def _report_health_status(
    *,
    missing_domain_count: Decimal,
    unknown_archetype_count: Decimal,
    stale_template_count: Decimal,
    template_version_mismatch_count: Decimal,
) -> str:
    if missing_domain_count > ZERO or unknown_archetype_count > ZERO:
        return "blocked"
    if stale_template_count > ZERO or template_version_mismatch_count > ZERO:
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    missing_domain_count: Decimal,
    unknown_archetype_count: Decimal,
    stale_template_count: Decimal,
    template_version_mismatch_count: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if missing_domain_count > ZERO:
        codes.append("missing_event_archetype_domain_coverage")
    if unknown_archetype_count > ZERO:
        codes.append("unknown_event_archetypes_observed")
    if stale_template_count > ZERO:
        codes.append("stale_event_archetype_templates")
    if template_version_mismatch_count > ZERO:
        codes.append("event_archetype_template_version_mismatch")
    if not codes:
        codes.append("event_archetype_registry_health_passed")
    return tuple(codes)


def _row_reason_codes(
    *,
    registered_archetype_count: Decimal,
    unknown_archetype_count: Decimal,
    stale_template_count: Decimal,
    template_version_mismatch_count: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if registered_archetype_count == ZERO:
        codes.append("missing_event_archetype_domain_coverage")
    if unknown_archetype_count > ZERO:
        codes.append("unknown_event_archetypes_observed")
    if stale_template_count > ZERO:
        codes.append("stale_event_archetype_templates")
    if template_version_mismatch_count > ZERO:
        codes.append("event_archetype_template_version_mismatch")
    if not codes:
        codes.append("event_archetype_registry_domain_health_passed")
    return tuple(codes)


def _normalize_entries(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[EventArchetypeRegistryEntry, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("registry entries must be an iterable")
    try:
        entries = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("registry entries must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for entry in entries:
        if type(entry) is not EventArchetypeRegistryEntry:
            raise ValueError("registry entries must contain EventArchetypeRegistryEntry values")
        require_paper_only_flags("registry entries", entry)
        if entry.updated_at > generated_at:
            raise ValueError("updated_at must not be future")
        key = _archetype_key(entry)
        if key in seen_keys:
            raise ValueError("registry entries must be unique")
        seen_keys.add(key)
    return entries


def _normalize_observations(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[EventArchetypeRegistryObservation, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_fingerprints: set[str] = set()
    for item in observations:
        if type(item) is not EventArchetypeRegistryObservation:
            raise ValueError(
                "observations must contain EventArchetypeRegistryObservation values",
            )
        require_paper_only_flags("observations", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be future")
        if item.event_fingerprint in seen_fingerprints:
            raise ValueError("observations must be unique")
        seen_fingerprints.add(item.event_fingerprint)
    return observations


def _normalize_rows(value: object) -> tuple[EventArchetypeRegistryHealthRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not EventArchetypeRegistryHealthRow:
            raise ValueError("rows must contain EventArchetypeRegistryHealthRow values")
        require_paper_only_flags("event archetype registry health row", row)
    return rows


def _normalize_domain_ids(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        domain_ids = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not domain_ids:
        raise ValueError(f"{field_name} must contain at least one domain")
    for domain_id in domain_ids:
        _require_domain_id(field_name, domain_id)
    if len(set(domain_ids)) != len(domain_ids):
        raise ValueError(f"{field_name} must be unique")
    return domain_ids


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


def _normalize_seconds_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(SECOND_QUANTUM)


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
        codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain canonical strings") from exc
    if not codes:
        raise ValueError("reason_codes must contain canonical strings")
    for code in codes:
        _require_canonical_string("reason_codes", code)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    return codes


def _validate_report_consistency(report: EventArchetypeRegistryHealthReport) -> None:
    if report.domain_count != _count_decimal(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.covered_domain_count != _count_decimal(
        sum(1 for row in report.rows if row.registered_archetype_count > ZERO),
    ):
        raise ValueError("covered_domain_count must match rows")
    if report.missing_domain_count != report.domain_count - report.covered_domain_count:
        raise ValueError("missing_domain_count must match rows")
    if report.registered_archetype_count != sum(
        (row.registered_archetype_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("registered_archetype_count must match rows")
    if report.observed_archetype_count != sum(
        (row.observed_archetype_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("observed_archetype_count must match rows")
    if report.covered_archetype_count != sum(
        (row.covered_archetype_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("covered_archetype_count must match rows")
    if report.unknown_archetype_count != sum(
        (row.unknown_archetype_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("unknown_archetype_count must match rows")
    if report.stale_template_count != sum(
        (row.stale_template_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("stale_template_count must match rows")
    if report.template_version_mismatch_count != sum(
        (row.template_version_mismatch_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("template_version_mismatch_count must match rows")
    if report.archetype_coverage_ratio != _safe_ratio(
        report.covered_domain_count,
        report.domain_count,
    ):
        raise ValueError("archetype_coverage_ratio must match domain counts")
    expected_status = _report_health_status(
        missing_domain_count=report.missing_domain_count,
        unknown_archetype_count=report.unknown_archetype_count,
        stale_template_count=report.stale_template_count,
        template_version_mismatch_count=report.template_version_mismatch_count,
    )
    if report.health_status != expected_status:
        raise ValueError("health_status must match report counts")
    expected_codes = _report_reason_codes(
        missing_domain_count=report.missing_domain_count,
        unknown_archetype_count=report.unknown_archetype_count,
        stale_template_count=report.stale_template_count,
        template_version_mismatch_count=report.template_version_mismatch_count,
    )
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match report counts")


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _age_seconds(later_at: datetime, earlier_at: datetime) -> Decimal:
    delta = later_at - earlier_at
    whole_seconds = delta.days * SECONDS_PER_DAY + delta.seconds
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(whole_seconds) + (
            Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        )
    return seconds.quantize(SECOND_QUANTUM)


def _require_domain_id(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in DEFAULT_DOMAIN_IDS:
        raise ValueError(f"{field_name} must be a known domain")
    return value


def _require_category_id(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in TEAM_CATEGORIES:
        raise ValueError(f"{field_name} must be a known category")
    if value not in CATEGORY_TO_DOMAIN_ID:
        raise ValueError(f"{field_name} must map to an archetype domain")
    return value


def _require_category_domain_pair(domain_id: str, category_id: str) -> None:
    if CATEGORY_TO_DOMAIN_ID[category_id] != domain_id:
        raise ValueError("category_id must match domain_id")


def _require_health_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be a known health status")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "EventArchetypeRegistryEntry",
    "EventArchetypeRegistryHealthConfig",
    "EventArchetypeRegistryHealthReport",
    "EventArchetypeRegistryHealthRow",
    "EventArchetypeRegistryObservation",
    "build_event_archetype_registry_health_report",
)
