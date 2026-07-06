"""Paper-only specialist team load smoothing reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "StrategyTeamSpecialistLoadSmoothingV10Input",
    "StrategyTeamSpecialistLoadSmoothingV10Result",
    "recommend_strategy_team_specialist_load_smoothing_v10",
    "strategy_team_specialist_load_smoothing_v10_payload",
)


DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

QUEUE_DEPTH_FULL_PRESSURE = Decimal("20.000000")
URGENT_CANDIDATE_FULL_PRESSURE = Decimal("5.000000")
STALE_PACKET_FULL_PRESSURE = Decimal("4.000000")
ERROR_RATE_FULL_PRESSURE = Decimal("0.250000")
TARGET_ANALYST_CAPACITY = Decimal("4.000000")

QUEUE_PRESSURE_WEIGHT = Decimal("0.180000")
URGENCY_PRESSURE_WEIGHT = Decimal("0.300000")
STALE_PRESSURE_WEIGHT = Decimal("0.096000")
ERROR_PRESSURE_WEIGHT = Decimal("0.300000")
CAPACITY_GAP_WEIGHT = Decimal("0.124000")

REDISTRIBUTE_PRESSURE_THRESHOLD = Decimal("0.700000")
STAGE_SUPPORT_PRESSURE_THRESHOLD = Decimal("0.250000")
HIGH_QUEUE_DEPTH = Decimal("12")
HIGH_URGENT_CANDIDATE_COUNT = Decimal("3")
HIGH_STALE_PACKET_COUNT = Decimal("3")
PRESENT_STALE_PACKET_COUNT = Decimal("1")
HIGH_ERROR_RATE = Decimal("0.200000")
ELEVATED_ERROR_RATE = Decimal("0.100000")
CONSTRAINED_ANALYST_CAPACITY = Decimal("1")
WATCH_ANALYST_CAPACITY = Decimal("2")

SMOOTHING_STATUSES = (
    "redistribute_now",
    "stage_support",
    "hold_capacity",
)
SMOOTHING_ACTIONS = (
    "shift_urgent_candidates_to_available_analysts",
    "pair_review_stale_packets",
    "add_temporary_analyst_capacity",
    "rebalance_queue_intake",
    "keep_current_specialist_load",
)
REDISTRIBUTE_REASON_CODE = "specialist_load_smoothing_redistribute_now"
STAGE_SUPPORT_REASON_CODE = "specialist_load_smoothing_stage_support"
HOLD_CAPACITY_REASON_CODE = "specialist_load_smoothing_hold_capacity"
REASON_CODE_PRIORITY = (
    "specialist_load_smoothing_input",
    REDISTRIBUTE_REASON_CODE,
    STAGE_SUPPORT_REASON_CODE,
    HOLD_CAPACITY_REASON_CODE,
    "queue_depth_high",
    "queue_depth_contained",
    "urgent_candidates_high",
    "urgent_candidates_contained",
    "stale_packets_high",
    "stale_packets_present",
    "stale_packets_contained",
    "error_rate_high",
    "error_rate_elevated",
    "error_rate_contained",
    "analyst_capacity_constrained",
    "analyst_capacity_watch",
    "analyst_capacity_available",
)
REASON_CODE_SORT_PRIORITY = {
    reason_code: index for index, reason_code in enumerate(REASON_CODE_PRIORITY)
}
SENSITIVE_PUBLIC_TEXT_FRAGMENTS = (
    "secret",
    "token",
    "private",
    "password",
    "bearer",
    "dsn",
)


@dataclass(frozen=True)
class StrategyTeamSpecialistLoadSmoothingV10Input:
    team_id: str
    specialist_domain: str
    queue_depth: Decimal
    urgent_candidate_count: Decimal
    stale_packet_count: Decimal
    recent_error_rate: Decimal
    available_analyst_capacity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("team_id", self.team_id)
        _require_public_string("specialist_domain", self.specialist_domain)
        for field_name in (
            "queue_depth",
            "urgent_candidate_count",
            "stale_packet_count",
            "available_analyst_capacity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recent_error_rate",
            _normalize_probability_decimal(
                "recent_error_rate",
                self.recent_error_rate,
            ),
        )
        _validate_load_input(self)
        require_paper_only_flags("specialist load smoothing input", self)


@dataclass(frozen=True)
class StrategyTeamSpecialistLoadSmoothingV10Result:
    team_id: str
    specialist_domain: str
    queue_depth: Decimal
    urgent_candidate_count: Decimal
    stale_packet_count: Decimal
    recent_error_rate: Decimal
    available_analyst_capacity: Decimal
    queue_pressure_score: Decimal
    urgency_pressure_score: Decimal
    stale_pressure_score: Decimal
    error_pressure_score: Decimal
    capacity_gap_score: Decimal
    smoothing_pressure_score: Decimal
    smoothing_status: str
    recommended_smoothing_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("team_id", self.team_id)
        _require_public_string("specialist_domain", self.specialist_domain)
        for field_name in (
            "queue_depth",
            "urgent_candidate_count",
            "stale_packet_count",
            "available_analyst_capacity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recent_error_rate",
            "queue_pressure_score",
            "urgency_pressure_score",
            "stale_pressure_score",
            "error_pressure_score",
            "capacity_gap_score",
            "smoothing_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("smoothing_status", self.smoothing_status, SMOOTHING_STATUSES)
        _require_member(
            "recommended_smoothing_action",
            self.recommended_smoothing_action,
            SMOOTHING_ACTIONS,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_result(self)
        _reject_unsafe_public_payload("specialist load smoothing result", self)
        require_paper_only_flags("specialist load smoothing result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_team_specialist_load_smoothing_v10_payload(self)


def recommend_strategy_team_specialist_load_smoothing_v10(
    load_input: StrategyTeamSpecialistLoadSmoothingV10Input,
) -> StrategyTeamSpecialistLoadSmoothingV10Result:
    if type(load_input) is not StrategyTeamSpecialistLoadSmoothingV10Input:
        raise ValueError(
            "load_input must be a StrategyTeamSpecialistLoadSmoothingV10Input",
        )
    require_paper_only_flags("specialist load smoothing input", load_input)

    queue_pressure_score = _queue_pressure_score(load_input.queue_depth)
    urgency_pressure_score = _urgency_pressure_score(load_input.urgent_candidate_count)
    stale_pressure_score = _stale_pressure_score(load_input.stale_packet_count)
    error_pressure_score = _error_pressure_score(load_input.recent_error_rate)
    capacity_gap_score = _capacity_gap_score(load_input.available_analyst_capacity)
    smoothing_pressure_score = _smoothing_pressure_score(
        queue_pressure_score=queue_pressure_score,
        urgency_pressure_score=urgency_pressure_score,
        stale_pressure_score=stale_pressure_score,
        error_pressure_score=error_pressure_score,
        capacity_gap_score=capacity_gap_score,
    )
    smoothing_status = _smoothing_status(load_input, smoothing_pressure_score)

    return StrategyTeamSpecialistLoadSmoothingV10Result(
        team_id=load_input.team_id,
        specialist_domain=load_input.specialist_domain,
        queue_depth=load_input.queue_depth,
        urgent_candidate_count=load_input.urgent_candidate_count,
        stale_packet_count=load_input.stale_packet_count,
        recent_error_rate=load_input.recent_error_rate,
        available_analyst_capacity=load_input.available_analyst_capacity,
        queue_pressure_score=queue_pressure_score,
        urgency_pressure_score=urgency_pressure_score,
        stale_pressure_score=stale_pressure_score,
        error_pressure_score=error_pressure_score,
        capacity_gap_score=capacity_gap_score,
        smoothing_pressure_score=smoothing_pressure_score,
        smoothing_status=smoothing_status,
        recommended_smoothing_action=_recommended_smoothing_action(
            load_input,
            smoothing_status=smoothing_status,
        ),
        reason_codes=_reason_codes(load_input, smoothing_status),
    )


def strategy_team_specialist_load_smoothing_v10_payload(
    result: StrategyTeamSpecialistLoadSmoothingV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyTeamSpecialistLoadSmoothingV10Result:
        raise ValueError(
            "result must be a StrategyTeamSpecialistLoadSmoothingV10Result",
        )
    require_paper_only_flags("specialist load smoothing result", result)
    _reject_unsafe_public_payload("specialist load smoothing result", result)
    payload = {
        "team_id": result.team_id,
        "specialist_domain": result.specialist_domain,
        "queue_depth": _decimal_payload(result.queue_depth),
        "urgent_candidate_count": _decimal_payload(result.urgent_candidate_count),
        "stale_packet_count": _decimal_payload(result.stale_packet_count),
        "recent_error_rate": _decimal_payload(result.recent_error_rate),
        "available_analyst_capacity": _decimal_payload(
            result.available_analyst_capacity,
        ),
        "queue_pressure_score": _decimal_payload(result.queue_pressure_score),
        "urgency_pressure_score": _decimal_payload(result.urgency_pressure_score),
        "stale_pressure_score": _decimal_payload(result.stale_pressure_score),
        "error_pressure_score": _decimal_payload(result.error_pressure_score),
        "capacity_gap_score": _decimal_payload(result.capacity_gap_score),
        "smoothing_pressure_score": _decimal_payload(
            result.smoothing_pressure_score,
        ),
        "smoothing_status": result.smoothing_status,
        "recommended_smoothing_action": result.recommended_smoothing_action,
        "reason_codes": list(result.reason_codes),
        "paper_only": result.paper_only,
        "report_only": result.report_only,
        "readonly": result.readonly,
    }
    _reject_unsafe_public_payload("specialist load smoothing payload", payload)
    return json_ready_no_floats(payload)


def _queue_pressure_score(queue_depth: Decimal) -> Decimal:
    return _min_decimal(_ratio_decimal(queue_depth, QUEUE_DEPTH_FULL_PRESSURE), ONE)


def _urgency_pressure_score(urgent_candidate_count: Decimal) -> Decimal:
    return _min_decimal(
        _ratio_decimal(urgent_candidate_count, URGENT_CANDIDATE_FULL_PRESSURE),
        ONE,
    )


def _stale_pressure_score(stale_packet_count: Decimal) -> Decimal:
    return _min_decimal(
        _ratio_decimal(stale_packet_count, STALE_PACKET_FULL_PRESSURE),
        ONE,
    )


def _error_pressure_score(recent_error_rate: Decimal) -> Decimal:
    return _min_decimal(_ratio_decimal(recent_error_rate, ERROR_RATE_FULL_PRESSURE), ONE)


def _capacity_gap_score(available_analyst_capacity: Decimal) -> Decimal:
    if available_analyst_capacity >= TARGET_ANALYST_CAPACITY:
        return ZERO
    return _ratio_decimal(
        TARGET_ANALYST_CAPACITY - available_analyst_capacity,
        TARGET_ANALYST_CAPACITY,
    )


def _smoothing_pressure_score(
    *,
    queue_pressure_score: Decimal,
    urgency_pressure_score: Decimal,
    stale_pressure_score: Decimal,
    error_pressure_score: Decimal,
    capacity_gap_score: Decimal,
) -> Decimal:
    pressure = _sum_decimal(
        (
            _multiply_decimal(queue_pressure_score, QUEUE_PRESSURE_WEIGHT),
            _multiply_decimal(urgency_pressure_score, URGENCY_PRESSURE_WEIGHT),
            _multiply_decimal(stale_pressure_score, STALE_PRESSURE_WEIGHT),
            _multiply_decimal(error_pressure_score, ERROR_PRESSURE_WEIGHT),
            _multiply_decimal(capacity_gap_score, CAPACITY_GAP_WEIGHT),
        ),
    )
    return _min_decimal(pressure, ONE)


def _smoothing_status(
    load_input: StrategyTeamSpecialistLoadSmoothingV10Input,
    smoothing_pressure_score: Decimal,
) -> str:
    if (
        smoothing_pressure_score >= REDISTRIBUTE_PRESSURE_THRESHOLD
        or (
            load_input.urgent_candidate_count >= HIGH_URGENT_CANDIDATE_COUNT
            and load_input.available_analyst_capacity <= WATCH_ANALYST_CAPACITY
        )
    ):
        return "redistribute_now"
    if (
        smoothing_pressure_score >= STAGE_SUPPORT_PRESSURE_THRESHOLD
        or load_input.stale_packet_count >= PRESENT_STALE_PACKET_COUNT
        or load_input.recent_error_rate >= ELEVATED_ERROR_RATE
    ):
        return "stage_support"
    return "hold_capacity"


def _recommended_smoothing_action(
    load_input: StrategyTeamSpecialistLoadSmoothingV10Input,
    *,
    smoothing_status: str,
) -> str:
    if smoothing_status == "hold_capacity":
        return "keep_current_specialist_load"
    if smoothing_status == "redistribute_now":
        if load_input.urgent_candidate_count >= HIGH_URGENT_CANDIDATE_COUNT:
            return "shift_urgent_candidates_to_available_analysts"
        if load_input.available_analyst_capacity <= CONSTRAINED_ANALYST_CAPACITY:
            return "add_temporary_analyst_capacity"
        return "rebalance_queue_intake"
    if load_input.stale_packet_count >= PRESENT_STALE_PACKET_COUNT:
        return "pair_review_stale_packets"
    if load_input.available_analyst_capacity <= WATCH_ANALYST_CAPACITY:
        return "add_temporary_analyst_capacity"
    return "rebalance_queue_intake"


def _reason_codes(
    load_input: StrategyTeamSpecialistLoadSmoothingV10Input,
    smoothing_status: str,
) -> tuple[str, ...]:
    reason_codes = [
        "specialist_load_smoothing_input",
        _status_reason_code(smoothing_status),
    ]
    if load_input.queue_depth >= HIGH_QUEUE_DEPTH:
        reason_codes.append("queue_depth_high")
    else:
        reason_codes.append("queue_depth_contained")
    if load_input.urgent_candidate_count >= HIGH_URGENT_CANDIDATE_COUNT:
        reason_codes.append("urgent_candidates_high")
    else:
        reason_codes.append("urgent_candidates_contained")
    if load_input.stale_packet_count >= HIGH_STALE_PACKET_COUNT:
        reason_codes.append("stale_packets_high")
    elif load_input.stale_packet_count >= PRESENT_STALE_PACKET_COUNT:
        reason_codes.append("stale_packets_present")
    else:
        reason_codes.append("stale_packets_contained")
    if load_input.recent_error_rate >= HIGH_ERROR_RATE:
        reason_codes.append("error_rate_high")
    elif load_input.recent_error_rate >= ELEVATED_ERROR_RATE:
        reason_codes.append("error_rate_elevated")
    else:
        reason_codes.append("error_rate_contained")
    if load_input.available_analyst_capacity <= CONSTRAINED_ANALYST_CAPACITY:
        reason_codes.append("analyst_capacity_constrained")
    elif load_input.available_analyst_capacity <= WATCH_ANALYST_CAPACITY:
        reason_codes.append("analyst_capacity_watch")
    else:
        reason_codes.append("analyst_capacity_available")
    return _normalize_reason_codes(tuple(reason_codes))


def _status_reason_code(smoothing_status: str) -> str:
    if smoothing_status == "redistribute_now":
        return REDISTRIBUTE_REASON_CODE
    if smoothing_status == "stage_support":
        return STAGE_SUPPORT_REASON_CODE
    if smoothing_status == "hold_capacity":
        return HOLD_CAPACITY_REASON_CODE
    raise ValueError("smoothing_status must be a known value")


def _validate_load_input(
    load_input: StrategyTeamSpecialistLoadSmoothingV10Input,
) -> None:
    if load_input.urgent_candidate_count > load_input.queue_depth:
        raise ValueError("urgent_candidate_count must not exceed queue_depth")
    if load_input.stale_packet_count > load_input.queue_depth:
        raise ValueError("stale_packet_count must not exceed queue_depth")


def _validate_result(result: StrategyTeamSpecialistLoadSmoothingV10Result) -> None:
    load_input = StrategyTeamSpecialistLoadSmoothingV10Input(
        team_id=result.team_id,
        specialist_domain=result.specialist_domain,
        queue_depth=result.queue_depth,
        urgent_candidate_count=result.urgent_candidate_count,
        stale_packet_count=result.stale_packet_count,
        recent_error_rate=result.recent_error_rate,
        available_analyst_capacity=result.available_analyst_capacity,
    )
    if result.queue_pressure_score != _queue_pressure_score(result.queue_depth):
        raise ValueError("queue_pressure_score must match inputs")
    if result.urgency_pressure_score != _urgency_pressure_score(
        result.urgent_candidate_count,
    ):
        raise ValueError("urgency_pressure_score must match inputs")
    if result.stale_pressure_score != _stale_pressure_score(result.stale_packet_count):
        raise ValueError("stale_pressure_score must match inputs")
    if result.error_pressure_score != _error_pressure_score(result.recent_error_rate):
        raise ValueError("error_pressure_score must match inputs")
    if result.capacity_gap_score != _capacity_gap_score(
        result.available_analyst_capacity,
    ):
        raise ValueError("capacity_gap_score must match inputs")
    expected_pressure = _smoothing_pressure_score(
        queue_pressure_score=result.queue_pressure_score,
        urgency_pressure_score=result.urgency_pressure_score,
        stale_pressure_score=result.stale_pressure_score,
        error_pressure_score=result.error_pressure_score,
        capacity_gap_score=result.capacity_gap_score,
    )
    if result.smoothing_pressure_score != expected_pressure:
        raise ValueError("smoothing_pressure_score must match inputs")
    expected_status = _smoothing_status(load_input, result.smoothing_pressure_score)
    if result.smoothing_status != expected_status:
        raise ValueError("smoothing_status must match inputs")
    if result.recommended_smoothing_action != _recommended_smoothing_action(
        load_input,
        smoothing_status=result.smoothing_status,
    ):
        raise ValueError("recommended_smoothing_action must match inputs")
    if result.reason_codes != _reason_codes(load_input, result.smoothing_status):
        raise ValueError("reason_codes must match inputs")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _tuple_from_iterable("reason_codes", value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SORT_PRIORITY:
            raise ValueError("reason_codes must contain known strings")
    normalized = tuple(dict.fromkeys(reason_codes))
    if normalized != tuple(
        sorted(normalized, key=lambda code: REASON_CODE_SORT_PRIORITY[code]),
    ):
        raise ValueError("reason_codes must use deterministic sequencing")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    with localcontext(DECIMAL_CONTEXT):
        return normalized.quantize(COUNT_QUANTUM)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "":
        raise ValueError(f"{field_name} must not be empty")
    if _contains_sensitive_text(value):
        raise ValueError(f"{field_name} must not contain sensitive content")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    for item in _iter_values(value):
        if type(item) is str and _contains_sensitive_text(item):
            raise ValueError(f"{label} contains sensitive public text")


def _iter_values(value: object) -> tuple[object, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_values(asdict(value))
    if isinstance(value, dict):
        values: list[object] = []
        for item in value.values():
            values.append(item)
            values.extend(_iter_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.append(item)
            values.extend(_iter_values(item))
        return tuple(values)
    return ()


def _contains_sensitive_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in SENSITIVE_PUBLIC_TEXT_FRAGMENTS)


def _ratio_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(QUANTUM)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(QUANTUM)


def _min_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(left, right).quantize(QUANTUM)


def _tuple_from_iterable(field_name: str, value: object) -> tuple[Any, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        return tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload value must be a Decimal")
    if not value.is_finite():
        raise ValueError("payload Decimal value must be finite")
    return str(value)
