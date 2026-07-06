"""Pure paper report information decay alert reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "StrategyMarketInformationDecayAlertV10Input",
    "StrategyMarketInformationDecayAlertV10Result",
    "evaluate_strategy_market_information_decay_alert_v10",
    "strategy_market_information_decay_alert_v10_payload",
)


VALUE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PRIMARY_AGING_MINUTES = Decimal("120.000000")
PRIMARY_STALE_MINUTES = Decimal("360.000000")
PRIMARY_CRITICAL_MINUTES = Decimal("720.000000")
SECONDARY_AGING_MINUTES = Decimal("240.000000")
SECONDARY_STALE_MINUTES = Decimal("720.000000")
SECONDARY_CRITICAL_MINUTES = Decimal("1440.000000")
MARKET_MOVE_WATCH_BPS = Decimal("50.000000")
MARKET_MOVE_MATERIAL_BPS = Decimal("150.000000")
MARKET_MOVE_CRITICAL_BPS = Decimal("300.000000")
LOW_SOURCE_RELIABILITY_SCORE = Decimal("0.600000")
CONSTRAINED_TEAM_CAPACITY_SCORE = Decimal("0.500000")
SEVERELY_CONSTRAINED_TEAM_CAPACITY_SCORE = Decimal("0.250000")
NEAR_RESOLUTION_MINUTES = Decimal("240.000000")
IMMINENT_RESOLUTION_MINUTES = Decimal("60.000000")
CURRENT_SLA_MINUTES = Decimal("480.000000")
WATCH_SLA_MINUTES = Decimal("240.000000")
REFRESH_DUE_SLA_MINUTES = Decimal("60.000000")
CRITICAL_SLA_MINUTES = Decimal("15.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ALERT_STATUSES = ("current", "watch", "refresh_due", "critical")
REFRESH_PRIORITIES = ("monitor", "normal", "high", "urgent")


@dataclass(frozen=True)
class StrategyMarketInformationDecayAlertV10Input:
    market_id: str
    last_primary_update_minutes: Decimal
    last_secondary_update_minutes: Decimal
    market_price_move_bps: Decimal
    source_reliability_score: Decimal
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in (
            "last_primary_update_minutes",
            "last_secondary_update_minutes",
            "market_price_move_bps",
            "time_to_resolution_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_reliability_score",
            "team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_paper_flags("input", self)


@dataclass(frozen=True)
class StrategyMarketInformationDecayAlertV10Result:
    market_id: str
    last_primary_update_minutes: Decimal
    last_secondary_update_minutes: Decimal
    market_price_move_bps: Decimal
    source_reliability_score: Decimal
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    alert_status: str
    refresh_priority: str
    sla_minutes: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        for field_name in (
            "last_primary_update_minutes",
            "last_secondary_update_minutes",
            "market_price_move_bps",
            "time_to_resolution_minutes",
            "sla_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_reliability_score",
            "team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "alert_status",
            _normalize_choice("alert_status", self.alert_status, ALERT_STATUSES),
        )
        object.__setattr__(
            self,
            "refresh_priority",
            _normalize_choice(
                "refresh_priority",
                self.refresh_priority,
                REFRESH_PRIORITIES,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.refresh_priority != _refresh_priority(self.alert_status):
            raise ValueError("result refresh_priority must match alert_status")
        if self.sla_minutes != _sla_minutes(self.alert_status):
            raise ValueError("result sla_minutes must match alert_status")
        _require_paper_flags("result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_market_information_decay_alert_v10_payload(self)


def evaluate_strategy_market_information_decay_alert_v10(
    input_row: StrategyMarketInformationDecayAlertV10Input,
) -> StrategyMarketInformationDecayAlertV10Result:
    if type(input_row) is not StrategyMarketInformationDecayAlertV10Input:
        raise ValueError(
            "input_row must be a StrategyMarketInformationDecayAlertV10Input",
        )
    _require_paper_flags("input", input_row)

    alert_status = _alert_status(input_row)
    return StrategyMarketInformationDecayAlertV10Result(
        market_id=input_row.market_id,
        last_primary_update_minutes=input_row.last_primary_update_minutes,
        last_secondary_update_minutes=input_row.last_secondary_update_minutes,
        market_price_move_bps=input_row.market_price_move_bps,
        source_reliability_score=input_row.source_reliability_score,
        time_to_resolution_minutes=input_row.time_to_resolution_minutes,
        team_capacity_score=input_row.team_capacity_score,
        alert_status=alert_status,
        refresh_priority=_refresh_priority(alert_status),
        sla_minutes=_sla_minutes(alert_status),
        reason_codes=_reason_codes(input_row, alert_status),
    )


def strategy_market_information_decay_alert_v10_payload(
    result: StrategyMarketInformationDecayAlertV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyMarketInformationDecayAlertV10Result:
        raise ValueError(
            "result must be a StrategyMarketInformationDecayAlertV10Result",
        )
    _require_paper_flags("result", result)
    return {
        "market_id": result.market_id,
        "last_primary_update_minutes": _decimal_payload(
            result.last_primary_update_minutes,
        ),
        "last_secondary_update_minutes": _decimal_payload(
            result.last_secondary_update_minutes,
        ),
        "market_price_move_bps": _decimal_payload(result.market_price_move_bps),
        "source_reliability_score": _decimal_payload(
            result.source_reliability_score,
        ),
        "time_to_resolution_minutes": _decimal_payload(
            result.time_to_resolution_minutes,
        ),
        "team_capacity_score": _decimal_payload(result.team_capacity_score),
        "alert_status": result.alert_status,
        "refresh_priority": result.refresh_priority,
        "sla_minutes": _decimal_payload(result.sla_minutes),
        "reason_codes": list(result.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _alert_status(input_row: StrategyMarketInformationDecayAlertV10Input) -> str:
    critical_condition = (
        input_row.last_primary_update_minutes >= PRIMARY_CRITICAL_MINUTES
        or input_row.last_secondary_update_minutes >= SECONDARY_CRITICAL_MINUTES
        or input_row.market_price_move_bps >= MARKET_MOVE_CRITICAL_BPS
        or (
            input_row.time_to_resolution_minutes <= IMMINENT_RESOLUTION_MINUTES
            and (
                input_row.last_primary_update_minutes >= PRIMARY_STALE_MINUTES
                or input_row.last_secondary_update_minutes >= SECONDARY_STALE_MINUTES
                or input_row.market_price_move_bps >= MARKET_MOVE_MATERIAL_BPS
            )
        )
    )
    if critical_condition:
        return "critical"
    if (
        input_row.last_primary_update_minutes >= PRIMARY_STALE_MINUTES
        or input_row.last_secondary_update_minutes >= SECONDARY_STALE_MINUTES
        or input_row.market_price_move_bps >= MARKET_MOVE_MATERIAL_BPS
        or (
            input_row.source_reliability_score <= LOW_SOURCE_RELIABILITY_SCORE
            and (
                input_row.last_primary_update_minutes >= PRIMARY_AGING_MINUTES
                or input_row.last_secondary_update_minutes >= SECONDARY_AGING_MINUTES
            )
        )
    ):
        return "refresh_due"
    if (
        input_row.last_primary_update_minutes >= PRIMARY_AGING_MINUTES
        or input_row.last_secondary_update_minutes >= SECONDARY_AGING_MINUTES
        or input_row.market_price_move_bps >= MARKET_MOVE_WATCH_BPS
    ):
        return "watch"
    return "current"


def _refresh_priority(alert_status: str) -> str:
    if alert_status == "critical":
        return "urgent"
    if alert_status == "refresh_due":
        return "high"
    if alert_status == "watch":
        return "normal"
    if alert_status == "current":
        return "monitor"
    raise ValueError("alert_status is not supported")


def _sla_minutes(alert_status: str) -> Decimal:
    if alert_status == "critical":
        return CRITICAL_SLA_MINUTES
    if alert_status == "refresh_due":
        return REFRESH_DUE_SLA_MINUTES
    if alert_status == "watch":
        return WATCH_SLA_MINUTES
    if alert_status == "current":
        return CURRENT_SLA_MINUTES
    raise ValueError("alert_status is not supported")


def _reason_codes(
    input_row: StrategyMarketInformationDecayAlertV10Input,
    alert_status: str,
) -> tuple[str, ...]:
    if alert_status == "current":
        return ("information_current",)

    codes: list[str] = [f"information_decay_{alert_status}"]
    codes.extend(_market_move_reason_codes(input_row.market_price_move_bps))
    codes.extend(_primary_reason_codes(input_row.last_primary_update_minutes))
    codes.extend(_resolution_reason_codes(input_row.time_to_resolution_minutes))
    codes.extend(_secondary_reason_codes(input_row.last_secondary_update_minutes))
    codes.extend(_source_reliability_reason_codes(input_row.source_reliability_score))
    codes.extend(_team_capacity_reason_codes(input_row.team_capacity_score))
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _market_move_reason_codes(market_price_move_bps: Decimal) -> tuple[str, ...]:
    if market_price_move_bps >= MARKET_MOVE_CRITICAL_BPS:
        return ("market_move_critical",)
    if market_price_move_bps >= MARKET_MOVE_MATERIAL_BPS:
        return ("market_move_material",)
    if market_price_move_bps >= MARKET_MOVE_WATCH_BPS:
        return ("market_move_watch",)
    return ()


def _primary_reason_codes(last_primary_update_minutes: Decimal) -> tuple[str, ...]:
    if last_primary_update_minutes >= PRIMARY_CRITICAL_MINUTES:
        return ("primary_update_critical",)
    if last_primary_update_minutes >= PRIMARY_STALE_MINUTES:
        return ("primary_update_stale",)
    if last_primary_update_minutes >= PRIMARY_AGING_MINUTES:
        return ("primary_update_aging",)
    return ()


def _secondary_reason_codes(last_secondary_update_minutes: Decimal) -> tuple[str, ...]:
    if last_secondary_update_minutes >= SECONDARY_CRITICAL_MINUTES:
        return ("secondary_update_critical",)
    if last_secondary_update_minutes >= SECONDARY_STALE_MINUTES:
        return ("secondary_update_stale",)
    if last_secondary_update_minutes >= SECONDARY_AGING_MINUTES:
        return ("secondary_update_aging",)
    return ()


def _resolution_reason_codes(time_to_resolution_minutes: Decimal) -> tuple[str, ...]:
    if time_to_resolution_minutes <= IMMINENT_RESOLUTION_MINUTES:
        return ("resolution_imminent",)
    if time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
        return ("resolution_near",)
    return ()


def _source_reliability_reason_codes(
    source_reliability_score: Decimal,
) -> tuple[str, ...]:
    if source_reliability_score <= LOW_SOURCE_RELIABILITY_SCORE:
        return ("source_reliability_low",)
    return ()


def _team_capacity_reason_codes(team_capacity_score: Decimal) -> tuple[str, ...]:
    if team_capacity_score <= SEVERELY_CONSTRAINED_TEAM_CAPACITY_SCORE:
        return ("team_capacity_severely_constrained",)
    if team_capacity_score <= CONSTRAINED_TEAM_CAPACITY_SCORE:
        return ("team_capacity_constrained",)
    return ()


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(VALUE_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} precision is too granular")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _normalize_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of the allowed values")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    if not value.is_finite():
        raise ValueError("payload decimal must be finite")
    return format(value, "f")
