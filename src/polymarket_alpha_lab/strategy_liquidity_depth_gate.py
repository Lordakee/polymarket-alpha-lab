"""Pure strategy liquidity/depth gate for paper-side market descriptors.

This module reduces caller-supplied in-memory liquidity fields into a readonly
report. It performs no IO, network access, credential handling, account access,
broker interaction, execution, or investment advice.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any


DEFAULT_STRATEGY_LIQUIDITY_DEPTH_GATE_CONFIG_VERSION = (
    "strategy-liquidity-depth-gate-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
GATE_STATUSES = ("pass", "watch", "blocked")
STATUS_PRIORITY = {
    "pass": 0,
    "watch": 1,
    "blocked": 2,
}
REPORT_REASON_CODES = (
    "missing_strategy_liquidity_depth_inputs",
    "missing_target_notional",
    "no_available_depth",
    "depth_below_watch_threshold",
    "spread_above_watch_threshold",
    "activity_below_watch_threshold",
    "depth_below_pass_threshold",
    "spread_above_pass_threshold",
    "activity_below_pass_threshold",
    "strategy_liquidity_depth_gate_pass",
)


@dataclass(frozen=True)
class StrategyLiquidityDepthGateInput:
    market_slug: str
    top_of_book_spread: Decimal
    available_depth: Decimal
    target_notional: Decimal
    market_activity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "top_of_book_spread",
            _normalize_probability("top_of_book_spread", self.top_of_book_spread),
        )
        for field_name in ("available_depth", "target_notional"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_activity_score",
            _normalize_probability("market_activity_score", self.market_activity_score),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyLiquidityDepthGateConfig:
    config_version: str = DEFAULT_STRATEGY_LIQUIDITY_DEPTH_GATE_CONFIG_VERSION
    max_pass_top_of_book_spread: Decimal = Decimal("0.020000")
    max_watch_top_of_book_spread: Decimal = Decimal("0.050000")
    min_pass_depth_ratio: Decimal = Decimal("0.800000")
    min_watch_depth_ratio: Decimal = Decimal("0.500000")
    min_pass_market_activity_score: Decimal = Decimal("0.700000")
    min_watch_market_activity_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_STRATEGY_LIQUIDITY_DEPTH_GATE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_top_of_book_spread",
            "max_watch_top_of_book_spread",
            "min_pass_depth_ratio",
            "min_watch_depth_ratio",
            "min_pass_market_activity_score",
            "min_watch_market_activity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.max_pass_top_of_book_spread > self.max_watch_top_of_book_spread:
            raise ValueError(
                "max_pass_top_of_book_spread must not exceed watch threshold",
            )
        if self.min_watch_depth_ratio > self.min_pass_depth_ratio:
            raise ValueError("min_watch_depth_ratio must not exceed pass threshold")
        if self.min_watch_market_activity_score > self.min_pass_market_activity_score:
            raise ValueError(
                "min_watch_market_activity_score must not exceed pass threshold",
            )
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyLiquidityDepthGateRow:
    market_slug: str
    top_of_book_spread: Decimal
    available_depth: Decimal
    target_notional: Decimal
    market_activity_score: Decimal
    depth_ratio: Decimal
    gate_status: str
    capacity_notional: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "top_of_book_spread",
            _normalize_probability("top_of_book_spread", self.top_of_book_spread),
        )
        for field_name in (
            "available_depth",
            "target_notional",
            "capacity_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_activity_score",
            _normalize_probability("market_activity_score", self.market_activity_score),
        )
        object.__setattr__(
            self,
            "depth_ratio",
            _normalize_probability("depth_ratio", self.depth_ratio),
        )
        _require_gate_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyLiquidityDepthGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    capacity_notional: Decimal
    rows: tuple[StrategyLiquidityDepthGateRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_gate_status("gate_status", self.gate_status)
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "capacity_notional",
            _normalize_nonnegative_decimal("capacity_notional", self.capacity_notional),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_strategy_liquidity_depth_gate_report(
    inputs: tuple[StrategyLiquidityDepthGateInput, ...],
    *,
    config: StrategyLiquidityDepthGateConfig,
    generated_at: datetime,
) -> StrategyLiquidityDepthGateReport:
    if type(config) is not StrategyLiquidityDepthGateConfig:
        raise ValueError("config must be a StrategyLiquidityDepthGateConfig")
    _require_safety_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(value, config=config) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    return StrategyLiquidityDepthGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        gate_status=_overall_status(rows),
        input_count=Decimal(len(normalized_inputs)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        capacity_notional=_sum_decimal(row.capacity_notional for row in rows),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def strategy_liquidity_depth_gate_payload(
    report: StrategyLiquidityDepthGateReport,
) -> dict[str, Any]:
    if type(report) is not StrategyLiquidityDepthGateReport:
        raise ValueError("report must be a StrategyLiquidityDepthGateReport")
    _require_safety_flags(report)
    payload = _payload_ready(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("payload must be a mapping")
    return payload


def _row_from_input(
    value: StrategyLiquidityDepthGateInput,
    *,
    config: StrategyLiquidityDepthGateConfig,
) -> StrategyLiquidityDepthGateRow:
    depth_ratio = _depth_ratio(value.available_depth, value.target_notional)
    gate_status = _gate_status(
        top_of_book_spread=value.top_of_book_spread,
        available_depth=value.available_depth,
        target_notional=value.target_notional,
        market_activity_score=value.market_activity_score,
        depth_ratio=depth_ratio,
        config=config,
    )
    return StrategyLiquidityDepthGateRow(
        market_slug=value.market_slug,
        top_of_book_spread=value.top_of_book_spread,
        available_depth=value.available_depth,
        target_notional=value.target_notional,
        market_activity_score=value.market_activity_score,
        depth_ratio=depth_ratio,
        gate_status=gate_status,
        capacity_notional=_capacity_notional(
            available_depth=value.available_depth,
            target_notional=value.target_notional,
        ),
        reason_codes=_row_reason_codes(
            top_of_book_spread=value.top_of_book_spread,
            available_depth=value.available_depth,
            target_notional=value.target_notional,
            market_activity_score=value.market_activity_score,
            depth_ratio=depth_ratio,
            config=config,
        ),
    )


def _gate_status(
    *,
    top_of_book_spread: Decimal,
    available_depth: Decimal,
    target_notional: Decimal,
    market_activity_score: Decimal,
    depth_ratio: Decimal,
    config: StrategyLiquidityDepthGateConfig,
) -> str:
    if target_notional <= ZERO:
        return "blocked"
    if available_depth <= ZERO:
        return "blocked"
    if depth_ratio < config.min_watch_depth_ratio:
        return "blocked"
    if top_of_book_spread > config.max_watch_top_of_book_spread:
        return "blocked"
    if market_activity_score < config.min_watch_market_activity_score:
        return "blocked"
    if depth_ratio < config.min_pass_depth_ratio:
        return "watch"
    if top_of_book_spread > config.max_pass_top_of_book_spread:
        return "watch"
    if market_activity_score < config.min_pass_market_activity_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    top_of_book_spread: Decimal,
    available_depth: Decimal,
    target_notional: Decimal,
    market_activity_score: Decimal,
    depth_ratio: Decimal,
    config: StrategyLiquidityDepthGateConfig,
) -> tuple[str, ...]:
    target_codes = (
        ("missing_target_notional",) if target_notional <= ZERO else ()
    )
    depth_absence_codes = (
        ("no_available_depth",)
        if target_notional > ZERO and available_depth <= ZERO
        else ()
    )
    depth_threshold_codes = _depth_threshold_reason_codes(
        available_depth=available_depth,
        target_notional=target_notional,
        depth_ratio=depth_ratio,
        config=config,
    )
    spread_codes = _spread_reason_codes(top_of_book_spread, config)
    activity_codes = _activity_reason_codes(market_activity_score, config)
    codes = (
        *target_codes,
        *depth_absence_codes,
        *depth_threshold_codes,
        *spread_codes,
        *activity_codes,
    )
    if not codes:
        codes = ("strategy_liquidity_depth_gate_pass",)
    return _normalize_reason_codes(codes)


def _depth_threshold_reason_codes(
    *,
    available_depth: Decimal,
    target_notional: Decimal,
    depth_ratio: Decimal,
    config: StrategyLiquidityDepthGateConfig,
) -> tuple[str, ...]:
    if target_notional <= ZERO or available_depth <= ZERO:
        return ()
    if depth_ratio < config.min_watch_depth_ratio:
        return ("depth_below_watch_threshold",)
    if depth_ratio < config.min_pass_depth_ratio:
        return ("depth_below_pass_threshold",)
    return ()


def _spread_reason_codes(
    top_of_book_spread: Decimal,
    config: StrategyLiquidityDepthGateConfig,
) -> tuple[str, ...]:
    if top_of_book_spread > config.max_watch_top_of_book_spread:
        return ("spread_above_watch_threshold",)
    if top_of_book_spread > config.max_pass_top_of_book_spread:
        return ("spread_above_pass_threshold",)
    return ()


def _activity_reason_codes(
    market_activity_score: Decimal,
    config: StrategyLiquidityDepthGateConfig,
) -> tuple[str, ...]:
    if market_activity_score < config.min_watch_market_activity_score:
        return ("activity_below_watch_threshold",)
    if market_activity_score < config.min_pass_market_activity_score:
        return ("activity_below_pass_threshold",)
    return ()


def _depth_ratio(available_depth: Decimal, target_notional: Decimal) -> Decimal:
    if target_notional <= ZERO:
        return _quantize(ZERO)
    if available_depth <= ZERO:
        return _quantize(ZERO)
    with localcontext(DECIMAL_CONTEXT):
        ratio = available_depth / target_notional
    if ratio > ONE:
        return _quantize(ONE)
    return _quantize(ratio)


def _capacity_notional(
    *,
    available_depth: Decimal,
    target_notional: Decimal,
) -> Decimal:
    if target_notional <= ZERO or available_depth <= ZERO:
        return _quantize(ZERO)
    if available_depth < target_notional:
        return available_depth
    return target_notional


def _overall_status(rows: tuple[StrategyLiquidityDepthGateRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.gate_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyLiquidityDepthGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("missing_strategy_liquidity_depth_inputs",)
    source_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != "strategy_liquidity_depth_gate_pass"
    )
    if not source_codes:
        return ("strategy_liquidity_depth_gate_pass",)
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_CODES
        if reason_code in source_codes
    )


def _row_sort_key(
    row: StrategyLiquidityDepthGateRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_PRIORITY[row.gate_status],
        -row.capacity_notional,
        -row.depth_ratio,
        row.top_of_book_spread,
        row.market_slug,
    )


def _status_count(
    rows: tuple[StrategyLiquidityDepthGateRow, ...],
    gate_status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.gate_status == gate_status))


def _sum_decimal(values: Any) -> Decimal:
    return _quantize(sum(values, ZERO))


def _normalize_inputs(
    inputs: tuple[StrategyLiquidityDepthGateInput, ...],
) -> tuple[StrategyLiquidityDepthGateInput, ...]:
    if type(inputs) is not tuple:
        raise ValueError("inputs must be a tuple of StrategyLiquidityDepthGateInput values")
    for value in inputs:
        if type(value) is not StrategyLiquidityDepthGateInput:
            raise ValueError(
                "inputs must contain only StrategyLiquidityDepthGateInput values",
            )
        _require_safety_flags(value)
    return inputs


def _normalize_rows(
    rows: tuple[StrategyLiquidityDepthGateRow, ...],
) -> tuple[StrategyLiquidityDepthGateRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyLiquidityDepthGateRow:
            raise ValueError("rows must contain StrategyLiquidityDepthGateRow values")
        _require_safety_flags(row)
    if len(set(rows)) != len(rows):
        raise ValueError("rows must be unique")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return rows


def _validate_row_consistency(row: StrategyLiquidityDepthGateRow) -> None:
    expected_depth_ratio = _depth_ratio(row.available_depth, row.target_notional)
    if row.depth_ratio != expected_depth_ratio:
        raise ValueError("depth_ratio must match available_depth and target_notional")
    expected_capacity_notional = _capacity_notional(
        available_depth=row.available_depth,
        target_notional=row.target_notional,
    )
    if row.capacity_notional != expected_capacity_notional:
        raise ValueError("capacity_notional must match available_depth and target_notional")
    if row.capacity_notional > row.available_depth:
        raise ValueError("capacity_notional must not exceed available_depth")
    if row.target_notional > ZERO and row.capacity_notional > row.target_notional:
        raise ValueError("capacity_notional must not exceed target_notional")


def _validate_report_consistency(report: StrategyLiquidityDepthGateReport) -> None:
    if report.input_count != Decimal(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.input_count != (
        report.pass_count + report.watch_count + report.blocked_count
    ):
        raise ValueError("input_count must match gate status counts")
    if report.capacity_notional != _sum_decimal(
        row.capacity_notional for row in report.rows
    ):
        raise ValueError("capacity_notional must match rows")
    if report.gate_status != _overall_status(report.rows):
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _payload_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_ready(item) for item in value]
    if isinstance(value, list):
        return [_payload_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _payload_ready(item) for key, item in value.items()}
    return value


def _normalize_report_reason_codes(
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    normalized = _normalize_reason_codes(reason_codes)
    for reason_code in normalized:
        if reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_codes contains an unsupported reason code")
    return normalized


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple of strings")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(dict.fromkeys(reason_codes))


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_integral_decimal(
    field_name: str,
    value: Decimal,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    integral_value = value.to_integral_value()
    if value != integral_value:
        raise ValueError(f"{field_name} must be integral")
    return integral_value


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_gate_status(field_name: str, value: str) -> None:
    if value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_safety_flags(value: Any) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "StrategyLiquidityDepthGateInput",
    "StrategyLiquidityDepthGateConfig",
    "StrategyLiquidityDepthGateRow",
    "StrategyLiquidityDepthGateReport",
    "build_strategy_liquidity_depth_gate_report",
    "strategy_liquidity_depth_gate_payload",
)
