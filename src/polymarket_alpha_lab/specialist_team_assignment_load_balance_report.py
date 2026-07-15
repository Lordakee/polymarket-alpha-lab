"""Paper-only specialist team assignment load-balance report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from .team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_SPECIALIST_TEAM_ASSIGNMENT_LOAD_BALANCE_CONFIG_VERSION = (
    "specialist-team-assignment-load-balance-report-v0"
)
SPECIALIST_TEAM_ASSIGNMENT_LOAD_BALANCE_BANDS = (
    "ready",
    "attention",
    "blocked",
)

READY_BAND = "ready"
ATTENTION_BAND = "attention"
BLOCKED_BAND = "blocked"

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

MAX_READY_AVERAGE_REVIEW_LAG_SECONDS = Decimal("900.000000")
MAX_READY_QUEUED_CANDIDATE_COUNT = Decimal("0.000000")
MAX_READY_HIGH_PRIORITY_CANDIDATE_COUNT = Decimal("0.000000")

NO_TEAMS_BLOCKED = "specialist_team_assignment_no_teams_blocked"
NO_READY_TEAMS_BLOCKED = "specialist_team_assignment_no_ready_teams_blocked"
ALL_TEAMS_OVERLOADED_BLOCKED = "specialist_team_assignment_all_teams_overloaded_blocked"
MANUAL_REVIEW_CAPACITY_BLOCKED = (
    "specialist_team_assignment_manual_review_capacity_blocked"
)
SUPABASE_MEMORY_BLOCKED = "specialist_team_assignment_supabase_memory_blocked"

OVERLOADED_TEAMS_ATTENTION = (
    "specialist_team_assignment_overloaded_teams_attention"
)
CANDIDATE_QUEUE_ATTENTION = (
    "specialist_team_assignment_candidate_queue_attention"
)
HIGH_PRIORITY_QUEUE_ATTENTION = (
    "specialist_team_assignment_high_priority_queue_attention"
)
REVIEW_LAG_ATTENTION = "specialist_team_assignment_review_lag_attention"

BLOCKED_REASON_CODES = (
    NO_TEAMS_BLOCKED,
    NO_READY_TEAMS_BLOCKED,
    ALL_TEAMS_OVERLOADED_BLOCKED,
    MANUAL_REVIEW_CAPACITY_BLOCKED,
    SUPABASE_MEMORY_BLOCKED,
)
ATTENTION_REASON_CODES = (
    OVERLOADED_TEAMS_ATTENTION,
    CANDIDATE_QUEUE_ATTENTION,
    HIGH_PRIORITY_QUEUE_ATTENTION,
    REVIEW_LAG_ATTENTION,
)

__all__ = (
    "DEFAULT_SPECIALIST_TEAM_ASSIGNMENT_LOAD_BALANCE_CONFIG_VERSION",
    "SPECIALIST_TEAM_ASSIGNMENT_LOAD_BALANCE_BANDS",
    "SpecialistTeamAssignmentLoadBalanceInput",
    "SpecialistTeamAssignmentLoadBalanceReport",
    "build_specialist_team_assignment_load_balance_report",
    "specialist_team_assignment_load_balance_report_digest",
    "specialist_team_assignment_load_balance_report_public_payload",
)


@dataclass(frozen=True)
class SpecialistTeamAssignmentLoadBalanceInput:
    team_count: Decimal
    overloaded_team_count: Decimal
    ready_team_count: Decimal
    queued_candidate_count: Decimal
    high_priority_candidate_count: Decimal
    average_review_lag_seconds: Decimal
    manual_review_capacity_ready: bool
    supabase_memory_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamAssignmentLoadBalanceInput:
            raise ValueError(
                "input must be exactly SpecialistTeamAssignmentLoadBalanceInput",
            )
        for field_name in (
            "team_count",
            "overloaded_team_count",
            "ready_team_count",
            "queued_candidate_count",
            "high_priority_candidate_count",
            "average_review_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("manual_review_capacity_ready", self.manual_review_capacity_ready)
        _require_bool("supabase_memory_ready", self.supabase_memory_ready)
        _validate_input_counts(self)
        require_paper_only_flags("specialist team assignment load-balance input", self)


@dataclass(frozen=True)
class SpecialistTeamAssignmentLoadBalanceReport:
    config_version: str
    team_count: Decimal
    overloaded_team_count: Decimal
    ready_team_count: Decimal
    queued_candidate_count: Decimal
    high_priority_candidate_count: Decimal
    average_review_lag_seconds: Decimal
    manual_review_capacity_ready: bool
    supabase_memory_ready: bool
    load_balance_ready: bool
    load_balance_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamAssignmentLoadBalanceReport:
            raise ValueError(
                "report must be exactly SpecialistTeamAssignmentLoadBalanceReport",
            )
        if (
            self.config_version
            != DEFAULT_SPECIALIST_TEAM_ASSIGNMENT_LOAD_BALANCE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "team_count",
            "overloaded_team_count",
            "ready_team_count",
            "queued_candidate_count",
            "high_priority_candidate_count",
            "average_review_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("manual_review_capacity_ready", self.manual_review_capacity_ready)
        _require_bool("supabase_memory_ready", self.supabase_memory_ready)
        _require_bool("load_balance_ready", self.load_balance_ready)
        _require_band(self.load_balance_band)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _require_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCKED_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _require_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _validate_report(self)
        require_paper_only_flags("specialist team assignment load-balance report", self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return specialist_team_assignment_load_balance_report_public_payload(self)

    @property
    def digest(self) -> str:
        return specialist_team_assignment_load_balance_report_digest(self)


def build_specialist_team_assignment_load_balance_report(
    load_balance_input: SpecialistTeamAssignmentLoadBalanceInput,
) -> SpecialistTeamAssignmentLoadBalanceReport:
    if type(load_balance_input) is not SpecialistTeamAssignmentLoadBalanceInput:
        raise ValueError(
            "load_balance_input must be a SpecialistTeamAssignmentLoadBalanceInput",
        )
    require_paper_only_flags("specialist team assignment load-balance input", load_balance_input)
    blocked_reason_codes = _blocked_reason_codes(load_balance_input)
    attention_reason_codes = _attention_reason_codes(load_balance_input)
    load_balance_band = _load_balance_band(blocked_reason_codes, attention_reason_codes)

    return SpecialistTeamAssignmentLoadBalanceReport(
        config_version=DEFAULT_SPECIALIST_TEAM_ASSIGNMENT_LOAD_BALANCE_CONFIG_VERSION,
        team_count=load_balance_input.team_count,
        overloaded_team_count=load_balance_input.overloaded_team_count,
        ready_team_count=load_balance_input.ready_team_count,
        queued_candidate_count=load_balance_input.queued_candidate_count,
        high_priority_candidate_count=load_balance_input.high_priority_candidate_count,
        average_review_lag_seconds=load_balance_input.average_review_lag_seconds,
        manual_review_capacity_ready=load_balance_input.manual_review_capacity_ready,
        supabase_memory_ready=load_balance_input.supabase_memory_ready,
        load_balance_ready=load_balance_band == READY_BAND,
        load_balance_band=load_balance_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ratio(load_balance_input.ready_team_count, load_balance_input.team_count),
    )


def specialist_team_assignment_load_balance_report_public_payload(
    report: SpecialistTeamAssignmentLoadBalanceReport,
) -> dict[str, Any]:
    if type(report) is not SpecialistTeamAssignmentLoadBalanceReport:
        raise ValueError("report must be a SpecialistTeamAssignmentLoadBalanceReport")
    require_paper_only_flags("specialist team assignment load-balance report", report)
    _validate_report(report)
    payload = json_ready_no_floats(asdict(report))
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    payload["digest"] = specialist_team_assignment_load_balance_report_digest(report)
    return payload


def specialist_team_assignment_load_balance_report_digest(
    report: SpecialistTeamAssignmentLoadBalanceReport,
) -> str:
    if type(report) is not SpecialistTeamAssignmentLoadBalanceReport:
        raise ValueError("report must be a SpecialistTeamAssignmentLoadBalanceReport")
    require_paper_only_flags("specialist team assignment load-balance report", report)
    _validate_report(report)
    payload = json_ready_no_floats(asdict(report))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    digest_source = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(digest_source.encode("utf-8")).hexdigest()


def _blocked_reason_codes(
    load_balance_input: SpecialistTeamAssignmentLoadBalanceInput,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if load_balance_input.team_count == ZERO:
        reasons.append(NO_TEAMS_BLOCKED)
    elif load_balance_input.ready_team_count == ZERO:
        reasons.append(NO_READY_TEAMS_BLOCKED)
    if (
        load_balance_input.team_count > ZERO
        and load_balance_input.overloaded_team_count == load_balance_input.team_count
    ):
        reasons.append(ALL_TEAMS_OVERLOADED_BLOCKED)
    if not load_balance_input.manual_review_capacity_ready:
        reasons.append(MANUAL_REVIEW_CAPACITY_BLOCKED)
    if not load_balance_input.supabase_memory_ready:
        reasons.append(SUPABASE_MEMORY_BLOCKED)
    return tuple(reasons)


def _attention_reason_codes(
    load_balance_input: SpecialistTeamAssignmentLoadBalanceInput,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if (
        load_balance_input.overloaded_team_count > ZERO
        and load_balance_input.overloaded_team_count < load_balance_input.team_count
    ):
        reasons.append(OVERLOADED_TEAMS_ATTENTION)
    if load_balance_input.queued_candidate_count > MAX_READY_QUEUED_CANDIDATE_COUNT:
        reasons.append(CANDIDATE_QUEUE_ATTENTION)
    if (
        load_balance_input.high_priority_candidate_count
        > MAX_READY_HIGH_PRIORITY_CANDIDATE_COUNT
    ):
        reasons.append(HIGH_PRIORITY_QUEUE_ATTENTION)
    if (
        load_balance_input.average_review_lag_seconds
        > MAX_READY_AVERAGE_REVIEW_LAG_SECONDS
    ):
        reasons.append(REVIEW_LAG_ATTENTION)
    return tuple(reasons)


def _load_balance_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return BLOCKED_BAND
    if attention_reason_codes:
        return ATTENTION_BAND
    return READY_BAND


def _validate_input_counts(
    load_balance_input: SpecialistTeamAssignmentLoadBalanceInput,
) -> None:
    if load_balance_input.ready_team_count > load_balance_input.team_count:
        raise ValueError("ready_team_count must be less than or equal to team_count")
    if load_balance_input.overloaded_team_count > load_balance_input.team_count:
        raise ValueError(
            "overloaded_team_count must be less than or equal to team_count",
        )
    if (
        load_balance_input.high_priority_candidate_count
        > load_balance_input.queued_candidate_count
    ):
        raise ValueError(
            "high_priority_candidate_count must be less than or equal to queued_candidate_count",
        )


def _validate_report(report: SpecialistTeamAssignmentLoadBalanceReport) -> None:
    _validate_input_counts(
        SpecialistTeamAssignmentLoadBalanceInput(
            team_count=report.team_count,
            overloaded_team_count=report.overloaded_team_count,
            ready_team_count=report.ready_team_count,
            queued_candidate_count=report.queued_candidate_count,
            high_priority_candidate_count=report.high_priority_candidate_count,
            average_review_lag_seconds=report.average_review_lag_seconds,
            manual_review_capacity_ready=report.manual_review_capacity_ready,
            supabase_memory_ready=report.supabase_memory_ready,
        ),
    )
    expected_blocked = _blocked_reason_codes(report)
    expected_attention = _attention_reason_codes(report)
    expected_band = _load_balance_band(expected_blocked, expected_attention)
    if report.blocked_reason_codes != expected_blocked:
        raise ValueError("blocked_reason_codes must match load-balance inputs")
    if report.attention_reason_codes != expected_attention:
        raise ValueError("attention_reason_codes must match load-balance inputs")
    if report.load_balance_band != expected_band:
        raise ValueError("load_balance_band must match reason codes")
    if report.load_balance_ready is not (expected_band == READY_BAND):
        raise ValueError("load_balance_ready must match load_balance_band")
    if report.ready_ratio != _ratio(report.ready_team_count, report.team_count):
        raise ValueError("ready_ratio must match team readiness counts")


def _require_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    previous_index = -1
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} must contain strings")
        if reason_code not in allowed_values:
            raise ValueError(f"{field_name} contains unsupported reason code")
        index = allowed_values.index(reason_code)
        if index <= previous_index:
            raise ValueError(f"{field_name} must be sorted deterministically")
        previous_index = index
    return reason_codes


def _require_band(value: object) -> None:
    if value not in SPECIALIST_TEAM_ASSIGNMENT_LOAD_BALANCE_BANDS:
        raise ValueError("load_balance_band must be a supported band")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(name, value)
    if decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    quantized = value.quantize(QUANTUM)
    if value != quantized:
        raise ValueError(f"{name} must be quantized to six decimal places")
    return quantized


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)
