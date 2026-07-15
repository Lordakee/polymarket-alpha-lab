"""Pure report-only specialist disagreement resolution protocol readiness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


SPECIALIST_TEAM_DISAGREEMENT_RESOLUTION_PROTOCOL_STATUSES = (
    "ready",
    "watch",
    "blocked",
)

REASON_CODES = (
    "resolution_protocol_ready",
    "no_dissenting_teams",
    "no_unresolved_claims",
    "mediator_not_assigned",
    "evidence_packet_digest_missing",
    "resolution_sla_missing",
)

MANUAL_NEXT_STEPS = (
    "manual_review_resolution_packet",
    "monitor_for_specialist_disagreement",
    "monitor_for_unresolved_claims",
    "assign_mediator_and_prepare_evidence_packet",
    "prepare_evidence_packet_for_mediator",
    "set_resolution_sla_before_manual_review",
)

_COUNT_QUANT = Decimal("1.000000")
_ZERO = Decimal("0.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_DECIMAL_STRING_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)\.[0-9]{6}$")

_UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "live",
        "auth",
        "wallet",
        "private_key",
        "signature",
        "signing",
        "execute",
        "execution",
        "order",
        "trade",
        "database",
        "table",
        "dsn",
        "jsonl",
        "file_path",
        "persist",
        "url",
    ),
)

_UNSAFE_PUBLIC_VALUE_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\blive\b",
        r"\bauth(?:entication|orization)?\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
        r"\bsign(?:ature|ing)\b",
        r"\bexecute\b",
        r"\bexecution\b",
        r"\border\b",
        r"\btrade\b",
        r"\bdatabase\b",
        r"\btable\b",
        r"\bdsn\b",
        r"\bjsonl\b",
        r"\bpersist(?:ence|ed|ing)?\b",
        r"https?://",
        r"\burl\b",
    )
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class SpecialistTeamDisagreementResolutionProtocolReport(_FinalDataclass):
    dissenting_team_count: Decimal
    unresolved_claim_count: Decimal
    mediator_assigned: bool
    evidence_packet_digest_present: bool
    resolution_sla_hours: Decimal
    protocol_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamDisagreementResolutionProtocolReport, "report")
        object.__setattr__(
            self,
            "dissenting_team_count",
            _require_nonnegative_integral_decimal(
                "dissenting_team_count",
                self.dissenting_team_count,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_claim_count",
            _require_nonnegative_integral_decimal(
                "unresolved_claim_count",
                self.unresolved_claim_count,
            ),
        )
        object.__setattr__(
            self,
            "resolution_sla_hours",
            _require_nonnegative_integral_decimal(
                "resolution_sla_hours",
                self.resolution_sla_hours,
            ),
        )
        _require_bool("mediator_assigned", self.mediator_assigned)
        _require_bool(
            "evidence_packet_digest_present",
            self.evidence_packet_digest_present,
        )
        _require_status("protocol_status", self.protocol_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        _require_digest("payload_digest", self.payload_digest)
        require_paper_only_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        if self.payload_digest != _digest_from_values(_report_values_without_digest(self)):
            raise ValueError("payload_digest must match report payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return specialist_team_disagreement_resolution_protocol_report_payload(self)


def build_specialist_team_disagreement_resolution_protocol_report(
    *,
    dissenting_team_count: Decimal,
    unresolved_claim_count: Decimal,
    mediator_assigned: bool,
    evidence_packet_digest_present: bool,
    resolution_sla_hours: Decimal,
) -> SpecialistTeamDisagreementResolutionProtocolReport:
    normalized_dissenting_team_count = _require_nonnegative_integral_decimal(
        "dissenting_team_count",
        dissenting_team_count,
    )
    normalized_unresolved_claim_count = _require_nonnegative_integral_decimal(
        "unresolved_claim_count",
        unresolved_claim_count,
    )
    normalized_resolution_sla_hours = _require_nonnegative_integral_decimal(
        "resolution_sla_hours",
        resolution_sla_hours,
    )
    _require_bool("mediator_assigned", mediator_assigned)
    _require_bool(
        "evidence_packet_digest_present",
        evidence_packet_digest_present,
    )
    protocol_status, reason_codes, manual_next_step = _protocol_decision(
        dissenting_team_count=normalized_dissenting_team_count,
        unresolved_claim_count=normalized_unresolved_claim_count,
        mediator_assigned=mediator_assigned,
        evidence_packet_digest_present=evidence_packet_digest_present,
        resolution_sla_hours=normalized_resolution_sla_hours,
    )
    values: dict[str, object] = {
        "dissenting_team_count": normalized_dissenting_team_count,
        "unresolved_claim_count": normalized_unresolved_claim_count,
        "mediator_assigned": mediator_assigned,
        "evidence_packet_digest_present": evidence_packet_digest_present,
        "resolution_sla_hours": normalized_resolution_sla_hours,
        "protocol_status": protocol_status,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return SpecialistTeamDisagreementResolutionProtocolReport(
        **values,
        payload_digest=_digest_from_values(values),
    )


def specialist_team_disagreement_resolution_protocol_report_payload(
    report: SpecialistTeamDisagreementResolutionProtocolReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is SpecialistTeamDisagreementResolutionProtocolReport:
        require_paper_only_flags("report", report)
        _validate_report(report)
        _reject_unsafe_public_payload("report", report)
        payload = json_ready_no_floats(report)
        if type(payload) is not dict:
            raise ValueError("public_payload must be a JSON object")
        _validate_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("public_payload", report)
        _validate_payload(report)
        payload = json_ready_no_floats(report)
        if type(payload) is not dict:
            raise ValueError("public_payload must be a JSON object")
        _validate_payload(payload)
        return payload
    raise ValueError(
        "report must be a SpecialistTeamDisagreementResolutionProtocolReport or payload",
    )


def _protocol_decision(
    *,
    dissenting_team_count: Decimal,
    unresolved_claim_count: Decimal,
    mediator_assigned: bool,
    evidence_packet_digest_present: bool,
    resolution_sla_hours: Decimal,
) -> tuple[str, tuple[str, ...], str]:
    if dissenting_team_count == _ZERO:
        return (
            "watch",
            ("no_dissenting_teams",),
            "monitor_for_specialist_disagreement",
        )
    if unresolved_claim_count == _ZERO:
        return (
            "watch",
            ("no_unresolved_claims",),
            "monitor_for_unresolved_claims",
        )

    blockers: list[str] = []
    if not mediator_assigned:
        blockers.append("mediator_not_assigned")
    if not evidence_packet_digest_present:
        blockers.append("evidence_packet_digest_missing")
    if resolution_sla_hours == _ZERO:
        blockers.append("resolution_sla_missing")
    if blockers:
        return "blocked", tuple(blockers), _blocked_next_step(tuple(blockers))
    return (
        "ready",
        ("resolution_protocol_ready",),
        "manual_review_resolution_packet",
    )


def _blocked_next_step(reason_codes: tuple[str, ...]) -> str:
    if (
        "mediator_not_assigned" in reason_codes
        or "evidence_packet_digest_missing" in reason_codes
    ):
        return "assign_mediator_and_prepare_evidence_packet"
    return "set_resolution_sla_before_manual_review"


def _validate_report(report: SpecialistTeamDisagreementResolutionProtocolReport) -> None:
    expected_status, expected_reasons, expected_step = _protocol_decision(
        dissenting_team_count=report.dissenting_team_count,
        unresolved_claim_count=report.unresolved_claim_count,
        mediator_assigned=report.mediator_assigned,
        evidence_packet_digest_present=report.evidence_packet_digest_present,
        resolution_sla_hours=report.resolution_sla_hours,
    )
    if report.protocol_status != expected_status:
        raise ValueError("protocol_status must match protocol readiness inputs")
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match protocol readiness inputs")
    if report.manual_next_step != expected_step:
        raise ValueError("manual_next_step must match protocol readiness inputs")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be {expected_type.__name__}")


def _require_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value.quantize(_COUNT_QUANT)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be bool")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SPECIALIST_TEAM_DISAGREEMENT_RESOLUTION_PROTOCOL_STATUSES:
        raise ValueError(
            f"{field_name} must be one of "
            f"{SPECIALIST_TEAM_DISAGREEMENT_RESOLUTION_PROTOCOL_STATUSES}",
        )


def _require_manual_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a supported manual protocol step")


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        items = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for item in items:
        if type(item) is not str or item not in REASON_CODES:
            raise ValueError(f"{field_name} must contain supported reason codes")
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)
    return items


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_values_without_digest(
    report: SpecialistTeamDisagreementResolutionProtocolReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("payload_digest", None)
    return values


def _digest_from_values(values: dict[str, object]) -> str:
    payload = json_ready_no_floats(values)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _validate_payload(payload: dict[str, Any]) -> None:
    _require_payload_flags(payload)
    _reject_unsafe_public_payload("public_payload", payload)
    for field_name in (
        "dissenting_team_count",
        "unresolved_claim_count",
        "resolution_sla_hours",
    ):
        _require_decimal_payload_string(field_name, payload.get(field_name))
    for field_name in ("mediator_assigned", "evidence_packet_digest_present"):
        if type(payload.get(field_name)) is not bool:
            raise ValueError(f"{field_name} must be bool")
    _require_status("protocol_status", payload.get("protocol_status"))
    _normalize_reason_codes("reason_codes", payload.get("reason_codes", ()))
    _require_manual_next_step("manual_next_step", payload.get("manual_next_step"))
    _require_digest("payload_digest", payload.get("payload_digest"))
    digest_values = {key: value for key, value in payload.items() if key != "payload_digest"}
    if payload["payload_digest"] != _digest_from_values(digest_values):
        raise ValueError("payload_digest must match public_payload")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if payload.get(flag) is not True:
            raise ValueError(f"{flag} must be True")


def _require_decimal_payload_string(field_name: str, value: object) -> None:
    if type(value) is not str or _DECIMAL_STRING_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be Decimal-derived string")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public payload keys must be strings")
            lowered_key = key.casefold()
            if any(fragment in lowered_key for fragment in _UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        lowered = value.casefold()
        if any(pattern.search(lowered) for pattern in _UNSAFE_PUBLIC_VALUE_PATTERNS):
            raise ValueError(f"{label} contains unsafe public value")
