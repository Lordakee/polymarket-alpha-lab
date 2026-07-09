"""Pure market mechanics risk report for analyst triage."""

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
    "SPREAD_DEPTH_LATENCY_RISK_STATUSES",
    "DEFAULT_RESEARCH_MARKET_SPREAD_DEPTH_LATENCY_RISK_REPORT_CONFIG_VERSION",
    "ResearchMarketSpreadDepthLatencyRiskConfig",
    "ResearchMarketSpreadDepthLatencyRiskInput",
    "ResearchMarketSpreadDepthLatencyRiskReasonCodeCount",
    "ResearchMarketSpreadDepthLatencyRiskReport",
    "ResearchMarketSpreadDepthLatencyRiskRow",
    "build_research_market_spread_depth_latency_risk_report",
    "research_market_spread_depth_latency_risk_report_digest",
    "research_market_spread_depth_latency_risk_report_payload",
)


DEFAULT_RESEARCH_MARKET_SPREAD_DEPTH_LATENCY_RISK_REPORT_CONFIG_VERSION = (
    "research-market-spread-depth-latency-risk-report-v0"
)
SPREAD_DEPTH_LATENCY_RISK_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
COMPONENT_REASON_PRIORITY = (
    "spread_width_block",
    "depth_coverage_block",
    "latency_haircut_block",
    "book_age_block",
    "liquidity_concentration_block",
    "spread_width_watch",
    "depth_coverage_watch",
    "latency_haircut_watch",
    "book_age_watch",
    "liquidity_concentration_watch",
)


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


@dataclass(frozen=True)
class ResearchMarketSpreadDepthLatencyRiskConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_SPREAD_DEPTH_LATENCY_RISK_REPORT_CONFIG_VERSION
    )
    maximum_pass_spread_width_ratio: Decimal = Decimal("0.030000")
    maximum_watch_spread_width_ratio: Decimal = Decimal("0.080000")
    minimum_pass_depth_coverage_ratio: Decimal = Decimal("0.800000")
    minimum_watch_depth_coverage_ratio: Decimal = Decimal("0.400000")
    maximum_pass_latency_haircut_ratio: Decimal = Decimal("0.020000")
    maximum_watch_latency_haircut_ratio: Decimal = Decimal("0.100000")
    maximum_pass_book_age_seconds: Decimal = Decimal("60.000000")
    maximum_watch_book_age_seconds: Decimal = Decimal("300.000000")
    maximum_pass_liquidity_concentration_ratio: Decimal = Decimal("0.500000")
    maximum_watch_liquidity_concentration_ratio: Decimal = Decimal("0.800000")
    spread_width_weight: Decimal = Decimal("0.250000")
    depth_coverage_weight: Decimal = Decimal("0.250000")
    latency_haircut_weight: Decimal = Decimal("0.200000")
    book_age_weight: Decimal = Decimal("0.150000")
    liquidity_concentration_weight: Decimal = Decimal("0.150000")
    maximum_pass_risk_score: Decimal = Decimal("0.250000")
    maximum_watch_risk_score: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadDepthLatencyRiskConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_SPREAD_DEPTH_LATENCY_RISK_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "maximum_pass_spread_width_ratio",
            "maximum_watch_spread_width_ratio",
            "minimum_pass_depth_coverage_ratio",
            "minimum_watch_depth_coverage_ratio",
            "maximum_pass_latency_haircut_ratio",
            "maximum_watch_latency_haircut_ratio",
            "maximum_pass_liquidity_concentration_ratio",
            "maximum_watch_liquidity_concentration_ratio",
            "spread_width_weight",
            "depth_coverage_weight",
            "latency_haircut_weight",
            "book_age_weight",
            "liquidity_concentration_weight",
            "maximum_pass_risk_score",
            "maximum_watch_risk_score",
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
        if self.maximum_pass_spread_width_ratio > self.maximum_watch_spread_width_ratio:
            raise ValueError("maximum_pass_spread_width_ratio must not exceed watch")
        if self.minimum_pass_depth_coverage_ratio < self.minimum_watch_depth_coverage_ratio:
            raise ValueError("minimum_pass_depth_coverage_ratio must be at least watch")
        if (
            self.maximum_pass_latency_haircut_ratio
            > self.maximum_watch_latency_haircut_ratio
        ):
            raise ValueError("maximum_pass_latency_haircut_ratio must not exceed watch")
        if self.maximum_pass_book_age_seconds > self.maximum_watch_book_age_seconds:
            raise ValueError("maximum_pass_book_age_seconds must not exceed watch")
        if (
            self.maximum_pass_liquidity_concentration_ratio
            > self.maximum_watch_liquidity_concentration_ratio
        ):
            raise ValueError(
                "maximum_pass_liquidity_concentration_ratio must not exceed watch",
            )
        if self.maximum_pass_risk_score > self.maximum_watch_risk_score:
            raise ValueError("maximum_pass_risk_score must not exceed watch")
        weight_sum = _quantize(
            self.spread_width_weight
            + self.depth_coverage_weight
            + self.latency_haircut_weight
            + self.book_age_weight
            + self.liquidity_concentration_weight,
        )
        if weight_sum != ONE:
            raise ValueError("risk weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketSpreadDepthLatencyRiskInput:
    bucket_label: str
    observed_at: datetime
    spread_width_ratio: Decimal
    depth_coverage_ratio: Decimal
    latency_haircut_ratio: Decimal
    liquidity_concentration_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadDepthLatencyRiskInput, "input")
        _require_public_label("bucket_label", self.bucket_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_width_ratio",
            "depth_coverage_ratio",
            "latency_haircut_ratio",
            "liquidity_concentration_ratio",
        ):
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
class ResearchMarketSpreadDepthLatencyRiskRow:
    public_row_ref: str
    observed_at: datetime
    book_age_seconds: Decimal
    spread_width_ratio: Decimal
    spread_width_risk_score: Decimal
    depth_coverage_ratio: Decimal
    depth_coverage_risk_score: Decimal
    latency_haircut_ratio: Decimal
    latency_haircut_risk_score: Decimal
    liquidity_concentration_ratio: Decimal
    liquidity_concentration_risk_score: Decimal
    book_age_risk_score: Decimal
    spread_width_weight: Decimal
    depth_coverage_weight: Decimal
    latency_haircut_weight: Decimal
    book_age_weight: Decimal
    liquidity_concentration_weight: Decimal
    risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadDepthLatencyRiskRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "book_age_seconds",
            _require_nonnegative_decimal("book_age_seconds", self.book_age_seconds),
        )
        for field_name in (
            "spread_width_ratio",
            "spread_width_risk_score",
            "depth_coverage_ratio",
            "depth_coverage_risk_score",
            "latency_haircut_ratio",
            "latency_haircut_risk_score",
            "liquidity_concentration_ratio",
            "liquidity_concentration_risk_score",
            "book_age_risk_score",
            "spread_width_weight",
            "depth_coverage_weight",
            "latency_haircut_weight",
            "book_age_weight",
            "liquidity_concentration_weight",
            "risk_score",
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
                sort_values=False,
            ),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketSpreadDepthLatencyRiskReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSpreadDepthLatencyRiskReasonCodeCount,
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
class ResearchMarketSpreadDepthLatencyRiskReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    wide_spread_count: Decimal
    thin_depth_count: Decimal
    latency_haircut_count: Decimal
    aged_book_count: Decimal
    concentrated_liquidity_count: Decimal
    average_risk_score: Decimal | None
    max_spread_width_ratio: Decimal
    min_depth_coverage_ratio: Decimal
    max_latency_haircut_ratio: Decimal
    max_book_age_seconds: Decimal
    max_liquidity_concentration_ratio: Decimal
    status: str
    rows: tuple[ResearchMarketSpreadDepthLatencyRiskRow, ...]
    reason_code_counts: tuple[ResearchMarketSpreadDepthLatencyRiskReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadDepthLatencyRiskReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "wide_spread_count",
            "thin_depth_count",
            "latency_haircut_count",
            "aged_book_count",
            "concentrated_liquidity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_risk_score",
            _require_optional_ratio_decimal("average_risk_score", self.average_risk_score),
        )
        object.__setattr__(
            self,
            "max_book_age_seconds",
            _require_nonnegative_decimal("max_book_age_seconds", self.max_book_age_seconds),
        )
        for field_name in (
            "max_spread_width_ratio",
            "min_depth_coverage_ratio",
            "max_latency_haircut_ratio",
            "max_liquidity_concentration_ratio",
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
                sort_values=False,
            ),
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


def build_research_market_spread_depth_latency_risk_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketSpreadDepthLatencyRiskConfig,
    generated_at: datetime,
) -> ResearchMarketSpreadDepthLatencyRiskReport:
    if type(config) is not ResearchMarketSpreadDepthLatencyRiskConfig:
        raise ValueError("config must be a ResearchMarketSpreadDepthLatencyRiskConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    for item in input_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    sorted_items = tuple(sorted(input_items, key=lambda item: item.bucket_label))
    rows = tuple(
        _row_from_input(
            item,
            public_row_ref=f"mechanics_risk_group_{index:03d}",
            config=config,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(sorted_items, start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketSpreadDepthLatencyRiskReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        wide_spread_count=_decimal_count(_reason_count(rows, "spread_width")),
        thin_depth_count=_decimal_count(_reason_count(rows, "depth_coverage")),
        latency_haircut_count=_decimal_count(_reason_count(rows, "latency_haircut")),
        aged_book_count=_decimal_count(_reason_count(rows, "book_age")),
        concentrated_liquidity_count=_decimal_count(
            _reason_count(rows, "liquidity_concentration"),
        ),
        average_risk_score=_average_risk_score(rows),
        max_spread_width_ratio=_maximum_row_value(rows, "spread_width_ratio"),
        min_depth_coverage_ratio=_minimum_row_value(rows, "depth_coverage_ratio"),
        max_latency_haircut_ratio=_maximum_row_value(rows, "latency_haircut_ratio"),
        max_book_age_seconds=_maximum_row_value(rows, "book_age_seconds"),
        max_liquidity_concentration_ratio=_maximum_row_value(
            rows,
            "liquidity_concentration_ratio",
        ),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_spread_depth_latency_risk_report_payload(
    report: ResearchMarketSpreadDepthLatencyRiskReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketSpreadDepthLatencyRiskReport:
        raise ValueError("report must be a ResearchMarketSpreadDepthLatencyRiskReport")
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


def research_market_spread_depth_latency_risk_report_digest(
    report: ResearchMarketSpreadDepthLatencyRiskReport,
) -> str:
    if type(report) is not ResearchMarketSpreadDepthLatencyRiskReport:
        raise ValueError("report must be a ResearchMarketSpreadDepthLatencyRiskReport")
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
    item: ResearchMarketSpreadDepthLatencyRiskInput,
    *,
    public_row_ref: str,
    config: ResearchMarketSpreadDepthLatencyRiskConfig,
    generated_at: datetime,
) -> ResearchMarketSpreadDepthLatencyRiskRow:
    book_age_seconds = _age_seconds(generated_at, item.observed_at)
    spread_width_risk_score = _high_ratio_risk(
        item.spread_width_ratio,
        config.maximum_watch_spread_width_ratio,
    )
    depth_coverage_risk_score = _quantize(ONE - item.depth_coverage_ratio)
    latency_haircut_risk_score = _high_ratio_risk(
        item.latency_haircut_ratio,
        config.maximum_watch_latency_haircut_ratio,
    )
    book_age_risk_score = _high_ratio_risk(
        book_age_seconds,
        config.maximum_watch_book_age_seconds,
    )
    liquidity_concentration_risk_score = item.liquidity_concentration_ratio
    risk_score = _risk_score(
        spread_width_risk_score=spread_width_risk_score,
        depth_coverage_risk_score=depth_coverage_risk_score,
        latency_haircut_risk_score=latency_haircut_risk_score,
        book_age_risk_score=book_age_risk_score,
        liquidity_concentration_risk_score=liquidity_concentration_risk_score,
        config=config,
    )
    status = _row_status(
        item=item,
        book_age_seconds=book_age_seconds,
        risk_score=risk_score,
        config=config,
    )
    return ResearchMarketSpreadDepthLatencyRiskRow(
        public_row_ref=public_row_ref,
        observed_at=item.observed_at,
        book_age_seconds=book_age_seconds,
        spread_width_ratio=item.spread_width_ratio,
        spread_width_risk_score=spread_width_risk_score,
        depth_coverage_ratio=item.depth_coverage_ratio,
        depth_coverage_risk_score=depth_coverage_risk_score,
        latency_haircut_ratio=item.latency_haircut_ratio,
        latency_haircut_risk_score=latency_haircut_risk_score,
        liquidity_concentration_ratio=item.liquidity_concentration_ratio,
        liquidity_concentration_risk_score=liquidity_concentration_risk_score,
        book_age_risk_score=book_age_risk_score,
        spread_width_weight=config.spread_width_weight,
        depth_coverage_weight=config.depth_coverage_weight,
        latency_haircut_weight=config.latency_haircut_weight,
        book_age_weight=config.book_age_weight,
        liquidity_concentration_weight=config.liquidity_concentration_weight,
        risk_score=risk_score,
        status=status,
        reason_codes=_row_reason_codes(
            item,
            book_age_seconds=book_age_seconds,
            status=status,
            config=config,
        ),
    )


def _high_ratio_risk(value: Decimal, one_at: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = value / one_at
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return _quantize(score)


def _risk_score(
    *,
    spread_width_risk_score: Decimal,
    depth_coverage_risk_score: Decimal,
    latency_haircut_risk_score: Decimal,
    book_age_risk_score: Decimal,
    liquidity_concentration_risk_score: Decimal,
    config: ResearchMarketSpreadDepthLatencyRiskConfig,
) -> Decimal:
    return _quantize(
        spread_width_risk_score * config.spread_width_weight
        + depth_coverage_risk_score * config.depth_coverage_weight
        + latency_haircut_risk_score * config.latency_haircut_weight
        + book_age_risk_score * config.book_age_weight
        + liquidity_concentration_risk_score * config.liquidity_concentration_weight,
    )


def _row_status(
    *,
    item: ResearchMarketSpreadDepthLatencyRiskInput,
    book_age_seconds: Decimal,
    risk_score: Decimal,
    config: ResearchMarketSpreadDepthLatencyRiskConfig,
) -> str:
    if (
        item.spread_width_ratio > config.maximum_watch_spread_width_ratio
        or item.depth_coverage_ratio < config.minimum_watch_depth_coverage_ratio
        or item.latency_haircut_ratio > config.maximum_watch_latency_haircut_ratio
        or book_age_seconds > config.maximum_watch_book_age_seconds
        or (
            item.liquidity_concentration_ratio
            > config.maximum_watch_liquidity_concentration_ratio
        )
        or risk_score > config.maximum_watch_risk_score
    ):
        return "block"
    if (
        item.spread_width_ratio > config.maximum_pass_spread_width_ratio
        or item.depth_coverage_ratio < config.minimum_pass_depth_coverage_ratio
        or item.latency_haircut_ratio > config.maximum_pass_latency_haircut_ratio
        or book_age_seconds > config.maximum_pass_book_age_seconds
        or (
            item.liquidity_concentration_ratio
            > config.maximum_pass_liquidity_concentration_ratio
        )
        or risk_score > config.maximum_pass_risk_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchMarketSpreadDepthLatencyRiskInput,
    *,
    book_age_seconds: Decimal,
    status: str,
    config: ResearchMarketSpreadDepthLatencyRiskConfig,
) -> tuple[str, ...]:
    codes = {
        f"spread_depth_latency_risk_{status}",
        _high_value_component_reason(
            prefix="spread_width",
            value=item.spread_width_ratio,
            pass_threshold=config.maximum_pass_spread_width_ratio,
            block_threshold=config.maximum_watch_spread_width_ratio,
        ),
        _low_value_component_reason(
            prefix="depth_coverage",
            value=item.depth_coverage_ratio,
            pass_threshold=config.minimum_pass_depth_coverage_ratio,
            block_threshold=config.minimum_watch_depth_coverage_ratio,
        ),
        _high_value_component_reason(
            prefix="latency_haircut",
            value=item.latency_haircut_ratio,
            pass_threshold=config.maximum_pass_latency_haircut_ratio,
            block_threshold=config.maximum_watch_latency_haircut_ratio,
        ),
        _high_value_component_reason(
            prefix="book_age",
            value=book_age_seconds,
            pass_threshold=config.maximum_pass_book_age_seconds,
            block_threshold=config.maximum_watch_book_age_seconds,
        ),
        _high_value_component_reason(
            prefix="liquidity_concentration",
            value=item.liquidity_concentration_ratio,
            pass_threshold=config.maximum_pass_liquidity_concentration_ratio,
            block_threshold=config.maximum_watch_liquidity_concentration_ratio,
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
) -> tuple[ResearchMarketSpreadDepthLatencyRiskInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for value in values:
        if type(value) is not ResearchMarketSpreadDepthLatencyRiskInput:
            raise ValueError(
                "inputs must contain ResearchMarketSpreadDepthLatencyRiskInput values",
            )
        _require_hard_flags("input", value)
        if value.bucket_label in seen:
            raise ValueError("bucket_label values must be unique")
        seen.add(value.bucket_label)
    return values


def _summary_reason_codes(
    rows: tuple[ResearchMarketSpreadDepthLatencyRiskRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_spread_depth_latency_risk_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("spread_depth_latency_risk_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("spread_depth_latency_risk_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("spread_depth_latency_risk_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in COMPONENT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_spread_depth_latency_risk_inputs",):
        return "block"
    if "spread_depth_latency_risk_block" in reason_codes:
        return "block"
    if "spread_depth_latency_risk_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketSpreadDepthLatencyRiskRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketSpreadDepthLatencyRiskReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketSpreadDepthLatencyRiskReasonCodeCount(
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
        ResearchMarketSpreadDepthLatencyRiskReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_risk_score(
    rows: tuple[ResearchMarketSpreadDepthLatencyRiskRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.risk_score for row in rows), ZERO) / Decimal(len(rows)))


def _maximum_row_value(
    rows: tuple[ResearchMarketSpreadDepthLatencyRiskRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _minimum_row_value(
    rows: tuple[ResearchMarketSpreadDepthLatencyRiskRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _status_count(
    rows: tuple[ResearchMarketSpreadDepthLatencyRiskRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchMarketSpreadDepthLatencyRiskRow, ...],
    prefix: str,
) -> int:
    return sum(
        1
        for row in rows
        if f"{prefix}_watch" in row.reason_codes or f"{prefix}_block" in row.reason_codes
    )


def _validate_row_consistency(row: ResearchMarketSpreadDepthLatencyRiskRow) -> None:
    if f"spread_depth_latency_risk_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")
    weight_sum = _quantize(
        row.spread_width_weight
        + row.depth_coverage_weight
        + row.latency_haircut_weight
        + row.book_age_weight
        + row.liquidity_concentration_weight,
    )
    if weight_sum != ONE:
        raise ValueError("risk weights must sum to 1")
    expected_score = _quantize(
        row.spread_width_risk_score * row.spread_width_weight
        + row.depth_coverage_risk_score * row.depth_coverage_weight
        + row.latency_haircut_risk_score * row.latency_haircut_weight
        + row.book_age_risk_score * row.book_age_weight
        + row.liquidity_concentration_risk_score
        * row.liquidity_concentration_weight,
    )
    if row.risk_score != expected_score:
        raise ValueError("risk_score must match component scores")


def _validate_report_consistency(report: ResearchMarketSpreadDepthLatencyRiskReport) -> None:
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
    if report.wide_spread_count != _decimal_count(_reason_count(report.rows, "spread_width")):
        raise ValueError("wide_spread_count must match rows")
    if report.thin_depth_count != _decimal_count(
        _reason_count(report.rows, "depth_coverage"),
    ):
        raise ValueError("thin_depth_count must match rows")
    if report.latency_haircut_count != _decimal_count(
        _reason_count(report.rows, "latency_haircut"),
    ):
        raise ValueError("latency_haircut_count must match rows")
    if report.aged_book_count != _decimal_count(_reason_count(report.rows, "book_age")):
        raise ValueError("aged_book_count must match rows")
    if report.concentrated_liquidity_count != _decimal_count(
        _reason_count(report.rows, "liquidity_concentration"),
    ):
        raise ValueError("concentrated_liquidity_count must match rows")
    if report.average_risk_score != _average_risk_score(report.rows):
        raise ValueError("average_risk_score must match rows")
    if report.max_spread_width_ratio != _maximum_row_value(rows=report.rows, field_name="spread_width_ratio"):
        raise ValueError("max_spread_width_ratio must match rows")
    if report.min_depth_coverage_ratio != _minimum_row_value(
        report.rows,
        "depth_coverage_ratio",
    ):
        raise ValueError("min_depth_coverage_ratio must match rows")
    if report.max_latency_haircut_ratio != _maximum_row_value(
        report.rows,
        "latency_haircut_ratio",
    ):
        raise ValueError("max_latency_haircut_ratio must match rows")
    if report.max_book_age_seconds != _maximum_row_value(report.rows, "book_age_seconds"):
        raise ValueError("max_book_age_seconds must match rows")
    if report.max_liquidity_concentration_ratio != _maximum_row_value(
        report.rows,
        "liquidity_concentration_ratio",
    ):
        raise ValueError("max_liquidity_concentration_ratio must match rows")
    expected_reasons = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(expected_reasons):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchMarketSpreadDepthLatencyRiskRow, ...],
) -> tuple[ResearchMarketSpreadDepthLatencyRiskRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketSpreadDepthLatencyRiskRow:
            raise ValueError("rows must contain ResearchMarketSpreadDepthLatencyRiskRow")
        _require_hard_flags("row", row)
        if row.public_row_ref in seen:
            raise ValueError("public_row_ref values must be unique")
        seen.add(row.public_row_ref)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketSpreadDepthLatencyRiskReasonCodeCount, ...],
) -> tuple[ResearchMarketSpreadDepthLatencyRiskReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketSpreadDepthLatencyRiskReasonCodeCount:
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
    if type(value) is not str or value not in SPREAD_DEPTH_LATENCY_RISK_STATUSES:
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
    sort_values: bool = True,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    normalized = tuple(_require_reason_code(name, value) for value in values)
    if sort_values:
        normalized = tuple(sorted(set(normalized)))
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
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{name} must be a sha256 hex digest")
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


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime payload value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if type(value) is float:
        raise ValueError("payload value must not be a float")
    if type(value) in (str, bool):
        return value
    raise ValueError("payload value is not supported")


def _derived_report_digest(report: ResearchMarketSpreadDepthLatencyRiskReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _contains_unsafe_public_text(key):
                raise ValueError("payload contains unsafe public key")
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str) and _contains_unsafe_public_text(value):
        raise ValueError("payload contains unsafe public text")


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
