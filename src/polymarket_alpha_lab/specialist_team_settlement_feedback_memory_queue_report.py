from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "SpecialistTeamSettlementFeedbackMemoryQueueInput",
    "SpecialistTeamSettlementFeedbackMemoryQueueReport",
    "build_specialist_team_settlement_feedback_memory_queue_report",
    "specialist_team_settlement_feedback_memory_queue_report_public_payload",
    "validate_specialist_team_settlement_feedback_memory_queue_payload_digest",
)


STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCK)
READY_REASON = "settlement_feedback_memory_queue_ready"
REASON_PRIORITY = (
    "settled_events_missing",
    "settlement_feedback_items_missing",
    "settlement_feedback_memory_writes_pending",
    "settlement_feedback_calibration_updates_sparse",
    "settlement_feedback_queue_age_block",
    "settlement_feedback_queue_age_watch",
    READY_REASON,
)
READY_STEP = "continue_readonly_memory_queue_monitoring"
WATCH_STEP = "review_pending_feedback_before_memory_queue_write"
BLOCK_STEP = "manual_settlement_feedback_triage_required"
COUNT_QUANTUM = Decimal("1")
HOUR_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
STALE_WATCH_HOURS = Decimal("24.000000")
STALE_BLOCK_HOURS = Decimal("72.000000")
_HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class SpecialistTeamSettlementFeedbackMemoryQueueInput(_FinalDataclass):
    settled_event_count: Decimal
    feedback_item_count: Decimal
    memory_write_ready_count: Decimal
    calibration_update_count: Decimal
    oldest_feedback_age_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamSettlementFeedbackMemoryQueueInput,
            "input",
        )
        for field_name in (
            "settled_event_count",
            "feedback_item_count",
            "memory_write_ready_count",
            "calibration_update_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_feedback_age_hours",
            _require_hour_decimal(
                "oldest_feedback_age_hours",
                self.oldest_feedback_age_hours,
            ),
        )
        _validate_count_relationships(
            settled_event_count=self.settled_event_count,
            feedback_item_count=self.feedback_item_count,
            memory_write_ready_count=self.memory_write_ready_count,
            calibration_update_count=self.calibration_update_count,
        )
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class SpecialistTeamSettlementFeedbackMemoryQueueReport(_FinalDataclass):
    settled_event_count: Decimal
    feedback_item_count: Decimal
    memory_write_ready_count: Decimal
    calibration_update_count: Decimal
    oldest_feedback_age_hours: Decimal
    feedback_queue_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamSettlementFeedbackMemoryQueueReport,
            "report",
        )
        for field_name in (
            "settled_event_count",
            "feedback_item_count",
            "memory_write_ready_count",
            "calibration_update_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_feedback_age_hours",
            _require_hour_decimal(
                "oldest_feedback_age_hours",
                self.oldest_feedback_age_hours,
            ),
        )
        _validate_count_relationships(
            settled_event_count=self.settled_event_count,
            feedback_item_count=self.feedback_item_count,
            memory_write_ready_count=self.memory_write_ready_count,
            calibration_update_count=self.calibration_update_count,
        )
        _require_status("feedback_queue_status", self.feedback_queue_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _validate_report_fields(self)
        require_paper_only_flags("report", self)
        expected_digest = _payload_digest(_report_public_values(self, include_digest=False))
        if self.payload_digest:
            _require_sha256("payload_digest", self.payload_digest)
            if self.payload_digest != expected_digest:
                raise ValueError("payload_digest must match report fields")
        else:
            object.__setattr__(self, "payload_digest", expected_digest)

    @property
    def public_payload(self) -> dict[str, object]:
        return specialist_team_settlement_feedback_memory_queue_report_public_payload(
            self,
        )


def build_specialist_team_settlement_feedback_memory_queue_report(
    queue_input: SpecialistTeamSettlementFeedbackMemoryQueueInput,
) -> SpecialistTeamSettlementFeedbackMemoryQueueReport:
    if type(queue_input) is not SpecialistTeamSettlementFeedbackMemoryQueueInput:
        raise TypeError(
            "queue_input must be SpecialistTeamSettlementFeedbackMemoryQueueInput",
        )
    require_paper_only_flags("input", queue_input)
    reason_codes = _reason_codes(queue_input)
    status = _status_from_reason_codes(reason_codes)
    return SpecialistTeamSettlementFeedbackMemoryQueueReport(
        settled_event_count=queue_input.settled_event_count,
        feedback_item_count=queue_input.feedback_item_count,
        memory_write_ready_count=queue_input.memory_write_ready_count,
        calibration_update_count=queue_input.calibration_update_count,
        oldest_feedback_age_hours=queue_input.oldest_feedback_age_hours,
        feedback_queue_status=status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(status),
    )


def specialist_team_settlement_feedback_memory_queue_report_public_payload(
    report: SpecialistTeamSettlementFeedbackMemoryQueueReport,
) -> dict[str, object]:
    if type(report) is not SpecialistTeamSettlementFeedbackMemoryQueueReport:
        raise TypeError(
            "report must be SpecialistTeamSettlementFeedbackMemoryQueueReport",
        )
    require_paper_only_flags("report", report)
    _validate_report_fields(report)
    if report.payload_digest != _payload_digest(
        _report_public_values(report, include_digest=False),
    ):
        raise ValueError("payload_digest must match report fields")
    payload = json_ready_no_floats(_report_public_values(report, include_digest=True))
    if type(payload) is not dict:
        raise ValueError("public_payload must be a dict")
    return payload


def validate_specialist_team_settlement_feedback_memory_queue_payload_digest(
    payload: Mapping[str, object],
) -> bool:
    if not isinstance(payload, Mapping):
        return False
    supplied_digest = payload.get("payload_digest")
    if type(supplied_digest) is not str or not _HEX_SHA256_RE.fullmatch(
        supplied_digest,
    ):
        return False
    payload_body = dict(payload)
    payload_body.pop("payload_digest", None)
    try:
        expected_digest = _payload_digest(payload_body)
    except (TypeError, ValueError, InvalidOperation):
        return False
    return supplied_digest == expected_digest


def _report_public_values(
    report: SpecialistTeamSettlementFeedbackMemoryQueueReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    values: dict[str, object] = {
        "settled_event_count": report.settled_event_count,
        "feedback_item_count": report.feedback_item_count,
        "memory_write_ready_count": report.memory_write_ready_count,
        "calibration_update_count": report.calibration_update_count,
        "oldest_feedback_age_hours": report.oldest_feedback_age_hours,
        "feedback_queue_status": report.feedback_queue_status,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        values["payload_digest"] = report.payload_digest
    return values


def _reason_codes(
    queue_input: SpecialistTeamSettlementFeedbackMemoryQueueInput,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if queue_input.settled_event_count == ZERO:
        reasons.append("settled_events_missing")
        reasons.append("settlement_feedback_items_missing")
        reasons.append("settlement_feedback_memory_writes_pending")
        reasons.append("settlement_feedback_calibration_updates_sparse")
    else:
        if queue_input.feedback_item_count < queue_input.settled_event_count:
            reasons.append("settlement_feedback_items_missing")
        if queue_input.memory_write_ready_count < queue_input.feedback_item_count:
            reasons.append("settlement_feedback_memory_writes_pending")
        if queue_input.calibration_update_count < _minimum_calibration_updates(
            queue_input.settled_event_count,
        ):
            reasons.append("settlement_feedback_calibration_updates_sparse")
    if queue_input.oldest_feedback_age_hours >= STALE_BLOCK_HOURS:
        reasons.append("settlement_feedback_queue_age_block")
    elif queue_input.oldest_feedback_age_hours >= STALE_WATCH_HOURS:
        reasons.append("settlement_feedback_queue_age_watch")
    if not reasons:
        reasons.append(READY_REASON)
    return _require_reason_codes(tuple(reasons))


def _minimum_calibration_updates(settled_event_count: Decimal) -> Decimal:
    return max(Decimal("1"), settled_event_count / Decimal("5"))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        "settled_events_missing" in reason_codes
        or "settlement_feedback_queue_age_block" in reason_codes
    ):
        return STATUS_BLOCK
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _manual_next_step(status: str) -> str:
    if status == STATUS_READY:
        return READY_STEP
    if status == STATUS_WATCH:
        return WATCH_STEP
    return BLOCK_STEP


def _validate_report_fields(
    report: SpecialistTeamSettlementFeedbackMemoryQueueReport,
) -> None:
    source = SpecialistTeamSettlementFeedbackMemoryQueueInput(
        settled_event_count=report.settled_event_count,
        feedback_item_count=report.feedback_item_count,
        memory_write_ready_count=report.memory_write_ready_count,
        calibration_update_count=report.calibration_update_count,
        oldest_feedback_age_hours=report.oldest_feedback_age_hours,
    )
    expected_reasons = _reason_codes(source)
    expected_status = _status_from_reason_codes(expected_reasons)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report counts")
    if report.feedback_queue_status != expected_status:
        raise ValueError("feedback_queue_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match feedback_queue_status")


def _validate_count_relationships(
    *,
    settled_event_count: Decimal,
    feedback_item_count: Decimal,
    memory_write_ready_count: Decimal,
    calibration_update_count: Decimal,
) -> None:
    if feedback_item_count > settled_event_count:
        raise ValueError("feedback_item_count must not exceed settled_event_count")
    if memory_write_ready_count > feedback_item_count:
        raise ValueError("memory_write_ready_count must not exceed feedback_item_count")
    if calibration_update_count > settled_event_count:
        raise ValueError("calibration_update_count must not exceed settled_event_count")


def _payload_digest(payload: Mapping[str, object]) -> str:
    ready_payload = json_ready_no_floats(dict(payload))
    encoded = json.dumps(
        ready_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_hour_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(HOUR_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or block")


def _require_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_PRIORITY:
            raise ValueError("reason_codes must be supported public reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    ordered = tuple(reason for reason in REASON_PRIORITY if reason in reason_codes)
    if ordered != reason_codes:
        raise ValueError("reason_codes must use canonical order")
    return ordered


def _require_manual_next_step(value: object) -> None:
    if value not in (READY_STEP, WATCH_STEP, BLOCK_STEP):
        raise ValueError("manual_next_step must be supported")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or not _HEX_SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
