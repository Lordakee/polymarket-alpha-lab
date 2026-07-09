"""Report-only spread and volatility breakpoint review."""

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
    "SPREAD_VOLATILITY_BREAKPOINT_STATUSES",
    "DEFAULT_RESEARCH_MARKET_SPREAD_VOLATILITY_BREAKPOINT_REPORT_CONFIG_VERSION",
    "ResearchMarketSpreadVolatilityBreakpointConfig",
    "ResearchMarketSpreadVolatilityBreakpointInput",
    "ResearchMarketSpreadVolatilityBreakpointReasonCodeCount",
    "ResearchMarketSpreadVolatilityBreakpointReport",
    "ResearchMarketSpreadVolatilityBreakpointRow",
    "build_research_market_spread_volatility_breakpoint_report",
    "research_market_spread_volatility_breakpoint_report_digest",
    "research_market_spread_volatility_breakpoint_report_payload",
)


DEFAULT_RESEARCH_MARKET_SPREAD_VOLATILITY_BREAKPOINT_REPORT_CONFIG_VERSION = (
    "research-market-spread-volatility-breakpoint-report-v0"
)
SPREAD_VOLATILITY_BREAKPOINT_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT_PRECISION = 28
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
REPORT_REASON_PRIORITY = (
    "spread_width_block",
    "volatility_breakpoint_block",
    "thin_depth_block",
    "book_age_block",
    "fee_drag_block",
    "slippage_cushion_block",
    "spread_width_watch",
    "volatility_breakpoint_watch",
    "thin_depth_watch",
    "book_age_watch",
    "fee_drag_watch",
    "slippage_cushion_watch",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate"),
    _join_parts("condition", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "-", "sl", "ug"),
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
    _join_parts("pos", "ition"),
    _join_parts("siz", "ing"),
    _join_parts("reco", "mmend"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
    "://",
)


@dataclass(frozen=True)
class ResearchMarketSpreadVolatilityBreakpointConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_SPREAD_VOLATILITY_BREAKPOINT_REPORT_CONFIG_VERSION
    )
    maximum_pass_spread_width_ratio: Decimal = Decimal("0.020000")
    maximum_watch_spread_width_ratio: Decimal = Decimal("0.080000")
    maximum_pass_volatility_ratio: Decimal = Decimal("0.050000")
    maximum_watch_volatility_ratio: Decimal = Decimal("0.150000")
    minimum_pass_depth_ratio: Decimal = Decimal("0.750000")
    minimum_watch_depth_ratio: Decimal = Decimal("0.350000")
    maximum_pass_book_age_seconds: Decimal = Decimal("90.000000")
    maximum_watch_book_age_seconds: Decimal = Decimal("600.000000")
    maximum_pass_fee_drag_ratio: Decimal = Decimal("0.010000")
    maximum_watch_fee_drag_ratio: Decimal = Decimal("0.040000")
    minimum_pass_slippage_cushion_ratio: Decimal = Decimal("0.040000")
    minimum_watch_slippage_cushion_ratio: Decimal = Decimal("0.010000")
    spread_width_weight: Decimal = Decimal("0.200000")
    volatility_weight: Decimal = Decimal("0.250000")
    depth_weight: Decimal = Decimal("0.150000")
    book_age_weight: Decimal = Decimal("0.100000")
    fee_drag_weight: Decimal = Decimal("0.150000")
    slippage_cushion_weight: Decimal = Decimal("0.150000")
    maximum_pass_noise_score: Decimal = Decimal("0.250000")
    maximum_watch_noise_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSpreadVolatilityBreakpointConfig:
            raise TypeError(
                "ResearchMarketSpreadVolatilityBreakpointConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSpreadVolatilityBreakpointConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_SPREAD_VOLATILITY_BREAKPOINT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "maximum_pass_spread_width_ratio",
            "maximum_watch_spread_width_ratio",
            "maximum_pass_volatility_ratio",
            "maximum_watch_volatility_ratio",
            "minimum_pass_depth_ratio",
            "minimum_watch_depth_ratio",
            "maximum_pass_fee_drag_ratio",
            "maximum_watch_fee_drag_ratio",
            "minimum_pass_slippage_cushion_ratio",
            "minimum_watch_slippage_cushion_ratio",
            "spread_width_weight",
            "volatility_weight",
            "depth_weight",
            "book_age_weight",
            "fee_drag_weight",
            "slippage_cushion_weight",
            "maximum_pass_noise_score",
            "maximum_watch_noise_score",
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
        if self.maximum_pass_spread_width_ratio >= self.maximum_watch_spread_width_ratio:
            raise ValueError("maximum_pass_spread_width_ratio must be below watch")
        if self.maximum_pass_volatility_ratio >= self.maximum_watch_volatility_ratio:
            raise ValueError("maximum_pass_volatility_ratio must be below watch")
        if self.minimum_pass_depth_ratio <= self.minimum_watch_depth_ratio:
            raise ValueError("minimum_pass_depth_ratio must exceed watch")
        if self.maximum_pass_book_age_seconds >= self.maximum_watch_book_age_seconds:
            raise ValueError("maximum_pass_book_age_seconds must be below watch")
        if self.maximum_pass_fee_drag_ratio >= self.maximum_watch_fee_drag_ratio:
            raise ValueError("maximum_pass_fee_drag_ratio must be below watch")
        if (
            self.minimum_pass_slippage_cushion_ratio
            <= self.minimum_watch_slippage_cushion_ratio
        ):
            raise ValueError("minimum_pass_slippage_cushion_ratio must exceed watch")
        if self.maximum_pass_noise_score >= self.maximum_watch_noise_score:
            raise ValueError("maximum_pass_noise_score must be below watch")
        weight_sum = _quantize(
            self.spread_width_weight
            + self.volatility_weight
            + self.depth_weight
            + self.book_age_weight
            + self.fee_drag_weight
            + self.slippage_cushion_weight,
        )
        if weight_sum != ONE:
            raise ValueError("spread_width_weight values must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketSpreadVolatilityBreakpointInput:
    public_breakpoint_ref: str
    observed_at: datetime
    spread_width_ratio: Decimal
    volatility_ratio: Decimal
    depth_ratio: Decimal
    book_age_seconds: Decimal
    fee_drag_ratio: Decimal
    slippage_cushion_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSpreadVolatilityBreakpointInput:
            raise TypeError(
                "ResearchMarketSpreadVolatilityBreakpointInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadVolatilityBreakpointInput, "input")
        _require_public_label("public_breakpoint_ref", self.public_breakpoint_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_width_ratio",
            "volatility_ratio",
            "depth_ratio",
            "fee_drag_ratio",
            "slippage_cushion_ratio",
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
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchMarketSpreadVolatilityBreakpointRow:
    public_breakpoint_ref: str
    observed_at: datetime
    spread_width_ratio: Decimal
    spread_width_pressure_score: Decimal
    volatility_ratio: Decimal
    volatility_pressure_score: Decimal
    depth_ratio: Decimal
    depth_pressure_score: Decimal
    book_age_seconds: Decimal
    book_age_pressure_score: Decimal
    fee_drag_ratio: Decimal
    fee_drag_pressure_score: Decimal
    slippage_cushion_ratio: Decimal
    slippage_cushion_pressure_score: Decimal
    noise_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSpreadVolatilityBreakpointRow:
            raise TypeError(
                "ResearchMarketSpreadVolatilityBreakpointRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadVolatilityBreakpointRow, "row")
        _require_public_label("public_breakpoint_ref", self.public_breakpoint_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_width_ratio",
            "spread_width_pressure_score",
            "volatility_ratio",
            "volatility_pressure_score",
            "depth_ratio",
            "depth_pressure_score",
            "fee_drag_ratio",
            "fee_drag_pressure_score",
            "slippage_cushion_ratio",
            "slippage_cushion_pressure_score",
            "noise_score",
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
            "book_age_pressure_score",
            _require_ratio_decimal(
                "book_age_pressure_score",
                self.book_age_pressure_score,
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
                sort_values=False,
            ),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketSpreadVolatilityBreakpointReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSpreadVolatilityBreakpointReasonCodeCount:
            raise TypeError(
                "ResearchMarketSpreadVolatilityBreakpointReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSpreadVolatilityBreakpointReasonCodeCount,
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
class ResearchMarketSpreadVolatilityBreakpointReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    breakpoint_count: Decimal
    average_noise_score: Decimal | None
    max_noise_score: Decimal
    max_spread_width_ratio: Decimal
    max_volatility_ratio: Decimal
    min_depth_ratio: Decimal
    max_book_age_seconds: Decimal
    max_fee_drag_ratio: Decimal
    min_slippage_cushion_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketSpreadVolatilityBreakpointReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchMarketSpreadVolatilityBreakpointRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSpreadVolatilityBreakpointReport:
            raise TypeError(
                "ResearchMarketSpreadVolatilityBreakpointReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadVolatilityBreakpointReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "breakpoint_count",
            "max_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_noise_score",
            "max_spread_width_ratio",
            "max_volatility_ratio",
            "min_depth_ratio",
            "max_fee_drag_ratio",
            "min_slippage_cushion_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_noise_score is not None:
            object.__setattr__(
                self,
                "average_noise_score",
                _require_ratio_decimal("average_noise_score", self.average_noise_score),
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
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report(self)
        if self.derived_validation_digest != _report_derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_spread_volatility_breakpoint_report_payload(self)


@dataclass(frozen=True)
class ResearchMarketSpreadVolatilityBreakpointReportDigest:
    generated_at: datetime
    config_version: str
    report_digest: str
    report_status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    breakpoint_count: Decimal
    average_noise_score: Decimal | None
    max_noise_score: Decimal
    max_spread_width_ratio: Decimal
    max_volatility_ratio: Decimal
    min_depth_ratio: Decimal
    max_book_age_seconds: Decimal
    max_fee_drag_ratio: Decimal
    min_slippage_cushion_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSpreadVolatilityBreakpointReportDigest:
            raise TypeError(
                "ResearchMarketSpreadVolatilityBreakpointReportDigest does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSpreadVolatilityBreakpointReportDigest,
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
            "breakpoint_count",
            "max_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_noise_score",
            "max_spread_width_ratio",
            "max_volatility_ratio",
            "min_depth_ratio",
            "max_fee_drag_ratio",
            "min_slippage_cushion_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_noise_score is not None:
            object.__setattr__(
                self,
                "average_noise_score",
                _require_ratio_decimal("average_noise_score", self.average_noise_score),
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
        _require_hard_flags("digest", self)
        _reject_unsafe_public_payload("digest", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_spread_volatility_breakpoint_report_payload(self)


def build_research_market_spread_volatility_breakpoint_report(
    inputs: Iterable[ResearchMarketSpreadVolatilityBreakpointInput],
    *,
    config: ResearchMarketSpreadVolatilityBreakpointConfig,
    generated_at: datetime,
) -> ResearchMarketSpreadVolatilityBreakpointReport:
    if type(config) is not ResearchMarketSpreadVolatilityBreakpointConfig:
        raise ValueError(
            "config must be a ResearchMarketSpreadVolatilityBreakpointConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
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
        "breakpoint_count": _decimal_count(
            sum(1 for row in rows if row.status in ("watch", "block")),
        ),
        "average_noise_score": _average_score(rows),
        "max_noise_score": _max_decimal(rows, "noise_score"),
        "max_spread_width_ratio": _max_decimal(rows, "spread_width_ratio"),
        "max_volatility_ratio": _max_decimal(rows, "volatility_ratio"),
        "min_depth_ratio": _min_decimal(rows, "depth_ratio"),
        "max_book_age_seconds": _max_decimal(rows, "book_age_seconds"),
        "max_fee_drag_ratio": _max_decimal(rows, "fee_drag_ratio"),
        "min_slippage_cushion_ratio": _min_decimal(rows, "slippage_cushion_ratio"),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketSpreadVolatilityBreakpointReport(
        **values,
        derived_validation_digest=_derived_validation_digest(values),
    )


def research_market_spread_volatility_breakpoint_report_payload(
    value: ResearchMarketSpreadVolatilityBreakpointReport
    | ResearchMarketSpreadVolatilityBreakpointReportDigest
    | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchMarketSpreadVolatilityBreakpointReport:
        _require_hard_flags("report", value)
        if value.derived_validation_digest != _report_derived_validation_digest(value):
            raise ValueError("derived_validation_digest must match report payload")
        payload = _json_ready(value)
    elif type(value) is ResearchMarketSpreadVolatilityBreakpointReportDigest:
        _require_hard_flags("digest", value)
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = _json_ready(value)
    else:
        raise ValueError(
            "value must be a ResearchMarketSpreadVolatilityBreakpointReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_market_spread_volatility_breakpoint_report_digest(
    report: ResearchMarketSpreadVolatilityBreakpointReport,
) -> ResearchMarketSpreadVolatilityBreakpointReportDigest:
    if type(report) is not ResearchMarketSpreadVolatilityBreakpointReport:
        raise ValueError(
            "report must be a ResearchMarketSpreadVolatilityBreakpointReport",
        )
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")
    return ResearchMarketSpreadVolatilityBreakpointReportDigest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_digest=report.derived_validation_digest,
        report_status=report.status,
        input_count=report.input_count,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        breakpoint_count=report.breakpoint_count,
        average_noise_score=report.average_noise_score,
        max_noise_score=report.max_noise_score,
        max_spread_width_ratio=report.max_spread_width_ratio,
        max_volatility_ratio=report.max_volatility_ratio,
        min_depth_ratio=report.min_depth_ratio,
        max_book_age_seconds=report.max_book_age_seconds,
        max_fee_drag_ratio=report.max_fee_drag_ratio,
        min_slippage_cushion_ratio=report.min_slippage_cushion_ratio,
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
    item: ResearchMarketSpreadVolatilityBreakpointInput,
    config: ResearchMarketSpreadVolatilityBreakpointConfig,
) -> ResearchMarketSpreadVolatilityBreakpointRow:
    spread_width_pressure_score = _threshold_pressure(
        item.spread_width_ratio,
        config.maximum_watch_spread_width_ratio,
    )
    volatility_pressure_score = _threshold_pressure(
        item.volatility_ratio,
        config.maximum_watch_volatility_ratio,
    )
    depth_pressure_score = _depth_pressure(item.depth_ratio)
    book_age_pressure_score = _threshold_pressure(
        item.book_age_seconds,
        config.maximum_watch_book_age_seconds,
    )
    fee_drag_pressure_score = _threshold_pressure(
        item.fee_drag_ratio,
        config.maximum_watch_fee_drag_ratio,
    )
    slippage_cushion_pressure_score = _cushion_pressure(
        item.slippage_cushion_ratio,
        pass_value=config.minimum_pass_slippage_cushion_ratio,
        watch_value=config.minimum_watch_slippage_cushion_ratio,
    )
    noise_score = _weighted_noise_score(
        spread_width_pressure_score=spread_width_pressure_score,
        volatility_pressure_score=volatility_pressure_score,
        depth_pressure_score=depth_pressure_score,
        book_age_pressure_score=book_age_pressure_score,
        fee_drag_pressure_score=fee_drag_pressure_score,
        slippage_cushion_pressure_score=slippage_cushion_pressure_score,
        config=config,
    )
    component_codes = _component_reason_codes(item=item, config=config)
    status = _row_status(noise_score, component_codes, config)
    return ResearchMarketSpreadVolatilityBreakpointRow(
        public_breakpoint_ref=item.public_breakpoint_ref,
        observed_at=item.observed_at,
        spread_width_ratio=item.spread_width_ratio,
        spread_width_pressure_score=spread_width_pressure_score,
        volatility_ratio=item.volatility_ratio,
        volatility_pressure_score=volatility_pressure_score,
        depth_ratio=item.depth_ratio,
        depth_pressure_score=depth_pressure_score,
        book_age_seconds=item.book_age_seconds,
        book_age_pressure_score=book_age_pressure_score,
        fee_drag_ratio=item.fee_drag_ratio,
        fee_drag_pressure_score=fee_drag_pressure_score,
        slippage_cushion_ratio=item.slippage_cushion_ratio,
        slippage_cushion_pressure_score=slippage_cushion_pressure_score,
        noise_score=noise_score,
        status=status,
        reason_codes=_row_reason_codes(status, component_codes, item.reason_codes),
    )


def _component_reason_codes(
    *,
    item: ResearchMarketSpreadVolatilityBreakpointInput,
    config: ResearchMarketSpreadVolatilityBreakpointConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if item.spread_width_ratio > config.maximum_watch_spread_width_ratio:
        codes.append("spread_width_block")
    elif item.spread_width_ratio > config.maximum_pass_spread_width_ratio:
        codes.append("spread_width_watch")
    if item.volatility_ratio > config.maximum_watch_volatility_ratio:
        codes.append("volatility_breakpoint_block")
    elif item.volatility_ratio > config.maximum_pass_volatility_ratio:
        codes.append("volatility_breakpoint_watch")
    if item.depth_ratio < config.minimum_watch_depth_ratio:
        codes.append("thin_depth_block")
    elif item.depth_ratio < config.minimum_pass_depth_ratio:
        codes.append("thin_depth_watch")
    if item.book_age_seconds > config.maximum_watch_book_age_seconds:
        codes.append("book_age_block")
    elif item.book_age_seconds > config.maximum_pass_book_age_seconds:
        codes.append("book_age_watch")
    if item.fee_drag_ratio > config.maximum_watch_fee_drag_ratio:
        codes.append("fee_drag_block")
    elif item.fee_drag_ratio > config.maximum_pass_fee_drag_ratio:
        codes.append("fee_drag_watch")
    if item.slippage_cushion_ratio < config.minimum_watch_slippage_cushion_ratio:
        codes.append("slippage_cushion_block")
    elif item.slippage_cushion_ratio < config.minimum_pass_slippage_cushion_ratio:
        codes.append("slippage_cushion_watch")
    return tuple(codes)


def _row_status(
    noise_score: Decimal,
    component_codes: tuple[str, ...],
    config: ResearchMarketSpreadVolatilityBreakpointConfig,
) -> str:
    if any(code.endswith("_block") for code in component_codes):
        return "block"
    if noise_score > config.maximum_watch_noise_score:
        return "block"
    if any(code.endswith("_watch") for code in component_codes):
        return "watch"
    if noise_score > config.maximum_pass_noise_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    status: str,
    component_codes: tuple[str, ...],
    input_codes: tuple[str, ...],
) -> tuple[str, ...]:
    codes = tuple(f"input_{code}" for code in input_codes) + (
        f"spread_volatility_breakpoint_{status}",
        *component_codes,
    )
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted(codes)),
        allow_empty=False,
    )


def _report_status(rows: tuple[ResearchMarketSpreadVolatilityBreakpointRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketSpreadVolatilityBreakpointRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_spread_volatility_breakpoint_inputs",)
    status = _report_status(rows)
    codes = [f"spread_volatility_breakpoint_{status}"]
    row_codes = {code for row in rows for code in row.reason_codes}
    codes.extend(code for code in REPORT_REASON_PRIORITY if code in row_codes)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(codes),
        allow_empty=False,
        sort_values=False,
    )


def _reason_code_counts(
    rows: tuple[ResearchMarketSpreadVolatilityBreakpointRow, ...],
) -> tuple[ResearchMarketSpreadVolatilityBreakpointReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketSpreadVolatilityBreakpointReasonCodeCount(
                reason_code="no_spread_volatility_breakpoint_inputs",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts = Counter(code for row in rows for code in row.reason_codes)
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchMarketSpreadVolatilityBreakpointReasonCodeCount(
            reason_code=code,
            count=_decimal_count(count),
            row_ratio=_safe_divide(_decimal_count(count), row_count),
        )
        for code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_inputs(
    inputs: Iterable[ResearchMarketSpreadVolatilityBreakpointInput],
) -> tuple[ResearchMarketSpreadVolatilityBreakpointInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized: list[ResearchMarketSpreadVolatilityBreakpointInput] = []
    seen_refs: set[str] = set()
    for item in inputs:
        if type(item) is not ResearchMarketSpreadVolatilityBreakpointInput:
            raise ValueError(
                "inputs must contain ResearchMarketSpreadVolatilityBreakpointInput values",
            )
        _require_hard_flags("input", item)
        if item.public_breakpoint_ref in seen_refs:
            raise ValueError("duplicate public_breakpoint_ref")
        seen_refs.add(item.public_breakpoint_ref)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.public_breakpoint_ref))


def _normalize_rows(
    rows: tuple[ResearchMarketSpreadVolatilityBreakpointRow, ...],
) -> tuple[ResearchMarketSpreadVolatilityBreakpointRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketSpreadVolatilityBreakpointRow:
            raise ValueError(
                "rows must contain ResearchMarketSpreadVolatilityBreakpointRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must be sorted by status, score, and reference")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketSpreadVolatilityBreakpointReasonCodeCount, ...],
) -> tuple[ResearchMarketSpreadVolatilityBreakpointReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in counts:
        if type(item) is not ResearchMarketSpreadVolatilityBreakpointReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchMarketSpreadVolatilityBreakpointReasonCodeCount values",
            )
        _require_hard_flags("reason code count", item)
    expected = tuple(sorted(counts, key=lambda item: (-item.count, item.reason_code)))
    if counts != expected:
        raise ValueError("reason_code_counts must be sorted")
    return counts


def _row_key(row: ResearchMarketSpreadVolatilityBreakpointRow) -> tuple[int, Decimal, str]:
    severity = {"block": 0, "watch": 1, "pass": 2}[row.status]
    return (severity, -row.noise_score, row.public_breakpoint_ref)


def _status_count(
    rows: tuple[ResearchMarketSpreadVolatilityBreakpointRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average_score(
    rows: tuple[ResearchMarketSpreadVolatilityBreakpointRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _safe_divide(
        sum((row.noise_score for row in rows), ZERO),
        _decimal_count(len(rows)),
    )


def _max_decimal(
    rows: tuple[ResearchMarketSpreadVolatilityBreakpointRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_decimal(
    rows: tuple[ResearchMarketSpreadVolatilityBreakpointRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _weighted_noise_score(
    *,
    spread_width_pressure_score: Decimal,
    volatility_pressure_score: Decimal,
    depth_pressure_score: Decimal,
    book_age_pressure_score: Decimal,
    fee_drag_pressure_score: Decimal,
    slippage_cushion_pressure_score: Decimal,
    config: ResearchMarketSpreadVolatilityBreakpointConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _quantize(
            spread_width_pressure_score * config.spread_width_weight
            + volatility_pressure_score * config.volatility_weight
            + depth_pressure_score * config.depth_weight
            + book_age_pressure_score * config.book_age_weight
            + fee_drag_pressure_score * config.fee_drag_weight
            + slippage_cushion_pressure_score * config.slippage_cushion_weight,
        )


def _threshold_pressure(value: Decimal, watch_value: Decimal) -> Decimal:
    if watch_value <= ZERO:
        raise ValueError("watch_value must be positive")
    return min(_safe_divide(value, watch_value), ONE)


def _depth_pressure(depth_ratio: Decimal) -> Decimal:
    return _quantize(max(ZERO, ONE - depth_ratio))


def _cushion_pressure(
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
) -> Decimal:
    if value >= pass_value:
        return ZERO
    if value <= watch_value:
        return ONE
    return _safe_divide(pass_value - value, pass_value - watch_value)


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _quantize(numerator / denominator)


def _sum_payload_without_digest(value: dict[str, object]) -> dict[str, object]:
    payload = dict(value)
    payload.pop("derived_validation_digest", None)
    return payload


def _derived_validation_digest(values: dict[str, object]) -> str:
    payload = _json_ready(_sum_payload_without_digest(values))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _report_derived_validation_digest(
    report: ResearchMarketSpreadVolatilityBreakpointReport,
) -> str:
    values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    return _derived_validation_digest(values)


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(_quantize(value), "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported JSON value type: {type(value).__name__}")


def _validate_report(report: ResearchMarketSpreadVolatilityBreakpointReport) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    *,
    allow_empty: bool,
    sort_values: bool = True,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or not REASON_CODE_RE.fullmatch(item):
            raise ValueError(f"{field_name} contains invalid reason code")
        _reject_unsafe_text(field_name, item)
        normalized.append(item)
    deduped = tuple(dict.fromkeys(normalized))
    if sort_values:
        return tuple(sorted(deduped))
    return deduped


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in SPREAD_VOLATILITY_BREAKPOINT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_label(field_name: str, value: str) -> None:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_text(field_name, value)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256_digest(field_name: str, value: str) -> None:
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_text(label, field.name)
            _reject_unsafe_public_payload(f"{label}.{field.name}", getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_text(label, str(key))
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload field in {label}")
