"""Pure in-memory probability event stale market risk review report."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_PROBABILITY_EVENT_STALE_MARKET_RISK_REVIEW_CONFIG_VERSION = (
    "probability-event-stale-market-risk-review-v0"
)

STALE_RISK_STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "urgent_market_close_stale_block",
    "last_trade_stale_watch",
    "orderbook_stale_watch",
    "price_move_since_forecast_block",
    "price_move_since_forecast_watch",
    "source_refresh_stale_watch",
    "stale_market_risk_clear",
)
MANUAL_NEXT_STEPS = (
    "allow_report_only_stale_market_risk_screen",
    "manual_review_stale_market_risk_before_shortlist",
    "exclude_report_only_until_market_freshness_reviewed",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


__all__ = (
    "DEFAULT_PROBABILITY_EVENT_STALE_MARKET_RISK_REVIEW_CONFIG_VERSION",
    "ProbabilityEventStaleMarketRiskReviewConfig",
    "ProbabilityEventStaleMarketRiskReviewInput",
    "ProbabilityEventStaleMarketRiskReviewReport",
    "build_probability_event_stale_market_risk_review_report",
    "probability_event_stale_market_risk_review_report_payload",
)


@dataclass(frozen=True)
class ProbabilityEventStaleMarketRiskReviewConfig:
    config_version: str = (
        DEFAULT_PROBABILITY_EVENT_STALE_MARKET_RISK_REVIEW_CONFIG_VERSION
    )
    last_trade_stale_after_hours: Decimal = Decimal("12.000000")
    last_orderbook_stale_after_minutes: Decimal = Decimal("30.000000")
    price_move_watch_threshold: Decimal = Decimal("0.050000")
    price_move_block_threshold: Decimal = Decimal("0.120000")
    source_refresh_stale_after_hours: Decimal = Decimal("8.000000")
    market_close_urgent_hours: Decimal = Decimal("24.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventStaleMarketRiskReviewConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_string("config_version", self.config_version)
        for field_name in (
            "last_trade_stale_after_hours",
            "last_orderbook_stale_after_minutes",
            "source_refresh_stale_after_hours",
            "market_close_urgent_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "price_move_watch_threshold",
            "price_move_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("ProbabilityEventStaleMarketRiskReviewConfig", self)


@dataclass(frozen=True)
class ProbabilityEventStaleMarketRiskReviewInput:
    last_trade_age_hours: Decimal
    last_orderbook_age_minutes: Decimal
    price_move_since_forecast: Decimal
    source_refresh_age_hours: Decimal
    market_close_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventStaleMarketRiskReviewInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in (
            "last_trade_age_hours",
            "last_orderbook_age_minutes",
            "source_refresh_age_hours",
            "market_close_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "price_move_since_forecast",
            _normalize_unit_decimal(
                "price_move_since_forecast",
                self.price_move_since_forecast,
            ),
        )
        require_paper_only_flags("ProbabilityEventStaleMarketRiskReviewInput", self)


@dataclass(frozen=True)
class ProbabilityEventStaleMarketRiskReviewReport:
    config_version: str
    last_trade_age_hours: Decimal
    last_orderbook_age_minutes: Decimal
    price_move_since_forecast: Decimal
    source_refresh_age_hours: Decimal
    market_close_hours: Decimal
    stale_risk_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    payload: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventStaleMarketRiskReviewReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_string("config_version", self.config_version)
        for field_name in (
            "last_trade_age_hours",
            "last_orderbook_age_minutes",
            "source_refresh_age_hours",
            "market_close_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "price_move_since_forecast",
            _normalize_unit_decimal(
                "price_move_since_forecast",
                self.price_move_since_forecast,
            ),
        )
        _require_member("stale_risk_status", self.stale_risk_status, STALE_RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_member("manual_next_step", self.manual_next_step, MANUAL_NEXT_STEPS)
        require_paper_only_flags("ProbabilityEventStaleMarketRiskReviewReport", self)
        _validate_report(self)
        object.__setattr__(self, "payload", _report_payload(self))


def build_probability_event_stale_market_risk_review_report(
    review_input: ProbabilityEventStaleMarketRiskReviewInput,
    *,
    config: ProbabilityEventStaleMarketRiskReviewConfig,
) -> ProbabilityEventStaleMarketRiskReviewReport:
    if type(review_input) is not ProbabilityEventStaleMarketRiskReviewInput:
        raise ValueError(
            "review_input must be a ProbabilityEventStaleMarketRiskReviewInput",
        )
    if type(config) is not ProbabilityEventStaleMarketRiskReviewConfig:
        raise ValueError(
            "config must be a ProbabilityEventStaleMarketRiskReviewConfig",
        )
    require_paper_only_flags("ProbabilityEventStaleMarketRiskReviewInput", review_input)
    require_paper_only_flags("ProbabilityEventStaleMarketRiskReviewConfig", config)

    reason_codes = _reason_codes(review_input, config=config)
    status = _stale_risk_status(reason_codes)
    return ProbabilityEventStaleMarketRiskReviewReport(
        config_version=config.config_version,
        last_trade_age_hours=review_input.last_trade_age_hours,
        last_orderbook_age_minutes=review_input.last_orderbook_age_minutes,
        price_move_since_forecast=review_input.price_move_since_forecast,
        source_refresh_age_hours=review_input.source_refresh_age_hours,
        market_close_hours=review_input.market_close_hours,
        stale_risk_status=status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(status),
    )


def probability_event_stale_market_risk_review_report_payload(
    report: ProbabilityEventStaleMarketRiskReviewReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventStaleMarketRiskReviewReport:
        raise ValueError(
            "report must be a ProbabilityEventStaleMarketRiskReviewReport",
        )
    require_paper_only_flags("ProbabilityEventStaleMarketRiskReviewReport", report)
    return report.payload


def _validate_config(config: ProbabilityEventStaleMarketRiskReviewConfig) -> None:
    if config.price_move_watch_threshold > config.price_move_block_threshold:
        raise ValueError("price move thresholds must be ascending")


def _validate_report(report: ProbabilityEventStaleMarketRiskReviewReport) -> None:
    expected_reason_codes = _reason_codes_from_fields(
        last_trade_age_hours=report.last_trade_age_hours,
        last_orderbook_age_minutes=report.last_orderbook_age_minutes,
        price_move_since_forecast=report.price_move_since_forecast,
        source_refresh_age_hours=report.source_refresh_age_hours,
        market_close_hours=report.market_close_hours,
        config=ProbabilityEventStaleMarketRiskReviewConfig(
            config_version=report.config_version,
        ),
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match input fields")
    expected_status = _stale_risk_status(report.reason_codes)
    if report.stale_risk_status != expected_status:
        raise ValueError("stale_risk_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(report.stale_risk_status):
        raise ValueError("manual_next_step must match stale_risk_status")


def _reason_codes(
    review_input: ProbabilityEventStaleMarketRiskReviewInput,
    *,
    config: ProbabilityEventStaleMarketRiskReviewConfig,
) -> tuple[str, ...]:
    return _reason_codes_from_fields(
        last_trade_age_hours=review_input.last_trade_age_hours,
        last_orderbook_age_minutes=review_input.last_orderbook_age_minutes,
        price_move_since_forecast=review_input.price_move_since_forecast,
        source_refresh_age_hours=review_input.source_refresh_age_hours,
        market_close_hours=review_input.market_close_hours,
        config=config,
    )


def _reason_codes_from_fields(
    *,
    last_trade_age_hours: Decimal,
    last_orderbook_age_minutes: Decimal,
    price_move_since_forecast: Decimal,
    source_refresh_age_hours: Decimal,
    market_close_hours: Decimal,
    config: ProbabilityEventStaleMarketRiskReviewConfig,
) -> tuple[str, ...]:
    requested_codes: list[str] = []
    market_close_is_urgent = market_close_hours <= config.market_close_urgent_hours
    has_stale_feed = (
        last_trade_age_hours > config.last_trade_stale_after_hours
        or last_orderbook_age_minutes > config.last_orderbook_stale_after_minutes
        or source_refresh_age_hours > config.source_refresh_stale_after_hours
    )

    if market_close_is_urgent and has_stale_feed:
        requested_codes.append("urgent_market_close_stale_block")
    if last_trade_age_hours > config.last_trade_stale_after_hours:
        requested_codes.append("last_trade_stale_watch")
    if last_orderbook_age_minutes > config.last_orderbook_stale_after_minutes:
        requested_codes.append("orderbook_stale_watch")
    if price_move_since_forecast > config.price_move_block_threshold:
        requested_codes.append("price_move_since_forecast_block")
    elif price_move_since_forecast > config.price_move_watch_threshold:
        requested_codes.append("price_move_since_forecast_watch")
    if source_refresh_age_hours > config.source_refresh_stale_after_hours:
        requested_codes.append("source_refresh_stale_watch")
    if not requested_codes:
        requested_codes.append("stale_market_risk_clear")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in requested_codes)


def _stale_risk_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "blocked"
    if reason_codes == ("stale_market_risk_clear",):
        return "pass"
    return "watch"


def _manual_next_step(stale_risk_status: str) -> str:
    if stale_risk_status == "pass":
        return "allow_report_only_stale_market_risk_screen"
    if stale_risk_status == "watch":
        return "manual_review_stale_market_risk_before_shortlist"
    if stale_risk_status == "blocked":
        return "exclude_report_only_until_market_freshness_reviewed"
    raise ValueError("stale_risk_status must be pass, watch, or blocked")


def _report_payload(
    report: ProbabilityEventStaleMarketRiskReviewReport,
) -> dict[str, Any]:
    payload = {
        "config_version": report.config_version,
        "last_trade_age_hours": report.last_trade_age_hours,
        "last_orderbook_age_minutes": report.last_orderbook_age_minutes,
        "price_move_since_forecast": report.price_move_since_forecast,
        "source_refresh_age_hours": report.source_refresh_age_hours,
        "market_close_hours": report.market_close_hours,
        "stale_risk_status": report.stale_risk_status,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    ready_payload = json_ready_no_floats(payload)
    if type(ready_payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready_payload


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        _require_member("reason_codes", reason_code, REASON_CODES)
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
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
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a str")
    if not value:
        raise ValueError(f"{field_name} must not be empty")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a str")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
