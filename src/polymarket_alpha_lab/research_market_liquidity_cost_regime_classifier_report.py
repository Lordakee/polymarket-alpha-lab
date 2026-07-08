"""Report-only liquidity and cost regime classifier for sanitized research groups."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from types import MappingProxyType
from typing import Any


CONFIG_VERSION = "research-market-liquidity-cost-regime-classifier-report-v0"
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
LIQUIDITY_COST_REGIME_CLASSIFIER_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

REGIME_PASS = "pass_liquid_low_cost"
REGIME_WATCH = "watch_cost_pressure"
REGIME_BLOCK = "block_cost_friction"
REGIMES = (REGIME_PASS, REGIME_WATCH, REGIME_BLOCK)

REASON_NO_INPUTS = "no_liquidity_cost_inputs"
REASON_PASS = "liquidity_cost_regime_pass"
REASON_WATCH = "liquidity_cost_regime_watch"
REASON_BLOCK = "liquidity_cost_regime_block"

_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "auth",
    "candidate",
    "credential",
    "dsn",
    "live",
    "market_id",
    "market_slug",
    "mnemonic",
    "private",
    "question",
    "recommendation",
    "secret",
    "sizing",
    "slug",
    "source_text",
    "source_url",
    "table",
    "text",
    "token",
    "trade",
    "url",
    "wallet",
)


__all__ = (
    "CONFIG_VERSION",
    "LIQUIDITY_COST_REGIME_CLASSIFIER_STATUSES",
    "ResearchMarketLiquidityCostRegimeClassifierConfig",
    "ResearchMarketLiquidityCostRegimeClassifierInput",
    "ResearchMarketLiquidityCostRegimeClassifierRow",
    "ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount",
    "ResearchMarketLiquidityCostRegimeClassifierReport",
    "build_research_market_liquidity_cost_regime_classifier_report",
    "research_market_liquidity_cost_regime_classifier_public_payload",
)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostRegimeClassifierConfig:
    config_version: str = CONFIG_VERSION
    min_pass_depth_score: Decimal = Decimal("0.750000")
    min_watch_depth_score: Decimal = Decimal("0.500000")
    max_pass_spread_rate: Decimal = Decimal("0.020000")
    max_watch_spread_rate: Decimal = Decimal("0.050000")
    max_pass_fee_drag_rate: Decimal = Decimal("0.010000")
    max_watch_fee_drag_rate: Decimal = Decimal("0.030000")
    max_pass_slippage_pressure_rate: Decimal = Decimal("0.015000")
    max_watch_slippage_pressure_rate: Decimal = Decimal("0.040000")
    max_pass_settlement_friction_rate: Decimal = Decimal("0.005000")
    max_watch_settlement_friction_rate: Decimal = Decimal("0.020000")
    max_pass_total_cost_rate: Decimal = Decimal("0.030000")
    max_watch_total_cost_rate: Decimal = Decimal("0.080000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostRegimeClassifierConfig:
            raise TypeError(
                "ResearchMarketLiquidityCostRegimeClassifierConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityCostRegimeClassifierConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_depth_score",
            "min_watch_depth_score",
            "max_pass_spread_rate",
            "max_watch_spread_rate",
            "max_pass_fee_drag_rate",
            "max_watch_fee_drag_rate",
            "max_pass_slippage_pressure_rate",
            "max_watch_slippage_pressure_rate",
            "max_pass_settlement_friction_rate",
            "max_watch_settlement_friction_rate",
            "max_pass_total_cost_rate",
            "max_watch_total_cost_rate",
        ):
            object.__setattr__(self, field_name, _rate(field_name, getattr(self, field_name)))
        if self.min_watch_depth_score > self.min_pass_depth_score:
            raise ValueError("watch depth threshold must not exceed pass depth threshold")
        _require_max_threshold_pair(
            "pass spread threshold",
            self.max_pass_spread_rate,
            self.max_watch_spread_rate,
        )
        _require_max_threshold_pair(
            "pass fee drag threshold",
            self.max_pass_fee_drag_rate,
            self.max_watch_fee_drag_rate,
        )
        _require_max_threshold_pair(
            "pass slippage pressure threshold",
            self.max_pass_slippage_pressure_rate,
            self.max_watch_slippage_pressure_rate,
        )
        _require_max_threshold_pair(
            "pass settlement friction threshold",
            self.max_pass_settlement_friction_rate,
            self.max_watch_settlement_friction_rate,
        )
        _require_max_threshold_pair(
            "pass total cost threshold",
            self.max_pass_total_cost_rate,
            self.max_watch_total_cost_rate,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostRegimeClassifierInput:
    sanitized_event_group: str
    domain: str
    depth_score: Decimal
    spread_rate: Decimal
    fee_drag_rate: Decimal
    slippage_pressure_rate: Decimal
    settlement_friction_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostRegimeClassifierInput:
            raise TypeError(
                "ResearchMarketLiquidityCostRegimeClassifierInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityCostRegimeClassifierInput, "input")
        for field_name in ("sanitized_event_group", "domain"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "depth_score",
            "spread_rate",
            "fee_drag_rate",
            "slippage_pressure_rate",
            "settlement_friction_rate",
        ):
            object.__setattr__(self, field_name, _rate(field_name, getattr(self, field_name)))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostRegimeClassifierRow:
    sanitized_event_group: str
    domain: str
    depth_score: Decimal
    spread_rate: Decimal
    effective_spread_cost_rate: Decimal
    fee_drag_rate: Decimal
    slippage_pressure_rate: Decimal
    settlement_friction_rate: Decimal
    total_cost_rate: Decimal
    depth_status: str
    spread_status: str
    fee_drag_status: str
    slippage_pressure_status: str
    settlement_friction_status: str
    total_cost_status: str
    liquidity_cost_regime: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostRegimeClassifierRow:
            raise TypeError(
                "ResearchMarketLiquidityCostRegimeClassifierRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityCostRegimeClassifierRow, "row")
        for field_name in ("sanitized_event_group", "domain"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "depth_score",
            "spread_rate",
            "effective_spread_cost_rate",
            "fee_drag_rate",
            "slippage_pressure_rate",
            "settlement_friction_rate",
            "total_cost_rate",
        ):
            object.__setattr__(self, field_name, _rate(field_name, getattr(self, field_name)))
        for field_name in (
            "depth_status",
            "spread_status",
            "fee_drag_status",
            "slippage_pressure_status",
            "settlement_friction_status",
            "total_cost_status",
            "status",
        ):
            _require_status(field_name, getattr(self, field_name))
        _require_regime("liquidity_cost_regime", self.liquidity_cost_regime)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount:
            raise TypeError(
                "ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _whole_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _rate("row_ratio", self.row_ratio))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostRegimeClassifierReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    depth_pressure_count: Decimal
    wide_spread_count: Decimal
    high_fee_drag_count: Decimal
    slippage_pressure_count: Decimal
    settlement_friction_count: Decimal
    high_total_cost_count: Decimal
    max_total_cost_rate: Decimal
    average_total_cost_rate: Decimal
    status: str
    rows: tuple[ResearchMarketLiquidityCostRegimeClassifierRow, ...]
    reason_code_counts: tuple[ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    min_pass_depth_score: Decimal
    min_watch_depth_score: Decimal
    max_pass_spread_rate: Decimal
    max_watch_spread_rate: Decimal
    max_pass_fee_drag_rate: Decimal
    max_watch_fee_drag_rate: Decimal
    max_pass_slippage_pressure_rate: Decimal
    max_watch_slippage_pressure_rate: Decimal
    max_pass_settlement_friction_rate: Decimal
    max_watch_settlement_friction_rate: Decimal
    max_pass_total_cost_rate: Decimal
    max_watch_total_cost_rate: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketLiquidityCostRegimeClassifierReport:
            raise TypeError(
                "ResearchMarketLiquidityCostRegimeClassifierReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityCostRegimeClassifierReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "depth_pressure_count",
            "wide_spread_count",
            "high_fee_drag_count",
            "slippage_pressure_count",
            "settlement_friction_count",
            "high_total_cost_count",
        ):
            object.__setattr__(self, field_name, _whole_decimal(field_name, getattr(self, field_name)))
        for field_name in (
            "max_total_cost_rate",
            "average_total_cost_rate",
            "min_pass_depth_score",
            "min_watch_depth_score",
            "max_pass_spread_rate",
            "max_watch_spread_rate",
            "max_pass_fee_drag_rate",
            "max_watch_fee_drag_rate",
            "max_pass_slippage_pressure_rate",
            "max_watch_slippage_pressure_rate",
            "max_pass_settlement_friction_rate",
            "max_watch_settlement_friction_rate",
            "max_pass_total_cost_rate",
            "max_watch_total_cost_rate",
        ):
            object.__setattr__(self, field_name, _rate(field_name, getattr(self, field_name)))
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
        expected_digest = _public_payload_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match public payload")
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_payload(
            "liquidity cost regime classifier report",
            _public_payload_dict(self),
            allow_json_containers=True,
        )

    @property
    def public_payload(self) -> MappingProxyType:
        return research_market_liquidity_cost_regime_classifier_public_payload(self)


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


def build_research_market_liquidity_cost_regime_classifier_report(
    items: Iterable[object],
    *,
    config: ResearchMarketLiquidityCostRegimeClassifierConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityCostRegimeClassifierReport:
    if type(config) is not ResearchMarketLiquidityCostRegimeClassifierConfig:
        raise ValueError(
            "config must be a ResearchMarketLiquidityCostRegimeClassifierConfig",
        )
    _require_hard_flags("config", config)
    rows = tuple(sorted((_row_from_input(item, config=config) for item in _normalize_inputs(items)), key=_row_sort_key))
    input_count = _decimal_count(len(rows))
    if not rows:
        reason_code_counts = (
            ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount(
                reason_code=REASON_NO_INPUTS,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    else:
        reason_code_counts = _reason_code_counts(rows)
    return ResearchMarketLiquidityCostRegimeClassifierReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_count=input_count,
        pass_count=_decimal_count(_status_count(rows, STATUS_PASS)),
        watch_count=_decimal_count(_status_count(rows, STATUS_WATCH)),
        block_count=_decimal_count(_status_count(rows, STATUS_BLOCK)),
        depth_pressure_count=_decimal_count(
            sum(1 for row in rows if row.depth_status != STATUS_PASS),
        ),
        wide_spread_count=_decimal_count(
            sum(1 for row in rows if row.spread_status != STATUS_PASS),
        ),
        high_fee_drag_count=_decimal_count(
            sum(1 for row in rows if row.fee_drag_status != STATUS_PASS),
        ),
        slippage_pressure_count=_decimal_count(
            sum(1 for row in rows if row.slippage_pressure_status != STATUS_PASS),
        ),
        settlement_friction_count=_decimal_count(
            sum(1 for row in rows if row.settlement_friction_status != STATUS_PASS),
        ),
        high_total_cost_count=_decimal_count(
            sum(1 for row in rows if row.total_cost_status != STATUS_PASS),
        ),
        max_total_cost_rate=_maximum((row.total_cost_rate for row in rows), ZERO),
        average_total_cost_rate=_average((row.total_cost_rate for row in rows), ZERO),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=tuple(item.reason_code for item in reason_code_counts),
        min_pass_depth_score=config.min_pass_depth_score,
        min_watch_depth_score=config.min_watch_depth_score,
        max_pass_spread_rate=config.max_pass_spread_rate,
        max_watch_spread_rate=config.max_watch_spread_rate,
        max_pass_fee_drag_rate=config.max_pass_fee_drag_rate,
        max_watch_fee_drag_rate=config.max_watch_fee_drag_rate,
        max_pass_slippage_pressure_rate=config.max_pass_slippage_pressure_rate,
        max_watch_slippage_pressure_rate=config.max_watch_slippage_pressure_rate,
        max_pass_settlement_friction_rate=config.max_pass_settlement_friction_rate,
        max_watch_settlement_friction_rate=config.max_watch_settlement_friction_rate,
        max_pass_total_cost_rate=config.max_pass_total_cost_rate,
        max_watch_total_cost_rate=config.max_watch_total_cost_rate,
    )


def research_market_liquidity_cost_regime_classifier_public_payload(
    report: ResearchMarketLiquidityCostRegimeClassifierReport | dict[str, Any],
) -> MappingProxyType:
    if type(report) is ResearchMarketLiquidityCostRegimeClassifierReport:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        if report.derived_validation_digest != _public_payload_digest(report):
            raise ValueError("derived_validation_digest does not match public payload")
        payload = _public_payload_dict(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketLiquidityCostRegimeClassifierReport",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload(
        "liquidity cost regime classifier public payload",
        payload,
        allow_json_containers=True,
    )
    _validate_public_payload_digest(payload)
    return MappingProxyType(payload)


def _row_from_input(
    item: ResearchMarketLiquidityCostRegimeClassifierInput,
    *,
    config: ResearchMarketLiquidityCostRegimeClassifierConfig,
) -> ResearchMarketLiquidityCostRegimeClassifierRow:
    effective_spread_cost_rate = _quantize(item.spread_rate / TWO)
    total_cost_rate = _quantize(
        effective_spread_cost_rate
        + item.fee_drag_rate
        + item.slippage_pressure_rate
        + item.settlement_friction_rate,
    )
    depth_status = _depth_status(item.depth_score, config)
    spread_status = _maximum_status(
        item.spread_rate,
        config.max_pass_spread_rate,
        config.max_watch_spread_rate,
    )
    fee_drag_status = _maximum_status(
        item.fee_drag_rate,
        config.max_pass_fee_drag_rate,
        config.max_watch_fee_drag_rate,
    )
    slippage_pressure_status = _maximum_status(
        item.slippage_pressure_rate,
        config.max_pass_slippage_pressure_rate,
        config.max_watch_slippage_pressure_rate,
    )
    settlement_friction_status = _maximum_status(
        item.settlement_friction_rate,
        config.max_pass_settlement_friction_rate,
        config.max_watch_settlement_friction_rate,
    )
    total_cost_status = _maximum_status(
        total_cost_rate,
        config.max_pass_total_cost_rate,
        config.max_watch_total_cost_rate,
    )
    status = _combined_status(
        (
            depth_status,
            spread_status,
            fee_drag_status,
            slippage_pressure_status,
            settlement_friction_status,
            total_cost_status,
        ),
    )
    return ResearchMarketLiquidityCostRegimeClassifierRow(
        sanitized_event_group=item.sanitized_event_group,
        domain=item.domain,
        depth_score=item.depth_score,
        spread_rate=item.spread_rate,
        effective_spread_cost_rate=effective_spread_cost_rate,
        fee_drag_rate=item.fee_drag_rate,
        slippage_pressure_rate=item.slippage_pressure_rate,
        settlement_friction_rate=item.settlement_friction_rate,
        total_cost_rate=total_cost_rate,
        depth_status=depth_status,
        spread_status=spread_status,
        fee_drag_status=fee_drag_status,
        slippage_pressure_status=slippage_pressure_status,
        settlement_friction_status=settlement_friction_status,
        total_cost_status=total_cost_status,
        liquidity_cost_regime=_regime(status),
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            depth_status=depth_status,
            spread_status=spread_status,
            fee_drag_status=fee_drag_status,
            slippage_pressure_status=slippage_pressure_status,
            settlement_friction_status=settlement_friction_status,
            total_cost_status=total_cost_status,
        ),
    )


def _depth_status(
    depth_score: Decimal,
    config: ResearchMarketLiquidityCostRegimeClassifierConfig,
) -> str:
    if depth_score >= config.min_pass_depth_score:
        return STATUS_PASS
    if depth_score >= config.min_watch_depth_score:
        return STATUS_WATCH
    return STATUS_BLOCK


def _maximum_status(value: Decimal, pass_threshold: Decimal, watch_threshold: Decimal) -> str:
    if value <= pass_threshold:
        return STATUS_PASS
    if value <= watch_threshold:
        return STATUS_WATCH
    return STATUS_BLOCK


def _combined_status(component_statuses: tuple[str, ...]) -> str:
    if STATUS_BLOCK in component_statuses:
        return STATUS_BLOCK
    if STATUS_WATCH in component_statuses:
        return STATUS_WATCH
    return STATUS_PASS


def _regime(status: str) -> str:
    if status == STATUS_BLOCK:
        return REGIME_BLOCK
    if status == STATUS_WATCH:
        return REGIME_WATCH
    return REGIME_PASS


def _row_reason_codes(
    *,
    status: str,
    depth_status: str,
    spread_status: str,
    fee_drag_status: str,
    slippage_pressure_status: str,
    settlement_friction_status: str,
    total_cost_status: str,
) -> tuple[str, ...]:
    if status == STATUS_PASS:
        return (REASON_PASS,)
    codes = [_status_reason_code(status)]
    for component, component_status in (
        ("depth", depth_status),
        ("spread", spread_status),
        ("fee_drag", fee_drag_status),
        ("slippage_pressure", slippage_pressure_status),
        ("settlement_friction", settlement_friction_status),
        ("total_cost", total_cost_status),
    ):
        if component_status != STATUS_PASS:
            codes.append(f"{component}_{component_status}")
    return tuple(sorted(codes))


def _status_reason_code(status: str) -> str:
    if status == STATUS_BLOCK:
        return REASON_BLOCK
    if status == STATUS_WATCH:
        return REASON_WATCH
    return REASON_PASS


def _normalize_inputs(
    items: Iterable[object],
) -> tuple[ResearchMarketLiquidityCostRegimeClassifierInput, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable")
    try:
        values = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchMarketLiquidityCostRegimeClassifierInput:
    if type(value) is ResearchMarketLiquidityCostRegimeClassifierInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchMarketLiquidityCostRegimeClassifierInput(
        sanitized_event_group=_field_value(value, "sanitized_event_group"),
        domain=_field_value(value, "domain"),
        depth_score=_field_value(value, "depth_score"),
        spread_rate=_field_value(value, "spread_rate"),
        fee_drag_rate=_field_value(value, "fee_drag_rate"),
        slippage_pressure_rate=_field_value(value, "slippage_pressure_rate"),
        settlement_friction_rate=_field_value(value, "settlement_friction_rate"),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _field_value(value: object, field_name: str) -> object:
    if type(value) is dict:
        if field_name not in value:
            raise ValueError(f"{field_name} is required")
        return value[field_name]
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _row_sort_key(
    row: ResearchMarketLiquidityCostRegimeClassifierRow,
) -> tuple[str, str, str]:
    return (row.sanitized_event_group, row.domain, row.status)


def _status_count(
    rows: tuple[ResearchMarketLiquidityCostRegimeClassifierRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _report_status(rows: tuple[ResearchMarketLiquidityCostRegimeClassifierRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquidityCostRegimeClassifierRow, ...],
) -> tuple[ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount(
                reason_code=REASON_NO_INPUTS,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = Decimal(len(rows))
    return tuple(
        ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
            row_ratio=_quantize(Decimal(counter[reason_code]) / row_count),
        )
        for reason_code in sorted(counter)
    )


def _normalize_rows(
    value: object,
) -> tuple[ResearchMarketLiquidityCostRegimeClassifierRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    if not all(type(row) is ResearchMarketLiquidityCostRegimeClassifierRow for row in rows):
        raise ValueError(
            "rows must contain ResearchMarketLiquidityCostRegimeClassifierRow values",
        )
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    counts = tuple(value)
    if not all(
        type(item) is ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount
        for item in counts
    ):
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount values",
        )
    if counts != tuple(sorted(counts, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must be sorted")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    codes = tuple(value)
    if not allow_empty and not codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    for code in codes:
        _require_public_string(field_name, code)
    normalized = tuple(sorted(codes))
    if normalized != codes:
        raise ValueError(f"{field_name} must be sorted")
    return normalized


def _validate_row_consistency(row: ResearchMarketLiquidityCostRegimeClassifierRow) -> None:
    if row.effective_spread_cost_rate != _quantize(row.spread_rate / TWO):
        raise ValueError("effective_spread_cost_rate does not match spread_rate")
    expected_total_cost_rate = _quantize(
        row.effective_spread_cost_rate
        + row.fee_drag_rate
        + row.slippage_pressure_rate
        + row.settlement_friction_rate,
    )
    if row.total_cost_rate != expected_total_cost_rate:
        raise ValueError("total_cost_rate does not match cost components")
    if row.status != _combined_status(
        (
            row.depth_status,
            row.spread_status,
            row.fee_drag_status,
            row.slippage_pressure_status,
            row.settlement_friction_status,
            row.total_cost_status,
        ),
    ):
        raise ValueError("status does not match component statuses")
    if row.liquidity_cost_regime != _regime(row.status):
        raise ValueError("liquidity_cost_regime does not match status")
    if row.reason_codes != _row_reason_codes(
        status=row.status,
        depth_status=row.depth_status,
        spread_status=row.spread_status,
        fee_drag_status=row.fee_drag_status,
        slippage_pressure_status=row.slippage_pressure_status,
        settlement_friction_status=row.settlement_friction_status,
        total_cost_status=row.total_cost_status,
    ):
        raise ValueError("reason_codes do not match component statuses")


def _validate_report_consistency(
    report: ResearchMarketLiquidityCostRegimeClassifierReport,
) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count does not match rows")
    if report.pass_count != _decimal_count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _decimal_count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _decimal_count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count does not match rows")
    if report.depth_pressure_count != _decimal_count(
        sum(1 for row in rows if row.depth_status != STATUS_PASS),
    ):
        raise ValueError("depth_pressure_count does not match rows")
    if report.wide_spread_count != _decimal_count(
        sum(1 for row in rows if row.spread_status != STATUS_PASS),
    ):
        raise ValueError("wide_spread_count does not match rows")
    if report.high_fee_drag_count != _decimal_count(
        sum(1 for row in rows if row.fee_drag_status != STATUS_PASS),
    ):
        raise ValueError("high_fee_drag_count does not match rows")
    if report.slippage_pressure_count != _decimal_count(
        sum(1 for row in rows if row.slippage_pressure_status != STATUS_PASS),
    ):
        raise ValueError("slippage_pressure_count does not match rows")
    if report.settlement_friction_count != _decimal_count(
        sum(1 for row in rows if row.settlement_friction_status != STATUS_PASS),
    ):
        raise ValueError("settlement_friction_count does not match rows")
    if report.high_total_cost_count != _decimal_count(
        sum(1 for row in rows if row.total_cost_status != STATUS_PASS),
    ):
        raise ValueError("high_total_cost_count does not match rows")
    if report.max_total_cost_rate != _maximum((row.total_cost_rate for row in rows), ZERO):
        raise ValueError("max_total_cost_rate does not match rows")
    if report.average_total_cost_rate != _average(
        (row.total_cost_rate for row in rows),
        ZERO,
    ):
        raise ValueError("average_total_cost_rate does not match rows")
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")
    expected_counts = _reason_code_counts(rows)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes do not match reason_code_counts")


def _public_payload_digest(report: ResearchMarketLiquidityCostRegimeClassifierReport) -> str:
    payload = _public_payload_dict(report, include_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _public_payload_dict(
    report: ResearchMarketLiquidityCostRegimeClassifierReport,
    *,
    include_digest: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in fields(report):
        if field.name == "derived_validation_digest" and not include_digest:
            continue
        payload[field.name] = _json_ready(getattr(report, field.name))
    return payload


def _validate_public_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest is required")
    _require_sha256_digest("derived_validation_digest", digest)
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


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
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


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
        _require_safe_public_text(current_path, value)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
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
            _require_safe_public_text(item_path, key)
            if key in _FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=True,
            )
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    raise ValueError(f"{current_path} is not JSON serializable")


def _require_safe_public_text(field_name: str, value: str) -> None:
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} has unsafe value")
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} has unsafe value")
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe value")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _require_safe_public_text(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if value not in LIQUIDITY_COST_REGIME_CLASSIFIER_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_regime(field_name: str, value: object) -> None:
    if value not in REGIMES:
        raise ValueError(f"{field_name} is not supported")


def _require_max_threshold_pair(label: str, pass_threshold: Decimal, watch_threshold: Decimal) -> None:
    if pass_threshold > watch_threshold:
        raise ValueError(f"{label} must not exceed watch threshold")


def _rate(field_name: str, value: object) -> Decimal:
    normalized = _decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return normalized


def _whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _maximum(values: Iterable[Decimal], default: Decimal) -> Decimal:
    items = tuple(values)
    if not items:
        return default
    return _quantize(max(items))


def _average(values: Iterable[Decimal], default: Decimal) -> Decimal:
    items = tuple(values)
    if not items:
        return default
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label}.{field_name} is required")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
