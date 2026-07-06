"""Paper/report-only strategy edge decay policy.

Pure supplied-input Decimal arithmetic for estimating edge decay before any
paper strategy candidate is promoted into downstream research reports.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields
from decimal import Context, Decimal, localcontext
from typing import Any


DEFAULT_STRATEGY_EDGE_DECAY_POLICY_CONFIG_VERSION = "strategy-edge-decay-policy-v0"

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)

SECONDS_PER_HALF_DAY = Decimal("43200.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
SECONDS_PER_TWO_DAYS = Decimal("172800.000000")
SECONDS_PER_THREE_HOURS = Decimal("10800.000000")
SECONDS_PER_FOUR_HOURS = Decimal("14400.000000")

EDGE_DECAY_STATUSES = ("clear", "watch", "blocked")
EDGE_DECAY_STATUS_PRIORITY = {
    "blocked": 0,
    "watch": 1,
    "clear": 2,
}
POLICY_REASON_CODES = frozenset(
    (
        "resolution_window_compressed",
        "last_forecast_stale",
        "information_velocity_high",
        "probability_volatility_high",
        "source_stale",
        "edge_decayed_below_floor",
    ),
)


@dataclass(frozen=True)
class StrategyEdgeDecayPolicyConfig:
    config_version: str = DEFAULT_STRATEGY_EDGE_DECAY_POLICY_CONFIG_VERSION
    resolution_decay_horizon: Decimal = SECONDS_PER_TWO_DAYS
    compressed_resolution_window: Decimal = SECONDS_PER_DAY
    forecast_age_decay_horizon: Decimal = SECONDS_PER_THREE_HOURS
    stale_forecast_age: Decimal = Decimal("3600.000000")
    source_staleness_decay_horizon: Decimal = SECONDS_PER_FOUR_HOURS
    stale_source_age: Decimal = Decimal("7200.000000")
    probability_volatility_decay_horizon: Decimal = Decimal("0.200000")
    high_information_velocity: Decimal = Decimal("0.800000")
    high_probability_volatility: Decimal = Decimal("0.100000")
    base_decay_ratio: Decimal = Decimal("0.169018")
    resolution_pressure_weight: Decimal = Decimal("0.279643")
    forecast_age_weight: Decimal = Decimal("0.180000")
    information_velocity_weight: Decimal = Decimal("0.200000")
    probability_volatility_weight: Decimal = Decimal("0.100000")
    source_staleness_weight: Decimal = Decimal("0.050000")
    max_edge_decay_ratio: Decimal = Decimal("0.900000")
    watch_edge_decay_ratio: Decimal = Decimal("0.500000")
    blocked_edge_decay_ratio: Decimal = Decimal("0.850000")
    minimum_decayed_edge_per_share: Decimal = Decimal("0.020000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyEdgeDecayPolicyConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_STRATEGY_EDGE_DECAY_POLICY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "resolution_decay_horizon",
            "compressed_resolution_window",
            "forecast_age_decay_horizon",
            "stale_forecast_age",
            "source_staleness_decay_horizon",
            "stale_source_age",
            "probability_volatility_decay_horizon",
            "base_decay_ratio",
            "resolution_pressure_weight",
            "forecast_age_weight",
            "information_velocity_weight",
            "probability_volatility_weight",
            "source_staleness_weight",
            "minimum_decayed_edge_per_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_information_velocity",
            "high_probability_volatility",
            "max_edge_decay_ratio",
            "watch_edge_decay_ratio",
            "blocked_edge_decay_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.resolution_decay_horizon == ZERO:
            raise ValueError("resolution_decay_horizon must be greater than zero")
        if self.forecast_age_decay_horizon == ZERO:
            raise ValueError("forecast_age_decay_horizon must be greater than zero")
        if self.source_staleness_decay_horizon == ZERO:
            raise ValueError("source_staleness_decay_horizon must be greater than zero")
        if self.probability_volatility_decay_horizon == ZERO:
            raise ValueError("probability_volatility_decay_horizon must be greater than zero")
        if self.watch_edge_decay_ratio > self.blocked_edge_decay_ratio:
            raise ValueError("watch_edge_decay_ratio must not exceed blocked_edge_decay_ratio")
        if self.blocked_edge_decay_ratio > self.max_edge_decay_ratio:
            raise ValueError("blocked_edge_decay_ratio must not exceed max_edge_decay_ratio")
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyEdgeDecayPolicyInput:
    signal_id: str
    market_slug: str
    side: str
    edge_per_share: Decimal
    time_to_resolution: Decimal
    last_forecast_age: Decimal
    information_velocity: Decimal
    probability_volatility: Decimal
    source_staleness: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyEdgeDecayPolicyInput, "input")
        _require_canonical_string("signal_id", self.signal_id)
        _require_canonical_string("market_slug", self.market_slug)
        if self.side not in ("yes", "no"):
            raise ValueError("side must be yes or no")
        for field_name in (
            "edge_per_share",
            "time_to_resolution",
            "last_forecast_age",
            "source_staleness",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("information_velocity", "probability_volatility"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyEdgeDecayPolicyRow:
    signal_id: str
    market_slug: str
    side: str
    edge_per_share: Decimal
    time_to_resolution: Decimal
    last_forecast_age: Decimal
    information_velocity: Decimal
    probability_volatility: Decimal
    source_staleness: Decimal
    edge_decay_ratio: Decimal
    decayed_edge_per_share: Decimal
    edge_decay_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyEdgeDecayPolicyRow, "row")
        _require_canonical_string("signal_id", self.signal_id)
        _require_canonical_string("market_slug", self.market_slug)
        if self.side not in ("yes", "no"):
            raise ValueError("side must be yes or no")
        for field_name in (
            "edge_per_share",
            "time_to_resolution",
            "last_forecast_age",
            "source_staleness",
            "decayed_edge_per_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "information_velocity",
            "probability_volatility",
            "edge_decay_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("edge_decay_status", self.edge_decay_status, EDGE_DECAY_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyEdgeDecayPolicyReport:
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    clear_count: Decimal
    max_edge_decay_ratio: Decimal
    average_edge_decay_ratio: Decimal
    rows: tuple[StrategyEdgeDecayPolicyRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyEdgeDecayPolicyReport, "report")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_STRATEGY_EDGE_DECAY_POLICY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "clear_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_edge_decay_ratio", "average_edge_decay_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_strategy_edge_decay_policy_report(
    signals: Iterable[StrategyEdgeDecayPolicyInput],
    *,
    config: StrategyEdgeDecayPolicyConfig,
) -> StrategyEdgeDecayPolicyReport:
    if type(config) is not StrategyEdgeDecayPolicyConfig:
        raise ValueError("config must be exactly StrategyEdgeDecayPolicyConfig")
    _require_safety_flags(config)
    normalized_signals = _normalize_inputs(signals)
    rows = tuple(
        sorted(
            (_row_from_input(value, config=config) for value in normalized_signals),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    return StrategyEdgeDecayPolicyReport(
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized_signals)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        clear_count=_status_count(rows, "clear"),
        max_edge_decay_ratio=_max_decimal((row.edge_decay_ratio for row in rows), ZERO),
        average_edge_decay_ratio=_ratio(
            _sum_decimal(row.edge_decay_ratio for row in rows),
            row_count,
        ),
        rows=rows,
    )


def strategy_edge_decay_policy_report_to_payload(
    report: StrategyEdgeDecayPolicyReport,
) -> dict[str, Any]:
    if type(report) is not StrategyEdgeDecayPolicyReport:
        raise ValueError("report must be exactly StrategyEdgeDecayPolicyReport")
    return _payload_value(report)


def _row_from_input(
    value: StrategyEdgeDecayPolicyInput,
    *,
    config: StrategyEdgeDecayPolicyConfig,
) -> StrategyEdgeDecayPolicyRow:
    edge_decay_ratio = _edge_decay_ratio(value, config)
    decayed_edge_per_share = _normalize_nonnegative_decimal(
        "decayed_edge_per_share",
        value.edge_per_share * (ONE - edge_decay_ratio),
    )
    reason_codes = _row_reason_codes(
        value,
        edge_decay_ratio=edge_decay_ratio,
        decayed_edge_per_share=decayed_edge_per_share,
        config=config,
    )
    return StrategyEdgeDecayPolicyRow(
        signal_id=value.signal_id,
        market_slug=value.market_slug,
        side=value.side,
        edge_per_share=value.edge_per_share,
        time_to_resolution=value.time_to_resolution,
        last_forecast_age=value.last_forecast_age,
        information_velocity=value.information_velocity,
        probability_volatility=value.probability_volatility,
        source_staleness=value.source_staleness,
        edge_decay_ratio=edge_decay_ratio,
        decayed_edge_per_share=decayed_edge_per_share,
        edge_decay_status=_edge_decay_status(
            edge_decay_ratio,
            decayed_edge_per_share=decayed_edge_per_share,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _edge_decay_ratio(
    value: StrategyEdgeDecayPolicyInput,
    config: StrategyEdgeDecayPolicyConfig,
) -> Decimal:
    resolution_pressure = _resolution_pressure(value.time_to_resolution, config)
    forecast_age_pressure = _capped_ratio(
        value.last_forecast_age,
        config.forecast_age_decay_horizon,
    )
    source_staleness_pressure = _capped_ratio(
        value.source_staleness,
        config.source_staleness_decay_horizon,
    )
    probability_volatility_pressure = _capped_ratio(
        value.probability_volatility,
        config.probability_volatility_decay_horizon,
    )
    with localcontext(DECIMAL_CONTEXT):
        raw_decay_ratio = (
            config.base_decay_ratio
            + (resolution_pressure * config.resolution_pressure_weight)
            + (forecast_age_pressure * config.forecast_age_weight)
            + (value.information_velocity * config.information_velocity_weight)
            + (probability_volatility_pressure * config.probability_volatility_weight)
            + (source_staleness_pressure * config.source_staleness_weight)
        )
    return _normalize_probability(
        "edge_decay_ratio",
        min(config.max_edge_decay_ratio, max(ZERO, raw_decay_ratio)),
    )


def _resolution_pressure(
    time_to_resolution: Decimal,
    config: StrategyEdgeDecayPolicyConfig,
) -> Decimal:
    if time_to_resolution >= config.resolution_decay_horizon:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "resolution_pressure",
            (config.resolution_decay_horizon - time_to_resolution)
            / config.resolution_decay_horizon,
        )


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        ratio = numerator / denominator
    return _normalize_probability("ratio", min(ONE, max(ZERO, ratio)))


def _edge_decay_status(
    edge_decay_ratio: Decimal,
    *,
    decayed_edge_per_share: Decimal,
    config: StrategyEdgeDecayPolicyConfig,
) -> str:
    if (
        edge_decay_ratio >= config.blocked_edge_decay_ratio
        or decayed_edge_per_share < config.minimum_decayed_edge_per_share
    ):
        return "blocked"
    if edge_decay_ratio >= config.watch_edge_decay_ratio:
        return "watch"
    return "clear"


def _row_reason_codes(
    value: StrategyEdgeDecayPolicyInput,
    *,
    edge_decay_ratio: Decimal,
    decayed_edge_per_share: Decimal,
    config: StrategyEdgeDecayPolicyConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if value.time_to_resolution <= config.compressed_resolution_window:
        _append_reason_code(reason_codes, "resolution_window_compressed")
    if value.last_forecast_age >= config.stale_forecast_age:
        _append_reason_code(reason_codes, "last_forecast_stale")
    if value.information_velocity >= config.high_information_velocity:
        _append_reason_code(reason_codes, "information_velocity_high")
    if value.probability_volatility >= config.high_probability_volatility:
        _append_reason_code(reason_codes, "probability_volatility_high")
    if value.source_staleness >= config.stale_source_age:
        _append_reason_code(reason_codes, "source_stale")
    if decayed_edge_per_share < config.minimum_decayed_edge_per_share:
        _append_reason_code(reason_codes, "edge_decayed_below_floor")
    for reason_code in value.reason_codes:
        _append_reason_code(reason_codes, reason_code)
    if not reason_codes and edge_decay_ratio >= config.watch_edge_decay_ratio:
        _append_reason_code(reason_codes, "edge_decayed_below_floor")
    return tuple(reason_codes)


def _validate_row_consistency(row: StrategyEdgeDecayPolicyRow) -> None:
    expected_status = _edge_decay_status(
        row.edge_decay_ratio,
        decayed_edge_per_share=row.decayed_edge_per_share,
        config=StrategyEdgeDecayPolicyConfig(),
    )
    if row.edge_decay_status != expected_status:
        raise ValueError("edge_decay_status is inconsistent with row values")
    with localcontext(DECIMAL_CONTEXT):
        expected_decayed_edge = _normalize_nonnegative_decimal(
            "decayed_edge_per_share",
            row.edge_per_share * (ONE - row.edge_decay_ratio),
        )
    if row.decayed_edge_per_share != expected_decayed_edge:
        raise ValueError("decayed_edge_per_share is inconsistent with edge_decay_ratio")
    required_reason_codes = _required_row_reason_codes(row)
    if not set(required_reason_codes).issubset(row.reason_codes):
        raise ValueError("reason_codes are inconsistent with row values")


def _required_row_reason_codes(row: StrategyEdgeDecayPolicyRow) -> tuple[str, ...]:
    config = StrategyEdgeDecayPolicyConfig()
    reason_codes: list[str] = []
    if row.time_to_resolution <= config.compressed_resolution_window:
        _append_reason_code(reason_codes, "resolution_window_compressed")
    if row.last_forecast_age >= config.stale_forecast_age:
        _append_reason_code(reason_codes, "last_forecast_stale")
    if row.information_velocity >= config.high_information_velocity:
        _append_reason_code(reason_codes, "information_velocity_high")
    if row.probability_volatility >= config.high_probability_volatility:
        _append_reason_code(reason_codes, "probability_volatility_high")
    if row.source_staleness >= config.stale_source_age:
        _append_reason_code(reason_codes, "source_stale")
    if row.decayed_edge_per_share < config.minimum_decayed_edge_per_share:
        _append_reason_code(reason_codes, "edge_decayed_below_floor")
    if row.edge_decay_status != "clear" and not reason_codes:
        raise ValueError("reason_codes must include at least one policy reason")
    return tuple(reason_codes)


def _validate_report_consistency(report: StrategyEdgeDecayPolicyReport) -> None:
    row_count = _count_decimal(len(report.rows))
    if report.row_count != row_count:
        raise ValueError("row_count must equal number of rows")
    if report.input_count != row_count:
        raise ValueError("input_count must equal number of normalized inputs")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count is inconsistent with rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count is inconsistent with rows")
    if report.clear_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_count is inconsistent with rows")
    if report.blocked_count + report.watch_count + report.clear_count != row_count:
        raise ValueError("status counts must sum to row_count")
    if report.max_edge_decay_ratio != _max_decimal(
        (row.edge_decay_ratio for row in report.rows),
        ZERO,
    ):
        raise ValueError("max_edge_decay_ratio is inconsistent with rows")
    if report.average_edge_decay_ratio != _ratio(
        _sum_decimal(row.edge_decay_ratio for row in report.rows),
        row_count,
    ):
        raise ValueError("average_edge_decay_ratio is inconsistent with rows")


def _normalize_inputs(
    values: Iterable[StrategyEdgeDecayPolicyInput],
) -> tuple[StrategyEdgeDecayPolicyInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable of StrategyEdgeDecayPolicyInput")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of StrategyEdgeDecayPolicyInput") from exc
    for value in normalized:
        if type(value) is not StrategyEdgeDecayPolicyInput:
            raise ValueError("inputs must contain only StrategyEdgeDecayPolicyInput")
        _require_safety_flags(value)
    return normalized


def _normalize_rows(
    values: tuple[StrategyEdgeDecayPolicyRow, ...],
) -> tuple[StrategyEdgeDecayPolicyRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    for value in values:
        if type(value) is not StrategyEdgeDecayPolicyRow:
            raise ValueError("rows must contain only StrategyEdgeDecayPolicyRow")
        _require_safety_flags(value)
    return values


def _row_sort_key(row: StrategyEdgeDecayPolicyRow) -> tuple[int, Decimal, str, str]:
    return (
        EDGE_DECAY_STATUS_PRIORITY[row.edge_decay_status],
        -row.edge_decay_ratio,
        row.market_slug,
        row.signal_id,
    )


def _status_count(rows: tuple[StrategyEdgeDecayPolicyRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.edge_decay_status == status))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _normalize_nonnegative_decimal("total", total)


def _max_decimal(values: Iterable[Decimal], default: Decimal) -> Decimal:
    return _normalize_probability("max_decimal", max(tuple(values), default=default))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("ratio", numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_member(field_name: str, value: str, valid_values: tuple[str, ...]) -> None:
    if value not in valid_values:
        raise ValueError(f"{field_name} must be one of {valid_values}")


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_exact_type(value: object, expected_type: type[object], value_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{value_name} must be exactly {expected_type.__name__}")


def _require_safety_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name, None)
        _require_bool(field_name, flag)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes: list[str] = []
    for value in values:
        _require_canonical_string("reason_code", value)
        _append_reason_code(reason_codes, value)
    return tuple(reason_codes)


def _append_reason_code(reason_codes: list[str], reason_code: str) -> None:
    if reason_code not in reason_codes:
        reason_codes.append(reason_code)


def _payload_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value.quantize(QUANTUM))
    if hasattr(value, "__dataclass_fields__"):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(child) for child in value]
    if isinstance(value, list):
        return [_payload_value(child) for child in value]
    return value


__all__ = [
    "DEFAULT_STRATEGY_EDGE_DECAY_POLICY_CONFIG_VERSION",
    "EDGE_DECAY_STATUSES",
    "StrategyEdgeDecayPolicyConfig",
    "StrategyEdgeDecayPolicyInput",
    "StrategyEdgeDecayPolicyReport",
    "StrategyEdgeDecayPolicyRow",
    "build_strategy_edge_decay_policy_report",
    "strategy_edge_decay_policy_report_to_payload",
]
