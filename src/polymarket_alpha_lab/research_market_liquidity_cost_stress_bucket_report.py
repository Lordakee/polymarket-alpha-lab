"""Report-only liquidity and cost stress bucketing for public research surfaces."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


CONFIG_VERSION = "research-market-liquidity-cost-stress-bucket-report-v0"
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HALF = Decimal("0.500000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

DEPTH_BAND_DEEP = "deep"
DEPTH_BAND_THIN = "thin"
DEPTH_BAND_FRAGILE = "fragile"
DEPTH_BANDS = (DEPTH_BAND_DEEP, DEPTH_BAND_THIN, DEPTH_BAND_FRAGILE)

REASON_PASS = "liquidity_cost_stress_pass"
REASON_WATCH = "liquidity_cost_stress_watch"
REASON_BLOCK = "liquidity_cost_stress_block"
REASON_SPREAD_WATCH = "spread_watch"
REASON_SPREAD_BLOCK = "spread_block"
REASON_DEPTH_THIN = "depth_thin_watch"
REASON_DEPTH_FRAGILE = "depth_fragile_block"
REASON_FEE_WATCH = "fee_drag_watch"
REASON_FEE_BLOCK = "fee_drag_block"
REASON_SLIPPAGE_WATCH = "slippage_cushion_watch"
REASON_SLIPPAGE_BLOCK = "slippage_cushion_block"
REASON_AGE_WATCH = "book_age_watch"
REASON_AGE_BLOCK = "book_age_block"
REASON_VOLATILITY_WATCH = "volatility_watch"
REASON_VOLATILITY_BLOCK = "volatility_block"
REASON_SETTLEMENT_WATCH = "settlement_friction_watch"
REASON_SETTLEMENT_BLOCK = "settlement_friction_block"
REASON_CODES = frozenset(
    (
        REASON_PASS,
        REASON_WATCH,
        REASON_BLOCK,
        REASON_SPREAD_WATCH,
        REASON_SPREAD_BLOCK,
        REASON_DEPTH_THIN,
        REASON_DEPTH_FRAGILE,
        REASON_FEE_WATCH,
        REASON_FEE_BLOCK,
        REASON_SLIPPAGE_WATCH,
        REASON_SLIPPAGE_BLOCK,
        REASON_AGE_WATCH,
        REASON_AGE_BLOCK,
        REASON_VOLATILITY_WATCH,
        REASON_VOLATILITY_BLOCK,
        REASON_SETTLEMENT_WATCH,
        REASON_SETTLEMENT_BLOCK,
    ),
)

_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("acc", "ount"),
    _join_parts("api", "_key"),
    "auth",
    _join_parts("bro", "ker"),
    "buy",
    _join_parts("can", "cel"),
    "candidate",
    _join_parts("cli", "ent"),
    "condition_id",
    _join_parts("data", "base"),
    "credential",
    "execution",
    _join_parts("file", "_path"),
    "market_id",
    "market_slug",
    _join_parts("net", "work"),
    "position",
    "private",
    _join_parts("per", "sist"),
    "recommend",
    _join_parts("repl", "ace"),
    "slug",
    "question",
    "secret",
    "sell",
    "sizing",
    "source_id",
    "source_identifier",
    "source_ref",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
)


__all__ = (
    "ResearchMarketLiquidityCostStressBucketConfig",
    "ResearchMarketLiquidityCostStressBucketInput",
    "ResearchMarketLiquidityCostStressBucketRow",
    "ResearchMarketLiquidityCostStressBucketReasonCodeCount",
    "ResearchMarketLiquidityCostStressBucketReport",
    "build_research_market_liquidity_cost_stress_bucket_report",
    "research_market_liquidity_cost_stress_bucket_payload",
)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostStressBucketConfig:
    config_version: str = CONFIG_VERSION
    spread_watch_threshold: Decimal = Decimal("0.030000")
    spread_block_threshold: Decimal = Decimal("0.070000")
    thin_depth_floor_usdc: Decimal = Decimal("500.000000")
    deep_depth_floor_usdc: Decimal = Decimal("2000.000000")
    fee_drag_watch_threshold: Decimal = Decimal("0.025000")
    fee_drag_block_threshold: Decimal = Decimal("0.060000")
    slippage_cushion_watch_floor: Decimal = Decimal("0.020000")
    slippage_cushion_block_floor: Decimal = Decimal("0.005000")
    book_age_watch_seconds: Decimal = Decimal("300.000000")
    book_age_block_seconds: Decimal = Decimal("900.000000")
    volatility_watch_threshold: Decimal = Decimal("0.250000")
    volatility_block_threshold: Decimal = Decimal("0.500000")
    settlement_friction_watch_threshold: Decimal = Decimal("0.100000")
    settlement_friction_block_threshold: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostStressBucketConfig:
            raise TypeError(
                "ResearchMarketLiquidityCostStressBucketConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityCostStressBucketConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "spread_watch_threshold",
            "spread_block_threshold",
            "fee_drag_watch_threshold",
            "fee_drag_block_threshold",
            "slippage_cushion_watch_floor",
            "slippage_cushion_block_floor",
            "volatility_watch_threshold",
            "volatility_block_threshold",
            "settlement_friction_watch_threshold",
            "settlement_friction_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _rate(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "thin_depth_floor_usdc",
            "deep_depth_floor_usdc",
            "book_age_watch_seconds",
            "book_age_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ordered_thresholds(
            "spread thresholds",
            self.spread_watch_threshold,
            self.spread_block_threshold,
        )
        _require_ordered_thresholds(
            "fee drag thresholds",
            self.fee_drag_watch_threshold,
            self.fee_drag_block_threshold,
        )
        _require_descending_floors(
            "slippage cushion floors",
            self.slippage_cushion_watch_floor,
            self.slippage_cushion_block_floor,
        )
        _require_ordered_thresholds(
            "book age thresholds",
            self.book_age_watch_seconds,
            self.book_age_block_seconds,
        )
        _require_ordered_thresholds(
            "volatility thresholds",
            self.volatility_watch_threshold,
            self.volatility_block_threshold,
        )
        _require_ordered_thresholds(
            "settlement friction thresholds",
            self.settlement_friction_watch_threshold,
            self.settlement_friction_block_threshold,
        )
        if self.deep_depth_floor_usdc <= self.thin_depth_floor_usdc:
            raise ValueError("deep_depth_floor_usdc must exceed thin_depth_floor_usdc")
        _require_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostStressBucketInput:
    surface_group: str
    category: str
    spread_rate: Decimal
    available_depth_usdc: Decimal
    fee_drag_rate: Decimal
    slippage_cushion_rate: Decimal
    book_age_seconds: Decimal
    volatility_rate: Decimal
    settlement_friction_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostStressBucketInput:
            raise TypeError(
                "ResearchMarketLiquidityCostStressBucketInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityCostStressBucketInput, "input")
        for field_name in ("surface_group", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "spread_rate",
            "fee_drag_rate",
            "slippage_cushion_rate",
            "volatility_rate",
            "settlement_friction_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _rate(field_name, getattr(self, field_name)),
            )
        for field_name in ("available_depth_usdc", "book_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostStressBucketRow:
    surface_group: str
    category: str
    spread_rate: Decimal
    available_depth_usdc: Decimal
    depth_band: str
    fee_drag_rate: Decimal
    slippage_cushion_rate: Decimal
    book_age_seconds: Decimal
    volatility_rate: Decimal
    settlement_friction_rate: Decimal
    spread_status: str
    depth_status: str
    fee_drag_status: str
    slippage_cushion_status: str
    book_age_status: str
    volatility_status: str
    settlement_friction_status: str
    stress_score: Decimal
    status: str
    stress_bucket: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostStressBucketRow:
            raise TypeError(
                "ResearchMarketLiquidityCostStressBucketRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityCostStressBucketRow, "row")
        for field_name in ("surface_group", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "spread_rate",
            "fee_drag_rate",
            "slippage_cushion_rate",
            "volatility_rate",
            "settlement_friction_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _rate(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "available_depth_usdc",
            "book_age_seconds",
            "stress_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("depth_band", self.depth_band, DEPTH_BANDS)
        for field_name in (
            "spread_status",
            "depth_status",
            "fee_drag_status",
            "slippage_cushion_status",
            "book_age_status",
            "volatility_status",
            "settlement_friction_status",
            "status",
            "stress_bucket",
        ):
            _require_choice(field_name, getattr(self, field_name), STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_flags("row", self)
        _set_or_validate_digest(self, "row")


@dataclass(frozen=True)
class ResearchMarketLiquidityCostStressBucketReasonCodeCount:
    reason_code: str
    row_count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostStressBucketReasonCodeCount:
            raise TypeError(
                "ResearchMarketLiquidityCostStressBucketReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityCostStressBucketReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "row_count", _count_decimal("row_count", self.row_count))
        object.__setattr__(self, "row_ratio", _rate("row_ratio", self.row_ratio))
        _require_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostStressBucketReport:
    generated_at: datetime
    config_version: str
    report_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    wide_spread_count: Decimal
    thin_depth_count: Decimal
    fragile_depth_count: Decimal
    high_fee_drag_count: Decimal
    low_slippage_cushion_count: Decimal
    stale_book_count: Decimal
    volatile_book_count: Decimal
    settlement_friction_count: Decimal
    max_stress_score: Decimal
    rows: tuple[ResearchMarketLiquidityCostStressBucketRow, ...]
    reason_code_counts: tuple[ResearchMarketLiquidityCostStressBucketReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostStressBucketReport:
            raise TypeError(
                "ResearchMarketLiquidityCostStressBucketReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityCostStressBucketReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_choice("report_status", self.report_status, STATUSES)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "wide_spread_count",
            "thin_depth_count",
            "fragile_depth_count",
            "high_fee_drag_count",
            "low_slippage_cushion_count",
            "stale_book_count",
            "volatile_book_count",
            "settlement_friction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_stress_score",
            _rate("max_stress_score", self.max_stress_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_flags("report", self)
        _set_or_validate_digest(self, "report")


def build_research_market_liquidity_cost_stress_bucket_report(
    rows: Iterable[ResearchMarketLiquidityCostStressBucketInput],
    *,
    generated_at: datetime,
    config: ResearchMarketLiquidityCostStressBucketConfig,
) -> ResearchMarketLiquidityCostStressBucketReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    if type(config) is not ResearchMarketLiquidityCostStressBucketConfig:
        raise ValueError(
            "config must be exactly ResearchMarketLiquidityCostStressBucketConfig",
        )
    ResearchMarketLiquidityCostStressBucketConfig.__post_init__(config)
    report_rows = tuple(
        sorted(
            (_row_from_input(row, config=config) for row in _normalize_inputs(rows)),
            key=_row_sort_key,
        ),
    )
    row_count = _decimal_count(len(report_rows))
    return ResearchMarketLiquidityCostStressBucketReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(report_rows),
        row_count=row_count,
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        wide_spread_count=_decimal_count(
            sum(1 for row in report_rows if row.spread_status != STATUS_PASS),
        ),
        thin_depth_count=_decimal_count(
            sum(1 for row in report_rows if row.depth_band == DEPTH_BAND_THIN),
        ),
        fragile_depth_count=_decimal_count(
            sum(1 for row in report_rows if row.depth_band == DEPTH_BAND_FRAGILE),
        ),
        high_fee_drag_count=_decimal_count(
            sum(1 for row in report_rows if row.fee_drag_status != STATUS_PASS),
        ),
        low_slippage_cushion_count=_decimal_count(
            sum(1 for row in report_rows if row.slippage_cushion_status != STATUS_PASS),
        ),
        stale_book_count=_decimal_count(
            sum(1 for row in report_rows if row.book_age_status != STATUS_PASS),
        ),
        volatile_book_count=_decimal_count(
            sum(1 for row in report_rows if row.volatility_status != STATUS_PASS),
        ),
        settlement_friction_count=_decimal_count(
            sum(1 for row in report_rows if row.settlement_friction_status != STATUS_PASS),
        ),
        max_stress_score=max((row.stress_score for row in report_rows), default=ZERO),
        rows=report_rows,
        reason_code_counts=_reason_code_counts(report_rows, row_count),
    )


def research_market_liquidity_cost_stress_bucket_payload(
    report: ResearchMarketLiquidityCostStressBucketReport | dict[str, Any],
) -> "FrozenJsonObject":
    validate_digest = False
    if type(report) is ResearchMarketLiquidityCostStressBucketReport:
        _require_flags("report", report)
        _validate_report_consistency(report)
        if report.derived_validation_digest != _digest_for_dataclass(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_canonical_public_scalars(report)
        payload = _json_ready(report)
        validate_digest = True
    else:
        raise ValueError(
            "report must be exactly ResearchMarketLiquidityCostStressBucketReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_shape(payload)
    if validate_digest:
        _validate_payload_digest(payload)
    _validate_public_payload_consistency(payload)
    return _freeze_json_object(payload)


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


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
    row: ResearchMarketLiquidityCostStressBucketInput,
    *,
    config: ResearchMarketLiquidityCostStressBucketConfig,
) -> ResearchMarketLiquidityCostStressBucketRow:
    if type(row) is not ResearchMarketLiquidityCostStressBucketInput:
        raise ValueError(
            "rows must contain ResearchMarketLiquidityCostStressBucketInput values",
        )
    _require_flags("input", row)
    depth_band, depth_status = _depth_band_and_status(row.available_depth_usdc, config)
    dimension_statuses = (
        _threshold_status(
            row.spread_rate,
            watch_threshold=config.spread_watch_threshold,
            block_threshold=config.spread_block_threshold,
        ),
        depth_status,
        _threshold_status(
            row.fee_drag_rate,
            watch_threshold=config.fee_drag_watch_threshold,
            block_threshold=config.fee_drag_block_threshold,
        ),
        _floor_status(
            row.slippage_cushion_rate,
            watch_floor=config.slippage_cushion_watch_floor,
            block_floor=config.slippage_cushion_block_floor,
        ),
        _threshold_status(
            row.book_age_seconds,
            watch_threshold=config.book_age_watch_seconds,
            block_threshold=config.book_age_block_seconds,
        ),
        _threshold_status(
            row.volatility_rate,
            watch_threshold=config.volatility_watch_threshold,
            block_threshold=config.volatility_block_threshold,
        ),
        _threshold_status(
            row.settlement_friction_rate,
            watch_threshold=config.settlement_friction_watch_threshold,
            block_threshold=config.settlement_friction_block_threshold,
        ),
    )
    status = _combined_status(dimension_statuses)
    return ResearchMarketLiquidityCostStressBucketRow(
        surface_group=row.surface_group,
        category=row.category,
        spread_rate=row.spread_rate,
        available_depth_usdc=row.available_depth_usdc,
        depth_band=depth_band,
        fee_drag_rate=row.fee_drag_rate,
        slippage_cushion_rate=row.slippage_cushion_rate,
        book_age_seconds=row.book_age_seconds,
        volatility_rate=row.volatility_rate,
        settlement_friction_rate=row.settlement_friction_rate,
        spread_status=dimension_statuses[0],
        depth_status=dimension_statuses[1],
        fee_drag_status=dimension_statuses[2],
        slippage_cushion_status=dimension_statuses[3],
        book_age_status=dimension_statuses[4],
        volatility_status=dimension_statuses[5],
        settlement_friction_status=dimension_statuses[6],
        stress_score=_stress_score(dimension_statuses),
        status=status,
        stress_bucket=status,
        reason_codes=_reason_codes(
            spread_status=dimension_statuses[0],
            depth_status=dimension_statuses[1],
            depth_band=depth_band,
            fee_drag_status=dimension_statuses[2],
            slippage_cushion_status=dimension_statuses[3],
            book_age_status=dimension_statuses[4],
            volatility_status=dimension_statuses[5],
            settlement_friction_status=dimension_statuses[6],
            status=status,
        ),
    )


def _normalize_inputs(
    rows: Iterable[ResearchMarketLiquidityCostStressBucketInput],
) -> tuple[ResearchMarketLiquidityCostStressBucketInput, ...]:
    if isinstance(rows, (str, bytes, dict)):
        raise ValueError("rows must be an iterable of inputs")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of inputs") from exc
    identities: set[tuple[str, str]] = set()
    for row in values:
        if type(row) is not ResearchMarketLiquidityCostStressBucketInput:
            raise ValueError(
                "rows must contain ResearchMarketLiquidityCostStressBucketInput values",
            )
        ResearchMarketLiquidityCostStressBucketInput.__post_init__(row)
        identity = (row.category, row.surface_group)
        if identity in identities:
            raise ValueError("rows must not contain duplicate public row identity")
        identities.add(identity)
    return values


def _depth_band_and_status(
    available_depth_usdc: Decimal,
    config: ResearchMarketLiquidityCostStressBucketConfig,
) -> tuple[str, str]:
    if available_depth_usdc < config.thin_depth_floor_usdc:
        return DEPTH_BAND_FRAGILE, STATUS_BLOCK
    if available_depth_usdc < config.deep_depth_floor_usdc:
        return DEPTH_BAND_THIN, STATUS_WATCH
    return DEPTH_BAND_DEEP, STATUS_PASS


def _threshold_status(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        return STATUS_BLOCK
    if value >= watch_threshold:
        return STATUS_WATCH
    return STATUS_PASS


def _floor_status(value: Decimal, *, watch_floor: Decimal, block_floor: Decimal) -> str:
    if value <= block_floor:
        return STATUS_BLOCK
    if value <= watch_floor:
        return STATUS_WATCH
    return STATUS_PASS


def _combined_status(statuses: tuple[str, ...]) -> str:
    if STATUS_BLOCK in statuses:
        return STATUS_BLOCK
    if STATUS_WATCH in statuses:
        return STATUS_WATCH
    return STATUS_PASS


def _stress_score(statuses: tuple[str, ...]) -> Decimal:
    score = sum(_status_score(status) for status in statuses)
    return _quantize(score / Decimal(len(statuses)))


def _status_score(status: str) -> Decimal:
    if status == STATUS_BLOCK:
        return ONE
    if status == STATUS_WATCH:
        return HALF
    return ZERO


def _reason_codes(
    *,
    spread_status: str,
    depth_status: str,
    depth_band: str,
    fee_drag_status: str,
    slippage_cushion_status: str,
    book_age_status: str,
    volatility_status: str,
    settlement_friction_status: str,
    status: str,
) -> tuple[str, ...]:
    if status == STATUS_PASS:
        return (REASON_PASS,)
    reasons = [REASON_BLOCK if status == STATUS_BLOCK else REASON_WATCH]
    _append_status_reason(
        reasons,
        status=spread_status,
        watch_reason=REASON_SPREAD_WATCH,
        block_reason=REASON_SPREAD_BLOCK,
    )
    if depth_status == STATUS_BLOCK and depth_band == DEPTH_BAND_FRAGILE:
        reasons.append(REASON_DEPTH_FRAGILE)
    elif depth_status == STATUS_WATCH and depth_band == DEPTH_BAND_THIN:
        reasons.append(REASON_DEPTH_THIN)
    _append_status_reason(
        reasons,
        status=fee_drag_status,
        watch_reason=REASON_FEE_WATCH,
        block_reason=REASON_FEE_BLOCK,
    )
    _append_status_reason(
        reasons,
        status=slippage_cushion_status,
        watch_reason=REASON_SLIPPAGE_WATCH,
        block_reason=REASON_SLIPPAGE_BLOCK,
    )
    _append_status_reason(
        reasons,
        status=book_age_status,
        watch_reason=REASON_AGE_WATCH,
        block_reason=REASON_AGE_BLOCK,
    )
    _append_status_reason(
        reasons,
        status=volatility_status,
        watch_reason=REASON_VOLATILITY_WATCH,
        block_reason=REASON_VOLATILITY_BLOCK,
    )
    _append_status_reason(
        reasons,
        status=settlement_friction_status,
        watch_reason=REASON_SETTLEMENT_WATCH,
        block_reason=REASON_SETTLEMENT_BLOCK,
    )
    return tuple(sorted(reasons))


def _append_status_reason(
    reasons: list[str],
    *,
    status: str,
    watch_reason: str,
    block_reason: str,
) -> None:
    if status == STATUS_BLOCK:
        reasons.append(block_reason)
    elif status == STATUS_WATCH:
        reasons.append(watch_reason)


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquidityCostStressBucketRow, ...],
    row_count: Decimal,
) -> tuple[ResearchMarketLiquidityCostStressBucketReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchMarketLiquidityCostStressBucketReasonCodeCount(
            reason_code=reason_code,
            row_count=_decimal_count(counter[reason_code]),
            row_ratio=_quantize(Decimal(counter[reason_code]) / row_count),
        )
        for reason_code in sorted(counter)
    )


def _status_count(
    rows: tuple[ResearchMarketLiquidityCostStressBucketRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _report_status(rows: tuple[ResearchMarketLiquidityCostStressBucketRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _row_sort_key(row: ResearchMarketLiquidityCostStressBucketRow) -> tuple[int, str, str]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[row.status],
        row.category,
        row.surface_group,
    )


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketLiquidityCostStressBucketRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    values = tuple(rows)
    if not all(type(row) is ResearchMarketLiquidityCostStressBucketRow for row in values):
        raise ValueError(
            "rows must contain ResearchMarketLiquidityCostStressBucketRow values",
        )
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    identities = {(row.category, row.surface_group) for row in values}
    if len(identities) != len(values):
        raise ValueError("rows must not contain duplicate public row identity")
    return values


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchMarketLiquidityCostStressBucketReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    values = tuple(counts)
    if not all(
        type(item) is ResearchMarketLiquidityCostStressBucketReasonCodeCount
        for item in values
    ):
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchMarketLiquidityCostStressBucketReasonCodeCount values",
        )
    if values != tuple(sorted(values, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must be sorted")
    return values


def _normalize_reason_codes(value: object, *, allow_empty: bool) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    codes = tuple(value)
    if not allow_empty and not codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    for code in codes:
        _require_reason_code("reason_codes", code)
    if codes != tuple(sorted(codes)):
        raise ValueError("reason_codes must be sorted")
    return codes


def _validate_row_consistency(row: ResearchMarketLiquidityCostStressBucketRow) -> None:
    if row.stress_bucket != row.status:
        raise ValueError("stress_bucket must match status")
    expected_statuses = (
        row.spread_status,
        row.depth_status,
        row.fee_drag_status,
        row.slippage_cushion_status,
        row.book_age_status,
        row.volatility_status,
        row.settlement_friction_status,
    )
    if row.status != _combined_status(expected_statuses):
        raise ValueError("status does not match dimension statuses")
    if row.stress_score != _stress_score(expected_statuses):
        raise ValueError("stress_score does not match dimension statuses")
    if row.reason_codes != _reason_codes(
        spread_status=row.spread_status,
        depth_status=row.depth_status,
        depth_band=row.depth_band,
        fee_drag_status=row.fee_drag_status,
        slippage_cushion_status=row.slippage_cushion_status,
        book_age_status=row.book_age_status,
        volatility_status=row.volatility_status,
        settlement_friction_status=row.settlement_friction_status,
        status=row.status,
    ):
        raise ValueError("reason_codes do not match row status")


def _validate_report_consistency(
    report: ResearchMarketLiquidityCostStressBucketReport,
) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count does not match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count does not match rows")
    if report.wide_spread_count != _decimal_count(
        sum(1 for row in rows if row.spread_status != STATUS_PASS),
    ):
        raise ValueError("wide_spread_count does not match rows")
    if report.thin_depth_count != _decimal_count(
        sum(1 for row in rows if row.depth_band == DEPTH_BAND_THIN),
    ):
        raise ValueError("thin_depth_count does not match rows")
    if report.fragile_depth_count != _decimal_count(
        sum(1 for row in rows if row.depth_band == DEPTH_BAND_FRAGILE),
    ):
        raise ValueError("fragile_depth_count does not match rows")
    if report.high_fee_drag_count != _decimal_count(
        sum(1 for row in rows if row.fee_drag_status != STATUS_PASS),
    ):
        raise ValueError("high_fee_drag_count does not match rows")
    if report.low_slippage_cushion_count != _decimal_count(
        sum(1 for row in rows if row.slippage_cushion_status != STATUS_PASS),
    ):
        raise ValueError("low_slippage_cushion_count does not match rows")
    if report.stale_book_count != _decimal_count(
        sum(1 for row in rows if row.book_age_status != STATUS_PASS),
    ):
        raise ValueError("stale_book_count does not match rows")
    if report.volatile_book_count != _decimal_count(
        sum(1 for row in rows if row.volatility_status != STATUS_PASS),
    ):
        raise ValueError("volatile_book_count does not match rows")
    if report.settlement_friction_count != _decimal_count(
        sum(1 for row in rows if row.settlement_friction_status != STATUS_PASS),
    ):
        raise ValueError("settlement_friction_count does not match rows")
    if report.max_stress_score != max((row.stress_score for row in rows), default=ZERO):
        raise ValueError("max_stress_score does not match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status does not match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.row_count):
        raise ValueError("reason_code_counts do not match rows")


def _set_or_validate_digest(value: object, label: str) -> None:
    existing = getattr(value, "derived_validation_digest")
    if existing == "":
        object.__setattr__(value, "derived_validation_digest", _digest_for_dataclass(value))
        return
    _require_digest("derived_validation_digest", existing)
    if existing != _digest_for_dataclass(value):
        raise ValueError(f"derived_validation_digest does not match {label} payload")


def _digest_for_dataclass(value: object) -> str:
    payload: dict[str, Any] = {}
    for field in fields(value):
        if field.name == "derived_validation_digest":
            continue
        payload[field.name] = _json_ready(getattr(value, field.name))
    return _sha256_for_payload(payload)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    digest_payload = {
        key: item for key, item in payload.items() if key != "derived_validation_digest"
    }
    if digest != _sha256_for_payload(digest_payload):
        raise ValueError("derived_validation_digest does not match report payload")


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    _require_exact_keys("payload", payload, _json_field_names(ResearchMarketLiquidityCostStressBucketReport))
    _require_payload_datetime("generated_at", payload["generated_at"])
    _require_payload_string("config_version", payload["config_version"])
    if payload["config_version"] != CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    _require_choice("report_status", payload["report_status"], STATUSES)
    for field_name in (
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "wide_spread_count",
        "thin_depth_count",
        "fragile_depth_count",
        "high_fee_drag_count",
        "low_slippage_cushion_count",
        "stale_book_count",
        "volatile_book_count",
        "settlement_friction_count",
    ):
        _require_payload_decimal(field_name, payload[field_name])
    _require_payload_decimal("max_stress_score", payload["max_stress_score"])
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    _require_payload_flags("payload", payload)
    _validate_public_payload_rows(payload["rows"])
    _validate_public_reason_code_counts(payload["reason_code_counts"])


def _validate_public_payload_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must be a JSON array")
    for index, row in enumerate(value):
        row_path = f"rows[{index}]"
        if type(row) is not dict:
            raise ValueError(f"{row_path} must be a JSON object")
        _require_exact_keys(
            row_path,
            row,
            _json_field_names(ResearchMarketLiquidityCostStressBucketRow),
        )
        for field_name in ("surface_group", "category"):
            _require_payload_string(f"{row_path}.{field_name}", row[field_name])
        for field_name in (
            "spread_rate",
            "available_depth_usdc",
            "fee_drag_rate",
            "slippage_cushion_rate",
            "book_age_seconds",
            "volatility_rate",
            "settlement_friction_rate",
            "stress_score",
        ):
            _require_payload_decimal(f"{row_path}.{field_name}", row[field_name])
        _require_choice(f"{row_path}.depth_band", row["depth_band"], DEPTH_BANDS)
        for field_name in (
            "spread_status",
            "depth_status",
            "fee_drag_status",
            "slippage_cushion_status",
            "book_age_status",
            "volatility_status",
            "settlement_friction_status",
            "status",
            "stress_bucket",
        ):
            _require_choice(f"{row_path}.{field_name}", row[field_name], STATUSES)
        _require_payload_reason_codes(f"{row_path}.reason_codes", row["reason_codes"])
        _require_digest(
            f"{row_path}.derived_validation_digest",
            row["derived_validation_digest"],
        )
        _require_payload_flags(row_path, row)


def _validate_public_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a JSON array")
    for index, item in enumerate(value):
        item_path = f"reason_code_counts[{index}]"
        if type(item) is not dict:
            raise ValueError(f"{item_path} must be a JSON object")
        _require_exact_keys(
            item_path,
            item,
            _json_field_names(ResearchMarketLiquidityCostStressBucketReasonCodeCount),
        )
        _require_reason_code(f"{item_path}.reason_code", item["reason_code"])
        _require_payload_decimal(f"{item_path}.row_count", item["row_count"])
        _require_payload_decimal(f"{item_path}.row_ratio", item["row_ratio"])
        _require_payload_flags(item_path, item)


def _validate_public_payload_consistency(payload: dict[str, Any]) -> None:
    report = ResearchMarketLiquidityCostStressBucketReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        report_status=payload["report_status"],
        row_count=_payload_decimal("row_count", payload["row_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        wide_spread_count=_payload_decimal(
            "wide_spread_count",
            payload["wide_spread_count"],
        ),
        thin_depth_count=_payload_decimal(
            "thin_depth_count",
            payload["thin_depth_count"],
        ),
        fragile_depth_count=_payload_decimal(
            "fragile_depth_count",
            payload["fragile_depth_count"],
        ),
        high_fee_drag_count=_payload_decimal(
            "high_fee_drag_count",
            payload["high_fee_drag_count"],
        ),
        low_slippage_cushion_count=_payload_decimal(
            "low_slippage_cushion_count",
            payload["low_slippage_cushion_count"],
        ),
        stale_book_count=_payload_decimal(
            "stale_book_count",
            payload["stale_book_count"],
        ),
        volatile_book_count=_payload_decimal(
            "volatile_book_count",
            payload["volatile_book_count"],
        ),
        settlement_friction_count=_payload_decimal(
            "settlement_friction_count",
            payload["settlement_friction_count"],
        ),
        max_stress_score=_payload_decimal(
            "max_stress_score",
            payload["max_stress_score"],
        ),
        rows=tuple(
            _payload_row(f"rows[{index}]", row)
            for index, row in enumerate(payload["rows"])
        ),
        reason_code_counts=tuple(
            _payload_reason_code_count(f"reason_code_counts[{index}]", item)
            for index, item in enumerate(payload["reason_code_counts"])
        ),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    if _json_ready(report) != payload:
        raise ValueError("payload does not match normalized report")


def _payload_row(
    row_path: str,
    row: object,
) -> ResearchMarketLiquidityCostStressBucketRow:
    if type(row) is not dict:
        raise ValueError(f"{row_path} must be a JSON object")
    return ResearchMarketLiquidityCostStressBucketRow(
        surface_group=row["surface_group"],
        category=row["category"],
        spread_rate=_payload_decimal(f"{row_path}.spread_rate", row["spread_rate"]),
        available_depth_usdc=_payload_decimal(
            f"{row_path}.available_depth_usdc",
            row["available_depth_usdc"],
        ),
        depth_band=row["depth_band"],
        fee_drag_rate=_payload_decimal(f"{row_path}.fee_drag_rate", row["fee_drag_rate"]),
        slippage_cushion_rate=_payload_decimal(
            f"{row_path}.slippage_cushion_rate",
            row["slippage_cushion_rate"],
        ),
        book_age_seconds=_payload_decimal(
            f"{row_path}.book_age_seconds",
            row["book_age_seconds"],
        ),
        volatility_rate=_payload_decimal(
            f"{row_path}.volatility_rate",
            row["volatility_rate"],
        ),
        settlement_friction_rate=_payload_decimal(
            f"{row_path}.settlement_friction_rate",
            row["settlement_friction_rate"],
        ),
        spread_status=row["spread_status"],
        depth_status=row["depth_status"],
        fee_drag_status=row["fee_drag_status"],
        slippage_cushion_status=row["slippage_cushion_status"],
        book_age_status=row["book_age_status"],
        volatility_status=row["volatility_status"],
        settlement_friction_status=row["settlement_friction_status"],
        stress_score=_payload_decimal(f"{row_path}.stress_score", row["stress_score"]),
        status=row["status"],
        stress_bucket=row["stress_bucket"],
        reason_codes=tuple(row["reason_codes"]),
        derived_validation_digest=row["derived_validation_digest"],
        paper_only=row["paper_only"],
        report_only=row["report_only"],
        readonly=row["readonly"],
    )


def _payload_reason_code_count(
    item_path: str,
    item: object,
) -> ResearchMarketLiquidityCostStressBucketReasonCodeCount:
    if type(item) is not dict:
        raise ValueError(f"{item_path} must be a JSON object")
    return ResearchMarketLiquidityCostStressBucketReasonCodeCount(
        reason_code=item["reason_code"],
        row_count=_payload_decimal(f"{item_path}.row_count", item["row_count"]),
        row_ratio=_payload_decimal(f"{item_path}.row_ratio", item["row_ratio"]),
        paper_only=item["paper_only"],
        report_only=item["report_only"],
        readonly=item["readonly"],
    )


def _json_field_names(dataclass_type: type[object]) -> frozenset[str]:
    return frozenset(field.name for field in fields(dataclass_type))


def _require_exact_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = frozenset(value)
    extra_keys = sorted(actual_keys - expected_keys)
    if extra_keys:
        raise ValueError(f"{label} has unexpected field")
    missing_keys = sorted(expected_keys - actual_keys)
    if missing_keys:
        raise ValueError(f"{label} is missing field")


def _require_payload_flags(label: str, value: dict[str, Any]) -> None:
    for field_name in _FLAG_FIELDS:
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    _reject_unsafe_string(name, value)


def _require_payload_datetime(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be an ISO datetime string")
    try:
        _payload_datetime(name, value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string") from exc


def _require_payload_decimal(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite")
    if value != str(_quantize(parsed)):
        raise ValueError(f"{name} must be quantized to 0.000001")


def _payload_datetime(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string") from exc
    return _as_utc(name, parsed)


def _payload_decimal(name: str, value: object) -> Decimal:
    _require_payload_decimal(name, value)
    return _quantize(Decimal(value))


def _require_payload_reason_codes(name: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"{name} must be a JSON array")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if len(set(codes)) != len(codes):
        raise ValueError(f"{name} must be unique")
    for code in codes:
        _require_reason_code(name, code)
    if codes != tuple(sorted(codes)):
        raise ValueError(f"{name} must be sorted")


def _sha256_for_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _require_canonical_public_scalars(value: object, path: str = "") -> None:
    current_path = path or "payload"
    if value is None or type(value) is bool or type(value) is str:
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{current_path} must be a Decimal string")
    if isinstance(value, datetime):
        raise ValueError(f"{current_path} must be an ISO datetime string")
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{current_path} must use a Decimal string")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _require_canonical_public_scalars(item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _require_canonical_public_scalars(item, f"{current_path}[{index}]")
        return
    raise ValueError(f"{current_path} is not a canonical public JSON value")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


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
        _reject_unsafe_string(current_path, value)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_key(item_path, field.name)
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
            _reject_unsafe_key(item_path, key)
            if key in _FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
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


def _reject_unsafe_key(path: str, key: str) -> None:
    lowered_key = key.lower()
    if any(fragment in lowered_key for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path} has unsafe field")


def _reject_unsafe_string(path: str, value: str) -> None:
    if value != value.strip():
        raise ValueError(f"{path} has unsafe value")
    lowered_value = value.lower()
    if "://" in lowered_value or "?" in lowered_value:
        raise ValueError(f"{path} has unsafe value")
    if any(fragment in lowered_value for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path} has unsafe value")


def _require_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    _reject_unsafe_key(name, name)
    _reject_unsafe_string(name, value)


def _require_choice(name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        joined_choices = ", ".join(choices)
        raise ValueError(f"{name} must be one of: {joined_choices}")


def _require_reason_code(name: str, value: object) -> None:
    _require_public_string(name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{name} must be a known reason code")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a 64-character hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be lowercase hex")


def _require_ordered_thresholds(name: str, watch: Decimal, block: Decimal) -> None:
    if block <= watch:
        raise ValueError(f"{name} must have block above watch")


def _require_descending_floors(name: str, watch: Decimal, block: Decimal) -> None:
    if watch <= block:
        raise ValueError(f"{name} must have watch above block")


def _rate(name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must be at most 1.000000")
    return normalized


def _count_decimal(name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integral Decimal")
    return normalized


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)
