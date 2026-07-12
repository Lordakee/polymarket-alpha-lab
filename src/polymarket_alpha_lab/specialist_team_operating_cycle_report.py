"""Pure specialist team operating-cycle readiness report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_SPECIALIST_TEAM_OPERATING_CYCLE_CONFIG_VERSION = (
    "specialist-team-operating-cycle-v0"
)
SPECIALIST_TEAM_OPERATING_CYCLE_BANDS = ("ready", "attention", "blocked")

READY_BAND = "ready"
ATTENTION_BAND = "attention"
BLOCKED_BAND = "blocked"

RESEARCH_QUEUE_NOT_READY = "research_queue_not_ready"
PLAYBOOK_NOT_READY = "playbook_not_ready"
RISK_REGISTER_NOT_READY = "risk_register_not_ready"
SUPABASE_MEMORY_NOT_READY = "supabase_memory_not_ready"
TEAM_SCORECARD_NOT_READY = "team_scorecard_not_ready"
POSTMORTEM_NOT_READY = "postmortem_not_ready"
MEMORY_UPDATE_QUEUE_NOT_READY = "memory_update_queue_not_ready"
LEARNING_FEEDBACK_NOT_READY = "learning_feedback_not_ready"

BLOCKED_REASON_CODES = (
    RESEARCH_QUEUE_NOT_READY,
    PLAYBOOK_NOT_READY,
    RISK_REGISTER_NOT_READY,
    SUPABASE_MEMORY_NOT_READY,
)
ATTENTION_REASON_CODES = (
    TEAM_SCORECARD_NOT_READY,
    POSTMORTEM_NOT_READY,
    MEMORY_UPDATE_QUEUE_NOT_READY,
    LEARNING_FEEDBACK_NOT_READY,
)
ALL_REASON_CODES = BLOCKED_REASON_CODES + ATTENTION_REASON_CODES

DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
SIX_PLACES = Decimal("0.000001")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")

__all__ = (
    "DEFAULT_SPECIALIST_TEAM_OPERATING_CYCLE_CONFIG_VERSION",
    "SPECIALIST_TEAM_OPERATING_CYCLE_BANDS",
    "SpecialistTeamOperatingCycleReport",
    "build_specialist_team_operating_cycle_report",
    "specialist_team_operating_cycle_report_payload",
    "specialist_team_operating_cycle_report_digest",
)


@dataclass(frozen=True)
class SpecialistTeamOperatingCycleReport:
    config_version: str
    research_queue_ready: bool
    playbook_ready: bool
    risk_register_ready: bool
    team_scorecard_ready: bool
    postmortem_ready: bool
    memory_update_queue_ready: bool
    learning_feedback_ready: bool
    supabase_memory_ready: bool
    operating_cycle_ready: bool
    cycle_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamOperatingCycleReport:
            raise ValueError("report must be exactly SpecialistTeamOperatingCycleReport")
        _require_config_version(self.config_version)
        for field_name in _READY_FLAG_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_bool("operating_cycle_ready", self.operating_cycle_ready)
        _require_band("cycle_band", self.cycle_band)
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
        _require_digest("digest", self.digest)
        require_paper_only_flags("specialist team operating cycle report", self)
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return specialist_team_operating_cycle_report_payload(self)


_READY_FLAG_FIELDS = (
    "research_queue_ready",
    "playbook_ready",
    "risk_register_ready",
    "team_scorecard_ready",
    "postmortem_ready",
    "memory_update_queue_ready",
    "learning_feedback_ready",
    "supabase_memory_ready",
)


def build_specialist_team_operating_cycle_report(
    *,
    research_queue_ready: bool,
    playbook_ready: bool,
    risk_register_ready: bool,
    team_scorecard_ready: bool,
    postmortem_ready: bool,
    memory_update_queue_ready: bool,
    learning_feedback_ready: bool,
    supabase_memory_ready: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SpecialistTeamOperatingCycleReport:
    flags = {
        "research_queue_ready": research_queue_ready,
        "playbook_ready": playbook_ready,
        "risk_register_ready": risk_register_ready,
        "team_scorecard_ready": team_scorecard_ready,
        "postmortem_ready": postmortem_ready,
        "memory_update_queue_ready": memory_update_queue_ready,
        "learning_feedback_ready": learning_feedback_ready,
        "supabase_memory_ready": supabase_memory_ready,
    }
    for field_name, value in flags.items():
        _require_bool(field_name, value)
    hard_flags = _HardFlags(
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )
    require_paper_only_flags("specialist team operating cycle build request", hard_flags)
    blocked_reason_codes = _blocked_reason_codes(flags)
    attention_reason_codes = _attention_reason_codes(flags)
    cycle_band = _cycle_band(blocked_reason_codes, attention_reason_codes)
    values: dict[str, object] = {
        "config_version": DEFAULT_SPECIALIST_TEAM_OPERATING_CYCLE_CONFIG_VERSION,
        **flags,
        "operating_cycle_ready": cycle_band == READY_BAND,
        "cycle_band": cycle_band,
        "blocked_reason_codes": blocked_reason_codes,
        "attention_reason_codes": attention_reason_codes,
        "ready_ratio": _ready_ratio(flags),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return SpecialistTeamOperatingCycleReport(
        **values,
        digest=_digest_from_values(values),
    )


def specialist_team_operating_cycle_report_payload(
    report: SpecialistTeamOperatingCycleReport,
) -> dict[str, Any]:
    if type(report) is not SpecialistTeamOperatingCycleReport:
        raise ValueError("report must be a SpecialistTeamOperatingCycleReport")
    require_paper_only_flags("specialist team operating cycle report", report)
    _validate_report(report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("public_payload must be a JSON object")
    if payload.get("digest") != specialist_team_operating_cycle_report_digest(report):
        raise ValueError("digest must match public payload")
    return payload


def specialist_team_operating_cycle_report_digest(
    report: SpecialistTeamOperatingCycleReport,
) -> str:
    if type(report) is not SpecialistTeamOperatingCycleReport:
        raise ValueError("report must be a SpecialistTeamOperatingCycleReport")
    return _digest_from_values(_report_values_without_digest(report))


@dataclass(frozen=True)
class _HardFlags:
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _blocked_reason_codes(values: dict[str, bool]) -> tuple[str, ...]:
    reasons: list[str] = []
    if not values["research_queue_ready"]:
        reasons.append(RESEARCH_QUEUE_NOT_READY)
    if not values["playbook_ready"]:
        reasons.append(PLAYBOOK_NOT_READY)
    if not values["risk_register_ready"]:
        reasons.append(RISK_REGISTER_NOT_READY)
    if not values["supabase_memory_ready"]:
        reasons.append(SUPABASE_MEMORY_NOT_READY)
    return tuple(reasons)


def _attention_reason_codes(values: dict[str, bool]) -> tuple[str, ...]:
    if _blocked_reason_codes(values):
        return ()
    reasons: list[str] = []
    if not values["team_scorecard_ready"]:
        reasons.append(TEAM_SCORECARD_NOT_READY)
    if not values["postmortem_ready"]:
        reasons.append(POSTMORTEM_NOT_READY)
    if not values["memory_update_queue_ready"]:
        reasons.append(MEMORY_UPDATE_QUEUE_NOT_READY)
    if not values["learning_feedback_ready"]:
        reasons.append(LEARNING_FEEDBACK_NOT_READY)
    return tuple(reasons)


def _cycle_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return BLOCKED_BAND
    if attention_reason_codes:
        return ATTENTION_BAND
    return READY_BAND


def _ready_ratio(values: dict[str, bool]) -> Decimal:
    ready_count = Decimal(sum(1 for field_name in _READY_FLAG_FIELDS if values[field_name]))
    total_count = Decimal(len(_READY_FLAG_FIELDS))
    with localcontext(DECIMAL_CONTEXT):
        return (ready_count / total_count).quantize(SIX_PLACES)


def _validate_report(report: SpecialistTeamOperatingCycleReport) -> None:
    values = {field_name: getattr(report, field_name) for field_name in _READY_FLAG_FIELDS}
    blocked_reason_codes = _blocked_reason_codes(values)
    attention_reason_codes = _attention_reason_codes(values)
    cycle_band = _cycle_band(blocked_reason_codes, attention_reason_codes)
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match readiness flags")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match readiness flags")
    if report.cycle_band != cycle_band:
        raise ValueError("cycle_band must match readiness flags")
    if report.operating_cycle_ready != (cycle_band == READY_BAND):
        raise ValueError("operating_cycle_ready must match readiness flags")
    if report.ready_ratio != _ready_ratio(values):
        raise ValueError("ready_ratio must match readiness flags")
    if report.digest != specialist_team_operating_cycle_report_digest(report):
        raise ValueError("digest must match public payload")


def _report_values_without_digest(
    report: SpecialistTeamOperatingCycleReport,
) -> dict[str, object]:
    values: dict[str, object] = {}
    for field in fields(report):
        if field.name == "digest":
            continue
        values[field.name] = getattr(report, field.name)
    return values


def _digest_from_values(values: dict[str, object]) -> str:
    payload = json_ready_no_floats(values)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_config_version(value: object) -> None:
    if value != DEFAULT_SPECIALIST_TEAM_OPERATING_CYCLE_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_band(name: str, value: object) -> None:
    if value not in SPECIALIST_TEAM_OPERATING_CYCLE_BANDS:
        raise ValueError(f"{name} must be a supported cycle band")


def _normalize_reason_codes(
    name: str,
    values: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable of reason codes")
    try:
        reason_codes = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable of reason codes") from exc
    seen: set[str] = set()
    previous_index = -1
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError(f"{name} must contain strings")
        if reason_code not in allowed_values:
            raise ValueError(f"{name} contains an unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{name} must be unique")
        seen.add(reason_code)
        index = ALL_REASON_CODES.index(reason_code)
        if index <= previous_index:
            raise ValueError(f"{name} must be sorted deterministically")
        previous_index = index
    return reason_codes


def _normalize_ratio(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    quantized = value.quantize(SIX_PLACES)
    if value != quantized:
        raise ValueError(f"{name} must be quantized to six places")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{name} must be between 0 and 1")
    return quantized


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")
