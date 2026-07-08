"""Pure report-only liquidity slippage watchlist reducer for manual research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "LIQUIDITY_SLIPPAGE_WATCHLIST_STATUSES",
    "DEFAULT_RESEARCH_STRATEGY_LIQUIDITY_SLIPPAGE_WATCHLIST_REPORT_CONFIG_VERSION",
    "ResearchStrategyLiquiditySlippageWatchlistConfig",
    "ResearchStrategyLiquiditySlippageWatchlistInput",
    "ResearchStrategyLiquiditySlippageWatchlistReasonCodeCount",
    "ResearchStrategyLiquiditySlippageWatchlistReport",
    "ResearchStrategyLiquiditySlippageWatchlistRow",
    "build_research_strategy_liquidity_slippage_watchlist_report",
    "research_strategy_liquidity_slippage_watchlist_report_digest",
    "research_strategy_liquidity_slippage_watchlist_report_payload",
)


LIQUIDITY_SLIPPAGE_WATCHLIST_STATUSES = ("pass", "watch", "block")
DEFAULT_RESEARCH_STRATEGY_LIQUIDITY_SLIPPAGE_WATCHLIST_REPORT_CONFIG_VERSION = (
    "research-strategy-liquidity-slippage-watchlist-report-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate" + "_" + "id",
    "condition" + "_" + "id",
    "market" + "_" + "id",
    "market" + "_" + "slug",
    "slug",
    "ques" + "tion",
    "source" + "_" + "url",
    "source" + "_" + "text",
    "dsn",
    "table",
    "token",
    "wall" + "et",
    "private" + "_" + "key",
    "au" + "th",
    "order",
    "trade",
    "buy",
    "sell",
    "position" + "_" + "amount",
    "siz" + "ing",
    "recommend" + "ation",
)
COMPONENT_REASON_PRIORITY = (
    "liquidity_slippage_watchlist_block",
    "liquidity_floor_block",
    "spread_width_block",
    "depth_concentration_block",
    "book_freshness_block",
    "stale_book_observation_block",
    "liquidity_floor_watch",
    "spread_width_watch",
    "depth_concentration_watch",
    "book_freshness_watch",
    "stale_book_observation_watch",
)


@dataclass(frozen=True)
class ResearchStrategyLiquiditySlippageWatchlistConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_LIQUIDITY_SLIPPAGE_WATCHLIST_REPORT_CONFIG_VERSION
    )
    min_pass_available_liquidity: Decimal = Decimal("500.000000")
    min_watch_available_liquidity: Decimal = Decimal("100.000000")
    max_pass_spread_width: Decimal = Decimal("0.020000")
    max_watch_spread_width: Decimal = Decimal("0.060000")
    max_pass_depth_concentration: Decimal = Decimal("0.350000")
    max_watch_depth_concentration: Decimal = Decimal("0.700000")
    max_pass_book_age_seconds: Decimal = Decimal("120.000000")
    max_watch_book_age_seconds: Decimal = Decimal("600.000000")
    max_pass_unchanged_book_seconds: Decimal = Decimal("180.000000")
    max_watch_unchanged_book_seconds: Decimal = Decimal("900.000000")
    liquidity_weight: Decimal = Decimal("0.250000")
    spread_weight: Decimal = Decimal("0.250000")
    depth_concentration_weight: Decimal = Decimal("0.200000")
    book_freshness_weight: Decimal = Decimal("0.150000")
    stale_book_weight: Decimal = Decimal("0.150000")
    pass_execution_quality_score: Decimal = Decimal("0.700000")
    watch_execution_quality_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyLiquiditySlippageWatchlistConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyLiquiditySlippageWatchlistConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_LIQUIDITY_SLIPPAGE_WATCHLIST_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "min_pass_available_liquidity",
            "min_watch_available_liquidity",
            "max_pass_book_age_seconds",
            "max_watch_book_age_seconds",
            "max_pass_unchanged_book_seconds",
            "max_watch_unchanged_book_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_spread_width",
            "max_watch_spread_width",
            "max_pass_depth_concentration",
            "max_watch_depth_concentration",
            "liquidity_weight",
            "spread_weight",
            "depth_concentration_weight",
            "book_freshness_weight",
            "stale_book_weight",
            "pass_execution_quality_score",
            "watch_execution_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_available_liquidity <= self.min_watch_available_liquidity:
            raise ValueError("min_pass_available_liquidity must exceed watch threshold")
        if self.max_pass_spread_width >= self.max_watch_spread_width:
            raise ValueError("max_pass_spread_width must be below watch threshold")
        if self.max_pass_depth_concentration >= self.max_watch_depth_concentration:
            raise ValueError("max_pass_depth_concentration must be below watch threshold")
        if self.max_pass_book_age_seconds >= self.max_watch_book_age_seconds:
            raise ValueError("max_pass_book_age_seconds must be below watch threshold")
        if self.max_pass_unchanged_book_seconds >= self.max_watch_unchanged_book_seconds:
            raise ValueError(
                "max_pass_unchanged_book_seconds must be below watch threshold",
            )
        if self.pass_execution_quality_score <= self.watch_execution_quality_score:
            raise ValueError("pass_execution_quality_score must exceed watch threshold")
        weight_sum = _quantize(
            self.liquidity_weight
            + self.spread_weight
            + self.depth_concentration_weight
            + self.book_freshness_weight
            + self.stale_book_weight,
        )
        if weight_sum != ONE:
            raise ValueError("execution quality weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyLiquiditySlippageWatchlistInput:
    input_key: str
    apparent_edge: Decimal
    best_bid_price: Decimal
    best_ask_price: Decimal
    available_liquidity: Decimal
    largest_level_liquidity: Decimal
    book_observed_at: datetime
    last_book_change_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyLiquiditySlippageWatchlistInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyLiquiditySlippageWatchlistInput,
            "input",
        )
        _require_public_label("input_key", self.input_key)
        for field_name in ("apparent_edge", "best_bid_price", "best_ask_price"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.best_ask_price <= self.best_bid_price:
            raise ValueError("best_ask_price must exceed best_bid_price")
        for field_name in ("available_liquidity", "largest_level_liquidity"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.largest_level_liquidity > self.available_liquidity:
            raise ValueError("largest_level_liquidity must not exceed available_liquidity")
        object.__setattr__(
            self,
            "book_observed_at",
            _as_utc("book_observed_at", self.book_observed_at),
        )
        object.__setattr__(
            self,
            "last_book_change_at",
            _as_utc("last_book_change_at", self.last_book_change_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyLiquiditySlippageWatchlistRow:
    watchlist_ref: str
    apparent_edge: Decimal
    best_bid_price: Decimal
    best_ask_price: Decimal
    spread_width: Decimal
    spread_score: Decimal
    available_liquidity: Decimal
    largest_level_liquidity: Decimal
    liquidity_score: Decimal
    depth_concentration_ratio: Decimal
    depth_concentration_score: Decimal
    book_observed_at: datetime
    book_age_seconds: Decimal
    book_freshness_score: Decimal
    last_book_change_at: datetime
    unchanged_book_seconds: Decimal
    stale_book_score: Decimal
    execution_quality_score: Decimal
    edge_fragility_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyLiquiditySlippageWatchlistRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyLiquiditySlippageWatchlistRow, "row")
        _require_public_label("watchlist_ref", self.watchlist_ref)
        object.__setattr__(
            self,
            "book_observed_at",
            _as_utc("book_observed_at", self.book_observed_at),
        )
        object.__setattr__(
            self,
            "last_book_change_at",
            _as_utc("last_book_change_at", self.last_book_change_at),
        )
        for field_name in (
            "apparent_edge",
            "best_bid_price",
            "best_ask_price",
            "spread_score",
            "liquidity_score",
            "depth_concentration_ratio",
            "depth_concentration_score",
            "book_freshness_score",
            "stale_book_score",
            "execution_quality_score",
            "edge_fragility_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.best_ask_price <= self.best_bid_price:
            raise ValueError("best_ask_price must exceed best_bid_price")
        for field_name in (
            "spread_width",
            "available_liquidity",
            "largest_level_liquidity",
            "book_age_seconds",
            "unchanged_book_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.largest_level_liquidity > self.available_liquidity:
            raise ValueError("largest_level_liquidity must not exceed available_liquidity")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchStrategyLiquiditySlippageWatchlistReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyLiquiditySlippageWatchlistReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyLiquiditySlippageWatchlistReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyLiquiditySlippageWatchlistReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_execution_quality_score: Decimal | None
    max_edge_fragility_score: Decimal
    min_available_liquidity: Decimal
    max_spread_width: Decimal
    max_depth_concentration_ratio: Decimal
    max_book_age_seconds: Decimal
    max_unchanged_book_seconds: Decimal
    status: str
    rows: tuple[ResearchStrategyLiquiditySlippageWatchlistRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyLiquiditySlippageWatchlistReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyLiquiditySlippageWatchlistReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyLiquiditySlippageWatchlistReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_execution_quality_score",
            _require_optional_ratio_decimal(
                "average_execution_quality_score",
                self.average_execution_quality_score,
            ),
        )
        for field_name in (
            "max_edge_fragility_score",
            "max_spread_width",
            "max_depth_concentration_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_available_liquidity",
            "max_book_age_seconds",
            "max_unchanged_book_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _derived_report_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_strategy_liquidity_slippage_watchlist_report(
    inputs: Iterable[object],
    *,
    config: ResearchStrategyLiquiditySlippageWatchlistConfig,
    generated_at: datetime,
) -> ResearchStrategyLiquiditySlippageWatchlistReport:
    if type(config) is not ResearchStrategyLiquiditySlippageWatchlistConfig:
        raise ValueError(
            "config must be a ResearchStrategyLiquiditySlippageWatchlistConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    for item in input_items:
        if item.book_observed_at > generated_at_utc:
            raise ValueError("book_observed_at must not be after generated_at")
        if item.last_book_change_at > generated_at_utc:
            raise ValueError("last_book_change_at must not be after generated_at")
    rows = tuple(
        _row_from_input(
            watchlist_ref=f"liquidity_slippage_watchlist_{index:03d}",
            item=item,
            config=config,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(sorted(input_items, key=_input_sort_key), start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchStrategyLiquiditySlippageWatchlistReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_execution_quality_score=_average_execution_quality_score(rows),
        max_edge_fragility_score=_max_or_zero(
            tuple(row.edge_fragility_score for row in rows),
        ),
        min_available_liquidity=_min_or_zero(
            tuple(row.available_liquidity for row in rows),
        ),
        max_spread_width=_max_or_zero(tuple(row.spread_width for row in rows)),
        max_depth_concentration_ratio=_max_or_zero(
            tuple(row.depth_concentration_ratio for row in rows),
        ),
        max_book_age_seconds=_max_or_zero(tuple(row.book_age_seconds for row in rows)),
        max_unchanged_book_seconds=_max_or_zero(
            tuple(row.unchanged_book_seconds for row in rows),
        ),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_liquidity_slippage_watchlist_report_payload(
    report: ResearchStrategyLiquiditySlippageWatchlistReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyLiquiditySlippageWatchlistReport:
        raise ValueError(
            "report must be a ResearchStrategyLiquiditySlippageWatchlistReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def research_strategy_liquidity_slippage_watchlist_report_digest(
    report: ResearchStrategyLiquiditySlippageWatchlistReport,
) -> str:
    if type(report) is not ResearchStrategyLiquiditySlippageWatchlistReport:
        raise ValueError(
            "report must be a ResearchStrategyLiquiditySlippageWatchlistReport",
        )
    _require_hard_flags("report", report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


def _row_from_input(
    *,
    watchlist_ref: str,
    item: ResearchStrategyLiquiditySlippageWatchlistInput,
    config: ResearchStrategyLiquiditySlippageWatchlistConfig,
    generated_at: datetime,
) -> ResearchStrategyLiquiditySlippageWatchlistRow:
    spread_width = _quantize(item.best_ask_price - item.best_bid_price)
    depth_concentration_ratio = _depth_concentration_ratio(
        item.available_liquidity,
        item.largest_level_liquidity,
    )
    book_age_seconds = _age_seconds(generated_at, item.book_observed_at)
    unchanged_book_seconds = _age_seconds(generated_at, item.last_book_change_at)
    liquidity_score = _liquidity_score(item.available_liquidity, config)
    spread_score = _inverse_ratio_score(spread_width, config.max_watch_spread_width)
    depth_concentration_score = _inverse_ratio_score(
        depth_concentration_ratio,
        config.max_watch_depth_concentration,
    )
    book_freshness_score = _inverse_ratio_score(
        book_age_seconds,
        config.max_watch_book_age_seconds,
    )
    stale_book_score = _inverse_ratio_score(
        unchanged_book_seconds,
        config.max_watch_unchanged_book_seconds,
    )
    execution_quality_score = _execution_quality_score(
        liquidity_score=liquidity_score,
        spread_score=spread_score,
        depth_concentration_score=depth_concentration_score,
        book_freshness_score=book_freshness_score,
        stale_book_score=stale_book_score,
        config=config,
    )
    edge_fragility_score = _edge_fragility_score(
        item.apparent_edge,
        execution_quality_score,
    )
    status = _row_status(
        available_liquidity=item.available_liquidity,
        spread_width=spread_width,
        depth_concentration_ratio=depth_concentration_ratio,
        book_age_seconds=book_age_seconds,
        unchanged_book_seconds=unchanged_book_seconds,
        execution_quality_score=execution_quality_score,
        config=config,
    )
    return ResearchStrategyLiquiditySlippageWatchlistRow(
        watchlist_ref=watchlist_ref,
        apparent_edge=item.apparent_edge,
        best_bid_price=item.best_bid_price,
        best_ask_price=item.best_ask_price,
        spread_width=spread_width,
        spread_score=spread_score,
        available_liquidity=item.available_liquidity,
        largest_level_liquidity=item.largest_level_liquidity,
        liquidity_score=liquidity_score,
        depth_concentration_ratio=depth_concentration_ratio,
        depth_concentration_score=depth_concentration_score,
        book_observed_at=item.book_observed_at,
        book_age_seconds=book_age_seconds,
        book_freshness_score=book_freshness_score,
        last_book_change_at=item.last_book_change_at,
        unchanged_book_seconds=unchanged_book_seconds,
        stale_book_score=stale_book_score,
        execution_quality_score=execution_quality_score,
        edge_fragility_score=edge_fragility_score,
        status=status,
        reason_codes=_row_reason_codes(
            item,
            available_liquidity=item.available_liquidity,
            spread_width=spread_width,
            depth_concentration_ratio=depth_concentration_ratio,
            book_age_seconds=book_age_seconds,
            unchanged_book_seconds=unchanged_book_seconds,
            status=status,
            config=config,
        ),
    )


def _liquidity_score(
    available_liquidity: Decimal,
    config: ResearchStrategyLiquiditySlippageWatchlistConfig,
) -> Decimal:
    return _quantize(min(ONE, available_liquidity / config.min_pass_available_liquidity))


def _depth_concentration_ratio(
    available_liquidity: Decimal,
    largest_level_liquidity: Decimal,
) -> Decimal:
    if available_liquidity <= ZERO:
        return ONE
    return _quantize(largest_level_liquidity / available_liquidity)


def _inverse_ratio_score(value: Decimal, zero_at: Decimal) -> Decimal:
    if zero_at <= ZERO:
        raise ValueError("zero_at must be positive")
    score = ONE - (value / zero_at)
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return _quantize(score)


def _execution_quality_score(
    *,
    liquidity_score: Decimal,
    spread_score: Decimal,
    depth_concentration_score: Decimal,
    book_freshness_score: Decimal,
    stale_book_score: Decimal,
    config: ResearchStrategyLiquiditySlippageWatchlistConfig,
) -> Decimal:
    return _quantize(
        liquidity_score * config.liquidity_weight
        + spread_score * config.spread_weight
        + depth_concentration_score * config.depth_concentration_weight
        + book_freshness_score * config.book_freshness_weight
        + stale_book_score * config.stale_book_weight,
    )


def _edge_fragility_score(apparent_edge: Decimal, execution_quality_score: Decimal) -> Decimal:
    return _quantize(apparent_edge * (ONE - execution_quality_score))


def _row_status(
    *,
    available_liquidity: Decimal,
    spread_width: Decimal,
    depth_concentration_ratio: Decimal,
    book_age_seconds: Decimal,
    unchanged_book_seconds: Decimal,
    execution_quality_score: Decimal,
    config: ResearchStrategyLiquiditySlippageWatchlistConfig,
) -> str:
    if (
        available_liquidity < config.min_watch_available_liquidity
        or spread_width > config.max_watch_spread_width
        or depth_concentration_ratio > config.max_watch_depth_concentration
        or book_age_seconds > config.max_watch_book_age_seconds
        or unchanged_book_seconds > config.max_watch_unchanged_book_seconds
        or execution_quality_score < config.watch_execution_quality_score
    ):
        return "block"
    if (
        available_liquidity < config.min_pass_available_liquidity
        or spread_width > config.max_pass_spread_width
        or depth_concentration_ratio > config.max_pass_depth_concentration
        or book_age_seconds > config.max_pass_book_age_seconds
        or unchanged_book_seconds > config.max_pass_unchanged_book_seconds
        or execution_quality_score < config.pass_execution_quality_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchStrategyLiquiditySlippageWatchlistInput,
    *,
    available_liquidity: Decimal,
    spread_width: Decimal,
    depth_concentration_ratio: Decimal,
    book_age_seconds: Decimal,
    unchanged_book_seconds: Decimal,
    status: str,
    config: ResearchStrategyLiquiditySlippageWatchlistConfig,
) -> tuple[str, ...]:
    codes = {
        f"liquidity_slippage_watchlist_{status}",
        _low_value_component_reason(
            prefix="liquidity_floor",
            value=available_liquidity,
            pass_threshold=config.min_pass_available_liquidity,
            block_threshold=config.min_watch_available_liquidity,
        ),
        _high_value_component_reason(
            prefix="spread_width",
            value=spread_width,
            pass_threshold=config.max_pass_spread_width,
            block_threshold=config.max_watch_spread_width,
        ),
        _high_value_component_reason(
            prefix="depth_concentration",
            value=depth_concentration_ratio,
            pass_threshold=config.max_pass_depth_concentration,
            block_threshold=config.max_watch_depth_concentration,
        ),
        _high_value_component_reason(
            prefix="book_freshness",
            value=book_age_seconds,
            pass_threshold=config.max_pass_book_age_seconds,
            block_threshold=config.max_watch_book_age_seconds,
        ),
        _high_value_component_reason(
            prefix="stale_book_observation",
            value=unchanged_book_seconds,
            pass_threshold=config.max_pass_unchanged_book_seconds,
            block_threshold=config.max_watch_unchanged_book_seconds,
        ),
    }
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _low_value_component_reason(
    *,
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value < block_threshold:
        return f"{prefix}_block"
    if value < pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _high_value_component_reason(
    *,
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value > block_threshold:
        return f"{prefix}_block"
    if value > pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchStrategyLiquiditySlippageWatchlistInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchStrategyLiquiditySlippageWatchlistInput:
            raise ValueError(
                "inputs must contain ResearchStrategyLiquiditySlippageWatchlistInput values",
            )
        _require_hard_flags("input", value)
    keys = tuple(value.input_key for value in values)
    if len(set(keys)) != len(keys):
        raise ValueError("input_key values must be unique")
    return values


def _normalize_rows(
    rows: tuple[ResearchStrategyLiquiditySlippageWatchlistRow, ...],
) -> tuple[ResearchStrategyLiquiditySlippageWatchlistRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyLiquiditySlippageWatchlistRow:
            raise ValueError(
                "rows must contain ResearchStrategyLiquiditySlippageWatchlistRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=lambda row: row.watchlist_ref)):
        raise ValueError("rows must be sorted by watchlist_ref")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyLiquiditySlippageWatchlistReasonCodeCount, ...],
) -> tuple[ResearchStrategyLiquiditySlippageWatchlistReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategyLiquiditySlippageWatchlistReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", count)
    if counts != tuple(sorted(counts, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _summary_status(
    rows: tuple[ResearchStrategyLiquiditySlippageWatchlistRow, ...],
) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchStrategyLiquiditySlippageWatchlistRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_liquidity_slippage_watchlist_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("liquidity_slippage_watchlist_pass",)
    row_codes = {code for row in rows for code in row.reason_codes}
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("liquidity_slippage_watchlist_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("liquidity_slippage_watchlist_watch")
    codes.extend(
        code
        for code in COMPONENT_REASON_PRIORITY
        if code in row_codes and code not in codes
    )
    return tuple(codes)


def _reason_code_counts(
    rows: tuple[ResearchStrategyLiquiditySlippageWatchlistRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyLiquiditySlippageWatchlistReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyLiquiditySlippageWatchlistReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchStrategyLiquiditySlippageWatchlistReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(_decimal_count(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_execution_quality_score(
    rows: tuple[ResearchStrategyLiquiditySlippageWatchlistRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.execution_quality_score for row in rows), ZERO)
        / _decimal_count(len(rows)),
    )


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _min_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _status_count(
    rows: tuple[ResearchStrategyLiquiditySlippageWatchlistRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _input_sort_key(
    value: ResearchStrategyLiquiditySlippageWatchlistInput,
) -> tuple[str, datetime]:
    return value.input_key, value.book_observed_at


def _validate_row(row: ResearchStrategyLiquiditySlippageWatchlistRow) -> None:
    if row.spread_width != _quantize(row.best_ask_price - row.best_bid_price):
        raise ValueError("spread_width must match price gap")
    if row.depth_concentration_ratio != _depth_concentration_ratio(
        row.available_liquidity,
        row.largest_level_liquidity,
    ):
        raise ValueError("depth_concentration_ratio must match depth fields")
    expected_edge_fragility = _edge_fragility_score(
        row.apparent_edge,
        row.execution_quality_score,
    )
    if row.edge_fragility_score != expected_edge_fragility:
        raise ValueError("edge_fragility_score must match apparent edge")
    if f"liquidity_slippage_watchlist_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_report(report: ResearchStrategyLiquiditySlippageWatchlistReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_execution_quality_score != _average_execution_quality_score(
        report.rows,
    ):
        raise ValueError("average_execution_quality_score must match rows")
    if report.max_edge_fragility_score != _max_or_zero(
        tuple(row.edge_fragility_score for row in report.rows),
    ):
        raise ValueError("max_edge_fragility_score must match rows")
    if report.min_available_liquidity != _min_or_zero(
        tuple(row.available_liquidity for row in report.rows),
    ):
        raise ValueError("min_available_liquidity must match rows")
    if report.max_spread_width != _max_or_zero(
        tuple(row.spread_width for row in report.rows),
    ):
        raise ValueError("max_spread_width must match rows")
    if report.max_depth_concentration_ratio != _max_or_zero(
        tuple(row.depth_concentration_ratio for row in report.rows),
    ):
        raise ValueError("max_depth_concentration_ratio must match rows")
    if report.max_book_age_seconds != _max_or_zero(
        tuple(row.book_age_seconds for row in report.rows),
    ):
        raise ValueError("max_book_age_seconds must match rows")
    if report.max_unchanged_book_seconds != _max_or_zero(
        tuple(row.unchanged_book_seconds for row in report.rows),
    ):
        raise ValueError("max_unchanged_book_seconds must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _derived_report_digest(
    report: ResearchStrategyLiquiditySlippageWatchlistReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError("payload contains unsafe public key")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, str) and _has_unsafe_public_fragment(value):
        raise ValueError("payload contains unsafe public value")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in LIQUIDITY_SLIPPAGE_WATCHLIST_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{name} has unsafe public text")
    return value


def _require_reason_code(name: str, value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a reason code")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{name} has unsafe public text")
    return value


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        reason_code = _require_reason_code(name, value)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must not be empty")
    return tuple(normalized)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return _quantize(+value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be finite") from exc


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value > ONE:
        raise ValueError(f"{name} must be at most one")
    return decimal_value


def _require_optional_ratio_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(name, value)


def _require_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal_value


def _require_positive_whole_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal_value


def _require_hex_digest(name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a SHA-256 hex digest") from exc
    return value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)
