"""Pure specialist team playbook readiness report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_SPECIALIST_TEAM_PLAYBOOK_READINESS_CONFIG_VERSION = (
    "specialist-team-playbook-readiness-v0"
)
SPECIALIST_TEAM_PLAYBOOK_READINESS_STATUSES = ("ready", "attention", "blocked")

ALLOWED_TEAM_CODES = ("politics", "finance", "sports")
READY_STATUS = "ready"
ATTENTION_STATUS = "attention"
BLOCKED_STATUS = "blocked"

PLAYBOOK_REVISION_MISSING = "playbook_revision_missing"
REQUIRED_SOURCE_CHECKLIST_MISSING = "required_source_checklist_missing"
DOMAIN_RISK_CHECKLIST_MISSING = "domain_risk_checklist_missing"
CALIBRATION_NOTES_MISSING = "calibration_notes_missing"
STALE_PLAYBOOK_AGE_REASON = "stale_playbook_update"
SUPABASE_MEMORY_NOT_READY = "supabase_memory_not_ready"
SPECIALIST_TEAM_PLAYBOOK_READY = "specialist_team_playbook_ready"

BLOCKER_REASON_CODES = (
    PLAYBOOK_REVISION_MISSING,
    REQUIRED_SOURCE_CHECKLIST_MISSING,
    CALIBRATION_NOTES_MISSING,
    SUPABASE_MEMORY_NOT_READY,
)
ATTENTION_REASON_CODES = (
    DOMAIN_RISK_CHECKLIST_MISSING,
    STALE_PLAYBOOK_AGE_REASON,
)
REPORT_REASON_CODES = (
    PLAYBOOK_REVISION_MISSING,
    REQUIRED_SOURCE_CHECKLIST_MISSING,
    DOMAIN_RISK_CHECKLIST_MISSING,
    CALIBRATION_NOTES_MISSING,
    STALE_PLAYBOOK_AGE_REASON,
    SUPABASE_MEMORY_NOT_READY,
    SPECIALIST_TEAM_PLAYBOOK_READY,
)

DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
SIX_PLACES = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ONE_COUNT = Decimal("1")
ONE_RATIO = Decimal("1.000000")
REQUIRED_CHECK_COUNT = Decimal("5")
DEFAULT_MAX_PLAYBOOK_UPDATE_AGE_SECONDS = Decimal("2592000")

STATUS_RANK = {BLOCKED_STATUS: 0, ATTENTION_STATUS: 1, READY_STATUS: 2}

__all__ = (
    "DEFAULT_SPECIALIST_TEAM_PLAYBOOK_READINESS_CONFIG_VERSION",
    "SPECIALIST_TEAM_PLAYBOOK_READINESS_STATUSES",
    "SpecialistTeamPlaybookReadinessConfig",
    "SpecialistTeamPlaybookReadinessInput",
    "SpecialistTeamPlaybookReadinessRow",
    "SpecialistTeamPlaybookReadinessReport",
    "build_specialist_team_playbook_readiness_report",
    "specialist_team_playbook_readiness_report_digest",
    "specialist_team_playbook_readiness_report_payload",
)


@dataclass(frozen=True)
class SpecialistTeamPlaybookReadinessConfig:
    config_version: str = DEFAULT_SPECIALIST_TEAM_PLAYBOOK_READINESS_CONFIG_VERSION
    max_playbook_update_age_seconds: Decimal = DEFAULT_MAX_PLAYBOOK_UPDATE_AGE_SECONDS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamPlaybookReadinessConfig:
            raise ValueError("config must be exactly SpecialistTeamPlaybookReadinessConfig")
        _require_config_version(self.config_version)
        object.__setattr__(
            self,
            "max_playbook_update_age_seconds",
            _normalize_count(
                "max_playbook_update_age_seconds",
                self.max_playbook_update_age_seconds,
            ),
        )
        require_paper_only_flags("specialist team playbook readiness config", self)


@dataclass(frozen=True)
class SpecialistTeamPlaybookReadinessInput:
    team_code: str
    domain: str
    playbook_revision_present: bool
    required_source_checklist_present: bool
    domain_risk_checklist_present: bool
    calibration_notes_present: bool
    last_playbook_update_age_seconds: Decimal
    supabase_memory_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamPlaybookReadinessInput:
            raise ValueError("input must be exactly SpecialistTeamPlaybookReadinessInput")
        _require_team_code("team_code", self.team_code)
        _require_team_code("domain", self.domain)
        if self.team_code != self.domain:
            raise ValueError("team_code and domain must match")
        for field_name in (
            "playbook_revision_present",
            "required_source_checklist_present",
            "domain_risk_checklist_present",
            "calibration_notes_present",
            "supabase_memory_ready",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "last_playbook_update_age_seconds",
            _normalize_count(
                "last_playbook_update_age_seconds",
                self.last_playbook_update_age_seconds,
            ),
        )
        require_paper_only_flags("specialist team playbook readiness input", self)


@dataclass(frozen=True)
class SpecialistTeamPlaybookReadinessRow:
    team_code: str
    domain: str
    playbook_revision_present: bool
    required_source_checklist_present: bool
    domain_risk_checklist_present: bool
    calibration_notes_present: bool
    last_playbook_update_age_seconds: Decimal
    supabase_memory_ready: bool
    playbook_ready: bool
    missing_check_count: Decimal
    attention_check_count: Decimal
    ready_check_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamPlaybookReadinessRow:
            raise ValueError("row must be exactly SpecialistTeamPlaybookReadinessRow")
        _require_team_code("team_code", self.team_code)
        _require_team_code("domain", self.domain)
        if self.team_code != self.domain:
            raise ValueError("team_code and domain must match")
        for field_name in (
            "playbook_revision_present",
            "required_source_checklist_present",
            "domain_risk_checklist_present",
            "calibration_notes_present",
            "supabase_memory_ready",
            "playbook_ready",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "last_playbook_update_age_seconds",
            _normalize_count(
                "last_playbook_update_age_seconds",
                self.last_playbook_update_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "missing_check_count",
            _normalize_count("missing_check_count", self.missing_check_count),
        )
        object.__setattr__(
            self,
            "attention_check_count",
            _normalize_count("attention_check_count", self.attention_check_count),
        )
        object.__setattr__(
            self,
            "ready_check_ratio",
            _normalize_ratio("ready_check_ratio", self.ready_check_ratio),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        require_paper_only_flags("specialist team playbook readiness row", self)


@dataclass(frozen=True)
class SpecialistTeamPlaybookReadinessReport:
    config_version: str
    team_count: Decimal
    playbook_ready_count: Decimal
    attention_team_count: Decimal
    blocked_team_count: Decimal
    missing_check_count: Decimal
    attention_check_count: Decimal
    ready_check_ratio: Decimal
    playbook_ready: bool
    status: str
    reason_codes: tuple[str, ...]
    readiness_rows: tuple[SpecialistTeamPlaybookReadinessRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamPlaybookReadinessReport:
            raise ValueError("report must be exactly SpecialistTeamPlaybookReadinessReport")
        _require_config_version(self.config_version)
        for field_name in (
            "team_count",
            "playbook_ready_count",
            "attention_team_count",
            "blocked_team_count",
            "missing_check_count",
            "attention_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ready_check_ratio",
            _normalize_ratio("ready_check_ratio", self.ready_check_ratio),
        )
        _require_bool("playbook_ready", self.playbook_ready)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, require_nonempty=False),
        )
        object.__setattr__(self, "readiness_rows", _normalize_rows(self.readiness_rows))
        _validate_report(self)
        require_paper_only_flags("specialist team playbook readiness report", self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return specialist_team_playbook_readiness_report_payload(self)

    @property
    def digest(self) -> str:
        return specialist_team_playbook_readiness_report_digest(self)


def build_specialist_team_playbook_readiness_report(
    inputs: Iterable[SpecialistTeamPlaybookReadinessInput],
    *,
    config: SpecialistTeamPlaybookReadinessConfig,
) -> SpecialistTeamPlaybookReadinessReport:
    if type(config) is not SpecialistTeamPlaybookReadinessConfig:
        raise ValueError("config must be a SpecialistTeamPlaybookReadinessConfig")
    require_paper_only_flags("config", config)
    normalized_inputs = _normalize_inputs(inputs)
    readiness_rows = tuple(
        sorted(
            (_readiness_row(row, config) for row in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    team_count = _count(len(readiness_rows))
    values = dict(
        config_version=config.config_version,
        team_count=team_count,
        playbook_ready_count=_count(
            sum(1 for row in readiness_rows if row.status == READY_STATUS),
        ),
        attention_team_count=_count(
            sum(1 for row in readiness_rows if row.status == ATTENTION_STATUS),
        ),
        blocked_team_count=_count(
            sum(1 for row in readiness_rows if row.status == BLOCKED_STATUS),
        ),
        missing_check_count=_sum_decimals(row.missing_check_count for row in readiness_rows),
        attention_check_count=_sum_decimals(
            (row.attention_check_count for row in readiness_rows),
        ),
        ready_check_ratio=_aggregate_ready_check_ratio(readiness_rows),
        playbook_ready=all(row.playbook_ready for row in readiness_rows),
        status=_report_status(readiness_rows),
        reason_codes=_report_reason_codes(readiness_rows),
        readiness_rows=readiness_rows,
    )
    return SpecialistTeamPlaybookReadinessReport(**values)


def specialist_team_playbook_readiness_report_payload(
    report: SpecialistTeamPlaybookReadinessReport,
) -> dict[str, Any]:
    if type(report) is not SpecialistTeamPlaybookReadinessReport:
        raise ValueError("report must be a SpecialistTeamPlaybookReadinessReport")
    require_paper_only_flags("report", report)
    _validate_report(report)
    reject_unsafe_surface_fields("specialist team playbook readiness report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("specialist team playbook readiness payload", payload)
    return payload


def specialist_team_playbook_readiness_report_digest(
    report: SpecialistTeamPlaybookReadinessReport,
) -> str:
    payload = specialist_team_playbook_readiness_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _readiness_row(
    row: SpecialistTeamPlaybookReadinessInput,
    config: SpecialistTeamPlaybookReadinessConfig,
) -> SpecialistTeamPlaybookReadinessRow:
    reason_codes = _input_reason_codes(row, config)
    missing_check_count = _count(
        sum(1 for reason in reason_codes if reason in BLOCKER_REASON_CODES),
    )
    attention_check_count = _count(
        sum(1 for reason in reason_codes if reason in ATTENTION_REASON_CODES),
    )
    ready_ratio = _ready_check_ratio(missing_check_count, attention_check_count)
    status = _row_status(missing_check_count, attention_check_count)
    return SpecialistTeamPlaybookReadinessRow(
        team_code=row.team_code,
        domain=row.domain,
        playbook_revision_present=row.playbook_revision_present,
        required_source_checklist_present=row.required_source_checklist_present,
        domain_risk_checklist_present=row.domain_risk_checklist_present,
        calibration_notes_present=row.calibration_notes_present,
        last_playbook_update_age_seconds=row.last_playbook_update_age_seconds,
        supabase_memory_ready=row.supabase_memory_ready,
        playbook_ready=status == READY_STATUS,
        missing_check_count=missing_check_count,
        attention_check_count=attention_check_count,
        ready_check_ratio=ready_ratio,
        status=status,
        reason_codes=reason_codes,
    )


def _input_reason_codes(
    row: SpecialistTeamPlaybookReadinessInput,
    config: SpecialistTeamPlaybookReadinessConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not row.playbook_revision_present:
        reasons.append(PLAYBOOK_REVISION_MISSING)
    if not row.required_source_checklist_present:
        reasons.append(REQUIRED_SOURCE_CHECKLIST_MISSING)
    if not row.domain_risk_checklist_present:
        reasons.append(DOMAIN_RISK_CHECKLIST_MISSING)
    if not row.calibration_notes_present:
        reasons.append(CALIBRATION_NOTES_MISSING)
    if (
        row.playbook_revision_present
        and row.last_playbook_update_age_seconds
        > config.max_playbook_update_age_seconds
    ):
        reasons.append(STALE_PLAYBOOK_AGE_REASON)
    if not row.supabase_memory_ready:
        reasons.append(SUPABASE_MEMORY_NOT_READY)
    if not reasons:
        reasons.append(SPECIALIST_TEAM_PLAYBOOK_READY)
    return _normalize_reason_codes("reason_codes", tuple(reasons), require_nonempty=True)


def _expected_reason_codes(row: SpecialistTeamPlaybookReadinessRow) -> tuple[str, ...]:
    reasons: list[str] = []
    if not row.playbook_revision_present:
        reasons.append(PLAYBOOK_REVISION_MISSING)
    if not row.required_source_checklist_present:
        reasons.append(REQUIRED_SOURCE_CHECKLIST_MISSING)
    if not row.domain_risk_checklist_present:
        reasons.append(DOMAIN_RISK_CHECKLIST_MISSING)
    if not row.calibration_notes_present:
        reasons.append(CALIBRATION_NOTES_MISSING)
    if (
        row.playbook_revision_present
        and row.last_playbook_update_age_seconds
        > DEFAULT_MAX_PLAYBOOK_UPDATE_AGE_SECONDS
    ):
        reasons.append(STALE_PLAYBOOK_AGE_REASON)
    if not row.supabase_memory_ready:
        reasons.append(SUPABASE_MEMORY_NOT_READY)
    if not reasons:
        reasons.append(SPECIALIST_TEAM_PLAYBOOK_READY)
    return tuple(reasons)


def _ready_check_ratio(
    missing_check_count: Decimal,
    attention_check_count: Decimal,
) -> Decimal:
    return _safe_ratio(
        REQUIRED_CHECK_COUNT - missing_check_count - attention_check_count,
        REQUIRED_CHECK_COUNT,
    )


def _row_status(missing_check_count: Decimal, attention_check_count: Decimal) -> str:
    if missing_check_count > ZERO_COUNT:
        return BLOCKED_STATUS
    if attention_check_count > ZERO_COUNT:
        return ATTENTION_STATUS
    return READY_STATUS


def _report_status(rows: tuple[SpecialistTeamPlaybookReadinessRow, ...]) -> str:
    if any(row.status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.status == ATTENTION_STATUS for row in rows):
        return ATTENTION_STATUS
    return READY_STATUS


def _report_reason_codes(
    rows: tuple[SpecialistTeamPlaybookReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ()
    found = {
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != SPECIALIST_TEAM_PLAYBOOK_READY
    }
    if not found:
        return (SPECIALIST_TEAM_PLAYBOOK_READY,)
    return tuple(reason for reason in REPORT_REASON_CODES if reason in found)


def _aggregate_ready_check_ratio(
    rows: tuple[SpecialistTeamPlaybookReadinessRow, ...],
) -> Decimal:
    if not rows:
        return _quantize_ratio(ZERO_COUNT)
    total_checks = REQUIRED_CHECK_COUNT * _count(len(rows))
    total_not_ready = _sum_decimals(row.missing_check_count for row in rows)
    total_not_ready += _sum_decimals(row.attention_check_count for row in rows)
    return _safe_ratio(total_checks - total_not_ready, total_checks)


def _row_sort_key(row: SpecialistTeamPlaybookReadinessRow) -> tuple[int, Decimal, str]:
    return (STATUS_RANK[row.status], row.ready_check_ratio, row.team_code)


def _normalize_inputs(
    inputs: Iterable[SpecialistTeamPlaybookReadinessInput],
) -> tuple[SpecialistTeamPlaybookReadinessInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not SpecialistTeamPlaybookReadinessInput:
            raise ValueError(
                "inputs must contain SpecialistTeamPlaybookReadinessInput values",
            )
        require_paper_only_flags("input", row)
        if row.team_code in seen:
            raise ValueError("duplicate specialist team")
        seen.add(row.team_code)
    return rows


def _normalize_rows(
    values: Iterable[SpecialistTeamPlaybookReadinessRow],
) -> tuple[SpecialistTeamPlaybookReadinessRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("readiness_rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("readiness_rows must be an iterable") from exc
    seen: set[str] = set()
    previous_key: tuple[int, Decimal, str] | None = None
    for row in rows:
        if type(row) is not SpecialistTeamPlaybookReadinessRow:
            raise ValueError(
                "readiness_rows must contain SpecialistTeamPlaybookReadinessRow values",
            )
        require_paper_only_flags("row", row)
        if row.team_code in seen:
            raise ValueError("readiness_rows must be unique")
        seen.add(row.team_code)
        key = _row_sort_key(row)
        if previous_key is not None and previous_key > key:
            raise ValueError("readiness_rows must use stable sort")
        previous_key = key
    return rows


def _validate_row(row: SpecialistTeamPlaybookReadinessRow) -> None:
    expected_reasons = _expected_reason_codes(row)
    expected_missing_count = _count(
        sum(1 for reason in expected_reasons if reason in BLOCKER_REASON_CODES),
    )
    expected_attention_count = _count(
        sum(1 for reason in expected_reasons if reason in ATTENTION_REASON_CODES),
    )
    expected_status = _row_status(expected_missing_count, expected_attention_count)
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match readiness checks")
    if row.missing_check_count != expected_missing_count:
        raise ValueError("missing_check_count must match readiness checks")
    if row.attention_check_count != expected_attention_count:
        raise ValueError("attention_check_count must match readiness checks")
    if row.ready_check_ratio != _ready_check_ratio(
        expected_missing_count,
        expected_attention_count,
    ):
        raise ValueError("ready_check_ratio must match readiness checks")
    if row.status != expected_status:
        raise ValueError("status must match readiness checks")
    if row.playbook_ready != (expected_status == READY_STATUS):
        raise ValueError("playbook_ready must match readiness checks")


def _validate_report(report: SpecialistTeamPlaybookReadinessReport) -> None:
    rows = report.readiness_rows
    if report.team_count != _count(len(rows)):
        raise ValueError("team_count must match readiness_rows")
    if report.playbook_ready_count != _count(
        sum(1 for row in rows if row.status == READY_STATUS),
    ):
        raise ValueError("playbook_ready_count must match readiness_rows")
    if report.attention_team_count != _count(
        sum(1 for row in rows if row.status == ATTENTION_STATUS),
    ):
        raise ValueError("attention_team_count must match readiness_rows")
    if report.blocked_team_count != _count(
        sum(1 for row in rows if row.status == BLOCKED_STATUS),
    ):
        raise ValueError("blocked_team_count must match readiness_rows")
    if report.missing_check_count != _sum_decimals(
        (row.missing_check_count for row in rows),
    ):
        raise ValueError("missing_check_count must match readiness_rows")
    if report.attention_check_count != _sum_decimals(
        (row.attention_check_count for row in rows),
    ):
        raise ValueError("attention_check_count must match readiness_rows")
    if report.ready_check_ratio != _aggregate_ready_check_ratio(rows):
        raise ValueError("ready_check_ratio must match readiness_rows")
    if report.playbook_ready != all(row.playbook_ready for row in rows):
        raise ValueError("playbook_ready must match readiness_rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match readiness_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match readiness_rows")


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reasons = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if require_nonempty and not reasons:
        raise ValueError(f"{field_name} must be nonempty")
    if len(set(reasons)) != len(reasons):
        raise ValueError(f"{field_name} must be unique")
    sequence = {reason: index for index, reason in enumerate(REPORT_REASON_CODES)}
    previous_index = -1
    for reason in reasons:
        if type(reason) is not str or reason not in sequence:
            raise ValueError(f"{field_name} must contain known values")
        index = sequence[reason]
        if index <= previous_index:
            raise ValueError(f"{field_name} must be deterministic")
        previous_index = index
    return reasons


def _require_config_version(value: object) -> None:
    if value != DEFAULT_SPECIALIST_TEAM_PLAYBOOK_READINESS_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_team_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ALLOWED_TEAM_CODES:
        raise ValueError(f"{field_name} must be one of politics, finance, or sports")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SPECIALIST_TEAM_PLAYBOOK_READINESS_STATUSES:
        raise ValueError(f"{field_name} must be ready, attention, or blocked")


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_ratio(value)
    if normalized < ZERO_COUNT or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return _quantize_ratio(ZERO_COUNT)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(numerator / denominator)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SIX_PLACES)


def _count(value: int) -> Decimal:
    return Decimal(value)


def _sum_decimals(values: Iterable[Decimal]) -> Decimal:
    total = ZERO_COUNT
    for value in values:
        total += value
    return total


def _public_dict(value: object) -> dict[str, Any]:
    if not is_dataclass(value):
        raise ValueError("value must be a dataclass")
    return {field.name: getattr(value, field.name) for field in fields(value)}
