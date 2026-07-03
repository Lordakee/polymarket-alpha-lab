from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext


DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_HEALTH_CONFIG_VERSION = (
    "market-outcome-freshness-recheck-health-v0"
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64)

FRESHNESS_STATUSES = ("missing", "stale", "fresh")
OUTCOME_GAP_STATUSES = ("gap", "clear")
CLOSE_TIME_STATUSES = ("pressure", "clear")
ROW_HEALTH_STATUSES = ("blocked", "watch", "pass")
REPORT_HEALTH_STATUSES = ("empty", "blocked", "watch", "pass")
HEALTH_STATUS_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}

CLEAR_REASON_CODE = "market_outcome_freshness_recheck_clear"
READY_REASON_CODE = "market_outcome_freshness_recheck_ready"
EMPTY_REASON_CODE = "no_market_outcome_freshness_recheck_rows"
REASON_CODE_WEIGHT = {
    "unresolved_outcome_gap": 0,
    "freshness_age_missing": 1,
    "freshness_age_stale": 2,
    "close_time_pressure": 3,
    CLEAR_REASON_CODE: 4,
    READY_REASON_CODE: 5,
    EMPTY_REASON_CODE: 6,
}
REASON_CODES = tuple(REASON_CODE_WEIGHT)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckHealthConfig:
    config_version: str = DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_HEALTH_CONFIG_VERSION
    stale_freshness_after_seconds: Decimal = Decimal("3600.000000")
    max_unresolved_outcome_gap: Decimal = Decimal("0.000000")
    close_time_pressure_within_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "stale_freshness_after_seconds",
            "max_unresolved_outcome_gap",
            "close_time_pressure_within_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_safety_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckHealthInput:
    market_id: str
    market_slug: str
    outcome_id: str
    recheck_requested_at: datetime
    market_closes_at: datetime
    freshness_checked_at: datetime | None
    expected_outcome_count: Decimal
    resolved_outcome_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "market_slug", "outcome_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "recheck_requested_at",
            _as_utc("recheck_requested_at", self.recheck_requested_at),
        )
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
class MarketOutcomeFreshnessRecheckHealthReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckHealthRow:
    market_id: str
    market_slug: str
    outcome_id: str
    recheck_requested_at: datetime
    market_closes_at: datetime
    freshness_checked_at: datetime | None
    expected_outcome_count: Decimal
    resolved_outcome_count: Decimal
    unresolved_outcome_gap: Decimal
    recheck_age_seconds: Decimal
    freshness_age_seconds: Decimal | None
    close_time_delta_seconds: Decimal
    freshness_status: str
    outcome_gap_status: str
    close_time_status: str
    health_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "market_slug", "outcome_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "recheck_requested_at",
            _as_utc("recheck_requested_at", self.recheck_requested_at),
        )
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
        for field_name in (
            "expected_outcome_count",
            "resolved_outcome_count",
            "unresolved_outcome_gap",
            "recheck_age_seconds",
            "close_time_delta_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "freshness_age_seconds",
                self.freshness_age_seconds,
            ),
        )
        _require_known_value("freshness_status", self.freshness_status, FRESHNESS_STATUSES)
        _require_known_value(
            "outcome_gap_status",
            self.outcome_gap_status,
            OUTCOME_GAP_STATUSES,
        )
        _require_known_value(
            "close_time_status",
            self.close_time_status,
            CLOSE_TIME_STATUSES,
        )
        _require_known_value("health_status", self.health_status, ROW_HEALTH_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_safety_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckHealthReport:
    generated_at: datetime
    config_version: str
    stale_freshness_after_seconds: Decimal
    max_unresolved_outcome_gap: Decimal
    close_time_pressure_within_seconds: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    stale_freshness_count: Decimal
    unresolved_outcome_gap_count: Decimal
    close_time_pressure_count: Decimal
    stale_freshness_ratio: Decimal
    unresolved_outcome_gap_ratio: Decimal
    close_time_pressure_ratio: Decimal
    health_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketOutcomeFreshnessRecheckHealthReasonCodeCount, ...]
    rows: tuple[MarketOutcomeFreshnessRecheckHealthRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "stale_freshness_after_seconds",
            "max_unresolved_outcome_gap",
            "close_time_pressure_within_seconds",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "stale_freshness_count",
            "unresolved_outcome_gap_count",
            "close_time_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_freshness_ratio",
            "unresolved_outcome_gap_ratio",
            "close_time_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_known_value("health_status", self.health_status, REPORT_HEALTH_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_market_outcome_freshness_recheck_health_report(
    rows: list[MarketOutcomeFreshnessRecheckHealthInput]
    | tuple[MarketOutcomeFreshnessRecheckHealthInput, ...],
    *,
    config: MarketOutcomeFreshnessRecheckHealthConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckHealthReport:
    if type(config) is not MarketOutcomeFreshnessRecheckHealthConfig:
        raise ValueError(
            "config must be a MarketOutcomeFreshnessRecheckHealthConfig",
        )
    _require_safety_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(rows)
    health_rows = tuple(
        sorted(
            (
                _row_from_input(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in normalized_inputs
            ),
            key=_row_key,
        ),
    )

    row_count = _count(len(health_rows))
    stale_count = _reason_count(health_rows, "freshness_age_missing") + _reason_count(
        health_rows,
        "freshness_age_stale",
    )
    gap_count = _reason_count(health_rows, "unresolved_outcome_gap")
    close_count = _reason_count(health_rows, "close_time_pressure")

    return MarketOutcomeFreshnessRecheckHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        stale_freshness_after_seconds=config.stale_freshness_after_seconds,
        max_unresolved_outcome_gap=config.max_unresolved_outcome_gap,
        close_time_pressure_within_seconds=config.close_time_pressure_within_seconds,
        row_count=row_count,
        pass_count=_status_count(health_rows, "pass"),
        watch_count=_status_count(health_rows, "watch"),
        blocked_count=_status_count(health_rows, "blocked"),
        stale_freshness_count=stale_count,
        unresolved_outcome_gap_count=gap_count,
        close_time_pressure_count=close_count,
        stale_freshness_ratio=_ratio(stale_count, row_count),
        unresolved_outcome_gap_ratio=_ratio(gap_count, row_count),
        close_time_pressure_ratio=_ratio(close_count, row_count),
        health_status=_report_health_status(health_rows),
        reason_codes=_report_reason_codes(health_rows),
        reason_code_counts=_reason_code_counts(health_rows),
        rows=health_rows,
    )


def market_outcome_freshness_recheck_health_report_payload(
    report: MarketOutcomeFreshnessRecheckHealthReport,
) -> dict[str, object]:
    if type(report) is not MarketOutcomeFreshnessRecheckHealthReport:
        raise ValueError(
            "report must be a MarketOutcomeFreshnessRecheckHealthReport",
        )
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("payload must be a dict")
    return value


def _row_from_input(
    item: MarketOutcomeFreshnessRecheckHealthInput,
    *,
    config: MarketOutcomeFreshnessRecheckHealthConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckHealthRow:
    _require_not_after_generated("recheck_requested_at", item.recheck_requested_at, generated_at)
    _require_not_after_generated("freshness_checked_at", item.freshness_checked_at, generated_at)
    recheck_age_seconds = _seconds_between(item.recheck_requested_at, generated_at)
    freshness_age_seconds = (
        None
        if item.freshness_checked_at is None
        else _seconds_between(item.freshness_checked_at, generated_at)
    )
    close_time_delta_seconds = (
        ZERO
        if item.market_closes_at <= generated_at
        else _seconds_between(generated_at, item.market_closes_at)
    )
    unresolved_outcome_gap = _normalize_nonnegative_decimal(
        "unresolved_outcome_gap",
        item.expected_outcome_count - item.resolved_outcome_count,
    )
    reason_codes = _row_reason_codes(
        unresolved_outcome_gap=unresolved_outcome_gap,
        freshness_age_seconds=freshness_age_seconds,
        close_time_delta_seconds=close_time_delta_seconds,
        config=config,
    )

    return MarketOutcomeFreshnessRecheckHealthRow(
        market_id=item.market_id,
        market_slug=item.market_slug,
        outcome_id=item.outcome_id,
        recheck_requested_at=item.recheck_requested_at,
        market_closes_at=item.market_closes_at,
        freshness_checked_at=item.freshness_checked_at,
        expected_outcome_count=item.expected_outcome_count,
        resolved_outcome_count=item.resolved_outcome_count,
        unresolved_outcome_gap=unresolved_outcome_gap,
        recheck_age_seconds=recheck_age_seconds,
        freshness_age_seconds=freshness_age_seconds,
        close_time_delta_seconds=close_time_delta_seconds,
        freshness_status=_freshness_status(freshness_age_seconds, config=config),
        outcome_gap_status=(
            "gap"
            if unresolved_outcome_gap > config.max_unresolved_outcome_gap
            else "clear"
        ),
        close_time_status=(
            "pressure"
            if "close_time_pressure" in reason_codes
            else "clear"
        ),
        health_status=_row_health_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    unresolved_outcome_gap: Decimal,
    freshness_age_seconds: Decimal | None,
    close_time_delta_seconds: Decimal,
    config: MarketOutcomeFreshnessRecheckHealthConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if unresolved_outcome_gap > config.max_unresolved_outcome_gap:
        reason_codes.append("unresolved_outcome_gap")
    if freshness_age_seconds is None:
        reason_codes.append("freshness_age_missing")
    elif freshness_age_seconds > config.stale_freshness_after_seconds:
        reason_codes.append("freshness_age_stale")
    if close_time_delta_seconds <= config.close_time_pressure_within_seconds:
        reason_codes.append("close_time_pressure")
    if not reason_codes:
        reason_codes.append(CLEAR_REASON_CODE)
    return tuple(sorted(reason_codes, key=_reason_key))


def _freshness_status(
    freshness_age_seconds: Decimal | None,
    *,
    config: MarketOutcomeFreshnessRecheckHealthConfig,
) -> str:
    if freshness_age_seconds is None:
        return "missing"
    if freshness_age_seconds > config.stale_freshness_after_seconds:
        return "stale"
    return "fresh"


def _row_health_status(reason_codes: tuple[str, ...]) -> str:
    if "unresolved_outcome_gap" in reason_codes:
        return "blocked"
    if reason_codes == (CLEAR_REASON_CODE,):
        return "pass"
    return "watch"


def _report_health_status(
    rows: tuple[MarketOutcomeFreshnessRecheckHealthRow, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.health_status == "blocked" for row in rows):
        return "blocked"
    if any(row.health_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[MarketOutcomeFreshnessRecheckHealthRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    issue_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON_CODE
    }
    if not issue_codes:
        return (READY_REASON_CODE,)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in issue_codes)


def _reason_code_counts(
    rows: tuple[MarketOutcomeFreshnessRecheckHealthRow, ...],
) -> tuple[MarketOutcomeFreshnessRecheckHealthReasonCodeCount, ...]:
    counts = {reason_code: ZERO for reason_code in REASON_CODES}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] += ONE
    return tuple(
        MarketOutcomeFreshnessRecheckHealthReasonCodeCount(
            reason_code=reason_code,
            count=count,
        )
        for reason_code, count in counts.items()
        if count > ZERO
    )


def _row_key(
    row: MarketOutcomeFreshnessRecheckHealthRow,
) -> tuple[int, int, str, str, str]:
    return (
        HEALTH_STATUS_WEIGHT[row.health_status],
        min(REASON_CODE_WEIGHT[reason_code] for reason_code in row.reason_codes),
        row.market_slug,
        row.market_id,
        row.outcome_id,
    )


def _normalize_inputs(
    values: list[MarketOutcomeFreshnessRecheckHealthInput]
    | tuple[MarketOutcomeFreshnessRecheckHealthInput, ...],
) -> tuple[MarketOutcomeFreshnessRecheckHealthInput, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(values)
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not MarketOutcomeFreshnessRecheckHealthInput:
            raise ValueError(
                "rows must contain MarketOutcomeFreshnessRecheckHealthInput values",
            )
        _require_safety_flags(item)
        key = (item.market_id, item.outcome_id)
        if key in seen:
            raise ValueError("market_id and outcome_id pairs must be unique")
        seen.add(key)
    return normalized


def _normalize_rows(
    values: tuple[MarketOutcomeFreshnessRecheckHealthRow, ...],
) -> tuple[MarketOutcomeFreshnessRecheckHealthRow, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(values)
    for row in rows:
        if type(row) is not MarketOutcomeFreshnessRecheckHealthRow:
            raise ValueError(
                "rows must contain MarketOutcomeFreshnessRecheckHealthRow values",
            )
        _require_safety_flags(row)
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must be deterministic")
    return rows


def _normalize_reason_code_counts(
    values: tuple[MarketOutcomeFreshnessRecheckHealthReasonCodeCount, ...],
) -> tuple[MarketOutcomeFreshnessRecheckHealthReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(values)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not MarketOutcomeFreshnessRecheckHealthReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketOutcomeFreshnessRecheckHealthReasonCodeCount values",
            )
        _require_safety_flags(item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        item for reason_code in REASON_CODES for item in counts if item.reason_code == reason_code
    )
    if counts != expected:
        raise ValueError("reason_code_counts must be deterministic")
    return counts


def _validate_row_consistency(row: MarketOutcomeFreshnessRecheckHealthRow) -> None:
    if row.resolved_outcome_count > row.expected_outcome_count:
        raise ValueError("resolved_outcome_count must be <= expected_outcome_count")
    if row.unresolved_outcome_gap != row.expected_outcome_count - row.resolved_outcome_count:
        raise ValueError("unresolved_outcome_gap must match outcome counts")
    if row.freshness_checked_at is None and row.freshness_age_seconds is not None:
        raise ValueError("freshness_age_seconds requires freshness_checked_at")
    if row.freshness_checked_at is not None and row.freshness_age_seconds is None:
        raise ValueError("freshness_age_seconds is required with freshness_checked_at")
    if row.freshness_checked_at is None and row.freshness_status != "missing":
        raise ValueError("freshness_status must match freshness_checked_at")
    if row.freshness_checked_at is not None and row.freshness_status == "missing":
        raise ValueError("freshness_status must match freshness_checked_at")
    expected_gap_status = (
        "gap" if "unresolved_outcome_gap" in row.reason_codes else "clear"
    )
    if row.outcome_gap_status != expected_gap_status:
        raise ValueError("outcome_gap_status must match unresolved_outcome_gap")
    expected_close_status = (
        "pressure" if "close_time_pressure" in row.reason_codes else "clear"
    )
    if row.close_time_status != expected_close_status:
        raise ValueError("close_time_status must match reason_codes")
    if row.health_status != _row_health_status(row.reason_codes):
        raise ValueError("health_status must match reason_codes")


def _validate_report_consistency(report: MarketOutcomeFreshnessRecheckHealthReport) -> None:
    rows = report.rows
    if report.row_count != _count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    stale_count = _reason_count(rows, "freshness_age_missing") + _reason_count(
        rows,
        "freshness_age_stale",
    )
    gap_count = _reason_count(rows, "unresolved_outcome_gap")
    close_count = _reason_count(rows, "close_time_pressure")
    if report.stale_freshness_count != stale_count:
        raise ValueError("stale_freshness_count must match rows")
    if report.unresolved_outcome_gap_count != gap_count:
        raise ValueError("unresolved_outcome_gap_count must match rows")
    if report.close_time_pressure_count != close_count:
        raise ValueError("close_time_pressure_count must match rows")
    if report.stale_freshness_ratio != _ratio(stale_count, report.row_count):
        raise ValueError("stale_freshness_ratio must match rows")
    if report.unresolved_outcome_gap_ratio != _ratio(gap_count, report.row_count):
        raise ValueError("unresolved_outcome_gap_ratio must match rows")
    if report.close_time_pressure_ratio != _ratio(close_count, report.row_count):
        raise ValueError("close_time_pressure_ratio must match rows")
    if report.health_status != _report_health_status(rows):
        raise ValueError("health_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[MarketOutcomeFreshnessRecheckHealthRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.health_status == status))


def _reason_count(
    rows: tuple[MarketOutcomeFreshnessRecheckHealthRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM)


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


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_WEIGHT:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _reason_key(reason_code: str) -> int:
    return REASON_CODE_WEIGHT[reason_code]


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(QUANTUM)


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


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
    "DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_HEALTH_CONFIG_VERSION",
    "MarketOutcomeFreshnessRecheckHealthConfig",
    "MarketOutcomeFreshnessRecheckHealthInput",
    "MarketOutcomeFreshnessRecheckHealthReasonCodeCount",
    "MarketOutcomeFreshnessRecheckHealthReport",
    "MarketOutcomeFreshnessRecheckHealthRow",
    "build_market_outcome_freshness_recheck_health_report",
    "market_outcome_freshness_recheck_health_report_payload",
)
