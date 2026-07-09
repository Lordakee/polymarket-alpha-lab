"""Report-only exit-liquidity gate for sanitized probability-event markets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Iterable


DEFAULT_CONFIG_VERSION = "research-market-depth-fee-exit-liquidity-gate-report-v1"
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_QUANT = Decimal("1")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_MISSING_INPUTS = "missing_depth_fee_exit_liquidity_inputs"
REASON_PASS = "exit_liquidity_gate_pass"
REASON_SCORE_WATCH = "exit_liquidity_score_watch"
REASON_SCORE_BLOCK = "exit_liquidity_score_block"
REASON_DEPTH_WATCH = "depth_coverage_watch"
REASON_DEPTH_BLOCK = "depth_coverage_block"
REASON_FEE_WATCH = "fee_drag_watch"
REASON_FEE_BLOCK = "fee_drag_block"
REASON_SPREAD_WATCH = "spread_watch"
REASON_SPREAD_BLOCK = "spread_block"
REASON_SLIPPAGE_WATCH = "slippage_pressure_watch"
REASON_SLIPPAGE_BLOCK = "slippage_pressure_block"
REASON_SETTLEMENT_WATCH = "settlement_friction_watch"
REASON_SETTLEMENT_BLOCK = "settlement_friction_block"
REASON_ESTIMATED_COST_WATCH = "estimated_exit_cost_watch"
REASON_ESTIMATED_COST_BLOCK = "estimated_exit_cost_block"
REASON_CODES = (
    REASON_MISSING_INPUTS,
    REASON_PASS,
    REASON_SCORE_WATCH,
    REASON_SCORE_BLOCK,
    REASON_DEPTH_WATCH,
    REASON_DEPTH_BLOCK,
    REASON_FEE_WATCH,
    REASON_FEE_BLOCK,
    REASON_SPREAD_WATCH,
    REASON_SPREAD_BLOCK,
    REASON_SLIPPAGE_WATCH,
    REASON_SLIPPAGE_BLOCK,
    REASON_SETTLEMENT_WATCH,
    REASON_SETTLEMENT_BLOCK,
    REASON_ESTIMATED_COST_WATCH,
    REASON_ESTIMATED_COST_BLOCK,
)

_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_SENSITIVE_TEXT_FRAGMENTS = (
    "api" + "_key",
    "auth",
    "credential",
    "dsn",
    "market" + "_id",
    "market" + "_slug",
    "private" + "_key",
    "question",
    "secret",
    "source",
    "table",
    "token",
    "url",
    "http",
    "wall" + "et",
    "ord" + "er",
    "tra" + "de",
)


@dataclass(frozen=True)
class ResearchMarketDepthFeeExitLiquidityGateConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_exit_liquidity_risk_score: Decimal = Decimal("0.350000")
    block_exit_liquidity_risk_score: Decimal = Decimal("0.700000")
    minimum_depth_coverage_ratio: Decimal = Decimal("1.000000")
    depth_coverage_watch_threshold: Decimal = Decimal("0.750000")
    depth_coverage_block_threshold: Decimal = Decimal("0.350000")
    fee_drag_watch_threshold: Decimal = Decimal("0.015000")
    fee_drag_block_threshold: Decimal = Decimal("0.040000")
    spread_watch_threshold: Decimal = Decimal("0.030000")
    spread_block_threshold: Decimal = Decimal("0.070000")
    slippage_pressure_watch_threshold: Decimal = Decimal("0.020000")
    slippage_pressure_block_threshold: Decimal = Decimal("0.060000")
    settlement_friction_watch_threshold: Decimal = Decimal("0.250000")
    settlement_friction_block_threshold: Decimal = Decimal("0.700000")
    estimated_exit_cost_watch_threshold: Decimal = Decimal("0.040000")
    estimated_exit_cost_block_threshold: Decimal = Decimal("0.100000")
    depth_weight: Decimal = Decimal("0.300000")
    fee_drag_weight: Decimal = Decimal("0.150000")
    spread_weight: Decimal = Decimal("0.150000")
    slippage_pressure_weight: Decimal = Decimal("0.250000")
    settlement_friction_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchMarketDepthFeeExitLiquidityGateConfig)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_exit_liquidity_risk_score",
            "block_exit_liquidity_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_rate(field_name, getattr(self, field_name)),
            )
        _require_ordered_thresholds(
            "watch_exit_liquidity_risk_score",
            self.watch_exit_liquidity_risk_score,
            self.block_exit_liquidity_risk_score,
        )
        object.__setattr__(
            self,
            "minimum_depth_coverage_ratio",
            _normalize_positive_decimal(
                "minimum_depth_coverage_ratio",
                self.minimum_depth_coverage_ratio,
            ),
        )
        for field_name in (
            "depth_coverage_watch_threshold",
            "depth_coverage_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.depth_coverage_block_threshold > self.depth_coverage_watch_threshold:
            raise ValueError(
                "depth_coverage_block_threshold must not exceed "
                "depth_coverage_watch_threshold",
            )
        for watch_field, block_field in (
            ("fee_drag_watch_threshold", "fee_drag_block_threshold"),
            ("spread_watch_threshold", "spread_block_threshold"),
            (
                "slippage_pressure_watch_threshold",
                "slippage_pressure_block_threshold",
            ),
            (
                "settlement_friction_watch_threshold",
                "settlement_friction_block_threshold",
            ),
            (
                "estimated_exit_cost_watch_threshold",
                "estimated_exit_cost_block_threshold",
            ),
        ):
            object.__setattr__(
                self,
                watch_field,
                _normalize_positive_rate(watch_field, getattr(self, watch_field)),
            )
            object.__setattr__(
                self,
                block_field,
                _normalize_positive_rate(block_field, getattr(self, block_field)),
            )
            _require_ordered_thresholds(
                watch_field,
                getattr(self, watch_field),
                getattr(self, block_field),
            )
        for field_name in (
            "depth_weight",
            "fee_drag_weight",
            "spread_weight",
            "slippage_pressure_weight",
            "settlement_friction_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_rate(field_name, getattr(self, field_name)),
            )
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthFeeExitLiquidityGateInput:
    event_reference: str
    observed_at: datetime
    depth_coverage_ratio: Decimal
    fee_drag_rate: Decimal
    bid_ask_spread_rate: Decimal
    slippage_pressure_rate: Decimal
    settlement_friction_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchMarketDepthFeeExitLiquidityGateInput)
        _require_canonical_string("event_reference", self.event_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "depth_coverage_ratio",
            _normalize_nonnegative_decimal(
                "depth_coverage_ratio",
                self.depth_coverage_ratio,
            ),
        )
        for field_name in (
            "fee_drag_rate",
            "bid_ask_spread_rate",
            "slippage_pressure_rate",
            "settlement_friction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_rate(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketDepthFeeExitLiquidityGateReportRow:
    event_digest: str
    observed_at: datetime
    depth_coverage_ratio: Decimal
    fee_drag_rate: Decimal
    bid_ask_spread_rate: Decimal
    slippage_pressure_rate: Decimal
    settlement_friction_score: Decimal
    estimated_exit_cost_rate: Decimal
    depth_risk_score: Decimal
    fee_drag_risk_score: Decimal
    spread_risk_score: Decimal
    slippage_pressure_risk_score: Decimal
    settlement_friction_risk_score: Decimal
    exit_liquidity_risk_score: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchMarketDepthFeeExitLiquidityGateReportRow)
        _require_sha256_digest("event_digest", self.event_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "depth_coverage_ratio",
            _normalize_nonnegative_decimal(
                "depth_coverage_ratio",
                self.depth_coverage_ratio,
            ),
        )
        for field_name in (
            "fee_drag_rate",
            "bid_ask_spread_rate",
            "slippage_pressure_rate",
            "settlement_friction_score",
            "estimated_exit_cost_rate",
            "depth_risk_score",
            "fee_drag_risk_score",
            "spread_risk_score",
            "slippage_pressure_risk_score",
            "settlement_friction_risk_score",
            "exit_liquidity_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_rate(field_name, getattr(self, field_name)),
            )
        _require_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchMarketDepthFeeExitLiquidityGateReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    highest_exit_liquidity_risk_score: Decimal
    max_estimated_exit_cost_rate: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketDepthFeeExitLiquidityGateReportRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchMarketDepthFeeExitLiquidityGateReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_exit_liquidity_risk_score",
            "max_estimated_exit_cost_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_rate(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            _validate_report(self)
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
            _validate_report(self)
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _reject_unsafe_public_payload(
            "research market depth fee exit liquidity gate report",
            _json_ready(self),
            allow_json_containers=True,
        )


def build_research_market_depth_fee_exit_liquidity_gate_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketDepthFeeExitLiquidityGateConfig,
    generated_at: datetime,
) -> ResearchMarketDepthFeeExitLiquidityGateReport:
    if type(config) is not ResearchMarketDepthFeeExitLiquidityGateConfig:
        raise ValueError(
            "config must be a ResearchMarketDepthFeeExitLiquidityGateConfig",
        )
    _require_hard_flags("config", config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return ResearchMarketDepthFeeExitLiquidityGateReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_count=_decimal_count(len(normalized_inputs)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        highest_exit_liquidity_risk_score=(
            rows[0].exit_liquidity_risk_score if rows else ZERO
        ),
        max_estimated_exit_cost_rate=_maximum(
            (row.estimated_exit_cost_rate for row in rows),
            ZERO,
        ),
        report_status=status,
        reason_codes=_report_reason_codes(rows, status),
        rows=rows,
    )


def research_market_depth_fee_exit_liquidity_gate_report_payload(
    report: ResearchMarketDepthFeeExitLiquidityGateReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketDepthFeeExitLiquidityGateReport:
        _require_hard_flags("report", report)
        if report.derived_validation_digest != _report_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketDepthFeeExitLiquidityGateReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload(
        "research market depth fee exit liquidity gate payload",
        payload,
        allow_json_containers=True,
    )
    return payload


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
    item: ResearchMarketDepthFeeExitLiquidityGateInput,
    *,
    config: ResearchMarketDepthFeeExitLiquidityGateConfig,
) -> ResearchMarketDepthFeeExitLiquidityGateReportRow:
    estimated_exit_cost_rate = _quantize(
        item.fee_drag_rate
        + (item.bid_ask_spread_rate / Decimal("2"))
        + item.slippage_pressure_rate,
    )
    depth_risk_score = _depth_risk_score(item.depth_coverage_ratio, config)
    fee_drag_risk_score = _threshold_score(
        item.fee_drag_rate,
        config.fee_drag_block_threshold,
        config.fee_drag_weight,
    )
    spread_risk_score = _threshold_score(
        item.bid_ask_spread_rate,
        config.spread_block_threshold,
        config.spread_weight,
    )
    slippage_pressure_risk_score = _threshold_score(
        item.slippage_pressure_rate,
        config.slippage_pressure_block_threshold,
        config.slippage_pressure_weight,
    )
    settlement_friction_risk_score = _threshold_score(
        item.settlement_friction_score,
        config.settlement_friction_block_threshold,
        config.settlement_friction_weight,
    )
    exit_liquidity_risk_score = _quantize(
        min(
            ONE,
            depth_risk_score
            + fee_drag_risk_score
            + spread_risk_score
            + slippage_pressure_risk_score
            + settlement_friction_risk_score,
        ),
    )
    gate_status = _score_status(exit_liquidity_risk_score, config)
    return ResearchMarketDepthFeeExitLiquidityGateReportRow(
        event_digest=_event_digest(item.event_reference),
        observed_at=item.observed_at,
        depth_coverage_ratio=item.depth_coverage_ratio,
        fee_drag_rate=item.fee_drag_rate,
        bid_ask_spread_rate=item.bid_ask_spread_rate,
        slippage_pressure_rate=item.slippage_pressure_rate,
        settlement_friction_score=item.settlement_friction_score,
        estimated_exit_cost_rate=estimated_exit_cost_rate,
        depth_risk_score=depth_risk_score,
        fee_drag_risk_score=fee_drag_risk_score,
        spread_risk_score=spread_risk_score,
        slippage_pressure_risk_score=slippage_pressure_risk_score,
        settlement_friction_risk_score=settlement_friction_risk_score,
        exit_liquidity_risk_score=exit_liquidity_risk_score,
        gate_status=gate_status,
        reason_codes=_row_reason_codes(
            item,
            config=config,
            estimated_exit_cost_rate=estimated_exit_cost_rate,
            gate_status=gate_status,
        ),
    )


def _depth_risk_score(
    depth_coverage_ratio: Decimal,
    config: ResearchMarketDepthFeeExitLiquidityGateConfig,
) -> Decimal:
    if depth_coverage_ratio >= config.minimum_depth_coverage_ratio:
        return ZERO
    shortfall_ratio = (
        config.minimum_depth_coverage_ratio - depth_coverage_ratio
    ) / config.minimum_depth_coverage_ratio
    return _quantize(min(ONE, shortfall_ratio) * config.depth_weight)


def _threshold_score(value: Decimal, block_threshold: Decimal, weight: Decimal) -> Decimal:
    return _quantize(min(ONE, value / block_threshold) * weight)


def _score_status(
    exit_liquidity_risk_score: Decimal,
    config: ResearchMarketDepthFeeExitLiquidityGateConfig,
) -> str:
    if exit_liquidity_risk_score >= config.block_exit_liquidity_risk_score:
        return STATUS_BLOCK
    if exit_liquidity_risk_score >= config.watch_exit_liquidity_risk_score:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    item: ResearchMarketDepthFeeExitLiquidityGateInput,
    *,
    config: ResearchMarketDepthFeeExitLiquidityGateConfig,
    estimated_exit_cost_rate: Decimal,
    gate_status: str,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.depth_coverage_ratio <= config.depth_coverage_block_threshold:
        reasons.append(REASON_DEPTH_BLOCK)
    elif item.depth_coverage_ratio <= config.depth_coverage_watch_threshold:
        reasons.append(REASON_DEPTH_WATCH)
    reasons.extend(
        _factor_reason(
            item.fee_drag_rate,
            config.fee_drag_watch_threshold,
            config.fee_drag_block_threshold,
            REASON_FEE_WATCH,
            REASON_FEE_BLOCK,
        ),
    )
    reasons.extend(
        _factor_reason(
            item.bid_ask_spread_rate,
            config.spread_watch_threshold,
            config.spread_block_threshold,
            REASON_SPREAD_WATCH,
            REASON_SPREAD_BLOCK,
        ),
    )
    reasons.extend(
        _factor_reason(
            item.slippage_pressure_rate,
            config.slippage_pressure_watch_threshold,
            config.slippage_pressure_block_threshold,
            REASON_SLIPPAGE_WATCH,
            REASON_SLIPPAGE_BLOCK,
        ),
    )
    reasons.extend(
        _factor_reason(
            item.settlement_friction_score,
            config.settlement_friction_watch_threshold,
            config.settlement_friction_block_threshold,
            REASON_SETTLEMENT_WATCH,
            REASON_SETTLEMENT_BLOCK,
        ),
    )
    reasons.extend(
        _factor_reason(
            estimated_exit_cost_rate,
            config.estimated_exit_cost_watch_threshold,
            config.estimated_exit_cost_block_threshold,
            REASON_ESTIMATED_COST_WATCH,
            REASON_ESTIMATED_COST_BLOCK,
        ),
    )
    if gate_status == STATUS_BLOCK:
        reasons.append(REASON_SCORE_BLOCK)
    elif gate_status == STATUS_WATCH:
        reasons.append(REASON_SCORE_WATCH)
    if not reasons:
        reasons.append(REASON_PASS)
    return _normalize_reason_codes(tuple(sorted(set(reasons))), allow_empty=False)


def _factor_reason(
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> tuple[str, ...]:
    if value >= block_threshold:
        return (block_reason,)
    if value >= watch_threshold:
        return (watch_reason,)
    return ()


def _event_digest(event_reference: str) -> str:
    return hashlib.sha256(event_reference.encode("utf-8")).hexdigest()


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketDepthFeeExitLiquidityGateInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchMarketDepthFeeExitLiquidityGateInput:
            raise ValueError(
                "inputs must contain ResearchMarketDepthFeeExitLiquidityGateInput values",
            )
        _require_hard_flags("input", value)
    return values


def _report_status(
    rows: tuple[ResearchMarketDepthFeeExitLiquidityGateReportRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.gate_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.gate_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketDepthFeeExitLiquidityGateReportRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    reasons: set[str] = set()
    for row in rows:
        if row.gate_status == status:
            reasons.update(row.reason_codes)
    if not reasons:
        raise ValueError("report_status must match at least one row")
    return tuple(sorted(reasons))


def _row_sort_key(
    row: ResearchMarketDepthFeeExitLiquidityGateReportRow,
) -> tuple[Decimal, datetime, str]:
    return (-row.exit_liquidity_risk_score, row.observed_at, row.event_digest)


def _status_count(
    rows: tuple[ResearchMarketDepthFeeExitLiquidityGateReportRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.gate_status == status))


def _normalize_rows(
    value: object,
) -> tuple[ResearchMarketDepthFeeExitLiquidityGateReportRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchMarketDepthFeeExitLiquidityGateReportRow:
            raise ValueError(
                "rows must contain ResearchMarketDepthFeeExitLiquidityGateReportRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if len({(row.event_digest, row.observed_at) for row in rows}) != len(rows):
        raise ValueError("rows must be unique by event digest and observed time")
    return rows


def _validate_row(row: ResearchMarketDepthFeeExitLiquidityGateReportRow) -> None:
    expected_cost = _quantize(
        row.fee_drag_rate
        + (row.bid_ask_spread_rate / Decimal("2"))
        + row.slippage_pressure_rate,
    )
    if row.estimated_exit_cost_rate != expected_cost:
        raise ValueError("estimated_exit_cost_rate does not match inputs")
    expected_score = _quantize(
        min(
            ONE,
            row.depth_risk_score
            + row.fee_drag_risk_score
            + row.spread_risk_score
            + row.slippage_pressure_risk_score
            + row.settlement_friction_risk_score,
        ),
    )
    if row.exit_liquidity_risk_score != expected_score:
        raise ValueError("exit_liquidity_risk_score does not match components")
    if row.gate_status == STATUS_PASS and row.reason_codes != (REASON_PASS,):
        raise ValueError("pass rows require pass reason")
    if row.gate_status == STATUS_WATCH and REASON_SCORE_WATCH not in row.reason_codes:
        raise ValueError("watch rows require score watch reason")
    if row.gate_status == STATUS_BLOCK and REASON_SCORE_BLOCK not in row.reason_codes:
        raise ValueError("block rows require score block reason")


def _validate_report(report: ResearchMarketDepthFeeExitLiquidityGateReport) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count does not match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count does not match rows")
    expected_highest = rows[0].exit_liquidity_risk_score if rows else ZERO
    if report.highest_exit_liquidity_risk_score != expected_highest:
        raise ValueError("highest_exit_liquidity_risk_score does not match rows")
    expected_max_cost = _maximum((row.estimated_exit_cost_rate for row in rows), ZERO)
    if report.max_estimated_exit_cost_rate != expected_max_cost:
        raise ValueError("max_estimated_exit_cost_rate does not match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status does not match rows")
    if report.reason_codes != _report_reason_codes(rows, report.report_status):
        raise ValueError("reason_codes do not match rows")


def _report_validation_digest(
    report: ResearchMarketDepthFeeExitLiquidityGateReport,
) -> str:
    payload = {
        field.name: _json_ready(getattr(report, field.name))
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None or type(value) is bool:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be exactly datetime")
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
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{current_path} must be exactly Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if isinstance(value, datetime):
        raise ValueError(f"{current_path} must be exactly datetime")
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{current_path} must not be a float")
    if type(value) is str:
        if value != value.strip():
            raise ValueError(f"{current_path} has unsafe value")
        lowered = value.lower()
        if any(fragment in lowered for fragment in _SENSITIVE_TEXT_FRAGMENTS):
            raise ValueError(f"{current_path} has unsafe value")
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
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in _SENSITIVE_TEXT_FRAGMENTS):
                raise ValueError(f"{item_path} has unsafe field")
            if key in _PHASE_FLAG_FIELDS and item is not True:
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


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_rate(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_rate(field_name: str, value: object) -> Decimal:
    normalized = _normalize_rate(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(COUNT_QUANT, rounding=ROUND_HALF_EVEN)
    if normalized != value:
        raise ValueError(f"{field_name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_reason_codes(value: object, *, allow_empty: bool) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain known gate reasons")
    if tuple(sorted(reason_codes)) != reason_codes:
        raise ValueError("reason_codes must be sorted")
    return reason_codes


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_ordered_thresholds(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if watch_value > block_value:
        raise ValueError(f"{field_name} watch threshold must not exceed block threshold")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT, rounding=ROUND_HALF_EVEN)


def _maximum(values: Iterable[Decimal], default: Decimal) -> Decimal:
    items = tuple(values)
    if not items:
        return default
    return _quantize(max(items))


def _weight_sum(config: ResearchMarketDepthFeeExitLiquidityGateConfig) -> Decimal:
    return _quantize(
        config.depth_weight
        + config.fee_drag_weight
        + config.spread_weight
        + config.slippage_pressure_weight
        + config.settlement_friction_weight,
    )


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketDepthFeeExitLiquidityGateConfig",
    "ResearchMarketDepthFeeExitLiquidityGateInput",
    "ResearchMarketDepthFeeExitLiquidityGateReportRow",
    "ResearchMarketDepthFeeExitLiquidityGateReport",
    "build_research_market_depth_fee_exit_liquidity_gate_report",
    "research_market_depth_fee_exit_liquidity_gate_report_payload",
)
