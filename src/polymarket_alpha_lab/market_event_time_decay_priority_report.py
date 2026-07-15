"""Pure in-memory time-decay urgency report for probability events."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from json import dumps
from typing import Any


DEFAULT_MARKET_EVENT_TIME_DECAY_PRIORITY_REPORT_CONFIG_VERSION = (
    "market-event-time-decay-priority-report-v0"
)

ZERO = Decimal("0")
ONE = Decimal("1.000000")
SECOND_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")

SETTLEMENT_RISK_BANDS = ("low", "medium", "high")
URGENCY_BANDS = ("blocked", "urgent", "watch", "low")
REPORT_STATUSES = ("empty", "blocked", "urgent", "watch", "low")
STATUS_WEIGHT = {"blocked": 0, "urgent": 1, "watch": 2, "low": 3}

EMPTY_REASON = "time_decay_priority_report_empty"
READY_REASON = "time_decay_priority_ready"
TEAM_MEMORY_NOT_READY_REASON = "team_memory_not_ready"
RESOLUTION_URGENT_REASON = "resolution_window_urgent"
RESOLUTION_WATCH_REASON = "resolution_window_watch"
SOURCE_STALE_REASON = "source_freshness_stale"
EDGE_MATERIAL_REASON = "edge_to_threshold_material"
LIQUIDITY_THIN_REASON = "liquidity_depth_thin"
SETTLEMENT_MEDIUM_REASON = "settlement_risk_medium"
SETTLEMENT_HIGH_REASON = "settlement_risk_high"
MANUAL_REVIEW_REASON = "manual_review_pending"

REASON_CODES = (
    EMPTY_REASON,
    TEAM_MEMORY_NOT_READY_REASON,
    RESOLUTION_URGENT_REASON,
    RESOLUTION_WATCH_REASON,
    SOURCE_STALE_REASON,
    EDGE_MATERIAL_REASON,
    LIQUIDITY_THIN_REASON,
    SETTLEMENT_HIGH_REASON,
    SETTLEMENT_MEDIUM_REASON,
    MANUAL_REVIEW_REASON,
    READY_REASON,
)
REASON_WEIGHT = {reason: index for index, reason in enumerate(REASON_CODES)}

UNSAFE_TERMS = (
    "auth",
    "authorization",
    "wallet",
    "account",
    "broker",
    "order",
    "submit",
    "cancel",
    "replace",
    "sign",
    "trade",
    "trading",
    "live",
    "recommend",
    "advice",
    "private_key",
    "api_key",
    "secret",
    "bearer",
    "password",
    "network",
    "request",
    "database",
    "db",
    "sqlite",
    "postgres",
    "mysql",
    "redis",
    "env",
    "environment",
    "dotenv",
    "file",
    "path",
    "persist",
    "persistence",
    "write",
    "condition_id",
    "token_id",
    "market_id",
    "slug",
    "question",
    "url",
    "uri",
    "endpoint",
    "clob",
    "polymarket.com",
)


@dataclass(frozen=True)
class MarketEventTimeDecayPriorityReportConfig:
    urgent_resolution_seconds: Decimal = Decimal("3600.000000")
    watch_resolution_seconds: Decimal = Decimal("86400.000000")
    stale_source_age_seconds: Decimal = Decimal("1800.000000")
    thin_liquidity_depth_usdc: Decimal = Decimal("5000.000000")
    must_review_floor_seconds: Decimal = Decimal("300.000000")
    config_version: str = DEFAULT_MARKET_EVENT_TIME_DECAY_PRIORITY_REPORT_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _reject_unsafe_string("config_version", self.config_version)
        for field_name in (
            "urgent_resolution_seconds",
            "watch_resolution_seconds",
            "stale_source_age_seconds",
            "thin_liquidity_depth_usdc",
            "must_review_floor_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.urgent_resolution_seconds > self.watch_resolution_seconds:
            raise ValueError("urgent_resolution_seconds must be <= watch_resolution_seconds")
        if self.must_review_floor_seconds > self.urgent_resolution_seconds:
            raise ValueError("must_review_floor_seconds must be <= urgent_resolution_seconds")
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketEventTimeDecayPriorityReportInput:
    event_ref: str
    time_to_resolution_seconds: Decimal
    source_freshness_age_seconds: Decimal
    edge_to_threshold_probability: Decimal
    liquidity_depth_usdc: Decimal
    settlement_risk_band: str
    manual_review_pending: bool
    team_memory_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_ref("event_ref", self.event_ref)
        for field_name in (
            "time_to_resolution_seconds",
            "source_freshness_age_seconds",
            "liquidity_depth_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_to_threshold_probability",
            _normalize_ratio("edge_to_threshold_probability", self.edge_to_threshold_probability),
        )
        _require_known_value("settlement_risk_band", self.settlement_risk_band, SETTLEMENT_RISK_BANDS)
        _require_bool("manual_review_pending", self.manual_review_pending)
        _require_bool("team_memory_ready", self.team_memory_ready)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketEventTimeDecayPriorityReportRow:
    event_ref: str
    time_to_resolution_seconds: Decimal
    source_freshness_age_seconds: Decimal
    edge_to_threshold_probability: Decimal
    liquidity_depth_usdc: Decimal
    settlement_risk_band: str
    manual_review_pending: bool
    team_memory_ready: bool
    urgency_score: Decimal
    urgency_band: str
    must_review_before_seconds: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_ref("event_ref", self.event_ref)
        for field_name in (
            "time_to_resolution_seconds",
            "source_freshness_age_seconds",
            "liquidity_depth_usdc",
            "must_review_before_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("edge_to_threshold_probability", "urgency_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_known_value("settlement_risk_band", self.settlement_risk_band, SETTLEMENT_RISK_BANDS)
        _require_bool("manual_review_pending", self.manual_review_pending)
        _require_bool("team_memory_ready", self.team_memory_ready)
        _require_known_value("urgency_band", self.urgency_band, URGENCY_BANDS)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(self.blocked_reason_codes, allow_empty=True),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(self.attention_reason_codes, allow_empty=True),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketEventTimeDecayPriorityReport:
    config_version: str
    event_count: Decimal
    urgent_count: Decimal
    watch_count: Decimal
    low_count: Decimal
    blocked_count: Decimal
    ready_count: Decimal
    ready_ratio: Decimal
    max_urgency_score: Decimal
    average_urgency_score: Decimal
    min_must_review_before_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketEventTimeDecayPriorityReportRow, ...]
    digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _reject_unsafe_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "urgent_count",
            "watch_count",
            "low_count",
            "blocked_count",
            "ready_count",
        ):
            object.__setattr__(self, field_name, _normalize_count(field_name, getattr(self, field_name)))
        for field_name in ("ready_ratio", "max_urgency_score", "average_urgency_score"):
            object.__setattr__(self, field_name, _normalize_ratio(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "min_must_review_before_seconds",
            _normalize_nonnegative_decimal(
                "min_must_review_before_seconds",
                self.min_must_review_before_seconds,
            ),
        )
        _require_known_value("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        if self.digest == "":
            object.__setattr__(self, "digest", _digest_for_report(self))
        else:
            _require_digest(self.digest)
            if self.digest != _digest_for_report(self):
                raise ValueError("digest must match public payload")


def build_market_event_time_decay_priority_report(
    inputs: list[MarketEventTimeDecayPriorityReportInput]
    | tuple[MarketEventTimeDecayPriorityReportInput, ...],
    *,
    config: MarketEventTimeDecayPriorityReportConfig,
) -> MarketEventTimeDecayPriorityReport:
    if type(config) is not MarketEventTimeDecayPriorityReportConfig:
        raise ValueError("config must be a MarketEventTimeDecayPriorityReportConfig")
    _require_hard_flags(config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(value, config=config) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    event_count = _count(len(rows))
    urgent_count = _count(sum(1 for row in rows if row.urgency_band == "urgent"))
    watch_count = _count(sum(1 for row in rows if row.urgency_band == "watch"))
    low_count = _count(sum(1 for row in rows if row.urgency_band == "low"))
    blocked_count = _count(sum(1 for row in rows if row.urgency_band == "blocked"))
    ready_count = _count(sum(1 for row in rows if not row.blocked_reason_codes))
    return MarketEventTimeDecayPriorityReport(
        config_version=config.config_version,
        event_count=event_count,
        urgent_count=urgent_count,
        watch_count=watch_count,
        low_count=low_count,
        blocked_count=blocked_count,
        ready_count=ready_count,
        ready_ratio=_ratio(ready_count, event_count),
        max_urgency_score=_max_urgency_score(rows),
        average_urgency_score=_average_urgency_score(rows),
        min_must_review_before_seconds=_min_must_review_before_seconds(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_event_time_decay_priority_report_payload(
    report: MarketEventTimeDecayPriorityReport,
) -> dict[str, Any]:
    if type(report) is not MarketEventTimeDecayPriorityReport:
        raise ValueError("report must be a MarketEventTimeDecayPriorityReport")
    _require_hard_flags(report)
    if report.digest != _digest_for_report(report):
        raise ValueError("digest must match public payload")
    payload = _json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def market_event_time_decay_priority_report_digest(
    report: MarketEventTimeDecayPriorityReport,
) -> str:
    if type(report) is not MarketEventTimeDecayPriorityReport:
        raise ValueError("report must be a MarketEventTimeDecayPriorityReport")
    _require_hard_flags(report)
    return _digest_for_report(report)


def _row_from_input(
    value: MarketEventTimeDecayPriorityReportInput,
    *,
    config: MarketEventTimeDecayPriorityReportConfig,
) -> MarketEventTimeDecayPriorityReportRow:
    blocked_reason_codes = _blocked_reason_codes(value)
    attention_reason_codes = _attention_reason_codes(value, config=config)
    urgency_score = _urgency_score(value, config=config)
    urgency_band = _urgency_band(
        value,
        urgency_score=urgency_score,
        blocked_reason_codes=blocked_reason_codes,
        config=config,
    )
    return MarketEventTimeDecayPriorityReportRow(
        event_ref=value.event_ref,
        time_to_resolution_seconds=value.time_to_resolution_seconds,
        source_freshness_age_seconds=value.source_freshness_age_seconds,
        edge_to_threshold_probability=value.edge_to_threshold_probability,
        liquidity_depth_usdc=value.liquidity_depth_usdc,
        settlement_risk_band=value.settlement_risk_band,
        manual_review_pending=value.manual_review_pending,
        team_memory_ready=value.team_memory_ready,
        urgency_score=urgency_score,
        urgency_band=urgency_band,
        must_review_before_seconds=_must_review_before_seconds(value, config=config),
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
    )


def _blocked_reason_codes(value: MarketEventTimeDecayPriorityReportInput) -> tuple[str, ...]:
    if value.team_memory_ready:
        return ()
    return (TEAM_MEMORY_NOT_READY_REASON,)


def _attention_reason_codes(
    value: MarketEventTimeDecayPriorityReportInput,
    *,
    config: MarketEventTimeDecayPriorityReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if value.time_to_resolution_seconds <= config.urgent_resolution_seconds:
        reasons.append(RESOLUTION_URGENT_REASON)
    elif value.time_to_resolution_seconds <= config.watch_resolution_seconds:
        reasons.append(RESOLUTION_WATCH_REASON)
    if value.team_memory_ready:
        if value.source_freshness_age_seconds >= config.stale_source_age_seconds:
            reasons.append(SOURCE_STALE_REASON)
        if value.edge_to_threshold_probability >= Decimal("0.050000"):
            reasons.append(EDGE_MATERIAL_REASON)
        if value.liquidity_depth_usdc <= config.thin_liquidity_depth_usdc:
            reasons.append(LIQUIDITY_THIN_REASON)
    if value.settlement_risk_band == "high":
        reasons.append(SETTLEMENT_HIGH_REASON)
    elif value.settlement_risk_band == "medium":
        reasons.append(SETTLEMENT_MEDIUM_REASON)
    if value.manual_review_pending:
        reasons.append(MANUAL_REVIEW_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_reason_codes(tuple(reasons), allow_empty=False)


def _urgency_score(
    value: MarketEventTimeDecayPriorityReportInput,
    *,
    config: MarketEventTimeDecayPriorityReportConfig,
) -> Decimal:
    score = (
        _inverse_pressure(value.time_to_resolution_seconds, config.watch_resolution_seconds)
        * Decimal("0.350000")
        + _capped_ratio(value.source_freshness_age_seconds, config.stale_source_age_seconds)
        * Decimal("0.200000")
        + value.edge_to_threshold_probability
        * Decimal("1.500000")
        + _inverse_pressure(value.liquidity_depth_usdc, config.thin_liquidity_depth_usdc)
        * Decimal("0.100000")
        + _settlement_risk_score(value.settlement_risk_band)
        * Decimal("0.150000")
        + (Decimal("0.050000") if value.manual_review_pending else ZERO)
    )
    return _normalize_ratio("urgency_score", min(score, ONE))


def _urgency_band(
    value: MarketEventTimeDecayPriorityReportInput,
    *,
    urgency_score: Decimal,
    blocked_reason_codes: tuple[str, ...],
    config: MarketEventTimeDecayPriorityReportConfig,
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if (
        urgency_score >= Decimal("0.650000")
        or value.time_to_resolution_seconds <= config.urgent_resolution_seconds
    ):
        return "urgent"
    if (
        urgency_score >= Decimal("0.300000")
        or value.time_to_resolution_seconds <= config.watch_resolution_seconds
    ):
        return "watch"
    return "low"


def _must_review_before_seconds(
    value: MarketEventTimeDecayPriorityReportInput,
    *,
    config: MarketEventTimeDecayPriorityReportConfig,
) -> Decimal:
    if value.time_to_resolution_seconds <= config.urgent_resolution_seconds:
        return config.must_review_floor_seconds
    if value.time_to_resolution_seconds <= config.watch_resolution_seconds:
        return _normalize_nonnegative_decimal(
            "must_review_before_seconds",
            value.time_to_resolution_seconds / Decimal("2"),
        )
    return config.watch_resolution_seconds


def _inverse_pressure(value: Decimal, scale: Decimal) -> Decimal:
    if value >= scale:
        return ZERO
    return _normalize_ratio("inverse_pressure", (scale - value) / scale)


def _capped_ratio(value: Decimal, scale: Decimal) -> Decimal:
    if value >= scale:
        return ONE
    return _normalize_ratio("capped_ratio", value / scale)


def _settlement_risk_score(value: str) -> Decimal:
    if value == "high":
        return ONE
    if value == "medium":
        return Decimal("0.500000")
    return ZERO


def _normalize_inputs(
    inputs: list[MarketEventTimeDecayPriorityReportInput]
    | tuple[MarketEventTimeDecayPriorityReportInput, ...],
) -> tuple[MarketEventTimeDecayPriorityReportInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen_event_refs: set[str] = set()
    for value in normalized:
        if type(value) is not MarketEventTimeDecayPriorityReportInput:
            raise ValueError("inputs must contain MarketEventTimeDecayPriorityReportInput values")
        if value.event_ref in seen_event_refs:
            raise ValueError("event_ref values must be unique")
        seen_event_refs.add(value.event_ref)
        _require_hard_flags(value)
    return normalized


def _normalize_rows(
    rows: tuple[MarketEventTimeDecayPriorityReportRow, ...],
) -> tuple[MarketEventTimeDecayPriorityReportRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_event_refs: set[str] = set()
    for row in normalized:
        if type(row) is not MarketEventTimeDecayPriorityReportRow:
            raise ValueError("rows must contain MarketEventTimeDecayPriorityReportRow values")
        if row.event_ref in seen_event_refs:
            raise ValueError("row event_ref values must be unique")
        seen_event_refs.add(row.event_ref)
        _require_hard_flags(row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _row_sort_key(row: MarketEventTimeDecayPriorityReportRow) -> tuple[int, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.urgency_band],
        -row.urgency_score,
        row.must_review_before_seconds,
        row.event_ref,
    )


def _report_status(rows: tuple[MarketEventTimeDecayPriorityReportRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.urgency_band == "blocked" for row in rows):
        return "blocked"
    if any(row.urgency_band == "urgent" for row in rows):
        return "urgent"
    if any(row.urgency_band == "watch" for row in rows):
        return "watch"
    return "low"


def _report_reason_codes(rows: tuple[MarketEventTimeDecayPriorityReportRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.blocked_reason_codes)
        observed.update(row.attention_reason_codes)
    return tuple(reason for reason in REASON_CODES if reason in observed)


def _max_urgency_score(rows: tuple[MarketEventTimeDecayPriorityReportRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.urgency_score for row in rows)


def _average_urgency_score(rows: tuple[MarketEventTimeDecayPriorityReportRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(sum((row.urgency_score for row in rows), ZERO), _count(len(rows)))


def _min_must_review_before_seconds(rows: tuple[MarketEventTimeDecayPriorityReportRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.must_review_before_seconds for row in rows)


def _validate_row_consistency(row: MarketEventTimeDecayPriorityReportRow) -> None:
    if row.blocked_reason_codes and row.urgency_band != "blocked":
        raise ValueError("blocked rows must use blocked urgency_band")
    if row.urgency_band == "blocked" and not row.blocked_reason_codes:
        raise ValueError("blocked urgency_band must include blocked_reason_codes")
    if not row.blocked_reason_codes and not row.team_memory_ready:
        raise ValueError("team_memory_ready must match blocked_reason_codes")


def _validate_report_consistency(report: MarketEventTimeDecayPriorityReport) -> None:
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.urgent_count != _count(sum(1 for row in report.rows if row.urgency_band == "urgent")):
        raise ValueError("urgent_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.urgency_band == "watch")):
        raise ValueError("watch_count must match rows")
    if report.low_count != _count(sum(1 for row in report.rows if row.urgency_band == "low")):
        raise ValueError("low_count must match rows")
    if report.blocked_count != _count(sum(1 for row in report.rows if row.urgency_band == "blocked")):
        raise ValueError("blocked_count must match rows")
    ready_count = _count(sum(1 for row in report.rows if not row.blocked_reason_codes))
    if report.ready_count != ready_count:
        raise ValueError("ready_count must match rows")
    if report.ready_ratio != _ratio(ready_count, report.event_count):
        raise ValueError("ready_ratio must match rows")
    if report.max_urgency_score != _max_urgency_score(report.rows):
        raise ValueError("max_urgency_score must match rows")
    if report.average_urgency_score != _average_urgency_score(report.rows):
        raise ValueError("average_urgency_score must match rows")
    if report.min_must_review_before_seconds != _min_must_review_before_seconds(report.rows):
        raise ValueError("min_must_review_before_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    return (numerator / denominator).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(RATIO_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(SECOND_QUANTUM)


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not allow_empty and not normalized:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in normalized:
        _require_known_value("reason_code", reason_code, REASON_CODES)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(normalized, key=lambda reason_code: REASON_WEIGHT[reason_code]))


def _require_public_ref(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _contains_url(value):
        raise ValueError(f"{field_name} must not contain URLs")
    _reject_unsafe_string(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _reject_unsafe_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if _contains_url(value):
        raise ValueError(f"{field_name} must not contain URLs")
    if any(term in lowered for term in UNSAFE_TERMS):
        raise ValueError(f"{field_name} must not expose unsafe terms")


def _contains_url(value: str) -> bool:
    lowered = value.lower()
    return "://" in lowered or lowered.startswith("www.") or "polymarket.com" in lowered


def _require_known_value(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _digest_for_report(report: MarketEventTimeDecayPriorityReport) -> str:
    payload = _json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload = dict(payload)
    payload["digest"] = ""
    encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_digest(value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError("digest must be a sha256 hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError("digest must be a sha256 hex string")


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
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("report payload must contain only JSON-safe scalar values")


__all__ = (
    "DEFAULT_MARKET_EVENT_TIME_DECAY_PRIORITY_REPORT_CONFIG_VERSION",
    "MarketEventTimeDecayPriorityReport",
    "MarketEventTimeDecayPriorityReportConfig",
    "MarketEventTimeDecayPriorityReportInput",
    "MarketEventTimeDecayPriorityReportRow",
    "build_market_event_time_decay_priority_report",
    "market_event_time_decay_priority_report_digest",
    "market_event_time_decay_priority_report_payload",
)
