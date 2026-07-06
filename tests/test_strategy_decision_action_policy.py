from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest

from polymarket_alpha_lab import strategy_decision_action_policy as policy_module
from polymarket_alpha_lab.strategy_decision_action_policy import (
    PaperStrategyDecisionActionPolicyDecision,
    PaperStrategyDecisionCandidateState,
    PaperStrategyDecisionCostState,
    PaperStrategyDecisionInformationQualityState,
    PaperStrategyDecisionLiquidityState,
    PaperStrategyDecisionResolutionState,
    PaperStrategyDecisionTeamMemoryState,
    reduce_paper_strategy_decision_action_policy,
)


ZERO = Decimal("0.000000")


class CandidateStateSubclass(PaperStrategyDecisionCandidateState):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _candidate(
    *,
    candidate_action: str = "candidate",
    priority: Decimal = Decimal("0.800000"),
    reason_codes: tuple[str, ...] = ("candidate_ranked",),
) -> PaperStrategyDecisionCandidateState:
    return PaperStrategyDecisionCandidateState(
        candidate_action=candidate_action,
        priority=priority,
        reason_codes=reason_codes,
    )


def _information_quality(
    *,
    status: str = "pass",
    priority_adjustment: Decimal = Decimal("0.050000"),
    reason_codes: tuple[str, ...] = ("information_quality_fresh",),
) -> PaperStrategyDecisionInformationQualityState:
    return PaperStrategyDecisionInformationQualityState(
        status=status,
        priority_adjustment=priority_adjustment,
        reason_codes=reason_codes,
    )


def _cost(
    *,
    status: str = "pass",
    priority_adjustment: Decimal = Decimal("-0.020000"),
    reason_codes: tuple[str, ...] = ("cost_inside_budget",),
) -> PaperStrategyDecisionCostState:
    return PaperStrategyDecisionCostState(
        status=status,
        priority_adjustment=priority_adjustment,
        reason_codes=reason_codes,
    )


def _liquidity(
    *,
    status: str = "pass",
    priority_adjustment: Decimal = Decimal("0.000000"),
    reason_codes: tuple[str, ...] = ("liquidity_depth_ready",),
) -> PaperStrategyDecisionLiquidityState:
    return PaperStrategyDecisionLiquidityState(
        status=status,
        priority_adjustment=priority_adjustment,
        reason_codes=reason_codes,
    )


def _resolution(
    *,
    status: str = "pass",
    priority_adjustment: Decimal = Decimal("-0.010000"),
    reason_codes: tuple[str, ...] = ("resolution_rules_clear",),
) -> PaperStrategyDecisionResolutionState:
    return PaperStrategyDecisionResolutionState(
        status=status,
        priority_adjustment=priority_adjustment,
        reason_codes=reason_codes,
    )


def _team_memory(
    *,
    status: str = "pass",
    priority_adjustment: Decimal = Decimal("0.020000"),
    reason_codes: tuple[str, ...] = ("team_memory_clean",),
) -> PaperStrategyDecisionTeamMemoryState:
    return PaperStrategyDecisionTeamMemoryState(
        status=status,
        priority_adjustment=priority_adjustment,
        reason_codes=reason_codes,
    )


def _reduce(
    candidate_state: PaperStrategyDecisionCandidateState | object | None = None,
    information_quality_state: (
        PaperStrategyDecisionInformationQualityState | object | None
    ) = None,
    cost_state: PaperStrategyDecisionCostState | object | None = None,
    liquidity_state: PaperStrategyDecisionLiquidityState | object | None = None,
    resolution_state: PaperStrategyDecisionResolutionState | object | None = None,
    team_memory_state: PaperStrategyDecisionTeamMemoryState | object | None = None,
) -> PaperStrategyDecisionActionPolicyDecision:
    return reduce_paper_strategy_decision_action_policy(
        candidate_state or _candidate(),
        information_quality_state or _information_quality(),
        cost_state or _cost(),
        liquidity_state or _liquidity(),
        resolution_state or _resolution(),
        team_memory_state or _team_memory(),
    )


def test_pass_states_promote_candidate_action_with_decimal_priority_and_reasons():
    decision = _reduce(_candidate(priority=d("0.850000")))

    assert isinstance(decision, PaperStrategyDecisionActionPolicyDecision)
    assert decision.final_action == "candidate"
    assert decision.priority == d("0.890000")
    assert type(decision.priority) is Decimal
    assert decision.reason_codes == (
        "strategy_decision_action_candidate",
        "candidate_ranked",
        "information_quality_fresh",
        "cost_inside_budget",
        "liquidity_depth_ready",
        "resolution_rules_clear",
        "team_memory_clean",
    )
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True


def test_blocked_precedence_over_watch_and_research_zeroes_priority():
    decision = _reduce(
        _candidate(
            candidate_action="research",
            priority=d("0.950000"),
            reason_codes=("candidate_needs_research",),
        ),
        _information_quality(
            status="watch",
            priority_adjustment=d("-0.100000"),
            reason_codes=("information_quality_stale",),
        ),
        _cost(
            status="blocked",
            priority_adjustment=d("-0.500000"),
            reason_codes=("cost_above_budget",),
        ),
        _liquidity(reason_codes=("liquidity_depth_ready",)),
        _resolution(
            status="watch",
            priority_adjustment=d("-0.050000"),
            reason_codes=("resolution_timeline_uncertain",),
        ),
        _team_memory(
            status="blocked",
            priority_adjustment=d("-0.250000"),
            reason_codes=("team_memory_recent_loss_pattern",),
        ),
    )

    assert decision.final_action == "blocked"
    assert decision.priority == ZERO
    assert decision.reason_codes == (
        "strategy_decision_action_blocked",
        "candidate_needs_research",
        "information_quality_stale",
        "cost_above_budget",
        "liquidity_depth_ready",
        "resolution_timeline_uncertain",
        "team_memory_recent_loss_pattern",
    )


def test_watch_precedence_over_research_when_no_states_are_blocked():
    decision = _reduce(
        _candidate(
            candidate_action="research",
            priority=d("0.700000"),
            reason_codes=("candidate_needs_research",),
        ),
        liquidity_state=_liquidity(
            status="watch",
            priority_adjustment=d("-0.200000"),
            reason_codes=("liquidity_depth_thin",),
        ),
    )

    assert decision.final_action == "watch"
    assert decision.priority == d("0.540000")
    assert decision.reason_codes == (
        "strategy_decision_action_watch",
        "candidate_needs_research",
        "information_quality_fresh",
        "cost_inside_budget",
        "liquidity_depth_thin",
        "resolution_rules_clear",
        "team_memory_clean",
    )


def test_research_action_survives_when_all_states_pass():
    decision = _reduce(
        _candidate(
            candidate_action="research",
            priority=d("0.3333333"),
            reason_codes=("candidate_needs_research",),
        ),
    )

    assert decision.final_action == "research"
    assert decision.priority == d("0.373333")
    assert decision.reason_codes[0] == "strategy_decision_action_research"


def test_dataclasses_are_frozen_tuple_only_and_decimal_only():
    candidate = _candidate()
    decision = _reduce(candidate)

    with pytest.raises(FrozenInstanceError):
        decision.priority = d("0.100000")
    with pytest.raises(FrozenInstanceError):
        candidate.candidate_action = "watch"
    with pytest.raises(ValueError, match="priority must be a Decimal"):
        replace(candidate, priority=1)
    with pytest.raises(ValueError, match="priority_adjustment must be a Decimal"):
        replace(_information_quality(), priority_adjustment=0.1)
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(candidate, reason_codes=["candidate_ranked"])
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(candidate, reason_codes=("candidate_ranked", "candidate_ranked"))
    with pytest.raises(ValueError, match="priority must be nonnegative"):
        replace(candidate, priority=d("-0.000001"))
    with pytest.raises(ValueError, match="final_action reason code"):
        replace(decision, reason_codes=("candidate_ranked",))
    with pytest.raises(ValueError, match="blocked decisions must use zero priority"):
        replace(decision, final_action="blocked")


def test_reducer_rejects_wrong_public_types_subclasses_and_hard_flag_breaks():
    with pytest.raises(ValueError, match="candidate_state"):
        _reduce(object())
    with pytest.raises(ValueError, match="candidate_state"):
        _reduce(CandidateStateSubclass(**_candidate().__dict__))
    with pytest.raises(ValueError, match="information_quality_state"):
        _reduce(information_quality_state=object())
    with pytest.raises(ValueError, match="cost_state"):
        _reduce(cost_state=object())
    with pytest.raises(ValueError, match="liquidity_state"):
        _reduce(liquidity_state=object())
    with pytest.raises(ValueError, match="resolution_state"):
        _reduce(resolution_state=object())
    with pytest.raises(ValueError, match="team_memory_state"):
        _reduce(team_memory_state=object())

    information_quality = _information_quality()
    object.__setattr__(information_quality, "readonly", False)
    with pytest.raises(ValueError, match="information_quality_state must be readonly"):
        _reduce(information_quality_state=information_quality)


def test_module_is_pure_unwired_and_has_no_io_surface():
    source = inspect.getsource(policy_module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "http",
        "io",
        "json",
        "os",
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {
        "open",
        "print",
        "input",
        "compile",
        "eval",
        "exec",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".", 1)[0] for alias in node.names}
            assert imported_roots.isdisjoint(forbidden_import_roots)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
