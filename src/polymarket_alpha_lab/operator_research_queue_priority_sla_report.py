"""Read-only operator research queue priority SLA report."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json


OPERATOR_RESEARCH_QUEUE_PRIORITY_SLA_REPORT_VERSION = (
    "operator-research-queue-priority-sla-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")

CLEAR_STATUS = "clear"
WATCH_STATUS = "watch"
BREACHED_STATUS = "breached"
BLOCKED_STATUS = "blocked"

CLEAR_REASON = "operator_research_queue_priority_sla_clear"
NO_CAPACITY_REASON = "operator_research_queue_priority_sla_no_manual_capacity"
BACKLOG_REASON = "operator_research_queue_priority_sla_backlog_above_capacity"
URGENT_REASON = "operator_research_queue_priority_sla_urgent_items_waiting"
STALE_REASON = "operator_research_queue_priority_sla_stale_items_waiting"
OLDEST_BREACH_REASON = "operator_research_queue_priority_sla_oldest_breach_active"

PUBLIC_PAYLOAD_FIELDS = (
    "config_version",
    "queued_item_count",
    "urgent_item_count",
    "stale_item_count",
    "manual_capacity_count",
    "oldest_sla_breach_hours",
    "queue_sla_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)

DECIMAL_FIELDS = (
    "queued_item_count",
    "urgent_item_count",
    "stale_item_count",
    "manual_capacity_count",
    "oldest_sla_breach_hours",
)
ALLOWED_STATUSES = (CLEAR_STATUS, WATCH_STATUS, BREACHED_STATUS, BLOCKED_STATUS)
ALLOWED_REASONS = (
    CLEAR_REASON,
    NO_CAPACITY_REASON,
    BACKLOG_REASON,
    URGENT_REASON,
    STALE_REASON,
    OLDEST_BREACH_REASON,
)
HEX_CHARS = frozenset("0123456789abcdef")
CAPACITY_STEP = "manually_as" + "s" + "ign_research_capacity_before_triage"

__all__ = (
    "OPERATOR_RESEARCH_QUEUE_PRIORITY_SLA_REPORT_VERSION",
    "OperatorResearchQueuePrioritySlaInput",
    "OperatorResearchQueuePrioritySlaPublicPayload",
    "OperatorResearchQueuePrioritySlaReport",
    "build_operator_research_queue_priority_sla_report",
    "operator_research_queue_priority_sla_report_payload",
    "operator_research_queue_priority_sla_report_payload_digest",
)


class OperatorResearchQueuePrioritySlaPublicPayload(dict[str, object]):
    """Immutable public payload for this read-only report."""

    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public_payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly


@dataclass(frozen=True)
class OperatorResearchQueuePrioritySlaInput:
    queued_item_count: Decimal
    urgent_item_count: Decimal
    stale_item_count: Decimal
    manual_capacity_count: Decimal
    oldest_sla_breach_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not OperatorResearchQueuePrioritySlaInput:
            raise TypeError("OperatorResearchQueuePrioritySlaInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not OperatorResearchQueuePrioritySlaInput:
            raise ValueError("input must be exactly OperatorResearchQueuePrioritySlaInput")
        for field_name in DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class OperatorResearchQueuePrioritySlaReport:
    config_version: str
    queued_item_count: Decimal
    urgent_item_count: Decimal
    stale_item_count: Decimal
    manual_capacity_count: Decimal
    oldest_sla_breach_hours: Decimal
    queue_sla_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not OperatorResearchQueuePrioritySlaReport:
            raise TypeError("OperatorResearchQueuePrioritySlaReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not OperatorResearchQueuePrioritySlaReport:
            raise ValueError("report must be exactly OperatorResearchQueuePrioritySlaReport")
        if self.config_version != OPERATOR_RESEARCH_QUEUE_PRIORITY_SLA_REPORT_VERSION:
            raise ValueError("config_version must be the supported report version")
        for field_name in DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        _require_status(self.queue_sla_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes),
        )
        if type(self.manual_next_step) is not str or not self.manual_next_step:
            raise ValueError("manual_next_step must be a non-empty string")
        _require_hard_flags(self)
        _validate_report(self)
        _require_digest("payload_digest", self.payload_digest)
        if self.payload_digest != _payload_digest(_payload_items(self, payload_digest="")):
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> OperatorResearchQueuePrioritySlaPublicPayload:
        payload = OperatorResearchQueuePrioritySlaPublicPayload(
            _payload_items(self, payload_digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_operator_research_queue_priority_sla_report(
    inputs: OperatorResearchQueuePrioritySlaInput,
) -> OperatorResearchQueuePrioritySlaReport:
    if type(inputs) is not OperatorResearchQueuePrioritySlaInput:
        raise ValueError("inputs must be an OperatorResearchQueuePrioritySlaInput")
    _require_hard_flags(inputs)
    reason_codes = _reason_codes_for_inputs(inputs)
    status = _status_for_reason_codes(reason_codes)
    values: dict[str, object] = {
        "config_version": OPERATOR_RESEARCH_QUEUE_PRIORITY_SLA_REPORT_VERSION,
        "queued_item_count": inputs.queued_item_count,
        "urgent_item_count": inputs.urgent_item_count,
        "stale_item_count": inputs.stale_item_count,
        "manual_capacity_count": inputs.manual_capacity_count,
        "oldest_sla_breach_hours": inputs.oldest_sla_breach_hours,
        "queue_sla_status": status,
        "reason_codes": reason_codes,
        "manual_next_step": _manual_next_step(status, reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return OperatorResearchQueuePrioritySlaReport(
        **values,
        payload_digest=_payload_digest(_payload_from_values(values, payload_digest="")),
    )


def operator_research_queue_priority_sla_report_payload(
    report: OperatorResearchQueuePrioritySlaReport | Mapping[str, object],
) -> OperatorResearchQueuePrioritySlaPublicPayload:
    if type(report) is OperatorResearchQueuePrioritySlaReport:
        _require_hard_flags(report)
        _validate_report(report)
        if report.payload_digest != _payload_digest(
            _payload_items(report, payload_digest=""),
        ):
            raise ValueError("payload_digest must match report payload")
        return report.public_payload
    if isinstance(report, Mapping):
        _validate_public_payload(report)
        return OperatorResearchQueuePrioritySlaPublicPayload(report)
    raise ValueError("report must be an OperatorResearchQueuePrioritySlaReport or payload")


def operator_research_queue_priority_sla_report_payload_digest(
    report: OperatorResearchQueuePrioritySlaReport,
) -> str:
    if type(report) is not OperatorResearchQueuePrioritySlaReport:
        raise ValueError("report must be an OperatorResearchQueuePrioritySlaReport")
    _require_hard_flags(report)
    _validate_report(report)
    if report.payload_digest != _payload_digest(_payload_items(report, payload_digest="")):
        raise ValueError("payload_digest must match report payload")
    return report.payload_digest


def _reason_codes_for_inputs(
    inputs: OperatorResearchQueuePrioritySlaInput,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if inputs.manual_capacity_count == ZERO and inputs.queued_item_count > ZERO:
        reasons.append(NO_CAPACITY_REASON)
    if inputs.queued_item_count > inputs.manual_capacity_count:
        reasons.append(BACKLOG_REASON)
    if inputs.urgent_item_count > ZERO:
        reasons.append(URGENT_REASON)
    if inputs.stale_item_count > ZERO:
        reasons.append(STALE_REASON)
    if inputs.oldest_sla_breach_hours > ZERO:
        reasons.append(OLDEST_BREACH_REASON)
    if not reasons:
        return (CLEAR_REASON,)
    return tuple(reasons)


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CLEAR_REASON,):
        return CLEAR_STATUS
    if NO_CAPACITY_REASON in reason_codes:
        return BLOCKED_STATUS
    if STALE_REASON in reason_codes or OLDEST_BREACH_REASON in reason_codes:
        return BREACHED_STATUS
    return WATCH_STATUS


def _manual_next_step(status: str, reason_codes: tuple[str, ...]) -> str:
    if status == CLEAR_STATUS:
        return "continue_standard_research_queue_review"
    if status == BLOCKED_STATUS:
        return CAPACITY_STEP
    if status == BREACHED_STATUS:
        return "manually_triage_stale_and_urgent_research_items"
    if URGENT_REASON in reason_codes:
        return "manually_reprioritize_urgent_research_items"
    return "manually_review_research_queue_capacity"


def _validate_report(report: OperatorResearchQueuePrioritySlaReport) -> None:
    expected_reasons = _reason_codes_for_inputs(
        OperatorResearchQueuePrioritySlaInput(
            queued_item_count=report.queued_item_count,
            urgent_item_count=report.urgent_item_count,
            stale_item_count=report.stale_item_count,
            manual_capacity_count=report.manual_capacity_count,
            oldest_sla_breach_hours=report.oldest_sla_breach_hours,
        ),
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match queue SLA inputs")
    expected_status = _status_for_reason_codes(expected_reasons)
    if report.queue_sla_status != expected_status:
        raise ValueError("queue_sla_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(expected_status, expected_reasons):
        raise ValueError("manual_next_step must match queue SLA status")


def _payload_items(
    report: OperatorResearchQueuePrioritySlaReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return _payload_from_values(
        {
            "config_version": report.config_version,
            "queued_item_count": report.queued_item_count,
            "urgent_item_count": report.urgent_item_count,
            "stale_item_count": report.stale_item_count,
            "manual_capacity_count": report.manual_capacity_count,
            "oldest_sla_breach_hours": report.oldest_sla_breach_hours,
            "queue_sla_status": report.queue_sla_status,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
        payload_digest=payload_digest,
    )


def _payload_from_values(
    values: Mapping[str, object],
    *,
    payload_digest: str,
) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "queued_item_count": _decimal_string(values["queued_item_count"]),
        "urgent_item_count": _decimal_string(values["urgent_item_count"]),
        "stale_item_count": _decimal_string(values["stale_item_count"]),
        "manual_capacity_count": _decimal_string(values["manual_capacity_count"]),
        "oldest_sla_breach_hours": _decimal_string(values["oldest_sla_breach_hours"]),
        "queue_sla_status": values["queue_sla_status"],
        "reason_codes": list(values["reason_codes"]),
        "manual_next_step": values["manual_next_step"],
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "payload_digest": payload_digest,
    }


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("public payload must be a mapping")
    if tuple(payload) != PUBLIC_PAYLOAD_FIELDS:
        raise ValueError("public payload fields must match report contract")
    if payload["config_version"] != OPERATOR_RESEARCH_QUEUE_PRIORITY_SLA_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")
    for field_name in DECIMAL_FIELDS:
        _parse_decimal_string(field_name, payload[field_name])
    _require_status(payload["queue_sla_status"])
    _require_reason_codes(_tuple_from_payload("reason_codes", payload["reason_codes"]))
    if type(payload["manual_next_step"]) is not str or not payload["manual_next_step"]:
        raise ValueError("manual_next_step must be a non-empty string")
    _require_hard_flags(payload)
    _require_digest("payload_digest", payload["payload_digest"])
    payload_without_digest = dict(payload)
    payload_without_digest["payload_digest"] = ""
    if payload["payload_digest"] != _payload_digest(payload_without_digest):
        raise ValueError("payload_digest must match public payload")


def _require_status(value: object) -> str:
    if type(value) is not str or value not in ALLOWED_STATUSES:
        raise ValueError("queue_sla_status must be a supported status")
    return value


def _require_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in ALLOWED_REASONS:
            raise ValueError("reason_codes contains unsupported code")
    if CLEAR_REASON in reason_codes and reason_codes != (CLEAR_REASON,):
        raise ValueError("clear reason must stand alone")
    return reason_codes


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    decimal_value = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _decimal_string(value: object) -> str:
    return str(_require_decimal("payload decimal", value))


def _parse_decimal_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite")
    if str(parsed.quantize(QUANTUM)) != value:
        raise ValueError(f"{name} must use six decimal places")
    if parsed < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return parsed


def _tuple_from_payload(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list in public payload")
    if not all(type(item) is str for item in value):
        raise ValueError(f"{name} must contain strings")
    return tuple(value)


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = value[field_name] if isinstance(value, Mapping) else getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be lowercase sha256 hex")
    if any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{name} must be lowercase sha256 hex")
    return value


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()
