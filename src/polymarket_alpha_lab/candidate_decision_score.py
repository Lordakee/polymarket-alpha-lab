"""Pure paper-only reducer for integrated candidate decision scores."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_CANDIDATE_DECISION_SCORE_CONFIG_VERSION = "candidate-decision-score-v0"
BOUNDARY_STATEMENT = (
    "Paper-only candidate decision support; no trading or execution authorization."
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
ACTION_STATES = ("reject", "watch", "research_more", "paper_recommend")
SELECTED_SIDES = ("yes", "no")
TEAM_MEMORY_POLICIES = ("allow", "throttle", "block")


@dataclass(frozen=True)
class CandidateDecisionScoreConfig:
    config_version: str = DEFAULT_CANDIDATE_DECISION_SCORE_CONFIG_VERSION
    min_component_score_for_paper_recommend: Decimal = Decimal("0.650000")
    min_decision_score_for_paper_recommend: Decimal = Decimal("0.700000")
    min_net_edge_for_paper_recommend: Decimal = Decimal("0.010000")
    evidence_block_score: Decimal = Decimal("0.350000")
    resolution_block_score: Decimal = Decimal("0.350000")
    liquidity_block_score: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionScoreConfig:
            raise ValueError("config must be a CandidateDecisionScoreConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_component_score_for_paper_recommend",
            "min_decision_score_for_paper_recommend",
            "min_net_edge_for_paper_recommend",
            "evidence_block_score",
            "resolution_block_score",
            "liquidity_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_component_score_for_paper_recommend",
            "min_decision_score_for_paper_recommend",
            "evidence_block_score",
            "resolution_block_score",
            "liquidity_block_score",
        ):
            if getattr(self, field_name) > ONE:
                raise ValueError(f"{field_name} must be no greater than 1")
        require_paper_only_flags("CandidateDecisionScoreConfig", self)


@dataclass(frozen=True)
class CandidateDecisionScoreInput:
    candidate_id: str
    market_id: str
    normalized_market_question: str
    primary_team_id: str
    secondary_team_ids: tuple[str, ...]
    selected_side: str
    forecast_probability: Decimal | None
    executable_price: Decimal | None
    gross_edge: Decimal | None
    estimated_cost_drag: Decimal
    cost_score: Decimal
    liquidity_score: Decimal
    evidence_score: Decimal
    resolution_score: Decimal
    team_memory_score: Decimal
    team_memory_policy: str
    source_report_refs: tuple[str, ...]
    adapter_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string(
            "normalized_market_question",
            self.normalized_market_question,
        )
        object.__setattr__(
            self,
            "primary_team_id",
            require_team_id("primary_team_id", self.primary_team_id),
        )
        object.__setattr__(
            self,
            "secondary_team_ids",
            _normalize_secondary_team_ids(self.secondary_team_ids, self.primary_team_id),
        )
        _require_member("selected_side", self.selected_side, SELECTED_SIDES)
        for field_name in ("forecast_probability", "executable_price"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "gross_edge",
            _normalize_optional_decimal("gross_edge", self.gross_edge),
        )
        object.__setattr__(
            self,
            "estimated_cost_drag",
            _normalize_nonnegative_decimal(
                "estimated_cost_drag",
                self.estimated_cost_drag,
            ),
        )
        for field_name in (
            "cost_score",
            "liquidity_score",
            "evidence_score",
            "resolution_score",
            "team_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "team_memory_policy",
            self.team_memory_policy,
            TEAM_MEMORY_POLICIES,
        )
        object.__setattr__(
            self,
            "source_report_refs",
            _normalize_string_tuple("source_report_refs", self.source_report_refs),
        )
        object.__setattr__(
            self,
            "adapter_reason_codes",
            _normalize_reason_codes(self.adapter_reason_codes, allow_empty=True),
        )
        reject_unsafe_surface_fields("candidate decision score input", self)
        require_paper_only_flags("CandidateDecisionScoreInput", self)


@dataclass(frozen=True)
class CandidateDecisionScoreReport:
    generated_at: datetime
    config_version: str
    candidate_id: str
    market_id: str
    normalized_market_question: str
    primary_team_id: str
    secondary_team_ids: tuple[str, ...]
    selected_side: str
    forecast_probability: Decimal | None
    executable_price: Decimal | None
    gross_edge: Decimal | None
    estimated_cost_drag: Decimal
    net_edge: Decimal | None
    cost_score: Decimal
    liquidity_score: Decimal
    evidence_score: Decimal
    resolution_score: Decimal
    team_memory_score: Decimal
    team_memory_policy: str
    decision_score: Decimal
    action: str
    hard_blocker_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    source_report_refs: tuple[str, ...]
    derived_validation_digest: str
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string(
            "normalized_market_question",
            self.normalized_market_question,
        )
        object.__setattr__(
            self,
            "primary_team_id",
            require_team_id("primary_team_id", self.primary_team_id),
        )
        object.__setattr__(
            self,
            "secondary_team_ids",
            _normalize_secondary_team_ids(self.secondary_team_ids, self.primary_team_id),
        )
        _require_member("selected_side", self.selected_side, SELECTED_SIDES)
        for field_name in ("forecast_probability", "executable_price"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("gross_edge", "net_edge"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "estimated_cost_drag",
            _normalize_nonnegative_decimal(
                "estimated_cost_drag",
                self.estimated_cost_drag,
            ),
        )
        for field_name in (
            "cost_score",
            "liquidity_score",
            "evidence_score",
            "resolution_score",
            "team_memory_score",
            "decision_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "team_memory_policy",
            self.team_memory_policy,
            TEAM_MEMORY_POLICIES,
        )
        _require_member("action", self.action, ACTION_STATES)
        object.__setattr__(
            self,
            "hard_blocker_codes",
            _normalize_reason_codes(self.hard_blocker_codes, allow_empty=True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "source_report_refs",
            _normalize_string_tuple("source_report_refs", self.source_report_refs),
        )
        _require_validation_digest(self.derived_validation_digest)
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match paper-only scope")
        reject_unsafe_surface_fields("candidate decision score report", self)
        require_paper_only_flags("CandidateDecisionScoreReport", self)
        _validate_report(self)
        if self.derived_validation_digest != _report_digest_from_values(
            _report_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match report payload")


def build_candidate_decision_score_report(
    input_value: CandidateDecisionScoreInput,
    *,
    config: CandidateDecisionScoreConfig,
    generated_at: datetime,
) -> CandidateDecisionScoreReport:
    if type(input_value) is not CandidateDecisionScoreInput:
        raise ValueError("input_value must be a CandidateDecisionScoreInput")
    if type(config) is not CandidateDecisionScoreConfig:
        raise ValueError("config must be a CandidateDecisionScoreConfig")
    require_paper_only_flags("CandidateDecisionScoreInput", input_value)
    require_paper_only_flags("CandidateDecisionScoreConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    net_edge = _net_edge(input_value)
    hard_blockers = _hard_blockers(input_value, config)
    decision_score = _decision_score(input_value)
    action = _action(input_value, config, hard_blockers, net_edge, decision_score)
    reason_codes = _reason_codes(input_value, config, action, hard_blockers, net_edge)
    report_values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_id": input_value.candidate_id,
        "market_id": input_value.market_id,
        "normalized_market_question": input_value.normalized_market_question,
        "primary_team_id": input_value.primary_team_id,
        "secondary_team_ids": input_value.secondary_team_ids,
        "selected_side": input_value.selected_side,
        "forecast_probability": input_value.forecast_probability,
        "executable_price": input_value.executable_price,
        "gross_edge": input_value.gross_edge,
        "estimated_cost_drag": input_value.estimated_cost_drag,
        "net_edge": net_edge,
        "cost_score": input_value.cost_score,
        "liquidity_score": input_value.liquidity_score,
        "evidence_score": input_value.evidence_score,
        "resolution_score": input_value.resolution_score,
        "team_memory_score": input_value.team_memory_score,
        "team_memory_policy": input_value.team_memory_policy,
        "decision_score": decision_score,
        "action": action,
        "hard_blocker_codes": hard_blockers,
        "reason_codes": reason_codes,
        "source_report_refs": input_value.source_report_refs,
        "boundary_statement": BOUNDARY_STATEMENT,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CandidateDecisionScoreReport(
        **report_values,
        derived_validation_digest=_report_digest_from_values(report_values),
    )


def candidate_decision_score_payload(
    report: CandidateDecisionScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionScoreReport:
        raise ValueError("report must be a CandidateDecisionScoreReport")
    require_paper_only_flags("CandidateDecisionScoreReport", report)
    reject_unsafe_surface_fields("candidate decision score report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("candidate decision score payload", payload)
    return payload


def _net_edge(input_value: CandidateDecisionScoreInput) -> Decimal | None:
    if input_value.gross_edge is None:
        return None
    return _normalize_decimal("net_edge", input_value.gross_edge - input_value.estimated_cost_drag)


def _decision_score(input_value: CandidateDecisionScoreInput) -> Decimal:
    total = (
        input_value.cost_score
        + input_value.liquidity_score
        + input_value.evidence_score
        + input_value.resolution_score
        + input_value.team_memory_score
    )
    return _normalize_unit_decimal("decision_score", total / Decimal("5"))


def _hard_blockers(
    input_value: CandidateDecisionScoreInput,
    config: CandidateDecisionScoreConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if input_value.evidence_score < config.evidence_block_score:
        codes.append("evidence_score_below_blocking_threshold")
    if input_value.resolution_score < config.resolution_block_score:
        codes.append("resolution_score_below_blocking_threshold")
    if input_value.liquidity_score < config.liquidity_block_score:
        codes.append("liquidity_score_below_blocking_threshold")
    if input_value.team_memory_policy == "block":
        codes.append("team_memory_policy_blocked")
    return tuple(codes)


def _action(
    input_value: CandidateDecisionScoreInput,
    config: CandidateDecisionScoreConfig,
    hard_blockers: tuple[str, ...],
    net_edge: Decimal | None,
    decision_score: Decimal,
) -> str:
    if hard_blockers:
        return "reject"
    if net_edge is None:
        return "research_more"
    if net_edge < config.min_net_edge_for_paper_recommend:
        return "watch"
    if input_value.team_memory_policy == "throttle":
        return "research_more"
    if _min_component_score(input_value) < config.min_component_score_for_paper_recommend:
        return "research_more"
    if decision_score < config.min_decision_score_for_paper_recommend:
        return "watch"
    return "paper_recommend"


def _reason_codes(
    input_value: CandidateDecisionScoreInput,
    config: CandidateDecisionScoreConfig,
    action: str,
    hard_blockers: tuple[str, ...],
    net_edge: Decimal | None,
) -> tuple[str, ...]:
    codes: list[str] = [f"candidate_decision_{action}"]
    codes.extend(hard_blockers)
    if hard_blockers:
        return _normalize_reason_codes(tuple(codes))
    codes.extend(input_value.adapter_reason_codes)
    if input_value.team_memory_policy == "throttle":
        codes.append("team_memory_policy_throttled")
    if net_edge is None:
        codes.append("net_edge_missing")
    elif net_edge < config.min_net_edge_for_paper_recommend:
        codes.append("net_edge_below_paper_recommend_threshold")
    elif _min_component_score(input_value) < config.min_component_score_for_paper_recommend:
        codes.append("component_score_below_paper_recommend_threshold")
    return _normalize_reason_codes(tuple(codes))


def _min_component_score(input_value: CandidateDecisionScoreInput) -> Decimal:
    return min(
        input_value.cost_score,
        input_value.liquidity_score,
        input_value.evidence_score,
        input_value.resolution_score,
        input_value.team_memory_score,
    )


def _validate_report(report: CandidateDecisionScoreReport) -> None:
    if report.net_edge != _expected_net_edge(report.gross_edge, report.estimated_cost_drag):
        raise ValueError("net_edge must match gross_edge minus estimated_cost_drag")
    if report.decision_score != _expected_decision_score(report):
        raise ValueError("decision_score must match component scores")
    if report.reason_codes[0] != f"candidate_decision_{report.action}":
        raise ValueError("reason_codes must start with action reason")
    if report.hard_blocker_codes:
        if report.action != "reject":
            raise ValueError("hard_blocker_codes require reject action")
        for reason_code in report.hard_blocker_codes:
            if reason_code not in report.reason_codes:
                raise ValueError("reason_codes must include hard blockers")


def _expected_net_edge(
    gross_edge: Decimal | None,
    estimated_cost_drag: Decimal,
) -> Decimal | None:
    if gross_edge is None:
        return None
    return _normalize_decimal("net_edge", gross_edge - estimated_cost_drag)


def _expected_decision_score(report: CandidateDecisionScoreReport) -> Decimal:
    total = (
        report.cost_score
        + report.liquidity_score
        + report.evidence_score
        + report.resolution_score
        + report.team_memory_score
    )
    return _normalize_unit_decimal("decision_score", total / Decimal("5"))


def _report_values_without_digest(report: CandidateDecisionScoreReport) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = json_ready_no_floats(values)
    reject_unsafe_surface_fields("candidate decision score digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_secondary_team_ids(value: object, primary_team_id: str) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("secondary_team_ids must be a list or tuple")
    team_ids = tuple(require_team_id("secondary_team_ids", item) for item in value)
    if primary_team_id in team_ids:
        raise ValueError("secondary_team_ids must not include primary_team_id")
    if len(set(team_ids)) != len(team_ids):
        raise ValueError("secondary_team_ids must be unique")
    return team_ids


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    items = tuple(value)
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(items))


def _normalize_reason_codes(
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    action_reasons = tuple(code for code in reason_codes if code.startswith("candidate_decision_"))
    other_reasons = tuple(sorted(code for code in reason_codes if not code.startswith("candidate_decision_")))
    if len(action_reasons) > 1:
        raise ValueError("reason_codes must contain one action reason")
    return action_reasons + other_reasons


def _normalize_optional_unit_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_unit_decimal(field_name, value)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_decimal(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_validation_digest(value: object) -> None:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_SCORE_CONFIG_VERSION",
    "BOUNDARY_STATEMENT",
    "CandidateDecisionScoreConfig",
    "CandidateDecisionScoreInput",
    "CandidateDecisionScoreReport",
    "build_candidate_decision_score_report",
    "candidate_decision_score_payload",
)
