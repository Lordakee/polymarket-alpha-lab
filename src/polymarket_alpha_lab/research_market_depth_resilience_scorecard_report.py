"""Pure report-only scorecard for public depth resilience review."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "MARKET_DEPTH_RESILIENCE_SCORECARD_STATUSES",
    "DEFAULT_RESEARCH_MARKET_DEPTH_RESILIENCE_SCORECARD_REPORT_CONFIG_VERSION",
    "ResearchMarketDepthResilienceScorecardConfig",
    "ResearchMarketDepthResilienceScorecardInput",
    "ResearchMarketDepthResilienceScorecardReasonCodeCount",
    "ResearchMarketDepthResilienceScorecardReport",
    "ResearchMarketDepthResilienceScorecardRow",
    "build_research_market_depth_resilience_scorecard_report",
    "research_market_depth_resilience_scorecard_report_digest",
    "research_market_depth_resilience_scorecard_report_payload",
)


DEFAULT_RESEARCH_MARKET_DEPTH_RESILIENCE_SCORECARD_REPORT_CONFIG_VERSION = (
    "research-market-depth-resilience-scorecard-report-v0"
)
MARKET_DEPTH_RESILIENCE_SCORECARD_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("condition", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("h", "ttp"),
    _join_parts("u", "rl"),
    _join_parts("sour", "ce", "_", "url"),
    _join_parts("sour", "ce", "_", "text"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le"),
    _join_parts("tab", "le", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    _join_parts("exec", "ution"),
    "://",
)
COMPONENT_REASON_PRIORITY = (
    "depth_band_block",
    "spread_stability_block",
    "book_age_block",
    "imbalance_volatility_block",
    "fee_drag_block",
    "slippage_cushion_block",
    "settlement_friction_block",
    "depth_band_watch",
    "spread_stability_watch",
    "book_age_watch",
    "imbalance_volatility_watch",
    "fee_drag_watch",
    "slippage_cushion_watch",
    "settlement_friction_watch",
)
DECIMAL_PAYLOAD_RE = re.compile(r"^(0|[1-9][0-9]*)\.[0-9]{6}$")
REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "observation_count",
    "pass_count",
    "watch_count",
    "block_count",
    "depth_band_pressure_count",
    "spread_instability_count",
    "stale_book_count",
    "imbalance_volatility_count",
    "fee_drag_count",
    "slippage_cushion_count",
    "settlement_friction_count",
    "average_resilience_score",
    "min_depth_band_score",
    "min_spread_stability_ratio",
    "max_book_age_seconds",
    "max_imbalance_volatility_ratio",
    "max_fee_drag_ratio",
    "min_slippage_cushion_ratio",
    "max_settlement_friction_ratio",
    "status",
    "rows",
    "reason_code_counts",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_FIELDS = (
    "public_row_ref",
    "observed_at",
    "near_band_depth_ratio",
    "mid_band_depth_ratio",
    "far_band_depth_ratio",
    "near_depth_band_weight",
    "mid_depth_band_weight",
    "far_depth_band_weight",
    "depth_band_score",
    "spread_stability_ratio",
    "spread_stability_score",
    "book_age_seconds",
    "book_age_score",
    "imbalance_volatility_ratio",
    "imbalance_stability_score",
    "fee_drag_ratio",
    "fee_drag_score",
    "slippage_cushion_ratio",
    "slippage_cushion_score",
    "settlement_friction_ratio",
    "settlement_friction_score",
    "depth_band_weight",
    "spread_stability_weight",
    "book_age_weight",
    "imbalance_volatility_weight",
    "fee_drag_weight",
    "slippage_cushion_weight",
    "settlement_friction_weight",
    "resilience_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_CODE_COUNT_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "row_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_WHOLE_DECIMAL_FIELDS = (
    "observation_count",
    "pass_count",
    "watch_count",
    "block_count",
    "depth_band_pressure_count",
    "spread_instability_count",
    "stale_book_count",
    "imbalance_volatility_count",
    "fee_drag_count",
    "slippage_cushion_count",
    "settlement_friction_count",
)
REPORT_RATIO_DECIMAL_FIELDS = (
    "min_depth_band_score",
    "min_spread_stability_ratio",
    "max_imbalance_volatility_ratio",
    "max_fee_drag_ratio",
    "min_slippage_cushion_ratio",
    "max_settlement_friction_ratio",
)
ROW_RATIO_DECIMAL_FIELDS = (
    "near_band_depth_ratio",
    "mid_band_depth_ratio",
    "far_band_depth_ratio",
    "near_depth_band_weight",
    "mid_depth_band_weight",
    "far_depth_band_weight",
    "depth_band_score",
    "spread_stability_ratio",
    "spread_stability_score",
    "book_age_score",
    "imbalance_volatility_ratio",
    "imbalance_stability_score",
    "fee_drag_ratio",
    "fee_drag_score",
    "slippage_cushion_ratio",
    "slippage_cushion_score",
    "settlement_friction_ratio",
    "settlement_friction_score",
    "depth_band_weight",
    "spread_stability_weight",
    "book_age_weight",
    "imbalance_volatility_weight",
    "fee_drag_weight",
    "slippage_cushion_weight",
    "settlement_friction_weight",
    "resilience_score",
)


class _Missing:
    pass


MISSING = _Missing()


@dataclass(frozen=True)
class ResearchMarketDepthResilienceScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_DEPTH_RESILIENCE_SCORECARD_REPORT_CONFIG_VERSION
    )
    minimum_pass_depth_band_score: Decimal = Decimal("0.700000")
    minimum_watch_depth_band_score: Decimal = Decimal("0.400000")
    minimum_pass_spread_stability_ratio: Decimal = Decimal("0.750000")
    minimum_watch_spread_stability_ratio: Decimal = Decimal("0.450000")
    maximum_pass_book_age_seconds: Decimal = Decimal("120.000000")
    maximum_watch_book_age_seconds: Decimal = Decimal("900.000000")
    maximum_pass_imbalance_volatility_ratio: Decimal = Decimal("0.200000")
    maximum_watch_imbalance_volatility_ratio: Decimal = Decimal("0.600000")
    maximum_pass_fee_drag_ratio: Decimal = Decimal("0.010000")
    maximum_watch_fee_drag_ratio: Decimal = Decimal("0.030000")
    minimum_pass_slippage_cushion_ratio: Decimal = Decimal("0.700000")
    minimum_watch_slippage_cushion_ratio: Decimal = Decimal("0.400000")
    maximum_pass_settlement_friction_ratio: Decimal = Decimal("0.150000")
    maximum_watch_settlement_friction_ratio: Decimal = Decimal("0.500000")
    near_depth_band_weight: Decimal = Decimal("0.500000")
    mid_depth_band_weight: Decimal = Decimal("0.300000")
    far_depth_band_weight: Decimal = Decimal("0.200000")
    depth_band_weight: Decimal = Decimal("0.250000")
    spread_stability_weight: Decimal = Decimal("0.150000")
    book_age_weight: Decimal = Decimal("0.150000")
    imbalance_volatility_weight: Decimal = Decimal("0.150000")
    fee_drag_weight: Decimal = Decimal("0.100000")
    slippage_cushion_weight: Decimal = Decimal("0.100000")
    settlement_friction_weight: Decimal = Decimal("0.100000")
    pass_resilience_score: Decimal = Decimal("0.750000")
    watch_resilience_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthResilienceScorecardConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_RESILIENCE_SCORECARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "minimum_pass_depth_band_score",
            "minimum_watch_depth_band_score",
            "minimum_pass_spread_stability_ratio",
            "minimum_watch_spread_stability_ratio",
            "maximum_pass_imbalance_volatility_ratio",
            "maximum_watch_imbalance_volatility_ratio",
            "maximum_pass_fee_drag_ratio",
            "maximum_watch_fee_drag_ratio",
            "minimum_pass_slippage_cushion_ratio",
            "minimum_watch_slippage_cushion_ratio",
            "maximum_pass_settlement_friction_ratio",
            "maximum_watch_settlement_friction_ratio",
            "near_depth_band_weight",
            "mid_depth_band_weight",
            "far_depth_band_weight",
            "depth_band_weight",
            "spread_stability_weight",
            "book_age_weight",
            "imbalance_volatility_weight",
            "fee_drag_weight",
            "slippage_cushion_weight",
            "settlement_friction_weight",
            "pass_resilience_score",
            "watch_resilience_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_pass_book_age_seconds",
            "maximum_watch_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_watch_imbalance_volatility_ratio",
            "maximum_watch_fee_drag_ratio",
            "maximum_watch_settlement_friction_ratio",
        ):
            if getattr(self, field_name) <= ZERO:
                raise ValueError(f"{field_name} must be positive")
        if self.minimum_pass_depth_band_score < self.minimum_watch_depth_band_score:
            raise ValueError("minimum_pass_depth_band_score must be at least watch")
        if (
            self.minimum_pass_spread_stability_ratio
            < self.minimum_watch_spread_stability_ratio
        ):
            raise ValueError("minimum_pass_spread_stability_ratio must be at least watch")
        if self.maximum_pass_book_age_seconds > self.maximum_watch_book_age_seconds:
            raise ValueError("maximum_pass_book_age_seconds must not exceed watch")
        if (
            self.maximum_pass_imbalance_volatility_ratio
            > self.maximum_watch_imbalance_volatility_ratio
        ):
            raise ValueError("maximum_pass_imbalance_volatility_ratio must not exceed watch")
        if self.maximum_pass_fee_drag_ratio > self.maximum_watch_fee_drag_ratio:
            raise ValueError("maximum_pass_fee_drag_ratio must not exceed watch")
        if self.minimum_pass_slippage_cushion_ratio < self.minimum_watch_slippage_cushion_ratio:
            raise ValueError("minimum_pass_slippage_cushion_ratio must be at least watch")
        if (
            self.maximum_pass_settlement_friction_ratio
            > self.maximum_watch_settlement_friction_ratio
        ):
            raise ValueError("maximum_pass_settlement_friction_ratio must not exceed watch")
        if self.pass_resilience_score < self.watch_resilience_score:
            raise ValueError("pass_resilience_score must be at least watch")
        depth_weight_sum = _quantize(
            self.near_depth_band_weight
            + self.mid_depth_band_weight
            + self.far_depth_band_weight,
        )
        if depth_weight_sum != ONE:
            raise ValueError("depth band weights must sum to 1")
        resilience_weight_sum = _quantize(
            self.depth_band_weight
            + self.spread_stability_weight
            + self.book_age_weight
            + self.imbalance_volatility_weight
            + self.fee_drag_weight
            + self.slippage_cushion_weight
            + self.settlement_friction_weight,
        )
        if resilience_weight_sum != ONE:
            raise ValueError("resilience weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthResilienceScorecardInput:
    public_observation_label: str
    observed_at: datetime
    near_band_depth_ratio: Decimal
    mid_band_depth_ratio: Decimal
    far_band_depth_ratio: Decimal
    spread_stability_ratio: Decimal
    book_age_seconds: Decimal
    imbalance_volatility_ratio: Decimal
    fee_drag_ratio: Decimal
    slippage_cushion_ratio: Decimal
    settlement_friction_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthResilienceScorecardInput, "input")
        _require_public_label("public_observation_label", self.public_observation_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "near_band_depth_ratio",
            "mid_band_depth_ratio",
            "far_band_depth_ratio",
            "spread_stability_ratio",
            "imbalance_volatility_ratio",
            "fee_drag_ratio",
            "slippage_cushion_ratio",
            "settlement_friction_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "book_age_seconds",
            _require_nonnegative_decimal("book_age_seconds", self.book_age_seconds),
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
class ResearchMarketDepthResilienceScorecardRow:
    public_row_ref: str
    observed_at: datetime
    near_band_depth_ratio: Decimal
    mid_band_depth_ratio: Decimal
    far_band_depth_ratio: Decimal
    near_depth_band_weight: Decimal
    mid_depth_band_weight: Decimal
    far_depth_band_weight: Decimal
    depth_band_score: Decimal
    spread_stability_ratio: Decimal
    spread_stability_score: Decimal
    book_age_seconds: Decimal
    book_age_score: Decimal
    imbalance_volatility_ratio: Decimal
    imbalance_stability_score: Decimal
    fee_drag_ratio: Decimal
    fee_drag_score: Decimal
    slippage_cushion_ratio: Decimal
    slippage_cushion_score: Decimal
    settlement_friction_ratio: Decimal
    settlement_friction_score: Decimal
    depth_band_weight: Decimal
    spread_stability_weight: Decimal
    book_age_weight: Decimal
    imbalance_volatility_weight: Decimal
    fee_drag_weight: Decimal
    slippage_cushion_weight: Decimal
    settlement_friction_weight: Decimal
    resilience_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthResilienceScorecardRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "book_age_seconds",
            _require_nonnegative_decimal("book_age_seconds", self.book_age_seconds),
        )
        for field_name in (
            "near_band_depth_ratio",
            "mid_band_depth_ratio",
            "far_band_depth_ratio",
            "near_depth_band_weight",
            "mid_depth_band_weight",
            "far_depth_band_weight",
            "depth_band_score",
            "spread_stability_ratio",
            "spread_stability_score",
            "book_age_score",
            "imbalance_volatility_ratio",
            "imbalance_stability_score",
            "fee_drag_ratio",
            "fee_drag_score",
            "slippage_cushion_ratio",
            "slippage_cushion_score",
            "settlement_friction_ratio",
            "settlement_friction_score",
            "depth_band_weight",
            "spread_stability_weight",
            "book_age_weight",
            "imbalance_volatility_weight",
            "fee_drag_weight",
            "slippage_cushion_weight",
            "settlement_friction_weight",
            "resilience_score",
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
class ResearchMarketDepthResilienceScorecardReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthResilienceScorecardReasonCodeCount,
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
class ResearchMarketDepthResilienceScorecardReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    depth_band_pressure_count: Decimal
    spread_instability_count: Decimal
    stale_book_count: Decimal
    imbalance_volatility_count: Decimal
    fee_drag_count: Decimal
    slippage_cushion_count: Decimal
    settlement_friction_count: Decimal
    average_resilience_score: Decimal | None
    min_depth_band_score: Decimal
    min_spread_stability_ratio: Decimal
    max_book_age_seconds: Decimal
    max_imbalance_volatility_ratio: Decimal
    max_fee_drag_ratio: Decimal
    min_slippage_cushion_ratio: Decimal
    max_settlement_friction_ratio: Decimal
    status: str
    rows: tuple[ResearchMarketDepthResilienceScorecardRow, ...]
    reason_code_counts: tuple[ResearchMarketDepthResilienceScorecardReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthResilienceScorecardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_RESILIENCE_SCORECARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "depth_band_pressure_count",
            "spread_instability_count",
            "stale_book_count",
            "imbalance_volatility_count",
            "fee_drag_count",
            "slippage_cushion_count",
            "settlement_friction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_resilience_score",
            _require_optional_ratio_decimal(
                "average_resilience_score",
                self.average_resilience_score,
            ),
        )
        object.__setattr__(
            self,
            "max_book_age_seconds",
            _require_nonnegative_decimal("max_book_age_seconds", self.max_book_age_seconds),
        )
        for field_name in (
            "min_depth_band_score",
            "min_spread_stability_ratio",
            "max_imbalance_volatility_ratio",
            "max_fee_drag_ratio",
            "min_slippage_cushion_ratio",
            "max_settlement_friction_ratio",
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


def build_research_market_depth_resilience_scorecard_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketDepthResilienceScorecardConfig,
    generated_at: datetime,
) -> ResearchMarketDepthResilienceScorecardReport:
    if type(config) is not ResearchMarketDepthResilienceScorecardConfig:
        raise ValueError("config must be a ResearchMarketDepthResilienceScorecardConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    sorted_items = tuple(sorted(input_items, key=lambda item: item.public_observation_label))
    rows = tuple(
        _row_from_input(
            item,
            public_row_ref=f"depth_resilience_group_{index:03d}",
            config=config,
        )
        for index, item in enumerate(sorted_items, start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketDepthResilienceScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        depth_band_pressure_count=_decimal_count(_reason_count(rows, "depth_band")),
        spread_instability_count=_decimal_count(_reason_count(rows, "spread_stability")),
        stale_book_count=_decimal_count(_reason_count(rows, "book_age")),
        imbalance_volatility_count=_decimal_count(
            _reason_count(rows, "imbalance_volatility"),
        ),
        fee_drag_count=_decimal_count(_reason_count(rows, "fee_drag")),
        slippage_cushion_count=_decimal_count(_reason_count(rows, "slippage_cushion")),
        settlement_friction_count=_decimal_count(
            _reason_count(rows, "settlement_friction"),
        ),
        average_resilience_score=_average_resilience_score(rows),
        min_depth_band_score=_minimum_row_value(rows, "depth_band_score"),
        min_spread_stability_ratio=_minimum_row_value(rows, "spread_stability_ratio"),
        max_book_age_seconds=_maximum_row_value(rows, "book_age_seconds"),
        max_imbalance_volatility_ratio=_maximum_row_value(
            rows,
            "imbalance_volatility_ratio",
        ),
        max_fee_drag_ratio=_maximum_row_value(rows, "fee_drag_ratio"),
        min_slippage_cushion_ratio=_minimum_row_value(rows, "slippage_cushion_ratio"),
        max_settlement_friction_ratio=_maximum_row_value(
            rows,
            "settlement_friction_ratio",
        ),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_depth_resilience_scorecard_report_payload(
    report: ResearchMarketDepthResilienceScorecardReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketDepthResilienceScorecardReport:
        raise ValueError("report must be a ResearchMarketDepthResilienceScorecardReport")
    _require_hard_flags("report", report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload_schema(payload, allow_empty_digest=False)
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload(payload)
    return payload


def research_market_depth_resilience_scorecard_report_digest(
    report: ResearchMarketDepthResilienceScorecardReport,
) -> str:
    if type(report) is not ResearchMarketDepthResilienceScorecardReport:
        raise ValueError("report must be a ResearchMarketDepthResilienceScorecardReport")
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
    item: ResearchMarketDepthResilienceScorecardInput,
    *,
    public_row_ref: str,
    config: ResearchMarketDepthResilienceScorecardConfig,
) -> ResearchMarketDepthResilienceScorecardRow:
    depth_band_score = _depth_band_score(item, config)
    spread_stability_score = item.spread_stability_ratio
    book_age_score = _book_age_score(item.book_age_seconds, config)
    imbalance_stability_score = _inverse_ratio_score(
        item.imbalance_volatility_ratio,
        config.maximum_watch_imbalance_volatility_ratio,
    )
    fee_drag_score = _inverse_ratio_score(
        item.fee_drag_ratio,
        config.maximum_watch_fee_drag_ratio,
    )
    slippage_cushion_score = item.slippage_cushion_ratio
    settlement_friction_score = _inverse_ratio_score(
        item.settlement_friction_ratio,
        config.maximum_watch_settlement_friction_ratio,
    )
    resilience_score = _resilience_score(
        depth_band_score=depth_band_score,
        spread_stability_score=spread_stability_score,
        book_age_score=book_age_score,
        imbalance_stability_score=imbalance_stability_score,
        fee_drag_score=fee_drag_score,
        slippage_cushion_score=slippage_cushion_score,
        settlement_friction_score=settlement_friction_score,
        config=config,
    )
    status = _row_status(
        depth_band_score=depth_band_score,
        spread_stability_ratio=item.spread_stability_ratio,
        book_age_seconds=item.book_age_seconds,
        imbalance_volatility_ratio=item.imbalance_volatility_ratio,
        fee_drag_ratio=item.fee_drag_ratio,
        slippage_cushion_ratio=item.slippage_cushion_ratio,
        settlement_friction_ratio=item.settlement_friction_ratio,
        resilience_score=resilience_score,
        config=config,
    )
    return ResearchMarketDepthResilienceScorecardRow(
        public_row_ref=public_row_ref,
        observed_at=item.observed_at,
        near_band_depth_ratio=item.near_band_depth_ratio,
        mid_band_depth_ratio=item.mid_band_depth_ratio,
        far_band_depth_ratio=item.far_band_depth_ratio,
        near_depth_band_weight=config.near_depth_band_weight,
        mid_depth_band_weight=config.mid_depth_band_weight,
        far_depth_band_weight=config.far_depth_band_weight,
        depth_band_score=depth_band_score,
        spread_stability_ratio=item.spread_stability_ratio,
        spread_stability_score=spread_stability_score,
        book_age_seconds=item.book_age_seconds,
        book_age_score=book_age_score,
        imbalance_volatility_ratio=item.imbalance_volatility_ratio,
        imbalance_stability_score=imbalance_stability_score,
        fee_drag_ratio=item.fee_drag_ratio,
        fee_drag_score=fee_drag_score,
        slippage_cushion_ratio=item.slippage_cushion_ratio,
        slippage_cushion_score=slippage_cushion_score,
        settlement_friction_ratio=item.settlement_friction_ratio,
        settlement_friction_score=settlement_friction_score,
        depth_band_weight=config.depth_band_weight,
        spread_stability_weight=config.spread_stability_weight,
        book_age_weight=config.book_age_weight,
        imbalance_volatility_weight=config.imbalance_volatility_weight,
        fee_drag_weight=config.fee_drag_weight,
        slippage_cushion_weight=config.slippage_cushion_weight,
        settlement_friction_weight=config.settlement_friction_weight,
        resilience_score=resilience_score,
        status=status,
        reason_codes=_row_reason_codes(item, depth_band_score, status, config),
    )


def _depth_band_score(
    item: ResearchMarketDepthResilienceScorecardInput,
    config: ResearchMarketDepthResilienceScorecardConfig,
) -> Decimal:
    return _quantize(
        item.near_band_depth_ratio * config.near_depth_band_weight
        + item.mid_band_depth_ratio * config.mid_depth_band_weight
        + item.far_band_depth_ratio * config.far_depth_band_weight,
    )


def _book_age_score(
    book_age_seconds: Decimal,
    config: ResearchMarketDepthResilienceScorecardConfig,
) -> Decimal:
    if book_age_seconds <= config.maximum_pass_book_age_seconds:
        return ONE
    if book_age_seconds >= config.maximum_watch_book_age_seconds:
        return ZERO
    age_band = config.maximum_watch_book_age_seconds - config.maximum_pass_book_age_seconds
    return _quantize(ONE - ((book_age_seconds - config.maximum_pass_book_age_seconds) / age_band))


def _inverse_ratio_score(value: Decimal, zero_at: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = ONE - (value / zero_at)
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return _quantize(score)


def _resilience_score(
    *,
    depth_band_score: Decimal,
    spread_stability_score: Decimal,
    book_age_score: Decimal,
    imbalance_stability_score: Decimal,
    fee_drag_score: Decimal,
    slippage_cushion_score: Decimal,
    settlement_friction_score: Decimal,
    config: ResearchMarketDepthResilienceScorecardConfig,
) -> Decimal:
    return _quantize(
        depth_band_score * config.depth_band_weight
        + spread_stability_score * config.spread_stability_weight
        + book_age_score * config.book_age_weight
        + imbalance_stability_score * config.imbalance_volatility_weight
        + fee_drag_score * config.fee_drag_weight
        + slippage_cushion_score * config.slippage_cushion_weight
        + settlement_friction_score * config.settlement_friction_weight,
    )


def _row_status(
    *,
    depth_band_score: Decimal,
    spread_stability_ratio: Decimal,
    book_age_seconds: Decimal,
    imbalance_volatility_ratio: Decimal,
    fee_drag_ratio: Decimal,
    slippage_cushion_ratio: Decimal,
    settlement_friction_ratio: Decimal,
    resilience_score: Decimal,
    config: ResearchMarketDepthResilienceScorecardConfig,
) -> str:
    if (
        depth_band_score < config.minimum_watch_depth_band_score
        or spread_stability_ratio < config.minimum_watch_spread_stability_ratio
        or book_age_seconds > config.maximum_watch_book_age_seconds
        or imbalance_volatility_ratio > config.maximum_watch_imbalance_volatility_ratio
        or fee_drag_ratio > config.maximum_watch_fee_drag_ratio
        or slippage_cushion_ratio < config.minimum_watch_slippage_cushion_ratio
        or settlement_friction_ratio > config.maximum_watch_settlement_friction_ratio
        or resilience_score < config.watch_resilience_score
    ):
        return "block"
    if (
        depth_band_score < config.minimum_pass_depth_band_score
        or spread_stability_ratio < config.minimum_pass_spread_stability_ratio
        or book_age_seconds > config.maximum_pass_book_age_seconds
        or imbalance_volatility_ratio > config.maximum_pass_imbalance_volatility_ratio
        or fee_drag_ratio > config.maximum_pass_fee_drag_ratio
        or slippage_cushion_ratio < config.minimum_pass_slippage_cushion_ratio
        or settlement_friction_ratio > config.maximum_pass_settlement_friction_ratio
        or resilience_score < config.pass_resilience_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchMarketDepthResilienceScorecardInput,
    depth_band_score: Decimal,
    status: str,
    config: ResearchMarketDepthResilienceScorecardConfig,
) -> tuple[str, ...]:
    codes = {
        f"depth_resilience_{status}",
        _low_value_component_reason(
            prefix="depth_band",
            value=depth_band_score,
            pass_threshold=config.minimum_pass_depth_band_score,
            block_threshold=config.minimum_watch_depth_band_score,
        ),
        _low_value_component_reason(
            prefix="spread_stability",
            value=item.spread_stability_ratio,
            pass_threshold=config.minimum_pass_spread_stability_ratio,
            block_threshold=config.minimum_watch_spread_stability_ratio,
        ),
        _high_value_component_reason(
            prefix="book_age",
            value=item.book_age_seconds,
            pass_threshold=config.maximum_pass_book_age_seconds,
            block_threshold=config.maximum_watch_book_age_seconds,
        ),
        _high_value_component_reason(
            prefix="imbalance_volatility",
            value=item.imbalance_volatility_ratio,
            pass_threshold=config.maximum_pass_imbalance_volatility_ratio,
            block_threshold=config.maximum_watch_imbalance_volatility_ratio,
        ),
        _high_value_component_reason(
            prefix="fee_drag",
            value=item.fee_drag_ratio,
            pass_threshold=config.maximum_pass_fee_drag_ratio,
            block_threshold=config.maximum_watch_fee_drag_ratio,
        ),
        _low_value_component_reason(
            prefix="slippage_cushion",
            value=item.slippage_cushion_ratio,
            pass_threshold=config.minimum_pass_slippage_cushion_ratio,
            block_threshold=config.minimum_watch_slippage_cushion_ratio,
        ),
        _high_value_component_reason(
            prefix="settlement_friction",
            value=item.settlement_friction_ratio,
            pass_threshold=config.maximum_pass_settlement_friction_ratio,
            block_threshold=config.maximum_watch_settlement_friction_ratio,
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
) -> tuple[ResearchMarketDepthResilienceScorecardInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    normalized = tuple(_coerce_input(value) for value in values)
    seen: set[str] = set()
    for item in normalized:
        if item.public_observation_label in seen:
            raise ValueError("public_observation_label values must be unique")
        seen.add(item.public_observation_label)
    return normalized


def _coerce_input(value: object) -> ResearchMarketDepthResilienceScorecardInput:
    if type(value) is ResearchMarketDepthResilienceScorecardInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchMarketDepthResilienceScorecardInput(
        public_observation_label=_field_value(value, "public_observation_label"),
        observed_at=_field_value(value, "observed_at"),
        near_band_depth_ratio=_field_value(value, "near_band_depth_ratio"),
        mid_band_depth_ratio=_field_value(value, "mid_band_depth_ratio"),
        far_band_depth_ratio=_field_value(value, "far_band_depth_ratio"),
        spread_stability_ratio=_field_value(value, "spread_stability_ratio"),
        book_age_seconds=_field_value(value, "book_age_seconds"),
        imbalance_volatility_ratio=_field_value(value, "imbalance_volatility_ratio"),
        fee_drag_ratio=_field_value(value, "fee_drag_ratio"),
        slippage_cushion_ratio=_field_value(value, "slippage_cushion_ratio"),
        settlement_friction_ratio=_field_value(value, "settlement_friction_ratio"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _field_value(value: object, name: str, default: object = MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        if any(field.name == name for field in fields(value)):
            return getattr(value, name)
    elif isinstance(value, Mapping):
        if name in value:
            return value[name]
    elif hasattr(value, name):
        return getattr(value, name)
    if default is not MISSING:
        return default
    raise ValueError(f"{name} is required")


def _summary_reason_codes(
    rows: tuple[ResearchMarketDepthResilienceScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_depth_resilience_observations",)
    if all(row.status == "pass" for row in rows):
        return ("depth_resilience_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("depth_resilience_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("depth_resilience_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in COMPONENT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_depth_resilience_observations",):
        return "block"
    if "depth_resilience_block" in reason_codes:
        return "block"
    if "depth_resilience_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketDepthResilienceScorecardRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketDepthResilienceScorecardReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketDepthResilienceScorecardReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = Decimal(len(rows))
    return tuple(
        ResearchMarketDepthResilienceScorecardReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_resilience_score(
    rows: tuple[ResearchMarketDepthResilienceScorecardRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.resilience_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _maximum_row_value(
    rows: tuple[ResearchMarketDepthResilienceScorecardRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _minimum_row_value(
    rows: tuple[ResearchMarketDepthResilienceScorecardRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _status_count(
    rows: tuple[ResearchMarketDepthResilienceScorecardRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchMarketDepthResilienceScorecardRow, ...],
    prefix: str,
) -> int:
    return sum(
        1
        for row in rows
        if f"{prefix}_watch" in row.reason_codes or f"{prefix}_block" in row.reason_codes
    )


def _validate_row_consistency(row: ResearchMarketDepthResilienceScorecardRow) -> None:
    if f"depth_resilience_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")
    depth_weight_sum = _quantize(
        row.near_depth_band_weight
        + row.mid_depth_band_weight
        + row.far_depth_band_weight,
    )
    if depth_weight_sum != ONE:
        raise ValueError("depth band weights must sum to 1")
    expected_depth_score = _quantize(
        row.near_band_depth_ratio * row.near_depth_band_weight
        + row.mid_band_depth_ratio * row.mid_depth_band_weight
        + row.far_band_depth_ratio * row.far_depth_band_weight,
    )
    if row.depth_band_score != expected_depth_score:
        raise ValueError("depth_band_score must match component depth bands")
    resilience_weight_sum = _quantize(
        row.depth_band_weight
        + row.spread_stability_weight
        + row.book_age_weight
        + row.imbalance_volatility_weight
        + row.fee_drag_weight
        + row.slippage_cushion_weight
        + row.settlement_friction_weight,
    )
    if resilience_weight_sum != ONE:
        raise ValueError("resilience weights must sum to 1")
    expected_resilience_score = _quantize(
        row.depth_band_score * row.depth_band_weight
        + row.spread_stability_score * row.spread_stability_weight
        + row.book_age_score * row.book_age_weight
        + row.imbalance_stability_score * row.imbalance_volatility_weight
        + row.fee_drag_score * row.fee_drag_weight
        + row.slippage_cushion_score * row.slippage_cushion_weight
        + row.settlement_friction_score * row.settlement_friction_weight,
    )
    if row.resilience_score != expected_resilience_score:
        raise ValueError("resilience_score must match component scores")


def _validate_report_consistency(report: ResearchMarketDepthResilienceScorecardReport) -> None:
    _normalize_rows(report.rows)
    for row in report.rows:
        _validate_public_row_state(row)
    _normalize_reason_code_counts(report.reason_code_counts)
    for reason_code_count in report.reason_code_counts:
        _validate_public_reason_code_count_state(reason_code_count)
    _normalize_reason_codes("reason_codes", report.reason_codes, allow_empty=False)
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.public_row_ref)):
        raise ValueError("rows must be sorted by public_row_ref")
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.depth_band_pressure_count != _decimal_count(
        _reason_count(report.rows, "depth_band"),
    ):
        raise ValueError("depth_band_pressure_count must match rows")
    if report.spread_instability_count != _decimal_count(
        _reason_count(report.rows, "spread_stability"),
    ):
        raise ValueError("spread_instability_count must match rows")
    if report.stale_book_count != _decimal_count(_reason_count(report.rows, "book_age")):
        raise ValueError("stale_book_count must match rows")
    if report.imbalance_volatility_count != _decimal_count(
        _reason_count(report.rows, "imbalance_volatility"),
    ):
        raise ValueError("imbalance_volatility_count must match rows")
    if report.fee_drag_count != _decimal_count(_reason_count(report.rows, "fee_drag")):
        raise ValueError("fee_drag_count must match rows")
    if report.slippage_cushion_count != _decimal_count(
        _reason_count(report.rows, "slippage_cushion"),
    ):
        raise ValueError("slippage_cushion_count must match rows")
    if report.settlement_friction_count != _decimal_count(
        _reason_count(report.rows, "settlement_friction"),
    ):
        raise ValueError("settlement_friction_count must match rows")
    if report.average_resilience_score != _average_resilience_score(report.rows):
        raise ValueError("average_resilience_score must match rows")
    if report.min_depth_band_score != _minimum_row_value(report.rows, "depth_band_score"):
        raise ValueError("min_depth_band_score must match rows")
    if report.min_spread_stability_ratio != _minimum_row_value(
        report.rows,
        "spread_stability_ratio",
    ):
        raise ValueError("min_spread_stability_ratio must match rows")
    if report.max_book_age_seconds != _maximum_row_value(report.rows, "book_age_seconds"):
        raise ValueError("max_book_age_seconds must match rows")
    if report.max_imbalance_volatility_ratio != _maximum_row_value(
        report.rows,
        "imbalance_volatility_ratio",
    ):
        raise ValueError("max_imbalance_volatility_ratio must match rows")
    if report.max_fee_drag_ratio != _maximum_row_value(report.rows, "fee_drag_ratio"):
        raise ValueError("max_fee_drag_ratio must match rows")
    if report.min_slippage_cushion_ratio != _minimum_row_value(
        report.rows,
        "slippage_cushion_ratio",
    ):
        raise ValueError("min_slippage_cushion_ratio must match rows")
    if report.max_settlement_friction_ratio != _maximum_row_value(
        report.rows,
        "settlement_friction_ratio",
    ):
        raise ValueError("max_settlement_friction_ratio must match rows")
    expected_reasons = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(expected_reasons):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchMarketDepthResilienceScorecardRow, ...],
) -> tuple[ResearchMarketDepthResilienceScorecardRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketDepthResilienceScorecardRow:
            raise ValueError("rows must contain ResearchMarketDepthResilienceScorecardRow")
        _require_hard_flags("row", row)
        if row.public_row_ref in seen:
            raise ValueError("public_row_ref values must be unique")
        seen.add(row.public_row_ref)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketDepthResilienceScorecardReasonCodeCount, ...],
) -> tuple[ResearchMarketDepthResilienceScorecardReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketDepthResilienceScorecardReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda item: item.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if _hard_flag_value(value, "paper_only") is not True:
        raise ValueError(f"{label} paper_only must be True")
    if _hard_flag_value(value, "report_only") is not True:
        raise ValueError(f"{label} report_only must be True")
    if _hard_flag_value(value, "readonly") is not True:
        raise ValueError(f"{label} readonly must be True")


def _hard_flag_value(value: object, name: str) -> object:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in MARKET_DEPTH_RESILIENCE_SCORECARD_STATUSES:
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
    sort_values: bool = False,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    checked = tuple(_require_reason_code(name, value) for value in values)
    if len(checked) != len(frozenset(checked)):
        raise ValueError(f"{name} must contain unique values")
    normalized = tuple(sorted(checked)) if sort_values else checked
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


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
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_public_report_state(
    report: ResearchMarketDepthResilienceScorecardReport,
) -> None:
    _require_exact_type(report, ResearchMarketDepthResilienceScorecardReport, "report")
    _as_utc("generated_at", report.generated_at)
    _require_public_label("config_version", report.config_version)
    if (
        report.config_version
        != DEFAULT_RESEARCH_MARKET_DEPTH_RESILIENCE_SCORECARD_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must match supported value")
    for field_name in REPORT_WHOLE_DECIMAL_FIELDS:
        _require_nonnegative_whole_decimal(field_name, getattr(report, field_name))
    _require_optional_ratio_decimal(
        "average_resilience_score",
        report.average_resilience_score,
    )
    _require_nonnegative_decimal("max_book_age_seconds", report.max_book_age_seconds)
    for field_name in REPORT_RATIO_DECIMAL_FIELDS:
        _require_ratio_decimal(field_name, getattr(report, field_name))
    _require_status("status", report.status)
    _normalize_rows(report.rows)
    _normalize_reason_code_counts(report.reason_code_counts)
    _normalize_reason_codes("reason_codes", report.reason_codes, allow_empty=False)
    _require_hard_flags("report", report)
    _validate_report_consistency(report)


def _validate_public_row_state(
    row: ResearchMarketDepthResilienceScorecardRow,
) -> None:
    _require_exact_type(row, ResearchMarketDepthResilienceScorecardRow, "row")
    _require_public_label("public_row_ref", row.public_row_ref)
    _as_utc("observed_at", row.observed_at)
    _require_nonnegative_decimal("book_age_seconds", row.book_age_seconds)
    for field_name in ROW_RATIO_DECIMAL_FIELDS:
        _require_ratio_decimal(field_name, getattr(row, field_name))
    _require_status("status", row.status)
    _normalize_reason_codes("reason_codes", row.reason_codes, allow_empty=False)
    _require_hard_flags("row", row)
    _validate_row_consistency(row)


def _validate_public_reason_code_count_state(
    reason_code_count: ResearchMarketDepthResilienceScorecardReasonCodeCount,
) -> None:
    _require_exact_type(
        reason_code_count,
        ResearchMarketDepthResilienceScorecardReasonCodeCount,
        "reason_code_count",
    )
    _require_reason_code("reason_code", reason_code_count.reason_code)
    _require_positive_whole_decimal("count", reason_code_count.count)
    _require_ratio_decimal("row_ratio", reason_code_count.row_ratio)
    _require_hard_flags("reason_code_count", reason_code_count)


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("payload value must use exact Decimal values")
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, datetime):
        raise ValueError("payload value must use exact datetime values")
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if type(value) is int or type(value) is float:
        raise ValueError("payload numeric values must be Decimal-derived")
    if value is not None and type(value) is not bool and type(value) is not str:
        raise ValueError("payload value must use canonical report payload schema")
    return value


def _derived_report_digest(report: ResearchMarketDepthResilienceScorecardReport) -> str:
    _validate_public_report_state(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload_schema(payload, allow_empty_digest=True)
    payload = dict(payload)
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload(payload)
    return sha256(_canonical_payload_bytes(payload)).hexdigest()


def _canonical_payload_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _validate_public_payload_schema(
    payload: dict[str, object],
    *,
    allow_empty_digest: bool,
) -> None:
    _require_payload_fields(
        "report",
        payload,
        REPORT_PAYLOAD_FIELDS,
        "canonical report payload schema",
    )
    _require_datetime_payload_string(
        "generated_at",
        payload["generated_at"],
        "canonical report payload schema",
    )
    _require_public_label("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_MARKET_DEPTH_RESILIENCE_SCORECARD_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must use canonical report payload schema")
    for field_name in REPORT_WHOLE_DECIMAL_FIELDS:
        _require_decimal_payload_string(
            field_name,
            payload[field_name],
            "canonical report payload schema",
            whole=True,
        )
    _require_optional_decimal_payload_string(
        "average_resilience_score",
        payload["average_resilience_score"],
        "canonical report payload schema",
        ratio=True,
    )
    _require_decimal_payload_string(
        "max_book_age_seconds",
        payload["max_book_age_seconds"],
        "canonical report payload schema",
    )
    for field_name in REPORT_RATIO_DECIMAL_FIELDS:
        _require_decimal_payload_string(
            field_name,
            payload[field_name],
            "canonical report payload schema",
            ratio=True,
        )
    _require_status_payload_string(
        "status",
        payload["status"],
        "canonical report payload schema",
    )
    _require_row_payloads(payload["rows"])
    _require_reason_code_count_payloads(payload["reason_code_counts"])
    _require_reason_code_payloads(
        "reason_codes",
        payload["reason_codes"],
        "canonical report payload schema",
        allow_empty=False,
    )
    digest = payload["derived_validation_digest"]
    if digest != "" or not allow_empty_digest:
        _require_hex_digest("derived_validation_digest", digest)
    _require_payload_flags(payload, "canonical report payload schema")


def _require_row_payloads(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must use canonical report payload schema")
    seen: set[str] = set()
    for row in value:
        if type(row) is not dict:
            raise ValueError("rows must use canonical row payload schema")
        _require_payload_fields(
            "row",
            row,
            ROW_PAYLOAD_FIELDS,
            "canonical row payload schema",
        )
        public_row_ref = _require_public_label("public_row_ref", row["public_row_ref"])
        if public_row_ref in seen:
            raise ValueError("public_row_ref must use canonical row payload schema")
        seen.add(public_row_ref)
        _require_datetime_payload_string(
            "observed_at",
            row["observed_at"],
            "canonical row payload schema",
        )
        for field_name in ROW_RATIO_DECIMAL_FIELDS:
            _require_decimal_payload_string(
                field_name,
                row[field_name],
                "canonical row payload schema",
                ratio=True,
            )
        _require_decimal_payload_string(
            "book_age_seconds",
            row["book_age_seconds"],
            "canonical row payload schema",
        )
        _require_status_payload_string(
            "status",
            row["status"],
            "canonical row payload schema",
        )
        _require_reason_code_payloads(
            "reason_codes",
            row["reason_codes"],
            "canonical row payload schema",
            allow_empty=False,
        )
        _require_payload_flags(row, "canonical row payload schema")


def _require_reason_code_count_payloads(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts must use canonical report payload schema")
    previous_reason_code = ""
    for item in value:
        if type(item) is not dict:
            raise ValueError(
                "reason_code_counts must use canonical reason code count payload schema",
            )
        _require_payload_fields(
            "reason_code_count",
            item,
            REASON_CODE_COUNT_PAYLOAD_FIELDS,
            "canonical reason code count payload schema",
        )
        reason_code = _require_reason_code("reason_code", item["reason_code"])
        if previous_reason_code and reason_code <= previous_reason_code:
            raise ValueError(
                "reason_code_counts must use canonical reason code count payload schema",
            )
        previous_reason_code = reason_code
        _require_decimal_payload_string(
            "count",
            item["count"],
            "canonical reason code count payload schema",
            whole=True,
        )
        _require_decimal_payload_string(
            "row_ratio",
            item["row_ratio"],
            "canonical reason code count payload schema",
            ratio=True,
        )
        _require_payload_flags(item, "canonical reason code count payload schema")


def _require_reason_code_payloads(
    name: str,
    value: object,
    schema_name: str,
    *,
    allow_empty: bool,
) -> None:
    if type(value) is not list:
        raise ValueError(f"{name} must use {schema_name}")
    if not allow_empty and not value:
        raise ValueError(f"{name} must use {schema_name}")
    seen: set[str] = set()
    for item in value:
        reason_code = _require_reason_code(name, item)
        if reason_code in seen:
            raise ValueError(f"{name} must use {schema_name}")
        seen.add(reason_code)


def _require_payload_fields(
    label: str,
    payload: dict[str, object],
    expected_fields: tuple[str, ...],
    schema_name: str,
) -> None:
    if type(payload) is not dict or tuple(payload) != expected_fields:
        raise ValueError(f"{label} must use {schema_name}")


def _require_datetime_payload_string(
    field_name: str,
    value: object,
    schema_name: str,
) -> None:
    if type(value) is not str or not value.endswith("+00:00"):
        raise ValueError(f"{field_name} must use {schema_name}")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must use {schema_name}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must use {schema_name}")
    if parsed.utcoffset().total_seconds() != 0:
        raise ValueError(f"{field_name} must use {schema_name}")


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    schema_name: str,
    *,
    whole: bool = False,
    ratio: bool = False,
) -> Decimal:
    if type(value) is not str or DECIMAL_PAYLOAD_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must use {schema_name}")
    decimal_value = Decimal(value)
    if whole and decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must use {schema_name}")
    if ratio and decimal_value > ONE:
        raise ValueError(f"{field_name} must use {schema_name}")
    return decimal_value


def _require_optional_decimal_payload_string(
    field_name: str,
    value: object,
    schema_name: str,
    *,
    ratio: bool = False,
) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal_payload_string(
        field_name,
        value,
        schema_name,
        ratio=ratio,
    )


def _require_status_payload_string(
    field_name: str,
    value: object,
    schema_name: str,
) -> None:
    if type(value) is not str or value not in MARKET_DEPTH_RESILIENCE_SCORECARD_STATUSES:
        raise ValueError(f"{field_name} must use {schema_name}")


def _require_payload_flags(payload: dict[str, object], schema_name: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must use {schema_name}")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str or _contains_unsafe_public_text(key):
                raise ValueError("public payload has unsafe key")
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str) and _contains_unsafe_public_text(value):
        raise ValueError("public payload has unsafe text")


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    compacted = re.sub(r"[^a-z0-9]", "", lowered)
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            return True
        compacted_fragment = re.sub(r"[^a-z0-9]", "", fragment)
        if compacted_fragment and compacted_fragment in compacted:
            return True
    return False
