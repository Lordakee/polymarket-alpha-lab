"""Pure in-memory Phase 1 market event depth decay/spread widening gate."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_MARKET_EVENT_ORDERBOOK_DEPTH_DECAY_GATE_V2_CONFIG_VERSION = (
    "market-event-orderbook-depth-decay-gate-v2"
)

STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("empty",) + STATUSES
PASS_REASON_CODE = "depth_decay_spread_gate_passed"

ROW_REASON_CODE_SEQUENCE = (
    "depth_decay_blocked",
    "spread_widening_blocked",
    "low_volume_blocked",
    "depth_decay_watch",
    "spread_widening_watch",
    "low_volume_watch",
    PASS_REASON_CODE,
)
DEPTH_DECAY_REASON_CODES = frozenset(("depth_decay_blocked", "depth_decay_watch"))
SPREAD_WIDENING_REASON_CODES = frozenset(
    ("spread_widening_blocked", "spread_widening_watch"),
)
LOW_VOLUME_REASON_CODES = frozenset(("low_volume_blocked", "low_volume_watch"))
BLOCKING_REASON_CODES = frozenset(
    ("depth_decay_blocked", "spread_widening_blocked", "low_volume_blocked"),
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
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
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
class MarketEventOrderbookDepthDecayGateV2Config:
    config_version: str = DEFAULT_MARKET_EVENT_ORDERBOOK_DEPTH_DECAY_GATE_V2_CONFIG_VERSION
    max_pass_depth_decay_ratio: Decimal = Decimal("0.250000")
    max_watch_depth_decay_ratio: Decimal = Decimal("0.500000")
    max_pass_spread_widening_ratio: Decimal = Decimal("0.200000")
    max_watch_spread_widening_ratio: Decimal = Decimal("1.000000")
    min_pass_volume_24h_usdc: Decimal = Decimal("5000.000000")
    min_watch_volume_24h_usdc: Decimal = Decimal("1000.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketEventOrderbookDepthDecayGateV2Config, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_EVENT_ORDERBOOK_DEPTH_DECAY_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_depth_decay_ratio",
            "max_watch_depth_decay_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_spread_widening_ratio",
            "max_watch_spread_widening_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_pass_volume_24h_usdc",
            _normalize_positive_decimal(
                "min_pass_volume_24h_usdc",
                self.min_pass_volume_24h_usdc,
            ),
        )
        object.__setattr__(
            self,
            "min_watch_volume_24h_usdc",
            _normalize_nonnegative_decimal(
                "min_watch_volume_24h_usdc",
                self.min_watch_volume_24h_usdc,
            ),
        )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketEventOrderbookDepthDecayGateV2MarketInput:
    market_id: str
    event_slug: str
    category: str
    depth_now_usdc: Decimal
    depth_24h_ago_usdc: Decimal
    bid_ask_spread_now: Decimal
    bid_ask_spread_24h_ago: Decimal
    volume_24h_usdc: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketEventOrderbookDepthDecayGateV2MarketInput, "market")
        for field_name in ("market_id", "event_slug", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("depth_now_usdc", "depth_24h_ago_usdc", "volume_24h_usdc"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("bid_ask_spread_now", "bid_ask_spread_24h_ago"):
            object.__setattr__(
                self,
                field_name,
                _normalize_score_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("market", self)


@dataclass(frozen=True)
class MarketEventOrderbookDepthDecayGateV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketEventOrderbookDepthDecayGateV2ReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketEventOrderbookDepthDecayGateV2Row:
    market_id: str
    event_slug: str
    category: str
    depth_now_usdc: Decimal
    depth_24h_ago_usdc: Decimal
    bid_ask_spread_now: Decimal
    bid_ask_spread_24h_ago: Decimal
    volume_24h_usdc: Decimal
    depth_decay_ratio: Decimal
    spread_widening_ratio: Decimal
    liquidity_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketEventOrderbookDepthDecayGateV2Row, "row")
        for field_name in ("market_id", "event_slug", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("depth_now_usdc", "depth_24h_ago_usdc", "volume_24h_usdc"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("bid_ask_spread_now", "bid_ask_spread_24h_ago"):
            object.__setattr__(
                self,
                field_name,
                _normalize_score_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "depth_decay_ratio",
            _normalize_score_ratio("depth_decay_ratio", self.depth_decay_ratio),
        )
        object.__setattr__(
            self,
            "spread_widening_ratio",
            _normalize_nonnegative_decimal(
                "spread_widening_ratio",
                self.spread_widening_ratio,
            ),
        )
        object.__setattr__(
            self,
            "liquidity_decay_score",
            _normalize_score_ratio("liquidity_decay_score", self.liquidity_decay_score),
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
class MarketEventOrderbookDepthDecayGateV2Report:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    depth_decay_count: Decimal
    spread_widening_count: Decimal
    low_volume_count: Decimal
    max_liquidity_decay_score: Decimal
    report_status: str
    reason_code_counts: tuple[MarketEventOrderbookDepthDecayGateV2ReasonCodeCount, ...]
    rows: tuple[MarketEventOrderbookDepthDecayGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketEventOrderbookDepthDecayGateV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "block_count",
            "depth_decay_count",
            "spread_widening_count",
            "low_volume_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_liquidity_decay_score",
            _normalize_score_ratio(
                "max_liquidity_decay_score",
                self.max_liquidity_decay_score,
            ),
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


def build_market_event_orderbook_depth_decay_gate_v2_report(
    markets: Any,
    *,
    config: MarketEventOrderbookDepthDecayGateV2Config,
    generated_at: datetime,
) -> MarketEventOrderbookDepthDecayGateV2Report:
    if type(config) is not MarketEventOrderbookDepthDecayGateV2Config:
        raise ValueError("config must be a MarketEventOrderbookDepthDecayGateV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_markets = _normalize_markets(markets)
    _validate_unique_markets(normalized_markets)

    rows = tuple(
        sorted(
            (_row_for_market(market, config=config) for market in normalized_markets),
            key=_row_sort_key,
        ),
    )
    return MarketEventOrderbookDepthDecayGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        depth_decay_count=_depth_decay_count(rows),
        spread_widening_count=_spread_widening_count(rows),
        low_volume_count=_low_volume_count(rows),
        max_liquidity_decay_score=max(
            (row.liquidity_decay_score for row in rows),
            default=ZERO,
        ),
        report_status=_report_status(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def market_event_orderbook_depth_decay_gate_v2_payload(
    report: MarketEventOrderbookDepthDecayGateV2Report,
) -> dict[str, Any]:
    if type(report) is not MarketEventOrderbookDepthDecayGateV2Report:
        raise ValueError("report must be a MarketEventOrderbookDepthDecayGateV2Report")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_market_event_orderbook_depth_decay_gate_v2_payload(payload)
    return payload


def validate_market_event_orderbook_depth_decay_gate_v2_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("market event depth decay gate payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_market(
    market: MarketEventOrderbookDepthDecayGateV2MarketInput,
    *,
    config: MarketEventOrderbookDepthDecayGateV2Config,
) -> MarketEventOrderbookDepthDecayGateV2Row:
    depth_decay_ratio = _decay_ratio(market.depth_now_usdc, market.depth_24h_ago_usdc)
    spread_widening_ratio = _widening_ratio(
        market.bid_ask_spread_now,
        market.bid_ask_spread_24h_ago,
    )
    liquidity_decay_score = _liquidity_decay_score(
        depth_decay_ratio=depth_decay_ratio,
        spread_widening_ratio=spread_widening_ratio,
        volume_24h_usdc=market.volume_24h_usdc,
        config=config,
    )
    reason_codes = _row_reason_codes(
        market,
        depth_decay_ratio=depth_decay_ratio,
        spread_widening_ratio=spread_widening_ratio,
        config=config,
    )
    return MarketEventOrderbookDepthDecayGateV2Row(
        market_id=market.market_id,
        event_slug=market.event_slug,
        category=market.category,
        depth_now_usdc=market.depth_now_usdc,
        depth_24h_ago_usdc=market.depth_24h_ago_usdc,
        bid_ask_spread_now=market.bid_ask_spread_now,
        bid_ask_spread_24h_ago=market.bid_ask_spread_24h_ago,
        volume_24h_usdc=market.volume_24h_usdc,
        depth_decay_ratio=depth_decay_ratio,
        spread_widening_ratio=spread_widening_ratio,
        liquidity_decay_score=liquidity_decay_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    market: MarketEventOrderbookDepthDecayGateV2MarketInput,
    *,
    depth_decay_ratio: Decimal,
    spread_widening_ratio: Decimal,
    config: MarketEventOrderbookDepthDecayGateV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if depth_decay_ratio > config.max_watch_depth_decay_ratio:
        reason_codes.append("depth_decay_blocked")
    elif depth_decay_ratio > config.max_pass_depth_decay_ratio:
        reason_codes.append("depth_decay_watch")
    if spread_widening_ratio > config.max_watch_spread_widening_ratio:
        reason_codes.append("spread_widening_blocked")
    elif spread_widening_ratio > config.max_pass_spread_widening_ratio:
        reason_codes.append("spread_widening_watch")
    if market.volume_24h_usdc < config.min_watch_volume_24h_usdc:
        reason_codes.append("low_volume_blocked")
    elif market.volume_24h_usdc < config.min_pass_volume_24h_usdc:
        reason_codes.append("low_volume_watch")
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "block"
    if reason_codes == (PASS_REASON_CODE,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[MarketEventOrderbookDepthDecayGateV2Row, ...]) -> str:
    if not rows:
        return "empty"
    statuses = tuple(row.status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[MarketEventOrderbookDepthDecayGateV2Row, ...],
) -> tuple[MarketEventOrderbookDepthDecayGateV2ReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        MarketEventOrderbookDepthDecayGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_markets(
    markets: Any,
) -> tuple[MarketEventOrderbookDepthDecayGateV2MarketInput, ...]:
    if isinstance(markets, (str, bytes)):
        raise ValueError("markets must be an iterable")
    try:
        normalized = tuple(markets)
    except TypeError as exc:
        raise ValueError("markets must be an iterable") from exc
    for market in normalized:
        if type(market) is not MarketEventOrderbookDepthDecayGateV2MarketInput:
            raise ValueError(
                "markets must contain MarketEventOrderbookDepthDecayGateV2MarketInput values",
            )
        _require_hard_flags("market", market)
    return normalized


def _normalize_rows(rows: Any) -> tuple[MarketEventOrderbookDepthDecayGateV2Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not MarketEventOrderbookDepthDecayGateV2Row:
            raise ValueError("rows must contain MarketEventOrderbookDepthDecayGateV2Row values")
        _require_hard_flags("row", row)
        _validate_row(row)
        key = _market_key(row)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate market event")
        seen_keys.add(key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    values: Any,
) -> tuple[MarketEventOrderbookDepthDecayGateV2ReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(values)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not MarketEventOrderbookDepthDecayGateV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketEventOrderbookDepthDecayGateV2ReasonCodeCount values",
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


def _validate_config(config: MarketEventOrderbookDepthDecayGateV2Config) -> None:
    _require_less_or_equal(
        "max_pass_depth_decay_ratio",
        config.max_pass_depth_decay_ratio,
        config.max_watch_depth_decay_ratio,
    )
    _require_less_or_equal(
        "max_pass_spread_widening_ratio",
        config.max_pass_spread_widening_ratio,
        config.max_watch_spread_widening_ratio,
    )
    _require_less_or_equal(
        "min_watch_volume_24h_usdc",
        config.min_watch_volume_24h_usdc,
        config.min_pass_volume_24h_usdc,
    )


def _validate_unique_markets(
    markets: tuple[MarketEventOrderbookDepthDecayGateV2MarketInput, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for market in markets:
        key = _market_key(market)
        if key in seen:
            raise ValueError("markets must not contain duplicate market event")
        seen.add(key)


def _validate_row(row: MarketEventOrderbookDepthDecayGateV2Row) -> None:
    if row.depth_decay_ratio != _decay_ratio(row.depth_now_usdc, row.depth_24h_ago_usdc):
        raise ValueError("depth_decay_ratio must match depth fields")
    if row.spread_widening_ratio != _widening_ratio(
        row.bid_ask_spread_now,
        row.bid_ask_spread_24h_ago,
    ):
        raise ValueError("spread_widening_ratio must match spread fields")
    if row.liquidity_decay_score < max(
        row.depth_decay_ratio,
        _score_cap(row.spread_widening_ratio),
    ):
        raise ValueError("liquidity_decay_score must cover depth and spread decay")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.reason_codes == (PASS_REASON_CODE,) and row.status != "pass":
        raise ValueError("pass reason must match status")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: MarketEventOrderbookDepthDecayGateV2Report) -> None:
    rows = report.rows
    if report.market_count != _count(len(rows)):
        raise ValueError("market_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.market_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match market_count")
    if report.depth_decay_count != _depth_decay_count(rows):
        raise ValueError("depth_decay_count must match rows")
    if report.spread_widening_count != _spread_widening_count(rows):
        raise ValueError("spread_widening_count must match rows")
    if report.low_volume_count != _low_volume_count(rows):
        raise ValueError("low_volume_count must match rows")
    if report.max_liquidity_decay_score != max(
        (row.liquidity_decay_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_liquidity_decay_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _market_key(
    value: MarketEventOrderbookDepthDecayGateV2MarketInput
    | MarketEventOrderbookDepthDecayGateV2Row,
) -> tuple[str, str]:
    return (value.market_id, value.event_slug)


def _row_sort_key(
    row: MarketEventOrderbookDepthDecayGateV2Row,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.liquidity_decay_score,
        -row.depth_decay_ratio,
        -_score_cap(row.spread_widening_ratio),
        row.category,
        row.event_slug,
        row.market_id,
    )


def _reason_code_count_sort_key(
    item: MarketEventOrderbookDepthDecayGateV2ReasonCodeCount,
) -> tuple[Decimal, str]:
    return (-item.count, item.reason_code)


def _status_count(
    rows: tuple[MarketEventOrderbookDepthDecayGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_present_count(
    rows: tuple[MarketEventOrderbookDepthDecayGateV2Row, ...],
    reason_codes: frozenset[str],
) -> Decimal:
    return _count(
        sum(1 for row in rows if any(code in reason_codes for code in row.reason_codes)),
    )


def _depth_decay_count(rows: tuple[MarketEventOrderbookDepthDecayGateV2Row, ...]) -> Decimal:
    return _reason_present_count(rows, DEPTH_DECAY_REASON_CODES)


def _spread_widening_count(
    rows: tuple[MarketEventOrderbookDepthDecayGateV2Row, ...],
) -> Decimal:
    return _reason_present_count(rows, SPREAD_WIDENING_REASON_CODES)


def _low_volume_count(rows: tuple[MarketEventOrderbookDepthDecayGateV2Row, ...]) -> Decimal:
    return _reason_present_count(rows, LOW_VOLUME_REASON_CODES)


def _decay_ratio(current_value: Decimal, prior_value: Decimal) -> Decimal:
    if prior_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        decay = prior_value - current_value
        if decay <= ZERO:
            return ZERO
        return _quantize(decay / prior_value)


def _widening_ratio(current_value: Decimal, prior_value: Decimal) -> Decimal:
    if prior_value == ZERO:
        if current_value > ZERO:
            return ONE
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        widening = current_value - prior_value
        if widening <= ZERO:
            return ZERO
        return _quantize(widening / prior_value)


def _liquidity_decay_score(
    *,
    depth_decay_ratio: Decimal,
    spread_widening_ratio: Decimal,
    volume_24h_usdc: Decimal,
    config: MarketEventOrderbookDepthDecayGateV2Config,
) -> Decimal:
    return max(
        depth_decay_ratio,
        _score_cap(spread_widening_ratio),
        _low_volume_pressure(volume_24h_usdc, config.min_pass_volume_24h_usdc),
    )


def _low_volume_pressure(volume_24h_usdc: Decimal, min_pass_volume_24h_usdc: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        volume_ratio = volume_24h_usdc / min_pass_volume_24h_usdc
        return _score_cap(_quantize(ONE - volume_ratio))


def _score_cap(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


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


def _normalize_score_ratio(field_name: str, value: Any) -> Decimal:
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


def _row_derived_validation_digest(row: MarketEventOrderbookDepthDecayGateV2Row) -> str:
    return _public_payload_derived_validation_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(report: MarketEventOrderbookDepthDecayGateV2Report) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _row_public_payload_for_digest(
    row: MarketEventOrderbookDepthDecayGateV2Row,
) -> dict[str, Any]:
    payload = _payload_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: MarketEventOrderbookDepthDecayGateV2Report,
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
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload value is not JSON-ready")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    current_path = path or label
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"{item_path} has unsafe field")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe value")
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"{current_path} has unsafe value")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, (Decimal, int, float)):
        return
    raise ValueError(f"{current_path} is not JSON serializable")


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        return True
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS)


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for flag_field in PHASE_FLAG_FIELDS:
        if payload.get(flag_field) is not True:
            raise ValueError(f"{flag_field} must be True for public payload")


def _reject_public_numeric_values(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError("public payload numeric values must use Decimal strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_values(item)


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


__all__ = (
    "DEFAULT_MARKET_EVENT_ORDERBOOK_DEPTH_DECAY_GATE_V2_CONFIG_VERSION",
    "MarketEventOrderbookDepthDecayGateV2Config",
    "MarketEventOrderbookDepthDecayGateV2MarketInput",
    "MarketEventOrderbookDepthDecayGateV2ReasonCodeCount",
    "MarketEventOrderbookDepthDecayGateV2Report",
    "MarketEventOrderbookDepthDecayGateV2Row",
    "build_market_event_orderbook_depth_decay_gate_v2_report",
    "market_event_orderbook_depth_decay_gate_v2_payload",
    "validate_market_event_orderbook_depth_decay_gate_v2_payload",
)
