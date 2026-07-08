"""Report-only resolution-window liquidity and cost frontier reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any


RESOLUTION_LIQUIDITY_COST_FRONTIER_STATUSES = ("pass", "watch", "block")
DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_COST_FRONTIER_REPORT_CONFIG_VERSION = (
    "research-market-resolution-liquidity-cost-frontier-report-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wal" "let",
    "au" "th",
    "private",
    "secret",
    "credential",
    "or" "der",
    "tra" "de",
    "live",
    "position",
    "siz" "ing",
    "recommendation",
)


__all__ = (
    "RESOLUTION_LIQUIDITY_COST_FRONTIER_STATUSES",
    "DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_COST_FRONTIER_REPORT_CONFIG_VERSION",
    "ResearchMarketResolutionLiquidityCostFrontierConfig",
    "ResearchMarketResolutionLiquidityCostFrontierReasonCodeCount",
    "ResearchMarketResolutionLiquidityCostFrontierReport",
    "ResearchMarketResolutionLiquidityCostFrontierRow",
    "ResearchMarketResolutionLiquidityCostFrontierSnapshot",
    "build_research_market_resolution_liquidity_cost_frontier_report",
    "research_market_resolution_liquidity_cost_frontier_report_digest",
    "research_market_resolution_liquidity_cost_frontier_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityCostFrontierConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_COST_FRONTIER_REPORT_CONFIG_VERSION
    )
    max_pass_spread_ratio: Decimal = Decimal("0.020000")
    max_watch_spread_ratio: Decimal = Decimal("0.080000")
    min_pass_near_band_depth: Decimal = Decimal("1000.000000")
    min_watch_near_band_depth: Decimal = Decimal("300.000000")
    min_pass_mid_band_depth: Decimal = Decimal("600.000000")
    min_watch_mid_band_depth: Decimal = Decimal("150.000000")
    min_pass_far_band_depth: Decimal = Decimal("300.000000")
    min_watch_far_band_depth: Decimal = Decimal("50.000000")
    max_pass_fee_drag_ratio: Decimal = Decimal("0.015000")
    max_watch_fee_drag_ratio: Decimal = Decimal("0.050000")
    min_pass_slippage_cushion_ratio: Decimal = Decimal("0.040000")
    min_watch_slippage_cushion_ratio: Decimal = Decimal("0.010000")
    max_pass_book_age_seconds: Decimal = Decimal("300.000000")
    max_watch_book_age_seconds: Decimal = Decimal("1200.000000")
    max_pass_volatility_ratio: Decimal = Decimal("0.200000")
    max_watch_volatility_ratio: Decimal = Decimal("0.500000")
    max_pass_settlement_friction_ratio: Decimal = Decimal("0.150000")
    max_watch_settlement_friction_ratio: Decimal = Decimal("0.400000")
    min_pass_resolution_window_seconds: Decimal = Decimal("3600.000000")
    min_watch_resolution_window_seconds: Decimal = Decimal("900.000000")
    pass_frontier_score: Decimal = Decimal("0.750000")
    watch_frontier_score: Decimal = Decimal("0.450000")
    spread_weight: Decimal = Decimal("0.150000")
    depth_band_weight: Decimal = Decimal("0.200000")
    fee_drag_weight: Decimal = Decimal("0.150000")
    slippage_cushion_weight: Decimal = Decimal("0.150000")
    book_age_weight: Decimal = Decimal("0.100000")
    volatility_weight: Decimal = Decimal("0.100000")
    settlement_friction_weight: Decimal = Decimal("0.100000")
    resolution_window_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketResolutionLiquidityCostFrontierConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketResolutionLiquidityCostFrontierConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_COST_FRONTIER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_spread_ratio",
            "max_watch_spread_ratio",
            "min_pass_near_band_depth",
            "min_watch_near_band_depth",
            "min_pass_mid_band_depth",
            "min_watch_mid_band_depth",
            "min_pass_far_band_depth",
            "min_watch_far_band_depth",
            "max_pass_fee_drag_ratio",
            "max_watch_fee_drag_ratio",
            "min_pass_slippage_cushion_ratio",
            "min_watch_slippage_cushion_ratio",
            "max_pass_book_age_seconds",
            "max_watch_book_age_seconds",
            "max_pass_volatility_ratio",
            "max_watch_volatility_ratio",
            "max_pass_settlement_friction_ratio",
            "max_watch_settlement_friction_ratio",
            "min_pass_resolution_window_seconds",
            "min_watch_resolution_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_watch_spread_ratio <= self.max_pass_spread_ratio:
            raise ValueError("max_watch_spread_ratio must exceed pass threshold")
        if self.min_pass_near_band_depth <= self.min_watch_near_band_depth:
            raise ValueError("min_pass_near_band_depth must exceed watch threshold")
        if self.min_pass_mid_band_depth <= self.min_watch_mid_band_depth:
            raise ValueError("min_pass_mid_band_depth must exceed watch threshold")
        if self.min_pass_far_band_depth <= self.min_watch_far_band_depth:
            raise ValueError("min_pass_far_band_depth must exceed watch threshold")
        if self.max_watch_fee_drag_ratio <= self.max_pass_fee_drag_ratio:
            raise ValueError("max_watch_fee_drag_ratio must exceed pass threshold")
        if (
            self.min_pass_slippage_cushion_ratio
            <= self.min_watch_slippage_cushion_ratio
        ):
            raise ValueError(
                "min_pass_slippage_cushion_ratio must exceed watch threshold",
            )
        if self.max_watch_book_age_seconds <= self.max_pass_book_age_seconds:
            raise ValueError("max_watch_book_age_seconds must exceed pass threshold")
        if self.max_watch_volatility_ratio <= self.max_pass_volatility_ratio:
            raise ValueError("max_watch_volatility_ratio must exceed pass threshold")
        if (
            self.max_watch_settlement_friction_ratio
            <= self.max_pass_settlement_friction_ratio
        ):
            raise ValueError(
                "max_watch_settlement_friction_ratio must exceed pass threshold",
            )
        if (
            self.min_pass_resolution_window_seconds
            <= self.min_watch_resolution_window_seconds
        ):
            raise ValueError(
                "min_pass_resolution_window_seconds must exceed watch threshold",
            )
        for field_name in (
            "pass_frontier_score",
            "watch_frontier_score",
            "spread_weight",
            "depth_band_weight",
            "fee_drag_weight",
            "slippage_cushion_weight",
            "book_age_weight",
            "volatility_weight",
            "settlement_friction_weight",
            "resolution_window_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_frontier_score <= self.watch_frontier_score:
            raise ValueError("pass_frontier_score must exceed watch threshold")
        weight_sum = _quantize(
            self.spread_weight
            + self.depth_band_weight
            + self.fee_drag_weight
            + self.slippage_cushion_weight
            + self.book_age_weight
            + self.volatility_weight
            + self.settlement_friction_weight
            + self.resolution_window_weight,
        )
        if weight_sum != ONE:
            raise ValueError("frontier score weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityCostFrontierSnapshot:
    frontier_snapshot_key: str
    observed_at: datetime
    resolution_window_seconds: Decimal
    best_bid_price: Decimal
    best_ask_price: Decimal
    near_band_depth: Decimal
    mid_band_depth: Decimal
    far_band_depth: Decimal
    fee_drag_ratio: Decimal
    slippage_cushion_ratio: Decimal
    volatility_ratio: Decimal
    settlement_friction_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketResolutionLiquidityCostFrontierSnapshot does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionLiquidityCostFrontierSnapshot,
            "snapshot",
        )
        _require_public_label("frontier_snapshot_key", self.frontier_snapshot_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolution_window_seconds",
            _require_positive_decimal(
                "resolution_window_seconds",
                self.resolution_window_seconds,
            ),
        )
        for field_name in ("best_bid_price", "best_ask_price"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.best_ask_price <= self.best_bid_price:
            raise ValueError("best_ask_price must exceed best_bid_price")
        for field_name in ("near_band_depth", "mid_band_depth", "far_band_depth"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.near_band_depth <= ZERO:
            raise ValueError("near_band_depth must be positive")
        if self.mid_band_depth > self.near_band_depth:
            raise ValueError("mid_band_depth must not exceed near_band_depth")
        if self.far_band_depth > self.mid_band_depth:
            raise ValueError("far_band_depth must not exceed mid_band_depth")
        for field_name in (
            "fee_drag_ratio",
            "slippage_cushion_ratio",
            "volatility_ratio",
            "settlement_friction_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityCostFrontierRow:
    public_frontier_ref: str
    observed_at: datetime
    resolution_window_seconds: Decimal
    book_age_seconds: Decimal
    spread_ratio: Decimal
    near_band_depth: Decimal
    mid_band_depth: Decimal
    far_band_depth: Decimal
    depth_band_coverage_ratio: Decimal
    depth_band_score: Decimal
    fee_drag_ratio: Decimal
    slippage_cushion_ratio: Decimal
    slippage_cushion_gap: Decimal
    volatility_ratio: Decimal
    settlement_friction_ratio: Decimal
    spread_score: Decimal
    fee_drag_score: Decimal
    slippage_cushion_score: Decimal
    book_age_score: Decimal
    book_age_pressure: Decimal
    volatility_score: Decimal
    settlement_friction_score: Decimal
    resolution_window_score: Decimal
    cost_pressure: Decimal
    frontier_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketResolutionLiquidityCostFrontierRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketResolutionLiquidityCostFrontierRow, "row")
        _require_public_label("public_frontier_ref", self.public_frontier_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "resolution_window_seconds",
            "book_age_seconds",
            "near_band_depth",
            "mid_band_depth",
            "far_band_depth",
            "slippage_cushion_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_ratio",
            "depth_band_coverage_ratio",
            "depth_band_score",
            "fee_drag_ratio",
            "slippage_cushion_ratio",
            "volatility_ratio",
            "settlement_friction_ratio",
            "spread_score",
            "fee_drag_score",
            "slippage_cushion_score",
            "book_age_score",
            "book_age_pressure",
            "volatility_score",
            "settlement_friction_score",
            "resolution_window_score",
            "cost_pressure",
            "frontier_score",
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
        _validate_row(self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityCostFrontierReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketResolutionLiquidityCostFrontierReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionLiquidityCostFrontierReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityCostFrontierReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_frontier_score: Decimal | None
    max_spread_ratio: Decimal
    min_near_band_depth: Decimal
    min_mid_band_depth: Decimal
    min_far_band_depth: Decimal
    max_fee_drag_ratio: Decimal
    max_slippage_cushion_gap: Decimal
    max_book_age_seconds: Decimal
    max_volatility_ratio: Decimal
    max_settlement_friction_ratio: Decimal
    min_resolution_window_seconds: Decimal
    status: str
    rows: tuple[ResearchMarketResolutionLiquidityCostFrontierRow, ...]
    reason_code_counts: tuple[
        ResearchMarketResolutionLiquidityCostFrontierReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketResolutionLiquidityCostFrontierReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionLiquidityCostFrontierReport,
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
            "average_frontier_score",
            _require_optional_ratio_decimal(
                "average_frontier_score",
                self.average_frontier_score,
            ),
        )
        for field_name in (
            "max_spread_ratio",
            "min_near_band_depth",
            "min_mid_band_depth",
            "min_far_band_depth",
            "max_fee_drag_ratio",
            "max_slippage_cushion_gap",
            "max_book_age_seconds",
            "max_volatility_ratio",
            "max_settlement_friction_ratio",
            "min_resolution_window_seconds",
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


def build_research_market_resolution_liquidity_cost_frontier_report(
    snapshots: Iterable[ResearchMarketResolutionLiquidityCostFrontierSnapshot],
    *,
    config: ResearchMarketResolutionLiquidityCostFrontierConfig,
    generated_at: datetime,
) -> ResearchMarketResolutionLiquidityCostFrontierReport:
    if type(config) is not ResearchMarketResolutionLiquidityCostFrontierConfig:
        raise ValueError(
            "config must be a ResearchMarketResolutionLiquidityCostFrontierConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_snapshots(snapshots)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        _row_from_snapshot(
            public_frontier_ref=f"resolution_frontier_group_{index:03d}",
            snapshot=item,
            config=config,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(sorted(normalized, key=_snapshot_sort_key), start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketResolutionLiquidityCostFrontierReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_frontier_score=_average_frontier_score(rows),
        max_spread_ratio=_maximum_row_value(rows, "spread_ratio"),
        min_near_band_depth=_minimum_row_value(rows, "near_band_depth"),
        min_mid_band_depth=_minimum_row_value(rows, "mid_band_depth"),
        min_far_band_depth=_minimum_row_value(rows, "far_band_depth"),
        max_fee_drag_ratio=_maximum_row_value(rows, "fee_drag_ratio"),
        max_slippage_cushion_gap=_maximum_row_value(rows, "slippage_cushion_gap"),
        max_book_age_seconds=_maximum_row_value(rows, "book_age_seconds"),
        max_volatility_ratio=_maximum_row_value(rows, "volatility_ratio"),
        max_settlement_friction_ratio=_maximum_row_value(
            rows,
            "settlement_friction_ratio",
        ),
        min_resolution_window_seconds=_minimum_row_value(
            rows,
            "resolution_window_seconds",
        ),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_resolution_liquidity_cost_frontier_report_payload(
    report: ResearchMarketResolutionLiquidityCostFrontierReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketResolutionLiquidityCostFrontierReport:
        raise ValueError(
            "report must be a ResearchMarketResolutionLiquidityCostFrontierReport",
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


def research_market_resolution_liquidity_cost_frontier_report_digest(
    report: ResearchMarketResolutionLiquidityCostFrontierReport,
) -> str:
    if type(report) is not ResearchMarketResolutionLiquidityCostFrontierReport:
        raise ValueError(
            "report must be a ResearchMarketResolutionLiquidityCostFrontierReport",
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


def _row_from_snapshot(
    *,
    public_frontier_ref: str,
    snapshot: ResearchMarketResolutionLiquidityCostFrontierSnapshot,
    config: ResearchMarketResolutionLiquidityCostFrontierConfig,
    generated_at: datetime,
) -> ResearchMarketResolutionLiquidityCostFrontierRow:
    book_age_seconds = _age_seconds(generated_at, snapshot.observed_at)
    spread_ratio = _quantize(snapshot.best_ask_price - snapshot.best_bid_price)
    depth_band_coverage_ratio = _safe_ratio(snapshot.far_band_depth, snapshot.near_band_depth)
    depth_band_score = _depth_band_score(snapshot, config)
    slippage_cushion_gap = _quantize(
        max(ZERO, config.min_pass_slippage_cushion_ratio - snapshot.slippage_cushion_ratio),
    )
    spread_score = _inverse_ratio_score(spread_ratio, config.max_watch_spread_ratio)
    fee_drag_score = _inverse_ratio_score(
        snapshot.fee_drag_ratio,
        config.max_watch_fee_drag_ratio,
    )
    slippage_cushion_score = _forward_ratio_score(
        snapshot.slippage_cushion_ratio,
        config.min_pass_slippage_cushion_ratio,
    )
    book_age_score = _inverse_ratio_score(
        book_age_seconds,
        config.max_watch_book_age_seconds,
    )
    book_age_pressure = _quantize(ONE - book_age_score)
    volatility_score = _inverse_ratio_score(
        snapshot.volatility_ratio,
        config.max_watch_volatility_ratio,
    )
    settlement_friction_score = _inverse_ratio_score(
        snapshot.settlement_friction_ratio,
        config.max_watch_settlement_friction_ratio,
    )
    resolution_window_score = _forward_ratio_score(
        snapshot.resolution_window_seconds,
        config.min_pass_resolution_window_seconds,
    )
    frontier_score = _frontier_score(
        spread_score=spread_score,
        depth_band_score=depth_band_score,
        fee_drag_score=fee_drag_score,
        slippage_cushion_score=slippage_cushion_score,
        book_age_score=book_age_score,
        volatility_score=volatility_score,
        settlement_friction_score=settlement_friction_score,
        resolution_window_score=resolution_window_score,
        config=config,
    )
    status = _row_status(
        spread_ratio=spread_ratio,
        near_band_depth=snapshot.near_band_depth,
        mid_band_depth=snapshot.mid_band_depth,
        far_band_depth=snapshot.far_band_depth,
        fee_drag_ratio=snapshot.fee_drag_ratio,
        slippage_cushion_ratio=snapshot.slippage_cushion_ratio,
        book_age_seconds=book_age_seconds,
        volatility_ratio=snapshot.volatility_ratio,
        settlement_friction_ratio=snapshot.settlement_friction_ratio,
        resolution_window_seconds=snapshot.resolution_window_seconds,
        frontier_score=frontier_score,
        config=config,
    )
    return ResearchMarketResolutionLiquidityCostFrontierRow(
        public_frontier_ref=public_frontier_ref,
        observed_at=snapshot.observed_at,
        resolution_window_seconds=snapshot.resolution_window_seconds,
        book_age_seconds=book_age_seconds,
        spread_ratio=spread_ratio,
        near_band_depth=snapshot.near_band_depth,
        mid_band_depth=snapshot.mid_band_depth,
        far_band_depth=snapshot.far_band_depth,
        depth_band_coverage_ratio=depth_band_coverage_ratio,
        depth_band_score=depth_band_score,
        fee_drag_ratio=snapshot.fee_drag_ratio,
        slippage_cushion_ratio=snapshot.slippage_cushion_ratio,
        slippage_cushion_gap=slippage_cushion_gap,
        volatility_ratio=snapshot.volatility_ratio,
        settlement_friction_ratio=snapshot.settlement_friction_ratio,
        spread_score=spread_score,
        fee_drag_score=fee_drag_score,
        slippage_cushion_score=slippage_cushion_score,
        book_age_score=book_age_score,
        book_age_pressure=book_age_pressure,
        volatility_score=volatility_score,
        settlement_friction_score=settlement_friction_score,
        resolution_window_score=resolution_window_score,
        cost_pressure=_cost_pressure(
            spread_score=spread_score,
            fee_drag_score=fee_drag_score,
            slippage_cushion_score=slippage_cushion_score,
            book_age_score=book_age_score,
            volatility_score=volatility_score,
            settlement_friction_score=settlement_friction_score,
            resolution_window_score=resolution_window_score,
            config=config,
        ),
        frontier_score=frontier_score,
        status=status,
        reason_codes=_row_reason_codes(
            snapshot=snapshot,
            spread_ratio=spread_ratio,
            near_band_depth=snapshot.near_band_depth,
            mid_band_depth=snapshot.mid_band_depth,
            far_band_depth=snapshot.far_band_depth,
            fee_drag_ratio=snapshot.fee_drag_ratio,
            slippage_cushion_ratio=snapshot.slippage_cushion_ratio,
            book_age_seconds=book_age_seconds,
            volatility_ratio=snapshot.volatility_ratio,
            settlement_friction_ratio=snapshot.settlement_friction_ratio,
            resolution_window_seconds=snapshot.resolution_window_seconds,
            status=status,
            config=config,
        ),
    )


def _frontier_score(
    *,
    spread_score: Decimal,
    depth_band_score: Decimal,
    fee_drag_score: Decimal,
    slippage_cushion_score: Decimal,
    book_age_score: Decimal,
    volatility_score: Decimal,
    settlement_friction_score: Decimal,
    resolution_window_score: Decimal,
    config: ResearchMarketResolutionLiquidityCostFrontierConfig,
) -> Decimal:
    return _quantize(
        _quantize(spread_score * config.spread_weight)
        + _quantize(depth_band_score * config.depth_band_weight)
        + _quantize(fee_drag_score * config.fee_drag_weight)
        + _quantize(slippage_cushion_score * config.slippage_cushion_weight)
        + _quantize(book_age_score * config.book_age_weight)
        + _quantize(volatility_score * config.volatility_weight)
        + _quantize(settlement_friction_score * config.settlement_friction_weight)
        + _quantize(resolution_window_score * config.resolution_window_weight),
    )


def _cost_pressure(
    *,
    spread_score: Decimal,
    fee_drag_score: Decimal,
    slippage_cushion_score: Decimal,
    book_age_score: Decimal,
    volatility_score: Decimal,
    settlement_friction_score: Decimal,
    resolution_window_score: Decimal,
    config: ResearchMarketResolutionLiquidityCostFrontierConfig,
) -> Decimal:
    non_depth_weight = _quantize(
        config.spread_weight
        + config.fee_drag_weight
        + config.slippage_cushion_weight
        + config.book_age_weight
        + config.volatility_weight
        + config.settlement_friction_weight
        + config.resolution_window_weight,
    )
    if non_depth_weight <= ZERO:
        raise ValueError("non-depth cost pressure weights must be positive")
    weighted_pressure = _quantize(
        _quantize((ONE - spread_score) * config.spread_weight)
        + _quantize((ONE - fee_drag_score) * config.fee_drag_weight)
        + _quantize((ONE - slippage_cushion_score) * config.slippage_cushion_weight)
        + _quantize((ONE - book_age_score) * config.book_age_weight)
        + _quantize((ONE - volatility_score) * config.volatility_weight)
        + _quantize(
            (ONE - settlement_friction_score)
            * config.settlement_friction_weight,
        )
        + _quantize((ONE - resolution_window_score) * config.resolution_window_weight),
    )
    return _bounded_ratio(_quantize(weighted_pressure / non_depth_weight))


def _row_status(
    *,
    spread_ratio: Decimal,
    near_band_depth: Decimal,
    mid_band_depth: Decimal,
    far_band_depth: Decimal,
    fee_drag_ratio: Decimal,
    slippage_cushion_ratio: Decimal,
    book_age_seconds: Decimal,
    volatility_ratio: Decimal,
    settlement_friction_ratio: Decimal,
    resolution_window_seconds: Decimal,
    frontier_score: Decimal,
    config: ResearchMarketResolutionLiquidityCostFrontierConfig,
) -> str:
    if (
        frontier_score < config.watch_frontier_score
        or spread_ratio >= config.max_watch_spread_ratio
        or near_band_depth < config.min_watch_near_band_depth
        or mid_band_depth < config.min_watch_mid_band_depth
        or far_band_depth < config.min_watch_far_band_depth
        or fee_drag_ratio >= config.max_watch_fee_drag_ratio
        or slippage_cushion_ratio < config.min_watch_slippage_cushion_ratio
        or book_age_seconds >= config.max_watch_book_age_seconds
        or volatility_ratio >= config.max_watch_volatility_ratio
        or settlement_friction_ratio >= config.max_watch_settlement_friction_ratio
        or resolution_window_seconds < config.min_watch_resolution_window_seconds
    ):
        return "block"
    if (
        frontier_score < config.pass_frontier_score
        or spread_ratio >= config.max_pass_spread_ratio
        or near_band_depth < config.min_pass_near_band_depth
        or mid_band_depth < config.min_pass_mid_band_depth
        or far_band_depth < config.min_pass_far_band_depth
        or fee_drag_ratio >= config.max_pass_fee_drag_ratio
        or slippage_cushion_ratio < config.min_pass_slippage_cushion_ratio
        or book_age_seconds >= config.max_pass_book_age_seconds
        or volatility_ratio >= config.max_pass_volatility_ratio
        or settlement_friction_ratio >= config.max_pass_settlement_friction_ratio
        or resolution_window_seconds < config.min_pass_resolution_window_seconds
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    snapshot: ResearchMarketResolutionLiquidityCostFrontierSnapshot,
    spread_ratio: Decimal,
    near_band_depth: Decimal,
    mid_band_depth: Decimal,
    far_band_depth: Decimal,
    fee_drag_ratio: Decimal,
    slippage_cushion_ratio: Decimal,
    book_age_seconds: Decimal,
    volatility_ratio: Decimal,
    settlement_friction_ratio: Decimal,
    resolution_window_seconds: Decimal,
    status: str,
    config: ResearchMarketResolutionLiquidityCostFrontierConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"frontier_score_{status}"}
    reason_codes.add(
        _maximum_threshold_reason(
            "spread",
            spread_ratio,
            config.max_pass_spread_ratio,
            config.max_watch_spread_ratio,
        ),
    )
    reason_codes.add(
        _minimum_depth_reason(
            "depth_band",
            near_band_depth,
            mid_band_depth,
            far_band_depth,
            config,
        ),
    )
    reason_codes.add(
        _maximum_threshold_reason(
            "fee_drag",
            fee_drag_ratio,
            config.max_pass_fee_drag_ratio,
            config.max_watch_fee_drag_ratio,
        ),
    )
    reason_codes.add(
        _minimum_threshold_reason(
            "slippage_cushion",
            slippage_cushion_ratio,
            config.min_pass_slippage_cushion_ratio,
            config.min_watch_slippage_cushion_ratio,
        ),
    )
    reason_codes.add(
        _maximum_threshold_reason(
            "book_age",
            book_age_seconds,
            config.max_pass_book_age_seconds,
            config.max_watch_book_age_seconds,
        ),
    )
    reason_codes.add(
        _maximum_threshold_reason(
            "volatility",
            volatility_ratio,
            config.max_pass_volatility_ratio,
            config.max_watch_volatility_ratio,
        ),
    )
    reason_codes.add(
        _maximum_threshold_reason(
            "settlement_friction",
            settlement_friction_ratio,
            config.max_pass_settlement_friction_ratio,
            config.max_watch_settlement_friction_ratio,
        ),
    )
    reason_codes.add(
        _minimum_threshold_reason(
            "resolution_window",
            resolution_window_seconds,
            config.min_pass_resolution_window_seconds,
            config.min_watch_resolution_window_seconds,
        ),
    )
    for reason_code in snapshot.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _maximum_threshold_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value >= watch_threshold:
        return f"{prefix}_block"
    if value >= pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _minimum_threshold_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value < watch_threshold:
        return f"{prefix}_block"
    if value < pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _minimum_depth_reason(
    prefix: str,
    near_band_depth: Decimal,
    mid_band_depth: Decimal,
    far_band_depth: Decimal,
    config: ResearchMarketResolutionLiquidityCostFrontierConfig,
) -> str:
    if (
        near_band_depth < config.min_watch_near_band_depth
        or mid_band_depth < config.min_watch_mid_band_depth
        or far_band_depth < config.min_watch_far_band_depth
    ):
        return f"{prefix}_block"
    if (
        near_band_depth < config.min_pass_near_band_depth
        or mid_band_depth < config.min_pass_mid_band_depth
        or far_band_depth < config.min_pass_far_band_depth
    ):
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _depth_band_score(
    snapshot: ResearchMarketResolutionLiquidityCostFrontierSnapshot,
    config: ResearchMarketResolutionLiquidityCostFrontierConfig,
) -> Decimal:
    return min(
        _forward_ratio_score(snapshot.near_band_depth, config.min_pass_near_band_depth),
        _forward_ratio_score(snapshot.mid_band_depth, config.min_pass_mid_band_depth),
        _forward_ratio_score(snapshot.far_band_depth, config.min_pass_far_band_depth),
    )


def _normalize_snapshots(
    snapshots: Iterable[ResearchMarketResolutionLiquidityCostFrontierSnapshot],
) -> tuple[ResearchMarketResolutionLiquidityCostFrontierSnapshot, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable")
    try:
        values = tuple(snapshots)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchMarketResolutionLiquidityCostFrontierSnapshot:
            raise ValueError(
                "snapshots must contain "
                "ResearchMarketResolutionLiquidityCostFrontierSnapshot values",
            )
        _require_hard_flags("snapshot", value)
    keys = tuple(value.frontier_snapshot_key for value in values)
    if len(set(keys)) != len(keys):
        raise ValueError("frontier_snapshot_key values must be unique")
    return values


def _normalize_rows(
    rows: tuple[ResearchMarketResolutionLiquidityCostFrontierRow, ...],
) -> tuple[ResearchMarketResolutionLiquidityCostFrontierRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketResolutionLiquidityCostFrontierRow:
            raise ValueError(
                "rows must contain ResearchMarketResolutionLiquidityCostFrontierRow "
                "values",
            )
        _require_hard_flags("row", row)
        if row.public_frontier_ref in seen:
            raise ValueError("public_frontier_ref values must be unique")
        seen.add(row.public_frontier_ref)
    if rows != tuple(sorted(rows, key=lambda row: row.public_frontier_ref)):
        raise ValueError("rows must be sorted by public_frontier_ref")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketResolutionLiquidityCostFrontierReasonCodeCount, ...],
) -> tuple[ResearchMarketResolutionLiquidityCostFrontierReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketResolutionLiquidityCostFrontierReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda item: item.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row(row: ResearchMarketResolutionLiquidityCostFrontierRow) -> None:
    if row.near_band_depth <= ZERO:
        raise ValueError("near_band_depth must be positive")
    if row.mid_band_depth > row.near_band_depth:
        raise ValueError("mid_band_depth must not exceed near_band_depth")
    if row.far_band_depth > row.mid_band_depth:
        raise ValueError("far_band_depth must not exceed mid_band_depth")
    if row.depth_band_coverage_ratio != _safe_ratio(
        row.far_band_depth,
        row.near_band_depth,
    ):
        raise ValueError("depth_band_coverage_ratio must match depth fields")
    if row.book_age_pressure != _quantize(ONE - row.book_age_score):
        raise ValueError("book_age_pressure must match book_age_score")
    if f"frontier_score_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchMarketResolutionLiquidityCostFrontierReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_frontier_score != _average_frontier_score(report.rows):
        raise ValueError("average_frontier_score must match rows")
    expected_pairs = (
        ("max_spread_ratio", _maximum_row_value(report.rows, "spread_ratio")),
        ("min_near_band_depth", _minimum_row_value(report.rows, "near_band_depth")),
        ("min_mid_band_depth", _minimum_row_value(report.rows, "mid_band_depth")),
        ("min_far_band_depth", _minimum_row_value(report.rows, "far_band_depth")),
        ("max_fee_drag_ratio", _maximum_row_value(report.rows, "fee_drag_ratio")),
        (
            "max_slippage_cushion_gap",
            _maximum_row_value(report.rows, "slippage_cushion_gap"),
        ),
        ("max_book_age_seconds", _maximum_row_value(report.rows, "book_age_seconds")),
        ("max_volatility_ratio", _maximum_row_value(report.rows, "volatility_ratio")),
        (
            "max_settlement_friction_ratio",
            _maximum_row_value(report.rows, "settlement_friction_ratio"),
        ),
        (
            "min_resolution_window_seconds",
            _minimum_row_value(report.rows, "resolution_window_seconds"),
        ),
    )
    for field_name, expected_value in expected_pairs:
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _summary_status(
    rows: tuple[ResearchMarketResolutionLiquidityCostFrontierRow, ...],
) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchMarketResolutionLiquidityCostFrontierRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_liquidity_cost_frontier_snapshots",)
    if all(row.status == "pass" for row in rows):
        return ("frontier_score_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchMarketResolutionLiquidityCostFrontierRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketResolutionLiquidityCostFrontierReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketResolutionLiquidityCostFrontierReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    total = _decimal_count(len(rows))
    return tuple(
        ResearchMarketResolutionLiquidityCostFrontierReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(_decimal_count(count) / total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_frontier_score(
    rows: tuple[ResearchMarketResolutionLiquidityCostFrontierRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.frontier_score for row in rows), ZERO) / _decimal_count(len(rows)))


def _status_count(
    rows: tuple[ResearchMarketResolutionLiquidityCostFrontierRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _maximum_row_value(
    rows: tuple[ResearchMarketResolutionLiquidityCostFrontierRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _minimum_row_value(
    rows: tuple[ResearchMarketResolutionLiquidityCostFrontierRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _inverse_ratio_score(value: Decimal, zero_at: Decimal) -> Decimal:
    if zero_at <= ZERO:
        raise ValueError("zero_at must be positive")
    return _bounded_ratio(_quantize(ONE - _quantize(value / zero_at)))


def _forward_ratio_score(value: Decimal, full_at: Decimal) -> Decimal:
    if full_at <= ZERO:
        raise ValueError("full_at must be positive")
    return _bounded_ratio(_quantize(value / full_at))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _bounded_ratio(_quantize(numerator / denominator))


def _bounded_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


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
    if (
        type(value) is not str
        or value not in RESOLUTION_LIQUIDITY_COST_FRONTIER_STATUSES
    ):
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    if _contains_unsafe_public_text(value):
        raise ValueError(f"{name} has unsafe public text")
    return value


def _require_reason_code(name: str, value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a reason code")
    if _contains_unsafe_public_text(value):
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
    checked = tuple(sorted(_require_reason_code(name, value) for value in values))
    if len(checked) != len(frozenset(checked)):
        raise ValueError(f"{name} must contain unique values")
    if not allow_empty and not checked:
        raise ValueError(f"{name} must not be empty")
    return checked


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


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


def _require_hex_digest(name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a SHA-256 hex digest") from exc
    if value.lower() != value:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    return value


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


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


def _snapshot_sort_key(
    snapshot: ResearchMarketResolutionLiquidityCostFrontierSnapshot,
) -> str:
    return snapshot.frontier_snapshot_key


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _derived_report_digest(
    report: ResearchMarketResolutionLiquidityCostFrontierReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload = dict(payload)
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str or _contains_unsafe_public_text(key):
                raise ValueError("public payload has unsafe public key")
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str) and _contains_unsafe_public_text(value):
        raise ValueError("public payload has unsafe public text")


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
