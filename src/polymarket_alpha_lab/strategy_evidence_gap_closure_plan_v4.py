"""Pure strategy evidence gap closure plan v4."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_STRATEGY_EVIDENCE_GAP_CLOSURE_PLAN_V4_VERSION = (
    "strategy-evidence-gap-closure-plan-v4"
)

COUNT_QUANTUM = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ONE_SCORE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

GAP_TYPES = (
    "missing_primary_source",
    "stale_evidence",
    "conflicting_sources",
    "unclear_resolution",
    "weak_team_memory",
)
INPUT_REASON_CODES = ("strategy_evidence_gap_closure_plan_v4_input",)
ACTION_REASON_CODES = (
    "strategy_evidence_gap_closure_plan_v4_missing_primary_source",
    "strategy_evidence_gap_closure_plan_v4_stale_evidence",
    "strategy_evidence_gap_closure_plan_v4_conflicting_sources",
    "strategy_evidence_gap_closure_plan_v4_unclear_resolution",
    "strategy_evidence_gap_closure_plan_v4_weak_team_memory",
)
PLAN_REASON_CODES = (
    "strategy_evidence_gap_closure_plan_v4_no_gaps",
    *ACTION_REASON_CODES,
)
NEXT_RESEARCH_ACTIONS = {
    "missing_primary_source": "collect_primary_resolution_source",
    "stale_evidence": "refresh_stale_evidence",
    "conflicting_sources": "reconcile_conflicting_sources",
    "unclear_resolution": "clarify_resolution_rule",
    "weak_team_memory": "rebuild_team_memory_support",
}
ACTION_STATUSES = {
    "missing_primary_source": "blocking",
    "stale_evidence": "watch",
    "conflicting_sources": "blocking",
    "unclear_resolution": "blocking",
    "weak_team_memory": "blocking",
}
GAP_TYPE_PRIORITY = {
    "missing_primary_source": Decimal("1"),
    "stale_evidence": Decimal("2"),
    "conflicting_sources": Decimal("3"),
    "unclear_resolution": Decimal("4"),
    "weak_team_memory": Decimal("5"),
}
GAP_TYPE_REASON_CODES = dict(zip(GAP_TYPES, ACTION_REASON_CODES, strict=True))

__all__ = (
    "DEFAULT_STRATEGY_EVIDENCE_GAP_CLOSURE_PLAN_V4_VERSION",
    "StrategyEvidenceGapClosurePlanV4Config",
    "StrategyEvidenceGapV4Input",
    "StrategyEvidenceGapClosureActionV4",
    "StrategyEvidenceGapClosurePlanV4",
    "build_strategy_evidence_gap_closure_plan_v4",
    "strategy_evidence_gap_closure_plan_v4_payload",
)


@dataclass(frozen=True)
class StrategyEvidenceGapClosurePlanV4Config:
    plan_version: str = DEFAULT_STRATEGY_EVIDENCE_GAP_CLOSURE_PLAN_V4_VERSION
    deadline_missing_primary_source_minutes: Decimal = Decimal("30")
    deadline_stale_evidence_minutes: Decimal = Decimal("45")
    deadline_conflicting_sources_minutes: Decimal = Decimal("60")
    deadline_unclear_resolution_minutes: Decimal = Decimal("90")
    deadline_weak_team_memory_minutes: Decimal = Decimal("120")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("plan_version", self.plan_version)
        for field_name in (
            "deadline_missing_primary_source_minutes",
            "deadline_stale_evidence_minutes",
            "deadline_conflicting_sources_minutes",
            "deadline_unclear_resolution_minutes",
            "deadline_weak_team_memory_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("StrategyEvidenceGapClosurePlanV4Config", self)


@dataclass(frozen=True)
class StrategyEvidenceGapV4Input:
    gap_id: str
    team_id: str
    category_id: str
    market_slug: str
    gap_type: str
    source_id: str | None
    memory_item_id: str | None
    severity_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        _require_canonical_string("gap_id", self.gap_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_member("gap_type", self.gap_type, GAP_TYPES)
        object.__setattr__(
            self,
            "source_id",
            _normalize_optional_string("source_id", self.source_id),
        )
        object.__setattr__(
            self,
            "memory_item_id",
            _normalize_optional_string("memory_item_id", self.memory_item_id),
        )
        object.__setattr__(
            self,
            "severity_score",
            _normalize_score("severity_score", self.severity_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                INPUT_REASON_CODES,
            ),
        )
        require_paper_only_flags("StrategyEvidenceGapV4Input", self)


@dataclass(frozen=True)
class StrategyEvidenceGapClosureActionV4:
    priority_rank: Decimal
    gap_id: str
    team_id: str
    category_id: str
    market_slug: str
    gap_type: str
    source_id: str | None
    memory_item_id: str | None
    next_research_action: str
    owner_team: str
    deadline_minutes: Decimal
    action_status: str
    severity_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_count("priority_rank", self.priority_rank),
        )
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        _require_canonical_string("gap_id", self.gap_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_member("gap_type", self.gap_type, GAP_TYPES)
        object.__setattr__(
            self,
            "source_id",
            _normalize_optional_string("source_id", self.source_id),
        )
        object.__setattr__(
            self,
            "memory_item_id",
            _normalize_optional_string("memory_item_id", self.memory_item_id),
        )
        _require_member(
            "next_research_action",
            self.next_research_action,
            tuple(NEXT_RESEARCH_ACTIONS.values()),
        )
        object.__setattr__(self, "owner_team", require_team_id("owner_team", self.owner_team))
        object.__setattr__(
            self,
            "deadline_minutes",
            _normalize_positive_count("deadline_minutes", self.deadline_minutes),
        )
        _require_member("action_status", self.action_status, ("blocking", "watch"))
        object.__setattr__(
            self,
            "severity_score",
            _normalize_score("severity_score", self.severity_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ACTION_REASON_CODES,
            ),
        )
        _validate_action(self)
        require_paper_only_flags("StrategyEvidenceGapClosureActionV4", self)


@dataclass(frozen=True)
class StrategyEvidenceGapClosurePlanV4:
    plan_version: str
    input_gap_count: Decimal
    action_count: Decimal
    blocking_action_count: Decimal
    watch_action_count: Decimal
    owner_team_count: Decimal
    reason_codes: tuple[str, ...]
    actions: tuple[StrategyEvidenceGapClosureActionV4, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("plan_version", self.plan_version)
        for field_name in (
            "input_gap_count",
            "action_count",
            "blocking_action_count",
            "watch_action_count",
            "owner_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                PLAN_REASON_CODES,
            ),
        )
        object.__setattr__(self, "actions", _normalize_actions(self.actions))
        _validate_plan(self)
        reject_unsafe_surface_fields("strategy evidence gap closure plan v4", self)
        require_paper_only_flags("StrategyEvidenceGapClosurePlanV4", self)


def build_strategy_evidence_gap_closure_plan_v4(
    inputs: list[StrategyEvidenceGapV4Input] | tuple[StrategyEvidenceGapV4Input, ...],
    *,
    config: StrategyEvidenceGapClosurePlanV4Config,
) -> StrategyEvidenceGapClosurePlanV4:
    if type(config) is not StrategyEvidenceGapClosurePlanV4Config:
        raise ValueError("config must be a StrategyEvidenceGapClosurePlanV4Config")
    require_paper_only_flags("config", config)
    rows = _normalize_inputs(inputs)
    sorted_rows = tuple(sorted(rows, key=lambda row: _input_sort_key(row, config)))
    actions = tuple(
        _action_for_gap(row, config, priority_rank=_count(index + 1))
        for index, row in enumerate(sorted_rows)
    )
    return StrategyEvidenceGapClosurePlanV4(
        plan_version=config.plan_version,
        input_gap_count=_count(len(rows)),
        action_count=_count(len(actions)),
        blocking_action_count=_status_count(actions, "blocking"),
        watch_action_count=_status_count(actions, "watch"),
        owner_team_count=_count(len({action.owner_team for action in actions})),
        reason_codes=_plan_reason_codes(actions),
        actions=actions,
    )


def strategy_evidence_gap_closure_plan_v4_payload(
    report: StrategyEvidenceGapClosurePlanV4,
) -> dict[str, Any]:
    if type(report) is not StrategyEvidenceGapClosurePlanV4:
        raise ValueError("report must be a StrategyEvidenceGapClosurePlanV4")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("strategy evidence gap closure plan v4", report)
    return json_ready_no_floats(report)


def _action_for_gap(
    row: StrategyEvidenceGapV4Input,
    config: StrategyEvidenceGapClosurePlanV4Config,
    *,
    priority_rank: Decimal,
) -> StrategyEvidenceGapClosureActionV4:
    return StrategyEvidenceGapClosureActionV4(
        priority_rank=priority_rank,
        gap_id=row.gap_id,
        team_id=row.team_id,
        category_id=row.category_id,
        market_slug=row.market_slug,
        gap_type=row.gap_type,
        source_id=row.source_id,
        memory_item_id=row.memory_item_id,
        next_research_action=NEXT_RESEARCH_ACTIONS[row.gap_type],
        owner_team=row.team_id,
        deadline_minutes=_deadline_minutes(row.gap_type, config),
        action_status=ACTION_STATUSES[row.gap_type],
        severity_score=row.severity_score,
        reason_codes=(GAP_TYPE_REASON_CODES[row.gap_type],),
    )


def _deadline_minutes(
    gap_type: str,
    config: StrategyEvidenceGapClosurePlanV4Config,
) -> Decimal:
    if gap_type == "missing_primary_source":
        return config.deadline_missing_primary_source_minutes
    if gap_type == "stale_evidence":
        return config.deadline_stale_evidence_minutes
    if gap_type == "conflicting_sources":
        return config.deadline_conflicting_sources_minutes
    if gap_type == "unclear_resolution":
        return config.deadline_unclear_resolution_minutes
    if gap_type == "weak_team_memory":
        return config.deadline_weak_team_memory_minutes
    raise ValueError("gap_type must be supported")


def _input_sort_key(
    row: StrategyEvidenceGapV4Input,
    config: StrategyEvidenceGapClosurePlanV4Config,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        GAP_TYPE_PRIORITY[row.gap_type],
        -row.severity_score,
        _deadline_minutes(row.gap_type, config),
        row.gap_id,
    )


def _action_sort_key(
    action: StrategyEvidenceGapClosureActionV4,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        GAP_TYPE_PRIORITY[action.gap_type],
        -action.severity_score,
        action.deadline_minutes,
        action.gap_id,
    )


def _plan_reason_codes(
    actions: tuple[StrategyEvidenceGapClosureActionV4, ...],
) -> tuple[str, ...]:
    if not actions:
        return ("strategy_evidence_gap_closure_plan_v4_no_gaps",)
    return tuple(
        reason_code
        for reason_code in ACTION_REASON_CODES
        if any(reason_code in action.reason_codes for action in actions)
    )


def _status_count(
    actions: tuple[StrategyEvidenceGapClosureActionV4, ...],
    action_status: str,
) -> Decimal:
    return _count(sum(1 for action in actions if action.action_status == action_status))


def _normalize_inputs(
    inputs: list[StrategyEvidenceGapV4Input] | tuple[StrategyEvidenceGapV4Input, ...],
) -> tuple[StrategyEvidenceGapV4Input, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_gap_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyEvidenceGapV4Input:
            raise ValueError("inputs must contain StrategyEvidenceGapV4Input values")
        require_paper_only_flags("input", row)
        if row.gap_id in seen_gap_ids:
            raise ValueError("inputs must not contain duplicate gap_id values")
        seen_gap_ids.add(row.gap_id)
    return rows


def _normalize_actions(
    value: object,
) -> tuple[StrategyEvidenceGapClosureActionV4, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("actions must be a list or tuple")
    actions = tuple(value)
    seen_gap_ids: set[str] = set()
    for action in actions:
        if type(action) is not StrategyEvidenceGapClosureActionV4:
            raise ValueError("actions must contain StrategyEvidenceGapClosureActionV4 values")
        require_paper_only_flags("action", action)
        if action.gap_id in seen_gap_ids:
            raise ValueError("actions must contain unique gap_id values")
        seen_gap_ids.add(action.gap_id)
    expected_ranks = tuple(_count(index + 1) for index in range(len(actions)))
    if tuple(action.priority_rank for action in actions) != expected_ranks:
        raise ValueError("actions must use contiguous priority_rank values")
    if actions != tuple(sorted(actions, key=_action_sort_key)):
        raise ValueError("actions must use stable priority sort")
    return actions


def _validate_action(action: StrategyEvidenceGapClosureActionV4) -> None:
    if action.next_research_action != NEXT_RESEARCH_ACTIONS[action.gap_type]:
        raise ValueError("next_research_action must match gap_type")
    if action.action_status != ACTION_STATUSES[action.gap_type]:
        raise ValueError("action_status must match gap_type")
    if action.reason_codes != (GAP_TYPE_REASON_CODES[action.gap_type],):
        raise ValueError("reason_codes must match gap_type")
    if action.owner_team != action.team_id:
        raise ValueError("owner_team must match team_id")


def _validate_plan(report: StrategyEvidenceGapClosurePlanV4) -> None:
    if report.input_gap_count != report.action_count:
        raise ValueError("input_gap_count must match action_count")
    if report.action_count != _count(len(report.actions)):
        raise ValueError("action_count must match actions")
    if report.blocking_action_count != _status_count(report.actions, "blocking"):
        raise ValueError("blocking_action_count must match actions")
    if report.watch_action_count != _status_count(report.actions, "watch"):
        raise ValueError("watch_action_count must match actions")
    if report.owner_team_count != _count(len({action.owner_team for action in report.actions})):
        raise ValueError("owner_team_count must match actions")
    if report.reason_codes != _plan_reason_codes(report.actions):
        raise ValueError("reason_codes must match actions")


def _require_canonical_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{name} must be canonical")
    return value


def _normalize_optional_string(name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_canonical_string(name, value)


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be supported")
    return value


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must not be empty")
    for reason_code in reason_codes:
        _require_member(name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{name} must not contain duplicates")
    if reason_codes != tuple(code for code in allowed if code in reason_codes):
        raise ValueError(f"{name} must use stable sort")
    return reason_codes


def _normalize_positive_count(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO_COUNT:
        raise ValueError(f"{name} must be positive")
    return _quantize_count(name, decimal_value)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize_count(name, decimal_value)


def _normalize_score(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO_COUNT or decimal_value > ONE_SCORE:
        raise ValueError(f"{name} must be between zero and one")
    with localcontext(DECIMAL_CONTEXT):
        quantized = decimal_value.quantize(SCORE_QUANTUM)
    if quantized != decimal_value:
        raise ValueError(f"{name} must use six decimal places")
    return quantized


def _quantize_count(name: str, value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{name} must be an integer Decimal")
    return quantized


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)
