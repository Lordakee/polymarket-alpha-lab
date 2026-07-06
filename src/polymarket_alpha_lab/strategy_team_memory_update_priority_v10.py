"""Pure read-only team memory update priority v10."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


STRATEGY_TEAM_MEMORY_UPDATE_PRIORITY_V10_CONFIG_VERSION = (
    "strategy-team-memory-update-priority-v10"
)

FEEDBACK_ROUTE_STATUSES = ("logged", "queued", "review_required", "blocked")
POSTMORTEM_STATUSES = ("complete", "pending", "missing", "blocked")
UPDATE_PRIORITY_STATUSES = (
    "monitor",
    "queue_update",
    "prioritize_update",
    "urgent_update",
    "blocked",
)
MEMORY_UPDATE_ACTIONS = (
    "continue_monitoring",
    "apply_forecast_calibration_update",
    "refresh_source_gap_playbook",
    "complete_postmortem_memory_update",
    "refresh_stale_team_memory",
    "escalate_memory_update_review",
    "escalate_blocked_memory_update",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
MAX_PRIORITY_SCORE = Decimal("100.000000")
MODERATE_FORECAST_ERROR_BPS = Decimal("250.000000")
HIGH_FORECAST_ERROR_BPS = Decimal("600.000000")
HIGH_SOURCE_GAP_COUNT = Decimal("3.000000")
STALE_UPDATE_DAYS = Decimal("14.000000")
SUFFICIENT_SAMPLE_SIZE = Decimal("10.000000")
QUEUE_PRIORITY_SCORE = Decimal("25.000000")
PRIORITIZE_PRIORITY_SCORE = Decimal("70.000000")
URGENT_PRIORITY_SCORE = Decimal("90.000000")

SENSITIVE_MARKERS = (
    "api_key",
    "secret",
    "password",
    "private_key",
    "bearer ",
)


@dataclass(frozen=True)
class StrategyTeamMemoryUpdatePriorityV10Input:
    team_id: str
    category: str
    feedback_route_status: str
    forecast_error_bps: Decimal
    source_gap_count: Decimal
    postmortem_status: str
    days_since_last_update: Decimal
    sample_size: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category", self.category)
        _require_member(
            "feedback_route_status",
            self.feedback_route_status,
            FEEDBACK_ROUTE_STATUSES,
        )
        object.__setattr__(
            self,
            "forecast_error_bps",
            _normalize_nonnegative_decimal("forecast_error_bps", self.forecast_error_bps),
        )
        object.__setattr__(
            self,
            "source_gap_count",
            _normalize_nonnegative_whole_decimal("source_gap_count", self.source_gap_count),
        )
        _require_member("postmortem_status", self.postmortem_status, POSTMORTEM_STATUSES)
        object.__setattr__(
            self,
            "days_since_last_update",
            _normalize_nonnegative_decimal(
                "days_since_last_update",
                self.days_since_last_update,
            ),
        )
        object.__setattr__(
            self,
            "sample_size",
            _normalize_positive_whole_decimal("sample_size", self.sample_size),
        )
        require_paper_only_flags(
            "strategy team memory update priority v10 input",
            self,
        )


@dataclass(frozen=True)
class StrategyTeamMemoryUpdatePriorityV10Result:
    team_id: str
    category: str
    feedback_route_status: str
    forecast_error_bps: Decimal
    source_gap_count: Decimal
    postmortem_status: str
    days_since_last_update: Decimal
    sample_size: Decimal
    update_priority_status: str
    priority_score: Decimal
    memory_update_actions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    payload: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category", self.category)
        _require_member(
            "feedback_route_status",
            self.feedback_route_status,
            FEEDBACK_ROUTE_STATUSES,
        )
        object.__setattr__(
            self,
            "forecast_error_bps",
            _normalize_nonnegative_decimal("forecast_error_bps", self.forecast_error_bps),
        )
        object.__setattr__(
            self,
            "source_gap_count",
            _normalize_nonnegative_whole_decimal("source_gap_count", self.source_gap_count),
        )
        _require_member("postmortem_status", self.postmortem_status, POSTMORTEM_STATUSES)
        object.__setattr__(
            self,
            "days_since_last_update",
            _normalize_nonnegative_decimal(
                "days_since_last_update",
                self.days_since_last_update,
            ),
        )
        object.__setattr__(
            self,
            "sample_size",
            _normalize_positive_whole_decimal("sample_size", self.sample_size),
        )
        _require_member(
            "update_priority_status",
            self.update_priority_status,
            UPDATE_PRIORITY_STATUSES,
        )
        object.__setattr__(
            self,
            "priority_score",
            _normalize_priority_score("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "memory_update_actions",
            _normalize_memory_update_actions(self.memory_update_actions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "payload", _normalize_payload("payload", self.payload))
        _validate_result(self)
        require_paper_only_flags(
            "strategy team memory update priority v10 result",
            self,
        )


def evaluate_strategy_team_memory_update_priority_v10(
    memory_signal: StrategyTeamMemoryUpdatePriorityV10Input,
) -> StrategyTeamMemoryUpdatePriorityV10Result:
    if type(memory_signal) is not StrategyTeamMemoryUpdatePriorityV10Input:
        raise ValueError(
            "memory_signal must be a StrategyTeamMemoryUpdatePriorityV10Input",
        )
    require_paper_only_flags(
        "strategy team memory update priority v10 input",
        memory_signal,
    )

    priority_score, priority_was_clamped = _priority_score(memory_signal)
    update_priority_status = _update_priority_status(
        memory_signal,
        priority_score=priority_score,
    )
    memory_update_actions = _memory_update_actions(
        memory_signal,
        update_priority_status=update_priority_status,
    )
    reason_codes = _reason_codes(
        memory_signal,
        update_priority_status=update_priority_status,
        priority_was_clamped=priority_was_clamped,
    )
    payload = _payload(
        memory_signal,
        update_priority_status=update_priority_status,
        priority_score=priority_score,
        memory_update_actions=memory_update_actions,
        reason_codes=reason_codes,
    )

    return StrategyTeamMemoryUpdatePriorityV10Result(
        team_id=memory_signal.team_id,
        category=memory_signal.category,
        feedback_route_status=memory_signal.feedback_route_status,
        forecast_error_bps=memory_signal.forecast_error_bps,
        source_gap_count=memory_signal.source_gap_count,
        postmortem_status=memory_signal.postmortem_status,
        days_since_last_update=memory_signal.days_since_last_update,
        sample_size=memory_signal.sample_size,
        update_priority_status=update_priority_status,
        priority_score=priority_score,
        memory_update_actions=memory_update_actions,
        reason_codes=reason_codes,
        payload=payload,
    )


def strategy_team_memory_update_priority_v10_payload(
    decision: StrategyTeamMemoryUpdatePriorityV10Result,
) -> dict[str, Any]:
    if type(decision) is not StrategyTeamMemoryUpdatePriorityV10Result:
        raise ValueError("decision must be a StrategyTeamMemoryUpdatePriorityV10Result")
    require_paper_only_flags(
        "strategy team memory update priority v10 result",
        decision,
    )
    payload = json_ready_no_floats(decision.payload)
    if type(payload) is not dict:
        raise ValueError("decision payload must be a JSON object")
    require_paper_only_flags(
        "strategy team memory update priority v10 payload",
        _PayloadFlags(payload),
    )
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


def _priority_score(
    value: StrategyTeamMemoryUpdatePriorityV10Input | StrategyTeamMemoryUpdatePriorityV10Result,
) -> tuple[Decimal, bool]:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = value.forecast_error_bps / Decimal("20.000000")
        raw_score += value.source_gap_count * Decimal("8.000000")
        raw_score += value.days_since_last_update / Decimal("2.000000")
        raw_score += _feedback_route_weight(value.feedback_route_status)
        raw_score += _postmortem_weight(value.postmortem_status)
    priority_score = _quantize(raw_score)
    if priority_score > MAX_PRIORITY_SCORE:
        return MAX_PRIORITY_SCORE, True
    if priority_score < ZERO:
        return ZERO, True
    return priority_score, False


def _feedback_route_weight(feedback_route_status: str) -> Decimal:
    if feedback_route_status == "blocked":
        return Decimal("25.000000")
    if feedback_route_status == "review_required":
        return Decimal("11.000000")
    if feedback_route_status == "queued":
        return Decimal("8.000000")
    return ZERO


def _postmortem_weight(postmortem_status: str) -> Decimal:
    if postmortem_status == "blocked":
        return Decimal("30.000000")
    if postmortem_status == "missing":
        return Decimal("18.000000")
    if postmortem_status == "pending":
        return Decimal("10.000000")
    return ZERO


def _update_priority_status(
    value: StrategyTeamMemoryUpdatePriorityV10Input | StrategyTeamMemoryUpdatePriorityV10Result,
    *,
    priority_score: Decimal,
) -> str:
    if value.feedback_route_status == "blocked" or value.postmortem_status == "blocked":
        return "blocked"
    if priority_score >= URGENT_PRIORITY_SCORE:
        return "urgent_update"
    if priority_score >= PRIORITIZE_PRIORITY_SCORE:
        return "prioritize_update"
    if (
        priority_score >= QUEUE_PRIORITY_SCORE
        or value.feedback_route_status == "queued"
        or value.postmortem_status != "complete"
        or value.source_gap_count > ZERO
        or value.days_since_last_update >= STALE_UPDATE_DAYS
    ):
        return "queue_update"
    return "monitor"


def _memory_update_actions(
    value: StrategyTeamMemoryUpdatePriorityV10Input | StrategyTeamMemoryUpdatePriorityV10Result,
    *,
    update_priority_status: str,
) -> tuple[str, ...]:
    actions: list[str] = []
    if update_priority_status == "blocked":
        actions.append("escalate_blocked_memory_update")
    if value.forecast_error_bps >= MODERATE_FORECAST_ERROR_BPS:
        actions.append("apply_forecast_calibration_update")
    if value.source_gap_count > ZERO:
        actions.append("refresh_source_gap_playbook")
    if value.postmortem_status != "complete":
        actions.append("complete_postmortem_memory_update")
    if value.days_since_last_update >= STALE_UPDATE_DAYS:
        actions.append("refresh_stale_team_memory")
    if update_priority_status in ("prioritize_update", "urgent_update"):
        actions.append("escalate_memory_update_review")
    if not actions:
        actions.append("continue_monitoring")
    return _normalize_memory_update_actions(tuple(actions))


def _reason_codes(
    value: StrategyTeamMemoryUpdatePriorityV10Input | StrategyTeamMemoryUpdatePriorityV10Result,
    *,
    update_priority_status: str,
    priority_was_clamped: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"feedback_route_status_{value.feedback_route_status}"]
    if value.forecast_error_bps >= HIGH_FORECAST_ERROR_BPS:
        reason_codes.append("forecast_error_high")
    elif value.forecast_error_bps >= MODERATE_FORECAST_ERROR_BPS:
        reason_codes.append("forecast_error_moderate")
    else:
        reason_codes.append("forecast_error_low")

    if value.source_gap_count >= HIGH_SOURCE_GAP_COUNT:
        reason_codes.append("source_gap_count_high")
    elif value.source_gap_count > ZERO:
        reason_codes.append("source_gap_present")
    else:
        reason_codes.append("source_gap_absent")

    reason_codes.append(f"postmortem_{value.postmortem_status}")
    if value.days_since_last_update >= STALE_UPDATE_DAYS:
        reason_codes.append("memory_update_stale")
    else:
        reason_codes.append("memory_recent")
    if value.sample_size >= SUFFICIENT_SAMPLE_SIZE:
        reason_codes.append("sample_size_sufficient")
    else:
        reason_codes.append("sample_size_limited")
    if priority_was_clamped:
        reason_codes.append("priority_score_clamped")
    reason_codes.append(f"update_priority_status_{update_priority_status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _payload(
    value: StrategyTeamMemoryUpdatePriorityV10Input | StrategyTeamMemoryUpdatePriorityV10Result,
    *,
    update_priority_status: str,
    priority_score: Decimal,
    memory_update_actions: tuple[str, ...],
    reason_codes: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "config_version": STRATEGY_TEAM_MEMORY_UPDATE_PRIORITY_V10_CONFIG_VERSION,
        "team_id": value.team_id,
        "category": value.category,
        "feedback_route_status": value.feedback_route_status,
        "forecast_error_bps": _decimal_payload(value.forecast_error_bps),
        "source_gap_count": _decimal_payload(value.source_gap_count),
        "postmortem_status": value.postmortem_status,
        "days_since_last_update": _decimal_payload(value.days_since_last_update),
        "sample_size": _decimal_payload(value.sample_size),
        "update_priority_status": update_priority_status,
        "priority_score": _decimal_payload(priority_score),
        "memory_update_actions": list(memory_update_actions),
        "reason_codes": list(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_result(decision: StrategyTeamMemoryUpdatePriorityV10Result) -> None:
    expected_priority_score, priority_was_clamped = _priority_score(decision)
    if decision.priority_score != expected_priority_score:
        raise ValueError("priority_score must match memory update inputs")
    expected_status = _update_priority_status(
        decision,
        priority_score=expected_priority_score,
    )
    if decision.update_priority_status != expected_status:
        raise ValueError("update_priority_status must match memory update inputs")
    expected_actions = _memory_update_actions(
        decision,
        update_priority_status=expected_status,
    )
    if decision.memory_update_actions != expected_actions:
        raise ValueError("memory_update_actions must match memory update inputs")
    expected_reasons = _reason_codes(
        decision,
        update_priority_status=expected_status,
        priority_was_clamped=priority_was_clamped,
    )
    if decision.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match memory update inputs")
    expected_payload = _payload(
        decision,
        update_priority_status=expected_status,
        priority_score=expected_priority_score,
        memory_update_actions=expected_actions,
        reason_codes=expected_reasons,
    )
    if decision.payload != expected_payload:
        raise ValueError("payload must match memory update inputs")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return decimal_value


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a positive whole Decimal")
    return decimal_value


def _normalize_priority_score(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > MAX_PRIORITY_SCORE:
        raise ValueError(f"{field_name} must be between 0 and 100")
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


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM)


def _normalize_memory_update_actions(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("memory_update_actions must be a tuple")
    if not value:
        raise ValueError("memory_update_actions must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for action in value:
        _require_member("memory_update_actions", action, MEMORY_UPDATE_ACTIONS)
        if action in seen:
            raise ValueError("memory_update_actions must be unique")
        seen.add(action)
        normalized.append(action)
    return tuple(normalized)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
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


def _normalize_payload(field_name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    normalized = json_ready_no_floats(value)
    if type(normalized) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


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
    _reject_sensitive_text(value)


def _reject_sensitive_text(value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError("must not contain sensitive material")


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    return format(value, "f")
