"""Pure specialist team postmortem readiness report for settled paper events."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_SPECIALIST_TEAM_POSTMORTEM_READINESS_CONFIG_VERSION = (
    "specialist-team-postmortem-readiness-v0"
)
SPECIALIST_TEAM_POSTMORTEM_REQUIRED_UPDATE_COUNT = Decimal("6.000000")

NO_SETTLED_PAPER_EVENTS = "no_settled_paper_events"
SUPABASE_PERSISTENCE_NOT_READY = "supabase_persistence_not_ready"

OUTCOME_EVIDENCE_NOT_READY = "outcome_evidence_not_ready"
FORECAST_ERROR_BUCKET_NOT_READY = "forecast_error_bucket_not_ready"
SOURCE_FAMILY_FEEDBACK_NOT_READY = "source_family_feedback_not_ready"
TEAM_MEMORY_UPDATE_NOT_READY = "team_memory_update_not_ready"
CALIBRATION_NOTE_NOT_READY = "calibration_note_not_ready"

BLOCKED_REASON_CODES = (
    NO_SETTLED_PAPER_EVENTS,
    SUPABASE_PERSISTENCE_NOT_READY,
)
ATTENTION_REASON_CODES = (
    OUTCOME_EVIDENCE_NOT_READY,
    FORECAST_ERROR_BUCKET_NOT_READY,
    SOURCE_FAMILY_FEEDBACK_NOT_READY,
    TEAM_MEMORY_UPDATE_NOT_READY,
    CALIBRATION_NOTE_NOT_READY,
)

DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")

__all__ = (
    "DEFAULT_SPECIALIST_TEAM_POSTMORTEM_READINESS_CONFIG_VERSION",
    "SPECIALIST_TEAM_POSTMORTEM_REQUIRED_UPDATE_COUNT",
    "SpecialistTeamPostmortemReadinessInput",
    "SpecialistTeamPostmortemReadinessReport",
    "build_specialist_team_postmortem_readiness_report",
    "specialist_team_postmortem_readiness_report_payload",
    "specialist_team_postmortem_readiness_report_digest",
)


@dataclass(frozen=True)
class SpecialistTeamPostmortemReadinessInput:
    settled_market_count: Decimal
    outcome_evidence_ready: bool
    forecast_error_bucket_ready: bool
    source_family_feedback_ready: bool
    team_memory_update_ready: bool
    calibration_note_ready: bool
    supabase_persistence_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamPostmortemReadinessInput:
            raise ValueError("input must be exactly SpecialistTeamPostmortemReadinessInput")
        object.__setattr__(
            self,
            "settled_market_count",
            _normalize_count("settled_market_count", self.settled_market_count),
        )
        for field_name in (
            "outcome_evidence_ready",
            "forecast_error_bucket_ready",
            "source_family_feedback_ready",
            "team_memory_update_ready",
            "calibration_note_ready",
            "supabase_persistence_ready",
        ):
            _require_bool(field_name, getattr(self, field_name))
        require_paper_only_flags("specialist team postmortem readiness input", self)


@dataclass(frozen=True)
class SpecialistTeamPostmortemReadinessReport:
    config_version: str
    settled_market_count: Decimal
    outcome_evidence_ready: bool
    forecast_error_bucket_ready: bool
    source_family_feedback_ready: bool
    team_memory_update_ready: bool
    calibration_note_ready: bool
    supabase_persistence_ready: bool
    postmortem_ready: bool
    learning_update_count: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamPostmortemReadinessReport:
            raise ValueError("report must be exactly SpecialistTeamPostmortemReadinessReport")
        _require_config_version(self.config_version)
        for field_name in (
            "settled_market_count",
            "learning_update_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "outcome_evidence_ready",
            "forecast_error_bucket_ready",
            "source_family_feedback_ready",
            "team_memory_update_ready",
            "calibration_note_ready",
            "supabase_persistence_ready",
            "postmortem_ready",
        ):
            _require_bool(field_name, getattr(self, field_name))
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
            "ready_ratio",
            _normalize_ratio("ready_ratio", self.ready_ratio),
        )
        require_paper_only_flags("specialist team postmortem readiness report", self)
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return specialist_team_postmortem_readiness_report_payload(self)

    @property
    def digest(self) -> str:
        return specialist_team_postmortem_readiness_report_digest(self)


def build_specialist_team_postmortem_readiness_report(
    readiness: SpecialistTeamPostmortemReadinessInput,
) -> SpecialistTeamPostmortemReadinessReport:
    if type(readiness) is not SpecialistTeamPostmortemReadinessInput:
        raise ValueError("readiness must be a SpecialistTeamPostmortemReadinessInput")
    require_paper_only_flags("readiness", readiness)
    blocked_reason_codes = _blocked_reason_codes(readiness)
    attention_reason_codes = _attention_reason_codes(readiness)

    return SpecialistTeamPostmortemReadinessReport(
        config_version=DEFAULT_SPECIALIST_TEAM_POSTMORTEM_READINESS_CONFIG_VERSION,
        settled_market_count=readiness.settled_market_count,
        outcome_evidence_ready=readiness.outcome_evidence_ready,
        forecast_error_bucket_ready=readiness.forecast_error_bucket_ready,
        source_family_feedback_ready=readiness.source_family_feedback_ready,
        team_memory_update_ready=readiness.team_memory_update_ready,
        calibration_note_ready=readiness.calibration_note_ready,
        supabase_persistence_ready=readiness.supabase_persistence_ready,
        postmortem_ready=not blocked_reason_codes and not attention_reason_codes,
        learning_update_count=_learning_update_count(readiness),
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ready_ratio(readiness),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def specialist_team_postmortem_readiness_report_payload(
    report: SpecialistTeamPostmortemReadinessReport,
) -> dict[str, Any]:
    if type(report) is not SpecialistTeamPostmortemReadinessReport:
        raise ValueError("report must be a SpecialistTeamPostmortemReadinessReport")
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    reject_unsafe_surface_fields("specialist team postmortem readiness report", payload)
    return payload


def specialist_team_postmortem_readiness_report_digest(
    report: SpecialistTeamPostmortemReadinessReport,
) -> str:
    payload = specialist_team_postmortem_readiness_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _learning_update_count(readiness: SpecialistTeamPostmortemReadinessInput) -> Decimal:
    return _count(
        sum(
            (
                readiness.outcome_evidence_ready,
                readiness.forecast_error_bucket_ready,
                readiness.source_family_feedback_ready,
                readiness.team_memory_update_ready,
                readiness.calibration_note_ready,
                readiness.supabase_persistence_ready,
            ),
        ),
    )


def _ready_ratio(readiness: SpecialistTeamPostmortemReadinessInput) -> Decimal:
    return _ratio(
        _learning_update_count(readiness),
        SPECIALIST_TEAM_POSTMORTEM_REQUIRED_UPDATE_COUNT,
    )


def _blocked_reason_codes(
    readiness: SpecialistTeamPostmortemReadinessInput,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if readiness.settled_market_count == ZERO:
        reasons.append(NO_SETTLED_PAPER_EVENTS)
    if not readiness.supabase_persistence_ready:
        reasons.append(SUPABASE_PERSISTENCE_NOT_READY)
    return tuple(reasons)


def _attention_reason_codes(
    readiness: SpecialistTeamPostmortemReadinessInput | SpecialistTeamPostmortemReadinessReport,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not readiness.outcome_evidence_ready:
        reasons.append(OUTCOME_EVIDENCE_NOT_READY)
    if not readiness.forecast_error_bucket_ready:
        reasons.append(FORECAST_ERROR_BUCKET_NOT_READY)
    if not readiness.source_family_feedback_ready:
        reasons.append(SOURCE_FAMILY_FEEDBACK_NOT_READY)
    if not readiness.team_memory_update_ready:
        reasons.append(TEAM_MEMORY_UPDATE_NOT_READY)
    if not readiness.calibration_note_ready:
        reasons.append(CALIBRATION_NOTE_NOT_READY)
    return tuple(reasons)


def _validate_report(report: SpecialistTeamPostmortemReadinessReport) -> None:
    expected_blockers = _blocked_reason_codes_from_report(report)
    expected_attention = _attention_reason_codes(report)
    if report.blocked_reason_codes != expected_blockers:
        raise ValueError("blocked_reason_codes must match readiness components")
    if report.attention_reason_codes != expected_attention:
        raise ValueError("attention_reason_codes must match readiness components")
    if report.learning_update_count != _learning_update_count_from_report(report):
        raise ValueError("learning_update_count must match readiness components")
    if report.ready_ratio != _ratio(
        report.learning_update_count,
        SPECIALIST_TEAM_POSTMORTEM_REQUIRED_UPDATE_COUNT,
    ):
        raise ValueError("ready_ratio must match readiness components")
    if report.postmortem_ready != (not expected_blockers and not expected_attention):
        raise ValueError("postmortem_ready must match readiness components")


def _blocked_reason_codes_from_report(
    report: SpecialistTeamPostmortemReadinessReport,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if report.settled_market_count == ZERO:
        reasons.append(NO_SETTLED_PAPER_EVENTS)
    if not report.supabase_persistence_ready:
        reasons.append(SUPABASE_PERSISTENCE_NOT_READY)
    return tuple(reasons)


def _learning_update_count_from_report(
    report: SpecialistTeamPostmortemReadinessReport,
) -> Decimal:
    return _count(
        sum(
            (
                report.outcome_evidence_ready,
                report.forecast_error_bucket_ready,
                report.source_family_feedback_ready,
                report.team_memory_update_ready,
                report.calibration_note_ready,
                report.supabase_persistence_ready,
            ),
        ),
    )


def _require_config_version(value: object) -> None:
    if value != DEFAULT_SPECIALIST_TEAM_POSTMORTEM_READINESS_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _normalize_count(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal_value.quantize(QUANTUM)


def _normalize_ratio(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > Decimal("1.000000"):
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


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)
