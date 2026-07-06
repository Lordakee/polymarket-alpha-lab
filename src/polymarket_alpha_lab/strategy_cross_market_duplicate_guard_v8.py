"""Pure typed cross-market duplicate guard v8 report reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_CROSS_MARKET_DUPLICATE_GUARD_V8_CONFIG_VERSION = (
    "strategy-cross-market-duplicate-guard-v8"
)
DECIMAL_CONTEXT = Context(prec=64)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")

DUPLICATE_STATUSES = ("canonical", "duplicate", "unique")
REPORT_STATUSES = ("clear", "duplicates_found")
REASON_CODES = (
    "no_markets_supplied",
    "same_event_slug",
    "resolution_criteria_highly_similar",
    "canonical_market_selected",
    "duplicate_of_canonical_market",
    "no_cross_market_duplicate_detected",
    "cross_market_duplicates_found",
)
CRITERIA_STOPWORDS = frozenset(
    (
        "a",
        "an",
        "if",
        "market",
        "on",
        "resolve",
        "resolves",
        "the",
        "this",
    ),
)

__all__ = (
    "DEFAULT_STRATEGY_CROSS_MARKET_DUPLICATE_GUARD_V8_CONFIG_VERSION",
    "StrategyCrossMarketDuplicateGuardV8Config",
    "StrategyCrossMarketDuplicateGuardV8Market",
    "StrategyCrossMarketDuplicateGuardV8Report",
    "StrategyCrossMarketDuplicateGuardV8Row",
    "build_strategy_cross_market_duplicate_guard_v8_report",
    "strategy_cross_market_duplicate_guard_v8_payload",
)


@dataclass(frozen=True)
class StrategyCrossMarketDuplicateGuardV8Config:
    config_version: str = DEFAULT_STRATEGY_CROSS_MARKET_DUPLICATE_GUARD_V8_CONFIG_VERSION
    criteria_similarity_duplicate_threshold: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "criteria_similarity_duplicate_threshold",
            _normalize_ratio(
                "criteria_similarity_duplicate_threshold",
                self.criteria_similarity_duplicate_threshold,
            ),
        )
        require_paper_only_flags("StrategyCrossMarketDuplicateGuardV8Config", self)
        reject_unsafe_surface_fields("strategy cross market duplicate guard v8 config", self)


@dataclass(frozen=True)
class StrategyCrossMarketDuplicateGuardV8Market:
    market_slug: str
    event_slug: str | None
    question: str
    resolution_criteria: str
    research_priority_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "event_slug",
            _normalize_optional_canonical_string("event_slug", self.event_slug),
        )
        _require_canonical_string("question", self.question)
        _require_canonical_string("resolution_criteria", self.resolution_criteria)
        object.__setattr__(
            self,
            "research_priority_score",
            _normalize_ratio("research_priority_score", self.research_priority_score),
        )
        require_paper_only_flags("StrategyCrossMarketDuplicateGuardV8Market", self)
        reject_unsafe_surface_fields("strategy cross market duplicate guard v8 market", self)


@dataclass(frozen=True)
class StrategyCrossMarketDuplicateGuardV8Row:
    market_slug: str
    event_slug: str | None
    question: str
    resolution_criteria: str
    research_priority_score: Decimal
    duplicate_status: str
    canonical_market_slug: str
    duplicate_group_id: str
    group_market_count: Decimal
    criteria_similarity_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "event_slug",
            _normalize_optional_canonical_string("event_slug", self.event_slug),
        )
        _require_canonical_string("question", self.question)
        _require_canonical_string("resolution_criteria", self.resolution_criteria)
        object.__setattr__(
            self,
            "research_priority_score",
            _normalize_ratio("research_priority_score", self.research_priority_score),
        )
        _require_member("duplicate_status", self.duplicate_status, DUPLICATE_STATUSES)
        _require_canonical_string("canonical_market_slug", self.canonical_market_slug)
        _require_canonical_string("duplicate_group_id", self.duplicate_group_id)
        object.__setattr__(
            self,
            "group_market_count",
            _normalize_nonnegative_count("group_market_count", self.group_market_count),
        )
        object.__setattr__(
            self,
            "criteria_similarity_score",
            _normalize_ratio("criteria_similarity_score", self.criteria_similarity_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        require_paper_only_flags("StrategyCrossMarketDuplicateGuardV8Row", self)
        reject_unsafe_surface_fields("strategy cross market duplicate guard v8 row", self)


@dataclass(frozen=True)
class StrategyCrossMarketDuplicateGuardV8Report:
    generated_at: datetime
    config_version: str
    duplicate_status: str
    market_count: Decimal
    duplicate_group_count: Decimal
    canonical_market_count: Decimal
    duplicate_market_count: Decimal
    unique_market_count: Decimal
    rows: tuple[StrategyCrossMarketDuplicateGuardV8Row, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("duplicate_status", self.duplicate_status, REPORT_STATUSES)
        for field_name in (
            "market_count",
            "duplicate_group_count",
            "canonical_market_count",
            "duplicate_market_count",
            "unique_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report(self)
        require_paper_only_flags("StrategyCrossMarketDuplicateGuardV8Report", self)
        reject_unsafe_surface_fields("strategy cross market duplicate guard v8 report", self)


def build_strategy_cross_market_duplicate_guard_v8_report(
    markets: tuple[StrategyCrossMarketDuplicateGuardV8Market, ...],
    *,
    config: StrategyCrossMarketDuplicateGuardV8Config | None = None,
    generated_at: datetime,
) -> StrategyCrossMarketDuplicateGuardV8Report:
    active_config = config if config is not None else StrategyCrossMarketDuplicateGuardV8Config()
    if type(active_config) is not StrategyCrossMarketDuplicateGuardV8Config:
        raise ValueError("config must be a StrategyCrossMarketDuplicateGuardV8Config")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_markets = _normalize_markets(markets)
    rows = _duplicate_rows(normalized_markets, active_config)
    duplicate_market_count = _count(sum(row.duplicate_status == "duplicate" for row in rows))
    canonical_market_count = _count(sum(row.duplicate_status == "canonical" for row in rows))
    unique_market_count = _count(sum(row.duplicate_status == "unique" for row in rows))
    duplicate_group_count = _count(len({row.duplicate_group_id for row in rows if row.duplicate_status != "unique"}))
    duplicate_status = "duplicates_found" if duplicate_market_count > ZERO_COUNT else "clear"
    return StrategyCrossMarketDuplicateGuardV8Report(
        generated_at=generated_at,
        config_version=active_config.config_version,
        duplicate_status=duplicate_status,
        market_count=_count(len(rows)),
        duplicate_group_count=duplicate_group_count,
        canonical_market_count=canonical_market_count,
        duplicate_market_count=duplicate_market_count,
        unique_market_count=unique_market_count,
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def strategy_cross_market_duplicate_guard_v8_payload(
    report: StrategyCrossMarketDuplicateGuardV8Report,
) -> dict[str, Any]:
    if type(report) is not StrategyCrossMarketDuplicateGuardV8Report:
        raise ValueError("report must be a StrategyCrossMarketDuplicateGuardV8Report")
    require_paper_only_flags("StrategyCrossMarketDuplicateGuardV8Report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _duplicate_rows(
    markets: tuple[StrategyCrossMarketDuplicateGuardV8Market, ...],
    config: StrategyCrossMarketDuplicateGuardV8Config,
) -> tuple[StrategyCrossMarketDuplicateGuardV8Row, ...]:
    grouped_slugs: set[str] = set()
    rows: list[StrategyCrossMarketDuplicateGuardV8Row] = []

    for event_slug, event_markets in _same_event_groups(markets):
        rows.extend(
            _rows_for_group(
                event_markets,
                group_id=f"event:{event_slug}",
                group_reason_code="same_event_slug",
                similarity_source="event",
            ),
        )
        grouped_slugs.update(market.market_slug for market in event_markets)

    remaining_markets = tuple(
        market for market in markets if market.market_slug not in grouped_slugs
    )
    for criteria_markets in _criteria_groups(
        remaining_markets,
        config.criteria_similarity_duplicate_threshold,
    ):
        canonical = _canonical_market(criteria_markets)
        rows.extend(
            _rows_for_group(
                criteria_markets,
                group_id=f"criteria:{canonical.market_slug}",
                group_reason_code="resolution_criteria_highly_similar",
                similarity_source="criteria",
            ),
        )
        grouped_slugs.update(market.market_slug for market in criteria_markets)

    for market in markets:
        if market.market_slug in grouped_slugs:
            continue
        rows.append(_unique_row(market))

    return tuple(sorted(rows, key=_row_sort_key))


def _same_event_groups(
    markets: tuple[StrategyCrossMarketDuplicateGuardV8Market, ...],
) -> tuple[tuple[str, tuple[StrategyCrossMarketDuplicateGuardV8Market, ...]], ...]:
    by_event: dict[str, list[StrategyCrossMarketDuplicateGuardV8Market]] = {}
    for market in markets:
        if market.event_slug is None:
            continue
        by_event.setdefault(market.event_slug, []).append(market)
    groups = []
    for event_slug, event_markets in by_event.items():
        if len(event_markets) < 2:
            continue
        groups.append((event_slug, tuple(sorted(event_markets, key=lambda item: item.market_slug))))
    return tuple(sorted(groups, key=lambda item: item[0]))


def _criteria_groups(
    markets: tuple[StrategyCrossMarketDuplicateGuardV8Market, ...],
    threshold: Decimal,
) -> tuple[tuple[StrategyCrossMarketDuplicateGuardV8Market, ...], ...]:
    if len(markets) < 2:
        return ()
    slugs = tuple(market.market_slug for market in markets)
    parents = {slug: slug for slug in slugs}

    for left_index, left_market in enumerate(markets):
        for right_market in markets[left_index + 1 :]:
            if _criteria_similarity(left_market.resolution_criteria, right_market.resolution_criteria) >= threshold:
                _union(parents, left_market.market_slug, right_market.market_slug)

    components: dict[str, list[StrategyCrossMarketDuplicateGuardV8Market]] = {}
    for market in markets:
        components.setdefault(_find_parent(parents, market.market_slug), []).append(market)

    groups = []
    for component_markets in components.values():
        if len(component_markets) < 2:
            continue
        groups.append(tuple(sorted(component_markets, key=lambda item: item.market_slug)))
    return tuple(sorted(groups, key=lambda group: _canonical_market(group).market_slug))


def _rows_for_group(
    markets: tuple[StrategyCrossMarketDuplicateGuardV8Market, ...],
    *,
    group_id: str,
    group_reason_code: str,
    similarity_source: str,
) -> tuple[StrategyCrossMarketDuplicateGuardV8Row, ...]:
    canonical = _canonical_market(markets)
    rows = []
    for market in markets:
        duplicate_status = "canonical" if market.market_slug == canonical.market_slug else "duplicate"
        row_reason = (
            group_reason_code,
            "canonical_market_selected"
            if duplicate_status == "canonical"
            else "duplicate_of_canonical_market",
        )
        similarity = (
            ONE_RATIO
            if similarity_source == "event" or duplicate_status == "canonical"
            else _criteria_similarity(canonical.resolution_criteria, market.resolution_criteria)
        )
        rows.append(
            StrategyCrossMarketDuplicateGuardV8Row(
                market_slug=market.market_slug,
                event_slug=market.event_slug,
                question=market.question,
                resolution_criteria=market.resolution_criteria,
                research_priority_score=market.research_priority_score,
                duplicate_status=duplicate_status,
                canonical_market_slug=canonical.market_slug,
                duplicate_group_id=group_id,
                group_market_count=_count(len(markets)),
                criteria_similarity_score=similarity,
                reason_codes=row_reason,
            ),
        )
    return tuple(rows)


def _unique_row(
    market: StrategyCrossMarketDuplicateGuardV8Market,
) -> StrategyCrossMarketDuplicateGuardV8Row:
    return StrategyCrossMarketDuplicateGuardV8Row(
        market_slug=market.market_slug,
        event_slug=market.event_slug,
        question=market.question,
        resolution_criteria=market.resolution_criteria,
        research_priority_score=market.research_priority_score,
        duplicate_status="unique",
        canonical_market_slug=market.market_slug,
        duplicate_group_id=f"unique:{market.market_slug}",
        group_market_count=ONE_RATIO,
        criteria_similarity_score=ONE_RATIO,
        reason_codes=("no_cross_market_duplicate_detected",),
    )


def _canonical_market(
    markets: tuple[StrategyCrossMarketDuplicateGuardV8Market, ...],
) -> StrategyCrossMarketDuplicateGuardV8Market:
    return sorted(markets, key=lambda market: (-market.research_priority_score, market.market_slug))[0]


def _criteria_similarity(left: str, right: str) -> Decimal:
    left_tokens = _criteria_tokens(left)
    right_tokens = _criteria_tokens(right)
    if not left_tokens or not right_tokens:
        return ZERO_RATIO
    left_counts = _token_counts(left_tokens)
    right_counts = _token_counts(right_tokens)
    common_count = sum(min(left_counts.get(token, 0), right_counts.get(token, 0)) for token in left_counts)
    base_count = max(len(left_tokens), len(right_tokens))
    if base_count == 0:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(common_count) / Decimal(base_count)).quantize(RATIO_QUANTUM)


def _criteria_tokens(value: str) -> tuple[str, ...]:
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    return tuple(token for token in tokens if token not in CRITERIA_STOPWORDS)


def _token_counts(tokens: tuple[str, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return counts


def _report_reason_codes(
    rows: tuple[StrategyCrossMarketDuplicateGuardV8Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_markets_supplied",)
    reason_codes: list[str] = []
    for group_reason_code in (
        "same_event_slug",
        "resolution_criteria_highly_similar",
    ):
        if any(group_reason_code in row.reason_codes for row in rows):
            reason_codes.append(group_reason_code)
    if reason_codes:
        reason_codes.append("cross_market_duplicates_found")
        return tuple(reason_codes)
    return ("no_cross_market_duplicate_detected",)


def _row_sort_key(row: StrategyCrossMarketDuplicateGuardV8Row) -> tuple[int, str, str]:
    priority = {"canonical": 0, "duplicate": 1, "unique": 2}[row.duplicate_status]
    return (priority, row.duplicate_group_id, row.market_slug)


def _normalize_markets(
    markets: tuple[StrategyCrossMarketDuplicateGuardV8Market, ...],
) -> tuple[StrategyCrossMarketDuplicateGuardV8Market, ...]:
    if type(markets) is not tuple:
        raise ValueError("markets must be a tuple")
    market_slugs: list[str] = []
    for market in markets:
        if type(market) is not StrategyCrossMarketDuplicateGuardV8Market:
            raise ValueError("markets must contain StrategyCrossMarketDuplicateGuardV8Market values")
        require_paper_only_flags("StrategyCrossMarketDuplicateGuardV8Market", market)
        market_slugs.append(market.market_slug)
    if len(set(market_slugs)) != len(market_slugs):
        raise ValueError("market_slug values must be unique")
    return markets


def _normalize_rows(
    rows: tuple[StrategyCrossMarketDuplicateGuardV8Row, ...],
) -> tuple[StrategyCrossMarketDuplicateGuardV8Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    market_slugs: list[str] = []
    for row in rows:
        if type(row) is not StrategyCrossMarketDuplicateGuardV8Row:
            raise ValueError("rows must contain StrategyCrossMarketDuplicateGuardV8Row values")
        require_paper_only_flags("StrategyCrossMarketDuplicateGuardV8Row", row)
        market_slugs.append(row.market_slug)
    if len(set(market_slugs)) != len(market_slugs):
        raise ValueError("row market_slug values must be unique")
    return rows


def _validate_row(row: StrategyCrossMarketDuplicateGuardV8Row) -> None:
    if row.duplicate_status == "unique":
        if row.canonical_market_slug != row.market_slug:
            raise ValueError("unique rows must be canonical to themselves")
        if row.group_market_count != COUNT_QUANTUM:
            raise ValueError("unique rows must have one market in group")
        if row.reason_codes != ("no_cross_market_duplicate_detected",):
            raise ValueError("unique rows must use the unique reason code")
        return
    if row.group_market_count <= COUNT_QUANTUM:
        raise ValueError("duplicate groups must contain more than one market")
    if row.duplicate_status == "canonical" and row.canonical_market_slug != row.market_slug:
        raise ValueError("canonical rows must point to themselves")
    if row.duplicate_status == "duplicate" and row.canonical_market_slug == row.market_slug:
        raise ValueError("duplicate rows must point to another canonical market")
    if row.reason_codes[0] not in ("same_event_slug", "resolution_criteria_highly_similar"):
        raise ValueError("duplicate group rows must include a group reason code")


def _validate_report(report: StrategyCrossMarketDuplicateGuardV8Report) -> None:
    if report.market_count != _count(len(report.rows)):
        raise ValueError("market_count must match rows")
    expected_canonical_count = _count(sum(row.duplicate_status == "canonical" for row in report.rows))
    expected_duplicate_count = _count(sum(row.duplicate_status == "duplicate" for row in report.rows))
    expected_unique_count = _count(sum(row.duplicate_status == "unique" for row in report.rows))
    if report.canonical_market_count != expected_canonical_count:
        raise ValueError("canonical_market_count must match rows")
    if report.duplicate_market_count != expected_duplicate_count:
        raise ValueError("duplicate_market_count must match rows")
    if report.unique_market_count != expected_unique_count:
        raise ValueError("unique_market_count must match rows")
    if report.market_count != report.canonical_market_count + report.duplicate_market_count + report.unique_market_count:
        raise ValueError("row status counts must sum to market_count")
    expected_group_count = _count(
        len({row.duplicate_group_id for row in report.rows if row.duplicate_status != "unique"}),
    )
    if report.duplicate_group_count != expected_group_count:
        raise ValueError("duplicate_group_count must match grouped rows")
    if report.duplicate_status == "duplicates_found" and report.duplicate_market_count == ZERO_COUNT:
        raise ValueError("duplicates_found reports must have duplicates")
    if report.duplicate_status == "clear" and report.duplicate_market_count > ZERO_COUNT:
        raise ValueError("clear reports must not have duplicates")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for value in values:
        _require_member(field_name, value, REASON_CODES)
        if value in normalized:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(value)
    return tuple(normalized)


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known {field_name.replace('_', ' ')}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_optional_canonical_string(field_name: str, value: str | None) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value, RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _find_parent(parents: dict[str, str], slug: str) -> str:
    parent = parents[slug]
    if parent != slug:
        parents[slug] = _find_parent(parents, parent)
    return parents[slug]


def _union(parents: dict[str, str], left: str, right: str) -> None:
    left_parent = _find_parent(parents, left)
    right_parent = _find_parent(parents, right)
    if left_parent != right_parent:
        parents[right_parent] = left_parent
