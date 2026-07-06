"""Pure read-only probability update trigger v7 report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_PROBABILITY_UPDATE_TRIGGER_V7_CONFIG_VERSION = (
    "strategy-probability-update-trigger-v7"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

TRIGGER_STATUSES = ("defer", "watch", "refresh")
DEFER_REASON = "probability_update_trigger_v7_defer"
PRICE_CHANGE_REFRESH_REASON = "price_change_refresh"
SOURCE_UPDATE_REFRESH_REASON = "source_update_refresh"
FORECAST_AGE_REFRESH_REASON = "forecast_age_refresh"
RESOLUTION_DEADLINE_REFRESH_REASON = "resolution_deadline_refresh"
VOLATILITY_REFRESH_REASON = "volatility_refresh"
SOURCE_CONFLICT_REFRESH_REASON = "source_conflict_refresh"
PRICE_CHANGE_WATCH_REASON = "price_change_watch"
SOURCE_UPDATE_WATCH_REASON = "source_update_watch"
FORECAST_AGE_WATCH_REASON = "forecast_age_watch"
RESOLUTION_DEADLINE_WATCH_REASON = "resolution_deadline_watch"
VOLATILITY_WATCH_REASON = "volatility_watch"
SOURCE_CONFLICT_WATCH_REASON = "source_conflict_watch"

REFRESH_REASONS = frozenset(
    (
        PRICE_CHANGE_REFRESH_REASON,
        SOURCE_UPDATE_REFRESH_REASON,
        FORECAST_AGE_REFRESH_REASON,
        RESOLUTION_DEADLINE_REFRESH_REASON,
        VOLATILITY_REFRESH_REASON,
        SOURCE_CONFLICT_REFRESH_REASON,
    ),
)
WATCH_REASONS = frozenset(
    (
        PRICE_CHANGE_WATCH_REASON,
        SOURCE_UPDATE_WATCH_REASON,
        FORECAST_AGE_WATCH_REASON,
        RESOLUTION_DEADLINE_WATCH_REASON,
        VOLATILITY_WATCH_REASON,
        SOURCE_CONFLICT_WATCH_REASON,
    ),
)
REASON_PRIORITY = (
    PRICE_CHANGE_REFRESH_REASON,
    SOURCE_UPDATE_REFRESH_REASON,
    FORECAST_AGE_REFRESH_REASON,
    RESOLUTION_DEADLINE_REFRESH_REASON,
    VOLATILITY_REFRESH_REASON,
    SOURCE_CONFLICT_REFRESH_REASON,
    PRICE_CHANGE_WATCH_REASON,
    SOURCE_UPDATE_WATCH_REASON,
    FORECAST_AGE_WATCH_REASON,
    RESOLUTION_DEADLINE_WATCH_REASON,
    VOLATILITY_WATCH_REASON,
    SOURCE_CONFLICT_WATCH_REASON,
    DEFER_REASON,
)


@dataclass(frozen=True)
class StrategyProbabilityUpdateTriggerV7Config:
    config_version: str = DEFAULT_STRATEGY_PROBABILITY_UPDATE_TRIGGER_V7_CONFIG_VERSION
    watch_price_change: Decimal = Decimal("0.030000")
    refresh_price_change: Decimal = Decimal("0.080000")
    watch_source_update_age_minutes: Decimal = Decimal("60.000000")
    refresh_source_update_age_minutes: Decimal = Decimal("10.000000")
    watch_forecast_age_minutes: Decimal = Decimal("30.000000")
    refresh_forecast_age_minutes: Decimal = Decimal("120.000000")
    watch_resolution_deadline_minutes: Decimal = Decimal("240.000000")
    refresh_resolution_deadline_minutes: Decimal = Decimal("60.000000")
    watch_volatility: Decimal = Decimal("0.250000")
    refresh_volatility: Decimal = Decimal("0.600000")
    watch_source_conflict: Decimal = Decimal("0.300000")
    refresh_source_conflict: Decimal = Decimal("0.650000")
    watch_next_update_minutes: Decimal = Decimal("15.000000")
    default_next_update_minutes: Decimal = Decimal("60.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_STRATEGY_PROBABILITY_UPDATE_TRIGGER_V7_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_price_change",
            "refresh_price_change",
            "watch_volatility",
            "refresh_volatility",
            "watch_source_conflict",
            "refresh_source_conflict",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_source_update_age_minutes",
            "refresh_source_update_age_minutes",
            "watch_forecast_age_minutes",
            "refresh_forecast_age_minutes",
            "watch_resolution_deadline_minutes",
            "refresh_resolution_deadline_minutes",
            "watch_next_update_minutes",
            "default_next_update_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_ascending_threshold(
            "refresh_price_change",
            self.watch_price_change,
            self.refresh_price_change,
        )
        _require_descending_threshold(
            "refresh_source_update_age_minutes",
            self.watch_source_update_age_minutes,
            self.refresh_source_update_age_minutes,
        )
        _require_ascending_threshold(
            "refresh_forecast_age_minutes",
            self.watch_forecast_age_minutes,
            self.refresh_forecast_age_minutes,
        )
        _require_descending_threshold(
            "refresh_resolution_deadline_minutes",
            self.watch_resolution_deadline_minutes,
            self.refresh_resolution_deadline_minutes,
        )
        _require_ascending_threshold(
            "refresh_volatility",
            self.watch_volatility,
            self.refresh_volatility,
        )
        _require_ascending_threshold(
            "refresh_source_conflict",
            self.watch_source_conflict,
            self.refresh_source_conflict,
        )
        reject_unsafe_surface_fields("strategy probability update trigger v7 config", self)
        require_paper_only_flags("strategy probability update trigger v7 config", self)


@dataclass(frozen=True)
class StrategyProbabilityUpdateTriggerV7Input:
    prior_market_probability: Decimal
    current_market_probability: Decimal
    source_update_age_minutes: Decimal
    forecast_age_minutes: Decimal
    minutes_to_resolution: Decimal
    volatility: Decimal
    source_conflict: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "prior_market_probability",
            "current_market_probability",
            "volatility",
            "source_conflict",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_update_age_minutes",
            "forecast_age_minutes",
            "minutes_to_resolution",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        reject_unsafe_surface_fields("strategy probability update trigger v7 input", self)
        require_paper_only_flags("strategy probability update trigger v7 input", self)


@dataclass(frozen=True)
class StrategyProbabilityUpdateTriggerV7Report:
    generated_at: datetime
    config_version: str
    prior_market_probability: Decimal
    current_market_probability: Decimal
    price_change: Decimal
    source_update_age_minutes: Decimal
    forecast_age_minutes: Decimal
    minutes_to_resolution: Decimal
    volatility: Decimal
    source_conflict: Decimal
    trigger_status: str
    next_update_minutes: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "prior_market_probability",
            "current_market_probability",
            "price_change",
            "volatility",
            "source_conflict",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_update_age_minutes",
            "forecast_age_minutes",
            "minutes_to_resolution",
            "next_update_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("trigger_status", self.trigger_status, TRIGGER_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("strategy probability update trigger v7 report", self)
        require_paper_only_flags("strategy probability update trigger v7 report", self)


def build_strategy_probability_update_trigger_v7_report(
    input_value: StrategyProbabilityUpdateTriggerV7Input,
    *,
    config: StrategyProbabilityUpdateTriggerV7Config,
    generated_at: datetime,
) -> StrategyProbabilityUpdateTriggerV7Report:
    if type(input_value) is not StrategyProbabilityUpdateTriggerV7Input:
        raise ValueError("input_value must be a StrategyProbabilityUpdateTriggerV7Input")
    if type(config) is not StrategyProbabilityUpdateTriggerV7Config:
        raise ValueError("config must be a StrategyProbabilityUpdateTriggerV7Config")
    require_paper_only_flags("strategy probability update trigger v7 input", input_value)
    require_paper_only_flags("strategy probability update trigger v7 config", config)

    price_change = _absolute_difference(
        input_value.current_market_probability,
        input_value.prior_market_probability,
    )
    reason_codes = _reason_codes(input_value, config, price_change=price_change)
    trigger_status = _trigger_status(reason_codes)
    next_update_minutes = _next_update_minutes(input_value, config, trigger_status)
    return StrategyProbabilityUpdateTriggerV7Report(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        prior_market_probability=input_value.prior_market_probability,
        current_market_probability=input_value.current_market_probability,
        price_change=price_change,
        source_update_age_minutes=input_value.source_update_age_minutes,
        forecast_age_minutes=input_value.forecast_age_minutes,
        minutes_to_resolution=input_value.minutes_to_resolution,
        volatility=input_value.volatility,
        source_conflict=input_value.source_conflict,
        trigger_status=trigger_status,
        next_update_minutes=next_update_minutes,
        reason_codes=reason_codes,
    )


def strategy_probability_update_trigger_v7_payload(
    report: StrategyProbabilityUpdateTriggerV7Report,
) -> dict[str, Any]:
    if type(report) is not StrategyProbabilityUpdateTriggerV7Report:
        raise ValueError("report must be a StrategyProbabilityUpdateTriggerV7Report")
    require_paper_only_flags("strategy probability update trigger v7 report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    require_paper_only_flags("strategy probability update trigger v7 payload", _PayloadFlags(payload))
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
    input_value: StrategyProbabilityUpdateTriggerV7Input,
    config: StrategyProbabilityUpdateTriggerV7Config,
    *,
    price_change: Decimal,
) -> tuple[str, ...]:
    refresh_codes: list[str] = []
    _append_ascending_reason(
        refresh_codes,
        price_change,
        config.refresh_price_change,
        PRICE_CHANGE_REFRESH_REASON,
    )
    _append_descending_reason(
        refresh_codes,
        input_value.source_update_age_minutes,
        config.refresh_source_update_age_minutes,
        SOURCE_UPDATE_REFRESH_REASON,
    )
    _append_ascending_reason(
        refresh_codes,
        input_value.forecast_age_minutes,
        config.refresh_forecast_age_minutes,
        FORECAST_AGE_REFRESH_REASON,
    )
    _append_descending_reason(
        refresh_codes,
        input_value.minutes_to_resolution,
        config.refresh_resolution_deadline_minutes,
        RESOLUTION_DEADLINE_REFRESH_REASON,
    )
    _append_ascending_reason(
        refresh_codes,
        input_value.volatility,
        config.refresh_volatility,
        VOLATILITY_REFRESH_REASON,
    )
    _append_ascending_reason(
        refresh_codes,
        input_value.source_conflict,
        config.refresh_source_conflict,
        SOURCE_CONFLICT_REFRESH_REASON,
    )
    if refresh_codes:
        return _normalize_reason_codes("reason_codes", tuple(refresh_codes))

    watch_codes: list[str] = []
    _append_ascending_reason(
        watch_codes,
        price_change,
        config.watch_price_change,
        PRICE_CHANGE_WATCH_REASON,
    )
    _append_descending_reason(
        watch_codes,
        input_value.source_update_age_minutes,
        config.watch_source_update_age_minutes,
        SOURCE_UPDATE_WATCH_REASON,
    )
    _append_ascending_reason(
        watch_codes,
        input_value.forecast_age_minutes,
        config.watch_forecast_age_minutes,
        FORECAST_AGE_WATCH_REASON,
    )
    _append_descending_reason(
        watch_codes,
        input_value.minutes_to_resolution,
        config.watch_resolution_deadline_minutes,
        RESOLUTION_DEADLINE_WATCH_REASON,
    )
    _append_ascending_reason(
        watch_codes,
        input_value.volatility,
        config.watch_volatility,
        VOLATILITY_WATCH_REASON,
    )
    _append_ascending_reason(
        watch_codes,
        input_value.source_conflict,
        config.watch_source_conflict,
        SOURCE_CONFLICT_WATCH_REASON,
    )
    if watch_codes:
        return _normalize_reason_codes("reason_codes", tuple(watch_codes))
    return (DEFER_REASON,)


def _append_ascending_reason(
    codes: list[str],
    value: Decimal,
    threshold: Decimal,
    reason_code: str,
) -> None:
    if value >= threshold:
        codes.append(reason_code)


def _append_descending_reason(
    codes: list[str],
    value: Decimal,
    threshold: Decimal,
    reason_code: str,
) -> None:
    if value <= threshold:
        codes.append(reason_code)


def _trigger_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in REFRESH_REASONS for reason_code in reason_codes):
        return "refresh"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "defer"


def _next_update_minutes(
    input_value: StrategyProbabilityUpdateTriggerV7Input,
    config: StrategyProbabilityUpdateTriggerV7Config,
    trigger_status: str,
) -> Decimal:
    if trigger_status == "refresh":
        return ZERO
    if trigger_status == "watch":
        return config.watch_next_update_minutes

    candidates = [config.default_next_update_minutes]
    if input_value.forecast_age_minutes < config.watch_forecast_age_minutes:
        candidates.append(
            _quantize(config.watch_forecast_age_minutes - input_value.forecast_age_minutes),
        )
    if input_value.minutes_to_resolution > config.watch_resolution_deadline_minutes:
        candidates.append(
            _quantize(input_value.minutes_to_resolution - config.watch_resolution_deadline_minutes),
        )
    return _min_decimal(tuple(candidates))


def _validate_report(report: StrategyProbabilityUpdateTriggerV7Report) -> None:
    if report.price_change != _absolute_difference(
        report.current_market_probability,
        report.prior_market_probability,
    ):
        raise ValueError("price_change must match current_market_probability and prior_market_probability")
    if report.trigger_status != _trigger_status(report.reason_codes):
        raise ValueError("trigger_status must match reason_codes")
    if report.trigger_status == "refresh" and report.next_update_minutes != ZERO:
        raise ValueError("next_update_minutes must be zero when trigger_status is refresh")
    if report.trigger_status == "defer" and report.reason_codes != (DEFER_REASON,):
        raise ValueError("defer report must include only the defer reason")
    if report.trigger_status != "defer" and DEFER_REASON in report.reason_codes:
        raise ValueError("non-defer report must not include defer reason")


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


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    current = values[0]
    for value in values:
        if value < current:
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
    refresh_value: Decimal,
) -> None:
    if refresh_value < watch_value:
        raise ValueError(f"{field_name} must be at least watch threshold")


def _require_descending_threshold(
    field_name: str,
    watch_value: Decimal,
    refresh_value: Decimal,
) -> None:
    if refresh_value > watch_value:
        raise ValueError(f"{field_name} must not exceed watch threshold")


__all__ = (
    "DEFAULT_STRATEGY_PROBABILITY_UPDATE_TRIGGER_V7_CONFIG_VERSION",
    "StrategyProbabilityUpdateTriggerV7Config",
    "StrategyProbabilityUpdateTriggerV7Input",
    "StrategyProbabilityUpdateTriggerV7Report",
    "build_strategy_probability_update_trigger_v7_report",
    "strategy_probability_update_trigger_v7_payload",
)
