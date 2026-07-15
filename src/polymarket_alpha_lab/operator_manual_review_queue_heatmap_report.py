"""Read-only Phase 1 report for manual review queue heatmap readiness."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Mapping


__all__ = (
    "OperatorManualReviewQueueHeatmapInput",
    "OperatorManualReviewQueueHeatmapReport",
    "build_operator_manual_review_queue_heatmap_report",
    "operator_manual_review_queue_heatmap_report_payload_digest",
    "validate_operator_manual_review_queue_heatmap_public_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")

READY_STATUS = "ready"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"

READY_REASON = "manual_review_queue_heatmap_ready"
CAPACITY_REASON = "manual_capacity_below_queue_count"
BLOCKED_REASON = "blocked_items_present"
URGENT_REASON = "urgent_items_need_manual_triage"
PACKET_REASON = "ready_packets_below_queue_count"
EMPTY_REASON = "manual_review_queue_empty"

READY_NEXT_STEP = "continue_manual_review_from_ready_packet_queue"
BLOCKED_NEXT_STEP = "resolve_manual_review_queue_blockers_before_triage"
URGENT_NEXT_STEP = "triage_urgent_manual_review_items_first"
PACKET_NEXT_STEP = "complete_ready_packets_before_manual_review"
EMPTY_NEXT_STEP = "wait_for_manual_review_queue_items"

COUNT_FIELDS = (
    "queue_item_count",
    "urgent_item_count",
    "blocked_item_count",
    "ready_packet_count",
    "manual_capacity_count",
)
PAYLOAD_FIELDS = (
    "queue_item_count",
    "urgent_item_count",
    "blocked_item_count",
    "ready_packet_count",
    "manual_capacity_count",
    "heatmap_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
ALLOWED_REASONS = (
    CAPACITY_REASON,
    BLOCKED_REASON,
    URGENT_REASON,
    PACKET_REASON,
    EMPTY_REASON,
    READY_REASON,
)
ALLOWED_STATUS = (READY_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ALLOWED_NEXT_STEPS = (
    READY_NEXT_STEP,
    BLOCKED_NEXT_STEP,
    URGENT_NEXT_STEP,
    PACKET_NEXT_STEP,
    EMPTY_NEXT_STEP,
)


class _NoSubclassing:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _NoSubclassing and issubclass(base, _NoSubclassing):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class OperatorManualReviewQueueHeatmapInput(_NoSubclassing):
    queue_item_count: Decimal
    urgent_item_count: Decimal
    blocked_item_count: Decimal
    ready_packet_count: Decimal
    manual_capacity_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, OperatorManualReviewQueueHeatmapInput, "heatmap input")
        for field_name in COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class OperatorManualReviewQueueHeatmapReport(_NoSubclassing):
    queue_item_count: Decimal
    urgent_item_count: Decimal
    blocked_item_count: Decimal
    ready_packet_count: Decimal
    manual_capacity_count: Decimal
    heatmap_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, OperatorManualReviewQueueHeatmapReport, "heatmap report")
        for field_name in COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_member("heatmap_status", self.heatmap_status, ALLOWED_STATUS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_member("manual_next_step", self.manual_next_step, ALLOWED_NEXT_STEPS)
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags(self)
        _validate_report(self)
        if self.payload_digest != _digest_payload(_payload_without_digest(self)):
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> dict[str, object]:
        return _report_to_payload(self)


def build_operator_manual_review_queue_heatmap_report(
    queue: OperatorManualReviewQueueHeatmapInput,
) -> OperatorManualReviewQueueHeatmapReport:
    if type(queue) is not OperatorManualReviewQueueHeatmapInput:
        raise ValueError("queue must be an OperatorManualReviewQueueHeatmapInput")
    _require_hard_flags(queue)

    reason_codes = _derived_reason_codes(
        queue_item_count=queue.queue_item_count,
        urgent_item_count=queue.urgent_item_count,
        blocked_item_count=queue.blocked_item_count,
        ready_packet_count=queue.ready_packet_count,
        manual_capacity_count=queue.manual_capacity_count,
    )
    heatmap_status = _status_for_reasons(reason_codes)
    manual_next_step = _next_step_for_reasons(reason_codes)
    values: dict[str, object] = {
        "queue_item_count": queue.queue_item_count,
        "urgent_item_count": queue.urgent_item_count,
        "blocked_item_count": queue.blocked_item_count,
        "ready_packet_count": queue.ready_packet_count,
        "manual_capacity_count": queue.manual_capacity_count,
        "heatmap_status": heatmap_status,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return OperatorManualReviewQueueHeatmapReport(
        **values,
        payload_digest=_digest_payload(_json_object(values)),
    )


def operator_manual_review_queue_heatmap_report_payload_digest(
    report: OperatorManualReviewQueueHeatmapReport,
) -> str:
    if type(report) is not OperatorManualReviewQueueHeatmapReport:
        raise ValueError("report must be an OperatorManualReviewQueueHeatmapReport")
    _validate_report(report)
    return _digest_payload(_payload_without_digest(report))


def validate_operator_manual_review_queue_heatmap_public_payload(
    payload: Mapping[str, object],
) -> bool:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload) != PAYLOAD_FIELDS:
        raise ValueError("payload must match the canonical heatmap schema")

    for field_name in COUNT_FIELDS:
        _validate_decimal_text(field_name, payload[field_name])
    _require_member("heatmap_status", payload["heatmap_status"], ALLOWED_STATUS)
    reason_codes = _normalize_reason_codes(payload["reason_codes"])
    _require_member("manual_next_step", payload["manual_next_step"], ALLOWED_NEXT_STEPS)
    _require_flag("paper_only", payload["paper_only"])
    _require_flag("report_only", payload["report_only"])
    _require_flag("readonly", payload["readonly"])
    _require_digest("payload_digest", payload["payload_digest"])

    expected_reasons = _derived_reason_codes(
        queue_item_count=Decimal(str(payload["queue_item_count"])),
        urgent_item_count=Decimal(str(payload["urgent_item_count"])),
        blocked_item_count=Decimal(str(payload["blocked_item_count"])),
        ready_packet_count=Decimal(str(payload["ready_packet_count"])),
        manual_capacity_count=Decimal(str(payload["manual_capacity_count"])),
    )
    if reason_codes != expected_reasons:
        raise ValueError("reason_codes must match queue heatmap inputs")
    if payload["heatmap_status"] != _status_for_reasons(reason_codes):
        raise ValueError("heatmap_status must match reason_codes")
    if payload["manual_next_step"] != _next_step_for_reasons(reason_codes):
        raise ValueError("manual_next_step must match reason_codes")
    expected_digest = _digest_payload(dict((field, payload[field]) for field in PAYLOAD_FIELDS[:-1]))
    if payload["payload_digest"] != expected_digest:
        raise ValueError("payload_digest must match public payload")
    return True


def _derived_reason_codes(
    *,
    queue_item_count: Decimal,
    urgent_item_count: Decimal,
    blocked_item_count: Decimal,
    ready_packet_count: Decimal,
    manual_capacity_count: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if queue_item_count == ZERO:
        reasons.append(EMPTY_REASON)
    if manual_capacity_count < queue_item_count:
        reasons.append(CAPACITY_REASON)
    if blocked_item_count > ZERO:
        reasons.append(BLOCKED_REASON)
    if urgent_item_count > Decimal("1.000000"):
        reasons.append(URGENT_REASON)
    if ready_packet_count < queue_item_count:
        reasons.append(PACKET_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reasons)


def _status_for_reasons(reason_codes: tuple[str, ...]) -> str:
    if CAPACITY_REASON in reason_codes or BLOCKED_REASON in reason_codes:
        return BLOCKED_STATUS
    if reason_codes == (READY_REASON,):
        return READY_STATUS
    return WATCH_STATUS


def _next_step_for_reasons(reason_codes: tuple[str, ...]) -> str:
    if _status_for_reasons(reason_codes) == BLOCKED_STATUS:
        return BLOCKED_NEXT_STEP
    if EMPTY_REASON in reason_codes:
        return EMPTY_NEXT_STEP
    if URGENT_REASON in reason_codes:
        return URGENT_NEXT_STEP
    if PACKET_REASON in reason_codes:
        return PACKET_NEXT_STEP
    return READY_NEXT_STEP


def _validate_report(report: OperatorManualReviewQueueHeatmapReport) -> None:
    expected_reasons = _derived_reason_codes(
        queue_item_count=report.queue_item_count,
        urgent_item_count=report.urgent_item_count,
        blocked_item_count=report.blocked_item_count,
        ready_packet_count=report.ready_packet_count,
        manual_capacity_count=report.manual_capacity_count,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match queue heatmap inputs")
    if report.heatmap_status != _status_for_reasons(report.reason_codes):
        raise ValueError("heatmap_status must match reason_codes")
    if report.manual_next_step != _next_step_for_reasons(report.reason_codes):
        raise ValueError("manual_next_step must match reason_codes")


def _report_to_payload(report: OperatorManualReviewQueueHeatmapReport) -> dict[str, object]:
    payload = _payload_without_digest(report)
    payload["payload_digest"] = report.payload_digest
    validate_operator_manual_review_queue_heatmap_public_payload(payload)
    return payload


def _payload_without_digest(
    report: OperatorManualReviewQueueHeatmapReport,
) -> dict[str, object]:
    return {
        "queue_item_count": str(report.queue_item_count),
        "urgent_item_count": str(report.urgent_item_count),
        "blocked_item_count": str(report.blocked_item_count),
        "ready_packet_count": str(report.ready_packet_count),
        "manual_capacity_count": str(report.manual_capacity_count),
        "heatmap_status": report.heatmap_status,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _digest_payload(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(
            dict(sorted(payload.items())),
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _json_object(values: Mapping[str, object]) -> dict[str, object]:
    converted: dict[str, object] = {}
    for name, value in values.items():
        if type(value) is Decimal:
            converted[name] = str(value)
        else:
            converted[name] = value
    return converted


def _normalize_count(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if normalized != value:
        raise ValueError(f"{name} must be a whole Decimal")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason in value:
        _require_member("reason_codes", reason, ALLOWED_REASONS)
        if reason in normalized:
            raise ValueError("reason_codes must not contain duplicates")
        normalized.append(reason)
    return tuple(normalized)


def _validate_decimal_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must use Decimal string values")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must use Decimal string values") from exc
    if str(_normalize_count(name, parsed)) != value:
        raise ValueError(f"{name} must use canonical Decimal string values")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a sha256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 digest")


def _require_hard_flags(value: object) -> None:
    _require_flag("paper_only", getattr(value, "paper_only", None))
    _require_flag("report_only", getattr(value, "report_only", None))
    _require_flag("readonly", getattr(value, "readonly", None))


def _require_flag(name: str, value: object) -> None:
    if value is not True:
        raise ValueError(f"{name} must be True")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")
