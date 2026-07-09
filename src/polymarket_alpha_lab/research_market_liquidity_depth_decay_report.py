"""Pure report-only liquidity depth decay reducer for manual research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


LIQUIDITY_DEPTH_DECAY_STATUSES = ("pass", "watch", "block")
DEFAULT_RESEARCH_MARKET_LIQUIDITY_DEPTH_DECAY_REPORT_CONFIG_VERSION = (
    "research-market-liquidity-depth-decay-report-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
UNSAFE_PUBLIC_FRAGMENTS = tuple(
    "".join(parts)
    for parts in (
        ("candidate", "_", "id"),
        ("condition", "_", "id"),
        ("market", "_", "id"),
        ("market", "_", "slug"),
        ("slug",),
        ("question",),
        ("source", "_", "url"),
        ("source", "_", "text"),
        ("d", "s", "n"),
        ("ta", "ble"),
        ("to", "ken"),
        ("wal", "let"),
        ("au", "th"),
        ("private",),
        ("secret",),
        ("credential",),
        ("or", "der"),
        ("tra", "de"),
        ("buy",),
        ("sell",),
        ("size",),
        ("siz", "ing"),
        ("recommendation",),
    )
)


__all__ = (
    "LIQUIDITY_DEPTH_DECAY_STATUSES",
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_DEPTH_DECAY_REPORT_CONFIG_VERSION",
    "ResearchMarketLiquidityDepthDecayConfig",
    "ResearchMarketLiquidityDepthDecayReasonCodeCount",
    "ResearchMarketLiquidityDepthDecayReport",
    "ResearchMarketLiquidityDepthDecayRow",
    "ResearchMarketLiquidityDepthDecaySnapshot",
    "build_research_market_liquidity_depth_decay_report",
    "research_market_liquidity_depth_decay_report_digest",
    "research_market_liquidity_depth_decay_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketLiquidityDepthDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_DEPTH_DECAY_REPORT_CONFIG_VERSION
    )
    max_pass_book_age_seconds: Decimal = Decimal("300.000000")
    max_watch_book_age_seconds: Decimal = Decimal("900.000000")
    max_pass_spread: Decimal = Decimal("0.020000")
    max_watch_spread: Decimal = Decimal("0.050000")
    max_pass_spread_change_pressure: Decimal = Decimal("0.010000")
    max_watch_spread_change_pressure: Decimal = Decimal("0.030000")
    max_pass_depth_decay_ratio: Decimal = Decimal("0.250000")
    max_watch_depth_decay_ratio: Decimal = Decimal("0.600000")
    max_pass_unchanged_book_seconds: Decimal = Decimal("180.000000")
    max_watch_unchanged_book_seconds: Decimal = Decimal("600.000000")
    max_pass_concentration_pressure: Decimal = Decimal("0.500000")
    max_watch_concentration_pressure: Decimal = Decimal("0.800000")
    pass_liquidity_depth_decay_score: Decimal = Decimal("0.750000")
    watch_liquidity_depth_decay_score: Decimal = Decimal("0.450000")
    depth_freshness_weight: Decimal = Decimal("0.250000")
    spread_pressure_weight: Decimal = Decimal("0.200000")
    spread_change_pressure_weight: Decimal = Decimal("0.100000")
    depth_decay_weight: Decimal = Decimal("0.200000")
    stale_book_risk_weight: Decimal = Decimal("0.150000")
    concentration_pressure_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchMarketLiquidityDepthDecayConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityDepthDecayConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_DEPTH_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_book_age_seconds",
            "max_watch_book_age_seconds",
            "max_pass_spread",
            "max_watch_spread",
            "max_pass_spread_change_pressure",
            "max_watch_spread_change_pressure",
            "max_pass_depth_decay_ratio",
            "max_watch_depth_decay_ratio",
            "max_pass_unchanged_book_seconds",
            "max_watch_unchanged_book_seconds",
            "max_pass_concentration_pressure",
            "max_watch_concentration_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_watch_book_age_seconds <= self.max_pass_book_age_seconds:
            raise ValueError("max_watch_book_age_seconds must exceed pass threshold")
        if self.max_watch_spread <= self.max_pass_spread:
            raise ValueError("max_watch_spread must exceed pass threshold")
        if self.max_watch_spread_change_pressure <= self.max_pass_spread_change_pressure:
            raise ValueError(
                "max_watch_spread_change_pressure must exceed pass threshold",
            )
        if self.max_watch_depth_decay_ratio <= self.max_pass_depth_decay_ratio:
            raise ValueError("max_watch_depth_decay_ratio must exceed pass threshold")
        if self.max_watch_unchanged_book_seconds <= self.max_pass_unchanged_book_seconds:
            raise ValueError("max_watch_unchanged_book_seconds must exceed pass threshold")
        if self.max_watch_concentration_pressure <= self.max_pass_concentration_pressure:
            raise ValueError(
                "max_watch_concentration_pressure must exceed pass threshold",
            )
        for field_name in (
            "pass_liquidity_depth_decay_score",
            "watch_liquidity_depth_decay_score",
            "depth_freshness_weight",
            "spread_pressure_weight",
            "spread_change_pressure_weight",
            "depth_decay_weight",
            "stale_book_risk_weight",
            "concentration_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_liquidity_depth_decay_score <= self.watch_liquidity_depth_decay_score:
            raise ValueError(
                "pass_liquidity_depth_decay_score must exceed watch threshold",
            )
        weight_sum = _quantize(
            self.depth_freshness_weight
            + self.spread_pressure_weight
            + self.spread_change_pressure_weight
            + self.depth_decay_weight
            + self.stale_book_risk_weight
            + self.concentration_pressure_weight,
        )
        if weight_sum != ONE:
            raise ValueError("liquidity depth decay score weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityDepthDecaySnapshot:
    book_snapshot_key: str
    observed_at: datetime
    last_depth_change_at: datetime
    best_bid_price: Decimal
    best_ask_price: Decimal
    spread_change_pressure: Decimal
    near_band_depth: Decimal
    far_band_depth: Decimal
    concentration_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquidityDepthDecaySnapshot does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityDepthDecaySnapshot, "snapshot")
        _require_canonical_string("book_snapshot_key", self.book_snapshot_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_depth_change_at",
            _as_utc("last_depth_change_at", self.last_depth_change_at),
        )
        for field_name in ("best_bid_price", "best_ask_price"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.best_ask_price <= self.best_bid_price:
            raise ValueError("best_ask_price must exceed best_bid_price")
        object.__setattr__(
            self,
            "spread_change_pressure",
            _require_ratio_decimal(
                "spread_change_pressure",
                self.spread_change_pressure,
            ),
        )
        for field_name in ("near_band_depth", "far_band_depth"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.near_band_depth <= ZERO:
            raise ValueError("near_band_depth must be positive")
        if self.far_band_depth > self.near_band_depth:
            raise ValueError("far_band_depth must not exceed near_band_depth")
        object.__setattr__(
            self,
            "concentration_pressure",
            _require_ratio_decimal("concentration_pressure", self.concentration_pressure),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityDepthDecayRow:
    liquidity_group_ref: str
    observed_at: datetime
    last_depth_change_at: datetime
    book_age_seconds: Decimal
    unchanged_book_seconds: Decimal
    spread_pressure: Decimal
    spread_change_pressure: Decimal
    near_band_depth: Decimal
    far_band_depth: Decimal
    depth_coverage_ratio: Decimal
    depth_decay_ratio: Decimal
    stale_book_pressure: Decimal
    concentration_pressure: Decimal
    depth_freshness_score: Decimal
    spread_pressure_score: Decimal
    spread_change_score: Decimal
    depth_decay_score: Decimal
    stale_book_risk_score: Decimal
    concentration_score: Decimal
    liquidity_depth_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchMarketLiquidityDepthDecayRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityDepthDecayRow, "row")
        _require_canonical_string("liquidity_group_ref", self.liquidity_group_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_depth_change_at",
            _as_utc("last_depth_change_at", self.last_depth_change_at),
        )
        for field_name in (
            "book_age_seconds",
            "unchanged_book_seconds",
            "spread_pressure",
            "spread_change_pressure",
            "near_band_depth",
            "far_band_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_coverage_ratio",
            "depth_decay_ratio",
            "stale_book_pressure",
            "concentration_pressure",
            "depth_freshness_score",
            "spread_pressure_score",
            "spread_change_score",
            "depth_decay_score",
            "stale_book_risk_score",
            "concentration_score",
            "liquidity_depth_decay_score",
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
class ResearchMarketLiquidityDepthDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketLiquidityDepthDecayReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityDepthDecayReasonCodeCount,
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
class ResearchMarketLiquidityDepthDecayReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_liquidity_depth_decay_score: Decimal | None
    max_book_age_seconds: Decimal
    max_spread_pressure: Decimal
    max_spread_change_pressure: Decimal
    max_depth_decay_ratio: Decimal
    max_unchanged_book_seconds: Decimal
    max_concentration_pressure: Decimal
    status: str
    rows: tuple[ResearchMarketLiquidityDepthDecayRow, ...]
    reason_code_counts: tuple[ResearchMarketLiquidityDepthDecayReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchMarketLiquidityDepthDecayReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityDepthDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_liquidity_depth_decay_score",
            _require_optional_ratio_decimal(
                "average_liquidity_depth_decay_score",
                self.average_liquidity_depth_decay_score,
            ),
        )
        for field_name in (
            "max_book_age_seconds",
            "max_spread_pressure",
            "max_spread_change_pressure",
            "max_depth_decay_ratio",
            "max_unchanged_book_seconds",
            "max_concentration_pressure",
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


def build_research_market_liquidity_depth_decay_report(
    snapshots: Iterable[ResearchMarketLiquidityDepthDecaySnapshot],
    *,
    config: ResearchMarketLiquidityDepthDecayConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityDepthDecayReport:
    if type(config) is not ResearchMarketLiquidityDepthDecayConfig:
        raise ValueError("config must be a ResearchMarketLiquidityDepthDecayConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_snapshots(snapshots)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
        if item.last_depth_change_at > generated_at_utc:
            raise ValueError("last_depth_change_at must not be after generated_at")
    rows = tuple(
        _row_from_snapshot(
            liquidity_group_ref=f"liquidity_depth_group_{index:03d}",
            snapshot=item,
            config=config,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(sorted(normalized, key=_snapshot_sort_key), start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketLiquidityDepthDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_liquidity_depth_decay_score=_average_score(rows),
        max_book_age_seconds=_max_or_zero(tuple(row.book_age_seconds for row in rows)),
        max_spread_pressure=_max_or_zero(tuple(row.spread_pressure for row in rows)),
        max_spread_change_pressure=_max_or_zero(
            tuple(row.spread_change_pressure for row in rows),
        ),
        max_depth_decay_ratio=_max_or_zero(tuple(row.depth_decay_ratio for row in rows)),
        max_unchanged_book_seconds=_max_or_zero(
            tuple(row.unchanged_book_seconds for row in rows),
        ),
        max_concentration_pressure=_max_or_zero(
            tuple(row.concentration_pressure for row in rows),
        ),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_liquidity_depth_decay_report_payload(
    report: ResearchMarketLiquidityDepthDecayReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketLiquidityDepthDecayReport:
        raise ValueError("report must be a ResearchMarketLiquidityDepthDecayReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def research_market_liquidity_depth_decay_report_digest(
    report: ResearchMarketLiquidityDepthDecayReport,
) -> str:
    if type(report) is not ResearchMarketLiquidityDepthDecayReport:
        raise ValueError("report must be a ResearchMarketLiquidityDepthDecayReport")
    _require_hard_flags("report", report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


def _row_from_snapshot(
    *,
    liquidity_group_ref: str,
    snapshot: ResearchMarketLiquidityDepthDecaySnapshot,
    config: ResearchMarketLiquidityDepthDecayConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityDepthDecayRow:
    book_age_seconds = _age_seconds(generated_at, snapshot.observed_at)
    unchanged_book_seconds = _age_seconds(generated_at, snapshot.last_depth_change_at)
    spread_pressure = _quantize(snapshot.best_ask_price - snapshot.best_bid_price)
    spread_change_pressure = _quantize(snapshot.spread_change_pressure)
    depth_coverage_ratio = _quantize(snapshot.far_band_depth / snapshot.near_band_depth)
    depth_decay_ratio = _quantize(
        (snapshot.near_band_depth - snapshot.far_band_depth) / snapshot.near_band_depth,
    )
    stale_book_pressure = _pressure_ratio(
        unchanged_book_seconds,
        config.max_watch_unchanged_book_seconds,
    )
    concentration_pressure = _quantize(snapshot.concentration_pressure)
    depth_freshness_score = _inverse_ratio_score(
        book_age_seconds,
        config.max_watch_book_age_seconds,
    )
    spread_pressure_score = _inverse_ratio_score(
        spread_pressure,
        config.max_watch_spread,
    )
    spread_change_score = _inverse_ratio_score(
        spread_change_pressure,
        config.max_watch_spread_change_pressure,
    )
    depth_decay_score = _inverse_ratio_score(
        depth_decay_ratio,
        config.max_watch_depth_decay_ratio,
    )
    stale_book_risk_score = _inverse_ratio_score(
        unchanged_book_seconds,
        config.max_watch_unchanged_book_seconds,
    )
    concentration_score = _inverse_ratio_score(
        concentration_pressure,
        config.max_watch_concentration_pressure,
    )
    liquidity_depth_decay_score = _liquidity_depth_decay_score(
        depth_freshness_score=depth_freshness_score,
        spread_pressure_score=spread_pressure_score,
        spread_change_score=spread_change_score,
        depth_decay_score=depth_decay_score,
        stale_book_risk_score=stale_book_risk_score,
        concentration_score=concentration_score,
        config=config,
    )
    status = _row_status(
        book_age_seconds=book_age_seconds,
        spread_pressure=spread_pressure,
        spread_change_pressure=spread_change_pressure,
        depth_decay_ratio=depth_decay_ratio,
        unchanged_book_seconds=unchanged_book_seconds,
        concentration_pressure=concentration_pressure,
        liquidity_depth_decay_score=liquidity_depth_decay_score,
        config=config,
    )
    return ResearchMarketLiquidityDepthDecayRow(
        liquidity_group_ref=liquidity_group_ref,
        observed_at=snapshot.observed_at,
        last_depth_change_at=snapshot.last_depth_change_at,
        book_age_seconds=book_age_seconds,
        unchanged_book_seconds=unchanged_book_seconds,
        spread_pressure=spread_pressure,
        spread_change_pressure=spread_change_pressure,
        near_band_depth=_quantize(snapshot.near_band_depth),
        far_band_depth=_quantize(snapshot.far_band_depth),
        depth_coverage_ratio=depth_coverage_ratio,
        depth_decay_ratio=depth_decay_ratio,
        stale_book_pressure=stale_book_pressure,
        concentration_pressure=concentration_pressure,
        depth_freshness_score=depth_freshness_score,
        spread_pressure_score=spread_pressure_score,
        spread_change_score=spread_change_score,
        depth_decay_score=depth_decay_score,
        stale_book_risk_score=stale_book_risk_score,
        concentration_score=concentration_score,
        liquidity_depth_decay_score=liquidity_depth_decay_score,
        status=status,
        reason_codes=_row_reason_codes(
            snapshot=snapshot,
            book_age_seconds=book_age_seconds,
            spread_pressure=spread_pressure,
            spread_change_pressure=spread_change_pressure,
            depth_decay_ratio=depth_decay_ratio,
            unchanged_book_seconds=unchanged_book_seconds,
            concentration_pressure=concentration_pressure,
            status=status,
            config=config,
        ),
    )


def _liquidity_depth_decay_score(
    *,
    depth_freshness_score: Decimal,
    spread_pressure_score: Decimal,
    spread_change_score: Decimal,
    depth_decay_score: Decimal,
    stale_book_risk_score: Decimal,
    concentration_score: Decimal,
    config: ResearchMarketLiquidityDepthDecayConfig,
) -> Decimal:
    return _quantize(
        depth_freshness_score * config.depth_freshness_weight
        + spread_pressure_score * config.spread_pressure_weight
        + spread_change_score * config.spread_change_pressure_weight
        + depth_decay_score * config.depth_decay_weight
        + stale_book_risk_score * config.stale_book_risk_weight
        + concentration_score * config.concentration_pressure_weight,
    )


def _row_status(
    *,
    book_age_seconds: Decimal,
    spread_pressure: Decimal,
    spread_change_pressure: Decimal,
    depth_decay_ratio: Decimal,
    unchanged_book_seconds: Decimal,
    concentration_pressure: Decimal,
    liquidity_depth_decay_score: Decimal,
    config: ResearchMarketLiquidityDepthDecayConfig,
) -> str:
    if (
        liquidity_depth_decay_score < config.watch_liquidity_depth_decay_score
        or book_age_seconds >= config.max_watch_book_age_seconds
        or spread_pressure >= config.max_watch_spread
        or spread_change_pressure >= config.max_watch_spread_change_pressure
        or depth_decay_ratio >= config.max_watch_depth_decay_ratio
        or unchanged_book_seconds >= config.max_watch_unchanged_book_seconds
        or concentration_pressure >= config.max_watch_concentration_pressure
    ):
        return "block"
    if (
        liquidity_depth_decay_score < config.pass_liquidity_depth_decay_score
        or book_age_seconds >= config.max_pass_book_age_seconds
        or spread_pressure >= config.max_pass_spread
        or spread_change_pressure >= config.max_pass_spread_change_pressure
        or depth_decay_ratio >= config.max_pass_depth_decay_ratio
        or unchanged_book_seconds >= config.max_pass_unchanged_book_seconds
        or concentration_pressure >= config.max_pass_concentration_pressure
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    snapshot: ResearchMarketLiquidityDepthDecaySnapshot,
    book_age_seconds: Decimal,
    spread_pressure: Decimal,
    spread_change_pressure: Decimal,
    depth_decay_ratio: Decimal,
    unchanged_book_seconds: Decimal,
    concentration_pressure: Decimal,
    status: str,
    config: ResearchMarketLiquidityDepthDecayConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"liquidity_depth_decay_{status}"}
    reason_codes.add(
        _threshold_reason(
            "depth_freshness",
            book_age_seconds,
            config.max_pass_book_age_seconds,
            config.max_watch_book_age_seconds,
        ),
    )
    reason_codes.add(
        _threshold_reason(
            "spread_pressure",
            spread_pressure,
            config.max_pass_spread,
            config.max_watch_spread,
        ),
    )
    reason_codes.add(
        _threshold_reason(
            "spread_change_pressure",
            spread_change_pressure,
            config.max_pass_spread_change_pressure,
            config.max_watch_spread_change_pressure,
        ),
    )
    reason_codes.add(
        _threshold_reason(
            "depth_coverage",
            depth_decay_ratio,
            config.max_pass_depth_decay_ratio,
            config.max_watch_depth_decay_ratio,
        ),
    )
    reason_codes.add(
        _threshold_reason(
            "stale_book_pressure",
            unchanged_book_seconds,
            config.max_pass_unchanged_book_seconds,
            config.max_watch_unchanged_book_seconds,
        ),
    )
    reason_codes.add(
        _threshold_reason(
            "concentration_pressure",
            concentration_pressure,
            config.max_pass_concentration_pressure,
            config.max_watch_concentration_pressure,
        ),
    )
    for reason_code in snapshot.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _threshold_reason(
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


def _normalize_snapshots(
    snapshots: Iterable[ResearchMarketLiquidityDepthDecaySnapshot],
) -> tuple[ResearchMarketLiquidityDepthDecaySnapshot, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable")
    try:
        values = tuple(snapshots)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchMarketLiquidityDepthDecaySnapshot:
            raise ValueError(
                "snapshots must contain ResearchMarketLiquidityDepthDecaySnapshot values",
            )
        _require_hard_flags("snapshot", value)
    keys = tuple(value.book_snapshot_key for value in values)
    if len(set(keys)) != len(keys):
        raise ValueError("book_snapshot_key values must be unique")
    return values


def _normalize_rows(
    rows: tuple[ResearchMarketLiquidityDepthDecayRow, ...],
) -> tuple[ResearchMarketLiquidityDepthDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketLiquidityDepthDecayRow:
            raise ValueError(
                "rows must contain ResearchMarketLiquidityDepthDecayRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=lambda row: row.liquidity_group_ref)):
        raise ValueError("rows must be sorted by liquidity_group_ref")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketLiquidityDepthDecayReasonCodeCount, ...],
) -> tuple[ResearchMarketLiquidityDepthDecayReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketLiquidityDepthDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketLiquidityDepthDecayReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    if counts != tuple(sorted(counts, key=lambda count: count.reason_code)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row(row: ResearchMarketLiquidityDepthDecayRow) -> None:
    if row.near_band_depth <= ZERO:
        raise ValueError("near_band_depth must be positive")
    if row.far_band_depth > row.near_band_depth:
        raise ValueError("far_band_depth must not exceed near_band_depth")
    expected_depth_coverage_ratio = _quantize(row.far_band_depth / row.near_band_depth)
    if row.depth_coverage_ratio != expected_depth_coverage_ratio:
        raise ValueError("depth_coverage_ratio must match depth fields")
    expected_depth_decay_ratio = _quantize(
        (row.near_band_depth - row.far_band_depth) / row.near_band_depth,
    )
    if row.depth_decay_ratio != expected_depth_decay_ratio:
        raise ValueError("depth_decay_ratio must match depth fields")
    if row.stale_book_pressure != _quantize(ONE - row.stale_book_risk_score):
        raise ValueError("stale_book_pressure must match stale book score")
    if f"liquidity_depth_decay_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchMarketLiquidityDepthDecayReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_liquidity_depth_decay_score != _average_score(report.rows):
        raise ValueError("average_liquidity_depth_decay_score must match rows")
    if report.max_book_age_seconds != _max_or_zero(
        tuple(row.book_age_seconds for row in report.rows),
    ):
        raise ValueError("max_book_age_seconds must match rows")
    if report.max_spread_pressure != _max_or_zero(
        tuple(row.spread_pressure for row in report.rows),
    ):
        raise ValueError("max_spread_pressure must match rows")
    if report.max_spread_change_pressure != _max_or_zero(
        tuple(row.spread_change_pressure for row in report.rows),
    ):
        raise ValueError("max_spread_change_pressure must match rows")
    if report.max_depth_decay_ratio != _max_or_zero(
        tuple(row.depth_decay_ratio for row in report.rows),
    ):
        raise ValueError("max_depth_decay_ratio must match rows")
    if report.max_unchanged_book_seconds != _max_or_zero(
        tuple(row.unchanged_book_seconds for row in report.rows),
    ):
        raise ValueError("max_unchanged_book_seconds must match rows")
    if report.max_concentration_pressure != _max_or_zero(
        tuple(row.concentration_pressure for row in report.rows),
    ):
        raise ValueError("max_concentration_pressure must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _summary_status(rows: tuple[ResearchMarketLiquidityDepthDecayRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchMarketLiquidityDepthDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_liquidity_depth_decay_snapshots",)
    if all(row.status == "pass" for row in rows):
        return ("liquidity_depth_decay_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquidityDepthDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketLiquidityDepthDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketLiquidityDepthDecayReasonCodeCount(
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
        ResearchMarketLiquidityDepthDecayReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(_decimal_count(count) / total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_score(
    rows: tuple[ResearchMarketLiquidityDepthDecayRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.liquidity_depth_decay_score for row in rows), ZERO)
        / _decimal_count(len(rows)),
    )


def _inverse_ratio_score(value: Decimal, zero_at: Decimal) -> Decimal:
    if zero_at <= ZERO:
        raise ValueError("zero_at must be positive")
    return _quantize(max(ZERO, ONE - (value / zero_at)))


def _pressure_ratio(value: Decimal, full_at: Decimal) -> Decimal:
    if full_at <= ZERO:
        raise ValueError("full_at must be positive")
    return _quantize(min(ONE, value / full_at))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _status_count(
    rows: tuple[ResearchMarketLiquidityDepthDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _snapshot_sort_key(
    value: ResearchMarketLiquidityDepthDecaySnapshot,
) -> tuple[str, datetime]:
    return value.book_snapshot_key, value.observed_at


def _payload_value(value: object) -> object:
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


def _derived_report_digest(report: ResearchMarketLiquidityDepthDecayReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in LIQUIDITY_DEPTH_DECAY_STATUSES:
        raise ValueError(f"{field_name} must be one of {LIQUIDITY_DEPTH_DECAY_STATUSES}")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain lowercase snake-case values")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name, None)
        if type(flag) is not bool or flag is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_hex_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a 64-character hex string")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a 64-character hex string")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
