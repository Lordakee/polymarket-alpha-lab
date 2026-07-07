"""Phase 1 paper-only liquidity cost and slippage surface report."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Iterable


CONFIG_VERSION = "market-event-liquidity-cost-slippage-surface-v2"
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_EMPTY = "empty"
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_PASS = "liquidity_cost_slippage_pass"
REASON_DEPTH_WATCH = "liquidity_depth_usage_watch"
REASON_DEPTH_BLOCK = "liquidity_depth_usage_block"
REASON_SPREAD_WATCH = "liquidity_wide_spread_watch"
REASON_SPREAD_BLOCK = "liquidity_wide_spread_block"
REASON_COST_WATCH = "liquidity_high_cost_watch"
REASON_COST_BLOCK = "liquidity_high_cost_block"

_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_TEXT_FRAGMENTS = (
    "auth",
    "credential",
    "mnemonic",
    "private",
    "secret",
    "token",
    "trade",
    "wallet",
    "webhook",
)


@dataclass(frozen=True)
class MarketEventLiquidityCostSlippageSurfaceV2Config:
    config_version: str = CONFIG_VERSION
    depth_usage_watch_threshold: Decimal = Decimal("0.250000")
    depth_usage_block_threshold: Decimal = Decimal("0.600000")
    wide_spread_watch_threshold: Decimal = Decimal("0.030000")
    wide_spread_block_threshold: Decimal = Decimal("0.070000")
    high_cost_watch_threshold: Decimal = Decimal("0.025000")
    high_cost_block_threshold: Decimal = Decimal("0.080000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketEventLiquidityCostSlippageSurfaceV2Config:
            raise TypeError(
                "MarketEventLiquidityCostSlippageSurfaceV2Config does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketEventLiquidityCostSlippageSurfaceV2Config:
            raise ValueError(
                "config must be exactly MarketEventLiquidityCostSlippageSurfaceV2Config",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "depth_usage_watch_threshold",
            "depth_usage_block_threshold",
            "wide_spread_watch_threshold",
            "wide_spread_block_threshold",
            "high_cost_watch_threshold",
            "high_cost_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ordered_thresholds(
            "depth_usage",
            self.depth_usage_watch_threshold,
            self.depth_usage_block_threshold,
        )
        _require_ordered_thresholds(
            "wide_spread",
            self.wide_spread_watch_threshold,
            self.wide_spread_block_threshold,
        )
        _require_ordered_thresholds(
            "high_cost",
            self.high_cost_watch_threshold,
            self.high_cost_block_threshold,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketEventLiquidityCostSlippageSurfaceV2Input:
    market_id: str
    event_slug: str
    category: str
    notional_usdc: Decimal
    orderbook_depth_usdc: Decimal
    bid_ask_spread: Decimal
    taker_fee_rate: Decimal
    volatility_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketEventLiquidityCostSlippageSurfaceV2Input:
            raise TypeError(
                "MarketEventLiquidityCostSlippageSurfaceV2Input does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketEventLiquidityCostSlippageSurfaceV2Input:
            raise ValueError(
                "input must be exactly MarketEventLiquidityCostSlippageSurfaceV2Input",
            )
        for field_name in ("market_id", "event_slug", "category"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "notional_usdc",
            "orderbook_depth_usdc",
            "bid_ask_spread",
            "taker_fee_rate",
            "volatility_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("bid_ask_spread", "taker_fee_rate", "volatility_score"):
            _require_rate(field_name, getattr(self, field_name))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class MarketEventLiquidityCostSlippageSurfaceV2Row:
    market_id: str
    event_slug: str
    category: str
    notional_usdc: Decimal
    orderbook_depth_usdc: Decimal
    bid_ask_spread: Decimal
    taker_fee_rate: Decimal
    volatility_score: Decimal
    depth_usage_ratio: Decimal
    estimated_slippage_rate: Decimal
    total_cost_rate: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketEventLiquidityCostSlippageSurfaceV2Row:
            raise TypeError(
                "MarketEventLiquidityCostSlippageSurfaceV2Row does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketEventLiquidityCostSlippageSurfaceV2Row:
            raise ValueError(
                "row must be exactly MarketEventLiquidityCostSlippageSurfaceV2Row",
            )
        for field_name in ("market_id", "event_slug", "category"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "notional_usdc",
            "orderbook_depth_usdc",
            "bid_ask_spread",
            "taker_fee_rate",
            "volatility_score",
            "depth_usage_ratio",
            "estimated_slippage_rate",
            "total_cost_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("bid_ask_spread", "taker_fee_rate", "volatility_score"):
            _require_rate(field_name, getattr(self, field_name))
        _require_status("status", self.status, allow_empty=False)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketEventLiquidityCostSlippageSurfaceV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketEventLiquidityCostSlippageSurfaceV2ReasonCodeCount:
            raise TypeError(
                "MarketEventLiquidityCostSlippageSurfaceV2ReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketEventLiquidityCostSlippageSurfaceV2ReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketEventLiquidityCostSlippageSurfaceV2ReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_nonnegative_decimal("row_ratio", self.row_ratio),
        )
        _require_rate("row_ratio", self.row_ratio)
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketEventLiquidityCostSlippageSurfaceV2Report:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_depth_usage_count: Decimal
    wide_spread_count: Decimal
    high_cost_count: Decimal
    max_total_cost_rate: Decimal
    report_status: str
    rows: tuple[MarketEventLiquidityCostSlippageSurfaceV2Row, ...]
    reason_code_counts: tuple[MarketEventLiquidityCostSlippageSurfaceV2ReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    depth_usage_watch_threshold: Decimal = Decimal("0.250000")
    depth_usage_block_threshold: Decimal = Decimal("0.600000")
    wide_spread_watch_threshold: Decimal = Decimal("0.030000")
    wide_spread_block_threshold: Decimal = Decimal("0.070000")
    high_cost_watch_threshold: Decimal = Decimal("0.025000")
    high_cost_block_threshold: Decimal = Decimal("0.080000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketEventLiquidityCostSlippageSurfaceV2Report:
            raise TypeError(
                "MarketEventLiquidityCostSlippageSurfaceV2Report does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketEventLiquidityCostSlippageSurfaceV2Report:
            raise ValueError(
                "report must be exactly MarketEventLiquidityCostSlippageSurfaceV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_depth_usage_count",
            "wide_spread_count",
            "high_cost_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_total_cost_rate",
            "depth_usage_watch_threshold",
            "depth_usage_block_threshold",
            "wide_spread_watch_threshold",
            "wide_spread_block_threshold",
            "high_cost_watch_threshold",
            "high_cost_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status, allow_empty=True)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            _validate_report_consistency(self)
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_validation_digest(self),
            )
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
            _validate_report_consistency(self)
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_payload(
            "market event liquidity cost slippage surface report",
            _json_ready(self),
            allow_json_containers=True,
        )


def build_market_event_liquidity_cost_slippage_surface_v2_report(
    events: Iterable[object],
    *,
    config: MarketEventLiquidityCostSlippageSurfaceV2Config,
    generated_at: datetime,
) -> MarketEventLiquidityCostSlippageSurfaceV2Report:
    if type(config) is not MarketEventLiquidityCostSlippageSurfaceV2Config:
        raise ValueError(
            "config must be a MarketEventLiquidityCostSlippageSurfaceV2Config",
        )
    _require_hard_flags("config", config)
    normalized_events = _normalize_inputs(events)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in normalized_events),
            key=_row_sort_key,
        ),
    )
    market_count = _decimal_count(len(rows))
    pass_count = _decimal_count(_status_count(rows, STATUS_PASS))
    watch_count = _decimal_count(_status_count(rows, STATUS_WATCH))
    block_count = _decimal_count(_status_count(rows, STATUS_BLOCK))
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    return MarketEventLiquidityCostSlippageSurfaceV2Report(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        market_count=market_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        high_depth_usage_count=_decimal_count(
            sum(
                1
                for row in rows
                if row.depth_usage_ratio >= config.depth_usage_watch_threshold
            ),
        ),
        wide_spread_count=_decimal_count(
            sum(1 for row in rows if row.bid_ask_spread >= config.wide_spread_watch_threshold),
        ),
        high_cost_count=_decimal_count(
            sum(1 for row in rows if row.total_cost_rate >= config.high_cost_watch_threshold),
        ),
        max_total_cost_rate=_maximum((row.total_cost_rate for row in rows), ZERO),
        report_status=_report_status(rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
        depth_usage_watch_threshold=config.depth_usage_watch_threshold,
        depth_usage_block_threshold=config.depth_usage_block_threshold,
        wide_spread_watch_threshold=config.wide_spread_watch_threshold,
        wide_spread_block_threshold=config.wide_spread_block_threshold,
        high_cost_watch_threshold=config.high_cost_watch_threshold,
        high_cost_block_threshold=config.high_cost_block_threshold,
    )


def market_event_liquidity_cost_slippage_surface_v2_payload(
    report: MarketEventLiquidityCostSlippageSurfaceV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketEventLiquidityCostSlippageSurfaceV2Report:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        if report.derived_validation_digest != _report_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a MarketEventLiquidityCostSlippageSurfaceV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload(
        "market event liquidity cost slippage surface payload",
        payload,
        allow_json_containers=True,
    )
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_input(
    item: MarketEventLiquidityCostSlippageSurfaceV2Input,
    *,
    config: MarketEventLiquidityCostSlippageSurfaceV2Config,
) -> MarketEventLiquidityCostSlippageSurfaceV2Row:
    depth_usage_ratio = _depth_usage_ratio(item.notional_usdc, item.orderbook_depth_usdc)
    estimated_slippage_rate = _quantize(depth_usage_ratio * item.volatility_score)
    total_cost_rate = _quantize(
        (item.bid_ask_spread / Decimal("2"))
        + item.taker_fee_rate
        + estimated_slippage_rate,
    )
    reason_codes = _row_reason_codes(
        depth_usage_ratio=depth_usage_ratio,
        bid_ask_spread=item.bid_ask_spread,
        total_cost_rate=total_cost_rate,
        config=config,
    )
    return MarketEventLiquidityCostSlippageSurfaceV2Row(
        market_id=item.market_id,
        event_slug=item.event_slug,
        category=item.category,
        notional_usdc=item.notional_usdc,
        orderbook_depth_usdc=item.orderbook_depth_usdc,
        bid_ask_spread=item.bid_ask_spread,
        taker_fee_rate=item.taker_fee_rate,
        volatility_score=item.volatility_score,
        depth_usage_ratio=depth_usage_ratio,
        estimated_slippage_rate=estimated_slippage_rate,
        total_cost_rate=total_cost_rate,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    depth_usage_ratio: Decimal,
    bid_ask_spread: Decimal,
    total_cost_rate: Decimal,
    config: MarketEventLiquidityCostSlippageSurfaceV2Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    if depth_usage_ratio >= config.depth_usage_block_threshold:
        codes.append(REASON_DEPTH_BLOCK)
    elif depth_usage_ratio >= config.depth_usage_watch_threshold:
        codes.append(REASON_DEPTH_WATCH)
    if bid_ask_spread >= config.wide_spread_block_threshold:
        codes.append(REASON_SPREAD_BLOCK)
    elif bid_ask_spread >= config.wide_spread_watch_threshold:
        codes.append(REASON_SPREAD_WATCH)
    if total_cost_rate >= config.high_cost_block_threshold:
        codes.append(REASON_COST_BLOCK)
    elif total_cost_rate >= config.high_cost_watch_threshold:
        codes.append(REASON_COST_WATCH)
    if not codes:
        codes.append(REASON_PASS)
    return tuple(sorted(codes))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return STATUS_BLOCK
    if any(code.endswith("_watch") for code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[MarketEventLiquidityCostSlippageSurfaceV2Row, ...],
) -> str:
    if not rows:
        return STATUS_EMPTY
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _depth_usage_ratio(notional_usdc: Decimal, orderbook_depth_usdc: Decimal) -> Decimal:
    if orderbook_depth_usdc == ZERO:
        if notional_usdc == ZERO:
            return ZERO
        return ONE
    return _quantize(notional_usdc / orderbook_depth_usdc)


def _normalize_inputs(
    events: Iterable[object],
) -> tuple[MarketEventLiquidityCostSlippageSurfaceV2Input, ...]:
    if isinstance(events, (str, bytes)):
        raise ValueError("events must be an iterable")
    try:
        values = tuple(events)
    except TypeError as exc:
        raise ValueError("events must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> MarketEventLiquidityCostSlippageSurfaceV2Input:
    if type(value) is MarketEventLiquidityCostSlippageSurfaceV2Input:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return MarketEventLiquidityCostSlippageSurfaceV2Input(
        market_id=_field_value(value, "market_id"),
        event_slug=_field_value(value, "event_slug"),
        category=_field_value(value, "category"),
        notional_usdc=_field_value(value, "notional_usdc"),
        orderbook_depth_usdc=_field_value(value, "orderbook_depth_usdc"),
        bid_ask_spread=_field_value(value, "bid_ask_spread"),
        taker_fee_rate=_field_value(value, "taker_fee_rate"),
        volatility_score=_field_value(value, "volatility_score"),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _field_value(value: object, field_name: str) -> object:
    if type(value) is dict:
        if field_name not in value:
            raise ValueError(f"{field_name} is required")
        return value[field_name]
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _reason_code_counts(
    rows: tuple[MarketEventLiquidityCostSlippageSurfaceV2Row, ...],
) -> tuple[MarketEventLiquidityCostSlippageSurfaceV2ReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = Decimal(len(rows))
    return tuple(
        MarketEventLiquidityCostSlippageSurfaceV2ReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
            row_ratio=_quantize(Decimal(counter[reason_code]) / row_count),
        )
        for reason_code in sorted(counter)
    )


def _status_count(
    rows: tuple[MarketEventLiquidityCostSlippageSurfaceV2Row, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(row: MarketEventLiquidityCostSlippageSurfaceV2Row) -> tuple[int, str, str, str]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[row.status],
        row.category,
        row.event_slug,
        row.market_id,
    )


def _normalize_rows(
    value: object,
) -> tuple[MarketEventLiquidityCostSlippageSurfaceV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    if not all(type(row) is MarketEventLiquidityCostSlippageSurfaceV2Row for row in rows):
        raise ValueError(
            "rows must contain MarketEventLiquidityCostSlippageSurfaceV2Row values",
        )
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketEventLiquidityCostSlippageSurfaceV2ReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    counts = tuple(value)
    if not all(
        type(item) is MarketEventLiquidityCostSlippageSurfaceV2ReasonCodeCount
        for item in counts
    ):
        raise ValueError(
            "reason_code_counts must contain "
            "MarketEventLiquidityCostSlippageSurfaceV2ReasonCodeCount values",
        )
    if counts != tuple(sorted(counts, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must be sorted")
    return counts


def _normalize_reason_codes(value: object, *, allow_empty: bool) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    codes = tuple(value)
    if not allow_empty and not codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    for code in codes:
        _require_canonical_string("reason_codes", code)
    normalized = tuple(sorted(codes))
    if normalized != codes:
        raise ValueError("reason_codes must be sorted")
    return normalized


def _validate_row_consistency(
    row: MarketEventLiquidityCostSlippageSurfaceV2Row,
) -> None:
    expected_depth_usage_ratio = _depth_usage_ratio(
        row.notional_usdc,
        row.orderbook_depth_usdc,
    )
    expected_estimated_slippage_rate = _quantize(
        row.depth_usage_ratio * row.volatility_score,
    )
    expected_total_cost_rate = _quantize(
        (row.bid_ask_spread / Decimal("2"))
        + row.taker_fee_rate
        + row.estimated_slippage_rate,
    )
    if row.depth_usage_ratio != expected_depth_usage_ratio:
        raise ValueError("depth_usage_ratio does not match inputs")
    if row.estimated_slippage_rate != expected_estimated_slippage_rate:
        raise ValueError("estimated_slippage_rate does not match inputs")
    if row.total_cost_rate != expected_total_cost_rate:
        raise ValueError("total_cost_rate does not match inputs")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status does not match reason_codes")


def _validate_report_consistency(
    report: MarketEventLiquidityCostSlippageSurfaceV2Report,
) -> None:
    rows = report.rows
    if report.market_count != _decimal_count(len(rows)):
        raise ValueError("market_count does not match rows")
    if report.pass_count != _decimal_count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _decimal_count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _decimal_count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count does not match rows")
    if report.high_depth_usage_count != _decimal_count(
        sum(
            1
            for row in rows
            if row.depth_usage_ratio >= report.depth_usage_watch_threshold
        ),
    ):
        raise ValueError("high_depth_usage_count does not match rows")
    if report.wide_spread_count != _decimal_count(
        sum(1 for row in rows if row.bid_ask_spread >= report.wide_spread_watch_threshold),
    ):
        raise ValueError("wide_spread_count does not match rows")
    if report.high_cost_count != _decimal_count(
        sum(1 for row in rows if row.total_cost_rate >= report.high_cost_watch_threshold),
    ):
        raise ValueError("high_cost_count does not match rows")
    if report.max_total_cost_rate != _maximum((row.total_cost_rate for row in rows), ZERO):
        raise ValueError("max_total_cost_rate does not match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status does not match rows")
    expected_reason_code_counts = _reason_code_counts(rows)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes do not match reason_code_counts")


def _report_validation_digest(report: MarketEventLiquidityCostSlippageSurfaceV2Report) -> str:
    digest_payload = _report_digest_payload(report)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _report_digest_payload(report: MarketEventLiquidityCostSlippageSurfaceV2Report) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in fields(report):
        if field.name == "derived_validation_digest":
            continue
        payload[field.name] = _json_ready(getattr(report, field.name))
    return payload


def _json_ready(value: Any) -> Any:
    if value is None or type(value) is bool:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("JSON value must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if value is None or type(value) is bool:
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{current_path} must not be a float")
    if type(value) is str:
        if value != value.strip():
            raise ValueError(f"{current_path} has unsafe value")
        lowered = value.lower()
        if "://" in lowered or "?" in lowered:
            raise ValueError(f"{current_path} has unsafe value")
        if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
            raise ValueError(f"{current_path} has unsafe value")
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                item_path,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in _UNSAFE_TEXT_FRAGMENTS):
                raise ValueError(f"{item_path} has unsafe field")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            item_path = f"{current_path}[{index}]"
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            item_path = f"{current_path}[{index}]"
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=allow_json_containers,
            )
        return
    raise ValueError(f"{current_path} is not JSON serializable")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _maximum(values: Iterable[Decimal], default: Decimal) -> Decimal:
    items = tuple(values)
    if not items:
        return default
    return _quantize(max(items))


def _require_rate(field_name: str, value: Decimal) -> None:
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_ordered_thresholds(label: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value > block_value:
        raise ValueError(f"{label} watch threshold must not exceed block threshold")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")


def _require_status(field_name: str, value: object, *, allow_empty: bool) -> None:
    allowed = {STATUS_PASS, STATUS_WATCH, STATUS_BLOCK}
    if allow_empty:
        allowed.add(STATUS_EMPTY)
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known status")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "MarketEventLiquidityCostSlippageSurfaceV2Config",
    "MarketEventLiquidityCostSlippageSurfaceV2Input",
    "MarketEventLiquidityCostSlippageSurfaceV2ReasonCodeCount",
    "MarketEventLiquidityCostSlippageSurfaceV2Report",
    "MarketEventLiquidityCostSlippageSurfaceV2Row",
    "build_market_event_liquidity_cost_slippage_surface_v2_report",
    "market_event_liquidity_cost_slippage_surface_v2_payload",
)
