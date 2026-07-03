from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext


DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_COVERAGE_CONFIG_VERSION = (
    "market-outcome-freshness-recheck-coverage-v0"
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64)

CATEGORY_STATUSES = ("blocked", "watch", "ready")
REPORT_STATUSES = ("empty", "blocked", "watch", "ready")
CATEGORY_STATUS_WEIGHT = {"blocked": 0, "watch": 1, "ready": 2}
REPORT_STATUS_WEIGHT = {"empty": -1, "blocked": 0, "watch": 1, "ready": 2}

READY_REASON_CODE = "market_outcome_freshness_recheck_coverage_ready"
EMPTY_REASON_CODE = "no_market_outcome_freshness_recheck_coverage_rows"
REASON_CODE_WEIGHT = {
    "unresolved_outcome_coverage_gap": 0,
    "freshness_recheck_coverage_gap": 1,
    "stale_close_time_coverage_gap": 2,
    READY_REASON_CODE: 3,
    EMPTY_REASON_CODE: 4,
}
REASON_CODES = tuple(REASON_CODE_WEIGHT)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckCoverageConfig:
    config_version: str = DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_COVERAGE_CONFIG_VERSION
    stale_freshness_after_seconds: Decimal = Decimal("3600.000000")
    stale_close_time_after_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_freshness_after_seconds",
            _normalize_nonnegative_decimal(
                "stale_freshness_after_seconds",
                self.stale_freshness_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "stale_close_time_after_seconds",
            _normalize_nonnegative_decimal(
                "stale_close_time_after_seconds",
                self.stale_close_time_after_seconds,
            ),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckCoverageInput:
    market_id: str
    market_slug: str
    category_id: str
    outcome_id: str
    market_closes_at: datetime
    freshness_checked_at: datetime | None
    close_time_checked_at: datetime | None
    expected_outcome_count: Decimal
    resolved_outcome_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "market_slug", "category_id", "outcome_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "market_closes_at",
            _as_utc("market_closes_at", self.market_closes_at),
        )
        object.__setattr__(
            self,
            "freshness_checked_at",
            _as_optional_utc("freshness_checked_at", self.freshness_checked_at),
        )
        object.__setattr__(
            self,
            "close_time_checked_at",
            _as_optional_utc("close_time_checked_at", self.close_time_checked_at),
        )
        object.__setattr__(
            self,
            "expected_outcome_count",
            _normalize_nonnegative_decimal(
                "expected_outcome_count",
                self.expected_outcome_count,
            ),
        )
        object.__setattr__(
            self,
            "resolved_outcome_count",
            _normalize_nonnegative_decimal(
                "resolved_outcome_count",
                self.resolved_outcome_count,
            ),
        )
        if self.resolved_outcome_count > self.expected_outcome_count:
            raise ValueError("resolved_outcome_count must be <= expected_outcome_count")
        _require_safety_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckCoverageCategoryRow:
    category_id: str
    market_count: Decimal
    freshness_covered_count: Decimal
    freshness_gap_count: Decimal
    unresolved_outcome_count: Decimal
    stale_close_time_count: Decimal
    freshness_coverage_ratio: Decimal
    unresolved_outcome_ratio: Decimal
    stale_close_time_ratio: Decimal
    category_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category_id", self.category_id)
        for field_name in (
            "market_count",
            "freshness_covered_count",
            "freshness_gap_count",
            "unresolved_outcome_count",
            "stale_close_time_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_coverage_ratio",
            "unresolved_outcome_ratio",
            "stale_close_time_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_known_value("category_status", self.category_status, CATEGORY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_category_row(self)
        _require_safety_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckCoverageReport:
    generated_at: datetime
    config_version: str
    stale_freshness_after_seconds: Decimal
    stale_close_time_after_seconds: Decimal
    market_count: Decimal
    category_count: Decimal
    freshness_covered_count: Decimal
    freshness_gap_count: Decimal
    unresolved_outcome_count: Decimal
    stale_close_time_count: Decimal
    freshness_coverage_ratio: Decimal
    unresolved_outcome_ratio: Decimal
    stale_close_time_ratio: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    category_rows: tuple[MarketOutcomeFreshnessRecheckCoverageCategoryRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "stale_freshness_after_seconds",
            "stale_close_time_after_seconds",
            "market_count",
            "category_count",
            "freshness_covered_count",
            "freshness_gap_count",
            "unresolved_outcome_count",
            "stale_close_time_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_coverage_ratio",
            "unresolved_outcome_ratio",
            "stale_close_time_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_known_value("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "category_rows", _normalize_category_rows(self.category_rows))
        _validate_report(self)
        _require_safety_flags(self)


def build_market_outcome_freshness_recheck_coverage_report(
    items: tuple[MarketOutcomeFreshnessRecheckCoverageInput, ...]
    | list[MarketOutcomeFreshnessRecheckCoverageInput],
    *,
    config: MarketOutcomeFreshnessRecheckCoverageConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckCoverageReport:
    if type(config) is not MarketOutcomeFreshnessRecheckCoverageConfig:
        raise ValueError(
            "config must be a MarketOutcomeFreshnessRecheckCoverageConfig",
        )
    _require_safety_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_inputs(items)
    for item in normalized_items:
        _require_not_after_generated(
            "freshness_checked_at",
            item.freshness_checked_at,
            generated_at_utc,
        )
        _require_not_after_generated(
            "close_time_checked_at",
            item.close_time_checked_at,
            generated_at_utc,
        )

    category_rows = _category_rows(
        normalized_items,
        config=config,
        generated_at=generated_at_utc,
    )
    market_count = _count(len(normalized_items))
    freshness_covered_count = _sum_decimal(
        row.freshness_covered_count for row in category_rows
    )
    freshness_gap_count = _sum_decimal(row.freshness_gap_count for row in category_rows)
    unresolved_outcome_count = _sum_decimal(
        row.unresolved_outcome_count for row in category_rows
    )
    stale_close_time_count = _sum_decimal(
        row.stale_close_time_count for row in category_rows
    )

    return MarketOutcomeFreshnessRecheckCoverageReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        stale_freshness_after_seconds=config.stale_freshness_after_seconds,
        stale_close_time_after_seconds=config.stale_close_time_after_seconds,
        market_count=market_count,
        category_count=_count(len(category_rows)),
        freshness_covered_count=freshness_covered_count,
        freshness_gap_count=freshness_gap_count,
        unresolved_outcome_count=unresolved_outcome_count,
        stale_close_time_count=stale_close_time_count,
        freshness_coverage_ratio=_ratio(freshness_covered_count, market_count),
        unresolved_outcome_ratio=_ratio(unresolved_outcome_count, market_count),
        stale_close_time_ratio=_ratio(stale_close_time_count, market_count),
        report_status=_report_status(category_rows),
        reason_codes=_report_reason_codes(category_rows),
        category_rows=category_rows,
    )


def market_outcome_freshness_recheck_coverage_report_payload(
    report: MarketOutcomeFreshnessRecheckCoverageReport,
) -> dict[str, object]:
    if type(report) is not MarketOutcomeFreshnessRecheckCoverageReport:
        raise ValueError(
            "report must be a MarketOutcomeFreshnessRecheckCoverageReport",
        )
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("payload must be a dict")
    return value


def _category_rows(
    items: tuple[MarketOutcomeFreshnessRecheckCoverageInput, ...],
    *,
    config: MarketOutcomeFreshnessRecheckCoverageConfig,
    generated_at: datetime,
) -> tuple[MarketOutcomeFreshnessRecheckCoverageCategoryRow, ...]:
    grouped: dict[str, list[MarketOutcomeFreshnessRecheckCoverageInput]] = {}
    for item in items:
        grouped.setdefault(item.category_id, []).append(item)
    rows = tuple(
        _category_row_from_items(
            category_id=category_id,
            items=tuple(grouped[category_id]),
            config=config,
            generated_at=generated_at,
        )
        for category_id in sorted(grouped)
    )
    return tuple(sorted(rows, key=_category_row_key))


def _category_row_from_items(
    *,
    category_id: str,
    items: tuple[MarketOutcomeFreshnessRecheckCoverageInput, ...],
    config: MarketOutcomeFreshnessRecheckCoverageConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckCoverageCategoryRow:
    market_count = _count(len(items))
    freshness_covered_count = _count(
        sum(
            1
            for item in items
            if _freshness_covered(
                item,
                config=config,
                generated_at=generated_at,
            )
        ),
    )
    freshness_gap_count = market_count - freshness_covered_count
    unresolved_outcome_count = _count(
        sum(1 for item in items if _unresolved_outcome_gap(item) > ZERO),
    )
    stale_close_time_count = _count(
        sum(
            1
            for item in items
            if _stale_close_time(
                item,
                config=config,
                generated_at=generated_at,
            )
        ),
    )
    reason_codes = _coverage_reason_codes(
        freshness_gap_count=freshness_gap_count,
        unresolved_outcome_count=unresolved_outcome_count,
        stale_close_time_count=stale_close_time_count,
    )
    return MarketOutcomeFreshnessRecheckCoverageCategoryRow(
        category_id=category_id,
        market_count=market_count,
        freshness_covered_count=freshness_covered_count,
        freshness_gap_count=freshness_gap_count,
        unresolved_outcome_count=unresolved_outcome_count,
        stale_close_time_count=stale_close_time_count,
        freshness_coverage_ratio=_ratio(freshness_covered_count, market_count),
        unresolved_outcome_ratio=_ratio(unresolved_outcome_count, market_count),
        stale_close_time_ratio=_ratio(stale_close_time_count, market_count),
        category_status=_category_status(reason_codes),
        reason_codes=reason_codes,
    )


def _freshness_covered(
    item: MarketOutcomeFreshnessRecheckCoverageInput,
    *,
    config: MarketOutcomeFreshnessRecheckCoverageConfig,
    generated_at: datetime,
) -> bool:
    if item.freshness_checked_at is None:
        return False
    return (
        _seconds_between(item.freshness_checked_at, generated_at)
        <= config.stale_freshness_after_seconds
    )


def _stale_close_time(
    item: MarketOutcomeFreshnessRecheckCoverageInput,
    *,
    config: MarketOutcomeFreshnessRecheckCoverageConfig,
    generated_at: datetime,
) -> bool:
    if item.close_time_checked_at is None:
        return True
    return (
        _seconds_between(item.close_time_checked_at, generated_at)
        > config.stale_close_time_after_seconds
    )


def _unresolved_outcome_gap(
    item: MarketOutcomeFreshnessRecheckCoverageInput,
) -> Decimal:
    return item.expected_outcome_count - item.resolved_outcome_count


def _coverage_reason_codes(
    *,
    freshness_gap_count: Decimal,
    unresolved_outcome_count: Decimal,
    stale_close_time_count: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if unresolved_outcome_count > ZERO:
        reason_codes.append("unresolved_outcome_coverage_gap")
    if freshness_gap_count > ZERO:
        reason_codes.append("freshness_recheck_coverage_gap")
    if stale_close_time_count > ZERO:
        reason_codes.append("stale_close_time_coverage_gap")
    if not reason_codes:
        return (READY_REASON_CODE,)
    return tuple(sorted(reason_codes, key=_reason_key))


def _category_status(reason_codes: tuple[str, ...]) -> str:
    if "unresolved_outcome_coverage_gap" in reason_codes:
        return "blocked"
    if reason_codes == (READY_REASON_CODE,):
        return "ready"
    return "watch"


def _report_status(
    category_rows: tuple[MarketOutcomeFreshnessRecheckCoverageCategoryRow, ...],
) -> str:
    if not category_rows:
        return "empty"
    return min(
        (row.category_status for row in category_rows),
        key=lambda status: REPORT_STATUS_WEIGHT[status],
    )


def _report_reason_codes(
    category_rows: tuple[MarketOutcomeFreshnessRecheckCoverageCategoryRow, ...],
) -> tuple[str, ...]:
    if not category_rows:
        return (EMPTY_REASON_CODE,)
    issue_codes = {
        reason_code
        for row in category_rows
        for reason_code in row.reason_codes
        if reason_code != READY_REASON_CODE
    }
    if not issue_codes:
        return (READY_REASON_CODE,)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in issue_codes)


def _category_row_key(
    row: MarketOutcomeFreshnessRecheckCoverageCategoryRow,
) -> tuple[int, int, str]:
    return (
        CATEGORY_STATUS_WEIGHT[row.category_status],
        min(REASON_CODE_WEIGHT[reason_code] for reason_code in row.reason_codes),
        row.category_id,
    )


def _normalize_inputs(
    values: tuple[MarketOutcomeFreshnessRecheckCoverageInput, ...]
    | list[MarketOutcomeFreshnessRecheckCoverageInput],
) -> tuple[MarketOutcomeFreshnessRecheckCoverageInput, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("items must be a list or tuple")
    items = tuple(values)
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not MarketOutcomeFreshnessRecheckCoverageInput:
            raise ValueError(
                "items must contain MarketOutcomeFreshnessRecheckCoverageInput values",
            )
        _require_safety_flags(item)
        key = (item.market_id, item.outcome_id)
        if key in seen:
            raise ValueError("market_id and outcome_id pairs must be unique")
        seen.add(key)
    return items


def _normalize_category_rows(
    values: tuple[MarketOutcomeFreshnessRecheckCoverageCategoryRow, ...],
) -> tuple[MarketOutcomeFreshnessRecheckCoverageCategoryRow, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("category_rows must be a list or tuple")
    rows = tuple(values)
    for row in rows:
        if type(row) is not MarketOutcomeFreshnessRecheckCoverageCategoryRow:
            raise ValueError(
                "category_rows must contain MarketOutcomeFreshnessRecheckCoverageCategoryRow values",
            )
        _require_safety_flags(row)
    if rows != tuple(sorted(rows, key=_category_row_key)):
        raise ValueError("category_rows must be deterministic")
    return rows


def _validate_category_row(
    row: MarketOutcomeFreshnessRecheckCoverageCategoryRow,
) -> None:
    if row.freshness_covered_count + row.freshness_gap_count != row.market_count:
        raise ValueError("freshness counts must match market_count")
    if row.unresolved_outcome_count > row.market_count:
        raise ValueError("unresolved_outcome_count must not exceed market_count")
    if row.stale_close_time_count > row.market_count:
        raise ValueError("stale_close_time_count must not exceed market_count")
    if row.freshness_coverage_ratio != _ratio(
        row.freshness_covered_count,
        row.market_count,
    ):
        raise ValueError("freshness_coverage_ratio must match counts")
    if row.unresolved_outcome_ratio != _ratio(
        row.unresolved_outcome_count,
        row.market_count,
    ):
        raise ValueError("unresolved_outcome_ratio must match counts")
    if row.stale_close_time_ratio != _ratio(
        row.stale_close_time_count,
        row.market_count,
    ):
        raise ValueError("stale_close_time_ratio must match counts")
    if row.reason_codes != _coverage_reason_codes(
        freshness_gap_count=row.freshness_gap_count,
        unresolved_outcome_count=row.unresolved_outcome_count,
        stale_close_time_count=row.stale_close_time_count,
    ):
        raise ValueError("reason_codes must match counts")
    if row.category_status != _category_status(row.reason_codes):
        raise ValueError("category_status must match reason_codes")


def _validate_report(report: MarketOutcomeFreshnessRecheckCoverageReport) -> None:
    rows = report.category_rows
    if report.category_count != _count(len(rows)):
        raise ValueError("category_count must match category_rows")
    if report.market_count != _sum_decimal(row.market_count for row in rows):
        raise ValueError("market_count must match category_rows")
    if report.freshness_covered_count != _sum_decimal(
        row.freshness_covered_count for row in rows
    ):
        raise ValueError("freshness_covered_count must match category_rows")
    if report.freshness_gap_count != _sum_decimal(
        row.freshness_gap_count for row in rows
    ):
        raise ValueError("freshness_gap_count must match category_rows")
    if report.unresolved_outcome_count != _sum_decimal(
        row.unresolved_outcome_count for row in rows
    ):
        raise ValueError("unresolved_outcome_count must match category_rows")
    if report.stale_close_time_count != _sum_decimal(
        row.stale_close_time_count for row in rows
    ):
        raise ValueError("stale_close_time_count must match category_rows")
    if report.freshness_coverage_ratio != _ratio(
        report.freshness_covered_count,
        report.market_count,
    ):
        raise ValueError("freshness_coverage_ratio must match counts")
    if report.unresolved_outcome_ratio != _ratio(
        report.unresolved_outcome_count,
        report.market_count,
    ):
        raise ValueError("unresolved_outcome_ratio must match counts")
    if report.stale_close_time_ratio != _ratio(
        report.stale_close_time_count,
        report.market_count,
    ):
        raise ValueError("stale_close_time_ratio must match counts")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match category_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match category_rows")


def _reason_key(reason_code: str) -> int:
    return REASON_CODE_WEIGHT[reason_code]


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        total += value
    return total.quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("datetime range must be nonnegative")
    delta = end - start
    microseconds = (
        ((delta.days * 24 * 60 * 60) + delta.seconds) * 1_000_000
    ) + delta.microseconds
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(microseconds) / MICROSECONDS_PER_SECOND).quantize(QUANTUM)


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _require_not_after_generated(
    field_name: str,
    value: datetime | None,
    generated_at: datetime,
) -> None:
    if value is not None and value > generated_at:
        raise ValueError(f"{field_name} must be <= generated_at")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_known_value(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be known")


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in REASON_CODE_WEIGHT:
            raise ValueError("reason_codes must be known")
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(QUANTUM)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


__all__ = (
    "DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_COVERAGE_CONFIG_VERSION",
    "MarketOutcomeFreshnessRecheckCoverageCategoryRow",
    "MarketOutcomeFreshnessRecheckCoverageConfig",
    "MarketOutcomeFreshnessRecheckCoverageInput",
    "MarketOutcomeFreshnessRecheckCoverageReport",
    "build_market_outcome_freshness_recheck_coverage_report",
    "market_outcome_freshness_recheck_coverage_report_payload",
)
