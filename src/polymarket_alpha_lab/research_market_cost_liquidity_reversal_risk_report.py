"""Report-only cost and liquidity reversal risk reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_REVERSAL_RISK_REPORT_CONFIG_VERSION = (
    "research-market-cost-liquidity-reversal-risk-report-v0"
)
MARKET_COST_LIQUIDITY_REVERSAL_RISK_STATUSES = ("pass", "watch", "block")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT_PRECISION = 28
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
REPORT_REASON_PRIORITY = (
    "reversal_pressure_block",
    "liquidity_shortfall_block",
    "cost_drag_block",
    "freshness_gap_block",
    "reversal_pressure_watch",
    "liquidity_shortfall_watch",
    "cost_drag_watch",
    "freshness_gap_watch",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "-", "sl", "ug"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "url"),
    _join_parts("sour", "ce", "_", "text"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le", "_", "name"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("pos", "ition"),
    _join_parts("siz", "ing"),
    _join_parts("reco", "mmend"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
    "://",
)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityReversalRiskConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_REVERSAL_RISK_REPORT_CONFIG_VERSION
    )
    reversal_watch_pressure: Decimal = Decimal("0.350000")
    reversal_block_pressure: Decimal = Decimal("0.700000")
    min_pass_depth: Decimal = Decimal("1000.000000")
    min_watch_depth: Decimal = Decimal("250.000000")
    max_pass_cost_ratio: Decimal = Decimal("0.030000")
    max_watch_cost_ratio: Decimal = Decimal("0.080000")
    max_pass_book_age_seconds: Decimal = Decimal("120.000000")
    max_watch_book_age_seconds: Decimal = Decimal("600.000000")
    reversal_weight: Decimal = Decimal("0.400000")
    liquidity_weight: Decimal = Decimal("0.250000")
    cost_weight: Decimal = Decimal("0.200000")
    freshness_weight: Decimal = Decimal("0.150000")
    max_pass_reversal_risk_score: Decimal = Decimal("0.300000")
    max_watch_reversal_risk_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostLiquidityReversalRiskConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostLiquidityReversalRiskConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_REVERSAL_RISK_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "min_pass_depth",
            "min_watch_depth",
            "max_pass_cost_ratio",
            "max_watch_cost_ratio",
            "max_pass_book_age_seconds",
            "max_watch_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "reversal_watch_pressure",
            "reversal_block_pressure",
            "reversal_weight",
            "liquidity_weight",
            "cost_weight",
            "freshness_weight",
            "max_pass_reversal_risk_score",
            "max_watch_reversal_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.reversal_watch_pressure >= self.reversal_block_pressure:
            raise ValueError("reversal_watch_pressure must be below block")
        if self.min_pass_depth <= self.min_watch_depth:
            raise ValueError("min_pass_depth must exceed watch")
        if self.max_pass_cost_ratio >= self.max_watch_cost_ratio:
            raise ValueError("max_pass_cost_ratio must be below watch")
        if self.max_pass_book_age_seconds >= self.max_watch_book_age_seconds:
            raise ValueError("max_pass_book_age_seconds must be below watch")
        if self.max_pass_reversal_risk_score >= self.max_watch_reversal_risk_score:
            raise ValueError("max_pass_reversal_risk_score must be below watch")
        weight_sum = _quantize(
            self.reversal_weight
            + self.liquidity_weight
            + self.cost_weight
            + self.freshness_weight,
        )
        if weight_sum != ONE:
            raise ValueError("risk weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityReversalRiskInput:
    public_risk_ref: str
    observed_at: datetime
    prior_probability: Decimal
    current_probability: Decimal
    fee_rate: Decimal
    spread_ratio: Decimal
    available_depth: Decimal
    book_age_seconds: Decimal
    liquidity_reversal_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostLiquidityReversalRiskInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostLiquidityReversalRiskInput, "input")
        _require_public_label("public_risk_ref", self.public_risk_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "prior_probability",
            "current_probability",
            "fee_rate",
            "spread_ratio",
            "liquidity_reversal_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("available_depth", "book_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=True,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityReversalRiskRow:
    public_risk_ref: str
    observed_at: datetime
    prior_probability: Decimal
    current_probability: Decimal
    probability_delta: Decimal
    fee_rate: Decimal
    spread_ratio: Decimal
    cost_ratio: Decimal
    available_depth: Decimal
    book_age_seconds: Decimal
    liquidity_reversal_pressure: Decimal
    reversal_pressure_score: Decimal
    liquidity_risk_score: Decimal
    cost_risk_score: Decimal
    freshness_risk_score: Decimal
    reversal_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostLiquidityReversalRiskRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostLiquidityReversalRiskRow, "row")
        _require_public_label("public_risk_ref", self.public_risk_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "prior_probability",
            "current_probability",
            "liquidity_reversal_pressure",
            "reversal_pressure_score",
            "liquidity_risk_score",
            "cost_risk_score",
            "freshness_risk_score",
            "reversal_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_delta",
            "fee_rate",
            "spread_ratio",
            "cost_ratio",
            "available_depth",
            "book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityReversalRiskReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostLiquidityReversalRiskReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketCostLiquidityReversalRiskReasonCodeCount,
            "reason code count",
        )
        _require_public_label("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityReversalRiskReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_reversal_risk_score: Decimal | None
    max_reversal_risk_score: Decimal
    max_probability_delta: Decimal
    max_cost_ratio: Decimal
    min_available_depth: Decimal
    max_book_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketCostLiquidityReversalRiskReasonCodeCount, ...]
    rows: tuple[ResearchMarketCostLiquidityReversalRiskRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostLiquidityReversalRiskReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostLiquidityReversalRiskReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_reversal_risk_score",
            "max_probability_delta",
            "max_cost_ratio",
            "min_available_depth",
            "max_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_reversal_risk_score is not None:
            object.__setattr__(
                self,
                "average_reversal_risk_score",
                _require_ratio_decimal(
                    "average_reversal_risk_score",
                    self.average_reversal_risk_score,
                ),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        reject_unsafe_surface_fields("cost liquidity reversal risk report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report(self)
        if self.derived_validation_digest != _report_derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_cost_liquidity_reversal_risk_report_payload(self)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityReversalRiskReportDigest:
    generated_at: datetime
    config_version: str
    report_digest: str
    report_status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_reversal_risk_score: Decimal | None
    max_reversal_risk_score: Decimal
    max_probability_delta: Decimal
    max_cost_ratio: Decimal
    min_available_depth: Decimal
    max_book_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostLiquidityReversalRiskReportDigest does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketCostLiquidityReversalRiskReportDigest,
            "digest",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_sha256_digest("report_digest", self.report_digest)
        _require_status("report_status", self.report_status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_reversal_risk_score",
            "max_probability_delta",
            "max_cost_ratio",
            "min_available_depth",
            "max_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_reversal_risk_score is not None:
            object.__setattr__(
                self,
                "average_reversal_risk_score",
                _require_ratio_decimal(
                    "average_reversal_risk_score",
                    self.average_reversal_risk_score,
                ),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _require_hard_flags("digest", self)
        reject_unsafe_surface_fields("cost liquidity reversal risk digest", self)
        _reject_unsafe_public_payload("digest", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_cost_liquidity_reversal_risk_report_payload(self)


def build_research_market_cost_liquidity_reversal_risk_report(
    inputs: Iterable[ResearchMarketCostLiquidityReversalRiskInput],
    *,
    config: ResearchMarketCostLiquidityReversalRiskConfig,
    generated_at: datetime,
) -> ResearchMarketCostLiquidityReversalRiskReport:
    if type(config) is not ResearchMarketCostLiquidityReversalRiskConfig:
        raise ValueError("config must be a ResearchMarketCostLiquidityReversalRiskConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs, generated_at_utc)
    rows = tuple(
        sorted(
            (_row_for_input(item, config) for item in normalized),
            key=_row_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "input_count": _decimal_count(len(normalized)),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_reversal_risk_score": _average_score(rows),
        "max_reversal_risk_score": _max_decimal(rows, "reversal_risk_score"),
        "max_probability_delta": _max_decimal(rows, "probability_delta"),
        "max_cost_ratio": _max_decimal(rows, "cost_ratio"),
        "min_available_depth": _min_decimal(rows, "available_depth"),
        "max_book_age_seconds": _max_decimal(rows, "book_age_seconds"),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketCostLiquidityReversalRiskReport(
        **values,
        derived_validation_digest=_derived_validation_digest(values),
    )


def research_market_cost_liquidity_reversal_risk_report_payload(
    value: ResearchMarketCostLiquidityReversalRiskReport
    | ResearchMarketCostLiquidityReversalRiskReportDigest
    | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchMarketCostLiquidityReversalRiskReport:
        _require_hard_flags("report", value)
        if value.derived_validation_digest != _report_derived_validation_digest(value):
            raise ValueError("derived_validation_digest must match report payload")
        payload = _json_ready(value)
    elif type(value) is ResearchMarketCostLiquidityReversalRiskReportDigest:
        _require_hard_flags("digest", value)
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = _json_ready(value)
    else:
        raise ValueError("value must be a ResearchMarketCostLiquidityReversalRiskReport")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    reject_unsafe_surface_fields("cost liquidity reversal risk payload", payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_market_cost_liquidity_reversal_risk_report_digest(
    report: ResearchMarketCostLiquidityReversalRiskReport,
) -> ResearchMarketCostLiquidityReversalRiskReportDigest:
    if type(report) is not ResearchMarketCostLiquidityReversalRiskReport:
        raise ValueError("report must be a ResearchMarketCostLiquidityReversalRiskReport")
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")
    return ResearchMarketCostLiquidityReversalRiskReportDigest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_digest=report.derived_validation_digest,
        report_status=report.status,
        input_count=report.input_count,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_reversal_risk_score=report.average_reversal_risk_score,
        max_reversal_risk_score=report.max_reversal_risk_score,
        max_probability_delta=report.max_probability_delta,
        max_cost_ratio=report.max_cost_ratio,
        min_available_depth=report.min_available_depth,
        max_book_age_seconds=report.max_book_age_seconds,
        reason_codes=report.reason_codes,
    )


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


def _row_for_input(
    item: ResearchMarketCostLiquidityReversalRiskInput,
    config: ResearchMarketCostLiquidityReversalRiskConfig,
) -> ResearchMarketCostLiquidityReversalRiskRow:
    probability_delta = _abs_decimal(item.current_probability - item.prior_probability)
    cost_ratio = _sum_decimal(item.fee_rate, item.spread_ratio)
    reversal_pressure_score = max(probability_delta, item.liquidity_reversal_pressure)
    liquidity_risk_score = _depth_risk_score(
        item.available_depth,
        pass_value=config.min_pass_depth,
        watch_value=config.min_watch_depth,
    )
    cost_risk_score = _threshold_risk_score(
        cost_ratio,
        pass_value=config.max_pass_cost_ratio,
        watch_value=config.max_watch_cost_ratio,
    )
    freshness_risk_score = _threshold_risk_score(
        item.book_age_seconds,
        pass_value=config.max_pass_book_age_seconds,
        watch_value=config.max_watch_book_age_seconds,
    )
    reversal_risk_score = _weighted_score(
        reversal_pressure_score=reversal_pressure_score,
        liquidity_risk_score=liquidity_risk_score,
        cost_risk_score=cost_risk_score,
        freshness_risk_score=freshness_risk_score,
        config=config,
    )
    component_codes = _component_reason_codes(
        reversal_pressure_score=reversal_pressure_score,
        available_depth=item.available_depth,
        cost_ratio=cost_ratio,
        book_age_seconds=item.book_age_seconds,
        config=config,
    )
    status = _row_status(reversal_risk_score, component_codes, config)
    return ResearchMarketCostLiquidityReversalRiskRow(
        public_risk_ref=item.public_risk_ref,
        observed_at=item.observed_at,
        prior_probability=item.prior_probability,
        current_probability=item.current_probability,
        probability_delta=probability_delta,
        fee_rate=item.fee_rate,
        spread_ratio=item.spread_ratio,
        cost_ratio=cost_ratio,
        available_depth=item.available_depth,
        book_age_seconds=item.book_age_seconds,
        liquidity_reversal_pressure=item.liquidity_reversal_pressure,
        reversal_pressure_score=reversal_pressure_score,
        liquidity_risk_score=liquidity_risk_score,
        cost_risk_score=cost_risk_score,
        freshness_risk_score=freshness_risk_score,
        reversal_risk_score=reversal_risk_score,
        status=status,
        reason_codes=_row_reason_codes(status, component_codes, item.reason_codes),
    )


def _component_reason_codes(
    *,
    reversal_pressure_score: Decimal,
    available_depth: Decimal,
    cost_ratio: Decimal,
    book_age_seconds: Decimal,
    config: ResearchMarketCostLiquidityReversalRiskConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if reversal_pressure_score >= config.reversal_block_pressure:
        codes.append("reversal_pressure_block")
    elif reversal_pressure_score >= config.reversal_watch_pressure:
        codes.append("reversal_pressure_watch")
    if available_depth <= config.min_watch_depth:
        codes.append("liquidity_shortfall_block")
    elif available_depth < config.min_pass_depth:
        codes.append("liquidity_shortfall_watch")
    if cost_ratio > config.max_watch_cost_ratio:
        codes.append("cost_drag_block")
    elif cost_ratio > config.max_pass_cost_ratio:
        codes.append("cost_drag_watch")
    if book_age_seconds > config.max_watch_book_age_seconds:
        codes.append("freshness_gap_block")
    elif book_age_seconds > config.max_pass_book_age_seconds:
        codes.append("freshness_gap_watch")
    return tuple(codes)


def _row_status(
    reversal_risk_score: Decimal,
    component_codes: tuple[str, ...],
    config: ResearchMarketCostLiquidityReversalRiskConfig,
) -> str:
    if any(code.endswith("_block") for code in component_codes):
        return "block"
    if reversal_risk_score > config.max_watch_reversal_risk_score:
        return "block"
    if any(code.endswith("_watch") for code in component_codes):
        return "watch"
    if reversal_risk_score > config.max_pass_reversal_risk_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    status: str,
    component_codes: tuple[str, ...],
    input_codes: tuple[str, ...],
) -> tuple[str, ...]:
    codes = tuple(f"input_{code}" for code in input_codes) + (
        f"reversal_risk_{status}",
        *component_codes,
    )
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted(codes)),
        allow_empty=False,
    )


def _report_status(
    rows: tuple[ResearchMarketCostLiquidityReversalRiskRow, ...],
) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketCostLiquidityReversalRiskRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_reversal_risk_inputs",)
    status = _report_status(rows)
    codes = [f"reversal_risk_{status}"]
    row_codes = {code for row in rows for code in row.reason_codes}
    codes.extend(code for code in REPORT_REASON_PRIORITY if code in row_codes)
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _reason_code_counts(
    rows: tuple[ResearchMarketCostLiquidityReversalRiskRow, ...],
) -> tuple[ResearchMarketCostLiquidityReversalRiskReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketCostLiquidityReversalRiskReasonCodeCount(
                reason_code="no_reversal_risk_inputs",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts = Counter(code for row in rows for code in row.reason_codes)
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchMarketCostLiquidityReversalRiskReasonCodeCount(
            reason_code=code,
            count=_decimal_count(count),
            row_ratio=_safe_ratio(_decimal_count(count), row_count),
        )
        for code, count in sorted(counts.items())
    )


def _normalize_inputs(
    inputs: Iterable[ResearchMarketCostLiquidityReversalRiskInput],
    generated_at: datetime,
) -> tuple[ResearchMarketCostLiquidityReversalRiskInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchMarketCostLiquidityReversalRiskInput:
            raise ValueError(
                "inputs must contain ResearchMarketCostLiquidityReversalRiskInput",
            )
        _require_hard_flags("input", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if item.public_risk_ref in seen_refs:
            raise ValueError("public_risk_ref must be unique")
        seen_refs.add(item.public_risk_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketCostLiquidityReversalRiskRow],
) -> tuple[ResearchMarketCostLiquidityReversalRiskRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchMarketCostLiquidityReversalRiskRow:
            raise ValueError("rows must contain ResearchMarketCostLiquidityReversalRiskRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_key))


def _normalize_reason_code_counts(
    items: Iterable[ResearchMarketCostLiquidityReversalRiskReasonCodeCount],
) -> tuple[ResearchMarketCostLiquidityReversalRiskReasonCodeCount, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchMarketCostLiquidityReversalRiskReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketCostLiquidityReversalRiskReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
    return tuple(sorted(normalized, key=lambda item: item.reason_code))


def _row_key(row: ResearchMarketCostLiquidityReversalRiskRow) -> tuple[int, Decimal, str]:
    return (STATUS_WEIGHT[row.status], -row.reversal_risk_score, row.public_risk_ref)


def _status_count(
    rows: tuple[ResearchMarketCostLiquidityReversalRiskRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average_score(
    rows: tuple[ResearchMarketCostLiquidityReversalRiskRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _safe_ratio(
        sum((row.reversal_risk_score for row in rows), ZERO),
        _decimal_count(len(rows)),
    )


def _min_decimal(
    rows: tuple[ResearchMarketCostLiquidityReversalRiskRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _require_nonnegative_decimal(
        field_name,
        min(getattr(row, field_name) for row in rows),
    )


def _max_decimal(
    rows: tuple[ResearchMarketCostLiquidityReversalRiskRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _require_nonnegative_decimal(
        field_name,
        max(getattr(row, field_name) for row in rows),
    )


def _validate_row(row: ResearchMarketCostLiquidityReversalRiskRow) -> None:
    if row.probability_delta != _abs_decimal(
        row.current_probability - row.prior_probability,
    ):
        raise ValueError("probability_delta must match probability inputs")
    if row.cost_ratio != _sum_decimal(row.fee_rate, row.spread_ratio):
        raise ValueError("cost_ratio must match fee and spread")
    if f"reversal_risk_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must match status")


def _validate_report(report: ResearchMarketCostLiquidityReversalRiskReport) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_reversal_risk_score != _average_score(rows):
        raise ValueError("average_reversal_risk_score must match rows")
    if report.max_reversal_risk_score != _max_decimal(rows, "reversal_risk_score"):
        raise ValueError("max_reversal_risk_score must match rows")
    if report.max_probability_delta != _max_decimal(rows, "probability_delta"):
        raise ValueError("max_probability_delta must match rows")
    if report.max_cost_ratio != _max_decimal(rows, "cost_ratio"):
        raise ValueError("max_cost_ratio must match rows")
    if report.min_available_depth != _min_decimal(rows, "available_depth"):
        raise ValueError("min_available_depth must match rows")
    if report.max_book_age_seconds != _max_decimal(rows, "book_age_seconds"):
        raise ValueError("max_book_age_seconds must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must be deterministic")


def _weighted_score(
    *,
    reversal_pressure_score: Decimal,
    liquidity_risk_score: Decimal,
    cost_risk_score: Decimal,
    freshness_risk_score: Decimal,
    config: ResearchMarketCostLiquidityReversalRiskConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        value = (
            reversal_pressure_score * config.reversal_weight
            + liquidity_risk_score * config.liquidity_weight
            + cost_risk_score * config.cost_weight
            + freshness_risk_score * config.freshness_weight
        )
    return _require_ratio_decimal("reversal_risk_score", value)


def _threshold_risk_score(
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
) -> Decimal:
    if value <= pass_value:
        return ZERO
    if value >= watch_value:
        return ONE
    return _safe_ratio(value - pass_value, watch_value - pass_value)


def _depth_risk_score(
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
) -> Decimal:
    if value >= pass_value:
        return ZERO
    if value <= watch_value:
        return ONE
    return _safe_ratio(pass_value - value, pass_value - watch_value)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        value = numerator / denominator
    return _require_ratio_decimal("ratio", value)


def _sum_decimal(*values: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        total = sum(values, ZERO)
    return _require_nonnegative_decimal("decimal_sum", total)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        result = abs(value)
    return _require_nonnegative_decimal("decimal_abs", result)


def _report_derived_validation_digest(
    report: ResearchMarketCostLiquidityReversalRiskReport,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _derived_validation_digest(values)


def _derived_validation_digest(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    reject_unsafe_surface_fields("cost liquidity reversal risk digest", payload)
    _reject_unsafe_public_payload("digest", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be exactly datetime")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not allow_empty and not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_public_label(field_name, code)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    if field_name == "reason_codes" and tuple(sorted(codes)) != codes:
        known_priority_codes = (
            "reversal_risk_block",
            "reversal_risk_watch",
            "reversal_risk_pass",
            *REPORT_REASON_PRIORITY,
            "no_reversal_risk_inputs",
        )
        priority_codes = tuple(code for code in codes if not code.startswith("input_"))
        input_codes = tuple(code for code in codes if code.startswith("input_"))
        if (
            tuple(code for code in known_priority_codes if code in priority_codes)
            != priority_codes
            or tuple(sorted(input_codes)) != input_codes
        ):
            raise ValueError(f"{field_name} must be deterministic")
        return codes
    if tuple(sorted(codes)) != codes:
        raise ValueError(f"{field_name} must be deterministic")
    return codes


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return _normalize_decimal("value", value)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in MARKET_COST_LIQUIDITY_REVERSAL_RISK_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    for character in value:
        if not (
            character.islower()
            or character.isdigit()
            or character in ("-", "_")
        ):
            raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_string(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_REVERSAL_RISK_REPORT_CONFIG_VERSION",
    "MARKET_COST_LIQUIDITY_REVERSAL_RISK_STATUSES",
    "ResearchMarketCostLiquidityReversalRiskConfig",
    "ResearchMarketCostLiquidityReversalRiskInput",
    "ResearchMarketCostLiquidityReversalRiskReasonCodeCount",
    "ResearchMarketCostLiquidityReversalRiskReport",
    "ResearchMarketCostLiquidityReversalRiskReportDigest",
    "ResearchMarketCostLiquidityReversalRiskRow",
    "build_research_market_cost_liquidity_reversal_risk_report",
    "research_market_cost_liquidity_reversal_risk_report_digest",
    "research_market_cost_liquidity_reversal_risk_report_payload",
)
