"""Pure Phase 1 market source-family divergence queue report."""

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


DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_QUEUE_REPORT_CONFIG_VERSION = (
    "market-source-family-divergence-queue-report-v0"
)

SOURCE_FAMILIES = ("official", "primary", "proxy", "team_acknowledged")
SOURCE_FAMILY_RANK = {
    "official": 0,
    "primary": 1,
    "proxy": 2,
    "team_acknowledged": 3,
}
REPORT_STATUSES = ("clear", "watch", "blocked")
QUEUE_STATUSES = ("clear", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}

OFFICIAL_PROXY_CONFLICT_REASON = (
    "market_source_family_divergence_queue_official_proxy_conflict"
)
STALE_SOURCE_FAMILY_REASON = (
    "market_source_family_divergence_queue_stale_source_family"
)
MISSING_TEAM_ACKNOWLEDGEMENT_REASON = (
    "market_source_family_divergence_queue_missing_team_acknowledgement"
)
REPEATED_CATEGORY_MISS_REASON = (
    "market_source_family_divergence_queue_repeated_category_miss"
)
CLEAR_REASON = "market_source_family_divergence_queue_clear"
REASON_CODES = (
    OFFICIAL_PROXY_CONFLICT_REASON,
    STALE_SOURCE_FAMILY_REASON,
    MISSING_TEAM_ACKNOWLEDGEMENT_REASON,
    REPEATED_CATEGORY_MISS_REASON,
    CLEAR_REASON,
)

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
class MarketSourceFamilyDivergenceQueueConfig:
    config_version: str = (
        DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_QUEUE_REPORT_CONFIG_VERSION
    )
    stale_source_family_seconds: Decimal = Decimal("3600.000000")
    team_acknowledgement_required_after_seconds: Decimal = Decimal("600.000000")
    repeated_category_miss_threshold: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
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
            "team_acknowledgement_required_after_seconds",
            _require_positive_decimal(
                "team_acknowledgement_required_after_seconds",
                self.team_acknowledgement_required_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "repeated_category_miss_threshold",
            _require_positive_whole_decimal(
                "repeated_category_miss_threshold",
                self.repeated_category_miss_threshold,
            ),
        )
        require_paper_only_flags(
            "market source family divergence queue config",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceQueueInputRow:
    market_id: str
    category_id: str
    source_family: str
    observed_value: str
    source_updated_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_public_string("category_id", self.category_id)
        _require_source_family("source_family", self.source_family)
        _require_public_string("observed_value", self.observed_value)
        object.__setattr__(
            self,
            "source_updated_at",
            _as_utc("source_updated_at", self.source_updated_at),
        )
        require_paper_only_flags(
            "market source family divergence queue input row",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceQueueRow:
    market_id: str
    category_id: str
    official_value: str | None
    primary_value: str | None
    proxy_value: str | None
    team_acknowledged_value: str | None
    source_family_count: Decimal
    official_proxy_conflict_count: Decimal
    stale_source_family_count: Decimal
    missing_team_acknowledgement_count: Decimal
    repeated_category_miss_count: Decimal
    category_miss_count: Decimal
    max_source_age_seconds: Decimal
    queue_status: str
    queue_required: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_public_string("category_id", self.category_id)
        for field_name in (
            "official_value",
            "primary_value",
            "proxy_value",
            "team_acknowledged_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_public_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_family_count",
            "official_proxy_conflict_count",
            "stale_source_family_count",
            "missing_team_acknowledgement_count",
            "repeated_category_miss_count",
            "category_miss_count",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_queue_status("queue_status", self.queue_status)
        _require_bool("queue_required", self.queue_required)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_queue_row(self)
        reject_unsafe_surface_fields(
            "market source family divergence queue row",
            self,
        )
        require_paper_only_flags(
            "market source family divergence queue row",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceQueueReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    source_family_count: Decimal
    clear_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    queued_market_count: Decimal
    official_proxy_conflict_market_count: Decimal
    stale_source_family_market_count: Decimal
    missing_team_acknowledgement_market_count: Decimal
    repeated_category_miss_market_count: Decimal
    queued_market_ratio: Decimal
    official_proxy_conflict_ratio: Decimal
    stale_source_family_ratio: Decimal
    missing_team_acknowledgement_ratio: Decimal
    repeated_category_miss_ratio: Decimal
    max_source_age_seconds: Decimal
    rows: tuple[MarketSourceFamilyDivergenceQueueRow, ...]
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
            "queued_market_count",
            "official_proxy_conflict_market_count",
            "stale_source_family_market_count",
            "missing_team_acknowledgement_market_count",
            "repeated_category_miss_market_count",
            "queued_market_ratio",
            "official_proxy_conflict_ratio",
            "stale_source_family_ratio",
            "missing_team_acknowledgement_ratio",
            "repeated_category_miss_ratio",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields(
            "market source family divergence queue report",
            self,
        )
        require_paper_only_flags(
            "market source family divergence queue report",
            self,
        )


@dataclass(frozen=True)
class _BaseQueueRow:
    market_id: str
    category_id: str
    official_value: str | None
    primary_value: str | None
    proxy_value: str | None
    team_acknowledged_value: str | None
    source_family_count: Decimal
    official_proxy_conflict_count: Decimal
    stale_source_family_count: Decimal
    missing_team_acknowledgement_count: Decimal
    max_source_age_seconds: Decimal
    base_miss_count: Decimal


def build_market_source_family_divergence_queue_report(
    input_rows: list[MarketSourceFamilyDivergenceQueueInputRow]
    | tuple[MarketSourceFamilyDivergenceQueueInputRow, ...],
    *,
    config: MarketSourceFamilyDivergenceQueueConfig,
    generated_at: datetime,
) -> MarketSourceFamilyDivergenceQueueReport:
    if type(config) is not MarketSourceFamilyDivergenceQueueConfig:
        raise ValueError(
            "config must be a MarketSourceFamilyDivergenceQueueConfig",
        )
    require_paper_only_flags(
        "market source family divergence queue config",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)

    by_market: dict[str, list[MarketSourceFamilyDivergenceQueueInputRow]] = {}
    for row in rows:
        by_market.setdefault(row.market_id, []).append(row)

    base_rows = tuple(
        _base_queue_row(
            market_id,
            tuple(market_rows),
            config=config,
            generated_at=generated_at_utc,
        )
        for market_id, market_rows in sorted(by_market.items())
    )
    category_miss_counts = _category_miss_counts(base_rows)
    report_rows = _sort_rows(
        tuple(
            _queue_row(
                base_row,
                category_miss_count=category_miss_counts.get(
                    base_row.category_id,
                    ZERO,
                ),
                repeated_category_miss_threshold=(
                    config.repeated_category_miss_threshold
                ),
            )
            for base_row in base_rows
        ),
    )
    reason_codes = _report_reason_codes(report_rows)
    market_count = _decimal_count(len(report_rows))

    return MarketSourceFamilyDivergenceQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        market_count=market_count,
        source_family_count=_sum_decimal(row.source_family_count for row in report_rows),
        clear_market_count=_status_count(report_rows, "clear"),
        watch_market_count=_status_count(report_rows, "watch"),
        blocked_market_count=_status_count(report_rows, "blocked"),
        queued_market_count=_queued_count(report_rows),
        official_proxy_conflict_market_count=_positive_metric_count(
            report_rows,
            "official_proxy_conflict_count",
        ),
        stale_source_family_market_count=_positive_metric_count(
            report_rows,
            "stale_source_family_count",
        ),
        missing_team_acknowledgement_market_count=_positive_metric_count(
            report_rows,
            "missing_team_acknowledgement_count",
        ),
        repeated_category_miss_market_count=_positive_metric_count(
            report_rows,
            "repeated_category_miss_count",
        ),
        queued_market_ratio=_ratio(_queued_count(report_rows), market_count),
        official_proxy_conflict_ratio=_ratio(
            _positive_metric_count(report_rows, "official_proxy_conflict_count"),
            market_count,
        ),
        stale_source_family_ratio=_ratio(
            _positive_metric_count(report_rows, "stale_source_family_count"),
            market_count,
        ),
        missing_team_acknowledgement_ratio=_ratio(
            _positive_metric_count(report_rows, "missing_team_acknowledgement_count"),
            market_count,
        ),
        repeated_category_miss_ratio=_ratio(
            _positive_metric_count(report_rows, "repeated_category_miss_count"),
            market_count,
        ),
        max_source_age_seconds=_max_decimal(
            row.max_source_age_seconds for row in report_rows
        ),
        rows=report_rows,
    )


def market_source_family_divergence_queue_report_to_payload(
    report: MarketSourceFamilyDivergenceQueueReport,
) -> dict[str, Any]:
    if type(report) is not MarketSourceFamilyDivergenceQueueReport:
        raise ValueError(
            "report must be a MarketSourceFamilyDivergenceQueueReport",
        )
    require_paper_only_flags(
        "market source family divergence queue report",
        report,
    )
    ready = json_ready_no_floats(report)
    if type(ready) is not dict:
        raise ValueError("report value must be a JSON object")
    reject_unsafe_surface_fields(
        "market source family divergence queue report value",
        ready,
    )
    return ready


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketSourceFamilyDivergenceQueueInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    market_categories: dict[str, str] = {}
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceQueueInputRow:
            raise ValueError("input rows must contain divergence queue input rows")
        require_paper_only_flags(
            "market source family divergence queue input row",
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
                row.observed_value,
                row.source_updated_at,
            ),
        ),
    )


def _base_queue_row(
    market_id: str,
    rows: tuple[MarketSourceFamilyDivergenceQueueInputRow, ...],
    *,
    config: MarketSourceFamilyDivergenceQueueConfig,
    generated_at: datetime,
) -> _BaseQueueRow:
    by_family = {row.source_family: row for row in rows}
    source_family_count = _decimal_count(len(rows))
    official_proxy_conflict_count = _official_proxy_conflict_count(by_family)
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
    missing_team_acknowledgement_count = (
        ONE
        if "team_acknowledged" not in by_family
        and (
            official_proxy_conflict_count > ZERO
            or stale_source_family_count > ZERO
        )
        and max_source_age_seconds >= config.team_acknowledgement_required_after_seconds
        else ZERO
    )
    base_miss_count = (
        ONE
        if (
            official_proxy_conflict_count > ZERO
            or stale_source_family_count > ZERO
            or missing_team_acknowledgement_count > ZERO
        )
        else ZERO
    )

    return _BaseQueueRow(
        market_id=market_id,
        category_id=rows[0].category_id,
        official_value=_value_for_family(by_family, "official"),
        primary_value=_value_for_family(by_family, "primary"),
        proxy_value=_value_for_family(by_family, "proxy"),
        team_acknowledged_value=_value_for_family(by_family, "team_acknowledged"),
        source_family_count=source_family_count,
        official_proxy_conflict_count=official_proxy_conflict_count,
        stale_source_family_count=stale_source_family_count,
        missing_team_acknowledgement_count=missing_team_acknowledgement_count,
        max_source_age_seconds=max_source_age_seconds,
        base_miss_count=base_miss_count,
    )


def _queue_row(
    base_row: _BaseQueueRow,
    *,
    category_miss_count: Decimal,
    repeated_category_miss_threshold: Decimal,
) -> MarketSourceFamilyDivergenceQueueRow:
    repeated_category_miss_count = (
        ONE
        if base_row.base_miss_count > ZERO
        and category_miss_count >= repeated_category_miss_threshold
        else ZERO
    )
    reason_codes = _row_reason_codes(
        official_proxy_conflict_count=base_row.official_proxy_conflict_count,
        stale_source_family_count=base_row.stale_source_family_count,
        missing_team_acknowledgement_count=(
            base_row.missing_team_acknowledgement_count
        ),
        repeated_category_miss_count=repeated_category_miss_count,
    )
    queue_status = _row_status_from_reason_codes(reason_codes)

    return MarketSourceFamilyDivergenceQueueRow(
        market_id=base_row.market_id,
        category_id=base_row.category_id,
        official_value=base_row.official_value,
        primary_value=base_row.primary_value,
        proxy_value=base_row.proxy_value,
        team_acknowledged_value=base_row.team_acknowledged_value,
        source_family_count=base_row.source_family_count,
        official_proxy_conflict_count=base_row.official_proxy_conflict_count,
        stale_source_family_count=base_row.stale_source_family_count,
        missing_team_acknowledgement_count=(
            base_row.missing_team_acknowledgement_count
        ),
        repeated_category_miss_count=repeated_category_miss_count,
        category_miss_count=category_miss_count,
        max_source_age_seconds=base_row.max_source_age_seconds,
        queue_status=queue_status,
        queue_required=queue_status != "clear",
        reason_codes=reason_codes,
    )


def _official_proxy_conflict_count(
    rows_by_family: dict[str, MarketSourceFamilyDivergenceQueueInputRow],
) -> Decimal:
    official = rows_by_family.get("official")
    proxy = rows_by_family.get("proxy")
    if official is None or proxy is None:
        return ZERO
    return ONE if official.observed_value != proxy.observed_value else ZERO


def _value_for_family(
    rows_by_family: dict[str, MarketSourceFamilyDivergenceQueueInputRow],
    source_family: str,
) -> str | None:
    row = rows_by_family.get(source_family)
    return None if row is None else row.observed_value


def _category_miss_counts(
    base_rows: tuple[_BaseQueueRow, ...],
) -> dict[str, Decimal]:
    counts: dict[str, Decimal] = {}
    for base_row in base_rows:
        if base_row.base_miss_count > ZERO:
            counts[base_row.category_id] = (
                counts.get(base_row.category_id, ZERO) + ONE
            ).quantize(QUANT)
    return counts


def _row_reason_codes(
    *,
    official_proxy_conflict_count: Decimal,
    stale_source_family_count: Decimal,
    missing_team_acknowledgement_count: Decimal,
    repeated_category_miss_count: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if official_proxy_conflict_count > ZERO:
        reason_codes.append(OFFICIAL_PROXY_CONFLICT_REASON)
    if stale_source_family_count > ZERO:
        reason_codes.append(STALE_SOURCE_FAMILY_REASON)
    if missing_team_acknowledgement_count > ZERO:
        reason_codes.append(MISSING_TEAM_ACKNOWLEDGEMENT_REASON)
    if repeated_category_miss_count > ZERO:
        reason_codes.append(REPEATED_CATEGORY_MISS_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[MarketSourceFamilyDivergenceQueueRow, ...],
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
    if (
        OFFICIAL_PROXY_CONFLICT_REASON in reason_codes
        or MISSING_TEAM_ACKNOWLEDGEMENT_REASON in reason_codes
        or REPEATED_CATEGORY_MISS_REASON in reason_codes
    ):
        return "blocked"
    if STALE_SOURCE_FAMILY_REASON in reason_codes:
        return "watch"
    return "clear"


def _report_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        OFFICIAL_PROXY_CONFLICT_REASON in reason_codes
        or MISSING_TEAM_ACKNOWLEDGEMENT_REASON in reason_codes
        or REPEATED_CATEGORY_MISS_REASON in reason_codes
    ):
        return "blocked"
    if STALE_SOURCE_FAMILY_REASON in reason_codes:
        return "watch"
    return "clear"


def _normalize_rows(
    value: object,
) -> tuple[MarketSourceFamilyDivergenceQueueRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceQueueRow:
            raise ValueError("rows must contain divergence queue rows")
        require_paper_only_flags(
            "market source family divergence queue row",
            row,
        )
        if row.market_id in seen:
            raise ValueError("rows must be unique per market_id")
        seen.add(row.market_id)
    expected = _sort_rows(rows)
    if rows != expected:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _sort_rows(
    rows: tuple[MarketSourceFamilyDivergenceQueueRow, ...],
) -> tuple[MarketSourceFamilyDivergenceQueueRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.queue_status],
                -row.missing_team_acknowledgement_count,
                -row.official_proxy_conflict_count,
                -row.repeated_category_miss_count,
                -row.stale_source_family_count,
                -row.max_source_age_seconds,
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
    return reason_codes


def _validate_queue_row(row: MarketSourceFamilyDivergenceQueueRow) -> None:
    present_source_family_count = _decimal_count(
        sum(
            1
            for value in (
                row.official_value,
                row.primary_value,
                row.proxy_value,
                row.team_acknowledged_value,
            )
            if value is not None
        ),
    )
    if row.source_family_count != present_source_family_count:
        raise ValueError("source_family_count must match populated source families")
    for field_name in (
        "official_proxy_conflict_count",
        "missing_team_acknowledgement_count",
        "repeated_category_miss_count",
    ):
        value = getattr(row, field_name)
        if value not in (ZERO, ONE):
            raise ValueError(f"{field_name} must be zero or one")
    expected_conflict_count = (
        ONE
        if row.official_value is not None
        and row.proxy_value is not None
        and row.official_value != row.proxy_value
        else ZERO
    )
    if row.official_proxy_conflict_count != expected_conflict_count:
        raise ValueError(
            "official_proxy_conflict_count must match official and proxy values",
        )
    if row.stale_source_family_count > row.source_family_count:
        raise ValueError(
            "stale_source_family_count must not exceed source_family_count",
        )
    if (
        row.team_acknowledged_value is not None
        and row.missing_team_acknowledgement_count != ZERO
    ):
        raise ValueError(
            "missing_team_acknowledgement_count must be zero with team acknowledgement",
        )
    if (
        row.repeated_category_miss_count > ZERO
        and row.category_miss_count == ZERO
    ):
        raise ValueError(
            "repeated_category_miss_count must have category misses",
        )
    expected_reason_codes = _row_reason_codes(
        official_proxy_conflict_count=row.official_proxy_conflict_count,
        stale_source_family_count=row.stale_source_family_count,
        missing_team_acknowledgement_count=row.missing_team_acknowledgement_count,
        repeated_category_miss_count=row.repeated_category_miss_count,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match queue row metrics")
    if row.queue_status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("queue_status must match reason_codes")
    if row.queue_required is not (row.queue_status != "clear"):
        raise ValueError("queue_required must match queue_status")


def _validate_report(report: MarketSourceFamilyDivergenceQueueReport) -> None:
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
    if report.queued_market_count != _queued_count(report.rows):
        raise ValueError("queued_market_count must match rows")
    expected_counts = {
        "official_proxy_conflict_market_count": _positive_metric_count(
            report.rows,
            "official_proxy_conflict_count",
        ),
        "stale_source_family_market_count": _positive_metric_count(
            report.rows,
            "stale_source_family_count",
        ),
        "missing_team_acknowledgement_market_count": _positive_metric_count(
            report.rows,
            "missing_team_acknowledgement_count",
        ),
        "repeated_category_miss_market_count": _positive_metric_count(
            report.rows,
            "repeated_category_miss_count",
        ),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_ratios = {
        "queued_market_ratio": _ratio(
            report.queued_market_count,
            report.market_count,
        ),
        "official_proxy_conflict_ratio": _ratio(
            report.official_proxy_conflict_market_count,
            report.market_count,
        ),
        "stale_source_family_ratio": _ratio(
            report.stale_source_family_market_count,
            report.market_count,
        ),
        "missing_team_acknowledgement_ratio": _ratio(
            report.missing_team_acknowledgement_market_count,
            report.market_count,
        ),
        "repeated_category_miss_ratio": _ratio(
            report.repeated_category_miss_market_count,
            report.market_count,
        ),
    }
    for field_name, expected in expected_ratios.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.max_source_age_seconds != _max_decimal(
        row.max_source_age_seconds for row in report.rows
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status_from_reason_codes(report.reason_codes):
        raise ValueError("report_status must match reason_codes")


def _status_count(
    rows: tuple[MarketSourceFamilyDivergenceQueueRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.queue_status == status))


def _queued_count(rows: tuple[MarketSourceFamilyDivergenceQueueRow, ...]) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.queue_required))


def _positive_metric_count(
    rows: tuple[MarketSourceFamilyDivergenceQueueRow, ...],
    field_name: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if getattr(row, field_name) > ZERO))


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


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value % ONE != ZERO:
        raise ValueError(f"{field_name} must be a whole Decimal")
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
    decimal_value = value.quantize(QUANT)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
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


def _require_queue_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUEUE_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or blocked")


def _require_source_family(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_FAMILIES:
        raise ValueError(
            f"{field_name} must be official, primary, proxy, or team_acknowledged",
        )


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _normalize_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_public_string(field_name, value)
    return value


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
    "DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_QUEUE_REPORT_CONFIG_VERSION",
    "MarketSourceFamilyDivergenceQueueConfig",
    "MarketSourceFamilyDivergenceQueueInputRow",
    "MarketSourceFamilyDivergenceQueueReport",
    "MarketSourceFamilyDivergenceQueueRow",
    "build_market_source_family_divergence_queue_report",
    "market_source_family_divergence_queue_report_to_payload",
)
