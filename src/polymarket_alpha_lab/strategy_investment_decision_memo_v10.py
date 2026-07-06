"""Read-only investment decision memo for candidate market research."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from decimal import Decimal
from typing import Any


MEMO_STATUSES = ("ready", "review_required", "blocked")
DECISION_LABELS = (
    "approve_for_paper_research",
    "defer_pending_review",
    "do_not_approve",
)
HUMAN_REVIEW_STATUSES = ("approved", "pending", "rejected")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MIN_SAMPLE_COUNT = Decimal("3.000000")
MIN_LIQUIDITY_DEPTH = Decimal("50.000000")
WATCH_CONFIDENCE_ADJUSTED_EDGE = Decimal("0.010000")
MAX_RISK_SCORE = Decimal("0.500000")
CRITICAL_GAP_SEVERITY = Decimal("0.800000")
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
class StrategyInvestmentDecisionTeamAssignment:
    team_id: str
    lead_analyst: str
    confidence_score: Decimal
    coverage_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", _safe_label("team_id", self.team_id))
        object.__setattr__(
            self,
            "lead_analyst",
            _safe_label("lead_analyst", self.lead_analyst),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _decimal_between_zero_and_one("confidence_score", self.confidence_score),
        )
        object.__setattr__(
            self,
            "coverage_score",
            _decimal_between_zero_and_one("coverage_score", self.coverage_score),
        )
        _require_flags("team_assignment", self)


@dataclass(frozen=True)
class StrategyInvestmentDecisionForecastSummary:
    forecast_probability: Decimal
    market_probability: Decimal
    confidence_score: Decimal
    sample_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "forecast_probability",
            "market_probability",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal_between_zero_and_one(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sample_count",
            _nonnegative_decimal("sample_count", self.sample_count),
        )
        _require_flags("forecast_summary", self)


@dataclass(frozen=True)
class StrategyInvestmentDecisionEdgeSummary:
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


@dataclass(frozen=True)
class StrategyInvestmentDecisionCostSummary:
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


@dataclass(frozen=True)
class StrategyInvestmentDecisionRiskSummary:
    risk_score: Decimal
    max_loss_estimate: Decimal
    correlation_risk: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("risk_score", "max_loss_estimate", "correlation_risk"):
            object.__setattr__(
                self,
                field_name,
                _decimal_between_zero_and_one(field_name, getattr(self, field_name)),
            )
        _require_flags("risk_summary", self)


@dataclass(frozen=True)
class StrategyInvestmentDecisionEvidenceGap:
    gap_code: str
    severity: Decimal
    description: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "gap_code", _safe_label("gap_code", self.gap_code))
        object.__setattr__(
            self,
            "severity",
            _decimal_between_zero_and_one("severity", self.severity),
        )
        object.__setattr__(
            self,
            "description",
            _safe_text("description", self.description),
        )
        _require_flags("evidence_gap", self)


@dataclass(frozen=True)
class StrategyInvestmentDecisionMemoV10:
    market_id: str
    team_assignment: StrategyInvestmentDecisionTeamAssignment
    forecast_summary: StrategyInvestmentDecisionForecastSummary
    edge_summary: StrategyInvestmentDecisionEdgeSummary
    cost_summary: StrategyInvestmentDecisionCostSummary
    risk_summary: StrategyInvestmentDecisionRiskSummary
    evidence_gaps: tuple[StrategyInvestmentDecisionEvidenceGap, ...]
    human_review_status: str
    memo_status: str
    decision_label: str
    approval_blockers: tuple[str, ...]
    summary_bullets: tuple[str, ...]
    reason_codes: tuple[str, ...]
    payload: dict[str, Any] = field(compare=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _safe_label("market_id", self.market_id))
        _require_instance(
            "team_assignment",
            self.team_assignment,
            StrategyInvestmentDecisionTeamAssignment,
        )
        _require_instance(
            "forecast_summary",
            self.forecast_summary,
            StrategyInvestmentDecisionForecastSummary,
        )
        _require_instance(
            "edge_summary",
            self.edge_summary,
            StrategyInvestmentDecisionEdgeSummary,
        )
        _require_instance(
            "cost_summary",
            self.cost_summary,
            StrategyInvestmentDecisionCostSummary,
        )
        _require_instance(
            "risk_summary",
            self.risk_summary,
            StrategyInvestmentDecisionRiskSummary,
        )
        object.__setattr__(
            self,
            "evidence_gaps",
            _normalize_gaps(self.evidence_gaps),
        )
        _require_member(
            "human_review_status",
            self.human_review_status,
            HUMAN_REVIEW_STATUSES,
        )
        _require_member("memo_status", self.memo_status, MEMO_STATUSES)
        _require_member("decision_label", self.decision_label, DECISION_LABELS)
        for field_name in ("approval_blockers", "summary_bullets", "reason_codes"):
            object.__setattr__(
                self,
                field_name,
                _safe_string_tuple(field_name, getattr(self, field_name)),
            )
        _require_flags("memo", self)
        _validate_consistency(self)
        expected_payload = _memo_payload(self)
        if self.payload != expected_payload:
            raise ValueError("payload must match memo fields")
        _reject_unsafe_payload("payload", self.payload)


def build_strategy_investment_decision_memo_v10(
    *,
    market_id: str,
    team_assignment: StrategyInvestmentDecisionTeamAssignment,
    forecast_summary: StrategyInvestmentDecisionForecastSummary,
    edge_summary: StrategyInvestmentDecisionEdgeSummary,
    cost_summary: StrategyInvestmentDecisionCostSummary,
    risk_summary: StrategyInvestmentDecisionRiskSummary,
    evidence_gaps: tuple[StrategyInvestmentDecisionEvidenceGap, ...]
    | list[StrategyInvestmentDecisionEvidenceGap],
    human_review_status: str,
) -> StrategyInvestmentDecisionMemoV10:
    market = _safe_label("market_id", market_id)
    _require_instance(
        "team_assignment",
        team_assignment,
        StrategyInvestmentDecisionTeamAssignment,
    )
    _require_instance(
        "forecast_summary",
        forecast_summary,
        StrategyInvestmentDecisionForecastSummary,
    )
    _require_instance("edge_summary", edge_summary, StrategyInvestmentDecisionEdgeSummary)
    _require_instance("cost_summary", cost_summary, StrategyInvestmentDecisionCostSummary)
    _require_instance("risk_summary", risk_summary, StrategyInvestmentDecisionRiskSummary)
    gaps = _normalize_gaps(evidence_gaps)
    _require_member("human_review_status", human_review_status, HUMAN_REVIEW_STATUSES)
    for label, value in (
        ("team_assignment", team_assignment),
        ("forecast_summary", forecast_summary),
        ("edge_summary", edge_summary),
        ("cost_summary", cost_summary),
        ("risk_summary", risk_summary),
    ):
        _require_flags(label, value)
    blockers = _approval_blockers(
        forecast_summary=forecast_summary,
        edge_summary=edge_summary,
        cost_summary=cost_summary,
        risk_summary=risk_summary,
        evidence_gaps=gaps,
        human_review_status=human_review_status,
    )
    memo_status = _memo_status(blockers)
    decision_label = _decision_label(memo_status)
    reason_codes = _reason_codes(blockers)
    summary_bullets = _summary_bullets(
        market_id=market,
        team_assignment=team_assignment,
        forecast_summary=forecast_summary,
        edge_summary=edge_summary,
        cost_summary=cost_summary,
        risk_summary=risk_summary,
        decision_label=decision_label,
    )
    return _memo_from_fields(
        market_id=market,
        team_assignment=team_assignment,
        forecast_summary=forecast_summary,
        edge_summary=edge_summary,
        cost_summary=cost_summary,
        risk_summary=risk_summary,
        evidence_gaps=gaps,
        human_review_status=human_review_status,
        memo_status=memo_status,
        decision_label=decision_label,
        approval_blockers=blockers,
        summary_bullets=summary_bullets,
        reason_codes=reason_codes,
    )


def strategy_investment_decision_memo_v10_payload(
    memo: StrategyInvestmentDecisionMemoV10 | dict[str, Any],
) -> dict[str, Any]:
    if type(memo) is StrategyInvestmentDecisionMemoV10:
        _require_flags("memo", memo)
        payload = memo.payload
    elif type(memo) is dict:
        payload = memo
    else:
        raise ValueError("memo must be a StrategyInvestmentDecisionMemoV10")
    _require_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("memo payload must be a JSON object")
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


def _memo_from_fields(
    *,
    market_id: str,
    team_assignment: StrategyInvestmentDecisionTeamAssignment,
    forecast_summary: StrategyInvestmentDecisionForecastSummary,
    edge_summary: StrategyInvestmentDecisionEdgeSummary,
    cost_summary: StrategyInvestmentDecisionCostSummary,
    risk_summary: StrategyInvestmentDecisionRiskSummary,
    evidence_gaps: tuple[StrategyInvestmentDecisionEvidenceGap, ...],
    human_review_status: str,
    memo_status: str,
    decision_label: str,
    approval_blockers: tuple[str, ...],
    summary_bullets: tuple[str, ...],
    reason_codes: tuple[str, ...],
) -> StrategyInvestmentDecisionMemoV10:
    payload = _memo_payload_from_parts(
        market_id=market_id,
        team_assignment=team_assignment,
        forecast_summary=forecast_summary,
        edge_summary=edge_summary,
        cost_summary=cost_summary,
        risk_summary=risk_summary,
        evidence_gaps=evidence_gaps,
        human_review_status=human_review_status,
        memo_status=memo_status,
        decision_label=decision_label,
        approval_blockers=approval_blockers,
        summary_bullets=summary_bullets,
        reason_codes=reason_codes,
    )
    return StrategyInvestmentDecisionMemoV10(
        market_id=market_id,
        team_assignment=team_assignment,
        forecast_summary=forecast_summary,
        edge_summary=edge_summary,
        cost_summary=cost_summary,
        risk_summary=risk_summary,
        evidence_gaps=evidence_gaps,
        human_review_status=human_review_status,
        memo_status=memo_status,
        decision_label=decision_label,
        approval_blockers=approval_blockers,
        summary_bullets=summary_bullets,
        reason_codes=reason_codes,
        payload=payload,
    )


def _approval_blockers(
    *,
    forecast_summary: StrategyInvestmentDecisionForecastSummary,
    edge_summary: StrategyInvestmentDecisionEdgeSummary,
    cost_summary: StrategyInvestmentDecisionCostSummary,
    risk_summary: StrategyInvestmentDecisionRiskSummary,
    evidence_gaps: tuple[StrategyInvestmentDecisionEvidenceGap, ...],
    human_review_status: str,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if human_review_status == "pending":
        blockers.append("human_review_pending")
    if human_review_status == "rejected":
        blockers.append("human_review_rejected")
    if forecast_summary.sample_count < MIN_SAMPLE_COUNT:
        blockers.append("insufficient_forecast_sample")
    if edge_summary.expected_value < ZERO:
        blockers.append("negative_expected_value")
    elif edge_summary.confidence_adjusted_edge < WATCH_CONFIDENCE_ADJUSTED_EDGE:
        blockers.append("confidence_adjusted_edge_watch")
    if cost_summary.estimated_cost > edge_summary.expected_value:
        blockers.append("cost_exceeds_expected_value")
    if cost_summary.liquidity_depth < MIN_LIQUIDITY_DEPTH:
        blockers.append("liquidity_below_floor")
    if risk_summary.risk_score > MAX_RISK_SCORE:
        blockers.append("risk_above_threshold")
    if any(gap.severity >= CRITICAL_GAP_SEVERITY for gap in evidence_gaps):
        blockers.append("critical_evidence_gap")
    elif evidence_gaps:
        blockers.append("evidence_gaps_present")
    return tuple(blockers)


def _memo_status(blockers: tuple[str, ...]) -> str:
    blocked_codes = {
        "human_review_rejected",
        "insufficient_forecast_sample",
        "negative_expected_value",
        "cost_exceeds_expected_value",
        "liquidity_below_floor",
        "risk_above_threshold",
        "critical_evidence_gap",
    }
    if any(code in blocked_codes for code in blockers):
        return "blocked"
    if blockers:
        return "review_required"
    return "ready"


def _decision_label(memo_status: str) -> str:
    if memo_status == "ready":
        return "approve_for_paper_research"
    if memo_status == "review_required":
        return "defer_pending_review"
    return "do_not_approve"


def _reason_codes(blockers: tuple[str, ...]) -> tuple[str, ...]:
    if blockers:
        return blockers
    return (
        "human_review_approved",
        "positive_confidence_adjusted_edge",
        "costs_within_expected_value",
        "risk_within_threshold",
        "no_evidence_gaps",
    )


def _summary_bullets(
    *,
    market_id: str,
    team_assignment: StrategyInvestmentDecisionTeamAssignment,
    forecast_summary: StrategyInvestmentDecisionForecastSummary,
    edge_summary: StrategyInvestmentDecisionEdgeSummary,
    cost_summary: StrategyInvestmentDecisionCostSummary,
    risk_summary: StrategyInvestmentDecisionRiskSummary,
    decision_label: str,
) -> tuple[str, ...]:
    return (
        f"{market_id}: {decision_label} for {team_assignment.team_id}.",
        "Forecast probability "
        f"{_decimal_payload(forecast_summary.forecast_probability)} vs market probability "
        f"{_decimal_payload(forecast_summary.market_probability)}.",
        "Confidence-adjusted edge "
        f"{_decimal_payload(edge_summary.confidence_adjusted_edge)} with expected value "
        f"{_decimal_payload(edge_summary.expected_value)}.",
        "Estimated cost "
        f"{_decimal_payload(cost_summary.estimated_cost)} and risk score "
        f"{_decimal_payload(risk_summary.risk_score)}.",
    )


def _memo_payload(report: StrategyInvestmentDecisionMemoV10) -> dict[str, Any]:
    return _memo_payload_from_parts(
        market_id=report.market_id,
        team_assignment=report.team_assignment,
        forecast_summary=report.forecast_summary,
        edge_summary=report.edge_summary,
        cost_summary=report.cost_summary,
        risk_summary=report.risk_summary,
        evidence_gaps=report.evidence_gaps,
        human_review_status=report.human_review_status,
        memo_status=report.memo_status,
        decision_label=report.decision_label,
        approval_blockers=report.approval_blockers,
        summary_bullets=report.summary_bullets,
        reason_codes=report.reason_codes,
    )


def _memo_payload_from_parts(
    *,
    market_id: str,
    team_assignment: StrategyInvestmentDecisionTeamAssignment,
    forecast_summary: StrategyInvestmentDecisionForecastSummary,
    edge_summary: StrategyInvestmentDecisionEdgeSummary,
    cost_summary: StrategyInvestmentDecisionCostSummary,
    risk_summary: StrategyInvestmentDecisionRiskSummary,
    evidence_gaps: tuple[StrategyInvestmentDecisionEvidenceGap, ...],
    human_review_status: str,
    memo_status: str,
    decision_label: str,
    approval_blockers: tuple[str, ...],
    summary_bullets: tuple[str, ...],
    reason_codes: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "market_id": market_id,
        "team_assignment": _json_ready(team_assignment),
        "forecast_summary": _json_ready(forecast_summary),
        "edge_summary": _json_ready(edge_summary),
        "cost_summary": _json_ready(cost_summary),
        "risk_summary": _json_ready(risk_summary),
        "evidence_gaps": _json_ready(evidence_gaps),
        "human_review_status": human_review_status,
        "memo_status": memo_status,
        "decision_label": decision_label,
        "approval_blockers": list(approval_blockers),
        "summary_bullets": list(summary_bullets),
        "reason_codes": list(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_consistency(report: StrategyInvestmentDecisionMemoV10) -> None:
    expected_blockers = _approval_blockers(
        forecast_summary=report.forecast_summary,
        edge_summary=report.edge_summary,
        cost_summary=report.cost_summary,
        risk_summary=report.risk_summary,
        evidence_gaps=report.evidence_gaps,
        human_review_status=report.human_review_status,
    )
    if report.approval_blockers != expected_blockers:
        raise ValueError("approval_blockers must match memo inputs")
    if report.memo_status != _memo_status(expected_blockers):
        raise ValueError("memo_status must match approval blockers")
    if report.decision_label != _decision_label(report.memo_status):
        raise ValueError("decision_label must match memo_status")
    if report.reason_codes != _reason_codes(expected_blockers):
        raise ValueError("reason_codes must match approval blockers")
    if report.summary_bullets != _summary_bullets(
        market_id=report.market_id,
        team_assignment=report.team_assignment,
        forecast_summary=report.forecast_summary,
        edge_summary=report.edge_summary,
        cost_summary=report.cost_summary,
        risk_summary=report.risk_summary,
        decision_label=report.decision_label,
    ):
        raise ValueError("summary_bullets must match memo inputs")


def _normalize_gaps(
    gaps: tuple[StrategyInvestmentDecisionEvidenceGap, ...]
    | list[StrategyInvestmentDecisionEvidenceGap],
) -> tuple[StrategyInvestmentDecisionEvidenceGap, ...]:
    if type(gaps) not in (tuple, list):
        raise ValueError("evidence_gaps must be a tuple or list")
    normalized = tuple(gaps)
    for gap in normalized:
        _require_instance("evidence_gaps", gap, StrategyInvestmentDecisionEvidenceGap)
        _require_flags("evidence_gaps", gap)
    return normalized


def _safe_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    normalized = tuple(value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(_safe_text(field_name, item) for item in normalized)


def _safe_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    _reject_unsafe_text(field_name, value)
    return value


def _safe_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    _reject_unsafe_text(field_name, value)
    return value


def _decimal_between_zero_and_one(field_name: str, value: object) -> Decimal:
    normalized = _finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
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


def _require_instance(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_flags(field_name, value)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


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
        return _decimal_payload(value)
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


def _decimal_payload(value: Decimal) -> str:
    _finite_decimal("JSON Decimal value", value)
    return str(value)


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
            if any(fragment in key.lower() for fragment in UNSAFE_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe field in {label}: {key}")
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
    "DECISION_LABELS",
    "HUMAN_REVIEW_STATUSES",
    "MEMO_STATUSES",
    "StrategyInvestmentDecisionCostSummary",
    "StrategyInvestmentDecisionEdgeSummary",
    "StrategyInvestmentDecisionEvidenceGap",
    "StrategyInvestmentDecisionForecastSummary",
    "StrategyInvestmentDecisionMemoV10",
    "StrategyInvestmentDecisionRiskSummary",
    "StrategyInvestmentDecisionTeamAssignment",
    "build_strategy_investment_decision_memo_v10",
    "strategy_investment_decision_memo_v10_payload",
)
