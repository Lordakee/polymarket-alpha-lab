"""Pure paper team specialist capacity pressure v10 reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "TeamSpecialistCapacityPressureV10Input",
    "TeamSpecialistCapacityPressureV10Result",
    "evaluate_team_specialist_capacity_pressure_v10",
    "team_specialist_capacity_pressure_v10_payload",
)


DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
LOW_CAPACITY_BUFFER_RATIO = Decimal("0.100000")
THIN_CAPACITY_BUFFER_RATIO = Decimal("0.250000")
ELEVATED_URGENT_TICKET_COUNT = Decimal("2.000000")
HIGH_URGENT_TICKET_COUNT = Decimal("4.000000")
HIGH_OPEN_TICKET_COUNT = Decimal("10.000000")
STALE_TICKET_AGE_MINUTES = Decimal("120.000000")
WATCH_TRUST_SCORE = Decimal("0.650000")
LOW_TRUST_SCORE = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PRESSURE_STATUSES = ("normal", "strained", "pressured", "critical")
TRIAGE_ACTIONS = (
    "continue_monitoring",
    "prioritize_aging_tickets",
    "rebalance_queue_and_prioritize_urgent",
    "pause_new_intake_and_escalate_specialist",
)
SENSITIVE_MARKERS = (
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "private_key",
    "access_key",
    "access_token",
    "bearer ",
    "://",
    "@",
)


@dataclass(frozen=True)
class TeamSpecialistCapacityPressureV10Input:
    team_id: str
    category: str
    open_ticket_count: Decimal
    urgent_ticket_count: Decimal
    capacity_minutes: Decimal
    committed_minutes: Decimal
    average_ticket_age_minutes: Decimal
    trust_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category", self.category)
        for field_name in (
            "open_ticket_count",
            "urgent_ticket_count",
            "committed_minutes",
            "average_ticket_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "capacity_minutes",
            _normalize_positive_decimal("capacity_minutes", self.capacity_minutes),
        )
        object.__setattr__(
            self,
            "trust_score",
            _normalize_probability("trust_score", self.trust_score),
        )
        if self.urgent_ticket_count > self.open_ticket_count:
            raise ValueError("urgent_ticket_count must not exceed open_ticket_count")
        _require_safety_flags("input", self)


@dataclass(frozen=True)
class TeamSpecialistCapacityPressureV10Result:
    team_id: str
    category: str
    open_ticket_count: Decimal
    urgent_ticket_count: Decimal
    capacity_minutes: Decimal
    committed_minutes: Decimal
    average_ticket_age_minutes: Decimal
    trust_score: Decimal
    available_capacity_minutes: Decimal
    pressure_status: str
    triage_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category", self.category)
        for field_name in (
            "open_ticket_count",
            "urgent_ticket_count",
            "committed_minutes",
            "average_ticket_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "capacity_minutes",
            _normalize_positive_decimal("capacity_minutes", self.capacity_minutes),
        )
        object.__setattr__(
            self,
            "trust_score",
            _normalize_probability("trust_score", self.trust_score),
        )
        object.__setattr__(
            self,
            "available_capacity_minutes",
            _normalize_decimal(
                "available_capacity_minutes",
                self.available_capacity_minutes,
            ),
        )
        if self.urgent_ticket_count > self.open_ticket_count:
            raise ValueError("urgent_ticket_count must not exceed open_ticket_count")
        _require_member("pressure_status", self.pressure_status, PRESSURE_STATUSES)
        _require_member("triage_action", self.triage_action, TRIAGE_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return team_specialist_capacity_pressure_v10_payload(self)


def evaluate_team_specialist_capacity_pressure_v10(
    capacity_signal: TeamSpecialistCapacityPressureV10Input,
) -> TeamSpecialistCapacityPressureV10Result:
    if type(capacity_signal) is not TeamSpecialistCapacityPressureV10Input:
        raise ValueError(
            "capacity_signal must be a TeamSpecialistCapacityPressureV10Input",
        )
    _require_safety_flags("capacity_signal", capacity_signal)
    available_capacity_minutes = _available_capacity_minutes(capacity_signal)
    pressure_status = _pressure_status(
        capacity_signal,
        available_capacity_minutes=available_capacity_minutes,
    )
    return TeamSpecialistCapacityPressureV10Result(
        team_id=capacity_signal.team_id,
        category=capacity_signal.category,
        open_ticket_count=capacity_signal.open_ticket_count,
        urgent_ticket_count=capacity_signal.urgent_ticket_count,
        capacity_minutes=capacity_signal.capacity_minutes,
        committed_minutes=capacity_signal.committed_minutes,
        average_ticket_age_minutes=capacity_signal.average_ticket_age_minutes,
        trust_score=capacity_signal.trust_score,
        available_capacity_minutes=available_capacity_minutes,
        pressure_status=pressure_status,
        triage_action=_triage_action(pressure_status),
        reason_codes=_reason_codes(
            capacity_signal,
            available_capacity_minutes=available_capacity_minutes,
        ),
    )


def team_specialist_capacity_pressure_v10_payload(
    result: TeamSpecialistCapacityPressureV10Result,
) -> dict[str, Any]:
    if type(result) is not TeamSpecialistCapacityPressureV10Result:
        raise ValueError("result must be a TeamSpecialistCapacityPressureV10Result")
    _require_safety_flags("result", result)
    return {
        "team_id": result.team_id,
        "category": result.category,
        "open_ticket_count": _decimal_payload(result.open_ticket_count),
        "urgent_ticket_count": _decimal_payload(result.urgent_ticket_count),
        "capacity_minutes": _decimal_payload(result.capacity_minutes),
        "committed_minutes": _decimal_payload(result.committed_minutes),
        "average_ticket_age_minutes": _decimal_payload(
            result.average_ticket_age_minutes,
        ),
        "trust_score": _decimal_payload(result.trust_score),
        "available_capacity_minutes": _decimal_payload(
            result.available_capacity_minutes,
        ),
        "pressure_status": result.pressure_status,
        "triage_action": result.triage_action,
        "reason_codes": list(result.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _available_capacity_minutes(
    capacity_signal: TeamSpecialistCapacityPressureV10Input,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            "available_capacity_minutes",
            capacity_signal.capacity_minutes - capacity_signal.committed_minutes,
        )


def _capacity_buffer_ratio(
    capacity_signal: TeamSpecialistCapacityPressureV10Input,
    *,
    available_capacity_minutes: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            "capacity_buffer_ratio",
            available_capacity_minutes / capacity_signal.capacity_minutes,
        )


def _pressure_status(
    capacity_signal: TeamSpecialistCapacityPressureV10Input,
    *,
    available_capacity_minutes: Decimal,
) -> str:
    if available_capacity_minutes < ZERO:
        return "critical"
    capacity_buffer_ratio = _capacity_buffer_ratio(
        capacity_signal,
        available_capacity_minutes=available_capacity_minutes,
    )
    if (
        capacity_buffer_ratio <= LOW_CAPACITY_BUFFER_RATIO
        or capacity_signal.urgent_ticket_count >= ELEVATED_URGENT_TICKET_COUNT
        or capacity_signal.average_ticket_age_minutes >= STALE_TICKET_AGE_MINUTES
        or capacity_signal.trust_score <= WATCH_TRUST_SCORE
    ):
        return "pressured"
    if (
        capacity_buffer_ratio <= THIN_CAPACITY_BUFFER_RATIO
        or capacity_signal.urgent_ticket_count > ZERO
    ):
        return "strained"
    return "normal"


def _triage_action(pressure_status: str) -> str:
    if pressure_status == "critical":
        return "pause_new_intake_and_escalate_specialist"
    if pressure_status == "pressured":
        return "rebalance_queue_and_prioritize_urgent"
    if pressure_status == "strained":
        return "prioritize_aging_tickets"
    return "continue_monitoring"


def _reason_codes(
    capacity_signal: TeamSpecialistCapacityPressureV10Input,
    *,
    available_capacity_minutes: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    capacity_buffer_ratio = _capacity_buffer_ratio(
        capacity_signal,
        available_capacity_minutes=available_capacity_minutes,
    )
    if available_capacity_minutes < ZERO:
        reason_codes.append("capacity_deficit_critical")
    elif capacity_buffer_ratio <= LOW_CAPACITY_BUFFER_RATIO:
        reason_codes.append("capacity_buffer_low")
    elif capacity_buffer_ratio <= THIN_CAPACITY_BUFFER_RATIO:
        reason_codes.append("capacity_buffer_thin")

    if capacity_signal.urgent_ticket_count >= HIGH_URGENT_TICKET_COUNT:
        reason_codes.append("urgent_ticket_pressure_high")
    elif capacity_signal.urgent_ticket_count >= ELEVATED_URGENT_TICKET_COUNT:
        reason_codes.append("urgent_ticket_pressure_elevated")
    elif capacity_signal.urgent_ticket_count > ZERO:
        reason_codes.append("urgent_ticket_present")

    if capacity_signal.open_ticket_count >= HIGH_OPEN_TICKET_COUNT:
        reason_codes.append("backlog_pressure_high")
    if capacity_signal.average_ticket_age_minutes >= STALE_TICKET_AGE_MINUTES:
        reason_codes.append("ticket_age_stale")
    if capacity_signal.trust_score <= LOW_TRUST_SCORE:
        reason_codes.append("trust_score_low")
    elif capacity_signal.trust_score <= WATCH_TRUST_SCORE:
        reason_codes.append("trust_score_watch")

    if not reason_codes:
        reason_codes.append("capacity_within_plan")
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(DECIMAL_QUANTUM)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return decimal_value


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(DECIMAL_QUANTUM)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if not value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(value)


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_safety_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_text(value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError("must not contain sensitive material")


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    return format(value, "f")
