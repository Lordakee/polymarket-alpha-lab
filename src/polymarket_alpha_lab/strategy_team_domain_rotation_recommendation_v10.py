"""Paper-only team domain rotation recommendation reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "StrategyTeamDomainRotationRecommendationV10Input",
    "StrategyTeamDomainRotationRecommendationV10Result",
    "recommend_strategy_team_domain_rotation_v10",
    "strategy_team_domain_rotation_recommendation_v10_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

CALIBRATION_PRESSURE_BPS = Decimal("1000.000000")
TENURE_FULL_PRESSURE_DAYS = Decimal("90.000000")
MIN_ROTATION_TENURE_DAYS = Decimal("30.000000")
MIN_ROTATION_LEARNING_SCORE = Decimal("0.600000")
ROTATE_PRIORITY_THRESHOLD = Decimal("0.450000")
WATCH_PRIORITY_THRESHOLD = Decimal("0.250000")
WEAK_HIT_RATE_THRESHOLD = Decimal("0.600000")
CRITICAL_HIT_RATE_THRESHOLD = Decimal("0.400000")
CRITICAL_HIT_RATE_PRIORITY_PENALTY = Decimal("0.099000")
HIGH_CALIBRATION_ERROR_BPS = Decimal("300.000000")
HIGH_SOURCE_GAP_RATE = Decimal("0.400000")
ELEVATED_SOURCE_GAP_RATE = Decimal("0.250000")
HIGH_QUEUE_PRESSURE_SCORE = Decimal("0.600000")

HIT_RATE_PRESSURE_WEIGHT = Decimal("0.250000")
CALIBRATION_PRESSURE_WEIGHT = Decimal("0.200000")
SOURCE_GAP_WEIGHT = Decimal("0.200000")
QUEUE_PRESSURE_WEIGHT = Decimal("0.150000")
TENURE_PRESSURE_WEIGHT = Decimal("0.100000")
LEARNING_GAP_WEIGHT = Decimal("0.100000")

ROTATION_STATUSES = ("rotate", "watch", "hold")
DOMAIN_ACTIONS = (
    "rotate_to_adjacent_domain",
    "repair_sources_before_rotation",
    "extend_domain_learning_window",
    "continue_current_domain",
    "monitor_current_domain",
)
ROTATE_REASON_CODE = "team_domain_rotation_rotate"
WATCH_REASON_CODE = "team_domain_rotation_watch"
HOLD_REASON_CODE = "team_domain_rotation_hold"
REASON_CODE_PRIORITY = (
    "team_domain_rotation_input",
    ROTATE_REASON_CODE,
    WATCH_REASON_CODE,
    HOLD_REASON_CODE,
    "hit_rate_weak",
    "hit_rate_stable",
    "calibration_error_high",
    "calibration_error_contained",
    "source_gap_high",
    "source_gap_elevated",
    "source_gap_contained",
    "queue_pressure_high",
    "queue_pressure_contained",
    "domain_tenure_mature",
    "domain_tenure_short",
    "domain_learning_sufficient",
    "domain_learning_developing",
)
REASON_CODE_SORT_PRIORITY = {
    reason_code: index for index, reason_code in enumerate(REASON_CODE_PRIORITY)
}
SENSITIVE_PUBLIC_TEXT_FRAGMENTS = (
    "secret",
    "token",
    "private",
    "key",
    "bearer",
    "dsn",
    "password",
    "wallet",
)


@dataclass(frozen=True)
class StrategyTeamDomainRotationRecommendationV10Input:
    team_id: str
    current_domain: str
    recent_hit_rate: Decimal
    calibration_error_bps: Decimal
    source_gap_rate: Decimal
    queue_pressure_score: Decimal
    days_in_domain: Decimal
    domain_learning_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("team_id", self.team_id)
        _require_public_string("current_domain", self.current_domain)
        for field_name in (
            "recent_hit_rate",
            "source_gap_rate",
            "queue_pressure_score",
            "domain_learning_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_error_bps",
            _normalize_nonnegative_decimal(
                "calibration_error_bps",
                self.calibration_error_bps,
            ),
        )
        object.__setattr__(
            self,
            "days_in_domain",
            _normalize_count_decimal("days_in_domain", self.days_in_domain),
        )
        require_paper_only_flags("rotation input", self)


@dataclass(frozen=True)
class StrategyTeamDomainRotationRecommendationV10Result:
    team_id: str
    current_domain: str
    recent_hit_rate: Decimal
    calibration_error_bps: Decimal
    source_gap_rate: Decimal
    queue_pressure_score: Decimal
    days_in_domain: Decimal
    domain_learning_score: Decimal
    hit_rate_pressure_score: Decimal
    calibration_pressure_score: Decimal
    domain_tenure_pressure_score: Decimal
    domain_learning_gap_score: Decimal
    rotation_status: str
    recommended_domain_action: str
    rotation_priority: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("team_id", self.team_id)
        _require_public_string("current_domain", self.current_domain)
        for field_name in (
            "recent_hit_rate",
            "source_gap_rate",
            "queue_pressure_score",
            "domain_learning_score",
            "hit_rate_pressure_score",
            "calibration_pressure_score",
            "domain_tenure_pressure_score",
            "domain_learning_gap_score",
            "rotation_priority",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_error_bps",
            _normalize_nonnegative_decimal(
                "calibration_error_bps",
                self.calibration_error_bps,
            ),
        )
        object.__setattr__(
            self,
            "days_in_domain",
            _normalize_count_decimal("days_in_domain", self.days_in_domain),
        )
        _require_member("rotation_status", self.rotation_status, ROTATION_STATUSES)
        _require_member(
            "recommended_domain_action",
            self.recommended_domain_action,
            DOMAIN_ACTIONS,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_result(self)
        _reject_unsafe_public_payload("domain rotation recommendation result", self)
        require_paper_only_flags("rotation result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_team_domain_rotation_recommendation_v10_payload(self)


def recommend_strategy_team_domain_rotation_v10(
    rotation_input: StrategyTeamDomainRotationRecommendationV10Input,
) -> StrategyTeamDomainRotationRecommendationV10Result:
    if type(rotation_input) is not StrategyTeamDomainRotationRecommendationV10Input:
        raise ValueError(
            "rotation_input must be a "
            "StrategyTeamDomainRotationRecommendationV10Input",
        )
    require_paper_only_flags("rotation input", rotation_input)

    hit_rate_pressure_score = _hit_rate_pressure_score(rotation_input.recent_hit_rate)
    calibration_pressure_score = _calibration_pressure_score(
        rotation_input.calibration_error_bps,
    )
    domain_tenure_pressure_score = _domain_tenure_pressure_score(
        rotation_input.days_in_domain,
    )
    domain_learning_gap_score = _domain_learning_gap_score(
        rotation_input.domain_learning_score,
    )
    rotation_priority = _rotation_priority(
        recent_hit_rate=rotation_input.recent_hit_rate,
        hit_rate_pressure_score=hit_rate_pressure_score,
        calibration_pressure_score=calibration_pressure_score,
        source_gap_rate=rotation_input.source_gap_rate,
        queue_pressure_score=rotation_input.queue_pressure_score,
        domain_tenure_pressure_score=domain_tenure_pressure_score,
        domain_learning_gap_score=domain_learning_gap_score,
    )
    rotation_status = _rotation_status(rotation_input, rotation_priority)

    return StrategyTeamDomainRotationRecommendationV10Result(
        team_id=rotation_input.team_id,
        current_domain=rotation_input.current_domain,
        recent_hit_rate=rotation_input.recent_hit_rate,
        calibration_error_bps=rotation_input.calibration_error_bps,
        source_gap_rate=rotation_input.source_gap_rate,
        queue_pressure_score=rotation_input.queue_pressure_score,
        days_in_domain=rotation_input.days_in_domain,
        domain_learning_score=rotation_input.domain_learning_score,
        hit_rate_pressure_score=hit_rate_pressure_score,
        calibration_pressure_score=calibration_pressure_score,
        domain_tenure_pressure_score=domain_tenure_pressure_score,
        domain_learning_gap_score=domain_learning_gap_score,
        rotation_status=rotation_status,
        recommended_domain_action=_recommended_domain_action(
            rotation_input,
            rotation_status=rotation_status,
        ),
        rotation_priority=rotation_priority,
        reason_codes=_reason_codes(rotation_input, rotation_status),
    )


def strategy_team_domain_rotation_recommendation_v10_payload(
    result: StrategyTeamDomainRotationRecommendationV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyTeamDomainRotationRecommendationV10Result:
        raise ValueError(
            "result must be a StrategyTeamDomainRotationRecommendationV10Result",
        )
    require_paper_only_flags("rotation result", result)
    _reject_unsafe_public_payload("domain rotation recommendation result", result)
    payload = {
        "team_id": result.team_id,
        "current_domain": result.current_domain,
        "recent_hit_rate": _decimal_payload(result.recent_hit_rate),
        "calibration_error_bps": _decimal_payload(result.calibration_error_bps),
        "source_gap_rate": _decimal_payload(result.source_gap_rate),
        "queue_pressure_score": _decimal_payload(result.queue_pressure_score),
        "days_in_domain": _decimal_payload(result.days_in_domain),
        "domain_learning_score": _decimal_payload(result.domain_learning_score),
        "hit_rate_pressure_score": _decimal_payload(result.hit_rate_pressure_score),
        "calibration_pressure_score": _decimal_payload(
            result.calibration_pressure_score,
        ),
        "domain_tenure_pressure_score": _decimal_payload(
            result.domain_tenure_pressure_score,
        ),
        "domain_learning_gap_score": _decimal_payload(
            result.domain_learning_gap_score,
        ),
        "rotation_status": result.rotation_status,
        "recommended_domain_action": result.recommended_domain_action,
        "rotation_priority": _decimal_payload(result.rotation_priority),
        "reason_codes": list(result.reason_codes),
        "paper_only": result.paper_only,
        "report_only": result.report_only,
        "readonly": result.readonly,
    }
    _reject_unsafe_public_payload("domain rotation recommendation payload", payload)
    return json_ready_no_floats(payload)


def _hit_rate_pressure_score(recent_hit_rate: Decimal) -> Decimal:
    return _subtract_decimal(ONE, recent_hit_rate)


def _calibration_pressure_score(calibration_error_bps: Decimal) -> Decimal:
    return _min_decimal(
        _ratio_decimal(calibration_error_bps, CALIBRATION_PRESSURE_BPS),
        ONE,
    )


def _domain_tenure_pressure_score(days_in_domain: Decimal) -> Decimal:
    return _min_decimal(_ratio_decimal(days_in_domain, TENURE_FULL_PRESSURE_DAYS), ONE)


def _domain_learning_gap_score(domain_learning_score: Decimal) -> Decimal:
    return _subtract_decimal(ONE, domain_learning_score)


def _rotation_priority(
    *,
    recent_hit_rate: Decimal,
    hit_rate_pressure_score: Decimal,
    calibration_pressure_score: Decimal,
    source_gap_rate: Decimal,
    queue_pressure_score: Decimal,
    domain_tenure_pressure_score: Decimal,
    domain_learning_gap_score: Decimal,
) -> Decimal:
    priority = _sum_decimal(
        (
            _multiply_decimal(hit_rate_pressure_score, HIT_RATE_PRESSURE_WEIGHT),
            _multiply_decimal(
                calibration_pressure_score,
                CALIBRATION_PRESSURE_WEIGHT,
            ),
            _multiply_decimal(source_gap_rate, SOURCE_GAP_WEIGHT),
            _multiply_decimal(queue_pressure_score, QUEUE_PRESSURE_WEIGHT),
            _multiply_decimal(
                domain_tenure_pressure_score,
                TENURE_PRESSURE_WEIGHT,
            ),
            _multiply_decimal(domain_learning_gap_score, LEARNING_GAP_WEIGHT),
        ),
    )
    if recent_hit_rate < CRITICAL_HIT_RATE_THRESHOLD:
        priority = _add_decimal(priority, CRITICAL_HIT_RATE_PRIORITY_PENALTY)
    return _min_decimal(priority, ONE)


def _rotation_status(
    rotation_input: StrategyTeamDomainRotationRecommendationV10Input,
    rotation_priority: Decimal,
) -> str:
    if (
        rotation_priority >= ROTATE_PRIORITY_THRESHOLD
        and rotation_input.days_in_domain >= MIN_ROTATION_TENURE_DAYS
        and rotation_input.domain_learning_score >= MIN_ROTATION_LEARNING_SCORE
    ):
        return "rotate"
    if (
        rotation_priority >= WATCH_PRIORITY_THRESHOLD
        or rotation_input.source_gap_rate >= ELEVATED_SOURCE_GAP_RATE
    ):
        return "watch"
    return "hold"


def _recommended_domain_action(
    rotation_input: StrategyTeamDomainRotationRecommendationV10Input,
    *,
    rotation_status: str,
) -> str:
    if rotation_status == "rotate":
        return "rotate_to_adjacent_domain"
    if rotation_status == "hold":
        return "continue_current_domain"
    if (
        rotation_input.days_in_domain < Decimal("10.000000")
        and (
            rotation_input.recent_hit_rate < WEAK_HIT_RATE_THRESHOLD
            or rotation_input.queue_pressure_score >= HIGH_QUEUE_PRESSURE_SCORE
        )
    ):
        return "extend_domain_learning_window"
    if rotation_input.source_gap_rate >= ELEVATED_SOURCE_GAP_RATE:
        return "repair_sources_before_rotation"
    if rotation_input.domain_learning_score < MIN_ROTATION_LEARNING_SCORE:
        return "extend_domain_learning_window"
    return "monitor_current_domain"


def _reason_codes(
    rotation_input: StrategyTeamDomainRotationRecommendationV10Input,
    rotation_status: str,
) -> tuple[str, ...]:
    reason_codes = [
        "team_domain_rotation_input",
        _status_reason_code(rotation_status),
    ]
    if rotation_input.recent_hit_rate < WEAK_HIT_RATE_THRESHOLD:
        reason_codes.append("hit_rate_weak")
    else:
        reason_codes.append("hit_rate_stable")
    if rotation_input.calibration_error_bps >= HIGH_CALIBRATION_ERROR_BPS:
        reason_codes.append("calibration_error_high")
    else:
        reason_codes.append("calibration_error_contained")
    if rotation_input.source_gap_rate >= HIGH_SOURCE_GAP_RATE:
        reason_codes.append("source_gap_high")
    elif rotation_input.source_gap_rate >= ELEVATED_SOURCE_GAP_RATE:
        reason_codes.append("source_gap_elevated")
    else:
        reason_codes.append("source_gap_contained")
    if rotation_input.queue_pressure_score >= HIGH_QUEUE_PRESSURE_SCORE:
        reason_codes.append("queue_pressure_high")
    else:
        reason_codes.append("queue_pressure_contained")
    if rotation_input.days_in_domain >= MIN_ROTATION_TENURE_DAYS:
        reason_codes.append("domain_tenure_mature")
    else:
        reason_codes.append("domain_tenure_short")
    if rotation_input.domain_learning_score >= MIN_ROTATION_LEARNING_SCORE:
        reason_codes.append("domain_learning_sufficient")
    else:
        reason_codes.append("domain_learning_developing")
    return _normalize_reason_codes(tuple(reason_codes))


def _status_reason_code(rotation_status: str) -> str:
    if rotation_status == "rotate":
        return ROTATE_REASON_CODE
    if rotation_status == "watch":
        return WATCH_REASON_CODE
    if rotation_status == "hold":
        return HOLD_REASON_CODE
    raise ValueError("rotation_status must be a known value")


def _validate_result(result: StrategyTeamDomainRotationRecommendationV10Result) -> None:
    rotation_input = StrategyTeamDomainRotationRecommendationV10Input(
        team_id=result.team_id,
        current_domain=result.current_domain,
        recent_hit_rate=result.recent_hit_rate,
        calibration_error_bps=result.calibration_error_bps,
        source_gap_rate=result.source_gap_rate,
        queue_pressure_score=result.queue_pressure_score,
        days_in_domain=result.days_in_domain,
        domain_learning_score=result.domain_learning_score,
    )
    if result.hit_rate_pressure_score != _hit_rate_pressure_score(result.recent_hit_rate):
        raise ValueError("hit_rate_pressure_score must match inputs")
    if result.calibration_pressure_score != _calibration_pressure_score(
        result.calibration_error_bps,
    ):
        raise ValueError("calibration_pressure_score must match inputs")
    if result.domain_tenure_pressure_score != _domain_tenure_pressure_score(
        result.days_in_domain,
    ):
        raise ValueError("domain_tenure_pressure_score must match inputs")
    if result.domain_learning_gap_score != _domain_learning_gap_score(
        result.domain_learning_score,
    ):
        raise ValueError("domain_learning_gap_score must match inputs")
    expected_priority = _rotation_priority(
        recent_hit_rate=result.recent_hit_rate,
        hit_rate_pressure_score=result.hit_rate_pressure_score,
        calibration_pressure_score=result.calibration_pressure_score,
        source_gap_rate=result.source_gap_rate,
        queue_pressure_score=result.queue_pressure_score,
        domain_tenure_pressure_score=result.domain_tenure_pressure_score,
        domain_learning_gap_score=result.domain_learning_gap_score,
    )
    if result.rotation_priority != expected_priority:
        raise ValueError("rotation_priority must match inputs")
    expected_status = _rotation_status(rotation_input, result.rotation_priority)
    if result.rotation_status != expected_status:
        raise ValueError("rotation_status must match inputs")
    if result.recommended_domain_action != _recommended_domain_action(
        rotation_input,
        rotation_status=result.rotation_status,
    ):
        raise ValueError("recommended_domain_action must match inputs")
    if result.reason_codes != _reason_codes(rotation_input, result.rotation_status):
        raise ValueError("reason_codes must match inputs")


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload decimal", value), "f")


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_probability_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_member(field_name: str, value: Any, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be a known value")


def _require_public_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    _require_no_sensitive_public_text(field_name, value)


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_code must be a string")
        if not reason_code or reason_code.strip() != reason_code:
            raise ValueError("reason_code must be canonical")
        if not all(char.islower() or char.isdigit() or char == "_" for char in reason_code):
            raise ValueError("reason_code must be lowercase snake case")
        _require_no_sensitive_public_text("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=_reason_code_sort_key))


def _reason_code_sort_key(reason_code: str) -> tuple[int, str]:
    return (
        REASON_CODE_SORT_PRIORITY.get(reason_code, len(REASON_CODE_SORT_PRIORITY)),
        reason_code,
    )


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    reject_unsafe_surface_fields(label, payload)
    for value in _iter_string_values(payload):
        _require_no_sensitive_public_text("payload string value", value)


def _require_no_sensitive_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in SENSITIVE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain sensitive content")


def _iter_string_values(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _iter_string_values(json_ready_no_floats(value))
    if type(value) is str:
        return (value,)
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_iter_string_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_iter_string_values(item))
        return tuple(values)
    return ()


def _min_decimal(left: Decimal, right: Decimal) -> Decimal:
    if left <= right:
        return left
    return right


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return total


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left + right).quantize(QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(QUANTUM)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(QUANTUM)


def _ratio_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left / right).quantize(QUANTUM)
