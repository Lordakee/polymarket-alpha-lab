"""Pure in-memory market outcome freshness recheck readiness report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_READINESS_CONFIG_VERSION = (
    "market-outcome-freshness-recheck-readiness-v0"
)

ZERO = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
SECOND_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")

ROW_STATUSES = ("blocked", "watch", "ready")
REPORT_STATUSES = ("empty", "blocked", "watch", "ready")
STATUS_WEIGHT = {"blocked": 0, "watch": 1, "ready": 2}

QUEUE_BUCKETS = ("not_queued", "queued_waiting_ack", "queued")
ACK_BUCKETS = ("missing_ack", "acknowledged")

MISSING_OFFICIAL_SOURCE_REASON = "missing_official_source"
STALE_OUTCOME_REASON = "stale_outcome_timestamp"
STALE_RECHECK_REASON = "stale_recheck_age"
QUEUE_NOT_READY_REASON = "queue_not_ready"
ACK_NOT_READY_REASON = "ack_not_ready"
READY_REASON = "outcome_freshness_recheck_ready"
EMPTY_REASON = "outcome_freshness_recheck_readiness_empty"

REASON_CODES = (
    MISSING_OFFICIAL_SOURCE_REASON,
    STALE_OUTCOME_REASON,
    STALE_RECHECK_REASON,
    QUEUE_NOT_READY_REASON,
    ACK_NOT_READY_REASON,
    READY_REASON,
    EMPTY_REASON,
)
REASON_WEIGHT = {reason: index for index, reason in enumerate(REASON_CODES)}


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckReadinessConfig:
    outcome_fresh_after_seconds: Decimal = Decimal("900.000000")
    recheck_fresh_after_seconds: Decimal = Decimal("1800.000000")
    config_version: str = DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_READINESS_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "outcome_fresh_after_seconds",
            _normalize_positive_seconds(
                "outcome_fresh_after_seconds",
                self.outcome_fresh_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "recheck_fresh_after_seconds",
            _normalize_positive_seconds(
                "recheck_fresh_after_seconds",
                self.recheck_fresh_after_seconds,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckReadinessSource:
    market_id: str
    market_slug: str
    category_id: str
    outcome_observed_at: datetime | None
    outcome_source_checked_at: datetime | None
    official_source_url: str | None
    queued_at: datetime | None
    acknowledged_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "market_slug", "category_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "outcome_observed_at",
            _as_optional_utc("outcome_observed_at", self.outcome_observed_at),
        )
        object.__setattr__(
            self,
            "outcome_source_checked_at",
            _as_optional_utc(
                "outcome_source_checked_at",
                self.outcome_source_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "official_source_url",
            _normalize_optional_string("official_source_url", self.official_source_url),
        )
        object.__setattr__(self, "queued_at", _as_optional_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        if (
            self.queued_at is not None
            and self.acknowledged_at is not None
            and self.acknowledged_at < self.queued_at
        ):
            raise ValueError("acknowledged_at must be >= queued_at")
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckReadinessRow:
    market_id: str
    market_slug: str
    category_id: str
    outcome_observed_at: datetime | None
    outcome_source_checked_at: datetime | None
    official_source_url: str | None
    queued_at: datetime | None
    acknowledged_at: datetime | None
    outcome_age_seconds: Decimal
    recheck_age_seconds: Decimal
    outcome_age_delta_seconds: Decimal
    recheck_age_delta_seconds: Decimal
    queue_bucket: str
    ack_bucket: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "market_slug", "category_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "outcome_observed_at",
            _as_optional_utc("outcome_observed_at", self.outcome_observed_at),
        )
        object.__setattr__(
            self,
            "outcome_source_checked_at",
            _as_optional_utc(
                "outcome_source_checked_at",
                self.outcome_source_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "official_source_url",
            _normalize_optional_string("official_source_url", self.official_source_url),
        )
        object.__setattr__(self, "queued_at", _as_optional_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        for field_name in (
            "outcome_age_seconds",
            "recheck_age_seconds",
            "outcome_age_delta_seconds",
            "recheck_age_delta_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        _require_known_value("queue_bucket", self.queue_bucket, QUEUE_BUCKETS)
        _require_known_value("ack_bucket", self.ack_bucket, ACK_BUCKETS)
        _require_known_value("status", self.status, ROW_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckReadinessReport:
    generated_at: datetime
    config_version: str
    outcome_fresh_after_seconds: Decimal
    recheck_fresh_after_seconds: Decimal
    market_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    missing_official_source_count: Decimal
    stale_outcome_count: Decimal
    stale_recheck_count: Decimal
    queue_ready_count: Decimal
    ack_ready_count: Decimal
    ready_ratio: Decimal
    queue_ready_ratio: Decimal
    ack_ready_ratio: Decimal
    max_outcome_age_seconds: Decimal
    max_recheck_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    category_rollups: tuple[tuple[str, Decimal, Decimal, Decimal, Decimal], ...]
    rows: tuple[MarketOutcomeFreshnessRecheckReadinessRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("outcome_fresh_after_seconds", "recheck_fresh_after_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "market_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "missing_official_source_count",
            "stale_outcome_count",
            "stale_recheck_count",
            "queue_ready_count",
            "ack_ready_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("ready_ratio", "queue_ready_ratio", "ack_ready_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_outcome_age_seconds", "max_recheck_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        _require_known_value("status", self.status, REPORT_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "category_rollups",
            _normalize_category_rollups(self.category_rollups),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_market_outcome_freshness_recheck_readiness_report(
    sources: list[MarketOutcomeFreshnessRecheckReadinessSource]
    | tuple[MarketOutcomeFreshnessRecheckReadinessSource, ...],
    *,
    config: MarketOutcomeFreshnessRecheckReadinessConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckReadinessReport:
    if type(config) is not MarketOutcomeFreshnessRecheckReadinessConfig:
        raise ValueError(
            "config must be a MarketOutcomeFreshnessRecheckReadinessConfig",
        )
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_sources = _normalize_sources(sources)
    rows = tuple(
        sorted(
            (
                _row_from_source(
                    source,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for source in normalized_sources
            ),
            key=_row_sort_key,
        ),
    )
    market_count = _count(len(rows))
    ready_count = _count(sum(1 for row in rows if row.status == "ready"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    blocked_count = _count(sum(1 for row in rows if row.status == "blocked"))
    missing_official_source_count = _count(
        sum(1 for row in rows if MISSING_OFFICIAL_SOURCE_REASON in row.reason_codes),
    )
    stale_outcome_count = _count(
        sum(1 for row in rows if STALE_OUTCOME_REASON in row.reason_codes),
    )
    stale_recheck_count = _count(
        sum(1 for row in rows if STALE_RECHECK_REASON in row.reason_codes),
    )
    queue_ready_count = _count(sum(1 for row in rows if row.queue_bucket != "not_queued"))
    ack_ready_count = _count(sum(1 for row in rows if row.ack_bucket == "acknowledged"))

    return MarketOutcomeFreshnessRecheckReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        outcome_fresh_after_seconds=config.outcome_fresh_after_seconds,
        recheck_fresh_after_seconds=config.recheck_fresh_after_seconds,
        market_count=market_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        missing_official_source_count=missing_official_source_count,
        stale_outcome_count=stale_outcome_count,
        stale_recheck_count=stale_recheck_count,
        queue_ready_count=queue_ready_count,
        ack_ready_count=ack_ready_count,
        ready_ratio=_ratio(ready_count, market_count),
        queue_ready_ratio=_ratio(queue_ready_count, market_count),
        ack_ready_ratio=_ratio(ack_ready_count, market_count),
        max_outcome_age_seconds=_max_age(row.outcome_age_seconds for row in rows),
        max_recheck_age_seconds=_max_age(row.recheck_age_seconds for row in rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        category_rollups=_category_rollups(rows),
        rows=rows,
    )


def market_outcome_freshness_recheck_readiness_payload(
    report: MarketOutcomeFreshnessRecheckReadinessReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeFreshnessRecheckReadinessReport:
        raise ValueError(
            "report must be a MarketOutcomeFreshnessRecheckReadinessReport",
        )
    _require_hard_flags(report)
    payload = _json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_source(
    source: MarketOutcomeFreshnessRecheckReadinessSource,
    *,
    config: MarketOutcomeFreshnessRecheckReadinessConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckReadinessRow:
    _validate_optional_not_after("outcome_observed_at", source.outcome_observed_at, generated_at)
    _validate_optional_not_after(
        "outcome_source_checked_at",
        source.outcome_source_checked_at,
        generated_at,
    )
    _validate_optional_not_after("queued_at", source.queued_at, generated_at)
    _validate_optional_not_after("acknowledged_at", source.acknowledged_at, generated_at)

    outcome_age_seconds = _optional_age_seconds(source.outcome_observed_at, generated_at)
    recheck_age_seconds = _optional_age_seconds(
        source.outcome_source_checked_at,
        generated_at,
    )
    reason_codes = _row_reason_codes(
        source,
        outcome_age_seconds=outcome_age_seconds,
        recheck_age_seconds=recheck_age_seconds,
        config=config,
    )
    status = _row_status(reason_codes)
    return MarketOutcomeFreshnessRecheckReadinessRow(
        market_id=source.market_id,
        market_slug=source.market_slug,
        category_id=source.category_id,
        outcome_observed_at=source.outcome_observed_at,
        outcome_source_checked_at=source.outcome_source_checked_at,
        official_source_url=source.official_source_url,
        queued_at=source.queued_at,
        acknowledged_at=source.acknowledged_at,
        outcome_age_seconds=outcome_age_seconds,
        recheck_age_seconds=recheck_age_seconds,
        outcome_age_delta_seconds=_age_delta(
            outcome_age_seconds,
            config.outcome_fresh_after_seconds,
        ),
        recheck_age_delta_seconds=_age_delta(
            recheck_age_seconds,
            config.recheck_fresh_after_seconds,
        ),
        queue_bucket=_queue_bucket(source),
        ack_bucket=_ack_bucket(source),
        status=status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    source: MarketOutcomeFreshnessRecheckReadinessSource,
    *,
    outcome_age_seconds: Decimal,
    recheck_age_seconds: Decimal,
    config: MarketOutcomeFreshnessRecheckReadinessConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source.official_source_url is None:
        reasons.append(MISSING_OFFICIAL_SOURCE_REASON)
    if source.outcome_observed_at is None or outcome_age_seconds > config.outcome_fresh_after_seconds:
        reasons.append(STALE_OUTCOME_REASON)
    if (
        source.outcome_source_checked_at is None
        or recheck_age_seconds > config.recheck_fresh_after_seconds
    ):
        reasons.append(STALE_RECHECK_REASON)
    if source.queued_at is None:
        reasons.append(QUEUE_NOT_READY_REASON)
    if source.acknowledged_at is None:
        reasons.append(ACK_NOT_READY_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_reason_codes(tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if QUEUE_NOT_READY_REASON in reason_codes:
        return "blocked"
    if reason_codes == (READY_REASON,):
        return "ready"
    return "watch"


def _queue_bucket(source: MarketOutcomeFreshnessRecheckReadinessSource) -> str:
    if source.queued_at is None:
        return "not_queued"
    if source.acknowledged_at is None:
        return "queued_waiting_ack"
    return "queued"


def _ack_bucket(source: MarketOutcomeFreshnessRecheckReadinessSource) -> str:
    if source.acknowledged_at is None:
        return "missing_ack"
    return "acknowledged"


def _report_status(rows: tuple[MarketOutcomeFreshnessRecheckReadinessRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "ready"


def _report_reason_codes(
    rows: tuple[MarketOutcomeFreshnessRecheckReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason
        for reason in REASON_CODES
        if reason != EMPTY_REASON
        and reason != READY_REASON
        and any(reason in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (READY_REASON,)


def _category_rollups(
    rows: tuple[MarketOutcomeFreshnessRecheckReadinessRow, ...],
) -> tuple[tuple[str, Decimal, Decimal, Decimal, Decimal], ...]:
    category_ids = tuple(sorted({row.category_id for row in rows}))
    rollups: list[tuple[str, Decimal, Decimal, Decimal, Decimal]] = []
    for category_id in category_ids:
        category_rows = tuple(row for row in rows if row.category_id == category_id)
        rollups.append(
            (
                category_id,
                _count(len(category_rows)),
                _count(sum(1 for row in category_rows if row.status == "ready")),
                _count(sum(1 for row in category_rows if row.status == "watch")),
                _count(sum(1 for row in category_rows if row.status == "blocked")),
            ),
        )
    return tuple(rollups)


def _row_sort_key(row: MarketOutcomeFreshnessRecheckReadinessRow) -> tuple[int, int, str, str]:
    return (
        STATUS_WEIGHT[row.status],
        min(REASON_WEIGHT[reason] for reason in row.reason_codes),
        row.category_id,
        row.market_id,
    )


def _max_age(values: Any) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO_RATIO
    return max(normalized)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO_RATIO
    return (numerator / denominator).quantize(RATIO_QUANTUM)


def _age_delta(age_seconds: Decimal, threshold_seconds: Decimal) -> Decimal:
    if age_seconds <= threshold_seconds:
        return ZERO_RATIO
    return _normalize_nonnegative_seconds("age_delta_seconds", age_seconds - threshold_seconds)


def _optional_age_seconds(value: datetime | None, generated_at: datetime) -> Decimal:
    if value is None:
        return ZERO_RATIO
    delta = generated_at - value
    seconds = (
        Decimal(delta.days * 86_400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return seconds.quantize(SECOND_QUANTUM)


def _normalize_sources(
    sources: list[MarketOutcomeFreshnessRecheckReadinessSource]
    | tuple[MarketOutcomeFreshnessRecheckReadinessSource, ...],
) -> tuple[MarketOutcomeFreshnessRecheckReadinessSource, ...]:
    if type(sources) not in (list, tuple):
        raise ValueError(
            "sources must be a list or tuple of MarketOutcomeFreshnessRecheckReadinessSource",
        )
    normalized = tuple(sources)
    seen_market_ids: set[str] = set()
    for source in normalized:
        if type(source) is not MarketOutcomeFreshnessRecheckReadinessSource:
            raise ValueError(
                "sources must contain MarketOutcomeFreshnessRecheckReadinessSource values",
            )
        if source.market_id in seen_market_ids:
            raise ValueError("market_id values must be unique")
        seen_market_ids.add(source.market_id)
        _require_hard_flags(source)
    return normalized


def _normalize_rows(
    rows: tuple[MarketOutcomeFreshnessRecheckReadinessRow, ...],
) -> tuple[MarketOutcomeFreshnessRecheckReadinessRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_market_ids: set[str] = set()
    for row in normalized:
        if type(row) is not MarketOutcomeFreshnessRecheckReadinessRow:
            raise ValueError(
                "rows must contain MarketOutcomeFreshnessRecheckReadinessRow values",
            )
        if row.market_id in seen_market_ids:
            raise ValueError("row market_id values must be unique")
        seen_market_ids.add(row.market_id)
        _require_hard_flags(row)
    return normalized


def _normalize_category_rollups(
    rollups: tuple[tuple[str, Decimal, Decimal, Decimal, Decimal], ...],
) -> tuple[tuple[str, Decimal, Decimal, Decimal, Decimal], ...]:
    if type(rollups) not in (list, tuple):
        raise ValueError("category_rollups must be a list or tuple")
    normalized: list[tuple[str, Decimal, Decimal, Decimal, Decimal]] = []
    seen_category_ids: set[str] = set()
    for rollup in tuple(rollups):
        if type(rollup) not in (list, tuple) or len(rollup) != 5:
            raise ValueError("category_rollups must contain five-value tuples")
        category_id, market_count, ready_count, watch_count, blocked_count = rollup
        _require_canonical_string("category_id", category_id)
        if category_id in seen_category_ids:
            raise ValueError("category_rollup category_id values must be unique")
        seen_category_ids.add(category_id)
        normalized.append(
            (
                category_id,
                _normalize_count("category_market_count", market_count),
                _normalize_count("category_ready_count", ready_count),
                _normalize_count("category_watch_count", watch_count),
                _normalize_count("category_blocked_count", blocked_count),
            ),
        )
    return tuple(sorted(normalized, key=lambda rollup: rollup[0]))


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in normalized:
        _require_known_value("reason_code", reason_code, REASON_CODES)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(normalized, key=lambda reason_code: REASON_WEIGHT[reason_code]))


def _validate_row_consistency(row: MarketOutcomeFreshnessRecheckReadinessRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.reason_codes == (READY_REASON,) and (
        row.queue_bucket != "queued" or row.ack_bucket != "acknowledged"
    ):
        raise ValueError("ready rows must be queued and acknowledged")
    if row.queue_bucket == "not_queued" and row.queued_at is not None:
        raise ValueError("not_queued rows must not include queued_at")
    if row.ack_bucket == "missing_ack" and row.acknowledged_at is not None:
        raise ValueError("missing_ack rows must not include acknowledged_at")


def _validate_report_consistency(report: MarketOutcomeFreshnessRecheckReadinessReport) -> None:
    if report.market_count != _count(len(report.rows)):
        raise ValueError("market_count must match rows")
    expected_ready = _count(sum(1 for row in report.rows if row.status == "ready"))
    expected_watch = _count(sum(1 for row in report.rows if row.status == "watch"))
    expected_blocked = _count(sum(1 for row in report.rows if row.status == "blocked"))
    if report.ready_count != expected_ready:
        raise ValueError("ready_count must match rows")
    if report.watch_count != expected_watch:
        raise ValueError("watch_count must match rows")
    if report.blocked_count != expected_blocked:
        raise ValueError("blocked_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.category_rollups != _category_rollups(report.rows):
        raise ValueError("category_rollups must match rows")


def _validate_optional_not_after(
    field_name: str,
    value: datetime | None,
    generated_at: datetime,
) -> None:
    if value is not None and value > generated_at:
        raise ValueError(f"{field_name} must be <= generated_at")


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(SECOND_QUANTUM)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value


def _count(value: int) -> Decimal:
    return Decimal(value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < ZERO or value > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
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


def _require_known_value(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _json_ready_no_floats(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_no_floats(asdict(value))
    if isinstance(value, dict):
        return {key: _json_ready_no_floats(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready_no_floats(item) for item in value]
    if isinstance(value, list):
        return [_json_ready_no_floats(item) for item in value]
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("report payload must contain only JSON-safe scalar values")


__all__ = (
    "DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_READINESS_CONFIG_VERSION",
    "MarketOutcomeFreshnessRecheckReadinessConfig",
    "MarketOutcomeFreshnessRecheckReadinessReport",
    "MarketOutcomeFreshnessRecheckReadinessRow",
    "MarketOutcomeFreshnessRecheckReadinessSource",
    "build_market_outcome_freshness_recheck_readiness_report",
    "market_outcome_freshness_recheck_readiness_payload",
)
