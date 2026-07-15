"""Pure Phase 1 readiness report for specialist team category playbooks."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_SPECIALIST_TEAM_CATEGORY_PLAYBOOK_READINESS_VERSION = (
    "specialist-team-category-playbook-readiness-report-v0"
)

PLAYBOOK_STATUSES = ("ready", "watch", "blocked")
REASON_CODES = (
    "category_playbook_exists",
    "category_playbook_missing",
    "settled_examples_ready",
    "settled_examples_thin",
    "settled_examples_missing",
    "source_family_coverage_ready",
    "source_family_coverage_partial",
    "source_family_coverage_thin",
    "calibration_notes_ready",
    "calibration_notes_missing",
    "playbook_recent",
    "playbook_recency_watch",
    "playbook_stale",
    "category_playbook_ready",
    "category_playbook_watch",
    "category_playbook_blocked",
)

UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "or" "der",
    "ke" "y",
    "si" "gn",
    "ex" "ec",
    "tra" "de",
    "bu" "y",
    "se" "ll",
    "data" "base",
    "per" "sist",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
HOUR_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
MIN_READY_SETTLED_EXAMPLES = Decimal("5")
MIN_WATCH_SETTLED_EXAMPLES = Decimal("1")
MIN_READY_SOURCE_FAMILIES = Decimal("3")
MIN_WATCH_SOURCE_FAMILIES = Decimal("2")
MIN_READY_CALIBRATION_NOTES = Decimal("1")
MAX_RECENT_AGE_HOURS = Decimal("24.000000")
MAX_WATCH_AGE_HOURS = Decimal("168.000000")


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class SpecialistTeamCategoryPlaybookReadinessInput(_FinalDataclass):
    category_id: str
    playbook_exists: bool
    settled_example_count: Decimal
    source_family_coverage_count: Decimal
    calibration_note_count: Decimal
    last_updated_age_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamCategoryPlaybookReadinessInput, "input")
        object.__setattr__(
            self,
            "category_id",
            _require_public_string("category_id", self.category_id),
        )
        _require_bool("playbook_exists", self.playbook_exists)
        for field_name in (
            "settled_example_count",
            "source_family_coverage_count",
            "calibration_note_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "last_updated_age_hours",
            _normalize_age_hours("last_updated_age_hours", self.last_updated_age_hours),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class SpecialistTeamCategoryPlaybookReadinessReport(_FinalDataclass):
    config_version: str
    category_id: str
    playbook_exists: bool
    settled_example_count: Decimal
    source_family_coverage_count: Decimal
    calibration_note_count: Decimal
    last_updated_age_hours: Decimal
    playbook_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamCategoryPlaybookReadinessReport, "report")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_SPECIALIST_TEAM_CATEGORY_PLAYBOOK_READINESS_VERSION:
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "category_id",
            _require_public_string("category_id", self.category_id),
        )
        _require_bool("playbook_exists", self.playbook_exists)
        for field_name in (
            "settled_example_count",
            "source_family_coverage_count",
            "calibration_note_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "last_updated_age_hours",
            _normalize_age_hours("last_updated_age_hours", self.last_updated_age_hours),
        )
        _require_status("playbook_status", self.playbook_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_public_string("manual_next_step", self.manual_next_step),
        )
        _require_digest_or_pending("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_public_payload_without_digest(self)
        if self.payload_digest != "pending" and self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return specialist_team_category_playbook_readiness_payload(self)


def build_specialist_team_category_playbook_readiness_report(
    readiness_input: SpecialistTeamCategoryPlaybookReadinessInput,
    *,
    config_version: str = DEFAULT_SPECIALIST_TEAM_CATEGORY_PLAYBOOK_READINESS_VERSION,
) -> SpecialistTeamCategoryPlaybookReadinessReport:
    if type(readiness_input) is not SpecialistTeamCategoryPlaybookReadinessInput:
        raise ValueError(
            "readiness_input must be a SpecialistTeamCategoryPlaybookReadinessInput",
        )
    _require_public_string("config_version", config_version)
    _require_hard_flags("input", readiness_input)
    _reject_unsafe_public_payload("input", readiness_input)

    playbook_status = _playbook_status(readiness_input)
    report = SpecialistTeamCategoryPlaybookReadinessReport(
        config_version=config_version,
        category_id=readiness_input.category_id,
        playbook_exists=readiness_input.playbook_exists,
        settled_example_count=readiness_input.settled_example_count,
        source_family_coverage_count=readiness_input.source_family_coverage_count,
        calibration_note_count=readiness_input.calibration_note_count,
        last_updated_age_hours=readiness_input.last_updated_age_hours,
        playbook_status=playbook_status,
        reason_codes=_reason_codes(readiness_input, playbook_status),
        manual_next_step=_manual_next_step(playbook_status),
        payload_digest="pending",
    )
    return SpecialistTeamCategoryPlaybookReadinessReport(
        config_version=report.config_version,
        category_id=report.category_id,
        playbook_exists=report.playbook_exists,
        settled_example_count=report.settled_example_count,
        source_family_coverage_count=report.source_family_coverage_count,
        calibration_note_count=report.calibration_note_count,
        last_updated_age_hours=report.last_updated_age_hours,
        playbook_status=report.playbook_status,
        reason_codes=report.reason_codes,
        manual_next_step=report.manual_next_step,
        payload_digest=_digest_public_payload_without_digest(report),
    )


def specialist_team_category_playbook_readiness_payload(
    report: SpecialistTeamCategoryPlaybookReadinessReport,
) -> dict[str, Any]:
    if type(report) is not SpecialistTeamCategoryPlaybookReadinessReport:
        raise ValueError("report must be a SpecialistTeamCategoryPlaybookReadinessReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    expected_digest = _digest_public_payload_without_digest(report)
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match public payload")
    payload = _public_payload_without_digest(report)
    payload["payload_digest"] = expected_digest
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _playbook_status(
    readiness_input: SpecialistTeamCategoryPlaybookReadinessInput,
) -> str:
    if (
        not readiness_input.playbook_exists
        or readiness_input.settled_example_count < MIN_WATCH_SETTLED_EXAMPLES
        or readiness_input.source_family_coverage_count < MIN_WATCH_SOURCE_FAMILIES
        or readiness_input.calibration_note_count < MIN_READY_CALIBRATION_NOTES
        or readiness_input.last_updated_age_hours > MAX_WATCH_AGE_HOURS
    ):
        return "blocked"
    if (
        readiness_input.settled_example_count < MIN_READY_SETTLED_EXAMPLES
        or readiness_input.source_family_coverage_count < MIN_READY_SOURCE_FAMILIES
        or readiness_input.last_updated_age_hours > MAX_RECENT_AGE_HOURS
    ):
        return "watch"
    return "ready"


def _reason_codes(
    readiness_input: SpecialistTeamCategoryPlaybookReadinessInput,
    playbook_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if readiness_input.playbook_exists:
        reason_codes.append("category_playbook_exists")
    else:
        reason_codes.append("category_playbook_missing")
    if readiness_input.settled_example_count >= MIN_READY_SETTLED_EXAMPLES:
        reason_codes.append("settled_examples_ready")
    elif readiness_input.settled_example_count >= MIN_WATCH_SETTLED_EXAMPLES:
        reason_codes.append("settled_examples_thin")
    else:
        reason_codes.append("settled_examples_missing")
    if readiness_input.source_family_coverage_count >= MIN_READY_SOURCE_FAMILIES:
        reason_codes.append("source_family_coverage_ready")
    elif readiness_input.source_family_coverage_count >= MIN_WATCH_SOURCE_FAMILIES:
        reason_codes.append("source_family_coverage_partial")
    else:
        reason_codes.append("source_family_coverage_thin")
    if readiness_input.calibration_note_count >= MIN_READY_CALIBRATION_NOTES:
        reason_codes.append("calibration_notes_ready")
    else:
        reason_codes.append("calibration_notes_missing")
    if readiness_input.last_updated_age_hours <= MAX_RECENT_AGE_HOURS:
        reason_codes.append("playbook_recent")
    elif readiness_input.last_updated_age_hours <= MAX_WATCH_AGE_HOURS:
        reason_codes.append("playbook_recency_watch")
    else:
        reason_codes.append("playbook_stale")
    reason_codes.append(f"category_playbook_{playbook_status}")
    return tuple(reason for reason in REASON_CODES if reason in reason_codes)


def _manual_next_step(playbook_status: str) -> str:
    if playbook_status == "ready":
        return "reuse_category_playbook_for_paper_research"
    if playbook_status == "watch":
        return "refresh_category_playbook_evidence_before_reuse"
    return "create_category_playbook_before_paper_research"


def _public_payload_without_digest(
    report: SpecialistTeamCategoryPlaybookReadinessReport,
) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "category_id": report.category_id,
        "playbook_exists": report.playbook_exists,
        "settled_example_count": _decimal_to_string(report.settled_example_count),
        "source_family_coverage_count": _decimal_to_string(
            report.source_family_coverage_count,
        ),
        "calibration_note_count": _decimal_to_string(report.calibration_note_count),
        "last_updated_age_hours": _decimal_to_string(report.last_updated_age_hours),
        "playbook_status": report.playbook_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _digest_public_payload_without_digest(
    report: SpecialistTeamCategoryPlaybookReadinessReport,
) -> str:
    payload = _public_payload_without_digest(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_report(report: SpecialistTeamCategoryPlaybookReadinessReport) -> None:
    if report.reason_codes[-1] != f"category_playbook_{report.playbook_status}":
        raise ValueError("playbook_status reason must be last")
    expected_step = _manual_next_step(report.playbook_status)
    if report.manual_next_step != expected_step:
        raise ValueError("manual_next_step must match playbook_status")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be bool")


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in PLAYBOOK_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_age_hours(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(HOUR_QUANTUM)


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(value)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in normalized:
        _require_public_string(field_name, reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason for reason in REASON_CODES if reason in normalized) != normalized:
        raise ValueError(f"{field_name} must be deterministic")
    return normalized


def _require_digest_or_pending(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "pending":
        return
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(value)
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for item in _public_payload_items(value):
        if isinstance(item, str):
            try:
                _reject_unsafe_text(item)
            except ValueError as exc:
                raise ValueError(f"unsafe public payload in {label}") from exc


def _public_payload_items(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values = value.values()
    elif hasattr(value, "__dataclass_fields__"):
        values = (
            getattr(value, field_name)
            for field_name in value.__dataclass_fields__
        )
    elif isinstance(value, (tuple, list)):
        values = value
    else:
        return (value,)

    flattened: list[object] = []
    for item in values:
        if isinstance(item, (dict, tuple, list)) or hasattr(item, "__dataclass_fields__"):
            flattened.extend(_public_payload_items(item))
        else:
            flattened.append(item)
    return tuple(flattened)


def _reject_unsafe_text(value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError("unsafe public payload")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError("unsafe public payload")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _decimal_to_string(value: Decimal) -> str:
    return format(value, "f")


__all__ = (
    "DEFAULT_SPECIALIST_TEAM_CATEGORY_PLAYBOOK_READINESS_VERSION",
    "SpecialistTeamCategoryPlaybookReadinessInput",
    "SpecialistTeamCategoryPlaybookReadinessReport",
    "build_specialist_team_category_playbook_readiness_report",
    "specialist_team_category_playbook_readiness_payload",
)
