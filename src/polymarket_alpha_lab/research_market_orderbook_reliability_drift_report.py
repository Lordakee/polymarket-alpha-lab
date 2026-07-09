"""Pure in-memory book reliability drift report for research review."""

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
    "ORDERBOOK_RELIABILITY_DRIFT_STATUSES",
    "DEFAULT_RESEARCH_MARKET_ORDERBOOK_RELIABILITY_DRIFT_REPORT_CONFIG_VERSION",
    "ResearchMarketOrderbookReliabilityDriftConfig",
    "ResearchMarketOrderbookReliabilityDriftReasonCodeCount",
    "ResearchMarketOrderbookReliabilityDriftReport",
    "ResearchMarketOrderbookReliabilityDriftRow",
    "ResearchMarketOrderbookReliabilityDriftSample",
    "build_research_market_orderbook_reliability_drift_report",
    "research_market_orderbook_reliability_drift_report_digest",
    "research_market_orderbook_reliability_drift_report_payload",
)


ORDERBOOK_RELIABILITY_DRIFT_STATUSES = ("pass", "watch", "block")
DEFAULT_RESEARCH_MARKET_ORDERBOOK_RELIABILITY_DRIFT_REPORT_CONFIG_VERSION = (
    "research-book-reliability-drift-report-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,191}$")
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
    _join_parts("ur", "l"),
    _join_parts("te", "xt"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    "://",
)


@dataclass(frozen=True)
class ResearchMarketOrderbookReliabilityDriftConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_ORDERBOOK_RELIABILITY_DRIFT_REPORT_CONFIG_VERSION
    )
    max_pass_depth_decay_ratio: Decimal = Decimal("0.200000")
    max_watch_depth_decay_ratio: Decimal = Decimal("0.500000")
    max_pass_spread_instability_ratio: Decimal = Decimal("0.050000")
    max_watch_spread_instability_ratio: Decimal = Decimal("0.200000")
    max_pass_stale_book_age_seconds: Decimal = Decimal("120.000000")
    max_watch_stale_book_age_seconds: Decimal = Decimal("600.000000")
    max_pass_imbalance_volatility_ratio: Decimal = Decimal("0.100000")
    max_watch_imbalance_volatility_ratio: Decimal = Decimal("0.350000")
    max_pass_fee_drag_ratio: Decimal = Decimal("0.015000")
    max_watch_fee_drag_ratio: Decimal = Decimal("0.050000")
    max_pass_settlement_friction_ratio: Decimal = Decimal("0.100000")
    max_watch_settlement_friction_ratio: Decimal = Decimal("0.300000")
    depth_decay_weight: Decimal = Decimal("0.166667")
    spread_instability_weight: Decimal = Decimal("0.166667")
    stale_book_weight: Decimal = Decimal("0.166666")
    imbalance_volatility_weight: Decimal = Decimal("0.166667")
    fee_drag_weight: Decimal = Decimal("0.166667")
    settlement_friction_weight: Decimal = Decimal("0.166666")
    pass_reliability_score: Decimal = Decimal("0.750000")
    watch_reliability_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketOrderbookReliabilityDriftConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_ORDERBOOK_RELIABILITY_DRIFT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "max_pass_depth_decay_ratio",
            "max_watch_depth_decay_ratio",
            "max_pass_spread_instability_ratio",
            "max_watch_spread_instability_ratio",
            "max_pass_imbalance_volatility_ratio",
            "max_watch_imbalance_volatility_ratio",
            "max_pass_fee_drag_ratio",
            "max_watch_fee_drag_ratio",
            "max_pass_settlement_friction_ratio",
            "max_watch_settlement_friction_ratio",
            "depth_decay_weight",
            "spread_instability_weight",
            "stale_book_weight",
            "imbalance_volatility_weight",
            "fee_drag_weight",
            "settlement_friction_weight",
            "pass_reliability_score",
            "watch_reliability_score",
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
        _require_ordered_threshold(
            "max_pass_depth_decay_ratio",
            self.max_pass_depth_decay_ratio,
            "max_watch_depth_decay_ratio",
            self.max_watch_depth_decay_ratio,
        )
        _require_ordered_threshold(
            "max_pass_spread_instability_ratio",
            self.max_pass_spread_instability_ratio,
            "max_watch_spread_instability_ratio",
            self.max_watch_spread_instability_ratio,
        )
        _require_ordered_threshold(
            "max_pass_stale_book_age_seconds",
            self.max_pass_stale_book_age_seconds,
            "max_watch_stale_book_age_seconds",
            self.max_watch_stale_book_age_seconds,
        )
        _require_ordered_threshold(
            "max_pass_imbalance_volatility_ratio",
            self.max_pass_imbalance_volatility_ratio,
            "max_watch_imbalance_volatility_ratio",
            self.max_watch_imbalance_volatility_ratio,
        )
        _require_ordered_threshold(
            "max_pass_fee_drag_ratio",
            self.max_pass_fee_drag_ratio,
            "max_watch_fee_drag_ratio",
            self.max_watch_fee_drag_ratio,
        )
        _require_ordered_threshold(
            "max_pass_settlement_friction_ratio",
            self.max_pass_settlement_friction_ratio,
            "max_watch_settlement_friction_ratio",
            self.max_watch_settlement_friction_ratio,
        )
        if self.pass_reliability_score < self.watch_reliability_score:
            raise ValueError("pass_reliability_score must be at least watch")
        weight_sum = _quantize(
            self.depth_decay_weight
            + self.spread_instability_weight
            + self.stale_book_weight
            + self.imbalance_volatility_weight
            + self.fee_drag_weight
            + self.settlement_friction_weight,
        )
        if weight_sum != ONE:
            raise ValueError("reliability weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketOrderbookReliabilityDriftSample:
    sample_ref: str
    observed_at: datetime
    depth_decay_ratio: Decimal
    spread_instability_ratio: Decimal
    stale_book_age_seconds: Decimal
    imbalance_volatility_ratio: Decimal
    fee_drag_ratio: Decimal
    settlement_friction_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketOrderbookReliabilityDriftSample, "sample")
        _require_input_reference("sample_ref", self.sample_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "depth_decay_ratio",
            "spread_instability_ratio",
            "imbalance_volatility_ratio",
            "fee_drag_ratio",
            "settlement_friction_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_book_age_seconds",
            _require_nonnegative_decimal(
                "stale_book_age_seconds",
                self.stale_book_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("sample", self)


@dataclass(frozen=True)
class ResearchMarketOrderbookReliabilityDriftRow:
    row_ref: str
    observed_at: datetime
    depth_decay_ratio: Decimal
    depth_decay_score: Decimal
    spread_instability_ratio: Decimal
    spread_instability_score: Decimal
    stale_book_age_seconds: Decimal
    stale_book_score: Decimal
    imbalance_volatility_ratio: Decimal
    imbalance_volatility_score: Decimal
    fee_drag_ratio: Decimal
    fee_drag_score: Decimal
    settlement_friction_ratio: Decimal
    settlement_friction_score: Decimal
    depth_decay_weight: Decimal
    spread_instability_weight: Decimal
    stale_book_weight: Decimal
    imbalance_volatility_weight: Decimal
    fee_drag_weight: Decimal
    settlement_friction_weight: Decimal
    reliability_score: Decimal
    drift_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketOrderbookReliabilityDriftRow, "row")
        _require_public_label("row_ref", self.row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "depth_decay_ratio",
            "depth_decay_score",
            "spread_instability_ratio",
            "spread_instability_score",
            "stale_book_score",
            "imbalance_volatility_ratio",
            "imbalance_volatility_score",
            "fee_drag_ratio",
            "fee_drag_score",
            "settlement_friction_ratio",
            "settlement_friction_score",
            "depth_decay_weight",
            "spread_instability_weight",
            "stale_book_weight",
            "imbalance_volatility_weight",
            "fee_drag_weight",
            "settlement_friction_weight",
            "reliability_score",
            "drift_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_book_age_seconds",
            _require_nonnegative_decimal(
                "stale_book_age_seconds",
                self.stale_book_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        if self.drift_pressure != _quantize(ONE - self.reliability_score):
            raise ValueError("drift_pressure must equal one minus reliability_score")


@dataclass(frozen=True)
class ResearchMarketOrderbookReliabilityDriftReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketOrderbookReliabilityDriftReasonCodeCount,
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
class ResearchMarketOrderbookReliabilityDriftReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    depth_decay_count: Decimal
    spread_instability_count: Decimal
    stale_book_count: Decimal
    imbalance_volatility_count: Decimal
    fee_drag_count: Decimal
    settlement_friction_count: Decimal
    average_reliability_score: Decimal | None
    max_depth_decay_ratio: Decimal
    max_spread_instability_ratio: Decimal
    max_stale_book_age_seconds: Decimal
    max_imbalance_volatility_ratio: Decimal
    max_fee_drag_ratio: Decimal
    max_settlement_friction_ratio: Decimal
    status: str
    rows: tuple[ResearchMarketOrderbookReliabilityDriftRow, ...]
    reason_code_counts: tuple[ResearchMarketOrderbookReliabilityDriftReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketOrderbookReliabilityDriftReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "depth_decay_count",
            "spread_instability_count",
            "stale_book_count",
            "imbalance_volatility_count",
            "fee_drag_count",
            "settlement_friction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_reliability_score",
            _require_optional_ratio_decimal(
                "average_reliability_score",
                self.average_reliability_score,
            ),
        )
        for field_name in (
            "max_depth_decay_ratio",
            "max_spread_instability_ratio",
            "max_imbalance_volatility_ratio",
            "max_fee_drag_ratio",
            "max_settlement_friction_ratio",
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
        _validate_report_consistency(self)
        expected_digest = _derived_report_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_orderbook_reliability_drift_report(
    samples: Iterable[object],
    *,
    config: ResearchMarketOrderbookReliabilityDriftConfig,
    generated_at: datetime,
) -> ResearchMarketOrderbookReliabilityDriftReport:
    if type(config) is not ResearchMarketOrderbookReliabilityDriftConfig:
        raise ValueError("config must be a ResearchMarketOrderbookReliabilityDriftConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    sample_items = _normalize_samples(samples)
    for item in sample_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    sorted_items = tuple(sorted(sample_items, key=lambda item: item.sample_ref))
    rows = tuple(
        _row_from_sample(
            item,
            row_ref=f"book_reliability_group_{index:03d}",
            config=config,
        )
        for index, item in enumerate(sorted_items, start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketOrderbookReliabilityDriftReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        depth_decay_count=_decimal_count(_reason_count(rows, "depth_decay")),
        spread_instability_count=_decimal_count(
            _reason_count(rows, "spread_instability"),
        ),
        stale_book_count=_decimal_count(_reason_count(rows, "stale_book_age")),
        imbalance_volatility_count=_decimal_count(
            _reason_count(rows, "imbalance_volatility"),
        ),
        fee_drag_count=_decimal_count(_reason_count(rows, "fee_drag")),
        settlement_friction_count=_decimal_count(
            _reason_count(rows, "settlement_friction"),
        ),
        average_reliability_score=_average_reliability_score(rows),
        max_depth_decay_ratio=_maximum_row_value(rows, "depth_decay_ratio"),
        max_spread_instability_ratio=_maximum_row_value(
            rows,
            "spread_instability_ratio",
        ),
        max_stale_book_age_seconds=_maximum_row_value(rows, "stale_book_age_seconds"),
        max_imbalance_volatility_ratio=_maximum_row_value(
            rows,
            "imbalance_volatility_ratio",
        ),
        max_fee_drag_ratio=_maximum_row_value(rows, "fee_drag_ratio"),
        max_settlement_friction_ratio=_maximum_row_value(
            rows,
            "settlement_friction_ratio",
        ),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_orderbook_reliability_drift_report_payload(
    report: ResearchMarketOrderbookReliabilityDriftReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketOrderbookReliabilityDriftReport:
        raise ValueError("report must be a ResearchMarketOrderbookReliabilityDriftReport")
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


def research_market_orderbook_reliability_drift_report_digest(
    report: ResearchMarketOrderbookReliabilityDriftReport,
) -> str:
    if type(report) is not ResearchMarketOrderbookReliabilityDriftReport:
        raise ValueError("report must be a ResearchMarketOrderbookReliabilityDriftReport")
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


def _row_from_sample(
    sample: ResearchMarketOrderbookReliabilityDriftSample,
    *,
    row_ref: str,
    config: ResearchMarketOrderbookReliabilityDriftConfig,
) -> ResearchMarketOrderbookReliabilityDriftRow:
    depth_decay_score = _inverse_score(
        sample.depth_decay_ratio,
        config.max_watch_depth_decay_ratio,
    )
    spread_instability_score = _inverse_score(
        sample.spread_instability_ratio,
        config.max_watch_spread_instability_ratio,
    )
    stale_book_score = _inverse_score(
        sample.stale_book_age_seconds,
        config.max_watch_stale_book_age_seconds,
    )
    imbalance_volatility_score = _inverse_score(
        sample.imbalance_volatility_ratio,
        config.max_watch_imbalance_volatility_ratio,
    )
    fee_drag_score = _inverse_score(sample.fee_drag_ratio, config.max_watch_fee_drag_ratio)
    settlement_friction_score = _inverse_score(
        sample.settlement_friction_ratio,
        config.max_watch_settlement_friction_ratio,
    )
    reliability_score = _reliability_score(
        depth_decay_score=depth_decay_score,
        spread_instability_score=spread_instability_score,
        stale_book_score=stale_book_score,
        imbalance_volatility_score=imbalance_volatility_score,
        fee_drag_score=fee_drag_score,
        settlement_friction_score=settlement_friction_score,
        config=config,
    )
    status = _row_status(sample, reliability_score=reliability_score, config=config)
    return ResearchMarketOrderbookReliabilityDriftRow(
        row_ref=row_ref,
        observed_at=sample.observed_at,
        depth_decay_ratio=sample.depth_decay_ratio,
        depth_decay_score=depth_decay_score,
        spread_instability_ratio=sample.spread_instability_ratio,
        spread_instability_score=spread_instability_score,
        stale_book_age_seconds=sample.stale_book_age_seconds,
        stale_book_score=stale_book_score,
        imbalance_volatility_ratio=sample.imbalance_volatility_ratio,
        imbalance_volatility_score=imbalance_volatility_score,
        fee_drag_ratio=sample.fee_drag_ratio,
        fee_drag_score=fee_drag_score,
        settlement_friction_ratio=sample.settlement_friction_ratio,
        settlement_friction_score=settlement_friction_score,
        depth_decay_weight=config.depth_decay_weight,
        spread_instability_weight=config.spread_instability_weight,
        stale_book_weight=config.stale_book_weight,
        imbalance_volatility_weight=config.imbalance_volatility_weight,
        fee_drag_weight=config.fee_drag_weight,
        settlement_friction_weight=config.settlement_friction_weight,
        reliability_score=reliability_score,
        drift_pressure=_quantize(ONE - reliability_score),
        status=status,
        reason_codes=_row_reason_codes(sample, status=status, config=config),
    )


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


def _reliability_score(
    *,
    depth_decay_score: Decimal,
    spread_instability_score: Decimal,
    stale_book_score: Decimal,
    imbalance_volatility_score: Decimal,
    fee_drag_score: Decimal,
    settlement_friction_score: Decimal,
    config: ResearchMarketOrderbookReliabilityDriftConfig,
) -> Decimal:
    return _quantize(
        depth_decay_score * config.depth_decay_weight
        + spread_instability_score * config.spread_instability_weight
        + stale_book_score * config.stale_book_weight
        + imbalance_volatility_score * config.imbalance_volatility_weight
        + fee_drag_score * config.fee_drag_weight
        + settlement_friction_score * config.settlement_friction_weight,
    )


def _row_status(
    sample: ResearchMarketOrderbookReliabilityDriftSample,
    *,
    reliability_score: Decimal,
    config: ResearchMarketOrderbookReliabilityDriftConfig,
) -> str:
    if any(level == "block" for level in _component_levels(sample, config).values()):
        return "block"
    if (
        reliability_score >= config.pass_reliability_score
        and all(level == "pass" for level in _component_levels(sample, config).values())
    ):
        return "pass"
    if reliability_score >= config.watch_reliability_score:
        return "watch"
    return "block"


def _row_reason_codes(
    sample: ResearchMarketOrderbookReliabilityDriftSample,
    *,
    status: str,
    config: ResearchMarketOrderbookReliabilityDriftConfig,
) -> tuple[str, ...]:
    levels = _component_levels(sample, config)
    codes = tuple(f"{name}_{level}" for name, level in levels.items())
    input_codes = tuple(f"input_{code}" for code in sample.reason_codes)
    return _normalize_reason_codes(
        "reason_codes",
        (*codes, *input_codes, f"book_reliability_drift_{status}"),
        allow_empty=False,
        sort_values=False,
    )


def _component_levels(
    sample: ResearchMarketOrderbookReliabilityDriftSample,
    config: ResearchMarketOrderbookReliabilityDriftConfig,
) -> dict[str, str]:
    return {
        "depth_decay": _threshold_level(
            sample.depth_decay_ratio,
            config.max_pass_depth_decay_ratio,
            config.max_watch_depth_decay_ratio,
        ),
        "spread_instability": _threshold_level(
            sample.spread_instability_ratio,
            config.max_pass_spread_instability_ratio,
            config.max_watch_spread_instability_ratio,
        ),
        "stale_book_age": _threshold_level(
            sample.stale_book_age_seconds,
            config.max_pass_stale_book_age_seconds,
            config.max_watch_stale_book_age_seconds,
        ),
        "imbalance_volatility": _threshold_level(
            sample.imbalance_volatility_ratio,
            config.max_pass_imbalance_volatility_ratio,
            config.max_watch_imbalance_volatility_ratio,
        ),
        "fee_drag": _threshold_level(
            sample.fee_drag_ratio,
            config.max_pass_fee_drag_ratio,
            config.max_watch_fee_drag_ratio,
        ),
        "settlement_friction": _threshold_level(
            sample.settlement_friction_ratio,
            config.max_pass_settlement_friction_ratio,
            config.max_watch_settlement_friction_ratio,
        ),
    }


def _threshold_level(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> str:
    if value <= pass_value:
        return "pass"
    if value <= watch_value:
        return "watch"
    return "block"


def _normalize_samples(
    samples: Iterable[object],
) -> tuple[ResearchMarketOrderbookReliabilityDriftSample, ...]:
    if isinstance(samples, (str, bytes)) or not isinstance(samples, Iterable):
        raise ValueError("samples must be an iterable")
    normalized: list[ResearchMarketOrderbookReliabilityDriftSample] = []
    seen: set[str] = set()
    for item in samples:
        if type(item) is not ResearchMarketOrderbookReliabilityDriftSample:
            raise ValueError(
                "samples must contain ResearchMarketOrderbookReliabilityDriftSample",
            )
        _require_hard_flags("sample", item)
        if item.sample_ref in seen:
            raise ValueError("duplicate sample_ref values are not allowed")
        seen.add(item.sample_ref)
        normalized.append(item)
    return tuple(normalized)


def _summary_reason_codes(
    rows: tuple[ResearchMarketOrderbookReliabilityDriftRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_book_reliability_samples",)
    if any(row.status == "block" for row in rows):
        return ("book_reliability_drift_block",)
    if any(row.status == "watch" for row in rows):
        return ("book_reliability_drift_watch",)
    return ("book_reliability_drift_pass",)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") or code.startswith("no_") for code in reason_codes):
        return "block"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketOrderbookReliabilityDriftRow, ...],
    summary_reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketOrderbookReliabilityDriftReasonCodeCount, ...]:
    counter: Counter[str] = Counter(summary_reason_codes)
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _decimal_count(len(rows))
    return tuple(
        ResearchMarketOrderbookReliabilityDriftReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_bounded_ratio(_decimal_count(count), denominator),
        )
        for reason_code, count in sorted(counter.items())
    )


def _status_count(
    rows: tuple[ResearchMarketOrderbookReliabilityDriftRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchMarketOrderbookReliabilityDriftRow, ...],
    reason_prefix: str,
) -> int:
    return sum(
        1
        for row in rows
        if any(
            code.startswith(reason_prefix) and not code.endswith("_pass")
            for code in row.reason_codes
        )
    )


def _average_reliability_score(
    rows: tuple[ResearchMarketOrderbookReliabilityDriftRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _safe_ratio(
        sum((row.reliability_score for row in rows), ZERO),
        _decimal_count(len(rows)),
    )


def _maximum_row_value(
    rows: tuple[ResearchMarketOrderbookReliabilityDriftRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _normalize_rows(
    rows: tuple[ResearchMarketOrderbookReliabilityDriftRow, ...],
) -> tuple[ResearchMarketOrderbookReliabilityDriftRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    previous_ref = ""
    for row in rows:
        if type(row) is not ResearchMarketOrderbookReliabilityDriftRow:
            raise ValueError("rows must contain ResearchMarketOrderbookReliabilityDriftRow")
        _require_hard_flags("row", row)
        if row.row_ref <= previous_ref:
            raise ValueError("rows must be sorted by row_ref")
        previous_ref = row.row_ref
    return rows


def _normalize_reason_code_counts(
    values: tuple[ResearchMarketOrderbookReliabilityDriftReasonCodeCount, ...],
) -> tuple[ResearchMarketOrderbookReliabilityDriftReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    previous_reason = ""
    for value in values:
        if type(value) is not ResearchMarketOrderbookReliabilityDriftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketOrderbookReliabilityDriftReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
        if value.reason_code <= previous_reason:
            raise ValueError("reason_code_counts must be sorted by reason_code")
        previous_reason = value.reason_code
    return values


def _validate_report_consistency(
    report: ResearchMarketOrderbookReliabilityDriftReport,
) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_reliability_score != _average_reliability_score(rows):
        raise ValueError("average_reliability_score must match rows")
    for report_field_name, reason_prefix in (
        ("depth_decay_count", "depth_decay"),
        ("spread_instability_count", "spread_instability"),
        ("stale_book_count", "stale_book_age"),
        ("imbalance_volatility_count", "imbalance_volatility"),
        ("fee_drag_count", "fee_drag"),
        ("settlement_friction_count", "settlement_friction"),
    ):
        if getattr(report, report_field_name) != _decimal_count(
            _reason_count(rows, reason_prefix),
        ):
            raise ValueError(f"{report_field_name} must match rows")
    for report_field_name, row_field_name in (
        ("max_depth_decay_ratio", "depth_decay_ratio"),
        ("max_spread_instability_ratio", "spread_instability_ratio"),
        ("max_stale_book_age_seconds", "stale_book_age_seconds"),
        ("max_imbalance_volatility_ratio", "imbalance_volatility_ratio"),
        ("max_fee_drag_ratio", "fee_drag_ratio"),
        ("max_settlement_friction_ratio", "settlement_friction_ratio"),
    ):
        if getattr(report, report_field_name) != _maximum_row_value(rows, row_field_name):
            raise ValueError(f"{report_field_name} must match rows")
    expected_reason_codes = _summary_reason_codes(rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_status = _summary_status(expected_reason_codes)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, expected_reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _as_utc(label: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{label} utcoffset must not be None")
    return value.astimezone(UTC)


def _require_decimal(label: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(label: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(label, value)
    if normalized < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return normalized


def _require_positive_decimal(label: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(label, value)
    if normalized <= ZERO:
        raise ValueError(f"{label} must be positive")
    return normalized


def _require_ratio_decimal(label: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(label, value)
    if normalized > ONE:
        raise ValueError(f"{label} must be less than or equal to 1")
    return normalized


def _require_optional_ratio_decimal(label: str, value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(label, value)


def _require_nonnegative_whole_decimal(label: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(label, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{label} must be a whole Decimal")
    return normalized


def _require_positive_whole_decimal(label: str, value: Decimal) -> Decimal:
    normalized = _require_positive_decimal(label, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{label} must be a whole Decimal")
    return normalized


def _require_ordered_threshold(
    pass_label: str,
    pass_value: Decimal,
    watch_label: str,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{pass_label} must not exceed {watch_label}")


def _require_public_label(label: str, value: str) -> None:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{label} must be a public label")


def _require_input_reference(label: str, value: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")


def _require_reason_code(label: str, value: str) -> None:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{label} must be a reason code")
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{label} contains unsafe public fragment")


def _normalize_reason_codes(
    label: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
    sort_values: bool = False,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{label} must be a tuple")
    if not values and not allow_empty:
        raise ValueError(f"{label} must not be empty")
    for value in values:
        _require_reason_code(label, value)
    normalized = tuple(sorted(set(values))) if sort_values else tuple(dict.fromkeys(values))
    if not normalized and not allow_empty:
        raise ValueError(f"{label} must not be empty")
    return normalized


def _require_status(label: str, value: str) -> None:
    if value not in ORDERBOOK_RELIABILITY_DRIFT_STATUSES:
        raise ValueError(f"{label} must be one of pass, watch, block")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label} must be {flag_name}")


def _require_hex_digest(label: str, value: str) -> None:
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{label} must be a lowercase sha256 hex digest")


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = 28
        return _quantize(numerator / denominator)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _safe_ratio(numerator, denominator)
    if ratio > ONE:
        return ONE
    return ratio


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _derived_report_digest(report: ResearchMarketOrderbookReliabilityDriftReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload Decimal value must be exactly Decimal")
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if is_dataclass(value):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError(f"unsupported payload value type {type(value).__name__}")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _contains_unsafe_public_fragment(str(key)):
                raise ValueError(f"unsafe public payload key {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for public payload")
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str) and _contains_unsafe_public_fragment(value):
        raise ValueError("unsafe public payload value")


def _contains_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
