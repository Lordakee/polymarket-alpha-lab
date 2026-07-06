"""Pure read-only market research budget guard for strategy candidates."""

from __future__ import annotations

from dataclasses import dataclass, is_dataclass
from decimal import Decimal
from typing import Any


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
LIMITED_MINUTES_CAP = Decimal("30.000000")

UNSAFE_SURFACE_FRAGMENTS = (
    "account",
    "auth",
    "broker",
    "cancel",
    "client",
    "connect",
    "database",
    "execute",
    "fetch",
    "key",
    "network",
    "order",
    "persist",
    "private",
    "secret",
    "sign",
    "submit",
    "token",
    "trade",
    "wallet",
)


@dataclass(frozen=True)
class StrategyMarketResearchBudgetGuardV10Input:
    market_id: str
    priority_score: Decimal
    estimated_research_minutes: Decimal
    team_capacity_score: Decimal
    time_to_resolution_minutes: Decimal
    expected_value_bps: Decimal
    source_gap_count: Decimal
    human_review_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "priority_score",
            _normalize_probability("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "estimated_research_minutes",
            _normalize_nonnegative_decimal(
                "estimated_research_minutes",
                self.estimated_research_minutes,
            ),
        )
        object.__setattr__(
            self,
            "team_capacity_score",
            _normalize_probability("team_capacity_score", self.team_capacity_score),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "expected_value_bps",
            _normalize_nonnegative_decimal("expected_value_bps", self.expected_value_bps),
        )
        object.__setattr__(
            self,
            "source_gap_count",
            _normalize_nonnegative_count("source_gap_count", self.source_gap_count),
        )
        _require_bool("human_review_required", self.human_review_required)
        _require_hard_flags("input", self)
        _reject_unsafe_payload("input", self)


@dataclass(frozen=True)
class StrategyMarketResearchBudgetGuardV10Decision:
    market_id: str
    priority_score: Decimal
    estimated_research_minutes: Decimal
    team_capacity_score: Decimal
    time_to_resolution_minutes: Decimal
    expected_value_bps: Decimal
    source_gap_count: Decimal
    human_review_required: bool
    budget_status: str
    approved_minutes: Decimal
    budget_warning_level: str
    reason_codes: tuple[str, ...]
    payload: dict[str, Any] | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "priority_score",
            _normalize_probability("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "estimated_research_minutes",
            _normalize_nonnegative_decimal(
                "estimated_research_minutes",
                self.estimated_research_minutes,
            ),
        )
        object.__setattr__(
            self,
            "team_capacity_score",
            _normalize_probability("team_capacity_score", self.team_capacity_score),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "expected_value_bps",
            _normalize_nonnegative_decimal("expected_value_bps", self.expected_value_bps),
        )
        object.__setattr__(
            self,
            "source_gap_count",
            _normalize_nonnegative_count("source_gap_count", self.source_gap_count),
        )
        _require_bool("human_review_required", self.human_review_required)
        _require_member("budget_status", self.budget_status, ("approved", "limited", "blocked"))
        object.__setattr__(
            self,
            "approved_minutes",
            _normalize_nonnegative_decimal("approved_minutes", self.approved_minutes),
        )
        _require_member(
            "budget_warning_level",
            self.budget_warning_level,
            ("none", "medium", "high"),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("decision", self)
        _validate_decision_derived_fields(self)
        _reject_unsafe_payload("decision", self)
        expected_payload = _decision_payload(self)
        if self.payload is None:
            object.__setattr__(self, "payload", expected_payload)
            return
        payload = _json_ready(self.payload)
        if payload != expected_payload:
            raise ValueError("payload must match decision fields")
        object.__setattr__(self, "payload", payload)


def evaluate_strategy_market_research_budget_guard_v10(
    inputs: StrategyMarketResearchBudgetGuardV10Input,
) -> StrategyMarketResearchBudgetGuardV10Decision:
    if type(inputs) is not StrategyMarketResearchBudgetGuardV10Input:
        raise ValueError("inputs must be a StrategyMarketResearchBudgetGuardV10Input")
    _require_hard_flags("input", inputs)
    _reject_unsafe_payload("input", inputs)

    budget_status = _budget_status(inputs)
    return StrategyMarketResearchBudgetGuardV10Decision(
        market_id=inputs.market_id,
        priority_score=inputs.priority_score,
        estimated_research_minutes=inputs.estimated_research_minutes,
        team_capacity_score=inputs.team_capacity_score,
        time_to_resolution_minutes=inputs.time_to_resolution_minutes,
        expected_value_bps=inputs.expected_value_bps,
        source_gap_count=inputs.source_gap_count,
        human_review_required=inputs.human_review_required,
        budget_status=budget_status,
        approved_minutes=_approved_minutes(inputs, budget_status),
        budget_warning_level=_budget_warning_level(budget_status),
        reason_codes=_reason_codes(inputs, budget_status),
    )


def strategy_market_research_budget_guard_v10_payload(
    decision: StrategyMarketResearchBudgetGuardV10Decision | dict[str, Any],
) -> dict[str, Any]:
    if type(decision) is StrategyMarketResearchBudgetGuardV10Decision:
        _require_hard_flags("decision", decision)
        _validate_decision_derived_fields(decision)
        _reject_unsafe_payload("decision", decision)
        payload = _decision_payload(decision)
        if decision.payload != payload:
            raise ValueError("payload must match decision fields")
        return payload
    if type(decision) is dict:
        _reject_unsafe_payload("payload", decision)
        payload = _json_ready(decision)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _reject_unsafe_payload("payload", payload)
        return payload
    raise ValueError("decision must be a StrategyMarketResearchBudgetGuardV10Decision")


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


def _budget_status(inputs: StrategyMarketResearchBudgetGuardV10Input) -> str:
    if _has_hard_blocker(inputs):
        return "blocked"
    if (
        inputs.priority_score >= Decimal("0.800000")
        and inputs.team_capacity_score >= Decimal("0.700000")
        and inputs.time_to_resolution_minutes >= Decimal("360.000000")
        and inputs.expected_value_bps >= Decimal("50.000000")
        and inputs.source_gap_count <= Decimal("1")
        and inputs.estimated_research_minutes <= Decimal("60.000000")
    ):
        return "approved"
    return "limited"


def _has_hard_blocker(inputs: StrategyMarketResearchBudgetGuardV10Input) -> bool:
    return (
        inputs.human_review_required
        or inputs.priority_score < Decimal("0.250000")
        or inputs.team_capacity_score < Decimal("0.250000")
        or inputs.time_to_resolution_minutes < Decimal("60.000000")
        or inputs.expected_value_bps <= ZERO
        or inputs.source_gap_count >= Decimal("5")
    )


def _approved_minutes(
    inputs: StrategyMarketResearchBudgetGuardV10Input,
    budget_status: str,
) -> Decimal:
    if budget_status == "blocked":
        return ZERO
    if budget_status == "limited":
        return min(inputs.estimated_research_minutes, LIMITED_MINUTES_CAP)
    return inputs.estimated_research_minutes


def _budget_warning_level(budget_status: str) -> str:
    if budget_status == "blocked":
        return "high"
    if budget_status == "limited":
        return "medium"
    return "none"


def _reason_codes(
    inputs: StrategyMarketResearchBudgetGuardV10Input,
    budget_status: str,
) -> tuple[str, ...]:
    codes = [f"market_research_budget_{budget_status}"]
    codes.append(_priority_reason_code(inputs.priority_score))
    codes.append(_team_capacity_reason_code(inputs.team_capacity_score))
    codes.append(_resolution_window_reason_code(inputs.time_to_resolution_minutes))
    codes.append(_expected_value_reason_code(inputs.expected_value_bps))
    codes.append(_source_gap_reason_code(inputs.source_gap_count))
    if inputs.human_review_required:
        codes.append("human_review_required")
    return tuple(codes)


def _priority_reason_code(value: Decimal) -> str:
    if value < Decimal("0.250000"):
        return "priority_score_below_floor"
    if value >= Decimal("0.800000"):
        return "priority_score_high"
    return "priority_score_standard"


def _team_capacity_reason_code(value: Decimal) -> str:
    if value < Decimal("0.250000"):
        return "team_capacity_below_floor"
    if value >= Decimal("0.700000"):
        return "team_capacity_available"
    return "team_capacity_constrained"


def _resolution_window_reason_code(value: Decimal) -> str:
    if value < Decimal("60.000000"):
        return "resolution_window_too_short"
    if value < Decimal("360.000000"):
        return "resolution_window_tight"
    return "resolution_window_sufficient"


def _expected_value_reason_code(value: Decimal) -> str:
    if value <= ZERO:
        return "expected_value_below_floor"
    if value >= Decimal("50.000000"):
        return "expected_value_supports_budget"
    return "expected_value_watch"


def _source_gap_reason_code(value: Decimal) -> str:
    if value >= Decimal("5"):
        return "source_gap_count_high"
    if value <= Decimal("1"):
        return "source_gap_count_low"
    return "source_gap_count_moderate"


def _validate_decision_derived_fields(
    decision: StrategyMarketResearchBudgetGuardV10Decision,
) -> None:
    inputs = StrategyMarketResearchBudgetGuardV10Input(
        market_id=decision.market_id,
        priority_score=decision.priority_score,
        estimated_research_minutes=decision.estimated_research_minutes,
        team_capacity_score=decision.team_capacity_score,
        time_to_resolution_minutes=decision.time_to_resolution_minutes,
        expected_value_bps=decision.expected_value_bps,
        source_gap_count=decision.source_gap_count,
        human_review_required=decision.human_review_required,
        paper_only=decision.paper_only,
        report_only=decision.report_only,
        readonly=decision.readonly,
    )
    expected_status = _budget_status(inputs)
    if decision.budget_status != expected_status:
        raise ValueError("budget_status must match budget inputs")
    if decision.approved_minutes != _approved_minutes(inputs, expected_status):
        raise ValueError("approved_minutes must match budget inputs")
    if decision.budget_warning_level != _budget_warning_level(expected_status):
        raise ValueError("budget_warning_level must match budget inputs")
    if decision.reason_codes != _reason_codes(inputs, expected_status):
        raise ValueError("reason_codes must match budget inputs")


def _decision_payload(
    decision: StrategyMarketResearchBudgetGuardV10Decision,
) -> dict[str, Any]:
    return {
        "market_id": decision.market_id,
        "priority_score": _decimal_payload(decision.priority_score),
        "estimated_research_minutes": _decimal_payload(
            decision.estimated_research_minutes,
        ),
        "team_capacity_score": _decimal_payload(decision.team_capacity_score),
        "time_to_resolution_minutes": _decimal_payload(
            decision.time_to_resolution_minutes,
        ),
        "expected_value_bps": _decimal_payload(decision.expected_value_bps),
        "source_gap_count": _decimal_payload(decision.source_gap_count),
        "human_review_required": decision.human_review_required,
        "budget_status": decision.budget_status,
        "approved_minutes": _decimal_payload(decision.approved_minutes),
        "budget_warning_level": decision.budget_warning_level,
        "reason_codes": list(decision.reason_codes),
        "paper_only": decision.paper_only,
        "report_only": decision.report_only,
        "readonly": decision.readonly,
    }


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    for reason_code in value:
        _require_canonical_string("reason_codes", reason_code)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    return value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(COUNT_QUANTUM)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized.quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _require_decimal(field_name, value).quantize(QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        raise ValueError("public payloads must be dictionaries")
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return _decimal_payload(value.quantize(QUANTUM))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived string values")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(label: str, value: object) -> None:
    _reject_unsafe_payload_keys(label, value)
    _reject_unsafe_payload_values(label, value)


def _reject_unsafe_payload_keys(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for key, item in value.__dict__.items():
            if key == "payload":
                continue
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_payload_keys(label, item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_payload_keys(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_payload_keys(label, item)


def _reject_unsafe_payload_values(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for key, item in value.__dict__.items():
            if key == "payload":
                continue
            _reject_unsafe_payload_values(label, item)
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"unsafe live surface value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_payload_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_payload_values(label, item)


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_SURFACE_FRAGMENTS)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


__all__ = (
    "StrategyMarketResearchBudgetGuardV10Decision",
    "StrategyMarketResearchBudgetGuardV10Input",
    "evaluate_strategy_market_research_budget_guard_v10",
    "strategy_market_research_budget_guard_v10_payload",
)
