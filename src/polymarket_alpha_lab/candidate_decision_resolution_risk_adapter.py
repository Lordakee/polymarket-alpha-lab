"""Paper-only adapter from resolution risk facts to candidate decision input."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.candidate_decision_score import CandidateDecisionScoreInput
from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

SPECIFICITY_STATUSES = ("pass", "watch", "blocked")
DEPENDENCY_STATUSES = ("pass", "watch", "blocked")
DISPUTE_RISK_STATUSES = ("clear", "watch", "elevated", "blocked")
OUTCOME_RULE_CLARITY_STATUSES = ("clear", "watch", "unclear")
CLOSE_READINESS_STATUSES = ("ready", "watch", "blocked")
TEAM_MEMORY_POLICIES = ("allow", "throttle", "block")
SELECTED_SIDES = ("yes", "no")
RESOLUTION_RISK_STATUSES = ("clear", "watch", "blocked")

CLOSE_READINESS_SCORES = {
    "ready": Decimal("1.000000"),
    "watch": Decimal("0.650000"),
    "blocked": Decimal("0.000000"),
}

BLOCKED_RESOLUTION_SCORE = Decimal("0.300000")

ADAPTER_REASON_CODES = (
    "resolution_adapter_clear",
    "resolution_adapter_watch",
    "resolution_adapter_blocked",
    "resolution_specificity_watch",
    "resolution_specificity_blocked",
    "resolution_dependency_watch",
    "resolution_dependency_blocked",
    "resolution_dispute_watch",
    "resolution_dispute_elevated",
    "resolution_dispute_blocked",
    "resolution_outcome_rule_clarity_watch",
    "resolution_outcome_rule_clarity_unclear",
    "resolution_close_ready",
    "resolution_close_watch",
    "resolution_close_blocked",
    "resolution_authoritative_source_present",
    "resolution_authoritative_source_missing",
    "resolution_no_unresolved_ambiguity",
    "resolution_ambiguity_unresolved",
)

UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    "api" + "_key",
    "author" + "ization",
    "creden" + "tial",
    "private" + "_key",
    "sec" + "ret",
    "wall" + "et",
    "account" + "_" + "access",
    "order" + "_" + "placement",
    "place" + "_" + "order",
    "submit" + "_" + "order",
    "cancel" + "_" + "order",
    "live" + "_" + "trading",
    "net" + "work",
    "data" + "base",
    "d" + "b" + "_",
)


@dataclass(frozen=True)
class CandidateDecisionResolutionRiskFacts:
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
    team_memory_score: Decimal
    team_memory_policy: str
    source_report_refs: tuple[str, ...]
    specificity_status: str
    specificity_risk_score: Decimal
    dependency_status: str
    dependency_risk_score: Decimal
    dispute_risk_status: str
    dispute_risk_score: Decimal
    outcome_rule_clarity_status: str
    outcome_rule_clarity_score: Decimal
    close_readiness_status: str
    authoritative_source_present: bool
    unresolved_ambiguity_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionRiskFacts:
            raise ValueError(
                "facts must be a CandidateDecisionResolutionRiskFacts",
            )
        for field_name in (
            "candidate_id",
            "market_id",
            "normalized_market_question",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
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
            "team_memory_score",
            "specificity_risk_score",
            "dependency_risk_score",
            "dispute_risk_score",
            "outcome_rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("team_memory_policy", self.team_memory_policy, TEAM_MEMORY_POLICIES)
        _require_member("specificity_status", self.specificity_status, SPECIFICITY_STATUSES)
        _require_member("dependency_status", self.dependency_status, DEPENDENCY_STATUSES)
        _require_member(
            "dispute_risk_status",
            self.dispute_risk_status,
            DISPUTE_RISK_STATUSES,
        )
        _require_member(
            "outcome_rule_clarity_status",
            self.outcome_rule_clarity_status,
            OUTCOME_RULE_CLARITY_STATUSES,
        )
        _require_member(
            "close_readiness_status",
            self.close_readiness_status,
            CLOSE_READINESS_STATUSES,
        )
        if type(self.authoritative_source_present) is not bool:
            raise ValueError("authoritative_source_present must be a bool")
        object.__setattr__(
            self,
            "unresolved_ambiguity_count",
            _normalize_whole_nonnegative_decimal(
                "unresolved_ambiguity_count",
                self.unresolved_ambiguity_count,
            ),
        )
        object.__setattr__(
            self,
            "source_report_refs",
            _normalize_string_tuple("source_report_refs", self.source_report_refs),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _reject_unsafe_surface_fields("candidate decision resolution risk facts", self)
        require_paper_only_flags("CandidateDecisionResolutionRiskFacts", self)


@dataclass(frozen=True)
class CandidateDecisionResolutionRiskAdapterReport:
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
    team_memory_score: Decimal
    team_memory_policy: str
    source_report_refs: tuple[str, ...]
    specificity_status: str
    specificity_risk_score: Decimal
    dependency_status: str
    dependency_risk_score: Decimal
    dispute_risk_status: str
    dispute_risk_score: Decimal
    outcome_rule_clarity_status: str
    outcome_rule_clarity_score: Decimal
    close_readiness_status: str
    close_readiness_score: Decimal
    authoritative_source_present: bool
    unresolved_ambiguity_count: Decimal
    resolution_score: Decimal
    resolution_risk_status: str
    hard_blocker_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionRiskAdapterReport:
            raise ValueError(
                "report must be a CandidateDecisionResolutionRiskAdapterReport",
            )
        facts = _facts_from_report(self)
        object.__setattr__(
            self,
            "close_readiness_score",
            _normalize_unit_decimal("close_readiness_score", self.close_readiness_score),
        )
        object.__setattr__(
            self,
            "resolution_score",
            _normalize_unit_decimal("resolution_score", self.resolution_score),
        )
        _require_member(
            "resolution_risk_status",
            self.resolution_risk_status,
            RESOLUTION_RISK_STATUSES,
        )
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
        expected_close_readiness_score = _close_readiness_score(
            facts.close_readiness_status,
        )
        if self.close_readiness_score != expected_close_readiness_score:
            raise ValueError("close_readiness_score must match close_readiness_status")
        expected_blockers = _hard_blocker_codes(facts)
        if self.hard_blocker_codes != expected_blockers:
            raise ValueError("hard_blocker_codes must match resolution facts")
        expected_score = _resolution_score(facts, expected_blockers)
        if self.resolution_score != expected_score:
            raise ValueError("resolution_score must match resolution facts")
        expected_status = _resolution_risk_status(facts, expected_score, expected_blockers)
        if self.resolution_risk_status != expected_status:
            raise ValueError("resolution_risk_status must match resolution facts")
        expected_reason_codes = _adapter_reason_codes(
            facts,
            expected_status,
            expected_blockers,
        )
        if self.reason_codes != expected_reason_codes:
            raise ValueError("reason_codes must match resolution facts")
        _normalize_report_fields(self, facts)
        _reject_unsafe_surface_fields("candidate decision resolution risk report", self)
        require_paper_only_flags("CandidateDecisionResolutionRiskAdapterReport", self)


def build_candidate_decision_resolution_risk_adapter_report(
    facts: CandidateDecisionResolutionRiskFacts,
) -> CandidateDecisionResolutionRiskAdapterReport:
    if type(facts) is not CandidateDecisionResolutionRiskFacts:
        raise ValueError("facts must be a CandidateDecisionResolutionRiskFacts")
    require_paper_only_flags("CandidateDecisionResolutionRiskFacts", facts)
    _reject_unsafe_surface_fields("candidate decision resolution risk facts", facts)
    blockers = _hard_blocker_codes(facts)
    resolution_score = _resolution_score(facts, blockers)
    resolution_risk_status = _resolution_risk_status(facts, resolution_score, blockers)
    return CandidateDecisionResolutionRiskAdapterReport(
        candidate_id=facts.candidate_id,
        market_id=facts.market_id,
        normalized_market_question=facts.normalized_market_question,
        primary_team_id=facts.primary_team_id,
        secondary_team_ids=facts.secondary_team_ids,
        selected_side=facts.selected_side,
        forecast_probability=facts.forecast_probability,
        executable_price=facts.executable_price,
        gross_edge=facts.gross_edge,
        estimated_cost_drag=facts.estimated_cost_drag,
        cost_score=facts.cost_score,
        liquidity_score=facts.liquidity_score,
        evidence_score=facts.evidence_score,
        team_memory_score=facts.team_memory_score,
        team_memory_policy=facts.team_memory_policy,
        source_report_refs=facts.source_report_refs,
        specificity_status=facts.specificity_status,
        specificity_risk_score=facts.specificity_risk_score,
        dependency_status=facts.dependency_status,
        dependency_risk_score=facts.dependency_risk_score,
        dispute_risk_status=facts.dispute_risk_status,
        dispute_risk_score=facts.dispute_risk_score,
        outcome_rule_clarity_status=facts.outcome_rule_clarity_status,
        outcome_rule_clarity_score=facts.outcome_rule_clarity_score,
        close_readiness_status=facts.close_readiness_status,
        close_readiness_score=_close_readiness_score(facts.close_readiness_status),
        authoritative_source_present=facts.authoritative_source_present,
        unresolved_ambiguity_count=facts.unresolved_ambiguity_count,
        resolution_score=resolution_score,
        resolution_risk_status=resolution_risk_status,
        hard_blocker_codes=blockers,
        reason_codes=_adapter_reason_codes(facts, resolution_risk_status, blockers),
    )


def build_candidate_decision_score_input_from_resolution_risk(
    facts: CandidateDecisionResolutionRiskFacts,
) -> CandidateDecisionScoreInput:
    report = build_candidate_decision_resolution_risk_adapter_report(facts)
    return CandidateDecisionScoreInput(
        candidate_id=report.candidate_id,
        market_id=report.market_id,
        normalized_market_question=report.normalized_market_question,
        primary_team_id=report.primary_team_id,
        secondary_team_ids=report.secondary_team_ids,
        selected_side=report.selected_side,
        forecast_probability=report.forecast_probability,
        executable_price=report.executable_price,
        gross_edge=report.gross_edge,
        estimated_cost_drag=report.estimated_cost_drag,
        cost_score=report.cost_score,
        liquidity_score=report.liquidity_score,
        evidence_score=report.evidence_score,
        resolution_score=report.resolution_score,
        team_memory_score=report.team_memory_score,
        team_memory_policy=report.team_memory_policy,
        source_report_refs=report.source_report_refs,
        adapter_reason_codes=report.reason_codes,
    )


def candidate_decision_resolution_risk_adapter_payload(
    report: CandidateDecisionResolutionRiskAdapterReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionResolutionRiskAdapterReport:
        raise ValueError("report must be a CandidateDecisionResolutionRiskAdapterReport")
    require_paper_only_flags("CandidateDecisionResolutionRiskAdapterReport", report)
    _reject_unsafe_surface_fields("candidate decision resolution risk report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_surface_fields("candidate decision resolution risk payload", payload)
    return payload


def _facts_from_report(
    report: CandidateDecisionResolutionRiskAdapterReport,
) -> CandidateDecisionResolutionRiskFacts:
    return CandidateDecisionResolutionRiskFacts(
        candidate_id=report.candidate_id,
        market_id=report.market_id,
        normalized_market_question=report.normalized_market_question,
        primary_team_id=report.primary_team_id,
        secondary_team_ids=report.secondary_team_ids,
        selected_side=report.selected_side,
        forecast_probability=report.forecast_probability,
        executable_price=report.executable_price,
        gross_edge=report.gross_edge,
        estimated_cost_drag=report.estimated_cost_drag,
        cost_score=report.cost_score,
        liquidity_score=report.liquidity_score,
        evidence_score=report.evidence_score,
        team_memory_score=report.team_memory_score,
        team_memory_policy=report.team_memory_policy,
        source_report_refs=report.source_report_refs,
        specificity_status=report.specificity_status,
        specificity_risk_score=report.specificity_risk_score,
        dependency_status=report.dependency_status,
        dependency_risk_score=report.dependency_risk_score,
        dispute_risk_status=report.dispute_risk_status,
        dispute_risk_score=report.dispute_risk_score,
        outcome_rule_clarity_status=report.outcome_rule_clarity_status,
        outcome_rule_clarity_score=report.outcome_rule_clarity_score,
        close_readiness_status=report.close_readiness_status,
        authoritative_source_present=report.authoritative_source_present,
        unresolved_ambiguity_count=report.unresolved_ambiguity_count,
        reason_codes=_upstream_reason_codes_from_report(report.reason_codes),
    )


def _resolution_score(
    facts: CandidateDecisionResolutionRiskFacts,
    hard_blocker_codes: tuple[str, ...],
) -> Decimal:
    if hard_blocker_codes:
        return BLOCKED_RESOLUTION_SCORE
    risk_penalty = (
        facts.specificity_risk_score * Decimal("0.250000")
        + facts.dependency_risk_score * Decimal("0.250000")
        + facts.dispute_risk_score * Decimal("0.200000")
    )
    clarity_penalty = (ONE - facts.outcome_rule_clarity_score) * Decimal("0.500000")
    close_penalty = (
        ONE
        - _close_readiness_score(facts.close_readiness_status)
    ) * Decimal("0.200000")
    raw_score = ONE - risk_penalty - clarity_penalty - close_penalty
    return _normalize_unit_decimal("resolution_score", raw_score)


def _resolution_risk_status(
    facts: CandidateDecisionResolutionRiskFacts,
    resolution_score: Decimal,
    hard_blocker_codes: tuple[str, ...],
) -> str:
    if hard_blocker_codes:
        return "blocked"
    if (
        facts.specificity_status != "pass"
        or facts.dependency_status != "pass"
        or facts.dispute_risk_status != "clear"
        or facts.outcome_rule_clarity_status != "clear"
        or facts.close_readiness_status != "ready"
        or resolution_score < ONE
    ):
        return "watch"
    return "clear"


def _hard_blocker_codes(
    facts: CandidateDecisionResolutionRiskFacts,
) -> tuple[str, ...]:
    codes: list[str] = []
    if facts.specificity_status == "blocked":
        codes.append("resolution_specificity_blocked")
    if facts.dependency_status == "blocked":
        codes.append("resolution_dependency_blocked")
    if facts.dispute_risk_status == "elevated":
        codes.append("resolution_dispute_elevated")
    elif facts.dispute_risk_status == "blocked":
        codes.append("resolution_dispute_blocked")
    if facts.outcome_rule_clarity_status == "unclear":
        codes.append("resolution_outcome_rule_clarity_unclear")
    if facts.close_readiness_status == "blocked":
        codes.append("resolution_close_blocked")
    if not facts.authoritative_source_present:
        codes.append("resolution_authoritative_source_missing")
    if facts.unresolved_ambiguity_count > ZERO:
        codes.append("resolution_ambiguity_unresolved")
    return tuple(codes)


def _adapter_reason_codes(
    facts: CandidateDecisionResolutionRiskFacts,
    resolution_risk_status: str,
    hard_blocker_codes: tuple[str, ...],
) -> tuple[str, ...]:
    codes: list[str] = [f"resolution_adapter_{resolution_risk_status}"]
    codes.extend(hard_blocker_codes)
    if facts.specificity_status == "watch":
        codes.append("resolution_specificity_watch")
    if facts.dependency_status == "watch":
        codes.append("resolution_dependency_watch")
    if facts.dispute_risk_status == "watch":
        codes.append("resolution_dispute_watch")
    if facts.outcome_rule_clarity_status == "watch":
        codes.append("resolution_outcome_rule_clarity_watch")
    if facts.authoritative_source_present:
        codes.append("resolution_authoritative_source_present")
    if facts.close_readiness_status == "ready":
        codes.append("resolution_close_ready")
    elif facts.close_readiness_status == "watch":
        codes.append("resolution_close_watch")
    if facts.unresolved_ambiguity_count == ZERO:
        codes.append("resolution_no_unresolved_ambiguity")
    codes.extend(facts.reason_codes)
    return _normalize_reason_codes(tuple(codes))


def _close_readiness_score(close_readiness_status: str) -> Decimal:
    if close_readiness_status == "ready":
        return CLOSE_READINESS_SCORES["ready"]
    if close_readiness_status == "watch":
        return CLOSE_READINESS_SCORES["watch"]
    if close_readiness_status == "blocked":
        return CLOSE_READINESS_SCORES["blocked"]
    raise ValueError("close_readiness_status must be known")


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
    generated = tuple(
        code
        for code in reason_codes
        if code.startswith("resolution_") and code in ADAPTER_REASON_CODES
    )
    upstream = tuple(
        sorted(
            code
            for code in reason_codes
            if not (code.startswith("resolution_") and code in ADAPTER_REASON_CODES)
        ),
    )
    action_codes = tuple(
        code for code in generated if code.startswith("resolution_adapter_")
    )
    if len(action_codes) > 1:
        raise ValueError("reason_codes must contain one adapter status reason")
    non_action_generated = tuple(
        code for code in generated if not code.startswith("resolution_adapter_")
    )
    return action_codes + non_action_generated + upstream


def _upstream_reason_codes_from_report(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(code for code in reason_codes if code not in ADAPTER_REASON_CODES)


def _normalize_report_fields(
    report: CandidateDecisionResolutionRiskAdapterReport,
    facts: CandidateDecisionResolutionRiskFacts,
) -> None:
    for field_name in (
        "candidate_id",
        "market_id",
        "normalized_market_question",
        "primary_team_id",
        "secondary_team_ids",
        "selected_side",
        "forecast_probability",
        "executable_price",
        "gross_edge",
        "estimated_cost_drag",
        "cost_score",
        "liquidity_score",
        "evidence_score",
        "team_memory_score",
        "team_memory_policy",
        "source_report_refs",
        "specificity_status",
        "specificity_risk_score",
        "dependency_status",
        "dependency_risk_score",
        "dispute_risk_status",
        "dispute_risk_score",
        "outcome_rule_clarity_status",
        "outcome_rule_clarity_score",
        "close_readiness_status",
        "authoritative_source_present",
        "unresolved_ambiguity_count",
    ):
        object.__setattr__(report, field_name, getattr(facts, field_name))


def _reject_unsafe_surface_fields(label: str, payload: object) -> None:
    for key in _iter_payload_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe live surface field in {label}: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_payload_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


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


def _normalize_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.quantize(COUNT_QUANTUM)


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


__all__ = (
    "SPECIFICITY_STATUSES",
    "DEPENDENCY_STATUSES",
    "DISPUTE_RISK_STATUSES",
    "OUTCOME_RULE_CLARITY_STATUSES",
    "CLOSE_READINESS_STATUSES",
    "RESOLUTION_RISK_STATUSES",
    "CandidateDecisionResolutionRiskFacts",
    "CandidateDecisionResolutionRiskAdapterReport",
    "build_candidate_decision_resolution_risk_adapter_report",
    "build_candidate_decision_score_input_from_resolution_risk",
    "candidate_decision_resolution_risk_adapter_payload",
)
