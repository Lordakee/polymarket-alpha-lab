"""Read-only market decision packet export for candidate research."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from decimal import Decimal
from typing import Any


PACKET_STATUSES = ("ready", "review_required", "blocked")
DECISION_READINESS_LEVELS = (
    "decision_ready",
    "manual_review_required",
    "not_ready",
)
TRIAGE_STATUSES = ("approved", "review_required", "blocked")
COVERAGE_STATUSES = ("met", "partial", "blocked")
SOURCE_QUORUM_STATUSES = ("met", "partial", "missing")
MANUAL_REVIEW_STATUSES = ("approved", "pending", "rejected")
MANUAL_TICKET_STATUSES = ("closed", "open", "blocked")

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
EDGE_WATCH_FLOOR = Decimal("0.010000")
MIN_LIQUIDITY_DEPTH = Decimal("50.000000")
MAX_RISK_SCORE = Decimal("0.500000")
MIN_TEAM_CAPACITY_SCORE = Decimal("0.500000")
MIN_SOURCE_COUNT = Decimal("2.000000")
MIN_EVIDENCE_QUALITY_SCORE = Decimal("0.600000")

EXPORT_SECTIONS = (
    "market_overview",
    "triage_conclusion",
    "edge_assessment",
    "cost_liquidity_assessment",
    "risk_review",
    "team_review",
    "evidence_review",
    "manual_ticket_review",
    "final_readonly_decision",
)

UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "credential",
        "private" " key",
        "key material",
        "secret",
        "wa" "llet",
        "account",
        "balance",
        "trade ticket",
        "exchange mutation",
        "place" " order",
        "cancel" " order",
        "replace" " order",
        "sig" "ning",
    ),
)
UNSAFE_FIELD_FRAGMENTS = frozenset(
    (
        "credential",
        "private" "_key",
        "key_material",
        "secret",
        "wa" "llet",
        "account",
        "balance",
        "trade_ticket",
        "exchange_mutation",
        "place" "_order",
        "cancel" "_order",
        "replace" "_order",
        "sig" "ning",
    ),
)


@dataclass(frozen=True)
class StrategyMarketDecisionTriageSummary:
    triage_status: str
    priority_score: Decimal
    unresolved_issue_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "triage_status",
            _require_member("triage_status", self.triage_status, TRIAGE_STATUSES),
        )
        object.__setattr__(
            self,
            "priority_score",
            _decimal_between_zero_and_one("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "unresolved_issue_count",
            _whole_nonnegative_decimal(
                "unresolved_issue_count",
                self.unresolved_issue_count,
            ),
        )
        _require_flags("triage_summary", self)
        _reject_unsafe_payload("triage_summary", self)


@dataclass(frozen=True)
class StrategyMarketDecisionEdgeSummary:
    probability_edge: Decimal
    expected_value: Decimal
    confidence_adjusted_edge: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "probability_edge",
            "expected_value",
            "confidence_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _finite_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("edge_summary", self)
        _reject_unsafe_payload("edge_summary", self)


@dataclass(frozen=True)
class StrategyMarketDecisionCostSummary:
    estimated_cost: Decimal
    fee_drag: Decimal
    liquidity_depth: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("estimated_cost", "fee_drag", "liquidity_depth"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("cost_summary", self)
        _reject_unsafe_payload("cost_summary", self)


@dataclass(frozen=True)
class StrategyMarketDecisionRiskSummary:
    risk_score: Decimal
    max_loss_estimate: Decimal
    unresolved_risk_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("risk_score", "max_loss_estimate"):
            object.__setattr__(
                self,
                field_name,
                _decimal_between_zero_and_one(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_risk_count",
            _whole_nonnegative_decimal(
                "unresolved_risk_count",
                self.unresolved_risk_count,
            ),
        )
        _require_flags("risk_summary", self)
        _reject_unsafe_payload("risk_summary", self)


@dataclass(frozen=True)
class StrategyMarketDecisionTeamSummary:
    team_id: str
    confidence_score: Decimal
    capacity_score: Decimal
    coverage_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", _safe_label("team_id", self.team_id))
        for field_name in ("confidence_score", "capacity_score"):
            object.__setattr__(
                self,
                field_name,
                _decimal_between_zero_and_one(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "coverage_status",
            _require_member("coverage_status", self.coverage_status, COVERAGE_STATUSES),
        )
        _require_flags("team_summary", self)
        _reject_unsafe_payload("team_summary", self)


@dataclass(frozen=True)
class StrategyMarketDecisionEvidenceSummary:
    source_count: Decimal
    evidence_quality_score: Decimal
    unresolved_evidence_gaps: Decimal
    source_quorum_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_count",
            _whole_nonnegative_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "evidence_quality_score",
            _decimal_between_zero_and_one(
                "evidence_quality_score",
                self.evidence_quality_score,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_evidence_gaps",
            _whole_nonnegative_decimal(
                "unresolved_evidence_gaps",
                self.unresolved_evidence_gaps,
            ),
        )
        object.__setattr__(
            self,
            "source_quorum_status",
            _require_member(
                "source_quorum_status",
                self.source_quorum_status,
                SOURCE_QUORUM_STATUSES,
            ),
        )
        _require_flags("evidence_summary", self)
        _reject_unsafe_payload("evidence_summary", self)


@dataclass(frozen=True)
class StrategyMarketDecisionManualTicketSummary:
    manual_review_status: str
    ticket_status: str
    open_ticket_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "manual_review_status",
            _require_member(
                "manual_review_status",
                self.manual_review_status,
                MANUAL_REVIEW_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "ticket_status",
            _require_member("ticket_status", self.ticket_status, MANUAL_TICKET_STATUSES),
        )
        object.__setattr__(
            self,
            "open_ticket_count",
            _whole_nonnegative_decimal("open_ticket_count", self.open_ticket_count),
        )
        _require_flags("manual_ticket_summary", self)
        _reject_unsafe_payload("manual_ticket_summary", self)


@dataclass(frozen=True)
class StrategyMarketDecisionPacketExportV10:
    market_id: str
    triage_summary: StrategyMarketDecisionTriageSummary
    edge_summary: StrategyMarketDecisionEdgeSummary
    cost_summary: StrategyMarketDecisionCostSummary
    risk_summary: StrategyMarketDecisionRiskSummary
    team_summary: StrategyMarketDecisionTeamSummary
    evidence_summary: StrategyMarketDecisionEvidenceSummary
    manual_ticket_summary: StrategyMarketDecisionManualTicketSummary
    packet_status: str
    decision_readiness: str
    export_sections: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    reason_codes: tuple[str, ...]
    payload: dict[str, Any] = field(compare=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _safe_label("market_id", self.market_id))
        _require_instance(
            "triage_summary",
            self.triage_summary,
            StrategyMarketDecisionTriageSummary,
        )
        _require_instance(
            "edge_summary",
            self.edge_summary,
            StrategyMarketDecisionEdgeSummary,
        )
        _require_instance(
            "cost_summary",
            self.cost_summary,
            StrategyMarketDecisionCostSummary,
        )
        _require_instance(
            "risk_summary",
            self.risk_summary,
            StrategyMarketDecisionRiskSummary,
        )
        _require_instance(
            "team_summary",
            self.team_summary,
            StrategyMarketDecisionTeamSummary,
        )
        _require_instance(
            "evidence_summary",
            self.evidence_summary,
            StrategyMarketDecisionEvidenceSummary,
        )
        _require_instance(
            "manual_ticket_summary",
            self.manual_ticket_summary,
            StrategyMarketDecisionManualTicketSummary,
        )
        object.__setattr__(
            self,
            "packet_status",
            _require_member("packet_status", self.packet_status, PACKET_STATUSES),
        )
        object.__setattr__(
            self,
            "decision_readiness",
            _require_member(
                "decision_readiness",
                self.decision_readiness,
                DECISION_READINESS_LEVELS,
            ),
        )
        for field_name in ("export_sections", "blocking_reasons", "reason_codes"):
            object.__setattr__(
                self,
                field_name,
                _safe_string_tuple(field_name, getattr(self, field_name)),
            )
        _require_flags("packet", self)
        _validate_consistency(self)
        if self.payload != _packet_payload(self):
            raise ValueError("payload must match packet fields")
        _reject_unsafe_payload("payload", self.payload)


def build_strategy_market_decision_packet_export_v10(
    *,
    market_id: str,
    triage_summary: StrategyMarketDecisionTriageSummary,
    edge_summary: StrategyMarketDecisionEdgeSummary,
    cost_summary: StrategyMarketDecisionCostSummary,
    risk_summary: StrategyMarketDecisionRiskSummary,
    team_summary: StrategyMarketDecisionTeamSummary,
    evidence_summary: StrategyMarketDecisionEvidenceSummary,
    manual_ticket_summary: StrategyMarketDecisionManualTicketSummary,
) -> StrategyMarketDecisionPacketExportV10:
    market = _safe_label("market_id", market_id)
    _require_instance(
        "triage_summary",
        triage_summary,
        StrategyMarketDecisionTriageSummary,
    )
    _require_instance("edge_summary", edge_summary, StrategyMarketDecisionEdgeSummary)
    _require_instance("cost_summary", cost_summary, StrategyMarketDecisionCostSummary)
    _require_instance("risk_summary", risk_summary, StrategyMarketDecisionRiskSummary)
    _require_instance("team_summary", team_summary, StrategyMarketDecisionTeamSummary)
    _require_instance(
        "evidence_summary",
        evidence_summary,
        StrategyMarketDecisionEvidenceSummary,
    )
    _require_instance(
        "manual_ticket_summary",
        manual_ticket_summary,
        StrategyMarketDecisionManualTicketSummary,
    )

    blocking_reasons = _blocking_reasons(
        triage_summary=triage_summary,
        edge_summary=edge_summary,
        cost_summary=cost_summary,
        risk_summary=risk_summary,
        team_summary=team_summary,
        evidence_summary=evidence_summary,
        manual_ticket_summary=manual_ticket_summary,
    )
    packet_status = _packet_status(blocking_reasons)
    decision_readiness = _decision_readiness(packet_status)
    reason_codes = _reason_codes(blocking_reasons)
    return _packet_from_fields(
        market_id=market,
        triage_summary=triage_summary,
        edge_summary=edge_summary,
        cost_summary=cost_summary,
        risk_summary=risk_summary,
        team_summary=team_summary,
        evidence_summary=evidence_summary,
        manual_ticket_summary=manual_ticket_summary,
        packet_status=packet_status,
        decision_readiness=decision_readiness,
        export_sections=EXPORT_SECTIONS,
        blocking_reasons=blocking_reasons,
        reason_codes=reason_codes,
    )


def strategy_market_decision_packet_export_v10_payload(
    packet: StrategyMarketDecisionPacketExportV10 | dict[str, Any],
) -> dict[str, Any]:
    if type(packet) is StrategyMarketDecisionPacketExportV10:
        _require_flags("packet", packet)
        _reject_unsafe_payload("packet", packet)
        payload = packet.payload
    elif type(packet) is dict:
        payload = packet
    else:
        raise ValueError("packet must be a StrategyMarketDecisionPacketExportV10")

    _require_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("packet payload must be a JSON object")
    _require_flags("payload", _DictFlags(ready))
    _reject_unsafe_payload("payload", ready)
    return ready


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


def _packet_from_fields(
    *,
    market_id: str,
    triage_summary: StrategyMarketDecisionTriageSummary,
    edge_summary: StrategyMarketDecisionEdgeSummary,
    cost_summary: StrategyMarketDecisionCostSummary,
    risk_summary: StrategyMarketDecisionRiskSummary,
    team_summary: StrategyMarketDecisionTeamSummary,
    evidence_summary: StrategyMarketDecisionEvidenceSummary,
    manual_ticket_summary: StrategyMarketDecisionManualTicketSummary,
    packet_status: str,
    decision_readiness: str,
    export_sections: tuple[str, ...],
    blocking_reasons: tuple[str, ...],
    reason_codes: tuple[str, ...],
) -> StrategyMarketDecisionPacketExportV10:
    payload = _packet_payload_from_parts(
        market_id=market_id,
        triage_summary=triage_summary,
        edge_summary=edge_summary,
        cost_summary=cost_summary,
        risk_summary=risk_summary,
        team_summary=team_summary,
        evidence_summary=evidence_summary,
        manual_ticket_summary=manual_ticket_summary,
        packet_status=packet_status,
        decision_readiness=decision_readiness,
        export_sections=export_sections,
        blocking_reasons=blocking_reasons,
        reason_codes=reason_codes,
    )
    return StrategyMarketDecisionPacketExportV10(
        market_id=market_id,
        triage_summary=triage_summary,
        edge_summary=edge_summary,
        cost_summary=cost_summary,
        risk_summary=risk_summary,
        team_summary=team_summary,
        evidence_summary=evidence_summary,
        manual_ticket_summary=manual_ticket_summary,
        packet_status=packet_status,
        decision_readiness=decision_readiness,
        export_sections=export_sections,
        blocking_reasons=blocking_reasons,
        reason_codes=reason_codes,
        payload=payload,
    )


def _blocking_reasons(
    *,
    triage_summary: StrategyMarketDecisionTriageSummary,
    edge_summary: StrategyMarketDecisionEdgeSummary,
    cost_summary: StrategyMarketDecisionCostSummary,
    risk_summary: StrategyMarketDecisionRiskSummary,
    team_summary: StrategyMarketDecisionTeamSummary,
    evidence_summary: StrategyMarketDecisionEvidenceSummary,
    manual_ticket_summary: StrategyMarketDecisionManualTicketSummary,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if triage_summary.triage_status == "blocked":
        reasons.append("triage_blocked")
    elif triage_summary.triage_status == "review_required":
        reasons.append("triage_review_required")
    if triage_summary.unresolved_issue_count > ZERO:
        reasons.append("triage_unresolved_issues")

    if edge_summary.expected_value <= ZERO:
        reasons.append("nonpositive_expected_value")
    elif edge_summary.confidence_adjusted_edge < EDGE_WATCH_FLOOR:
        reasons.append("confidence_adjusted_edge_watch")

    if cost_summary.estimated_cost > edge_summary.expected_value:
        reasons.append("cost_exceeds_expected_value")
    if cost_summary.liquidity_depth < MIN_LIQUIDITY_DEPTH:
        reasons.append("liquidity_below_floor")

    if risk_summary.risk_score > MAX_RISK_SCORE:
        reasons.append("risk_above_threshold")
    if risk_summary.unresolved_risk_count > ZERO:
        reasons.append("unresolved_risk_review")

    if team_summary.capacity_score < MIN_TEAM_CAPACITY_SCORE:
        reasons.append("team_capacity_below_floor")
    if team_summary.coverage_status == "blocked":
        reasons.append("team_coverage_blocked")
    elif team_summary.coverage_status == "partial":
        reasons.append("team_coverage_partial")

    if evidence_summary.source_count < MIN_SOURCE_COUNT:
        reasons.append("insufficient_source_count")
    if evidence_summary.evidence_quality_score < MIN_EVIDENCE_QUALITY_SCORE:
        reasons.append("evidence_quality_below_floor")
    if evidence_summary.source_quorum_status == "missing":
        reasons.append("source_quorum_missing")
    elif evidence_summary.source_quorum_status == "partial":
        reasons.append("source_quorum_partial")
    if evidence_summary.unresolved_evidence_gaps > ZERO:
        reasons.append("evidence_gaps_present")

    if manual_ticket_summary.manual_review_status == "rejected":
        reasons.append("manual_review_rejected")
    elif manual_ticket_summary.manual_review_status == "pending":
        reasons.append("manual_review_pending")
    if manual_ticket_summary.ticket_status == "blocked":
        reasons.append("manual_ticket_blocked")
    elif (
        manual_ticket_summary.ticket_status == "open"
        or manual_ticket_summary.open_ticket_count > ZERO
    ):
        reasons.append("manual_ticket_open")

    return tuple(reasons)


def _packet_status(blocking_reasons: tuple[str, ...]) -> str:
    hard_blocks = {
        "triage_blocked",
        "nonpositive_expected_value",
        "cost_exceeds_expected_value",
        "liquidity_below_floor",
        "risk_above_threshold",
        "team_capacity_below_floor",
        "team_coverage_blocked",
        "insufficient_source_count",
        "evidence_quality_below_floor",
        "source_quorum_missing",
        "manual_review_rejected",
        "manual_ticket_blocked",
    }
    if any(reason in hard_blocks for reason in blocking_reasons):
        return "blocked"
    if blocking_reasons:
        return "review_required"
    return "ready"


def _decision_readiness(packet_status: str) -> str:
    if packet_status == "ready":
        return "decision_ready"
    if packet_status == "review_required":
        return "manual_review_required"
    return "not_ready"


def _reason_codes(blocking_reasons: tuple[str, ...]) -> tuple[str, ...]:
    if blocking_reasons:
        return blocking_reasons
    return (
        "triage_approved",
        "edge_above_floor",
        "costs_within_expected_value",
        "risk_within_threshold",
        "team_coverage_met",
        "evidence_quorum_met",
        "manual_ticket_clear",
        "readonly_export_ready",
    )


def _packet_payload(packet: StrategyMarketDecisionPacketExportV10) -> dict[str, Any]:
    return _packet_payload_from_parts(
        market_id=packet.market_id,
        triage_summary=packet.triage_summary,
        edge_summary=packet.edge_summary,
        cost_summary=packet.cost_summary,
        risk_summary=packet.risk_summary,
        team_summary=packet.team_summary,
        evidence_summary=packet.evidence_summary,
        manual_ticket_summary=packet.manual_ticket_summary,
        packet_status=packet.packet_status,
        decision_readiness=packet.decision_readiness,
        export_sections=packet.export_sections,
        blocking_reasons=packet.blocking_reasons,
        reason_codes=packet.reason_codes,
    )


def _packet_payload_from_parts(
    *,
    market_id: str,
    triage_summary: StrategyMarketDecisionTriageSummary,
    edge_summary: StrategyMarketDecisionEdgeSummary,
    cost_summary: StrategyMarketDecisionCostSummary,
    risk_summary: StrategyMarketDecisionRiskSummary,
    team_summary: StrategyMarketDecisionTeamSummary,
    evidence_summary: StrategyMarketDecisionEvidenceSummary,
    manual_ticket_summary: StrategyMarketDecisionManualTicketSummary,
    packet_status: str,
    decision_readiness: str,
    export_sections: tuple[str, ...],
    blocking_reasons: tuple[str, ...],
    reason_codes: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "market_id": market_id,
        "triage_summary": _json_ready(triage_summary),
        "edge_summary": _json_ready(edge_summary),
        "cost_summary": _json_ready(cost_summary),
        "risk_summary": _json_ready(risk_summary),
        "team_summary": _json_ready(team_summary),
        "evidence_summary": _json_ready(evidence_summary),
        "manual_ticket_summary": _json_ready(manual_ticket_summary),
        "packet_status": packet_status,
        "decision_readiness": decision_readiness,
        "export_sections": list(export_sections),
        "blocking_reasons": list(blocking_reasons),
        "reason_codes": list(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_consistency(packet: StrategyMarketDecisionPacketExportV10) -> None:
    expected_reasons = _blocking_reasons(
        triage_summary=packet.triage_summary,
        edge_summary=packet.edge_summary,
        cost_summary=packet.cost_summary,
        risk_summary=packet.risk_summary,
        team_summary=packet.team_summary,
        evidence_summary=packet.evidence_summary,
        manual_ticket_summary=packet.manual_ticket_summary,
    )
    if packet.export_sections != EXPORT_SECTIONS:
        raise ValueError("export_sections must match decision packet template")
    if packet.blocking_reasons != expected_reasons:
        raise ValueError("blocking_reasons must match packet summaries")
    expected_status = _packet_status(expected_reasons)
    if packet.packet_status != expected_status:
        raise ValueError("packet_status must match blocking_reasons")
    if packet.decision_readiness != _decision_readiness(expected_status):
        raise ValueError("decision_readiness must match packet_status")
    if packet.reason_codes != _reason_codes(expected_reasons):
        raise ValueError("reason_codes must match blocking_reasons")


def _require_instance(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_flags(field_name, value)
    _reject_unsafe_payload(field_name, value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    label = _safe_label(field_name, value)
    if label not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return label


def _safe_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    normalized = tuple(_safe_label(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _safe_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    _reject_unsafe_text(field_name, value)
    return value


def _decimal_between_zero_and_one(field_name: str, value: object) -> Decimal:
    normalized = _finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool):
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)
        return
    if isinstance(value, Decimal):
        _finite_decimal(label, value)
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal-derived string values")
    if value is None or type(value) is bool:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_payload(label, item)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe value")


__all__ = (
    "COVERAGE_STATUSES",
    "DECISION_READINESS_LEVELS",
    "MANUAL_REVIEW_STATUSES",
    "MANUAL_TICKET_STATUSES",
    "PACKET_STATUSES",
    "SOURCE_QUORUM_STATUSES",
    "TRIAGE_STATUSES",
    "StrategyMarketDecisionCostSummary",
    "StrategyMarketDecisionEdgeSummary",
    "StrategyMarketDecisionEvidenceSummary",
    "StrategyMarketDecisionManualTicketSummary",
    "StrategyMarketDecisionPacketExportV10",
    "StrategyMarketDecisionRiskSummary",
    "StrategyMarketDecisionTeamSummary",
    "StrategyMarketDecisionTriageSummary",
    "build_strategy_market_decision_packet_export_v10",
    "strategy_market_decision_packet_export_v10_payload",
)
