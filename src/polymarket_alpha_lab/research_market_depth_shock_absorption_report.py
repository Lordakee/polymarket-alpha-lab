"""Pure report-only depth shock absorption reducer for manual research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


DEPTH_SHOCK_ABSORPTION_STATUSES = ("pass", "watch", "block")
DEFAULT_RESEARCH_MARKET_DEPTH_SHOCK_ABSORPTION_REPORT_CONFIG_VERSION = (
    "research-market-depth-shock-absorption-report-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "url",
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
    "li" "ve",
    "buy",
    "sell",
    "size",
    "siz" "ing",
    "recommendation",
)


__all__ = (
    "DEPTH_SHOCK_ABSORPTION_STATUSES",
    "DEFAULT_RESEARCH_MARKET_DEPTH_SHOCK_ABSORPTION_REPORT_CONFIG_VERSION",
    "ResearchMarketDepthShockAbsorptionConfig",
    "ResearchMarketDepthShockAbsorptionObservation",
    "ResearchMarketDepthShockAbsorptionReasonCodeCount",
    "ResearchMarketDepthShockAbsorptionReport",
    "ResearchMarketDepthShockAbsorptionRow",
    "build_research_market_depth_shock_absorption_report",
    "research_market_depth_shock_absorption_report_digest",
    "research_market_depth_shock_absorption_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketDepthShockAbsorptionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_DEPTH_SHOCK_ABSORPTION_REPORT_CONFIG_VERSION
    )
    max_pass_shock_shortfall_ratio: Decimal = Decimal("0.050000")
    max_watch_shock_shortfall_ratio: Decimal = Decimal("0.250000")
    max_pass_spread_widening: Decimal = Decimal("0.020000")
    max_watch_spread_widening: Decimal = Decimal("0.060000")
    max_pass_imbalance_volatility: Decimal = Decimal("0.200000")
    max_watch_imbalance_volatility: Decimal = Decimal("0.500000")
    max_pass_stale_book_age_seconds: Decimal = Decimal("120.000000")
    max_watch_stale_book_age_seconds: Decimal = Decimal("600.000000")
    min_pass_fee_slippage_cushion_ratio: Decimal = Decimal("0.150000")
    min_watch_fee_slippage_cushion_ratio: Decimal = Decimal("0.050000")
    pass_absorption_score: Decimal = Decimal("0.750000")
    watch_absorption_score: Decimal = Decimal("0.450000")
    depth_absorption_weight: Decimal = Decimal("0.350000")
    spread_resilience_weight: Decimal = Decimal("0.200000")
    imbalance_stability_weight: Decimal = Decimal("0.150000")
    freshness_weight: Decimal = Decimal("0.150000")
    fee_slippage_cushion_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketDepthShockAbsorptionConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthShockAbsorptionConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_SHOCK_ABSORPTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_shock_shortfall_ratio",
            "max_watch_shock_shortfall_ratio",
            "max_pass_spread_widening",
            "max_watch_spread_widening",
            "max_pass_imbalance_volatility",
            "max_watch_imbalance_volatility",
            "min_pass_fee_slippage_cushion_ratio",
            "min_watch_fee_slippage_cushion_ratio",
            "pass_absorption_score",
            "watch_absorption_score",
            "depth_absorption_weight",
            "spread_resilience_weight",
            "imbalance_stability_weight",
            "freshness_weight",
            "fee_slippage_cushion_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_stale_book_age_seconds",
            "max_watch_stale_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_watch_shock_shortfall_ratio <= self.max_pass_shock_shortfall_ratio:
            raise ValueError("max_watch_shock_shortfall_ratio must exceed pass threshold")
        if self.max_watch_spread_widening <= self.max_pass_spread_widening:
            raise ValueError("max_watch_spread_widening must exceed pass threshold")
        if self.max_watch_imbalance_volatility <= self.max_pass_imbalance_volatility:
            raise ValueError("max_watch_imbalance_volatility must exceed pass threshold")
        if self.max_watch_stale_book_age_seconds <= self.max_pass_stale_book_age_seconds:
            raise ValueError("max_watch_stale_book_age_seconds must exceed pass threshold")
        if (
            self.min_pass_fee_slippage_cushion_ratio
            <= self.min_watch_fee_slippage_cushion_ratio
        ):
            raise ValueError(
                "min_pass_fee_slippage_cushion_ratio must exceed watch threshold",
            )
        if self.pass_absorption_score <= self.watch_absorption_score:
            raise ValueError("pass_absorption_score must exceed watch threshold")
        weight_sum = _quantize(
            self.depth_absorption_weight
            + self.spread_resilience_weight
            + self.imbalance_stability_weight
            + self.freshness_weight
            + self.fee_slippage_cushion_weight,
        )
        if weight_sum != ONE:
            raise ValueError("depth shock absorption score weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthShockAbsorptionObservation:
    book_snapshot_key: str
    observed_at: datetime
    last_book_update_at: datetime
    target_shock_probability: Decimal
    near_band_depth: Decimal
    mid_band_depth: Decimal
    far_band_depth: Decimal
    spread_widening: Decimal
    imbalance_volatility: Decimal
    fee_cushion: Decimal
    slippage_cushion: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketDepthShockAbsorptionObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthShockAbsorptionObservation,
            "observation",
        )
        _require_canonical_string("book_snapshot_key", self.book_snapshot_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_book_update_at",
            _as_utc("last_book_update_at", self.last_book_update_at),
        )
        object.__setattr__(
            self,
            "target_shock_probability",
            _require_positive_ratio_decimal(
                "target_shock_probability",
                self.target_shock_probability,
            ),
        )
        for field_name in ("near_band_depth", "mid_band_depth", "far_band_depth"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.near_band_depth + self.mid_band_depth + self.far_band_depth <= ZERO:
            raise ValueError("depth bands must provide positive aggregate depth")
        for field_name in (
            "spread_widening",
            "imbalance_volatility",
            "fee_cushion",
            "slippage_cushion",
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
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketDepthShockAbsorptionRow:
    absorption_group_ref: str
    observed_at: datetime
    last_book_update_at: datetime
    stale_book_age_seconds: Decimal
    target_shock_probability: Decimal
    near_band_depth: Decimal
    mid_band_depth: Decimal
    far_band_depth: Decimal
    total_band_depth: Decimal
    fee_slippage_cushion: Decimal
    fee_slippage_cushion_ratio: Decimal
    net_absorbable_probability: Decimal
    net_depth_coverage_ratio: Decimal
    shock_shortfall_ratio: Decimal
    spread_widening: Decimal
    imbalance_volatility: Decimal
    stale_book_pressure: Decimal
    depth_absorption_score: Decimal
    spread_resilience_score: Decimal
    imbalance_stability_score: Decimal
    freshness_score: Decimal
    fee_slippage_cushion_score: Decimal
    depth_shock_absorption_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketDepthShockAbsorptionRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthShockAbsorptionRow, "row")
        _require_canonical_string("absorption_group_ref", self.absorption_group_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_book_update_at",
            _as_utc("last_book_update_at", self.last_book_update_at),
        )
        for field_name in (
            "stale_book_age_seconds",
            "near_band_depth",
            "mid_band_depth",
            "far_band_depth",
            "total_band_depth",
            "fee_slippage_cushion",
            "net_absorbable_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "target_shock_probability",
            _require_positive_ratio_decimal(
                "target_shock_probability",
                self.target_shock_probability,
            ),
        )
        for field_name in (
            "fee_slippage_cushion_ratio",
            "net_depth_coverage_ratio",
            "shock_shortfall_ratio",
            "spread_widening",
            "imbalance_volatility",
            "stale_book_pressure",
            "depth_absorption_score",
            "spread_resilience_score",
            "imbalance_stability_score",
            "freshness_score",
            "fee_slippage_cushion_score",
            "depth_shock_absorption_score",
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
class ResearchMarketDepthShockAbsorptionReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketDepthShockAbsorptionReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthShockAbsorptionReasonCodeCount,
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
class ResearchMarketDepthShockAbsorptionReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_depth_shock_absorption_score: Decimal | None
    min_net_depth_coverage_ratio: Decimal
    max_shock_shortfall_ratio: Decimal
    max_spread_widening: Decimal
    max_imbalance_volatility: Decimal
    max_stale_book_age_seconds: Decimal
    min_fee_slippage_cushion_ratio: Decimal
    status: str
    rows: tuple[ResearchMarketDepthShockAbsorptionRow, ...]
    reason_code_counts: tuple[ResearchMarketDepthShockAbsorptionReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketDepthShockAbsorptionReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthShockAbsorptionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_SHOCK_ABSORPTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_depth_shock_absorption_score",
            _require_optional_ratio_decimal(
                "average_depth_shock_absorption_score",
                self.average_depth_shock_absorption_score,
            ),
        )
        for field_name in (
            "min_net_depth_coverage_ratio",
            "max_shock_shortfall_ratio",
            "max_spread_widening",
            "max_imbalance_volatility",
            "min_fee_slippage_cushion_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_stale_book_age_seconds",
            _require_nonnegative_decimal(
                "max_stale_book_age_seconds",
                self.max_stale_book_age_seconds,
            ),
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


def build_research_market_depth_shock_absorption_report(
    observations: Iterable[ResearchMarketDepthShockAbsorptionObservation],
    *,
    config: ResearchMarketDepthShockAbsorptionConfig,
    generated_at: datetime,
) -> ResearchMarketDepthShockAbsorptionReport:
    if type(config) is not ResearchMarketDepthShockAbsorptionConfig:
        raise ValueError("config must be a ResearchMarketDepthShockAbsorptionConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
        if item.last_book_update_at > generated_at_utc:
            raise ValueError("last_book_update_at must not be after generated_at")
    rows = tuple(
        _row_from_observation(
            absorption_group_ref=f"depth_shock_group_{index:03d}",
            observation=item,
            config=config,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(sorted(normalized, key=_observation_sort_key), start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketDepthShockAbsorptionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_depth_shock_absorption_score=_average_score(rows),
        min_net_depth_coverage_ratio=_min_or_zero(
            tuple(row.net_depth_coverage_ratio for row in rows),
        ),
        max_shock_shortfall_ratio=_max_or_zero(
            tuple(row.shock_shortfall_ratio for row in rows),
        ),
        max_spread_widening=_max_or_zero(tuple(row.spread_widening for row in rows)),
        max_imbalance_volatility=_max_or_zero(
            tuple(row.imbalance_volatility for row in rows),
        ),
        max_stale_book_age_seconds=_max_or_zero(
            tuple(row.stale_book_age_seconds for row in rows),
        ),
        min_fee_slippage_cushion_ratio=_min_or_zero(
            tuple(row.fee_slippage_cushion_ratio for row in rows),
        ),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_depth_shock_absorption_report_payload(
    report: ResearchMarketDepthShockAbsorptionReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketDepthShockAbsorptionReport:
        raise ValueError("report must be a ResearchMarketDepthShockAbsorptionReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload)
    return payload


def research_market_depth_shock_absorption_report_digest(
    report: ResearchMarketDepthShockAbsorptionReport,
) -> str:
    if type(report) is not ResearchMarketDepthShockAbsorptionReport:
        raise ValueError("report must be a ResearchMarketDepthShockAbsorptionReport")
    _require_hard_flags("report", report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


def _row_from_observation(
    *,
    absorption_group_ref: str,
    observation: ResearchMarketDepthShockAbsorptionObservation,
    config: ResearchMarketDepthShockAbsorptionConfig,
    generated_at: datetime,
) -> ResearchMarketDepthShockAbsorptionRow:
    stale_book_age_seconds = _age_seconds(generated_at, observation.last_book_update_at)
    total_band_depth = _quantize(
        observation.near_band_depth
        + observation.mid_band_depth
        + observation.far_band_depth,
    )
    fee_slippage_cushion = _quantize(
        observation.fee_cushion + observation.slippage_cushion,
    )
    net_absorbable_probability = _quantize(total_band_depth + fee_slippage_cushion)
    net_depth_coverage_ratio = _bounded_ratio(
        net_absorbable_probability,
        observation.target_shock_probability,
    )
    shock_shortfall_ratio = _shortfall_ratio(
        net_absorbable_probability,
        observation.target_shock_probability,
    )
    fee_slippage_cushion_ratio = _bounded_ratio(
        fee_slippage_cushion,
        observation.target_shock_probability,
    )
    stale_book_pressure = _pressure_ratio(
        stale_book_age_seconds,
        config.max_watch_stale_book_age_seconds,
    )
    depth_absorption_score = _quantize(ONE - shock_shortfall_ratio)
    spread_resilience_score = _inverse_ratio_score(
        observation.spread_widening,
        config.max_watch_spread_widening,
    )
    imbalance_stability_score = _inverse_ratio_score(
        observation.imbalance_volatility,
        config.max_watch_imbalance_volatility,
    )
    freshness_score = _inverse_ratio_score(
        stale_book_age_seconds,
        config.max_watch_stale_book_age_seconds,
    )
    fee_slippage_cushion_score = _bounded_ratio(
        fee_slippage_cushion_ratio,
        config.min_pass_fee_slippage_cushion_ratio,
    )
    depth_shock_absorption_score = _depth_shock_absorption_score(
        depth_absorption_score=depth_absorption_score,
        spread_resilience_score=spread_resilience_score,
        imbalance_stability_score=imbalance_stability_score,
        freshness_score=freshness_score,
        fee_slippage_cushion_score=fee_slippage_cushion_score,
        config=config,
    )
    status = _row_status(
        shock_shortfall_ratio=shock_shortfall_ratio,
        spread_widening=observation.spread_widening,
        imbalance_volatility=observation.imbalance_volatility,
        stale_book_age_seconds=stale_book_age_seconds,
        fee_slippage_cushion_ratio=fee_slippage_cushion_ratio,
        depth_shock_absorption_score=depth_shock_absorption_score,
        config=config,
    )
    return ResearchMarketDepthShockAbsorptionRow(
        absorption_group_ref=absorption_group_ref,
        observed_at=observation.observed_at,
        last_book_update_at=observation.last_book_update_at,
        stale_book_age_seconds=stale_book_age_seconds,
        target_shock_probability=observation.target_shock_probability,
        near_band_depth=observation.near_band_depth,
        mid_band_depth=observation.mid_band_depth,
        far_band_depth=observation.far_band_depth,
        total_band_depth=total_band_depth,
        fee_slippage_cushion=fee_slippage_cushion,
        fee_slippage_cushion_ratio=fee_slippage_cushion_ratio,
        net_absorbable_probability=net_absorbable_probability,
        net_depth_coverage_ratio=net_depth_coverage_ratio,
        shock_shortfall_ratio=shock_shortfall_ratio,
        spread_widening=observation.spread_widening,
        imbalance_volatility=observation.imbalance_volatility,
        stale_book_pressure=stale_book_pressure,
        depth_absorption_score=depth_absorption_score,
        spread_resilience_score=spread_resilience_score,
        imbalance_stability_score=imbalance_stability_score,
        freshness_score=freshness_score,
        fee_slippage_cushion_score=fee_slippage_cushion_score,
        depth_shock_absorption_score=depth_shock_absorption_score,
        status=status,
        reason_codes=_row_reason_codes(
            observation=observation,
            shock_shortfall_ratio=shock_shortfall_ratio,
            spread_widening=observation.spread_widening,
            imbalance_volatility=observation.imbalance_volatility,
            stale_book_age_seconds=stale_book_age_seconds,
            fee_slippage_cushion_ratio=fee_slippage_cushion_ratio,
            status=status,
            config=config,
        ),
    )


def _depth_shock_absorption_score(
    *,
    depth_absorption_score: Decimal,
    spread_resilience_score: Decimal,
    imbalance_stability_score: Decimal,
    freshness_score: Decimal,
    fee_slippage_cushion_score: Decimal,
    config: ResearchMarketDepthShockAbsorptionConfig,
) -> Decimal:
    return _quantize(
        depth_absorption_score * config.depth_absorption_weight
        + spread_resilience_score * config.spread_resilience_weight
        + imbalance_stability_score * config.imbalance_stability_weight
        + freshness_score * config.freshness_weight
        + fee_slippage_cushion_score * config.fee_slippage_cushion_weight,
    )


def _row_status(
    *,
    shock_shortfall_ratio: Decimal,
    spread_widening: Decimal,
    imbalance_volatility: Decimal,
    stale_book_age_seconds: Decimal,
    fee_slippage_cushion_ratio: Decimal,
    depth_shock_absorption_score: Decimal,
    config: ResearchMarketDepthShockAbsorptionConfig,
) -> str:
    if (
        depth_shock_absorption_score < config.watch_absorption_score
        or shock_shortfall_ratio >= config.max_watch_shock_shortfall_ratio
        or spread_widening >= config.max_watch_spread_widening
        or imbalance_volatility >= config.max_watch_imbalance_volatility
        or stale_book_age_seconds >= config.max_watch_stale_book_age_seconds
        or fee_slippage_cushion_ratio < config.min_watch_fee_slippage_cushion_ratio
    ):
        return "block"
    if (
        depth_shock_absorption_score < config.pass_absorption_score
        or shock_shortfall_ratio >= config.max_pass_shock_shortfall_ratio
        or spread_widening >= config.max_pass_spread_widening
        or imbalance_volatility >= config.max_pass_imbalance_volatility
        or stale_book_age_seconds >= config.max_pass_stale_book_age_seconds
        or fee_slippage_cushion_ratio < config.min_pass_fee_slippage_cushion_ratio
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    observation: ResearchMarketDepthShockAbsorptionObservation,
    shock_shortfall_ratio: Decimal,
    spread_widening: Decimal,
    imbalance_volatility: Decimal,
    stale_book_age_seconds: Decimal,
    fee_slippage_cushion_ratio: Decimal,
    status: str,
    config: ResearchMarketDepthShockAbsorptionConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"depth_shock_absorption_{status}"}
    reason_codes.add(
        _upper_threshold_reason(
            "depth_band_shortfall",
            shock_shortfall_ratio,
            config.max_pass_shock_shortfall_ratio,
            config.max_watch_shock_shortfall_ratio,
        ),
    )
    reason_codes.add(
        _upper_threshold_reason(
            "spread_widening",
            spread_widening,
            config.max_pass_spread_widening,
            config.max_watch_spread_widening,
        ),
    )
    reason_codes.add(
        _upper_threshold_reason(
            "imbalance_volatility",
            imbalance_volatility,
            config.max_pass_imbalance_volatility,
            config.max_watch_imbalance_volatility,
        ),
    )
    reason_codes.add(
        _upper_threshold_reason(
            "stale_book_age",
            stale_book_age_seconds,
            config.max_pass_stale_book_age_seconds,
            config.max_watch_stale_book_age_seconds,
        ),
    )
    reason_codes.add(
        _lower_threshold_reason(
            "fee_slippage_cushion",
            fee_slippage_cushion_ratio,
            config.min_pass_fee_slippage_cushion_ratio,
            config.min_watch_fee_slippage_cushion_ratio,
        ),
    )
    for reason_code in observation.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _upper_threshold_reason(
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


def _lower_threshold_reason(
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


def _normalize_observations(
    observations: Iterable[ResearchMarketDepthShockAbsorptionObservation],
) -> tuple[ResearchMarketDepthShockAbsorptionObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchMarketDepthShockAbsorptionObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketDepthShockAbsorptionObservation values",
            )
        _require_hard_flags("observation", value)
    keys = tuple(value.book_snapshot_key for value in values)
    if len(set(keys)) != len(keys):
        raise ValueError("book_snapshot_key values must be unique")
    return values


def _normalize_rows(
    rows: tuple[ResearchMarketDepthShockAbsorptionRow, ...],
) -> tuple[ResearchMarketDepthShockAbsorptionRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketDepthShockAbsorptionRow:
            raise ValueError(
                "rows must contain ResearchMarketDepthShockAbsorptionRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=lambda row: row.absorption_group_ref)):
        raise ValueError("rows must be sorted by absorption_group_ref")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketDepthShockAbsorptionReasonCodeCount, ...],
) -> tuple[ResearchMarketDepthShockAbsorptionReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketDepthShockAbsorptionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketDepthShockAbsorptionReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    if counts != tuple(sorted(counts, key=lambda count: count.reason_code)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row(row: ResearchMarketDepthShockAbsorptionRow) -> None:
    expected_total_depth = _quantize(
        row.near_band_depth + row.mid_band_depth + row.far_band_depth,
    )
    if row.total_band_depth != expected_total_depth:
        raise ValueError("total_band_depth must match depth bands")
    expected_net_absorbable = _quantize(row.total_band_depth + row.fee_slippage_cushion)
    if row.net_absorbable_probability != expected_net_absorbable:
        raise ValueError("net_absorbable_probability must match depth and cushion")
    if row.net_depth_coverage_ratio != _bounded_ratio(
        row.net_absorbable_probability,
        row.target_shock_probability,
    ):
        raise ValueError("net_depth_coverage_ratio must match shock depth fields")
    if row.shock_shortfall_ratio != _shortfall_ratio(
        row.net_absorbable_probability,
        row.target_shock_probability,
    ):
        raise ValueError("shock_shortfall_ratio must match shock depth fields")
    if f"depth_shock_absorption_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchMarketDepthShockAbsorptionReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_depth_shock_absorption_score != _average_score(report.rows):
        raise ValueError("average_depth_shock_absorption_score must match rows")
    if report.min_net_depth_coverage_ratio != _min_or_zero(
        tuple(row.net_depth_coverage_ratio for row in report.rows),
    ):
        raise ValueError("min_net_depth_coverage_ratio must match rows")
    if report.max_shock_shortfall_ratio != _max_or_zero(
        tuple(row.shock_shortfall_ratio for row in report.rows),
    ):
        raise ValueError("max_shock_shortfall_ratio must match rows")
    if report.max_spread_widening != _max_or_zero(
        tuple(row.spread_widening for row in report.rows),
    ):
        raise ValueError("max_spread_widening must match rows")
    if report.max_imbalance_volatility != _max_or_zero(
        tuple(row.imbalance_volatility for row in report.rows),
    ):
        raise ValueError("max_imbalance_volatility must match rows")
    if report.max_stale_book_age_seconds != _max_or_zero(
        tuple(row.stale_book_age_seconds for row in report.rows),
    ):
        raise ValueError("max_stale_book_age_seconds must match rows")
    if report.min_fee_slippage_cushion_ratio != _min_or_zero(
        tuple(row.fee_slippage_cushion_ratio for row in report.rows),
    ):
        raise ValueError("min_fee_slippage_cushion_ratio must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _summary_status(rows: tuple[ResearchMarketDepthShockAbsorptionRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchMarketDepthShockAbsorptionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_depth_shock_absorption_observations",)
    if all(row.status == "pass" for row in rows):
        return ("depth_shock_absorption_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchMarketDepthShockAbsorptionRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketDepthShockAbsorptionReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketDepthShockAbsorptionReasonCodeCount(
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
        ResearchMarketDepthShockAbsorptionReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(_decimal_count(count) / total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_score(
    rows: tuple[ResearchMarketDepthShockAbsorptionRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.depth_shock_absorption_score for row in rows), ZERO)
        / _decimal_count(len(rows)),
    )


def _bounded_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _quantize(min(ONE, value / denominator))


def _shortfall_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    if value >= denominator:
        return ZERO
    return _quantize((denominator - value) / denominator)


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


def _min_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _status_count(
    rows: tuple[ResearchMarketDepthShockAbsorptionRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _observation_sort_key(
    value: ResearchMarketDepthShockAbsorptionObservation,
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
    if isinstance(value, Mapping):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _derived_report_digest(report: ResearchMarketDepthShockAbsorptionReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("report digest payload", digest_payload)
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


def _require_positive_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_ratio_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


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
    if type(value) is not str or value not in DEPTH_SHOCK_ABSORPTION_STATUSES:
        raise ValueError(f"{field_name} must be one of {DEPTH_SHOCK_ABSORPTION_STATUSES}")


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


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(label: str, value: str) -> None:
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{label} contains unsafe public surface text")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
