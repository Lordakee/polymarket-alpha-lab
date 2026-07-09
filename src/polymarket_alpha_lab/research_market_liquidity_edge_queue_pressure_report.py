"""Report-only queue pressure scoring for sanitized probability-event markets."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_LIQUIDITY_EDGE_QUEUE_PRESSURE_CONFIG_VERSION = (
    "research-market-liquidity-edge-queue-pressure-report-v0"
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_EDGE_QUEUE_PRESSURE_CONFIG_VERSION",
    "ResearchMarketLiquidityEdgeQueuePressureConfig",
    "ResearchMarketLiquidityEdgeQueuePressureInput",
    "ResearchMarketLiquidityEdgeQueuePressureRow",
    "ResearchMarketLiquidityEdgeQueuePressureReport",
    "build_research_market_liquidity_edge_queue_pressure_report",
    "research_market_liquidity_edge_queue_pressure_report_payload",
)


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_STATUSES = frozenset(("pass", "watch", "block"))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "execution",
    "sizing",
    "recommendation",
    "auth",
    "network",
    "database",
    "persist",
    "live",
    "buy",
    "sell",
)
_UNSAFE_PUBLIC_SEGMENTS = frozenset(("db", "text"))
_PUBLIC_SEGMENT_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class ResearchMarketLiquidityEdgeQueuePressureConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_EDGE_QUEUE_PRESSURE_CONFIG_VERSION
    )
    max_pass_queue_pressure: Decimal = Decimal("0.300000")
    max_watch_queue_pressure: Decimal = Decimal("0.600000")
    min_pass_liquidity_depth_ratio: Decimal = Decimal("1.500000")
    min_watch_liquidity_depth_ratio: Decimal = Decimal("0.750000")
    max_pass_bid_ask_spread: Decimal = Decimal("0.015000")
    max_watch_bid_ask_spread: Decimal = Decimal("0.040000")
    max_block_bid_ask_spread: Decimal = Decimal("0.080000")
    max_pass_fee_drag: Decimal = Decimal("0.010000")
    max_watch_fee_drag: Decimal = Decimal("0.025000")
    max_block_fee_drag: Decimal = Decimal("0.040000")
    max_pass_slippage_risk: Decimal = Decimal("0.020000")
    max_watch_slippage_risk: Decimal = Decimal("0.050000")
    max_block_slippage_risk: Decimal = Decimal("0.080000")
    max_pass_settlement_friction: Decimal = Decimal("0.015000")
    max_watch_settlement_friction: Decimal = Decimal("0.040000")
    max_block_settlement_friction: Decimal = Decimal("0.060000")
    min_pass_edge_stability: Decimal = Decimal("0.800000")
    min_watch_edge_stability: Decimal = Decimal("0.500000")
    liquidity_depth_weight: Decimal = Decimal("0.250000")
    spread_weight: Decimal = Decimal("0.200000")
    fee_drag_weight: Decimal = Decimal("0.150000")
    slippage_risk_weight: Decimal = Decimal("0.200000")
    settlement_friction_weight: Decimal = Decimal("0.100000")
    edge_stability_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityEdgeQueuePressureConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_EDGE_QUEUE_PRESSURE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_queue_pressure",
            "max_watch_queue_pressure",
            "max_pass_bid_ask_spread",
            "max_watch_bid_ask_spread",
            "max_block_bid_ask_spread",
            "max_pass_fee_drag",
            "max_watch_fee_drag",
            "max_block_fee_drag",
            "max_pass_slippage_risk",
            "max_watch_slippage_risk",
            "max_block_slippage_risk",
            "max_pass_settlement_friction",
            "max_watch_settlement_friction",
            "max_block_settlement_friction",
            "min_pass_edge_stability",
            "min_watch_edge_stability",
            "liquidity_depth_weight",
            "spread_weight",
            "fee_drag_weight",
            "slippage_risk_weight",
            "settlement_friction_weight",
            "edge_stability_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_liquidity_depth_ratio",
            "min_watch_liquidity_depth_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityEdgeQueuePressureInput:
    queue_bucket: str
    liquidity_depth_ratio: Decimal
    bid_ask_spread: Decimal
    fee_drag: Decimal
    slippage_risk: Decimal
    settlement_friction: Decimal
    edge_stability: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityEdgeQueuePressureInput, "input")
        _require_public_identifier("queue_bucket", self.queue_bucket)
        object.__setattr__(
            self,
            "liquidity_depth_ratio",
            _require_nonnegative_decimal(
                "liquidity_depth_ratio",
                self.liquidity_depth_ratio,
            ),
        )
        for field_name in (
            "bid_ask_spread",
            "fee_drag",
            "slippage_risk",
            "settlement_friction",
            "edge_stability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityEdgeQueuePressureRow:
    queue_bucket: str
    liquidity_depth_ratio: Decimal
    liquidity_depth_pressure: Decimal
    bid_ask_spread: Decimal
    spread_pressure: Decimal
    fee_drag: Decimal
    fee_drag_pressure: Decimal
    slippage_risk: Decimal
    slippage_risk_pressure: Decimal
    settlement_friction: Decimal
    settlement_friction_pressure: Decimal
    edge_stability: Decimal
    edge_stability_pressure: Decimal
    queue_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityEdgeQueuePressureRow, "row")
        _require_public_identifier("queue_bucket", self.queue_bucket)
        object.__setattr__(
            self,
            "liquidity_depth_ratio",
            _require_nonnegative_decimal(
                "liquidity_depth_ratio",
                self.liquidity_depth_ratio,
            ),
        )
        for field_name in (
            "liquidity_depth_pressure",
            "bid_ask_spread",
            "spread_pressure",
            "fee_drag",
            "fee_drag_pressure",
            "slippage_risk",
            "slippage_risk_pressure",
            "settlement_friction",
            "settlement_friction_pressure",
            "edge_stability",
            "edge_stability_pressure",
            "queue_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityEdgeQueuePressureReport:
    config_version: str
    status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_queue_pressure_score: Decimal
    max_queue_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketLiquidityEdgeQueuePressureRow, ...]
    derived_validation_digest: str = ""
    public_payload: Mapping[str, Any] | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityEdgeQueuePressureReport, "report")
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(self, "status", _require_status(self.status))
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_queue_pressure_score",
            "max_queue_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _finalize_report_public_payload(self)


def build_research_market_liquidity_edge_queue_pressure_report(
    inputs: Iterable[object],
    config: ResearchMarketLiquidityEdgeQueuePressureConfig,
) -> ResearchMarketLiquidityEdgeQueuePressureReport:
    """Build a deterministic, report-only queue pressure scorecard."""

    _require_exact_type(config, ResearchMarketLiquidityEdgeQueuePressureConfig, "config")
    clean_inputs = _normalize_inputs(inputs)
    rows = tuple(
        _row_from_input(input_item, config)
        for input_item in sorted(clean_inputs, key=lambda item: item.queue_bucket)
    )
    input_count = _decimal_count(len(rows))
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    block_count = _status_count(rows, "block")

    return ResearchMarketLiquidityEdgeQueuePressureReport(
        config_version=config.config_version,
        status=_summary_status(
            input_count=input_count,
            watch_count=watch_count,
            block_count=block_count,
        ),
        input_count=input_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_queue_pressure_score=_mean(
            tuple(row.queue_pressure_score for row in rows),
        ),
        max_queue_pressure_score=_max_decimal(
            tuple(row.queue_pressure_score for row in rows),
        ),
        reason_codes=_report_reason_codes(
            input_count=input_count,
            watch_count=watch_count,
            block_count=block_count,
        ),
        rows=rows,
    )


def research_market_liquidity_edge_queue_pressure_report_payload(
    report: ResearchMarketLiquidityEdgeQueuePressureReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketLiquidityEdgeQueuePressureReport:
        _require_hard_flags("report", report)
        if report.public_payload is None:
            raise ValueError("public_payload must be finalized")
        payload = dict(report.public_payload)
    elif type(report) is dict:
        payload = dict(report)
    else:
        raise ValueError(
            "report must be ResearchMarketLiquidityEdgeQueuePressureReport or dict",
        )
    _validate_public_payload(payload)
    return payload


def _row_from_input(
    input_item: ResearchMarketLiquidityEdgeQueuePressureInput,
    config: ResearchMarketLiquidityEdgeQueuePressureConfig,
) -> ResearchMarketLiquidityEdgeQueuePressureRow:
    liquidity_depth_pressure = _liquidity_depth_pressure(
        input_item.liquidity_depth_ratio,
        config.min_pass_liquidity_depth_ratio,
    )
    spread_pressure = _capped_ratio(
        input_item.bid_ask_spread,
        config.max_block_bid_ask_spread,
    )
    fee_drag_pressure = _capped_ratio(input_item.fee_drag, config.max_block_fee_drag)
    slippage_risk_pressure = _capped_ratio(
        input_item.slippage_risk,
        config.max_block_slippage_risk,
    )
    settlement_friction_pressure = _capped_ratio(
        input_item.settlement_friction,
        config.max_block_settlement_friction,
    )
    edge_stability_pressure = _quantize(_ONE - input_item.edge_stability)
    queue_pressure_score = _quantize(
        liquidity_depth_pressure * config.liquidity_depth_weight
        + spread_pressure * config.spread_weight
        + fee_drag_pressure * config.fee_drag_weight
        + slippage_risk_pressure * config.slippage_risk_weight
        + settlement_friction_pressure * config.settlement_friction_weight
        + edge_stability_pressure * config.edge_stability_weight,
    )
    status = _queue_pressure_status(queue_pressure_score, config)

    return ResearchMarketLiquidityEdgeQueuePressureRow(
        queue_bucket=input_item.queue_bucket,
        liquidity_depth_ratio=input_item.liquidity_depth_ratio,
        liquidity_depth_pressure=liquidity_depth_pressure,
        bid_ask_spread=input_item.bid_ask_spread,
        spread_pressure=spread_pressure,
        fee_drag=input_item.fee_drag,
        fee_drag_pressure=fee_drag_pressure,
        slippage_risk=input_item.slippage_risk,
        slippage_risk_pressure=slippage_risk_pressure,
        settlement_friction=input_item.settlement_friction,
        settlement_friction_pressure=settlement_friction_pressure,
        edge_stability=input_item.edge_stability,
        edge_stability_pressure=edge_stability_pressure,
        queue_pressure_score=queue_pressure_score,
        status=status,
        reason_codes=_row_reason_codes(input_item, config, status),
    )


def _row_reason_codes(
    input_item: ResearchMarketLiquidityEdgeQueuePressureInput,
    config: ResearchMarketLiquidityEdgeQueuePressureConfig,
    status: str,
) -> tuple[str, ...]:
    reason_codes = list(input_item.reason_codes)
    _append_lower_bound_reason(
        reason_codes,
        prefix="liquidity_depth_pressure",
        value=input_item.liquidity_depth_ratio,
        pass_threshold=config.min_pass_liquidity_depth_ratio,
        watch_threshold=config.min_watch_liquidity_depth_ratio,
    )
    _append_upper_bound_reason(
        reason_codes,
        prefix="spread_pressure",
        value=input_item.bid_ask_spread,
        pass_threshold=config.max_pass_bid_ask_spread,
        watch_threshold=config.max_watch_bid_ask_spread,
    )
    _append_upper_bound_reason(
        reason_codes,
        prefix="fee_drag_pressure",
        value=input_item.fee_drag,
        pass_threshold=config.max_pass_fee_drag,
        watch_threshold=config.max_watch_fee_drag,
    )
    _append_upper_bound_reason(
        reason_codes,
        prefix="slippage_risk_pressure",
        value=input_item.slippage_risk,
        pass_threshold=config.max_pass_slippage_risk,
        watch_threshold=config.max_watch_slippage_risk,
    )
    _append_upper_bound_reason(
        reason_codes,
        prefix="settlement_friction_pressure",
        value=input_item.settlement_friction,
        pass_threshold=config.max_pass_settlement_friction,
        watch_threshold=config.max_watch_settlement_friction,
    )
    _append_lower_bound_reason(
        reason_codes,
        prefix="edge_stability_pressure",
        value=input_item.edge_stability,
        pass_threshold=config.min_pass_edge_stability,
        watch_threshold=config.min_watch_edge_stability,
    )
    reason_codes.append(f"queue_pressure_{status}")
    return tuple(dict.fromkeys(reason_codes))


def _append_upper_bound_reason(
    reason_codes: list[str],
    *,
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if value > watch_threshold:
        reason_codes.append(f"{prefix}_block")
    elif value > pass_threshold:
        reason_codes.append(f"{prefix}_watch")


def _append_lower_bound_reason(
    reason_codes: list[str],
    *,
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if value < watch_threshold:
        reason_codes.append(f"{prefix}_block")
    elif value < pass_threshold:
        reason_codes.append(f"{prefix}_watch")


def _liquidity_depth_pressure(value: Decimal, pass_threshold: Decimal) -> Decimal:
    if value >= pass_threshold:
        return _ZERO
    return _capped_ratio(pass_threshold - value, pass_threshold)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _quantize(numerator / denominator)
    if ratio > _ONE:
        return _ONE
    return ratio


def _queue_pressure_status(
    score: Decimal,
    config: ResearchMarketLiquidityEdgeQueuePressureConfig,
) -> str:
    if score <= config.max_pass_queue_pressure:
        return "pass"
    if score <= config.max_watch_queue_pressure:
        return "watch"
    return "block"


def _summary_status(
    *,
    input_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
) -> str:
    if input_count == _ZERO or block_count > _ZERO:
        return "block"
    if watch_count > _ZERO:
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    input_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
) -> tuple[str, ...]:
    if input_count == _ZERO:
        return ("no_queue_pressure_inputs",)
    reason_codes: list[str] = []
    if block_count > _ZERO:
        reason_codes.append("queue_pressure_report_block_rows")
    if watch_count > _ZERO:
        reason_codes.append("queue_pressure_report_watch_rows")
    if not reason_codes:
        reason_codes.append("queue_pressure_report_pass")
    return tuple(reason_codes)


def _validate_config(
    config: ResearchMarketLiquidityEdgeQueuePressureConfig,
) -> None:
    _require_ordered_max(
        "max_pass_queue_pressure",
        config.max_pass_queue_pressure,
        "max_watch_queue_pressure",
        config.max_watch_queue_pressure,
    )
    _require_descending_min(
        "min_pass_liquidity_depth_ratio",
        config.min_pass_liquidity_depth_ratio,
        "min_watch_liquidity_depth_ratio",
        config.min_watch_liquidity_depth_ratio,
    )
    for pass_name, watch_name, block_name in (
        (
            "max_pass_bid_ask_spread",
            "max_watch_bid_ask_spread",
            "max_block_bid_ask_spread",
        ),
        ("max_pass_fee_drag", "max_watch_fee_drag", "max_block_fee_drag"),
        (
            "max_pass_slippage_risk",
            "max_watch_slippage_risk",
            "max_block_slippage_risk",
        ),
        (
            "max_pass_settlement_friction",
            "max_watch_settlement_friction",
            "max_block_settlement_friction",
        ),
    ):
        _require_ordered_max(
            pass_name,
            getattr(config, pass_name),
            watch_name,
            getattr(config, watch_name),
        )
        _require_ordered_max(
            watch_name,
            getattr(config, watch_name),
            block_name,
            getattr(config, block_name),
        )
    _require_descending_min(
        "min_pass_edge_stability",
        config.min_pass_edge_stability,
        "min_watch_edge_stability",
        config.min_watch_edge_stability,
    )
    if _weight_sum(config) != _ONE:
        raise ValueError("weights must sum to 1.000000")


def _require_ordered_max(
    lower_name: str,
    lower_value: Decimal,
    upper_name: str,
    upper_value: Decimal,
) -> None:
    if lower_value > upper_value:
        raise ValueError(f"{lower_name} must not exceed {upper_name}")


def _require_descending_min(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{pass_name} must be >= {watch_name}")


def _weight_sum(config: ResearchMarketLiquidityEdgeQueuePressureConfig) -> Decimal:
    return _quantize(
        config.liquidity_depth_weight
        + config.spread_weight
        + config.fee_drag_weight
        + config.slippage_risk_weight
        + config.settlement_friction_weight
        + config.edge_stability_weight,
    )


def _validate_report(report: ResearchMarketLiquidityEdgeQueuePressureReport) -> None:
    input_count = _decimal_count(len(report.rows))
    pass_count = _status_count(report.rows, "pass")
    watch_count = _status_count(report.rows, "watch")
    block_count = _status_count(report.rows, "block")
    if report.input_count != input_count:
        raise ValueError("input_count must match rows")
    if report.pass_count != pass_count:
        raise ValueError("pass_count must match rows")
    if report.watch_count != watch_count:
        raise ValueError("watch_count must match rows")
    if report.block_count != block_count:
        raise ValueError("block_count must match rows")
    if report.average_queue_pressure_score != _mean(
        tuple(row.queue_pressure_score for row in report.rows),
    ):
        raise ValueError("average_queue_pressure_score must match rows")
    if report.max_queue_pressure_score != _max_decimal(
        tuple(row.queue_pressure_score for row in report.rows),
    ):
        raise ValueError("max_queue_pressure_score must match rows")
    if report.status != _summary_status(
        input_count=input_count,
        watch_count=watch_count,
        block_count=block_count,
    ):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(
        input_count=input_count,
        watch_count=watch_count,
        block_count=block_count,
    ):
        raise ValueError("reason_codes must match rows")


def _finalize_report_public_payload(
    report: ResearchMarketLiquidityEdgeQueuePressureReport,
) -> None:
    base_payload = _report_payload_base(report)
    expected_digest = _payload_digest(base_payload)
    supplied_digest = report.derived_validation_digest
    if supplied_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected_digest)
    elif supplied_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")

    public_payload = dict(base_payload)
    public_payload["derived_validation_digest"] = report.derived_validation_digest
    _validate_public_payload(public_payload)

    supplied_payload = report.public_payload
    if supplied_payload is None or supplied_payload == {}:
        object.__setattr__(report, "public_payload", public_payload)
        return
    if type(supplied_payload) is not dict:
        raise ValueError("public_payload must be a JSON object")
    if supplied_payload != public_payload:
        raise ValueError("public_payload must match report fields")
    object.__setattr__(report, "public_payload", dict(supplied_payload))


def _report_payload_base(
    report: ResearchMarketLiquidityEdgeQueuePressureReport,
) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "status": report.status,
        "input_count": _decimal_string(report.input_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "average_queue_pressure_score": _decimal_string(
            report.average_queue_pressure_score,
        ),
        "max_queue_pressure_score": _decimal_string(report.max_queue_pressure_score),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: ResearchMarketLiquidityEdgeQueuePressureRow) -> dict[str, Any]:
    return {
        "queue_bucket_digest": _public_digest(row.queue_bucket),
        "liquidity_depth_ratio": _decimal_string(row.liquidity_depth_ratio),
        "liquidity_depth_pressure": _decimal_string(row.liquidity_depth_pressure),
        "bid_ask_spread": _decimal_string(row.bid_ask_spread),
        "spread_pressure": _decimal_string(row.spread_pressure),
        "fee_drag": _decimal_string(row.fee_drag),
        "fee_drag_pressure": _decimal_string(row.fee_drag_pressure),
        "slippage_risk": _decimal_string(row.slippage_risk),
        "slippage_risk_pressure": _decimal_string(row.slippage_risk_pressure),
        "settlement_friction": _decimal_string(row.settlement_friction),
        "settlement_friction_pressure": _decimal_string(
            row.settlement_friction_pressure,
        ),
        "edge_stability": _decimal_string(row.edge_stability),
        "edge_stability_pressure": _decimal_string(row.edge_stability_pressure),
        "queue_pressure_score": _decimal_string(row.queue_pressure_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketLiquidityEdgeQueuePressureInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    clean = tuple(inputs)
    for item in clean:
        if type(item) is not ResearchMarketLiquidityEdgeQueuePressureInput:
            raise ValueError(
                "inputs must contain ResearchMarketLiquidityEdgeQueuePressureInput values",
            )
        _require_hard_flags("input", item)
    if len({item.queue_bucket for item in clean}) != len(clean):
        raise ValueError("inputs must contain unique queue_bucket values")
    return clean


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketLiquidityEdgeQueuePressureRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    clean = tuple(rows)
    for row in clean:
        if type(row) is not ResearchMarketLiquidityEdgeQueuePressureRow:
            raise ValueError(
                "rows must contain ResearchMarketLiquidityEdgeQueuePressureRow values",
            )
        _require_hard_flags("row", row)
    return clean


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    clean: list[str] = []
    for item in reason_codes:
        code = _require_public_identifier("reason_codes", item)
        if code not in clean:
            clean.append(code)
    return tuple(clean)


def _status_count(
    rows: tuple[ResearchMarketLiquidityEdgeQueuePressureRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return max(values)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_nonnegative_decimal(field_name, value)
    if clean > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return clean


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_nonnegative_decimal(field_name, value)
    if clean <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return clean


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_decimal(field_name, value)
    if clean < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return clean


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _decimal_string(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical public identifier")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_status(value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError("status must be pass, watch, or block")
    return value


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if type(value) is str:
        if _has_unsafe_public_term(value):
            raise ValueError("unsafe public payload")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("unsafe public payload")
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError("unsafe public payload")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(f"{label}.key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    raise ValueError("unsafe public payload")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError("public_payload must be a JSON object")
    _reject_unsafe_json_payload("public_payload", payload)
    supplied = payload.get("derived_validation_digest")
    if type(supplied) is not str or _SHA256_RE.fullmatch(supplied) is None:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
    base_payload = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    if _payload_digest(base_payload) != supplied:
        raise ValueError("derived_validation_digest must match payload fields")


def _reject_unsafe_json_payload(label: str, value: object) -> None:
    if type(value) is str:
        if _has_unsafe_public_term(value):
            raise ValueError("unsafe public payload")
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("unsafe public payload")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload")
            _reject_unsafe_json_payload(f"{label}.key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError("unsafe public payload")
            _reject_unsafe_json_payload(f"{label}.{key}", item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_json_payload(label, item)
        return
    raise ValueError("unsafe public payload")


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _has_unsafe_public_term(value: str) -> bool:
    lower_value = value.lower()
    if any(term in lower_value for term in _UNSAFE_PUBLIC_TERMS):
        return True
    return any(
        segment in _UNSAFE_PUBLIC_SEGMENTS
        for segment in _PUBLIC_SEGMENT_RE.split(lower_value)
    )


def _public_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"
