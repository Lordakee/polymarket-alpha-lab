"""Pure depth stability report for manual research eligibility."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "ORDERBOOK_DEPTH_STABILITY_STATUSES",
    "DEFAULT_RESEARCH_MARKET_ORDERBOOK_DEPTH_STABILITY_REPORT_CONFIG_VERSION",
    "ResearchMarketOrderbookDepthStabilityConfig",
    "ResearchMarketOrderbookDepthStabilityInput",
    "ResearchMarketOrderbookDepthStabilityReasonCodeCount",
    "ResearchMarketOrderbookDepthStabilityReport",
    "ResearchMarketOrderbookDepthStabilityRow",
    "build_research_market_orderbook_depth_stability_report",
    "research_market_orderbook_depth_stability_report_digest",
    "research_market_orderbook_depth_stability_report_payload",
)


DEFAULT_RESEARCH_MARKET_ORDERBOOK_DEPTH_STABILITY_REPORT_CONFIG_VERSION = (
    "research-depth-stability-report-v0"
)
ORDERBOOK_DEPTH_STABILITY_STATUSES = ("pass", "watch", "block")
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
    _join_parts("exec", "ution"),
    _join_parts("place", "ment"),
    "://",
)
COMPONENT_REASON_PRIORITY = (
    "depth_coverage_block",
    "spread_stability_block",
    "imbalance_volatility_block",
    "liquidity_age_block",
    "shock_sensitivity_block",
    "depth_coverage_watch",
    "spread_stability_watch",
    "imbalance_volatility_watch",
    "liquidity_age_watch",
    "shock_sensitivity_watch",
)


@dataclass(frozen=True)
class ResearchMarketOrderbookDepthStabilityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_ORDERBOOK_DEPTH_STABILITY_REPORT_CONFIG_VERSION
    )
    minimum_pass_depth_coverage_ratio: Decimal = Decimal("0.800000")
    minimum_watch_depth_coverage_ratio: Decimal = Decimal("0.500000")
    maximum_pass_spread_instability_ratio: Decimal = Decimal("0.100000")
    maximum_watch_spread_instability_ratio: Decimal = Decimal("0.300000")
    maximum_pass_imbalance_volatility_ratio: Decimal = Decimal("0.100000")
    maximum_watch_imbalance_volatility_ratio: Decimal = Decimal("0.250000")
    maximum_pass_liquidity_age_seconds: Decimal = Decimal("120.000000")
    maximum_watch_liquidity_age_seconds: Decimal = Decimal("600.000000")
    maximum_pass_shock_depth_loss_ratio: Decimal = Decimal("0.100000")
    maximum_watch_shock_depth_loss_ratio: Decimal = Decimal("0.300000")
    depth_coverage_weight: Decimal = Decimal("0.300000")
    spread_stability_weight: Decimal = Decimal("0.200000")
    imbalance_volatility_weight: Decimal = Decimal("0.200000")
    liquidity_age_weight: Decimal = Decimal("0.150000")
    shock_sensitivity_weight: Decimal = Decimal("0.150000")
    pass_stability_score: Decimal = Decimal("0.750000")
    watch_stability_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketOrderbookDepthStabilityConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_ORDERBOOK_DEPTH_STABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "minimum_pass_depth_coverage_ratio",
            "minimum_watch_depth_coverage_ratio",
            "maximum_pass_spread_instability_ratio",
            "maximum_watch_spread_instability_ratio",
            "maximum_pass_imbalance_volatility_ratio",
            "maximum_watch_imbalance_volatility_ratio",
            "maximum_pass_shock_depth_loss_ratio",
            "maximum_watch_shock_depth_loss_ratio",
            "depth_coverage_weight",
            "spread_stability_weight",
            "imbalance_volatility_weight",
            "liquidity_age_weight",
            "shock_sensitivity_weight",
            "pass_stability_score",
            "watch_stability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_pass_liquidity_age_seconds",
            "maximum_watch_liquidity_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_pass_depth_coverage_ratio < self.minimum_watch_depth_coverage_ratio:
            raise ValueError("minimum_pass_depth_coverage_ratio must be at least watch")
        if (
            self.maximum_pass_spread_instability_ratio
            > self.maximum_watch_spread_instability_ratio
        ):
            raise ValueError("maximum_pass_spread_instability_ratio must not exceed watch")
        if (
            self.maximum_pass_imbalance_volatility_ratio
            > self.maximum_watch_imbalance_volatility_ratio
        ):
            raise ValueError(
                "maximum_pass_imbalance_volatility_ratio must not exceed watch",
            )
        if self.maximum_pass_liquidity_age_seconds > self.maximum_watch_liquidity_age_seconds:
            raise ValueError("maximum_pass_liquidity_age_seconds must not exceed watch")
        if self.maximum_pass_shock_depth_loss_ratio > self.maximum_watch_shock_depth_loss_ratio:
            raise ValueError("maximum_pass_shock_depth_loss_ratio must not exceed watch")
        if self.pass_stability_score < self.watch_stability_score:
            raise ValueError("pass_stability_score must be at least watch")
        weight_sum = _quantize(
            self.depth_coverage_weight
            + self.spread_stability_weight
            + self.imbalance_volatility_weight
            + self.liquidity_age_weight
            + self.shock_sensitivity_weight,
        )
        if weight_sum != ONE:
            raise ValueError("stability weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketOrderbookDepthStabilityInput:
    bucket_label: str
    sampled_at: datetime
    depth_coverage_ratio: Decimal
    spread_instability_ratio: Decimal
    imbalance_volatility_ratio: Decimal
    liquidity_age_seconds: Decimal
    shock_depth_loss_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketOrderbookDepthStabilityInput, "input")
        _require_public_label("bucket_label", self.bucket_label)
        object.__setattr__(self, "sampled_at", _as_utc("sampled_at", self.sampled_at))
        for field_name in (
            "depth_coverage_ratio",
            "spread_instability_ratio",
            "imbalance_volatility_ratio",
            "shock_depth_loss_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_age_seconds",
            _require_nonnegative_decimal(
                "liquidity_age_seconds",
                self.liquidity_age_seconds,
            ),
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
class ResearchMarketOrderbookDepthStabilityRow:
    public_row_ref: str
    sampled_at: datetime
    depth_coverage_ratio: Decimal
    depth_coverage_score: Decimal
    spread_instability_ratio: Decimal
    spread_stability_score: Decimal
    imbalance_volatility_ratio: Decimal
    imbalance_volatility_score: Decimal
    liquidity_age_seconds: Decimal
    liquidity_age_score: Decimal
    shock_depth_loss_ratio: Decimal
    shock_sensitivity_score: Decimal
    depth_coverage_weight: Decimal
    spread_stability_weight: Decimal
    imbalance_volatility_weight: Decimal
    liquidity_age_weight: Decimal
    shock_sensitivity_weight: Decimal
    stability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketOrderbookDepthStabilityRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "sampled_at", _as_utc("sampled_at", self.sampled_at))
        for field_name in (
            "depth_coverage_ratio",
            "depth_coverage_score",
            "spread_instability_ratio",
            "spread_stability_score",
            "imbalance_volatility_ratio",
            "imbalance_volatility_score",
            "liquidity_age_score",
            "shock_depth_loss_ratio",
            "shock_sensitivity_score",
            "depth_coverage_weight",
            "spread_stability_weight",
            "imbalance_volatility_weight",
            "liquidity_age_weight",
            "shock_sensitivity_weight",
            "stability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_age_seconds",
            _require_nonnegative_decimal(
                "liquidity_age_seconds",
                self.liquidity_age_seconds,
            ),
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
class ResearchMarketOrderbookDepthStabilityReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketOrderbookDepthStabilityReasonCodeCount,
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
class ResearchMarketOrderbookDepthStabilityReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    weak_depth_coverage_count: Decimal
    unstable_spread_count: Decimal
    high_imbalance_volatility_count: Decimal
    aged_liquidity_count: Decimal
    shock_sensitive_count: Decimal
    average_stability_score: Decimal | None
    min_depth_coverage_ratio: Decimal
    max_spread_instability_ratio: Decimal
    max_imbalance_volatility_ratio: Decimal
    max_liquidity_age_seconds: Decimal
    max_shock_depth_loss_ratio: Decimal
    status: str
    rows: tuple[ResearchMarketOrderbookDepthStabilityRow, ...]
    reason_code_counts: tuple[ResearchMarketOrderbookDepthStabilityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketOrderbookDepthStabilityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "weak_depth_coverage_count",
            "unstable_spread_count",
            "high_imbalance_volatility_count",
            "aged_liquidity_count",
            "shock_sensitive_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_stability_score",
            _require_optional_ratio_decimal(
                "average_stability_score",
                self.average_stability_score,
            ),
        )
        for field_name in (
            "min_depth_coverage_ratio",
            "max_spread_instability_ratio",
            "max_imbalance_volatility_ratio",
            "max_shock_depth_loss_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_liquidity_age_seconds",
            _require_nonnegative_decimal(
                "max_liquidity_age_seconds",
                self.max_liquidity_age_seconds,
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
        _validate_report_consistency(self)
        expected_digest = _derived_report_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_orderbook_depth_stability_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketOrderbookDepthStabilityConfig,
    generated_at: datetime,
) -> ResearchMarketOrderbookDepthStabilityReport:
    if type(config) is not ResearchMarketOrderbookDepthStabilityConfig:
        raise ValueError("config must be a ResearchMarketOrderbookDepthStabilityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    for item in input_items:
        if item.sampled_at > generated_at_utc:
            raise ValueError("sampled_at must not be after generated_at")
    sorted_items = tuple(sorted(input_items, key=lambda item: item.bucket_label))
    rows = tuple(
        _row_from_input(
            item,
            public_row_ref=f"depth_stability_group_{index:03d}",
            config=config,
        )
        for index, item in enumerate(sorted_items, start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketOrderbookDepthStabilityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        weak_depth_coverage_count=_decimal_count(_reason_count(rows, "depth_coverage")),
        unstable_spread_count=_decimal_count(_reason_count(rows, "spread_stability")),
        high_imbalance_volatility_count=_decimal_count(
            _reason_count(rows, "imbalance_volatility"),
        ),
        aged_liquidity_count=_decimal_count(_reason_count(rows, "liquidity_age")),
        shock_sensitive_count=_decimal_count(_reason_count(rows, "shock_sensitivity")),
        average_stability_score=_average_stability_score(rows),
        min_depth_coverage_ratio=_minimum_row_value(rows, "depth_coverage_ratio"),
        max_spread_instability_ratio=_maximum_row_value(
            rows,
            "spread_instability_ratio",
        ),
        max_imbalance_volatility_ratio=_maximum_row_value(
            rows,
            "imbalance_volatility_ratio",
        ),
        max_liquidity_age_seconds=_maximum_row_value(rows, "liquidity_age_seconds"),
        max_shock_depth_loss_ratio=_maximum_row_value(rows, "shock_depth_loss_ratio"),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_orderbook_depth_stability_report_payload(
    report: ResearchMarketOrderbookDepthStabilityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketOrderbookDepthStabilityReport:
        raise ValueError("report must be a ResearchMarketOrderbookDepthStabilityReport")
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


def research_market_orderbook_depth_stability_report_digest(
    report: ResearchMarketOrderbookDepthStabilityReport,
) -> str:
    if type(report) is not ResearchMarketOrderbookDepthStabilityReport:
        raise ValueError("report must be a ResearchMarketOrderbookDepthStabilityReport")
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
    item: ResearchMarketOrderbookDepthStabilityInput,
    *,
    public_row_ref: str,
    config: ResearchMarketOrderbookDepthStabilityConfig,
) -> ResearchMarketOrderbookDepthStabilityRow:
    depth_coverage_score = _coverage_score(
        item.depth_coverage_ratio,
        config.minimum_pass_depth_coverage_ratio,
    )
    spread_stability_score = _inverse_score(
        item.spread_instability_ratio,
        config.maximum_watch_spread_instability_ratio,
    )
    imbalance_volatility_score = _inverse_score(
        item.imbalance_volatility_ratio,
        config.maximum_watch_imbalance_volatility_ratio,
    )
    liquidity_age_score = _inverse_score(
        item.liquidity_age_seconds,
        config.maximum_watch_liquidity_age_seconds,
    )
    shock_sensitivity_score = _inverse_score(
        item.shock_depth_loss_ratio,
        config.maximum_watch_shock_depth_loss_ratio,
    )
    stability_score = _stability_score(
        depth_coverage_score=depth_coverage_score,
        spread_stability_score=spread_stability_score,
        imbalance_volatility_score=imbalance_volatility_score,
        liquidity_age_score=liquidity_age_score,
        shock_sensitivity_score=shock_sensitivity_score,
        config=config,
    )
    status = _row_status(
        item,
        stability_score=stability_score,
        config=config,
    )
    return ResearchMarketOrderbookDepthStabilityRow(
        public_row_ref=public_row_ref,
        sampled_at=item.sampled_at,
        depth_coverage_ratio=item.depth_coverage_ratio,
        depth_coverage_score=depth_coverage_score,
        spread_instability_ratio=item.spread_instability_ratio,
        spread_stability_score=spread_stability_score,
        imbalance_volatility_ratio=item.imbalance_volatility_ratio,
        imbalance_volatility_score=imbalance_volatility_score,
        liquidity_age_seconds=item.liquidity_age_seconds,
        liquidity_age_score=liquidity_age_score,
        shock_depth_loss_ratio=item.shock_depth_loss_ratio,
        shock_sensitivity_score=shock_sensitivity_score,
        depth_coverage_weight=config.depth_coverage_weight,
        spread_stability_weight=config.spread_stability_weight,
        imbalance_volatility_weight=config.imbalance_volatility_weight,
        liquidity_age_weight=config.liquidity_age_weight,
        shock_sensitivity_weight=config.shock_sensitivity_weight,
        stability_score=stability_score,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _coverage_score(value: Decimal, pass_threshold: Decimal) -> Decimal:
    if pass_threshold <= ZERO:
        raise ValueError("pass threshold must be positive")
    with localcontext() as context:
        context.prec = 28
        score = value / pass_threshold
    if score > ONE:
        return ONE
    return _quantize(score)


def _inverse_score(value: Decimal, zero_at: Decimal) -> Decimal:
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


def _stability_score(
    *,
    depth_coverage_score: Decimal,
    spread_stability_score: Decimal,
    imbalance_volatility_score: Decimal,
    liquidity_age_score: Decimal,
    shock_sensitivity_score: Decimal,
    config: ResearchMarketOrderbookDepthStabilityConfig,
) -> Decimal:
    return _quantize(
        depth_coverage_score * config.depth_coverage_weight
        + spread_stability_score * config.spread_stability_weight
        + imbalance_volatility_score * config.imbalance_volatility_weight
        + liquidity_age_score * config.liquidity_age_weight
        + shock_sensitivity_score * config.shock_sensitivity_weight,
    )


def _row_status(
    item: ResearchMarketOrderbookDepthStabilityInput,
    *,
    stability_score: Decimal,
    config: ResearchMarketOrderbookDepthStabilityConfig,
) -> str:
    if (
        item.depth_coverage_ratio < config.minimum_watch_depth_coverage_ratio
        or item.spread_instability_ratio > config.maximum_watch_spread_instability_ratio
        or item.imbalance_volatility_ratio
        > config.maximum_watch_imbalance_volatility_ratio
        or item.liquidity_age_seconds > config.maximum_watch_liquidity_age_seconds
        or item.shock_depth_loss_ratio > config.maximum_watch_shock_depth_loss_ratio
        or stability_score < config.watch_stability_score
    ):
        return "block"
    if (
        item.depth_coverage_ratio < config.minimum_pass_depth_coverage_ratio
        or item.spread_instability_ratio > config.maximum_pass_spread_instability_ratio
        or item.imbalance_volatility_ratio > config.maximum_pass_imbalance_volatility_ratio
        or item.liquidity_age_seconds > config.maximum_pass_liquidity_age_seconds
        or item.shock_depth_loss_ratio > config.maximum_pass_shock_depth_loss_ratio
        or stability_score < config.pass_stability_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchMarketOrderbookDepthStabilityInput,
    *,
    status: str,
    config: ResearchMarketOrderbookDepthStabilityConfig,
) -> tuple[str, ...]:
    codes = {
        f"depth_stability_{status}",
        _low_value_component_reason(
            prefix="depth_coverage",
            value=item.depth_coverage_ratio,
            pass_threshold=config.minimum_pass_depth_coverage_ratio,
            block_threshold=config.minimum_watch_depth_coverage_ratio,
        ),
        _high_value_component_reason(
            prefix="spread_stability",
            value=item.spread_instability_ratio,
            pass_threshold=config.maximum_pass_spread_instability_ratio,
            block_threshold=config.maximum_watch_spread_instability_ratio,
        ),
        _high_value_component_reason(
            prefix="imbalance_volatility",
            value=item.imbalance_volatility_ratio,
            pass_threshold=config.maximum_pass_imbalance_volatility_ratio,
            block_threshold=config.maximum_watch_imbalance_volatility_ratio,
        ),
        _high_value_component_reason(
            prefix="liquidity_age",
            value=item.liquidity_age_seconds,
            pass_threshold=config.maximum_pass_liquidity_age_seconds,
            block_threshold=config.maximum_watch_liquidity_age_seconds,
        ),
        _high_value_component_reason(
            prefix="shock_sensitivity",
            value=item.shock_depth_loss_ratio,
            pass_threshold=config.maximum_pass_shock_depth_loss_ratio,
            block_threshold=config.maximum_watch_shock_depth_loss_ratio,
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
) -> tuple[ResearchMarketOrderbookDepthStabilityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for value in values:
        if type(value) is not ResearchMarketOrderbookDepthStabilityInput:
            raise ValueError(
                "inputs must contain ResearchMarketOrderbookDepthStabilityInput values",
            )
        _require_hard_flags("input", value)
        if value.bucket_label in seen:
            raise ValueError("bucket_label values must be unique")
        seen.add(value.bucket_label)
    return values


def _summary_reason_codes(
    rows: tuple[ResearchMarketOrderbookDepthStabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_depth_stability_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("depth_stability_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("depth_stability_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("depth_stability_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in COMPONENT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_depth_stability_inputs",):
        return "block"
    if "depth_stability_block" in reason_codes:
        return "block"
    if "depth_stability_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketOrderbookDepthStabilityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketOrderbookDepthStabilityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketOrderbookDepthStabilityReasonCodeCount(
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
        ResearchMarketOrderbookDepthStabilityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_stability_score(
    rows: tuple[ResearchMarketOrderbookDepthStabilityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.stability_score for row in rows), ZERO) / Decimal(len(rows)))


def _maximum_row_value(
    rows: tuple[ResearchMarketOrderbookDepthStabilityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _minimum_row_value(
    rows: tuple[ResearchMarketOrderbookDepthStabilityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _status_count(
    rows: tuple[ResearchMarketOrderbookDepthStabilityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchMarketOrderbookDepthStabilityRow, ...],
    prefix: str,
) -> int:
    return sum(
        1
        for row in rows
        if f"{prefix}_watch" in row.reason_codes or f"{prefix}_block" in row.reason_codes
    )


def _validate_row_consistency(row: ResearchMarketOrderbookDepthStabilityRow) -> None:
    if f"depth_stability_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")
    weight_sum = _quantize(
        row.depth_coverage_weight
        + row.spread_stability_weight
        + row.imbalance_volatility_weight
        + row.liquidity_age_weight
        + row.shock_sensitivity_weight,
    )
    if weight_sum != ONE:
        raise ValueError("stability weights must sum to 1")
    expected_score = _quantize(
        row.depth_coverage_score * row.depth_coverage_weight
        + row.spread_stability_score * row.spread_stability_weight
        + row.imbalance_volatility_score * row.imbalance_volatility_weight
        + row.liquidity_age_score * row.liquidity_age_weight
        + row.shock_sensitivity_score * row.shock_sensitivity_weight,
    )
    if row.stability_score != expected_score:
        raise ValueError("stability_score must match component scores")


def _validate_report_consistency(
    report: ResearchMarketOrderbookDepthStabilityReport,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.public_row_ref)):
        raise ValueError("rows must be sorted by public_row_ref")
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.weak_depth_coverage_count != _decimal_count(
        _reason_count(report.rows, "depth_coverage"),
    ):
        raise ValueError("weak_depth_coverage_count must match rows")
    if report.unstable_spread_count != _decimal_count(
        _reason_count(report.rows, "spread_stability"),
    ):
        raise ValueError("unstable_spread_count must match rows")
    if report.high_imbalance_volatility_count != _decimal_count(
        _reason_count(report.rows, "imbalance_volatility"),
    ):
        raise ValueError("high_imbalance_volatility_count must match rows")
    if report.aged_liquidity_count != _decimal_count(
        _reason_count(report.rows, "liquidity_age"),
    ):
        raise ValueError("aged_liquidity_count must match rows")
    if report.shock_sensitive_count != _decimal_count(
        _reason_count(report.rows, "shock_sensitivity"),
    ):
        raise ValueError("shock_sensitive_count must match rows")
    if report.average_stability_score != _average_stability_score(report.rows):
        raise ValueError("average_stability_score must match rows")
    if report.min_depth_coverage_ratio != _minimum_row_value(
        report.rows,
        "depth_coverage_ratio",
    ):
        raise ValueError("min_depth_coverage_ratio must match rows")
    if report.max_spread_instability_ratio != _maximum_row_value(
        report.rows,
        "spread_instability_ratio",
    ):
        raise ValueError("max_spread_instability_ratio must match rows")
    if report.max_imbalance_volatility_ratio != _maximum_row_value(
        report.rows,
        "imbalance_volatility_ratio",
    ):
        raise ValueError("max_imbalance_volatility_ratio must match rows")
    if report.max_liquidity_age_seconds != _maximum_row_value(
        report.rows,
        "liquidity_age_seconds",
    ):
        raise ValueError("max_liquidity_age_seconds must match rows")
    if report.max_shock_depth_loss_ratio != _maximum_row_value(
        report.rows,
        "shock_depth_loss_ratio",
    ):
        raise ValueError("max_shock_depth_loss_ratio must match rows")
    expected_reasons = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(expected_reasons):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchMarketOrderbookDepthStabilityRow, ...],
) -> tuple[ResearchMarketOrderbookDepthStabilityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketOrderbookDepthStabilityRow:
            raise ValueError("rows must contain ResearchMarketOrderbookDepthStabilityRow")
        _require_hard_flags("row", row)
        if row.public_row_ref in seen:
            raise ValueError("public_row_ref values must be unique")
        seen.add(row.public_row_ref)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketOrderbookDepthStabilityReasonCodeCount, ...],
) -> tuple[ResearchMarketOrderbookDepthStabilityReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketOrderbookDepthStabilityReasonCodeCount:
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
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in ORDERBOOK_DEPTH_STABILITY_STATUSES:
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
    return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


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


def _derived_report_digest(report: ResearchMarketOrderbookDepthStabilityReport) -> str:
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
                raise ValueError("public payload has unsafe key")
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str) and _contains_unsafe_public_text(value):
        raise ValueError("public payload has unsafe text")


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
