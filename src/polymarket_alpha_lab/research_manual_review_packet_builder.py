"""Safe report-only manual review packet builder."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_MANUAL_REVIEW_PACKET_POLICY_VERSION = (
    "research-manual-review-packet-builder-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PACKET_STATUSES = frozenset(("pass", "watch", "block"))
_EVIDENCE_STATUSES = frozenset(("ready", "limited", "missing"))
_CONFLICT_STATUSES = frozenset(("clear", "minor", "material"))
_COST_STATUSES = frozenset(("low", "elevated", "high"))
_SETTLEMENT_STATUSES = frozenset(("low", "watch", "high"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_REVIEW_SECTIONS = (
    "evidence_state",
    "conflict_review",
    "cost_friction_review",
    "settlement_risk_review",
    "next_research_steps",
    "safe_review_packet",
)
_UNSAFE_PUBLIC_TERMS = (
    "ra" "w",
    "source" "_url",
    "source url",
    "market" "_question",
    "market question",
    "ds" "n",
    "ta" "ble",
    "to" "ken",
    "b" "uy",
    "se" "ll",
    "pos" "ition",
    "rec" "ommend",
    "://" ,
    "http" ":" "//",
    "https" ":" "//",
    "@",
)
_REASON_CODE_SEQUENCE = (
    "evidence_missing",
    "evidence_limited",
    "missing_verified_evidence",
    "insufficient_independent_notes",
    "evidence_quality_watch",
    "evidence_gaps_open",
    "evidence_ready",
    "conflicts_material",
    "conflict_score_above_limit",
    "conflicts_minor",
    "conflicts_unresolved",
    "conflicts_clear",
    "cost_friction_high",
    "cost_friction_above_limit",
    "cost_friction_elevated",
    "cost_issues_open",
    "cost_friction_low",
    "settlement_risk_high",
    "settlement_score_above_limit",
    "settlement_risk_watch",
    "settlement_issues_open",
    "settlement_risk_low",
    "blocking_research_step_open",
    "high_priority_research_step",
    "research_steps_logged",
    "manual_review_packet_ready",
)


@dataclass(frozen=True)
class ResearchManualReviewPacketPolicy:
    policy_version: str = DEFAULT_RESEARCH_MANUAL_REVIEW_PACKET_POLICY_VERSION
    min_verified_item_count: Decimal = Decimal("1.000000")
    min_independent_note_count: Decimal = Decimal("2.000000")
    min_evidence_quality_score: Decimal = Decimal("0.650000")
    max_conflict_severity_score: Decimal = Decimal("0.700000")
    max_total_friction_score: Decimal = Decimal("0.600000")
    max_settlement_risk_score: Decimal = Decimal("0.600000")
    high_priority_step_score: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchManualReviewPacketPolicy:
            raise TypeError("ResearchManualReviewPacketPolicy does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchManualReviewPacketPolicy:
            raise ValueError("policy must be exactly ResearchManualReviewPacketPolicy")
        _require_public_identifier("policy_version", self.policy_version)
        if self.policy_version != DEFAULT_RESEARCH_MANUAL_REVIEW_PACKET_POLICY_VERSION:
            raise ValueError("policy_version must be the supported policy version")
        for field_name in ("min_verified_item_count", "min_independent_note_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_evidence_quality_score",
            "max_conflict_severity_score",
            "max_total_friction_score",
            "max_settlement_risk_score",
            "high_priority_step_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("policy", self)
        _reject_unsafe_public_payload("policy", self)


@dataclass(frozen=True)
class ResearchManualReviewEvidenceState:
    evidence_status: str
    verified_item_count: Decimal
    independent_note_count: Decimal
    evidence_quality_score: Decimal
    unresolved_gap_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchManualReviewEvidenceState:
            raise TypeError("ResearchManualReviewEvidenceState does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchManualReviewEvidenceState:
            raise ValueError("evidence_state must be exactly ResearchManualReviewEvidenceState")
        object.__setattr__(
            self,
            "evidence_status",
            _require_member("evidence_status", self.evidence_status, _EVIDENCE_STATUSES),
        )
        for field_name in (
            "verified_item_count",
            "independent_note_count",
            "unresolved_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_quality_score",
            _require_ratio_decimal("evidence_quality_score", self.evidence_quality_score),
        )
        _require_hard_flags("evidence_state", self)
        _reject_unsafe_public_payload("evidence_state", self)


@dataclass(frozen=True)
class ResearchManualReviewConflictState:
    conflict_status: str
    conflict_count: Decimal
    conflict_severity_score: Decimal
    unresolved_conflict_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchManualReviewConflictState:
            raise TypeError("ResearchManualReviewConflictState does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchManualReviewConflictState:
            raise ValueError("conflict_state must be exactly ResearchManualReviewConflictState")
        object.__setattr__(
            self,
            "conflict_status",
            _require_member("conflict_status", self.conflict_status, _CONFLICT_STATUSES),
        )
        for field_name in ("conflict_count", "unresolved_conflict_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "conflict_severity_score",
            _require_ratio_decimal("conflict_severity_score", self.conflict_severity_score),
        )
        if self.unresolved_conflict_count > self.conflict_count:
            raise ValueError("unresolved_conflict_count must not exceed conflict_count")
        _require_hard_flags("conflict_state", self)
        _reject_unsafe_public_payload("conflict_state", self)


@dataclass(frozen=True)
class ResearchManualReviewCostFrictionState:
    cost_status: str
    fee_friction_score: Decimal
    spread_friction_score: Decimal
    liquidity_friction_score: Decimal
    total_friction_score: Decimal
    unresolved_cost_issue_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchManualReviewCostFrictionState:
            raise TypeError("ResearchManualReviewCostFrictionState does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchManualReviewCostFrictionState:
            raise ValueError(
                "cost_friction_state must be exactly ResearchManualReviewCostFrictionState",
            )
        object.__setattr__(
            self,
            "cost_status",
            _require_member("cost_status", self.cost_status, _COST_STATUSES),
        )
        for field_name in (
            "fee_friction_score",
            "spread_friction_score",
            "liquidity_friction_score",
            "total_friction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_cost_issue_count",
            _require_nonnegative_count_decimal(
                "unresolved_cost_issue_count",
                self.unresolved_cost_issue_count,
            ),
        )
        expected_total = _average(
            (
                self.fee_friction_score,
                self.spread_friction_score,
                self.liquidity_friction_score,
            ),
        )
        if self.total_friction_score != expected_total:
            raise ValueError("total_friction_score must match friction component average")
        _require_hard_flags("cost_friction_state", self)
        _reject_unsafe_public_payload("cost_friction_state", self)


@dataclass(frozen=True)
class ResearchManualReviewSettlementRiskState:
    settlement_status: str
    ambiguity_score: Decimal
    rule_dependency_score: Decimal
    arbiter_dependency_score: Decimal
    settlement_risk_score: Decimal
    unresolved_settlement_issue_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchManualReviewSettlementRiskState:
            raise TypeError("ResearchManualReviewSettlementRiskState does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchManualReviewSettlementRiskState:
            raise ValueError(
                "settlement_risk_state must be exactly ResearchManualReviewSettlementRiskState",
            )
        object.__setattr__(
            self,
            "settlement_status",
            _require_member(
                "settlement_status",
                self.settlement_status,
                _SETTLEMENT_STATUSES,
            ),
        )
        for field_name in (
            "ambiguity_score",
            "rule_dependency_score",
            "arbiter_dependency_score",
            "settlement_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_settlement_issue_count",
            _require_nonnegative_count_decimal(
                "unresolved_settlement_issue_count",
                self.unresolved_settlement_issue_count,
            ),
        )
        expected_risk = _average(
            (
                self.ambiguity_score,
                self.rule_dependency_score,
                self.arbiter_dependency_score,
            ),
        )
        if self.settlement_risk_score != expected_risk:
            raise ValueError("settlement_risk_score must match settlement component average")
        _require_hard_flags("settlement_risk_state", self)
        _reject_unsafe_public_payload("settlement_risk_state", self)


@dataclass(frozen=True)
class ResearchManualReviewNextStep:
    focus_code: str
    priority_score: Decimal
    blocks_review: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchManualReviewNextStep:
            raise TypeError("ResearchManualReviewNextStep does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchManualReviewNextStep:
            raise ValueError("next step must be exactly ResearchManualReviewNextStep")
        _require_public_identifier("focus_code", self.focus_code)
        object.__setattr__(
            self,
            "priority_score",
            _require_ratio_decimal("priority_score", self.priority_score),
        )
        if type(self.blocks_review) is not bool:
            raise ValueError("blocks_review must be a bool")
        _require_hard_flags("next step", self)
        _reject_unsafe_public_payload("next step", self)


@dataclass(frozen=True)
class ResearchManualReviewPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchManualReviewPublicPayloadItem:
            raise TypeError("ResearchManualReviewPublicPayloadItem does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchManualReviewPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly ResearchManualReviewPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_value("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchManualReviewPacket:
    generated_at: datetime
    policy_version: str
    packet_status: str
    evidence_state: ResearchManualReviewEvidenceState
    conflict_state: ResearchManualReviewConflictState
    cost_friction_state: ResearchManualReviewCostFrictionState
    settlement_risk_state: ResearchManualReviewSettlementRiskState
    next_research_steps: tuple[ResearchManualReviewNextStep, ...]
    next_research_step_count: Decimal
    review_sections: tuple[str, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchManualReviewPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchManualReviewPacket:
            raise TypeError("ResearchManualReviewPacket does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchManualReviewPacket:
            raise ValueError("packet must be exactly ResearchManualReviewPacket")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("policy_version", self.policy_version)
        if self.policy_version != DEFAULT_RESEARCH_MANUAL_REVIEW_PACKET_POLICY_VERSION:
            raise ValueError("policy_version must be the supported policy version")
        _require_packet_status("packet_status", self.packet_status)
        _require_instance(
            "evidence_state",
            self.evidence_state,
            ResearchManualReviewEvidenceState,
        )
        _require_instance(
            "conflict_state",
            self.conflict_state,
            ResearchManualReviewConflictState,
        )
        _require_instance(
            "cost_friction_state",
            self.cost_friction_state,
            ResearchManualReviewCostFrictionState,
        )
        _require_instance(
            "settlement_risk_state",
            self.settlement_risk_state,
            ResearchManualReviewSettlementRiskState,
        )
        object.__setattr__(
            self,
            "next_research_steps",
            _normalize_next_steps(self.next_research_steps),
        )
        object.__setattr__(
            self,
            "next_research_step_count",
            _require_nonnegative_count_decimal(
                "next_research_step_count",
                self.next_research_step_count,
            ),
        )
        object.__setattr__(self, "review_sections", _normalize_review_sections(self.review_sections))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_packet_consistency(self)
        _require_hard_flags("packet", self)
        _reject_unsafe_public_payload("packet", self)
        expected_digest = _packet_digest_from_values(_packet_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match packet payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchManualReviewPacket.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_manual_review_packet(
    *,
    generated_at: datetime,
    evidence_state: ResearchManualReviewEvidenceState,
    conflict_state: ResearchManualReviewConflictState,
    cost_friction_state: ResearchManualReviewCostFrictionState,
    settlement_risk_state: ResearchManualReviewSettlementRiskState,
    next_research_steps: Sequence[ResearchManualReviewNextStep] = (),
    public_payload: Sequence[ResearchManualReviewPublicPayloadItem] = (),
    policy: ResearchManualReviewPacketPolicy | None = None,
) -> ResearchManualReviewPacket:
    if policy is None:
        policy = ResearchManualReviewPacketPolicy()
    if type(policy) is not ResearchManualReviewPacketPolicy:
        raise ValueError("policy must be a ResearchManualReviewPacketPolicy")
    generated_at = _as_utc("generated_at", generated_at)
    _require_instance("evidence_state", evidence_state, ResearchManualReviewEvidenceState)
    _require_instance("conflict_state", conflict_state, ResearchManualReviewConflictState)
    _require_instance(
        "cost_friction_state",
        cost_friction_state,
        ResearchManualReviewCostFrictionState,
    )
    _require_instance(
        "settlement_risk_state",
        settlement_risk_state,
        ResearchManualReviewSettlementRiskState,
    )
    steps = _normalize_next_steps(next_research_steps)
    payload_items = _normalize_public_payload(public_payload)
    reason_codes = _reason_codes(
        policy=policy,
        evidence_state=evidence_state,
        conflict_state=conflict_state,
        cost_friction_state=cost_friction_state,
        settlement_risk_state=settlement_risk_state,
        next_research_steps=steps,
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "policy_version": policy.policy_version,
        "packet_status": _packet_status(reason_codes),
        "evidence_state": evidence_state,
        "conflict_state": conflict_state,
        "cost_friction_state": cost_friction_state,
        "settlement_risk_state": settlement_risk_state,
        "next_research_steps": steps,
        "next_research_step_count": _decimal_count(len(steps)),
        "review_sections": _REVIEW_SECTIONS,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchManualReviewPacket(
        **values,
        derived_validation_digest=_packet_digest_from_values(values),
    )


def _reason_codes(
    *,
    policy: ResearchManualReviewPacketPolicy,
    evidence_state: ResearchManualReviewEvidenceState,
    conflict_state: ResearchManualReviewConflictState,
    cost_friction_state: ResearchManualReviewCostFrictionState,
    settlement_risk_state: ResearchManualReviewSettlementRiskState,
    next_research_steps: tuple[ResearchManualReviewNextStep, ...],
) -> tuple[str, ...]:
    codes: list[str] = []

    if evidence_state.evidence_status == "missing":
        codes.append("evidence_missing")
    elif evidence_state.evidence_status == "limited":
        codes.append("evidence_limited")
    if evidence_state.verified_item_count < policy.min_verified_item_count:
        codes.append("missing_verified_evidence")
    if evidence_state.independent_note_count < policy.min_independent_note_count:
        codes.append("insufficient_independent_notes")
    if (
        evidence_state.verified_item_count >= policy.min_verified_item_count
        and evidence_state.evidence_quality_score < policy.min_evidence_quality_score
    ):
        codes.append("evidence_quality_watch")
    if evidence_state.unresolved_gap_count > _ZERO:
        codes.append("evidence_gaps_open")
    if (
        evidence_state.evidence_status == "ready"
        and evidence_state.verified_item_count >= policy.min_verified_item_count
        and evidence_state.independent_note_count >= policy.min_independent_note_count
        and evidence_state.evidence_quality_score >= policy.min_evidence_quality_score
        and evidence_state.unresolved_gap_count == _ZERO
    ):
        codes.append("evidence_ready")

    if conflict_state.conflict_status == "material":
        codes.append("conflicts_material")
    if conflict_state.conflict_severity_score > policy.max_conflict_severity_score:
        codes.append("conflict_score_above_limit")
    elif conflict_state.conflict_status == "minor":
        codes.append("conflicts_minor")
    if conflict_state.unresolved_conflict_count > _ZERO:
        codes.append("conflicts_unresolved")
    if (
        conflict_state.conflict_status == "clear"
        and conflict_state.conflict_count == _ZERO
        and conflict_state.unresolved_conflict_count == _ZERO
        and conflict_state.conflict_severity_score <= policy.max_conflict_severity_score
    ):
        codes.append("conflicts_clear")

    if cost_friction_state.cost_status == "high":
        codes.append("cost_friction_high")
    if cost_friction_state.total_friction_score > policy.max_total_friction_score:
        codes.append("cost_friction_above_limit")
    elif cost_friction_state.cost_status == "elevated":
        codes.append("cost_friction_elevated")
    if cost_friction_state.unresolved_cost_issue_count > _ZERO:
        codes.append("cost_issues_open")
    if (
        cost_friction_state.cost_status == "low"
        and cost_friction_state.total_friction_score <= policy.max_total_friction_score
        and cost_friction_state.unresolved_cost_issue_count == _ZERO
    ):
        codes.append("cost_friction_low")

    if settlement_risk_state.settlement_status == "high":
        codes.append("settlement_risk_high")
    if settlement_risk_state.settlement_risk_score > policy.max_settlement_risk_score:
        codes.append("settlement_score_above_limit")
    elif settlement_risk_state.settlement_status == "watch":
        codes.append("settlement_risk_watch")
    if settlement_risk_state.unresolved_settlement_issue_count > _ZERO:
        codes.append("settlement_issues_open")
    if (
        settlement_risk_state.settlement_status == "low"
        and settlement_risk_state.settlement_risk_score <= policy.max_settlement_risk_score
        and settlement_risk_state.unresolved_settlement_issue_count == _ZERO
    ):
        codes.append("settlement_risk_low")

    if any(step.blocks_review for step in next_research_steps):
        codes.append("blocking_research_step_open")
    elif any(step.priority_score >= policy.high_priority_step_score for step in next_research_steps):
        codes.append("high_priority_research_step")
    elif next_research_steps:
        codes.append("research_steps_logged")

    if not codes:
        return ("manual_review_packet_ready",)
    normalized = _normalize_reason_codes(tuple(codes))
    pass_codes = (
        "evidence_ready",
        "conflicts_clear",
        "cost_friction_low",
        "settlement_risk_low",
        "research_steps_logged",
    )
    if normalized == pass_codes or normalized == pass_codes[:-1]:
        normalized = (*normalized, "manual_review_packet_ready")
    return normalized


def _packet_status(reason_codes: tuple[str, ...]) -> str:
    block_codes = frozenset(
        (
            "evidence_missing",
            "missing_verified_evidence",
            "insufficient_independent_notes",
            "conflicts_material",
            "conflict_score_above_limit",
            "cost_friction_high",
            "cost_friction_above_limit",
            "settlement_risk_high",
            "settlement_score_above_limit",
            "blocking_research_step_open",
        ),
    )
    watch_codes = frozenset(
        (
            "evidence_limited",
            "evidence_quality_watch",
            "evidence_gaps_open",
            "conflicts_minor",
            "conflicts_unresolved",
            "cost_friction_elevated",
            "cost_issues_open",
            "settlement_risk_watch",
            "settlement_issues_open",
            "high_priority_research_step",
        ),
    )
    if any(code in block_codes for code in reason_codes):
        return "block"
    if any(code in watch_codes for code in reason_codes):
        return "watch"
    return "pass"


def _validate_packet_consistency(packet: ResearchManualReviewPacket) -> None:
    if packet.next_research_step_count != _decimal_count(len(packet.next_research_steps)):
        raise ValueError("next_research_step_count must match next_research_steps")
    if packet.review_sections != _REVIEW_SECTIONS:
        raise ValueError("review_sections must match manual review packet template")
    policy = ResearchManualReviewPacketPolicy(policy_version=packet.policy_version)
    expected_codes = _reason_codes(
        policy=policy,
        evidence_state=packet.evidence_state,
        conflict_state=packet.conflict_state,
        cost_friction_state=packet.cost_friction_state,
        settlement_risk_state=packet.settlement_risk_state,
        next_research_steps=packet.next_research_steps,
    )
    if packet.reason_codes != expected_codes:
        raise ValueError("reason_codes must match packet state")
    if packet.packet_status != _packet_status(expected_codes):
        raise ValueError("packet_status must match reason_codes")


def _require_instance(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_hard_flags(field_name, value)
    _reject_unsafe_public_payload(field_name, value)


def _normalize_next_steps(
    next_research_steps: Sequence[ResearchManualReviewNextStep],
) -> tuple[ResearchManualReviewNextStep, ...]:
    if isinstance(next_research_steps, (str, bytes)) or not isinstance(
        next_research_steps,
        Sequence,
    ):
        raise ValueError("next_research_steps must be a sequence")
    normalized: list[ResearchManualReviewNextStep] = []
    for item in next_research_steps:
        if type(item) is not ResearchManualReviewNextStep:
            raise ValueError("next_research_steps items must be ResearchManualReviewNextStep")
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: (item.blocks_review, item.focus_code)))


def _normalize_public_payload(
    public_payload: Sequence[ResearchManualReviewPublicPayloadItem],
) -> tuple[ResearchManualReviewPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchManualReviewPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchManualReviewPublicPayloadItem:
            raise ValueError(
                "public_payload items must be ResearchManualReviewPublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_review_sections(review_sections: Sequence[str]) -> tuple[str, ...]:
    if isinstance(review_sections, (str, bytes)) or not isinstance(review_sections, Sequence):
        raise ValueError("review_sections must be a sequence")
    normalized = tuple(_require_public_identifier("review_section", item) for item in review_sections)
    if normalized != _REVIEW_SECTIONS:
        raise ValueError("review_sections must match manual review packet template")
    return normalized


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(code for code in _REASON_CODE_SEQUENCE if code in normalized)


def _require_member(field_name: str, value: object, allowed_values: frozenset[str]) -> str:
    label = _require_public_identifier(field_name, value)
    if label not in allowed_values:
        raise ValueError(f"{field_name} must be supported")
    return label


def _require_packet_status(field_name: str, value: object) -> str:
    label = _require_public_identifier(field_name, value)
    if label not in _PACKET_STATUSES:
        raise ValueError(f"{field_name} must be supported")
    return label


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_value(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public value")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _packet_values_without_digest(packet: ResearchManualReviewPacket) -> dict[str, object]:
    values = asdict(packet)
    values.pop("derived_validation_digest", None)
    return values


def _packet_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_RESEARCH_MANUAL_REVIEW_PACKET_POLICY_VERSION",
    "ResearchManualReviewConflictState",
    "ResearchManualReviewCostFrictionState",
    "ResearchManualReviewEvidenceState",
    "ResearchManualReviewNextStep",
    "ResearchManualReviewPacket",
    "ResearchManualReviewPacketPolicy",
    "ResearchManualReviewPublicPayloadItem",
    "ResearchManualReviewSettlementRiskState",
    "build_research_manual_review_packet",
)
