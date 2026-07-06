"""Pure read-only probability tail-risk v6 report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_PROBABILITY_TAIL_RISK_V6_CONFIG_VERSION = (
    "strategy-probability-tail-risk-v6"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

TAIL_RISK_STATUSES = ("pass", "watch", "block")
PASS_REASON = "probability_tail_risk_v6_pass"
PROBABILITY_GAP_WATCH_REASON = "probability_gap_watch"
PROBABILITY_GAP_BLOCK_REASON = "probability_gap_block"
RESOLUTION_RISK_WATCH_REASON = "resolution_risk_watch"
RESOLUTION_RISK_BLOCK_REASON = "resolution_risk_block"
SOURCE_CONFLICT_WATCH_REASON = "source_conflict_watch"
SOURCE_CONFLICT_BLOCK_REASON = "source_conflict_block"
LIQUIDITY_DEPTH_WATCH_REASON = "liquidity_depth_watch"
LIQUIDITY_DEPTH_BLOCK_REASON = "liquidity_depth_block"
TIME_TO_RESOLUTION_WATCH_REASON = "time_to_resolution_watch"
TIME_TO_RESOLUTION_BLOCK_REASON = "time_to_resolution_block"
TAIL_RISK_SCORE_WATCH_REASON = "tail_risk_score_watch"
TAIL_RISK_SCORE_BLOCK_REASON = "tail_risk_score_block"

REASON_PRIORITY = (
    PROBABILITY_GAP_BLOCK_REASON,
    RESOLUTION_RISK_BLOCK_REASON,
    SOURCE_CONFLICT_BLOCK_REASON,
    LIQUIDITY_DEPTH_BLOCK_REASON,
    TIME_TO_RESOLUTION_BLOCK_REASON,
    TAIL_RISK_SCORE_BLOCK_REASON,
    PROBABILITY_GAP_WATCH_REASON,
    RESOLUTION_RISK_WATCH_REASON,
    SOURCE_CONFLICT_WATCH_REASON,
    LIQUIDITY_DEPTH_WATCH_REASON,
    TIME_TO_RESOLUTION_WATCH_REASON,
    TAIL_RISK_SCORE_WATCH_REASON,
    PASS_REASON,
)
BLOCK_REASONS = frozenset(
    (
        PROBABILITY_GAP_BLOCK_REASON,
        RESOLUTION_RISK_BLOCK_REASON,
        SOURCE_CONFLICT_BLOCK_REASON,
        LIQUIDITY_DEPTH_BLOCK_REASON,
        TIME_TO_RESOLUTION_BLOCK_REASON,
        TAIL_RISK_SCORE_BLOCK_REASON,
    ),
)
WATCH_REASONS = frozenset(
    (
        PROBABILITY_GAP_WATCH_REASON,
        RESOLUTION_RISK_WATCH_REASON,
        SOURCE_CONFLICT_WATCH_REASON,
        LIQUIDITY_DEPTH_WATCH_REASON,
        TIME_TO_RESOLUTION_WATCH_REASON,
        TAIL_RISK_SCORE_WATCH_REASON,
    ),
)


@dataclass(frozen=True)
class StrategyProbabilityTailRiskV6Config:
    config_version: str = DEFAULT_STRATEGY_PROBABILITY_TAIL_RISK_V6_CONFIG_VERSION
    watch_tail_risk_score: Decimal = Decimal("0.350000")
    block_tail_risk_score: Decimal = Decimal("0.700000")
    watch_probability_gap: Decimal = Decimal("0.100000")
    block_probability_gap: Decimal = Decimal("0.250000")
    watch_resolution_risk: Decimal = Decimal("0.350000")
    block_resolution_risk: Decimal = Decimal("0.700000")
    watch_source_conflict: Decimal = Decimal("0.350000")
    block_source_conflict: Decimal = Decimal("0.700000")
    watch_liquidity_depth: Decimal = Decimal("0.700000")
    block_liquidity_depth: Decimal = Decimal("0.250000")
    near_resolution_window: Decimal = Decimal("24.000000")
    watch_time_to_resolution_risk: Decimal = Decimal("0.350000")
    block_time_to_resolution_risk: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_tail_risk_score",
            "block_tail_risk_score",
            "watch_probability_gap",
            "block_probability_gap",
            "watch_resolution_risk",
            "block_resolution_risk",
            "watch_source_conflict",
            "block_source_conflict",
            "watch_liquidity_depth",
            "block_liquidity_depth",
            "watch_time_to_resolution_risk",
            "block_time_to_resolution_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "near_resolution_window",
            _normalize_positive_decimal(
                "near_resolution_window",
                self.near_resolution_window,
            ),
        )
        _require_ascending_threshold(
            "block_tail_risk_score",
            self.watch_tail_risk_score,
            self.block_tail_risk_score,
        )
        _require_ascending_threshold(
            "block_probability_gap",
            self.watch_probability_gap,
            self.block_probability_gap,
        )
        _require_ascending_threshold(
            "block_resolution_risk",
            self.watch_resolution_risk,
            self.block_resolution_risk,
        )
        _require_ascending_threshold(
            "block_source_conflict",
            self.watch_source_conflict,
            self.block_source_conflict,
        )
        _require_descending_threshold(
            "block_liquidity_depth",
            self.watch_liquidity_depth,
            self.block_liquidity_depth,
        )
        _require_ascending_threshold(
            "block_time_to_resolution_risk",
            self.watch_time_to_resolution_risk,
            self.block_time_to_resolution_risk,
        )
        require_paper_only_flags("strategy probability tail risk v6 config", self)


@dataclass(frozen=True)
class StrategyProbabilityTailRiskV6Input:
    forecast_probability: Decimal
    market_probability: Decimal
    resolution_risk: Decimal
    source_conflict: Decimal
    liquidity_depth: Decimal
    time_to_resolution: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "forecast_probability",
            "market_probability",
            "resolution_risk",
            "source_conflict",
            "liquidity_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "time_to_resolution",
            _normalize_nonnegative_decimal(
                "time_to_resolution",
                self.time_to_resolution,
            ),
        )
        require_paper_only_flags("strategy probability tail risk v6 input", self)


@dataclass(frozen=True)
class StrategyProbabilityTailRiskV6Report:
    generated_at: datetime
    config_version: str
    forecast_probability: Decimal
    market_probability: Decimal
    probability_gap: Decimal
    resolution_risk: Decimal
    source_conflict: Decimal
    liquidity_depth: Decimal
    liquidity_depth_risk: Decimal
    time_to_resolution: Decimal
    time_to_resolution_risk: Decimal
    tail_risk_score: Decimal
    tail_risk_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "forecast_probability",
            "market_probability",
            "probability_gap",
            "resolution_risk",
            "source_conflict",
            "liquidity_depth",
            "liquidity_depth_risk",
            "time_to_resolution_risk",
            "tail_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "time_to_resolution",
            _normalize_nonnegative_decimal(
                "time_to_resolution",
                self.time_to_resolution,
            ),
        )
        _require_member("tail_risk_status", self.tail_risk_status, TAIL_RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("strategy probability tail risk v6 report", self)


def build_strategy_probability_tail_risk_v6_report(
    input_value: StrategyProbabilityTailRiskV6Input,
    *,
    config: StrategyProbabilityTailRiskV6Config,
    generated_at: datetime,
) -> StrategyProbabilityTailRiskV6Report:
    if type(input_value) is not StrategyProbabilityTailRiskV6Input:
        raise ValueError("input_value must be a StrategyProbabilityTailRiskV6Input")
    if type(config) is not StrategyProbabilityTailRiskV6Config:
        raise ValueError("config must be a StrategyProbabilityTailRiskV6Config")
    require_paper_only_flags("strategy probability tail risk v6 input", input_value)
    require_paper_only_flags("strategy probability tail risk v6 config", config)

    probability_gap = _absolute_difference(
        input_value.forecast_probability,
        input_value.market_probability,
    )
    liquidity_depth_risk = _quantize(ONE - input_value.liquidity_depth)
    time_to_resolution_risk = _time_to_resolution_risk(input_value, config)
    tail_risk_score = _max_decimal(
        (
            probability_gap,
            input_value.resolution_risk,
            input_value.source_conflict,
            liquidity_depth_risk,
            time_to_resolution_risk,
        ),
    )
    reason_codes = _reason_codes(
        input_value,
        config,
        probability_gap=probability_gap,
        liquidity_depth_risk=liquidity_depth_risk,
        time_to_resolution_risk=time_to_resolution_risk,
        tail_risk_score=tail_risk_score,
    )
    return StrategyProbabilityTailRiskV6Report(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        forecast_probability=input_value.forecast_probability,
        market_probability=input_value.market_probability,
        probability_gap=probability_gap,
        resolution_risk=input_value.resolution_risk,
        source_conflict=input_value.source_conflict,
        liquidity_depth=input_value.liquidity_depth,
        liquidity_depth_risk=liquidity_depth_risk,
        time_to_resolution=input_value.time_to_resolution,
        time_to_resolution_risk=time_to_resolution_risk,
        tail_risk_score=tail_risk_score,
        tail_risk_status=_tail_risk_status(reason_codes),
        reason_codes=reason_codes,
    )


def strategy_probability_tail_risk_v6_payload(
    report: StrategyProbabilityTailRiskV6Report,
) -> dict[str, Any]:
    if type(report) is not StrategyProbabilityTailRiskV6Report:
        raise ValueError("report must be a StrategyProbabilityTailRiskV6Report")
    require_paper_only_flags("strategy probability tail risk v6 report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    require_paper_only_flags("strategy probability tail risk v6 payload", _PayloadFlags(payload))
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
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


def _reason_codes(
    input_value: StrategyProbabilityTailRiskV6Input,
    config: StrategyProbabilityTailRiskV6Config,
    *,
    probability_gap: Decimal,
    liquidity_depth_risk: Decimal,
    time_to_resolution_risk: Decimal,
    tail_risk_score: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_threshold_reason(
        codes,
        probability_gap,
        config.watch_probability_gap,
        config.block_probability_gap,
        PROBABILITY_GAP_WATCH_REASON,
        PROBABILITY_GAP_BLOCK_REASON,
    )
    _append_threshold_reason(
        codes,
        input_value.resolution_risk,
        config.watch_resolution_risk,
        config.block_resolution_risk,
        RESOLUTION_RISK_WATCH_REASON,
        RESOLUTION_RISK_BLOCK_REASON,
    )
    _append_threshold_reason(
        codes,
        input_value.source_conflict,
        config.watch_source_conflict,
        config.block_source_conflict,
        SOURCE_CONFLICT_WATCH_REASON,
        SOURCE_CONFLICT_BLOCK_REASON,
    )
    if input_value.liquidity_depth <= config.block_liquidity_depth:
        codes.append(LIQUIDITY_DEPTH_BLOCK_REASON)
    elif input_value.liquidity_depth <= config.watch_liquidity_depth:
        codes.append(LIQUIDITY_DEPTH_WATCH_REASON)
    _append_threshold_reason(
        codes,
        time_to_resolution_risk,
        config.watch_time_to_resolution_risk,
        config.block_time_to_resolution_risk,
        TIME_TO_RESOLUTION_WATCH_REASON,
        TIME_TO_RESOLUTION_BLOCK_REASON,
    )
    if not any(code in BLOCK_REASONS for code in codes):
        if tail_risk_score >= config.block_tail_risk_score:
            codes.append(TAIL_RISK_SCORE_BLOCK_REASON)
        elif not codes and tail_risk_score >= config.watch_tail_risk_score:
            codes.append(TAIL_RISK_SCORE_WATCH_REASON)
    if not codes:
        codes.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _append_threshold_reason(
    codes: list[str],
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value >= block_value:
        codes.append(block_reason)
    elif value >= watch_value:
        codes.append(watch_reason)


def _tail_risk_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _time_to_resolution_risk(
    input_value: StrategyProbabilityTailRiskV6Input,
    config: StrategyProbabilityTailRiskV6Config,
) -> Decimal:
    if input_value.time_to_resolution >= config.near_resolution_window:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (config.near_resolution_window - input_value.time_to_resolution)
            / config.near_resolution_window,
        )


def _validate_report(report: StrategyProbabilityTailRiskV6Report) -> None:
    if report.probability_gap != _absolute_difference(
        report.forecast_probability,
        report.market_probability,
    ):
        raise ValueError("probability_gap must match forecast_probability and market_probability")
    if report.liquidity_depth_risk != _quantize(ONE - report.liquidity_depth):
        raise ValueError("liquidity_depth_risk must match liquidity_depth")
    if report.tail_risk_score != _max_decimal(
        (
            report.probability_gap,
            report.resolution_risk,
            report.source_conflict,
            report.liquidity_depth_risk,
            report.time_to_resolution_risk,
        ),
    ):
        raise ValueError("tail_risk_score must match risk inputs")
    if report.tail_risk_status != _tail_risk_status(report.reason_codes):
        raise ValueError("tail_risk_status must match reason_codes")
    if report.tail_risk_status == "pass" and PASS_REASON not in report.reason_codes:
        raise ValueError("pass report must include pass reason")
    if report.tail_risk_status != "pass" and PASS_REASON in report.reason_codes:
        raise ValueError("non-pass report must not include pass reason")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
        if reason_code not in REASON_PRIORITY:
            raise ValueError(f"{field_name} must contain known reason codes")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in REASON_PRIORITY if reason_code in seen)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part.lower() != part:
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _absolute_difference(left: Decimal, right: Decimal) -> Decimal:
    if left >= right:
        return _quantize(left - right)
    return _quantize(right - left)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    current = ZERO
    for value in values:
        if value > current:
            current = value
    return _quantize(current)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


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


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_ascending_threshold(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value < watch_value:
        raise ValueError(f"{field_name} must be at least watch threshold")


def _require_descending_threshold(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value > watch_value:
        raise ValueError(f"{field_name} must not exceed watch threshold")


__all__ = (
    "DEFAULT_STRATEGY_PROBABILITY_TAIL_RISK_V6_CONFIG_VERSION",
    "StrategyProbabilityTailRiskV6Config",
    "StrategyProbabilityTailRiskV6Input",
    "StrategyProbabilityTailRiskV6Report",
    "build_strategy_probability_tail_risk_v6_report",
    "strategy_probability_tail_risk_v6_payload",
)
