"""Pure paper/report/readonly calendar risk reducer for market outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONFIG_VERSION = "strategy-market-outcome-resolution-calendar-v10"
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
MICROSECONDS_PER_MINUTE = Decimal("60000000")
DECIMAL_CONTEXT = Context(prec=64)

TIMEZONE_RISKS = ("low", "medium", "high")
EVENT_TYPES = (
    "corporate",
    "court",
    "economic_data",
    "election",
    "other",
    "sports",
    "weather",
)
RESOLUTION_CALENDAR_STATUSES = ("ready", "watch", "blocked")
STATUS_REASON_CODES = (
    "calendar_blocked",
    "calendar_ready",
    "calendar_watch",
)
TIMEZONE_REASON_CODES = (
    "high_timezone_risk",
    "low_timezone_risk",
    "medium_timezone_risk",
)
DATE_REASON_CODES = (
    "weekday_resolution",
    "weekend_or_holiday_resolution",
)
SOURCE_LAG_REASON_CODES = (
    "source_lag_included",
    "source_lag_none",
)
WAIT_REASON_CODES = (
    "wait_exceeds_ready_threshold",
    "wait_exceeds_watch_threshold",
    "wait_within_ready_threshold",
)
MANUAL_CHECK_REASON_CODES = (
    "manual_check_immediate",
    "manual_check_scheduled",
)
EVENT_TYPE_REASON_CODES = tuple(f"event_type_{event_type}" for event_type in EVENT_TYPES)
REASON_CODES = tuple(
    sorted(
        (
            *STATUS_REASON_CODES,
            *TIMEZONE_REASON_CODES,
            *DATE_REASON_CODES,
            *SOURCE_LAG_REASON_CODES,
            *WAIT_REASON_CODES,
            *MANUAL_CHECK_REASON_CODES,
            *EVENT_TYPE_REASON_CODES,
        ),
    ),
)
EVENT_TYPE_RISK_MINUTES = {
    "corporate": Decimal("120.000000"),
    "court": Decimal("240.000000"),
    "economic_data": Decimal("60.000000"),
    "election": Decimal("720.000000"),
    "other": Decimal("120.000000"),
    "sports": Decimal("30.000000"),
    "weather": Decimal("60.000000"),
}


@dataclass(frozen=True)
class StrategyMarketOutcomeResolutionCalendarV10Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    ready_expected_wait_minutes: Decimal = Decimal("180.000000")
    watch_expected_wait_minutes: Decimal = Decimal("1440.000000")
    manual_check_lead_minutes: Decimal = Decimal("30.000000")
    medium_timezone_risk_minutes: Decimal = Decimal("60.000000")
    high_timezone_risk_minutes: Decimal = Decimal("180.000000")
    weekend_or_holiday_risk_minutes: Decimal = Decimal("1440.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "ready_expected_wait_minutes",
            "watch_expected_wait_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "manual_check_lead_minutes",
            "medium_timezone_risk_minutes",
            "high_timezone_risk_minutes",
            "weekend_or_holiday_risk_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.ready_expected_wait_minutes >= self.watch_expected_wait_minutes:
            raise ValueError(
                "watch_expected_wait_minutes must exceed ready_expected_wait_minutes",
            )
        if self.medium_timezone_risk_minutes > self.high_timezone_risk_minutes:
            raise ValueError(
                "medium_timezone_risk_minutes must be at most high_timezone_risk_minutes",
            )
        reject_unsafe_surface_fields("resolution calendar v10 config", self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class StrategyMarketOutcomeResolutionCalendarV10Input:
    close_time: datetime
    expected_resolution_time: datetime
    source_publication_lag_minutes: Decimal
    timezone_risk: str
    weekend_or_holiday: bool
    event_type: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "close_time", _as_utc("close_time", self.close_time))
        object.__setattr__(
            self,
            "expected_resolution_time",
            _as_utc("expected_resolution_time", self.expected_resolution_time),
        )
        if self.expected_resolution_time < self.close_time:
            raise ValueError("expected_resolution_time must not be before close_time")
        object.__setattr__(
            self,
            "source_publication_lag_minutes",
            _require_nonnegative_decimal(
                "source_publication_lag_minutes",
                self.source_publication_lag_minutes,
            ),
        )
        _require_timezone_risk("timezone_risk", self.timezone_risk)
        _require_bool("weekend_or_holiday", self.weekend_or_holiday)
        _require_event_type("event_type", self.event_type)
        reject_unsafe_surface_fields("resolution calendar v10 input", self)
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class StrategyMarketOutcomeResolutionCalendarV10Result:
    config_version: str
    close_time: datetime
    expected_resolution_time: datetime
    source_publication_lag_minutes: Decimal
    timezone_risk: str
    weekend_or_holiday: bool
    event_type: str
    resolution_calendar_status: str
    expected_wait_minutes: Decimal
    manual_check_deadline_minutes: Decimal
    reason_codes: tuple[str, ...]
    payload: dict[str, Any]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(self, "close_time", _as_utc("close_time", self.close_time))
        object.__setattr__(
            self,
            "expected_resolution_time",
            _as_utc("expected_resolution_time", self.expected_resolution_time),
        )
        if self.expected_resolution_time < self.close_time:
            raise ValueError("expected_resolution_time must not be before close_time")
        object.__setattr__(
            self,
            "source_publication_lag_minutes",
            _require_nonnegative_decimal(
                "source_publication_lag_minutes",
                self.source_publication_lag_minutes,
            ),
        )
        _require_timezone_risk("timezone_risk", self.timezone_risk)
        _require_bool("weekend_or_holiday", self.weekend_or_holiday)
        _require_event_type("event_type", self.event_type)
        _require_status("resolution_calendar_status", self.resolution_calendar_status)
        object.__setattr__(
            self,
            "expected_wait_minutes",
            _require_nonnegative_decimal("expected_wait_minutes", self.expected_wait_minutes),
        )
        object.__setattr__(
            self,
            "manual_check_deadline_minutes",
            _require_nonnegative_decimal(
                "manual_check_deadline_minutes",
                self.manual_check_deadline_minutes,
            ),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "payload", _normalize_payload(self.payload))
        reject_unsafe_surface_fields("resolution calendar v10 result", self)
        require_paper_only_flags("result", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_derived_validation_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        object.__setattr__(
            self,
            "payload",
            _payload_with_validation_digest(
                self.payload,
                self.derived_validation_digest,
            ),
        )
        _validate_result_consistency(self)


def resolve_market_outcome_resolution_calendar_v10(
    *,
    close_time: datetime,
    expected_resolution_time: datetime,
    source_publication_lag_minutes: Decimal,
    timezone_risk: str,
    weekend_or_holiday: bool,
    event_type: str,
    config: StrategyMarketOutcomeResolutionCalendarV10Config | None = None,
) -> StrategyMarketOutcomeResolutionCalendarV10Result:
    return build_strategy_market_outcome_resolution_calendar_v10_result(
        StrategyMarketOutcomeResolutionCalendarV10Input(
            close_time=close_time,
            expected_resolution_time=expected_resolution_time,
            source_publication_lag_minutes=source_publication_lag_minutes,
            timezone_risk=timezone_risk,
            weekend_or_holiday=weekend_or_holiday,
            event_type=event_type,
        ),
        config=config or StrategyMarketOutcomeResolutionCalendarV10Config(),
    )


def build_strategy_market_outcome_resolution_calendar_v10_result(
    value: object,
    *,
    config: StrategyMarketOutcomeResolutionCalendarV10Config,
) -> StrategyMarketOutcomeResolutionCalendarV10Result:
    if type(config) is not StrategyMarketOutcomeResolutionCalendarV10Config:
        raise ValueError(
            "config must be a StrategyMarketOutcomeResolutionCalendarV10Config",
        )
    reject_unsafe_surface_fields("resolution calendar v10 config", config)
    require_paper_only_flags("config", config)
    input_row = _input_from_supplied_shape(value)
    base_calendar_wait_minutes = _datetime_minutes(
        input_row.expected_resolution_time - input_row.close_time,
    )
    timezone_risk_minutes = _timezone_risk_minutes(input_row.timezone_risk, config)
    event_type_risk_minutes = EVENT_TYPE_RISK_MINUTES[input_row.event_type]
    weekend_or_holiday_risk_minutes = (
        config.weekend_or_holiday_risk_minutes if input_row.weekend_or_holiday else ZERO
    )
    expected_wait_minutes = _sum_decimal(
        (
            base_calendar_wait_minutes,
            input_row.source_publication_lag_minutes,
            timezone_risk_minutes,
            event_type_risk_minutes,
            weekend_or_holiday_risk_minutes,
        ),
    )
    status = _status_for_wait(expected_wait_minutes, config)
    manual_check_deadline_minutes = _manual_check_deadline_minutes(
        status=status,
        expected_wait_minutes=expected_wait_minutes,
        manual_check_lead_minutes=config.manual_check_lead_minutes,
    )
    reason_codes = _reason_codes(
        status=status,
        expected_wait_minutes=expected_wait_minutes,
        source_publication_lag_minutes=input_row.source_publication_lag_minutes,
        timezone_risk=input_row.timezone_risk,
        weekend_or_holiday=input_row.weekend_or_holiday,
        event_type=input_row.event_type,
        config=config,
    )
    payload = _result_payload(
        input_row=input_row,
        config=config,
        status=status,
        expected_wait_minutes=expected_wait_minutes,
        manual_check_deadline_minutes=manual_check_deadline_minutes,
        reason_codes=reason_codes,
        base_calendar_wait_minutes=base_calendar_wait_minutes,
        timezone_risk_minutes=timezone_risk_minutes,
        event_type_risk_minutes=event_type_risk_minutes,
        weekend_or_holiday_risk_minutes=weekend_or_holiday_risk_minutes,
    )
    return StrategyMarketOutcomeResolutionCalendarV10Result(
        config_version=config.config_version,
        close_time=input_row.close_time,
        expected_resolution_time=input_row.expected_resolution_time,
        source_publication_lag_minutes=input_row.source_publication_lag_minutes,
        timezone_risk=input_row.timezone_risk,
        weekend_or_holiday=input_row.weekend_or_holiday,
        event_type=input_row.event_type,
        resolution_calendar_status=status,
        expected_wait_minutes=expected_wait_minutes,
        manual_check_deadline_minutes=manual_check_deadline_minutes,
        reason_codes=reason_codes,
        payload=payload,
    )


def strategy_market_outcome_resolution_calendar_v10_payload(
    result: StrategyMarketOutcomeResolutionCalendarV10Result | dict[str, Any],
) -> dict[str, Any]:
    if type(result) is not StrategyMarketOutcomeResolutionCalendarV10Result:
        if type(result) is dict:
            return _payload_from_public_dict(result)
        raise ValueError(
            "result must be a StrategyMarketOutcomeResolutionCalendarV10Result",
        )
    require_paper_only_flags("result", result)
    payload = _normalize_payload(result.payload)
    _reject_unsafe_public_payload_values("resolution calendar v10 payload", payload)
    _validate_result_consistency(result)
    return payload


def _input_from_supplied_shape(value: object) -> StrategyMarketOutcomeResolutionCalendarV10Input:
    if type(value) is StrategyMarketOutcomeResolutionCalendarV10Input:
        reject_unsafe_surface_fields("resolution calendar v10 input", value)
        require_paper_only_flags("input", value)
        return value
    reject_unsafe_surface_fields("resolution calendar v10 input", value)
    require_paper_only_flags("input", value)
    return StrategyMarketOutcomeResolutionCalendarV10Input(
        close_time=_required_attr(value, "close_time"),
        expected_resolution_time=_required_attr(value, "expected_resolution_time"),
        source_publication_lag_minutes=_required_attr(
            value,
            "source_publication_lag_minutes",
        ),
        timezone_risk=_required_attr(value, "timezone_risk"),
        weekend_or_holiday=_required_attr(value, "weekend_or_holiday"),
        event_type=_required_attr(value, "event_type"),
    )


def _result_payload(
    *,
    input_row: StrategyMarketOutcomeResolutionCalendarV10Input,
    config: StrategyMarketOutcomeResolutionCalendarV10Config,
    status: str,
    expected_wait_minutes: Decimal,
    manual_check_deadline_minutes: Decimal,
    reason_codes: tuple[str, ...],
    base_calendar_wait_minutes: Decimal,
    timezone_risk_minutes: Decimal,
    event_type_risk_minutes: Decimal,
    weekend_or_holiday_risk_minutes: Decimal,
) -> dict[str, Any]:
    return {
        "config_version": config.config_version,
        "close_time": input_row.close_time.isoformat(),
        "expected_resolution_time": input_row.expected_resolution_time.isoformat(),
        "source_publication_lag_minutes": _decimal_payload(
            input_row.source_publication_lag_minutes,
        ),
        "timezone_risk": input_row.timezone_risk,
        "weekend_or_holiday": input_row.weekend_or_holiday,
        "event_type": input_row.event_type,
        "resolution_calendar_status": status,
        "expected_wait_minutes": _decimal_payload(expected_wait_minutes),
        "manual_check_deadline_minutes": _decimal_payload(manual_check_deadline_minutes),
        "reason_codes": list(reason_codes),
        "base_calendar_wait_minutes": _decimal_payload(base_calendar_wait_minutes),
        "timezone_risk_minutes": _decimal_payload(timezone_risk_minutes),
        "event_type_risk_minutes": _decimal_payload(event_type_risk_minutes),
        "weekend_or_holiday_risk_minutes": _decimal_payload(
            weekend_or_holiday_risk_minutes,
        ),
        "ready_expected_wait_minutes": _decimal_payload(config.ready_expected_wait_minutes),
        "watch_expected_wait_minutes": _decimal_payload(config.watch_expected_wait_minutes),
        "manual_check_lead_minutes": _decimal_payload(config.manual_check_lead_minutes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_codes(
    *,
    status: str,
    expected_wait_minutes: Decimal,
    source_publication_lag_minutes: Decimal,
    timezone_risk: str,
    weekend_or_holiday: bool,
    event_type: str,
    config: StrategyMarketOutcomeResolutionCalendarV10Config,
) -> tuple[str, ...]:
    reason_codes = [
        _status_reason(status),
        f"{timezone_risk}_timezone_risk",
        "weekend_or_holiday_resolution" if weekend_or_holiday else "weekday_resolution",
        "source_lag_included"
        if source_publication_lag_minutes > ZERO
        else "source_lag_none",
        _wait_reason(expected_wait_minutes, config),
        "manual_check_immediate" if status == "blocked" else "manual_check_scheduled",
        f"event_type_{event_type}",
    ]
    return _normalize_reason_codes(tuple(sorted(reason_codes)))


def _validate_result_consistency(
    result: StrategyMarketOutcomeResolutionCalendarV10Result,
) -> None:
    expected_wait_minutes = _sum_decimal(
        (
            _datetime_minutes(result.expected_resolution_time - result.close_time),
            result.source_publication_lag_minutes,
            _payload_decimal(result.payload, "timezone_risk_minutes"),
            _payload_decimal(result.payload, "event_type_risk_minutes"),
            _payload_decimal(result.payload, "weekend_or_holiday_risk_minutes"),
        ),
    )
    if result.expected_wait_minutes != expected_wait_minutes:
        raise ValueError("expected_wait_minutes must match inputs")

    ready_expected_wait_minutes = _payload_decimal(
        result.payload,
        "ready_expected_wait_minutes",
    )
    watch_expected_wait_minutes = _payload_decimal(
        result.payload,
        "watch_expected_wait_minutes",
    )
    manual_check_lead_minutes = _payload_decimal(result.payload, "manual_check_lead_minutes")
    expected_status = _status_for_wait_values(
        result.expected_wait_minutes,
        ready_expected_wait_minutes,
        watch_expected_wait_minutes,
    )
    if result.resolution_calendar_status != expected_status:
        raise ValueError("resolution_calendar_status must match expected_wait_minutes")
    expected_deadline = _manual_check_deadline_minutes(
        status=result.resolution_calendar_status,
        expected_wait_minutes=result.expected_wait_minutes,
        manual_check_lead_minutes=manual_check_lead_minutes,
    )
    if result.manual_check_deadline_minutes != expected_deadline:
        raise ValueError("manual_check_deadline_minutes must match status")

    expected_reason_codes = _reason_codes_from_payload_thresholds(result)
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match status and inputs")

    _validate_payload_matches_result(result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")


def _reason_codes_from_payload_thresholds(
    result: StrategyMarketOutcomeResolutionCalendarV10Result,
) -> tuple[str, ...]:
    ready_expected_wait_minutes = _payload_decimal(
        result.payload,
        "ready_expected_wait_minutes",
    )
    watch_expected_wait_minutes = _payload_decimal(
        result.payload,
        "watch_expected_wait_minutes",
    )
    wait_reason = _wait_reason_values(
        result.expected_wait_minutes,
        ready_expected_wait_minutes,
        watch_expected_wait_minutes,
    )
    reason_codes = [
        _status_reason(result.resolution_calendar_status),
        f"{result.timezone_risk}_timezone_risk",
        "weekend_or_holiday_resolution"
        if result.weekend_or_holiday
        else "weekday_resolution",
        "source_lag_included"
        if result.source_publication_lag_minutes > ZERO
        else "source_lag_none",
        wait_reason,
        "manual_check_immediate"
        if result.resolution_calendar_status == "blocked"
        else "manual_check_scheduled",
        f"event_type_{result.event_type}",
    ]
    return _normalize_reason_codes(tuple(sorted(reason_codes)))


def _validate_payload_matches_result(
    result: StrategyMarketOutcomeResolutionCalendarV10Result,
) -> None:
    expected_pairs: tuple[tuple[str, object], ...] = (
        ("config_version", result.config_version),
        ("close_time", result.close_time.isoformat()),
        ("expected_resolution_time", result.expected_resolution_time.isoformat()),
        (
            "source_publication_lag_minutes",
            _decimal_payload(result.source_publication_lag_minutes),
        ),
        ("timezone_risk", result.timezone_risk),
        ("weekend_or_holiday", result.weekend_or_holiday),
        ("event_type", result.event_type),
        ("resolution_calendar_status", result.resolution_calendar_status),
        ("expected_wait_minutes", _decimal_payload(result.expected_wait_minutes)),
        (
            "manual_check_deadline_minutes",
            _decimal_payload(result.manual_check_deadline_minutes),
        ),
        ("paper_only", True),
        ("report_only", True),
        ("readonly", True),
        ("derived_validation_digest", result.derived_validation_digest),
    )
    for field_name, expected_value in expected_pairs:
        if result.payload.get(field_name) != expected_value:
            raise ValueError(f"{field_name} must match payload")
    if result.payload.get("reason_codes") != list(result.reason_codes):
        raise ValueError("payload reason_codes must match result")


def _status_for_wait(
    value: Decimal,
    config: StrategyMarketOutcomeResolutionCalendarV10Config,
) -> str:
    return _status_for_wait_values(
        value,
        config.ready_expected_wait_minutes,
        config.watch_expected_wait_minutes,
    )


def _status_for_wait_values(
    value: Decimal,
    ready_expected_wait_minutes: Decimal,
    watch_expected_wait_minutes: Decimal,
) -> str:
    if value > watch_expected_wait_minutes:
        return "blocked"
    if value > ready_expected_wait_minutes:
        return "watch"
    return "ready"


def _status_reason(status: str) -> str:
    if status == "blocked":
        return "calendar_blocked"
    if status == "watch":
        return "calendar_watch"
    return "calendar_ready"


def _wait_reason(
    value: Decimal,
    config: StrategyMarketOutcomeResolutionCalendarV10Config,
) -> str:
    return _wait_reason_values(
        value,
        config.ready_expected_wait_minutes,
        config.watch_expected_wait_minutes,
    )


def _wait_reason_values(
    value: Decimal,
    ready_expected_wait_minutes: Decimal,
    watch_expected_wait_minutes: Decimal,
) -> str:
    if value > watch_expected_wait_minutes:
        return "wait_exceeds_watch_threshold"
    if value > ready_expected_wait_minutes:
        return "wait_exceeds_ready_threshold"
    return "wait_within_ready_threshold"


def _manual_check_deadline_minutes(
    *,
    status: str,
    expected_wait_minutes: Decimal,
    manual_check_lead_minutes: Decimal,
) -> Decimal:
    if status == "blocked":
        return ZERO
    deadline = expected_wait_minutes - manual_check_lead_minutes
    if deadline < ZERO:
        return ZERO
    return _quantize(deadline)


def _timezone_risk_minutes(
    timezone_risk: str,
    config: StrategyMarketOutcomeResolutionCalendarV10Config,
) -> Decimal:
    if timezone_risk == "high":
        return config.high_timezone_risk_minutes
    if timezone_risk == "medium":
        return config.medium_timezone_risk_minutes
    return ZERO


def _datetime_minutes(value: timedelta) -> Decimal:
    total_microseconds = Decimal(
        value.days * 86400000000 + value.seconds * 1000000 + value.microseconds,
    )
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(total_microseconds / MICROSECONDS_PER_MINUTE)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        with localcontext(DECIMAL_CONTEXT):
            total = _quantize(total + value)
    return total


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_timezone_risk(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TIMEZONE_RISKS:
        raise ValueError(f"{field_name} must be low, medium, or high")


def _require_event_type(field_name: str, value: object) -> None:
    if type(value) is not str or value not in EVENT_TYPES:
        raise ValueError(f"{field_name} must be known")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESOLUTION_CALENDAR_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must use six decimal places")
    decimal_value = _quantize(value)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes must be known")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(sorted(reason_codes)) != reason_codes:
        raise ValueError("reason_codes must be sorted")
    return reason_codes


def _normalize_payload(value: object) -> dict[str, Any]:
    ready = json_ready_no_floats(value)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    reject_unsafe_surface_fields("resolution calendar v10 payload", ready)
    _reject_unsafe_public_payload_values("resolution calendar v10 payload", ready)
    return dict(ready)


def _payload_from_public_dict(value: dict[str, Any]) -> dict[str, Any]:
    payload = _normalize_payload(value)
    _require_payload_flags(payload)
    if "derived_validation_digest" not in payload:
        raise ValueError("payload derived_validation_digest is required")
    result = StrategyMarketOutcomeResolutionCalendarV10Result(
        config_version=_payload_string(payload, "config_version"),
        close_time=_payload_datetime(payload, "close_time"),
        expected_resolution_time=_payload_datetime(
            payload,
            "expected_resolution_time",
        ),
        source_publication_lag_minutes=_payload_decimal(
            payload,
            "source_publication_lag_minutes",
        ),
        timezone_risk=_payload_string(payload, "timezone_risk"),
        weekend_or_holiday=_payload_bool(payload, "weekend_or_holiday"),
        event_type=_payload_string(payload, "event_type"),
        resolution_calendar_status=_payload_string(
            payload,
            "resolution_calendar_status",
        ),
        expected_wait_minutes=_payload_decimal(payload, "expected_wait_minutes"),
        manual_check_deadline_minutes=_payload_decimal(
            payload,
            "manual_check_deadline_minutes",
        ),
        reason_codes=tuple(_payload_string_list(payload, "reason_codes")),
        payload=payload,
        derived_validation_digest=_payload_string(
            payload,
            "derived_validation_digest",
        ),
    )
    return result.payload


def _payload_decimal(payload: dict[str, Any], field_name: str) -> Decimal:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"payload {field_name} must be a decimal string")
    return _require_nonnegative_decimal(f"payload {field_name}", Decimal(value))


def _payload_datetime(payload: dict[str, Any], field_name: str) -> datetime:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"payload {field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"payload {field_name} must be a datetime string") from exc
    return _as_utc(f"payload {field_name}", parsed)


def _payload_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    _require_canonical_string(f"payload {field_name}", value)
    return value


def _payload_bool(payload: dict[str, Any], field_name: str) -> bool:
    value = payload.get(field_name)
    _require_bool(f"payload {field_name}", value)
    return value


def _payload_string_list(payload: dict[str, Any], field_name: str) -> list[str]:
    value = payload.get(field_name)
    if type(value) is not list:
        raise ValueError(f"payload {field_name} must be a list")
    for item in value:
        _require_canonical_string(f"payload {field_name}", item)
    return value


def _payload_with_validation_digest(
    payload: dict[str, Any],
    derived_validation_digest: str,
) -> dict[str, Any]:
    payload_digest = payload.get("derived_validation_digest")
    if payload_digest is not None:
        normalized_digest = _normalize_derived_validation_digest(
            "payload derived_validation_digest",
            payload_digest,
        )
        if normalized_digest != derived_validation_digest:
            raise ValueError("payload derived_validation_digest must match result")
    return {**payload, "derived_validation_digest": derived_validation_digest}


def _normalize_derived_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest") from exc
    return value


def _derived_validation_digest(
    result: StrategyMarketOutcomeResolutionCalendarV10Result,
) -> str:
    digest_material = "|".join(
        (
            f"config_version={result.config_version}",
            f"close_time={result.close_time.isoformat()}",
            f"expected_resolution_time={result.expected_resolution_time.isoformat()}",
            f"source_publication_lag_minutes={_decimal_payload(result.source_publication_lag_minutes)}",
            f"timezone_risk={result.timezone_risk}",
            f"weekend_or_holiday={result.weekend_or_holiday}",
            f"event_type={result.event_type}",
            f"resolution_calendar_status={result.resolution_calendar_status}",
            f"expected_wait_minutes={_decimal_payload(result.expected_wait_minutes)}",
            f"manual_check_deadline_minutes={_decimal_payload(result.manual_check_deadline_minutes)}",
            f"reason_codes={','.join(result.reason_codes)}",
            f"base_calendar_wait_minutes={_payload_decimal(result.payload, 'base_calendar_wait_minutes')}",
            f"timezone_risk_minutes={_payload_decimal(result.payload, 'timezone_risk_minutes')}",
            f"event_type_risk_minutes={_payload_decimal(result.payload, 'event_type_risk_minutes')}",
            f"weekend_or_holiday_risk_minutes={_payload_decimal(result.payload, 'weekend_or_holiday_risk_minutes')}",
            f"ready_expected_wait_minutes={_payload_decimal(result.payload, 'ready_expected_wait_minutes')}",
            f"watch_expected_wait_minutes={_payload_decimal(result.payload, 'watch_expected_wait_minutes')}",
            f"manual_check_lead_minutes={_payload_decimal(result.payload, 'manual_check_lead_minutes')}",
            f"paper_only={result.paper_only}",
            f"report_only={result.report_only}",
            f"readonly={result.readonly}",
        ),
    )
    return hashlib.sha256(digest_material.encode("utf-8")).hexdigest()


def _require_payload_flags(payload: dict[str, Any]) -> None:
    require_paper_only_flags("payload", _DictFlags(payload))


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


def _reject_unsafe_public_payload_values(label: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe public payload value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_payload_values(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload_values(label, item)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "StrategyMarketOutcomeResolutionCalendarV10Config",
    "StrategyMarketOutcomeResolutionCalendarV10Input",
    "StrategyMarketOutcomeResolutionCalendarV10Result",
    "build_strategy_market_outcome_resolution_calendar_v10_result",
    "resolve_market_outcome_resolution_calendar_v10",
    "strategy_market_outcome_resolution_calendar_v10_payload",
)
