"""Pure Phase 1 market source-family divergence priority report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_PRIORITY_REPORT_CONFIG_VERSION = (
    "market-source-family-divergence-priority-report-v0"
)

SOURCE_FAMILIES = ("official", "primary", "proxy", "team_acknowledged")
SOURCE_FAMILY_RANK = {
    "official": 0,
    "primary": 1,
    "proxy": 2,
    "team_acknowledged": 3,
}
REPORT_STATUSES = ("clear", "watch", "blocked")
PRIORITY_STATUSES = ("clear", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}

DELTA_BLOCKED_REASON = "market_source_family_divergence_priority_delta_blocked"
DELTA_WATCH_REASON = "market_source_family_divergence_priority_delta_watch"
STALE_SOURCE_AGE_REASON = (
    "market_source_family_divergence_priority_stale_source_age"
)
CONCENTRATION_BLOCKED_REASON = (
    "market_source_family_divergence_priority_concentration_blocked"
)
CONCENTRATION_WATCH_REASON = (
    "market_source_family_divergence_priority_concentration_watch"
)
MISSING_FAMILY_COVERAGE_REASON = (
    "market_source_family_divergence_priority_missing_family_coverage"
)
CLEAR_REASON = "market_source_family_divergence_priority_clear"
REASON_CODES = (
    DELTA_BLOCKED_REASON,
    DELTA_WATCH_REASON,
    STALE_SOURCE_AGE_REASON,
    CONCENTRATION_BLOCKED_REASON,
    CONCENTRATION_WATCH_REASON,
    MISSING_FAMILY_COVERAGE_REASON,
    CLEAR_REASON,
)
BLOCKING_REASONS = frozenset((DELTA_BLOCKED_REASON, CONCENTRATION_BLOCKED_REASON))

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "credential",
        "private",
        "secret",
        "token",
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ),
)


@dataclass(frozen=True)
class MarketSourceFamilyDivergencePriorityConfig:
    config_version: str = (
        DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_PRIORITY_REPORT_CONFIG_VERSION
    )
    watch_probability_delta: Decimal = Decimal("0.050000")
    blocked_probability_delta: Decimal = Decimal("0.150000")
    stale_source_family_seconds: Decimal = Decimal("3600.000000")
    concentration_watch_ratio: Decimal = Decimal("0.500000")
    concentration_blocked_ratio: Decimal = Decimal("0.750000")
    expected_source_family_count: Decimal = Decimal("4.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_probability_delta",
            _require_positive_probability_delta(
                "watch_probability_delta",
                self.watch_probability_delta,
            ),
        )
        object.__setattr__(
            self,
            "blocked_probability_delta",
            _require_positive_probability_delta(
                "blocked_probability_delta",
                self.blocked_probability_delta,
            ),
        )
        object.__setattr__(
            self,
            "stale_source_family_seconds",
            _require_positive_decimal(
                "stale_source_family_seconds",
                self.stale_source_family_seconds,
            ),
        )
        object.__setattr__(
            self,
            "concentration_watch_ratio",
            _require_ratio_decimal(
                "concentration_watch_ratio",
                self.concentration_watch_ratio,
            ),
        )
        object.__setattr__(
            self,
            "concentration_blocked_ratio",
            _require_ratio_decimal(
                "concentration_blocked_ratio",
                self.concentration_blocked_ratio,
            ),
        )
        object.__setattr__(
            self,
            "expected_source_family_count",
            _require_positive_whole_decimal(
                "expected_source_family_count",
                self.expected_source_family_count,
            ),
        )
        if self.blocked_probability_delta < self.watch_probability_delta:
            raise ValueError(
                "blocked_probability_delta must be >= watch_probability_delta",
            )
        if self.concentration_blocked_ratio < self.concentration_watch_ratio:
            raise ValueError(
                "concentration_blocked_ratio must be >= concentration_watch_ratio",
            )
        if _whole_decimal_to_int(
            "expected_source_family_count",
            self.expected_source_family_count,
        ) > len(SOURCE_FAMILIES):
            raise ValueError("expected_source_family_count must fit source families")
        require_paper_only_flags(
            "market source family divergence priority config",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergencePriorityInputRow:
    market_id: str
    category_id: str
    source_family: str
    probability: Decimal
    source_updated_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_public_string("category_id", self.category_id)
        _require_source_family("source_family", self.source_family)
        object.__setattr__(
            self,
            "probability",
            _require_probability_decimal("probability", self.probability),
        )
        object.__setattr__(
            self,
            "source_updated_at",
            _as_utc("source_updated_at", self.source_updated_at),
        )
        reject_unsafe_surface_fields(
            "market source family divergence priority input row",
            self,
        )
        require_paper_only_flags(
            "market source family divergence priority input row",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergencePriorityRow:
    priority_rank: Decimal
    market_id: str
    category_id: str
    official_probability: Decimal | None
    primary_probability: Decimal | None
    proxy_probability: Decimal | None
    team_acknowledged_probability: Decimal | None
    source_family_count: Decimal
    missing_source_family_count: Decimal
    max_probability_delta: Decimal
    stale_source_family_count: Decimal
    max_source_age_seconds: Decimal
    category_pressure_count: Decimal
    category_pressure_ratio: Decimal
    priority_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "priority_rank",
            _require_positive_whole_decimal("priority_rank", self.priority_rank),
        )
        _require_public_string("market_id", self.market_id)
        _require_public_string("category_id", self.category_id)
        for field_name in (
            "official_probability",
            "primary_probability",
            "proxy_probability",
            "team_acknowledged_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_family_count",
            "missing_source_family_count",
            "max_probability_delta",
            "stale_source_family_count",
            "max_source_age_seconds",
            "category_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "category_pressure_ratio",
            _require_ratio_decimal(
                "category_pressure_ratio",
                self.category_pressure_ratio,
            ),
        )
        _require_priority_status("priority_status", self.priority_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_priority_row(self)
        reject_unsafe_surface_fields(
            "market source family divergence priority row",
            self,
        )
        require_paper_only_flags(
            "market source family divergence priority row",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergencePriorityReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    source_family_count: Decimal
    clear_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    priority_market_count: Decimal
    divergent_market_count: Decimal
    stale_market_count: Decimal
    concentrated_market_count: Decimal
    missing_family_market_count: Decimal
    priority_market_ratio: Decimal
    divergent_market_ratio: Decimal
    stale_market_ratio: Decimal
    concentrated_market_ratio: Decimal
    missing_family_market_ratio: Decimal
    max_probability_delta: Decimal
    max_source_age_seconds: Decimal
    max_category_pressure_ratio: Decimal
    rows: tuple[MarketSourceFamilyDivergencePriorityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "market_count",
            "source_family_count",
            "clear_market_count",
            "watch_market_count",
            "blocked_market_count",
            "priority_market_count",
            "divergent_market_count",
            "stale_market_count",
            "concentrated_market_count",
            "missing_family_market_count",
            "priority_market_ratio",
            "divergent_market_ratio",
            "stale_market_ratio",
            "concentrated_market_ratio",
            "missing_family_market_ratio",
            "max_probability_delta",
            "max_source_age_seconds",
            "max_category_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields(
            "market source family divergence priority report",
            self,
        )
        require_paper_only_flags(
            "market source family divergence priority report",
            self,
        )


@dataclass(frozen=True)
class _BasePriorityRow:
    market_id: str
    category_id: str
    official_probability: Decimal | None
    primary_probability: Decimal | None
    proxy_probability: Decimal | None
    team_acknowledged_probability: Decimal | None
    source_family_count: Decimal
    missing_source_family_count: Decimal
    max_probability_delta: Decimal
    stale_source_family_count: Decimal
    max_source_age_seconds: Decimal
    base_pressure_count: Decimal


def build_market_source_family_divergence_priority_report(
    input_rows: list[MarketSourceFamilyDivergencePriorityInputRow]
    | tuple[MarketSourceFamilyDivergencePriorityInputRow, ...],
    *,
    config: MarketSourceFamilyDivergencePriorityConfig,
    generated_at: datetime,
) -> MarketSourceFamilyDivergencePriorityReport:
    if type(config) is not MarketSourceFamilyDivergencePriorityConfig:
        raise ValueError(
            "config must be a MarketSourceFamilyDivergencePriorityConfig",
        )
    require_paper_only_flags(
        "market source family divergence priority config",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)

    by_market: dict[str, list[MarketSourceFamilyDivergencePriorityInputRow]] = {}
    for row in rows:
        by_market.setdefault(row.market_id, []).append(row)

    base_rows = tuple(
        _base_priority_row(
            market_id,
            tuple(market_rows),
            config=config,
            generated_at=generated_at_utc,
        )
        for market_id, market_rows in sorted(by_market.items())
    )
    category_pressure_counts = _category_pressure_counts(base_rows)
    total_pressure_count = _sum_decimal(
        row.base_pressure_count for row in base_rows
    )
    unranked_rows = tuple(
        _priority_row(
            base_row,
            priority_rank=ONE,
            category_pressure_count=category_pressure_counts.get(
                base_row.category_id,
                ZERO,
            ),
            total_pressure_count=total_pressure_count,
            config=config,
        )
        for base_row in base_rows
    )
    report_rows = _assign_priority_ranks(_sort_rows(unranked_rows))
    reason_codes = _report_reason_codes(report_rows)
    market_count = _decimal_count(len(report_rows))
    priority_market_count = _priority_count(report_rows)
    divergent_market_count = _reason_metric_count(
        report_rows,
        (DELTA_BLOCKED_REASON, DELTA_WATCH_REASON),
    )
    stale_market_count = _reason_metric_count(report_rows, (STALE_SOURCE_AGE_REASON,))
    concentrated_market_count = _reason_metric_count(
        report_rows,
        (CONCENTRATION_BLOCKED_REASON, CONCENTRATION_WATCH_REASON),
    )
    missing_family_market_count = _reason_metric_count(
        report_rows,
        (MISSING_FAMILY_COVERAGE_REASON,),
    )

    return MarketSourceFamilyDivergencePriorityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        market_count=market_count,
        source_family_count=_sum_decimal(
            row.source_family_count for row in report_rows
        ),
        clear_market_count=_status_count(report_rows, "clear"),
        watch_market_count=_status_count(report_rows, "watch"),
        blocked_market_count=_status_count(report_rows, "blocked"),
        priority_market_count=priority_market_count,
        divergent_market_count=divergent_market_count,
        stale_market_count=stale_market_count,
        concentrated_market_count=concentrated_market_count,
        missing_family_market_count=missing_family_market_count,
        priority_market_ratio=_ratio(priority_market_count, market_count),
        divergent_market_ratio=_ratio(divergent_market_count, market_count),
        stale_market_ratio=_ratio(stale_market_count, market_count),
        concentrated_market_ratio=_ratio(concentrated_market_count, market_count),
        missing_family_market_ratio=_ratio(
            missing_family_market_count,
            market_count,
        ),
        max_probability_delta=_max_decimal(
            row.max_probability_delta for row in report_rows
        ),
        max_source_age_seconds=_max_decimal(
            row.max_source_age_seconds for row in report_rows
        ),
        max_category_pressure_ratio=_max_decimal(
            row.category_pressure_ratio for row in report_rows
        ),
        rows=report_rows,
    )


def market_source_family_divergence_priority_report_to_payload(
    report: MarketSourceFamilyDivergencePriorityReport,
) -> dict[str, Any]:
    if type(report) is not MarketSourceFamilyDivergencePriorityReport:
        raise ValueError(
            "report must be a MarketSourceFamilyDivergencePriorityReport",
        )
    require_paper_only_flags(
        "market source family divergence priority report",
        report,
    )
    ready = json_ready_no_floats(report)
    if type(ready) is not dict:
        raise ValueError("report value must be a JSON object")
    reject_unsafe_surface_fields(
        "market source family divergence priority report value",
        ready,
    )
    return ready


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketSourceFamilyDivergencePriorityInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    market_categories: dict[str, str] = {}
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergencePriorityInputRow:
            raise ValueError("input rows must contain divergence priority input rows")
        require_paper_only_flags(
            "market source family divergence priority input row",
            row,
        )
        if row.source_updated_at > generated_at:
            raise ValueError("source_updated_at must not be after generated_at")
        existing_category_id = market_categories.setdefault(
            row.market_id,
            row.category_id,
        )
        if existing_category_id != row.category_id:
            raise ValueError("category_id must be stable per market_id")
        key = (row.market_id, row.source_family)
        if key in seen:
            raise ValueError("source_family values must be unique per market_id")
        seen.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.market_id,
                row.category_id,
                SOURCE_FAMILY_RANK[row.source_family],
                row.probability,
                row.source_updated_at,
            ),
        ),
    )


def _base_priority_row(
    market_id: str,
    rows: tuple[MarketSourceFamilyDivergencePriorityInputRow, ...],
    *,
    config: MarketSourceFamilyDivergencePriorityConfig,
    generated_at: datetime,
) -> _BasePriorityRow:
    by_family = {row.source_family: row for row in rows}
    probabilities = tuple(row.probability for row in rows)
    source_family_count = _decimal_count(len(rows))
    expected_source_family_count = config.expected_source_family_count
    missing_source_family_count = max(
        ZERO,
        expected_source_family_count - source_family_count,
    ).quantize(QUANT)
    max_probability_delta = _probability_delta(probabilities)
    stale_source_family_count = _decimal_count(
        sum(
            1
            for row in rows
            if _age_seconds(generated_at, row.source_updated_at)
            > config.stale_source_family_seconds
        ),
    )
    max_source_age_seconds = _max_decimal(
        _age_seconds(generated_at, row.source_updated_at) for row in rows
    )
    base_pressure_count = (
        ONE
        if (
            max_probability_delta >= config.watch_probability_delta
            or stale_source_family_count > ZERO
            or missing_source_family_count > ZERO
        )
        else ZERO
    )
    return _BasePriorityRow(
        market_id=market_id,
        category_id=rows[0].category_id,
        official_probability=_probability_for_family(by_family, "official"),
        primary_probability=_probability_for_family(by_family, "primary"),
        proxy_probability=_probability_for_family(by_family, "proxy"),
        team_acknowledged_probability=_probability_for_family(
            by_family,
            "team_acknowledged",
        ),
        source_family_count=source_family_count,
        missing_source_family_count=missing_source_family_count,
        max_probability_delta=max_probability_delta,
        stale_source_family_count=stale_source_family_count,
        max_source_age_seconds=max_source_age_seconds,
        base_pressure_count=base_pressure_count,
    )


def _priority_row(
    base_row: _BasePriorityRow,
    *,
    priority_rank: Decimal,
    category_pressure_count: Decimal,
    total_pressure_count: Decimal,
    config: MarketSourceFamilyDivergencePriorityConfig,
) -> MarketSourceFamilyDivergencePriorityRow:
    category_pressure_ratio = (
        ZERO
        if base_row.base_pressure_count == ZERO
        else _ratio(category_pressure_count, total_pressure_count)
    )
    reason_codes = _row_reason_codes(
        max_probability_delta=base_row.max_probability_delta,
        stale_source_family_count=base_row.stale_source_family_count,
        category_pressure_ratio=category_pressure_ratio,
        missing_source_family_count=base_row.missing_source_family_count,
        config=config,
    )
    return MarketSourceFamilyDivergencePriorityRow(
        priority_rank=priority_rank,
        market_id=base_row.market_id,
        category_id=base_row.category_id,
        official_probability=base_row.official_probability,
        primary_probability=base_row.primary_probability,
        proxy_probability=base_row.proxy_probability,
        team_acknowledged_probability=base_row.team_acknowledged_probability,
        source_family_count=base_row.source_family_count,
        missing_source_family_count=base_row.missing_source_family_count,
        max_probability_delta=base_row.max_probability_delta,
        stale_source_family_count=base_row.stale_source_family_count,
        max_source_age_seconds=base_row.max_source_age_seconds,
        category_pressure_count=(
            ZERO if base_row.base_pressure_count == ZERO else category_pressure_count
        ),
        category_pressure_ratio=category_pressure_ratio,
        priority_status=_row_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _assign_priority_ranks(
    rows: tuple[MarketSourceFamilyDivergencePriorityRow, ...],
) -> tuple[MarketSourceFamilyDivergencePriorityRow, ...]:
    return tuple(
        MarketSourceFamilyDivergencePriorityRow(
            priority_rank=_decimal_count(index),
            market_id=row.market_id,
            category_id=row.category_id,
            official_probability=row.official_probability,
            primary_probability=row.primary_probability,
            proxy_probability=row.proxy_probability,
            team_acknowledged_probability=row.team_acknowledged_probability,
            source_family_count=row.source_family_count,
            missing_source_family_count=row.missing_source_family_count,
            max_probability_delta=row.max_probability_delta,
            stale_source_family_count=row.stale_source_family_count,
            max_source_age_seconds=row.max_source_age_seconds,
            category_pressure_count=row.category_pressure_count,
            category_pressure_ratio=row.category_pressure_ratio,
            priority_status=row.priority_status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(rows, start=1)
    )


def _probability_for_family(
    rows_by_family: dict[str, MarketSourceFamilyDivergencePriorityInputRow],
    source_family: str,
) -> Decimal | None:
    row = rows_by_family.get(source_family)
    return None if row is None else row.probability


def _probability_delta(probabilities: tuple[Decimal, ...]) -> Decimal:
    if len(probabilities) < 2:
        return ZERO
    return (max(probabilities) - min(probabilities)).quantize(QUANT)


def _category_pressure_counts(base_rows: tuple[_BasePriorityRow, ...]) -> dict[str, Decimal]:
    counts: dict[str, Decimal] = {}
    for row in base_rows:
        if row.base_pressure_count > ZERO:
            counts[row.category_id] = (
                counts.get(row.category_id, ZERO) + ONE
            ).quantize(QUANT)
    return counts


def _row_reason_codes(
    *,
    max_probability_delta: Decimal,
    stale_source_family_count: Decimal,
    category_pressure_ratio: Decimal,
    missing_source_family_count: Decimal,
    config: MarketSourceFamilyDivergencePriorityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if max_probability_delta >= config.blocked_probability_delta:
        reason_codes.append(DELTA_BLOCKED_REASON)
    elif max_probability_delta >= config.watch_probability_delta:
        reason_codes.append(DELTA_WATCH_REASON)
    if stale_source_family_count > ZERO:
        reason_codes.append(STALE_SOURCE_AGE_REASON)
    if category_pressure_ratio >= config.concentration_blocked_ratio:
        reason_codes.append(CONCENTRATION_BLOCKED_REASON)
    elif category_pressure_ratio >= config.concentration_watch_ratio:
        reason_codes.append(CONCENTRATION_WATCH_REASON)
    if missing_source_family_count > ZERO:
        reason_codes.append(MISSING_FAMILY_COVERAGE_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[MarketSourceFamilyDivergencePriorityRow, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for reason_code in REASON_CODES:
        if reason_code == CLEAR_REASON:
            continue
        if any(reason_code in row.reason_codes for row in rows):
            reason_codes.append(reason_code)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return tuple(reason_codes)


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in reason_codes for reason in BLOCKING_REASONS):
        return "blocked"
    if reason_codes != (CLEAR_REASON,):
        return "watch"
    return "clear"


def _report_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in reason_codes for reason in BLOCKING_REASONS):
        return "blocked"
    if reason_codes != (CLEAR_REASON,):
        return "watch"
    return "clear"


def _normalize_rows(
    value: object,
) -> tuple[MarketSourceFamilyDivergencePriorityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergencePriorityRow:
            raise ValueError("rows must contain divergence priority rows")
        require_paper_only_flags(
            "market source family divergence priority row",
            row,
        )
        if row.market_id in seen:
            raise ValueError("rows must be unique per market_id")
        seen.add(row.market_id)
    if rows != _sort_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.priority_rank for row in rows) != expected_ranks:
        raise ValueError("priority_rank values must be sequential")
    return rows


def _sort_rows(
    rows: tuple[MarketSourceFamilyDivergencePriorityRow, ...],
) -> tuple[MarketSourceFamilyDivergencePriorityRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.priority_status],
                -row.max_probability_delta,
                -row.max_source_age_seconds,
                -row.category_pressure_ratio,
                -row.missing_source_family_count,
                row.category_id,
                row.market_id,
            ),
        ),
    )


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    if CLEAR_REASON in reason_codes and reason_codes != (CLEAR_REASON,):
        raise ValueError("clear reason must stand alone")
    return reason_codes


def _validate_priority_row(row: MarketSourceFamilyDivergencePriorityRow) -> None:
    if (
        DELTA_BLOCKED_REASON in row.reason_codes
        and DELTA_WATCH_REASON in row.reason_codes
    ):
        raise ValueError("delta reason codes must be exclusive")
    if (
        CONCENTRATION_BLOCKED_REASON in row.reason_codes
        and CONCENTRATION_WATCH_REASON in row.reason_codes
    ):
        raise ValueError("concentration reason codes must be exclusive")
    populated_probabilities = tuple(
        value
        for value in (
            row.official_probability,
            row.primary_probability,
            row.proxy_probability,
            row.team_acknowledged_probability,
        )
        if value is not None
    )
    if row.source_family_count != _decimal_count(len(populated_probabilities)):
        raise ValueError("source_family_count must match populated source families")
    if row.source_family_count + row.missing_source_family_count > _decimal_count(
        len(SOURCE_FAMILIES),
    ):
        raise ValueError("missing_source_family_count must fit source families")
    if row.max_probability_delta != _probability_delta(populated_probabilities):
        raise ValueError("max_probability_delta must match probabilities")
    if row.stale_source_family_count > row.source_family_count:
        raise ValueError("stale_source_family_count must not exceed source_family_count")
    if row.category_pressure_count == ZERO and row.category_pressure_ratio != ZERO:
        raise ValueError("category_pressure_ratio requires category pressure")
    if row.category_pressure_ratio == ZERO and any(
        reason in row.reason_codes
        for reason in (CONCENTRATION_BLOCKED_REASON, CONCENTRATION_WATCH_REASON)
    ):
        raise ValueError("concentration reason requires category pressure")
    if row.stale_source_family_count == ZERO and STALE_SOURCE_AGE_REASON in row.reason_codes:
        raise ValueError("stale reason requires stale source families")
    if row.stale_source_family_count > ZERO and STALE_SOURCE_AGE_REASON not in row.reason_codes:
        raise ValueError("stale source families require stale reason")
    if (
        row.missing_source_family_count == ZERO
        and MISSING_FAMILY_COVERAGE_REASON in row.reason_codes
    ):
        raise ValueError("missing family reason requires missing coverage")
    if (
        row.missing_source_family_count > ZERO
        and MISSING_FAMILY_COVERAGE_REASON not in row.reason_codes
    ):
        raise ValueError("missing coverage requires missing family reason")
    if row.priority_status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("priority_status must match reason_codes")


def _validate_report(report: MarketSourceFamilyDivergencePriorityReport) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.source_family_count != _sum_decimal(
        row.source_family_count for row in report.rows
    ):
        raise ValueError("source_family_count must match rows")
    if report.clear_market_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_market_count must match rows")
    if report.watch_market_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_market_count must match rows")
    if report.blocked_market_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_market_count must match rows")
    if (
        report.clear_market_count
        + report.watch_market_count
        + report.blocked_market_count
        != report.market_count
    ):
        raise ValueError("market status counts must sum to market_count")
    expected_counts = {
        "priority_market_count": _priority_count(report.rows),
        "divergent_market_count": _reason_metric_count(
            report.rows,
            (DELTA_BLOCKED_REASON, DELTA_WATCH_REASON),
        ),
        "stale_market_count": _reason_metric_count(
            report.rows,
            (STALE_SOURCE_AGE_REASON,),
        ),
        "concentrated_market_count": _reason_metric_count(
            report.rows,
            (CONCENTRATION_BLOCKED_REASON, CONCENTRATION_WATCH_REASON),
        ),
        "missing_family_market_count": _reason_metric_count(
            report.rows,
            (MISSING_FAMILY_COVERAGE_REASON,),
        ),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_ratios = {
        "priority_market_ratio": _ratio(
            report.priority_market_count,
            report.market_count,
        ),
        "divergent_market_ratio": _ratio(
            report.divergent_market_count,
            report.market_count,
        ),
        "stale_market_ratio": _ratio(report.stale_market_count, report.market_count),
        "concentrated_market_ratio": _ratio(
            report.concentrated_market_count,
            report.market_count,
        ),
        "missing_family_market_ratio": _ratio(
            report.missing_family_market_count,
            report.market_count,
        ),
    }
    for field_name, expected in expected_ratios.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.max_probability_delta != _max_decimal(
        row.max_probability_delta for row in report.rows
    ):
        raise ValueError("max_probability_delta must match rows")
    if report.max_source_age_seconds != _max_decimal(
        row.max_source_age_seconds for row in report.rows
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.max_category_pressure_ratio != _max_decimal(
        row.category_pressure_ratio for row in report.rows
    ):
        raise ValueError("max_category_pressure_ratio must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status_from_reason_codes(report.reason_codes):
        raise ValueError("report_status must match reason_codes")


def _status_count(
    rows: tuple[MarketSourceFamilyDivergencePriorityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.priority_status == status))


def _priority_count(rows: tuple[MarketSourceFamilyDivergencePriorityRow, ...]) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.priority_status != "clear"))


def _reason_metric_count(
    rows: tuple[MarketSourceFamilyDivergencePriorityRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)),
    )


def _max_decimal(values: object) -> Decimal:
    normalized = tuple(values)  # type: ignore[arg-type]
    if not normalized:
        return ZERO
    return max(normalized)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        total += value
    return total.quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    age_seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if age_seconds < ZERO:
        raise ValueError("age_seconds must be nonnegative")
    return age_seconds.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANT)


def _whole_decimal_to_int(field_name: str, value: Decimal) -> int:
    decimal_value = _require_positive_whole_decimal(field_name, value)
    return int(decimal_value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value % ONE != ZERO:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_probability_delta(field_name: str, value: object) -> Decimal:
    decimal_value = _require_probability_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    decimal_value = value.quantize(QUANT)
    if decimal_value == ZERO:
        return ZERO
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or blocked")


def _require_priority_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PRIORITY_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or blocked")


def _require_source_family(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_FAMILIES:
        raise ValueError(
            f"{field_name} must be official, primary, proxy, or team_acknowledged",
        )


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_optional_probability(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


__all__ = (
    "DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_PRIORITY_REPORT_CONFIG_VERSION",
    "MarketSourceFamilyDivergencePriorityConfig",
    "MarketSourceFamilyDivergencePriorityInputRow",
    "MarketSourceFamilyDivergencePriorityReport",
    "MarketSourceFamilyDivergencePriorityRow",
    "build_market_source_family_divergence_priority_report",
    "market_source_family_divergence_priority_report_to_payload",
)
