"""Read-only research packet to final recommendation decision trace v10."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from typing import Any


CONFIG_VERSION = "strategy-research-packet-decision-trace-v10"

DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")

TRACE_POINTS = (
    "triage",
    "packet",
    "edge",
    "risk",
    "budget",
    "decision",
    "review",
)
TRACE_STATUSES = ("recommendation_ready", "review_required", "blocked")
STEP_STATUSES = ("complete", "missing", "blocked")

TRIAGE_STATUSES = ("approved", "review_required", "blocked")
PACKET_STATUSES = ("ready", "review_required", "blocked")
EDGE_STATUSES = ("positive", "watch", "negative", "blocked")
RISK_STATUSES = ("cleared", "review_required", "blocked")
BUDGET_STATUSES = ("available", "constrained", "blocked")
DECISION_STATUSES = ("recommended", "watchlist", "rejected", "blocked")
REVIEW_STATUSES = ("approved", "pending", "rejected", "blocked")

TRACE_SEQUENCE = {
    "triage": Decimal("1.000000"),
    "packet": Decimal("2.000000"),
    "edge": Decimal("3.000000"),
    "risk": Decimal("4.000000"),
    "budget": Decimal("5.000000"),
    "decision": Decimal("6.000000"),
    "review": Decimal("7.000000"),
}
COMPLETE_STATUSES = {
    "triage": "approved",
    "packet": "ready",
    "edge": "positive",
    "risk": "cleared",
    "budget": "available",
    "decision": "recommended",
    "review": "approved",
}
BLOCKED_STATUSES = {
    "triage": frozenset(("blocked",)),
    "packet": frozenset(("blocked",)),
    "edge": frozenset(("negative", "blocked")),
    "risk": frozenset(("blocked",)),
    "budget": frozenset(("blocked",)),
    "decision": frozenset(("rejected", "blocked")),
    "review": frozenset(("rejected", "blocked")),
}

PAYLOAD_FIELDS = (
    "config_version",
    "market_id",
    "trace_status",
    "trace_steps",
    "missing_trace_points",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
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
class ResearchPacketDecisionTraceV10Input:
    market_id: str
    triage_status: str
    packet_status: str
    edge_status: str
    risk_status: str
    budget_status: str
    decision_status: str
    review_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketDecisionTraceV10Input:
            raise ValueError("input must be exactly ResearchPacketDecisionTraceV10Input")
        object.__setattr__(self, "market_id", _safe_label("market_id", self.market_id))
        object.__setattr__(
            self,
            "triage_status",
            _require_member("triage_status", self.triage_status, TRIAGE_STATUSES),
        )
        object.__setattr__(
            self,
            "packet_status",
            _require_member("packet_status", self.packet_status, PACKET_STATUSES),
        )
        object.__setattr__(
            self,
            "edge_status",
            _require_member("edge_status", self.edge_status, EDGE_STATUSES),
        )
        object.__setattr__(
            self,
            "risk_status",
            _require_member("risk_status", self.risk_status, RISK_STATUSES),
        )
        object.__setattr__(
            self,
            "budget_status",
            _require_member("budget_status", self.budget_status, BUDGET_STATUSES),
        )
        object.__setattr__(
            self,
            "decision_status",
            _require_member("decision_status", self.decision_status, DECISION_STATUSES),
        )
        object.__setattr__(
            self,
            "review_status",
            _require_member("review_status", self.review_status, REVIEW_STATUSES),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_payload("input", self)


@dataclass(frozen=True)
class ResearchPacketDecisionTraceV10Step:
    sequence: Decimal
    trace_point: str
    input_status: str
    step_status: str
    reason_code: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketDecisionTraceV10Step:
            raise ValueError("step must be exactly ResearchPacketDecisionTraceV10Step")
        object.__setattr__(
            self,
            "sequence",
            _normalize_positive_whole_decimal("sequence", self.sequence),
        )
        object.__setattr__(
            self,
            "trace_point",
            _require_member("trace_point", self.trace_point, TRACE_POINTS),
        )
        object.__setattr__(
            self,
            "input_status",
            _safe_label("input_status", self.input_status),
        )
        object.__setattr__(
            self,
            "step_status",
            _require_member("step_status", self.step_status, STEP_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_code",
            _safe_label("reason_code", self.reason_code),
        )
        _validate_step(self)
        _require_hard_flags("step", self)
        _reject_unsafe_payload("step", self)


@dataclass(frozen=True)
class ResearchPacketDecisionTraceV10Report:
    market_id: str
    trace_status: str
    trace_steps: tuple[ResearchPacketDecisionTraceV10Step, ...]
    missing_trace_points: tuple[str, ...]
    reason_codes: tuple[str, ...]
    config_version: str = CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketDecisionTraceV10Report:
            raise ValueError("report must be exactly ResearchPacketDecisionTraceV10Report")
        object.__setattr__(self, "market_id", _safe_label("market_id", self.market_id))
        object.__setattr__(
            self,
            "trace_status",
            _require_member("trace_status", self.trace_status, TRACE_STATUSES),
        )
        object.__setattr__(
            self,
            "trace_steps",
            _normalize_trace_steps(self.trace_steps),
        )
        object.__setattr__(
            self,
            "missing_trace_points",
            _safe_string_tuple("missing_trace_points", self.missing_trace_points),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _safe_string_tuple("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "config_version",
            _safe_label("config_version", self.config_version),
        )
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_payload("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_research_packet_decision_trace_v10_payload(self)


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


def strategy_research_packet_decision_trace_v10(
    value: ResearchPacketDecisionTraceV10Input,
) -> ResearchPacketDecisionTraceV10Report:
    if type(value) is not ResearchPacketDecisionTraceV10Input:
        raise ValueError("value must be a ResearchPacketDecisionTraceV10Input")
    _require_hard_flags("input", value)
    _reject_unsafe_payload("input", value)
    trace_steps = _trace_steps(value)
    trace_status = _trace_status(trace_steps)
    missing_trace_points = _missing_trace_points(trace_steps)
    return ResearchPacketDecisionTraceV10Report(
        market_id=value.market_id,
        trace_status=trace_status,
        trace_steps=trace_steps,
        missing_trace_points=missing_trace_points,
        reason_codes=_reason_codes(trace_steps, trace_status),
    )


def strategy_research_packet_decision_trace_v10_payload(
    report: ResearchPacketDecisionTraceV10Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketDecisionTraceV10Report:
        _require_hard_flags("report", report)
        _reject_unsafe_payload("report", report)
        payload: Any = _report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _validate_payload_fields(report)
        _reject_unsafe_payload("payload", report)
        payload = report
    else:
        raise ValueError("report must be a ResearchPacketDecisionTraceV10Report")

    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(ready))
    _validate_payload_fields(ready)
    _reject_unsafe_payload("payload", ready)
    return ready


def _trace_steps(
    value: ResearchPacketDecisionTraceV10Input,
) -> tuple[ResearchPacketDecisionTraceV10Step, ...]:
    statuses = {
        "triage": value.triage_status,
        "packet": value.packet_status,
        "edge": value.edge_status,
        "risk": value.risk_status,
        "budget": value.budget_status,
        "decision": value.decision_status,
        "review": value.review_status,
    }
    return tuple(
        _trace_step(trace_point, statuses[trace_point])
        for trace_point in TRACE_POINTS
    )


def _trace_step(trace_point: str, input_status: str) -> ResearchPacketDecisionTraceV10Step:
    return ResearchPacketDecisionTraceV10Step(
        sequence=TRACE_SEQUENCE[trace_point],
        trace_point=trace_point,
        input_status=input_status,
        step_status=_step_status(trace_point, input_status),
        reason_code=_reason_code(trace_point, input_status),
    )


def _step_status(trace_point: str, input_status: str) -> str:
    if input_status == COMPLETE_STATUSES[trace_point]:
        return "complete"
    if input_status in BLOCKED_STATUSES[trace_point]:
        return "blocked"
    return "missing"


def _reason_code(trace_point: str, input_status: str) -> str:
    return f"{trace_point}_{input_status}"


def _trace_status(
    trace_steps: tuple[ResearchPacketDecisionTraceV10Step, ...],
) -> str:
    if any(step.step_status == "blocked" for step in trace_steps):
        return "blocked"
    if any(step.step_status == "missing" for step in trace_steps):
        return "review_required"
    return "recommendation_ready"


def _missing_trace_points(
    trace_steps: tuple[ResearchPacketDecisionTraceV10Step, ...],
) -> tuple[str, ...]:
    return tuple(
        step.reason_code
        for step in trace_steps
        if step.step_status != "complete"
    )


def _reason_codes(
    trace_steps: tuple[ResearchPacketDecisionTraceV10Step, ...],
    trace_status: str,
) -> tuple[str, ...]:
    step_reason_codes = tuple(step.reason_code for step in trace_steps)
    if trace_status == "recommendation_ready":
        return step_reason_codes + (
            "trace_complete",
            "readonly_recommendation_ready",
        )
    if trace_status == "blocked":
        return step_reason_codes + ("trace_blocked",)
    return step_reason_codes + ("trace_review_required",)


def _validate_step(step: ResearchPacketDecisionTraceV10Step) -> None:
    if step.sequence != TRACE_SEQUENCE[step.trace_point]:
        raise ValueError("sequence must match trace_point")
    allowed_statuses = _statuses_for_trace_point(step.trace_point)
    if step.input_status not in allowed_statuses:
        raise ValueError("input_status must match trace_point")
    if step.step_status != _step_status(step.trace_point, step.input_status):
        raise ValueError("step_status must match input_status")
    if step.reason_code != _reason_code(step.trace_point, step.input_status):
        raise ValueError("reason_code must match trace_point and input_status")


def _validate_report(report: ResearchPacketDecisionTraceV10Report) -> None:
    if tuple(step.trace_point for step in report.trace_steps) != TRACE_POINTS:
        raise ValueError("trace_steps must match trace template")
    expected_trace_status = _trace_status(report.trace_steps)
    if report.trace_status != expected_trace_status:
        raise ValueError("trace_status must match trace_steps")
    if report.missing_trace_points != _missing_trace_points(report.trace_steps):
        raise ValueError("missing_trace_points must match trace_steps")
    if report.reason_codes != _reason_codes(report.trace_steps, expected_trace_status):
        raise ValueError("reason_codes must match trace_steps")


def _report_payload(report: ResearchPacketDecisionTraceV10Report) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "market_id": report.market_id,
        "trace_status": report.trace_status,
        "trace_steps": report.trace_steps,
        "missing_trace_points": report.missing_trace_points,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.quantize(DECIMAL_QUANTUM))
    if type(value) is bool or value is None:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_trace_steps(
    value: object,
) -> tuple[ResearchPacketDecisionTraceV10Step, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("trace_steps must be a tuple or list")
    trace_steps = tuple(value)
    if len(trace_steps) != len(TRACE_POINTS):
        raise ValueError("trace_steps must include every trace point")
    for step in trace_steps:
        if type(step) is not ResearchPacketDecisionTraceV10Step:
            raise ValueError("trace_steps must contain ResearchPacketDecisionTraceV10Step")
        _require_hard_flags("step", step)
    return trace_steps


def _safe_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    normalized = tuple(_safe_label(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _finite_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value().quantize(DECIMAL_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.quantize(DECIMAL_QUANTUM)


def _finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(DECIMAL_QUANTUM)


def _statuses_for_trace_point(trace_point: str) -> tuple[str, ...]:
    if trace_point == "triage":
        return TRIAGE_STATUSES
    if trace_point == "packet":
        return PACKET_STATUSES
    if trace_point == "edge":
        return EDGE_STATUSES
    if trace_point == "risk":
        return RISK_STATUSES
    if trace_point == "budget":
        return BUDGET_STATUSES
    if trace_point == "decision":
        return DECISION_STATUSES
    if trace_point == "review":
        return REVIEW_STATUSES
    raise ValueError("trace_point must be supported")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    label = _safe_label(field_name, value)
    if label not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return label


def _safe_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(field_name, value)
    return value


def _validate_payload_fields(payload: dict[str, Any]) -> None:
    for key in payload:
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        if key not in PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        if label == "payload":
            raise ValueError("payload paper_only must be True")
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        if label == "payload":
            raise ValueError("payload report_only must be True")
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        if label == "payload":
            raise ValueError("payload readonly must be True")
        raise ValueError(f"{label} must be readonly")


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
        raise ValueError(f"{label} must use Decimal values")
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
    "BUDGET_STATUSES",
    "CONFIG_VERSION",
    "DECISION_STATUSES",
    "EDGE_STATUSES",
    "PACKET_STATUSES",
    "REVIEW_STATUSES",
    "RISK_STATUSES",
    "STEP_STATUSES",
    "TRACE_POINTS",
    "TRACE_STATUSES",
    "TRIAGE_STATUSES",
    "ResearchPacketDecisionTraceV10Input",
    "ResearchPacketDecisionTraceV10Report",
    "ResearchPacketDecisionTraceV10Step",
    "strategy_research_packet_decision_trace_v10",
    "strategy_research_packet_decision_trace_v10_payload",
)
