"""Pure report-only scorecard for public liquidity exit-window review."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "LIQUIDITY_EXIT_WINDOW_SCORECARD_STATUSES",
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_WINDOW_SCORECARD_REPORT_CONFIG_VERSION",
    "ResearchMarketLiquidityExitWindowScorecardConfig",
    "ResearchMarketLiquidityExitWindowScorecardInput",
    "ResearchMarketLiquidityExitWindowScorecardReasonCodeCount",
    "ResearchMarketLiquidityExitWindowScorecardReport",
    "ResearchMarketLiquidityExitWindowScorecardRow",
    "build_research_market_liquidity_exit_window_scorecard_report",
    "research_market_liquidity_exit_window_scorecard_report_digest",
    "research_market_liquidity_exit_window_scorecard_report_payload",
)


DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_WINDOW_SCORECARD_REPORT_CONFIG_VERSION = (
    "research-market-liquidity-exit-window-scorecard-report-v0"
)
LIQUIDITY_EXIT_WINDOW_SCORECARD_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("condition", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "url"),
    _join_parts("sour", "ce", "_", "text"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    "://",
)

COMPONENT_REASON_PRIORITY = (
    "exit_depth_block",
    "spread_block",
    "fill_window_block",
    "book_age_block",
    "resolution_window_block",
    "depth_decay_block",
    "fee_drag_block",
    "exit_depth_watch",
    "spread_watch",
    "fill_window_watch",
    "book_age_watch",
    "resolution_window_watch",
    "depth_decay_watch",
    "fee_drag_watch",
)


@dataclass(frozen=True)
class ResearchMarketLiquidityExitWindowScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_WINDOW_SCORECARD_REPORT_CONFIG_VERSION
    )
    minimum_pass_exit_depth_ratio: Decimal = Decimal("0.700000")
    minimum_watch_exit_depth_ratio: Decimal = Decimal("0.400000")
    maximum_pass_spread_ratio: Decimal = Decimal("0.020000")
    maximum_watch_spread_ratio: Decimal = Decimal("0.050000")
    maximum_pass_fill_window_minutes: Decimal = Decimal("15.000000")
    maximum_watch_fill_window_minutes: Decimal = Decimal("60.000000")
    maximum_pass_book_age_seconds: Decimal = Decimal("120.000000")
    maximum_watch_book_age_seconds: Decimal = Decimal("900.000000")
    minimum_pass_resolution_window_hours: Decimal = Decimal("72.000000")
    minimum_watch_resolution_window_hours: Decimal = Decimal("24.000000")
    maximum_pass_depth_decay_ratio: Decimal = Decimal("0.200000")
    maximum_watch_depth_decay_ratio: Decimal = Decimal("0.600000")
    maximum_pass_fee_drag_ratio: Decimal = Decimal("0.010000")
    maximum_watch_fee_drag_ratio: Decimal = Decimal("0.030000")
    exit_depth_weight: Decimal = Decimal("0.300000")
    spread_weight: Decimal = Decimal("0.200000")
    fill_window_weight: Decimal = Decimal("0.150000")
    book_age_weight: Decimal = Decimal("0.100000")
    resolution_window_weight: Decimal = Decimal("0.100000")
    depth_decay_weight: Decimal = Decimal("0.100000")
    fee_drag_weight: Decimal = Decimal("0.050000")
    pass_exit_window_score: Decimal = Decimal("0.750000")
    watch_exit_window_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityExitWindowScorecardConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_WINDOW_SCORECARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "minimum_pass_exit_depth_ratio",
            "minimum_watch_exit_depth_ratio",
            "maximum_pass_spread_ratio",
            "maximum_watch_spread_ratio",
            "maximum_pass_depth_decay_ratio",
            "maximum_watch_depth_decay_ratio",
            "maximum_pass_fee_drag_ratio",
            "maximum_watch_fee_drag_ratio",
            "exit_depth_weight",
            "spread_weight",
            "fill_window_weight",
            "book_age_weight",
            "resolution_window_weight",
            "depth_decay_weight",
            "fee_drag_weight",
            "pass_exit_window_score",
            "watch_exit_window_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_pass_fill_window_minutes",
            "maximum_watch_fill_window_minutes",
            "maximum_pass_book_age_seconds",
            "maximum_watch_book_age_seconds",
            "minimum_pass_resolution_window_hours",
            "minimum_watch_resolution_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_pass_exit_depth_ratio < self.minimum_watch_exit_depth_ratio:
            raise ValueError("minimum_pass_exit_depth_ratio must be at least watch")
        if self.maximum_pass_spread_ratio > self.maximum_watch_spread_ratio:
            raise ValueError("maximum_pass_spread_ratio must not exceed watch")
        if self.maximum_pass_fill_window_minutes > self.maximum_watch_fill_window_minutes:
            raise ValueError("maximum_pass_fill_window_minutes must not exceed watch")
        if self.maximum_pass_book_age_seconds > self.maximum_watch_book_age_seconds:
            raise ValueError("maximum_pass_book_age_seconds must not exceed watch")
        if (
            self.minimum_pass_resolution_window_hours
            < self.minimum_watch_resolution_window_hours
        ):
            raise ValueError("minimum_pass_resolution_window_hours must be at least watch")
        if self.maximum_pass_depth_decay_ratio > self.maximum_watch_depth_decay_ratio:
            raise ValueError("maximum_pass_depth_decay_ratio must not exceed watch")
        if self.maximum_pass_fee_drag_ratio > self.maximum_watch_fee_drag_ratio:
            raise ValueError("maximum_pass_fee_drag_ratio must not exceed watch")
        if self.pass_exit_window_score < self.watch_exit_window_score:
            raise ValueError("pass_exit_window_score must be at least watch")
        weight_sum = _quantize(
            self.exit_depth_weight
            + self.spread_weight
            + self.fill_window_weight
            + self.book_age_weight
            + self.resolution_window_weight
            + self.depth_decay_weight
            + self.fee_drag_weight,
        )
        if weight_sum != ONE:
            raise ValueError("scorecard weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityExitWindowScorecardInput:
    review_reference: str
    observed_at: datetime
    exit_depth_ratio: Decimal
    spread_ratio: Decimal
    expected_fill_window_minutes: Decimal
    book_age_seconds: Decimal
    resolution_window_hours: Decimal
    depth_decay_ratio: Decimal
    fee_drag_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityExitWindowScorecardInput, "input")
        _require_reference("review_reference", self.review_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "exit_depth_ratio",
            "spread_ratio",
            "depth_decay_ratio",
            "fee_drag_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_fill_window_minutes",
            "book_age_seconds",
            "resolution_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=True,
                sort_values=True,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityExitWindowScorecardRow:
    public_row_ref: str
    observed_at: datetime
    exit_depth_ratio: Decimal
    exit_depth_score: Decimal
    spread_ratio: Decimal
    spread_score: Decimal
    expected_fill_window_minutes: Decimal
    fill_window_score: Decimal
    book_age_seconds: Decimal
    book_age_score: Decimal
    resolution_window_hours: Decimal
    resolution_window_score: Decimal
    depth_decay_ratio: Decimal
    depth_decay_score: Decimal
    fee_drag_ratio: Decimal
    fee_drag_score: Decimal
    exit_depth_weight: Decimal
    spread_weight: Decimal
    fill_window_weight: Decimal
    book_age_weight: Decimal
    resolution_window_weight: Decimal
    depth_decay_weight: Decimal
    fee_drag_weight: Decimal
    exit_window_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityExitWindowScorecardRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_fill_window_minutes",
            "book_age_seconds",
            "resolution_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "exit_depth_ratio",
            "exit_depth_score",
            "spread_ratio",
            "spread_score",
            "fill_window_score",
            "book_age_score",
            "resolution_window_score",
            "depth_decay_ratio",
            "depth_decay_score",
            "fee_drag_ratio",
            "fee_drag_score",
            "exit_depth_weight",
            "spread_weight",
            "fill_window_weight",
            "book_age_weight",
            "resolution_window_weight",
            "depth_decay_weight",
            "fee_drag_weight",
            "exit_window_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketLiquidityExitWindowScorecardReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityExitWindowScorecardReasonCodeCount,
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
class ResearchMarketLiquidityExitWindowScorecardReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    exit_depth_pressure_count: Decimal
    spread_pressure_count: Decimal
    fill_window_pressure_count: Decimal
    stale_book_count: Decimal
    resolution_window_pressure_count: Decimal
    depth_decay_pressure_count: Decimal
    fee_drag_pressure_count: Decimal
    average_exit_window_score: Decimal | None
    min_exit_depth_ratio: Decimal
    max_spread_ratio: Decimal
    max_expected_fill_window_minutes: Decimal
    max_book_age_seconds: Decimal
    min_resolution_window_hours: Decimal
    max_depth_decay_ratio: Decimal
    max_fee_drag_ratio: Decimal
    status: str
    rows: tuple[ResearchMarketLiquidityExitWindowScorecardRow, ...]
    reason_code_counts: tuple[
        ResearchMarketLiquidityExitWindowScorecardReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityExitWindowScorecardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_WINDOW_SCORECARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "exit_depth_pressure_count",
            "spread_pressure_count",
            "fill_window_pressure_count",
            "stale_book_count",
            "resolution_window_pressure_count",
            "depth_decay_pressure_count",
            "fee_drag_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_exit_window_score",
            _require_optional_ratio_decimal(
                "average_exit_window_score",
                self.average_exit_window_score,
            ),
        )
        for field_name in (
            "max_expected_fill_window_minutes",
            "max_book_age_seconds",
            "min_resolution_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_exit_depth_ratio",
            "max_spread_ratio",
            "max_depth_decay_ratio",
            "max_fee_drag_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
        _validate_report_consistency(self)
        expected_digest = _derived_report_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_liquidity_exit_window_scorecard_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketLiquidityExitWindowScorecardConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityExitWindowScorecardReport:
    if type(config) is not ResearchMarketLiquidityExitWindowScorecardConfig:
        raise ValueError(
            "config must be a ResearchMarketLiquidityExitWindowScorecardConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    sorted_items = tuple(sorted(input_items, key=lambda item: item.review_reference))
    rows = tuple(
        _row_from_input(
            item,
            public_row_ref=f"exit_window_group_{index:03d}",
            config=config,
        )
        for index, item in enumerate(sorted_items, start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketLiquidityExitWindowScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        exit_depth_pressure_count=_decimal_count(_reason_count(rows, "exit_depth")),
        spread_pressure_count=_decimal_count(_reason_count(rows, "spread")),
        fill_window_pressure_count=_decimal_count(_reason_count(rows, "fill_window")),
        stale_book_count=_decimal_count(_reason_count(rows, "book_age")),
        resolution_window_pressure_count=_decimal_count(
            _reason_count(rows, "resolution_window"),
        ),
        depth_decay_pressure_count=_decimal_count(_reason_count(rows, "depth_decay")),
        fee_drag_pressure_count=_decimal_count(_reason_count(rows, "fee_drag")),
        average_exit_window_score=_average_exit_window_score(rows),
        min_exit_depth_ratio=_minimum_row_value(rows, "exit_depth_ratio"),
        max_spread_ratio=_maximum_row_value(rows, "spread_ratio"),
        max_expected_fill_window_minutes=_maximum_row_value(
            rows,
            "expected_fill_window_minutes",
        ),
        max_book_age_seconds=_maximum_row_value(rows, "book_age_seconds"),
        min_resolution_window_hours=_minimum_row_value(rows, "resolution_window_hours"),
        max_depth_decay_ratio=_maximum_row_value(rows, "depth_decay_ratio"),
        max_fee_drag_ratio=_maximum_row_value(rows, "fee_drag_ratio"),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_liquidity_exit_window_scorecard_report_payload(
    report: ResearchMarketLiquidityExitWindowScorecardReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketLiquidityExitWindowScorecardReport:
        raise ValueError(
            "report must be a ResearchMarketLiquidityExitWindowScorecardReport",
        )
    _require_hard_flags("report", report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload(payload)
    return payload


def research_market_liquidity_exit_window_scorecard_report_digest(
    report: ResearchMarketLiquidityExitWindowScorecardReport,
) -> str:
    if type(report) is not ResearchMarketLiquidityExitWindowScorecardReport:
        raise ValueError(
            "report must be a ResearchMarketLiquidityExitWindowScorecardReport",
        )
    _require_hard_flags("report", report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


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
    item: ResearchMarketLiquidityExitWindowScorecardInput,
    *,
    public_row_ref: str,
    config: ResearchMarketLiquidityExitWindowScorecardConfig,
) -> ResearchMarketLiquidityExitWindowScorecardRow:
    exit_depth_score = item.exit_depth_ratio
    spread_score = _inverse_ratio_score(item.spread_ratio, config.maximum_watch_spread_ratio)
    fill_window_score = _inverse_decimal_score(
        item.expected_fill_window_minutes,
        config.maximum_watch_fill_window_minutes,
    )
    book_age_score = _inverse_decimal_score(
        item.book_age_seconds,
        config.maximum_watch_book_age_seconds,
    )
    resolution_window_score = _positive_decimal_score(
        item.resolution_window_hours,
        config.minimum_pass_resolution_window_hours,
    )
    depth_decay_score = _inverse_ratio_score(
        item.depth_decay_ratio,
        config.maximum_watch_depth_decay_ratio,
    )
    fee_drag_score = _inverse_ratio_score(
        item.fee_drag_ratio,
        config.maximum_watch_fee_drag_ratio,
    )
    exit_window_score = _exit_window_score(
        exit_depth_score=exit_depth_score,
        spread_score=spread_score,
        fill_window_score=fill_window_score,
        book_age_score=book_age_score,
        resolution_window_score=resolution_window_score,
        depth_decay_score=depth_decay_score,
        fee_drag_score=fee_drag_score,
        config=config,
    )
    status = _row_status(
        exit_depth_ratio=item.exit_depth_ratio,
        spread_ratio=item.spread_ratio,
        expected_fill_window_minutes=item.expected_fill_window_minutes,
        book_age_seconds=item.book_age_seconds,
        resolution_window_hours=item.resolution_window_hours,
        depth_decay_ratio=item.depth_decay_ratio,
        fee_drag_ratio=item.fee_drag_ratio,
        exit_window_score=exit_window_score,
        config=config,
    )
    return ResearchMarketLiquidityExitWindowScorecardRow(
        public_row_ref=public_row_ref,
        observed_at=item.observed_at,
        exit_depth_ratio=item.exit_depth_ratio,
        exit_depth_score=exit_depth_score,
        spread_ratio=item.spread_ratio,
        spread_score=spread_score,
        expected_fill_window_minutes=item.expected_fill_window_minutes,
        fill_window_score=fill_window_score,
        book_age_seconds=item.book_age_seconds,
        book_age_score=book_age_score,
        resolution_window_hours=item.resolution_window_hours,
        resolution_window_score=resolution_window_score,
        depth_decay_ratio=item.depth_decay_ratio,
        depth_decay_score=depth_decay_score,
        fee_drag_ratio=item.fee_drag_ratio,
        fee_drag_score=fee_drag_score,
        exit_depth_weight=config.exit_depth_weight,
        spread_weight=config.spread_weight,
        fill_window_weight=config.fill_window_weight,
        book_age_weight=config.book_age_weight,
        resolution_window_weight=config.resolution_window_weight,
        depth_decay_weight=config.depth_decay_weight,
        fee_drag_weight=config.fee_drag_weight,
        exit_window_score=exit_window_score,
        status=status,
        reason_codes=_row_reason_codes(item, status, config),
    )


def _inverse_ratio_score(value: Decimal, zero_at: Decimal) -> Decimal:
    return _inverse_decimal_score(value, zero_at)


def _inverse_decimal_score(value: Decimal, zero_at: Decimal) -> Decimal:
    if zero_at <= ZERO:
        raise ValueError("zero_at must be positive")
    with localcontext() as context:
        context.prec = 28
        score = ONE - (value / zero_at)
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return _quantize(score)


def _positive_decimal_score(value: Decimal, pass_at: Decimal) -> Decimal:
    if pass_at <= ZERO:
        raise ValueError("pass_at must be positive")
    with localcontext() as context:
        context.prec = 28
        score = value / pass_at
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return _quantize(score)


def _exit_window_score(
    *,
    exit_depth_score: Decimal,
    spread_score: Decimal,
    fill_window_score: Decimal,
    book_age_score: Decimal,
    resolution_window_score: Decimal,
    depth_decay_score: Decimal,
    fee_drag_score: Decimal,
    config: ResearchMarketLiquidityExitWindowScorecardConfig,
) -> Decimal:
    return _quantize(
        exit_depth_score * config.exit_depth_weight
        + spread_score * config.spread_weight
        + fill_window_score * config.fill_window_weight
        + book_age_score * config.book_age_weight
        + resolution_window_score * config.resolution_window_weight
        + depth_decay_score * config.depth_decay_weight
        + fee_drag_score * config.fee_drag_weight,
    )


def _row_status(
    *,
    exit_depth_ratio: Decimal,
    spread_ratio: Decimal,
    expected_fill_window_minutes: Decimal,
    book_age_seconds: Decimal,
    resolution_window_hours: Decimal,
    depth_decay_ratio: Decimal,
    fee_drag_ratio: Decimal,
    exit_window_score: Decimal,
    config: ResearchMarketLiquidityExitWindowScorecardConfig,
) -> str:
    if (
        exit_depth_ratio < config.minimum_watch_exit_depth_ratio
        or spread_ratio > config.maximum_watch_spread_ratio
        or expected_fill_window_minutes > config.maximum_watch_fill_window_minutes
        or book_age_seconds > config.maximum_watch_book_age_seconds
        or resolution_window_hours < config.minimum_watch_resolution_window_hours
        or depth_decay_ratio > config.maximum_watch_depth_decay_ratio
        or fee_drag_ratio > config.maximum_watch_fee_drag_ratio
        or exit_window_score < config.watch_exit_window_score
    ):
        return "block"
    if (
        exit_depth_ratio < config.minimum_pass_exit_depth_ratio
        or spread_ratio > config.maximum_pass_spread_ratio
        or expected_fill_window_minutes > config.maximum_pass_fill_window_minutes
        or book_age_seconds > config.maximum_pass_book_age_seconds
        or resolution_window_hours < config.minimum_pass_resolution_window_hours
        or depth_decay_ratio > config.maximum_pass_depth_decay_ratio
        or fee_drag_ratio > config.maximum_pass_fee_drag_ratio
        or exit_window_score < config.pass_exit_window_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchMarketLiquidityExitWindowScorecardInput,
    status: str,
    config: ResearchMarketLiquidityExitWindowScorecardConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    reasons.extend(
        _lower_is_pressure_reason(
            item.exit_depth_ratio,
            config.minimum_pass_exit_depth_ratio,
            config.minimum_watch_exit_depth_ratio,
            "exit_depth_watch",
            "exit_depth_block",
        ),
    )
    reasons.extend(
        _higher_is_pressure_reason(
            item.spread_ratio,
            config.maximum_pass_spread_ratio,
            config.maximum_watch_spread_ratio,
            "spread_watch",
            "spread_block",
        ),
    )
    reasons.extend(
        _higher_is_pressure_reason(
            item.expected_fill_window_minutes,
            config.maximum_pass_fill_window_minutes,
            config.maximum_watch_fill_window_minutes,
            "fill_window_watch",
            "fill_window_block",
        ),
    )
    reasons.extend(
        _higher_is_pressure_reason(
            item.book_age_seconds,
            config.maximum_pass_book_age_seconds,
            config.maximum_watch_book_age_seconds,
            "book_age_watch",
            "book_age_block",
        ),
    )
    reasons.extend(
        _lower_is_pressure_reason(
            item.resolution_window_hours,
            config.minimum_pass_resolution_window_hours,
            config.minimum_watch_resolution_window_hours,
            "resolution_window_watch",
            "resolution_window_block",
        ),
    )
    reasons.extend(
        _higher_is_pressure_reason(
            item.depth_decay_ratio,
            config.maximum_pass_depth_decay_ratio,
            config.maximum_watch_depth_decay_ratio,
            "depth_decay_watch",
            "depth_decay_block",
        ),
    )
    reasons.extend(
        _higher_is_pressure_reason(
            item.fee_drag_ratio,
            config.maximum_pass_fee_drag_ratio,
            config.maximum_watch_fee_drag_ratio,
            "fee_drag_watch",
            "fee_drag_block",
        ),
    )
    reasons.append(f"exit_window_{status}")
    reasons.extend(f"input_{reason_code}" for reason_code in item.reason_codes)
    return _dedupe_reason_codes(reasons)


def _higher_is_pressure_reason(
    value: Decimal,
    pass_value: Decimal,
    watch_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> tuple[str, ...]:
    if value > watch_value:
        return (block_reason,)
    if value > pass_value:
        return (watch_reason,)
    return ()


def _lower_is_pressure_reason(
    value: Decimal,
    pass_value: Decimal,
    watch_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> tuple[str, ...]:
    if value < watch_value:
        return (block_reason,)
    if value < pass_value:
        return (watch_reason,)
    return ()


def _summary_reason_codes(
    rows: tuple[ResearchMarketLiquidityExitWindowScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_exit_window_observations",)
    status = _summary_status(rows)
    reasons = [f"exit_window_{status}"]
    row_reasons = {reason for row in rows for reason in row.reason_codes}
    reasons.extend(reason for reason in COMPONENT_REASON_PRIORITY if reason in row_reasons)
    return tuple(reasons)


def _summary_status(rows: tuple[ResearchMarketLiquidityExitWindowScorecardRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketLiquidityExitWindowScorecardInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized: list[ResearchMarketLiquidityExitWindowScorecardInput] = []
    seen: set[str] = set()
    for item in inputs:
        value = _coerce_input(item)
        _require_hard_flags("input", value)
        if value.review_reference in seen:
            raise ValueError("review_reference values must be unique")
        seen.add(value.review_reference)
        normalized.append(value)
    return tuple(normalized)


def _coerce_input(item: object) -> ResearchMarketLiquidityExitWindowScorecardInput:
    if type(item) is ResearchMarketLiquidityExitWindowScorecardInput:
        return item
    required_names = (
        "review_reference",
        "observed_at",
        "exit_depth_ratio",
        "spread_ratio",
        "expected_fill_window_minutes",
        "book_age_seconds",
        "resolution_window_hours",
        "depth_decay_ratio",
        "fee_drag_ratio",
    )
    if not all(hasattr(item, name) for name in required_names):
        raise ValueError(
            "inputs must contain ResearchMarketLiquidityExitWindowScorecardInput",
        )
    _require_hard_flags("input", item)
    reason_codes = getattr(item, "reason_codes", ())
    return ResearchMarketLiquidityExitWindowScorecardInput(
        review_reference=getattr(item, "review_reference"),
        observed_at=getattr(item, "observed_at"),
        exit_depth_ratio=getattr(item, "exit_depth_ratio"),
        spread_ratio=getattr(item, "spread_ratio"),
        expected_fill_window_minutes=getattr(item, "expected_fill_window_minutes"),
        book_age_seconds=getattr(item, "book_age_seconds"),
        resolution_window_hours=getattr(item, "resolution_window_hours"),
        depth_decay_ratio=getattr(item, "depth_decay_ratio"),
        fee_drag_ratio=getattr(item, "fee_drag_ratio"),
        reason_codes=reason_codes,
        paper_only=getattr(item, "paper_only"),
        report_only=getattr(item, "report_only"),
        readonly=getattr(item, "readonly"),
    )


def _normalize_rows(
    rows: Iterable[ResearchMarketLiquidityExitWindowScorecardRow],
) -> tuple[ResearchMarketLiquidityExitWindowScorecardRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketLiquidityExitWindowScorecardRow:
            raise ValueError("rows must contain ResearchMarketLiquidityExitWindowScorecardRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=lambda row: row.public_row_ref))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketLiquidityExitWindowScorecardReasonCodeCount],
) -> tuple[ResearchMarketLiquidityExitWindowScorecardReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketLiquidityExitWindowScorecardReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketLiquidityExitWindowScorecardReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    return tuple(sorted(normalized, key=lambda item: item.reason_code))


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquidityExitWindowScorecardRow, ...],
    summary_reasons: tuple[str, ...],
) -> tuple[ResearchMarketLiquidityExitWindowScorecardReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketLiquidityExitWindowScorecardReasonCodeCount(
                reason_code=summary_reasons[0],
                count=_decimal_count(1),
                row_ratio=ZERO,
            ),
        )
    row_count = _decimal_count(len(rows))
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(set(row.reason_codes))
    return tuple(
        ResearchMarketLiquidityExitWindowScorecardReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
            row_ratio=_quantize(_decimal_count(counter[reason_code]) / row_count),
        )
        for reason_code in sorted(summary_reasons)
    )


def _status_count(
    rows: tuple[ResearchMarketLiquidityExitWindowScorecardRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchMarketLiquidityExitWindowScorecardRow, ...],
    reason_prefix: str,
) -> int:
    return sum(
        1
        for row in rows
        if any(reason.startswith(f"{reason_prefix}_") for reason in row.reason_codes)
    )


def _average_exit_window_score(
    rows: tuple[ResearchMarketLiquidityExitWindowScorecardRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    with localcontext() as context:
        context.prec = 28
        return _quantize(
            sum((row.exit_window_score for row in rows), ZERO) / Decimal(len(rows)),
        )


def _minimum_row_value(
    rows: tuple[ResearchMarketLiquidityExitWindowScorecardRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _maximum_row_value(
    rows: tuple[ResearchMarketLiquidityExitWindowScorecardRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _validate_row_consistency(
    row: ResearchMarketLiquidityExitWindowScorecardRow,
) -> None:
    expected_score = _quantize(
        row.exit_depth_score * row.exit_depth_weight
        + row.spread_score * row.spread_weight
        + row.fill_window_score * row.fill_window_weight
        + row.book_age_score * row.book_age_weight
        + row.resolution_window_score * row.resolution_window_weight
        + row.depth_decay_score * row.depth_decay_weight
        + row.fee_drag_score * row.fee_drag_weight,
    )
    if row.exit_window_score != expected_score:
        raise ValueError("exit_window_score must match component scores")
    if f"exit_window_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchMarketLiquidityExitWindowScorecardReport,
) -> None:
    rows = report.rows
    if report.observation_count != _decimal_count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    count_checks = (
        ("exit_depth_pressure_count", "exit_depth"),
        ("spread_pressure_count", "spread"),
        ("fill_window_pressure_count", "fill_window"),
        ("stale_book_count", "book_age"),
        ("resolution_window_pressure_count", "resolution_window"),
        ("depth_decay_pressure_count", "depth_decay"),
        ("fee_drag_pressure_count", "fee_drag"),
    )
    for field_name, reason_prefix in count_checks:
        if getattr(report, field_name) != _decimal_count(_reason_count(rows, reason_prefix)):
            raise ValueError(f"{field_name} must match rows")
    if report.average_exit_window_score != _average_exit_window_score(rows):
        raise ValueError("average_exit_window_score must match rows")
    metric_checks = (
        ("min_exit_depth_ratio", _minimum_row_value(rows, "exit_depth_ratio")),
        ("max_spread_ratio", _maximum_row_value(rows, "spread_ratio")),
        (
            "max_expected_fill_window_minutes",
            _maximum_row_value(rows, "expected_fill_window_minutes"),
        ),
        ("max_book_age_seconds", _maximum_row_value(rows, "book_age_seconds")),
        (
            "min_resolution_window_hours",
            _minimum_row_value(rows, "resolution_window_hours"),
        ),
        ("max_depth_decay_ratio", _maximum_row_value(rows, "depth_decay_ratio")),
        ("max_fee_drag_ratio", _maximum_row_value(rows, "fee_drag_ratio")),
    )
    for field_name, expected in metric_checks:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _summary_status(rows):
        raise ValueError("status must match rows")
    expected_reasons = _summary_reason_codes(rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, expected_reasons):
        raise ValueError("reason_code_counts must match reason_codes")


def _derived_report_digest(
    report: ResearchMarketLiquidityExitWindowScorecardReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload(unsigned)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: Any) -> Any:
    return _json_ready(asdict(value) if is_dataclass(value) and not isinstance(value, type) else value)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, Mapping):
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            payload[key] = _json_ready(item)
        return payload
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError("unsafe public payload value")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError("unsafe public payload field")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)


def _dedupe_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    values: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in values:
            values.append(reason_code)
    return tuple(values)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
    sort_values: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    normalized = tuple(value)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in normalized:
        _require_reason_code(field_name, reason_code)
    deduped = _dedupe_reason_codes(normalized)
    if sort_values:
        return tuple(sorted(deduped))
    return deduped


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} values must be public safe")
    return value


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must contain public reason codes")
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} values must be public safe")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in LIQUIDITY_EXIT_WINDOW_SCORECARD_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(decimal_value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_hex_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
