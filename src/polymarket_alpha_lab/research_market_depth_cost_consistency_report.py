"""Pure depth/cost consistency report for manual research."""

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
    "MARKET_DEPTH_COST_CONSISTENCY_STATUSES",
    "DEFAULT_RESEARCH_MARKET_DEPTH_COST_CONSISTENCY_REPORT_CONFIG_VERSION",
    "ResearchMarketDepthCostConsistencyConfig",
    "ResearchMarketDepthCostConsistencyInput",
    "ResearchMarketDepthCostConsistencyReasonCodeCount",
    "ResearchMarketDepthCostConsistencyReport",
    "ResearchMarketDepthCostConsistencyRow",
    "build_research_market_depth_cost_consistency_report",
    "research_market_depth_cost_consistency_report_digest",
    "research_market_depth_cost_consistency_report_payload",
)


DEFAULT_RESEARCH_MARKET_DEPTH_COST_CONSISTENCY_REPORT_CONFIG_VERSION = (
    "research-market-depth-cost-consistency-report-v0"
)
MARKET_DEPTH_COST_CONSISTENCY_STATUSES = ("pass", "watch", "block")
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
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
    "://",
)
COMPONENT_REASON_PRIORITY = (
    "available_depth_block",
    "spread_cost_block",
    "slippage_cost_block",
    "fee_drag_block",
    "quote_freshness_block",
    "available_depth_watch",
    "spread_cost_watch",
    "slippage_cost_watch",
    "fee_drag_watch",
    "quote_freshness_watch",
)


@dataclass(frozen=True)
class ResearchMarketDepthCostConsistencyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_DEPTH_COST_CONSISTENCY_REPORT_CONFIG_VERSION
    )
    minimum_pass_available_depth: Decimal = Decimal("1000.000000")
    minimum_watch_available_depth: Decimal = Decimal("250.000000")
    maximum_pass_spread_ratio: Decimal = Decimal("0.030000")
    maximum_watch_spread_ratio: Decimal = Decimal("0.080000")
    maximum_pass_slippage_ratio: Decimal = Decimal("0.020000")
    maximum_watch_slippage_ratio: Decimal = Decimal("0.060000")
    maximum_pass_fee_drag_ratio: Decimal = Decimal("0.010000")
    maximum_watch_fee_drag_ratio: Decimal = Decimal("0.030000")
    maximum_pass_quote_age_seconds: Decimal = Decimal("120.000000")
    maximum_watch_quote_age_seconds: Decimal = Decimal("600.000000")
    depth_weight: Decimal = Decimal("0.250000")
    spread_weight: Decimal = Decimal("0.200000")
    slippage_weight: Decimal = Decimal("0.200000")
    fee_drag_weight: Decimal = Decimal("0.150000")
    quote_freshness_weight: Decimal = Decimal("0.200000")
    pass_consistency_score: Decimal = Decimal("0.750000")
    watch_consistency_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthCostConsistencyConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_COST_CONSISTENCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "minimum_pass_available_depth",
            "minimum_watch_available_depth",
            "maximum_pass_quote_age_seconds",
            "maximum_watch_quote_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_pass_spread_ratio",
            "maximum_watch_spread_ratio",
            "maximum_pass_slippage_ratio",
            "maximum_watch_slippage_ratio",
            "maximum_pass_fee_drag_ratio",
            "maximum_watch_fee_drag_ratio",
            "depth_weight",
            "spread_weight",
            "slippage_weight",
            "fee_drag_weight",
            "quote_freshness_weight",
            "pass_consistency_score",
            "watch_consistency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_pass_available_depth < self.minimum_watch_available_depth:
            raise ValueError("minimum_pass_available_depth must be at least watch")
        if self.maximum_pass_spread_ratio > self.maximum_watch_spread_ratio:
            raise ValueError("maximum_pass_spread_ratio must not exceed watch")
        if self.maximum_pass_slippage_ratio > self.maximum_watch_slippage_ratio:
            raise ValueError("maximum_pass_slippage_ratio must not exceed watch")
        if self.maximum_pass_fee_drag_ratio > self.maximum_watch_fee_drag_ratio:
            raise ValueError("maximum_pass_fee_drag_ratio must not exceed watch")
        if self.maximum_pass_quote_age_seconds > self.maximum_watch_quote_age_seconds:
            raise ValueError("maximum_pass_quote_age_seconds must not exceed watch")
        if self.pass_consistency_score < self.watch_consistency_score:
            raise ValueError("pass_consistency_score must be at least watch")
        weight_sum = _quantize(
            self.depth_weight
            + self.spread_weight
            + self.slippage_weight
            + self.fee_drag_weight
            + self.quote_freshness_weight,
        )
        if weight_sum != ONE:
            raise ValueError("consistency weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthCostConsistencyInput:
    bucket_label: str
    quote_observed_at: datetime
    available_depth: Decimal
    spread_ratio: Decimal
    slippage_ratio: Decimal
    fee_drag_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthCostConsistencyInput, "input")
        _require_public_label("bucket_label", self.bucket_label)
        object.__setattr__(
            self,
            "quote_observed_at",
            _as_utc("quote_observed_at", self.quote_observed_at),
        )
        object.__setattr__(
            self,
            "available_depth",
            _require_nonnegative_decimal("available_depth", self.available_depth),
        )
        for field_name in ("spread_ratio", "slippage_ratio", "fee_drag_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
class ResearchMarketDepthCostConsistencyRow:
    public_row_ref: str
    quote_observed_at: datetime
    quote_age_seconds: Decimal
    available_depth: Decimal
    depth_score: Decimal
    spread_ratio: Decimal
    spread_score: Decimal
    slippage_ratio: Decimal
    slippage_score: Decimal
    fee_drag_ratio: Decimal
    fee_drag_score: Decimal
    quote_freshness_score: Decimal
    depth_weight: Decimal
    spread_weight: Decimal
    slippage_weight: Decimal
    fee_drag_weight: Decimal
    quote_freshness_weight: Decimal
    consistency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthCostConsistencyRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(
            self,
            "quote_observed_at",
            _as_utc("quote_observed_at", self.quote_observed_at),
        )
        for field_name in ("quote_age_seconds", "available_depth"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_score",
            "spread_ratio",
            "spread_score",
            "slippage_ratio",
            "slippage_score",
            "fee_drag_ratio",
            "fee_drag_score",
            "quote_freshness_score",
            "depth_weight",
            "spread_weight",
            "slippage_weight",
            "fee_drag_weight",
            "quote_freshness_weight",
            "consistency_score",
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
class ResearchMarketDepthCostConsistencyReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthCostConsistencyReasonCodeCount,
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
class ResearchMarketDepthCostConsistencyReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    low_depth_count: Decimal
    wide_spread_count: Decimal
    high_slippage_count: Decimal
    high_fee_drag_count: Decimal
    stale_quote_count: Decimal
    average_consistency_score: Decimal | None
    min_available_depth: Decimal
    max_spread_ratio: Decimal
    max_slippage_ratio: Decimal
    max_fee_drag_ratio: Decimal
    max_quote_age_seconds: Decimal
    status: str
    rows: tuple[ResearchMarketDepthCostConsistencyRow, ...]
    reason_code_counts: tuple[ResearchMarketDepthCostConsistencyReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthCostConsistencyReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "low_depth_count",
            "wide_spread_count",
            "high_slippage_count",
            "high_fee_drag_count",
            "stale_quote_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_consistency_score",
            _require_optional_ratio_decimal(
                "average_consistency_score",
                self.average_consistency_score,
            ),
        )
        for field_name in ("min_available_depth", "max_quote_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_spread_ratio",
            "max_slippage_ratio",
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


def build_research_market_depth_cost_consistency_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketDepthCostConsistencyConfig,
    generated_at: datetime,
) -> ResearchMarketDepthCostConsistencyReport:
    if type(config) is not ResearchMarketDepthCostConsistencyConfig:
        raise ValueError("config must be a ResearchMarketDepthCostConsistencyConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    for item in input_items:
        if item.quote_observed_at > generated_at_utc:
            raise ValueError("quote_observed_at must not be after generated_at")
    sorted_items = tuple(sorted(input_items, key=lambda item: item.bucket_label))
    rows = tuple(
        _row_from_input(
            item,
            public_row_ref=f"depth_cost_group_{index:03d}",
            config=config,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(sorted_items, start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketDepthCostConsistencyReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        low_depth_count=_decimal_count(_reason_count(rows, "available_depth")),
        wide_spread_count=_decimal_count(_reason_count(rows, "spread_cost")),
        high_slippage_count=_decimal_count(_reason_count(rows, "slippage_cost")),
        high_fee_drag_count=_decimal_count(_reason_count(rows, "fee_drag")),
        stale_quote_count=_decimal_count(_reason_count(rows, "quote_freshness")),
        average_consistency_score=_average_consistency_score(rows),
        min_available_depth=_minimum_row_value(rows, "available_depth"),
        max_spread_ratio=_maximum_row_value(rows, "spread_ratio"),
        max_slippage_ratio=_maximum_row_value(rows, "slippage_ratio"),
        max_fee_drag_ratio=_maximum_row_value(rows, "fee_drag_ratio"),
        max_quote_age_seconds=_maximum_row_value(rows, "quote_age_seconds"),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_depth_cost_consistency_report_payload(
    report: ResearchMarketDepthCostConsistencyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketDepthCostConsistencyReport:
        raise ValueError("report must be a ResearchMarketDepthCostConsistencyReport")
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


def research_market_depth_cost_consistency_report_digest(
    report: ResearchMarketDepthCostConsistencyReport,
) -> str:
    if type(report) is not ResearchMarketDepthCostConsistencyReport:
        raise ValueError("report must be a ResearchMarketDepthCostConsistencyReport")
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
    item: ResearchMarketDepthCostConsistencyInput,
    *,
    public_row_ref: str,
    config: ResearchMarketDepthCostConsistencyConfig,
    generated_at: datetime,
) -> ResearchMarketDepthCostConsistencyRow:
    quote_age_seconds = _age_seconds(generated_at, item.quote_observed_at)
    depth_score = _depth_score(item.available_depth, config.minimum_pass_available_depth)
    spread_score = _inverse_ratio_score(
        item.spread_ratio,
        config.maximum_watch_spread_ratio,
    )
    slippage_score = _inverse_ratio_score(
        item.slippage_ratio,
        config.maximum_watch_slippage_ratio,
    )
    fee_drag_score = _inverse_ratio_score(
        item.fee_drag_ratio,
        config.maximum_watch_fee_drag_ratio,
    )
    quote_freshness_score = _inverse_ratio_score(
        quote_age_seconds,
        config.maximum_watch_quote_age_seconds,
    )
    consistency_score = _consistency_score(
        depth_score=depth_score,
        spread_score=spread_score,
        slippage_score=slippage_score,
        fee_drag_score=fee_drag_score,
        quote_freshness_score=quote_freshness_score,
        config=config,
    )
    status = _row_status(
        available_depth=item.available_depth,
        spread_ratio=item.spread_ratio,
        slippage_ratio=item.slippage_ratio,
        fee_drag_ratio=item.fee_drag_ratio,
        quote_age_seconds=quote_age_seconds,
        consistency_score=consistency_score,
        config=config,
    )
    return ResearchMarketDepthCostConsistencyRow(
        public_row_ref=public_row_ref,
        quote_observed_at=item.quote_observed_at,
        quote_age_seconds=quote_age_seconds,
        available_depth=item.available_depth,
        depth_score=depth_score,
        spread_ratio=item.spread_ratio,
        spread_score=spread_score,
        slippage_ratio=item.slippage_ratio,
        slippage_score=slippage_score,
        fee_drag_ratio=item.fee_drag_ratio,
        fee_drag_score=fee_drag_score,
        quote_freshness_score=quote_freshness_score,
        depth_weight=config.depth_weight,
        spread_weight=config.spread_weight,
        slippage_weight=config.slippage_weight,
        fee_drag_weight=config.fee_drag_weight,
        quote_freshness_weight=config.quote_freshness_weight,
        consistency_score=consistency_score,
        status=status,
        reason_codes=_row_reason_codes(
            item,
            quote_age_seconds=quote_age_seconds,
            status=status,
            config=config,
        ),
    )


def _depth_score(available_depth: Decimal, minimum_pass_available_depth: Decimal) -> Decimal:
    if minimum_pass_available_depth <= ZERO:
        raise ValueError("minimum_pass_available_depth must be positive")
    return _quantize(min(ONE, available_depth / minimum_pass_available_depth))


def _inverse_ratio_score(value: Decimal, zero_at: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = ONE - (value / zero_at)
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return _quantize(score)


def _consistency_score(
    *,
    depth_score: Decimal,
    spread_score: Decimal,
    slippage_score: Decimal,
    fee_drag_score: Decimal,
    quote_freshness_score: Decimal,
    config: ResearchMarketDepthCostConsistencyConfig,
) -> Decimal:
    return _quantize(
        depth_score * config.depth_weight
        + spread_score * config.spread_weight
        + slippage_score * config.slippage_weight
        + fee_drag_score * config.fee_drag_weight
        + quote_freshness_score * config.quote_freshness_weight,
    )


def _row_status(
    *,
    available_depth: Decimal,
    spread_ratio: Decimal,
    slippage_ratio: Decimal,
    fee_drag_ratio: Decimal,
    quote_age_seconds: Decimal,
    consistency_score: Decimal,
    config: ResearchMarketDepthCostConsistencyConfig,
) -> str:
    if (
        available_depth < config.minimum_watch_available_depth
        or spread_ratio > config.maximum_watch_spread_ratio
        or slippage_ratio > config.maximum_watch_slippage_ratio
        or fee_drag_ratio > config.maximum_watch_fee_drag_ratio
        or quote_age_seconds > config.maximum_watch_quote_age_seconds
        or consistency_score < config.watch_consistency_score
    ):
        return "block"
    if (
        available_depth < config.minimum_pass_available_depth
        or spread_ratio > config.maximum_pass_spread_ratio
        or slippage_ratio > config.maximum_pass_slippage_ratio
        or fee_drag_ratio > config.maximum_pass_fee_drag_ratio
        or quote_age_seconds > config.maximum_pass_quote_age_seconds
        or consistency_score < config.pass_consistency_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchMarketDepthCostConsistencyInput,
    *,
    quote_age_seconds: Decimal,
    status: str,
    config: ResearchMarketDepthCostConsistencyConfig,
) -> tuple[str, ...]:
    codes = {
        f"depth_cost_consistency_{status}",
        _low_value_component_reason(
            prefix="available_depth",
            value=item.available_depth,
            pass_threshold=config.minimum_pass_available_depth,
            block_threshold=config.minimum_watch_available_depth,
        ),
        _high_value_component_reason(
            prefix="spread_cost",
            value=item.spread_ratio,
            pass_threshold=config.maximum_pass_spread_ratio,
            block_threshold=config.maximum_watch_spread_ratio,
        ),
        _high_value_component_reason(
            prefix="slippage_cost",
            value=item.slippage_ratio,
            pass_threshold=config.maximum_pass_slippage_ratio,
            block_threshold=config.maximum_watch_slippage_ratio,
        ),
        _high_value_component_reason(
            prefix="fee_drag",
            value=item.fee_drag_ratio,
            pass_threshold=config.maximum_pass_fee_drag_ratio,
            block_threshold=config.maximum_watch_fee_drag_ratio,
        ),
        _high_value_component_reason(
            prefix="quote_freshness",
            value=quote_age_seconds,
            pass_threshold=config.maximum_pass_quote_age_seconds,
            block_threshold=config.maximum_watch_quote_age_seconds,
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
) -> tuple[ResearchMarketDepthCostConsistencyInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for value in values:
        if type(value) is not ResearchMarketDepthCostConsistencyInput:
            raise ValueError(
                "inputs must contain ResearchMarketDepthCostConsistencyInput values",
            )
        _require_hard_flags("input", value)
        if value.bucket_label in seen:
            raise ValueError("bucket_label values must be unique")
        seen.add(value.bucket_label)
    return values


def _summary_reason_codes(
    rows: tuple[ResearchMarketDepthCostConsistencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_depth_cost_consistency_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("depth_cost_consistency_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("depth_cost_consistency_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("depth_cost_consistency_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in COMPONENT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_depth_cost_consistency_inputs",):
        return "block"
    if "depth_cost_consistency_block" in reason_codes:
        return "block"
    if "depth_cost_consistency_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketDepthCostConsistencyRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketDepthCostConsistencyReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketDepthCostConsistencyReasonCodeCount(
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
        ResearchMarketDepthCostConsistencyReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_consistency_score(
    rows: tuple[ResearchMarketDepthCostConsistencyRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.consistency_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _maximum_row_value(
    rows: tuple[ResearchMarketDepthCostConsistencyRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _minimum_row_value(
    rows: tuple[ResearchMarketDepthCostConsistencyRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _status_count(
    rows: tuple[ResearchMarketDepthCostConsistencyRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchMarketDepthCostConsistencyRow, ...],
    prefix: str,
) -> int:
    return sum(
        1
        for row in rows
        if f"{prefix}_watch" in row.reason_codes or f"{prefix}_block" in row.reason_codes
    )


def _validate_row_consistency(row: ResearchMarketDepthCostConsistencyRow) -> None:
    if f"depth_cost_consistency_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")
    weight_sum = _quantize(
        row.depth_weight
        + row.spread_weight
        + row.slippage_weight
        + row.fee_drag_weight
        + row.quote_freshness_weight,
    )
    if weight_sum != ONE:
        raise ValueError("consistency weights must sum to 1")
    expected_score = _quantize(
        row.depth_score * row.depth_weight
        + row.spread_score * row.spread_weight
        + row.slippage_score * row.slippage_weight
        + row.fee_drag_score * row.fee_drag_weight
        + row.quote_freshness_score * row.quote_freshness_weight,
    )
    if row.consistency_score != expected_score:
        raise ValueError("consistency_score must match component scores")
    if row.consistency_score > ONE:
        raise ValueError("consistency_score must be at most one")


def _validate_report_consistency(report: ResearchMarketDepthCostConsistencyReport) -> None:
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
    if report.low_depth_count != _decimal_count(_reason_count(report.rows, "available_depth")):
        raise ValueError("low_depth_count must match rows")
    if report.wide_spread_count != _decimal_count(_reason_count(report.rows, "spread_cost")):
        raise ValueError("wide_spread_count must match rows")
    if report.high_slippage_count != _decimal_count(
        _reason_count(report.rows, "slippage_cost"),
    ):
        raise ValueError("high_slippage_count must match rows")
    if report.high_fee_drag_count != _decimal_count(_reason_count(report.rows, "fee_drag")):
        raise ValueError("high_fee_drag_count must match rows")
    if report.stale_quote_count != _decimal_count(
        _reason_count(report.rows, "quote_freshness"),
    ):
        raise ValueError("stale_quote_count must match rows")
    if report.average_consistency_score != _average_consistency_score(report.rows):
        raise ValueError("average_consistency_score must match rows")
    if report.min_available_depth != _minimum_row_value(report.rows, "available_depth"):
        raise ValueError("min_available_depth must match rows")
    if report.max_spread_ratio != _maximum_row_value(report.rows, "spread_ratio"):
        raise ValueError("max_spread_ratio must match rows")
    if report.max_slippage_ratio != _maximum_row_value(report.rows, "slippage_ratio"):
        raise ValueError("max_slippage_ratio must match rows")
    if report.max_fee_drag_ratio != _maximum_row_value(report.rows, "fee_drag_ratio"):
        raise ValueError("max_fee_drag_ratio must match rows")
    if report.max_quote_age_seconds != _maximum_row_value(report.rows, "quote_age_seconds"):
        raise ValueError("max_quote_age_seconds must match rows")
    expected_reasons = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(expected_reasons):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchMarketDepthCostConsistencyRow, ...],
) -> tuple[ResearchMarketDepthCostConsistencyRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketDepthCostConsistencyRow:
            raise ValueError("rows must contain ResearchMarketDepthCostConsistencyRow")
        _require_hard_flags("row", row)
        if row.public_row_ref in seen:
            raise ValueError("public_row_ref values must be unique")
        seen.add(row.public_row_ref)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketDepthCostConsistencyReasonCodeCount, ...],
) -> tuple[ResearchMarketDepthCostConsistencyReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketDepthCostConsistencyReasonCodeCount:
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
    if type(value) is not str or value not in MARKET_DEPTH_COST_CONSISTENCY_STATUSES:
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


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


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


def _derived_report_digest(report: ResearchMarketDepthCostConsistencyReport) -> str:
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
