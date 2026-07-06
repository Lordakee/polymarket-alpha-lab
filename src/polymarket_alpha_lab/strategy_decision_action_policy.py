"""Pure paper-only strategy decision action policy reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


__all__ = (
    "PaperStrategyDecisionActionPolicyDecision",
    "PaperStrategyDecisionCandidateState",
    "PaperStrategyDecisionCostState",
    "PaperStrategyDecisionInformationQualityState",
    "PaperStrategyDecisionLiquidityState",
    "PaperStrategyDecisionResolutionState",
    "PaperStrategyDecisionTeamMemoryState",
    "reduce_paper_strategy_decision_action_policy",
)


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
FINAL_ACTIONS = ("candidate", "research", "watch", "blocked")
SIGNAL_STATUSES = ("pass", "watch", "blocked")
FINAL_ACTION_REASON_PREFIX = "strategy_decision_action_"


@dataclass(frozen=True)
class PaperStrategyDecisionCandidateState:
    candidate_action: str
    priority: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_final_action("candidate_action", self.candidate_action)
        object.__setattr__(
            self,
            "priority",
            _quantize_priority("priority", self.priority),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("candidate_state", self)


@dataclass(frozen=True)
class PaperStrategyDecisionInformationQualityState:
    status: str
    priority_adjustment: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _normalize_signal_state("information_quality_state", self)


@dataclass(frozen=True)
class PaperStrategyDecisionCostState:
    status: str
    priority_adjustment: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _normalize_signal_state("cost_state", self)


@dataclass(frozen=True)
class PaperStrategyDecisionLiquidityState:
    status: str
    priority_adjustment: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _normalize_signal_state("liquidity_state", self)


@dataclass(frozen=True)
class PaperStrategyDecisionResolutionState:
    status: str
    priority_adjustment: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _normalize_signal_state("resolution_state", self)


@dataclass(frozen=True)
class PaperStrategyDecisionTeamMemoryState:
    status: str
    priority_adjustment: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _normalize_signal_state("team_memory_state", self)


@dataclass(frozen=True)
class PaperStrategyDecisionActionPolicyDecision:
    final_action: str
    priority: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_final_action("final_action", self.final_action)
        object.__setattr__(
            self,
            "priority",
            _quantize_priority("priority", self.priority),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_decision_consistency(self)
        _require_hard_flags("decision", self)


def reduce_paper_strategy_decision_action_policy(
    candidate_state: PaperStrategyDecisionCandidateState,
    information_quality_state: PaperStrategyDecisionInformationQualityState,
    cost_state: PaperStrategyDecisionCostState,
    liquidity_state: PaperStrategyDecisionLiquidityState,
    resolution_state: PaperStrategyDecisionResolutionState,
    team_memory_state: PaperStrategyDecisionTeamMemoryState,
) -> PaperStrategyDecisionActionPolicyDecision:
    """Reduce candidate and guardrail states into one paper-only final action."""

    _require_exact_type(
        "candidate_state",
        candidate_state,
        PaperStrategyDecisionCandidateState,
    )
    _require_exact_type(
        "information_quality_state",
        information_quality_state,
        PaperStrategyDecisionInformationQualityState,
    )
    _require_exact_type("cost_state", cost_state, PaperStrategyDecisionCostState)
    _require_exact_type(
        "liquidity_state",
        liquidity_state,
        PaperStrategyDecisionLiquidityState,
    )
    _require_exact_type(
        "resolution_state",
        resolution_state,
        PaperStrategyDecisionResolutionState,
    )
    _require_exact_type(
        "team_memory_state",
        team_memory_state,
        PaperStrategyDecisionTeamMemoryState,
    )

    signal_states = (
        information_quality_state,
        cost_state,
        liquidity_state,
        resolution_state,
        team_memory_state,
    )
    final_action = _final_action(candidate_state, signal_states)
    priority = (
        ZERO
        if final_action == "blocked"
        else _clamp_priority(
            candidate_state.priority
            + sum(
                (signal_state.priority_adjustment for signal_state in signal_states),
                ZERO,
            ),
        )
    )
    return PaperStrategyDecisionActionPolicyDecision(
        final_action=final_action,
        priority=priority,
        reason_codes=_decision_reason_codes(
            final_action,
            candidate_state,
            signal_states,
        ),
    )


def _normalize_signal_state(field_name: str, state: object) -> None:
    _require_signal_status("status", getattr(state, "status", None))
    object.__setattr__(
        state,
        "priority_adjustment",
        _quantize_decimal("priority_adjustment", getattr(state, "priority_adjustment", None)),
    )
    object.__setattr__(
        state,
        "reason_codes",
        _normalize_reason_codes("reason_codes", getattr(state, "reason_codes", None)),
    )
    _require_hard_flags(field_name, state)


def _final_action(
    candidate_state: PaperStrategyDecisionCandidateState,
    signal_states: tuple[
        PaperStrategyDecisionInformationQualityState
        | PaperStrategyDecisionCostState
        | PaperStrategyDecisionLiquidityState
        | PaperStrategyDecisionResolutionState
        | PaperStrategyDecisionTeamMemoryState,
        ...,
    ],
) -> str:
    if candidate_state.candidate_action == "blocked" or any(
        signal_state.status == "blocked" for signal_state in signal_states
    ):
        return "blocked"
    if candidate_state.candidate_action == "watch" or any(
        signal_state.status == "watch" for signal_state in signal_states
    ):
        return "watch"
    return candidate_state.candidate_action


def _decision_reason_codes(
    final_action: str,
    candidate_state: PaperStrategyDecisionCandidateState,
    signal_states: tuple[
        PaperStrategyDecisionInformationQualityState
        | PaperStrategyDecisionCostState
        | PaperStrategyDecisionLiquidityState
        | PaperStrategyDecisionResolutionState
        | PaperStrategyDecisionTeamMemoryState,
        ...,
    ],
) -> tuple[str, ...]:
    reason_codes = [f"{FINAL_ACTION_REASON_PREFIX}{final_action}"]
    for reason_code in candidate_state.reason_codes:
        reason_codes.append(reason_code)
    for signal_state in signal_states:
        for reason_code in signal_state.reason_codes:
            reason_codes.append(reason_code)
    return tuple(dict.fromkeys(reason_codes))


def _validate_decision_consistency(
    decision: PaperStrategyDecisionActionPolicyDecision,
) -> None:
    if decision.final_action == "blocked" and decision.priority != ZERO:
        raise ValueError("blocked decisions must use zero priority")
    expected_reason_code = f"{FINAL_ACTION_REASON_PREFIX}{decision.final_action}"
    if decision.reason_codes[0] != expected_reason_code:
        raise ValueError("reason_codes must start with final_action reason code")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_hard_flags(field_name, value)


def _require_final_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FINAL_ACTIONS:
        raise ValueError(f"{field_name} must be candidate, research, watch, or blocked")


def _require_signal_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIGNAL_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return value


def _quantize_priority(field_name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")
    return normalized


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _clamp_priority(value: Decimal) -> Decimal:
    quantized = value.quantize(QUANTUM)
    if quantized < ZERO:
        return ZERO
    if quantized > ONE:
        return ONE
    return quantized


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")
