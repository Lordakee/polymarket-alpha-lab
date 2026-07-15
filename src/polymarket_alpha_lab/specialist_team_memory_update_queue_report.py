"""Pure paper-only specialist team memory-queue readiness report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_SPECIALIST_TEAM_MEMORY_UPDATE_QUEUE_CONFIG_VERSION = (
    "specialist-team-memory-update-queue-report-v0"
)
SPECIALIST_TEAM_MEMORY_UPDATE_QUEUE_PRIORITY_BANDS = (
    "ready",
    "attention",
    "blocked",
)

SETTLED_FEEDBACK_NOT_READY = "settled_feedback_not_ready"
POSTMORTEM_NOT_READY = "postmortem_not_ready"
SUPABASE_PERSISTENCE_NOT_READY = "supabase_persistence_not_ready"
PLAYBOOK_NOT_READY = "playbook_not_ready"

SOURCE_FAMILY_FEEDBACK_NOT_READY = "source_family_feedback_not_ready"
CALIBRATION_NOTE_NOT_READY = "calibration_note_not_ready"
DOMAIN_RISK_REGISTER_NOT_READY = "domain_risk_register_not_ready"

BLOCKED_REASON_CODES = (
    SETTLED_FEEDBACK_NOT_READY,
    POSTMORTEM_NOT_READY,
    SUPABASE_PERSISTENCE_NOT_READY,
    PLAYBOOK_NOT_READY,
)
ATTENTION_REASON_CODES = (
    SOURCE_FAMILY_FEEDBACK_NOT_READY,
    CALIBRATION_NOTE_NOT_READY,
    DOMAIN_RISK_REGISTER_NOT_READY,
)

REQUIRED_SIGNAL_COUNT = Decimal("7.000000")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)

__all__ = (
    "DEFAULT_SPECIALIST_TEAM_MEMORY_UPDATE_QUEUE_CONFIG_VERSION",
    "SPECIALIST_TEAM_MEMORY_UPDATE_QUEUE_PRIORITY_BANDS",
    "SpecialistTeamMemoryUpdateQueueInput",
    "SpecialistTeamMemoryUpdateQueueReport",
    "build_specialist_team_memory_update_queue_report",
    "specialist_team_memory_update_queue_report_digest",
    "specialist_team_memory_update_queue_report_payload",
)


@dataclass(frozen=True)
class SpecialistTeamMemoryUpdateQueueInput:
    settled_feedback_ready: bool
    postmortem_ready: bool
    source_family_feedback_ready: bool
    calibration_note_ready: bool
    supabase_persistence_ready: bool
    playbook_ready: bool
    domain_risk_register_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamMemoryUpdateQueueInput:
            raise ValueError("input must be exactly SpecialistTeamMemoryUpdateQueueInput")
        for field_name in READY_SIGNAL_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        require_paper_only_flags("specialist team memory queue input", self)


@dataclass(frozen=True)
class SpecialistTeamMemoryUpdateQueueReport:
    config_version: str
    settled_feedback_ready: bool
    postmortem_ready: bool
    source_family_feedback_ready: bool
    calibration_note_ready: bool
    supabase_persistence_ready: bool
    playbook_ready: bool
    domain_risk_register_ready: bool
    memory_update_queue_ready: bool
    update_priority_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_signal_count: Decimal
    required_signal_count: Decimal
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamMemoryUpdateQueueReport:
            raise ValueError("report must be exactly SpecialistTeamMemoryUpdateQueueReport")
        _require_config_version(self.config_version)
        for field_name in READY_SIGNAL_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_bool("memory_update_queue_ready", self.memory_update_queue_ready)
        _require_priority_band("update_priority_band", self.update_priority_band)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCKED_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "ready_signal_count",
            _normalize_count("ready_signal_count", self.ready_signal_count),
        )
        object.__setattr__(
            self,
            "required_signal_count",
            _normalize_count("required_signal_count", self.required_signal_count),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _normalize_ratio("ready_ratio", self.ready_ratio),
        )
        _require_digest("digest", self.digest)
        require_paper_only_flags("specialist team memory queue report", self)
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return specialist_team_memory_update_queue_report_payload(self)


READY_SIGNAL_FIELDS = (
    "settled_feedback_ready",
    "postmortem_ready",
    "source_family_feedback_ready",
    "calibration_note_ready",
    "supabase_persistence_ready",
    "playbook_ready",
    "domain_risk_register_ready",
)


def build_specialist_team_memory_update_queue_report(
    readiness: SpecialistTeamMemoryUpdateQueueInput,
) -> SpecialistTeamMemoryUpdateQueueReport:
    if type(readiness) is not SpecialistTeamMemoryUpdateQueueInput:
        raise ValueError("readiness must be a SpecialistTeamMemoryUpdateQueueInput")
    require_paper_only_flags("readiness", readiness)
    blocked_reason_codes = _blocked_reason_codes(readiness)
    attention_reason_codes = _attention_reason_codes(readiness)
    ready_signal_count = _ready_signal_count(readiness)
    report_without_digest = dict(
        config_version=DEFAULT_SPECIALIST_TEAM_MEMORY_UPDATE_QUEUE_CONFIG_VERSION,
        settled_feedback_ready=readiness.settled_feedback_ready,
        postmortem_ready=readiness.postmortem_ready,
        source_family_feedback_ready=readiness.source_family_feedback_ready,
        calibration_note_ready=readiness.calibration_note_ready,
        supabase_persistence_ready=readiness.supabase_persistence_ready,
        playbook_ready=readiness.playbook_ready,
        domain_risk_register_ready=readiness.domain_risk_register_ready,
        memory_update_queue_ready=not blocked_reason_codes and not attention_reason_codes,
        update_priority_band=_priority_band(blocked_reason_codes, attention_reason_codes),
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_signal_count=ready_signal_count,
        required_signal_count=REQUIRED_SIGNAL_COUNT,
        ready_ratio=_ratio(ready_signal_count, REQUIRED_SIGNAL_COUNT),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return SpecialistTeamMemoryUpdateQueueReport(
        **report_without_digest,
        digest=_digest_for_payload(report_without_digest),
    )


def specialist_team_memory_update_queue_report_payload(
    report: SpecialistTeamMemoryUpdateQueueReport,
) -> dict[str, Any]:
    if type(report) is not SpecialistTeamMemoryUpdateQueueReport:
        raise ValueError("report must be a SpecialistTeamMemoryUpdateQueueReport")
    require_paper_only_flags("report", report)
    payload = {
        "config_version": report.config_version,
        "settled_feedback_ready": report.settled_feedback_ready,
        "postmortem_ready": report.postmortem_ready,
        "source_family_feedback_ready": report.source_family_feedback_ready,
        "calibration_note_ready": report.calibration_note_ready,
        "supabase_persistence_ready": report.supabase_persistence_ready,
        "playbook_ready": report.playbook_ready,
        "domain_risk_register_ready": report.domain_risk_register_ready,
        "memory_update_queue_ready": report.memory_update_queue_ready,
        "update_priority_band": report.update_priority_band,
        "blocked_reason_codes": report.blocked_reason_codes,
        "attention_reason_codes": report.attention_reason_codes,
        "ready_signal_count": report.ready_signal_count,
        "required_signal_count": report.required_signal_count,
        "ready_ratio": report.ready_ratio,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    ready_payload = json_ready_no_floats(payload)
    if not isinstance(ready_payload, dict):
        raise ValueError("payload must be a JSON object")
    return ready_payload


def specialist_team_memory_update_queue_report_digest(
    report: SpecialistTeamMemoryUpdateQueueReport,
) -> str:
    payload = specialist_team_memory_update_queue_report_payload(report)
    return _digest_for_payload(payload)


def _blocked_reason_codes(
    readiness: SpecialistTeamMemoryUpdateQueueInput | SpecialistTeamMemoryUpdateQueueReport,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not readiness.settled_feedback_ready:
        reasons.append(SETTLED_FEEDBACK_NOT_READY)
    if not readiness.postmortem_ready:
        reasons.append(POSTMORTEM_NOT_READY)
    if not readiness.supabase_persistence_ready:
        reasons.append(SUPABASE_PERSISTENCE_NOT_READY)
    if not readiness.playbook_ready:
        reasons.append(PLAYBOOK_NOT_READY)
    return tuple(reasons)


def _attention_reason_codes(
    readiness: SpecialistTeamMemoryUpdateQueueInput | SpecialistTeamMemoryUpdateQueueReport,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not readiness.source_family_feedback_ready:
        reasons.append(SOURCE_FAMILY_FEEDBACK_NOT_READY)
    if not readiness.calibration_note_ready:
        reasons.append(CALIBRATION_NOTE_NOT_READY)
    if not readiness.domain_risk_register_ready:
        reasons.append(DOMAIN_RISK_REGISTER_NOT_READY)
    return tuple(reasons)


def _priority_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes:
        return "attention"
    return "ready"


def _ready_signal_count(
    readiness: SpecialistTeamMemoryUpdateQueueInput | SpecialistTeamMemoryUpdateQueueReport,
) -> Decimal:
    return _count(sum(bool(getattr(readiness, field_name)) for field_name in READY_SIGNAL_FIELDS))


def _validate_report(report: SpecialistTeamMemoryUpdateQueueReport) -> None:
    expected_blocked = _blocked_reason_codes(report)
    expected_attention = _attention_reason_codes(report)
    expected_ready_signal_count = _ready_signal_count(report)
    expected_band = _priority_band(expected_blocked, expected_attention)
    if report.blocked_reason_codes != expected_blocked:
        raise ValueError("blocked_reason_codes must match readiness components")
    if report.attention_reason_codes != expected_attention:
        raise ValueError("attention_reason_codes must match readiness components")
    if report.ready_signal_count != expected_ready_signal_count:
        raise ValueError("ready_signal_count must match readiness components")
    if report.required_signal_count != REQUIRED_SIGNAL_COUNT:
        raise ValueError("required_signal_count must match readiness components")
    if report.ready_ratio != _ratio(expected_ready_signal_count, REQUIRED_SIGNAL_COUNT):
        raise ValueError("ready_ratio must match readiness components")
    if report.update_priority_band != expected_band:
        raise ValueError("update_priority_band must match readiness components")
    if report.memory_update_queue_ready != (expected_band == "ready"):
        raise ValueError("memory_update_queue_ready must match readiness components")
    if report.digest != specialist_team_memory_update_queue_report_digest(report):
        raise ValueError("digest must match report payload")


def _require_config_version(value: object) -> None:
    if value != DEFAULT_SPECIALIST_TEAM_MEMORY_UPDATE_QUEUE_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_priority_band(name: str, value: object) -> None:
    if value not in SPECIALIST_TEAM_MEMORY_UPDATE_QUEUE_PRIORITY_BANDS:
        raise ValueError(f"{name} must be a supported priority band")


def _normalize_count(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal_value.quantize(QUANTUM)


def _normalize_ratio(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value.quantize(QUANTUM)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable of reason codes")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable of reason codes") from exc
    seen: set[str] = set()
    previous_index = -1
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError(f"{name} must contain strings")
        if reason_code not in allowed_values:
            raise ValueError(f"{name} contains unsupported reason codes")
        if reason_code in seen:
            raise ValueError(f"{name} must be unique")
        seen.add(reason_code)
        index = allowed_values.index(reason_code)
        if index <= previous_index:
            raise ValueError(f"{name} must be sorted deterministically")
        previous_index = index
    return reason_codes


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    allowed = set("0123456789abcdef")
    if any(char not in allowed for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _digest_for_payload(payload: dict[str, Any]) -> str:
    ready_payload = json_ready_no_floats(payload)
    encoded = json.dumps(
        ready_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
