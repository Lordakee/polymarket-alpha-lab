"""Pure paper-only specialist review capacity forecast."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_TEAM_REVIEW_CAPACITY_FORECAST_V10_CONFIG_VERSION = (
    "strategy-team-review-capacity-forecast-v10"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ZERO_COUNT = Decimal("0")
ONE = Decimal("1.000000")

REVIEW_CAPACITY_STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "review_queue_clear",
    "active_analyst_capacity_available",
    "no_active_analysts",
    "urgent_candidates_present",
    "stale_packets_present",
    "quality_rework_load",
    "capacity_buffer_sufficient",
    "capacity_buffer_watch",
    "capacity_gap_present",
    "review_capacity_pass",
    "review_capacity_watch",
    "review_capacity_blocked",
)


@dataclass(frozen=True)
class StrategyTeamReviewCapacityForecastV10Config:
    config_version: str = (
        DEFAULT_STRATEGY_TEAM_REVIEW_CAPACITY_FORECAST_V10_CONFIG_VERSION
    )
    analyst_review_minutes_per_day: Decimal = Decimal("360.000000")
    minimum_capacity_buffer_ratio: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, StrategyTeamReviewCapacityForecastV10Config)
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "analyst_review_minutes_per_day",
            _normalize_positive_decimal(
                "analyst_review_minutes_per_day",
                self.analyst_review_minutes_per_day,
            ),
        )
        object.__setattr__(
            self,
            "minimum_capacity_buffer_ratio",
            _normalize_ratio(
                "minimum_capacity_buffer_ratio",
                self.minimum_capacity_buffer_ratio,
            ),
        )
        reject_unsafe_surface_fields("StrategyTeamReviewCapacityForecastV10Config", self)
        require_paper_only_flags("StrategyTeamReviewCapacityForecastV10Config", self)


@dataclass(frozen=True)
class StrategyTeamReviewCapacityForecastV10Input:
    active_analyst_count: Decimal
    urgent_candidate_count: Decimal
    stale_packet_count: Decimal
    average_review_minutes: Decimal
    quality_rework_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("forecast", self, StrategyTeamReviewCapacityForecastV10Input)
        for field_name in (
            "active_analyst_count",
            "urgent_candidate_count",
            "stale_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_review_minutes",
            _normalize_positive_decimal(
                "average_review_minutes",
                self.average_review_minutes,
            ),
        )
        object.__setattr__(
            self,
            "quality_rework_rate",
            _normalize_ratio("quality_rework_rate", self.quality_rework_rate),
        )
        reject_unsafe_surface_fields("StrategyTeamReviewCapacityForecastV10Input", self)
        require_paper_only_flags("StrategyTeamReviewCapacityForecastV10Input", self)


@dataclass(frozen=True)
class StrategyTeamReviewCapacityForecastV10Report:
    config_version: str
    active_analyst_count: Decimal
    urgent_candidate_count: Decimal
    stale_packet_count: Decimal
    total_candidate_count: Decimal
    average_review_minutes: Decimal
    quality_rework_rate: Decimal
    adjusted_review_minutes_per_candidate: Decimal
    available_review_minutes: Decimal
    demand_review_minutes: Decimal
    forecast_capacity_candidate_count: Decimal
    projected_backlog_candidate_count: Decimal
    capacity_gap_minutes: Decimal
    capacity_gap_candidate_count: Decimal
    capacity_buffer_minutes: Decimal
    capacity_buffer_ratio: Decimal
    demand_coverage_ratio: Decimal
    review_capacity_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, StrategyTeamReviewCapacityForecastV10Report)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "active_analyst_count",
            "urgent_candidate_count",
            "stale_packet_count",
            "total_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_review_minutes",
            "adjusted_review_minutes_per_candidate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quality_rework_rate",
            _normalize_ratio("quality_rework_rate", self.quality_rework_rate),
        )
        for field_name in (
            "available_review_minutes",
            "demand_review_minutes",
            "forecast_capacity_candidate_count",
            "projected_backlog_candidate_count",
            "capacity_gap_minutes",
            "capacity_gap_candidate_count",
            "capacity_buffer_minutes",
            "capacity_buffer_ratio",
            "demand_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice(
            "review_capacity_status",
            self.review_capacity_status,
            REVIEW_CAPACITY_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_surface(self)
        reject_unsafe_surface_fields("StrategyTeamReviewCapacityForecastV10Report", self)
        require_paper_only_flags("StrategyTeamReviewCapacityForecastV10Report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_team_review_capacity_forecast_v10_payload(self)


def forecast_strategy_team_review_capacity_v10(
    forecast: StrategyTeamReviewCapacityForecastV10Input,
    *,
    config: StrategyTeamReviewCapacityForecastV10Config | None = None,
) -> StrategyTeamReviewCapacityForecastV10Report:
    if type(forecast) is not StrategyTeamReviewCapacityForecastV10Input:
        raise ValueError("forecast must be a StrategyTeamReviewCapacityForecastV10Input")
    require_paper_only_flags("forecast", forecast)
    active_config = config or StrategyTeamReviewCapacityForecastV10Config()
    if type(active_config) is not StrategyTeamReviewCapacityForecastV10Config:
        raise ValueError(
            "config must be a StrategyTeamReviewCapacityForecastV10Config",
        )
    require_paper_only_flags("config", active_config)

    total_candidate_count = _whole_sum(
        forecast.urgent_candidate_count,
        forecast.stale_packet_count,
    )
    adjusted_review_minutes = _multiply(
        forecast.average_review_minutes,
        ONE + forecast.quality_rework_rate,
    )
    available_review_minutes = _multiply(
        forecast.active_analyst_count,
        active_config.analyst_review_minutes_per_day,
    )
    demand_review_minutes = _multiply(total_candidate_count, adjusted_review_minutes)
    forecast_capacity_candidate_count = _divide(
        available_review_minutes,
        adjusted_review_minutes,
    )
    capacity_gap_minutes = _positive_delta(
        demand_review_minutes,
        available_review_minutes,
    )
    capacity_gap_candidate_count = _divide(
        capacity_gap_minutes,
        adjusted_review_minutes,
    )
    capacity_buffer_minutes = _positive_delta(
        available_review_minutes,
        demand_review_minutes,
    )
    projected_backlog_candidate_count = _positive_delta(
        total_candidate_count,
        forecast_capacity_candidate_count,
    )
    capacity_buffer_ratio = (
        _divide(capacity_buffer_minutes, available_review_minutes)
        if available_review_minutes > ZERO
        else ZERO
    )
    demand_coverage_ratio = (
        _divide(available_review_minutes, demand_review_minutes)
        if demand_review_minutes > ZERO
        else ONE
    )
    review_capacity_status = _review_capacity_status(
        forecast=forecast,
        config=active_config,
        total_candidate_count=total_candidate_count,
        capacity_gap_minutes=capacity_gap_minutes,
        capacity_buffer_ratio=capacity_buffer_ratio,
    )

    return StrategyTeamReviewCapacityForecastV10Report(
        config_version=active_config.config_version,
        active_analyst_count=forecast.active_analyst_count,
        urgent_candidate_count=forecast.urgent_candidate_count,
        stale_packet_count=forecast.stale_packet_count,
        total_candidate_count=total_candidate_count,
        average_review_minutes=forecast.average_review_minutes,
        quality_rework_rate=forecast.quality_rework_rate,
        adjusted_review_minutes_per_candidate=adjusted_review_minutes,
        available_review_minutes=available_review_minutes,
        demand_review_minutes=demand_review_minutes,
        forecast_capacity_candidate_count=forecast_capacity_candidate_count,
        projected_backlog_candidate_count=projected_backlog_candidate_count,
        capacity_gap_minutes=capacity_gap_minutes,
        capacity_gap_candidate_count=capacity_gap_candidate_count,
        capacity_buffer_minutes=capacity_buffer_minutes,
        capacity_buffer_ratio=capacity_buffer_ratio,
        demand_coverage_ratio=demand_coverage_ratio,
        review_capacity_status=review_capacity_status,
        reason_codes=_reason_codes(
            forecast=forecast,
            config=active_config,
            total_candidate_count=total_candidate_count,
            capacity_gap_minutes=capacity_gap_minutes,
            capacity_buffer_ratio=capacity_buffer_ratio,
            review_capacity_status=review_capacity_status,
        ),
    )


def strategy_team_review_capacity_forecast_v10_payload(
    report: StrategyTeamReviewCapacityForecastV10Report,
) -> dict[str, Any]:
    if type(report) is not StrategyTeamReviewCapacityForecastV10Report:
        raise ValueError("report must be a StrategyTeamReviewCapacityForecastV10Report")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("strategy team review capacity forecast v10", report)
    payload = {
        "config_version": report.config_version,
        "active_analyst_count": report.active_analyst_count,
        "urgent_candidate_count": report.urgent_candidate_count,
        "stale_packet_count": report.stale_packet_count,
        "total_candidate_count": report.total_candidate_count,
        "average_review_minutes": report.average_review_minutes,
        "quality_rework_rate": report.quality_rework_rate,
        "adjusted_review_minutes_per_candidate": (
            report.adjusted_review_minutes_per_candidate
        ),
        "available_review_minutes": report.available_review_minutes,
        "demand_review_minutes": report.demand_review_minutes,
        "forecast_capacity_candidate_count": (
            report.forecast_capacity_candidate_count
        ),
        "projected_backlog_candidate_count": (
            report.projected_backlog_candidate_count
        ),
        "capacity_gap_minutes": report.capacity_gap_minutes,
        "capacity_gap_candidate_count": report.capacity_gap_candidate_count,
        "capacity_buffer_minutes": report.capacity_buffer_minutes,
        "capacity_buffer_ratio": report.capacity_buffer_ratio,
        "demand_coverage_ratio": report.demand_coverage_ratio,
        "review_capacity_status": report.review_capacity_status,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    reject_unsafe_surface_fields("strategy team review capacity forecast v10 payload", payload)
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _review_capacity_status(
    *,
    forecast: StrategyTeamReviewCapacityForecastV10Input,
    config: StrategyTeamReviewCapacityForecastV10Config,
    total_candidate_count: Decimal,
    capacity_gap_minutes: Decimal,
    capacity_buffer_ratio: Decimal,
) -> str:
    if total_candidate_count == ZERO_COUNT:
        return "pass"
    if forecast.active_analyst_count == ZERO_COUNT:
        return "blocked"
    if capacity_gap_minutes > ZERO:
        return "blocked"
    if capacity_buffer_ratio < config.minimum_capacity_buffer_ratio:
        return "watch"
    return "pass"


def _reason_codes(
    *,
    forecast: StrategyTeamReviewCapacityForecastV10Input,
    config: StrategyTeamReviewCapacityForecastV10Config,
    total_candidate_count: Decimal,
    capacity_gap_minutes: Decimal,
    capacity_buffer_ratio: Decimal,
    review_capacity_status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if total_candidate_count == ZERO_COUNT:
        codes.append("review_queue_clear")
    if forecast.active_analyst_count > ZERO_COUNT:
        codes.append("active_analyst_capacity_available")
    else:
        codes.append("no_active_analysts")
    if forecast.urgent_candidate_count > ZERO_COUNT:
        codes.append("urgent_candidates_present")
    if forecast.stale_packet_count > ZERO_COUNT:
        codes.append("stale_packets_present")
    if forecast.quality_rework_rate > ZERO:
        codes.append("quality_rework_load")
    if capacity_gap_minutes > ZERO:
        codes.append("capacity_gap_present")
    elif (
        total_candidate_count > ZERO_COUNT
        and capacity_buffer_ratio < config.minimum_capacity_buffer_ratio
    ):
        codes.append("capacity_buffer_watch")
    else:
        codes.append("capacity_buffer_sufficient")
    codes.append(f"review_capacity_{review_capacity_status}")
    return _normalize_reason_codes(tuple(codes))


def _validate_report_surface(
    report: StrategyTeamReviewCapacityForecastV10Report,
) -> None:
    if (
        _whole_sum(report.urgent_candidate_count, report.stale_packet_count)
        != report.total_candidate_count
    ):
        raise ValueError("total_candidate_count must equal urgent plus stale counts")
    status_reason_code = f"review_capacity_{report.review_capacity_status}"
    if status_reason_code not in report.reason_codes:
        raise ValueError("reason_codes must include review_capacity_status")
    if report.capacity_gap_minutes > ZERO and report.review_capacity_status != "blocked":
        raise ValueError("capacity gap requires blocked status")
    if (
        report.review_capacity_status == "blocked"
        and report.capacity_gap_minutes == ZERO
        and report.total_candidate_count > ZERO_COUNT
        and report.active_analyst_count > ZERO_COUNT
    ):
        raise ValueError("blocked status requires a capacity gap or no active analysts")


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string("reason_codes", value)
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return tuple(value for value in REASON_CODES if value in seen)


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    quantized = _quantize(normalized)
    if quantized < ZERO or quantized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return quantized


def _normalize_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        quantized = decimal.quantize(COUNT_QUANTUM)
    if decimal != quantized:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if quantized == ZERO_COUNT:
        return ZERO_COUNT
    return quantized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(QUANTUM)
    if quantized == ZERO:
        return ZERO
    return quantized


def _whole_sum(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = left + right
    return _normalize_whole_decimal("total_candidate_count", total)


def _multiply(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _positive_delta(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        delta = left - right
    if delta <= ZERO:
        return ZERO
    return _quantize(delta)


def _require_choice(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


__all__ = (
    "DEFAULT_STRATEGY_TEAM_REVIEW_CAPACITY_FORECAST_V10_CONFIG_VERSION",
    "REASON_CODES",
    "REVIEW_CAPACITY_STATUSES",
    "StrategyTeamReviewCapacityForecastV10Config",
    "StrategyTeamReviewCapacityForecastV10Input",
    "StrategyTeamReviewCapacityForecastV10Report",
    "forecast_strategy_team_review_capacity_v10",
    "strategy_team_review_capacity_forecast_v10_payload",
)
