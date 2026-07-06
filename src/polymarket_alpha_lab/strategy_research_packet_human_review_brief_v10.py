"""Pure read-only human review brief builder for research packets v10."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
READY_THRESHOLD = Decimal("0.700000")
NEAR_RESOLUTION_MINUTES = Decimal("60.000000")

BRIEF_STATUSES = ("approval_ready", "review_required", "blocked")
PACKET_STATUSES = ("complete", "watch", "blocked", "rejected")
REASON_CODES = (
    "packet_status_complete",
    "packet_status_watch",
    "packet_status_blocked",
    "packet_status_rejected",
    "missing_sections_present",
    "decision_readiness_ready",
    "decision_readiness_low",
    "evidence_present",
    "evidence_missing",
    "positive_cost_adjusted_edge",
    "nonpositive_cost_adjusted_edge",
    "no_top_risks",
    "risks_present",
    "near_resolution",
    "approval_ready",
    "human_review_required",
    "approval_blocked",
)


@dataclass(frozen=True)
class StrategyResearchPacketHumanReviewBriefV10Input:
    market_id: str
    decision_readiness: Decimal
    packet_status: str
    top_risks: tuple[str, ...]
    top_evidence_points: tuple[str, ...]
    missing_sections_count: Decimal
    cost_adjusted_edge_bps: Decimal
    time_to_resolution_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "decision_readiness",
            _normalize_probability("decision_readiness", self.decision_readiness),
        )
        _require_member("packet_status", self.packet_status, PACKET_STATUSES)
        object.__setattr__(
            self,
            "top_risks",
            _normalize_string_tuple("top_risks", self.top_risks),
        )
        object.__setattr__(
            self,
            "top_evidence_points",
            _normalize_string_tuple("top_evidence_points", self.top_evidence_points),
        )
        object.__setattr__(
            self,
            "missing_sections_count",
            _normalize_nonnegative_count(
                "missing_sections_count",
                self.missing_sections_count,
            ),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge_bps",
            _normalize_decimal("cost_adjusted_edge_bps", self.cost_adjusted_edge_bps),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        reject_unsafe_surface_fields("research packet human review brief input", self)
        require_paper_only_flags("research packet human review brief input", self)


@dataclass(frozen=True)
class StrategyResearchPacketHumanReviewBriefV10Result:
    market_id: str
    decision_readiness: Decimal
    packet_status: str
    top_risks: tuple[str, ...]
    top_evidence_points: tuple[str, ...]
    missing_sections_count: Decimal
    cost_adjusted_edge_bps: Decimal
    time_to_resolution_minutes: Decimal
    brief_status: str
    review_questions: tuple[str, ...]
    approval_blockers: tuple[str, ...]
    summary_points: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "decision_readiness",
            _normalize_probability("decision_readiness", self.decision_readiness),
        )
        _require_member("packet_status", self.packet_status, PACKET_STATUSES)
        object.__setattr__(
            self,
            "top_risks",
            _normalize_string_tuple("top_risks", self.top_risks),
        )
        object.__setattr__(
            self,
            "top_evidence_points",
            _normalize_string_tuple("top_evidence_points", self.top_evidence_points),
        )
        object.__setattr__(
            self,
            "missing_sections_count",
            _normalize_nonnegative_count(
                "missing_sections_count",
                self.missing_sections_count,
            ),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge_bps",
            _normalize_decimal("cost_adjusted_edge_bps", self.cost_adjusted_edge_bps),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        _require_member("brief_status", self.brief_status, BRIEF_STATUSES)
        object.__setattr__(
            self,
            "review_questions",
            _normalize_string_tuple("review_questions", self.review_questions),
        )
        object.__setattr__(
            self,
            "approval_blockers",
            _normalize_string_tuple("approval_blockers", self.approval_blockers),
        )
        object.__setattr__(
            self,
            "summary_points",
            _normalize_string_tuple("summary_points", self.summary_points),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_result(self)
        reject_unsafe_surface_fields("research packet human review brief result", self)
        require_paper_only_flags("research packet human review brief result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_research_packet_human_review_brief_v10_payload(self)


def build_strategy_research_packet_human_review_brief_v10(
    candidate: StrategyResearchPacketHumanReviewBriefV10Input,
) -> StrategyResearchPacketHumanReviewBriefV10Result:
    if type(candidate) is not StrategyResearchPacketHumanReviewBriefV10Input:
        raise ValueError(
            "candidate must be a StrategyResearchPacketHumanReviewBriefV10Input",
        )
    reject_unsafe_surface_fields("research packet human review brief input", candidate)
    require_paper_only_flags("research packet human review brief input", candidate)

    approval_blockers = _approval_blockers(candidate)
    return StrategyResearchPacketHumanReviewBriefV10Result(
        market_id=candidate.market_id,
        decision_readiness=candidate.decision_readiness,
        packet_status=candidate.packet_status,
        top_risks=candidate.top_risks,
        top_evidence_points=candidate.top_evidence_points,
        missing_sections_count=candidate.missing_sections_count,
        cost_adjusted_edge_bps=candidate.cost_adjusted_edge_bps,
        time_to_resolution_minutes=candidate.time_to_resolution_minutes,
        brief_status=_brief_status(candidate, approval_blockers),
        review_questions=_review_questions(candidate),
        approval_blockers=approval_blockers,
        summary_points=_summary_points(candidate),
        reason_codes=_reason_codes(candidate, approval_blockers),
    )


def strategy_research_packet_human_review_brief_v10_payload(
    result: StrategyResearchPacketHumanReviewBriefV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyResearchPacketHumanReviewBriefV10Result:
        raise ValueError(
            "result must be a StrategyResearchPacketHumanReviewBriefV10Result",
        )
    reject_unsafe_surface_fields("research packet human review brief result", result)
    require_paper_only_flags("research packet human review brief result", result)
    payload = json_ready_no_floats(result)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    reject_unsafe_surface_fields("research packet human review brief payload", payload)
    return payload


def _approval_blockers(
    candidate: StrategyResearchPacketHumanReviewBriefV10Input,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if candidate.packet_status != "complete":
        blockers.append(f"Resolve packet status {candidate.packet_status} before approval.")
    if candidate.missing_sections_count > ZERO:
        blockers.append(
            f"Complete {candidate.missing_sections_count} missing research packet sections.",
        )
    if candidate.decision_readiness < READY_THRESHOLD:
        blockers.append("Raise decision readiness to at least 0.700000.")
    if not candidate.top_evidence_points:
        blockers.append("Add at least one evidence point.")
    if candidate.cost_adjusted_edge_bps <= ZERO:
        blockers.append("Cost-adjusted edge must be positive before approval.")
    return tuple(blockers)


def _brief_status(
    candidate: StrategyResearchPacketHumanReviewBriefV10Input,
    approval_blockers: tuple[str, ...],
) -> str:
    if approval_blockers:
        return "blocked"
    if candidate.top_risks:
        return "review_required"
    return "approval_ready"


def _review_questions(
    candidate: StrategyResearchPacketHumanReviewBriefV10Input,
) -> tuple[str, ...]:
    questions: list[str] = []
    if candidate.missing_sections_count > ZERO:
        questions.append("Which missing sections are blocking the research packet?")
    for risk in candidate.top_risks:
        questions.append(f"What evidence resolves the top risk: {risk}?")
    if candidate.cost_adjusted_edge_bps <= ZERO:
        questions.append("Why is the cost-adjusted edge still acceptable after costs?")
    else:
        questions.append(
            "Confirm the evidence still supports the positive cost-adjusted edge.",
        )
    if candidate.time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
        questions.append(
            f"Is {candidate.time_to_resolution_minutes} minutes enough time for manual review?",
        )
    return tuple(questions)


def _summary_points(
    candidate: StrategyResearchPacketHumanReviewBriefV10Input,
) -> tuple[str, ...]:
    points = [
        (
            f"{candidate.market_id} packet {candidate.packet_status} "
            f"with readiness {candidate.decision_readiness}."
        ),
        (
            f"Cost-adjusted edge is {candidate.cost_adjusted_edge_bps} bps "
            f"with {candidate.time_to_resolution_minutes} minutes to resolution."
        ),
    ]
    if candidate.missing_sections_count > ZERO:
        points.append(f"Missing sections: {candidate.missing_sections_count}.")
    elif candidate.top_evidence_points:
        points.append(
            "Evidence highlights: " + "; ".join(candidate.top_evidence_points) + ".",
        )
    else:
        points.append("No evidence points supplied.")

    if candidate.top_risks:
        points.append("Top risks: " + "; ".join(candidate.top_risks) + ".")
    else:
        points.append("No top risks supplied.")
    return tuple(points)


def _reason_codes(
    candidate: StrategyResearchPacketHumanReviewBriefV10Input,
    approval_blockers: tuple[str, ...],
) -> tuple[str, ...]:
    codes = [f"packet_status_{candidate.packet_status}"]
    if candidate.missing_sections_count > ZERO:
        codes.append("missing_sections_present")
    codes.append(
        "decision_readiness_ready"
        if candidate.decision_readiness >= READY_THRESHOLD
        else "decision_readiness_low",
    )
    codes.append(
        "evidence_present" if candidate.top_evidence_points else "evidence_missing",
    )
    codes.append(
        "positive_cost_adjusted_edge"
        if candidate.cost_adjusted_edge_bps > ZERO
        else "nonpositive_cost_adjusted_edge",
    )
    codes.append("risks_present" if candidate.top_risks else "no_top_risks")
    if candidate.time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
        codes.append("near_resolution")
    if approval_blockers:
        codes.append("approval_blocked")
    elif candidate.top_risks:
        codes.append("human_review_required")
    else:
        codes.append("approval_ready")
    return _normalize_reason_codes(tuple(codes))


def _validate_result(result: StrategyResearchPacketHumanReviewBriefV10Result) -> None:
    candidate = StrategyResearchPacketHumanReviewBriefV10Input(
        market_id=result.market_id,
        decision_readiness=result.decision_readiness,
        packet_status=result.packet_status,
        top_risks=result.top_risks,
        top_evidence_points=result.top_evidence_points,
        missing_sections_count=result.missing_sections_count,
        cost_adjusted_edge_bps=result.cost_adjusted_edge_bps,
        time_to_resolution_minutes=result.time_to_resolution_minutes,
    )
    approval_blockers = _approval_blockers(candidate)
    if result.approval_blockers != approval_blockers:
        raise ValueError("approval_blockers must match candidate fields")
    if result.brief_status != _brief_status(candidate, approval_blockers):
        raise ValueError("brief_status must match candidate fields")
    if result.review_questions != _review_questions(candidate):
        raise ValueError("review_questions must match candidate fields")
    if result.summary_points != _summary_points(candidate):
        raise ValueError("summary_points must match candidate fields")
    if result.reason_codes != _reason_codes(candidate, approval_blockers):
        raise ValueError("reason_codes must match candidate fields")


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    normalized = _normalize_string_tuple("reason_codes", values)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in normalized:
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return normalized


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(COUNT_QUANT)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return decimal_value.quantize(SCORE_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical strings")


__all__ = (
    "BRIEF_STATUSES",
    "PACKET_STATUSES",
    "REASON_CODES",
    "StrategyResearchPacketHumanReviewBriefV10Input",
    "StrategyResearchPacketHumanReviewBriefV10Result",
    "build_strategy_research_packet_human_review_brief_v10",
    "strategy_research_packet_human_review_brief_v10_payload",
)
