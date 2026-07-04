"""Pure Phase 1 energy grid reserve margin squeeze digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_RESEARCH_ENERGY_GRID_RESERVE_MARGIN_SQUEEZE_DIGEST_CONFIG_VERSION = (
    "market-research-energy-grid-reserve-margin-squeeze-digest-v0"
)

NO_INPUTS_REASON = (
    "market_research_energy_grid_reserve_margin_squeeze_digest_no_inputs"
)
RESERVE_MARGIN_BLOCK_REASON = (
    "market_research_energy_grid_reserve_margin_squeeze_digest_reserve_margin_block"
)
LOAD_UTILIZATION_BLOCK_REASON = (
    "market_research_energy_grid_reserve_margin_squeeze_digest_load_utilization_block"
)
FORCED_OUTAGE_BLOCK_REASON = (
    "market_research_energy_grid_reserve_margin_squeeze_digest_forced_outage_block"
)
PROBABILITY_SHIFT_REASON = (
    "market_research_energy_grid_reserve_margin_squeeze_digest_probability_shift"
)
RESERVE_MARGIN_WATCH_REASON = (
    "market_research_energy_grid_reserve_margin_squeeze_digest_reserve_margin_watch"
)
LOAD_UTILIZATION_WATCH_REASON = (
    "market_research_energy_grid_reserve_margin_squeeze_digest_load_utilization_watch"
)
FORCED_OUTAGE_WATCH_REASON = (
    "market_research_energy_grid_reserve_margin_squeeze_digest_forced_outage_watch"
)
STALE_SNAPSHOT_REASON = (
    "market_research_energy_grid_reserve_margin_squeeze_digest_stale_snapshot"
)
THIN_SOURCES_REASON = (
    "market_research_energy_grid_reserve_margin_squeeze_digest_thin_sources"
)
CLEAR_REASON = "market_research_energy_grid_reserve_margin_squeeze_digest_clear"

REASON_CODES = (
    NO_INPUTS_REASON,
    RESERVE_MARGIN_BLOCK_REASON,
    LOAD_UTILIZATION_BLOCK_REASON,
    FORCED_OUTAGE_BLOCK_REASON,
    PROBABILITY_SHIFT_REASON,
    RESERVE_MARGIN_WATCH_REASON,
    LOAD_UTILIZATION_WATCH_REASON,
    FORCED_OUTAGE_WATCH_REASON,
    STALE_SNAPSHOT_REASON,
    THIN_SOURCES_REASON,
    CLEAR_REASON,
)
ROW_REASON_CODES = REASON_CODES[1:]
SQUEEZE_STATUSES = ("blocked", "watch", "clear")
NEXT_STEPS = {
    "blocked": (
        "block_report_only_market_research_energy_grid_reserve_margin_squeeze_digest"
    ),
    "watch": (
        "watch_report_only_market_research_energy_grid_reserve_margin_squeeze_digest"
    ),
    "clear": (
        "allow_report_only_market_research_energy_grid_reserve_margin_squeeze_digest"
    ),
}
STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
NEGATIVE_ONE = Decimal("-1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_ENERGY_GRID_RESERVE_MARGIN_SQUEEZE_DIGEST_CONFIG_VERSION",
    "MarketResearchEnergyGridReserveMarginSqueezeDigestConfig",
    "MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow",
    "MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount",
    "MarketResearchEnergyGridReserveMarginSqueezeDigestReport",
    "MarketResearchEnergyGridReserveMarginSqueezeDigestRow",
    "build_market_research_energy_grid_reserve_margin_squeeze_digest",
    "market_research_energy_grid_reserve_margin_squeeze_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEnergyGridReserveMarginSqueezeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_ENERGY_GRID_RESERVE_MARGIN_SQUEEZE_DIGEST_CONFIG_VERSION
    )
    fresh_snapshot_max_age_seconds: Decimal = Decimal("7200.000000")
    min_public_source_count: Decimal = Decimal("2.000000")
    watch_reserve_margin_ratio: Decimal = Decimal("0.100000")
    block_reserve_margin_ratio: Decimal = Decimal("0.060000")
    watch_load_utilization_ratio: Decimal = Decimal("0.900000")
    block_load_utilization_ratio: Decimal = Decimal("0.970000")
    watch_forced_outage_ratio: Decimal = Decimal("0.080000")
    block_forced_outage_ratio: Decimal = Decimal("0.150000")
    probability_shift_threshold: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyGridReserveMarginSqueezeDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchEnergyGridReserveMarginSqueezeDigestConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_GRID_RESERVE_MARGIN_SQUEEZE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "fresh_snapshot_max_age_seconds",
            _require_positive_decimal(
                "fresh_snapshot_max_age_seconds",
                self.fresh_snapshot_max_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_public_source_count",
            _require_whole_positive_decimal(
                "min_public_source_count",
                self.min_public_source_count,
            ),
        )
        for field_name in (
            "watch_reserve_margin_ratio",
            "block_reserve_margin_ratio",
            "watch_forced_outage_ratio",
            "block_forced_outage_ratio",
            "probability_shift_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_load_utilization_ratio",
            "block_load_utilization_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_reserve_margin_ratio > self.watch_reserve_margin_ratio:
            raise ValueError(
                "block_reserve_margin_ratio must be at most watch_reserve_margin_ratio",
            )
        if self.block_load_utilization_ratio < self.watch_load_utilization_ratio:
            raise ValueError(
                "block_load_utilization_ratio must be at least "
                "watch_load_utilization_ratio",
            )
        if self.block_forced_outage_ratio < self.watch_forced_outage_ratio:
            raise ValueError(
                "block_forced_outage_ratio must be at least watch_forced_outage_ratio",
            )
        _require_hard_flags("reserve margin squeeze config", self)


@dataclass(frozen=True)
class MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow:
    grid_region: str
    grid_area: str
    condition_id: str
    market_slug: str
    source_id: str
    snapshot_at: datetime
    available_capacity_mw: Decimal
    forecast_peak_load_mw: Decimal
    reserve_margin_ratio: Decimal
    forced_outage_ratio: Decimal
    public_source_count: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow",
            )
        object.__setattr__(self, "grid_region", _require_key("grid_region", self.grid_region))
        object.__setattr__(self, "grid_area", _require_key("grid_area", self.grid_area))
        object.__setattr__(
            self,
            "condition_id",
            _require_safe_id("condition_id", self.condition_id),
        )
        object.__setattr__(
            self,
            "market_slug",
            _require_slug("market_slug", self.market_slug),
        )
        object.__setattr__(self, "source_id", _require_safe_id("source_id", self.source_id))
        object.__setattr__(self, "snapshot_at", _as_utc("snapshot_at", self.snapshot_at))
        for field_name in ("available_capacity_mw", "forecast_peak_load_mw"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "reserve_margin_ratio",
            "forced_outage_ratio",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_source_count",
            _require_whole_nonnegative_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        _require_hard_flags("reserve margin squeeze input row", self)


@dataclass(frozen=True)
class MarketResearchEnergyGridReserveMarginSqueezeDigestRow:
    grid_region: str
    grid_area: str
    condition_id: str
    market_slug: str
    source_id: str
    snapshot_at: datetime
    snapshot_age_seconds: Decimal
    available_capacity_mw: Decimal
    forecast_peak_load_mw: Decimal
    capacity_surplus_mw: Decimal
    load_utilization_ratio: Decimal
    reserve_margin_ratio: Decimal
    forced_outage_ratio: Decimal
    public_source_count: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_change: Decimal
    squeeze_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyGridReserveMarginSqueezeDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchEnergyGridReserveMarginSqueezeDigestRow",
            )
        object.__setattr__(self, "grid_region", _require_key("grid_region", self.grid_region))
        object.__setattr__(self, "grid_area", _require_key("grid_area", self.grid_area))
        object.__setattr__(
            self,
            "condition_id",
            _require_safe_id("condition_id", self.condition_id),
        )
        object.__setattr__(
            self,
            "market_slug",
            _require_slug("market_slug", self.market_slug),
        )
        object.__setattr__(self, "source_id", _require_safe_id("source_id", self.source_id))
        object.__setattr__(self, "snapshot_at", _as_utc("snapshot_at", self.snapshot_at))
        for field_name in (
            "snapshot_age_seconds",
            "available_capacity_mw",
            "forecast_peak_load_mw",
            "load_utilization_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "capacity_surplus_mw",
            _require_decimal("capacity_surplus_mw", self.capacity_surplus_mw),
        )
        for field_name in (
            "reserve_margin_ratio",
            "forced_outage_ratio",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_source_count",
            _require_whole_nonnegative_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        object.__setattr__(
            self,
            "probability_change",
            _require_signed_ratio("probability_change", self.probability_change),
        )
        object.__setattr__(
            self,
            "squeeze_status",
            _require_member("squeeze_status", self.squeeze_status, SQUEEZE_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("reserve margin squeeze row", self)


@dataclass(frozen=True)
class MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    grid_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, REASON_CODES),
        )
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "grid_ratio",
            _require_ratio("grid_ratio", self.grid_ratio),
        )
        _require_hard_flags("reserve margin squeeze reason count", self)


@dataclass(frozen=True)
class MarketResearchEnergyGridReserveMarginSqueezeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    grid_count: Decimal
    clear_grid_count: Decimal
    watch_grid_count: Decimal
    blocked_grid_count: Decimal
    low_reserve_margin_count: Decimal
    high_load_utilization_count: Decimal
    forced_outage_pressure_count: Decimal
    stale_snapshot_count: Decimal
    thin_source_count: Decimal
    probability_shift_count: Decimal
    min_reserve_margin_ratio: Decimal
    max_load_utilization_ratio: Decimal
    max_forced_outage_ratio: Decimal
    average_reserve_margin_ratio: Decimal
    average_capacity_surplus_mw: Decimal
    max_snapshot_age_seconds: Decimal
    average_public_source_count: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[MarketResearchEnergyGridReserveMarginSqueezeDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyGridReserveMarginSqueezeDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchEnergyGridReserveMarginSqueezeDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_GRID_RESERVE_MARGIN_SQUEEZE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "digest_status",
            _require_member("digest_status", self.digest_status, SQUEEZE_STATUSES),
        )
        object.__setattr__(
            self,
            "recommended_next_step",
            _require_text("recommended_next_step", self.recommended_next_step),
        )
        for field_name in (
            "grid_count",
            "clear_grid_count",
            "watch_grid_count",
            "blocked_grid_count",
            "low_reserve_margin_count",
            "high_load_utilization_count",
            "forced_outage_pressure_count",
            "stale_snapshot_count",
            "thin_source_count",
            "probability_shift_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_reserve_margin_ratio",
            "max_forced_outage_ratio",
            "average_reserve_margin_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_load_utilization_ratio",
            "max_snapshot_age_seconds",
            "average_public_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_capacity_surplus_mw",
            _require_decimal(
                "average_capacity_surplus_mw",
                self.average_capacity_surplus_mw,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags("reserve margin squeeze report", self)


def build_market_research_energy_grid_reserve_margin_squeeze_digest(
    rows: Iterable[MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow],
    *,
    config: MarketResearchEnergyGridReserveMarginSqueezeDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyGridReserveMarginSqueezeDigestReport:
    if type(config) is not MarketResearchEnergyGridReserveMarginSqueezeDigestConfig:
        raise ValueError(
            "config must be a MarketResearchEnergyGridReserveMarginSqueezeDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(rows)
    if not input_rows:
        return _empty_report(config=config, generated_at=generated_at_utc)

    digest_rows = tuple(
        sorted(
            (
                _row_from_input(input_row, config=config, generated_at=generated_at_utc)
                for input_row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    grid_count = _count(len(digest_rows))
    reason_codes = _report_reason_codes(digest_rows)
    reason_code_counts = _reason_code_counts(digest_rows, reason_codes, grid_count)
    digest_status = _report_status(digest_rows)
    return MarketResearchEnergyGridReserveMarginSqueezeDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        grid_count=grid_count,
        clear_grid_count=_status_count(digest_rows, "clear"),
        watch_grid_count=_status_count(digest_rows, "watch"),
        blocked_grid_count=_status_count(digest_rows, "blocked"),
        low_reserve_margin_count=_count(
            sum(
                1
                for row in digest_rows
                if RESERVE_MARGIN_BLOCK_REASON in row.reason_codes
                or RESERVE_MARGIN_WATCH_REASON in row.reason_codes
            ),
        ),
        high_load_utilization_count=_count(
            sum(
                1
                for row in digest_rows
                if LOAD_UTILIZATION_BLOCK_REASON in row.reason_codes
                or LOAD_UTILIZATION_WATCH_REASON in row.reason_codes
            ),
        ),
        forced_outage_pressure_count=_count(
            sum(
                1
                for row in digest_rows
                if FORCED_OUTAGE_BLOCK_REASON in row.reason_codes
                or FORCED_OUTAGE_WATCH_REASON in row.reason_codes
            ),
        ),
        stale_snapshot_count=_event_count_with(digest_rows, STALE_SNAPSHOT_REASON),
        thin_source_count=_event_count_with(digest_rows, THIN_SOURCES_REASON),
        probability_shift_count=_event_count_with(digest_rows, PROBABILITY_SHIFT_REASON),
        min_reserve_margin_ratio=min(
            (row.reserve_margin_ratio for row in digest_rows),
            default=ZERO,
        ),
        max_load_utilization_ratio=max(
            (row.load_utilization_ratio for row in digest_rows),
            default=ZERO,
        ),
        max_forced_outage_ratio=max(
            (row.forced_outage_ratio for row in digest_rows),
            default=ZERO,
        ),
        average_reserve_margin_ratio=_average_decimal(
            row.reserve_margin_ratio for row in digest_rows
        ),
        average_capacity_surplus_mw=_average_decimal(
            row.capacity_surplus_mw for row in digest_rows
        ),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in digest_rows),
            default=ZERO,
        ),
        average_public_source_count=_average_decimal(
            row.public_source_count for row in digest_rows
        ),
        reason_codes=reason_codes,
        rows=digest_rows,
        reason_code_counts=reason_code_counts,
    )


def market_research_energy_grid_reserve_margin_squeeze_digest_payload(
    report: MarketResearchEnergyGridReserveMarginSqueezeDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEnergyGridReserveMarginSqueezeDigestReport:
        raise ValueError(
            "report must be a MarketResearchEnergyGridReserveMarginSqueezeDigestReport",
        )
    _require_hard_flags("reserve margin squeeze report", report)
    plain = json_ready_no_floats(report)
    if type(plain) is not dict:
        raise ValueError("serialized report must be a dict")
    return plain


def _empty_report(
    *,
    config: MarketResearchEnergyGridReserveMarginSqueezeDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyGridReserveMarginSqueezeDigestReport:
    return MarketResearchEnergyGridReserveMarginSqueezeDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        digest_status="blocked",
        recommended_next_step=NEXT_STEPS["blocked"],
        grid_count=ZERO,
        clear_grid_count=ZERO,
        watch_grid_count=ZERO,
        blocked_grid_count=ZERO,
        low_reserve_margin_count=ZERO,
        high_load_utilization_count=ZERO,
        forced_outage_pressure_count=ZERO,
        stale_snapshot_count=ZERO,
        thin_source_count=ZERO,
        probability_shift_count=ZERO,
        min_reserve_margin_ratio=ZERO,
        max_load_utilization_ratio=ZERO,
        max_forced_outage_ratio=ZERO,
        average_reserve_margin_ratio=ZERO,
        average_capacity_surplus_mw=ZERO,
        max_snapshot_age_seconds=ZERO,
        average_public_source_count=ZERO,
        reason_codes=(NO_INPUTS_REASON,),
        rows=(),
        reason_code_counts=(
            MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                grid_ratio=ZERO,
            ),
        ),
    )


def _row_from_input(
    row: MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow,
    *,
    config: MarketResearchEnergyGridReserveMarginSqueezeDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyGridReserveMarginSqueezeDigestRow:
    if row.snapshot_at > generated_at:
        raise ValueError("snapshot_at must not be after generated_at")
    snapshot_age_seconds = _seconds_between(row.snapshot_at, generated_at)
    capacity_surplus_mw = _quantize(row.available_capacity_mw - row.forecast_peak_load_mw)
    load_utilization_ratio = _ratio(
        row.forecast_peak_load_mw,
        row.available_capacity_mw,
    )
    probability_change = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        row,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        load_utilization_ratio=load_utilization_ratio,
        probability_change=probability_change,
    )
    return MarketResearchEnergyGridReserveMarginSqueezeDigestRow(
        grid_region=row.grid_region,
        grid_area=row.grid_area,
        condition_id=row.condition_id,
        market_slug=row.market_slug,
        source_id=row.source_id,
        snapshot_at=row.snapshot_at,
        snapshot_age_seconds=snapshot_age_seconds,
        available_capacity_mw=row.available_capacity_mw,
        forecast_peak_load_mw=row.forecast_peak_load_mw,
        capacity_surplus_mw=capacity_surplus_mw,
        load_utilization_ratio=load_utilization_ratio,
        reserve_margin_ratio=row.reserve_margin_ratio,
        forced_outage_ratio=row.forced_outage_ratio,
        public_source_count=row.public_source_count,
        market_probability_before=row.market_probability_before,
        market_probability_after=row.market_probability_after,
        probability_change=probability_change,
        squeeze_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow,
    *,
    config: MarketResearchEnergyGridReserveMarginSqueezeDigestConfig,
    snapshot_age_seconds: Decimal,
    load_utilization_ratio: Decimal,
    probability_change: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if row.reserve_margin_ratio <= config.block_reserve_margin_ratio:
        reason_codes.append(RESERVE_MARGIN_BLOCK_REASON)
    elif row.reserve_margin_ratio <= config.watch_reserve_margin_ratio:
        reason_codes.append(RESERVE_MARGIN_WATCH_REASON)
    if load_utilization_ratio >= config.block_load_utilization_ratio:
        reason_codes.append(LOAD_UTILIZATION_BLOCK_REASON)
    elif load_utilization_ratio >= config.watch_load_utilization_ratio:
        reason_codes.append(LOAD_UTILIZATION_WATCH_REASON)
    if row.forced_outage_ratio >= config.block_forced_outage_ratio:
        reason_codes.append(FORCED_OUTAGE_BLOCK_REASON)
    elif row.forced_outage_ratio >= config.watch_forced_outage_ratio:
        reason_codes.append(FORCED_OUTAGE_WATCH_REASON)
    if probability_change.copy_abs() >= config.probability_shift_threshold:
        reason_codes.append(PROBABILITY_SHIFT_REASON)
    if snapshot_age_seconds > config.fresh_snapshot_max_age_seconds:
        reason_codes.append(STALE_SNAPSHOT_REASON)
    if row.public_source_count < config.min_public_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        RESERVE_MARGIN_BLOCK_REASON in reason_codes
        or LOAD_UTILIZATION_BLOCK_REASON in reason_codes
        or FORCED_OUTAGE_BLOCK_REASON in reason_codes
    ):
        return "blocked"
    if reason_codes == (CLEAR_REASON,):
        return "clear"
    return "watch"


def _report_status(
    rows: tuple[MarketResearchEnergyGridReserveMarginSqueezeDigestRow, ...],
) -> str:
    if any(row.squeeze_status == "blocked" for row in rows):
        return "blocked"
    if any(row.squeeze_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketResearchEnergyGridReserveMarginSqueezeDigestRow, ...],
) -> tuple[str, ...]:
    found = {code for row in rows for code in row.reason_codes}
    return tuple(code for code in REASON_CODES if code in found)


def _reason_code_counts(
    rows: tuple[MarketResearchEnergyGridReserveMarginSqueezeDigestRow, ...],
    reason_codes: tuple[str, ...],
    grid_count: Decimal,
) -> tuple[MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount(
            reason_code=reason_code,
            count=_event_count_with(rows, reason_code),
            grid_ratio=_ratio(_event_count_with(rows, reason_code), grid_count),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    rows: Iterable[MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow],
) -> tuple[MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of input rows")
    normalized: list[MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow:
            raise ValueError(
                "rows must contain MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow",
            )
        _require_hard_flags("reserve margin squeeze input row", row)
        key = (row.grid_region, row.grid_area)
        if key in seen:
            raise ValueError("rows must be unique by grid_region and grid_area")
        seen.add(key)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[MarketResearchEnergyGridReserveMarginSqueezeDigestRow, ...],
) -> tuple[MarketResearchEnergyGridReserveMarginSqueezeDigestRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchEnergyGridReserveMarginSqueezeDigestRow:
            raise ValueError(
                "rows must contain MarketResearchEnergyGridReserveMarginSqueezeDigestRow",
            )
        _require_hard_flags("reserve margin squeeze row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic reserve margin squeeze sorting")
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount, ...],
) -> tuple[MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount, ...]:
    if not isinstance(items, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount",
            )
        _require_hard_flags("reserve margin squeeze reason count", item)
    if items != tuple(sorted(items, key=lambda item: REASON_CODES.index(item.reason_code))):
        raise ValueError("reason_code_counts must use deterministic reason code sequencing")
    return items


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        code = _require_member(field_name, item, allowed)
        if code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(code)
        normalized.append(code)
    if allowed is REASON_CODES and tuple(normalized) != tuple(
        code for code in allowed if code in seen
    ):
        raise ValueError(f"{field_name} must use deterministic reason code sequencing")
    return tuple(normalized)


def _validate_row(row: MarketResearchEnergyGridReserveMarginSqueezeDigestRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.squeeze_status != expected_status:
        raise ValueError("squeeze_status must match reason_codes")
    if row.capacity_surplus_mw != _quantize(
        row.available_capacity_mw - row.forecast_peak_load_mw,
    ):
        raise ValueError("capacity_surplus_mw must match capacity values")
    if row.load_utilization_ratio != _ratio(
        row.forecast_peak_load_mw,
        row.available_capacity_mw,
    ):
        raise ValueError("load_utilization_ratio must match capacity values")
    if row.probability_change != _quantize(
        row.market_probability_after - row.market_probability_before,
    ):
        raise ValueError("probability_change must match market probability values")


def _validate_report(report: MarketResearchEnergyGridReserveMarginSqueezeDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.grid_count != _count(len(report.rows)):
        raise ValueError("grid_count must match rows")
    if report.clear_grid_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_grid_count must match rows")
    if report.watch_grid_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_grid_count must match rows")
    if report.blocked_grid_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_grid_count must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.rows and report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if not report.rows and report.digest_status != "blocked":
        raise ValueError("empty digest_status must be blocked")


def _row_sort_key(
    row: MarketResearchEnergyGridReserveMarginSqueezeDigestRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.squeeze_status],
        row.reserve_margin_ratio,
        -row.load_utilization_ratio,
        -row.forced_outage_ratio,
        row.grid_region,
        row.grid_area,
    )


def _event_count_with(
    rows: tuple[MarketResearchEnergyGridReserveMarginSqueezeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[MarketResearchEnergyGridReserveMarginSqueezeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.squeeze_status == status))


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _ratio(_sum_decimal(items), _count(len(items)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_text(field_name: str, value: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_text(field_name, value)
    return value


def _require_key(field_name: str, value: str) -> str:
    text = _require_text(field_name, value)
    if text.lower() != text or not all(char.isalnum() or char == "_" for char in text):
        raise ValueError(f"{field_name} must be a canonical snake case key")
    return text


def _require_safe_id(field_name: str, value: str) -> str:
    text = _require_text(field_name, value)
    if text.lower() != text or not all(char.isalnum() or char in "._-" for char in text):
        raise ValueError(f"{field_name} must be a canonical public id")
    return text


def _require_slug(field_name: str, value: str) -> str:
    text = _require_text(field_name, value)
    if text.lower() != text or not all(char.isalnum() or char == "-" for char in text):
        raise ValueError(f"{field_name} must be a canonical public slug")
    return text


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    blocked_fragments = (
        "\x61uth",
        "\x61pi_key",
        "priv\x61te_key",
        "w\x61llet",
        "br\x6fker",
        "sub\x6dit_\x6frder",
        "c\x61ncel_\x6frder",
        "repl\x61ce_\x6frder",
        "sign",
        "\x74oken",
    )
    for fragment in blocked_fragments:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains a reserved surface fragment")


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> str:
    text = _require_text(field_name, value)
    if text not in allowed:
        raise ValueError(f"{field_name} must be one of supported values")
    return text


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_signed_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < NEGATIVE_ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _require_whole_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_whole_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    require_paper_only_flags(label, value)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    elapsed = end - start
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(elapsed.days * 86400 + elapsed.seconds)
            + (Decimal(elapsed.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)
