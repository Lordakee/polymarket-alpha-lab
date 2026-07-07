"""Pure in-memory Phase 1 event probability volatility/liquidity gate."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_MARKET_EVENT_PROBABILITY_VOLATILITY_LIQUIDITY_GATE_V2_CONFIG_VERSION = (
    "market-event-probability-volatility-liquidity-gate-v2"
)

STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("empty",) + STATUSES
PASS_REASON_CODE = "event_probability_volatility_liquidity_gate_passed"

ROW_REASON_CODE_SEQUENCE = (
    "probability_volatility_blocked",
    "probability_volatility_watch",
    "wide_bid_ask_spread_blocked",
    "wide_bid_ask_spread_watch",
    "thin_depth_blocked",
    "thin_depth_watch",
    "low_volume_blocked",
    "low_volume_watch",
    "near_close_watch",
    PASS_REASON_CODE,
)
BLOCKING_REASON_CODES = frozenset(
    (
        "probability_volatility_blocked",
        "wide_bid_ask_spread_blocked",
        "thin_depth_blocked",
        "low_volume_blocked",
    ),
)
LOW_LIQUIDITY_REASON_CODES = frozenset(
    (
        "wide_bid_ask_spread_blocked",
        "wide_bid_ask_spread_watch",
        "thin_depth_blocked",
        "thin_depth_watch",
        "low_volume_blocked",
        "low_volume_watch",
    ),
)
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sig", "ning"),
        _join_parts("bu", "y"),
        _join_parts("sel", "l"),
        _join_parts("tra", "de"),
        _join_parts("api", "_", "key"),
        _join_parts("private", "_", "key"),
    ),
)


@dataclass(frozen=True)
class MarketEventProbabilityVolatilityLiquidityGateV2Config:
    config_version: str = (
        DEFAULT_MARKET_EVENT_PROBABILITY_VOLATILITY_LIQUIDITY_GATE_V2_CONFIG_VERSION
    )
    volatility_watch_threshold: Decimal = Decimal("0.080000")
    volatility_block_threshold: Decimal = Decimal("0.150000")
    short_horizon_volatility_multiplier: Decimal = Decimal("4.000000")
    max_pass_bid_ask_spread: Decimal = Decimal("0.030000")
    max_watch_bid_ask_spread: Decimal = Decimal("0.080000")
    min_pass_depth_usdc: Decimal = Decimal("1000.000000")
    min_watch_depth_usdc: Decimal = Decimal("250.000000")
    min_pass_volume_24h: Decimal = Decimal("5000.000000")
    min_watch_volume_24h: Decimal = Decimal("1000.000000")
    near_close_minutes: Decimal = Decimal("60.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketEventProbabilityVolatilityLiquidityGateV2Config,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_EVENT_PROBABILITY_VOLATILITY_LIQUIDITY_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "volatility_watch_threshold",
            "volatility_block_threshold",
            "max_pass_bid_ask_spread",
            "max_watch_bid_ask_spread",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "short_horizon_volatility_multiplier",
            "min_pass_depth_usdc",
            "min_pass_volume_24h",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_watch_depth_usdc",
            "min_watch_volume_24h",
            "near_close_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketEventProbabilityVolatilityLiquidityGateV2EventInput:
    market_id: str
    event_slug: str
    category: str
    probability_move_24h: Decimal
    probability_move_1h: Decimal
    bid_ask_spread: Decimal
    depth_usdc: Decimal
    volume_24h: Decimal
    minutes_to_close: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketEventProbabilityVolatilityLiquidityGateV2EventInput,
            "event",
        )
        for field_name in ("market_id", "event_slug", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "probability_move_24h",
            "probability_move_1h",
            "bid_ask_spread",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("depth_usdc", "volume_24h", "minutes_to_close"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("event", self)


@dataclass(frozen=True)
class MarketEventProbabilityVolatilityLiquidityGateV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketEventProbabilityVolatilityLiquidityGateV2ReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketEventProbabilityVolatilityLiquidityGateV2Row:
    market_id: str
    event_slug: str
    category: str
    probability_move_24h: Decimal
    probability_move_1h: Decimal
    bid_ask_spread: Decimal
    depth_usdc: Decimal
    volume_24h: Decimal
    minutes_to_close: Decimal
    volatility_score: Decimal
    liquidity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketEventProbabilityVolatilityLiquidityGateV2Row, "row")
        for field_name in ("market_id", "event_slug", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "probability_move_24h",
            "probability_move_1h",
            "bid_ask_spread",
            "volatility_score",
            "liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("depth_usdc", "volume_24h", "minutes_to_close"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)


@dataclass(frozen=True)
class MarketEventProbabilityVolatilityLiquidityGateV2Report:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_volatility_count: Decimal
    low_liquidity_count: Decimal
    near_close_count: Decimal
    max_volatility_score: Decimal
    min_liquidity_score: Decimal
    report_status: str
    reason_code_counts: tuple[
        MarketEventProbabilityVolatilityLiquidityGateV2ReasonCodeCount,
        ...,
    ]
    rows: tuple[MarketEventProbabilityVolatilityLiquidityGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketEventProbabilityVolatilityLiquidityGateV2Report,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_volatility_count",
            "low_liquidity_count",
            "near_close_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_volatility_score", "min_liquidity_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_market_event_probability_volatility_liquidity_gate_v2_report(
    events: Any,
    *,
    config: MarketEventProbabilityVolatilityLiquidityGateV2Config,
    generated_at: datetime,
) -> MarketEventProbabilityVolatilityLiquidityGateV2Report:
    if type(config) is not MarketEventProbabilityVolatilityLiquidityGateV2Config:
        raise ValueError(
            "config must be a MarketEventProbabilityVolatilityLiquidityGateV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_events = _normalize_events(events)
    _validate_unique_events(normalized_events)

    rows = tuple(
        sorted(
            (_row_for_event(event, config=config) for event in normalized_events),
            key=_row_sort_key,
        ),
    )

    return MarketEventProbabilityVolatilityLiquidityGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        high_volatility_count=_high_volatility_count(rows),
        low_liquidity_count=_low_liquidity_count(rows),
        near_close_count=_near_close_count(rows),
        max_volatility_score=max((row.volatility_score for row in rows), default=ZERO),
        min_liquidity_score=min((row.liquidity_score for row in rows), default=ZERO),
        report_status=_report_status(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def market_event_probability_volatility_liquidity_gate_v2_payload(
    report: MarketEventProbabilityVolatilityLiquidityGateV2Report,
) -> dict[str, Any]:
    if type(report) is not MarketEventProbabilityVolatilityLiquidityGateV2Report:
        raise ValueError(
            "report must be a MarketEventProbabilityVolatilityLiquidityGateV2Report",
        )
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_market_event_probability_volatility_liquidity_gate_v2_payload(payload)
    return payload


def validate_market_event_probability_volatility_liquidity_gate_v2_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(
        "market event probability volatility liquidity gate payload",
        payload,
    )
    _require_public_payload_flags(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_event(
    event: MarketEventProbabilityVolatilityLiquidityGateV2EventInput,
    *,
    config: MarketEventProbabilityVolatilityLiquidityGateV2Config,
) -> MarketEventProbabilityVolatilityLiquidityGateV2Row:
    volatility_score = _volatility_score(event, config=config)
    liquidity_score = _liquidity_score(event, config=config)
    reason_codes = _row_reason_codes(
        event,
        volatility_score=volatility_score,
        config=config,
    )
    return MarketEventProbabilityVolatilityLiquidityGateV2Row(
        market_id=event.market_id,
        event_slug=event.event_slug,
        category=event.category,
        probability_move_24h=event.probability_move_24h,
        probability_move_1h=event.probability_move_1h,
        bid_ask_spread=event.bid_ask_spread,
        depth_usdc=event.depth_usdc,
        volume_24h=event.volume_24h,
        minutes_to_close=event.minutes_to_close,
        volatility_score=volatility_score,
        liquidity_score=liquidity_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    event: MarketEventProbabilityVolatilityLiquidityGateV2EventInput,
    *,
    volatility_score: Decimal,
    config: MarketEventProbabilityVolatilityLiquidityGateV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if volatility_score >= config.volatility_block_threshold:
        reason_codes.append("probability_volatility_blocked")
    elif volatility_score >= config.volatility_watch_threshold:
        reason_codes.append("probability_volatility_watch")
    if event.bid_ask_spread > config.max_watch_bid_ask_spread:
        reason_codes.append("wide_bid_ask_spread_blocked")
    elif event.bid_ask_spread > config.max_pass_bid_ask_spread:
        reason_codes.append("wide_bid_ask_spread_watch")
    if event.depth_usdc < config.min_watch_depth_usdc:
        reason_codes.append("thin_depth_blocked")
    elif event.depth_usdc < config.min_pass_depth_usdc:
        reason_codes.append("thin_depth_watch")
    if event.volume_24h < config.min_watch_volume_24h:
        reason_codes.append("low_volume_blocked")
    elif event.volume_24h < config.min_pass_volume_24h:
        reason_codes.append("low_volume_watch")
    if event.minutes_to_close <= config.near_close_minutes:
        reason_codes.append("near_close_watch")
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _volatility_score(
    event: MarketEventProbabilityVolatilityLiquidityGateV2EventInput,
    *,
    config: MarketEventProbabilityVolatilityLiquidityGateV2Config,
) -> Decimal:
    short_horizon_score = _multiply_decimal(
        event.probability_move_1h,
        config.short_horizon_volatility_multiplier,
    )
    return max(event.probability_move_24h, min(short_horizon_score, ONE))


def _liquidity_score(
    event: MarketEventProbabilityVolatilityLiquidityGateV2EventInput,
    *,
    config: MarketEventProbabilityVolatilityLiquidityGateV2Config,
) -> Decimal:
    spread_quality = max(
        ZERO,
        _subtract_decimal(ONE, _ratio(event.bid_ask_spread, config.max_watch_bid_ask_spread)),
    )
    depth_quality = min(_ratio(event.depth_usdc, config.min_pass_depth_usdc), ONE)
    volume_quality = min(_ratio(event.volume_24h, config.min_pass_volume_24h), ONE)
    return min(spread_quality, depth_quality, volume_quality)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "block"
    if reason_codes == (PASS_REASON_CODE,):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[MarketEventProbabilityVolatilityLiquidityGateV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    statuses = tuple(row.status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[MarketEventProbabilityVolatilityLiquidityGateV2Row, ...],
) -> tuple[MarketEventProbabilityVolatilityLiquidityGateV2ReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        MarketEventProbabilityVolatilityLiquidityGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_events(
    events: Any,
) -> tuple[MarketEventProbabilityVolatilityLiquidityGateV2EventInput, ...]:
    if isinstance(events, (str, bytes)):
        raise ValueError("events must be an iterable")
    try:
        normalized = tuple(events)
    except TypeError as exc:
        raise ValueError("events must be an iterable") from exc
    for event in normalized:
        if type(event) is not MarketEventProbabilityVolatilityLiquidityGateV2EventInput:
            raise ValueError(
                "events must contain MarketEventProbabilityVolatilityLiquidityGateV2EventInput values",
            )
        _require_hard_flags("event", event)
    return normalized


def _normalize_rows(
    rows: Any,
) -> tuple[MarketEventProbabilityVolatilityLiquidityGateV2Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not MarketEventProbabilityVolatilityLiquidityGateV2Row:
            raise ValueError(
                "rows must contain MarketEventProbabilityVolatilityLiquidityGateV2Row values",
            )
        _require_hard_flags("row", row)
        _validate_row(row)
        key = _event_key(row)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate market event")
        seen_keys.add(key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    values: Any,
) -> tuple[MarketEventProbabilityVolatilityLiquidityGateV2ReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(values)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not MarketEventProbabilityVolatilityLiquidityGateV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketEventProbabilityVolatilityLiquidityGateV2ReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", value)
        if value.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate values")
        seen.add(value.reason_code)
    if normalized != tuple(sorted(normalized, key=_reason_code_count_sort_key)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _normalize_reason_codes(field_name: str, values: Any) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(values)
    seen: set[str] = set()
    for reason_code in normalized:
        _require_reason_code(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate values")
        seen.add(reason_code)
    expected = tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in seen
    )
    if normalized != expected:
        raise ValueError(f"{field_name} must use deterministic sorting")
    return normalized


def _validate_config(config: MarketEventProbabilityVolatilityLiquidityGateV2Config) -> None:
    _require_less_or_equal(
        "volatility_watch_threshold",
        config.volatility_watch_threshold,
        config.volatility_block_threshold,
    )
    _require_less_or_equal(
        "max_pass_bid_ask_spread",
        config.max_pass_bid_ask_spread,
        config.max_watch_bid_ask_spread,
    )
    _require_less_or_equal(
        "min_watch_depth_usdc",
        config.min_watch_depth_usdc,
        config.min_pass_depth_usdc,
    )
    _require_less_or_equal(
        "min_watch_volume_24h",
        config.min_watch_volume_24h,
        config.min_pass_volume_24h,
    )
    if config.max_watch_bid_ask_spread <= ZERO:
        raise ValueError("max_watch_bid_ask_spread must be positive")


def _validate_unique_events(
    events: tuple[MarketEventProbabilityVolatilityLiquidityGateV2EventInput, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for event in events:
        key = _event_key(event)
        if key in seen:
            raise ValueError("events must not contain duplicate market event")
        seen.add(key)


def _validate_row(row: MarketEventProbabilityVolatilityLiquidityGateV2Row) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.reason_codes == (PASS_REASON_CODE,) and row.status != "pass":
        raise ValueError("pass reason must match status")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: MarketEventProbabilityVolatilityLiquidityGateV2Report) -> None:
    rows = report.rows
    if report.event_count != _count(len(rows)):
        raise ValueError("event_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.event_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match event_count")
    if report.high_volatility_count != _high_volatility_count(rows):
        raise ValueError("high_volatility_count must match rows")
    if report.low_liquidity_count != _low_liquidity_count(rows):
        raise ValueError("low_liquidity_count must match rows")
    if report.near_close_count != _near_close_count(rows):
        raise ValueError("near_close_count must match rows")
    if report.max_volatility_score != max(
        (row.volatility_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_volatility_score must match rows")
    if report.min_liquidity_score != min(
        (row.liquidity_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_liquidity_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _event_key(
    value: MarketEventProbabilityVolatilityLiquidityGateV2EventInput
    | MarketEventProbabilityVolatilityLiquidityGateV2Row,
) -> tuple[str, str]:
    return (value.market_id, value.event_slug)


def _row_sort_key(
    row: MarketEventProbabilityVolatilityLiquidityGateV2Row,
) -> tuple[Decimal, Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.volatility_score,
        row.liquidity_score,
        row.category,
        row.event_slug,
        row.market_id,
    )


def _reason_code_count_sort_key(
    item: MarketEventProbabilityVolatilityLiquidityGateV2ReasonCodeCount,
) -> tuple[Decimal, str]:
    return (-item.count, item.reason_code)


def _status_count(
    rows: tuple[MarketEventProbabilityVolatilityLiquidityGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _high_volatility_count(
    rows: tuple[MarketEventProbabilityVolatilityLiquidityGateV2Row, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if "probability_volatility_blocked" in row.reason_codes
            or "probability_volatility_watch" in row.reason_codes
        ),
    )


def _low_liquidity_count(
    rows: tuple[MarketEventProbabilityVolatilityLiquidityGateV2Row, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason_code in LOW_LIQUIDITY_REASON_CODES for reason_code in row.reason_codes)
        ),
    )


def _near_close_count(
    rows: tuple[MarketEventProbabilityVolatilityLiquidityGateV2Row, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if "near_close_watch" in row.reason_codes))


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_count(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_ratio(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if value != normalized:
        raise ValueError(f"{field_name} must have at most six decimal places")
    return normalized


def _require_public_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_surface_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_reason_code(field_name: str, value: Any) -> None:
    _require_member(field_name, value, ROW_REASON_CODE_SEQUENCE)


def _require_member(field_name: str, value: Any, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_less_or_equal(field_name: str, left: Decimal, right: Decimal) -> None:
    if left > right:
        raise ValueError(f"{field_name} must not exceed paired threshold")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_sha256_digest(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _row_derived_validation_digest(
    row: MarketEventProbabilityVolatilityLiquidityGateV2Row,
) -> str:
    return _public_payload_derived_validation_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(
    report: MarketEventProbabilityVolatilityLiquidityGateV2Report,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _row_public_payload_for_digest(
    row: MarketEventProbabilityVolatilityLiquidityGateV2Row,
) -> dict[str, Any]:
    payload = _payload_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: MarketEventProbabilityVolatilityLiquidityGateV2Report,
) -> dict[str, Any]:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded_payload = json.dumps(
        digest_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{path or label} must use Decimal strings, not numeric values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS)


__all__ = (
    "DEFAULT_MARKET_EVENT_PROBABILITY_VOLATILITY_LIQUIDITY_GATE_V2_CONFIG_VERSION",
    "MarketEventProbabilityVolatilityLiquidityGateV2Config",
    "MarketEventProbabilityVolatilityLiquidityGateV2EventInput",
    "MarketEventProbabilityVolatilityLiquidityGateV2ReasonCodeCount",
    "MarketEventProbabilityVolatilityLiquidityGateV2Report",
    "MarketEventProbabilityVolatilityLiquidityGateV2Row",
    "build_market_event_probability_volatility_liquidity_gate_v2_report",
    "market_event_probability_volatility_liquidity_gate_v2_payload",
    "validate_market_event_probability_volatility_liquidity_gate_v2_payload",
)
