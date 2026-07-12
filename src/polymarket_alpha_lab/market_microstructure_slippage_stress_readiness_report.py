"""Pure in-memory market microstructure slippage stress readiness report."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_MICROSTRUCTURE_SLIPPAGE_STRESS_READINESS_CONFIG_VERSION = (
    "market-microstructure-slippage-stress-readiness-v0"
)

STRESS_STATUSES = ("ready", "watch", "blocked")
REASON_CODES = (
    "slippage_stress_ready",
    "spread_probability_block",
    "spread_probability_watch",
    "depth_probability_block",
    "depth_probability_watch",
    "depth_coverage_block",
    "depth_coverage_watch",
    "slippage_probability_block",
    "slippage_probability_watch",
    "exit_depth_probability_block",
    "exit_depth_probability_watch",
)
MANUAL_NEXT_STEPS = (
    "manual_filter_pass_liquidity_slippage_stress",
    "manual_review_microstructure_stress_before_shortlist",
    "manual_exclude_until_depth_or_slippage_stress_improves",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


__all__ = (
    "DEFAULT_MARKET_MICROSTRUCTURE_SLIPPAGE_STRESS_READINESS_CONFIG_VERSION",
    "MarketMicrostructureSlippageStressReadinessConfig",
    "MarketMicrostructureSlippageStressInput",
    "MarketMicrostructureSlippageStressReadinessReport",
    "build_market_microstructure_slippage_stress_readiness_report",
    "market_microstructure_slippage_stress_readiness_payload",
)


@dataclass(frozen=True)
class MarketMicrostructureSlippageStressReadinessConfig:
    config_version: str = (
        DEFAULT_MARKET_MICROSTRUCTURE_SLIPPAGE_STRESS_READINESS_CONFIG_VERSION
    )
    min_ready_spread_probability: Decimal = Decimal("0.750000")
    min_watch_spread_probability: Decimal = Decimal("0.500000")
    min_ready_depth_probability: Decimal = Decimal("0.750000")
    min_watch_depth_probability: Decimal = Decimal("0.500000")
    max_ready_slippage_probability: Decimal = Decimal("0.100000")
    max_watch_slippage_probability: Decimal = Decimal("0.250000")
    min_ready_exit_depth_probability: Decimal = Decimal("0.750000")
    min_watch_exit_depth_probability: Decimal = Decimal("0.500000")
    min_ready_depth_coverage_ratio: Decimal = Decimal("2.000000")
    min_watch_depth_coverage_ratio: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_string("config_version", self.config_version)
        for field_name in (
            "min_ready_spread_probability",
            "min_watch_spread_probability",
            "min_ready_depth_probability",
            "min_watch_depth_probability",
            "max_ready_slippage_probability",
            "max_watch_slippage_probability",
            "min_ready_exit_depth_probability",
            "min_watch_exit_depth_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_ready_depth_coverage_ratio",
            "min_watch_depth_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags(
            "MarketMicrostructureSlippageStressReadinessConfig",
            self,
        )


@dataclass(frozen=True)
class MarketMicrostructureSlippageStressInput:
    spread_probability: Decimal
    depth_probability: Decimal
    expected_trade_notional: Decimal
    available_depth: Decimal
    slippage_probability: Decimal
    exit_depth_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "spread_probability",
            "depth_probability",
            "slippage_probability",
            "exit_depth_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_trade_notional",
            _normalize_positive_decimal(
                "expected_trade_notional",
                self.expected_trade_notional,
            ),
        )
        object.__setattr__(
            self,
            "available_depth",
            _normalize_nonnegative_decimal("available_depth", self.available_depth),
        )
        require_paper_only_flags("MarketMicrostructureSlippageStressInput", self)


@dataclass(frozen=True)
class MarketMicrostructureSlippageStressReadinessReport:
    generated_at: datetime
    config_version: str
    spread_probability: Decimal
    depth_probability: Decimal
    expected_trade_notional: Decimal
    available_depth: Decimal
    depth_coverage_ratio: Decimal
    slippage_probability: Decimal
    exit_depth_probability: Decimal
    stress_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    payload: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_string("config_version", self.config_version)
        for field_name in (
            "spread_probability",
            "depth_probability",
            "slippage_probability",
            "exit_depth_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_trade_notional",
            _normalize_positive_decimal(
                "expected_trade_notional",
                self.expected_trade_notional,
            ),
        )
        object.__setattr__(
            self,
            "available_depth",
            _normalize_nonnegative_decimal("available_depth", self.available_depth),
        )
        object.__setattr__(
            self,
            "depth_coverage_ratio",
            _normalize_nonnegative_decimal(
                "depth_coverage_ratio",
                self.depth_coverage_ratio,
            ),
        )
        _require_member("stress_status", self.stress_status, STRESS_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_member("manual_next_step", self.manual_next_step, MANUAL_NEXT_STEPS)
        require_paper_only_flags(
            "MarketMicrostructureSlippageStressReadinessReport",
            self,
        )
        _validate_report(self)
        reject_unsafe_surface_fields(
            "market microstructure slippage stress readiness report",
            self,
        )
        object.__setattr__(self, "payload", _report_payload(self))


def build_market_microstructure_slippage_stress_readiness_report(
    stress_input: MarketMicrostructureSlippageStressInput,
    *,
    config: MarketMicrostructureSlippageStressReadinessConfig,
    generated_at: datetime,
) -> MarketMicrostructureSlippageStressReadinessReport:
    if type(stress_input) is not MarketMicrostructureSlippageStressInput:
        raise ValueError(
            "stress_input must be a MarketMicrostructureSlippageStressInput",
        )
    if type(config) is not MarketMicrostructureSlippageStressReadinessConfig:
        raise ValueError(
            "config must be a MarketMicrostructureSlippageStressReadinessConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    depth_coverage_ratio = _depth_coverage_ratio(
        stress_input.available_depth,
        stress_input.expected_trade_notional,
    )
    reason_codes = _reason_codes(
        stress_input,
        config,
        depth_coverage_ratio=depth_coverage_ratio,
    )
    stress_status = _stress_status(reason_codes)
    return MarketMicrostructureSlippageStressReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        spread_probability=stress_input.spread_probability,
        depth_probability=stress_input.depth_probability,
        expected_trade_notional=stress_input.expected_trade_notional,
        available_depth=stress_input.available_depth,
        depth_coverage_ratio=depth_coverage_ratio,
        slippage_probability=stress_input.slippage_probability,
        exit_depth_probability=stress_input.exit_depth_probability,
        stress_status=stress_status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(stress_status),
    )


def market_microstructure_slippage_stress_readiness_payload(
    report: MarketMicrostructureSlippageStressReadinessReport,
) -> dict[str, Any]:
    if type(report) is not MarketMicrostructureSlippageStressReadinessReport:
        raise ValueError(
            "report must be a MarketMicrostructureSlippageStressReadinessReport",
        )
    require_paper_only_flags(
        "MarketMicrostructureSlippageStressReadinessReport",
        report,
    )
    reject_unsafe_surface_fields(
        "market microstructure slippage stress readiness payload",
        report.payload,
    )
    return report.payload


def _validate_config(
    config: MarketMicrostructureSlippageStressReadinessConfig,
) -> None:
    if config.min_ready_spread_probability < config.min_watch_spread_probability:
        raise ValueError("spread probability thresholds must be descending")
    if config.min_ready_depth_probability < config.min_watch_depth_probability:
        raise ValueError("depth probability thresholds must be descending")
    if config.min_ready_exit_depth_probability < config.min_watch_exit_depth_probability:
        raise ValueError("exit depth probability thresholds must be descending")
    if config.max_ready_slippage_probability > config.max_watch_slippage_probability:
        raise ValueError("slippage probability thresholds must be ascending")
    if config.min_ready_depth_coverage_ratio < config.min_watch_depth_coverage_ratio:
        raise ValueError("depth coverage thresholds must be descending")


def _validate_report(
    report: MarketMicrostructureSlippageStressReadinessReport,
) -> None:
    expected_depth_coverage_ratio = _depth_coverage_ratio(
        report.available_depth,
        report.expected_trade_notional,
    )
    if report.depth_coverage_ratio != expected_depth_coverage_ratio:
        raise ValueError("depth_coverage_ratio must match input fields")
    expected_reason_codes = _reason_codes_from_fields(
        spread_probability=report.spread_probability,
        depth_probability=report.depth_probability,
        depth_coverage_ratio=report.depth_coverage_ratio,
        slippage_probability=report.slippage_probability,
        exit_depth_probability=report.exit_depth_probability,
        config=MarketMicrostructureSlippageStressReadinessConfig(
            config_version=report.config_version,
        ),
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match input fields")
    expected_stress_status = _stress_status(report.reason_codes)
    if report.stress_status != expected_stress_status:
        raise ValueError("stress_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(report.stress_status):
        raise ValueError("manual_next_step must match stress_status")


def _reason_codes(
    stress_input: MarketMicrostructureSlippageStressInput,
    config: MarketMicrostructureSlippageStressReadinessConfig,
    *,
    depth_coverage_ratio: Decimal,
) -> tuple[str, ...]:
    return _reason_codes_from_fields(
        spread_probability=stress_input.spread_probability,
        depth_probability=stress_input.depth_probability,
        depth_coverage_ratio=depth_coverage_ratio,
        slippage_probability=stress_input.slippage_probability,
        exit_depth_probability=stress_input.exit_depth_probability,
        config=config,
    )


def _reason_codes_from_fields(
    *,
    spread_probability: Decimal,
    depth_probability: Decimal,
    depth_coverage_ratio: Decimal,
    slippage_probability: Decimal,
    exit_depth_probability: Decimal,
    config: MarketMicrostructureSlippageStressReadinessConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_min_threshold_reason(
        reason_codes,
        value=spread_probability,
        watch_threshold=config.min_watch_spread_probability,
        ready_threshold=config.min_ready_spread_probability,
        block_reason="spread_probability_block",
        watch_reason="spread_probability_watch",
    )
    _append_min_threshold_reason(
        reason_codes,
        value=depth_probability,
        watch_threshold=config.min_watch_depth_probability,
        ready_threshold=config.min_ready_depth_probability,
        block_reason="depth_probability_block",
        watch_reason="depth_probability_watch",
    )
    _append_min_threshold_reason(
        reason_codes,
        value=depth_coverage_ratio,
        watch_threshold=config.min_watch_depth_coverage_ratio,
        ready_threshold=config.min_ready_depth_coverage_ratio,
        block_reason="depth_coverage_block",
        watch_reason="depth_coverage_watch",
    )
    _append_max_threshold_reason(
        reason_codes,
        value=slippage_probability,
        ready_threshold=config.max_ready_slippage_probability,
        watch_threshold=config.max_watch_slippage_probability,
        block_reason="slippage_probability_block",
        watch_reason="slippage_probability_watch",
    )
    _append_min_threshold_reason(
        reason_codes,
        value=exit_depth_probability,
        watch_threshold=config.min_watch_exit_depth_probability,
        ready_threshold=config.min_ready_exit_depth_probability,
        block_reason="exit_depth_probability_block",
        watch_reason="exit_depth_probability_watch",
    )
    if not reason_codes:
        return ("slippage_stress_ready",)
    return tuple(reason_codes)


def _append_min_threshold_reason(
    reason_codes: list[str],
    *,
    value: Decimal,
    watch_threshold: Decimal,
    ready_threshold: Decimal,
    block_reason: str,
    watch_reason: str,
) -> None:
    if value < watch_threshold:
        reason_codes.append(block_reason)
    elif value < ready_threshold:
        reason_codes.append(watch_reason)


def _append_max_threshold_reason(
    reason_codes: list[str],
    *,
    value: Decimal,
    ready_threshold: Decimal,
    watch_threshold: Decimal,
    block_reason: str,
    watch_reason: str,
) -> None:
    if value > watch_threshold:
        reason_codes.append(block_reason)
    elif value > ready_threshold:
        reason_codes.append(watch_reason)


def _stress_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "ready"


def _manual_next_step(stress_status: str) -> str:
    if stress_status == "ready":
        return "manual_filter_pass_liquidity_slippage_stress"
    if stress_status == "watch":
        return "manual_review_microstructure_stress_before_shortlist"
    if stress_status == "blocked":
        return "manual_exclude_until_depth_or_slippage_stress_improves"
    raise ValueError("stress_status must be ready, watch, or blocked")


def _depth_coverage_ratio(available_depth: Decimal, expected_trade_notional: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_nonnegative_decimal(
            "depth_coverage_ratio",
            available_depth / expected_trade_notional,
        )


def _report_payload(
    report: MarketMicrostructureSlippageStressReadinessReport,
) -> dict[str, Any]:
    payload = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "spread_probability": report.spread_probability,
        "depth_probability": report.depth_probability,
        "expected_trade_notional": report.expected_trade_notional,
        "available_depth": report.available_depth,
        "depth_coverage_ratio": report.depth_coverage_ratio,
        "slippage_probability": report.slippage_probability,
        "exit_depth_probability": report.exit_depth_probability,
        "stress_status": report.stress_status,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    ready_payload = json_ready_no_floats(payload)
    if type(ready_payload) is not dict:
        raise ValueError("payload must be a JSON object")
    reject_unsafe_surface_fields(
        "market microstructure slippage stress readiness payload",
        ready_payload,
    )
    return ready_payload


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_member("reason_codes", reason_code, REASON_CODES)
    return reason_codes


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be an exact Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a str")
    if not value:
        raise ValueError(f"{field_name} must not be empty")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a str")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
