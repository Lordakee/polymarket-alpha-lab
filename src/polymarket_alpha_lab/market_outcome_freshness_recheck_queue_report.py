"""Pure in-memory report for market outcome freshness recheck queues."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from numbers import Number
from typing import Any


DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_QUEUE_CONFIG_VERSION = (
    "market-outcome-freshness-recheck-queue-v0"
)

RECHECK_REASON_CODES = (
    "missing_outcome",
    "stale_official_source",
    "proxy_contradiction",
    "missing_acknowledgement",
    "close_age_priority",
)
QUEUE_STATUSES = ("clear", "queued")
ROW_QUEUE_STATUSES = ("queued",)
PRIORITY_STATUSES = ("urgent", "priority", "standard")
RATIO_QUANT = Decimal("0.000001")
DECIMAL_ZERO = Decimal("0")
MICROSECONDS_PER_SECOND = Decimal("1000000")


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckQueueConfig:
    config_version: str = DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_QUEUE_CONFIG_VERSION
    stale_official_source_after_seconds: Decimal = Decimal("900")
    priority_close_age_seconds: Decimal = Decimal("3600")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_official_source_after_seconds",
            _require_nonnegative_decimal(
                "stale_official_source_after_seconds",
                self.stale_official_source_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "priority_close_age_seconds",
            _require_nonnegative_decimal(
                "priority_close_age_seconds",
                self.priority_close_age_seconds,
            ),
        )
        _require_hard_flags("MarketOutcomeFreshnessRecheckQueueConfig", self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessObservation:
    market_id: str
    market_slug: str
    closed_at: datetime
    outcome: str | None
    official_source_checked_at: datetime | None
    proxy_outcome: str | None
    acknowledged_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(self, "closed_at", _as_utc("closed_at", self.closed_at))
        object.__setattr__(
            self,
            "outcome",
            _normalize_optional_string("outcome", self.outcome),
        )
        object.__setattr__(
            self,
            "official_source_checked_at",
            _as_optional_utc(
                "official_source_checked_at",
                self.official_source_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "proxy_outcome",
            _normalize_optional_string("proxy_outcome", self.proxy_outcome),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        _require_hard_flags("MarketOutcomeFreshnessObservation", self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckReasonCodeCount:
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
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("MarketOutcomeFreshnessRecheckReasonCodeCount", self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckQueueRow:
    market_id: str
    market_slug: str
    closed_at: datetime
    close_age_seconds: Decimal
    official_source_checked_at: datetime | None
    official_source_age_seconds: Decimal | None
    queue_status: str
    priority_status: str
    priority_rank: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(self, "closed_at", _as_utc("closed_at", self.closed_at))
        object.__setattr__(
            self,
            "close_age_seconds",
            _require_nonnegative_decimal("close_age_seconds", self.close_age_seconds),
        )
        object.__setattr__(
            self,
            "official_source_checked_at",
            _as_optional_utc(
                "official_source_checked_at",
                self.official_source_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "official_source_age_seconds",
            _require_optional_nonnegative_decimal(
                "official_source_age_seconds",
                self.official_source_age_seconds,
            ),
        )
        _require_row_queue_status("queue_status", self.queue_status)
        _require_priority_status("priority_status", self.priority_status)
        object.__setattr__(
            self,
            "priority_rank",
            _require_nonnegative_decimal("priority_rank", self.priority_rank),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("MarketOutcomeFreshnessRecheckQueueRow", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckQueueReport:
    generated_at: datetime
    config_version: str
    queue_status: str
    market_count: Decimal
    queued_count: Decimal
    clear_count: Decimal
    queued_ratio: Decimal
    stale_official_source_after_seconds: Decimal
    priority_close_age_seconds: Decimal
    rows: tuple[MarketOutcomeFreshnessRecheckQueueRow, ...]
    reason_code_counts: tuple[MarketOutcomeFreshnessRecheckReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_queue_status("queue_status", self.queue_status)
        for field_name in ("market_count", "queued_count", "clear_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "queued_ratio",
            _require_ratio("queued_ratio", self.queued_ratio),
        )
        object.__setattr__(
            self,
            "stale_official_source_after_seconds",
            _require_nonnegative_decimal(
                "stale_official_source_after_seconds",
                self.stale_official_source_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "priority_close_age_seconds",
            _require_nonnegative_decimal(
                "priority_close_age_seconds",
                self.priority_close_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("MarketOutcomeFreshnessRecheckQueueReport", self)
        _validate_report_consistency(self)


def build_market_outcome_freshness_recheck_queue_report(
    observations: list[MarketOutcomeFreshnessObservation]
    | tuple[MarketOutcomeFreshnessObservation, ...],
    *,
    config: MarketOutcomeFreshnessRecheckQueueConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckQueueReport:
    if type(config) is not MarketOutcomeFreshnessRecheckQueueConfig:
        raise ValueError("config must be a MarketOutcomeFreshnessRecheckQueueConfig")
    _require_hard_flags("MarketOutcomeFreshnessRecheckQueueConfig", config)

    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = _queue_rows(
        normalized,
        config=config,
        generated_at=generated_at_utc,
    )
    market_count = _count(len(normalized))
    queued_count = _count(len(rows))
    clear_count = market_count - queued_count
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)

    return MarketOutcomeFreshnessRecheckQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        queue_status="queued" if queued_count > DECIMAL_ZERO else "clear",
        market_count=market_count,
        queued_count=queued_count,
        clear_count=clear_count,
        queued_ratio=_ratio(queued_count, market_count),
        stale_official_source_after_seconds=config.stale_official_source_after_seconds,
        priority_close_age_seconds=config.priority_close_age_seconds,
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_outcome_freshness_recheck_queue_payload(
    report: MarketOutcomeFreshnessRecheckQueueReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeFreshnessRecheckQueueReport:
        raise ValueError("report must be a MarketOutcomeFreshnessRecheckQueueReport")
    _require_hard_flags("MarketOutcomeFreshnessRecheckQueueReport", report)
    payload = _json_ready_decimal_only(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _queue_rows(
    observations: tuple[MarketOutcomeFreshnessObservation, ...],
    *,
    config: MarketOutcomeFreshnessRecheckQueueConfig,
    generated_at: datetime,
) -> tuple[MarketOutcomeFreshnessRecheckQueueRow, ...]:
    rows = tuple(
        row
        for row in (
            _queue_row(observation, config=config, generated_at=generated_at)
            for observation in observations
        )
        if row is not None
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _queue_row(
    observation: MarketOutcomeFreshnessObservation,
    *,
    config: MarketOutcomeFreshnessRecheckQueueConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckQueueRow | None:
    _validate_not_after("closed_at", observation.closed_at, generated_at)
    _validate_optional_not_after(
        "official_source_checked_at",
        observation.official_source_checked_at,
        generated_at,
    )
    _validate_optional_not_after("acknowledged_at", observation.acknowledged_at, generated_at)

    close_age_seconds = _age_seconds(generated_at, observation.closed_at)
    official_source_age_seconds = (
        None
        if observation.official_source_checked_at is None
        else _age_seconds(generated_at, observation.official_source_checked_at)
    )
    reason_codes = _observation_reason_codes(
        observation,
        close_age_seconds=close_age_seconds,
        official_source_age_seconds=official_source_age_seconds,
        config=config,
    )
    if not reason_codes:
        return None

    priority_status, priority_rank = _priority(reason_codes)
    return MarketOutcomeFreshnessRecheckQueueRow(
        market_id=observation.market_id,
        market_slug=observation.market_slug,
        closed_at=observation.closed_at,
        close_age_seconds=close_age_seconds,
        official_source_checked_at=observation.official_source_checked_at,
        official_source_age_seconds=official_source_age_seconds,
        queue_status="queued",
        priority_status=priority_status,
        priority_rank=priority_rank,
        reason_codes=reason_codes,
    )


def _observation_reason_codes(
    observation: MarketOutcomeFreshnessObservation,
    *,
    close_age_seconds: Decimal,
    official_source_age_seconds: Decimal | None,
    config: MarketOutcomeFreshnessRecheckQueueConfig,
) -> tuple[str, ...]:
    checks = {
        "missing_outcome": observation.outcome is None,
        "stale_official_source": (
            official_source_age_seconds is None
            or official_source_age_seconds >= config.stale_official_source_after_seconds
        ),
        "proxy_contradiction": _has_proxy_contradiction(observation),
        "missing_acknowledgement": observation.acknowledged_at is None,
        "close_age_priority": close_age_seconds >= config.priority_close_age_seconds,
    }
    return tuple(reason_code for reason_code in RECHECK_REASON_CODES if checks[reason_code])


def _has_proxy_contradiction(observation: MarketOutcomeFreshnessObservation) -> bool:
    if observation.outcome is None or observation.proxy_outcome is None:
        return False
    return observation.outcome.casefold() != observation.proxy_outcome.casefold()


def _priority(reason_codes: tuple[str, ...]) -> tuple[str, Decimal]:
    if "missing_outcome" in reason_codes or "proxy_contradiction" in reason_codes:
        return "urgent", Decimal("1")
    if "close_age_priority" in reason_codes:
        return "priority", Decimal("2")
    return "standard", Decimal("3")


def _row_sort_key(
    row: MarketOutcomeFreshnessRecheckQueueRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (row.priority_rank, -row.close_age_seconds, row.market_slug, row.market_id)


def _reason_code_counts(
    rows: tuple[MarketOutcomeFreshnessRecheckQueueRow, ...],
) -> tuple[MarketOutcomeFreshnessRecheckReasonCodeCount, ...]:
    counts = dict.fromkeys(RECHECK_REASON_CODES, DECIMAL_ZERO)
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] += Decimal("1")
    return tuple(
        MarketOutcomeFreshnessRecheckReasonCodeCount(
            reason_code=reason_code,
            count=count,
        )
        for reason_code, count in counts.items()
        if count > DECIMAL_ZERO
    )


def _normalize_observations(
    observations: list[MarketOutcomeFreshnessObservation]
    | tuple[MarketOutcomeFreshnessObservation, ...],
) -> tuple[MarketOutcomeFreshnessObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not MarketOutcomeFreshnessObservation:
            raise ValueError(
                "observations must contain MarketOutcomeFreshnessObservation values",
            )
        _require_hard_flags("MarketOutcomeFreshnessObservation", observation)
    return normalized


def _normalize_rows(
    rows: list[MarketOutcomeFreshnessRecheckQueueRow]
    | tuple[MarketOutcomeFreshnessRecheckQueueRow, ...],
) -> tuple[MarketOutcomeFreshnessRecheckQueueRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketOutcomeFreshnessRecheckQueueRow:
            raise ValueError("rows must contain MarketOutcomeFreshnessRecheckQueueRow values")
        _require_hard_flags("MarketOutcomeFreshnessRecheckQueueRow", row)
    if tuple(sorted(normalized, key=_row_sort_key)) != normalized:
        raise ValueError("rows must be deterministic")
    return normalized


def _normalize_reason_code_counts(
    reason_code_counts: list[MarketOutcomeFreshnessRecheckReasonCodeCount]
    | tuple[MarketOutcomeFreshnessRecheckReasonCodeCount, ...],
) -> tuple[MarketOutcomeFreshnessRecheckReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(reason_code_counts)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not MarketOutcomeFreshnessRecheckReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketOutcomeFreshnessRecheckReasonCodeCount values",
            )
        _require_hard_flags("MarketOutcomeFreshnessRecheckReasonCodeCount", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        item
        for reason_code in RECHECK_REASON_CODES
        for item in normalized
        if item.reason_code == reason_code
    )
    if normalized != expected:
        raise ValueError("reason_code_counts must be deterministic")
    return normalized


def _normalize_reason_codes(reason_codes: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    seen: set[str] = set()
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in RECHECK_REASON_CODES if reason_code in seen)
    if normalized != expected:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _validate_row_consistency(row: MarketOutcomeFreshnessRecheckQueueRow) -> None:
    if not row.reason_codes:
        raise ValueError("queued rows require reason_codes")
    expected_priority_status, expected_priority_rank = _priority(row.reason_codes)
    if row.priority_status != expected_priority_status:
        raise ValueError("priority_status must match reason_codes")
    if row.priority_rank != expected_priority_rank:
        raise ValueError("priority_rank must match reason_codes")
    if row.official_source_checked_at is None and row.official_source_age_seconds is not None:
        raise ValueError("official_source_age_seconds must be absent without a source check")
    if row.official_source_checked_at is not None and row.official_source_age_seconds is None:
        raise ValueError("official_source_age_seconds is required with a source check")


def _validate_report_consistency(report: MarketOutcomeFreshnessRecheckQueueReport) -> None:
    if report.market_count != report.queued_count + report.clear_count:
        raise ValueError("market_count must equal queued_count plus clear_count")
    if report.queued_count != _count(len(report.rows)):
        raise ValueError("queued_count must match rows")
    if report.queued_ratio != _ratio(report.queued_count, report.market_count):
        raise ValueError("queued_ratio must match counts")
    if report.queue_status == "clear" and report.queued_count != DECIMAL_ZERO:
        raise ValueError("clear reports must not have queued rows")
    if report.queue_status == "queued" and report.queued_count == DECIMAL_ZERO:
        raise ValueError("queued reports require queued rows")
    expected_counts = _reason_code_counts(report.rows)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    expected_reason_codes = tuple(item.reason_code for item in expected_counts)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")


def _validate_not_after(field_name: str, value: datetime, upper_bound: datetime) -> None:
    if value > upper_bound:
        raise ValueError(f"{field_name} must be at or before generated_at")


def _validate_optional_not_after(
    field_name: str,
    value: datetime | None,
    upper_bound: datetime,
) -> None:
    if value is not None:
        _validate_not_after(field_name, value, upper_bound)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _require_nonnegative_decimal("age_seconds", seconds)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == DECIMAL_ZERO:
        return DECIMAL_ZERO.quantize(RATIO_QUANT)
    return (numerator / denominator).quantize(RATIO_QUANT)


def _count(value: int) -> Decimal:
    return Decimal(value)


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


def _normalize_optional_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_queue_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in QUEUE_STATUSES:
        raise ValueError(f"{field_name} must be clear or queued")


def _require_row_queue_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in ROW_QUEUE_STATUSES:
        raise ValueError(f"{field_name} must be queued")


def _require_priority_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in PRIORITY_STATUSES:
        raise ValueError(f"{field_name} must be urgent, priority, or standard")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in RECHECK_REASON_CODES:
        raise ValueError(f"{field_name} must be a known recheck reason")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > Decimal("1"):
        raise ValueError(f"{field_name} must be <= 1")
    if decimal_value != decimal_value.quantize(RATIO_QUANT):
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return decimal_value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _json_ready_decimal_only(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready_decimal_only(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_json_ready_decimal_only(item) for item in value]
    if type(value) is list:
        return [_json_ready_decimal_only(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready_decimal_only(item)
        return ready
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, Number):
        raise ValueError("payload numeric values must be Decimal-only")
    raise ValueError(f"payload contains unsupported value type {type(value).__name__}")


__all__ = (
    "DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_QUEUE_CONFIG_VERSION",
    "MarketOutcomeFreshnessObservation",
    "MarketOutcomeFreshnessRecheckQueueConfig",
    "MarketOutcomeFreshnessRecheckQueueReport",
    "MarketOutcomeFreshnessRecheckQueueRow",
    "MarketOutcomeFreshnessRecheckReasonCodeCount",
    "build_market_outcome_freshness_recheck_queue_report",
    "market_outcome_freshness_recheck_queue_payload",
)
